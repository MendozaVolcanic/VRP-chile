# -*- coding: utf-8 -*-
"""P2 (S159), complemento de escalon_fino.py. El Npix de las filas V750 del OSF salta en 50 grados? (sobre 50 casi
todas las filas tienen Npix >= 5). Compara Npix bajo y sobre 50 en V750, con V375 y MODIS como control (si el salto
fuera del archivo y no de V750, apareceria en los tres). Pregunta 2: el conteo por tramo se imprime con su n.
Ventana: todo el OSF v2.5, global; noche y dia por separado."""
import sys, io
import numpy as np, pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
OSF = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\data\mirova_reference\VRP_GLOBAL_ARCHIVE_2025.csv"
K = {"MODIS_1000": 1.89e7, "VIIRS_375": 18.0 * 140625, "VIIRS_750": 1.97e7 * 0.5625}
o = pd.read_csv(OSF, usecols=["Satellite", "Resolution", "SatZen", "Npix", "Tot_Lmir_hot", "Tot_Lmir_bk", "VRP", "Dayflag"])
o["sensor"] = o.Satellite.map({1: "MODIS", 2: "MODIS", 3: "VIIRS", 4: "VIIRS"}) + "_" + o.Resolution.astype(str)
o["ratio"] = o.VRP / ((o.Tot_Lmir_hot - o.Tot_Lmir_bk) * o.sensor.map(K))
o["zb"] = pd.cut(o.SatZen, [0, 40, 45, 48, 50, 52, 55, 60, 70], right=False)
for d in (0, 1):
    print(f"\n=== Dayflag={d}: mediana de Npix por sensor y tramo de cenit (n) ===")
    t = o[o.Dayflag == d].groupby(["zb", "sensor"], observed=True).Npix.agg(["median", "size"]).unstack(1)
    print(t.to_string())
v = o[(o.sensor == "VIIRS_750") & (o.SatZen >= 50)].copy()
v["npb"] = pd.cut(v.Npix, [0, 1, 4, 10, 30, 100, 10**6])
print("\nV750 sobre 50: ratio VRP/(dL k) por tramo de Npix (mediana, p5, p95, n)")
print(v.groupby("npb", observed=True).ratio.describe(percentiles=[.05, .5, .95])[["count", "5%", "50%", "95%"]].round(4).to_string())
