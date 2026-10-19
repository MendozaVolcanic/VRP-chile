// V2-01: alertas PROTEGIDAS de MIROVA (>= 1 MW, nocturnas) en la ventana K (2026-09-18 en adelante): ¿el tablero
// (index.html literal, mismo emparejamiento que computeMetrics: mismo sensor, +-60 min) publica algo en esa pasada?
// Si no publica, ¿habia un cumulo nuestro con energia que la vista oculta (lejano / fuera del inner)?
// P1: si el tablero perdiera protegidas, esto lo veria (cuento una a una). P2: n protegidas > 0 (control: Chillan).
const { evaluar, REPO } = require('./harness');
const fs = require('fs'), path = require('path');
const X = evaluar('index.html', '2026-10-19T12:00:00Z', '', ['mirovaEqVrpDisplay', 'isThermalArtifact', 'isValidDetection', 'VOLCANOES_ALL', 'parseUtcMs', 'ourSensorBucket', 'mirovaSensorBucket']);
let tot = 0, pub = 0; const perdidas = [];
for (const v of X.VOLCANOES_ALL.filter(v => v.hasMirova)) {
  const ik = v.inner_radius_km ?? 10;
  const recs = JSON.parse(fs.readFileSync(path.join(REPO, 'data/mirova_equivalent', v.name + '.json'), 'utf8')).records.filter(r => r.datetime_utc >= '2026-09-17');
  const mir = JSON.parse(fs.readFileSync(path.join(REPO, 'data/mirova', v.name + '.json'), 'utf8')).records.filter(m => m.datetime_utc >= '2026-09-18' && !m.dia && +m.VRP_MW >= 1);
  for (const m of mir) {
    tot++;
    const b = X.mirovaSensorBucket(m.sensor), t = X.parseUtcMs(m.datetime_utc);
    const cand = recs.filter(r => X.ourSensorBucket(r.sensor) === b && Math.abs(X.parseUtcMs(r.datetime_utc) - t) <= 3600000);
    const shown = cand.map(r => (!X.isValidDetection(r) || X.isThermalArtifact(r, ik)) ? 0 : X.mirovaEqVrpDisplay(r, ik, false));
    if (shown.some(x => x > 0)) { pub++; continue; }
    perdidas.push([v.name, m.datetime_utc, m.sensor, m.VRP_MW, m.source, m.clasificacion, m.distancia_km, cand.map(r => [r.sensor, r.distance_class, r.primary_cluster && r.primary_cluster.vrp_mw, r.primary_cluster && r.primary_cluster.centroid_dist_km, X.isThermalArtifact(r, ik) ? 'artefacto' : ''])]);
  }
}
console.log('protegidas nocturnas en ventana K:', tot, 'con publicacion del tablero:', pub, 'sin publicacion:', perdidas.length);
for (const p of perdidas) console.log(JSON.stringify(p));
