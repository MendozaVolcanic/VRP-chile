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

from .scan_geometry import modis_pixel_areas


SIGMA = 5.670374419e-8
C1 = 1.191042e8
C2 = 14388.0

BAND21_LAMBDA = 3.929
BAND22_LAMBDA = 3.959
# Nadir pixel area; actual area is computed per-pixel from scan column index
# in scan_geometry.modis_pixel_areas (sec^3(theta_z) correction).
NADIR_PIXEL_AREA_M2 = 1e6  # 1 km^2 at nadir

# Wooster MIR radiance coefficient (Coppola 2015, Eq.7)
WOOSTER_COEFF = 18.9

ANOMALY_THRESHOLD_K = 5.0
N_SIGMA = 3.0
BG_INNER_KM = 5.0
BG_OUTER_KM = 25.0

# Indices of bands 21 and 22 within EV_1KM_Emissive
# Band_1KM_Emissive order: [20,21,22,23,24,25,27,28,29,30,31,32,33,34,35,36]
BAND21_IDX = 1
BAND22_IDX = 2


def radiance_to_bt(L: np.ndarray, wavelength_um: float) -> np.ndarray:
    with np.errstate(invalid="ignore", divide="ignore"):
        return C2 / (wavelength_um * np.log(C1 / (L * wavelength_um ** 5) + 1))


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
    fill = attrs.get("_FillValue", 65535)
    emissive_sds.endaccess()

    def calibrate(band_idx, wavelength):
        dn = emissive_data[band_idx].astype(np.float32)
        rad = (dn - offsets[band_idx]) * scales[band_idx]
        rad[dn >= fill] = np.nan
        return rad

    band21 = calibrate(BAND21_IDX, BAND21_LAMBDA)
    band22 = calibrate(BAND22_IDX, BAND22_LAMBDA)

    # --- Read coarse geolocation (5km grid embedded in MOD021KM) ---
    lat_coarse = sd.select("Latitude").get().astype(np.float32)   # (406, 271) for 2030x1354
    lon_coarse = sd.select("Longitude").get().astype(np.float32)

    sd.end()

    # Interpolate coarse lat/lon to full 1km resolution
    n_lines, n_samples = band21.shape
    lat = _interp_geo(lat_coarse, n_lines, n_samples)
    lon = _interp_geo(lon_coarse, n_lines, n_samples)

    return {"band21": band21, "band22": band22, "lat": lat, "lon": lon}


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


def haversine_km(lat1, lon1, lat2_arr, lon2_arr):
    R = 6371.0
    dlat = np.radians(lat2_arr - lat1)
    dlon = np.radians(lon2_arr - lon1)
    a = (np.sin(dlat / 2) ** 2
         + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2_arr)) * np.sin(dlon / 2) ** 2)
    return R * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def calculate_vrp(hdf_path: Path, geo_path: Path,
                  volcano_lat: float, volcano_lon: float,
                  radius_km: float = 15.0,
                  vent_lat: float = None, vent_lon: float = None,
                  vent_radius_km: float = 4.0) -> dict | None:
    """
    Calculate VRP from MODIS L1B granule.

    geo_path is accepted for API compatibility but not used —
    geolocation is embedded in MOD021KM.

    Args:
        vent_lat/vent_lon: Optional vent coordinates for weak-signal detection.
            Uses a low threshold (1K) in a tight ROI without ROI p95 filter.
        vent_radius_km: Radius for vent-scale search.

    Returns dict or None if granule does not cover volcano.
    """
    data = read_modis_l1b(hdf_path)

    lat = data["lat"]
    lon = data["lon"]
    # Per-pixel ground area corrected for off-nadir scan geometry
    pixel_areas = modis_pixel_areas(lat.shape)
    dist = haversine_km(volcano_lat, volcano_lon, lat, lon)

    roi_mask = dist <= radius_km
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

    bg_vals = bt_mir[bg_mask & ~np.isnan(bt_mir)]
    if len(bg_vals) < 10:
        return None

    t_bg = float(np.median(bg_vals))
    std_bg = float(np.std(bg_vals))
    threshold = max(ANOMALY_THRESHOLD_K, N_SIGMA * std_bg)

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
    P95_VENT_EXCLUSION_KM = 5.0  # conservative margin for MODIS 1km pixels
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
        effective_threshold = t_bg + threshold

    # Find all anomalous pixels with their 2D indices
    hot_mask_2d = roi_bt_full > effective_threshold
    hot_rows, hot_cols = np.where(hot_mask_2d)
    n_anomalous = len(hot_rows)

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
        L_bg = float(C1 / (BAND21_LAMBDA ** 5 * (np.exp(C2 / (BAND21_LAMBDA * t_bg)) - 1)))

        hotpix_bt = bt_mir[hot_rows, hot_cols]
        # Convert hot pixel BT to radiance for consistent VRP calculation
        hotpix_rad = C1 / (BAND21_LAMBDA ** 5 * (np.exp(C2 / (BAND21_LAMBDA * hotpix_bt)) - 1))
        # Per-pixel area accounts for scan-angle elongation
        hotpix_area = pixel_areas[hot_rows, hot_cols]
        per_pixel_vrp_mw = hotpix_area * WOOSTER_COEFF * (hotpix_rad - L_bg) / 1e6
        vrp_mw = float(np.nansum(per_pixel_vrp_mw))

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
    t_max = float(np.max(valid_roi)) if len(valid_roi) else float("nan")

    # --- Vent-scale detection (weak fumarolic signals) ---
    # Same approach as VIIRS 375m: tight ROI around known vent, low threshold,
    # no ROI p95 filter. Uses the regional background (t_bg) already computed.
    vrp_vent_mw = 0.0
    n_vent_pixels = 0
    if vent_lat is not None and vent_lon is not None and not np.isnan(t_bg):
        vent_dist = haversine_km(vent_lat, vent_lon, lat, lon)
        vent_roi_mask = vent_dist <= vent_radius_km
        if np.any(vent_roi_mask):
            vent_bt = np.where(vent_roi_mask & ~np.isnan(bt_mir), bt_mir, np.nan)
            if np.any(~np.isnan(vent_bt)):
                flat_idx = np.nanargmax(vent_bt)
                r_vent, c_vent = np.unravel_index(flat_idx, vent_bt.shape)
                t_max_vent = float(vent_bt[r_vent, c_vent])
                # Low threshold: 1K above regional background (no ROI p95)
                if t_max_vent > (t_bg + 1.0):
                    L_vent = float(C1 / (BAND21_LAMBDA ** 5 * (np.exp(C2 / (BAND21_LAMBDA * t_max_vent)) - 1)))
                    L_bg_vent = float(C1 / (BAND21_LAMBDA ** 5 * (np.exp(C2 / (BAND21_LAMBDA * t_bg)) - 1)))
                    vent_area = float(pixel_areas[r_vent, c_vent])
                    vrp_vent_mw = float(vent_area * WOOSTER_COEFF * (L_vent - L_bg_vent)) / 1e6
                    n_vent_pixels = 1

    return {
        "vrp_mw": round(vrp_mw, 3),
        "vrp_vent_mw": round(vrp_vent_mw, 3),
        "n_anomalous_pixels": n_anomalous,
        "n_vent_pixels": n_vent_pixels,
        "hotspot_lat": hotspot_lat,
        "hotspot_lon": hotspot_lon,
        "hotspot_dist_km": hotspot_dist_km,
        "anomaly_pixels": anomaly_pixels,
        "t_bg_k": round(t_bg, 2),
        "t_max_k": round(t_max, 2),
        "sensor": "MODIS_TERRA" if "MOD0" in hdf_path.name else "MODIS_AQUA",
        "granule": hdf_path.name,
        "datetime_utc": _parse_datetime(hdf_path.name),
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
