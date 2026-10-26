// F2-09: VIIRS 375 publicados con K (index.html literal): nucleo F5' (mostrado) contra cumulo pc.vrp_mw.
// Si nucleo > cumulo, el nucleo suma pixeles fuera del cumulo (la suma es aditiva). P2: n publicados > 0 por control.
const { evaluar, REPO } = require('./harness');
const fs = require('fs'), path = require('path');
const X = evaluar('index.html', '2026-10-19T12:00:00Z', '', ['mirovaEqVrpDisplay', 'mirovaEqVrp', 'isThermalArtifact', 'isValidDetection', 'getLevel', 'VOLCANOES_ALL']);
let n = 0, mayor = 0, menor = 0, igual = 0, cambiaNivel = 0, sumaPix = 0, sumaOk = 0; const ej = [];
for (const v of X.VOLCANOES_ALL.filter(v => v.hasMirova)) {
  const ik = v.inner_radius_km ?? 10;
  for (const r of JSON.parse(fs.readFileSync(path.join(REPO, 'data/mirova_equivalent', v.name + '.json'), 'utf8')).records) {
    if (!r.regimen) continue; const s = r.sensor; if (!(s.startsWith('VIIRS') && !s.endsWith('_750'))) continue;
    if (!X.isValidDetection(r) || X.isThermalArtifact(r, ik)) continue;
    const show = X.mirovaEqVrpDisplay(r, ik, false), clu = X.mirovaEqVrp(r, ik, false);
    if (!(show > 0)) continue; n++;
    // control de aditividad: suma de anomaly_pixels vs vrp del record
    const sp = (r.anomaly_pixels || []).reduce((a, p) => a + (p.vrp_mw || 0), 0); sumaPix++; if (Math.abs(sp - r.vrp_mw) / Math.max(r.vrp_mw, 1e-9) < 0.02) sumaOk++;
    if (show > clu * 1.001) mayor++; else if (show < clu * 0.999) menor++; else igual++;
    if (X.getLevel(show).label !== X.getLevel(clu).label) { cambiaNivel++; ej.push([v.name, r.datetime_utc, s, +clu.toFixed(3), +show.toFixed(3), X.getLevel(clu).label, '->', X.getLevel(show).label]); }
  }
}
console.log('V375 K publicados', n, 'nucleo>cumulo', mayor, 'nucleo<cumulo', menor, 'igual', igual, 'cambia nivel', cambiaNivel);
console.log('control aditividad: suma anomaly_pixels == vrp_mw del record (2 %) en', sumaOk, 'de', sumaPix);
for (const e of ej) console.log(JSON.stringify(e));
