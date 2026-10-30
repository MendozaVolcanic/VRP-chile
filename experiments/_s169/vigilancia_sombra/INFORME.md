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
