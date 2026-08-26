# -*- coding: utf-8 -*-
"""Donde se pierde el VRP: en la DETECCION o en la ATRIBUCION al cluster?

Tres candidatos contra el VRP que MIROVA publico esa noche:
  A. vent_anchored : primary_cluster (lo que reportamos hoy)
  B. vrp_max       : el mejor cluster de la escena (re-agrupado offline)
  C. scene_total   : la suma de TODOS los anomaly_pixels de la escena

Interpretacion:
  - Si C ~ 1.0 o mas -> detectamos radiancia suficiente; la perdemos al
    ATRIBUIRLA (seleccion de cluster / que pixeles entran).
  - Si C < 1.0 todavia -> no detectamos bastante RADIANCIA. El problema esta
    aguas arriba, en que pixeles pasan el gate.
"""
import sys, os, json, math, statistics
from collections import defaultdict
from datetime import datetime, timezone
sys.path.insert(0, os.getcwd())
from pipeline.store import _solar_elevation, _reject_daytime
from pipeline.profile import ENABLE_DAYTIME_MODIS
from pipeline.mirova_csv_loader import load_mirova_alertas
from scripts.auto_audit_weekly import our_bucket, INNER, SENSORS, CONS, OCR
import yaml
CO={v["name"]:(v["lat"],v["lon"]) for v in yaml.safe_load(open("volcanoes.yaml",encoding="utf-8"))["volcanoes"]}
WIN=("2026-04-01","2026-08-24")
ESP={"MODIS":1.0,"VIIRS375":0.375,"VIIRS750":0.75}
FOCO=["Lascar","Isluga","Lastarria","PlanchonPeteroa","Chaiten"]  # 3 fuera + 2 control

def hav(a,b,c,d):
    R=6371.0;p1,p2=math.radians(a),math.radians(c)
    x=math.sin(math.radians(c-a)/2)**2+math.cos(p1)*math.cos(p2)*math.sin(math.radians(d-b)/2)**2
    return 2*R*math.asin(math.sqrt(x))

def mejor_cluster(px, u):
    n=len(px); pa=list(range(n))
    def f(i):
        while pa[i]!=i: pa[i]=pa[pa[i]]; i=pa[i]
        return i
    for i in range(n):
        for j in range(i+1,n):
            if hav(px[i]["lat"],px[i]["lon"],px[j]["lat"],px[j]["lon"])<=u:
                a,b=f(i),f(j)
                if a!=b: pa[a]=b
    g=defaultdict(list)
    for i in range(n): g[f(i)].append(px[i])
    return max((sum(p.get("vrp_mw") or 0 for p in gr), len(gr)) for gr in g.values())

print(f"=== Descomposicion de la brecha · {WIN[0]}..{WIN[1]} ===")
print(f"{'volcan':<20}{'n':>5}{'A vent':>9}{'B max':>8}{'C escena':>10}{'px_ours':>9}")
for vol in FOCO:
    lat0,lon0=CO[vol]
    mir=defaultdict(float)
    for a in load_mirova_alertas(cons_path=CONS,ocr_path=OCR,volcano=vol):
        fu=a["fecha_utc"] or ""
        if not (WIN[0]<=fu[:10]<=WIN[1]) or a["sensor_bucket"] not in SENSORS: continue
        s={"MODIS":"MODIS_TERRA","VIIRS375":"VIIRS_SNPP","VIIRS750":"VIIRS_SNPP_750"}[a["sensor_bucket"]]
        if _reject_daytime(s,_solar_elevation(lat0,lon0,datetime.fromisoformat(fu).replace(tzinfo=timezone.utc)),ENABLE_DAYTIME_MODIS): continue
        k=(a["sensor_bucket"],fu[:10]); mir[k]=max(mir[k],a["vrp_mw"] or 0)
    d=json.load(open(f"data/mirova_equivalent/{vol}.json",encoding="utf-8"))
    acc=defaultdict(lambda:{"A":0.0,"B":0.0,"C":0.0,"px":0})
    for r in d["records"]:
        dt=r.get("datetime_utc") or ""
        if not (WIN[0]<=dt[:10]<=WIN[1]): continue
        b=our_bucket(r.get("sensor",""))
        if b is None: continue
        k=(b,dt[:10])
        if k not in mir: continue
        pc=r.get("primary_cluster") or {}; cd=pc.get("centroid_dist_km")
        if (pc.get("vrp_mw") or 0)>0 and cd is not None and cd<=INNER[vol]:
            acc[k]["A"]=max(acc[k]["A"],pc["vrp_mw"])
        px=[p for p in (r.get("anomaly_pixels") or []) if p.get("lat") is not None]
        if px:
            acc[k]["C"]=max(acc[k]["C"], sum(p.get("vrp_mw") or 0 for p in px))
            acc[k]["px"]=max(acc[k]["px"], len(px))
            if len(px)<=400:
                v,_=mejor_cluster(px,ESP[b]*1.5); acc[k]["B"]=max(acc[k]["B"],v)
    rA=[a["A"]/mir[k] for k,a in acc.items() if a["A"]>0 and mir[k]>0]
    rB=[a["B"]/mir[k] for k,a in acc.items() if a["B"]>0 and mir[k]>0]
    rC=[a["C"]/mir[k] for k,a in acc.items() if a["C"]>0 and mir[k]>0]
    pxs=[a["px"] for a in acc.values() if a["px"]>0]
    if not rA: continue
    med=lambda x: statistics.median(x) if x else 0
    print(f"{vol:<20}{len(rA):>5}{med(rA):>9.2f}{med(rB):>8.2f}{med(rC):>10.2f}{med(pxs):>9.0f}")
print("\n  C = suma de TODA la escena. Si C sigue <1, no es atribucion: es deteccion.")
