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

from .scan_geometry import viirs_pixel_areas

SIGMA = 5.670374419e-8  # kept for reference, not used in MIR VRP
# Nadir pixel area; actual area is per-pixel via sensor_zenith correction.
NADIR_PIXEL_AREA_M2 = 750.0 ** 2   # 562,500 m²

# Planck constants for spectral radiance (W/m²/sr/µm)
C1_PLANCK = 1.191042e8   # 2hc² in W·µm⁴/m²/sr
C2_PLANCK = 14388.0      # hc/k in µm·K

# Wooster MIR radiance coefficient (Coppola 2015, Eq.7)
WOOSTER_COEFF = 18.9

FLAG_DNS = {65532, 65533, 65534, 65535}

ANOMALY_THRESHOLD_K = 5.0
N_SIGMA_MIR = 3.0
BG_INNER_KM = 5.0
BG_OUTER_KM = 25.0

# M13 band index within VNP02MOD observation_data
# M-bands: M01..M16 — M13 is at index 12 (0-based)
M13_INDEX = 12
M13_LAMBDA = 4.050   # µm


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


def haversine_km(lat1, lon1, lat2_arr, lon2_arr):
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
                  vent_radius_km: float = 4.0) -> dict | None:
    """
    Calculate VRP from VIIRS 750m M-band granule (VNP02MOD / VJ102MOD).

    Args:
        vent_lat/vent_lon: Optional vent coordinates for weak-signal detection.
        vent_radius_km: Radius for vent-scale search.

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

    roi_mask = dist <= radius_km
    bg_mask  = (dist >= BG_INNER_KM) & (dist <= BG_OUTER_KM)

    if not np.any(roi_mask):
        return None

    bt = bands["M13"]
    bg_vals = bt[bg_mask & ~np.isnan(bt)]
    if len(bg_vals) < 10:
        return None

    t_bg   = float(np.median(bg_vals))
    std_bg = float(np.std(bg_vals))
    threshold = max(ANOMALY_THRESHOLD_K, N_SIGMA_MIR * std_bg)

    # Additional local-ROI filter: avoid topographic false positives
    roi_bt_full = np.where(roi_mask & ~np.isnan(bt), bt, np.nan)
    roi_valid = roi_bt_full[~np.isnan(roi_bt_full)]
    if len(roi_valid) >= 10:
        roi_p95 = float(np.percentile(roi_valid, 95))
        roi_std = float(np.std(roi_valid))
        local_threshold = roi_p95 + max(3.0, 2.0 * roi_std)
        effective_threshold = max(t_bg + threshold, local_threshold)
    else:
        effective_threshold = t_bg + threshold

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
        hotpix_bt = bt[hot_rows, hot_cols]
        L_hot = bt_to_spectral_radiance(hotpix_bt, M13_LAMBDA)
        L_bg_rad = bt_to_spectral_radiance(np.float64(t_bg), M13_LAMBDA)
        # Per-pixel area accounts for scan-angle elongation
        hotpix_area = pixel_areas[hot_rows, hot_cols]
        per_pixel_vrp_mw = hotpix_area * WOOSTER_COEFF * (L_hot - L_bg_rad) / 1e6
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
    vrp_vent_mw = 0.0
    n_vent_pixels = 0
    if vent_lat is not None and vent_lon is not None and not np.isnan(t_bg):
        vent_dist = haversine_km(vent_lat, vent_lon, lat, lon)
        vent_roi_mask = vent_dist <= vent_radius_km
        if np.any(vent_roi_mask):
            vent_bt = np.where(vent_roi_mask & ~np.isnan(bt), bt, np.nan)
            if np.any(~np.isnan(vent_bt)):
                flat_idx = np.nanargmax(vent_bt)
                r_vent, c_vent = np.unravel_index(flat_idx, vent_bt.shape)
                t_max_vent = float(vent_bt[r_vent, c_vent])
                if t_max_vent > (t_bg + 1.0):
                    L_vent = bt_to_spectral_radiance(np.float64(t_max_vent), M13_LAMBDA)
                    L_bg_vent = bt_to_spectral_radiance(np.float64(t_bg), M13_LAMBDA)
                    vent_area = float(pixel_areas[r_vent, c_vent])
                    vrp_vent_mw = float(vent_area * WOOSTER_COEFF * (L_vent - L_bg_vent)) / 1e6
                    n_vent_pixels = 1

    name   = l1b_path.name
    sensor = "VIIRS_SNPP_750" if name.startswith("VNP") else "VIIRS_NOAA20_750"

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
        "t_max_k": round(t_max, 2) if not np.isnan(t_max) else None,
        "sensor": sensor,
        "granule": name,
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
