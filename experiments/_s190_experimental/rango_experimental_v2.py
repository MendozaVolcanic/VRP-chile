# -*- coding: utf-8 -*-
"""S190: que hay hoy en data/experimental_v2 (la serie del laboratorio congelado en C0).

POR QUE. El encargo partia de que el perfil `experimental` no corre desde S101 (ultimo record 2026-08-25). Eso
es cierto de data/experimental/ (serie legacy de S15), no de data/experimental_v2/, que escribe a diario
.github/workflows/experimental-diario.yml desde S150. Este script lo deja medido: por volcan, cuantos records,
primera y ultima pasada, y cuantos con VRP > 0. Corre sobre el checkout (origin/main al momento de correrlo).
"""
import json, sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
SUB = sys.argv[1] if len(sys.argv) > 1 else "experimental_v2"  # otro subdir para comparar ventanas
TIER_A = {"Lascar", "PuyehueCordonCaulle", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa",
          "Chaiten", "Villarrica", "NevadosDeChillan", "Llaima", "Copahue"}
filas = []
print("subdir:", SUB)
for p in sorted((RAIZ / "data" / SUB).glob("*.json")):
    if p.stem not in TIER_A:
        continue
    r = json.loads(p.read_text(encoding="utf-8"))["records"]
    fechas = sorted(x["datetime_utc"] for x in r if x.get("datetime_utc"))
    pos = sum(1 for x in r if (x.get("vrp_mw") or 0) > 0)
    filas.append((p.stem, len(r), fechas[0] if fechas else "-", fechas[-1] if fechas else "-", pos))
print(f"{'volcan':22} {'records':>7} {'primera':>20} {'ultima':>20} {'vrp>0':>6}")
for f in filas:
    print(f"{f[0]:22} {f[1]:>7} {f[2][:19]:>20} {f[3][:19]:>20} {f[4]:>6}")
print("TOTAL", sum(f[1] for f in filas), "records,", sum(f[4] for f in filas), "con vrp_mw > 0")
