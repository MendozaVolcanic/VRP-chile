// M7 (frente D, S179). Donde pone el tablero la linea vertical de "cambio a la via" de MODIS si queda K residual tras
// el reemplazo. Ejecuta primeraVia y notarRecords del modulo real frontend/cambio_detector.js de 438a60a1e.
// Pregunta 1: si un K residual moviera la linea a una fecha falsa, esto lo veria?  Si: compara la fecha devuelta.
// Pregunta 2 (control): con los datos de hoy (K hasta el 2026-11-01, via desde el 2026-11-02) tiene que dar 2026-11-02;
// con una serie entera de la via tiene que dar null.
// Uso: node m7_linea_via_con_k_residual.js <snapshot main> <carpeta mirova_equivalent de la base>
const path = require("path"), fs = require("fs");
const [MAIN, DIR] = process.argv.slice(2);
const CD = require(path.join(MAIN, "frontend", "cambio_detector.js"));
const leer = (v) => JSON.parse(fs.readFileSync(path.join(DIR, v + ".json"), "utf8")).records;
const esModis = (r) => String(r.sensor || "").startsWith("MODIS");
const hoy = leer("Villarrica");
console.log("control, Villarrica hoy (438a60a1e):", CD.primeraVia(hoy, "MODIS"));
const todoVia = hoy.map((r) => (esModis(r) ? { ...r, via_codigo_mirova: true } : r));
console.log("control, Villarrica con MODIS entero de la via:", CD.primeraVia(todoVia, "MODIS"));
// opcion 2 del plan (seccion 3): Tupungatito queda con K antes del 2026-02-23 y con la via despues
const tup = leer("Tupungatito").map((r) => (esModis(r) && r.datetime_utc.slice(0, 10) >= "2026-02-23" ? { ...r, via_codigo_mirova: true } : r));
console.log("Tupungatito con K antes del 2026-02-23 y la via despues:", CD.primeraVia(tup, "MODIS"));
// regla B del plan (2.3): una sola pasada K de borde conservada en 2025 en un volcan
const unK = todoVia.map((r) => r);
const i = unK.findIndex((r) => esModis(r) && r.datetime_utc.slice(0, 10) >= "2025-06-01");
unK[i] = { ...unK[i], via_codigo_mirova: undefined };
console.log("Villarrica con una sola pasada K conservada (" + unK[i].datetime_utc + "):", CD.primeraVia(unK, "MODIS"));
// lo que ve cada vista: notarRecords guarda la fecha mas temprana de todos los volcanes cargados
CD.notarRecords(todoVia, null); const a = CD.notarRecords(tup, null);
console.log("notarRecords tras cargar Villarrica (toda via) y Tupungatito (K antes del 02-23): linea de MODIS en", a);
