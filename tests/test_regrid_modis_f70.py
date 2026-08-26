# -*- coding: utf-8 -*-
"""F70.2a — integración del regrid en el procesador MODIS (flag-OFF).

Contrato que fijan estos tests:
  1. El flag `enable_utm_regrid` NO existe activo en el perfil operacional:
     bajo `mirova_equivalent` debe ser False. Mientras sea False, el
     procesador es byte-idéntico al actual (la rama no se ejecuta).
  2. `_regrid_modis_granule` transforma el dict de `read_modis_l1b` al mismo
     schema pero sobre la grilla 51×51 de 1 km — así TODO el código aguas
     abajo (masks, kernels, clustering) corre sin cambios.
  3. El patrón saturación/respaldo de MODIS sobrevive el regrid: band21=NaN
     con band22 válida NO se descarta (es el píxel más caliente del granule).
"""
import numpy as np

import pipeline.profile as vrp_profile
from pipeline.process_modis import _regrid_modis_granule

CLAT, CLON = -36.867210, -71.378241


def _swath(step_deg=0.005, half_deg=0.30):
    lats = np.arange(CLAT - half_deg, CLAT + half_deg, step_deg)
    lons = np.arange(CLON - half_deg, CLON + half_deg, step_deg)
    lon2d, lat2d = np.meshgrid(lons, lats)
    return lat2d, lon2d


def _data(lat2d, lon2d):
    shape = lat2d.shape
    return {
        "band21": np.full(shape, 0.5),
        "band22": np.full(shape, 0.6),
        "band31": np.full(shape, 8.0),
        "lat": lat2d,
        "lon": lon2d,
        "angles": {
            "sensor_zenith_deg": np.full(shape, 12.0),
            "sensor_azimuth_deg": None,          # SDS ausente: debe sobrevivir
            "solar_zenith_deg": np.full(shape, 140.0),
            "solar_azimuth_deg": np.full(shape, 30.0),
        },
    }


def test_flag_apagado_en_el_perfil_operacional():
    """El operacional no cambia hasta el veredicto del A/B F70.3 (A45)."""
    assert vrp_profile.ENABLE_UTM_REGRID is False


def test_schema_preservado_sobre_la_grilla():
    lat2d, lon2d = _swath()
    out = _regrid_modis_granule(_data(lat2d, lon2d), CLAT, CLON)
    assert set(out) == {"band21", "band22", "band31", "lat", "lon", "angles"}
    for k in ("band21", "band22", "band31", "lat", "lon"):
        assert out[k].shape == (51, 51), k
    # los ángulos presentes se regrillan; el ausente sigue ausente
    assert out["angles"]["sensor_zenith_deg"].shape == (51, 51)
    assert out["angles"]["sensor_azimuth_deg"] is None


def test_latlon_son_centros_de_celda():
    lat2d, lon2d = _swath()
    out = _regrid_modis_granule(_data(lat2d, lon2d), CLAT, CLON)
    ci = 51 // 2
    # el centro de la grilla es el volcán (a menos de media celda = 0.5 km)
    assert abs(out["lat"][ci, ci] - CLAT) * 111.32 < 0.5
    # y las distancias crecen hacia el borde (geometría coherente para dist/ROI)
    assert out["lat"][0, ci] > out["lat"][-1, ci]


def test_saturacion_con_respaldo_sobrevive():
    """El píxel MÁS CALIENTE del granule (b21 saturada→NaN) no puede perderse."""
    lat2d, lon2d = _swath()
    d = _data(lat2d, lon2d)
    i, j = np.unravel_index(
        np.argmin((lat2d - CLAT) ** 2 + (lon2d - CLON) ** 2), lat2d.shape)
    d["band21"][i, j] = np.nan         # saturada
    d["band22"][i, j] = 57.0           # respaldo con el valor real
    out = _regrid_modis_granule(d, CLAT, CLON)
    ci = 51 // 2
    centro22 = out["band22"][ci - 1:ci + 2, ci - 1:ci + 2]
    assert np.nanmax(centro22) == 57.0, (
        "el respaldo de la banda 22 debe aterrizar cerca del centro")
    fila, col = np.unravel_index(np.nanargmax(out["band22"]), out["band22"].shape)
    assert np.isnan(out["band21"][fila, col]), (
        "la banda 21 conserva su NaN de saturación en ESA celda")


def test_pixel_sin_tir_no_vale():
    """Sin banda 31 no hay NTI: esa muestra no debe representar a su celda."""
    lat2d = np.array([[CLAT, CLAT + 0.0027]])
    lon2d = np.array([[CLON, CLON]])
    d = {
        "band21": np.array([[9.0, 1.0]]),
        "band22": np.array([[9.0, 1.0]]),
        "band31": np.array([[np.nan, 8.0]]),   # la muestra cercana no tiene TIR
        "lat": lat2d, "lon": lon2d,
        "angles": {"sensor_zenith_deg": None, "sensor_azimuth_deg": None,
                   "solar_zenith_deg": None, "solar_azimuth_deg": None},
    }
    out = _regrid_modis_granule(d, CLAT, CLON)
    ci = 51 // 2
    assert out["band21"][ci, ci] == 1.0, (
        "debe ganar la muestra completa (con TIR), no la más cercana sin TIR")
