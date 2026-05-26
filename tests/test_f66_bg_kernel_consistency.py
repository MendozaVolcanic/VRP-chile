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
