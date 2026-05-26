"""Audit MW outliers in data/mirova_equivalent/*.json post F2.8 fixes."""
import json
import glob
import os
import sys

io_encoding = "utf-8"
sys.stdout.reconfigure(encoding=io_encoding)

ROOT = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP-Chile-s70"
PATTERN = os.path.join(ROOT, "data/mirova_equivalent/*.json")

THRESH_VRP = 5000.0       # MW
THRESH_TIR = 1000.0       # MW

def get_nested(d, *keys):
    cur = d
    for k in keys:
        if isinstance(cur, dict) and k in cur:
            cur = cur[k]
        else:
            return None
    return cur

def record_mw(r):
    """Return max MW-like value across known schemas."""
    candidates = []
    for k in ("vrp_mw", "vrp_mir_mw", "vrp_tir_mw"):
        v = r.get(k)
        if isinstance(v, (int, float)):
            candidates.append((k, v))
    pc = r.get("primary_cluster") or r.get("pc")
    if isinstance(pc, dict):
        for k in ("vrp_mw", "vrp_mir_mw", "vrp_tir_mw"):
            v = pc.get(k)
            if isinstance(v, (int, float)):
                candidates.append((f"pc.{k}", v))
    return candidates

def record_bt(r):
    fields = ("t_max_i04_k","t_max_i05_k","t_max_m13_k","t_max_b21_k","t_max_b22_k",
              "t_max","t_max_k","bt_max","bt_max_k")
    out = {}
    for f in fields:
        v = r.get(f)
        if isinstance(v, (int, float)):
            out[f] = v
    pc = r.get("primary_cluster") or r.get("pc") or {}
    if isinstance(pc, dict):
        for f in fields:
            v = pc.get(f)
            if isinstance(v, (int, float)):
                out[f"pc.{f}"] = v
    return out

outliers = []        # all records over threshold
top_per_volcano = {} # top 5 by max MW

for path in sorted(glob.glob(PATTERN)):
    vol = os.path.splitext(os.path.basename(path))[0]
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"ERR {vol}: {e}")
        continue
    # data may be {"records":[...]} or list
    records = data.get("records") if isinstance(data, dict) else data
    if not isinstance(records, list):
        continue
    ranked = []
    for r in records:
        if not isinstance(r, dict):
            continue
        mws = record_mw(r)
        if not mws:
            continue
        max_k, max_v = max(mws, key=lambda kv: kv[1])
        ranked.append((max_v, max_k, r))
        # check thresholds
        flag = False
        for k, v in mws:
            if "tir" in k and v > THRESH_TIR:
                flag = True
            elif v > THRESH_VRP:
                flag = True
        if flag:
            outliers.append((vol, max_v, max_k, r, record_bt(r), mws))
    ranked.sort(key=lambda x: -x[0])
    top_per_volcano[vol] = ranked[:5]

# Print global top outliers
outliers.sort(key=lambda x: -x[1])
print("\n=== OUTLIERS (vrp>5000 MW OR vrp_tir>1000 MW) ===")
print(f"Total: {len(outliers)}")
for vol, mw, k, r, bt, mws in outliers[:30]:
    date = r.get("date") or r.get("acquisition_time") or r.get("acq_time") or r.get("datetime") or r.get("time") or "?"
    sensor = r.get("sensor") or r.get("satellite") or r.get("platform") or "?"
    npx = r.get("n_anomalous_pixels") or r.get("n_pixels") or (r.get("primary_cluster") or {}).get("n_pixels") or "?"
    print(f"  {vol:25s} {date}  {sensor:10s}  {k}={mw:>10.1f} MW  BT={bt}  npx={npx}")
    if len(mws) > 1:
        print(f"     all_mw_fields: {mws}")

# Per-volcano top 5
print("\n=== TOP 5 BY VOLCANO ===")
for vol, ranks in sorted(top_per_volcano.items()):
    if not ranks:
        continue
    if ranks[0][0] < 50:
        continue
    print(f"\n-- {vol} --")
    for mw, k, r in ranks:
        date = r.get("date") or r.get("acquisition_time") or r.get("acq_time") or r.get("datetime") or r.get("time") or "?"
        sensor = r.get("sensor") or r.get("satellite") or r.get("platform") or "?"
        print(f"   {date}  {sensor:10s}  {k}={mw:>10.1f}")
