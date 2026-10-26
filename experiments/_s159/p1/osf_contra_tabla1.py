# -*- coding: utf-8 -*-
"""P1 S159: ¿el OSF v2.5 cumple lo que Coppola et al. 2026 (Scientific Data) dice de él?

Pregunta del instrumento 1: si la Tabla 1 (umbrales de VRP por sensor y día/noche) o las
definiciones de LAT/LON y Max_Dist (Tabla 2) fueran falsas, ¿esto lo vería? Sí: cuenta filas
bajo el umbral y filas donde el píxel más caliente queda MÁS lejos que el "más lejano".
Pregunta 2: si el lector del CSV estuviera muerto (columnas mal leídas), los controles lo
delatan: (C+) la identidad VRP = (hot - bk) * k * A bajo 50° debe dar ~100 % en las tres
resoluciones; (C-) un umbral absurdo (1e15 W) debe dar 100 % de filas "bajo umbral".
Denominador: todas las filas del CSV (2000-2025, global, todas las clases), por resolución y Dayflag.
"""
import sys, io
import numpy as np, pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

CSV = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\data\mirova_reference\VRP_GLOBAL_ARCHIVE_2025.csv"
df = pd.read_csv(CSV)
print("filas:", len(df), " ventana:", df.timeUTC.min(), "->", df.timeUTC.max(), "(texto, sin ordenar)")

# Tabla 1 de Coppola 2026 SciData (PDF p. 8, renderizada): umbrales en W
UMB = {(1000, 0): 1.0e5, (750, 0): 5.0e6, (375, 0): 1.0e4,
       (1000, 1): 5.0e7, (750, 1): 5.0e7, (375, 1): 5.0e7}
K = {1000: 18.9 * 1.0e6, 750: 19.7 * 562500.0, 375: 18.0 * 140625.0}

print("\n== Umbrales de la Tabla 1 contra el VRP publicado ==")
for (res, day), u in sorted(UMB.items()):
    s = df[(df.Resolution == res) & (df.Dayflag == day)]
    if len(s) == 0:
        print(res, day, "SIN DATO"); continue
    bajo = (s.VRP < u).sum()
    print(f"res {res:4d} dayflag {day}: n={len(s):7d}  min VRP={s.VRP.min():.4g} W  "
          f"mediana={s.VRP.median():.4g}  bajo umbral {u:.1e}: {bajo} ({100*bajo/len(s):.2f} %)  "
          f"control(-) bajo 1e15: {100*(s.VRP<1e15).mean():.1f} %")

print("\n== Control (+): identidad del coeficiente bajo 50° de cenit ==")
for res, k in K.items():
    s = df[(df.Resolution == res) & (df.SatZen < 50)]
    pred = (s.Tot_Lmir_hot - s.Tot_Lmir_bk) * k
    ok = np.isclose(pred, s.VRP, rtol=1e-3, atol=1.0)
    print(f"res {res}: n={len(s)} cumple VRP=(hot-bk)*k*A: {100*ok.mean():.2f} %")

print("\n== Tabla 2: ¿el píxel más caliente queda dentro de Max_Dist (píxel más lejano)? ==")
R = 6371008.8
la1, lo1, la2, lo2 = map(np.radians, (df.LAT, df.LON, df.Volc_LAT, df.Volc_LON))
a = np.sin((la2 - la1) / 2) ** 2 + np.cos(la1) * np.cos(la2) * np.sin((lo2 - lo1) / 2) ** 2
dhot = 2 * R * np.arcsin(np.sqrt(a))
for res in (1000, 750, 375):
    m = df.Resolution == res
    exceso = dhot[m] - df.Max_Dist[m]
    tol = res / 2.0
    n_mal = (exceso > tol).sum()
    print(f"res {res}: n={m.sum()}  dist(hottest) > Max_Dist + {tol:.0f} m: {n_mal} "
          f"({100*n_mal/m.sum():.2f} %); mediana exceso {np.nanmedian(exceso):.0f} m")
    m1 = m & (df.Npix == 1)
    e1 = np.abs(dhot[m1] - df.Max_Dist[m1])
    print(f"   Npix=1 (n={m1.sum()}): |dist(hottest) - Max_Dist| mediana {np.nanmedian(e1):.0f} m, "
          f"p95 {np.nanpercentile(e1,95):.0f} m")
