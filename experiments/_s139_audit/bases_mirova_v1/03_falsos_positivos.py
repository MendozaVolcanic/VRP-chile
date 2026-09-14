"""03: FALSO_POSITIVO (consolidado) y FALSO_POSITIVO_OCR: donde estan, cuantos,
que volcanes, que sensores, si traen posicion, y si en la misma noche otro
sensor vio el crater (indicio de que un foco lejano puede tapar al crater en
una tabla que publica UNA fila por pasada).
"""
import sys

import pandas as pd

from comun import dir_remoto, encabezado, leer

D = dir_remoto(sys.argv)
cons = leer(f"{D}/registro_vrp_consolidado.csv")
ocr = leer(f"{D}/registro_vrp_ocr.csv")
pd.set_option("display.width", 220); pd.set_option("display.max_rows", 400); pd.set_option("display.max_columns", 40)

encabezado(
    "FALSOS POSITIVOS (focos lejanos) EN LAS BASES DE MIROVA-V1",
    "si no hubiera FP se imprimiria 0 por volcan; si la distancia no viniera, la columna seria NaN y se cuenta",
    "todas las tablas llevan n; una tabla vacia se imprime vacia",
    "se fuerza un FP con distancia NaN y se comprueba que el conteo de 'sin distancia' sube a 1",
)
fp = cons[cons["Tipo_Registro"] == "FALSO_POSITIVO"].copy()
print("FALSO_POSITIVO en consolidado:", len(fp), "| ventana:", fp["dt"].min(), "->", fp["dt"].max())
print("sin Distancia_km:", fp["Distancia_km"].isna().sum(), "| sin lat/lon: no existen esas columnas en el CSV:",
      [c for c in ("lat", "lon", "Lat", "Lon", "acimut", "Azimut") if c in cons.columns] == [])
print("\n--- FP por volcan x sensor")
print(pd.crosstab(fp["Volcan"], fp["Sensor"], margins=True))
print("\n--- FP nocturnos por volcan x sensor")
print(pd.crosstab(fp[fp.noche]["Volcan"], fp[fp.noche]["Sensor"], margins=True))
print("\n--- FP por mes x sensor")
print(pd.crosstab(fp["mes"], fp["Sensor"], margins=True))
print("\n--- distancia (km) de los FP por sensor: min / mediana / max")
print(fp.groupby("Sensor")["Distancia_km"].agg(["min", "median", "max", "count"]))
print("\n--- VRP (MW) de los FP por sensor: min / mediana / max")
print(fp.groupby("Sensor")["VRP_MW"].agg(["min", "median", "max"]))

print("\n=== MODIS: FP por volcan, con distancia redondeada (fuentes lejanas persistentes) ===")
fm = fp[fp["Sensor"] == "MODIS"].copy()
fm["dist_r"] = fm["Distancia_km"].round(0)
for v, g in fm.groupby("Volcan"):
    top = g["dist_r"].value_counts().head(4).to_dict()
    print(f"  {v:22s} n={len(g):3d} noct={int(g['noche'].sum()):3d} dist_km mediana={g['Distancia_km'].median():5.1f} "
          f"VRP mediana={g['VRP_MW'].median():5.2f} max={g['VRP_MW'].max():6.2f} distancias frecuentes={top}")

print("\n=== En la misma noche de volcan de un FP, hubo ALERTA (dentro del radio) en OTRO sensor? ===")
al = cons[cons["Tipo_Registro"] == "ALERTA_TERMICA"]
al_keys = set(zip(al["Volcan"], al["noche_id"], al["Sensor"]))
al_vn = {}
for v, n, s in al_keys:
    al_vn.setdefault((v, n), set()).add(s)
res = []
for _, r in fp[fp.noche].iterrows():
    otros = al_vn.get((r["Volcan"], r["noche_id"]), set()) - {r["Sensor"]}
    mismo = r["Sensor"] in al_vn.get((r["Volcan"], r["noche_id"]), set())
    res.append({"Volcan": r["Volcan"], "Sensor": r["Sensor"], "otro_sensor_alerta": bool(otros),
                "mismo_sensor_alerta_otra_pasada": mismo})
res = pd.DataFrame(res)
print("FP nocturnos:", len(res))
print(res.groupby("Sensor")[["otro_sensor_alerta", "mismo_sensor_alerta_otra_pasada"]].agg(["sum", "count"]))
print("\n  por volcan (MODIS): FP nocturnos con alerta de otro sensor esa noche")
print(res[res.Sensor == "MODIS"].groupby("Volcan")["otro_sensor_alerta"].agg(["sum", "count"]))

print("\n=== FALSO_POSITIVO_OCR ===")
fo = ocr[ocr["Tipo_Registro"] == "FALSO_POSITIVO_OCR"].copy()
print("filas:", len(fo), "| ventana:", fo["dt"].min(), "->", fo["dt"].max())
print(pd.crosstab(fo["Volcan"], fo["Sensor"], margins=True))
print("Distancia_km == 0 (no medida):", (fo["Distancia_km"] == 0).sum())
print("Confianza:", fo["Confianza_Validacion"].value_counts().to_dict())
print("Editado (AUTO = reconciliado contra latest.php):", fo["Editado"].value_counts().to_dict())
print("Version_OCR:", fo["Version_OCR"].value_counts().to_dict())
print("Clasificacion Mirova (deberia ser NULO):", fo["Clasificacion Mirova"].value_counts().to_dict())
print("con nota RECONCILIADO:", fo["Nota_Validacion"].str.contains("RECONCILIADO").sum())
print("VRP >= 10 MW:", (fo["VRP_MW"] >= 10).sum(), "| diurnas (12<=h UTC<=23):",
      int(((fo["dt"].dt.hour >= 12) & (fo["dt"].dt.hour <= 23)).sum()))

print("\n=== Unicidad: una fila por (Volcan, Sensor, timestamp) en el consolidado -> UNA distancia y UN VRP por pasada ===")
print("filas:", len(cons), "| llaves distintas:", len(cons.drop_duplicates(["timestamp", "Volcan", "Sensor"])))
print("pasadas (Volcan, Sensor, timestamp) con >1 fila:", int((cons.groupby(["timestamp", "Volcan", "Sensor"]).size() > 1).sum()))

# control positivo
fp2 = fp.copy(); fp2.loc[fp2.index[0], "Distancia_km"] = float("nan")
print("\nCONTROL: tras anular una distancia, 'sin Distancia_km' =", int(fp2["Distancia_km"].isna().sum()), "(esperado 1)")

print("\n=== Filas de artefacto curadas a mano (anotaciones.csv) ===")
try:
    print(open(f"{D}/anotaciones.csv", encoding="utf-8").read())
except FileNotFoundError:
    print("anotaciones.csv no esta en", D)
