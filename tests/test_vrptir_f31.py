"""Tests F31 VRPTIR Aveni 2025 GRL — fórmula standalone.

Verifica la matemática de Eq.8 y Eq.9 contra valores conocidos del paper
y casos sintéticos VRP Chile. Tests UNIT — no requieren pipeline real.

**STATUS S74**: experimental — k_TIR=60.17 + rango 300-600K de notas Vault
`aveni2025volcanic.md` (confidence:medium per A35). Antes de adoptar pipeline
operacional, verificar contra PDF original.

Refs:
- pipeline/vrptir.py
- docs/F31_AVENI_VRPTIR_PLAN_S74.md
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from pipeline.vrptir import (
    A_PIX_MODIS,
    A_PIX_VIIRS_I,
    A_PIX_VIIRS_M,
    LAMBDA_MODIS_B31,
    LAMBDA_VIIRS_I5,
    LAMBDA_VIIRS_M15,
    VRPTIR_T_MAX_K,
    VRPTIR_T_MIN_K,
    filter_t_range,
    k_tir,
    planck_radiance,
    vrp_tir,
    vrp_tir_mw,
)


# Eq.8 — k_TIR(λ) coefficient

def test_k_tir_viirs_i5_matches_paper():
    """k_TIR(11.45 µm) ≈ 60.17 m·sr per Aveni 2025 GRL Vault note."""
    assert abs(k_tir(LAMBDA_VIIRS_I5) - 60.17) < 0.5, (
        f"VIIRS I5 k_TIR = {k_tir(LAMBDA_VIIRS_I5):.3f}, esperado ~60.17"
    )


def test_k_tir_viirs_m15_plausible():
    k = k_tir(LAMBDA_VIIRS_M15)
    assert 50.0 < k < 80.0, f"M15 k_TIR fuera de rango plausible: {k:.3f}"


def test_k_tir_modis_b31_plausible():
    k = k_tir(LAMBDA_MODIS_B31)
    assert 50.0 < k < 80.0, f"MODIS B31 k_TIR fuera de rango plausible: {k:.3f}"


def test_k_tir_monotone_in_thermal_range():
    assert k_tir(10.0) < k_tir(11.0) < k_tir(12.0)


# Planck radiance helper

def test_planck_scalar_vs_array():
    scalar = planck_radiance(400.0, LAMBDA_VIIRS_I5)
    arr = planck_radiance([400.0, 400.0], LAMBDA_VIIRS_I5)
    assert abs(scalar - arr[0]) < 1e-9


def test_planck_increases_with_bt():
    assert planck_radiance(500.0, LAMBDA_VIIRS_I5) > planck_radiance(300.0, LAMBDA_VIIRS_I5)


def test_planck_temperature_inverse_consistent():
    T = 400.0
    L = planck_radiance(T, LAMBDA_VIIRS_I5)
    C1, C2 = 1.1910429e8, 1.4387752e4
    T_back = C2 / (LAMBDA_VIIRS_I5 * math.log(C1 / (L * LAMBDA_VIIRS_I5**5) + 1))
    assert abs(T_back - T) < 0.01


# Eq.9 — VRP_TIR formula

def test_vrp_tir_zero_when_no_hot():
    assert vrp_tir([], 280.0, LAMBDA_VIIRS_I5, A_PIX_VIIRS_I) == 0.0


def test_vrp_tir_zero_when_bt_equal_bg():
    assert abs(vrp_tir([280.0] * 5, 280.0, LAMBDA_VIIRS_I5, A_PIX_VIIRS_I)) < 1e-3


def test_vrp_tir_positive_when_hot_above_bg():
    result = vrp_tir([400.0] * 4, 280.0, LAMBDA_VIIRS_I5, A_PIX_VIIRS_I)
    assert result > 0


def test_vrp_tir_scales_with_npixels():
    v4 = vrp_tir([400.0] * 4, 280.0, LAMBDA_VIIRS_I5, A_PIX_VIIRS_I)
    v8 = vrp_tir([400.0] * 8, 280.0, LAMBDA_VIIRS_I5, A_PIX_VIIRS_I)
    assert abs(v8 / v4 - 2.0) < 0.01


def test_vrp_tir_negative_delta_clipped_to_zero():
    v_all = vrp_tir([400.0, 400.0, 250.0, 250.0], 280.0, LAMBDA_VIIRS_I5, A_PIX_VIIRS_I)
    v_hot_only = vrp_tir([400.0, 400.0], 280.0, LAMBDA_VIIRS_I5, A_PIX_VIIRS_I)
    assert abs(v_all - v_hot_only) < 1e-3


def test_vrp_tir_mw_villarrica_lava_lake_scenario():
    """Smoke: 4 pixels VIIRS I5 a 450K sobre BG 280K — Villarrica lava lake plausible.

    Math sanity: A_pix=140625 × k=60.17 × ΔL ≈ 8.46e6 × ΔL per pixel.
    ΔL @ 450K vs 280K = ~33 W/m²/sr/µm. 4 pixels × 33 × 8.46e6 ≈ 1.1 GW.
    Valor alto vs MIROVA Villarrica NRT típico (0.1-50 MW) es ESPERADO: claim
    Aveni "Wooster subestima 90% sub-pixel <600K" — VRPTIR captura señal pérdida.
    """
    vrp = vrp_tir_mw([450.0] * 4, 280.0, LAMBDA_VIIRS_I5, A_PIX_VIIRS_I)
    assert 500.0 < vrp < 2000.0, f"VRP fuera rango sanity: {vrp:.2f} MW"


# T-range filter

def test_filter_t_range_basic():
    bts = np.array([250.0, 300.0, 400.0, 600.0, 700.0, np.nan])
    mask = filter_t_range(bts)
    expected = np.array([False, True, True, True, False, False])
    np.testing.assert_array_equal(mask, expected)


def test_filter_t_range_custom():
    bts = np.array([350.0, 450.0, 550.0])
    mask = filter_t_range(bts, t_min=400.0, t_max=500.0)
    expected = np.array([False, True, False])
    np.testing.assert_array_equal(mask, expected)


# Constantes consistency

def test_a_pix_values_match_sensor_specs():
    assert A_PIX_VIIRS_I == 375 * 375
    assert A_PIX_VIIRS_M == 750 * 750
    assert A_PIX_MODIS == 1000 * 1000


def test_t_range_constants_match_paper():
    assert VRPTIR_T_MIN_K == 300.0
    assert VRPTIR_T_MAX_K == 600.0


# Integration / scenario

def test_vrptir_complementary_to_wooster_below_600k():
    """5 pixels VIIRS I5 a 500K sobre BG 270K → VRPTIR produce señal sustantiva.

    Math: 5 × A_pix × k × ΔL_TIR(500-270). Aveni: VRPTIR captura lo que Wooster
    subestima 90% sub-pixel <600K. Magnitudes en orden 1-5 GW para escenas activas.
    """
    vrp = vrp_tir_mw([500.0] * 5, 270.0, LAMBDA_VIIRS_I5, A_PIX_VIIRS_I)
    assert 1000.0 < vrp < 5000.0, f"VRP fuera sanity: {vrp:.2f} MW"


def test_vrptir_handles_nan_input():
    vrp_with_nan = vrp_tir([400.0, np.nan, 400.0], 280.0, LAMBDA_VIIRS_I5, A_PIX_VIIRS_I)
    vrp_no_nan = vrp_tir([400.0, 400.0], 280.0, LAMBDA_VIIRS_I5, A_PIX_VIIRS_I)
    assert abs(vrp_with_nan - vrp_no_nan) < 1e-3
