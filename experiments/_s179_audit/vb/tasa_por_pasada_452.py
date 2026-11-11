#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verificador VB, S179. Afirmación 452 por otro denominador: la pasada con alerta Muy Bajo, no el día.
Tasa de la calibración C-rad por pasada Muy Bajo: 0,0213 (experiments/_s178_cotas_v375/cotas_v375_con_retro_salida.txt
l. 86, en 438a60a1e). Noviembre: 3 de 36 (ventana 11-03 a 11-09, datos 438a60a1e, re_sim_vigilancia_salida.txt) y
3 de 38 (11-03 a 11-10, datos 16d78e3e0, sim_ventana_16d78_salida.txt).
Pregunta 1 (¿vería algo roto?): control, con k = 0 la cola P(X >= 0) tiene que dar 1. Pregunta 2: se imprime n."""
import math, sys
sys.stdout.reconfigure(encoding="utf-8")
def binom_ge(k, n, p):
    return sum(math.comb(n, i) * p**i * (1 - p)**(n - i) for i in range(k, n + 1))
p0 = 0.0213
print(f"control: P(X >= 0 | n 36) = {binom_ge(0, 36, p0):.3f}")
for k, n, ventana, dias in ((3, 36, "11-03 a 11-09 (438a60a1e)", 7.79), (3, 38, "11-03 a 11-10 (16d78e3e0)", 8.79)):
    print(f"{ventana}: {k} de {n} = {k/n:.4f} por pasada, {k/n/p0:.1f} veces la calibración; "
          f"P(X >= {k} | n {n}, p {p0}) = {binom_ge(k, n, p0):.4f}; por día, proyección a 120 d {k/dias*120:.2f} "
          f"= {k/dias*120/9.48:.2f} veces 9,48")
print("salida 0")
