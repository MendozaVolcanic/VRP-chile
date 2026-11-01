# -*- coding: utf-8 -*-
"""Verificador S159: el control positivo «mitad de camino» de la prueba unitaria según la dispersión de K.
Correr desde la raíz del worktree."""
import sys
sys.path.insert(0, "tests")
import test_evaluar_d25_placebo_s159 as T
X = T.X
for ruido in (0.03, 0.1, 0.2, 0.3):
    P = T._pares(0.6, ruido=ruido)
    for p in P:
        p["d"] = p["k"] * (p["m"] / p["k"]) ** 0.5
    r, det = X.decidir_estrato(P, "decide", "simetrica", True)
    print("dispersion de K %.2f -> final %s | d %s | d' %s IC [%+.4f, %+.4f] volcanes d'<0 %d | nota %s" % (ruido, r, det["regla"], det["regla_dprima"], *det["ic95_dprima"], det["volcanes_con_dprima_negativa"], det["nota"]))
