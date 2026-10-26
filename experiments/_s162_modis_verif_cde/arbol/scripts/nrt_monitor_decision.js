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

module.exports = { decidir };
