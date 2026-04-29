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
    vrp_per_pixel: np.ndarray = None,
) -> List[dict]:
    """Agrupa pixels detectados (hot_mask_2d=True) en clusters espaciales.

    Args:
        hot_mask_2d: bool 2D array, True donde hay deteccion.
        lat, lon: 2D arrays mismas shape, lat/lon de cada pixel del granule.
        vent_lat, vent_lon: coordenadas del vent (para computar dist).
        connectivity: 4 (solo H/V) o 8 (H/V + diagonales). Default 8 — mas
            permisivo, alineado con Coppola 2016a "neighbor pixels" tipica.
        vrp_per_pixel: 2D array opcional con VRP_MW por pixel (mismo shape
            que hot_mask_2d). Cuando se provee, cada cluster output incluye
            `vrp_mw` (suma de VRPs de sus pixels) y los clusters se ordenan
            por vrp_mw desc (no por n_pixels). Alineado con MIROVA NRT que
            reporta VRP del cluster contiguo principal.

    Returns:
        Lista de dicts (uno por cluster). Sin vrp_per_pixel, ordenados por
        n_pixels desc. Con vrp_per_pixel, ordenados por vrp_mw desc.
        Cada dict:
            n_pixels: int.
            vrp_mw: float (solo si vrp_per_pixel se proveyo).
            centroid_lat: float.
            centroid_lon: float.
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
    has_vrp = vrp_per_pixel is not None
    clusters = []
    for k in range(1, n_clusters + 1):
        ii, jj = np.where(labels == k)
        n = len(ii)
        c_lat = float(np.mean(lat[ii, jj]))
        c_lon = float(np.mean(lon[ii, jj]))
        c_dist = _haversine_km(c_lat, c_lon, vent_lat, vent_lon)
        cluster = {
            "n_pixels": n,
            "centroid_lat": c_lat,
            "centroid_lon": c_lon,
            "centroid_dist_km": c_dist,
            "pixel_indices": [(int(i), int(j)) for i, j in zip(ii, jj)],
        }
        if has_vrp:
            cluster["vrp_mw"] = float(np.sum(vrp_per_pixel[ii, jj]))
        clusters.append(cluster)

    if has_vrp:
        clusters.sort(key=lambda c: c["vrp_mw"], reverse=True)
    else:
        clusters.sort(key=lambda c: c["n_pixels"], reverse=True)
    return clusters


def cluster_pixels_geographic(
    pixels: list,
    *,
    max_dist_km: float = 1.5,
) -> List[dict]:
    """Agrupa pixels (lista de dicts con lat/lon/vrp_mw) por proximidad
    geográfica (haversine), ordenados por VRP del cluster descendente.

    A diferencia de `cluster_hotspots()` que opera sobre grid 2D regular,
    este helper funciona sobre lista arbitraria de pixels con coords —
    útil para post-procesar JSONs existentes con `anomaly_pixels` array.

    Args:
        pixels: lista de dicts. Cada uno debe tener al menos keys 'lat',
            'lon' y 'vrp_mw'. Otros keys se preservan en pixel_indices.
        max_dist_km: distancia máxima entre pixels para considerarlos del
            mismo cluster. Default 1.5 km (Coppola 2016a "neighbor pixels"
            con tolerancia para pixel size 750m + grid drift).

    Returns:
        Lista de dicts (uno por cluster), ordenados por vrp_mw desc:
            n_pixels: int.
            vrp_mw: float, suma de VRPs de pixels en el cluster.
            centroid_lat, centroid_lon: media de coords del cluster.
            pixel_indices: list[int], índices al array de entrada.
    """
    n = len(pixels)
    if n == 0:
        return []
    if n == 1:
        p = pixels[0]
        return [{
            "n_pixels": 1,
            "vrp_mw": float(p.get("vrp_mw", 0.0)),
            "centroid_lat": float(p["lat"]),
            "centroid_lon": float(p["lon"]),
            "pixel_indices": [0],
        }]

    # Union-find sobre pares de pixels
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py

    for i in range(n):
        for j in range(i + 1, n):
            d = _haversine_km(
                pixels[i]["lat"], pixels[i]["lon"],
                pixels[j]["lat"], pixels[j]["lon"],
            )
            if d <= max_dist_km:
                union(i, j)

    groups: dict = {}
    for i in range(n):
        root = find(i)
        groups.setdefault(root, []).append(i)

    clusters = []
    for indices in groups.values():
        vrp_sum = sum(pixels[i].get("vrp_mw", 0.0) for i in indices)
        c_lat = sum(pixels[i]["lat"] for i in indices) / len(indices)
        c_lon = sum(pixels[i]["lon"] for i in indices) / len(indices)
        clusters.append({
            "n_pixels": len(indices),
            "vrp_mw": float(vrp_sum),
            "centroid_lat": float(c_lat),
            "centroid_lon": float(c_lon),
            "pixel_indices": list(indices),
        })

    clusters.sort(key=lambda c: c["vrp_mw"], reverse=True)
    return clusters
