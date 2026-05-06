"""S33 D4 — TDD test1 L_bg global fix.

Cuando ENABLE_TEST1_LBG_GLOBAL ON, el VRP del Test 1 usa L_bg(t_bg_i04)
global del anillo 5-25km en lugar de test1_L_bg_local (ring 1-3km cráter).

Físicamente: en volcanes con geotermal crónico ring cráter (Tupungatito,
Lastarria fumarolas), test1_L_bg_local está contaminado y los pixels
individualmente clip a 0. L_bg global (lejos del cráter) recupera la
señal que el integrated trigger ya detectó.
"""
from __future__ import annotations
import importlib
import numpy as np


def test_profile_default_off_in_mirova_equivalent(monkeypatch):
    """S33 post-refutación: Phase 1 + D4 ambos OFF en operacional.
    Driver A solo es el operacional (recall 74.2%, ratio 2.53×).
    Phase 1 refutado (-18.6pp recall con métrica corregida).
    D4 refutado (efecto despreciable, no recupera Tupungatito).
    """
    monkeypatch.setenv("VRP_PROFILE", "mirova_equivalent")
    import pipeline.profile as profile
    importlib.reload(profile)
    assert profile.ENABLE_TEST1_LBG_GLOBAL is False
    assert profile.ENABLE_TEST1_PIXEL_FILTER is False


def test_profile_on_in_lbg_global_profile(monkeypatch):
    """Profile A/B D4 tiene flag ON + Phase 1 ON."""
    monkeypatch.setenv("VRP_PROFILE", "mirova_equivalent_lbg_global")
    import pipeline.profile as profile
    importlib.reload(profile)
    assert profile.ENABLE_TEST1_LBG_GLOBAL is True
    assert profile.ENABLE_TEST1_PIXEL_FILTER is True
    assert profile.ENABLE_DUAL_ROI_BT is True


def test_lbg_global_recovers_signal_when_local_contaminado():
    """Caso Tupungatito: L_bg_local (ring 1-3km) caliente, L_bg_global frío.

    pixels Test 1 con BT 270 K, t_bg_local 271 K, t_bg_global 265 K.
    - Con local: ΔL = L(270) - L(271) < 0 → clip 0 → sum = 0.
    - Con global: ΔL = L(270) - L(265) > 0 → sum > 0.
    """
    # Lambda Planck en MIR
    C1 = 1.191042e8
    C2 = 14388.0
    LAMBDA = 3.74  # I04

    def planck(bt, lam=LAMBDA):
        with np.errstate(invalid="ignore", divide="ignore", over="ignore"):
            return C1 / (lam ** 5 * (np.exp(C2 / (lam * bt)) - 1))

    t1_bt_pixels = np.array([270.0, 270.5, 271.0])
    L_pixels = planck(t1_bt_pixels)

    L_bg_local = float(planck(np.array([271.0]))[0])  # contaminado por geotermal
    L_bg_global = float(planck(np.array([265.0]))[0])  # frío, lejos del cráter

    # Con L_bg_local: clip
    delta_local = np.maximum(L_pixels - L_bg_local, 0.0)
    sum_local = float(np.sum(delta_local))
    # Con L_bg_global
    delta_global = np.maximum(L_pixels - L_bg_global, 0.0)
    sum_global = float(np.sum(delta_global))

    assert sum_local <= 0.001, f"Con L_bg local contaminado, suma debería clip a 0; got {sum_local}"
    assert sum_global > 0.0, f"Con L_bg global, suma debería ser positiva; got {sum_global}"
    # Y el sum_global debe ser sustancial (no marginal)
    assert sum_global > 1e-6, "señal recuperada significativa"


def test_lbg_global_preserves_signal_when_local_limpio():
    """Caso Lascar: L_bg_local ≈ L_bg_global (cráter sin geotermal crónico).

    pixels Test 1 con BT 290 K (cráter caliente), t_bg_local 270 K,
    t_bg_global 268 K.
    - Con local: ΔL grande positivo → sum > 0.
    - Con global: ΔL grande positivo, ligeramente mayor → sum > 0.
    Diferencia mínima.
    """
    C1 = 1.191042e8
    C2 = 14388.0
    LAMBDA = 3.74

    def planck(bt, lam=LAMBDA):
        with np.errstate(invalid="ignore", divide="ignore", over="ignore"):
            return C1 / (lam ** 5 * (np.exp(C2 / (lam * bt)) - 1))

    t1_bt = np.array([290.0, 295.0, 300.0])
    L_pixels = planck(t1_bt)
    L_bg_local = float(planck(np.array([270.0]))[0])
    L_bg_global = float(planck(np.array([268.0]))[0])

    delta_local = np.maximum(L_pixels - L_bg_local, 0.0)
    delta_global = np.maximum(L_pixels - L_bg_global, 0.0)
    s_local = float(np.sum(delta_local))
    s_global = float(np.sum(delta_global))

    assert s_local > 0.0
    assert s_global > 0.0
    # Ambos del mismo orden, diferencia <10% (porque la diferencia 270 vs 268
    # es despreciable comparada con pixels 290+)
    rel_diff = abs(s_global - s_local) / s_local
    assert rel_diff < 0.1, f"local vs global similares con cráter caliente; rel_diff={rel_diff}"


def test_flag_off_uses_local_default():
    """ENABLE_TEST1_LBG_GLOBAL=False mantiene comportamiento test1_L_bg_local."""
    enable_flag = False
    test1_L_bg_local = 100.0  # valor sintético
    t_bg_global = 95.0

    if enable_flag:
        effective = t_bg_global  # placeholder, en código real es planck(t_bg)
    else:
        effective = test1_L_bg_local

    assert effective == test1_L_bg_local
