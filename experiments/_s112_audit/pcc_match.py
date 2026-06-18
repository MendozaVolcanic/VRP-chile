# PCC night-by-night match: our far detections vs MIROVA same-day alerts
import json, csv, collections, math, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/"
GT = ROOT+"experiments/_s111_d11/mirova_fresh/"

def bucket(s):
    if s is None: return "unknown"
    if "MODIS" in s: return "MODIS"
    if s.endswith("_750"): return "VIIRS750"
    return "VIIRS375"
def pcv(r):
    pc=r.get("primary_cluster") or {}; return pc.get("vrp_mw",0.0) or 0.0
def pcd(r):
    pc=r.get("primary_cluster") or {}; return pc.get("centroid_dist_km")

# MIROVA alert DAYS (any sensor, any alert)
mirova_days=set()
for path in ("cons.csv","ocr.csv"):
    with open(GT+path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["Volcan"]!="Puyehue-Cordon Caulle": continue
            dt=row["Fecha_Satelite_UTC"]
            if not dt.startswith(("2026-05","2026-06")): continue
            try: vrp=float(row["VRP_MW"])
            except: vrp=0.0
            tipo=row.get("Tipo_Registro","")
            if (vrp>0 or "ALERTA" in tipo) and "FALSO" not in tipo:
                mirova_days.add(dt[:10])
print(f"MIROVA alert-days (May+June, excl FALSO_POSITIVO): {len(mirova_days)}")

d=json.load(open(ROOT+"data/mirova_equivalent/PuyehueCordonCaulle.json"))
recs=[r for r in d["records"] if r.get("datetime_utc","").startswith(("2026-05","2026-06"))]

# Classify OUR far (>10km) detections
far=[r for r in recs if pcv(r)>0 and (pcd(r) or 0)>10]
print(f"\n=== Our far(>10km) detections: {len(far)} ===")
matched=0; unmatched=0
unm_by_sensor=collections.Counter()
for r in far:
    day=r["datetime_utc"][:10]
    has_mirova = day in mirova_days
    if has_mirova: matched+=1
    else:
        unmatched+=1; unm_by_sensor[bucket(r.get("sensor"))]+=1
print(f"Far detections on a MIROVA alert-DAY (but MIROVA's point is at ~7.7km, not where ours is): {matched}")
print(f"Far detections on a day MIROVA saw NOTHING: {unmatched}")
print(f"  unmatched far by sensor: {dict(unm_by_sensor)}")

# MODIS specifically: MIROVA never reports MODIS for PCC. So ANY MODIS detection >0 is uncorrelated with MIROVA-MODIS
print("\n=== MODIS DETECTIONS (May+June) — MIROVA reports 0 MODIS alerts for PCC ===")
modis=[r for r in recs if bucket(r.get('sensor'))=="MODIS" and pcv(r)>0]
md_far=[r for r in modis if (pcd(r) or 0)>5]
md_far10=[r for r in modis if (pcd(r) or 0)>10]
vrps=sorted(pcv(r) for r in modis)
print(f"MODIS detections pc.vrp>0: {len(modis)}  pc.vrp median={vrps[len(vrps)//2]:.2f} max={max(vrps):.2f}MW")
print(f"  MODIS >5km from center: {len(md_far)}  >10km: {len(md_far10)}")
print(f"  MODIS dist median: {sorted(pcd(r) or 0 for r in modis)[len(modis)//2]:.1f}km")
# the 5-15MW MODIS ones the task asks about
big_modis=[r for r in modis if pcv(r)>=3]
print(f"\n  MODIS with pc.vrp>=3MW: {len(big_modis)}")
for r in sorted(big_modis,key=lambda r:-pcv(r)):
    print(f"    {r['datetime_utc']} pc.vrp={pcv(r):.1f}MW dist={pcd(r):.1f}km t_bg={r.get('t_bg_k')} t_max={r.get('t_max_k')} src={r.get('final_hotspot_source')} t1={r.get('triggered_test1')} dclass={r.get('distance_class')}")

# What does MODIS look like scene-wide (record.vrp_mw = diffuse field sum, A69)?
print("\n=== record.vrp_mw (scene-wide diffuse, A69) vs pc.vrp for MODIS ===")
for r in sorted(modis,key=lambda r:-(r.get('vrp_mw') or 0))[:8]:
    print(f"    {r['datetime_utc']} record.vrp={r.get('vrp_mw'):.0f}MW pc.vrp={pcv(r):.2f}MW n_anom_px={r.get('n_anomalous_pixels')}  <- diffuse field A69")
