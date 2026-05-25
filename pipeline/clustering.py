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
    strategy: str = "vrp_max",
    inner_radius_km: float = None,
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
            `vrp_mw` (suma de VRPs de sus pixels).
        strategy: estrategia de ordenamiento (cuál cluster gana el "primary"):
            * "vrp_max" (default, backward-compat): mayor vrp_mw gana.
              Comportamiento histórico. Alineado con MIROVA cuando el
              cluster volcánico real es también el más grande.
            * "vent_anchored" (S38): prioridad por proximidad al vent.
              Clusters con centroide dentro de `inner_radius_km` ganan
              sobre clusters fuera (independiente de vrp_mw). Entre
              clusters dentro: el más cercano gana. Entre clusters fuera:
              el más cercano gana. Resuelve bug D8 donde un cluster
              grande lejano (Salar Atacama, lago) se elegía como primary
              ignorando el cluster real del cráter. Requiere
              `inner_radius_km` no-None.
        inner_radius_km: usado solo con strategy="vent_anchored". Radio en
            km del vent dentro del cual los clusters son "del cráter".

    Returns:
        Lista de dicts (uno por cluster), ordenados según strategy. Sin
        vrp_per_pixel y strategy="vrp_max", ordenados por n_pixels desc.
        Cada dict contiene n_pixels, centroid_lat/lon, centroid_dist_km,
        pixel_indices, y vrp_mw (si vrp_per_pixel se proveyo).
    """
    if hot_mask_2d.size == 0 or not hot_mask_2d.any():
        return []

    if strategy not in ("vrp_max", "vent_anchored"):
        raise ValueError(
            f"strategy debe ser 'vrp_max' o 'vent_anchored', got {strategy!r}"
        )
    if strategy == "vent_anchored" and inner_radius_km is None:
        raise ValueError(
            "strategy='vent_anchored' requiere inner_radius_km"
        )

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

    if strategy == "vent_anchored":
        # S38 D8 fix: cluster cercano al vent gana sobre cluster lejano,
        # independiente de vrp_mw. Filtro vent-anchored: clusters dentro
        # del inner_radius_km tienen prioridad absoluta; entre ellos y
        # entre los fuera, el más cercano gana. Empate por proximity con
        # vrp_mw desc como tiebreaker.
        #
        # S43 fix: cuando has_vrp, primero filtrar clusters con vrp_mw > 0.
        # Bug pre-S43: si cluster A está a 1.8km del vent con vrp=0 (todos
        # pixels delta_L clip a 0) y cluster B está a 5km con vrp=0.43 MW
        # (pixels hot reales), vent_anchored elegía A (más cerca) y pc.vrp=0.
        # Eso causaba 18 FNs sistemáticos en Tupungatito/Lastarria/Planchón
        # donde Test 1 dispara pero D4 fix solo aplica a SOME pixels —
        # cluster cercano queda vrp=0 mientras pixels con vrp real están más
        # lejos. Fix: si hay clusters con vrp>0, ignorar los con vrp=0 al
        # rankear. Solo si todos vrp=0, fallback al menor dist (preserva
        # comportamiento previo cuando no hay señal real).
        # F63/S78 — fix intentado, RECHAZADO post-TDD por trade-off legítimo.
        # docs/F63_CLUSTER_CONNECTIVITY_BRAINSTORM_S78.md (PR #209).
        # El fix simple (filtrar S43 solo cuando hay vrp>0 inside) ROMPE el
        # caso legítimo Tup/Last/PP donde cluster inside vrp=0 es ruido y
        # outside vrp>0 es lava real (test_d8_vent_anchored.py:163-216).
        # F63 propio = ambos casos indistinguibles sin más metadata
        # (triggered_test1 flag, vent_anchored explícito, etc).
        # Approach correcto S79+ = F66 híbrido (bg kernel local dual-gate)
        # que resuelve ambos físicamente sin trade-off.
        # docs/F66_BG_KERNEL_LOCAL_DEEP_S78.md (PR #214).
        if has_vrp:
            with_vrp = [c for c in clusters if c.get("vrp_mw", 0.0) > 0]
            ranking_set = with_vrp if with_vrp else clusters
        else:
            ranking_set = clusters

        def _vent_key(c):
            inside = c["centroid_dist_km"] <= inner_radius_km
            # tuple: (0 si inside else 1, dist asc, -vrp desc)
            vrp = c.get("vrp_mw", 0.0) if has_vrp else 0.0
            return (0 if inside else 1, c["centroid_dist_km"], -vrp)
        ranking_set.sort(key=_vent_key)
        # Clusters no en ranking_set van al final (no eligibles para primary)
        not_ranked = [c for c in clusters if c not in ranking_set]
        not_ranked.sort(key=_vent_key)
        clusters = ranking_set + not_ranked
    elif has_vrp:
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
