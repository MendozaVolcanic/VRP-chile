# -*- coding: utf-8 -*-
"""V1 (S158) F6-2: que poblacion de VIIRS 750 trae el OSF v2.5 (VRP minimo por dia/noche, global y Chile).
Chile = Volc_LAT entre -56 y -17 y Volc_LON entre -76 y -66. Denominador: filas Resolution == 750."""
import sys, io, pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
df = pd.read_csv(r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\data\mirova_reference\VRP_GLOBAL_ARCHIVE_2025.csv")
d = df[df.Resolution == 750]
ch = d[d.Volc_LAT.between(-56, -17) & d.Volc_LON.between(-76, -66)]
for nm, x in [("global", d), ("Chile", ch)]:
    print(nm, "n", len(x), x.groupby("Dayflag").VRP.agg(["size", "min", "median"]).assign(min_MW=lambda t: t["min"] / 1e6).round(4).to_string())
    print("   filas < 5 MW:", int((x.VRP < 5e6).sum()))
print("Chile por volcan:", ch.groupby(["Volc_Name", "Dayflag"]).size().to_dict())
for res in (375, 1000):
    x = df[df.Resolution == res]
    print("res", res, "VRP min MW por Dayflag", (x.groupby("Dayflag").VRP.min() / 1e6).round(4).to_dict())
