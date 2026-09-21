# -*- coding: utf-8 -*-
"""Verificador S149. De donde salen las 32 pasadas de diferencia entre las 141 de c3 y las 109 de c4."""
import json, sys, io, collections
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
EXP = Path(__file__).resolve().parent.parent
T = json.loads((EXP / "_s148_verificador_resultado" / "tabla.json").read_text(encoding="utf-8"))
S = json.loads((EXP / "_s149_costo_oculto" / "sin_info_v375.json").read_text(encoding="utf-8"))
B = "_s146_ab_sin_test1"
lab_noche = collections.defaultdict(set)
for k, v in T.items():
    vol, b, dt = k.split("|"); lab_noche[(vol, dt[:10])].add((b, v[B]["lab"]))
c = collections.Counter()
for r in S:
    if not r["rut"]: continue
    l = lab_noche[(r["vol"], r["dt"][:10])]
    pos_any = any(x[1] == "pos" for x in l); far375 = ("VIIRS375", "far_ref") in l
    c["con pos esa noche (109 del doc)" if pos_any else ("sin pos, con far_ref V375 nuestro" if far375 else "sin pos ni far_ref nuestro: alerta o FP de MIROVA sin record nuestro pareado")] += 1
print(dict(c))
rest = [r for r in S if r["rut"] and not any(x[1] == "pos" for x in lab_noche[(r["vol"], r["dt"][:10])])]
print("las 32: B publica %d | F publica %d" % (sum(r["pB"] for r in rest), sum(r["pF"] for r in rest)))
