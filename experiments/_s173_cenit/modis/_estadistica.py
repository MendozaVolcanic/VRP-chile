# -*- coding: utf-8 -*-
# Estadistica comun (copiada tal cual de 01_pasadas_y_salidas_existentes.py; la cargan 02 y 03 con exec)
import math, random, statistics


def rango(v):
    o = sorted(v)
    n = len(o)
    r = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and o[j + 1] == o[i]:
            j += 1
        for k in range(i, j + 1):
            r[k] = (i + j) / 2.0
        i = j + 1
    pos = {}
    for k, x in enumerate(o):
        pos.setdefault(x, []).append(r[k])
    return [statistics.mean(pos[x]) for x in v]


def spearman(a, b):
    if len(a) < 3:
        return None
    ra, rb = rango(a), rango(b)
    ma, mb = statistics.mean(ra), statistics.mean(rb)
    num = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    den = math.sqrt(sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb))
    return num / den if den else None


def con_barajado(z, r, n=200, semilla=173):
    rho = spearman(r, z)
    rng = random.Random(semilla)
    bs = []
    for _ in range(n):
        zz = z[:]
        rng.shuffle(zz)
        s = spearman(r, zz)
        if s is not None:
            bs.append(s)
    bs.sort()
    lo, hi = (bs[int(0.025 * len(bs))], bs[int(0.975 * len(bs)) - 1]) if bs else (None, None)
    return rho, lo, hi


def med(x):
    x = [v for v in x if v is not None]
    return round(statistics.median(x), 3) if x else None


