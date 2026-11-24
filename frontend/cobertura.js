// cobertura.js (S199, hallazgo F6-112 de la auditoría externa con Codex, ronda 2). Marca de sólo display «no medida».
//
// POR QUÉ. Cuando el catálogo de NASA (CMR) no responde, o una pasada no se puede bajar o leer, el sistema no escribe
// ningún record de esa pasada. En los datos, una pasada que no se midió y una noche en que el satélite no pasó se veían
// igual (no hay fila), y el tablero las mostraba como «sin anomalía». Para el operador, una caída de NASA se leía como
// un volcán tranquilo. Desde S199 el NRT y el barrido semanal de huecos escriben data/cobertura/<volcán>.json
// (scripts/cobertura_publicada.py) con lo que no pudieron medir en los últimos 30 días, por día UTC y plataforma:
//   - busqueda_fallida: la búsqueda en el catálogo no respondió. No se sabe si hubo pasada: puede haber una anomalía
//     que no se vio.
//   - pasadas_no_medidas: la búsqueda respondió, pero una o más pasadas no se pudieron bajar, procesar o geolocalizar.
// Lo que una corrida posterior sí midió ya no está en el archivo. Este módulo lo lee y lo dice en las tres vistas.
//
// NO dice nada de la actividad del volcán, no cambia ninguna potencia, nivel, clase ni frescura: sólo avisa que esa
// parte del período no se miró. Si el archivo no está (volcán fuera del NRT, o antes del primer NRT con S199), no se
// marca nada: eso es SIN DATO, no «todo medido».
//
// UN SOLO LUGAR para las tres vistas (A102), como crater_no_medido.js. Prueba: tests/test_cobertura_publicada_s199.py
(function (raiz) {
  "use strict";

  const COLOR = "#ce93d8";
  const SIMBOLO = "⊗";
  const DIA_MS = 86400000;
  const NOMBRES = {
    MODIS_TERRA: "MODIS Terra", MODIS_AQUA: "MODIS Aqua",
    VIIRS_SNPP: "VIIRS 375 Suomi NPP", VIIRS_NOAA20: "VIIRS 375 NOAA-20", VIIRS_NOAA21: "VIIRS 375 NOAA-21",
    VIIRS_SNPP_750: "VIIRS 750 Suomi NPP", VIIRS_NOAA20_750: "VIIRS 750 NOAA-20", VIIRS_NOAA21_750: "VIIRS 750 NOAA-21",
  };
  const ETAPAS = { descarga: "no se pudo bajar", procesamiento: "se bajó y falló al procesarse",
                   geolocalizacion: "llegó sin su archivo de posición" };
  const cache = {};

  function nombrePlataforma(p) { return NOMBRES[p] || String(p || "plataforma sin dato"); }
  function msDia(f) { return Date.parse(f + "T00:00:00Z"); }
  function msMinuto(m) { return Date.parse(String(m).replace(" ", "T").slice(0, 16) + ":00Z"); }
  function plural(n, s, p) { return n + " " + (n === 1 ? s : p); }

  // Carga data/cobertura/<volcán>.json. Devuelve {estado: "ok", datos} o {estado: "sin_archivo"}.
  async function cargar(volcan, base) {
    const b = typeof base === "string" ? base : (typeof BASE_PATH === "string" ? BASE_PATH : "");
    if (volcan in cache) return cache[volcan];
    const p = (async () => {
      try {
        const r = await fetch(b + "data/cobertura/" + encodeURIComponent(volcan) + ".json", { cache: "no-cache" });
        if (!r.ok) return { estado: "sin_archivo" };
        const d = await r.json();
        return d && Array.isArray(d.no_medidas) ? { estado: "ok", datos: d } : { estado: "sin_archivo" };
      } catch (e) { return { estado: "sin_archivo" }; }
    })();
    cache[volcan] = p;
    return p;
  }

  // Lo no medido que toca [desdeMs, hastaMs] (extremos incluidos) y cuya plataforma pasa `filtro(plataforma)`. Un día
  // entero (búsqueda fallida) toca el intervalo si alguna parte del día cae dentro; una pasada, si su minuto cae dentro.
  // Más reciente primero.
  function pendientes(datos, opciones) {
    const o = opciones || {};
    const t0 = o.desdeMs != null ? o.desdeMs : -Infinity;
    const t1 = o.hastaMs != null ? o.hastaMs : Infinity;
    const filtro = typeof o.filtro === "function" ? o.filtro : () => true;
    const out = [];
    for (const it of (datos && datos.no_medidas) || []) {
      if (!it || !it.fecha || !filtro(it.plataforma)) continue;
      if (it.motivo === "pasadas_no_medidas") {
        const pas = (it.pasadas || []).filter(p => {
          if (!p.minuto) { const a = msDia(it.fecha); return a + DIA_MS - 1 >= t0 && a <= t1; }
          const t = msMinuto(p.minuto); return t >= t0 && t <= t1;
        });
        if (pas.length) out.push(Object.assign({}, it, { pasadas: pas }));
      } else {
        const a = msDia(it.fecha);
        if (a + DIA_MS - 1 >= t0 && a <= t1) out.push(it);
      }
    }
    return out.sort((x, y) => (x.fecha < y.fecha ? 1 : x.fecha > y.fecha ? -1 : 0));
  }

  // {dias, pasadas}: días-plataforma con la búsqueda caída y pasadas conocidas que no se midieron.
  function conteo(items) {
    let dias = 0, pasadas = 0;
    for (const it of items || []) {
      if (it.motivo === "pasadas_no_medidas") pasadas += (it.pasadas || []).length || 1;
      else dias += 1;
    }
    return { dias, pasadas };
  }

  // Texto corto: «sin medir: 3 días-satélite (NASA no respondió) y 1 pasada».
  function textoCorto(items) {
    const c = conteo(items);
    if (!c.dias && !c.pasadas) return "";
    const partes = [];
    if (c.dias) partes.push(plural(c.dias, "día-satélite", "días-satélite") + " sin búsqueda (NASA no respondió)");
    if (c.pasadas) partes.push(plural(c.pasadas, "pasada", "pasadas") + " sin medir");
    return "no medido: " + partes.join(" y ");
  }

  // Una línea por día-plataforma: «24 nov · MODIS Aqua: la búsqueda en NASA no respondió».
  function lineaItem(it) {
    const f = it.fecha;
    const quien = nombrePlataforma(it.plataforma);
    if (it.motivo !== "pasadas_no_medidas") {
      return f + " · " + quien + ": la búsqueda en el catálogo de NASA no respondió; no se sabe si hubo pasada";
    }
    const pas = (it.pasadas || []).map(p => (p.minuto ? p.minuto.slice(11, 16) + " UTC" : "hora sin dato") + " " +
      (ETAPAS[p.etapa] || "no se midió"));
    return f + " · " + quien + ": " + (pas.length ? pas.join("; ") : "pasada no medida");
  }

  // Explicación para el operador (title).
  function titulo(items) {
    const t = ["Partes del período que el sistema no pudo medir (no son noches tranquilas):"];
    for (const it of (items || []).slice(0, 12)) t.push("· " + lineaItem(it));
    if ((items || []).length > 12) t.push("· y " + ((items || []).length - 12) + " más (en la página del volcán)");
    t.push("Cuando la búsqueda falla no se sabe si el satélite pasó, y una pasada que no se bajó o no se pudo leer no " +
      "deja fila: en ambos casos la falta de anomalía no está confirmada. El NRT vuelve a intentar cada 2 h durante 8 " +
      "días y el barrido de los domingos, hasta 30 días atrás; lo que se mida desaparece de aquí. Sólo avisa: no cambia " +
      "ninguna potencia, nivel ni clase.");
    return t.join("\n");
  }

  // Pinta en `host` (un elemento vacío ya puesto en la página) el aviso del volcán para [desdeMs, hastaMs]. `modo`:
  // "corto" (una línea con title) o "lista" (encabezado y una línea por día-plataforma). Si no hay nada que decir, el
  // host queda vacío y oculto. Devuelve la promesa de los items (para pruebas).
  async function pintar(host, volcan, opciones) {
    const o = opciones || {};
    if (!host) return [];
    host.style.display = "none";
    const r = await cargar(volcan, o.base);
    if (r.estado !== "ok") return [];
    const items = pendientes(r.datos, o);
    while (host.firstChild) host.removeChild(host.firstChild);
    if (!items.length) return items;
    host.style.display = "";
    host.style.color = COLOR;
    if (o.modo === "lista") {
      const h = document.createElement("div");
      h.className = "cobertura-hdr";
      h.textContent = SIMBOLO + " " + (o.prefijo || "No medido en el período") + ": " + textoCorto(items).replace(/^no medido: /, "");
      h.title = titulo(items);
      host.appendChild(h);
      const ul = document.createElement("ul");
      ul.className = "cobertura-lista";
      for (const it of items) {
        const li = document.createElement("li");
        li.textContent = lineaItem(it);
        ul.appendChild(li);
      }
      host.appendChild(ul);
      const p = document.createElement("div");
      p.className = "cobertura-nota";
      p.textContent = "No son noches «sin anomalía»: el sistema no pudo mirar. Se reintenta solo; lo que se mida sale de " +
        "esta lista. Sólo avisa: no cambia ninguna potencia, nivel ni clase.";
      host.appendChild(p);
    } else {
      host.textContent = (o.antes || "") + SIMBOLO + " " + (o.prefijo ? o.prefijo + " " : "") + textoCorto(items) + (o.despues || "");
      host.title = titulo(items);
      host.style.cursor = "help";
    }
    return items;
  }

  const api = { COLOR, SIMBOLO, cargar, pendientes, conteo, textoCorto, lineaItem, titulo, pintar, nombrePlataforma };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else raiz.CoberturaTablero = api;
})(typeof window !== "undefined" ? window : this);
