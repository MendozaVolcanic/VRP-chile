# -*- coding: utf-8 -*-
"""VERIFICADOR S134 F3 - H1/H2/H3: reproduccion independiente sobre data/mirova_equivalent."""
import io, json, sys, math, statistics as st
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import yaml
BASE = r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
VOLS = yaml.safe_load(open(BASE+"/volcanoes.yaml", encoding="utf-8"))
vmap = {v["name"]: v for v in (VOLS["volcanoes"] if isinstance(VOLS, dict) else VOLS)}

def hav(la1, lo1, la2, lo2):
    R=6371.0088; p=math.radians
    dla=p(la2-la1); dlo=p(lo2-lo1)
    a=math.sin(dla/2)**2+math.cos(p(la1))*math.cos(p(la2))*math.sin(dlo/2)**2
    return 2*R*math.asin(math.sqrt(a))

TIER_A = ["Villarrica","Lascar","Copahue","Llaima","NevadosDeChillan","Isluga",
          "Lastarria","Chaiten","PlanchonPeteroa","PuyehueCordonCaulle","Tupungatito"]
SINCE = "2026-06-01"

def load(vol):
    d = json.load(open(f"{BASE}/data/mirova_equivalent/{vol}.json", encoding="utf-8"))
    return d["records"] if isinstance(d, dict) and "records" in d else d

print("=== flags/geom ===")
for v in TIER_A[:3]:
    c=vmap[v]; print(v, "vent", c.get("vent_lat"), c.get("vent_lon"), "inner", c.get("inner_radius_km"))

print("\n=== A) desglose final_hotspot_source, summit, V375, desde", SINCE, "===")
hdr = f"{'volcan':<22}{'n_sum':>6}{'test1_roi':>10}{'ctx':>6}{'otros':>7}"
print(hdr)
rows={}
for v in TIER_A:
    recs=[r for r in load(v) if r.get("sensor","").startswith("VIIRS")
          and not r.get("sensor","").endswith("_750")
          and r.get("datetime_utc","") >= SINCE
          and r.get("distance_class")=="summit"]
    c=Counter(r.get("final_hotspot_source") for r in recs)
    rows[v]=(recs,c)
    print(f"{v:<22}{len(recs):>6}{c.get('test1_roi',0):>10}{c.get('ctx_cluster',0):>6}"
          f"{sum(n for k,n in c.items() if k not in ('test1_roi','ctx_cluster')):>7}")

print("\n=== B) test1_roi: n_pixels y distancia REAL del pc.centroid al vent ===")
print(f"{'volcan':<22}{'n':>5}{'1px%':>7}{'med_dist':>10}{'p25':>7}{'p75':>7}{'en[2.5,3]':>10}")
for v in TIER_A:
    recs,_=rows[v]; cfg=vmap[v]
    tr=[r for r in recs if r.get("final_hotspot_source")=="test1_roi"]
    if not tr: print(f"{v:<22}{0:>5}"); continue
    npx=[ (r.get("primary_cluster") or {}).get("n_pixels") for r in tr]
    one=sum(1 for x in npx if x==1)
    ds=[]
    for r in tr:
        pc=r.get("primary_cluster") or {}
        if pc.get("centroid_lat") is not None:
            ds.append(hav(cfg["vent_lat"],cfg["vent_lon"],pc["centroid_lat"],pc["centroid_lon"]))
    ds.sort()
    if not ds: print(f"{v:<22}{len(tr):>5} sin centroid"); continue
    q=lambda p: ds[min(len(ds)-1,int(p*len(ds)))]
    inring=sum(1 for d in ds if 2.5<=d<=3.0)
    print(f"{v:<22}{len(tr):>5}{100*one/len(npx):>6.0f}%{st.median(ds):>10.2f}{q(.25):>7.2f}{q(.75):>7.2f}"
          f"{inring:>7}/{len(ds)}")

print("\n=== C) ctx_cluster control: distancia real al vent ===")
for v in TIER_A:
    recs,_=rows[v]; cfg=vmap[v]
    cc=[r for r in recs if r.get("final_hotspot_source")=="ctx_cluster"]
    ds=[]
    for r in cc:
        pc=r.get("primary_cluster") or {}
        if pc.get("centroid_lat") is not None:
            ds.append(hav(cfg["vent_lat"],cfg["vent_lon"],pc["centroid_lat"],pc["centroid_lon"]))
    if ds: print(f"{v:<22} n={len(ds):>4} med={st.median(ds):.2f} km")

print("\n=== D) H3: pc.centroid != final_hotspot (Villarrica/Llaima/Tupungatito) ===")
for v in ["Villarrica","Llaima","Tupungatito"]:
    recs,_=rows[v]
    ctx=[r for r in recs if r.get("final_hotspot_source")=="ctx_cluster"]
    dif=0
    for r in ctx:
        pc=r.get("primary_cluster") or {}
        if pc.get("centroid_lat") is None or r.get("final_hotspot_lat") is None: continue
        if abs(pc["centroid_lat"]-r["final_hotspot_lat"])>1e-5 or abs(pc["centroid_lon"]-r["final_hotspot_lon"])>1e-5:
            dif+=1
    print(f"{v:<22} ctx n={len(ctx)} pc!=final={dif}")
