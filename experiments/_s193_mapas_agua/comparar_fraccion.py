# -*- coding: utf-8 -*-
"""S193 mapas: ¿la capa de agua del tablero (frontend/agua/*.geojson, simplificada) clasifica cada píxel alertado
igual que la máscara JRC a 30 m de experiments/_s193_lagos/medir_agua.py?

POR QUÉ. El tablero marca «sobre agua» cuando 50 % o más de la celda del píxel es agua, recortando los polígonos de la
capa (frontend/agua.js). Los polígonos se simplificaron y se les quitaron los charcos chicos para que pesen poco; eso
puede mover la fracción de una celda en el borde del 50 %. Antes de mostrar la marca hay que saber cuántos píxeles
cambian de clase frente a la medición del informe (pixeles.csv, 41.989 píxeles de la vía).

La fracción se calcula como la hará el navegador: área de (polígonos ∩ celda) / área de la celda, en grados, con la
celda de lado = paso del sensor centrada en el píxel (lat ± lado/2/111320, lon ± lado/2/(111320·cos lat)).

Uso: python comparar_fraccion.py <pixeles.csv> <dir_geojson>  > comparar_fraccion.txt
"""
import csv
import json
import math
import os
import sys
from collections import Counter, defaultdict

from shapely.geometry import box, shape
from shapely.strtree import STRtree

PASO_M = {"MODIS": 1000.0, "V750": 750.0, "V375": 375.0}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    pix_csv, dir_gj = sys.argv[1], sys.argv[2]
    capas = {}
    for f in os.listdir(dir_gj):
        if f.endswith(".geojson"):
            gj = json.load(open(os.path.join(dir_gj, f), encoding="utf-8"))
            polys = [shape(ft["geometry"]) for ft in gj["features"]]
            p = gj["properties"]
            dlat = p["media_ventana_km"] / 111.32
            dlon = p["media_ventana_km"] / (111.32 * math.cos(math.radians(p["lat"])))
            marco = box(p["lon"] - dlon, p["lat"] - dlat, p["lon"] + dlon, p["lat"] + dlat)
            capas[f[:-8]] = (polys, STRtree(polys) if polys else None, marco)
    tabla = Counter()
    por_volcan = defaultdict(Counter)
    difs = []
    fuera = 0
    for row in csv.DictReader(open(pix_csv, encoding="utf-8")):
        v = row["volcan"]
        lat, lon = float(row["lat"]), float(row["lon"])
        lado = PASO_M[row["familia"]]
        hl = lado / 2 / 111320.0
        hn = lado / 2 / (111320.0 * math.cos(math.radians(lat)))
        celda = box(lon - hn, lat - hl, lon + hn, lat + hl)
        polys, arbol, marco = capas[v]
        if not marco.contains(celda):
            fuera += 1
            continue
        a = 0.0
        if arbol is not None:
            for i in arbol.query(celda):
                a += polys[i].intersection(celda).area
        f_capa = a / celda.area
        f_jrc = float(row["frac_agua"])
        c_jrc, c_capa = f_jrc >= 0.5, f_capa >= 0.5
        tabla[(c_jrc, c_capa)] += 1
        por_volcan[v][(c_jrc, c_capa)] += 1
        difs.append(abs(f_capa - f_jrc))
    n = sum(tabla.values())
    print(f"píxeles comparados: {n} (fuera de la ventana de la capa: {fuera})")
    print(f"agua en JRC 30 m y en la capa:   {tabla[(True, True)]}")
    print(f"tierra en las dos:               {tabla[(False, False)]}")
    print(f"agua sólo en JRC (capa no marca): {tabla[(True, False)]}")
    print(f"agua sólo en la capa (marca de más): {tabla[(False, True)]}")
    print(f"acuerdo: {(tabla[(True, True)] + tabla[(False, False)]) / n * 100:.3f} %")
    difs.sort()
    print(f"|fracción capa − fracción JRC|: mediana {difs[len(difs)//2]:.4f}, p99 {difs[int(len(difs)*0.99)]:.4f}, "
          f"máx {difs[-1]:.4f}")
    print("volcanes con desacuerdos (jrc_agua_capa_tierra, jrc_tierra_capa_agua, agua_en_ambas):")
    for v, c in sorted(por_volcan.items()):
        if c[(True, False)] or c[(False, True)]:
            print(f"  {v}: {c[(True, False)]}, {c[(False, True)]}, {c[(True, True)]}")


if __name__ == "__main__":
    main()
