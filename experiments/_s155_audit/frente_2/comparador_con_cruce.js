// Igual que predicados_tres_vistas.js pero con el cruce _mirova_confirmed que index.html aplica al cargar
// (enrichWithMirovaConfirmation) y que mosaico/diario no aplican. Mide si ese cinturón hace que index grafique un
// record que mosaico y diario ocultan como artefacto térmico (o al revés). Ventanas por fecha de observación.
"use strict";
const fs = require("fs"), path = require("path");
const { cargarVista } = require("./extraer.js");
const ROOT = path.resolve(__dirname, "../../..");
const NOW = Date.parse("2026-10-19T12:00:00Z");
const comunes = ["mirovaEqVrp","_havKm","f5CoreMagnitude","mirovaEqVrpCore","isCirrusArtifact","isDiffuseFieldArtifact","isThermalArtifact","parseUtcMs","isValidDetection"];
const IX = cargarVista(path.join(ROOT,"frontend/index.html"), comunes.concat(["mirovaEqVrpDisplay","ourSensorBucket","mirovaSensorBucket","sensorGroup","enrichWithMirovaConfirmation"]), ["PATH_D_CAP_MW","F5_R_CORE_KM","F5_BT_EXT_K"], "var USE_F5_CORE = true;", NOW);
const MO = cargarVista(path.join(ROOT,"frontend/mosaico.html"), comunes.concat(["eqVrpDisplay"]), ["PATH_D_CAP_MW","F5_R_CORE_KM","F5_BT_EXT_K"], "var USE_F5_CORE = true;", NOW);
const INNER = {Lascar:5,Lastarria:3,Tupungatito:7,Villarrica:5,PuyehueCordonCaulle:20,Copahue:4,NevadosDeChillan:5,Llaima:5,Chaiten:5,PlanchonPeteroa:3,Isluga:5};
const out = {};
for (const v of Object.keys(INNER)) {
  const recs = JSON.parse(fs.readFileSync(path.join(ROOT,"data/mirova_equivalent",v+".json"),"utf8")).records;
  const mr = JSON.parse(fs.readFileSync(path.join(ROOT,"data/mirova",v+".json"),"utf8")).records || [];
  // mosaico primero (sin cruce), después index con cruce sobre copias
  const mo = recs.map(r => MO.eqVrpDisplay(r, INNER[v]));
  const copia = recs.map(r => Object.assign({}, r));
  IX.enrichWithMirovaConfirmation(copia, mr);
  copia.forEach((r, i) => {
    const e = r.datetime_utc >= "2026-09-18" ? "K" : r.datetime_utc >= "2026-07-20" ? "C0" : "antes";
    const ix = IX.isThermalArtifact(r, INNER[v]) ? 0 : IX.mirovaEqVrpDisplay(r, INNER[v], false);
    if (Math.abs(ix - mo[i]) > 1e-9) { (out[e] ||= []).push([v, r.datetime_utc, r.sensor, +ix.toFixed(3), +mo[i].toFixed(3), r.t_max_k]); }
  });
}
for (const [e, l] of Object.entries(out)) { console.log(e, l.length); for (const x of l.slice(0, 8)) console.log("  ", JSON.stringify(x)); }
if (!Object.keys(out).length) console.log("0 diferencias en todas las eras");
