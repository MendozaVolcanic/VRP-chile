# -*- coding: utf-8 -*-
"""Auditoría externa con Codex, ronda 4, frente E+F (S199): un archivo que no se lee afecta sólo a su volcán y lo dice.

POR QUÉ. R4FEF-109 (gravedad 3): `fetchJSON` devolvía `r.json()` sin esperarlo, así que un JSON cortado o inválido
rechazaba fuera del try; el Promise.all de la carga caía entero y bastaba UN archivo (de un volcán, de MIROVA o de la
sombra de los 34) para que index.html quedara con 0 de 43 tarjetas y mosaico.html en «Cargando…». El geólogo de turno
perdía también los volcanes cuyos datos estaban bien. R4FEF-106 (gravedad 3): frontend/cobertura.js guardaba en caché
toda la sesión la falla y la lectura buena; con el archivo ilegible el aviso quedaba vacío, igual que «todo medido», y un
hueco nuevo de NASA nunca aparecía en una página abierta. Detalle: D:\\codex-vrp\\_salida\\ronda4\\fef_r4\\INFORME.md y
D:\\codex-vrp\\_salida\\ronda4\\fef_r4_verificacion\\VEREDICTO.md.

QUÉ FIJA, ejecutando con node el JavaScript real de las páginas (los <script> en línea y los módulos locales que cada
página incluye, en su orden) en un DOM mínimo, con un fetch que sirve datos sintéticos y falla a pedido:
(1) index.html: con el JSON de Llaima, el de MIROVA de Llaima o la sombra de Antuco cortados, monta las 43 tarjetas; sólo
    la del volcán afectado dice «no se pudo leer» y el encabezado no dice «Sistema Operativo». Control: sin fallas, 43
    tarjetas, ningún aviso y «Sistema Operativo».
(2) index.html, sondeo de 5 min: si un archivo que ya se leyó deja de leerse, la tarjeta lo avisa y conserva los datos
    leídos antes; cuando se vuelve a leer, el aviso se va.
(3) mosaico.html: con el JSON de Llaima cortado monta las 11 tarjetas y la cabecera dice que faltó un archivo.
(4) diario.html: con el JSON de Llaima cortado monta las 11 tarjetas y la de Llaima dice «no cargó» (ya lo hacía: se fija).
(5) cobertura.js: con el archivo ilegible el aviso dice «cobertura no disponible» (en la tarjeta y en la lista); la falla
    no queda en caché (la llamada siguiente vuelve a pedir el archivo y pinta lo que trae); una lectura buena se relee al
    vencer VIGENCIA_MS y repintar() muestra un hueco nuevo sin redibujar la página. Control: archivo sano y vacío no pinta.
(6) miniaturas.js: un índice ilegible deja el panel con «No se pudo leer el índice de miniaturas» en vez de quitarlo; un
    404 (volcán sin miniaturas) sigue sin mostrar nada.

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) ¿Fallaría con el código de antes? Sí: con frontend/ de origin/main previo a este
cambio, (1) da 0 tarjetas (init rechaza), (3) queda en «Cargando…», (5) deja el aviso vacío y hace una sola petición
(comprobado al escribirla, en un worktree de origin/main). (2) ¿Y si la carga muriera? El harness exige returncode 0,
cuenta los errores de cada <script> y cada caso exige su número de tarjetas; un DOM que no monta da 0 y cae.
"""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
FRONT = RAIZ / "frontend"

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="el tablero se prueba con node")

HARNESS = r"""
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm');
const IN = JSON.parse(fs.readFileSync(0, 'utf8'));
const AHORA = Date.parse(IN.ahora);
const RECHAZOS = [];   // una promesa rechazada sin atrapar (el defecto de R4FEF-109) no debe matar al harness: se cuenta
process.on('unhandledRejection', e => RECHAZOS.push(String(e && e.message || e)));

// ---------- DOM mínimo ----------
function crearElemento(tag, doc) {
  const e = { tagName: String(tag || 'div').toUpperCase(), nodeType: 1, children: [], parentNode: null, _text: '',
    className: '', id: '', title: '', style: {}, dataset: {}, attrs: {}, isConnected: true, value: '', options: [],
    hidden: false, href: '', innerHTML: '' };
  const clases = new Set();
  e.classList = { add: (...c) => c.forEach(x => clases.add(x)), remove: (...c) => c.forEach(x => clases.delete(x)),
    toggle: (c, f) => { const on = f === undefined ? !clases.has(c) : f; on ? clases.add(c) : clases.delete(c); return on; },
    contains: c => clases.has(c) };
  Object.defineProperty(e, 'textContent', { get() { return e._text + e.children.map(c => c.textContent).join(''); },
    set(v) { e._text = v == null ? '' : String(v); e.children = []; } });
  Object.defineProperty(e, 'innerText', { get() { return e.textContent; }, set(v) { e.textContent = v; } });
  Object.defineProperty(e, 'firstChild', { get() { return e.children[0] || null; } });
  Object.defineProperty(e, 'lastChild', { get() { return e.children[e.children.length - 1] || null; } });
  e.appendChild = c => { if (c && typeof c === 'object') { c.parentNode = e; e.children.push(c); } return c; };
  e.append = (...cs) => cs.forEach(c => e.appendChild(typeof c === 'string' ? doc.createTextNode(c) : c));
  e.prepend = (...cs) => cs.reverse().forEach(c => { const n = typeof c === 'string' ? doc.createTextNode(c) : c; n.parentNode = e; e.children.unshift(n); });
  e.insertBefore = (c, ref) => { const i = e.children.indexOf(ref); c.parentNode = e; if (i < 0) e.children.push(c); else e.children.splice(i, 0, c); return c; };
  e.removeChild = c => { const i = e.children.indexOf(c); if (i >= 0) e.children.splice(i, 1); c.isConnected = false; return c; };
  e.remove = () => { if (e.parentNode) e.parentNode.removeChild(e); e.isConnected = false; };
  e.replaceChildren = (...cs) => { e.children = []; e._text = ''; e.append(...cs); };
  e.setAttribute = (k, v) => { e.attrs[k] = String(v); if (k === 'id') e.id = String(v); };
  e.getAttribute = k => (k in e.attrs ? e.attrs[k] : null);
  e.removeAttribute = k => { delete e.attrs[k]; };
  e.addEventListener = () => {}; e.removeEventListener = () => {}; e.dispatchEvent = () => true;
  e.insertAdjacentHTML = (pos, h) => { e.innerHTML += h; };
  e.querySelector = () => crearElemento('div', doc); e.querySelectorAll = () => []; e.getElementsByTagName = () => [];
  e.closest = () => null; e.contains = () => false; e.scrollIntoView = () => {}; e.focus = () => {}; e.click = () => {};
  e.getBoundingClientRect = () => ({ left: 0, top: 0, width: 100, height: 100, right: 100, bottom: 100 });
  e.getContext = () => new Proxy({}, { get: (t, k) => (k === 'canvas' ? e : () => ({ data: [] })) });
  return e;
}
function crearDocumento() {
  const doc = { _porId: {} };
  doc.createElement = t => crearElemento(t, doc);
  doc.createTextNode = s => { const n = crearElemento('#text', doc); n.nodeType = 3; n.textContent = s; return n; };
  doc.createDocumentFragment = () => crearElemento('#frag', doc);
  doc.getElementById = id => { if (!doc._porId[id]) { const e = crearElemento('div', doc); e.id = id; doc._porId[id] = e; } return doc._porId[id]; };
  doc.querySelector = s => (s === '.status-dot' ? doc.getElementById('__status_dot') : crearElemento('div', doc));
  doc.querySelectorAll = () => []; doc.addEventListener = () => {}; doc.removeEventListener = () => {};
  doc.head = crearElemento('head', doc); doc.body = crearElemento('body', doc); doc.documentElement = crearElemento('html', doc);
  return doc;
}

// ---------- datos sintéticos y fallas ----------
const hace = h => new Date(AHORA - h * 3600000).toISOString().slice(0, 16).replace('T', ' ');
function record(sensor) {
  return { datetime_utc: hace(6), sensor, vrp_mw: 0, n_anomalous_pixels: 0, distance_class: null, granule: 'g',
           product_version: 'nrt', t_bg_k: 250 };
}
function cuerpo(u, estado) {
  if (/data\/cobertura\/([^/?]+)\.json/.test(u)) {
    const v = decodeURIComponent(RegExp.$1);
    return JSON.stringify({ no_medidas: (estado.cobertura[v] || []) });
  }
  if (/mirova_equivalent\/[^/?]+\.json|sombra_34\/[^/?]+\.json/.test(u))
    return JSON.stringify({ updated: hace(1).replace(' ', 'T') + ':00Z', records: [record('VIIRS_NOAA20')] });
  if (/data\/mirova\/[^/?]+\.json/.test(u)) return JSON.stringify({ records: [] });
  return null;
}
function crearFetch(estado) {
  return async function fetch(url) {
    const u = String(url);
    estado.peticiones.push(u.split('?')[0]);
    const r = (status, txt) => ({ ok: status >= 200 && status < 300, status, headers: { get: () => null },
      text: async () => txt, json: async () => JSON.parse(txt) });
    for (const f of estado.fallas) {
      if (!new RegExp(f.patron).test(u)) continue;
      if (f.modo === 'red') throw new TypeError('Failed to fetch');
      if (f.modo === '404') return r(404, 'Not Found');
      if (f.modo === 'cortado') { const c = cuerpo(u, estado) || '{"records": ['; return r(200, c.slice(0, Math.floor(c.length / 2))); }
    }
    const c = cuerpo(u, estado);
    return c == null ? r(404, 'Not Found') : r(200, c);
  };
}

// ---------- carga de la página ----------
function cargarPagina(pagina, estado) {
  const html = fs.readFileSync(path.join(IN.front, pagina), 'utf8');
  const doc = crearDocumento();
  class Chart { constructor(ctx, cfg) { this.data = cfg && cfg.data; this.options = cfg && cfg.options; } destroy() {} update() {} static register() {} }
  Chart.Interaction = { modes: {} };
  Chart.defaults = new Proxy({}, { get: (t, k) => (t[k] = t[k] || {}), set: () => true });
  const L = new Proxy(function () {}, { get: (t, k) => (k === 'then' ? undefined : L), apply: () => L, construct: () => L });
  const intervalos = [];
  const DateReal = Date;
  class DateFijo extends DateReal {
    constructor(...a) { if (a.length === 0) super(estado.ahora); else super(...a); }
    static now() { return estado.ahora; }
  }
  DateFijo.parse = DateReal.parse; DateFijo.UTC = DateReal.UTC;
  const errores = [];
  const ctx = {
    console: { log() {}, warn() {}, info() {}, debug() {}, error: (...a) => errores.push('console.error ' + a.map(String).join(' ')) },
    document: doc, location: { search: '', pathname: '/frontend/' + pagina, hash: '', href: 'http://localhost/frontend/' + pagina },
    history: { replaceState() {}, pushState() {} }, navigator: { userAgent: 'node', clipboard: { writeText: async () => {} } },
    localStorage: { getItem: () => null, setItem() {}, removeItem() {} },
    sessionStorage: { getItem: () => null, setItem() {}, removeItem() {} },
    fetch: crearFetch(estado), Chart, L,
    requestAnimationFrame: f => { try { f(); } catch (e) {} return 1; }, cancelAnimationFrame() {},
    setTimeout: () => 1, clearTimeout() {},
    setInterval: (f, ms) => { intervalos.push({ f, ms }); return intervalos.length; }, clearInterval() {},
    getComputedStyle: () => ({ getPropertyValue: () => '' }),
    matchMedia: () => ({ matches: false, addEventListener() {}, addListener() {} }),
    Image: function () {}, URL, URLSearchParams, Blob: function () {}, Intl, Date: DateFijo, Math, JSON, Promise, Map, Set,
    Number, String, Array, Object, TextDecoder, TextEncoder, structuredClone, alert() {}, confirm: () => true,
    innerWidth: 1280, innerHeight: 900, devicePixelRatio: 1, removeEventListener() {},
    CustomEvent: class { constructor(type) { this.type = type; } },
  };
  const oyentes = {};   // eventos de window ("vrp-falla-capa" de cobertura.js y miniaturas.js)
  ctx.addEventListener = (t, f) => { (oyentes[t] = oyentes[t] || []).push(f); };
  ctx.dispatchEvent = e => { for (const f of oyentes[e.type] || []) f(e); return true; };
  ctx.window = ctx; ctx.self = ctx; ctx.globalThis = ctx;
  vm.createContext(ctx);
  const re = /<script(\s[^>]*)?>([\s\S]*?)<\/script>/g;
  let m;
  while ((m = re.exec(html))) {
    const src = /src="([^"]+)"/.exec(m[1] || '');
    if (src && /^https?:/.test(src[1])) continue;   // Chart.js y Leaflet: talones
    const codigo = src ? fs.readFileSync(path.join(IN.front, src[1]), 'utf8') : m[2];
    const nombre = src ? src[1] : pagina;
    // DOMContentLoaded no se dispara: init() se llama a mano.
    const sinArranque = codigo.replace(/document\.addEventListener\("DOMContentLoaded", init\);/, '').replace(/^init\(\);$/m, '');
    try { vm.runInContext(sinArranque, ctx, { filename: nombre }); } catch (e) { errores.push(nombre + ': ' + String(e)); }
  }
  return { ctx, doc, intervalos, errores, ev: c => vm.runInContext(c, ctx) };
}
const flush = async (n = 80) => { for (let i = 0; i < n; i++) await new Promise(r => setImmediate(r)); };
function buscar(e, pred, out = []) { if (!e) return out; if (pred(e)) out.push(e); for (const c of e.children || []) buscar(c, pred, out); return out; }
const clase = cls => e => typeof e.className === 'string' && (' ' + e.className + ' ').includes(' ' + cls + ' ');

async function pagina(caso) {
  const estado = { fallas: caso.fallas || [], cobertura: caso.cobertura || {}, peticiones: [], ahora: AHORA };
  const P = cargarPagina(caso.pagina, estado);
  let rechazo = null;
  try { await P.ev('init()'); } catch (e) { rechazo = String(e).slice(0, 160); }
  await flush();
  const out = { rechazo, errores: P.errores.filter(x => !/console\.error/.test(x)), sueltos: RECHAZOS.splice(0) };
  const leer = () => {
    const grid = P.doc.getElementById(caso.grid);
    const tarjetas = grid.children.filter(c => c.tagName !== '#TEXT');
    out.tarjetas = tarjetas.length;
    out.porVolcan = {};
    for (const n of caso.mirar || []) {
      const t = tarjetas.find(c => c.textContent.includes(n));
      out.porVolcan[n] = t ? t.textContent : null;
    }
    out.conFalla = tarjetas.filter(t => buscar(t, x => /falla-carga/.test(x.className || '')).length > 0 ||
                                        /no cargó/.test(t.textContent)).length;
    out.semaforo = P.doc.getElementById('status-text').textContent;
    out.cabecera = P.doc.getElementById('updated-label').textContent;
  };
  leer();
  if (caso.detalle) {
    P.ev('currentVolcano = VOLCANOES.find(x => x.name === ' + JSON.stringify(caso.detalle) + '); renderDetail();');
    await flush();
    out.detalle = P.doc.getElementById('detail').textContent;
    out.semaforo = P.doc.getElementById('status-text').textContent;
  }
  if (caso.refresco) {
    out.antes = Object.assign({}, out);
    for (const paso of caso.refresco) {
      estado.fallas = paso.fallas;
      const poll = P.intervalos.find(x => x.ms === 5 * 60 * 1000);
      let rechazoPoll = null;
      try { await poll.f(); } catch (e) { rechazoPoll = String(e).slice(0, 160); }
      await flush();
      leer();
      out['tras_' + paso.nombre] = { rechazo: rechazoPoll, tarjetas: out.tarjetas, porVolcan: Object.assign({}, out.porVolcan), semaforo: out.semaforo,
        records: P.ev('allData["Llaima"].records.length') };
    }
  }
  return out;
}
(async () => {
  const out = {};
  for (const [k, caso] of Object.entries(IN.casos)) out[k] = await pagina(caso);
  process.stdout.write(JSON.stringify(out));
})().catch(e => { console.error(e && e.stack || e); process.exit(1); });
"""

LLAIMA_PROPIO = r"mirova_equivalent/Llaima(_recent)?\.json"
LLAIMA_MIROVA = r"data/mirova/Llaima\.json"
ANTUCO_SOMBRA = r"sombra_34/Antuco\.json"


def _correr(casos):
    datos = {"front": str(FRONT), "ahora": "2026-11-25T07:00:00Z", "casos": casos}
    r = subprocess.run(["node", "-e", HARNESS], input=json.dumps(datos), capture_output=True, text=True,
                       encoding="utf-8", timeout=600)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def _index(fallas=None, **kw):
    return dict(pagina="index.html", grid="volcano-grid", fallas=fallas or [], mirar=["Llaima", "Villarrica", "Antuco"], **kw)


@pytest.fixture(scope="module")
def index():
    return _correr({
        "control": _index(detalle="Llaima"),
        "miniaturas": _index([{"patron": r"miniaturas/Llaima/indice\.json", "modo": "cortado"}], detalle="Llaima"),
        "propio": _index([{"patron": LLAIMA_PROPIO, "modo": "cortado"}]),
        "mirova": _index([{"patron": LLAIMA_MIROVA, "modo": "cortado"}]),
        "sombra": _index([{"patron": ANTUCO_SOMBRA, "modo": "cortado"}]),
        "cobertura": _index([{"patron": r"cobertura/Villarrica\.json", "modo": "cortado"}]),
        "refresco": _index(refresco=[{"nombre": "falla", "fallas": [{"patron": LLAIMA_PROPIO, "modo": "cortado"}]},
                                     {"nombre": "sana", "fallas": []}]),
    })


def test_index_control_sin_fallas(index):
    c = index["control"]
    assert c["rechazo"] is None and not c["errores"], (c["rechazo"], c["errores"])
    assert c["tarjetas"] == 43
    assert c["conFalla"] == 0
    assert c["semaforo"] == "Sistema Operativo"


@pytest.mark.parametrize("caso,volcan,texto", [
    ("propio", "Llaima", "sin datos: no se pudo leer su archivo (JSON ilegible"),
    ("mirova", "Llaima", "no se pudo leer la referencia de MIROVA (JSON ilegible"),
    ("sombra", "Antuco", "sin datos: no se pudo leer su archivo (JSON ilegible"),
])
def test_index_un_json_cortado_afecta_solo_a_su_volcan(index, caso, volcan, texto):
    r = index[caso]
    assert r["rechazo"] is None and not r["sueltos"], (r["rechazo"], r["sueltos"])
    assert r["tarjetas"] == 43, "un archivo cortado no puede apagar las otras tarjetas"
    assert r["conFalla"] == 1
    assert texto in r["porVolcan"][volcan], r["porVolcan"][volcan]
    otro = "Villarrica" if volcan != "Villarrica" else "Llaima"
    assert "no se pudo" not in r["porVolcan"][otro]
    assert r["semaforo"] != "Sistema Operativo", r["semaforo"]


def test_index_cobertura_ilegible_lo_dice_la_tarjeta_y_el_encabezado(index):
    r = index["cobertura"]
    assert r["rechazo"] is None and r["tarjetas"] == 43
    assert "cobertura no disponible" in r["porVolcan"]["Villarrica"], r["porVolcan"]["Villarrica"]
    assert "cobertura no disponible" not in r["porVolcan"]["Llaima"]
    assert r["semaforo"] == "Archivos sin leer: 1 volcán", r["semaforo"]
    assert "cobertura no disponible" not in index["control"]["porVolcan"]["Villarrica"]


def test_index_miniaturas_ilegibles_lo_dicen_y_no_apagan_el_panel_del_volcan(index):
    r = index["miniaturas"]
    assert r["rechazo"] is None and r["tarjetas"] == 43
    assert "No se pudo leer el índice de miniaturas (JSON ilegible)" in r["detalle"], r["detalle"][:300]
    assert "Llaima" in r["detalle"]
    assert "índice de miniaturas" not in index["control"]["detalle"], "control: sin índice (404) no se avisa nada"
    assert r["semaforo"] == "Archivos sin leer: 1 volcán", r["semaforo"]


def test_index_falla_en_el_sondeo_conserva_lo_leido_y_lo_avisa(index):
    r = index["refresco"]
    assert r["antes"]["conFalla"] == 0
    f = r["tras_falla"]
    assert f["rechazo"] is None, f["rechazo"]
    assert f["tarjetas"] == 43
    assert "no se pudo releer sus datos (JSON ilegible" in f["porVolcan"]["Llaima"], f["porVolcan"]["Llaima"]
    assert "lectura anterior" in f["porVolcan"]["Llaima"]
    assert f["records"] == 1, "los datos ya leídos se conservan"
    assert f["semaforo"] != "Sistema Operativo"
    s = r["tras_sana"]
    assert "no se pudo" not in s["porVolcan"]["Llaima"] and s["semaforo"] == "Sistema Operativo"


def test_mosaico_y_diario_montan_con_un_json_cortado():
    r = _correr({
        "mosaico": dict(pagina="mosaico.html", grid="mosaico", mirar=["Llaima", "Villarrica"],
                        fallas=[{"patron": LLAIMA_PROPIO, "modo": "cortado"}]),
        "mosaico_control": dict(pagina="mosaico.html", grid="mosaico", mirar=["Llaima"]),
        "diario": dict(pagina="diario.html", grid="grid", mirar=["Llaima", "Villarrica"],
                       fallas=[{"patron": LLAIMA_PROPIO, "modo": "cortado"}]),
    })
    m = r["mosaico"]
    assert m["rechazo"] is None and m["tarjetas"] == 11, m
    assert "Cargando" not in m["cabecera"] and "archivos sin leer: 1 volcán" in m["cabecera"], m["cabecera"]
    assert "sin datos: no se pudo leer su archivo" in m["porVolcan"]["Llaima"]
    assert "no se pudo" not in m["porVolcan"]["Villarrica"]
    c = r["mosaico_control"]
    assert c["tarjetas"] == 11 and c["conFalla"] == 0 and "sin leer" not in c["cabecera"]
    d = r["diario"]
    assert d["rechazo"] is None and d["tarjetas"] == 11, d
    assert "no cargó" in d["porVolcan"]["Llaima"] and "no cargó" not in d["porVolcan"]["Villarrica"]


# ── (5) cobertura.js ─────────────────────────────────────────────────────────────────────────────────────────────

COB = r"""
'use strict';
let ahora = Date.parse('2026-11-25T07:00:00Z');
const DateReal = Date;
global.Date = class extends DateReal { constructor(...a) { if (a.length === 0) super(ahora); else super(...a); } static now() { return ahora; } };
Date.parse = DateReal.parse;
let modo = 'red', items = [], peticiones = 0;
global.fetch = async () => {
  peticiones++;
  if (modo === 'red') throw new TypeError('Failed to fetch');
  if (modo === 'cortado') return { ok: true, status: 200, json: async () => JSON.parse('{"no_medidas": [') };
  return { ok: true, status: 200, json: async () => ({ no_medidas: items }) };
};
function el() { return { style: {}, children: [], _t: '', title: '', isConnected: true, className: '',
  get firstChild() { return this.children[0] || null; }, removeChild(c) { this.children = this.children.filter(x => x !== c); },
  appendChild(c) { this.children.push(c); return c; },
  set textContent(v) { this._t = String(v); this.children = []; }, get textContent() { return this._t + this.children.map(c => c.textContent).join(''); } }; }
global.document = { createElement: el };
const C = require(process.argv[1]);
const pasada = { fecha: '2026-11-25', plataforma: 'VIIRS_NOAA20', motivo: 'pasadas_no_medidas',
                 pasadas: [{ minuto: '2026-11-25 05:30', etapa: 'descarga' }] };
const foto = h => ({ texto: h.textContent, oculto: h.style.display === 'none', title: h.title });
(async () => {
  const o = { ventanaMs: 48 * 3600000, prefijo: 'En 48 h,' };
  const out = {};
  const h1 = el();
  await C.pintar(h1, 'X', o); out.red = foto(h1); out.red_pet = peticiones;
  modo = 'cortado'; const h2 = el(); await C.pintar(h2, 'X', o); out.cortado = foto(h2); out.cortado_pet = peticiones;
  const hl = el(); await C.pintar(hl, 'X', { modo: 'lista' }); out.lista = foto(hl);
  modo = 'ok'; items = [pasada]; const h3 = el(); await C.pintar(h3, 'X', o); out.sano = foto(h3); out.sano_pet = peticiones;
  // Lectura buena en caché: dentro de la vigencia no relee; un hueco nuevo aparece al vencer (repintar).
  items = [pasada, { fecha: '2026-11-24', plataforma: 'MODIS_AQUA', motivo: 'busqueda_fallida', pasadas: [] }];
  await C.pintar(h3, 'X', o); out.cache_pet = peticiones; out.cache = foto(h3);
  ahora += (C.VIGENCIA_MS || 0) + 1000; if (C.repintar) await C.repintar(); else await C.pintar(h3, 'X', o); out.vencido = foto(h3); out.vencido_pet = peticiones;
  // Control: archivo sano y vacío no pinta nada.
  items = []; ahora += (C.VIGENCIA_MS || 0) + 1000; const h4 = el(); await C.pintar(h4, 'Y', o); out.vacio = foto(h4);
  process.stdout.write(JSON.stringify(out));
})().catch(e => { console.error(e && e.stack || e); process.exit(1); });
"""


@pytest.fixture(scope="module")
def cob():
    r = subprocess.run(["node", "-e", COB, str(FRONT / "cobertura.js")], capture_output=True, text=True,
                       encoding="utf-8", timeout=120)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def test_cobertura_ilegible_dice_no_disponible(cob):
    for k in ("red", "cortado"):
        assert not cob[k]["oculto"], cob[k]
        assert "cobertura no disponible" in cob[k]["texto"], cob[k]
        assert "No se sabe si hubo pasadas" in cob[k]["title"]
    assert "falla de red" in cob["red"]["title"] and "JSON ilegible" in cob["cortado"]["title"]
    assert not cob["lista"]["oculto"] and "cobertura no disponible" in cob["lista"]["texto"]


def test_cobertura_la_falla_no_queda_en_cache(cob):
    assert cob["red_pet"] == 1 and cob["cortado_pet"] == 2, "cada llamada tras una falla vuelve a pedir el archivo"
    assert cob["sano_pet"] > cob["cortado_pet"] and "1 pasada sin medir" in cob["sano"]["texto"], cob["sano"]


def test_cobertura_lectura_buena_vence_y_repintar_muestra_el_hueco_nuevo(cob):
    assert cob["cache_pet"] == cob["sano_pet"], "dentro de la vigencia no relee"
    assert "día-satélite" not in cob["cache"]["texto"]
    assert cob["vencido_pet"] == cob["cache_pet"] + 1
    assert "1 día-satélite sin búsqueda" in cob["vencido"]["texto"], cob["vencido"]


def test_cobertura_control_archivo_sano_vacio_no_pinta(cob):
    assert cob["vacio"]["oculto"] and cob["vacio"]["texto"] == ""
