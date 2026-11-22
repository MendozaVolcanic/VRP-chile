// crater_no_medido.js (S194, hallazgos C1-102 y C1-V202 de la auditoría Codex, ronda 2). Marca de sólo display
// «cráter no medido».
//
// POR QUÉ. A veces el infrarrojo medio (MIR, cerca de 4 µm, la banda que ve el calor) llega sin dato en uno o más
// píxeles sobre el cráter: una línea de barrido perdida o un píxel con calibración fallida en VIIRS (Missing_EV,
// Cal_Fail), o las dos bandas MIR saturadas en MODIS. La vía «código MIROVA» rellena la grilla con los vecinos antes de
// buscar anomalías, y los vecinos son más fríos: si el foco caía en el hueco, la pasada sale «sin anomalía» (foco
// aislado) o con una potencia que es sólo una parte de la real (foco con vecinos tibios: 11,5 MW en vez de 464 en el
// gránulo sintético del verificador, D:\codex-vrp\_salida\ronda2\cierre1_verificacion\instrumentos\b_psf_publica_salida.txt).
// Para el operador, «no se pudo medir el cráter» y «el cráter está frío» son cosas distintas. La vía ya lo anota en el
// record (diag_codigo_mirova, #1060 y #1077, ficha v1.47 y v1.61); hasta aquí el tablero no lo leía.
//
// CRITERIO (el mismo que experiments/_s194_mir_perdido/medir_mir_perdido.py, que exige igualdad record por record):
//   - px_mir_hueco_crater > 0: píxeles a menos de dos celdas de la grilla del cráter con la MIR no finita por una causa
//     que NO es el relleno bow-tie. Es el campo que el pipeline deja para esto («son lo que debe leer el paso B, no el
//     total», mirova_v750_codigo.py, dato_faltante_crater).
//   - crater_sin_posicion: el barrido que cruza el cráter llegó sin latitud ni longitud (la regla «cráter sin dato» de
//     la guardia K).
//   - px_saturados_crater > 0 (sólo VIIRS, que trae el bit): la MIR llegó con valor, pero en el tope de la banda; la
//     potencia de esos píxeles es un mínimo (Codex F1V-101 y F4-104, «subestimación sin marca, no cero»). No es «no
//     medido», así que lleva otro texto.
// NO se marca:
//   - el relleno bow-tie de VIIRS (px_bowtie_crater): el borde de cada barrido repite el suelo que ya midió el barrido
//     vecino y VIIRS lo descarta a bordo; no se pierde información (ficha v1.61: los 105 píxeles del 2026-11-20 eran
//     todos relleno). Medido aquí: en los records con las marcas separadas, todo px_mir_invalido_crater > 0 es bow-tie.
//   - px_mir_invalido_crater solo (records procesados entre el 2026-11-20 y el 2026-11-22, antes de #1077): mezcla
//     bow-tie y hueco y no se pueden separar; marcarlos pondría «cráter no medido» en pasadas que casi seguro sí lo
//     midieron.
//   - px_tir_hueco_crater: perder sólo la TIR tiene otro efecto (S191, tir_perdida) y no hay texto verificado para él.
// Los records anteriores a #1060 (2026-11-19) no traen ninguna de estas claves: no se marcan, y eso no dice que el
// cráter se haya medido (SIN DATO). Esta marca no cambia la potencia publicada, ni el nivel, ni la clase, ni la
// frescura: sólo avisa.
//
// UN SOLO LUGAR para las tres vistas (A102), como cumbre.js. Prueba: tests/test_tablero_crater_no_medido_s194.py
(function (raiz) {
  "use strict";

  const COLOR = "#ffab40";
  const SIMBOLO = "⊘";

  function entero(x) { return (typeof x === "number" && Number.isFinite(x) && x > 0) ? Math.round(x) : 0; }
  function plural(n, s, p) { return n + " " + (n === 1 ? s : p); }

  // {nMir, nSat, sinPosicion} si el record trae alguna marca de cráter sin medir entero; null si no.
  function craterNoMedido(r) {
    const d = r && r.diag_codigo_mirova;
    if (!d || typeof d !== "object") return null;
    const nMir = entero(d.px_mir_hueco_crater);
    const nSat = entero(d.px_saturados_crater);
    const sinPosicion = d.crater_sin_posicion === true;
    return (nMir || nSat || sinPosicion) ? { nMir, nSat, sinPosicion } : null;
  }

  // Texto corto: «cráter no medido: MIR sin dato en 2 píxeles».
  function textoCrater(m) {
    if (!m) return "";
    const partes = [];
    if (m.nMir) partes.push("MIR sin dato en " + plural(m.nMir, "píxel", "píxeles"));
    if (m.sinPosicion) partes.push("barrido sin posición sobre el cráter");
    const t = partes.length ? "cráter no medido: " + partes.join(", ") : "";
    const s = m.nSat ? "MIR saturada en " + plural(m.nSat, "píxel", "píxeles") + " del cráter: la potencia puede ser mayor" : "";
    return [t, s].filter(Boolean).join("; ");
  }

  // Explicación para el operador (title).
  function tituloCrater(m) {
    if (!m) return "";
    const t = [];
    if (m.nMir) t.push((m.nMir === 1 ? "1 píxel sobre el cráter llegó" : m.nMir + " píxeles sobre el cráter llegaron") +
      " sin dato en el infrarrojo medio (MIR, cerca de 4 µm, la banda que ve el calor): en VIIRS, una línea de barrido " +
      "perdida o un píxel con calibración fallida; en MODIS, las dos bandas MIR saturadas. Antes de buscar anomalías la " +
      "grilla se rellena con los vecinos, que son más fríos: si el foco estaba en ese hueco, la pasada sale «sin " +
      "anomalía» o con una potencia que es sólo una parte de la real. No se pudo medir el cráter, que no es lo mismo que " +
      "un cráter frío.");
    if (m.sinPosicion) t.push("El barrido que cruza el cráter llegó sin latitud ni longitud (el píxel con posición más " +
      "cercano quedó en el borde del gránulo o junto a píxeles sin posición): la pasada no vio el cráter entero.");
    if (m.nSat) t.push("El sensor marcó " + (m.nSat === 1 ? "1 píxel" : m.nSat + " píxeles") + " del cráter como " +
      "saturados en el MIR: el calor superó el tope de la banda y el valor quedó recortado, así que la potencia de " +
      (m.nSat === 1 ? "ese píxel" : "esos píxeles") + " es un mínimo.");
    t.push("No se marca el relleno bow-tie del borde del barrido de VIIRS, que no pierde dato (ese suelo lo midió el " +
      "barrido vecino). Esta marca no cambia la potencia publicada, ni el nivel, ni la clase: sólo avisa.");
    return t.join(" ");
  }

  // La pasada más reciente desde `desdeMs` con la marca que pase el filtro de la vista. {rec, m, t} o null. Una escena
  // que la vía no midió (motivo_vacio) no es pasada (S183) y ya se rotula aparte: no entra. La usan las tarjetas de index
  // y mosaico.
  function ultimaPasadaNoMedida(records, desdeMs, filtro, parseMs) {
    let best = null;
    for (const r of records || []) {
      const t = parseMs(r.datetime_utc);
      if (!(t >= desdeMs)) continue;
      if (r.diag_codigo_mirova && r.diag_codigo_mirova.motivo_vacio) continue;
      if (filtro && !filtro(r)) continue;
      const m = craterNoMedido(r);
      if (!m) continue;
      if (!best || t > best.t) best = { rec: r, m, t };
    }
    return best;
  }

  const api = { COLOR, SIMBOLO, craterNoMedido, textoCrater, tituloCrater, ultimaPasadaNoMedida };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else raiz.CraterNoMedido = api;
})(typeof window !== "undefined" ? window : this);
