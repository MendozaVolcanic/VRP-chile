# -*- coding: utf-8 -*-
"""Verificador: miniaturas de MIROVA. (a) duplicados de imagen entre pasadas; (b) px blancos vs M y f;
(c) el tamaño del bloque de pixeles del mapa (rejilla visible) crece con el angulo aunque no haya foco."""
import io, json, math, sys, hashlib, statistics as st
from pathlib import Path
import numpy as np
from PIL import Image
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
PNG = Path("D:/vrp-trabajo/temporales/s157_magnitud/png")
X0 = [15, 180, 345, 510, 675]; Y0 = [165, 400]; L = 150
def minis(n):
    a = np.asarray(Image.open(PNG / n).convert("RGB")).astype(int)
    return [a[y:y + L, x:x + L] for y in Y0 for x in X0]
A = minis("20261018_093004_VIIRS375_Latest10NTI.png")
B = minis("20261018_082654_VIIRS375_Latest10NTI.png")
C = minis("20261018_091701_VIIRS750_Latest10NTI.png")
D = minis("20261018_080827_VIIRS750_Latest10NTI.png")
# (a) 18-oct 05:42 375 (A[2]) contra 17-oct 05:24 375 (B[8]) y contra todas
def dif(u, v):
    return float(np.abs(u - v).mean())
print("A[2] (375 18-oct 05:42) vs B[8] (375 17-oct 05:24) dif media", dif(A[2], B[8]))
for i, m in enumerate(B):
    print("  A[2] vs B[%d] %.1f" % (i, dif(A[2], m)))
print("control A[1] (06:00) vs B[0] (06:00) =", dif(A[1], B[0]))
# 375 vs 750 misma pasada
print("A[0] 375 06:48 vs C[0] 750 06:48", dif(A[0], C[0]))
# (c) tamaño de bloque: longitud media de corridas horizontales de valor identico en la mitad de la miniatura (sin foco)
def corrida(m):
    g = m.sum(axis=2)[10:140, 10:140]
    runs = []
    for row in g:
        n = 1
        for a, b in zip(row[:-1], row[1:]):
            if a == b:
                n += 1
            else:
                runs.append(n); n = 1
        runs.append(n)
    return st.mean(runs)
lab375 = ["06:48 z67", "06:00 z22", "05:42 z20", "05:06 z48", "x", "x", "x", "x", "17 06:18 z45", "17 06:00 z10"]
for i, m in enumerate(A):
    print("375 %s corrida media %.2f  blancos(41x41) %d" % (lab375[i], corrida(m), int((m.sum(axis=2)[55:96, 55:96] >= 765).sum())))
lab750 = lab375
for i, m in enumerate(C):
    print("750 %s corrida media %.2f  blancos(41x41) %d" % (lab750[i], corrida(m), int((m.sum(axis=2)[55:96, 55:96] >= 765).sum())))
labB = ["18 06:00 z22", "18 05:06 z48", "x", "x", "x", "17:42 dia", "17 06:18 z45", "17 06:00 z10", "17 05:24 z27", "17 04:42 z68"]
for i, m in enumerate(B):
    print("375B %s corrida media %.2f  blancos %d" % (labB[i], corrida(m), int((m.sum(axis=2)[55:96, 55:96] >= 765).sum())))
for i, m in enumerate(D):
    print("750D %s corrida media %.2f  blancos %d" % (labB[i] if i != 0 else "18 05:42 z20", corrida(m), int((m.sum(axis=2)[55:96, 55:96] >= 765).sum())))
# (b) regresion px ~ M y f en las 5 de >=9 MW (375)
rows = [(3, 9.94, 1.24), (2, 11.03, 1.40), (2, 11.36, 1.75), (7, 21.25, 2.02), (19, 25.79, 3.73)]
y = [math.log(r[0]) for r in rows]; m = [math.log(r[1]) for r in rows]; f = [math.log(r[2]) for r in rows]
def corr(a, b):
    ma, mb = st.mean(a), st.mean(b)
    return sum((x - ma) * (z - mb) for x, z in zip(a, b)) / math.sqrt(sum((x - ma) ** 2 for x in a) * sum((z - mb) ** 2 for z in b))
print("375 >=9MW: corr(log px, log M) %.2f  corr(log px, log f) %.2f  corr(log M, log f) %.2f" % (corr(y, m), corr(y, f), corr(m, f)))
rows7 = [(24, 20.87, 1.20), (12, 18.98, 1.24), (20, 21.94, 1.75), (20, 19.63, 2.02), (46, 22.85, 3.72)]
y = [math.log(r[0]) for r in rows7]; m = [math.log(r[1]) for r in rows7]; f = [math.log(r[2]) for r in rows7]
print("750 >=9MW: corr(log px, log M) %.2f  corr(log px, log f) %.2f  corr(log M, log f) %.2f" % (corr(y, m), corr(y, f), corr(m, f)))
