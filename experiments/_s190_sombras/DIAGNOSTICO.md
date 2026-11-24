# S190: por qué fallan las dos sombras (issues #1027 y #1028)

Fecha: 2026-11-17. Corridas revisadas: las 8 últimas de `sombra-codigo-mirova.yml` (11 volcanes) y de `sombra-34.yml`
(34 volcanes), del 9 al 16 de noviembre, más el NRT de la misma hora del 16. Logs bajados por job con
`gh api repos/MendozaVolcanic/VRP-chile/actions/jobs/<id>/logs` a `D:\vrp-trabajo\temporales\s190_sombras\` y leídos
con grep (no se suben al repo).

## Respuesta corta

No hay una causa recurrente: cada día rojo tiene la suya. Tres ya estaban resueltas o fueron externas. El 16 de
noviembre, el que tiene abiertos los issues, la causa es una degradación pasajera de CMR (NASA) que nuestro código
convirtió en pérdida de datos y en rojo por dos defectos propios. Este PR arregla los dos.

| Día | Sombra | Jobs rojos | Causa | Estado |
|---|---|---|---|---|
| 9-nov | 11 | NdC, Copahue, Llaima | Corrida atrasada que cruzó la medianoche: juzgó el 10 sin la noche cerrada («catálogo de CMR vacío») | CONFIRMADO; arreglado en S178 (`e6d3700f0`) |
| 11-nov | 34 | 12 jobs | Paso «Guardar log»: `Failed to CreateArtifact ... "<!DOCTYPE"`, el servicio de artefactos de GitHub respondió HTML | CONFIRMADO; externo (GitHub), los datos se commitearon |
| 12 y 13-nov | 11 | Puyehue, Villarrica; Llaima | Runner en AWS us-west-2: earthaccess 0.17 baja por S3 y revienta con `FileExistsError` en cada descarga (161 errores), el paso llega al techo de 75 min | CONFIRMADO; arreglado en S182 (`c763f6c2d`, en main desde el 14-nov 19:34 UTC) |
| 13 y 14-nov | 34 | Lonquimay, OlcaParuma; Callaqui, Calbuco | El mismo `FileExistsError` (162 errores por job). La corrida del 14 arrancó 18:42 UTC sobre `778bca1`, antes del merge del arreglo | CONFIRMADO; arreglado en S182 |
| 16-nov | 11 | PlanchonPeteroa, NdC, Villarrica, Tupungatito, Isluga | ReadTimeout de CMR en la búsqueda por día, breaker al primero, y revisor que juzga un día sin noche cerrada | CONFIRMADO; arreglado en este PR |
| 16-nov | 34 | Putana, SanJose | ReadTimeout de CMR en la búsqueda por día, breaker al primero: VIIRS del 16 sin buscar | CONFIRMADO; arreglado en este PR (reintento) |

## El 16 de noviembre en detalle

**Lo que pasó en CMR (CONFIRMADO).** Entre las 23:50 y las 00:30 UTC, `cmr.earthdata.nasa.gov` respondió con
ReadTimeout sueltos (acepta la conexión y no contesta a tiempo) a los dos workflows y también al NRT de las 23:58
(run 43983769917: 72 líneas de error de búsqueda; el NRT de las 01:10 tuvo 0). Era NASA y era pasajero.

**Primer defecto: la búsqueda por día no reintenta (CONFIRMADO).** `pipeline/fetch.py` busca de dos maneras. La
búsqueda por ventana (S157) reintenta una vez a los 20 s: ese día tuvo 3 ReadTimeout y los 3 se curaron al
reintentar. La búsqueda por día (`search_granules`, la de los días que la ventana no cubre, los más recientes)
enciende el breaker de CMR al primer ReadTimeout (S116) y devuelve [] para todo lo que queda de esa fecha. Así se
perdieron el 16 entero de Tupungatito (los tres sensores), el VIIRS 750 y 375 del 16 de Putana y SanJose, y búsquedas
sueltas de Isluga y Villarrica. A64 dice que ReadTimeout se reintenta y ConnectTimeout no; la búsqueda por día no lo
cumplía. Que un reintento a los 20 s también habría curado esas búsquedas es SOSPECHA razonable (lo apoyan los 3 de 3
de la ventana, en la misma hora), no está medido.

**Segundo defecto: el revisor juzga búsquedas de un día que no juzga (CONFIRMADO).** El cron de las sombras se atrasa
de 5 a 10 h (la de los 11, programada a las 15:00 UTC, partió el 16 a las 23:39; la de los 34, programada a las 13:07,
a las 22:50). Los jobs que arrancan después de medianoche tienen `fin` = 17. `scripts/revisar_sombra.py` declara «la
noche no estaba cerrada, no se juzga» para el 17 (S178), pero la regla de cobertura (VV169-03) seguía mirando `fin` y
dejaba rojo por las búsquedas caídas del 17. PlanchonPeteroa y NevadosDeChillan quedaron rojos sólo por eso.

**Lo que NO fue (CONFIRMADO).**
- Choque de push: los 11 commits de la sombra entraron; Villarrica tuvo un rechazo `fetch first` y el reintento
  `pull --rebase` lo resolvió en el segundo intento. La línea «all push attempts failed» que aparece en el log es el
  texto del script impreso por GitHub al abrir el paso, no un mensaje emitido. El paso de commit no falló en ningún
  job de las 16 corridas. La regla de concurrencia (grupo propio más reintento, guard G4) se cumple.
- Reproceso de las tandas compitiendo por runners: entre las 22:30 y las 00:40 UTC del 16 no corrió
  `reproc-historia-via.yml`; corrían NRT, experimental-diario, la vigilancia y las dos sombras.
- Chequeo demasiado estricto en general: el rojo de Tupungatito, Putana y SanJose es verdadero (perdieron un día de
  datos). El revisor sólo se equivocaba con el día sin noche cerrada.

**SOSPECHA sin medir.** El atraso del cron amontona a la misma hora las dos sombras (4 + 8 jobs), el NRT (8) y
experimental-diario contra CMR. Que esa carga propia contribuya a los ReadTimeout no está probado; el NRT de las 01:10,
ya sin las sombras, salió limpio, lo que es compatible con las dos lecturas.

## Arreglo (este PR)

1. `pipeline/fetch.py::_buscar_dia_con_reintento`: un ReadTimeout de la búsqueda por día se reintenta una vez, a los
   20 s (la misma espera de la ventana, `_CMR_DIA_ESPERAS_S`), mismo producto y versión. Si el reintento también falla,
   el breaker se enciende como antes. ConnectTimeout y ConnectionError lo encienden al primero (A64). El costo extra
   está acotado a 20 s más un intento por fecha, así que la garantía de S116 contra el cuelgue de Copahue sigue en
   pie. Con `VRP_CMR_BREAKER=0` no se reintenta. Afecta también al NRT (mismo `fetch.py`): en el peor caso le suma
   unos 80 s a una corrida con CMR degradada.
2. `scripts/revisar_sombra.py`: la búsqueda caída deja rojo sólo si es del último día JUZGADO (o sin fecha); la de un
   día sin noche cerrada va como NOTA y la juzga la corrida siguiente, que lo vuelve a buscar.

Con el arreglo 2 solo, el 16 habría dado 2 rojos menos en la sombra de los 11 (PlanchonPeteroa y NdC). Con el 1, los
otros tres casos dependen de que el reintento hubiera encontrado a CMR de vuelta (SOSPECHA, arriba).

Pruebas: `tests/test_sombra_cmr_s190.py` (6, rojas antes del arreglo) y `tests/test_fetch_cmr_search_breaker_s116.py`
(2 aserciones pasan de 1 a 2 llamadas, con nota).

## Fuera de este PR

- `scripts/revisar_guardia_modis.py` tiene la misma regla de cobertura con `fin` (líneas 99 y 104). No se tocó: la
  guardia no falló en estas fechas y no era el encargo.
- El vigilante (26 h sin verde) no da falsas alarmas: el 16 hubo pérdida real de datos. No se ajusta.
