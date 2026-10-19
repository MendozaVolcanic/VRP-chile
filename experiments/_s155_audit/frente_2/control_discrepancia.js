// Control positivo del comparador de vistas de predicados_tres_vistas.js: con diario en "Cluster" (USE_F5_CORE=false)
// y index en "Núcleo", el comparador TIENE que ver diferencias en VIIRS 375 (donde f5 != pc). Si da 0, el comparador
// está muerto. Denominador: records K (>= 2026-09-18) de los 11 Tier A.
"use strict";
const fs = require("fs"), path = require("path");
const { cargarVista } = require("./extraer.js");
const ROOT = path.resolve(__dirname, "../../..");
const NOW = Date.parse("2026-10-19T12:00:00Z");
const comunes = ["mirovaEqVrp","_havKm","f5CoreMagnitude","mirovaEqVrpCore","isCirrusArtifact","isDiffuseFieldArtifact","isThermalArtifact","parseUtcMs","isValidDetection"];
const IX = cargarVista(path.join(ROOT,"frontend/index.html"), comunes.concat(["mirovaEqVrpDisplay"]), ["PATH_D_CAP_MW","F5_R_CORE_KM","F5_BT_EXT_K"], "var USE_F5_CORE = true;", NOW);
const DI = cargarVista(path.join(ROOT,"frontend/diario.html"), comunes.concat(["eqVrpDisplay"]), ["INNER_RADIUS_KM","PATH_D_CAP_MW","F5_R_CORE_KM","F5_BT_EXT_K"], "var USE_F5_CORE = false; var includeFarDistance = false;", NOW);
const INNER = {Lascar:5,Lastarria:3,Tupungatito:7,Villarrica:5,PuyehueCordonCaulle:20,Copahue:4,NevadosDeChillan:5,Llaima:5,Chaiten:5,PlanchonPeteroa:3,Isluga:5};
let n = 0, dif = 0;
for (const v of Object.keys(INNER)) for (const r of JSON.parse(fs.readFileSync(path.join(ROOT,"data/mirova_equivalent",v+".json"),"utf8")).records) {
  if (r.datetime_utc < "2026-09-18") continue; n++;
  const a = IX.isThermalArtifact(r, INNER[v]) ? 0 : IX.mirovaEqVrpDisplay(r, INNER[v], false), b = DI.eqVrpDisplay(r, v);
  if (Math.abs(a-b) > 1e-9) dif++;
}
console.log("records K:", n, "diferencias index(Núcleo) vs diario(Cluster):", dif);
