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
    order = np.argsort(-vrps)[:top_n]
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
