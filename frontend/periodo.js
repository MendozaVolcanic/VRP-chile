// periodo.js (S153): el período que muestran las tres vistas del tablero (index, diario, mosaico).
//
// POR QUÉ: el geólogo de turno pregunta por una noche o un rango concreto («¿qué pasó la noche del 1 de octubre en
// Chillán?»), y hasta S153 el tablero sólo ofrecía ventanas móviles desde «ahora». Toda la lógica de fechas vive acá,
// en un solo lugar, porque ya falló una vez por zona horaria (PR #250). Sólo funciones nuevas: los ayudantes del
// criterio de publicación (isValidDetection, mirovaEqVrp, ...) siguen en cada vista, donde los leen los guards y
// scripts/banco_paridad.py.
//
// LA UNIDAD ES LA NOCHE, EN UTC: una noche chilena (21 a 06 local, UTC-3 o UTC-4) cae entera dentro de una sola fecha
// UTC, la de la mañana (auditoría S153: 11.571 de 11.584 records de 100 días entre 00 y 08 UTC). Por eso un rango se
// pide en fechas UTC y se filtra [desde 00:00 UTC, hasta 23:59:59 UTC].
//
// Un período es {dias: N} (ventana móvil desde ahora; 0 = todo) o {desde: "AAAA-MM-DD", hasta: "AAAA-MM-DD"}.
(function (raiz) {
  "use strict";
  const DIA_MS = 86400000;
  const MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
  // La ventana liviana que se publica (scripts/build_recent_json.py, RECENT_DAYS = 100) menos el margen del corte al
  // desplegar: dentro de 90 días no hace falta bajar la historia completa.
  const DIAS_LIVIANOS = 90;

  function fechaValida(s) {
    if (typeof s !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(s)) return null;
    const t = Date.parse(s + "T00:00:00Z");
    if (isNaN(t)) return null;
    return new Date(t).toISOString().slice(0, 10) === s ? s : null;   // descarta 2026-02-30
  }

  // Igual que parseUtcMs de las vistas: un "AAAA-MM-DD HH:MM" sin zona se lee como UTC, nunca como hora local.
  function parseUtcMs(s) {
    if (s == null) return NaN;
    let str = String(s).replace(" ", "T");
    if (!/[zZ]$|[+-]\d\d:?\d\d$/.test(str)) str += "Z";
    return new Date(str).getTime();
  }

  function msDeFecha(f) { return Date.parse(f + "T00:00:00Z"); }
  function fechaDeMs(ms) { return new Date(ms).toISOString().slice(0, 10); }
  function sumarDias(f, n) { return fechaDeMs(msDeFecha(f) + n * DIA_MS); }

  function ordenar(desde, hasta) {
    return desde <= hasta ? { desde, hasta } : { desde: hasta, hasta: desde };
  }

  function desdeURL(search, diasPorDefecto) {
    const q = new URLSearchParams(search || "");
    const desde = fechaValida(q.get("desde"));
    if (desde) {
      const hasta = fechaValida(q.get("hasta")) || desde;
      return ordenar(desde, hasta);
    }
    const d = q.get("dias");
    if (d != null && /^\d+$/.test(d)) return { dias: parseInt(d, 10) };
    return { dias: diasPorDefecto };
  }

  function esRango(p) { return p != null && p.desde != null; }

  function esPorDefecto(p, diasPorDefecto) { return !esRango(p) && p.dias === diasPorDefecto; }

  // Devuelve el search con el período escrito, conservando el resto (por ejemplo ?volcano=). El período por defecto
  // no se escribe, así una URL sin tocar queda igual que antes de S153.
  function aURL(p, search, diasPorDefecto) {
    const q = new URLSearchParams(search || "");
    q.delete("dias"); q.delete("desde"); q.delete("hasta");
    if (esRango(p)) { q.set("desde", p.desde); q.set("hasta", p.hasta); }
    else if (!esPorDefecto(p, diasPorDefecto)) q.set("dias", String(p.dias));
    const s = q.toString();
    return s ? "?" + s : "";
  }

  // [t0, t1] en ms, extremos incluidos.
  function intervalo(p, ahoraMs) {
    if (esRango(p)) return [msDeFecha(p.desde), msDeFecha(p.hasta) + DIA_MS - 1];
    if (!p.dias) return [-Infinity, Infinity];
    return [ahoraMs - p.dias * DIA_MS, Infinity];
  }

  function filtrar(records, p, ahoraMs, campo) {
    const [t0, t1] = intervalo(p, ahoraMs == null ? Date.now() : ahoraMs);
    const c = campo || "datetime_utc";
    return (records || []).filter(r => { const t = parseUtcMs(r[c]); return t >= t0 && t <= t1; });
  }

  function necesitaHistoria(p, ahoraMs) {
    if (esRango(p)) return msDeFecha(p.desde) < (ahoraMs == null ? Date.now() : ahoraMs) - DIAS_LIVIANOS * DIA_MS;
    return p.dias === 0 || p.dias > DIAS_LIVIANOS;
  }

  function diaMes(f, conMesSiempre) {
    const [, m, d] = f.split("-").map(Number);
    return conMesSiempre ? d + " " + MESES[m - 1] : String(d);
  }

  function corto(f) { const [, m, d] = f.split("-").map(Number); return d + " " + MESES[m - 1]; }

  // «noche del 15 al 16 de oct en Chile»: la fecha UTC D trae la noche que empieza la tarde local del día D-1.
  function nocheChile(f) {
    const antes = sumarDias(f, -1);
    const mismoMes = antes.slice(0, 7) === f.slice(0, 7);
    const [, m] = f.split("-").map(Number);
    return mismoMes
      ? "noche del " + diaMes(antes) + " al " + diaMes(f) + " de " + MESES[m - 1] + " en Chile"
      : "noche del " + diaMes(antes, true).replace(" ", " de ") + " al " + diaMes(f, true).replace(" ", " de ") + " en Chile";
  }

  function rotulo(p) {
    if (esRango(p)) {
      const anio = p.hasta.slice(0, 4);
      if (p.desde === p.hasta) return corto(p.desde) + " " + anio + " UTC (" + nocheChile(p.desde) + ")";
      return corto(p.desde) + (p.desde.slice(0, 4) !== anio ? " " + p.desde.slice(0, 4) : "") + " a " + corto(p.hasta) + " " + anio + " UTC";
    }
    if (!p.dias) return "toda la historia";
    if (p.dias === 1) return "últimas 24 h";
    return "últimos " + p.dias + " días";
  }

  function rotuloCorto(p) {
    if (esRango(p)) return p.desde === p.hasta ? corto(p.desde) : corto(p.desde) + " a " + corto(p.hasta);
    if (!p.dias) return "todo";
    if (p.dias === 1) return "24 h";
    return p.dias + " d";
  }

  // Corre un rango n noches; una ventana móvil no se desplaza.
  function desplazar(p, n) {
    if (!esRango(p)) return p;
    return { desde: sumarDias(p.desde, n), hasta: sumarDias(p.hasta, n) };
  }

  // Fecha UTC de un punto del gráfico (Chart.js da el x como "AAAA-MM-DD" o como ms).
  function fechaDeX(x) {
    if (typeof x === "number" && isFinite(x)) return fechaDeMs(x);
    if (typeof x === "string") return fechaValida(x.slice(0, 10));
    return null;
  }

  function noche(f) { return { desde: f, hasta: f }; }

  const Periodo = { desdeURL, aURL, esRango, esPorDefecto, intervalo, filtrar, necesitaHistoria, rotulo,
                    rotuloCorto, desplazar, fechaDeX, noche, fechaValida, DIAS_LIVIANOS };
  if (typeof module !== "undefined" && module.exports) module.exports = Periodo;
  else raiz.Periodo = Periodo;
})(typeof window !== "undefined" ? window : this);
