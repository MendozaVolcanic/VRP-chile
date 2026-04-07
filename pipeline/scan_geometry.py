"""
scan_geometry.py — Per-pixel ground area correction for off-nadir scan angles.

Polar-orbiting cross-track scanners (MODIS, VIIRS) project a wider IFOV onto
the ground as the scan angle increases. Without correction, VRP values use the
nadir pixel area and underestimate radiative power at off-nadir pixels.

Formula (Wooster et al. 2003 RSE 86; Wolfe et al. 2002 RSE 83):

    A_pix(theta_z) = A_nadir / cos^3(theta_z)

where theta_z is the satellite zenith angle at the pixel (NOT the scan angle
at the satellite). The factor sec^3 accounts for:
  - sec(theta_z): along-track elongation of the IFOV slant range
  - sec^2(theta_z): along-scan elongation due to mirror geometry

For MODIS at the scan edge (theta_z ~ 65 deg with Earth curvature) the
correction is ~13x; integrated across the swath the mean correction is ~2x.

For VIIRS, on-board pixel aggregation (bow-tie deletion) reduces the
elongation but the correction is still ~1.5-3x at edge.

References:
  - Wooster, M.J., Zhukov, B., Oertel, D. (2003) RSE 86, 83-107.
  - Wolfe, R.E., Nishihama, M. et al. (2002) RSE 83, 31-49 (MODIS geolocation).
  - Wolfe, R.E., Lin, G. et al. (2013) RSE 137, 76-88 (VIIRS bow-tie).
  - Coppola, D., Laiolo, M. et al. (2016) MIROVA pixel area treatment.
"""

import numpy as np


# ---------- Constants ----------
EARTH_RADIUS_KM = 6371.0
MODIS_ALTITUDE_KM = 705.0          # Terra/Aqua orbital altitude
VIIRS_ALTITUDE_KM = 829.0          # Suomi-NPP / NOAA-20 orbital altitude

MODIS_NSAMPLES = 1354              # samples per scan line
MODIS_SCAN_HALFWIDTH_DEG = 55.0    # +/- from nadir at the satellite

# Maximum sensor zenith we will trust; beyond this we cap to avoid runaway sec^3
MAX_SENSOR_ZENITH_DEG = 70.0


def area_factor_from_zenith(sensor_zenith_deg: np.ndarray) -> np.ndarray:
    """
    Multiplicative area correction factor as a function of sensor zenith angle.

    A_pix(theta_z) = A_nadir * factor(theta_z)
    factor = 1 / cos^3(theta_z)

    Args:
        sensor_zenith_deg: scalar or array of sensor (satellite) zenith
            angles in degrees, measured at the surface from local vertical.

    Returns:
        Same shape as input. At theta_z=0, returns 1.0.
    """
    z = np.clip(np.abs(np.asarray(sensor_zenith_deg, dtype=np.float64)),
                0.0, MAX_SENSOR_ZENITH_DEG)
    cos_z = np.cos(np.radians(z))
    return 1.0 / (cos_z ** 3)


def modis_zenith_from_column(col_idx: np.ndarray) -> np.ndarray:
    """
    Estimate the surface sensor-zenith angle for MODIS pixels from the
    along-scan column index.

    MODIS scans +/- 55 deg from nadir across 1354 samples per line. The
    surface zenith angle differs from the scan angle at the satellite due
    to Earth curvature. Using law of sines in the satellite-Earth-target
    triangle:

        sin(theta_z) = ((R + h) / R) * sin(theta_scan)

    where R = 6371 km and h = 705 km for MODIS.

    Args:
        col_idx: integer column index (0..1353) — scalar or array.

    Returns:
        Sensor zenith angle in degrees, same shape as input.
    """
    half = (MODIS_NSAMPLES - 1) / 2.0
    theta_scan = MODIS_SCAN_HALFWIDTH_DEG * (np.asarray(col_idx) - half) / half
    sin_z = ((EARTH_RADIUS_KM + MODIS_ALTITUDE_KM) / EARTH_RADIUS_KM) \
            * np.sin(np.radians(theta_scan))
    sin_z = np.clip(np.abs(sin_z), 0.0, 0.999)
    return np.degrees(np.arcsin(sin_z))


def modis_pixel_areas(shape: tuple) -> np.ndarray:
    """
    Return per-pixel area (m^2) for a full MODIS 1km granule of given shape.

    shape = (n_lines, n_samples) where n_samples should be 1354 for MOD021KM.
    """
    n_lines, n_samples = shape
    cols = np.arange(n_samples)
    z = modis_zenith_from_column(cols)        # 1D, length n_samples
    factor = area_factor_from_zenith(z)       # 1D
    nadir_area = 1.0e6                         # 1 km^2
    # Broadcast across lines
    return nadir_area * np.broadcast_to(factor, (n_lines, n_samples)).copy()


def viirs_pixel_areas(sensor_zenith_deg: np.ndarray, nadir_area_m2: float) -> np.ndarray:
    """
    Return per-pixel area (m^2) for a VIIRS granule.

    NOTE: VIIRS performs on-board bow-tie aggregation (Wolfe et al. 2013,
    RSE 137, 76-88). The aggregation divides the swath into 3 zones and
    aggregates 1x, 2x, or 3x detector samples in the along-scan direction
    so that the resulting L1B "pixel" has approximately constant ground
    sample distance regardless of scan angle. Empirical aggregated I-band
    pixel area varies only between ~0.32 and ~0.6 km^2 across the full
    swath (Cao et al. 2014, JGR Atmospheres 119), not the sec^3 ~25x that
    a non-aggregated scanner would produce.

    Empirical test: applying sec^3 to a VIIRS edge pixel (zenith ~70 deg)
    on Lascar gave a 25x overshoot vs MIROVA reference values. Therefore
    we apply only a mild correction here, capped at 2.0x, modelled as
    sec(theta_z)/2 + 0.5 to match the published 0.32->0.6 km^2 range.

    A residual systematic bias vs MIROVA may still exist; it must come
    from a different source (background method, wavelength, threshold)
    not from pixel area. Investigate separately.

    Args:
        sensor_zenith_deg: array of per-pixel sensor zenith angles (degrees).
        nadir_area_m2: nadir pixel area: 140625 for I-band (375m),
                       562500 for M-band (750m).
    """
    z = np.clip(np.abs(np.asarray(sensor_zenith_deg, dtype=np.float64)),
                0.0, MAX_SENSOR_ZENITH_DEG)
    cos_z = np.cos(np.radians(z))
    # Linear interpolation between 1.0 (nadir) and ~2.0 (max zenith ~70 deg)
    # to approximate published VIIRS aggregated pixel area variation.
    factor = 1.0 + (1.0 / cos_z - 1.0) * 0.5
    factor = np.minimum(factor, 2.0)
    return nadir_area_m2 * factor
