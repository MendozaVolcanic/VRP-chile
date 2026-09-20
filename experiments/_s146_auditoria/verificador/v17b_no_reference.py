# -*- coding: utf-8 -*-
"""V-17b: por que 33 'no_reference' tienen fila RUTINA a +-2 min. Hipotesis: (i) RUTINA con VRP>0, (ii) FALSO_POSITIVO del mismo
sensor en otra pasada de la misma fecha UTC, (iii) fila solo OCR. (1) roto? la suma de causas debe dar 33. (2) muerto? imprime n."""
import io, sys, json, datetime as dt
from collections import Counter, defaultdict
from vlib import *
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
R = referencia(); REF = defaultdict(list)
for f in R: REF[(f["vol"], f["b"])].append(f)
c = Counter(); ej = []
for v in VOLS:
    d = json.load(open(os.path.join(ROOT, "data", "clasificacion_referencia", v + ".json"), encoding="utf-8"))["clasificacion"]
    for clave, e in d.items():
        if e["valor"] != "no_reference": continue
        t, s = clave.split("|"); T = dt.datetime.fromisoformat(t); b = bucket(s)
        cerca = [f for f in REF[(v, b)] if abs((dt.datetime.fromisoformat(f["dt"]) - T).total_seconds()) <= 120]
        if not cerca: continue
        fp_noche = [f for f in REF[(v, b)] if f["fecha"] == t[:10] and f["tipo"].startswith("FALSO")]
        causa = ("RUTINA con VRP>0" if any((f["vrp"] or 0) > 0 for f in cerca) else
                 "FALSO_POSITIVO mismo sensor misma fecha UTC, otra pasada" if fp_noche else "otra")
        c[causa] += 1
        if len(ej) < 4: ej.append((v, clave, [(f["dt"], f["tipo"], f["vrp"], f["dist"]) for f in fp_noche][:2]))
print(sum(c.values()), dict(c)); [print(x) for x in ej]
