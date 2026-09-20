# -*- coding: utf-8 -*-
"""d04: far->summit (A81, divergencia D18, D11/A82). Definicion verbatim S113: far AND pc.vrp>0 AND pc.centroid_dist<=inner.
Mide: total hoy, reparto por sensor, tasa mensual (con Y sin los meses donde solo hay 1 volcan), distancia del final_hotspot
(D18: 'mediana 22 km, p10 11,8; NI UNO dentro del ROI1'), y en NOCHES: en cuantas noches-volcan TODA pasada con cumulo crateriano queda far.
Instrumento: (1) si distance_class estuviera roto (todo summit) daria 0: contradice 9.196 declarado, se veria. (2) n total impreso."""
import io, sys, json, statistics as st
from collections import defaultdict, Counter
from dlib import *
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
D = cargar()
fs = []; tot_mes = Counter(); fs_mes = Counter(); vols_mes = defaultdict(set)
for v in VOLS:
    for r in D[v]:
        m = r["datetime_utc"][:7]; tot_mes[m] += 1; vols_mes[m].add(v)
        pc = r.get("pc") or {}
        if r.get("distance_class") == "far" and (pc.get("vrp_mw") or 0) > 0 and pc.get("centroid_dist_km") is not None and pc["centroid_dist_km"] <= INNER[v]:
            fs.append((v, r)); fs_mes[m] += 1
out = {"far_summit_hoy": len(fs), "al_2026-08-31": sum(1 for v, r in fs if r["datetime_utc"][:10] <= "2026-08-31"),
       "por_sensor": Counter(bucket(r["sensor"]) for v, r in fs)}
nmod = sum(1 for v in VOLS for r in D[v] if bucket(r["sensor"]) == "modis")
out["modis_total_records"] = nmod; out["pct_de_modis"] = round(100*out["por_sensor"]["modis"]/nmod, 1)
dist = sorted(r.get("final_hotspot_dist_km") for v, r in fs if r.get("final_hotspot_dist_km") is not None)
out["final_hotspot_dist_km"] = {"n": len(dist), "mediana": st.median(dist), "p10": dist[len(dist)//10], "min": dist[0],
                                "n_dentro_del_inner": sum(1 for v, r in fs if (r.get("final_hotspot_dist_km") or 99) <= INNER[v]),
                                "n_a_menos_de_3.54km(esquina caja)": sum(1 for d in dist if d <= 3.54)}
tasas = {m: round(100*fs_mes[m]/tot_mes[m], 1) for m in sorted(tot_mes)}
out["tasa_mensual_pct_de_TODOS_los_records"] = tasas
out["meses_con_menos_de_11_volcanes"] = {m: len(vols_mes[m]) for m in sorted(vols_mes) if len(vols_mes[m]) < 11}
# tasa dentro de MODIS, que es donde vive
tm = Counter(); fm = Counter()
for v in VOLS:
    for r in D[v]:
        if bucket(r["sensor"]) == "modis": tm[r["datetime_utc"][:7]] += 1
for v, r in fs:
    if bucket(r["sensor"]) == "modis": fm[r["datetime_utc"][:7]] += 1
out["tasa_mensual_pct_de_MODIS"] = {m: round(100*fm[m]/tm[m], 1) for m in sorted(tm)}
out["por_volcan_pct_de_sus_modis"] = {}
for v in VOLS:
    a = sum(1 for r in D[v] if bucket(r["sensor"]) == "modis"); b = sum(1 for vv, r in fs if vv == v and bucket(r["sensor"]) == "modis")
    out["por_volcan_pct_de_sus_modis"][v] = (b, a, round(100*b/a, 1))
json.dump(out, open("d04_far_summit.json", "w"), indent=1, default=dict)
print(json.dumps(out, indent=1, default=dict))
