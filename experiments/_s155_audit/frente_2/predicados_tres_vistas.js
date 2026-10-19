// Ejecuta los predicados LITERALES de las tres vistas live sobre los JSON reales (A97).
//
// Pregunta 1: si un predicado de una vista estuviera roto respecto de las otras, esto lo ve: compara, record por
//   record, el valor que grafica cada vista (index eqVrp del detalle, diario eqVrpDisplay, mosaico eqVrpDisplay).
// Pregunta 2: si el extractor no cargara la función, cargarVista lanza error (no da cero). Si los JSON no se leyeran,
//   el denominador sale 0 y se imprime.
// Control positivo: con includeFar=true la vista index debe mostrar MÁS records que con false (se imprime).
// Denominador: records de los 11 Tier A en data/mirova_equivalent/*.json del worktree cb90031a.
// Ventanas por fecha de observación: C0 = 2026-07-20..2026-09-17 (60 d), K = 2026-09-18..2026-10-19.
"use strict";
const fs = require("fs"), path = require("path");
const { cargarVista } = require("./extraer.js");
const ROOT = path.resolve(__dirname, "../../..");
const NOW = Date.parse("2026-10-19T12:00:00Z");
const TIER = ["Isluga","Lascar","Lastarria","Tupungatito","PlanchonPeteroa","NevadosDeChillan","Copahue","Llaima","Villarrica","PuyehueCordonCaulle","Chaiten"];
const INNER = {Lascar:5,Lastarria:3,Tupungatito:7,Villarrica:5,PuyehueCordonCaulle:20,Copahue:4,NevadosDeChillan:5,Llaima:5,Chaiten:5,PlanchonPeteroa:3,Isluga:5};

const comunes = ["mirovaEqVrp","_havKm","f5CoreMagnitude","mirovaEqVrpCore","isCirrusArtifact","isDiffuseFieldArtifact","isThermalArtifact","parseUtcMs","isValidDetection"];
const IX = cargarVista(path.join(ROOT,"frontend/index.html"),
  comunes.concat(["mirovaEqVrpDisplay","isSummitDetection","latestDetection","sensorGroup","isSensorVisible","getLevel","esValorCensurado","anomaliaRelativa","distanceCounts","corroboracionMirova","ourSensorBucket","mirovaSensorBucket","computeMetrics","enrichWithMirovaConfirmation"]),
  ["PATH_D_CAP_MW","F5_R_CORE_KM","F5_BT_EXT_K","LEVELS"],
  "var USE_F5_CORE = true; var includeFarDistance = false; var sensorVisible = {MODIS:true,VIIRS375:true,VIIRS750:true,MIROVA:true};", NOW);
const DI = cargarVista(path.join(ROOT,"frontend/diario.html"),
  comunes.concat(["eqVrpDisplay","sensorBucket"]),
  ["INNER_RADIUS_KM","PATH_D_CAP_MW","F5_R_CORE_KM","F5_BT_EXT_K"],
  "var USE_F5_CORE = true; var includeFarDistance = false;", NOW);
const MO = cargarVista(path.join(ROOT,"frontend/mosaico.html"),
  comunes.concat(["eqVrpDisplay","isSummitDetection","latestVRP","getLevel"]),
  ["PATH_D_CAP_MW","F5_R_CORE_KM","F5_BT_EXT_K","LEVELS"],
  "var USE_F5_CORE = true;", NOW);

function bucket(s){ s=String(s||""); if(s.startsWith("MODIS"))return "MODIS"; if(s.endsWith("_750"))return "V750"; if(s.startsWith("VIIRS"))return "V375"; return "?"; }
function era(r){ const d=(r.datetime_utc||"").slice(0,10); if(d>="2026-09-18") return "K"; if(d>="2026-07-20") return "C0"; return null; }
const med = a => { if(!a.length) return null; const s=a.slice().sort((x,y)=>x-y); const m=s.length>>1; return s.length%2?s[m]:(s[m-1]+s[m])/2; };

const out = { tabla: [], discrepancias: [], control: {} };
let nTot = 0, nFarCtl = [0,0];
for (const v of TIER) {
  const d = JSON.parse(fs.readFileSync(path.join(ROOT,"data/mirova_equivalent",v+".json"),"utf8"));
  const inner = INNER[v];
  const agg = {};
  for (const r of d.records) {
    nTot++;
    const e = era(r); if (!e) continue;
    const b = bucket(r.sensor);
    const k = v+"|"+b+"|"+e;
    const a = agg[k] ||= {vol:v,sensor:b,era:e,n:0,n_mark:0,shown:0,vals:[],t1:0,src:{},dc:{},f5:0,f5num:0,valid:0,summit:0,pcfar_summit:0};
    a.n++;
    if (r.regimen && r.regimen.codigo_sha) a.n_mark++;
    if (r.triggered_test1) a.t1++;
    a.src[r.final_hotspot_source||"null"]=(a.src[r.final_hotspot_source||"null"]||0)+1;
    a.dc[r.distance_class||"null"]=(a.dc[r.distance_class||"null"]||0)+1;
    if (IX.isValidDetection(r)) a.valid++;
    if (IX.isSummitDetection(r)) a.summit++;
    const ix = IX.isThermalArtifact(r, inner) ? 0 : IX.mirovaEqVrpDisplay(r, inner, false);
    const di = DI.eqVrpDisplay(r, v);
    const mo = MO.eqVrpDisplay(r, inner);
    if (ix > 0) { a.shown++; a.vals.push(ix); if (b==="V375") { a.f5++; if (typeof r.f5_core_vrp_mw === "number") a.f5num++; } }
    // control positivo: includeFar aumenta lo mostrado
    if (IX.mirovaEqVrp(r, inner, false) > 0) nFarCtl[0]++;
    if (IX.mirovaEqVrp(r, inner, true) > 0) nFarCtl[1]++;
    const close = (x,y)=>Math.abs(x-y) < 1e-9;
    if (!close(ix,di) || !close(ix,mo)) out.discrepancias.push({vol:v,dt:r.datetime_utc,sensor:r.sensor,ix,di,mo,dc:r.distance_class,pcd:r.primary_cluster&&r.primary_cluster.centroid_dist_km});
  }
  for (const a of Object.values(agg)) { a.med = med(a.vals); a.max = a.vals.length?Math.max(...a.vals):null; delete a.vals; out.tabla.push(a); }
}
out.control = { n_total_records: nTot, mostrados_solo_crater: nFarCtl[0], mostrados_incluir_lejanas: nFarCtl[1] };
fs.writeFileSync(path.join(__dirname,"predicados_tres_vistas.json"), JSON.stringify(out,null,1));
console.log("control:", JSON.stringify(out.control));
console.log("discrepancias entre vistas (records C0+K ventanas):", out.discrepancias.length);
for (const x of out.discrepancias.slice(0,15)) console.log("  ", JSON.stringify(x));
console.log("\nvol sensor era | n n_marca | t1 | validos summit mostrados | med max | f5num/mostrados375 | fuentes");
for (const a of out.tabla.sort((x,y)=>(x.vol+x.sensor+x.era).localeCompare(y.vol+y.sensor+y.era)))
  console.log(`${a.vol.padEnd(20)} ${a.sensor.padEnd(5)} ${a.era.padEnd(3)}| ${String(a.n).padStart(4)} ${String(a.n_mark).padStart(4)} | ${String(a.t1).padStart(3)} | ${String(a.valid).padStart(4)} ${String(a.summit).padStart(4)} ${String(a.shown).padStart(4)} | ${a.med==null?"-":a.med.toFixed(3)} ${a.max==null?"-":a.max.toFixed(2)} | ${a.f5num}/${a.f5} | ${JSON.stringify(a.src)}`);
