"""TDD tests para pipeline/process_modis.py funciones core.

S23 Task 5 audit followup: process_modis.py procesa 50% de records Tier A
pero NO tenía tests dedicados. Solo cobertura indirecta via S18+ forenses.

Approach: mockear `read_modis_l1b` para inyectar arrays sintéticos y testear
calculate_vrp end-to-end sin requerir HDF files reales.
"""
from __future__ import annotations
import sys
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


def _synthetic_modis_data(hot_pixel_at=None, hot_radiance=20.0,
                          bg_radiance=5.0, bg_std=0.1,
                          center_lat=-33.4, center_lon=-69.8,
                          span_km=15, n=50, seed=42):
    """Crea dict synthetic con bands + lat/lon como retorna read_modis_l1b.

    bands: radiancias en W/m²/sr/μm (no BT). En MODIS L1B emissive es radiancia
    calibrada; la conversión a BT se hace internally en process_modis.

    hot_pixel_at: tuple (row, col) o None.
    hot_radiance: valor de radiancia en pixel hot (W/m²/sr/μm). 5.0 ≈ bg típico
        a 290K, 20.0 ≈ pixel a ~330K (hot detectable).
    """
    rng = np.random.default_rng(seed)
    band21 = rng.normal(bg_radiance, bg_std, size=(n, n)).astype(np.float32)
    band22 = band21.copy()
    band31 = rng.normal(bg_radiance * 1.5, bg_std, size=(n, n)).astype(np.float32)
    if hot_pixel_at is not None:
        r, c = hot_pixel_at
        band21[r, c] = hot_radiance
        band22[r, c] = hot_radiance
        band31[r, c] = bg_radiance * 1.5  # TIR no se eleva tanto para hot real

    dlat = span_km / 111.0
    dlon = span_km / (111.0 * np.cos(np.radians(center_lat)))
    lats = np.linspace(center_lat - dlat, center_lat + dlat, n)
    lons = np.linspace(center_lon - dlon, center_lon + dlon, n)
    lat_grid, lon_grid = np.meshgrid(lats, lons, indexing="ij")
    return {
        "band21": band21, "band22": band22, "band31": band31,
        "lat": lat_grid.astype(np.float32),
        "lon": lon_grid.astype(np.float32),
    }


def test_calculate_vrp_returns_none_when_volcano_outside_granule():
    """ROI completamente fuera del granule → retorna None."""
    from pipeline import process_modis as pm

    # Granule centrado en (-33.4, -69.8) span 15km, volcano a 50° distintos
    data = _synthetic_modis_data(center_lat=-33.4, center_lon=-69.8)

    with patch.object(pm, 'read_modis_l1b', return_value=data):
        result = pm.calculate_vrp(
            hdf_path=Path("fake.hdf"),
            geo_path=Path("fake_geo.hdf"),
            volcano_lat=10.0,  # MUY lejos
            volcano_lon=10.0,
            radius_km=15.0,
            vent_lat=None, vent_lon=None,
        )

    assert result is None, "Volcano fuera de granule debe retornar None"


def test_calculate_vrp_no_anomaly_in_uniform_scene():
    """Escena uniforme (sin pixel hot) → n_anomalous_pixels=0, vrp_mw=0."""
    from pipeline import process_modis as pm

    data = _synthetic_modis_data(hot_pixel_at=None,
                                 bg_radiance=5.0, bg_std=0.1)

    with patch.object(pm, 'read_modis_l1b', return_value=data):
        result = pm.calculate_vrp(
            hdf_path=Path("fake.hdf"),
            geo_path=Path("fake_geo.hdf"),
            volcano_lat=-33.4, volcano_lon=-69.8,
            radius_km=15.0,
            vent_lat=None, vent_lon=None,
        )

    assert result is not None
    assert result["n_anomalous_pixels"] == 0
    assert result["vrp_mw"] == 0
    assert result["vrp_vent_mw"] == 0


def test_calculate_vrp_returns_diag_fields():
    """Return dict debe incluir diag_* fields S22.1 paridad MODIS."""
    from pipeline import process_modis as pm

    data = _synthetic_modis_data(bg_radiance=5.0)

    with patch.object(pm, 'read_modis_l1b', return_value=data):
        result = pm.calculate_vrp(
            hdf_path=Path("fake_MOD021KM.A2026100.0500.061.fake.hdf"),
            geo_path=Path("fake_geo.hdf"),
            volcano_lat=-33.4, volcano_lon=-69.8,
            radius_km=15.0,
        )

    assert result is not None
    # Schema MODIS canonical (S22.1 paridad). Cada uno debe estar presente
    # (puede ser None si no hay data válida pero la key debe estar).
    expected_diag_keys = {
        "diag_sigma_bg_k", "diag_eff_threshold_k",
        "diag_t_max_dist_km", "diag_roi_p95_k",
        "diag_n_bt_path", "diag_n_nti_path", "diag_n_dnti_ctx_path",
        "diag_nti_bg", "diag_nti_max", "diag_nti_std",
    }
    actual_keys = set(result.keys())
    missing = expected_diag_keys - actual_keys
    assert not missing, f"Diag fields faltantes en retorno MODIS: {missing}"


def test_calculate_vrp_sensor_field_correct():
    """sensor field debe inferirse del filename (MOD vs MYD)."""
    from pipeline import process_modis as pm

    data = _synthetic_modis_data()

    with patch.object(pm, 'read_modis_l1b', return_value=data):
        result_terra = pm.calculate_vrp(
            hdf_path=Path("MOD021KM.A2026100.0500.061.NRT.hdf"),
            geo_path=Path("MOD03.A2026100.0500.061.NRT.hdf"),
            volcano_lat=-33.4, volcano_lon=-69.8,
            radius_km=15.0,
        )
        result_aqua = pm.calculate_vrp(
            hdf_path=Path("MYD021KM.A2026100.0500.061.NRT.hdf"),
            geo_path=Path("MYD03.A2026100.0500.061.NRT.hdf"),
            volcano_lat=-33.4, volcano_lon=-69.8,
            radius_km=15.0,
        )

    assert result_terra is not None and result_aqua is not None
    assert result_terra["sensor"] == "MODIS_TERRA"
    assert result_aqua["sensor"] == "MODIS_AQUA"


def test_calculate_vrp_product_version_detection():
    """product_version debe ser 'nrt' si filename contiene '_NRT'."""
    from pipeline import process_modis as pm

    data = _synthetic_modis_data()

    with patch.object(pm, 'read_modis_l1b', return_value=data):
        nrt = pm.calculate_vrp(
            hdf_path=Path("MOD021KM_NRT.A2026100.0500.061.fake.hdf"),
            geo_path=Path("fake.hdf"),
            volcano_lat=-33.4, volcano_lon=-69.8,
            radius_km=15.0,
        )
        std = pm.calculate_vrp(
            hdf_path=Path("MOD021KM.A2026100.0500.061.fake.hdf"),
            geo_path=Path("fake.hdf"),
            volcano_lat=-33.4, volcano_lon=-69.8,
            radius_km=15.0,
        )

    assert nrt is not None and std is not None
    assert nrt["product_version"] == "nrt"
    assert std["product_version"] == "standard"
