# Fase 1, paso 1 (v2): instrumento del vecino del foco, VIIRS 375 m

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans. Probe de sólo lectura (A75):
> no toca `pipeline/`, `store.py`, `pipeline/profiles/` ni `data/`. Corre sólo en CI.

**Antecedente:** el v1 (`docs/superpowers/plans/2026-09-15-fase1-probe-vecinos.md`, run 34929024703) dio
INDETERMINADO y el verificador con contexto limpio (`experiments/_s141_fase1_probe/VERIFICADOR.md`) encontró
ocho defectos del instrumento (§4) y ocho correcciones necesarias (§6). Este plan es el instrumento v2 y su
pre-registro. **Muestra nueva**: las 40 pasadas del v1 quedan excluidas por construcción.

## 1. Por qué (el fenómeno antes que el código)

Un foco incandescente chico (lago de lava, domo, fumarola caliente) no cabe en un píxel VIIRS de 375 m: su
calor se reparte entre el píxel donde cae y los vecinos, por la respuesta espacial del sensor y porque el foco
rara vez cae centrado. MIROVA suma esos vecinos tibios (3 o más píxeles en el OSF) y nosotros publicamos uno;
por eso nuestra magnitud queda en ~0,66 de la suya (S139). La Fase 1 quiere saber **dónde** se pierden esos
vecinos dentro de nuestro ensamblado, para que el A/B toque la etapa correcta y no otra.

El v1 no pudo decirlo por dos razones físicas y dos de código:

- **No siempre mirábamos el mismo foco.** En Nevados de Chillán el píxel caliente de MIROVA estaba a 13 a 17 km
  del cráter: MIROVA sumaba otra anomalía. Una brecha de magnitud entre dos focos distintos no es de vecinos.
- **Vecinos tibios por azar.** En un campo con ruido y relieve, los vecinos más calientes de cualquier píxel
  superan a su entorno. Sin un píxel de control lejos del foco, "los vecinos están tibios" no distingue el
  derrame térmico del foco de la simple selección de los más calientes.
- **Dos rutas en paralelo leídas como fila.** La ruta contextual (Tests 2 y 3, segundo pase, cúmulo) y la del
  Test 1 (disco integrado, filtro contextual con `keep_peak`, cúmulo) no son etapas sucesivas: sólo una publica.
- **La máscara del Test 1 no es un test por píxel**: marca todo exceso sobre la mediana del anillo dentro de 3 km.

## 2. Cómo arma hoy el pipeline el cúmulo publicado (trazado en esta sesión, A6 y A89)

Perfil `mirova_equivalent`, flags leídos de `pipeline.process_viirs` con `VRP_PROFILE=mirova_equivalent`:
`ENABLE_FIRST_PASS_TESTS_2_AND_3=True`, `ENABLE_SECOND_PASS_ADJACENT=True`, `ENABLE_TEST1_CONTEXTUAL_FILTER=True`,
`ENABLE_TEST1_CONTEXTUAL_KEEP_PEAK=True`, `ENABLE_TEST1_PIXEL_FILTER=False`, `ENABLE_TEST1_SPATIAL_CORE=False`,
`ENABLE_TEST1_LAVA_LAKE_EQ16=False`, `ENABLE_ETI_QUADRATIC_SCENE=False`, `PATH_D_ATM_GATE_TBG_MIN_K=None`,
`ENABLE_SINGLE_PIXEL_SUB_MW_MODE=True` (`SINGLE_PIXEL_MAX_CLUSTER_PIXELS=3`), `ENABLE_HONEST_ANCHOR=True`.

| paso | dónde | qué |
|---|---|---|
| dNTI contextual (8 vecinos) | `process_viirs.py:1026-1052` | `dnti_ctx_hot`, test por píxel |
| Test 1 integrado | `:1099-1121` | `mask_contributing`: exceso sobre el anillo en el disco, **no** es test por píxel |
| primer pase Tests 2 y 3 | `:1240-1263` | `hot_mask_2d = fp_hot` |
| segundo pase | `:1287-1306` | llamada con `active_mask=` por nombre (las de `:1149/:1164` son posicionales y no corren: ETI de escena apagado) |
| **cúmulo contextual** | `:1467-1472` | `cluster_hotspots(hot_mask_2d, ...)` **sin** `connectivity=` |
| single pixel mode | `:1522-1527` | cambia `vrp_mw`, conserva `n_pixels` y centroide (`single_pixel_mode.py:149-184`) |
| fuente interna | `:1712-1745` | `final_hotspot_source` = test1 / eruption / vent |
| filtro contextual con pico | `:1788-1799` | `apply_contextual_test1_filter(test1, dnti_ctx, keep_peak_rc)` sólo si la fuente interna es test1 |
| **cúmulo Test 1** | `:1910-1914` | `cluster_hotspots(test1_hot_filtered, ..., connectivity=8, ...)`; si devuelve algo, **pisa** `primary_cluster` (`:1939`) |
| ancla honesta | `:2014-2015` | pisa `final_hotspot_source` del record; la fuente interna se pierde |
| núcleo F5 | `store.py:551-554` | `f5_core_vrp_mw(record, inner_radius_km)`, **no** dentro de `calculate_vrp` |

## 3. Las ocho correcciones de `VERIFICADOR.md` §6, cómo se implementan

1. **Posición del foco de MIROVA.** `muestra.py` exige que el punto `LAT/LON` del OSF esté a ≤ 0,75 km del
   cráter (`vent_lat/vent_lon` de `volcanoes.yaml`) **o** del píxel pico persistido del núcleo F5 del record
   pareado; las que no, van a `excluidas.json` con motivo y distancias. En la corrida se **vuelve a medir**
   contra el píxel pico de hoy (`foco_ok` en el resumen): una pasada que pasó el filtro con el record del
   backfill pero no con el de hoy sale del criterio y se cuenta aparte.
2. **Rótulo dentro de la ruta publicada.** Cada vecino recibe uno de cuatro rótulos (`incluido`,
   `alertado_fuera_del_cumulo`, `marcado_y_quitado`, `nunca_marcado`) calculados con las máscaras **de la ruta
   que publicó**, y el destino se nombra `ruta:rótulo`. "Marcado" es un test por píxel: en la ruta contextual,
   primer pase ∪ salidas del segundo pase llamado con `active_mask=`; en la del Test 1, la máscara dNTI
   contextual que entra al filtro (`:1798`). **`mask_contributing` nunca cuenta como marcado**; se guarda como
   dato aparte.
3. **Evidencia del cúmulo publicado.** Cada llamada a `cluster_hotspots` se guarda con su ruta (con o sin
   `connectivity=`), su máscara de entrada y los índices de su cúmulo 0. El publicado se **identifica** por
   coincidencia exacta con el `primary_cluster` del record (`n_pixels` y centroide redondeado a 5 decimales,
   que `single_pixel_mode` no toca). Sin coincidencia, o con dos llamadas que coinciden con índices distintos,
   la pasada queda "no identificada" o "ambigua" y no entra al criterio. Booleanos por etapa que corrió
   (`corrio`): primer pase, segundo pase por nombre, Test 1 (y si disparó), filtro contextual, cúmulo
   contextual, cúmulo Test 1, y el valor devuelto por `resolve_test1_source_priority`.
4. **Centro = píxel pico del cúmulo publicado**: el de mayor VRP por píxel (el array `vrp_per_pixel` que
   recibió esa llamada), desempate por BT. La distancia del centro al punto del OSF se guarda como variable de
   pareo, no se usa para elegir el centro.
5. **Lo que se publica hoy, en la misma corrida.** `f5_core_vrp_mw(record, inner_radius_km)` del pipeline y una
   réplica que además devuelve el conteo; `n_publicado_hoy` = conteo del núcleo F5 si existe, si no 1 cuando
   `single_pixel_mode` es True, si no `primary_cluster.n_pixels`. La brecha es VRP del OSF menos el publicado
   de hoy (F5 si existe, si no `pc.vrp_mw`, regla A10).
6. **Fondo local con la máscara de alertas de la ruta publicada**: la máscara de entrada de la llamada que
   publicó. Ver §5, punto 2: para la ruta del Test 1 no coincide con "Tests 2/3 más segundo pase".
7. **Contraste.** Exceso sobre fondo local (a) de los `Npix−1` vecinos más calientes, (b) de los vecinos
   restantes, y (c) de los `Npix−1` vecinos más calientes de un **píxel de control**: el más caliente entre
   los que están a 3 a 6 km del centro, fuera de la máscara de alertas y sin vecinos alertados. Para que el
   contraste sea simétrico, el píxel de control se trata como alertado al calcular el fondo de sus vecinos,
   igual que el centro.
8. **Por volcán, con mínimo y dejando uno fuera.** Ver §4.

## 4. Criterio pre-registrado (no se cambia después de ver datos)

Constantes en `experiments/_s141_fase1_probe_v2/analisis_v2.py`; un test las fija.

**Pasada válida para el criterio**: `ok`, clase candidato, grilla consistente, publicado identificado y no
ambiguo, `foco_ok` con el pico de hoy, y `n_publicado_hoy < Npix` del OSF (hoy seguimos publicando menos
píxeles que MIROVA). Las demás se cuentan por motivo.

**Control del instrumento** (sobre todas las pasadas `ok`, candidatos y controles; umbrales alcanzables por
construcción, porque un instrumento correcto da 1,0 en los tres):

- C1, captura: fracción de pasadas con publicado identificado y no ambiguo ≥ 0,90.
- C2, réplica F5: fracción de identificadas donde la réplica y `f5_core_vrp_mw` coinciden (ambas None, o
  |Δ| ≤ 1e-3 MW) ≥ 0,95.
- C3, rótulos: en todas las pasadas resumidas, `incluido` ⇔ índice en el cúmulo publicado, y el centro está
  en él. Tiene que ser 1,0.

Si falla alguno: **INDETERMINADO:instrumento**.

**Por volcán** (evaluable con ≥ 3 pasadas válidas):

- *destino*: entre los vecinos calientes no incluidos de todas sus pasadas, el `ruta:rótulo` con fracción
  ≥ 0,60; si no, DISPERSO.
- *contraste*: mediana por pasada del exceso de los calientes menos mediana por pasada del exceso de los
  calientes del control. ≥ 1,0 K: VECINOS_TIBIOS; si no, SIN_CONTRASTE.
- *fondo*: mediana de (aporte con fondo local de los calientes no incluidos) / brecha. ≥ 0,5 CIERRA, < 0,2
  NO_CIERRA, si no PARCIAL.

**Por estrato (focal, nevado) y total** (se necesitan ≥ 3 volcanes evaluables; si no,
**INDETERMINADO:pocos_volcanes**):

- destino **PATRON:ruta:rótulo** si el destino agrupado de todos los volcanes tiene fracción ≥ 0,60, al menos
  2/3 de los volcanes evaluables tienen ese mismo destino, y al sacar cada volcán por turno el destino agrupado
  de los restantes no cambia. Si no, HETEROGENEO.
- contraste VECINOS_TIBIOS (o SIN_CONTRASTE) si al menos 2/3 de los volcanes lo tienen y sigue siendo así al
  sacar cada volcán por turno; si no, HETEROGENEO.
- fondo: la clase que comparten al menos 2/3 de los volcanes, estable al sacar cada uno; si no, HETEROGENEO.

**Qué justifica.** Sólo `PATRON` con `VECINOS_TIBIOS` justifica diseñar un brazo de A/B, y sobre la etapa que
nombra el destino: `contextual:marcado_y_quitado` (algo entre el segundo pase y el cúmulo),
`test1:marcado_y_quitado` (no debería ocurrir: el filtro conserva Test 1 ∩ dNTI; si aparece, es la
intersección con el disco del Test 1), `*:alertado_fuera_del_cumulo` (conectividad o selección del cúmulo),
`*:nunca_marcado` (umbral o fondo de la detección). SIN_CONTRASTE refuta que el hueco sean vecinos tibios
detectables a 375 m; no justifica brazo.

**Límites que se escriben antes de correr.** Los `Npix` de MIROVA están en su grilla remuestreada (D17): que
sean nuestros `Npix−1` vecinos nativos más calientes es un supuesto. El umbral de 1,0 K es una elección redonda,
no un valor instrumental medido: el contraste crudo se reporta siempre. Los controles de clase (publicábamos
tantos píxeles como MIROVA en el backfill) sólo entran a C1 a C3 y se describen aparte; no deciden.

## 5. Correcciones de §6 que no se pueden implementar tal como están escritas

1. **§6.2 "guardar la fuente interna (`final_hotspot_source` antes del ancla honesta)".** Es una variable local
   asignada en `process_viirs.py:1724/1729/1735/1740` y pisada en `:2014-2015`; ninguna llamada la recibe, así
   que un monkeypatch no la ve. Alternativa: se identifica la **consecuencia observable** (qué llamada a
   `cluster_hotspots` produjo el `primary_cluster` publicado, punto 3) y se guarda el valor que devuelve
   `resolve_test1_source_priority` (`:1712`) como evidencia parcial; es parcial porque el `and` de `:1712` no la
   llama cuando `test1_centroid_lat` es None.
2. **§6.6 "fondo local con Tests 2/3 más segundo pase de la ruta ganadora".** Vale para la ruta contextual, donde
   la entrada del cúmulo (`:1467`) es `hot_mask_2d` tras el segundo pase (`:1287`). En la ruta del Test 1 los
   Tests 2/3 **no** alimentan el cúmulo publicado: su entrada es `test1_hot_filtered` = Test 1 ∩ dNTI contextual
   más el pico (`:1798-1799`, `:1910`). Alternativa, implementada: la máscara de alertas es la **entrada de la
   llamada que publicó**, que en la ruta contextual es exactamente lo que pide §6.6.
3. **§6.5 "capturar `f5_core_vrp_mw`".** No existe en el record que devuelve `calculate_vrp`: lo agrega
   `store.py:552-554`. El probe lo calcula con la misma función sobre el record devuelto. SOSPECHA no
   verificada: que algo de `store.append_record` antes de `:551` modifique `anomaly_pixels` o
   `primary_cluster`; sólo leí `store.py:530-564`.

## 6. SOSPECHAS del instrumento (no verificadas)

- La cuantización de `LAT/LON` del OSF: si MIROVA informa el centro de una celda de su grilla (D15), el radio de
  0,75 km podría excluir focos que sí son el mismo. Por eso `excluidas.json` guarda las distancias.
- Que la ruta se reconozca por la presencia del argumento `connectivity=` depende del código de hoy; un test
  (`test_a89_llamadas_de_cluster_distinguibles`) cuenta con frontera de palabra que sólo la llamada del Test 1
  lo pasa, y falla si eso cambia.
- Que `bt`, `lat`, `lon` y las máscaras compartan grilla lo verificó V1 para el perfil de hoy; el probe lo vuelve
  a comprobar por forma en cada pasada.

## 7. Archivos

| archivo | rol |
|---|---|
| `experiments/_s141_fase1_probe_v2/muestra.py` | selección con filtro por posición del foco de MIROVA y exclusión del v1 |
| `experiments/_s141_fase1_probe_v2/captura.py` | envoltorios que registran llamadas por etapa (puros, testeables) |
| `experiments/_s141_fase1_probe_v2/analisis_v2.py` | publicado, núcleo F5, rótulos, fondo, contraste, criterio |
| `experiments/_s141_fase1_probe_v2/probe_vecinos_v2.py` | runner en CI (reutiliza descarga y parches de S135) |
| `experiments/_s141_fase1_probe_v2/juntar.py` | junta artefactos y aplica el criterio (única fuente de números, S91) |
| `tests/test_probe_vecinos_v2_s141.py` | tests |
| `.github/workflows/probe-s141-vecinos-v2.yml` | workflow de sólo lectura, `set -o pipefail` |

## 8. Tareas

- [ ] **T1 tests en rojo**: escribir `tests/test_probe_vecinos_v2_s141.py`, correrlo y leer que cada test falla
  por la razón que dice (módulo inexistente, yml inexistente), no por un error de sintaxis del test.
- [ ] **T2 muestra** (`muestra.py`), verde; correr localmente con `--osf` apuntando al OSF del checkout principal
  y commitear `pasadas.json` y `excluidas.json`.
- [ ] **T3 captura y análisis**, verde.
- [ ] **T4 runner, juntar y workflow**, verde; el test del runner lo corre como script en un subproceso.
- [ ] **T5 suite completa** `python -m pytest tests/ -q -p no:cacheprovider`.
- [ ] **T6 (orquestador, fuera de esta tarea)**: anotar la hipótesis en `docs/HYPOTHESIS_LOG.md`, mergear,
  despachar, juntar con `juntar.py`, verificador con contexto limpio.

## 9. Muestra (se completa en T2 con la salida de `muestra.py`, sin mirar resultados del probe)

Ver §10, escrita por el script de selección.
