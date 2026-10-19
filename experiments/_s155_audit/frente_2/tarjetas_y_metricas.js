// Tarjeta de index (latestDetection, anomaliaRelativa, corroboracionMirova) y métricas del detalle (computeMetrics)
// ejecutadas con el código literal sobre los JSON reales, en NOW = 2026-10-19 12:00 UTC.
// Pregunta 1: si la base de 90 días mezclara detectores, comparar la base completa contra la base K sola lo ve.
// Pregunta 2: si anomaliaRelativa no devolviera nada (instrumento muerto) se imprime "null" con su motivo (< 10 base).
// Control positivo: restringir la base a K tiene que cambiar n (si no cambia, el filtro no actúa).
// Denominador: 11 Tier A; ventana de la base = 90 d antes de la última detección; métricas = últimos 30 d.
"use strict";
const fs = require("fs"), path = require("path");
const { cargarVista } = require("./extraer.js");
const ROOT = path.resolve(__dirname, "../../..");
const NOW = Date.parse("2026-10-19T12:00:00Z");
const TIER = ["Isluga","Lascar","Lastarria","Tupungatito","PlanchonPeteroa","NevadosDeChillan","Copahue","Llaima","Villarrica","PuyehueCordonCaulle","Chaiten"];
const INNER = {Lascar:5,Lastarria:3,Tupungatito:7,Villarrica:5,PuyehueCordonCaulle:20,Copahue:4,NevadosDeChillan:5,Llaima:5,Chaiten:5,PlanchonPeteroa:3,Isluga:5};
const IX = cargarVista(path.join(ROOT,"frontend/index.html"),
  ["mirovaEqVrp","_havKm","f5CoreMagnitude","mirovaEqVrpCore","mirovaEqVrpDisplay","isCirrusArtifact","isDiffuseFieldArtifact","isThermalArtifact","parseUtcMs","isValidDetection","isSummitDetection","latestDetection","sensorGroup","isSensorVisible","getLevel","anomaliaRelativa","corroboracionMirova","ourSensorBucket","mirovaSensorBucket","computeMetrics","enrichWithMirovaConfirmation","distanceCounts"],
  ["PATH_D_CAP_MW","F5_R_CORE_KM","F5_BT_EXT_K","LEVELS"],
  "var USE_F5_CORE = true; var includeFarDistance = false; var sensorVisible = {MODIS:true,VIIRS375:true,VIIRS750:true,MIROVA:true};", NOW);
const MO = cargarVista(path.join(ROOT,"frontend/mosaico.html"),
  ["mirovaEqVrp","_havKm","f5CoreMagnitude","mirovaEqVrpCore","isCirrusArtifact","isDiffuseFieldArtifact","isThermalArtifact","parseUtcMs","isValidDetection","eqVrpDisplay","isSummitDetection","latestVRP","getLevel"],
  ["PATH_D_CAP_MW","F5_R_CORE_KM","F5_BT_EXT_K","LEVELS"], "var USE_F5_CORE = true;", NOW);
const esK = r => !!(r.regimen && r.regimen.codigo_sha);
const res = [];
for (const v of TIER) {
  const recs = JSON.parse(fs.readFileSync(path.join(ROOT,"data/mirova_equivalent",v+".json"),"utf8")).records;
  const mref = JSON.parse(fs.readFileSync(path.join(ROOT,"data/mirova",v+".json"),"utf8"));
  const mrecs = mref.records || [];
  IX.enrichWithMirovaConfirmation(recs, mrecs);
  const inner = INNER[v];
  const det = IX.latestDetection(recs, false, inner);
  const mo = MO.latestVRP(recs, inner);
  const arMix = IX.anomaliaRelativa(recs, det, inner);
  const arK = IX.anomaliaRelativa(recs.filter(esK), det, inner);
  // base: cuántos records de la base son C0
  let baseC0 = 0, baseK = 0;
  if (det) for (const r of recs) { const t = IX.parseUtcMs(r.datetime_utc); if (!(t >= det.ts - 90*86400000 && t < det.ts)) continue;
    if (!IX.isValidDetection(r) || IX.isThermalArtifact(r, inner)) continue; if (!(IX.mirovaEqVrpDisplay(r, inner, false) > 0)) continue; esK(r) ? baseK++ : baseC0++; }
  const corr = IX.corroboracionMirova({records: recs, mirovaRecords: mrecs}, 90);
  // "nuestras" del 90d: cuántas son far (no summit) y cuántas C0
  let nuestFar = 0, nuestC0 = 0, nuestPub = 0;
  for (const r of recs) { const t = IX.parseUtcMs(r.datetime_utc); if (!(t >= NOW - 90*86400000)) continue; if (!IX.isValidDetection(r)) continue;
    if (!IX.isSummitDetection(r)) nuestFar++; if (!esK(r)) nuestC0++; if (IX.mirovaEqVrpDisplay(r, inner, false) > 0 && !IX.isThermalArtifact(r, inner)) nuestPub++; }
  // métricas 30 d
  const ours30 = recs.filter(r => IX.parseUtcMs(r.datetime_utc) >= NOW - 30*86400000);
  const m30 = mrecs.filter(r => IX.parseUtcMs(r.datetime_utc) >= NOW - 30*86400000);
  const met = IX.computeMetrics(ours30, m30, inner, false);
  const metNoche = IX.computeMetrics(ours30, m30.filter(r => r.dia !== true), inner, false);
  const nDia = m30.filter(r => r.dia === true && !["NULO","RUTINA"].includes(String(r.clasificacion||"").toUpperCase()) && parseFloat(r.VRP_MW) > 0).length;
  const nNone375 = m30.filter(r => r.sensor === "VIIRS375" && r.dia !== true && parseFloat(r.VRP_MW) > 0 && parseFloat(r.VRP_MW) <= 0.05).length;
  res.push({v, det: det && {vrp: +det.vrp.toFixed(3), dt: det.datetime_utc, dist: det.dist, lvl: IX.getLevel(det.vrp).label, mirova: det.mirova},
    mosaico: {vrp: +mo.max.toFixed(3), ts: mo.ts, lvl: MO.getLevel(mo.max).label},
    anom_mezclada: arMix && {pct: arMix.pct, n: arMix.n, med: +arMix.mediana.toFixed(3), veces: arMix.veces && +arMix.veces.toFixed(2)},
    anom_soloK: arK && {pct: arK.pct, n: arK.n, med: +arK.mediana.toFixed(3), veces: arK.veces && +arK.veces.toFixed(2)},
    base_C0: baseC0, base_K: baseK,
    corrob90: corr, nuestras90_far: nuestFar, nuestras90_C0: nuestC0, nuestras90_publicadas: nuestPub,
    met30: Object.fromEntries(Object.entries(met.byBucket).map(([k,o]) => [k, {tp:o.tp, fn:o.fn, fp:o.fp, recall: o.recall && +o.recall.toFixed(2)}])),
    met30_noche: Object.fromEntries(Object.entries(metNoche.byBucket).map(([k,o]) => [k, {tp:o.tp, fn:o.fn, fp:o.fp, recall: o.recall && +o.recall.toFixed(2)}])),
    mirova30_diurnas: nDia, mirova30_v375_noche_le005: nNone375 });
}
fs.writeFileSync(path.join(__dirname,"tarjetas_y_metricas.json"), JSON.stringify(res,null,1));
for (const r of res) console.log(JSON.stringify(r));
