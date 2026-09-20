# -*- coding: utf-8 -*-
"""d07: cierre S126 de la divergencia D13: 'levantarla destaparia SOBRE TODO mas del mismo artefacto (37 %) y corroboraria
casi nada (1,5 %)'. Ventana declarada 2026-05-01..08-28, 2.694 de 8.033 records con VRP.
Remide en RECORDS y en MW (leccion D13), por anillo de distancia del cumulo y por sensor.
Instrumento: (1) control: debe reproducir ~2.694/8.033 y ~36,9 % / 14,8 %; si no, mi definicion no es la de S126 y se declara.
(2) n impreso."""
import io, sys, json
from collections import Counter, defaultdict
from dlib import *
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
D = cargar(); W = ("2026-05-01", "2026-08-28")
den = []; ap = []
for v in VOLS:
    for r in D[v]:
        if not (W[0] <= r["datetime_utc"][:10] <= W[1]) or pcv(r) <= 0: continue
        den.append((v, r))
        if r.get("distance_class") and r["distance_class"] != "summit": ap.append((v, r))
def anillo(v, r):
    cd = (r.get("pc") or {}).get("centroid_dist_km")
    if cd is None: return "sin_dist"
    if cd < 1: return "a_<1km"
    if cd < 1.5: return "b_1-1.5"
    if cd <= 3: return "c_anillo_1.5-3"
    if cd <= INNER[v]: return "d_3km-inner"
    return "e_fuera_inner"
cn = Counter(); cm = defaultdict(float); cs = Counter(); csm = defaultdict(float)
for v, r in ap:
    a = anillo(v, r); cn[a] += 1; cm[a] += pcv(r); b = bucket(r["sensor"]); cs[b] += 1; csm[b] += pcv(r)
N = len(ap); M = sum(cm.values())
out = {"apagados": N, "con_vrp": len(den), "pct": round(100*N/len(den), 1), "MW_apagados": round(M, 1),
       "por_anillo": {a: {"n": cn[a], "pct_records": round(100*cn[a]/N, 1), "MW": round(cm[a], 1), "pct_MW": round(100*cm[a]/M, 1)} for a in sorted(cn)},
       "por_sensor": {b: {"n": cs[b], "pct_records": round(100*cs[b]/N, 1), "pct_MW": round(100*csm[b]/M, 1)} for b in cs}}
json.dump(out, open("d07_D13_S126_clasificacion.json", "w"), indent=1); print(json.dumps(out, indent=1))
