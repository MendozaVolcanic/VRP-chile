// S150 frente B. Evalua, con el codigo LITERAL de las tres vistas del tablero, que muestra
// cada una para cada record. No reimplementa nada: extrae las funciones de cada HTML y las
// ejecuta en un contexto vm aparte (cada vista tiene sus propias copias).
//   node vistas.js <frontend_dir> <casos.json> <mirova_ndc.json>
// casos.json: lista de records crudos del JSON del pipeline.
const fs = require('fs'), vm = require('vm'), path = require('path');
const [dir, casosP, mirP] = process.argv.slice(2);
const casos = JSON.parse(fs.readFileSync(casosP, 'utf8'));
const mir = JSON.parse(fs.readFileSync(mirP, 'utf8')).records;

function extraer(src, nombre, tipo) {
  const re = tipo === 'fn' ? 'function ' + nombre + '(' : null;
  const i = src.indexOf(re);
  if (i < 0) throw new Error('no encontre ' + nombre);
  let j = src.indexOf('{', i), d = 0;
  for (let k = j; k < src.length; k++) {
    if (src[k] === '{') d++;
    else if (src[k] === '}') { d--; if (d === 0) return src.slice(i, k + 1); }
  }
  throw new Error('no cerro ' + nombre);
}
function constante(src, nombre) {
  const m = src.match(new RegExp('(const|let) ' + nombre + '\\s*=\\s*([^;]+);'));
  if (!m) throw new Error('no encontre const ' + nombre);
  return m[0];
}
function contexto(archivo, consts, fns, extra) {
  const src = fs.readFileSync(path.join(dir, archivo), 'utf8');
  const code = [extra || ''].concat(consts.map(c => constante(src, c)))
    .concat(fns.map(f => extraer(src, f, 'fn'))).join('\n');
  const ctx = { console };
  vm.createContext(ctx);
  vm.runInContext(code + '\n;globalThis.__ok=1;', ctx);
  return ctx;
}
const FN_COMUNES = ['_havKm', 'mirovaEqVrp', 'f5CoreMagnitude', 'mirovaEqVrpCore', 'isCirrusArtifact',
  'isDiffuseFieldArtifact', 'isThermalArtifact', 'isValidDetection', 'esValorCensurado', 'parseUtcMs'];
// index.html
const IX = contexto('index.html', ['F5_R_CORE_KM', 'F5_BT_EXT_K', 'PATH_D_CAP_MW', 'LEVELS'],
  FN_COMUNES.concat(['mirovaEqVrpDisplay', 'isSummitDetection', 'getLevel', 'sensorGroup',
    'ourSensorBucket', 'mirovaSensorBucket', 'enrichWithMirovaConfirmation']),
  'var USE_F5_CORE = true; var includeFarDistance = false;');
// diario.html (sin isSummitDetection: no existe en esa vista)
const DI = contexto('diario.html', ['F5_R_CORE_KM', 'F5_BT_EXT_K', 'PATH_D_CAP_MW', 'INNER_RADIUS_KM'],
  FN_COMUNES.concat(['eqVrpDisplay']),
  'var USE_F5_CORE = true; var includeFarDistance = false;');
// mosaico.html
const MO = contexto('mosaico.html', ['F5_R_CORE_KM', 'F5_BT_EXT_K', 'PATH_D_CAP_MW', 'LEVELS'],
  FN_COMUNES.concat(['eqVrpDisplay', 'isSummitDetection', 'getLevel']),
  'var USE_F5_CORE = true;');

const INNER = 5;  // NevadosDeChillan inner_radius_km en index.html y mosaico.html
// enrich de index (cinturon _mirova_confirmed) con la referencia que el tablero carga
vm.runInContext('enrichWithMirovaConfirmation', IX)(casos, mir);

const out = casos.map(r => {
  const ix = IX, inner = INNER;
  const summit = ix.isSummitDetection(r), valid = ix.isValidDetection(r);
  const art = ix.isThermalArtifact(r, inner);
  const disp = ix.mirovaEqVrpDisplay(r, inner, false);
  const chart = art ? 0 : disp;                      // eqVrp de renderDetail (grafico, tabla, stats)
  const dispFar = ix.mirovaEqVrpDisplay(r, inner, true);
  const card = summit && valid && !art && disp > 0;  // latestDetection sin la ventana de 48 h
  const di = DI.eqVrpDisplay(r, 'NevadosDeChillan');
  const mo_spark = MO.eqVrpDisplay(r, inner);
  const mo_card = MO.isSummitDetection(r) && MO.isValidDetection(r) && mo_spark > 0;
  return {
    dt: r.datetime_utc, sensor: r.sensor, summit, valid, art,
    ix_chart: chart, ix_card: card, ix_far: dispFar, ix_conf: !!r._mirova_confirmed,
    ix_cens: ix.esValorCensurado(chart), ix_level: ix.getLevel(chart).label,
    di_chart: di, mo_spark, mo_card,
  };
});
process.stdout.write(JSON.stringify(out));
