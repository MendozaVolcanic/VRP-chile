"""G-R1 (S88 Frente C) — Coverage tests: radiometric-constant + structural
parity across the three sensor processors.

Why this test exists (physical motivation)
------------------------------------------
VRP Chile runs three radiometric pipelines, one per sensor footprint:

  * pipeline/process_modis.py       — MODIS 1 km    (B21/22 MIR)
  * pipeline/process_viirs.py       — VIIRS I-band 375 m  (I04 MIR)
  * pipeline/process_viirs_mod.py   — VIIRS M-band 750 m  (M13 MIR)

Each turns a Mid-InfraRed radiance into a Volcanic Radiative Power with the
Wooster (2003) MIR proxy ``VRP = k * A_pix * (L_MIR - L_bg)``. Two constants
fully fix the radiometric calibration of each sensor:

  * ``WOOSTER_COEFF``        — the empirical Wooster ``k`` (validated S14 vs OSF).
  * ``NADIR_PIXEL_AREA_M2``  — the nadir footprint = (sensor side length)^2.

If any drifts accidentally, the whole magnitude scale for that sensor shifts
silently. These are the canonical values pinned in CLAUDE.md ("Reglas
cientificas no negociables"):

  * MODIS    WOOSTER_COEFF = 18.9   side 1000 m  (area 1e6 m^2)
  * VIIRS-I  WOOSTER_COEFF = 18.0   side  375 m  (area 140625 m^2)
  * VIIRS-M  WOOSTER_COEFF = 19.7   side  750 m  (area 562500 m^2)

Pure offline guard: imports the modules, asserts constants + structural
parity. Does NOT touch the NRT pipeline. Verified S88 against source:
the public processing entrypoint in all three modules is ``calculate_vrp``;
the two VIIRS modules share the ``bt_to_spectral_radiance`` Planck helper
(MODIS uses a differently-named pair, so no cross-MODIS Planck assertion).
"""
import inspect
import math

import pipeline.process_modis as p_modis
import pipeline.process_viirs as p_viirs_i      # VIIRS I-band 375 m
import pipeline.process_viirs_mod as p_viirs_m  # VIIRS M-band 750 m


# --------------------------------------------------------------------------
# Canonical Wooster coefficients (CLAUDE.md "Reglas cientificas").
# --------------------------------------------------------------------------
def test_modis_wooster_coeff_is_18_9():
    assert p_modis.WOOSTER_COEFF == 18.9


def test_viirs_iband_wooster_coeff_is_18_0():
    assert p_viirs_i.WOOSTER_COEFF == 18.0


def test_viirs_mband_wooster_coeff_is_19_7():
    assert p_viirs_m.WOOSTER_COEFF == 19.7


# --------------------------------------------------------------------------
# Nadir pixel areas = (side length)^2. MIROVA uses fixed nadir area (no
# zenithal correction) for the three sensors.
# --------------------------------------------------------------------------
def test_modis_pixel_area_is_one_km2():
    assert p_modis.NADIR_PIXEL_AREA_M2 == 1e6


def test_viirs_iband_pixel_area_is_375_squared():
    assert p_viirs_i.NADIR_PIXEL_AREA_M2 == 375.0 ** 2
    assert p_viirs_i.NADIR_PIXEL_AREA_M2 == 140625.0


def test_viirs_mband_pixel_area_is_750_squared():
    assert p_viirs_m.NADIR_PIXEL_AREA_M2 == 750.0 ** 2
    assert p_viirs_m.NADIR_PIXEL_AREA_M2 == 562500.0


def test_viirs_pixel_area_is_side_squared_generic():
    """Each VIIRS pixel area must be the exact square of its side length."""
    for mod, side in [(p_viirs_i, 375.0), (p_viirs_m, 750.0)]:
        assert math.isclose(mod.NADIR_PIXEL_AREA_M2, side * side, rel_tol=0, abs_tol=0)


def test_mband_area_is_four_times_iband():
    """750 m is exactly 2x the 375 m side -> 4x the area. Footprint sanity."""
    ratio = p_viirs_m.NADIR_PIXEL_AREA_M2 / p_viirs_i.NADIR_PIXEL_AREA_M2
    assert math.isclose(ratio, 4.0, rel_tol=0, abs_tol=0)


# --------------------------------------------------------------------------
# Structural parity: the public processing entrypoint of all three modules is
# ``calculate_vrp`` and the two VIIRS processors share its parameter list.
# --------------------------------------------------------------------------
def test_all_three_expose_calculate_vrp():
    for mod in (p_modis, p_viirs_i, p_viirs_m):
        assert callable(getattr(mod, "calculate_vrp", None)), (
            f"{mod.__name__} must expose public entrypoint calculate_vrp"
        )


def test_both_viirs_calculate_vrp_share_signature():
    sig_i = inspect.signature(p_viirs_i.calculate_vrp)
    sig_m = inspect.signature(p_viirs_m.calculate_vrp)
    assert list(sig_i.parameters) == list(sig_m.parameters)


def test_both_viirs_share_bt_to_spectral_radiance_helper():
    """Both VIIRS processors define the same Planck radiance helper
    (``bt_to_spectral_radiance``) — parity of the radiometric core."""
    for mod in (p_viirs_i, p_viirs_m):
        assert callable(getattr(mod, "bt_to_spectral_radiance", None))


def test_all_three_share_profile_flag_plumbing():
    """All three sensor modules pull detection flags from pipeline.profile, so a
    profile change reaches every sensor path uniformly. ANOMALY_THRESHOLD_K and
    the background geometry are imported by all three."""
    for mod in (p_modis, p_viirs_i, p_viirs_m):
        assert hasattr(mod, "ANOMALY_THRESHOLD_K")
        assert hasattr(mod, "BG_INNER_KM")
        assert hasattr(mod, "BG_OUTER_KM")


def test_modis_uses_n_sigma_alias_viirs_use_n_sigma_mir():
    """Verified S88 quirk worth pinning: the MIR sigma multiplier reaches MODIS
    under the name ``N_SIGMA`` (profile.py defines ``N_SIGMA = N_SIGMA_MIR`` as
    an explicit 'alias for process_modis.py compatibility'), while the two VIIRS
    processors import it as ``N_SIGMA_MIR``. Same value, two names — this test
    documents the asymmetry so a future refactor that unifies the name does it
    on purpose, not by accident."""
    assert hasattr(p_modis, "N_SIGMA")
    assert not hasattr(p_modis, "N_SIGMA_MIR")
    for mod in (p_viirs_i, p_viirs_m):
        assert hasattr(mod, "N_SIGMA_MIR")
    # Same underlying value regardless of the name it travels under.
    assert p_modis.N_SIGMA == p_viirs_i.N_SIGMA_MIR == p_viirs_m.N_SIGMA_MIR
