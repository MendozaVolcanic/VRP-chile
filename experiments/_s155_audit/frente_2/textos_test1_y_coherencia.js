// (1) Textos que suponen el Test 1: ¿cuántas detecciones publicadas con K caen en "en el cráter (ancla)" (tarjeta,
//     det.dist < 0.05) o "cráter" (tabla, ancla honesta y dist === 0)? En C0 eso era el ancla test1_roi; con K la
//     fuente es ctx_cluster, una medición.
// (2) Coherencia gráfico/tarjeta: records que el gráfico grafica (eqVrp > 0) y la tarjeta descarta (isSummitDetection
//     false), y al revés, por era.
// Pregunta 1: si los textos no se dispararan nunca con K, el conteo da 0 (y en C0 da > 0: control positivo).
// Pregunta 2: el instrumento cuenta records con distancia no nula; si el campo faltara, n_con_dist sale 0 y se imprime.
// Denominador: records de los 11 Tier A, eras por fecha de observación C0 = 2026-07-20..2026-09-17, K = 2026-09-18..
"use strict";
const fs = require("fs"), path = require("path");
const { cargarVista } = require("./extraer.js");
const ROOT = path.resolve(__dirname, "../../..");
const NOW = Date.parse("2026-10-19T12:00:00Z");
const TIER = ["Isluga","Lascar","Lastarria","Tupungatito","PlanchonPeteroa","NevadosDeChillan","Copahue","Llaima","Villarrica","PuyehueCordonCaulle","Chaiten"];
const INNER = {Lascar:5,Lastarria:3,Tupungatito:7,Villarrica:5,PuyehueCordonCaulle:20,Copahue:4,NevadosDeChillan:5,Llaima:5,Chaiten:5,PlanchonPeteroa:3,Isluga:5};
const IX = cargarVista(path.join(ROOT,"frontend/index.html"),
  ["mirovaEqVrp","_havKm","f5CoreMagnitude","mirovaEqVrpCore","mirovaEqVrpDisplay","isCirrusArtifact","isDiffuseFieldArtifact","isThermalArtifact","parseUtcMs","isValidDetection","isSummitDetection"],
  ["PATH_D_CAP_MW","F5_R_CORE_KM","F5_BT_EXT_K"], "var USE_F5_CORE = true;", NOW);
const era = r => { const d = r.datetime_utc.slice(0,10); return d >= "2026-09-18" ? "K" : d >= "2026-07-20" ? "C0" : null; };
const c = {C0:{pub:0,con_dist:0,ancla_tarjeta:0,cráter_tabla:0,src:{},graf_no_tarj:0,tarj_no_graf:0,ej:[]},K:{pub:0,con_dist:0,ancla_tarjeta:0,cráter_tabla:0,src:{},graf_no_tarj:0,tarj_no_graf:0,ej:[]}};
for (const v of TIER) {
  for (const r of JSON.parse(fs.readFileSync(path.join(ROOT,"data/mirova_equivalent",v+".json"),"utf8")).records) {
    const e = era(r); if (!e) continue; const a = c[e]; const inner = INNER[v];
    const graf = !IX.isThermalArtifact(r, inner) && IX.mirovaEqVrpDisplay(r, inner, false) > 0;
    const tarj = IX.isSummitDetection(r) && IX.isValidDetection(r) && graf;
    if (graf && !IX.isSummitDetection(r)) { a.graf_no_tarj++; if (a.ej.length < 5) a.ej.push([v, r.datetime_utc, r.sensor, r.distance_class, r.vrp_mw, r.discarded_reason, r.vrp_vent_mw]); }
    if (IX.isSummitDetection(r) && IX.isValidDetection(r) && !graf) a.tarj_no_graf++;
    if (!tarj) continue;
    a.pub++;
    const honest = ["ctx_cluster","test1_roi","test1_nti_peak"].includes(r.final_hotspot_source);
    const pc = r.primary_cluster || {};
    const dist = (honest ? r.final_hotspot_dist_km : null) ?? pc.centroid_dist_km ?? null;
    if (dist != null) a.con_dist++;
    if (dist != null && dist < 0.05) { a.ancla_tarjeta++; a.src[r.final_hotspot_source] = (a.src[r.final_hotspot_source]||0)+1; }
    if (honest && r.final_hotspot_dist_km === 0) a.cráter_tabla++;
  }
}
console.log(JSON.stringify(c, null, 1));
fs.writeFileSync(path.join(__dirname,"textos_test1_y_coherencia.json"), JSON.stringify(c,null,1));
