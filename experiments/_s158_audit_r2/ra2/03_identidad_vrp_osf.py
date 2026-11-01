# -*- coding: utf-8 -*-
"""RA2 (S158 r2), afirmacion 3. Identidad VRP = (Tot_Lmir_hot - Tot_Lmir_bk) x k_sensor en el OSF v2.5, por sensor
y por tramo de cenit. La constante k se DEDUCE del dato (mediana de VRP/dL por sensor), no se supone.

Pregunta 1: si el OSF no cumpliera la identidad en una parte de las filas, la fraccion fuera de tolerancia lo
mostraria por tramo. Pregunta 2: si el instrumento estuviera muerto (columna mal leida), la mediana de k no daria
una constante reconocible y la dispersion seria enorme. Control positivo: una fila sintetica con VRP x 1,10 cae
fuera de la tolerancia de 1 % (se imprime).
Tolerancia declarada: |VRP/(dL x k) - 1| <= 1e-3 (redondeo a 9 cifras del CSV) y, por separado, 1 %.
Ventana: todo el OSF (2000-02 a 2025-12), global, y aparte 2025.
"""
from __future__ import annotations
import sys, io
import numpy as np, pandas as pd
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
OSF = Path(r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\data\mirova_reference\VRP_GLOBAL_ARCHIVE_2025.csv")
K_CODIGO_750 = 1.97e7 * 0.5625  # W por (W m-2 sr-1 um-1): MIROVA_VIIRS750_VRP.m l. 88-91 (VRP_MW = dL*1.97e7*0.5625/1e6)

osf = pd.read_csv(OSF, encoding="utf-8")
osf["t"] = pd.to_datetime(osf.timeUTC, format="%d/%m/%Y %H:%M")
osf["sensor"] = osf.Satellite.map({1: "MODIS", 2: "MODIS", 3: "VIIRS", 4: "VIIRS"}) + "_" + osf.Resolution.astype(str)
osf["dL"] = osf.Tot_Lmir_hot - osf.Tot_Lmir_bk
print("filas OSF:", len(osf), "| dL <= 0:", int((osf.dL <= 0).sum()), "| VRP <= 0:", int((osf.VRP <= 0).sum()))
ok = osf[osf.dL > 0].copy()
ok["k"] = ok.VRP / ok.dL
print("\nk = VRP/dL por sensor (W por unidad de radiancia), todo el archivo:")
res = ok.groupby("sensor").k.describe(percentiles=[.01, .05, .5, .95, .99])
print(res.to_string())
K = ok.groupby("sensor").k.median().to_dict()
print("\nk mediana por sensor:", {s: round(v, 1) for s, v in K.items()})
print("k 750 del codigo .m:", K_CODIGO_750, "| k 750 del dato / codigo:", round(K["VIIRS_750"] / K_CODIGO_750, 6))
print("k 375 / 140625 m2:", round(K["VIIRS_375"] / 140625, 4), " k 1000 / 1e6 m2:", round(K["MODIS_1000"] / 1e6, 4),
      " k 750 / 562500 m2:", round(K["VIIRS_750"] / 562500, 4))

ok["ratio"] = ok.VRP / (ok.dL * ok.sensor.map(K))
ok["zbin"] = pd.cut(ok.SatZen, [0, 20, 30, 40, 50, 55, 60, 65, 70, 90], right=False)
for tol, nombre in [(1e-3, "1e-3 (redondeo)"), (1e-2, "1 %")]:
    ok["cumple"] = (ok.ratio - 1).abs() <= tol
    print(f"\n=== fraccion que cumple |VRP/(dL k) - 1| <= {nombre}, por sensor y tramo de cenit (n filas) ===")
    tab = ok.groupby(["sensor", "zbin"], observed=True).cumple.agg(["mean", "size"])
    print(tab.unstack(0).to_string())
    print("global por sensor:", ok.groupby("sensor").cumple.mean().round(5).to_dict())
    print("2025 por sensor:", ok[ok.t.dt.year == 2025].groupby("sensor").cumple.mean().round(5).to_dict(),
          "n:", ok[ok.t.dt.year == 2025].groupby("sensor").size().to_dict())

# Que explica las que no cumplen (tolerancia 1 %)
ok["cumple"] = (ok.ratio - 1).abs() <= 1e-2
mal = ok[~ok.cumple]
print("\nfilas que NO cumplen al 1 %:", len(mal), "de", len(ok))
if len(mal):
    print(mal.groupby("sensor").size().to_dict())
    print("distribucion de ratio en las que no cumplen:")
    print(mal.groupby("sensor").ratio.describe(percentiles=[.05, .5, .95]).to_string())
    # candidatos: ratio ~ 1/cos(z), 1/cos^2, 1/cos^3, o ratio constante distinto
    cz = np.cos(np.radians(mal.SatZen))
    for nom, f in [("sec z", 1 / cz), ("sec^2", 1 / cz ** 2), ("sec^3", 1 / cz ** 3)]:
        r2 = mal.ratio / f
        print(f"  ratio / {nom}: mediana {r2.median():.4f}, p5 {r2.quantile(.05):.4f}, p95 {r2.quantile(.95):.4f}")
    print("  correlacion Spearman ratio vs SatZen en las que no cumplen:",
          round(mal[["ratio", "SatZen"]].corr(method="spearman").iloc[0, 1], 4))
    print("  primeras 15 filas que no cumplen:")
    print(mal[["id", "timeUTC", "Volc_Name", "sensor", "SatZen", "Npix", "Tot_Lmir_hot", "Tot_Lmir_bk", "VRP", "ratio"]]
          .head(15).to_string())

# Sobre 50 grados, por sensor: fraccion de cumplimiento al 1e-3 y al 1 %
print("\n=== Sobre 50 grados de cenit ===")
alto = ok[ok.SatZen >= 50]
for tol in (1e-3, 1e-2):
    c = ((alto.ratio - 1).abs() <= tol)
    print(f"tol {tol}:", alto.assign(c=c).groupby("sensor").c.agg(["mean", "size"]).to_string().replace("\n", " | "))

# Control positivo del instrumento
fila = ok.iloc[0]
print("\ncontrol positivo: fila", int(fila.id), "ratio real", round(fila.ratio, 6),
      "| con VRP x 1,10 el ratio seria", round(fila.ratio * 1.10, 6), "-> fuera de la tolerancia de 1 %:",
      abs(fila.ratio * 1.10 - 1) > 1e-2)
# Dependencia de k con el cenit en las que SI cumplen (si el area fuera por pixel geolocalizado, k creceria con z)
print("\nk mediana por tramo de cenit (todas las filas), por sensor:")
print(ok.groupby(["sensor", "zbin"], observed=True).k.median().unstack(0).round(1).to_string())
