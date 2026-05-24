"""Tests F31 Task A1 — TIRVolcH detector (Aveni 2024 RSE).

Synthetic-only tests. Verifica gates principales del paper:
- Paso 1 absoluto OBS > 313.15 K
- Paso 2-4 residuo + Z-score temporal (default 7 sigma)
- Sensibilidad declarada 0.5 K
- Baseline temporal robusto MAD
- Ring contextual mean/std/p99.95

Refs:
- pipeline/detect_tirvolch.py
- Vault/10_Bibliografia/99_por_clasificar/aveni2024tirvolch.md
"""
from __future__ import annotations

import numpy as np
import pytest

from pipeline.detect_tirvolch import (
    TIRVOLCH_DT_MIN_K,
    TIRVOLCH_T_ABS_MIN_K,
    TIRVOLCH_Z_THRESHOLD,
    compute_contextual_ring,
    compute_temporal_baseline,
    detect_tirvolch,
)


# ---------------------------------------------------------------------------
# detect_tirvolch — gates principales
# ---------------------------------------------------------------------------

def test_detect_positive_above_threshold():
    bt = np.full((5, 5), 315.0)
    ref = np.full((5, 5), 315.0)
    sigma = np.full((5, 5), 1.0)
    bt[2, 2] = 325.0

    mask = detect_tirvolch(bt, ref, sigma)

    assert mask[2, 2] == True
    assert mask.sum() == 1


def test_detect_negative_below_dt_threshold():
    bt = np.full((3, 3), 315.0)
    ref = np.full((3, 3), 315.0)
    sigma = np.full((3, 3), 0.01)
    bt[1, 1] = 315.3

    mask = detect_tirvolch(bt, ref, sigma)

    assert mask.any() == False


def test_detect_negative_below_absolute_gate():
    bt = np.full((3, 3), 280.0)
    ref = np.full((3, 3), 270.0)
    sigma = np.full((3, 3), 1.0)
    bt[1, 1] = 312.0

    mask = detect_tirvolch(bt, ref, sigma)

    assert mask.any() == False


def test_detect_negative_below_zscore():
    bt = np.full((3, 3), 320.0)
    ref = np.full((3, 3), 317.0)
    sigma = np.full((3, 3), 1.0)

    mask = detect_tirvolch(bt, ref, sigma)

    assert mask.any() == False


def test_detect_nan_propagation():
    bt = np.full((3, 3), 325.0)
    ref = np.full((3, 3), 315.0)
    sigma = np.full((3, 3), 1.0)
    bt[0, 0] = np.nan
    ref[1, 1] = np.nan
    sigma[2, 2] = np.nan

    mask = detect_tirvolch(bt, ref, sigma)

    assert mask[0, 0] == False
    assert mask[1, 1] == False
    assert mask[2, 2] == False
    assert mask[1, 0] == True


def test_detect_sigma_zero_rejected():
    bt = np.full((2, 2), 325.0)
    ref = np.full((2, 2), 315.0)
    sigma = np.zeros((2, 2))

    mask = detect_tirvolch(bt, ref, sigma)

    assert mask.any() == False


def test_detect_shape_mismatch_raises():
    bt = np.zeros((3, 3))
    ref = np.zeros((3, 4))
    sigma = np.zeros((3, 3))

    with pytest.raises(ValueError, match="Shapes mismatch"):
        detect_tirvolch(bt, ref, sigma)


def test_detect_custom_thresholds():
    bt = np.full((3, 3), 320.0)
    ref = np.full((3, 3), 317.0)
    sigma = np.full((3, 3), 1.0)

    assert detect_tirvolch(bt, ref, sigma).any() == False
    assert detect_tirvolch(bt, ref, sigma, n_sigma_temporal=2.0).all() == True


# ---------------------------------------------------------------------------
# compute_temporal_baseline
# ---------------------------------------------------------------------------

def test_baseline_mean_recovers_signal():
    stack = np.full((20, 4, 4), 290.0)
    mean, std = compute_temporal_baseline(stack)

    assert np.allclose(mean, 290.0)
    assert np.all(std >= 0)


def test_baseline_std_monotone_with_noise():
    rng = np.random.default_rng(seed=42)
    n_frames = 50
    shape = (5, 5)

    low_noise = 290.0 + rng.normal(0, 0.5, size=(n_frames, *shape))
    high_noise = 290.0 + rng.normal(0, 3.0, size=(n_frames, *shape))

    _, std_low = compute_temporal_baseline(low_noise)
    _, std_high = compute_temporal_baseline(high_noise)

    assert np.nanmean(std_low) < np.nanmean(std_high)


def test_baseline_robust_to_outliers():
    n_frames = 30
    stack = np.full((n_frames, 3, 3), 290.0)
    stack[0, 1, 1] = 500.0

    mean, _ = compute_temporal_baseline(stack)

    assert abs(mean[1, 1] - 290.0) < 1.0


def test_baseline_requires_minimum_frames():
    with pytest.raises(ValueError, match="at least 2 frames"):
        compute_temporal_baseline(np.full((1, 3, 3), 290.0))


def test_baseline_wrong_ndim_raises():
    with pytest.raises(ValueError, match=r"Expected \(N,H,W\)"):
        compute_temporal_baseline(np.full((3, 3), 290.0))


# ---------------------------------------------------------------------------
# compute_contextual_ring
# ---------------------------------------------------------------------------

def test_ring_hot_center_cold_neighbors():
    bt = np.full((11, 11), 290.0)
    bt[5, 5] = 320.0

    stats = compute_contextual_ring(bt, row=5, col=5, ring_radius_px=4,
                                    inner_exclude_px=1)

    assert stats["n_valid"] > 0
    assert abs(stats["mean"] - 290.0) < 0.5
    assert stats["center_dt"] > 25.0


def test_ring_uniform_field_center_dt_zero():
    bt = np.full((9, 9), 295.0)
    stats = compute_contextual_ring(bt, row=4, col=4, ring_radius_px=3)

    assert abs(stats["center_dt"]) < 1e-9
    assert abs(stats["std"]) < 1e-9


def test_ring_off_grid_returns_nan():
    bt = np.full((5, 5), 290.0)
    stats = compute_contextual_ring(bt, row=10, col=10, ring_radius_px=2)

    assert np.isnan(stats["center_dt"])
    assert stats["n_valid"] == 0


def test_ring_edge_pixel_partial_neighborhood():
    bt = np.full((10, 10), 290.0)
    bt[0, 0] = 320.0

    stats = compute_contextual_ring(bt, row=0, col=0, ring_radius_px=3)

    assert stats["n_valid"] > 0
    assert stats["center_dt"] > 25.0


def test_ring_all_nan_neighbors_returns_nan():
    bt = np.full((7, 7), np.nan)
    bt[3, 3] = 320.0

    stats = compute_contextual_ring(bt, row=3, col=3, ring_radius_px=2)

    assert stats["n_valid"] == 0
    assert np.isnan(stats["mean"])


# ---------------------------------------------------------------------------
# Constantes paper
# ---------------------------------------------------------------------------

def test_paper_constants_match_vault():
    assert TIRVOLCH_T_ABS_MIN_K == 313.15
    assert TIRVOLCH_Z_THRESHOLD == 7.0
    assert TIRVOLCH_DT_MIN_K == 0.5


# ---------------------------------------------------------------------------
# Integration smoke
# ---------------------------------------------------------------------------

def test_pipeline_baseline_then_detect():
    rng = np.random.default_rng(seed=7)
    n_history = 30
    shape = (6, 6)

    history = 290.0 + rng.normal(0, 0.3, size=(n_history, *shape))
    mean, sigma = compute_temporal_baseline(history)

    new_scene = 290.0 + rng.normal(0, 0.3, size=shape)
    new_scene[3, 3] = 325.0

    mask = detect_tirvolch(new_scene, mean, sigma)

    assert mask[3, 3] == True
    n_fp = int(mask.sum()) - 1
    assert n_fp <= 1
