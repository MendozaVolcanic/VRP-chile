// F2-08: records sin marca de regimen dentro de la ventana K: ¿los publica index.html (predicado literal)? ¿hay gemelo K?
const { evaluar, REPO } = require('./harness');
const fs = require('fs'), path = require('path');
const X = evaluar('index.html', '2026-10-19T12:00:00Z', '', ['mirovaEqVrpDisplay', 'isThermalArtifact', 'isValidDetection', 'isSummitDetection', 'VOLCANOES_ALL']);
let n = 0, pub = 0;
for (const v of X.VOLCANOES_ALL.filter(v => v.hasMirova)) {
  const recs = JSON.parse(fs.readFileSync(path.join(REPO, 'data/mirova_equivalent', v.name + '.json'), 'utf8')).records;
  const ik = v.inner_radius_km ?? 10;
  const claves = {}; for (const r of recs) { const k = r.datetime_utc + '|' + r.sensor; claves[k] = (claves[k] || 0) + 1; }
  const dup = Object.values(claves).filter(c => c > 1).length;
  for (const r of recs.filter(r => r.datetime_utc >= '2026-09-18' && !r.regimen)) {
    n++;
    const val = (!X.isValidDetection(r) || X.isThermalArtifact(r, ik)) ? 0 : X.mirovaEqVrpDisplay(r, ik, false);
    if (val > 0) { pub++; console.log('PUBLICADO', v.name, r.datetime_utc, r.sensor, val, r.granule); }
  }
  if (dup) console.log(v.name, 'claves (hora|sensor) repetidas en todo el archivo:', dup);
}
console.log('sin marca en ventana K:', n, 'publicados:', pub);
