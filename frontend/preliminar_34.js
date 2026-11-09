// FICHA (Resolución CPLT N°372, docs/FICHA_SDA_VRP_CHILE.md). Sistema: VRP Chile. Componente: vista preliminar de los 34
// volcanes fuera del NRT. Clasifica para mostrar; no detecta ni decide alerta. Sin referencia de MIROVA: paridad no medida.
//
// POR QUÉ este módulo aparte: la sombra detecta dentro de una grilla de unos 50 km y estos volcanes no tienen radio de cráter en
// `volcanoes.yaml`, así que sus records salen con `distance_class: null`. Medido del 2026-11-03 al 11-08: 22 detecciones, ninguna
// a 5 km o menos del volcán. Si la página las pintara como anomalía del volcán, el operador leería actividad donde hay un foco
// a 30 km, que puede ser un incendio, otro volcán o un artefacto. Por eso cada detección se separa por distancia. Se prueba en
// node sin navegador: tests/test_vista_preliminar_34_s177.py.
(function (raiz) {
  "use strict";

  // POR QUÉ 5 km: es el radio de cumbre de 6 de los 11 KML de MIROVA y el que usa el plan de los 34 (decisión D5). Es un
  // valor por defecto para volcanes que MIROVA no definió, no una medida de cada cráter.
  const RADIO_CUMBRE_KM = 5;

  // POR QUÉ 72 h: la sombra corre una vez al día y puede perder un día por un corte de NASA; dos días sin pasada es un aviso.
  const HORAS_SIN_PASADA = 72;

  // POR QUÉ 1 km: en los dos pares medidos el foco visto desde dos volcanes difiere en 0,11 y 0,16 km; 1 km es unos dos
  // píxeles de 375 m y no junta focos distintos.
  const KM_MISMO_FOCO = 1;

  // Copia de volcanoes.yaml (radius_km distinto de 25); la prueba exige que coincidan.
  const VOLCANES = [
    { name: "Taapaca", display: "Taapaca", region: "Arica y Parinacota", lat: -18.1, lon: -69.5 },
    { name: "Parinacota", display: "Parinacota", region: "Arica y Parinacota", lat: -18.166, lon: -69.142 },
    { name: "Guallatiri", display: "Guallatiri", region: "Arica y Parinacota", lat: -18.42, lon: -69.09 },
    { name: "Irruputuncu", display: "Irruputuncu", region: "Tarapacá", lat: -20.73, lon: -68.55 },
    { name: "OlcaParuma", display: "Olca-Paruma", region: "Tarapacá", lat: -20.942, lon: -68.503 },
    { name: "Ollague", display: "Ollagüe", region: "Antofagasta", lat: -21.3, lon: -68.18 },
    { name: "SanPedro", display: "San Pedro", region: "Antofagasta", lat: -21.88, lon: -68.4 },
    { name: "Putana", display: "Putana", region: "Antofagasta", lat: -22.557, lon: -67.853 },
    { name: "SanJose", display: "San José", region: "Metropolitana", lat: -33.789, lon: -69.897 },
    { name: "Tinguiririca", display: "Tinguiririca", region: "O'Higgins", lat: -34.814, lon: -70.352 },
    { name: "DescabezadoGrande", display: "Descabezado Grande", region: "Maule", lat: -35.58, lon: -70.75 },
    { name: "CerroAzulQuizapu", display: "Cerro Azul - Quizapu", region: "Maule", lat: -35.653, lon: -70.761 },
    { name: "LagunaDelMaule", display: "Laguna del Maule", region: "Maule", lat: -36.056836, lon: -70.501398 },
    { name: "NevadoDeLongavi", display: "Nevado de Longaví", region: "Maule", lat: -36.193, lon: -71.161 },
    { name: "Antuco", display: "Antuco", region: "Biobío", lat: -37.406, lon: -71.349 },
    { name: "Callaqui", display: "Callaqui", region: "Biobío", lat: -37.92, lon: -71.45 },
    { name: "Tolhuaca", display: "Tolhuaca", region: "Araucanía", lat: -38.31, lon: -71.645 },
    { name: "Lonquimay", display: "Lonquimay", region: "Araucanía", lat: -38.38, lon: -71.58 },
    { name: "Sollipulli", display: "Sollipulli", region: "Araucanía", lat: -38.97, lon: -71.52 },
    { name: "Quetrupillan", display: "Quetrupillán", region: "Araucanía", lat: -39.496, lon: -71.722 },
    { name: "Lanin", display: "Lanín", region: "Araucanía", lat: -39.633, lon: -71.503 },
    { name: "MochoChoshuenco", display: "Mocho-Choshuenco", region: "Los Ríos", lat: -39.927, lon: -72.027 },
    { name: "CarranLosVenados", display: "Carrán-Los Venados", region: "Los Ríos", lat: -40.35, lon: -72.07 },
    { name: "AntillancaCasablanca", display: "Antillanca-Casablanca", region: "Los Lagos", lat: -40.77, lon: -72.15 },
    { name: "Osorno", display: "Osorno", region: "Los Lagos", lat: -41.1, lon: -72.493 },
    { name: "Calbuco", display: "Calbuco", region: "Los Lagos", lat: -41.33, lon: -72.614 },
    { name: "YateHornopiren", display: "Yate-Hornopirén", region: "Los Lagos", lat: -41.76, lon: -72.39 },
    { name: "Huequi", display: "Huequi", region: "Los Lagos", lat: -42.377, lon: -72.578 },
    { name: "Michinmahuida", display: "Michinmahuida", region: "Los Lagos", lat: -42.79, lon: -72.44 },
    { name: "CorcovadoYanteles", display: "Corcovado-Yanteles", region: "Los Lagos", lat: -43.183, lon: -72.8 },
    { name: "Melimoyu", display: "Melimoyu", region: "Aysén", lat: -44.08, lon: -72.88 },
    { name: "Mentolat", display: "Mentolat", region: "Aysén", lat: -44.67, lon: -73.08 },
    { name: "MacaCay", display: "Macá-Cay", region: "Aysén", lat: -45.1, lon: -73.2 },
    { name: "Hudson", display: "Hudson", region: "Aysén", lat: -45.9, lon: -72.97 },
  ];

  function clasificar(r, volcan) {
    if (!r || !(r.vrp_mw > 0)) return { estado: "sin_deteccion", dist_km: null };
    // POR QUÉ mirar cada píxel: la distancia del record es la del cúmulo más radiante y el VRP suma todos. Un píxel alertado en
    // el cráter con un cúmulo mayor lejos se leería como «foco lejano», y es justo la actividad que hay que ver.
    if (volcan && Array.isArray(r.anomaly_pixels)) {
      let min = Infinity;
      for (const p of r.anomaly_pixels) {
        if (p.lat != null && p.lon != null) min = Math.min(min, distanciaKm(volcan.lat, volcan.lon, p.lat, p.lon));
      }
      if (min <= RADIO_CUMBRE_KM) return { estado: "cumbre", dist_km: min };
    }
    const d = r.final_hotspot_dist_km;
    // Una detección sin posición no se asigna a la cumbre ni a lo lejano: se muestra como lo que es.
    if (d === null || d === undefined) return { estado: "sin_posicion", dist_km: null };
    return { estado: d <= RADIO_CUMBRE_KM ? "cumbre" : "lejos", dist_km: d };
  }

  function distanciaKm(aLat, aLon, bLat, bLon) {
    const rad = Math.PI / 180;
    const dLat = (bLat - aLat) * rad;
    const dLon = (bLon - aLon) * rad;
    const x = Math.sin(dLat / 2) ** 2 + Math.cos(aLat * rad) * Math.cos(bLat * rad) * Math.sin(dLon / 2) ** 2;
    return 2 * 6371 * Math.asin(Math.sqrt(x));
  }

  // Una grilla de 50 km se traslapa con la del volcán vecino: la misma pasada puede detectar el mismo foco desde los dos.
  function focosCompartidos(detecciones) {
    return detecciones.map((d) => ({
      ...d,
      tambien_desde: detecciones
        .filter((o) => o.volcan !== d.volcan && o.datetime_utc === d.datetime_utc && o.sensor === d.sensor &&
          o.final_hotspot_lat != null && d.final_hotspot_lat != null &&
          distanciaKm(d.final_hotspot_lat, d.final_hotspot_lon, o.final_hotspot_lat, o.final_hotspot_lon) <= KM_MISMO_FOCO)
        .map((o) => o.volcan),
    }));
  }

  // `datetime_utc` viene como «2026-11-08 05:12», en UTC: sin la Z, el navegador lo leería como hora local.
  function msUtc(texto) {
    return Date.parse(texto.replace(" ", "T") + ":00Z");
  }

  function contarFocos(detecciones) {
    const c = { cumbre: 0, lejos: 0 };
    for (const d of detecciones) {
      if (d.estado === "cumbre") c.cumbre++;
      else if (d.tambien_desde.every((o) => d.volcan < o)) c.lejos++;   // el mismo foco, una sola vez
    }
    return c;
  }

  function resumenVolcan(records, ahoraMs, ventanaDias, volcan) {
    const desde = ahoraMs - ventanaDias * 86400000;
    let ultima = null;
    const res = { n_cumbre: 0, n_lejos: 0, n_sin_posicion: 0, vrp_max: 0, ultima_pasada: null, primera_pasada: null,
      ultima_deteccion: null, sin_pasadas_recientes: true };
    for (const r of records) {
      // POR QUÉ: una escena inválida no miró el volcán; contarla como pasada presentaría una ausencia como calma.
      if (r.diag_codigo_mirova && r.diag_codigo_mirova.motivo_vacio) continue;
      if (ultima === null || r.datetime_utc > ultima) ultima = r.datetime_utc;
      if (res.primera_pasada === null || r.datetime_utc < res.primera_pasada) res.primera_pasada = r.datetime_utc;
      if (msUtc(r.datetime_utc) < desde) continue;
      const { estado } = clasificar(r, volcan);
      if (estado === "sin_deteccion") continue;
      if (res.ultima_deteccion === null || r.datetime_utc > res.ultima_deteccion) res.ultima_deteccion = r.datetime_utc;
      if (estado === "cumbre") res.n_cumbre++;
      else if (estado === "lejos") res.n_lejos++;
      else res.n_sin_posicion++;
      res.vrp_max = Math.max(res.vrp_max, r.vrp_mw);
    }
    res.ultima_pasada = ultima;
    res.sin_pasadas_recientes = ultima === null || ahoraMs - msUtc(ultima) > HORAS_SIN_PASADA * 3600000;
    return res;
  }

  const api = { VOLCANES, RADIO_CUMBRE_KM, clasificar, focosCompartidos, contarFocos, resumenVolcan, msUtc };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else raiz.P34 = api;
})(typeof window !== "undefined" ? window : globalThis);
