# -*- coding: utf-8 -*-
"""Contadores baratos sobre records escritos con K (processed_utc >= merge #850) en la ventana
2026-09-18 a 2026-10-18, y sobre records C0 de la ventana previa (2026-08-18 a 2026-09-17):
  D31: diag_n_bt_path > 0 (camino BT apagado: debe ser 0 en los dos)
  D23: n_nti_path > 0 (pixeles con NTI > K1; el paper los declara activos)
  D9/A23: primary_cluster.vrp_mw == 5,0 exacto (tope) y > 5 MW, solo en records con K
P1: un contador que deberia ser > 0 en algun lado (n_nti_path en C0) sirve de control positivo de que
el campo se lee. P2: 'sin campo' se cuenta aparte (SIN DATO)."""
import sys, io, json, collections
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[3]
VOLS = ["Lascar","Lastarria","Isluga","Tupungatito","PlanchonPeteroa","NevadosDeChillan","Llaima","Villarrica","Copahue","PuyehueCordonCaulle","Chaiten"]
MERGE = "2026-10-18T09:57:30"
def b(s):
    return "MODIS" if s.startswith("MODIS") else ("VIIRS750" if s.endswith("_750") else "VIIRS375")
c = collections.Counter(); topados = []
for v in VOLS:
    for r in json.load(open(ROOT/"data/mirova_equivalent"/f"{v}.json", encoding="utf-8"))["records"]:
        dt = r.get("datetime_utc", "")[:10]; k = (r.get("processed_utc") or "")[:19] >= MERGE
        if "2026-09-18" <= dt <= "2026-10-18" and k: g = "K"
        elif "2026-08-18" <= dt <= "2026-09-17" and not k: g = "C0"
        else: continue
        s = b(r["sensor"]); c[(g, s, "n")] += 1
        for campo in ("diag_n_bt_path", "n_nti_path"):
            if campo not in r: c[(g, s, campo + "_sin_campo")] += 1
            elif (r[campo] or 0) > 0: c[(g, s, campo)] += 1
        pv = (r.get("primary_cluster") or {}).get("vrp_mw")
        if pv == 5.0: c[(g, s, "tope_5")] += 1
        if pv is not None and pv > 5.0: c[(g, s, "sobre_5")] += 1
        if g == "K" and pv == 5.0: topados.append((v, r["datetime_utc"], r["sensor"], r.get("distance_class")))
for g in ("C0", "K"):
    for s in ("MODIS", "VIIRS375", "VIIRS750"):
        print(g, s, {k[2]: n for k, n in c.items() if k[0] == g and k[1] == s})
print("topados 5,0 con K:", topados)
