"""C3: nulo del disparador (i). Si la pérdida diferencial verdadera de K en cada volcán es IGUAL a la del A/B
(V1, 16/194 = 0,0825) o la observada en el retrospectivo (3/67), ¿con qué probabilidad la vigilancia diaria
dispara INVESTIGAR por (i) en algún volcán antes de los 120 días? Tasa de pasadas Muy Bajo V375 por volcán y día
tomada del retrospectivo (muy_bajo_retro.out, 16 noches de sombra: 2026-10-02 a 2026-10-17).
Uso: python sim_falsa_alarma_i.py"""
import math
import random

N_RETRO = {"Chaiten": 6, "Isluga": 21, "Lascar": 7, "Lastarria": 3, "NevadosDeChillan": 9,
           "PlanchonPeteroa": 8, "PuyehueCordonCaulle": 9, "Tupungatito": 4}
NOCHES_RETRO = 16
COTA = 0.1298   # max(Wilson sup V1 16/194, V2 26/388)


def wilson_lo(k, n, z=1.96):
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return c - m


def una(p, rng, dias=120):
    k = {v: 0 for v in N_RETRO}
    n = {v: 0 for v in N_RETRO}
    for _ in range(dias):
        for v, nr in N_RETRO.items():
            lam = nr / NOCHES_RETRO
            # Poisson por día
            m, L, pr = 0, math.exp(-lam), 1.0
            while True:
                pr *= rng.random()
                if pr < L:
                    break
                m += 1
            for _ in range(m):
                n[v] += 1
                k[v] += rng.random() < p
            if n[v] and wilson_lo(k[v], n[v]) > COTA:
                return True
    return False


rng = random.Random(156)
for p in (3 / 67, 16 / 194, 0.10):
    reps = 2000
    print(f"p={p:.4f}: P(dispara (i) en 120 dias) = {sum(una(p, rng) for _ in range(reps)) / reps:.3f} (reps {reps})")
