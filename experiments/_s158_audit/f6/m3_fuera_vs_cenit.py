# -*- coding: utf-8 -*-
"""F6 M3: las filas fuera de la identidad, contra el cenit del satelite y contra combinaciones.
Denominador: 100.641 filas V750 del OSF v2.5 (2012-01-19 a 2025-12-31)."""
import sys, io
import numpy as np, pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
d = pd.read_pickle(sys.argv[1])
K = 1.97e7 * 0.5625
d["dL"] = d.Tot_Lmir_hot - d.Tot_Lmir_bk
d["r"] = d.VRP / (K * d.dL)
d["fuera"] = (d.r - 1).abs() >= 1e-4
d["zb"] = pd.cut(d.SatZen, [0,10,20,30,40,45,50,55,60,65,70,75])
print(d.groupby("zb", observed=True).fuera.agg(["sum","count","mean"]).to_string())
print("\nmediana de r en fuera por cenit:")
print(d[d.fuera].groupby("zb", observed=True).r.describe().to_string())
print("\nSatZen min en filas fuera:", d[d.fuera].SatZen.min())
print("\nfuera con SatZen<40, muestra:")
print(d[d.fuera & (d.SatZen<40)][["timeUTC","Volc_Name","Dayflag","SatZen","Npix","Tot_Lmir_hot","Tot_Lmir_bk","VRP","r"]].head(20).to_string())
# a igual cenit, ¿que separa dentro de fuera?
z = d[d.SatZen > 50]
print("\nSatZen>50: n", len(z), "fuera", z.fuera.sum())
z["kb"] = pd.cut(K*z.dL/1e6, [0,20,50,100,200,500,1e5])
print(z.groupby("kb", observed=True).fuera.agg(["sum","count","mean"]).to_string())
z["npb"] = pd.cut(z.Npix, [0,4,10,30,50,1000])
print(z.groupby("npb", observed=True).fuera.agg(["sum","count","mean"]).to_string())
