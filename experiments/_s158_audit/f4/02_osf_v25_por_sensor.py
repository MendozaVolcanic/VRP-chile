# -*- coding: utf-8 -*-
"""F4 S158: qué dice el OSF v2.5 por sensor (producto FILTRADO, A105: sólo sirve para lo que sobrevive al filtro).
Pregunta 1 del instrumento: si el coeficiente o el filtro de Coppola 2026 Tabla 1 estuvieran mal, el VRP/ΔL por sensor
y el mínimo de VRP por sensor y dayflag lo mostrarían. Pregunta 2: si el CSV estuviera vacío o mal parseado, n=0.
Control positivo: el coeficiente de MODIS (18.9e6) difiere del de VIIRS 750 (1.97e7*0.5625=1.108e7): si el cálculo
no distinguiera sensores, los tres darían lo mismo."""
import sys, io, pandas as pd, numpy as np
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
F = r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv"
df = pd.read_csv(F, usecols=["timeUTC","Dayflag","Satellite","Resolution","SatZen","Npix","Tot_Lmir_hot","Tot_Lmir_bk","VRP","Volc_Name","class"])
df["t"] = pd.to_datetime(df["timeUTC"], format="%d/%m/%Y %H:%M", errors="coerce")
print("filas", len(df), "ventana", df.t.min(), "a", df.t.max())
df["dL"] = df.Tot_Lmir_hot - df.Tot_Lmir_bk
df["coef"] = df.VRP / df.dL
for (res, day), g in df.groupby(["Resolution","Dayflag"]):
    c = g.coef.replace([np.inf,-np.inf],np.nan).dropna()
    print(f"res={res} day={day} n={len(g)} coef mediana={c.median():.1f} p1={c.quantile(.01):.1f} p99={c.quantile(.99):.1f} "
          f"VRP min={g.VRP.min():.1f} p1={g.VRP.quantile(.01):.1f} p5={g.VRP.quantile(.05):.1f} mediana={g.VRP.median():.1f} "
          f"Npix mediana={g.Npix.median()} Npix1 frac={(g.Npix==1).mean():.3f} dL<=0 n={(g.dL<=0).sum()}")
# ΔL por pixel para Npix=1: el exceso mínimo que sobrevive al filtro, por sensor
print("\nΔL por píxel con Npix=1 (noche):")
for res, g in df[(df.Npix==1)&(df.Dayflag==0)].groupby("Resolution"):
    print(f"res={res} n={len(g)} dL min={g.dL.min():.5f} p1={g.dL.quantile(.01):.5f} p5={g.dL.quantile(.05):.5f} mediana={g.dL.median():.5f}")
print("\nChile (nombres con Villarrica/Lascar/Láscar/Copahue/Llaima/Nevados):")
ch = df[df.Volc_Name.str.contains("Villarrica|Lascar|Láscar|Copahue|Llaima|Nevados de Chillan|Planchon|Caulle|Isluga|Lastarria|Tupungatito|Chait", case=False, na=False)]
print(ch.groupby(["Volc_Name","Resolution"]).size().to_string())
