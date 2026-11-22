# -*- coding: utf-8 -*-
"""Censo rapido: anomaly_pixels de la via trae todos los alertados (len == n_anomalous_pixels)? desde cuando?"""
import collections
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(sys.argv[1])
VOLS = ["Lascar", "Isluga", "Lastarria", "NevadosDeChillan", "PlanchonPeteroa", "PuyehueCordonCaulle", "Tupungatito",
        "Villarrica", "Chaiten", "Llaima", "Copahue"]
c = collections.Counter()
primera = {}
malos = []
for vol in VOLS:
    p = ROOT / "data" / "mirova_equivalent" / f"{vol}.json"
    if not p.exists():
        print("falta", vol)
        continue
    d = json.loads(p.read_text(encoding="utf-8"))
    for r in d["records"]:
        via = r.get("via_codigo_mirova") is True
        n = r.get("n_anomalous_pixels") or 0
        ap = r.get("anomaly_pixels") or []
        k = "via" if via else "no_via"
        c[k] += 1
        if n:
            c[k + "_con_alertados"] += 1
            if len(ap) == n:
                c[k + "_completos"] += 1
            else:
                c[k + "_distintos"] += 1
                if via and len(malos) < 10:
                    malos.append((vol, r.get("datetime_utc"), r.get("sensor"), n, len(ap),
                                  len(r.get("discarded_anomaly_pixels") or [])))
            if via and all("dist_km" in q for q in ap):
                c["via_con_dist_km"] += 1
        if via and r.get("discarded_anomaly_pixels"):
            c["via_con_discarded"] += 1
        if via:
            dt = r.get("datetime_utc", "")
            primera[vol] = min(primera.get(vol, dt), dt)
print(dict(c))
print("primera pasada de la via por volcan:", primera)
print("via con len distinto:", malos)
