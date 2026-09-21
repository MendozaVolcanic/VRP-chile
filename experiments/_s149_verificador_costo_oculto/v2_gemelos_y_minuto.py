# -*- coding: utf-8 -*-
"""Verificador S149. (1) pareo exacto al MINUTO (los CSV traen segundos 00, 01 o 02). (2) gemelos: pasadas
nuestras en granulos contiguos (6 min) del mismo sobrevuelo; una sin_info cuyo gemelo es pos NO es otra pasada."""
import csv, json, sys, io, collections
from datetime import datetime
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent; EXP = AQUI.parent
T = json.loads((EXP / "_s148_verificador_resultado" / "tabla.json").read_text(encoding="utf-8"))
B, F = "_s146_ab_sin_test1", "_s147_ab_sin_test1_max"
NOMBRE = {"Puyehue-Cordon Caulle": "PuyehueCordonCaulle", "Nevados de Chillan": "NevadosDeChillan"}
ref = collections.defaultdict(list)
for n, src in (("registro_vrp_consolidado.csv", "CONS"), ("registro_vrp_ocr.csv", "OCR")):
    for r in csv.DictReader(open(EXP / "_s146_ab_sin_test1" / "_congelado" / n, encoding="utf-8")):
        if r["Sensor"].strip() != "VIIRS375": continue
        v = NOMBRE.get(r["Volcan"].strip(), r["Volcan"].strip())
        ref[(v, r["Fecha_Satelite_UTC"][:16])].append((r["Tipo_Registro"].strip(), float(r["VRP_MW"] or 0), src))
print("segundos en Fecha_Satelite_UTC (CONS V375): ver salida_v1; aca el pareo es por minuto truncado")
mias = json.load(open(AQUI / "apagadas_mias.json", encoding="utf-8"))
ex = 0
for a in mias:
    ff = ref.get((a["vol"], a["dt"][:16]), [])
    a["rut_min"] = any(t == "RUTINA" and s == "CONS" and v == 0 for t, v, s in ff)
    ex += a["rut_min"]
print("apagadas (50) con fila RUTINA CONS VRP 0 en el MISMO minuto:", ex, "| sin:", len(mias) - ex)
print("coincide con el pareo de 120 s:", all(a["rut_min"] == a["rut"] for a in mias))
# gemelos
labs = {}
for k, v in T.items():
    vol, b, dts = k.split("|")
    if b == "VIIRS375": labs[(vol, datetime.strptime(dts[:16], "%Y-%m-%d %H:%M"))] = (v[B]["lab"], v[B]["sensor"], v[B]["pub"], v[F]["pub"])
print("\napagadas con un gemelo nuestro a 6 min o menos (mismo sobrevuelo partido en dos granulos):")
n = 0
for a in mias:
    dt = datetime.strptime(a["dt"][:16], "%Y-%m-%d %H:%M")
    for (vol, d2), (lab, sat, pb, pf) in labs.items():
        if vol == a["vol"] and d2 != dt and abs((d2 - dt).total_seconds()) <= 420:
            n += 1; print("   %-20s %s (%s, rut=%s) gemelo %s lab %s sat %s pubB %s pubF %s" % (a["vol"], a["dt"], a["sat"], a["rut"], d2.strftime("%H:%M"), lab, sat, pb, pf))
print("total:", n)
