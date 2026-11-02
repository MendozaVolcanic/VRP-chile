// V1: marcador por defecto de un record de la via (final_hotspot_source=codigo_mirova) en index.html de A y de B.
const fs = require('fs');
function extraer(src, nombre) {
  const i = src.indexOf('function ' + nombre + '(');
  if (i < 0) return null;
  let j = src.indexOf('{', i), d = 0;
  for (let k = j; k < src.length; k++) { if (src[k] === '{') d++; else if (src[k] === '}') { d--; if (d === 0) return src.slice(i, k + 1); } }
}
const LEJOS = {lat: -36.73, lon: -71.37, dist_km: 14.89, vrp_mw: 0.4};
const CERCA = {lat: -36.86, lon: -71.37, dist_km: 0.4, vrp_mw: 1.0};
function rec(f) { return {final_hotspot_source: f, final_hotspot_lat: -36.864, final_hotspot_lon: -71.377, final_hotspot_dist_km: 0.567, vrp_mw: 2.0, t_max_k: 300, anomaly_pixels: [LEJOS, CERCA]}; }
for (const tag of ['A', 'B']) {
  const src = fs.readFileSync(process.argv[2] + '/index_' + tag + '.html', 'utf8');
  const ea = extraer(src, 'esAnclaHonesta'); if (ea) eval(ea);
  eval(extraer(src, 'pixelesDelMarcador'));
  for (const f of ['codigo_mirova', 'ctx_cluster', 'vent']) {
    const px = pixelesDelMarcador(rec(f), {});
    console.log(tag, f, 'marcador[0].dist_km=', px[0].dist_km, 'tieneEsAnclaHonesta=', !!ea);
  }
}
