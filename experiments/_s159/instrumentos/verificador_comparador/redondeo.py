# -*- coding: utf-8 -*-
"""Verificador S159: ¿el redondeo de d′ a 1e-12 (DEC_DPRIMA) es necesario? Cambia el global en memoria, no el archivo.
Correr desde la raíz del worktree: python experiments/_s159/instrumentos/verificador_comparador/redondeo.py"""
import sys, json
sys.path.insert(0, "tests"); sys.path.insert(0, "experiments/_s157_prereg_d25")
import test_evaluar_d25_placebo_s159 as T
X = T.X
D = json.load(open("experiments/_s159/instrumentos/verificador_comparador/pares_k.json", encoding="utf-8"))
for dec in (12, 30):
    X.DEC_DPRIMA = dec
    for razon, g in ((0.6, 1.2), (1.6, 0.8)):
        r, det = X.decidir_estrato(T._con_ganancia(T._pares(razon, ruido=0.3), g), "decide", "simetrica", True)
        print("DEC %d sintético razon %.1f g %.1f -> final %s | d %s | d' %s IC %s max|d'| %r" % (dec, razon, g, r, det["regla"], det["regla_dprima"], det["ic95_dprima"], det["dprima_max_abs"]))
    for w in ("V1", "V2"):
        for nom in ("VIIRS750|z<=40", "VIIRS375|sin_kernel|z<=40"):
            r, det = X.decidir_estrato([dict(p, d=p["k"] * 1.2) for p in D[w][nom]], "decide", "simetrica", True)
            print("DEC %d real %s %s x1.2 -> final %s | d' %s IC %s max|d'| %r" % (dec, w, nom, r, det["regla_dprima"], det["ic95_dprima"], det["dprima_max_abs"]))
