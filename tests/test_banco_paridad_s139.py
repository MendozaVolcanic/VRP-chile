# -*- coding: utf-8 -*-
"""Fase 0 tarea 3 (S139/S140): banco de paridad por pasada con negativos.

POR QUE: la brecha con MIROVA es sobre-publicacion (S139). El banco mide, contra la referencia
unificada (tarea 2) y con el predicado del dashboard ejecutado desde frontend/index.html, cuanto
publicamos en pasadas que MIROVA miro sin ver nada, y cuanto recuperamos de sus alertas.

Los tests fijan los controles del instrumento (identidad del predicado, barajado, oraculo, todo y
nada) y una banda para la linea base medida en S139. El banco se corre una vez por modulo.
"""
import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture(scope="module")
def banco(tmp_path_factory):
    out = tmp_path_factory.mktemp("banco") / "banco.json"
    r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "banco_paridad.py"),
                        "--snapshot", "--out", str(out)],
                       capture_output=True, text=True, timeout=600,
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    assert r.returncode == 0, r.stderr[-1500:]
    with open(out, encoding="utf-8") as fh:
        return json.load(fh)


def test_meta(banco):
    assert banco["meta"]["ventana"][0] == "2026-03-01"
    assert len(banco["meta"]["sha_index_html"]) == 40


def test_controles_de_instrumento(banco):
    c = banco["controles"]
    # el predicado extraido reproduce los casos del guard S139
    assert c["identidad_predicado"] is True
    # barajar etiquetas dentro del volcan destruye la separacion
    assert c["auc_barajado_por_volcan"], "sin volcanes con n suficiente"
    for v, a in c["auc_barajado_por_volcan"].items():
        assert 0.4 <= a <= 0.6, (v, a)
    # un campo igual a la etiqueta separa perfecto
    assert c["auc_oraculo"] == 1.0
    # todo publica / nada publica sobre el mismo denominador
    assert c["todo_publica"]["VIIRS375"]["recall_pos"] == 1.0
    assert c["todo_publica"]["VIIRS375"]["tasa_pub_neg"] == 1.0
    assert c["nada_publica"]["VIIRS375"]["recall_pos"] == 0.0
    assert c["nada_publica"]["VIIRS375"]["tasa_pub_neg"] == 0.0


def test_linea_base_reproduce_s139(banco):
    """S139 (VERIFICADOR.md) midio V375 publicando en 63,5 % de los negativos limpios por pasada con
    la referencia solo-snapshot. Con la referencia unificada y ventana desde marzo el valor puede
    moverse unos puntos, no de orden: se fija una banda."""
    v375 = banco["por_sensor"]["VIIRS375"]["pasada"]
    assert v375["n_neg_limpio"] > 1000
    assert 0.50 <= v375["tasa_pub_neg"] <= 0.75
    assert banco["por_sensor"]["VIIRS375"]["noche_volcan"]["recall_pos"] > 0.95


def test_por_volcan_y_far_ref(banco):
    assert len(banco["por_volcan"]) == 11
    far = banco["far_ref"]["VIIRS375"]
    assert far["n"] > 50
    assert 0.0 <= far["frac_far_con_cumulo"] <= 1.0
    assert banco["far_ref"]["noches_crater_tapado"] >= 0
