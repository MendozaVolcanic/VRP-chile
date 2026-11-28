# Acta de cierre de la auditoría externa con Codex, ronda 6

**PROPUESTA, espera la aprobación de Nicolás Mendoza.** Escrita por la sesión S204 a partir del cierre informado de
Codex y su verificador Claude de contexto limpio. Las decisiones de la tabla «Acta» son propuestas hasta que Nicolás las
apruebe; al aprobarse, esta cabecera se reemplaza por la fecha y su frase textual.

## Por qué existe este documento

La ronda 6 (2026-11-27 y 2026-11-28) revisó dos cambios de S203 que el acta de la ronda 5
(`docs/ACTA_CIERRE_AUDITORIA_CODEX_RONDA5_2026-11-26.md`) no cubría: el respaldo de búsqueda por LANCE cuando el
catálogo CMR de NASA falla (#1143, código de producción; frente L) y la cadena del laboratorio del piso, calibrar, la
vara contra NHI y el exceso mínimo (#1142, #1144, #1145; frente N). Cada frente tuvo pase ciego de Codex, confrontación
con las rondas anteriores y un verificador Claude de contexto limpio; el cierre informado de Codex tuvo el suyo.
Como las actas anteriores: **cerrada con límites explícitos**, no «todo está bien».

## Qué se cerró y sobre qué

| Qué | Valor |
|---|---|
| Copias auditadas | main `7a9c1c658` (v1.121) para los frentes; `115abf7c3` (v1.124) para el cierre |
| Registro de hallazgos verificados | 507 filas (46 de la ronda 6, ninguna refutada), `D:\codex-vrp\_salida\ronda6\hallazgos_verificados.csv` (fuera del repo) |
| Veredictos | `D:\codex-vrp\_salida\ronda6\fl_r6_verificacion\`, `fn_r6_verificacion\`, `cierre_verificacion\` (`VEREDICTO.md`) |
| Resumen para Nicolás | `D:\codex-vrp\_salida\ronda6\RESUMEN_R6_PARA_NICOLAS.md` |
| Decisión de lanzarla | Nicolás, 2026-11-27 ~23:35 UTC: «Sí, lánzala» |

Los archivos de `D:\codex-vrp\` están fuera del repo a propósito. Si se pierden, esta acta y la ficha conservan lo
decidido, no la evidencia.

## Conteo del registro (filas de la ronda 6, gravedad del verificador)

| Frente | Gravedad 3 | Gravedad 2 | Gravedad 1 |
|---|---|---|---|
| L, respaldo LANCE | 3 | 9 | 9 |
| N, cadena del laboratorio | 2 | 5 | 6 |
| Cierre | 1 | 7 | 4 |

## Las gravedades 3 y su estado

| ID | Qué | Estado | Dónde |
|---|---|---|---|
| R6FL-108 | descargas desde nrt4 sin tiempo de espera | CORREGIDA | #1147 (v1.124); `pipeline/fetch.py` `_NASA_HOSTS`; prueba `tests/test_lance_respaldo_tiempo_s204.py` |
| R6FL-118 | LANCE lento se come el paso de 50 min | CORREGIDA | #1147; presupuesto en dos bolsas de `pipeline/lance_respaldo.py`; con 29 s por pedido el proceso baja de 49,6 a 17,0 min (verificador del cierre) |
| R6FL-V201 | nrt3 colgado y nrt4 sano: 30 s por consulta | CORREGIDA | #1147; el espejo que se cuelga pasa al final; de 52,8 a 5,3 min (verificador del cierre) |
| R6FN-102 | la vara carga MODIS de día de producción (cobertura desigual casi entera de ese artefacto) | CORREGIDA EN LA LECTURA; el NO CUMPLE se mantiene | #1148 (v1.122); el cargador de la vara sellada sigue igual |
| R6FN-V201 | la misma vara se invalidaría sola con fin desde el 2026-11-28 | CORREGIDA EN LA LECTURA | #1148; se arregla sólo si hay un segundo intento, con pre-registro nuevo |
| R6C-105 | CMR caído con 503 lentos pasa el paso de 50 min (y desde ~47 s por pedido el job de 80) | ABIERTA, anterior al respaldo (lo agrava #1143) | decisión 1 abajo |

Residuales de gravedad 2 que dejó #1147: R6C-108 (un vacío de nrt4 ocultaba a un nrt3 recuperado) y R6C-V201 (un corte
del presupuesto callado) van en #1151. Quedan R6C-102, R6C-103 y R6C-109 (decisión 2).

## Acta (propuestas)

| # | Decisión | Propuesta | Responsable, costo, límite y revisión |
|---|---|---|---|
| 1 | R6C-105 | (a) plazo total de red por proceso también para las búsquedas de CMR, con margen bajo los 50 min del paso, en un PR con plan, pruebas y verificador limpio | sesión del loop; un PR; mientras no entre, una caída lenta de CMR cuesta a lo más una corrida por volcán (la siguiente reprocesa la ventana); revisar si un log muestra un paso cortado por tiempo |
| 2 | R6C-102, R6C-103, R6C-109 | aceptarlos: ninguno quita lo que CMR entrega | revisar si un log muestra `LANCE_RESPALDO_SIN_RESPUESTA` por presupuesto agotado en una caída real |
| 3 | Cargador de la vara (R6FN-102, R6C-101) | no tocar la vara sellada; un segundo intento del laboratorio la arregla primero, con pre-registro nuevo | Nicolás decide si hay segundo intento |

## Qué obliga a repetir parte de esta ronda

| Cambio futuro | Repetir |
|---|---|
| Cambiar `pipeline/lance_respaldo.py` o la búsqueda de `pipeline/fetch.py` | frente L, escenarios de tiempo y de espejos |
| Cambiar el tope del paso o del job en `.github/workflows/nrt.yml` | la cuenta de minutos del cierre (R6C-105) |
| Un segundo intento del laboratorio | frente N completo, con la vara arreglada |
