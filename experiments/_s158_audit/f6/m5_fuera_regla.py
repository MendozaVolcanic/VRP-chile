# -*- coding: utf-8 -*-
"""F6 M5: ¿que regla separa las filas fuera de las sanas dentro de cenit > 50? Barrido de Max_Dist, Npix y k*dL.
Denominador: 34.250 filas V750 con SatZen > 50 (OSF v2.5, 2012-2025). Control: con cenit <= 50 ninguna fila
esta fuera (M3), asi que cualquier regla que encuentre aca es exclusiva del cenit alto."""
import sys, io
import numpy as np, pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
d = pd.read_pickle(sys.argv[1])
K = 1.97e7 * 0.5625
d["kdl"] = K * (d.Tot_Lmir_hot - d.Tot_Lmir_bk)
d["r"] = d.VRP / d.kdl
d["fuera"] = (d.r - 1).abs() >= 1e-4
z = d[d.SatZen > 50].copy()
z["mdb"] = pd.cut(z.Max_Dist, [-1,0,750,1500,2500,4000,6000,10000,15000,20000,31000])
print(z.groupby("mdb", observed=True).fuera.agg(["sum","count","mean"]).to_string())
print("\nfuera: Max_Dist min", z[z.fuera].Max_Dist.min(), " Npix min", z[z.fuera].Npix.min(), " kdl min MW", (z[z.fuera].kdl.min()/1e6).round(2))
lo = z[z.fuera].nsmallest(8, "kdl")[["timeUTC","Volc_Name","SatZen","Npix","Tot_Lmir_hot","Tot_Lmir_bk","VRP","r","Max_Dist"]]
print(lo.to_string())
# VRP publicado frente a k*Lhot_max aproximado: si el pub fuera el pixel mas caliente, VRP_pub <= k*Lhot/1; ver r*Npix
print("\nVRP_pub/(k*dL/Npix) (cuantos 'pixeles medios' publica): mediana",
      (z[z.fuera].VRP/(z[z.fuera].kdl/z[z.fuera].Npix)).median().round(2))
# ¿el VRP publicado en fuera se parece al de cenit bajo del mismo volcan y mes? (normalizacion)
