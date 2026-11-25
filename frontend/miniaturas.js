// S184: panel «Últimas 10 pasadas» de la página del volcán, como el «Latest images» de MIROVA
// (docs/DISENO_MINIATURAS_POR_PASADA.md). POR QUÉ: una pasada con VRP 0 no dice si el volcán estaba tranquilo, si una
// nube lo tapaba o si la escena quedó cortada en el borde de la franja; la miniatura lo deja ver. Sólo muestra: no
// cambia ninguna detección ni ningún número del tablero.
//
// Lee data/miniaturas/<Volcan>/indice.json y los PNG que escribe el NRT (pipeline/miniaturas.py). Cada PNG es el NTI
// de la grilla de MIROVA del volcán en gris (0 a 254, escala fija), con 255 = sin dato. Aquí se pinta: el gris tal
// cual, el sin dato con un tramado (no blanco, para no confundirlo con un foco saturado, como pasa en MIROVA) y los
// píxeles alertados del índice en rojo encima. El borde va con el color de la clase de la pasada.
const Miniaturas = (() => {
  const FAMILIAS = [
    { key: "VIIRS375", label: "VIIRS 375" },
    { key: "VIIRS750", label: "VIIRS 750" },
    { key: "MODIS",    label: "MODIS" },
  ];
  // R4FB-104 (auditoría Codex ronda 4, S199): TODOS los motivos con que la vía deja una escena sin medir
  // (diag_codigo_mirova.motivo_vacio, pipeline/mirova_v750_codigo.py). POR QUÉ: antes sólo se reconocían los dos
  // primeros y los otros tres caían a «Sin anomalía», que afirma una medición negativa; una escena sin radiancia, con el
  // cráter sin contraste que comparar o una pasada MODIS sin fondo no dicen nada del volcán. [rótulo corto, explicación].
  const MOTIVOS = {
    escena_invalida: ["escena inválida", "La vía «código MIROVA» no midió esta escena: la mitad o más de la grilla " +
      "quedó sin dato útil (borde de la franja o del gránulo, o nubes muy frías). MIROVA tampoco la mide."],
    sunglint: ["reflejo solar", "La pasada no se pudo medir: el reflejo del sol sobre la escena la anula (corte de 12° " +
      "del código de MIROVA)."],
    fondo_no_estimado: ["fondo no estimado", "La vía no midió esta pasada MODIS: los píxeles calientes quedaron junto a " +
      "un hueco de datos y no hubo suelo vecino para restar, así que su potencia sería la radiancia entera del píxel. " +
      "MIROVA no publica pasadas MODIS sin fondo."],
    crater_no_evaluado: ["cráter no evaluable", "La escena pasó el corte de media grilla, pero en el 7 x 7 del cráter no " +
      "quedó ninguna celda con contraste que comparar (escaneos sin dato o nube muy fría justo encima) y no hubo " +
      "alertados en ninguna parte: el cráter no se miró. El código de MIROVA deja ese VRP indefinido."],
    sin_radiancia_valida: ["sin radiancia válida", "La grilla del volcán quedó sin ninguna radiancia válida que " +
      "interpolar: no hubo medición."],
    // S199 (F8-107, F3-102, R3F3-102; acta de cierre de la auditoría Codex): pipeline/mirova_v750_codigo.py,
    // MOTIVO_ANGULO_AUSENTE.
    angulo_ausente: ["sin ángulo", "El gránulo no trajo un ángulo válido del sol o del satélite: no se pudo saber si " +
      "era de noche ni cuánto reflejo solar había, y la vía no midió la pasada."],
  };
  const COLA_NO_MEDIDA = " No dice nada de la actividad del volcán: no es «sin anomalía». El 0 MW guardado no es una medición.";
  const SIN_IMAGEN = {
    detector_k: "Sin imagen: esta pasada la leyó el detector K de guardia, que no usa la grilla de MIROVA",
    sin_granulo_en_esta_corrida: "Sin imagen: el gránulo no se pudo volver a bajar",
  };
  const cache = {};
  // S198: misma raíz que el resto del tablero (BASE_PATH de index.html): en Pages es "" y servido desde la raíz del
  // repo es "/", porque la página cuelga de /frontend/ y los datos de /data/.
  const raiz = () => (typeof BASE_PATH === "string" ? BASE_PATH : "");
  let familiaElegida = null;

  // R4FEF-109 (Codex ronda 4, S199): un índice que no se pudo leer (red, JSON cortado, error del servidor) no se guarda
  // en caché y el panel lo dice; antes quedaba null toda la sesión y el panel desaparecía sin aviso. Un 404 sigue siendo
  // «este volcán no tiene miniaturas» (los 34 de la sombra) y no muestra nada.
  const fallas = {};
  // R4FEF-107, segunda mitad (Codex ronda 4, S200). POR QUÉ: el índice leído bien quedaba en caché toda la sesión; el
  // sondeo de index.html redibuja el panel cuando el NRT trae pasadas nuevas, pero el panel seguía con el índice viejo
  // (la tabla mostraba la pasada nueva y «Últimas 10 pasadas» no) hasta recargar. Una lectura, buena o 404, vale
  // VIGENCIA_MS, la cadencia del sondeo de index.html y de cobertura.js, y después se relee.
  // Prueba: tests/test_miniaturas_relectura_r4fef107.py
  const VIGENCIA_MS = 5 * 60 * 1000;
  const leidoEn = {};
  async function cargarIndice(volcan) {
    if (volcan in cache && Date.now() - leidoEn[volcan] < VIGENCIA_MS) return cache[volcan];
    let idx = null, falla = null;
    try {
      const r = await fetch(`${raiz()}data/miniaturas/${encodeURIComponent(volcan)}/indice.json`, { cache: "no-cache" });
      if (r.ok) idx = await r.json();
      else if (r.status !== 404) falla = "HTTP " + r.status;
    } catch (e) { idx = null; falla = e && e.name === "SyntaxError" ? "JSON ilegible" : "falla de red"; }
    const antes = fallas[volcan];
    if (falla) fallas[volcan] = falla; else delete fallas[volcan];
    if (antes !== fallas[volcan] && typeof window !== "undefined" && typeof window.dispatchEvent === "function" &&
        typeof CustomEvent === "function") window.dispatchEvent(new CustomEvent("vrp-falla-capa"));   // el encabezado lo cuenta
    if (falla) return null;   // no se guarda: se reintenta la próxima vez que se abra el volcán
    cache[volcan] = idx;
    leidoEn[volcan] = Date.now();
    return idx;
  }

  function nodo(tag, cls, texto) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (texto != null) e.textContent = texto;
    return e;
  }

  function colorVar(nombre, defecto) {
    const v = getComputedStyle(document.documentElement).getPropertyValue(nombre).trim();
    return v || defecto;
  }

  // Pinta el PNG en un canvas de n x n celdas: gris, sin dato tramado, alertados en rojo.
  function pintar(canvas, img, entrada) {
    const n = entrada.n || img.naturalWidth;
    canvas.width = n; canvas.height = n;
    const ctx = canvas.getContext("2d");
    ctx.imageSmoothingEnabled = false;
    ctx.drawImage(img, 0, 0, n, n);
    const datos = ctx.getImageData(0, 0, n, n);
    const px = datos.data;
    for (let f = 0; f < n; f++) {
      for (let c = 0; c < n; c++) {
        const k = (f * n + c) * 4;
        if (px[k] === 255) {                         // sin dato: tramado diagonal claro
          const t = ((f + c) % 4 < 2) ? 215 : 238;
          px[k] = t; px[k + 1] = t + 6; px[k + 2] = 255;
        }
      }
    }
    for (const [f, c] of entrada.alertadas || []) {
      if (f < 0 || c < 0 || f >= n || c >= n) continue;
      const k = (f * n + c) * 4;
      px[k] = 255; px[k + 1] = 23; px[k + 2] = 68; px[k + 3] = 255;
    }
    ctx.putImageData(datos, 0, 0);
  }

  function minutos(dt) {
    const ms = Date.parse(String(dt).replace(" ", "T") + (String(dt).length <= 16 ? ":00Z" : "Z"));
    return isNaN(ms) ? null : ms / 60000;
  }

  const CNM = () => (typeof CraterNoMedido !== "undefined" ? CraterNoMedido : null);   // frontend/crater_no_medido.js
  const CUMBRE = () => (typeof CumbreTablero !== "undefined" ? CumbreTablero : null);   // frontend/cumbre.js

  function km(x) {   // como cumbre.js: un decimal bajo 10 km, coma decimal
    return (typeof x === "number" && Number.isFinite(x)) ? x.toFixed(x < 10 ? 1 : 0).replace(".", ",") + " km" : null;
  }

  // R4FB-104, R4FB-105, R4FB-106 y R4FB-V202 (auditoría Codex ronda 4, S199): qué dice el pie de la tarjeta. POR QUÉ.
  // La imagen pinta en rojo TODOS los alertados de la pasada, y la potencia que se publica es la del tablero (eqVrp), que
  // con «Solo cráter» vale 0 para una detección lejana. Leer ese 0 como «Sin anomalía» al lado de píxeles rojos le dice
  // al geólogo de turno que no hubo calor (6 de 120 tarjetas al 2026-11-24, VIIRS 375 de Isluga, Láscar, Lastarria y
  // Planchón-Peteroa). Tampoco es «Sin anomalía» una escena que la vía no midió, ni un cráter con la MIR perdida. Se usa
  // la misma lógica que la tabla de «Últimas pasadas» (rotuloPasadaSinPublicar de index.html) y las marcas de
  // crater_no_medido.js, en este orden: escena no medida (motivo_vacio), falta el record del tablero, potencia publicada,
  // cráter no medido, anomalía lejana, anomalía no publicada, sin anomalía. Con opts.recordDe, si el record de la pasada
  // no está (el JSON del volcán no cargó o ya no tiene esa pasada) NO se cae a la potencia del índice: esa es la suma de
  // todos los alertados, sin el filtro de lejanas, y mostraba lejanas como potencia del cráter (R4FB-V202). Sólo display:
  // no cambia ninguna potencia, nivel, clase ni detección.
  // Devuelve {tipo, texto, title, vrp, avisos: [{texto, title}]}; tipo: con | no_medida | sin_dato | cnm | lejana |
  // no_publicada | nada.
  function estado(entrada, opts) {
    const conRecord = typeof opts.recordDe === "function";
    const rec = conRecord ? (opts.recordDe(entrada) || null) : null;
    const diag = rec && rec.diag_codigo_mirova && typeof rec.diag_codigo_mirova === "object" ? rec.diag_codigo_mirova : null;
    const motivo = (diag && diag.motivo_vacio) || entrada.motivo_vacio || null;
    if (motivo) {
      const m = MOTIVOS[motivo];
      return { tipo: "no_medida", texto: "No medida: " + (m ? m[0] : String(motivo).replace(/_/g, " ")),
               title: (m ? m[1] : "La vía «código MIROVA» dejó esta escena sin medir (" + motivo + ").") + COLA_NO_MEDIDA,
               vrp: 0, avisos: [] };
    }
    const sinDato = { tipo: "sin_dato", texto: "Sin dato del tablero", vrp: 0, avisos: [],
      title: "No se encontró esta pasada en los datos del volcán (no cargaron o ya no la traen), así que no se puede " +
        "decir qué potencia publica el tablero. La imagen y sus píxeles rojos sí son de la pasada; la suma de todos sus " +
        "alertados no se muestra porque incluiría las detecciones lejanas que el tablero no publica con «Solo cráter»." };
    if (conRecord && !rec) return sinDato;
    const vrp = opts.vrpDe ? opts.vrpDe(entrada, rec) : (entrada.vrp_mw || 0);
    if (typeof vrp !== "number" || !Number.isFinite(vrp)) return sinDato;
    const C = CNM();
    const cnm = rec && C ? C.craterNoMedido(rec) : null;
    const fondo = rec && C ? C.fondoNoEstimado(rec) : null;
    const avisoCrater = cnm ? { texto: C.SIMBOLO + " " + C.textoCrater(cnm), title: C.tituloCrater(cnm) } : null;
    const avisoFondo = fondo ? { texto: C.SIMBOLO + " " + C.textoFondo(fondo), title: C.tituloFondo(fondo) } : null;
    if (vrp > 0) {
      return { tipo: "con", texto: `VRP = ${vrp >= 10 ? vrp.toFixed(1) : vrp.toFixed(2)} MW`, title: "", vrp,
               avisos: [avisoCrater, avisoFondo].filter(Boolean) };
    }
    if (cnm && C.esNoMedido(cnm)) {
      return { tipo: "cnm", texto: "Cráter no medido", title: C.tituloCrater(cnm), vrp: 0,
               avisos: [avisoFondo].filter(Boolean) };
    }
    const fuente = rec || entrada;
    const nAlert = Math.max(fuente.n_anomalous_pixels || 0, (entrada.alertadas || []).length);
    const conCumulo = !!(rec && rec.primary_cluster && (rec.primary_cluster.vrp_mw || 0) > 0);
    const avisos = [avisoCrater, avisoFondo].filter(Boolean);
    if (nAlert > 0 || conCumulo) {
      const dist = km(fuente.final_hotspot_dist_km);
      if (fuente.distance_class === "far") {
        const radio = km(opts.radioKm);
        // La regla «radiante» (D8') pone la pasada lejos aunque también haya alertados en la cumbre; la marca de cumbre.js
        // que ya llevan la tabla y el mapa lo avisa, y aquí también (si no, «lejana» escondería el calor del cráter).
        const Cu = CUMBRE();
        const mcu = rec && Cu ? Cu.calorEnCumbre(rec, opts.radioKm) : null;
        if (mcu) avisos.unshift({ texto: "◉ " + Cu.textoCumbre(mcu), title: Cu.tituloCumbre(mcu, rec, opts.radioKm),
                                  color: Cu.COLOR });
        return { tipo: "lejana", texto: "Anomalía lejana" + (dist ? ", " + dist : ""), vrp: 0, avisos,
          title: "La pasada tuvo " + (nAlert === 1 ? "1 píxel alertado" : nAlert + " píxeles alertados") +
            (dist ? ", con el foco más radiante a " + dist + " del cráter" : "") + ", fuera del radio del cráter" +
            (radio ? " (" + radio + ")" : "") + ": son los píxeles rojos de la imagen. Con «Solo cráter» el tablero " +
            "no publica la potencia de las detecciones lejanas; con «Incluir lejanas» cuenta. No es «sin anomalía»." };
      }
      return { tipo: "no_publicada", texto: "Anomalía no publicada", vrp: 0, avisos,
        title: "La pasada tuvo píxeles anómalos, pero ninguno cuenta como detección publicada: lejana (fuera del radio " +
          "del cráter, con «Solo cráter»), descartada por el pipeline o marcada como artefacto térmico. Con «Incluir " +
          "lejanas» las lejanas vuelven a contar." };
    }
    return { tipo: "nada", texto: "Sin anomalía", title: "", vrp: 0, avisos };
  }

  function tarjeta(base, entrada, siguiente, opts) {
    const est = estado(entrada, opts);
    const vrp = est.vrp;
    const nivel = opts.getLevel && vrp > 0 ? opts.getLevel(vrp) : null;
    const t = nodo("figure", "mini-tarjeta" + (vrp > 0 ? " mini-con" : "") +
      (est.tipo === "lejana" || est.tipo === "no_publicada" ? " mini-lejana" : "") +
      (est.tipo === "no_medida" || est.tipo === "sin_dato" || est.tipo === "cnm" ? " mini-no-medida" : ""));
    t.dataset.estado = est.tipo;
    if (nivel && vrp > 0) t.dataset.nivel = nivel.key;
    const fecha = nodo("figcaption", "mini-fecha", opts.fmtHora ? opts.fmtHora(entrada.datetime_utc) : entrada.datetime_utc);
    fecha.title = entrada.datetime_utc + " UTC · " + (entrada.granule || "");
    t.appendChild(fecha);
    const marco = nodo("div", "mini-marco");
    if (entrada.archivo) {
      const cv = nodo("canvas", "mini-canvas");
      cv.setAttribute("role", "img");
      cv.setAttribute("aria-label", `NTI de la pasada ${entrada.datetime_utc} UTC, ${entrada.sensor}`);
      const img = new Image();
      img.onload = () => pintar(cv, img, entrada);
      img.onerror = () => { marco.textContent = "No cargó la imagen"; };
      img.src = `${base}/${entrada.archivo}`;
      marco.appendChild(cv);
    } else {
      marco.appendChild(nodo("div", "mini-vacia", SIN_IMAGEN[entrada.sin_imagen] || "Sin imagen"));
    }
    t.appendChild(marco);
    const pie = nodo("div", "mini-pie");
    const l1 = nodo("div", "mini-vrp", est.texto);
    if (est.title) l1.title = est.title;
    pie.appendChild(l1);
    for (const a of est.avisos) {   // R4FB-105: las marcas de crater_no_medido.js, como en la tabla y los gráficos
      const ma = nodo("div", "mini-marca", a.texto);
      ma.title = a.title;
      if (a.color) ma.style.color = a.color;
      pie.appendChild(ma);
    }
    const zen = entrada.sensor_zenith_deg, azi = entrada.sensor_azimuth_deg;
    pie.appendChild(nodo("div", "mini-geo",
      (zen != null ? `cenit ${Math.round(zen)}°` : "cenit ?") + (azi != null ? ` · azimut ${Math.round(azi)}°` : "")));
    const sat = String(entrada.sensor || "").replace(/^VIIRS_|^MODIS_/, "").replace(/_750$/, "");
    let l3 = sat + (entrada.product_version === "nrt" ? " · NRT" : "");
    // S198: desde que main abrió el día de MODIS (S193) el store trae pasadas diurnas; de día el MIR suma luz solar
    // reflejada y la imagen sale más clara sin que haya calor, así que se dice.
    if (entrada.dayflag === 1) l3 += " · de día";
    if (siguiente && siguiente.sensor === entrada.sensor) {
      const a = minutos(entrada.datetime_utc), b = minutos(siguiente.datetime_utc);
      if (a != null && b != null && Math.abs(a - b) <= 6) {
        l3 += " · mismo paso que la siguiente";
      }
    }
    pie.appendChild(nodo("div", "mini-sat", l3));
    t.appendChild(pie);
    return t;
  }

  function estilos() {
    if (document.getElementById("mini-estilos")) return;
    const s = document.createElement("style");
    s.id = "mini-estilos";
    s.textContent = `
      .mini-panel { margin: 18px 0; }
      .mini-cab { display: flex; flex-wrap: wrap; align-items: baseline; gap: 8px 14px; margin-bottom: 8px; }
      .mini-cab h3 { margin: 0; font-size: 1rem; }
      .mini-tabs button { background: transparent; border: 1px solid var(--border, #3a4a5c); color: inherit;
        border-radius: 4px; padding: 2px 8px; margin-right: 4px; cursor: pointer; font: inherit; font-size: .85rem; }
      .mini-tabs button[aria-pressed="true"] { background: var(--border, #3a4a5c); }
      .mini-grilla { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 10px; }
      @media (max-width: 760px) { .mini-grilla { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
      .mini-tarjeta { margin: 0; font-size: .78rem; text-align: center; min-width: 0; }
      .mini-fecha { color: var(--muted, #7a8fa6); margin-bottom: 3px; }
      .mini-con .mini-fecha, .mini-con .mini-vrp { color: var(--red, #f44336); font-weight: 600; }
      .mini-marco { border: 3px solid var(--border, #3a4a5c); aspect-ratio: 1 / 1; background: #10161d;
        display: flex; align-items: center; justify-content: center; }
      .mini-tarjeta[data-nivel="vlow"] .mini-marco { border-color: var(--green, #00d084); }
      .mini-tarjeta[data-nivel="low"] .mini-marco { border-color: var(--yellow, #ffc107); }
      .mini-tarjeta[data-nivel="mod"] .mini-marco { border-color: var(--orange, #ff7043); }
      .mini-tarjeta[data-nivel="high"] .mini-marco { border-color: var(--red, #f44336); }
      .mini-tarjeta[data-nivel="vhigh"] .mini-marco { border-color: var(--red, #f44336); }
      .mini-canvas { width: 100%; height: 100%; image-rendering: pixelated; display: block; }
      .mini-vacia { color: var(--muted, #7a8fa6); padding: 6px; font-size: .72rem; }
      .mini-pie { margin-top: 3px; line-height: 1.3; }
      .mini-geo, .mini-sat { color: var(--muted, #7a8fa6); }
      .mini-lejana .mini-vrp { color: var(--muted, #7a8fa6); font-weight: 600; }
      .mini-no-medida .mini-vrp { color: var(--muted, #7a8fa6); font-style: italic; }
      .mini-marca { color: #ffab40; font-size: .72rem; }
      .mini-aviso { color: var(--muted, #7a8fa6); font-size: .75rem; margin-top: 8px; }
    `;
    document.head.appendChild(s);
  }

  // Monta el panel en `host` (se agrega al final). opts: { sensor: "VIIRS375" | "VIIRS750" | "MODIS" | "COMB",
  // vrpDe(entrada) -> MW como lo cuenta el tablero, getLevel(vrp) -> {cls}, fmtHora(datetime_utc) -> texto }.
  function montar(host, volcan, opts = {}) {
    estilos();
    const panel = nodo("section", "mini-panel");
    panel.id = "mini-panel";
    host.appendChild(panel);
    cargarIndice(volcan).then(idx => {
      if (!idx && fallas[volcan]) {   // R4FEF-109: no se pudo leer; no es «sin pasadas»
        panel.appendChild(nodo("h3", null, "Últimas pasadas"));
        panel.appendChild(nodo("div", "mini-aviso", "No se pudo leer el índice de miniaturas (" + fallas[volcan] + "). " +
          "Se vuelve a intentar al abrir de nuevo el volcán; el resto de la página no se afecta."));
        return;
      }
      if (!idx || !idx.familias) { panel.remove(); return; }   // volcán sin miniaturas todavía: no se muestra nada
      const base = `${raiz()}data/miniaturas/${encodeURIComponent(volcan)}`;
      const conDatos = FAMILIAS.filter(f => (idx.familias[f.key] || []).length);
      if (!conDatos.length) { panel.remove(); return; }
      let fam = FAMILIAS.some(f => f.key === opts.sensor) ? opts.sensor : familiaElegida;
      if (!fam || !conDatos.some(f => f.key === fam)) {
        // «Combinado»: la del sensor de la pasada más nueva, como la cabecera de MIROVA
        fam = conDatos.slice().sort((a, b) =>
          String(idx.familias[b.key][0].datetime_utc).localeCompare(String(idx.familias[a.key][0].datetime_utc)))[0].key;
      }
      const dibujar = () => {
        while (panel.firstChild) panel.removeChild(panel.firstChild);
        const cab = nodo("div", "mini-cab");
        cab.appendChild(nodo("h3", null, `Últimas ${idx.n_ultimas || 10} pasadas`));
        const tabs = nodo("div", "mini-tabs");
        for (const f of conDatos) {
          const b = nodo("button", null, f.label);
          b.type = "button";
          b.setAttribute("aria-pressed", String(f.key === fam));
          b.addEventListener("click", () => { fam = f.key; familiaElegida = f.key; dibujar(); });
          tabs.appendChild(b);
        }
        cab.appendChild(tabs);
        cab.appendChild(nodo("small", "mini-nota",
          "NTI de cada pasada, de la más nueva a la más vieja; frío oscuro, caliente claro; rojo = píxel alertado; tramado = sin dato"));
        panel.appendChild(cab);
        const grilla = nodo("div", "mini-grilla");
        const lista = idx.familias[fam] || [];
        lista.forEach((e, i) => grilla.appendChild(tarjeta(base, e, lista[i + 1], opts)));
        panel.appendChild(grilla);
        panel.appendChild(nodo("div", "mini-aviso",
          "Una anomalía puede deberse a incendios u otras fuentes no volcánicas. Una nube puede ocultarla o atenuarla. " +
          "VIIRS: sólo pasadas de noche. MODIS: también de día (marcadas «de día»; el sol aclara la imagen sin que haya calor)."));
      };
      dibujar();
    });
    return panel;
  }

  return { montar, cargarIndice, VIGENCIA_MS, fallasIndice: () => Object.assign({}, fallas), _pintar: pintar, _estado: estado };
})();
