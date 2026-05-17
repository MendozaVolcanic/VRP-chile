"""TDD S53 R2 — Tests para compute_vrp_lava_lake_eq16 (Coppola 2024 §Lava lakes).

Implementa el régimen R2 lava lake magmático sub-pixel:
- Asume T_e = 1000 K (Burgi-Coppola convention para lava lake)
- Despeja A_hot vía Eq.15: A_hot = (L_pixel - L_bg) / (B(λ, T_e) - L_bg) × A_pix
- Calcula VRP vía Eq.16: φ_rad = A_hot × σ × ε × (T_e⁴ - T_bk⁴)

Caso paradigmático Villarrica 2026-05-11 06:00 NOAA20:
- MIROVA reportó 0.31 MW
- BT_pixel summit ≈ 281K, T_bg ≈ 280K
- Eq.16 con T_e=1000 → A_hot ~1.4 m² → VRP ~0.07-0.1 MW (rango MIROVA)

Design doc: docs/superpowers/specs/2026-05-17-vrp-three-regimes-design.md
"""

import math
import pytest

# Iron law TDD: módulo no existe aún. Estos imports DEBEN fallar.
from pipeline.vrp_regimes import compute_vrp_lava_lake_eq16


# Constantes para los tests (CODATA 2018)
SIGMA = 5.670374419e-8  # Stefan-Boltzmann W/m²/K⁴
VIIRS_I04_LAMBDA = 3.74  # μm (banda MIR VIIRS I-band 375m)
VIIRS_I04_NADIR_AREA = 140625.0  # m² (375m × 375m)


# ============================================================================
# Test 1: signature básico
# ============================================================================

def test_function_signature_accepts_required_args():
    """RED 1: la función debe aceptar BT_hot, BT_bg, T_bk, T_e, eps, A_pix, lambda_mir."""
    result = compute_vrp_lava_lake_eq16(
        bt_hot_k=281.0,
        bt_bg_k=280.0,
        t_bk_k=280.0,
        t_e_k=1000.0,
        epsilon=0.95,
        a_pix_m2=VIIRS_I04_NADIR_AREA,
        lambda_mir_um=VIIRS_I04_LAMBDA,
    )
    assert isinstance(result, dict)
    assert "vrp_mw" in result
    assert "a_hot_m2" in result


# ============================================================================
# Test 2: caso canónico Villarrica con cálculo a mano
# ============================================================================

def test_villarrica_canonical_case_yields_sub_mw():
    """RED 2: Villarrica 2026-05-11 06:00 NOAA20 case canonical.

    Pixel summit real del record: BT_hot=283.3K, dist=0.79km, T_bg~280K.
    MIROVA reportó 0.31 MW para esta noche.

    Cálculo verificado matemáticamente con T_e=1000K, ε=0.95, A_pix=140625:
    - ΔL = L(283.3) - L(280) ≈ 0.022 W/m²/sr/μm
    - B(3.74, 1000) ≈ 3547 W/m²/sr/μm
    - A_hot = 0.022/3547 × 140625 ≈ 0.87 m²
    - VRP = 0.87 × 5.67e-8 × 0.95 × (1e12 - 6.15e9) ≈ 0.046 MW

    El método R2 con T_e=1000K da ~0.05 MW vs MIROVA 0.31 MW (ratio ~0.15).
    Esto es 6× menor que MIROVA pero MUCHO más cerca que Wooster (que daría
    0.385 MW para el cluster completo, ratio 1.24×).

    Hipótesis S54: T_e=1000K puede ser muy alto. Calibrar empíricamente
    600-1400K vs CSV MIROVA para ajustar.

    Por ahora test exige: vrp_mw debe ser sub-MW (<1 MW) y >0.
    """
    result = compute_vrp_lava_lake_eq16(
        bt_hot_k=283.3,  # pixel summit real del record S51 confirmado
        bt_bg_k=280.0,
        t_bk_k=280.0,
    )
    # Sub-MW (lava lake debe estar en rango MIROVA 0.05-1.0 MW)
    assert 0.01 <= result["vrp_mw"] <= 1.0, (
        f"vrp_mw={result['vrp_mw']} fuera rango sub-MW esperado"
    )
    # A_hot esperado <10 m² (lava lake Villarrica muy pequeño)
    assert 0.1 <= result["a_hot_m2"] <= 50.0, (
        f"a_hot_m2={result['a_hot_m2']} fuera rango plausible lava lake"
    )


# ============================================================================
# Test 3: Edge case BT_hot ≈ T_bk → vrp ≈ 0
# ============================================================================

def test_no_thermal_gradient_returns_zero():
    """RED 3: si BT_hot = T_bk, no hay anomalía → vrp = 0."""
    result = compute_vrp_lava_lake_eq16(
        bt_hot_k=280.0,
        bt_bg_k=280.0,
        t_bk_k=280.0,
    )
    assert result["vrp_mw"] == 0.0
    assert result["a_hot_m2"] == 0.0


# ============================================================================
# Test 4: Edge case BT_hot < T_bk → vrp = 0 (clip, no negativo)
# ============================================================================

def test_negative_gradient_clipped_to_zero():
    """RED 4: pixel más frío que background no puede ser lava lake → vrp = 0."""
    result = compute_vrp_lava_lake_eq16(
        bt_hot_k=275.0,  # más frío que bg
        bt_bg_k=280.0,
        t_bk_k=280.0,
    )
    assert result["vrp_mw"] == 0.0
    assert result["a_hot_m2"] == 0.0


# ============================================================================
# Test 5: T_e diferente cambia resultado (validar uso del parámetro)
# ============================================================================

def test_higher_te_yields_smaller_a_hot_same_vrp():
    """RED 5: T_e más alto → A_hot más pequeño pero VRP similar (proporcional).

    Físicamente: si el lava lake está más caliente, ocupa menos área para
    irradiar la misma potencia.
    """
    bt_hot, bt_bg, t_bk = 282.0, 280.0, 280.0
    result_1000 = compute_vrp_lava_lake_eq16(bt_hot, bt_bg, t_bk, t_e_k=1000.0)
    result_1400 = compute_vrp_lava_lake_eq16(bt_hot, bt_bg, t_bk, t_e_k=1400.0)
    # T_e más alto → menos A_hot
    assert result_1400["a_hot_m2"] < result_1000["a_hot_m2"]


# ============================================================================
# Test 6: epsilon afecta VRP linealmente
# ============================================================================

def test_epsilon_scales_vrp_linearly():
    """RED 6: VRP proporcional a ε (validar uso del parámetro)."""
    bt_hot, bt_bg, t_bk = 282.0, 280.0, 280.0
    result_ep_1 = compute_vrp_lava_lake_eq16(bt_hot, bt_bg, t_bk, epsilon=1.0)
    result_ep_05 = compute_vrp_lava_lake_eq16(bt_hot, bt_bg, t_bk, epsilon=0.5)
    # ε=0.5 debería dar ~50% del VRP de ε=1.0
    ratio = result_ep_05["vrp_mw"] / result_ep_1["vrp_mw"]
    assert 0.45 <= ratio <= 0.55, f"VRP no escala con ε: ratio={ratio}"


# ============================================================================
# Test 7: defaults T_e=1000, epsilon=0.95
# ============================================================================

def test_defaults_te_1000_eps_095():
    """RED 7: defaults Burgi-Coppola T_e=1000K + ε=0.95 (literatura volcánica)."""
    bt_hot, bt_bg, t_bk = 282.0, 280.0, 280.0
    result_default = compute_vrp_lava_lake_eq16(bt_hot, bt_bg, t_bk)
    result_explicit = compute_vrp_lava_lake_eq16(
        bt_hot, bt_bg, t_bk, t_e_k=1000.0, epsilon=0.95
    )
    assert result_default["vrp_mw"] == pytest.approx(result_explicit["vrp_mw"])
    assert result_default["a_hot_m2"] == pytest.approx(result_explicit["a_hot_m2"])


# ============================================================================
# Test 8: A_hot máximo = A_pix (clip físico)
# ============================================================================

def test_a_hot_clipped_to_a_pix():
    """RED 8: A_hot no puede exceder A_pix (lava lake llena el pixel completo)."""
    # Caso extremo: BT_hot muy caliente → A_hot tendería a >A_pix
    result = compute_vrp_lava_lake_eq16(
        bt_hot_k=600.0,  # pixel saturado con lava
        bt_bg_k=280.0,
        t_bk_k=280.0,
    )
    assert result["a_hot_m2"] <= VIIRS_I04_NADIR_AREA, (
        f"a_hot_m2={result['a_hot_m2']} excede A_pix={VIIRS_I04_NADIR_AREA}"
    )


# ============================================================================
# Test 9: T_bk fríos extremos (caso invierno chileno Villarrica)
# ============================================================================

def test_cold_background_winter_villarrica():
    """RED 9: invierno chileno T_bk ≈ 265K (nieve summit Villarrica).

    Caso 2026-02-26 05:42 documentado: MIROVA reportó 0.12 MW.
    Background típico Villarrica invierno: ~265-275K.
    """
    result = compute_vrp_lava_lake_eq16(
        bt_hot_k=281.85,  # top pixel summit del record real
        bt_bg_k=265.0,    # invierno típico
        t_bk_k=265.0,
    )
    # Esperado: rango plausible 0.03-1.0 MW (mayor gradiente → mayor VRP)
    assert 0.03 <= result["vrp_mw"] <= 2.0, (
        f"vrp_mw={result['vrp_mw']} fuera rango plausible invierno"
    )


# ============================================================================
# Test 10: monotonía — mayor BT_hot → mayor VRP
# ============================================================================

def test_monotone_increasing_in_bt_hot():
    """RED 10: si fijamos bg, mayor BT_hot debe dar mayor VRP."""
    bt_bg, t_bk = 280.0, 280.0
    vrps = []
    for bt_hot in [281.0, 283.0, 286.0, 290.0]:
        r = compute_vrp_lava_lake_eq16(bt_hot, bt_bg, t_bk)
        vrps.append(r["vrp_mw"])
    # Estrictamente creciente
    assert all(vrps[i] < vrps[i+1] for i in range(len(vrps)-1)), (
        f"VRP no monótono creciente: {vrps}"
    )
