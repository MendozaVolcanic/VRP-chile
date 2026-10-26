// F1 (S158): el predicado de publicación del tablero, ejecutado con node sobre los records de VIIRS 750 (A97).
// No reconstruye el predicado a mano: extrae el texto de frontend/index.html entre `function mirovaEqVrp(` y el
// comentario `// S18: clasifica` (mirovaEqVrp, f5CoreMagnitude, mirovaEqVrpCore, mirovaEqVrpDisplay, filtros de
// artefacto) y lo evalúa. Valor publicado = el que usa la tarjeta (index.html:2432):
//   isThermalArtifact(r, innerKm) ? 0 : mirovaEqVrpDisplay(r, innerKm, false)
// y se agrega isValidDetection (index.html:1595). `_mirova_confirmed` no se setea (el enriquecimiento cruza con el
// CSV en el navegador): con eso los filtros de artefacto actúan sobre todo record, que es la cota que oculta MÁS.
// Uso: node predicado_tablero.js <data_dir> <salida.json> Vol1:inner1 Vol2:inner2 ...
const fs = require("fs");
const path = require("path");
const html = fs.readFileSync(path.join(__dirname, "..", "..", "..", "frontend", "index.html"), "utf8");
const a = html.indexOf("function mirovaEqVrp(");
const b = html.indexOf("// S18: clasifica", a);
const c = html.indexOf("function isValidDetection(");
const d = html.indexOf("function isSummitDetection(", c);
if (a < 0 || b < 0 || c < 0 || d < 0) { console.error("no encontré los marcadores en index.html"); process.exit(2); }
const persistedFlag = (k, def) => def;
const src = html.slice(a, b) + "\n" + html.slice(c, d) +
  "\nmodule.exports = {mirovaEqVrp, mirovaEqVrpDisplay, isThermalArtifact, isValidDetection};";
const m = { exports: {} };
new Function("module", "persistedFlag", src)(m, persistedFlag);
const F = m.exports;
const [dataDir, out, ...vols] = process.argv.slice(2);
const res = [];
for (const vi of vols) {
  const [name, innerS] = vi.split(":");
  const inner = parseFloat(innerS);
  const j = JSON.parse(fs.readFileSync(path.join(dataDir, name + ".json"), "utf8"));
  for (const r of j.records) {
    if (!String(r.sensor || "").endsWith("_750")) continue;
    const pub = F.isThermalArtifact(r, inner) ? 0 : F.mirovaEqVrpDisplay(r, inner, false);
    res.push({ v: name, t: r.datetime_utc, s: r.sensor, pub, eq: F.mirovaEqVrp(r, inner, false),
               valid: F.isValidDetection(r), art: F.isThermalArtifact(r, inner) });
  }
}
fs.writeFileSync(out, JSON.stringify(res));
console.log("records V750 evaluados:", res.length, " publicados (pub>0):", res.filter(x => x.pub > 0).length);
