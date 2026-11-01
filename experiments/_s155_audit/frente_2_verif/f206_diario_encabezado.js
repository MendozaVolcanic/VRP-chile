// F2-06: encabezado de tarjeta de diario.html (computeStats literal), 90 d por defecto; variante: mismos records pero solo K.
// P1/P2: si la mezcla no existiera, literal y soloK coincidirian; median 0 = sin detecciones, se informa como '-'.
const { evaluar, REPO } = require('./harness');
const fs = require('fs'), path = require('path');
const AHORA = process.argv[2] || '2026-10-19T12:00:00Z';
const X = evaluar('diario.html', AHORA, '', ['computeStats', 'TIER_A']);
for (const v of X.TIER_A) {
  const d = JSON.parse(fs.readFileSync(path.join(REPO, 'data/mirova_equivalent', v.name + '.json'), 'utf8'));
  const a = X.computeStats(d, [], v.name);
  const k = X.computeStats({ records: d.records.filter(r => r.datetime_utc >= '2026-09-18') }, [], v.name);
  console.log(v.name.padEnd(20), 'literal: det', a.n_det_us, 'max', a.max_us.toFixed(2), 'mediana', a.median_us.toFixed(3), '| soloK: det', k.n_det_us, 'max', k.max_us.toFixed(2), 'mediana', k.median_us.toFixed(3));
}
