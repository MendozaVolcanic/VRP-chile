// crater_no_medido.js (S194, hallazgos C1-102 y C1-V202 de la auditoría Codex, ronda 2). Marca de sólo display
// «cráter no medido».
//
// POR QUÉ. A veces el infrarrojo medio (MIR, cerca de 4 µm, la banda que ve el calor) llega sin dato en uno o más
// píxeles sobre el cráter: una línea de barrido perdida o un píxel con calibración fallida en VIIRS (Missing_EV,
// Cal_Fail), o las dos bandas MIR saturadas en MODIS. La vía «código MIROVA» rellena la grilla con los vecinos antes de
// buscar anomalías, y los vecinos son más fríos: si el foco caía en el hueco, la pasada sale «sin anomalía» (foco
// aislado) o con una potencia que es sólo una parte de la real (foco con vecinos tibios: 11,5 MW en vez de 464 en el
// gránulo sintético del verificador, D:\codex-vrp\_salida\ronda2\cierre1_verificacion\instrumentos\b_psf_publica_salida.txt).
// Para el operador, «no se pudo medir el cráter» y «el cráter está frío» son cosas distintas. La vía ya lo anota en el
// record (diag_codigo_mirova, #1060 y #1077, ficha v1.47 y v1.61); hasta aquí el tablero no lo leía.
//
// CRITERIO (el mismo que experiments/_s194_mir_perdido/medir_mir_perdido.py, que exige igualdad record por record):
//   - px_mir_hueco_crater > 0: píxeles a menos de dos celdas de la grilla del cráter con la MIR no finita por una causa
//     que NO es el relleno bow-tie. Es el campo que el pipeline deja para esto («son lo que debe leer el paso B, no el
//     total», mirova_v750_codigo.py, dato_faltante_crater).
//   - crater_sin_posicion: el barrido que cruza el cráter llegó sin latitud ni longitud (la regla «cráter sin dato» de
//     la guardia K).
//   - px_saturados_crater > 0 (sólo VIIRS, que trae el bit): la MIR llegó con valor, pero en el tope de la banda; la
//     potencia de esos píxeles es un mínimo (Codex F1V-101 y F4-104, «subestimación sin marca, no cero»). No es «no
//     medido», así que lleva otro texto.
// NO se marca:
//   - el relleno bow-tie de VIIRS (px_bowtie_crater): el borde de cada barrido repite el suelo que ya midió el barrido
//     vecino y VIIRS lo descarta a bordo; no se pierde información (ficha v1.61: los 105 píxeles del 2026-11-20 eran
//     todos relleno). Medido aquí: en los records con las marcas separadas, todo px_mir_invalido_crater > 0 es bow-tie.
//   - px_mir_invalido_crater solo (records procesados entre el 2026-11-20 y el 2026-11-22, antes de #1077): mezcla
//     bow-tie y hueco y no se pueden separar; marcarlos pondría «cráter no medido» en pasadas que casi seguro sí lo
//     midieron.
//   - px_tir_hueco_crater: perder sólo la TIR tiene otro efecto (S191, tir_perdida) y no hay texto verificado para él.
// Los records anteriores a #1060 (2026-11-19) no traen ninguna de estas claves: no se marcan, y eso no dice que el
// cráter se haya medido (SIN DATO). Esta marca no cambia la potencia publicada, ni el nivel, ni la clase, ni la
// frescura: sólo avisa.
//
// UN SOLO LUGAR para las tres vistas (A102), como cumbre.js. Prueba: tests/test_tablero_crater_no_medido_s194.py
(function (raiz) {
  "use strict";

  const COLOR = "#ffab40";
  const SIMBOLO = "⊘";

  function entero(x) { return (typeof x === "number" && Number.isFinite(x) && x > 0) ? Math.round(x) : 0; }
  function plural(n, s, p) { return n + " " + (n === 1 ? s : p); }

  // {nMir, nSat, sinPosicion} si el record trae alguna marca de cráter sin medir entero; null si no.
  function craterNoMedido(r) {
    const d = r && r.diag_codigo_mirova;
    if (!d || typeof d !== "object") return null;
    const nMir = entero(d.px_mir_hueco_crater);
    const nSat = entero(d.px_saturados_crater);
    const sinPosicion = d.crater_sin_posicion === true;
    return (nMir || nSat || sinPosicion) ? { nMir, nSat, sinPosicion } : null;
  }

  // Texto corto: «cráter no medido: MIR sin dato en 2 píxeles».
  function textoCrater(m) {
    if (!m) return "";
    const partes = [];
    if (m.nMir) partes.push("MIR sin dato en " + plural(m.nMir, "píxel", "píxeles"));
    if (m.sinPosicion) partes.push("barrido sin posición sobre el cráter");
    const t = partes.length ? "cráter no medido: " + partes.join(", ") : "";
    const s = m.nSat ? "MIR saturada en " + plural(m.nSat, "píxel", "píxeles") + " del cráter: la potencia puede ser mayor" : "";
    return [t, s].filter(Boolean).join("; ");
  }

  // Explicación para el operador (title).
  function tituloCrater(m) {
    if (!m) return "";
    const t = [];
    if (m.nMir) t.push((m.nMir === 1 ? "1 píxel sobre el cráter llegó" : m.nMir + " píxeles sobre el cráter llegaron") +
      " sin dato en el infrarrojo medio (MIR, cerca de 4 µm, la banda que ve el calor): en VIIRS, una línea de barrido " +
      "perdida o un píxel con calibración fallida; en MODIS, las dos bandas MIR saturadas. Antes de buscar anomalías la " +
      "grilla se rellena con los vecinos, que son más fríos: si el foco estaba en ese hueco, la pasada sale «sin " +
      "anomalía» o con una potencia que es sólo una parte de la real. No se pudo medir el cráter, que no es lo mismo que " +
      "un cráter frío.");
    if (m.sinPosicion) t.push("El barrido que cruza el cráter llegó sin latitud ni longitud (el píxel con posición más " +
      "cercano quedó en el borde del gránulo o junto a píxeles sin posición): la pasada no vio el cráter entero.");
    if (m.nSat) t.push("El sensor marcó " + (m.nSat === 1 ? "1 píxel" : m.nSat + " píxeles") + " del cráter como " +
      "saturados en el MIR: el calor superó el tope de la banda y el valor quedó recortado, así que la potencia de " +
      (m.nSat === 1 ? "ese píxel" : "esos píxeles") + " es un mínimo.");
    t.push("No se marca el relleno bow-tie del borde del barrido de VIIRS, que no pierde dato (ese suelo lo midió el " +
      "barrido vecino). Esta marca no cambia la potencia publicada, ni el nivel, ni la clase: sólo avisa.");
    return t.join(" ");
  }

  // La pasada más reciente desde `desdeMs` con la marca que pase el filtro de la vista. {rec, m, t} o null. Una escena
  // que la vía no midió (motivo_vacio) no es pasada (S183) y ya se rotula aparte: no entra. La usan las tarjetas de index
  // y mosaico.
  function ultimaPasadaNoMedida(records, desdeMs, filtro, parseMs) {
    let best = null;
    for (const r of records || []) {
      const t = parseMs(r.datetime_utc);
      if (!(t >= desdeMs)) continue;
      if (r.diag_codigo_mirova && r.diag_codigo_mirova.motivo_vacio) continue;
      if (filtro && !filtro(r)) continue;
      const m = craterNoMedido(r);
      if (!m) continue;
      if (!best || t > best.t) best = { rec: r, m, t };
    }
    return best;
  }

  // R3F5-101 (auditoría Codex ronda 3, S198). La marca llegaba a la tabla, el popup, las tarjetas de 48 h y el conteo
  // del diario, pero no a los gráficos: la evolución de index dibujaba la pasada con el cráter no medido como «se midió,
  // nada» (y su recuadro decía «sin anomalía»), el minigráfico de mosaico la contaba como día observado y el gráfico del
  // diario no la mostraba. Pasada la ventana de 48 h, el operador ya no tenía cómo distinguirla de un cráter frío.
  // esNoMedido: la pasada no midió el cráter entero (hueco de MIR o barrido sin posición). La saturación sola no es «no
  // medido» (sí se midió, con un valor que es un mínimo): se avisa con su propio texto.
  function esNoMedido(m) { return !!(m && (m.nMir || m.sinPosicion)); }

  // Marcas para los gráficos por día o por pasada: [{t, sat, noMedido, m}] de los records marcados que pasan el filtro
  // de la vista. Como ultimaPasadaNoMedida, salta la escena que la vía no midió (motivo_vacio): ya se rotula aparte.
  function marcasGrafico(records, filtro, parseMs) {
    const out = [];
    for (const r of records || []) {
      if (r && r.diag_codigo_mirova && r.diag_codigo_mirova.motivo_vacio) continue;
      if (filtro && !filtro(r)) continue;
      const m = craterNoMedido(r);
      if (!m) continue;
      const t = parseMs(r.datetime_utc);
      if (!Number.isFinite(t)) continue;
      out.push({ t, noMedido: esNoMedido(m), sat: m.nSat > 0, m });
    }
    return out.sort((a, b) => a.t - b.t);
  }

  // Plugin de Chart.js que dibuja, arriba del área del gráfico, una raya naranja por marca: llena si la pasada no midió
  // el cráter, hueca si sólo la MIR saturó (la potencia es un mínimo). Opciones en options.plugins.craterNoMedido:
  // {marcas: [{x, noMedido, sat}]}, con x en las unidades del eje (Date, milisegundos o el texto del día que usa la
  // vista); se convierte con el parse del propio eje para que la raya caiga donde cae la barra.
  const plugin = {
    id: "craterNoMedido",
    afterDatasetsDraw(chart, args, o) {
      const a = chart.chartArea, x = chart.scales && chart.scales.x;
      if (!a || !x || !o || !o.marcas || !o.marcas.length) return;
      const ctx = chart.ctx; ctx.save();
      ctx.strokeStyle = COLOR; ctx.fillStyle = COLOR; ctx.lineWidth = 1;
      for (const mk of o.marcas) {
        const v = typeof x.parse === "function" ? x.parse(mk.x) : mk.x;
        if (v == null || !Number.isFinite(+v)) continue;
        const px = x.getPixelForValue(+v);
        if (!(px >= a.left && px <= a.right)) continue;
        if (mk.noMedido) ctx.fillRect(px - 1.5, a.top, 3, 7);
        else ctx.strokeRect(px - 1.5, a.top + 0.5, 3, 6);
      }
      ctx.restore();
    },
  };

  // R3F5-V101: un fondo de 0 K es la señal de «fondo no estimado» que dejan algunos records (13 de los Tier A, de
  // 2025-05 a 2026-04), no una medición: la tabla de index lo mostraba como -273,1 °C y la tarjeta habría leído un ΔT de
  // 259 a 279 K como «material caliente expuesto». Devuelve el fondo en kelvin o null si no hay fondo medido. No se
  // inventa un piso físico: sólo se descarta lo que no puede ser una temperatura (no finito, cero o negativo).
  function fondoK(r) {
    const k = r ? r.t_bg_k : null;
    return (typeof k === "number" && Number.isFinite(k) && k > 0) ? k : null;
  }

  // R3F3-V101 (auditoría Codex ronda 3, S199): potencia con alertados sin fondo estimado. La potencia de una pasada suma,
  // sobre los alertados, el exceso de radiancia sobre el fondo, que se interpola desde los vecinos no alertados. Si un
  // alertado queda junto a un hueco de datos, el halo que se saca alrededor de los alertados se come los vecinos útiles y
  // su fondo no se puede estimar; en VIIRS la vía sigue al .m de MIROVA y lo suma con fondo 0: la potencia de ese píxel es
  // su radiancia entera, posiblemente inflada (D36, «Fondo no estimable»; en MODIS, si ninguno tiene fondo, la escena ya
  // es no medida con motivo_vacio «fondo_no_estimado» y no entra aquí). El record lo cuenta en alertados_sin_fondo (desde
  // S192). Los records anteriores no traen la clave: en ellos L_bk = 0 con alertados dice que NINGUNO tuvo fondo (L_bk
  // suma sólo los fondos que existen, np.nansum en vrp_mirova) y se cuentan todos; si sólo una parte quedó sin fondo, el
  // record viejo no lo dice (SIN DATO, no se marca). Medición y criterio idéntico en
  // experiments/_s199_r3f3_v101/medir_sin_fondo.py. Prueba: tests/test_tablero_fondo_no_estimado_r3f3.py
  // {n, total, inferido} si la potencia suma alertados sin fondo; null si no. total es null si el record no lo trae.
  function fondoNoEstimado(r) {
    const d = r && r.diag_codigo_mirova;
    if (!d || typeof d !== "object" || d.motivo_vacio) return null;
    const total = entero(r.n_anomalous_pixels);
    const conClave = Object.prototype.hasOwnProperty.call(d, "alertados_sin_fondo");
    const n = conClave ? entero(d.alertados_sin_fondo)
            : (r.via_codigo_mirova === true && total > 0 && d.L_bk === 0 ? total : 0);
    return n ? { n, total: total >= n ? total : null, inferido: !conClave } : null;
  }

  // Texto corto: «fondo no estimado en 2 de 5 alertados: la potencia puede estar sobreestimada».
  function textoFondo(f) {
    if (!f) return "";
    return "fondo no estimado en " + (f.total ? f.n + " de " + plural(f.total, "alertado", "alertados")
                                              : plural(f.n, "alertado", "alertados")) +
      ": la potencia puede estar sobreestimada";
  }

  // Explicación para el operador (title).
  function tituloFondo(f) {
    if (!f) return "";
    const uno = f.n === 1;
    return "La potencia de la pasada suma, sobre los píxeles alertados, el exceso de radiancia sobre el fondo, que se " +
      "estima con los vecinos no alertados. " + (uno ? "1 píxel alertado quedó" : f.n + " píxeles alertados quedaron") +
      " junto a un hueco de datos, sin vecinos útiles, y su fondo no se pudo estimar. Como en el código de MIROVA, " +
      (uno ? "ese píxel se suma" : "esos píxeles se suman") + " con fondo cero: entra su radiancia entera, no sólo el " +
      "exceso, así que la potencia publicada puede ser mayor que la real." +
      (f.inferido ? " Record anterior a la marca de fondo: se sabe porque la suma de los fondos de la pasada es cero, lo que " +
        "dice que ningún alertado tuvo fondo." : "") +
      " Esta marca no cambia la potencia publicada, ni el nivel, ni la clase: sólo avisa.";
  }

  const api = { COLOR, SIMBOLO, craterNoMedido, textoCrater, tituloCrater, ultimaPasadaNoMedida, esNoMedido, marcasGrafico,
                plugin, fondoK, fondoNoEstimado, textoFondo, tituloFondo };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else raiz.CraterNoMedido = api;
})(typeof window !== "undefined" ? window : this);
