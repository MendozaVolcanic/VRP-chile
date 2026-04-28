"""S26 — TDD para clip ΔL ≥ 0 en cálculo VRP_MIR.

Bug detectado en logs reproc Villarrica + Test 1: VRP_MIR sale negativo
(-26 MW, -7 MW) cuando paths nuevos (Path D dNTI, Test 1) marcan pixels
hot vs L_bg LOCAL pero más fríos que t_bg_i04 GLOBAL del anillo 5-25km.

Fix universal: clip delta_L = max(L_hot - L_bg, 0). Pixels frios contribuyen
0 al VRP (no negativo). Mantienen su lugar en hot_mask por compatibilidad.

Estos tests verifican el comportamiento del clip en una lógica simulada
del cálculo VRP per-pixel (no requieren granule completo).
"""
from __future__ import annotations
import numpy as np


def _per_pixel_vrp_clipped(L_hot, L_bg, area, wooster_coeff):
    """Helper que reproduce el cómputo VRP per-pixel con clip aplicado."""
    delta_L = np.maximum(L_hot - L_bg, 0.0)
    return area * wooster_coeff * delta_L / 1e6


def test_vrp_clip_pixel_below_background_contributes_zero():
    """Pixel marcado hot pero L_hot < L_bg debe contribuir 0 al VRP, no negativo."""
    L_hot = np.array([1e6, 5e5, 8e5])  # tres pixels (uno bajo bg)
    L_bg = 7e5
    area = 140625.0
    wooster = 18.0
    vrps = _per_pixel_vrp_clipped(L_hot, L_bg, area, wooster)
    # pixel[0] L_hot=1e6 > L_bg=7e5 → contribuye positivo
    # pixel[1] L_hot=5e5 < L_bg=7e5 → contribución 0 (clip)
    # pixel[2] L_hot=8e5 > L_bg=7e5 → contribuye positivo
    assert vrps[0] > 0
    assert vrps[1] == 0.0  # clip aplicado
    assert vrps[2] > 0
    # Sum total debe ser POSITIVO
    assert float(np.sum(vrps)) > 0


def test_vrp_clip_no_change_when_all_pixels_above_background():
    """Si todos los pixels son hot vs bg, clip no cambia nada."""
    L_hot = np.array([1e6, 9e5, 1.2e6])
    L_bg = 5e5
    area = 140625.0
    wooster = 18.0
    vrps_clipped = _per_pixel_vrp_clipped(L_hot, L_bg, area, wooster)
    vrps_unclipped = area * wooster * (L_hot - L_bg) / 1e6
    np.testing.assert_array_equal(vrps_clipped, vrps_unclipped)


def test_vrp_clip_all_pixels_below_bg_returns_zero_total():
    """Caso degenerado: si todos los pixels están bajo bg, suma = 0 (no negativo)."""
    L_hot = np.array([3e5, 4e5, 5e5])
    L_bg = 7e5
    area = 140625.0
    wooster = 18.0
    vrps = _per_pixel_vrp_clipped(L_hot, L_bg, area, wooster)
    assert float(np.sum(vrps)) == 0.0
