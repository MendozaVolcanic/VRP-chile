# -*- coding: utf-8 -*-
"""S146 B: D20 "despreciable". La cuantificacion S128 comparo el corrimiento de NTI (b31 vs b32) con el margen a K1 (~0,14).
Aqui se compara con lo que S136 dice que gobierna MODIS: el piso C1 = 0,003 del dNTI. Pixel isotermo a T+dT contra vecinos a T.
1. Si lo medido estuviera roto (corrimiento independiente de T), el dNTI diferencial daria 0 en todas las filas: se veria.
2. Instrumento muerto: control NTI(b31)-NTI(b32) a 250 K y 290 K debe reproducir ~0,0001 y ~0,0054 de S128; si no, el script no mide lo mismo.
Solo Planck, sin datos. No prueba nada sobre escenas reales (sub-pixel, emisividad): es una cota de orden de magnitud."""
import math
C1, C2 = 1.191042e8, 14387.75
def L(lam, T): return C1 / (lam**5 * (math.exp(C2/(lam*T)) - 1))
def nti(T, tir): return (L(3.959, T) - L(tir, T)) / (L(3.959, T) + L(tir, T))
print("control S128: NTI31-NTI32 a 250 K = %.4f ; a 290 K = %.4f" % (nti(250,11.03)-nti(250,12.02), nti(290,11.03)-nti(290,12.02)))
print("T_vecinos  dT   dNTI_b31   dNTI_b32   diferencia   diferencia/C1(0.003)")
for T in (260, 270, 280):
    for dT in (3, 5, 10, 15):
        a = nti(T+dT, 11.03) - nti(T, 11.03); b = nti(T+dT, 12.02) - nti(T, 12.02)
        print(f"{T:9d} {dT:4d} {a:10.5f} {b:10.5f} {a-b:11.5f} {(a-b)/0.003:10.2f}")
