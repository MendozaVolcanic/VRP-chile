# Verificación del arreglo S169 de vigilancia de la sombra (rama claude/s169-vigilancia-sombra, commit 16d9e894d)

CARPETA: D:/vrp-trabajo/temporales/s169_ver_vigilancia/
Informe escrito a medida; versión final al cierre de la sesión.

## 1. Encabezado

- Fecha y hora del servidor: `date -u` = Fri Oct 30 04:41:12 UTC 2026 (inicio) a ~05:05 UTC (cierre).
- Commit medido: 16d9e894d (árbol extraído con `git archive`, sin `.git`, sin `docs/`, sin `data/`, sin `CLAUDE.md`), base 161536698. Datos de producción: `origin/main` a33070b9 (2026-10-30 04:33 UTC), sólo `git show`.
- Modelo: Sonnet 5.5 (claude-sonnet-5-5), esfuerzo bajo.
- `caminos.md` escrito y sellado ANTES de abrir INFORME.md o cualquier archivo citado (sha256 f0a4d2fb...614a, 04:42:09 UTC).
- NO miré: `data/sombra_codigo_mirova/` (prohibido), el pipeline corriendo (prohibido), GitHub Actions real (sin red), la API de issues, ningún run del cron real. No medí frecuencia de rojos por corte de CMR (no hay histórico local de `cobertura.json`). No leí las 23 pruebas nuevas línea por línea (sí corrí 18 mutaciones contra ellas, ver §5).

## 2. En una pantalla

- B1, B3, B5 CONFIRMADOS en lo que afirman; B6 CONFIRMADO (23/23, 43/43, 20 rojas contra el código de main; en mi árbol parcial 141 de la suite de guardias + 8 que fallan por archivos ausentes del `git archive`, no por el arreglo).
- B2 CONFIRMADO EN PARTE: SNPP queda fuera desde el 3-nov (bien); el riesgo declarado (gránulos sin record) mide 0 de 77 en la corrida de Láscar de S168, pero hay dos huecos de diseño de signo contrario: un record reescrito de días anteriores cuenta como "de esta corrida" (VV169-01, falso verde) y un catálogo CMR vacío da verde con 3 NOTA (VV169-02).
- B4 CONFIRMADO EN PARTE: borde del 2026-11-03 15:00 UTC, sólo `schedule`, sin duplicados y permisos correctos; pero alerta si la corrida de hoy aún está en curso a las 18:30 (VV169-04) y un rojo de un solo volcán abre el issue (VV169-03).
- Veredicto: **MERGEABLE CON CAMBIOS** (ningún cambio bloquea; son 2 líneas de código y 1 regla del monitor, y pueden ir en un PR corto después del despacho de prueba). Recomiendo el despacho manual `medir=true` después del merge (ver §7).

## 3. Hallazgos (ordenados por gravedad)

### VV169-01
- TÍTULO: El control por sensor se satisface con records reescritos de días anteriores (NRT a estándar) y de la víspera: un sensor puede fallar hoy y salir verde
- ARCHIVO:LÍNEA: scripts/revisar_sombra.py:89-97 y 123-131; pipeline/store.py:541, 549, 695-699
- QUÉ PASA: cuando una pasada de hace varios días se reprocesa porque ya existe el L1B estándar, store.py reemplaza el record NRT y le pone un `processed_utc` nuevo y el sha del disparo; `de_esta_corrida` lo cuenta como escrito hoy, y el control por sensor sólo exige "algún record de la familia", sin pedir que sea de la fecha `fin` o `fin-1`. Una falla que afecte sólo la pasada de hoy de un sensor (gránulo descartado, geolocalización que no llegó) queda tapada si ese día hubo una reescritura vieja de ese sensor.
- CÓMO SE VE EN EL DASHBOARD: invisible (la sombra no se lee en el tablero); en el job queda verde sin NOTA.
- CÓMO REPRODUCIRLO: `python D:/vrp-trabajo/temporales/s169_ver_vigilancia/medidas/m2_revisar_casos.py`, caso C ("FUGA"): 0 records del 2026-11-06, 3 records de los días 3 y 4 reescritos hoy: OK. Control B (records de ayer sin reescribir): FALLA.
- CONFIANZA: CONFIRMADO el mecanismo (código y caso sintético). La frecuencia es SOSPECHA parcial: en los JSON del NRT de main (`origin/main`, `data/mirova_equivalent/`, cron horario, no la sombra) hay reescrituras de pasadas de 1 a 4 días de edad en 3 de los 12 días entre 2026-10-19 y 2026-10-30 (Villarrica/Llaima/PCC: 10-19 una, 10-22 seis, 10-29 ocho; Láscar: 10-29 seis; `medidas/m1_*_salida.txt`). El ritmo real en la sombra (cron diario a las 15:00) depende de cuándo aparece el L1B estándar y no está medido.
- GRAVEDAD: 2. Torcería la lectura de "esta noche el sensor sí produjo", no una alerta de volcán. Arreglo propuesto: en `de_esta_corrida`, exigir además `datetime_utc[:10] >= fin - 1 día`.

### VV169-02
- TÍTULO: Un catálogo CMR vacío deja la corrida verde con tres NOTA "miró y no hubo pasada"
- ARCHIVO:LÍNEA: scripts/revisar_sombra.py:61-80 y 125-131; pipeline/fetch.py (comentario S159 I1 sobre R2-13, "CMR devolvía cero gránulos de todo el día" el 2026-10-18; incidencia `sin_granulos` "sin juicio")
- QUÉ PASA: la NOTA se escribe cuando todas las plataformas vivas de un sensor respondieron vacío el día `fin`. Si CMR responde vacío para TODO (el caso R2-13 que el propio fetch.py documenta), los tres sensores quedan en NOTA y el job sale verde con cero records de hoy; el monitor lo ve como corrida verde. Físicamente es casi imposible que ningún sensor pase de noche sobre un volcán de Chile (VIIRS tiene 3.000 km de franja y dos plataformas vivas).
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: m2_revisar_casos.py, caso E: salida OK con NOTA MODIS, NOTA VIIRS750, NOTA VIIRS375 y 0 escritos. Control D2 (una plataforma vacía y otra con gránulos): FALLA.
- CONFIANZA: CONFIRMADO (mecanismo y caso sintético); que vuelva a ocurrir es SOSPECHA (ocurrió el 2026-10-18 según el comentario de fetch.py, que no releí en la fuente primaria).
- GRAVEDAD: 2. Se autocura al día siguiente porque la ventana de 8 días vuelve a buscar y esos records entran como nuevos; el daño es un día invisible. Arreglo propuesto: si los tres sensores quedan en NOTA el mismo día, FALLA (o al menos VIIRS750 y VIIRS375 en NOTA a la vez).

### VV169-03
- TÍTULO: Cualquier búsqueda o descarga fallida en cualquiera de los 8 días de la ventana deja el job en rojo, y un solo job rojo hace fallar la corrida y abre el issue del monitor
- ARCHIVO:LÍNEA: scripts/revisar_sombra.py:113-120; scripts/run_pipeline.py::informar_cobertura (el JSON trae `fallas` de toda la ventana); pipeline/fetch.py (cortacircuito de CMR: tras el primer timeout toda búsqueda posterior queda como falla)
- QUÉ PASA: la cobertura cubre la ventana entera, y el recorrido va de la fecha más antigua a la de hoy. Un corte de CMR en el día 1 de la ventana dispara el cortacircuito y pierde también las búsquedas de hoy (rojo correcto); uno en un día viejo cuyo record ya existe también deja rojo (rojo sin pérdida real). Un volcán rojo vuelve `failure` a todo el run, y `decidirSombra` sólo mira la conclusión del run.
- CÓMO SE VE EN EL DASHBOARD: invisible; en GitHub, X roja en el run y un issue "Sombra codigo MIROVA: sin corrida verde en 26 h" abierto hasta la próxima corrida verde (~24 h).
- CÓMO REPRODUCIRLO: m2, caso M (1 falla de cobertura en 4 records sanos): FALLA. Frecuencia real: SIN DATO. Comando para medirla (necesita red, no lo corrí): `gh run list --workflow nrt.yml -L 100 --json conclusion` y contar `SEARCH_CMR_TIMEOUT` en los logs.
- CONFIANZA: CONFIRMADO el mecanismo; frecuencia SOSPECHA. Referencia del proyecto (CLAUDE.md, regla A108, TEXTO): "3 de 108 quedaron con pasadas de menos por cortes de NASA (SEARCH_CMR_TIMEOUT, A64)", que sería ~2,8 % de jobs y ~27 % de días con al menos un rojo entre 11 volcanes si se repitiera. Es otro workflow y otra carga: sólo como orden de magnitud.
- GRAVEDAD: 2 (ruido que acostumbra a no mirar el rojo; el rojo es verdadero en la mayoría de los casos).

### VV169-04
- TÍTULO: El monitor alerta a las 18:30 si la corrida de hoy sigue en curso, y el margen depende del retraso del cron de GitHub
- ARCHIVO:LÍNEA: scripts/nrt_monitor_decision.js:53-75 (`created_at` de la última verde, tope 26 h, `status === 'completed'`); .github/workflows/nrt-monitor.yml:145-200
- QUÉ PASA: la edad se mide desde el `created_at` de la última corrida verde (ayer ~15:0x), de modo que desde ~17:05 del día siguiente la verde de ayer ya pasó las 26 h. El chequeo de las 18:30 (cron `30 */6 * * *`) sólo ve verde si la corrida de hoy terminó y salió verde. 11 jobs con `max-parallel: 4` son 3 oleadas de ~15 min (907 s medidos en Láscar, run 40945613044) más instalación, o sea ~1 h; con arranque a las 15:00 a 16:00 queda ≥1,5 h de margen, pero GitHub retrasa los cron del minuto 0.
- CÓMO SE VE EN EL DASHBOARD: invisible; issue falso que se cierra solo a las 00:30.
- CÓMO REPRODUCIRLO: `node D:/vrp-trabajo/temporales/s169_ver_vigilancia/medidas/m3_monitor.js`, línea "hoy en curso a las 18:30": alerta.
- CONFIANZA: CONFIRMADO el comportamiento de la función; que ocurra es SOSPECHA (depende del retraso real).
- GRAVEDAD: 2. Arreglo propuesto: si hay una corrida `schedule` en `queued` o `in_progress` creada hace menos de 6 h, devolver 'pendiente' y no abrir ni cerrar nada.

### VV169-05
- TÍTULO: Un record de K caído un día queda para siempre y el rojo dura una sola corrida
- ARCHIVO:LÍNEA: pipeline/store.py:695-699 (sólo reemplaza con `overwrite` o NRT a estándar); .github/workflows/sombra-codigo-mirova.yml:26-46 (los inputs son volcano, medir, start, end: no hay overwrite); scripts/revisar_sombra.py:97-123
- QUÉ PASA: antes el record de K dejaba el job rojo 8 días (ruido que tapaba, pero gritaba); ahora lo juzga sólo el día en que se escribe. Al día siguiente la vía puede estar sana, pero la pasada ya existe con K y store.py no la reemplaza (salvo que fuera NRT y llegue el estándar), el workflow no ofrece reproceso con overwrite, y el monitor cierra el issue con la corrida verde siguiente. El hueco sólo se ve filtrando por `via_codigo_mirova`.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: m2 casos K1 (K de ayer: OK) y K2 (K de hoy: FALLA); el no reemplazo se lee en store.py.
- CONFIANZA: CONFIRMADO por lectura del código; el efecto en la medición pre-registrada es SOSPECHA.
- GRAVEDAD: 2. No es regresión (el hueco existía), pero el arreglo quita el único aviso prolongado. Sugerencia: input `overwrite` del despacho, o que el issue del monitor mencione cuántos K hay en la ventana.

## 4. Veredicto por afirmación

| Afirmación | Veredicto | Evidencia de esta sesión |
|---|---|---|
| B1 juzga sólo `processed_utc` desde el inicio anotado, con sha, y lee la cobertura | CONFIRMADO EN PARTE | `processed_utc` lo escribe `pipeline/store.py:541` en todo record que pasa por `append_record` (también los de la vía, `scripts/run_pipeline.py` l. 266, 311, 358) y `regimen.codigo_sha` = `GITHUB_SHA` (`store.py:90-94`). Mismo runner, mismo formato `Z`, segundos, `>=` (caso J, igualdad exacta: cuenta). Cobertura ausente o con fallas: FALLA (casos F, M; mutaciones F y G). Un duplicado exacto no se reescribe y no cuenta (correcto). Un reemplazo NRT a estándar SÍ cuenta como de esta corrida: VV169-01. Corrida con 0 records nuevos: FALLA (control B), también un despacho manual repetido el mismo día aunque esté sano (no rutinario). |
| B2 al menos un record por sensor y volcán; NOTA si todas las plataformas vivas respondieron vacío | CONFIRMADO EN PARTE | Suomi NPP: `fetch.py::cese_cumplido` la retira desde el día UTC siguiente al 2026-11-02 13:00 (00:00 del 3-nov >= cese) y `_sin_pasada_hoy` la salta con `inicio_dia >= cese`; en la primera corrida no queda "viva" ni deja rojo VIIRS (caso D, mutación D). Terra y Aqua se cuentan las dos (D2: una plataforma con gránulos y sin record da FALLA). Riesgo declarado "gránulos sin record": en Láscar, 2026-10-21 a 28, 77 gránulos procesados dieron 77 records (`experiments/_s168/sombra_run_40945613044/salida.txt`, en loop/activo: leí ese archivo, no re-corrí nada); un gránulo que cubre el volcán da record aunque no haya anomalía ("vacio"). Las ramas `return None` existen (`mirova_v750_codigo.py:804` menos de 100 píxeles; `:807` centro a más de 5 km en MODIS y VIIRS 375, no en VIIRS 750) pero afectan un borde de ~20 km de la franja (1 a 2 % de las pasadas por plataforma, estimación teórica, SIN DATO medido) y casi siempre el gránulo vecino o la otra plataforma sí da record. Otro origen posible: L1B sin MOD03/geolocalización (incidencia `sin_geolocalizacion`, el 2026-10-20 CMR traía 72 MOD021KM NRT contra 68 MOD03 según el comentario de fetch.py): quedaría rojo ese día y la ventana lo repara al siguiente. Huecos de diseño: VV169-01, VV169-02. |
| B3 K de un día anterior ya no enrojece; uno de hoy sí | CONFIRMADO | m2 K1 OK, K2 FALLA; caso L (K viejo reescrito hoy) FALLA, lo que es razonable. Mutación C (contar K sobre toda la ventana) atrapada por las pruebas. Ver VV169-05 por el costo. |
| B4 monitor de la sombra | CONFIRMADO EN PARTE | Borde: antes de 14:59:59Z 'inactivo', desde 15:00:00Z activo (m3). Todo en UTC con `Z`; no hay zona horaria local. Cuenta sólo `event === 'schedule'`, `status completed` y `success` (despacho manual verde no tapa: m3, línea "despacho manual"; cancelado tampoco). Sin duplicados: busca el issue abierto por título dentro de `nrt-alert`, refresca el cuerpo sin notificar; cierra con comentario al volver una verde (lectura del yml; NO probado en GitHub, sólo la función pura). Permisos: `permissions` de nivel workflow tiene `issues: write` y `actions: read`, suficiente (`yaml.safe_load`, medidas). `retries: 3` es input de github-script v7 (SOSPECHA, no abrí el action.yml). Falla de la API: `core.setFailed`, no decide. Reservas: VV169-03 y VV169-04. |
| B5 workflow | CONFIRMADO | `"on"` entre comillas (yaml: claves str); único secreto `secrets.EARTHDATA_TOKEN` (grep); `--cobertura-json cobertura.json` en la llamada (l. 128); artefacto `if: always() && corrio == 'true'`, nombre con volcán e intento (único, sin choque v4), `if-no-files-found: warn`; el input `medir` booleano llega como la cadena "true" por `env` y se compara con `= "true"`. El revisor corre `always()` y después del commit. Pipeline.log en bruto en un repo público: SEGUIMIENTO. |
| B6 pruebas | CONFIRMADO | Ver §6. |

## 5. Mutaciones sobre las pruebas nuevas
Script `medidas/m4_mutaciones_rapido.py`, salida `medidas/m4_salida.txt`. Sobre una copia del árbol se rompe una cosa a la vez y se corren sólo las 23 pruebas nuevas. Control: la copia sin tocar da `23 passed` (el instrumento no inventa fallas) y 13 de 18 mutaciones se atrapan por aserción (el instrumento puede fallar).

Atrapadas (13): B sin filtro de sha, C K viejo cuenta, D Suomi NPP tratada como viva, F cobertura ausente, H una plataforma vacía basta, I sensor faltante nunca falla, J monitor cuenta despachos manuales, K tope de 200 h, L fecha de inicio 2020, M corridas sin terminar cuentan como verdes, N artefacto sin `always()`, O `--sha ""`, Q paso del monitor sin `always()`.

SOBREVIVEN (5), cada una es un hueco de prueba:
- A, quitar el filtro de `processed_utc`: las pruebas separan los días por sha, así que el filtro de tiempo no se prueba solo. En producción el sha de cada día cambia porque los commits de datos mueven main, pero un reintento o dos corridas sobre el mismo sha sólo las separa el tiempo.
- E, aceptar una incidencia `sin_granulos` de cualquier día (no sólo de `fin`): ninguna prueba pone la incidencia en otra fecha. Mi caso H de m2 sí lo cubre (FALLA correcto), el código está bien pero no tiene prueba.
- G, ignorar las `fallas` del JSON de cobertura: las pruebas con fallas fallan igual por otro motivo (el log dice «Cobertura INCOMPLETA» o no hay records). Si el log no lo dijera, el JSON con fallas pasaría.
- P, anotar `inicio` con una fecha constante vieja: la prueba sólo comprueba que el `echo "inicio="` quede antes de correr, no su valor ni que use `date -u`. (Con el sha distinto cada día lo taparía el sha.)
- R, quitar `issues: write` del monitor: ninguna prueba mira los permisos; en producción el paso fallaría con 403 el 3-nov.

Estas cinco no son fallas del arreglo, pero P y R son las que la primera corrida real descubriría tarde.

## 6. Pruebas re-corridas (árbol quieto, un hilo)

- Las 23 nuevas: `23 passed in 3.92s` (`medidas/b6_nuevas.txt`).
- Con cadencia y monitor del NRT (`test_cadencia_cron_s133`, `test_nrt_monitor_decision_s150`): `43 passed` (`medidas/b6_43.txt`).
- Contra el código de main: copia del árbol con los 5 archivos no-prueba del diff devueltos a 161536698 (`arbol_main/`): `20 failed, 3 passed` (`medidas/b6_rojo_contra_main.txt`). Los 3 que pasan son controles (sano verde, ERROR processing rojo, K de hoy rojo). Ojo: 8 de los 20 rojos son de `decidirSombra`, que en main no existe (rojo por ausencia de la función, no por detectar un defecto); los 12 de la revisión y el workflow sí fallan por aserción.
- Guardias de workflows y de la sombra (8 archivos del autor): en mi árbol `141 passed, 8 failed, 4 skipped` (`medidas/b6_fallas_en_arbol.txt`). 141 + 8 = 149, la cifra del autor. Los 8 fallan por `FileNotFoundError` de archivos que mi `git archive` no trae (`docs/FICHA_SDA_VRP_CHILE.md`, `CLAUDE.md`, `docs/INDEX.md`, `experiments/_s153_fk_v2/v1.log` y `v1.json`), en `test_guard_declarado_vs_efectivo_s131` (4) y `test_vigilancia_sombra_s156` (4); ninguno toca los archivos del diff. NO pude confirmar que pasen en el árbol completo: SIN DATO (comando: `python -m pytest -q tests/test_guard_declarado_vs_efectivo_s131.py tests/test_vigilancia_sombra_s156.py` en un checkout completo de 16d9e894d).
- Las 4 saltadas: las cuatro son `tests/test_guard_timeout_vs_ventana_s129.py:102`, "backfill-tier-a.yml / nrt.yml / reproc-chunked.yml / sombra-codigo-mirova.yml no declara fechas por defecto parseables". No son por falta de node (node 22.16 está y los tests del monitor pasan). Consecuencia: ningún guardia compara el timeout de 75 min de la sombra con su ventana (preexistente: el yml de main tampoco declara fechas por defecto).
- El docstring de `tests/test_revisar_sombra_corrida_s169.py` dice que se vio rojo "contra el código de main cc3887290" y el INFORME dice 161536698: inconsistencia documental (SEGUIMIENTO).

## 7. Despacho manual de prueba recomendado (después del merge, antes del 2026-11-03 15:00 UTC)

1. `sombra-codigo-mirova.yml`, workflow_dispatch con `medir=true`, `volcano=Lascar`, `start`/`end` de los últimos 2 a 3 días (por ejemplo 2026-10-28 a 2026-10-30; Suomi NPP aún viva). Es barato (un volcán, ~15 min). Ejerce los pasos nuevos: anotar `inicio`, `--cobertura-json`, la línea de revisión con `--desde-utc` y `--sha`, y el artefacto `sombra-Lascar-intento-1`. Esperado: Revisar verde con "escritos en esta corrida" > 0 por sensor (en el runner no hay records de la sombra para esas fechas, así que todo es nuevo), commit omitido. Lo que NO ejerce: la rama del 3-nov (SNPP retirada), el commit real ni el monitor.
2. `nrt-monitor.yml`, workflow_dispatch: debe imprimir "Sombra: inactivo" y terminar verde; comprueba que `listWorkflowRuns` sobre la sombra y los permisos funcionan. La apertura del issue sólo se ejerce el 3-nov 18:30.

## 8. SEGUIMIENTOS (fuera de mi eje o de baja gravedad; los arreglos los decide quien orquesta)

- VV169-06 (SOSPECHA, gravedad 1): el cron de la sombra es `0 15 * * *` (minuto 0, hora punta de GitHub, que retrasa o pierde eventos `schedule`; el repo ya perdió uno el 2026-08-27 según el comentario de `scripts/nrt_monitor_decision.js`), y el monitor sólo acepta `event === 'schedule'`. Un minuto fuera de punta lo atenuaría; si se agrega un disparador externo (como el NRT) hay que cambiar `decidirSombra` o alertará siempre. Archivo: `.github/workflows/sombra-codigo-mirova.yml:25`, `scripts/nrt_monitor_decision.js:58`.
- VV169-07 (SOSPECHA, gravedad 1): el artefacto sube `pipeline.log` crudo. El enmascarado de secretos de Actions actúa sobre el visor, no sobre un archivo escrito con `tee`. En `pipeline/fetch.py` no vi que se imprima el token (grep de `EARTHDATA_TOKEN`, `Bearer`, `Authorization`), y ya hay 10+ workflows `probe-*` con `upload-artifact`, pero el repo es público. Archivo: `.github/workflows/sombra-codigo-mirova.yml:161-172`.
- VV169-08 (CONFIRMADO, gravedad 1): el docstring de `tests/test_revisar_sombra_corrida_s169.py` (l. 18) dice "main cc3887290" y el INFORME.md dice 161536698.
- Las pruebas nuevas no cubren VV169-01 ni VV169-02 (ningún caso reescribe un record viejo ni pone los tres sensores en NOTA): ver la tabla de mutaciones, que no puede atraparlas porque no son mutaciones del código sino huecos de diseño.
- Cron-job.org externo del NRT y la sombra por `schedule`: dos mecanismos de disparo distintos en el mismo repo; el monitor del NRT cuenta cualquier evento y el de la sombra sólo `schedule`. No es un defecto, pero conviene dejarlo escrito.

## 9. VERIFICADO LIMPIO (con la vara usada)

- `processed_utc` y `regimen.codigo_sha` los escribe `store.py:541,549` para todo record guardado por `append_record` (lectura); la vara es el código de producción, no un doc. Casos J (igualdad exacta con el inicio) y B (record de ayer) lo confirman en `revisar`.
- Suomi NPP: `scripts/ceses_esperados.json` (2026-11-02T13:00:00Z) y `fetch.py::cese_cumplido` retiran el sensor por día UTC completo; `revisar_sombra._sin_pasada_hoy` usa la misma regla (`inicio_dia >= cese`). Vara: la mutación D (tratar SNPP como viva) tiene que atraparla una prueba (ver §5).
- Monitor: antes y después del 2026-11-03 15:00:00Z (m3), sólo `schedule`, sin duplicados por título, permisos del workflow suficientes. Vara: salida de `decidirSombra` con 12 casos; control positivo "verde de hoy" = ok, control "sin corridas" = alerta.
- Workflow: `"on"` string, un solo secreto, nombre del artefacto único por volcán e intento, `corrio == 'true'` en el revisor y el artefacto (si la ventana no toca todavía, ambos se saltan: correcto antes del 3-nov).
- `store.py` no reescribe un duplicado exacto (sin overwrite ni NRT a estándar): no cuenta como de esta corrida.

## 10. SIN DATO

- Frecuencia de rojos por cortes de CMR en la sombra (comando: `gh run list --workflow nrt.yml -L 100` y buscar `SEARCH_CMR_TIMEOUT`; sin red no lo hice).
- Frecuencia con que el estándar llega después de la corrida de las 15:00 y produce reescrituras diarias (VV169-01): se necesitan los JSON de la sombra después de unos días; no abrí `data/sombra_codigo_mirova/` (prohibido).
- `retries: 3` de github-script v7, el comportamiento real de `upload-artifact@v4`, la apertura real del issue: no probados en GitHub.
- Los 8 tests de guardias que fallan en mi árbol parcial: comprobar en un checkout completo.
- Retraso real del cron de las 15:00 UTC y duración total de las 3 oleadas con los 11 volcanes.

## 11. FUERA DE ALCANCE

P3-01 y P3-05 a P3-16 del informe F3; el pipeline (congelado); el rendimiento de la vía; si la regla de 26 h es la correcta para la decisión de pasar a producción.
