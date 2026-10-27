# Las 6 protegidas de Suomi NPP que el port de VIIRS 375 no publica: ¿son del cráter?

Auditoría de sólo lectura, S162. Rama `s162-v375-protegidas-snpp` (worktree `C:\vrp-trabajo\s162-v375-prot`), scripts y
salidas en esta carpeta. No se tocó nada fuera de ella; no se despachó ningún workflow; `gh` sólo para leer.

## En una pantalla

1. **Ninguna de las 6 es protegida de cráter.** Con la regla de #903 aplicada tal cual (código de `instrumento/clase-pasada`
   719e9c32e, sin modificar): 0 de 6, motivo `ocr_snpp_antes_del_hito` en las 6; la tabla de latest.php no trae ninguna
   (canal `tabla`: SIN PASADA en las 6). Controles: 30 de 30 protegidas de la tabla salen de cráter; la misma pasada movida a
   radio + 1 km sale `lejos_del_crater`.
2. **La evidencia independiente dice lo mismo en las 6 y por tres caminos.** (a) La imagen que el scraper guardó con la hora
   de cada fila lleva la cabecera «Last Update» de una pasada POSTERIOR (18 a 102 min después), así que la distancia y la
   clase de la fila son de otra pasada; en Láscar es el mismo archivo (md5 idéntico) que el de las 05:24. (b) El VRP de la fila
   sí es de su pasada, y coincide con lo que el port y K miden en píxeles a 8,7 a 29 km del cráter: 1,28 contra 1,25; 1,66
   contra 1,65; 2,18 contra 1,91; 2,28 contra 2,22; 2,53 contra 2,51; 1,79 contra 1,86 MW. (c) La serie de distancias de
   MIROVA (Dist.png de fechas posteriores, leída en RENDER) dibuja esas pasadas a 15, 24, 13, 22 a 23 y 9,5 km; en Láscar la
   serie no separa (SIN DATO) y decide la magnitud: el cráter de Láscar esa noche estuvo en 0,23 y 0,11 MW (tabla, 18 y 66 min
   después).
3. **Las 3 que K publica, las publica por el cráter, no por el objeto lejano**: cúmulo de 1 píxel a 0,26, 0,84 y 0,17 km del
   cráter con 0,016, 0,041 y 0,008 MW (K re-corrido en el lote de S159), todos bajo el umbral de 0,05 MW que MIROVA rotula
   NONE (regla D-9). El objeto que vale 1 a 2 MW queda en la magnitud de escena de K y no se publica (`far`). El port no ve ese
   píxel débil del cráter en esas 3 pasadas: ésa es la única diferencia real entre K y el port en las 6, y no es una protegida.
4. **Para la regla de adopción (PREREGISTRO_E §5.4 a)**: si las 6 cuentan como protegidas, el paquete falla por filas cuya
   distancia es de otra pasada y cuya magnitud está a 9 a 29 km del cráter. La decisión de cambiar la vara para ese estrato
   es de Nicolás; el estrato es grande: 128 de las 234 protegidas A de VIIRS 375 de toda la referencia son sólo OCR anteriores
   al 2026-10-09 (plataforma por resolver con el record de cada una).
5. **Lo que no se pudo mirar**: el repo de TIF no tiene ninguna captura con «Last Update» igual a la hora de estas 6 pasadas
   (el sondeo de 30 min llegó después de que MIROVA reemplazara la imagen; y desde el 2026-09-22 el archivo está congelado), así
   que la cabecera salió de las imágenes de Mirova-v1 y no del repo de TIF. VIIRS 750 y MODIS de esas noches no sirven de
   corroboración: sus records son del detector anterior (Test 1 integrado) o están vacíos.

## Encabezado

- Hora del servidor al cerrar: `Date: Sun, 25 Oct 2026 02:29:03 GMT` (cabecera HTTP de api.github.com).
- Commit medido: `17cc8c0df` (punta de `origin/claude/s162-viirs375-c1b864`; el material decía `c0215a97d`, que es ancestro y
  difiere sólo en `tasks/LOOP_VIIRS375.md` y un archivo más, 92 líneas, nada de lo que esta auditoría lee). Regla de #903:
  `origin/instrumento/clase-pasada` 719e9c32e, `scripts/clase_mirova.py` blob `2b59957f8` copiado verbatim a
  `_clase_mirova_903.py`; `scripts/referencia_mirova_unificada.py` es idéntico entre las dos ramas (`git diff` vacío).
- Referencia de MIROVA: `latest_consolidado.csv` (commit ba7b594ab, 2026-10-18 20:42 UTC) y
  `data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv` (commit 0c8848ff9) de la rama medida. Imágenes: Mirova-v1 en
  e09e684c8 y mirova-tif-archive en 7feffde74 (punta remota al bajar; md5 de cada archivo en `00_md5_png.txt`).
- Artefactos del port: lote de S159, run 39712862945, `D:\vrp-trabajo\temporales\s159_portes\run_39712862945` (grillas
  `grilla_<id>.npz` y `resultados_VIIRS375_*.json`; sha corto de cada grilla en `03_evidencia_por_pasada.json`).
- Modelo y esfuerzo: Claude Fable 5.1, esfuerzo por defecto de la sesión, sin verificador de contexto limpio (quien orquesta
  decide si lo pide).
- Qué NO miré: los gránulos crudos (no hay credenciales ni se debían usar); la imagen `Latest10NTI` celda por celda (el VRP
  por pasada se toma de la fila y de la celda de la imagen `_Latest.png`, que sí leí); el algoritmo del OCR de Mirova-v1 (no
  es de este repo); las imágenes de las pasadas vecinas más allá de las 12 bajadas; la geometría de las fuentes lejanas (qué
  son física o geográficamente: SOSPECHA de fuegos o actividad no volcánica, no medido).

## Qué se preguntó y cómo se midió

Para cada una de las 6 pasadas de la lista P1 de `evaluar.json` (run 40116289866, brazo C13|cercano; la misma lista en M14 y
en B2):

| canal | qué dice | instrumento |
|---|---|---|
| regla de #903 | `resumir_pasadas` + `es_protegida` + `protegida_de_crater`, canales `union` y `tabla`, plataforma del record | `02_regla_903.py` |
| tabla de latest.php | si trae la pasada; qué dice de las otras pasadas de la noche | `03_evidencia_por_pasada.py` (grep del consolidado) |
| distancia y canal de MIROVA | fila OCR: VRP, distancia, método del OCR, columnas `Distancia_aprox_*` de la serie | ídem |
| cabecera «Last Update» | imagen `_Latest.png` y `_Dist.png` guardadas con la hora de la fila, leídas en RENDER | bajadas por la API de Mirova-v1 (`00_md5_png.txt`) |
| serie de distancias | Dist.png posterior que usó el scraper para `Distancia_aprox`, leído en RENDER | bajadas por la API de mirova-tif-archive `data/png/` |
| otras pasadas de la noche (A109) | records de producción de hoy, todos los sensores, ±12 h; píxel más caliente de la escena | `01_records_produccion.py`, `01b` |
| K y el port en la pasada | K re-corrido del artefacto de S159; píxeles «fisica» del port con distancia al cráter; 10 brazos recalculados | `03_evidencia_por_pasada.py`, `03b` |

Las dos preguntas del instrumento van en la cabecera de cada script. Resumen: (1) si una de las 6 fuera del cráter, se vería
como `de_crater True` en 02, como un alertado del port a menos de 2,44 km (media caja C13) o del inner en 03/03b, o como una
cabecera igual a la hora de la fila; (2) los controles positivos (30 de 30 protegidas de la tabla de cráter en 02; 29 de 29
protegidas de la tabla con píxeles en C13 y `summit` por «cercano» en 03/03b) muestran que los instrumentos distinguen.

## Tabla por protegida

Distancias desde el cráter de `volcanoes.yaml` (`vent_lat/lon`) salvo donde se dice «centro»: MIROVA mide desde el centro de
su grilla (`mirova_center`), que en Tupungatito está a 4,86 km del cráter, por eso sus distancias de cráter en ese volcán
son 5,2 a 5,4 km. Inner: Tupungatito 7 km, Láscar 5, Isluga 5. Zenit de la pasada según el gránulo.

| id | pasada (SNPP) | MIROVA (fila sólo OCR) | cabecera de la imagen guardada | serie Dist.png | tabla esa noche (VIIRS 375) | K re-corrido | port (fisica) y 10 brazos | regla #903 | VEREDICTO |
|---|---|---|---|---|---|---|---|---|---|
| 279 | Tupungatito 2026-08-01 05:00, zen 58° | 1,25 MW a 5,41 km (del centro); «Estrella gris», conf media, v29.2 | 01-Aug-2026 06:06:02 (NOAA-21, +66 min) | 15,27 km, único (14 pareos); en RENDER, punto negro ~15 km el 01-Aug | 05:24 RUTINA; 06:06 0,04 MW a 5,21; 06:42 RUTINA | publica el cráter: 0,016 MW a 0,26 km; escena 0,907 MW, 2 px, t_max 297 K | 3 px a 14,3 a 15,0 km, 1,28 MW; cercano 14,3 km, far en 10 de 10 | no: `ocr_snpp_antes_del_hito` | **no de cráter** (fuente a ~15 km; el cráter estuvo en 0,04 a 0,05 MW toda la noche) |
| 285 | Láscar 2026-08-22 05:06, zen 59° | 1,65 MW a 1,22 km; «Estrella verde», conf alta | 22-Aug-2026 05:24:01 (NOAA-20, +18 min); **md5 idéntico** al archivo de las 05:24 | 0,81 solapado (26 pareos): SIN DATO | 05:24 0,23 MW a 1,19; 06:12 0,11 a 0,75; 06:48 RUTINA | no publica: far, 0,511 MW a 8,23 km; nada en el cráter | 5 px: 2 a 9,0 km y 3 a 29 km, 1,66 MW; cercano 9,0 km, far en 10 de 10 | no: `ocr_snpp_antes_del_hito` | **no de cráter** (magnitud igual a la suma lejana; la distancia es la de las 05:24; cráter en 0,23 MW 18 min después) |
| 288 | Isluga 2026-09-09 06:06, zen 21° | 1,91 MW a 0,81 km; «Grupo píxeles rojos Y=289, 35 px²», conf alta | 09-Sep-2026 06:30:01 (NOAA-20, +24 min) | 0,95 a 24,8 ambiguo (37 pareos); en RENDER, punto negro ~24 km y rojo ~1 km el 09-Sep | 05:30 0,15 MW a 0,84; 06:30 RUTINA | publica el cráter: 0,041 MW a 0,84 km; escena 1,742 MW, 3 px, t_max 305 K (píxel más caliente a 21,6 km) | 6 px: 4 a 21,2 a 21,7 km y 2 a 24,0 a 24,1 km, 2,18 MW; cercano 21,2 km, far en 10 de 10 | no: `ocr_snpp_antes_del_hito` | **no de cráter** (la magnitud protegida está a 21 a 24 km; el cráter da 0,04 MW en K y 0,15 MW 36 min antes) |
| 289 | Tupungatito 2026-09-14 06:18, zen 42° | 2,22 MW a 2,97 km; «Grupo píxeles rojos Y=273, 73 px²», conf alta | 14-Sep-2026 06:36:01 (NOAA-20, +18 min) | 13,11 km, único (21 pareos); en RENDER, punto negro ~13 km el 14-Sep | 05:42 0,13 MW a 5,21; 06:36 RUTINA (OCR: 05:00 0,10 MW) | publica el cráter: 0,008 MW a 0,17 km; escena 2,292 MW, 2 px, t_max 319 K (píxel más caliente a 13,1 km del centro) | 2 px a 12,5 a 12,6 km (uno a 312 K), 2,28 MW; cercano 12,5 km, far en 10 de 10 | no: `ocr_snpp_antes_del_hito` | **no de cráter** (fuente a ~13 km con 312 K; la serie de MIROVA la ubica a 13,11 km) |
| 294 | Tupungatito 2026-09-28 05:18, zen 49° | 2,51 MW a 5,27 km; «Estrella verde Y=256», conf alta | 28-Sep-2026 05:36:01 (NOAA-20, +18 min) | 5,27 a 22,57 ambiguo (17 pareos); en RENDER, puntos negros ~22 a 23 km el 27/28-Sep | 05:36 0,09 MW a 5,21; 06:18 y 06:54 RUTINA | no publica: far, 0,15 MW a 21,6 km; descartado 0,89 MW a 25,5 km; nada en el cráter | 6 px a 22,3 a 23,0 km, 2,53 MW; cercano 22,3 km, far en 10 de 10 | no: `ocr_snpp_antes_del_hito` | **no de cráter** (fuente a ~22,5 km; NOAA-20 la ve 18 min después a 21,9 km con 0,20 MW, otro gránulo) |
| 295 | Tupungatito 2026-09-29 04:54, zen 62° | 1,86 MW a 5,68 km; «Grupo píxeles rojos Y=253, 3 px²», conf alta | 29-Sep-2026 06:36:00 (SNPP siguiente, +102 min) | 5,41 a 9,59 ambiguo (17 pareos); en RENDER, puntos negros ~9,5 y ~22,5 km el 29-Sep | 05:18 0,04 MW a 5,41; 06:00 y 06:36 RUTINA | no publica: far, 1,112 MW a 9,40 km, 1 px, t_max 302 K; nada en el cráter | 4 px a 8,7 a 9,2 km, 1,79 MW (SENS 5 px, 1,83); cercano 8,7 km, far en 10 de 10 | no: `ocr_snpp_antes_del_hito` | **no de cráter** (fuente a ~9 km, 9,3 km del centro; el cráter en 0,02 a 0,04 MW a las 05:18 y 06:00) |

Lectura de la columna «veredicto»: la regla de #903 decide «no» por el hito en las 6; la evidencia independiente la confirma
en las 6 sin apoyarse en el hito. En ninguna hay SIN DATO en el veredicto; los SIN DATO están en canales sueltos (serie de
Láscar; repo de TIF en las 6; VIIRS 750 y MODIS como corroboración).

## Hallazgos (por gravedad)

### H1. Las 6 «protegidas perdidas» no son del cráter: la distancia es de otra pasada y la magnitud está a 9 a 29 km

- **ARCHIVO:LÍNEA / SCRIPT:SALIDA**: `02_regla_903_salida.txt` (0 de 6 de cráter); `03_evidencia_por_pasada_salida.txt`
  (cabeceras, píxeles del port, K); `03b_regla_distancia_port_salida.txt` (clase `far` en las 6 por «cercano» y por
  «centroide»); imágenes `*_Latest.png` y `*_Dist.png` en `00_md5_png.txt`.
- **QUÉ PASA**. Físico primero: en cada una de las seis noches el cráter estuvo tibio y estable, entre 0,02 y 0,23 MW en las
  pasadas de 18 a 66 min antes o después (tabla de MIROVA y producción coinciden), y una fuente caliente separada (píxeles de
  280 a 312 K en el infrarrojo medio) apareció a 9 a 29 km del cráter, dentro de la ventana de 50 km de MIROVA. MIROVA suma
  el VRP de todos los alertados de la ventana (lectura que ya hizo P-5 de S159 sobre `VRP.m`), así que su VRP de esa pasada
  es la fuente lejana. El scraper, al correr, bajó una imagen que MIROVA ya había reemplazado por la de la pasada siguiente
  (cabecera «Last Update» posterior en 6 de 6; en Láscar el mismo archivo que la fila de las 05:24) y tomó de ahí la
  distancia y la clase; el VRP sí lo leyó de la celda de su hora (visible en la imagen `_Latest.png`, columna de la pasada).
  Resultado: una fila con VRP real de 1,25 a 2,51 MW y distancia de cráter prestada. El código: la lectura A define
  protegida como «alerta del scraper con VRP de 1 MW o más» (`_clase_mirova_903.py:20-21, 279-287`) y no mira de dónde
  salió la distancia; por eso entran al veto P1. La regla `protegida_de_crater` (l. 290-319) las saca por el hito
  `HITO_OCR_SNPP = "2026-10-09"` (l. 198) cuando la plataforma del record es Suomi NPP, y los gránulos lo confirman
  (`VNP02IMG` en las 6).
- **CÓMO SE VE EN EL DASHBOARD**: no se ve. Pesa sólo en la vara de adopción del paquete (P1).
- **CÓMO REPRODUCIRLO**: `python -I 02_regla_903.py`; `python -I 03_evidencia_por_pasada.py` (lento, ~3 min, lee el
  consolidado seis veces); `python -I 03b_regla_distancia_port.py`; abrir las imágenes listadas en `00_md5_png.txt`.
- **CONFIANZA**: CONFIRMADO (cabecera y md5; magnitudes; regla). SOSPECHA sólo en qué son las fuentes lejanas.
- **GRAVEDAD**: 4 para la decisión (si se cuentan como protegidas, vetan el paquete por filas que no describen el cráter).

### H2. Las 3 que K publica son el cráter a 0,008 a 0,041 MW; el port no ve ese píxel en esas 3 pasadas

- **SCRIPT:SALIDA**: `03_evidencia_por_pasada_salida.txt` (K re-corrido de 279, 288, 289: `summit`, 1 píxel a 0,26, 0,84 y
  0,17 km, 0,016, 0,041 y 0,008 MW; port sin alertado bajo 12,5 km); `01b_hotspots_otras_pasadas_salida.txt`.
- **QUÉ PASA**. K publica el cúmulo del cráter y deja la fuente lejana en la magnitud de escena sin publicar (`geo_class`
  far). El port, en el mismo gránulo, no alerta ningún píxel en el cráter: en Tupungatito 08-01 (zen 58°) y 09-14 (zen 42°) y
  en Isluga 09-09 (zen 21°, casi nadir, así que no es sólo el borde del barrido). Las pasadas vecinas de NOAA-20 y NOAA-21 ven
  el cráter en 0,04 a 0,11 MW (producción) y 0,04 a 0,15 MW (tabla). Es la misma clase de diferencia que B2 ya midió como
  «apaga el 72,5 % de neg_pub»: el port calla puntos débiles que K publica. Los tres están bajo 0,05 MW, el valor que el
  banner de MIROVA rotula NONE (D-9, `_clase_mirova_903.py:87-110`), así que no son alertas de MIROVA que se pierdan.
- **CÓMO SE VE EN EL DASHBOARD**: si el paquete reemplazara a K, esas tres noches el operador no vería un punto de 0,01 a
  0,04 MW en el cráter de Tupungatito o Isluga; sí lo vería en las otras pasadas de la misma noche.
- **CÓMO REPRODUCIRLO**: ídem H1.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 2.

### H3. Lo que el tablero muestra HOY en 4 de las 6 no es K: son records del detector anterior

- **SCRIPT:SALIDA**: `01_records_produccion_salida.txt` y `01b_hotspots_otras_pasadas_salida.txt` contra el bloque «K
  re-corrido» de `03_evidencia_por_pasada_salida.txt`; `git log --since=2026-10-10 -- data/mirova_equivalent/{Tupungatito,
  Lascar,Isluga}.json` (último backfill: «data(backfill): ... 2026-09-18..2026-10-18 (S120)»).
- **QUÉ PASA**. Los records de `data/mirova_equivalent/` de las pasadas del 1 de agosto, 22 de agosto, 9 y 14 de septiembre
  llevan `triggered_test1 True`, `n_test1_pixels` 50 a 101 y `final_hotspot_source test1_roi` (el Test 1 integrado, apagado en
  K desde S153), y sus cúmulos difieren del K re-corrido: Tupungatito 08-01 0,05 MW contra 0,016; Láscar 08-22 **summit 0,034
  MW a 0,73 km** contra **far 0,511 MW a 8,23 km y nada publicado**; Isluga 09-09 0,078 contra 0,041; Tupungatito 09-14 0,04
  MW a 2,93 km contra 0,008 a 0,17 km. Los del 28 y 29 de septiembre coinciden con K exactamente (están dentro del backfill
  2026-09-18 a 10-18). O sea que el tablero muestra hoy para Láscar 2026-08-22 05:06 una detección en el cráter que K no
  produce. Es A104/A85 (dos detectores a los dos lados del 2026-09-18); no cambia nada de esta auditoría, porque «K publica»
  se midió con K re-corrido, pero cambia lo que un operador ve si abre esas fechas.
- **CÓMO SE VE EN EL DASHBOARD**: Láscar 2026-08-22 05:06 aparece como detección summit de 0,034 MW; con K no aparecería.
- **CÓMO REPRODUCIRLO**: `python -I 01_records_produccion.py` y comparar con el bloque K de 03.
- **CONFIANZA**: CONFIRMADO en los 6 records; SOSPECHA de que la frontera sea exactamente el 2026-09-18 (no la busqué en el
  tablero; sale del mensaje del commit de backfill).
- **GRAVEDAD**: 2.

### H4. El OCR rotula «geometría medida, confianza alta» en filas cuya imagen es de otra pasada

- **SCRIPT:SALIDA**: `03_evidencia_por_pasada_salida.txt` (campo «método»): 5 de las 6 filas traen `Confianza_Validacion
  alta` y «geometría medida»; la de 279 trae «conf media» y «detección débil sub-umbral MIROVA» con 1,25 MW.
- **QUÉ PASA**. La distancia que el OCR midió (estrella o grupo de píxeles rojos en Dist.png) es geométricamente correcta
  sobre la imagen, pero la imagen no es de la pasada de la fila (cabecera posterior en 6 de 6). El propio scraper lo
  contradice después en sus columnas `Distancia_aprox_*` (13,11 km único para 289 contra 2,97 de la fila; 15,27 único para
  279 contra 5,41). La versión V31.1 del scraper (filas `ALERTA_SIN_GEOMETRIA_OCR`, ejemplo en la primera fila del CSV)
  arregló esto hacia adelante; estas 6 son anteriores y no se reprocesaron. Es del repo Mirova-v1, no de éste; acá sólo
  importa para no leer «conf alta» como «distancia de su pasada».
- **CÓMO SE VE EN EL DASHBOARD**: no se ve.
- **CONFIANZA**: CONFIRMADO (filas y cabeceras). **GRAVEDAD**: 1 para este repo.

### H5. El repo de TIF no tiene ninguna de las 6 pasadas; la cabecera tuvo que salir de Mirova-v1

- **SCRIPT:SALIDA**: `index.csv` de mirova-tif-archive (21.874 filas; 7.837 de VIIRS375, 6.550 con `acquisition_utc`),
  bajado por la API: para Tupungatito el 2026-08-01 hay adquisiciones 05:24:01, 06:06:02 y 06:42:00 (ninguna 05:00); para
  Isluga el 2026-09-09, 05:30:02 y 06:30:01 (ninguna 06:06); para Tupungatito el 2026-09-14, 05:42:02 y 06:36:01 (ninguna
  06:18); Láscar no tiene filas VIIRS375 el 2026-08-22 (sí el 18 al 21 y el 27); Tupungatito no tiene nada después del
  2026-09-22 (últimas filas del índice: 2026-09-22T11:01 UTC).
- **QUÉ PASA**. MIROVA escribe el TIF 3 a 4 h después de la adquisición y lo reemplaza con la pasada siguiente; el sondeo
  cada 30 min capturó la siguiente. Y el archivo está congelado desde el 2026-09-22 (memoria `reference_mirova_tif_congelados_
  20260922`). SIN DATO en ese canal para las 6; se cubrió con las imágenes `_Latest.png` y `_Dist.png` de Mirova-v1, que
  llevan la misma cabecera.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 1 (el canal alternativo bastó).

### H6. El estrato «sólo OCR de Suomi NPP antes del hito» es más de la mitad de las protegidas A de VIIRS 375

- **SCRIPT:SALIDA**: `02_regla_903_salida.txt`, última línea: protegidas A de VIIRS 375 en el canal `union` de toda la
  referencia (2026-01-10 al 2026-10-18): **234**; sólo OCR anteriores al 2026-10-09: **128**; de la tabla: 104 (la plataforma
  de las 128 hay que resolverla con el record de cada una; acá no se hizo).
- **QUÉ PASA**. La vara P1 del paquete se construye con la lectura A sobre la unión; si el estrato de 128 contiene más filas
  como estas 6, el veto puede dispararse por filas que no describen el cráter. Lo que esta auditoría NO dice: que las 128
  sean todas así. Sólo las 6 están medidas. Es el riesgo que PREREGISTRO_E §5.4 ya nombra.
- **CONFIANZA**: CONFIRMADO el conteo; SOSPECHA su composición. **GRAVEDAD**: 2 (para la decisión de PD4).

### H7. El material citaba un commit que no es la punta de la rama

- `c0215a97d` es ancestro de `17cc8c0df`; la diferencia son 2 archivos y 92 líneas (`tasks/LOOP_VIIRS375.md` y uno más),
  ninguno de los que se leen acá. CONFIRMADO. GRAVEDAD 1.

## VERIFICADO LIMPIO

- La regla de #903 hace lo que dice en las 6 y en los controles: `python -I 02_regla_903.py` da `de cráter False
  ('ocr_snpp_antes_del_hito',)` en las 6 con plataforma `VIIRS_SNPP`, `plataforma_desconocida_antes_del_hito` sin plataforma;
  30 de 30 protegidas de la tabla con distancia dentro del radio salen de cráter; la sintética a radio + 1 km sale
  `lejos_del_crater`; la sintética sólo OCR de Suomi NPP del día del hito (2026-10-09) y la de NOAA-20 antes del hito salen de
  cráter. El canal `tabla` no trae ninguna de las 6 (SIN PASADA en las 6).
- El recálculo de los 10 brazos sobre las grillas guardadas reproduce al runner en las 6 (npix y MW iguales a `fisica`) y da
  píxeles en C13 en 29 de 29 protegidas de la tabla del lote; la regla «cercano» da `summit` en esas 29 de 29 y `far` en las
  6 (`03b_regla_distancia_port_salida.txt`).
- Los gránulos de las 6 son `VNP02IMG` (Suomi NPP) y el sensor del record es `VIIRS_SNPP` (`03_evidencia_por_pasada.json`).
- El VRP de cada fila OCR está en la celda de su hora en la imagen `_Latest.png` (leído en RENDER en las 6: 1,25; 1,65; 1,91;
  2,22; 2,51; 1,86), así que la fila no inventa la magnitud: la ubica mal.
- Para 294, otro gránulo (NOAA-20, 05:36) ve la misma fuente lejana a 21,9 km con 0,20 MW: comprobación independiente del
  mismo gránulo (A109) de que la fuente existe y está lejos.
- Disco al cerrar: C: 34,4 GB y D: 9,5 GB libres (parada en 3 GB, no se tocó).

## SIN DATO

- Repo de TIF: ninguna captura con «Last Update» de las 6 pasadas (H5).
- Serie de distancias para Láscar 2026-08-22 (pareo `solapado`): no separa la pasada de las 05:06 de la de las 05:24.
- VIIRS 750 y MODIS de esas noches como corroboración: los records de producción de agosto y del 14 de septiembre son del
  detector anterior (MODIS con 85 a 315 píxeles y tope 5,0 MW `far`; VIIRS 750 del 06:06 y 06:18 con `test1_roi` y 2,8 y
  2,0 MW de escena) y los de 750 de las pasadas exactas de las 6 dan 0 MW. No prueban ni refutan un cráter de 1 MW.
- Qué son las fuentes lejanas (fuegos, actividad humana, otro volcán): no se miró ninguna imagen de alta resolución.
- La fuente de 295 (9 km, 1,1 MW en 1 píxel a zen 62°) no la ve NOAA-20 24 min después (que ve otra a 24,6 km): puede ser
  transitoria o un artefacto del borde del barrido; no decide el veredicto porque el cráter en esa pasada está vacío en K y en
  el port, y en 0,02 a 0,04 MW en las dos pasadas siguientes.
- Composición del estrato de 128 protegidas sólo OCR anteriores al hito (H6).

## Archivos de esta carpeta

`00_md5_png.txt` (md5 de las 29 imágenes bajadas), `01_records_produccion.py/.json/_salida.txt`,
`01b_hotspots_otras_pasadas_salida.txt`, `02_regla_903.py/.json/_salida.txt`, `03_evidencia_por_pasada.py/.json/_salida.txt`,
`03b_regla_distancia_port.py/_salida.txt`, `_clase_mirova_903.py` (copia verbatim), este informe. Imágenes bajadas (no se
commitean): `C:\vrp-trabajo\temporales\s162_v375_prot_png\` y `C:\vrp-trabajo\temporales\s162_v375_prot_tif\`.
