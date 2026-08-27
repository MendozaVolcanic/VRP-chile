# -*- coding: utf-8 -*-
"""F70.2b — ¿cuántos píxeles calientes pierde el regrillado nearest-neighbor?

POR QUÉ importa: el regrid resuelve un problema real (los ocho vecinos dejan de
ser objetos geométricamente distintos en cada pasada), pero introduce uno nuevo.
Cuando dos muestras del swath caen en la MISMA celda, gana la más próxima al
centro — aunque la otra sea la caliente. En un volcán eso es un FALSO NEGATIVO:
justo el píxel que el algoritmo busca.

El resultado depende de cuánto sobre-muestrea el swath a la celda, que es
función de dónde cae el volcán dentro del barrido (efecto bow-tie: hacia el
borde del scan las muestras se comprimen y solapan).

Fuente de verdad de los números del informe (regla S91).
"""
import io
import sys

import numpy as np

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2]))
from pipeline.regrid import regrid_to_utm

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
CLAT, CLON = -36.867210, -71.378241


def tasa_perdida(step_km, cell_km, half_km, n=300, semilla=11):
    """Pone UN píxel caliente a <2 km del cráter y pregunta si sobrevive."""
    rng = np.random.default_rng(semilla)
    sd_lat = step_km / 111.32
    sd_lon = step_km / (111.32 * np.cos(np.radians(CLAT)))
    lats = np.arange(CLAT - 0.25, CLAT + 0.25, sd_lat)
    lons = np.arange(CLON - 0.25, CLON + 0.25, sd_lon)
    lon2d, lat2d = np.meshgrid(lons, lats)
    dy = (lat2d - CLAT) * 111.32
    dx = (lon2d - CLON) * 111.32 * np.cos(np.radians(CLAT))
    cand = np.argwhere(dy ** 2 + dx ** 2 < 4.0)
    perdidos = 0
    for _ in range(n):
        i, j = cand[rng.integers(len(cand))]
        mir = np.full(lat2d.shape, 280.0)
        tir = np.full(lat2d.shape, 270.0)
        mir[i, j] = 340.0
        g = regrid_to_utm(lat2d, lon2d, {"mir": mir, "tir": tir}, CLAT, CLON,
                          cell_km=cell_km, half_km=half_km,
                          required=("mir", "tir"))
        if not np.any(g["mir"] == 340.0):
            perdidos += 1
    return 100.0 * perdidos / n


if __name__ == "__main__":
    print("A) Al paso NATIVO de cada sensor (una muestra por celda):\n")
    print(f"{'sensor':16s} {'paso':>9s} {'celda':>9s} {'hot px perdidos':>17s}")
    for nom, step, cell, half in (("VIIRS I (375m)", 0.375, 0.375, 25.125),
                                  ("VIIRS M (750m)", 0.750, 0.750, 25.125),
                                  ("MODIS (1km)", 1.000, 1.000, 25.5)):
        print(f"{nom:16s} {step:6.3f} km {cell:6.3f} km "
              f"{tasa_perdida(step, cell, half):16.1f}%")

    print("\nB) Con SOLAPAMIENTO de barrido (VIIRS I, celda 0.375 km):\n")
    print(f"{'paso':>10s} {'muestras/celda':>16s} {'hot px perdidos':>17s}")
    for f in (1.0, 0.8, 0.6, 0.5, 0.4):
        paso = 0.375 * f
        print(f"{paso:7.3f} km {(0.375/paso)**2:16.2f} "
              f"{tasa_perdida(paso, 0.375, 25.125):16.1f}%")
    print("\nLectura: al paso nativo no se pierde nada. El riesgo aparece SOLO")
    print("donde el swath solapa. VIIRS aplica borrado bow-tie en el producto")
    print("(los duplicados del borde vienen como fill = NaN, y un NaN nunca")
    print("compite), así que el caso B acota el peor escenario, no el típico.")
    print("MODIS NO borra bow-tie: es el sensor a vigilar en el A/B de F70.3.")
