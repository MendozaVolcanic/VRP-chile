"""D1: filas presentes en el consolidado antes de la caida (e489b42f) y ausentes despues (fec07850)
y si reaparecen en la version mas reciente. Uso: python d1_filas_perdidas.py <antes.csv> <despues.csv> <ultimo.csv> [ocr.csv]"""
import sys, pandas as pd
a, d, u = [pd.read_csv(p, dtype=str) for p in sys.argv[1:4]]
key = ["Fecha_Satelite_UTC", "Volcan", "Sensor"]
print("filas antes/despues/ultimo:", len(a), len(d), len(u))
for n, df in (("antes", a), ("despues", d), ("ultimo", u)):
    print(n, "duplicados por clave:", df.duplicated(key).sum())
ka = set(map(tuple, a[key].values)); kd = set(map(tuple, d[key].values)); ku = set(map(tuple, u[key].values))
lost = a[[tuple(r) not in kd for r in a[key].values]]
print("claves perdidas:", len(lost), " nuevas en despues:", len(kd - ka))
print("perdidas que reaparecen en ultimo:", sum(tuple(r) in ku for r in lost[key].values))
print(lost["Tipo_Registro"].value_counts().to_string())
lost = lost.copy(); lost["fecha"] = lost["Fecha_Satelite_UTC"].str[:10]
print("rango fechas perdidas:", lost.fecha.min(), lost.fecha.max())
print(lost.groupby(["Sensor"]).size().to_string())
al = lost[lost.Tipo_Registro.str.contains("ALERTA", na=False)]
cols = ["Fecha_Satelite_UTC", "Fecha_Captura_Chile", "Volcan", "Sensor", "VRP_MW", "Distancia_km", "Tipo_Registro", "Clasificacion Mirova"]
print(al[cols].to_string())
if len(sys.argv) > 4:
    o = pd.read_csv(sys.argv[4], dtype=str)
    print("OCR columnas:", list(o.columns)[:15])
