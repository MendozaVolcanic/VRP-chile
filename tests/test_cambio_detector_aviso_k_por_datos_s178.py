"""frontend/cambio_detector.js (S178, decisión b3 de Nicolás): el aviso del detector K y su línea salen de los DATOS.

POR QUÉ: el aviso decía «los datos desde el 15 feb 2025 son de K y los anteriores, del detector C0», pero desde #883
(S158) no hay ningún record anterior al 2025-02-15 en data/mirova_equivalent/: describía algo que no está. Se quedó
tres semanas en pantalla porque su prueba vigilaba la fecha de la frontera, no que existiera algo al otro lado
(lección S177). Ahora el aviso y la línea aparecen sólo si las vistas le pasan (notarRecords, la misma llamada de las
marcas de la vía) algún record con fecha de observación anterior a DATOS_K_DESDE_UTC; si un dato así vuelve, el aviso
vuelve solo. La constante NO se borra: scripts/vigilancia_sombra.py y scripts/auto_audit_weekly.py la leen como
frontera, y sin ella la vigilancia se declara ciega.
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
MODULO = RAIZ / "frontend" / "cambio_detector.js"
HAY_NODE = shutil.which("node") is not None

pytestmark = pytest.mark.skipif(not HAY_NODE, reason="el módulo se prueba con node")

# DOM y Chart mínimos, como en tests/test_cambio_detector_s153.py.
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
function cargar() {
  const src = require('fs').readFileSync(process.argv[process.argv.length - 1], 'utf8');
  const registrados = [];
  const d = docFalso();
  const ventana = { Chart: { register: p => registrados.push(p), instances: {} }, document: d };
  new Function("window", "module", src)(ventana, undefined);
  const pK = registrados.filter(p => p.id === "cambioDetector")[0];
  return { ventana, d, pK, M: ventana.CambioDetector };
}
function dibujaLinea(pK, utc) {
  const t = Date.parse(utc);
  const trazos = [];
  const ctx = new Proxy({}, { get: (o, k) => (k in o ? o[k] : (...a) => trazos.push([k, ...a])),
                              set: (o, k, v) => { o[k] = v; return true; } });
  const chart = { ctx, chartArea: { top: 10, bottom: 110, left: 0, right: 200 },
    scales: { x: { type: "time", min: t - 5 * 86400000, max: t + 5 * 86400000,
                   getPixelForValue: v => (v - (t - 5 * 86400000)) / (10 * 86400000) * 200 } } };
  return [pK.afterDatasetsDraw(chart), trazos.filter(x => x[0] === "moveTo")[0] || null];
}
"""


def node(js):
    r = subprocess.run(["node", "-e", DOM_FALSO + js, str(MODULO)], capture_output=True, text=True,
                       encoding="utf-8", timeout=60)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def _desde():
    m = re.search(r'^\s*const DATOS_K_DESDE_UTC = "(\d{4}-\d{2}-\d{2})T00:00:00Z";', MODULO.read_text(encoding="utf-8"),
                  re.M)
    assert m, "la constante tiene que seguir declarada: la leen la vigilancia de la sombra y el auto-audit"
    return m.group(1)


def test_al_cargar_no_hay_aviso_k_ni_linea():
    """Sin records, la página no muestra el aviso K ni dibuja su línea (antes los ponía siempre al cargar)."""
    aviso, (dibujo, mov) = node(r"""
    const { d, pK, M } = cargar();
    process.stdout.write(JSON.stringify([!!d.getElementById("aviso-cambio-detector"), dibujaLinea(pK, M.DATOS_K_DESDE_UTC)]));
    """)
    assert aviso is False
    assert dibujo is False and mov is None


def test_records_desde_la_frontera_no_ponen_el_aviso():
    """Lo que pasa hoy: todos los records son del 2025-02-15 o posteriores (K o vía). Ni aviso ni línea."""
    desde = _desde()
    aviso, (dibujo, mov) = node(r"""
    const { d, pK, M } = cargar();
    M.notarRecords([{ sensor: "VIIRS_NOAA20", datetime_utc: "%s 05:12" },
                    { sensor: "MODIS_AQUA", datetime_utc: "2026-11-09 06:40", via_codigo_mirova: true }], d);
    process.stdout.write(JSON.stringify([!!d.getElementById("aviso-cambio-detector"), dibujaLinea(pK, M.DATOS_K_DESDE_UTC)]));
    """ % desde)
    assert aviso is False
    assert dibujo is False and mov is None


def test_un_record_anterior_a_la_frontera_trae_el_aviso_y_la_linea():
    """Control positivo: si un record C0 volviera a la serie, el aviso y la línea vuelven solos, en la frontera."""
    aviso, (dibujo, mov) = node(r"""
    const { d, pK, M } = cargar();
    M.notarRecords([{ sensor: "VIIRS_NOAA20", datetime_utc: "2025-02-14 23:59" }], d);
    const a = d.getElementById("aviso-cambio-detector");
    process.stdout.write(JSON.stringify([a ? texto(a) : null, dibujaLinea(pK, M.DATOS_K_DESDE_UTC)]));
    """)
    assert aviso and aviso.startswith("Los datos con fecha de observación desde el 15 feb 2025"), aviso
    assert dibujo is True and mov == ["moveTo", 100, 10]


def test_un_record_sin_fecha_no_cuenta_como_anterior():
    aviso = node(r"""
    const { d, M } = cargar();
    M.notarRecords([{ sensor: "VIIRS_NOAA20", datetime_utc: "" }, { sensor: "MODIS_TERRA" }, null], d);
    process.stdout.write(JSON.stringify(!!d.getElementById("aviso-cambio-detector")));
    """)
    assert aviso is False
