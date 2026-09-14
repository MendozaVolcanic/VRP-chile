# -*- coding: utf-8 -*-
"""S139 - ¿el exceso es del dato o del filtro que uso para encontrar el foco?

EL CONFUSOR. El foco se localiza restándole al campo su mediana móvil. Si la anomalía es
grande, contamina su propia ventana de mediana y el máximo filtrado puede correrse. Como una
anomalía grande es también una anomalía de VRP alto, ese corrimiento imitaría justo lo que la
sonda 08 interpretó como "el cúmulo crece": el filtro fabricaría la pendiente.

CÓMO SE DESCARTA. Si la pendiente la fabrica el filtro, cambiar el tamaño de la ventana
(5, 9, 15 y 21 píxeles, o sea de 1,9 a 7,9 km en VIIRS de 375 m) tiene que cambiarla mucho.
Si es del dato, se mantiene. Se reporta la constante y la pendiente con cada ventana.

Read-only. Reusa las mismas pasadas pareadas de la sonda 06.
"""
import io
import json
import math
import os
import subprocess
import sys

import numpy as np
import pandas as pd
import rasterio
from scipy.ndimage import median_filter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
CORTE_KM = 1.0


def medir(path, k):
    with rasterio.open(path) as src:
        a = src.read(1).astype(float)
        tr = src.transform
        h, w = a.shape
        clon, clat = rasterio.transform.xy(tr, h / 2.0 - 0.5, w / 2.0 - 0.5)
        rows, cols = np.mgrid[0:h, 0:w]
        xs, ys = rasterio.transform.xy(tr, rows.ravel(), cols.ravel())
        lat = np.array(ys).reshape(h, w)
        lon = np.array(xs).reshape(h, w)
    fin = np.isfinite(a)
    if fin.sum() < 200:
        return None
    b = np.where(fin, a, np.nanmedian(a[fin]))
    hp = b - median_filter(b, size=k)
    hp[~fin] = np.nan
    sig = float(np.nanstd(hp))
    if not np.isfinite(sig) or sig <= 0:
        return None
    i = int(np.nanargmax(np.where(fin, hp, -np.inf)))
    r, c = np.unravel_index(i, a.shape)
    olat = clat - 0.25 / 110.574
    olon = clon - 0.25 / (111.320 * math.cos(math.radians(clat)))
    d = math.hypot((lat[r, c] - olat) * 110.574,
                   (lon[r, c] - olon) * 111.320 * math.cos(math.radians(clat)))
    return d, float(hp[r, c] / sig)


def pendiente(y, x, n_boot=1500, semilla=139):
    lx = np.log10(np.clip(x, 1e-3, None))
    X = np.column_stack([np.ones_like(lx), lx])
    c, *_ = np.linalg.lstsq(X, y, rcond=None)
    rng = np.random.default_rng(semilla)
    b = [np.linalg.lstsq(X[i], y[i], rcond=None)[0][1]
         for i in (rng.integers(0, len(y), len(y)) for _ in range(n_boot))]
    b = np.array(b)
    return round(float(c[1]), 3), [round(float(np.percentile(b, 2.5)), 3),
                                   round(float(np.percentile(b, 97.5)), 3)]


def main():
    det = json.load(open(os.path.join(AQUI, "06_hipotesis_caliente_vs_lejano.json"),
                         encoding="utf-8"))["detalle"]
    d = pd.DataFrame(det)
    for c in ("dist_pub_km", "vrp_mw"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    ARCH = os.path.abspath(os.path.join(AQUI, "..", "..", "..", "..", "mirova-tif-archive"))
    DL = os.path.join(AQUI, "_dl_")
    R = {"_meta": {"corte_km": CORTE_KM, "n_pasadas_entrada": int(len(d)),
                   "prediccion_pendiente_si_mas_lejano": 0.238,
                   "prediccion_pendiente_si_mas_caliente": 0.0,
                   "fuente_prediccion": "08_exceso_crece_con_la_magnitud.json, "
                                        "calibración sobre OSF VIIRS375 (n=30.537)"},
         "por_kernel": {}}
    for k in (5, 9, 15, 21):
        ds, prom = [], []
        for t in d.tif:
            p = os.path.join(ARCH, t.replace("/", os.sep))
            if not os.path.exists(p):
                p = os.path.join(DL, t.replace("/", os.sep))
            m = medir(p, k) if os.path.exists(p) else None
            ds.append(m[0] if m else np.nan)
            prom.append(m[1] if m else np.nan)
        ds = np.array(ds)
        prom = np.array(prom)
        resid = d.dist_pub_km.values - ds
        ok = (np.abs(resid) <= CORTE_KM) & (prom >= 6.0) & (d.vrp_mw.values > 0)
        ok &= np.isfinite(resid)
        m, ic = pendiente(resid[ok], d.vrp_mw.values[ok])
        R["por_kernel"][str(k)] = {
            "ventana_km_viirs375": round(k * 0.375, 2),
            "n_incluidos": int(ok.sum()),
            "exceso_mediano_km": round(float(np.median(resid[ok])), 3),
            "pendiente_km_por_decada": m, "IC95": ic}
        print(f"kernel {k:2d} ({k*0.375:.1f} km)  n={int(ok.sum()):4d}  "
              f"exceso mediano {np.median(resid[ok]):+.3f} km  pendiente {m:+.3f} {ic}")
    json.dump(R, open(os.path.join(AQUI, "09_robustez_kernel.json"), "w",
                      encoding="utf-8"), indent=1, ensure_ascii=False)
    print("escrito: 09_robustez_kernel.json")


if __name__ == "__main__":
    main()
