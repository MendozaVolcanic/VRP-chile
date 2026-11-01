# -*- coding: utf-8 -*-
"""V-TIF para las protegidas que tienen GeoTIFF MODIS de MIROVA de SU pasada (solo 2 de 48: el archivo parte el
2026-05-09 y las protegidas de Lascar son casi todas de marzo y abril). Donde puso MIROVA el calor en esa misma pasada
(celda de maximo LOCAL a <= 5 km del crater, A24), contra el cumulo de K y de X.
No es independiente (A109: mismo granulo); mide paridad con la geolocalizacion de MIROVA, no verdad fisica.
Uso: python -I tif_mirova_protegidas.py DIR_CON_LOS_TIF   (bajados con
  gh api -H "Accept: application/vnd.github.raw" repos/MendozaVolcanic/mirova-tif-archive/contents/data/tif/Lascar/<f>_MODIS.tif)
P1: si la georreferencia del TIF estuviera corrida, el maximo local de Lascar con cenit <= 25 no caeria a una celda del
crater (A106, se imprime). P2: si el TIF fuera plano o nulo, el maximo no se distinguiria de la mediana (se imprime el
exceso del maximo sobre la mediana)."""
import csv
import io
import math
import sys
from pathlib import Path

import numpy as np
import rasterio

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cargar_a61 import haversine_km, punto_cardinal, rumbo  # noqa: E402

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
D = Path(sys.argv[1])
tab = {(f["vol"], f["dt"]): f for f in csv.DictReader(open(Path(__file__).parent / "a61_protegidas.csv", encoding="utf-8"))}
CASOS = [("Lascar", "2026-05-10 01:25", "Lascar_20260510_012500_MODIS.tif"), ("Lascar", "2026-06-27 01:35", "Lascar_20260627_013500_MODIS.tif")]
VENT = {"Lascar": (-23.36293, -67.731416)}
for vol, dt, fn in CASOS:
    f = tab[(vol, dt)]
    vlat, vlon = VENT[vol]
    with rasterio.open(D / fn) as ds:
        a = ds.read(1).astype(float)
        T = ds.transform
        rows, cols = np.indices(a.shape)
        xs, ys = rasterio.transform.xy(T, rows.ravel(), cols.ravel(), offset="center")
        lon, lat = np.array(xs).reshape(a.shape), np.array(ys).reshape(a.shape)
        crs, res = ds.crs, ds.res
    d = np.vectorize(haversine_km)(vlat, vlon, lat, lon)
    cc = np.unravel_index(np.argmin(d), d.shape)
    med = float(np.nanmedian(a))
    gm = np.unravel_index(np.nanargmax(a), a.shape)
    m = np.where(d <= 5.0, a, np.nan)
    lm = np.unravel_index(np.nanargmax(m), m.shape)
    print("%s %s | %s | CRS %s, %dx%d celdas de %.2f x %.2f km | %d NaN | mediana %.4f, max global %.4f en (%d,%d) a %.1f km (acimut %.0f)" % (
        vol, dt, fn, crs, a.shape[1], a.shape[0], abs(T.e) * 111.32, abs(T.a) * 111.32 * math.cos(math.radians(vlat)), int(np.isnan(a).sum()),
        med, a[gm], gm[0], gm[1], d[gm], rumbo(vlat, vlon, lat[gm], lon[gm])))
    print("   celda del crater (%d,%d) a %.2f km de su centro | maximo LOCAL (<= 5 km) en (%d,%d): valor %.4f (exceso %.4f sobre la mediana), lat %.5f lon %.5f, a %.2f km del crater, acimut %.0f (%s) -> %s" % (
        cc[0], cc[1], d[cc], lm[0], lm[1], a[lm], a[lm] - med, lat[lm], lon[lm], d[lm], rumbo(vlat, vlon, lat[lm], lon[lm]), punto_cardinal(rumbo(vlat, vlon, lat[lm], lon[lm])),
        "georreferencia OK (A106: a una celda del crater)" if d[lm] <= 1.5 else "georreferencia DUDOSA"))
    top = np.argsort(np.nan_to_num(m, nan=-1e9).ravel())[::-1][:4]
    print("   4 celdas mas calientes a <= 5 km:", [(int(i // a.shape[1]), int(i % a.shape[1]), round(float(a.ravel()[i]), 4), round(float(d.ravel()[i]), 2), punto_cardinal(rumbo(vlat, vlon, lat.ravel()[i], lon.ravel()[i]))) for i in top])
    for b in ("K", "X"):
        bl, bo = float(f[b + "_lat"]), float(f[b + "_lon"])
        print("   cumulo %s: lat %.5f lon %.5f, a %.2f km del crater (%s) | a %.2f km de la celda caliente de MIROVA | cae en la celda (%d,%d) del TIF" % (
            b, bl, bo, float(f[b + "_dist"]), f[b + "_rumbo"], haversine_km(bl, bo, lat[lm], lon[lm]),
            *np.unravel_index(np.argmin(np.vectorize(haversine_km)(bl, bo, lat, lon)), a.shape)))
    print("   MIROVA en la tabla: VRP %s, Distancia_km %s | pixel mas caliente por indice (pico): C a %s km, M a %s km del crater" % (f["mirova_vrp"], f["mirova_dist"], f["pico_C_dist"], f["pico_M_dist"]))
