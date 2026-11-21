# -*- coding: utf-8 -*-
"""S192, falla «No points given» de la vía «código MIROVA» (run 44768057665, trozo 28 de la tanda 7 de la historia
de los 34: MOD021KM.A2026213.0300 sobre Mentolat, MacaCay y Hudson).

POR QUÉ (el fenómeno primero). Un gránulo puede traer posición para todos los píxeles alrededor del volcán y ninguna
radiancia utilizable: el MxD03 (o el GEO de VIIRS) se calcula de la órbita y la actitud, que siempre existen, mientras
que la radiancia del L1B puede faltar en escaneos enteros (pérdida de datos en la transmisión, o DN de relleno). El
filtro de cobertura de `calcular_vrp_granulo` cuenta píxeles con posición (>= 100 en el recorte de 45 km), pero la
interpolación a la grilla de MIROVA (`remuestrear_grilla`) usa sólo los píxeles con radiancia finita. Con menos de tres
la triangulación no existe y scipy lanza `ValueError: No points given` (cero puntos) o un error de Qhull (uno o dos).
`run_pipeline` atrapa la excepción, la pasada queda sin record y `scripts/revisar_errores_modis_nrt.py` deja el job en
rojo; en el NRT se repetiría en cada corrida mientras el gránulo siga en la ventana de 8 días.

Qué se exige: esa escena se guarda vacía (0 MW, sin píxeles), con `diag_codigo_mirova.motivo_vacio` =
"sin_radiancia_valida", y el número de píxeles con radiancia válida de cada banda en el recorte. Es la misma clase de
escena que la vía ya guarda vacía cuando la mitad o más de la grilla queda sin dato (`escena_invalida`, ficha v1.27):
el tablero no la cuenta como pasada. Controles: el gránulo sano sigue dando record sin las claves nuevas, y con tres o
más píxeles válidos el camino de siempre no cambia (la marca no se enciende).

Las aserciones leen con `.get` para que una marca ausente falle por aserción y no por excepción (S152). Gránulo
sintético: el de tests/test_via_dato_faltante_crater_s190.py (malla con leve desorden, fondo 268 K, valores
ilustrativos, no instrumentales).
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest

from pipeline import mirova_v750_codigo as MV

VOLC = "Villarrica"
V_LAT, V_LON = -39.42, -71.93          # volcanoes.yaml, Villarrica (volcan_por_coordenadas exige igualdad)
INNER_KM = 5.0
FAMILIAS = ("MODIS", "VIIRS750", "VIIRS375")
SENSOR = {"MODIS": "MODIS_TERRA", "VIIRS750": "VIIRS_NOAA20_750", "VIIRS375": "VIIRS_NOAA20"}
PASO_NATIVO_KM = {"MODIS": 1.0, "VIIRS750": 0.75, "VIIRS375": 0.375}


def _granulo(familia, semilla=192):
    """Gránulo sintético de ±41 km alrededor del cráter (cubre el recorte de 45 km de la grilla)."""
    paso = PASO_NATIVO_KM[familia]
    n = 2 * int(round(41.0 / paso)) + 1
    c = n // 2
    rng = np.random.default_rng(semilla)
    fil, col = np.indices((n, n))
    yn = (c - fil) * paso + rng.normal(0, 0.05 * paso, (n, n))
    xe = (col - c) * paso + rng.normal(0, 0.05 * paso, (n, n))
    lat = V_LAT + yn / 111.32
    lon = V_LON + xe / (111.32 * math.cos(math.radians(V_LAT)))
    cfg = MV.FAMILIAS[familia]
    t = 268.0 + rng.normal(0, 0.4, (n, n))
    b_mir, b_tir = cfg["bandas"]
    rad = {b_mir: MV.temperatura_a_radiancia(t, cfg["lam_mir"]),
           b_tir: MV.temperatura_a_radiancia(t - 3.0, cfg["lam_tir"])}
    ang = {"sensor_zenith": np.full((n, n), 20.0), "solar_zenith": np.full((n, n), 120.0),
           "sensor_azimuth": np.full((n, n), -100.0), "solar_azimuth": np.full((n, n), 50.0)}
    return {"rad": rad, "lat": lat, "lon": lon, "ang": ang, "b_mir": b_mir, "b_tir": b_tir, "c": c}


def _correr(gr, familia):
    return MV.calcular_vrp_granulo(gr["rad"], gr["lat"], gr["lon"], gr["ang"], VOLC, V_LAT, V_LON, INNER_KM,
                                   SENSOR[familia], familia=familia)


def _dejar_validos(gr, banda, k):
    """Deja sólo k píxeles con radiancia finita en `banda`, junto al centro y no colineales; el resto NaN."""
    a = gr["rad"][banda]
    c = gr["c"]
    keep = np.zeros(a.shape, bool)
    for i in range(k):
        keep[c + (i % 2), c + i] = True     # no colineales con k = 3: (c,c), (c+1,c+1), (c,c+2)
    a[~keep] = np.nan


def _assert_vacia(rec, n_mir, n_tir):
    assert rec is not None, "la escena sin radiancia debe guardarse vacía, no descartarse"
    d = rec.get("diag_codigo_mirova") or {}
    assert d.get("motivo_vacio") == "sin_radiancia_valida", d.get("motivo_vacio")
    assert rec.get("vrp_mw") == 0.0
    assert rec.get("n_anomalous_pixels") == 0
    assert rec.get("anomaly_pixels") == []
    assert rec.get("primary_cluster") is None
    assert rec.get("via_codigo_mirova") is True
    assert d.get("px_radiancia_valida") == {"mir": n_mir, "tir": n_tir}, d.get("px_radiancia_valida")


@pytest.mark.parametrize("familia", FAMILIAS)
@pytest.mark.parametrize("banda", ("mir", "tir"))
def test_banda_sin_ningun_valido_da_escena_vacia(familia, banda):
    """El caso del run 44768057665: posición en todo el recorte, radiancia en ninguno (cero puntos para griddata)."""
    gr = _granulo(familia)
    b = gr["b_mir"] if banda == "mir" else gr["b_tir"]
    n_total = int(np.isfinite(gr["rad"][gr["b_tir"] if banda == "mir" else gr["b_mir"]]).sum())
    gr["rad"][b][:] = np.nan
    rec = _correr(gr, familia)
    # la otra banda queda entera: se cuentan sus píxeles en el recorte, no en todo el gránulo
    d = (rec or {}).get("diag_codigo_mirova") or {}
    otra = (d.get("px_radiancia_valida") or {}).get("tir" if banda == "mir" else "mir")
    assert otra is not None and 100 <= otra <= n_total
    _assert_vacia(rec, 0 if banda == "mir" else otra, 0 if banda == "tir" else otra)


@pytest.mark.parametrize("familia", FAMILIAS)
def test_uno_o_dos_validos_da_escena_vacia(familia):
    """Con uno o dos puntos tampoco hay triangulación (Qhull): misma escena vacía, no excepción."""
    for k in (1, 2):
        gr = _granulo(familia)
        _dejar_validos(gr, gr["b_mir"], k)
        _dejar_validos(gr, gr["b_tir"], k)
        _assert_vacia(_correr(gr, familia), k, k)


@pytest.mark.parametrize("familia", FAMILIAS)
def test_tres_validos_sigue_el_camino_de_siempre(familia):
    """Control del umbral: con tres puntos no colineales griddata corre y la grilla queda casi toda sin dato; la
    escena sale `escena_invalida` por la regla de media escena del .m, como antes del cambio (sin marca nueva)."""
    gr = _granulo(familia)
    _dejar_validos(gr, gr["b_mir"], 3)
    _dejar_validos(gr, gr["b_tir"], 3)
    rec = _correr(gr, familia)
    d = rec["diag_codigo_mirova"]
    assert d.get("motivo_vacio") == "escena_invalida"
    assert "px_radiancia_valida" not in d


@pytest.mark.parametrize("familia", FAMILIAS)
def test_granulo_sano_sin_marca(familia):
    """Control: el gránulo sano no lleva la marca ni el motivo nuevo."""
    rec = _correr(_granulo(familia), familia)
    d = rec["diag_codigo_mirova"]
    assert d.get("motivo_vacio") != "sin_radiancia_valida"
    assert "px_radiancia_valida" not in d


def test_sin_posicion_suficiente_sigue_siendo_none():
    """Control: el filtro de cobertura no cambia (menos de 100 píxeles con posición: el volcán no está en el
    gránulo y no se escribe record)."""
    gr = _granulo("MODIS")
    gr["lat"][:] = np.nan
    assert _correr(gr, "MODIS") is None


# ------------------------------------------------------------------------------------- recortes reales del gránulo
# MOD021KM.A2026213.0300.061.2026216005223.hdf con su MOD03, bajados por experiments/_s192_no_points/diag_granulo.py
# (evidencia en experiments/_s192_no_points/diag_s192_no_points.json): ventana de filas y columnas que contiene el
# recorte de 45 km de la grilla de MIROVA, con la MIR fusionada y la TIR de leer_radiancia_modis y la posición del
# MxD03. Mentolat: todos sus píxeles con posición y DN 65527 en las bandas 21, 22 y 31. Melimoyu (control, el volcán
# vecino que pasó): la misma franja, con radiancia válida en parte del recorte.
DATOS = Path(__file__).resolve().parent / "datos_s192_sin_radiancia"
DIAG = Path(__file__).resolve().parents[1] / "experiments" / "_s192_no_points" / "diag_s192_no_points.json"
VOLCANES_REALES = {"Mentolat": (-44.7, -73.08), "Melimoyu": (-44.08, -72.88)}   # volcanoes.yaml


def _real(nombre):
    z = np.load(DATOS / f"recorte_{nombre}.npz")
    lat, lon = z["lat"].astype(float), z["lon"].astype(float)
    ang = {"sensor_zenith": np.full(lat.shape, 60.0), "solar_zenith": np.full(lat.shape, 120.0),
           "sensor_azimuth": np.full(lat.shape, -100.0), "solar_azimuth": np.full(lat.shape, 50.0)}
    vl, vo = VOLCANES_REALES[nombre]
    return MV.calcular_vrp_granulo({"MIR": z["MIR"].astype(float), "TIR": z["TIR"].astype(float)}, lat, lon, ang,
                                   nombre, vl, vo, 5.0, "MODIS_TERRA", familia="MODIS")


def test_mentolat_real_escena_vacia():
    esperado = json.loads(DIAG.read_text(encoding="utf-8"))["volcanes"]["Mentolat"]
    assert esperado["n_mir_valido"] == 0 and esperado["n_con_posicion"] >= 100   # el caso que falló
    rec = _real("Mentolat")
    _assert_vacia(rec, 0, 0)


def test_melimoyu_real_sigue_el_camino_de_siempre():
    esperado = json.loads(DIAG.read_text(encoding="utf-8"))["volcanes"]["Melimoyu"]
    assert esperado["n_mir_valido"] >= MV.MIN_PX_TRIANGULAR
    rec = _real("Melimoyu")
    d = rec["diag_codigo_mirova"]
    assert d.get("motivo_vacio") != "sin_radiancia_valida"
    assert "px_radiancia_valida" not in d
