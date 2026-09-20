# Fase 1 del plan de paridad S146: dónde vive la sobre-publicación, medido por camino de detección

> Generado por `experiments/_s146_fase1_sustrato/generar_informe.py` desde `experiments/_s146_fase1_sustrato/resultados_sustrato.json` (corrida 2026-09-20T11:02:08+00:00). Ningún número de este documento está escrito a mano: cada cifra sale del JSON y al lado va el fragmento crudo. La salida completa de consola está en `experiments/_s146_fase1_sustrato/salida_cruda.txt`. Sólo lectura: no se tocó `pipeline/`, `frontend/`, perfiles, `data/`, `scripts/` ni `tests/`.

## 0. Lo que hay que saber antes de leer una tabla

**Qué ve el satélite en cada camino.** En una pasada nocturna el sensor mide dos cosas sobre cada píxel: cuánto brilla en el infrarrojo medio (MIR, muy sensible a un punto muy caliente aunque sea chico) y cuánto en el térmico (TIR, que responde a la temperatura promedio del terreno). Hay dos maneras físicamente distintas de decidir que un cráter está caliente:

1. **El camino contextual (Tests 2 y 3 del paper de MIROVA)** pregunta si UN píxel destaca contra sus ocho vecinos en el índice que compara MIR con TIR. Es la firma de un foco puntual: lava o una fumarola de alta temperatura que ocupa una fracción del píxel hace subir el MIR sin subir el TIR, y ese píxel se despega de los de al lado. En el código es el primer pase (con una compuerta adicional `bt > t_bg + 3 K` que el paper no tiene) más la recaptura del segundo pase (sin compuerta).

2. **El Test 1 integrado en el ROI (detector propio, no está en el paper)** no pregunta por ningún píxel. Suma el exceso de radiancia MIR de todo el disco de 3 km alrededor del cráter contra un anillo de fondo, y dispara si la suma supera 3 sigmas. Físicamente eso detecta que la cumbre, en conjunto, está un poco más tibia que su entorno. Un lago de lava sub-píxel produce eso, pero también lo produce una cumbre de roca oscura sin nieve rodeada de glaciar, o el contraste de altitud entre el cono y el valle (A69): es un camino de MIR absoluto.

**El mecanismo que importa, y que cambia cómo se leen los contadores (A89, A6).** Leyendo el código y no los nombres de los campos: con `ENABLE_FIRST_PASS_TESTS_2_AND_3 = True` la máscara de píxeles calientes ES el primer pase más el segundo (`pipeline/process_viirs.py` l. 1299 y 1357). Los caminos legacy (BT, NTI, `dnti_ctx`, ETI) se calculan y se cuentan pero **no entran a la máscara** (comentario del propio código en la l. 1237). Por eso `diag_n_dnti_ctx_path > 0` NO significa que el "path D" sostuvo algo: es un diagnóstico. El Test 1 tampoco entra a la máscara: **compite por la fuente del cúmulo publicado** (l. 1763 a 1786 y `pipeline/anchor.py` l. 67 a 89). Si no hay cúmulo contextual, o está fuera del radio interno, el Test 1 pone el ancla en el cráter (`final_hotspot_source = test1_roi`) y arma él solo el cúmulo que el dashboard publica. Ese campo persistido es lo que permite atribuir por lógica de la etapa siguiente y no sólo por conteo.

**El test de temperatura de brillo con N·σ 5/10 está apagado en producción.** `ENABLE_BT_PATH_HOT = False`, `ENABLE_FINAL_PIXEL_FILTER = False` y `ENABLE_TEST1_PIXEL_FILTER = False` (leídos de `pipeline.profile` con `VRP_PROFILE=mirova_equivalent`, no del YAML). `ENABLE_DUAL_ROI_BT = True` construye la máscara pero la l. 997 la pone en cero. Medido sobre todas las pasadas nocturnas de la ventana:

```json
{"MODIS": {"n": 457, "diag_n_bt_path>0": 0, "diag_n_nti_path>0": 0, "diag_n_eti_path>0": 0, "triggered_test1": 16, "d9_capped": 59, "d9_capped_y_publicada": 7}, "VIIRS375": {"n": 954, "diag_n_bt_path>0": 0, "diag_n_nti_path>0": 5, "diag_n_eti_path>0": 0, "triggered_test1": 800, "d9_capped": 0, "d9_capped_y_publicada": 0}, "VIIRS750": {"n": 949, "diag_n_bt_path>0": 0, "diag_n_nti_path>0": 0, "diag_n_eti_path>0": 0, "triggered_test1": 200, "d9_capped": 0, "d9_capped_y_publicada": 0}}
```

El contador `diag_n_bt_path` es cero en todas. Ese camino no decide nada hoy: un brazo de A/B "sin test de temperatura de brillo" tiene **sustrato cero**.

## 1. Cobertura y control positivo

- Ventana: 2026-09-01 a 2026-09-20, toda posterior al 2026-08-28 23:00 UTC (no cruza #535). 11 Tier A.
- Referencia: los mismos dos CSV que bajó S145 (`experiments/_s145_paridad/_dl_referencia/`, sin red). Última fila CONS 2026-09-20 02:45:00, última fila OCR 2026-09-19 06:24:00. Esa copia del OCR llega más lejos que el snapshot del repo (2026-09-14); por eso se informa aparte una sensibilidad cortada en la noche del 2026-09-14.
- Pasadas nocturnas hoy: 2360 (S145 tenía 2285; el cron NRT siguió escribiendo). Etiquetas: {'neg_limpio': 1434, 'sin_info': 732, 'far_ref': 32, 'pos': 162}.
- Predicado de publicación: el del dashboard, ejecutado con node desde `frontend/index.html` (sha 24fba8a157136bf76509ed647c7d086d3f9f45aa, el mismo de S145) a través de `banco_paridad.correr_node`. No se portó a Python.

**Control positivo (reproducir S145 antes de atribuir nada):**

| sensor | S145 publicado | mi carga, todo | mi carga, sólo records procesados antes del corte de S145 |
|---|---|---|---|
| VIIRS375 | 0.8633 (n 373) | 0.8633 (n 373) | 0.8623 (n 363) |
| VIIRS750 | 0.2138 (n 622) | 0.2138 (n 622) | 0.2135 (n 609) |
| MODIS | 0.1142 (n 438) | 0.1139 (n 439) | 0.1142 (n 438) |

```json
{"identidad_predicado": true, "pub_identico_a_bp": true, "s145_publicado": {"MODIS": {"n_neg_limpio": 438, "tasa_pub_neg": 0.1142, "n_pos": 1}, "VIIRS375": {"n_neg_limpio": 373, "tasa_pub_neg": 0.8633, "n_pos": 143}, "VIIRS750": {"n_neg_limpio": 622, "tasa_pub_neg": 0.2138, "n_pos": 18}}, "hoy_todo": {"MODIS": {"n_neg_limpio": 439, "tasa_pub_neg": 0.1139, "n_pos": 1}, "VIIRS375": {"n_neg_limpio": 373, "tasa_pub_neg": 0.8633, "n_pos": 143}, "VIIRS750": {"n_neg_limpio": 622, "tasa_pub_neg": 0.2138, "n_pos": 18}}, "hoy_con_corte_processed_utc_s145": {"MODIS": {"n_neg_limpio": 438, "tasa_pub_neg": 0.1142, "n_pos": 1}, "VIIRS375": {"n_neg_limpio": 363, "tasa_pub_neg": 0.8623, "n_pos": 140}, "VIIRS750": {"n_neg_limpio": 609, "tasa_pub_neg": 0.2135, "n_pos": 17}}}
```

Lectura: VIIRS 375 y VIIRS 750 reproducen S145 exacto con la carga completa. MODIS tiene un negativo limpio más que S145 (una pasada que entró después) y reproduce exacto al cortar por `processed_utc`. Ese corte NO sirve para los VIIRS porque el pipeline reescribe `processed_utc` cuando un gránulo NRT se actualiza: es un reloj de escritura, no de llegada (se declara, no se usa para nada más). El vector de publicación de mi carga es idéntico al de `bp.cargar_nuestros`.

**Controles del clasificador de sostén:**

```json
{"coherencia_clasificador_T1_sin_trigger": 0, "control_centroides_ctx_sin_t1": {"n": 180, "n_centroide_distinto": 0}}
```

El primero: ninguna pasada clasificada como sostenida por el Test 1 tiene `triggered_test1 = False` (en la primera corrida este control dio 39 incoherencias, todas MODIS, y ABORTÓ: en MODIS el ancla honesta está apagada y `final_hotspot` es el píxel suelto más caliente, no el centroide; se corrigió la regla para la cascada legacy y quedó en 0). El segundo: entre las pasadas con ancla contextual donde el Test 1 no disparó, el centroide del cúmulo publicado coincide siempre con el ancla; eso valida usar la diferencia de centroides como huella de que el Test 1 reconstruyó el cúmulo.

## 2. Inventario de campos (qué hay persistido de verdad)

Hecho con `Counter` sobre las claves de los records de la ventana (salida de mi sesión, 954 V375, 949 V750, 457 MODIS):

- Existen y con cobertura completa en los tres sensores: `triggered_test1`, `n_test1_pixels`, `test1_k_observed`, `diag_n_bt_path`, `diag_n_nti_path`, `diag_n_dnti_ctx_path`, `diag_n_eti_path`, `diag_n_first_pass_pixels`, `diag_n_second_pass_recapture`, `diag_sigma_bg_k`, `t_bg_k` (949 de 954 en V375), `final_hotspot_source` (nulo cuando no hay detección), `primary_cluster` (con `geo_class`, `single_pixel_mode`, y a veces `focal_magnitude`, `d9_capped`).
- Sólo MODIS: `diag_n_first_pass_summit`. Sólo V375: `f5_core_vrp_mw` (846 de 954).
- **No existe**: máscara por píxel ni etiqueta de camino por píxel. `anomaly_pixels` trae `lat, lon, dist_km, bt_k, vrp_mw` y nada más. Tampoco se persiste el VRP del cúmulo contextual cuando el Test 1 lo reemplaza.
- Valores reales de `final_hotspot_source` en la ventana: VIIRS `ctx_cluster` y `test1_roi`; MODIS `eruption`, `test1` y `cluster_rescue` (cascada legacy).

## 3. Las clases de sostén y los tres niveles de evidencia

| clase | definición sobre campos persistidos | qué pasa si se apaga el Test 1 integrado | nivel |
|---|---|---|---|
| **T1_SOLO** | fuente `test1_roi` (VIIRS) o `test1` (MODIS): no había cúmulo contextual o estaba fuera del radio interno | la pasada queda sin cúmulo o con clase `far`: **no se publica** | N3 por lógica del código (en MODIS queda la salvedad del rescate de `store.py`) |
| **CTX_SOLO** | cúmulo contextual publicado y el Test 1 no disparó | nada cambia; depende sólo de los Tests 2 y 3 | N3 |
| **AMBOS** | cúmulo contextual publicado y el Test 1 también disparó | **sigue publicada** con el mismo cúmulo | N3 para el Test 1; apagar el contextual es SIN DATO |
| **T1_SOBRE_CTX** | ancla contextual pero el Test 1 reconstruyó el cúmulo encima (rival débil bajo 0,01 MW, o fuente única) | **SIN DATO**: publicaría sólo si el cúmulo contextual tenía más de 0 MW, y ese valor no se persiste | N2 |
| RESCATE_SIN_DATO | `cluster_rescue`: `store.py` reescribió la fuente | SIN DATO | N1 |

Lo que NO se puede llevar a N3 desde lo persistido: quitar la compuerta de 3 K (D22), cambiar la banda primaria (D21), quitar el segundo pase o cambiar el fondo. Para eso va el probe de la sección 9.

## 4. La tabla: camino por sensor

Unidad de la sobre-publicación: la PASADA en negativo limpio. Unidad del recall: la NOCHE de volcán.

| sensor | neg. limpios publicados / n | T1_SOLO | T1_SOBRE_CTX (SIN DATO) | AMBOS | CTX_SOLO | tasa hoy | tasa sin Test 1 (cota mín a máx) |
|---|---|---|---|---|---|---|---|
| VIIRS375 | 322 / 373 | 186 (57,8 %) | 56 | 63 | 17 (5,3 %) | 86,3 % | 21,4 % a 36,5 % |
| VIIRS750 | 133 / 622 | 89 (66,9 %) | 11 | 9 | 24 (18,1 %) | 21,4 % | 5,3 % a 7,1 % |
| MODIS | 50 / 439 | 8 (16,0 %) | 0 + 3 rescate | 1 | 38 (76,0 %) | 11,4 % | 8,9 % a 9,6 % |

| sensor | noches pos | publicadas hoy | sin Test 1: siguen seguro | sin Test 1: SIN DATO | sin Test 1: se pierden seguro | pasadas pos T1_SOLO |
|---|---|---|---|---|---|---|
| VIIRS375 | 75 | 75 | 71 | 4 | 0 | 2 |
| VIIRS750 | 14 | 13 | 11 | 1 | 1 | 0 |
| MODIS | 1 | 1 | 1 | 0 | 0 | 0 |
| CUALQUIERA | 78 | 78 | 74 | 4 | 0 | n/a |

Crudo (clases por etiqueta y sensor, y contrafactual):

```json
{"VIIRS375": {"neg_limpio": {"n": 373, "n_pub": 322, "clases_pub": {"AMBOS": 63, "CTX_SOLO": 17, "T1_SOBRE_CTX": 56, "T1_SOLO": 186}}, "pos": {"n": 143, "n_pub": 143, "clases_pub": {"AMBOS": 118, "T1_SOBRE_CTX": 23, "T1_SOLO": 2}}}, "VIIRS750": {"neg_limpio": {"n": 622, "n_pub": 133, "clases_pub": {"AMBOS": 9, "CTX_SOLO": 24, "T1_SOBRE_CTX": 11, "T1_SOLO": 89}}, "pos": {"n": 18, "n_pub": 13, "clases_pub": {"AMBOS": 8, "CTX_SOLO": 5}}}, "MODIS": {"neg_limpio": {"n": 439, "n_pub": 50, "clases_pub": {"AMBOS": 1, "CTX_SOLO": 38, "RESCATE_SIN_DATO": 3, "T1_SOLO": 8}}, "pos": {"n": 1, "n_pub": 1, "clases_pub": {"CTX_SOLO": 1}}}}
```

```json
{"VIIRS375": {"neg_limpio": {"n": 373, "pub_hoy": 322, "tasa_hoy": 0.8633, "T1_SOLO": 186, "frac_T1_SOLO_de_lo_publicado": 0.5776, "sinT1_pub_min": 80, "sinT1_pub_max": 136, "sinT1_tasa_min": 0.2145, "sinT1_tasa_max": 0.3646, "sinCTX_pub_seguro(T1_SOLO)": 186, "CTX_SOLO": 17, "frac_CTX_SOLO_de_lo_publicado": 0.0528}, "pos": {"n": 143, "pub_hoy": 143, "tasa_hoy": 1.0, "T1_SOLO": 2, "frac_T1_SOLO_de_lo_publicado": 0.014, "sinT1_pub_min": 118, "sinT1_pub_max": 141, "sinT1_tasa_min": 0.8252, "sinT1_tasa_max": 0.986, "sinCTX_pub_seguro(T1_SOLO)": 2, "CTX_SOLO": 0, "frac_CTX_SOLO_de_lo_publicado": 0.0}}, "VIIRS750": {"neg_limpio": {"n": 622, "pub_hoy": 133, "tasa_hoy": 0.2138, "T1_SOLO": 89, "frac_T1_SOLO_de_lo_publicado": 0.6692, "sinT1_pub_min": 33, "sinT1_pub_max": 44, "sinT1_tasa_min": 0.0531, "sinT1_tasa_max": 0.0707, "sinCTX_pub_seguro(T1_SOLO)": 89, "CTX_SOLO": 24, "frac_CTX_SOLO_de_lo_publicado": 0.1805}, "pos": {"n": 18, "pub_hoy": 13, "tasa_hoy": 0.7222, "T1_SOLO": 0, "frac_T1_SOLO_de_lo_publicado": 0.0, "sinT1_pub_min": 13, "sinT1_pub_max": 13, "sinT1_tasa_min": 0.7222, "sinT1_tasa_max": 0.7222, "sinCTX_pub_seguro(T1_SOLO)": 0, "CTX_SOLO": 5, "frac_CTX_SOLO_de_lo_publicado": 0.3846}}, "MODIS": {"neg_limpio": {"n": 439, "pub_hoy": 50, "tasa_hoy": 0.1139, "T1_SOLO": 8, "frac_T1_SOLO_de_lo_publicado": 0.16, "sinT1_pub_min": 39, "sinT1_pub_max": 42, "sinT1_tasa_min": 0.0888, "sinT1_tasa_max": 0.0957, "sinCTX_pub_seguro(T1_SOLO)": 8, "CTX_SOLO": 38, "frac_CTX_SOLO_de_lo_publicado": 0.76}, "pos": {"n": 1, "pub_hoy": 1, "tasa_hoy": 1.0, "T1_SOLO": 0, "frac_T1_SOLO_de_lo_publicado": 0.0, "sinT1_pub_min": 1, "sinT1_pub_max": 1, "sinT1_tasa_min": 1.0, "sinT1_tasa_max": 1.0, "sinCTX_pub_seguro(T1_SOLO)": 0, "CTX_SOLO": 1, "frac_CTX_SOLO_de_lo_publicado": 1.0}}}
```

Noches de recall que no quedan aseguradas sin el Test 1 (todas SIN DATO salvo que se indique; lista completa):

```json
{"VIIRS375": [["Isluga", "2026-09-19", "SIN_DATO", {"T1_SOBRE_CTX": 2, "T1_SOLO": 2}], ["Lastarria", "2026-09-01", "SIN_DATO", {"T1_SOLO": 1, "T1_SOBRE_CTX": 2}], ["NevadosDeChillan", "2026-09-18", "SIN_DATO", {"T1_SOBRE_CTX": 2, "T1_SOLO": 2}], ["Villarrica", "2026-09-16", "SIN_DATO", {"T1_SOLO": 1, "T1_SOBRE_CTX": 1}]], "VIIRS750": [["Isluga", "2026-09-05", "SIN_DATO", {"T1_SOBRE_CTX": 1}], ["PuyehueCordonCaulle", "2026-09-07", "SE_PIERDE", {"T1_SOLO": 1}]], "MODIS": [], "CUALQUIERA": [["Isluga", "2026-09-19", "SIN_DATO", {"T1_SOBRE_CTX": 2, "T1_SOLO": 3}], ["Lastarria", "2026-09-01", "SIN_DATO", {"T1_SOLO": 1, "T1_SOBRE_CTX": 2}], ["NevadosDeChillan", "2026-09-18", "SIN_DATO", {"T1_SOBRE_CTX": 2, "T1_SOLO": 2}], ["Villarrica", "2026-09-16", "SIN_DATO", {"T1_SOLO": 1, "T1_SOBRE_CTX": 1}]]}
```

La noche de PCC 2026-09-07 en VIIRS 750 figura como perdida dentro de ese sensor, pero a nivel de volcán (cualquier sensor) la misma noche sigue publicada por otra pasada: en CUALQUIERA no hay ninguna pérdida segura.

**Niveles 1 y 2 (contadores), para no mezclarlos con lo anterior.** Entre las pasadas publicadas:

```json
{"MODIS": {"neg_limpio": {"n_pub": 50, "N1_test1": 12, "N1_primer_pase": 50, "N1_segundo_pase": 49, "N1_dnti_ctx_diag": 50, "N1_bt_path": 0, "N1_nti_path": 0, "N2_solo_test1": 0, "N2_solo_primer_pase": 1, "N2_solo_segundo_pase": 0, "N2_solo_contextual(1o+2o)": 38, "ninguno_de_los_tres": 0}, "pos": {"n_pub": 1, "N1_test1": 0, "N1_primer_pase": 1, "N1_segundo_pase": 1, "N1_dnti_ctx_diag": 1, "N1_bt_path": 0, "N1_nti_path": 0, "N2_solo_test1": 0, "N2_solo_primer_pase": 0, "N2_solo_segundo_pase": 0, "N2_solo_contextual(1o+2o)": 1, "ninguno_de_los_tres": 0}}, "VIIRS375": {"neg_limpio": {"n_pub": 322, "N1_test1": 305, "N1_primer_pase": 85, "N1_segundo_pase": 123, "N1_dnti_ctx_diag": 144, "N1_bt_path": 0, "N1_nti_path": 0, "N2_solo_test1": 158, "N2_solo_primer_pase": 2, "N2_solo_segundo_pase": 11, "N2_solo_contextual(1o+2o)": 17, "ninguno_de_los_tres": 0}, "pos": {"n_pub": 143, "N1_test1": 143, "N1_primer_pase": 111, "N1_segundo_pase": 107, "N1_dnti_ctx_diag": 127, "N1_bt_path": 0, "N1_nti_path": 1, "N2_solo_test1": 0, "N2_solo_primer_pase": 0, "N2_solo_segundo_pase": 0, "N2_solo_contextual(1o+2o)": 0, "ninguno_de_los_tres": 0}}, "VIIRS750": {"neg_limpio": {"n_pub": 133, "N1_test1": 109, "N1_primer_pase": 21, "N1_segundo_pase": 38, "N1_dnti_ctx_diag": 86, "N1_bt_path": 0, "N1_nti_path": 0, "N2_solo_test1": 86, "N2_solo_primer_pase": 4, "N2_solo_segundo_pase": 12, "N2_solo_contextual(1o+2o)": 24, "ninguno_de_los_tres": 0}, "pos": {"n_pub": 13, "N1_test1": 8, "N1_primer_pase": 5, "N1_segundo_pase": 10, "N1_dnti_ctx_diag": 12, "N1_bt_path": 0, "N1_nti_path": 0, "N2_solo_test1": 0, "N2_solo_primer_pase": 1, "N2_solo_segundo_pase": 4, "N2_solo_contextual(1o+2o)": 5, "ninguno_de_los_tres": 0}}}
```

Se lee así: en V375 el Test 1 participó en casi todas las publicadas de ambos lados (N1 no discrimina nada); fue el ÚNICO que disparó (N2) en muchas de las negativas y en ninguna de las positivas. N3 es mayor que N2 porque incluye las pasadas donde hubo píxeles contextuales pero lejos del cráter. Las columnas `N2_solo_segundo_pase` son pasadas sostenidas por píxeles que la compuerta de 3 K rechazó en el primer pase y el segundo pase recapturó sin compuerta.

Subclases (para T1_SOBRE_CTX, `rival_debil` significa que sin Test 1 la pasada se publicaría con menos de 0,01 MW o no se publicaría):

```json
{"MODIS": {"neg_limpio": {"RESCATE_SIN_DATO|cluster_rescue": 3, "CTX_SOLO|eruption": 38, "T1_SOLO|test1": 8, "AMBOS|eruption": 1}, "pos": {"CTX_SOLO|eruption": 1}}, "VIIRS375": {"neg_limpio": {"AMBOS|ctx_cluster": 63, "T1_SOBRE_CTX|ctx_cluster|rival_debil_lt_0.01MW": 21, "T1_SOLO|test1_roi": 186, "T1_SOBRE_CTX|ctx_cluster|fuente_unica": 35, "CTX_SOLO|ctx_cluster": 17}, "pos": {"AMBOS|ctx_cluster": 118, "T1_SOBRE_CTX|ctx_cluster|rival_debil_lt_0.01MW": 20, "T1_SOBRE_CTX|ctx_cluster|fuente_unica": 3, "T1_SOLO|test1_roi": 2}}, "VIIRS750": {"neg_limpio": {"CTX_SOLO|ctx_cluster": 24, "T1_SOLO|test1_roi": 89, "T1_SOBRE_CTX|ctx_cluster|fuente_unica": 8, "AMBOS|ctx_cluster": 9, "T1_SOBRE_CTX|ctx_cluster|rival_debil_lt_0.01MW": 3}, "pos": {"CTX_SOLO|ctx_cluster": 5, "AMBOS|ctx_cluster": 8}}}
```

Tamaño de lo que sostiene cada clase (mediana de la magnitud publicada, MW):

```json
{"MODIS": {"neg_limpio": {"T1_SOLO": {"n": 8, "mediana": 0.951}, "CTX_SOLO": {"n": 38, "mediana": 0.767}, "AMBOS": {"n": 1, "mediana": 0.566}, "T1_SOBRE_CTX": {"n": 0, "mediana": null}}, "pos": {"T1_SOLO": {"n": 0, "mediana": null}, "CTX_SOLO": {"n": 1, "mediana": 3.859}, "AMBOS": {"n": 0, "mediana": null}, "T1_SOBRE_CTX": {"n": 0, "mediana": null}}}, "VIIRS375": {"neg_limpio": {"T1_SOLO": {"n": 186, "mediana": 0.0411}, "CTX_SOLO": {"n": 17, "mediana": 0.0194}, "AMBOS": {"n": 63, "mediana": 0.0374}, "T1_SOBRE_CTX": {"n": 56, "mediana": 0.0471}}, "pos": {"T1_SOLO": {"n": 2, "mediana": 0.0531}, "CTX_SOLO": {"n": 0, "mediana": null}, "AMBOS": {"n": 118, "mediana": 0.1188}, "T1_SOBRE_CTX": {"n": 23, "mediana": 0.1053}}}, "VIIRS750": {"neg_limpio": {"T1_SOLO": {"n": 89, "mediana": 0.248}, "CTX_SOLO": {"n": 24, "mediana": 0.241}, "AMBOS": {"n": 9, "mediana": 0.151}, "T1_SOBRE_CTX": {"n": 11, "mediana": 0.343}}, "pos": {"T1_SOLO": {"n": 0, "mediana": null}, "CTX_SOLO": {"n": 5, "mediana": 0.208}, "AMBOS": {"n": 8, "mediana": 0.267}, "T1_SOBRE_CTX": {"n": 0, "mediana": null}}}}
```

## 5. Estratificación por volcán (antes de creer el agregado)

**VIIRS375**

| volcán | neg n | neg pub | T1_SOLO | T1_SOBRE_CTX | AMBOS | CTX_SOLO | pos n | pos pub | pos T1_SOLO | pos T1_SOBRE_CTX | pos AMBOS | pos CTX_SOLO |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Lascar | 25 | 22 | 8 | 4 | 10 | 0 | 18 | 18 | 0 | 3 | 15 | 0 |
| Lastarria | 24 | 21 | 13 | 2 | 4 | 2 | 9 | 9 | 0 | 3 | 6 | 0 |
| Isluga | 9 | 7 | 1 | 4 | 1 | 1 | 33 | 33 | 1 | 8 | 24 | 0 |
| Tupungatito | 14 | 13 | 6 | 3 | 4 | 0 | 26 | 26 | 0 | 7 | 19 | 0 |
| PlanchonPeteroa | 35 | 30 | 21 | 3 | 5 | 1 | 8 | 8 | 0 | 0 | 8 | 0 |
| NevadosDeChillan | 48 | 44 | 26 | 7 | 11 | 0 | 4 | 4 | 1 | 0 | 3 | 0 |
| Llaima | 57 | 45 | 26 | 10 | 4 | 5 | 0 | 0 | 0 | 0 | 0 | 0 |
| Villarrica | 48 | 40 | 27 | 8 | 3 | 2 | 5 | 5 | 0 | 2 | 3 | 0 |
| Copahue | 57 | 48 | 39 | 7 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| PuyehueCordonCaulle | 18 | 17 | 2 | 2 | 11 | 2 | 32 | 32 | 0 | 0 | 32 | 0 |
| Chaiten | 38 | 35 | 17 | 6 | 9 | 3 | 8 | 8 | 0 | 0 | 8 | 0 |

**VIIRS750**

| volcán | neg n | neg pub | T1_SOLO | T1_SOBRE_CTX | AMBOS | CTX_SOLO | pos n | pos pub | pos T1_SOLO | pos T1_SOBRE_CTX | pos AMBOS | pos CTX_SOLO |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Lascar | 48 | 5 | 3 | 0 | 0 | 2 | 3 | 3 | 0 | 0 | 0 | 3 |
| Lastarria | 57 | 3 | 2 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Isluga | 50 | 21 | 13 | 3 | 2 | 3 | 1 | 0 | 0 | 0 | 0 | 0 |
| Tupungatito | 59 | 13 | 9 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| PlanchonPeteroa | 57 | 15 | 12 | 0 | 2 | 1 | 1 | 1 | 0 | 0 | 1 | 0 |
| NevadosDeChillan | 62 | 4 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Llaima | 65 | 15 | 10 | 1 | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| Villarrica | 57 | 11 | 8 | 0 | 1 | 2 | 2 | 1 | 0 | 0 | 0 | 1 |
| Copahue | 62 | 9 | 9 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| PuyehueCordonCaulle | 40 | 23 | 9 | 2 | 1 | 11 | 11 | 8 | 0 | 0 | 7 | 1 |
| Chaiten | 65 | 14 | 10 | 0 | 1 | 3 | 0 | 0 | 0 | 0 | 0 | 0 |

**MODIS**

| volcán | neg n | neg pub | T1_SOLO | T1_SOBRE_CTX | AMBOS | CTX_SOLO | pos n | pos pub | pos T1_SOLO | pos T1_SOBRE_CTX | pos AMBOS | pos CTX_SOLO |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Lascar | 36 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Lastarria | 36 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Isluga | 33 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Tupungatito | 40 | 3 | 2 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| PlanchonPeteroa | 43 | 2 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| NevadosDeChillan | 41 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Llaima | 40 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Villarrica | 39 | 6 | 2 | 0 | 0 | 3 | 1 | 1 | 0 | 0 | 0 | 1 |
| Copahue | 40 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| PuyehueCordonCaulle | 46 | 31 | 1 | 0 | 1 | 28 | 0 | 0 | 0 | 0 | 0 | 0 |
| Chaiten | 45 | 4 | 0 | 0 | 0 | 4 | 0 | 0 | 0 | 0 | 0 | 0 |

Noches de recall por volcán (cualquier sensor):

```json
{"Lascar": {"n_noches_pos": 10, "publicada_hoy": 10, "sinT1_sigue_publicada": 10, "sinCTX_sigue_publicada": 3, "sinCTX_SIN_DATO": 7}, "Lastarria": {"n_noches_pos": 7, "publicada_hoy": 7, "sinT1_SIN_DATO": 1, "sinCTX_sigue_publicada": 3, "sinT1_sigue_publicada": 6, "sinCTX_SIN_DATO": 4}, "Isluga": {"n_noches_pos": 15, "publicada_hoy": 15, "sinT1_sigue_publicada": 14, "sinCTX_sigue_publicada": 11, "sinCTX_SIN_DATO": 4, "sinT1_SIN_DATO": 1}, "Tupungatito": {"n_noches_pos": 12, "publicada_hoy": 12, "sinT1_sigue_publicada": 12, "sinCTX_SIN_DATO": 6, "sinCTX_sigue_publicada": 6}, "PlanchonPeteroa": {"n_noches_pos": 6, "publicada_hoy": 6, "sinT1_sigue_publicada": 6, "sinCTX_sigue_publicada": 5, "sinCTX_SIN_DATO": 1}, "NevadosDeChillan": {"n_noches_pos": 4, "publicada_hoy": 4, "sinT1_sigue_publicada": 3, "sinCTX_SIN_DATO": 1, "sinCTX_sigue_publicada": 3, "sinT1_SIN_DATO": 1}, "Llaima": {}, "Villarrica": {"n_noches_pos": 6, "publicada_hoy": 6, "sinT1_sigue_publicada": 5, "sinCTX_sigue_publicada": 6, "sinT1_SIN_DATO": 1}, "Copahue": {}, "PuyehueCordonCaulle": {"n_noches_pos": 12, "publicada_hoy": 12, "sinT1_sigue_publicada": 12, "sinCTX_sigue_publicada": 6, "sinCTX_SIN_DATO": 6}, "Chaiten": {"n_noches_pos": 6, "publicada_hoy": 6, "sinT1_sigue_publicada": 6, "sinCTX_SIN_DATO": 3, "sinCTX_sigue_publicada": 3}}
```

Lo que dice la estratificación, en palabras:
- **VIIRS 375**: el patrón no es de un volcán. T1_SOLO es la clase mayor de los negativos publicados en 8 de 11 volcanes (Lastarria, Tupungatito, PlanchonPeteroa, NevadosDeChillan, Llaima, Villarrica, Copahue, Chaiten) y casi no aparece entre los positivos de ninguno. Las excepciones son físicas y conocidas: **PCC** (sus negativos publicados son sobre todo AMBOS: el lacolito da píxeles contextuales casi siempre), **Láscar** e **Isluga** (mezcla).
- **VIIRS 750**: mismo patrón, con n por celda chico (3 a 23 publicadas por volcán). PCC vuelve a ser la excepción: ahí manda CTX_SOLO.
- **MODIS**: la sobre-publicación es de UN volcán. PCC concentra 31 de las 50 publicadas y 28 de ellas son CTX_SOLO, es decir Tests 2 y 3, el camino que SÍ está en el paper. Fuera de PCC quedan celdas de 0 a 6 pasadas: sin muestra.
- Positivos: Llaima y Copahue no tienen ninguna noche positiva en la ventana, así que ahí el recall que sostiene cada camino es SIN DATO, no cero.

## 6. El nulo (barajar pos y neg_limpio dentro de cada volcán, sensor fijo, 1000 veces)

Contraste = fracción de la clase entre los negativos limpios publicados menos la misma fracción entre los positivos publicados.

| sensor | clase | observado | nulo media | nulo 2,5 a 97,5 % | n neg pub | n pos pub | fuera del nulo |
|---|---|---|---|---|---|---|---|
| VIIRS375 | T1_SOLO | 0.5637 | 0.3077 | 0.2506 a 0.3718 | 322 | 143 | SÍ |
| VIIRS375 | CTX_SOLO | 0.0528 | 0.0154 | -0.0078 a 0.0427 | 322 | 143 | SÍ |
| VIIRS375 | AMBOS | -0.6295 | -0.3073 | -0.3771 a -0.2357 | 322 | 143 | SÍ |
| VIIRS375 | T1_SOBRE_CTX | 0.0131 | -0.0168 | -0.0778 a 0.0434 | 322 | 143 | no |
| VIIRS750 | T1_SOLO | 0.6692 | 0.2655 | -0.0064 a 0.5003 | 133 | 13 | SÍ |
| VIIRS750 | CTX_SOLO | -0.2042 | -0.2259 | -0.4575 a -0.0353 | 133 | 13 | no |
| VIIRS750 | AMBOS | -0.5477 | -0.0749 | -0.2944 a 0.1278 | 133 | 13 | SÍ |
| VIIRS750 | T1_SOBRE_CTX | 0.0827 | 0.0379 | -0.0862 a 0.0827 | 133 | 13 | no |
| MODIS | T1_SOLO | 0.16 | -0.1297 | -0.86 a 0.16 | 50 | 1 | no |
| MODIS | CTX_SOLO | -0.24 | 0.2098 | -0.24 a 0.78 | 50 | 1 | no |
| MODIS | AMBOS | 0.02 | 0.02 | 0.02 a 0.02 | 50 | 1 | no |
| MODIS | T1_SOBRE_CTX | 0.0 | 0.0 | 0.0 a 0.0 | 50 | 1 | no |

```json
{"MODIS": {"T1_SOLO": {"observado": 0.16, "nulo_media": -0.1297, "nulo_p2.5": -0.86, "nulo_p97.5": 0.16, "n_neg_pub": 50, "n_pos_pub": 1, "fuera_del_nulo": false}, "CTX_SOLO": {"observado": -0.24, "nulo_media": 0.2098, "nulo_p2.5": -0.24, "nulo_p97.5": 0.78, "n_neg_pub": 50, "n_pos_pub": 1, "fuera_del_nulo": false}, "AMBOS": {"observado": 0.02, "nulo_media": 0.02, "nulo_p2.5": 0.02, "nulo_p97.5": 0.02, "n_neg_pub": 50, "n_pos_pub": 1, "fuera_del_nulo": false}, "T1_SOBRE_CTX": {"observado": 0.0, "nulo_media": 0.0, "nulo_p2.5": 0.0, "nulo_p97.5": 0.0, "n_neg_pub": 50, "n_pos_pub": 1, "fuera_del_nulo": false}}, "VIIRS375": {"T1_SOLO": {"observado": 0.5637, "nulo_media": 0.3077, "nulo_p2.5": 0.2506, "nulo_p97.5": 0.3718, "n_neg_pub": 322, "n_pos_pub": 143, "fuera_del_nulo": true}, "CTX_SOLO": {"observado": 0.0528, "nulo_media": 0.0154, "nulo_p2.5": -0.0078, "nulo_p97.5": 0.0427, "n_neg_pub": 322, "n_pos_pub": 143, "fuera_del_nulo": true}, "AMBOS": {"observado": -0.6295, "nulo_media": -0.3073, "nulo_p2.5": -0.3771, "nulo_p97.5": -0.2357, "n_neg_pub": 322, "n_pos_pub": 143, "fuera_del_nulo": true}, "T1_SOBRE_CTX": {"observado": 0.0131, "nulo_media": -0.0168, "nulo_p2.5": -0.0778, "nulo_p97.5": 0.0434, "n_neg_pub": 322, "n_pos_pub": 143, "fuera_del_nulo": false}}, "VIIRS750": {"T1_SOLO": {"observado": 0.6692, "nulo_media": 0.2655, "nulo_p2.5": -0.0064, "nulo_p97.5": 0.5003, "n_neg_pub": 133, "n_pos_pub": 13, "fuera_del_nulo": true}, "CTX_SOLO": {"observado": -0.2042, "nulo_media": -0.2259, "nulo_p2.5": -0.4575, "nulo_p97.5": -0.0353, "n_neg_pub": 133, "n_pos_pub": 13, "fuera_del_nulo": false}, "AMBOS": {"observado": -0.5477, "nulo_media": -0.0749, "nulo_p2.5": -0.2944, "nulo_p97.5": 0.1278, "n_neg_pub": 133, "n_pos_pub": 13, "fuera_del_nulo": true}, "T1_SOBRE_CTX": {"observado": 0.0827, "nulo_media": 0.0379, "nulo_p2.5": -0.0862, "nulo_p97.5": 0.0827, "n_neg_pub": 133, "n_pos_pub": 13, "fuera_del_nulo": false}}}
```

Dos lecturas. Primera: el nulo NO está centrado en cero. Su media es la parte del contraste que se explica sólo porque los volcanes con muchos positivos (PCC, Isluga, Tupungatito) son también los que tienen más píxeles contextuales: es la paradoja de Simpson cuantificada, y por eso un agregado crudo exagera. Segunda: aun descontando eso, en VIIRS 375 el contraste de T1_SOLO (y el espejo negativo de AMBOS) queda fuera del intervalo del nulo; en VIIRS 750 también pero con 13 positivos publicados, así que el intervalo es ancho. En MODIS hay UN positivo: el nulo no tiene poder y todo contraste de MODIS es **SIN DATO**, no "no significativo".

## 7. Fondo frío (adelanto de la Fase 3)

| sensor | etiqueta | t_bg | n | publicadas | tasa | T1_SOLO | CTX_SOLO | AMBOS | con tope de 5 MW (`d9_capped`) |
|---|---|---|---|---|---|---|---|---|---|
| VIIRS375 | neg_limpio | lt262 | 152 | 140 | 92,1 % | 71 | 10 | 40 | 0 |
| VIIRS375 | neg_limpio | 262-270 | 119 | 104 | 87,4 % | 59 | 4 | 18 | 0 |
| VIIRS375 | neg_limpio | ge270 | 101 | 78 | 77,2 % | 56 | 3 | 5 | 0 |
| VIIRS375 | pos | lt262 | 40 | 40 | 100,0 % | 0 | 0 | 29 | 0 |
| VIIRS375 | pos | 262-270 | 56 | 56 | 100,0 % | 2 | 0 | 45 | 0 |
| VIIRS375 | pos | ge270 | 47 | 47 | 100,0 % | 0 | 0 | 44 | 0 |
| VIIRS750 | neg_limpio | lt262 | 313 | 75 | 24,0 % | 53 | 12 | 4 | 0 |
| VIIRS750 | neg_limpio | 262-270 | 218 | 52 | 23,9 % | 34 | 9 | 4 | 0 |
| VIIRS750 | neg_limpio | ge270 | 91 | 6 | 6,6 % | 2 | 3 | 1 | 0 |
| VIIRS750 | pos | lt262 | 2 | 2 | 100,0 % | 0 | 1 | 1 | 0 |
| VIIRS750 | pos | 262-270 | 9 | 6 | 66,7 % | 0 | 3 | 3 | 0 |
| VIIRS750 | pos | ge270 | 7 | 5 | 71,4 % | 0 | 1 | 4 | 0 |
| MODIS | neg_limpio | lt262 | 121 | 12 | 9,9 % | 3 | 7 | 0 | 4 |
| MODIS | neg_limpio | 262-270 | 146 | 13 | 8,9 % | 2 | 10 | 0 | 3 |
| MODIS | neg_limpio | ge270 | 172 | 25 | 14,5 % | 3 | 21 | 1 | 0 |
| MODIS | pos | 262-270 | 1 | 1 | 100,0 % | 0 | 1 | 0 | 0 |

```json
{"MODIS": {"neg_limpio": {"lt262": {"n": 121, "n_pub": 12, "clases_pub": {"CTX_SOLO": 7, "T1_SOLO": 3, "RESCATE_SIN_DATO": 2}, "d9_capped_pub": 4, "pub_por_volcan": {"Tupungatito": 3, "NevadosDeChillan": 1, "Villarrica": 2, "PuyehueCordonCaulle": 6}}, "262-270": {"n": 146, "n_pub": 13, "clases_pub": {"RESCATE_SIN_DATO": 1, "CTX_SOLO": 10, "T1_SOLO": 2}, "d9_capped_pub": 3, "pub_por_volcan": {"Lascar": 1, "Lastarria": 1, "Villarrica": 1, "PuyehueCordonCaulle": 9, "Chaiten": 1}}, "ge270": {"n": 172, "n_pub": 25, "clases_pub": {"CTX_SOLO": 21, "T1_SOLO": 3, "AMBOS": 1}, "d9_capped_pub": 0, "pub_por_volcan": {"PlanchonPeteroa": 2, "Villarrica": 3, "Copahue": 1, "PuyehueCordonCaulle": 16, "Chaiten": 3}}, "t_bg?": {"n": 0, "n_pub": 0, "clases_pub": {}, "d9_capped_pub": 0, "pub_por_volcan": {}}}, "pos": {"lt262": {"n": 0, "n_pub": 0, "clases_pub": {}, "d9_capped_pub": 0, "pub_por_volcan": {}}, "262-270": {"n": 1, "n_pub": 1, "clases_pub": {"CTX_SOLO": 1}, "d9_capped_pub": 0, "pub_por_volcan": {"Villarrica": 1}}, "ge270": {"n": 0, "n_pub": 0, "clases_pub": {}, "d9_capped_pub": 0, "pub_por_volcan": {}}, "t_bg?": {"n": 0, "n_pub": 0, "clases_pub": {}, "d9_capped_pub": 0, "pub_por_volcan": {}}}}, "VIIRS375": {"neg_limpio": {"lt262": {"n": 152, "n_pub": 140, "clases_pub": {"AMBOS": 40, "T1_SOBRE_CTX": 19, "T1_SOLO": 71, "CTX_SOLO": 10}, "d9_capped_pub": 0, "pub_por_volcan": {"Lascar": 13, "Lastarria": 21, "Tupungatito": 13, "PlanchonPeteroa": 16, "NevadosDeChillan": 10, "Llaima": 13, "Villarrica": 12, "Copahue": 16, "PuyehueCordonCaulle": 11, "Chaiten": 15}}, "262-270": {"n": 119, "n_pub": 104, "clases_pub": {"AMBOS": 18, "T1_SOBRE_CTX": 23, "T1_SOLO": 59, "CTX_SOLO": 4}, "d9_capped_pub": 0, "pub_por_volcan": {"Lascar": 9, "Isluga": 7, "PlanchonPeteroa": 14, "NevadosDeChillan": 21, "Llaima": 5, "Villarrica": 7, "Copahue": 26, "PuyehueCordonCaulle": 6, "Chaiten": 9}}, "ge270": {"n": 101, "n_pub": 78, "clases_pub": {"T1_SOLO": 56, "AMBOS": 5, "T1_SOBRE_CTX": 14, "CTX_SOLO": 3}, "d9_capped_pub": 0, "pub_por_volcan": {"NevadosDeChillan": 13, "Llaima": 27, "Villarrica": 21, "Copahue": 6, "Chaiten": 11}}, "t_bg?": {"n": 1, "n_pub": 0, "clases_pub": {}, "d9_capped_pub": 0, "pub_por_volcan": {}}}, "pos": {"lt262": {"n": 40, "n_pub": 40, "clases_pub": {"AMBOS": 29, "T1_SOBRE_CTX": 11}, "d9_capped_pub": 0, "pub_por_volcan": {"Lascar": 2, "Lastarria": 9, "Tupungatito": 26, "PlanchonPeteroa": 3}}, "262-270": {"n": 56, "n_pub": 56, "clases_pub": {"AMBOS": 45, "T1_SOBRE_CTX": 9, "T1_SOLO": 2}, "d9_capped_pub": 0, "pub_por_volcan": {"Lascar": 16, "Isluga": 30, "PlanchonPeteroa": 5, "NevadosDeChillan": 2, "PuyehueCordonCaulle": 3}}, "ge270": {"n": 47, "n_pub": 47, "clases_pub": {"AMBOS": 44, "T1_SOBRE_CTX": 3}, "d9_capped_pub": 0, "pub_por_volcan": {"Isluga": 3, "NevadosDeChillan": 2, "Villarrica": 5, "PuyehueCordonCaulle": 29, "Chaiten": 8}}, "t_bg?": {"n": 0, "n_pub": 0, "clases_pub": {}, "d9_capped_pub": 0, "pub_por_volcan": {}}}}, "VIIRS750": {"neg_limpio": {"lt262": {"n": 313, "n_pub": 75, "clases_pub": {"T1_SOLO": 53, "T1_SOBRE_CTX": 6, "CTX_SOLO": 12, "AMBOS": 4}, "d9_capped_pub": 0, "pub_por_volcan": {"Lascar": 3, "Lastarria": 3, "Isluga": 2, "Tupungatito": 13, "PlanchonPeteroa": 9, "NevadosDeChillan": 4, "Llaima": 8, "Villarrica": 8, "Copahue": 4, "PuyehueCordonCaulle": 13, "Chaiten": 8}}, "262-270": {"n": 218, "n_pub": 52, "clases_pub": {"CTX_SOLO": 9, "T1_SOLO": 34, "T1_SOBRE_CTX": 5, "AMBOS": 4}, "d9_capped_pub": 0, "pub_por_volcan": {"Lascar": 2, "Isluga": 19, "PlanchonPeteroa": 6, "Llaima": 4, "Villarrica": 2, "Copahue": 5, "PuyehueCordonCaulle": 10, "Chaiten": 4}}, "ge270": {"n": 91, "n_pub": 6, "clases_pub": {"CTX_SOLO": 3, "AMBOS": 1, "T1_SOLO": 2}, "d9_capped_pub": 0, "pub_por_volcan": {"Llaima": 3, "Villarrica": 1, "Chaiten": 2}}, "t_bg?": {"n": 0, "n_pub": 0, "clases_pub": {}, "d9_capped_pub": 0, "pub_por_volcan": {}}}, "pos": {"lt262": {"n": 2, "n_pub": 2, "clases_pub": {"CTX_SOLO": 1, "AMBOS": 1}, "d9_capped_pub": 0, "pub_por_volcan": {"Lascar": 1, "PlanchonPeteroa": 1}}, "262-270": {"n": 9, "n_pub": 6, "clases_pub": {"CTX_SOLO": 3, "AMBOS": 3}, "d9_capped_pub": 0, "pub_por_volcan": {"Lascar": 2, "Villarrica": 1, "PuyehueCordonCaulle": 3}}, "ge270": {"n": 7, "n_pub": 5, "clases_pub": {"AMBOS": 4, "CTX_SOLO": 1}, "d9_capped_pub": 0, "pub_por_volcan": {"PuyehueCordonCaulle": 5}}, "t_bg?": {"n": 0, "n_pub": 0, "clases_pub": {}, "d9_capped_pub": 0, "pub_por_volcan": {}}}}}
```

En VIIRS 375 la tasa de publicación en negativos es alta en los tres tramos de temperatura de fondo y T1_SOLO manda en los tres: el fondo frío NO es donde se concentra la sobre-publicación de ese sensor. En VIIRS 750 sí hay escalón (los dos tramos fríos publican varias veces más que el tibio), pero lo que publica ahí sigue siendo sobre todo T1_SOLO, no el camino contextual. El tope de 5 MW sólo actúa en MODIS. Advertencia A68: `t_bg` bajo está contaminado por altitud y por estación, y cada tramo tiene otra mezcla de volcanes (ver `pub_por_volcan` en el crudo); esta tabla no separa cirrus de cumbre alta.

## 8. Veredicto sobre la hipótesis, por sensor

Hipótesis: *la sobre-publicación vive en los caminos que MIROVA no tiene.*

- **VIIRS 375: CONFIRMADA para el Test 1 integrado; REFUTADA para el test de temperatura de brillo (sustrato cero); SIN DATO para la compuerta de 3 K.** 186 de 322 negativos limpios publicados (57,8 %) dependen sólo del Test 1, contra 2 de 143 pasadas positivas. Sin él la tasa bajaría de 86,3 % a entre 21,4 % y 36,5 %, y de las 75 noches positivas 71 siguen seguro, 4 son SIN DATO y 0 se pierden seguro. Es la pareja que el plan pedía: mucha sobre-publicación, poco recall. Sensibilidad hasta el 2026-09-14: 59,0 % de T1_SOLO, mismo cuadro. Pero queda un piso que el Test 1 no explica: entre 21,4 % y 36,5 % de los negativos limpios se seguirían publicando por el camino contextual, que es el del paper.

- **VIIRS 750: CONFIRMADA para el Test 1 integrado, con n chico del lado del recall.** 89 de 133 (66,9 %); la tasa iría de 21,4 % a entre 5,3 % y 7,1 %. Ninguna de las 13 pasadas positivas publicadas es T1_SOLO. Son sólo 14 noches positivas.

- **MODIS: REFUTADA en lo medible.** 38 de 50 negativos publicados (76,0 %) son CTX_SOLO, el camino del paper, y se concentran en PCC; el Test 1 sostiene 8. Lo que queda por medir en MODIS (banda 21 y compuerta, D21 y D22) actúa DENTRO del camino contextual y no se puede separar desde lo persistido: SIN DATO. Recall: un solo positivo, SIN DATO.

- **Camino contextual sobre fondo frío con tope de 5 MW (D9):** como camino separado no existe en la máscara actual (el `dnti_ctx` legacy es diagnóstico). Lo que existe es el tope, que sólo actúa en MODIS. PARCIAL: hay escalón de fondo frío sólo en VIIRS 750, y lo que publica ahí es sobre todo el Test 1, no el camino contextual.

**Lo que este resultado NO dice.** "MIROVA calló" no es "artefacto" (A54). Los T1_SOLO de Villarrica y Copahue son, con toda probabilidad, en parte calor real (lago de lava, lago cratérico ácido) que MIROVA no publica: el Test 1 se adoptó en S27 justo por eso. La mediana publicada de esa clase es de centésimas de MW. La tabla dice dónde está la palanca de PARIDAD, no qué es real. Eso empuja hacia la Fase 2b del plan (mudar al perfil experimental, no borrar), que es decisión de Nicolás.

## 9. Qué brazos de A/B tienen sustrato y cuáles no

| brazo del plan (Fase 2, paso 3) | sustrato | comentario |
|---|---|---|
| sin Test 1 integrado | **ALTO en VIIRS 375 y 750**, bajo en MODIS | es el brazo que hay que correr primero. El criterio de recall debe listar las noches SIN DATO de la sección 4 una por una |
| sin test de temperatura de brillo (N·σ 5/10) | **CERO** | ya está apagado por flag y el contador es 0 en toda la ventana. No correr. Corregir los documentos que lo dan por activo (V-08 es un hallazgo de cita, no de comportamiento) |
| Test 1 por píxel literal (NTI > K1) en reemplazo | casi cero | `diag_n_nti_path > 0` en 5 pasadas de V375 y 0 en el resto: no recupera nada de lo que el integrado sostiene |
| banda 22 más sin compuerta (D21 y D22) | **SIN DATO** | la compuerta es un Y lógico: quitarla sólo puede AGREGAR píxeles al primer pase, así que no puede ser la causa de la sobre-publicación actual; puede aumentarla. El segundo pase ya opera sin compuerta. Medirlo exige el probe |
| co-validación del contextual en fondo frío (Fase 3) | bajo en V375 y en MODIS, medio en V750 | en V375 el fondo frío no concentra nada; MODIS publica más con fondo tibio que frío y el grueso es PCC; en V750 hay escalón pero lo sostiene sobre todo el Test 1 (tabla de la sección 7) |

**Probe de sólo lectura para llevar a N3 lo que quedó SIN DATO (especificado, NO ejecutado).** Patrón A75, en GitHub Actions (MODIS no corre en Windows), sin escribir en `data/`:
1. Entrada: la lista de pasadas de `resultados_sustrato.json` con clase T1_SOBRE_CTX o RESCATE_SIN_DATO, más una muestra estratificada por volcán de AMBOS y CTX_SOLO en negativos limpios, más todas las pasadas de las noches SIN DATO. Un job por volcán, en serie (A47), `data_subdir` temporal fuera del repo.
2. Monkeypatch por etapa, reusando el preámbulo real: envolver `first_pass_tests_2_and_3`, `second_pass_adjacent` y `compute_test1_mir` para capturar sus máscaras; capturar `ctx_cluster_anchor` (el cúmulo contextual con su VRP antes de que el Test 1 lo pise).
3. Por pasada, ensamblar cuatro variantes con el MISMO código aguas abajo y pasar cada record por el predicado del dashboard con node: (a) control; (b) `compute_test1_mir` devuelve `triggered = False`; (c) `apply_bt_gate = False` en el primer pase (los flags de D22 ya existen, apagados); (d) segundo pase identidad.
4. Salida por pasada: publica sí o no en cada variante, VRP del cúmulo contextual, número de píxeles por etapa dentro y fuera del radio interno. Control positivo del probe: la variante (a) debe reproducir el record persistido campo por campo; si no, el probe no es fiel y se descarta. Nulo: las mismas variantes sobre pasadas sin detección no deben crear publicaciones en (b) ni en (d).
5. Contar las pasadas efectivamente procesadas por job contra la lista de entrada antes de leer el resultado (A108).

## 10. Límites de este informe

- N3 es por lógica del código sobre campos persistidos, no por re-ejecución. Supone que apagar el Test 1 no cambia nada más aguas arriba; se verificó en el código que el Test 1 no entra a la máscara ni al fondo (`ENABLE_TEST1_K1_BG_EXCLUDE = False`, `ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK = False`), pero no se ejecutó.
- En MODIS un T1_SOLO podría ser rescatado por `store.py` (`cluster_rescue`) al apagar el Test 1: ahí N3 es una cota, no un hecho.
- Ventana de 20 días de fines de invierno. Llaima y Copahue sin positivos. MODIS con un positivo.
- Los negativos limpios de los últimos días son más blandos porque el OCR llega con atraso; la sensibilidad cortada al 2026-09-14 da el mismo cuadro y está en `contrafactual_sin_test1` del JSON.
- Todo lo anterior es hallazgo del que midió. Falta el verificador con contexto limpio que pide el plan.
