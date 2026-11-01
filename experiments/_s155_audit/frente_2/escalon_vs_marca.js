// ¿Dónde cae el escalón C0 -> K que ve el operador en la tendencia de diario.html y dónde dibuja la marca?
// Usa el predicado literal de diario (eqVrpDisplay) y la fecha literal de frontend/cambio_detector.js.
// Pregunta 1: si la marca estuviera en el lugar del escalón, la tasa de barras antes y después del 2026-09-18 sería
//   parecida y el cambio caería en el 2026-10-18; esta tabla separa los tres tramos y lo vería.
// Pregunta 2: si el predicado no publicara nada (instrumento muerto), los tres tramos darían 0 en todos los volcanes;
//   Chillán en erupción tiene que dar barras en el tramo K (control positivo).
// Denominador: días-barra (día UTC con al menos un record graficado) por volcán y sensor, ventana de 90 d de diario
// terminada el 2026-10-19 12:00 UTC: tramo A = 2026-07-21..2026-09-17 (59 d), B = 2026-09-18..2026-10-17 (30 d),
// C = 2026-10-18..2026-10-19 (2 d).
"use strict";
const fs = require("fs"), path = require("path");
const { cargarVista } = require("./extraer.js");
const CD = require("../../../frontend/cambio_detector.js");
const ROOT = path.resolve(__dirname, "../../..");
const NOW = Date.parse("2026-10-19T12:00:00Z");
const TIER = ["Isluga","Lascar","Lastarria","Tupungatito","PlanchonPeteroa","NevadosDeChillan","Copahue","Llaima","Villarrica","PuyehueCordonCaulle","Chaiten"];
const DI = cargarVista(path.join(ROOT,"frontend/diario.html"),
  ["mirovaEqVrp","_havKm","f5CoreMagnitude","mirovaEqVrpCore","isCirrusArtifact","isDiffuseFieldArtifact","isThermalArtifact","parseUtcMs","isValidDetection","eqVrpDisplay","sensorBucket"],
  ["INNER_RADIUS_KM","PATH_D_CAP_MW","F5_R_CORE_KM","F5_BT_EXT_K"], "var USE_F5_CORE = true; var includeFarDistance = false;", NOW);
console.log("marca de cambio_detector.js:", CD.CAMBIO_DETECTOR_UTC, "| texto:", CD.textoAviso(CD.CAMBIO_DETECTOR_UTC));
const tramo = d => d < "2026-07-21" ? null : d < "2026-09-18" ? "A" : d < "2026-10-18" ? "B" : "C";
const largo = {A:59, B:30, C:2};
console.log("\nvolcan sensor | dias-barra A/59  B/30  C/2 | fraccion A  B  C | mediana MW A  B");
const filas = [];
for (const v of TIER) {
  const recs = JSON.parse(fs.readFileSync(path.join(ROOT,"data/mirova_equivalent",v+".json"),"utf8")).records;
  for (const b of ["MODIS","VIIRS375","VIIRS750"]) {
    const dias = {A:new Set(),B:new Set(),C:new Set()}, vals = {A:[],B:[],C:[]};
    for (const r of recs) {
      const t = DI.parseUtcMs(r.datetime_utc); if (!(t >= NOW - 90*86400000 && t <= NOW)) continue;
      if (DI.sensorBucket(r.sensor) !== b) continue;
      const x = DI.eqVrpDisplay(r, v); if (!(x > 0)) continue;
      const d = r.datetime_utc.slice(0,10), tr = tramo(d); if (!tr) continue;
      dias[tr].add(d); vals[tr].push(x);
    }
    const med = a => { if(!a.length) return null; const s=a.slice().sort((p,q)=>p-q); return s[s.length>>1]; };
    const f = k => (dias[k].size/largo[k]).toFixed(2);
    filas.push({v,b,A:dias.A.size,B:dias.B.size,C:dias.C.size,medA:med(vals.A),medB:med(vals.B)});
    console.log(`${v.padEnd(20)} ${b.padEnd(8)} | ${String(dias.A.size).padStart(3)} ${String(dias.B.size).padStart(5)} ${String(dias.C.size).padStart(4)} | ${f("A")} ${f("B")} ${f("C")} | ${med(vals.A)==null?"-":med(vals.A).toFixed(3)} ${med(vals.B)==null?"-":med(vals.B).toFixed(3)}`);
  }
}
fs.writeFileSync(path.join(__dirname,"escalon_vs_marca.json"), JSON.stringify(filas,null,1));
