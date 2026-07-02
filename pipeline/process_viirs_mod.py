# ════════════════════════════════════════════════════════════════════
# FICHA SDA · process_viirs_mod.py · SDA: VRP Chile (clon MIROVA) · ID: VRP-CL
# Objetivo      : Detectar y cuantificar anomalias termicas en granulos VIIRS M-band 750m
#                 (VNP02MOD/VJ102MOD) — equivalente al canal 'VIIRS' por defecto de MIROVA.
# Lógica        : Misma formula VRP MIROVA-style que process_viirs.py pero sobre banda M13 (4.05um, area
#                 750x750m), con su coeficiente Wooster propio.
# Modelo/método : Reglas fisicas deterministicas (Wooster MIR; Coppola 2016a). NO es caja negra (punto 5.5
#                 Res.372).
# Datos entrada : Radiancia/BT VIIRS M13 (MIR) y M15 (TIR). SIN datos personales.
# Variables     : NTI/dNTI, T de fondo, umbrales N·sigma, area de pixel 750m (nadir-fijo), distancia al
#                 crater.
# Limitaciones  : Mayor area de pixel amplifica el gradiente topografico crater-nieve (A69/A80); dispersion
#                 del centroide; solo noche por contaminacion solar.
# Refs/datos    : Coppola 2016a, Massimetti tesis (adaptacion VIIRS). Entrenamiento: No aplica (sin ML).
#                 Ficha: docs/FICHA_SDA_VRP_CHILE.md
# ════════════════════════════════════════════════════════════════════
"""
process_viirs_mod.py — Calculate VRP from VIIRS VNP02MOD / VJ102MOD L1B granules.

These are the 750m M-band products. Band M13 (4.05 µm) is the primary channel,
equivalent to MIROVA's "VIIRS" (750m) sensor.

This is the same spatial resolution sensor that MIROVA displays as the default
VIIRS channel in its web interface.

Algorithm: same MIROVA-style VRP formula as process_viirs.py but for M-band.
  - Band M13 (4.05 µm, 750m): primary MIR channel
  - Pixel area: 750² = 562,500 m²

References:
  - VIIRS L1B User Guide (M-band section)
  - Coppola et al. 2015 (MIROVA)
"""

import numpy as np
from pathlib import Path

try:
    import h5py
    H5_AVAILABLE = True
except ImportError:
    H5_AVAILABLE = False

from .scan_geometry import viirs_pixel_areas, roi_mask_bbox
from .exclusion_zones import filter_hot_mask, guard_exclude_zones
from .clustering import cluster_hotspots, cluster_pixels_geographic
from .path_d_cap import apply_d9_scene_cap  # F50/S77

# S23 T17: constantes físicas centralizadas en pipeline/constants.py
from pipeline.constants import SIGMA  # kept for reference, not used in MIR VRP
# Nadir pixel area; actual area is per-pixel via sensor_zenith correction.
NADIR_PIXEL_AREA_M2 = 750.0 ** 2   # 562,500 m²

# Planck constants for spectral radiance (W/m²/sr/µm)
from pipeline.constants import C1_PLANCK, C2_PLANCK  # 2hc², hc/k Planck

# Wooster MIR radiance coefficient.
# For VIIRS M13 (4.05 µm, 750 m) use 19.7 per empirical calibration against
# MIROVA v2.5 OSF (experiments/21_calibrate_k_viirs375_vs_osf.py): reconstructs
# exactly the effective coefficient 1.97e7 × A_pix(0.5625 km²) = 11,081,250
# that MIROVA publishes for VIIRS_M across 2,515 Chilean rows with 0.169% error.
# Not 18.9 (which is MODIS 1km). Difference is band center (4.05 vs 3.96 µm).
WOOSTER_COEFF = 19.7   # VIIRS M13 750m, empirically validated S14 2026-04-21

FLAG_DNS = {65532, 65533, 65534, 65535}

# --- All detection thresholds come from the active profile ---
# See pipeline/profiles/*.yaml. Profile selected via $VRP_PROFILE.
from pipeline.profile import (
    ANOMALY_THRESHOLD_K,
    N_SIGMA_MIR,
    BG_INNER_KM,
    BG_OUTER_KM,
    ENABLE_ERUPTION_PATH,
    ENABLE_VENT_PATH,
    VENT_THRESHOLD_K,
    NTI_K1_NIGHT,
    NTI_BT_SANITY_K,
    ENABLE_NTI_RELATIVE_PATH,
    NTI_REL_N_SIGMA,
    NTI_REL_MIN_FLOOR,
    N_SIGMA_VENT,
    MAX_VENT_SIGMA_CONTRIB_K,
    MIN_VENT_PIXELS,
    MAX_SIGMA_COMPONENT_K,
    DNTI_CONTEXTUAL_C1,
    DNTI_CONTEXTUAL_C1_SUMMIT,
    DNTI_CONTEXTUAL_C1_SCENE,
    ENABLE_DNTI_CONTEXTUAL_PATH,
    ENABLE_DNTI_DUAL_ROI,
    ENABLE_DUAL_ROI_BT,
    ENABLE_TEST1_PIXEL_FILTER,
    ENABLE_FINAL_PIXEL_FILTER,
    ENABLE_TEST1_LBG_GLOBAL,
    N_SIGMA_MIR_SUMMIT,
    N_SIGMA_MIR_SCENE,
    ENABLE_EXCLUDE_ZONES,
    ENABLE_TEST1_PATH,
    TEST1_K_SIGMA,
    TEST1_MIR_RELATIVE,
    TEST1_ROI_KM,
    TEST1_INNER_RING_KM,
    P95_VENT_EXCLUSION_VIIRS750_KM,
    ENABLE_ETI_QUADRATIC_SCENE,
    ENABLE_SECOND_PASS_ADJACENT,
    ENABLE_SECOND_PASS_INTRA_RADIO_GATE,
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
    ENABLE_NADIR_FIXED_PIXEL_AREA_VIIRS,
    ENABLE_FIRST_PASS_TESTS_2_AND_3,
    ENABLE_DUAL_ROI_FIRST_PASS,
    ENABLE_DUAL_ROI_SECOND_PASS,
    VIIRS_C2_OVERRIDE_NIGHT,
    PATH_D_ATM_GATE_TBG_MIN_K,
    PATH_D_REQUIRES_COVALIDATION,
    PATH_D_ONLY_CAP_MW,
    PATH_D_ONLY_CAP_TBG_MAX_K,
    ENABLE_SINGLE_PIXEL_SUB_MW_MODE,
    SUB_MW_REGIME_THRESHOLD_MW,
    SINGLE_PIXEL_MAX_CLUSTER_PIXELS,
    ENABLE_HONEST_ANCHOR_VIIRS750,
    HONEST_ANCHOR_TEST1_MODE,
    ENABLE_FOCAL_CLUSTER_MAGNITUDE_VIIRS750,
    FOCAL_CLUSTER_KEEP_PEAK,
)
from .anchor import resolve_honest_anchor  # S106 ancla espacial honesta
from .single_pixel_mode import apply_single_pixel_mode
from .vrp_regimes import cluster_focal_vrp_mw  # S112 magnitud núcleo-focal (A69/D11)
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
from .test1_integrated import compute_test1_mir
from .anomaly_pixels import build_anomaly_pixels
from .second_pass_intra_radio import apply_second_pass_intra_radio_gate  # S85 F-S81-B'

# M-band wavelengths (µm)
M13_INDEX = 12       # M13 index within VNP02MOD observation_data (0-based)
M13_LAMBDA = 4.050   # µm — primary MIR channel
M15_LAMBDA = 10.763  # µm — TIR channel for NTI computation


def _sensor_label_from_filename(filename: str) -> str:
    """Map VIIRS M-band 750m L1B filename → sensor label.

    VNP02MOD  → VIIRS_SNPP_750
    VJ102MOD  → VIIRS_NOAA20_750   (JPSS-1)
    VJ202MOD  → VIIRS_NOAA21_750   (JPSS-2, S18)

    Ver pipeline/process_viirs.py para el equivalente I-band.
    """
    if filename.startswith("VNP"):
        return "VIIRS_SNPP_750"
    if filename.startswith("VJ2"):
        return "VIIRS_NOAA21_750"
    return "VIIRS_NOAA20_750"


def read_viirs_mod_l1b(l1b_path: Path) -> dict:
    """
    Read VIIRS VNP02MOD HDF5/NetCDF4 file.

    Returns:
        {"M13": ndarray float32 — brightness temperature (K)}

    Uses BT LUT if available, else Planck inversion fallback.
    """
    if not H5_AVAILABLE:
        raise ImportError("h5py required. pip install h5py")

    # F2.8 fix (S73 Task 3 H2+H10): VIIRS M-band saturation guard simétrico a I-band.
    # M13 (4.05 µm low-gain fire channel) sat ~634 K per Coppola 2025 Cap.11 Table 1.
    # M15 (10.76 µm TIR) sat ~423 K análogo a I05. Quality flags bit-2 schema
    # idéntico al de I-band (VIIRS L1B UserGuide Aug 2021 Tabla C.1).
    SAT_BIT_MASK = 0b100
    BT_LUT_MAX_MBAND = {"M13": 634.0, "M15": 423.0}

    result = {}
    with h5py.File(l1b_path, "r") as f:
        obs = f["observation_data"]

        # Try direct M13 dataset first
        band_key = "M13"
        if band_key not in obs:
            return result

        dn = obs[band_key][:]
        # F2.8 H2: leer quality_flags M13
        qf_key = f"{band_key}_quality_flags"
        qf = obs[qf_key][:] if qf_key in obs else None

        lut_key = "M13_brightness_temperature_lut"
        if lut_key in obs:
            lut = obs[lut_key][:]
            bt = lut[dn].astype(np.float32)
            flag_mask = np.isin(dn, list(FLAG_DNS))
            bt[flag_mask] = np.nan
            bt[bt < 0] = np.nan
            if qf is not None:
                bt[(qf & SAT_BIT_MASK) != 0] = np.nan
            lut_max = BT_LUT_MAX_MBAND.get(band_key)
            if lut_max is not None:
                bt[bt >= lut_max - 0.5] = np.nan
        else:
            ds = obs[band_key]
            scale  = float(ds.attrs.get("scale_factor", 1.0))
            offset = float(ds.attrs.get("add_offset", 0.0))
            rad = dn.astype(np.float32) * scale + offset
            flag_mask = np.isin(dn, list(FLAG_DNS))
            rad[flag_mask] = np.nan
            if qf is not None:
                rad[(qf & SAT_BIT_MASK) != 0] = np.nan
            # Planck inversion
            C1, C2 = 1.191042e8, 14388.0
            with np.errstate(invalid="ignore", divide="ignore"):
                bt = C2 / (M13_LAMBDA * np.log(C1 / (rad * M13_LAMBDA ** 5) + 1))

        result["M13"] = bt

        # --- M15 TIR band (10.763 µm) for NTI computation ---
        band_key_15 = "M15"
        if band_key_15 in obs:
            dn15 = obs[band_key_15][:]
            # F2.8 H2: leer quality_flags M15
            qf15_key = f"{band_key_15}_quality_flags"
            qf15 = obs[qf15_key][:] if qf15_key in obs else None
            lut_key_15 = "M15_brightness_temperature_lut"
            if lut_key_15 in obs:
                lut15 = obs[lut_key_15][:]
                bt15 = lut15[dn15].astype(np.float32)
                flag_mask_15 = np.isin(dn15, list(FLAG_DNS))
                bt15[flag_mask_15] = np.nan
                bt15[bt15 < 0] = np.nan
                if qf15 is not None:
                    bt15[(qf15 & SAT_BIT_MASK) != 0] = np.nan
                lut_max_15 = BT_LUT_MAX_MBAND.get(band_key_15)
                if lut_max_15 is not None:
                    bt15[bt15 >= lut_max_15 - 0.5] = np.nan
            else:
                ds15 = obs[band_key_15]
                scale15  = float(ds15.attrs.get("scale_factor", 1.0))
                offset15 = float(ds15.attrs.get("add_offset", 0.0))
                rad15 = dn15.astype(np.float32) * scale15 + offset15
                flag_mask_15 = np.isin(dn15, list(FLAG_DNS))
                rad15[flag_mask_15] = np.nan
                if qf15 is not None:
                    rad15[(qf15 & SAT_BIT_MASK) != 0] = np.nan
                # Planck inversion for M15
                C1, C2 = 1.191042e8, 14388.0
                with np.errstate(invalid="ignore", divide="ignore"):
                    bt15 = C2 / (M15_LAMBDA * np.log(C1 / (rad15 * M15_LAMBDA ** 5) + 1))
            result["M15"] = bt15

    return result


def read_viirs_mod_geo(geo_path: Path) -> dict:
    """Read VNP03MOD geolocation file. Returns lat/lon and sensor_zenith arrays."""
    if not H5_AVAILABLE:
        raise ImportError("h5py required.")

    with h5py.File(geo_path, "r") as f:
        geo = f["geolocation_data"]
        lat = geo["latitude"][:].astype(np.float32)
        lon = geo["longitude"][:].astype(np.float32)
        lat[lat < -90] = np.nan
        lon[lon < -180] = np.nan
        if "sensor_zenith" in geo:
            sz = geo["sensor_zenith"][:].astype(np.float32)
        elif "satellite_zenith" in geo:
            sz = geo["satellite_zenith"][:].astype(np.float32)
        else:
            sz = np.zeros_like(lat)
        sz[np.isnan(lat)] = np.nan
    return {"lat": lat, "lon": lon, "sensor_zenith": sz}


def bt_to_spectral_radiance(bt: np.ndarray, wavelength_um: float) -> np.ndarray:
    """Convert brightness temperature (K) to spectral radiance (W/m²/sr/µm) via Planck."""
    with np.errstate(invalid="ignore", divide="ignore", over="ignore"):
        return C1_PLANCK / (wavelength_um ** 5 * (np.exp(C2_PLANCK / (wavelength_um * bt)) - 1))


# S23 Task 2: haversine_km centralizado en pipeline/scan_geometry.py
from pipeline.scan_geometry import haversine_km


def calculate_vrp(l1b_path: Path, geo_path: Path,
                  volcano_lat: float, volcano_lon: float,
                  radius_km: float = 30.0,
                  vent_lat: float = None, vent_lon: float = None,
                  vent_radius_km: float = 4.0,
                  inner_radius_km: float | None = None,
                  exclude_zones: list = None,
                  active_water_bodies: list = None,
                  lbg_global_compatible: bool = False,
                  local_kernel_bg_compatible: bool = False,
                  lava_lake_magmatic: bool = False) -> dict | None:
    """
    Calculate VRP from VIIRS 750m M-band granule (VNP02MOD / VJ102MOD).

    Nota S99: `lava_lake_magmatic` se acepta por paridad de firma con
    process_viirs (GR1) pero NO se usa aquí — Eq.16 lava lake es régimen
    sub-píxel I-band 375m, no M-band 750m.

    Args:
        vent_lat/vent_lon: Optional vent coordinates for weak-signal detection.
        vent_radius_km: Radius for vent-scale search.
        inner_radius_km: MIROVA-style visual classification radius (S14 D1).
            If None, distance_class is None.
        local_kernel_bg_compatible: per-vol opt-in para kernel local 3x3
            background (Coppola 2024 §1129). **NOTA F2.9 S72**: aceptado en
            signature para evitar TypeError en `scripts/run_pipeline.py:276`,
            pero la implementación kernel-local para M-band aún no existe
            (a diferencia de process_viirs.py I-band 375m). Para vols opt-in
            (Villarrica/PP/Lastarria/Chaiten/PCC), M-band sigue usando t_bg
            global del ring 5-25km mientras se implementa T1.5+ S73. TODO:
            replicar `compute_local_background` block de process_viirs.py:856.

    Returns dict with VRP or None if granule does not cover volcano.
    """
    bands = read_viirs_mod_l1b(l1b_path)
    if "M13" not in bands:
        return None

    geo = read_viirs_mod_geo(geo_path)
    lat, lon = geo["lat"], geo["lon"]
    # Per-pixel ground area corrected for off-nadir geometry
    pixel_areas = viirs_pixel_areas(
        geo["sensor_zenith"],
        NADIR_PIXEL_AREA_M2,
        nadir_fixed=ENABLE_NADIR_FIXED_PIXEL_AREA_VIIRS,
    )
    dist = haversine_km(volcano_lat, volcano_lon, lat, lon)

    # P3.1 S15: per-pixel distance from effective vent for dual-ROI.
    if vent_lat is not None and vent_lon is not None:
        vent_dist_per_pixel = haversine_km(vent_lat, vent_lon, lat, lon)
    else:
        vent_dist_per_pixel = dist

    # S15 Tema E: bbox cuadrado (paridad MIROVA KMZ 50x50 km).
    roi_mask = roi_mask_bbox(lat, lon, volcano_lat, volcano_lon, radius_km)
    bg_mask  = (dist >= BG_INNER_KM) & (dist <= BG_OUTER_KM)

    if not np.any(roi_mask):
        return None

    bt = bands["M13"]

    # S46 drift #1b: pre-computar NTI antes del bg_vals para que
    # compute_bg_stats pueda excluir Test 1 K1 active pixels del bg ring
    # (Coppola 2016a:352-356). NTI requiere M15 (TIR). Si no está, nti=None
    # y el flag drift #1b no aplica (compute_bg_stats opera legacy).
    nti = None
    if "M15" in bands:
        bt_mir = bands["M13"]
        bt_tir = bands["M15"]
        L_mir_all = bt_to_spectral_radiance(bt_mir, M13_LAMBDA)
        L_tir_all = bt_to_spectral_radiance(bt_tir, M15_LAMBDA)
        valid_both = ~np.isnan(L_mir_all) & ~np.isnan(L_tir_all) & (L_mir_all + L_tir_all > 0)
        nti = np.full_like(L_mir_all, np.nan)
        nti[valid_both] = (L_mir_all[valid_both] - L_tir_all[valid_both]) / (L_mir_all[valid_both] + L_tir_all[valid_both])

    t_bg, std_bg, _n_bg = compute_bg_stats(
        bt=bt,
        bg_mask=bg_mask,
        nti=nti,
        nti_k1_threshold=NTI_K1_NIGHT,
        enable_test1_k1_bg_exclude=ENABLE_TEST1_K1_BG_EXCLUDE,
        min_bg_pixels=10,
    )
    if t_bg is None:
        return None

    # S15 Tema F: sigma-cap eruption-path (cura Tupungatito recall 0.04).
    sigma_component = min(N_SIGMA_MIR * std_bg, MAX_SIGMA_COMPONENT_K)
    threshold = max(ANOMALY_THRESHOLD_K, sigma_component)

    # --- NTI: Normalized Thermal Index (Coppola 2015) ---
    # NTI = (L_MIR - L_TIR) / (L_MIR + L_TIR) per-pixel
    # Anomaly when NTI_pixel > NTI_bg_median + NTI_threshold
    # This is MIROVA's primary detection method — filters solar contamination
    # and works contextually against local background.
    nti_max = float("nan")
    nti_bg = float("nan")
    nti_std = float("nan")
    n_nti_anomalous = 0
    # S22.1 paridad MODIS schema (H_S21_11). roi_p95 y t_max_dist_km_diag se
    # rellenan en el bloque BT cuando hay ROI válida; quedan NaN si no.
    roi_p95 = float("nan")
    t_max_dist_km_diag = float("nan")

    if nti is not None:
        # Background NTI statistics (NTI ya computado arriba para drift #1b)
        bg_nti = nti[bg_mask & ~np.isnan(nti)]
        if len(bg_nti) >= 10:
            nti_bg = float(np.median(bg_nti))
            nti_std = float(np.std(bg_nti))
            nti_threshold = nti_bg + max(0.005, 3.0 * nti_std)

            # ROI NTI anomalies
            roi_nti = nti[roi_mask]
            roi_nti_valid = roi_nti[~np.isnan(roi_nti)]
            if len(roi_nti_valid) > 0:
                nti_max = float(np.max(roi_nti_valid))
                n_nti_anomalous = int(np.sum(roi_nti_valid > nti_threshold))

    # Additional local-ROI filter: avoid topographic false positives.
    # Session 6 E1 fix: exclude a vent safety zone from the p95 calculation
    # so the vent pixel doesn't inflate its own filter. See process_modis.py
    # for the full rationale.
    # S23 T18: configurable via profile (era hardcoded 4.0 km).
    P95_VENT_EXCLUSION_KM = P95_VENT_EXCLUSION_VIIRS750_KM
    roi_bt_full = np.where(roi_mask & ~np.isnan(bt), bt, np.nan)
    if vent_lat is not None and vent_lon is not None:
        vent_dist_for_p95 = haversine_km(vent_lat, vent_lon, lat, lon)
        p95_mask = (roi_mask
                    & ~np.isnan(bt)
                    & (vent_dist_for_p95 > max(vent_radius_km, P95_VENT_EXCLUSION_KM)))
        roi_valid = bt[p95_mask]
    else:
        roi_valid = roi_bt_full[~np.isnan(roi_bt_full)]
    # S120 (cacería): inicializar — la rama dual-ROI BT (más abajo) referencia
    # local_threshold incondicionalmente; con roi_valid<10 era UnboundLocalError.
    local_threshold = float("nan")
    if len(roi_valid) >= 10:
        roi_p95 = float(np.percentile(roi_valid, 95))
        roi_std = float(np.std(roi_valid))
        local_threshold = roi_p95 + max(3.0, 2.0 * roi_std)
        effective_threshold = max(t_bg + threshold, local_threshold)
    else:
        effective_threshold = t_bg + threshold

    # S22.1 paridad MODIS: distancia al pixel más caliente del ROI.
    if np.any(~np.isnan(roi_bt_full)):
        flat_idx_max = np.nanargmax(roi_bt_full)
        r_max, c_max = np.unravel_index(flat_idx_max, roi_bt_full.shape)
        t_max_dist_km_diag = float(dist[r_max, c_max])

    # --- Dual-PATH detection (logical OR), mirroring process_viirs.py ---
    # A pixel is hot if EITHER:
    #   (A) BT path: bt > effective_threshold (includes p95 local filter)
    #   (B) NTI path: nti > NTI_K1_NIGHT  AND  bt > t_bg + NTI_BT_SANITY_K
    # The OR logic rescues detections on cloudy nights where BT threshold
    # alone fails because std_bg is inflated.

    # Path A — BT path (classic threshold with local p95 filter)
    # S26: si ENABLE_DUAL_ROI_BT, threshold dual summit/scene (Coppola 2016a Tabla 1)
    if (ENABLE_DUAL_ROI_BT and inner_radius_km is not None
            and vent_lat is not None and vent_lon is not None):
        bt_dual_hot = dual_roi_bt_threshold(
            bt=roi_bt_full, roi_mask=roi_mask, dist_km=vent_dist_per_pixel,
            t_bg=t_bg, std_bg=std_bg, inner_km=inner_radius_km,
            n_sigma_summit=N_SIGMA_MIR_SUMMIT,
            n_sigma_scene=N_SIGMA_MIR_SCENE,
            anomaly_floor_k=ANOMALY_THRESHOLD_K,
            max_sigma_cap_k=MAX_SIGMA_COMPONENT_K,
        )
        # Combinar con local_threshold p95 (preserva fix histórico)
        if not np.isnan(local_threshold):
            bt_path_hot = bt_dual_hot & (roi_bt_full > local_threshold)
        else:
            bt_path_hot = bt_dual_hot
    else:
        bt_path_hot = roi_bt_full > effective_threshold
    # S40 cleanup paths viejos: desactivar bt_path_hot si flag OFF.
    if not ENABLE_BT_PATH_HOT:
        bt_path_hot = np.zeros_like(bt_path_hot, dtype=bool)

    # Path B — NTI path (Coppola 2015 Test 1, night)
    # Only valid if NTI was successfully computed (needs both M13+M15)
    if nti is not None and not np.isnan(nti_bg):
        nti_path_hot = (
            roi_mask
            & ~np.isnan(nti)
            & ~np.isnan(bt)
            & (nti > NTI_K1_NIGHT)
            & (bt > (t_bg + NTI_BT_SANITY_K))
        )
    else:
        nti_path_hot = np.zeros_like(roi_mask)

    # Path C — NTI relative path (Session 11).
    # Uses contextual NTI threshold (nti_bg + max(0.005, 3*sigma)) for weak
    # fumarolic signals unreachable by the absolute NTI_K1_NIGHT floor.
    n_nti_rel_path = 0
    if (ENABLE_NTI_RELATIVE_PATH
            and nti is not None
            and not np.isnan(nti_bg)
            and not np.isnan(nti_std)):
        nti_rel_threshold = nti_bg + max(NTI_REL_MIN_FLOOR, NTI_REL_N_SIGMA * nti_std)
        nti_rel_hot = (
            roi_mask
            & ~np.isnan(nti)
            & ~np.isnan(bt)
            & (nti > nti_rel_threshold)
            & (bt > (t_bg + NTI_BT_SANITY_K))
        )
        n_nti_rel_path = int(np.sum(nti_rel_hot))
    else:
        nti_rel_hot = np.zeros_like(roi_mask)

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
    n_eti_path = 0  # S37 H_D8_5 — init aquí para paridad MODIS pattern.
    if (ENABLE_DNTI_CONTEXTUAL_PATH
            and nti is not None
            and not np.isnan(nti_bg)
            and not _path_d_atm_gate_skip):
        # S72 F2.3 — Coppola 2016a SP 426.5 §267-273 también aplican a path D
        # contextual cuando el flag está ON.
        if ENABLE_DNTI_DUAL_ROI and inner_radius_km is not None:
            dnti_ctx_hot = dual_roi_contextual_dnti_hot_mask(
                nti=nti, bt=bt, roi_mask=roi_mask,
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
                nti=nti, bt=bt, roi_mask=roi_mask,
                t_bg=t_bg,
                c1=DNTI_CONTEXTUAL_C1,
                bt_sanity_k=NTI_BT_SANITY_K,
                apply_unsuitable_filters=ENABLE_UNSUITABLE_FILTERS_267_273,
            )
        n_dnti_ctx_path = int(np.sum(dnti_ctx_hot))
    else:
        dnti_ctx_hot = np.zeros_like(roi_mask)

    # S28 — Path Test 1 integrated-ROI MIR (Coppola 2015 §2.2 Eq.1) en VIIRS 750m M13.
    # Extensión post-S27 H_S27_1 (validada en VIIRS 375m). Misma función pura
    # con lambda=M13_LAMBDA=4.05µm. Detecta señal sub-pixel espacialmente
    # extendida que paths per-pixel pierden — esperado rescatar ~20 FNs en
    # Tupungatito (8) + Isluga (10) + PCC (1) según delta S27 madrugada.
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
            bt=bt, lat=lat, lon=lon,
            vent_lat=vent_lat, vent_lon=vent_lon,
            lambda_um=M13_LAMBDA,
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

    # S37 H_D8_5 — path ETI cuadrático scene-wide VIIRS M13/M15 (750m).
    # Mismo flujo que process_viirs.py I04/I05 con λ_MIR=M13_LAMBDA (4.050 μm)
    # y λ_TIR=M15_LAMBDA (10.763 μm). Tests 2 ∧ 3 sobre dNTI/dETI.
    eti_path_hot = np.zeros_like(bt_path_hot, dtype=bool)
    n_eti_path = 0
    if (ENABLE_ETI_QUADRATIC_SCENE
            and "M15" in bands and "M13" in bands
            and inner_radius_km is not None
            and vent_lat is not None and vent_lon is not None
            and not np.isnan(nti_bg)):
        _, nti_app_m = compute_nti_and_nti_app(
            rad_mir=L_mir_all,
            bt_tir=bt_tir,
            lambda_mir_um=M13_LAMBDA,
            lambda_tir_um=M15_LAMBDA,
        )
        mask_valid_eti = (
            roi_mask
            & ~np.isnan(nti) & ~np.isnan(nti_app_m)
            & ~np.isnan(bt_mir)
        )
        eti_2d = compute_eti_scene_quadratic(nti, nti_app_m, mask_valid_eti)
        is_summit = vent_dist_per_pixel <= inner_radius_km
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
        eti_path_hot = (eti_path_hot & roi_mask & ~np.isnan(bt_mir)
                        & (bt_mir > (t_bg + NTI_BT_SANITY_K)))
        n_eti_path = int(np.sum(eti_path_hot))

    hot_mask_2d = combine_hot_paths(
        bt_path_hot=bt_path_hot,
        nti_path_hot=nti_path_hot,
        dnti_ctx_hot=dnti_ctx_hot,
        test1_hot=test1_hot,
        nti_rel_hot=nti_rel_hot,
        eti_path_hot=eti_path_hot,
        enable_test1_k1_retire_from_hot_mask=ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK,
    )

    # S46 Drift #2+#3 — first-pass Tests 2 ∧ 3 (Coppola 2016a SP426.5:316-325).
    # Reemplaza hot_mask_2d con la conjunción Test 2 ∧ Test 3 + dual-ROI Tabla 2.
    # Paths legacy se calcularon arriba (diag) pero no contribuyen cuando ON.
    n_first_pass = 0
    fp_diag = None
    if (ENABLE_FIRST_PASS_TESTS_2_AND_3
            and "M15" in bands and "M13" in bands
            and inner_radius_km is not None
            and not np.isnan(t_bg)
            and not _path_d_atm_gate_skip):
        _, nti_app_fp = compute_nti_and_nti_app(
            rad_mir=L_mir_all,
            bt_tir=bt_tir,
            lambda_mir_um=M13_LAMBDA,
            lambda_tir_um=M15_LAMBDA,
        )
        # S46 Task 6 + Ronda 2 — overrides C1/C2 summit.
        # Precedencia: VIIRS_C2_OVERRIDE_NIGHT > C2_SUMMIT_OVERRIDE > defaults.
        _c1_sum = C1_SUMMIT_OVERRIDE if C1_SUMMIT_OVERRIDE is not None else DNTI_CONTEXTUAL_C1_SUMMIT
        if VIIRS_C2_OVERRIDE_NIGHT is not None:
            _c2_summit_v13 = VIIRS_C2_OVERRIDE_NIGHT
            _c2_scene_v13 = VIIRS_C2_OVERRIDE_NIGHT
        elif C2_SUMMIT_OVERRIDE is not None:
            _c2_summit_v13 = C2_SUMMIT_OVERRIDE
            _c2_scene_v13 = C2_DNTI_SCENE_NIGHT
        else:
            _c2_summit_v13 = C2_DNTI_SUMMIT_NIGHT
            _c2_scene_v13 = C2_DNTI_SCENE_NIGHT
        # S72 F1.2 — pasar Test 1 K1 mask como unsuitable bg si flag retire ON
        # (Coppola 2016a SP 426.5 §298-300).
        _test1_mask_for_fp = (
            nti_path_hot if ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK else None
        )
        # S72 F2.3 — floors §267-273 controlables vía flag.
        _unsuit_dnti = -0.1 if ENABLE_UNSUITABLE_FILTERS_267_273 else -np.inf
        _unsuit_deti = -0.1 if ENABLE_UNSUITABLE_FILTERS_267_273 else -np.inf
        fp_hot, fp_diag = first_pass_tests_2_and_3(
            nti=nti, nti_app=nti_app_fp, bt=bt_mir,
            roi_mask=roi_mask, dist_km=vent_dist_per_pixel,
            t_bg=t_bg, bt_sanity_k=NTI_BT_SANITY_K,
            c1_dnti_summit=_c1_sum,
            c1_deti_summit=_c1_sum,
            c2_dnti_summit=_c2_summit_v13,
            c2_deti_summit=_c2_summit_v13,
            inner_km=inner_radius_km,
            c1_dnti_scene=(DNTI_CONTEXTUAL_C1_SCENE
                           if ENABLE_DUAL_ROI_FIRST_PASS else None),
            c1_deti_scene=(DNTI_CONTEXTUAL_C1_SCENE
                           if ENABLE_DUAL_ROI_FIRST_PASS else None),
            c2_dnti_scene=(_c2_scene_v13
                           if ENABLE_DUAL_ROI_FIRST_PASS else None),
            c2_deti_scene=(_c2_scene_v13
                           if ENABLE_DUAL_ROI_FIRST_PASS else None),
            test1_mask=_test1_mask_for_fp,
            unsuitable_dnti_floor=_unsuit_dnti,
            unsuitable_deti_floor=_unsuit_deti,
        )
        hot_mask_2d = fp_hot
        n_first_pass = fp_diag["n_first_pass_pixels"]

    # S46 Task 5 Drift #4 — second_pass_adjacent recapture (paper SP426.5:347-356).
    # Tras el first-pass, recompute dNTI/dETI excluyendo active pixels del 8-vecino
    # mean → recaptura pixels marginales adyacentes contaminados por vecinos.
    n_second_pass_recapture = 0
    if (ENABLE_SECOND_PASS_ADJACENT
            and ENABLE_FIRST_PASS_TESTS_2_AND_3
            and fp_diag is not None
            and inner_radius_km is not None
            and not np.isnan(t_bg)):
        eti_for_second_pass = fp_diag.get("eti")
        if eti_for_second_pass is not None:
            is_summit_mask = vent_dist_per_pixel <= inner_radius_km
            # S46 Task 6 + Ronda 2 — overrides C1/C2 en second-pass.
            if VIIRS_C2_OVERRIDE_NIGHT is not None:
                _c2_summit_sp = VIIRS_C2_OVERRIDE_NIGHT
                _c2_scene_sp = VIIRS_C2_OVERRIDE_NIGHT
            elif C2_SUMMIT_OVERRIDE is not None:
                _c2_summit_sp = C2_SUMMIT_OVERRIDE
                _c2_scene_sp = C2_DNTI_SCENE_NIGHT
            else:
                _c2_summit_sp = C2_DNTI_SUMMIT_NIGHT
                _c2_scene_sp = C2_DNTI_SCENE_NIGHT
            final_active_mask = second_pass_adjacent(
                nti=nti, eti=eti_for_second_pass,
                active_mask=hot_mask_2d,
                c1_dnti=_c1_sum,
                c1_deti=_c1_sum,
                c2_dnti=_c2_summit_sp,
                c2_deti=_c2_summit_sp,
                is_summit=(is_summit_mask
                           if ENABLE_DUAL_ROI_SECOND_PASS else None),
                c1_dnti_scene=(DNTI_CONTEXTUAL_C1_SCENE
                               if ENABLE_DUAL_ROI_SECOND_PASS else None),
                c1_deti_scene=(DNTI_CONTEXTUAL_C1_SCENE
                               if ENABLE_DUAL_ROI_SECOND_PASS else None),
                c2_dnti_scene=(_c2_scene_sp
                               if ENABLE_DUAL_ROI_SECOND_PASS else None),
                c2_deti_scene=(_c2_scene_sp
                               if ENABLE_DUAL_ROI_SECOND_PASS else None),
            )
            # S85 F-S81-B' — gate intra-radio sobre pixels NUEVOS del second
            # pass. Default OFF; ON via profile A/B. Ver
            # docs/F_S81_B_PRIME_SECOND_PASS_GATE.md.
            if ENABLE_SECOND_PASS_INTRA_RADIO_GATE:
                final_active_mask = apply_second_pass_intra_radio_gate(
                    first_pass_mask=hot_mask_2d,
                    final_active_mask=final_active_mask,
                    vent_dist_per_pixel=vent_dist_per_pixel,
                    inner_radius_km=inner_radius_km,
                    enabled=True,
                )
            n_second_pass_recapture = int(
                np.sum(final_active_mask & ~hot_mask_2d))
            hot_mask_2d = final_active_mask

    # S33 Driver B Phase 2 — filtro dual-ROI 5σ summit / 10σ scene a la mask
    # final combinada (Coppola 2016a Tabla 1). Ver explicación en process_viirs.py.
    if (ENABLE_FINAL_PIXEL_FILTER and inner_radius_km is not None
            and not np.isnan(t_bg) and not np.isnan(std_bg)):
        final_thr_mask = dual_roi_bt_threshold(
            bt=bt,
            roi_mask=np.ones_like(bt, dtype=bool),
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
    # path también dispararon. Si los paths "duros" no vieron nada → descartar
    # la contribución contextual (probable cirrus FP).
    if PATH_D_REQUIRES_COVALIDATION:
        _ctx_only = (not np.any(bt_path_hot)) and (not np.any(nti_path_hot))
        if _ctx_only:
            hot_mask_2d = np.zeros_like(hot_mask_2d)

    # S16 P3.6: filtrar exclude_zones (cuerpos de agua/salares).
    # S27 T3: guard ENABLE_EXCLUDE_ZONES — en _mirova_literal queda en False
    # (parche no documentado en papers MIROVA).
    exclude_zones, active_water_bodies = guard_exclude_zones(
        exclude_zones, active_water_bodies, enabled=ENABLE_EXCLUDE_ZONES)
    n_excluded_water = 0
    if exclude_zones:
        hot_mask_2d, n_excluded_water = filter_hot_mask(
            hot_mask_2d, lat, lon, exclude_zones, active_water_bodies)
    n_bt_path = int(np.sum(bt_path_hot & ~np.isnan(bt_path_hot)))
    n_nti_path = int(np.sum(nti_path_hot))

    # S71 D9 Opción C — predicado para cap magnitud path D contextual-only.
    # Activo cuando firing solo contextual (BT/NTI duros = 0) AND t_bg bajo
    # umbral cirrus. Se aplica en cada sitio donde primary_cluster se asigna
    # (eruption inicial + Test 1 recompute).
    _path_d_cap_active = (
        PATH_D_ONLY_CAP_MW is not None
        and PATH_D_ONLY_CAP_TBG_MAX_K is not None
        and not np.isnan(t_bg)
        and n_bt_path == 0
        and n_nti_path == 0
        and t_bg < PATH_D_ONLY_CAP_TBG_MAX_K
    )

    hot_rows, hot_cols = np.where(hot_mask_2d)
    n_anomalous = len(hot_rows)

    # S27 cluster aggregation se mueve abajo (post per_pixel_vrp_mw)
    # para incluir vrp_mw del cluster contiguo principal (D1 cierre completo).
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
        hotpix_bt = bt[hot_rows, hot_cols]
        L_hot = bt_to_spectral_radiance(hotpix_bt, M13_LAMBDA)
        L_bg_rad = bt_to_spectral_radiance(np.float64(t_bg), M13_LAMBDA)
        # Per-pixel area accounts for scan-angle elongation
        hotpix_area = pixel_areas[hot_rows, hot_cols]
        # S26: clip ΔL ≥ 0 (paridad MODIS/VIIRS 375m). Wooster physics.
        delta_L = np.maximum(L_hot - L_bg_rad, 0.0)
        per_pixel_vrp_mw = hotpix_area * WOOSTER_COEFF * delta_L / 1e6
        vrp_mw = float(np.nansum(per_pixel_vrp_mw))
        # F50/S77 fix Opción A: cap D9 también a vrp_mw scene-wide M-band.
        vrp_mw = apply_d9_scene_cap(vrp_mw, _path_d_cap_active, PATH_D_ONLY_CAP_MW)

        # Build list of TOP-100 anomalous pixels sorted by VRP (descending).
        # S26: cap a 100 (paridad MODIS/VIIRS 375m) para evitar bloat JSON
        # >100MB GitHub limit. n_anomalous_pixels conserva el count total.
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

        # S27 — cluster aggregation con vrp_mw del cluster principal (Coppola
        # 2016a). MIROVA reporta VRP del cluster contiguo, no suma indistinta.
        # Cierre D1 a nivel pipeline.
        vrp_per_pixel_2d = np.zeros_like(hot_mask_2d, dtype=float)
        vrp_per_pixel_2d[hot_rows, hot_cols] = per_pixel_vrp_mw
        _vlat = vent_lat if vent_lat is not None else volcano_lat
        _vlon = vent_lon if vent_lon is not None else volcano_lon
        # S38 D8 fix: cluster selection vent-anchored.
        _cluster_strategy = ("vent_anchored"
                              if (ENABLE_VENT_ANCHORED_CLUSTERING
                                  and inner_radius_km is not None)
                              else "vrp_max")
        _cluster_inner = (inner_radius_km
                           if _cluster_strategy == "vent_anchored" else None)
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
            # test1 pisa primary_cluster más abajo). Espejo de process_viirs.py.
            if ENABLE_HONEST_ANCHOR_VIIRS750 and primary_cluster is not None:
                ctx_cluster_anchor = dict(primary_cluster)
        hotspot_dist_km = anomaly_pixels[0]["dist_km"]

    valid_roi = roi_bt_full[~np.isnan(roi_bt_full)]
    t_max = float(np.max(valid_roi)) if len(valid_roi) else float("nan")

    # --- Vent-scale detection (weak fumarolic signals) ---
    vrp_vent_mw = 0.0
    n_vent_pixels = 0
    vent_hotspot_lat = None
    vent_hotspot_lon = None
    vent_hotspot_dist_km = None
    if (ENABLE_VENT_PATH
            and vent_lat is not None and vent_lon is not None
            and not np.isnan(t_bg)):
        vent_dist = haversine_km(vent_lat, vent_lon, lat, lon)
        vent_roi_mask = vent_dist <= vent_radius_km
        if np.any(vent_roi_mask):
            vent_bt = np.where(vent_roi_mask & ~np.isnan(bt), bt, np.nan)
            if np.any(~np.isnan(vent_bt)):
                flat_idx = np.nanargmax(vent_bt)
                r_vent, c_vent = np.unravel_index(flat_idx, vent_bt.shape)
                t_max_vent = float(vent_bt[r_vent, c_vent])
                sigma_contrib = min(N_SIGMA_VENT * std_bg, MAX_VENT_SIGMA_CONTRIB_K)
                vent_thresh = max(VENT_THRESHOLD_K, sigma_contrib)
                if t_max_vent > (t_bg + vent_thresh):
                    # S12 E4: count pixels above threshold
                    vent_hot_mask = vent_bt > (t_bg + vent_thresh)
                    n_hot_in_vent = int(np.sum(vent_hot_mask))
                    if n_hot_in_vent >= MIN_VENT_PIXELS:
                        L_vent = bt_to_spectral_radiance(np.float64(t_max_vent), M13_LAMBDA)
                        L_bg_vent = bt_to_spectral_radiance(np.float64(t_bg), M13_LAMBDA)
                        vent_area = float(pixel_areas[r_vent, c_vent])
                        vrp_vent_mw = float(vent_area * WOOSTER_COEFF * (L_vent - L_bg_vent)) / 1e6
                        n_vent_pixels = n_hot_in_vent
                        vent_hotspot_lat = float(lat[r_vent, c_vent])
                        vent_hotspot_lon = float(lon[r_vent, c_vent])
                        vent_hotspot_dist_km = float(haversine_km(vent_lat, vent_lon, vent_hotspot_lat, vent_hotspot_lon))

    name   = l1b_path.name
    sensor = _sensor_label_from_filename(name)

    # --- Schema unification (S14 D6) ---
    # S30+ (2026-05-02): portar Regla D Test 1-priority + VRP recompute +
    # primary_cluster coherence desde process_viirs.py / process_modis.py.
    # Sin esto, en VIIRS 750m el Test 1 disparaba (S28) pero nunca llegaba a
    # final_hotspot_source.
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

    # S44 fix: si Test 1 es única fuente (ver process_viirs.py).
    only_test1_source = (
        test1_triggered and test1_centroid_lat is not None
        and (n_bt_path or 0) == 0
        and (n_nti_path or 0) == 0
        and (n_dnti_ctx_path or 0) == 0
        and (n_eti_path or 0) == 0
    )

    if hotspot_lat is not None and hotspot_lon is not None:
        if test1_summit_hit and eruption_far:
            final_hotspot_lat = test1_centroid_lat
            final_hotspot_lon = test1_centroid_lon
            final_hotspot_dist_km = test1_hotspot_dist_km
            final_hotspot_source = "test1"
        elif only_test1_source:
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

    # S32 P2 Driver B — Test 1 pixel-level filter (Coppola 2016a Tabla 1).
    # Ver explicación en process_viirs.py. Default OFF.
    test1_hot_filtered = test1_hot
    if (ENABLE_TEST1_PIXEL_FILTER and final_hotspot_source == "test1"
            and inner_radius_km is not None
            and not np.isnan(t_bg) and not np.isnan(std_bg)):
        pixel_thr_mask = dual_roi_bt_threshold(
            bt=bt,
            roi_mask=np.ones_like(bt, dtype=bool),
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
    # S39 D4 per-volcano: combinar profile flag con lbg_global_compatible
    # per-volcán para evitar regresión en glaciares (Tupungatito, Planchón).
    if ENABLE_TEST1_LBG_GLOBAL and lbg_global_compatible and not np.isnan(t_bg):
        effective_L_bg = float(bt_to_spectral_radiance(np.float64(t_bg), M13_LAMBDA))
    else:
        effective_L_bg = test1_L_bg_local

    # S30+: VRP recompute cuando final_hotspot_source='test1' (mismo fix S26 D
    # de VIIRS 375m). Replica MIROVA: bg local del cráter (1-3km), no global.
    if (final_hotspot_source == "test1" and test1_n_contrib > 0
            and effective_L_bg is not None
            and not np.isnan(effective_L_bg)):
        t1_rows, t1_cols = np.where(test1_hot_filtered)
        if len(t1_rows) > 0:
            t1_bt = bt[t1_rows, t1_cols]
            t1_L = bt_to_spectral_radiance(t1_bt, M13_LAMBDA)
            t1_delta_L = np.maximum(t1_L - effective_L_bg, 0.0)
            t1_area = pixel_areas[t1_rows, t1_cols]
            t1_vrp = t1_area * WOOSTER_COEFF * t1_delta_L / 1e6
            vrp_mw = float(np.sum(t1_vrp))

    # S31+ fix magnitud: cluster_hotspots (8-conn pixel-vecindad scipy.label)
    # — ver explicación en process_viirs.py.
    if (final_hotspot_source == "test1" and test1_n_contrib > 0
            and effective_L_bg is not None
            and not np.isnan(effective_L_bg)):
        t1_vrp_2d = np.zeros_like(bt, dtype=np.float64)
        t1_rows, t1_cols = np.where(test1_hot_filtered)
        if len(t1_rows) > 0:
            t1_bt = bt[t1_rows, t1_cols]
            t1_L = bt_to_spectral_radiance(t1_bt, M13_LAMBDA)
            t1_delta_L = np.maximum(t1_L - effective_L_bg, 0.0)
            t1_area = pixel_areas[t1_rows, t1_cols]
            t1_vrp_arr = t1_area * WOOSTER_COEFF * t1_delta_L / 1e6
            t1_vrp_2d[t1_rows, t1_cols] = t1_vrp_arr
            # S95 (A45) — gap A07: el path Test1 calculaba la magnitud pero dejaba
            # anomaly_pixels=[] vacío → bloqueaba F5' display y rompía el mapa de
            # píxeles del dashboard para records VIIRS750 pure-Test1. Espejo del fix
            # S94 (PR #294) en process_viirs.py:1486. Poblar desde t1_vrp_2d (los
            # mismos píxeles que ya alimentan pc.vrp_mw). NO cambia detección ni
            # magnitud — solo serializa píxeles ya calculados.
            anomaly_pixels = build_anomaly_pixels(t1_vrp_2d, lat, lon, dist, bt)
            # S38: vent-anchored strategy también al cluster Test 1.
            _t1_strategy = ("vent_anchored"
                             if (ENABLE_VENT_ANCHORED_CLUSTERING
                                 and inner_radius_km is not None)
                             else "vrp_max")
            _t1_inner = (inner_radius_km
                          if _t1_strategy == "vent_anchored" else None)
            t1_clusters = cluster_hotspots(
                test1_hot_filtered, lat, lon, vent_lat, vent_lon,
                connectivity=8, vrp_per_pixel=t1_vrp_2d,
                strategy=_t1_strategy, inner_radius_km=_t1_inner,
            )
            if t1_clusters:
                top = t1_clusters[0]
                _vrp_t = float(top["vrp_mw"])
                # S112 §A69/D11 — magnitud núcleo focal/contextual (espejo de
                # process_modis.py:1213-1219). VIIRS750 era el único path Test1 sin la
                # cura: integra el gradiente topográfico MIR sobre píxeles grandes (562.500
                # m²) → infla 10-25× sobre MIROVA en nevados (excepto Lascar, foco real).
                # cluster_focal_vrp_mw suma SOLO píxeles dnti_ctx ∪ {pico} (keep_peak protege
                # el cráter real de Lascar / lava lake Villarrica). dnti_ctx_hot ya en scope.
                # Flag SEPARADO del global (ON en MODIS) para A/B independiente (A45).
                _focal_degraded_t = None
                if ENABLE_FOCAL_CLUSTER_MAGNITUDE_VIIRS750:
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

    # S106 — ancla espacial honesta VIIRS750 (design 2026-06-11 §3.1, espejo de
    # process_viirs.py). SOLO posición: los bloques de magnitud de arriba ya
    # corrieron con la semántica legacy. Flag SEPARADO del de VIIRS375
    # (enable_honest_anchor_viirs750) — activar tras validar destape propio.
    _ha_nti_peak = None
    if ENABLE_HONEST_ANCHOR_VIIRS750:
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
        "n_bt_path": n_bt_path,
        "n_nti_path": n_nti_path,
        "n_nti_rel_path": n_nti_rel_path,
        "n_dnti_ctx_path": n_dnti_ctx_path,
        "n_nti_anomalous": n_nti_anomalous,
        # S28: Test 1 integrated-ROI extendido a VIIRS 750m M13.
        "triggered_test1": test1_triggered,
        "n_test1_pixels": test1_n_contrib,
        "test1_k_observed": round(test1_k_obs, 2) if test1_k_obs else 0.0,
        "n_vent_pixels": n_vent_pixels,
        "vent_hotspot_lat": vent_hotspot_lat,
        "vent_hotspot_lon": vent_hotspot_lon,
        "vent_hotspot_dist_km": round(vent_hotspot_dist_km, 3) if vent_hotspot_dist_km is not None else None,
        "nti_bg": round(nti_bg, 6) if not np.isnan(nti_bg) else None,
        "nti_max": round(nti_max, 6) if not np.isnan(nti_max) else None,
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
        "t_max_k": round(t_max, 2) if not np.isnan(t_max) else None,
        # S22.1 paridad schema MODIS (H_S21_11). Algunos diag_* duplican campos
        # existentes (nti_bg, nti_max, n_*_path) por compat frontend; otros son
        # nuevos (sigma_bg, eff_threshold, nti_std, t_max_dist_km, roi_p95).
        "diag_sigma_bg_k": round(std_bg, 3) if not np.isnan(std_bg) else None,
        "diag_eff_threshold_k": round(effective_threshold, 2) if not np.isnan(effective_threshold) else None,
        "diag_t_max_dist_km": round(t_max_dist_km_diag, 2) if not np.isnan(t_max_dist_km_diag) else None,
        "diag_roi_p95_k": round(roi_p95, 2) if not np.isnan(roi_p95) else None,
        "diag_nti_bg": round(nti_bg, 4) if not np.isnan(nti_bg) else None,
        "diag_nti_std": round(nti_std, 4) if not np.isnan(nti_std) else None,
        "diag_nti_max": round(nti_max, 4) if not np.isnan(nti_max) else None,
        "diag_n_eti_path": n_eti_path,  # S37 H_D8_5
        "diag_n_bt_path": n_bt_path,
        "diag_n_nti_path": n_nti_path,
        "diag_n_dnti_ctx_path": n_dnti_ctx_path,
        # S46 drift23 — first_pass_tests_2_and_3 diag fields (Task 4 wiring).
        # Persistir n_first_pass_pixels + estadísticos μ/σ del background usados
        # en la regla μ+C2σ. Ausentes (0/None) si flag OFF o sin background válido.
        "diag_n_first_pass_pixels": (
            fp_diag["n_first_pass_pixels"] if fp_diag is not None else 0),
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
        "sensor": sensor,
        "granule": name,
        "product_version": "nrt" if "_NRT" in name else "standard",
        "datetime_utc": _parse_datetime(name),
    }


def _parse_datetime(filename: str) -> str:
    try:
        parts = filename.split(".")
        year  = int(parts[1][1:5])
        doy   = int(parts[1][5:8])
        hour  = int(parts[2][:2])
        minute = int(parts[2][2:4])
        import datetime
        dt = datetime.datetime(year, 1, 1) + datetime.timedelta(
            days=doy - 1, hours=hour, minutes=minute)
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return "unknown"
