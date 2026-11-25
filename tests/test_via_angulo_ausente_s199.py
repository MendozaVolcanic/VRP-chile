# -*- coding: utf-8 -*-
"""S199, escena sin ángulo de observación: F8-107 y F3-102 (auditoría Codex, ronda 2) y R3F3-102 (ronda 3).

POR QUÉ (el fenómeno primero). La vía «código MIROVA» necesita cuatro ángulos del píxel más cercano al centro de la
grilla: el cenit del sol decide si la pasada es de noche o de día (umbrales distintos), y con los cuatro (cenit y
azimut del sol y del satélite) calcula el ángulo de reflejo solar; si es menor que 12 grados el .m anula la escena.
Si el gránulo trae un ángulo ausente, NaN o con el valor de relleno, la vía rellenaba en silencio: 180 para decidir la
noche y 0 para el reflejo (`calcular_vrp_granulo`). Con el cenit del satélite bajo 12 grados, o sin ningún ángulo, la
escena salía con 0 MW y motivo «sunglint»: el tablero decía «reflejo solar» de una pasada que no midió el reflejo. Con
el cenit del sol NaN o de relleno la escena corría con umbrales de día de noche. Y con el cenit del satélite bien y sin
el del sol, el detector corría con umbrales de noche sin saber si era de noche. El acta de cierre de la auditoría,
aprobada por Nicolás (docs/ACTA_CIERRE_AUDITORIA_CODEX_2026-11-24.md, F8-107 y F3-102), decide: «Aceptar con marca:
marcar "sin ángulo" como escena no medida cuando aparezca».

Qué se exige, en los tres sensores, por el código real (`calcular_vrp_granulo`): si alguno de los cuatro ángulos falta,
no es finito o cae fuera de su rango físico (cenit de 0 a 180 grados, azimut de -180 a 360; el relleno escalado de
NASA, -327,68 o -327,67, cae fuera), la escena se guarda vacía (0 MW, sin píxeles) con `motivo_vacio`
«angulo_ausente», la lista `angulos_invalidos`, `dayflag` y `sunglint` nulos (no se pudieron decidir) y ningún NaN en
el record (un NaN en el JSON rompe la carga del volcán en el navegador). Controles: con los cuatro ángulos válidos el
record no cambia (la neutralidad byte a byte la comprueba experiments/_s199_sin_angulo/neutralidad.py) y no lleva las
claves nuevas; y la escena sin radiancia conserva su motivo.

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) ¿Fallaría con el código de antes? Sí: en main los casos dan motivo «sunglint»,
null o una detección, nunca «angulo_ausente» (comprobado al escribirla). (2) ¿Puede dar distinto de cero? El control
con ángulos válidos exige que el foco sintético SÍ se detecte (vrp_mw > 0): si el gránulo no tuviera foco, la prueba de
que la marca deja 0 MW no diría nada.

Gránulo sintético: el de tests/test_via_sin_radiancia_s192.py (malla con leve desorden, fondo 268 K) con un foco de
2 x 2 píxeles a 600 K en la MIR sobre el cráter; valores ilustrativos, no instrumentales.
"""
from __future__ import annotations

import json
import math
import shutil

import numpy as np
import pytest

from pipeline import mirova_v750_codigo as MV

VOLC = "Villarrica"
V_LAT, V_LON = -39.42, -71.93          # volcanoes.yaml, Villarrica (volcan_por_coordenadas exige igualdad)
INNER_KM = 5.0
FAMILIAS = ("MODIS", "VIIRS750", "VIIRS375")
SENSOR = {"MODIS": "MODIS_TERRA", "VIIRS750": "VIIRS_NOAA20_750", "VIIRS375": "VIIRS_NOAA20"}
PASO_NATIVO_KM = {"MODIS": 1.0, "VIIRS750": 0.75, "VIIRS375": 0.375}
CLAVES = ("sensor_zenith", "sensor_azimuth", "solar_zenith", "solar_azimuth")
RELLENO = -327.68                      # int16 -32768 por el factor 0,01 del GEO de VIIRS (MxD03: -32767, -327,67)


def _granulo(familia, sat_zen=20.0, semilla=199):
    """Gránulo sintético de ±41 km alrededor del cráter, de noche (sol a 120°), con un foco sobre el cráter."""
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
    t_mir = t.copy()
    t_mir[c:c + 2, c:c + 2] = 600.0
    b_mir, b_tir = cfg["bandas"]
    rad = {b_mir: MV.temperatura_a_radiancia(t_mir, cfg["lam_mir"]),
           b_tir: MV.temperatura_a_radiancia(t - 3.0, cfg["lam_tir"])}
    ang = {"sensor_zenith": np.full((n, n), sat_zen), "solar_zenith": np.full((n, n), 120.0),
           "sensor_azimuth": np.full((n, n), -100.0), "solar_azimuth": np.full((n, n), 50.0)}
    return {"rad": rad, "lat": lat, "lon": lon, "ang": ang}


def _correr(gr, familia):
    return MV.calcular_vrp_granulo(gr["rad"], gr["lat"], gr["lon"], gr["ang"], VOLC, V_LAT, V_LON, INNER_KM,
                                   SENSOR[familia], familia=familia)


def _assert_marcada(rec, invalidos):
    assert rec is not None, "la escena sin ángulo debe guardarse como no medida, no descartarse"
    d = rec.get("diag_codigo_mirova") or {}
    assert d.get("motivo_vacio") == "angulo_ausente", d.get("motivo_vacio")
    assert d.get("angulos_invalidos") == sorted(invalidos), d.get("angulos_invalidos")
    assert rec.get("vrp_mw") == 0.0
    assert rec.get("n_anomalous_pixels") == 0
    assert rec.get("anomaly_pixels") == []
    assert rec.get("primary_cluster") is None
    assert rec.get("via_codigo_mirova") is True
    # la noche y el reflejo no se pudieron decidir: no se escribe un valor inventado
    assert "dayflag" in d and d.get("dayflag") is None
    assert "sunglint" in d and d.get("sunglint") is None
    # JSON estándar: un NaN rompe JSON.parse del tablero (R3F3-107)
    json.dumps({k: v for k, v in rec.items() if k != "_miniatura"}, allow_nan=False)


@pytest.mark.parametrize("familia", FAMILIAS)
@pytest.mark.parametrize("valor", ("ausente", "nan", "relleno"))
def test_cenit_solar_invalido_con_satelite_bajo_12(familia, valor):
    """El caso de F8-107: sin cenit solar y con el satélite casi en el nadir (5°). En main da 0 MW con motivo
    «sunglint» (ausente o NaN) o umbrales de día de noche (relleno)."""
    gr = _granulo(familia, sat_zen=5.0)
    if valor == "ausente":
        del gr["ang"]["solar_zenith"]
    else:
        gr["ang"]["solar_zenith"][:] = np.nan if valor == "nan" else RELLENO
    _assert_marcada(_correr(gr, familia), ["solar_zenith"])


@pytest.mark.parametrize("familia", FAMILIAS)
def test_sin_ningun_angulo(familia):
    """Sin ningún ángulo: en main el reflejo vale 0 y la escena sale «reflejo solar»."""
    gr = _granulo(familia)
    gr["ang"] = {}
    _assert_marcada(_correr(gr, familia), list(CLAVES))


@pytest.mark.parametrize("familia", FAMILIAS)
def test_sin_cenit_solar_con_satelite_oblicuo(familia):
    """Sin cenit solar y con el satélite a 30°: en main el foco se detecta con umbrales de noche aunque nada dice que
    sea de noche (F8-107, i3: 448,854 MW en VIIRS 750). La pasada no se pudo clasificar: no medida."""
    gr = _granulo(familia, sat_zen=30.0)
    del gr["ang"]["solar_zenith"]
    _assert_marcada(_correr(gr, familia), ["solar_zenith"])


@pytest.mark.parametrize("familia", FAMILIAS)
@pytest.mark.parametrize("clave", ("sensor_zenith", "sensor_azimuth", "solar_azimuth"))
@pytest.mark.parametrize("valor", ("ausente", "nan", "relleno"))
def test_otro_angulo_invalido(familia, clave, valor):
    """Los otros tres ángulos también entran al reflejo solar: ausente, NaN o de relleno, la escena no es medida."""
    gr = _granulo(familia)
    if valor == "ausente":
        del gr["ang"][clave]
    else:
        gr["ang"][clave][:] = np.nan if valor == "nan" else RELLENO
    _assert_marcada(_correr(gr, familia), [clave])


@pytest.mark.parametrize("familia", FAMILIAS)
def test_angulo_none_cuenta_como_ausente(familia):
    """El lector puede entregar la clave con None (calcular_vrp_granulo ya lo filtraba): es un ángulo ausente."""
    gr = _granulo(familia)
    gr["ang"]["solar_zenith"] = None
    _assert_marcada(_correr(gr, familia), ["solar_zenith"])


@pytest.mark.parametrize("familia", FAMILIAS)
def test_control_angulos_validos_detecta_y_no_marca(familia):
    """Control (pregunta 2 del instrumento): con los cuatro ángulos válidos el foco se detecta y no hay claves nuevas."""
    rec = _correr(_granulo(familia), familia)
    d = rec["diag_codigo_mirova"]
    assert rec["vrp_mw"] > 0, "el foco sintético debe detectarse con ángulos válidos"
    assert d.get("motivo_vacio") is None
    assert "angulos_invalidos" not in d
    assert d.get("dayflag") == 0 and isinstance(d.get("sunglint"), float)
    assert {f"{k}_deg" for k in CLAVES} <= set(rec)


@pytest.mark.parametrize("familia", FAMILIAS)
def test_control_reflejo_real_sigue_siendo_sunglint(familia):
    """Control: con los cuatro ángulos válidos y reflejo real (sol y satélite casi alineados, de día) el motivo sigue
    siendo «sunglint», no el nuevo."""
    gr = _granulo(familia, sat_zen=5.0)
    gr["ang"]["solar_zenith"][:] = 5.0
    gr["ang"]["solar_azimuth"][:] = -100.0 + 180.0
    rec = _correr(gr, familia)
    d = rec["diag_codigo_mirova"]
    assert d.get("motivo_vacio") == "sunglint"
    assert "angulos_invalidos" not in d


@pytest.mark.skipif(shutil.which("node") is None, reason="el tablero se prueba con node")
def test_tablero_rotula_sin_angulo(tmp_path):
    """El tablero (funciones reales de frontend/index.html) rotula la escena «sin ángulo», con su explicación, y no la
    cuenta como pasada; control: sin motivo, «sin anomalía». El panel de miniaturas lo fija
    tests/test_miniaturas_rotulo_r4fb.py. En main la fila decía el genérico «escena sin medir»."""
    from test_tablero_escenas_invalidas_s183 import _node, _r
    casos = [_r("t", "angulo_ausente"), _r("t", None)]
    cuerpo = """
const isValidDetection = r => false;
process.stdout.write(JSON.stringify(DATOS.map(r => [escenaSinDato(r), rotuloPasadaSinPublicar(r)])));
"""
    out = _node(tmp_path, ["escenaSinDato", "rotuloPasadaSinPublicar"], cuerpo, casos)
    assert out[0][0] == "sin ángulo" and out[0][1]["texto"] == "sin ángulo" and out[0][1]["sinDato"] is True, out[0]
    assert "ángulo válido del sol o del satélite" in out[0][1]["title"], out[0][1]["title"]
    assert out[1][0] is None and out[1][1]["texto"] == "sin anomalía"


@pytest.mark.parametrize("familia", FAMILIAS)
def test_sin_radiancia_conserva_su_motivo(familia):
    """Control de precedencia: sin radiancia que interpolar, la escena sigue siendo «sin_radiancia_valida» aunque
    también falte un ángulo (no hubo nada que medir), y la lista de ángulos inválidos queda igual de escrita."""
    gr = _granulo(familia)
    for b in gr["rad"]:
        gr["rad"][b][:] = np.nan
    del gr["ang"]["solar_zenith"]
    rec = _correr(gr, familia)
    d = rec["diag_codigo_mirova"]
    assert d.get("motivo_vacio") == "sin_radiancia_valida"
    assert d.get("angulos_invalidos") == ["solar_zenith"]
    assert rec.get("vrp_mw") == 0.0
