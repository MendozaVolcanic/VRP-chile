# -*- coding: utf-8 -*-
"""S163: tasa agrupada de falsos del placebo simétrico (c) de P2, desde placebos_produccion_salida.json.

POR QUÉ: cada celda tiene 400 repeticiones y la prueba de signos es exacta (su tasa verdadera por cola es 5 % o menos
por construcción), así que una celda en 6,5 % puede ser azar de 400 tiradas. Se agrupan las celdas INDEPENDIENTES: en
la ventana O, VIIRS 750 y MODIS dan la misma tabla con y sin OCR (las pasadas sólo OCR no entran a P2), así que el canal
«tabla» de esos dos sensores se deja fuera para no contarlas dos veces. Se separa además prueba exacta (B de 20 o
menos) de prueba por sorteos.

Uso: python -I experiments/_s163_instrumento_pendientes/agrupar_placebo_c.py <salida.json>
"""
import json
import math
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")


def wilson(k, n, z=1.96):
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0.0, c - m), min(1.0, c + m)


d = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
grupos = {}
for c in d["celdas"]:
    duplicada = c["ventana"] == "O" and c["canal"] == "tabla" and c["sensor"] in ("VIIRS750", "MODIS")
    for x in c["placebo_c"]:
        if duplicada:
            continue
        metodo = "exacta (B<=20)" if x["B_mediana"] <= 20 else "sorteos (B>20)"
        for clave in (("fraccion %.2f" % x["fraccion"], "todas"), ("fraccion %.2f" % x["fraccion"], metodo),
                      ("todas", "todas")):
            g = grupos.setdefault(clave, {"GANA": 0, "PIERDE": 0, "n": 0, "celdas": 0})
            g["GANA"] += x["GANA"]["k"]
            g["PIERDE"] += x["PIERDE"]["k"]
            g["n"] += x["n"]
            g["celdas"] += 1
print("Placebo simétrico (c), celdas independientes (sin O-tabla de VIIRS 750 y MODIS)")
for (fr, met), g in sorted(grupos.items()):
    lg, hg = wilson(g["GANA"], g["n"])
    lp, hp = wilson(g["PIERDE"], g["n"])
    print("%-15s %-16s celdas %2d  GANA %4d/%5d = %.2f %% (IC95 %.2f a %.2f)  PIERDE %4d/%5d = %.2f %% (IC95 %.2f a %.2f)"
          % (fr, met, g["celdas"], g["GANA"], g["n"], 100 * g["GANA"] / g["n"], 100 * lg, 100 * hg,
             g["PIERDE"], g["n"], 100 * g["PIERDE"] / g["n"], 100 * lp, 100 * hp))
# Comprobación de la premisa de duplicado: placebo c idéntico en O union y O tabla para VIIRS 750 y MODIS.
por = {(c["ventana"], c["sensor"], c["canal"]): c for c in d["celdas"]}
for s in ("VIIRS750", "MODIS"):
    a, b = por[("O", s, "union")], por[("O", s, "tabla")]
    print("O %s: placebo c union == tabla: %s; sustrato union %s / tabla %s" % (
        s, [x["resultados"] for x in a["placebo_c"]] == [x["resultados"] for x in b["placebo_c"]],
        a["sustrato_p2"], b["sustrato_p2"]))
