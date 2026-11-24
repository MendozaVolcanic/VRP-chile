// S198, auditoría Codex ronda 3, R3F5-101: ¿cómo dibujan los gráficos del tablero las pasadas con la marca «cráter no
// medido» (frontend/crater_no_medido.js)? Corre con node las funciones REALES extraídas del texto de frontend/index.html
// y frontend/mosaico.html sobre los records REALES de data/mirova_equivalent (11 Tier A) y data/sombra_34.
// El método de extracción sigue al del verificador de la ronda 3 (D:\codex-vrp\_salida\ronda3\f5_r3_verificacion\
// instrumentos\vistas.js); este script es propio y mide el antes y el después con el mismo código.
// Uso: node medir_marcas.js <raiz_del_arbol> <salida_json>
//   raiz = el árbol cuyo frontend se mide (el de main para «antes», este worktree para «después»); los datos se leen
//   siempre de la misma raíz de datos (tercer argumento opcional, por defecto la misma raíz) para comparar igual con igual.
"use strict";
const fs = require("fs"), path = require("path"), vm = require("vm");
const [RAIZ, SALIDA, RAIZ_DATOS] = process.argv.slice(2);
const FE = path.join(RAIZ, "frontend"), DATA = path.join(RAIZ_DATOS || RAIZ, "data");
const leer = (p) => fs.readFileSync(p, "utf8");

function extraerFn(src, nombre) {
  const i = src.indexOf("\nfunction " + nombre + "(");
  if (i < 0) throw new Error("no encontré function " + nombre);
  let d = 0;
  for (let k = src.indexOf("{", i); k < src.length; k++) {
    if (src[k] === "{") d++;
    else if (src[k] === "}" && --d === 0) return src.slice(i + 1, k + 1);
  }
  throw new Error("no cerró " + nombre);
}
function extraerConst(src, nombre) {
  const m = new RegExp("\\n(const|let) " + nombre + "\\s*=").exec(src);
  if (!m) throw new Error("no encontré const " + nombre);
  let d = 0, q = null;
  for (let k = m.index + m[0].length; k < src.length; k++) {
    const c = src[k];
    if (q) { if (c === "\\") { k++; continue; } if (c === q) q = null; continue; }
    if (c === '"' || c === "'" || c === "`") { q = c; continue; }
    if ("([{".includes(c)) d++; else if (")]}".includes(c)) d--;
    else if (c === ";" && d === 0) return src.slice(m.index + 1, k + 1).replace(/^(let|const) /, "var ");
  }
  throw new Error("no cerró const " + nombre);
}
function opcional(src, f) { try { return extraerFn(src, f); } catch (e) { return ""; } }
const RANGO = { t0: 0, t1: 0 };   // período del minigráfico de mosaico (lo lee el stub de Periodo)
function contexto(src, consts, fns, extra, opcionales) {
  const ctx = vm.createContext({ RANGO,
    CambioDetector: require(path.join(FE, "cambio_detector.js")), DiurnoTablero: require(path.join(FE, "diurno.js")),
    CraterNoMedido: require(path.join(FE, "crater_no_medido.js")), console, Math, Date, JSON, Number, String, Object,
    Array, Set, Map, parseFloat, isNaN, Infinity, NaN });
  const codigo = (extra || "") + "\n" + consts.map(c => extraerConst(src, c)).join("\n") + "\n" +
    fns.map(f => extraerFn(src, f)).join("\n") + "\n" + (opcionales || []).map(f => opcional(src, f)).join("\n") +
    "\nglobalThis.__api = {" + fns.join(",") + "};" +
    (opcionales || []).map(f => "\nif (typeof " + f + " === 'function') globalThis.__api." + f + " = " + f + ";").join("");
  vm.runInContext(codigo, ctx);
  return ctx.__api;
}

const srcIx = leer(path.join(FE, "index.html"));
const IX = contexto(srcIx,
  ["USE_F5_CORE", "F5_R_CORE_KM", "F5_BT_EXT_K", "PATH_D_CAP_MW", "EVOL_MISMA_PASADA_MS", "EVOL_PRIORIDAD_ESTADO",
   "EVOL_COLOR_MARCA", "EVOL_FILA_MARCA", "EVOL_EXTREMO_MW", "ETIQUETA_SENSOR", "LEVELS"],
  ["parseUtcMs", "_havKm", "mirovaEqVrp", "f5CoreMagnitude", "mirovaEqVrpCore", "mirovaEqVrpDisplay",
   "isCirrusArtifact", "isDiffuseFieldArtifact", "isThermalArtifact", "isValidDetection", "isSummitDetection",
   "esAnclaHonesta", "sensorGroup", "escenaSinDato", "distanciaDePasada", "todasPasadasEvol", "vrpPublicadoEvol",
   "ultimaPasadaEvol", "textoUltimaPasadaEvol", "marcasEvol", "getLevel", "mwEvol", "haceEvol", "esOblicuaEvol",
   "textoCenitEvol"],
  "var sensorVisible = { MODIS: true, VIIRS375: true, VIIRS750: true, MIROVA: true }; var EVOL_CENIT_OBLICUO = 40;",
  ["fondoMedidoK"]);
const srcMo = leer(path.join(FE, "mosaico.html"));
const MO = contexto(srcMo, ["USE_F5_CORE", "F5_R_CORE_KM", "F5_BT_EXT_K"],
  ["parseUtcMs", "_havKm", "mirovaEqVrp", "f5CoreMagnitude", "mirovaEqVrpCore", "isCirrusArtifact",
   "isDiffuseFieldArtifact", "isThermalArtifact", "eqVrpDisplay", "isValidDetection", "isSummitDetection",
   "buildSparklineData", "etiquetaDiaSparkline"],
  "function fmtVRP(v){return String(v);} var PERIODO = null; var Periodo = { intervalo: (p, a) => [RANGO.t0, RANGO.t1] };");
const CNM = require(path.join(FE, "crater_no_medido.js"));

// lat, lon e inner de VOLCANOES_ALL de index (como loadVolcano); los 34 usan inner 5 (index.html, VOLCANOES)
const VOL = {};
for (const m of srcIx.matchAll(/\{ name: "(\w+)",[^\n]*?lat: (-?[\d.]+), lon: (-?[\d.]+)([^\n]*)/g)) {
  if (VOL[m[1]]) continue;
  const inner = /inner_radius_km: ([\d.]+)/.exec(m[4]);
  VOL[m[1]] = { lat: +m[2], lon: +m[3], inner: inner ? +inner[1] : 5 };
}
const Diurno = require(path.join(FE, "diurno.js"));
const fuentes = [["mirova_equivalent", "Tier A"], ["sombra_34", "sombra"]];
const filas = [];
let tmax = 0;
const porVolcan = [];
for (const [carpeta, grupo] of fuentes) {
  const dir = path.join(DATA, carpeta);
  for (const f of fs.readdirSync(dir).filter(x => x.endsWith(".json")).sort()) {
    const v = f.replace(/\.json$/, "");
    const vv = VOL[v]; if (!vv) continue;
    let recs; try { recs = JSON.parse(leer(path.join(dir, f))).records || []; } catch (e) { continue; }
    Diurno.marcar(recs, vv.lat, vv.lon);
    for (const r of recs) { const t = IX.parseUtcMs(r.datetime_utc); if (t > tmax) tmax = t; }
    porVolcan.push({ v, grupo, vv, recs });
  }
}
const AHORA = tmax + 60000;
const conteo = { marcas: 0, con_motivo_vacio: 0, evol: {}, evol_nada_o_publicada_sin_aviso: 0, recuadro_sin_anomalia_con_marca: 0,
                 mosaico_dia_observado_sin_aviso: 0, mosaico_dias_marcados: 0, fondo_cero: 0, fondo_cero_tabla_sin_fondo: 0 };
for (const { v, grupo, vv, recs } of porVolcan) {
  const pas = IX.todasPasadasEvol(recs, vv.inner);
  const marcas = IX.marcasEvol(pas);
  const marcaEn = new Set(marcas.map(m => m.t + "|" + m.estado));
  const porClave = new Map(pas.map(p => [p.dt + "|" + p.sensor, p]));
  for (const r of recs) {
    if (r.t_bg_k === 0) { conteo.fondo_cero++; if (typeof IX.fondoMedidoK === "function" && IX.fondoMedidoK(r) === null) conteo.fondo_cero_tabla_sin_fondo++; }
    const m = CNM.craterNoMedido(r);
    if (!m) continue;
    conteo.marcas++;
    const vacia = !!(r.diag_codigo_mirova && r.diag_codigo_mirova.motivo_vacio);
    if (vacia) conteo.con_motivo_vacio++;
    const p = porClave.get(r.datetime_utc + "|" + r.sensor);
    const est = p ? p.estado : "sin_pasada";
    conteo.evol[est] = (conteo.evol[est] || 0) + 1;
    // ¿lo dibuja como «se midió, nada» o publica potencia sin aviso? Sin aviso = sin raya naranja ni texto de la marca
    const naranja = p && marcaEn.has(p.t + "|no_medido");
    const avisoTexto = p && p.cnm;   // el tooltip y el recuadro leen p.cnm (sólo existe con este cambio)
    const malo = !vacia && p && (est === "nada" || est === "no_publicada" || ((est === "crater" || est === "fuera") && !(naranja && avisoTexto)));
    if (malo) conteo.evol_nada_o_publicada_sin_aviso++;
    // recuadro de «Última pasada» si esta fuera la última pasada del volcán
    const u = IX.ultimaPasadaEvol([p].filter(Boolean), false);
    const rec = u ? IX.textoUltimaPasadaEvol(u, AHORA, false, null).texto : "";
    const recuadroMalo = !vacia && /sin anomalía/.test(rec) && !/⊘/.test(rec);
    if (recuadroMalo) conteo.recuadro_sin_anomalia_con_marca++;
    filas.push({ volcan: v, grupo, dt: r.datetime_utc, sensor: r.sensor, diurna: r._diurna === true, motivo_vacio: vacia,
                 nMir: m.nMir, nSat: m.nSat, sinPosicion: m.sinPosicion, estado_evol: est, raya_naranja: !!naranja,
                 texto_en_tooltip: !!avisoTexto, recuadro: rec, malo: !!malo, recuadro_malo: recuadroMalo });
  }
  // mosaico (sólo los 11 Tier A): el día UTC de cada pasada nocturna marcada sin escena vacía
  if (grupo !== "Tier A") continue;
  const marcadas = recs.filter(r => r._diurna !== true && CNM.craterNoMedido(r) && !(r.diag_codigo_mirova && r.diag_codigo_mirova.motivo_vacio));
  if (!marcadas.length) continue;
  const ts = marcadas.map(r => IX.parseUtcMs(r.datetime_utc));
  RANGO.t0 = Math.min(...ts) - 86400000; RANGO.t1 = Math.min(Math.max(...ts) + 86400000, Date.now());
  const s = MO.buildSparklineData(recs, vv.inner);
  for (const r of marcadas) {
    const d = r.datetime_utc.slice(0, 10);
    const i = s.labels.findIndex(x => x.toISOString().slice(0, 10) === d);
    if (i < 0) continue;
    conteo.mosaico_dias_marcados++;
    const et = MO.etiquetaDiaSparkline(s.values[i], s.observado[i], s.noMedido && s.noMedido[i], s.sat && s.sat[i]);
    const sinAviso = !/⊘/.test(et);
    if (sinAviso) conteo.mosaico_dia_observado_sin_aviso++;
    filas.push({ volcan: v, grupo: "mosaico", dt: d, etiqueta_dia: et, malo: sinAviso });
  }
}
// Control: un record sintético con hueco de MIR sobre el cráter tiene que salir como marca en el gráfico.
const sint = { sensor: "VIIRS_NOAA20", datetime_utc: "2026-11-22 05:06", via_codigo_mirova: true, vrp_mw: 0,
  n_anomalous_pixels: 0, anomaly_pixels: [], diag_codigo_mirova: { motivo_vacio: null, px_mir_hueco_crater: 3 } };
const ps = IX.todasPasadasEvol([sint], 5);
const control = { estado: ps[0].estado, marcas: IX.marcasEvol(ps).map(m => m.estado) };
const out = { raiz: RAIZ, raiz_datos: RAIZ_DATOS || RAIZ, ahora_emulado: new Date(AHORA).toISOString(), conteo, control, filas };
fs.writeFileSync(SALIDA, JSON.stringify(out, null, 1));
console.log(JSON.stringify({ conteo, control }, null, 1));
