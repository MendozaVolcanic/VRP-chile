# -*- coding: utf-8 -*-
"""Frente 4 S155: separa los records por detector (K vs C0) segun processed_utc y mide
los marcadores del Test 1 en cada grupo.

PREGUNTA 1 (si lo medido estuviera roto, lo veria?): si K no se hubiera aplicado a los
records reprocesados, triggered_test1 / n_test1_pixels / final_hotspot_source=='test1'
seguirian > 0 en el grupo K. Lo veria.
PREGUNTA 2 (instrumento muerto?): CONTROL POSITIVO = el grupo C0 (processed_utc anterior al
merge #850) debe mostrar triggered_test1 > 0. Si el instrumento no leyera el campo, ambos
grupos darian 0 y el script lo marca SIN DATO.
Denominador: records de los 11 Tier A en data/mirova_equivalent, por sensor.
"""
import json, sys, io
from pathlib import Path
from collections import Counter, defaultdict
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]
TIER_A = ["Lascar","Lastarria","Isluga","NevadosDeChillan","Llaima","Villarrica","Chaiten",
          "PlanchonPeteroa","Copahue","Tupungatito","PuyehueCordonCaulle"]
MERGE_K = "2026-10-18T09:57:30"
VENT_INI, VENT_FIN = "2026-09-18", "2026-10-19"
def cargar(v):
    p = ROOT/"data/mirova_equivalent"/f"{v}.json"
    if not p.exists():
        cand = [q for q in (ROOT/"data/mirova_equivalent").glob("*.json") if q.stem.lower().startswith(v.lower()[:6])]
        print("  aviso: no existe", v, "candidatos", [c.name for c in cand]); return []
    return json.load(open(p, encoding="utf-8"))["records"]
stats = defaultdict(Counter)
for v in TIER_A:
    for r in cargar(v):
        pu = (r.get("processed_utc") or "")[:19]
        dt = (r.get("datetime_utc") or "")[:19]
        grupo = "K" if pu >= MERGE_K else "C0"
        en_vent = VENT_INI <= dt[:10] < VENT_FIN
        key = (grupo, "ventana30d" if en_vent else "fuera", r.get("sensor","?").replace("_NOAA20","").replace("_NOAA21","").replace("_SNPP",""))
        c = stats[key]
        c["n"] += 1
        c["triggered_test1"] += bool(r.get("triggered_test1"))
        c["n_test1_pixels>0"] += (r.get("n_test1_pixels") or 0) > 0
        c["src_test1"] += r.get("final_hotspot_source") == "test1"
        c["vrp>0"] += (r.get("vrp_mw") or 0) > 0
for k in sorted(stats):
    c = stats[k]
    print(k, dict(c))
# chequeo de cobertura: records dentro de la ventana procesados ANTES del merge (no reprocesados)
