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

from .scan_geometry import viirs_pixel_areas


SIGMA = 5.670374419e-8   # Stefan-Boltzmann constant, W/m^2/K^4 (TIR only)

# VIIRS I-band nadir pixel area (375 m resolution).
# IMPORTANT: actual pixel area is corrected per-pixel using sensor_zenith
# from the geolocation file. See pipeline/scan_geometry.py.
NADIR_PIXEL_AREA_M2 = 375.0 ** 2   # 140,625 m^2

# Planck constants for spectral radiance (W/m²/sr/µm)
C1 = 1.191042e8   # 2hc² in W·µm⁴/m²/sr
C2 = 14388.0      # hc/k in µm·K

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
)


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


def haversine_km(lat1: float, lon1: float,
                 lat2_arr: np.ndarray, lon2_arr: np.ndarray) -> np.ndarray:
    """Vectorized haversine distance (km) from point to array."""
    R = 6371.0
    dlat = np.radians(lat2_arr - lat1)
    dlon = np.radians(lon2_arr - lon1)
    a = (np.sin(dlat / 2) ** 2
         + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2_arr)) * np.sin(dlon / 2) ** 2)
    return R * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def calculate_vrp(l1b_path: Path, geo_path: Path,
                  volcano_lat: float, volcano_lon: float,
                  radius_km: float = 30.0,
                  vent_lat: float = None, vent_lon: float = None,
                  vent_radius_km: float = 4.0,
                  inner_radius_km: float | None = None) -> dict | None:
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
    pixel_areas = viirs_pixel_areas(geo["sensor_zenith"], NADIR_PIXEL_AREA_M2)

    dist = haversine_km(volcano_lat, volcano_lon, lat, lon)

    roi_mask = dist <= radius_km
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
    n_nti_anomalous = 0

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
    hotspot_lat = None
    hotspot_lon = None
    hotspot_dist_km = None
    anomaly_pixels = []   # All anomalous pixels with location + per-pixel VRP

    if "I04" in bands:
        bt = bands["I04"]
        bg_vals = bt[bg_mask & ~np.isnan(bt)]
        if len(bg_vals) >= 10:
            t_bg_i04 = float(np.median(bg_vals))
            std_bg = float(np.std(bg_vals))
            std_bg_i04 = std_bg  # S12: save for vent-path sigma gating
            threshold_mir = max(ANOMALY_THRESHOLD_K, N_SIGMA_MIR * std_bg)

            roi_bt_full = np.where(roi_mask & ~np.isnan(bt), bt, np.nan)

            # Path A — BT path (existing classic threshold)
            bt_path_hot = roi_mask & ~np.isnan(bt) & (bt > (t_bg_i04 + threshold_mir))

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

            hot_mask_2d = bt_path_hot | nti_path_hot | nti_rel_hot
            n_bt_path = int(np.sum(bt_path_hot))
            n_nti_path = int(np.sum(nti_path_hot))

            hot_rows, hot_cols = np.where(hot_mask_2d)
            n_anomalous = len(hot_rows)

            if n_anomalous > 0:
                hotpix_bt = bt[hot_rows, hot_cols]
                L_hot = bt_to_spectral_radiance(hotpix_bt, I04_LAMBDA)
                L_bg = bt_to_spectral_radiance(np.float64(t_bg_i04), I04_LAMBDA)
                delta_L = L_hot - L_bg
                # Per-pixel area accounts for scan-angle elongation.
                hotpix_area = pixel_areas[hot_rows, hot_cols]
                per_pixel_vrp_mw = hotpix_area * WOOSTER_COEFF * delta_L / 1e6
                vrp_mir_mw = float(np.sum(per_pixel_vrp_mw))

                # Build list of all anomalous pixels sorted by VRP (descending)
                for idx in np.argsort(-per_pixel_vrp_mw):
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
    sensor = "VIIRS_SNPP" if name.startswith("VNP") else "VIIRS_NOAA20"

    # --- Schema unification (S14 D6) ---
    # Unified final_hotspot_* fields with eruption→vent fallback so downstream
    # (dashboard, auditorías) no tiene que elegir entre dos pares de campos.
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

    # MIROVA-style visual classification (S14 D1): summit=red, far=gray.
    distance_class = None
    if final_hotspot_dist_km is not None and inner_radius_km is not None:
        distance_class = "summit" if final_hotspot_dist_km <= inner_radius_km else "far"

    return {
        "vrp_mir_mw": round(vrp_mir_mw, 3),
        "vrp_tir_mw": round(vrp_tir_mw, 3),
        "vrp_vent_mw": round(vrp_vent_mw, 3),
        "n_anomalous_pixels": n_anomalous,
        "n_bt_path": n_bt_path,
        "n_nti_path": n_nti_path,
        "n_nti_rel_path": n_nti_rel_path,
        "n_vent_pixels": n_vent_pixels,
        "vent_hotspot_lat": vent_hotspot_lat,
        "vent_hotspot_lon": vent_hotspot_lon,
        "vent_hotspot_dist_km": round(vent_hotspot_dist_km, 3) if vent_hotspot_dist_km is not None else None,
        "n_cloud_masked": n_cloud_masked,
        "nti_max": round(nti_max, 6) if not np.isnan(nti_max) else None,
        "nti_bg": round(nti_bg, 6) if not np.isnan(nti_bg) else None,
        "n_nti_anomalous": n_nti_anomalous,
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
