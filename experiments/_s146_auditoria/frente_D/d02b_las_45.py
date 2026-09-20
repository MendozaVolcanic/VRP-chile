# -*- coding: utf-8 -*-
"""d02b: las 45 fechas 'sin nada' de S136: que son? Lista fecha, y cuantos volcanes Tier A tienen ALGUN record esa fecha
(si ninguno o pocos => hueco de cobertura del pipeline, no fallo de deteccion).
Instrumento: (1) si el conteo de records por fecha estuviera roto daria 0 en todas: se imprime el maximo para verlo. (2) idem."""
import io, sys, os, json
from collections import defaultdict, Counter
from dlib import *
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, ROOT); os.environ["VRP_PROFILE"] = "mirova_equivalent"
from pipeline.mirova_csv_loader import load_mirova_alertas
SNAP = os.path.join(ROOT, "data", "mirova_reference", "mirova_v1_snapshot")
al = load_mirova_alertas(cons_path=os.path.join(SNAP, "registro_vrp_consolidado.csv"), ocr_path=os.path.join(SNAP, "registro_vrp_ocr.csv"))
D = cargar(); FIN = "2026-09-07"
fechas = {v: Counter(r["datetime_utc"][:10] for r in D[v]) for v in VOLS}
vols_con_record = Counter()
for v in VOLS:
    for f in fechas[v]: vols_con_record[f] += 1
print("control: max volcanes con record en una fecha =", max(vols_con_record.values()))
mir = defaultdict(set)
for a in al:
    f = (a.get("fecha_utc") or "")[:10]
    if f and f <= FIN and a["volcano"] in VOLS: mir[a["volcano"]].add(f)
sin = [(f, v) for v in VOLS for f in mir[v] if f not in fechas[v]]
sin.sort()
res = [{"fecha": f, "volcan": v, "otros_tier_a_con_record_esa_fecha": vols_con_record.get(f, 0)} for f, v in sin]
print("n =", len(res))
print("por mes:", sorted(Counter(f[:7] for f, _ in sin).items()))
print("distribucion de 'otros Tier A con record esa fecha':", sorted(Counter(x["otros_tier_a_con_record_esa_fecha"] for x in res).items()))
for x in res: print(x["fecha"], x["volcan"], x["otros_tier_a_con_record_esa_fecha"])
json.dump(res, open("d02b_las_45.json", "w"), indent=1)
