# -*- coding: utf-8 -*-
"""S172: frontend/cambio_detector.js marca, desde los datos, la fecha en que MODIS pasó a la vía «código MIROVA».

POR QUÉ (diseño docs/superpowers/specs/2026-11-01-encendido-modd-design.md, decisión 5; regla de reversión de MOD-D
§5). Con la vía, la magnitud de MODIS sube y aparecen alertas que K callaba. Sin marca, ese escalón en la serie de
MODIS se lee como un cambio del volcán: en Nevados de Chillán, con el domo activo, «la erupción crece». La marca sale
de los records (la primera pasada MODIS con `via_codigo_mirova: true` que tiene antes una de K), no de una constante
que alguien tiene que llenar el día del merge, y vive en un solo lugar (A102): las vistas sólo le pasan los records.
Sin records de la vía no dibuja nada. Se prueba con node, como la marca de K (tests/test_cambio_detector_s153.py).
"""
import json
import re
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "tests"))
from test_cambio_detector_s153 import DOM_FALSO, HAY_NODE, node  # noqa: E402,F401

MODULO = RAIZ / "frontend" / "cambio_detector.js"
VISTAS = ["index.html", "diario.html", "mosaico.html"]
pytestmark = pytest.mark.skipif(not HAY_NODE, reason="el módulo se prueba con node")
REQ = f"const M = require({json.dumps(str(MODULO))});"

# Records como los guarda pipeline/store.py ('YYYY-MM-DD HH:MM'); K no trae la clave, la vía trae true y su caída a K
# trae un texto.
K1 = {"sensor": "MODIS_AQUA", "datetime_utc": "2026-11-01 07:20"}
K2 = {"sensor": "MODIS_TERRA", "datetime_utc": "2026-11-03 03:10"}
VIA1 = {"sensor": "MODIS_TERRA", "datetime_utc": "2026-11-04 03:10", "via_codigo_mirova": True}
VIA2 = {"sensor": "MODIS_AQUA", "datetime_utc": "2026-11-06 07:20", "via_codigo_mirova": True}
CAIDA = {"sensor": "MODIS_AQUA", "datetime_utc": "2026-11-07 07:20", "via_codigo_mirova": "sin_mxd03"}
V375 = {"sensor": "VIIRS_NOAA20", "datetime_utc": "2026-11-02 05:00", "via_codigo_mirova": True}


def _primera(recs):
    (v,) = node(REQ + f"process.stdout.write(JSON.stringify([M.primeraViaModis({json.dumps(recs)})]));")
    return v


def test_sin_records_de_la_via_no_hay_fecha():
    assert _primera([K1, K2]) is None
    assert _primera([]) is None
    assert _primera([K1, V375]) is None, "la vía de VIIRS no es la de MODIS"
    assert _primera([K1, CAIDA]) is None, "la caída a K no es la vía"


def test_la_fecha_es_la_primera_pasada_de_la_via_que_tiene_k_antes():
    assert _primera([VIA2, K2, K1, VIA1, CAIDA]) == "2026-11-04T03:10:00.000Z"


def test_si_toda_la_ventana_es_de_la_via_no_hay_escalon_que_marcar():
    """El JSON liviano (_recent, 100 días) deja de traer K 100 días después del encendido: entonces ninguna serie de
    esa ventana cruza el cambio y la marca no se dibuja (no se corre al primer día de la ventana). Una caída a K
    posterior al encendido tampoco cuenta como «K antes»."""
    assert _primera([VIA1, VIA2]) is None
    assert _primera([CAIDA, VIA2]) is None


def test_notar_records_guarda_la_menor_de_todos_los_volcanes_y_pone_el_aviso_una_vez():
    js = REQ + f"""
    const d = docFalso();
    // como un nodo de texto del navegador: se lee y se corrige por nodeValue
    d.createTextNode = t => ({{ tag: "#text", nodeValue: t, get text() {{ return this.nodeValue; }} }});
    const a = M.notarRecords({json.dumps([K1, VIA2])}, d);
    const b = M.notarRecords({json.dumps([K1, VIA1])}, d);
    const c = M.notarRecords({json.dumps([K1, K2])}, d);
    const aviso = d.getElementById("aviso-cambio-via-modis");
    const n = d.body.children.filter(x => x.id === "aviso-cambio-via-modis").length;
    process.stdout.write(JSON.stringify([a, b, c, M.viaModisDesde(), n, aviso ? texto(aviso) : null]));
    """
    a, b, c, desde, n, txt = node(js)
    assert a == "2026-11-06T07:20:00.000Z" and b == c == desde == "2026-11-04T03:10:00.000Z"
    assert n == 1
    assert "4 nov 2026" in txt and "MODIS" in txt and "vía «código MIROVA»" in txt
    assert "la magnitud de MODIS sube" in txt and "aparecen alertas que K callaba" in txt
    assert "Chillán" in txt and "la erupción crece" in txt
    assert "—" not in txt and "–" not in txt          # sin guiones largos ni medios (regla del usuario)


def test_sin_records_de_la_via_notar_no_pone_aviso_ni_dibuja():
    js = REQ + f"""
    const d = docFalso();
    const r = M.notarRecords({json.dumps([K1, K2, V375, CAIDA])}, d);
    const c = chartFalso("time", 0, 4e12); c.data = {{ datasets: [{{ label: "MODIS (1km)" }}] }};
    process.stdout.write(JSON.stringify([r, d.body.children.length, M.crearPluginViaModis().afterDatasetsDraw(c)]));
    """
    assert node(js) == [None, 1, False]


def _dibuja(etiquetas, ocultos=()):
    t = "Date.parse('2026-11-04T03:10:00Z')"
    js = REQ + f"""
    const d = docFalso();
    M.notarRecords({json.dumps([K1, VIA1])}, d);
    const c = chartFalso("time", {t} - 5*86400000, {t} + 5*86400000);
    c.data = {{ datasets: {json.dumps([{"label": e} if e is not None else {} for e in etiquetas])} }};
    const ocultos = {json.dumps(list(ocultos))};
    c.isDatasetVisible = i => !ocultos.includes(i);
    const r = M.crearPluginViaModis().afterDatasetsDraw(c);
    const textos = c.trazos.filter(x => x[0] === "fillText").map(x => x[1]);
    process.stdout.write(JSON.stringify([r, textos]));
    """
    return node(js)


def test_la_linea_va_solo_en_las_series_de_modis():
    assert _dibuja(["MODIS (1km)", "VIIRS 375m"])[0] is True                   # index
    assert _dibuja(["MODIS (1 km)", "MIROVA MODIS (ref.)"])[0] is True         # diario
    assert _dibuja([None])[0] is True, "mosaico: una sola serie sin rótulo que suma los tres sensores"
    assert _dibuja(["VIIRS 375m", "VIIRS 750m", "MIROVA ref."])[0] is False
    assert _dibuja(["MIROVA MODIS (ref.)"])[0] is False, "la referencia de MIROVA no es nuestra serie de MODIS"
    assert _dibuja(["MODIS (1km)", "VIIRS 375m"], ocultos=[0])[0] is False, "MODIS oculto en la leyenda"
    r, textos = _dibuja(["MODIS (1km)"])
    assert textos == ["MODIS: vía MIROVA"]


def test_camino_del_navegador_registra_el_plugin_de_modis(tmp_path):
    src = MODULO.read_text(encoding="utf-8")
    archivo = tmp_path / "cd.js"
    archivo.write_text(src, encoding="utf-8")
    js = r"""
    const src = require('fs').readFileSync(process.argv[process.argv.length - 1], 'utf8');
    const registrados = [];
    const d = docFalso();
    const ventana = { Chart: { register: p => registrados.push(p.id) }, document: d };
    new Function("window", "module", src)(ventana, undefined);
    ventana.CambioDetector.notarRecords([%s, %s]);
    const aviso = d.getElementById("aviso-cambio-via-modis");
    process.stdout.write(JSON.stringify([registrados, !!aviso]));
    """ % (json.dumps(K1), json.dumps(VIA1))
    registrados, hay_aviso = node(js, str(archivo))
    assert "cambioViaModis" in registrados and hay_aviso is True


def test_las_tres_vistas_le_pasan_los_records_al_modulo_sin_copiar_su_logica():
    for v in VISTAS:
        src = (RAIZ / "frontend" / v).read_text(encoding="utf-8")
        llamadas = re.findall(r"CambioDetector\.notarRecords\(", src)
        assert len(llamadas) == 1, f"{v}: {len(llamadas)} llamadas a notarRecords"
        assert "via_codigo_mirova" not in src, f"{v} copia la lógica de la marca (A102)"


def test_las_llamadas_no_corren_las_lineas_de_las_vistas():
    """Las citas archivo:línea del CLAUDE.md (guard G8) apuntan a index.html; la llamada va en una línea existente."""
    import subprocess
    for v in VISTAS:
        r = subprocess.run(["git", "show", f"pre-s171-adopcion-modd:frontend/{v}"], cwd=RAIZ, capture_output=True,
                           text=True, encoding="utf-8")
        if r.returncode != 0:
            pytest.skip("sin el tag pre-s171-adopcion-modd en este checkout")
        antes = len(r.stdout.splitlines())
        ahora = len((RAIZ / "frontend" / v).read_text(encoding="utf-8").splitlines())
        assert antes == ahora, f"{v}: {antes} -> {ahora} líneas"
