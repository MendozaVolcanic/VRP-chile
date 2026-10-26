// RA1: ejecuta el predicado REAL del tablero (frontend/index.html: mirovaEqVrp e isValidDetection) con node
// sobre records_v750.json (regla A97: el predicado del operador, no uno reconstruido a mano).
// Las dos funciones se extraen del texto de index.html por su cabecera y se evaluan tal cual.
const fs = require("fs");
const path = require("path");
const src = fs.readFileSync("frontend/index.html", "utf8");

function extraer(nombre) {
  const i = src.indexOf("function " + nombre + "(");
  if (i < 0) throw new Error("no encontre " + nombre);
  // cuenta llaves desde la primera { de la cabecera
  let j = src.indexOf("{", i), depth = 0;
  for (let k = j; k < src.length; k++) {
    if (src[k] === "{") depth++;
    else if (src[k] === "}") { depth--; if (depth === 0) return src.slice(i, k + 1); }
  }
  throw new Error("sin cierre " + nombre);
}
const fEq = extraer("mirovaEqVrp");
const fValid = extraer("isValidDetection");
const linea = (n) => src.slice(0, src.indexOf("function " + n + "(")).split("\n").length;
console.log("mirovaEqVrp en frontend/index.html:" + linea("mirovaEqVrp") + " ; isValidDetection en :" + linea("isValidDetection"));
const mirovaEqVrp = new Function(fEq + "; return mirovaEqVrp;")();
const isValidDetection = new Function(fValid + "; return isValidDetection;")();

const recs = JSON.parse(fs.readFileSync(path.join(__dirname, "records_v750.json"), "utf8"));
let out = [];
for (const r of recs) {
  const inner = r.inner_radius_km == null ? 10 : r.inner_radius_km;
  out.push({ eq_vrp: mirovaEqVrp(r, inner, false), eq_vrp_far: mirovaEqVrp(r, inner, true), valid: isValidDetection(r) });
}
fs.writeFileSync(path.join(__dirname, "predicado_tablero_salida.json"), JSON.stringify(out));
// control positivo del instrumento: un record sintetico con cumulo de 0,5 MW dentro del inner debe ser visible y uno con 0 no
const ctrl1 = { distance_class: "summit", primary_cluster: { vrp_mw: 0.5, centroid_dist_km: 1 } };
const ctrl0 = { distance_class: "summit", primary_cluster: { vrp_mw: 0, centroid_dist_km: 1 } };
console.log("control positivo: eq=" + mirovaEqVrp(ctrl1, 5) + " valid=" + isValidDetection(ctrl1) + " | control cero: eq=" + mirovaEqVrp(ctrl0, 5) + " valid=" + isValidDetection(ctrl0));
let nValid = out.filter(o => o.valid).length, nEq = out.filter(o => o.eq_vrp > 0).length;
console.log("records V750 con cumulo: " + out.length + " ; isValidDetection=true: " + nValid + " ; mirovaEqVrp>0: " + nEq);
