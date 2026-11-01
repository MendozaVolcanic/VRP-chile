# -*- coding: utf-8 -*-
"""Verificador D-42, camino propio para la afirmacion 6: el exceso de PIERDE por muestreo en A, B7 y B8,
¿es del generador (las semillas 0..499 de np.random.default_rng dan mas +1 que -1 en los primeros sorteos)?

Pregunta 1: si el generador estuviera sesgado, ¿se ve? Si: la media de los primeros k sorteos de choice((-1,1)) sobre
las semillas 0..499 se aleja de 0 mas de lo que permite el azar (desvio tipico de la media = 1/sqrt(500) = 0,045).
Pregunta 2: si el instrumento estuviera muerto, ¿se ve? Si: con semillas de otro tramo (500..999, 100000..100499) y
con 100.000 semillas la media tiene que volver a 0 si el sesgo es solo de la muestra 0..499.

Reproduce exactamente el orden de sorteo del generador de cobertura_p2_calibrada.py: escenario B (signo comun por
noche): r.choice((-1, 1)) escalar, B veces; escenario A: r.choice((-1, 1), size=3), 12 veces.
"""
import math
import sys

import numpy as np


def escalares(semillas, k):
    """(v2: la primera version creaba un generador nuevo por sorteo y repetia el primero k veces; corregido.)
    Los primeros k sorteos escalares de choice((-1,1)) por semilla (orden de B5..B8)."""
    out = []
    for s in semillas:
        r = np.random.default_rng(s)          # UN generador por semilla, k sorteos seguidos (como el implementador)
        out.append([r.choice((-1, 1)) for _ in range(k)])
    return np.array(out)


def vectores(semillas, k=12, size=3):
    """Los 12 sorteos de size=3 de A por semilla."""
    out = []
    for s in semillas:
        r = np.random.default_rng(s)
        out.append(np.concatenate([r.choice((-1, 1), size=size) for _ in range(k)]))
    return np.array(out)


def informar(nombre, X):
    n = X.shape[0]
    m = X.mean(axis=0)
    z = m / (1 / math.sqrt(n))
    todas_pos = {B: int((X[:, :B] == 1).all(axis=1).sum()) for B in (3, 4, 5, 8) if X.shape[1] >= 8}
    todas_neg = {B: int((X[:, :B] == -1).all(axis=1).sum()) for B in (3, 4, 5, 8) if X.shape[1] >= 8}
    print("%-34s n=%d | media de +1 por posicion (z): %s | media global %.4f (z %.2f)" % (
        nombre, n, " ".join("%.3f(%.1f)" % (a, b) for a, b in zip(m[:8], z[:8])), X.mean(), X.mean() * math.sqrt(X.size)))
    if todas_pos:
        print("      todas +1 / todas -1 en las primeras B: %s / %s | esperado por lado %s" % (
            todas_pos, todas_neg, {B: round(n / 2 ** B, 1) for B in todas_pos}))


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print("== sorteos escalares (como B5..B8), 8 por semilla")
    informar("semillas 0..499 (las del implementador)", escalares(range(500), 8))
    informar("semillas 500..999", escalares(range(500, 1000), 8))
    informar("semillas 100000..100499", escalares(range(100000, 100500), 8))
    informar("semillas 0..99999", escalares(range(100000), 8))
    print("== sorteos vectoriales (como A: 12 x size=3), 36 por semilla")
    XA = vectores(range(500))
    print("semillas 0..499: media global de +1 %.4f (z %.2f) | suma por conjunto: media %.3f, conjuntos con suma>0 %d, <0 %d, =0 %d" % (
        XA.mean(), XA.mean() * math.sqrt(XA.size), XA.sum(axis=1).mean(), (XA.sum(axis=1) > 0).sum(),
        (XA.sum(axis=1) < 0).sum(), (XA.sum(axis=1) == 0).sum()))
    XA2 = vectores(range(100000, 100500))
    print("semillas 100000..100499: media global %.4f (z %.2f) | conjuntos con suma>0 %d, <0 %d, =0 %d" % (
        XA2.mean(), XA2.mean() * math.sqrt(XA2.size), (XA2.sum(axis=1) > 0).sum(), (XA2.sum(axis=1) < 0).sum(),
        (XA2.sum(axis=1) == 0).sum()))
    XA3 = vectores(range(20000))
    print("semillas 0..19999: media global %.4f (z %.2f)" % (XA3.mean(), XA3.mean() * math.sqrt(XA3.size)))


if __name__ == "__main__":
    main()
