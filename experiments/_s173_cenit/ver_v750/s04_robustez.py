# -*- coding: utf-8 -*-
"""s04 (S173, cenit V750): robustez de los brazos clave de s03 a (a) la regla A119 (sólo filas de la tabla CONS
decide; el OCR se informa aparte) y (b) quitar una noche a la vez (12 noches): ¿cambia el signo o la significancia?

P1: si la caída de K dependiera de una sola noche, quitarla la haría desaparecer; se informa el Spearman mínimo y
    máximo de las 12 réplicas. P2: barajado 200, semilla 173 (el de s02).
Razón con ceros, denominador = positivos de s02/s03 (28; 25 con CONS).
Uso: python -B s04_robustez.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from s02_razon_por_cenit import spearman, barajado, med, fl  # noqa: E402

L = []


def pr(*x):
    s = " ".join(str(y) for y in x)
    print(s, flush=True)
    L.append(s)


def r0(x, v):
    v = fl(v)
    return max(v, 0.0) / fl(x["vM"]) if v else 0.0


BRAZOS = {
    "K nativo (pc)": lambda x: r0(x, x["NK_pc"]),
    "F nativo (pc)": lambda x: r0(x, x["NF_pc"]),
    "O grilla": lambda x: r0(x, x["O_vrp"]),
    "X_fanillo_rec": lambda x: r0(x, x["X_fanillo_rec_vrp"]),
    "X_todoK_fcodigo": lambda x: r0(x, x["X_todoK_fcodigo_vrp"]),
    "O_comp": lambda x: r0(x, x["O_comp_vrp"]),
}


def fila(nombre, S, fn):
    z = [fl(x["z"]) for x in S]
    r = [fn(x) for x in S]
    lo = [b for a, b in zip(z, r) if a < 30]
    hi = [b for a, b in zip(z, r) if a >= 30]
    sp = spearman(z, r)
    bj = barajado(z, r)
    pr(f"{nombre:18s} n={len(S)} (<30 {len(lo)}, >=30 {len(hi)}) med<30 {med(lo):.3f} med>=30 {med(hi):.3f} "
       f"Spearman {sp:+.3f} barajado [{bj[0]:+.3f}, {bj[1]:+.3f}] {'FUERA' if sp < bj[0] or sp > bj[1] else 'dentro'}")


def main():
    P = list(csv.DictReader(open(AQUI / "s03_por_pasada.csv", encoding="utf-8")))
    pr("== (a) sólo filas CONS (A119)")
    S = [x for x in P if x["srcM"] == "CONS"]
    for b, fn in BRAZOS.items():
        fila(b, S, fn)
    pr("\n== (b) dejar una noche fuera (12 réplicas): Spearman mínimo y máximo, y cuántas réplicas FUERA del barajado")
    noches = sorted({x["hora_utc"][:10] for x in P})
    pr("noches:", len(noches))
    for b, fn in BRAZOS.items():
        sps, fuera = [], 0
        for n in noches:
            S = [x for x in P if x["hora_utc"][:10] != n]
            z = [fl(x["z"]) for x in S]
            r = [fn(x) for x in S]
            sp = spearman(z, r)
            bj = barajado(z, r)
            sps.append(sp)
            fuera += sp < bj[0] or sp > bj[1]
        pr(f"{b:18s} Spearman [{min(sps):+.3f}, {max(sps):+.3f}] réplicas FUERA {fuera}/{len(noches)}")
    (AQUI / "s04_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
