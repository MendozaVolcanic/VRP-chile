"""
process_viirs.py — Calculate VRP from VIIRS VNP02IMG / VJ102IMG L1B granules.

Algorithm: adapted from TIRVolcH (Aveni et al. 2024, RSE) and
           MODIS-to-VIIRS transition (Campus et al. 2022, Sensors).

Bands used:
  - I04 (3.74 um, 375m): primary MIR channel for volcanic hotspots
  - I05 (11.45 um, 375m): TIR channel for low-temperature anomalies (TIRVolcH)

Calibration: VIIRS files include a pre-computed brightness temperature LUT
  (65536 values indexed by raw DN). This is used directly instead of
  manual Planck inversion, per the VIIRS L1B User Guide (Aug 2021).

References:
  - VIIRS L1B User Guide Aug 2021 (VIIRS_L1B_UserGuide_Aug2021.pdf)
  - Aveni et al. 2024, Remote Sensing of Environment (TIRVolcH)
  - Campus et al. 2022, Sensors 22(5):1713
"""

import numpy as np
from pathlib import Path

try:
    import h5py
    H5_AVAILABLE = True
except ImportError:
    H5_AVAILABLE = False
    print("WARNING: h5py not found. Install: pip install h5py")

from .scan_geometry import viirs_pixel_areas, roi_mask_bbox
from .exclusion_zones import filter_hot_mask, guard_exclude_zones
from .clustering import cluster_hotspots, cluster_pixels_geographic


# S23 T17: constantes físicas centralizadas en pipeline/constants.py
from pipeline.constants import SIGMA  # Stefan-Boltzmann (TIR only)

# VIIRS I-band nadir pixel area (375 m resolution).
# IMPORTANT: actual pixel area is corrected per-pixel using sensor_zenith
# from the geolocation file. See pipeline/scan_geometry.py.
NADIR_PIXEL_AREA_M2 = 375.0 ** 2   # 140,625 m^2

# Planck constants for spectral radiance (W/m²/sr/µm)
from pipeline.constants import C1, C2  # 2hc², hc/k Planck radiation

# Wooster MIR radiance coefficient.
# For VIIRS I4 (3.74 µm, 375 m) use 18.0 per Laiolo et al. 2024
# (s00445-024-01721-z, Vulcano VIIRS 375m), not 18.9 which is calibrated for
# MODIS B21 at 3.959 µm / 1 km. Difference comes from band center and pixel
# footprint in the Planck→Stefan-Boltzmann approximation over 600–1500 K.
WOOSTER_COEFF = 18.0   # W/m² per (W/m²/sr/µm) — VIIRS I4 375m

# Band wavelengths (µm)
I04_LAMBDA = 3.740

# Flag DN values (from file attributes)
FLAG_DNS = {65532, 65533, 65534, 65535}  # Missing_EV, Bowtie_Deleted, Cal_Fail, Fill

# --- All detection thresholds and path toggles come from the active profile ---
# Profile is selected via $VRP_PROFILE (set by run_pipeline.py --profile).
# Values documented in pipeline/profiles/*.yaml.
from pipeline.profile import (
    ANOMALY_THRESHOLD_K,
    TIR_THRESHOLD_K,
    N_SIGMA_MIR,
    N_SIGMA_TIR,
    VENT_THRESHOLD_K,
    N_SIGMA_VENT,
    MAX_VENT_SIGMA_CONTRIB_K,
    MIN_VENT_PIXELS,
    BG_INNER_KM,
    BG_OUTER_KM,
    NTI_K1_NIGHT,
    NTI_BT_SANITY_K,
    ENABLE_VENT_PATH,
    ENABLE_ERUPTION_PATH,
    ENABLE_NTI_RELATIVE_PATH,
    NTI_REL_N_SIGMA,
    NTI_REL_MIN_FLOOR,
    MAX_SIGMA_COMPONENT_K,
    DNTI_CONTEXTUAL_C1,
    DNTI_CONTEXTUAL_C1_SUMMIT,
    DNTI_CONTEXTUAL_C1_SCENE,
    ENABLE_DNTI_CONTEXTUAL_PATH,
    ENABLE_DNTI_DUAL_ROI,
    ENABLE_DUAL_ROI_BT,
    N_SIGMA_MIR_SUMMIT,
    N_SIGMA_MIR_SCENE,
    ENABLE_TEST1_PIXEL_FILTER,
    ENABLE_FINAL_PIXEL_FILTER,
    ENABLE_TEST1_LBG_GLOBAL,
    ENABLE_TEST1_PATH,
    TEST1_K_SIGMA,
    TEST1_MIR_RELATIVE,
    TEST1_ROI_KM,
    TEST1_INNER_RING_KM,
    ENABLE_EXCLUDE_ZONES,
    ENABLE_ETI_QUADRATIC_SCENE,
    ENABLE_SECOND_PASS_ADJACENT,
    C2_DNTI_SUMMIT_NIGHT,
    C2_DNTI_SCENE_NIGHT,
    C2_DETI_SUMMIT_NIGHT,
    C2_DETI_SCENE_NIGHT,
    ENABLE_VENT_ANCHORED_CLUSTERING,
    ENABLE_BT_PATH_HOT,
    ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK,
    ENABLE_TEST1_K1_BG_EXCLUDE,
    ENABLE_NADIR_FIXED_PIXEL_AREA_VIIRS,
    ENABLE_FIRST_PASS_TESTS_2_AND_3,
    ENABLE_DUAL_ROI_FIRST_PASS,
)
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


def _sensor_label_from_filename(filename: str) -> str:
    """Map VIIRS I-band L1B filename → sensor label used in records/CSV.

    VNP02IMG / VNP03IMG  → VIIRS_SNPP     (Suomi-NPP, 2011)
    VJ102IMG / VJ103IMG  → VIIRS_NOAA20   (JPSS-1, 2017)
    VJ202IMG / VJ203IMG  → VIIRS_NOAA21   (JPSS-2, 2022, S18)

    El sufijo _NRT (LANCE) no altera el sensor. Antes de S18 todo VJ*IMG se
    colapsaba a VIIRS_NOAA20, confundiendo NOAA-21 con NOAA-20 en el CSV.
    """
    if filename.startswith("VNP"):
        return "VIIRS_SNPP"
    if filename.startswith("VJ2"):
        return "VIIRS_NOAA21"
    return "VIIRS_NOAA20"


def bt_to_spectral_radiance(bt: np.ndarray, wavelength_um: float) -> np.ndarray:
    """Convert brightness temperature (K) to spectral radiance (W/m²/sr/µm) via Planck."""
    with np.errstate(invalid="ignore", divide="ignore", over="ignore"):
        return C1 / (wavelength_um ** 5 * (np.exp(C2 / (wavelength_um * bt)) - 1))


def read_viirs_l1b(l1b_path: Path) -> dict:
    """
    Read VIIRS VNP02IMG HDF5/NetCDF4 file.

    Returns:
        {
          "I04": ndarray float32 — brightness temperature (K) for band I04
          "I05": ndarray float32 — brightness temperature (K) for band I05
        }

    Calibration uses the built-in BT LUT (I04_brightness_temperature_lut).
    Flag values (65532–65535) are replaced with NaN.
    """
    if not H5_AVAILABLE:
        raise ImportError("h5py required. Install: pip install h5py")

    result = {}
    with h5py.File(l1b_path, "r") as f:
        obs = f["observation_data"]
        for band in ("I04", "I05"):
            if band not in obs:
                continue
            dn = obs[band][:]                                   # uint16, shape (lines, pixels)
            lut_key = f"{band}_brightness_temperature_lut"
            if lut_key in obs:
                # Direct LUT lookup: bt[i,j] = lut[dn[i,j]]
                lut = obs[lut_key][:]                           # float32, 65536 values
                bt = lut[dn].astype(np.float32)
                # Mask flag values
                flag_mask = np.isin(dn, list(FLAG_DNS))
                bt[flag_mask] = np.nan
                # LUT fill value is -999.9
                bt[bt < 0] = np.nan
            else:
                # Fallback: manual radiance conversion
                ds = obs[band]
                scale = float(ds.attrs.get("scale_factor", 1.0))
                offset = float(ds.attrs.get("add_offset", 0.0))
                rad = dn.astype(np.float32) * scale + offset
                flag_mask = np.isin(dn, list(FLAG_DNS))
                rad[flag_mask] = np.nan
                bt = _radiance_to_bt_viirs(rad, band)
            result[band] = bt
    return result


def _radiance_to_bt_viirs(L: np.ndarray, band: str) -> np.ndarray:
    """Planck inversion fallback (used only if LUT is absent)."""
    C1 = 1.191042e8
    C2 = 14388.0
    wavelengths = {"I04": 3.740, "I05": 11.450}
    lam = wavelengths.get(band, 3.740)
    with np.errstate(invalid="ignore", divide="ignore"):
        return C2 / (lam * np.log(C1 / (L * lam ** 5) + 1))


def read_viirs_geo(geo_path: Path) -> dict:
    """
    Read VIIRS VNP03IMG / VJ103IMG geolocation HDF5/NetCDF4 file.

    Returns dict with:
        'lat', 'lon': float32 arrays (degrees)
        'sensor_zenith': float32 array of per-pixel satellite zenith angles
            (degrees from local vertical at the surface). Used for the
            scan-angle pixel area correction in scan_geometry.viirs_pixel_areas.
    """
    if not H5_AVAILABLE:
        raise ImportError("h5py required.")

    with h5py.File(geo_path, "r") as f:
        geo = f["geolocation_data"]
        lat = geo["latitude"][:].astype(np.float32)
        lon = geo["longitude"][:].astype(np.float32)
        # Fill value is -999.9
        lat[lat < -90] = np.nan
        lon[lon < -180] = np.nan

        # Per-pixel sensor zenith (degrees). Required for pixel-area correction.
        if "sensor_zenith" in geo:
            sz = geo["sensor_zenith"][:].astype(np.float32)
        elif "satellite_zenith" in geo:
            sz = geo["satellite_zenith"][:].astype(np.float32)
        else:
            # Fallback: assume nadir (no correction). Should not happen for
            # standard VNP03/VJ103 products.
            sz = np.zeros_like(lat)
        sz[np.isnan(lat)] = np.nan
    return {"lat": lat, "lon": lon, "sensor_zenith": sz}


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
                  lbg_global_compatible: bool = False) -> dict | None:
    """
    Calculate VRP from a single VIIRS L1B granule.

    Args:
        l1b_path: Path to VNP02IMG or VJ102IMG file (.nc)
        geo_path: Path to VNP03IMG or VJ103IMG geolocation file (.nc)
        volcano_lat: Volcano reference latitude (degrees)
        volcano_lon: Volcano reference longitude (degrees)
        radius_km: Search radius for eruption-scale detection
        vent_lat: Latitude of active vent/fumarolic source (optional)
        vent_lon: Longitude of active vent/fumarolic source (optional)
        vent_radius_km: Tight search radius for weak fumarolic detection
        inner_radius_km: MIROVA-style visual classification radius. Detections
            with final_hotspot_dist_km <= inner_radius_km are tagged as "summit"
            (real anomaly, red); beyond → "far" (possible distant, gray). If
            None, distance_class is None.

    Returns dict with VRP values, or None if granule does not cover volcano.
    """
    bands = read_viirs_l1b(l1b_path)
    geo = read_viirs_geo(geo_path)

    lat = geo["lat"]
    lon = geo["lon"]
    # Per-pixel ground area (m^2) corrected for off-nadir scan geometry.
    # See pipeline/scan_geometry.py for the sec^3(theta_z) formula.
    pixel_areas = viirs_pixel_areas(
        geo["sensor_zenith"],
        NADIR_PIXEL_AREA_M2,
        nadir_fixed=ENABLE_NADIR_FIXED_PIXEL_AREA_VIIRS,
    )

    dist = haversine_km(volcano_lat, volcano_lon, lat, lon)

    # P3.1 S15: per-pixel distance from effective vent (mirova_center if set,
    # else vent_lat/lon, else volcano center). Used for dual-ROI summit/scene.
    if vent_lat is not None and vent_lon is not None:
        vent_dist_per_pixel = haversine_km(vent_lat, vent_lon, lat, lon)
    else:
        vent_dist_per_pixel = dist

    # S15 Tema E: bbox cuadrado (paridad MIROVA) en vez de circulo inscrito.
    # Recupera las esquinas del bbox 50x50 km (hasta ~35 km diagonal) donde
    # MIROVA publica detecciones que circulo radio 25 km perdia (Llaima
    # Conguillio a 28 km, Copahue lejanas, etc.).
    roi_mask = roi_mask_bbox(lat, lon, volcano_lat, volcano_lon, radius_km)
    bg_mask = (dist >= BG_INNER_KM) & (dist <= BG_OUTER_KM)

    if not np.any(roi_mask):
        return None

    # --- Cloud mask: exclude cold pixels using TIR band (I05) ---
    # Cloud tops are typically <260K. Excluding them prevents:
    #  (a) artificially low T_bg from cloudy background pixels
    #  (b) false negatives from cloudy ROI pixels hiding real anomalies
    # This is a simple threshold approach — no extra download needed.
    CLOUD_BT_THRESHOLD = 260.0  # K — pixels colder than this are likely cloudy
    n_cloud_masked = 0
    if "I05" in bands:
        cloud_free = bands["I05"] >= CLOUD_BT_THRESHOLD
        cloud_free = cloud_free | np.isnan(bands["I05"])  # keep pixels without I05
        n_cloud_masked = int(np.sum(roi_mask & ~cloud_free & ~np.isnan(bands["I05"])))
        roi_mask = roi_mask & cloud_free
        bg_mask = bg_mask & cloud_free

    # --- NTI: Normalized Thermal Index (Coppola 2015) ---
    # NTI = (L_MIR - L_TIR) / (L_MIR + L_TIR) per-pixel
    # Anomaly when NTI_pixel > NTI_bg_median + NTI_threshold
    # This is MIROVA's primary detection method — filters solar contamination
    # and works contextually against local background.
    nti_max = float("nan")
    nti_bg = float("nan")
    nti_std = float("nan")
    n_nti_anomalous = 0
    # S46 drift #1b: inicializar nti=None aquí (antes del bloque I04+I05) para
    # que compute_bg_stats reciba un argumento válido aunque I05 no esté.
    # Cuando nti es None y enable_test1_k1_bg_exclude=False (default OFF),
    # compute_bg_stats opera como legacy. Cuando flag ON sin I05, levanta error
    # (configuración inválida — drift #1b requiere NTI para detectar K1 active).
    nti = None
    # S22.1 paridad MODIS schema (H_S21_11): diagnósticos siempre presentes
    # aunque no haya bandas válidas. Reseteados a valores reales en el path BT.
    roi_p95_diag = float("nan")
    t_max_dist_km_diag = float("nan")
    effective_threshold_diag = float("nan")

    if "I04" in bands and "I05" in bands:
        bt4 = bands["I04"]
        bt5 = bands["I05"]
        # Compute spectral radiance for NTI
        L_mir = bt_to_spectral_radiance(bt4, I04_LAMBDA)
        L_tir = bt_to_spectral_radiance(bt5, 11.450)
        valid_both = ~np.isnan(L_mir) & ~np.isnan(L_tir) & (L_mir + L_tir > 0)
        nti = np.full_like(L_mir, np.nan)
        nti[valid_both] = (L_mir[valid_both] - L_tir[valid_both]) / (L_mir[valid_both] + L_tir[valid_both])

        # Background NTI statistics
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

    # --- MIR channel I04 (3.74 um) — high-temperature features ---
    # F1 (S9): Dual-PATH detection (logical OR), mirroring process_modis.py.
    # A pixel is hot if EITHER:
    #   (A) BT path: bt > t_bg + max(ANOMALY_THRESHOLD_K, N_SIGMA*std_bg)
    #   (B) NTI path: nti > NTI_K1_NIGHT  AND  bt > t_bg + NTI_BT_SANITY_K
    # The previous code AND-ed BT and NTI, which killed any pixel where
    # std_bg was inflated by clouds/orography even when NTI was clearly
    # anomalous (RF4 Villarrica, RF6 Tupungatito; see L7.2 / ROOT_CAUSE_S9).
    vrp_mir_mw = 0.0
    t_bg_i04 = float("nan")
    t_max_i04 = float("nan")
    std_bg_i04 = float("nan")  # S12: needed for vent-path sigma gating
    n_anomalous = 0
    n_bt_path = 0
    n_nti_path = 0
    n_nti_rel_path = 0
    # S16 fix: inicializar n_dnti_ctx_path aqui en vez de dentro del bloque
    # condicional, para evitar UnboundLocalError cuando "I04" no esta en bands
    # o len(bg_vals) < 10 (granules con poco data utilizable).
    n_dnti_ctx_path = 0
    n_eti_path = 0  # S37 H_D8_5 — mismo motivo (paridad MODIS pattern).
    # S27: cluster aggregation defaults (mismo motivo: evitar UnboundLocalError
    # si rama "I04" no se ejecuta).
    n_hotspots_clustered = 0
    primary_cluster = None
    # S25 Path Test 1 — defaults antes del bloque I04 (mismo patrón S16)
    test1_triggered = False
    test1_n_contrib = 0
    test1_k_obs = 0.0
    test1_centroid_lat = None
    test1_centroid_lon = None
    test1_L_bg_local = None  # S26 default outside I04 block
    n_excluded_water = 0
    hotspot_lat = None
    hotspot_lon = None
    hotspot_dist_km = None
    anomaly_pixels = []   # All anomalous pixels with location + per-pixel VRP
    # S46 drift23 — first_pass_tests_2_and_3 diag (default outside I04 block).
    fp_diag = None

    if "I04" in bands:
        bt = bands["I04"]
        # S46 drift #1b: cuando ENABLE_TEST1_K1_BG_EXCLUDE, excluir pixels
        # Test 1 K1 active (NTI > -0.8 noche) del bg per Coppola 2016a:352-356.
        # Requiere nti (computed arriba si I05 disponible). Si nti is None y
        # flag OFF, compute_bg_stats opera como legacy.
        _t_bg_tmp, _std_bg_tmp, _n_bg_tmp = compute_bg_stats(
            bt=bt,
            bg_mask=bg_mask,
            nti=nti,
            nti_k1_threshold=NTI_K1_NIGHT,
            enable_test1_k1_bg_exclude=ENABLE_TEST1_K1_BG_EXCLUDE,
            min_bg_pixels=10,
        )
        if _t_bg_tmp is not None:
            t_bg_i04 = _t_bg_tmp
            std_bg = _std_bg_tmp
            std_bg_i04 = std_bg  # S12: save for vent-path sigma gating
            # S15 Tema F: sigma-cap en eruption-path (paridad con MODIS,
            # cura Tupungatito recall 0.04). Sin cap, sigma_bg inflado por
            # glaciar/orografia (Tupungatito 5682m, Villarrica cono glaciar)
            # empujaba el threshold a 9-12 K, rechazando pixels reales
            # MIROVA a DeltaT=8-9 K. Cap a 7 K (default MIROVA) coincide
            # con el gate MODIS (process_modis.py linea 253).
            sigma_component = min(N_SIGMA_MIR * std_bg, MAX_SIGMA_COMPONENT_K)
            threshold_mir = max(ANOMALY_THRESHOLD_K, sigma_component)
            # S22.1 paridad MODIS: threshold efectivo es BT absoluto (t_bg + delta),
            # no el delta solo. process_modis.py:289 hace lo mismo.
            effective_threshold_diag = t_bg_i04 + threshold_mir

            roi_bt_full = np.where(roi_mask & ~np.isnan(bt), bt, np.nan)
            # S22.1 paridad MODIS: percentile 95 ROI + distancia al pixel más
            # caliente. Útiles para diagnosticar T4 (cráter sub-detección).
            roi_bt_valid_flat = roi_bt_full[~np.isnan(roi_bt_full)]
            if roi_bt_valid_flat.size >= 10:
                roi_p95_diag = float(np.percentile(roi_bt_valid_flat, 95))
            if np.any(~np.isnan(roi_bt_full)):
                flat_idx_max = np.nanargmax(roi_bt_full)
                r_max, c_max = np.unravel_index(flat_idx_max, roi_bt_full.shape)
                t_max_dist_km_diag = float(dist[r_max, c_max])

            # Path A — BT path (existing classic threshold)
            # S26: si ENABLE_DUAL_ROI_BT, usar threshold dual summit/scene
            # (Coppola 2016a Tabla 1) en lugar del N_SIGMA_MIR uniforme.
            if (ENABLE_DUAL_ROI_BT and inner_radius_km is not None
                    and vent_lat is not None and vent_lon is not None):
                bt_path_hot = dual_roi_bt_threshold(
                    bt=bt, roi_mask=roi_mask, dist_km=vent_dist_per_pixel,
                    t_bg=t_bg_i04, std_bg=std_bg, inner_km=inner_radius_km,
                    n_sigma_summit=N_SIGMA_MIR_SUMMIT,
                    n_sigma_scene=N_SIGMA_MIR_SCENE,
                    anomaly_floor_k=ANOMALY_THRESHOLD_K,
                    max_sigma_cap_k=MAX_SIGMA_COMPONENT_K,
                )
            else:
                bt_path_hot = roi_mask & ~np.isnan(bt) & (bt > (t_bg_i04 + threshold_mir))
            # S40 cleanup paths viejos: desactivar bt_path_hot si flag OFF.
            if not ENABLE_BT_PATH_HOT:
                bt_path_hot = np.zeros_like(bt_path_hot, dtype=bool)

            # Path B — NTI path (Coppola 2015 Test 1, night).
            # Only valid if NTI was successfully computed (needs both I04+I05).
            if "I05" in bands and not np.isnan(nti_bg):
                nti_path_hot = (
                    roi_mask
                    & ~np.isnan(nti)
                    & ~np.isnan(bt)
                    & (nti > NTI_K1_NIGHT)
                    & (bt > (t_bg_i04 + NTI_BT_SANITY_K))
                )
            else:
                nti_path_hot = np.zeros_like(bt_path_hot)

            # Path C — NTI relative path (Session 11).
            # Uses the contextual NTI threshold (nti_bg + max(0.005, 3*sigma))
            # instead of the absolute NTI_K1_NIGHT floor. This detects weak
            # fumarolic signals (0.05-0.3 MW) where the NTI shifts by ~0.01
            # above background — too small for the -0.8 absolute floor but
            # clearly anomalous against the local sigma (~0.002-0.004).
            # Gated by enable_nti_relative_path (experimental only).
            if (ENABLE_NTI_RELATIVE_PATH
                    and "I05" in bands
                    and not np.isnan(nti_bg)
                    and len(bg_nti) >= 10):
                nti_rel_threshold = nti_bg + max(NTI_REL_MIN_FLOOR, NTI_REL_N_SIGMA * nti_std)
                nti_rel_hot = (
                    roi_mask
                    & ~np.isnan(nti)
                    & ~np.isnan(bt)
                    & (nti > nti_rel_threshold)
                    & (bt > (t_bg_i04 + NTI_BT_SANITY_K))
                )
                n_nti_rel_path = int(np.sum(nti_rel_hot))
            else:
                nti_rel_hot = np.zeros_like(bt_path_hot)

            # Path D — dNTI contextual 8-vecinos (P3.2 + P3.1 S15, Coppola 2016a).
            # P3.2: anomaly requires the pixel to stand out from its immediate
            # neighbors, not from the ring average -- immune to uniformly warm
            # terrain (Lastarria hidrotermal, ratio 19.87 pre-P3.2).
            # P3.1: when enabled + inner_radius_km set, use dual-ROI thresholds:
            # summit (dist<=inner) C1=0.003 sensible; scene C1=0.010 strict.
            # Necesario para Lastarria: Path D solo capturaba 55% pixels en
            # 15-25 km (Lazufre, termico real pero MIROVA descarta).
            # n_dnti_ctx_path ya inicializado a 0 antes del bloque (S16 fix).
            if (ENABLE_DNTI_CONTEXTUAL_PATH
                    and "I05" in bands
                    and not np.isnan(nti_bg)):
                if ENABLE_DNTI_DUAL_ROI and inner_radius_km is not None:
                    dnti_ctx_hot = dual_roi_contextual_dnti_hot_mask(
                        nti=nti, bt=bt, roi_mask=roi_mask,
                        dist_km=vent_dist_per_pixel,
                        t_bg=t_bg_i04,
                        c1_summit=DNTI_CONTEXTUAL_C1_SUMMIT,
                        c1_scene=DNTI_CONTEXTUAL_C1_SCENE,
                        inner_km=inner_radius_km,
                        bt_sanity_k=NTI_BT_SANITY_K,
                    )
                else:
                    dnti_ctx_hot = contextual_dnti_hot_mask(
                        nti=nti, bt=bt, roi_mask=roi_mask,
                        t_bg=t_bg_i04,
                        c1=DNTI_CONTEXTUAL_C1,
                        bt_sanity_k=NTI_BT_SANITY_K,
                    )
                n_dnti_ctx_path = int(np.sum(dnti_ctx_hot))
            else:
                dnti_ctx_hot = np.zeros_like(bt_path_hot)

            # Path Test 1 — integrated-ROI MIR (Coppola 2015 §2.2 Eq.1).
            # Suma el exceso de radiancia MIR sobre la ROI vent y compara
            # contra σ_bg propagado (cae como √N). Detecta señales sub-pixel
            # espacialmente extendidas (lava lake Villarrica 0.05-0.21 MW)
            # que los paths per-pixel pierden porque ningún pixel rompe
            # threshold absoluto pero su suma integrada sí. POC S25 (6/6
            # refs Villarrica disparan vs 0/6 con paths actuales).
            test1_hot = np.zeros_like(bt_path_hot)
            test1_triggered = False
            test1_n_contrib = 0
            test1_k_obs = 0.0
            test1_centroid_lat = None
            test1_centroid_lon = None
            test1_L_bg_local = None  # S26 para recompute VRP test1-only
            if (ENABLE_TEST1_PATH
                    and vent_lat is not None and vent_lon is not None):
                test1_res = compute_test1_mir(
                    bt=bt, lat=lat, lon=lon,
                    vent_lat=vent_lat, vent_lon=vent_lon,
                    lambda_um=I04_LAMBDA,
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
                    # L_bg local del ring 1-3km, NO el anillo global 5-25km.
                    # En Villarrica el global está MÁS caliente (lago lateral)
                    # que el cráter (glaciar). Usar global → todos los ΔL clip a 0.
                    test1_L_bg_local = test1_res.get("L_bg")

            # S37 H_D8_5 — path ETI cuadrático scene-wide VIIRS I04/I05.
            # I04 (3.74 μm MIR) + I05 (11.45 μm TIR) entran al cómputo de
            # NTI / NTI_app. Tests 2 ∧ 3 sobre dNTI/dETI (8-vecinos).
            # Opcional second-pass que recapture marginales contaminados.
            eti_path_hot = np.zeros_like(bt_path_hot, dtype=bool)
            n_eti_path = 0
            if (ENABLE_ETI_QUADRATIC_SCENE
                    and inner_radius_km is not None
                    and vent_lat is not None and vent_lon is not None
                    and not np.isnan(nti_bg)):
                _, nti_app_viirs = compute_nti_and_nti_app(
                    rad_mir=L_mir,
                    bt_tir=bt5,
                    lambda_mir_um=I04_LAMBDA,
                    lambda_tir_um=11.450,
                )
                mask_valid_eti = (
                    roi_mask
                    & ~np.isnan(nti) & ~np.isnan(nti_app_viirs)
                    & ~np.isnan(bt)
                )
                eti_2d = compute_eti_scene_quadratic(
                    nti, nti_app_viirs, mask_valid_eti,
                )
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
                eti_path_hot = (eti_path_hot & roi_mask & ~np.isnan(bt)
                                & (bt > (t_bg_i04 + NTI_BT_SANITY_K)))
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
            if (ENABLE_FIRST_PASS_TESTS_2_AND_3
                    and inner_radius_km is not None
                    and not np.isnan(t_bg_i04)):
                _, nti_app_fp = compute_nti_and_nti_app(
                    rad_mir=L_mir,
                    bt_tir=bt5,
                    lambda_mir_um=I04_LAMBDA,
                    lambda_tir_um=11.450,
                )
                fp_hot, fp_diag = first_pass_tests_2_and_3(
                    nti=nti, nti_app=nti_app_fp, bt=bt,
                    roi_mask=roi_mask, dist_km=vent_dist_per_pixel,
                    t_bg=t_bg_i04, bt_sanity_k=NTI_BT_SANITY_K,
                    c1_dnti_summit=DNTI_CONTEXTUAL_C1_SUMMIT,
                    c1_deti_summit=DNTI_CONTEXTUAL_C1_SUMMIT,
                    c2_dnti_summit=C2_DNTI_SUMMIT_NIGHT,
                    c2_deti_summit=C2_DETI_SUMMIT_NIGHT,
                    inner_km=inner_radius_km,
                    c1_dnti_scene=(DNTI_CONTEXTUAL_C1_SCENE
                                   if ENABLE_DUAL_ROI_FIRST_PASS else None),
                    c1_deti_scene=(DNTI_CONTEXTUAL_C1_SCENE
                                   if ENABLE_DUAL_ROI_FIRST_PASS else None),
                    c2_dnti_scene=(C2_DNTI_SCENE_NIGHT
                                   if ENABLE_DUAL_ROI_FIRST_PASS else None),
                    c2_deti_scene=(C2_DETI_SCENE_NIGHT
                                   if ENABLE_DUAL_ROI_FIRST_PASS else None),
                )
                hot_mask_2d = fp_hot
                n_first_pass = fp_diag["n_first_pass_pixels"]

            # S33 Driver B Phase 2 — filtro dual-ROI 5σ summit / 10σ scene a
            # la mask final combinada (Coppola 2016a Tabla 1). Pixels que
            # entraron via dNTI/NTI/Test1 pero no superan BT > t_bg + 5σ summit
            # (o 10σ scene) son removidos del cluster reportado. Garantiza que
            # cualquier pixel sumado al VRP supere el gate de magnitud absoluta.
            if (ENABLE_FINAL_PIXEL_FILTER and inner_radius_km is not None
                    and not np.isnan(t_bg_i04) and not np.isnan(std_bg_i04)):
                final_thr_mask = dual_roi_bt_threshold(
                    bt=bt,
                    roi_mask=np.ones_like(bt, dtype=bool),
                    dist_km=vent_dist_per_pixel,
                    t_bg=t_bg_i04, std_bg=std_bg_i04,
                    inner_km=inner_radius_km,
                    n_sigma_summit=N_SIGMA_MIR_SUMMIT,
                    n_sigma_scene=N_SIGMA_MIR_SCENE,
                    anomaly_floor_k=ANOMALY_THRESHOLD_K,
                    max_sigma_cap_k=MAX_SIGMA_COMPONENT_K,
                )
                hot_mask_2d = hot_mask_2d & final_thr_mask

            # S16 P3.6: filtrar pixels en exclude_zones (cuerpos de agua/salares
            # irradiando calor nocturno que bbox 50x50 km incluye -> FPs masivos).
            # Whitelist active_water_bodies preserva (lagos crateres activos).
            # S27 T3: guard ENABLE_EXCLUDE_ZONES — en _mirova_literal queda en
            # False (parche no documentado en papers MIROVA).
            exclude_zones, active_water_bodies = guard_exclude_zones(
                exclude_zones, active_water_bodies, enabled=ENABLE_EXCLUDE_ZONES)
            n_excluded_water = 0
            if exclude_zones:
                hot_mask_2d, n_excluded_water = filter_hot_mask(
                    hot_mask_2d, lat, lon, exclude_zones, active_water_bodies)

            n_bt_path = int(np.sum(bt_path_hot))
            n_nti_path = int(np.sum(nti_path_hot))

            hot_rows, hot_cols = np.where(hot_mask_2d)
            n_anomalous = len(hot_rows)

            # S27 — cluster aggregation alineado con MIROVA n_hotspots
            # (Coppola 2016a connectivity ~1km). Cierre divergencia D1.
            # S27: cluster aggregation se mueve abajo (post per_pixel_vrp_mw)
            # para incluir vrp_mw del cluster contiguo principal.

            if n_anomalous > 0:
                hotpix_bt = bt[hot_rows, hot_cols]
                L_hot = bt_to_spectral_radiance(hotpix_bt, I04_LAMBDA)
                L_bg = bt_to_spectral_radiance(np.float64(t_bg_i04), I04_LAMBDA)
                # S26: clip a 0 — Wooster requiere ΔL ≥ 0 por física.
                # Bug detectado cuando Test 1 (path D nuevo) o NTI agregaba
                # pixels hot vs L_bg LOCAL (3km) pero más fríos que t_bg_i04
                # GLOBAL (anillo 5-25km). VRP_MIR salía negativo (-26 MW).
                # Fix: pixel "hot" pero L_hot < L_bg_global no contribuye.
                delta_L = np.maximum(L_hot - L_bg, 0.0)
                # Per-pixel area accounts for scan-angle elongation.
                hotpix_area = pixel_areas[hot_rows, hot_cols]
                per_pixel_vrp_mw = hotpix_area * WOOSTER_COEFF * delta_L / 1e6
                vrp_mir_mw = float(np.sum(per_pixel_vrp_mw))

                # Build list of TOP-100 anomalous pixels sorted by VRP (descending).
                # S26: cap a 100 para evitar bloat JSON (>100MB GitHub limit).
                # Records eruptivos típicamente tienen 1000-4000 pixels; los top
                # 100 capturan >95% de la señal VRP y bastan para visualización.
                # n_anomalous_pixels conserva el count total.
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

                # S27 — cluster aggregation con vrp_mw del cluster principal
                # (Coppola 2016a). Cierre D1. Construimos mapa 2D de VRPs y
                # agrupamos componentes conexos 8-vec.
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
                                   if _cluster_strategy == "vent_anchored"
                                   else None)
                _clusters = cluster_hotspots(
                    hot_mask_2d, lat, lon, _vlat, _vlon,
                    vrp_per_pixel=vrp_per_pixel_2d,
                    strategy=_cluster_strategy,
                    inner_radius_km=_cluster_inner,
                )
                n_hotspots_clustered = len(_clusters)
                if _clusters:
                    _c = _clusters[0]
                    primary_cluster = {
                        "n_pixels": _c["n_pixels"],
                        "vrp_mw": round(_c["vrp_mw"], 3),
                        "centroid_lat": round(_c["centroid_lat"], 5),
                        "centroid_lon": round(_c["centroid_lon"], 5),
                        "centroid_dist_km": round(_c["centroid_dist_km"], 3),
                    }

            valid_roi = roi_bt_full[~np.isnan(roi_bt_full)]
            t_max_i04 = float(np.max(valid_roi)) if len(valid_roi) else float("nan")

    # --- TIR channel I05 (11.45 um) — TIRVolcH, low-temperature features ---
    vrp_tir_mw = 0.0
    t_max_i05 = float("nan")

    if "I05" in bands:
        bt5 = bands["I05"]
        bg_vals5 = bt5[bg_mask & ~np.isnan(bt5)]
        if len(bg_vals5) >= 10:
            t_bg_i05 = float(np.median(bg_vals5))
            std_bg5 = float(np.std(bg_vals5))
            threshold_tir = max(TIR_THRESHOLD_K, N_SIGMA_TIR * std_bg5)
            # Use 2D mask so we can pull per-pixel areas (scan-angle corrected)
            hot5_mask_2d = roi_mask & ~np.isnan(bt5) & (bt5 > (t_bg_i05 + threshold_tir))
            hot5_rows, hot5_cols = np.where(hot5_mask_2d)
            if len(hot5_rows) > 0:
                hotpix5 = bt5[hot5_rows, hot5_cols]
                hotpix5_area = pixel_areas[hot5_rows, hot5_cols]
                vrp_w5 = float(np.sum(hotpix5_area * SIGMA * (hotpix5 ** 4 - t_bg_i05 ** 4)))
                vrp_tir_mw = vrp_w5 / 1e6
            roi_bt5 = bt5[roi_mask]
            valid_roi5 = roi_bt5[~np.isnan(roi_bt5)]
            t_max_i05 = float(np.max(valid_roi5)) if len(valid_roi5) else float("nan")

    # --- Vent-scale detection (weak fumarolic signals, VIIRS only) ---
    # Designed to match MIROVA VIIRS375 sensitivity for point-source fumarolic
    # anomalies (~0.1–2 MW). Uses the single hottest pixel in a tight ROI
    # around the known vent, evaluated against the SAME regional background
    # (t_bg_i04) already computed from the volcano reference annulus.
    # Using a shared background avoids biases from separate vent-centered rings
    # and is consistent with the eruption-scale VRP calculation.
    vrp_vent_mw = 0.0
    n_vent_pixels = 0
    vent_hotspot_lat = None
    vent_hotspot_lon = None
    vent_hotspot_dist_km = None
    if (ENABLE_VENT_PATH
            and vent_lat is not None and vent_lon is not None
            and "I04" in bands and not np.isnan(t_bg_i04)):
        vent_dist = haversine_km(vent_lat, vent_lon, lat, lon)
        vent_roi_mask = vent_dist <= vent_radius_km
        if np.any(vent_roi_mask):
            bt = bands["I04"]
            vent_bt_2d = np.where(vent_roi_mask & ~np.isnan(bt), bt, np.nan)
            if np.any(~np.isnan(vent_bt_2d)):
                # Locate the hottest vent pixel (need indices for per-pixel area)
                flat_idx = np.nanargmax(vent_bt_2d)
                r_vent, c_vent = np.unravel_index(flat_idx, vent_bt_2d.shape)
                t_max_vent = float(vent_bt_2d[r_vent, c_vent])
                # S12 2026-04-15: capturar la posición REAL del pixel detectado.
                # Antes no la guardábamos y el frontend dibujaba todos los
                # vent-only en un spiral sintético alrededor del vent. Con
                # las coords reales el mapa refleja dónde físicamente está
                # la anomalía (igual que MIROVA muestra los pixeles dispersos
                # sobre el domo/crater).
                vent_hotspot_lat_candidate = float(lat[r_vent, c_vent])
                vent_hotspot_lon_candidate = float(lon[r_vent, c_vent])
                vent_hotspot_dist_km_candidate = float(
                    haversine_km(vent_lat, vent_lon,
                                 vent_hotspot_lat_candidate,
                                 vent_hotspot_lon_candidate)
                )
                # S12 fix F1: apply sigma gating (N_SIGMA_VENT was imported
                # but never used — the fixed 1K threshold fired on every
                # overpass where the crater was slightly warmer than background,
                # producing ~85% of all FPs system-wide).
                # S12 fix F1b: CAP sigma contribution (MAX_VENT_SIGMA_CONTRIB_K).
                # Without the cap, orographically-complex backgrounds produced
                # thresholds of 6–10 K that killed real 1–2 K sub-pixel signals
                # at Tupungatito and Lastarria (recall drops 54%->10% and 76%->34%).
                if not np.isnan(std_bg_i04):
                    sigma_contrib = min(N_SIGMA_VENT * std_bg_i04, MAX_VENT_SIGMA_CONTRIB_K)
                    vent_thresh = max(VENT_THRESHOLD_K, sigma_contrib)
                else:
                    vent_thresh = VENT_THRESHOLD_K
                if t_max_vent > (t_bg_i04 + vent_thresh):
                    # S12 E4: count how many pixels in vent radius exceed threshold
                    vent_hot_mask = vent_bt_2d > (t_bg_i04 + vent_thresh)
                    n_hot_in_vent = int(np.sum(vent_hot_mask))
                    if n_hot_in_vent >= MIN_VENT_PIXELS:
                        # Wooster MIR radiance with scan-angle corrected pixel area
                        L_vent = bt_to_spectral_radiance(np.float64(t_max_vent), I04_LAMBDA)
                        L_bg_vent = bt_to_spectral_radiance(np.float64(t_bg_i04), I04_LAMBDA)
                        vent_area = float(pixel_areas[r_vent, c_vent])
                        vrp_vent_mw = float(
                            vent_area * WOOSTER_COEFF * (L_vent - L_bg_vent)
                        ) / 1e6
                        n_vent_pixels = n_hot_in_vent
                        vent_hotspot_lat = vent_hotspot_lat_candidate
                        vent_hotspot_lon = vent_hotspot_lon_candidate
                        vent_hotspot_dist_km = vent_hotspot_dist_km_candidate

    name = l1b_path.name
    sensor = _sensor_label_from_filename(name)

    # --- Schema unification (S14 D6) + Regla D Test 1-priority (S26 D) ---
    # S26 D: cuando Test 1 dispara con centroide dentro de inner_radius_km,
    # priorizar ese centroide sobre eruption hotspot far. Análogo a Regla D
    # vent-priority S20 pero para Test 1. Razón: lava lake sub-pixel
    # (Villarrica) genera pixels Test 1 summit pero otros paths detectan
    # pixels far en lago/fjord con VRP individual mayor → primary hotspot
    # cae far → distance_class=far → no matchea ref MIROVA summit.
    # Compute Test 1 hotspot candidate (centroide + dist al vent).
    test1_hotspot_dist_km = None
    if (test1_triggered and test1_centroid_lat is not None
            and vent_lat is not None and vent_lon is not None):
        from .scan_geometry import haversine_km as _hav
        # haversine devuelve array; convertir a float si entradas escalares
        _d = _hav(vent_lat, vent_lon, np.array([test1_centroid_lat]),
                  np.array([test1_centroid_lon]))
        test1_hotspot_dist_km = float(_d[0]) if hasattr(_d, '__len__') else float(_d)

    # Cascada con Regla D Test 1-priority:
    # 1) Si eruption hotspot está far Y Test 1 detectó summit → priorizar Test 1.
    # 2) Sino, eruption normal.
    # 3) Sino, vent-priority (Regla D S20).
    # 4) Sino, None.
    test1_summit_hit = (test1_triggered and inner_radius_km is not None
                        and test1_hotspot_dist_km is not None
                        and test1_hotspot_dist_km <= inner_radius_km)
    eruption_far = (hotspot_dist_km is not None and inner_radius_km is not None
                    and hotspot_dist_km > inner_radius_km)

    # S44 fix: si Test 1 disparó y NINGÚN otro path contribuyó pixels al
    # hot_mask (bt/nti/dnti_ctx/eti todos 0), entonces TODO el hotspot real
    # viene de Test 1, independiente de si está "summit" o "far" relative al
    # inner_radius. Sin este fix, Tupungatito FN persistente: Test 1 dispara
    # con 100 pixels @ 1.05km (summit) pero source="eruption" porque
    # eruption_far=False (1.81km < 7km inner), bloqueando el D4 VRP recompute.
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
            # S44: Test 1 es la única fuente — eruption hotspot existe pero
            # viene desde pixels Test 1 (que están en hot_mask vía OR).
            # source="test1" garantiza que D4 VRP recompute aplique correctamente.
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
        # No hay eruption hotspot pero Test 1 detectó summit.
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

    # MIROVA-style visual classification (S14 D1): summit=red, far=gray.
    distance_class = None
    if final_hotspot_dist_km is not None and inner_radius_km is not None:
        distance_class = "summit" if final_hotspot_dist_km <= inner_radius_km else "far"

    # S26 D fix magnitud: cuando final_hotspot_source='test1', recomputar VRP_MIR
    # usando SOLO los pixels Test 1 mask Y con L_bg LOCAL (ring 1-3km del Test 1).
    # Sin esto:
    #   (a) si usamos t_bg_i04 GLOBAL (anillo 5-25km), Villarrica sale 0 porque
    #       el lago lateral calienta el global por encima del cráter glaciar.
    #   (b) si sumamos todos los hot pixels (no solo Test 1), VRP infla por
    #       contribuciones far (562 MW vs MIROVA 0.05 MW).
    # MIROVA reporta solo cráter usando bg local — replicamos exactamente.
    vrp_mir_mw_test1_only = None  # diag
    # S32 P2 Driver B — Test 1 pixel-level filter (Coppola 2016a Tabla 1).
    # Cuando Test 1 dispara, MIROVA reporta sum solo de pixels que también
    # superan threshold dual-ROI 5σ summit / 10σ scene. Sin este filtro
    # nuestra mask test1_hot suma 14-49 pixels marginales → factor 8-30× MIROVA.
    # Default OFF (backward compat). Activar via enable_test1_pixel_filter.
    test1_hot_filtered = test1_hot
    if (ENABLE_TEST1_PIXEL_FILTER and final_hotspot_source == "test1"
            and inner_radius_km is not None
            and not np.isnan(t_bg_i04) and not np.isnan(std_bg_i04)):
        pixel_thr_mask = dual_roi_bt_threshold(
            bt=bt,
            roi_mask=np.ones_like(bt, dtype=bool),
            dist_km=vent_dist_per_pixel,
            t_bg=t_bg_i04, std_bg=std_bg_i04,
            inner_km=inner_radius_km,
            n_sigma_summit=N_SIGMA_MIR_SUMMIT,
            n_sigma_scene=N_SIGMA_MIR_SCENE,
            anomaly_floor_k=ANOMALY_THRESHOLD_K,
            max_sigma_cap_k=MAX_SIGMA_COMPONENT_K,
        )
        test1_hot_filtered = test1_hot & pixel_thr_mask

    # S33 D4 fix — effective L_bg para Test 1 VRP recompute. En volcanes con
    # geotermal crónico ring 1-3km cráter (Lascar cráter permanente, Lastarria
    # fumarolas), test1_L_bg_local está contaminado → ΔL clip 0 → vrp=0
    # falsos negativos. Cuando flag ON, usar L_bg(t_bg_i04) global del anillo
    # background 5-25km.
    # S39 D4 per-volcano: combinar profile flag con field lbg_global_compatible
    # de volcanoes.yaml — solo aplica si AMBOS son true. Evita regresión
    # Tupungatito glaciar (combo C.1 S38 mostró -1 TP con D4 universal).
    if ENABLE_TEST1_LBG_GLOBAL and lbg_global_compatible and not np.isnan(t_bg_i04):
        effective_L_bg = float(bt_to_spectral_radiance(np.float64(t_bg_i04), I04_LAMBDA))
    else:
        effective_L_bg = test1_L_bg_local

    if (final_hotspot_source == "test1" and "I04" in bands
            and test1_n_contrib > 0 and effective_L_bg is not None
            and not np.isnan(effective_L_bg)):
        t1_rows, t1_cols = np.where(test1_hot_filtered)
        if len(t1_rows) > 0:
            t1_bt = bt[t1_rows, t1_cols]
            t1_L = bt_to_spectral_radiance(t1_bt, I04_LAMBDA)
            # S33 D4: usar effective_L_bg (local default, global con flag ON).
            t1_delta_L = np.maximum(t1_L - effective_L_bg, 0.0)
            t1_area = pixel_areas[t1_rows, t1_cols]
            t1_vrp = t1_area * WOOSTER_COEFF * t1_delta_L / 1e6
            vrp_mir_mw_test1_only = float(np.sum(t1_vrp))
            vrp_mir_mw = vrp_mir_mw_test1_only

    # S31+ fix magnitud: cuando final_hotspot_source='test1', primary_cluster
    # debe ser el cluster contiguo PIXEL-VECINDAD principal (8-conn scipy.label
    # sobre grid 2D), NO un cluster geográfico haversine (que con max_dist
    # 1.5km uniría todos los 62 pixels Test 1 en 1 solo cluster falso).
    # Coppola 2016a SP 426.5 §2.2: "neighbor pixels" = pixels que comparten
    # borde, no "pixels a <Xkm". cluster_hotspots con vrp_per_pixel hace eso.
    if (final_hotspot_source == "test1" and test1_n_contrib > 0
            and effective_L_bg is not None
            and not np.isnan(effective_L_bg)):
        # Construir array 2D de VRP por pixel (solo los pixels Test 1 tienen
        # valor; resto en 0 para que no entren al sum del cluster).
        # S32 P2 Driver B: usar test1_hot_filtered (con N·σ pixel-level si flag ON)
        # S33 D4: usar effective_L_bg (global con flag ON).
        t1_vrp_2d = np.zeros_like(bt, dtype=np.float64)
        t1_rows, t1_cols = np.where(test1_hot_filtered)
        if len(t1_rows) > 0:
            t1_bt = bt[t1_rows, t1_cols]
            t1_L = bt_to_spectral_radiance(t1_bt, I04_LAMBDA)
            t1_delta_L = np.maximum(t1_L - effective_L_bg, 0.0)
            t1_area = pixel_areas[t1_rows, t1_cols]
            t1_vrp_arr = t1_area * WOOSTER_COEFF * t1_delta_L / 1e6
            t1_vrp_2d[t1_rows, t1_cols] = t1_vrp_arr
            # S38: aplicar strategy vent-anchored al cluster Test 1.
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
                top = t1_clusters[0]  # mayor VRP (helper ordena desc cuando vrp dado)
                primary_cluster = {
                    "n_pixels": top["n_pixels"],
                    "vrp_mw": round(top["vrp_mw"], 3),
                    "centroid_lat": round(top["centroid_lat"], 5),
                    "centroid_lon": round(top["centroid_lon"], 5),
                    "centroid_dist_km": round(top["centroid_dist_km"], 3),
                }
                n_hotspots_clustered = len(t1_clusters)

    return {
        "vrp_mir_mw": round(vrp_mir_mw, 3),
        "vrp_tir_mw": round(vrp_tir_mw, 3),
        "vrp_vent_mw": round(vrp_vent_mw, 3),
        "n_anomalous_pixels": n_anomalous,
        "n_hotspots_clustered": n_hotspots_clustered,
        "primary_cluster": primary_cluster,
        "n_excluded_water": n_excluded_water if "I04" in bands and len(bg_vals) >= 10 else 0,
        "n_bt_path": n_bt_path,
        "n_nti_path": n_nti_path,
        "n_nti_rel_path": n_nti_rel_path,
        "n_dnti_ctx_path": n_dnti_ctx_path,
        "n_vent_pixels": n_vent_pixels,
        "vent_hotspot_lat": vent_hotspot_lat,
        "vent_hotspot_lon": vent_hotspot_lon,
        "vent_hotspot_dist_km": round(vent_hotspot_dist_km, 3) if vent_hotspot_dist_km is not None else None,
        "n_cloud_masked": n_cloud_masked,
        "nti_max": round(nti_max, 6) if not np.isnan(nti_max) else None,
        "nti_bg": round(nti_bg, 6) if not np.isnan(nti_bg) else None,
        "n_nti_anomalous": n_nti_anomalous,
        # S22.1 paridad schema MODIS (H_S21_11). Los `diag_*` permiten
        # diagnosticar T4 sin descargar granules raw cada vez. Algunos son
        # alias de campos existentes (nti_bg, nti_max, n_*_path) preservados
        # por compat frontend; otros son nuevos (sigma_bg, eff_threshold,
        # nti_std, t_max_dist_km, roi_p95).
        "diag_sigma_bg_k": round(std_bg_i04, 3) if not np.isnan(std_bg_i04) else None,
        "diag_eff_threshold_k": round(effective_threshold_diag, 2) if not np.isnan(effective_threshold_diag) else None,
        "diag_t_max_dist_km": round(t_max_dist_km_diag, 2) if not np.isnan(t_max_dist_km_diag) else None,
        "diag_roi_p95_k": round(roi_p95_diag, 2) if not np.isnan(roi_p95_diag) else None,
        "diag_nti_bg": round(nti_bg, 4) if not np.isnan(nti_bg) else None,
        "diag_nti_std": round(nti_std, 4) if not np.isnan(nti_std) else None,
        "diag_nti_max": round(nti_max, 4) if not np.isnan(nti_max) else None,
        "diag_n_bt_path": n_bt_path,
        "diag_n_nti_path": n_nti_path,
        "diag_n_dnti_ctx_path": n_dnti_ctx_path,
        "diag_n_eti_path": n_eti_path,  # S37 H_D8_5
        # S46 drift23 — first_pass_tests_2_and_3 diag fields (Task 4 wiring).
        # Persistir n_first_pass_pixels + estadísticos μ/σ del background usados
        # en la regla μ+C2σ. Ausentes (0/None) si flag OFF, I04 no presente, o
        # sin background válido.
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
        # S25 Path Test 1 (Coppola 2015 Eq.1) integrated-ROI MIR
        "triggered_test1": test1_triggered,
        "n_test1_pixels": test1_n_contrib,
        "test1_k_observed": round(float(test1_k_obs), 2) if test1_k_obs else 0.0,
        "hotspot_lat": hotspot_lat,
        "hotspot_lon": hotspot_lon,
        "hotspot_dist_km": hotspot_dist_km,
        # --- unified fields (S14) ---
        "final_hotspot_lat": final_hotspot_lat,
        "final_hotspot_lon": final_hotspot_lon,
        "final_hotspot_dist_km": round(final_hotspot_dist_km, 3) if final_hotspot_dist_km is not None else None,
        "final_hotspot_source": final_hotspot_source,
        "distance_class": distance_class,
        "anomaly_pixels": anomaly_pixels,
        "t_bg_k": round(t_bg_i04, 2) if not np.isnan(t_bg_i04) else None,
        "t_max_i04_k": round(t_max_i04, 2) if not np.isnan(t_max_i04) else None,
        "t_max_i05_k": round(t_max_i05, 2) if not np.isnan(t_max_i05) else None,
        "sensor": sensor,
        "granule": name,
        "product_version": "nrt" if "_NRT" in name else "standard",
        "datetime_utc": _parse_datetime(name),
    }


def _parse_datetime(filename: str) -> str:
    """
    Extract UTC datetime from VIIRS filename.
    Example: VNP02IMG.A2024074.0506.002.nc → 2024-03-14 05:06
    """
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
