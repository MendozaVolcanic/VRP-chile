# Probabilidad de ADOPTAR (caso b, e-ii) para un brazo que publica AL AZAR con tasa q chica (la grilla del nulo empieza en 0,5 %).
# Estructura de W2..W6 (sustrato_k_salida.txt): V375 neg 2246, mb 10 (en 10 bloques), prot 26; V750 neg 2433, mb 0, prot 6.
import numpy as np
from scipy.stats import binom
rng = np.random.default_rng(1)
def sim(neg, mb, prot, q, reps=200000):
    nn = rng.binomial(neg, q, reps); m = rng.binomial(mb, q, reps); p = rng.binomial(prot, q, reps)
    neto = nn - m
    n_alert = mb + prot; x = m + p
    # D: binom.sf(x-1, n_alert, qd) < .05 con qd = nn/neg ; qd=0 y x>=1 cumple
    qd = nn / neg
    D = np.where(x <= 0, False, np.where(qd <= 0, True, binom.sf(x - 1, n_alert, np.clip(qd, 1e-12, 1)) < 0.05))
    b = (neto <= 0) & (p >= 1) & D
    return b.mean()
for nombre, (neg, mb, prot) in {"V375": (2246, 10, 26), "V750": (2433, 0, 6)}.items():
    print(nombre, " ".join("q=%.4f:%.4f" % (q, sim(neg, mb, prot, q)) for q in (0.0001, 0.0002, 0.0005, 0.001, 0.002, 0.005)))
