"""F52-B (S77, A45) — TDD tests para single_pixel_mode helper.

Spec: apply_single_pixel_mode() pure function ajusta primary_cluster.vrp_mw
cuando el cluster cae en régimen sub-MW (vrp_mw < threshold Y n_pixels <= max).
Reporta `max(per_pixel_vrp)` en vez de `sum`, alineado con MIROVA NRT
single-pixel reporting en sub-MW.

Referencias:
    pipeline/single_pixel_mode.py — helper bajo test
    pipeline/profiles/mirova_equivalent.yaml — drift T1.5 S72 (líneas 281-283)
    PRs #191 + #192 — audit completo del drift
"""
import math

import pytest

from pipeline.single_pixel_mode import apply_single_pixel_mode


def test_sub_mw_regime_triggers_single_pixel():
    """Cluster sub-MW (3 pixels, sum=2.5 MW < 5.0) → reporta max=1.2."""
    pc = {"vrp_mw": 2.5, "n_pixels": 3, "centroid_lat": -23.0, "centroid_lon": -67.5}
    out = apply_single_pixel_mode(
        pc, per_pixel_vrp=[1.2, 0.8, 0.5],
        enabled=True, threshold_mw=5.0, max_pixels=3,
    )
    assert out["vrp_mw"] == 1.2
    assert out["single_pixel_mode"] is True
    assert out["n_pixels"] == 3  # n_pixels intacto (informativo)
    # otras keys preservadas
    assert out["centroid_lat"] == -23.0


def test_above_threshold_passthrough():
    """Cluster vrp_mw_sum=10 MW >= threshold → passthrough sin cambio."""
    pc = {"vrp_mw": 10.0, "n_pixels": 3}
    out = apply_single_pixel_mode(
        pc, per_pixel_vrp=[5.0, 3.0, 2.0],
        enabled=True, threshold_mw=5.0, max_pixels=3,
    )
    assert out["vrp_mw"] == 10.0
    assert out["single_pixel_mode"] is False


def test_large_cluster_passthrough():
    """Cluster con n_pixels=5 (> max_pixels=3) → passthrough."""
    pc = {"vrp_mw": 2.5, "n_pixels": 5}
    out = apply_single_pixel_mode(
        pc, per_pixel_vrp=[0.7, 0.6, 0.5, 0.4, 0.3],
        enabled=True, threshold_mw=5.0, max_pixels=3,
    )
    assert out["vrp_mw"] == 2.5
    assert out["single_pixel_mode"] is False


def test_disabled_flag_passthrough():
    """Flag OFF → passthrough sin cambio incluso si régimen sub-MW."""
    pc = {"vrp_mw": 2.5, "n_pixels": 3}
    out = apply_single_pixel_mode(
        pc, per_pixel_vrp=[1.2, 0.8, 0.5],
        enabled=False, threshold_mw=5.0, max_pixels=3,
    )
    assert out["vrp_mw"] == 2.5
    assert "single_pixel_mode" not in out  # flag OFF no marca


def test_edge_single_pixel_exact_threshold():
    """Cluster 1 pixel a exactamente 5.0 MW → boundary, passthrough (>=)."""
    pc = {"vrp_mw": 5.0, "n_pixels": 1}
    out = apply_single_pixel_mode(
        pc, per_pixel_vrp=[5.0],
        enabled=True, threshold_mw=5.0, max_pixels=3,
    )
    # 5.0 NO es < 5.0 → passthrough
    assert out["vrp_mw"] == 5.0
    assert out["single_pixel_mode"] is False


def test_single_pixel_just_below_threshold():
    """Cluster 1 pixel a 4.99 MW → single-pixel mode (sub-MW)."""
    pc = {"vrp_mw": 4.99, "n_pixels": 1}
    out = apply_single_pixel_mode(
        pc, per_pixel_vrp=[4.99],
        enabled=True, threshold_mw=5.0, max_pixels=3,
    )
    assert out["vrp_mw"] == 4.99
    assert out["single_pixel_mode"] is True


def test_none_primary_cluster():
    """primary_cluster=None → return None."""
    out = apply_single_pixel_mode(
        None, per_pixel_vrp=[1.0],
        enabled=True, threshold_mw=5.0, max_pixels=3,
    )
    assert out is None


def test_empty_per_pixel_vrp_passthrough():
    """per_pixel_vrp vacío → passthrough sin marcar single-pixel mode."""
    pc = {"vrp_mw": 2.0, "n_pixels": 2}
    out = apply_single_pixel_mode(
        pc, per_pixel_vrp=[],
        enabled=True, threshold_mw=5.0, max_pixels=3,
    )
    assert out["vrp_mw"] == 2.0
    assert out["single_pixel_mode"] is False


def test_nan_filtered_in_per_pixel_vrp():
    """NaN en per_pixel_vrp se ignora; max sobre finitos."""
    pc = {"vrp_mw": 1.5, "n_pixels": 3}
    out = apply_single_pixel_mode(
        pc, per_pixel_vrp=[0.8, float("nan"), 0.4],
        enabled=True, threshold_mw=5.0, max_pixels=3,
    )
    assert out["vrp_mw"] == 0.8
    assert out["single_pixel_mode"] is True


def test_does_not_mutate_input_dict():
    """Pure function: no muta el primary_cluster de entrada."""
    pc = {"vrp_mw": 2.5, "n_pixels": 3}
    pc_orig = dict(pc)
    _ = apply_single_pixel_mode(
        pc, per_pixel_vrp=[1.2, 0.8, 0.5],
        enabled=True, threshold_mw=5.0, max_pixels=3,
    )
    assert pc == pc_orig  # entrada intacta


def test_tupungatito_canonical_case():
    """Caso canónico Tupungatito (ratio 30.15× pre-fix).

    Ejemplo sintético basado en audit PR #191: cluster 2 pixels suma ~3 MW
    cuando MIROVA reporta 0.1 MW (single pixel hottest). El fix reduce
    nuestro reporte al pixel más caliente, comprimiendo el ratio.
    """
    pc = {"vrp_mw": 3.0, "n_pixels": 2}
    out = apply_single_pixel_mode(
        pc, per_pixel_vrp=[2.0, 1.0],
        enabled=True, threshold_mw=5.0, max_pixels=3,
    )
    # Pre-fix: ratio 3.0/0.1 = 30×. Post-fix: ratio 2.0/0.1 = 20× (mejor,
    # aunque no perfecto — otros factores contribuyen al drift residual).
    assert out["vrp_mw"] == 2.0
    assert out["single_pixel_mode"] is True
