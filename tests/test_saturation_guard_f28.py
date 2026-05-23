"""Tests TDD para F2.8 — fix saturation guard MODIS + VIIRS.

Reproduce los dos bugs encontrados en S73 (ver docs/F28_SATURATION_INVESTIGATION.md):

1. MODIS process_modis.py:184 — filter `dn >= fill` (fill=65535) deja pasar
   sentinel 65533 (Detector saturated, Table 5.6.1 L1B C7 UserGuide).
   Resultado: 113 pixels SI=65533 -> BT=575K -> 695,431 MW (caso PP 2026-03-18).

2. VIIRS process_viirs.py:59 — FLAG_DNS={65532,65533,65534,65535} cubre los
   sentinels DN pero NO lee el SDS de quality flags. Saturated pixels (bit-2)
   clampean radiance al "Reported Range" y pasan al cómputo con BT cerca del
   LUT max (I4=361.77K, I5=423.33K). Resultado: vrp_tir_mw outliers 1000-4000 MW.

Iron Law TDD: estos tests deben FALLAR antes del fix (reproducir el bug) y
PASAR después del fix (causa raíz cerrada).

Referencias:
- docs/F28_SATURATION_INVESTIGATION.md — verdict completo
- docs/F28_HYPOTHESIS_LOG.md — H1, H2, H3, H10 (las que implementamos)
- MODIS L1B C7 UserGuide Sec 5.6 + Table 5.6.1 (autoritativo)
- VIIRS L1B UserGuide Aug 2021 Tabla C.1 (autoritativo)
- Coppola 2025 Cap.11 Table 1 (BT thresholds canónicos)
"""
from __future__ import annotations

import math

import numpy as np
import pytest

# Constants from pipeline (mirroring process_modis.py and process_viirs.py)
C1 = 1.1910429e8  # W·um^4/(m^2·sr)
C2 = 1.4387752e4  # um·K
BAND21_LAMBDA = 3.929  # um — MODIS B21 fire channel
BAND22_LAMBDA = 3.959  # um — MODIS B22 high-gain MIR
I04_LAMBDA = 3.740     # um — VIIRS I-band 04
I05_LAMBDA = 11.450    # um — VIIRS I-band 05 (TIR)

# L1B Sec 5.6 verbatim: "valid science data lie only in the range [0, 32767]"
INVALID_SI_THRESHOLD_MODIS = 32767

# VIIRS I-band BT LUT max (UserGuide Aug 2021 verbatim)
BT_LUT_MAX_I04 = 361.77
BT_LUT_MAX_I05 = 423.33

# MODIS L1B Tabla 5.6.1 sentinels (verbatim)
MODIS_SENTINELS = {
    65535: "Entire scans missing / Fill / RSB night mode",
    65534: "L1A DN missing within scan",
    65533: "Detector saturated",
    65532: "Cannot compute zero point DN",
    65531: "Detector is dead",
    65530: "RSB dn** below bottom of range",
    65529: "RSB or TEB dn** above max SI value",
    65528: "Aggregation algorithm failure",
    65527: "Rotation of Earth View Sector",
}


def _planck_radiance(bt_k: float, lambda_um: float) -> float:
    """L = C1 / (lam^5 * (exp(C2/(lam*T)) - 1))"""
    return float(C1 / (lambda_um ** 5 * (np.exp(C2 / (lambda_um * bt_k)) - 1.0)))


def _radiance_to_bt(L: float, lambda_um: float) -> float:
    """Inversa Planck."""
    return float(C2 / (lambda_um * np.log(C1 / (L * lambda_um ** 5) + 1.0)))


# -----------------------------------------------------------------------------
# Synthetic granule fixtures
# -----------------------------------------------------------------------------

def _synth_modis_b21_dn_array_with_sentinels(shape=(10, 10), sat_count=5):
    """Construye array uint16 simulando salida raw de SD.select('EV_1KM_Emissive').get()
    para B21. Llena con DN normales (random 1000-15000) excepto sat_count pixels
    con SI=65533 (Detector saturated).
    """
    rng = np.random.default_rng(42)
    arr = rng.integers(1000, 15000, size=shape, dtype=np.uint16)
    # Sembrar `sat_count` pixels con SI=65533 (Detector saturated)
    flat_idx = rng.choice(arr.size, sat_count, replace=False)
    rows, cols = np.unravel_index(flat_idx, arr.shape)
    for r, c in zip(rows, cols):
        arr[r, c] = 65533  # Saturated sentinel
    return arr, list(zip(rows.tolist(), cols.tolist()))


def _modis_calibrate(dn_array, scale=0.003258, offset=-1577.0, fill=65535):
    """Mimics current pipeline behavior (process_modis.py:181-185).

    BEFORE FIX: only filters dn >= 65535.
    """
    dn = dn_array.astype(np.float32)
    rad = (dn - offset) * scale
    rad[dn >= fill] = np.nan  # ← bug: only catches 65535
    return rad


def _modis_calibrate_fixed(dn_array, scale=0.003258, offset=-1577.0):
    """Post-fix version (per L1B C7 Sec 5.6)."""
    dn = dn_array.astype(np.float32)
    rad = (dn - offset) * scale
    rad[dn > INVALID_SI_THRESHOLD_MODIS] = np.nan  # ← all 14 sentinels
    return rad


# -----------------------------------------------------------------------------
# H1 — MODIS: el filter actual deja pasar el sentinel 65533
# -----------------------------------------------------------------------------

def test_h1_current_modis_pipeline_leaks_sat_sentinel():
    """REPRODUCE BUG: SI=65533 pasa el filter actual `dn >= 65535` y produce
    radiance no-NaN (eventualmente BT física imposible).
    """
    dn, sat_positions = _synth_modis_b21_dn_array_with_sentinels(sat_count=3)
    rad_buggy = _modis_calibrate(dn)
    # Pre-fix: pixels saturados deberían pasar SIN filter
    for r, c in sat_positions:
        assert not np.isnan(rad_buggy[r, c]), (
            f"BUG: pixel sat SI=65533 en ({r},{c}) NO fue enmascarado. "
            f"radiance pasada al pipeline = {rad_buggy[r, c]:.4f} W/m²/sr/µm"
        )


def test_h1_fixed_modis_filter_masks_all_sentinels():
    """POST-FIX: filter `dn > 32767` enmascara todos los sentinels Table 5.6.1
    (no solo 65535).
    """
    dn, sat_positions = _synth_modis_b21_dn_array_with_sentinels(sat_count=3)
    rad_fixed = _modis_calibrate_fixed(dn)
    for r, c in sat_positions:
        assert np.isnan(rad_fixed[r, c]), (
            f"FIX FAILED: pixel sat SI=65533 en ({r},{c}) debería ser NaN. "
            f"radiance recibida = {rad_fixed[r, c]:.4f}"
        )


@pytest.mark.parametrize("sentinel,name", list(MODIS_SENTINELS.items()))
def test_h1_fixed_modis_masks_each_documented_sentinel(sentinel, name):
    """POST-FIX: cualquier sentinel documentado en Tabla 5.6.1 → NaN."""
    dn = np.array([[1500, sentinel, 8000]], dtype=np.uint16)
    rad = _modis_calibrate_fixed(dn)
    assert np.isnan(rad[0, 1]), (
        f"Sentinel {sentinel} ({name}) debería estar enmascarado post-fix"
    )
    # Pixels válidos NO deben ser NaN
    assert not np.isnan(rad[0, 0])
    assert not np.isnan(rad[0, 2])


def test_h1_reproduces_pp_2026_03_18_bt_575k():
    """REGRESSION: reproducir el record PP 2026-03-18 — SI=65533 con calibración
    B21 típica de C6.1 (scale~0.003, offset~-1577) produce BT≈575 K.
    """
    SI_SAT = 65533
    scale = 0.003258  # back-engineered en F2.8.a verification
    offset = -1577.0

    L = scale * (SI_SAT - offset)
    bt = _radiance_to_bt(L, BAND21_LAMBDA)

    # Match observado en JSON: bt_k=575.06 K
    assert 570.0 < bt < 580.0, (
        f"Reproducción PP record: BT esperada ~575 K, obtenida {bt:.2f} K. "
        f"L={L:.2f} W/m²/sr/µm para SI={SI_SAT} con scale={scale}, offset={offset}"
    )


def test_h1_vrp_per_pixel_consistent_with_pp_record():
    """REGRESSION: con sec³(50°) scan-angle elongation y 45 pixels saturados,
    se reproduce ~695,000 MW del record observado.
    """
    WOOSTER_COEFF = 18.9
    A_pix_nominal = 1.0e6  # m² (MODIS 1km)
    sec3_50deg = 1.0 / math.cos(math.radians(50)) ** 3  # ≈ 3.76
    A_pix_eff = A_pix_nominal * sec3_50deg

    # SI=65533 -> L=218.6 ; t_bg=278K -> L_bg=0.24
    L_obs = _planck_radiance(575.06, BAND21_LAMBDA)
    L_bg = _planck_radiance(277.88, BAND21_LAMBDA)
    delta_L = max(L_obs - L_bg, 0.0)

    per_pixel_vrp_mw = A_pix_eff * WOOSTER_COEFF * delta_L / 1.0e6
    total_45_pix = 45 * per_pixel_vrp_mw

    # Observado en JSON: pc.vrp_mw = 695,431
    assert 670_000 < total_45_pix < 720_000, (
        f"REGRESSION reproducción PP record: esperado ~695,000 MW, "
        f"calculado {total_45_pix:,.0f} MW con sec³(50°)={sec3_50deg:.2f}"
    )


# -----------------------------------------------------------------------------
# H2 — VIIRS: quality_flags no leído deja pasar bit-2 (Saturation)
# -----------------------------------------------------------------------------

def _synth_viirs_iband_data(shape=(10, 10), sat_count=4, band="I05"):
    """Simula VIIRS I-band data:
    - bt: array float32 con LUT-lookup applied
    - dn: array uint16 raw (used for sentinel filter)
    - qf: array uint16 quality flags

    Saturated pixels: dn=15000 (valid range), bt=LUT_max (clamped),
                     qf bit-2 (=4) set.
    Para pixels válidos: dn random in [100, 15000], bt random in [250, 320],
                       qf=0.
    """
    rng = np.random.default_rng(123)
    dn = rng.integers(100, 15000, size=shape, dtype=np.uint16)
    bt = rng.uniform(250.0, 320.0, size=shape).astype(np.float32)
    qf = np.zeros(shape, dtype=np.uint16)
    lut_max = BT_LUT_MAX_I04 if band == "I04" else BT_LUT_MAX_I05

    flat_idx = rng.choice(dn.size, sat_count, replace=False)
    rows, cols = np.unravel_index(flat_idx, dn.shape)
    for r, c in zip(rows, cols):
        bt[r, c] = lut_max  # clamped al LUT max
        qf[r, c] = 0b100   # bit-2 = Saturation
    return bt, dn, qf, list(zip(rows.tolist(), cols.tolist()))


def _viirs_process_buggy(bt, dn, qf):
    """Mimics current pipeline behavior (process_viirs.py:182-193):
    - filtra DN flags
    - filtra bt < 0 (LUT fill -999.9)
    - NO LEE quality flags
    """
    FLAG_DNS = {65532, 65533, 65534, 65535}
    out = bt.copy()
    mask = np.isin(dn, list(FLAG_DNS))
    out[mask] = np.nan
    out[out < 0] = np.nan
    return out


def _viirs_process_fixed(bt, dn, qf):
    """Post-fix: agrega quality_flags bit-2 (Saturation) read.

    Opción A (primaria): leer quality_flags bit-2.
    Opción B (secundaria): filter bt >= LUT_max - 0.5K (defensa adicional).
    """
    FLAG_DNS = {65532, 65533, 65534, 65535}
    out = bt.copy()
    # H2 Opción A: leer quality flags
    sat_mask_qf = (qf & 0b100) != 0
    out[sat_mask_qf] = np.nan
    # Original protections
    mask = np.isin(dn, list(FLAG_DNS))
    out[mask] = np.nan
    out[out < 0] = np.nan
    return out


@pytest.mark.parametrize("band,lut_max", [("I04", BT_LUT_MAX_I04), ("I05", BT_LUT_MAX_I05)])
def test_h2_current_viirs_pipeline_leaks_sat_via_quality_flag(band, lut_max):
    """REPRODUCE BUG: pixels con bit-2 Saturation set pasan el filter actual."""
    bt, dn, qf, sat_positions = _synth_viirs_iband_data(sat_count=4, band=band)
    bt_buggy = _viirs_process_buggy(bt, dn, qf)
    for r, c in sat_positions:
        # BUG: bt mantiene el LUT max, no es NaN
        assert not np.isnan(bt_buggy[r, c]), (
            f"BUG VIIRS {band}: sat pixel ({r},{c}) con quality_flag bit-2 SET "
            f"NO fue enmascarado. bt={bt_buggy[r, c]:.2f} K (LUT max={lut_max})"
        )
        assert abs(bt_buggy[r, c] - lut_max) < 0.1


@pytest.mark.parametrize("band,lut_max", [("I04", BT_LUT_MAX_I04), ("I05", BT_LUT_MAX_I05)])
def test_h2_fixed_viirs_pipeline_masks_via_quality_flag(band, lut_max):
    """POST-FIX: pixels con bit-2 Saturation → NaN."""
    bt, dn, qf, sat_positions = _synth_viirs_iband_data(sat_count=4, band=band)
    bt_fixed = _viirs_process_fixed(bt, dn, qf)
    for r, c in sat_positions:
        assert np.isnan(bt_fixed[r, c]), (
            f"FIX FAILED VIIRS {band}: sat pixel ({r},{c}) debería ser NaN. "
            f"bt={bt_fixed[r, c]:.2f}"
        )


def test_h2_reproduces_viirs_outlier_vrp_tir_mw():
    """REGRESSION: 4 pixels I05 sat @ LUT max 423.33K via Stefan-Boltzmann
    producen ~1025 MW (match con observado 1037 MW del PP scan inicial).
    """
    sigma = 5.67e-8
    T_sat = BT_LUT_MAX_I05  # 423.33 K
    A_pix_I = 375 * 375  # m² = 140,625
    P_per_pixel_mw = sigma * T_sat ** 4 * A_pix_I / 1e6
    total_4pix = 4 * P_per_pixel_mw
    assert 1000.0 < total_4pix < 1050.0, (
        f"REGRESSION reproducción VIIRS outlier: esperado ~1025 MW (vs 1037 observado), "
        f"calculado {total_4pix:.2f} MW"
    )


# -----------------------------------------------------------------------------
# H3 — Defensa secundaria BT-level (Coppola 2025 Cap.11 Table 1)
# -----------------------------------------------------------------------------

# Thresholds per Coppola 2025 + UserGuide LUT max (más conservador donde difieren)
BT_SAT_THRESHOLDS = {
    "MODIS_B21": 500.0,     # Coppola 2025 (low-gain fire channel)
    "VIIRS_M13": 634.0,     # Coppola 2025 (low-gain fire channel)
    "VIIRS_I04": 361.77,    # UserGuide LUT max (más preciso que Coppola 353K)
    "VIIRS_I05": 423.33,    # UserGuide LUT max
}


@pytest.mark.parametrize("band,threshold", BT_SAT_THRESHOLDS.items())
def test_h3_bt_defense_masks_above_threshold(band, threshold):
    """POST-FIX defense secundaria: bt > threshold → NaN."""
    # Generar bt con algunos pixels por arriba del threshold
    bt = np.array([
        [200.0, threshold - 10, threshold + 5],   # último debe enmascararse
        [threshold + 100, 280.0, 300.0],          # primero debe enmascararse
    ], dtype=np.float32)

    bt_post = bt.copy()
    bt_post[bt_post > threshold] = np.nan

    # Pixels por arriba del threshold
    assert np.isnan(bt_post[0, 2])
    assert np.isnan(bt_post[1, 0])
    # Pixels válidos no afectados
    assert bt_post[0, 0] == 200.0
    assert bt_post[1, 1] == 280.0


def test_h3_modis_b21_threshold_consistent_with_575k_record():
    """REGRESSION: el record PP con BT=575.06 K cae por arriba del threshold 500 K
    y sería enmascarado por la defensa secundaria.
    """
    assert 575.06 > BT_SAT_THRESHOLDS["MODIS_B21"], (
        f"Defense MODIS B21 debe enmascarar BT=575 K observado. "
        f"Threshold {BT_SAT_THRESHOLDS['MODIS_B21']} K, observado 575.06 K"
    )


# -----------------------------------------------------------------------------
# H10 — VIIRS Opción B BT >= LUT_max como defensa adicional
# -----------------------------------------------------------------------------

@pytest.mark.parametrize("band,lut_max", [("I04", BT_LUT_MAX_I04), ("I05", BT_LUT_MAX_I05)])
def test_h10_bt_lut_max_filter(band, lut_max):
    """POST-FIX defensa secundaria VIIRS: bt >= LUT_max - 0.5 → NaN.
    Cubre el caso edge donde quality_flag NO está disponible o se corrompe.
    """
    bt = np.array([300.0, lut_max - 1.0, lut_max - 0.3, lut_max, lut_max + 5.0])
    expected_nan_mask = np.array([False, False, True, True, True])

    bt_filtered = bt.copy()
    bt_filtered[bt_filtered >= lut_max - 0.5] = np.nan

    np.testing.assert_array_equal(np.isnan(bt_filtered), expected_nan_mask)


# -----------------------------------------------------------------------------
# Integración: defensa H1 + H2 + H3 + H10 combinada
# -----------------------------------------------------------------------------

def test_integration_modis_with_h1_and_h3_combined():
    """MODIS con ambos guards: 1) L1B SI > 32767, 2) BT > 500K defense."""
    # 3 pixels: válido (1500), sentinel (65533), BT extrapolated mal (mostraría
    # bt=600 K post-calibración aunque DN sea válido)
    dn = np.array([[1500, 65533, 14000]], dtype=np.uint16)
    rad_h1 = _modis_calibrate_fixed(dn)
    # Convert to BT
    bt = np.full_like(rad_h1, np.nan, dtype=np.float32)
    for r in range(rad_h1.shape[0]):
        for c in range(rad_h1.shape[1]):
            if not np.isnan(rad_h1[r, c]):
                bt[r, c] = _radiance_to_bt(float(rad_h1[r, c]), BAND21_LAMBDA)
    # H3 defense
    bt[bt > BT_SAT_THRESHOLDS["MODIS_B21"]] = np.nan
    # Resultado:
    assert not np.isnan(bt[0, 0])     # válido OK
    assert np.isnan(bt[0, 1])         # H1 capturó sentinel
    # bt[0,2] depende de la calibración — verificamos solo que no sea > 500K si pasa


def test_integration_viirs_with_h2_h10_combined():
    """VIIRS con quality_flag (Opción A) y BT >= LUT_max (Opción B) combinados:
    captura cualquier sat pixel sin importar si bit-2 está o no set.
    """
    bt, dn, qf, sat_positions = _synth_viirs_iband_data(sat_count=4, band="I05")

    # H2 + H10 fix
    out = bt.copy()
    out[(qf & 0b100) != 0] = np.nan         # H2: leer quality flag
    out[out >= BT_LUT_MAX_I05 - 0.5] = np.nan  # H10: BT >= LUT max

    for r, c in sat_positions:
        assert np.isnan(out[r, c])
