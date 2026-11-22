// diurno.js (S193): qué pasada NUESTRA es diurna, y cómo se marca en las tres vistas del tablero (index, diario, mosaico).
//
// POR QUÉ. De día el canal de infrarrojo medio (3,7 a 4 µm) suma a la emisión térmica la luz del sol reflejada: una
// nube, un salar o una ladera nevada pueden levantar píxeles sin nada caliente debajo. Hasta S193 la réplica sólo
// procesaba pasadas nocturnas, y el tablero lo daba por hecho en la frescura del monitoreo, en las series diarias y en
// los textos de ayuda. El A/B diurno sobre la vía (issue #813, PR #1084) terminó con la decisión de Nicolás de encender
// el día sólo en MODIS (`enable_daytime_modis` en el perfil `mirova_equivalent`; VIIRS sigue sólo de noche). Desde ese
// cambio de perfil el NRT escribe records MODIS diurnos en el mismo JSON que los nocturnos, y el operador no puede
// confundir uno con otro: el de día puede ser reflejo. Este módulo dice cuál es cuál; cada vista
// decide qué hace con eso (las series nocturnas y la frescura siguen siendo nocturnas; lo diurno se dibuja aparte con
// un sol, la misma convención que S151 usa para las alertas diurnas de MIROVA).
//
// UNA SOLA DEFINICIÓN, LA QUE DECIDE QUÉ SE PUBLICA. Una pasada es diurna si el Sol está sobre el horizonte del volcán
// a la hora del record: elevación solar > 0, con la misma fórmula que `pipeline/store.py::_solar_elevation`, la
// compuerta que guarda o rechaza un record diurno (y la de `pipeline/diurno.py::pasada_es_diurna` y
// `process_modis._scene_is_day`). Es exactamente lo que el cambio de perfil agrega: con la rama diurna apagada store
// rechaza todo record con elevación > 0, así que con los datos de hoy ningún record queda marcado y el tablero se ve
// igual que antes. NO se usa `solar_zenith_deg` del record (cenit del sol en la geometría del gránulo; es el que usa el
// detector de la vía para su `dayflag`, `diag_codigo_mirova.dayflag`): cerca del crepúsculo no coincide con la
// compuerta. En main del 2026-11-21 hay 5 records MODIS con `solar_zenith_deg` entre 89,0 y 89,96 (dayflag 1, todos con
// 0 MW: Chaitén 2026-06-09 y 2026-07-17, Llaima, Villarrica y Cordón Caulle 2026-07-25) que store guardó como nocturnos
// porque en el volcán el Sol estaba bajo el horizonte; son parte del ritmo nocturno de siempre y con el cenit del record
// se habrían marcado de día. Prueba: tests/test_tablero_diurno_s193.py (compara con la función de Python sobre una
// grilla de fechas y lugares, y fija esos 5 casos).
//
// Sólo marca y dibuja: no cambia ninguna detección, ningún valor publicado ni el criterio de publicación.
(function (raiz) {
  "use strict";

  const TEXTO = "pasada diurna: puede incluir reflejo solar";
  const RAYOS = "#ffc400";   // el dorado de los rayos del sol de MIROVA_DIA_RAYOS (S151), para que se lea igual
  const SIMBOLO = "☀";  // ☀

  // "AAAA-MM-DD HH:MM" en UTC, el formato exacto que store.py lee con strptime("%Y-%m-%d %H:%M"). Otro formato: null
  // (store tampoco lo puede leer y pasada_es_diurna lo trata como noche).
  function partesFecha(s) {
    const m = /^(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2})$/.exec(String(s == null ? "" : s));
    if (!m) return null;
    const y = +m[1], mo = +m[2], d = +m[3], h = +m[4], mi = +m[5];
    const t = Date.UTC(y, mo - 1, d);
    const f = new Date(t);
    if (f.getUTCFullYear() !== y || f.getUTCMonth() !== mo - 1 || f.getUTCDate() !== d || h > 23 || mi > 59) return null;
    const diaDelAnio = Math.round((t - Date.UTC(y, 0, 1)) / 86400000) + 1;   // tm_yday de Python (1 = 1 de enero)
    return { diaDelAnio, horaUtc: h + mi / 60 };
  }

  // Port literal de pipeline/store.py::_solar_elevation (grados; negativo = noche). Mismas constantes y mismo orden.
  function elevacionSolar(lat, lon, fechaUtc) {
    if (!Number.isFinite(lat) || !Number.isFinite(lon)) return null;
    const p = partesFecha(fechaUtc);
    if (!p) return null;
    const gamma = 2 * Math.PI * (p.diaDelAnio - 1) / 365.0;
    const decl = (0.006918 - 0.399912 * Math.cos(gamma) + 0.070257 * Math.sin(gamma)
                  - 0.006758 * Math.cos(2 * gamma) + 0.000907 * Math.sin(2 * gamma));
    const horaSolar = p.horaUtc + lon / 15.0;
    const anguloHorario = (15.0 * (horaSolar - 12.0)) * Math.PI / 180;
    const latR = lat * Math.PI / 180;
    const senElev = (Math.sin(latR) * Math.sin(decl)
                     + Math.cos(latR) * Math.cos(decl) * Math.cos(anguloHorario));
    return Math.asin(Math.max(-1.0, Math.min(1.0, senElev))) * 180 / Math.PI;
  }

  // Misma regla que pasada_es_diurna: elevación > 0. Sin fecha legible o sin coordenadas: noche (conservador).
  function esDiurna(fechaUtc, lat, lon) {
    const e = elevacionSolar(lat, lon, fechaUtc);
    return e != null && e > 0;
  }

  // Marca transitoria `_diurna` en cada record (como `_mirova_confirmed`: empieza con «_», no se persiste). Las vistas
  // la leen sin recalcular, y las funciones que las pruebas extraen sueltas (lastEventTime, monitoringFreshness...)
  // sólo miran la propiedad, sin depender de este módulo. Devuelve cuántas quedaron diurnas.
  function marcar(records, lat, lon) {
    let n = 0;
    for (const r of records || []) {
      if (!r) continue;
      r._diurna = esDiurna(r.datetime_utc, lat, lon);
      if (r._diurna) n++;
    }
    return n;
  }

  // Sol de una pasada NUESTRA: los mismos rayos dorados que el de MIROVA, con un CUADRADO del color del sensor al centro
  // en vez del disco, para que nuestro sol y el de MIROVA no se confundan en el mismo gráfico.
  const _iconos = new Map();
  function iconoSol(color) {
    if (_iconos.has(color)) return _iconos.get(color);
    if (typeof document === "undefined") return "rect";
    const n = 20, c = n / 2, cv = document.createElement("canvas");
    cv.width = n; cv.height = n;
    const g = cv.getContext("2d");
    g.strokeStyle = RAYOS; g.lineWidth = 1.6; g.lineCap = "round";
    for (let i = 0; i < 8; i++) {
      const a = i * Math.PI / 4;
      g.beginPath(); g.moveTo(c + 6 * Math.cos(a), c + 6 * Math.sin(a));
      g.lineTo(c + 9.2 * Math.cos(a), c + 9.2 * Math.sin(a)); g.stroke();
    }
    g.fillStyle = color; g.fillRect(c - 3.6, c - 3.6, 7.2, 7.2);
    g.lineWidth = 1; g.strokeStyle = "#ffffff"; g.strokeRect(c - 3.6, c - 3.6, 7.2, 7.2);
    _iconos.set(color, cv);
    return cv;
  }
  function estiloPunto(ctx) { return ctx && ctx.raw ? iconoSol(ctx.raw.color) : "rect"; }

  // Un punto por día y sensor con el máximo DIURNO (el mismo número que daría la barra nocturna de ese día).
  // valor(r) -> MW; infoDe(r) -> { clave, color, label } o null para no dibujarlo. Los puntos llevan `dia: true`
  // para que las líneas del tooltip del sol (mirovaLineasDia de cada vista) los describan igual que a los de MIROVA.
  function puntosDiarios(records, valor, infoDe) {
    const m = new Map();
    for (const r of records || []) {
      if (!r || r._diurna !== true) continue;
      const d = String(r.datetime_utc || "").slice(0, 10); if (!d) continue;
      const info = infoDe(r); if (!info) continue;
      const v = valor(r);
      if (!(v > 0)) continue;
      const k = d + "|" + info.clave;
      if (!m.has(k) || v > m.get(k).y) {
        m.set(k, { x: d, y: v, dt: r.datetime_utc, sensor: info.label, color: info.color, dia: true, propia: true });
      }
    }
    return [...m.values()].sort((a, b) => (a.x < b.x ? -1 : a.x > b.x ? 1 : 0));
  }

  // Dataset de Chart.js para esos puntos. `mirovaDia: true` no dice que sea de MIROVA: es la marca con que el modo de
  // interacción «indexMasSol» de cada vista reconoce una serie de soles (sólo muestra su tooltip con el cursor encima,
  // porque el modo «index» los alinea por posición y no por fecha).
  function dataset(puntos) {
    return {
      label: SIMBOLO + " VRP Chile pasada diurna", data: puntos, type: "line", showLine: false, order: 0,
      borderColor: RAYOS, backgroundColor: RAYOS, pointRadius: 8, pointHoverRadius: 9,
      mirovaDia: true, diurnaPropia: true, pointStyle: estiloPunto,
    };
  }

  const DiurnoTablero = { TEXTO, RAYOS, SIMBOLO, elevacionSolar, esDiurna, marcar, iconoSol, estiloPunto,
                          puntosDiarios, dataset };

  if (typeof module !== "undefined" && module.exports) module.exports = DiurnoTablero;
  else raiz.DiurnoTablero = DiurnoTablero;
})(typeof window !== "undefined" ? window : this);
