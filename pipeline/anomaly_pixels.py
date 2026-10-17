"""Helper puro para construir la lista `anomaly_pixels` de un record.

Extraído en S94 (A45) para que TODOS los paths que producen un VRP por-píxel
(el path normal de process_viirs.py y el path Test1) persistan los píxeles de la
misma forma. Antes, el path Test1 dejaba anomaly_pixels=[] vacío aunque tenía los
píxeles calculados (patrón A07) → bloqueaba el F5' display y rompía el mapa de
píxeles del dashboard para Tupungatito/Villarrica.

NO cambia detección ni magnitud (pc.vrp_mw): solo serializa píxeles ya calculados.
"""
from __future__ import annotations

import numpy as np


def orden_vrp_descendente(vrps, rows, cols):
    """Índices que ordenan los píxeles por VRP descendente, con desempate por (fila, columna).

    POR QUÉ (S151, tarea 1.22). En MODIS la temperatura de brillo sale de enteros escalados del
    L1B y toma valores discretos; con el área fija de nadir (A66) y el fondo del anillo como un
    solo número, dos píxeles con el mismo entero tienen un VRP por píxel IDÉNTICO bit a bit, y esos
    empates son frecuentes. `np.argsort` por defecto no es estable y numpy lo despacha a una ruta
    SIMD distinta según la CPU (AVX2, AVX-512 o ninguna), así que el orden de los empates, y con él
    el hotspot de escena (primer elemento) y qué píxeles entran al top-100, cambiaba de un runner a
    otro con el mismo commit (medido: Llaima Terra 2026-10-06 01:45, `vrp_mw` 4,281 contra 3,568).

    La clave (VRP descendente, fila, columna) depende sólo de la identidad del píxel, no de su
    posición en el arreglo ni de la CPU: define una permutación ÚNICA, que `np.lexsort` (estable)
    devuelve igual en cualquier máquina. Para los valores distintos el orden es el de siempre; sólo
    fija cuál de los empatados va primero, que antes era cualquiera. Los NaN van al final, como en
    el `argsort` anterior.

    Args:
        vrps: VRP por píxel [MW], 1D.
        rows, cols: fila y columna de cada píxel en la grilla del gránulo, 1D, alineadas con vrps.

    Returns:
        np.ndarray de índices sobre `vrps` (el llamador recorta a top-N).
    """
    vrps = np.asarray(vrps, dtype=np.float64)
    # lexsort ordena por la ÚLTIMA clave primero: -vrp, luego fila, luego columna.
    return np.lexsort((np.asarray(cols), np.asarray(rows), -vrps))


def build_anomaly_pixels(vrp_2d, lat, lon, dist, bt, top_n: int = 100):
    """Top-N píxeles anómalos (vrp>0) ordenados por VRP descendente.

    Args:
        vrp_2d: grid 2D de VRP por píxel [MW] (0 donde no hay anomalía).
        lat, lon, dist, bt: grids 2D alineados (lat/lon grados, dist km al centro
            del volcán — convención existente, NO desde el vent; bt en K).
        top_n: cap de píxeles persistidos (default 100, evita bloat del JSON;
            captura >95% de la señal VRP en records eruptivos).

    Returns:
        list[dict] con {lat, lon, dist_km, bt_k, vrp_mw}, redondeo igual al path
        histórico de process_viirs.py (lat/lon 5, dist 2, bt 2, vrp 4). [] si no
        hay píxeles con vrp>0.
    """
    rows, cols = np.where(vrp_2d > 0)
    if len(rows) == 0:
        return []
    vrps = vrp_2d[rows, cols]
    # S151 1.22: desempate explícito, independiente de la CPU (ver orden_vrp_descendente).
    order = orden_vrp_descendente(vrps, rows, cols)[:top_n]
    out = []
    for k in order:
        r, c = int(rows[k]), int(cols[k])
        out.append({
            "lat": round(float(lat[r, c]), 5),
            "lon": round(float(lon[r, c]), 5),
            "dist_km": round(float(dist[r, c]), 2),
            "bt_k": round(float(bt[r, c]), 2),
            "vrp_mw": round(float(vrp_2d[r, c]), 4),
        })
    return out
