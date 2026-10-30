// M3. decidirSombra (arbol 16d9e894d). Preguntas del instrumento: (1) si decidirSombra estuviera rota (siempre ok) el caso
// "sin corridas" daria ok: lo imprimimos como control; (2) si estuviera muerta (siempre alerta) el caso "verde reciente" lo delataria.
const { decidirSombra } = require("D:/vrp-trabajo/temporales/s169_ver_vigilancia/arbol/scripts/nrt_monitor_decision.js");
const r = (c, conc, ev = "schedule", st = "completed") => ({ created_at: c, conclusion: conc, event: ev, status: st, html_url: "u" });
const casos = [
  ["control: verde de hoy 15:03, chequeo 18:30", [r("2026-11-04T15:03:00Z", "success")], "2026-11-04T18:30:00Z"],
  ["control: sin corridas, 3-nov 18:30", [], "2026-11-03T18:30:00Z"],
  ["3-nov 12:30 (antes de 15:00)", [], "2026-11-03T12:30:00Z"],
  ["borde exacto 15:00:00Z sin corridas", [], "2026-11-03T15:00:00Z"],
  ["borde 14:59:59Z", [], "2026-11-03T14:59:59Z"],
  ["hoy en curso a las 18:30 (ayer verde 15:03), corrida de hoy 15:05 in_progress", [r("2026-11-05T15:05:00Z", null, "schedule", "in_progress"), r("2026-11-04T15:03:00Z", "success")], "2026-11-05T18:30:00Z"],
  ["ayer verde 14:50 (cron temprano), hoy en curso, 18:30 -> edad 27.7h", [r("2026-11-05T15:05:00Z", null, "schedule", "in_progress"), r("2026-11-04T14:50:00Z", "success")], "2026-11-05T18:30:00Z"],
  ["hoy 1 job rojo (run failure), 18:30", [r("2026-11-05T15:05:00Z", "failure"), r("2026-11-04T15:03:00Z", "success")], "2026-11-05T18:30:00Z"],
  ["hoy failure, chequeo 12:30 del dia siguiente (ayer verde es de hace 45 h)", [r("2026-11-05T15:05:00Z", "failure"), r("2026-11-04T15:03:00Z", "success")], "2026-11-06T12:30:00Z"],
  ["despacho manual verde de hoy (workflow_dispatch) con cron fallido", [r("2026-11-05T17:00:00Z", "success", "workflow_dispatch"), r("2026-11-05T15:05:00Z", "failure"), r("2026-11-04T15:03:00Z", "success")], "2026-11-06T00:30:00Z"],
  ["cron cancelado (cancelled) hoy", [r("2026-11-05T15:05:00Z", "cancelled"), r("2026-11-04T15:03:00Z", "success")], "2026-11-06T00:30:00Z"],
  ["API da 30 corridas viejas (todas manuales)", Array.from({ length: 30 }, (_, i) => r(`2026-11-0${1 + (i % 9)}T10:00:00Z`, "success", "workflow_dispatch")), "2026-11-10T18:30:00Z"],
];
for (const [n, runs, t] of casos) { const d = decidirSombra(runs, Date.parse(t)); console.log(`${d.accion.padEnd(8)} | ${n} | ${d.motivo}`); }
