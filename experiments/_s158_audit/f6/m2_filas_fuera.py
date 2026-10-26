# -*- coding: utf-8 -*-
"""F6 M2: caracterizar las filas V750 del OSF v2.5 que NO cumplen VRP = 1,97e7*0,5625*(Lhot-Lbk).
Instrumento: r = VRP / (k750 * dL). En las 92.402 filas sanas r = 1 a 1e-6 (M1), asi que r != 1 no es redondeo.
Denominador: 100.641 filas V750 (2012-01-19 a 2025-12-31)."""
import sys, io
import numpy as np, pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
d = pd.read_pickle(sys.argv[1])
K = 1.97e7 * 0.5625
d["dL"] = d.Tot_Lmir_hot - d.Tot_Lmir_bk
d["r"] = d.VRP / (K * d.dL)
d["fuera"] = (d.r - 1).abs() >= 1e-4
d["year"] = d.t.dt.year
d["Lpp"] = d.Tot_Lmir_hot / d.Npix
f = d[d.fuera]
print("fuera:", len(f), "de", len(d), f"({100*len(f)/len(d):.2f} %)")
print("r en las fuera:"); print(f.r.describe())
print("r > 1 en fuera:", (f.r > 1).sum())
print("\nfraccion fuera por anio y satelite:")
print(d.groupby(["year"]).fuera.agg(["sum","count","mean"]).to_string())
print(d.groupby(["Satellite"]).fuera.agg(["sum","count","mean"]).to_string())
print(d.groupby(["Dayflag"]).fuera.agg(["sum","count","mean"]).to_string())
print("\nfraccion fuera por clase de Npix:")
d["npb"] = pd.cut(d.Npix, [0,1,2,4,10,30,50,100,1000])
print(d.groupby("npb", observed=True).fuera.agg(["sum","count","mean"]).to_string())
print("\nfraccion fuera por Lhot/Npix:")
d["lb"] = pd.cut(d.Lpp, [0,0.5,1,2,3,5,10,20,100])
print(d.groupby("lb", observed=True).fuera.agg(["sum","count","mean"]).to_string())
print("\nfraccion fuera por VRP (MW):")
d["vb"] = pd.cut(d.VRP/1e6, [0,10,20,50,100,200,500,1e5])
print(d.groupby("vb", observed=True).fuera.agg(["sum","count","mean"]).to_string())
print("\nfraccion fuera por k*dL (MW, VRP que daria el codigo):")
d["kb"] = pd.cut(K*d.dL/1e6, [0,10,20,50,100,200,500,1e5])
print(d.groupby("kb", observed=True).fuera.agg(["sum","count","mean"]).to_string())
print("\nvolcanes con mas filas fuera:")
g = d.groupby("Volc_Name").fuera.agg(["sum","count","mean"]).sort_values("sum", ascending=False)
print(g.head(15).to_string())
# r frente a cocientes simples: VRP/(k*Lhot)? VRP/(k*(Lhot - Lbk)*npix_sub/npix)?
f = d[d.fuera].copy()
f["r_hot"] = f.VRP / (K * f.Tot_Lmir_hot)
print("\nVRP/(k*Lhot) en fuera:"); print(f.r_hot.describe())
print("r*Npix (si VRP saliera de un subconjunto de pixeles, r*Npix ~ entero):")
x = f.r * f.Npix
print((x - x.round()).abs().describe())
print("muestra:"); print(f[["timeUTC","Volc_Name","Satellite","Dayflag","SatZen","Npix","Tot_Lmir_hot","Tot_Lmir_bk","VRP","r","Max_Dist","class"]].sample(15, random_state=1).to_string())
d[["id","fuera","r"]].to_pickle(sys.argv[2])
