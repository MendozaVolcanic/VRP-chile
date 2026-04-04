"""
process_viirs.py — Calculate VRP from VIIRS VNP02IMG / VJ102IMG L1B granules.

Algorithm: adapted from TIRVolcH (Aveni et al. 2024, RSE) and
           MODIS-to-VIIRS transition (Campus et al. 2022, Sensors).

Bands used:
  - I4 (3.74 um, 375m): primary MIR channel for volcanic hotspots
    Saturation radiance: ~26.3 W/m^2/sr/um (~600 K equivalent)
  - I5 (11.45 um, 375m): TIR channel for low-temperature anomalies
    Used for hydrothermal/fumarolic systems (T < 600 K) per TIRVolcH

VIIRS I-band spatial resolution: 375 m (vs MODIS 1 km)
-> Higher spatial resolution = better for small/weak anomalies like Cordon Caulle

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


SIGMA = 5.670374419e-8
C1 = 1.191042e8
C2 = 14388.0

# VIIRS I-band central wavelengths (um)
BAND_I4_LAMBDA = 3.740
BAND_I5_LAMBDA = 11.450

# VIIRS I-band pixel area at nadir (375 m resolution)
PIXEL_AREA_M2 = 375.0**2    # = 140,625 m^2

ANOMALY_THRESHOLD_K = 5.0
BG_INNER_KM = 5.0
BG_OUTER_KM = 25.0


def radiance_to_bt(L: np.ndarray, wavelength_um: float) -> np.ndarray:
    with np.errstate(invalid="ignore", divide="ignore"):
        bt = C2 / (wavelength_um * np.log(C1 / (L * wavelength_um**5) + 1))
    return bt


def read_viirs_l1b(l1b_path: Path) -> dict:
    """
    Read VIIRS VNP02IMG HDF5 file.

    VIIRS L1B stores radiance as scaled integers under:
      /observation_data/I4_Radiance   (shape: n_scans*32, n_samples)
      /observation_data/I5_Radiance
    Scaling: radiance = DN * scale + offset  (stored as attributes)

    Returns dict with 'I4' and 'I5' radiance arrays (W/m^2/sr/um).
    """
    if not H5_AVAILABLE:
        raise ImportError("h5py required. Install: pip install h5py")

    result = {}
    with h5py.File(l1b_path, "r") as f:
        obs = f["observation_data"]
        for band_name in ("I4", "I5"):
            key = f"{band_name}_Radiance"
            if key not in obs:
                continue
            ds = obs[key]
            data = ds[:].astype(np.float32)
            # Read calibration coefficients
            scale = ds.attrs.get("scale_factor", 1.0)
            offset = ds.attrs.get("add_offset", 0.0)
            fill = ds.attrs.get("_FillValue", 65535)
            # Apply scaling
            radiance = data * scale + offset
            radiance = np.where(data >= fill, np.nan, radiance)
            result[band_name] = radiance
    return result


def read_viirs_geo(geo_path: Path) -> dict:
    """
    Read VIIRS VNP03IMG / VJ103IMG geolocation HDF5 file.
    Returns dict with 'lat' and 'lon' arrays (degrees).
    """
    if not H5_AVAILABLE:
        raise ImportError("h5py required.")

    with h5py.File(geo_path, "r") as f:
        geo_data = f["geolocation_data"]
        lat = geo_data["latitude"][:].astype(np.float32)
        lon = geo_data["longitude"][:].astype(np.float32)
    return {"lat": lat, "lon": lon}


def haversine_km(lat1, lon1, lat2_arr, lon2_arr):
    R = 6371.0
    dlat = np.radians(lat2_arr - lat1)
    dlon = np.radians(lon2_arr - lon1)
    a = (np.sin(dlat / 2)**2
         + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2_arr)) * np.sin(dlon / 2)**2)
    return R * 2 * np.arcsin(np.sqrt(a))


def calculate_vrp(l1b_path: Path, geo_path: Path,
                  volcano_lat: float, volcano_lon: float,
                  radius_km: float = 30.0) -> dict:
    """
    Calculate VRP from a single VIIRS L1B granule.

    Uses band I4 (3.74 um) for the MIR-based VRP (same approach as MIROVA/MODIS).
    Also computes a TIR-based VRP from I5 (11.45 um) using the TIRVolcH approach,
    which is more sensitive to low-temperature features like Cordon Caulle fumaroles.

    Returns:
        {
          "vrp_mir_mw": float,    # VRP from I4 band (MW)
          "vrp_tir_mw": float,    # VRP from I5 band, TIRVolcH approach (MW)
          "n_anomalous_pixels": int,
          "t_bg_k": float,
          "t_max_i4_k": float,
          "t_max_i5_k": float,
          "sensor": str,
          "granule": str,
          "datetime_utc": str,
        }
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

    # --- MIR channel (I4, 3.74 um) ---
    vrp_mir_mw = 0.0
    t_bg_i4 = float("nan")
    t_max_i4 = float("nan")
    n_anomalous = 0

    if "I4" in bands:
        bt_i4 = radiance_to_bt(bands["I4"], BAND_I4_LAMBDA)
        bg_bt = bt_i4[bg_mask]
        bg_bt = bg_bt[~np.isnan(bg_bt)]
        if len(bg_bt) >= 10:
            t_bg_i4 = float(np.median(bg_bt))
            roi_bt = bt_i4[roi_mask]
            anomaly = roi_bt > (t_bg_i4 + ANOMALY_THRESHOLD_K)
            n_anomalous = int(np.sum(anomaly))
            if n_anomalous > 0:
                t_hot = roi_bt[anomaly]
                vrp_w = float(np.sum(PIXEL_AREA_M2 * SIGMA * (t_hot**4 - t_bg_i4**4)))
                vrp_mir_mw = vrp_w / 1e6
            t_max_i4 = float(np.nanmax(bt_i4[roi_mask]))

    # --- TIR channel (I5, 11.45 um) — TIRVolcH approach ---
    # Detects anomalies as low as 0.5 K above background
    # Better suited for Cordon Caulle fumarolic activity (T < 600 K)
    vrp_tir_mw = 0.0
    t_max_i5 = float("nan")
    TIR_THRESHOLD_K = 0.5   # Per TIRVolcH (Aveni et al. 2024)

    if "I5" in bands:
        bt_i5 = radiance_to_bt(bands["I5"], BAND_I5_LAMBDA)
        bg_bt5 = bt_i5[bg_mask]
        bg_bt5 = bg_bt5[~np.isnan(bg_bt5)]
        if len(bg_bt5) >= 10:
            t_bg_i5 = float(np.median(bg_bt5))
            roi_bt5 = bt_i5[roi_mask]
            anomaly5 = roi_bt5 > (t_bg_i5 + TIR_THRESHOLD_K)
            if np.any(anomaly5):
                t_hot5 = roi_bt5[anomaly5]
                vrp_w5 = float(np.sum(PIXEL_AREA_M2 * SIGMA * (t_hot5**4 - t_bg_i5**4)))
                vrp_tir_mw = vrp_w5 / 1e6
            t_max_i5 = float(np.nanmax(bt_i5[roi_mask]))

    sensor = "VIIRS_SNPP" if l1b_path.name.startswith("VNP") else "VIIRS_NOAA20"

    return {
        "vrp_mir_mw": round(vrp_mir_mw, 3),
        "vrp_tir_mw": round(vrp_tir_mw, 3),
        "n_anomalous_pixels": n_anomalous,
        "t_bg_k": round(t_bg_i4, 2),
        "t_max_i4_k": round(t_max_i4, 2),
        "t_max_i5_k": round(t_max_i5, 2),
        "sensor": sensor,
        "granule": l1b_path.name,
        "datetime_utc": _parse_datetime(l1b_path.name),
    }


def _parse_datetime(filename: str) -> str:
    """
    Extract UTC datetime from VIIRS filename.
    Example: VNP02IMG.A2024074.0006.002.2024074123456.nc
             -> 2024-03-14 00:06
    """
    try:
        parts = filename.split(".")
        date_part = parts[1]
        time_part = parts[2]
        year = int(date_part[1:5])
        doy = int(date_part[5:8])
        hour = int(time_part[:2])
        minute = int(time_part[2:4])
        import datetime
        dt = datetime.datetime(year, 1, 1) + datetime.timedelta(days=doy - 1,
                                                                  hours=hour,
                                                                  minutes=minute)
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return "unknown"
