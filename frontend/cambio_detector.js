// cambio_detector.js (S153): marca visible de la fecha en que la réplica cambió de detector (adopción de K).
//
// POR QUÉ: con K (sin el Test 1 integrado en el ROI, conectiva `max` de Coppola 2016a en los Tests 2 y 3, banda 22
// primaria en MODIS) la publicación de VIIRS 375 en pasadas donde MIROVA miró y no vio nada cae de 85 a 88 % a 2,5 a
// 3,7 %, y la magnitud de VIIRS 375 baja en las pasadas que cambian (experiments/_s153_fk_v2/, regla de adopción
// experiments/_s151_prereg_fk_11/REGLA_ADOPCION.md §4.8). Sin una marca, ese escalón en la tendencia de 90 días se lee
// como un cambio del volcán: con Chillán en erupción, «la erupción declina». La marca no cambia ningún dato ni el
// criterio de publicación (isValidDetection, mirovaEqVrp y compañía siguen en cada vista, intactos).
//
// UN SOLO LUGAR: la fecha vive acá y no copiada en las tres vistas, para que el día del merge se complete una vez y
// ninguna vista quede atrás (A102: las copias en línea de una lógica se olvidan). Mientras sea null no se dibuja nada.
//
// S155 (auditoría post-K, frentes 2, 3 y 4): la línea iba en la hora del MERGE, pero los 30 días anteriores se
// reprocesaron con K, así que en las series el escalón está en la fecha de OBSERVACIÓN 2026-09-18. Con la marca un mes
// después, Copahue o Llaima «dejaban de tener anomalías» el 18-sep sin ninguna marca. Ahora hay dos fechas: la línea
// va donde cambian los datos y el aviso dice además desde cuándo corre K en producción. La frontera la vigila
// tests/test_cambio_detector_frontera_s155.py contra los JSON: cuando se aplique el histórico con K (tarea 1.24) se
// pondrá roja y habrá que mover DATOS_K_DESDE_UTC.
//
// S158 (tarea 1.24 aplicada): el histórico 2025-02-15..2026-09-17 se reemplazó por el reproceso con K en los 11
// Tier A, y las 90 pasadas que NASA no permite reprocesar (Suomi NPP del 3 al 6-ago-2026, MODIS Terra sin estándar)
// se apartaron a data/_c0_residuales/ por decisión de Nicolás del 2026-10-21. Desde el 2025-02-15, primer día de la
// serie, todo lo publicado es K; lo vigila además tests/test_guard_serie_k_pura_s158.py (100 %, no 95 %). La
// vigilancia de la sombra sigue cortando sus disparos en CAMBIO_DETECTOR_UTC, que no cambia.
(function (raiz) {
  "use strict";

  // Fecha y hora UTC del merge del PR de adopción de K, en ISO con Z (p. ej. "2026-10-19T14:05:00Z"). null = sin marca.
  const CAMBIO_DETECTOR_UTC = "2026-10-18T09:57:30Z";
  // Fecha de OBSERVACIÓN desde la que los records de data/mirova_equivalent/ son de K (medianoche UTC). Es donde va la
  // línea vertical. null = sin línea ni aviso.
  const DATOS_K_DESDE_UTC = "2025-02-15T00:00:00Z";

  const MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
  const FICHA_URL = "https://github.com/MendozaVolcanic/VRP-chile/blob/main/docs/FICHA_SDA_VRP_CHILE.md";
  const COLOR = "#ffc107";

  function msDelCambio(utc) {
    if (utc == null) return null;
    const t = Date.parse(String(utc));
    return isNaN(t) ? null : t;
  }

  function fechaLegible(utc) {
    const t = msDelCambio(utc);
    if (t == null) return null;
    const d = new Date(t);
    const hh = String(d.getUTCHours()).padStart(2, "0");
    const mm = String(d.getUTCMinutes()).padStart(2, "0");
    return d.getUTCDate() + " " + MESES[d.getUTCMonth()] + " " + d.getUTCFullYear() + " " + hh + ":" + mm;
  }

  function diaLegible(utc) {
    const t = msDelCambio(utc);
    if (t == null) return null;
    const d = new Date(t);
    return d.getUTCDate() + " " + MESES[d.getUTCMonth()] + " " + d.getUTCFullYear();
  }

  // Texto del aviso, o null si no hay cambio que marcar. Sin argumentos usa las dos constantes del módulo.
  function textoAviso(desde, produccion) {
    if (arguments.length === 0) { desde = DATOS_K_DESDE_UTC; produccion = CAMBIO_DETECTOR_UTC; }
    const dia = diaLegible(desde);
    if (dia == null) return null;
    const prod = fechaLegible(produccion);
    return "Los datos con fecha de observación desde el " + dia + " son del detector K (sin el Test 1 integrado; " +
      "ver ficha SDA) y los anteriores, del detector C0" +
      (prod == null ? "" : "; la réplica corre K en producción desde el " + prod + " UTC") + ". " +
      "Las series que crucen el " + dia + " mezclan dos detectores: un cambio en esa fecha no es un cambio del volcán.";
  }

  // Inserta el aviso justo después del primer <header> (o al inicio del body). Devuelve el elemento o null.
  function insertarAviso(doc, desde, produccion) {
    const txt = textoAviso(desde, produccion);
    if (txt == null || !doc || !doc.body) return null;
    if (doc.getElementById && doc.getElementById("aviso-cambio-detector")) return doc.getElementById("aviso-cambio-detector");
    const div = doc.createElement("div");
    div.id = "aviso-cambio-detector";
    div.setAttribute("role", "note");
    div.style.cssText = "margin:6px 16px;padding:6px 10px;border:1px solid " + COLOR + ";border-radius:4px;" +
      "color:" + COLOR + ";background:rgba(255,193,7,0.08);font-size:0.85rem;line-height:1.4;";
    div.appendChild(doc.createTextNode(txt + " "));
    const a = doc.createElement("a");
    a.href = FICHA_URL;
    a.target = "_blank";
    a.rel = "noopener";
    a.style.color = COLOR;
    a.appendChild(doc.createTextNode("Ficha SDA"));
    div.appendChild(a);
    const header = doc.querySelector ? doc.querySelector("header") : null;
    if (header && header.parentNode) header.parentNode.insertBefore(div, header.nextSibling);
    else doc.body.insertBefore(div, doc.body.firstChild);
    return div;
  }

  // Plugin de Chart.js: línea vertical punteada en la fecha del cambio, sólo en gráficos con eje x de tiempo y sólo
  // si la fecha cae dentro del rango visible. No toca datos ni escalas.
  function crearPlugin(utc) {
    return {
      id: "cambioDetector",
      afterDatasetsDraw(chart) {
        const t = msDelCambio(utc);
        const x = chart && chart.scales ? chart.scales.x : null;
        if (t == null || !x || x.type !== "time") return false;
        if (t < x.min || t > x.max) return false;
        const px = x.getPixelForValue(t);
        const area = chart.chartArea;
        if (!isFinite(px) || !area) return false;
        const ctx = chart.ctx;
        ctx.save();
        ctx.strokeStyle = COLOR;
        ctx.lineWidth = 1.5;
        if (ctx.setLineDash) ctx.setLineDash([5, 4]);
        ctx.beginPath();
        ctx.moveTo(px, area.top);
        ctx.lineTo(px, area.bottom);
        ctx.stroke();
        if (ctx.setLineDash) ctx.setLineDash([]);
        ctx.fillStyle = COLOR;
        ctx.font = "10px sans-serif";
        ctx.fillText("detector K", px + 3, area.top + 10);
        ctx.restore();
        return true;
      },
    };
  }

  // ── S172: segunda marca, la vía «código MIROVA» en MODIS (diseño docs/superpowers/specs/2026-11-01-encendido-modd-
  // design.md, decisión 5; regla experiments/_s171_modd_adopcion/REGLA_REVERSION_MODD_BORRADOR.md §5).
  //
  // POR QUÉ: con la vía (el gránulo pasado a la grilla de MIROVA, su detector, su fondo, la suma de todos los
  // alertados) la magnitud de MODIS sube y aparecen alertas que K callaba. Sin marca, ese escalón en la serie de MODIS
  // se lee como un cambio del volcán: en Nevados de Chillán, con el domo activo, «la erupción crece».
  //
  // DESDE LOS DATOS, no desde una constante: la fecha es la de la primera pasada MODIS con `via_codigo_mirova: true`
  // que tiene antes, en los mismos records, una pasada MODIS de K (sin la clave). La condición de «K antes» evita que la
  // marca se corra al primer día del JSON liviano (_recent, 100 días) cuando, pasados 100 días, toda la ventana ya es de
  // la vía; y la caída a K de la vía (la clave con un texto, "sin_mxd03") no cuenta ni como vía ni como K. Las vistas
  // sólo le pasan los records con notarRecords (una llamada por vista, A102); sin records de la vía no se dibuja nada.
  // El auto-audit usa la misma fecha (scripts/auto_audit_weekly.py, frontera_via_modis).
  const COLOR_MODIS = "#ff8c00";       // el naranja de la serie MODIS del tablero
  let viaModis = null;                 // ISO UTC de la primera pasada de la vía, o null

  function isoDeRecord(dt) {
    const s = String(dt || "").trim().replace(" ", "T");
    if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/.test(s)) return null;
    const t = Date.parse(s.slice(0, 16) + ":00Z");
    return isNaN(t) ? null : t;
  }

  // Fecha ISO de la primera pasada MODIS de la vía con una de K antes, o null.
  function primeraViaModis(records) {
    let primeraK = null;
    const via = [];
    for (const r of records || []) {
      if (!r || String(r.sensor || "").indexOf("MODIS") !== 0) continue;
      const t = isoDeRecord(r.datetime_utc);
      if (t == null) continue;
      if (r.via_codigo_mirova === true) via.push(t);
      else if (r.via_codigo_mirova === undefined || r.via_codigo_mirova === null) {
        if (primeraK == null || t < primeraK) primeraK = t;
      }
    }
    if (primeraK == null) return null;
    const despues = via.filter(t => t > primeraK);
    return despues.length ? new Date(Math.min.apply(null, despues)).toISOString() : null;
  }

  function textoAvisoModis(desde) {
    const dia = diaLegible(desde);
    if (dia == null) return null;
    return "Desde el " + dia + " la serie de MODIS viene de la vía «código MIROVA» (el detector que MIROVA publicó " +
      "en su código), que reemplazó al detector K en MODIS; VIIRS no cambia. Desde esa fecha la magnitud de MODIS " +
      "sube y aparecen alertas que K callaba: un escalón en la serie de MODIS en esa fecha es un cambio del detector, " +
      "no del volcán. En Nevados de Chillán ese escalón no quiere decir que la erupción crece.";
  }

  function insertarAvisoModis(doc, desde) {
    const txt = textoAvisoModis(desde);
    if (txt == null || !doc || !doc.body) return null;
    const ya = doc.getElementById ? doc.getElementById("aviso-cambio-via-modis") : null;
    if (ya) {
      // otro volcán trajo una fecha anterior: se corrige el texto (nodo de texto guardado al crearlo)
      if (ya._texto) ya._texto.nodeValue = txt + " ";
      return ya;
    }
    const div = doc.createElement("div");
    div.id = "aviso-cambio-via-modis";
    div.setAttribute("role", "note");
    div.style.cssText = "margin:6px 16px;padding:6px 10px;border:1px solid " + COLOR_MODIS + ";border-radius:4px;" +
      "color:" + COLOR_MODIS + ";background:rgba(255,140,0,0.08);font-size:0.85rem;line-height:1.4;";
    div._texto = doc.createTextNode(txt + " ");
    div.appendChild(div._texto);
    const a = doc.createElement("a");
    a.href = FICHA_URL;
    a.target = "_blank";
    a.rel = "noopener";
    a.style.color = COLOR_MODIS;
    a.appendChild(doc.createTextNode("Ficha SDA"));
    div.appendChild(a);
    const avisoK = doc.getElementById ? doc.getElementById("aviso-cambio-detector") : null;
    const ancla = (avisoK && avisoK.parentNode) ? avisoK : (doc.querySelector ? doc.querySelector("header") : null);
    if (ancla && ancla.parentNode) ancla.parentNode.insertBefore(div, ancla.nextSibling);
    else doc.body.insertBefore(div, doc.body.firstChild);
    return div;
  }

  // Las vistas llaman esto con los records de cada volcán apenas los cargan. Guarda la fecha más temprana de todos los
  // volcanes, pone o actualiza el aviso y redibuja los gráficos ya dibujados. Devuelve la fecha vigente (o null).
  function notarRecords(records, doc) {
    const t = primeraViaModis(records);
    if (t != null && (viaModis == null || Date.parse(t) < Date.parse(viaModis))) {
      viaModis = t;
      const d = doc || (typeof raiz !== "undefined" ? raiz.document : null);
      insertarAvisoModis(d, viaModis);
      const C = typeof raiz !== "undefined" ? raiz.Chart : null;
      if (C && C.instances) Object.values(C.instances).forEach(c => { if (c && c.draw) c.draw(); });
    }
    return viaModis;
  }

  // ¿El gráfico muestra nuestra serie de MODIS? Sí si tiene un dataset visible rotulado «MODIS...» (index, diario), o
  // si todos sus datasets van sin rótulo (la barra de mosaico, que suma los tres sensores). La referencia de MIROVA
  // («MIROVA MODIS (ref.)») no es nuestra serie.
  function muestraModis(chart) {
    const ds = (chart && chart.data && chart.data.datasets) || [];
    if (!ds.length) return false;
    const visible = i => !(chart.isDatasetVisible && !chart.isDatasetVisible(i));
    if (ds.every(d => !d.label)) return ds.some((d, i) => visible(i));
    return ds.some((d, i) => /^MODIS/.test(String(d.label || "")) && visible(i));
  }

  function crearPluginViaModis() {
    return {
      id: "cambioViaModis",
      afterDatasetsDraw(chart) {
        const t = msDelCambio(viaModis);
        const x = chart && chart.scales ? chart.scales.x : null;
        if (t == null || !x || x.type !== "time" || !muestraModis(chart)) return false;
        if (t < x.min || t > x.max) return false;
        const px = x.getPixelForValue(t);
        const area = chart.chartArea;
        if (!isFinite(px) || !area) return false;
        const ctx = chart.ctx;
        ctx.save();
        ctx.strokeStyle = COLOR_MODIS;
        ctx.lineWidth = 1.5;
        if (ctx.setLineDash) ctx.setLineDash([6, 3]);
        ctx.beginPath();
        ctx.moveTo(px, area.top);
        ctx.lineTo(px, area.bottom);
        ctx.stroke();
        if (ctx.setLineDash) ctx.setLineDash([]);
        ctx.fillStyle = COLOR_MODIS;
        ctx.font = "10px sans-serif";
        ctx.fillText("MODIS: vía MIROVA", px + 3, area.top + 34);
        ctx.restore();
        return true;
      },
    };
  }

  const CambioDetector = { CAMBIO_DETECTOR_UTC, DATOS_K_DESDE_UTC, textoAviso, insertarAviso, crearPlugin, fechaLegible,
    primeraViaModis, notarRecords, textoAvisoModis, insertarAvisoModis, crearPluginViaModis,
    viaModisDesde: () => viaModis };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = CambioDetector;
  } else {
    raiz.CambioDetector = CambioDetector;
    raiz.CAMBIO_DETECTOR_UTC = CAMBIO_DETECTOR_UTC;
    // Registro global: cubre el gráfico principal de index, los de diario (tarjetas y ampliado) y los de mosaico,
    // sin tocar el código de cada gráfico. En los que no son de tiempo, el plugin no hace nada. La línea va en la
    // frontera de los DATOS (S155), no en la hora del merge.
    if (DATOS_K_DESDE_UTC != null && raiz.Chart && raiz.Chart.register) raiz.Chart.register(crearPlugin(DATOS_K_DESDE_UTC));
    // S172: el plugin de MODIS se registra siempre; no dibuja nada hasta que notarRecords encuentre la vía.
    if (raiz.Chart && raiz.Chart.register) raiz.Chart.register(crearPluginViaModis());
    if (DATOS_K_DESDE_UTC != null && raiz.document) {
      const poner = () => insertarAviso(raiz.document, DATOS_K_DESDE_UTC, CAMBIO_DETECTOR_UTC);
      if (raiz.document.readyState === "loading") raiz.document.addEventListener("DOMContentLoaded", poner);
      else poner();
    }
  }
})(typeof window !== "undefined" ? window : this);
