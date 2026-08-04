# ════════════════════════════════════════════════════════════════════
# FICHA SDA · process_modis.py · SDA: VRP Chile (clon MIROVA) · ID: VRP-CL
# Objetivo      : Detectar y cuantificar anomalias termicas en granulos MODIS L1B (Terra/Aqua) para apoyar
#                 la vigilancia de actividad volcanica (alerta tecnica OVDAS).
# Lógica        : En cada escena nocturna se buscan pixeles 'calientes' (Tests contextuales y de ROI
#                 integrado de Coppola 2016a), se estima la temperatura de fondo local por anillo, y se
#                 calcula la potencia radiada (VRP) con la ecuacion de Wooster/Planck.
# Modelo/método : Reglas fisicas deterministicas (Planck/Wooster; Coppola 2015/2016a/2024). NO es caja negra
#                 — logica auditable (punto 5.5 Res.372).
# Datos entrada : Radiancia/temperatura de brillo MODIS MOD021KM/MYD021KM (bandas 21/22 MIR, 31 TIR). SIN
#                 datos personales.
# Variables     : BT del pixel, T de fondo (anillo/contextual), umbrales N·sigma dual-ROI (5 summit / 10
#                 scene), area de pixel (nadir-fijo), distancia al crater.
# Limitaciones  : Sesgo topografico en cumbres nevadas (MIR absoluto), sobre-deteccion difusa irreducible a
#                 1 km, saturacion de pixel, contaminacion por lago/nieve, falsos positivos por incendios.
# Refs/datos    : Coppola et al. 2015 (BV 77:55), Coppola 2016a (GS SP426.5), Coppola 2024 (Springer).
#                 Entrenamiento: No aplica (sin ML). Ficha: docs/FICHA_SDA_VRP_CHILE.md
# ════════════════════════════════════════════════════════════════════
"""
process_modis.py — Calculate VRP from MODIS MOD021KM / MYD021KM L1B granules.

Algorithm: MIROVA (Coppola et al. 2015, sp426.5)
  VRP = A_pixel * sigma * (T_pix^4 - T_bg^4)
  threshold = max(5K, 3 * std_background)

Bands:
  EV_1KM_Emissive contains all 16 emissive bands [20-25, 27-36]
  - Band 21 (3.929 um): index 1 in EV_1KM_Emissive — primary MIR hotspot channel
  - Band 22 (3.959 um): index 2 — used where Band 21 is saturated

Geolocation: MOD021KM includes coarse lat/lon (every 5 pixels),
  interpolated to 1km for pixel-level matching.

References:
  - MODIS L1B User Guide C7 (MODIS_L1B_UserGuide_C7.pdf)
  - Coppola et al. 2015, Geological Society Special Publication 426
"""

import numpy as np
from pathlib import Path

try:
    from pyhdf.SD import SD, SDC
    HDF4_AVAILABLE = True
except ImportError:
    HDF4_AVAILABLE = False
    print("WARNING: pyhdf not found. Install: conda install -c conda-forge pyhdf")

from .scan_geometry import modis_pixel_areas, roi_mask_bbox, observation_geometry
from .exclusion_zones import filter_hot_mask, guard_exclude_zones
from .clustering import cluster_hotspots, cluster_pixels_geographic
from .vrp_regimes import (
    compute_local_background,
    cluster_corona_background,
    cluster_vrp_mw_with_bg,
    cluster_focal_vrp_mw,
)
from .test1_integrated import compute_test1_mir
from .anomaly_pixels import build_anomaly_pixels
from .path_d_cap import apply_d9_scene_cap  # F50/S77
from .path_d_intra_radio import apply_intra_radio_gate  # S83 F-S81-A Fase 2
from .second_pass_intra_radio import apply_second_pass_intra_radio_gate  # S85 F-S81-B'


# S23 T17: constantes físicas centralizadas en pipeline/constants.py
from pipeline.constants import SIGMA, C1, C2

BAND21_LAMBDA = 3.929
BAND22_LAMBDA = 3.959
# Band 31 (TIR 11 um) — used for NTI dual criteria (E3).
# EV_1KM_Emissive band order [20,21,22,23,24,25,27,28,29,30,31,32,33,34,35,36]
# so Band 31 is index 10.
BAND31_IDX = 10
BAND31_LAMBDA = 11.03
# Nadir pixel area; actual area is computed per-pixel from scan column index
# in scan_geometry.modis_pixel_areas (sec^3(theta_z) correction).
NADIR_PIXEL_AREA_M2 = 1e6  # 1 km^2 at nadir

# Wooster MIR radiance coefficient (Coppola 2015, Eq.7)
WOOSTER_COEFF = 18.9

# --- All detection thresholds come from the active profile ---
# See pipeline/profiles/*.yaml for the documented values. Profile is
# selected via $VRP_PROFILE (set by run_pipeline.py --profile).
#
# E3 — NTI (Normalized Thermal Index, Coppola 2015) for MODIS.
# Analogous to the dual criteria already used in process_viirs.py on I04/I05.
# NTI = (L_MIR - L_TIR) / (L_MIR + L_TIR), computed per-pixel from Band 21
# (MIR ~3.93 um) and Band 31 (TIR ~11 um). A pixel is flagged hot if EITHER
# the BT-branch passes OR the NTI-branch passes (Coppola 2015 Test 1).
# See ROOT_CAUSE_S9.md RF4/RF6 and experiments/F1_validation.md.
#
# E2a — Cloud mask for the background annulus (CLOUD_MASK_BT_K).
# E2b' — Sigma cap for detection threshold (MAX_SIGMA_COMPONENT_K).
from pipeline.profile import (
    ANOMALY_THRESHOLD_K,
    N_SIGMA,
    BG_INNER_KM,
    BG_OUTER_KM,
    NTI_K1_NIGHT,
    NTI_BT_SANITY_K,
    CLOUD_MASK_BT_K,
    MAX_SIGMA_COMPONENT_K,
    ENABLE_ERUPTION_PATH,
    ENABLE_VENT_PATH_MODIS,
    VENT_THRESHOLD_K,
    MODIS_VENT_THRESHOLD_K,
    MODIS_VENT_VRP_FLOOR_MW,
    N_SIGMA_VENT,
    MAX_VENT_SIGMA_CONTRIB_K,
    MIN_VENT_PIXELS,
    DNTI_CONTEXTUAL_C1,
    DNTI_CONTEXTUAL_C1_SUMMIT,
    DNTI_CONTEXTUAL_C1_SCENE,
    ENABLE_DNTI_CONTEXTUAL_PATH,
    ENABLE_DNTI_DUAL_ROI,
    ENABLE_PATH_D_INTRA_RADIO_GATE,
    ENABLE_SECOND_PASS_INTRA_RADIO_GATE,
    ENABLE_DUAL_ROI_BT,
    ENABLE_TEST1_PIXEL_FILTER,
    ENABLE_FINAL_PIXEL_FILTER,
    ENABLE_TEST1_LBG_GLOBAL,
    N_SIGMA_MIR_SUMMIT,
    N_SIGMA_MIR_SCENE,
    NTI_K1_DAY,
    N_SIGMA_MIR_DAY,
    DNTI_CONTEXTUAL_C1_DAY,
    ENABLE_DAYTIME_MODIS,
    ENABLE_EXCLUDE_ZONES,
    ENABLE_TEST1_PATH,
    TEST1_K_SIGMA,
    TEST1_MIR_RELATIVE,
    TEST1_ROI_KM,
    TEST1_INNER_RING_KM,
    P95_VENT_EXCLUSION_MODIS_KM,
    ENABLE_ETI_QUADRATIC_SCENE,
    ENABLE_SECOND_PASS_ADJACENT,
    C1_SUMMIT_OVERRIDE,
    C2_SUMMIT_OVERRIDE,
    C2_DNTI_SUMMIT_NIGHT,
    C2_DNTI_SCENE_NIGHT,
    C2_DETI_SUMMIT_NIGHT,
    C2_DETI_SCENE_NIGHT,
    ENABLE_VENT_ANCHORED_CLUSTERING,
    ENABLE_BT_PATH_HOT,
    ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK,
    ENABLE_UNSUITABLE_FILTERS_267_273,
    ENABLE_TEST1_K1_BG_EXCLUDE,
    ENABLE_NADIR_FIXED_PIXEL_AREA_MODIS,
    ENABLE_FIRST_PASS_TESTS_2_AND_3,
    ENABLE_DUAL_ROI_FIRST_PASS,
    ENABLE_DUAL_ROI_SECOND_PASS,
    ENABLE_LOCAL_KERNEL_BG,
    PATH_D_ATM_GATE_TBG_MIN_K,
    PATH_D_REQUIRES_COVALIDATION,
    PATH_D_ONLY_CAP_MW,
    PATH_D_ONLY_CAP_TBG_MAX_K,
    ENABLE_BT_SAT_SECONDARY_GUARD,
    BT_SAT_MIR_K_MODIS,
    ENABLE_SINGLE_PIXEL_SUB_MW_MODE,
    SUB_MW_REGIME_THRESHOLD_MW,
    SINGLE_PIXEL_MAX_CLUSTER_PIXELS,
    ENABLE_HONEST_ANCHOR_MODIS,
    ENABLE_HONEST_ANCHOR_MODIS_FIRST_PASS_GATE,
    HONEST_ANCHOR_TEST1_MODE,
    ENABLE_LOCAL_CLUSTER_MAGNITUDE,
    LOCAL_CLUSTER_MAG_MODE,
    LOCAL_CLUSTER_MAG_RING_PX,
    LOCAL_CLUSTER_MAG_MIN_CORONA,
    ENABLE_FOCAL_CLUSTER_MAGNITUDE,
    FOCAL_CLUSTER_KEEP_PEAK,
)
from pipeline.anchor import resolve_honest_anchor, honest_anchor_applies  # S106/S111
from pipeline.single_pixel_mode import apply_single_pixel_mode
from .detection_context import (
    contextual_dnti_hot_mask,
    dual_roi_contextual_dnti_hot_mask,
    dual_roi_bt_threshold,
    compute_eti_scene_quadratic,
    compute_nti_and_nti_app,
    second_pass_adjacent,
    combine_hot_paths,
    compute_bg_stats,
    first_pass_tests_2_and_3,
)

# Indices of bands 21 and 22 within EV_1KM_Emissive
# Band_1KM_Emissive order: [20,21,22,23,24,25,27,28,29,30,31,32,33,34,35,36]
BAND21_IDX = 1
BAND22_IDX = 2


def radiance_to_bt(L: np.ndarray, wavelength_um: float) -> np.ndarray:
    with np.errstate(invalid="ignore", divide="ignore"):
        return C2 / (wavelength_um * np.log(C1 / (L * wavelength_um ** 5) + 1))


def bt_to_radiance(bt, wavelength_um: float):
    """Planck spectral radiance (W/m^2/sr/um) for a given BT (K) and wavelength."""
    with np.errstate(invalid="ignore", divide="ignore", over="ignore"):
        return C1 / (wavelength_um ** 5 * (np.exp(C2 / (wavelength_um * bt)) - 1))


def read_modis_l1b(hdf_path: Path) -> dict:
    """
    Read MODIS MOD021KM L1B HDF4 file.

    Returns:
        {
          "band21": ndarray float32 — calibrated radiance (W/m^2/sr/um)
          "band22": ndarray float32
          "lat":    ndarray float32 — latitude at 1km resolution (interpolated)
          "lon":    ndarray float32 — longitude at 1km resolution
        }
    """
    if not HDF4_AVAILABLE:
        raise ImportError("pyhdf required: conda install -c conda-forge pyhdf")

    sd = SD(str(hdf_path), SDC.READ)

    # --- Read emissive bands ---
    emissive_sds = sd.select("EV_1KM_Emissive")
    emissive_data = emissive_sds.get()              # shape: (16, n_lines, n_samples)
    attrs = emissive_sds.attributes()
    scales = np.array(attrs["radiance_scales"])     # (16,) — one per band
    offsets = np.array(attrs["radiance_offsets"])   # (16,)
    # F2.8 fix (S73): MODIS L1B C7 UserGuide Sec 5.6 (Toller & Isaacman 2025,
    # MCST PUB-01-U-0202-REV E) — "valid science data lie only in the range
    # [0, 32767]. Specific values greater than 32767 are reserved to indicate
    # why data cannot be calibrated" (Table 5.6.1). Los 14 sentinels documentados
    # son 65500-65535, incluyendo 65533 = "Detector is saturated".
    # Pre-fix: solo enmascarábamos `dn >= 65535` (1 sentinel). Causó el record
    # PP 2026-03-18 pc.vrp_mw=695,431 MW (45 pixels SI=65533 → BT=575K, sec³(50°)
    # scan-angle elongation, Wooster k=18.9). Ver docs/F28_SATURATION_INVESTIGATION.md
    INVALID_SI_THRESHOLD = 32767
    emissive_sds.endaccess()

    def calibrate(band_idx, wavelength):
        dn = emissive_data[band_idx].astype(np.float32)
        rad = (dn - offsets[band_idx]) * scales[band_idx]
        rad[dn > INVALID_SI_THRESHOLD] = np.nan
        return rad

    band21 = calibrate(BAND21_IDX, BAND21_LAMBDA)
    band22 = calibrate(BAND22_IDX, BAND22_LAMBDA)
    band31 = calibrate(BAND31_IDX, BAND31_LAMBDA)  # E3: TIR for NTI

    # --- Read coarse geolocation (5km grid embedded in MOD021KM) ---
    lat_coarse = sd.select("Latitude").get().astype(np.float32)   # (406, 271) for 2030x1354
    lon_coarse = sd.select("Longitude").get().astype(np.float32)

    # S122 — ángulos de observación (misma grilla 5km, ya abierta).
    # POR QUÉ: el ángulo de visión condiciona lo que el sensor ve del cráter
    # (píxel oblicuo = más grande, promedia más terreno frío, más atmósfera).
    # NO entran en detección ni magnitud (A_pix es nadir-fijo, A66); se
    # persisten para estudiarlos. Defensivo: si un SDS falta, queda None.
    angles_coarse = {}
    for key, sds_name in (("sensor_zenith_deg", "SensorZenith"),
                          ("sensor_azimuth_deg", "SensorAzimuth"),
                          ("solar_zenith_deg", "SolarZenith"),
                          ("solar_azimuth_deg", "SolarAzimuth")):
        try:
            sds = sd.select(sds_name)
            raw = sds.get().astype(np.float32)
            # MODIS almacena los ángulos como enteros escalados (scale 0.01).
            scale = sds.attributes().get("scale_factor", 1.0)
            sds.endaccess()
            angles_coarse[key] = raw * float(scale)
        except Exception:
            angles_coarse[key] = None

    sd.end()

    # Interpolate coarse lat/lon to full 1km resolution
    n_lines, n_samples = band21.shape
    lat = _interp_geo(lat_coarse, n_lines, n_samples)
    lon = _interp_geo(lon_coarse, n_lines, n_samples)
    angles = {k: (_interp_geo(v, n_lines, n_samples) if v is not None else None)
              for k, v in angles_coarse.items()}

    return {"band21": band21, "band22": band22, "band31": band31,
            "lat": lat, "lon": lon, "angles": angles}


def _interp_geo(coarse: np.ndarray, target_lines: int, target_samples: int) -> np.ndarray:
    """Bilinear interpolation of coarse (5km) geolocation to 1km resolution."""
    from scipy.ndimage import zoom
    scale_y = target_lines / coarse.shape[0]
    scale_x = target_samples / coarse.shape[1]
    try:
        from scipy.ndimage import zoom as _zoom
        return _zoom(coarse, (scale_y, scale_x), order=1)
    except ImportError:
        # Fallback: repeat each value (less accurate but functional)
        return np.repeat(np.repeat(coarse, int(round(scale_y)), axis=0),
                         int(round(scale_x)), axis=1)[:target_lines, :target_samples]


# S23 Task 2: haversine_km centralizado en pipeline/scan_geometry.py
# (era duplicado en 3 archivos process_*.py).
from pipeline.scan_geometry import haversine_km


def _select_thresholds(is_day: bool, enable_day: bool) -> dict:
    """S90 — set de thresholds día/noche para MODIS (Coppola 2016a Tabla 1).

    Día (SOLO si enable_day y is_day): K1=-0.6, C1=0.02 ambos ROIs, N·σ=15 ambos.
    Noche (cualquier otro caso): K1=-0.8, C1=0.003/0.010 summit/scene,
    N·σ=5/10 summit/scene. Con enable_day=False el comportamiento es idéntico
    al histórico (siempre noche) → no toca operacional.
    """
    if enable_day and is_day:
        return {
            "nti_k1": NTI_K1_DAY,
            "n_sigma_summit": N_SIGMA_MIR_DAY,
            "n_sigma_scene": N_SIGMA_MIR_DAY,
            "c1_summit": DNTI_CONTEXTUAL_C1_DAY,
            "c1_scene": DNTI_CONTEXTUAL_C1_DAY,
        }
    return {
        "nti_k1": NTI_K1_NIGHT,
        "n_sigma_summit": N_SIGMA_MIR_SUMMIT,
        "n_sigma_scene": N_SIGMA_MIR_SCENE,
        "c1_summit": DNTI_CONTEXTUAL_C1_SUMMIT,
        "c1_scene": DNTI_CONTEXTUAL_C1_SCENE,
    }


def _scene_is_day(filename: str, lat: float, lon: float) -> bool:
    """S90 — True si la pasada MODIS es diurna (elevación solar > 0) sobre el
    volcán. Parsea la fecha del nombre del granule (formato MODIS) y reusa
    `_solar_elevation` de store.py (DRY, sin ciclo: store no importa process_*).
    Nombre no parseable → False (noche conservadora: no procesar diurno dudoso)."""
    from datetime import datetime as _dt
    from pipeline.store import _solar_elevation
    iso = _parse_datetime(filename)
    if iso == "unknown":
        return False
    try:
        dt = _dt.strptime(iso, "%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        return False
    return _solar_elevation(lat, lon, dt) > 0


def calculate_vrp(hdf_path: Path, geo_path: Path,
                  volcano_lat: float, volcano_lon: float,
                  radius_km: float = 15.0,
                  vent_lat: float = None, vent_lon: float = None,
                  vent_radius_km: float = 4.0,
                  inner_radius_km: float | None = None,
                  exclude_zones: list = None,
                  active_water_bodies: list = None,
                  lbg_global_compatible: bool = False,
                  local_kernel_bg_compatible: bool = False) -> dict | None:
    """
    Calculate VRP from MODIS L1B granule.

    geo_path is accepted for API compatibility but not used —
    geolocation is embedded in MOD021KM.

    Args:
        vent_lat/vent_lon: Optional vent coordinates for weak-signal detection.
            Uses a low threshold (1K) in a tight ROI without ROI p95 filter.
        vent_radius_km: Radius for vent-scale search.
        inner_radius_km: MIROVA-style visual classification radius (S14 D1).
            If None, distance_class is None.

    Returns dict or None if granule does not cover volcano.
    """
    # S90 — set de thresholds día/noche MODIS según elevación solar de la pasada
    # (Coppola 2016a Tabla 1). Con ENABLE_DAYTIME_MODIS=False (operacional) SIEMPRE
    # devuelve noche → idéntico al baseline (y el gate de store.py rechaza el
    # diurno igual). Con el flag ON, las pasadas diurnas usan K1=-0.6/C1=0.02/15σ.
    #
    # Implementación por REBINDING LOCAL (scoping Python): re-asignamos los mismos
    # nombres de las constantes globales a variables locales con el valor día/noche.
    # Así los ~20 call-sites de detección dentro de calculate_vrp (first-pass,
    # second-pass, dual-ROI, vent, Test1) toman el valor correcto SIN editarlos
    # uno por uno (minimiza riesgo de regresión A49). Estas locales NO afectan a
    # _select_thresholds ni a otras funciones (cada una tiene su propio scope).
    _TH = _select_thresholds(
        is_day=_scene_is_day(hdf_path.name, volcano_lat, volcano_lon),
        enable_day=ENABLE_DAYTIME_MODIS,
    )
    NTI_K1_NIGHT = _TH["nti_k1"]                  # noche -0.8 / día -0.6
    N_SIGMA_MIR_SUMMIT = _TH["n_sigma_summit"]    # noche 5 / día 15
    N_SIGMA_MIR_SCENE = _TH["n_sigma_scene"]      # noche 10 / día 15
    DNTI_CONTEXTUAL_C1_SUMMIT = _TH["c1_summit"]  # noche 0.003 / día 0.02
    DNTI_CONTEXTUAL_C1_SCENE = _TH["c1_scene"]    # noche 0.010 / día 0.02
    DNTI_CONTEXTUAL_C1 = _TH["c1_summit"]         # single-ROI: noche 0.003 / día 0.02

    data = read_modis_l1b(hdf_path)

    lat = data["lat"]
    lon = data["lon"]
    # Per-pixel ground area corrected for off-nadir scan geometry
    pixel_areas = modis_pixel_areas(
        lat.shape, nadir_fixed=ENABLE_NADIR_FIXED_PIXEL_AREA_MODIS
    )
    dist = haversine_km(volcano_lat, volcano_lon, lat, lon)

    # P3.1 S15: per-pixel distance from effective vent for dual-ROI.
    if vent_lat is not None and vent_lon is not None:
        vent_dist_per_pixel = haversine_km(vent_lat, vent_lon, lat, lon)
    else:
        vent_dist_per_pixel = dist

    # S15 Tema E: bbox cuadrado (paridad MIROVA KMZ 50x50 km).
    roi_mask = roi_mask_bbox(lat, lon, volcano_lat, volcano_lon, radius_km)
    bg_mask = (dist >= BG_INNER_KM) & (dist <= BG_OUTER_KM)

    if not np.any(roi_mask):
        return None

    # Merge bands: use Band 21 primary, Band 22 where 21 is NaN (saturated)
    # Work with both radiance (for VRP) and BT (for thresholds/reporting)
    rad21 = data["band21"]
    rad22 = data["band22"]
    rad_mir = np.where(np.isnan(rad21), rad22, rad21)

    bt21 = radiance_to_bt(rad21, BAND21_LAMBDA)
    bt22 = radiance_to_bt(rad22, BAND22_LAMBDA)
    bt_mir = np.where(np.isnan(bt21), bt22, bt21)

    # F2.8 S73 H3 — defensa secundaria post-Planck-inversion.
    # Si por alguna razón un pixel saturado escapó al fix L1B (calibrate() filter
    # dn > 32767), su BT extrapolado seguro está por arriba de 500 K (Coppola 2025
    # Cap.11 Table 1 MODIS B21 sat threshold). Defense in depth — costo trivial.
    if ENABLE_BT_SAT_SECONDARY_GUARD:
        bt_mir = np.where(bt_mir > BT_SAT_MIR_K_MODIS, np.nan, bt_mir)

    # E3: TIR Band 31 for NTI. Keep the MIR radiance we'll use for NTI aligned
    # with whichever band provided bt_mir (21 primary, 22 fallback).
    rad31 = data["band31"]
    bt31 = radiance_to_bt(rad31, BAND31_LAMBDA)
    rad_mir_for_nti = np.where(np.isnan(rad21), rad22, rad21)
    with np.errstate(invalid="ignore", divide="ignore"):
        nti = (rad_mir_for_nti - rad31) / (rad_mir_for_nti + rad31)

    # E2a: exclude cold-cloud contaminated pixels from the background annulus.
    # S46 drift #1b: cuando ENABLE_TEST1_K1_BG_EXCLUDE, además excluir pixels
    # Test 1 K1 active (NTI > -0.8 noche) del bg per Coppola 2016a:352-356.
    bg_cloud_free = bg_mask & ~np.isnan(bt_mir) & (bt_mir > CLOUD_MASK_BT_K)
    t_bg, std_bg, _n_bg = compute_bg_stats(
        bt=bt_mir,
        bg_mask=bg_cloud_free,
        nti=nti,
        nti_k1_threshold=NTI_K1_NIGHT,
        enable_test1_k1_bg_exclude=ENABLE_TEST1_K1_BG_EXCLUDE,
        min_bg_pixels=10,
    )
    if t_bg is None:
        return None
    # E2b': cap the sigma component so orographic heterogeneity in the
    # annulus can't blow up the threshold and mask real vent anomalies.
    sigma_component = min(N_SIGMA * std_bg, MAX_SIGMA_COMPONENT_K)
    threshold = max(ANOMALY_THRESHOLD_K, sigma_component)

    # Additional local-ROI filter: use the ROI's own statistics to avoid
    # topographic false positives (e.g., high-altitude volcanoes with warmer
    # low-altitude terrain in the background annulus).
    # A pixel must exceed BOTH the background threshold AND the ROI p95 threshold.
    #
    # IMPORTANT (session 6, E1 fix): when a vent is known, exclude a safety
    # zone around it from the p95 calculation. Otherwise the vent pixel itself
    # elevates the p95 and the filter "eats its own tail": the vent ends up
    # needing to be ~3 K hotter than itself to clear the local threshold.
    # Empirically (Lascar, 16 MODIS pairs in the 2-10 MW bucket), this caused
    # the pipeline to report n_anomalous_pixels=0 on every single ref, with
    # dT_bg as high as 11.7 K but blocked by `p95 + 3K`. The vent exclusion
    # uses a slightly larger margin than vent_radius_km because the 1 km MODIS
    # pixel footprint can overlap the vent even when its center is outside the
    # vent ROI (an Aqua pass with vent_radius_km=3 may still have the hottest
    # pixel at ~4 km from the vent center due to pixel centering).
    # S23 T18: configurable via profile (era hardcoded 5.0 km).
    P95_VENT_EXCLUSION_KM = P95_VENT_EXCLUSION_MODIS_KM
    roi_bt_full = np.where(roi_mask & ~np.isnan(bt_mir), bt_mir, np.nan)
    if vent_lat is not None and vent_lon is not None:
        vent_dist_for_p95 = haversine_km(vent_lat, vent_lon, lat, lon)
        p95_mask = (roi_mask
                    & ~np.isnan(bt_mir)
                    & (vent_dist_for_p95 > max(vent_radius_km, P95_VENT_EXCLUSION_KM)))
        roi_valid = bt_mir[p95_mask]
    else:
        roi_valid = roi_bt_full[~np.isnan(roi_bt_full)]
    if len(roi_valid) >= 10:
        roi_p95 = float(np.percentile(roi_valid, 95))
        roi_std = float(np.std(roi_valid))
        local_threshold = roi_p95 + max(3.0, 2.0 * roi_std)
        effective_threshold = max(t_bg + threshold, local_threshold)
    else:
        roi_p95 = float("nan")
        local_threshold = float("nan")
        effective_threshold = t_bg + threshold

    # E3: NTI background statistics on the same cloud-masked annulus.
    # We also require band 31 to be valid on those pixels.
    nti_bg_vals = nti[bg_cloud_free & ~np.isnan(nti)]
    if len(nti_bg_vals) >= 10:
        nti_bg = float(np.median(nti_bg_vals))
        nti_std = float(np.std(nti_bg_vals))
    else:
        nti_bg = float("nan")
        nti_std = float("nan")

    # Find all anomalous pixels with their 2D indices.
    # Dual path (Coppola 2015 / MIROVA Test 1, analogous to process_viirs.py NTI):
    #   A) BT path: existing E2-capped local+bg threshold (conservative).
    #   B) NTI path: MIROVA fixed floor K1_NIGHT=-0.8 with a BT sanity margin
    #      so we never trigger on pure noise. This rescues subpixel hotspots
    #      at andean volcanoes where sigma_bg inflates the BT threshold beyond
    #      reach but NTI still responds cleanly to even a 1-2% hot fraction.
    # S26 dual-ROI N·sigma BT (Coppola 2016a Tabla 1): summit 5sigma, scene 10sigma.
    # Cuando flag activo y hay vent + inner_radius, sustituimos el bt_path_hot
    # uniforme por dos thresholds diferenciados. local_threshold sigue aplicando
    # encima como filtro p95 (preserva fix histórico).
    if (ENABLE_DUAL_ROI_BT and inner_radius_km is not None
            and vent_lat is not None and vent_lon is not None):
        bt_path_hot = dual_roi_bt_threshold(
            bt=bt_mir, roi_mask=roi_mask, dist_km=vent_dist_per_pixel,
            t_bg=t_bg, std_bg=std_bg, inner_km=inner_radius_km,
            n_sigma_summit=N_SIGMA_MIR_SUMMIT,
            n_sigma_scene=N_SIGMA_MIR_SCENE,
            anomaly_floor_k=ANOMALY_THRESHOLD_K,
            max_sigma_cap_k=MAX_SIGMA_COMPONENT_K,
        )
        # Aplicar local_threshold p95 si existe (filtro complementario).
        if not np.isnan(local_threshold):
            bt_path_hot = bt_path_hot & (bt_mir > local_threshold)
    else:
        bt_path_hot = roi_mask & ~np.isnan(bt_mir) & (bt_mir > effective_threshold)
    # S40 cleanup paths viejos: desactivar bt_path_hot si flag OFF.
    if not ENABLE_BT_PATH_HOT:
        bt_path_hot = np.zeros_like(bt_path_hot, dtype=bool)
    nti_path_hot = (
        roi_mask
        & ~np.isnan(nti)
        & ~np.isnan(bt_mir)
        & (nti > NTI_K1_NIGHT)
        & (bt_mir > (t_bg + NTI_BT_SANITY_K))
    )

    # S71 D9 Opción A — gate atmosférico path D contextual.
    # Cirrus alto enfría t_bg → infla dNTI/dETI artificialmente. Omitir el
    # firing contextual (legacy path D + first-pass Tests 2&3) cuando
    # t_bg < min_k. Ver experiments/127_path_d_tbg_calibration/.
    _path_d_atm_gate_skip = (
        PATH_D_ATM_GATE_TBG_MIN_K is not None
        and not np.isnan(t_bg)
        and t_bg < PATH_D_ATM_GATE_TBG_MIN_K
    )

    # Path D — dNTI contextual 8-vecinos (P3.2 + P3.1 S15, Coppola 2016a).
    # P3.1 dual-ROI: summit C1=0.003 sensible, scene C1=0.010 estricto.
    n_dnti_ctx_path = 0
    if ENABLE_DNTI_CONTEXTUAL_PATH and not np.isnan(nti_bg) and not _path_d_atm_gate_skip:
        # S72 F2.3 — Coppola 2016a SP 426.5 §267-273: path D contextual también
        # debe descartar pixels unsuitable (edge + dETI<-0.1) cuando el flag está
        # ON. Default mantiene comportamiento post-F1.2.a operacional.
        if ENABLE_DNTI_DUAL_ROI and inner_radius_km is not None:
            dnti_ctx_hot = dual_roi_contextual_dnti_hot_mask(
                nti=nti, bt=bt_mir, roi_mask=roi_mask,
                dist_km=vent_dist_per_pixel,
                t_bg=t_bg,
                c1_summit=DNTI_CONTEXTUAL_C1_SUMMIT,
                c1_scene=DNTI_CONTEXTUAL_C1_SCENE,
                inner_km=inner_radius_km,
                bt_sanity_k=NTI_BT_SANITY_K,
                apply_unsuitable_filters=ENABLE_UNSUITABLE_FILTERS_267_273,
            )
        else:
            dnti_ctx_hot = contextual_dnti_hot_mask(
                nti=nti, bt=bt_mir, roi_mask=roi_mask,
                t_bg=t_bg,
                c1=DNTI_CONTEXTUAL_C1,
                bt_sanity_k=NTI_BT_SANITY_K,
                apply_unsuitable_filters=ENABLE_UNSUITABLE_FILTERS_267_273,
            )
        n_dnti_ctx_path = int(np.sum(dnti_ctx_hot))
        # S83 F-S81-A Fase 2 (A-simplificada): gate Path D MODIS intra-radio.
        # Mascarea pixels dnti_ctx fuera del inner_radius_km del KMZ MIROVA.
        # Motivación: 99.5% FPs MODIS Tier A audit S81/S82 son Path D puro lejos
        # del cráter; MIROVA tagged RUTINA 98% → gate intra-ROI no replicado.
        # Default OFF en operacional; ON solo via profile A/B. Ver docs/F_S81_A_*.
        if ENABLE_PATH_D_INTRA_RADIO_GATE:
            dnti_ctx_hot = apply_intra_radio_gate(
                dnti_ctx_hot=dnti_ctx_hot,
                vent_dist_per_pixel=vent_dist_per_pixel,
                inner_radius_km=inner_radius_km,
                enabled=True,
            )
            n_dnti_ctx_path = int(np.sum(dnti_ctx_hot))
    else:
        dnti_ctx_hot = np.zeros_like(bt_path_hot)

    # S29 — Path Test 1 integrated-ROI MIR (Coppola 2015 §2.2 Eq.1) en MODIS
    # Banda 21 (3.929 µm). Coppola 2015 fue diseñado ORIGINALMENTE para MODIS
    # L1B. Tras S27 (VIIRS 375m) y S28 (VIIRS 750m M13) confirmaron H_S27_1 con
    # +30pp y +2pp recall, S29 lo extiende a MODIS para rescatar Lascar 77 FNs
    # MODIS donde el primary_cluster cae en Salar de Atacama (~25 km del vent)
    # mientras MIROVA detecta el cráter a 1-2 km. Test 1 con ROI=3km centrado
    # en vent ignora el Salar y rescata el cráter sub-pixel.
    test1_hot = np.zeros_like(bt_path_hot)
    test1_triggered = False
    test1_n_contrib = 0
    test1_k_obs = 0.0
    test1_centroid_lat = None
    test1_centroid_lon = None
    test1_L_bg_local = None
    if (ENABLE_TEST1_PATH
            and vent_lat is not None and vent_lon is not None):
        test1_res = compute_test1_mir(
            bt=bt_mir, lat=lat, lon=lon,
            vent_lat=vent_lat, vent_lon=vent_lon,
            lambda_um=BAND21_LAMBDA,
            roi_km=TEST1_ROI_KM,
            inner_ring_km=TEST1_INNER_RING_KM,
            k_sigma=TEST1_K_SIGMA,
            mir_relative=TEST1_MIR_RELATIVE,
        )
        test1_triggered = test1_res["triggered"]
        test1_k_obs = test1_res["k_sigma_observed"]
        if test1_triggered:
            test1_hot = test1_res["mask_contributing"]
            test1_n_contrib = test1_res["n_contributing"]
            test1_centroid_lat = test1_res.get("centroid_lat")
            test1_centroid_lon = test1_res.get("centroid_lon")
            test1_L_bg_local = test1_res.get("L_bg")

    # S37 H_D8_5 — path ETI cuadrático scene-wide (Coppola 2016a SP 426.5).
    # ETI = NTI - NTI_bk donde NTI_bk = a·NTI²_app + b·NTI_app + c es la
    # regresión cuadrática de la escena. Pixels que desvían de la regresión
    # son anómalos. Aplica Tests 2 y 3 (paper líneas 311-315) sobre dNTI y
    # dETI contextuales 8-vecinos. Opcional second-pass que recapture
    # marginales (líneas 347-356).
    eti_path_hot = np.zeros_like(bt_path_hot, dtype=bool)
    n_eti_path = 0
    if (ENABLE_ETI_QUADRATIC_SCENE
            and inner_radius_km is not None
            and vent_lat is not None and vent_lon is not None):
        # NTI_app sintético desde BT_TIR (B31) + λ_MIR (B21 primary, B22 fallback)
        lambda_mir_for_nti_app = BAND21_LAMBDA
        _, nti_app = compute_nti_and_nti_app(
            rad_mir=rad_mir_for_nti,
            bt_tir=bt31,
            lambda_mir_um=lambda_mir_for_nti_app,
            lambda_tir_um=BAND31_LAMBDA,
        )
        # Mask scene-wide válida (ROI completo, cloud-free, finite)
        mask_valid_eti = (
            roi_mask
            & ~np.isnan(nti) & ~np.isnan(nti_app)
            & ~np.isnan(bt_mir) & (bt_mir > CLOUD_MASK_BT_K)
        )
        eti_2d = compute_eti_scene_quadratic(nti, nti_app, mask_valid_eti)

        is_summit = vent_dist_per_pixel <= inner_radius_km
        # First pass — Tests 2 ∧ 3 sin exclusión (active_mask vacío).
        empty_active = np.zeros_like(mask_valid_eti, dtype=bool)
        first_pass_active = second_pass_adjacent(
            nti, eti_2d, empty_active,
            c1_dnti=DNTI_CONTEXTUAL_C1_SUMMIT,
            c1_deti=DNTI_CONTEXTUAL_C1_SUMMIT,
            c2_dnti=C2_DNTI_SUMMIT_NIGHT,
            c2_deti=C2_DETI_SUMMIT_NIGHT,
            is_summit=is_summit,
            c1_dnti_scene=DNTI_CONTEXTUAL_C1_SCENE,
            c1_deti_scene=DNTI_CONTEXTUAL_C1_SCENE,
            c2_dnti_scene=C2_DNTI_SCENE_NIGHT,
            c2_deti_scene=C2_DETI_SCENE_NIGHT,
        )

        # Second pass — recapture marginales contaminados (opcional).
        if ENABLE_SECOND_PASS_ADJACENT:
            eti_path_hot = second_pass_adjacent(
                nti, eti_2d, first_pass_active,
                c1_dnti=DNTI_CONTEXTUAL_C1_SUMMIT,
                c1_deti=DNTI_CONTEXTUAL_C1_SUMMIT,
                c2_dnti=C2_DNTI_SUMMIT_NIGHT,
                c2_deti=C2_DETI_SUMMIT_NIGHT,
                is_summit=is_summit,
                c1_dnti_scene=DNTI_CONTEXTUAL_C1_SCENE,
                c1_deti_scene=DNTI_CONTEXTUAL_C1_SCENE,
                c2_dnti_scene=C2_DNTI_SCENE_NIGHT,
                c2_deti_scene=C2_DETI_SCENE_NIGHT,
            )
        else:
            eti_path_hot = first_pass_active

        # Restringir a ROI + sanity BT (no marcar pixels con BT bajo)
        eti_path_hot = (eti_path_hot & roi_mask & ~np.isnan(bt_mir)
                        & (bt_mir > (t_bg + NTI_BT_SANITY_K)))
        n_eti_path = int(np.sum(eti_path_hot))

    hot_mask_2d = combine_hot_paths(
        bt_path_hot=bt_path_hot,
        nti_path_hot=nti_path_hot,
        dnti_ctx_hot=dnti_ctx_hot,
        test1_hot=test1_hot,
        eti_path_hot=eti_path_hot,
        enable_test1_k1_retire_from_hot_mask=ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK,
    )

    # S46 Drift #2+#3 — first-pass Tests 2 ∧ 3 (Coppola 2016a SP426.5:316-325).
    # Reemplaza hot_mask_2d con la conjunción AND de Test 2 (dNTI) y Test 3 (dETI),
    # rama OR estadística μ+C2σ + dual-ROI Tabla 2 (summit/scene).
    # Paths legacy se calcularon arriba pero no contribuyen al hot_mask cuando ON.
    n_first_pass = 0
    n_first_pass_summit = 0  # S111 D11 — seeds first-pass dentro del inner (gate ancla)
    fp_diag = None
    if (ENABLE_FIRST_PASS_TESTS_2_AND_3
            and inner_radius_km is not None
            and not np.isnan(t_bg)
            and not _path_d_atm_gate_skip):
        # NTI_app necesario; lo computamos si no se generó antes (ETI quadratic OFF)
        _, nti_app_fp = compute_nti_and_nti_app(
            rad_mir=rad_mir_for_nti,
            bt_tir=bt31,
            lambda_mir_um=BAND21_LAMBDA,
            lambda_tir_um=BAND31_LAMBDA,
        )
        # S46 Ronda 2: C1/C2 summit override si profile lo provee (default Tabla 1).
        _c1_sum = C1_SUMMIT_OVERRIDE if C1_SUMMIT_OVERRIDE is not None else DNTI_CONTEXTUAL_C1_SUMMIT
        _c2_sum = C2_SUMMIT_OVERRIDE if C2_SUMMIT_OVERRIDE is not None else C2_DNTI_SUMMIT_NIGHT
        _c2_det_sum = C2_SUMMIT_OVERRIDE if C2_SUMMIT_OVERRIDE is not None else C2_DETI_SUMMIT_NIGHT
        # S72 F1.2 — pasar Test 1 K1 mask como unsuitable bg si flag retire ON
        # (Coppola 2016a SP 426.5 §298-300). Si flag OFF mantiene legacy bg.
        _test1_mask_for_fp = (
            nti_path_hot if ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK else None
        )
        # S72 F2.3 — floors §267-273 controlables vía flag. ON (default post-
        # F1.2.a): -0.1. OFF: -inf (sin filtrado dNTI/dETI). Edge filter
        # siempre activo dentro de build_unsuitable_mask, pero §267-273
        # off-able vía floors para A/B test1_retire_only.
        _unsuit_dnti = -0.1 if ENABLE_UNSUITABLE_FILTERS_267_273 else -np.inf
        _unsuit_deti = -0.1 if ENABLE_UNSUITABLE_FILTERS_267_273 else -np.inf
        fp_hot, fp_diag = first_pass_tests_2_and_3(
            nti=nti, nti_app=nti_app_fp, bt=bt_mir,
            roi_mask=roi_mask, dist_km=vent_dist_per_pixel,
            t_bg=t_bg, bt_sanity_k=NTI_BT_SANITY_K,
            c1_dnti_summit=_c1_sum,
            c1_deti_summit=_c1_sum,
            c2_dnti_summit=_c2_sum,
            c2_deti_summit=_c2_det_sum,
            inner_km=inner_radius_km,
            c1_dnti_scene=(DNTI_CONTEXTUAL_C1_SCENE
                           if ENABLE_DUAL_ROI_FIRST_PASS else None),
            c1_deti_scene=(DNTI_CONTEXTUAL_C1_SCENE
                           if ENABLE_DUAL_ROI_FIRST_PASS else None),
            c2_dnti_scene=(C2_DNTI_SCENE_NIGHT
                           if ENABLE_DUAL_ROI_FIRST_PASS else None),
            c2_deti_scene=(C2_DETI_SCENE_NIGHT
                           if ENABLE_DUAL_ROI_FIRST_PASS else None),
            test1_mask=_test1_mask_for_fp,
            unsuitable_dnti_floor=_unsuit_dnti,
            unsuitable_deti_floor=_unsuit_deti,
        )
        hot_mask_2d = fp_hot
        n_first_pass = fp_diag["n_first_pass_pixels"]
        # S111 D11 — señal-summit propia: píxeles del FIRST-PASS (Tests 2&3) dentro
        # del inner_radius, ANTES del second_pass_adjacent. Excluye la recaptura que
        # el gate S85 preserva (A55): ese cluster near-crater es artefacto topográfico
        # (valle NdC). El ancla honesta MODIS solo promueve a summit si esto es >0.
        # Deliberado (A73): se mide sobre fp_hot CRUDO (pre dual_roi_final_filter y
        # pre co-validación path-D) = la señal de DETECCIÓN genuina del first-pass, no
        # el hot_mask contaminado por la recaptura. Efecto: el gate puede ser
        # ligeramente MÁS permisivo (un fp_hot summit que un filtro posterior elimine
        # igual abre el ancla), nunca menos — borde inocuo (señal real débil), jamás
        # apaga una cura. CAVEAT: n_first_pass_summit también queda 0 si el first-pass
        # NO corrió (ENABLE_FIRST_PASS_TESTS_2_AND_3 OFF o _path_d_atm_gate_skip). NO
        # combinar el gate del ancla con path_d_atm_gate sin re-validar el régimen
        # cirrus (D9/A23): ahí el gate bloquearía el ancla aunque hubiera señal real.
        n_first_pass_summit = int(np.sum(fp_hot & (vent_dist_per_pixel <= inner_radius_km)))

    # S46 Task 5 Drift #4 — second_pass_adjacent recapture (paper SP426.5:347-356).
    # Tras el first-pass, recompute dNTI/dETI excluyendo active pixels del 8-vecino
    # mean → recaptura pixels marginales adyacentes que el first-pass perdió por
    # contaminación de vecinos. Sólo opera cuando first-pass Tests 2 ∧ 3 ya corrió
    # (necesitamos hot_mask_2d = fp_hot del bloque anterior y eti reusable del diag).
    n_second_pass_recapture = 0
    if (ENABLE_SECOND_PASS_ADJACENT
            and ENABLE_FIRST_PASS_TESTS_2_AND_3
            and fp_diag is not None
            and inner_radius_km is not None
            and not np.isnan(t_bg)):
        eti_for_second_pass = fp_diag.get("eti")
        if eti_for_second_pass is not None:
            is_summit_mask = vent_dist_per_pixel <= inner_radius_km
            final_active_mask = second_pass_adjacent(
                nti=nti, eti=eti_for_second_pass,
                active_mask=hot_mask_2d,
                c1_dnti=_c1_sum,
                c1_deti=_c1_sum,
                c2_dnti=_c2_sum,
                c2_deti=_c2_det_sum,
                is_summit=(is_summit_mask if ENABLE_DUAL_ROI_SECOND_PASS
                           else None),
                c1_dnti_scene=(DNTI_CONTEXTUAL_C1_SCENE
                               if ENABLE_DUAL_ROI_SECOND_PASS else None),
                c1_deti_scene=(DNTI_CONTEXTUAL_C1_SCENE
                               if ENABLE_DUAL_ROI_SECOND_PASS else None),
                c2_dnti_scene=(C2_DNTI_SCENE_NIGHT
                               if ENABLE_DUAL_ROI_SECOND_PASS else None),
                c2_deti_scene=(C2_DETI_SCENE_NIGHT
                               if ENABLE_DUAL_ROI_SECOND_PASS else None),
            )
            # S85 F-S81-B' — gate intra-radio sobre pixels NUEVOS del second
            # pass. Default OFF; ON via profile A/B. Solo afecta pixels nuevos
            # recapturados; first pass intacto. Ver docs/F_S81_B_PRIME_SECOND_PASS_GATE.md.
            if ENABLE_SECOND_PASS_INTRA_RADIO_GATE:
                final_active_mask = apply_second_pass_intra_radio_gate(
                    first_pass_mask=hot_mask_2d,
                    final_active_mask=final_active_mask,
                    vent_dist_per_pixel=vent_dist_per_pixel,
                    inner_radius_km=inner_radius_km,
                    enabled=True,
                )
            n_second_pass_recapture = int(np.sum(final_active_mask & ~hot_mask_2d))
            hot_mask_2d = final_active_mask

    # S33 Driver B Phase 2 — filtro dual-ROI 5σ summit / 10σ scene a la mask
    # final combinada (Coppola 2016a Tabla 1). Ver explicación en process_viirs.py.
    if (ENABLE_FINAL_PIXEL_FILTER and inner_radius_km is not None
            and not np.isnan(t_bg) and not np.isnan(std_bg)):
        final_thr_mask = dual_roi_bt_threshold(
            bt=bt_mir,
            roi_mask=np.ones_like(bt_mir, dtype=bool),
            dist_km=vent_dist_per_pixel,
            t_bg=t_bg, std_bg=std_bg,
            inner_km=inner_radius_km,
            n_sigma_summit=N_SIGMA_MIR_SUMMIT,
            n_sigma_scene=N_SIGMA_MIR_SCENE,
            anomaly_floor_k=ANOMALY_THRESHOLD_K,
            max_sigma_cap_k=MAX_SIGMA_COMPONENT_K,
        )
        hot_mask_2d = hot_mask_2d & final_thr_mask

    # S71 D9 Opción B — co-validación path D contextual. Cuando ON, el firing
    # contextual (first_pass / dnti_ctx / Test 1) solo cuenta si BT path O NTI
    # path también dispararon. Si los paths "duros" no vieron nada, descartar
    # la contribución contextual (probable cirrus FP).
    if PATH_D_REQUIRES_COVALIDATION:
        _ctx_only = (not np.any(bt_path_hot)) and (not np.any(nti_path_hot))
        if _ctx_only:
            hot_mask_2d = np.zeros_like(hot_mask_2d)

    # S16 P3.6: filtrar exclude_zones.
    # S27 T3: guard ENABLE_EXCLUDE_ZONES — en _mirova_literal queda en False
    # (parche no documentado en papers MIROVA).
    exclude_zones, active_water_bodies = guard_exclude_zones(
        exclude_zones, active_water_bodies, enabled=ENABLE_EXCLUDE_ZONES)
    n_excluded_water = 0
    if exclude_zones:
        hot_mask_2d, n_excluded_water = filter_hot_mask(
            hot_mask_2d, lat, lon, exclude_zones, active_water_bodies)
    hot_rows, hot_cols = np.where(hot_mask_2d)
    n_anomalous = len(hot_rows)
    n_bt_path = int(np.sum(bt_path_hot))
    n_nti_path = int(np.sum(nti_path_hot))

    # S71 D9 Opción C — predicado para cap magnitud path D contextual-only.
    # Activo cuando el firing es solo contextual (BT/NTI duros = 0) AND t_bg
    # por debajo del umbral cirrus. Se aplica en cada sitio donde
    # primary_cluster se asigna (eruption inicial + Test 1 recompute).
    _path_d_cap_active = (
        PATH_D_ONLY_CAP_MW is not None
        and PATH_D_ONLY_CAP_TBG_MAX_K is not None
        and not np.isnan(t_bg)
        and n_bt_path == 0
        and n_nti_path == 0
        and t_bg < PATH_D_ONLY_CAP_TBG_MAX_K
    )

    # S27 cluster aggregation se mueve abajo (post per_pixel_vrp_mw)
    # para incluir vrp_mw del cluster contiguo principal.
    n_hotspots_clustered = 0
    primary_cluster = None
    ctx_cluster_anchor = None  # S106 ancla honesta (snapshot cluster contextual)

    vrp_mw = 0.0
    hotspot_lat = None
    hotspot_lon = None
    hotspot_dist_km = None
    anomaly_pixels = []

    if n_anomalous > 0:
        # Wooster MIR radiance method (Coppola 2015, Eq.7)
        # Use L_bg derived from BT median (not direct radiance median) to avoid
        # inconsistency when background annulus has heterogeneous terrain/clouds.
        # Planck is nonlinear: median(radiance) != radiance(median(BT)).
        L_bg_global = float(C1 / (BAND21_LAMBDA ** 5 * (np.exp(C2 / (BAND21_LAMBDA * t_bg)) - 1)))

        hotpix_bt = bt_mir[hot_rows, hot_cols]
        # Convert hot pixel BT to radiance for consistent VRP calculation
        hotpix_rad = C1 / (BAND21_LAMBDA ** 5 * (np.exp(C2 / (BAND21_LAMBDA * hotpix_bt)) - 1))
        # Per-pixel area accounts for scan-angle elongation
        hotpix_area = pixel_areas[hot_rows, hot_cols]

        # S58 — Coppola 2024 L1129 literal: "T_bk is retrieved from the pixels
        # adjacent to the hot one". Cuando ENABLE_LOCAL_KERNEL_BG ON, calcular
        # L_bg per-pixel desde kernel 3x3 alrededor de cada hot pixel (excluye
        # otros hot + NaNs). Fallback al L_bg_global derivado del ring 5-25km
        # cuando todos los vecinos son NaN. Paridad con VIIRS (process_viirs.py
        # ~791-802).
        # S59 H_S58_PER_VOL: combinar con field local_kernel_bg_compatible per-vol.
        # Solo aplica si AMBOS true. Audit S58 mostro que Tupungatito tiene ring
        # FRIO (glaciar) y kernel local empeoraria. Candidatos opt-in: Villarrica,
        # Copahue, Planchon, Llaima.
        if ENABLE_LOCAL_KERNEL_BG and local_kernel_bg_compatible:
            t_bk_local = compute_local_background(
                bt_mir, list(hot_rows), list(hot_cols), kernel_size=3
            )
            t_bk_arr = np.array(t_bk_local, dtype=np.float64)
            # Fallback a t_bg global cuando local es NaN
            if t_bg is not None and not np.isnan(t_bg):
                t_bk_arr = np.where(np.isnan(t_bk_arr), t_bg, t_bk_arr)
            L_bg = C1 / (BAND21_LAMBDA ** 5 * (np.exp(C2 / (BAND21_LAMBDA * t_bk_arr)) - 1))
        else:
            L_bg = L_bg_global

        # S26: clip ΔL ≥ 0 — Wooster requiere excess radiancia positivo.
        # Pixels marcados hot por Path D dNTI o Test 1 pueden tener BT < t_bg
        # global (vs L_bg local). Sin clip, VRP_MIR sale negativo y rompe sumas.
        delta_L = np.maximum(hotpix_rad - L_bg, 0.0)
        per_pixel_vrp_mw = hotpix_area * WOOSTER_COEFF * delta_L / 1e6
        vrp_mw = float(np.nansum(per_pixel_vrp_mw))
        # F50/S77 fix Opción A: aplicar cap D9 también a vrp_mw scene-wide.
        # Antes solo se aplicaba al primary_cluster (líneas 802 + 1017). En
        # cirrus extendido la suma scene-wide alcanzaba 80-510 MW mientras
        # el cluster era 0.6-5 MW. 715 records afectados pre-fix. Ver doc
        # F50_MODIS_07_25_AUDIT_S77.md. Helper compartida con VIIRS.
        vrp_mw = apply_d9_scene_cap(vrp_mw, _path_d_cap_active, PATH_D_ONLY_CAP_MW)

        # Build list of TOP-100 anomalous pixels sorted by VRP (descending).
        # S26: cap a 100 para evitar bloat JSON (>100MB GitHub limit). Records
        # eruptivos típicamente tienen 1000-4000 pixels detectados; los top 100
        # capturan >95% de la señal VRP y son suficientes para visualización
        # frontend. n_anomalous_pixels conserva el count total.
        sorted_indices = np.argsort(-per_pixel_vrp_mw)[:100]
        for idx in sorted_indices:
            r, c = int(hot_rows[idx]), int(hot_cols[idx])
            anomaly_pixels.append({
                "lat": round(float(lat[r, c]), 5),
                "lon": round(float(lon[r, c]), 5),
                "dist_km": round(float(dist[r, c]), 2),
                "bt_k": round(float(hotpix_bt[idx]), 2),
                "vrp_mw": round(float(per_pixel_vrp_mw[idx]), 4),
            })

        # Primary hotspot = highest VRP pixel
        hotspot_lat = anomaly_pixels[0]["lat"]
        hotspot_lon = anomaly_pixels[0]["lon"]
        hotspot_dist_km = anomaly_pixels[0]["dist_km"]

        # S27 — cluster aggregation alineado con MIROVA n_hotspots (Coppola 2016a).
        # MIROVA reporta VRP del cluster contiguo principal (~1km connectivity),
        # NO la suma indistinta de todos los pixels. Construimos un mapa 2D de
        # VRPs por pixel y agrupamos por componentes conexos 8-vecinos.
        # Cierre divergencia D1 (docs/MIROVA_DIVERGENCES.md).
        vrp_per_pixel_2d = np.zeros_like(hot_mask_2d, dtype=float)
        vrp_per_pixel_2d[hot_rows, hot_cols] = per_pixel_vrp_mw
        _vlat = vent_lat if vent_lat is not None else volcano_lat
        _vlon = vent_lon if vent_lon is not None else volcano_lon
        # S38 D8 fix: cluster selection vent-anchored vs vrp_max.
        _cluster_strategy = ("vent_anchored" if (ENABLE_VENT_ANCHORED_CLUSTERING
                                                  and inner_radius_km is not None)
                              else "vrp_max")
        _cluster_inner = inner_radius_km if _cluster_strategy == "vent_anchored" else None
        _clusters = cluster_hotspots(
            hot_mask_2d, lat, lon, _vlat, _vlon,
            vrp_per_pixel=vrp_per_pixel_2d,
            strategy=_cluster_strategy,
            inner_radius_km=_cluster_inner,
        )
        n_hotspots_clustered = len(_clusters)
        if _clusters:
            _c = _clusters[0]
            _vrp_c = float(_c["vrp_mw"])
            # S107 §2 (D12 destape) — fondo LOCAL de magnitud Eq.6: recomputar el
            # VRP del cluster PRIMARIO con la corona del cluster CONTIGUO en vez del
            # anillo regional 5-25km. Desinfla los blobs warm-scene (corona tibia →
            # ΔL≈0) y preserva lava real (corona fría → ΔL grande). Flag-OFF default
            # (A45). Si la corona degrada (<min_corona válidos) → conserva el VRP
            # regional (fallback explícito, no silencioso). Va ANTES del cap D9.
            _corona_degraded = None
            if ENABLE_LOCAL_CLUSTER_MAGNITUDE:
                _t_bk_corona, _corona_degraded = cluster_corona_background(
                    bt_mir, _c["pixel_indices"], hot_mask_2d,
                    mode=LOCAL_CLUSTER_MAG_MODE,
                    ring_px=LOCAL_CLUSTER_MAG_RING_PX,
                    min_corona=LOCAL_CLUSTER_MAG_MIN_CORONA,
                )
                if not _corona_degraded:
                    _vrp_c = cluster_vrp_mw_with_bg(
                        bt_mir, pixel_areas, _c["pixel_indices"],
                        _t_bk_corona, WOOSTER_COEFF, BAND21_LAMBDA,
                    )
            # S109 §1 — magnitud NÚCLEO FOCAL/CONTEXTUAL: recomputar pc.vrp_mw sumando
            # SOLO los píxeles del cluster contextualmente anómalos (dnti_ctx ∪ {pico}).
            # Corta el campo difuso topográfico (A69/D11, ~10K sobre fondo frío) que
            # MIROVA ignora ("insensitive to diffuse heat") y conserva el foco discreto
            # (cráter activo / lava / incendio). Solo magnitud — posición y detección
            # intactas (recompute post-selección). Flag-OFF default (A45). NO es
            # fondo-local (no toca L_bg). Va ANTES del cap D9.
            _focal_degraded = None
            if ENABLE_FOCAL_CLUSTER_MAGNITUDE:
                _vrp_c, _focal_n, _focal_degraded = cluster_focal_vrp_mw(
                    _c["pixel_indices"], vrp_per_pixel_2d, dnti_ctx_hot,
                    keep_peak=FOCAL_CLUSTER_KEEP_PEAK,
                )
            # S71 D9 Opción C — cap si firing contextual-only en cirrus.
            _d9_capped = False
            if _path_d_cap_active and _vrp_c > PATH_D_ONLY_CAP_MW:
                _vrp_c = PATH_D_ONLY_CAP_MW
                _d9_capped = True
            primary_cluster = {
                "n_pixels": _c["n_pixels"],
                "vrp_mw": round(_vrp_c, 3),
                "centroid_lat": round(_c["centroid_lat"], 5),
                "centroid_lon": round(_c["centroid_lon"], 5),
                "centroid_dist_km": round(_c["centroid_dist_km"], 3),
            }
            if _d9_capped:
                primary_cluster["d9_capped"] = True
            if _corona_degraded is not None:
                primary_cluster["corona_degraded"] = bool(_corona_degraded)
            if _focal_degraded is not None:
                primary_cluster["focal_magnitude"] = True
                primary_cluster["focal_degraded"] = bool(_focal_degraded)
            # F52-B S77 (A45) — single-pixel mode régimen sub-MW.
            _pix_vrps = [float(vrp_per_pixel_2d[i, j])
                         for (i, j) in _c["pixel_indices"]]
            primary_cluster = apply_single_pixel_mode(
                primary_cluster, _pix_vrps,
                enabled=ENABLE_SINGLE_PIXEL_SUB_MW_MODE,
                threshold_mw=SUB_MW_REGIME_THRESHOLD_MW,
                max_pixels=SINGLE_PIXEL_MAX_CLUSTER_PIXELS,
            )
            # S106 ancla honesta — snapshot del cluster CONTEXTUAL (con
            # first-pass ON el hot_mask no incluye píxeles Test1; el recompute
            # S30 pisa primary_cluster más abajo para src=test1). Espejo del
            # patrón process_viirs.py.
            if ENABLE_HONEST_ANCHOR_MODIS and primary_cluster is not None:
                ctx_cluster_anchor = dict(primary_cluster)

    valid_roi = roi_bt_full[~np.isnan(roi_bt_full)]
    t_max = float(np.max(valid_roi)) if len(valid_roi) else float("nan")

    # E3 diag: max NTI inside the ROI
    roi_nti = np.where(roi_mask & ~np.isnan(nti), nti, np.nan)
    nti_max = float(np.nanmax(roi_nti)) if np.any(~np.isnan(roi_nti)) else float("nan")

    # Diagnostic (session 6): location of the hottest pixel in the ROI.
    # Useful when n_anomalous_pixels=0 to understand whether the hottest
    # pixel was inside or outside the vent_radius.
    t_max_dist_km_diag = float("nan")
    if len(valid_roi) > 0:
        flat_idx_max = np.nanargmax(roi_bt_full)
        r_max, c_max = np.unravel_index(flat_idx_max, roi_bt_full.shape)
        t_max_dist_km_diag = float(dist[r_max, c_max])

    # --- Vent-scale detection (weak fumarolic signals) ---
    # Same approach as VIIRS 375m: tight ROI around known vent, low threshold,
    # no ROI p95 filter. Uses the regional background (t_bg) already computed.
    # Session 10 (RF1 fix): gated by ENABLE_VENT_PATH_MODIS. In mirova_equivalent
    # this is False — MODIS 1km pixel produces too many vent-only FPs (21% vs 9%
    # in VIIRS). The eruption-path still runs; only the permissive vent-scale is off.
    vrp_vent_mw = 0.0
    n_vent_pixels = 0
    vent_hotspot_lat = None
    vent_hotspot_lon = None
    vent_hotspot_dist_km = None
    if ENABLE_VENT_PATH_MODIS and vent_lat is not None and vent_lon is not None and not np.isnan(t_bg):
        vent_dist = haversine_km(vent_lat, vent_lon, lat, lon)
        vent_roi_mask = vent_dist <= vent_radius_km
        if np.any(vent_roi_mask):
            vent_bt = np.where(vent_roi_mask & ~np.isnan(bt_mir), bt_mir, np.nan)
            if np.any(~np.isnan(vent_bt)):
                flat_idx = np.nanargmax(vent_bt)
                r_vent, c_vent = np.unravel_index(flat_idx, vent_bt.shape)
                t_max_vent = float(vent_bt[r_vent, c_vent])
                # Session 12: MODIS uses its own higher threshold (2.5K in experimental)
                # to compensate for 1km pixel dilution (SNR 2.5× vs VIIRS 4-5×).
                # Fix F1: also apply sigma gating (same as VIIRS).
                # Fix F1b: cap the sigma contribution (MAX_VENT_SIGMA_CONTRIB_K).
                sigma_contrib = min(N_SIGMA_VENT * std_bg, MAX_VENT_SIGMA_CONTRIB_K)
                modis_vent_thresh = max(MODIS_VENT_THRESHOLD_K, sigma_contrib)
                if t_max_vent > (t_bg + modis_vent_thresh):
                    L_vent = float(C1 / (BAND21_LAMBDA ** 5 * (np.exp(C2 / (BAND21_LAMBDA * t_max_vent)) - 1)))
                    L_bg_vent = float(C1 / (BAND21_LAMBDA ** 5 * (np.exp(C2 / (BAND21_LAMBDA * t_bg)) - 1)))
                    vent_area = float(pixel_areas[r_vent, c_vent])
                    vrp_vent_mw = float(vent_area * WOOSTER_COEFF * (L_vent - L_bg_vent)) / 1e6
                    # S12 E4: count hot pixels + floor check
                    vent_hot_mask = vent_bt > (t_bg + modis_vent_thresh)
                    n_hot_in_vent = int(np.sum(vent_hot_mask))
                    if vrp_vent_mw >= MODIS_VENT_VRP_FLOOR_MW and n_hot_in_vent >= MIN_VENT_PIXELS:
                        n_vent_pixels = n_hot_in_vent
                        vent_hotspot_lat = float(lat[r_vent, c_vent])
                        vent_hotspot_lon = float(lon[r_vent, c_vent])
                        vent_hotspot_dist_km = float(haversine_km(vent_lat, vent_lon, vent_hotspot_lat, vent_hotspot_lon))
                    else:
                        vrp_vent_mw = 0.0

    # --- Schema unification (S14 D6) ---
    # S30: portar Regla D Test 1-priority desde process_viirs.py.
    # Cuando eruption-path detecta lejos (Salar Atacama caso Lascar MODIS) Y
    # Test 1 detecta señal sub-pixel summit (cráter), Test 1 GANA. Sin este
    # fix los 63 FNs MODIS Lascar quedaban "far" porque el primary_cluster
    # caía en el Salar a 19-27km.
    test1_hotspot_dist_km = None
    if (test1_triggered and test1_centroid_lat is not None
            and vent_lat is not None and vent_lon is not None):
        from .scan_geometry import haversine_km as _hav
        _d = _hav(vent_lat, vent_lon, np.array([test1_centroid_lat]),
                  np.array([test1_centroid_lon]))
        test1_hotspot_dist_km = float(_d[0]) if hasattr(_d, '__len__') else float(_d)

    test1_summit_hit = (test1_triggered and inner_radius_km is not None
                        and test1_hotspot_dist_km is not None
                        and test1_hotspot_dist_km <= inner_radius_km)
    eruption_far = (hotspot_dist_km is not None and inner_radius_km is not None
                    and hotspot_dist_km > inner_radius_km)

    # S44 fix: si Test 1 es la única fuente (ver process_viirs.py para detalle).
    only_test1_source = (
        test1_triggered and test1_centroid_lat is not None
        and (n_bt_path or 0) == 0
        and (n_nti_path or 0) == 0
        and (n_dnti_ctx_path or 0) == 0
        and (n_eti_path or 0) == 0
    )

    if hotspot_lat is not None and hotspot_lon is not None:
        if test1_summit_hit and eruption_far:
            # Regla D Test 1-priority: eruption far + Test 1 summit → Test 1 gana.
            final_hotspot_lat = test1_centroid_lat
            final_hotspot_lon = test1_centroid_lon
            final_hotspot_dist_km = test1_hotspot_dist_km
            final_hotspot_source = "test1"
        elif only_test1_source:
            # S44 fix Tupungatito FN: Test 1 única fuente.
            final_hotspot_lat = test1_centroid_lat
            final_hotspot_lon = test1_centroid_lon
            final_hotspot_dist_km = test1_hotspot_dist_km
            final_hotspot_source = "test1"
        else:
            final_hotspot_lat = hotspot_lat
            final_hotspot_lon = hotspot_lon
            final_hotspot_dist_km = hotspot_dist_km
            final_hotspot_source = "eruption"
    elif test1_summit_hit:
        # No hay eruption pero Test 1 detectó summit.
        final_hotspot_lat = test1_centroid_lat
        final_hotspot_lon = test1_centroid_lon
        final_hotspot_dist_km = test1_hotspot_dist_km
        final_hotspot_source = "test1"
    elif vent_hotspot_lat is not None and vent_hotspot_lon is not None:
        final_hotspot_lat = vent_hotspot_lat
        final_hotspot_lon = vent_hotspot_lon
        final_hotspot_dist_km = vent_hotspot_dist_km
        final_hotspot_source = "vent"
    else:
        final_hotspot_lat = None
        final_hotspot_lon = None
        final_hotspot_dist_km = None
        final_hotspot_source = None

    distance_class = None
    if final_hotspot_dist_km is not None and inner_radius_km is not None:
        distance_class = "summit" if final_hotspot_dist_km <= inner_radius_km else "far"

    # S30: VRP recompute cuando final_hotspot_source='test1' — replica fix
    # S26 D de process_viirs.py. Sin esto vrp_mw queda como suma del cluster
    # eruption far (Salar) o 0. Recomputamos VRP usando SOLO pixels Test 1
    # con L_bg LOCAL del ring 1-3km del cráter (no global del ROI 25km).
    # S32 P2 Driver B — Test 1 pixel-level filter (Coppola 2016a Tabla 1).
    # Ver explicación en process_viirs.py. Default OFF.
    test1_hot_filtered = test1_hot
    if (ENABLE_TEST1_PIXEL_FILTER and final_hotspot_source == "test1"
            and inner_radius_km is not None
            and not np.isnan(t_bg) and not np.isnan(std_bg)):
        pixel_thr_mask = dual_roi_bt_threshold(
            bt=bt_mir,
            roi_mask=np.ones_like(bt_mir, dtype=bool),
            dist_km=vent_dist_per_pixel,
            t_bg=t_bg, std_bg=std_bg,
            inner_km=inner_radius_km,
            n_sigma_summit=N_SIGMA_MIR_SUMMIT,
            n_sigma_scene=N_SIGMA_MIR_SCENE,
            anomaly_floor_k=ANOMALY_THRESHOLD_K,
            max_sigma_cap_k=MAX_SIGMA_COMPONENT_K,
        )
        test1_hot_filtered = test1_hot & pixel_thr_mask

    # S33 D4 fix — effective L_bg para Test 1 VRP (ver process_viirs.py).
    # S39 D4 per-volcano: combinar profile flag (ENABLE_TEST1_LBG_GLOBAL) con
    # field per-volcán (lbg_global_compatible) — solo aplica si AMBOS son true.
    # Esto evita regresión Tupungatito glaciar (donde global > local empeora
    # ΔL) y permite el fix donde ring 1-3km está caliente (Lascar cráter
    # permanente, Lastarria fumarolas).
    if ENABLE_TEST1_LBG_GLOBAL and lbg_global_compatible and not np.isnan(t_bg):
        # MODIS Banda 21 — Planck 3.929 µm
        effective_L_bg = float(C1 / (BAND21_LAMBDA ** 5 * (np.exp(C2 / (BAND21_LAMBDA * t_bg)) - 1)))
    else:
        effective_L_bg = test1_L_bg_local

    if (final_hotspot_source == "test1" and test1_n_contrib > 0
            and effective_L_bg is not None
            and not np.isnan(effective_L_bg)):
        t1_rows, t1_cols = np.where(test1_hot_filtered)
        if len(t1_rows) > 0:
            t1_bt = bt_mir[t1_rows, t1_cols]
            t1_rad = C1 / (BAND21_LAMBDA ** 5 * (np.exp(C2 / (BAND21_LAMBDA * t1_bt)) - 1))
            t1_delta_L = np.maximum(t1_rad - effective_L_bg, 0.0)
            t1_area = pixel_areas[t1_rows, t1_cols]
            t1_vrp = t1_area * WOOSTER_COEFF * t1_delta_L / 1e6
            vrp_mw = float(np.sum(t1_vrp))

    # S31+ fix magnitud: cluster_hotspots (8-conn pixel-vecindad scipy.label)
    # — ver explicación en process_viirs.py.
    if (final_hotspot_source == "test1" and test1_n_contrib > 0
            and effective_L_bg is not None
            and not np.isnan(effective_L_bg)):
        t1_vrp_2d = np.zeros_like(bt_mir, dtype=np.float64)
        t1_rows, t1_cols = np.where(test1_hot_filtered)
        if len(t1_rows) > 0:
            t1_bt = bt_mir[t1_rows, t1_cols]
            t1_rad = C1 / (BAND21_LAMBDA ** 5 * (np.exp(C2 / (BAND21_LAMBDA * t1_bt)) - 1))
            t1_delta_L = np.maximum(t1_rad - effective_L_bg, 0.0)
            t1_area = pixel_areas[t1_rows, t1_cols]
            t1_vrp_arr = t1_area * WOOSTER_COEFF * t1_delta_L / 1e6
            t1_vrp_2d[t1_rows, t1_cols] = t1_vrp_arr
            # S95 (A45) — gap A07: el path Test1 calculaba la magnitud pero dejaba
            # anomaly_pixels=[] vacío → bloqueaba F5' display y rompía el mapa de
            # píxeles del dashboard para records MODIS pure-Test1. Espejo del fix
            # S94 (PR #294) en process_viirs.py:1486. Poblar desde t1_vrp_2d (los
            # mismos píxeles que ya alimentan pc.vrp_mw). NO cambia detección ni
            # magnitud — solo serializa píxeles ya calculados.
            anomaly_pixels = build_anomaly_pixels(t1_vrp_2d, lat, lon, dist, bt_mir)
            # S38: aplicar también strategy vent-anchored al cluster Test 1.
            _t1_strategy = ("vent_anchored" if (ENABLE_VENT_ANCHORED_CLUSTERING
                                                 and inner_radius_km is not None)
                             else "vrp_max")
            _t1_inner = inner_radius_km if _t1_strategy == "vent_anchored" else None
            t1_clusters = cluster_hotspots(
                test1_hot_filtered, lat, lon, vent_lat, vent_lon,
                connectivity=8, vrp_per_pixel=t1_vrp_2d,
                strategy=_t1_strategy, inner_radius_km=_t1_inner,
            )
            if t1_clusters:
                top = t1_clusters[0]
                _vrp_t = float(top["vrp_mw"])
                # S109 §1 — magnitud núcleo focal/contextual (espejo del bloque eruption).
                _focal_degraded_t = None
                if ENABLE_FOCAL_CLUSTER_MAGNITUDE:
                    _vrp_t, _focal_n_t, _focal_degraded_t = cluster_focal_vrp_mw(
                        top["pixel_indices"], t1_vrp_2d, dnti_ctx_hot,
                        keep_peak=FOCAL_CLUSTER_KEEP_PEAK,
                    )
                # S71 D9 Opción C — cap si firing contextual-only en cirrus.
                _d9_capped_t = False
                if _path_d_cap_active and _vrp_t > PATH_D_ONLY_CAP_MW:
                    _vrp_t = PATH_D_ONLY_CAP_MW
                    _d9_capped_t = True
                primary_cluster = {
                    "n_pixels": top["n_pixels"],
                    "vrp_mw": round(_vrp_t, 3),
                    "centroid_lat": round(top["centroid_lat"], 5),
                    "centroid_lon": round(top["centroid_lon"], 5),
                    "centroid_dist_km": round(top["centroid_dist_km"], 3),
                }
                if _d9_capped_t:
                    primary_cluster["d9_capped"] = True
                if _focal_degraded_t is not None:
                    primary_cluster["focal_magnitude"] = True
                    primary_cluster["focal_degraded"] = bool(_focal_degraded_t)
                # F52-B S77 (A45) — single-pixel mode régimen sub-MW.
                _pix_vrps_t = [float(t1_vrp_2d[i, j])
                               for (i, j) in top["pixel_indices"]]
                primary_cluster = apply_single_pixel_mode(
                    primary_cluster, _pix_vrps_t,
                    enabled=ENABLE_SINGLE_PIXEL_SUB_MW_MODE,
                    threshold_mw=SUB_MW_REGIME_THRESHOLD_MW,
                    max_pixels=SINGLE_PIXEL_MAX_CLUSTER_PIXELS,
                )
                n_hotspots_clustered = len(t1_clusters)

    # S106 — ancla espacial honesta MODIS (design 2026-06-11 §3.1, espejo de
    # process_viirs.py). SOLO posición: los bloques de magnitud de arriba ya
    # corrieron con la semántica legacy. Flag SEPARADO del de VIIRS375
    # (enable_honest_anchor_modis).
    # S111 D11 (M1, design 2026-06-16) — el override solo se aplica si el MODIS
    # tiene señal-summit propia (first_pass_summit>0). Sin ella, el cluster
    # near-crater es artefacto topográfico A69 (recaptura second-pass/gate S85,
    # A55) → NO override → queda la clasificación legacy (far, como hoy). Cura el
    # FN D12 Láscar (first-pass genuino) sin promover el artefacto NdC.
    _apply_honest_anchor_modis = honest_anchor_applies(
        enabled=ENABLE_HONEST_ANCHOR_MODIS,
        first_pass_gate_enabled=ENABLE_HONEST_ANCHOR_MODIS_FIRST_PASS_GATE,
        n_first_pass_summit=n_first_pass_summit,
    )
    _ha_nti_peak = None
    if _apply_honest_anchor_modis:
        if (HONEST_ANCHOR_TEST1_MODE == "nti_peak" and nti is not None
                and vent_dist_per_pixel is not None):
            _roi3 = (vent_dist_per_pixel <= TEST1_ROI_KM) & ~np.isnan(nti)
            if bool(_roi3.any()):
                _pk_flat = np.nanargmax(np.where(_roi3, nti, -np.inf))
                _pk_r, _pk_c = np.unravel_index(int(_pk_flat), nti.shape)
                _ha_nti_peak = {
                    "lat": round(float(lat[_pk_r, _pk_c]), 5),
                    "lon": round(float(lon[_pk_r, _pk_c]), 5),
                    "dist_km": round(float(vent_dist_per_pixel[_pk_r, _pk_c]), 3),
                }
        _ha_vent_hs = None
        if vent_hotspot_lat is not None and vent_hotspot_lon is not None:
            _ha_vent_hs = {"lat": vent_hotspot_lat, "lon": vent_hotspot_lon,
                           "dist_km": vent_hotspot_dist_km}
        _ha_loose = None
        if hotspot_lat is not None and hotspot_lon is not None:
            _ha_loose = {"lat": hotspot_lat, "lon": hotspot_lon,
                         "dist_km": hotspot_dist_km}
        (final_hotspot_lat, final_hotspot_lon, final_hotspot_dist_km,
         final_hotspot_source) = resolve_honest_anchor(
            ctx_cluster=ctx_cluster_anchor,
            test1_triggered=bool(test1_triggered),
            test1_summit_hit=bool(test1_summit_hit),
            vent_lat=vent_lat, vent_lon=vent_lon,
            nti_peak=_ha_nti_peak,
            vent_hotspot=_ha_vent_hs,
            loose_pixel=_ha_loose,
            inner_radius_km=inner_radius_km,
            mode=HONEST_ANCHOR_TEST1_MODE,
        )
        distance_class = None
        if final_hotspot_dist_km is not None and inner_radius_km is not None:
            distance_class = ("summit" if final_hotspot_dist_km <= inner_radius_km
                              else "far")

    return {
        "vrp_mw": round(vrp_mw, 3),
        "vrp_vent_mw": round(vrp_vent_mw, 3),
        "n_anomalous_pixels": n_anomalous,
        "n_hotspots_clustered": n_hotspots_clustered,
        "primary_cluster": primary_cluster,
        # S29: Test 1 integrated-ROI extendido a MODIS Banda 21.
        "triggered_test1": test1_triggered,
        "n_test1_pixels": test1_n_contrib,
        "test1_k_observed": round(test1_k_obs, 2) if test1_k_obs else 0.0,
        "n_vent_pixels": n_vent_pixels,
        "vent_hotspot_lat": vent_hotspot_lat,
        "vent_hotspot_lon": vent_hotspot_lon,
        "vent_hotspot_dist_km": round(vent_hotspot_dist_km, 3) if vent_hotspot_dist_km is not None else None,
        "hotspot_lat": hotspot_lat,
        "hotspot_lon": hotspot_lon,
        "hotspot_dist_km": hotspot_dist_km,
        "final_hotspot_lat": final_hotspot_lat,
        "final_hotspot_lon": final_hotspot_lon,
        "final_hotspot_dist_km": round(final_hotspot_dist_km, 3) if final_hotspot_dist_km is not None else None,
        "final_hotspot_source": final_hotspot_source,
        "distance_class": distance_class,
        "anomaly_pixels": anomaly_pixels,
        "t_bg_k": round(t_bg, 2),
        "t_max_k": round(t_max, 2),
        # Diagnostic fields (session 6) — present when MODIS path runs.
        "diag_sigma_bg_k": round(std_bg, 3),
        "diag_t_max_dist_km": round(t_max_dist_km_diag, 2) if not (t_max_dist_km_diag != t_max_dist_km_diag) else None,
        "diag_roi_p95_k": round(roi_p95, 2) if not (roi_p95 != roi_p95) else None,
        "diag_eff_threshold_k": round(effective_threshold, 2),
        # E3 NTI diagnostics
        "diag_nti_bg": round(nti_bg, 4) if not (nti_bg != nti_bg) else None,
        "diag_nti_std": round(nti_std, 4) if not (nti_std != nti_std) else None,
        "diag_nti_max": round(nti_max, 4) if not (nti_max != nti_max) else None,
        "diag_n_bt_path": n_bt_path,
        "diag_n_nti_path": n_nti_path,
        "diag_n_dnti_ctx_path": n_dnti_ctx_path,
        "diag_n_eti_path": n_eti_path,  # S37 H_D8_5
        # S46 drift23 — first_pass_tests_2_and_3 diag fields (Task 4 wiring).
        # Persistir n_first_pass_pixels + estadísticos μ/σ del background usados
        # en la regla μ+C2σ. Ausentes (0/None) si flag OFF o sin background válido.
        "diag_n_first_pass_pixels": (
            fp_diag["n_first_pass_pixels"] if fp_diag is not None else 0),
        # S111 D11 — seeds del first-pass dentro del inner_radius (señal-summit
        # propia). Gate del ancla honesta MODIS: >0 → ancla al cráter; 0 →
        # artefacto topográfico (recaptura S85, A55) → no se promueve.
        "diag_n_first_pass_summit": n_first_pass_summit,
        "diag_mu_dnti": (
            fp_diag["mu_dnti"] if fp_diag is not None else None),
        "diag_sd_dnti": (
            fp_diag["sd_dnti"] if fp_diag is not None else None),
        "diag_mu_deti": (
            fp_diag["mu_deti"] if fp_diag is not None else None),
        "diag_sd_deti": (
            fp_diag["sd_deti"] if fp_diag is not None else None),
        "diag_n_bg_used_first_pass": (
            fp_diag["n_bg_used"] if fp_diag is not None else 0),
        # S46 Task 5 — second_pass_adjacent recapture diag (Drift #4).
        "diag_n_second_pass_recapture": n_second_pass_recapture,
        "sensor": "MODIS_TERRA" if "MOD0" in hdf_path.name else "MODIS_AQUA",
        "granule": hdf_path.name,
        "product_version": "nrt" if "_NRT" in hdf_path.name else "standard",
        "datetime_utc": _parse_datetime(hdf_path.name),
        # S122 — geometría de observación en el punto reportado (research).
        **observation_geometry(
            data["lat"], data["lon"], data.get("angles"),
            final_hotspot_lat if final_hotspot_lat is not None else vent_lat,
            final_hotspot_lon if final_hotspot_lon is not None else vent_lon,
        ),
    }


def _parse_datetime(filename: str) -> str:
    try:
        parts = filename.split(".")
        year = int(parts[1][1:5])
        doy = int(parts[1][5:8])
        hour = int(parts[2][:2])
        minute = int(parts[2][2:4])
        import datetime
        dt = datetime.datetime(year, 1, 1) + datetime.timedelta(days=doy - 1,
                                                                  hours=hour,
                                                                  minutes=minute)
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return "unknown"
