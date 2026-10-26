# -*- coding: utf-8 -*-
"""Pruebas de dias_excluidos_nasa.py (adenda del 2026-10-26 en el §11 del pre-registro).

POR QUÉ. La regla excluye días enteros de los dos brazos; si el criterio se equivoca, saca del A/B días con datos o deja
dentro un hueco de NASA. El criterio es mecánico (adenda 1 del §11): un día se excluye si, para alguna plataforma VIIRS,
(a) CMR no tiene ningún gránulo de esa plataforma ese día, y (b') el control no tiene ningún record de esa plataforma ese
día. La regla (b) original (el control pierde una pasada nocturna de MIROVA) se informa y no decide.

Correr: python -m pytest -q -p no:cacheprovider experiments/_s163_diurno_k/test_dias_excluidos_nasa.py
"""
from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

import pytest

os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
for p in (str(ROOT), str(ROOT / "scripts"), str(AQUI)):
    if p not in sys.path:
        sys.path.insert(0, p)

import clase_mirova as cm  # noqa: E402
import dias_excluidos_nasa as dx  # noqa: E402

V375, V750 = "VIIRS375", "VIIRS750"


def test_productos_por_sensor():
    assert set(dx.PRODUCTOS[V375]) == {"VNP02IMG", "VJ102IMG", "VJ202IMG"}
    assert set(dx.PRODUCTOS[V750]) == {"VNP02MOD", "VJ102MOD", "VJ202MOD"}


@pytest.mark.parametrize("vacios,faltas,esperado", [
    # el caso de W1: Suomi NPP sin gránulos 3 días y el control pierde noches esos días
    ({"VNP02IMG": {"2026-03-10", "2026-03-11", "2026-03-12"}, "VNP02MOD": {"2026-03-10", "2026-03-11", "2026-03-12"}},
     {V375: {"2026-03-10"}, V750: {"2026-03-11"}}, ["2026-03-10", "2026-03-11"]),
    # sólo (a): CMR vacío pero el control no pierde nada ese día -> no se excluye
    ({"VNP02IMG": {"2026-03-10"}}, {}, []),
    # sólo (b): el control pierde una noche pero CMR tiene todo -> no se excluye (no es hueco de NASA)
    ({}, {V375: {"2026-03-10"}}, []),
    # (a) en un sensor y (b) en el otro, el mismo día -> no se excluye (las dos condiciones van por sensor)
    ({"VNP02IMG": {"2026-03-10"}}, {V750: {"2026-03-10"}}, []),
    # (a) un día y (b) otro día -> no se excluye
    ({"VJ102MOD": {"2026-08-01"}}, {V750: {"2026-08-02"}}, []),
    # cualquier plataforma del sensor vale para (a)
    ({"VJ202MOD": {"2026-08-01"}}, {V750: {"2026-08-01"}}, ["2026-08-01"]),
])
def test_regla_b_informativa(vacios, faltas, esperado):
    assert dx.dias_a_excluir_b(vacios, faltas) == esperado


def test_faltas_nocturnas_del_control():
    P = lambda vol, s, t: cm.PasadaMirova(vol, s, t, "rutina", 0.0, None, "CONS", False, False, (), False)  # noqa: E731
    noche1, noche2, dia = datetime(2026, 3, 10, 5, 0), datetime(2026, 3, 11, 5, 0), datetime(2026, 3, 12, 17, 0)
    pasadas = [P("Lascar", V375, noche1), P("Lascar", V375, noche2), P("Lascar", V750, noche1), P("Lascar", V375, dia)]
    recs = [{"vol": "Lascar", "b": V375, "dt": datetime(2026, 3, 10, 5, 1), "es_dia": False},   # a 60 s: la cubre
            {"vol": "Lascar", "b": V750, "dt": datetime(2026, 3, 10, 5, 3), "es_dia": False}]   # a 180 s: no la cubre
    f = dx.faltas_nocturnas_del_control(pasadas, recs)
    assert f == {V375: {"2026-03-11"}, V750: {"2026-03-10"}}          # la diurna sin record no cuenta


def test_salida_declara_la_consulta_y_las_dos_reglas():
    vacios = {"VNP02IMG": {"2026-03-10", "2026-03-11"}, "VJ102IMG": {"2026-03-11"}}
    con_records = {"VJ102IMG": {"2026-03-11"}}
    r = dx.armar_salida(["2026-03-10", "2026-03-11"], vacios, con_records, ["2026-03-10"], {V375: {"2026-03-10"}},
                        "2026-10-26T18:40:00Z", [("W1", "2026-03-01", "2026-03-20")])
    assert r["excluir_dias"] == ["2026-03-10", "2026-03-11"]
    assert r["consulta_cmr_utc"] == "2026-10-26T18:40:00Z" and r["caja"] == dx.CAJA
    # en el 11 sólo Suomi NPP cumple las dos: NOAA-20 no tiene gránulos según CMR pero el control sí tiene records
    assert r["evidencia"]["2026-03-11"] == {"cmr_sin_granulos_y_control_sin_records": ["VNP02IMG"]}
    assert r["informativo_regla_b"]["excluir_dias"] == ["2026-03-10"]
    assert r["informativo_regla_b"]["control_dias_con_noches_perdidas"] == {V375: ["2026-03-10"]}


@pytest.mark.parametrize("vacios,con_records,esperado", [
    # el caso de W1: CMR sin Suomi NPP 3 días y el control sin records de Suomi NPP esos días
    ({"VNP02IMG": {"2026-03-10", "2026-03-11", "2026-03-12"}, "VNP02MOD": {"2026-03-10", "2026-03-11", "2026-03-12"}},
     {"VNP02IMG": {"2026-03-09", "2026-03-13"}, "VNP02MOD": {"2026-03-09", "2026-03-13"}},
     ["2026-03-10", "2026-03-11", "2026-03-12"]),
    # CMR vacío pero el control sí tiene records de esa plataforma ese día -> no se excluye
    ({"VJ102IMG": {"2026-03-14"}}, {"VJ102IMG": {"2026-03-14"}}, []),
    # el control no tiene records de una plataforma pero CMR sí tiene gránulos -> no se excluye (no es hueco de NASA)
    ({}, {}, []),
    # (a) en una plataforma y (b') en otra, el mismo día -> no se excluye (las dos van por plataforma)
    ({"VNP02IMG": {"2026-08-01"}}, {"VNP02IMG": {"2026-08-01"}, "VJ102IMG": set()}, []),
    # cualquier plataforma, también de la banda M
    ({"VJ202MOD": {"2026-08-01"}}, {"VJ202MOD": {"2026-07-31"}}, ["2026-08-01"]),    # el control tiene records de OTRA plataforma ese día (NOAA-20) pero no de la que NASA no tiene: se excluye
    ({"VNP02IMG": {"2026-03-11"}}, {"VJ102IMG": {"2026-03-11"}, "VNP02IMG": {"2026-03-09"}}, ["2026-03-11"]),
])
def test_dias_a_excluir_regla_a_y_b_prima(vacios, con_records, esperado):
    assert dx.dias_a_excluir(vacios, con_records) == esperado


def test_producto_de_sensor():
    assert dx.PRODUCTO_DE_SENSOR["VIIRS_SNPP_750"] == "VNP02MOD" and dx.PRODUCTO_DE_SENSOR["VIIRS_NOAA21"] == "VJ202IMG"


def test_solo_records_nocturnos_cubren_noches():
    # un record marcado diurno no cuenta como cobertura de una pasada nocturna (el control no mira el día)
    P = cm.PasadaMirova("Lascar", V375, datetime(2026, 3, 10, 5, 0), "rutina", 0.0, None, "CONS", False, False, (), False)
    recs = [{"vol": "Lascar", "b": V375, "dt": datetime(2026, 3, 10, 5, 0), "es_dia": True}]
    assert dx.faltas_nocturnas_del_control([P], recs) == {V375: {"2026-03-10"}}


def test_dias_con_records_por_producto(tmp_path):
    import json as _json
    (tmp_path / "ctrl").mkdir()
    recs = [{"sensor": "VIIRS_SNPP", "datetime_utc": "2026-03-09 05:00"},
            {"sensor": "VIIRS_SNPP_750", "datetime_utc": "2026-03-13 05:00"},
            {"sensor": "VIIRS_NOAA21", "datetime_utc": "2026-03-10 05:00"},
            {"sensor": "MODIS_AQUA", "datetime_utc": "2026-03-10 05:00"},
            {"sensor": "VIIRS_SNPP", "datetime_utc": "2026-04-09 05:00"}]          # fuera de la ventana
    (tmp_path / "ctrl" / "Lascar.json").write_text(_json.dumps({"records": recs}), encoding="utf-8")
    out = dx.dias_con_records_por_producto([tmp_path], "ctrl", [("W1", "2026-03-01", "2026-03-20")])
    assert out == {"VNP02IMG": {"2026-03-09"}, "VNP02MOD": {"2026-03-13"}, "VJ202IMG": {"2026-03-10"}}
