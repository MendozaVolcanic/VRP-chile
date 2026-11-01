// cese_plataformas.js (S159): aviso al operador del cese de Suomi NPP (NASA, 2026-11-02 13:00 UTC).
//
// POR QUÉ: VIIRS vuela en tres satélites (Suomi NPP, NOAA-20 y NOAA-21) que pasan sobre Chile de noche en un racimo
// de una a dos horas. Desde el cese quedan dos: cada noche hay una mirada menos al volcán, y una anomalía débil que a
// veces se ve y a veces no (nube fina, ángulo de visión, píxel que parte el foco) tiene menos probabilidad de
// publicarse. El pipeline no se entera (cero gránulos se lee como «no hubo pasada»), las series «VIIRS SNPP» salen de
// la leyenda sin mensaje y la tendencia tiene un tercio menos de puntos VIIRS por noche. Sin aviso, eso se lee como un
// cambio del volcán. Este módulo no cambia ningún dato ni el criterio de publicación.
//
// UN SOLO LUGAR, como cambio_detector.js: la fecha vive acá y no copiada en las tres vistas (A102). La misma fecha
// vive en scripts/ceses_esperados.json para la vigilancia por plataforma; tests/test_cese_plataformas_s159.py exige
// que coincidan. Si NASA mueve la fecha, se cambia en los dos.
//
// CUÁNDO SE VE: antes del cese, como aviso previo en futuro (el operador sabe desde ya que la serie va a cambiar y
// por qué; NASA lo anunció con fecha y hora). Desde el cese, en pasado, durante DIAS_AVISO_DESPUES días: la vista
// diaria muestra la tendencia de 90 días, así que pasado ese plazo ninguna serie de esa vista cruza la fecha. La línea
// vertical se queda para siempre, porque sólo aparece cuando la fecha cae dentro del rango que se mira.
//
// ZONA HORARIA: el corte compara milisegundos UTC (Date.now() contra Date.parse de una fecha con Z), y la fecha se
// escribe con getUTC*, así que no depende de la hora local del computador del operador (el proyecto ya tuvo un bug de
// zona horaria en el frontend).
//
// comparacion.html NO lleva este aviso: es una vista de preview («no es el dashboard live»), igual que no lleva
// mirovaEqVrp.
(function (raiz) {
  "use strict";

  const PLATAFORMA = "Suomi NPP";
  const CESE_UTC = "2026-11-02T13:00:00Z";
  const FUENTE_URL = "https://www.earthdata.nasa.gov/data/alerts-outages/reminder-suomi-npp-observations-cease-november-2-2026";
  const DIAS_AVISO_DESPUES = 90;

  const MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
  const COLOR = "#8ec5ff";
  const DIA_MS = 86400000;

  function ms(utc) {
    if (utc == null) return null;
    const t = Date.parse(String(utc));
    return isNaN(t) ? null : t;
  }

  function dia(t) {
    const d = new Date(t);
    return d.getUTCDate() + " " + MESES[d.getUTCMonth()] + " " + d.getUTCFullYear();
  }

  function hora(t) {
    const d = new Date(t);
    return String(d.getUTCHours()).padStart(2, "0") + ":" + String(d.getUTCMinutes()).padStart(2, "0");
  }

  // Texto del aviso para el instante `ahoraMs` (milisegundos UTC), o null si ya pasó el plazo.
  function textoAviso(ahoraMs, ceseUtc) {
    const c = ms(ceseUtc === undefined ? CESE_UTC : ceseUtc);
    if (c == null || ahoraMs == null || isNaN(ahoraMs)) return null;
    if (ahoraMs >= c + DIAS_AVISO_DESPUES * DIA_MS) return null;
    const fecha = dia(c), h = hora(c);
    if (ahoraMs < c) {
      return "Aviso de NASA: el satélite " + PLATAFORMA + " dejará de entregar datos el " + fecha + " a las " + h +
        " UTC. Desde entonces VIIRS (375 m y 750 m) seguirá sólo con NOAA-20 y NOAA-21: habrá una pasada VIIRS menos " +
        "por noche (dos en vez de tres). Las series anteriores no cambian.";
    }
    return "Desde el " + fecha + " a las " + h + " UTC, el satélite " + PLATAFORMA + " dejó de entregar datos " +
      "(aviso de NASA). VIIRS (375 m y 750 m) sigue con NOAA-20 y NOAA-21: hay una pasada VIIRS menos por noche (dos " +
      "en vez de tres), así que una anomalía débil que aparece en una sola pasada tiene menos probabilidad de verse. " +
      "Las series anteriores al " + fecha + " no cambian.";
  }

  // Inserta el aviso después del aviso del detector K si existe, si no después del primer <header> (o al inicio del
  // body). Devuelve el elemento, o null si no corresponde mostrarlo.
  function insertarAviso(doc, ahoraMs) {
    const txt = textoAviso(ahoraMs);
    if (txt == null || !doc || !doc.body) return null;
    const ya = doc.getElementById ? doc.getElementById("aviso-cese-plataformas") : null;
    if (ya) return ya;
    const div = doc.createElement("div");
    div.id = "aviso-cese-plataformas";
    div.setAttribute("role", "note");
    div.style.cssText = "margin:6px 16px;padding:6px 10px;border:1px solid " + COLOR + ";border-radius:4px;" +
      "color:" + COLOR + ";background:rgba(142,197,255,0.08);font-size:0.85rem;line-height:1.4;" +
      "overflow-wrap:anywhere;";
    div.appendChild(doc.createTextNode(txt + " "));
    const a = doc.createElement("a");
    a.href = FUENTE_URL;
    a.target = "_blank";
    a.rel = "noopener";
    a.style.color = COLOR;
    a.appendChild(doc.createTextNode("Aviso de NASA"));
    div.appendChild(a);
    const avisoK = doc.getElementById ? doc.getElementById("aviso-cambio-detector") : null;
    const ancla = (avisoK && avisoK.parentNode) ? avisoK : (doc.querySelector ? doc.querySelector("header") : null);
    if (ancla && ancla.parentNode) ancla.parentNode.insertBefore(div, ancla.nextSibling);
    else doc.body.insertBefore(div, doc.body.firstChild);
    return div;
  }

  // Plugin de Chart.js: línea vertical punteada en la fecha del cese, sólo en ejes de tiempo y dentro del rango visible.
  function crearPlugin(utc) {
    return {
      id: "cesePlataformas",
      afterDatasetsDraw(chart) {
        const t = ms(utc);
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
        if (ctx.setLineDash) ctx.setLineDash([2, 3]);
        ctx.beginPath();
        ctx.moveTo(px, area.top);
        ctx.lineTo(px, area.bottom);
        ctx.stroke();
        if (ctx.setLineDash) ctx.setLineDash([]);
        ctx.fillStyle = COLOR;
        ctx.font = "10px sans-serif";
        ctx.fillText("sin " + PLATAFORMA, px + 3, area.top + 22);
        ctx.restore();
        return true;
      },
    };
  }

  const CesePlataformas = { PLATAFORMA, CESE_UTC, FUENTE_URL, DIAS_AVISO_DESPUES, textoAviso, insertarAviso, crearPlugin };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = CesePlataformas;
  } else {
    raiz.CesePlataformas = CesePlataformas;
    if (raiz.Chart && raiz.Chart.register) raiz.Chart.register(crearPlugin(CESE_UTC));
    if (raiz.document) {
      const reloj = (raiz.Date && raiz.Date.now) ? raiz.Date : Date;
      const poner = () => insertarAviso(raiz.document, reloj.now());
      if (raiz.document.readyState === "loading") raiz.document.addEventListener("DOMContentLoaded", poner);
      else poner();
    }
  }
})(typeof window !== "undefined" ? window : this);
