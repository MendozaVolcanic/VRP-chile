// cumbre.js (S194, salida intermedia de experiments/_s193_radiante_variante/INFORME.md que Nicolás aprobó el 2026-11-21:
// «continua con todo lo que puedas»). Marca de sólo display «también hay calor en la cumbre».
//
// POR QUÉ. En una misma pasada puede haber un píxel tibio sobre el cráter y, a varios km, un cúmulo más radiante (salar
// o roca tibia del altiplano, un incendio, un borde de nube). La regla de posición «radiante» (D8' de
// docs/MIROVA_DIVERGENCES.md, decisión de Nicolás del 2026-11-15) pone el record en el cúmulo más radiante: la pasada
// queda lejana y el operador no ve que también hubo calor en la cumbre. Así quedan fuera de vista 12 alertas protegidas
// que sólo el OCR de MIROVA ubica en la cumbre (Codex F12-V301). Mover la posición a la cumbre se midió y se rechazó
// (recupera esas 12, pero pone en la cumbre 114 pasadas que la tabla de MIROVA ubica lejos). Esta marca no mueve nada:
// ni la posición, ni distance_class, ni la potencia publicada (la suma de todos los alertados, D32), ni el nivel, ni la
// frescura. Sólo avisa que dentro del radio de la cumbre también hubo píxeles alertados.
//
// CRITERIO, el de experiments/_s194_marcador_cumbre/medir_marcador.py (que exige igualdad record por record con este
// módulo): record de la vía «código MIROVA» (sus anomaly_pixels traen TODOS los alertados, 10.361 de 10.361 records
// con alertados en main del 2026-11-21, con dist_km medido desde el mismo cráter que distance_class) que el tablero
// pone lejos (distance_class "far") y con al menos un alertado a dist_km <= inner_radius_km del volcán. Los records de
// otra vía (K, legado) no se marcan: su lista de píxeles puede estar recortada (A46) y su distancia tener otro origen.
// Medido en las noches del 2026-03-01 al 2026-11-18 (11 Tier A): 218 de 707 pasadas lejanas, las 12 de Codex entre ellas.
//
// UN SOLO LUGAR para las tres vistas (A102), como agua.js. Prueba: tests/test_tablero_cumbre_s194.py
(function (raiz) {
  "use strict";

  const COLOR = "#ff8a65";

  function fmtKm(x) { return x.toFixed(x < 10 ? 1 : 0).replace(".", ","); }

  // {n, dMinKm, btMaxK} si la pasada lejana de la vía tiene alertados dentro del radio de la cumbre; null si no.
  function calorEnCumbre(r, innerKm) {
    if (!r || r.via_codigo_mirova !== true || r.distance_class !== "far") return null;
    if (!Number.isFinite(innerKm)) return null;
    let n = 0, dMin = Infinity, btMax = null;
    for (const p of r.anomaly_pixels || []) {
      const d = p && p.dist_km;
      if (d == null || !Number.isFinite(Number(d)) || Number(d) > innerKm) continue;
      n++;
      if (Number(d) < dMin) dMin = Number(d);
      if (Number.isFinite(p.bt_k) && (btMax == null || p.bt_k > btMax)) btMax = p.bt_k;
    }
    return n ? { n, dMinKm: dMin, btMaxK: btMax } : null;
  }

  // Texto corto: «también hay calor en la cumbre (1 píxel a 0,9 km)».
  function textoCumbre(m) {
    if (!m) return "";
    return "también hay calor en la cumbre (" + (m.n === 1
      ? "1 píxel a " + fmtKm(m.dMinKm) + " km)"
      : m.n + " píxeles, el más cercano a " + fmtKm(m.dMinKm) + " km)");
  }

  // Explicación para el operador (title).
  function tituloCumbre(m, r, innerKm) {
    if (!m) return "";
    const pc = (r && r.primary_cluster) || {};
    const lejos = r && r.final_hotspot_dist_km != null ? r.final_hotspot_dist_km : pc.centroid_dist_km;
    return "El cúmulo más radiante de esta pasada está " + (lejos != null ? "a " + fmtKm(Number(lejos)) + " km del cráter" : "lejos del cráter") +
      " y por eso el tablero la ubica lejos, pero " + (m.n === 1 ? "1 píxel alertado cae" : m.n + " píxeles alertados caen") +
      " dentro del radio de la cumbre (" + fmtKm(innerKm) + " km), el más cercano a " + fmtKm(m.dMinKm) + " km del cráter" +
      (m.btMaxK != null ? " (hasta " + (m.btMaxK - 273.15).toFixed(1).replace(".", ",") + " °C de temperatura de brillo)" : "") +
      ". Puede ser calor del cráter más débil que la fuente lejana. La potencia publicada es la suma de todos los " +
      "alertados, como en MIROVA, y esta marca no la cambia, ni la posición, ni el nivel: sólo avisa.";
  }

  // La pasada lejana con calor en la cumbre más reciente desde `desdeMs` que pase el filtro de la vista (válida,
  // sensor visible). {rec, m, t} o null. La usan las tarjetas de index y mosaico.
  function ultimaLejanaConCumbre(records, innerKm, desdeMs, filtro, parseMs) {
    let best = null;
    for (const r of records || []) {
      const t = parseMs(r.datetime_utc);
      if (!(t >= desdeMs)) continue;
      if (filtro && !filtro(r)) continue;
      const m = calorEnCumbre(r, innerKm);
      if (!m) continue;
      if (!best || t > best.t) best = { rec: r, m, t };
    }
    return best;
  }

  const api = { COLOR, calorEnCumbre, textoCumbre, tituloCumbre, ultimaLejanaConCumbre };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else raiz.CumbreTablero = api;
})(typeof window !== "undefined" ? window : this);
