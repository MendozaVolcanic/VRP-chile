# -*- coding: utf-8 -*-
"""S194: cruce de la partición con el marcador «también hay calor en la cumbre» (#1091).

POR QUÉ: «publicada lejana con alertados en el cráter» de la partición es el mismo predicado del marcador
(distance_class far y algún alertado a dist_km <= inner_radius_km). En la ventana del marcador (noches 2026-03-01 a
2026-11-18) y sin Cordón Caulle, el marcador cuenta 214 de sus 218 (Cordón Caulle V375 aporta 4) entre las lejanas
PUBLICABLES (con «Incluir lejanas», magnitud > 0, no artefacto). La partición cuenta todas las lejanas, publicables o
no, así que debe dar 214 o más; si da menos, uno de los dos instrumentos está mal.

Uso: python experiments/_s194_areas/cruce_marcador.py [--salida DIR]
"""
import argparse
import collections
import csv
import gzip
import sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", default="D:/vrp-trabajo/temporales/s194_areas")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    c = collections.Counter()
    with gzip.open(Path(args.salida) / "pasadas.csv.gz", "rt", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if not ("2026-03-01" <= r["noche"] <= "2026-11-18"):
                continue
            c["con_alertados"] += 1
            if r["distance_class"] == "far":
                c["lejanas"] += 1
                if int(r["crater_n"]) > 0:
                    c["lejanas_con_crater"] += 1
                    c[f"lejanas_con_crater_{r['familia']}"] += 1
    print("Ventana del marcador (noches 2026-03-01 a 2026-11-18), 10 volcanes sin Cordón Caulle:", dict(c))
    print("Marcador #1091 en esa ventana sin Cordón Caulle: 214 lejanas publicables con marca (218 menos 4 de PCC V375).")


if __name__ == "__main__":
    main()
