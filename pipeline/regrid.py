# -*- coding: utf-8 -*-
# ============================================================================
# FICHA SDA — Nivel 1 (Res. CPLT N°372)
# Módulo      : regrid.py — resampleo del swath a grilla UTM regular (F70)
# Rol         : PRE-PROCESAMIENTO geométrico. No decide ni clasifica: prepara
#               el sustrato de área constante sobre el que la detección corre
#               sin cambios. Flag-OFF hasta veredicto del A/B F70.3.
# Entradas    : lat/lon + radiancias del granule (swath crudo)
# Salidas     : matrices regulares (celda de área constante) + máscara suitable
# Autoridad   : Coppola 2016a SP426.5 (~L162: "cropped and resampled (into an
#               equally spaced 1 km grid) ... within a grid (50 × 50 km)
#               centred on the volcano's summit"; ~L150-160: la detección
#               "requires homogenous pixel scale"). Campus 2024 (L102-104):
#               mismo esquema para VIIRS 375 m.
# Diseño      : docs/superpowers/specs/2026-08-25-grilla-utm-kernel-global-design.md
# ============================================================================
"""Resampleo del swath satelital a la grilla regular que MIROVA usa.

POR QUÉ (el fenómeno físico): un píxel de satélite no es un cuadrado fijo —
lejos del nadir se estira hasta ~10 km² (MODIS). Cuando el algoritmo pregunta
"¿este píxel es más caliente que sus vecinos?", la respuesta depende de la
geometría de esos vecinos tanto como de su temperatura: sobre un volcán con
glaciar, un vecino elongado promedia hielo + roca + valle en proporciones que
cambian en cada pasada. MIROVA elimina ese problema ANTES de detectar,
resampleando cada escena a celdas regulares de área constante. Este módulo
replica ese paso.

DECISIÓN DOCUMENTADA (la única no-literal): los papers no especifican el
interpolador. Usamos VECINO MÁS CERCANO por defecto porque conserva
radiancias que el sensor midió de verdad — promediar inventaría mezclas.
Queda parametrizado (`method`) para el análisis de sensibilidad de F70.1.
"""
import math

import numpy as np


def _utm_like_xy(lat, lon, clat, clon):
    """Coordenadas locales en km respecto del centro (aproximación local).

    Para una ventana de ±25 km, la proyección transversal local (equirectangular
    escalada por cos(lat) del centro) difiere de UTM verdadero en <0.1% —
    muy por debajo del tamaño de celda. Se mantiene sin dependencia de pyproj
    para que el módulo sea puro-numpy y trivial de testear; si F70.2 detecta
    que la diferencia importa en volcanes extremos, se cambia por pyproj acá
    sin tocar a los llamadores.
    """
    kx = 111.320 * math.cos(math.radians(clat))
    ky = 111.320
    return (np.asarray(lon, dtype=np.float64) - clon) * kx, \
           (np.asarray(lat, dtype=np.float64) - clat) * ky


def regrid_to_utm(lat2d, lon2d, bands: dict, center_lat: float,
                  center_lon: float, cell_km: float = 1.0,
                  half_km: float = 25.5, method: str = "nearest") -> dict:
    """Resamplea las bandas del swath a una grilla regular centrada en el volcán.

    Args:
        lat2d, lon2d: geolocalización del swath (cualquier shape 2D).
        bands: {nombre: array 2D} — todas con la MISMA shape que lat2d.
            Se regrillan juntas para que compartan geometría celda a celda
            (una celda con MIR pero sin TIR rompería el NTI aguas abajo).
        center_lat/lon: centro de la grilla (mirova_center del volcán).
        cell_km: lado de la celda (1.0 MODIS/VIIRS750; 0.375 VIIRS I-band).
        half_km: semiancho de la ventana (25.5 → grilla 51×51 de 1 km).
        method: "nearest" (default y única implementación por ahora — ver
            docstring del módulo).

    Returns:
        dict con: una matriz (n×n, float64, NaN donde no hubo muestra) por
        banda; "suitable" (bool, celdas con muestra válida en TODAS las
        bandas); "cell_area_km2" (constante — el punto de todo esto);
        "n" (lado de la grilla).
    """
    if method != "nearest":
        raise ValueError(f"method {method!r} no implementado (solo 'nearest')")

    n = int(round(2 * half_km / cell_km))
    x, y = _utm_like_xy(lat2d, lon2d, center_lat, center_lon)
    x, y = x.ravel(), y.ravel()

    # índice de celda de cada muestra del swath (col desde el Oeste, fila
    # desde el Norte — orientación de imagen, consistente con los procesadores)
    ix = np.floor((x + half_km) / cell_km).astype(np.int64)
    iy = np.floor((half_km - y) / cell_km).astype(np.int64)
    dentro = (ix >= 0) & (ix < n) & (iy >= 0) & (iy < n)

    # validez: la muestra debe traer valor finito en TODAS las bandas —
    # así las matrices de salida comparten geometría exactamente.
    flat = {k: np.asarray(v, dtype=np.float64).ravel() for k, v in bands.items()}
    validas = dentro.copy()
    for v in flat.values():
        validas &= np.isfinite(v)

    # distancia de cada muestra al centro de SU celda: en caso de duplicados
    # en una celda gana la más cercana (se escriben de peor a mejor, la
    # última escritura queda). Un NaN nunca compite: ya quedó fuera de
    # `validas` — por eso un píxel inválido no desplaza a un valor real.
    cx = (ix + 0.5) * cell_km - half_km
    cy = half_km - (iy + 0.5) * cell_km
    d2 = (x - cx) ** 2 + (y - cy) ** 2
    orden = np.argsort(-d2[validas])          # peor primero, mejor al final
    sel = np.flatnonzero(validas)[orden]

    out = {}
    for k, v in flat.items():
        g = np.full((n, n), np.nan, dtype=np.float64)
        g[iy[sel], ix[sel]] = v[sel]
        out[k] = g

    suitable = np.ones((n, n), dtype=bool)
    for g in out.values():
        suitable &= np.isfinite(g)
    out["suitable"] = suitable
    out["cell_area_km2"] = cell_km * cell_km
    out["n"] = n
    return out
