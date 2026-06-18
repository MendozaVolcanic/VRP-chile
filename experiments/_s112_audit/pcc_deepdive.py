# PCC deep-dive S112: spatial distribution of detections vs MIROVA ground truth
# FICHA: análisis read-only, no toca pipeline
import json, csv, collections, math, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/"
VENT = (-40.5255, -72.1461)
CENTER = (-40.5903, -72.1187)  # mirova_center
INNER = 20.0

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1); dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(a))

def bucket_sensor(s):
    if s is None: return "unknown"
    if "MODIS" in s: return "MODIS"
    if s.endswith("_750"): return "VIIRS750"
    return "VIIRS375"

d = json.load(open(ROOT + "data/mirova_equivalent/PuyehueCordonCaulle.json"))
recs = d["records"]

# filter May + June 2026
recs_mj = [r for r in recs if r.get("datetime_utc","").startswith("2026-05") or r.get("datetime_utc","").startswith("2026-06")]
print(f"=== Records May+June 2026: {len(recs_mj)} of {len(recs)} total ===\n")

# A detection = pc.vrp_mw > 0 (what MIROVA would "report"). Use pc.vrp (A10).
def pc_vrp(r):
    pc = r.get("primary_cluster") or {}
    return pc.get("vrp_mw", 0.0) or 0.0
def pc_dist(r):
    pc = r.get("primary_cluster") or {}
    return pc.get("centroid_dist_km")
def pc_latlon(r):
    pc = r.get("primary_cluster") or {}
    return pc.get("centroid_lat"), pc.get("centroid_lon")

# Use final_hotspot as the "reported point" too (it's what dashboard distance uses)
print("=== (1) SPATIAL DISTRIBUTION (May+June), per sensor ===")
print("Detection = pc.vrp_mw>0. dist = centroid_dist_km (from mirova_center).\n")
by_sensor = collections.defaultdict(list)
for r in recs_mj:
    if pc_vrp(r) > 0:
        by_sensor[bucket_sensor(r.get("sensor"))].append(r)

for sb in sorted(by_sensor):
    rs = by_sensor[sb]
    dists = [pc_dist(r) for r in rs if pc_dist(r) is not None]
    far = [r for r in rs if (pc_dist(r) or 0) > 10]
    far15 = [r for r in rs if (pc_dist(r) or 0) > 15]
    vrps = [pc_vrp(r) for r in rs]
    print(f"  {sb}: n_det={len(rs)}  dist_median={sorted(dists)[len(dists)//2]:.1f}km  dist_max={max(dists):.1f}km" if dists else f"  {sb}: n_det={len(rs)} no dist")
    print(f"      >10km: {len(far)}  >15km: {len(far15)}  pc.vrp median={sorted(vrps)[len(vrps)//2]:.3f}MW max={max(vrps):.3f}MW")

print("\n=== FAR detections (pc.centroid_dist > 10km), May+June, ALL sensors ===")
far_all = [r for r in recs_mj if pc_vrp(r) > 0 and (pc_dist(r) or 0) > 10]
print(f"Total far(>10km) detections: {len(far_all)}")
for r in sorted(far_all, key=lambda r: -(pc_dist(r) or 0)):
    lat, lon = pc_latlon(r)
    dv = haversine(lat, lon, *VENT) if lat else None
    print(f"  {r['datetime_utc']} {bucket_sensor(r.get('sensor')):9s} dist_ctr={pc_dist(r):.1f} dist_vent={dv:.1f} pc.vrp={pc_vrp(r):.3f}MW dclass={r.get('distance_class')} t1={r.get('triggered_test1')} src={r.get('final_hotspot_source')} lat={lat:.4f} lon={lon:.4f}")
