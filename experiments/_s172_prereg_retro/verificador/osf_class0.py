# VPR172-12: filas OSF de >=1 MW por class y distancia al cráter (inner_radius_km). P1: control positivo: suma por class debe dar 334+105 (375), 37+8 (750), 174+9 (1000) = osf_protegidas_salida.txt.
import pandas as pd, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
w=pd.read_pickle(r"D:\vrp-trabajo\temporales\ver_s172_prereg_retro\osf_w.pkl")
a=w[(w.VRP>=1e6)]
print("VRP>=1MW noche, por resolucion y class:", a.groupby(["Resolution","class"]).size().to_dict())
b=a[a.d_vent<=a.inner]
print("dentro de inner (pixel caliente):", b.groupby(["Resolution","class"]).size().to_dict())
print("class0 dentro de inner por volcan:", b[b["class"]==0].groupby(["Resolution","Volc_Name"]).size().to_dict())
print("class1 fuera de inner por res/volcan:", a[(a["class"]==1)&(a.d_vent>a.inner)].groupby(["Resolution","Volc_Name"]).size().to_dict())
x=a[(a["class"]==1)&(a.d_vent>a.inner)&(a.Volc_Name.str.contains("Chill"))]
print("Chillan class1 fuera inner: n",len(x),"dist km min/mediana/max", round(x.d_vent.min(),1), round(x.d_vent.median(),1), round(x.d_vent.max(),1), "fechas", x.t.dt.date.min(), x.t.dt.date.max(), "VRP MW mediana", round((x.VRP/1e6).median(),1))
