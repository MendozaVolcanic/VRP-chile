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
from pipeline.detection_context import contextual_dnti_hot_mask


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
