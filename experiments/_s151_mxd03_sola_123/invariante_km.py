# Tarea 1.23 (arreglo del bloqueante 1 del verificador): en que unidad el nulo tiene "el mismo tamano"
# que MxD03, medido y no razonado (A110).
#
# POR QUE. Todo lo que el pipeline MODIS hace con la lat/lon pasa por distancias en km al crater: el inner,
# el ROI de 25 km, el disco de 3 km y el anillo de 1 km del Test 1. Trasladar la grilla cambia cuantos
# CENTROS de pixel caen dentro de cada circulo, y eso es lo que mueve la deteccion. Para un circulo grande
# frente al pixel, el area barrida por el borde al trasladar d km es ~4 R d, igual en cualquier direccion:
# el invariante seria el km, no el pixel. Aca se cuenta, sobre grillas sinteticas con pixeles de 1 x 2 km
# (el borde del barrido) y con el diente de sierra del bow tie, cuantos centros cambian de lado de cada
# circulo al trasladar la grilla en 36 rumbos, con el tamano fijo en km o fijo en pixeles.
#
# Uso: python invariante_km.py [--salida x.txt]
import argparse
import io
import math
import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

import probar_probe_sola as T  # noqa: E402  (grilla en diente de sierra)

N = 121


def grilla(paso_lin, paso_frame, sierra=None):
    k = N // 2
    if sierra is None:
        y = paso_lin * (np.arange(N) - k)
    else:
        y = T.lineas_bowtie(N, sierra) - T.lineas_bowtie(N, sierra)[k]
    x = paso_frame * (np.arange(N) - k)
    return np.meshgrid(-y, x, indexing="ij")     # (norte, este) en km; la linea crece hacia el sur


def cambios(n, e, radio, dn, de):
    """Centros que cambian de lado del circulo de radio `radio` al trasladar la grilla (dn, de) km."""
    a = np.hypot(n, e) <= radio
    b = np.hypot(n + dn, e + de) <= radio
    return int(np.sum(a != b))


def medir(n, e, jac_px, d_km, radio, unidad):
    """Cuenta en 36 rumbos. unidad 'km': todos con |d| = d_km. 'px': mismo modulo en pixeles que d_km a lo
    ancho del barrido, devuelto a km con el jacobiano medio (diag(paso_lin, paso_frame))."""
    out = []
    for a in np.arange(0, 360, 10):
        t = math.radians(a)
        if unidad == "km":
            dn, de = d_km * math.cos(t), d_km * math.sin(t)
        else:
            mod = d_km / jac_px[1]
            dn, de = mod * math.cos(t) * jac_px[0], mod * math.sin(t) * jac_px[1]
        out.append(cambios(n, e, radio, dn, de))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", default=None)
    a = ap.parse_args()
    buf = io.StringIO()
    p = lambda *x: print(*x, file=buf)  # noqa: E731
    p("Centros de pixel que cambian de lado de un circulo al trasladar la grilla, en 36 rumbos")
    p("(media, minimo y maximo, y coeficiente de variacion entre rumbos; un tamano 'correcto' da CV bajo)")
    for nombre, n, e, jac in (("pixel 1 x 2 km", *grilla(1.0, 2.0), (1.0, 2.0)),
                              ("diente de sierra f=1,95, 2 km a lo ancho", *grilla(None, 2.0, sierra=1.95), (1.0, 2.0))):
        p("\n" + nombre)
        for radio in (1.0, 3.0, 5.0, 25.0):
            for unidad in ("km", "px"):
                c = medir(n, e, jac, 2.0, radio, unidad)
                m = float(np.mean(c))
                p("  radio %4.1f km, tamano fijo en %-2s: media %6.1f, min %3d, max %3d, CV %.2f" % (
                    radio, unidad, m, min(c), max(c), (float(np.std(c)) / m) if m else 0.0))
    sys.stdout.write(buf.getvalue())
    if a.salida:
        Path(a.salida).write_text(buf.getvalue(), encoding="utf-8")


if __name__ == "__main__":
    main()
