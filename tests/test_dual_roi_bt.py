"""S26 T1+T2 — TDD para dual-ROI N·σ en eruption-path BT (Coppola 2016a Tabla 1).

Validación que helper aplica thresholds distintos summit (5σ) vs scene (10σ),
respetando floor (ANOMALY_THRESHOLD_K) y cap (MAX_SIGMA_COMPONENT_K).
"""
from __future__ import annotations

import importlib
import os

import numpy as np
import pytest


# === T1: profile keys ===

def test_profile_loads_dual_roi_bt_keys(monkeypatch):
    """ENABLE_DUAL_ROI_BT y N_SIGMA_MIR_{SUMMIT,SCENE} deben cargarse del YAML."""
    monkeypatch.setenv("VRP_PROFILE", "_dual_roi_bt_enabled")
    import pipeline.profile as profile
    importlib.reload(profile)
    assert profile.ENABLE_DUAL_ROI_BT is True
    assert profile.N_SIGMA_MIR_SUMMIT == 5.0
    assert profile.N_SIGMA_MIR_SCENE == 10.0


def test_profile_default_state_post_s27(monkeypatch):
    """S27: dual-ROI BT activado en mirova_equivalent operacional.

    Pre-S27 (este test originalmente): default OFF mientras se validaba A/B.
    S27 (commit 2026-04-29): A/B validado, dual-ROI BT pasa a operacional con
    5σ summit / 10σ scene Coppola 2016a Tabla 1. Ver pipeline/profiles/mirova_equivalent.yaml
    enable_dual_roi_bt: true.
    """
    monkeypatch.setenv("VRP_PROFILE", "mirova_equivalent")
    import pipeline.profile as profile
    importlib.reload(profile)
    assert profile.ENABLE_DUAL_ROI_BT is True
    assert profile.N_SIGMA_MIR_SUMMIT == 5.0
    assert profile.N_SIGMA_MIR_SCENE == 10.0


# === T2: helper dual_roi_bt_threshold ===
# Importado dentro de los tests porque la función aún no existe (TDD red).

def test_dual_roi_bt_summit_lower_threshold_than_scene():
    """Mismo pixel +4K: summit (5σ=2.5K) pasa, scene (10σ=5K) NO pasa."""
    from pipeline.detection_context import dual_roi_bt_threshold
    bt = np.full((10, 10), 270.0)
    bt[5, 5] = 274.0  # +4K
    roi_mask = np.ones((10, 10), dtype=bool)
    t_bg = 270.0
    std_bg = 0.5  # 5σ=2.5K, 10σ=5K

    # Caso summit: pixel a 1km del vent (dentro inner=3km)
    dist_summit = np.full((10, 10), 5.0)  # mostly scene
    dist_summit[5, 5] = 1.0  # this pixel summit
    hot_summit = dual_roi_bt_threshold(
        bt=bt, roi_mask=roi_mask, dist_km=dist_summit, t_bg=t_bg, std_bg=std_bg,
        inner_km=3.0, n_sigma_summit=5.0, n_sigma_scene=10.0,
        anomaly_floor_k=2.0, max_sigma_cap_k=7.0,
    )
    assert hot_summit[5, 5] == True, "summit pixel +4K (5σ=2.5K) debería disparar"

    # Caso scene: mismo pixel pero a 5km del vent (fuera inner)
    dist_scene = np.full((10, 10), 5.0)
    hot_scene = dual_roi_bt_threshold(
        bt=bt, roi_mask=roi_mask, dist_km=dist_scene, t_bg=t_bg, std_bg=std_bg,
        inner_km=3.0, n_sigma_summit=5.0, n_sigma_scene=10.0,
        anomaly_floor_k=2.0, max_sigma_cap_k=7.0,
    )
    assert hot_scene[5, 5] == False, "scene pixel +4K (10σ=5K) NO debería disparar"


def test_dual_roi_bt_respects_anomaly_floor():
    """Si N·σ < floor, threshold = floor (Coppola 2015 ANOMALY_THRESHOLD_K)."""
    from pipeline.detection_context import dual_roi_bt_threshold
    bt = np.full((5, 5), 270.0)
    bt[2, 2] = 272.5  # +2.5K
    dist_km = np.zeros((5, 5))  # todo summit
    roi_mask = np.ones((5, 5), dtype=bool)
    hot = dual_roi_bt_threshold(
        bt=bt, roi_mask=roi_mask, dist_km=dist_km, t_bg=270.0, std_bg=0.1,
        inner_km=3.0, n_sigma_summit=5.0, n_sigma_scene=10.0,
        anomaly_floor_k=2.0, max_sigma_cap_k=7.0,
    )
    # 5·0.1=0.5K < floor 2K, threshold efectivo summit = 2K. +2.5K pasa.
    assert hot[2, 2] == True


def test_dual_roi_bt_respects_sigma_cap():
    """Si N·σ > cap, threshold = cap (S15 Tema F MAX_SIGMA_COMPONENT_K=7K)."""
    from pipeline.detection_context import dual_roi_bt_threshold
    bt = np.full((5, 5), 270.0)
    bt[2, 2] = 277.5  # +7.5K
    dist_km = np.full((5, 5), 5.0)  # todo scene
    roi_mask = np.ones((5, 5), dtype=bool)
    hot = dual_roi_bt_threshold(
        bt=bt, roi_mask=roi_mask, dist_km=dist_km, t_bg=270.0, std_bg=2.0,
        inner_km=3.0, n_sigma_summit=5.0, n_sigma_scene=10.0,
        anomaly_floor_k=2.0, max_sigma_cap_k=7.0,
    )
    # 10·2=20K → capped a 7K. +7.5K pasa.
    assert hot[2, 2] == True


def test_dual_roi_bt_excludes_outside_roi():
    """roi_mask=False → siempre False sin importar BT."""
    from pipeline.detection_context import dual_roi_bt_threshold
    bt = np.full((5, 5), 290.0)  # MUY caliente
    dist_km = np.zeros((5, 5))
    roi_mask = np.zeros((5, 5), dtype=bool)  # nada en ROI
    hot = dual_roi_bt_threshold(
        bt=bt, roi_mask=roi_mask, dist_km=dist_km, t_bg=270.0, std_bg=0.5,
        inner_km=3.0, n_sigma_summit=5.0, n_sigma_scene=10.0,
        anomaly_floor_k=2.0, max_sigma_cap_k=7.0,
    )
    assert not hot.any()


def test_dual_roi_bt_handles_nan():
    """Pixels con BT=NaN nunca deben ser hot."""
    from pipeline.detection_context import dual_roi_bt_threshold
    bt = np.full((5, 5), 270.0)
    bt[2, 2] = np.nan
    dist_km = np.zeros((5, 5))
    roi_mask = np.ones((5, 5), dtype=bool)
    hot = dual_roi_bt_threshold(
        bt=bt, roi_mask=roi_mask, dist_km=dist_km, t_bg=270.0, std_bg=0.5,
        inner_km=3.0, n_sigma_summit=5.0, n_sigma_scene=10.0,
        anomaly_floor_k=2.0, max_sigma_cap_k=7.0,
    )
    assert hot[2, 2] == False


# === Regla D Test 1-priority (S26 D fix) ===
# Validación schema-source: el código contiene la lógica que prioriza Test 1
# cuando dispara summit y eruption hotspot está far.

def test_regla_d_test1_priority_logic_present_in_process_viirs():
    """process_viirs.py debe contener la cascada Regla D Test 1-priority.

    Anti-regresión del fix S26 D — si alguien remueve la lógica que
    prioriza Test 1 sobre eruption-far, el recall Villarrica volverá a 0.
    """
    from pathlib import Path
    src = Path("pipeline/process_viirs.py").read_text(encoding="utf-8")
    # Marker comment del fix
    assert "Regla D Test 1-priority" in src, \
        "Regla D Test 1 lógica removida — recall Villarrica regresaría a 0"
    # S111: la lógica de prioridad Test1 se centralizó en el helper puro
    # resolve_test1_source_priority (test1_integrated.py). process_viirs lo USA;
    # el helper contiene la Regla D clásica. Anti-regresión adaptado al refactor.
    assert "resolve_test1_source_priority" in src, \
        "Helper de prioridad Test1 (Regla D + cluster débil) no usado en process_viirs"
    from pathlib import Path as _P
    _t1src = _P("pipeline/test1_integrated.py").read_text(encoding="utf-8")
    assert "test1_summit_hit and eruption_far" in _t1src, \
        "Combinación test1_summit_hit + eruption_far rota en el helper"
    assert 'final_hotspot_source = "test1"' in src, \
        "Asignación final_hotspot_source=\"test1\" rota"


def test_vrp_recompute_test1_only_logic_present():
    """Anti-regresión S26 D fix magnitud: cuando source=test1 → VRP solo
    sobre Test 1 mask. Sin esto, Villarrica reporta 562 MW vs MIROVA 0.05
    porque pixels far inflan el sum.
    """
    from pathlib import Path
    src = Path("pipeline/process_viirs.py").read_text(encoding="utf-8")
    assert "vrp_mir_mw_test1_only" in src, \
        "Recálculo VRP_MIR solo Test 1 mask removido"
    assert 'final_hotspot_source == "test1"' in src, \
        "Guard `if source==test1 → recompute VRP` rota"
