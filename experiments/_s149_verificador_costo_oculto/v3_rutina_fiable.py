# -*- coding: utf-8 -*-
"""Verificador S149. Cuan fiable es 'fila RUTINA CONS VRP 0' como 'MIROVA miro y no alerto'?
Control interno: pasadas V375 de la ventana donde el consolidado dice RUTINA y el canal OCR (imagen por volcan)
dice ALERTA en el mismo minuto. Y latencia/edicion de las filas RUTINA de las 34."""
import csv, json, sys, io, collections
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent; EXP = AQUI.parent
C = list(csv.DictReader(open(EXP / "_s146_ab_sin_test1/_congelado/registro_vrp_consolidado.csv", encoding="utf-8")))
O = list(csv.DictReader(open(EXP / "_s146_ab_sin_test1/_congelado/registro_vrp_ocr.csv", encoding="utf-8")))
ven = lambda r: "2026-09-01" <= r["Fecha_Satelite_UTC"][:10] <= "2026-09-20" and r["Sensor"].strip() == "VIIRS375" and r["Fecha_Satelite_UTC"][11:13] < "12"
c = {(r["Volcan"], r["Fecha_Satelite_UTC"][:16]): r for r in C if ven(r)}
o = {(r["Volcan"], r["Fecha_Satelite_UTC"][:16]): r for r in O if ven(r)}
print("CONS V375 nocturnas en ventana:", len(c), dict(collections.Counter(r["Tipo_Registro"] for r in c.values())))
print("OCR  V375 nocturnas en ventana:", len(o), dict(collections.Counter(r["Tipo_Registro"] for r in o.values())))
x = collections.Counter((c[k]["Tipo_Registro"] if k in c else "SIN_FILA_CONS", r["Tipo_Registro"]) for k, r in o.items())
print("cruce CONS x OCR en el mismo minuto:", dict(x))
for k, r in sorted(o.items()):
    if k in c and c[k]["Tipo_Registro"] == "RUTINA": print("   CONS RUTINA pero OCR", r["Tipo_Registro"], k, "VRP OCR", r["VRP_MW"], "| conf", r.get("Confianza_Validacion"))
    if k not in c: print("   OCR sin fila CONS", k, r["Tipo_Registro"], r["VRP_MW"])
print("\nColumnas que distinguen una RUTINA 'vista' de una 'generada':")
rut = [r for r in c.values() if r["Tipo_Registro"] == "RUTINA"]
for col in ("Clasificacion Mirova", "Ruta Foto", "Editado", "Distancia_km", "VRP_MW"):
    print("  ", col, dict(collections.Counter(r[col] for r in rut).most_common(4)))
# alertas CONS: VRP minimo publicado (piso de lo que MIROVA llama alerta)
al = sorted(float(r["VRP_MW"]) for r in c.values() if r["Tipo_Registro"] == "ALERTA_TERMICA")
print("\nALERTA_TERMICA CONS V375: n %d | VRP min %.3f | p10 %.3f | mediana %.3f" % (len(al), al[0], al[len(al) // 10], al[len(al) // 2]))
fp = sorted(float(r["VRP_MW"]) for r in c.values() if r["Tipo_Registro"] == "FALSO_POSITIVO")
print("FALSO_POSITIVO CONS V375: n %d | VRP min %.3f" % (len(fp), fp[0] if fp else -1))
