// Panel "Métricas vs MIROVA (live) por sensor" de index.html (computeMetrics literal), 30 d por defecto, en tres
// variantes de la referencia: (a) la que usa el panel; (b) sin alertas diurnas (la réplica es sólo nocturna,
// ENABLE_DAYTIME_* = False en pipeline.profile); (c) además sin VIIRS 375 <= 0,05 MW (regla SN de D-9, CLAUDE.md
// glosario "Recall"). Si (b) o (c) cambian TP/FN, el panel está contando como pérdidas cosas que no lo son.
// Denominador: 11 Tier A, 2026-09-19 12:00 a 2026-10-19 12:00 UTC.
"use strict";
const fs = require("fs"), path = require("path");
const { cargarVista } = require("./extraer.js");
const ROOT = path.resolve(__dirname, "../../..");
const NOW = Date.parse("2026-10-19T12:00:00Z");
const IX = cargarVista(path.join(ROOT,"frontend/index.html"),
  ["mirovaEqVrp","_havKm","f5CoreMagnitude","mirovaEqVrpCore","mirovaEqVrpDisplay","isCirrusArtifact","isDiffuseFieldArtifact","isThermalArtifact","parseUtcMs","isValidDetection","sensorGroup","ourSensorBucket","mirovaSensorBucket","computeMetrics","enrichWithMirovaConfirmation"],
  ["PATH_D_CAP_MW","F5_R_CORE_KM","F5_BT_EXT_K"], "var USE_F5_CORE = true;", NOW);
const INNER = {Lascar:5,Lastarria:3,Tupungatito:7,Villarrica:5,PuyehueCordonCaulle:20,Copahue:4,NevadosDeChillan:5,Llaima:5,Chaiten:5,PlanchonPeteroa:3,Isluga:5};
const tot = {a:{}, b:{}, c:{}};
const s = (m) => Object.fromEntries(Object.entries(m.byBucket).map(([k,o]) => [k, `${o.tp}/${o.tp+o.fn}`]));
for (const v of Object.keys(INNER)) {
  const recs = JSON.parse(fs.readFileSync(path.join(ROOT,"data/mirova_equivalent",v+".json"),"utf8")).records.filter(r => IX.parseUtcMs(r.datetime_utc) >= NOW - 30*86400000);
  const mr = (JSON.parse(fs.readFileSync(path.join(ROOT,"data/mirova",v+".json"),"utf8")).records || []).filter(r => IX.parseUtcMs(r.datetime_utc) >= NOW - 30*86400000);
  IX.enrichWithMirovaConfirmation(recs, mr);
  const a = IX.computeMetrics(recs, mr, INNER[v], false);
  const b = IX.computeMetrics(recs, mr.filter(r => r.dia !== true), INNER[v], false);
  const c = IX.computeMetrics(recs, mr.filter(r => r.dia !== true && !(r.sensor === "VIIRS375" && parseFloat(r.VRP_MW) <= 0.05)), INNER[v], false);
  console.log(v.padEnd(20), "panel", JSON.stringify(s(a)), "| sin diurnas", JSON.stringify(s(b)), "| + regla SN", JSON.stringify(s(c)));
  for (const [k, m] of [["a",a],["b",b],["c",c]]) for (const [bk,o] of Object.entries(m.byBucket)) { const t = tot[k][bk] ||= {tp:0,fn:0}; t.tp += o.tp; t.fn += o.fn; }
}
for (const k of ["a","b","c"]) console.log("TOTAL", k, JSON.stringify(Object.fromEntries(Object.entries(tot[k]).map(([bk,o]) => [bk, `${o.tp}/${o.tp+o.fn} = ${(o.tp/(o.tp+o.fn)).toFixed(3)}`]))));
