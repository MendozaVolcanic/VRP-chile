# -*- coding: utf-8 -*-
"""COB 06 (S159). Reparto de las pasadas OSF 2025 sin record por volcan, sensor/plataforma y mes, con la magnitud que MIROVA
les asigna. Entrada: osf_pareo.csv (de 01; 2.934 filas OSF 2025 de 10 volcanes). Denominador de cada tabla declarado.
Pregunta 1: si el reparto fuera un artefacto del pareo, el control (las pasadas cubiertas) tendria que repartirse igual; se
imprime la tasa de faltantes sobre el total OSF por celda. Pregunta 2: tablas vacias = assert."""
import sys, io
from pathlib import Path
import pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(r"C:\vrp-trabajo\s159-pruebas\experiments\_s159\cob")
df = pd.read_csv(HERE / "osf_pareo.csv", parse_dates=["t"]); assert len(df) == 2934
INI = pd.Timestamp("2025-02-15")
df["tramo"] = df.t.map(lambda x: "A_antes_0215" if x < INI else "B_desde_0215")
df["falta"] = ~df.cubierta
df["mw"] = df.vrp_w / 1e6
pd.set_option("display.width", 220)
print("== por tramo (denominador = filas OSF del tramo) ==")
print(df.groupby("tramo").agg(osf=("falta", "size"), faltan=("falta", "sum")).assign(tasa=lambda d: (d.faltan / d.osf).round(3)).to_string())
print("\n== tramo A (antes de 2025-02-15) por volcan ==")
a = df[df.tramo == "A_antes_0215"]
print(a.groupby("vol").agg(osf=("falta", "size"), faltan=("falta", "sum"), dias_distintos=("t", lambda x: x.dt.normalize().nunique())).to_string())
print("\n== tramo B (desde 2025-02-15) por volcan ==")
b = df[df.tramo == "B_desde_0215"]
print(b.groupby("vol").agg(osf=("falta", "size"), faltan=("falta", "sum"), faltan_diurnas=("dayflag", lambda x: int(((x == 1) & b.loc[x.index, "falta"]).sum()))).assign(tasa=lambda d: (d.faltan / d.osf).round(3)).to_string())
print("\n== tramo B por Dayflag (denominador = filas OSF del tramo con ese Dayflag) ==")
print(b.groupby("dayflag").agg(osf=("falta", "size"), faltan=("falta", "sum")).to_string())
print("\n== tramo B nocturno (Dayflag=0): faltan por sensor ==")
print(b[(b.dayflag == 0)].groupby("sensor_esp").agg(osf=("falta", "size"), faltan=("falta", "sum")).to_string())
print("\n== tramo A por sensor (denominador OSF del tramo) ==")
print(a.groupby("sensor_esp").agg(osf=("falta", "size"), faltan=("falta", "sum")).to_string())
print("\n== tramo A por mes ==")
print(a.groupby(a.t.dt.strftime("%Y-%m")).agg(osf=("falta", "size"), faltan=("falta", "sum")).to_string())
print("\n== Magnitud MIROVA (VRP del OSF, MW) de las faltantes: tramo A nocturnas, tramo B nocturnas, tramo B diurnas, y de las cubiertas ==")
for nom, g in (("A noche", a[a.dayflag == 0]), ("B noche faltan", b[(b.dayflag == 0) & b.falta]), ("B dia faltan", b[(b.dayflag == 1) & b.falta]), ("cubiertas", df[df.cubierta])):
    print(f"{nom:16s} n={len(g):5d} mediana={g.mw.median():8.3f} p90={g.mw.quantile(.9):8.3f} max={g.mw.max():9.2f} | >=1 MW: {int((g.mw >= 1).sum())} | >=0.1 MW: {int((g.mw >= .1).sum())}")
print("\n== faltantes >= 1 MW por volcan y tramo (alertas protegidas por la regla de 1 MW) ==")
big = df[df.falta & (df.mw >= 1)]
print(big.groupby(["tramo", "vol", "dayflag"]).size().to_string())
print("\nclase OSF ('class') de faltantes vs cubiertas:")
print(pd.crosstab(df.falta, df["cls"]).to_string())
