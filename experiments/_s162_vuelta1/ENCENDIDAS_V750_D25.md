# Las pasadas de VIIRS 750 que D25 publica y K no (V1 y V2): qué son

**Hora del servidor** (GitHub, cabecera `Date`): Sat, 24 Oct 2026 13:42:46 GMT.
**Commit medido**: los records de los brazos llevan `regimen.codigo_sha = 66961f65d` (2026-10-21, «vigilancia(auto): sombra de K», tag de los despachos); `origin/main` está en `e850152b5` y entre los dos sólo cambia `pipeline/fetch.py` (+93 líneas), así que las citas a `process_viirs_mod.py` y `detection_context.py` valen para los dos. Los flags se leyeron importando `pipeline.profile` desde el árbol de 66961f65 extraído a `_arbol_66961f65/`, no desde el worktree (que está en `loop/activo` y difiere de main en 11 archivos de `pipeline/`).
**Modelo y esfuerzo**: claude-fable-5-1; el esfuerzo es el que configuró la sesión que me lanzó, no lo veo desde adentro.
**Qué NO miré**: no corrí el pipeline ni el oráculo de MIROVA sobre ningún gránulo (no hay Earthdata para esta tarea y no era el encargo); no abrí TIF de MIROVA ni imágenes; no miré MODIS (los brazos lo llevan apagado); no medí el dNTI ni el dETI del píxel alertado, porque no están persistidos (sólo `nti_max` de la escena); no revisé el brazo S17 (17 a 19 de octubre) ni el gemelo G; no toqué nada fuera de CARPETA.

**Ruta de este informe**: `C:\Users\nmend\AppData\Local\Temp\claude\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile\a3efc9fd-8a35-470a-aad1-531abaec64d8\scratchpad\vuelta1\encendidas_v750\INFORME.md`

## En una pantalla

1. Las 127 pasadas de VIIRS 750 que D publica y K no (45 en V1, 82 en V2: 33 recuperadas, 37 encendidas, 57 «otras») son **un solo objeto**: un cúmulo de **un píxel**, pegado al cráter, que entra al detector **sólo por el segundo pase sin condicionar** (primer pase vacío en 126 de 127), que está **0 a 6,3 K más frío que la mediana del anillo regional** y **1,1 a 10 K más tibio que sus vecinos**; K le recorta la magnitud a 0,0 MW y el tablero lo esconde, D le da 0,17 a 0,60 MW y lo publica.
2. **Recuperadas y encendidas son indistinguibles** con todo lo persistido: 29 variables, el mejor AUC es 0,67 (magnitud de la VIIRS 375 del mismo barrido) con p 0,017, por encima del umbral de Bonferroni 0,0017; controles positivo (AUC 0,000) y negativo (0,548) en orden. A83 se sostiene acá.
3. Las encendidas **no son noches frías**: en 32 de 37 MIROVA alertó el volcán esa misma noche en VIIRS 375, en las otras 5 tiene un FALSO_POSITIVO de 375 m a 20 a 30 km, y la VIIRS 375 **del mismo barrido** publica en K en 37 de 37 a 0,30 km del píxel de 750 m (MIROVA la etiqueta `pos` en 27 de 37). Lectura física: fuente sub-píxel que 375 m resuelve y 750 m diluye (categoría b de A54), con la salvedad de que el mismo barrido no es independiente (A109).
4. En **noches de volcán D25 no estrena ninguna**: en las 127 pasadas otra pasada de la misma noche ya publica en K (la VIIRS 375 del mismo barrido en 126 de 127). El +6 neto de P2 en V1 son puntos de 750 m agregados a noches que el tablero ya muestra calientes.
5. Posición: el píxel está donde están los cúmulos con magnitud del mismo volcán (mediana 0,38 km) salvo PCC 2026-04-30 06:06, una recuperada a 17,6 km al N del vent, publicada `summit` por el inner de 20 km; y la magnitud de D en las recuperadas queda 1,25 a 1,43 veces la de MIROVA.

## Primero el fenómeno, después el código

**Lo que pasa en el volcán.** De noche, la cumbre de Isluga, Láscar, Tupungatito o Planchón Peteroa es nieve o roca a gran altura, y está más fría que el anillo de 5 a 25 km que la rodea, que es puna, valle o salar a menos altura y que guarda el calor del día. El cráter con fumarolas o un lago tibio ocupa una fracción chica de un píxel de 750 m: calienta ese píxel unos pocos kelvin sobre la nieve que tiene al lado, pero no alcanza a subirlo hasta la temperatura del anillo. Medido en los 127 records: el píxel del cúmulo está a 263,5 K (mediana), **entre 0 y 6,3 K por debajo de la mediana del anillo** (ninguno por encima: máximo exactamente 0,0) y **entre 1,1 y 10 K por encima de sus vecinos no alertados** (mediana 4,3 a 4,9 K, `t_vecinos_D_K` 258 a 261 K). El anillo está 5 a 7 K más tibio que la corona inmediata del cráter. A 375 m la misma fuente ocupa una fracción cuatro veces mayor del píxel y sí se ve: la I-band del mismo barrido publica en K en 126 de los 127 casos, a 0,30 km del píxel de 750 m.

**Lo que hace el código.** (a) El primer pase de los Tests 2 y 3 exige `bt > t_bg + 3 K` (`detection_context.py:546`, `NTI_BT_SANITY_K = 3.0`, D22): un píxel más frío que el anillo no pasa, y `diag_n_first_pass_pixels` es 0 en 126 de 127 (en Láscar 2026-05-28 05:36 el primer pase es un píxel a 20 km, no el del cráter). (b) El segundo pase corre **aunque el primero esté vacío**, porque `ENABLE_SECOND_PASS_CONDITIONED = False` en el perfil operacional y en los dos brazos (`detection_context.py:906` sólo sale temprano si `conditioned`), y no reaplica la compuerta de BT: el píxel pasa Test 2 y Test 3 contra sus 8 vecinos con `max(C1 = 0,003, mu + 5 sigma)` y entra con `diag_n_second_pass_recapture = 1` (`process_viirs_mod.py:911-968`). El propio docstring de la función lo advierte: sin detección previa es «una segunda detección MÁS permisiva que la primera». (c) La magnitud resta la radiancia de Planck de la **mediana del anillo** y recorta a cero (`process_viirs_mod.py:1041` y `:1056`, `np.maximum(L_hot - L_bg_rad, 0.0)`): como el píxel está por debajo del anillo, `pc.vrp_mw = 0,0`. (d) El tablero exige `primary_cluster.vrp_mw > 0` (`frontend/index.html:1595-1604`, `isValidDetection`): K no publica. (e) D25 (`ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750`, `process_viirs_mod.py:1047-1052`, `vrp_regimes.neighbor_mean_radiance_background`) cambia sólo el fondo del paso (c) por la media de la radiancia de los vecinos no alertados hasta 7x7: el exceso pasa a ser positivo y el mismo cúmulo, con el mismo píxel, se publica. PREREGISTRO §3 tiene razón en que D25 no toca la máscara; para el operador sí es un cambio de detección, porque la publicación cuelga de la magnitud.

**Qué hace MIROVA con el mismo píxel.** Su código de VIIRS 750 (`MIROVA_VIIRS750_hotspot_detection.m` l. 205-235) también corre el segundo pase sin condición y no tiene compuerta de BT; su fondo del VRP (`MIROVA_VIIRS750_VRP.m` l. 63-85) borra el alertado más un halo de 3 celdas e interpola desde afuera, sin recorte. O sea que si MIROVA alerta ese píxel, su magnitud sale positiva y del orden de la de D (en las 33 recuperadas MIROVA publicó 0,09 a 0,50 MW; D da 1,25 a 1,43 veces eso). Lo que separa recuperadas de encendidas es que **el detector de MIROVA marcó el píxel en unas y en otras no**, y con lo que persistimos no se distingue por qué (EN162-02, EN162-09).

## Hallazgos (lo peor primero)

### EN162-01. Las 127 pasadas son un solo mecanismo: píxel único de cumbre, segundo pase sin condicionar, más frío que el anillo y más tibio que sus vecinos
- ARCHIVO:LÍNEA: `pipeline/process_viirs_mod.py:911-968` (segundo pase), `:1041` y `:1056` (fondo del anillo y recorte), `:1047-1052` (D25); `pipeline/detection_context.py:546` (compuerta `bt > t_bg + 3 K` del primer pase), `:906` (el segundo pase sólo se salta si `conditioned`), `:943-967`; `frontend/index.html:1595-1604`. SCRIPT: `caracterizar.py` -> `resumen.txt`, `pasadas.csv`; `detalle.py` sección (d).
- QUÉ PASA: fenómeno y código en la sección anterior. Números: 127 de 127 con `primary_cluster.n_pixels = 1`, `single_pixel_mode`, `distance_class = summit` en K y en D, `final_hotspot_source = ctx_cluster`; `diag_n_first_pass_pixels = 0` en 126 (1 en Láscar 2026-05-28 05:36, y ese píxel está a 20 km); `diag_n_second_pass_recapture >= 1` en 127; `triggered_test1 = 0`, `d9_capped = 0`, `product_version = standard` en 127. BT del píxel del cúmulo menos mediana del anillo: mediana -1,86 K (recuperadas), -1,98 K (encendidas), -1,29 K («otras»), máximo 0,00, mínimo -6,28. BT del píxel menos BT equivalente del fondo de D25: mediana +4,46, +4,32 y +4,18 K; mínimo +1,09. Magnitud de D: mediana 0,309 MW en V1 (0,167 a 0,514) y 0,360 MW en V2 (0,200 a 0,603). Cenit mediano 17 a 24 grados (no es efecto de borde), hora 05:36 a 05:54 UTC.
- CÓMO SE VE EN EL DASHBOARD: bajo K no se ve nada de esto (0 MW no publica); bajo D aparecería un punto `summit` «Muy Bajo» de 0,17 a 0,60 MW en cada una de las 127 pasadas.
- CÓMO REPRODUCIRLO: `python caracterizar.py` en CARPETA (lee `scratchpad/d25/tmpV1/t_K_D.json`, `tmpV2/t_K_D.json` y los records de `d25/{V1,V2a,V2b}`); ejemplo mínimo Isluga VIIRS_NOAA20_750 2026-09-06 05:42 UTC: píxel 265,22 K, anillo 267,34 K, fondo D25 equivalente 261,5 K, `pc.vrp_mw` K 0,0 y D 0,263.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 4. Es la palanca que decide las 127 publicaciones; no tuerce una alerta sola, tuerce la regla.

### EN162-02. Recuperadas y encendidas son indistinguibles con lo persistido (A83 se sostiene)
- SCRIPT:SALIDA: `discriminar.py` -> `discriminar.txt`, `discriminar.json`.
- QUÉ PASA: 33 recuperadas (10 V1, 23 V2) contra 37 encendidas (16 V1, 21 V2), 29 variables persistidas (cenit, hora, magnitud de D, distancia al cráter, temperaturas del píxel, del anillo y de los vecinos, sigma del anillo, NTI máximo y su desviación, mu y sigma del dNTI y dETI, temperatura y distancia del máximo de la escena, tamaño del anillo, p95 del ROI, cenit solar, magnitud y distancia de la VIIRS 375 del mismo barrido, cuántas otras pasadas de la noche publican, radiancia de los vecinos). AUC entre 0,35 y 0,67; nulo por barajado (5000 permutaciones, semilla 162) con intervalo 0,36 a 0,64; p mínima 0,0168 (`v375_misma_pasada_pc_vrp_K`, AUC 0,672; intra-volcán 0,646) y 0,0264 (`hora_decimal_utc`, AUC 0,348), las dos sobre el umbral de Bonferroni 0,0017 y dentro de lo que 29 pruebas dan por azar (1,5 esperadas bajo 0,05; salieron 2). Las dos preguntas del instrumento: el control positivo `rutina_pasada` (1 en toda encendida por construcción de la etiqueta) da AUC 0,000 y p 0,0000; el control negativo (gaussiana con semilla) da 0,548, p 0,50. Estratos por volcán (Isluga 9 contra 14, Láscar 7 contra 5, PP 4 contra 4, Tupungatito 7 contra 12): ningún AUC intra-volcán ponderado pasa de 0,70.
- CÓMO SE VE EN EL DASHBOARD: no se ve; es lo que le falta al operador: nada en el record separa un punto que MIROVA también publicó de uno que no.
- CÓMO REPRODUCIRLO: `python discriminar.py` (tarda ~2 min por las permutaciones).
- CONFIANZA: CONFIRMADO para las 29 variables listadas; la ausencia de discriminante no se extiende a lo no persistido (dNTI y dETI del píxel, textura del 3x3, regrilla).
- GRAVEDAD: 4. Cierra el camino «publicar sólo las que MIROVA publicaría» por variable persistida.

### EN162-03. Las encendidas son calor real de la misma noche que MIROVA sí publica a 375 m y no a 750 m
- SCRIPT:SALIDA: `caracterizar.py` -> `pasadas.csv` (columnas `v375_misma_pasada_*`, `mirova_alertas_noche_cualquier_sensor`, `mirova_fp_noche`); `detalle.py` secciones (a), (b2), (b3).
- QUÉ PASA: la etiqueta «negativo limpio» es por sensor (`banco_paridad.etiquetar`: fila RUTINA de la tabla a ±2 min y noche sin alerta ni FP **de ese sensor**), no por volcán. Cruzada contra la referencia congelada completa (consolidado, OCR en V1, capa histórica y respaldo, unidos con la misma clave que `cargar_referencia_unificada`): MIROVA alertó el volcán **esa misma noche en VIIRS 375** en 13 de 16 encendidas de V1 y 19 de 21 de V2. Las 5 restantes (Láscar 2026-09-13 06:00 y 2026-09-24 05:54, Isluga 2026-09-23 05:24, Láscar 2026-05-22 05:48, Tupungatito 2026-04-07 05:42) tienen todas una fila FALSO_POSITIVO de VIIRS 375 de MIROVA esa noche a 19,9 a 29,8 km (calor fuera del límite), y nuestra VIIRS 375 del mismo barrido publica 0,02 a 0,18 MW a 0,20 a 0,66 km del cráter. En las 37 encendidas la I-band del mismo barrido y plataforma publica en K (37 de 37), su cúmulo está a 0,30 km (mediana) del píxel de 750 m (36 de 37 a 0,75 km o menos), y la propia MIROVA la etiqueta `pos` en 27 de 37 (`far_ref` en 4, `sin_info` en 6). Lectura: fuente sub-píxel que 375 m resuelve y 750 m no, categoría b de A54 (señal real que MIROVA no publica en M-band). Salvedad A109: la I-band viene del mismo barrido, así que un borde de nube tibio aparecería en las dos bandas; lo que la I-band sí aporta es otra resolución y otro detector sobre la misma atmósfera.
- CÓMO SE VE EN EL DASHBOARD: el operador ya ve el volcán caliente esa noche por la VIIRS 375; D le agrega un punto de 750 m en la misma noche y lugar.
- CÓMO REPRODUCIRLO: `python detalle.py`, sección (b2) para las 5 sin alerta de MIROVA; `pasadas.csv` filtrado por `clase = encendida`.
- CONFIANZA: CONFIRMADO (los conteos); la lectura «fumarola o lago, no roca tibia» es la interpretación más parsimoniosa pero no está probada con un dato independiente del barrido (ver SIN DATO).
- GRAVEDAD: 3.

### EN162-04. D25 en VIIRS 750 no estrena ninguna noche de volcán
- SCRIPT:SALIDA: `caracterizar.py` -> `pasadas.csv` (`otras_pasadas_noche_publican_K`, `n_otras_pub_K`); `resumen.txt` («otras pasadas de la noche publican en K»).
- QUÉ PASA: en las 127 pasadas (10 de 10, 16 de 16, 19 de 19, 23 de 23, 21 de 21, 38 de 38) alguna otra pasada de la misma noche y volcán ya publica en K; en 126 de 127 es la VIIRS 375 del mismo barrido. En la unidad en que el operador lo vive (A94) D25 en M-band suma cero noches; en pasadas suma 127. Coincide con lo que el catálogo D25 ya medía en S145 («en noches el premio es cero») y lo extiende a los negativos: tampoco enciende noches nuevas, enciende puntos de 750 m en noches ya encendidas.
- CÓMO SE VE EN EL DASHBOARD: ningún volcán cambia de apagado a encendido en una noche por D25 en M-band; cambia la densidad de puntos de 750 m.
- CÓMO REPRODUCIRLO: `pasadas.csv`, columna `n_otras_pub_K` (mínimo 1 en las 127 filas). Noche = fecha UTC de la pasada; todas caen entre 04:42 y 06:54 UTC.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 3. Baja el peso de la decisión: lo que P2 cuenta como +6 neto en V1 no mueve el veredicto nocturno de ningún volcán.

### EN162-05. Posición: el píxel está donde están los cúmulos con magnitud, salvo PCC 2026-04-30 06:06 a 17,6 km; Isluga tiene un rumbo fijo al SW del vent nominal
- SCRIPT:SALIDA: `discriminar.py` (sección Posición); `detalle.py` (b1) y (c); `volcanoes.yaml` del árbol 66961f65.
- QUÉ PASA: distancia de cada píxel de 0 MW al centro (mediana de lat y lon) de los cúmulos de V750 que K publica con magnitud en el mismo volcán y ventana: mediana 0,38 km en recuperadas y en encendidas; 27 de 29 y 30 de 35 a 0,75 km o menos (un píxel de M-band). Las 5 encendidas que quedan fuera (Tupungatito 2026-09-08 y 09-17, PP 2026-09-27, 10-05 y 10-16, todas V1) están a 0,27 a 0,60 km del cráter y a 0,21 a 0,43 km de su propia V375: lo que falla es el centro de referencia, que en Tupungatito V1 sale de 2 cúmulos y en PP V1 de 1. Distancia al cúmulo de VIIRS 375 del mismo barrido: mediana 0,30 km; 68 de 70 a 0,75 km o menos. Atípicos reales: **PCC 2026-04-30 06:06 (recuperada)**, píxel a 17,64 km al N (rumbo 12) del vent, a 17,6 km de su propia V375 (que está a 0,14 km del cráter), publicado `summit` porque el inner de PCC es 20 km, y con alerta de MIROVA de VIIRS 750 de 0,41 MW a ±2 min (Distancia_km de MIROVA no comprobable sin acimut, A93); **NdC 2026-10-01 04:42 (recuperada)**, píxel a 2,39 km con cenit 68 (el más oblicuo de las 127) y V375 a 1,98 km. Isluga: las 40 pasadas (todas las clases) caen entre 0,43 y 1,18 km del vent con rumbo medio 215 y concentración circular R 0,97: una fuente fija al SW del punto nominal; el `vent_lat/lon` de Isluga en `volcanoes.yaml` es la coordenada GVP redonda (-19,15, -68,83), así que el offset es del punto de referencia, no del píxel (SOSPECHA en cuanto a dónde está el cráter activo; el rumbo fijo es dato).
- CÓMO SE VE EN EL DASHBOARD: PCC 2026-04-30 06:06 se dibujaría rojo `summit` a 17,6 km del cráter (A61); el resto cae sobre el cráter o sobre el mismo punto que las noches con magnitud.
- CÓMO REPRODUCIRLO: `python detalle.py` (b1) y (c); `discriminar.json` clave `posicion`.
- CONFIANZA: CONFIRMADO en las distancias; SOSPECHA en la ubicación del cráter de Isluga.
- GRAVEDAD: 3 por el caso de PCC (una publicación `summit` que no es el cráter); 1 para el resto.

### EN162-06. En las recuperadas D queda 1,25 a 1,43 veces por encima de MIROVA
- SCRIPT:SALIDA: `discriminar.py` (Razón pc_vrp_D / VRP de MIROVA); `experiments/_s158_d17_diseno/osf_codigo_mirova/MIROVA_VIIRS750_VRP.m` l. 63-85.
- QUÉ PASA: razón D / MIROVA en la misma pasada: V1 n 10, mediana 1,25 (0,65 a 2,51); V2 n 23, mediana 1,43 (0,54 a 3,07); 29 de 33 entre 0,5 y 2. MIROVA publica 0,09 a 0,50 MW; D da 0,17 a 0,57 MW. Atribución SOSPECHA: MIROVA interpola el fondo desde fuera de un halo de 3 celdas (`fillmissing2`) y D25 promedia los vecinos inmediatos (hasta 7x7 sólo si los 8 están alertados), que en una cumbre nevada son lo más frío de la escena; un fondo más frío da más magnitud. No está medido porque no corrí ninguno de los dos sobre la misma matriz.
- CÓMO SE VE EN EL DASHBOARD: el punto de D sale 25 a 43 % más alto que el de MIROVA en esas pasadas.
- CÓMO REPRODUCIRLO: `python discriminar.py`; `pasadas.csv` columnas `pc_vrp_D` y `mirova_vrp_mw` con `clase = recuperada`.
- CONFIANZA: CONFIRMADO el número; SOSPECHA la causa.
- GRAVEDAD: 2.

### EN162-07. Las «otras» son pasadas que la tabla de MIROVA no listó, en noches que MIROVA sí alertó a 375 m
- SCRIPT:SALIDA: `discriminar.py` («'otra' por etiqueta»); `resumen.txt` bloques «otra».
- QUÉ PASA: 19 en V1 y 38 en V2 (una de V1, Tupungatito 2026-10-17 05:24, está en los días excluidos por D-29 y por eso el evaluador lista 44 y no 45). Todas `sin_info`: 39 de 57 sin fila de MIROVA en una noche sin alerta del sensor (26 de las 38 de V2 son Suomi NPP), 8 sin fila en noche con alerta del sensor en otra pasada, 9 con RUTINA en noche con alerta del sensor (que por regla no son negativo limpio). MIROVA alertó el volcán esa noche en VIIRS 375 en 55 de 57. En todo lo medible (temperaturas, posición, cenit, magnitud de D, VIIRS 375 del mismo barrido publicando en 56 de 57) son iguales a recuperadas y encendidas. No informan sobre el cráter; informan que la tabla no cubre la pasada (A119) y que el evaluador hace bien en dejarlas fuera del denominador.
- CÓMO SE VE EN EL DASHBOARD: igual que las encendidas.
- CÓMO REPRODUCIRLO: `pasadas.csv` con `clase = otra`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2.

### EN162-08. D25 no apaga nada ni mueve cúmulos en VIIRS 750; levanta todos los cúmulos de cumbre en 0 MW, que son el 29 a 35 % de los cúmulos de cumbre de K
- SCRIPT:SALIDA: `detalle.py` sección (d); `caracterizar.py` (control positivo de la selección).
- QUÉ PASA: a nivel record, sobre los records nocturnos de V750 de los 11 Tier A (2.296 en V1, 3.373 en V2, cenit solar > 90): cúmulos de cumbre con `pc.vrp_mw = 0` en K: 45 (V1) y 82 (V2); D les da magnitud a 45 de 45 y 82 de 82 (mediana 0,309 y 0,360 MW); cúmulos de cumbre con magnitud en K: 84 y 200 (D no apaga ninguno); `far` 34 y 47. Fracción de cumbre en cero: 45 de 129 (35 %) y 82 de 282 (29 %), consistente con el 30 de 97 (31 %) del hallazgo 203 de S160 sobre la ventana K. «K publica, D no» = 0 en las dos ventanas. Cúmulo (n_pixels y centroide) idéntico entre K y D en los 127 pares; gránulo idéntico (comprobado por aserción).
- CÓMO SE VE EN EL DASHBOARD: no hay pérdidas por D25 en M-band; sólo altas.
- CÓMO REPRODUCIRLO: `python detalle.py` (d).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2 (es lo que ya decía la nota del estrato 203; acá queda medido a nivel record y en las dos ventanas).

### EN162-09. El detector de MIROVA podría marcar estos mismos píxeles y en las encendidas no lo hizo; por qué, no está medido
- ARCHIVO:LÍNEA: `experiments/_s158_d17_diseno/osf_codigo_mirova/MIROVA_VIIRS750_hotspot_detection.m` l. 205-235 (segundo pase llamado sin condición) y l. 262-345 (contraste contra la media 3x3 que incluye al central, piso -0,1 sólo en NTI, mu y sigma sobre toda la escena, `polyfit` de grado 2 sin alertas).
- QUÉ PASA: ni el paper ni el código de MIROVA tienen compuerta de BT, y el segundo pase corre siempre, así que el mecanismo de EN162-01 existe también del lado de MIROVA; sin embargo en 37 encendidas MIROVA dejó RUTINA a ±2 min y en 33 recuperadas alertó, con records nuestros iguales. Candidatos no medidos: la media 3x3 con el central rebaja el contraste de un píxel aislado a 8/9; la regrilla UTM de 1 km (D17) diluye un píxel de 750 m; mu y sigma sobre 67x67 con N-1 y la regresión recalculada mueven el umbral `mu + 5 sigma`. El oráculo `experiments/_s158_oraculo_mirova/mirova_v750.py` podría correrse sobre estos gránulos para separar estas hipótesis.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: no reproducido; requiere los gránulos L1B.
- CONFIANZA: SOSPECHA.
- GRAVEDAD: 1.

## SEGUIMIENTOS (para quien orquesta; ninguno lo ejecuté)

1. Correr el oráculo de MIROVA V750 sobre 4 a 6 de estos gránulos (2 recuperadas, 2 encendidas, misma noche si se puede) para ver si su detector marca el píxel y con qué contraste (EN162-09). Es la única vía para separar «MIROVA no lo ve» de «MIROVA lo ve y su umbral lo deja fuera».
2. Decidir qué es el vent de Isluga: 40 de 40 píxeles de 0 MW caen 0,4 a 1,2 km al SW (rumbo 215, R 0,97) del punto GVP redondo que `volcanoes.yaml` usa como `vent_lat/lon`, y los cúmulos de V750 con magnitud que K publica caen en el mismo sitio (V1: 7 cúmulos, mediana 0,99 km, rumbo 215, R 0,99; V2: 22, mediana 0,91 km, rumbo 220, R 0,89; medido con `caracterizar.cargar_records` sobre los brazos). No cambia ninguna etiqueta hoy (inner 5 km), pero toda distancia al cráter de Isluga arrastra ese offset (A3).
3. PCC 2026-04-30 06:06: mirar el TIF de MIROVA de esa pasada (sin pull del archivo de 17 GB; por la API) para saber si el 0,41 MW de MIROVA está a 17,6 km al N como el nuestro o en el cráter como la V375 (A61, A93).
4. Si se quiere un discriminante, hay que persistir el dNTI y el dETI del píxel alertado y su contraste contra la media 3x3 con el central (lo que MIROVA mide), porque con lo persistido no hay nada (EN162-02).
5. La regla de la etiqueta: «negativo limpio» es por sensor; para una decisión sobre M-band conviene informar también cuántos negativos limpios de V750 tienen alerta de V375 la misma noche (acá 32 de 37), porque cambia la lectura de «MIROVA no vio nada».

## VERIFICADO LIMPIO (con la vara de cada ítem)

- **Selección de pasadas** (vara: reproducir los totales del evaluador): V2 82 = 23 recuperadas + 21 encendidas + 38 otras, igual a `v2.log`; V1 45 contra 44 de `v1.log`, y la de más es Tupungatito 2026-10-17 05:24, dentro de `dias_excluidos` de `v1.json` (D-29). `caracterizar.py` -> `caracterizar.txt`.
- **Flags de los brazos** (vara: leer `pipeline.profile` desde el árbol de 66961f65, no el YAML): control y D difieren sólo en `ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375/750` (False/True); en los dos y en `mirova_equivalent`: `ENABLE_SECOND_PASS_CONDITIONED = False`, `ENABLE_FIRST_PASS_TESTS_2_AND_3 = True`, `ENABLE_SECOND_PASS_ADJACENT = True`, `ENABLE_TESTS_23_PROSE_BRANCH = True`, `ENABLE_TEST1_PATH = False`, `ENABLE_FINAL_PIXEL_FILTER = False`, `PATH_D_REQUIRES_COVALIDATION = False`, `C1 = 0,003 / 0,01`, `C2 = 5 / 10`, `NTI_BT_SANITY_K = 3,0`, `VRP_BG_NEIGHBOR_MAX_HALF_PX = 3`. `diff` de los dos YAML: sólo los dos flags y el `data_subdir`.
- **Código medido = código citado** (vara: `git diff --stat 66961f65 origin/main -- pipeline/`): sólo `pipeline/fetch.py`.
- **Mismo gránulo en K y D** (vara: aserción en `caracterizar.py` sobre `granule`): 127 de 127.
- **Mismo cúmulo en K y D** (vara: `n_pixels` y centroide, `detalle.py` (d)): 0 distintos en 5.669 records nocturnos.
- **Constantes de Planck del script** (vara: `|Planck(t_bg) - diag_L_bg_w_m2_sr_um| / diag_L_bg` sobre los 127 records): máximo 4,8e-4 (el `t_bg_k` está redondeado a 2 decimales).
- **El recorte explica el cero** (vara: BT del píxel del cúmulo menos `t_bg_k`): máximo 0,00 en los 127; ninguno positivo. El píxel del cúmulo se identificó por coincidencia de posición con el centroide, no por el máximo de `anomaly_pixels` (en Láscar 2026-05-28 05:36 el máximo está a 20 km).
- **Instrumento de discriminación** (vara: controles): positivo AUC 0,000 p 0,0000; negativo 0,548 dentro del nulo (0,365 a 0,636).
- **Referencia de MIROVA** (vara: misma unión que el evaluador): consolidado, OCR (sólo V1), capa histórica y respaldo, clave `(volcán, bucket, fecha[:16], source)`, «VIIRS» = M-band; 0 nombres de volcán sin reconocer; las 33 recuperadas parean con una fila `ALERTA_TERMICA/CONS` de VIIRS 750 a ±2 min y las 37 encendidas con `RUTINA/CONS`.
- **Ninguna pasada es diurna ni Test 1 ni topada** (vara: `solar_zenith_deg` 145 a 160, `triggered_test1 = 0`, `d9_capped = 0`, `product_version = standard`): 127 de 127.
- **D25 no quita publicaciones en V750** (vara: «K publica, D no»): 0 en V1 y 0 en V2.
- **Disco**: C: 32,4 GB libres al empezar; no se bajó de 10 GB. No se tocó nada fuera de CARPETA; no hubo commit, push, despacho ni credenciales (`gh` sólo para la cabecera `Date` y lectura).

## SIN DATO

- dNTI y dETI del píxel alertado, y su contraste contra la media 3x3 con el central: no se persisten (`nti_max` es de toda la escena).
- MODIS de la misma noche: los brazos llevan MODIS apagado (`SENSOR_MODIS = False`), así que no hay corroboración de 1 km desde este material.
- Independencia de la corroboración por VIIRS 375: es el mismo barrido (A109); no hay otra pasada de otro satélite con separación de 45 a 120 min medida acá.
- Qué hay en el suelo bajo el píxel (fumarola, lago, roca sin nieve): no hay dato de cobertura ni imagen de alta resolución en este material; la lectura «categoría b» se apoya en la V375 del mismo barrido y en que MIROVA alertó el volcán esa noche, no en una observación independiente.
- Distancia de MIROVA en las recuperadas (mediana 1,5 km, máximo 7,83) contra la nuestra (0,42): sin acimut y cuantizada a celda (D15, A93); no sirve para decir si es el mismo objeto.
- Esfuerzo del modelo: no visible desde la sesión.

## Archivos en CARPETA

`C:\Users\nmend\AppData\Local\Temp\claude\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile\a3efc9fd-8a35-470a-aad1-531abaec64d8\scratchpad\vuelta1\encendidas_v750\`
- `INFORME.md` (este), `hallazgos.csv` (escrito con `csv`, `escribir_hallazgos.py`).
- `caracterizar.py` -> `pasadas.csv` (127 filas, 81 columnas), `resumen.txt`, `resumen.json`, `caracterizar.txt`.
- `discriminar.py` -> `discriminar.txt`, `discriminar.json` (AUC, nulo, posiciones).
- `detalle.py` -> `detalle.txt` (tabla por pasada de recuperadas y encendidas, atípicos, estabilidad por volcán, conteos a nivel record).
- `_arbol_66961f65/` (extracción de `pipeline/` y `volcanoes.yaml` del commit de los brazos, para leer los flags).
