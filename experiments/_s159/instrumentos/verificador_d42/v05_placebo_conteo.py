# -*- coding: utf-8 -*-
"""Verificador D-42, afirmacion 7: en el placebo del 1 % (placebo_1pct_V1.jsonl y _V2.jsonl del implementador),
¿en cuantas celdas (semilla x regla x sensor) la calibracion de P2 LLEGO A CORRER (falsos_gana no es None)? Un
«GANA en 0 de 20» solo mide algo donde P2 paso del SIN SUSTRATO.

Pregunta 1: si la calibracion nunca corriera, ¿se ve? Si: todas las celdas tendrian falsos_gana None.
Pregunta 2: si el conteo estuviera muerto, ¿se ve? Si: el total de celdas tiene que ser 20 x 2 reglas x 2 sensores = 80
por ventana.
"""
import collections
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
CAL = AQUI.parent / "calib_p2"


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    for v in ("V1", "V2"):
        filas = [json.loads(l) for l in open(CAL / ("placebo_1pct_%s.jsonl" % v), encoding="utf-8") if l.strip()]
        celdas = corrio = 0
        por = collections.Counter()
        gana_posible = collections.Counter()
        for x in filas:
            for k in x:
                if k.startswith("P2|"):
                    celdas += 1
                    c = x[k]
                    if c["falsos_gana"] is not None:
                        corrio += 1
                        por[(k, c["calibrada"], c["sin_calibrar"])] += 1
                    else:
                        gana_posible[(k, c["calibrada"])] += 1
        print("== %s: %d semillas, %d celdas semilla x regla x sensor | la calibracion corrio en %d (%.0f %%) | "
              "apagadas por semilla %s" % (v, len(filas), celdas, corrio, 100 * corrio / celdas,
                                            sorted({x["apagadas_pedidas"] for x in filas})))
        for k, n in sorted(por.items()):
            print("   corrio: %-22s calibrada %-12s sin calibrar %-12s x%d" % (k[0], k[1], k[2], n))
        for k, n in sorted(gana_posible.items()):
            print("   no corrio: %-22s %-12s x%d" % (k[0], k[1], n))
        nn = [x[k]["n"] for x in filas for k in x if k.startswith("P2|")]
        print("   discordantes por celda: min %d, mediana %d, max %d | minimo para calibrar N_MIN_PARES=5 y 3 noches" % (
            min(nn), sorted(nn)[len(nn) // 2], max(nn)))


if __name__ == "__main__":
    main()
