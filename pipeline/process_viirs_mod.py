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
from .clustering import cluster_hotspots

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
    N_SIGMA_MIR_SUMMIT,
    N_SIGMA_MIR_SCENE,
    ENABLE_EXCLUDE_ZONES,
    P95_VENT_EXCLUSION_VIIRS750_KM,
)
from .detection_context import (
    contextual_dnti_hot_mask,
    dual_roi_contextual_dnti_hot_mask,
    dual_roi_bt_threshold,
)

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

    result = {}
    with h5py.File(l1b_path, "r") as f:
        obs = f["observation_data"]

        # Try direct M13 dataset first
        band_key = "M13"
        if band_key not in obs:
            return result

        dn = obs[band_key][:]

        lut_key = "M13_brightness_temperature_lut"
        if lut_key in obs:
            lut = obs[lut_key][:]
            bt = lut[dn].astype(np.float32)
            flag_mask = np.isin(dn, list(FLAG_DNS))
            bt[flag_mask] = np.nan
            bt[bt < 0] = np.nan
        else:
            ds = obs[band_key]
            scale  = float(ds.attrs.get("scale_factor", 1.0))
            offset = float(ds.attrs.get("add_offset", 0.0))
            rad = dn.astype(np.float32) * scale + offset
            flag_mask = np.isin(dn, list(FLAG_DNS))
            rad[flag_mask] = np.nan
            # Planck inversion
            C1, C2 = 1.191042e8, 14388.0
            with np.errstate(invalid="ignore", divide="ignore"):
                bt = C2 / (M13_LAMBDA * np.log(C1 / (rad * M13_LAMBDA ** 5) + 1))

        result["M13"] = bt

        # --- M15 TIR band (10.763 µm) for NTI computation ---
        band_key_15 = "M15"
        if band_key_15 in obs:
            dn15 = obs[band_key_15][:]
            lut_key_15 = "M15_brightness_temperature_lut"
            if lut_key_15 in obs:
                lut15 = obs[lut_key_15][:]
                bt15 = lut15[dn15].astype(np.float32)
                flag_mask_15 = np.isin(dn15, list(FLAG_DNS))
                bt15[flag_mask_15] = np.nan
                bt15[bt15 < 0] = np.nan
            else:
                ds15 = obs[band_key_15]
                scale15  = float(ds15.attrs.get("scale_factor", 1.0))
                offset15 = float(ds15.attrs.get("add_offset", 0.0))
                rad15 = dn15.astype(np.float32) * scale15 + offset15
                flag_mask_15 = np.isin(dn15, list(FLAG_DNS))
                rad15[flag_mask_15] = np.nan
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
                  active_water_bodies: list = None) -> dict | None:
    """
    Calculate VRP from VIIRS 750m M-band granule (VNP02MOD / VJ102MOD).

    Args:
        vent_lat/vent_lon: Optional vent coordinates for weak-signal detection.
        vent_radius_km: Radius for vent-scale search.
        inner_radius_km: MIROVA-style visual classification radius (S14 D1).
            If None, distance_class is None.

    Returns dict with VRP or None if granule does not cover volcano.
    """
    bands = read_viirs_mod_l1b(l1b_path)
    if "M13" not in bands:
        return None

    geo = read_viirs_mod_geo(geo_path)
    lat, lon = geo["lat"], geo["lon"]
    # Per-pixel ground area corrected for off-nadir geometry
    pixel_areas = viirs_pixel_areas(geo["sensor_zenith"], NADIR_PIXEL_AREA_M2)
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
    bg_vals = bt[bg_mask & ~np.isnan(bt)]
    if len(bg_vals) < 10:
        return None

    t_bg   = float(np.median(bg_vals))
    std_bg = float(np.std(bg_vals))
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
    nti = None
    # S22.1 paridad MODIS schema (H_S21_11). roi_p95 y t_max_dist_km_diag se
    # rellenan en el bloque BT cuando hay ROI válida; quedan NaN si no.
    roi_p95 = float("nan")
    t_max_dist_km_diag = float("nan")

    if "M15" in bands:
        bt_mir = bands["M13"]
        bt_tir = bands["M15"]
        L_mir_all = bt_to_spectral_radiance(bt_mir, M13_LAMBDA)
        L_tir_all = bt_to_spectral_radiance(bt_tir, M15_LAMBDA)
        valid_both = ~np.isnan(L_mir_all) & ~np.isnan(L_tir_all) & (L_mir_all + L_tir_all > 0)
        nti = np.full_like(L_mir_all, np.nan)
        nti[valid_both] = (L_mir_all[valid_both] - L_tir_all[valid_both]) / (L_mir_all[valid_both] + L_tir_all[valid_both])

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

    # Path D — dNTI contextual 8-vecinos (P3.2 + P3.1 S15, Coppola 2016a).
    # P3.1 dual-ROI: summit C1=0.003 sensible, scene C1=0.010 estricto.
    n_dnti_ctx_path = 0
    if (ENABLE_DNTI_CONTEXTUAL_PATH
            and nti is not None
            and not np.isnan(nti_bg)):
        if ENABLE_DNTI_DUAL_ROI and inner_radius_km is not None:
            dnti_ctx_hot = dual_roi_contextual_dnti_hot_mask(
                nti=nti, bt=bt, roi_mask=roi_mask,
                dist_km=vent_dist_per_pixel,
                t_bg=t_bg,
                c1_summit=DNTI_CONTEXTUAL_C1_SUMMIT,
                c1_scene=DNTI_CONTEXTUAL_C1_SCENE,
                inner_km=inner_radius_km,
                bt_sanity_k=NTI_BT_SANITY_K,
            )
        else:
            dnti_ctx_hot = contextual_dnti_hot_mask(
                nti=nti, bt=bt, roi_mask=roi_mask,
                t_bg=t_bg,
                c1=DNTI_CONTEXTUAL_C1,
                bt_sanity_k=NTI_BT_SANITY_K,
            )
        n_dnti_ctx_path = int(np.sum(dnti_ctx_hot))
    else:
        dnti_ctx_hot = np.zeros_like(roi_mask)

    hot_mask_2d = bt_path_hot | nti_path_hot | nti_rel_hot | dnti_ctx_hot

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

    hot_rows, hot_cols = np.where(hot_mask_2d)
    n_anomalous = len(hot_rows)

    # S27 cluster aggregation se mueve abajo (post per_pixel_vrp_mw)
    # para incluir vrp_mw del cluster contiguo principal (D1 cierre completo).
    n_hotspots_clustered = 0
    primary_cluster = None

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
        _clusters = cluster_hotspots(
            hot_mask_2d, lat, lon, _vlat, _vlon,
            vrp_per_pixel=vrp_per_pixel_2d,
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
    if hotspot_lat is not None and hotspot_lon is not None:
        final_hotspot_lat = hotspot_lat
        final_hotspot_lon = hotspot_lon
        final_hotspot_dist_km = hotspot_dist_km
        final_hotspot_source = "eruption"
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
        "diag_n_bt_path": n_bt_path,
        "diag_n_nti_path": n_nti_path,
        "diag_n_dnti_ctx_path": n_dnti_ctx_path,
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
