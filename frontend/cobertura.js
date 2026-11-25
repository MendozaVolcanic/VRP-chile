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
// parte del período no se miró.
//
// R4FEF-106 (auditoría externa con Codex, ronda 4, S199). POR QUÉ: si el archivo no se podía leer (falta, falla de red,
// JSON cortado), el aviso quedaba vacío y oculto, igual que cuando todo se midió, y esa falla quedaba en caché toda la
// sesión; una lectura buena también, así que un hueco nuevo de NASA nunca aparecía en una página abierta por horas, que
// es como se usa en turno. Ahora: (1) si el archivo no se puede leer, el aviso dice «cobertura no disponible» (no se
// sabe si hubo pasadas sin medir) y la falla no se guarda, se reintenta en la consulta siguiente; (2) una lectura buena
// vale VIGENCIA_MS, la cadencia con que index.html vuelve a consultar los datos (5 min), y después se relee; (3)
// `repintar()` vuelve a pintar los avisos que siguen en la página, para el sondeo de index.html que no redibuja si no
// cambió ningún volcán. Las tres vistas llaman este módulo sólo para los volcanes del NRT, que tienen su archivo desde
// S199, así que un 404 también es «no se pudo leer».
//
// UN SOLO LUGAR para las tres vistas (A102), como crater_no_medido.js. Pruebas: tests/test_cobertura_publicada_s199.py y
// tests/test_tablero_falla_de_carga_r4fef.py
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
  const VIGENCIA_MS = 5 * 60 * 1000;   // R4FEF-106: igual al sondeo de index.html (setInterval de 5 min)
  const cache = {};                     // volcán -> {p: promesa, t: hora de la lectura buena}
  let pintados = [];                    // [{host, volcan, opciones}] para repintar()

  function nombrePlataforma(p) { return NOMBRES[p] || String(p || "plataforma sin dato"); }
  function msDia(f) { return Date.parse(f + "T00:00:00Z"); }
  function msMinuto(m) { return Date.parse(String(m).replace(" ", "T").slice(0, 16) + ":00Z"); }
  function plural(n, s, p) { return n + " " + (n === 1 ? s : p); }

  // Carga data/cobertura/<volcán>.json. Devuelve {estado: "ok", datos} o {estado: "error", motivo}. La falla no queda en
  // caché (se reintenta en la llamada siguiente) y la lectura buena vale VIGENCIA_MS (R4FEF-106).
  async function cargar(volcan, base) {
    const b = typeof base === "string" ? base : (typeof BASE_PATH === "string" ? BASE_PATH : "");
    const c = cache[volcan];
    if (c && (c.t == null || Date.now() - c.t < VIGENCIA_MS)) return c.p;   // t == null: lectura en curso
    const entrada = { p: null, t: null };
    entrada.p = (async () => {
      try {
        const r = await fetch(b + "data/cobertura/" + encodeURIComponent(volcan) + ".json", { cache: "no-cache" });
        if (!r.ok) return { estado: "error", motivo: "HTTP " + r.status };
        const d = await r.json();
        return d && Array.isArray(d.no_medidas) ? { estado: "ok", datos: d } : { estado: "error", motivo: "archivo sin la lista no_medidas" };
      } catch (e) { return { estado: "error", motivo: e && e.name === "SyntaxError" ? "JSON ilegible" : "falla de red" }; }
    })().then(res => {
      if (res.estado === "ok") entrada.t = Date.now();
      else if (cache[volcan] === entrada) delete cache[volcan];
      return res;
    });
    cache[volcan] = entrada;
    return entrada.p;
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

  // R4FEF-106: texto y explicación cuando el archivo no se pudo leer. No afirma nada de las pasadas: no se sabe.
  const TXT_NO_DISPONIBLE = "cobertura no disponible";
  function tituloNoDisponible(motivo) {
    return "No se pudo leer el registro de pasadas no medidas de este volcán (" + (motivo || "motivo sin dato") + "). " +
      "No se sabe si hubo pasadas que el sistema no pudo medir: que no aparezca ninguna no confirma que todo se midió. " +
      "Se vuelve a intentar en la próxima consulta (el tablero consulta cada 5 min). Sólo avisa: no cambia ninguna " +
      "potencia, nivel ni clase.";
  }

  // Pinta en `host` (un elemento vacío ya puesto en la página) el aviso del volcán para [desdeMs, hastaMs]; con
  // `ventanaMs`, el intervalo es [ahora - ventanaMs, ahora] al momento de pintar (así repintar() no lo deja atrás).
  // `modo`: "corto" (una línea con title) o "lista" (encabezado y una línea por día-plataforma). Si no hay nada que
  // decir, el host queda vacío y oculto; si el archivo no se pudo leer, dice «cobertura no disponible». Devuelve la
  // promesa de los items (para pruebas).
  async function pintar(host, volcan, opciones) {
    const o = opciones || {};
    if (!host) return [];
    pintados = pintados.filter(x => x.host !== host && x.host.isConnected !== false);
    pintados.push({ host, volcan, opciones: o });
    host.style.display = "none";
    const r = await cargar(volcan, o.base);
    while (host.firstChild) host.removeChild(host.firstChild);
    host.textContent = "";
    host.title = "";
    if (r.estado !== "ok") {
      host.style.display = "";
      host.style.color = COLOR;
      host.style.cursor = "help";
      host.title = tituloNoDisponible(r.motivo);
      if (o.modo === "lista") {
        const h = document.createElement("div");
        h.className = "cobertura-hdr";
        h.textContent = SIMBOLO + " " + TXT_NO_DISPONIBLE + ": no se pudo leer qué pasadas quedaron sin medir (" + (r.motivo || "motivo sin dato") + ")";
        h.title = host.title;
        host.appendChild(h);
      } else {
        host.textContent = (o.antes || "") + SIMBOLO + " " + TXT_NO_DISPONIBLE + (o.despues || "");
      }
      return [];
    }
    const items = pendientes(r.datos, o.ventanaMs != null ? Object.assign({}, o, { desdeMs: Date.now() - o.ventanaMs, hastaMs: Date.now() }) : o);
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

  // R4FEF-106: vuelve a pintar los avisos que siguen en la página (relee los archivos cuya lectura venció). Para el
  // sondeo de index.html cuando ningún volcán cambió y no se redibujan las tarjetas.
  function repintar() {
    pintados = pintados.filter(x => x.host.isConnected !== false);
    return Promise.all(pintados.slice().map(x => pintar(x.host, x.volcan, x.opciones)));
  }

  const api = { COLOR, SIMBOLO, VIGENCIA_MS, TXT_NO_DISPONIBLE, cargar, pendientes, conteo, textoCorto, lineaItem, titulo,
                pintar, repintar, nombrePlataforma };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else raiz.CoberturaTablero = api;
})(typeof window !== "undefined" ? window : this);
