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
(function (raiz) {
  "use strict";

  // Fecha y hora UTC del merge del PR de adopción de K, en ISO con Z (p. ej. "2026-10-19T14:05:00Z"). null = sin marca.
  const CAMBIO_DETECTOR_UTC = "2026-10-18T09:57:30Z";

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

  // Texto del aviso, o null si no hay cambio que marcar.
  function textoAviso(utc) {
    const f = fechaLegible(utc);
    if (f == null) return null;
    return "Desde el " + f + " UTC la réplica usa el detector K (sin el Test 1 integrado; ver ficha SDA). " +
      "Las comparaciones que crucen esa fecha mezclan dos detectores.";
  }

  // Inserta el aviso justo después del primer <header> (o al inicio del body). Devuelve el elemento o null.
  function insertarAviso(doc, utc) {
    const txt = textoAviso(utc);
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

  const CambioDetector = { CAMBIO_DETECTOR_UTC, textoAviso, insertarAviso, crearPlugin, fechaLegible };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = CambioDetector;
  } else {
    raiz.CambioDetector = CambioDetector;
    raiz.CAMBIO_DETECTOR_UTC = CAMBIO_DETECTOR_UTC;
    // Registro global: cubre el gráfico principal de index, los de diario (tarjetas y ampliado) y los de mosaico,
    // sin tocar el código de cada gráfico. En los que no son de tiempo, el plugin no hace nada.
    if (CAMBIO_DETECTOR_UTC != null && raiz.Chart && raiz.Chart.register) raiz.Chart.register(crearPlugin(CAMBIO_DETECTOR_UTC));
    if (CAMBIO_DETECTOR_UTC != null && raiz.document) {
      const poner = () => insertarAviso(raiz.document, CAMBIO_DETECTOR_UTC);
      if (raiz.document.readyState === "loading") raiz.document.addEventListener("DOMContentLoaded", poner);
      else poner();
    }
  }
})(typeof window !== "undefined" ? window : this);
