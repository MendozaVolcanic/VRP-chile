# -*- coding: utf-8 -*-
"""S139: la Ec. 2 de Coppola et al. 2025 (Fernandina, Remote Sens. 17, 1191, p. 9)
da el coeficiente de Wooster en FORMA CERRADA como funcion de la longitud de onda
central de la banda MIR:

    alpha = -8.6344e-10 * lambda + 6.3796e-9       (lambda en um)
    VRP   = dL_MIR * (sigma * eps) / (alpha * eps_MIR) * A_pix     (Ec. 1)

con eps = eps_MIR = 1, el factor es sigma / alpha, que es el "WOOSTER_COEFF" del
proyecto. Este script lo evalua para los tres sensores y lo compara contra los
valores empiricos calibrados en S14 contra MIROVA OSF v2.5.

Instrumento: (1) si la formula estuviera mal transcrita, los tres numeros caerian
fuera de rango (el coeficiente de Wooster vive en 17-21); (2) si el script estuviera
muerto, no imprimiria los ratios. Un acuerdo de 2 de 3 a la cuarta cifra no es
casualidad numerica.
"""
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

SIGMA = 5.67e-8


def alpha(lam_um):
    return -8.6344e-10 * lam_um + 6.3796e-9


# lambda: longitud de onda central de la banda MIR (Tabla 1 del mismo paper, p. 5)
CASOS = [
    ("MODIS B21/B22", 3.959, 18.9),
    ("VIIRS M13 (750 m)", 4.05, 19.7),
    ("VIIRS I4 (375 m)", 3.74, 18.0),
]

print("banda                 lambda(um)   alpha         sigma/alpha   proyecto   ratio")
for nombre, lam, nuestro in CASOS:
    a = alpha(lam)
    k = SIGMA / a
    print(
        "%-20s  %8.4f   %.6e   %10.4f   %8.2f   %7.4f"
        % (nombre, lam, a, k, nuestro, k / nuestro)
    )

# Rango de la banda MIR de MODIS segun la Tabla 1 del paper: 3.929-3.989 um
for lam in (3.929, 3.989):
    print("MODIS extremo %.3f um -> sigma/alpha = %.4f" % (lam, SIGMA / alpha(lam)))
