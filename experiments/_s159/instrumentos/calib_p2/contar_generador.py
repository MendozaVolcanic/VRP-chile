# -*- coding: utf-8 -*-
"""Cuenta, en la muestra de cobertura_p2_calibrada.py (semillas 0..n-1), cuántos conjuntos de B5 a B8 tienen TODAS
las noches del mismo lado: la única forma de un falso GANA o PIERDE de la regla en B5 a B7. Si la muestra no es pareja
entre los dos lados, la tasa medida por cola sale inflada de un lado por la muestra, no por la regla.
Uso: python contar_generador.py [n]"""
import sys
import numpy as np

n = int(sys.argv[1]) if len(sys.argv) > 1 else 500
for nombre, B in (("B5", 3), ("B6", 4), ("B7", 5), ("B8", 8)):
    pos = neg = 0
    for s in range(n):
        r = np.random.default_rng(s)
        x = [r.choice((-1, 1)) for _ in range(B)]     # mismo orden de sorteo que el generador del escenario
        pos += all(v == 1 for v in x); neg += all(v == -1 for v in x)
    print("%s (%d noches): todas positivas %d, todas negativas %d, esperado por lado %.1f de %d" % (nombre, B, pos, neg, n / 2 ** B, n))
