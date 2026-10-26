# -*- coding: utf-8 -*-
"""Resume placebo_<fraccion>_<V>.jsonl: fracción de semillas con P2 GANA, PIERDE, EMPATE, BLOQUEA, INDECIDIBLE y SIN
SUSTRATO, calibrada y sin calibrar, por regla y sensor, con intervalo de Wilson al 95 %. Criterio del control: P2
calibrada no puede dar GANA en más del 5 % de las semillas (en ningún sensor ni regla).
Después del verificador de D-42 (V42-01): por archivo (punto de la curva) se cuentan las celdas (semilla x regla x
sensor) en que la calibración corrió (falsos_gana no None). El control vale sólo en los puntos donde corrió en la
mayoría de las celdas; en los demás se informa «NO VALE: sin sustrato» y el punto no cuenta ni para cumplir ni para
fallar. Uso: python resumir_placebo.py placebo_1pct_V1.jsonl [placebo_0.05_V1.jsonl ...]"""
import collections
import json
import math
import sys

CAT = ("GANA", "PIERDE", "EMPATE", "BLOQUEA", "INDECIDIBLE", "SIN SUSTRATO")


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    falla, validos, no_validos = [], [], []
    for f in sys.argv[1:]:
        filas = [json.loads(l) for l in open(f, encoding="utf-8") if l.strip()]
        ok = [x for x in filas if "caido" not in x]
        n = len(ok)
        print("== %s: %d semillas, %d caídas | apagadas pedidas %s | apagadas que llegan a la tabla %s | en días excluidos %s"
              % (f, len(filas), len(filas) - n, sorted({x["apagadas_pedidas"] for x in ok}),
                 sorted(x["apagadas_en_tabla"] for x in ok), sorted(x["apagadas_en_dias_excluidos"] for x in ok)))
        print("   estados de la ventana: %s" % dict(collections.Counter(x["estado"].split(" (")[0] for x in ok)))
        claves = sorted({k for x in ok for k in x if k.startswith("P2|")})
        celdas = [(x, k) for x in ok for k in claves]
        corrio = sum(x[k]["falsos_gana"] is not None for x, k in celdas)
        vale = corrio > len(celdas) / 2
        (validos if vale else no_validos).append(f)
        print("   celdas con calibración: %d de %d (%s) | por regla y sensor: %s" % (
            corrio, len(celdas), "VALE: corrió en la mayoría" if vale else "NO VALE: sin sustrato en la mayoría",
            ", ".join("%s %d/%d" % (k[3:], sum(x[k]["falsos_gana"] is not None for x in ok), n) for k in claves)))
        for k in claves:
            for lado in ("calibrada", "sin_calibrar"):
                c = collections.Counter(x[k][lado] for x in ok)
                partes = []
                for cat in CAT:
                    lo, hi = wilson(c[cat], n)
                    partes.append("%s %d/%d (%.0f %% [%.0f, %.0f])" % (cat, c[cat], n, 100 * c[cat] / n, 100 * lo, 100 * hi))
                print("   %-22s %-12s %s" % (k, lado, " | ".join(partes)))
                if lado == "calibrada" and vale and c["GANA"] > 0.05 * n:
                    falla.append("%s %s: GANA en %d de %d semillas" % (f, k, c["GANA"], n))
            netos = [x[k]["neto"] for x in ok]
            print("   %-22s neto D menos K: min %d mediana %s max %d | discordantes mediana %s | noches mediana %s" % (
                k, min(netos), sorted(netos)[n // 2], max(netos), sorted(x[k]["n"] for x in ok)[n // 2],
                sorted(x[k]["noches"] for x in ok)[n // 2]))
    print("\nPUNTOS DONDE EL CONTROL VALE (calibración en la mayoría de las celdas): %s" % (validos or "ninguno"))
    print("PUNTOS QUE NO VALEN (sin sustrato en la mayoría): %s" % (no_validos or "ninguno"))
    print("CRITERIO DEL CONTROL en los puntos que valen (P2 calibrada no da GANA en más del 5 %% de las semillas): %s" % (
        "SIN PUNTOS QUE VALGAN" if not validos else "CUMPLE" if not falla else "NO CUMPLE: " + "; ".join(falla)))


if __name__ == "__main__":
    main()
