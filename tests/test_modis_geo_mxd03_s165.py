# -*- coding: utf-8 -*-
"""S165: piezas de los tres flags MxD03 de MODIS, sin HDF (plan 2026-10-25-flag-mxd03-modis, Tareas 2, 3 y 5).

POR QUÉ. El pipeline estira la grilla de 5 km de geolocalización suponiendo que cada muestra está en el píxel 5i cuando
está en el 5i+2, y el cráter queda corrido 1 a 3 km hacia el nadir (A61 H2). El MxD03, que el pipeline ya baja, trae la
posición de cada píxel. Con esa posición aparecen dos defectos que el mismo paquete arregla: una pasada sin cráter
(relleno o borde del gránulo) se guardaba como negativo (A61 H1, VA61-01), y la etiqueta summit/far medía desde el
centro del volcán y no desde el cráter (A61 H5). Aquí se prueba cada pieza por separado; el cableado de punta a punta
lo prueba tests/test_guard_mxd03_flags_s165.py.
"""
import numpy as np
import pytest
from unittest.mock import patch

import pipeline.process_modis as pm


# ------------------------------------------------------------------------------------------------ Tarea 2
def test_leer_mxd03_usa_el_lector_de_la_via_codigo_mirova():
    """Un solo lector del MxD03 en el repo (A102): el de la vía «código MIROVA», que ya limpia el relleno."""
    from pipeline import mirova_v750_codigo as MV
    lat = np.array([[-23.0, np.nan]]), np.array([[-67.0, np.nan]])
    with patch.object(MV, "leer_geo_mxd03", lambda ruta: (lat[0], lat[1], {"sensor_zenith": None})):
        la, lo = pm.leer_mxd03("geo.hdf")
    assert la is lat[0] and lo is lat[1]


def test_posicion_con_flag_es_mxd03():
    datos = {"lat": np.zeros((4, 4), np.float32), "lon": np.zeros((4, 4), np.float32)}
    mxd = (np.full((4, 4), -23.0, np.float32), np.full((4, 4), -67.0, np.float32))
    with patch.object(pm, "ENABLE_MODIS_GEO_MXD03", True), patch.object(pm, "leer_mxd03", lambda _p: mxd):
        lat, lon, fuente = pm.posicion_de_calculo(datos, "geo.hdf")
    assert fuente == "mxd03" and lat is mxd[0] and lon is mxd[1]


def test_posicion_mxd03_queda_en_float32_como_el_brazo_x():
    datos = {"lat": np.zeros((2, 2), np.float32), "lon": np.zeros((2, 2), np.float32)}
    mxd = (np.full((2, 2), -23.123456, np.float64), np.full((2, 2), -67.0, np.float64))
    with patch.object(pm, "ENABLE_MODIS_GEO_MXD03", True), patch.object(pm, "leer_mxd03", lambda _p: mxd):
        lat, lon, fuente = pm.posicion_de_calculo(datos, "geo.hdf")
    assert lat.dtype == np.float32 and lon.dtype == np.float32
    assert lat[0, 0] == np.float32(-23.123456)


def test_posicion_sin_flag_es_la_de_siempre_y_no_lee_el_mxd03():
    datos = {"lat": np.ones((4, 4), np.float32), "lon": np.ones((4, 4), np.float32)}
    with patch.object(pm, "leer_mxd03", lambda _p: (_ for _ in ()).throw(AssertionError("leyó el MxD03"))):
        lat, lon, fuente = pm.posicion_de_calculo(datos, "geo.hdf")
    assert fuente == "interp_5km" and lat is datos["lat"] and lon is datos["lon"]


def test_mxd03_que_no_calza_cae_a_la_interpolada_y_lo_dice():
    datos = {"lat": np.ones((4, 4), np.float32), "lon": np.ones((4, 4), np.float32)}
    malo = (np.zeros((3, 3), np.float32), np.zeros((3, 3), np.float32))
    with patch.object(pm, "ENABLE_MODIS_GEO_MXD03", True), patch.object(pm, "leer_mxd03", lambda _p: malo):
        lat, lon, fuente = pm.posicion_de_calculo(datos, "geo.hdf")
    assert fuente == "interp_5km_mxd03_no_calza" and lat is datos["lat"]


@pytest.mark.parametrize("geo_path", [None, "geo.hdf"])
def test_mxd03_ilegible_o_ausente_cae_a_la_interpolada_y_lo_dice(geo_path):
    datos = {"lat": np.ones((4, 4), np.float32), "lon": np.ones((4, 4), np.float32)}

    def falla(_p):
        raise OSError("HDF roto")

    with patch.object(pm, "ENABLE_MODIS_GEO_MXD03", True), patch.object(pm, "leer_mxd03", falla):
        lat, lon, fuente = pm.posicion_de_calculo(datos, geo_path)
    assert fuente == "interp_5km_mxd03_ilegible" and lat is datos["lat"]


# ------------------------------------------------------------------------------------------------ Tarea 3
def _grilla(n=9):
    i = np.arange(n)
    lat, lon = np.meshgrid(-23.0 - i * 0.009, -67.0 + i * 0.0098, indexing="ij")
    return lat.astype(np.float32), lon.astype(np.float32)


def test_crater_cubierto_en_el_interior():
    lat, lon = _grilla()
    assert pm.crater_cubierto(lat, lon, float(lat[4, 4]), float(lon[4, 4])) is True


def test_crater_en_un_bloque_de_relleno_no_esta_cubierto():
    lat, lon = _grilla()
    lat[3:6, :], lon[3:6, :] = np.nan, np.nan
    assert pm.crater_cubierto(lat, lon, -23.036, -66.9608) is False


@pytest.mark.parametrize("i,j", [(0, 4), (8, 4), (4, 0), (4, 8)])
def test_crater_en_la_primera_o_ultima_linea_o_frame_no_esta_cubierto(i, j):
    lat, lon = _grilla()
    assert pm.crater_cubierto(lat, lon, float(lat[i, j]), float(lon[i, j])) is False


def test_crater_sin_ninguna_posicion_no_esta_cubierto():
    lat, lon = _grilla()
    lat[:], lon[:] = np.nan, np.nan
    assert pm.crater_cubierto(lat, lon, -23.0, -67.0) is False


def test_vecino_sin_posicion_basta_para_sin_dato():
    lat, lon = _grilla()
    lat[3, 5] = np.nan
    assert pm.crater_cubierto(lat, lon, float(lat[4, 4]), float(lon[4, 4])) is False


def test_sin_dato_solo_con_mxd03_y_con_el_flag():
    lat, lon = _grilla()
    with patch.object(pm, "ENABLE_MODIS_CRATER_SIN_DATO", True), patch.object(pm, "crater_cubierto", lambda *a: False):
        assert pm.sin_dato_de_geolocalizacion(lat, lon, -23.0, -67.0, "mxd03") is True
        for fuente in ("interp_5km", "interp_5km_mxd03_no_calza", "interp_5km_mxd03_ilegible"):
            assert pm.sin_dato_de_geolocalizacion(lat, lon, -23.0, -67.0, fuente) is False
    with patch.object(pm, "crater_cubierto", lambda *a: False):
        assert pm.sin_dato_de_geolocalizacion(lat, lon, -23.0, -67.0, "mxd03") is False


# ------------------------------------------------------------------------------------------------ Tarea 5
def test_dist_de_etiqueta_desde_el_crater_con_flag():
    dist_centro = np.array([[5.05]])
    dist_crater = np.array([[4.40]])
    with patch.object(pm, "ENABLE_MODIS_DIST_DESDE_CRATER", True):
        assert pm.dist_de_etiqueta(dist_centro, dist_crater) is dist_crater
    assert pm.dist_de_etiqueta(dist_centro, dist_crater) is dist_centro
