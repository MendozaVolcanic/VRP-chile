# Fase 1, paso 1 (v2): instrumento del vecino del foco, VIIRS 375 m

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans. Probe de sólo lectura (A75):
> no toca `pipeline/`, `store.py`, `pipeline/profiles/` ni `data/`. Corre sólo en CI.

**Antecedentes.** El v1 (`docs/superpowers/plans/2026-09-15-fase1-probe-vecinos.md`, run 34929024703) dio
INDETERMINADO y su verificador (`experiments/_s141_fase1_probe/VERIFICADOR.md`) pidió ocho correcciones (§6).
La primera versión de este v2 (commit `1e5a6b7f9`, PR #675) las implementó, y un verificador con contexto
limpio antes de correrla (`experiments/_s141_fase1_probe/VERIFICADOR_V2_PRE_CORRIDA.md`) dictaminó
DESPACHAR CON CAMBIOS con tres defectos de gravedad 4 (H1, H2, H3). **Este plan reemplaza el pre-registro de
esa primera versión**, que no llegó a correrse: no hay datos del probe que mirar.

## 0. Qué cambió y por qué (H3 cambia la pregunta)

La primera versión preguntaba "¿en qué etapa del ensamblado se pierde cada vecino tibio?" y rotulaba su
destino (`incluido`, `alertado_fuera_del_cumulo`, `marcado_y_quitado`, `nunca_marcado`). El verificador
mostró que la respuesta estaba fijada antes de correr: dos de los cuatro destinos son imposibles por
construcción (§3) y todo vecino no incluido de la ruta contextual sale `nunca_marcado`, haya calor o no.
O sea, **si un vecino tibio no está en nuestro cúmulo, es porque la detección no lo alertó**; el ensamblado
no puede perderlo. La pregunta pasa a ser:

> **¿Qué test de la detección deja fuera a los vecinos tibios del foco, y por cuánto?**

## 1. Por qué (el fenómeno antes que el código)

Un foco incandescente chico (lago de lava, domo, fumarola caliente) no cabe en un píxel VIIRS de 375 m: su
calor se reparte entre el píxel donde cae y los vecinos, por la respuesta espacial del sensor y porque el foco
rara vez cae centrado. MIROVA suma esos vecinos tibios (3 o más píxeles en el OSF) y nosotros publicamos uno;
por eso nuestra magnitud queda en ~0,66 de la suya (S139). Un vecino tibio puede quedar fuera por dos
familias de razones físicas distintas, y cada una pide un A/B distinto:

- **Contraste espacial insuficiente.** Los Tests 2 y 3 comparan el índice del píxel con la media de sus 8
  vecinos. Un píxel pegado al foco tiene al foco entre sus vecinos, así que la media sube y su contraste baja.
  El segundo pase existe justo para eso (saca a los activos de la media), pero exige superar el umbral igual.
- **Compuerta de temperatura.** El primer pase y el dNTI contextual exigen `bt > t_bg + 3 K` (D22). En un
  nevado, un vecino que recibe una fracción del calor del foco puede quedar bajo esa cota.

Y hay una tercera cuestión, que no deja fuera a nadie pero cambia la magnitud: **el fondo** (D25). Nosotros
restamos el anillo de 5 a 25 km (o el fondo del Test 1); MIROVA resta la media de los vecinos no alertados.

## 2. Cómo arma hoy el pipeline el cúmulo publicado (trazado en esta sesión, A6 y A89)

Perfil `mirova_equivalent`, flags leídos de `pipeline.process_viirs` y afirmados por el runner (`flags.py`).

| paso | dónde | qué |
|---|---|---|
| dNTI contextual dual-ROI | `process_viirs.py:1034-1043`; `detection_context.py:241-284`, `:359-378` | `dnti > C1` (sin rama estadística) y `bt > t_bg + bt_sanity_k`; filtros no aptos §267-273 |
| Test 1 integrado | `process_viirs.py:1099-1121` | `mask_contributing`: exceso sobre el anillo en el disco, **no** es test por píxel |
| primer pase Tests 2 y 3 | `process_viirs.py:1240-1263`; `detection_context.py:463-533` | `dNTI > combinar(C1, mu + C2 sigma)` y lo mismo con dETI, `combinar = min` hoy (`:510`), y `bt > t_bg + 3 K` (`:532`) |
| segundo pase | `process_viirs.py:1287-1306`; `detection_context.py:884-948` | Tests 2 y 3 sin los activos en la media, **sin compuerta de BT** (`:939-940`); devuelve `active_mask \| newly_active` (`:948`) |
| cúmulo contextual | `process_viirs.py:1467-1472` | `cluster_hotspots(hot_mask_2d, ...)` sin `connectivity=` |
| filtro contextual con pico | `process_viirs.py:1788-1799` | Test 1 ∩ dNTI contextual, más el pico |
| cúmulo Test 1 | `process_viirs.py:1910-1914` | `connectivity=8`; si devuelve algo pisa `primary_cluster` (`:1939`) |
| agrupamiento | `clustering.py:91-96` | `ndi_label` con estructura 3x3 completa: componentes 8-conexas |
| filtro por distancia | `store.py:312-313` (`_filter_pixels_by_distance`, `:217-269`) | antes de F5; radio `radius_km` (`run_pipeline.py:250-251`), `dist_km` desde el centro del catálogo |
| núcleo F5 | `store.py:551-554` | `f5_core_vrp_mw(record, inner_radius_km)` |

## 3. Resultados imposibles por construcción (se declaran antes de correr)

1. **"Alertado fuera del cúmulo" es imposible** para un vecino del centro. `cluster_hotspots` etiqueta
   componentes conexas con estructura 3x3 completa (`clustering.py:91-96`) en las dos llamadas (la contextual
   usa el valor por defecto `connectivity=8`, `clustering.py:38`; la del Test 1 lo pasa, `process_viirs.py:1912`).
   Un vecino alertado cae en la misma componente que el centro, y el centro está en el cúmulo publicado.
   Probado en `test_imposible_por_construccion_vecino_alertado_fuera_del_cumulo`.
2. **"Marcado y quitado" es imposible en la ruta contextual.** El segundo pase devuelve
   `active_mask | newly_active` (`detection_context.py:948`) y con los flags de hoy nada filtra entre
   `process_viirs.py:1287` y `:1467` (S85, filtro final, exclusión y co-validación en False, afirmados).
3. **En la ruta contextual con segundo pase, la compuerta de BT no puede ser la única limitante.** El segundo
   pase no tiene compuerta (`detection_context.py:939-940`): un vecino que el primer pase dejó fuera sólo por BT
   entra en el segundo si su dNTI y dETI (sin el foco en la media) superan el umbral. Probado en
   `test_imposible_por_construccion_la_compuerta_sola_tras_el_segundo_pase`. Por eso, en esa ruta la limitante
   sólo puede ser `dnti_2p`, `deti_2p` o ambas; la compuerta del primer pase se reporta aparte como
   `solo_compuerta_1p` (lente de D22), sin decidir nada.
4. **En la ruta del Test 1, el pico siempre está incluido** (`keep_peak_rc`, `process_viirs.py:1792-1799`).

Consecuencia: el rótulo de destino no distingue nada y se elimina. Lo que queda por medir es qué test falla y
por cuánto.

## 4. El instrumento

**Las ocho correcciones de `VERIFICADOR.md` §6** (se mantienen): muestra filtrada por la posición del foco de
MIROVA; lectura dentro de la ruta que publicó; eventos por llamada con booleanos por etapa y el cúmulo
publicado identificado contra el `primary_cluster` del record; centro = píxel de mayor VRP del cúmulo
publicado; núcleo F5 y brecha de la misma corrida; fondo local con la máscara de entrada de la llamada que
publicó; contraste con los vecinos restantes y con un píxel de control a 3 a 6 km; criterio por volcán con
mínimo y dejando uno fuera.

**Cambios mínimos del verificador pre-corrida (§8), implementados:**

1. **H1, foco contra nuestro centro.** `muestra.py` exige el punto del OSF a ≤ 0,75 km del píxel pico
   persistido (sin rama del cráter; `sin_pico_persistido` es motivo de exclusión) y `foco_ok` en la corrida
   exige `dist_centro_osf_km <= 0,75`. La distancia al cráter queda sólo como descripción.
2. **H2, C3 que puede fallar.** `alineacion_bt`: `len(indices) == primary_cluster.n_pixels` y la BT de la grilla
   en cada índice publicado igual (±0,006 K, `bt_k` va con 2 decimales) a `bt_k` del `anomaly_pixels` del record
   en la misma lat/lon. Se exige presencia sólo a los píxeles que el record debía guardar (VRP > 0 y, si la lista
   llegó al tope de 100, VRP sobre el mínimo guardado). `test_c3_alineacion_bt_falla_ante_un_indice_corrido`
   comprueba que un índice corrido una fila da False.
3. **H3, pre-registro reescrito** (§3 y §5): márgenes por test en vez de destino.
4. **H4, C1.** Denominador = pasadas `ok` con `primary_cluster`; `sin_primary_cluster` se cuenta aparte. Una
   excepción en el análisis conserva `ok` del pipeline, marca `error_analisis` y cuenta como falla de C1.
5. **H5, filtro de store.py.** `aplicar_filtro_store` corre `store._filter_pixels_by_distance` sobre una copia del
   record, con el mismo flag y radio que usa `run_pipeline`, antes de F5 y de la réplica.
6. **H10, flags afirmados.** `flags.verificar_flags(pv)` al inicio del runner; si un flag del que dependen las
   imposibilidades cambió, el runner se detiene antes de bajar un granule.

**Márgenes (`margenes.py`).** Cada test se recalcula con los argumentos con que el pipeline llamó a la
función, enlazados con su firma real (`inspect.signature`, así los valores por defecto son los de la función).
Para cada píxel (centro y 8 vecinos) se guarda índice, umbral efectivo, margen (índice menos umbral; compuerta
en K) y `replica_ok` (el "pasa" recalculado contra la máscara que devolvió la función). Los tests
`test_margenes_*_replican_la_funcion_real` corren las funciones reales sobre escenas sintéticas y exigen
réplica exacta en todos los píxeles; `test_la_replica_puede_fallar` muestra que C4 no aprueba por construcción.

## 5. Criterio pre-registrado (no se cambia después de ver datos)

Constantes en `experiments/_s141_fase1_probe_v2/analisis_v2.py`; `test_constantes_pre_registradas` las fija.

**Pasada válida**: `ok`, candidato, sin `error_analisis`, con `primary_cluster`, publicado identificado y no
ambiguo, grilla consistente, `replica_ok` True, alineación no False, `foco_ok` y `n_publicado_hoy < Npix` del OSF.

**Vecinos calientes**: los `Npix−1` (máximo 8) vecinos del centro con mayor BT. **Limitante** de un vecino
caliente no incluido: los tests de la ruta publicada con margen ≤ 0, unidos por `+`:

- ruta contextual con segundo pase: `dnti_2p`, `deti_2p`;
- ruta contextual sin segundo pase: `dnti_1p`, `deti_1p`, `bt_1p`, `fuera_roi`;
- ruta del Test 1: `test1_disco`, `dnti_ctx`, `bt_ctx`, `no_apto_ctx`, `fuera_roi`.

`ninguno` (pasa todos pero no está incluido) sería una contradicción del instrumento.

**Control del instrumento** (todas las pasadas `ok`; un instrumento correcto da 1,0 en todos):
C1 captura ≥ 0,90; C2 réplica F5 ≥ 0,95 (tautológica respecto del código, H5: sólo detecta que el port o el
filtro diverjan); **C3 alineación = 1,0**; **C4 réplica de márgenes = 1,0**. Si falla: **INDETERMINADO:instrumento**.

**Por volcán** (evaluable con ≥ 3 pasadas válidas):
- *limitante*: el `ruta:limitante` con fracción ≥ 0,60 entre los vecinos calientes no incluidos; si no, DISPERSO.
  Se reporta la mediana del margen relativo (margen / |umbral|) de los tests de índice que fallan: "por cuánto".
- *contraste*: mediana del exceso de los calientes menos mediana del exceso de los calientes del control;
  ≥ 1,0 K VECINOS_TIBIOS, si no SIN_CONTRASTE. Se reporta el exceso del centro y del control (H6).
- *fondo de vecinos*: mediana de (aporte con fondo local de los calientes no incluidos) / brecha.
- *fondo del cúmulo* (D25): mediana de (aporte con fondo local de los píxeles publicados menos su VRP con el
  fondo de la ruta) / brecha. Ambos: ≥ 0,5 CIERRA, < 0,2 NO_CIERRA, si no PARCIAL.

**Por estrato y total** (≥ 3 volcanes evaluables; si no, **INDETERMINADO:pocos_volcanes**):
- **PATRON:ruta:limitante** si el agregado tiene fracción ≥ 0,60, al menos 2/3 de los volcanes comparten esa
  limitante y al sacar cada volcán por turno el agregado no cambia; si no, HETEROGENEO.
- contraste, fondo de vecinos y fondo del cúmulo: la clase que comparten ≥ 2/3 de los volcanes y sigue así al
  sacar cada uno; si no, HETEROGENEO.

**Qué justifica.** Sólo `PATRON` con `VECINOS_TIBIOS` justifica diseñar un brazo de A/B sobre el test nombrado:
`*:dnti_*` o `*:deti_*` (umbral o conectiva de los Tests 2 y 3, frente de la conectiva de S136), `*:bt_*`
(compuerta de D22; en la ruta contextual con segundo pase es imposible, §3.3), `test1:test1_disco` (disco del
Test 1). El fondo del cúmulo CIERRA o PARCIAL justifica un brazo de D25 independiente de la limitante.
SIN_CONTRASTE refuta que el hueco sean vecinos tibios detectables a 375 m; no justifica brazo.

**Límites que se escriben antes de correr.** Los `Npix` de MIROVA están en su grilla remuestreada (D17): que sean
nuestros `Npix−1` vecinos nativos más calientes es un supuesto. El umbral de 1,0 K es una elección redonda, no un
valor instrumental. H6 sigue: el control no está pareado en intensidad con el centro, así que VECINOS_TIBIOS es
casi seguro en toda pasada con detección real; por eso se reportan los dos excesos y el contraste no decide solo.
H11 sigue: el aporte con fondo local suma exceso positivo de vecinos, aunque ahora sólo de los `Npix−1` calientes.

## 6. Desviaciones declaradas

1. **`final_hotspot_source` interno** (§6.2 del v1): variable local pisada por el ancla honesta
   (`process_viirs.py:2014-2015`). Se registra la llamada que produjo `primary_cluster` y el valor de
   `resolve_test1_source_priority` (evidencia parcial, `:1712`). El verificador pre-corrida confirmó que con el
   código de hoy equivale a la fuente interna.
2. **Fondo local en la ruta del Test 1** (§6.6 del v1): los Tests 2 y 3 no alimentan ese cúmulo
   (`:1798-1799`, `:1910`); la máscara de alertas es la entrada de la llamada que publicó.
3. **H7, tres "picos"**: la muestra filtra con el pico del núcleo F5 persistido; la corrida centra en el máximo
   VRP del cúmulo publicado hoy; `n_publicado_hoy` cuenta el núcleo F5. No se unifican; `foco_ok` de la corrida
   usa el centro de hoy, que es el que decide.
4. **H8**: en Isluga y Lastarria `vent_lat/vent_lon` es el punto del catálogo. Desde H1 no decide nada.

## 7. SOSPECHAS del instrumento (no verificadas)

- **Memoria.** Los eventos guardan referencias (no copias) a los arreglos de escena completa que recibieron las
  funciones de detección, y el segundo pase se recalcula sobre la escena entera. Puede subir el pico de memoria
  del runner; no medido.
- **Cuantización de `LAT/LON` del OSF** (D15): ver §9.
- **Ruta por `connectivity=`**: depende del código de hoy; `test_a89_llamadas_distinguibles_en_el_fuente` falla
  si cambia.
- **Estadística del primer pase**: `mu` y `sigma` se toman del `diag` que devuelve la función, no se recalculan.

## 8. Archivos

| archivo | rol |
|---|---|
| `experiments/_s141_fase1_probe_v2/muestra.py` | muestra con filtro por foco de MIROVA contra nuestro pico y exclusión del v1 |
| `experiments/_s141_fase1_probe_v2/captura.py` | envoltorios por etapa, con los argumentos de los tests de detección |
| `experiments/_s141_fase1_probe_v2/margenes.py` | margen a cada test, réplica contra la firma real, limitante |
| `experiments/_s141_fase1_probe_v2/analisis_v2.py` | publicado, F5, C3, filtro de store, fondo, contraste, criterio |
| `experiments/_s141_fase1_probe_v2/flags.py` | flags afirmados |
| `experiments/_s141_fase1_probe_v2/ensamblar.py` | junta captura y análisis (probado con funciones reales) |
| `experiments/_s141_fase1_probe_v2/probe_vecinos_v2.py` | runner en CI |
| `experiments/_s141_fase1_probe_v2/juntar.py` | junta artefactos y aplica el criterio (S91) |
| `tests/test_probe_vecinos_v2_s141.py` | tests |
| `.github/workflows/probe-s141-vecinos-v2.yml` | workflow de sólo lectura, `set -o pipefail` |

Hipótesis: `H_S141_VECINO_FOCO_V2` en `docs/HYPOTHESIS_LOG.md`, escrita antes de cualquier corrida.

## 9. Muestra (salida de `muestra.py` con el filtro H1, antes de cualquier corrida del probe)

Números en `experiments/_s141_fase1_probe_v2/muestra_resumen.json` (escrito por el script, S91); detalle en
`pasadas.json` y `excluidas.json`. OSF 2025 (ventana de `scripts/descomponer_magnitud_osf.py`), 6 candidatos y 2
controles por volcán como máximo.

- **38 pasadas**: 30 candidatos, 6 por volcán en Isluga, Láscar, Lastarria, Planchón-Peteroa y Puyehue-Cordón
  Caulle; 8 controles.
- **Excluidas por foco de MIROVA lejos de nuestro pico** (candidatos): Lastarria 15, Nevados de Chillán 10,
  Isluga 2, Puyehue-Cordón Caulle 1 (la 2025-07-18 05:24 que señaló H1). Las demás exclusiones son pasadas del v1.
  Respecto de la muestra con rama del cráter, en Puyehue salen 2025-07-04 04:48 y 2025-07-18 05:24 y entran
  2025-07-03 05:06 y 2025-07-18 05:00 (el espaciado en el tiempo se recalcula sobre las aptas).
- **Decidido S142 (Nicolás aprobó la recomendación): el estrato nevado queda INDETERMINADO:pocos_volcanes en este probe, sin backfill.** Una muestra en otra ventana del OSF no es viable: nuestros records de los 11 Tier A empiezan el 2025-02-15, y aun con backfill sólo Chaitén, Nevados de Chillán y Villarrica juntan 3 pasadas a la vez, entre 2017 y 2022, con código distinto al de las muestras v1 y v2 (`experiments/_s142_nevado_muestra/PROPUESTA.md`). La pregunta del nevado se retoma con los TIF UTM de MIROVA posteriores al 2026-09-14.
- **El estrato nevado queda sin candidatos: decisión de Nicolás.** Los de Chaitén y Villarrica ya estaban en el
  v1 y los de Nevados de Chillán tienen el foco de MIROVA a más de 10 km. Con el pre-registro, el nevado sale
  INDETERMINADO:pocos_volcanes por construcción. Las dos salidas posibles (otra ventana del OSF, o reusar
  pasadas del v1 ya miradas) cambian lo que la muestra puede afirmar, y no las decide el instrumento.
- **Cuantización (SOSPECHA de §7).** Las distancias del foco de MIROVA se repiten en pocos valores en
  `excluidas.json`, compatible con `LAT/LON` en el centro de una celda de su grilla. El radio de 0,75 km no se
  cambia; el informe tiene que decir que el estrato focal quedó sin esa franja de Lastarria.

## 10. Tests en rojo (TDD)

Primera versión: 29 de 31 fallaron por módulo, muestra o yml inexistentes; los dos de ensamblado se escribieron
junto con `ensamblar.py` y no pasaron por rojo. Rediseño por H3: 28 de 39 fallaron por la razón que dicen
(`margenes` y `flags` inexistentes, métodos de captura ausentes, firma vieja de `resumir_pasada`, filtro de foco
con rama del cráter, `sin_primary_cluster` contado como falla). Los 11 que pasaron son guardas de premisas del
código de hoy que deben pasar sin código nuevo, incluidas las dos imposibilidades por construcción de §3.

## 11. Tareas

- [x] T1 tests en rojo; T2 muestra; T3 captura, márgenes y análisis; T4 runner, juntar y workflow.
- [x] T5 suite completa `python -m pytest tests/ -q -p no:cacheprovider`.
- [ ] T6 (orquestador): mergear, despachar, juntar con `juntar.py`, verificador con contexto limpio.
