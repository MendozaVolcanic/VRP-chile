# -*- coding: utf-8 -*-
"""Qué campos difieren entre dos brazos en las pasadas pareadas (por volcán, sensor, gránulo). Uso: --a DIR --b DIR."""
import argparse, collections, json, sys
from pathlib import Path
ap = argparse.ArgumentParser(); ap.add_argument("--a"); ap.add_argument("--b"); a = ap.parse_args()
VOL = {"processed_utc", "first_processed_utc", "regimen"}
cnt, n = collections.Counter(), 0
for p in sorted(Path(a.a).glob("*.json")):
    q = Path(a.b) / p.name
    if not q.exists():
        continue
    A = {(r.get("sensor"), r.get("granule")): r for r in json.load(open(p, encoding="utf-8"))["records"]}
    B = {(r.get("sensor"), r.get("granule")): r for r in json.load(open(q, encoding="utf-8"))["records"]}
    for k in set(A) & set(B):
        n += 1
        for f in set(A[k]) | set(B[k]):
            if f not in VOL and A[k].get(f) != B[k].get(f):
                cnt[(("MODIS" if (k[0] or "").startswith("MODIS") else k[0]), f)] += 1
print("pares", n)
for (s, f), c in sorted(cnt.items(), key=lambda x: -x[1])[:25]:
    print("%-20s %-28s %d" % (s, f, c))
