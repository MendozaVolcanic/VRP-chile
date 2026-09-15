# Verificador con contexto limpio del instrumento v2 (antes de la corrida)

Rama verificada: `origin/s141-fase1-probe-v2`, commit `1e5a6b7f9` (PR #675). Fecha: 2026-09-15.
Worktree temporal de sólo lectura en el scratchpad (`verif_v2`, eliminado al terminar). Scripts propios:
`...\scratchpad\taxonomia.py` (rótulos y C3 con `cluster_hotspots` real). No se tocó la rama, el PR ni ningún workflow.
Rutas de código relativas a la raíz del repo en esa rama; `pipeline/` es idéntico a `origin/main` (el diff sólo trae `scripts/medir_atraso_despacho_nrt.py`).

## 0. Veredicto global

**DESPACHAR CON CAMBIOS.** El v2 corrige de verdad los defectos de secuencia, de centro tautológico y de la brecha contra el backfill, pero tal como está puede dar un veredicto `PATRON | VECINOS_TIBIOS` que no depende del fenómeno: el destino sale por construcción, un control (C3) no puede fallar, y el filtro de foco deja entrar una pasada con nuestro pico a 16 km del foco de MIROVA.

## 1. Las 8 correcciones de `VERIFICADOR.md` §6

| # | Corrección | Veredicto | Evidencia | Grav. |
|---|---|---|---|---|
| 1 | Filtrar por posición del foco de MIROVA | CORRECTA CON MATIZ (grave) | `muestra.py:94` y `analisis_v2.py:275` usan `min(d_pico, d_crater) <= 0,75`. Por la rama del cráter entra **Puyehue 2025-07-18 05:24** con el foco de MIROVA a 0,109 km del cráter y **nuestro pico persistido a 16,39 km** (`pasadas.json`). En la corrida, `foco_ok` vuelve a medir con `d_crater`, que es fijo, así que la "re-medición con el pico de hoy" no puede excluir ninguna de las 25 de 38 pasadas con `dist_crater_km <= 0,75`. Ver H1 | 4 |
| 2 | Rotular dentro de la ruta; `mask_contributing` no marca | CORRECTA CON MATIZ (grave) | Implementado (`analisis_v2.py:138-154`, test `test_marcado_por_pixel_nunca_usa_la_mascara_del_test1`). Pero la taxonomía colapsa: dos de los cuatro destinos son imposibles por construcción y el destino de la ruta contextual está fijado antes de correr. Ver H3 | 4 |
| 3 | Evidencia del cúmulo publicado y booleanos por etapa | CORRECTA CON MATIZ | `identificar_publicado` (`analisis_v2.py:67-88`) compara con `round(c, 5)` contra `primary_cluster` que el pipeline redondea igual (`process_viirs.py:1506-1507`, `:1942-1943`); `apply_single_pixel_mode` copia y sólo toca `vrp_mw` y `single_pixel_mode` (`single_pixel_mode.py:149-184`). La llamada de `:1910` pisa `primary_cluster` sólo si devuelve algo (`:1915`), y eso coincide con tomar la última coincidencia. `corrio()` es por llamada, no por `None` (`captura.py:43-54`). Matiz: C1 castiga pasadas sin cúmulo (H4) | 3 |
| 4 | Centro = nuestro píxel pico del cúmulo publicado | CORRECTA CON MATIZ | `analisis_v2.py:240-241` elige el máximo de `vrp_per_pixel` dentro de los índices publicados; la distancia al OSF queda como variable (`:243`). Matiz: la muestra filtró con otro "pico" (el de F5, H7) | 2 |
| 5 | Lo publicado hoy, brecha de la misma corrida | CORRECTA CON MATIZ | `ensamblar.py:26-36`. La SOSPECHA del autor es real: `store.append_record` filtra `anomaly_pixels` por distancia antes de F5 (`store.py:312-313`, `ENABLE_PIXEL_LEVEL_DISTANCE_FILTER=True` en el perfil, radio `radius_km`=25 desde `run_pipeline.py:250-251`, sobre `dist_km` medido desde el centro del catálogo, `process_viirs.py:727`). El probe no lo aplica, y C2 no lo puede ver (H5) | 3 |
| 6 | Fondo local con la máscara de alertas de la ruta publicada | CORRECTA | `alerta = entrada | en_cumulo` (`analisis_v2.py:236`); la entrada es la de la llamada que publicó. El halo del Test 1 entra al fondo (test `test_fondo_local_usa_la_mascara_de_la_ruta...`) | 1 |
| 7 | Contraste: restantes y píxel de control lejos | CORRECTA CON MATIZ | `pixel_control` (`analisis_v2.py:194-207`) y fondo simétrico (`:264-265`). Matiz: el control no está pareado en intensidad con el centro (H6) | 3 |
| 8 | Por volcán, mínimo y dejando uno fuera | CORRECTA CON MATIZ | `evaluar` (`analisis_v2.py:360-426`), `_estable` (`:350-357`). Aritmética revisada: con 3 volcanes evaluables el dejar-uno-fuera exige 3 de 3 (con 2 de 3, el volcán que sí cumple deja 1 < 2/3·2); con 4, basta 3 de 4. El destino sí es dejando uno fuera sobre el agregado (`:393-396`). El criterio es correcto, pero lo que juzga el destino es casi vacío (H3) | 2 |

## 2. Las tres desviaciones declaradas

1. **`final_hotspot_source` local y pisado por el ancla honesta.** CONFIRMADA. Asignado en `process_viirs.py:1724/1729/1735/1740/1745`, pisado en `:2014-2015` por `resolve_honest_anchor`, y lo que queda en el record (`:2096`) es la versión honesta. **La alternativa resuelve el problema original**: la ruta que publica se deduce de qué llamada produjo `primary_cluster`, y con el código de hoy eso equivale a la fuente interna (si la fuente es `test1` y hay píxeles, `:1889-1914` llama al cúmulo del Test 1 con máscara no vacía, `cluster_hotspots` devuelve al menos un cúmulo y `:1939` pisa). `resolve_test1_source_priority` es evidencia parcial, como dice el plan (el `and` de `:1712`).
2. **En la ruta del Test 1 los Tests 2 y 3 no alimentan el cúmulo.** CONFIRMADA. La entrada de `:1910` es `test1_hot_filtered` = `apply_contextual_test1_filter(test1_hot, dnti_ctx_hot, keep_peak_rc)` (`:1798-1799`), con `test1_hot = mask_contributing` (`:1112`). `fp_hot` sólo entra en `hot_mask_2d` (`:1262`, `:1320`) que alimenta `:1467`. La alternativa (alerta = entrada de la llamada publicada) es la lectura correcta de §6.6.
3. **`f5_core_vrp_mw` lo agrega `store.py`.** CONFIRMADA en `store.py:551-554`. **La alternativa no resuelve del todo**: entre `append_record` (`:272`) y `:551` hay mutaciones de `anomaly_pixels` (`:312-313` filtro por distancia; `:388-393` vaciado cuando el píxel más caliente queda lejos y no hay rescate). El vaciado no debería dispararse después del filtro, que recalcula el hotspot dentro del radio (`:252-257`); el filtro sí puede sacar píxeles en Puyehue (inner 20 km, vent a ~7 km del centro del catálogo). Ver H5.

## 3. Controles del instrumento

| control | ¿aprueba un instrumento correcto? | ¿puede aprobar uno roto? | Grav. |
|---|---|---|---|
| C1 captura ≥ 0,90 | No siempre: `identificar_publicado` devuelve `sin_primary_cluster` (`analisis_v2.py:71-72`) y eso cuenta como fallo del instrumento (`:316-319`). Si con el código de hoy 4 de 38 pasadas no tienen cúmulo, C1 = 0,895 y el veredicto es `INDETERMINADO:instrumento` sin que el instrumento haya fallado | Sí, parcialmente: una excepción dentro de `analizar` convierte la fila en `ok: False` (`probe_vecinos_v2.py:86-87`) y la saca del denominador de C1, C2 y C3 | 3 |
| C2 réplica F5 ≥ 0,95 | Sí, por construcción | **Sí**: `nucleo_f5` es copia línea a línea de `f5_core_vrp_mw` aplicada al mismo record (`analisis_v2.py:91-112` contra `f5_core.py:61-104`); "ambas None" cuenta como acierto (`:311`). No compara contra lo que `store.py` habría persistido | 3 |
| C3 rótulos = 1,0 | Sí, por construcción | **Sí, no puede fallar (A92)**: `incluido` sale de `en_cumulo`, construido con los mismos índices (`analisis_v2.py:232-235`, `:255`), y el centro se elige dentro de esos índices (`:240`). `consistencia_rotulos` (`:210-215`) compara la máscara consigo misma. Comprobado: 0 falsos de 6.000 resúmenes con `cluster_hotspots` real e índices reales (`taxonomia.py`). El test `test_consistencia_detecta_un_rotulo_roto` sólo alimenta la función con entradas que el ensamblado nunca produce | 4 |

## 4. Criterio pre-registrado

**Alcanzable, pero no discrimina el fenómeno en el destino.**

- *Estrato nevado*: sin candidatos (sólo 2 controles de Chaitén), `INDETERMINADO:pocos_volcanes` por construcción, declarado en el plan §9. El total es, en la práctica, el estrato focal.
- *Focal*: 5 volcanes con 6 candidatos cada uno; hacen falta ≥ 3 volcanes con ≥ 3 pasadas válidas. Riesgos (SOSPECHA, no medible sin correr): los 6 candidatos de Lastarria entran por el pico (`dist_crater_km` 1,08 a 2,68) y dependen de que el pico de hoy quede a ≤ 0,75 km del punto OSF, que salta en pasos de ~375 m; y 13 de 30 candidatos tienen `Npix = 3`, que quedan fuera si hoy el núcleo F5 cuenta 3 o más (`fila_valida`, `analisis_v2.py:301-303`).
- **Camino a `PATRON` sin fenómeno (H3)**: para un vecino 8-conexo del centro, `alertado_fuera_del_cumulo` es imposible en las dos rutas (las dos llamadas usan conectividad 8 sobre su entrada, `clustering.py` `connectivity=8` por defecto y `:1912` explícito; un vecino alertado cae en la misma componente que el centro). En la ruta contextual `marcado ⊆ entrada` (`detection_context.py:948` devuelve `active_mask | newly_active`, y con los flags de hoy nada filtra entre `:1287` y `:1467`), así que `contextual:marcado_y_quitado` también es imposible. Todo vecino no incluido de la ruta contextual sale `nunca_marcado`, haya o no calor en él. Comprobado con `taxonomia.py`: 7.556 `incluido`, 40.426 `nunca_marcado`, 0 de los otros dos. Si ≥ 2/3 de los volcanes publican por la ruta contextual, `PATRON:contextual:nunca_marcado` sale seguro. `justifica_brazo` queda sostenido sólo por el contraste, y el contraste tiene el sesgo de H6.

## 5. Tests y muestra

- `python -m pytest tests/test_probe_vecinos_v2_s141.py -q -p no:cacheprovider`: **33 passed** (el plan §10 habla de 31).
- Suite completa `python -m pytest tests/ -q -p no:cacheprovider`: **1424 passed, 14 skipped, 2 xfailed** en 65 s.
- `muestra.py --osf data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv` corrió sin red (rc=0) y regeneró `pasadas.json`, `excluidas.json` y `muestra_resumen.json` **byte a byte idénticos** a los commiteados.
- Exclusiones (A93): distancias por haversine en grados a km (`f5_core._hav_km`), desde el punto `LAT/LON` del OSF hasta (a) `vent_lat/vent_lon` de `load_volcanoes` y (b) el píxel pico del núcleo F5 del record pareado con `nearest` (±10 min, `descomponer_magnitud_osf.py:92-97`), el mismo pareo de `build`. El `merge` por `(t_osf, vol, res)` es seguro: 0 claves duplicadas en el OSF filtrado y 0 de 329 candidatos con clave múltiple. Matiz de "desde qué punto": en Isluga y Lastarria `vent_lat/vent_lon` es el punto del catálogo redondeado (-19,15/-68,83 y -25,168/-68,507), no el cráter; 11 de las 13 pasadas que entran sólo por el pico son de esos dos volcanes (H8). En Láscar los 6 candidatos tienen el mismo `LAT/LON` del OSF (-23,36212691, -67,73252062), coherente con la SOSPECHA de cuantización del plan §6.

## 6. Runner y yml

- **stdout**: `probe_vecinos_v2.py` no envuelve (`:24-26`); `probe_etapas.py:35` envuelve una sola vez al importarse; en la cadena de imports no hay otro `TextIOWrapper` (`grep` sobre `scripts/run_pipeline.py`, `pipeline/*.py`, `experiments/_s135_probe_etapas/probe_etapas.py` y `experiments/_s141_fase1_probe_v2/*.py`: sólo `juntar.py:54`, dentro de `main`, que el runner no importa). `test_runner_como_script_no_cierra_stdout` pasa como subproceso. Queda sin cubrir la ruta después de `auth()` (el test sale antes), pero no hay envoltorios en `auth`/`load_volcanoes` según el grep.
- **A89**: los siete nombres parcheados se importan al tope de `process_viirs.py` (`:53`, `:193`, `:201-211`, `:212-213`) y se llaman por nombre global dentro de `calculate_vrp`; no hay imports locales de ellos (los indentados son `h5py`, `vrptir`, `haversine_km`, `datetime`). El runner llama `pv.calculate_vrp` vía `s135.correr_pasada` (`probe_etapas.py:204`), así que el envoltorio de `calculate_vrp` corre. `bt` capturado por referencia no se modifica en sitio dentro de `calculate_vrp` (las escrituras `bt[...] =` están en la lectura del L1B, `:380-393`).
- **yml**: `"on":` entre comillas (`:8`), `set -o pipefail` antes del `tee` (`:48`), sin `git push` ni `contents: write`, matriz igual a los volcanes de la muestra (test). `timeout-minutes: 120` holgado frente a los ~9 min del v1.

## 7. Hallazgos propios por gravedad

**Gravedad 4**

- **H1. El filtro de foco admite focos distintos y la re-medición es nula para 25 de 38 pasadas.** Puyehue 2025-07-18 05:24: MIROVA en el cráter, nuestro pico a 16,39 km (`pasadas.json`). Con inner 20 km nuestro cúmulo puede estar en otro lugar del complejo y la pasada será válida siempre, porque `foco_ok = min(d_osf, d_crater)` (`analisis_v2.py:275`) y `d_crater` no depende de la corrida. Es V5 del v1 en espejo: vecinos de nuestro pico comparados con la brecha de otro foco.
- **H2. C3 no puede fallar** (§3). Un control que aprueba por construcción da permiso a cualquier error de alineación entre índices, BT y coordenadas.
- **H3. El destino está determinado antes de correr** (§4). La pregunta "dónde se pierden los vecinos" queda respondida analíticamente para la ruta contextual (`nunca_marcado`) y el `PATRON` no depende de que los vecinos estén tibios. El mapeo de "Qué justifica" del plan §4 para `*:alertado_fuera_del_cumulo` (conectividad o selección del cúmulo) nombra un resultado imposible.

**Gravedad 3**

- **H4. C1 mezcla "sin cúmulo hoy" con "instrumento no identifica", y una excepción en `analizar` esconde la pasada de los controles** (`analisis_v2.py:71-72`, `:316-319`; `probe_vecinos_v2.py:86-87`).
- **H5. C2 es tautológico y el probe no reproduce el filtro de `store.py:312-313`** antes de F5. Afecta sobre todo a Puyehue (inner 20 km contra radio 25 km medido desde el centro del catálogo).
- **H6. Contraste sin pareo de intensidad.** El centro es el píxel de mayor VRP de un cúmulo detectado; el control es el píxel más caliente no alertado del anillo 3 a 6 km (`analisis_v2.py:194-207`), normalmente apenas sobre su entorno. Cualquier píxel caliente reparte calor a sus vecinos por la respuesta espacial del sensor, así que `VECINOS_TIBIOS` con 1,0 K es casi seguro en toda pasada con detección real; no separa "vecinos que MIROVA suma" de "vecinos de un píxel más caliente que el control". No produce un falso fenómeno físico, pero hace que el umbral no informe.

**Gravedad 2**

- **H7. Tres "picos" distintos.** La muestra filtró con el pico del núcleo F5 persistido (máximo VRP entre `anomaly_pixels` dentro de `inner` del centroide, `muestra.py:117-129`), que puede estar fuera del cúmulo; la corrida usa el máximo de `vrp_per_pixel` dentro del cúmulo publicado; y `n_publicado_hoy` cuenta el núcleo F5, que puede sumar píxeles fuera del cúmulo. `incluido` no es lo mismo que "sumado en lo publicado".
- **H8. "Cráter" de Isluga y Lastarria es el punto del catálogo** (`load_volcanoes`: `vent_lat == lat`). Las columnas `dist_crater_km` y `dist_osf_crater_km` de esos volcanes miden a un punto nominal.
- **H9. Alcanzabilidad frágil del estrato focal** (§4, SOSPECHA): Lastarria depende entero del pico de hoy; 13 candidatos con `Npix = 3`.
- **H10. Flags sólo impresos, no afirmados** (`probe_vecinos_v2.py:71`). H3 depende de que `ENABLE_FINAL_PIXEL_FILTER`, `PATH_D_REQUIRES_COVALIDATION`, `ENABLE_EXCLUDE_ZONES`, `ENABLE_SECOND_PASS_INTRA_RADIO_GATE` sigan en False (hoy lo están, leído de `pipeline.process_viirs` con `VRP_PROFILE=mirova_equivalent`).
- **H11. El criterio de fondo suma ruido positivo** (D2 del v1 sigue en `aporte_mw`, `analisis_v2.py:58-62`, y `:271`). No decide `justifica_brazo`.

**Gravedad 1**

- **H12.** Plan §10 dice 31 tests; hay 33.

## 8. Cambios mínimos antes de despachar

1. `foco_ok` de la corrida: exigir `dist_centro_osf_km <= 0,75` (sin la rama del cráter), o sacar de la muestra las pasadas con `dist_pico_km > 0,75`. Hoy es una: Puyehue 2025-07-18 05:24.
2. Reemplazar C3 por un control que pueda fallar: por ejemplo, que `bt[ij]` en los índices publicados coincida (±0,01 K) con `bt_k` de los `anomaly_pixels` del record en la misma lat/lon, y que `len(indices) == primary_cluster.n_pixels`.
3. Reescribir el pre-registro del destino antes de ver datos: declarar que `alertado_fuera_del_cumulo` y `contextual:marcado_y_quitado` son imposibles, y que `PATRON` no cuenta como evidencia de etapa; si se quiere la etapa, registrar para cada vecino el margen contra el umbral que lo dejó fuera (dNTI contra C1/C2, BT contra la compuerta).
4. C1: denominador = pasadas `ok` con `primary_cluster` no nulo, contando aparte `sin_primary_cluster`; y que una excepción en `analizar` conserve `ok` del pipeline y marque `error_analisis`, contando en C1.
5. Aplicar sobre una copia del record el filtro `store._filter_pixels_by_distance(rec, radius_km)` antes de `f5_core_vrp_mw`, o declarar la limitación.
6. Afirmar (no sólo imprimir) los flags de los que depende la taxonomía.

Recomendados, no bloqueantes: parear el píxel de control por exceso del centro (H6) o reportar el exceso del centro junto al contraste; unificar la definición de pico entre muestra y corrida (H7).

## 9. VERIFICADO LIMPIO

- Identificación del cúmulo publicado contra `primary_cluster` por `n_pixels` y centroide redondeado: equivalente exacto a qué llamada publica con el código de hoy.
- Las tres desviaciones declaradas son ciertas en el código de hoy.
- Ruta distinguida por `connectivity=` y segundo pase por `active_mask=`: coincide con `process_viirs.py:1467-1472`, `:1910-1914`, `:1149`, `:1164`, `:1287`.
- Nombres parcheados resueltos por global del módulo; ninguno reimportado dentro de `calculate_vrp`.
- `bt`, `lat`, `lon` y máscaras capturados sin mutación posterior; las máscaras se copian.
- Selector de muestra reproducible sin red y byte a byte igual; pareo con el OSF sin claves duplicadas; ninguna pasada del v1 repetida.
- Runner sin doble envoltorio de stdout; yml con `pipefail`, `"on"` y sin push.
- Aritmética del dejar-uno-fuera y de los mínimos por volcán y por estrato.
- Tests del v2 (33) y suite completa (1424) en verde.
