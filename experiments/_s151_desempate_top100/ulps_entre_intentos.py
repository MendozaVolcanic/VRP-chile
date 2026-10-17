"""Cuantos pares (mismo commit, runner distinto) difieren en algun escalar float, y cuanto."""
import json, glob, math
from collections import Counter, defaultdict
BASE = "C:/Users/nmend/AppData/Local/Temp/claude"
pares = [("v1_38639658446", "i1", "i3"), ("v2a_38648773684", "i1", "i2"), ("w2a_38853230521", "i1", "i2")]
SKIP = {"processed_utc", "first_processed_utc", "anomaly_pixels", "discarded_anomaly_pixels", "primary_cluster"}


def idx(root):
    out = {}
    for p in glob.glob(root + "/**/*.json", recursive=True):
        parts = p.replace("\\", "/").split("/")
        if parts[-2].startswith("_s1"):
            out[parts[-2] + "/" + parts[-1]] = p
    return out


campo = defaultdict(Counter)
maxrel = defaultdict(float)
tot = Counter()
for run, a, b in pares:
    A, B = idx(f"{BASE}/{run}/{a}"), idx(f"{BASE}/{run}/{b}")
    for k in sorted(set(A) & set(B)):
        ra = {(r["sensor"], r["datetime_utc"]): r for r in json.load(open(A[k]))["records"]}
        rb = {(r["sensor"], r["datetime_utc"]): r for r in json.load(open(B[k]))["records"]}
        for kk in set(ra) & set(rb):
            x, y = ra[kk], rb[kk]
            s = "MODIS" if "MODIS" in kk[0] else ("V750" if kk[0].endswith("_750") else "V375")
            tot[s] += 1
            for f in set(x) | set(y):
                if f in SKIP:
                    continue
                va, vb = x.get(f), y.get(f)
                if va != vb and isinstance(va, float) and isinstance(vb, float):
                    rel = abs(va - vb) / max(abs(va), abs(vb), 1e-300)
                    if rel < 1e-9:
                        campo[s][f] += 1
                        maxrel[(s, f)] = max(maxrel[(s, f)], rel)
print("pares por sensor", dict(tot))
for s in campo:
    print(s)
    for f, n in campo[s].most_common():
        print(f"   {f}: {n} pares con diferencia relativa <1e-9 (max {maxrel[(s, f)]:.1e})")
