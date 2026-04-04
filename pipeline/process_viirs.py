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


SIGMA = 5.670374419e-8   # Stefan-Boltzmann constant, W/m^2/K^4

# VIIRS I-band pixel area at nadir (375 m resolution)
PIXEL_AREA_M2 = 375.0 ** 2   # 140,625 m^2

# Flag DN values (from file attributes)
FLAG_DNS = {65532, 65533, 65534, 65535}  # Missing_EV, Bowtie_Deleted, Cal_Fail, Fill

# Minimum fixed threshold (K above background)
ANOMALY_THRESHOLD_K = 5.0    # MIR channel (I04)
TIR_THRESHOLD_K = 0.5        # TIR channel (I05), per TIRVolcH

# Statistical multiplier: threshold = max(fixed, N_SIGMA * std_background)
# MIROVA uses this to reject natural terrain variability
N_SIGMA_MIR = 3.0
N_SIGMA_TIR = 4.0   # TIR is noisier due to surface/cloud variability

BG_INNER_KM = 5.0
BG_OUTER_KM = 25.0


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
    Returns dict with 'lat' and 'lon' arrays (degrees, float32).
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
    return {"lat": lat, "lon": lon}


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
                  radius_km: float = 30.0) -> dict | None:
    """
    Calculate VRP from a single VIIRS L1B granule.

    Args:
        l1b_path: Path to VNP02IMG or VJ102IMG file (.nc)
        geo_path: Path to VNP03IMG or VJ103IMG geolocation file (.nc)
        volcano_lat: Volcano latitude (degrees)
        volcano_lon: Volcano longitude (degrees)
        radius_km: Search radius around volcano for anomaly detection

    Returns dict with VRP values, or None if granule does not cover volcano.
    """
    bands = read_viirs_l1b(l1b_path)
    geo = read_viirs_geo(geo_path)

    lat = geo["lat"]
    lon = geo["lon"]
    dist = haversine_km(volcano_lat, volcano_lon, lat, lon)

    roi_mask = dist <= radius_km
    bg_mask = (dist >= BG_INNER_KM) & (dist <= BG_OUTER_KM)

    if not np.any(roi_mask):
        return None

    # --- MIR channel I04 (3.74 um) — high-temperature features ---
    vrp_mir_mw = 0.0
    t_bg_i04 = float("nan")
    t_max_i04 = float("nan")
    n_anomalous = 0

    if "I04" in bands:
        bt = bands["I04"]
        bg_vals = bt[bg_mask & ~np.isnan(bt)]
        if len(bg_vals) >= 10:
            t_bg_i04 = float(np.median(bg_vals))
            std_bg = float(np.std(bg_vals))
            threshold_mir = max(ANOMALY_THRESHOLD_K, N_SIGMA_MIR * std_bg)
            roi_bt = bt[roi_mask]
            hotpix = roi_bt[roi_bt > (t_bg_i04 + threshold_mir)]
            hotpix = hotpix[~np.isnan(hotpix)]
            n_anomalous = len(hotpix)
            if n_anomalous > 0:
                vrp_w = float(np.sum(PIXEL_AREA_M2 * SIGMA * (hotpix ** 4 - t_bg_i04 ** 4)))
                vrp_mir_mw = vrp_w / 1e6
            valid_roi = roi_bt[~np.isnan(roi_bt)]
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
            roi_bt5 = bt5[roi_mask]
            hotpix5 = roi_bt5[roi_bt5 > (t_bg_i05 + threshold_tir)]
            hotpix5 = hotpix5[~np.isnan(hotpix5)]
            if len(hotpix5) > 0:
                vrp_w5 = float(np.sum(PIXEL_AREA_M2 * SIGMA * (hotpix5 ** 4 - t_bg_i05 ** 4)))
                vrp_tir_mw = vrp_w5 / 1e6
            valid_roi5 = roi_bt5[~np.isnan(roi_bt5)]
            t_max_i05 = float(np.max(valid_roi5)) if len(valid_roi5) else float("nan")

    name = l1b_path.name
    sensor = "VIIRS_SNPP" if name.startswith("VNP") else "VIIRS_NOAA20"

    return {
        "vrp_mir_mw": round(vrp_mir_mw, 3),
        "vrp_tir_mw": round(vrp_tir_mw, 3),
        "n_anomalous_pixels": n_anomalous,
        "t_bg_k": round(t_bg_i04, 2) if not np.isnan(t_bg_i04) else None,
        "t_max_i04_k": round(t_max_i04, 2) if not np.isnan(t_max_i04) else None,
        "t_max_i05_k": round(t_max_i05, 2) if not np.isnan(t_max_i05) else None,
        "sensor": sensor,
        "granule": name,
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
