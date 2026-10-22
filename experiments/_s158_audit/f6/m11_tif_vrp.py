# -*- coding: utf-8 -*-
"""F6 M11: el VRP de la funcion publicada (via el oraculo) sobre el TIF M13 de MIROVA, contra el VRP de latest.php.
El TIF VIIRS750 es una matriz de 67 x 67 float64 escrita con MATLAB R2024b (etiqueta TIFFTAG_SOFTWARE): candidato a ser
ZI_M13. No tenemos M15, asi que no se puede correr la deteccion: se prueban como alerta los k pixeles mas calientes
dentro de 4 km de la cumbre (k = 1..6) y se mira si alguno reproduce el VRP publicado (redondeado a 0,01 MW).
Pregunta 1: si la funcion publicada no fuera la operacional (otro fondo, otro k o area) ningun k coincidiria, salvo por
azar; el azar se acota con el control: el mismo barrido con VRP publicado de OTRA pasada del mismo volcan.
Pregunta 2: si el TIF no fuera ZI_M13 (por ejemplo un remuestreo a EPSG:4326 hecho despues), tampoco coincidiria: un
NO no distingue «codigo distinto» de «TIF distinto». Solo un SI informa.
Denominador: los pares TIF + alerta VIIRS (750) del scraper listados en pares_tif.csv que se bajaron."""
import sys, io, glob, os, math
import numpy as np, pandas as pd, rasterio
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, sys.argv[1])
import mirova_v750 as mv
pares = pd.read_csv(sys.argv[2])
tifdir = sys.argv[3]
res = []
for _, p in pares.iterrows():
    f = os.path.join(tifdir, os.path.basename(p.path))
    if not os.path.exists(f):
        continue
    with rasterio.open(f) as r:
        m13 = r.read(1).astype(float)
    n = m13.shape[0]; c = n // 2
    ii, jj = np.indices(m13.shape)
    dist = 0.75 * np.hypot(ii - c, jj - c)
    cand = np.where((dist <= 4.0) & np.isfinite(m13))
    order = np.argsort(-m13[cand])
    hot = (ii[cand][order], jj[cand][order])
    fila = {"t": p.t, "vol": p.vol, "vrp_pub": p.vrp, "dist_pub": p.dist,
            "dist_pixel_max": round(float(dist[hot[0][0], hot[1][0]]), 2)}
    for k in range(1, 7):
        lin = np.ravel_multi_index((hot[0][:k], hot[1][:k]), m13.shape, order="F")
        v, *_ = mv.vrp(m13, lin)
        fila[f"k{k}"] = round(float(v), 3)
    res.append(fila)
df = pd.DataFrame(res)
print(df.to_string())
ks = [f"k{k}" for k in range(1, 7)]
hit = df.apply(lambda r: any(abs(r[k] - r.vrp_pub) <= 0.006 for k in ks), axis=1)
print("\ncoincide algun k (|dif| <= 0,006 MW):", int(hit.sum()), "de", len(df))
# control: VRP publicado de otra pasada (rotacion de la columna)
ctl = df.copy(); ctl["vrp_pub"] = np.roll(ctl.vrp_pub.to_numpy(), 1)
hc = ctl.apply(lambda r: any(abs(r[k] - r.vrp_pub) <= 0.006 for k in ks), axis=1)
print("control (VRP de otra pasada):", int(hc.sum()), "de", len(ctl))
