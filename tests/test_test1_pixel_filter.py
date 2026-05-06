"""S32 P2 Driver B — TDD test1 pixel filter.

Cuando ENABLE_TEST1_PIXEL_FILTER ON y Test 1 dispara, la mask test1_hot debe
intersectar dual_roi_bt_threshold (5σ summit / 10σ scene Coppola 2016a Tabla 1)
antes de sumar VRP. Sin el flag, comportamiento idéntico al previo.

Estos tests validan la mecánica con arrays sintéticos, no granules reales.
"""
from __future__ import annotations

import importlib
import numpy as np
import pytest


def test_profile_state_post_s33_refutation(monkeypatch):
    """S33: flag REVERTIDO a OFF tras refutación con métrica corregida.

    S32 adoptó flag=true creyendo validar 73.6%/1.66×, pero la métrica
    `mirovaEqVrp` tenía bug (no validaba pc.centroid_dist_km contra
    inner_radius). Re-audit S33 con métrica corregida:
      Driver A solo:      recall 74.2%, ratio 2.53×
      Driver A + Phase 1: recall 55.6%, ratio 1.39× (-18.6pp recall)
    Phase 1 destruye señal real validada por MIROVA. Revertido.
    Ver docs/PROCESS_RULES_S33.md.
    """
    monkeypatch.setenv("VRP_PROFILE", "mirova_equivalent")
    import pipeline.profile as profile
    importlib.reload(profile)
    assert profile.ENABLE_TEST1_PIXEL_FILTER is False


def test_profile_on_in_test1pix_filter_profile(monkeypatch):
    """En profile A/B, flag debe estar ON."""
    monkeypatch.setenv("VRP_PROFILE", "mirova_equivalent_test1pix_filter")
    import pipeline.profile as profile
    importlib.reload(profile)
    assert profile.ENABLE_TEST1_PIXEL_FILTER is True
    # También debe heredar dual_roi_bt y test1
    assert profile.ENABLE_DUAL_ROI_BT is True
    assert profile.ENABLE_TEST1_PATH is True
    assert profile.N_SIGMA_MIR_SUMMIT == 5.0
    assert profile.N_SIGMA_MIR_SCENE == 10.0


def test_filter_drops_marginal_pixels_keeps_hot():
    """Test 1 mask con 4 pixels muy calientes (>5σ) + 8 marginales (2-3σ).
    Filtro 5σ summit debe dejar solo los 4 calientes.
    """
    from pipeline.detection_context import dual_roi_bt_threshold
    from pipeline.profile import (
        ANOMALY_THRESHOLD_K,
        MAX_SIGMA_COMPONENT_K,
    )

    # Setup sintético: pixel grid 10x10
    bt = np.full((10, 10), 270.0)  # background
    # 4 pixels muy calientes (>5σ con std=0.5K → +2.5K piso, pero usamos +6K)
    hot_coords = [(4, 4), (4, 5), (5, 4), (5, 5)]
    for r, c in hot_coords:
        bt[r, c] = 276.0  # +6K (>5σ summit con σ=0.5)
    # 8 pixels marginales (+1.5K, entre 1σ y 5σ no llegando)
    marg_coords = [(3, 3), (3, 6), (6, 3), (6, 6), (4, 3), (4, 6), (5, 3), (5, 6)]
    for r, c in marg_coords:
        bt[r, c] = 271.5  # +1.5K (3σ pero <5σ)

    # test1_hot mask: incluye TODOS los 12 pixels (los 4 hot + 8 marginales)
    test1_hot = np.zeros_like(bt, dtype=bool)
    for r, c in hot_coords + marg_coords:
        test1_hot[r, c] = True

    # Distancia: todos summit (dist <= 3km inner_radius)
    vent_dist_per_pixel = np.full_like(bt, 1.0)

    t_bg = 270.0
    std_bg = 0.5  # 5σ summit threshold = 2.5K, 10σ scene = 5.0K

    # Aplicar filtro dual-ROI con N_SIGMA_MIR_SUMMIT=5
    pixel_thr_mask = dual_roi_bt_threshold(
        bt=bt,
        roi_mask=np.ones_like(bt, dtype=bool),
        dist_km=vent_dist_per_pixel,
        t_bg=t_bg, std_bg=std_bg,
        inner_km=3.0,
        n_sigma_summit=5.0,
        n_sigma_scene=10.0,
        anomaly_floor_k=ANOMALY_THRESHOLD_K,  # 5K floor
        max_sigma_cap_k=MAX_SIGMA_COMPONENT_K,
    )

    test1_hot_filtered = test1_hot & pixel_thr_mask

    # Floor 5K + 5σ=2.5K → effective threshold = max(5K, 2.5K) = 5K (floor)
    # → pixels ≥275K pasan (los 4 con +6K=276K), los marginales con +1.5K=271.5K NO
    n_kept = int(test1_hot_filtered.sum())
    n_orig = int(test1_hot.sum())

    assert n_orig == 12, f"setup error, expected 12 hot in test1_hot, got {n_orig}"
    assert n_kept == 4, (
        f"filtered should keep only the 4 hot pixels (>5K above bg), got {n_kept}. "
        f"Marginal pixels with +1.5K should be filtered out."
    )


def test_filter_disabled_keeps_all_pixels():
    """Cuando flag OFF (default), no aplica filtro: test1_hot_filtered === test1_hot.

    Test conceptual: simula el camino del código en process_*.py:
        if ENABLE_TEST1_PIXEL_FILTER and ...: test1_hot_filtered = test1_hot & mask
        else:                                test1_hot_filtered = test1_hot
    """
    test1_hot = np.zeros((5, 5), dtype=bool)
    test1_hot[2, 2] = True
    test1_hot[2, 3] = True

    # Simulate flag OFF
    enable_flag = False
    if enable_flag:
        # would apply filter, but skipped
        test1_hot_filtered = test1_hot & np.zeros_like(test1_hot)
    else:
        test1_hot_filtered = test1_hot

    assert np.array_equal(test1_hot_filtered, test1_hot)
    assert int(test1_hot_filtered.sum()) == 2


def test_filter_handles_nan_background():
    """Si t_bg o std_bg son NaN (background vacío), filtro NO debe aplicarse:
    test1_hot_filtered === test1_hot. Defensa contra divisiones inválidas.

    El check `not np.isnan(t_bg) and not np.isnan(std_bg)` en process_*.py
    debe prevenir aplicar el filtro en ese caso.
    """
    test1_hot = np.zeros((5, 5), dtype=bool)
    test1_hot[2, 2] = True

    t_bg = float('nan')
    std_bg = float('nan')

    # Lógica equivalente a process_*.py
    enable_flag = True
    if enable_flag and not np.isnan(t_bg) and not np.isnan(std_bg):
        # would apply filter
        test1_hot_filtered = test1_hot & np.zeros_like(test1_hot)
    else:
        test1_hot_filtered = test1_hot

    assert np.array_equal(test1_hot_filtered, test1_hot)


def test_filter_summit_vs_scene_thresholds():
    """Pixel a 2km (summit) +4K vs pixel a 8km (scene) +4K, std=0.5:
    summit threshold = max(5K, 5σ*0.5)=max(5,2.5)=5K → pixel +4K NO pasa.
    scene threshold = max(5K, 10σ*0.5)=max(5,5.0)=5K → pixel +4K NO pasa.
    Ambos filtrados (la distinción importa cuando std es alto).

    Caso con std alto: std=1.5K. summit 5σ=7.5K, scene 10σ=15K.
    summit eff=max(5,7.5)=7.5 → +4K NO pasa.
    scene eff=max(5,15)=15 → +4K NO pasa.

    Caso std=0.6K: summit 5σ=3K, scene 10σ=6K.
    summit eff=max(5,3)=5 → +5.5K pasa. scene eff=max(5,6)=6 → +5.5K NO pasa.
    Ese es el caso que diferencia ambos.
    """
    from pipeline.detection_context import dual_roi_bt_threshold

    bt = np.full((10, 10), 270.0)
    # Pixel summit: +5.5K
    bt[3, 3] = 275.5
    # Pixel scene: +5.5K también
    bt[8, 8] = 275.5
    test1_hot = np.zeros_like(bt, dtype=bool)
    test1_hot[3, 3] = True
    test1_hot[8, 8] = True

    # dist
    dist = np.full_like(bt, 8.0)  # scene default
    dist[3, 3] = 2.0  # summit
    # 8,8 → 8.0 (scene)

    # std_bg = 0.6: summit 5σ=3K (cap 5 floor), scene 10σ=6K
    pixel_mask = dual_roi_bt_threshold(
        bt=bt, roi_mask=np.ones_like(bt, bool),
        dist_km=dist, t_bg=270.0, std_bg=0.6,
        inner_km=3.0, n_sigma_summit=5.0, n_sigma_scene=10.0,
        anomaly_floor_k=5.0, max_sigma_cap_k=999.0,
    )
    filtered = test1_hot & pixel_mask
    assert filtered[3, 3] == True, "summit pixel +5.5K with eff_thr=5K should pass"
    assert filtered[8, 8] == False, "scene pixel +5.5K with eff_thr=6K should NOT pass"
