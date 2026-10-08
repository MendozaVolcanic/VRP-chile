# Auditoría S150, frente C: magnitudes y constantes del pipeline en régimen de erupción

Auditor C, 2026-10-08 (hora del servidor de GitHub 18:25 UTC). Sólo lectura sobre `pipeline/`,
`store.py`, `volcanoes.yaml` y los JSON de `data/mirova_equivalent/`. Scripts y salidas en
`experiments/_s150_audit/C/`.

**Eje que estrena esta auditoría**: el régimen fuerte. Las 149 sesiones anteriores midieron las
compuertas contra señales de 0,05 a 0,5 MW; acá cada constante se pregunta qué hace con 2 a 50 MW,
muchos píxeles y focos múltiples.

**Datos**: `data/mirova_equivalent/NevadosDeChillan.json` local, idéntico al remoto (último commit del
archivo 85be8ec21, 2026-10-02 12:34 UTC, comprobado con `gh api` a las 18:25 UTC del 2026-10-08: el
relleno del apagón del 3 al 8 de octubre todavía no llegó). Referencia de MIROVA: CSV consolidado
(tabla, decide) y OCR (aparte), bajados hoy de `MendozaVolcanic/Mirova-v1` main a
`experiments/_s150_audit/C/`. Pareo: misma familia de sensor, ±8 min, sólo filas `ALERTA*`. Ventana
general del pareo: desde 2026-03-01 (A119: tabla sana desde marzo); denominador, 16.837 pasadas con
`primary_cluster`, 1.326 pareadas a una alerta de la tabla. Control positivo del pareo: el par
NdC 2026-10-01 08:35 MODIS_AQUA contra 5,18 MW aparece (`c02_pares.csv`).

**Perfil**: resuelto como lo lee el código, `VRP_PROFILE=mirova_equivalent python -c "import
pipeline.profile as p"`, volcado completo en `perfil_resuelto_mirova_equivalent.txt`.

---

## C-01. El tope D9 de 5 MW es, en MODIS, un techo de magnitud que depende sólo de que el fondo esté bajo 270 K

- **ARCHIVO:LÍNEA**: `pipeline/process_modis.py:663-665` (camino BT forzado a cero porque
  `ENABLE_BT_PATH_HOT = False`), `:1009-1016` (predicado del tope), `:1078` (escena),
  `:1171-1174` y `:1422-1423` (cúmulo primario, contextual y Test 1); simétricos en
  `pipeline/process_viirs.py:1414-1421`, `:1558`, `:2012` y `pipeline/process_viirs_mod.py:987-993`,
  `:1084`, `:1327`. Perfil: `PATH_D_ONLY_CAP_MW = 5.0`, `PATH_D_ONLY_CAP_TBG_MAX_K = 270.0`.
- **SCRIPT:SALIDA**: `c05_compuertas_magnitud.py` → `c05_salida.txt`; `c03_analisis.py` → `c03_salida.txt`.
- **QUÉ PASA**. Fenómeno: en una noche de primavera o invierno el anillo de fondo de los volcanes del sur
  (nieve, cumbres) está bajo 270 K casi siempre, y un píxel MODIS de 1 km con un cráter activo casi nunca
  llega a NTI > -0,8, porque para eso necesita del orden de 8 MW por píxel. Código: el tope se diseñó
  para el cirrus (D9) con la condición «ni el camino BT ni el NTI vieron nada y el fondo está frío». Pero
  el camino BT está apagado en el perfil, así que `n_bt_path` vale 0 siempre, y el NTI no dispara en
  MODIS: medido, **el 99,9 % de los records MODIS con cúmulo tienen `n_nti == 0`** (toda la historia,
  11 Tier A). La condición queda reducida a `t_bg < 270 K`, y con ella el cúmulo primario MODIS
  publicado no puede pasar de 5,00 MW. No hay detector de cirrus: hay un techo estacional.
- **Medición**. En la ventana de la erupción de Chillán (desde 2026-09-28) el predicado estuvo activo en
  8 de 10 pasadas MODIS, 14 de 16 V750 y 14 de 21 V375 (reconstruido `t_bg < 270 ∧ n_nti == 0`). Desde
  el 2026-09-20 hay 11 records MODIS de Chillán con `d9_capped` (todos rotulados `far`, ninguno pareado a
  una alerta de MIROVA). En toda la historia hay **303 records con cúmulo > 5 MW y `n_nti == 0` que se
  salvaron sólo porque el fondo estaba en 270 K o más** (256 MODIS, 47 V750; ejemplo PCC 2025-04-27 07:00,
  233 MW con `t_bg` 270,9 K: con un grado menos habría salido 5,00). El tope ya publicó **134 cúmulos
  `summit` dentro del inner en exactamente 5,0 MW** desde marzo (89 de PCC). Contra MIROVA, el tope no ha
  recortado todavía ninguna alerta de la tabla con valor > 5 MW (1 par recortado en la tabla, Villarrica
  0,9 MW; 1 en OCR, Láscar V750 2026-03-29 05:36, MIROVA 5,0).
- **Agravante**: el record no guarda el valor anterior al tope (claves del record NdC 2026-10-02 07:35:
  sólo `d9_capped: true`), así que nadie puede saber cuánto se cortó. Y el tablero dice lo contrario:
  `frontend/index.html:1087-1103` afirma que «el pipeline no deja marca en el record» (falso: deja
  `primary_cluster.d9_capped`, `process_modis.py:1182-1183`) y rotula todo 5,00 como «Valor CENSURADO,
  probablemente cirrus, probablemente artefacto».
- **CÓMO SE VE EN EL DASHBOARD**: una erupción de Chillán que dé 20 MW en MODIS en una noche fría se
  publica como 5,00 MW con la leyenda «probablemente artefacto». La curva MODIS queda plana en 5 mientras
  la erupción crece. Si además el píxel caliente queda `far` (C-07, A46), ni eso se ve.
- **CÓMO REPRODUCIRLO**: `VRP_PROFILE=mirova_equivalent python experiments/_s150_audit/C/c05_compuertas_magnitud.py`,
  bloque (3); record NdC 2026-10-02 07:35 MODIS_AQUA (`pc.vrp_mw` 5.0, 198 px, `d9_capped`).
- **CONFIANZA**: CONFIRMADO el mecanismo (leído y medido). SOSPECHA el daño sobre una alerta real: 0 casos
  observados con MIROVA > 5 MW, porque MIROVA todavía no publicó más de 6,17 MW en MODIS para Chillán.
- **GRAVEDAD 4**: tuerce la lectura de magnitud MODIS justo cuando sube, y la etiqueta empuja a
  descartarla.

## C-02. Un píxel VIIRS 375 que satura se borra: la magnitud cae cuando la erupción se intensifica

- **ARCHIVO:LÍNEA**: `pipeline/process_viirs.py:372-373` (`SAT_BIT_MASK`, `BT_LUT_MAX = {"I04": 361.77, ...}`),
  `:395-401` (bit de saturación → NaN; `bt >= 361,27 K` → NaN). Mismo criterio en MODIS
  `pipeline/process_modis.py:250-256` (`dn > 32767` → NaN, incluye 65533 «detector saturado») y en
  bandas M `pipeline/process_viirs_mod.py:183-194`, `:251-253`, `:284-286`.
- **QUÉ PASA**. Fenómeno: cuando un domo o una colada pone unos cientos de m² de material a 800-1100 K
  dentro de un píxel de 375 m, la banda I4 llega a su techo. Código: ese píxel se vuelve NaN y desaparece
  del cálculo, en lugar de quedar como cota inferior. Calculé el techo por píxel con la misma fórmula del
  pipeline (área nadir 140.625 m², k = 18,0): **9,6 MW por píxel** (fondo 250 a 270 K). Comprobación del
  cálculo: a 336,5 K da 4,31 MW contra 4,21 MW del record. **Chillán ya llegó a 4,21 MW en un solo píxel
  I4** (2026-10-01 06:18 VIIRS_NOAA20, 336,5 K) y MIROVA publicó 8,24 MW en V375 el 2026-10-05 (OCR):
  falta un factor ~2,3 por píxel para empezar a borrar el foco. Consecuencias en cadena (SOSPECHA, no
  observadas): (a) el píxel más caliente aporta 0 MW, así que la serie V375 baja cuando la erupción sube;
  (b) un NaN no cuenta para el camino NTI, lo que puede encender el tope de C-01 si era el único píxel
  con NTI > -0,8; (c) V750 (M13, techo 633,5 K) sigue viendo, así que los dos sensores divergirían.
- **Contra el paper**: Coppola et al. 2016a, SP 426, p. 3 (índice 2 del PDF), segundo párrafo de la
  columna izquierda, verificado **renderizando la página** (`sp426_saturados.png`): MIROVA elimina los
  DN > 32.768 «with the exception of the pixels with DN = 65 533, indicating saturated values». O sea,
  MIROVA conserva el píxel saturado de MODIS; nuestro `calibrate()` lo borra. Para VIIRS I4 no leí
  ningún texto de MIROVA: la paridad en V375 queda SIN VERIFICAR.
- **Intento de medir el efecto**: la fuente fuerte de febrero de 2025 a 15-19 km de Chillán (por la
  distancia y la fecha la llamo «incendio», sin haberlo verificado; V750 hasta
  67 MW por píxel, 365 K) era el caso natural, pero no sirve: en 50 de las 58 pasadas en que V750 vio más de 1 MW en el incendio, el record V375 no guarda ningún píxel del incendio (guarda
  sólo el píxel del Test 1 de la cumbre), porque con `final_hotspot_source == "test1"` se reconstruye
  `anomaly_pixels` sólo con los píxeles del Test 1 (`process_viirs.py:1978`). SIN DATO
  (`c06_incendio_feb2025.py`). En el corpus no hay ningún píxel alertado V375 sobre 355 K, pero ese cero
  no distingue «no hubo» de «se borró».
- **Gravedad baja en lo demás**: MODIS con banda 21 primaria satura cerca de 500 K, ~700 a 1.500 MW por
  píxel; M15 satura a 343 K, lo que exige 400 a 1.700 MW por píxel de 750 m. No pesan para Chillán hoy.
- **CÓMO SE VE EN EL DASHBOARD**: la magnitud V375 (núcleo F5') cae o se apaga mientras V750 sube, en la
  pasada más intensa. Un operador lo leería como pulso o enfriamiento.
- **CÓMO REPRODUCIRLO**: lectura de `process_viirs.py:395-401`; cálculo del techo en el informe de esta
  sesión (Planck con `C1 = 1.191042e8`, `C2 = 1.4387752e4`, λ = 3,74 µm).
- **CONFIANZA**: CONFIRMADO el mecanismo y el techo por píxel; SOSPECHA el efecto (no observado aún).
- **GRAVEDAD 4**: la señal más fuerte es la que se pierde, y está a un factor ~2 del régimen actual.

## C-03. El «modo de un solo píxel» parte la magnitud en 5 MW, justo en el rango de Chillán

- **ARCHIVO:LÍNEA**: `pipeline/single_pixel_mode.py` (condición `vrp_mw < threshold_mw` y
  `n_pixels <= max_pixels`, devuelve `max(per_pixel_vrp)`); llamada en `process_modis.py:1193-1198`
  y sus simétricos. Perfil: `SUB_MW_REGIME_THRESHOLD_MW = 5.0`, `SINGLE_PIXEL_MAX_CLUSTER_PIXELS = 3`.
- **SCRIPT:SALIDA**: `c05_compuertas_magnitud.py` bloque (1), llamando a la función real.
- **QUÉ PASA**. El modo se pensó para el régimen «sub-MW» (0,21 a 0,45 MW, docstring), pero el corte
  quedó en 5 MW. Con un cúmulo de 2 o 3 píxeles, si la suma no llega a 5 MW se publica el píxel más
  caliente; si pasa de 5, la suma. Medido con la función real: tres píxeles de 1,6 MW (suma 4,8) →
  **1,6**; tres de 1,7 (suma 5,1) → **5,1**. Un cambio de 6 % en la señal triplica o divide por tres el
  número publicado. Casos reales de Chillán en V750 (el tablero publica `pc.vrp_mw` en MODIS y V750):
  2026-10-01 05:24 NOAA21_750, píxeles 2,655 + 1,828 → publicado 2,655, MIROVA (OCR) 9,0;
  06:18 NOAA20_750, 2,491 + 0,432 → 2,491, MIROVA 7,06. En V375 el tablero muestra el núcleo F5', que
  suma, así que ahí el efecto se diluye.
- **Exposición**: el modo actúa en 212 de 245 pasadas V750 y 979 de 1.003 V375 pareadas a una alerta;
  en la ventana de Chillán, en 12 de 16 V750 y 2 de 10 MODIS.
- **CÓMO SE VE EN EL DASHBOARD**: en V750 y MODIS, una erupción que cruza 5 MW aparece como un salto de
  ×2 o ×3, y una que baja de 5 como una caída igual.
- **CÓMO REPRODUCIRLO**: `VRP_PROFILE=mirova_equivalent python experiments/_s150_audit/C/c05_compuertas_magnitud.py`.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD 4**: no oculta la detección, pero rompe la monotonía de la magnitud en el rango donde está
  hoy el volcán.

## C-04. La magnitud focal MODIS ahueca las anomalías extendidas: ayuda en reposo y resta en erupción

- **ARCHIVO:LÍNEA**: `pipeline/vrp_regimes.py:343-383` (`cluster_focal_vrp_mw`: suma sólo píxeles
  `dnti_ctx` más el pico); llamada en `process_modis.py:1165-1169`. Perfil:
  `ENABLE_FOCAL_CLUSTER_MAGNITUDE = True`, `FOCAL_CLUSTER_KEEP_PEAK = True`.
- **SCRIPT:SALIDA**: `c03_analisis.py` (C) y `c05_compuertas_magnitud.py` (2).
- **QUÉ PASA**. El filtro deja sólo los píxeles que destacan contra el promedio de sus 8 vecinos. En un
  foco extenso los píxeles interiores tienen vecinos calientes, así que no destacan y se caen de la suma.
  Medido en MODIS con MIROVA ≥ 2 MW (n = 14: 12 Láscar, 2 Chillán): mediana pc/MIROVA **0,573** contra
  **0,744** de la suma de los píxeles alertados dentro del inner; en el tramo 2-5 MW (n = 12) 0,573 contra
  0,986. En reposo (MIROVA < 1 MW) la suma del cráter da 5 a 8 veces MIROVA, que es por lo que se adoptó
  el filtro. Chillán: 2026-10-01 01:45 pc 4,17 (cráter 4,23, MIROVA 6,17); 08:35 pc 2,29 (cráter 3,28,
  MIROVA 5,18).
- **CÓMO SE VE EN EL DASHBOARD**: magnitudes MODIS de erupción en torno a la mitad de MIROVA.
- **CÓMO REPRODUCIRLO**: `python experiments/_s150_audit/C/c03_analisis.py`, tabla (C).
- **CONFIANZA**: CONFIRMADO el déficit medido; SOSPECHA la atribución al ahuecamiento (el JSON no guarda
  qué píxeles eran contextuales). n chico.
- **GRAVEDAD 3**: a 10 MW o más mueve la clase de MIROVA (Moderado a Bajo).

## C-05. El cúmulo primario es el más CERCANO al cráter, no el más energético

- **ARCHIVO:LÍNEA**: `pipeline/clustering.py`, `_vent_key` dentro de `cluster_hotspots`
  (`(0 si dentro del inner, distancia, -vrp)`).
- **SCRIPT:SALIDA**: `c07_pico_fuera_del_cumulo.py`.
- **QUÉ PASA**. Con varios focos dentro del inner (Chillán tiene varios cráteres) gana el más cercano al
  ancla aunque sea el menor, y la magnitud publicada es sólo la de ese fragmento. Prueba: como
  `pc.vrp_mw ≥` cualquiera de sus píxeles, si el píxel más energético del inner supera al pc, está fuera
  del pc. Control: 0 de 8.483 records de un solo cúmulo. Resultado: **2.435 de 8.354 records con 2 o más
  cúmulos (29 %)**; 13 de 177 pasadas con alerta de MIROVA ≥ 1 MW. Chillán 2026-09-29 06:36 VIIRS_SNPP
  (cenit 55,7°): dos píxeles del cráter a 0,2 km entre sí, 1,375 y 1,297 MW, quedaron en cúmulos
  distintos y se publicó el de 1,297; el V750 de la misma pasada publicó 0,329 contra 2,03 de MIROVA.
  Que dos píxeles vecinos en el terreno no sean vecinos en la matriz a 56° de cenit apunta al solapamiento
  de barridos (bow tie): SOSPECHA.
- **CÓMO SE VE EN EL DASHBOARD**: magnitud de un fragmento; en V375 lo corrige en parte el núcleo F5'
  (2,683 en ese caso), en V750 y MODIS no.
- **CÓMO REPRODUCIRLO**: `python experiments/_s150_audit/C/c07_pico_fuera_del_cumulo.py`.
- **CONFIANZA**: CONFIRMADO la regla y el conteo; SOSPECHA la causa geométrica.
- **GRAVEDAD 3**.

## C-06. Villarrica: un cúmulo de más de 12 píxeles se anula en `record.vrp_mw`, y eso apaga la detección «summit»

- **ARCHIVO:LÍNEA**: `pipeline/store.py:413-420` (`max_cluster_pixels`), `volcanoes.yaml:75`
  (`max_cluster_pixels: 12`, sólo Villarrica, leído por `scripts/run_pipeline.py:252`);
  `frontend/index.html:1484` y `frontend/mosaico.html:405` (`isSummitDetection` devuelve falso si
  `vrp_mw === 0`, hay `discarded_reason` y no hay Test 1).
- **QUÉ PASA**. El tope se calibró contra glaciares (Pichillancahue, 16 a 86 px tibios). Una colada en
  Villarrica también da más de 12 píxeles, y su record quedaría con `vrp_mw = 0` y
  `discarded_reason = cluster_too_large_for_volcano` aunque `pc.vrp_mw` siga con la magnitud. Hoy hay 504
  records así; 16 son MODIS `summit` sin Test 1, el mayor 2026-01-05 08:00 MODIS_AQUA, 16,4 MW, 23 px a
  1,1 km.
- **CÓMO SE VE EN EL DASHBOARD**: SOSPECHA, para el frente B: el gráfico (que lee pc) lo mostraría, pero
  los contadores y la tarjeta de «última detección del cráter» no.
- **CONFIANZA**: CONFIRMADO en el pipeline; SOSPECHA en el efecto en las vistas.
- **GRAVEDAD 3**.

## C-07. Contexto del defecto conocido `far` en MODIS: la constante implícita es «un píxel del cráter más energético que el valle más tibio»

- **SCRIPT**: consulta directa al record (salida en esta sesión).
- **QUÉ PASA**. Con el fondo tomado como mediana del anillo de 5 a 25 km (267 K el 2026-10-01 08:35),
  los píxeles de valle a 13-25 km, 7 a 12 K más tibios por altitud, reciben 1,2 a 2,1 MW cada uno, más
  que el píxel del cráter (1,64 MW a 0,88 km). La etiqueta pasa a `summit` sólo cuando un píxel del
  cráter supera al valle más tibio: a las 01:45 el cráter dio 4,17 MW y salió `summit`. No agrega un
  defecto nuevo (es A46/A81 con A69, ya en el plan); fija el umbral físico efectivo, del orden de 2 MW
  por píxel MODIS en estas noches.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: la del defecto conocido; no se cuenta aparte.

## C-08. Medición de contexto: subestimación sistemática de ~0,5 a 0,6 contra MIROVA, sin colapso hasta 10 MW

Mediana de la razón contra MIROVA por tramo de la alerta de MIROVA (`c03_salida.txt`, desde 2026-03-01;
«operador» = pc, salvo V375 donde es el núcleo F5'):

| familia | tramo MIROVA | n | pc | suma cráter | operador |
|---|---|---|---|---|---|
| MODIS | 2-5 MW | 12 | 0,573 | 0,986 | 0,573 |
| MODIS | 5-10 MW | 2 | 0,559 | 0,659 | 0,559 |
| V750 | 2-5 MW | 25 | 0,590 | 0,592 | 0,590 |
| V750 | 5-10 MW | 2 | 0,369 | 0,400 | 0,369 |
| V375 | 2-5 MW | 20 | 0,553 | 0,745 | 0,730 |
| V375 | 5-10 MW | 2 | 0,566 | 0,566 | 0,566 |

No hay un pareo con MIROVA sobre 10 MW: **ese régimen está SIN DATO**. Chillán sólo (MIROVA ≥ 2 MW):
MODIS 0,559 (n = 2), V750 0,319 (n = 4), V375 0,578 (n = 5). El déficit de fondo en V750 y V375 es el ya
conocido de A99 (conteo de píxeles y anillo tibio); no es nuevo de este frente.

---

## Lo que cambiaría el plan

1. C-01 y C-02 se encadenan: si I4 satura, se pierde el único píxel con NTI > -0,8 y el tope de 5 MW
   se enciende. El verificador debería mirarlos juntos.
2. El frente B debería revisar la leyenda «CENSURADO, probablemente artefacto» de `index.html:1087-1103`
   sobre valores de erupción y el `isSummitDetection` de C-06.
3. El frente D debería saber que cualquier reconstrucción desde `anomaly_pixels` es un piso: sólo se
   guardan 100 píxeles (`process_modis.py:1085`), en MODIS de Chillán hubo hasta 914, y en V375 con
   ancla Test 1 se guardan sólo los del Test 1 (`process_viirs.py:1978`).

## Pruebas de campo propuestas

1. **Tope D9 en vivo**: en cada pasada MODIS de Chillán con `pc.vrp_mw == 5.0`, comparar con la fila de
   MIROVA de la misma hora. Si MIROVA da más de 5, el tope recortó una erupción. Decide si C-01 sube a 5.
2. **Saturación I4**: en cada pasada V375 de Chillán con MIROVA V375 sobre 8 MW, mirar `t_max_k` (si
   queda bajo 361 K mientras V750 sube, sospechar píxel borrado) y la razón V375/V750 de la misma pasada.
3. **Frontera de 5 MW**: listar las pasadas V750 y MODIS de Chillán con `single_pixel_mode: true` y
   suma de píxeles del cúmulo entre 3 y 5 MW, y ver si la serie del tablero salta al cruzar 5.
4. **Caso conocido** 2026-10-01 08:35 MODIS_AQUA: el tablero muestra la pasada oculta (`far`); su pc es
   2,29 MW con predicado del tope activo (escena 5,0).

## Límites de esta auditoría

- `crater_sum` se reconstruye de `anomaly_pixels` (top 100) con `dist_km` medida desde el centro del
  volcán, no desde el ancla; en reposo incluye el campo difuso y por eso supera a MIROVA.
- No corrí el pipeline sobre gránulos: todo sale de los JSON y de leer el código.
- Ninguna afirmación sobre lo que hace MIROVA con I4 saturada: no lo leí.
- Las pasadas del 3 al 8 de octubre no están en el repo; las alertas de MIROVA del 5 de octubre (hasta
  8,24 MW en V375 y 7,86 en V750) no se pudieron parear.

## VERIFICADO LIMPIO

- **La desviación inflada por la erupción no sube los umbrales**: `pipeline/detection_context.py:525`
  y `:943`, conectiva `min(C1, μ + C2·σ)` con `ENABLE_TESTS_23_PROSE_BRANCH = False`; una σ grande sólo
  puede bajar el umbral hasta C1, nunca subirlo sobre él. El segundo pase saca los píxeles activos del
  promedio de vecinos y del cálculo de μ y σ (`:905-930`).
- **El fondo de Chillán no lo contamina la anomalía del cráter**: Chillán no tiene `local_kernel_bg`
  en `volcanoes.yaml` (leído con `yaml.safe_load`, valor `None`), así que usa el anillo de
  `BG_INNER_KM = 5` a `BG_OUTER_KM = 25`, y los píxeles del cráter en la erupción están a menos de 2 km.
- **Tope de cordura de 50.000 MW**: `pipeline/store.py:64` y `:135-161`; sólo anula si además
  `t_max > 500 K`, sobre eso sólo marca. No toca el régimen de Chillán.
- **Pisos de magnitud**: `MIN_VRP_MW_MODIS/VIIRS375/VIIRS750 = 0.0`; `MAX_SIGMA_COMPONENT_K = 999.0` (sin
  tope de σ); `ENABLE_FINAL_PIXEL_FILTER = False`; `PATH_D_REQUIRES_COVALIDATION = False` (perfil
  resuelto).
- **Filtro de distancia de `store.py`**: usa `radius_km` = 25 (`scripts/run_pipeline.py:250`), no corta
  dentro de 25 km.
- **El pc MODIS no sale del top 100**: `pc.vrp_mw` se calcula sobre las matrices completas
  (`process_modis.py:1106-1124`); el recorte a 100 sólo afecta a la lista guardada.
