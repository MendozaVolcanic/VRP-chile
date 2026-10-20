# Búsqueda por ventana y brazos en el mismo job: plan de implementación (S157)

> Para quien lo ejecute: tareas en orden, cada una con su prueba primero (TDD). Casillas `- [ ]`.

**Objetivo.** Buscar en CMR una vez por producto y por ventana (no una vez por día), correr los brazos de un A/B que
comparten volcán y ventana en el mismo job reusando búsquedas y gránulos, y que un día que no se pudo buscar ya no
salga verde en silencio.

**Arquitectura.** La búsqueda por ventana vive dentro de `fetch.search_granules`, detrás de la misma firma: si la fecha
cae en una ventana configurada, la respuesta sale de una caché llenada con una sola consulta por producto y ventana,
repartida por día con la misma regla con que CMR responde una consulta de un día. Si la ventana no se puede consultar,
se vuelve al camino de hoy (una consulta por día). Los brazos corren en serie, un proceso por día y brazo, sobre una
caché en disco de búsquedas y gránulos que el driver borra día a día. Ningún procesador ni perfil cambia.

**Base medida.** `MEDICION.md` en esta carpeta.

---

## Criterios de aceptación (se fijan antes de escribir código)

- **A1, identidad de gránulos.** Para cada producto y cada día de la ventana, la lista que devuelve `search_granules`
  con ventana es la MISMA lista (mismos `GranuleUR`, mismo orden) que devuelve hoy la consulta de un día, incluida la
  regla «standard primero, versiones en orden, NRT (LANCE) si el standard del día viene vacío». Se comprueba con
  pruebas sobre earthaccess simulado y, contra el CMR real (público, sin credencial), con `identidad_cmr.py` sobre una
  ventana de reproceso y una ventana NRT.
- **A2, identidad de records.** El mismo volcán y la misma ventana corridos con el código del tag
  `pre-s157-busqueda-ventana` y con la rama dan los mismos records: misma clave `(datetime_utc, sensor)` y todos los
  campos iguales salvo `processed_utc`, `regimen.codigo_sha` y `regimen.origen` (marcas de escritura y de versión). Lo
  mide `comparar_records.py`.
- **A3, el NRT no cambia de comportamiento**: misma salida, y si CMR falla, a lo más ~2,5 min extra antes de caer al
  camino de hoy (un solo intento de ventana fallido apaga la ventana para el resto del proceso).
- **A4, cobertura visible.** Toda búsqueda que no se pudo hacer (cortacircuito, timeout, HTTP 5xx) y toda descarga
  fallida queda registrada por volcán, día y producto; `run_pipeline` la imprime, la escribe en `--cobertura-json`, emite
  `::warning::` en Actions, y con `--estricto-cobertura` sale con código 3. El NRT no usa el modo estricto.
- **A5, brazos.** `scripts/reproc_brazos.py` corre N perfiles sobre la misma ventana; cada búsqueda a CMR y cada
  gránulo se baja una sola vez por job; los records de cada brazo son idénticos (A2) a los de correr el brazo solo.
- **A6, tiempos.** Cada paso de los workflows queda bajo 170 min (A15: duración esperada por 1,3).
- **A7, interruptor.** `VRP_BUSQUEDA_VENTANA=0` vuelve al camino de hoy (variable de infraestructura como
  `VRP_CMR_BREAKER`, no de método; no va al perfil). Una prueba comprueba que la lee el código que la usa (A89).

## Archivos

- Modificar `pipeline/fetch.py`: caché de ventana, reparto por día, caché en disco, registro de fallas.
- Modificar `scripts/run_pipeline.py`: configurar la ventana, conservar gránulos, cobertura y modo estricto.
- Crear `scripts/reproc_brazos.py`: driver de brazos.
- Modificar `.github/workflows/reproc-s146-ab-sin-test1.yml`: plan por trozos, brazos en el mismo job, unión por brazo.
- Modificar `.github/workflows/reproc-chunked.yml`: modo estricto y cobertura como artefacto.
- Crear `.github/workflows/probe-s157-busqueda-ventana.yml`: validación tag contra rama (push a una rama propia).
- Crear `tests/test_busqueda_ventana_s157.py`, `tests/test_reproc_brazos_s157.py`.
- Crear en esta carpeta: `identidad_cmr.py`, `comparar_records.py`, `mutaciones.py`.

## Tareas

### Tarea 1: reparto por día (función pura)
- [ ] Prueba: `_repartir_por_dia(granulos, dias)` asigna un gránulo al día D si `inicio <= D 23:59:59` y
  `fin >= D 00:00:00` (es lo que pide earthaccess 0.17 para `temporal=(D, D)`: `cmr/queries.py::_format_date` pone
  `T00:00:00Z` y `T23:59:59Z`, y CMR cruza por traslape con bordes incluidos); un gránulo que cruza la medianoche va a
  los dos días; uno que empieza a las 23:59:59.500 no es del día; sin tiempos parseables o a menos de 2 s de una
  medianoche, los días tocados quedan `None` (se consultan por día); 20 o más gránulos en un día quedan `None` (la
  consulta de un día pide `count=20` y truncaría).
- [ ] Implementar, correr, commit.

### Tarea 2: consulta de la ventana con la regla standard → NRT
- [ ] Prueba con `earthaccess.search_data` simulado: por cada intento (short_name, versión) en el orden de hoy se
  consulta el tramo de días aún sin resolver; un día queda resuelto con el primer intento que le trae algo; los días que
  ningún intento resuelve quedan `[]`. Un `NOAA20` cuyo 2.1 cubre todo hace UNA consulta, no tres.
- [ ] Prueba: si `len(resultados) >= count` (truncado), toda la ventana del producto cae al camino por día.
- [ ] Implementar `_buscar_ventana(product_key, bbox, d_ini, d_fin)`; commit.

### Tarea 3: `search_granules` sirve desde la ventana
- [ ] Prueba: con `configurar_ventana(fechas)`, 8 días por 2 productos hacen 2 consultas (no 16) y cada día devuelve
  lo mismo que la consulta por día; fuera de la ventana o con otra caja, camino de hoy; `VRP_BUSQUEDA_VENTANA=0`, camino
  de hoy.
- [ ] Prueba: si la ventana falla (timeout o `RuntimeError` de HTTP 5xx) se reintenta una vez; si vuelve a fallar, se
  usa el camino por día y la ventana queda apagada para el resto del proceso; una credencial muerta aborta como hoy.
- [ ] Prueba: con el cortacircuito de CMR encendido, un día ya en la caché se sirve igual (no hace falta CMR).
- [ ] Implementar; commit.

### Tarea 4: caché en disco (para el segundo brazo)
- [ ] Prueba: con `cache_dir`, un segundo proceso (módulo recargado) sirve todos los días sin llamar a CMR; los
  gránulos reconstruidos tienen el mismo `umm`, `data_links()` y `cloud_hosted`.
- [ ] Implementar; commit.

### Tarea 5: registro de cobertura
- [ ] Prueba: `SEARCH_SKIP`, `SEARCH_CMR_TIMEOUT`, un `RuntimeError` de CMR y una descarga fallida dejan una entrada
  `{volcan, fecha, plataforma, producto, etapa, motivo}`; un día sin gránulos (respuesta vacía) no deja ninguna.
- [ ] Prueba de `run_pipeline`: con fallas, `--estricto-cobertura` sale con 3 y `--cobertura-json` escribe el archivo;
  sin el flag sale con 0 y avisa.
- [ ] Implementar; commit.

### Tarea 6: conservar gránulos y driver de brazos
- [ ] Prueba: `VRP_CONSERVAR_GRANULOS=1` no borra el directorio del día.
- [ ] Prueba del driver con `run_pipeline` simulado: orden día por fuera y brazo por dentro, mismo `VRP_TMP_DIR` y
  misma caché de búsquedas para todos los brazos, borra el día al terminar sus brazos, sale distinto de 0 si un brazo
  falla, y 3 si hay fallas de cobertura en modo estricto.
- [ ] Implementar `scripts/reproc_brazos.py`; commit.

### Tarea 7: workflows
- [ ] A/B: job `plan` que parte la ventana con `split_date_window` en trozos de
  `dias_por_trozo(n_brazos)` (presupuesto 130 min = 170 / 1,3, con 0,6 min/día de búsqueda y descarga y 1,6 min/día de
  proceso por brazo, de `MEDICION.md` y del estimador de F/K), matrix volcán por trozo, driver con todos los brazos,
  artefacto por (volcán, trozo), `recolectar` une los trozos de cada brazo con `merge_chunk_stores.py --ventanas`.
  Paso 170 min, job 180.
- [ ] reproc-chunked: `--estricto-cobertura --cobertura-json` y artefacto de cobertura con `if: always()`. El merge no
  se toca (lo vigilan las pruebas de `test_reproc_chunked_merge_conserva_s157.py`).
- [ ] `python -c "import yaml; ..."`: la clave `"on"` es cadena en los tres; correr las pruebas que leen los yml.

### Tarea 8: validación (A1, A2, A5, tiempos)
- [ ] `identidad_cmr.py` contra el CMR real: ventana de reproceso (Chillán, 10 días) y ventana NRT (Láscar, 8 días
  hasta ayer); 0 diferencias en `GranuleUR` y orden.
- [ ] Workflow de validación (4 jobs, grupo propio, sólo token, sin push a main): {Chillán 4 días, Láscar 2 días
  recientes} por {tag, rama}; el tag corre los dos brazos por separado, la rama con el driver; tiempos por job.
- [ ] `comparar_records.py` sobre los artefactos: 0 diferencias fuera de las marcas de escritura.

### Tarea 9: mutaciones con control (A110) y suite con el árbol quieto (A112)
- [ ] Mutaciones: borde `<=` por `<`, sin la regla de 20, NRT antes que standard, sin registro en el `except`
  genérico, modo estricto que no sale con 3, driver que borra antes del segundo brazo, reparto corrido un día.
  Contar como atrapada sólo la que falla por aserción; la que cae por error se informa aparte.
- [ ] Suite completa sin tocar archivos mientras corre.

### Tarea 10: verificador con contexto limpio, PR borrador, CI con conclusión. Sin merge.
