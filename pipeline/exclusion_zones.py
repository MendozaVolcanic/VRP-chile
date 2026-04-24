"""exclusion_zones.py — Filtro post-deteccion de zonas geograficas conocidas.

S16 P3.6 simplificado: en vez de water mask global Natural Earth (requiere
geopandas/fiona y shapefile externo), usamos coordinadas hardcoded por
volcan en volcanoes.yaml de zonas conocidas que generan FPs (cuerpos de
agua, salares, embalses irradiando calor nocturno).

Identificacion S16 2026-04-23:
  - Lascar: Salar de Atacama a 22-23 km NW del vent. Bbox S15 lo incluye
    -> 4326 pixels Path A => VRP fantasma 1437 MW (vs MIROVA real 4 MW).
  - Tupungatito: Embalse El Yeso a 25-27 km SE. Bbox S15 lo incluye ->
    cientos de pixels => VRPs 58-205 MW (vs MIROVA real <1 MW).

Schema yaml por volcan:
  exclude_zones:
    - name: "Salar de Atacama"
      lat: -23.5
      lon: -68.2
      radius_km: 25.0

Aplicacion: en process_*.py despues del hot_mask, descartar pixels que
caen dentro de cualquier exclude_zone del volcano (excepto si estan en
whitelist active_water_bodies, que prevalece).
"""

import math
from typing import Iterable

import numpy as np


def haversine_km(lat1: float, lon1: float,
                 lat2: np.ndarray, lon2: np.ndarray) -> np.ndarray:
    """Distancia haversine entre punto fijo y array de puntos. Devuelve km."""
    R = 6371.0
    p1 = math.radians(lat1)
    p2 = np.radians(lat2)
    dp = np.radians(lat2 - lat1)
    dl = np.radians(lon2 - lon1)
    a = np.sin(dp / 2) ** 2 + math.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


def in_exclusion_mask(lat: np.ndarray,
                      lon: np.ndarray,
                      exclude_zones: Iterable[dict]) -> np.ndarray:
    """Mask 2D True donde el pixel cae dentro de alguna exclusion zone.

    Args:
        lat, lon: arrays 2D mismo shape.
        exclude_zones: iterable de dicts con keys 'lat', 'lon', 'radius_km'.

    Returns:
        bool array mismo shape que lat. True = pixel a excluir.
    """
    if not exclude_zones:
        return np.zeros(lat.shape, dtype=bool)
    excl = np.zeros(lat.shape, dtype=bool)
    for zone in exclude_zones:
        d = haversine_km(zone["lat"], zone["lon"], lat, lon)
        excl |= (d <= zone["radius_km"])
    return excl


def in_whitelist_mask(lat: np.ndarray,
                      lon: np.ndarray,
                      whitelist: Iterable[dict]) -> np.ndarray:
    """Mask 2D True donde el pixel cae dentro de un active water body.

    active_water_bodies whitelist (Tupungatito laguna cratérica, Villarrica
    lava lake, Copahue Laguna El Agrio, etc). Prevalece sobre exclude_zones.

    Args:
        lat, lon: arrays 2D.
        whitelist: iterable de dicts con keys 'lat', 'lon', 'radius_km'.

    Returns:
        bool array True = pixel en whitelist (no se debe filtrar).
    """
    if not whitelist:
        return np.zeros(lat.shape, dtype=bool)
    wl = np.zeros(lat.shape, dtype=bool)
    for body in whitelist:
        d = haversine_km(body["lat"], body["lon"], lat, lon)
        wl |= (d <= body["radius_km"])
    return wl


def filter_hot_mask(hot_mask: np.ndarray,
                    lat: np.ndarray,
                    lon: np.ndarray,
                    exclude_zones: Iterable[dict],
                    active_water_bodies: Iterable[dict] = None) -> tuple:
    """Aplica filtro water-aware al hot_mask.

    Pixel se descarta si:
        hot_mask[pixel] AND in_exclusion[pixel] AND NOT in_whitelist[pixel]

    Args:
        hot_mask: bool 2D, True = pixel detectado por algun path.
        lat, lon: arrays 2D coords.
        exclude_zones: lista zonas a excluir (e.g., Salar de Atacama).
        active_water_bodies: whitelist de lagos crateres activos.

    Returns:
        (filtered_hot_mask, n_filtered) — mask post-filter y conteo de pixels removidos.
    """
    if not exclude_zones:
        return hot_mask, 0
    excl = in_exclusion_mask(lat, lon, exclude_zones)
    wl = in_whitelist_mask(lat, lon, active_water_bodies or [])
    # Pixel se descarta si: estaba caliente AND en zona excluida AND no en whitelist
    to_remove = hot_mask & excl & ~wl
    n_filtered = int(np.sum(to_remove))
    filtered = hot_mask & ~to_remove
    return filtered, n_filtered
