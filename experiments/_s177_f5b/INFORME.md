# F5b re-corrido (S177): ¿la lámina PNG de MIROVA dice que su foco en Chillán coincide con el nuestro?

Carpeta de trabajo: `C:\Users\nmend\vrp-temporales\s177_f5b\`. Originales de F5b y V5B intactos (copiados a `C:\Users\nmend\vrp-temporales\s177_f5b\orig\`, nada escrito en el worktree ni en el repo). Sin commits, sin llamadas a NASA, a GitHub ni a credenciales. Un solo proceso pesado a la vez; C: quedó en 14 GB libres.

## 1. Respuesta corta

Con la mancha saturada conservada y un nulo al lado, la lámina permite decir **menos de lo que F5b creyó y más de lo que el nulo de V5B sugería**:

1. **Descartar que el foco de MIROVA esté desplazado.** CONFIRMADO en VIIRS 375 y VIIRS 750 de Chillán: el hallazgo 351 de F5b («el foco de MIROVA está a 1 a 2,5 km de nuestro punto» en 4 protegidas) desaparece. Las 4 pasan a «mismo foco» con nuestro punto a 0,19 a 0,78 km del centro de la mancha. La lámina habría detectado un desplazamiento de 1 km en VIIRS 375 (la clase «i» cae de 98 % a 10 %) y de 1,5 a 2 km en VIIRS 750 (de 100 % a 43 % y 8 %), y no encontró ninguno.
2. **Confirmar que es el mismo píxel de esa noche, más allá de «la misma zona»: sólo en parte.** La clase binaria separa claramente contra el nulo de permutación (VIIRS 375: 98 % observado contra 62 %; VIIRS 750: 100 % contra 86 %). Pero con un nulo que iguala la geometría de visada (otras pasadas con zenit y azimut parecidos) el margen casi desaparece (VIIRS 375: 98 % contra 93 %, diferencia +0,05 con IC95 que incluye 0; VIIRS 750: 100 % contra 99 %). Lo que queda es poco: en VIIRS 375, AUC 0,64 y una ventaja de 0,11 a 0,12 en la superposición de cúmulos. Mi lectura: la lámina y nosotros vemos el mismo píxel del cráter en cada pasada, que es lo que da un foco fijo visto con una geometría dada; no hay evidencia independiente de «el mismo foco de esa noche» frente a «el cráter de siempre».
3. **MODIS: SIN DATO.** El nulo no separa (AUC 0,52, IC95 de 0,39 a 0,65), la lámina MODIS no está validada contra TIF, y 4 protegidas quedan a 3,0 a 6,1 km sin que se pueda decir si es otro foco o un desfase de geolocalización.
4. **Nunca «el píxel».** Con la paleta saturada, la lámina no ordena los píxeles de la mancha; sólo se puede hablar de la mancha (mediana 3 celdas en VIIRS 375 y 4 en VIIRS 750 en Chillán; hasta 20 celdas) y de su centroide.

## 2. El fenómeno, antes del código

En una erupción el foco térmico es tan intenso que la paleta de gris de la lámina Latest10NTI se satura: la anomalía se dibuja como una **mancha blanca de varias celdas**, no como un píxel. El «sin dato» (zona fuera de la franja del sensor) también es blanco, pero es enorme (2000 px o más) o toca el borde del panel. F5b trató toda componente blanca de 20 px o más como «sin dato», así que **borró justo el foco de la erupción** y eligió un píxel del borde (V5B-01).

Un segundo fenómeno explica por qué la clase binaria engaña. El cráter de Chillán es fijo y el foco se mueve unas pocas celdas entre pasadas. Nuestro punto y la mancha de MIROVA caen siempre cerca del cráter, así que una clase «i» («la mancha está a menos de 0,75 km de nuestro punto») sale verdadera incluso con el punto de otra noche. Por eso hace falta el nulo, y por eso hay que preguntarse si lo que lo explica es la zona, la geometría de visada o la identidad del foco.

## 3. El instrumento corregido y sus controles

Código: `C:\Users\nmend\vrp-temporales\s177_f5b\lib177.py` (copia de `f5b_lib.py` más un selector nuevo; `f5b_lib.py` se importa sin tocarlo). Sin dato = componente blanca (min RGB > 245) que toca el borde del panel o de 400 px o más. Tres selectores: A (el de F5b), C1 (sólo la máscara corregida) y C2 (C1 más empates: si el máximo está saturado, los píxeles saturados separados por 1 px forman una sola mancha y se guardan todas las componentes).

| Control | Resultado | Etiqueta | Script y salida |
|---|---|---|---|
| Reproducción: A con el código original de F5b da las mismas lat/lon que `p8_clases.json` | 303 de 303 | CONFIRMADO | `s02_manchas.py`, `salidas\s02_manchas.out.txt` |
| Reproducción de las clases guardadas de F5b con `lib177.clase` sobre la mancha A | 303 de 303 con lámina (los 2 sin lámina son iv) | CONFIRMADO | `s03_clases_y_nulo.py`, sección 1 |
| Caso conocido, Chillán VIIRS_NOAA20_750 2026-10-10 06:54 UTC: A da lum 196,7 y 1 px; C1 y C2 dan lum 255, 48 px, 11 celdas (centro -36,86492, -71,37219) | conserva la mancha, igual que V5B m1 | CONFIRMADO | `s02_manchas.out.txt` |
| No cambia láminas sin mancha: records donde A no borraba ninguna componente de calor | C1 igual a A en 268 de 268 | CONFIRMADO | `s02_manchas.out.txt` |
| Pregunta 2 (el selector puede dar otra cosa): records donde C1 difiere de A | 35 de 303, los 35 son los que tenían componente borrada (Chillán VIIRS 750 17, MODIS 12, VIIRS 375 2; Caulle 4) | CONFIRMADO | `s02_manchas.out.txt` |
| C2 sin saturación es igual a C1 | 0 diferencias entre los no saturados; C2 difiere de C1 en 14 records (Chillán: 1 VIIRS 375 y 1 MODIS) | CONFIRMADO | `s02_manchas.out.txt` |
| Umbral de sin dato de 100, 200, 400, 1000 y 1500 px | 0 records cambian de celda ni de área de mancha | CONFIRMADO | `s04_robustez.py`, sección A |
| Nulo de V5B reproducido con la mancha A (todos los volcanes, pasadas con control ok) | VIIRS 375: 94,8 % observado contra 72,0 % (V5B: 94,8 y 73,0); VIIRS 750: 94,0 contra 75,9 (V5B: 94,0 y 76,9). Mi nulo es exacto (todos los pares), el de V5B era por sorteo | CONFIRMADO | `s03_clases_y_nulo.out.txt`, sección 3 |

El histograma de componentes blancas que no tocan el borde (`s02_manchas.out.txt`) tiene 441 de menos de 50 px, 16 de 50 a 99, 2 de 100 a 149, 1 de 150 a 199 y 4 de 2000 o más: nada entre 200 y 2000 px. Por eso el umbral de 400 no es una elección delicada.

Una nota de inventario: las láminas distintas usadas son 291, no 288 como dice el INFORME de F5b; las 291 están en disco y su md5 coincide con el de F5b (`salidas\s01_disponibilidad.out.txt`). Las 2 pasadas sin lámina (Chillán MODIS 2026-10-10 07:40 y Láscar MODIS 2026-09-25 08:00) siguen sin lámina y se cuentan como iv; no se reemplazaron.

## 4. Antes y después, mismo universo (305 aciertos)

Formato i / iii / iv. «F5b» es lo guardado en `p8_clases.json`. «C1» cambia sólo la máscara. «C2p» es la variante primaria: mancha completa con empates, control «alguna celda de la mancha reproduce la `Distancia_km` de la tabla» (blando, no es «el píxel»), clase por distancia de nuestro punto al centroide de la mancha principal. «C2 sin control» mide sólo posición. Fuente: `salidas\s03_clases_y_nulo.out.txt` sección 2 y `salidas\s03_clases.csv`; transiciones en `salidas\s04_robustez.out.txt` sección D. CONFIRMADO como recuento.

| Universo | n | F5b | C1 | C2p | C2 sin control |
|---|---|---|---|---|---|
| Todos | 305 | 172 / 15 / 118 | 173 / 10 / 122 | 194 / 21 / 90 | 207 / 96 / 2 |
| Chillán VIIRS 375 | 69 | 46 / 1 / 22 | 46 / 1 / 22 | 57 / 1 / 11 | 68 / 1 / 0 |
| Chillán VIIRS 750 | 55 | 44 / 3 / 8 | 43 / 0 / 12 | 54 / 0 / 1 | 55 / 0 / 0 |
| Chillán MODIS (sin validar) | 23 | 15 / 6 / 2 | 18 / 4 / 1 | 18 / 4 / 1 | 18 / 4 / 1 |
| Chillán protegidas VIIRS 375 | 56 | 33 / 1 / 22 | 33 / 1 / 22 | 44 / 1 / 11 | 55 / 1 / 0 |
| Chillán protegidas VIIRS 750 | 53 | 42 / 3 / 8 | 41 / 0 / 12 | 52 / 0 / 1 | 53 / 0 / 0 |
| Chillán protegidas MODIS | 23 | 15 / 6 / 2 | 18 / 4 / 1 | 18 / 4 / 1 | 18 / 4 / 1 |
| Resto VIIRS 375 (sin Chillán) | 145 | 64 / 5 / 76 | 63 / 5 / 77 | 62 / 15 / 68 | 63 / 82 / 0 |

Cómo leerlo:

- **Qué mueve cada corrección.** Con C1 (sólo la máscara) las tres (iii) de VIIRS 750 desaparecen pero cuatro (i) y dos (iii) pasan a (iv): el control por centroide falla con una mancha grande porque el centroide de 11 celdas no reproduce la distancia de la tabla. El paso a «alguna celda de la mancha» (C2p) recupera esos casos; por eso los (iv) de VIIRS 750 bajan de 8 a 1. Ese cambio viene de la **definición del control**, no de nueva información de posición. El control en sí filtra poco en Chillán: la mancha de otra pasada reproduce la distancia de esta pasada en 67 % de los casos en VIIRS 375 (propio 84 %), 91 % en VIIRS 750 (propio 98 %) y 100 % en MODIS (propio 100 %) (`s03`, sección 5). Por eso la columna sin control es la lectura de posición más limpia.
- **Las 4 protegidas de 351** (`s03`, sección 2, y V5B): todas pasan de (iii) a (i). VIIRS_NOAA21 2026-10-18 05:06 (21,25 MW): centroide a 0,19 km, mancha de 5 celdas. VIIRS_NOAA20_750 2026-10-10 06:54 (15,26 MW): 0,78 km al centroide y 0,14 km a la celda más cercana, mancha de 11 celdas. VIIRS_NOAA20_750 2026-10-16 06:42 (14,02 MW): 0,48 y 0,29 km, 7 celdas. VIIRS_NOAA21_750 2026-10-29 06:42 (29,35 MW): 0,65 y 0,11 km, 8 celdas. El hallazgo 351 no se sostiene. CONFIRMADO.
- **La única (iii) VIIRS de Chillán que queda** es VIIRS_NOAA21 2026-10-30 04:42 (21,69 MW): 1,07 km al centroide (tolerancia 0,75) pero 0,63 km a la celda más cercana de una mancha de 11 celdas. F5b la tenía en (iv). Una mancha alargada con nuestro punto en un costado no es un foco desplazado: SOSPECHA de que es forma de la mancha, no medida más allá de eso.
- **Resto de los volcanes.** Allí el píxel más claro del inner a menudo no es la anomalía (la vara no alcanza, conclusión de F5b que la corrección no cambia). La unión de manchas saturadas de C2 puede juntar parches lejanos (dos de Cordón Caulle pasan de (i) a (iii) con centroides a 16 y 18 km, 8 y 2 componentes). Para esos volcanes la lectura honesta es C1 (63 / 5 / 77), no C2p. SIN DATO de posición del foco fuera de Chillán.

## 5. El nulo, con el mismo código

Mismo `lib177.clase` para el observado y el nulo; sólo cambia el punto que se compara con la mancha de la pasada i. N1: nuestro punto de cada otra pasada del mismo volcán y sensor (todos los pares, exacto). N2 y N2b: sólo pasadas a 3 y 1 día. N3: sólo pasadas con |diferencia de zenit| de 5 grados o menos y |diferencia de azimut| de 30 grados o menos (geometría de visada igualada; zenit y azimut del record de Chillán de la base 752d348bc, copiado por V5B). AUC = probabilidad de que la distancia propia sea menor que la de otra pasada (0,5 = la lámina no distingue pasadas). IC95 por bootstrap sobre pasadas (2000, semilla fija). Variante C2p, pasadas con control ok. Fuentes: `s03_clases_y_nulo.out.txt` sección 4 y `s04_robustez.out.txt` sección C.

| Chillán | n | Observado | Nulo N1 | Diferencia (IC95) | AUC N1 (IC95) | Nulo N3 | Diferencia N3 (IC95) | AUC N3 (IC95) |
|---|---|---|---|---|---|---|---|---|
| VIIRS 375 | 58 / 52 | 0,983 | 0,615 | +0,368 (+0,303 a +0,439) | 0,818 (0,776 a 0,863) | 0,929 | +0,052 (-0,008 a +0,109) | 0,641 (0,553 a 0,727) |
| VIIRS 750 | 54 / 44 | 1,000 | 0,861 | +0,139 (+0,099 a +0,193) | 0,714 (0,644 a 0,781) | 0,989 | +0,011 (0,000 a +0,028) | 0,609 (0,485 a 0,722) |
| MODIS (sin validar) | 22 / 12 | 0,818 | 0,779 | +0,039 (-0,136 a +0,177) | 0,519 (0,385 a 0,654) | 0,792 | +0,042 (-0,292 a +0,333) | 0,500 (0,250 a 0,750) |

(n es pasadas con control ok en N1 / en N3; N3 pierde pasadas sin al menos 2 vecinas de geometría parecida.) CONFIRMADO como cálculo; la interpretación es mía.

Lecturas:

- **¿Separa más que el nulo?** Contra el nulo ingenuo (N1, N2, N2b), sí en VIIRS, con p de permutación menor que 0,0001 en la distancia media (propia 0,28 contra 0,77 km en VIIRS 375; 0,51 contra 0,85 km en VIIRS 750). Contra el nulo con geometría igualada, no de forma distinguible de cero: el margen cae de +0,37 a +0,05 y de +0,14 a +0,01. Casi toda la separación que ve el nulo ingenuo es que las pasadas con otra geometría ponen el mismo píxel en otro lugar. Mantiene que **la clase «i», tal como la definió F5b, no mide identidad de foco**; V5B tenía razón en la conclusión aunque su nulo (73 y 77 %) estaba calculado con todos los volcanes juntos y la mancha borrada. Con sólo Chillán y la mancha completa el nulo N1 es 62 % y 86 %.
- **Techo de la clase.** En VIIRS 750 el observado es 100 %, así que la clase binaria no tiene margen. El barrido de umbral (`s03`, sección 6) muestra que la separación persiste a umbrales más finos: a 1 celda, VIIRS 375 tiene 75 % propia contra 33 % de otras pasadas y VIIRS 750 tiene 82 % contra 53 %; a 0,5 celda, 29 % contra 12 % y 38 % contra 17 %. Eso sigue siendo N1, es decir mezcla geometría.
- **Cúmulo contra cúmulo** (`s05_cumulo.py`, `salidas\s05_cumulo.out.txt`; usa los píxeles alertados nuestros del record, no sólo el punto): fracción de nuestros píxeles a una celda o menos de la mancha (cov_N) y fracción de celdas de la mancha a una celda o menos de alguno de nuestros píxeles (cov_M). Con geometría igualada, VIIRS 375: cov_N 0,77 contra 0,65 (diferencia +0,12, IC95 +0,04 a +0,19), cov_M 0,87 contra 0,75 (+0,11, +0,06 a +0,16). VIIRS 750: cov_N 0,93 contra 0,88 (+0,05, -0,03 a +0,13), cov_M 0,85 contra 0,71 (+0,14, +0,08 a +0,21). Es la única señal que sobrevive al nulo con geometría igualada: en VIIRS 375 los dos cúmulos calzan algo mejor de lo que calzaría un cúmulo de otra pasada de igual geometría. Magnitud pequeña. SOSPECHA de coincidencia de cúmulo específica de la noche, no CONFIRMADA. Además cov_N de 0,75 y 0,93 dicen que 25 % (VIIRS 375) y 7 % (VIIRS 750) de nuestros píxeles alertados caen a más de una celda de la mancha.
- **Dispersión entre pasadas** (`s03`, sección 7): nuestro punto se mueve 0,54 km al este y 0,30 al norte (desviación estándar) en VIIRS 375, y el centroide de la mancha 0,61 y 0,28; la correlación pasada a pasada es +0,93 este y +0,72 norte (p de permutación menor que 0,001). Es el mismo efecto de geometría: las dos medidas siguen el desplazamiento del píxel por ángulo de barrido. Los centroides de la mancha ocupan sólo 14 posiciones de celda distintas en 69 pasadas VIIRS 375 y 11 en 55 VIIRS 750: la resolución de la lámina es de una celda.

## 6. Lo que se sostiene, por sensor y por volcán

| Sensor y volcán | Se sostiene | Etiqueta |
|---|---|---|
| Chillán VIIRS 375 (69 aciertos, 56 protegidas) | Nuestro punto está a 0,75 km o menos del centroide de la mancha en 57 de 58 pasadas con control (98 %) y en 68 de 69 sin control. Un desplazamiento de 1 km se detectaría (la clase «i» cae a 10 %). No hay evidencia de foco desplazado. Identidad de foco más allá del cráter fijo: no distinguible, con un residuo pequeño a nivel de cúmulo (+0,11 a +0,12) | CONFIRMADO lo primero; SOSPECHA el residuo |
| Chillán VIIRS 750 (55 aciertos, 53 protegidas) | 54 de 54 pasadas con control y 55 de 55 sin control están a 1,5 km o menos del centroide. La mancha es grande (mediana 4 celdas, hasta 20; en el caso 10-10 06:54, 11 celdas con extensión de 2,4 km según V5B), así que la resolución efectiva es de 1,5 a 2 km: un desplazamiento de 2 km se detectaría (8 % siguen siendo «i»), uno de 1 km no (86 %). El nulo con geometría igualada no se distingue (AUC 0,61, IC95 incluye 0,5) | CONFIRMADO «no desplazado a 2 km o más»; SIN DATO por debajo |
| Chillán MODIS | No se puede saber. La lámina MODIS no está validada contra TIF (F5b hallazgo 354, V5B lo confirma), el nulo no separa (AUC 0,52; correlación pasada a pasada este +0,08, norte -0,36), y 4 protegidas (2026-10-17 08:50, 10-28 07:35, 10-17 02:20 y 10-30 08:55, con 7,1 a 14,4 MW) quedan a 3,0 a 6,1 km del centroide. Posible causa de nuestro lado: la memoria del proyecto anota una geolocalización MODIS corrida 1 a 3 km hacia el nadir (S151); no la verifiqué | SIN DATO; la causa SOSPECHA |
| Isluga, Láscar, Lastarria, Planchón, Caulle, Tupungatito, Chaitén | La lámina no sirve de vara de posición: el control falla en cerca de la mitad de las pasadas y una mancha de otra pasada lo pasa tan seguido como la propia (VIIRS 375: 52 % contra 54 %). Sin Chillán, la mancha saturada tampoco corresponde a la alerta (anomalías débiles) | SIN DATO |

## 7. Lo que no se puede saber (y por qué)

1. **Cuál píxel de la mancha es «el» foco.** La paleta satura y la lámina no ordena los píxeles. CONFIRMADO como límite; el selector de F5b elegía el primero en orden de barrido (V5B-02).
2. **Qué extensión física tiene la mancha.** El tamaño depende de dónde satura la paleta, no de la anomalía.
3. **Si el selector de mancha acierta con anomalías fuertes.** La georreferencia de la lámina se validó con anomalías débiles (correlación 0,992 a 0,994 contra TIF). Los TIF de referencia locales de Chillán tienen máximo de 0,08 a 0,58 y no hay TIF de validación de Chillán (los TIF terminaron el 2026-09-22); las láminas de Chillán en disco son todas posteriores (`s06_tif_chillan.py`, `salidas\s06_tif_chillan.out.txt`). No hay control positivo contra TIF con mancha saturada. Habría que bajar de `mirova-tif-archive` un par TIF y lámina de Chillán anterior al 22-sep con anomalía alta; no lo hice porque cae fuera de lo autorizado. SIN DATO.
4. **MODIS** (sección 6).
5. **Las 2 pasadas sin lámina** y los huecos de láminas de F5b (hallazgo 353): sin cambio.
6. **Origen real de la `Distancia_km` de MIROVA** (V5B-03): el control de distancia sigue siendo blando y no resuelve si es el centro, un extremo de la mancha o otro punto. En V750 las manchas de las cuatro pasadas de 351 llegan hasta 1,7 a 2,4 km del centro de MIROVA (cifra de V5B, `v5b\m1_mancha.out.txt`, no recalculada aquí) y la tabla dice 2,1 a 2,4 km, lo que es coherente con que la tabla informe un extremo; SOSPECHA, no probado.

## 8. Qué V5B atendí y qué quedó

| V5B | Estado |
|---|---|
| V5B-01 (la máscara borra la mancha) | Corregido en `lib177.py`; probado con el caso 10-10 06:54 y con 268 de 268 láminas sin mancha sin cambio; 35 records cambian |
| V5B-02 (empate: el primero en orden de barrido) | C2 guarda todas las componentes (unión con dilatación de 1 px); en Chillán sólo 1 de 69 VIIRS 375 y 1 de 22 MODIS tienen más de una componente. No se usa «el píxel» en ninguna cifra |
| V5B-03 (la regla se ajustó y se validó en los mismos 4 casos) | No lo reabrí. La georreferencia no cambió; sigue validada fuera de muestra por V5B (`m2_validacion`) con anomalías débiles |
| V5B-04 (la clase casi no separa) | Reproducido (72,0 y 75,9 % exacto), calculado ahora por Chillán y con geometría igualada (sección 5) |
| V5B-05 (docstring con el resultado esperado) | Mis cabeceras llevan sólo pre-registro y criterio de lectura, sin resultado; los resultados están en las salidas. El `p8_clasificar.py` original no se tocó. Mi control de instrumento por desplazamiento (s04, B) no es el sintético de F5b: mueve el punto en 8 direcciones y k = 0 a 3 km, y por construcción puede fallar; da 98 % a 0 % en VIIRS 375 |
| «Alguna celda de la mancha» contra «el píxel» | El control de distancia de C2p es del primer tipo y está rotulado «blando»; el control por centroide (C2_cc) y la columna sin control se reportan al lado. La clase usa el centroide, no la celda más cercana (que está en C2_min y da más «i» siempre) |

## 9. Reproducción

Desde `C:\Users\nmend\vrp-temporales\s177_f5b\` con `python -I`:

- `s01_disponibilidad.py` -> `salidas\s01_disponibilidad.out.txt` (291 láminas y 14 TIF de referencia presentes, md5 igual).
- `s02_manchas.py` -> `salidas\s02_manchas.out.txt` y `salidas\s02_manchas.json` (selectores A, C1, C2 por acierto).
- `s03_clases_y_nulo.py` -> `salidas\s03_clases_y_nulo.out.txt` y `salidas\s03_clases.csv` (clases antes y después, nulo N1, N2, N2b, control del control, umbrales, dispersión).
- `s04_robustez.py` -> `salidas\s04_robustez.out.txt` (umbral de sin dato, desplazamiento, nulo N3, transiciones, MODIS por régimen).
- `s05_cumulo.py` -> `salidas\s05_cumulo.out.txt` (cúmulo contra cúmulo).
- `s06_tif_chillan.py` -> `salidas\s06_tif_chillan.out.txt` (TIF de Chillán en disco).

Los p de permutación son aleatorios (semilla fija en cada script); las cifras de recuento y de nulo exacto no.

## 10. Qué no miré

Las láminas «VRP», «logVRP» y «Dist»; el valor de NTI que codifica el gris; el eje de tiempo más fino que pasada a pasada; la secundaria de nuestros píxeles más allá de `anomaly_pixels`; MODIS por régimen del detector (21 de 22 son anteriores a la vía código MIROVA, así que no hay comparación); si el `effort` pedido llegó a esta sesión (SIN DATO).
