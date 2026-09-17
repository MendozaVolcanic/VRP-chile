# Verificador con contexto limpio, ANTES de correr el probe de las 12 noches

> Auditoría del instrumento, no de la hipótesis. Escrita el 2026-09-17 sin red, sin git y sin
> despachar nada. Cada hallazgo lleva archivo:línea, comando y salida. Nada de lo que sigue está
> copiado de otro informe: los números salen de correr los comandos que se citan.

**VEREDICTO: CORREGIR ANTES DE CORRER.** El instrumento mide casi todo lo que dice medir, pero los
brazos `*_sin_compuerta_ctx` cambian dos cosas a la vez y la salida del probe no permite separarlas
(hallazgo 1), y tres detalles de ejecución pueden quemar la corrida o leerse como resultado
(hallazgos 3, 4 y 5). Los cuatro se arreglan en una tarde y ninguno obliga a rediseñar el probe.

## Tabla de hallazgos

| # | grav. | estado | hallazgo |
|---|---|---|---|
| 1 | 4 | CONFIRMADO | Quitar la compuerta en la máscara contextual no es un cambio aislado: también puede apagar el filtro del Test 1 entero, que es el otro mecanismo bajo prueba |
| 2 | 3 | CONFIRMADO el mecanismo, NO realizado en la muestra | El objeto medido es el record ANTES de `store.append_record`; la selección se hizo sobre records DESPUÉS |
| 3 | 3 | CONFIRMADO | Con el input `vol`, tres de los cuatro jobs de la matriz terminan VERDES sin correr nada ni subir artefacto |
| 4 | 3 | SOSPECHA | El presupuesto de 240 min puede no alcanzar para 132 procesamientos del job de Planchón-Peteroa |
| 5 | 3 | CONFIRMADO | El control 3 es global sobre las 61 pasadas: una sola pasada sin bloque contextual declara INCONCLUSO el probe entero |
| 6 | 2 | CONFIRMADO, sin efecto hoy | Predicado mixto: la noche perdida viene de `publica_en_crater` (S135) y la pasada del predicado del dashboard |
| 7 | 2 | CONFIRMADO | El lado del costo está sub-dimensionado y medio trivial por construcción |
| 8 | 2 | CONFIRMADO | Tres de los cuatro controles de instrumento son casi tautológicos |
| 9 | 2 | CONFIRMADO | El reuso de granules no filtra por plataforma y nadie comprueba que las seis variantes usaron el mismo archivo |
| 10 | 2 | CONFIRMADO | La carpeta no está commiteada y `workflow_dispatch` sólo corre desde `main` |
| 11 | 1 | CONFIRMADO, heredado a conciencia | La cota A93 compara radios, no posiciones |

---

### 1. El brazo sin compuerta cambia dos cosas a la vez (gravedad 4, CONFIRMADO)

El envoltorio baja la compuerta dentro de `dual_roi_contextual_dnti_hot_mask`, o sea cambia
`dnti_ctx_hot`. Ese arreglo no alimenta sólo al filtro del Test 1: su conteo entra en la decisión de
quién es la fuente del hotspot.

```
pipeline/process_viirs.py:1081   n_dnti_ctx_path = int(np.sum(dnti_ctx_hot))
pipeline/process_viirs.py:1746   only_test1_source = (
pipeline/process_viirs.py:1751       and (n_dnti_ctx_path or 0) == 0
pipeline/process_viirs.py:1765   _test1_wins = (... only_test1_source=only_test1_source ...)
pipeline/process_viirs.py:1775           final_hotspot_source = "test1"
pipeline/process_viirs.py:1839   if (ENABLE_TEST1_CONTEXTUAL_FILTER and final_hotspot_source == "test1"
```

El fenómeno: al sacar la exigencia de que el píxel esté más caliente que el fondo del anillo, el
camino contextual pasa de cero píxeles a varios en las noches débiles, que son justamente estas.
En cuanto `n_dnti_ctx_path` deja de ser cero, `only_test1_source` se cae, `_test1_wins` puede dar
False, la fuente pasa a `"eruption"` y **el filtro contextual del Test 1 no llega a correr**. Es
decir, el brazo `literal_sin_compuerta_ctx` puede "recuperar" la noche por el mismo mecanismo que
`literal_t1_sin_filtro`, y la lectura pre-registrada lo atribuiría a la máscara.

Peor: la fuente interna, la que gobierna la línea 1839, **se pisa antes de persistirse**.

```
pipeline/process_viirs.py:2084   ...  final_hotspot_source) = resolve_honest_anchor(
```

Verificado sobre los artefactos de S135: las fuentes que quedan escritas son `test1_roi` (16) y
`ctx_cluster` (25) en las 41 `perdida`, que son etiquetas del ancla honesta, no el valor que leyó la
línea 1839. O sea, con la salida actual del probe **no se puede saber si el filtro corrió**.

**Corrección propuesta.** En `probe.py`, envolver también `pv.apply_contextual_test1_filter`
contando llamadas y guardando `n_entrada` y `n_salida` de píxeles, y agregar `diag_n_dnti_ctx_path`
y `hotspot_dist_km` a `CAMPOS`. En el README, la fila 2 de la lectura ("la compuerta de la máscara
es la causa") exige además que el filtro haya corrido en esas pasadas; si no corrió, el resultado es
el de la fila 3 disfrazado. Alternativa más limpia, si se quiere aislar de verdad: una séptima
variante que use una máscara sin compuerta **sólo** en la llamada de la línea 1850, dejando
`n_dnti_ctx_path` con la máscara con compuerta.

### 2. El objeto medido es el record antes de `store.append_record` (gravedad 3, CONFIRMADO)

El probe llama `pv.calculate_vrp` y le pasa el resultado directo al predicado del dashboard. La
selección, en cambio, leyó los JSON de S135, que pasaron por `store.append_record`. Tres campos que
el predicado lee **no existen** en el record crudo:

- `vrp_mw`: `calculate_vrp` devuelve `vrp_mir_mw` pero no `vrp_mw` (bloque de retorno,
  `pipeline/process_viirs.py:2101-2180`); lo crea `store.py:316` y lo cierra `store.py:414`.
- `discarded_reason`: `grep -n "discarded_reason" pipeline/process_viirs.py` devuelve **cero
  líneas**; sólo lo escribe `store.py`. Lo lee `frontend/index.html:1484` (`isSummitDetection`).
- `f5_core_vrp_mw`: lo calcula y persiste `store.py:552`. Está presente en 53 de los 53 records
  publicados de la muestra y ausente en todos los del probe.

Y `store` además reescribe `distance_class`, `final_hotspot_*` y `anomaly_pixels` (`store.py:316-414`
rescate y anulación por hotspot lejano, `store.py:472-477` guard de coherencia).

**Medido, y esto lo baja de 5 a 3**: sobre las 61 pasadas, borrar `vrp_mw`, `discarded_reason` y
`f5_core_vrp_mw` de los records de S135 y volver a correr el predicado con node no cambia **ninguna**
publicación (0 de 61 en el brazo A y 0 de 61 en el D). El JS recalcula el núcleo desde
`anomaly_pixels` (`frontend/index.html:1126-1149`) y el resto lo decide `primary_cluster`. Pero el
riesgo no es cero: 2 de las 41 `perdida` del brazo A traen
`discarded_reason = "single_pixel_far_overridden_by_cluster"`, o sea ya dependieron de una rama que
sólo existe en `store`, y 14 de los 61 tienen el centroide del cúmulo a más del 87 % del
`inner_radius` (Lastarria 6 de 10, Planchón-Peteroa 8 de 20), donde un corrimiento chico cruza el
borde. Las variantes nuevas mueven exactamente eso.

**Corrección propuesta.** Pasar el record por `store.append_record` con los mismos argumentos que
`run_pipeline.py:292-299`, neutralizando la escritura (`store._save = lambda *a, **k: None` y
`store._load = lambda n: {"records": []}`). Son cuatro líneas y deja al probe midiendo el mismo
objeto que midió la selección. Si se decide no hacerlo, decirlo en el README como límite explícito
y persistir `hotspot_dist_km` para poder detectar después los records que producción habría anulado.

### 3. Jobs verdes sin datos (gravedad 3, CONFIRMADO)

`.github/workflows/probe-s143-12-noches.yml` repite `if: github.event.inputs.vol == '' ||
github.event.inputs.vol == matrix.vol` en **todos** los pasos, incluido el de subida. Si alguien
despacha con `vol: Lastarria`, la matriz igual crea cuatro jobs y tres terminan en verde sin ejecutar
un solo paso y sin artefacto. Es el modo de falla de S141 y el error de lectura de S134 (A93b): "24
de 24 jobs verdes" no dice nada del universo cubierto.

**Corrección.** Matriz dinámica (`fromJSON` sobre la entrada) para que sólo exista el job pedido, o
un paso final sin condición que falle con un mensaje cuando el job no corrió.

### 4. El presupuesto de tiempo (gravedad 3, SOSPECHA)

El job de Planchón-Peteroa tiene 22 pasadas (`seleccion_resumen.json`: 17 `perdida` + 3 + 2), que por
seis variantes son **132 llamadas a `calculate_vrp`** más 44 descargas de L1B y GEO. `timeout-minutes:
240`. Si el promedio de proceso pasa de 1,7 min por granule, el job muere y `1_todas_ok` da falso,
o sea el probe entero queda INCONCLUSO (bien atrapado, pero con la corrida quemada). No puedo medirlo
sin red, por eso es SOSPECHA.

**Corrección.** Subir a `timeout-minutes: 350` (el techo de GitHub es 360 y no cuesta nada), y
pilotear primero con `vol: Lastarria` (12 pasadas, el job más chico) para calibrar antes de soltar
los cuatro.

### 5. El control 3 es demasiado frágil (gravedad 3, CONFIRMADO)

`analizar.py:186` exige `llamadas_envoltorio_min >= 1`, o sea que el envoltorio se haya llamado en
**todas** las 61 pasadas. El bloque contextual está condicionado
(`pipeline/process_viirs.py:1049-1053`: `ENABLE_DNTI_CONTEXTUAL_PATH`, `"I05" in bands`,
`not np.isnan(nti_bg)`, gate atmosférico). Confirmado que el gate atmosférico no aplica
(`PATH_D_ATM_GATE_TBG_MIN_K = None`, comprobado con `python -c "import pipeline.profile"`), pero un
granule sin I05 o un anillo sin fondo válido deja el conteo en cero, y entonces **una sola pasada
invalida el probe completo, incluidas las cuatro variantes que no tienen envoltorio**.

**Corrección.** Exigirlo sólo donde el control tenga `diag_n_dnti_ctx_path` definido (que es lo que
hay que agregar a `CAMPOS` igual por el hallazgo 1), y listar las excepciones en vez de tumbar todo.

### 6. Predicado mixto (gravedad 2, CONFIRMADO, sin efecto en la muestra)

Las 12 noches de `PERDIDAS_S135` se definieron con `publica_en_crater`
(`experiments/_s135_ab_d1d2/evaluar_ab.py:136-144`), un predicado de Python sobre
`primary_cluster.vrp_mw`, sin `isThermalArtifact`. El probe usa el predicado del dashboard con node.
Y el criterio 1 del A/B que este probe va a informar cita `publica_en_crater`
(`docs/PREREGISTRO_AB_D22_D25_S143.md:122-127`).

**Medido**: sobre las 61 pasadas los dos predicados coinciden 61 de 61 en los dos brazos, así que hoy
no cambia nada. Vale como nota al pie: un brazo puede pasar el probe y perder la noche en el A/B si
los predicados se separan en records nuevos.

### 7. El costo está sub-dimensionado y medio trivial (gravedad 2)

`neg_artefacto` se eligió como "A publica y D no", así que cualquier variante que recupere las noches
volviéndose parecida a A publicará esas 12 por construcción: ese número no compara nada. El lado
informativo es `neg_quieta`, y son **8** (Isluga y Lastarria sólo tenían 2 disponibles cada uno, ver
`seleccion_resumen.json`). La advertencia del README ("una variante que publique las 8 no se
propone") descansa sobre n = 8. El README ya declara el límite general; conviene decir esto en
particular, porque es el único lado que puede frenar una adopción.

### 8. Los controles 2a, 2b y 4 son casi tautológicos (gravedad 2)

`perdida` y `neg_artefacto` se definieron como "A publica y D no", y `control` corre con los flags de
A y `s135_d` con los de D. Verifiqué que `_s142_ab_control` es **flag por flag idéntico** a
`_s135_ab_a_control` (ver abajo), así que esos tres controles comprueban reproducibilidad del código
de hoy contra septiembre, que es legítimo y útil, pero no son un control independiente del
mecanismo. Los únicos independientes son el 1 (cobertura) y el 3 (envoltorio).

### 9. Reuso de granules (gravedad 2)

`probe.py:bajar_par` reusa con `DEST.glob(f"*{stamp}*")` y `_tipo(p.name)`, sin filtrar por
plataforma: dos pasadas de satélites distintos con el mismo `Adoy.HHMM` se pisarían (improbable, no
imposible). Y nadie comprueba después que las seis variantes hayan usado el mismo par de archivos,
aunque `fila["granules"]` lo guarda. Sugerencia barata: que `analizar.py` verifique que los seis
`granules` de una pasada son iguales, y lo repita en el control de instrumento.

### 10. La carpeta no está commiteada (gravedad 2)

`git status --short` muestra los seis archivos en `A` (agregados al índice, sin commit) sobre la rama
`s143-evaluador-ab`, y `workflow_dispatch` sólo es invocable desde la rama por defecto
(S73, y el yml ya aplica A43 con `"on":` entre comillas). Mergear antes de despachar, obvio, pero
vale escribirlo porque el modo de falla es un HTTP 422 confuso.

### 11. La cota compara radios (gravedad 1, heredado a conciencia)

`mismo_objeto` mide `|radio_nuestro - Distancia_km|`, y dos puntos distintos pueden compartir radio.
Es la propia A93. Viene de S135 y el README lo asume; lo dejo anotado para que nadie lea "mismo
objeto" como "misma posición".

---

## Lo que comprobé que SÍ está bien

- **Las seis variantes declaran lo que hacen.** `PROBE_VARIANTE=<v> python -c "import probe as p;
  print(p.flags_efectivos())"` para las seis: `control` (compuerta puesta, keep_peak on, segundo pase
  suelto), `s135_d` (keep_peak off, condicionado on), `literal` y sus dos hijas (D22 on, D25 on,
  condicionado on, keep_peak off), y `literal_t1_sin_filtro` con
  `ENABLE_TEST1_CONTEXTUAL_FILTER: false`. Ninguna sorpresa.
- **El control reproduce el brazo A del A/B S135.** Volcando todas las constantes de
  `pipeline.profile` con los dos perfiles y diffeando, `_s142_ab_control` difiere de
  `_s135_ab_a_control` sólo en `DATA_SUBDIR`, `PROFILE_NAME`, `SENSOR_MODIS` y `SENSOR_VIIRS_750`,
  que no tocan el cálculo de un granule I-band.
- **`pv.ENABLE_TEST1_CONTEXTUAL_FILTER = False` sí equivale al flag de perfil.** El nombre sólo
  aparece en `pipeline/profile.py:257` y `pipeline/process_viirs.py:179`, y ahí se usa como global de
  módulo (línea 1839). No hay copia en línea de esa lógica en otro procesador (A102 comprobada).
- **El envoltorio alcanza de verdad la máscara que llega al filtro.** `process_viirs` llama por
  nombre de módulo (`pipeline/process_viirs.py:1063` y `:1074`), así que el parche en el namespace de
  `pv` intercepta (A89 no aplica acá), y el dual reenvía `apply_bt_gate` a sus dos llamadas internas
  (`pipeline/detection_context.py:384`). La compuerta que se quita es la de
  `detection_context.py:272`.
- **`ENABLE_SECOND_PASS_CONDITIONED` se lee sólo del perfil**, en los tres procesadores
  (`grep -rn` sobre `pipeline/`), y cada perfil de variante lo fija: `_s135_ab_d_ambos` y
  `_s142_ab_literal` en `true`, `_s142_ab_control` hereda `false` de `mirova_equivalent:432`.
- **El camino D legacy publicado NO cambia por el envoltorio** (pregunta 2 del encargo, con la
  salvedad del hallazgo 1, que es indirecta). `hot_mask_2d` se pisa con `fp_hot` en
  `process_viirs.py:1299` porque `enable_first_pass_tests_2_and_3: true`, así que lo que
  `combine_hot_paths` armó con `dnti_ctx_hot` (línea 1228) se descarta; la única otra lectura
  (línea 1127) está detrás de `ENABLE_TEST1_NTI_COVALIDATION`, que está apagado. Y el bloque del
  primer pase no se salta, porque los cuatro volcanes tienen `inner_radius_km` y el gate atmosférico
  es `None`.
- **El sello de la pasada se reconstruye exacto.** `datetime_utc` sale del propio nombre del granule
  (`process_viirs.py:2212-2227`), así que `A{año}{doy}.{HHMM}` cierra el círculo, y sirve igual para
  los nombres NRT (`VNP02IMG_NRT.A....`).
- **Los tres productos existen** en `pipeline.fetch.PRODUCTS` (`VIIRS_SNPP`, `VIIRS_NOAA20`,
  `VIIRS_NOAA21`, cada uno con L1B, GEO y su variante NRT) y `_tipo` distingue bien `02IMG` de
  `03IMG` en los nombres estándar y NRT.
- **Las dependencias alcanzan.** El camino importado (`process_viirs`, `fetch`, `detection_context`,
  `geo_utils`, `clustering`, `regrid`) no usa `pyproj` ni `netCDF4`, y `pyhdf` está detrás de un
  `try/except` en `process_modis`. La importación completa corre en esta máquina con lo que el
  workflow instala.
- **La llamada a `calculate_vrp` y el ancla son los de producción**: misma firma y mismos kwargs que
  `scripts/run_pipeline.py:277-290`, incluido `get_detection_anchor(volcano)`.
- **El workflow no se traga un fallo**: `set -o pipefail` con `tee` (S141), `sys.exit(2)` cuando
  falta una pasada, `rc=1` que no corta las demás variantes, `if-no-files-found: error` y `"on":`
  entre comillas (A43).
- **La estructura de artefactos calza** con el `rglob(f"{v}/*.json")` de `analizar.py`, que sirve
  igual con uno o con los cuatro artefactos.
- **La cota tiene la misma semántica que S135**: mismo origen (`mirova_center`), mismo
  `min |nuestro - Distancia_km|`, mismo 0,55 km y la misma indulgencia cuando falta el centroide o la
  distancia de MIROVA (`evaluar_ab.py:271-283` contra `analizar.py:mismo_objeto`). Los cuatro
  volcanes tienen `mirova_center_lat/lon` en `volcanoes.yaml`.
- **La referencia es la misma** en selección y análisis
  (`experiments/_s143_preregistro/_dl_referencia`, los dos CSV existen).
- **Reproduje el ensayo del README.** Con los records de S135 disfrazados de variantes, `analizar.py`
  da `control` 12 de 12, `s135_d` 0 de 12, los cuatro controles en verde y la lectura "literal
  recupera". Idéntico a lo que declara el README y coherente con `resultado_final.json`. O sea: el
  analizador funciona y sus criterios son alcanzables, no imposibles de cumplir.
- **La muestra cubre lo que dice cubrir**: 61 pasadas, 12 de 12 noches con al menos una pasada,
  `noches_perdidas_sin_pasada` vacío, cero duplicados de `(volcán, pasada, sensor)`, y las horas son
  todas nocturnas.

## Orden sugerido para corregir

1. Hallazgo 1 (envoltorio del filtro del Test 1 + `diag_n_dnti_ctx_path` + la lectura de la fila 2).
2. Hallazgo 5 (aflojar el control 3 usando ese mismo diagnóstico).
3. Hallazgos 3 y 4 (matriz y timeout: dos líneas del yml).
4. Hallazgo 2 (`store.append_record` con la escritura neutralizada), o declararlo como límite.
5. Piloto con `vol: Lastarria` antes de soltar los cuatro jobs.
