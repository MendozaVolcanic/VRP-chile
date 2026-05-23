"""VRPTIR — Volcanic Radiative Power via TIR single-band method.

Implementación de Aveni 2025 GRL (doi:10.1029/2024GL113324) Eq.8 + Eq.9.

**STATUS S74**: EXPERIMENTAL — coeficientes derivados de notas Vault
`aveni2025volcanic.md` (confidence:medium per A35). Antes de adoptación
operacional verificar contra PDF original (BLOQUEANTE: PDF AGU paywalled,
ver docs/F31_AVENI_VRPTIR_PLAN_S74.md §6 Task A6).

Coeficientes pendientes verificación:
- k_TIR(λ) = 1.0575·λ² − 14.3139·λ + 85.4239 (Eq.8)
- k_TIR(11.45 µm I5) = 60.17 m·sr (cited in Vault note)
- Rango validez: 300-600 K (complementario Wooster MIR 600-1500 K)

**Pre-requisito operacional**: requiere TIRVolcH detector (Aveni 2024 RSE)
para identificar pixels candidatos. Este módulo provee SOLO la función VRP,
no la detección. Ver Plan F31 Task A1.

Refs:
- docs/F31_AVENI_VRPTIR_PLAN_S74.md — plan integración VRP Chile
- Vault/10_Bibliografia/99_por_clasificar/aveni2025volcanic.md
- CLAUDE.md A35 (jerarquía autoridad fuentes)
"""
from __future__ import annotations

import numpy as np

# Constantes Planck (mismo valor que pipeline/process_modis.py)
_C1 = 1.1910429e8  # W·µm⁴/(m²·sr)
_C2 = 1.4387752e4  # µm·K

# Aveni 2025 GRL Eq.8 verbatim de notas Vault (confidence:medium)
# k_TIR(λ) = 1.0575·λ² − 14.3139·λ + 85.4239 [m·sr]
# **A35 caveat**: verificar contra PDF original antes de adoptación operacional
_AVENI_EQ8_A = 1.0575
_AVENI_EQ8_B = -14.3139
_AVENI_EQ8_C = 85.4239

# Rango validez physical (Aveni 2025 GRL — sharp breakdown <300, T>600 → use Wooster)
VRPTIR_T_MIN_K = 300.0
VRPTIR_T_MAX_K = 600.0

# Wavelengths sensores VRP Chile (µm)
LAMBDA_VIIRS_I5 = 11.45    # I-band 375m TIR
LAMBDA_VIIRS_M15 = 10.76   # M-band 750m TIR
LAMBDA_MODIS_B31 = 11.02   # MODIS 1km TIR

# A_pix per sensor (m²) — área pixel nominal nadir
A_PIX_VIIRS_I = 140625.0     # 375 × 375
A_PIX_VIIRS_M = 562500.0     # 750 × 750
A_PIX_MODIS = 1000000.0      # 1000 × 1000


def k_tir(lambda_um: float) -> float:
    """Coeficiente k_TIR(λ) per Aveni 2025 GRL Eq.8.

    Args:
        lambda_um: longitud de onda central del canal TIR (µm)

    Returns:
        k_TIR en m·sr

    Examples:
        >>> abs(k_tir(11.45) - 60.17) < 0.1   # VIIRS I5, valor verbatim Vault
        True
    """
    return _AVENI_EQ8_A * lambda_um**2 + _AVENI_EQ8_B * lambda_um + _AVENI_EQ8_C


def planck_radiance(bt_k, lambda_um: float):
    """Radiancia spectral Planck (W/m²/sr/µm) para BT (K) en wavelength (µm).

    Implementación numpy-vectorized para arrays. Igual a la de process_modis.py
    y process_viirs.py pero exportable.

    Args:
        bt_k: brightness temperature en Kelvin (scalar o array)
        lambda_um: wavelength en µm

    Returns:
        Radiancia en W/m²/sr/µm
    """
    bt = np.asarray(bt_k, dtype=np.float64)
    with np.errstate(invalid="ignore", divide="ignore", over="ignore"):
        return _C1 / (lambda_um**5 * (np.exp(_C2 / (lambda_um * bt)) - 1.0))


def vrp_tir(
    bt_hot,
    bt_bg: float,
    lambda_um: float,
    a_pix: float,
) -> float:
    """VRPTIR Aveni 2025 GRL Eq.9.

    VRP_TIR = A_pix · k_TIR(λ) · Σ_j (L_TIR(BT_hot_j) − L_TIR(BT_bg))

    Args:
        bt_hot: array-like de BT (K) de pixels hot detectados por TIRVolcH
        bt_bg: BT (K) del background local (ring vecindad, o median scene)
        lambda_um: wavelength del canal TIR (µm)
        a_pix: área del pixel TIR (m²)

    Returns:
        VRP_TIR en Watts. Convertir a MW dividiendo por 1e6.

    **Caveats**:
    - Solo válido para BT_hot dentro de rango [VRPTIR_T_MIN_K, VRPTIR_T_MAX_K].
      Pixels fuera de rango deberían filtrarse antes de llamar esta función.
    - Pre-requisito: bt_hot debe ser output del detector TIRVolcH (Aveni 2024 RSE),
      NO de NTI/dNTI nuestros — TIRVolcH usa baseline temporal 10yr cloud-free.
    - Asume ε = 1 (no aplicar correction emisividad sin verificar contra PDF original).
    - Solo válido nighttime (excluye contaminación solar diurna sobre TIR).

    Examples:
        >>> # 4 pixels VIIRS I5 a 400K sobre BG 280K — Villarrica-like lava lake
        >>> result = vrp_tir([400.0]*4, 280.0, LAMBDA_VIIRS_I5, A_PIX_VIIRS_I)
        >>> result > 0
        True
    """
    bt_hot_arr = np.asarray(bt_hot, dtype=np.float64).ravel()
    if bt_hot_arr.size == 0:
        return 0.0

    k = k_tir(lambda_um)
    l_hot = planck_radiance(bt_hot_arr, lambda_um)
    l_bg = planck_radiance(bt_bg, lambda_um)
    delta_l = l_hot - l_bg

    # Solo contar diferencias positivas (hot > bg)
    delta_l_positive = np.maximum(delta_l, 0.0)

    return float(a_pix * k * np.nansum(delta_l_positive))


def vrp_tir_mw(
    bt_hot,
    bt_bg: float,
    lambda_um: float,
    a_pix: float,
) -> float:
    """Convenience wrapper que retorna VRP_TIR en MW.

    Args/Returns: igual que vrp_tir() pero output en MW.
    """
    return vrp_tir(bt_hot, bt_bg, lambda_um, a_pix) / 1e6


def filter_t_range(bt_array, t_min: float = VRPTIR_T_MIN_K, t_max: float = VRPTIR_T_MAX_K):
    """Devuelve mask boolean para pixels dentro del rango validez VRPTIR.

    Pixels fuera de rango deben enviarse a Wooster MIR (>T_MAX) o ignorarse (<T_MIN).

    Args:
        bt_array: array-like BTs (K)
        t_min: rango mínimo (default 300 K)
        t_max: rango máximo (default 600 K)

    Returns:
        Boolean array same shape — True = VRPTIR-valid
    """
    bt = np.asarray(bt_array, dtype=np.float64)
    return (bt >= t_min) & (bt <= t_max) & ~np.isnan(bt)
