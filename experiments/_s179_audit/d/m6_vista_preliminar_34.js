// M6 (frente D, S179). Que muestra la vista publica preliminar de los 34 (frontend/preliminar_34.html, main 438a60a1e)
// con los datos de data/sombra_34/ de ese mismo commit. Ejecuta el modulo real frontend/preliminar_34.js (no una copia).
//
// Las dos preguntas del instrumento:
// 1. Si la vista pintara como "anomalia en cumbre" el calor del volcan vecino, esta medicion lo veria?  Si: para cada
//    deteccion calcula la distancia del foco (final_hotspot_lat/lon) a los 11 Tier A y lista las que caen a 5 km o menos
//    de un Tier A, con el estado que la vista les da.
// 2. Si el instrumento estuviera muerto?  Control positivo: una deteccion sintetica con un pixel a 1 km del volcan tiene
//    que salir "cumbre", y una con el foco a 20 km, "lejos". Y el numero de volcanes con archivo tiene que ser 34.
//
// Denominador: todos los records de los 34 archivos de data/sombra_34/ de 438a60a1e. Ventana de la vista: 14 dias hasta
// "ahora" = 2026-11-10T17:00:00Z (hora del merge de la base).
// Uso: node m6_vista_preliminar_34.js <snapshot main> <carpeta sombra_34> <salida.json>
const fs = require("fs");
const path = require("path");
const [MAIN, DIR, OUT] = process.argv.slice(2);
const P34 = require(path.join(MAIN, "frontend", "preliminar_34.js"));
const AHORA = Date.parse("2026-11-10T17:00:00Z");
const VENTANA = 14;
const TIER_A = { Lascar: [-23.37, -67.73], Lastarria: [-25.168, -68.507], Isluga: [-19.15, -68.83], Tupungatito: [-33.4, -69.8],
  PlanchonPeteroa: [-35.24, -70.57], NevadosDeChillan: [-36.863, -71.377], Copahue: [-37.85, -71.17], Llaima: [-38.692, -71.729],
  Villarrica: [-39.42, -71.93], PuyehueCordonCaulle: [-40.59, -72.117], Chaiten: [-42.833, -72.646] };
// las coordenadas de los Tier A se leen de volcanoes.yaml del snapshot (sin dependencia de yaml: expresion regular)
const yaml = fs.readFileSync(path.join(MAIN, "volcanoes.yaml"), "utf8");
const coords = {};
const re = /-\s+name:\s*"?([A-Za-z]+)"?[\s\S]*?\n\s+lat:\s*(-?[\d.]+)\s*\n\s+lon:\s*(-?[\d.]+)/g;
let m;
while ((m = re.exec(yaml)) !== null) coords[m[1]] = [parseFloat(m[2]), parseFloat(m[3])];
const tierA = {};
for (const k of Object.keys(TIER_A)) tierA[k] = coords[k] || null;
const faltan = Object.keys(tierA).filter((k) => !tierA[k]);

function hav(aLat, aLon, bLat, bLon) {
  const rad = Math.PI / 180, dLat = (bLat - aLat) * rad, dLon = (bLon - aLon) * rad;
  const x = Math.sin(dLat / 2) ** 2 + Math.cos(aLat * rad) * Math.cos(bLat * rad) * Math.sin(dLon / 2) ** 2;
  return 2 * 6371 * Math.asin(Math.sqrt(x));
}

// control positivo
const v0 = P34.VOLCANES[0];
const cerca = P34.clasificar({ vrp_mw: 1, final_hotspot_dist_km: 20, anomaly_pixels: [{ lat: v0.lat + 0.009, lon: v0.lon }] }, v0);
const lejos = P34.clasificar({ vrp_mw: 1, final_hotspot_dist_km: 20, anomaly_pixels: [{ lat: v0.lat + 0.2, lon: v0.lon }] }, v0);
const ctrl = cerca.estado === "cumbre" && lejos.estado === "lejos";

const filas = [];
let dets = [];
let conArchivo = 0, nRecords = 0, primera = null, ultima = null;
const marcas = {};
for (const v of P34.VOLCANES) {
  const f = path.join(DIR, v.name + ".json");
  if (!fs.existsSync(f)) { filas.push({ volcan: v.name, estado: "sin archivo" }); continue; }
  conArchivo++;
  const recs = JSON.parse(fs.readFileSync(f, "utf8")).records || [];
  nRecords += recs.length;
  for (const r of recs) {
    const k = String(r.via_codigo_mirova);
    marcas[k] = (marcas[k] || 0) + 1;
    if (!primera || r.datetime_utc < primera) primera = r.datetime_utc;
    if (!ultima || r.datetime_utc > ultima) ultima = r.datetime_utc;
  }
  const res = P34.resumenVolcan(recs, AHORA, VENTANA, v);
  let estado = "sin deteccion";
  if (res.n_cumbre > 0) estado = "anomalia en cumbre";
  else if (res.sin_pasadas_recientes) estado = "sin pasadas recientes";
  else if (res.n_lejos > 0 || res.n_sin_posicion > 0) estado = "foco lejano";
  filas.push({ volcan: v.name, estado, n_cumbre: res.n_cumbre, n_lejos: res.n_lejos, n_sin_posicion: res.n_sin_posicion,
    vrp_max: res.vrp_max, ultima_pasada: res.ultima_pasada });
  for (const r of recs) {
    const c = P34.clasificar(r, v);
    if (c.estado !== "sin_deteccion" && P34.msUtc(r.datetime_utc) >= AHORA - VENTANA * 86400000) {
      let vecino = null, dv = Infinity;
      if (r.final_hotspot_lat != null) {
        for (const [n, ll] of Object.entries(tierA)) {
          if (!ll) continue;
          const d = hav(r.final_hotspot_lat, r.final_hotspot_lon, ll[0], ll[1]);
          if (d < dv) { dv = d; vecino = n; }
        }
      }
      dets.push({ volcan: v.name, datetime_utc: r.datetime_utc, sensor: r.sensor, vrp_mw: r.vrp_mw, estado: c.estado,
        dist_km: c.dist_km, final_hotspot_lat: r.final_hotspot_lat, final_hotspot_lon: r.final_hotspot_lon,
        via: r.via_codigo_mirova, tier_a_mas_cercano: vecino, km_al_tier_a: isFinite(dv) ? Math.round(dv * 100) / 100 : null });
    }
  }
}
dets = P34.focosCompartidos(dets);
const cuenta = P34.contarFocos(dets);
const porEstado = {};
for (const f of filas) porEstado[f.estado] = (porEstado[f.estado] || 0) + 1;
const enTierA = dets.filter((d) => d.km_al_tier_a != null && d.km_al_tier_a <= 5);
console.log("CONTROL POSITIVO (pixel a 1 km -> cumbre; pixel a 22 km y foco a 20 km -> lejos):", ctrl ? "OK" : "FALLA");
console.log("coordenadas Tier A leidas de volcanoes.yaml:", Object.keys(tierA).length - faltan.length, "de 11", faltan.length ? "FALTAN " + faltan : "");
console.log("volcanes con archivo:", conArchivo, "de", P34.VOLCANES.length, "| records:", nRecords, "| de", primera, "a", ultima);
console.log("marca via_codigo_mirova de los records:", JSON.stringify(marcas));
console.log("estado que muestra la vista, por volcan:", JSON.stringify(porEstado));
console.log("detecciones en la ventana de 14 dias:", dets.length, "| focos distintos (como los cuenta la vista):", JSON.stringify(cuenta));
console.log("VRP maximo mostrado por volcan (los con deteccion):");
for (const f of filas.filter((x) => x.vrp_max > 0)) console.log("  ", f.volcan, f.estado, "VRP max", f.vrp_max.toFixed(2), "MW; cumbre", f.n_cumbre, "lejanos", f.n_lejos);
console.log("detecciones cuyo foco cae a 5 km o menos de un Tier A (calor del vecino visto desde la grilla del volcan nuevo):", enTierA.length);
for (const d of enTierA) console.log("  ", d.volcan, d.datetime_utc, d.sensor, d.vrp_mw.toFixed(2), "MW, estado", d.estado, "-> a", d.km_al_tier_a, "km de", d.tier_a_mas_cercano);
fs.writeFileSync(OUT, JSON.stringify({ ahora: "2026-11-10T17:00:00Z", control: ctrl, conArchivo, nRecords, primera, ultima, marcas, porEstado,
  n_detecciones: dets.length, focos: cuenta, filas, detecciones: dets }, null, 1));
