# -*- coding: utf-8 -*-
"""V1 (S158) verificacion de F6-1: en el OSF v2.5, VIIRS 750, la razon VRP / (1,97e7 * 0,5625 * (Lhot - Lbk)) por cenit.

Pregunta 1: si el OSF no siguiera la formula del codigo en algun estrato, la razon se apartaria de 1 ahi; se mide por
fila. Pregunta 2: control positivo, la misma razon con el k de 750 sobre las filas de 375 m y 1 km debe dar != 1 en
TODAS (otro k); y control de lectura: n > 0 por estrato o SIN DATO.
Hipotesis alternativas que se prueban: (a) la razon sigue una ley continua del cenit (p. ej. cos, 1/sec^n, area de
pixel en el borde del barrido) en vez de un escalon; (b) depende de Npix, dia/noche, satelite o anio; (c) es una
reasignacion del fondo (VRP coherente con otro Lbk) y no un factor.
Denominador: filas Resolution == 750 de VRP_GLOBAL_ARCHIVE_2025.csv (ventana del archivo, se imprime). Solo lectura.
"""
import sys, io
import numpy as np, pandas as pd
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RUTA = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\data\mirova_reference\VRP_GLOBAL_ARCHIVE_2025.csv"
df = pd.read_csv(RUTA)
df["t"] = pd.to_datetime(df.timeUTC, format="%d/%m/%Y %H:%M")
K = 1.97e7 * 0.5625
df["r"] = df.VRP / (K * (df.Tot_Lmir_hot - df.Tot_Lmir_bk))
for res in (375, 1000):
    x = df[df.Resolution == res]
    print(f"CONTROL res {res}: n={len(x)} filas con |r-1|<1e-4: {int(((x.r-1).abs()<1e-4).sum())}")
d = df[df.Resolution == 750].copy()
d["fuera"] = (d.r - 1).abs() >= 1e-4
print("V750 n", len(d), "ventana", d.t.min(), d.t.max(), "fuera de identidad", int(d.fuera.sum()))
d["zbin"] = pd.cut(d.SatZen, [0, 10, 20, 30, 40, 45, 48, 49, 49.5, 50, 50.5, 51, 52, 55, 60, 65, 70, 75])
g = d.groupby("zbin", observed=True).agg(n=("r", "size"), fuera=("fuera", "sum"), r_med_fuera=("r", lambda s: s[d.loc[s.index, "fuera"]].median()))
print(g.to_string())
z = d[d.SatZen > 50]
print("\ncenit > 50: n", len(z), "fuera", int(z.fuera.sum()), f"({z.fuera.mean():.3f})", " mediana r en fuera", round(z[z.fuera].r.median(), 4))
print("cenit <= 50: n", int((d.SatZen <= 50).sum()), "fuera", int(d[d.SatZen <= 50].fuera.sum()))
zf = z[z.fuera]
print("\n(b) fuera>50 por Dayflag:", z.groupby("Dayflag").fuera.agg(["size", "sum"]).to_dict())
print("    por Satellite:", z.groupby("Satellite").fuera.agg(["size", "sum"]).to_dict())
print("    por anio:", z.groupby(z.t.dt.year).fuera.agg(["size", "sum"]).T.to_string())
print("    Npix fuera vs dentro (>50): mediana", zf.Npix.median(), z[~z.fuera].Npix.median())
# (a) ley continua: correlacion de r con el cenit dentro de las filas fuera
print("\n(a) r en filas fuera por cenit (cuantiles de r):")
print(zf.groupby(pd.cut(zf.SatZen, [50, 52, 55, 60, 65, 70, 75]), observed=True).r.describe()[["count", "25%", "50%", "75%"]].round(4).to_string())
# candidatos geometricos de area de pixel VIIRS en el borde: no son de la formula; se compara mediana de r con 1/f
th = np.radians(zf.SatZen)
for nm, f in [("cos", np.cos(th)), ("cos^2", np.cos(th) ** 2), ("cos^3", np.cos(th) ** 3)]:
    print(f"   mediana r / {nm}: {np.median(zf.r / f):.4f}  dispersion IQR {np.subtract(*np.percentile(zf.r / f, [75, 25])):.4f}")
# (c) Lbk implicito: el Lbk que haria cumplir la identidad, contra el publicado
lbk_imp = d.Tot_Lmir_hot - d.VRP / K
zf2 = d[(d.SatZen > 50) & d.fuera]
print("\n(c) Lbk implicito / Lbk publicado en fuera>50: mediana", round(float((lbk_imp[zf2.index] / zf2.Tot_Lmir_bk).median()), 4))
print("    VRP/(K*Lhot) en fuera>50: mediana", round(float((zf2.VRP / (K * zf2.Tot_Lmir_hot)).median()), 4))
# valores redondos de r
print("    r en fuera>50, 15 valores mas frecuentes (4 decimales):", zf2.r.round(4).value_counts().head(15).to_dict())
# caso Villarrica 2023-11-27 06:18
v = d[(d.Volc_Name.str.contains("Villarrica")) & (d.timeUTC.str.startswith("27/11/2023 06:1"))]
print("\nVillarrica 2023-11-27 06:1x:\n", v[["timeUTC", "Satellite", "SatZen", "Npix", "Tot_Lmir_hot", "Tot_Lmir_bk", "VRP", "r"]].to_string())
print("   VRP codigo MW", (K * (v.Tot_Lmir_hot - v.Tot_Lmir_bk) / 1e6).round(2).tolist(), "VRP OSF MW", (v.VRP / 1e6).round(2).tolist())
