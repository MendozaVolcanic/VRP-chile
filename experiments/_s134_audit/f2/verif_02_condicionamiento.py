# -*- coding: utf-8 -*-
"""VERIF/02 - robustez del hallazgo 3 (condicionamiento) sin exigir TIF, y sesgo de seleccion.

C4  El hallazgo 3 no necesita el TIF: 06_ lee resultados.json, que exige TIF+record a <=120 s
    y por eso pierde el 61% de las ALERTAS. Recomputo con TODAS las ALERTAS V375.
C5  Sesgo de seleccion: si el motor fuera la INTENSIDAD (y la ALERTA solo su proxy), los
    records SIN alerta pero de magnitud alta tambien caerian en el crater. Estratifico.
Read-only."""
import os, sys, io, json, datetime as dt, statistics as st, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
sys.path.insert(0, RAIZ)
from pipeline.mirova_csv_loader import load_mirova_alertas
import yaml
D0 = dt.datetime(2026, 6, 1, tzinfo=dt.timezone.utc)
IBAND = ("VIIRS_SNPP","VIIRS_NOAA20","VIIRS_NOAA21")
BASE = os.path.join(RAIZ,"data","mirova_reference","mirova_v1_snapshot")
CAT = {v["name"]: v for v in yaml.safe_load(open(os.path.join(RAIZ,"volcanoes.yaml"),encoding="utf-8"))["volcanoes"]}
VOLS = ["Lascar","Isluga","PuyehueCordonCaulle","Tupungatito","Lastarria","PlanchonPeteroa",
        "Chaiten","NevadosDeChillan","Villarrica","Copahue","Llaima"]

def hav(a,b,c,d):
    R=6371.0088; p1,p2=math.radians(a),math.radians(c)
    x=(math.sin((p2-p1)/2)**2+math.cos(p1)*math.cos(p2)*math.sin(math.radians(d-b)/2)**2)
    return 2*R*math.asin(math.sqrt(x))
def pu(s):
    t=dt.datetime.fromisoformat(str(s).replace("Z","+00:00"))
    return t.replace(tzinfo=dt.timezone.utc) if t.tzinfo is None else t.astimezone(dt.timezone.utc)

def recs(v):
    out=[]
    for r in json.load(open(os.path.join(RAIZ,"data","mirova_equivalent",v+".json"),encoding="utf-8"))["records"]:
        if r.get("sensor") not in IBAND: continue
        try: t=pu(r["datetime_utc"])
        except Exception: continue
        if t<D0: continue
        r["_ts"]=t; out.append(r)
    return out

def publicado(r, vla, vlo):
    """criterio S133: summit + magnitud>0 + centroide. Devuelve (d_crater, magnitud)."""
    if r.get("distance_class")!="summit": return None
    p=r.get("primary_cluster") or {}
    m=r.get("f5_core_vrp_mw");  m=p.get("vrp_mw") if m is None else m
    if not m or m<=0: return None
    if p.get("centroid_lat") is None: return None
    return hav(vla,vlo,p["centroid_lat"],p["centroid_lon"]), m

print("="*94)
print("C4 - condicionamiento SIN exigir TIF (todas las ALERTAS V375, record a <=120 s)")
print("%-21s %8s | %-16s | %-18s | %s" % ("volcan","alertas","todos (n)","con ALERTA (n)","06_ reportaba (n)"))
print("-"*94)
prev = json.load(open(os.path.join(RAIZ,"experiments","_s134_audit","f2","control_condicionamiento.json"),encoding="utf-8"))
desp=[]
for v in VOLS:
    c=CAT[v]; vla,vlo=c["vent_lat"],c["vent_lon"]
    R=recs(v)
    al=[dt.datetime.fromtimestamp(int(x["timestamp"]),dt.timezone.utc)
        for x in load_mirova_alertas(cons_path=os.path.join(BASE,"registro_vrp_consolidado.csv"),
                                     ocr_path=os.path.join(BASE,"registro_vrp_ocr.csv"), volcano=v)
        if x.get("sensor_bucket")=="VIIRS375" and dt.datetime.fromtimestamp(int(x["timestamp"]),dt.timezone.utc)>=D0]
    todos=[]; conal=[]
    for r in R:
        pv=publicado(r,vla,vlo)
        if pv is None: continue
        todos.append(pv[0])
        if any(abs((r["_ts"]-t).total_seconds())<=120 for t in al): conal.append(pv[0])
    p=prev.get(v,{})
    print("%-21s %8d | %6s km (n=%-4d) | %6s km (n=%-4d) | %6s km (n=%d)" % (
        v, len(al),
        "%.2f"%st.median(todos) if todos else "s/d", len(todos),
        "%.2f"%st.median(conal) if conal else "s/d", len(conal),
        p.get("con_alerta_km"), p.get("con_alerta_n") or 0))
    if todos and conal: desp.append(st.median(conal)-st.median(todos))
print("  mediana del desplazamiento (mi recomputo, n=%d volcanes): %+.2f km" % (len(desp), st.median(desp)))

print("="*94)
print("C5 - SESGO DE SELECCION: records SIN alerta, estratificados por magnitud propia")
print("Si la ALERTA fuera solo proxy de intensidad, el decil alto SIN alerta tambien caeria al crater.")
print("%-21s | %-24s | %-24s | %s" % ("volcan","sin alerta, decil BAJO","sin alerta, decil ALTO","con ALERTA"))
print("-"*94)
for v in VOLS:
    c=CAT[v]; vla,vlo=c["vent_lat"],c["vent_lon"]
    R=recs(v)
    al=[dt.datetime.fromtimestamp(int(x["timestamp"]),dt.timezone.utc)
        for x in load_mirova_alertas(cons_path=os.path.join(BASE,"registro_vrp_consolidado.csv"),
                                     ocr_path=os.path.join(BASE,"registro_vrp_ocr.csv"), volcano=v)
        if x.get("sensor_bucket")=="VIIRS375" and dt.datetime.fromtimestamp(int(x["timestamp"]),dt.timezone.utc)>=D0]
    sin=[]; con=[]
    for r in R:
        pv=publicado(r,vla,vlo)
        if pv is None: continue
        if any(abs((r["_ts"]-t).total_seconds())<=120 for t in al): con.append(pv)
        else: sin.append(pv)
    if len(sin)<20: print("%-21s | n insuficiente (%d)"%(v,len(sin))); continue
    sin.sort(key=lambda x:x[1])
    k=max(1,len(sin)//10)
    bajo=sin[:k]; alto=sin[-k:]
    print("%-21s | %5.2f km (n=%-3d mag %.3f) | %5.2f km (n=%-3d mag %.3f) | %s km (n=%d)" % (
        v, st.median([x[0] for x in bajo]), len(bajo), st.median([x[1] for x in bajo]),
        st.median([x[0] for x in alto]), len(alto), st.median([x[1] for x in alto]),
        "%.2f"%st.median([x[0] for x in con]) if con else "s/d", len(con)))
