# -*- coding: utf-8 -*-
"""VB2: geometría de la grilla, de la celda del cráter y del ancla `pos_crater` (VB-01/07/16 de la v1).

Preguntas del instrumento. (1) Si pos_crater o celda_crater estuvieran corridos media celda, ¿se vería? Se recalcula por
una vía independiente (pyproj directo sobre volcanoes.yaml y la esquina de la grilla) y se compara contra los objetivos
del ensayo; control positivo: se corre el mismo cálculo con el signo de la fila invertido y tiene que dar DISTINTO.
(2) Si el instrumento estuviera muerto (sin objetivos), imprime 0 comparaciones y sale 1.
Además mide dónde cae el centro REAL del TIF en coordenadas de índice (la v2 usa C = 33 como «centro de la grilla»).
Uso: python geometria_ancla.py --arbol <arbol> --ens <ens con objetivos_ensayo.json>
"""
import argparse, json, sys
from pathlib import Path
import yaml
from pyproj import Transformer
ap = argparse.ArgumentParser(); ap.add_argument("--arbol", required=True); ap.add_argument("--ens", required=True)
a = ap.parse_args()
A = Path(a.arbol)
objs = json.loads((Path(a.ens) / "objetivos_ensayo.json").read_text(encoding="utf-8"))
vy = {v["name"]: v for v in yaml.safe_load((A / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanes" if False else "volcanoes"]}
vistos, n_ok, n_mal, n_inv = {}, 0, 0, 0
for o in objs:
    if o["volcan"] in vistos:
        continue
    g = o["grilla"]; v = vy[o["volcan"]]
    t = Transformer.from_crs("EPSG:4326", f"EPSG:{g['epsg']}", always_xy=True)
    x, y = t.transform(v.get("vent_lon", v["lon"]), v.get("vent_lat", v["lat"]))
    pos = [(g["ul_y"] - y) / 750.0 - 0.5, (x - g["ul_x"]) / 750.0 - 0.5]
    cel = [int(round(pos[0])), int(round(pos[1]))]
    xc, yc = t.transform(g["centro_lon"], g["centro_lat"])
    cen = [(g["ul_y"] - yc) / 750.0 - 0.5, (xc - g["ul_x"]) / 750.0 - 0.5]
    inv = [(y - g["ul_y"]) / 750.0 - 0.5, pos[1]]
    ok = all(abs(p - q) < 1e-6 for p, q in zip(pos, o["pos_crater"])) and cel == o["celda_crater"]
    n_ok += ok; n_mal += (not ok); n_inv += (abs(inv[0] - o["pos_crater"][0]) > 0.5)
    vistos[o["volcan"]] = (o["celda_crater"], [round(p, 3) for p in pos], [round(c, 3) for c in cen])
for k, v in sorted(vistos.items()):
    print(f"{k:22s} celda {v[0]} pos_crater {v[1]} centro_TIF_en_indices {v[2]}")
print(f"comparaciones {len(vistos)}: iguales {n_ok}, distintas {n_mal}; control positivo (fila invertida) distinto en {n_inv} de {len(vistos)}")
sys.exit(0 if vistos else 1)
