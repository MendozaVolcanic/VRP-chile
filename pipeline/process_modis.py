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


SIGMA = 5.670374419e-8
C1 = 1.191042e8
C2 = 14388.0

BAND21_LAMBDA = 3.929
BAND22_LAMBDA = 3.959
PIXEL_AREA_M2 = 1e6       # 1 km^2

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
                  radius_km: float = 15.0) -> dict | None:
    """
    Calculate VRP from MODIS L1B granule.

    geo_path is accepted for API compatibility but not used —
    geolocation is embedded in MOD021KM.

    Returns dict or None if granule does not cover volcano.
    """
    data = read_modis_l1b(hdf_path)

    lat = data["lat"]
    lon = data["lon"]
    dist = haversine_km(volcano_lat, volcano_lon, lat, lon)

    roi_mask = dist <= radius_km
    bg_mask = (dist >= BG_INNER_KM) & (dist <= BG_OUTER_KM)

    if not np.any(roi_mask):
        return None

    # Merge bands: use Band 21 primary, Band 22 where 21 is NaN (saturated)
    bt21 = radiance_to_bt(data["band21"], BAND21_LAMBDA)
    bt22 = radiance_to_bt(data["band22"], BAND22_LAMBDA)
    bt_mir = np.where(np.isnan(bt21), bt22, bt21)

    bg_vals = bt_mir[bg_mask & ~np.isnan(bt_mir)]
    if len(bg_vals) < 10:
        return None

    t_bg = float(np.median(bg_vals))
    std_bg = float(np.std(bg_vals))
    threshold = max(ANOMALY_THRESHOLD_K, N_SIGMA * std_bg)

    roi_bt = bt_mir[roi_mask]
    hotpix = roi_bt[roi_bt > (t_bg + threshold)]
    hotpix = hotpix[~np.isnan(hotpix)]
    n_anomalous = len(hotpix)

    vrp_mw = 0.0
    if n_anomalous > 0:
        vrp_w = float(np.sum(PIXEL_AREA_M2 * SIGMA * (hotpix ** 4 - t_bg ** 4)))
        vrp_mw = vrp_w / 1e6

    valid_roi = roi_bt[~np.isnan(roi_bt)]
    t_max = float(np.max(valid_roi)) if len(valid_roi) else float("nan")

    return {
        "vrp_mw": round(vrp_mw, 3),
        "n_anomalous_pixels": n_anomalous,
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
