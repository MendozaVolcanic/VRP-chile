# -*- coding: utf-8 -*-
"""P2 (S159), pregunta (c). Donde empieza exactamente el escalon del OSF v2.5 en VIIRS 750: en 50,0 grados de cenit
(un umbral escrito en codigo) o en ~52,6 (limite 2:1 -> 1:1 de la zona de agregacion, Geolocation ATBD 2014
p_idx 33: barrido 44,680 grados, convertido en zona_agregacion_cenit.py).
Pregunta 1: si el escalon estuviera en 52,6 y no en 50,0, los tramos finos de 0,25 grados entre 49 y 54 lo mostrarian.
Pregunta 2: si el instrumento estuviera muerto (columna mal leida), VIIRS 375 y MODIS (que cumplen el 100 %) no darian
1,0 en el mismo tramo; se imprimen como control negativo. Control positivo: el tramo 50-55 debe repetir el ~0,684 de
ra2/03 (8.753 filas). Ventana: todo el OSF v2.5 (2000-02 a 2025-12), global, tolerancia 1 %.
"""
import sys, io
import numpy as np, pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
OSF = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\data\mirova_reference\VRP_GLOBAL_ARCHIVE_2025.csv"
K = {"MODIS_1000": 1.89e7, "VIIRS_375": 18.0 * 140625, "VIIRS_750": 1.97e7 * 0.5625}
o = pd.read_csv(OSF, usecols=["timeUTC", "Satellite", "Resolution", "SatZen", "SatAzi", "Npix", "Tot_Lmir_hot", "Tot_Lmir_bk", "VRP", "Dayflag"])
o["sensor"] = o.Satellite.map({1: "MODIS", 2: "MODIS", 3: "VIIRS", 4: "VIIRS"}) + "_" + o.Resolution.astype(str)
o["ratio"] = o.VRP / ((o.Tot_Lmir_hot - o.Tot_Lmir_bk) * o.sensor.map(K))
o["cumple"] = (o.ratio - 1).abs() <= 1e-2
print("control positivo, V750 50<=z<55:", round(o[(o.sensor == "VIIRS_750") & (o.SatZen >= 50) & (o.SatZen < 55)].cumple.mean(), 6))
edges = list(np.round(np.arange(48.0, 54.01, 0.25), 2))
o["zb"] = pd.cut(o.SatZen, edges, right=False)
t = o[o.SatZen.between(48, 54)].groupby(["zb", "sensor"], observed=True).cumple.agg(["mean", "size"]).unstack(1)
print(t.round(4).to_string())
v = o[o.sensor == "VIIRS_750"]
print("\nV750: maximo cenit entre las que NO cumplen bajo 50:", v[(~v.cumple) & (v.SatZen < 50)].SatZen.max())
print("V750: minimo cenit entre las que NO cumplen:", v[~v.cumple].SatZen.min())
print("V750: n filas 50,00 <= z < 50,05 y fraccion que cumple:", int(((v.SatZen >= 50) & (v.SatZen < 50.05)).sum()),
      round(v[(v.SatZen >= 50) & (v.SatZen < 50.05)].cumple.mean(), 4))
v = v.copy(); v["anio"] = pd.to_datetime(v.timeUTC, format="%d/%m/%Y %H:%M").dt.year
s = v[v.SatZen >= 50]
print("\nV750 sobre 50: fraccion que cumple por anio (n)")
print(s.groupby("anio").cumple.agg(["mean", "size"]).round(4).to_string())
print("\nV750 sobre 50: por signo del azimut (lado del barrido aproximado) y dia/noche")
print(s.groupby([np.sign(s.SatAzi), "Dayflag"]).cumple.agg(["mean", "size"]).round(4).to_string())
print("\nV750 sobre 50: por Npix (1, 2-4, 5+)")
print(s.groupby(pd.cut(s.Npix, [0, 1, 4, 10**6])).cumple.agg(["mean", "size"]).round(4).to_string())
print("\nV750 que no cumplen: cuantiles de ratio y de ratio*cos(z)")
m = s[~s.cumple]
print(m.ratio.describe(percentiles=[.05, .25, .5, .75, .95]).round(4).to_string())
