# -*- coding: utf-8 -*-
"""F70.1 — tests del módulo de regrillado UTM (pipeline/regrid.py).

Por qué existe este módulo: MIROVA no trabaja sobre la imagen cruda del
satélite. Antes de detectar nada, recorta y resamplea cada escena a una grilla
regular de 1 km (50×50 km UTM centrada en la cumbre) porque su esquema de
detección "requires homogenous pixel scale" (Coppola 2016a ~L150-165; Campus
2024 L102-104 para VIIRS). Nosotros veníamos computando sobre el swath crudo,
donde un píxel off-nadir se estira hasta ~10 km² y "los 8 vecinos" son objetos
geométricamente distintos en cada pasada. Diseño completo:
docs/superpowers/specs/2026-08-25-grilla-utm-kernel-global-design.md

Estos tests son sintéticos (sin HDF real): construyen swaths de lat/lon
conocidos y verifican que cada valor aterriza en la celda que corresponde.
"""
import numpy as np
import pytest

from pipeline.regrid import regrid_to_utm

# Cráter de referencia para los tests (Nicanor, NdC — da igual cuál sea,
# solo importa que la geometría sea autoconsistente).
CLAT, CLON = -36.867210, -71.378241


def _swath_regular(step_deg=0.005, half_deg=0.30):
    """Swath sintético: malla regular de lat/lon centrada en el cráter.

    step 0.005° ≈ 550 m N-S: más fino que la celda de 1 km, así cada celda
    de la grilla recibe al menos una muestra dentro del área cubierta.
    """
    lats = np.arange(CLAT - half_deg, CLAT + half_deg, step_deg)
    lons = np.arange(CLON - half_deg, CLON + half_deg, step_deg)
    lon2d, lat2d = np.meshgrid(lons, lats)
    return lat2d, lon2d


def test_forma_y_tipo_de_la_grilla():
    """51×51 celdas de 1 km para half=25.5 km (grilla MIROVA MODIS)."""
    lat2d, lon2d = _swath_regular()
    rad = np.full(lat2d.shape, 5.0)
    out = regrid_to_utm(lat2d, lon2d, {"mir": rad}, CLAT, CLON,
                        cell_km=1.0, half_km=25.5)
    assert out["mir"].shape == (51, 51)
    assert out["suitable"].shape == (51, 51)
    assert out["mir"].dtype == np.float64


def test_valor_uniforme_se_preserva():
    """Un campo constante debe seguir constante: el regrid no inventa valores."""
    lat2d, lon2d = _swath_regular()
    rad = np.full(lat2d.shape, 7.25)
    out = regrid_to_utm(lat2d, lon2d, {"mir": rad}, CLAT, CLON,
                        cell_km=1.0, half_km=25.5)
    vals = out["mir"][out["suitable"]]
    assert vals.size > 2000, "la malla sintética debe cubrir casi toda la grilla"
    assert np.allclose(vals, 7.25), "nearest-neighbor no debe alterar valores"


def test_pixel_caliente_aterriza_en_la_celda_central():
    """Un hot pixel EN el cráter debe caer en la celda del centro de la grilla."""
    lat2d, lon2d = _swath_regular()
    rad = np.full(lat2d.shape, 1.0)
    # el punto del swath más cercano al cráter se calienta
    i, j = np.unravel_index(
        np.argmin((lat2d - CLAT) ** 2 + (lon2d - CLON) ** 2), lat2d.shape)
    rad[i, j] = 99.0
    out = regrid_to_utm(lat2d, lon2d, {"mir": rad}, CLAT, CLON,
                        cell_km=1.0, half_km=25.5)
    ci = out["mir"].shape[0] // 2
    centro = out["mir"][ci - 1:ci + 2, ci - 1:ci + 2]
    assert np.nanmax(centro) == 99.0, (
        "el hot pixel del cráter debe aterrizar en la celda central (±1 por "
        "el desfase swath-vs-celda)")
    assert np.nanmax(out["mir"]) == 99.0, "el valor caliente no debe perderse"


def test_duplicados_gana_el_mas_cercano_al_centro_de_celda():
    """Si dos muestras caen en la misma celda, queda la más cercana al centro.

    Es la decisión documentada del diseño: nearest-neighbor conserva
    radiancias reales (promediar inventaría mezclas que el sensor no midió).
    """
    # dos puntos: uno casi exacto al cráter, otro a ~300 m (misma celda de 1 km)
    lat2d = np.array([[CLAT, CLAT + 0.0027]])
    lon2d = np.array([[CLON, CLON]])
    rad = np.array([[50.0, 10.0]])
    out = regrid_to_utm(lat2d, lon2d, {"mir": rad}, CLAT, CLON,
                        cell_km=1.0, half_km=25.5)
    ci = out["mir"].shape[0] // 2
    assert out["mir"][ci, ci] == 50.0, (
        "debe ganar la muestra más cercana al centro de la celda")


def test_celdas_sin_muestra_quedan_nan_y_no_suitable():
    """Cobertura parcial honesta: sin muestra → NaN, no relleno (diseño §4)."""
    # swath chico que solo cubre el cuadrante NE de la grilla
    lats = np.arange(CLAT + 0.02, CLAT + 0.20, 0.005)
    lons = np.arange(CLON + 0.02, CLON + 0.20, 0.005)
    lon2d, lat2d = np.meshgrid(lons, lats)
    rad = np.full(lat2d.shape, 3.0)
    out = regrid_to_utm(lat2d, lon2d, {"mir": rad}, CLAT, CLON,
                        cell_km=1.0, half_km=25.5)
    assert np.isnan(out["mir"][~out["suitable"]]).all()
    assert 0 < out["suitable"].sum() < out["suitable"].size, (
        "cobertura parcial: ni vacía ni completa")
    # el cuadrante SW (sin datos) debe estar completamente no-suitable
    assert not out["suitable"][40:, :10].any()


def test_multiples_bandas_comparten_geometria():
    """MIR y TIR del mismo swath deben aterrizar en las MISMAS celdas."""
    lat2d, lon2d = _swath_regular()
    mir = np.full(lat2d.shape, 2.0)
    tir = np.full(lat2d.shape, 9.0)
    out = regrid_to_utm(lat2d, lon2d, {"mir": mir, "tir": tir}, CLAT, CLON,
                        cell_km=1.0, half_km=25.5)
    assert (np.isnan(out["mir"]) == np.isnan(out["tir"])).all(), (
        "una celda con MIR pero sin TIR rompería el NTI aguas abajo")


def test_nan_de_entrada_no_gana_la_celda():
    """Un NaN del swath (píxel inválido) no debe desplazar a un valor real."""
    lat2d = np.array([[CLAT, CLAT + 0.0027]])
    lon2d = np.array([[CLON, CLON]])
    rad = np.array([[np.nan, 10.0]])
    out = regrid_to_utm(lat2d, lon2d, {"mir": rad}, CLAT, CLON,
                        cell_km=1.0, half_km=25.5)
    ci = out["mir"].shape[0] // 2
    assert out["mir"][ci, ci] == 10.0, (
        "el NaN estaba más cerca del centro, pero un inválido nunca gana")


def test_area_de_celda_es_constante():
    """El punto de todo esto: área homogénea. La grilla lo da por construcción."""
    lat2d, lon2d = _swath_regular()
    out = regrid_to_utm(lat2d, lon2d, {"mir": np.ones(lat2d.shape)},
                        CLAT, CLON, cell_km=1.0, half_km=25.5)
    assert out["cell_area_km2"] == pytest.approx(1.0)


def test_grilla_viirs375():
    """Resolución I-band: celda de 375 m (Campus 2024, grilla UTM 50×50 km)."""
    lat2d, lon2d = _swath_regular(step_deg=0.002)
    out = regrid_to_utm(lat2d, lon2d, {"mir": np.ones(lat2d.shape)},
                        CLAT, CLON, cell_km=0.375, half_km=25.125)
    assert out["mir"].shape == (134, 134)
    assert out["cell_area_km2"] == pytest.approx(0.375 ** 2)
