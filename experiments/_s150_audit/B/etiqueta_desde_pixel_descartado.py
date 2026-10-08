# -*- coding: utf-8 -*-
"""S150 frente B. Mide, en el JSON remoto de Nevados de Chillan (todo el historial), cuantos
records quedan con distance_class='far' porque final_hotspot_dist_km apunta a un pixel que la
geocerca del propio store (radius_km = 25) ya habia descartado, y si el rescate F47
(store.py:359, 'single_pixel_far_overridden_by_cluster') sigue disparando.

Preguntas del instrumento:
1. Si la etiqueta saliera siempre del pixel descartado, esto lo veria: columna fh>radio.
   Control positivo: 2026-10-01 08:35 MODIS_AQUA (fh 32,84 km) debe contar.
2. Si el JSON no trae los campos, el conteo daria 0 por ausencia: se cuenta aparte cuantos
   records tienen final_hotspot_dist_km no nulo (denominador), y se imprime por mes.
"""
import json, sys, collections
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
RADIO, INNER = 25.0, 5.0
d = json.load(open(AQUI / "datos" / "NevadosDeChillan.json", encoding="utf-8"))
por_mes = collections.defaultdict(collections.Counter)
for r in d["records"]:
    mes = r["datetime_utc"][:7]
    s = r.get("sensor", "")
    b = "MODIS" if s.startswith("MODIS") else ("V750" if s.endswith("_750") else "V375")
    c = por_mes[(mes, b)]
    c["n"] += 1
    fh = r.get("final_hotspot_dist_km")
    pc = r.get("primary_cluster") or {}
    if fh is not None:
        c["con_fh"] += 1
    if r.get("discarded_reason") == "single_pixel_far_overridden_by_cluster":
        c["rescate_f47"] += 1
    if r.get("distance_class") == "far" and fh is not None and fh > RADIO:
        c["far_fh>radio"] += 1
        if (pc.get("vrp_mw") or 0) > 0 and pc.get("centroid_dist_km") is not None and pc["centroid_dist_km"] <= INNER:
            c["far_fh>radio_pc<=inner_vrp>0"] += 1
    if r.get("distance_class") == "far" and (pc.get("vrp_mw") or 0) > 0 and \
            pc.get("centroid_dist_km") is not None and pc["centroid_dist_km"] <= INNER:
        c["far_pc<=inner_vrp>0"] += 1
        if abs((pc.get("vrp_mw") or 0) - 5.0) < 1e-9:
            c["  de_ellos_pc=5.000(tope D9)"] += 1
print("mes      sensor  n  con_fh  rescateF47  far_fh>radio  far_fh>radio_pc<=inner  far_pc<=inner  pc=5.000")
for (mes, b) in sorted(por_mes):
    if mes < "2025-10":
        continue
    c = por_mes[(mes, b)]
    print(f"{mes}  {b:<5} {c['n']:>4} {c['con_fh']:>6} {c['rescate_f47']:>10} {c['far_fh>radio']:>12} "
          f"{c['far_fh>radio_pc<=inner_vrp>0']:>22} {c['far_pc<=inner_vrp>0']:>13} {c['  de_ellos_pc=5.000(tope D9)']:>8}")
tot = collections.Counter()
for (mes, b), c in por_mes.items():
    tot[b, "rescate"] += c["rescate_f47"]
    tot[b, "far_pc_inner"] += c["far_pc<=inner_vrp>0"]
print("total historico:", dict(tot))
ult = [r["datetime_utc"] for r in d["records"] if r.get("discarded_reason") == "single_pixel_far_overridden_by_cluster"]
print("ultimo rescate F47 en NdC:", max(ult) if ult else None)
