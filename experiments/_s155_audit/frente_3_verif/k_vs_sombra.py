#!/usr/bin/env python3
"""F3-06: en las MISMAS pasadas, pc.vrp_mw de K (mirova_equivalent) contra la sombra C0 (experimental_v2).
P1: si K cambiara la magnitud por pasada, la mediana K/C0 se alejaria de 1; si no, la caida del ratio del
audit viene del conteo de pasadas por noche. P2: n de pares impreso; n=0 = SIN DATO.
Criterio 'dash' del audit (l. 415-420): 0<vrp<=50000, centroid<=inner, distance_class in {summit,None}."""
import json, statistics, sys, collections
from pathlib import Path
REPO = Path(__file__).resolve().parents[3]; sys.stdout.reconfigure(encoding="utf-8")
INNER = {"Lascar": 5, "Lastarria": 3, "Tupungatito": 7, "PlanchonPeteroa": 3, "NevadosDeChillan": 5, "Chaiten": 5,
         "Villarrica": 5, "Llaima": 5, "Copahue": 4, "Isluga": 5, "PuyehueCordonCaulle": 20}
def dash(r, vol):
    pc = r.get("primary_cluster") or {}; v = pc.get("vrp_mw") or 0; c = pc.get("centroid_dist_km")
    return v if (0 < v <= 50000 and c is not None and c <= INNER[vol] and r.get("distance_class") in (None, "summit")) else 0
def b(s): return "MODIS" if s.startswith("MODIS") else ("VIIRS750" if s.endswith("_750") else "VIIRS375")
for vol in INNER:
    p = REPO / "data/experimental_v2" / f"{vol}.json"
    if not p.exists(): continue
    sh = {(r["datetime_utc"], r["sensor"]): r for r in json.load(open(p, encoding="utf-8"))["records"]}
    k = {(r["datetime_utc"], r["sensor"]): r for r in json.load(open(REPO / "data/mirova_equivalent" / f"{vol}.json", encoding="utf-8"))["records"]
         if r.get("regimen")}
    comunes = set(sh) & set(k)
    pares = [(dash(k[x], vol), dash(sh[x], vol), b(x[1])) for x in comunes]
    ambos = [a / c for a, c, _ in pares if a > 0 and c > 0]
    solo_sh = sum(1 for a, c, _ in pares if c > 0 and a == 0); solo_k = sum(1 for a, c, _ in pares if a > 0 and c == 0)
    print(f"{vol:20s} pasadas_comunes={len(comunes)} ambos_dash={len(ambos)} med_K/C0={round(statistics.median(ambos),3) if ambos else 'SIN DATO'} "
          f"solo_sombra={solo_sh} solo_K={solo_k}")
