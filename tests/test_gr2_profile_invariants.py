"""G-R2 (S88 Frente C) — Coverage tests: invariants of pipeline.profile and the
operational ``mirova_equivalent`` profile.

Why this test exists
--------------------
``mirova_equivalent`` is the ONE profile the NRT cron + dashboard consume. Every
feature flag in it is an operational/methodological decision (CLAUDE.md "Skill
triggers": flipping any flag requires brainstorming + R2 pixel-level validation
+ a defensive tag). An accidental flip — a stray edit, a bad merge — would
silently change what the whole system detects. These tests are a tripwire for
*accidental* flag changes.

How pipeline.profile actually works (verified S88, NOT a class API)
-------------------------------------------------------------------
``pipeline.profile`` is a module that, AT IMPORT TIME, reads the ``VRP_PROFILE``
environment variable (default ``mirova_equivalent``), loads the matching YAML,
and exposes its values as module-level constants (``ENABLE_*``, ``BG_INNER_KM``,
etc.). To test a specific profile you set ``VRP_PROFILE`` then
``importlib.reload(pipeline.profile)`` — the same pattern as the existing
tests/test_enable_exclude_zones_flag.py. An unknown profile raises ``ValueError``
at load time.

Where a value is genuinely policy-mutable, the test reads the YAML as source of
truth and only checks structural invariants, so a *deliberate* documented change
does not fail the test for the wrong reason.

Pure offline: only reloads the module + reads the YAML. No pipeline run.
"""
import importlib
import os

import pytest
import yaml


PROFILE_NAME = "mirova_equivalent"
_YAML_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "pipeline",
    "profiles",
    f"{PROFILE_NAME}.yaml",
)


@pytest.fixture(autouse=True)
def _restore_default_profile():
    """After each test reload pipeline.profile back to mirova_equivalent so the
    module-level global state cannot leak into other tests (same rationale as
    tests/test_enable_exclude_zones_flag.py)."""
    yield
    os.environ["VRP_PROFILE"] = PROFILE_NAME
    import pipeline.profile
    importlib.reload(pipeline.profile)


def _load_operational():
    os.environ["VRP_PROFILE"] = PROFILE_NAME
    import pipeline.profile as profile
    importlib.reload(profile)
    return profile


@pytest.fixture()
def yaml_raw():
    with open(_YAML_PATH, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


# --------------------------------------------------------------------------
# (a) The operational profile loads without error and identifies itself.
# --------------------------------------------------------------------------
def test_mirova_equivalent_loads():
    profile = _load_operational()
    assert profile.PROFILE_NAME == PROFILE_NAME


def test_default_profile_is_mirova_equivalent():
    """With no VRP_PROFILE set, the module defaults to mirova_equivalent."""
    os.environ.pop("VRP_PROFILE", None)
    import pipeline.profile as profile
    importlib.reload(profile)
    assert profile.PROFILE_NAME == PROFILE_NAME
    assert profile.DEFAULT_PROFILE == PROFILE_NAME


# --------------------------------------------------------------------------
# (b) Safety-relevant flags hold their operational values. These are the flags
# whose accidental flip would change detections. Asserted explicitly so a stray
# edit fails CI. (Mirrors current mirova_equivalent.yaml, S88.)
# --------------------------------------------------------------------------
EXPECTED_OPERATIONAL_FLAGS = {
    "ENABLE_VENT_ANCHORED_CLUSTERING": True,
    "ENABLE_PIXEL_LEVEL_DISTANCE_FILTER": True,
    "ENABLE_BT_PATH_HOT": False,
    "ENABLE_EXCLUDE_ZONES": False,
    "ENABLE_TEST1_PATH": True,
    "ENABLE_DNTI_CONTEXTUAL_PATH": True,
    "ENABLE_DNTI_DUAL_ROI": True,
    "ENABLE_VENT_PATH": False,
    # S102 (A45): nadir-fijo MODIS adoptado. MIROVA resamplea a grid 1km de
    # area constante; el sec^3(theta) off-nadir era un DRIFT que inflaba el
    # campo difuso de los vols del sur (PCC/Tupun) 3-5x. Calibracion S14
    # (experiments/21_results.json a_pix_mode=nadir_fijo) + A/B sec^3 (run
    # 27012025326) + validacion (run 27022484062: Lascar 0.92x MIROVA, 0 FN
    # con piso 0.05). Activar nadir-fijo RESTAURA el clon literal.
    "ENABLE_NADIR_FIXED_PIXEL_AREA_MODIS": True,
    # S103 (A45): nadir-fijo VIIRS adoptado (espejo de MODIS S102). Mismo drift
    # off-nadir (factor lineal cap 2x en VIIRS, scan_geometry.viirs_pixel_areas);
    # calibracion S14 (a_pix_mode=nadir_fijo) confirma ambos sensores VIIRS. A/B
    # 3-way (runs 27069747395 + 27079762282, design doc 2026-06-06 §5bis): la
    # hipotesis "ctxpeak=parche sec^3" fue REFUTADA (nadir-SIN-ctx 2.43x peor) ->
    # se adopta nadir + se MANTIENE ctxpeak (mecanismos ortogonales A66). Global
    # VIIRS375 1.95->0.78x, VIIRS750 1.63->0.80x, 0 FN VIIRS375. Tag defensivo:
    # pre-s103-nadir-fixed-viirs.
    "ENABLE_NADIR_FIXED_PIXEL_AREA_VIIRS": True,
    # S106 (AUDIT_S106 P2.2/P2.4): ancla espacial honesta. enable_honest_anchor
    # esta LIVE en VIIRS375 (cura el sesgo topografico D11/A69 de la posicion del
    # record; no toca deteccion ni magnitud, A/B run 27343409067 0-diffs trig_t1).
    # El espejo MODIS sigue OFF A PROPOSITO: reclasificaria 134 records-artefacto
    # far->summit (destape) hasta cerrar el fix de magnitud fondo-local Eq.6
    # (design 2026-06-13). VIIRS750 ADOPTADO S108 (A/B run 27468739388, A45 OK
    # Nicolas): el ancla solo toca posicion (probado +157/-0 en path magnitud).
    # Pinear MODIS OFF para que un flip accidental falle CI (landmine destape, P2.4).
    "ENABLE_HONEST_ANCHOR": True,
    "ENABLE_HONEST_ANCHOR_MODIS": False,
    "ENABLE_HONEST_ANCHOR_VIIRS750": True,
    # S107 §2 (A45/P2.4): fondo-local de magnitud MODIS (corona del cluster contiguo,
    # Coppola 2016a Eq.6). OFF hasta cerrar el A/B V-A/V-B. ES el fix que GATEA el
    # destape del ancla MODIS (ENABLE_HONEST_ANCHOR_MODIS): un flip de este flag sin
    # el A/B cambiaria la magnitud publicada (pc.vrp_mw) de los 11 Tier A. Pinear OFF
    # para que un flip accidental falle CI. Design 2026-06-13 (revision S107, gap A48).
    "ENABLE_LOCAL_CLUSTER_MAGNITUDE": False,
}


@pytest.mark.parametrize("const,expected", sorted(EXPECTED_OPERATIONAL_FLAGS.items()))
def test_operational_flag_value(const, expected):
    profile = _load_operational()
    actual = getattr(profile, const)
    assert actual is expected, (
        f"{const} changed operational value -> {actual} (expected {expected}). "
        f"If intentional, see CLAUDE.md flag-change rule (defensive tag + "
        f"brainstorming) and update EXPECTED_OPERATIONAL_FLAGS."
    )


def test_profile_constants_match_yaml_paths(yaml_raw):
    """Each ENABLE_* flag we pin must match the YAML 'paths' section, so a
    silent default cannot mask a missing/typo'd YAML key."""
    profile = _load_operational()
    paths = yaml_raw.get("paths", {})
    const_to_yaml = {
        "ENABLE_VENT_ANCHORED_CLUSTERING": "enable_vent_anchored_clustering",
        "ENABLE_PIXEL_LEVEL_DISTANCE_FILTER": "enable_pixel_level_distance_filter",
        "ENABLE_BT_PATH_HOT": "enable_bt_path_hot",
        "ENABLE_EXCLUDE_ZONES": "enable_exclude_zones",
        "ENABLE_TEST1_PATH": "enable_test1_path",
        "ENABLE_DNTI_CONTEXTUAL_PATH": "enable_dnti_contextual_path",
        "ENABLE_DNTI_DUAL_ROI": "enable_dnti_dual_roi",
        "ENABLE_VENT_PATH": "enable_vent_path",
        "ENABLE_NADIR_FIXED_PIXEL_AREA_MODIS": "enable_nadir_fixed_pixel_area_modis",
        "ENABLE_NADIR_FIXED_PIXEL_AREA_VIIRS": "enable_nadir_fixed_pixel_area_viirs",
    }
    for const, ykey in const_to_yaml.items():
        assert ykey in paths, f"{ykey} missing from YAML paths"
        assert getattr(profile, const) is bool(paths[ykey])


# --------------------------------------------------------------------------
# (c) Background-ring geometry. inner/outer radii define the cold-background
# annulus. Read YAML as source of truth + pin the documented values + invariant.
# --------------------------------------------------------------------------
def test_background_geometry_matches_yaml(yaml_raw):
    profile = _load_operational()
    assert profile.BG_INNER_KM == float(yaml_raw["background"]["inner_km"])
    assert profile.BG_OUTER_KM == float(yaml_raw["background"]["outer_km"])


def test_background_geometry_operational_values():
    profile = _load_operational()
    assert profile.BG_INNER_KM == 5.0
    assert profile.BG_OUTER_KM == 25.0


def test_background_inner_less_than_outer():
    profile = _load_operational()
    assert 0.0 < profile.BG_INNER_KM < profile.BG_OUTER_KM


# --------------------------------------------------------------------------
# (d) Robustness of the loader: an unknown profile must raise ValueError, not
# silently fall back to a default (which would hide a typo'd --profile flag).
# --------------------------------------------------------------------------
def test_unknown_profile_raises_value_error():
    os.environ["VRP_PROFILE"] = "definitely_not_a_real_profile_xyz_s88"
    import pipeline.profile as profile
    with pytest.raises(ValueError):
        importlib.reload(profile)


# --------------------------------------------------------------------------
# (e) S102 (A45) — MODIS VRP floor lowered 0.27 -> 0.05 as part of the
# nadir-fixed adoption. The nadir-fixed area reduction shrinks the MODIS VRP
# of weak real signals; at 0.27 the validation lost 5 confirmed MIROVA-MODIS
# detections of Lascar (FN). The floor sweep {0.27,0.15,0.10,0.05} (run
# 27022484062, analyze_nadir_validation.py) showed 0.05 is the ONLY floor with
# FN=0. The VIIRS floors are NOT touched in S102. Read YAML as source of truth
# and pin the documented value so a stray edit fails CI.
# --------------------------------------------------------------------------
def test_min_vrp_mw_modis_floor_matches_yaml(yaml_raw):
    profile = _load_operational()
    assert profile.MIN_VRP_MW_MODIS == float(yaml_raw["thresholds"]["min_vrp_mw_modis"])


def test_min_vrp_mw_modis_operational_value():
    profile = _load_operational()
    assert profile.MIN_VRP_MW_MODIS == 0.05, (
        "MODIS VRP floor must be 0.05 (S102 nadir-fixed adoption, only FN=0 "
        "floor per run 27022484062). If intentional, see CLAUDE.md flag-change "
        "rule and update this test + the nadir-fixed adoption record."
    )


def test_viirs_floors_unchanged_by_s102(yaml_raw):
    """Guard anti-confusion MODIS/VIIRS: S102 only touched the MODIS floor.
    The VIIRS floors stay at their pre-S102 operational values."""
    th = yaml_raw["thresholds"]
    assert float(th["min_vrp_mw_viirs375"]) == 0.02
    assert float(th["min_vrp_mw_viirs750"]) == 0.15
