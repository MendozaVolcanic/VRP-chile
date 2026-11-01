// Harness propio del verificador: extrae las funciones del tablero de index.html y evalua records COMPLETOS.
const fs = require('fs');
const src = fs.readFileSync(process.argv[2], 'utf8');
function extraer(nombre) {
  const re = new RegExp('function\\s+' + nombre + '\\s*\\(');
  const m = re.exec(src);
  if (!m) throw new Error('falta ' + nombre);
  let j = src.indexOf('{', m.index), d = 0;
  for (let k = j; k < src.length; k++) {
    if (src[k] === '{') d++;
    else if (src[k] === '}') { d--; if (d === 0) return src.slice(m.index, k + 1); }
  }
  throw new Error('no cierra ' + nombre);
}
function constante(n) { const m = src.match(new RegExp('const ' + n + '\\s*=\\s*([^;]+);')); return m[0]; }
let USE_F5_CORE = true;
eval([constante('F5_R_CORE_KM'), constante('F5_BT_EXT_K')].concat(
  ['_havKm','mirovaEqVrp','f5CoreMagnitude','mirovaEqVrpCore','mirovaEqVrpDisplay',
   'isCirrusArtifact','isDiffuseFieldArtifact','isThermalArtifact','isValidDetection',
   'isSummitDetection'].map(extraer)).join('\n'));
const casos = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
console.log(JSON.stringify(casos.map(([r, inner]) => {
  const s = isSummitDetection(r), v = isValidDetection(r), a = isThermalArtifact(r, inner);
  const d = mirovaEqVrpDisplay(r, inner, false);
  return {summit: s, valid: v, art: a, disp: d, pub: (s && v && !a && d > 0)};
})));
