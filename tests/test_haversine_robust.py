"""haversine_km debe manejar inputs None y NaN sin crashear silenciosamente.

S23 Task 2 audit followup: detectado en audit S22 que haversine_km estaba
duplicado en process_modis.py, process_viirs.py, process_viirs_mod.py
(misma función) y no validaba volcano_lat=None → np.radians(None) genera
TypeError con mensaje confuso. Centralizado a scan_geometry.py con guard.
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.scan_geometry import haversine_km


def test_haversine_returns_array_for_array_inputs():
    lat2 = np.array([-33.5, -33.6])
    lon2 = np.array([-69.7, -69.6])
    out = haversine_km(-33.4, -69.8, lat2, lon2)
    assert out.shape == (2,)
    assert all(out > 0)


def test_haversine_zero_when_same_point():
    out = haversine_km(-33.4, -69.8,
                       np.array([-33.4]), np.array([-69.8]))
    assert out[0] == pytest.approx(0.0, abs=1e-6)


def test_haversine_known_distance():
    """1 grado lat ≈ 111.19 km en el ecuador (verificación física)."""
    out = haversine_km(0.0, 0.0, np.array([1.0]), np.array([0.0]))
    assert out[0] == pytest.approx(111.19, abs=0.5)


def test_haversine_raises_when_volcano_lat_is_none():
    """Defensa: volcano_lat=None debe disparar TypeError explícito,
    no silenciosamente propagar np.radians(None) → ValueError críptico."""
    with pytest.raises(TypeError, match="cannot be None"):
        haversine_km(None, -69.8,
                     np.array([-33.4]), np.array([-69.8]))


def test_haversine_raises_when_volcano_lon_is_none():
    with pytest.raises(TypeError, match="cannot be None"):
        haversine_km(-33.4, None,
                     np.array([-33.4]), np.array([-69.8]))


def test_haversine_handles_nan_in_array():
    """NaN en arrays input → NaN en output (no crash)."""
    lat2 = np.array([-33.5, np.nan])
    lon2 = np.array([-69.7, -69.6])
    out = haversine_km(-33.4, -69.8, lat2, lon2)
    assert out.shape == (2,)
    assert not np.isnan(out[0])
    assert np.isnan(out[1])


def test_haversine_2d_array_shape_preserved():
    """Inputs 2D mantienen shape (caso real grid lat/lon de granule)."""
    lat2 = np.array([[-33.4, -33.5], [-33.6, -33.7]])
    lon2 = np.array([[-69.8, -69.7], [-69.6, -69.5]])
    out = haversine_km(-33.4, -69.8, lat2, lon2)
    assert out.shape == (2, 2)
    assert out[0, 0] == pytest.approx(0.0, abs=1e-6)
