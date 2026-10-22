# -*- coding: utf-8 -*-
"""Tamaño de la diferencia de diag_mu_deti y diag_sd_deti entre dos brazos pareados, por familia de sensor."""
import argparse, collections, json
from pathlib import Path
ap = argparse.ArgumentParser(); ap.add_argument("--a"); ap.add_argument("--b"); a = ap.parse_args()
d = collections.defaultdict(list)
for p in sorted(Path(a.a).glob("*.json")):
    q = Path(a.b) / p.name
    if not q.exists():
        continue
    A = {(r.get("sensor"), r.get("granule")): r for r in json.load(open(p, encoding="utf-8"))["records"]}
    B = {(r.get("sensor"), r.get("granule")): r for r in json.load(open(q, encoding="utf-8"))["records"]}
    for k in set(A) & set(B):
        fam = "MODIS" if k[0].startswith("MODIS") else ("VIIRS750" if k[0].endswith("_750") else "VIIRS375")
        for f in ("diag_mu_deti", "diag_sd_deti"):
            x, y = A[k].get(f), B[k].get(f)
            if isinstance(x, float) and isinstance(y, float) and x != y:
                d[(fam, f)].append((abs(x - y), abs(x - y) / max(abs(x), abs(y), 1e-300)))
for k, v in sorted(d.items()):
    ab = sorted(t[0] for t in v); rel = sorted(t[1] for t in v)
    print("%-9s %-13s n=%4d  abs max %.3g  rel mediana %.3g  rel max %.3g" % (k[0], k[1], len(v), ab[-1], rel[len(rel)//2], rel[-1]))
