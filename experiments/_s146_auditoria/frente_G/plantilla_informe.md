# Frente G (S146): inventario de todo lo que hoy puede cambiar lo que el operador ve

> Auditoría de sólo lectura. No se modificó ningún archivo existente: ni `pipeline/`, ni `frontend/`, ni
> perfiles, ni `data/`, ni `CLAUDE.md`, ni docs. No se corrió pytest, no se descargó nada, git sólo para leer.
> Todo lo que este informe afirma sale de una herramienta ejecutada en esta sesión; los scripts y sus salidas
> están en `experiments/_s146_auditoria/frente_G/`. Este archivo lo arma `armar_informe.py` desde
> `plantilla_informe.md` más `tabla_inventario.md` (generada por `construir_inventario.py`): los valores
> efectivos de los flags y las fechas de git no están transcritos a mano.
> Régimen de todas las huellas medidas: records de los 11 Tier A desde el 2026-09-01 (posterior a #535).

## 0. Lo que pasa físicamente, antes de la tabla

Cada pasada nocturna entrega dos imágenes del volcán: una en infrarrojo medio, que reacciona mucho a un
punto muy caliente aunque sea chico, y una en térmico, que sigue la temperatura media del suelo. Entre esas
dos imágenes y el punto rojo que ve el operador hay una cadena de nueve etapas. El paper de MIROVA describe
una parte corta de esa cadena (leer, recortar, comparar cada píxel con sus vecinos, sumar la energía de los
píxeles alertados). Todo lo demás lo fuimos poniendo nosotros, casi siempre para curar un caso concreto:
un glaciar que inflaba la suma, un salar que robaba la posición, un lago que parecía caliente.

Lo que este inventario muestra es que **varias de esas curas actúan sobre el mismo número una detrás de
otra, y algunas se deshacen entre sí**. La más importante para la brecha de VIIRS 375: el detector propio
"Test 1 integrado" no pregunta si hay un píxel caliente, pregunta si el disco de 3 km alrededor del cráter
tiene dispersión de temperatura. Medido acá con ruido puro, sin ningún cuerpo caliente, su criterio
"3 sigma" se cumple el 100 % de las veces a la resolución de 375 m. Lo único que lo frena es un piso
relativo de 2 %, que se supera con cerca de 1 K de contraste espacial dentro del disco: una cumbre con
roca y nieve lo cumple casi cualquier noche. Y cuando dispara, el ancla honesta lo pone a 0,0 km del
cráter, de modo que la cerca por distancia del dashboard ya no tiene nada que frenar.

## 1. COBERTURA

**Recorridos enteros (lectura línea a línea de la parte ejecutable):** `pipeline/process_viirs.py`
(l. 222 a 2229), `pipeline/store.py`, `pipeline/anchor.py`, `pipeline/single_pixel_mode.py`,
`pipeline/f5_core.py`, `pipeline/geo_utils.py`, `pipeline/clustering.py` (`cluster_hotspots` y
`cluster_pixels_geographic`), `scripts/run_pipeline.py` l. 116 a 360 (todos los callers de los tres
procesadores y de `store.append_record`), `scripts/build_recent_json.py` (cabecera y filtro).

**Recorridos por tramos dirigidos:** `pipeline/process_modis.py` (l. 484 a 663, 995 a 1215 y búsquedas),
`pipeline/test1_integrated.py` (cabecera, l. 129 a 182, 372 a 446), `pipeline/profile.py` (definiciones de
lectura de claves), `frontend/index.html` (l. 780 a 800, 1036 a 1240, 1425 a 1530).

**Sólo por búsqueda:** `pipeline/process_viirs_mod.py`, `pipeline/detection_context.py`, `pipeline/fetch.py`,
`pipeline/scan_geometry.py`, `pipeline/vrp_regimes.py`, `pipeline/path_d_cap.py`, `frontend/diario.html`,
`frontend/mosaico.html`, `.github/workflows/*.yml`, `scripts/auto_audit_weekly.py`,
`scripts/clasificar_referencia.py`, `scripts/banco_paridad.py` (reutilizado para ejecutar el predicado).
Lo que sólo se buscó puede esconder un literal que no vi: **`process_viirs_mod.py` y `detection_context.py`
no tienen cobertura completa**, y ahí la tabla vale como piso.

**No abiertos:** `pipeline/regrid.py`, `exclusion_zones.py`, `test1_spatial_core.py`, `detect_tirvolch.py`,
`mirova_csv_loader.py`, `audit_metrics.py`, `constants.py`, `product_version.py`, `diag_fondo.py`,
`frontend/comparacion.html` (se comprobó por script que no contiene ninguna de las funciones del predicado).
Ningún PDF (lo hace otro frente).

**Atributos de `pipeline.profile`:** {{N_ATTR}} con `VRP_PROFILE=mirova_equivalent`
(`volcar_perfil.py`, salida `perfil_efectivo.json`). **Clasificados {{N_ATTR}} de {{N_ATTR}}**: {{N_CITADOS}} citados
en alguna de las {{N_FILAS}} filas de la tabla y {{N_DEP}} como parámetros de un camino apagado o metadatos
(sección 6). Se resolvió de qué sección del YAML lee el código cada uno (`declarado_vs_leido.py`):
**0 claves escritas en una sección distinta de la que se lee**, y **56 atributos toman su valor del
default de `profile.py` porque la clave no está escrita en el YAML operacional**. Entre esos 56 están los
cuatro umbrales del Test 1 integrado (`TEST1_K_SIGMA`, `TEST1_MIR_RELATIVE`, `TEST1_ROI_KM`,
`TEST1_INNER_RING_KM`), los C2 de los Tests 2 y 3 y el flag de los filtros de no aptos.

**Reglas por volcán:** `volcanoes.yaml` completo por script (`reglas_por_volcan.py`): 45 volcanes, 11 con
excepciones; los otros 34 sólo llevan `radius_km: 5` y ninguna otra clave de detección.

**Predicado del dashboard:** extraídas y comparadas por hash las 14 funciones del predicado en las cuatro
vistas (`comparar_frontend.py`); el predicado de `index.html` se ejecutó con node sobre las 2.360 pasadas del
régimen (`huellas_en_records.py`, vía `scripts/banco_paridad.correr_node`, sin portarlo a Python).

**Fechado:** `git log -S` por atributo sobre `pipeline/profile.py` y `git log -G` sobre la línea del YAML
(`fechar_mecanismos.py`, `declarado_vs_leido.py`), más `git log -S` manual para `volcanoes.yaml`,
`store.py` y `frontend/index.html`. El número de PR se da sólo donde aparece en el asunto del commit.

**Conteo por clase de origen (filas):** {{CONTEO}}

## 2. La tabla, ordenada por etapa de la cadena

Leyenda de "origen": ESTA EN EL PAPER vale sólo como "según tal documento del proyecto"; este frente no
abrió ningún PDF. NUESTRO Y DECLARADO nombra la D del catálogo o la regla que lo reconoce. NUESTRO Y NO
DECLARADO significa que ni `docs/MIROVA_DIVERGENCES.md` ni `docs/MISSION.md` lo tienen como divergencia
(búsqueda por nombre del mecanismo y por sus sinónimos; los ceros se confirmaron con una segunda búsqueda
por el nombre con que lo lee el código).

{{TABLA}}

### 2.1 La contracara: lo que según el catálogo el paper hace y nosotros no

| qué hace el paper (según el catálogo) | D | flag | valor efectivo | estado |
|---|---|---|---|---|
| Remuestrea el gránulo a una grilla UTM regular antes de detectar | D17 | `ENABLE_UTM_REGRID` | {{ENABLE_UTM_REGRID}} | no se hace; el área fija al nadir (G-10) es lo único que lo aproxima |
| Trata el bow tie de MODIS | D28 | no existe | | no se hace en ningún paso |
| Banda 22 primaria en MODIS, 21 sólo donde la 22 satura | D21 | `ENABLE_MODIS_B22_PRIMARY` | {{ENABLE_MODIS_B22_PRIMARY}} | no se hace |
| NTI de MODIS con banda 32 | D20 | no existe | | no se hace |
| Tests 2 y 3 sin condición de temperatura | D22 | `ENABLE_TESTS_23_NO_BT_GATE_VIIRS375` (sólo V375; MODIS y V750 no tienen flag) | {{ENABLE_TESTS_23_NO_BT_GATE_VIIRS375}} | no se hace en el primer pase; el segundo pase nunca tuvo compuerta (ver I-6) |
| Test 1 por píxel (NTI > K1) como camino de detección | D23 | no existe | | se calcula y la máscara del primer pase lo pisa |
| Retira los píxeles del Test 1 del pool de mu y sigma y de los pasos siguientes | GAP A dentro de D11 | `ENABLE_TEST1_K1_BG_EXCLUDE`, `ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK` | {{ENABLE_TEST1_K1_BG_EXCLUDE}}, {{ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK}} | no se hace |
| Conserva los píxeles saturados | D24 | no existe | | se eliminan (G-07), y en VIIRS también (G-05, G-06, no declarado) |
| Fondo del VRP = media de los vecinos no alertados del píxel | D25 | `ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375`, `..._VIIRS750` (MODIS no tiene) | {{ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375}}, {{ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750}} | no se hace |
| Segundo pase con los filtros de no aptos | D26 | no existe | | no se hace |
| Tabla 1 diurna | D27 | `ENABLE_DAYTIME_MODIS` | {{ENABLE_DAYTIME_MODIS}} | deliberado |
| Refit iterativo a 3 sigma de la regresión de NTIbk | D29 | parámetro `iterative_refit` de `compute_eti_scene_quadratic` (`detection_context.py:699-795`) | SIN DATO: no tracé con qué valor lo llama el primer pase | SOSPECHA, no verificado |
| ROI1 = caja de 5 x 5 km | D18 | `ENABLE_ROI1_BOX_PAPER` | {{ENABLE_ROI1_BOX_PAPER}} | no se hace |
| Conectiva de los Tests 2 y 3 según la prosa (`max`) | S136 | `ENABLE_TESTS_23_PROSE_BRANCH` | {{ENABLE_TESTS_23_PROSE_BRANCH}} | rige `min` |

## 3. Los ES NUESTRO Y NO DECLARADO, por peso

Ordenados por cuánto pueden pesar en la sobre-publicación de VIIRS 375 primero, y en la magnitud después.
Cada uno trae cómo medir su efecto sin tocar el pipeline.

**G-27. El criterio "3 sigma" del Test 1 integrado se cumple sin señal.** Peso: el mayor del inventario.
El fenómeno: el test suma, sobre el disco de 3 km, sólo los excesos positivos de cada píxel respecto de la
mediana del anillo. En un campo de puro ruido la mitad de los píxeles queda sobre la mediana, así que la
suma no tiene media cero: vale cerca de 0,4 sigma por el número de píxeles, mientras el umbral crece sólo
con la raíz de ese número. Con los 208 píxeles que caben en el disco a 375 m el umbral queda superado
siempre. Medido con la función real `compute_test1_mir` y los parámetros efectivos del perfil
(`nulo_test1_ruido_puro.json`, 300 campos por celda): el criterio absoluto pasa 100 % en VIIRS 375,
35 a 55 % en VIIRS 750 y 13 a 19 % en MODIS, **el mismo orden que la sobre-publicación medida por sensor
(86,3 %, 21,4 %, 11,4 %)**. El disparo completo depende entonces del piso relativo de 2 %: 0 % con
0,5 K de dispersión, 84 % con 1,0 K, 100 % con 1,5 K. En los records reales el `test1_k_observed` de las 800
pasadas V375 disparadas tiene mediana 4,86 con 70 píxeles contribuyentes (`k_observado_vs_nulo.json`); el
nulo de ruido puro predice 5,75 y 104 para un disco lleno, o sea que el disparo típico es compatible con
no tener ninguna fuente. Esto no dice que el lago de lava de Villarrica no exista: dice que este estadístico
no lo distingue de una cumbre con textura. D30 declara que el detector es propio; no declara esto.
*Cómo medirlo sobre lo persistido:* no hay campo de dispersión del disco, pero `diag_sigma_bg_k` y
`test1_k_observed` sí están: cruzar `triggered_test1` contra `test1_k_observed / (0,4 raíz(2 n_test1_pixels))`
por etiqueta (negativo limpio, positivo) con el banco de paridad. Si la razón es ~1 en los negativos y
mayor en los positivos, el nulo explica la sobre-publicación. Un umbral corregido por la media del nulo se
puede simular sin reproceso porque `test1_k_observed` y `n_test1_pixels` están persistidos.

**G-19 (con G-18). Un contador "de diagnóstico" decide qué fuente se publica.** `only_test1_source` declara
al Test 1 "fuente única" cuando los contadores de los caminos legacy (BT, NTI, dNTI contextual, ETI) están
en cero. Pero la máscara real hoy son los Tests 2 y 3, que no entran en esa cuenta. Medido
(`huellas_en_records.json`): **132 pasadas VIIRS 375 y 16 VIIRS 750** con Test 1 disparado, píxeles
contextuales reales en la máscara y los contadores legacy en cero; ahí el Test 1 gana la fuente, rehace el
cúmulo y los píxeles publicados sólo con los suyos, y el cúmulo contextual (el camino del paper) se descarta
sin quedar escrito. El verificador de la Fase 1 lo vio como subclase `fuente_unica` (35 negativos limpios);
acá está el mecanismo y el total. El camino D legacy además decide la magnitud: filtra qué píxeles del
Test 1 cuentan en VIIRS 375 (G-38) y cuáles del cúmulo cuentan en MODIS y VIIRS 750 (G-39), con su propia
compuerta de 3 K y un umbral distinto del que arma la máscara.
*Cómo medirlo:* la lista ya es reproducible con `huellas_en_records.py`; para saber cuánto cambia la
publicación hace falta el VRP del cúmulo contextual pisado, que no se persiste (mismo SIN DATO que la Fase 1).
El probe A75 especificado en la Fase 1 lo cubre si captura `ctx_cluster_anchor` antes del pisado.

**G-47 y G-51 con G-41. Dos correcciones de magnitud apiladas en VIIRS 375 que se deshacen.** El modo de un
píxel (pipeline) cambia la suma del cúmulo por su píxel máximo cuando hay menos de 5 MW y hasta 3 píxeles:
está activo en 837 de 849 cúmulos VIIRS 375. Después el núcleo F5' (store y dashboard) vuelve a sumar los
píxeles persistidos a 0,75 km del pico o con BT de 295 K o más, **incluidos píxeles que no son del cúmulo**.
Medido (`apilamiento_f5_single_pixel.json`): F5' difiere de `pc.vrp_mw` en 159 de 830, y en 152 es MAYOR; en
los 82 records donde el modo de un píxel había cambiado el número, la mediana de F5'/pc es 1,74; en 80
records el cúmulo tiene un solo píxel y F5' igual suma otros. Ninguno de los dos mecanismos figura en el
catálogo ni en MISSION. La cifra de paridad 0,68 de CLAUDE.md A10 es el resultado neto de los dos.
*Cómo medirlo:* todo está persistido (`f5_core_vrp_mw`, `pc.vrp_mw`, `pc.single_pixel_mode`,
`anomaly_pixels`): cuatro brazos offline contra MIROVA (suma del cúmulo, máximo, F5' sobre suma, F5' sobre
máximo) con el banco de paridad, por volcán.

**G-45 con G-50. El tope de Villarrica no llega al operador.** El tope pone `vrp_mw` en cero cuando el cúmulo
pasa de 12 píxeles, para no publicar el glaciar Pichillancahue. Pero el dashboard no lee `vrp_mw`: lee
`pc.vrp_mw`, y `isSummitDetection` sólo oculta un record descartado si además `triggered_test1` es falso.
Medido: 13 records topados en el régimen, **8 publicados igual** (los 7 de VIIRS 750, todos con
`triggered_test1`, y 1 de MODIS), con `vrp_mw = 0` y `pc.vrp_mw` entre 0,05 y 4,9 MW. La misma salida de
escape publica 49 records VIIRS 375, 12 VIIRS 750 y 44 MODIS que llevan `discarded_reason`.
*Cómo medirlo:* ya medido; para la historia completa correr `apilamiento_f5_single_pixel.py` sin el corte
de fecha.

**G-44. La geocerca por píxel deshace la caja que recupera las esquinas.** La ROI es una caja de más o menos
25 km (diagonal 35 km) "para recuperar las esquinas donde MIROVA publica" (comentario S15); al guardar, los
píxeles a más de 25 km del centro se descartan y `vrp_mir_mw` se recalcula, y el record queda con
`discarded_reason = partial_eruption_hotspot_too_far`. Pasa en **432 de 457 records MODIS**, 19 VIIRS 375 y
4 VIIRS 750. No cambia `pc.vrp_mw`, pero marca casi todo MODIS como "descartado parcial", que es justo el
campo que `isSummitDetection` mira (G-50).
*Cómo medirlo:* contar `discarded_n_pixels` y cruzar con `Distancia_km` de MIROVA mayor que 25.

**G-05 y G-06. En VIIRS los píxeles saturados desaparecen.** D24 lo declara para MODIS; en VIIRS nadie. La
banda I04 satura cerca de 367 K: en una fase efusiva el píxel del foco queda NaN y no entra ni a la máscara
ni a la magnitud. Hoy no pesa (no hay fase efusiva); pesa el día que importe. SIN DATO de frecuencia: no deja
huella. *Cómo medirlo:* sólo con un probe sobre gránulos (contar `qf & 4` dentro del inner).

**G-33. Rescate de cúmulo F47 en MODIS** con geocerca de 25 km: 4 records del régimen, los 4 publicados.
Sin D propia. *Cómo medirlo:* `final_hotspot_source == cluster_rescue`.

**G-13 (parte). Mínimo de 10 píxeles de fondo como literal**, y en MODIS "sin fondo" significa "sin record"
(`return None`), mientras VIIRS guarda el record sin detección: asimetría que cambia los denominadores de
cualquier tasa por pasada. *Cómo medirlo:* comparar pasadas por noche y sensor contra el catálogo CMR.

**G-02 y G-03. Infraestructura que cambia lo publicado sin dejar rastro en la D:** el reemplazo NRT a
Standard (el 13 % de los records V375 del régimen todavía son NRT) y los cortacircuitos que pueden dejar una
pasada sin procesar (A108). *Cómo medirlo:* `product_version` y el conteo de pasadas por job.

**Configuración invisible (no es un mecanismo, es dónde vive):** 56 atributos rigen desde el default de
`profile.py`. Un lector del YAML operacional no puede saber que el Test 1 integrado usa k = 3, piso 2 %,
disco de 3 km y anillo desde 1 km, ni que los filtros de no aptos están encendidos. Lista completa en
`declarado_vs_leido.json`.

## 4. Apilamientos e interacciones

- **I-1. Ancla honesta contra cerca por distancia (G-32 con G-49).** Cuando gana el Test 1 la posición
  publicada es el cráter exacto. Medido (`interacciones.json`): los 348 records `test1_roi` de VIIRS 375 y
  los 138 de VIIRS 750 tienen `final_hotspot_dist_km = 0` y `distance_class = summit`, el 100 %. En 328 de
  los 348 el centroide del cúmulo que aporta la magnitud está a más de 1 km del cráter. La cerca del
  dashboard, pensada para frenar lo lejano, queda sin efecto sobre el camino que sostiene la mayoría de la
  sobre-publicación. Es la cara de posición de D19 y D11-bis, y está declarada; lo que no está dicho es que
  anula a G-49.
- **I-2. Modo de un píxel más F5'** (sección 3): la segunda deshace a la primera en VIIRS 375.
- **I-3. Tope de Villarrica más `isSummitDetection`** (sección 3): el filtro escribe en un campo que el
  operador no ve.
- **I-4. Caja de 35 km de diagonal más geocerca de 25 km** (G-12 con G-44).
- **I-5. Un camino apagado sigue siendo condición de otros.** Con `ENABLE_BT_PATH_HOT = False` el contador
  `n_bt_path` vale cero siempre; aun así es condición de `only_test1_source` (G-19) y del tope de 5 MW
  (G-40: "sólo contextual" pasó a ser casi siempre verdadero, y el tope depende en los hechos sólo de
  `t_bg < 270 K`). Apagar G-16 cambió el significado de G-19 y G-40 sin tocar su código.
- **I-6. El segundo pase deshace la compuerta del primero.** La compuerta de 3 K (D22) vive sólo en el primer
  pase. Medido: en **230 pasadas VIIRS 375 y 139 VIIRS 750 el primer pase da 0 píxeles y el segundo pase
  "recaptura" alguno**, o sea detecta solo, sin conjunto activo del cual ser adyacente y sin compuerta
  (en MODIS pasa 1 vez). D19 declara que corre sin conjunto activo; la consecuencia (la compuerta D22 es
  permeable en VIIRS) cambia cómo leer cualquier A/B de D22: quitar la compuerta del primer pase puede mover
  poco porque el segundo pase ya opera sin ella.
- **I-7. El fondo con que se detecta no es el fondo con que se mide, y cambia por volcán y por camino**
  (G-37). En VIIRS 375 un mismo volcán puede publicar, en dos pasadas de la misma noche, una magnitud contra
  el núcleo 3 x 3 (si publicó el cúmulo contextual y el volcán es uno de los 5 opt-in), contra el anillo
  1,5 a 3 km (si ganó el Test 1 y es Láscar, NdC o Lastarria) o contra el anillo 1 a 3 km del propio Test 1
  (los otros ocho). En VIIRS 750 el núcleo 3 x 3 no existe aunque el volcán lo tenga pedido
  (`process_viirs_mod.py:460-467` lo declara como TODO desde S72). Lastarria es el único volcán con las dos
  excepciones a la vez.
- **I-8. Tres magnitudes apiladas en MODIS:** fondo por núcleo (5 volcanes), luego núcleo focal (todos),
  luego tope de 5 MW, luego modo de un píxel. El orden importa: el tope deja el cúmulo en 5,0 MW exactos y el
  modo de un píxel exige menos de 5, así que un cúmulo topado nunca pasa al máximo por píxel.

## 5. Divergencias entre las tres copias del frontend

Comparación por hash del cuerpo normalizado (`frontend_funciones.json`):

| función | index | mosaico | diario |
|---|---|---|---|
| `f5CoreMagnitude`, `_havKm` | referencia | idéntica | idéntica |
| `mirovaEqVrp` | referencia | idéntica | **distinta**: sin cúmulo devuelve `vrp_mw` sin el tope de 50.000 y sin el respaldo a `vrp_mir_mw`; aplica la cerca de `distance_class` también a los records sin cúmulo (index no) |
| `mirovaEqVrpCore`, artefactos | referencia | equivalente (sin `includeFar`) | equivalente (toma el nombre del volcán) |
| `isValidDetection` | referencia | equivalente | **no existe** |
| `isSummitDetection` | referencia | idéntica | **no existe** |
| niveles de alerta | 1/10/100/1000 | idénticos | no tiene |
| radio interno | del arreglo de volcanes, respaldo 10 km | del arreglo, sin respaldo | tabla propia `INNER_RADIUS_KM`, respaldo 5 km |

`diario.html` decide "hay detección" sólo con `eqVrpDisplay > 0`. Como no tiene `isSummitDetection`, no aplica
la regla "record descartado sin Test 1 no se muestra": un record con `vrp_mw = 0`, `discarded_reason` y
`triggered_test1` falso que index oculta, diario lo grafica (caso real del régimen: Villarrica MODIS_AQUA 2026-09-01 07:35, topado por G-45, `summit`, `pc.vrp_mw` 5,0, Test 1 falso). Los radios internos están escritos en cuatro
lugares (YAML y tres HTML); hoy coinciden los 11 (comprobado por script). El estado del toggle F5' se guarda
con tres claves distintas de `sessionStorage`, así que dos vistas abiertas pueden mostrar magnitudes distintas
del mismo record. `comparacion.html` no tiene ninguna de estas funciones (deliberado según CLAUDE.md).

## 6. Flags muertos, anulados o con sustrato cero (candidatos a limpiar, no a tocar ahora)

- **Anulado por otro flag:** camino A de temperatura de brillo con todos sus umbrales (G-16);
  `enable_exclude_zones` con zonas todavía escritas en 5 volcanes (G-25); `lava_lake_magmatic` de Villarrica
  (flag Eq. 16 apagado); `local_kernel_bg` en VIIRS 750 (parámetro aceptado, sin implementación).
- **Sustrato cero en el régimen (0 records):** máscara de nube, tope de cordura de 50.000 MW, piso de VRP,
  Regla D vent en store, los dos filtros de artefacto del display (0 de 2.360 pasadas), tope de 5 MW en los
  dos VIIRS, `diag_n_eti_path`, `n_nti_rel_path`, `vrp_tir_mw`.
- **Importado y no leído en ninguna condición:** `ENABLE_ERUPTION_PATH` (aparece sólo en los import de los
  tres procesadores); `VRPTIR_K_TIR_I5` (0 usos fuera de `profile.py`). SOSPECHA hasta confirmarlo con una
  segunda herramienta sobre `scripts/` y `experiments/`.
- **Guard casi sin sustrato:** coherencia A46 (1 record MODIS).
- **Parámetros de caminos apagados** (de `inventario.json`, `atributos_dependientes`):

{{DEPENDIENTES}}

## 7. VERIFICADO LIMPIO

- Ninguna clave del YAML operacional está escrita en una sección distinta de la que lee `profile.py`
  (140 atributos resueltos). Las únicas claves del YAML que el código no lee son `profile`, `description` y
  `data_subdir` de cabecera.
- El Test 1 no entra a la máscara ni al fondo con los flags de hoy; coincide con la Fase 1 y su verificador.
- `inner_radius_km` coincide en `volcanoes.yaml` y en las tres vistas para los 11 volcanes.
- `f5CoreMagnitude` es idéntica en las tres vistas y el dashboard usa el valor persistido cuando existe.
- Los tres filtros nocturnos usan el mismo umbral.
- No hay ningún `VOLCANO_OVERRIDES` en el perfil operacional, ni overrides de C1 o C2.
- El post-proceso de clasificación de S146 no está cableado a ningún workflow ni a ninguna vista: no cambia
  lo que el operador ve.

## 8. Límites

- La clase ESTA EN EL PAPER se apoya en documentos del proyecto, no en los PDF.
- "No declarado" significa cero menciones en `docs/MIROVA_DIVERGENCES.md` y `docs/MISSION.md` al momento de
  la búsqueda; otro agente está editando esos dos archivos hoy.
- El nulo del Test 1 es de ruido blanco sin correlación espacial sobre grilla regular; un campo real tiene
  textura correlacionada y un disco con menos píxeles fuera del nadir. Sirve para mostrar que el estadístico
  no tiene media cero, no para fijar una tasa.
- Las huellas son de 20 días de fin de invierno.
- Todo esto es hallazgo del que midió. Falta el verificador con contexto limpio.
