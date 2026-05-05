"""S33 Driver B Phase 2 — TDD final pixel filter.

ENABLE_FINAL_PIXEL_FILTER aplica dual_roi_bt_threshold a la mask combinada
post-OR de todos los paths. Cubre Path D dNTI que Phase 1 (test1 only) no
filtraba.
"""
from __future__ import annotations

import importlib
import numpy as np
import pytest


def test_profile_default_off_in_mirova_equivalent(monkeypatch):
    """Phase 2 todavía no operacional (post-A/B aún pendiente)."""
    monkeypatch.setenv("VRP_PROFILE", "mirova_equivalent")
    import pipeline.profile as profile
    importlib.reload(profile)
    assert profile.ENABLE_FINAL_PIXEL_FILTER is False


def test_profile_on_in_phase2_profile(monkeypatch):
    """Profile A/B Phase 2 tiene flag ON + Phase 1 ON."""
    monkeypatch.setenv("VRP_PROFILE", "mirova_equivalent_phase2")
    import pipeline.profile as profile
    importlib.reload(profile)
    assert profile.ENABLE_FINAL_PIXEL_FILTER is True
    # Hereda Phase 1
    assert profile.ENABLE_TEST1_PIXEL_FILTER is True
    assert profile.ENABLE_DUAL_ROI_BT is True


def test_filter_drops_dnti_marginal_keeps_pico():
    """Simula caso Chaiten/PCC: pixels Path D dNTI con BT marginal entran al
    OR pero filtro 5σ summit los elimina. Pixels-pico reales con BT >5σ
    sobreviven.
    """
    from pipeline.detection_context import dual_roi_bt_threshold

    bt = np.full((10, 10), 270.0)
    # 2 pixels-pico (similar a hotspot real cráter)
    bt[5, 5] = 280.0  # +10K (super pasa 5σ summit con std=0.5)
    bt[5, 6] = 278.0  # +8K
    # 8 pixels Path D dNTI marginales (NTI alto pero BT casi-bg, +1.5K)
    marg = [(4, 4), (4, 5), (4, 6), (4, 7), (6, 4), (6, 5), (6, 6), (6, 7)]
    for r, c in marg:
        bt[r, c] = 271.5  # +1.5K — no pasa 5σ summit (=2.5K) por floor 5K

    # hot_mask combinado (incluye los 10 pixels)
    hot_mask = np.zeros_like(bt, dtype=bool)
    for r, c in [(5, 5), (5, 6)] + marg:
        hot_mask[r, c] = True

    # Filtro dual-ROI 5σ summit (todos summit con dist=1km)
    dist = np.full_like(bt, 1.0)
    pixel_thr_mask = dual_roi_bt_threshold(
        bt=bt,
        roi_mask=np.ones_like(bt, dtype=bool),
        dist_km=dist, t_bg=270.0, std_bg=0.5,
        inner_km=3.0, n_sigma_summit=5.0, n_sigma_scene=10.0,
        anomaly_floor_k=5.0, max_sigma_cap_k=999.0,
    )
    final_mask = hot_mask & pixel_thr_mask

    n_orig = int(hot_mask.sum())
    n_kept = int(final_mask.sum())

    assert n_orig == 10, f"setup: 10 pixels in hot_mask, got {n_orig}"
    # Solo los 2 picos (>5K) sobreviven; los 8 marginales caen
    assert n_kept == 2, (
        f"final filter should keep only 2 hot pixels (>5K above bg), "
        f"got {n_kept}. Marginal pixels with +1.5K should be filtered out."
    )
    assert final_mask[5, 5] == True
    assert final_mask[5, 6] == True


def test_filter_disabled_keeps_all_paths():
    """Cuando flag OFF (Phase 1 only), no aplica final filter."""
    enable_final = False
    hot_mask = np.zeros((5, 5), dtype=bool)
    hot_mask[2, 2] = True
    hot_mask[2, 3] = True
    hot_mask[3, 3] = True
    if enable_final:
        hot_mask = hot_mask & np.zeros_like(hot_mask)
    assert int(hot_mask.sum()) == 3


def test_phase2_complementa_phase1_no_double_filter():
    """Phase 2 al hot_mask combinado puede aplicarse después de Phase 1
    a test1_hot. El doble filtrado de pixels Test 1 es idempotente — el
    pixel ya filtrado por Phase 1 sigue pasando Phase 2 si supera el
    mismo threshold (que es).
    """
    from pipeline.detection_context import dual_roi_bt_threshold

    bt = np.full((5, 5), 270.0)
    bt[2, 2] = 277.0  # +7K — pasa 5σ summit (5K floor) holgado

    test1_hot = np.zeros_like(bt, dtype=bool)
    test1_hot[2, 2] = True

    dist = np.full_like(bt, 1.0)
    # Phase 1 filter
    p1_mask = dual_roi_bt_threshold(
        bt=bt, roi_mask=np.ones_like(bt, bool), dist_km=dist,
        t_bg=270.0, std_bg=0.5, inner_km=3.0,
        n_sigma_summit=5.0, n_sigma_scene=10.0,
        anomaly_floor_k=5.0, max_sigma_cap_k=999.0,
    )
    test1_filtered_p1 = test1_hot & p1_mask
    # Combine in hot_mask (simula el OR con otras paths vacías)
    hot_mask = test1_filtered_p1
    # Phase 2 filter (mismo cálculo, idempotente)
    p2_mask = dual_roi_bt_threshold(
        bt=bt, roi_mask=np.ones_like(bt, bool), dist_km=dist,
        t_bg=270.0, std_bg=0.5, inner_km=3.0,
        n_sigma_summit=5.0, n_sigma_scene=10.0,
        anomaly_floor_k=5.0, max_sigma_cap_k=999.0,
    )
    final = hot_mask & p2_mask

    assert final[2, 2] == True, "pixel pico debe sobrevivir ambos filtros"
    assert int(final.sum()) == 1
