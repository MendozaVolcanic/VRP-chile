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


def haversine_km(lat1: float, lon1: float,
                 lat2: np.ndarray, lon2: np.ndarray) -> np.ndarray:
    """Vectorized haversine distance (km) from scalar point to array.

    S23 Task 2: centralized here (was duplicated in process_modis/viirs/viirs_mod).

    Args:
        lat1, lon1: scalar floats (volcano center).
        lat2, lon2: numpy arrays (per-pixel grids).

    Returns:
        Array same shape as lat2/lon2, distance in km. NaN propagates.

    Raises:
        TypeError: si lat1 o lon1 es None (defensa: antes silenciosamente
            propagaba np.radians(None) → ValueError críptico).
    """
    if lat1 is None or lon1 is None:
        raise TypeError(
            f"haversine_km: lat1/lon1 cannot be None (got lat1={lat1}, "
            f"lon1={lon1}). Check volcano YAML config has lat/lon set."
        )
    R = EARTH_RADIUS_KM
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = (np.sin(dlat / 2) ** 2
         + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2))
         * np.sin(dlon / 2) ** 2)
    return R * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))

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


def modis_pixel_areas(shape: tuple, nadir_fixed: bool = False) -> np.ndarray:
    """
    Return per-pixel area (m^2) for a full MODIS 1km granule of given shape.

    shape = (n_lines, n_samples) where n_samples should be 1354 for MOD021KM.

    Args:
        shape: granule shape (n_lines, n_samples).
        nadir_fixed: si True, retorna A_pix uniforme = 1 km^2 (1e6 m^2) para
            todas las pixels. Corresponde a la definición de Coppola 2016a
            SP426.5 línea 201-202 + Eq.7: "A_PIX is the pixel size (1 km^2
            for the resampled MODIS pixels)". MIROVA resamplea a grid UTM
            50x50 km de 1km uniforme antes de aplicar VRP. Default False
            preserva el factor sec^3(theta_z) histórico (Drift #7 S46).
    """
    n_lines, n_samples = shape
    if nadir_fixed:
        return np.full((n_lines, n_samples), 1.0e6, dtype=np.float64)
    cols = np.arange(n_samples)
    z = modis_zenith_from_column(cols)        # 1D, length n_samples
    factor = area_factor_from_zenith(z)       # 1D
    nadir_area = 1.0e6                         # 1 km^2
    # Broadcast across lines
    return nadir_area * np.broadcast_to(factor, (n_lines, n_samples)).copy()


def roi_mask_bbox(
    lat: np.ndarray,
    lon: np.ndarray,
    center_lat: float,
    center_lon: float,
    half_km: float,
) -> np.ndarray:
    """Bbox cuadrado de ``half_km`` por lado en cada eje centrado en
    (center_lat, center_lon). Es la geometria que MIROVA usa en sus KMZ
    GroundOverlay (bbox 50x50 km confirmado S15 2026-04-22), en lugar
    del circulo inscrito que usabamos con ``dist <= radius_km``.

    Diferencia fisica: un circulo radio 25 km tiene area 1963 km^2; un
    bbox 50x50 (half=25) tiene 2500 km^2 — 27% mas, las esquinas diagonales.
    MIROVA publica detecciones en esas esquinas (Llaima Conguillio a 28 km
    del vent, en esquina NE del bbox). Cambiar a bbox recupera esas refs.

    Args:
        lat, lon: arrays 2D de latitud/longitud per-pixel (grados).
        center_lat, center_lon: centro del volcan (usar vent o mirova_center).
        half_km: medio lado del bbox en km (=radius_km del volcano).

    Returns:
        bool array mismo shape que lat, True dentro del bbox.
    """
    lat_span_km = (lat - center_lat) * 111.0
    lon_span_km = (lon - center_lon) * 111.0 * np.cos(np.radians(center_lat))
    return (np.abs(lat_span_km) <= half_km) & (np.abs(lon_span_km) <= half_km)


def viirs_pixel_areas(
    sensor_zenith_deg: np.ndarray,
    nadir_area_m2: float,
    nadir_fixed: bool = False,
) -> np.ndarray:
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
        nadir_fixed: si True, retorna A_pix uniforme = nadir_area_m2 para
            todas las pixels (Coppola 2016a SP426.5 Eq.7 + CLAUDE.md regla:
            MIROVA usa A_pix nadir-fijo en los 3 sensores). Default False
            preserva el factor lineal 1-2x calibrado empíricamente S14
            (Drift #7 S46, ver CLAUDE.md).
    """
    z = np.clip(np.abs(np.asarray(sensor_zenith_deg, dtype=np.float64)),
                0.0, MAX_SENSOR_ZENITH_DEG)
    if nadir_fixed:
        return np.full_like(z, nadir_area_m2, dtype=np.float64)
    cos_z = np.cos(np.radians(z))
    # Linear interpolation between 1.0 (nadir) and ~2.0 (max zenith ~70 deg)
    # to approximate published VIIRS aggregated pixel area variation.
    factor = 1.0 + (1.0 / cos_z - 1.0) * 0.5
    factor = np.minimum(factor, 2.0)
    return nadir_area_m2 * factor


# ════════════════════════════════════════════════════════════════════
# S122 — Geometría de observación persistida por record (research use).
# POR QUÉ: el ángulo de visión condiciona lo que el sensor "ve" del cráter.
# Un píxel muy oblicuo (zenith alto) es más grande y más elongado en el
# terreno, promedia más superficie fría alrededor del foco y atraviesa más
# atmósfera → una misma anomalía puede leerse más débil. El azimut solar y
# el zenith solar permiten además separar efectos de iluminación/sombra de
# ladera. NO participan de la detección ni de la magnitud (el pipeline usa
# A_pix nadir-fijo, A66/A67); se persisten para estudiarlos después.
# ════════════════════════════════════════════════════════════════════

OBSERVATION_ANGLE_KEYS = (
    "sensor_zenith_deg",
    "sensor_azimuth_deg",
    "solar_zenith_deg",
    "solar_azimuth_deg",
)


def observation_geometry(lat, lon, angles: dict,
                         target_lat: float, target_lon: float) -> dict:
    """Ángulos de observación en el píxel más cercano a (target_lat, target_lon).

    Args:
        lat, lon: arrays 2-D de geolocalización de la escena.
        angles: dict con cualquier subconjunto de OBSERVATION_ANGLE_KEYS →
            array 2-D de la misma forma que lat/lon (o None si el producto
            no lo trae).
        target_lat, target_lon: punto de interés (hotspot final o cráter).

    Returns:
        dict con las claves de OBSERVATION_ANGLE_KEYS presentes y resolubles,
        redondeadas a 2 decimales; None en las que no se puedan resolver.
        Defensivo: nunca lanza — ante cualquier problema devuelve None por clave.
    """
    out = {k: None for k in OBSERVATION_ANGLE_KEYS}
    if target_lat is None or target_lon is None or not angles:
        return out
    try:
        la = np.asarray(lat, dtype=np.float64)
        lo = np.asarray(lon, dtype=np.float64)
        if la.shape != lo.shape or la.size == 0:
            return out
        # Distancia euclídea en grados: suficiente para elegir el píxel más
        # cercano dentro de una escena (no es una medida de distancia real).
        d2 = (la - float(target_lat)) ** 2 + (lo - float(target_lon)) ** 2
        if not np.any(np.isfinite(d2)):
            return out
        idx = np.unravel_index(np.nanargmin(d2), la.shape)
    except Exception:
        return out
    for key in OBSERVATION_ANGLE_KEYS:
        arr = angles.get(key)
        if arr is None:
            continue
        try:
            a = np.asarray(arr, dtype=np.float64)
            if a.shape != la.shape:
                continue
            v = float(a[idx])
            if np.isfinite(v):
                out[key] = round(v, 2)
        except Exception:
            continue
    return out


def attr_scale_factor(attrs, key: str = "scale_factor", default: float = 1.0) -> float:
    """Extrae un scale_factor de atributos HDF5/HDF4 de forma robusta.

    POR QUÉ existe: h5py devuelve los atributos como arrays de numpy
    (`array([0.01], dtype=float32)`), y en numpy >=2.0 `float()` sobre un array
    de 1 elemento con ndim>0 lanza TypeError. Un try/except alrededor de eso
    convierte silenciosamente el ángulo en None (bug S122, detectado por el
    piloto real: VIIRS quedó sin geometría). pyhdf en cambio devuelve floats.
    """
    try:
        raw = attrs.get(key, default)
    except Exception:
        return float(default)
    try:
        arr = np.asarray(raw).ravel()
        if arr.size == 0:
            return float(default)
        val = float(arr[0])
        return val if np.isfinite(val) and val != 0.0 else float(default)
    except Exception:
        return float(default)
