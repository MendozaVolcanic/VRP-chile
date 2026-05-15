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
# S24: discovery dinámico — un profile válido es cualquier YAML en profiles/.
# Antes era hardcoded duplicado en run_pipeline.py argparse choices, drift
# generaba bug invisible (S24 A/B P3.1 falló 8/8 jobs por profile no en lista).
VALID_PROFILES = {p.stem for p in PROFILES_DIR.glob("*.yaml")}


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
# S15 P3.2: dNTI contextual 8-vecinos (Coppola 2016a SP 426.5).
# Pixel hot si (NTI_pixel - median(NTI_8_vecinos)) > C1 AND bt > t_bg + sanity.
DNTI_CONTEXTUAL_C1: float = float(_t.get("dnti_contextual_c1", 0.003))
# S15 P3.1: dual-ROI thresholds (Coppola 2016a Table 2).
# summit (dist <= inner_radius_km): C1_SUMMIT sensible.
# scene  (dist >  inner_radius_km): C1_SCENE estricto (3.3x summit).
DNTI_CONTEXTUAL_C1_SUMMIT: float = float(_t.get("dnti_contextual_c1_summit", 0.003))
DNTI_CONTEXTUAL_C1_SCENE: float = float(_t.get("dnti_contextual_c1_scene", 0.010))
MODIS_VENT_THRESHOLD_K: float = float(_t.get("modis_vent_threshold_k", VENT_THRESHOLD_K))
MODIS_VENT_VRP_FLOOR_MW: float = float(_t.get("modis_vent_vrp_floor_mw", 0.0))
# S23 T18: P95_VENT_EXCLUSION_KM antes hardcoded en process_*.py.
# Margen alrededor del vent_radius_km para excluir el cráter del cómputo
# del percentil 95 local (sino contaminaría con detecciones reales).
# Defaults: MODIS 5km (pixels 1km), VIIRS 750m 4km (pixels 750m).
P95_VENT_EXCLUSION_MODIS_KM: float = float(_t.get("p95_vent_exclusion_modis_km", 5.0))
P95_VENT_EXCLUSION_VIIRS750_KM: float = float(_t.get("p95_vent_exclusion_viirs750_km", 4.0))
# S12 2026-04-15: piso VRP por sensor. Aplicado en store.py después de
# unificar vrp_mw = max(eruption, vent). Cualquier VRP por debajo del
# piso se lleva a 0 (no-detección). Piso calibrado al mínimo MIROVA
# observado por sensor (inclusive, operador >=). Default 0.0 = sin piso.
# S12 E4: mínimo de pixeles calientes en el vent radius para declarar
# detección vent-path. Default 1 = comportamiento actual.
MIN_VENT_PIXELS: int = int(_t.get("min_vent_pixels", 1))
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
# S15 P3.2: dNTI contextual 8-vecinos (Path D). On = agregar al OR de
# hot_mask el gate contextual vs vecinos inmediatos. Default false para
# compatibilidad con profiles previos.
ENABLE_DNTI_CONTEXTUAL_PATH: bool = bool(_p.get("enable_dnti_contextual_path", False))
# S15 P3.1: dual-ROI (summit vs scene C1 distintos). On = Path D usa
# C1_SUMMIT cerca del vent y C1_SCENE lejos. Off = usa C1 unico (P3.2 solo).
ENABLE_DNTI_DUAL_ROI: bool = bool(_p.get("enable_dnti_dual_roi", False))
# S25: Path Test 1 integrated-ROI (Coppola 2015 Eq.1). Suma exceso de radiancia
# MIR sobre toda la ROI vent (default 3 km radio); detecta señales sub-pixel
# espacialmente extendidas que paths per-pixel pierden. POC S25 6/6 refs
# Villarrica disparan vs 0/6 con paths actuales.
ENABLE_TEST1_PATH: bool = bool(_p.get("enable_test1_path", False))
TEST1_K_SIGMA: float = float(_t.get("test1_k_sigma", 3.0))
TEST1_MIR_RELATIVE: float = float(_t.get("test1_mir_relative", 0.02))
TEST1_ROI_KM: float = float(_t.get("test1_roi_km", 3.0))
TEST1_INNER_RING_KM: float = float(_t.get("test1_inner_ring_km", 1.0))
# S26 Dual-ROI N·σ en eruption-path BT (Coppola 2016a Tabla 1).
# Path BT (eruption) usa thresholds N·σ distintos summit vs scene.
# - summit (dist <= inner_radius_km): N·σ_summit = 5 (sensible).
# - scene  (dist >  inner_radius_km): N·σ_scene  = 10 (estricto).
# Análogo a P3.1 P3.2 que ya aplican dual-ROI en Path D dNTI.
# Default OFF mientras se valida con A/B.
ENABLE_DUAL_ROI_BT: bool = bool(_p.get("enable_dual_roi_bt", False))
N_SIGMA_MIR_SUMMIT: float = float(_t.get("n_sigma_mir_summit", 5.0))
N_SIGMA_MIR_SCENE: float = float(_t.get("n_sigma_mir_scene", 10.0))

# S32 P2 Driver B — Test 1 pixel-level filter (Coppola 2016a Tabla 1 aplicado
# a la mask Test 1 antes de sumar VRP). Cuando Test 1 integrated-ROI dispara,
# nuestra mask test1_hot incluye TODOS los pixels que contribuyeron al
# integrated trigger sin filtro N·σ pixel-level adicional. Resultado:
# clusters de 14-49 pixels suman VRP factor 8-30× MIROVA. Hipótesis (validada
# vía análisis agregación): MIROVA reporta sum solo de los pixels que
# además superan threshold dual-ROI 5σ summit / 10σ scene.
# Default OFF (backward compat). Activar en profile experimental para A/B.
ENABLE_TEST1_PIXEL_FILTER: bool = bool(_p.get("enable_test1_pixel_filter", False))

# S33 Driver B Phase 2 — filtro dual-ROI 5σ summit / 10σ scene aplicado a
# la mask final combinada (post-OR de todos los paths) antes de calcular
# n_anomalous_pixels, cluster_hotspots y vrp_mw.
# Phase 1 (test1_pixel_filter) cubre solo path Test 1; Phase 2 cubre TODOS
# los paths incluyendo Path D dNTI contextual (Coppola 2016a SP 426.5)
# que aporta los pixels marginales en Chaiten 14.5x y PCC 11.9x post-Phase 1.
# Default OFF (backward-compat). Activar en profile A/B para validación.
ENABLE_FINAL_PIXEL_FILTER: bool = bool(_p.get("enable_final_pixel_filter", False))

# S35 H8 — Filtro distance pixel-por-pixel en store.append_record.
# Cuando True, filtra anomaly_pixels in/out según volcano.radius_km en lugar
# del filtro all-or-nothing (basado en pixel más caliente individual).
# Bug pre-S35: cuando coexistían cluster summit + pixel lejano (incendio),
# el lejano "robaba" la decisión y se descartaba TODO. Reach 13.7% records
# Tier A en 30d. Fix sin cambio metodológico — alinea con MIROVA per-pixel.
# Default OFF (CLAUDE.md regla: requiere A/B antes de adopción operacional).
ENABLE_PIXEL_LEVEL_DISTANCE_FILTER: bool = bool(_p.get("enable_pixel_level_distance_filter", False))

# S33 D4 fix — Tupungatito 51% FNs sub-pixel: cuando Test 1 dispara, usar
# L_bg del anillo background global (5-25km) en lugar de test1_L_bg_local
# (ring 1-3km del cráter). En volcanes con geotermal crónico (Tupungatito,
# Lastarria fumarolas, Llaima cráter, Copahue lago ácido), el ring 1-3km
# está contaminado por el calor crónico — ΔL pixel-individual clip a 0 →
# suma=0 aunque Test 1 integrated SÍ haya detectado señal.
# Fallback a L_bg global anillo 5-25km (lejos del cráter) recupera la
# señal que el integrated trigger ya detectó.
# Default OFF (backward-compat). Activar via profile A/B.
ENABLE_TEST1_LBG_GLOBAL: bool = bool(_p.get("enable_test1_lbg_global", False))

# S27 MIROVA literal: flag para deshabilitar exclude_zones (parche nuestro).
# MIROVA NO usa máscaras geográficas (verificado vs Coppola 2016a, Coppola 2020,
# Laiolo 2026). Default true (operacional mantiene comportamiento actual);
# false en _mirova_literal para test A/B.
ENABLE_EXCLUDE_ZONES: bool = bool(_p.get("enable_exclude_zones", True))

# S37 H_D8_5 — algoritmo MIROVA literal (Coppola 2016a SP 426.5).
# Tres flags coordinados que activan el clon literal:
#   1. enable_eti_quadratic_scene: regresión cuadrática scene-wide
#      (NTI_bk = a·NTI²_app + b·NTI_app + c, eqs 4-5 paper) +
#      first pass Tests 2 ∧ 3 sobre dNTI/dETI contextuales.
#   2. enable_second_pass_adjacent: tras first pass, re-correr el cómputo
#      excluyendo active pixels (líneas 347-356 paper). Recapture pixels
#      marginales que el first pass perdió por contaminación de vecinos.
#   3. enable_sum_vrp_reporting: store.py reporta vrp_mw_sum_active y
#      hotspot_dist_km_furthest (cluster-agnostic). MIROVA no selecciona
#      cluster — suma TODOS los active pixels (eq 8). Resuelve D8.
# Default OFF en mirova_equivalent. Activar solo en _h_d8_5_full.yaml para A/B.
ENABLE_ETI_QUADRATIC_SCENE: bool = bool(_p.get("enable_eti_quadratic_scene", False))
ENABLE_SECOND_PASS_ADJACENT: bool = bool(_p.get("enable_second_pass_adjacent", False))
ENABLE_SUM_VRP_REPORTING: bool = bool(_p.get("enable_sum_vrp_reporting", False))

# C2 multiplicadores σ contextual para Tests 2 (dNTI) y 3 (dETI), por ROI.
# Coppola 2016a Tabla 1 noche: 5σ summit (ROI1) / 10σ scene (ROI2).
# Tests 2 y 3 usan los mismos valores pero los expongo separados para
# afinamientos futuros (paper deja libertad ROI-specific).
C2_DNTI_SUMMIT_NIGHT: float = float(_t.get("c2_dnti_summit_night", 5.0))
C2_DNTI_SCENE_NIGHT: float = float(_t.get("c2_dnti_scene_night", 10.0))
C2_DETI_SUMMIT_NIGHT: float = float(_t.get("c2_deti_summit_night", 5.0))
C2_DETI_SCENE_NIGHT: float = float(_t.get("c2_deti_scene_night", 10.0))

# S38 D8 fix verdadero — cluster selection vent-anchored.
# A/B H_D8_5 (S37) refutó "MIROVA suma todo" empíricamente: el path ETI
# cuadrático del paper produce subset redundante con paths existentes,
# NO mejora recall. Re-análisis caso canónico Puyehue lacolito + Lascar
# Salar: el problema no es detección (clusters relevantes sí se detectan)
# sino selection — nuestro pipeline elige el cluster con vrp_mw máximo,
# que típicamente es el más grande, NO el más relevante volcanológicamente.
# Fix S38: cuando ON, cluster_hotspots() ordena por vent-anchored
# (clusters dentro de inner_radius_km ganan sobre lejanos, entre cada
# grupo el más cercano gana). Combinado con enable_pixel_level_distance_filter
# (H8 fix existente OFF default) para filtrar pixels lejanos individuales.
# Default OFF en mirova_equivalent. Activar solo en _d8_vent_anchored.yaml.
ENABLE_VENT_ANCHORED_CLUSTERING: bool = bool(_p.get("enable_vent_anchored_clustering", False))

# S40 cleanup paths viejos — flag para desactivar bt_path_hot path.
# Análisis empírico S39 (records operacional 30d): bt_path_hot solo
# contribuye EXCLUSIVAMENTE en 0-6 records de 1846 TPs totales en 11 vol
# Tier A. Test 1 integrated-ROI (test1_hot) + dNTI contextual (dnti_ctx_hot)
# cubren prácticamente todas las detecciones. bt_path puede ser redundante.
# Default true para backward-compat. A/B desactivar en _no_bt_path.yaml
# y comparar recall delta. Si baja < 1pp → safe retirar del clon literal.
ENABLE_BT_PATH_HOT: bool = bool(_p.get("enable_bt_path_hot", True))

# S46 Drift #1a — Coppola 2016a SP426.5:298-300 dice que Test 1 K1 pixels
# se "discard (unsuitable) for further steps". Nuestro código actual los
# mete al hot_mask reportable vía nti_path_hot — drift respecto al paper.
# Cuando ON: nti_path_hot NO contribuye al hot_mask. Su cálculo se mantiene
# para diagnóstico. Default OFF (backward-compat).
ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK: bool = bool(_p.get("enable_test1_k1_retire_from_hot_mask", False))

# S46 Drift #1b — Coppola 2016a SP426.5:352-356 dice "step 2 is performed a
# second time, being particularly careful to eliminate all of the 'active'
# pixels already detected". Nuestro bg_vals NO excluye pixels Test 1 K1 active,
# contaminando t_bg/std_bg si hay anomalías cerca/dentro del ring.
# Cuando ON: compute_bg_stats excluye pixels NTI > NTI_K1 antes de computar
# t_bg/std_bg. Default OFF (backward-compat).
ENABLE_TEST1_K1_BG_EXCLUDE: bool = bool(_p.get("enable_test1_k1_bg_exclude", False))

# S46 Drift #7 — Coppola 2016a SP426.5 línea 201-202 + Eq.7 dicen:
# "resampled within a 50x50 km grid... spatial resolution of the resampled
# MODIS pixels is 1 km" y "A_PIX is the pixel size (1 km^2 for the resampled
# MODIS pixels)". MIROVA usa A_pix nadir-fijo en los 3 sensores (CLAUDE.md
# regla científica). Flags opt-in por sensor para preservar calibración
# empírica S14 (MODIS sec^3, VIIRS factor lineal 1-2x) como default.
# Cuando ON: A_pix uniforme (1 km^2 MODIS, 0.140625 km^2 VIIRS I, 0.5625 km^2
# VIIRS M) — clon literal MIROVA.
ENABLE_NADIR_FIXED_PIXEL_AREA_MODIS: bool = bool(
    _p.get("enable_nadir_fixed_pixel_area_modis", False)
)
ENABLE_NADIR_FIXED_PIXEL_AREA_VIIRS: bool = bool(
    _p.get("enable_nadir_fixed_pixel_area_viirs", False)
)

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
