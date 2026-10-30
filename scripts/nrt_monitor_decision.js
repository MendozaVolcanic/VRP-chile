// S150 (auditoria S150, A-2). Decision del monitor del NRT, como funcion pura para poder probarla con node
// (tests/test_nrt_monitor_decision_s150.py) y llamarla desde .github/workflows/nrt-monitor.yml.
//
// POR QUE: el 2026-10-07 06:19 el monitor cerro el issue del apagon (#754) como "recuperado" con el NRT
// todavia caido. La API de GitHub le devolvio tres corridas verdes del 2026-09-03 y el monitor no miraba
// su fecha. Ademas filtraba solo corridas `schedule`, asi que no veria las que dispara un cron externo
// (workflow_dispatch). Una alerta que se cierra sola en falso es peor que no tener alerta: el operador
// cree que el sistema volvio.
//
// Reglas: (1) se cuentan todas las corridas completadas, de cualquier evento; (2) se ordenan por fecha y
// se usan las tres mas nuevas, sin confiar en el orden de la API; (3) si la mas nueva tiene mas de
// `maxHoras` horas, la respuesta de la API no describe el presente: SIN DATO, ni se alerta ni se cierra.
// La antiguedad del DATO publicado la vigila aparte nrt-healthcheck.yml.

function decidir(runs, ahoraMs, maxHoras) {
  const completas = (runs || [])
    .filter((r) => r && r.created_at && r.conclusion)
    .slice()
    .sort((a, b) => Date.parse(b.created_at) - Date.parse(a.created_at));
  const usadas = completas.slice(0, 3);
  if (usadas.length < 3) {
    return { accion: 'sin_dato', motivo: `menos de 3 corridas completadas (${usadas.length})`, usadas };
  }
  const edadHoras = (ahoraMs - Date.parse(usadas[0].created_at)) / 3.6e6;
  if (edadHoras > maxHoras) {
    return {
      accion: 'sin_dato',
      motivo: `la corrida mas nueva que entrego la API es vieja (${edadHoras.toFixed(1)} h, tope ${maxHoras} h): ` +
        'no se puede decidir si el NRT esta sano',
      usadas,
    };
  }
  const fallas = usadas.filter((r) => r.conclusion === 'failure' || r.conclusion === 'timed_out').length;
  if (fallas === 3) return { accion: 'alerta', motivo: '3 de 3 corridas recientes fallaron', usadas };
  if (fallas === 0) return { accion: 'recuperado', motivo: '3 de 3 corridas recientes en verde', usadas };
  return { accion: 'nada', motivo: `${fallas} de 3 corridas recientes fallaron`, usadas };
}

// S169 (P3-09 de experiments/_s169/audit_patrones/f3/INFORME_F3.md, en loop/activo). Vigilancia de la sombra
// «codigo MIROVA» (.github/workflows/sombra-codigo-mirova.yml, cron diario 15:00 UTC), probada en
// tests/test_monitor_sombra_s169.py y llamada desde nrt-monitor.yml.
//
// POR QUE: nadie miraba ese workflow. Un job rojo dejaba una X en Actions y un cron que no llega (workflow
// desactivado, evento `schedule` perdido como el 2026-08-27) no deja nada; sobre esas noches se decide si la via
// pasa a produccion. La regla es de AUSENCIA, no de fallas seguidas: desde la primera corrida con datos
// (2026-11-03 15:00 UTC, scripts/ventana_sombra.py), alerta si no hay una corrida PROGRAMADA terminada en verde en
// las ultimas `maxHoras` (26: el cron es diario y el monitor pasa cada 6 h, asi que una corrida de las 15:00 que
// falla se ve en el chequeo de las 18:30). Solo cuenta `schedule`: un despacho a mano (medir, un solo volcan) no
// prueba que la corrida diaria completa salio. Si algun dia se le pone un disparador externo a la sombra, esta
// regla dara una alerta visible, no un verde falso.
const SOMBRA_DESDE = '2026-11-03T15:00:00Z';

function decidirSombra(runs, ahoraMs, desde = SOMBRA_DESDE, maxHoras = 26) {
  if (ahoraMs < Date.parse(desde)) {
    return { accion: 'inactivo', motivo: `la sombra mide desde ${desde}`, ultima_verde: null };
  }
  const verdes = (runs || [])
    .filter((r) => r && r.created_at && r.event === 'schedule' && r.status === 'completed' &&
      r.conclusion === 'success')
    .slice()
    .sort((a, b) => Date.parse(b.created_at) - Date.parse(a.created_at));
  const ultima = verdes[0] || null;
  if (!ultima) {
    return { accion: 'alerta', motivo: 'ninguna corrida programada verde en lo que entrego la API', ultima_verde: null };
  }
  const edadHoras = (ahoraMs - Date.parse(ultima.created_at)) / 3.6e6;
  if (edadHoras > maxHoras) {
    return {
      accion: 'alerta',
      motivo: `la ultima corrida programada verde es del ${ultima.created_at} (tope ${maxHoras} h)`,
      ultima_verde: ultima,
    };
  }
  return { accion: 'ok', motivo: `corrida programada verde del ${ultima.created_at}`, ultima_verde: ultima };
}

module.exports = { decidir, decidirSombra, SOMBRA_DESDE };
