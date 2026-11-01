// Harness: carga el codigo LITERAL de una vista (scripts inline + periodo.js + cambio_detector.js) en un contexto vm
// con un DOM de juguete. No reconstruye ninguna funcion: las llama tal como estan en el HTML (A97).
const fs = require('fs'), vm = require('vm'), path = require('path');
const REPO = path.resolve(__dirname, '..', '..', '..');
function stubEl() {
  const h = { get: (t, k) => {
    if (k === Symbol.toPrimitive) return () => '';
    if (k in t) return t[k];
    if (k === 'style' || k === 'dataset' || k === 'classList') return t[k] = new Proxy({}, h2);
    if (k === 'value') return '';
    if (k === 'checked') return false;
    if (k === 'children' || k === 'childNodes') return [];
    if (k === 'firstChild' || k === 'parentNode' || k === 'nextSibling') return null;
    return function () { return stubEl(); };
  }, set: (t, k, v) => { t[k] = v; return true; } };
  const h2 = { get: (t, k) => (k in t ? t[k] : function () { return false; }), set: (t, k, v) => { t[k] = v; return true; } };
  return new Proxy({}, h);
}
function cargar(vista, ahoraIso, search) {
  const html = fs.readFileSync(path.join(REPO, 'frontend', vista), 'utf8');
  const scripts = [];
  const re = /<script([^>]*)>([\s\S]*?)<\/script>/g; let m;
  while ((m = re.exec(html))) {
    const src = /src="([^"]+)"/.exec(m[1]);
    if (src) { if (!/^https?:/.test(src[1])) scripts.push(fs.readFileSync(path.join(REPO, 'frontend', src[1]), 'utf8')); }
    else scripts.push(m[2]);
  }
  const ahora = Date.parse(ahoraIso);
  const RealDate = Date;
  class FDate extends RealDate { constructor(...a) { if (a.length === 0) super(ahora); else super(...a); } static now() { return ahora; } }
  const store = {};
  const storage = { getItem: k => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = String(v); }, removeItem: k => { delete store[k]; } };
  const doc = stubEl(); doc.readyState = 'complete'; doc.body = stubEl();
  doc.getElementById = () => stubEl(); doc.querySelector = () => null; doc.querySelectorAll = () => [];
  doc.createElement = () => stubEl(); doc.createTextNode = () => stubEl(); doc.addEventListener = () => {};
  const ctx = {
    console, Date: FDate, Math, JSON, Map, Set, Promise, URLSearchParams, Number, String, Array, Object, isNaN, isFinite, parseFloat, parseInt, Symbol, RegExp, Error, encodeURIComponent, decodeURIComponent, Infinity, NaN,
    document: doc, sessionStorage: storage, localStorage: storage,
    location: { search: search || '', pathname: '/', href: 'http://x/' },
    fetch: () => new Promise(() => {}), setTimeout: () => 0, setInterval: () => 0, clearTimeout: () => {}, clearInterval: () => {},
    requestAnimationFrame: () => 0, addEventListener: () => {}, alert: () => {}, history: { replaceState() {}, pushState() {} },
    Chart: Object.assign(function () { return stubEl(); }, { register() {}, Interaction: { modes: {} }, defaults: stubEl() }),
    L: new Proxy({}, { get: () => function () { return stubEl(); } }), navigator: { userAgent: 'node' }, matchMedia: () => ({ matches: false, addEventListener() {} }),
  };
  ctx.window = ctx; ctx.globalThis = ctx; ctx.self = ctx;
  vm.createContext(ctx);
  // Los const/let de nivel superior no quedan en ctx: concateno todo en un solo script y exporto lo pedido.
  const codigo = scripts.join('\n;\n');
  return { ctx, codigo, ahora };
}
function evaluar(vista, ahoraIso, search, exportar) {
  const { ctx, codigo } = cargar(vista, ahoraIso, search);
  const exp = '\n;globalThis.__X = {' + exportar.map(n => `${n}: (typeof ${n} !== 'undefined' ? ${n} : undefined)`).join(',') +
    ', __setFar: (v) => { includeFarDistance = v; }, __setF5: (v) => { if (typeof USE_F5_CORE !== "undefined") USE_F5_CORE = v; } };';
  vm.runInContext(codigo + exp, ctx, { filename: vista });
  return ctx.__X;
}
module.exports = { evaluar, REPO };
