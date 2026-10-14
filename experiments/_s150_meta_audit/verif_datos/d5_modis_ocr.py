"""D5: alertas MODIS que existen solo en el OCR (sin fila ALERTA_TERMICA de la tabla para el mismo volcan, sensor MODIS y
fecha +-10 min). argv: consolidado.csv ocr.csv [etiqueta]"""
import sys, pandas as pd
c = pd.read_csv(sys.argv[1], dtype=str); o = pd.read_csv(sys.argv[2], dtype=str)
norm = lambda s: s.str.lower().str.replace(r"[^a-z]", "", regex=True)
for df in (c, o):
    df["t"] = pd.to_datetime(df.Fecha_Satelite_UTC); df["v"] = norm(df.Volcan)
om = o[(o.Sensor == "MODIS") & o.Tipo_Registro.str.contains("ALERTA", na=False)]
ca = c[(c.Sensor == "MODIS")]
res = []
for _, r in om.iterrows():
    m = ca[(ca.v == r.v) & (abs(ca.t - r.t) <= pd.Timedelta(minutes=10))]
    tipo = "|".join(m.Tipo_Registro) if len(m) else "SIN FILA"
    if "ALERTA_TERMICA" not in tipo:
        res.append((r.Fecha_Satelite_UTC, r.Volcan, r.VRP_MW, r.Distancia_km, tipo, r.get("Version_OCR")))
print(sys.argv[3] if len(sys.argv) > 3 else "", "OCR MODIS alertas:", len(om), "sin ALERTA en tabla:", len(res))
for x in res: print("  ", x)
