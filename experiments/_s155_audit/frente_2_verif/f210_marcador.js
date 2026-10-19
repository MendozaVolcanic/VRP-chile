// F2-10: records K publicados (index literal) cuyo final_hotspot_source no es ancla honesta: distancia del marcador
// (pixelesDelMarcador literal, primer punto) al centroide del cumulo publicado, y distancia en tabla vs cumulo.
const { evaluar, REPO } = require('./harness');
const fs = require('fs'), path = require('path');
const X = evaluar('index.html', '2026-10-19T12:00:00Z', '', ['mirovaEqVrpDisplay', 'isThermalArtifact', 'isValidDetection', 'pixelesDelMarcador', '_havKm', 'VOLCANOES_ALL']);
const fuentes = {}; const casos = [];
for (const v of X.VOLCANOES_ALL.filter(v => v.hasMirova)) {
  const ik = v.inner_radius_km ?? 10;
  for (const r of JSON.parse(fs.readFileSync(path.join(REPO, 'data/mirova_equivalent', v.name + '.json'), 'utf8')).records) {
    if (!r.regimen || !X.isValidDetection(r) || X.isThermalArtifact(r, ik) || !(X.mirovaEqVrpDisplay(r, ik, false) > 0)) continue;
    const k = r.sensor.slice(0, 5) + ':' + r.final_hotspot_source; fuentes[k] = (fuentes[k] || 0) + 1;
    if (['ctx_cluster', 'test1_roi', 'test1_nti_peak'].includes(r.final_hotspot_source)) continue;
    const m = X.pixelesDelMarcador(r, v)[0], pc = r.primary_cluster;
    const d = (m && pc) ? X._havKm(m.lat, m.lon, pc.centroid_lat, pc.centroid_lon) : null;
    const distTabla = r.hotspot_dist_km ?? r.final_hotspot_dist_km;
    casos.push([v.name, r.datetime_utc, r.sensor, r.final_hotspot_source, d == null ? null : +d.toFixed(2), 'tabla', distTabla, 'pc', pc && pc.centroid_dist_km]);
  }
}
console.log('fuentes de records K publicados:', JSON.stringify(fuentes));
casos.sort((a, b) => (b[4] || 0) - (a[4] || 0));
console.log('no-honestos publicados:', casos.length, 'marcador a >1 km del cumulo:', casos.filter(c => c[4] > 1).length);
for (const c of casos) console.log(JSON.stringify(c));
