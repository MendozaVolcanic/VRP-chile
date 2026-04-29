"""S27 — Cluster aggregation de pixels detectados al estilo MIROVA n_hotspots.

MIROVA reporta `n_hotspots` = numero de regiones espacialmente contiguas
(~1km connectivity, Coppola 2016a). Cada cluster equivale a 1 punto en el
mapa MIROVA (al estilo CSV consolidado scrapeado de latest.php que reporta
exactamente 1 registro por (timestamp, volcan, sensor)).

Cierre divergencia D1 documentada en docs/MIROVA_DIVERGENCES.md:
nuestro pipeline reportaba `n_anomalous_pixels` (count de pixels) y este
modulo agrega `n_hotspots_clustered` (count de regiones espacialmente
contiguas), alineado con la convencion MIROVA.
"""
from __future__ import annotations

import math
from typing import List

import numpy as np
from scipy.ndimage import label as ndi_label


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    lat1r, lat2r = math.radians(lat1), math.radians(lat2)
    dlat = lat2r - lat1r
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1r) * math.cos(lat2r) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def cluster_hotspots(
    hot_mask_2d: np.ndarray,
    lat: np.ndarray,
    lon: np.ndarray,
    vent_lat: float,
    vent_lon: float,
    *,
    connectivity: int = 8,
) -> List[dict]:
    """Agrupa pixels detectados (hot_mask_2d=True) en clusters espaciales.

    Args:
        hot_mask_2d: bool 2D array, True donde hay deteccion.
        lat, lon: 2D arrays mismas shape, lat/lon de cada pixel del granule.
        vent_lat, vent_lon: coordenadas del vent (para computar dist).
        connectivity: 4 (solo H/V) o 8 (H/V + diagonales). Default 8 — mas
            permisivo, alineado con Coppola 2016a "neighbor pixels" tipica.

    Returns:
        Lista de dicts (uno por cluster), ordenados por n_pixels descendente.
        Cada dict:
            n_pixels: int, cantidad de pixels en el cluster.
            centroid_lat: float, media de lat de los pixels.
            centroid_lon: float, media de lon de los pixels.
            centroid_dist_km: float, haversine centroid -> vent.
            pixel_indices: list[(i, j)] coords de los pixels en arrays 2D.
    """
    if hot_mask_2d.size == 0 or not hot_mask_2d.any():
        return []

    if connectivity == 4:
        structure = np.array([[0, 1, 0],
                              [1, 1, 1],
                              [0, 1, 0]])
    elif connectivity == 8:
        structure = np.ones((3, 3), dtype=int)
    else:
        raise ValueError(f"connectivity debe ser 4 u 8, got {connectivity}")

    labels, n_clusters = ndi_label(hot_mask_2d, structure=structure)
    clusters = []
    for k in range(1, n_clusters + 1):
        ii, jj = np.where(labels == k)
        n = len(ii)
        c_lat = float(np.mean(lat[ii, jj]))
        c_lon = float(np.mean(lon[ii, jj]))
        c_dist = _haversine_km(c_lat, c_lon, vent_lat, vent_lon)
        clusters.append({
            "n_pixels": n,
            "centroid_lat": c_lat,
            "centroid_lon": c_lon,
            "centroid_dist_km": c_dist,
            "pixel_indices": [(int(i), int(j)) for i, j in zip(ii, jj)],
        })

    clusters.sort(key=lambda c: c["n_pixels"], reverse=True)
    return clusters
