"""D2: detecciones lejanas de MIROVA (Tipo_Registro FALSO_POSITIVO) desde 2026-03-01, por dia/noche.
Noche = hora UTC en [0, 12) (pasadas nocturnas MODIS 01-07 UTC y VIIRS 04-08 UTC en Chile; diurnas 14-21 UTC).
argv: csv consolidado [hasta=YYYY-MM-DD]"""
import sys, pandas as pd
df = pd.read_csv(sys.argv[1], dtype=str)
df["t"] = pd.to_datetime(df.Fecha_Satelite_UTC)
hasta = sys.argv[2] if len(sys.argv) > 2 else "2100-01-01"
w = df[(df.t >= "2026-03-01") & (df.t < hasta)]
print("ventana:", w.t.min(), w.t.max(), "filas:", len(w))
print(w.Tipo_Registro.value_counts().to_string())
fp = w[w.Tipo_Registro == "FALSO_POSITIVO"].copy()
fp["d"] = pd.to_numeric(fp.Distancia_km); fp["v"] = pd.to_numeric(fp.VRP_MW)
fp["noche"] = fp.t.dt.hour < 12
print("FP total", len(fp), "noche", fp.noche.sum(), "dia", (~fp.noche).sum())
print("hist hora UTC:", fp.t.dt.hour.value_counts().sort_index().to_dict())
print("mediana dist", fp.d.median(), "max", fp.d.max(), "min", fp.d.min())
print("duplicados clave", fp.duplicated(["Fecha_Satelite_UTC","Volcan","Sensor"]).sum())
print("Clasificacion de las FP:", fp["Clasificacion Mirova"].value_counts().to_dict())
print("VRP==0 entre FP:", (fp.v == 0).sum())
print(fp.groupby(["noche","Sensor"]).size().to_string())
print(fp.groupby(["noche","Volcan"]).size().unstack(0).to_string())
al = w[w.Tipo_Registro == "ALERTA_TERMICA"]
print("ALERTA_TERMICA en ventana:", len(al))
print("NULO por Tipo:", w[w["Clasificacion Mirova"]=="NULO"].Tipo_Registro.value_counts().to_dict())
