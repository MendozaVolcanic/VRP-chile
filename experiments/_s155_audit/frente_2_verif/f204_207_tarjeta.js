// F2-04 (anomalia relativa) y F2-07 (corroboracion) con las funciones LITERALES de index.html.
// Variante: mismas funciones, pero alimentadas solo con records K (observacion >= 2026-09-18).
// P1: si la base mezclara regimenes, ¿lo veria? Si: comparo literal contra solo-K. P2: anomalia null = "sin historia"
//     (<10), se informa como null y no como 0. Control +: Chillan (en erupcion) debe tener det no nulo.
const { evaluar, REPO } = require('./harness');
const fs = require('fs'), path = require('path');
const AHORA = process.argv[2] || '2026-10-19T12:00:00Z';
const X = evaluar('index.html', AHORA, '', ['latestDetection', 'anomaliaRelativa', 'corroboracionMirova', 'isValidDetection', 'isSummitDetection', 'mirovaEqVrpDisplay', 'isThermalArtifact', 'VOLCANOES_ALL', 'enrichWithMirovaConfirmation', 'parseUtcMs']);
console.log('ahora', AHORA);
const corteMs = Date.parse(AHORA) - 100 * 86400000; // _recent.json = 100 d
for (const v of X.VOLCANOES_ALL.filter(v => v.hasMirova)) {
  const recs = JSON.parse(fs.readFileSync(path.join(REPO, 'data/mirova_equivalent', v.name + '.json'), 'utf8')).records.filter(r => X.parseUtcMs(r.datetime_utc) >= corteMs);
  const mir = JSON.parse(fs.readFileSync(path.join(REPO, 'data/mirova', v.name + '.json'), 'utf8')).records;
  X.enrichWithMirovaConfirmation(recs, mir);
  const ik = v.inner_radius_km ?? 10;
  const det = X.latestDetection(recs, false, ik);
  const a = X.anomaliaRelativa(recs, det, ik);
  const soloK = recs.filter(r => r.datetime_utc >= '2026-09-18');
  const aK = X.anomaliaRelativa(soloK, det, ik);
  const cm = X.corroboracionMirova({ records: recs, mirovaRecords: mir }, 90);
  const corte90 = Date.parse(AHORA) - 90 * 86400000;
  const en90 = recs.filter(r => X.parseUtcMs(r.datetime_utc) >= corte90 && X.isValidDetection(r));
  const summitPub = en90.filter(r => X.isSummitDetection(r) && !X.isThermalArtifact(r, ik) && X.mirovaEqVrpDisplay(r, ik, false) > 0);
  const f = o => o ? `p${o.pct} ${o.veces != null ? o.veces.toFixed(1) + 'x' : ''} n${o.n} med${o.mediana.toFixed(3)}` : 'null';
  console.log(v.name.padEnd(20), 'det', det ? det.datetime_utc + ' ' + det.vrp.toFixed(2) : 'null', '| anom literal', f(a), '| anom soloK', f(aK),
    '| corr literal', cm ? `MIROVA ${cm.alertas} nuestras ${cm.nuestras}` : 'null', '| de esas: lejanas', en90.filter(r => !X.isSummitDetection(r)).length, 'C0', en90.filter(r => r.datetime_utc < '2026-09-18').length, '| publicadas cumbre', summitPub.length, '(K', summitPub.filter(r => r.datetime_utc >= '2026-09-18').length + ')');
}
