// Pregunta 1: si decidirSombra estuviera rota (p.ej. pendiente sin tope), ¿lo vería? Si, cada caso lleva su esperado.
// Pregunta 2: si el instrumento estuviera muerto, el script termina con exit 1 si algún esperado no coincide.
const { decidirSombra } = require('D:/vrp-trabajo/temporales/s169_ver_vigilancia_r2/arbol/scripts/nrt_monitor_decision.js');
const H = 3.6e6;
const now = Date.parse('2026-11-04T18:30:00Z');
const run = (h, o) => Object.assign({ created_at: new Date(now - h * H).toISOString(), event: 'schedule', status: 'completed', conclusion: 'success' }, o || {});
const casos = [
  ['control: verde de 3 h', [run(3)], 'ok'],
  ['verde 25.9 h + hoy en curso -> ok antes que pendiente', [run(3, {status:'in_progress', conclusion:null}), run(25.9)], 'ok'],
  ['verde 27 h + hoy in_progress 3.2 h', [run(3.2, {status:'in_progress', conclusion:null}), run(27)], 'pendiente'],
  ['verde 27 h + hoy queued 5.99 h', [run(5.99, {status:'queued', conclusion:null}), run(27)], 'pendiente'],
  ['verde 27 h + hoy queued 6.0 h exacto', [run(6.0, {status:'queued', conclusion:null}), run(27)], 'alerta'],
  ['verde 27 h + hoy queued 6.01 h (colgada)', [run(6.01, {status:'queued', conclusion:null}), run(27)], 'alerta'],
  ['verde 27 h + hoy in_progress 20 h (colgada)', [run(20, {status:'in_progress', conclusion:null}), run(27)], 'alerta'],
  ['verde 27 h + hoy waiting 1 h', [run(1, {status:'waiting', conclusion:null}), run(27)], 'pendiente'],
  ['verde 27 h + hoy requested 1 h', [run(1, {status:'requested', conclusion:null}), run(27)], 'pendiente'],
  ['verde 27 h + hoy pending 1 h', [run(1, {status:'pending', conclusion:null}), run(27)], 'pendiente'],
  ['verde 27 h + hoy completed failure', [run(3, {conclusion:'failure'}), run(27)], 'alerta'],
  ['verde 27 h + hoy cancelled', [run(3, {conclusion:'cancelled'}), run(27)], 'alerta'],
  ['verde 27 h + dispatch in_progress 1 h (no schedule)', [run(1, {event:'workflow_dispatch', status:'in_progress', conclusion:null}), run(27)], 'alerta'],
  ['sin verdes + hoy in_progress', [run(2, {status:'in_progress', conclusion:null})], 'pendiente'],
  ['sin runs', [], 'alerta'],
  ['pendiente con created_at basura', [run(1, {status:'queued', conclusion:null, created_at:'basura'}), run(27)], 'alerta'],
  ['pendiente sin created_at', [run(1, {status:'queued', conclusion:null, created_at:undefined}), run(27)], 'alerta'],
  ['pendiente con created_at en el futuro (reloj)', [run(-2, {status:'queued', conclusion:null}), run(27)], 'pendiente'],
  ['dos pendientes, una vieja una nueva', [run(2, {status:'queued', conclusion:null}), run(9, {status:'in_progress', conclusion:null}), run(27)], 'pendiente'],
  ['antes de desde', null, 'inactivo'],
];
let mal = 0;
for (const [n, runs, esp] of casos) {
  const d = n === 'antes de desde' ? decidirSombra([], Date.parse('2026-11-03T14:59:59Z')) : decidirSombra(runs, now);
  const ok = d.accion === esp; if (!ok) mal++;
  console.log((ok ? 'OK   ' : 'MAL  ') + n + ' -> ' + d.accion + ' (esperado ' + esp + ')');
}
console.log('FALLAN', mal, 'de', casos.length);
process.exit(mal ? 1 : 0);
