#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verificador VB, auditoría S179. Afirmación 453 y DEC-6: ¿cuánto pesa la incertidumbre de la tasa en la falsa alarma
de las cuatro cotas selladas de VIIRS? El auditor usó un solo modelo (Jeffreys, Gamma(k + 0,5)). Aquí, otro camino:
(1) la misma pregunta con tres distribuciones de la tasa (Gamma(k), Gamma(k + 0,5), Gamma(k + 1)); (2) un camino sin
prior: la falsa alarma si la tasa verdadera fuera el límite superior unilateral de 80 % de Garwood; (3) para los
estratos de un solo sumando, la predictiva exacta (binomial negativa), para controlar el Monte Carlo.

Constantes de la calibración, leídas de las salidas selladas en 438a60a1e (no del auditor):
- experiments/_s178_cotas_v375/cotas_v375_con_retro_salida.txt l. 8 y 9 (O: 2 crudos, ponderado 9,8, denominador
  ponderado 464,5; 5 crudos, ponderado 10,5, denominador 2062,7) y l. 51 (F26-V radiante: 3 de 139; 5 de 528); l. 84 y
  85 (C-rad: lambda 9,48 y 11,82; cotas 14 y 17).
- experiments/_s176_v375e_adopcion/cotas_retrospectiva_v750_salida.txt (sin Suomi NPP: 9 de 90 y 1 de 3218 en 143 días;
  lambda 7,55 y 0,84; cotas 12 y 2).

Las dos preguntas del instrumento.
1. Si lo medido estuviera roto, ¿lo vería? Control: con la tasa puntual, mi Poisson tiene que devolver la falsa alarma
   que publica la regla (0,059; 0,056; 0,045; 0,053). Control positivo del Monte Carlo: en el estrato de un sumando,
   el MC tiene que coincidir con la binomial negativa exacta a 0,005.
2. Si el instrumento estuviera muerto, ¿se vería distinto? Un MC que no sorteara daría la falsa alarma puntual en las
   tres columnas; se imprime la puntual al lado para verlo.
"""
import math
import random
import sys

sys.stdout.reconfigure(encoding="utf-8")
random.seed(20261111)
N = 100000


def sf(k, lam):
    """P(X > k), X ~ Poisson(lam)."""
    if lam <= 0:
        return 0.0
    acc, term = 0.0, math.exp(-lam)
    for i in range(k + 1):
        acc += term
        term *= lam / (i + 1)
    return max(0.0, 1.0 - acc)


def garwood_sup(k, conf=0.80):
    """Límite superior unilateral de la media de Poisson con k eventos: P(X <= k | lam) = 1 - conf."""
    a = 1.0 - conf
    lo, hi = float(k), float(k) * 6 + 20
    for _ in range(200):
        m = (lo + hi) / 2
        if 1.0 - sf(k, m) > a:
            lo = m
        else:
            hi = m
    return (lo + hi) / 2


def nb_sf(c, a, escala):
    """P(X > c) con X | lam ~ Poisson(lam), lam ~ Gamma(a, escala): binomial negativa con p = 1 / (1 + escala)."""
    p = 1.0 / (1.0 + escala)
    acc = 0.0
    for x in range(c + 1):
        acc += math.exp(math.lgamma(x + a) - math.lgamma(a) - math.lgamma(x + 1) + a * math.log(p) + x * math.log(1 - p))
    return 1.0 - acc


# (nombre, cota, lambda de la regla, función de la tasa a 120 días dada una función g(k) que da el conteo «verdadero»)
CASOS = [
    ("VIIRS 375 (i) Muy Bajo, cota 14", 14, 9.48,
     lambda g: ((9.8 / 2) * g(2) + g(3)) / (464.5 + 139) * 464.5 * 120 / 125, None),
    ("VIIRS 375 (ii) sobre-publicación, cota 17", 17, 11.82,
     lambda g: ((10.5 / 5) * g(5) + g(5)) / (2062.7 + 528) * 2062.7 * 120 / 125, None),
    ("VIIRS 750 (i) Muy Bajo, cota 12", 12, 7.55, lambda g: g(9) * 120 / 143, (9, 120 / 143)),
    ("VIIRS 750 (ii) sobre-publicación, cota 2", 2, 0.84, lambda g: g(1) * 120 / 143, (1, 120 / 143)),
]

print("Falsa alarma de cada cota en 120 días, según cómo se trate la incertidumbre de la tasa")
print("columnas: puntual (la regla) | Gamma(k) | Gamma(k+0,5) Jeffreys | Gamma(k+1) | tasa = sup. 80 % de Garwood")
for nombre, cota, lam_regla, f, simple in CASOS:
    lam_pt = f(lambda k: float(k))
    fila = [sf(cota, lam_pt)]
    for extra in (0.0, 0.5, 1.0):
        vals = [sf(cota, f(lambda k: random.gammavariate(k + extra, 1.0))) for _ in range(N)]
        fila.append(sum(vals) / N)
    lam_sup = f(lambda k: garwood_sup(k))
    fila.append(sf(cota, lam_sup))
    print(f"  {nombre}: lambda regla {lam_regla}, mía {lam_pt:.2f} | " + " | ".join(f"{x:.3f}" for x in fila)
          + f"   (lambda sup. 80 % = {lam_sup:.2f})")
    if simple:
        k, esc = simple
        exactos = [nb_sf(cota, k + e, esc) for e in (0.0, 0.5, 1.0)]
        print("      control binomial negativa exacta (Gamma(k), Jeffreys, Gamma(k+1)): "
              + ", ".join(f"{x:.3f}" for x in exactos))
print("\nsalida 0")
