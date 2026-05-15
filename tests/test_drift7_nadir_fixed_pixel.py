"""Tests Drift #7 — A_pix nadir-fijo (Coppola 2016a SP426.5:201-202).

Coppola 2016a SP426.5 línea 201-202: "resampled within a 50x50 km grid…
spatial resolution of the resampled MODIS pixels is 1 km". Eq.7 línea 384:
"A_PIX is the pixel size (1 km^2 for the resampled MODIS pixels)".

MIROVA usa A_pix nadir-fijo para los 3 sensores (CLAUDE.md regla científica).
Flag opt-in por sensor preserva calibración empírica S14 como default.
"""
import numpy as np
import pytest

from pipeline.scan_geometry import modis_pixel_areas, viirs_pixel_areas


def test_drift7_modis_nadir_fixed_returns_uniform_1km2():
    """nadir_fixed=True: todas las pixels son 1 km^2 = 1e6 m^2."""
    shape = (10, 1354)  # MODIS shape canónico (n_lines, n_samples=1354)

    areas = modis_pixel_areas(shape, nadir_fixed=True)

    assert areas.shape == shape
    assert np.allclose(areas, 1_000_000.0), (
        f"Con nadir_fixed=True, todas deben ser 1e6 "
        f"(got range {areas.min()}-{areas.max()})"
    )


def test_drift7_modis_legacy_sec3_preserved():
    """nadir_fixed=False (default): aplica sec^3(theta_z) como antes."""
    shape = (1, 1354)
    areas_default = modis_pixel_areas(shape)
    areas_explicit = modis_pixel_areas(shape, nadir_fixed=False)

    # Comportamiento idéntico: default = nadir_fixed=False
    assert np.array_equal(areas_default, areas_explicit), (
        "Default debe ser nadir_fixed=False (backward-compat)"
    )

    # Nadir (centro col 676/677): A_pix ~ 1e6 (factor sec^3 ~ 1)
    center_col = 676
    nadir_pixel = areas_default[0, center_col]
    assert nadir_pixel == pytest.approx(1e6, rel=0.01), (
        f"Centro debe ser ~1e6 m^2 (got {nadir_pixel})"
    )

    # Edge (col 0 ó 1353): factor sec^3 mucho mayor a nadir (>4x esperado)
    edge_pixel = areas_default[0, 0]
    assert edge_pixel > 4 * nadir_pixel, (
        f"Edge debe ser >4x nadir (legacy sec^3) (got edge={edge_pixel}, "
        f"nadir={nadir_pixel})"
    )


def test_drift7_viirs_375m_nadir_fixed():
    """VIIRS I-band: nadir_fixed=True -> todos 140625 m^2 (0.140625 km^2)."""
    zen = np.array([0.0, 30.0, 60.0, 70.0])
    areas = viirs_pixel_areas(
        sensor_zenith_deg=zen,
        nadir_area_m2=140625.0,
        nadir_fixed=True,
    )
    assert np.allclose(areas, 140625.0)


def test_drift7_viirs_750m_nadir_fixed():
    """VIIRS M-band: nadir_fixed=True -> todos 562500 m^2 (0.5625 km^2)."""
    zen = np.array([0.0, 30.0, 60.0, 70.0])
    areas = viirs_pixel_areas(
        sensor_zenith_deg=zen,
        nadir_area_m2=562500.0,
        nadir_fixed=True,
    )
    assert np.allclose(areas, 562500.0)


def test_drift7_viirs_legacy_factor_preserved():
    """nadir_fixed=False (default): factor lineal 1-2x como antes."""
    zen = np.array([0.0, 60.0, 70.0])
    areas = viirs_pixel_areas(
        sensor_zenith_deg=zen,
        nadir_area_m2=140625.0,
        nadir_fixed=False,
    )
    # Nadir: factor 1.0 -> 140625
    assert areas[0] == pytest.approx(140625.0, rel=0.01)
    # 60 deg: factor entre 1.0 y 2.0
    assert areas[1] > 140625.0
    assert areas[1] < 280000.0
    # 70 deg (cap MAX_SENSOR_ZENITH_DEG): factor ~ 1 + (sec(70)-1)*0.5 ~ 1.962
    # Resultado esperado ~275892 (cap 2.0 nunca alcanzado con z=70)
    assert areas[2] == pytest.approx(275892.5, rel=0.01)
    assert areas[2] > 140625.0  # > nadir
    assert areas[2] < 281250.0  # < cap 2.0x
