# Mide el corrimiento del pixel caliente del crater respecto de vent_lat/vent_lon en los 11 Tier A, para
# MODIS (el sospechoso) y VIIRS (el control). Solo lectura de data/mirova_equivalent/*.json.
#
# POR QUE ASI. Las tres explicaciones posibles predicen formas distintas:
#  - Interpolacion de `_interp_geo`: corrimiento HACIA el sensor, asimetrico segun el lado del barrido
#    (hasta 2 frames del lado del frame 0, hasta 1 frame del otro), igual para todos los volcanes, y con
#    una componente a lo largo de la traza que cambia de signo segun la linea del granulo (dispersion).
#  - Paralaje residual: corrimiento ALEJANDOSE del sensor, simetrico entre lados, proporcional a
#    (altura de la cumbre sobre las alturas de la grilla gruesa) x tan(cenit).
#  - Un foco real corrido del crater o un vent mal ubicado: desplazamiento FIJO en (norte, este), que
#    cambia de signo en la componente "hacia el sensor" cuando el sensor pasa del este al oeste.
# El ajuste separa las tres a la vez: desplazamiento fijo por volcan + a x (prediccion de la
# interpolacion) + b x (paralaje residual) + g x tan(cenit) libre.
#
# Uso: python medir_corrimiento.py            (escribe salidas/corrimiento_pasadas.csv y resumen)
import csv
import datetime as dt
import json
import math
import random
import re
import statistics as st
import sys
from pathlib import Path

import numpy as np

import comun

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(comun.RAIZ / "scripts"))
import calidad_referencia_mirova  # noqa: E402  (A119: el cargador avisa de los tramos defectuosos)

RMAX_KM = 8.0          # radio de busqueda del pixel del crater: mayor que el corrimiento esperado (<5 km)
DT_FUERTE_K = 10.0     # "fuente clara" por senal: pixel >= 10 K sobre el fondo de la escena
TOL_MIN = 6            # pareo con la alerta de MIROVA (granulo MODIS 5 min, VIIRS 6 min)


def grupo(sensor):
    s = sensor.upper()
    if s.startswith("MODIS"):
        return "MODIS"
    return "V750" if s.endswith("_750") else "V375"


def norm(nombre):
    return re.sub(r"[^a-z]", "", nombre.lower())


def alertas_mirova():
    """(volcan normalizado, bucket) -> lista de datetimes de ALERTA_TERMICA de la tabla consolidada."""
    f = comun.RAIZ / "data" / "mirova_reference" / "mirova_v1_snapshot" / "registro_vrp_consolidado.csv"
    out = {}
    fechas = []
    for row in csv.DictReader(open(f, encoding="utf-8")):
        if row["Tipo_Registro"] != "ALERTA_TERMICA":
            continue
        b = {"MODIS": "MODIS", "VIIRS375": "V375", "VIIRS": "V750"}.get(row["Sensor"])
        if b is None:
            continue
        t = dt.datetime.strptime(row["Fecha_Satelite_UTC"][:16], "%Y-%m-%d %H:%M")
        out.setdefault((norm(row["Volcan"]), b), []).append(t)
        fechas.append(t)
    calidad_referencia_mirova.avisar(min(fechas).strftime("%Y-%m-%d"), max(fechas).strftime("%Y-%m-%d"))
    return out


def es_alerta(al, vol, b, t):
    claves = [k for k in al if k[1] == b and (k[0] == norm(vol) or k[0].startswith(norm(vol)[:7]))]
    return any(abs((x - t).total_seconds()) <= TOL_MIN * 60 for k in claves for x in al[k])


def cargar(brazo=None, cache=None):
    vents = comun.vents()
    dem = json.load(open(comun.SALIDAS / "alturas_dem.json", encoding="utf-8"))["volcanes"]
    al = alertas_mirova()
    filas = []
    for vol, (la, lo) in vents.items():
        recs = comun.cargar_records(vol, brazo, cache)
        for r in recs:
            z, az = r.get("sensor_zenith_deg"), r.get("sensor_azimuth_deg")
            if z is None or az is None or (r.get("solar_zenith_deg") or 0) <= 90:
                continue        # solo noche y solo records con geometria (persistida desde S122)
            cerca = []
            for p in r.get("anomaly_pixels") or []:
                if p.get("lat") is None or p.get("bt_k") is None:
                    continue
                dn, de = comun.ne_km(la, lo, p["lat"], p["lon"])
                if math.hypot(dn, de) <= RMAX_KM:
                    cerca.append((p["bt_k"], dn, de))
            if not cerca:
                continue
            bt, dn, de = max(cerca)
            t = dt.datetime.strptime(r["datetime_utc"][:16], "%Y-%m-%d %H:%M")
            g = grupo(r["sensor"])
            sat = comun.satelite(r["sensor"])
            u, v = comun.hacia_sensor(dn, de, az)
            tbg = r.get("t_bg_k")
            filas.append({
                "volcan": vol, "grupo": g, "sat": sat, "fecha": r["datetime_utc"], "granulo": r.get("granule"),
                "cenit": z, "acimut": az % 360, "lado": comun.lado(sat, t, lo, az),
                "dn_km": dn, "de_km": de, "u_km": u, "v_km": v,
                "bt_k": bt, "t_bg_k": tbg, "exceso_k": (bt - tbg) if tbg else None,
                "alerta_mirova": es_alerta(al, vol, g, t),
                "h_vent_km": dem[vol]["vent_m"] / 1000.0, "relieve_km": dem[vol]["relieve_m"] / 1000.0,
                "pred_der": comun.pred_interp_km(z, True) if g == "MODIS" else 0.0,
                "pred_izq": comun.pred_interp_km(z, False) if g == "MODIS" else 0.0,
            })
    return filas


def ajustar(filas, columnas, n_boot=400, semilla=7):
    """Minimos cuadrados con desplazamiento fijo (norte, este) por volcan.
    Observacion: (dn, de) = (dn0, de0)_volcan + sum_k c_k * x_k * (cos az, sin az)."""
    vols = sorted({f["volcan"] for f in filas})
    iv = {v: i for i, v in enumerate(vols)}

    def resolver(sub):
        nfix = 2 * len(vols)
        A = np.zeros((2 * len(sub), nfix + len(columnas)))
        y = np.zeros(2 * len(sub))
        for i, f in enumerate(sub):
            a = math.radians(f["acimut"])
            j = iv[f["volcan"]]
            A[2 * i, 2 * j] = 1.0
            A[2 * i + 1, 2 * j + 1] = 1.0
            for k, c in enumerate(columnas):
                x = c(f)
                A[2 * i, nfix + k] = x * math.cos(a)
                A[2 * i + 1, nfix + k] = x * math.sin(a)
            y[2 * i], y[2 * i + 1] = f["dn_km"], f["de_km"]
        coef, *_ = np.linalg.lstsq(A, y, rcond=None)
        res = y - A @ coef
        return coef, float(np.sqrt(np.mean(res ** 2)))

    coef, rms = resolver(filas)
    rnd = random.Random(semilla)
    boots = []
    for _ in range(n_boot):
        sub = [filas[rnd.randrange(len(filas))] for _ in filas]
        if len({f["volcan"] for f in sub}) < len(vols):
            continue
        boots.append(resolver(sub)[0][2 * len(vols):])
    boots = np.array(boots)
    lo_, hi_ = np.percentile(boots, 2.5, axis=0), np.percentile(boots, 97.5, axis=0)
    nfix = 2 * len(vols)
    fijo = {v: (coef[2 * iv[v]], coef[2 * iv[v] + 1]) for v in vols}
    return coef[nfix:], lo_, hi_, rms, fijo


def tabla_bins(filas, out, titulo):
    print("\n" + titulo, file=out)
    print("%-20s %-7s %-4s %-7s %4s %8s %8s %8s %8s %8s" % ("volcan", "sat", "lado", "cenit", "n", "u_med", "v_med",
                                                           "v_iqr", "pred", "paralaje"), file=out)
    bins = ((0, 20), (20, 35), (35, 50), (50, 70))
    for vol in comun.TIER_A:
        for sat in ("AQUA", "TERRA", "SNPP", "NOAA20", "NOAA21"):
            for ld in ("der", "izq"):
                for z0, z1 in bins:
                    s = [f for f in filas if f["volcan"] == vol and f["sat"] == sat and f["lado"] == ld
                         and z0 <= f["cenit"] < z1]
                    if len(s) < 3:
                        continue
                    vs = sorted(f["v_km"] for f in s)
                    iqr = vs[3 * len(vs) // 4] - vs[len(vs) // 4]
                    par = -st.median(f["relieve_km"] * math.tan(math.radians(f["cenit"])) for f in s)
                    print("%-20s %-7s %-4s %2d-%2d   %4d %+8.2f %+8.2f %8.2f %+8.2f %+8.2f" % (
                        vol, sat, ld, z0, z1, len(s), st.median(f["u_km"] for f in s), st.median(f["v_km"] for f in s),
                        iqr, st.median(f["pred_der"] if ld == "der" else f["pred_izq"] for f in s), par), file=out)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--brazo", default=None, help="brazo de A/B (por defecto, produccion)")
    ap.add_argument("--cache", default=None, help="carpeta con <run_id>/<brazo>/<vol>.json")
    args = ap.parse_args()
    sufijo = "produccion" if args.brazo is None else args.brazo.strip("_")
    comun.SALIDAS.mkdir(exist_ok=True)
    filas = cargar(args.brazo, args.cache)
    with open(comun.SALIDAS / f"corrimiento_pasadas_{sufijo}.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas[0].keys()))
        w.writeheader()
        for f in filas:
            w.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in f.items()})

    out = open(comun.SALIDAS / f"corrimiento_resumen_{sufijo}.txt", "w", encoding="utf-8")

    class Tee:
        def write(self, s):
            out.write(s)
            sys.stdout.write(s)

        def flush(self):
            pass
    tee = Tee()

    tanz = lambda f: math.tan(math.radians(f["cenit"]))          # noqa: E731
    paralaje = lambda f: -f["relieve_km"] * tanz(f)                # noqa: E731  (alejandose del sensor)
    paralaje_abs = lambda f: -f["h_vent_km"] * tanz(f)             # noqa: E731  (sin correccion de terreno)
    pred_der = lambda f: f["pred_der"]                             # noqa: E731
    pred_izq = lambda f: f["pred_izq"]                             # noqa: E731
    pred_lado = lambda f: f["pred_der"] if f["lado"] == "der" else f["pred_izq"]   # noqa: E731  frame 0 a la derecha
    pred_lado_inv = lambda f: f["pred_izq"] if f["lado"] == "der" else f["pred_der"]  # noqa: E731  frame 0 a la izquierda

    selecciones = {
        "todas las pasadas con pixel a <= 8 km": lambda f: True,
        "alerta MIROVA (misma pasada, +-6 min)": lambda f: f["alerta_mirova"],
        "senal fuerte (pixel >= 10 K sobre el fondo)": lambda f: (f["exceso_k"] or 0) >= DT_FUERTE_K,
        "Lascar y Villarrica, todas las pasadas nocturnas": lambda f: f["volcan"] in ("Lascar", "Villarrica"),
    }
    print("Filas (pasadas nocturnas con pixel a <= %.0f km del crater): %d" % (RMAX_KM, len(filas)), file=tee)
    for nombre, cond in selecciones.items():
        for g in ("MODIS", "V375", "V750"):
            sub = [f for f in filas if f["grupo"] == g and cond(f)]
            vols = sorted({f["volcan"] for f in sub})
            if len(sub) < 20:
                print("\n[%s | %s] n=%d: muy pocas" % (nombre, g, len(sub)), file=tee)
                continue
            print("\n[%s | %s] n=%d pasadas, %d volcanes" % (nombre, g, len(sub), len(vols)), file=tee)
            modelos = {
                "M0 solo libre: g*tan(z)": [tanz],
                "M1 paralaje (relieve*tan z) + libre": [paralaje, tanz],
            }
            if g == "MODIS":
                modelos.update({
                    "M2b interpolacion sola, frame 0 a la DERECHA": [pred_lado],
                    "M2 interpolacion, frame 0 a la DERECHA de la traza + paralaje": [pred_lado, paralaje],
                    "M3 interpolacion, frame 0 a la IZQUIERDA + paralaje": [pred_lado_inv, paralaje],
                    "M4 interpolacion frame 0 der + paralaje absoluto (h*tan z)": [pred_lado, paralaje_abs],
                    "M5 interpolacion frame 0 der + paralaje + libre": [pred_lado, paralaje, tanz],
                })
            for mn, cols in modelos.items():
                c, lo_, hi_, rms, fijo = ajustar(sub, cols)
                txt = "  ".join("%+.2f [%+.2f, %+.2f]" % (c[k], lo_[k], hi_[k]) for k in range(len(cols)))
                print("   %-62s rms %.2f km | %s" % (mn, rms, txt), file=tee)
                if mn.startswith("M2") or (g != "MODIS" and mn.startswith("M0")):
                    print("      desplazamiento fijo del rasgo respecto de vent_lat/lon (dN, dE km): " + ", ".join(
                        "%s (%+.2f, %+.2f)" % (v, a, b) for v, (a, b) in fijo.items()), file=tee)
    # Lados por separado: la asimetria es la firma de la interpolacion. En produccion se filtra por alerta o
    # senal fuerte; en un brazo sin Test 1 entran todas (los pixeles ya son pocos y casi todos del crater).
    clara = (lambda f: True) if args.brazo else (lambda f: f["alerta_mirova"] or (f["exceso_k"] or 0) >= DT_FUERTE_K)
    print("\nMODIS, seleccion '%s': mediana de u (km, + = hacia el sensor) por satelite, lado y cenit"
          % ("todas" if args.brazo else "alerta o senal fuerte"), file=tee)
    sub = [f for f in filas if f["grupo"] == "MODIS" and clara(f)]
    for sat in ("AQUA", "TERRA"):
        for ld in ("der", "izq"):
            for z0, z1 in ((0, 20), (20, 35), (35, 50), (50, 70)):
                s = [f for f in sub if f["sat"] == sat and f["lado"] == ld and z0 <= f["cenit"] < z1]
                if len(s) >= 3:
                    print("   %-5s %-3s cenit %2d-%2d n=%4d  u med %+.2f  pred interp %+.2f  paralaje %+.2f  v med %+.2f" % (
                        sat, ld, z0, z1, len(s), st.median(f["u_km"] for f in s),
                        st.median(pred_lado(f) for f in s), st.median(paralaje(f) for f in s),
                        st.median(f["v_km"] for f in s)), file=tee)
    tabla_bins([f for f in filas if f["grupo"] == "MODIS" and clara(f)],
               tee, "Detalle MODIS por volcan, satelite, lado y cenit [km; u + = hacia el sensor]")
    tabla_bins([f for f in filas if f["grupo"] == "V375" and clara(f)],
               tee, "Detalle VIIRS 375, control [km]")
    out.close()


if __name__ == "__main__":
    main()
