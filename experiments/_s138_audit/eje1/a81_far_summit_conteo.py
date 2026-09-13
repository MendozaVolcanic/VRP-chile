"""EJE 1 S138: conteo A81 cara (b) far->summit oculto, con denominador y ventana (A90).
Pregunta 1: si el bug no existiera (0 records con pc dentro del inner y distance_class!=summit) el conteo daria 0 y lo veria.
Pregunta 2: si el instrumento estuviera muerto (campos ausentes) se reporta 'sin_campo' aparte, no como 0.
Control positivo: cuenta tambien la cara (a) y los summit coherentes; si todo da 0 el lector esta roto.
"""
import json, glob, math, os, sys, yaml
from collections import Counter, defaultdict
os.chdir(os.path.dirname(os.path.abspath(__file__)) + "/../../..")
vols = {v["name"]: v for v in yaml.safe_load(open("volcanoes.yaml"))["volcanoes"]}
def hav(a,b,c,d):
    R=6371.0; p1,p2=math.radians(a),math.radians(c); dp=p2-p1; dl=math.radians(d-b)
    h=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(h))
tot=Counter(); permes=defaultdict(Counter); fechas=[]
for f in sorted(glob.glob("data/mirova_equivalent/*.json")):
    name=os.path.basename(f)[:-5]
    if name not in vols or vols[name].get("radius_km")!=25: continue
    v=vols[name]; inner=v.get("inner_radius_km"); vlat,vlon=v.get("vent_lat"),v.get("vent_lon")
    recs=json.load(open(f,encoding="utf-8"))
    if isinstance(recs,dict): recs=recs.get("records",[])
    for r in recs:
        pc=r.get("primary_cluster") or {}
        dc=r.get("distance_class")
        if not pc or pc.get("vrp_mw") in (None,0,0.0):
            tot["sin_cluster_o_vrp0"]+=1; continue
        clat,clon=pc.get("centroid_lat"),pc.get("centroid_lon")
        if clat is None or clon is None or dc is None:
            tot["sin_campo"]+=1; continue
        d=hav(vlat,vlon,clat,clon); mes=(r.get("datetime_utc") or "")[:7]
        fechas.append(mes)
        if d<=inner and dc!="summit": k="b_far_pero_pc_dentro_inner"
        elif d>inner and dc=="summit": k="a_summit_pero_pc_fuera_inner"
        elif d<=inner and dc=="summit": k="coherente_summit"
        else: k="coherente_far"
        tot[k]+=1; permes[mes][k]+=1
tot_eval=sum(v for k,v in tot.items() if not k.startswith("sin"))
print("denominador (records Tier A con cluster y vrp>0):",tot_eval)
print("ventana:",min(x for x in fechas if x),"a",max(fechas))
for k,v in sorted(tot.items()): print(f"{k:32s} {v:6d}  {100*v/tot_eval if tot_eval else 0:5.1f}%")
print("\ntasa mensual cara (b) sobre records evaluados:")
for m in sorted(permes):
    c=permes[m]; n=sum(c.values()); print(m, n, f"{100*c['b_far_pero_pc_dentro_inner']/n:5.1f}%")
