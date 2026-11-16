#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V1 (S175), afirmación 153: pasadas MODIS que la guardia K registra y producción no (por volcán, minuto y
sensor), desde 2026-11-01, en una carpeta de datos (e75a7d52d).
Pregunta 1: si la vía descartara gránulos en silencio, faltarían claves en producción que la guardia sí tiene;
este cruce lo ve. Control positivo: el mismo cruce en sentido inverso (producción sin guardia) y el número total
de pares; y un control sintético: borrar de producción una clave conocida y comprobar que aparece.
Pregunta 2: si el lector estuviera muerto, el total de claves sería 0 en los dos lados (se imprime).
El pareo es por minuto exacto 'YYYY-MM-DD HH:MM' y sensor, más una tolerancia de ±2 min como la del banco.
Uso: python claves_guardia_vs_prod.py <carpeta con mirova_equivalent/ y guardia_k_modis/>
"""
import json, os, sys
from datetime import datetime
VOLS = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan",
        "Llaima", "Villarrica", "Copahue", "PuyehueCordonCaulle", "Chaiten"]
base = sys.argv[1]
DESDE = "2026-11-01"

def claves(sub, quitar=None):
    out = {}
    for v in VOLS:
        with open(os.path.join(base, sub, v + ".json"), encoding="utf-8") as fh:
            for r in json.load(fh).get("records") or []:
                s = str(r.get("sensor") or "")
                d = str(r.get("datetime_utc") or "").replace("T", " ")[:16]
                if s.startswith("MODIS") and d >= DESDE:
                    k = (v, s, d)
                    if k != quitar:
                        out[k] = r
    return out

def faltan(a, b):
    res = []
    for (v, s, d) in sorted(a):
        t = datetime.strptime(d, "%Y-%m-%d %H:%M")
        if not any(v2 == v and s2 == s and abs((datetime.strptime(d2, "%Y-%m-%d %H:%M") - t).total_seconds()) <= 120
                   for (v2, s2, d2) in b):
            res.append((v, s, d))
    return res

g, p = claves("guardia_k_modis"), claves("mirova_equivalent")
print("claves MODIS desde", DESDE, ": guardia", len(g), "produccion", len(p))
f1 = faltan(g, p)
print("guardia registra y produccion no:", len(f1))
for k in f1:
    r = g[k]
    print("  ", k, "guardia vrp_mw", r.get("vrp_mw"), "distance_class", r.get("distance_class"), "pv",
          r.get("product_version"), "processed", r.get("processed_utc"))
f2 = faltan(p, g)
print("produccion registra y guardia no:", len(f2))
for k in f2:
    print("  ", k, "via", p[k].get("via_codigo_mirova"), "processed", p[k].get("processed_utc"))
# control sintético: quitar de producción la primera clave común
comun = sorted(set(g) & set(p))
if comun:
    q = comun[len(comun) // 2]
    p2 = claves("mirova_equivalent", quitar=q)
    f3 = faltan(g, p2)
    print("CONTROL: quitada", q, "-> aparece en el cruce:", q in f3, "(", len(f3), "faltantes )")
