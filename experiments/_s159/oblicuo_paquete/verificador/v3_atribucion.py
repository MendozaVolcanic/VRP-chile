# -*- coding: utf-8 -*-
"""S159 verificador, paso 3: (a) la atribución F/K y O/F por tramo, ¿es del cenit o de Chillán? (b) el interpolador
lineal se eligió en las mismas 181 alertas (N-2): ¿gana también sólo en <=50°, de modo que >50° quede fuera de muestra?
Pregunta 1: si la tendencia con el cenit fuera composición (Chillán), sin Chillán se aplana; se imprime con y sin.
Pregunta 2: n por celda; n 0 = SIN DATO; n < 5 = SIN PODER.
Denominador: 181 alertas que deciden, VIIRS 750 nocturno, 2026-04-01 a 2026-10-21 sin 18-19 oct (tabla de N).
"""
from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
N = AQUI.parents[1] / "n"
L = []
TR = (("<=25", 0, 25), ("25-40", 25, 40), ("40-50", 40, 50), (">50", 50, 99))


def pr(*x):
    s = " ".join(str(y) for y in x)
    print(s)
    L.append(s)


def q(xs):
    if not xs:
        return "SIN DATO"
    a = np.asarray(xs, float)
    s = " SIN PODER" if len(a) < 5 else ""
    return f"{np.median(a):.3f} [{np.quantile(a, .25):.3f}, {np.quantile(a, .75):.3f}] n={len(a)}{s}"


def main():
    obj = {o["id"]: o for o in json.loads((N / "objetivos_n.json").read_text(encoding="utf-8"))}
    rows = [r for r in csv.DictReader(open(N / "tabla_por_pasada.csv", encoding="utf-8"))]
    pos = [r for r in rows if obj[int(r["id"])]["lab"] == "pos" and obj[int(r["id"])]["decide"]
           and r["estado"] == "ok" and obj[int(r["id"])]["clase"] != "diurna"]
    pr(f"alertas: {len(pos)} (cenit = z de la tabla, que v1 mostró a 0,01° del centro de grilla)")
    f = lambda s: None if s in ("", None) else float(s)
    T = lambda z: next(nm for nm, a, b in TR if (a < z <= b) or (a == 0 and z <= b))

    pr("\n== (a) F/K y O/F por tramo, con y sin Chillán (pares con ambos > 0; O 'publica' = columna O_pub de N)")
    for etq, sel in (("todas", lambda r: True), ("sin Chillán", lambda r: r["volcan"] != "NevadosDeChillan")):
        for nom, cond, val in (
                ("F/K", lambda r: r["K_pub"] == "True" and r["F_pub"] == "True" and f(r["K_pc"]) > 0,
                 lambda r: f(r["F_pc"]) / f(r["K_pc"])),
                ("O/F", lambda r: r["F_pub"] == "True" and r["O_pub"] == "True" and f(r["F_pc"]) > 0,
                 lambda r: f(r["O_geo_linear_vrp"]) / f(r["F_pc"]))):
            pr(f"   {etq:11s} {nom}: " + " | ".join(
                f"{nm} {q([val(r) for r in pos if sel(r) and cond(r) and T(f(r['z'])) == nm])}" for nm, _, _ in TR))

    pr("\n== (b) interpolador: razón O/MIROVA por variante, sólo donde la variante tiene VRP > 0 (sin el filtro de"
       " inner; es para comparar variantes, no la cifra del informe)")
    for var in ("geo_linear", "geo_nearest", "geo_cubic", "r2_linear"):
        out = []
        for etq, s in (("<=50", lambda z: z <= 50), (">50", lambda z: z > 50)):
            xs = [f(r[f"O_{var}_vrp"]) / f(r["mirova_vrp"]) for r in pos
                  if s(f(r["z"])) and f(r[f"O_{var}_vrp"]) and f(r[f"O_{var}_vrp"]) > 0]
            a = np.asarray(xs)
            out.append(f"{etq}: {q(xs)}; en [0,9;1,1] {int(((a >= .9) & (a <= 1.1)).sum())}/{len(a)}")
        pr(f"   {var:12s} " + " | ".join(out))
    (AQUI / "v3_atribucion_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
