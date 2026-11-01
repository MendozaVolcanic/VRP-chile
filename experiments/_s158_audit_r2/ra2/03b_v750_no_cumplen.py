# -*- coding: utf-8 -*-
"""RA2 (S158 r2), afirmacion 3, segunda parte: que explica las filas VIIRS 750 del OSF v2.5 que no cumplen
VRP = (hot - bk) x 11.081.250. Se buscan patrones en Npix, ano, satelite, Dayflag, latitud, clase, y se prueba si
el VRP de esas filas corresponde a un subconjunto de pixeles (Npix x ratio) o a un factor sobre el fondo.
Pregunta 1: si el defecto fuera un factor del angulo, ratio/sec^n seria constante (03 ya mostro que no).
Pregunta 2: el control es la poblacion que SI cumple (ratio = 1 exacto); todo contraste se hace contra ella.
Ventana: todo el OSF; VIIRS 750 unicamente.
"""
from __future__ import annotations
import sys, io
import numpy as np, pandas as pd
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
OSF = Path(r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\data\mirova_reference\VRP_GLOBAL_ARCHIVE_2025.csv")
K = 1.97e7 * 0.5625
osf = pd.read_csv(OSF, encoding="utf-8")
osf["t"] = pd.to_datetime(osf.timeUTC, format="%d/%m/%Y %H:%M")
v = osf[osf.Resolution == 750].copy()
v["dL"] = v.Tot_Lmir_hot - v.Tot_Lmir_bk
v["ratio"] = v.VRP / (v.dL * K)
v["cumple"] = (v.ratio - 1).abs() <= 1e-3
v["anio"] = v.t.dt.year
print("VIIRS 750 filas:", len(v), "cumplen:", int(v.cumple.sum()), "no cumplen:", int((~v.cumple).sum()))
print("\nfraccion que NO cumple por ano:")
print(v.groupby("anio").cumple.agg(lambda s: 1 - s.mean()).round(4).to_string())
print("\nfraccion que NO cumple por satelite (3 = SNPP, 4 = NOAA20 segun el pareo 01):")
print(v.groupby("Satellite").cumple.agg(lambda s: 1 - s.mean()).round(4).to_dict())
print("por Dayflag:", v.groupby("Dayflag").cumple.agg(lambda s: 1 - s.mean()).round(4).to_dict())
print("por class:", v.groupby("class").cumple.agg(lambda s: 1 - s.mean()).round(4).to_dict())
print("\nfraccion que NO cumple por tramo de cenit FINO (sobre 45):")
v["zb"] = pd.cut(v.SatZen, [0, 45, 48, 49, 50, 51, 52, 53, 55, 58, 60, 63, 66, 70, 90], right=False)
print(v.groupby("zb", observed=True).cumple.agg([lambda s: round(1 - s.mean(), 4), "size"]).to_string())
print("\ncenit minimo de una fila que no cumple:", round(v[~v.cumple].SatZen.min(), 3),
      "| cenit maximo de una que cumple:", round(v[v.cumple].SatZen.max(), 3))
print("\nfraccion que NO cumple por Npix (sobre 50 grados):")
a = v[v.SatZen >= 50]
print(a.groupby(pd.cut(a.Npix, [0, 1, 2, 3, 5, 10, 30, 1e9]), observed=True).cumple.agg([lambda s: round(1 - s.mean(), 4), "size"]).to_string())
print("\nfraccion que NO cumple por latitud del volcan (sobre 50 grados):")
print(a.groupby(pd.cut(a.Volc_LAT, [-90, -40, -20, 0, 20, 40, 60, 90]), observed=True).cumple.agg([lambda s: round(1 - s.mean(), 4), "size"]).to_string())

m = v[~v.cumple].copy()
# Hipotesis A: VRP = k x suma sobre un subconjunto de pixeles. Entonces ratio x Npix = "pixeles efectivos", no
# necesariamente entero. Hipotesis B: VRP = k x (hot - c x bk): c = (hot - VRP/k)/bk.
m["npix_ef"] = m.ratio * m.Npix
m["c_bk"] = (m.Tot_Lmir_hot - m.VRP / K) / m.Tot_Lmir_bk
print("\nNO cumplen: Npix x ratio (pixeles efectivos) describe:")
print(m.npix_ef.describe(percentiles=[.05, .25, .5, .75, .95]).round(3).to_string())
print("fraccion con Npix x ratio a menos de 0,02 de un entero:", round(((m.npix_ef - m.npix_ef.round()).abs() < 0.02).mean(), 4),
      "| control (que esperaria el azar con dispersion uniforme): 0.04")
print("hipotesis B, c = (hot - VRP/k)/bk:")
print(m.c_bk.describe(percentiles=[.05, .25, .5, .75, .95]).round(3).to_string())
# Hipotesis C: VRP = k' x dL con k' = k x cos(z)^n o k x area del pixel oblicuo (bow tie): ratio vs cenit
print("\nSpearman ratio vs SatZen (no cumplen):", round(m[["ratio", "SatZen"]].corr(method="spearman").iloc[0, 1], 4))
print("Spearman ratio vs Npix:", round(m[["ratio", "Npix"]].corr(method="spearman").iloc[0, 1], 4))
print("Spearman ratio vs Tot_Lmir_bk/Npix (fondo medio):",
      round(m.assign(bkm=m.Tot_Lmir_bk / m.Npix)[["ratio", "bkm"]].corr(method="spearman").iloc[0, 1], 4))
print("Spearman ratio vs Tot_Lmir_hot/Npix:",
      round(m.assign(hm=m.Tot_Lmir_hot / m.Npix)[["ratio", "hm"]].corr(method="spearman").iloc[0, 1], 4))
# Npix = 1 que no cumplen: ahi no hay subconjunto posible
m1 = m[m.Npix == 1]
print("\nNO cumplen con Npix = 1:", len(m1), "de", int((a.Npix == 1).sum()), "filas Npix=1 sobre 50 grados")
if len(m1):
    print(m1[["timeUTC", "Volc_Name", "SatZen", "Tot_Lmir_hot", "Tot_Lmir_bk", "VRP", "ratio", "c_bk"]].head(12).to_string())
    print("ratio en Npix=1:", m1.ratio.describe(percentiles=[.05, .5, .95]).round(4).to_dict())
# Hipotesis D: VRP calculado con el fondo de otra manera: VRP/k + bk_osf = hot' (hot implicito). hot'/hot:
m["hot_impl"] = m.VRP / K + m.Tot_Lmir_bk
print("\nhot implicito (VRP/k + bk) / Tot_Lmir_hot:", m.assign(r=m.hot_impl / m.Tot_Lmir_hot).r.describe(percentiles=[.05, .5, .95]).round(4).to_dict())
m["bk_impl"] = m.Tot_Lmir_hot - m.VRP / K
print("bk implicito (hot - VRP/k) / Tot_Lmir_bk:", m.assign(r=m.bk_impl / m.Tot_Lmir_bk).r.describe(percentiles=[.05, .5, .95]).round(4).to_dict())
# Volcanes chilenos
chi = m[m.Volc_LON.between(-76, -66) & (m.Volc_LAT < -17)]
print("\nfilas chilenas VIIRS 750 que no cumplen:", len(chi), "de",
      int((v.Volc_LON.between(-76, -66) & (v.Volc_LAT < -17) & (v.SatZen >= 50)).sum()), "sobre 50 grados")
print(chi.groupby("Volc_Name").size().to_dict())
print(chi[["timeUTC", "Volc_Name", "SatZen", "Npix", "Tot_Lmir_hot", "Tot_Lmir_bk", "VRP", "ratio"]].head(10).to_string())
