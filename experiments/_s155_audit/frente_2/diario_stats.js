// Encabezado de cada tarjeta de diario.html (computeStats literal): "det. nuestras · MIROVA: N alertas · Max VRP ·
// mediana" sobre la ventana por defecto de 90 d, con todos los records (lo que ve el operador) y con sólo los de la
// ventana K (2026-09-18 en adelante), para medir cuánto del número viene de C0.
// Pregunta 1: si el número no dependiera del detector, las dos columnas darían proporciones parecidas.
// Pregunta 2: si computeStats no corriera, n_det_us sería 0 en Chillán en erupción (control positivo: debe ser > 0
//   también en la columna K).
// Denominador: 11 Tier A, período 90 d terminado el 2026-10-19 12:00 UTC; referencia data/mirova/<v>.json.
"use strict";
const fs = require("fs"), path = require("path");
const { cargarVista } = require("./extraer.js");
const ROOT = path.resolve(__dirname, "../../..");
const NOW = Date.parse("2026-10-19T12:00:00Z");
const DI = cargarVista(path.join(ROOT,"frontend/diario.html"),
  ["mirovaEqVrp","_havKm","f5CoreMagnitude","mirovaEqVrpCore","isCirrusArtifact","isDiffuseFieldArtifact","isThermalArtifact","parseUtcMs","isValidDetection","eqVrpDisplay","applyS38Filter","computeStats"],
  ["INNER_RADIUS_KM","PATH_D_CAP_MW","F5_R_CORE_KM","F5_BT_EXT_K"],
  "var USE_F5_CORE = true; var includeFarDistance = false; var enPeriodo = (ms) => ms >= " + (NOW - 90*86400000) + " && ms <= " + NOW + ";", NOW);
const TIER = ["Isluga","Lascar","Lastarria","Tupungatito","PlanchonPeteroa","NevadosDeChillan","Copahue","Llaima","Villarrica","PuyehueCordonCaulle","Chaiten"];
console.log("volcan | det.nuestras todo / sólo K | MIROVA alertas todo / desde 09-18 | Max todo / K | mediana todo / K");
for (const v of TIER) {
  const d = JSON.parse(fs.readFileSync(path.join(ROOT,"data/mirova_equivalent",v+".json"),"utf8"));
  const m = JSON.parse(fs.readFileSync(path.join(ROOT,"data/mirova",v+".json"),"utf8"));
  const mref = (m.records||[]).map(x => ({dt:x.datetime_utc, sensor:x.sensor, vrp:parseFloat(x.VRP_MW)||0, dist: Number.isFinite(parseFloat(x.distancia_km))?parseFloat(x.distancia_km):null}));
  const todo = DI.computeStats(d, mref, v);
  const soloK = DI.computeStats({records: d.records.filter(r => r.datetime_utc >= "2026-09-18")}, mref.filter(x => x.dt >= "2026-09-18"), v);
  const f = x => x == null ? "-" : (+x).toFixed(3);
  console.log(`${v.padEnd(20)} | ${String(todo.n_det_us).padStart(4)} / ${String(soloK.n_det_us).padStart(4)} | ${String(todo.n_det_mirova).padStart(4)} / ${String(soloK.n_det_mirova).padStart(4)} | ${f(todo.max_us)} / ${f(soloK.max_us)} | ${f(todo.median_us)} / ${f(soloK.median_us)}`);
}
