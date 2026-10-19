# -*- coding: utf-8 -*-
"""¿La mutación xobs_techo (ceil(m1*npos - 1e-9)) puede dar distinto de round(m1*npos)? m1 = x/npos como lo calcula
d_de (una suma de booleanos dividida por el largo). Se prueban todos los pares x <= n < 5000."""
import math
dist = [(x, n) for n in range(1, 5000) for x in range(n + 1) if math.ceil(x / n * n - 1e-9) != round(x / n * n)]
print("pares (x, n) con n < 5000: %d | distintos: %d %s" % (sum(n + 1 for n in range(1, 5000)), len(dist), dist[:5]))
# control positivo: el techo crudo SÍ cambia (7 de 25)
print("control: ceil(7/25*25) = %d, round = %d" % (math.ceil(7 / 25 * 25), round(7 / 25 * 25)))
