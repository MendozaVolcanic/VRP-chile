# -*- coding: utf-8 -*-
import io,json,sys,math,statistics as st
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
import yaml
BASE=r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
V=yaml.safe_load(open(BASE+"/volcanoes.yaml",encoding="utf-8"))
vmap={v["name"]:v for v in (V["volcanoes"] if isinstance(V,dict) else V)}
def hav(a,b,c,d):
    R=6371.0088;p=math.radians
    x=math.sin(p(c-a)/2)**2+math.cos(p(a))*math.cos(p(c))*math.sin(p(d-b)/2)**2
    return 2*R*math.asin(math.sqrt(x))
def load(v):
    d=json.load(open(f"{BASE}/data/mirova_equivalent/{v}.json",encoding="utf-8"))
    return d["records"] if isinstance(d,dict) and "records" in d else d
cfg=vmap["Villarrica"]
print("catalogo lat/lon:",cfg.get("lat"),cfg.get("lon"),"| vent:",cfg["vent_lat"],cfg["vent_lon"],
      "| sep=%.3f km"%hav(cfg["lat"],cfg["lon"],cfg["vent_lat"],cfg["vent_lon"]))
recs=[r for r in load("Villarrica") if r.get("sensor","").startswith("VIIRS")
      and not r.get("sensor","").endswith("_750") and r.get("datetime_utc","")>="2026-06-01"
      and r.get("distance_class")=="summit"]
tr=[r for r in recs if r.get("final_hotspot_source")=="test1_roi"]

print("\n=== final_hotspot_dist_km (valores crudos) ===")
from collections import Counter
print(Counter(r.get("final_hotspot_dist_km") for r in tr).most_common(4))

print("\n=== H1(d) BT del pico vs fondos ===")
n=lt_bg=lt_p95=0; ds=[]
for r in tr:
    tmax=r.get("t_max_i04_k"); tbg=r.get("t_bg_k"); p95=r.get("diag_roi_p95_k")
    if tmax is None or tbg is None: continue
    n+=1
    if tmax<tbg: lt_bg+=1
    ds.append(tmax-tbg)
print(f"n={n}  t_max_i04 < t_bg_k en {lt_bg} ({100*lt_bg/max(n,1):.0f}%)  med delta={st.median(ds):+.2f} K")
# el pixel del cluster (no el t_max de escena)
n2=lt2=0; d2=[]
for r in tr:
    pc=r.get("primary_cluster") or {}; tbg=r.get("t_bg_k")
    ap=r.get("anomaly_pixels") or []
    if not ap or tbg is None: continue
    # pixel del cluster = el mas cercano al centroid
    if pc.get("centroid_lat") is None: continue
    best=min(ap,key=lambda p:hav(pc["centroid_lat"],pc["centroid_lon"],p["lat"],p["lon"]))
    if best.get("bt_k") is None: continue
    n2+=1; d2.append(best["bt_k"]-tbg)
    if best["bt_k"]<tbg: lt2+=1
print(f"pixel del cluster: n={n2}  bt_k < t_bg_k en {lt2} ({100*lt2/max(n2,1):.0f}%)  med delta={st.median(d2):+.2f} K")

print("\n=== H4: origen de cada campo de distancia (Villarrica) ===")
err_vent=[];err_cat=[]
for r in tr[:200]:
    for p in (r.get("anomaly_pixels") or [])[:3]:
        if p.get("dist_km") is None: continue
        err_vent.append(abs(p["dist_km"]-hav(cfg["vent_lat"],cfg["vent_lon"],p["lat"],p["lon"])))
        err_cat.append(abs(p["dist_km"]-hav(cfg["lat"],cfg["lon"],p["lat"],p["lon"])))
print(f"anomaly_pixels.dist_km: err vs VENT med={st.median(err_vent):.4f} | err vs CATALOGO med={st.median(err_cat):.4f}")
ev=[];ec=[]
for r in tr:
    if r.get("hotspot_lat") is None or r.get("hotspot_dist_km") is None: continue
    ev.append(abs(r["hotspot_dist_km"]-hav(cfg["vent_lat"],cfg["vent_lon"],r["hotspot_lat"],r["hotspot_lon"])))
    ec.append(abs(r["hotspot_dist_km"]-hav(cfg["lat"],cfg["lon"],r["hotspot_lat"],r["hotspot_lon"])))
if ev: print(f"hotspot_dist_km:        err vs VENT med={st.median(ev):.4f} | err vs CATALOGO med={st.median(ec):.4f}")
