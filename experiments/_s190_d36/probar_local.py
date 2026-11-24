# -*- coding: utf-8 -*-
# FICHA (SDA, CPLT 372): prueba de los controles del A/B de D36 punto 1. Sin red, sin pyhdf.
"""Corre en Windows y en el runner antes del A/B. Sale con 1 si un control falla.
  C1  con los números de la vía, detectar_param da la misma máscara que MV.detectar_mirova (40 escenas al azar,
      noche y día, semilla 190): el control que se cancela por construcción (A110).
  C2  el instrumento puede dar distinto de cero (A116): en una escena con una celda tibia en la zona conservadora
      (contraste de NTI entre 0,01 y 0,02), B2 la alerta y A no; y en una con NTI entre -0,8 y -0,7 en la zona 0,
      B1 la alerta y A no.
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np  # noqa: E402

from pipeline import mirova_v750_codigo as MV  # noqa: E402
import brazos as BR  # noqa: E402

LMIR, LTIR = MV.LAMBDA_MODIS_B22, MV.LAMBDA_MODIS_B31
N = 51
box = MV.caja_roi("def", n=N, lado_sensible=5, lado_anillo=15, paso_m=1000.0)
fallas = 0


def escena(rng, t_bg=265.0, ruido=0.4):
    tt = t_bg + rng.normal(0, ruido, (N, N))
    t11 = tt - 2 + rng.normal(0, 0.3, (N, N))
    return MV.temperatura_a_radiancia(tt, LMIR), MV.temperatura_a_radiancia(t11, LTIR)


rng = np.random.default_rng(190)
iguales = 0
for i in range(40):
    m13, m15 = escena(rng)
    if i % 3 == 0:   # un foco caliente para que haya alertas
        f, k = rng.integers(5, N - 5, 2)
        m13[f, k] *= rng.uniform(1.5, 20)
    day = int(i % 4 == 0)
    a = MV.detectar_mirova(m13, m15, box, day, 90.0, lam_mir=LMIR, lam_tir=LTIR)
    b = BR.detectar_param(m13, m15, box, day, 90.0, lam_mir=LMIR, lam_tir=LTIR)
    iguales += bool(np.array_equal(a, b))
print(f"C1 copia == produccion: {iguales} de 40")
fallas += iguales != 40


def nti_de(m13, m15):
    return (m13 - m15) / (m13 + m15)


# C2a: celda tibia en zona 1 (anillo conservador): sube su NTI hasta un contraste ~0,015
m13, m15 = escena(np.random.default_rng(7), ruido=0.05)
f, k = 25, 31          # zona 1 (fuera del 5 x 5, dentro del 15 x 15)
assert box[f, k] == 1
nti0 = nti_de(m13[f, k], m15[f, k])
objetivo = nti0 + 0.0168 * 9 / 8
r = (1 + objetivo) / (1 - objetivo)
m13[f, k] = r * m15[f, k]
mA = BR.detectar_param(m13, m15, box, 0, 90.0, lam_mir=LMIR, lam_tir=LTIR, u_abs_noche=-0.7, n1_noche=0.02)
mB2 = BR.detectar_param(m13, m15, box, 0, 90.0, lam_mir=LMIR, lam_tir=LTIR, u_abs_noche=-0.7, n1_noche=0.01)
print(f"C2a celda tibia zona 1: A {bool(mA[f, k])}, B2 {bool(mB2[f, k])}")
fallas += not (mB2[f, k] and not mA[f, k])

# C2b: NTI absoluto -0,75 en zona 0 con fondo tibio parecido (contraste chico, sólo el Test 1 la ve)
m13, m15 = escena(np.random.default_rng(8), t_bg=300.0, ruido=0.05)
f, k = 5, 5
assert box[f, k] == 0
r = (1 - 0.75) / (1 + 0.75)
m13[f, k] = r * m15[f, k]
for df in (-1, 0, 1):
    for dk in (-1, 0, 1):
        if df or dk:
            m13[f + df, k + dk] = (1 - 0.755) / (1 + 0.755) * m15[f + df, k + dk]
mA = BR.detectar_param(m13, m15, box, 0, 90.0, lam_mir=LMIR, lam_tir=LTIR, u_abs_noche=-0.7, n1_noche=0.02)
mB1 = BR.detectar_param(m13, m15, box, 0, 90.0, lam_mir=LMIR, lam_tir=LTIR, u_abs_noche=-0.8, n1_noche=0.02)
print(f"C2b NTI -0,75 en zona 0: A {bool(mA[f, k])}, B1 {bool(mB1[f, k])}")
fallas += not (mB1[f, k] and not mA[f, k])
print("FALLAS", fallas)
sys.exit(1 if fallas else 0)
