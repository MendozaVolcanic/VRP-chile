// S193 mapas: la fracción de agua que calcula el navegador (frontend/agua.js) contra la máscara JRC a 30 m de
// experiments/_s193_lagos/medir_agua.py, píxel por píxel (pixeles.csv, 41.989 píxeles de la vía).
// POR QUÉ: comparar_fraccion.py mide la capa con shapely; esto mide el código que de verdad corre en el tablero.
// Uso: node comparar_js.js <pixeles.csv> <dir_geojson> <frontend/agua.js>  > comparar_js.txt
"use strict";
const fs = require("fs");
const path = require("path");
const [csvPath, dirGj, modPath] = process.argv.slice(2);
const A = require(path.resolve(modPath));
const PASO = { MODIS: "MODIS_TERRA", V750: "VIIRS_NOAA20_750", V375: "VIIRS_NOAA20" };
const lineas = fs.readFileSync(csvPath, "utf8").trim().split(/\r?\n/);
const cab = lineas.shift().split(",");
const ix = n => cab.indexOf(n);
const capas = {};
let n = 0, ambos = 0, tierra = 0, soloJrc = 0, soloJs = 0, sinMedir = 0, maxDif = 0;
const difs = [];
const t0 = Date.now();
for (const l of lineas) {
  const c = l.split(",");
  const v = c[ix("volcan")];
  if (!(v in capas)) capas[v] = JSON.parse(fs.readFileSync(path.join(dirGj, v + ".geojson"), "utf8"));
  const lado = A.ladoCeldaKm(PASO[c[ix("familia")]]);
  const f = A.fraccionAgua(capas[v], +c[ix("lat")], +c[ix("lon")], lado);
  if (f === null) { sinMedir++; continue; }
  const fj = +c[ix("frac_agua")];
  const a = fj >= 0.5, b = f >= A.UMBRAL_CELDA;
  n++;
  if (a && b) ambos++; else if (!a && !b) tierra++; else if (a) soloJrc++; else soloJs++;
  const d = Math.abs(f - fj); difs.push(d); if (d > maxDif) maxDif = d;
}
difs.sort((x, y) => x - y);
console.log("píxeles comparados: " + n + " (fuera de la ventana: " + sinMedir + ")");
console.log("agua en JRC 30 m y en agua.js: " + ambos);
console.log("tierra en los dos: " + tierra);
console.log("agua sólo en JRC: " + soloJrc);
console.log("agua sólo en agua.js: " + soloJs);
console.log("acuerdo: " + ((ambos + tierra) / n * 100).toFixed(3) + " %");
console.log("|fracción agua.js - fracción JRC|: mediana " + difs[difs.length >> 1].toFixed(4) + ", p99 " +
            difs[Math.floor(difs.length * 0.99)].toFixed(4) + ", máx " + maxDif.toFixed(4));
console.log("tiempo por píxel (ms): " + ((Date.now() - t0) / (n + sinMedir)).toFixed(3));
