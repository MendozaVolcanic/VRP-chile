// Gráfico «distancia vs tiempo» del detalle de index.html: buildDistanceData literal (función anidada en renderDetail,
// extraída por texto) sobre 90 d, antes y después de la frontera de datos 2026-09-18.
// Pregunta 1: si la serie cruzara la frontera sin escalón, la fracción de puntos en 0,0 km sería parecida a ambos
//   lados; si hay escalón por cambio de ancla (test1_roi -> ctx_cluster), lo ve.
// Pregunta 2: si la función extraída no devolviera puntos, n_A y n_B salen 0 en todos los volcanes (se imprime).
// Denominador: puntos del gráfico con período = 90 d terminado el 2026-10-19 12:00 UTC, toggle «Solo cráter».
"use strict";
const fs = require("fs"), path = require("path"), vm = require("vm");
const { cargarVista } = require("./extraer.js");
const ROOT = path.resolve(__dirname, "../../..");
const NOW = Date.parse("2026-10-19T12:00:00Z");
const src = fs.readFileSync(path.join(ROOT,"frontend/index.html"),"utf8").split(/\r?\n/);
const i0 = src.findIndex(l => l.startsWith("  function buildDistanceData() {"));
let i1 = i0 + 1; while (src[i1] !== "  }") i1++;
const cuerpo = src.slice(i0, i1 + 1).join("\n");
const IX = cargarVista(path.join(ROOT,"frontend/index.html"),
  ["parseUtcMs","isValidDetection","sensorGroup","isSensorVisible"], [],
  "var sensorVisible = {MODIS:true,VIIRS375:true,VIIRS750:true,MIROVA:true};", NOW);
const TIER = ["Isluga","Lascar","Lastarria","Tupungatito","PlanchonPeteroa","NevadosDeChillan","Copahue","Llaima","Villarrica","PuyehueCordonCaulle","Chaiten"];
const INNER = {Lascar:5,Lastarria:3,Tupungatito:7,Villarrica:5,PuyehueCordonCaulle:20,Copahue:4,NevadosDeChillan:5,Llaima:5,Chaiten:5,PlanchonPeteroa:3,Isluga:5};
const med = a => { if (!a.length) return null; const s = a.slice().sort((x,y)=>x-y); return s[s.length>>1]; };
console.log("volcan | n_A n_B | en 0,0 km A  B | mediana km A  B");
for (const v of TIER) {
  const recs = JSON.parse(fs.readFileSync(path.join(ROOT,"data/mirova_equivalent",v+".json"),"utf8")).records
    .filter(r => IX.parseUtcMs(r.datetime_utc) >= NOW - 90*86400000);
  const ctx = Object.assign(IX.__ctx, { filtered: recs, innerKm: INNER[v], includeFarDistance: false });
  vm.runInContext(cuerpo + "\nthis.__pts = buildDistanceData();", ctx);
  const pts = ctx.__pts;
  const A = pts.filter(p => p.x < "2026-09-18"), B = pts.filter(p => p.x >= "2026-09-18");
  const z = a => a.filter(p => p.y === 0).length;
  console.log(`${v.padEnd(20)} | ${String(A.length).padStart(4)} ${String(B.length).padStart(4)} | ${(A.length?z(A)/A.length:0).toFixed(2)} ${(B.length?z(B)/B.length:0).toFixed(2)} | ${med(A.map(p=>p.y))} ${med(B.map(p=>p.y))}`);
}
