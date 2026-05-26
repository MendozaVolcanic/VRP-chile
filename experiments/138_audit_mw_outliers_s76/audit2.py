"""Audit v2 with datetime_utc + pre/post F2.8 partition + max anomaly_pixel BT inspection."""
import json, glob, os, sys
sys.stdout.reconfigure(encoding="utf-8")

ROOT = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP-Chile-s70"
F28 = "2026-05-23T17:00:00Z"   # fcd3ba34 ~ 12:45 -0400 = 16:45 UTC -> use 17:00 cutoff

def mw_total(r):
    """Return (best_field, value)."""
    cand = []
    for k in ("vrp_mw","vrp_mir_mw","vrp_tir_mw"):
        v = r.get(k)
        if isinstance(v,(int,float)):
            cand.append((k,v))
    if not cand: return ("none",0)
    return max(cand,key=lambda x:x[1])

def is_outlier(r):
    v_total = r.get("vrp_mw") or 0
    v_mir = r.get("vrp_mir_mw") or 0
    v_tir = r.get("vrp_tir_mw") or 0
    return v_total > 5000 or v_mir > 5000 or v_tir > 1000

all_out = []
for path in sorted(glob.glob(os.path.join(ROOT,"data/mirova_equivalent/*.json"))):
    vol = os.path.splitext(os.path.basename(path))[0]
    with open(path,"r",encoding="utf-8") as f:
        data = json.load(f)
    recs = data.get("records") if isinstance(data,dict) else data
    if not isinstance(recs,list): continue
    for r in recs:
        if not isinstance(r,dict): continue
        if not is_outlier(r): continue
        dt = r.get("datetime_utc") or r.get("date") or "?"
        sensor = r.get("sensor","?")
        npx = r.get("n_anomalous_pixels","?")
        # max BT of anomaly pixels
        ap = r.get("anomaly_pixels") or []
        bt_max_anom = max((p.get("bt_k",0) for p in ap if isinstance(p,dict)),default=None)
        all_out.append({
            "vol": vol,
            "dt": dt,
            "sensor": sensor,
            "vrp_mw": r.get("vrp_mw"),
            "vrp_mir_mw": r.get("vrp_mir_mw"),
            "vrp_tir_mw": r.get("vrp_tir_mw"),
            "t_max_i04_k": r.get("t_max_i04_k"),
            "t_max_i05_k": r.get("t_max_i05_k"),
            "t_max_k": r.get("t_max_k"),
            "bt_max_anomaly": bt_max_anom,
            "n_pixels": npx,
            "t_bg_k": r.get("t_bg_k"),
            "diag_sigma_bg_k": r.get("diag_sigma_bg_k"),
            "diag_eff_threshold_k": r.get("diag_eff_threshold_k"),
            "post_f28": dt >= F28,
        })

all_out.sort(key=lambda x: -(x["vrp_tir_mw"] or 0))

post = [x for x in all_out if x["post_f28"]]
pre  = [x for x in all_out if not x["post_f28"]]
print(f"Total outliers: {len(all_out)}  (post-F2.8={len(post)}, pre-F2.8={len(pre)})")
print(f"F2.8 cutoff: {F28}")
print()

print("=== TOP 20 (all) ===")
print(f"{'vol':22} {'dt':25} {'sensor':14} {'tir_mw':>9} {'mir_mw':>8} {'bt_i04':>7} {'bt_i05':>7} {'bt_anom':>7} {'npx':>5} {'F2.8?':6}")
for x in all_out[:20]:
    f28 = "POST" if x["post_f28"] else "pre"
    print(f"{x['vol'][:22]:22} {str(x['dt'])[:25]:25} {str(x['sensor'])[:14]:14} {x['vrp_tir_mw'] or 0:9.1f} {x['vrp_mir_mw'] or 0:8.1f} {x['t_max_i04_k'] or 0:7.2f} {x['t_max_i05_k'] or 0:7.2f} {x['bt_max_anomaly'] or 0:7.2f} {str(x['n_pixels']):>5} {f28:6}")

print()
print("=== POST-F2.8 outliers ===")
for x in post:
    print(f"  {x['vol']:22} {x['dt']:25} {x['sensor']:14} tir={x['vrp_tir_mw']:9.1f} mir={x['vrp_mir_mw'] or 0:7.1f} bt_i05={x['t_max_i05_k']} npx={x['n_pixels']}")

# Date range overall
all_dates = sorted({x["dt"] for x in all_out})
print(f"\nDate range: {all_dates[0]} ... {all_dates[-1]}")

# Save JSON
import json as j
with open(os.path.join(ROOT,"experiments/138_audit_mw_outliers_s76/outliers.json"),"w",encoding="utf-8") as f:
    j.dump(all_out,f,indent=2,default=str)
print(f"\nWrote {len(all_out)} outliers -> outliers.json")
