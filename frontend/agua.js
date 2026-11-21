// agua.js (S193, pedido de Nicolás del 2026-11-21: «tenemos gente revisando las anomalías, sería bueno mejorar los
// mapas»). Capa de cuerpos de agua y marca «pico sobre agua» para quien revisa anomalías a mano.
//
// POR QUÉ. De noche un lago guarda el calor del día y queda más tibio que la roca y la nieve que lo rodean: para el
// detector es un conjunto de píxeles más tibios que sus vecinos, que es lo que busca. MIROVA no tiene máscara de agua
// (el .m de VIIRS 750 sólo rechaza el reflejo solar, de día) y Coppola et al. 2016a (documentacion/sp426_5.txt,
// l. 689 a 694) reconoce falsas detecciones de menos de 5 MW en el borde de cuerpos de agua, que el operador quita
// mirando el mapa. La sesión S193 «lagos» (experiments/_s193_lagos/INFORME.md) midió el píxel más caliente sobre agua
// en 124 de 14.391 pasadas de la vía (0,9 %), 35 de ellas en Laguna del Maule (su punto está dentro del lago) y 21 en
// Carrán-Los Venados. Sobre la imagen satelital el revisor no distinguía el lago del cráter.
//
// QUÉ HACE Y QUÉ NO. Sólo dibuja y rotula: no cambia ninguna detección, ningún valor publicado ni el nivel de alerta.
// Una erupción también puede empezar en el agua (Laguna del Maule, maares de Carrán), así que la marca invita a mirar,
// no descarta. El criterio es el de experiments/_s193_lagos/medir_agua.py para que el tablero y el informe digan lo
// mismo: el píxel de la pasada con mayor temperatura de brillo MIR («pico») está «sobre agua» si UMBRAL_CELDA o más de
// su celda (375 m en VIIRS 375, 750 m en VIIRS 750, 1 km en MODIS, la grilla de MIROVA) es agua en JRC Global Surface
// Water v1.4 (ocurrencia de 50 % o más, 1984 a 2021). La capa (frontend/agua/<Volcan>.geojson) la genera
// scripts/generar_capa_agua.py; contra la máscara a 30 m clasifica igual 41.988 de 41.989 píxeles de la vía
// (experiments/_s193_mapas_agua/comparar_fraccion.txt). JRC es un promedio de 37 años: no sabe si esa noche el lago
// estaba congelado. La celda es la del nadir; fuera de nadir la huella real es mayor (A36).
//
// UN SOLO LUGAR para las tres vistas (A102), como cambio_detector.js. Prueba: tests/test_tablero_agua_s193.py
(function (raiz) {
  "use strict";

  const UMBRAL_CELDA = 0.5;
  const BASE_CAPAS = "agua/";
  const TOPE_PIXELES = 3000;   // como TOPE_PIXELES_MEDIDOS de index.html: con K hubo pasadas de casi 2000 píxeles
  const KM_POR_GRADO = 111.32;
  const FUENTE = "JRC Global Surface Water v1.4, ocurrencia de agua de 50 % o más entre 1984 y 2021";

  // Lado de la celda (km) de la grilla de MIROVA por sensor. Igual a sensorFootprintKm de index.html para los 8
  // sensores (la prueba lo exige); aquí porque diario y mosaico no tienen esa función.
  function ladoCeldaKm(sensor) {
    const s = String(sensor || "").toUpperCase();
    if (s.includes("MODIS")) return 1.0;
    if (s.endsWith("_750")) return 0.75;
    if (s.startsWith("VIIRS")) return 0.375;
    return 0.5;
  }

  // Área (grados²) de un anillo [[lon, lat], ...] recortado contra el rectángulo (Sutherland-Hodgman: el recorte de
  // un polígono cualquiera contra uno convexo conserva el área de la intersección).
  function areaRecortada(anillo, x0, y0, x1, y1) {
    let pts = anillo;
    const bordes = [
      p => p[0] >= x0, p => p[0] <= x1, p => p[1] >= y0, p => p[1] <= y1,
    ];
    const cortes = [
      (a, b) => [x0, a[1] + (b[1] - a[1]) * (x0 - a[0]) / (b[0] - a[0])],
      (a, b) => [x1, a[1] + (b[1] - a[1]) * (x1 - a[0]) / (b[0] - a[0])],
      (a, b) => [a[0] + (b[0] - a[0]) * (y0 - a[1]) / (b[1] - a[1]), y0],
      (a, b) => [a[0] + (b[0] - a[0]) * (y1 - a[1]) / (b[1] - a[1]), y1],
    ];
    for (let k = 0; k < 4 && pts.length; k++) {
      const dentro = bordes[k], corte = cortes[k], sal = [];
      for (let i = 0; i < pts.length; i++) {
        const a = pts[i], b = pts[(i + 1) % pts.length];
        const ia = dentro(a), ib = dentro(b);
        if (ia) sal.push(a);
        if (ia !== ib) sal.push(corte(a, b));
      }
      pts = sal;
    }
    let s = 0;
    for (let i = 0; i < pts.length; i++) {
      const a = pts[i], b = pts[(i + 1) % pts.length];
      s += a[0] * b[1] - b[0] * a[1];
    }
    return Math.abs(s) / 2;
  }

  function cajaDe(anillo) {
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    for (const p of anillo) {
      if (p[0] < x0) x0 = p[0]; if (p[0] > x1) x1 = p[0];
      if (p[1] < y0) y0 = p[1]; if (p[1] > y1) y1 = p[1];
    }
    return [x0, y0, x1, y1];
  }

  // Polígonos de la capa con su caja, calculados una vez por capa.
  function indice(capa) {
    if (capa._indice) return capa._indice;
    const out = [];
    for (const f of capa.features || []) {
      const g = f && f.geometry;
      if (!g) continue;
      const polys = g.type === "Polygon" ? [g.coordinates] : g.type === "MultiPolygon" ? g.coordinates : [];
      for (const anillos of polys) if (anillos && anillos.length) out.push({ anillos, caja: cajaDe(anillos[0]) });
    }
    Object.defineProperty(capa, "_indice", { value: out, enumerable: false });
    return out;
  }

  // Fracción (0 a 1) de la celda de lado `ladoKm` centrada en (lat, lon) que es agua en la capa. null si no hay capa
  // o la celda no cabe entera en la ventana de la capa: ahí no se midió, y un 0 diría «tierra» sin saberlo.
  function fraccionAgua(capa, lat, lon, ladoKm) {
    if (!capa || !Number.isFinite(lat) || !Number.isFinite(lon) || !(ladoKm > 0)) return null;
    const cos = Math.cos(lat * Math.PI / 180);
    const hl = ladoKm / 2 / KM_POR_GRADO, hn = ladoKm / 2 / (KM_POR_GRADO * cos);
    const x0 = lon - hn, x1 = lon + hn, y0 = lat - hl, y1 = lat + hl;
    const p = capa.properties || {};
    if (Number.isFinite(p.lat) && Number.isFinite(p.lon) && Number.isFinite(p.media_ventana_km)) {
      const vl = p.media_ventana_km / KM_POR_GRADO;
      const vn = p.media_ventana_km / (KM_POR_GRADO * Math.cos(p.lat * Math.PI / 180));
      if (y0 < p.lat - vl || y1 > p.lat + vl || x0 < p.lon - vn || x1 > p.lon + vn) return null;
    }
    let agua = 0;
    for (const { anillos, caja } of indice(capa)) {
      if (caja[2] <= x0 || caja[0] >= x1 || caja[3] <= y0 || caja[1] >= y1) continue;
      agua += areaRecortada(anillos[0], x0, y0, x1, y1);
      for (let i = 1; i < anillos.length; i++) agua -= areaRecortada(anillos[i], x0, y0, x1, y1);
    }
    const f = agua / ((x1 - x0) * (y1 - y0));
    return Math.min(1, Math.max(0, f));
  }

  function pixelesValidos(r) {
    return ((r && r.anomaly_pixels) || []).filter(p => p && Number.isFinite(p.lat) && Number.isFinite(p.lon));
  }

  // Píxel de mayor temperatura de brillo MIR (el que define la posición en la vía, regla «radiante»); sin bt_k, el
  // primero de la lista. null sin píxeles.
  function pixelPico(r) {
    let mejor = null;
    for (const p of pixelesValidos(r)) {
      if (mejor === null) { mejor = p; continue; }
      if (Number.isFinite(p.bt_k) && (!Number.isFinite(mejor.bt_k) || p.bt_k > mejor.bt_k)) mejor = p;
    }
    return mejor;
  }

  // Lo que el revisor necesita de una pasada: fracción de agua de la celda del pico, si está sobre agua, cuántos de
  // sus píxeles lo están, y el contraste del pico contra el fondo (dT, K). null sin capa, sin píxeles o fuera de la
  // ventana de la capa.
  function aguaDePasada(r, capa) {
    const pico = pixelPico(r);
    if (!capa || !pico) return null;
    const lado = ladoCeldaKm(r.sensor);
    const fraccion = fraccionAgua(capa, pico.lat, pico.lon, lado);
    if (fraccion === null) return null;
    const pix = pixelesValidos(r).slice(0, TOPE_PIXELES);
    let nAgua = 0;
    for (const p of pix) {
      const f = p === pico ? fraccion : fraccionAgua(capa, p.lat, p.lon, lado);
      if (f !== null && f >= UMBRAL_CELDA) nAgua++;
    }
    const dT = Number.isFinite(pico.bt_k) && Number.isFinite(r.t_bg_k) ? pico.bt_k - r.t_bg_k : null;
    return { fraccion, sobreAgua: fraccion >= UMBRAL_CELDA, pixel: pico, ladoKm: lado, nAgua, n: pix.length, dT };
  }

  function pct(f) { return Math.round(f * 100) + " %"; }
  function num(x, d) { return x.toFixed(d).replace(".", ","); }

  // Rótulo corto (tabla, tarjeta, popup).
  function textoAgua(m) {
    if (!m || !m.sobreAgua) return "";
    return "pico sobre agua (" + pct(m.fraccion) + " de la celda)";
  }

  // Explicación larga (title y popup).
  function tituloAgua(m) {
    if (!m) return "";
    const lado = m.ladoKm >= 1 ? "1 km" : Math.round(m.ladoKm * 1000) + " m";
    return "El píxel más caliente de esta pasada cae en una celda de " + lado + " de la que " + pct(m.fraccion) +
      " es agua (" + FUENTE + ")" + (m.n > 1 ? "; " + m.nAgua + " de sus " + m.n + " píxeles alertados están sobre agua" : "") +
      (m.dT !== null ? ". Contraste del pico contra el fondo: " + num(m.dT, 1) + " K" : "") +
      ". De noche un lago queda más tibio que la roca a su alrededor y el detector, como el de MIROVA, puede " +
      "alertarlo (Coppola 2016a: falsas detecciones de menos de 5 MW en orillas). No es un descarte: una erupción " +
      "también puede empezar en el agua. Revísalo en el mapa.";
  }

  // Carga perezosa de la capa de un volcán. capaEnCache: undefined = no se ha pedido; null = falló; objeto = capa.
  const cache = new Map();
  const pendientes = new Map();
  function capaEnCache(nombre) { return cache.get(nombre); }
  function cargarCapa(nombre, base) {
    if (cache.has(nombre)) return Promise.resolve(cache.get(nombre));
    if (pendientes.has(nombre)) return pendientes.get(nombre);
    const url = (base == null ? BASE_CAPAS : base) + encodeURIComponent(nombre) + ".geojson";
    const p = fetch(url).then(r => (r.ok ? r.json() : null)).catch(() => null).then(capa => {
      cache.set(nombre, capa && capa.type === "FeatureCollection" ? capa : null);
      pendientes.delete(nombre);
      return cache.get(nombre);
    });
    pendientes.set(nombre, p);
    return p;
  }

  // Estilo de la capa en Leaflet: celeste con borde, poco relleno para no tapar la imagen satelital.
  const ESTILO_CAPA = { color: "#40c4ff", weight: 1.2, fillColor: "#40c4ff", fillOpacity: 0.18, interactive: false };
  const COLOR_AGUA = "#40c4ff";

  const AguaTablero = {
    UMBRAL_CELDA, FUENTE, ESTILO_CAPA, COLOR_AGUA, ladoCeldaKm, fraccionAgua, pixelPico, aguaDePasada,
    textoAgua, tituloAgua, cargarCapa, capaEnCache,
  };

  if (typeof module !== "undefined" && module.exports) module.exports = AguaTablero;
  else raiz.AguaTablero = AguaTablero;
})(typeof window !== "undefined" ? window : this);
