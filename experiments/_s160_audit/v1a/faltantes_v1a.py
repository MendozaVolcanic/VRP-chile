# -*- coding: utf-8 -*-
"""V1a, fila R11 por el camino de la cobertura: el evaluador tolera que a C0 le falte hasta 5 % de las pasadas de
produccion por volcan y sensor (MAX_FALTA_CONTRA_PRODUCCION, evaluar_fk.py:73). Una pasada que falta en TODOS los
brazos no entra a ninguna cuenta. Pregunta: cuantas de esas pasadas tienen una alerta de MIROVA de 1 MW o mas
(lectura A, tipo ALERTA*, sin SIN_GEOMETRIA) en la referencia congelada del instrumento, +-120 s, mismo volcan y sensor.
Vara de produccion: data/mirova_equivalent de d516b9d8c (OJO: reprocesada con K despues de S153, #883/#884; lo que
falta hoy no es necesariamente lo que faltaba al evaluar). Control positivo: se inyecta una pasada falsa con alerta.
Uso: python faltantes_v1a.py"""
import csv, glob, json
from datetime import datetime
from pathlib import Path
R = Path(r"C:\vrp-trabajo\s159-pruebas\experiments\_s151_prereg_fk_11")
D = Path(r"D:\vrp-trabajo\temporales\s160_audit")
def bucket(s):
    s = s or ""
    return "MODIS" if s.startswith("MODIS") else ("VIIRS750" if s.endswith("_750") else ("VIIRS375" if s.startswith("VIIRS") else None))
def claves(dirs, d, h):
    out = set()
    for dd in dirs:
        for p in glob.glob(str(dd / "*.json")):
            for r in json.load(open(p, encoding="utf-8"))["records"]:
                b = bucket(r.get("sensor")); t = r.get("datetime_utc", "")
                if b and d <= t[:10] <= h: out.add((Path(p).stem, b, t[:16].replace("T", " ")))
    return out
VOLMAP = {"PlanchonPeteroa": ["PlanchonPeteroa", "Planchon-Peteroa"], "PuyehueCordonCaulle": ["Puyehue-Cordon Caulle", "PuyehueCordonCaulle"],
          "NevadosDeChillan": ["Nevados de Chillan", "NevadosDeChillan"]}
def alertas(cfg, d, h):
    out = []
    for f in ("registro_vrp_consolidado.csv", "registro_vrp_ocr.csv"):
        with open(cfg / f, encoding="utf-8", errors="replace", newline="") as fh:
            rows = list(csv.reader(fh))
        for r in rows[1:]:
            if len(r) < 9 or not (d <= r[1][:10] <= h): continue
            try: v = float(r[5])
            except ValueError: continue
            if r[7].startswith("ALERTA") and "SIN_GEOMETRIA" not in r[7] and v >= 1.0:
                out.append((r[3], r[4], datetime.strptime(r[1][:19], "%Y-%m-%d %H:%M:%S"), v, f[13:16]))
    return out
for nom, raices, cfg, d, h in (("V1", [D/"f1a"/"v1_union"], R/"_congelado_v1", "2026-08-29", "2026-10-08"),
                              ("V2", [D/"f1a"/"v2a_union", D/"f1a"/"v2b_union"], R/"_congelado_v2", "2026-03-01", "2026-06-12")):
    c0 = claves([x / "_s146_ab_control" for x in raices], d, h)
    prod = claves([D/"main"/"data"/"mirova_equivalent"], d, h)
    vols11 = {x[0] for x in c0}
    prod = {x for x in prod if x[0] in vols11}   # solo los 11 Tier A (la primera version mezclaba los 34 restantes)
    falta = sorted(prod - c0)
    A = alertas(cfg, d, h)
    for sint in (False, True):
        f2 = falta + ([("Lascar", "VIIRS375", A[0][2].strftime("%Y-%m-%d %H:%M"))] if sint and A else [])
        hits = []
        for (v, b, t) in f2:
            tt = datetime.strptime(t, "%Y-%m-%d %H:%M")
            for (vol, sen, ta, vrp, canal) in A:
                if (vol == v or vol in VOLMAP.get(v, [])) and sen == b and abs((ta - tt).total_seconds()) <= 120:
                    hits.append((v, b, t, vrp, canal))
        if sint and A:
            # el control inyecta la hora de una alerta real con el volcan de la alerta
            vol0, sen0, ta0 = A[0][0], A[0][1], A[0][2]
            f3 = falta + [(vol0, sen0, ta0.strftime("%Y-%m-%d %H:%M"))]
            hits = [x for x in f3 if any((a[0] == x[0]) and a[1] == x[1] and abs((a[2] - datetime.strptime(x[2], "%Y-%m-%d %H:%M")).total_seconds()) <= 120 for a in A)]
        print("%s%s: pasadas C0 %d, produccion %d, en produccion y no en C0 %d (VIIRS375 %d, VIIRS750 %d, MODIS %d); alertas >=1 MW en la referencia %d; faltantes con alerta >=1 MW: %d %s" % (
            "[CONTROL] " if sint else "", nom, len(c0), len(prod), len(falta), sum(x[1] == "VIIRS375" for x in falta), sum(x[1] == "VIIRS750" for x in falta),
            sum(x[1] == "MODIS" for x in falta), len(A), len(hits), hits[:8]))
