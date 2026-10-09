# -*- coding: utf-8 -*-
"""S150. En la imagen que MIROVA publica de la MISMA pasada (GeoTIFF I04, grilla remuestreada de 134 x 134
celdas), ¿cuanto sobresale la celda donde B publico, medido como lo mide el Test 2 pero en radiancia MIR:
dL = L - media de los 8 vecinos, normalizado por la media y la desviacion de dL de TODA la imagen?

  z = (dL_celda - mu_dL) / sd_dL        (y la version robusta con mediana y MAD)

Grupos (mismo instrumento para los tres): alertas que F PIERDE, alertas que F CONSERVA (y su tramo debil
< 0,10 MW), y negativos limpios que B publica (el residual). Si en la grilla de MIROVA las perdidas
sobresalen como las conservadas (z alto) y el residual no, la imagen de MIROVA permite detectar con la
lectura `max` lo que nuestra grilla nativa no deja: apunta al remuestreo / la sigma de la escena (D17).
Si las perdidas tampoco sobresalen en la imagen de MIROVA, MIROVA no podria verlas con `max` sobre ese
campo, y la explicacion es otra (lectura `min`, otra prueba, otro campo).

LIMITES DECLARADOS. (1) Es radiancia MIR sola, no NTI ni ETI: el Test 2 real mira el NTI, que divide por
la radiancia TIR; esto es un proxy. (2) El TIF sale del mismo granulo que nuestra deteccion (A109): no
certifica la deteccion, solo describe el campo de MIROVA. (3) La hora del nombre del archivo no se usa:
solo `acquisition_utc` a +-180 s (A106); se descartan los md5 que el indice asigna a mas de una hora de
adquisicion (imagen vieja servida bajo hora nueva). (4) Solo hay TIF con hora desde el 2026-05-09: abril
queda fuera.

LAS DOS PREGUNTAS DEL INSTRUMENTO. Si estuviera roto (celda equivocada, georreferencia corrida), las
conservadas fuertes NO sobresaldrian: es el control positivo. Si estuviera muerto, celdas sorteadas de
la misma imagen darian el mismo z que la nuestra: es el nulo, medido en cada imagen.

  python tif_contraste.py --tmp <dir del paso 1> --filas filas.json
"""
import argparse, collections, io, json, random, statistics as st, sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
import numpy as np
import pandas as pd
import rasterio
from rasterio.warp import transform as rio_transform
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent; RAIZ = AQUI.parents[1]
DL = RAIZ / "experiments" / "_s144_conteo_tif" / "_dl_tif"
IDX = DL / "da4fe36e8920_index.csv"; BASE = DL / "da4fe36e8920"
TIF2VOL = {"ChillanNevadosde": "NevadosDeChillan"}
MALAS = {"Lastarria|VIIRS375|2026-05-02 05:06", "Isluga|VIIRS375|2026-05-29 04:54", "Lascar|VIIRS375|2026-06-25 04:54",
         "Lascar|VIIRS375|2026-08-17 05:00", "Lascar|VIIRS375|2026-08-22 05:06"}
MESES = ["abril", "mayo", "junio", "julio", "agosto"]


def mean8(a):
    v = np.isfinite(a); x = np.where(v, a, 0.0)
    p = np.pad(x, 1); q = np.pad(v.astype(float), 1); s = np.zeros_like(x); n = np.zeros_like(x)
    for dr in (0, 1, 2):
        for dc in (0, 1, 2):
            if dr == 1 and dc == 1:
                continue
            s += p[dr:dr + a.shape[0], dc:dc + a.shape[1]]; n += q[dr:dr + a.shape[0], dc:dc + a.shape[1]]
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(n > 0, s / n, np.nan)


def indice():
    ix = pd.read_csv(IDX)
    ix = ix[(ix.sensor == "VIIRS375") & ix.acquisition_utc.notna() & (ix.size_bytes > 0)].copy()
    ix["t"] = pd.to_datetime(ix.acquisition_utc, utc=True, errors="coerce")
    ix["vol"] = ix.volcano.map(lambda v: TIF2VOL.get(v, v))
    horas_por_md5 = ix.groupby("md5")["t"].nunique()
    ix["md5_reusado"] = ix.md5.map(lambda m: horas_por_md5[m] > 1)
    ix["ruta"] = ix.tif_path.map(lambda p: BASE / p)
    ix = ix[ix.ruta.map(lambda p: p.exists())].drop_duplicates(["vol", "t", "md5"])
    return ix


def medir(ruta, lat, lon, rng):
    with rasterio.open(ruta) as ds:
        L = ds.read(1).astype(float)
        if ds.nodata is not None:
            L[L == ds.nodata] = np.nan
        L[L <= 0] = np.nan
        xs, ys = rio_transform("EPSG:4326", ds.crs, [lon], [lat])
        r, c = ds.index(xs[0], ys[0])
    n0, n1 = L.shape
    if not (1 <= r < n0 - 1 and 1 <= c < n1 - 1):
        return None
    dl = L - mean8(L)
    borde = np.zeros_like(L, bool); borde[1:-1, 1:-1] = True
    pool = dl[borde & np.isfinite(dl)]
    mu, sd = float(pool.mean()), float(pool.std())
    med = float(np.median(pool)); mad = 1.4826 * float(np.median(np.abs(pool - med)))
    win = dl[r - 1:r + 2, c - 1:c + 2]
    zc = (dl[r, c] - mu) / sd
    zw = (np.nanmax(win) - mu) / sd
    zwr = (np.nanmax(win) - med) / mad if mad > 0 else np.nan
    # nulo: ventanas 3x3 sorteadas en la misma imagen, lejos del borde
    nul = []
    for _ in range(60):
        rr, cc = rng.randrange(2, n0 - 2), rng.randrange(2, n1 - 2)
        w = dl[rr - 1:rr + 2, cc - 1:cc + 2]
        if np.isfinite(w).any():
            nul.append((np.nanmax(w) - mu) / sd)
    return {"dL_ventana": float(np.nanmax(win)), "z_celda": float(zc), "z_ventana": float(zw), "z_ventana_robusto": float(zwr), "sd_dL": sd, "mad_dL": mad,
            "sd_sobre_mad": sd / mad if mad > 0 else None, "nulo_z_ventana_med": float(np.median(nul)),
            "nulo_frac_mayor5": float(np.mean(np.array(nul) > 5))}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--tmp", required=True); ap.add_argument("--filas", required=True)
    ap.add_argument("--out", default=str(AQUI / "tif_contraste.json")); a = ap.parse_args()
    rng = random.Random(150)
    ix = indice(); por_vol = {v: g.sort_values("t") for v, g in ix.groupby("vol")}
    filas = {r["clave"]: r for r in json.load(open(a.filas, encoding="utf-8"))}
    crudoB = {}
    for mes in MESES:
        for p in (Path(a.tmp) / mes / "_s146_ab_sin_test1").glob("*.json"):
            for r in json.loads(p.read_text(encoding="utf-8"))["records"]:
                if (r.get("sensor") or "").startswith("VIIRS") and not (r.get("sensor") or "").endswith("_750"):
                    crudoB["%s|VIIRS375|%s" % (p.stem, r.get("datetime_utc"))] = r
    casos = []   # (grupo, clave, lat, lon, mirova_mw)
    for mes in MESES:
        T = json.loads((Path(a.tmp) / mes / "tabla.json").read_text(encoding="utf-8"))["pasadas"]
        for k, v in T.items():
            vol, b, dts = k.split("|")
            if b != "VIIRS375" or len(v) != 2 or not v["control"]["pub"] or k in MALAS:
                continue
            c = v["control"]
            if c["pc_lat"] is None:
                continue
            if c["lab"] == "neg_limpio":
                casos.append(("residual (neg. limpio que B publica)", k, c["pc_lat"], c["pc_lon"], None))
            elif c["lab"] == "pos" and k in filas:
                g = "perdida por F" if filas[k]["perdida"] else "conservada por F"
                casos.append((g, k, c["pc_lat"], c["pc_lon"], c.get("vrp_ref")))
    res = []; sin_tif = collections.Counter(); reusado = collections.Counter()
    for g, k, lat, lon, mw in casos:
        vol, b, dts = k.split("|")
        t = datetime.strptime(dts, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        s = por_vol.get(vol)
        if s is None:
            sin_tif[g] += 1; continue
        cand = s[(s.t >= t - timedelta(seconds=180)) & (s.t <= t + timedelta(seconds=180))]
        if cand.empty:
            sin_tif[g] += 1; continue
        if cand.md5_reusado.all():
            reusado[g] += 1; continue
        row = cand[~cand.md5_reusado].iloc[0]
        m = medir(row.ruta, lat, lon, rng)
        if m is None:
            sin_tif[g] += 1; continue
        rb = crudoB.get(k, {})
        tb = rb.get("t_bg_k")
        if tb:   # radiancia TIR aproximada del fondo con la BT de fondo I04 (aprox.; ver limites)
            lam = 11.45; Lt = 1.191042e8 / (lam ** 5 * (np.exp(1.4387752e4 / (lam * tb)) - 1.0))
            m["dnti_proxy_mirova"] = 2.0 * m["dL_ventana"] / Lt
            m["sd_dnti_proxy_mirova"] = 2.0 * m["sd_dL"] / Lt
        m["sd_dnti_nuestro"] = rb.get("diag_sd_dnti")
        m.update({"grupo": g, "clave": k, "mirova_mw": mw, "tif": str(row.tif_path)}); res.append(m)
    Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=0), encoding="utf-8")
    print("casos:", collections.Counter(c[0] for c in casos)); print("sin TIF a +-180 s:", dict(sin_tif)); print("solo con md5 reusado:", dict(reusado))
    grupos = collections.defaultdict(list)
    for m in res:
        grupos[m["grupo"]].append(m)
        if m["grupo"] == "conservada por F" and m["mirova_mw"] is not None and m["mirova_mw"] < 0.10:
            grupos["conservada por F, MIROVA < 0,10 MW"].append(m)
        if m["grupo"] == "conservada por F" and m["mirova_mw"] is not None and m["mirova_mw"] >= 0.5:
            grupos["conservada por F, MIROVA >= 0,5 MW (control positivo)"].append(m)
    def q(xs):
        xs = sorted(x for x in xs if x is not None and np.isfinite(x)); n = len(xs)
        return "p25 %.2f med %.2f p75 %.2f" % (xs[n // 4], st.median(xs), xs[(3 * n) // 4]) if n else "-"
    for g, ms in sorted(grupos.items()):
        print("\n== %s: n = %d" % (g, len(ms)))
        print("   z ventana 3x3 (media/sd):     %s | > 5: %d (%.0f %%)" % (q([m["z_ventana"] for m in ms]), sum(m["z_ventana"] > 5 for m in ms), 100 * np.mean([m["z_ventana"] > 5 for m in ms])))
        print("   z ventana 3x3 (mediana/MAD):  %s | > 5: %d" % (q([m["z_ventana_robusto"] for m in ms]), sum((m["z_ventana_robusto"] or 0) > 5 for m in ms)))
        print("   z celda exacta:               %s" % q([m["z_celda"] for m in ms]))
        print("   sd_dL / MAD_dL (colas):       %s" % q([m["sd_sobre_mad"] for m in ms]))
        print("   dNTI proxy en la grilla MIROVA (2 dL / L_TIR): %s | > C1 0,003: %d" % (q([m.get("dnti_proxy_mirova") for m in ms]), sum((m.get("dnti_proxy_mirova") or 0) > 0.003 for m in ms)))
        print("   sd dNTI proxy MIROVA / sd dNTI nuestro (misma pasada): %s" % q([m["sd_dnti_proxy_mirova"] / m["sd_dnti_nuestro"] for m in ms if m.get("sd_dnti_proxy_mirova") and m.get("sd_dnti_nuestro")]))
        print("   NULO, z ventana sorteada:     mediana de medianas %.2f | fraccion > 5 media %.3f" % (
            st.median(m["nulo_z_ventana_med"] for m in ms), np.mean([m["nulo_frac_mayor5"] for m in ms])))
    print("\nperdidas, una por una:")
    for m in sorted(grupos.get("perdida por F", []), key=lambda m: m["clave"]):
        print("  %-40s MIROVA %s | z ventana %.2f | robusto %.2f | z celda %.2f | sd/MAD %.2f" % (m["clave"], m["mirova_mw"], m["z_ventana"], m["z_ventana_robusto"], m["z_celda"], m["sd_sobre_mad"] or float("nan")))


if __name__ == "__main__":
    main()
