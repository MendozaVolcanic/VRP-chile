"""C3/(iii): nulo del disparador de negativos limpios VIIRS 375. Con la tasa real de K en el retrospectivo
(SN: 21/611 = 0,0344; original: 12/580 = 0,0207, negativos_sn.out) y ~20 negativos por noche (611 en 30 noches),
P(INVESTIGAR por (iii) en algun dia de 120) con evaluacion diaria acumulada. Cota 0,0501.
Uso: python sim_falsa_alarma_iii.py"""
import math
import random


def wilson_lo(k, n, z=1.96):
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return c - m


rng = random.Random(156)
for p in (21 / 611, 12 / 580):
    hits, reps = 0, 2000
    for _ in range(reps):
        k = n = 0
        for _ in range(120):
            for _ in range(20):
                n += 1
                k += rng.random() < p
            if wilson_lo(k, n) > 0.0501:
                hits += 1
                break
    print(f"p={p:.4f}: P(dispara (iii) en 120 dias) = {hits / reps:.3f}")
