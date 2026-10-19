// ¿Los filtros de artefacto térmico (cirrus t_max<0°C y VRP>10; campo difuso n_px>=100, VRP>=50, VRP/px<1, t_max<5°C),
// calibrados en S90/S93 sobre otro detector, ocultan algo con K? Cuenta records con mirovaEqVrp > 0 que el filtro
// oculta, por era. Control positivo: en la historia completa el filtro tiene que ocultar algo (si da 0 en todo, el
// instrumento no está midiendo). Denominador: 11 Tier A, records con mirovaEqVrp(solo cráter) > 0.
"use strict";
const fs = require("fs"), path = require("path");
const { cargarVista } = require("./extraer.js");
const ROOT = path.resolve(__dirname, "../../..");
const IX = cargarVista(path.join(ROOT,"frontend/index.html"), ["mirovaEqVrp","isCirrusArtifact","isDiffuseFieldArtifact","isThermalArtifact"], [], "", Date.parse("2026-10-19T12:00:00Z"));
const INNER = {Lascar:5,Lastarria:3,Tupungatito:7,Villarrica:5,PuyehueCordonCaulle:20,Copahue:4,NevadosDeChillan:5,Llaima:5,Chaiten:5,PlanchonPeteroa:3,Isluga:5};
const c = {};
for (const v of Object.keys(INNER)) for (const r of JSON.parse(fs.readFileSync(path.join(ROOT,"data/mirova_equivalent",v+".json"),"utf8")).records) {
  if (!(IX.mirovaEqVrp(r, INNER[v], false) > 0)) continue;
  const e = r.datetime_utc >= "2026-09-18" ? "K" : "historia_previa";
  const k = c[e] ||= {n:0, ocultos:0, ej:[]}; k.n++;
  if (IX.isThermalArtifact(r, INNER[v])) { k.ocultos++; if (e === "K") k.ej.push([v, r.datetime_utc, r.sensor, r.t_max_k, r.primary_cluster.vrp_mw]); }
}
console.log(JSON.stringify(c, null, 1));
