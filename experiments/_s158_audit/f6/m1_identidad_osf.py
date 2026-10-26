# -*- coding: utf-8 -*-
"""F6 M1: el OSF v2.5 contra la parte VRP del codigo publicado (MIROVA_VIIRS750_VRP.m).

Pregunta 1 (si lo medido estuviera roto, ¿se veria?): la identidad VRP = 1,97e7 * 0,5625 * (Lhot - Lbk) es una
igualdad por fila; un coeficiente o un area distinta la rompe en todas las filas. Control positivo: la misma prueba
sobre las filas de 375 m y de 1000 m tiene que FALLAR con el coeficiente de 750 (otros k).
Pregunta 2 (instrumento muerto): si el CSV no se leyera, n = 0 y se imprime SIN DATO.
Denominador: todas las filas del archivo con Resolution == 750 (ventana: la del archivo, se imprime).
"""
import sys, io
import numpy as np, pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RUTA = sys.argv[1]
df = pd.read_csv(RUTA)
df["t"] = pd.to_datetime(df["timeUTC"], format="%d/%m/%Y %H:%M")
print("filas totales", len(df))
print(df.groupby(["Resolution", "Satellite"]).size())
K750 = 1.97e7 * 0.5625
for res, kesp in [(750, K750), (375, 18.0 * 0.140625 * 1e6), (1000, 18.9e6)]:
    d = df[df.Resolution == res].copy()
    if len(d) == 0:
        print(res, "SIN DATO"); continue
    dl = d.Tot_Lmir_hot - d.Tot_Lmir_bk
    coef = d.VRP / dl
    rel750 = (d.VRP - K750 * dl) / d.VRP
    relk = (d.VRP - kesp * dl) / d.VRP
    print(f"\n== Resolution {res}: n={len(d)}  ventana {d.t.min()} a {d.t.max()}")
    print(f"  coef VRP/dL: mediana {coef.median():.6g}  p0.1 {coef.quantile(0.001):.6g}  p99.9 {coef.quantile(0.999):.6g}")
    print(f"  |rel| contra k750 <1e-6: {(rel750.abs()<1e-6).sum()} de {len(d)}")
    print(f"  |rel| contra k propio ({kesp:.6g}) <1e-6: {(relk.abs()<1e-6).sum()};  <1e-4: {(relk.abs()<1e-4).sum()}")
    print(f"  dL<=0: {(dl<=0).sum()}  VRP<=0: {(d.VRP<=0).sum()}  VRP NaN: {d.VRP.isna().sum()}  Npix NaN: {d.Npix.isna().sum()}")
    print(f"  VRP min {d.VRP.min():.6g} W; dL min {dl.min():.6g}")
    out = d[relk.abs() >= 1e-4]
    if len(out):
        print("  filas fuera de la identidad (primeras 10):")
        print(out[["id","timeUTC","Volc_Name","Satellite","Npix","Tot_Lmir_hot","Tot_Lmir_bk","VRP"]].head(10).to_string())
d = df[df.Resolution == 750].copy()
print("\n== V750 Npix")
print(d.Npix.describe())
for c in [1,2,3,4,5,10,30,31,50,100,200,500]:
    print(f"  Npix > {c}: {(d.Npix>c).sum()}")
print("  Npix no entero:", (d.Npix != d.Npix.round()).sum())
print("\n== V750 Max_Dist (m)")
print(d.Max_Dist.describe())
for c in [5000, 10000, 20000, 24000, 25000, 34000, 36000, 50000]:
    print(f"  Max_Dist > {c}: {(d.Max_Dist>c).sum()}")
print("  Npix==1 y Max_Dist==0:", ((d.Npix==1)&(d.Max_Dist==0)).sum(), " Npix==1:", (d.Npix==1).sum())
print("\n== V750 Dayflag / class")
print(d.groupby(["Dayflag","class"]).size())
print("\n== V750 Lhot/Npix y Lbk/Npix (W m-2 sr-1 um-1 por pixel)")
print((d.Tot_Lmir_hot/d.Npix).describe()); print((d.Tot_Lmir_bk/d.Npix).describe())
d.to_pickle(sys.argv[2])
