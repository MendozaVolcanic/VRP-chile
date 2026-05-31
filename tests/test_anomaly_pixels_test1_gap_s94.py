"""S94 (A45) — TDD para el gap del path Test1: anomaly_pixels vacío.

Bug (hallazgo S94, process_viirs.py:1500-1517): los records con
final_hotspot_source='test1' arman primary_cluster con la magnitud pero dejan
anomaly_pixels=[] vacío, aunque tienen los píxeles en t1_vrp_2d. Patrón A07
("calculado pero no persistido"). Bloquea el F5' display + rompe el mapa de
píxeles del dashboard para esos records (Tupungatito, Villarrica).

Fix: extraer la construcción de anomaly_pixels a un helper puro
`build_anomaly_pixels(vrp_2d, lat, lon, dist, bt, top_n)` que ambos paths usan
(el line-1128 normal Y el Test1). Helper bajo test acá.

Referencias: pipeline/anomaly_pixels.py (helper), pipeline/process_viirs.py.
"""
import numpy as np

from pipeline.anomaly_pixels import build_anomaly_pixels


def test_returns_pixels_sorted_by_vrp_desc_with_fields():
    """Top-N por vrp descendente, con lat/lon/dist_km/bt_k/vrp_mw."""
    vrp = np.array([[0.0, 0.5], [2.0, 0.1]])
    lat = np.array([[-23.0, -23.1], [-23.2, -23.3]])
    lon = np.array([[-67.0, -67.1], [-67.2, -67.3]])
    dist = np.array([[1.0, 2.0], [0.5, 3.0]])
    bt = np.array([[280.0, 290.0], [310.0, 275.0]])
    out = build_anomaly_pixels(vrp, lat, lon, dist, bt, top_n=2)
    assert len(out) == 2
    assert out[0]["vrp_mw"] == 2.0  # el más caliente primero
    assert out[0]["lat"] == -23.2 and out[0]["lon"] == -67.2
    assert out[0]["bt_k"] == 310.0 and out[0]["dist_km"] == 0.5
    assert out[1]["vrp_mw"] == 0.5
    assert set(out[0].keys()) == {"lat", "lon", "dist_km", "bt_k", "vrp_mw"}


def test_excludes_zero_vrp_pixels():
    """Píxeles con vrp=0 (resto del grid) NO entran."""
    vrp = np.zeros((3, 3))
    vrp[1, 1] = 0.13
    lat = np.full((3, 3), -33.39)
    lon = np.full((3, 3), -69.83)
    dist = np.full((3, 3), 0.1)
    bt = np.full((3, 3), 277.0)
    out = build_anomaly_pixels(vrp, lat, lon, dist, bt)
    assert len(out) == 1
    assert all(p["vrp_mw"] > 0 for p in out)


def test_test1_like_sparse_grid_is_nonempty():
    """EL GAP: un grid Test1 (sparse, pocos nonzero) DEBE producir píxeles, no []."""
    vrp = np.zeros((5, 5))
    vrp[2, 2] = 0.1328
    vrp[2, 3] = 0.024
    lat = np.full((5, 5), -33.389)
    lon = np.full((5, 5), -69.827)
    dist = np.full((5, 5), 0.06)
    bt = np.full((5, 5), 276.7)
    out = build_anomaly_pixels(vrp, lat, lon, dist, bt)
    assert len(out) == 2  # NO vacío
    assert out[0]["vrp_mw"] == 0.1328


def test_caps_at_top_n():
    """Limita a top_n (default 100) para no inflar el JSON."""
    vrp = np.arange(1, 151, dtype=float).reshape(10, 15) / 100.0
    lat = np.zeros((10, 15))
    lon = np.zeros((10, 15))
    dist = np.zeros((10, 15))
    bt = np.full((10, 15), 290.0)
    out = build_anomaly_pixels(vrp, lat, lon, dist, bt, top_n=100)
    assert len(out) == 100
    # el primero es el de mayor vrp (1.50)
    assert out[0]["vrp_mw"] == 1.5


def test_empty_grid_returns_empty():
    vrp = np.zeros((4, 4))
    z = np.zeros((4, 4))
    assert build_anomaly_pixels(vrp, z, z, z, z) == []
