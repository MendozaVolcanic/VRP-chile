# -*- coding: utf-8 -*-
# S197 (A116): el brazo C movió la caja? Cuenta, en volcanes con el cráter fuera de la celda central, las pasadas donde
# el diagnóstico de C (umbrales o celda decisiva) difiere del de A, y el margen máximo de C. Sólo lectura.
# Uso: python control_c_actua.py <salida_ab_caja>
import sys, json, collections
from pathlib import Path
pas = [p for p in json.load(open(Path(sys.argv[1]) / "x" / "p1_resultados_0.json", encoding="utf-8"))["pasadas"]
       if p.get("estado") == "ok" and not p["celda_central"]]
por = collections.defaultdict(lambda: [0, 0, 0])
cerca = []
for p in pas:
    a, c = p["brazos"]["A"], p["brazos"]["C"]
    if a is None or c is None:
        continue
    por[p["volcan"]][1] += 1
    if json.dumps(a.get("s1"), sort_keys=True) != json.dumps(c.get("s1"), sort_keys=True):
        por[p["volcan"]][0] += 1
    cd = ((c.get("s1") or {}).get("celda_decisiva") or {})
    ca = ((a.get("s1") or {}).get("celda_decisiva") or {})
    if cd.get("margen") and cd["margen"] >= 0.9 and c.get("n", 0) == 0:
        cerca.append((p["volcan"], p["dt"], ca.get("margen"), cd.get("margen")))
print("volcán: [pasadas con diagnóstico de C distinto de A, pasadas]")
for v, x in sorted(por.items()):
    print("  ", v, x[:2])
print("pasadas sin alerta con margen de C >= 0,9 (casi alerta):", len(cerca))
for x in cerca:
    print("   %s %s margen A %s, margen C %s" % x)
