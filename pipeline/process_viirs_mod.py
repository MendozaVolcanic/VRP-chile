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

SIGMA = 5.670374419e-8
PIXEL_AREA_M2 = 750.0 ** 2   # 562,500 m²

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
    """Read VNP03MOD geolocation file. Returns lat/lon arrays."""
    if not H5_AVAILABLE:
        raise ImportError("h5py required.")

    with h5py.File(geo_path, "r") as f:
        geo = f["geolocation_data"]
        lat = geo["latitude"][:].astype(np.float32)
        lon = geo["longitude"][:].astype(np.float32)
        lat[lat < -90] = np.nan
        lon[lon < -180] = np.nan
    return {"lat": lat, "lon": lon}


def haversine_km(lat1, lon1, lat2_arr, lon2_arr):
    R = 6371.0
    dlat = np.radians(lat2_arr - lat1)
    dlon = np.radians(lon2_arr - lon1)
    a = (np.sin(dlat / 2) ** 2
         + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2_arr)) * np.sin(dlon / 2) ** 2)
    return R * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def calculate_vrp(l1b_path: Path, geo_path: Path,
                  volcano_lat: float, volcano_lon: float,
                  radius_km: float = 30.0) -> dict | None:
    """
    Calculate VRP from VIIRS 750m M-band granule (VNP02MOD / VJ102MOD).

    Returns dict with VRP or None if granule does not cover volcano.
    """
    bands = read_viirs_mod_l1b(l1b_path)
    if "M13" not in bands:
        return None

    geo = read_viirs_mod_geo(geo_path)
    lat, lon = geo["lat"], geo["lon"]
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

    roi_bt  = bt[roi_mask]
    hotpix  = roi_bt[roi_bt > (t_bg + threshold)]
    hotpix  = hotpix[~np.isnan(hotpix)]
    n_anomalous = len(hotpix)

    vrp_mw = 0.0
    if n_anomalous > 0:
        vrp_w  = float(np.sum(PIXEL_AREA_M2 * SIGMA * (hotpix ** 4 - t_bg ** 4)))
        vrp_mw = vrp_w / 1e6

    valid_roi = roi_bt[~np.isnan(roi_bt)]
    t_max = float(np.max(valid_roi)) if len(valid_roi) else float("nan")

    name   = l1b_path.name
    sensor = "VIIRS_SNPP_750" if name.startswith("VNP") else "VIIRS_NOAA20_750"

    return {
        "vrp_mw": round(vrp_mw, 3),
        "n_anomalous_pixels": n_anomalous,
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
