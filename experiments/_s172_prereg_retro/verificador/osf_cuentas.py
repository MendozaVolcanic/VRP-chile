# -*- coding: utf-8 -*-
"""VPR172 V-4: recalcula sobre el OSF local los conteos del borrador (§4.2, §7). Copia: sha 0863c240... (el del borrador).
P1: control positivo = filas totales 615470 y esquema; un cero se lee solo si n filas>0.
P2: instrumento muerto: cada conteo imprime el denominador (filas Chile en la ventana)."""
import pandas as pd, numpy as np, io, sys, yaml, collections, math
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
P = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\data\mirova_reference\VRP_GLOBAL_ARCHIVE_2025.csv"
df = pd.read_csv(P, low_memory=False)
df["t"] = pd.to_datetime(df["timeUTC"], format="%d/%m/%Y %H:%M")
print("filas", len(df), "rango", df.t.min(), df.t.max())
vols = yaml.safe_load(open(r"D:\vrp-trabajo\temporales\ver_s172_prereg_retro\export_main\volcanoes.yaml", encoding="utf-8"))
vl = vols["volcanoes"] if isinstance(vols, dict) and "volcanoes" in vols else vols
tier = [v for v in vl if v.get("radius_km")==25] if isinstance(vl, list) else None
print("Tier A en yaml:", [(v["name"], v.get("inner_radius_km")) for v in tier])
names = sorted(df.Volc_Name.unique())
chile = df[(df.Volc_LAT<-17)&(df.Volc_LAT>-56)&(df.Volc_LON<-65)&(df.Volc_LON>-76)]
print("volcanes OSF en Chile:", sorted(chile.Volc_Name.unique()))
print("Satellite x Resolution (Chile, todo):"); print(pd.crosstab(chile.Satellite, chile.Resolution))
print("Satellite x anio, Chile 375/750:"); 
c2 = chile[chile.Resolution.isin([375,750])]
print(pd.crosstab(c2.t.dt.year, c2.Satellite))
w = chile[(chile.t>="2025-02-15")&(chile.t<"2026-01-01")]
print("Chile 2025-02-15..12-31:", len(w), w.Volc_Name.value_counts().to_dict())
print("Dayflag:", w.Dayflag.value_counts().to_dict(), "horas UTC min/max Dayflag0:", w[w.Dayflag==0].t.dt.hour.min(), w[w.Dayflag==0].t.dt.hour.max(),
      "Dayflag1 horas:", sorted(w[w.Dayflag==1].t.dt.hour.unique()))
print("VRP min por resolucion (W):"); print(w.groupby("Resolution").VRP.agg(["min","median","max","count"]))
# piso en todo el archivo Chile y global por resolucion
print("VRP minimo global por resolucion 2025:"); g=df[df.t.dt.year==2025]; print(g.groupby("Resolution").VRP.min())
print("VRP minimo global por resolucion 2020-2025:"); print(df[df.t.dt.year>=2020].groupby("Resolution").VRP.min())
# satelites en 2025 global
print("Sat x Res 2025 global:"); print(pd.crosstab(g.Satellite, g.Resolution))
print("Sat x Res Chile 2025-26:"); print(pd.crosstab(w.Satellite, w.Resolution))
# protegida: nocturna Dayflag 0, class 1, VRP>=1e6, distancia del pixel LAT/LON a cumbre yaml <= inner
def hav(lat1,lon1,lat2,lon2):
    R=6371.0088; p1=np.radians(lat1);p2=np.radians(lat2);dl=np.radians(lon2-lon1);dp=p2-p1
    a=np.sin(dp/2)**2+np.cos(p1)*np.cos(p2)*np.sin(dl/2)**2
    return 2*R*np.arcsin(np.sqrt(a))
# mapear nombres OSF -> yaml
import unicodedata
def norm(s): return unicodedata.normalize("NFKD", s).encode("ascii","ignore").decode().lower().replace(" ","").replace("-","").replace("_","")
yamap = {norm(v["name"]): v for v in tier}
print("claves yaml:", list(yamap))
osfn = {n: norm(n) for n in w.Volc_Name.unique()}
print("osf->norm:", osfn)
