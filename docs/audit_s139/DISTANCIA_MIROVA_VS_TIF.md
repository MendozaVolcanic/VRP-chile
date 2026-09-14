# S139: la distancia que MIROVA publica por pasada es la del píxel alertado MÁS LEJANO

**Fecha**: 2026-09-14 (hora del servidor, A86). **Alcance**: auditoría read-only. No se modificó
ningún archivo del repositorio fuera de este informe y de `experiments/_s139_audit/distancia_tif/`.
No se tocó `../mirova-tif-archive` salvo para leerlo.

---

## 1. Respuesta

El número que MIROVA publica por pasada, el que el scraper guarda como `Distancia_km` y con el que
decide etiquetar FALSO_POSITIVO, se comporta como **`Max_Dist`**: la distancia de la cumbre al
**píxel alertado más lejano**, no al más caliente. Dos pruebas independientes lo dicen, las dos
calibradas contra el archivo del propio MIROVA, donde las dos definiciones conviven en la misma
fila y por lo tanto la respuesta correcta se conoce de antemano:

| prueba | predice "más caliente" | predice "más lejano" | medido en la web |
|---|---|---|---|
| exceso que ningún corrimiento de origen explica | 0,000 km | +0,232 km [0,229; 0,235] | **+0,113 km [0,072; 0,153]** (n = 171) |
| ídem, sólo foco a 5 km o menos del centro | 0,000 km | +0,241 km | **+0,301 km [0,180; 0,436]** (n = 79) |
| crecimiento del exceso con el VRP | 0,000 km por década | +0,238 km/déc. [0,232; 0,243] | **+0,211 km/déc. [0,102; 0,335]** (n = 171) |

Las dos pruebas excluyen el cero con 95 % de confianza y caen sobre la predicción de la hipótesis
"más lejano". La segunda no depende del punto de origen (el VRP no tiene nada que ver con el rumbo
del foco), así que no comparte el confusor de la primera.

**Fuerza de la conclusión, honestamente**: firme para el conjunto agregado y para las pasadas con
foco cerca del cráter; **más débil para los focos lejanos** (>10 km), donde el exceso medido es
+0,063 km [0,003; 0,123] contra los +0,126 km que predice `Max_Dist` en el archivo OSF para ese
mismo estrato. Ahí el dato es compatible con las dos hipótesis y se marca **SOSPECHA**.

Y lo más importante para el uso operacional: **la pregunta importa mucho menos de lo que parecía.**
En los diez volcanes chilenos del archivo OSF las dos definiciones se separan 0,30 km en mediana y
coinciden dentro de 1 km en el 86,7 % de las 48.360 filas. El caso que preocupaba (una fila
FALSO_POSITIVO con el cráter caliente adentro del cúmulo) existe, pero es el **7,8 %** de las filas
que el umbral del scraper escondería.

---

## 2. Por qué importa, en términos del volcán

MIROVA no reporta un píxel: reporta un **cúmulo** de píxeles que superaron su prueba, y de ese
cúmulo publica un solo número de distancia. Si ese número es la posición del punto más caliente,
entonces "distancia grande" significa "el calor está lejos del cráter" y esconder la fila es
correcto. Si es la extensión del cúmulo, entonces "distancia grande" significa "el cúmulo llega
lejos", y el cúmulo puede perfectamente empezar en el cráter: esconder la fila borra una anomalía
real del volcán. Es la diferencia entre un dato que dice "acá no pasa nada" y uno que dice "no sé".

---

## 3. Correcciones al encargo (verificadas en esta sesión)

1. **Los TIF SÍ están georreferenciados.** El encargo decía "sin georreferencia en tags". Cada TIF
   trae `ModelPixelScaleTag`, `ModelTiepointTag` y `GeoKeyDirectoryTag` con EPSG:4326, y `rasterio`
   los abre con transformación correcta (verificado sobre `Lascar/20260509_013955_VIIRS375.tif`:
   escala 0,0036730 x 0,0033908 grados, o sea 375 m; `Software = MATLAB R2024b, Mapping Toolbox`).
   No hace falta reconstruir la georreferencia desde el `LatLonBox` del KMZ.
2. **El máximo crudo del TIF no sirve para nada en esta pregunta.** Sobre las 1.545 pasadas
   pareadas de la copia local, el máximo del campo quedó a **22,5 km del centro en mediana**
   (p25 = 16,5 km): es el terreno más tibio de la escena, el valle bajo contra la cumbre nevada,
   que es exactamente el gradiente topográfico de A69. Reproduce el hallazgo A24 de S70 con
   1.545 casos en vez de 5. La anomalía sólo aparece después de restarle al campo su mediana móvil.
3. **El pull del archivo de TIF no se relanzó** (falló por disco lleno). Se trabajó con la copia
   local de mayo y con una descarga selectiva, declarada en §4.

---

## 4. Materiales, ventanas y cobertura del pareo

**Archivo de TIF local**: `../mirova-tif-archive`, último commit 2026-05-20, 2.685 filas de
`index.csv`, 1.966 TIF, adquisiciones del **2026-05-08 21:43 al 2026-05-20 09:28 UTC**.

**Descarga selectiva** (`experiments/_s139_audit/distancia_tif/_dl_/`, ignorado por git):
**400 TIF, 49,1 MB**, adquisiciones del **2026-05-21 02:00 al 2026-09-07 05:30 UTC**, elegidos
entre 458 emparejables como las pasadas nocturnas con VRP > 0 posteriores a la copia local, con
prioridad a las FALSO_POSITIVO: **92 FALSO_POSITIVO y 308 ALERTA_TERMICA**; por sensor, 18 MODIS,
64 VIIRS750, 318 VIIRS375. Cero fallos de descarga. El índice remoto (`index.csv` de GitHub) llega
al **2026-09-14 11:27 UTC**.

**Ground truth**: `data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv`,
36.255 filas del 2026-01-10 al 2026-09-07 (1.413 ALERTA_TERMICA, 830 FALSO_POSITIVO,
34.012 RUTINA). Variantes de nombre resueltas con el diccionario completo de A14.

**Archivo OSF v2.5**: `data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv`, 615.470 filas globales,
de las cuales **48.360 son de los 10 volcanes chilenos** (Tupungatito no está), del 2000 al
2025-12-31. **No hay solape temporal con el CSV de la web** (que empieza el 2026-01-10): las dos
fuentes nunca describen la misma pasada, así que el OSF se usa sólo para **calibrar** el
instrumento, nunca para parear filas.

### Qué significa el timestamp del nombre del TIF (verificado)

De las 2.684 filas del índice local, el **84,8 %** trae `acquisition_utc`. En ésas, el nombre del
archivo coincide con la adquisición dentro de 60 s en el **82,3 %** (el resto discrepa una a dos
horas: mismo paso orbital, gránulo distinto, ya documentado en `experiments/_s134_audit/f2`). Donde
falta `acquisition_utc`, el nombre coincide con `last_modified_utc` en el **99,3 %**. Por eso el
pareo usa `acquisition_utc` cuando existe y el nombre cuando no, con **tolerancia de 30 minutos**
contra `Fecha_Satelite_UTC`.

### Cobertura (punto 1 del encargo)

Denominador: filas ALERTA_TERMICA o FALSO_POSITIVO con `VRP_MW` > 0 del CSV, dentro de la ventana
del archivo remoto (2026-05-08 a 2026-09-14). **n = 1.264; con TIF 838 (66,3 %); sin TIF 426.**

| corte | n | con TIF | cobertura |
|---|---:|---:|---:|
| ALERTA_TERMICA | 760 | 509 | 67,0 % |
| FALSO_POSITIVO | 504 | 329 | 65,3 % |
| MODIS | 49 | 38 | 77,6 % |
| VIIRS750 | 185 | 127 | 68,6 % |
| VIIRS375 | 1.030 | 673 | 65,3 % |
| noche | 973 | 621 | 63,8 % |
| día | 291 | 217 | 74,6 % |
| VIIRS375 FALSO_POSITIVO de noche | 202 | 104 | 51,5 % |

El archivo de TIF también es un poller de ~1 h: una pasada que MIROVA sobrescribió antes de la
captura no está. La cobertura es una **cota inferior** de lo que MIROVA publicó, mismo argumento
que S128.

---

## 5. Cuánto separan las dos definiciones (archivo OSF, exógeno)

`experiments/_s139_audit/distancia_tif/01_*.py` y `03_*.py`.

El esquema v2.5 define `LAT/LON` como el píxel alertado más caliente y `Max_Dist` como la distancia
de la cumbre al píxel alertado más lejano. Calculando la distancia al píxel más caliente y
restándola de `Max_Dist`, sobre las 48.360 filas chilenas:

| estrato | n | Npix mediana | separación mediana | p90 | iguales dentro de 0,19 km |
|---|---:|---:|---:|---:|---:|
| todas | 48.360 | 3 | **0,304 km** | 1,137 km | 33,3 % |
| **Npix = 1 (control positivo)** | 8.357 | 1 | **0,000 km** | 0,216 km | 71,4 % (98,6 % dentro de 0,5 km) |
| Npix 2 a 3 | 16.090 | 2 | 0,216 km | 0,726 km | 42,3 % |
| Npix 4 a 10 | 21.831 | 5 | 0,551 km | 1,264 km | 15,0 % |
| **Npix ≥ 11 (control negativo)** | 2.082 | 13 | **1,091 km** | | 1,9 % |
| VIIRS 375 m | 32.688 | 3 | 0,243 km | 0,708 km | 37,0 % |
| VIIRS 750 m | 2.515 | 6 | 0,752 km | 1,474 km | 16,6 % |
| MODIS 1 km | 13.157 | 3 | 0,551 km | 1,602 km | 27,2 % |

Los dos controles se comportan como deben: donde el cúmulo es un solo píxel las dos definiciones
coinciden exactamente, y donde es grande se separan más de un kilómetro.

### Desde qué punto mide MIROVA (hallazgo lateral, sólido)

La primera versión de esta medición falló su propio control positivo (con `Npix = 1` las dos cifras
coincidían sólo en el 47 %). La causa no era el archivo sino el origen: `Volc_LAT/LON` viene
redondeado a tres decimales. Las filas `Npix = 1` son una trilateración (se conoce el píxel y su
distancia exacta), así que el origen se despeja por mínimos cuadrados. Resultado, en VIIRS 375 m:

- el ajuste cierra con **residuo mediano de 0,3 a 1,8 m** sobre 265 a 1.100 filas por volcán;
- el origen está **250 m al suroeste** del `Volc_LAT/LON` publicado, con el mismo valor
  (-0,25 / -0,25 km) en los **diez** volcanes, pese a que el redondeo de cada uno es distinto;
- control negativo con las distancias barajadas: residuo de 700 a 8.800 m.

En MODIS el mismo ajuste queda en 99 a 216 m, bastante peor, coherente con que la grilla de 1 km no
esté anclada igual. **Conclusión**: `Max_Dist` es una distancia euclídea desde un punto fijo a un
centro de píxel del retículo del sensor, y el origen no es exactamente la coordenada que el propio
archivo publica. Esto toca D15 y A93 y conviene anotarlo en el catálogo de divergencias.

---

## 6. La prueba sobre la web (puntos 2 y 5 del encargo)

`04_*.py`, `06_*.py`, `07_*.py`, `08_*.py`, `09_*.py`.

**Cómo se encuentra el foco.** Restarle al campo su mediana móvil de 9 píxeles (3,4 km en VIIRS375)
borra el gradiente topográfico, que varía en decenas de kilómetros, y deja el foco, que vive en uno
o dos píxeles. Control de que el filtro mide algo: la prominencia mediana del máximo filtrado es
**7,93 sigma** en las pasadas ALERTA_TERMICA (n = 396), **14,98 sigma** en las FALSO_POSITIVO
(n = 128, incendios y salares, señales fuertes) y **5,29 sigma** en las RUTINA (n = 1.418).
Control de pareo barajando las distancias entre pasadas: la coincidencia dentro de 0,5 km cae de
**40,8 % a 4,9 %** (n = 385). El instrumento mide algo real.

**El confusor y cómo se separa.** En las pasadas con foco cerca del cráter la distancia publicada
queda unos 0,26 a 0,30 km por encima de la distancia al foco, que es justo lo que predice
`Max_Dist`. Pero también es del tamaño del corrimiento de origen de §5, así que el número solo no
decide. Mover el origen una distancia δ cambia la distancia a un punto en −δ·û, o sea depende del
**rumbo** del foco y de nada más; el exceso del cúmulo no mira el rumbo. Regresando el residuo
contra el rumbo, la **constante** es lo que ningún origen puede explicar:

| conjunto | n | constante | IC 95 % |
|---|---:|---:|---|
| control positivo OSF, publicada = más caliente | 30.537 | 0,000 km | [0,000; 0,000] |
| control negativo OSF, publicada = `Max_Dist` | 30.537 | +0,232 km | [0,229; 0,235] |
| ídem, sólo `d_hot` ≤ 5 km | 22.430 | +0,241 km | |
| ídem, sólo `d_hot` > 10 km | 3.991 | +0,126 km | |
| **web, todas** | 171 | **+0,113 km** | [0,072; 0,153] |
| web, ALERTA_TERMICA | 105 | +0,291 km | [0,176; 0,423] |
| web, FALSO_POSITIVO | 66 | +0,063 km | [0,009; 0,121] |
| web, foco ≤ 5 km | 79 | +0,301 km | [0,180; 0,436] |
| web, foco > 10 km | 63 | +0,063 km | [0,003; 0,123] |

*(El control de barajar los residuos entre pasadas, que el script también corre, **no informa sobre
la constante**: barajar conserva la media. Sólo destruye el término direccional, y ahí sí funciona.
Se declara para que nadie lo lea como validación de la constante.)*

**La prueba ortogonal.** Cuanto más potente la anomalía, más píxeles superan el umbral y más grande
es el cúmulo: el píxel más caliente sigue sobre el foco, el más lejano se aleja. Entonces el exceso
tiene que crecer con el VRP si la web publica el más lejano, y no crecer si publica el más caliente.
La pendiente esperada no se inventa, se mide en el archivo OSF:

| conjunto | n | pendiente (km por década de VRP) | IC 95 % |
|---|---:|---:|---|
| OSF VIIRS375, si publicara `Max_Dist` | 30.537 | +0,238 | [0,232; 0,243] |
| OSF, si publicara el más caliente | | 0,000 | exacto por construcción |
| **web, todas** | 171 | **+0,211** | [0,102; 0,335] |
| web, sólo VIIRS375 | 160 | +0,218 | [0,095; 0,345] |
| web, foco ≤ 5 km | 79 | +0,361 | [0,096; 0,622] |

**Robustez al filtro.** Si la pendiente la fabricara la ventana de la mediana móvil (una anomalía
grande contamina su propia ventana), cambiarla la cambiaría mucho. Medido con cuatro ventanas:

| ventana | km en VIIRS375 | n | exceso mediano | pendiente | IC 95 % |
|---:|---:|---:|---:|---:|---|
| 5 px | 1,9 | 182 | +0,093 km | +0,178 | [0,080; 0,287] |
| 9 px | 3,4 | 171 | +0,093 km | +0,211 | [0,102; 0,335] |
| 15 px | 5,6 | 136 | +0,101 km | +0,278 | [0,131; 0,432] |
| 21 px | 7,9 | 127 | +0,093 km | +0,314 | [0,166; 0,462] |

Las cuatro excluyen el cero y las cuatro rodean la predicción de `Max_Dist`. El exceso mediano ni
se mueve.

### Casos a mano contra la lámina `Dist` (punto 5)

- **MODIS**: `data/png/Llaima/20260520_085930_MODIS_Dist.png`, encabezado
  "Last Update: 20-May-2026 07:10:00", "VRP = 1 MW", estrella verde a ≈24,7 km. La fila del CSV
  para Llaima MODIS 2026-05-20 07:10 dice **1,81 MW y 24,70 km, FALSO_POSITIVO**. El número del
  CSV es el que MIROVA dibuja.
- **VIIRS750**: `data/png/Llaima/20260520_102000_VIIRS750_Dist.png`, "Last Update: 20-May-2026
  06:30:01", "Thermal anomaly: NONE", "VRP = NaN MW" y **ningún punto dibujado**. Control negativo:
  sin cúmulo alertado no hay distancia publicada.
- **VIIRS375**: `data/png/Isluga/20260520_072324_VIIRS375_Dist.png`, los puntos rojos del último mes
  se apoyan apenas sobre 0 km, coherente con los 0,84 km que el CSV trae para Isluga.

La lámina `Dist` sólo grafica un valor por pasada, con la leyenda ">5 km" en negro y "<5 km" en
rojo, y la lámina `VRP` colorea su serie con la misma regla. No dibuja el cúmulo ni marca píxeles,
así que las imágenes confirman **qué número** es (el mismo del CSV) pero no **cuál definición**.

---

## 7. Cuantización (punto 4 del encargo)

`10_*.py`. Sobre los valores únicos de `Distancia_km` del CSV con VRP > 0, comprobando si cada uno
es `paso · sqrt(i² + j²)` con i, j enteros y el paso igual al tamaño de píxel del sensor:

| sensor | valores únicos en la web | sobre el retículo | `Max_Dist` del OSF sobre el retículo |
|---|---:|---:|---:|
| VIIRS375 (paso 0,375 km) | 458 | **100,0 %** | 100,0 % |
| VIIRS750 (paso 0,750 km) | 80 | **100,0 %** | 100,0 % |
| MODIS (paso 1,000 km) | 38 | **100,0 %** | 100,0 % |

Los primeros valores de VIIRS375 son 0,38 / 0,53 / 0,75 / 0,84 / 1,06 / 1,13 / 1,19 / 1,35 / 1,50 /
1,55, que son 0,375·√1, √2, √4, √5, √8, √9, √10, √13, √16, √17. Los de MODIS son 1,00 / 1,41 /
2,00 / 2,24 / 3,16, el retículo de 1 km. Se publican con dos decimales.

**Qué prueba y qué no**: prueba que la distancia publicada es de un **centro de píxel** a un nodo
fijo del retículo, y que ese retículo es el mismo que el de `Max_Dist`. **No discrimina** entre las
dos hipótesis, porque el píxel más caliente también es un centro de píxel del mismo retículo. Y
confirma D15: un `Distancia_km` de 0,00 significa "en la misma celda que la referencia", no "a cero
metros del cráter".

---

## 8. ¿Hay señal en el cráter en las filas FALSO_POSITIVO? (punto 3)

**El proxy que pedía el encargo resultó INCONCLUSO, y hay que decirlo.** Se midió si el máximo del
campo filtrado dentro del `inner_radius_km` supera el percentil 99 del mismo campo en la escena,
sobre 1.910 pasadas del 2026-05-09 al 2026-09-07:

| etiqueta | n | supera el p99 | pico dentro del inner |
|---|---:|---:|---:|
| ALERTA_TERMICA | 397 | 83,6 % | 4,96 sigma |
| FALSO_POSITIVO | 130 | **51,5 %** | 2,47 sigma |
| RUTINA (control negativo) | 1.383 | **43,1 %** | 2,35 sigma |

El umbral está mal calibrado: un percentil 99 sobre 17.956 píxeles deja ~180 píxeles por encima en
toda la escena, y un disco de inner 5 km en VIIRS375 tiene ~230 píxeles, así que el control negativo
ya da 43 % por pura construcción. Las FALSO_POSITIVO quedan 8 puntos sobre ese piso: **SIN DATO**,
no "no hay señal". La medición correcta necesitaría el conjunto de píxeles alertados, que el TIF no
trae porque la prueba NTI de MIROVA usa la banda térmica y el archivo sólo publica la MIR.

**La cota sí se puede dar, y sale del archivo del propio MIROVA.** Se despejó primero el umbral real
del scraper por volcán, como el corte entre la ALERTA más lejana y el FALSO_POSITIVO más cercano
del CSV (los dos conjuntos no se solapan en 8 de 9 volcanes; Tupungatito sí se solapa y su umbral
queda incierto):

| volcán | umbral estimado | filas OSF que lo superan por `Max_Dist` | de ésas, con el más caliente adentro |
|---|---:|---:|---:|
| Láscar | 5,70 km | 963 | **20,5 %** |
| Chaitén | 4,87 km | 74 | 16,2 % |
| Puyehue Cordón Caulle | 19,29 km | 65 | 13,9 % |
| Villarrica | 4,50 km | 249 | 12,5 % |
| Nevados de Chillán | 4,75 km | 599 | 9,0 % |
| Isluga | 5,26 km | 912 | 4,2 % |
| Lastarria | 3,24 km | 1.079 | 0,8 % |
| Planchón Peteroa | 3,83 km | 582 | 0,7 % |
| **agregado** | | **4.523** | **7,8 %** (354 filas) |

---

## 9. Conclusión operativa para el banco de prueba (§7.1 de la spec)

1. **`Distancia_km` es `Max_Dist`**: la distancia del origen de la grilla al píxel alertado más
   lejano, cuantizada al retículo del sensor y publicada con dos decimales. Anotarlo así en el banco
   y en la ficha del ground truth. La pregunta 11 del correo a Coppola queda como **confirmación**,
   no como bloqueante.
2. **Una fila FALSO_POSITIVO NO se puede usar como "el cráter no tenía señal".** Es, en el 7,8 %
   agregado de los casos (hasta el 20,5 % en Láscar), un cúmulo que llega lejos y que puede empezar
   en el cráter. Usarla como negativo mete ese porcentaje de etiquetas equivocadas en el banco.
3. **Tampoco es "cráter tapado"**: no hay nada en la fila ni en el TIF que diga que el cráter estaba
   cubierto. La lectura correcta es **"sin información sobre el cráter"**, y el lugar del banco es
   la categoría de descartadas, no la de negativos.
4. **Lo que sí se puede usar como negativo limpio** es la fila **RUTINA**: sin anomalía publicada no
   hay punto dibujado en la lámina `Dist` (verificado a mano, §6), o sea MIROVA no alertó ningún
   píxel de la escena. Esa sí es la afirmación "no detecté nada".
5. **Consecuencia para la posición**: una fila con `Distancia_km` de 8 km no dice que el calor esté a
   8 km. Dice que el cúmulo llega hasta 8 km. Cualquier comparación de POSICIÓN contra nuestra
   detección (A61, A93) está comparando un radio de extensión contra la posición de un centroide, y
   eso no es comparable. Para posición hay que usar `LAT/LON` del OSF, que sólo existe hasta 2025.

---

## 10. Límites y lo que queda marcado SOSPECHA

- **SOSPECHA**: el estrato de foco lejano (>10 km), exceso +0,063 km [0,003; 0,123] contra +0,126
  km predicho. Compatible con las dos hipótesis. El resto del peso de la conclusión no se apoya ahí.
- **El foco del TIF no es, verificadamente, el píxel más caliente del cúmulo de MIROVA.** Es el
  máximo del campo MIR filtrado. Si hubiera un sesgo sistemático entre los dos, sesgaría las
  mediciones de §6. No se encontró un mecanismo que lo produzca y la robustez al kernel (§6) es
  evidencia en contra, pero no es prueba.
- **OSF y la web nunca describen la misma pasada** (2000 a 2025 contra 2026). El OSF calibra el
  instrumento; no valida filas.
- **Ventana corta**: la comparación TIF contra web cubre del 2026-05-09 al 2026-09-07, cuatro meses,
  con 171 pasadas en el subconjunto de la prueba. Los conteos absolutos de este informe no son
  comparables con los de otra sesión sin su ventana pegada (A90).
- **MODIS queda casi sin medir** en §6: 11 pasadas en el subconjunto de la prueba. Lo que se afirma
  de MODIS sale del archivo OSF, no de la web.
- **El umbral del scraper es una estimación** despejada de los datos, no su configuración: el
  scraper `Mirova-v1` no está en este repositorio. Tupungatito solapa (ALERTA hasta 6,55 km,
  FALSO_POSITIVO desde 5,03 km) y su umbral no se pudo fijar.
- **Discrepancia observada, no explicada**: la lámina `Dist` de Láscar del 19-may lleva "VRP = 0 MW"
  en el encabezado mientras la lámina `Latest10NTI` de la misma actualización dice "VRP = 0,82 MW".
  No afecta nada de lo anterior, pero si alguien usa el encabezado de la lámina `Dist` como fuente
  de VRP, conviene revisarlo.

---

## 11. Scripts y salidas

Todo en `experiments/_s139_audit/distancia_tif/`:

| script | qué mide |
|---|---|
| `01_osf_maxdist_vs_hotpixel.py` | separación entre las dos definiciones en el archivo OSF |
| `02_ceros_y_forma_por_volcan.py` | discriminante de los ceros (resultó **sin poder**, se conserva) |
| `03_desde_donde_mide_mirova.py` | trilateración del origen; separación con el origen corregido |
| `04_pareo_tif_vs_distancia.py` | pareo de 1.545 pasadas; refuta el máximo crudo del TIF |
| `05_bajar_tif_faltantes.py` | descarga selectiva (400 TIF, 49,1 MB) |
| `06_hipotesis_caliente_vs_lejano.py` | foco por paso alto; ajuste del origen; comparación directa |
| `07_exceso_no_explicable_por_el_origen.py` | la constante direccional, con controles sobre OSF |
| `08_exceso_crece_con_la_magnitud.py` | la prueba ortogonal de la pendiente contra el VRP |
| `09_robustez_kernel.py` | las cuatro ventanas del filtro |
| `10_falsos_positivos_y_cuantizacion.py` | señal en el cráter (inconcluso) y cuantización |
| `11_umbral_del_scraper_y_timestamps.py` | umbral por volcán, timestamps, cota del 7,8 % |
| `12_cobertura_del_pareo.py` | cobertura del pareo por sensor, etiqueta y hora |

Cada script escribe su `.json` con el mismo nombre. Los PNG del archivo no se copiaron al
repositorio; los TIF descargados viven en `_dl_/`, que `.gitignore` ya excluye.
