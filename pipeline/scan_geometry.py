"""
scan_geometry.py — Per-pixel ground area correction for off-nadir scan angles.

**Nota operacional (S131)**: el pipeline usa área de píxel **nadir-fija** en los tres
sensores (`ENABLE_NADIR_FIXED_PIXEL_AREA_{MODIS,VIIRS}=True`, A66/A67) — las ramas sec³ y
de corrección leve de abajo NO se ejecutan en producción. Lo que sigue describe la
geometría; el estado real lo da `pipeline.profile`. Sobre el sub-reporte con el ángulo que
el área nadir-fija sin remuestreo produce, ver `docs/s131/REMUESTREO_LEY_DE_AREA.md`.

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

import warnings

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
    del vent, en esquina NE del bbox).

    Uso actual (S131): el flag `enable_roi1_box_paper` (OFF, A/B S130 → NO ADOPTAR)
    aplica esta función con `half_km = ROI1_BOX_HALF_KM = 2.5` para la caja 5×5 del
    ROI1 (D18); el ROI exterior sigue siendo el círculo de `radius_km`.

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
    sample distance regardless of scan angle.

    ⚠️ S131: la cifra que seguía acá («~0.32 a ~0.6 km², Cao 2014») está MAL. Contra el
    ATBD de geolocalización VIIRS (423-ATBD-002, Tabla 2.2-1) el HSI de I4 va de
    0.371×0.388 km (nadir) a 0.80×0.789 km (fin de swath): área 0.144 → 0.631 km²,
    **4.38×**. El «approximately 2» del ATBD es POR EJE; el área es el producto. El tope
    de 2.0× de abajo hereda esa lectura y sub-corrige; la rama está muerta en producción
    (nadir_fixed=True). Ver `docs/s131/REMUESTREO_LEY_DE_AREA.md`. Texto original:
    «Empirical aggregated I-band
    pixel area varies only between ~0.32 and ~0.6 km^2 across the full
    swath (Cao et al. 2014, JGR Atmospheres 119), not the sec^3 ~25x that
    a non-aggregated scanner would produce.»

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


def pixel_areas_from_geolocation(lat, lon):
    """Área de cada píxel (m²) MEDIDA en la geolocalización del granule, sin modelo.

    POR QUE. La energia radiante es una radiancia (por unidad de area) multiplicada por el
    area del pixel. Un sensor de barrido que apunta de reojo al borde del swath cubre con
    el mismo detector un pedazo de terreno mucho mas grande que en el nadir, asi que usar
    area nadir en una pasada oblicua sub-reporta la magnitud. S131 midio que ese efecto
    explica el gradiente cenital COMPLETO en VIIRS (razon contra MIROVA 0,77 -> 0,45 sin
    corregir; 0,79-0,87 plana con la ley de area del ATBD).

    POR QUE MEDIRLA Y NO MODELARLA. VIIRS agrega bow-tie a bordo (Wolfe et al. 2013): junta
    3, 2 o 1 muestras del detector segun la zona del swath, de modo que el area da SALTOS en
    dos fronteras en vez de seguir una curva. Cualquier modelo analitico se equivoca en algun
    tramo -el sec^3 de un barredor puro sobre-corrige, y el factor lineal capado a 2,0 de
    `viirs_pixel_areas` sub-corrige, como su propio docstring reconoce contra el ATBD (4,38x
    de nadir a borde). La geolocalizacion no es un modelo: es donde cayo cada pixel. La
    distancia en el terreno entre centros vecinos ES el tamano del pixel, con los saltos de
    agregacion ya adentro y sin suponer nada de la orbita ni del sensor.

    METODO. Para cada pixel se toma la distancia a su vecino en la direccion de barrido y a
    su vecino en la direccion de vuelo, usando diferencias centradas en el interior y
    diferencias hacia adelante/atras en los bordes (nunca extrapolando, para no inventar
    area donde no hay vecino). El area es el producto de las dos.

    Aproximacion asumida, dicha explicitamente: se toma el pixel como un paralelogramo de
    lados iguales a esas dos distancias. Es exacto para una grilla localmente regular y no
    modela el corte real del footprint (que en el borde del swath es un trapecio curvo).
    Para el uso que se le da -escalar la energia radiada- el error de esa aproximacion es
    mucho menor que el 4,38x que se esta corrigiendo.

    Args:
        lat, lon: arrays 2-D de la geolocalizacion del granule, en grados.

    Returns:
        Array de la misma forma, en m^2. Un pixel cuya geolocalizacion (o la de sus vecinos
        usados) venga invalida devuelve NaN a proposito: es preferible un NaN visible a un
        area plausible pero falsa, que se propagaria a la magnitud sin que nadie lo note.
    """
    lat = np.asarray(lat, dtype=np.float64)
    lon = np.asarray(lon, dtype=np.float64)
    if lat.ndim != 2 or lat.shape != lon.shape:
        raise ValueError("lat y lon deben ser arrays 2-D de la misma forma")
    if lat.shape[0] < 2 or lat.shape[1] < 2:
        raise ValueError("hace falta al menos 2x2 pixeles para medir un paso")

    def _paso(eje):
        """Distancia en el terreno al vecino a lo largo de `eje`, por pixel."""
        # Diferencia hacia adelante y hacia atras; en el interior se promedian (diferencia
        # centrada), en los bordes sobrevive la unica que existe.
        a = np.roll(lat, -1, axis=eje), np.roll(lon, -1, axis=eje)
        b = np.roll(lat, 1, axis=eje), np.roll(lon, 1, axis=eje)
        d_fwd = haversine_km(lat, lon, a[0], a[1])
        d_bwd = haversine_km(b[0], b[1], lat, lon)
        # `roll` es circular: el borde toma el extremo opuesto del granule, que no es su
        # vecino. Se invalida y queda la diferencia del lado que si existe.
        sl_fin = [slice(None)] * 2; sl_fin[eje] = -1
        sl_ini = [slice(None)] * 2; sl_ini[eje] = 0
        d_fwd[tuple(sl_fin)] = np.nan
        d_bwd[tuple(sl_ini)] = np.nan
        # Un pixel con ambos lados invalidos (geolocalizacion corrupta) da NaN a proposito;
        # `nanmean` avisa de la rebanada vacia y ese aviso es ruido, no informacion.
        with np.errstate(invalid="ignore"), warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            return np.nanmean(np.stack([d_fwd, d_bwd]), axis=0)

    with np.errstate(invalid="ignore"):
        paso_scan = _paso(1)     # a lo ancho del barrido
        paso_track = _paso(0)    # a lo largo del vuelo
        return paso_scan * paso_track * 1.0e6   # km^2 -> m^2


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
