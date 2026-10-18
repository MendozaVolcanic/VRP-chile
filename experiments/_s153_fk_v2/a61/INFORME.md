# A61 de las 62 pasadas movidas de P4 (cambio K contra C0)

Auditoría espacial pedida por `experiments/_s151_prereg_fk_11/REGLA_ADOPCION.md` §3 (P4 FALLA en V1 y V2).
Sólo lectura sobre el repo. Todo lo de aquí sale de los scripts de esta carpeta
(`C:\Users\nmend\AppData\Local\Temp\claude\a61_p4\`), corridos el 2026-10-18.

## 1. Qué se preguntó y con qué instrumentos

La pregunta: cuando K mueve el cúmulo publicado más de 0,5 km, ¿lo pone más cerca o más lejos del calor que vio
MIROVA, y en alguna alerta protegida lo pone sobre **otro objeto**?

Lista exacta: las 62 pasadas de `verif_fk_v2\a4_p4_mag.json` (8 de V1, 54 de V2), leídas con las mismas tablas
`t_C0_K.json` del verificador. Posiciones desde `primary_cluster.centroid_*` de cada brazo; distancia y rumbo desde
`vent_lat/vent_lon` de `volcanoes.yaml`.

Tres instrumentos, de más a menos confiable:

1. **Píxeles (todas las pasadas)** (`s5_pixeles.py`). De los records crudos de las uniones se toman los píxeles
   anómalos que guarda cada brazo (`anomaly_pixels` más `discarded_anomaly_pixels`, top 100 de la escena) y el
   tamaño del cúmulo. Si el centroide de K cae sobre un píxel que C0 también marcó, el objeto es el mismo y lo que
   cambió es cómo se agrega el cúmulo; si no, K publica en un lugar donde C0 no guardó nada. Límite: el record no
   guarda la lista de píxeles del cúmulo, así que «el píxel está en el cúmulo de C0» queda SIN VERIFICAR; sólo
   consta que C0 lo marcó anómalo.
2. **Radio (todas)** (`s4_analisis.py`). `Distancia_km` de MIROVA se mide desde `mirova_center` y viene cuantizada a
   la celda del sensor (verificado aquí: 2,4 = 0,375·√41, 1,68 = 0,75·√5, 1,41 = 1·√2). Se compara con la
   distancia de cada cúmulo al mismo punto, con tolerancia de media celda más 0,1 km. Es una **cota** (A93, A107):
   descarta que un cúmulo sea el objeto de MIROVA, no lo identifica. Sólo informa de verdad donde `mirova_center`
   está casi sobre el cráter (Lastarria 0,07 km, Isluga 0,37, Chillán, Llaima, Copahue); en Tupungatito (4,86 km),
   Cordón Caulle (7,6) y Planchón (2,0) es aritmética (S144 §2.2).
3. **Imagen de MIROVA (35 de 62 sin imagen)** (`s2_emparejar.py`, `s3_bajar.py`, `s4_analisis.py`, `s6_nulo.py`).
   Índice remoto de `mirova-tif-archive` leído por la API, 40 GeoTIFF bajados de a uno. Emparejados por **hora de
   adquisición** (`acquisition_utc`, ±15 min), no por el nombre (A106: en 2 casos el nombre dice 14:29 o 15:29 y la
   adquisición es de madrugada). Un md5 ya visto en una adquisición anterior se marca «reciclada». Todos son
   EPSG:4326 (~375, 750 y 1.000 m); el centro de cada imagen cae a 0,0 a 0,4 km de `mirova_center`. El campo es
   radiancia MIR (0,035 a 0,14 en Lastarria, con el cono frío). «Objeto de MIROVA» = celda de mayor anomalía
   (valor menos mediana del anillo de 2 a 5 celdas) sobre el anillo de radio `Distancia_km`. La imagen de la propia
   pasada sale del **mismo gránulo** que usó nuestro detector (A109): se dice en cada fila. La de otra pasada de la
   misma noche (45 a 120 min) es el control independiente.

**El instrumento 3 no pasa su nulo (A110).** Primero lo medí con radios falsos de ±1,5 km y el verdadero ganó en 20
de 41 imágenes, pero ese nulo estaba sesgado (un anillo mayor tiene más celdas y su máximo crece por construcción).
Con un nulo justo (percentil del máximo del anillo verdadero entre 500 máximos de subconjuntos al azar del mismo
número de celdas, mismo disco): **media 0,47, 7 de 41 sobre 0,9 cuando el azar da 4,1**; imagen propia 0,45 (2 de
13), otra pasada 0,44 (4 de 24). O sea: a estos niveles de señal (casi todas bajo 0,3 MW) el campo de MIROVA no
muestra sobre el anillo un calor que se distinga de la textura del terreno. **Los veredictos de imagen de las tablas
no identifican el objeto de MIROVA y no deciden nada**; quedan como dato. La única familia donde el anillo sí
destaca es Tupungatito con imagen propia (0,82, 0,90, 0,90), justo donde A109 infla.

Imágenes que faltaban: el archivo de TIF empieza en mayo de 2026 y está congelado desde el 2026-09-22, así que
marzo, abril y octubre no tienen ninguna. **Ninguna pasada protegida tiene imagen propia.**

## 2. Lo que pasa físicamente en las 62

**El mecanismo dominante no es que K encuentre otro foco: es que K publica un píxel y C0 publicaba un centroide.**
K deja el cúmulo de un solo píxel en 54 de 62 pasadas. En 40 de 62 el centroide de K cae sobre un píxel que C0
también marcó anómalo (38 a 0,00 km, exacto), y en 30 de esas 40 es además el píxel más caliente de C0. En 28 de
las 40 el cúmulo de C0 tenía de 2 a 24 píxeles: su centroide quedaba corrido hacia donde se juntaban los vecinos
tibios, y K lo colapsa al píxel pico. Ese corrimiento es lo que P4 mide como «movimiento». Es el mismo objeto
térmico, contado de otra manera.

En las otras **22** K publica en un lugar donde C0 no guardó ningún píxel (0,7 a 3,4 km del más cercano). Ahí sí
cambia el objeto entre brazos. Son todas VIIRS 375 y todas de señal débil (el mayor de los dos brazos publica 0,04 a 0,18 MW) salvo
Isluga 06-10 (1,08 MW): Lastarria 8, Isluga 6, Tupungatito 5, Chaitén, Láscar y Planchón 1 cada uno. Contra el radio de
MIROVA, en esas 22: **sólo K compatible 11, sólo C0 2, ninguno 9**. Cuando K cambia de objeto, cae en el radio de
MIROVA bastante más seguido que C0, y 20 de esas 22 se mueven hacia el cráter (Tupungatito 5 de 5, desde ~2,8 km N a
menos de 0,3 km; Isluga 5 de 6; Chaitén de 2,9 km NO a 0,27 km S, con MIROVA a 0,38).

En total: K queda más cerca del cráter en 34 de 62; radio compatible sólo con K 21, sólo con C0 9, con ambos 10, con
ninguno 22.

## 3. Resumen por volcán y sensor

| volcán | sensor | movidas | protegidas | mismo píxel caliente | K en otro lugar | K más cerca del cráter | radio: sólo K / sólo C0 / ambos / ninguno | imagen: K cerca / K lejos / igual / sin imagen |
|---|---|---|---|---|---|---|---|---|
| Chaiten | VIIRS375 | 1 | 0 | 0 | 1 | 1 | 1 / 0 / 0 / 0 | 1 / 0 / 0 / 0 |
| Isluga | VIIRS375 | 6 | 1 | 0 | 6 | 5 | 4 / 1 / 0 / 1 | 2 / 1 / 0 / 3 |
| Isluga | VIIRS750 | 6 | 0 | 6 | 0 | 6 | 4 / 0 / 2 / 0 | 5 / 0 / 1 / 0 |
| Lascar | MODIS | 6 | 5 | 6 | 0 | 1 | 0 / 2 / 4 / 0 | 0 / 1 / 0 / 5 |
| Lascar | VIIRS375 | 1 | 0 | 0 | 1 | 1 | 1 / 0 / 0 / 0 | 0 / 0 / 0 / 1 |
| Lascar | VIIRS750 | 8 | 4 | 8 | 0 | 4 | 0 / 4 / 0 / 4 | 1 / 0 / 0 / 7 |
| Lastarria | VIIRS375 | 21 | 0 | 13 | 8 | 7 | 6 / 1 / 1 / 13 | 4 / 2 / 2 / 13 |
| NevadosDeChillan | MODIS | 2 | 2 | 2 | 0 | 1 | 0 / 1 / 1 / 0 | 0 / 0 / 0 / 2 |
| NevadosDeChillan | VIIRS375 | 1 | 0 | 1 | 0 | 0 | 1 / 0 / 0 / 0 | 0 / 0 / 0 / 1 |
| PlanchonPeteroa | VIIRS375 | 1 | 0 | 0 | 1 | 1 | 0 / 0 / 0 / 1 | 1 / 0 / 0 / 0 |
| PuyehueCordonCaulle | VIIRS375 | 1 | 0 | 1 | 0 | 0 | 0 / 0 / 0 / 1 | 0 / 0 / 0 / 1 |
| PuyehueCordonCaulle | VIIRS750 | 2 | 0 | 2 | 0 | 2 | 1 / 0 / 1 / 0 | 0 / 1 / 0 / 1 |
| Tupungatito | VIIRS375 | 5 | 1 | 0 | 5 | 5 | 3 / 0 / 0 / 2 | 4 / 0 / 0 / 1 |
| Villarrica | MODIS | 1 | 1 | 1 | 0 | 0 | 0 / 0 / 1 / 0 | 1 / 0 / 0 / 0 |
| **total** | | 62 | 14 | 40 | 22 | 34 | 21 / 9 / 10 / 22 | 19 / 5 / 3 / 35 |

«Imagen» usa la imagen propia si la hay, si no la de otra pasada; **no valida** (nulo fallido, §1).

### Lastarria, VIIRS 375 (21 movidas, ninguna protegida)

En 13 el cúmulo de K está sobre un píxel que C0 ya había marcado: C0 guardaba de 2 a 7 píxeles en el flanco y
publicaba uno al N (a ~1,0-1,2 km); K publica otro del mismo conjunto, al NO (1,1-2,4 km). En 8 K publica donde C0
no tenía nada. El rumbo cambia de N a NO en 12 de 21. MIROVA da 2,4 km en 12 de las 21 (la celda (4,5) desde su
centro, que está sobre el cráter): radio compatible sólo con K en 6, sólo con C0 en 1, con ambos en 1 y con ninguno
en 13. O sea, cuando K sale hacia afuera (14 de 21) va hacia el radio que MIROVA publica, pero en 13 de 21 ninguno
de los dos llega a su celda. Las 8 con imagen no deciden (percentiles del nulo 0,00 a 0,82, ninguno sobre 0,9). Lo
que estos datos no pueden decir: si el objeto a ~2,4 km NO es fuente real (A54) o borde tibio de cota baja (A69); el
TIF no separa esas dos cosas (S144 §2.1).

### Láscar, MODIS (6 movidas, 5 protegidas)

Las 6 son «mismo objeto»: K publica como cúmulo de un solo píxel un píxel que C0 ya tenía (el más caliente de C0 en
4 de 6; en 05-03 y 05-13 el más caliente de C0 está a 1,07 y 1,09 km), y C0 publicaba el centroide de un cúmulo de 4 a 14 píxeles,
corrido 0,6 a 1,8 km. Radio: compatible con ambos en 4, sólo con C0 en 2 (04-05 y 04-30, las dos protegidas): el
píxel de K queda a 2,78 y 2,18 km de `mirova_center`, contra 1,41 y 1,0 de MIROVA. Eso **no** muestra que K esté
sobre otro objeto: el píxel lo marcan los dos brazos, y un centroide puede caer en el radio de MIROVA por promedio.
Además la posición MODIS arrastra un sesgo de geolocalización de 1 a 3 km hacia el nadir (memoria S151,
`_interp_geo`), que aquí no medí: el radio MODIS es una cota débil. Imagen: sólo 05-13 (no protegida, propia), con
nulo 0,04: inútil.

### Láscar, VIIRS 750 (8, 4 protegidas)

Las 8 son «mismo objeto» (C0 de 2 a 21 píxeles, K de 1). Radio: sólo C0 en 4, ninguno en 4. Mismo mecanismo que en
MODIS. La única con imagen (05-11, protegida) es **reciclada**: ese md5 ya existía en una adquisición anterior, no
es la imagen de esa pasada.

### Isluga VIIRS 750 (6), Cordón Caulle (3), Chillán (3), Villarrica (1)

Todas «mismo objeto». En Isluga 750 C0 llevaba 7 a 17 píxeles y su centroide quedaba 1,3 a 1,9 km al S; K publica
un píxel a 0,55-1,16 km, y el radio es compatible sólo con K en 4 de 6 y con ambos en 2.

## 4. Las 14 protegidas, una por una

| pasada | qué hace K | radio | imagen | lectura |
|---|---|---|---|---|
| Chillán MODIS 10-01 01:45 | C0 7 px, K 2 px; mismo píxel caliente | ambos | no hay (archivo congelado desde el 22-sep) | mismo objeto |
| Chillán MODIS 10-05 07:50 | C0 4 px, K 1; mismo píxel caliente | sólo C0 (K a 0,62 km de la celda, en el borde de la tolerancia) | no hay | mismo objeto |
| Villarrica MODIS 09-04 07:50 | C0 6 px, K 1; mismo píxel caliente | ambos | otra pasada −86 min, nulo 0,03 | mismo objeto |
| Láscar MODIS 03-11, 04-05, 04-20, 04-30, 05-03 | C0 4-14 px, K 1; K sobre un píxel de C0 | ambos 3, sólo C0 2 | no hay | mismo objeto |
| Láscar V750 03-21, 04-16, 04-30, 05-11 | C0 2-20 px, K 1; K sobre un píxel de C0 | sólo C0 2, ninguno 2 | sólo 05-11, reciclada | mismo objeto |
| Isluga V375 06-10 04:48 | **otro lugar**: C0 0,01 MW a 0,98 km N; K 1,08 MW a 3,25 km NE | **sólo K** (K a 3,62 km de `mirova_center`; MIROVA 3,75 en la tabla y 4,36 en el OCR) | otra pasada +102 min, nulo 0,08 | K se acerca al objeto de MIROVA (2,15 MW a 3,75 km) y C0 queda descartado por el radio. Dirección SIN VERIFICAR |
| Tupungatito V375 09-14 06:18 | **otro lugar**: C0 0,04 MW a 2,94 km O; K 0,008 MW a 0,17 km del cráter | **ninguno**: MIROVA a 2,97 km de su centro, que está a 4,86 del cráter, así que su objeto está a 1,9 km o más del cráter; quedan descartados los dos | sólo MODIS +77 min | ninguno de los dos es el objeto de MIROVA (2,22 MW). La protección descansa sólo en el OCR de Suomi NPP, cuya distancia puede ser de otra pasada (A119; `resultado_v1/CABECERAS_SNPP.md`). SIN VERIFICAR |

## 5. Veredicto para la regla

**No encontré ninguna movida que ponga el cúmulo publicado sobre otro objeto que el que vio MIROVA en una alerta
protegida.** En 12 de las 14 protegidas K publica un píxel que C0 ya tenía (el mismo objeto, colapsado de un
centroide al píxel pico). En Isluga 06-10 K cambia de objeto **hacia** el radio de MIROVA y con una magnitud del
mismo orden (1,08 contra 2,15 MW), mientras el cúmulo de C0 queda descartado por el radio. En Tupungatito 09-14
ninguno de los dos brazos está en el objeto de MIROVA, y esa protección es dudosa por la distancia del OCR.

Lo que esto **no** prueba:

- Que el objeto publicado por K **sea** el de MIROVA: SIN VERIFICAR en las 14. Ninguna protegida tiene imagen propia,
  y el instrumento de imagen falló su nulo en general. El radio sólo descarta.
- Que el píxel de K esté **dentro** del cúmulo de C0: el record no guarda los miembros del cúmulo; sólo consta que C0
  lo marcó anómalo.
- Que en MODIS el radio diga algo fino: hay un sesgo de geolocalización conocido de 1 a 3 km, no medido aquí.

La consecuencia para la regla: P4 mide sobre todo un **cambio de agregación**, no un cambio de objeto. Con K el
punto publicado pasa del centroide de un cúmulo de varios píxeles al píxel pico. Si eso se parece más a lo que
publica MIROVA (su `Distancia_km` cuantizada a una celda sugiere que informa una celda, no un centroide) queda por
medir: en las 40 de «mismo objeto» el radio favorece a K en 10 y a C0 en 7, sin un lado claro.

## 6. Tabla por pasada (las 62)

Rumbo desde el cráter; «km» es la distancia al cráter. Radio compatible = |distancia del cúmulo a `mirova_center` −
`Distancia_km`| ≤ media celda + 0,1 km. «pct» es el percentil del nulo justo de la imagen (0,5 = azar).

| # | volcán | sensor | fecha UTC | prot. A | C0: lat, lon | C0: km, rumbo | K: lat, lon | K: km, rumbo | MIROVA Distancia_km (fuente) | radio: compatible | píxeles: K respecto de C0 | imagen MIROVA (tipo, pct nulo) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Chaiten | VIIRS375 | 2026-05-09 05:42 | no | -42.8156, -72.6773 | 2.89, NO | -42.8368, -72.6517 | 0.27, S | 0.38 (CONS) | sólo K | otro lugar (a 3.1 km del píxel de C0 más cercano) | propia, mismo gránulo: K más cerca, pct 0.06; otra pasada +54 min: K más cerca, pct 0.99 |
| 2 | Isluga | VIIRS375 | 2026-03-10 05:12 | no | -19.1526, -68.8392 | 1.01, O | -19.1565, -68.8340 | 0.83, SO | 0.84 (CONS) | sólo C0 | otro lugar (a 0.7 km del píxel de C0 más cercano) | sin imagen |
| 3 | Isluga | VIIRS375 | 2026-03-11 04:54 | no | -19.1745, -68.8292 | 2.72, S | -19.1497, -68.8483 | 1.92, O | 1.91 (CONS) | sólo K | otro lugar (a 3.4 km del píxel de C0 más cercano) | sin imagen |
| 4 | Isluga | VIIRS375 | 2026-04-13 06:18 | no | -19.1314, -68.8467 | 2.71, NO | -19.1562, -68.8358 | 0.92, SO | 0.53 (CONS) | sólo K | otro lugar (a 3.0 km del píxel de C0 más cercano) | sin imagen |
| 5 | Isluga | VIIRS375 | 2026-05-18 06:12 | no | -19.1767, -68.8298 | 2.97, S | -19.1551, -68.8354 | 0.80, SO | 0.53 (CONS) | sólo K | otro lugar (a 2.5 km del píxel de C0 más cercano) | reciclada (md5 anterior): K más cerca, pct 0.88; otra pasada -54 min: K más cerca, pct 0.87 |
| 6 | Isluga | VIIRS375 | 2026-06-10 04:48 | sí | -19.1416, -68.8272 | 0.98, N | -19.1320, -68.8056 | 3.25, NE | 3.75 (CONS) | sólo K | otro lugar (a 1.7 km del píxel de C0 más cercano) | otra pasada +102 min: K más lejos, pct 0.08 |
| 7 | Isluga | VIIRS375 | 2026-09-21 05:06 | no | -19.1761, -68.8282 | 2.91, S | -19.1576, -68.8370 | 1.12, SO | 1.06 (CONS) | ninguno | otro lugar (a 2.3 km del píxel de C0 más cercano) | otra pasada +54 min: K más cerca, pct 0.60 |
| 8 | Isluga | VIIRS750 | 2026-05-11 05:54 | no | -19.1642, -68.8310 | 1.58, S | -19.1544, -68.8324 | 0.55, SO | 0.0 (CONS) | sólo K | mismo píxel caliente (C0 n=17, K n=1) | reciclada (md5 anterior): K más cerca, pct 0.12 |
| 9 | Isluga | VIIRS750 | 2026-05-15 05:24 | no | -19.1619, -68.8303 | 1.32, S | -19.1573, -68.8362 | 1.04, SO | 1.06 (CONS) | ambos | mismo píxel caliente (C0 n=17, K n=1) | propia, mismo gránulo: K más cerca, pct 0.00; otra pasada +54 min: K más cerca, pct 0.94 |
| 10 | Isluga | VIIRS750 | 2026-05-17 05:42 | no | -19.1627, -68.8349 | 1.50, S | -19.1573, -68.8324 | 0.85, S | 0.75 (CONS) | ambos | mismo píxel caliente (C0 n=16, K n=1) | propia, mismo gránulo: igual, pct 0.00; otra pasada +48 min: K más cerca, pct 0.33 |
| 11 | Isluga | VIIRS750 | 2026-05-27 05:54 | no | -19.1669, -68.8307 | 1.88, S | -19.1581, -68.8332 | 0.96, S | 0.75 (CONS) | sólo K | mismo píxel caliente (C0 n=13, K n=1) | otra pasada +48 min: K más cerca, pct 0.96 |
| 12 | Isluga | VIIRS750 | 2026-06-05 05:30 | no | -19.1663, -68.8282 | 1.83, S | -19.1578, -68.8373 | 1.16, SO | 1.06 (CONS) | sólo K | mismo píxel caliente (C0 n=11, K n=1) | otra pasada +54 min: K más cerca, pct 0.23 |
| 13 | Isluga | VIIRS750 | 2026-06-06 05:12 | no | -19.1643, -68.8300 | 1.59, S | -19.1577, -68.8335 | 0.93, SO | 0.75 (CONS) | sólo K | mismo píxel caliente (C0 n=7, K n=1) | propia, mismo gránulo: K más cerca, pct 0.00; otra pasada +54 min: K más cerca, pct 0.88 |
| 14 | Lascar | MODIS | 2026-03-11 01:35 | sí | -23.3742, -67.7398 | 1.51, SO | -23.3777, -67.7317 | 1.64, S | 1.0 (CONS) | ambos | mismo píxel caliente (C0 n=4, K n=1) | sin imagen |
| 15 | Lascar | MODIS | 2026-04-05 01:35 | sí | -23.3620, -67.7441 | 1.29, O | -23.3468, -67.7397 | 1.99, NO | 1.41 (CONS) | sólo C0 | mismo píxel caliente (C0 n=10, K n=1) | sin imagen |
| 16 | Lascar | MODIS | 2026-04-20 01:30 | sí | -23.3634, -67.7384 | 0.72, O | -23.3654, -67.7333 | 0.34, SO | 1.0 (CONS) | ambos | mismo píxel caliente (C0 n=14, K n=1) | sin imagen |
| 17 | Lascar | MODIS | 2026-04-30 01:30 | sí | -23.3618, -67.7397 | 0.86, O | -23.3510, -67.7341 | 1.35, N | 1.0 (CONS) | sólo C0 | mismo píxel caliente (C0 n=12, K n=1) | sin imagen |
| 18 | Lascar | MODIS | 2026-05-03 07:45 | sí | -23.3537, -67.7313 | 1.03, N | -23.3546, -67.7254 | 1.11, NE | 1.41 (CONS) | ambos | mismo píxel caliente (C0 n=7, K n=1) | sin imagen |
| 19 | Lascar | MODIS | 2026-05-13 01:45 | no | -23.3576, -67.7407 | 1.12, NO | -23.3688, -67.7432 | 1.36, SO | 1.41 (CONS) | ambos | mismo píxel caliente (C0 n=13, K n=1) | propia, mismo gránulo: K más lejos, pct 0.04 |
| 20 | Lascar | VIIRS375 | 2026-03-06 06:30 | no | -23.3715, -67.7572 | 2.80, O | -23.3617, -67.7330 | 0.21, NO | 1.13 (CONS) | sólo K | otro lugar (a 2.7 km del píxel de C0 más cercano) | sin imagen |
| 21 | Lascar | VIIRS750 | 2026-03-16 05:00 | no | -23.3523, -67.7421 | 1.61, NO | -23.3636, -67.7319 | 0.09, SO | 1.5 (CONS) | ninguno | mismo píxel caliente (C0 n=7, K n=1) | sin imagen |
| 22 | Lascar | VIIRS750 | 2026-03-16 06:24 | no | -23.3629, -67.7436 | 1.24, O | -23.3622, -67.7341 | 0.28, O | 1.5 (CONS) | sólo C0 | mismo píxel caliente (C0 n=21, K n=1) | sin imagen |
| 23 | Lascar | VIIRS750 | 2026-03-21 05:06 | sí | -23.3647, -67.7305 | 0.22, SE | -23.3636, -67.7357 | 0.45, O | 2.25 (CONS) | ninguno | mismo píxel caliente (C0 n=2, K n=1) | sin imagen |
| 24 | Lascar | VIIRS750 | 2026-03-27 04:54 | no | -23.3605, -67.7383 | 0.75, O | -23.3624, -67.7299 | 0.16, E | 1.5 (CONS) | sólo C0 | mismo píxel caliente (C0 n=13, K n=1) | sin imagen |
| 25 | Lascar | VIIRS750 | 2026-04-16 06:12 | sí | -23.3627, -67.7316 | 0.03, NO | -23.3621, -67.7368 | 0.56, O | 1.68 (CONS) | ninguno | mismo píxel caliente (C0 n=2, K n=1) | sin imagen |
| 26 | Lascar | VIIRS750 | 2026-04-24 05:18 | no | -23.3626, -67.7293 | 0.22, E | -23.3616, -67.7347 | 0.37, NO | 1.68 (CONS) | ninguno | mismo píxel caliente (C0 n=2, K n=1) | sin imagen |
| 27 | Lascar | VIIRS750 | 2026-04-30 06:00 | sí | -23.3597, -67.7328 | 0.39, N | -23.3603, -67.7279 | 0.47, NE | 1.68 (CONS) | sólo C0 | mismo píxel caliente (C0 n=2, K n=1) | sin imagen |
| 28 | Lascar | VIIRS750 | 2026-05-11 05:54 | sí | -23.3616, -67.7414 | 1.03, O | -23.3613, -67.7330 | 0.24, NO | 1.68 (CONS) | sólo C0 | mismo píxel caliente (C0 n=20, K n=1) | reciclada (md5 anterior): K más cerca, pct 0.89 |
| 29 | Lastarria | VIIRS375 | 2026-03-25 05:36 | no | -25.1577, -68.5106 | 1.21, N | -25.1538, -68.5230 | 2.25, NO | 2.4 (CONS) | sólo K | mismo píxel caliente (C0 n=2, K n=2) | sin imagen |
| 30 | Lastarria | VIIRS375 | 2026-03-28 06:18 | no | -25.1580, -68.5086 | 1.12, N | -25.1601, -68.5143 | 1.15, NO | 2.4 (CONS) | ninguno | mismo píxel caliente (C0 n=1, K n=1) | sin imagen |
| 31 | Lastarria | VIIRS375 | 2026-03-30 05:42 | no | -25.1587, -68.5108 | 1.10, N | -25.1786, -68.5245 | 2.12, SO | 2.7 (CONS) | ninguno | mismo píxel caliente (C0 n=2, K n=1) | sin imagen |
| 32 | Lastarria | VIIRS375 | 2026-04-04 05:48 | no | -25.1524, -68.5235 | 2.40, NO | -25.1579, -68.5092 | 1.14, N | 2.7 (CONS) | ninguno | otro lugar (a 1.6 km del píxel de C0 más cercano) | sin imagen |
| 33 | Lastarria | VIIRS375 | 2026-04-12 05:48 | no | -25.1584, -68.5147 | 1.32, NO | -25.1595, -68.5071 | 0.94, N | 2.4 (CONS) | ninguno | otro lugar (a 0.8 km del píxel de C0 más cercano) | sin imagen |
| 34 | Lastarria | VIIRS375 | 2026-04-17 05:54 | no | -25.1586, -68.5152 | 1.33, NO | -25.1598, -68.5070 | 0.92, N | 2.4 (CONS) | ninguno | otro lugar (a 0.8 km del píxel de C0 más cercano) | sin imagen |
| 35 | Lastarria | VIIRS375 | 2026-04-17 06:24 | no | -25.1589, -68.5079 | 1.02, N | -25.1601, -68.5151 | 1.20, NO | 2.4 (CONS) | ninguno | mismo píxel caliente (C0 n=1, K n=1) | sin imagen |
| 36 | Lastarria | VIIRS375 | 2026-04-18 06:24 | no | -25.1593, -68.5078 | 0.97, N | -25.1587, -68.5147 | 1.29, NO | 1.55 (CONS) | ninguno | mismo píxel caliente (C0 n=1, K n=1) | sin imagen |
| 37 | Lastarria | VIIRS375 | 2026-04-29 06:18 | no | -25.1590, -68.5066 | 1.00, N | -25.1584, -68.5125 | 1.20, NO | 1.55 (CONS) | ninguno | mismo píxel caliente (C0 n=1, K n=1) | sin imagen |
| 38 | Lastarria | VIIRS375 | 2026-04-30 06:00 | no | -25.1590, -68.5063 | 1.00, N | -25.1529, -68.5235 | 2.36, NO | 2.4 (CONS) | sólo K | mismo píxel caliente (C0 n=1, K n=1) | sin imagen |
| 39 | Lastarria | VIIRS375 | 2026-05-04 05:36 | no | -25.1587, -68.5088 | 1.05, N | -25.1531, -68.5212 | 2.19, NO | 2.19 (CONS) | sólo K | mismo píxel caliente (C0 n=1, K n=1) | sin imagen |
| 40 | Lastarria | VIIRS375 | 2026-05-09 05:42 | no | -25.1526, -68.5244 | 2.45, NO | -25.1611, -68.5141 | 1.05, NO | 2.4 (CONS) | sólo C0 | otro lugar (a 1.4 km del píxel de C0 más cercano) | propia, mismo gránulo: K más lejos, pct 0.66; otra pasada +48 min: K más lejos, pct 0.47 |
| 41 | Lastarria | VIIRS375 | 2026-05-22 06:36 | no | -25.1531, -68.5227 | 2.29, NO | -25.1605, -68.5130 | 1.03, NO | 1.19 (CONS) | sólo K | otro lugar (a 1.3 km del píxel de C0 más cercano) | otra pasada -48 min: igual, pct 0.00 |
| 42 | Lastarria | VIIRS375 | 2026-05-23 05:30 | no | -25.1596, -68.5063 | 0.94, N | -25.1555, -68.5186 | 1.81, NO | 2.19 (CONS) | ninguno | otro lugar (a 0.4 km del píxel de C0 más cercano) | propia, mismo gránulo: K más cerca, pct 0.82; otra pasada +48 min: K más cerca, pct 0.29 |
| 43 | Lastarria | VIIRS375 | 2026-05-25 06:30 | no | -25.1613, -68.5153 | 1.12, NO | -25.1558, -68.5136 | 1.51, NO | 2.4 (CONS) | ninguno | mismo píxel caliente (C0 n=1, K n=1) | propia, mismo gránulo: igual, pct 0.72; otra pasada -48 min: K más cerca, pct 0.00 |
| 44 | Lastarria | VIIRS375 | 2026-05-28 05:36 | no | -25.1578, -68.5071 | 1.13, N | -25.1598, -68.5160 | 1.28, NO | 1.35 (CONS) | ambos | mismo píxel caliente (C0 n=1, K n=1) | propia, mismo gránulo: K más cerca, pct 0.31; otra pasada +48 min: igual, pct 0.69 |
| 45 | Lastarria | VIIRS375 | 2026-06-05 05:30 | no | -25.1539, -68.5214 | 2.14, NO | -25.1592, -68.5111 | 1.06, NO | 2.4 (CONS) | ninguno | otro lugar (a 1.2 km del píxel de C0 más cercano) | otra pasada +54 min: K más lejos, pct 0.32 |
| 46 | Lastarria | VIIRS375 | 2026-06-08 06:18 | no | -25.1607, -68.5084 | 0.83, N | -25.1601, -68.5139 | 1.11, NO | 2.4 (CONS) | ninguno | mismo píxel caliente (C0 n=1, K n=1) | propia, mismo gránulo: K más cerca, pct 0.65; otra pasada -48 min: K más cerca, pct 0.26 |
| 47 | Lastarria | VIIRS375 | 2026-09-21 06:06 | no | -25.1514, -68.5233 | 2.48, NO | -25.1601, -68.5163 | 1.29, NO | 1.35 (CONS) | sólo K | otro lugar (a 1.2 km del píxel de C0 más cercano) | otra pasada -60 min: K más cerca, pct 0.00 |
| 48 | Lastarria | VIIRS375 | 2026-09-26 05:48 | no | -25.1584, -68.5106 | 1.12, N | -25.1546, -68.5237 | 2.25, NO | 2.4 (CONS) | sólo K | mismo píxel caliente (C0 n=2, K n=1) | sin imagen |
| 49 | Lastarria | VIIRS375 | 2026-09-27 05:54 | no | -25.1595, -68.5079 | 0.94, N | -25.1584, -68.5155 | 1.37, NO | 2.4 (CONS) | ninguno | mismo píxel caliente (C0 n=1, K n=1) | sin imagen |
| 50 | NevadosDeChillan | MODIS | 2026-10-01 01:45 | sí | -36.8636, -71.3972 | 1.80, O | -36.8768, -71.3796 | 1.56, S | 1.41 (CONS) | ambos | mismo píxel caliente (C0 n=7, K n=2) | sin imagen |
| 51 | NevadosDeChillan | MODIS | 2026-10-05 07:50 | sí | -36.8755, -71.3764 | 1.39, S | -36.8766, -71.3700 | 1.64, SE | 1.0 (CONS) | sólo C0 | mismo píxel caliente (C0 n=4, K n=1) | sin imagen |
| 52 | NevadosDeChillan | VIIRS375 | 2026-03-22 04:54 | no | -36.8659, -71.3761 | 0.34, S | -36.9021, -71.3705 | 4.39, S | 4.28 (CONS) | sólo K | mismo píxel caliente (C0 n=1, K n=1) | sin imagen |
| 53 | PlanchonPeteroa | VIIRS375 | 2026-05-13 05:18 | no | -35.2182, -70.5904 | 2.98, NO | -35.2398, -70.5747 | 0.19, NO | 1.55 (CONS) | ninguno | otro lugar (a 2.8 km del píxel de C0 más cercano) | otra pasada +48 min: K más cerca, pct 0.26 |
| 54 | PuyehueCordonCaulle | VIIRS375 | 2026-04-10 04:48 | no | -40.5265, -72.1470 | 0.13, SO | -40.5471, -72.1677 | 3.01, SO | 7.83 (CONS) | ninguno | mismo píxel caliente (C0 n=1, K n=1) | sin imagen |
| 55 | PuyehueCordonCaulle | VIIRS750 | 2026-04-09 06:00 | no | -40.5215, -72.1470 | 0.45, N | -40.5258, -72.1444 | 0.15, E | 7.83 (CONS) | ambos | mismo píxel caliente (C0 n=24, K n=1) | sin imagen |
| 56 | PuyehueCordonCaulle | VIIRS750 | 2026-06-06 06:12 | no | -40.5318, -72.1439 | 0.73, S | -40.5257, -72.1466 | 0.04, SO | 7.83 (CONS) | sólo K | mismo píxel caliente (C0 n=13, K n=1) | reciclada (md5 anterior): igual, pct 0.95; otra pasada -102 min: K más lejos, pct 0.93 |
| 57 | Tupungatito | VIIRS375 | 2026-04-26 04:48 | no | -33.3646, -69.8247 | 2.72, N | -33.3907, -69.8251 | 0.22, SE | 4.89 (CONS) | sólo K | otro lugar (a 2.9 km del píxel de C0 más cercano) | sin imagen |
| 58 | Tupungatito | VIIRS375 | 2026-05-29 06:06 | no | -33.3643, -69.8263 | 2.75, N | -33.3898, -69.8294 | 0.29, O | 4.89 (CONS) | sólo K | otro lugar (a 2.9 km del píxel de C0 más cercano) | propia, mismo gránulo: K más cerca, pct 0.82; otra pasada -48 min: K más cerca, pct 0.07 |
| 59 | Tupungatito | VIIRS375 | 2026-05-31 06:24 | no | -33.3739, -69.8513 | 2.86, NO | -33.3887, -69.8271 | 0.08, NO | 5.21 (CONS) | sólo K | otro lugar (a 2.8 km del píxel de C0 más cercano) | propia, mismo gránulo: K más cerca, pct 0.90; otra pasada -102 min: K más cerca, pct 0.04 |
| 60 | Tupungatito | VIIRS375 | 2026-06-03 05:24 | no | -33.3648, -69.8222 | 2.73, N | -33.3869, -69.8261 | 0.24, N | 5.41 (CONS) | ninguno | otro lugar (a 2.5 km del píxel de C0 más cercano) | propia, mismo gránulo: K más cerca, pct 0.90; otra pasada -54 min: K más cerca, pct 0.50 |
| 61 | Tupungatito | VIIRS375 | 2026-09-14 06:18 | sí | -33.3804, -69.8562 | 2.94, O | -33.3877, -69.8271 | 0.17, NO | 2.97 (OCR), sólo OCR | ninguno | otro lugar (a 2.8 km del píxel de C0 más cercano) | otra pasada +77 min: K más cerca, pct 0.84 |
| 62 | Villarrica | MODIS | 2026-09-04 07:50 | sí | -39.4156, -71.9406 | 0.51, N | -39.4134, -71.9254 | 1.46, NE | 1.41 (CONS) | ambos | mismo píxel caliente (C0 n=6, K n=1) | otra pasada -86 min: K más cerca, pct 0.03 |

## 7. Archivos

- `s1_tabla.py`: posiciones, protección, filas de MIROVA pareadas (±120 s) -> `s1_tabla.json`, `s1_tabla.txt`.
- `s2_emparejar.py`: TIF por hora de adquisición, md5 reciclado -> `s2_emparejar.json`.
- `s3_bajar.py`: 40 GeoTIFF de a uno por la API, con `index.csv` remoto -> `tif\`.
- `s4_analisis.py`: radio, objeto en la imagen, nulo sesgado (descartado) -> `s4_analisis.json`, `s4_analisis.txt`.
- `s5_pixeles.py`: mismo píxel u otro lugar, desde los records crudos -> `s5_pixeles.json`, `s5_pixeles.txt`.
- `s6_nulo.py`: nulo justo del anillo -> `s6_nulo.json`.
- `s7_tablas.py`: `tabla_resumen.md`, `tabla_movidas.md`.
