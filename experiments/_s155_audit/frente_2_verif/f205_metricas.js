// F2-05: panel de metricas (computeMetrics literal de index.html) en la ventana por defecto (30 d, Periodo.filtrar literal).
// Variantes alimentando la MISMA funcion: (b) sin alertas diurnas de MIROVA, (c) sin diurnas y sin minimas VIIRS375 <=0,05 MW (SN, aproximada por fila).
// P1: si el panel contara mal las diurnas, ¿lo veria? Si: diferencia de FN entre (a) y (b). P2: recall null = sin alertas, se informa null.
const { evaluar, REPO } = require('./harness');
const fs = require('fs'), path = require('path');
const AHORA = process.argv[2] || '2026-10-19T12:00:00Z';
const X = evaluar('index.html', AHORA, '', ['computeMetrics', 'VOLCANOES_ALL', 'Periodo', 'currentPeriodo', 'DIAS_POR_DEFECTO']);
console.log('ahora', AHORA, 'periodo por defecto', JSON.stringify(X.currentPeriodo), 'DIAS_POR_DEFECTO', X.DIAS_POR_DEFECTO);
const fmt = o => o.recall == null ? 'null' : `${o.recall.toFixed(2)} (tp${o.tp} fn${o.fn})`;
for (const v of X.VOLCANOES_ALL.filter(v => v.hasMirova)) {
  const recs = X.Periodo.filtrar(JSON.parse(fs.readFileSync(path.join(REPO, 'data/mirova_equivalent', v.name + '.json'), 'utf8')).records, X.currentPeriodo);
  const mirAll = JSON.parse(fs.readFileSync(path.join(REPO, 'data/mirova', v.name + '.json'), 'utf8')).records;
  const mir = X.Periodo.filtrar(mirAll, X.currentPeriodo);
  const ik = v.inner_radius_km ?? 10;
  const a = X.computeMetrics(recs, mir, ik, false).byBucket;
  const b = X.computeMetrics(recs, mir.filter(m => m.dia !== true), ik, false).byBucket;
  const c = X.computeMetrics(recs, mir.filter(m => m.dia !== true && !(m.sensor === 'VIIRS375' && +m.VRP_MW <= 0.05)), ik, false).byBucket;
  const nd = mir.filter(m => m.dia === true).length, nsn = mir.filter(m => m.dia !== true && m.sensor === 'VIIRS375' && +m.VRP_MW <= 0.05).length;
  console.log(v.name.padEnd(20), 'filas', mir.length, 'diurnas', nd, 'minimasV375', nsn, '| V375', fmt(a.VIIRS375), '->', fmt(b.VIIRS375), '->', fmt(c.VIIRS375), '| V750', fmt(a.VIIRS750), '->', fmt(b.VIIRS750), '| MODIS', fmt(a.MODIS), '->', fmt(b.MODIS));
}
