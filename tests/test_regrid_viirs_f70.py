# -*- coding: utf-8 -*-
"""F70.2b — integración del regrid en los dos procesadores VIIRS (flag-OFF).

Contrato que fijan estos tests, análogo al de MODIS (`test_regrid_modis_f70.py`):
  1. Con `enable_utm_regrid` en False el procesador es idéntico al actual.
  2. `_regrid_viirs_granule` devuelve los dos dicts (`bands`, `geo`) sobre la
     grilla regular, con el mismo schema — así máscaras, kernel 8-vecinos,
     second-pass y clustering corren sin tocarse.
  3. Resolución NATIVA por sensor: la banda I a 375 m (134×134) y la banda M a
     750 m (67×67). Resamplear la banda M a 1 km tiraría resolución real.
  4. Sin TIR no hay NTI: una muestra sin I05/M15 no puede representar su celda.

Trazabilidad — las tres grillas están VERIFICADAS verbatim contra el paper
(S124; el PDF de Campus 2022 se descargó de Europe PMC PMC8914890 y vive en
`documentacion/campus2022_sensors_22_1713.pdf`):

- **banda M y MODIS**, Campus et al. 2022 §3.2: *"Resampling is performed in a
  UTM 51 × 51 km grid, centered on the volcano summit (consistent with
  MODIS-MIROVA images) by keeping the nominal resolution of 750 m. This results
  in matrices of 67 × 67 pixels rather than 51 × 51 pixels obtained from
  MODIS."*
- **banda I**, Campus 2024 (L102-104) da la ventana —*"an initial resampling of
  the original granule in a regular 50×50 km UTM grid"*— pero NO la matriz. Los
  134×134 salen de aplicar el mismo patrón: 134 = 67 × 2, o sea la misma
  ventana de 50,25 km al doble de resolución. Es la única de las tres que se
  deduce en vez de leerse; queda parametrizada.
"""
import math

import numpy as np

import pipeline.profile as vrp_profile
from pipeline.process_viirs import _regrid_viirs_granule
from pipeline.process_viirs_mod import _regrid_viirs_mod_granule

CLAT, CLON = -36.867210, -71.378241


def _swath(step_km=0.375, half_deg=0.30):
    """Malla sintética al paso NATIVO del sensor, en KILÓMETROS.

    Importa que el paso sea el real y en km, no el mismo número de grados en
    lat y lon: a esta latitud un grado de longitud mide 0,80 de uno de latitud,
    así que usar el mismo Δgrados sobre-muestrea en x un 25 % y mete dos
    muestras en algunas celdas. Con eso, el vecino-más-cercano descarta píxeles
    que en un granule real no competirían — ver
    `test_vecino_mas_cercano_puede_descartar_un_pico_sub_celda`.
    """
    sd_lat = step_km / 111.32
    sd_lon = step_km / (111.32 * math.cos(math.radians(CLAT)))
    lats = np.arange(CLAT - half_deg, CLAT + half_deg, sd_lat)
    lons = np.arange(CLON - half_deg, CLON + half_deg, sd_lon)
    lon2d, lat2d = np.meshgrid(lons, lats)
    return lat2d, lon2d


def _geo(lat2d, lon2d):
    shape = lat2d.shape
    return {
        "lat": lat2d,
        "lon": lon2d,
        "sensor_zenith": np.full(shape, 15.0),
        "angles": {
            "sensor_zenith_deg": np.full(shape, 15.0),
            "sensor_azimuth_deg": None,        # SDS ausente: debe sobrevivir
            "solar_zenith_deg": np.full(shape, 145.0),
        },
    }


# ── flag ────────────────────────────────────────────────────────────────────

def test_flag_apagado_en_el_perfil_operacional():
    """El operacional no cambia hasta el veredicto del A/B F70.3 (A45)."""
    assert vrp_profile.ENABLE_UTM_REGRID is False


# ── banda I (375 m) ─────────────────────────────────────────────────────────

def test_iband_grilla_nativa_375m():
    lat2d, lon2d = _swath()
    bands = {"I04": np.full(lat2d.shape, 280.0),
             "I05": np.full(lat2d.shape, 270.0)}
    b, g = _regrid_viirs_granule(bands, _geo(lat2d, lon2d), CLAT, CLON)
    assert b["I04"].shape == (134, 134), "la banda I se regrilla a 375 m"
    assert g["lat"].shape == (134, 134)
    assert g["sensor_zenith"].shape == (134, 134)


def test_iband_schema_y_angulos_ausentes():
    lat2d, lon2d = _swath()
    bands = {"I04": np.full(lat2d.shape, 280.0),
             "I05": np.full(lat2d.shape, 270.0)}
    b, g = _regrid_viirs_granule(bands, _geo(lat2d, lon2d), CLAT, CLON)
    assert set(b) == {"I04", "I05"}
    assert set(g) == {"lat", "lon", "sensor_zenith", "angles"}
    assert g["angles"]["sensor_zenith_deg"].shape == (134, 134)
    assert g["angles"]["sensor_azimuth_deg"] is None


def test_iband_latlon_son_centros_de_celda():
    lat2d, lon2d = _swath()
    bands = {"I04": np.full(lat2d.shape, 280.0),
             "I05": np.full(lat2d.shape, 270.0)}
    _, g = _regrid_viirs_granule(bands, _geo(lat2d, lon2d), CLAT, CLON)
    ci = 134 // 2
    # el centro de la grilla es el volcán, a menos de media celda (0.1875 km)
    assert abs(g["lat"][ci, ci] - CLAT) * 111.32 < 0.19
    assert g["lat"][0, ci] > g["lat"][-1, ci], "Norte arriba"


def test_iband_hot_pixel_aterriza_en_el_centro():
    """El píxel del cráter no puede perderse en el resampleo."""
    lat2d, lon2d = _swath()
    i, j = np.unravel_index(
        np.argmin((lat2d - CLAT) ** 2 + (lon2d - CLON) ** 2), lat2d.shape)
    bands = {"I04": np.full(lat2d.shape, 280.0),
             "I05": np.full(lat2d.shape, 270.0)}
    bands["I04"][i, j] = 340.0
    b, _ = _regrid_viirs_granule(bands, _geo(lat2d, lon2d), CLAT, CLON)
    ci = 134 // 2
    assert np.nanmax(b["I04"][ci - 1:ci + 2, ci - 1:ci + 2]) == 340.0


def test_iband_sin_tir_no_representa_su_celda():
    """Sin I05 no hay NTI: esa muestra no puede ganar la celda."""
    # ambas caen en la celda 67 (que abarca y ∈ [-0.375, 0] km); la que NO
    # trae TIR está justo en el centro de la celda, o sea es la "más cercana":
    # aun así debe perder, porque sin TIR no hay NTI.
    lat2d = np.array([[CLAT - 0.001684, CLAT - 0.000449]])
    lon2d = np.array([[CLON, CLON]])
    bands = {"I04": np.array([[350.0, 275.0]]),
             "I05": np.array([[np.nan, 268.0]])}   # la del centro no trae TIR
    geo = {"lat": lat2d, "lon": lon2d,
           "sensor_zenith": np.full((1, 2), 15.0),
           "angles": {"sensor_zenith_deg": None}}
    b, _ = _regrid_viirs_granule(bands, geo, CLAT, CLON)
    ci = 134 // 2
    assert b["I04"][ci, ci] == 275.0, "gana la muestra completa, no la cercana"


# ── banda M (750 m) ─────────────────────────────────────────────────────────

def test_mband_grilla_nativa_750m():
    """La banda M mantiene sus 750 m: llevarla a 1 km tiraría resolución."""
    lat2d, lon2d = _swath(step_km=0.75)
    bands = {"M13": np.full(lat2d.shape, 4.0),
             "M15": np.full(lat2d.shape, 8.0)}
    b, g = _regrid_viirs_mod_granule(bands, _geo(lat2d, lon2d), CLAT, CLON)
    assert b["M13"].shape == (67, 67)
    assert g["lat"].shape == (67, 67)


def test_mband_preserva_valores():
    """nearest-neighbor no inventa: un campo constante sigue constante."""
    lat2d, lon2d = _swath(step_km=0.75)
    bands = {"M13": np.full(lat2d.shape, 4.25),
             "M15": np.full(lat2d.shape, 8.0)}
    b, _ = _regrid_viirs_mod_granule(bands, _geo(lat2d, lon2d), CLAT, CLON)
    vals = b["M13"][np.isfinite(b["M13"])]
    assert vals.size > 1000
    assert np.allclose(vals, 4.25)


def test_mband_bandas_extra_sobreviven():
    """El lector M puede traer bandas opcionales; no deben perderse."""
    lat2d, lon2d = _swath(step_km=0.75)
    bands = {"M13": np.full(lat2d.shape, 4.0),
             "M15": np.full(lat2d.shape, 8.0),
             "M12": np.full(lat2d.shape, 3.0)}
    b, _ = _regrid_viirs_mod_granule(bands, _geo(lat2d, lon2d), CLAT, CLON)
    assert set(b) == {"M13", "M15", "M12"}
    assert b["M12"].shape == (67, 67)


def test_vecino_mas_cercano_puede_descartar_un_pico_sub_celda():
    """Comportamiento DOCUMENTADO, no deseado: con vecino-más-cercano, si dos
    muestras válidas caen en la misma celda gana la más próxima al centro —
    aunque la otra sea la caliente.

    Por qué se deja así y no se cambia a "máximo": el diseño F70 elige
    nearest-neighbor porque conserva radiancias medidas (un promedio inventaría
    mezclas y rompería el VRP de Wooster), y los papers no publican el
    interpolador. Tomar el máximo sesgaría toda la escena hacia arriba, no solo
    el cráter. El riesgo real es de FALSO NEGATIVO y sólo aparece cuando el
    granule trae varias muestras por celda (bordes de scan, solapamiento de
    barrido); con la resolución nativa ≈ el tamaño de celda es infrecuente.

    Queda como test para que el A/B de F70.3 lo mida en vez de suponerlo: si
    aparecen FN nuevos al prender la grilla, este es el primer sospechoso.
    """
    # dos muestras en la celda central: la fría en el centro, la caliente al borde
    lat2d = np.array([[CLAT - 0.001684, CLAT - 0.000449]])
    lon2d = np.array([[CLON, CLON]])
    bands = {"I04": np.array([[275.0, 340.0]]),      # la CALIENTE es la lejana
             "I05": np.array([[268.0, 268.0]])}
    geo = {"lat": lat2d, "lon": lon2d,
           "sensor_zenith": np.full((1, 2), 15.0),
           "angles": {"sensor_zenith_deg": None}}
    b, _ = _regrid_viirs_granule(bands, geo, CLAT, CLON)
    ci = 134 // 2
    assert b["I04"][ci, ci] == 275.0, (
        "hoy gana la más cercana al centro; si esto cambia, cambió el "
        "interpolador y hay que re-medir los FN")
