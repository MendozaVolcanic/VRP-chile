# -*- coding: utf-8 -*-
"""Inventario de Distancia_km en registro_vrp_ocr.csv (Mirova-v1, bajado hoy por raw).
Clases: vacia (NaN), cero (==0), medida (>0). Tramos A119 del OCR: <2026-03-01, 03-01..06-10, 06-11..06-12,
06-13..08-05, 08-06..10-08, >=10-09 (hito Suomi NPP otra pasada)."""
import sys, pandas as pd
sys.stdout.reconfigure(encoding="utf-8")
d = pd.read_csv(sys.argv[1])
d["f"] = d.Fecha_Satelite_UTC.str[:10]
def clase(x):
    if pd.isna(x): return "vacia"
    return "cero" if float(x) == 0 else "medida"
d["cl"] = d.Distancia_km.map(clase)
cortes = [("2026-03-01","a <03-01"),("2026-06-11","b 03-01..06-10"),("2026-06-13","c 06-11..06-12"),
          ("2026-08-06","d 06-13..08-05"),("2026-10-09","e 08-06..10-08"),("9999","f >=10-09")]
def tramo(f):
    for c,n in cortes:
        if f < c: return n
d["tramo"] = d.f.map(tramo)
print("filas", len(d), "| rango", d.Fecha_Satelite_UTC.min(), "a", d.Fecha_Satelite_UTC.max())
print("\n== total por clase\n", d.cl.value_counts().to_string())
for col in ["Tipo_Registro", "Sensor", "tramo"]:
    print(f"\n== {col} x clase\n", pd.crosstab(d[col], d.cl, margins=True).to_string())
print("\n== tramo x Tipo x clase\n", pd.crosstab([d.tramo, d.Tipo_Registro], d.cl).to_string())
print("\n== primera y ultima fecha con distancia medida (>0):", d[d.cl=="medida"].f.min(), d[d.cl=="medida"].f.max())
print("== ultima fecha con cero:", d[d.cl=="cero"].f.max(), "| cero desde 06-13:", ((d.cl=="cero")&(d.f>="2026-06-13")).sum())
print("== medida antes de 06-13:", ((d.cl=="medida")&(d.f<"2026-06-13")).sum())
print("\n== cero desde 06-13 por tipo/sensor\n", d[(d.cl=="cero")&(d.f>="2026-06-13")].groupby(["Tipo_Registro","Sensor"]).size().to_string())
print("\n== Version_OCR x clase\n", pd.crosstab(d.Version_OCR, d.cl).to_string())
