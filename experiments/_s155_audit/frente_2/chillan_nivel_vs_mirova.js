// Nevados de Chillán en erupción, ventana K: nivel MIROVA (Muy Bajo <1, Bajo <10, Moderado <100 MW) del número que
// grafica index.html (eqVrp del detalle: Núcleo F5' por defecto) contra el VRP que MIROVA publicó en la pasada más
// cercana (±60 min, mismo sensor, sólo nocturnas de la tabla y OCR). También con el cúmulo (toggle "Cluster").
// Pregunta 1: si el número mostrado estuviera calibrado con MIROVA, la razón mediana sería ~1 y el nivel coincidiría.
// Pregunta 2: si no hubiera pares, n = 0 y se dice. Denominador: pares TP de computeMetrics-equivalente, 2026-09-18..
"use strict";
const fs = require("fs"), path = require("path");
const { cargarVista } = require("./extraer.js");
const ROOT = path.resolve(__dirname, "../../..");
const NOW = Date.parse("2026-10-19T12:00:00Z");
const mk = (f5) => cargarVista(path.join(ROOT,"frontend/index.html"),
  ["mirovaEqVrp","_havKm","f5CoreMagnitude","mirovaEqVrpCore","mirovaEqVrpDisplay","isCirrusArtifact","isDiffuseFieldArtifact","isThermalArtifact","parseUtcMs","getLevel","sensorGroup","ourSensorBucket","mirovaSensorBucket"],
  ["PATH_D_CAP_MW","F5_R_CORE_KM","F5_BT_EXT_K","LEVELS"], "var USE_F5_CORE = " + f5 + ";", NOW);
const NU = mk(true), CL = mk(false);
const recs = JSON.parse(fs.readFileSync(path.join(ROOT,"data/mirova_equivalent/NevadosDeChillan.json"),"utf8")).records.filter(r => r.datetime_utc >= "2026-09-18");
const mr = JSON.parse(fs.readFileSync(path.join(ROOT,"data/mirova/NevadosDeChillan.json"),"utf8")).records.filter(r => r.datetime_utc >= "2026-09-18" && r.dia !== true);
const res = {};
for (const r of recs) {
  const b = NU.ourSensorBucket(r.sensor); const t = NU.parseUtcMs(r.datetime_utc);
  const vN = NU.isThermalArtifact(r,5) ? 0 : NU.mirovaEqVrpDisplay(r, 5, false), vC = CL.mirovaEqVrpDisplay(r, 5, false);
  if (!(vN > 0)) continue;
  let best = null;
  for (const m of mr) { if (NU.mirovaSensorBucket(m.sensor) !== b) continue; const dt = Math.abs(NU.parseUtcMs(m.datetime_utc) - t); if (dt <= 3600000 && (!best || dt < best.dt)) best = {dt, v: parseFloat(m.VRP_MW)}; }
  if (!best || !(best.v > 0)) continue;
  const o = res[b] ||= {n:0, rN:[], rC:[], nivN:0, nivC:0, bajoN:0};
  o.n++; o.rN.push(vN/best.v); o.rC.push(vC/best.v);
  if (NU.getLevel(vN).key === NU.getLevel(best.v).key) o.nivN++;
  if (NU.getLevel(vC).key === NU.getLevel(best.v).key) o.nivC++;
  if (["vlow","low"].includes(NU.getLevel(vN).key) && NU.getLevel(best.v).key === "mod") o.bajoN++;
}
const med = a => { const s = a.slice().sort((x,y)=>x-y); return s.length ? s[s.length>>1] : null; };
for (const [b,o] of Object.entries(res)) console.log(b, "pares", o.n, "| razón mediana núcleo/MIROVA", med(o.rN)?.toFixed(2), "cúmulo/MIROVA", med(o.rC)?.toFixed(2), "| mismo nivel núcleo", o.nivN, "cúmulo", o.nivC, "| nosotros <=Bajo con MIROVA Moderado (núcleo):", o.bajoN);
