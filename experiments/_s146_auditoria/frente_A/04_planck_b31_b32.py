# -*- coding: utf-8 -*-
"""S146 frente A, paso 4: recomputo independiente del cierre D20 (MIROVA_DIVERGENCES.md:2219-2222):
"el corrimiento del NTI entre banda 31 (11,03 um) y banda 32 (12,02 um) va de 0,0001 (250 K) a 0,0054
(290 K)... numericamente despreciable". Planck puro, cuerpo negro isotermo, MIR = 3,959 um.
 1. Si el enunciado fuese falso, fallaria? SI: imprime el corrimiento por temperatura para comparar.
    LIMITE declarado: escena ISOTERMA. Con un pixel sub-pixel caliente el corrimiento puede ser otro;
    se mide tambien ese caso (fraccion f a T_hot sobre fondo T_bg), que el cierre no menciona.
 2. Instrumento muerto? Control: L(11,03 um, 300 K) debe dar ~9,5 W/m2/sr/um (valor de tabla).
"""
import numpy as np
h, c, k = 6.62607015e-34, 2.99792458e8, 1.380649e-23
def L(lam_um, T):
    lam = lam_um * 1e-6
    return 2 * h * c**2 / lam**5 / np.expm1(h * c / (lam * k * T)) * 1e-6
print("control L(11.03um,300K) =", round(float(L(11.03, 300)), 3), "W/m2/sr/um (esperado ~9,5)")
nti = lambda mir, tir: (mir - tir) / (mir + tir)
print("\nescena isoterma:")
for T in (250, 260, 270, 280, 290, 300):
    a, b = nti(L(3.959, T), L(11.03, T)), nti(L(3.959, T), L(12.02, T))
    print(f"  T={T} K  NTI_b31={a:+.4f}  NTI_b32={b:+.4f}  corrimiento={a-b:+.4f}")
print("\npixel mixto (fraccion f a 900 K sobre fondo 270 K), y dNTI contra vecino de fondo puro:")
for f in (1e-4, 1e-3, 1e-2):
    mix = lambda lam: f * L(lam, 900) + (1 - f) * L(lam, 270)
    a, b = nti(mix(3.959), mix(11.03)), nti(mix(3.959), mix(12.02))
    a0, b0 = nti(L(3.959, 270), L(11.03, 270)), nti(L(3.959, 270), L(12.02, 270))
    print(f"  f={f:g}  NTI_b31={a:+.4f}  NTI_b32={b:+.4f}  | dNTI_b31={a-a0:+.5f}  dNTI_b32={b-b0:+.5f}  razon={(b-b0)/(a-a0):.3f}")
