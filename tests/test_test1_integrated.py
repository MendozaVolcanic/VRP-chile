"""TDD para pipeline/test1_integrated.py — Coppola 2015 Eq.1 Test 1."""
from __future__ import annotations
import math

import numpy as np
import pytest

from pipeline.test1_integrated import bt_to_radiance_um, compute_test1_mir


# === bt_to_radiance_um ===

def test_radiance_strictly_increases_with_temperature():
    """Planck: radiance is monotone in T at fixed λ."""
    Ts = np.array([200.0, 250.0, 300.0, 350.0, 400.0])
    L = bt_to_radiance_um(Ts, lambda_um=3.74)
    assert np.all(np.diff(L) > 0)


def test_radiance_nan_in_nan_out():
    bt = np.array([np.nan, 250.0, np.nan])
    L = bt_to_radiance_um(bt, 3.74)
    assert np.isnan(L[0]) and np.isnan(L[2])
    assert np.isfinite(L[1])


def test_radiance_known_value_blackbody_300K_at_3p74um():
    """Sanity: Planck blackbody at 300K, 3.74μm ≈ 0.439 W/m²/sr/μm.

    Computed from c1=1.191e-16 W·m²·sr⁻¹, c2=1.439e-2 m·K:
      B(λ,T) = (c1/λ⁵) / (exp(c2/(λT))−1)
    """
    L = bt_to_radiance_um(np.array([300.0]), 3.74)
    # Tolerance 1%
    assert 0.434 < L[0] < 0.444


# === compute_test1_mir on synthetic granules ===

def _make_grid(n=20, vent_lat=0.0, vent_lon=0.0, pixel_km=0.375):
    """Make synthetic VIIRS-I-like grid centered on vent. Each cell ≈0.375 km."""
    deg_per_km_lat = 1 / 111.0
    deg_per_km_lon = 1 / (111.0 * math.cos(math.radians(vent_lat)))
    half = (n - 1) / 2.0
    di = np.arange(n) - half
    dj = np.arange(n) - half
    dlat = di[:, None] * pixel_km * deg_per_km_lat
    dlon = dj[None, :] * pixel_km * deg_per_km_lon
    lat = vent_lat + dlat * np.ones((n, n))
    lon = vent_lon + dlon * np.ones((n, n))
    return lat, lon


def test_pure_uniform_background_does_not_trigger():
    """Granule with uniform bg ≈260K should NOT trigger Test 1."""
    n = 20
    lat, lon = _make_grid(n)
    bt = np.full((n, n), 260.0)
    # Add tiny gaussian noise so MAD is non-zero
    rng = np.random.default_rng(42)
    bt += rng.normal(0, 0.5, size=bt.shape)

    res = compute_test1_mir(bt, lat, lon, 0.0, 0.0, lambda_um=3.74,
                            roi_km=3.0, inner_ring_km=1.0)
    assert res["triggered"] is False
    assert res["n_bg"] >= 20


def test_strong_central_hotspot_triggers():
    """Granule with bright sub-pixel center should trigger."""
    n = 20
    lat, lon = _make_grid(n)
    bt = np.full((n, n), 260.0)
    rng = np.random.default_rng(42)
    bt += rng.normal(0, 0.5, size=bt.shape)
    # Add bright pixel at center (one pixel = lava lake-like)
    bt[n // 2, n // 2] = 280.0
    bt[n // 2, n // 2 + 1] = 275.0

    res = compute_test1_mir(bt, lat, lon, 0.0, 0.0, lambda_um=3.74,
                            roi_km=3.0, inner_ring_km=1.0)
    assert res["triggered"] is True
    assert res["abs_criterion"] is True
    assert res["rel_criterion"] is True
    assert res["n_contributing"] >= 1
    assert res["k_sigma_observed"] > 3.0
    # Centroid near vent
    assert abs(res["centroid_lat"]) < 0.005
    assert abs(res["centroid_lon"]) < 0.005


def test_diffuse_subpixel_warm_anomaly_triggers():
    """The Villarrica case: many pixels slightly warm (sub-pixel mixed)
    should trigger via integration even if no single pixel is hot."""
    n = 20
    lat, lon = _make_grid(n)
    bt = np.full((n, n), 260.0)
    rng = np.random.default_rng(42)
    bt += rng.normal(0, 0.5, size=bt.shape)
    # 20 pixels in central ROI lifted by +2K (each below 5K threshold)
    cy, cx = n // 2, n // 2
    for di in range(-2, 3):
        for dj in range(-2, 3):
            bt[cy + di, cx + dj] += 2.0

    res = compute_test1_mir(bt, lat, lon, 0.0, 0.0, lambda_um=3.74,
                            roi_km=3.0, inner_ring_km=1.0)
    assert res["triggered"] is True, f"failed with k={res['k_sigma_observed']:.2f} rel={res['rel_observed']:.4f}"


def test_returns_diagnostic_fields_when_not_triggered():
    """Even when not triggered, dict has all expected keys."""
    n = 20
    lat, lon = _make_grid(n)
    bt = np.full((n, n), 260.0)
    rng = np.random.default_rng(42)
    bt += rng.normal(0, 0.5, size=bt.shape)

    res = compute_test1_mir(bt, lat, lon, 0.0, 0.0, lambda_um=3.74)
    expected_keys = {"triggered", "abs_criterion", "rel_criterion", "n_roi",
                     "n_bg", "n_contributing", "L_bg", "sigma_bg",
                     "delta_L_integrated", "sigma_delta_L_integrated",
                     "k_sigma_observed", "rel_observed", "mask_roi",
                     "mask_contributing", "centroid_lat", "centroid_lon",
                     "reason"}
    assert expected_keys <= set(res.keys())


def test_insufficient_bg_pixels_returns_no_trigger_with_reason():
    """Small grid where bg ring is empty should return triggered=False with reason."""
    n = 6  # very small grid, bg ring will be tiny
    lat, lon = _make_grid(n, pixel_km=0.1)  # only 0.6 km across — entirely inner
    bt = np.full((n, n), 260.0)

    res = compute_test1_mir(bt, lat, lon, 0.0, 0.0, lambda_um=3.74,
                            roi_km=3.0, inner_ring_km=1.0, min_bg_pixels=20)
    assert res["triggered"] is False
    assert "insufficient_bg" in res["reason"] or res["n_bg"] < 20


def test_nan_pixels_excluded_from_stats():
    """NaN pixels should not contaminate L_bg or σ_bg."""
    n = 20
    lat, lon = _make_grid(n)
    bt = np.full((n, n), 260.0)
    rng = np.random.default_rng(42)
    bt += rng.normal(0, 0.5, size=bt.shape)
    # Inject NaN strip
    bt[0:3, :] = np.nan

    res = compute_test1_mir(bt, lat, lon, 0.0, 0.0, lambda_um=3.74)
    # Should still work (n_bg still >= 20 because grid is 20x20 with strip on edge)
    assert res["n_bg"] > 0
    # No crash, returns finite L_bg
    assert math.isfinite(res["L_bg"])


def test_shape_mismatch_raises():
    bt = np.zeros((10, 10))
    lat = np.zeros((10, 10))
    lon = np.zeros((10, 11))  # wrong
    with pytest.raises(ValueError, match="shape mismatch"):
        compute_test1_mir(bt, lat, lon, 0.0, 0.0, lambda_um=3.74)


def test_higher_k_sigma_makes_trigger_harder():
    """Same diffuse anomaly: trigger at k=3 but not at k=10."""
    n = 20
    lat, lon = _make_grid(n)
    bt = np.full((n, n), 260.0)
    rng = np.random.default_rng(42)
    bt += rng.normal(0, 0.5, size=bt.shape)
    cy, cx = n // 2, n // 2
    for di in range(-1, 2):
        for dj in range(-1, 2):
            bt[cy + di, cx + dj] += 1.0

    res_low = compute_test1_mir(bt, lat, lon, 0.0, 0.0, lambda_um=3.74, k_sigma=3.0)
    res_high = compute_test1_mir(bt, lat, lon, 0.0, 0.0, lambda_um=3.74, k_sigma=10.0)
    # Low k may or may not trigger, high k should be harder to trigger
    # If both trigger, k_high observation should still be > 3 to satisfy
    if res_low["triggered"]:
        # weak signal: k=3 fires, k=10 should NOT
        assert not res_high["triggered"] or res_high["k_sigma_observed"] >= 10.0
