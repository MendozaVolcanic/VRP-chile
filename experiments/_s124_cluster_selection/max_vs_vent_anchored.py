# -*- coding: utf-8 -*-
"""Cual selection de cluster se parece mas a MIROVA: el MAXIMO o el vent-anchored?

La pregunta de Nicolas: "en el operacional no reportamos la mayor? deberiamos".
La informacion esta: anomaly_pixels guarda lat/lon/vrp por pixel, asi que el
cluster de VRP maximo se reconstruye offline sin reprocesar.

Se re-agrupa por enlace de distancia (single-linkage al espaciado del sensor,
x1.5 para cubrir la diagonal = la connectivity-8 del pipeline) y se comparan
DOS candidatos contra el valor que MIROVA publico esa noche:
  - vent_anchored : lo que hoy guardamos en primary_cluster
  - vrp_max       : el cluster de mayor VRP de la escena
"""
import sys, os, json, math, statistics
from collections import defaultdict
from datetime import datetime, timezone
sys.path.insert(0, os.getcwd())
from pipeline.store import _solar_elevation, _reject_daytime
from pipeline.profile import ENABLE_DAYTIME_MODIS
from pipeline.mirova_csv_loader import load_mirova_alertas
from scripts.auto_audit_weekly import our_bucket, VOLS, INNER, SENSORS, CONS, OCR
import yaml
CO={v["name"]:(v["lat"],v["lon"]) for v in yaml.safe_load(open("volcanoes.yaml",encoding="utf-8"))["volcanoes"]}
WIN=("2026-04-01","2026-08-24")
ESPACIADO={"MODIS":1.0,"VIIRS375":0.375,"VIIRS750":0.75}

def hav(a,b,c,d):
    R=6371.0;p1,p2=math.radians(a),math.radians(c)
    x=math.sin(math.radians(c-a)/2)**2+math.cos(p1)*math.cos(p2)*math.sin(math.radians(d-b)/2)**2
    return 2*R*math.asin(math.sqrt(x))

def recluster(pixels, umbral_km):
    """single-linkage por distancia -> lista de clusters con vrp y centroide."""
    n=len(pixels); padre=list(range(n))
    def find(i):
        while padre[i]!=i: padre[i]=padre[padre[i]]; i=padre[i]
        return i
    for i in range(n):
        for j in range(i+1,n):
            if hav(pixels[i]["lat"],pixels[i]["lon"],pixels[j]["lat"],pixels[j]["lon"])<=umbral_km:
                a,b=find(i),find(j)
                if a!=b: padre[a]=b
    grupos=defaultdict(list)
    for i in range(n): grupos[find(i)].append(pixels[i])
    out=[]
    for g in grupos.values():
        v=sum(p.get("vrp_mw") or 0 for p in g)
        out.append({"vrp_mw":v,"n":len(g),
                    "lat":sum(p["lat"] for p in g)/len(g),
                    "lon":sum(p["lon"] for p in g)/len(g)})
    return out

res=defaultdict(lambda: {"vent":[], "max":[]})
for vol in VOLS:
    lat0,lon0=CO[vol]
    mir=defaultdict(float)
    for a in load_mirova_alertas(cons_path=CONS,ocr_path=OCR,volcano=vol):
        fu=a["fecha_utc"] or ""
        if not (WIN[0]<=fu[:10]<=WIN[1]) or a["sensor_bucket"] not in SENSORS: continue
        dt=datetime.fromisoformat(fu).replace(tzinfo=timezone.utc)
        sens={"MODIS":"MODIS_TERRA","VIIRS375":"VIIRS_SNPP","VIIRS750":"VIIRS_SNPP_750"}[a["sensor_bucket"]]
        if _reject_daytime(sens,_solar_elevation(lat0,lon0,dt),ENABLE_DAYTIME_MODIS): continue
        k=(a["sensor_bucket"],fu[:10]); mir[k]=max(mir[k],a["vrp_mw"] or 0)
    if not mir: continue
    d=json.load(open(f"data/mirova_equivalent/{vol}.json",encoding="utf-8"))
    por=defaultdict(lambda: {"vent":0.0,"max":0.0})
    for r in d["records"]:
        dt=r.get("datetime_utc") or ""
        if not (WIN[0]<=dt[:10]<=WIN[1]): continue
        b=our_bucket(r.get("sensor",""))
        if b is None: continue
        k=(b,dt[:10])
        if k not in mir: continue
        pc=r.get("primary_cluster") or {}
        cd=pc.get("centroid_dist_km")
        if (pc.get("vrp_mw") or 0)>0 and cd is not None and cd<=INNER[vol]:
            por[k]["vent"]=max(por[k]["vent"], pc["vrp_mw"])
        px=[p for p in (r.get("anomaly_pixels") or []) if p.get("lat") is not None]
        if px and len(px)<=400:
            cl=recluster(px, ESPACIADO[b]*1.5)
            if cl:
                mejor=max(cl,key=lambda c:c["vrp_mw"])
                por[k]["max"]=max(por[k]["max"], mejor["vrp_mw"])
    for k,vv in por.items():
        if mir[k]>0:
            if vv["vent"]>0: res[vol]["vent"].append(vv["vent"]/mir[k])
            if vv["max"]>0:  res[vol]["max"].append(vv["max"]/mir[k])

print(f"=== Ratio contra MIROVA · {WIN[0]}..{WIN[1]} · noches pareadas nocturnas ===")
print(f"{'volcan':<24}{'n':>4}{'vent_anchored':>16}{'vrp_max':>12}{'cual gana':>14}")
gv,gm=[],[]
for vol in sorted(res):
    v,m=res[vol]["vent"],res[vol]["max"]
    if not v: continue
    mv,mm=statistics.median(v),(statistics.median(m) if m else None)
    gv+=v; gm+=m
    def err(x): return abs(math.log(x)) if x and x>0 else 99
    gana = "-" if mm is None else ("vent" if err(mv)<err(mm) else "MAX")
    print(f"{vol:<24}{len(v):>4}{mv:>16.2f}{(mm if mm else 0):>12.2f}{gana:>14}")
print(f"{'GLOBAL':<24}{len(gv):>4}{statistics.median(gv):>16.2f}{statistics.median(gm):>12.2f}")
print("\n(ratio 1.00 = paridad perfecta con MIROVA; se compara cual queda mas cerca de 1)")
