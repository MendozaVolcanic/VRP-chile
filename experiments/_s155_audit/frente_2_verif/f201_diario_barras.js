// F2-01: dias con barra VIIRS 375 (y demas sensores) en diario.html, antes y despues de 2026-09-18 y del 2026-10-18.
// P1: si el escalon no existiera, ¿lo veria? Si: cuento dias con barra por tramo; con regimen plano los tramos serian parejos.
// P2: instrumento muerto -> datasets vacios en TODOS los volcanes; control positivo: total de dias con barra > 0 y
//     Chillan (en erupcion) debe tener barras despues del 18-sep.
const { evaluar, REPO } = require('./harness');
const fs = require('fs'), path = require('path');
const AHORA = process.argv[2] || '2026-10-19T12:00:00Z';
const X = evaluar('diario.html', AHORA, '', ['buildDatasets', 'computeStats', 'TIER_A', 'eqVrpDisplay', 'sensorBucket', 'PERIODO']);
console.log('ahora', AHORA, 'periodo', JSON.stringify(X.PERIODO));
const cortes = ['2026-09-18', '2026-10-18'];
for (const v of X.TIER_A) {
  const d = JSON.parse(fs.readFileSync(path.join(REPO, 'data/mirova_equivalent', v.name + '.json'), 'utf8'));
  const { datasets, n_records } = X.buildDatasets(d, [], v.name);
  const fila = [v.name.padEnd(20), 'n_rec_det', n_records];
  for (const lab of ['MODIS (1 km)', 'VIIRS 750m', 'VIIRS 375m']) {
    const ds = datasets.find(x => x.label === lab);
    const dias = ds ? ds.data.map(p => p.x) : [];
    const a = dias.filter(x => x < cortes[0]).length, b = dias.filter(x => x >= cortes[0] && x < cortes[1]).length, c = dias.filter(x => x >= cortes[1]).length;
    fila.push(lab.split(' ')[0] + lab.split(' ')[1][0] + ':', `${a}|${b}|${c}`);
  }
  // dias calendario por tramo dentro de la ventana con al menos un record procesado (dias con dato)
  const t0 = Date.parse(AHORA) - 90 * 86400000;
  const conDato = new Set(d.records.filter(r => Date.parse(r.datetime_utc.replace(' ', 'T') + 'Z') >= t0).map(r => r.datetime_utc.slice(0, 10)));
  const cd = [...conDato];
  fila.push('dias_con_dato', `${cd.filter(x => x < cortes[0]).length}|${cd.filter(x => x >= cortes[0] && x < cortes[1]).length}|${cd.filter(x => x >= cortes[1]).length}`);
  console.log(fila.join(' '));
}
console.log('formato: antes del 18-sep | 18-sep a 17-oct | 18-oct en adelante');
