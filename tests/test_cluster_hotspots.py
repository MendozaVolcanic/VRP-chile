"""S27 — TDD para cluster_hotspots: agrupacion de pixels detectados en clusters
espacialmente contiguos al estilo MIROVA n_hotspots.

MIROVA reporta n_hotspots = numero de regiones espacialmente contiguas
(~1km connectivity, Coppola 2016a). Cada cluster equivale a 1 punto en el
mapa MIROVA (al estilo CSV consolidado scrapeado de latest.php).

Cierre divergencia D1 documentada en docs/MIROVA_DIVERGENCES.md.
"""
from __future__ import annotations

import numpy as np


def test_empty_mask_returns_zero_clusters():
    from pipeline.clustering import cluster_hotspots
    mask = np.zeros((10, 10), dtype=bool)
    lat = np.full((10, 10), -23.0)
    lon = np.full((10, 10), -67.0)
    clusters = cluster_hotspots(mask, lat, lon, -23.0, -67.0)
    assert clusters == []


def test_single_pixel_one_cluster():
    from pipeline.clustering import cluster_hotspots
    mask = np.zeros((10, 10), dtype=bool)
    mask[5, 5] = True
    lat = np.linspace(-23.5, -22.5, 10).reshape(-1, 1).repeat(10, axis=1)
    lon = np.linspace(-68.0, -67.0, 10).reshape(1, -1).repeat(10, axis=0)
    clusters = cluster_hotspots(mask, lat, lon, -23.0, -67.5)
    assert len(clusters) == 1
    assert clusters[0]["n_pixels"] == 1


def test_two_adjacent_pixels_one_cluster():
    """Pixels adyacentes horizontalmente -> mismo cluster (conectividad 4 y 8)."""
    from pipeline.clustering import cluster_hotspots
    mask = np.zeros((10, 10), dtype=bool)
    mask[5, 4] = True
    mask[5, 5] = True
    lat = np.full((10, 10), -23.0)
    lon = np.full((10, 10), -67.0)
    clusters = cluster_hotspots(mask, lat, lon, -23.0, -67.0)
    assert len(clusters) == 1
    assert clusters[0]["n_pixels"] == 2


def test_diagonal_pixels_connectivity_8():
    """Conectividad 8 (default) une pixels en diagonal."""
    from pipeline.clustering import cluster_hotspots
    mask = np.zeros((10, 10), dtype=bool)
    mask[5, 5] = True
    mask[6, 6] = True
    lat = np.full((10, 10), -23.0)
    lon = np.full((10, 10), -67.0)
    clusters = cluster_hotspots(mask, lat, lon, -23.0, -67.0, connectivity=8)
    assert len(clusters) == 1
    assert clusters[0]["n_pixels"] == 2


def test_diagonal_pixels_connectivity_4_separates():
    """Conectividad 4 NO une diagonales -> 2 clusters separados."""
    from pipeline.clustering import cluster_hotspots
    mask = np.zeros((10, 10), dtype=bool)
    mask[5, 5] = True
    mask[6, 6] = True
    lat = np.full((10, 10), -23.0)
    lon = np.full((10, 10), -67.0)
    clusters = cluster_hotspots(mask, lat, lon, -23.0, -67.0, connectivity=4)
    assert len(clusters) == 2


def test_gap_separates_clusters():
    """Pixels separados por gap (no contiguos) -> clusters distintos."""
    from pipeline.clustering import cluster_hotspots
    mask = np.zeros((10, 10), dtype=bool)
    mask[5, 5] = True
    mask[5, 7] = True  # gap de 1 pixel entre col 5 y 7
    lat = np.full((10, 10), -23.0)
    lon = np.full((10, 10), -67.0)
    clusters = cluster_hotspots(mask, lat, lon, -23.0, -67.0)
    assert len(clusters) == 2


def test_centroid_is_mean_of_pixel_coords():
    """Centroide de cluster = media aritmetica de lat/lon de sus pixels."""
    from pipeline.clustering import cluster_hotspots
    mask = np.zeros((4, 4), dtype=bool)
    mask[1, 1] = True
    mask[1, 2] = True
    mask[2, 1] = True
    mask[2, 2] = True  # cuadrado 2x2
    # lat varia con i (row), lon varia con j (col)
    lat = np.array([[-23.0, -23.0, -23.0, -23.0],
                    [-23.1, -23.1, -23.1, -23.1],
                    [-23.2, -23.2, -23.2, -23.2],
                    [-23.3, -23.3, -23.3, -23.3]])
    lon = np.array([[-67.0, -67.1, -67.2, -67.3],
                    [-67.0, -67.1, -67.2, -67.3],
                    [-67.0, -67.1, -67.2, -67.3],
                    [-67.0, -67.1, -67.2, -67.3]])
    clusters = cluster_hotspots(mask, lat, lon, -23.15, -67.15)
    assert len(clusters) == 1
    c = clusters[0]
    assert c["n_pixels"] == 4
    # Centroide del cuadrado 2x2: rows 1+2 / cols 1+2 -> mean lat=-23.15, mean lon=-67.15
    assert abs(c["centroid_lat"] - (-23.15)) < 1e-6
    assert abs(c["centroid_lon"] - (-67.15)) < 1e-6


def test_centroid_dist_km_to_vent():
    """centroid_dist_km es haversine entre centroide y vent."""
    from pipeline.clustering import cluster_hotspots
    mask = np.zeros((3, 3), dtype=bool)
    mask[1, 1] = True
    lat = np.full((3, 3), -23.0)
    lon = np.full((3, 3), -67.0)
    clusters = cluster_hotspots(mask, lat, lon, -23.0, -67.0)
    # Centroide = (-23, -67), vent = (-23, -67) -> dist 0 km
    assert clusters[0]["centroid_dist_km"] < 0.01


def test_returns_pixel_indices():
    """Cada cluster lista los (i,j) de sus pixels (para debugging/forensics)."""
    from pipeline.clustering import cluster_hotspots
    mask = np.zeros((5, 5), dtype=bool)
    mask[2, 2] = True
    mask[2, 3] = True
    lat = np.full((5, 5), -23.0)
    lon = np.full((5, 5), -67.0)
    clusters = cluster_hotspots(mask, lat, lon, -23.0, -67.0)
    assert "pixel_indices" in clusters[0]
    assert sorted(clusters[0]["pixel_indices"]) == [(2, 2), (2, 3)]


def test_cluster_with_vrp_per_pixel_sums_correctly():
    """S27: cluster_hotspots con vrp_per_pixel devuelve vrp_mw del cluster."""
    from pipeline.clustering import cluster_hotspots
    import numpy as np
    mask = np.zeros((4, 4), dtype=bool)
    mask[1, 1] = True
    mask[1, 2] = True
    lat = np.full((4, 4), -23.0)
    lon = np.full((4, 4), -67.0)
    vrp = np.zeros((4, 4))
    vrp[1, 1] = 3.5
    vrp[1, 2] = 7.0
    clusters = cluster_hotspots(mask, lat, lon, -23.0, -67.0, vrp_per_pixel=vrp)
    assert len(clusters) == 1
    assert clusters[0]["n_pixels"] == 2
    assert "vrp_mw" in clusters[0]
    assert abs(clusters[0]["vrp_mw"] - 10.5) < 1e-6


def test_clusters_sorted_by_vrp_when_vrp_provided():
    """Cuando se pasa vrp_per_pixel, ordenar por vrp_mw desc (no por n_pixels)."""
    from pipeline.clustering import cluster_hotspots
    import numpy as np
    mask = np.zeros((10, 10), dtype=bool)
    # Cluster A: 3 pixels VRP total = 3 (1+1+1)
    mask[1, 1] = mask[1, 2] = mask[1, 3] = True
    # Cluster B: 1 pixel VRP = 50 (más caliente, gana)
    mask[8, 8] = True
    lat = np.full((10, 10), -23.0)
    lon = np.full((10, 10), -67.0)
    vrp = np.zeros((10, 10))
    vrp[1, 1] = vrp[1, 2] = vrp[1, 3] = 1.0
    vrp[8, 8] = 50.0
    clusters = cluster_hotspots(mask, lat, lon, -23.0, -67.0, vrp_per_pixel=vrp)
    assert clusters[0]["vrp_mw"] == 50.0
    assert clusters[0]["n_pixels"] == 1
    assert clusters[1]["vrp_mw"] == 3.0


def test_cluster_without_vrp_per_pixel_keeps_old_behavior():
    """Sin vrp_per_pixel: ordenar por n_pixels desc, no incluir vrp_mw."""
    from pipeline.clustering import cluster_hotspots
    import numpy as np
    mask = np.zeros((4, 4), dtype=bool)
    mask[1, 1] = mask[1, 2] = True
    lat = np.full((4, 4), -23.0)
    lon = np.full((4, 4), -67.0)
    clusters = cluster_hotspots(mask, lat, lon, -23.0, -67.0)
    assert clusters[0]["n_pixels"] == 2
    # vrp_mw no debe aparecer si no se pasó vrp_per_pixel
    assert "vrp_mw" not in clusters[0]


def test_clusters_sorted_by_size_descending():
    """Convencion: clusters retornados ordenados por n_pixels desc.

    El primero es el cluster mas grande (analogo al hotspot principal MIROVA).
    """
    from pipeline.clustering import cluster_hotspots
    mask = np.zeros((10, 10), dtype=bool)
    # Cluster A (n=4): rows 1-2, cols 1-2
    mask[1, 1] = mask[1, 2] = mask[2, 1] = mask[2, 2] = True
    # Cluster B (n=1): row 8, col 8
    mask[8, 8] = True
    # Cluster C (n=2): rows 5-5, cols 5-6
    mask[5, 5] = mask[5, 6] = True
    lat = np.full((10, 10), -23.0)
    lon = np.full((10, 10), -67.0)
    clusters = cluster_hotspots(mask, lat, lon, -23.0, -67.0)
    assert len(clusters) == 3
    assert [c["n_pixels"] for c in clusters] == [4, 2, 1]
