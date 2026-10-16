# Tarea 1.21: modelo de corrimiento de `_interp_geo` con los dos ejes.
#
# POR QUE. `_interp_geo` (pipeline/process_modis.py:342) estira la grilla de 5 km del L1B a 1 km con
# `scipy.ndimage.zoom(order=1)`, que alinea esquina con esquina. Los nodos de 5 km del L1B estan en el
# frame 5k + 2 y en la linea 5k + 2 (#828, offset 2 en los dos ejes), asi que el zoom corre la posicion
# en los DOS ejes:
#   a lo ancho del barrido: el frame s recibe la posicion del frame 0,99778*s + 2 (270/1353*5);
#   a lo largo de la traza: la linea y recibe la posicion de la linea 0,998029*y + 2 (405/2029*5).
# El modelo de #828 (seleccionar_mxd03.corrimiento_predicho) tenia solo el primero. El verificador del
# resultado de la 1.17 encontro el segundo con r = 0,955 bajo 30 grados de cenit
# (C:\Users\nmend\AppData\Local\Temp\claude\verif_117r\v5_along_track.py). Aca se suman los dos, que
# son perpendiculares. El terreno (300 a 450 m de relieve a escala de 1 km, #828) queda fuera del modelo
# y lo cubre el margen.
#
# La componente a lo largo de la traza vale 2 - 0,001971*y lineas: +2 al inicio del granulo, 0 al medio
# y -2 al final. Un record guardado no trae la linea del crater, asi que sin linea se usa el peor caso
# (2 lineas). Una linea mide en el suelo lo que el IFOV a la distancia oblicua: 1 km en nadir, R/H km a
# un angulo de barrido con distancia oblicua R.
import math
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "_s151_mxd03_etiquetas"))

import seleccionar_mxd03 as S  # noqa: E402  (modelo de #828 a lo ancho del barrido, sin cambios)

ALTURA_KM, RADIO_KM = S.ALTURA_KM, S.RADIO_KM
LINEAS = 2030                 # lineas de 1 km de un granulo MODIS de 5 min
PEOR_LINEAS = 2.0             # |2 - 0,001971*y| maximo (y = 0)


def lineas_a_lo_largo(linea):
    """Corrimiento a lo largo de la traza en lineas (con signo), para la linea `linea` del granulo."""
    return 2.0 - 0.001971 * linea


def angulo_barrido(cenit):
    """Angulo de barrido (grados) que da ese cenit de sensor, por biseccion sobre la geometria de 705 km."""
    lo, hi = 0.0, 55.0
    for _ in range(60):
        m = (lo + hi) / 2
        if S._cenit(m) < cenit:
            lo = m
        else:
            hi = m
    return (lo + hi) / 2


def km_por_linea(cenit):
    """Paso en el suelo entre dos lineas: distancia oblicua sobre la altura (1 km en nadir)."""
    t = math.radians(angulo_barrido(cenit))
    oblicua = (RADIO_KM + ALTURA_KM) * math.cos(t) - math.sqrt(
        RADIO_KM ** 2 - (RADIO_KM + ALTURA_KM) ** 2 * math.sin(t) ** 2)
    return oblicua / ALTURA_KM


def corrimiento_predicho_traza(cenit, acimut, sensor, linea=None):
    """Modulo del corrimiento (km) en el pixel: hipotenusa del termino del barrido (#828) y del de la
    traza. Sin `linea`, el peor caso de la traza (2 lineas). None si faltan los angulos."""
    a = S.corrimiento_predicho(cenit, acimut, sensor)
    if a is None:
        return None
    n_lin = PEOR_LINEAS if linea is None else abs(lineas_a_lo_largo(linea))
    return math.hypot(a, n_lin * km_por_linea(cenit))
