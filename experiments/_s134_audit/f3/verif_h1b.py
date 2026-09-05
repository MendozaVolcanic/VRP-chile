# -*- coding: utf-8 -*-
import io,json,sys,math,statistics as st
from collections import Counter
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
recs=[r for r in load("Villarrica") if r.get("sensor","").startswith("VIIRS")
      and not r.get("sensor","").endswith("_750") and r.get("datetime_utc","")>="2026-06-01"
      and r.get("distance_class")=="summit"]
tr=[r for r in recs if r.get("final_hotspot_source")=="test1_roi"]
print("n test1_roi:",len(tr))
print("\n--- claves disponibles (1 record) ---")
print(sorted(k for k in tr[0].keys()))
print("\n--- claves *dist* / *t_bg* / *t_max* ---")
ks=set()
for r in tr: ks|=set(r.keys())
print([k for k in sorted(ks) if 'dist' in k or 't_bg' in k or 't_max' in k or 'bt' in k.lower()])
ap=tr[0].get("anomaly_pixels")
if ap: print("\nanomaly_pixels[0] keys:",sorted(ap[0].keys()))
print("\n--- H1(d): BT del pico vs fondo ---")
tb=[];tm=[];cmp_lt=0;n=0
for r in tr:
    a=r.get("diag_t_max_k") or r.get("t_max_i04") or r.get("diag_t_max_i04")
    b=r.get("diag_t_bg_k") or r.get("t_bg_i04") or r.get("diag_t_bg_i04")
    if a is None or b is None: continue
    n+=1; tm.append(a); tb.append(b)
    if a<b: cmp_lt+=1
print(f"n con ambos={n}  t_max<t_bg en {cmp_lt}  ({100*cmp_lt/max(n,1):.0f}%)")
if n: print(f"  med t_max={st.median(tm):.2f}K  med t_bg={st.median(tb):.2f}K  med delta={st.median([x-y for x,y in zip(tm,tb)]):.2f}K")
print("\n--- ctx_cluster Villarrica: distribucion de distancia ---")
cfg=vmap["Villarrica"]
ds=sorted(hav(cfg["vent_lat"],cfg["vent_lon"],(r["primary_cluster"] or {})["centroid_lat"],(r["primary_cluster"])["centroid_lon"])
          for r in recs if r.get("final_hotspot_source")=="ctx_cluster" and (r.get("primary_cluster") or {}).get("centroid_lat") is not None)
print("n=",len(ds),"min=%.2f p25=%.2f med=%.2f p75=%.2f max=%.2f"%(ds[0],ds[len(ds)//4],st.median(ds),ds[3*len(ds)//4],ds[-1]))
print("ctx en [2.5,3.0]:",sum(1 for d in ds if 2.5<=d<=3.0),"/",len(ds))
print("ctx >3.0 km:",sum(1 for d in ds if d>3.0))
print("\n--- final_hotspot_dist_km publicado para test1_roi ---")
print(Counter(round(r.get("final_hotspot_dist_km") or -1,2) for r in tr).most_common(5))
print("\n--- pc.vrp_mw test1_roi ---")
vv=sorted(float((r.get("primary_cluster") or {}).get("vrp_mw") or 0) for r in tr)
print("min=%.4f p25=%.4f med=%.4f p75=%.4f max=%.4f"%(vv[0],vv[len(vv)//4],st.median(vv),vv[3*len(vv)//4],vv[-1]))
