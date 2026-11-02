# -*- coding: utf-8 -*-
"""VPR172 V-4: Dayflag del OSF vs elevacion solar con la regla del proyecto (es_pasada_diurna_descartada). 
P1: control positivo: filas Dayflag=1 deben salir diurnas bajo la regla. P2: imprime n."""
import sys, os, io, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
EXP = r"D:\vrp-trabajo\temporales\ver_s172_prereg_retro\export_main"
sys.path.insert(0, EXP); sys.path.insert(0, EXP + r"\scripts"); os.chdir(EXP)
import pandas as pd
from auto_audit_weekly import es_pasada_diurna_descartada
from datetime import timezone
P = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\data\mirova_reference\VRP_GLOBAL_ARCHIVE_2025.csv"
df = pd.read_csv(P, low_memory=False); df["t"]=pd.to_datetime(df["timeUTC"], format="%d/%m/%Y %H:%M")
ch = df[(df.Volc_LAT<-17)&(df.Volc_LAT>-56)&(df.Volc_LON<-65)&(df.Volc_LON>-76)]
w = ch[(ch.t>="2025-02-15")&(ch.t<"2026-01-01")].copy()
print("n ventana", len(w))
print("Dayflag0 por hora UTC:", w[w.Dayflag==0].t.dt.hour.value_counts().sort_index().to_dict())
print("Dayflag1 por hora UTC:", w[w.Dayflag==1].t.dt.hour.value_counts().sort_index().to_dict())
def bucket(r): return {375:"VIIRS375",750:"VIIRS750",1000:"MODIS"}[r]
res=[]
for _,r in w.iterrows():
    dt = r.t.to_pydatetime().replace(tzinfo=timezone.utc)
    res.append(es_pasada_diurna_descartada(bucket(r.Resolution), r.Volc_LAT, r.Volc_LON, dt))
w["diurna"]=res
print(pd.crosstab(w.Dayflag, w.diurna))
print("Dayflag0 pero diurna por regla, por resolucion y volcan:"); 
x=w[(w.Dayflag==0)&(w.diurna)]; print(x.groupby(["Resolution","Volc_Name"]).size().to_dict())
print("VRP>=1MW class1 entre esas:", ((x.VRP>=1e6)&(x["class"]==1)).sum())
print("Dayflag1 y no diurna:", len(w[(w.Dayflag==1)&(~w.diurna)]))
# nocturnas por regla, protegidas class1 VRP>=1e6 por resolucion
nn = w[~w.diurna]
print("nocturnas por regla:", len(nn))
print(nn[(nn.VRP>=1e6)&(nn["class"]==1)].groupby("Resolution").size().to_dict())
print("clase 0 >=1MW noct:", nn[(nn.VRP>=1e6)&(nn["class"]==0)].groupby("Resolution").size().to_dict())
x.to_csv(r"D:\vrp-trabajo\temporales\ver_s172_prereg_retro\osf_dayflag0_diurnas.csv", index=False)
