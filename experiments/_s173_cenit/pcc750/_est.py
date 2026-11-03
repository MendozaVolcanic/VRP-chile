# -*- coding: utf-8 -*-
"""Estadística compartida de los scripts de esta carpeta (S173, cenit PCC V750).

Copia de las funciones de experiments/_s173_cenit/v750/s02_razon_por_cenit.py (spearman con rangos medios, barajado
del cenit 200 veces con semilla 173, cuartiles), para que el instrumento sea el mismo que en Chillán.
"""
from __future__ import annotations

import math
import random
import statistics


def fl(x):
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def rank(v):
    o = sorted(range(len(v)), key=lambda i: v[i])
    rk = [0.0] * len(v)
    i = 0
    while i < len(o):
        j = i
        while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
            j += 1
        for k in range(i, j + 1):
            rk[o[k]] = (i + j) / 2 + 1
        i = j + 1
    return rk


def spearman(x, y):
    pr_ = [(a, b) for a, b in zip(x, y) if a is not None and b is not None]
    if len(pr_) < 4:
        return None
    a, b = rank([p[0] for p in pr_]), rank([p[1] for p in pr_])
    ma, mb = statistics.mean(a), statistics.mean(b)
    num = sum((p - ma) * (q - mb) for p, q in zip(a, b))
    den = math.sqrt(sum((p - ma) ** 2 for p in a) * sum((q - mb) ** 2 for q in b))
    return num / den if den else None


def barajado(z, r, n=200, semilla=173):
    rng = random.Random(semilla)
    out = []
    for _ in range(n):
        zz = list(z)
        rng.shuffle(zz)
        s = spearman(zz, r)
        if s is not None:
            out.append(s)
    out.sort()
    return (out[int(0.025 * len(out))], out[int(0.975 * len(out)) - 1]) if out else (None, None)


def med(v):
    v = [x for x in v if x is not None]
    return statistics.median(v) if v else None


def q(v):
    v = sorted(x for x in v if x is not None)
    if not v:
        return "sin datos"
    n = len(v)
    return f"{statistics.median(v):.3f} [{v[n // 4]:.3f}, {v[(3 * n) // 4]:.3f}] n={n} rango [{v[0]:.3f}, {v[-1]:.3f}]"


def linea(pr, nombre, pares, corte=30.0):
    """pares: lista de (z, valor). Imprime tramos, cociente de medianas y Spearman con barajado."""
    z = [a for a, _ in pares]
    r = [b for _, b in pares]
    lo = [b for a, b in pares if a < corte]
    hi = [b for a, b in pares if a >= corte]
    sp = spearman(z, r)
    bj = barajado(z, r) if sp is not None else (None, None)
    c = med(hi) / med(lo) if lo and hi and med(lo) else None
    fuera = sp is not None and bj[0] is not None and (sp < bj[0] or sp > bj[1])
    pr(f"{nombre:22s} z<30 {q(lo)} | z>=30 {q(hi)} | med>=30/med<30 " + (f"{c:.3f}" if c is not None else "-")
       + (f" | Spearman {sp:+.3f} barajado [{bj[0]:+.3f}, {bj[1]:+.3f}] {'FUERA' if fuera else 'dentro'}"
          if sp is not None else " | Spearman - (n<4)"))
    return {"n": len(pares), "n_lo": len(lo), "n_hi": len(hi), "med_lo": med(lo), "med_hi": med(hi),
            "cociente": c, "spearman": sp, "barajado": bj, "fuera": fuera}
