# -*- coding: utf-8 -*-
"""S193 (A45, aprobado por Nicolás el 2026-11-21): dos diagnósticos de la vía que decían menos de lo que pasó.

POR QUÉ (el fenómeno primero).

F2-V303 (auditoría Codex ronda 2, frente 2). En VIIRS 375 la vía no usa la caja de la grilla: busca el volcán en la
caja C13 (13 x 13 celdas de 375 m) puesta sobre el cráter dentro de la ROI1 física (caja_v375). Pero el record decía
`diag_codigo_mirova.roi = "def"` en los 28.930 records V375 de la vía en data/mirova_equivalent y en los 1.621 de
data/sombra_34 (censo S193 sobre main 27ded66ee, D:\\vrp-trabajo\\temporales\\s193_f2f3\\censo_main_27ded66ee.txt).
Quien revisara la caja con ese campo veía la matriz de ejemplo del .m, que no se usó. Lo mismo pasaría en VIIRS 750 si
alguien pasa tipo_roi a mano. El diagnóstico tiene que decir la caja que de verdad buscó.

F3-107 y F3-V201 (frente 3). Si la escena es válida en conjunto (menos de media grilla sin dato) pero en el 7 x 7
alrededor del cráter no hay ni una celda que el detector pudiera evaluar (hueco de datos, nube fría bajo 200 K en la
banda térmica, o ajuste imposible), el detector no miró el cráter. El record salía con vrp_mw 0 y motivo_vacio nulo, y
el tablero lo pintaba como «pasada medida sin anomalía». Hoy son 23 records de los 11 principales (20 de Puyehue-Cordón
Caulle). El .m de MIROVA hace lo mismo y advierte no leerlo como cero (MIROVA_VIIRS750_VRP.m l. 20-22). Desde aquí la
escena lleva motivo_vacio «crater_no_evaluado»: la cifra publicada sigue siendo 0 MW (como las demás escenas no
medidas, ficha v1.27), sólo deja de presentarse como medición.

Qué se exige: (1) la roi del diagnóstico es la caja usada en los tres sensores; (2) cráter sin ninguna celda evaluable y
sin alertados: motivo «crater_no_evaluado»; (3) con una sola celda evaluable en el 7 x 7, o con un alertado en
cualquier parte, o con otro motivo ya puesto, no cambia nada; (4) ningún campo de detección ni de potencia cambia.
Grillas y gránulos sintéticos: temperaturas ilustrativas, no instrumentales.
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from pipeline import mirova_v750_codigo as MV

VOLC = "Villarrica"
V_LAT, V_LON = -39.42, -71.93          # volcanoes.yaml, Villarrica
INNER_KM = 5.0
SENSOR = {"MODIS": "MODIS_AQUA", "VIIRS750": "VIIRS_NOAA20_750", "VIIRS375": "VIIRS_NOAA20"}
PASO_NATIVO_KM = {"MODIS": 1.0, "VIIRS750": 0.75, "VIIRS375": 0.375}
CRATER = (33, 33)                       # celda del cráter en la grilla 67 x 67 de V750 usada abajo


# ------------------------------------------------------------------------------------------ F2-V303: roi usada
def _granulo(familia, semilla=193):
    paso = PASO_NATIVO_KM[familia]
    n = 2 * int(round(41.0 / paso)) + 1
    c = n // 2
    rng = np.random.default_rng(semilla)
    fil, col = np.indices((n, n))
    yn = (c - fil) * paso + rng.normal(0, 0.05 * paso, (n, n))
    xe = (col - c) * paso + rng.normal(0, 0.05 * paso, (n, n))
    lat = V_LAT + yn / 111.32
    lon = V_LON + xe / (111.32 * math.cos(math.radians(V_LAT)))
    lat[c, c], lon[c, c] = V_LAT, V_LON
    cfg = MV.FAMILIAS[familia]
    t = 268.0 + rng.normal(0, 0.4, (n, n))
    mir = MV.temperatura_a_radiancia(t, cfg["lam_mir"])
    tir = MV.temperatura_a_radiancia(t - 3.0, cfg["lam_tir"])
    ang = {"sensor_zenith": np.full((n, n), 20.0), "solar_zenith": np.full((n, n), 120.0),
           "sensor_azimuth": np.full((n, n), -100.0), "solar_azimuth": np.full((n, n), 50.0)}
    b_mir, b_tir = cfg["bandas"]
    return {b_mir: mir, b_tir: tir}, lat, lon, ang


def _roi(familia, **kw):
    rad, lat, lon, ang = _granulo(familia)
    rec = MV.calcular_vrp_granulo(rad, lat, lon, ang, VOLC, V_LAT, V_LON, INNER_KM, SENSOR[familia],
                                  familia=familia, **kw)
    assert rec is not None, "el gránulo sintético no dio record (error de armado)"
    return rec["diag_codigo_mirova"]["roi"]


def test_viirs375_dice_la_caja_c13_en_el_crater():
    """(1) VIIRS 375 usa siempre caja_v375 (C13 en el cráter dentro de la ROI1 física): el diagnóstico lo dice."""
    assert _roi("VIIRS375") == "c13_crater"


@pytest.mark.parametrize("tipo", ("sens", "crater", "corona"))
def test_viirs750_con_tipo_roi_explicito_dice_ese(tipo):
    """(1) Si el llamador elige la caja, el diagnóstico dice esa y no la de la grilla (Villarrica: def)."""
    assert _roi("VIIRS750", tipo_roi=tipo) == tipo


def test_viirs750_y_modis_por_defecto_dicen_la_de_la_grilla():
    """(1) Sin tipo_roi, la caja es la de grillas_mirova.yaml (Villarrica: def en V750; MODIS sin clave: def)."""
    assert _roi("VIIRS750") == "def"
    assert _roi("MODIS") == "def"


def test_grilla_sin_clave_roi_dice_def():
    """(1) Una grilla dada a mano sin «roi» se procesa con la caja def; el diagnóstico decía None."""
    g = dict(MV.grilla_del_volcan(VOLC))
    g.pop("roi")
    assert _roi("VIIRS750", grilla=g) == "def"


# ------------------------------------------------------------------------------- F3-107: cráter no evaluado
def _escena(caliente_lejos=False, frio_radio=None, hueco_radio=None):
    """Grilla 67 x 67 de V750 con fondo tibio. frio_radio: celdas del cráter con la banda térmica a 190 K (el .m las
    descarta bajo 200 K, l. 151-154); hueco_radio: celdas del cráter sin dato en las dos bandas."""
    rng = np.random.default_rng(162)
    T15 = 265.0 + rng.normal(0, 0.3, (67, 67))
    T13 = T15 - 3 + rng.normal(0, 0.3, (67, 67))
    if caliente_lejos:
        T13[12, 12] += 25                                   # foco a unos 22 km del cráter, dentro de la ROI def
    f0, k0 = CRATER
    if frio_radio is not None:
        r = frio_radio
        T15[f0 - r:f0 + r + 1, k0 - r:k0 + r + 1] = 190.0
    m13 = MV.temperatura_a_radiancia(T13, MV.LAMBDA_M13)
    m15 = MV.temperatura_a_radiancia(T15, MV.LAMBDA_M15)
    if hueco_radio is not None:
        r = hueco_radio
        m13[f0 - r:f0 + r + 1, k0 - r:k0 + r + 1] = np.nan
        m15[f0 - r:f0 + r + 1, k0 - r:k0 + r + 1] = np.nan
    return m13, m15


def _rec(m13, m15, box=None, sunglint=40.0):
    return MV.procesar_grilla(m13, m15, MV.grilla_del_volcan("Lascar"), MV.caja_roi("def") if box is None else box,
                              0, sunglint, (33.0, 33.0), 5.0, "VIIRS_NOAA20_750")




@pytest.mark.parametrize("como", ("frio", "hueco"))
def test_crater_sin_celda_evaluable_es_no_evaluado(como):
    """(2) El 7 x 7 del cráter sin ninguna celda evaluable y sin alertados: no es «sin anomalía», es no evaluado."""
    kw = {"frio_radio": 3} if como == "frio" else {"hueco_radio": 3}
    rec = _rec(*_escena(**kw))
    d = rec["diag_codigo_mirova"]
    assert d["s1"]["celda_decisiva"] is None and "pasada1" in d["s1"]     # el detector corrió y no evaluó el cráter
    assert d["motivo_vacio"] == "crater_no_evaluado"
    assert rec["vrp_mw"] == 0.0 and rec["primary_cluster"] is None and rec["n_anomalous_pixels"] == 0   # (4)


def test_una_celda_evaluable_basta():
    """(3) Con el hueco en el 5 x 5 queda el anillo exterior del 7 x 7: el cráter se evaluó, motivo nulo."""
    rec = _rec(*_escena(frio_radio=2))
    d = rec["diag_codigo_mirova"]
    assert d["s1"]["celda_decisiva"] is not None
    assert d["motivo_vacio"] is None


def test_con_un_alertado_lejos_no_se_marca():
    """(3) Si el detector alertó en otra parte, la escena es una medición con VRP: no se toca."""
    rec = _rec(*_escena(caliente_lejos=True, frio_radio=3))
    d = rec["diag_codigo_mirova"]
    assert rec["n_anomalous_pixels"] > 0 and rec["vrp_mw"] > 0
    assert d["s1"]["celda_decisiva"] is None
    assert d["motivo_vacio"] is None


def test_escena_sana_sin_alertas_sigue_sin_motivo():
    """(3) La noche tranquila de siempre: el cráter se evaluó y no alertó; motivo nulo como antes."""
    d = _rec(*_escena())["diag_codigo_mirova"]
    assert d["s1"]["celda_decisiva"] is not None and d["motivo_vacio"] is None


def test_otro_motivo_no_se_pisa():
    """(3) Reflejo solar: el motivo del detector se conserva (el detector no corrió, no hay pases)."""
    d = _rec(*_escena(frio_radio=3), sunglint=5.0)["diag_codigo_mirova"]
    assert d["motivo_vacio"] == "sunglint"


@pytest.mark.parametrize("kw", ({"frio_radio": 3}, {"hueco_radio": 3}, {"frio_radio": 2}, {},
                                {"caliente_lejos": True, "frio_radio": 3}, {"caliente_lejos": True}))
def test_lo_publicado_sale_del_detector_y_del_vrp(kw):
    """(4) La marca no toca la potencia ni los alertados: salen del detector y del VRP del .m como siempre."""
    m13, m15 = _escena(**kw)
    rec = _rec(m13, m15)
    mask = MV.detectar_mirova(m13, m15, MV.caja_roi("def"), 0, 40.0)
    assert rec["n_anomalous_pixels"] == int(mask.sum())
    esperado = round(float(MV.vrp_mirova(m13, mask)["VRP_MW"]), 3) if mask.any() else 0.0
    assert rec["vrp_mw"] == esperado
