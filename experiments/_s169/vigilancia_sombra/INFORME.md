# S169: vigilancia de la sombra «código MIROVA» antes del 2026-11-03

Rama `claude/s169-vigilancia-sombra`, cortada de `origin/main` en `161536698` (2026-10-30). Defectos de
`experiments/_s169/audit_patrones/f3/INFORME_F3.md` y de su verificador (rama `loop/activo`). Nada tocado en
`pipeline/`, `data/` ni `frontend/`. Temporales en `D:/vrp-trabajo/temporales/s169_vigilancia/`.

## 1. Por qué

La sombra corre una vez al día los últimos 8 días, y su JSON ya trae lo que commitearon las corridas anteriores. Si
la revisión mira la ventana entera, juzga el trabajo de ayer como si fuera de hoy: una noche sin medir pasa por
medida, y un solo record malo de un día tiñe de rojo la semana siguiente. Sobre esas noches se decide si la vía pasa
a producción, así que la revisión tiene que juzgar lo que hizo **esta** corrida, sensor por sensor, y alguien tiene
que avisar cuando la corrida ni siquiera ocurre.

## 2. Qué cambió, por defecto

| Defecto | Cambio | Archivo |
|---|---|---|
| P3-02 (corrida vacía verde desde el día 2) | La revisión cuenta sólo los records con `processed_utc` igual o posterior al inicio de la corrida **y** con `regimen.codigo_sha` igual al sha del disparo. `pipeline/store.py` (l. 541 y 549) reescribe los dos campos en cada record que guarda, nuevo o reemplazo NRT->estándar, y no toca los que ya estaban (l. 687-708). El workflow anota `inicio` antes de llamar a run_pipeline. Además lee la cobertura: búsquedas o descargas fallidas, o un log que dice «Cobertura INCOMPLETA», son falla. Sin JSON de cobertura también es falla. | `scripts/revisar_sombra.py`, `.github/workflows/sombra-codigo-mirova.yml` |
| P3-03 (sin control por sensor) | Exige al menos un record de la vía de esta corrida para MODIS, VIIRS 750 y VIIRS 375 (el job ya es uno por volcán). Única excepción, escrita en una línea `NOTA`: todas las plataformas vivas del sensor respondieron sin gránulos el día `fin` (incidencia `sin_granulos` de `pipeline/fetch.py`) o están retiradas por cese anunciado. Eso dice «miró y no hubo pasada». | `scripts/revisar_sombra.py` |
| VF3-01 (rojo arrastrado 8 días) | Los records que no son de la vía se cuentan sólo entre los de esta corrida. | `scripts/revisar_sombra.py` |
| P3-09 (nadie vigila la sombra) | `nrt-monitor.yml` (el mecanismo que ya abre issues para el NRT) tiene un segundo paso, `if: always()`. La decisión pura `decidirSombra` vive en `scripts/nrt_monitor_decision.js`: desde el 2026-11-03 15:00 UTC, si no hay una corrida **programada** terminada en verde en las últimas 26 h, abre el issue «Sombra codigo MIROVA: sin corrida verde en 26 h» (etiqueta `nrt-alert`) o refresca su cuerpo sin notificar; con una verde, lo cierra. Si la API no responde, deja el job rojo y no decide. La sombra entra también al reporte de cadencia (`ESPERADO_POR_DIA`, 1 por día). | `scripts/nrt_monitor_decision.js`, `.github/workflows/nrt-monitor.yml`, `scripts/medir_cadencia_cron.py` |
| P3-04, parte del workflow | `run_pipeline.py ... --cobertura-json cobertura.json`. Nuevo paso `actions/upload-artifact@v4`, con `if: always()` y corrida hecha, que sube `pipeline.log` y `cobertura.json` como `sombra-<volcán>-intento-<n>`, con retención de 90 días. | `.github/workflows/sombra-codigo-mirova.yml` |

La línea de la revisión en el workflow quedó en una sola línea a propósito: la prueba nueva la extrae del YAML y la
ejecuta tal cual, así que prueba también el cableado (A118).

## 3. Pruebas: rojo antes, verde después

Pruebas nuevas: `tests/test_revisar_sombra_corrida_s169.py` (15) y `tests/test_monitor_sombra_s169.py` (8). Se
corrieron primero contra el código de `main` (`161536698`), con las pruebas ya escritas y sin el arreglo:
`20 failed, 3 passed`. Los 3 que pasan son controles (corrida sana verde, `ERROR processing` rojo, record de K de hoy
rojo). Así se ven los rojos de la revisión con el código viejo, todos fallando por la aserción y no por un error de
la prueba (salida completa en `D:/vrp-trabajo/temporales/s169_vigilancia/rojo_antes_motivos.txt`):

```
test_corrida_vacia_del_dia_2_con_cmr_caido_sale_roja     AssertionError: ventana 2026-11-03 a 2026-11-04: 3 records, 3 de la vía, ... assert 0 != 0
test_corrida_vacia_del_dia_8_sale_roja                   AssertionError: ventana 2026-11-03 a 2026-11-10: 21 records, 21 de la vía, ... assert 0 != 0
test_falta_un_sensor_entero_sale_rojo                    AssertionError: ventana 2026-11-03 a 2026-11-05: 6 records, 6 de la vía, ... assert (0 != 0)
test_un_sensor_que_esta_corrida_no_produjo_sale_rojo     AssertionError: ... 8 records, 8 de la vía ... assert (0 != 0)
test_sin_pasada_legitima_se_dice_por_escrito_y_sale_verde AssertionError: ... assert ([])      (sale 0 pero no lo dice)
test_record_de_k_viejo_no_enrojece_la_corrida_de_hoy     AssertionError: ... FALLA: records que no son de la vía: {'geo_distinta': 1} assert 1 == 0
test_el_workflow_pide_cobertura_y_anota_el_inicio...     AssertionError: run_pipeline sin --cobertura-json
test_el_workflow_sube_log_y_cobertura_como_artefacto...  AssertionError: [] assert 0 == 1
test_nrt_monitor_vigila_el_workflow_de_la_sombra         AssertionError: nrt-monitor no tiene un paso que mire la sombra
test_la_cadencia_del_cron_cuenta_la_sombra_una_vez_al_dia AssertionError: (...) assert None == 1
(las 6 de decidirSombra: CalledProcessError, la función no existía)
```

Después del arreglo, las 23 nuevas más las de cadencia y del monitor del NRT dan **43 passed**
(`D:/vrp-trabajo/temporales/s169_vigilancia/verde_despues.txt`). La salida de la revisión nueva en los casos
principales (`muestras.py`, salida en `muestras_salida.txt` de la misma carpeta):

```
--- dia2_vacia_cmr_caido: salida 1
  FALLA: cobertura incompleta: 30 búsquedas o descargas fallidas; MODIS: ningún record de la vía escrito en esta corrida; VIIRS750: ...; VIIRS375: ...
--- dia8_vacia: salida 1   (21 records en la ventana, 0 escritos en esta corrida)
--- falta_modis_entero: salida 1
  FALLA: MODIS: ningún record de la vía escrito en esta corrida
--- sin_v750_esta_corrida: salida 1
  FALLA: VIIRS750: ningún record de la vía escrito en esta corrida
--- sin_pasada_v750_legitima: salida 0
  NOTA VIIRS750: sin records de esta corrida; miró y no hubo pasada el 2026-11-05 (búsqueda sin gránulos en VIIRS_NOAA20_750, VIIRS_NOAA21_750)
--- k_viejo_dia5_juzgado_dia7: salida 0
```

`tests/test_sombra_codigo_mirova_s167.py::test_revisar_sombra_falla_si_la_corrida_queda_verde_sin_la_via` se
actualizó a la firma nueva y conserva sus cuatro casos. La de cadencia (`test_lo_esperado_por_dia_coincide_con_el_cron_declarado_en_el_yml`)
ahora vigila también el cron de la sombra.

Guardias de workflows y de la sombra, en una sola corrida y con el árbol quieto (A112):
`test_sombra_codigo_mirova_s167`, `test_guard_expresiones_workflows_s161`, `test_guard_declarado_vs_efectivo_s131`
(incluye la de `"on"` entre comillas, A43), `test_guard_timeout_vs_ventana_s129`, `test_guard_token_vacio_cron_s160`,
`test_workflow_aplicar_reemplazo_s158`, `test_reproc_watchdog_vivos_s133` y `test_vigilancia_sombra_s156`:
**149 passed, 4 skipped** en 126 s (`guardias.txt`). No miré por qué saltan los 4.

## 4. Qué quedó sin cubrir

- **Falso rojo posible**: si un sensor tuvo gránulos hoy pero ninguno dio record (todos de día, o ninguno cubre la
  grilla de la vía, `return None` en pipeline/), la revisión da rojo aunque nada haya fallado del lado nuestro. La
  cobertura cuenta gránulos por búsqueda, antes del filtro nocturno y sin saber qué hizo la vía, así que desde aquí
  no se distingue. A las 15:00 UTC los gránulos del día son los nocturnos (los diurnos sobre Chile pasan después,
  más 3 h de latencia), así que lo espero raro; no está medido. Si ocurre, el rojo se lee en la línea FALLA y el log
  está en el artefacto.
- **El aviso dentro de `pipeline/`** cuando la vía descarta un gránulo (resto de P3-04) no se tocó: pipeline/ está
  congelado durante la sombra. El artefacto con el log y la cobertura deja el rastro, pero el log sigue sin una línea
  por gránulo descartado.
- **El monitor** sólo cuenta corridas `schedule`: un despacho a mano verde no cierra el issue. Si algún día la sombra
  recibe un disparador externo, el monitor dará alerta visible (no verde falso) y habrá que ajustar `decidirSombra`.
  Tampoco distingue un job rojo de un volcán de todo el run rojo: ambos dan conclusión `failure`.
- **No probado en GitHub**: el paso nuevo de `nrt-monitor.yml` (github-script), el `upload-artifact` y la línea de
  `inicio` sólo se probaron por lectura del YAML y por la función pura; no hubo despacho (prohibido en esta tarea).
  La primera evidencia real será la corrida del 2026-11-03 15:00 UTC y el chequeo de nrt-monitor de las 18:30.
- **Fuera de alcance**: P3-01 y P3-05 a P3-16 (evaluador común, procedencia, `nan`, perfil ambiental, etc.).

## 5. Ronda 2

Un verificador limpio revisó `16d9e894d` (`D:/vrp-trabajo/temporales/s169_ver_vigilancia/INFORME_VERIFICACION.md`) y
concluyó MERGEABLE CON CAMBIOS. Las decisiones son de la coordinadora; lo de abajo las aplica. Por qué importa cada
una: la revisión diaria tiene que decir la verdad sobre **esta noche**. Un verde que se apoya en el trabajo de otro
día (VV169-01) o en un catálogo vacío (VV169-02) hace pasar por medida una noche que no se midió. Un rojo por algo
que ya estaba cubierto (VV169-03) o por una corrida que todavía no termina (VV169-04) acostumbra a no mirar el rojo.

| Hallazgo | Decisión | Cambio | Prueba que lo fija |
|---|---|---|---|
| VV169-01, falso verde | El control por sensor cuenta sólo los records de esta corrida con pasada de `fin` o de `fin` menos un día | `scripts/revisar_sombra.py`: filtro `datetime_utc[:10] >= vispera` en el conteo por sensor. Un reemplazo NRT a estándar de hace días sigue contando como «de esta corrida» para el control de K, no para cumplir | `test_vv01_reemplazos_de_dias_viejos_no_cumplen...` (rojo antes) y `test_vv01_un_record_de_ayer_escrito_hoy_si_cumple` |
| VV169-02, falso verde | FALLA si quedan sin pasada a la vez los tres sensores, o VIIRS 750 y VIIRS 375 | Igual, regla después de las NOTA: «catálogo de CMR vacío, no la órbita» | `test_vv02_catalogo_vacio_en_los_tres_sensores_es_falla`, `test_vv02_viirs_750_y_375_vacios_a_la_vez_es_falla` (rojas antes) |
| VV169-03, falso rojo | Una falla de búsqueda o descarga de un día anterior a `fin` es NOTA; sólo la de `fin` (o sin fecha) es FALLA | Igual, y escrito en el docstring del módulo | `test_vv03_falla_de_busqueda_de_un_dia_viejo_es_nota` (roja antes), `test_g_falla_de_busqueda_del_ultimo_dia_es_falla...` |
| VV169-04, falso rojo | Corrida `schedule` en cola o en curso creada hace menos de 6 h: «pendiente», ni alerta ni cierre | `scripts/nrt_monitor_decision.js` (`horasPendiente = 6`); `nrt-monitor.yml` sale antes de tocar el issue con `pendiente` | `test_vv04_la_corrida_de_hoy_en_curso_es_pendiente` (roja antes), `test_vv04_una_corrida_en_curso_vieja_no_tapa_la_alerta`, `test_vv04_el_monitor_no_abre_ni_cierra_con_pendiente` (roja antes) |
| VV169-05 | No se arregla en `pipeline/store.py` (congelado); se deja a la vista | La revisión escribe siempre «K caídos en la ventana: N», con el detalle por tipo, en su salida y en el resumen del job (GITHUB_STEP_SUMMARY), también en verde y también con 0 | `test_vv05_los_k_caidos_quedan_a_la_vista...` y `test_vv05_la_linea_de_k_esta_aunque_sea_cero` (rojas antes) |
| Mutaciones A, E, G, P, R | Pruebas que las atrapen por aserción | Sin cambio de código | `test_a_record_de_ayer_con_el_mismo_sha_no_cuenta`, `test_e_sin_granulos_de_otro_dia_no_justifica...`, `test_g_...`, `test_p_el_inicio_anotado_es_la_hora_de_la_corrida_en_el_formato_del_store` (exige `INICIO=$(date -u +%Y-%m-%dT%H:%M:%SZ)` y que ese formato sea el de `processed_utc` en `pipeline/store.py`), `test_r_nrt_monitor_tiene_permiso_de_issues_y_de_actions` |
| VV169-07 | Que el log subido no lleve el token | Nuevo `scripts/tachar_secreto_log.py` y paso «Tachar el token en el log y la cobertura» antes del artefacto, con la misma condición `always()` | `test_vv07_el_log_se_tacha_antes_de_subirlo` (roja antes; prueba el paso y ejecuta el script con un token falso) |
| VV169-08 | Corregir el docstring | `tests/test_revisar_sombra_corrida_s169.py`: base `161536698` | (documental) |

**Rojo antes, verde después.** Con las pruebas nuevas de la ronda 2 escritas y el código de `16d9e894d`:
`9 failed, 30 passed` (`D:/vrp-trabajo/temporales/s169_vigilancia/r2_rojo_antes.txt`), todas por aserción: VV01,
VV02 (2), VV03, VV05 (2), VV07, VV04 (2). Las de A, E, G, P y R pasan con el código correcto a propósito: existen para
atrapar mutaciones, y se ve abajo que lo hacen. Una prueba de la ronda 1
(`test_una_corrida_en_curso_o_manual_no_cuenta_como_verde`) cambió su aserción a «nunca ok», porque con VV169-04 la
respuesta correcta para una corrida de hoy en curso es «pendiente». Después del arreglo: **39 de 39** en las dos
pruebas nuevas, y **208 passed, 4 skipped** en la batería completa (las dos nuevas, cadencia, monitor del NRT,
`test_sombra_codigo_mirova_s167` y las siete guardias de workflows, incluida la de `"on"` entre comillas;
`r2_guardias.txt`). Las 4 saltadas son de `test_guard_timeout_vs_ventana_s129.py:102`: «backfill-tier-a.yml,
nrt.yml, reproc-chunked.yml, sombra-codigo-mirova.yml no declara fechas por defecto parseables», o sea que ninguna
guardia compara hoy el timeout de la sombra con su ventana (preexistente).

**Mutaciones.** `m4_mutaciones_r2.py` (en esta carpeta, adaptado del `m4_mutaciones_rapido.py` del verificador)
copia scripts, tests, `.github` y `pipeline` a una carpeta temporal y rompe una cosa a la vez. Control: la copia sin
tocar da `39 passed`. Resultado: **32 de 32 atrapadas por aserción, 0 sobreviven** (`m4_r2_salida.txt`). Son las 18
del verificador (A a R, con G e I reescritas para los textos nuevos) más P2 (inicio en otro formato), R2 (sin
`actions: read`) y 12 de la ronda 2: V1, V2, V2b, V3, V3b, V4, V4b, V4c, V5, V5b, V7 y V7b. No declaré ninguna
equivalente.

**VV169-07, lo que sí y lo que no comprobé.** Por grep: en `pipeline/fetch.py` ninguna línea imprime el token, una
cabecera `Authorization` ni `Bearer`. Los `print` con excepción (`Failed to fetch {platform}: {e}`, l. 1282) pueden
llevar URL de datos, que no son secretas. En earthaccess 0.17.0 (la instalada en este computador) el único log que
toca el token es `logger.info("Using token with expiration date %s", ...)`, que imprime la fecha y no el valor.
Además, el workflow no usa `set -x`, y el paso del perfil sólo imprime nombre y flags. **No pude comprobar** la
versión que instala el runner, que no está fijada (`pip install earthaccess`), ni el contenido de un log real.
Por eso el paso de tachado va antes de subir el artefacto: si el token apareciera, se reemplaza por `***` y queda un
`::warning::` que no repite el valor.

**Riesgo aceptado (VV169-05).** Un record de K caído queda en `data/sombra_codigo_mirova/` para siempre:
`pipeline/store.py` sólo lo reemplaza con `overwrite` o en el paso NRT a estándar, y el workflow no ofrece
`overwrite`. El job queda rojo sólo el día en que se escribe, y el issue del monitor se cierra con la corrida verde
siguiente. Desde la ronda 2 el conteo acumulado de la ventana sale en cada resumen del job, pero **nadie lo va a
borrar**: el lector de la sombra tiene que filtrar por `via_codigo_mirova` (P3-10, fuera de esta tarea). Arreglarlo
de raíz (un `overwrite` en el despacho, o que store reemplace un K con un record de la vía) toca `pipeline/` y
queda para después de la sombra.

**Sigue sin probarse en GitHub**: el paso del monitor, `upload-artifact`, el tachado, el resumen del job y la línea
de `inicio`. El verificador recomienda, después del merge y antes del 2026-11-03 15:00 UTC, un despacho
`medir=true` de Láscar sobre 2 o 3 días pasados, y un despacho de `nrt-monitor.yml`, que debería decir «Sombra:
inactivo» (§7 de su informe). No los hice: los despachos están fuera de esta tarea.
