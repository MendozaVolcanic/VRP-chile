"""Tests sintéticos F66 dual-bg consistency gate (S79 P1).

Cubre 7 escenarios físicos canónicos en pipeline VRP Chile:
1. Lago uniforme tibio (Caviahue/Conguillío) → vetado
2. Lava lake sub-pixel (Villarrica) → válido
3. Lava extendida cluster (vecinos hot) → fallback ring válido
4. Cirrus dispersa (vecinos cirrus aún más fríos) → válido pero cap D9 limita VRP
5. Salar borde halita (Lascar) → vetado borderline
6. Pixel borde imagen vecinos NaN → fallback válido
7. dNTI dual-ROI Path D compat (regression no rompe path existente)
"""
import numpy as np
import pytest

from pipeline.detection_context import apply_f66_consistency_gate


def test_lake_uniform_vetoed():
    """Lago Caviahue uniforme 278K + pixel central 279K: ΔT=1K < 5K → vetado."""
    bt = np.full((10, 10), 278.0)
    bt[5, 5] = 279.0
    hot_mask = np.zeros((10, 10), dtype=bool)
    hot_mask[5, 5] = True

    hot_mask_out, diag = apply_f66_consistency_gate(
        bt, hot_mask, kernel_size=3, dt_min=5.0
    )

    assert hot_mask_out[5, 5] == False, "Pixel lago uniforme debe ser vetado"
    assert diag["n_evaluated"] == 1
    assert diag["n_vetoed"] == 1
    assert diag["n_nan_fallback"] == 0


def test_lava_lake_sub_pixel_passes():
    """Lava lake Villarrica sub-pixel: vecinos fríos 270K, pixel 285K → ΔT=15K → válido."""
    bt = np.full((10, 10), 270.0)
    bt[5, 5] = 285.0
    hot_mask = np.zeros((10, 10), dtype=bool)
    hot_mask[5, 5] = True

    hot_mask_out, diag = apply_f66_consistency_gate(
        bt, hot_mask, kernel_size=3, dt_min=5.0
    )

    assert hot_mask_out[5, 5] == True
    assert diag["n_vetoed"] == 0


def test_extended_lava_cluster_fallback():
    """Cluster lava extendida 5×5 todos hot: t_bg_local NaN → fallback válido."""
    bt = np.full((10, 10), 270.0)
    bt[3:8, 3:8] = 320.0
    hot_mask = np.zeros((10, 10), dtype=bool)
    hot_mask[3:8, 3:8] = True

    hot_mask_out, diag = apply_f66_consistency_gate(
        bt, hot_mask, kernel_size=3, dt_min=5.0
    )

    assert hot_mask_out[5, 5] == True, "Pixel central cluster con todos vecinos hot debe pasar (fallback)"
    assert hot_mask_out.sum() == 25, "Todos los 25 pixels del cluster preservados"
    assert diag["n_nan_fallback"] >= 1


def test_cirrus_dispersed_passes():
    """Pixel cráter caliente 295K rodeado de cirrus fría 245K → ΔT=50K → válido.

    F66 NO veta este caso. El cap D9=5MW del profile (otro path) maneja
    el VRP inflado downstream. F66 solo decide entrada a hot_mask.
    """
    bt = np.full((10, 10), 245.0)
    bt[5, 5] = 295.0
    hot_mask = np.zeros((10, 10), dtype=bool)
    hot_mask[5, 5] = True

    hot_mask_out, diag = apply_f66_consistency_gate(
        bt, hot_mask, kernel_size=3, dt_min=5.0
    )

    assert hot_mask_out[5, 5] == True
    assert diag["n_vetoed"] == 0


def test_border_pixel_nan_fallback():
    """Pixel en (0,0) con vecinos fuera de imagen + NaN: fallback ring válido."""
    bt = np.full((10, 10), 270.0)
    bt[0, 0] = 285.0
    bt[0, 1] = np.nan
    bt[1, 0] = np.nan
    bt[1, 1] = np.nan
    hot_mask = np.zeros((10, 10), dtype=bool)
    hot_mask[0, 0] = True

    hot_mask_out, diag = apply_f66_consistency_gate(
        bt, hot_mask, kernel_size=3, dt_min=5.0
    )

    assert hot_mask_out[0, 0] == True, "Border pixel con vecinos NaN debe pasar fallback"
    assert diag["n_nan_fallback"] == 1


def test_salar_border_halita_vetoed():
    """Salar Atacama Lascar borde halita: vecinos 277K, pixel 280K → ΔT=3K < 5K → vetado."""
    bt = np.full((10, 10), 270.0)
    bt[3:6, 3:6] = 277.0
    bt[4, 4] = 280.0
    hot_mask = np.zeros((10, 10), dtype=bool)
    hot_mask[4, 4] = True

    hot_mask_out, diag = apply_f66_consistency_gate(
        bt, hot_mask, kernel_size=3, dt_min=5.0
    )

    assert hot_mask_out[4, 4] == False, "Pixel Salar borde con vecinos halita debe ser vetado"
    assert diag["n_vetoed"] == 1


def test_empty_hot_mask():
    """Hot mask vacío: no-op, no errores."""
    bt = np.full((10, 10), 270.0)
    hot_mask = np.zeros((10, 10), dtype=bool)

    hot_mask_out, diag = apply_f66_consistency_gate(
        bt, hot_mask, kernel_size=3, dt_min=5.0
    )

    assert hot_mask_out.sum() == 0
    assert diag["n_evaluated"] == 0
    assert diag["n_vetoed"] == 0


def test_dnti_dual_roi_path_d_compat():
    """Regression: F66 gate NO interfiere con dNTI dual-ROI Path D existente.

    Path D dispara con dnti > C1 contextual; F66 actúa sobre el hot_mask
    resultante. Pixel que pasa Path D + tiene ΔT_local válida → pasa ambos.
    """
    bt = np.full((20, 20), 270.0)
    bt[10, 10] = 285.0
    hot_mask = np.zeros((20, 20), dtype=bool)
    hot_mask[10, 10] = True

    hot_mask_out, diag = apply_f66_consistency_gate(
        bt, hot_mask, kernel_size=3, dt_min=5.0
    )

    assert hot_mask_out[10, 10] == True, "Path D pixel debe sobrevivir F66 gate"
    assert diag["n_vetoed"] == 0
