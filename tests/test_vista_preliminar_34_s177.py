# -*- coding: utf-8 -*-
"""S177: la vista preliminar de los 34 volcanes dice sólo lo que el dato sostiene.

POR QUÉ. Estos 34 volcanes corren en sombra y MIROVA no los publica: no hay contra qué medir la paridad. Medido del 2026-11-03
al 11-08, ninguna de las 22 detecciones cae a 5 km o menos del volcán, y hay focos vistos desde dos volcanes a la vez. Si la
página pintara cada detección como anomalía del volcán, el operador leería actividad donde hay un foco a 30 km.

QUÉ FIJA, ejecutando en node el módulo real: (1) el corte de cumbre y qué pasa sin posición; (2) el mismo foco visto desde dos
volcanes se marca; (3) el resumen cuenta sólo la ventana y avisa si faltan pasadas; (4) la lista es la de volcanoes.yaml; (5) la
página lleva su rótulo, y el tablero principal sigue sin leer la sombra.
"""
import json
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "frontend" / "preliminar_34.js"
HTML = ROOT / "frontend" / "preliminar_34.html"


def _node(expr):
    """Evalúa `expr` con el módulo real cargado como `m` y devuelve el JSON que produce."""
    prog = f"const m = require({json.dumps(str(JS))}); console.log(JSON.stringify({expr}));"
    salida = subprocess.run(["node", "-e", prog], capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert salida.returncode == 0, salida.stderr
    return json.loads(salida.stdout)


def _r(**k):
    base = {"datetime_utc": "2026-11-08 05:12", "sensor": "VIIRS_NOAA21", "vrp_mw": 1.0, "final_hotspot_dist_km": 12.0,
            "final_hotspot_lat": -30.0, "final_hotspot_lon": -70.0}
    base.update(k)
    return base


@pytest.mark.parametrize("registro, estado", [
    ({"vrp_mw": 0}, "sin_deteccion"),
    ({"vrp_mw": None}, "sin_deteccion"),
    ({"final_hotspot_dist_km": 5.0}, "cumbre"),
    ({"final_hotspot_dist_km": 5.416}, "lejos"),
    ({"final_hotspot_dist_km": None}, "sin_posicion"),
])
def test_clasificar_corta_en_cinco_km_y_no_inventa_posicion(registro, estado):
    assert _node(f"m.clasificar({json.dumps(_r(**registro))}).estado") == estado


def test_el_mismo_foco_visto_desde_dos_volcanes_se_marca():
    dets = [
        {"volcan": "Guallatiri", **_r(datetime_utc="2026-11-07 05:24", final_hotspot_lat=-18.42, final_hotspot_lon=-69.09)},
        {"volcan": "Parinacota", **_r(datetime_utc="2026-11-07 05:24", final_hotspot_lat=-18.421, final_hotspot_lon=-69.09)},
        {"volcan": "Otro", **_r(datetime_utc="2026-11-07 05:24", final_hotspot_lat=-18.50, final_hotspot_lon=-69.09)},
        {"volcan": "Tarde", **_r(datetime_utc="2026-11-07 06:24", final_hotspot_lat=-18.42, final_hotspot_lon=-69.09)},
    ]
    res = _node(f"m.focosCompartidos({json.dumps(dets)}).map(d => d.tambien_desde)")
    assert res == [["Parinacota"], ["Guallatiri"], [], []]


def test_el_resumen_cuenta_solo_la_ventana():
    regs = [_r(datetime_utc="2026-11-08 05:12", final_hotspot_dist_km=20.0, vrp_mw=2.5),
            _r(datetime_utc="2026-11-07 05:12", final_hotspot_dist_km=3.0, vrp_mw=0.5),
            _r(datetime_utc="2026-11-08 06:00", vrp_mw=0),
            _r(datetime_utc="2026-10-01 05:12", final_hotspot_dist_km=2.0, vrp_mw=9.0)]
    res = _node(f"m.resumenVolcan({json.dumps(regs)}, Date.UTC(2026,10,9,12,0), 14)")
    assert res["n_lejos"] == 1 and res["n_cumbre"] == 1
    assert res["vrp_max"] == 2.5
    assert res["ultima_pasada"] == "2026-11-08 06:00"
    assert res["sin_pasadas_recientes"] is False


def test_sin_pasadas_recientes_se_avisa_y_sin_records_tambien():
    regs = [_r(datetime_utc="2026-11-01 05:12", vrp_mw=0)]
    assert _node(f"m.resumenVolcan({json.dumps(regs)}, Date.UTC(2026,10,9,12,0), 14).sin_pasadas_recientes") is True
    vacio = _node("m.resumenVolcan([], Date.UTC(2026,10,9,12,0), 14)")
    assert vacio["sin_pasadas_recientes"] is True and vacio["ultima_pasada"] is None


def test_la_lista_es_la_de_los_34_de_volcanoes_yaml():
    todos = yaml.safe_load((ROOT / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]
    esperados = {v["name"]: v for v in todos if v["radius_km"] != 25}
    assert len(esperados) == 34
    lista = _node("m.VOLCANES")
    assert {v["name"] for v in lista} == set(esperados)
    for v in lista:
        assert v["lat"] == esperados[v["name"]]["lat"] and v["lon"] == esperados[v["name"]]["lon"], v["name"]


def test_la_pagina_lleva_el_rotulo_y_el_modulo():
    texto = HTML.read_text(encoding="utf-8")
    assert "sin referencia de MIROVA, paridad no medida" in texto
    assert 'src="preliminar_34.js"' in texto


def test_el_tablero_principal_sigue_sin_leer_la_sombra():
    for pagina in ("index.html", "diario.html", "mosaico.html"):
        assert "data/sombra_34" not in (ROOT / "frontend" / pagina).read_text(encoding="utf-8"), pagina


@pytest.mark.parametrize("archivo", [JS, HTML])
def test_sin_guiones_largos_ni_voseo_visible(archivo):
    texto = archivo.read_text(encoding="utf-8")
    assert chr(0x2014) not in texto and chr(0x2013) not in texto


def test_un_pixel_en_la_cumbre_manda_aunque_el_cumulo_mayor_este_lejos():
    """Sumar todos los píxeles y ubicar sólo el cúmulo mayor escondería justo lo que importa: actividad en el cráter."""
    volcan = {"lat": -30.0, "lon": -70.0}
    regs = _r(final_hotspot_dist_km=20.0, anomaly_pixels=[{"lat": -30.01, "lon": -70.0}, {"lat": -30.2, "lon": -70.0}])
    res = _node(f"m.clasificar({json.dumps(regs)}, {json.dumps(volcan)})")
    assert res["estado"] == "cumbre" and res["dist_km"] < 2
    lejos = _r(final_hotspot_dist_km=20.0, anomaly_pixels=[{"lat": -30.2, "lon": -70.0}])
    assert _node(f"m.clasificar({json.dumps(lejos)}, {json.dumps(volcan)}).estado") == "lejos"


def test_una_escena_invalida_no_cuenta_como_pasada():
    regs = [_r(datetime_utc="2026-11-08 05:12", vrp_mw=0),
            _r(datetime_utc="2026-11-08 09:00", vrp_mw=0, diag_codigo_mirova={"motivo_vacio": "escena_invalida"})]
    assert _node(f"m.resumenVolcan({json.dumps(regs)}, Date.UTC(2026,10,9,12,0), 14).ultima_pasada") == "2026-11-08 05:12"


def test_el_resumen_dice_cuando_fue_la_ultima_deteccion_y_desde_cuando_hay_datos():
    regs = [_r(datetime_utc="2026-11-04 05:42", final_hotspot_dist_km=17.0), _r(datetime_utc="2026-11-08 05:12", vrp_mw=0),
            _r(datetime_utc="2026-11-03 06:00", vrp_mw=0)]
    res = _node(f"m.resumenVolcan({json.dumps(regs)}, Date.UTC(2026,10,9,12,0), 14)")
    assert res["ultima_deteccion"] == "2026-11-04 05:42" and res["primera_pasada"] == "2026-11-03 06:00"


def test_el_foco_visto_desde_dos_volcanes_se_cuenta_una_vez():
    dets = [{"volcan": "Guallatiri", "tambien_desde": ["Parinacota"], "estado": "lejos"},
            {"volcan": "Parinacota", "tambien_desde": ["Guallatiri"], "estado": "lejos"},
            {"volcan": "Putana", "tambien_desde": [], "estado": "lejos"},
            {"volcan": "Osorno", "tambien_desde": [], "estado": "cumbre"}]
    assert _node(f"m.contarFocos({json.dumps(dets)})") == {"cumbre": 1, "lejos": 2}


def test_la_hora_se_lee_en_utc_y_no_en_la_hora_local():
    assert _node('m.msUtc("2026-11-08 05:12")') == 1794114720000


def test_mismo_foco_exige_el_mismo_sensor():
    dets = [{"volcan": "A", **_r(sensor="VIIRS_NOAA20")}, {"volcan": "B", **_r(sensor="VIIRS_NOAA21")}]
    assert _node(f"m.focosCompartidos({json.dumps(dets)}).map(d => d.tambien_desde)") == [[], []]


def test_el_rotulo_no_afirma_que_se_proceso_cuando_pudo_fallar_la_carga():
    for pagina in ("index.html", "diario.html", "mosaico.html"):
        texto = (ROOT / "frontend" / pagina).read_text(encoding="utf-8")
        assert "procesado, sin publicar" not in texto and "sin datos en este tablero" in texto, pagina
