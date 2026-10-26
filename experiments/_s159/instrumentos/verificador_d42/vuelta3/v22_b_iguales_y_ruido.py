# -*- coding: utf-8 -*-
"""Verificador D-42, vuelta 3: (1) tasa EXACTA por cola de la regla de D-34 (intervalo bootstrap por bloques, W real)
bajo el nulo de signos por bloque con B noches IGUALES de una contribucion, B = 5..12 (enumeracion de los 2^B signos),
para ver en que B la regla queda sobre el tope del 5 %; (2) con 1.000 sorteos, probabilidad de que la calibracion
FALLE por ruido de muestreo cuando la tasa verdadera por cola es p (binomial: falla si alguna de las dos colas pasa de
50 de 1.000). Reusa exacto() de v21."""
import math
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from v21_noches_desiguales import exacto  # noqa: E402


def p_falla(p, n=1000, tope=50):
    """P(una cola > tope) con Binomial(n, p); las dos colas se tratan como independientes (aproximacion)."""
    q = sum(math.comb(n, k) * p ** k * (1 - p) ** (n - k) for k in range(0, tope + 1))
    return 1 - q * q


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    for B in range(5, 13):
        tot, cuenta, p1, p2 = exacto([1] * B)
        pe = cuenta["PIERDE"] / tot
        print("B=%2d noches iguales: exacto PIERDE %.4f (%d de %d) GANA %.4f | valor-p signos una cola %.4f | con 1.000 sorteos, P(calibracion falla) = %.2f" % (
            B, pe, cuenta["PIERDE"], tot, cuenta["GANA"] / tot, p1, p_falla(pe)), flush=True)
    for p in (0.0459, 0.0547, 0.0625, 0.040, 0.030):
        print("tasa verdadera por cola %.4f: P(falla con 1.000 sorteos) = %.2f" % (p, p_falla(p)))
