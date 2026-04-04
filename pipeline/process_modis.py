"""
process_modis.py — Calculate VRP from MODIS MOD021KM / MYD021KM L1B granules.

Algorithm: MIROVA (Coppola et al. 2015, sp426.5)
  VRP = A_pixel * sigma * (T_pix^4 - T_bg^4)

Bands used:
  - Band 21 (3.929 um): primary MIR channel, saturation ~500 K
  - Band 22 (3.959 um): backup, saturation ~335 K (more sensitive, saturates sooner)

Strategy: use Band 21 as primary; fall back to Band 22 where Band 21 is saturated.

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
    print("WARNING: pyhdf not found. Install via: conda install -c conda-forge pyhdf")


# Physical constants
SIGMA = 5.670374419e-8   # Stefan-Boltzmann constant, W/m^2/K^4
C1 = 1.191042e8          # First radiation constant for Planck, W*um^4/m^2/sr
C2 = 14388.0             # Second radiation constant, um*K

# MODIS band central wavelengths (um)
BAND21_LAMBDA = 3.929
BAND22_LAMBDA = 3.959

# MODIS nominal pixel area at nadir (1 km resolution)
PIXEL_AREA_M2 = 1e6      # 1 km^2 in m^2

# Threshold for anomaly detection (K above background)
ANOMALY_THRESHOLD_K = 5.0

# Background annulus: pixels between inner_km and outer_km from volcano center
BG_INNER_KM = 5.0
BG_OUTER_KM = 25.0


def radiance_to_bt(L: np.ndarray, wavelength_um: float) -> np.ndarray:
    """
    Convert spectral radiance to brightness temperature (Planck inversion).

    Args:
        L: Radiance in W/m^2/sr/um
        wavelength_um: Central wavelength in micrometers

    Returns:
        Brightness temperature in Kelvin
    """
    with np.errstate(invalid="ignore", divide="ignore"):
        bt = C2 / (wavelength_um * np.log(C1 / (L * wavelength_um**5) + 1))
    return bt


def read_modis_l1b(hdf_path: Path) -> dict:
    """
    Read MODIS L1B HDF4 file and return calibrated radiances for bands 21 and 22.

    The HDF4 file stores scaled integers. Calibration:
        L = (DN - offset) * scale
    where scale and offset are per-detector, stored as SDS attributes.

    Returns dict with keys: 'band21', 'band22' (radiance arrays, W/m^2/sr/um)
    """
    if not HDF4_AVAILABLE:
        raise ImportError("pyhdf required. Install: conda install -c conda-forge pyhdf")

    sd = SD(str(hdf_path), SDC.READ)

    def read_band(sds_name):
        sds = sd.select(sds_name)
        data = sds.get().astype(np.float32)
        attrs = sds.attributes()
        scales = np.array(attrs["radiance_scales"])
        offsets = np.array(attrs["radiance_offsets"])
        # scales/offsets are per detector (rows in the scan)
        # data shape: (n_scans*10, n_samples) for 1km product
        # each scan = 10 detectors; scales shape = (n_detectors,)
        n_det = len(scales)
        # Reshape to apply per-detector calibration
        n_rows, n_cols = data.shape
        radiance = np.empty_like(data)
        for det in range(n_det):
            radiance[det::n_det, :] = (data[det::n_det, :] - offsets[det]) * scales[det]
        # Mask fill values (stored as 65535 or as flagged values)
        fill = attrs.get("_FillValue", 65535)
        radiance = np.where(data >= fill, np.nan, radiance)
        sds.endaccess()
        return radiance

    result = {
        "band21": read_band("EV_Band21"),
        "band22": read_band("EV_Band22"),
    }
    sd.end()
    return result


def read_modis_geo(geo_path: Path) -> dict:
    """
    Read MODIS MOD03/MYD03 geolocation file.
    Returns dict with 'lat' and 'lon' arrays (degrees).
    """
    if not HDF4_AVAILABLE:
        raise ImportError("pyhdf required.")

    sd = SD(str(geo_path), SDC.READ)
    lat = sd.select("Latitude").get().astype(np.float32)
    lon = sd.select("Longitude").get().astype(np.float32)
    sd.end()
    return {"lat": lat, "lon": lon}


def haversine_km(lat1, lon1, lat2_arr, lon2_arr):
    """
    Vectorized haversine distance from a single point to an array of points.
    Returns distance array in km.
    """
    R = 6371.0
    dlat = np.radians(lat2_arr - lat1)
    dlon = np.radians(lon2_arr - lon1)
    a = np.sin(dlat / 2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2_arr)) * np.sin(dlon / 2)**2
    return R * 2 * np.arcsin(np.sqrt(a))


def calculate_vrp(l1b_path: Path, geo_path: Path,
                  volcano_lat: float, volcano_lon: float,
                  radius_km: float = 30.0) -> dict:
    """
    Calculate Volcanic Radiative Power from a single MODIS L1B granule.

    Args:
        l1b_path: Path to MOD021KM or MYD021KM HDF4 file
        geo_path: Path to MOD03 or MYD03 geolocation HDF4 file
        volcano_lat: Volcano latitude (degrees)
        volcano_lon: Volcano longitude (degrees)
        radius_km: Search radius around volcano for hotspot detection

    Returns:
        {
          "vrp_mw": float,          # Volcanic Radiative Power in MW (0 if no anomaly)
          "n_anomalous_pixels": int, # Number of pixels exceeding threshold
          "t_bg_k": float,          # Background brightness temperature (K)
          "t_max_k": float,         # Max pixel brightness temperature (K)
          "sensor": str,            # "MODIS_TERRA" or "MODIS_AQUA"
          "granule": str,           # Granule filename
          "datetime_utc": str,      # Datetime from filename (YYYY-MM-DD HH:MM)
        }
    """
    bands = read_modis_l1b(l1b_path)
    geo = read_modis_geo(geo_path)

    lat = geo["lat"]
    lon = geo["lon"]
    dist = haversine_km(volcano_lat, volcano_lon, lat, lon)

    # Region of interest: pixels within radius_km of volcano
    roi_mask = dist <= radius_km
    # Background annulus: between BG_INNER_KM and BG_OUTER_KM
    bg_mask = (dist >= BG_INNER_KM) & (dist <= BG_OUTER_KM)

    if not np.any(roi_mask):
        # Granule does not cover the volcano
        return None

    # Convert radiance to brightness temperature
    # Use Band 21 primarily; replace saturated pixels with Band 22 estimate
    bt21 = radiance_to_bt(bands["band21"], BAND21_LAMBDA)
    bt22 = radiance_to_bt(bands["band22"], BAND22_LAMBDA)

    # Band 22 saturates at lower temperatures (~335 K) so if bt22 is NaN/invalid
    # AND bt21 is also saturated, we can only flag — for now use bt21 where valid
    # Use bt22 where bt21 is NaN (saturated or fill)
    bt_mir = np.where(np.isnan(bt21), bt22, bt21)

    # Background temperature: median of background annulus pixels
    bg_bt = bt_mir[bg_mask]
    bg_bt = bg_bt[~np.isnan(bg_bt)]
    if len(bg_bt) < 10:
        return None  # Not enough background pixels
    t_bg = float(np.median(bg_bt))

    # Anomalous pixels: within ROI and > threshold above background
    roi_bt = bt_mir[roi_mask]
    anomaly_mask_roi = roi_bt > (t_bg + ANOMALY_THRESHOLD_K)
    n_anomalous = int(np.sum(anomaly_mask_roi))

    if n_anomalous == 0:
        vrp_w = 0.0
    else:
        # VRP = sum over anomalous pixels of: A * sigma * (T^4 - T_bg^4)
        t_hot = roi_bt[anomaly_mask_roi]
        vrp_w = float(np.sum(PIXEL_AREA_M2 * SIGMA * (t_hot**4 - t_bg**4)))

    vrp_mw = vrp_w / 1e6
    t_max = float(np.nanmax(roi_bt)) if np.any(~np.isnan(roi_bt)) else float("nan")

    return {
        "vrp_mw": round(vrp_mw, 3),
        "n_anomalous_pixels": n_anomalous,
        "t_bg_k": round(t_bg, 2),
        "t_max_k": round(t_max, 2),
        "sensor": "MODIS_TERRA" if "MOD0" in l1b_path.name else "MODIS_AQUA",
        "granule": l1b_path.name,
        "datetime_utc": _parse_datetime(l1b_path.name),
    }


def _parse_datetime(filename: str) -> str:
    """
    Extract UTC datetime from MODIS filename.
    Example: MOD021KM.A2024074.0000.061.2024074061234.hdf
             -> 2024-03-14 00:00
    """
    try:
        parts = filename.split(".")
        date_part = parts[1]   # e.g. A2024074
        time_part = parts[2]   # e.g. 0000
        year = int(date_part[1:5])
        doy = int(date_part[5:8])
        hour = int(time_part[:2])
        minute = int(time_part[2:4])
        from datetime import datetime
        dt = datetime(year, 1, 1) + __import__("datetime").timedelta(days=doy - 1,
                                                                      hours=hour,
                                                                      minutes=minute)
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return "unknown"
