# -*- coding: utf-8 -*-
"""S178: las diferencias de C-montaje en VIIRS 375, contra la banda de triangulación del propio port C13 de V375-E.

POR QUÉ. Las 12 diferencias de montaje_dm_salida.json son todas de VRP en VIIRS 375, con las mismas celdas y las mismas
temperaturas. El port de V375-E guardó `vrp_banda` (VRP mínimo y máximo con 20 semillas de jitter en la triangulación
del fondo). Este script dice cuántas caen dentro, con 0,0005 MW de holgura por el redondeo a 0,001 MW del record.
INFORMA: la declaración de C-montaje no usa esta banda en VIIRS 375; usarla es decisión de Nicolás.

Uso: python banda_v375.py montaje_dm_salida.json CARPETA_V375E [CARPETA_V375E ...]
"""
import glob
import json
import sys

d = json.load(open(sys.argv[1], encoding="utf-8"))
quiero = {(x["pasada"].split("|")[0], x["pasada"].split("|")[2]): x["via"]["vrp"] for x in d["diferencias"]
          if x["origen"] == "V375-E" and x["via"] is not None}
vistos, dentro = set(), 0
for c in sys.argv[2:]:
    for f in sorted(glob.glob(c + "/**/resultados_VIIRS375_*.json", recursive=True)):
        for e in json.load(open(f, encoding="utf-8")):
            k = (e["volcan"], e["hora_utc"][:16])
            if k in quiero and k not in vistos:
                vistos.add(k)
                b, v = e["port"]["C13"]["vrp_banda"], quiero[k]
                ok = b[0] - 0.0005 <= v <= b[1] + 0.0005
                dentro += ok
                print(f"{k[0]} {k[1]} via {v} banda [{b[0]:.4f}, {b[1]:.4f}] ancho {b[1]-b[0]:.4f} "
                      f"{'DENTRO' if ok else 'FUERA'}")
print(f"diferencias de VIIRS 375: {len(quiero)}; con banda encontrada: {len(vistos)}; dentro: {dentro}")
