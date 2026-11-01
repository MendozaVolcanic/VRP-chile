// M2 (S158 r2): las tres vistas del tablero, copia contra copia, sobre los records reales.
//
// Fenómeno: index.html, diario.html y mosaico.html llevan cada una su copia de mirovaEqVrp,
// isValidDetection, isCirrusArtifact, etc. Si una copia difiere, el operador ve un volcán con
// magnitud en una vista y sin ella en otra. Instrumento: extraigo el texto de cada función de cada
// HTML (sin reescribirlas), las ejecuto en tres sandboxes de node con los MISMOS records y cuento
// cuántos records muestran un valor distinto, y por qué.
//
// Pregunta 1: si una copia estuviera rota, el conteo de discrepancias sería > 0 (control positivo
// al final: un record sintético en que las copias DEBEN diferir por construcción). Pregunta 2: si la
// extracción fallara, el sandbox lanza (no devuelve 0 en silencio): cada función se verifica que
// exista antes de medir.
//
// Denominador: todos los records de data/mirova_equivalent/*.json (45 volcanes) para index/diario;
// los 11 Tier A para mosaico (solo esos están en su lista). Ventana: todo el corpus y los últimos
// 90 días contados desde el último record.
"use strict";
const fs = require("fs"), path = require("path"), vm = require("vm");
const REPO = path.resolve(__dirname, "..", "..", "..");
const read = (p) => fs.readFileSync(path.join(REPO, p), "utf8");

function extractFn(src, name) {
  const re = new RegExp("(^|\\n)function " + name.replace("$", "\\$") + "\\s*\\(");
  const m = re.exec(src);
  if (!m) throw new Error("no encontré function " + name);
  let i = m.index + m[0].length - 1;
  // avanzar hasta la primera llave del cuerpo
  i = src.indexOf("{", i);
  let depth = 0, j = i, inStr = null, inLine = false, inBlock = false;
  for (; j < src.length; j++) {
    const c = src[j], n = src[j + 1];
    if (inLine) { if (c === "\n") inLine = false; continue; }
    if (inBlock) { if (c === "*" && n === "/") { inBlock = false; j++; } continue; }
    if (inStr) { if (c === "\\") { j++; continue; } if (c === inStr) inStr = null; continue; }
    if (c === "/" && n === "/") { inLine = true; continue; }
    if (c === "/" && n === "*") { inBlock = true; continue; }
    if (c === '"' || c === "'" || c === "`") { inStr = c; continue; }
    if (c === "{") depth++;
    if (c === "}") { depth--; if (depth === 0) break; }
  }
  return src.slice(m.index + m[0].length - "function ".length - name.length - 1, j + 1).replace(/^\n/, "");
}
function extractConst(src, re) { const m = re.exec(src); if (!m) throw new Error("const no encontrada " + re); return m[0]; }

const srcIdx = read("frontend/index.html"), srcDia = read("frontend/diario.html"), srcMos = read("frontend/mosaico.html");

function build(src, names, prelude) {
  const code = prelude + "\n" + names.map(n => extractFn(src, n)).join("\n") + "\n";
  const ctx = { console };
  vm.createContext(ctx);
  vm.runInContext(code, ctx);
  for (const n of names) if (typeof ctx[n] !== "function") throw new Error("no quedó definida " + n);
  return ctx;
}
const F5 = (src) => extractConst(src, /const F5_R_CORE_KM = [^;]+;/) + "\n" + extractConst(src, /const F5_BT_EXT_K = [^;]+;/) + "\n";

const IDX = build(srcIdx,
  ["mirovaEqVrp", "f5CoreMagnitude", "mirovaEqVrpCore", "mirovaEqVrpDisplay", "isCirrusArtifact", "isDiffuseFieldArtifact",
   "isThermalArtifact", "isValidDetection", "isSummitDetection", "_havKm", "parseUtcMs", "sensorGroup", "isSensorVisible",
   "ourSensorBucket", "mirovaSensorBucket", "enrichWithMirovaConfirmation"],
  "let USE_F5_CORE = true; const sensorVisible = {}; let includeFarDistance = false;\n" + F5(srcIdx));
const DIA = build(srcDia,
  ["mirovaEqVrp", "f5CoreMagnitude", "mirovaEqVrpCore", "isCirrusArtifact", "isDiffuseFieldArtifact", "isThermalArtifact",
   "isValidDetection", "eqVrpDisplay", "_havKm", "parseUtcMs"],
  "let USE_F5_CORE = true; let includeFarDistance = false;\n" + extractConst(srcDia, /const INNER_RADIUS_KM = \{[^}]*\};/) + "\n" + F5(srcDia));
const MOS = build(srcMos,
  ["mirovaEqVrp", "f5CoreMagnitude", "mirovaEqVrpCore", "isCirrusArtifact", "isDiffuseFieldArtifact", "isThermalArtifact",
   "eqVrpDisplay", "isValidDetection", "isSummitDetection", "_havKm", "parseUtcMs"],
  "let USE_F5_CORE = true;\n" + F5(srcMos));

// inner_radius_km según cada vista
const innerIdx = {}, innerMos = {};
for (const m of srcIdx.matchAll(/\{ name: "([A-Za-z]+)",[^\n]*?\}/g)) { const k = /inner_radius_km: (\d+)/.exec(m[0]); innerIdx[m[1]] = k ? +k[1] : undefined; }
for (const m of srcMos.matchAll(/\{ name: "([A-Za-z]+)",[^\n]*?\}/g)) { const k = /inner_radius_km: (\d+)/.exec(m[0]); innerMos[m[1]] = k ? +k[1] : undefined; }
const innerDia = vm.runInContext("INNER_RADIUS_KM", DIA);
console.log("volcanes en index:", Object.keys(innerIdx).length, "| en mosaico:", Object.keys(innerMos).length, "| en tabla de diario:", Object.keys(innerDia).length);
const difInner = [];
for (const v of Object.keys(innerIdx)) { const a = innerIdx[v] ?? 10, b = innerDia[v] ?? 5; if (a !== b) difInner.push(`${v}:${a}/${b}`); }
console.log("volcanes donde innerKm efectivo index != diario (index ?? 10 / diario ?? 5):", difInner.length, difInner.slice(0, 8).join(" "), "...");

// ---- medición ----
const files = fs.readdirSync(path.join(REPO, "data/mirova_equivalent")).filter(f => f.endsWith(".json"));
let maxDt = "";
for (const f of files) for (const r of JSON.parse(read("data/mirova_equivalent/" + f)).records) if (r.datetime_utc > maxDt) maxDt = r.datetime_utc;
const t90 = IDX.parseUtcMs(maxDt) - 90 * 86400000;
const tot = { all: 0, w90: 0 }, dif = {}, ejem = {};
const bump = (k, w) => { dif[k] = dif[k] || { all: 0, w90: 0 }; dif[k].all++; if (w) dif[k].w90++; };
const ej = (k, s) => { (ejem[k] = ejem[k] || []); if (ejem[k].length < 3) ejem[k].push(s); };
const neq = (a, b) => Math.abs((a || 0) - (b || 0)) > 1e-9;
let pc0summitConfirmed = 0, pc0summit = 0;

for (const f of files) {
  const name = f.slice(0, -5);
  const recs = JSON.parse(read("data/mirova_equivalent/" + f)).records;
  let mref = [];
  try { mref = JSON.parse(read("data/mirova/" + name + ".json")).records || []; } catch (e) { mref = []; }
  // index enriquece; diario y mosaico no (lo dicen sus propios comentarios): copias separadas
  const recsIdx = JSON.parse(JSON.stringify(recs));
  IDX.enrichWithMirovaConfirmation(recsIdx, mref);
  const iIdx = innerIdx[name] ?? 10, iMos = innerMos[name], iDiaKm = innerDia[name] ?? 5;
  const esTierA = iMos !== undefined;
  for (let k = 0; k < recs.length; k++) {
    const r = recs[k], ri = recsIdx[k];
    const w = IDX.parseUtcMs(r.datetime_utc) >= t90;
    tot.all++; if (w) tot.w90++;
    const idxChart = IDX.isThermalArtifact(ri, iIdx) ? 0 : IDX.mirovaEqVrpDisplay(ri, iIdx, false);
    const idxCard = IDX.isSummitDetection(ri) && IDX.isValidDetection(ri) && !IDX.isThermalArtifact(ri, iIdx) && idxChart > 0;
    const diaChart = DIA.eqVrpDisplay(r, name);
    const tag = `${name} ${r.datetime_utc} ${r.sensor}`;
    if (ri.primary_cluster && ri.primary_cluster.vrp_mw === 0 && ri.primary_cluster.centroid_dist_km != null && ri.primary_cluster.centroid_dist_km <= (iMos ?? 99) && (r.n_anomalous_pixels || 0) > 0 && r.sensor.startsWith("MODIS")) { pc0summit++; if (ri._mirova_confirmed) pc0summitConfirmed++; }
    if (neq(idxChart, diaChart)) {
      let causa = "otra";
      if (!r.primary_cluster) causa = "sin primary_cluster (legacy)";
      else if (iIdx !== iDiaKm && r.primary_cluster.centroid_dist_km != null && (r.primary_cluster.centroid_dist_km > Math.min(iIdx, iDiaKm)) && (r.primary_cluster.centroid_dist_km <= Math.max(iIdx, iDiaKm))) causa = `innerKm distinto (index ${iIdx} / diario ${iDiaKm})`;
      else if (ri._mirova_confirmed && (IDX.isCirrusArtifact(r, iIdx) || IDX.isDiffuseFieldArtifact(r, iIdx))) causa = "cirrus/difuso suprimido en diario pero confirmado por MIROVA en index";
      bump("index_chart != diario_chart: " + causa, w); ej("index_chart != diario_chart: " + causa, `${tag} idx=${idxChart} dia=${diaChart}`);
    }
    if (esTierA) {
      const mosChart = MOS.eqVrpDisplay(r, iMos);
      const mosCard = MOS.isSummitDetection(r) && MOS.isValidDetection(r) && mosChart > 0;
      if (neq(idxChart, mosChart)) {
        let causa = "otra";
        if (!r.primary_cluster) causa = "sin primary_cluster (legacy)";
        else if (ri._mirova_confirmed && (IDX.isCirrusArtifact(r, iIdx) || IDX.isDiffuseFieldArtifact(r, iIdx))) causa = "cirrus/difuso suprimido en mosaico pero confirmado por MIROVA en index";
        bump("index_chart != mosaico_chart: " + causa, w); ej("index_chart != mosaico_chart: " + causa, `${tag} idx=${idxChart} mos=${mosChart}`);
      }
      if (idxCard !== mosCard) { bump("tarjeta index != tarjeta mosaico", w); ej("tarjeta index != tarjeta mosaico", `${tag} idx=${idxCard} mos=${mosCard}`); }
      if (neq(diaChart, mosChart)) { bump("diario_chart != mosaico_chart", w); ej("diario_chart != mosaico_chart", `${tag} dia=${diaChart} mos=${mosChart}`); }
      // diario grafica algo que la tarjeta de index/mosaico no titularía
      if (diaChart > 0 && !idxCard) {
        const causa = !IDX.isSummitDetection(ri) ? "isSummitDetection false (vrp_mw==0 && discarded_reason, o distance_class ausente)" : "otra";
        bump("diario grafica > 0 pero index no lo titularía: " + causa, w); ej("diario grafica > 0 pero index no lo titularía: " + causa, `${tag} dia=${diaChart} vrp_mw=${r.vrp_mw} dr=${r.discarded_reason} dc=${r.distance_class}`);
      }
    }
  }
}
console.log(`records: ${tot.all} (ultimos 90 dias desde ${maxDt}: ${tot.w90})`);
console.log("MODIS con cumulo en el inner, pixeles anomalos y pc.vrp_mw == 0:", pc0summit, "| de ellos con alerta MIROVA +-60 min (index _mirova_confirmed):", pc0summitConfirmed);
for (const k of Object.keys(dif).sort()) { console.log(`\n[${k}] total ${dif[k].all} | 90d ${dif[k].w90}`); for (const e of ejem[k]) console.log("   ej:", e); }
if (!Object.keys(dif).length) console.log("\nsin discrepancias entre vistas en ningun record");

// ---- control positivo: un record en que las copias DEBEN diferir ----
console.log("\n== control positivo ==");
const rc = { sensor: "MODIS_TERRA", datetime_utc: "2026-10-01 05:00", distance_class: "summit", vrp_mw: 0, discarded_reason: "cluster_too_large_for_volcano", t_max_k: 290, primary_cluster: { vrp_mw: 3.3, centroid_dist_km: 1.0, n_pixels: 2, centroid_lat: -39.4, centroid_lon: -71.9 } };
const a = IDX.isThermalArtifact(rc, 5) ? 0 : IDX.mirovaEqVrpDisplay(rc, 5, false), b = DIA.eqVrpDisplay(rc, "Villarrica"), c = MOS.eqVrpDisplay(rc, 5);
console.log("record sintetico vrp_mw=0+discarded_reason, pc=3.3 @1 km: index chart", a, "| diario", b, "| mosaico", c, "| tarjeta index:", IDX.isSummitDetection(rc), "| tarjeta mosaico:", MOS.isSummitDetection(rc));
const rl = { sensor: "MODIS_TERRA", datetime_utc: "2025-03-01 05:00", vrp_mw: 60000, distance_class: "far" };
console.log("record legacy sin pc, far, 60 GW: index", IDX.mirovaEqVrp(rl, 5, false), "| diario", DIA.mirovaEqVrp(rl, "Villarrica"), "| mosaico", MOS.mirovaEqVrp(rl, 5, false));
const rl2 = { sensor: "MODIS_TERRA", datetime_utc: "2025-03-01 05:00", vrp_mw: 2.0 };
console.log("record legacy sin pc, sin distance_class, 2 MW: index", IDX.mirovaEqVrp(rl2, 5, false), "| diario", DIA.mirovaEqVrp(rl2, "Villarrica"), "| mosaico", MOS.mirovaEqVrp(rl2, 5, false));
