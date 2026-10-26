"""frontend/cambio_detector.js (S153, adopción de K): la marca visible de la fecha del cambio de detector.

POR QUÉ: con K la publicación de VIIRS 375 en negativos limpios cae de 85 a 88 % a 2,5 a 3,7 % y su magnitud baja en
las pasadas que cambian (experiments/_s153_fk_v2/). Sin marca, el escalón en la tendencia se lee como un cambio del
volcán (REGLA_ADOPCION.md §4.8). Se prueba el módulo tal como se publica, con node, y también el camino del navegador
(registro del plugin y aviso en la página) con la constante completada, que es como quedará el día del merge.
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
MODULO = RAIZ / "frontend" / "cambio_detector.js"
VISTAS = ["index.html", "diario.html", "mosaico.html"]
HAY_NODE = shutil.which("node") is not None
FECHA = "2026-10-19T14:05:00Z"

# DOM y Chart mínimos: lo justo para que insertarAviso y el plugin corran sin navegador.
DOM_FALSO = r"""
function el(tag) {
  return { tag, id: "", style: {}, attrs: {}, children: [], parentNode: null, nextSibling: null,
    setAttribute(k, v) { this.attrs[k] = v; },
    appendChild(c) { c.parentNode = this; this.children.push(c); return c; },
    insertBefore(c, ref) { c.parentNode = this; const i = ref ? this.children.indexOf(ref) : -1;
      if (i < 0) this.children.push(c); else this.children.splice(i, 0, c); return c; } };
}
function docFalso() {
  const body = el("body"), header = el("header");
  body.appendChild(header);
  const todos = [];
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


def node(js, *args):
    r = subprocess.run(["node", "-e", DOM_FALSO + js, *args], capture_output=True, text=True,
                       encoding="utf-8", timeout=60)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


pytestmark = pytest.mark.skipif(not HAY_NODE, reason="el módulo se prueba con node")


def test_las_tres_vistas_cargan_el_modulo_despues_de_chartjs():
    for v in VISTAS:
        src = (RAIZ / "frontend" / v).read_text(encoding="utf-8")
        i_mod = src.find('<script src="cambio_detector.js"></script>')
        i_chart = src.find("chart.umd")
        assert i_mod > 0, f"{v} no carga cambio_detector.js"
        assert 0 < i_chart < i_mod, f"{v}: el módulo tiene que cargarse después de Chart.js para registrar el plugin"


def test_la_constante_existe_y_es_null_o_fecha_iso():
    src = MODULO.read_text(encoding="utf-8")
    assert re.search(r"^\s*const CAMBIO_DETECTOR_UTC = (null|\"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?Z\");", src, re.M)
    (v,) = node(f"const M = require({json.dumps(str(MODULO))}); process.stdout.write(JSON.stringify([M.CAMBIO_DETECTOR_UTC]));")
    assert v is None or re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?Z", v)


def test_sin_fecha_no_hay_aviso_ni_linea():
    js = f"""
    const M = require({json.dumps(str(MODULO))});
    const d = docFalso(); const c = chartFalso("time", 0, 1e13);
    const dibujo = M.crearPlugin(null).afterDatasetsDraw(c);
    process.stdout.write(JSON.stringify([M.textoAviso(null), M.insertarAviso(d, null), d.body.children.length, dibujo]));
    """
    assert node(js) == [None, None, 1, False]


def test_con_fecha_el_aviso_aparece_despues_del_header_y_dice_lo_que_debe():
    js = f"""
    const M = require({json.dumps(str(MODULO))});
    const d = docFalso();
    const e = M.insertarAviso(d, {json.dumps(FECHA)}, {json.dumps(FECHA)});
    M.insertarAviso(d, {json.dumps(FECHA)}, {json.dumps(FECHA)});   // idempotente: no duplica
    process.stdout.write(JSON.stringify([texto(e), d.body.children.map(c => c.tag), e.id]));
    """
    txt, hijos, ident = node(js)
    # S155: el aviso nombra la fecha de observación de los datos (frontera) y, aparte, la de producción.
    assert txt.startswith("Los datos con fecha de observación desde el 19 oct 2026 son del detector K (sin el Test 1 "
                          "integrado; ver ficha SDA) y los anteriores, del detector C0; la réplica corre K en producción "
                          "desde el 19 oct 2026 14:05 UTC. Las series que crucen el 19 oct 2026 mezclan dos detectores")
    assert "Ficha SDA" in txt
    assert hijos == ["header", "div"] and ident == "aviso-cambio-detector"


def test_la_linea_vertical_se_dibuja_solo_en_ejes_de_tiempo_y_dentro_del_rango():
    t = "Date.parse(%s)" % json.dumps(FECHA)
    js = f"""
    const M = require({json.dumps(str(MODULO))});
    const p = M.crearPlugin({json.dumps(FECHA)});
    const dentro = chartFalso("time", {t} - 5*86400000, {t} + 5*86400000);
    const fuera = chartFalso("time", {t} + 86400000, {t} + 9*86400000);
    const lineal = chartFalso("linear", 0, 1e13);
    const r = [p.afterDatasetsDraw(dentro), p.afterDatasetsDraw(fuera), p.afterDatasetsDraw(lineal)];
    const mov = dentro.trazos.filter(x => x[0] === "moveTo")[0];
    process.stdout.write(JSON.stringify([r, mov]));
    """
    r, mov = node(js)
    assert r == [True, False, False]
    assert mov == ["moveTo", 100, 10]   # a mitad del rango, desde el borde superior del área


def test_camino_del_navegador_con_la_constante_completada(tmp_path):
    """Lo que pasará el día del merge: se completa la constante y el módulo, cargado como <script>, registra el
    plugin en Chart.js y pone el aviso en la página. Si el registro o el aviso dejaran de ocurrir, falla."""
    src = MODULO.read_text(encoding="utf-8")
    # S154: la constante ya está completada con la hora del merge de #850; se reemplaza el valor que tenga (null o fecha).
    completado, n = re.subn(r'const CAMBIO_DETECTOR_UTC = (null|"[^"]*");', f"const CAMBIO_DETECTOR_UTC = {json.dumps(FECHA)};", src)
    assert n == 1
    # S155: la línea y el aviso dependen además de la frontera de los datos; también se completa.
    completado, n = re.subn(r'const DATOS_K_DESDE_UTC = (null|"[^"]*");', f"const DATOS_K_DESDE_UTC = {json.dumps(FECHA)};", completado)
    assert n == 1
    archivo = tmp_path / "cambio_detector_completado.js"
    archivo.write_text(completado, encoding="utf-8")
    js = r"""
    const src = require('fs').readFileSync(process.argv[process.argv.length - 1], 'utf8');
    const registrados = [];
    const d = docFalso();
    const ventana = { Chart: { register: p => registrados.push(p.id) }, document: d };
    new Function("window", "module", src)(ventana, undefined);
    const aviso = d.getElementById("aviso-cambio-detector");
    process.stdout.write(JSON.stringify([registrados, ventana.CAMBIO_DETECTOR_UTC, aviso ? texto(aviso).slice(0, 41) : null]));
    """
    registrados, const, aviso = node(js, str(archivo))
    assert registrados == ["cambioDetector"]
    assert const == FECHA
    assert aviso == "Los datos con fecha de observación desde "


def test_el_modulo_no_toca_el_criterio_de_publicacion():
    src = MODULO.read_text(encoding="utf-8")
    codigo = "\n".join(l for l in src.splitlines() if not l.lstrip().startswith("//"))
    for nombre in ("isValidDetection", "mirovaEqVrp", "latestDetection"):
        assert nombre not in codigo
