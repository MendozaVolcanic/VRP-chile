"""Invariantes script 39: centroide ponderado VRP + propose_mirova_center."""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from experiments.locate_active_vent import (
    weighted_centroid, propose_mirova_center, load_volcano_cfg,
)


def test_centroid_single_pixel():
    pixels = [{"lat": -33.4, "lon": -69.8, "vrp_mw": 0.2}]
    lat, lon = weighted_centroid(pixels)
    assert abs(lat - (-33.4)) < 1e-9
    assert abs(lon - (-69.8)) < 1e-9


def test_centroid_two_pixels_equal_weight():
    pixels = [
        {"lat": -33.4, "lon": -69.8, "vrp_mw": 0.1},
        {"lat": -33.5, "lon": -69.9, "vrp_mw": 0.1},
    ]
    lat, lon = weighted_centroid(pixels)
    assert abs(lat - (-33.45)) < 1e-9
    assert abs(lon - (-69.85)) < 1e-9


def test_centroid_weighted_pulls_toward_hot_pixel():
    pixels = [
        {"lat": -33.4, "lon": -69.8, "vrp_mw": 1.0},
        {"lat": -33.5, "lon": -69.9, "vrp_mw": 0.01},
    ]
    lat, lon = weighted_centroid(pixels)
    assert lat > -33.45
    assert lon > -69.85


def test_centroid_zero_vrp_uses_arithmetic_mean():
    pixels = [
        {"lat": -33.4, "lon": -69.8, "vrp_mw": 0.0},
        {"lat": -33.5, "lon": -69.9, "vrp_mw": 0.0},
    ]
    lat, lon = weighted_centroid(pixels)
    assert abs(lat - (-33.45)) < 1e-9


def test_centroid_empty_returns_nan():
    import math
    lat, lon = weighted_centroid([])
    assert math.isnan(lat)
    assert math.isnan(lon)


def test_propose_offset_under_threshold_returns_none():
    nominal = {"vent_lat": -33.4, "vent_lon": -69.8}
    proposed = propose_mirova_center(
        observed_centroid=(-33.4015, -69.8015),
        nominal=nominal, threshold_km=0.5,
    )
    assert proposed is None


def test_propose_offset_above_threshold_returns_dict():
    nominal = {"vent_lat": -33.4, "vent_lon": -69.8}
    proposed = propose_mirova_center(
        observed_centroid=(-33.43, -69.85),
        nominal=nominal, threshold_km=0.5,
    )
    assert proposed is not None
    assert "mirova_center_lat" in proposed
    assert "mirova_center_lon" in proposed
    assert "offset_km" in proposed
    assert proposed["offset_km"] > 0.5


def test_load_volcano_cfg_list_format(tmp_path):
    yaml_path = tmp_path / "v.yaml"
    yaml_path.write_text(
        "volcanoes:\n"
        "  - name: Tupungatito\n"
        "    vent_lat: -33.389\n"
        "    vent_lon: -69.826\n"
        "    inner_radius_km: 7\n"
        "  - name: Lascar\n"
        "    vent_lat: -23.36\n"
        "    vent_lon: -67.73\n"
    )
    cfg = load_volcano_cfg(yaml_path, "Tupungatito")
    assert cfg["vent_lat"] == -33.389
    assert cfg["inner_radius_km"] == 7
