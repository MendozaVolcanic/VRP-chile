# Tarea 1.23: presupuesto de tiempo por job MEDIDO, no supuesto (A15).
# La 1.17 (2 brazos) y la 1.21 (6 brazos) corrieron los MISMOS granulos en los mismos 12 jobs. Por job,
# la diferencia de duracion dividida por 4 brazos extra y por la cantidad de granulos da el costo de un
# brazo por granulo (a); lo que queda de la 1.17 es la bajada y la lectura por granulo (d). Con eso se
# predice un job de la 1.23 (2 + K brazos) partido en dos mitades.
#
# Uso: python presupuesto_tiempo.py <artefactos 1.17> <artefactos 1.21> [--k 20] [--salida x.txt]
import argparse
import io
import json
import math
import sys
from pathlib import Path


def duraciones(carpeta):
    out = {}
    for p in sorted(Path(carpeta).rglob("*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(d, dict) and "granulos" in d and "job" in d and d.get("minutos") is not None:
            out[d["job"]] = (float(d["minutos"]), sum(1 for g in d["granulos"] if g.get("estado") == "ok"))
    return out


def ajustar(t117, t121, brazos117=2, brazos121=6):
    filas = {}
    for j in sorted(set(t117) & set(t121)):
        (m17, n), (m21, n21) = t117[j], t121[j]
        n = max(n, n21, 1)
        a = max((m21 - m17) / (n * (brazos121 - brazos117)), 0.0)
        d = max(m17 / n - brazos117 * a, 0.0)
        filas[j] = {"n": n, "min_117": m17, "min_121": m21, "a_min_por_brazo_granulo": round(a, 4),
                    "d_min_por_granulo": round(d, 4)}
    return filas


def predecir(filas, k, partes=2):
    brazos = 2 + k
    a_max = max(f["a_min_por_brazo_granulo"] for f in filas.values())
    d_max = max(f["d_min_por_granulo"] for f in filas.values())
    pred = {}
    for j, f in filas.items():
        n = math.ceil(f["n"] / partes)
        pred[j] = {"granulos_por_parte": n,
                   "min_propio": round(n * (f["d_min_por_granulo"] + brazos * f["a_min_por_brazo_granulo"]), 1),
                   "min_peor_caso": round(n * (d_max + brazos * a_max), 1)}
    return pred, a_max, d_max


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("art117")
    ap.add_argument("art121")
    ap.add_argument("--k", type=int, default=20)
    ap.add_argument("--salida", default=None)
    a = ap.parse_args()
    filas = ajustar(duraciones(a.art117), duraciones(a.art121))
    buf = io.StringIO()
    p = lambda *x: print(*x, file=buf)  # noqa: E731
    p("Costo medido por job (1.17 con 2 brazos contra 1.21 con 6, mismos granulos)")
    for j, f in filas.items():
        p("  %-20s n=%2d  1.17 %5.1f min  1.21 %5.1f min  a=%.4f min/brazo/granulo  d=%.4f min/granulo" % (
            j, f["n"], f["min_117"], f["min_121"], f["a_min_por_brazo_granulo"], f["d_min_por_granulo"]))
    for partes in (1, 2):
        pred, a_max, d_max = predecir(filas, a.k, partes)
        p("\nPrediccion con %d brazos (C, M y %d nulos), jobs partidos en %d (peor caso: a=%.4f y d=%.4f de "
          "jobs distintos)" % (2 + a.k, a.k, partes, a_max, d_max))
        for j, x in pred.items():
            p("  %-20s %2d granulos  propio %5.1f min  peor caso %5.1f min" % (
                j, x["granulos_por_parte"], x["min_propio"], x["min_peor_caso"]))
        p("  maximo propio %.1f min, maximo peor caso %.1f min, suma propia %.1f min" % (
            max(x["min_propio"] for x in pred.values()), max(x["min_peor_caso"] for x in pred.values()),
            partes * sum(x["min_propio"] for x in pred.values())))
    sys.stdout.write(buf.getvalue())
    if a.salida:
        Path(a.salida).write_text(buf.getvalue(), encoding="utf-8")


if __name__ == "__main__":
    main()
