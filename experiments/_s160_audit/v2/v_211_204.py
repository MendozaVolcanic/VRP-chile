#!/usr/bin/env python
"""211: horas integradas por la VRE del tablero contando SOLO los records que la VRE suma (isValidDetection,
no artefacto, magnitud > 0, aproximado con el predicado de publicacion del banco: exige ademas summit).
204: records sin distance_class (solo ahi el tablero usa pixels[0].dist_km para la clase).
Pregunta 1: si cada record integrara 6 h y hubiera >4 por dia, horas/dia > 24 lo veria. Control: las
horas con TODOS los records (lo que conto el auditor) deben reproducir ~62,5 h/dia.
Ventanas: 2026-09-18..2026-10-21 y 2026-03-01..2026-10-21, nocturnos (cargar_nuestros).
"""
import json, os, sys
from collections import Counter, defaultdict
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
SNAP = Path(r"D:\vrp-trabajo\temporales\s160_audit\main")
sys.path.insert(0, str(SNAP / "scripts")); sys.path.insert(0, str(SNAP))
os.environ["VRP_PROFILE"] = "mirova_equivalent"
import banco_paridad as bp
coords = bp._coords_por_volcan(); inner = bp.inner_desde_html(); L = []
def p(*a):
    s = " ".join(str(x) for x in a); print(s); L.append(s)
for w in [("2026-09-18", "2026-10-21"), ("2026-03-01", "2026-10-21")]:
    recs = bp.cargar_nuestros(coords, inner, w)
    todos = Counter((r["vol"], r["noche"]) for r in recs)
    pub = Counter((r["vol"], r["noche"]) for r in recs if r["pub"])
    dias_vol = len(todos)
    p(f"== {w} dias-volcan con records {dias_vol}")
    p(f"  CONTROL todos los records: {6*sum(todos.values())/dias_vol:.1f} h/dia")
    p(f"  solo los que suma la VRE: {6*sum(pub.values())/dias_vol:.1f} h/dia (sobre todos los dias-volcan)")
    nd = Counter(pub.values())
    p(f"  dias-volcan con >=1 publicado {len(pub)}; distribucion n publicados/dia {dict(sorted(nd.items()))}")
    p(f"  dias con >4 publicados (VRE >24 h ese dia): {sum(v for k,v in nd.items() if k>4)}")
    por = defaultdict(lambda: [0, 0])
    for (v, d), n in todos.items():
        por[v][0] += 1; por[v][1] += pub.get((v, d), 0)
    for v, (d, n) in sorted(por.items()):
        p(f"   {v:22s} dias={d} publicados={n} h_integradas/dia={6*n/d:.1f}")
# 204
c = Counter()
for v in bp.VOLS:
    for r in json.load(open(SNAP/"data"/"mirova_equivalent"/f"{v}.json", encoding="utf-8"))["records"]:
        c["n"] += 1
        if not r.get("distance_class"): c["sin_distance_class"] += 1
p("204: records Tier A", dict(c))
Path(__file__).with_name("v_211_204_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
