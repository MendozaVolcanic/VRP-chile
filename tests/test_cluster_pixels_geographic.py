"""S27 — TDD para cluster_pixels_geographic: cluster pixels por proximidad
lat/lon (vs cluster_hotspots que opera sobre grid 2D).

Caso de uso: post-procesar JSONs existentes que tienen `anomaly_pixels`
array con coords lat/lon y vrp_mw individuales, agruparlos por proximidad
geográfica (~1 km Coppola 2016a) y reportar primary_cluster.vrp_mw.
"""
from __future__ import annotations


def test_empty_returns_empty():
    from pipeline.clustering import cluster_pixels_geographic
    assert cluster_pixels_geographic([]) == []


def test_single_pixel_one_cluster():
    from pipeline.clustering import cluster_pixels_geographic
    pixels = [{"lat": -40.5, "lon": -72.0, "vrp_mw": 5.0}]
    clusters = cluster_pixels_geographic(pixels)
    assert len(clusters) == 1
    assert clusters[0]["n_pixels"] == 1
    assert clusters[0]["vrp_mw"] == 5.0


def test_two_close_pixels_one_cluster():
    """Dos pixels a <1km se agrupan."""
    from pipeline.clustering import cluster_pixels_geographic
    pixels = [
        {"lat": -40.500, "lon": -72.000, "vrp_mw": 5.0},
        {"lat": -40.503, "lon": -72.000, "vrp_mw": 3.0},  # ~330m al sur
    ]
    clusters = cluster_pixels_geographic(pixels, max_dist_km=1.5)
    assert len(clusters) == 1
    assert clusters[0]["n_pixels"] == 2
    assert clusters[0]["vrp_mw"] == 8.0


def test_two_far_pixels_separate_clusters():
    """Dos pixels separados >1.5km son clusters distintos."""
    from pipeline.clustering import cluster_pixels_geographic
    pixels = [
        {"lat": -40.500, "lon": -72.000, "vrp_mw": 5.0},
        {"lat": -40.530, "lon": -72.000, "vrp_mw": 3.0},  # ~3.3 km al sur
    ]
    clusters = cluster_pixels_geographic(pixels, max_dist_km=1.5)
    assert len(clusters) == 2


def test_clusters_sorted_by_vrp_desc():
    """Cluster primario = el que más VRP totaliza, no el más numeroso."""
    from pipeline.clustering import cluster_pixels_geographic
    pixels = [
        # Cluster A — 3 pixels, VRP total 15
        {"lat": -40.500, "lon": -72.000, "vrp_mw": 5.0},
        {"lat": -40.501, "lon": -72.000, "vrp_mw": 5.0},
        {"lat": -40.502, "lon": -72.000, "vrp_mw": 5.0},
        # Cluster B — 1 pixel, VRP 50 (caliente único, gana en VRP)
        {"lat": -40.600, "lon": -72.000, "vrp_mw": 50.0},
    ]
    clusters = cluster_pixels_geographic(pixels, max_dist_km=1.5)
    assert len(clusters) == 2
    assert clusters[0]["vrp_mw"] == 50.0
    assert clusters[0]["n_pixels"] == 1
    assert clusters[1]["vrp_mw"] == 15.0


def test_centroid_is_mean_lat_lon():
    from pipeline.clustering import cluster_pixels_geographic
    pixels = [
        {"lat": -40.500, "lon": -72.000, "vrp_mw": 5.0},
        {"lat": -40.502, "lon": -72.002, "vrp_mw": 5.0},
    ]
    clusters = cluster_pixels_geographic(pixels)
    assert abs(clusters[0]["centroid_lat"] - (-40.501)) < 1e-4
    assert abs(clusters[0]["centroid_lon"] - (-72.001)) < 1e-4


def test_chain_three_pixels_all_in_one_cluster():
    """A-B-C cadena: A-B <1.5km, B-C <1.5km, A-C >1.5km. Todos en un cluster."""
    from pipeline.clustering import cluster_pixels_geographic
    pixels = [
        {"lat": -40.500, "lon": -72.000, "vrp_mw": 1.0},
        {"lat": -40.510, "lon": -72.000, "vrp_mw": 1.0},  # 1.1km de A
        {"lat": -40.520, "lon": -72.000, "vrp_mw": 1.0},  # 1.1km de B, 2.2km de A
    ]
    clusters = cluster_pixels_geographic(pixels, max_dist_km=1.5)
    assert len(clusters) == 1
    assert clusters[0]["n_pixels"] == 3
