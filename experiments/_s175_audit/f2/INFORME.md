# F2 S175: VIIRS 375 en producción contra MIROVA, por volcán y por cenit, más la sombra V375-E

## 1. Encabezado

- Hora del servidor al empezar: Sat, 07 Nov 2026 04:23:38 GMT (`gh api -i repos/MendozaVolcanic/VRP-chile`, cabecera Date).
  Hora al cerrar: en la sección 8.
- Commit medido: la base `752d348bc67190e53b610989877e2405d238a1bc` (NRT Copahue 2026-11-07 03:38 UTC). Línea base roja (1)
  sobre `d516b9d8c0fad5b0ca458b9fb57cdf5e6f75f956`. Lector de la sombra en el tag `s172-v375e-lector-resellado` (objeto de
  tag `12b49057f`, commit `fc3912cb2`), **fuera de main** (sólo en `origin/claude/s172-v375e-relector`).
- Árboles de medición: `git -c core.autocrlf=false archive` de cada commit en `C:\Users\nmend\vrp-temporales\s175_audit\f2\`
  (`arbol_752d348bc`, `arbol_d516b9d8c`, `arbol_tag_lector`). sha256 comprobados en la base: consolidado del snapshot
  `f833bfde...`, OCR `577a336e...` (los del preámbulo), `frontend/index.html` blob `8ac54a2a...` (sha256 `e3963f56...`).
- Modelo: Claude Opus 5.5 (`claude-opus-5-5`). Esfuerzo real: el sistema de esta sesión declara `reasoning_effort` **15**, no
  «alto»; lo informo tal cual.
- CARPETA: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\f2\`
- Cenit: campo `sensor_zenith_deg` de cada record (29.503 de 29.503 records V375 lo traen). Bins `z<30`, `z30-50`, `z50-60`,
  `z>=60` (los de `banco_paridad.zbin`).
- Vara: «publica» = `banco_paridad.correr_node` (l. 156) sobre `frontend/index.html` de la base; alerta, negativo limpio =
  `banco_paridad.etiquetar` (l. 317) tras `indexar_referencia(..., regla_minimas="SN")` (D-9); protegida = fila de alerta
  pareada a ±`TOL_S` (l. 78, 120 s) con VRP de 1 MW o más (`clase_mirova.alerta_protegida`, lectura A).
- Ventana: 2026-03-01 a 2026-11-07 (la tabla de MIROVA es sana desde marzo, A119). Frontera de K en la fecha de los datos:
  los 11.525 records V375 nocturnos de la ventana son K; hasta septiembre llevan `regimen.perfil = _s154_reproc_k_historico`
  (reproceso #883) y desde septiembre `mirova_equivalent` (NRT, sha `34cea39e4` y siguientes). Se informa por tramo
  (`reproc` y `nrt`) y por mes.
- Llamadas a la API de GitHub: 1 de 10.
- Lo que NO miré (mi silencio aquí no es «todo bien»): pasadas diurnas (el banco las descarta); MODIS y VIIRS 750; la
  magnitud contra MIROVA salvo la línea base de Chillán; el código del detector K de VIIRS 375 en `pipeline/`; la
  geolocalización; ninguna lámina como imagen (sólo rutas); la lectura retrospectiva de V375-E; la lectura sellada de la
  sombra (no se generó: la parada no se alcanzó, y no la habría abierto); los números del auto-audit semanal (#915, #936);
  el texto de `PREREGISTRO_E.md` §3.3 y §8.8 (leí las constantes del lector y el comentario del perfil, no el documento).

## 2. En una pantalla

1. En la ventana K (2026-03-01 a 2026-11-07, base), VIIRS 375 publica 166 de 171 pasadas protegidas (97,1 %) y las 111 de 111 noches protegidas; las 5 pasadas perdidas son sólo OCR, 4 de Suomi NPP, todas con nuestro único píxel a 8 a 22 km y nada dentro del inner (C-04 es una de ellas).
2. La pérdida se concentra en las pasadas oblicuas: 4 de 36 protegidas con cenit de 50° o más se pierden, contra 1 de 135 bajo 50°.
3. La sobre-publicación en negativos limpios es 3,9 % por pasada y 13,5 % por noche, pero Lastarria publica en 25,6 % de sus pasadas (54,9 % de sus noches) y Puyehue en 11,6 % (41,9 %); ninguna de alto VRP (máximo 0,378 MW).
4. El tablero marca «MIROVA confirmó» con ±60 min y sin D-9: de 2.225 publicaciones V375 marcadas, 647 no tienen alerta de MIROVA de su pasada (143 de ellas tienen una RUTINA de su pasada: MIROVA miró y no vio nada) y 113 sólo tienen alertas de 0,05 MW o menos.
5. Sombra V375-E: su lector no está en la base; da NO LEGIBLE sin datos (bien), pero su criterio (b) da CUMPLE sin negativos y su tablero sellado no es el de hoy; parada en la noche 30 (2026-12-02 si no falta ninguna).

## 3. Líneas base rojas

### LB1. El 201 de S160 (C1 de escena) se reproduce exacto

- Pregunta 1: si el C1 de escena tocara lo publicado, los píxeles del núcleo F5 fuera del inner aparecerían aquí. Pregunta 2:
  el control positivo (inner/4) tiene que subir, y `pub_v375` no puede ser 0.
- Sobre `d516b9d8c`, ventana 2026-03-01 a 2026-10-21: `{"pub_v375": 2452, "CONTROL_fuera_inner/4": 507, "fuera_inner": 4}`,
  idéntico a `experiments/_s160_audit/v2/v_201_efecto_v375_salida.txt`. Las 4: Lastarria 2026-05-12 05:36 NOAA20,
  2026-07-17 06:18 SNPP, 2026-07-29 05:18 NOAA21; Isluga 2026-06-14 05:18 NOAA20.
- Sobre la base, misma ventana: igual (2.452, 4, 507), aunque los records nocturnos de la ventana pasan de 27.190 a 27.195
  (el corpus creció hacia atrás, A90). Hasta 2026-11-07: 4 de 2.632, control 546.
- Salidas: `lb1_c1_escena_d516b9d8c_salida.txt`, `lb1_c1_escena_base_misma_ventana_salida.txt`,
  `lb1_c1_escena_base_hasta_base_salida.txt`. Script `lb1_c1_escena.py` (lógica copiada del de S160, sólo cambia la raíz).

### LB2. Chillán cae con el cenit: la estratificación no está ciega

- Pregunta 1: si el cenit no ordenara la magnitud, las medianas por bin serían iguales. Pregunta 2: n por bin; bin vacío
  = SIN DATO.
- El 2026-10-18, razón nuestro (display del tablero) sobre MIROVA: 0,72 a 22,3°, 0,46 a 48,6°, 0,35 a 67,6°, las tres de
  S154 al centésimo. La cuarta de S154 (05:42 SNPP, 0,64) hoy es `ALERTA_SIN_GEOMETRIA_OCR` en el snapshot (fila OCR
  «No descargada - la imagen de MIROVA ya era de otra pasada») y sale del estrato de alerta: diferencia explicada, no
  ceguera.
- Erupción 2026-10-18 a 2026-11-07: mediana 0,801 (n 7) bajo 30°, 0,563 (10) de 30 a 50°, 0,237 (3) de 50 a 60°, 0,339 (9)
  sobre 60°. Ventana completa: 0,724 (23), 0,556 (23), 0,552 (12), 0,321 (19).
- Salida `lb2_chillan_cenit_base_salida.txt`, script `lb2_chillan_cenit.py`.

### LB3. El lector de la sombra sobre una noche sintética sin datos da SIN DATO

- 11 JSON con `records: []` para K y para la sombra, `--hasta 2026-11-03`: sale 3, «LECTURA NO LEGIBLE», caen S2 a S7,
  «noches 0 de 30, alertas 0 de 40: NO ALCANZADA». K real y sombra vacía: también sale 3 (cae S7). No da CUMPLE ni VERDE.
- Salidas: `C:\Users\nmend\vrp-temporales\s175_audit\f2\lector_sintetico_vacio_stdout.txt` y
  `...\lector_sombra_vacia_stdout.txt` (copiadas también a CARPETA, ver sección 8).

## 4. Hallazgos

Instrumento principal: `f2_banco_v375.py` (salida `banco_base_0301_1107_salida.txt` y `.json`). Sus preguntas: P1, los
controles `todo_publica` y `nada_publica` sobre el mismo denominador dan recall 1,0 y 0,0 y tasa en negativos 1,0 y 0,0
(impresos en la salida); P2, cada denominador se imprime y un denominador 0 sale `None` (SIN DATO), nunca 0. Etiquetas V375
con SN en la ventana: 1.469 pos, 4.087 neg_limpio, 374 far_ref, 64 sin_geometria, 5.531 sin_info.

### F2-201. Cinco pasadas protegidas de VIIRS 375 que el tablero no publica

- TÍTULO: 5 de 171 pasadas protegidas (lectura A) quedan sin publicar; las 5 noches tienen otra pasada publicada.
- ARCHIVO:LÍNEA / SCRIPT:SALIDA: `f2_banco_v375.py` → `banco_base_0301_1107_salida.txt` (bloque «PROTEGIDAS NO
  PUBLICADAS»); `perdidas_protegidas.py` → `perdidas_protegidas_base_salida.txt`.
- QUÉ PASA: MIROVA leyó en su imagen de 1,29 a 2,51 MW, y nuestro record de esa pasada tiene un solo píxel, a 8,2 a 21,6 km
  del cráter, sin ningún píxel dentro del inner; el record queda `far` y el predicado no lo publica (`summit` 0). Las 5
  filas son sólo OCR (la tabla no lista la pasada) y ninguna es «de cráter» según `clase_mirova.protegida_de_crater`
  (V375-A): 4 son de Suomi NPP antes del hito del 2026-10-09 (la distancia puede ser de otra pasada) y Lastarria 2026-04-18
  es anterior al 2026-06-13 (OCR sin distancia medida).

  | volcán | pasada UTC | sat. | cenit | MIROVA (OCR) | nuestro | tramo | lámina de MIROVA (Mirova-v1) |
  |---|---|---|---|---|---|---|---|
  | Láscar | 2026-08-22 05:06 | SNPP | 59,3 | 1,65 MW a 1,22 km | 1 px, 0,511 MW a 8,23 km | reproc | `imagenes_satelitales/Lascar/2026-08-22/05-06-00_Lascar_VIIRS375_VRP.png` |
  | Lastarria | 2026-04-18 04:42 | NOAA20 | 67,0 | 1,29 MW, «dist≈2.48 km» | 1 px, 0,531 MW a 19,63 km | reproc | `imagenes_satelitales/Lastarria/2026-04-18/04-42-01_Lastarria_VIIRS375_VRP.png` |
  | Lastarria | 2026-05-02 05:06 | SNPP | 59,5 | 2,36 MW, «dist≈2.48 km» | 1 px, 1,107 MW a 19,55 km | reproc | `imagenes_satelitales/Lastarria/2026-05-02/05-06-00_Lastarria_VIIRS375_VRP.png` |
  | Tupungatito | 2026-09-28 05:18 | SNPP | 48,8 | 2,51 MW a 5,27 km | 1 px, 0,150 MW a 21,57 km | nrt | `imagenes_satelitales/Tupungatito/2026-09-28/05-18-00_Tupungatito_VIIRS375_VRP.png` |
  | Tupungatito | 2026-09-29 04:54 | SNPP | 62,4 | 1,86 MW a 5,68 km | 1 px, 1,112 MW a 9,40 km | nrt | `imagenes_satelitales/Tupungatito/2026-09-29/04-54-00_Tupungatito_VIIRS375_VRP.png` |

  El verificador agrega (A1): el píxel de Tupungatito 2026-09-29 está a 7,52 km de la coordenada de `volcanoes.yaml`
  (inner 7 km) y a 9,40 km según `primary_cluster.centroid_dist_km`: esa pérdida depende de medio kilómetro y del punto
  desde el que se mide (A3).

  mirova-tif-archive no tiene lámina VRP de VIIRS 375 de Láscar ni de Lastarria en las 6 h siguientes; de Tupungatito
  guardó PNG de las 06:47, 08:13 y 08:44 del 09-28 y de las 08:49 y 09:48 del 09-29 (posteriores, `png_index.csv`).
- CÓMO SE VE EN EL DASHBOARD: en esas 5 pasadas el operador ve un punto «lejano» gris y ninguna detección de cráter; en la
  noche ve igual una detección de cráter, de otra pasada (recall por noche protegida 111 de 111).
- CÓMO REPRODUCIRLO: `python f2_banco_v375.py C:\Users\nmend\vrp-temporales\s175_audit\f2\arbol_752d348bc 2026-03-01 2026-11-07 banco_base_0301_1107`
  y `python perdidas_protegidas.py <arbol> banco_base_0301_1107.json C:\Users\nmend\vrp-temporales\s175_audit\insumos\png_index.csv perdidas_protegidas_base_salida.txt`.
- CONFIANZA: CONFIRMADO (medido). Que la alerta de MIROVA estuviera en el cráter es SOSPECHA en las 5 (distancia OCR no
  confiable en esas fechas).
- GRAVEDAD: 3. Lectura A las cuenta como pérdida protegida y el criterio de victoria no acepta ninguna; por noche no se
  pierde nada, y 4 de 5 son de un satélite que dejó de servir el 2026-11-02.

### F2-202. Las pérdidas se concentran en pasadas oblicuas y en Suomi NPP; el agregado lo esconde

- TÍTULO: recall de protegidas 99,3 % bajo 50° de cenit y 88,9 % sobre 50°; el agregado dice 97,1 %.
- SCRIPT:SALIDA: `banco_base_0301_1107_salida.txt`, bloques «POR CENIT» y «POR PLATAFORMA».
- QUÉ PASA: mirado de lado, el píxel de VIIRS crece y el foco se diluye; ahí es donde nuestro único píxel cae lejos y MIROVA
  todavía ve 1 a 2,5 MW. Protegidas publicadas por cenit: 64 de 64 bajo 30°, 70 de 71 de 30 a 50°, 13 de 15 de 50 a 60°,
  19 de 21 sobre 60°. Todas las alertas (pos): 97,5 % (609), 95,5 % (471), 93,6 % (264), 88,8 % (125). Por plataforma,
  protegidas: SNPP 47 de 51, NOAA20 70 de 71, NOAA21 49 de 49.
- CÓMO SE VE EN EL DASHBOARD: invisible como tasa; en las pasadas oblicuas falta el punto de cráter.
- CÓMO REPRODUCIRLO: el mismo comando de F2-201.
- CONFIANZA: CONFIRMADO. n chico sobre 50° (36 protegidas): la diferencia es de 4 casos.
- GRAVEDAD: 3.

### F2-203. La sobre-publicación en negativos limpios vive en Lastarria y Puyehue, y por noche es tres veces la de la pasada

- TÍTULO: 3,9 % de pasadas limpias publicadas en el agregado; 25,6 % en Lastarria y 11,6 % en Puyehue; por noche 13,5 %,
  54,9 % y 41,9 %.
- SCRIPT:SALIDA: `banco_base_0301_1107_salida.txt` («POR VOLCAN», «VOLCAN x CENIT»); `d9_por_volcan.py` →
  `d9_por_volcan_base_salida.txt`.
- QUÉ PASA: en Lastarria hay fumarolas permanentes de centésimas de MW; MIROVA las lista con 0,05 MW o menos (D-9 las
  vuelve «no vio nada») o con 0, y nosotros publicamos. De los 49 negativos publicados de Lastarria, 25 eran alerta bajo la
  etiqueta original del scraper y 8 sin_info: dos tercios los crea la regla D-9. En Puyehue es otra cosa: 42 de 43 son
  pasadas que MIROVA dio en 0, con nuestro cúmulo de cumbre a 0,2 a 17,7 km del cráter (inner 20 km), mediana 0,082 MW y
  máximo 0,378 MW. Chaitén: 24 de 544 (4,4 %), 23 sin D-9. Por cenit, la tasa cae de 7,2 % bajo 30° a 1,0 % sobre 60°
  (Lastarria 43,6 % bajo 30°, n 39; Puyehue 23,5 %, n 81). Por tramo es pareja: reproceso 3,92 %, NRT 4,01 %. Ningún
  negativo limpio publicado llega a 1 MW (136 bajo 0,1 MW, 25 de 0,1 a 1 MW).
- CÓMO SE VE EN EL DASHBOARD: en Lastarria, en más de la mitad de las noches que MIROVA miró sin ver nada, el operador ve
  una detección de cráter de centésimas de MW; en Puyehue, en 4 de cada 10.
- CÓMO REPRODUCIRLO: el comando de F2-201 y `python d9_por_volcan.py <arbol> 2026-03-01 2026-11-07 d9_por_volcan_base_salida.txt`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 3 (sobre-publicación de baja magnitud; no mueve una decisión de alerta por sí sola, pero desgasta la confianza
  del operador en dos volcanes).

### F2-204. «MIROVA confirmó» en el tablero no es la vara del banco: ±60 min, cualquier distancia y sin D-9

- TÍTULO: de 2.225 publicaciones V375 que el tablero marca como confirmadas por MIROVA, 647 no tienen alerta de MIROVA de
  su propia pasada (143 tienen una RUTINA de esa pasada y 73 un FALSO_POSITIVO) y 113 sólo tienen alertas de 0,05 MW o menos.
- CORRECCIÓN DEL VERIFICADOR (contexto limpio, `verificador\INFORME_VERIFICADOR.md` A4): mi port lee
  `data/mirova/<volcán>.json`, que para este conteo sólo aporta alertas, así que el 647 es «sin alerta de su pasada», no «sin
  ninguna fila». Contra la referencia completa, 448 no tienen fila de su pasada en la tabla y 431 en ninguna de las dos
  fuentes; 143 tienen RUTINA del consolidado de su propia pasada, que es peor: MIROVA miró y no vio nada y el tablero dice
  «confirmó». Además, 53 de los 161 negativos limpios publicados salen «confirmados» (48 sólo por alertas mínimas).
- ARCHIVO:LÍNEA: `frontend/index.html` l. 1544 (`enrichWithMirovaConfirmation`), l. 1548 (filtra sólo NULO y RUTINA),
  l. 1559 (`const TOL_MS = 60 * 60000;`), l. 1008 (se llama al cargar cada volcán); el mismo criterio en `computeMetrics`
  (l. 1422, 1441, 1452) y en `corroboracionMirova` (l. 2182). Exención de artefactos: l. 1337 y 1356
  (`if (!r || r._mirova_confirmed || ...) return false;`). SCRIPT:SALIDA: `confirmado_navegador.py` →
  `confirmado_navegador_base_salida.txt`; `confirmado_tolerancia.py` → `confirmado_tolerancia_base_salida.txt`;
  `confirmado_publicados.py` → `confirmado_publicados_base_salida.txt`.
- QUÉ PASA: el tablero dice «MIROVA también vio esto» si hay cualquier alerta de MIROVA del mismo sensor en una hora a cada
  lado, aunque sea de otra pasada, de otro lugar o de 0,04 MW, que D-9 cuenta como «MIROVA no vio nada». El banco parea a
  120 s y aplica D-9. Medido sobre todos los records V375 (2026-03-01 a 2026-11-07): 3.554 confirmados, 1.857 sólo por
  otra pasada, 255 sólo por filas mínimas. Sobre los 2.632 publicados: 2.225 confirmados, 647 sin fila de su pasada, 113
  sólo por mínimas, 105 cuya fila propia es sólo mínima. La misma marca exime al record de los filtros de cirro y campo
  difuso; hoy eso no cambia ninguna publicación (0 records artefacto en la ventana: la medición no podía ver diferencia,
  se dice), así que esa parte es latente. Control de identidad del port de conteo contra la función real con node: 3.554
  y 3.554, PASA.
- CÓMO SE VE EN EL DASHBOARD: la columna MIROVA y el color de «confirmado» (l. 3119, 3142, 3934 a 3937) y el panel de
  recall y precisión contra MIROVA cuentan como coincidencia lo que el banco y D-9 cuentan como negativo; el operador lee
  más corroboración de la que hay.
- CÓMO REPRODUCIRLO: `python confirmado_navegador.py <arbol> 2026-03-01 2026-11-07 confirmado_navegador_base_salida.txt`,
  `python confirmado_tolerancia.py <arbol> 2026-03-01 2026-11-07 3554 confirmado_tolerancia_base_salida.txt`,
  `python confirmado_publicados.py <arbol> 2026-03-01 2026-11-07 confirmado_publicados_base_salida.txt`.
- CONFIANZA: CONFIRMADO (código leído y conteos medidos). El efecto numérico en el panel de recall y precisión: SIN MEDIR.
- GRAVEDAD: 3.

### F2-205. La regla sellada de la sombra V375-E da CUMPLE en (b) sin ningún negativo

- TÍTULO: `criterios_sombra` acepta «SIN SUSTRATO» en P2 y en el silencio, y S7 no cae con clases de negativo vacías.
- ARCHIVO:LÍNEA (fuera de main, tag `s172-v375e-lector-resellado`): `experiments/_s168/v375e_sombra/leer_sombra_v375e.py`
  l. 577 a 594, en particular l. 584 (`"b": CUMPLE if (p2k in ("GANA", "EMPATE", "SIN SUSTRATO") and silencio != "ENCIENDE DE MAS" ...`),
  l. 617 (sin negativos, `silencio` vale `"SIN SUSTRATO (faltan negativos de alguna clase)"`), l. 364 y 366 (S7 sólo mira
  clases con n mayor que 0). SCRIPT:SALIDA: `criterio_b_sin_sustrato.py` → `criterio_b_sin_sustrato_salida.txt`.
- QUÉ PASA: la mitad de la pregunta de la sombra es si la vía publica menos que K donde MIROVA no vio nada. Si en la
  ventana no hay negativos limpios (por ejemplo, porque la tabla de MIROVA no llegó, ver F2-207), la función sellada da
  (b) CUMPLE: llamada con P2 y silencio en SIN SUSTRATO devuelve `"b": "CUMPLE", "estado": "CUMPLE"`; el control con
  «ENCIENDE DE MAS» da NO CUMPLE (la función puede fallar). S7 con sólo una protegida con dato y negativos con n 0 da `ok=True`.
  Lo que hoy lo frena es S9 (la tabla tiene que llegar 2 días después del corte), que sólo mira la fecha de la última
  fila, no los huecos dentro de la ventana. La salida guarda `b_sin_evidencia` (l. 627) y el reporte agrega «CUMPLE POR FALTA DE EVIDENCIA» (l. 750), pero
  el estado de (b) y el estado final no cambian.
- CÓMO SE VE EN EL DASHBOARD: invisible; afecta la lectura que decide la adopción de la vía en VIIRS 375.
- CÓMO REPRODUCIRLO: `python criterio_b_sin_sustrato.py C:\Users\nmend\vrp-temporales\s175_audit\f2\arbol_tag_lector criterio_b_sin_sustrato_salida.txt`.
- CONFIANZA: CONFIRMADO el camino de código; que se alcance con datos reales es SOSPECHA (hoy la tabla trae cientos de
  negativos por semana). La docstring lista SIN SUSTRATO como aceptable, así que es deliberado en la regla; no leí §9.7.
- GRAVEDAD: 3.

### F2-206. El lector de la sombra mide con el tablero del 2026-11-02, no con el de la base

- TÍTULO: el lector sella `frontend/index.html` sha256 `260b4a...` del tag; el de la base exime a la vía del filtro de cirro
  (S173 S1) y el sellado no.
- ARCHIVO:LÍNEA: lector l. 71 (sello del `index.html`); base `frontend/index.html` l. 1337 y 1356. SCRIPT:SALIDA:
  `predicado_tag_vs_base.py` → `predicado_tag_vs_base_salida.txt`.
- QUÉ PASA: en una pasada oblicua de Chillán, la celda de la vía mezcla foco y nieve y su píxel más caliente puede quedar
  bajo 0 °C con calor real; el tablero de hoy lo publica, el sellado lo esconde si pasa de 10 MW. Control positivo (record de
  la vía de cumbre, 260 K, 20 MW): base publica, tag no. Sobre los 122 records V375 de la sombra y 127 de K del 2026-11-03 al
  2026-11-07: 0 diferencias. Si la vía se adopta, la lectura habrá medido un predicado distinto del que publicará.
- CÓMO SE VE EN EL DASHBOARD: invisible hoy; tras una adopción, pasadas de la vía frías y de más de 10 MW que la lectura
  contó como calladas aparecerían publicadas.
- CÓMO REPRODUCIRLO: `python predicado_tag_vs_base.py <arbol_base> <arbol_tag> 2026-11-03 2026-11-07 predicado_tag_vs_base_salida.txt`.
- CONFIANZA: CONFIRMADO el mecanismo; efecto en la lectura SOSPECHA (0 casos en 5 noches).
- GRAVEDAD: 3.

### F2-207. La tabla de MIROVA del snapshot que leen el banco y la sombra termina el 2026-11-02

- TÍTULO: `data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv` de la base no tiene filas V375 después del
  2026-11-02; la copia de la raíz (`latest_consolidado.csv`) llega al 2026-11-06.
- ARCHIVO:LÍNEA / SCRIPT:SALIDA: `git log 752d348bc -- data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv`
  (último cambio `79f410697`, 2026-11-02 19:29 UTC, «audit(auto): paridad semanal»); el OCR del snapshot sí se actualiza en
  cada sync (último `e2d73eb04`, 2026-11-06 17:57 UTC). Conteo por fecha con `awk` sobre los dos CSV de insumos. Corridas del
  lector: `lector_base_stdout.txt` (snapshot: 3 noches de 30, 9 alertas de 40) y `lector_base_tabla_fresca_stdout.txt`
  (raíz: 4 noches, 26 alertas).
- QUÉ PASA: sin la tabla no hay filas RUTINA y por lo tanto no hay negativos limpios: desde el 2026-11-03 el banco y la
  sombra sólo ven las alertas que trae el OCR. El snapshot del consolidado lo refresca sólo el auto-audit semanal; el sync de
  cada pocas horas refresca la raíz y el OCR. El contador de la parada que imprime el lector depende de qué CSV se le pase.
  Mis números de noviembre en el banco (25 negativos) son sólo del 01 y 02.
- CÓMO SE VE EN EL DASHBOARD: invisible (el tablero lee `data/mirova/<volcán>.json`).
- CÓMO REPRODUCIRLO: `awk -F, '$5=="VIIRS375"{print substr($2,1,10)}' C:\Users\nmend\vrp-temporales\s175_audit\insumos\snapshot_consolidado_base.csv | sort | uniq -c | tail`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2 (S9 frena una lectura que decide con la tabla atrasada; el riesgo es un contador provisional engañoso y una
  semana de negativos fuera de cualquier medición hecha con el snapshot).

### F2-208. Fecha de parada de la sombra V375-E (ítem con fecha)

- TÍTULO: la parada (30 noches y 40 alertas, lo que llegue último) cae en la noche 30 con datos; si no falta ninguna, el
  2026-12-02.
- ARCHIVO:LÍNEA: lector l. 90 (`PARADA_NOCHES, PARADA_ALERTAS = 30, 40`), l. 279 a 293 (`noche_parada`: cuenta una noche
  de calendario si alguna pasada no SNPP de cualquiera de los 11 volcanes tiene record de la vía y etiqueta; las alertas son
  pasadas pos). Base `pipeline/profiles/sombra_codigo_mirova.yaml` l. 7, TEXTO: «30 noches o 40 alertas que decidan, lo que
  llegue último». Workflow `sombra-codigo-mirova.yml` l. 25: `cron: "0 15 * * *"`.
- QUÉ PASA: con la tabla fresca, 4 noches (03 a 06 de noviembre, las cuatro con records de la vía en los 11 volcanes) y 26
  alertas: las alertas no frenan (unas 6 por noche), así que decide el conteo de noches: 2026-11-03 más 29 noches es el
  2026-12-02. Cada noche sin records de la vía o sin referencia la corre un día. La fecha sí se sigue de las noches
  acumuladas.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: ver `lector_base_tabla_fresca_stdout.txt`; comando en la sección 8.
- CONFIANZA: CONFIRMADO (contadores del lector); la fecha es proyección.
- GRAVEDAD: 1 (ítem con fecha).

### F2-209. El lector de la sombra no está en la base

- TÍTULO: `experiments/_s168/v375e_sombra/leer_sombra_v375e.py` (blob `e720dbc4...`) no existe en `752d348bc` ni en
  `origin/main`; vive en el tag y en `origin/claude/s172-v375e-relector` (fuera de main).
- SCRIPT:SALIDA: `git ls-tree -r 752d348bc | grep e720dbc4` (vacío); `git merge-base --is-ancestor fc3912cb2 752d348bc` (no).
  En la base sí están el perfil, el workflow y los datos de la sombra (11 JSON en `data/sombra_codigo_mirova/`).
- QUÉ PASA: «el lector de la base es el del tag» no se puede comprobar porque la base no tiene lector. Para leer hay que
  armar un árbol del tag con `experiments/**/*.py` (el lector importa `mirova_port`, `mirova_v750_r2` y otros de
  `experiments/_s158_audit_r2`, `_s159`, `_s162_v375`) y un repositorio git donde `origin/loop/activo` resuelva (lo usa para
  el registro de la ventana).
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: los dos comandos de arriba.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2.

### F2-210. Dos protegidas de marzo sin record nuestro

- TÍTULO: Láscar 2026-03-11 06:18 UTC (4,35 MW) e Isluga 2026-03-10 04:54 UTC (1,45 MW), filas sólo OCR, sin pasada nuestra a
  ±120 s.
- SCRIPT:SALIDA: `banco_base_0301_1107_salida.txt` («PROTEGIDAS SIN RECORD NUESTRO»).
- QUÉ PASA: esas noches tenemos NOAA20 y NOAA21 pero no la pasada de esa hora (por la hora, probablemente Suomi NPP; no lo
  verifiqué en NASA). Las dos filas OCR tienen `Distancia_km` 0,0 (antes del 2026-06-13 el OCR no medía distancia).
- CÓMO SE VE EN EL DASHBOARD: falta la pasada; la noche tiene otras.
- CÓMO REPRODUCIRLO: el comando de F2-201.
- CONFIANZA: CONFIRMADO la ausencia; la causa (gránulo faltante) SOSPECHA.
- GRAVEDAD: 2.

### F2-211. Las pasadas «sin geometría» de la erupción de Chillán quedan fuera del denominador protegido

- TÍTULO: 18 pasadas V375 con fila `ALERTA_SIN_GEOMETRIA_OCR` de 1 MW o más; 14 son de Chillán en erupción (hasta 31,74 MW) y
  no cuentan como protegidas bajo la lectura A; 2 no se publican: Villarrica 2026-10-29 05:36 SNPP (2,83 MW) y Copahue
  2026-10-16 06:18 SNPP (1,34 MW), con nuestro record `far`.
- ARCHIVO:LÍNEA: `scripts/clase_mirova.py` (docstring inicial: las filas sin geometría «NO son alerta protegida bajo A»).
  SCRIPT:SALIDA: `sin_geometria.py` → `sin_geometria_base_salida.txt`.
- QUÉ PASA: MIROVA midió calor en esa pasada pero la imagen de distancia era de otra; por decisión conservadora no entra al
  criterio. En la erupción de Chillán eso saca del denominador 14 pasadas de 1,3 a 31,7 MW (todas publicadas). Una de ellas,
  2026-10-25 05:12 SNPP a 54,7° de cenit, la mostramos con 0,469 MW contra 31,74 MW de MIROVA.
- CÓMO SE VE EN EL DASHBOARD: las 16 publicadas se ven; las 2 de Villarrica y Copahue, como punto lejano.
- CÓMO REPRODUCIRLO: `python sin_geometria.py <arbol> 2026-03-01 2026-11-07 sin_geometria_base_salida.txt`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2 (bajo la lectura B, que Nicolás no ha decidido, Villarrica y Copahue serían pérdidas protegidas).

### F2-212. Dos consumidores del etiquetador siguen con la etiqueta original y no con D-9

- TÍTULO: `banco_paridad.main` y `clasificacion_referencia.clasificar_pasadas` llaman `indexar_referencia` sin
  `regla_minimas`, que vale `"original"` por defecto.
- ARCHIVO:LÍNEA: `scripts/banco_paridad.py` l. 227 (default `regla_minimas="original"`, documentado como deliberado) y
  l. 526; `scripts/clasificacion_referencia.py` l. 149. El auto-audit (`scripts/auto_audit_weekly.py` l. 226 a 232) y la
  vigilancia de la sombra (`scripts/vigilancia_sombra.py` l. 447 a 450) sí aplican SN.
- QUÉ PASA: el mismo banco, con la regla original, da en V375 recall 93,1 % y 2,79 % en negativos; con SN, 95,4 % y 3,94 %
  (`banco_base_0301_1107_salida.txt`, «REGLA MINIMAS»). Quien corra el banco por su CLI lee la regla vieja.
  `data/clasificacion_referencia/` no lo consume ningún archivo de la base (búsqueda en `.github`, `frontend` y `scripts`) y
  su último cambio es del 2026-09-20.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `git grep -n "indexar_referencia(" 752d348bc -- scripts`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2.

### F2-213. C-04 actualizado: Tupungatito 2026-09-28 05:18 UTC

- TÍTULO: la distancia de MIROVA de esa pasada (5,27 km) es la misma que la de su pasada siguiente de las 05:36 (OCR 5,27 km,
  tabla 5,21 km, 0,09 MW); la tabla no lista las 05:18.
- SCRIPT:SALIDA: `perdidas_protegidas_base_salida.txt`; filas del snapshot (`grep -i tupungatito ... | grep 2026-09-2[89]`).
- QUÉ PASA: el VRP de 2,51 MW es de su propia pasada (el OCR lo lee de la imagen de esa pasada), pero la distancia probablemente
  es de la imagen de las 05:36 (Suomi NPP antes del arreglo Mirova-v1#20 del 2026-10-09; V375-A da «no de cráter» por
  `ocr_snpp_antes_del_hito`). Nuestro record: un píxel de 0,150 MW a 21,57 km. Lo mismo el 2026-09-29 04:54 (1,86 MW a
  5,68 km, nuestro píxel 1,112 MW a 9,40 km). C-04 sigue abierto: no se sabe si el calor de 2,5 MW estaba en el cráter.
  Para cerrarlo hay que mirar la lámina «Last Month» de Mirova-v1 (no la miré como imagen).
- CÓMO SE VE EN EL DASHBOARD: punto lejano gris.
- CÓMO REPRODUCIRLO: el de F2-201.
- CONFIANZA: CONFIRMADO lo medido; la atribución de la distancia, SOSPECHA.
- GRAVEDAD: 2.

### Por mes, con la calidad de la referencia (A119)

`banco_base_0301_1107_salida.txt`, bloque «POR MES» (pasadas V375, regla SN). Los hitos los imprime el propio cargador
(`calidad_referencia_mirova.avisar`, `banco_base_stderr.txt`): tabla con 1,6 a 1,8 gránulos VIIRS por noche antes del
2026-04-01; sin NOAA-21 en la tabla antes del 2026-04-09; OCR con geometría mal calibrada antes del 2026-06-11 y sin
distancia medida antes del 2026-06-13; OCR v30 desde el 2026-08-06; filas sólo OCR de Suomi NPP con distancia
posiblemente de otra pasada antes del 2026-10-09; sin filas sin geometría antes del 2026-10-10.

| mes | pos (recall) | protegidas publicadas | negativos limpios publicados |
|---|---|---|---|
| 2026-03 | 163 (0,976) | 37 de 37 | 12 de 341 (3,5 %) |
| 2026-04 | 195 (0,939) | 33 de 34 | 20 de 444 (4,5 %) |
| 2026-05 | 273 (0,952) | 17 de 18 | 19 de 369 (5,1 %) |
| 2026-06 | 215 (0,944) | 10 de 10 | 15 de 498 (3,0 %) |
| 2026-07 | 140 (0,986) | 0 de 0 (SIN DATO) | 14 de 525 (2,7 %) |
| 2026-08 | 126 (0,921) | 6 de 7 | 28 de 673 (4,2 %) |
| 2026-09 | 172 (0,948) | 8 de 10 | 27 de 655 (4,1 %) |
| 2026-10 | 168 (0,976) | 50 de 50 | 24 de 557 (4,3 %) |
| 2026-11 (01 a 07) | 17 (0,941) | 5 de 5 | 2 de 25 (tabla sólo hasta el 02, F2-207) |

Las 5 protegidas perdidas caen en abril, mayo, agosto y septiembre (2), todas antes del hito de Suomi NPP del 2026-10-09
o del de distancia del 2026-06-13: justo los meses en que la distancia de una fila sólo OCR no es confiable.

## 5. SEGUIMIENTOS (fuera de mi eje)

- S-1. La instantánea compartida `C:\Users\nmend\vrp-temporales\s175_audit\main\` está convertida a CRLF: `index.html` da
  sha256 `e75224f5...` contra `e3963f56...` del blob, y `scripts/banco_paridad.py` tiene fin de línea CRLF (`file`). Quien
  compare sha256 contra el preámbulo sobre esa copia ve una falsa discrepancia. Confianza CONFIRMADO. Yo medí sobre mis
  propios árboles con `core.autocrlf=false`.
- S-2. No hay records V375 de Suomi NPP en la base después del 2026-11-01 06 UTC (16 records el 2026-11-01), aunque el cese
  declarado es el 2026-11-02 13:00 UTC: falta la noche del 02. Es de F0 (C-06). Confianza CONFIRMADO el conteo, causa SIN
  MIRAR.
- S-3. Chillán 2026-10-25 05:12 SNPP (cenit 54,7°): mostramos 0,469 MW contra 31,74 MW de MIROVA (razón 0,015), muy por
  debajo de la curva de cenit de LB2. Es magnitud, no mi eje. `sin_geometria_base_salida.txt`. CONFIRMADO el número.

## 6. VERIFICADO LIMPIO

- El lector de la sombra sobre noche sintética vacía y con la sombra vacía da NO LEGIBLE (sale 3), nunca CUMPLE (LB3). Vara:
  la regla del encargo («SIN DATO»).
- Con los datos reales de la base, los controles S0 a S7 y S10 del lector pasan y no imprime lectura (sale 5, parada no
  alcanzada). S0 confirma que las dependencias del árbol que armé son las del sello.
- El tag `s172-v375e-lector-resellado` resuelve al objeto `12b49057f` y al commit `fc3912cb2` (local y en el remoto,
  `git ls-remote`): el `12b49057f` del encargo es el objeto de tag, no un commit distinto.
- La regla D-9 (`clase_mirova.aplicar_regla_minimas`, umbral 0,05 l. 106) la aplican el auto-audit y la vigilancia de la
  sombra; y bajo SN ninguna protegida se reescribe (el banco da las mismas 171 protegidas con SN y con original).
- Predicado del banco contra el del navegador con la marca de confirmación calculada como en el navegador: 0 diferencias de
  publicación en los tres sensores (`confirmado_navegador_base_salida.txt`); salvedad: 0 artefactos, la medición no podía
  ver diferencias.
- Ningún negativo limpio publicado de 1 MW o más en V375 (máximo 0,378 MW).
- Cobertura por plataforma pareja de febrero a octubre (390 a 504 records V375 por mes y satélite).

## 7. SIN DATO y FUERA DE ALCANCE

- SIN DATO: el efecto de F2-204 en el panel de recall y precisión del tablero (no corrí `computeMetrics`); si las 5
  protegidas perdidas y las 2 sin record eran calor de cráter (requiere ver láminas); la causa del gránulo faltante de F2-210;
  §9.7 y §3.3 de `PREREGISTRO_E.md` en texto.
- FUERA DE ALCANCE: MODIS, VIIRS 750, el detector K en `pipeline/`, la retrospectiva de V375-E, la lectura sellada.

## 8. Verificador, archivos y cierre

- Verificador con contexto limpio (subagente, esfuerzo pedido high, real SIN DATO), scripts propios en
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\f2\verificador\`
  e informe `INFORME_VERIFICADOR.md` ahí mismo. Seis afirmaciones (F2-201, 202, 203, 204, 205, 207 y 209): cinco
  CONFIRMADAS y F2-204 CONFIRMADA EN PARTE (corrección incorporada arriba). Ninguna refutada. Fisher para F2-202: p de 0,002
  a 0,013 con cortes de 45° a 58°, sobre sólo 5 eventos.
- Comando del lector de la sombra (F2-207, F2-208), desde `C:\Users\nmend\vrp-temporales\s175_audit\f2\` con
  `GIT_DIR` apuntando al `.git` común del repositorio (sólo lectura, para que `origin/loop/activo` resuelva):
  `python -I arbol_tag_lector/experiments/_s168/v375e_sombra/leer_sombra_v375e.py --data-k arbol_752d348bc/data/mirova_equivalent --data-sombra arbol_752d348bc/data/sombra_codigo_mirova --cons ../insumos/latest_consolidado_base.csv --ocr arbol_752d348bc/data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv --hasta 2026-11-07 --commit 752d348bc67190e53b610989877e2405d238a1bc --dir-salida salida_lector_base_tabla_fresca`.
  El árbol del tag necesita `experiments/**/*.py` además de `experiments/_s162_v375` y `_s168/v375e_sombra`.
- Todo script de CARPETA tiene su salida al lado (`*_salida.txt`, `*_stdout.txt`). `hallazgos.csv` lo escribe `hacer_csv.py`.
- Disco: los árboles ocupan unos 0,45 GB en `C:\Users\nmend\vrp-temporales\s175_audit\f2\` (tope 2 GB). C: con 11 GB libres
  y D: con 4,9 GB al empezar.
- Llamadas a la API de GitHub: 2 mías, 4 del verificador.
- Hora del servidor al cerrar: Sat, 07 Nov 2026 04:48:06 GMT.
