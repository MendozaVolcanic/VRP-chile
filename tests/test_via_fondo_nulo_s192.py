"""S192: fondo nulo en la vía «código MIROVA» (F4-101, F2-108, F2-V201, F3-104).

POR QUÉ. El VRP es el exceso de radiancia del alertado sobre el suelo que tendría sin la anomalía. Si el alertado queda
junto a un hueco de datos, el halo del `.m` se come los vecinos útiles, `fillmissing2` no extrapola y el fondo queda
vacío; el `.m` lo suma con `omitnan`, o sea como cero, y el VRP publicado es la radiancia entera del píxel.
- En MODIS, MIROVA no tiene ninguna detección con fondo 0 en 262.455 del OSF v2.5 (F4-101 §4): el fondo 0 nace de correr
  el código de VIIRS 750 con bandas MODIS (D36). Decisión de Nicolás del 2026-11-20 (opción a): esa escena es no medida.
- En VIIRS 375 y 750 el OSF sí trae fondo 0 (501 y 464 detecciones): la vía es fiel, conserva la cifra y lo marca.

Caso real: pasada 3933 de `tests/datos_s164_modis` (Cordón Caulle 2026-03-16 03:10 MODIS Terra), una alerta fuera de
la envolvente convexa tras el halo; hoy la vía publica 2,535 MW y MIROVA la listó sin alerta (falso positivo nuestro).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tests"))

from pipeline import mirova_v750_codigo as MV  # noqa: E402
import test_mirova_modis_codigo_s164 as T164  # noqa: E402

MODIS = MV.FAMILIAS["MODIS"]


def _rec(pid, familia, sensor):
    p, mir, tir, g, box, mask, _d = T164._via_sobre_grilla(pid)
    vl = T164._yaml_volcan(p["vol"])
    rec = MV.procesar_grilla(mir, tir, g, box, p["dayflag"], p["sunglint"], MV.posicion_de(g, vl["lat"], vl["lon"]),
                             p["inner"], sensor, familia=familia)
    return p, mir, mask, rec


def test_el_caso_existe_y_hoy_no_tiene_fondo():
    """Control del instrumento: la pasada 3933 tiene 1 alertado y su fondo no se puede interpolar."""
    p, mir, mask, _ = _rec(3933, "MODIS", "MODIS_TERRA")
    assert (p["vol"], p["dt"]) == ("PuyehueCordonCaulle", "2026-03-16 03:10")
    v = MV.vrp_mirova(mir, mask, coef=MODIS["coef"])
    assert v["npix"] == 1 and v["n_sin_fondo"] == 1
    # vrp_mirova sigue siendo el .m literal: suma sin fondo
    assert v["VRP_MW"] == pytest.approx(float(mir[mask][0]) * MODIS["coef"], rel=1e-12)


def test_modis_sin_fondo_es_escena_no_medida():
    _p, mir, mask, rec = _rec(3933, "MODIS", "MODIS_TERRA")
    dg = rec["diag_codigo_mirova"]
    assert dg["motivo_vacio"] == "fondo_no_estimado"
    assert rec["vrp_mw"] == 0.0
    assert rec["n_anomalous_pixels"] == 0 and rec["anomaly_pixels"] == []
    assert rec["primary_cluster"] is None and rec["distance_class"] is None and rec["t_bg_k"] is None
    assert rec["final_hotspot_lat"] is None
    # el diagnóstico conserva lo que se vio, para auditar
    assert dg["alertados_sin_fondo"] == 1
    assert dg["L_hot"] == pytest.approx(float(mir[mask][0]), rel=1e-12)


def test_viirs_sin_fondo_conserva_la_cifra_y_la_marca():
    """La misma grilla procesada como VIIRS 750: MIROVA publica con fondo 0 en VIIRS, la vía también."""
    _p, mir, _mask, rec = _rec(3933, "VIIRS750", "VIIRS_NOAA20_750")
    dg = rec["diag_codigo_mirova"]
    assert dg["motivo_vacio"] is None
    assert rec["n_anomalous_pixels"] >= 1
    assert dg["alertados_sin_fondo"] == rec["n_anomalous_pixels"]
    assert rec["vrp_mw"] > 0
    assert rec["vrp_mw"] == pytest.approx(round(dg["L_hot"] * MV.FAMILIAS["VIIRS750"]["coef"], 3), abs=1e-3)
    # sin ningún fondo, la temperatura del fondo no existe (antes: 0 K)
    assert rec["t_bg_k"] is None


def test_modis_con_fondo_no_cambia():
    """Láscar 2026-04-25 07:35 MODIS Aqua (protegida, 1,112 MW): con fondo, nada cambia."""
    _p, _mir, _mask, rec = _rec(1611, "MODIS", "MODIS_AQUA")
    dg = rec["diag_codigo_mirova"]
    assert dg["motivo_vacio"] is None
    assert rec["vrp_mw"] == 1.112
    assert dg["alertados_sin_fondo"] == 0
    assert rec["t_bg_k"] is not None and 200 < rec["t_bg_k"] < 320


def test_t_bg_k_promedia_solo_los_alertados_con_fondo():
    """Fondo parcial: t_bg_k es la temperatura del fondo medio de los alertados que sí lo tienen, no de L_bk / npix
    (que mete ceros). Grilla sintética: dos alertados, uno junto a un hueco de datos."""
    n = 21
    m13 = np.full((n, n), 0.30)
    m13[:, :4] = np.nan           # hueco de datos al oeste (borde del barrido)
    mascara = np.zeros((n, n), bool)
    mascara[10, 4] = True         # junto al hueco: su halo 3x3 no deja vecinos al oeste
    mascara[10, 15] = True
    m13[mascara] = 3.0
    v = MV.vrp_mirova(m13, mascara, coef=1.0)
    assert v["npix"] == 2
    # el halo 3x3 junta el hueco (columnas 0 a 4) con el de (10, 4): la columna 4 queda fuera de la envolvente de las
    # celdas con dato (columnas 5 a 20) y sin fondo; (10, 15) está dentro y su fondo es el del suelo, 0,30
    assert v["n_sin_fondo"] == 1
    assert v["L_bk"] == pytest.approx(0.30, rel=1e-9)
    tb = MV.t_bg_de(v, MV.FAMILIAS["VIIRS750"]["lam_mir"])
    esperado = float(MV.radiancia_a_temperatura(np.array([0.30]), MV.FAMILIAS["VIIRS750"]["lam_mir"])[0])
    assert tb == pytest.approx(round(esperado, 2), abs=1e-9)
    # con L_bk / npix (lo de antes) saldría la temperatura de 0,15, varios kelvin más fría
    antes = float(MV.radiancia_a_temperatura(np.array([0.15]), MV.FAMILIAS["VIIRS750"]["lam_mir"])[0])
    assert tb - antes > 5


def test_t_bg_de_sin_alertados_con_fondo_es_nulo():
    assert MV.t_bg_de({"npix": 3, "n_sin_fondo": 3, "L_bk": 0.0}, MV.FAMILIAS["MODIS"]["lam_mir"]) is None
    assert MV.t_bg_de({"npix": 0, "n_sin_fondo": 0, "L_bk": float("nan")}, MV.FAMILIAS["MODIS"]["lam_mir"]) is None


def _grilla_parcial():
    """Grilla sintética con dos alertados: (10, 4) junto a un hueco de datos (sin fondo) y (10, 15) con fondo."""
    n = 21
    m13 = np.full((n, n), 0.30)
    m13[:, :4] = np.nan
    mascara = np.zeros((n, n), bool)
    mascara[10, 4] = True
    mascara[10, 15] = True
    m13[mascara] = 3.0
    g = {"n": n, "paso": 1000.0, "ul_x": 0.0, "ul_y": 0.0, "zona": 19, "hemisferio": "S", "roi": "def"}
    return m13, mascara, g


@pytest.mark.parametrize("familia", ["MODIS", "VIIRS750"])
def test_fondo_parcial_no_es_escena_no_medida(familia, monkeypatch):
    """Si al menos un alertado tiene fondo, la escena SÍ se midió en los dos sensores: se publica (con el .m) y la marca
    dice cuántos quedaron sin fondo. Sólo «ninguno con fondo» es no medida en MODIS."""
    m13, mascara, g = _grilla_parcial()
    monkeypatch.setattr(MV, "detectar_mirova", lambda *a, **k: (mascara.copy(), {"motivo": None}))
    monkeypatch.setattr(MV, "latlon_de", lambda grilla, f, c: (-40.0 - f * 0.01, -72.0 + c * 0.01))
    rec = MV.procesar_grilla(m13, m13, g, None, 0, 90.0, (10.0, 10.0), 5.0, "SENSOR", familia=familia)
    dg = rec["diag_codigo_mirova"]
    assert dg["motivo_vacio"] is None
    assert rec["n_anomalous_pixels"] == 2 and dg["alertados_sin_fondo"] == 1
    assert rec["vrp_mw"] > 0
