# -*- coding: utf-8 -*-
"""Verificador D-42, vuelta 2, afirmacion 5 (V42-01): la curva del placebo (1, 5, 10, 20 % de las publicaciones de K
apagadas al azar en D), leida desde los JSONL del implementador (calib_p2/placebo_*_V1.jsonl y _V2.jsonl).

Por celda (semilla x regla x sensor): ¿corrio la calibracion (falsos_gana no None)? ¿que dio? Y la COMPOSICION de las
pasadas discordantes, que los JSONL permiten reconstruir sin abrir nada mas: cada discordante aporta +1 (alerta bajo
1 MW que K publicaba y D apago: error nuevo de D) o -1 (negativo limpio que K publicaba y D apago: error que D deja de
cometer); con n discordantes y neto, alertas = (n + neto) / 2 y negativos = (n - neto) / 2.

Pregunta 1 (¿veria un placebo que SI pudiera dar GANA?): si: si negativos > alertas en una celda, el neto es negativo y
GANA es posible; se cuenta cuantas celdas tienen neto < 0. Pregunta 2 (¿veria un instrumento muerto?): el total de
celdas tiene que ser 80 por archivo y n = alertas + negativos en cada celda (paridad: n + neto par).
Uso: python v10_placebo_curva.py
"""
import collections
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
CAL = AQUI.parents[1] / "calib_p2"
PUNTOS = (("1pct", 0.01), ("0.05", 0.05), ("0.10", 0.10), ("0.20", 0.20))


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    tot_al = tot_ne = 0
    for v in ("V1", "V2"):
        print("== ventana %s" % v)
        for tag, frac in PUNTOS:
            f = CAL / ("placebo_%s_%s.jsonl" % (tag, v))
            filas = [json.loads(l) for l in open(f, encoding="utf-8") if l.strip()]
            celdas = corrio = 0
            por = collections.Counter()
            al = ne = neg_neto = 0
            gana_cal = gana_sin = 0
            por_sensor = collections.defaultdict(lambda: [0, 0, 0])   # alertas, negativos, celdas con neto<0
            for x in filas:
                assert "caido" not in x, x
                for k in x:
                    if not k.startswith("P2|"):
                        continue
                    c = x[k]
                    celdas += 1
                    n, neto = c["n"], c["neto"]
                    assert (n + neto) % 2 == 0 and abs(neto) <= n, (k, n, neto)
                    a, b = (n + neto) // 2, (n - neto) // 2
                    al += a; ne += b
                    s = k.split("|")[2]
                    por_sensor[s][0] += a; por_sensor[s][1] += b; por_sensor[s][2] += neto < 0
                    neg_neto += neto < 0
                    if c["falsos_gana"] is not None:
                        corrio += 1
                        por[(k[3:], c["calibrada"])] += 1
                        gana_cal += c["calibrada"] == "GANA"
                    gana_sin += c["sin_calibrar"] == "GANA"
            tot_al += al; tot_ne += ne
            print("  %4.0f %% apagado | apagadas por semilla %s | celdas %d | calibracion corrio %d (%.0f %%) | GANA calibrada %d, GANA sin calibrar %d | "
                  "discordantes: alertas bajo 1 MW apagadas %d, negativos limpios apagados %d (%.1f %% negativos) | celdas con neto < 0: %d" % (
                      100 * frac, sorted({x["apagadas_pedidas"] for x in filas}), celdas, corrio, 100 * corrio / celdas, gana_cal,
                      gana_sin, al, ne, 100 * ne / max(1, al + ne), neg_neto))
            for s, (a, b, nn) in sorted(por_sensor.items()):
                print("        %-9s alertas %4d negativos %3d (%.1f %% negativos) | celdas con neto < 0: %d de %d" % (
                    s, a, b, 100 * b / max(1, a + b), nn, celdas // 2))
            for (k, est), n in sorted(por.items()):
                print("        calibro: %-20s %-12s x%d" % (k, est, n))
    print("== total sobre las 8 curvas: alertas bajo 1 MW apagadas %d, negativos limpios apagados %d (%.1f %% negativos)" % (
        tot_al, tot_ne, 100 * tot_ne / (tot_al + tot_ne)))


if __name__ == "__main__":
    main()
