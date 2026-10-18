# Segundo lector: cuatro alertas de MIROVA que K no publica (regla de adopción de K, §3 y §4.2)

Tarea de solo lectura, 2026-10-18. Ningún repo editado ni commiteado. Todo lo de aquí sale de archivos en
`C:\Users\nmend\AppData\Local\Temp\claude\lector2\`. Leí `CABECERAS_SNPP.md` del primer lector, pero bajé las imágenes
de nuevo y repetí cada lectura por mi cuenta antes de comparar.

## 0. En una línea

**Las cuatro son LEJANAS.** En las cuatro, la distancia propia de la pasada queda muy por fuera del límite del scraper
(Lastarria 3 km, Tupungatito 7 km desde su punto de referencia), así que con su distancia propia el scraper habría
escrito FALSO_POSITIVO_OCR, no ALERTA. Ninguna cuenta como pérdida neta. En tres de las cuatro, la miniatura propia de
la pasada pone el punto caliente de MIROVA en el mismo lugar (distancia y rumbo) que el cúmulo lejano de K.

## 1. Fuentes y método

- Imágenes: bajadas de a una por la API de GitHub desde `MendozaVolcanic/Mirova-v1`, rama `main` al 2026-10-18,
  carpetas `monitoreo_satelital/imagenes_satelitales/<Volcán>/<fecha>/` (48 archivos, en `img\`). Cabeceras leídas en
  `crop\headers_all.png` (montaje de las 48).
- Fila del OCR: `experiments/_s151_prereg_fk_11/_congelado_v1` y `_congelado_v2` (`registro_vrp_ocr.csv`); columna
  `Distancia_aprox_*` del CSV vivo de Mirova-v1 (commit `4ce5be54`, 2026-10-17 23:02 UTC), copia en `ocr_vivo.csv`.
- Tabla de MIROVA de esas noches: `_congelado_v1/_congelado_v2/registro_vrp_consolidado.csv`.
- Cúmulos de C0 y K: uniones de V1 y V2 (`v1_38639658446\union_2766`, `v2a_38648773684\union_2766`,
  `v2b_39033530622\union`), distancia y rumbo calculados con `pos.py` desde el cráter y desde `mirova_center`.
- Clasificador del scraper: corrí la función real `validar_con_estrella_verde` de `ocr_utils.py` de Mirova-v1 (main)
  sobre las imágenes (`run_scraper.py`, código en `code\`). El scraper usa 7,4 px/km con el eje 0 en y = 295
  (`volcanes.py:19`); mi calibración por las líneas de grilla da lo mismo (`star.py`).
- Miniaturas del panel «Latest Images»: cada celda es la imagen PROPIA de su pasada (lleva su hora, VRP, cenit y
  azimut). Localicé el punto blanco y medí su desplazamiento desde el centro de la miniatura (`thumbs.py` y recortes
  ampliados en `crop\`). Escala supuesta: 149 px ≈ 50 km, o sea 0,335 km/px, tomada del LatLonBox de
  `Pruebas/mirova_real/Lascar_VIIRS375_Last_GE.kmz` (50,5 × 49,4 km), con el centro en `mirova_center`. La escala la
  valida el caso 3, donde la estrella de la imagen propia (20,0 km) y la miniatura (19,7 km) dan lo mismo.

Hallazgo de mecanismo, el mismo en las cuatro: la imagen que el scraper guardó con la hora de la pasada es de otra
pasada. En los tres casos de Suomi NPP (1, 2 y 4) la pasada propia fue procesada por MIROVA **después** que la pasada
siguiente, y su imagen no quedó archivada; en el caso 3 (NOAA-20) la imagen propia sí quedó, pero con el nombre de
otra hora. El punto de la pasada propia aparece en la serie «Last Month»
sólo en versiones posteriores de la imagen; eso es lo que permite asignar cada punto a su pasada por eliminación.

## 2. Tabla

Distancias de MIROVA en km desde su punto de referencia. «Imagen propia» = imagen cuya cabecera «Last Update» es la
hora de la pasada.

| caso | VRP fila (propio, celda Latest) | cabecera de la imagen guardada con esa hora | imagen propia | distancia propia de MIROVA | clase del scraper con esa distancia | miniatura propia: punto caliente | cúmulo de K | veredicto | certeza |
|---|---|---|---|---|---|---|---|---|---|
| 1. Tupungatito V375 2026-09-28 05:18 (SNPP) | 2,51 (sí, celda 05:18:00) | 28-Sep 05:36:01 (los 4 archivos) | no archivada | **22,5 km** (serie; `Distancia_aprox_max` 22,57) | FALSO_POSITIVO_OCR (límite 7 km) | dos puntos: 24,1 km rumbo 25° y 22,5 km rumbo 205°; nada visible en la zona del cráter | far, 23,9 km rumbo 26° desde la referencia, 0,15 MW | **LEJANO** | alta |
| 2. Tupungatito V375 2026-09-29 04:54 (SNPP) | 1,86 (sí, celda 04:54:00) | 29-Sep 06:36:00 | no archivada | **9,6 km** (serie: 9,57; `Distancia_aprox_max` 9,59) | FALSO_POSITIVO_OCR (límite 7 km) | 9,3 km rumbo 44°; además un punto tenue a ~5,4 km rumbo 330° (zona del cráter) | far, 9,29 km rumbo 46°, 1,11 MW | **LEJANO** | alta en la distancia; ver nota |
| 3. Lastarria V375 2026-04-18 04:42 (NOAA-20) | 1,29 (sí, celda 04:42:01) | 18-Apr 06:24:01 | **sí, guardada bajo el nombre `05-36-02_*`** (cabecera 04:42:01, Zen 67°, Azi 106°, «LOW») | **20,0 km** (estrella verde de la imagen propia, y = 146-147) | **FALSO_POSITIVO_OCR**, «Estrella verde en Y=147 -> 20.00 km», salida literal del clasificador del scraper | 19,7 km rumbo 99° | far, 19,73 km rumbo 99°, 0,53 MW | **LEJANO** | muy alta |
| 4. Lastarria V375 2026-05-02 05:06 (SNPP) | 2,36 (sí, celda 05:06:00) | 02-May 06:42:00 (md5 de `05-06-00_*` = `06-42-00_*`) | no archivada | **19,3 km** (serie; `Distancia_aprox` 19,36 «unico») | FALSO_POSITIVO_OCR (límite 3 km) | 19,4 km rumbo 203° | far, 19,47 km rumbo 201°, 1,11 MW | **LEJANO** | alta |

### Cómo se asignó cada punto de la serie (casos 1, 2 y 4)

- **Caso 1.** Pasadas con VRP del 28-sep (panel Latest de las 06:54): 05:18 (2,51) y 05:36 (0,09); 04:42, 06:18,
  06:54 y todas las diurnas, NaN. En la versión de las 05:36 del Dist, la columna del 28-sep tiene sólo la estrella a
  5,27 km (la de 05:36; la tabla la da a 5,21). En la versión de las 05:18 del 29-sep ya aparece un cuadrado gris a
  22,5 km en la columna del 28-sep, junto al círculo de 5,2. Entre una versión y otra, la única pasada con VRP que
  entró fue la de 05:18. → 22,5 km es la de 05:18.
- **Caso 2.** Pasadas con VRP del 29-sep (panel Latest de las 06:36): 04:54 (1,86) y 05:18 (0,04); 06:00 y 06:36,
  NaN; del 28-sep 17:36 a 19:36, NaN. En la versión de las 05:18 la columna del 29-sep tiene sólo la estrella gris a
  5,54 km (05:18). En la de las 06:36 aparecen un cuadrado a 9,57 km y un círculo a 5,36. → 9,6 km es la de 04:54.
- **Caso 4.** En la versión de las 05:24 del panel Latest no existe todavía la celda 05:06; en la de las 06:42 sí, con
  2,36 MW. En el Dist de las 06:12 la columna del 2-may no tiene ningún punto lejano; en el de las 06:42 aparece un
  cuadrado a ~19,3 km y la estrella a 1,5 (la de 06:42; tabla 1,55). La pasada de 05:24 es NaN. → 19,3 km es la de
  05:06. Coincide con `Distancia_aprox` 19,36 «unico» (84 pareos), que el scraper sacó por su cuenta de una imagen
  del 27-may.

## 3. Nota del caso 2 (lo único que no cierra del todo)

En la miniatura propia de 04:54 hay, además del punto brillante a 9,3 km, un punto tenue en la zona del cráter
(~5,4 km rumbo 330° desde la referencia; brillo 125 contra mediana local 56), en el mismo lugar donde MIROVA ubica
la pasada de 05:18 (5,41 km) y donde C0 publicaba su cúmulo (5,17 km rumbo 329°, 0,059 MW). La miniatura es una
imagen en escala de grises reestirada por pasada y **no** muestra qué píxeles alertó MIROVA; la pasada de 05:18,
que MIROVA sí alertó en el cráter, tiene un contraste parecido (93 contra 44). Así que es posible que el 1,86 MW de
MIROVA incluya algo del cráter, **SIN VERIFICAR**. Pero MIROVA rotula la pasada con una sola distancia, 9,6 km, y con
esa distancia el scraper la clasifica FALSO_POSITIVO_OCR. En el marco de la lectura A que fija la regla (¿la habría
clasificado ALERTA con su distancia propia?), la respuesta es no. Por eso el veredicto es LEJANO y no INDETERMINADO;
si Nicolás quiere el marco «¿había calor en el cráter?», este caso sería el candidato a mirarlo.

En los casos 3 y 4 el brillo de la zona del cráter en la miniatura no discrimina (en el 2-may la pasada NaN de 05:24
lo tiene igual de alto que las alertas), así que no lo uso.

## 4. Contra el primer lector

- **Coincido** en las dos de Tupungatito: imagen de otra pasada, distancia propia ~22,6 y ~9,6 km, no serían
  protegidas A.
- **Agrego** lo que él dejó SIN VERIFICAR: la posición. Sí se puede leer en las miniaturas del panel Latest (el punto
  blanco aislado es legible ampliando a 4×). En el caso 2 el punto de MIROVA y el cúmulo de K coinciden en distancia y
  rumbo (9,3 km 44° contra 9,29 km 46°). En el caso 1 hay dos puntos lejanos: uno coincide con K (24,1 km 25° contra
  23,9 km 26°) y el otro (22,5 km 205°) coincide mejor con el número que MIROVA puso en su serie. Los dos lejanos.
- **Agrego** el mecanismo de asignación por versiones sucesivas de la imagen, que resuelve la ambigüedad que el primer
  lector resolvía contando puntos por columna.
- Los dos casos de Lastarria no los revisó el primer lector. El caso 3 es el más firme de los cuatro: la imagen propia
  existe (guardada con el nombre de otra hora) y el clasificador del propio scraper devuelve FALSO_POSITIVO_OCR a
  20,00 km.

## 5. Límites

- Imágenes de la rama `main` de Mirova-v1 al 2026-10-18, no de un commit fijo.
- Escala de la miniatura supuesta (KMZ de Láscar) y validada en un solo caso (el 3); un error de escala del 20 %
  no cambia ningún veredicto (el punto más cercano está a 9,3 km contra un límite de 7).
- Lecturas de la serie con la calibración del scraper; los cuadrados grises los leí en recortes ampliados, con un
  error de ±0,2 km. Sólo el caso 3 pasó por el clasificador real del scraper, porque es el único con imagen propia.
- No corrí el algoritmo `Distancia_aprox` de Mirova-v1; uso su salida publicada como contraste independiente.
- `TOLERANCIA_KM` del scraper es 0,15 km (`ocr_utils.py:1016`); irrelevante con estos márgenes.
