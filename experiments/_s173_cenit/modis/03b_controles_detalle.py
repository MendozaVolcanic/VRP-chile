# -*- coding: utf-8 -*-
"""03b (S173): detalle de dos controles de 03: (a) las pasadas donde V0 y el port del lote difieren en VRP a 1e-3;
(b) las pasadas donde G5 cambia y V0 no detecta. Lee 03_salida.json. Uso: python -B 03b_controles_detalle.py"""
import json, math
from pathlib import Path
A = Path(__file__).resolve().parent
d = json.load(open(A / "03_salida.json", encoding="utf-8"))["pasadas"]
L = []
for i, e in d.items():
    v0 = e["brazos"]["V0"]["vrp_mw"] or 0
    pv = e["port_vrp"]
    pvr = None if pv is None or (isinstance(pv, float) and math.isnan(pv)) else round(pv, 3)
    if pvr is None and not e["brazos"]["V0"]["npix"]:
        continue   # sin detección en los dos: el port guarda None, no es diferencia
    if pvr is None or abs(v0 - pvr) > 0.001:
        L.append(f"(a) id {i} {e['volcan']} {e['hora']} V0 npix {e['brazos']['V0']['npix']} vrp {v0} | port npix {e['port_npix']} vrp {pv}")
for i, e in d.items():
    g = e["brazos"]["G5"]
    if g["npix"] and not e["brazos"]["V0"]["npix"]:
        L.append(f"(b) id {i} {e['volcan']} {e['hora']} z {e['z']} clase {e['clase']} G5 npix {g['npix']} vrp {g['vrp_mw']} dc {g['distance_class']} pub {g.get('publica')}")
print("\n".join(L)); (A / "03b_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
