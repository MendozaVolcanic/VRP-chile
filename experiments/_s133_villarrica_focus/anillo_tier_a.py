# -*- coding: utf-8 -*-
"""S133 - El anillo de Villarrica, medido en los 11 Tier A.

FICHA SDA - medicion read-only sobre records persistidos; no toca la deteccion.

POR QUE. El mapa de Villarrica mostro que los cumulos VIIRS375 se pegan al crater mientras
MODIS y VIIRS750 forman un anillo a 2-4 km sobre la frontera nieve-roca (A69 amplificado por
el pixel grande). Nicolas pregunto si eso pasa en todos los volcanes. Se mide en vez de
suponerlo: distancia del centroide del primary_cluster al ANCLA de deteccion, por volcan y
sensor, sobre los records que el dashboard publica (magnitud > 0, summit).

Ancla: vent_lat/vent_lon si el volcan lo declara, si no lat/lon del catalogo. Se anota cual
se uso, porque en Villarrica el catalogo esta a 0,85 km del crater (A13) y eso desplaza
todas las distancias.
"""
import io, json, math, os, sys, statistics as st
import yaml
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DESDE = sys.argv[1] if len(sys.argv) > 1 else "2026-06-01"
TIER = ['Lascar','Isluga','Lastarria','Llaima','Villarrica','Copahue','Chaiten',
        'NevadosDeChillan','PlanchonPeteroa','PuyehueCordonCaulle','Tupungatito']

def hav(a,b,c,d):
    p=math.pi/180
    x=math.sin((c-a)*p/2)**2+math.cos(a*p)*math.cos(c*p)*math.sin((d-b)*p/2)**2
    return 2*6371*math.asin(math.sqrt(x))

cfg=yaml.safe_load(io.open(os.path.join(ROOT,"volcanoes.yaml"),encoding="utf-8"))
vols=cfg["volcanoes"] if isinstance(cfg,dict) and "volcanoes" in cfg else cfg
ancla={}
for v in (vols if isinstance(vols,list) else [dict(name=k,**x) for k,x in vols.items()]):
    if v.get("vent_lat") is not None: ancla[v["name"]]=(v["vent_lat"],v["vent_lon"],"vent")
    else: ancla[v["name"]]=(v["lat"],v["lon"],"catalogo")

res={}
print("Distancia del centroide del cumulo al ancla (km), records publicados desde %s"%DESDE)
print("%-20s %-8s | %-22s | %-22s | %-22s"%("volcan","ancla","VIIRS375 med (n) <=0.5","VIIRS750 med (n) <=0.5","MODIS med (n) <=0.5"))
print("-"*105)
for vol in TIER:
    p=os.path.join(ROOT,"data","mirova_equivalent",vol+".json")
    d=json.load(io.open(p,encoding="utf-8")); recs=d["records"] if isinstance(d,dict) and "records" in d else d
    la,lo,tipo=ancla[vol]; por={"VIIRS375":[],"VIIRS750":[],"MODIS":[]}
    for r in recs:
        if not isinstance(r,dict) or str(r.get("datetime_utc") or "")[:10]<DESDE: continue
        s=str(r.get("sensor") or "")
        k="MODIS" if s.startswith("MODIS") else ("VIIRS750" if s.endswith("750") else "VIIRS375") if s.startswith("VIIRS") else None
        if not k: continue
        pc=r.get("primary_cluster") or {}
        v=r.get("f5_core_vrp_mw") if k=="VIIRS375" else None
        if v is None: v=pc.get("vrp_mw")
        if not v or v<=0 or pc.get("centroid_lat") is None or r.get("distance_class")!="summit": continue
        por[k].append(hav(pc["centroid_lat"],pc["centroid_lon"],la,lo))
    fila=[]; res[vol]={"ancla":tipo}
    for k in ("VIIRS375","VIIRS750","MODIS"):
        x=por[k]
        if x:
            med=st.median(x); f=sum(1 for q in x if q<=0.5)/len(x)
            res[vol][k]={"n":len(x),"mediana_km":round(med,2),"frac_500m":round(f,3)}
            fila.append("%5.2f (%3d) %4.0f%%"%(med,len(x),100*f))
        else:
            res[vol][k]=None; fila.append("%-22s"%"—")
    print("%-20s %-8s | %-22s | %-22s | %-22s"%(vol,tipo,*fila))
json.dump({"desde":DESDE,"nota":"mediana de distancia centroide->ancla, records summit con magnitud>0","por_volcan":res},
          io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"anillo_tier_a.json"),"w",encoding="utf-8"),indent=2,ensure_ascii=False)
