# PCC final: MODIS day/night, far-VIIRS summary, inner_radius quantification
import json, collections, math, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/"
def bucket(s):
    if "MODIS" in s: return "MODIS"
    return "VIIRS750" if s.endswith("_750") else "VIIRS375"
def pcv(r):
    pc=r.get("primary_cluster") or {}; return pc.get("vrp_mw",0.0) or 0.0
def pcd(r):
    pc=r.get("primary_cluster") or {}; return pc.get("centroid_dist_km")
d=json.load(open(ROOT+"data/mirova_equivalent/PuyehueCordonCaulle.json"))
recs=[r for r in d["records"] if r.get("datetime_utc","").startswith(("2026-05","2026-06"))]

# MODIS: pc.vrp distribution & the 5.0 spike (likely VRP floor / piso 0.05? no, 5.0 = ?)
modis=[r for r in recs if bucket(r['sensor'])=="MODIS" and pcv(r)>0]
v=collections.Counter(round(pcv(r),1) for r in modis)
print("MODIS pc.vrp histogram (top):", v.most_common(6))
# all MODIS at crater?
md_crater=[r for r in modis if (pcd(r) or 0)<=5]
print(f"MODIS: {len(modis)} det, {len(md_crater)} within 5km of center ({100*len(md_crater)/len(modis):.0f}%)")
print(f"  -> MIROVA reports 0 MODIS for PCC. Our MODIS pc.vrp 1-15MW at crater = diffuse-field/topographic core (A69), NOT MIROVA-corroborated.")

# Far VIIRS that are on NON-mirova days: are they cirrus (cold t_bg)?
far=[r for r in recs if pcv(r)>0 and (pcd(r) or 0)>10]
cirrus=[r for r in far if (r.get('t_bg_k') or 999)<270]
print(f"\nFar(>10km) detections: {len(far)}, of which t_bg<270K (cirrus/path-D proxy A23): {len(cirrus)} ({100*len(cirrus)/len(far):.0f}%)")
ctx=[r for r in far if r.get('final_hotspot_source')=='ctx_cluster']
print(f"  ctx_cluster (path D dNTI): {len(ctx)} ({100*len(ctx)/len(far):.0f}%)")

# inner_radius quantification: detections by dist band, and how dclass would change
print("\n=== inner_radius=20km effect quantified (May+June, det pc.vrp>0) ===")
det=[r for r in recs if pcv(r)>0]
bands={"0-3":0,"3-5":0,"5-8":0,"8-10":0,"10-15":0,"15-20":0,">20":0}
for r in det:
    dd=pcd(r) or 0
    if dd<=3: bands["0-3"]+=1
    elif dd<=5: bands["3-5"]+=1
    elif dd<=8: bands["5-8"]+=1
    elif dd<=10: bands["8-10"]+=1
    elif dd<=15: bands["10-15"]+=1
    elif dd<=20: bands["15-20"]+=1
    else: bands[">20"]+=1
print("Distance bands (from center):", bands)
n=len(det)
# all <=20km painted summit; MIROVA's true signal is at ~7.7km (lacolito). >8km is beyond lacolito+VIIRS pixel
beyond_lacolito=[r for r in det if (pcd(r) or 0)>10]
print(f"Total det={n}. Painted summit by inner=20: {len([r for r in det if (pcd(r) or 0)<=20])}")
print(f"Detections >10km painted 'summit' (beyond lacolito MIROVA signal ~7.7km): {len(beyond_lacolito)} = {100*len(beyond_lacolito)/n:.0f}% of all det")
print(f"If inner_radius=10km: these {len(beyond_lacolito)} flip far->correct. MIROVA's own signal (~8.5km max) stays summit.")
print(f"MIROVA max alert distance (excl FALSO): ~8.55km -> inner=10km safely contains real lacolito signal.")
