// Extrae funciones y constantes top-level de una vista HTML del frontend para ejecutarlas en node
// (regla A97: el predicado literal del operador, no uno reconstruido a mano).
// Convención del código: `function NOMBRE(` empieza en columna 0 y termina en la primera línea "}" en columna 0.
"use strict";
const fs = require("fs");
const vm = require("vm");

function extraerFuncion(src, nombre) {
  const lines = src.split(/\r?\n/);
  const i = lines.findIndex(l => l.startsWith("function " + nombre + "(") || l.startsWith("async function " + nombre + "("));
  if (i < 0) throw new Error("no encontrada: " + nombre);
  // función de una sola línea
  if (/\}\s*$/.test(lines[i]) && (lines[i].match(/\{/g) || []).length === (lines[i].match(/\}/g) || []).length) return lines[i];
  let j = i + 1;
  while (j < lines.length && lines[j] !== "}") j++;
  if (j >= lines.length) throw new Error("sin cierre: " + nombre);
  return lines.slice(i, j + 1).join("\n");
}
function extraerConst(src, nombre) {
  const lines = src.split(/\r?\n/);
  const i = lines.findIndex(l => l.startsWith("const " + nombre + " = "));
  if (i < 0) throw new Error("const no encontrada: " + nombre);
  if (/;\s*(\/\/.*)?$/.test(lines[i])) return lines[i];
  let j = i + 1;
  while (j < lines.length && !/^\];|^\};|^\]\s*;|^};$/.test(lines[j])) j++;
  return lines.slice(i, j + 1).join("\n");
}
function cargarVista(ruta, funciones, consts, preludio, nowMs) {
  const src = fs.readFileSync(ruta, "utf8");
  let code = preludio + "\n";
  for (const c of consts) code += extraerConst(src, c) + "\n";
  for (const f of funciones) code += extraerFuncion(src, f) + "\n";
  // exportar
  code += "\nthis.__exp = {" + funciones.concat(consts).join(",") + "};";
  const RealDate = Date;
  class FakeDate extends RealDate {
    constructor(...a) { if (a.length === 0) super(nowMs); else super(...a); }
    static now() { return nowMs; }
  }
  const ctx = { Date: FakeDate, Math, console, String, Number, Array, Set, Map, JSON, parseFloat, isNaN, isFinite, Infinity, Object };
  vm.createContext(ctx);
  vm.runInContext(code, ctx, { filename: ruta });
  ctx.__exp.__ctx = ctx;
  return ctx.__exp;
}
module.exports = { extraerFuncion, extraerConst, cargarVista };
