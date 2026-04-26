"""Invariantes geométricos del script 41 (medición std_bg multi-ROI)."""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from experiments.measure_local_bg_offline import (
    bbox_mask, annulus_mask, std_bg, exclude_disk,
)


def _grid(half_km: float = 30.0, n: int = 200, center=(-33.4, -69.8)):
    """Mesh de lat/lon centrado en `center` cubriendo ±half_km."""
    lat0, lon0 = center
    dlat = half_km / 111.0
    dlon = half_km / (111.0 * np.cos(np.radians(lat0)))
    lats = np.linspace(lat0 - dlat, lat0 + dlat, n)
    lons = np.linspace(lon0 - dlon, lon0 + dlon, n)
    lat_grid, lon_grid = np.meshgrid(lats, lons, indexing="ij")
    return lat_grid, lon_grid


# === bbox_mask ===

def test_bbox_mask_returns_bool_2d():
    lat, lon = _grid(half_km=10)
    mask = bbox_mask(lat, lon, -33.4, -69.8, half_km=2.5)
    assert mask.dtype == bool
    assert mask.shape == lat.shape


def test_bbox_mask_smaller_when_radius_smaller():
    lat, lon = _grid(half_km=10)
    big = bbox_mask(lat, lon, -33.4, -69.8, half_km=5.0).sum()
    small = bbox_mask(lat, lon, -33.4, -69.8, half_km=2.0).sum()
    assert big > small > 0


# === annulus_mask ===

def test_annulus_mask_excludes_inner_disk():
    lat, lon = _grid(half_km=20)
    inner = annulus_mask(lat, lon, -33.4, -69.8, inner_km=2.0, outer_km=10.0)
    # Centro del grid no debe estar incluido
    h = lat.shape[0] // 2
    assert inner[h, h] == False


def test_annulus_mask_size_growing_with_outer():
    lat, lon = _grid(half_km=20)
    a1 = annulus_mask(lat, lon, -33.4, -69.8, inner_km=2.0, outer_km=5.0).sum()
    a2 = annulus_mask(lat, lon, -33.4, -69.8, inner_km=2.0, outer_km=10.0).sum()
    assert a2 > a1


# === std_bg ===

def test_std_bg_zero_for_constant_array():
    bt = np.full((50, 50), 280.0)
    mask = np.ones_like(bt, dtype=bool)
    s, n = std_bg(bt, mask)
    assert s == pytest.approx(0.0)
    assert n == 2500


def test_std_bg_returns_nan_when_too_few():
    bt = np.full((10, 10), 280.0)
    mask = np.zeros_like(bt, dtype=bool)
    mask[0, 0] = True
    s, n = std_bg(bt, mask, min_pixels=25)
    assert np.isnan(s)
    assert n == 1


def test_std_bg_excludes_nans():
    bt = np.full((10, 10), 280.0)
    bt[0, 0] = np.nan
    mask = np.ones_like(bt, dtype=bool)
    s, n = std_bg(bt, mask)
    assert s == pytest.approx(0.0)
    assert n == 99


# === exclude_disk ===

def test_exclude_disk_removes_center_pixels():
    lat, lon = _grid(half_km=10)
    full = bbox_mask(lat, lon, -33.4, -69.8, half_km=5.0)
    excluded = exclude_disk(full, lat, lon, -33.4, -69.8, radius_km=2.0)
    assert excluded.sum() < full.sum()
    # Esquina debería seguir incluida
    assert excluded[0, 0] == full[0, 0]
