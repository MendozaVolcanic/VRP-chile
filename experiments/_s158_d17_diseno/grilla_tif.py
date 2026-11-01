# -*- coding: utf-8 -*-
"""S158, diseño D17: la grilla UTM de MIROVA leída de sus propios GeoTIFF de VIIRS 375.

POR QUÉ: D17 da por hecho que MIROVA centra su grilla en `mirova_center` (derivado en S80 de los KMZ,
que son reproyecciones geográficas). Entre el 2026-09-14 06:36 y el 2026-09-15 06:24 MIROVA publicó sus
TIF de VIIRS 375 en su grilla UTM nativa (A106). Este script baja uno por volcán (dos en cuatro de ellos,
para ver si la grilla es fija) y mide: EPSG, tamaño y origen de la grilla, distancia de su centro a
`mirova_center`, a `vent` y a `lat/lon` de `volcanoes.yaml`, convergencia de meridianos, y la firma del
remuestreo (fracción de celdas vecinas con valor idéntico y celdas vacías).

Lee el archivo de TIF por la API de GitHub (nunca `git pull` del repo de 17 GB, regla S143).
Uso: python -I grilla_tif.py <raiz del repo> <carpeta temporal>
"""
import glob
import math
import os
import subprocess
import sys

import numpy as np
import rasterio
import yaml
from pyproj import Transformer

REPO_TIF = "MendozaVolcanic/mirova-tif-archive"
# un TIF UTM por volcán (y un segundo en cuatro), dentro de la ventana UTM de A106
TIFS = [
    "Chaiten/20260914_064201", "ChillanNevadosde/20260915_052402", "Copahue/20260915_052402",
    "Isluga/20260914_063601", "Lascar/20260914_063601", "Lascar/20260915_061801",
    "Lastarria/20260914_063601", "Llaima/20260914_064201", "Llaima/20260915_052402",
    "PlanchonPeteroa/20260914_063601", "PuyehueCordonCaulle/20260914_064201",
    "Tupungatito/20260914_063601", "Tupungatito/20260915_043601",
    "Villarrica/20260915_052402", "Villarrica/20260915_061801",
]
ALIAS = {"ChillanNevadosde": "NevadosDeChillan"}


def bajar(ruta, destino):
    if os.path.exists(destino) and os.path.getsize(destino) > 0:
        return
    datos = subprocess.run(["gh", "api", "-H", "Accept: application/vnd.github.raw",
                            f"repos/{REPO_TIF}/contents/data/tif/{ruta}_VIIRS375.tif"],
                           capture_output=True, check=True).stdout
    with open(destino, "wb") as f:
        f.write(datos)


def main(repo, tmp):
    os.makedirs(tmp, exist_ok=True)
    vols = {v["name"]: v for v in yaml.safe_load(open(os.path.join(repo, "volcanoes.yaml"),
                                                      encoding="utf-8"))["volcanoes"]}
    for ruta in TIFS:
        f = os.path.join(tmp, ruta.replace("/", "_") + ".tif")
        bajar(ruta, f)
        nom = ruta.split("/")[0]
        v = vols[ALIAS.get(nom, nom)]
        with rasterio.open(f) as s:
            t, epsg, w, h, a = s.transform, s.crs.to_epsg(), s.width, s.height, s.read(1)
        if epsg == 4326:
            print(f"{ruta}: EPSG 4326, no es grilla UTM, se omite")
            continue
        cx, cy = t.c + t.a * w / 2, t.f + t.e * h / 2
        fwd = Transformer.from_crs(4326, epsg, always_xy=True)
        clon, clat = Transformer.from_crs(epsg, 4326, always_xy=True).transform(cx, cy)
        x2, y2 = fwd.transform(clon, clat + 0.1)
        iguales = np.r_[(a[:, 1:] == a[:, :-1]).ravel(), (a[1:, :] == a[:-1, :]).ravel()].mean()
        vacias = int((a <= 0).sum() + np.isnan(a).sum())
        print(f"{ruta}: EPSG {epsg}, {w}x{h}, celda {t.a:.1f} m, origen UL ({t.c:.1f}, {t.f:.1f}), "
              f"centro ({clat:.5f}, {clon:.5f}), convergencia {math.degrees(math.atan2(x2 - cx, y2 - cy)):+.2f} grados")
        print(f"    firma: celdas vecinas iguales {100 * iguales:.1f} %, celdas vacias {vacias} de {a.size}")
        for et, la, lo in (("mirova_center", v.get("mirova_center_lat"), v.get("mirova_center_lon")),
                           ("vent", v.get("vent_lat"), v.get("vent_lon")),
                           ("lat/lon", v.get("lat"), v.get("lon"))):
            x, y = fwd.transform(lo, la)
            print(f"    {et:14s} a {math.hypot(x - cx, y - cy):6.0f} m del centro (dx {x - cx:+6.0f}, dy {y - cy:+6.0f})")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
