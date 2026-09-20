# -*- coding: utf-8 -*-
"""I-08. Cota: que le pasa a la tasa en negativos si las pasadas SIN fila de MIROVA hubieran sido negativos.
P1: es una cota, no una medicion: dice cuanto PODRIA moverse el numero, no cuanto se mueve.
P2: los conteos base (322/373, 133/622, 50/439) se reimprimen para verificar que el cache es el mismo.
"""
import sys, io, json, collections
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
A = Path(__file__).parent
RECS = json.load(open(A / "_cache_recs.json", encoding="utf-8"))
REF = [f for f in json.load(open(A / "_cache_ref.json", encoding="utf-8")) if not f["diurna"]]
claves = {(f["volcano"], f["sensor_bucket"], f["fecha_utc"][:16]) for f in REF}
ult = max(f["fecha_utc"] for f in REF if f["source"] == "CONS")[:16]
base = {"VIIRS375": (322, 373), "VIIRS750": (133, 622), "MODIS": (50, 439)}
for b, (a, n) in base.items():
    s = [r for r in RECS if r["b"] == b and (r["vol"], r["b"], r["dt"][:16].replace("T", " ")) not in claves and r["dt"][:16].replace("T", " ") <= ult]
    p = sum(r["pub"] for r in s)
    print(f"{b}: base {a}/{n} = {100*a/n:.1f}% | sin fila (antes del fin de la tabla): {len(s)}, publican {p} ({100*p/len(s):.1f}%)"
          f" | si TODAS fueran negativos: {100*(a+p)/(n+len(s)):.1f}% | si solo las que NO publicamos lo fueran (extremo): {100*a/(n+len(s)-p):.1f}%")
