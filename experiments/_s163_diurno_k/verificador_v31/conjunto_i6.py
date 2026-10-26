# Probabilidad de que I6 (placebo c) falle por azar, con las tasas GANA/PIERDE medidas por el verificador v3 (400 semillas).
import numpy as np
rng = np.random.default_rng(1)
filas = {"q.05 V375": (21, 10), "q.05 V750": (18, 15), "q.20 V375": (16, 13), "q.20 V750": (14, 19),
         "q.50 V375": (17, 14), "q.50 V750": (18, 15)}
for k, (g, p) in filas.items():
    pg, pp = g / 400, p / 400
    N = 200000
    X = rng.multinomial(40, [pg, pp, 1 - pg - pp], size=N)
    G, P = X[:, 0], X[:, 1]
    v3 = ((G + P) > 7).mean()
    v31 = (((G + P) > 7) | (G > 4)).mean()
    sol = (G > 4).mean()
    print("%s pg=%.4f pp=%.4f | falla v3 %.4f | falla v3.1 %.4f | solo tope GANA %.4f" % (k, pg, pp, v3, v31, sol))
