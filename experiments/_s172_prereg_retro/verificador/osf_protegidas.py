# -*- coding: utf-8 -*-
"""VPR172 V-4: protegidas OSF (borrador §4.2): nocturna, class 1, VRP>=1 MW, pixel mas caliente (LAT,LON) a <= inner_radius_km del crater
(vent_lat/vent_lon de volcanoes.yaml, que es lo que usa el pipeline; el borrador dice 'del crater de volcanoes.yaml').
P1: control positivo: sin filtro de distancia cuenta 334/37/173; con filtro debe bajar. P2: imprime denominadores."""
import pandas as pd, numpy as np, yaml, io, sys, unicodedata, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
P = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\data\mirova_reference\VRP_GLOBAL_ARCHIVE_2025.csv"
df = pd.read_csv(P, low_memory=False); df["t"]=pd.to_datetime(df["timeUTC"], format="%d/%m/%Y %H:%M")
ch = df[(df.Volc_LAT<-17)&(df.Volc_LAT>-56)&(df.Volc_LON<-65)&(df.Volc_LON>-76)]
w = ch[(ch.t>="2025-02-15")&(ch.t<"2026-01-01")&(ch.Dayflag==0)].copy()
vl = yaml.safe_load(open(r"D:\vrp-trabajo\temporales\ver_s172_prereg_retro\export_main\volcanoes.yaml",encoding="utf-8"))["volcanoes"]
def norm(s): return unicodedata.normalize("NFKD", s).encode("ascii","ignore").decode().lower().replace(" ","").replace("-","").replace(",","")
ym = {norm(v["name"]): v for v in vl if v.get("radius_km")==25}
alias = {"chillannevadosde":"nevadosdechillan"}
def hav(lat1,lon1,lat2,lon2):
    R=6371.0088; p1=np.radians(lat1);p2=np.radians(lat2);dl=np.radians(lon2-lon1);dp=p2-p1
    a=np.sin(dp/2)**2+np.cos(p1)*np.cos(p2)*np.sin(dl/2)**2
    return 2*R*np.arcsin(np.sqrt(a))
def key(n): k=norm(n); return alias.get(k,k)
w["yaml"]=w.Volc_Name.map(lambda n: ym.get(key(n)))
assert w.yaml.notna().all()
w["d_vent"]=[hav(r.LAT,r.LON,r.yaml.get("vent_lat",r.yaml["lat"]),r.yaml.get("vent_lon",r.yaml["lon"])) for r in w.itertuples()]
w["d_cumbre"]=[hav(r.LAT,r.LON,r.yaml["lat"],r.yaml["lon"]) for r in w.itertuples()]
w["d_osf"]=[hav(r.LAT,r.LON,r.Volc_LAT,r.Volc_LON) for r in w.itertuples()]
w["inner"]=[r.yaml["inner_radius_km"] for r in w.itertuples()]
w["maxd_km"]=w.Max_Dist/1000.0
pr = w[(w["class"]==1)&(w.VRP>=1e6)]
print("protegidas sin filtro de distancia:", pr.groupby("Resolution").size().to_dict())
for nom,col in (("pixel caliente a vent_yaml","d_vent"),("a lat/lon yaml","d_cumbre"),("a Volc_LAT/LON OSF","d_osf")):
    ok = pr[pr[col]<=pr.inner]
    print(nom, ok.groupby("Resolution").size().to_dict(), "Lascar:", ok[ok.Volc_Name=="Láscar"].groupby("Resolution").size().to_dict())
ok = pr[pr["maxd_km"]<=pr.inner]; print("Max_Dist<=inner", ok.groupby("Resolution").size().to_dict())
ok = pr[pr["d_vent"]<=pr.inner]
print("por volcan (vent):"); print(ok.groupby(["Resolution","Volc_Name"]).size().to_string())
print("fuera de inner 750 por volcan:", pr[(pr.Resolution==750)&(pr.d_vent>pr.inner)].groupby("Volc_Name").size().to_dict())
# VIIRS750 rango de VRP de las protegidas dentro del inner
print("750 dentro inner VRP MW:", sorted((ok[ok.Resolution==750].VRP/1e6).round(2).tolist())[:5], "...")
# bajo 1 MW 
b=w[(w["class"]==1)&(w.VRP<1e6)]
print("bajo 1 MW class1 por resolucion:", b.groupby("Resolution").size().to_dict())
print("class0 >=1MW por res:", w[(w["class"]==0)&(w.VRP>=1e6)].groupby("Resolution").size().to_dict())
# delta tiempo: minutos truncados
print("segundos en timeUTC: todos 00 (trunc a minuto)")
# ejemplos por noche: filas por (volc, res, dia) multiples
g=w.groupby(["Volc_Name","Resolution",w.t.dt.date]).size()
print("pares volcan-res-dia con >1 fila:", int((g>1).sum()), "de", len(g))
# protegidas por volcan y sin Lascar share
for r in (375,750,1000):
    s=ok[ok.Resolution==r]; print(r, "n", len(s), "Lascar share", round((s.Volc_Name=="Láscar").mean(),3))
w.to_pickle(r"D:\vrp-trabajo\temporales\ver_s172_prereg_retro\osf_w.pkl")
