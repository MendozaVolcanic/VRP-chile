# -*- coding: utf-8 -*-
"""S150, sonda de los tres campos. Paso 0b (local): la georreferencia de la grilla de MIROVA por volcan.

POR QUE. El campo (c) de la sonda es el granulo interpolado a la grilla exacta en que MIROVA publica su
GeoTIFF de VIIRS 375. Si esa grilla es la MISMA en todas las pasadas de un volcan (MIROVA recorta un
marco fijo de 50 x 50 km alrededor de su centro), el campo (c) se puede construir para TODAS las
pasadas, incluso las de abril que no tienen TIF; el TIF de la misma pasada se usa solo para validar.
Este script lo comprueba leyendo la cabecera de TODOS los TIF de VIIRS 375 que hay en disco (no baja
nada), y escribe plantillas_tif.json con la grilla geografica de cada volcan.

A106: la grilla UTM nativa de 375 m solo existio del 2026-09-14 06:36 al 2026-09-15 06:24. Esos TIF
se cuentan aparte y NO entran en la plantilla (la ventana de la sonda es abril a agosto).

  python plantillas_tif.py --dir <carpeta con data/tif/...> --indice <index.csv>
"""
import argparse, collections, io, json, sys
from pathlib import Path

import pandas as pd
import rasterio

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
TIF2VOL = {"ChillanNevadosde": "NevadosDeChillan"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--indice", required=True)
    a = ap.parse_args()
    ix = pd.read_csv(a.indice)
    ix = ix[(ix.sensor == "VIIRS375") & (ix.size_bytes > 0)]
    geos = collections.defaultdict(collections.Counter)
    ejemplo = {}
    n_leidos = n_faltan = 0
    for _, x in ix.iterrows():
        f = Path(a.dir) / x.tif_path
        if not f.exists():
            n_faltan += 1
            continue
        with rasterio.open(f) as ds:
            t = ds.transform
            clave = (str(ds.crs), ds.shape[0], ds.shape[1], round(t.a, 9), round(t.b, 9), round(t.c, 7),
                     round(t.d, 9), round(t.e, 9), round(t.f, 7))
        vol = TIF2VOL.get(x.volcano, x.volcano)
        geos[vol][clave] += 1
        ejemplo.setdefault((vol, clave), (x.tif_path, x.acquisition_utc))
        n_leidos += 1
    print("TIF leidos:", n_leidos, "| en el indice pero no en disco:", n_faltan)
    plantillas = {}
    for vol, c in sorted(geos.items()):
        geo4326 = {k: n for k, n in c.items() if k[0] == "EPSG:4326"}
        otras = {k: n for k, n in c.items() if k[0] != "EPSG:4326"}
        print(vol, "| grillas EPSG:4326 distintas:", len(geo4326), dict((str(k[1:]), n) for k, n in geo4326.items()),
              "| otras (UTM, A106):", {k[0]: n for k, n in otras.items()})
        if len(geo4326) != 1:
            print("  NO UNICA: el volcan queda sin plantilla")
            continue
        k = next(iter(geo4326))
        plantillas[vol] = {"crs": k[0], "alto": k[1], "ancho": k[2],
                           "transform": [k[3], k[4], k[5], k[6], k[7], k[8]],
                           "n_tif": geo4326[k], "ejemplo": ejemplo[(vol, k)][0]}
    (AQUI / "plantillas_tif.json").write_text(json.dumps(plantillas, indent=1, ensure_ascii=False), encoding="utf-8")
    print("escrito plantillas_tif.json con", len(plantillas), "volcanes")


if __name__ == "__main__":
    main()
