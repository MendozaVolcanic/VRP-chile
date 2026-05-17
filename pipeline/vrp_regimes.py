"""VRP regímenes diferenciados según Coppola 2024 chapter Springer.

3 regímenes según rango T del VTF (volcanic thermal feature):
- R1: Lava fresca >600K → Wooster MIR Eq.17 (ya implementado en process_*.py)
- R2: Lava lake magmático sub-pixel ~1000K → Eq.16 Burgi-Coppola (este módulo)
- R3: Crater lake hidrotermal <600K → Eq.25 Ruapehu (pendiente)

Design doc: docs/superpowers/specs/2026-05-17-vrp-three-regimes-design.md
HYPOTHESIS_LOG: H_S52_VIIRS375_OVERDETECT + H_S53_R2_LAVA_LAKE_EQ16
"""
from __future__ import annotations

import math

from pipeline.constants import SIGMA, C1, C2


def _planck_spectral_radiance(t_k: float, lambda_um: float) -> float:
    """Planck spectral radiance B(λ, T) en W/m²/sr/μm."""
    if t_k <= 0 or lambda_um <= 0:
        return 0.0
    try:
        denom = math.exp(C2 / (lambda_um * t_k)) - 1.0
        if denom <= 0:
            return 0.0
        return C1 / (lambda_um ** 5 * denom)
    except OverflowError:
        return 0.0


def compute_vrp_lava_lake_eq16(
    bt_hot_k: float,
    bt_bg_k: float,
    t_bk_k: float,
    t_e_k: float = 1000.0,
    epsilon: float = 0.95,
    a_pix_m2: float = 140625.0,
    lambda_mir_um: float = 3.74,
) -> dict:
    """Calcula VRP de lava lake magmático sub-pixel vía Coppola 2024 Eq.15+16.

    Aplica cuando el VTF es lava magmática expuesta sub-pixel (típico Villarrica,
    Erebus): A_lake ≪ A_pix, BT_pixel mezclado con background frío.

    Método (Coppola 2024 chapter §Lava lakes, Burgi-Coppola convention):
    1. Asume T_e (lava lake temperature) fijo, default 1000 K
    2. Despeja A_hot desde Eq.15:
       A_hot = (L_pixel - L_bg) / (B(λ, T_e) - L_bg) × A_pix
    3. Calcula VRP via Eq.16:
       φ_rad = A_hot × σ × ε × (T_e⁴ - T_bk⁴)

    Args:
        bt_hot_k: Brightness temperature del pixel hot (K)
        bt_bg_k: BT del background ring (K) — usado para L_bg en Eq.15
        t_bk_k: T background físico para Stefan-Boltzmann en Eq.16 (típicamente = bt_bg_k)
        t_e_k: T efectiva asumida del lava lake (K). Default 1000 (Burgi-Coppola)
        epsilon: emisividad. Default 0.95 (literatura volcánica)
        a_pix_m2: área del pixel (m²). Default VIIRS I04 nadir 140625
        lambda_mir_um: longitud de onda MIR (μm). Default 3.74 (VIIRS I04)

    Returns:
        dict con keys:
          - vrp_mw: VRP en MW
          - a_hot_m2: área hot estimada en m²

    Edge cases:
        - bt_hot ≤ bt_bg → vrp=0, a_hot=0 (no anomalía)
        - a_hot > a_pix → clip a a_pix (saturación física)
        - T_bk ≥ T_e → vrp=0 (sin gradiente útil)
    """
    # Edge: sin gradiente positivo
    if bt_hot_k <= bt_bg_k:
        return {"vrp_mw": 0.0, "a_hot_m2": 0.0}
    if t_bk_k >= t_e_k:
        return {"vrp_mw": 0.0, "a_hot_m2": 0.0}

    # Radiancias espectrales Planck
    l_pixel = _planck_spectral_radiance(bt_hot_k, lambda_mir_um)
    l_bg = _planck_spectral_radiance(bt_bg_k, lambda_mir_um)
    b_te = _planck_spectral_radiance(t_e_k, lambda_mir_um)

    if b_te <= l_bg:
        return {"vrp_mw": 0.0, "a_hot_m2": 0.0}

    # Eq.15 — despejar A_hot (Coppola 2024 chapter L1140-1143)
    a_hot = (l_pixel - l_bg) / (b_te - l_bg) * a_pix_m2

    # Clip físico: A_hot ≤ A_pix
    a_hot = min(max(a_hot, 0.0), a_pix_m2)

    # Eq.16 — VRP radiante (Coppola 2024 chapter L1146-1148)
    phi_rad_w = a_hot * SIGMA * epsilon * (t_e_k ** 4 - t_bk_k ** 4)
    vrp_mw = phi_rad_w / 1e6

    return {"vrp_mw": vrp_mw, "a_hot_m2": a_hot}
