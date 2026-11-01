// F2-03: grafico "Distancia" de index.html. Extraigo el texto LITERAL de buildDistanceData (anidada en renderDetail)
// y la evaluo con `filtered`, `innerKm`, `includeFarDistance` del volcan.
// P1: si la distancia cambiara de definicion en la frontera, ¿lo veria? Si: fraccion en 0,0 y fuente por tramo.
// P2: instrumento muerto -> 0 puntos en ambos tramos; control: n puntos > 0 en cada tramo.
const { evaluar, REPO } = require('./harness');
const fs = require('fs'), path = require('path'), vm = require('vm');
const html = fs.readFileSync(path.join(REPO, 'frontend/index.html'), 'utf8');
const i0 = html.indexOf('function buildDistanceData()');
let i = html.indexOf('{', i0), d = 0, j = i; for (; j < html.length; j++) { if (html[j] === '{') d++; else if (html[j] === '}') { d--; if (d === 0) break; } }
const fuente = html.slice(i0, j + 1);
const X = evaluar('index.html', '2026-10-19T12:00:00Z', '', ['isValidDetection', 'isSensorVisible', 'VOLCANOES_ALL']);
const build = new Function('filtered', 'innerKm', 'includeFarDistance', 'isValidDetection', 'isSensorVisible', fuente + '; return buildDistanceData();');
for (const v of X.VOLCANOES_ALL.filter(v => v.hasMirova)) {
  const recs = JSON.parse(fs.readFileSync(path.join(REPO, 'data/mirova_equivalent', v.name + '.json'), 'utf8')).records.filter(r => r.datetime_utc >= '2026-07-21');
  const src = {}; for (const r of recs) if (X.isValidDetection(r)) { const k = (r.datetime_utc < '2026-09-18' ? 'C0:' : 'K:') + r.final_hotspot_source; src[k] = (src[k] || 0) + 1; }
  const pts = build(recs, v.inner_radius_km ?? 10, false, X.isValidDetection, X.isSensorVisible);
  const tramo = t => pts.filter(p => (p.x < '2026-09-18') === (t === 'C0'));
  const med = a => { const s = a.map(p => p.y).sort((x, y) => x - y); return s.length ? s[s.length >> 1].toFixed(2) : '-'; };
  const fr = a => a.length ? (100 * a.filter(p => p.y === 0).length / a.length).toFixed(0) + '%' : '-';
  console.log(v.name.padEnd(20), 'C0 n', tramo('C0').length, 'en0', fr(tramo('C0')), 'med', med(tramo('C0')), '| K n', tramo('K').length, 'en0', fr(tramo('K')), 'med', med(tramo('K')), '|', JSON.stringify(src));
}
console.log('ventana: 2026-07-21 a 2026-10-19 (90 d), C0 = observacion < 2026-09-18');
