# -*- coding: utf-8 -*-
"""VERIF/03 - hallazgo 2: 'separacion mediana 0,21 km' es una DIFERENCIA DE RADIOS.

EL PROBLEMA GEOMETRICO. El CSV de MIROVA entrega Distancia_km, un ESCALAR: no hay lat/lon
del cumulo de MIROVA en ninguna columna. 08_reanclar compara |nuestro|_mc contra |MIROVA|_mc,
dos RADIOS desde el mismo centro. La diferencia de dos radios no es la distancia entre los
dos puntos: dos puntos a 7,65 y 7,96 km del mismo centro pueden estar a 0,31 km o a 15,6 km
segun el acimut, que no se conoce. Mido: (a) las columnas del CSV; (b) la cota superior
r1+r2 por volcan; (c) donde el TIF SI es arbitro (Lascar, PP; control 03_/07_), la separacion
2D VERDADERA entre nuestro centroide y el maximo del TIF dentro del inner.
Read-only. No baja ningun TIF nuevo (aborta si falta el archivo)."""
import os, sys, io, csv, json, math, datetime as dt, statistics as st
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
WT   = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP-Chile-s134-f2"
TIFD = os.path.join(WT, "experiments", "_s134_audit", "tif")
sys.path.insert(0, RAIZ)
import numpy as np, yaml, rasterio
CAT = {v["name"]: v for v in yaml.safe_load(open(os.path.join(RAIZ,"volcanoes.yaml"),encoding="utf-8"))["volcanoes"]}
F2 = os.path.join(RAIZ,"experiments","_s134_audit","f2")
R = json.load(open(os.path.join(F2,"resultados.json"),encoding="utf-8"))["filas"]
IBAND=("VIIRS_SNPP","VIIRS_NOAA20","VIIRS_NOAA21")
def pu(s_):
    t=dt.datetime.fromisoformat(str(s_).replace("Z","+00:00"))
    return t.replace(tzinfo=dt.timezone.utc) if t.tzinfo is None else t.astimezone(dt.timezone.utc)
_CACHE={}
def centroide(v, pasada):
    """centroide del primary_cluster del record de esa pasada (mismo criterio que 08_)."""
    if v not in _CACHE:
        d={}
        for r in json.load(open(os.path.join(RAIZ,"data","mirova_equivalent",v+".json"),encoding="utf-8"))["records"]:
            if r.get("sensor") not in IBAND: continue
            try: t=pu(r["datetime_utc"])
            except Exception: continue
            d[t.strftime("%Y-%m-%d %H:%M:%S")]=r
        _CACHE[v]=d
    d=_CACHE[v]; r0=d.get(pasada)
    if r0 is None:
        c=[rr for k,rr in d.items() if k[:16]==pasada[:16]]
        r0=c[0] if c else None
    if r0 is None: return None
    pc=r0.get("primary_cluster") or {}
    if pc.get("centroid_lat") is None: return None
    return pc["centroid_lat"], pc["centroid_lon"]

def hav(a,b,c,d):
    Rk=6371.0088; p1,p2=math.radians(a),math.radians(c)
    x=(math.sin((p2-p1)/2)**2+math.cos(p1)*math.cos(p2)*math.sin(math.radians(d-b)/2)**2)
    return 2*Rk*math.asin(math.sqrt(x))

print("="*88)
print("(a) el CSV de MIROVA: hay coordenadas del cumulo?")
h = next(csv.reader(open(os.path.join(RAIZ,"data","mirova_reference","mirova_v1_snapshot","registro_vrp_consolidado.csv"),encoding="utf-8")))
print("   columnas CONS:", h)
print("   columnas con 'lat'/'lon':", [c for c in h if "lat" in c.lower() or "lon" in c.lower()] or "NINGUNA")
print("   -> la posicion de MIROVA es un ESCALAR (radio). El acimut no existe en el dato.")

print("="*88)
print("(b) cota de la separacion real por volcan (r1=nuestro@mc, r2=MIROVA_decl)")
print("%-21s %4s | %-9s %-9s | %-11s | %s" % ("volcan","n","r1_med","r2_med","|r1-r2| (lo que reporta 08_)","cota sup r1+r2"))
claves = {}
for v in sorted(set(x["volcan"] for x in R)):
    c=CAT[v]
    if c.get("mirova_center_lat") is None: continue
    mla,mlo=c["mirova_center_lat"],c["mirova_center_lon"]
    p=[]
    for x in R:
        if x["volcan"]!=v or x.get("dist_km_mirova") is None: continue
        ct=centroide(v,x["pasada_utc"])
        if ct is None: continue
        r1=hav(mla,mlo,ct[0],ct[1])
        p.append((r1,x["dist_km_mirova"]))
    if not p: continue
    r1=[a for a,_ in p]; r2=[b for _,b in p]
    print("%-21s %4d | %-9.2f %-9.2f | %-11.2f | %.2f" % (
        v,len(p),st.median(r1),st.median(r2),
        st.median([abs(a-b) for a,b in p]), st.median([a+b for a,b in p])))
print("   -> la separacion real esta ENTRE las dos ultimas columnas; el dato no la determina.")

print("="*88)
print("(c) separacion 2D VERDADERA donde el TIF si es arbitro (Lascar, PlanchonPeteroa)")
print("    proxy del cumulo de MIROVA = maximo del TIF dentro del inner (control 03_/07_)")
for VOL in ("Lascar","PlanchonPeteroa","Isluga","Villarrica"):
    c=CAT[VOL]; vla,vlo=c["vent_lat"],c["vent_lon"]; inner=float(c["inner_radius_km"])
    seps=[]; falt=0
    for x in [r for r in R if r["volcan"]==VOL]:
        ct=centroide(VOL,x["pasada_utc"])
        if ct is None or not x.get("tif"): continue
        p = os.path.join(TIFD, ("tif/"+x["tif"]).replace("/","__"))
        if not os.path.exists(p):
            cand=[f for f in os.listdir(TIFD) if f.endswith(x["tif"])]
            if not cand: falt+=1; continue
            p=os.path.join(TIFD,cand[0])
        with rasterio.open(p) as s:
            a=s.read(1).astype(float)
            if s.nodata is not None: a=np.where(a==s.nodata,np.nan,a)
            T=s.transform; hgt,w=a.shape
        j,i=np.meshgrid(np.arange(w),np.arange(hgt))
        lon=T.c+(j+0.5)*T.a+(i+0.5)*T.b; lat=T.f+(j+0.5)*T.d+(i+0.5)*T.e
        dn=(lat-vla)*111.320; de=(lon-vlo)*111.320*math.cos(math.radians(vla))
        dg=np.hypot(dn,de)
        f=np.where((dg<=inner)&np.isfinite(a),a,-np.inf)
        if not np.isfinite(f).any(): continue
        ii,jj=np.unravel_index(int(np.argmax(f)),f.shape)
        seps.append(hav(float(lat[ii,jj]),float(lon[ii,jj]),ct[0],ct[1]))
    if seps:
        seps.sort()
        print("  %-21s n=%-3d separacion 2D real: p50=%.2f km  p90=%.2f km  max=%.2f km  (<0.375 km: %.0f%%)  faltan_tif=%d" % (
            VOL,len(seps),seps[len(seps)//2],seps[int(.9*len(seps))],seps[-1],
            100*sum(1 for s_ in seps if s_<0.375)/len(seps),falt))
    else:
        print("  %-21s SIN DATO (faltan_tif=%d)" % (VOL,falt))
