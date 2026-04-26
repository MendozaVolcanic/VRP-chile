"""TDD tests para pipeline.scan_geometry.

S23 Task 7 audit followup: scan_geometry.py (172 líneas) tenía cálculos
críticos sin tests dedicados:
- area_factor_from_zenith (sec³ correction)
- modis_zenith_from_column
- modis_pixel_areas
- viirs_pixel_areas (aggregated bow-tie)
- roi_mask_bbox

Solo cobertura indirecta vía process_*.py.
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.scan_geometry import (
    area_factor_from_zenith, modis_zenith_from_column, modis_pixel_areas,
    viirs_pixel_areas, roi_mask_bbox,
)


# === area_factor_from_zenith (sec³) ===

def test_area_factor_at_nadir_is_one():
    """zenith=0° → factor=1.0 (cos(0)=1, 1/1³=1)."""
    assert area_factor_from_zenith(0.0) == pytest.approx(1.0, abs=1e-6)


def test_area_factor_at_60deg_is_eight():
    """zenith=60° → cos(60°)=0.5, factor=1/0.5³=8.0."""
    assert area_factor_from_zenith(60.0) == pytest.approx(8.0, abs=0.01)


def test_area_factor_capped_at_70deg():
    """Más allá de 70° debe capear (no runaway sec³)."""
    cap_value = area_factor_from_zenith(70.0)
    beyond = area_factor_from_zenith(89.0)  # Casi rasante
    # Debería ser igual al cap (no diverger a infinito)
    assert beyond == pytest.approx(cap_value, abs=0.01)


def test_area_factor_array_input():
    """Input array preserva shape."""
    z = np.array([0.0, 30.0, 60.0])
    out = area_factor_from_zenith(z)
    assert out.shape == (3,)
    assert out[0] == pytest.approx(1.0, abs=1e-6)


# === modis_zenith_from_column ===

def test_modis_zenith_center_column_near_zero():
    """Columna central (676 de 1354) → zenith ~0."""
    z = modis_zenith_from_column(676)  # (1354-1)/2 = 676.5
    assert z == pytest.approx(0.0, abs=0.5)


def test_modis_zenith_edge_columns_high():
    """Columna borde (0 o 1353) → zenith máximo (~65° con curvatura tierra)."""
    z_left = modis_zenith_from_column(0)
    z_right = modis_zenith_from_column(1353)
    # Ambos extremos son simétricos (mismo abs valor)
    assert z_left > 50, f"Edge column zenith demasiado bajo: {z_left}"
    assert z_right > 50
    assert z_left == pytest.approx(z_right, abs=1.0)


# === modis_pixel_areas ===

def test_modis_pixel_areas_shape_correct():
    """Shape (n_lines, n_samples) preservado."""
    areas = modis_pixel_areas((100, 1354))
    assert areas.shape == (100, 1354)


def test_modis_pixel_areas_nadir_column_one_km_squared():
    """Columna nadir (676-677) ≈ 1.0e6 m² (1 km²)."""
    areas = modis_pixel_areas((10, 1354))
    nadir_val = areas[5, 676]
    assert nadir_val == pytest.approx(1.0e6, rel=0.05)


# === viirs_pixel_areas ===

def test_viirs_pixel_areas_nadir_unchanged():
    """zenith=0 → nadir_area_m2 sin escalar."""
    z = np.array([0.0])
    out = viirs_pixel_areas(z, nadir_area_m2=140625.0)
    assert out[0] == pytest.approx(140625.0, abs=1.0)


def test_viirs_pixel_areas_capped_at_2x():
    """Aggregation cap evita runaway: factor max 2.0."""
    z = np.array([60.0, 70.0])
    out = viirs_pixel_areas(z, nadir_area_m2=140625.0)
    # Factor max es 2.0 → area max 281,250 m²
    assert all(out <= 281_250.0 * 1.001)


# === roi_mask_bbox ===

def test_roi_mask_bbox_center_inside():
    """Centro del bbox debe estar incluido."""
    n = 50
    lat = np.linspace(-33.5, -33.3, n)[:, None] * np.ones((n, n))
    lon = np.ones((n, n)) * np.linspace(-69.9, -69.7, n)
    mask = roi_mask_bbox(lat, lon, -33.4, -69.8, half_km=2.5)
    # Punto central del grid debe estar incluido
    assert mask[n // 2, n // 2] == True


def test_roi_mask_bbox_corners_excluded():
    """Esquinas lejos del centro deben estar excluidas."""
    n = 50
    lat = np.linspace(-33.5, -33.3, n)[:, None] * np.ones((n, n))
    lon = np.ones((n, n)) * np.linspace(-69.9, -69.7, n)
    mask = roi_mask_bbox(lat, lon, -33.4, -69.8, half_km=2.5)
    # Esquina (0,0) está lejos del centro
    assert mask[0, 0] == False


def test_roi_mask_bbox_size_increases_with_half_km():
    """Mayor half_km → más pixels incluidos."""
    n = 50
    lat = np.linspace(-33.5, -33.3, n)[:, None] * np.ones((n, n))
    lon = np.ones((n, n)) * np.linspace(-69.9, -69.7, n)
    small = roi_mask_bbox(lat, lon, -33.4, -69.8, half_km=1.0).sum()
    big = roi_mask_bbox(lat, lon, -33.4, -69.8, half_km=10.0).sum()
    assert big > small
