"""Smoke test — Wooster MIR coefficients.

Guard against silent regression of WOOSTER_COEFF values. These were empirically
validated in S14 against MIROVA OSF v2.5 with error <=0.17% across 48,360 rows.
Any change breaking this test means the pipeline no longer matches MIROVA.

Reference: CLAUDE.md "Reglas cientificas" + experiments/21_results.json.
"""

from pipeline import process_modis, process_viirs, process_viirs_mod


def test_modis_wooster_coeff():
    """MODIS B21/B22 1 km, empirical k = 18.9 * A_pix(1e6 m2) = 1.89e7."""
    assert process_modis.WOOSTER_COEFF == 18.9


def test_viirs_i4_wooster_coeff():
    """VIIRS I-band 375m (I4), empirical k = 18.0 * A_pix(140625 m2) = 2.53e6.

    NOT 2.48e7 from Di Bella 2024 — that value does not reproduce OSF (S14 A1).
    """
    assert process_viirs.WOOSTER_COEFF == 18.0


def test_viirs_m13_wooster_coeff():
    """VIIRS M-band 750m (M13), empirical k = 19.7 * A_pix(km2) -> 1.97e7 k.

    Updated S14 from prior 18.9; validated empirically against MIROVA OSF v2.5.
    """
    assert process_viirs_mod.WOOSTER_COEFF == 19.7
