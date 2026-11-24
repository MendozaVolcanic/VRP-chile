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
  const MOTIVOS = {
    escena_invalida: "Sin lectura: escena inválida (más de la mitad sin dato, borde de franja)",
    sunglint: "Sin lectura: reflejo solar (sun glint)",
  };
  const SIN_IMAGEN = {
    detector_k: "Sin imagen: esta pasada la leyó el detector K de guardia, que no usa la grilla de MIROVA",
    sin_granulo_en_esta_corrida: "Sin imagen: el gránulo no se pudo volver a bajar",
  };
  const cache = {};
  // S198: misma raíz que el resto del tablero (BASE_PATH de index.html): en Pages es "" y servido desde la raíz del
  // repo es "/", porque la página cuelga de /frontend/ y los datos de /data/.
  const raiz = () => (typeof BASE_PATH === "string" ? BASE_PATH : "");
  let familiaElegida = null;

  async function cargarIndice(volcan) {
    if (volcan in cache) return cache[volcan];
    let idx = null;
    try {
      const r = await fetch(`${raiz()}data/miniaturas/${encodeURIComponent(volcan)}/indice.json`, { cache: "no-cache" });
      if (r.ok) idx = await r.json();
    } catch (e) { idx = null; }
    cache[volcan] = idx;
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

  function tarjeta(base, entrada, siguiente, opts) {
    const vrp = opts.vrpDe ? opts.vrpDe(entrada) : (entrada.vrp_mw || 0);
    const nivel = opts.getLevel ? opts.getLevel(vrp) : null;
    const t = nodo("figure", "mini-tarjeta" + (vrp > 0 ? " mini-con" : ""));
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
    let linea1;
    if (vrp > 0) linea1 = `VRP = ${vrp >= 10 ? vrp.toFixed(1) : vrp.toFixed(2)} MW`;
    else if (MOTIVOS[entrada.motivo_vacio]) linea1 = "Sin lectura";
    else linea1 = "Sin anomalía";
    const l1 = nodo("div", "mini-vrp", linea1);
    if (MOTIVOS[entrada.motivo_vacio]) l1.title = MOTIVOS[entrada.motivo_vacio];
    pie.appendChild(l1);
    const zen = entrada.sensor_zenith_deg, azi = entrada.sensor_azimuth_deg;
    pie.appendChild(nodo("div", "mini-geo",
      (zen != null ? `cenit ${Math.round(zen)}°` : "cenit ?") + (azi != null ? ` · azimut ${Math.round(azi)}°` : "")));
    const sat = String(entrada.sensor || "").replace(/^VIIRS_|^MODIS_/, "").replace(/_750$/, "");
    let l3 = sat + (entrada.product_version === "nrt" ? " · NRT" : "");
    // S198: desde que main abrió el día de MODIS (S193) el store trae pasadas diurnas; de día el MIR suma luz solar
    // reflejada y la imagen sale más clara sin que haya calor, así que se dice.
    if (entrada.dayflag === 1) l3 += " · de día";
    if (MOTIVOS[entrada.motivo_vacio]) l3 += entrada.motivo_vacio === "escena_invalida" ? " · escena inválida" : " · sun glint";
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

  return { montar, cargarIndice, _pintar: pintar };
})();
