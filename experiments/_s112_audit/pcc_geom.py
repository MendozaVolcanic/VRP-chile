# PCC geometry + MIROVA cross-check S112
import json, csv, collections, math, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/"
VENT = (-40.5255, -72.1461)      # Puyehue summit/vent
CENTER = (-40.5903, -72.1187)    # mirova_center
# Cordon Caulle 2011 lacolito vent ~NW of Puyehue (GVP fissure ~-40.51,-72.20)
LACOLITO = (-40.510, -72.200)
INNER = 20.0

def hav(a,b,c,e):
    R=6371.0; p1,p2=math.radians(a),math.radians(c); dp=math.radians(c-a); dl=math.radians(e-b)
    x=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(x))
def bearing(a,b,c,e):
    # compass bearing from (a,b) to (c,e)
    dl=math.radians(e-b); y=math.sin(dl)*math.cos(math.radians(c))
    x=math.cos(math.radians(a))*math.sin(math.radians(c))-math.sin(math.radians(a))*math.cos(math.radians(c))*math.cos(dl)
    return (math.degrees(math.atan2(y,x))+360)%360
def compass(brg):
    dirs=["N","NE","E","SE","S","SW","W","NW"]; return dirs[int((brg+22.5)//45)%8]
def bucket(s):
    if s is None: return "unknown"
    if "MODIS" in s: return "MODIS"
    if s.endswith("_750"): return "VIIRS750"
    return "VIIRS375"
def pcv(r):
    pc=r.get("primary_cluster") or {}; return pc.get("vrp_mw",0.0) or 0.0
def pcd(r):
    pc=r.get("primary_cluster") or {}; return pc.get("centroid_dist_km")
def pcll(r):
    pc=r.get("primary_cluster") or {}; return pc.get("centroid_lat"),pc.get("centroid_lon")

d=json.load(open(ROOT+"data/mirova_equivalent/PuyehueCordonCaulle.json"))
recs=[r for r in d["records"] if r.get("datetime_utc","").startswith(("2026-05","2026-06"))]

print(f"Lacolito ref {LACOLITO} is {hav(*VENT,*LACOLITO):.1f}km from vent, {hav(*CENTER,*LACOLITO):.1f}km from center")
print(f"vent->center distance: {hav(*VENT,*CENTER):.1f}km bearing {compass(bearing(*VENT,*CENTER))}\n")

# Directional analysis of far detections (>10km from center)
print("=== (3) DIRECTIONAL + DISTANCE-TO-LACOLITO of far(>10km) detections ===")
far=[r for r in recs if pcv(r)>0 and (pcd(r) or 0)>10]
brg_count=collections.Counter()
dist_to_lac=[]; dist_to_vent=[]
for r in far:
    lat,lon=pcll(r)
    if lat is None: continue
    brg=bearing(*CENTER,lat,lon); c=compass(brg)
    brg_count[c]+=1
    dist_to_lac.append(hav(lat,lon,*LACOLITO))
    dist_to_vent.append(hav(lat,lon,*VENT))
print("Bearing from center:", dict(brg_count))
print(f"Distance to lacolito ref: median={sorted(dist_to_lac)[len(dist_to_lac)//2]:.1f}km min={min(dist_to_lac):.1f} max={max(dist_to_lac):.1f}")
print(f"Distance to VENT:         median={sorted(dist_to_vent)[len(dist_to_vent)//2]:.1f}km min={min(dist_to_vent):.1f} max={max(dist_to_vent):.1f}")
print("-> If these were lacolito, dist_to_lacolito would be small. If regional fires, scattered & large.\n")

# (4) inner_radius effect: how many far(>5km from vent, the real edifice) are painted summit?
print("=== (4) inner_radius=20km EFFECT (May+June) ===")
det=[r for r in recs if pcv(r)>0]
summit=[r for r in det if r.get("distance_class")=="summit"]
far_lbl=[r for r in det if r.get("distance_class")=="far"]
# 'true far' = beyond 5km from vent (outside the volcanic edifice proper)
painted=[r for r in summit if (pcd(r) or 0)>5]
painted10=[r for r in summit if (pcd(r) or 0)>10]
print(f"Total detections: {len(det)}  labeled summit: {len(summit)}  labeled far: {len(far_lbl)}")
print(f"Painted 'summit' but >5km from center: {len(painted)} ({100*len(painted)/len(summit):.0f}% of summit)")
print(f"Painted 'summit' but >10km from center: {len(painted10)}")
# what inner_radius would these need
print(f"\nIf inner were 5km: summit count -> {len([r for r in det if (pcd(r) or 0)<=5])}")
print(f"If inner were 8km: summit count -> {len([r for r in det if (pcd(r) or 0)<=8])}")
print(f"If inner were 10km: summit count -> {len([r for r in det if (pcd(r) or 0)<=10])}")

# Path attribution of far detections
print("\n=== Path attribution of far(>10km) detections ===")
src_count=collections.Counter(r.get("final_hotspot_source") for r in far)
t1_count=collections.Counter(r.get("triggered_test1") for r in far)
print("final_hotspot_source:", dict(src_count))
print("triggered_test1:", dict(t1_count))
# t_bg cold? cirrus proxy
tbg=[r.get("t_bg_k") for r in far if r.get("t_bg_k")]
if tbg: print(f"t_bg_k of far dets: median={sorted(tbg)[len(tbg)//2]:.0f}K min={min(tbg):.0f} max={max(tbg):.0f}  (<270K = cirrus proxy A68)")
