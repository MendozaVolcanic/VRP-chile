# Corrimiento RELATIVO entre las dos familias de pasadas de un mismo satelite (volcan a la derecha de la
# traza contra volcan a la izquierda), por volcan y por rango de cenit. Solo lectura.
#
# POR QUE ASI. En produccion el pixel mas caliente cerca del crater muchas veces no es el crater: es un
# valle tibio mas bajo (A69), y elegir "el pixel del crater" sin sesgar la medicion no es posible desde
# los records. Pero el error de geolocalizacion corre TODA la imagen local, crater y valles juntos. Si se
# compara el mapa de densidad de todos los pixeles anomalos de las pasadas con el volcan a la derecha
# contra el de las pasadas con el volcan a la izquierda (mismo satelite, mismo rango de cenit, misma mezcla
# de estaciones), la posicion real de cada rasgo se cancela y queda solo la diferencia de corrimientos.
#   - Interpolacion: del lado del frame 0 corre hasta 2 frames hacia el sensor, del otro hasta 1 frame;
#     como el sensor queda al este en una familia y al oeste en la otra, la diferencia es grande.
#   - Paralaje residual: corre alejandose del sensor, igual en los dos lados: diferencia -2 x paralaje.
#   - Rasgo real fuera del crater o vent mal ubicado: se cancela, diferencia 0.
# Control: lo mismo en VIIRS 375, cuya geolocalizacion es por pixel y no pasa por `_interp_geo`.
import json
import math
import random
import statistics as st
import sys
import datetime as dt

import numpy as np

import comun

sys.stdout.reconfigure(encoding="utf-8")

RADIO_KM = 12.0
PASO = 0.25
SIGMA_KM = 1.0
BINS = ((0, 25), (25, 45), (45, 66))
N_BOOT = 150
L = 2 * 15.0
NG = int(L / PASO)
_ax = (np.arange(NG) - NG / 2) * PASO
GN, GE = np.meshgrid(_ax, _ax, indexing="ij")
_k = np.exp(-(GN ** 2 + GE ** 2) / (2 * SIGMA_KM ** 2))
KER = np.fft.fft2(np.fft.ifftshift(_k))


def grupo(sensor):
    s = sensor.upper()
    if s.startswith("MODIS"):
        return "MODIS"
    return "V750" if s.endswith("_750") else "V375"


def mapa(pasadas):
    """Densidad suavizada; cada pasada pesa 1 (repartido entre sus pixeles)."""
    h = np.zeros((NG, NG))
    for pix in pasadas:
        w = 1.0 / len(pix)
        for dn, de in pix:
            i = int(round(dn / PASO + NG / 2))
            j = int(round(de / PASO + NG / 2))
            if 0 <= i < NG and 0 <= j < NG:
                h[i, j] += w
    return np.real(np.fft.ifft2(np.fft.fft2(h) * KER))


def desplazamiento(a, b, max_km=6.0):
    """Vector (dN, dE) que hay que aplicar a b para que calce con a (correlacion cruzada, pico subpixel)."""
    a = a - a.mean()
    b = b - b.mean()
    cc = np.real(np.fft.ifft2(np.fft.fft2(a) * np.conj(np.fft.fft2(b))))
    cc = np.fft.fftshift(cc)
    c = NG // 2
    m = int(max_km / PASO)
    sub = cc[c - m:c + m + 1, c - m:c + m + 1]
    i, j = np.unravel_index(np.argmax(sub), sub.shape)

    def parab(fm, f0, fp):
        d = fm - 2 * f0 + fp
        return 0.0 if d == 0 else 0.5 * (fm - fp) / d
    di = parab(sub[i - 1, j], sub[i, j], sub[i + 1, j]) if 0 < i < sub.shape[0] - 1 else 0.0
    dj = parab(sub[i, j - 1], sub[i, j], sub[i, j + 1]) if 0 < j < sub.shape[1] - 1 else 0.0
    return ((i - m + di) * PASO, (j - m + dj) * PASO)


def vec(km, az):
    a = math.radians(az)
    return km * math.cos(a), km * math.sin(a)


def cargar(brazo=None, cache=None):
    vents = comun.vents()
    dem = json.load(open(comun.SALIDAS / "alturas_dem.json", encoding="utf-8"))["volcanes"]
    fam = {}
    for vol, (la, lo) in vents.items():
        recs = comun.cargar_records(vol, brazo, cache)
        for r in recs:
            z, az = r.get("sensor_zenith_deg"), r.get("sensor_azimuth_deg")
            if z is None or az is None or (r.get("solar_zenith_deg") or 0) <= 90:
                continue
            g = grupo(r["sensor"])
            if g == "V750":
                continue
            pix = []
            for p in r.get("anomaly_pixels") or []:
                if p.get("lat") is None:
                    continue
                dn, de = comun.ne_km(la, lo, p["lat"], p["lon"])
                if math.hypot(dn, de) <= RADIO_KM:
                    pix.append((dn, de))
            if not pix:
                continue
            t = dt.datetime.strptime(r["datetime_utc"][:16], "%Y-%m-%d %H:%M")
            sat = comun.satelite(r["sensor"])
            sat_k = sat if g == "MODIS" else "VIIRS375"      # los tres VIIRS juntos: misma geolocalizacion
            zb = next((b for b in BINS if b[0] <= z < b[1]), None)
            if zb is None:
                continue
            ld = comun.lado(sat, t, lo, az)
            fam.setdefault((vol, sat_k, zb, ld), []).append({"pix": pix, "z": z, "az": az % 360})
    return fam, dem


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--brazo", default=None, help="brazo de A/B (por defecto, produccion)")
    ap.add_argument("--cache", default=None, help="carpeta con <run_id>/<brazo>/<vol>.json")
    args = ap.parse_args()
    sufijo = "produccion" if args.brazo is None else args.brazo.strip("_")
    fam, dem = cargar(args.brazo, args.cache)
    rnd = random.Random(11)
    filas = []
    out = open(comun.SALIDAS / f"desplazamiento_por_familia_{sufijo}.txt", "w", encoding="utf-8")

    def p(s=""):
        print(s)
        out.write(s + "\n")

    p("Diferencia de corrimiento (familia volcan-a-la-derecha menos volcan-a-la-izquierda), proyectada sobre la")
    p("direccion hacia el sensor de la familia derecha (km). Prediccion de la interpolacion con el frame 0 a la")
    p("derecha de la traza; paralaje residual con el relieve SRTM; IC 95 %% bootstrap por pasadas (%d)." % N_BOOT)
    p("%-20s %-8s %-6s %5s %5s %8s %17s %8s %8s %8s" % ("volcan", "sat", "cenit", "n_der", "n_izq", "obs", "IC95", "interp",
                                                       "paralaje", "perp_obs"))
    for vol in comun.TIER_A:
        for sat in ("AQUA", "TERRA", "VIIRS375"):
            for zb in BINS:
                a = fam.get((vol, sat, zb, "der"), [])
                b = fam.get((vol, sat, zb, "izq"), [])
                if len(a) < 8 or len(b) < 8:
                    continue
                d = desplazamiento(mapa([x["pix"] for x in a]), mapa([x["pix"] for x in b]))
                az_a = st.median(x["az"] for x in a)
                az_b = st.median(x["az"] for x in b)
                z_a = st.median(x["z"] for x in a)
                z_b = st.median(x["z"] for x in b)
                ua = (math.cos(math.radians(az_a)), math.sin(math.radians(az_a)))
                obs = d[0] * ua[0] + d[1] * ua[1]
                perp = -d[0] * ua[1] + d[1] * ua[0]
                boots = []
                for _ in range(N_BOOT):
                    aa = [a[rnd.randrange(len(a))]["pix"] for _ in a]
                    bb = [b[rnd.randrange(len(b))]["pix"] for _ in b]
                    db = desplazamiento(mapa(aa), mapa(bb))
                    boots.append(db[0] * ua[0] + db[1] * ua[1])
                lo_, hi_ = np.percentile(boots, [2.5, 97.5])
                if sat == "VIIRS375":
                    pi = 0.0
                else:
                    sa = vec(comun.pred_interp_km(z_a, True), az_a)
                    sb = vec(comun.pred_interp_km(z_b, False), az_b)
                    pi = (sa[0] - sb[0]) * ua[0] + (sa[1] - sb[1]) * ua[1]
                rel = dem[vol]["relieve_m"] / 1000.0
                qa = vec(-rel * math.tan(math.radians(z_a)), az_a)
                qb = vec(-rel * math.tan(math.radians(z_b)), az_b)
                pp = (qa[0] - qb[0]) * ua[0] + (qa[1] - qb[1]) * ua[1]
                filas.append({"volcan": vol, "sat": sat, "cenit": "%d-%d" % zb, "n_der": len(a), "n_izq": len(b),
                              "obs_km": round(obs, 3), "ic_lo": round(float(lo_), 3), "ic_hi": round(float(hi_), 3),
                              "pred_interp_km": round(pi, 3), "pred_paralaje_km": round(pp, 3),
                              "perp_obs_km": round(perp, 3), "z_der": z_a, "z_izq": z_b})
                p("%-20s %-8s %2d-%2d %5d %5d %+8.2f [%+6.2f, %+6.2f] %+8.2f %+8.2f %+8.2f" % (
                    vol, sat, zb[0], zb[1], len(a), len(b), obs, lo_, hi_, pi, pp, perp))
    json.dump(filas, open(comun.SALIDAS / f"desplazamiento_por_familia_{sufijo}.json", "w", encoding="utf-8"), indent=1)

    p()
    for sat in ("AQUA", "TERRA", "VIIRS375"):
        s = [f for f in filas if f["sat"] == sat]
        if not s:
            continue
        x = np.array([f["pred_interp_km"] for f in s])
        y = np.array([f["obs_km"] for f in s])
        q = np.array([f["pred_paralaje_km"] for f in s])
        dentro_i = sum(f["ic_lo"] <= f["pred_interp_km"] <= f["ic_hi"] for f in s)
        dentro_p = sum(f["ic_lo"] <= f["pred_paralaje_km"] <= f["ic_hi"] for f in s)
        dentro_0 = sum(f["ic_lo"] <= 0 <= f["ic_hi"] for f in s)
        p("%-8s celdas %2d | media obs %+.2f  media interp %+.2f  media paralaje %+.2f | "
          "error medio abs contra interp %.2f, contra paralaje %.2f, contra cero %.2f | IC contiene interp %d, paralaje %d, cero %d"
          % (sat, len(s), y.mean(), x.mean(), q.mean(), np.abs(y - x).mean(), np.abs(y - q).mean(), np.abs(y).mean(),
             dentro_i, dentro_p, dentro_0))
    out.close()


if __name__ == "__main__":
    main()
