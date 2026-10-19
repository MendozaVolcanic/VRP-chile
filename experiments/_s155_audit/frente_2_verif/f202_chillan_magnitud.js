// F2-02: Chillan, magnitud mostrada (codigo literal de index.html) contra MIROVA, por pasada.
// P1: si la magnitud mostrada estuviera rota (p.ej. 0 o x10), ¿lo veria? Si: razon por par y nivel por par.
// P2: instrumento muerto -> 0 pares; distingo "sin par" (FN) de "par con 0". Control positivo: computeMetrics literal
//     sobre el mismo universo debe dar el mismo numero de TP que mi emparejamiento.
const { evaluar, REPO } = require('./harness');
const fs = require('fs'), path = require('path');
const X = evaluar('index.html', '2026-10-19T12:00:00Z', '', ['mirovaEqVrpDisplay', 'mirovaEqVrp', 'isThermalArtifact', 'isValidDetection', 'getLevel', 'VOLCANOES_ALL', 'parseUtcMs', 'ourSensorBucket', 'mirovaSensorBucket', 'computeMetrics', 'f5CoreMagnitude']);
const VOL = process.argv[2] || 'NevadosDeChillan';
const DESDE = process.argv[3] || '2026-09-18';
const HASTA = process.argv[4] || '9999';
const v = X.VOLCANOES_ALL.find(x => x.name === VOL);
const innerKm = v.inner_radius_km ?? 10;
const ours = JSON.parse(fs.readFileSync(path.join(REPO, 'data/mirova_equivalent', VOL + '.json'), 'utf8')).records.filter(r => r.datetime_utc >= DESDE && r.datetime_utc < HASTA);
const mir = JSON.parse(fs.readFileSync(path.join(REPO, 'data/mirova', VOL + '.json'), 'utf8')).records.filter(r => r.datetime_utc >= DESDE && r.datetime_utc < HASTA);
const eqVrp = r => X.isThermalArtifact(r, innerKm) ? 0 : X.mirovaEqVrpDisplay(r, innerKm, false);
const eqClu = r => X.isThermalArtifact(r, innerKm) ? 0 : X.mirovaEqVrp(r, innerKm, false);
const byB = {}; for (const r of ours) { const b = X.ourSensorBucket(r.sensor); if (!b) continue; (byB[b] = byB[b] || []).push({ t: X.parseUtcMs(r.datetime_utc), r }); }
const TOL = 3600000;
function nearest(list, t) { let best = null, bd = TOL + 1; for (const o of list || []) { const d = Math.abs(o.t - t); if (d <= TOL && d < bd) { bd = d; best = o; } } return best; }
const ORD = ['Sin datos', 'Muy Bajo', 'Bajo', 'Moderado', 'Alto', 'Muy Alto'];
function resumen(etq, filtro) {
  const out = {}; let pares = [];
  for (const m of mir.filter(filtro)) {
    const cls = String(m.clasificacion || '').toUpperCase(); if (cls === 'NULO' || cls === 'RUTINA') continue;
    const vrp = +m.VRP_MW; if (!(vrp > 0)) continue;
    const b = X.mirovaSensorBucket(m.sensor); if (!b) continue;
    const o = nearest(byB[b], X.parseUtcMs(m.datetime_utc));
    const s = (out[b] = out[b] || { alertas: 0, tp: 0, fn: 0, ratios: [], ratiosClu: [], bajaNivelDesdeMod: 0, modTot: 0, nivelMenor: 0, nivelMayor: 0 });
    s.alertas++;
    const val = o ? eqVrp(o.r) : 0;
    if (!(o && val > 0)) { s.fn++; continue; }
    s.tp++; s.ratios.push(val / vrp); s.ratiosClu.push(eqClu(o.r) / vrp);
    const ln = ORD.indexOf(X.getLevel(val).label), lm = ORD.indexOf(X.getLevel(vrp).label);
    if (lm === 3) { s.modTot++; if (ln < 3) s.bajaNivelDesdeMod++; }
    if (ln < lm) s.nivelMenor++; if (ln > lm) s.nivelMayor++;
    pares.push([m.datetime_utc, b, m.source, m.dia ? 'dia' : 'noche', vrp, +val.toFixed(3), X.getLevel(val).label, m.clasificacion, o.r.datetime_utc, (o.r.regimen ? 'K' : 'sinmarca')]);
  }
  const med = a => { if (!a.length) return null; const s = a.slice().sort((x, y) => x - y), k = s.length >> 1; return +(s.length % 2 ? s[k] : (s[k - 1] + s[k]) / 2).toFixed(3); };
  console.log('==', etq);
  let tot = { tp: 0, mod: 0, baja: 0 };
  for (const [b, s] of Object.entries(out)) { console.log(b, 'alertas', s.alertas, 'tp', s.tp, 'fn', s.fn, 'razon_med_mostrada', med(s.ratios), 'razon_med_cumulo', med(s.ratiosClu), 'MIROVA_Moderado', s.modTot, 'nuestro_<Moderado', s.bajaNivelDesdeMod, 'nivel_menor', s.nivelMenor, 'nivel_mayor', s.nivelMayor); tot.tp += s.tp; tot.mod += s.modTot; tot.baja += s.bajaNivelDesdeMod; }
  console.log('total pares', tot.tp, 'MIROVA Moderado', tot.mod, 'nuestro bajo Moderado', tot.baja);
  return pares;
}
console.log(VOL, 'desde', DESDE, 'innerKm', innerKm, 'records nuestros', ours.length, 'filas MIROVA', mir.length);
const p = resumen('todas las alertas (como computeMetrics: incluye diurnas)', () => true);
resumen('solo nocturnas', m => !m.dia);
resumen('solo nocturnas, solo consolidado', m => !m.dia && m.source === 'consolidado');
// duplicados MIROVA (misma hora y sensor)
const k = {}; for (const m of mir) { const kk = m.datetime_utc + '|' + m.sensor; k[kk] = (k[kk] || 0) + 1; }
console.log('filas MIROVA duplicadas (hora|sensor):', Object.entries(k).filter(([, n]) => n > 1).length);
// dias de MIROVA emparejados con records 'dia' nuestros? (la replica es nocturna)
// control positivo: computeMetrics literal
const cm = X.computeMetrics(ours, mir, innerKm, false);
console.log('computeMetrics literal:', JSON.stringify(Object.fromEntries(Object.entries(cm.byBucket).map(([b, o]) => [b, { tp: o.tp, fn: o.fn, fp: o.fp, ratio_med: o.ratio_med && +o.ratio_med.toFixed(3), recall: o.recall && +o.recall.toFixed(3) }]))));
fs.writeFileSync(path.join(__dirname, 'f202_pares_' + VOL + '.json'), JSON.stringify(p, null, 0));
