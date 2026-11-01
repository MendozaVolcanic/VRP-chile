"""V2 / F2-H1: ¿Npix del OSF de MIROVA cuenta píxeles o cúmulos?

Pregunta 1 (si lo medido estuviera roto, ¿se vería?): si Npix contara cúmulos, el fondo MIR
por unidad de Npix (Tot_Lmir_bk / Npix) crecería con Npix, porque cada cúmulo trae varios
píxeles de fondo. Si cuenta píxeles, Tot_Lmir_bk / Npix es la radiancia de fondo de UN píxel,
plana en Npix. La medición distingue las dos.
Pregunta 2 (instrumento muerto): si la columna estuviera vacía o constante, el conteo por bin
saldría 0 o un solo bin; se imprime n por bin.
Control positivo: Npix = 1 es un píxel por definición bajo las dos lecturas; su fondo
por unidad fija la escala de un píxel (Planck a ~4 um y ~250-300 K da ~0,1 a 0,6).
Denominador: todas las filas del OSF v2.5 (VRP_GLOBAL_ARCHIVE_2025.csv), sin filtro de
fecha (2000-2025, ventana completa del archivo), separadas por Resolution.
"""
import sys, io
import numpy as np
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
OSF = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\data\mirova_reference\VRP_GLOBAL_ARCHIVE_2025.csv"
df = pd.read_csv(OSF, usecols=["Satellite", "Resolution", "Npix", "Tot_Lmir_hot", "Tot_Lmir_bk", "VRP", "timeUTC"])
print("filas totales:", len(df))
print("Resolution x Satellite:\n", df.groupby(["Resolution", "Satellite"]).size())
df = df[(df.Npix > 0) & df.Tot_Lmir_bk.notna()]
df["bk_por_npix"] = df.Tot_Lmir_bk / df.Npix
df["kA"] = df.VRP / (df.Tot_Lmir_hot - df.Tot_Lmir_bk)
bins = [0, 1, 2, 4, 10, 30, 100, 10**6]
for res, g in df.groupby("Resolution"):
    print(f"\n== Resolution {res} (n={len(g)}) ==")
    g = g.assign(b=pd.cut(g.Npix, bins))
    t = g.groupby("b", observed=True).agg(n=("Npix", "size"),
                                          bk_por_npix_med=("bk_por_npix", "median"),
                                          bk_por_npix_p10=("bk_por_npix", lambda s: s.quantile(.1)),
                                          bk_por_npix_p90=("bk_por_npix", lambda s: s.quantile(.9)),
                                          kA_med=("kA", "median"))
    print(t.to_string())
    print("Npix max:", g.Npix.max(), " percentil 99:", g.Npix.quantile(.99))
