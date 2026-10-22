# -*- coding: utf-8 -*-
"""frontend/cese_plataformas.js (S159): aviso al operador del cese de Suomi NPP en las tres vistas live.

POR QUÉ: desde el 2026-11-02 13:00 UTC Suomi NPP deja de entregar datos. VIIRS sigue con NOAA-20 y NOAA-21, así que
hay una mirada menos al volcán por noche y un foco débil que sólo se veía en una pasada tiene menos probabilidad de
publicarse. Sin aviso, la caída de puntos VIIRS en la tendencia se lee como un cambio del volcán, y las series de
Suomi NPP desaparecen de la leyenda sin explicación. Se prueba el módulo tal como se publica, con node: el texto
antes y después de la fecha, que el corte no dependa de la zona horaria del computador del operador (el proyecto ya
tuvo un bug de zona horaria en el frontend), la línea vertical y el camino del navegador.
"""
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
MODULO = RAIZ / "frontend" / "cese_plataformas.js"
VISTAS = ["index.html", "diario.html", "mosaico.html"]
HAY_NODE = shutil.which("node") is not None
CESE = "2026-11-02T13:00:00Z"

DOM_FALSO = r"""
function el(tag) {
  return { tag, id: "", style: {}, attrs: {}, children: [], parentNode: null, nextSibling: null,
    setAttribute(k, v) { this.attrs[k] = v; },
    appendChild(c) { c.parentNode = this; this.children.push(c); return c; },
    insertBefore(c, ref) { c.parentNode = this; const i = ref ? this.children.indexOf(ref) : -1;
      if (i < 0) this.children.push(c); else this.children.splice(i, 0, c); return c; } };
}
function docFalso(conAvisoK) {
  const body = el("body"), header = el("header");
  body.appendChild(header);
  const todos = [];
  if (conAvisoK) { const k = el("div"); k.id = "aviso-cambio-detector"; body.appendChild(k); todos.push(k); }
  for (let i = 0; i < body.children.length; i++) body.children[i].nextSibling = body.children[i + 1] || null;
  return { body, readyState: "complete", addEventListener() {},
    createElement(t) { const e = el(t); todos.push(e); return e; },
    createTextNode(t) { return { tag: "#text", text: t }; },
    querySelector(s) { return s === "header" ? header : null; },
    getElementById(id) { return todos.find(e => e.id === id) || null; } };
}
function texto(e) { return (e.children || []).map(c => c.tag === "#text" ? c.text : texto(c)).join(""); }
function chartFalso(tipo, min, max) {
  const trazos = [];
  const ctx = new Proxy({}, { get: (o, k) => (k in o ? o[k] : (...a) => trazos.push([k, ...a])),
                              set: (o, k, v) => { o[k] = v; return true; } });
  return { trazos, ctx, chartArea: { top: 10, bottom: 110, left: 0, right: 200 },
    scales: { x: { type: tipo, min, max, getPixelForValue: t => (t - min) / (max - min) * 200 } } };
}
"""


def node(js, *args, tz=None):
    env = dict(os.environ)
    if tz:
        env["TZ"] = tz
    r = subprocess.run(["node", "-e", DOM_FALSO + js, *args], capture_output=True, text=True,
                       encoding="utf-8", timeout=60, env=env)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def _req():
    return f"const M = require({json.dumps(str(MODULO))});"


pytestmark = pytest.mark.skipif(not HAY_NODE, reason="el módulo se prueba con node")


def test_las_tres_vistas_cargan_el_modulo_despues_de_chartjs_y_del_aviso_de_k():
    for v in VISTAS:
        src = (RAIZ / "frontend" / v).read_text(encoding="utf-8")
        i_mod = src.find('<script src="cese_plataformas.js"></script>')
        i_k = src.find('<script src="cambio_detector.js"></script>')
        i_chart = src.find("chart.umd")
        assert i_mod > 0, f"{v} no carga cese_plataformas.js"
        assert 0 < i_chart < i_mod, f"{v}: el módulo tiene que cargarse después de Chart.js para registrar el plugin"
        assert 0 < i_k < i_mod, f"{v}: el aviso del cese va después del aviso del detector K"


def test_comparacion_no_lleva_el_aviso_porque_es_preview():
    src = (RAIZ / "frontend" / "comparacion.html").read_text(encoding="utf-8")
    assert "cese_plataformas.js" not in src


def test_la_fecha_y_la_fuente_son_las_de_la_lista_de_ceses():
    ceses = json.loads((RAIZ / "scripts" / "ceses_esperados.json").read_text(encoding="utf-8"))["ceses"]
    snpp = next(c for c in ceses if c["plataforma"] == "Suomi NPP")
    v = node(_req() + "process.stdout.write(JSON.stringify([M.CESE_UTC, M.FUENTE_URL, M.PLATAFORMA]));")
    assert v == [snpp["desde_utc"], snpp["fuente"], "Suomi NPP"]


def test_antes_del_cese_avisa_en_futuro_y_despues_en_pasado():
    js = _req() + """
    const t = s => Date.parse(s);
    process.stdout.write(JSON.stringify([
      M.textoAviso(t("2026-10-25T12:00:00Z")),
      M.textoAviso(t("2026-11-02T12:59:59Z")),
      M.textoAviso(t("2026-11-02T13:00:00Z")),
      M.textoAviso(t("2026-11-20T00:00:00Z")),
    ]));"""
    antes, borde_antes, borde_despues, despues = node(js)
    assert antes == borde_antes
    assert antes.startswith("Aviso de NASA: el satélite Suomi NPP dejará de entregar datos el 2 nov 2026 a las "
                            "13:00 UTC.")
    assert "una pasada VIIRS menos por noche" in antes and "NOAA-20 y NOAA-21" in antes
    assert borde_despues == despues
    assert despues.startswith("Desde el 2 nov 2026 a las 13:00 UTC, el satélite Suomi NPP dejó de entregar datos "
                              "(aviso de NASA).")
    assert "una pasada VIIRS menos por noche" in despues
    assert "Las series anteriores al 2 nov 2026 no cambian." in despues
    for txt in (antes, despues):
        assert "\u2014" not in txt and "\u2013" not in txt   # guiones largo y medio
        assert not re.search(r"\b(tenés|podés|mirá|fijate)\b", txt)


def test_el_aviso_se_retira_a_los_90_dias_del_cese():
    js = _req() + """
    const t = s => Date.parse(s);
    process.stdout.write(JSON.stringify([M.DIAS_AVISO_DESPUES,
      M.textoAviso(t("2027-01-31T12:59:00Z")) !== null, M.textoAviso(t("2027-01-31T13:00:00Z"))]));"""
    assert node(js) == [90, True, None]


@pytest.mark.parametrize("tz", ["America/Santiago", "Asia/Tokyo", "Pacific/Kiritimati", "UTC"])
def test_el_corte_no_depende_de_la_zona_horaria_del_navegador(tz):
    js = _req() + """
    const t = s => Date.parse(s);
    const a = M.textoAviso(t("2026-11-02T12:59:00Z")), b = M.textoAviso(t("2026-11-02T13:01:00Z"));
    process.stdout.write(JSON.stringify([a.slice(0, 40), b.slice(0, 40)]));"""
    assert node(js, tz=tz) == ["Aviso de NASA: el satélite Suomi NPP dej", "Desde el 2 nov 2026 a las 13:00 UTC, el "]


def test_el_aviso_va_despues_del_aviso_de_k_es_idempotente_y_enlaza_a_nasa():
    js = _req() + """
    const ahora = Date.parse("2026-11-03T00:00:00Z");
    const d = docFalso(true);
    const e = M.insertarAviso(d, ahora);
    M.insertarAviso(d, ahora);
    const a = e.children.find(c => c.tag === "a");
    const d2 = docFalso(false);
    M.insertarAviso(d2, ahora);
    process.stdout.write(JSON.stringify([d.body.children.map(c => c.id || c.tag), e.id, a.href, texto(e),
      d2.body.children.map(c => c.id || c.tag), e.attrs.role]));"""
    hijos, ident, href, txt, hijos2, rol = node(js)
    assert hijos == ["header", "aviso-cambio-detector", "aviso-cese-plataformas"]
    assert ident == "aviso-cese-plataformas" and rol == "note"
    assert href.startswith("https://www.earthdata.nasa.gov/")
    assert txt.endswith("Aviso de NASA")
    assert hijos2 == ["header", "aviso-cese-plataformas"]


def test_pasado_el_plazo_no_inserta_nada():
    js = _req() + """
    const d = docFalso(false);
    process.stdout.write(JSON.stringify([M.insertarAviso(d, Date.parse("2027-06-01T00:00:00Z")),
      d.body.children.length]));"""
    assert node(js) == [None, 1]


def test_la_linea_vertical_se_dibuja_solo_en_ejes_de_tiempo_y_dentro_del_rango():
    t = "Date.parse(%s)" % json.dumps(CESE)
    js = _req() + f"""
    const p = M.crearPlugin({json.dumps(CESE)});
    const dentro = chartFalso("time", {t} - 5*86400000, {t} + 5*86400000);
    const fuera = chartFalso("time", {t} - 9*86400000, {t} - 86400000);
    const lineal = chartFalso("linear", 0, 1e13);
    const r = [p.afterDatasetsDraw(dentro), p.afterDatasetsDraw(fuera), p.afterDatasetsDraw(lineal)];
    const mov = dentro.trazos.filter(x => x[0] === "moveTo")[0];
    const rot = dentro.trazos.filter(x => x[0] === "fillText")[0];
    process.stdout.write(JSON.stringify([r, mov, rot && rot[1], p.id]));
    """
    r, mov, rotulo, ident = node(js)
    assert r == [True, False, False]
    assert mov == ["moveTo", 100, 10]
    assert rotulo == "sin Suomi NPP" and ident == "cesePlataformas"


def test_camino_del_navegador_registra_el_plugin_y_pone_el_aviso():
    js = r"""
    const src = require('fs').readFileSync(process.argv[process.argv.length - 1], 'utf8');
    const registrados = [];
    const d = docFalso(false);
    const ventana = { Chart: { register: p => registrados.push(p.id) }, document: d,
                      Date: { now: () => Date.parse("2026-10-25T00:00:00Z") } };
    new Function("window", "module", src)(ventana, undefined);
    const aviso = d.getElementById("aviso-cese-plataformas");
    process.stdout.write(JSON.stringify([registrados, aviso ? texto(aviso).slice(0, 14) : null]));
    """
    assert node(js, str(MODULO)) == [["cesePlataformas"], "Aviso de NASA:"]
