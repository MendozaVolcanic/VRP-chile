# -*- coding: utf-8 -*-
"""S190 (H04 de la auditoría de Codex, verificado en D:\\vrp-trabajo\\temporales\\s190_codex\\verif\\V1\\): el almacén
juzga si una temperatura de brillo es imposible con el techo físico de la banda que la midió, no con el de MODIS.

POR QUÉ, COMO GEÓLOGO. Sobre 50.000 MW el almacén pregunta por la causa: si la temperatura del píxel más caliente pasa
el techo del sensor, el dato es basura (una bandera de DN sin enmascarar, como los 566 K de Lastarria del 2026-04-23
en MODIS) y se anula; si no, puede ser una erupción enorme de verdad y se guarda con la marca
`vrp_exceeds_sanity_cap`. Hasta S190 el techo era 500 K para todos, pensado para la banda 21 de MODIS. Pero la banda
M13 de VIIRS 750 mide hasta 634 K (Campus et al. 2022, Sensors 22:1713, Tabla 1, la misma cita que ya usa
`pipeline/process_viirs_mod.py::BT_LUT_MAX_MBAND`), y el comentario «VIIRS clampea antes» era falso para ella. Una
erupción vista por M13 a 550 K, con más de 50 GW, se guardaba como 0 MW: indistinguible de una noche tranquila.

QUÉ EXIGE. (1) VIIRS 750: una escena a 550 K y más de 50 GW salida del detector real de la vía se guarda con su
magnitud y la marca. (2) Sobre 634 K en VIIRS 750 se sigue anulando. (3) MODIS no cambia (500 K). (4) VIIRS 375 no
cambia (500 K): su techo propio queda SIN DATO para la temperatura que da la vía (ver la constante en store.py).
(5) El 634 de store.py es el mismo número que el del lector de bandas M; si uno cambia, la prueba lo dice.

LAS DOS PREGUNTAS DEL INSTRUMENTO. ¿Puede dar rojo? Sí: sin el arreglo (1) y la escena sintética de 550 K fallan por
aserción (el almacén las anula). Controles que no pueden pasar por casualidad: (2) y (3) anulan, (4) marca sin anular.
"""
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pipeline.store as store  # noqa: E402
from pipeline import mirova_v750_codigo as MV  # noqa: E402
from pipeline import process_viirs_mod  # noqa: E402

GW60 = 60_000.0


def _rec(sensor, t_max_k, vrp=GW60):
    return {"sensor": sensor, "vrp_mw": vrp, "t_max_k": t_max_k, "primary_cluster": {"vrp_mw": vrp}}


@pytest.mark.parametrize("sensor", ["VIIRS_SNPP_750", "VIIRS_NOAA20_750", "VIIRS_NOAA21_750"])
def test_v750_bajo_634_k_se_conserva_y_se_marca(sensor):
    r = _rec(sensor, 550.0)
    store._apply_sanity_cap(r)
    assert r["vrp_mw"] == GW60 and r["primary_cluster"]["vrp_mw"] == GW60, r
    assert r.get("vrp_exceeds_sanity_cap") is True, r
    assert "discarded_reason" not in r, r


def test_v750_justo_en_634_k_se_conserva():
    """Borde: el TMAX del detector es medible (`>` y no `>=`); 634,0 K no es imposible."""
    r = _rec("VIIRS_NOAA20_750", 634.0)
    store._apply_sanity_cap(r)
    assert r["vrp_mw"] == GW60 and r.get("vrp_exceeds_sanity_cap") is True, r


@pytest.mark.parametrize("t", [634.01, 650.0])
def test_v750_sobre_634_k_se_anula(t):
    r = _rec("VIIRS_NOAA20_750", t)
    store._apply_sanity_cap(r)
    assert r["vrp_mw"] == 0.0 and r["primary_cluster"]["vrp_mw"] == 0.0, r
    assert r["diag_rejected_sanity_cap_mw"] == GW60
    assert r.get("discarded_reason") == "sanity_cap_pc_garbage"


@pytest.mark.parametrize("sensor", ["MODIS_AQUA", "MODIS_TERRA"])
def test_modis_no_cambia(sensor):
    basura = _rec(sensor, 550.0)
    store._apply_sanity_cap(basura)
    assert basura["vrp_mw"] == 0.0, basura
    real = _rec(sensor, 450.0)
    store._apply_sanity_cap(real)
    assert real["vrp_mw"] == GW60 and real.get("vrp_exceeds_sanity_cap") is True, real


@pytest.mark.parametrize("sensor", ["VIIRS_SNPP", "VIIRS_NOAA20", "VIIRS_NOAA21"])
def test_v375_no_cambia(sensor):
    basura = _rec(sensor, 550.0)
    store._apply_sanity_cap(basura)
    assert basura["vrp_mw"] == 0.0, basura
    marcada = _rec(sensor, 450.0)
    store._apply_sanity_cap(marcada)
    assert marcada["vrp_mw"] == GW60 and marcada.get("vrp_exceeds_sanity_cap") is True, marcada


def test_sin_temperatura_se_sigue_anulando():
    r = _rec("VIIRS_NOAA20_750", None)
    store._apply_sanity_cap(r)
    assert r["vrp_mw"] == 0.0


def test_techo_m13_es_el_del_lector_de_bandas_m():
    assert store.techo_bt_k("VIIRS_NOAA20_750") == process_viirs_mod.BT_LUT_MAX_MBAND["M13"] == 634.0
    assert store.techo_bt_k("MODIS_AQUA") == store.techo_bt_k("VIIRS_NOAA20") == 500.0
    assert store.techo_bt_k("") == 500.0  # sensor desconocido: el techo de siempre


def test_escena_m13_del_detector_real_llega_entera_al_record(tmp_path, monkeypatch):
    """La escena de Codex (D:\\codex-vrp\\_salida\\parches\\prueba_tope_m13.py): 36 alertados a 550 K sobre fondo de
    277 K en la grilla de Láscar, por `procesar_grilla` de la vía, y después `append_record` con el almacén real."""
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    rng = np.random.default_rng(176)
    tir = MV.temperatura_a_radiancia(280 + rng.normal(0, .2, (67, 67)), MV.LAMBDA_M15)
    mir = MV.temperatura_a_radiancia(277 + rng.normal(0, .2, (67, 67)), MV.LAMBDA_M13)
    mir[30:36, 30:36] = MV.temperatura_a_radiancia(np.array([550.]), MV.LAMBDA_M13)[0]
    r = MV.procesar_grilla(mir, tir, MV.grilla_del_volcan("Lascar"), MV.caja_roi(), 0, 40., (33., 33.), 5.,
                           "VIIRS_NOAA20_750")
    crudo = r["vrp_mw"]
    assert 50_000 < crudo < 70_000 and r["t_max_k"] == 550.0, (crudo, r["t_max_k"])
    r["datetime_utc"] = "2026-11-10 05:00"
    store.append_record("Lascar", r, inner_radius_km=5.0)
    guardado = store.get_records("Lascar")[0]
    assert guardado["vrp_mw"] == crudo, guardado.get("diag_rejected_sanity_cap_mw")
    assert guardado.get("vrp_exceeds_sanity_cap") is True
