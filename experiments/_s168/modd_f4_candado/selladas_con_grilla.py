# -*- coding: utf-8 -*-
"""S170: ¿cuántas pasadas con grilla del censo sacó el propio port del censo como «escena inválida»? En t1 el runner
sacó 24 pasadas con grilla del censo por `escena_invalida` y la identidad las declaró del mismo gránulo; la regla
sellada N-01 (§8.2) las cuenta como «selladas sin explicar» y deja la identidad en rojo. Aquí se mira si el censo
llegó al mismo motivo en esas mismas pasadas (port fisica motivo_vacio), en todo el censo y en las de t1.
Uso: python selladas_con_grilla.py <carpeta del censo> <carpeta de la tanda> (escribe a stdout)
"""
import ast
import glob
import json
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[3]
censo, tanda = sys.argv[1], sys.argv[2]
pob = {(p["vol"], p["dt"]): p for p in
       json.load(open(RAIZ / "experiments/_s166_modd_f4/poblacion_f4.json", encoding="utf-8"))["pasadas"]}
motivo_censo = {}
for a in glob.glob(censo + "/run_*/*/ab_parte*.jsonl"):
    for x in open(a, encoding="utf-8"):
        r = json.loads(x)
        if r.get("tipo") != "record":
            continue
        port = r.get("port")
        port = ast.literal_eval(port) if isinstance(port, str) else (port or {})
        motivo_censo[(r["vol"], r["dt"])] = (port.get("fisica") or {}).get("motivo_vacio")
con_grilla = [k for k, p in pob.items() if p.get("grilla_censo")]
print("censo: pasadas con grilla %d; con motivo del port del censo: %s" % (
    len(con_grilla), dict(Counter(str(motivo_censo.get(k)) for k in con_grilla))))
rec = [json.loads(x) for a in glob.glob(tanda + "/*-parte-*/f4_parte*.jsonl") for x in open(a, encoding="utf-8")]
rec = [r for r in rec if r.get("tipo") == "record"]
sel = [(r["vol"], r["dt"], r["motivo"]) for r in rec if pob[(r["vol"], r["dt"])].get("grilla_censo") and r["motivo"]]
print("tanda: pasadas con grilla del censo y motivo sellado del runner: %d" % len(sel))
print("  el censo llegó al mismo motivo en: %d; distinto: %s" % (
    sum(1 for v, d, m in sel if motivo_censo.get((v, d)) == m),
    [(v, d, m, motivo_censo.get((v, d))) for v, d, m in sel if motivo_censo.get((v, d)) != m]))
