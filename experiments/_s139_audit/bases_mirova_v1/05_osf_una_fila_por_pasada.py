"""05: que publica MIROVA por pasada y volcan, segun su propia base OSF v2.5
(VRP_GLOBAL_ARCHIVE_2025.csv, esquema en MIROVA_Database_Schema_v2.5.docx):
una fila por pasada, VRP integrado sobre TODOS los pixeles alertados, LAT/LON del
pixel MAS CALIENTE, Max_Dist al pixel alertado MAS LEJANO.

Pregunta: la 'Distance km' de latest.php se parece a Max_Dist (pixel mas lejano)
o a la distancia del pixel mas caliente? Se compara, para los volcanes chilenos,
la distribucion de Max_Dist (OSF 2025) contra la de Distancia_km (latest.php
2026) y contra la distancia calculada del pixel mas caliente (LAT/LON vs
Volc_LAT/LON). No se puede cruzar pasada a pasada (anos distintos): es una
comparacion de distribuciones, o sea SOSPECHA, no confirmacion.
"""
import math
import os
import sys

import pandas as pd

from comun import REPO, dir_remoto, encabezado, leer

D = dir_remoto(sys.argv)
OSF = os.path.join(REPO, "data", "mirova_reference", "VRP_GLOBAL_ARCHIVE_2025.csv")
encabezado(
    "OSF v2.5: UNA FILA POR PASADA; QUE DISTANCIA PUBLICA MIROVA",
    "si MIROVA publicara varias filas por pasada, habria duplicados (timeUTC, IDvolc, Satellite, Resolution)",
    "un archivo vacio daria 0 filas; se imprime n en cada tabla",
    "la distancia del pixel mas caliente calculada debe ser <= Max_Dist en toda fila (si no, el calculo esta mal)",
)
ids = {355030: "Isluga", 355100: "Lascar", 355120: "Lastarria", 357010: "Tupungatito", 357040: "PlanchonPeteroa",
       357070: "Nevados de Chillan", 357090: "Copahue", 357110: "Llaima", 357120: "Villarrica",
       357150: "Puyehue-Cordon Caulle", 358041: "Chaiten"}
osf = pd.read_csv(OSF, usecols=["timeUTC", "IDvolc", "Dayflag", "Satellite", "Resolution", "Npix", "VRP", "LAT", "LON",
                                "Max_Dist", "Volc_Name", "Volc_LAT", "Volc_LON", "class"])
o = osf[osf["IDvolc"].isin(ids)].copy()
print("filas OSF Chile Tier A:", len(o), "| duplicados (timeUTC, IDvolc, Satellite, Resolution):",
      int(o.duplicated(["timeUTC", "IDvolc", "Satellite", "Resolution"]).sum()))
print("Npix: distribucion", o["Npix"].describe().round(2).to_dict())
print("filas con Npix > 1:", int((o["Npix"] > 1).sum()), "/", len(o))


def hav(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1; dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


o["d_hot_km"] = [hav(a, b, c, d) for a, b, c, d in zip(o["LAT"], o["LON"], o["Volc_LAT"], o["Volc_LON"])]
o["maxd_km"] = o["Max_Dist"] / 1000.0
print("CONTROL: filas con d_hot_km > Max_Dist + 0.5 km (deberian ser ~0):", int((o["d_hot_km"] > o["maxd_km"] + 0.5).sum()))
print("filas Npix>1 con Max_Dist - d_hot > 0.5 km (el pixel mas lejano NO es el mas caliente):",
      int(((o["Npix"] > 1) & (o["maxd_km"] - o["d_hot_km"] > 0.5)).sum()), "/", int((o["Npix"] > 1).sum()))

cons = leer(f"{D}/registro_vrp_consolidado.csv")
det = cons[cons["VRP_MW"] > 0]
print("\n--- por volcan: fraccion de distancias == 0 y mediana, OSF (Max_Dist, d_hot) 2025 vs latest.php 2026")
print(f"{'volcan':22s} {'n_osf':>6s} {'MaxD=0%':>8s} {'dhot=0%':>8s} {'MaxD_med':>9s} {'dhot_med':>9s} | {'n_php':>6s} {'php=0%':>7s} {'php_med':>8s} {'Npix>1%':>8s}")
for i, v in ids.items():
    g = o[o["IDvolc"] == i]; p = det[det["Volcan"] == v]
    if len(g) == 0:
        continue
    print(f"{v:22s} {len(g):6d} {100*(g['maxd_km']==0).mean():8.1f} {100*(g['d_hot_km']<0.3).mean():8.1f} "
          f"{g['maxd_km'].median():9.2f} {g['d_hot_km'].median():9.2f} | {len(p):6d} "
          f"{100*(p['Distancia_km']==0).mean() if len(p) else float('nan'):7.1f} "
          f"{p['Distancia_km'].median() if len(p) else float('nan'):8.2f} {100*(g['Npix']>1).mean():8.1f}")
print("\nNota: d_hot < 0.3 km se usa como '0' porque LAT/LON son continuos y Volc_LAT/LON tienen 3 decimales.")
print("MODIS 2025 (Resolution 1000) Max_Dist en km redondeado, top 10 valores:",
      o[o["Resolution"] == 1000]["maxd_km"].round(2).value_counts().head(10).to_dict())
