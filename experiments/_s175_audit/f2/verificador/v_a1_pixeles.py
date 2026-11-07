# -*- coding: utf-8 -*-
"""A1: pixeles de nuestro record en las 5 protegidas no publicadas. Control: una protegida publicada al azar.
Uso: python v_a1_pixeles.py <arbol_base>"""
import io
import json
import math
import sys
from pathlib import Path

import yaml

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
A = Path(sys.argv[1])
coords = {v["name"]: (v["lat"], v["lon"]) for v in yaml.safe_load(open(A / "volcanoes.yaml", encoding="utf-8"))["volcanoes"] if "lat" in v}
INNER = {"Lascar": 5, "Lastarria": 3, "Tupungatito": 7}
CASOS = [("Lascar", "VIIRS_SNPP", "2026-08-22 05:06"), ("Lastarria", "VIIRS_NOAA20", "2026-04-18 04:42"),
         ("Lastarria", "VIIRS_SNPP", "2026-05-02 05:06"), ("Tupungatito", "VIIRS_SNPP", "2026-09-28 05:18"),
         ("Tupungatito", "VIIRS_SNPP", "2026-09-29 04:54"),
         # controles positivos: pasadas publicadas de la misma noche
         ("Lascar", "VIIRS_NOAA20", "2026-08-22 05:24"), ("Tupungatito", "VIIRS_NOAA20", "2026-09-28 05:36")]


def hav(a, b, c, d):
    R = 6371.0
    p1, p2 = math.radians(a), math.radians(c)
    x = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(d - b) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(x))


cache = {}
for vol, sen, t in CASOS:
    if vol not in cache:
        cache[vol] = json.load(open(A / "data" / "mirova_equivalent" / f"{vol}.json", encoding="utf-8"))["records"]
    rs = [r for r in cache[vol] if r.get("sensor") == sen and r.get("datetime_utc") == t]
    print(f"== {vol} {sen} {t}: {len(rs)} record(s)")
    for r in rs:
        px = r.get("anomaly_pixels") or []
        la, lo = coords[vol]
        d = [round(hav(la, lo, p["lat"], p["lon"]), 2) for p in px]
        pc = r.get("primary_cluster") or {}
        print("   n_anomaly_pixels", len(px), "| dist px al volcan km", d, "| inner", INNER.get(vol),
              "| fuera del inner:", sum(1 for x in d if x > INNER.get(vol, 5)),
              "| pc n_pixels", pc.get("n_pixels"), "pc dist", pc.get("centroid_dist_km"), "pc vrp", pc.get("vrp_mw"),
              "| dc", r.get("distance_class"), "| vrp_mw", r.get("vrp_mw"), "f5", r.get("f5_core_vrp_mw"),
              "| via", r.get("via_codigo_mirova"), "| discarded", r.get("discarded_reason"),
              "| px vrp", [p.get("vrp_mw") for p in px], "| px bt", [p.get("bt_k") for p in px])
