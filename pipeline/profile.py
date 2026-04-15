"""
profile.py — active VRP-Chile detection profile loader.

Loads one YAML file from pipeline/profiles/ and exposes its values as
module-level constants that the processor modules import. The active
profile is selected via the VRP_PROFILE environment variable, which
run_pipeline.py sets from its --profile command-line flag BEFORE any
pipeline module is imported.

Default profile: mirova_equivalent (operational).

Usage from a processor module:
    from pipeline.profile import ANOMALY_THRESHOLD_K, N_SIGMA_MIR, ...

Usage from run_pipeline.py:
    os.environ["VRP_PROFILE"] = args.profile  # BEFORE importing pipeline
    from pipeline import process_viirs  # now loads with the selected profile
"""

import os
import sys
import yaml
from pathlib import Path


PROFILES_DIR = Path(__file__).parent / "profiles"
DEFAULT_PROFILE = "mirova_equivalent"
VALID_PROFILES = {"mirova_equivalent", "experimental"}


def _load_profile() -> dict:
    name = os.environ.get("VRP_PROFILE", DEFAULT_PROFILE)
    if name not in VALID_PROFILES:
        raise ValueError(
            f"VRP_PROFILE={name!r} is not a known profile. "
            f"Valid: {sorted(VALID_PROFILES)}"
        )
    path = PROFILES_DIR / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Profile YAML not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    cfg["_name"] = name
    return cfg


_cfg = _load_profile()

# --- Profile identity ---
PROFILE_NAME: str = _cfg["_name"]

# --- Detection thresholds ---
_t = _cfg["thresholds"]
ANOMALY_THRESHOLD_K: float = float(_t["anomaly_threshold_k"])
TIR_THRESHOLD_K: float = float(_t["tir_threshold_k"])
N_SIGMA_MIR: float = float(_t["n_sigma_mir"])
N_SIGMA_TIR: float = float(_t["n_sigma_tir"])
N_SIGMA: float = N_SIGMA_MIR  # alias for process_modis.py compatibility
VENT_THRESHOLD_K: float = float(_t["vent_threshold_k"])
N_SIGMA_VENT: float = float(_t["n_sigma_vent"])
NTI_K1_NIGHT: float = float(_t["nti_k1_night"])
NTI_BT_SANITY_K: float = float(_t["nti_bt_sanity_k"])
CLOUD_MASK_BT_K: float = float(_t.get("cloud_mask_bt_k", 260.0))
MAX_SIGMA_COMPONENT_K: float = float(_t.get("max_sigma_component_k", 7.0))
# S12 F1b: cap on sigma contribution for VENT-path threshold. Prevents
# orographically-noisy backgrounds (Tupungatito, Lastarria) from inflating
# the effective gate beyond real sub-pixel signal magnitude (1–3 K).
MAX_VENT_SIGMA_CONTRIB_K: float = float(_t.get("max_vent_sigma_contrib_k", 3.0))
# Session 12: configurable Path C sigma and MODIS vent threshold
NTI_REL_N_SIGMA: float = float(_t.get("nti_rel_n_sigma", 3.0))
NTI_REL_MIN_FLOOR: float = float(_t.get("nti_rel_min_floor", 0.005))
MODIS_VENT_THRESHOLD_K: float = float(_t.get("modis_vent_threshold_k", VENT_THRESHOLD_K))
MODIS_VENT_VRP_FLOOR_MW: float = float(_t.get("modis_vent_vrp_floor_mw", 0.0))
# S12 2026-04-15: piso VRP por sensor. Aplicado en store.py después de
# unificar vrp_mw = max(eruption, vent). Cualquier VRP por debajo del
# piso se lleva a 0 (no-detección). Piso calibrado al mínimo MIROVA
# observado por sensor (inclusive, operador >=). Default 0.0 = sin piso.
MIN_VRP_MW_VIIRS375: float = float(_t.get("min_vrp_mw_viirs375", 0.0))
MIN_VRP_MW_VIIRS750: float = float(_t.get("min_vrp_mw_viirs750", 0.0))
MIN_VRP_MW_MODIS: float = float(_t.get("min_vrp_mw_modis", 0.0))

# --- Background annulus geometry (km) ---
_bg = _cfg["background"]
BG_INNER_KM: float = float(_bg["inner_km"])
BG_OUTER_KM: float = float(_bg["outer_km"])

# --- Detection paths ---
_p = _cfg["paths"]
ENABLE_ERUPTION_PATH: bool = bool(_p["enable_eruption_path"])
ENABLE_VENT_PATH: bool = bool(_p["enable_vent_path"])
# Session 10: sensor-specific vent_path gate for MODIS (RF1 fix).
# Defaults to ENABLE_VENT_PATH for backward compatibility.
ENABLE_VENT_PATH_MODIS: bool = bool(_p.get("enable_vent_path_modis", ENABLE_VENT_PATH))
# Session 11: NTI-relative detection path (Path C) for weak fumarolic signals.
# When True, pixels passing nti > nti_bg + max(0.005, 3*sigma_nti) AND
# bt > t_bg + NTI_BT_SANITY_K are included in hot_mask_2d.
ENABLE_NTI_RELATIVE_PATH: bool = bool(_p.get("enable_nti_relative_path", False))

# --- Sensor activation ---
_s = _cfg["sensors"]
SENSOR_MODIS: bool = bool(_s.get("modis", True))
SENSOR_VIIRS_375: bool = bool(_s.get("viirs_375", True))
SENSOR_VIIRS_750: bool = bool(_s.get("viirs_750", True))

# --- Data output subdirectory under data/ ---
DATA_SUBDIR: str = str(_cfg["output"]["data_subdir"])


def describe() -> str:
    return (
        f"[VRP profile={PROFILE_NAME}] "
        f"anomaly_K={ANOMALY_THRESHOLD_K} "
        f"nsigma_mir={N_SIGMA_MIR} "
        f"vent_K={VENT_THRESHOLD_K} "
        f"nti_k1={NTI_K1_NIGHT} "
        f"nti_rel={'on' if ENABLE_NTI_RELATIVE_PATH else 'off'} "
        f"vent_path={'on' if ENABLE_VENT_PATH else 'off'} "
        f"sensors=MODIS:{SENSOR_MODIS} V375:{SENSOR_VIIRS_375} V750:{SENSOR_VIIRS_750} "
        f"data_subdir={DATA_SUBDIR}"
    )


# Print the active profile once at import time so every run_pipeline.py run
# has an unambiguous header in its stdout log.
print(describe(), file=sys.stderr)
