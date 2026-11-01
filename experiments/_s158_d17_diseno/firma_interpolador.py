# -*- coding: utf-8 -*-
"""S158, diseño D17: firma de tres remuestreos sobre un barrido sintético.

POR QUÉ: los GeoTIFF UTM de MIROVA (14 y 15 de septiembre de 2026) no repiten ningún valor entre celdas
vecinas aun en pasadas de cenit 60 a 65 grados (`grilla_tif.py`). Este script mide qué firma deja cada
remuestreo candidato, para saber cuál es compatible con eso, y cuánto conserva la energía de un foco
sub-píxel (lo que el paper dice que el remuestreo corrige).

Remuestreos:
  F70     el de `pipeline/regrid.py` (cada muestra va a la celda que contiene su centro; gana la más
          cercana al centro de la celda; las celdas sin muestra quedan vacías).
  vecino  vecino más cercano inverso (cada celda toma la muestra más cercana a su centro).
  lineal  interpolación lineal de los datos dispersos (triangulación de Delaunay, scipy griddata).

Barrido sintético: muestras en una malla regular girada 17 grados, espaciado dx por dy (huella del
píxel), fondo 0,10 W m-2 sr-1 um-1 con ruido de 0,003, y un foco que suma 0,50 a una sola muestra (foco
sub-píxel: el sensor ve la media de la huella). Energía nativa = exceso de esa muestra por el área de su
huella (dx·dy). Energía remuestreada = suma del exceso de las celdas por el área de la celda.

Sin datos reales ni red: corre en un segundo. Uso: python -I firma_interpolador.py <raiz del repo>
"""
import sys
import math

import numpy as np
from scipy.interpolate import griddata
from scipy.spatial import cKDTree

sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else ".")
from pipeline.regrid import regrid_to_utm  # noqa: E402

CLAT, CLON = -36.86, -71.38
KX, KY = 111.32 * math.cos(math.radians(CLAT)), 111.32
RNG = np.random.default_rng(158)


def barrido(dx, dy, rot=17.0, semi=30.0):
    n = int(semi / min(dx, dy))
    U, V = np.meshgrid(np.arange(-n, n) * dx, np.arange(-n, n) * dy)
    a = math.radians(rot)
    X = U * math.cos(a) - V * math.sin(a)
    Y = U * math.sin(a) + V * math.cos(a)
    L = 0.10 + RNG.normal(0, 0.003, X.shape)
    # foco en la muestra más cercana a (0,4 km, 0,3 km) del centro: no cae justo en un borde de celda
    k = np.unravel_index(np.argmin((X - 0.4) ** 2 + (Y - 0.3) ** 2), X.shape)
    L[k] += 0.50
    return X, Y, L, (X[k], Y[k])


def malla(cell, half):
    n = int(round(2 * half / cell))
    ejes = (np.arange(n) + 0.5) * cell - half
    gx, gy = np.meshgrid(ejes, ejes[::-1])
    return gx, gy, n


def remuestrear(metodo, X, Y, L, cell, half):
    gx, gy, n = malla(cell, half)
    if metodo == "F70":
        lat, lon = CLAT + Y / KY, CLON + X / KX
        return regrid_to_utm(lat, lon, {"m": L, "t": L}, CLAT, CLON, cell_km=cell, half_km=half)["m"]
    pts = np.column_stack([X.ravel(), Y.ravel()])
    if metodo == "vecino":
        d, i = cKDTree(pts).query(np.column_stack([gx.ravel(), gy.ravel()]))
        return L.ravel()[i].reshape(n, n)
    if metodo == "lineal":
        return griddata(pts, L.ravel(), (gx, gy), method="linear")
    raise ValueError(metodo)


def firma(G, cell, foco_xy, half):
    vac = np.isnan(G).mean()
    iguales = np.nanmean(np.r_[(G[:, 1:] == G[:, :-1]).ravel(), (G[1:, :] == G[:-1, :]).ravel()])
    exceso = np.nan_to_num(G - 0.10)
    # energía del foco: suma del exceso en un radio de 3 km alrededor del foco (el ruido suma cero en media)
    gx, gy, _ = malla(cell, half)
    cerca = (gx - foco_xy[0]) ** 2 + (gy - foco_xy[1]) ** 2 <= 3.0 ** 2
    energia = exceso[cerca].sum() * cell * cell
    npix = int((exceso[cerca] > 0.05).sum())   # celdas sobre un umbral fijo de exceso (0,05)
    return vac, iguales, energia, npix


def main():
    print(__doc__.splitlines()[1])
    casos = [("VIIRS 375", 0.375, 25.125, [(0.375, 0.375), (0.55, 0.45), (0.79, 0.78)]),
             ("VIIRS 750", 0.75, 25.125, [(0.75, 0.75), (1.1, 0.9), (1.6, 1.6)]),
             ("MODIS", 1.0, 25.5, [(1.0, 1.0), (2.0, 1.4), (4.8, 2.0)])]
    print("%-10s %-11s %-7s %8s %9s %10s %6s" % ("sensor", "huella km", "metodo", "vacias", "iguales",
                                                "E/E_nat", "Npix"))
    for nombre, cell, half, huellas in casos:
        for dx, dy in huellas:
            X, Y, L, foco = barrido(dx, dy)
            e_nat = 0.50 * dx * dy
            for m in ("F70", "vecino", "lineal"):
                G = remuestrear(m, X, Y, L, cell, half)
                vac, ig, e, npix = firma(G, cell, foco, half)
                print("%-10s %4.2fx%-6.2f %-7s %7.1f%% %8.1f%% %10.2f %6d" % (
                    nombre, dx, dy, m, 100 * vac, 100 * ig, e / e_nat, npix))


if __name__ == "__main__":
    main()
