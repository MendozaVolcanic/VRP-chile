# -*- coding: utf-8 -*-
"""d02: A94 (S136: '1 noche util sobre 946', '45 noches sin nada = el FN real') y A98 (S139: '874 de 877').
Que cuenta cada 'noche'? Reconstruye impacto_neto.py (S136) con corte GT 2026-09-07 y separa las fechas UTC cuyo
UNICO respaldo MIROVA es una alerta DIURNA (hora UTC fuera de 03-09; A76: el pipeline es night-only).
Instrumento: (1) si el pareo estuviera roto, el control 'reproduce 946/897/4/45' fallaria; (2) muerto => 0 noches, se ve.
"""
import io, sys, os, json
from collections import defaultdict
from dlib import *
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, ROOT); os.environ["VRP_PROFILE"] = "mirova_equivalent"
from pipeline.mirova_csv_loader import load_mirova_alertas
SNAP = os.path.join(ROOT, "data", "mirova_reference", "mirova_v1_snapshot")
al = load_mirova_alertas(cons_path=os.path.join(SNAP, "registro_vrp_consolidado.csv"), ocr_path=os.path.join(SNAP, "registro_vrp_ocr.csv"))
FIN = "2026-09-07"
def noct(f):
    try: return 3 <= int(f[11:13]) <= 9
    except Exception: return None
mir = defaultdict(lambda: defaultdict(list))
for a in al:
    f = a.get("fecha_utc") or ""
    if f and f[:10] <= FIN and a["volcano"] in VOLS: mir[a["volcano"]][f[:10]].append(noct(f))
D = cargar()
T = defaultdict(int); porvol = {}
for vol in VOLS:
    inn = INNER[vol]; pub = set(); ocu = set(); algo = set(); dash = set()
    for r in D[vol]:
        f = r["datetime_utc"][:10]
        if f > FIN: continue
        algo.add(f)
        pc = r.get("pc") or {}; cd = pc.get("centroid_dist_km"); v = pc.get("vrp_mw") or 0
        if r.get("distance_class") == "summit" and ((r.get("vrp_mw") or 0) > 0 or r.get("triggered_test1")): dash.add(f)
        if v <= 0 or cd is None: continue
        if r.get("distance_class") == "summit" and cd <= inn: pub.add(f)
        elif r.get("distance_class") == "far" and cd <= inn: ocu.add(f)
    row = defaultdict(int)
    for n, horas in mir[vol].items():
        solo_dia = all(h is False for h in horas)
        row["fechas_mirova"] += 1
        row["fechas_solo_alerta_diurna"] += solo_dia
        if n in pub: row["publica"] += 1
        elif n in ocu: row["oculta"] += 1
        else:
            row["sin_nada"] += 1
            row["sin_nada_solo_diurna"] += solo_dia
            row["sin_nada_pero_dashboard_summit"] += (n in dash)
            row["sin_nada_sin_ningun_record"] += (n not in algo)
        if not solo_dia:
            row["NOCT_total"] += 1
            if n in pub: row["NOCT_publica"] += 1
            elif n in ocu: row["NOCT_oculta"] += 1
            else: row["NOCT_sin_nada"] += 1
    porvol[vol] = dict(row)
    for k, v in row.items(): T[k] += v
out = {"corte_gt": FIN, "total": dict(T), "por_volcan": porvol,
       "recall_S136_reconstruido_pct": round(100*T["publica"]/T["fechas_mirova"], 1),
       "recall_solo_noches_con_alerta_nocturna_pct": round(100*T["NOCT_publica"]/T["NOCT_total"], 1)}
json.dump(out, open("d02_noches_A94_A98.json", "w"), indent=1, ensure_ascii=False)
print(json.dumps(out["total"], indent=1)); print(out["recall_S136_reconstruido_pct"], out["recall_solo_noches_con_alerta_nocturna_pct"])
for v in VOLS: print(v, porvol[v])
