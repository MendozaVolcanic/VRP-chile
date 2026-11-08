# -*- coding: utf-8 -*-
"""S176: frontend/cambio_detector.js marca, desde los datos, la fecha en que cada VIIRS pasó a la vía «código MIROVA».

POR QUÉ (diseño docs/superpowers/specs/2026-11-08-encendido-v375e-design.md, decisiones 4 y 7). Con la vía, la magnitud de
VIIRS 375 sube cerca del doble (K publicaba cerca de la mitad que MIROVA): sin marca, ese escalón se lee como que el
volcán crece. Cada VIIRS se enciende y se revierte por separado, así que cada uno lleva su propia marca. La marca sale de
los records y vive en un solo lugar (A102). Sin records de la vía no dibuja nada: mientras los flags estén apagados, el
tablero no cambia. Se prueba con node, como las marcas de K y de MODIS.
"""
import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "tests"))
from test_cambio_detector_s153 import DOM_FALSO, HAY_NODE, node  # noqa: E402,F401

MODULO = RAIZ / "frontend" / "cambio_detector.js"
pytestmark = pytest.mark.skipif(not HAY_NODE, reason="el módulo se prueba con node")
REQ = f"const M = require({json.dumps(str(MODULO))});"

K375 = {"sensor": "VIIRS_NOAA20", "datetime_utc": "2026-11-01 05:00"}
V375 = {"sensor": "VIIRS_NOAA20", "datetime_utc": "2026-11-04 05:00", "via_codigo_mirova": True}
K750 = {"sensor": "VIIRS_NOAA21_750", "datetime_utc": "2026-11-02 05:00"}
V750 = {"sensor": "VIIRS_NOAA21_750", "datetime_utc": "2026-11-06 05:00", "via_codigo_mirova": True}
KM = {"sensor": "MODIS_AQUA", "datetime_utc": "2026-11-01 07:20"}
VM = {"sensor": "MODIS_AQUA", "datetime_utc": "2026-11-02 07:20", "via_codigo_mirova": True}
CAIDA = {"sensor": "VIIRS_NOAA20", "datetime_utc": "2026-11-07 05:00", "via_codigo_mirova": "sin_grilla"}


def _primera(recs, familia):
    (v,) = node(REQ + f"process.stdout.write(JSON.stringify([M.primeraVia({json.dumps(recs)}, {json.dumps(familia)})]));")
    return v


def test_la_fecha_de_cada_viirs_sale_de_sus_records():
    assert _primera([K375, V375, K750, V750], "VIIRS375") == "2026-11-04T05:00:00.000Z"
    assert _primera([K375, V375, K750, V750], "VIIRS750") == "2026-11-06T05:00:00.000Z"


def test_la_via_de_un_sensor_no_marca_otro():
    assert _primera([K375, V750], "VIIRS375") is None, "la vía de 750 no marca 375"
    assert _primera([K750, V375], "VIIRS750") is None, "la vía de 375 no marca 750"
    assert _primera([KM, VM], "VIIRS375") is None and _primera([KM, VM], "VIIRS750") is None
    assert _primera([K375, CAIDA], "VIIRS375") is None, "la caída a K no es la vía"


def test_si_toda_la_ventana_es_de_la_via_no_hay_escalon():
    assert _primera([V375], "VIIRS375") is None
    assert _primera([CAIDA, V375], "VIIRS375") is None, "una caída a K no cuenta como K antes"


def test_notar_guarda_cada_familia_y_pone_un_aviso_por_familia():
    js = REQ + f"""
    const d = docFalso();
    d.createTextNode = t => ({{ tag: "#text", nodeValue: t, get text() {{ return this.nodeValue; }} }});
    M.notarRecords({json.dumps([K375, V375, K750, V750])}, d);
    M.notarRecords({json.dumps([K375, {**V375, "datetime_utc": "2026-11-03 05:00"}])}, d);
    const a375 = d.getElementById("aviso-cambio-via-v375");
    const a750 = d.getElementById("aviso-cambio-via-v750");
    const n375 = d.body.children.filter(x => x.id === "aviso-cambio-via-v375").length;
    const n750 = d.body.children.filter(x => x.id === "aviso-cambio-via-v750").length;
    process.stdout.write(JSON.stringify([M.viaDesde("VIIRS375"), M.viaDesde("VIIRS750"), M.viaDesde("MODIS"), n375, n750,
                                         texto(a375), texto(a750)]));
    """
    d375, d750, dm, n375, n750, t375, t750 = node(js)
    assert d375 == "2026-11-03T05:00:00.000Z", "se corrige a la fecha más temprana de todos los volcanes"
    assert d750 == "2026-11-06T05:00:00.000Z" and dm is None
    assert n375 == 1 and n750 == 1
    assert "3 nov 2026" in t375 and "VIIRS 375" in t375 and "vía «código MIROVA»" in t375
    assert "cerca del doble" in t375 and "no quiere decir que el volcán crezca" in t375
    assert "6 nov 2026" in t750 and "VIIRS 750" in t750 and "cambio del detector" in t750
    for t in (t375, t750):
        assert chr(0x2014) not in t and chr(0x2013) not in t     # sin guiones largos ni medios (regla del usuario)


def test_sin_records_de_la_via_de_viirs_no_cambia_nada():
    js = REQ + f"""
    const d = docFalso();
    const n0 = d.body.children.length;
    M.notarRecords({json.dumps([K375, K750, CAIDA])}, d);
    const c = chartFalso("time", 0, 4e12); c.data = {{ datasets: [{{ label: "VIIRS 375m" }}, {{ label: "VIIRS 750m" }}] }};
    process.stdout.write(JSON.stringify([M.viaDesde("VIIRS375"), M.viaDesde("VIIRS750"), d.body.children.length - n0,
        M.crearPluginVia("VIIRS375").afterDatasetsDraw(c), M.crearPluginVia("VIIRS750").afterDatasetsDraw(c)]));
    """
    assert node(js) == [None, None, 0, False, False]


def _dibuja(familia, etiquetas, ocultos=()):
    t = "Date.parse('2026-11-04T05:00:00Z')"
    recs = [K375, V375] if familia == "VIIRS375" else [K750, {**V750, "datetime_utc": "2026-11-04 05:00"}]
    js = REQ + f"""
    const d = docFalso();
    M.notarRecords({json.dumps(recs)}, d);
    const c = chartFalso("time", {t} - 5*86400000, {t} + 5*86400000);
    c.data = {{ datasets: {json.dumps([{"label": e} if e is not None else {} for e in etiquetas])} }};
    const ocultos = {json.dumps(list(ocultos))};
    c.isDatasetVisible = i => !ocultos.includes(i);
    const r = M.crearPluginVia({json.dumps(familia)}).afterDatasetsDraw(c);
    const textos = c.trazos.filter(x => x[0] === "fillText").map(x => x[1]);
    process.stdout.write(JSON.stringify([r, textos]));
    """
    return node(js)


def test_la_linea_de_cada_viirs_va_solo_en_su_serie():
    assert _dibuja("VIIRS375", ["MODIS (1km)", "VIIRS 375m"])[0] is True
    assert _dibuja("VIIRS375", ["MODIS (1km)", "VIIRS 750m"])[0] is False
    assert _dibuja("VIIRS750", ["VIIRS 375m", "VIIRS 750m"])[0] is True
    assert _dibuja("VIIRS750", ["MODIS (1km)", "VIIRS 375m"])[0] is False
    assert _dibuja("VIIRS375", [None])[0] is True, "mosaico: una sola serie sin rótulo que suma los tres sensores"
    assert _dibuja("VIIRS375", ["VIIRS 375m"], ocultos=[0])[0] is False, "oculta en la leyenda"
    assert _dibuja("VIIRS375", ["MIROVA VIIRS (ref.)"])[0] is False, "la referencia de MIROVA no es nuestra serie"
    assert _dibuja("VIIRS375", ["VIIRS 375m"])[1] == ["VIIRS 375: vía MIROVA"]
    assert _dibuja("VIIRS750", ["VIIRS 750m"])[1] == ["VIIRS 750: vía MIROVA"]


def test_modis_sigue_igual():
    js = REQ + f"""
    const d = docFalso();
    d.createTextNode = t => ({{ tag: "#text", nodeValue: t, get text() {{ return this.nodeValue; }} }});
    const r = M.notarRecords({json.dumps([KM, VM, K375, V375])}, d);
    process.stdout.write(JSON.stringify([r, M.viaModisDesde(), M.primeraViaModis({json.dumps([KM, VM])}),
                                         typeof M.crearPluginViaModis, texto(d.getElementById("aviso-cambio-via-modis"))]));
    """
    r, desde, primera, tipo, txt = node(js)
    assert r == desde == primera == "2026-11-02T07:20:00.000Z" and tipo == "function"
    assert "la magnitud de MODIS sube" in txt


def test_camino_del_navegador_registra_los_plugins_de_viirs(tmp_path):
    src = MODULO.read_text(encoding="utf-8")
    archivo = tmp_path / "cd.js"
    archivo.write_text(src, encoding="utf-8")
    js = r"""
    const src = require('fs').readFileSync(process.argv[process.argv.length - 1], 'utf8');
    const registrados = [];
    const d = docFalso();
    const ventana = { Chart: { register: p => registrados.push(p.id) }, document: d };
    new Function("window", "module", src)(ventana, undefined);
    process.stdout.write(JSON.stringify(registrados));
    """
    registrados = node(js, str(archivo))
    assert {"cambioViaModis", "cambioViaV375", "cambioViaV750"} <= set(registrados)
