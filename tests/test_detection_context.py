"""Tests for contextual dNTI 8-neighbor mask (P3.2).

Fenomeno fisico: en una zona fumarolica heterogenea (Lastarria), el gate
global sigma_bg-anillo infla muchos pixels tibios. El gate contextual
8-vecinos exige que el pixel destaque vs sus vecinos inmediatos. Si la
zona completa esta tibia, los vecinos tambien -> dNTI chico -> rechazo.
Solo sobrevive el pixel verdaderamente localizado.

Referencia: Coppola et al. 2016 SP 426.5 "An enhanced automated thermal
anomaly detection", seccion "contextual NTI difference".
"""

import numpy as np
from pipeline.detection_context import (
    contextual_dnti_hot_mask,
    dual_roi_contextual_dnti_hot_mask,
)


def test_isolated_hotspot_passes():
    """Pixel con dNTI=+0.020 destacado del entorno = detectado."""
    nti = np.full((5, 5), -0.95, dtype=np.float64)
    nti[2, 2] = -0.93   # +0.02 sobre vecinos
    bt = np.full((5, 5), 285.0)
    bt[2, 2] = 295.0     # sanity BT pasa (+10K)
    roi = np.ones((5, 5), dtype=bool)
    mask = contextual_dnti_hot_mask(
        nti=nti, bt=bt, roi_mask=roi,
        t_bg=285.0, c1=0.003, bt_sanity_k=3.0)
    assert mask[2, 2] == True
    # Vecinos no deben pasar (son todos iguales entre si)
    mask[2, 2] = False
    assert not mask.any()


def test_uniformly_warm_region_rejected():
    """Toda la region uniformemente tibia (Lastarria): dNTI~0 en todos,
    ninguno pasa aunque BT este elevado."""
    nti = np.full((7, 7), -0.90, dtype=np.float64)
    bt = np.full((7, 7), 295.0)
    roi = np.ones((7, 7), dtype=bool)
    mask = contextual_dnti_hot_mask(
        nti=nti, bt=bt, roi_mask=roi,
        t_bg=285.0, c1=0.003, bt_sanity_k=3.0)
    assert not mask.any(), "Region uniformemente tibia no debe generar detecciones"


def test_bt_sanity_gate_blocks_cold_anomaly():
    """Pixel con dNTI anomalo pero BT bajo el sanity -> rechazo."""
    nti = np.full((5, 5), -0.95)
    nti[2, 2] = -0.90    # dNTI > c1
    bt = np.full((5, 5), 285.0)
    bt[2, 2] = 286.0      # solo +1K, menor que bt_sanity_k=3.0
    roi = np.ones((5, 5), dtype=bool)
    mask = contextual_dnti_hot_mask(
        nti=nti, bt=bt, roi_mask=roi,
        t_bg=285.0, c1=0.003, bt_sanity_k=3.0)
    assert mask[2, 2] == False


def test_outside_roi_rejected():
    """Pixel anomalo fuera del ROI -> no entra aunque dNTI pase."""
    nti = np.full((5, 5), -0.95)
    nti[0, 0] = -0.90
    bt = np.full((5, 5), 295.0)
    roi = np.ones((5, 5), dtype=bool)
    roi[0, 0] = False
    mask = contextual_dnti_hot_mask(
        nti=nti, bt=bt, roi_mask=roi,
        t_bg=285.0, c1=0.003, bt_sanity_k=3.0)
    assert mask[0, 0] == False


def test_nan_pixels_handled():
    """Pixels NaN en NTI (cloud, edge) no deben romper ni ser reportados hot."""
    nti = np.full((5, 5), -0.95)
    nti[2, 2] = np.nan
    nti[1, 1] = np.nan
    bt = np.full((5, 5), 295.0)
    roi = np.ones((5, 5), dtype=bool)
    mask = contextual_dnti_hot_mask(
        nti=nti, bt=bt, roi_mask=roi,
        t_bg=285.0, c1=0.003, bt_sanity_k=3.0)
    assert mask[2, 2] == False
    assert mask.shape == nti.shape


def test_c1_threshold_below_rejects_above_passes():
    """dNTI claramente bajo c1 se rechaza; claramente sobre se acepta.
    Coppola 2016a usa comparacion estricta > (no >=)."""
    # Caso 1: dNTI = 0.002 (claramente bajo 0.003) -> rechazo
    nti_below = np.full((5, 5), -0.95)
    nti_below[2, 2] = -0.948       # dNTI ~ 0.002
    bt = np.full((5, 5), 295.0)
    roi = np.ones((5, 5), dtype=bool)
    mask_below = contextual_dnti_hot_mask(
        nti=nti_below, bt=bt, roi_mask=roi,
        t_bg=285.0, c1=0.003, bt_sanity_k=3.0)
    assert mask_below[2, 2] == False

    # Caso 2: dNTI = 0.005 (claramente sobre 0.003) -> aceptacion
    nti_above = np.full((5, 5), -0.95)
    nti_above[2, 2] = -0.945       # dNTI ~ 0.005
    mask_above = contextual_dnti_hot_mask(
        nti=nti_above, bt=bt, roi_mask=roi,
        t_bg=285.0, c1=0.003, bt_sanity_k=3.0)
    assert mask_above[2, 2] == True


# ===================================================================
# P3.1 dual-ROI tests: summit vs scene con C1 distintos
# ===================================================================


def test_dual_roi_pixel_in_summit_passes_with_low_c1():
    """Pixel a 2 km del vent (summit si inner=5) con dNTI=0.005 pasa
    con c1_summit=0.003 pero fallaria con c1_scene=0.010."""
    nti = np.full((5, 5), -0.95)
    nti[2, 2] = -0.945       # dNTI ~ 0.005
    bt = np.full((5, 5), 295.0)
    roi = np.ones((5, 5), dtype=bool)
    dist = np.full((5, 5), 20.0)  # default lejos
    dist[2, 2] = 2.0              # este pixel a 2 km (summit)
    mask = dual_roi_contextual_dnti_hot_mask(
        nti=nti, bt=bt, roi_mask=roi, dist_km=dist,
        t_bg=285.0,
        c1_summit=0.003, c1_scene=0.010,
        inner_km=5.0, bt_sanity_k=3.0,
    )
    assert mask[2, 2] == True


def test_dual_roi_pixel_in_scene_rejected_with_strict_c1():
    """Pixel a 15 km del vent (scene si inner=5) con dNTI=0.005 falla
    porque scene requiere c1=0.010."""
    nti = np.full((5, 5), -0.95)
    nti[2, 2] = -0.945       # dNTI ~ 0.005
    bt = np.full((5, 5), 295.0)
    roi = np.ones((5, 5), dtype=bool)
    dist = np.full((5, 5), 2.0)   # default summit
    dist[2, 2] = 15.0             # este pixel scene
    mask = dual_roi_contextual_dnti_hot_mask(
        nti=nti, bt=bt, roi_mask=roi, dist_km=dist,
        t_bg=285.0,
        c1_summit=0.003, c1_scene=0.010,
        inner_km=5.0, bt_sanity_k=3.0,
    )
    assert mask[2, 2] == False


def test_dual_roi_pixel_in_scene_passes_with_high_dnti():
    """Pixel a 15 km con dNTI=0.015 (clearly sobre c1_scene=0.010) pasa."""
    nti = np.full((5, 5), -0.95)
    nti[2, 2] = -0.935       # dNTI ~ 0.015
    bt = np.full((5, 5), 295.0)
    roi = np.ones((5, 5), dtype=bool)
    dist = np.full((5, 5), 2.0)
    dist[2, 2] = 15.0
    mask = dual_roi_contextual_dnti_hot_mask(
        nti=nti, bt=bt, roi_mask=roi, dist_km=dist,
        t_bg=285.0,
        c1_summit=0.003, c1_scene=0.010,
        inner_km=5.0, bt_sanity_k=3.0,
    )
    assert mask[2, 2] == True


def test_dual_roi_lastarria_realistic_scenario():
    """Escenario Lastarria realista: 7x7 zona mixta.
    - pixel summit a 1 km, dNTI=0.005 -> pasa (C1=0.003).
    - pixel scene a 20 km, dNTI=0.005 -> rechazo (C1=0.010 scene).
    - pixel scene a 20 km, dNTI=0.015 -> pasa (>C1 scene).
    Esto emula: MIROVA summit ok + Lazufre rechazado + eventual erupcion
    grande fuera del summit tambien detectada.
    """
    nti = np.full((7, 7), -0.95)
    nti[1, 1] = -0.945    # summit, dNTI=0.005
    nti[5, 5] = -0.945    # scene lejos, dNTI=0.005 (Lazufre ruido)
    nti[3, 6] = -0.935    # scene lejos, dNTI=0.015 (erupcion real)
    bt = np.full((7, 7), 295.0)
    roi = np.ones((7, 7), dtype=bool)
    dist = np.full((7, 7), 10.0)
    dist[1, 1] = 1.0       # summit
    dist[5, 5] = 20.0      # Lazufre
    dist[3, 6] = 20.0      # erupcion

    mask = dual_roi_contextual_dnti_hot_mask(
        nti=nti, bt=bt, roi_mask=roi, dist_km=dist,
        t_bg=285.0,
        c1_summit=0.003, c1_scene=0.010,
        inner_km=3.0, bt_sanity_k=3.0,
    )
    assert mask[1, 1] == True, "summit fumarola debe pasar"
    assert mask[5, 5] == False, "Lazufre dNTI=0.005 con c1_scene=0.010 debe rechazarse"
    assert mask[3, 6] == True, "erupcion dNTI=0.015 scene debe pasar"


def test_lastarria_scenario_with_one_real_hotspot():
    """Escenario Lastarria sintetico: 7x7 region uniformemente tibia
    + 1 pixel localizado de fumarola activa. Gate sigma-anillo inflaria
    VRP; gate contextual solo retiene el localizado."""
    rng = np.random.default_rng(42)
    nti = rng.normal(-0.92, 0.001, size=(7, 7))
    bt = rng.normal(290.0, 0.5, size=(7, 7))
    nti[3, 3] = -0.90
    bt[3, 3] = 300.0
    roi = np.ones((7, 7), dtype=bool)
    mask = contextual_dnti_hot_mask(
        nti=nti, bt=bt, roi_mask=roi,
        t_bg=290.0, c1=0.003, bt_sanity_k=3.0)
    assert mask[3, 3] == True
    others = mask.copy()
    others[3, 3] = False
    assert others.sum() == 0, f"Expected 0 false positives, got {others.sum()}"
