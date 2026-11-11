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
//
// S178 (decisión b3 de Nicolás, 2026-11-10): el aviso y la línea de K salen de los DATOS. Desde #883 no hay ningún
// record anterior al 2025-02-15, así que el aviso «los anteriores, del detector C0» describía algo que no está; siguió
// tres semanas en pantalla porque su prueba vigilaba la fecha, no que existiera algo al otro lado. Ahora sólo aparecen
// si notarRecords (la llamada de las marcas de la vía, una por vista) recibe un record con fecha de observación
// anterior a DATOS_K_DESDE_UTC; si un dato así vuelve, el aviso vuelve solo. La constante se queda: la leen
// scripts/vigilancia_sombra.py y scripts/auto_audit_weekly.py como frontera (sin ella la vigilancia se declara ciega).
// Prueba: tests/test_cambio_detector_aviso_k_por_datos_s178.py.
(function (raiz) {
  "use strict";

  // Fecha y hora UTC del merge del PR de adopción de K, en ISO con Z (p. ej. "2026-10-19T14:05:00Z"). null = sin marca.
  const CAMBIO_DETECTOR_UTC = "2026-10-18T09:57:30Z";
  // Fecha de OBSERVACIÓN desde la que los records de data/mirova_equivalent/ son de K (medianoche UTC). Es donde va la
  // línea vertical. null = sin línea ni aviso. S178: aun con fecha, línea y aviso sólo si hay datos anteriores.
  const DATOS_K_DESDE_UTC = "2025-02-15T00:00:00Z";
  let hayDatosAntesDeK = false;   // S178: ¿alguna vista pasó un record anterior a DATOS_K_DESDE_UTC?

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
  // si la fecha cae dentro del rango visible. No toca datos ni escalas. `activo` (S178, opcional): función que dice si
  // hay algo que marcar; el plugin registrado en las vistas usa hayDatosAntesDeK.
  function crearPlugin(utc, activo) {
    return {
      id: "cambioDetector",
      afterDatasetsDraw(chart) {
        if (activo && !activo()) return false;
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
  //
  // S176: lo mismo para cada VIIRS (diseño docs/superpowers/specs/2026-11-08-encendido-v375e-design.md, decisiones 4 y 7).
  // POR QUÉ: con la vía, K deja de publicar el núcleo recortado y la magnitud sube cerca del doble (VIIRS 375: razón mediana
  // contra MIROVA 0,50 con K y 0,99 con la vía en la sombra; VIIRS 750: K publica 0,510 de MIROVA y el código 0,999,
  // experiments/_s162_v750c/INFORME.md punto 3). Sin marca, el operador lee que el volcán crece. Cada sensor se enciende y se
  // revierte por separado (B1 y B2), así que cada uno tiene su fecha, su aviso y su línea. Sin records de la vía no se
  // dibuja nada: con los flags apagados el tablero no cambia.
  const VIAS = {
    MODIS: {
      color: "#ff8c00", fondo: "rgba(255,140,0,0.08)", idAviso: "aviso-cambio-via-modis", idPlugin: "cambioViaModis",
      rotulo: "MODIS: vía MIROVA", dy: 34, serie: /^MODIS/,
      texto: dia => "Desde el " + dia + " la serie de MODIS viene de la vía «código MIROVA» (el detector que MIROVA publicó " +
        "en su código), que reemplazó al detector K en MODIS; VIIRS no cambia. Desde esa fecha la magnitud de MODIS " +
        "sube y aparecen alertas que K callaba: un escalón en la serie de MODIS en esa fecha es un cambio del detector, " +
        "no del volcán. En Nevados de Chillán ese escalón no quiere decir que la erupción crece.",
    },
    VIIRS375: {
      color: "#e91e63", fondo: "rgba(233,30,99,0.08)", idAviso: "aviso-cambio-via-v375", idPlugin: "cambioViaV375",
      rotulo: "VIIRS 375: vía MIROVA", dy: 46, serie: /^VIIRS\b.*375/,
      texto: dia => "Desde el " + dia + " la serie de VIIRS 375 viene de la vía «código MIROVA» (el detector que MIROVA " +
        "publicó en su código), que reemplazó al detector K en VIIRS 375. Desde esa fecha la magnitud de VIIRS 375 sube " +
        "cerca del doble, porque K publicaba el núcleo del cúmulo y la vía suma todos los píxeles alertados: un escalón en " +
        "esa fecha es un cambio del detector y no quiere decir que el volcán crezca.",
    },
    VIIRS750: {
      color: "#00bcd4", fondo: "rgba(0,188,212,0.08)", idAviso: "aviso-cambio-via-v750", idPlugin: "cambioViaV750",
      rotulo: "VIIRS 750: vía MIROVA", dy: 58, serie: /^VIIRS\b.*750/,
      texto: dia => "Desde el " + dia + " la serie de VIIRS 750 viene de la vía «código MIROVA» (el detector que MIROVA " +
        "publicó en su código), que reemplazó al detector K en VIIRS 750. Desde esa fecha la magnitud de VIIRS 750 sube " +
        "cerca del doble: un escalón en esa fecha es un cambio del detector, no del volcán.",
    },
  };
  const COLOR_MODIS = VIAS.MODIS.color;   // el naranja de la serie MODIS del tablero
  const desdeVia = { MODIS: null, VIIRS375: null, VIIRS750: null };   // ISO UTC de la primera pasada de cada vía, o null

  function isoDeRecord(dt) {
    const s = String(dt || "").trim().replace(" ", "T");
    if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/.test(s)) return null;
    const t = Date.parse(s.slice(0, 16) + ":00Z");
    return isNaN(t) ? null : t;
  }

  // S173 S1: ¿el record lo escribió la vía «código MIROVA»? Un solo lugar para la marca (A102): lo usan
  // primeraVia y los filtros de artefacto térmico de las tres vistas (isCirrusArtifact, isDiffuseFieldArtifact),
  // que no se aplican a la vía porque se calibraron contra el path D de K, que la vía no tiene. `=== true`: la clave
  // con texto ("sin_grilla", "sin_mxd03", "geo_distinta") es K que corrió con la vía encendida (A118).
  function esViaCodigoMirova(r) {
    return !!r && r.via_codigo_mirova === true;
  }

  // La convención de sensores del proyecto (A48): VIIRS_*_750 es M-band; los demás VIIRS, I-band.
  function familiaSensor(sensor) {
    const s = String(sensor || "");
    if (s.indexOf("MODIS") === 0) return "MODIS";
    if (s.indexOf("VIIRS") !== 0) return null;
    return /_750$/.test(s) ? "VIIRS750" : "VIIRS375";
  }

  // Fecha ISO de la primera pasada de la vía del sensor con una de K antes, o null.
  function primeraVia(records, familia) {
    let primeraK = null;
    const via = [];
    for (const r of records || []) {
      if (!r || familiaSensor(r.sensor) !== familia) continue;
      const t = isoDeRecord(r.datetime_utc);
      if (t == null) continue;
      if (esViaCodigoMirova(r)) via.push(t);
      else if (r.via_codigo_mirova === undefined || r.via_codigo_mirova === null) {
        if (primeraK == null || t < primeraK) primeraK = t;
      }
    }
    if (primeraK == null) return null;
    const despues = via.filter(t => t > primeraK);
    return despues.length ? new Date(Math.min.apply(null, despues)).toISOString() : null;
  }

  function primeraViaModis(records) { return primeraVia(records, "MODIS"); }

  function textoAvisoVia(familia, desde) {
    const dia = diaLegible(desde);
    return dia == null ? null : VIAS[familia].texto(dia);
  }

  function textoAvisoModis(desde) { return textoAvisoVia("MODIS", desde); }

  function insertarAvisoVia(familia, doc, desde) {
    const v = VIAS[familia];
    const txt = textoAvisoVia(familia, desde);
    if (txt == null || !doc || !doc.body) return null;
    const ya = doc.getElementById ? doc.getElementById(v.idAviso) : null;
    if (ya) {
      // otro volcán trajo una fecha anterior: se corrige el texto (nodo de texto guardado al crearlo)
      if (ya._texto) ya._texto.nodeValue = txt + " ";
      return ya;
    }
    const div = doc.createElement("div");
    div.id = v.idAviso;
    div.setAttribute("role", "note");
    div.style.cssText = "margin:6px 16px;padding:6px 10px;border:1px solid " + v.color + ";border-radius:4px;" +
      "color:" + v.color + ";background:" + v.fondo + ";font-size:0.85rem;line-height:1.4;";
    div._texto = doc.createTextNode(txt + " ");
    div.appendChild(div._texto);
    const a = doc.createElement("a");
    a.href = FICHA_URL;
    a.target = "_blank";
    a.rel = "noopener";
    a.style.color = v.color;
    a.appendChild(doc.createTextNode("Ficha SDA"));
    div.appendChild(a);
    const avisoK = doc.getElementById ? doc.getElementById("aviso-cambio-detector") : null;
    const ancla = (avisoK && avisoK.parentNode) ? avisoK : (doc.querySelector ? doc.querySelector("header") : null);
    if (ancla && ancla.parentNode) ancla.parentNode.insertBefore(div, ancla.nextSibling);
    else doc.body.insertBefore(div, doc.body.firstChild);
    return div;
  }

  function insertarAvisoModis(doc, desde) { return insertarAvisoVia("MODIS", doc, desde); }

  // Las vistas llaman esto con los records de cada volcán apenas los cargan. Guarda, por sensor, la fecha más temprana de
  // todos los volcanes y redibuja los gráficos ya dibujados (la vía no pone aviso de texto desde S178). Devuelve la fecha de MODIS
  // (lo que siempre devolvió; las de VIIRS se leen con viaDesde).
  function notarRecords(records, doc) {
    let cambio = false;
    const tK = msDelCambio(DATOS_K_DESDE_UTC);
    if (!hayDatosAntesDeK && tK != null && (records || []).some(r => {
      const t = r ? isoDeRecord(r.datetime_utc) : null;
      return t != null && t < tK;
    })) {
      hayDatosAntesDeK = true;
      insertarAviso(doc || (typeof raiz !== "undefined" ? raiz.document : null), DATOS_K_DESDE_UTC, CAMBIO_DETECTOR_UTC);
      cambio = true;
    }
    Object.keys(VIAS).forEach(familia => {
      const t = primeraVia(records, familia);
      if (t != null && (desdeVia[familia] == null || Date.parse(t) < Date.parse(desdeVia[familia]))) {
        desdeVia[familia] = t;
        // POR QUÉ (S178, pedido de Nicolás del 2026-11-10, «quita los 3»): la vía ya no pone aviso de texto arriba del
        // tablero; la marca queda sólo como línea vertical en los gráficos (crearPluginVia), que da la fecha sin ocupar
        // espacio. insertarAvisoVia y textoAvisoVia siguen exportadas, pero nadie las llama.
        // Prueba: tests/test_cambio_detector_via_modis_s172.py y tests/test_cambio_detector_via_viirs_s176.py.
        cambio = true;
      }
    });
    if (cambio) {
      const C = typeof raiz !== "undefined" ? raiz.Chart : null;
      if (C && C.instances) Object.values(C.instances).forEach(c => { if (c && c.draw) c.draw(); });
    }
    return desdeVia.MODIS;
  }

  // ¿El gráfico muestra nuestra serie de ese sensor? Sí si tiene un dataset visible con su rótulo (index, diario), o si
  // todos sus datasets van sin rótulo (la barra de mosaico, que suma los tres sensores). La referencia de MIROVA
  // («MIROVA MODIS (ref.)») no es nuestra serie.
  function muestraSensor(chart, familia) {
    const ds = (chart && chart.data && chart.data.datasets) || [];
    if (!ds.length) return false;
    const visible = i => !(chart.isDatasetVisible && !chart.isDatasetVisible(i));
    if (ds.every(d => !d.label)) return ds.some((d, i) => visible(i));
    return ds.some((d, i) => VIAS[familia].serie.test(String(d.label || "")) && visible(i));
  }

  function crearPluginVia(familia) {
    const v = VIAS[familia];
    return {
      id: v.idPlugin,
      afterDatasetsDraw(chart) {
        const t = msDelCambio(desdeVia[familia]);
        const x = chart && chart.scales ? chart.scales.x : null;
        if (t == null || !x || x.type !== "time" || !muestraSensor(chart, familia)) return false;
        if (t < x.min || t > x.max) return false;
        const px = x.getPixelForValue(t);
        const area = chart.chartArea;
        if (!isFinite(px) || !area) return false;
        const ctx = chart.ctx;
        ctx.save();
        ctx.strokeStyle = v.color;
        ctx.lineWidth = 1.5;
        if (ctx.setLineDash) ctx.setLineDash([6, 3]);
        ctx.beginPath();
        ctx.moveTo(px, area.top);
        ctx.lineTo(px, area.bottom);
        ctx.stroke();
        if (ctx.setLineDash) ctx.setLineDash([]);
        ctx.fillStyle = v.color;
        ctx.font = "10px sans-serif";
        ctx.fillText(v.rotulo, px + 3, area.top + v.dy);
        ctx.restore();
        return true;
      },
    };
  }

  function crearPluginViaModis() { return crearPluginVia("MODIS"); }

  const CambioDetector = { CAMBIO_DETECTOR_UTC, DATOS_K_DESDE_UTC, textoAviso, insertarAviso, crearPlugin, fechaLegible,
    primeraViaModis, primeraVia, esViaCodigoMirova, notarRecords, textoAvisoModis, textoAvisoVia, insertarAvisoModis,
    insertarAvisoVia, crearPluginViaModis, crearPluginVia, familiaSensor,
    viaModisDesde: () => desdeVia.MODIS, viaDesde: familia => desdeVia[familia], hayDatosAntesDeK: () => hayDatosAntesDeK };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = CambioDetector;
  } else {
    raiz.CambioDetector = CambioDetector;
    raiz.CAMBIO_DETECTOR_UTC = CAMBIO_DETECTOR_UTC;
    // Registro global: cubre el gráfico principal de index, los de diario (tarjetas y ampliado) y los de mosaico,
    // sin tocar el código de cada gráfico. En los que no son de tiempo, el plugin no hace nada. La línea va en la
    // frontera de los DATOS (S155), no en la hora del merge, y sólo si hay datos anteriores a ella (S178).
    if (DATOS_K_DESDE_UTC != null && raiz.Chart && raiz.Chart.register) {
      raiz.Chart.register(crearPlugin(DATOS_K_DESDE_UTC, () => hayDatosAntesDeK));
    }
    // S172: los plugins de la vía se registran siempre; no dibujan nada hasta que notarRecords encuentre la vía.
    if (raiz.Chart && raiz.Chart.register) Object.keys(VIAS).forEach(f => raiz.Chart.register(crearPluginVia(f)));
    // S178: el aviso de K ya no se pone al cargar; lo pone notarRecords cuando ve un record anterior a la frontera.
  }
})(typeof window !== "undefined" ? window : this);
