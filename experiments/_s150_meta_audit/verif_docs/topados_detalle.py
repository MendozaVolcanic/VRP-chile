"""Detalle: pc.vrp_mw == 5,0 por distance_class, y pc.vrp_mw > 5,0 por volcan/sensor. Solo lectura."""
import glob, json, os, sys, io
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
eqc = Counter(); gt = Counter(); gtv = Counter(); gt_summit = 0; eq_rng = []
for f in sorted(glob.glob("data/mirova_equivalent/*.json")):
    vol = os.path.basename(f)[:-5]
    for r in json.load(open(f, encoding="utf-8")).get("records", []):
        pv = (r.get("primary_cluster") or {}).get("vrp_mw")
        if not isinstance(pv, (int, float)): continue
        if abs(pv - 5.0) < 1e-9:
            eqc[r.get("distance_class")] += 1; eq_rng.append(r.get("datetime_utc"))
        elif pv > 5.0:
            gt[r.get("sensor")] += 1; gtv[vol] += 1
            if r.get("distance_class") == "summit": gt_summit += 1
print("pc==5,0 por distance_class:", dict(eqc), "ventana", min(eq_rng), max(eq_rng))
print("pc>5,0 por sensor:", dict(gt)); print("pc>5,0 por volcan:", dict(gtv)); print("pc>5,0 summit:", gt_summit)
