# Verificación del informe «Las 6 protegidas de Suomi NPP que el port de VIIRS 375 no publica»

Verificador con contexto limpio, S162. Rama `s162-verif-protegidas-snpp` (worktree `C:\vrp-trabajo\s162-verif-snpp`).
Scripts y salidas en `C:\vrp-trabajo\s162-verif-snpp\experiments\_s162_v375\protegidas_snpp\verificador\`. Los caminos
de falla se escribieron antes de leer el informe: `caminos.md` (con sha256 de cada artefacto y hora del servidor).

## En una pantalla

1. Afirmación 1 CONFIRMADA, pero es tautológica: la regla de #903 (copia idéntica salvo CRLF) saca las 6 SÓLO por la fecha; sin el hito las 6 serían de cráter (distancias 0,81 a 5,68 km, todas dentro del inner). La tabla congelada y la remota de hoy no traen ninguna.
2. Afirmación 2 CONFIRMADA: leí las 6 cabeceras, «Last Update» posterior en 6 de 6 (+66, +18, +24, +18, +18, +102 min); en Láscar los 4 archivos tienen el mismo blob git que los de las 05:24. La distancia de la fila coincide con la de otra pasada en 5 de 6; la de Tupungatito 09-14 (2,97 km) no corresponde a ninguna.
3. Afirmación 3 CONFIRMADA EN PARTE: el VRP es de su pasada (celda y cenit calzan) y el port calza con él sin que sea azar (nulo p < 1/2000), pero las distancias «al cráter» del informe se midieron al centro de MIROVA (al cráter: 8,2 a 28,9 km), y la magnitud de K no calza en 4 de 6. La «comprobación independiente» de NOAA-20 en 294 mira OTRO objeto, a 34,8 km.
4. Afirmación 4 CONFIRMADA con el predicado del tablero ejecutado en node: K publica 279, 288 y 289 por un píxel a 0,26, 0,83 y 0,17 km del cráter, con 0,016, 0,041 y 0,008 MW; el port no tiene ningún píxel a menos de 13 km del cráter en esas pasadas.
5. Afirmación 5: el conteo 128 de 234 está CONFIRMADO (crudo y agrupado, igual), pero «de ese tipo» NO: sólo 48 resuelven a Suomi NPP con nuestro record, 9 son NOAA, 71 no tienen record; 88 también caen antes del hito de distancia. Iguales a las 6 en el sentido estricto: 11.

## Encabezado

- Hora del servidor: inicio `Mon, 26 Oct 2026 01:45:10 GMT`, cierre de las mediciones `Mon, 26 Oct 2026 01:56:00 GMT` (cabecera HTTP de api.github.com).
- Commit medido: `014a1ab61` (`origin/s162-v375-protegidas-snpp`). El informe declara `17cc8c0df`; es ancestro y la diferencia
  fuera de la carpeta del informe es vacía (`git diff --stat 17cc8c0df 014a1ab61 -- . ':!experiments/_s162_v375/protegidas_snpp'`).
  Regla: `origin/instrumento/clase-pasada` 719e9c32e = cabeza del PR #903 (`gh pr view 903`: OPEN, headRefOid 719e9c32e).
- Modelo y esfuerzo: Claude Opus 5.5, esfuerzo de razonamiento bajo. Sin subagentes.
- Qué NO miré: si el «K re-corrido» del lote de S159 corrió exactamente con el perfil de producción de K (sólo vi que los 6
  records traen `triggered_test1 False`); el hallazgo H3 del informe (records viejos del tablero); el algoritmo del OCR de
  Mirova-v1; las imágenes `_Dist.png` de 279, 285 y 294 (sí sus `_Latest.png` y, en Láscar, los blobs); qué son físicamente
  las fuentes lejanas; la columna `Nivel_Anomalia_MIROVA` del CSV de las 6 filas; los gránulos crudos.

## Veredictos por afirmación

Cada medición lleva en su script las dos preguntas del instrumento. Ventana de la referencia en todo lo que sigue: copia
congelada de la rama medida, 2026-01-10 19:06 a 2026-10-18 05:42 UTC (44.521 filas; `v02_regla_y_estrato_salida.txt`).

### Afirmación 1: 0 de 6 de cráter con #903, motivo `ocr_snpp_antes_del_hito`; la tabla no trae ninguna

**CONFIRMADO.** Gravedad del matiz: 2.

- Copia de la regla: `diff --strip-trailing-cr <(git show 719e9c32e:scripts/clase_mirova.py) _clase_mirova_903.py` vacío; la
  única diferencia es el fin de línea (CRLF en el checkout de Windows, LF en el índice: `git ls-files --eol` da `i/lf w/crlf`).
  Además no usé la copia: importé el módulo de una extracción fresca de 719e9c32e (`git archive`), `v02_regla_y_estrato.py`.
- Resultado propio: las 6 salen `(False, ('ocr_snpp_antes_del_hito',))`, con la plataforma resuelta desde NUESTRO record a
  ≤ 3 min (`VIIRS_SNPP` en las 6, no copiada del informe). Canal `tabla`: SIN PASADA en las 6. Control positivo: 30 de 30
  protegidas de la tabla dentro del radio salen de cráter; las 104 de la tabla, 104 de cráter.
- Tabla, por fuera del agrupador (`v01_filas_crudas_salida.txt`): 0 filas de tabla a ≤ 10 min en la copia del snapshot y en
  `latest_consolidado.csv`; y en la tabla REMOTA de Mirova-v1 de hoy (commit 736cdca69, 2026-10-26 01:51 UTC, filas hasta el
  2026-10-25 19:30), tampoco (`v06_conteo_crudo_salida.txt`).
- **Matiz (VP162-04)**: el «0 de 6» no es evidencia física. La regla excluye por construcción toda fila sólo OCR de Suomi NPP
  anterior al 2026-10-09 (`clase_mirova.py` de 719e9c32e, función `protegida_de_crater`, rama `if p.solo_ocr ... dia <
  HITO_OCR_SNPP`). La misma corrida con plataforma NOAA-20 da `(True, ())` en las 6: sus distancias (5,41; 1,22; 0,81; 2,97;
  5,27; 5,68 km) caen todas dentro del inner. Lo que sostiene que no son de cráter son las afirmaciones 2 a 4, no ésta.

### Afirmación 2: la cabecera «Last Update» de la imagen guardada es de una pasada posterior (18 a 102 min)

**CONFIRMADO.** Gravedad del matiz: 1.

- Bajé las imágenes por la API de Mirova-v1 (archivo suelto) a `C:\vrp-trabajo\temporales\s162_verif_snpp_png\`; md5 iguales a
  los de `00_md5_png.txt` del informe en los 8 `_Latest.png` y 3 `_Dist.png` que bajé. Las leí renderizadas:

  | id | pasada | cabecera que leí | diferencia | celda de la pasada en la imagen |
  |---|---|---|---|---|
  | 279 | Tupungatito 08-01 05:00 | 01-Aug-2026 06:06:02 | +66 min | VRP 1,25 MW, ZEN 58° |
  | 285 | Láscar 08-22 05:06 | 22-Aug-2026 05:24:01 | +18 min | VRP 1,65 MW, ZEN 59° |
  | 288 | Isluga 09-09 06:06 | 09-Sep-2026 06:30:01 | +24 min | VRP 1,91 MW, ZEN 20° |
  | 289 | Tupungatito 09-14 06:18 | 14-Sep-2026 06:36:01 | +18 min | VRP 2,22 MW, ZEN 42° |
  | 294 | Tupungatito 09-28 05:18 | 28-Sep-2026 05:36:01 | +18 min | VRP 2,51 MW, ZEN 48° |
  | 295 | Tupungatito 09-29 04:54 | 29-Sep-2026 06:36:00 | +102 min | VRP 1,86 MW, ZEN 62° |

  Las 6 cabeceras nombran el volcán correcto. En las `_Dist.png` de 288, 289 y 295 la cabecera es la misma que la del `_Latest`.
- md5 de Láscar: no es coincidencia. La API da el MISMO blob git para los cuatro archivos (`Dist`, `Latest`, `VRP`, `logVRP`)
  de las 05:06 y de las 05:24 (`a0c40ba9...` en `Latest`, por ejemplo). En los otros 5 volcanes los archivos difieren, así que
  el md5 repetido es propio de Láscar y no un artefacto del scraper que se repita siempre.
- ¿La distancia es de otra pasada? En 3 la distancia de la fila es IGUAL a la que el OCR leyó para la pasada siguiente
  (5,41 = OCR 06:06; 1,22 = OCR 05:24; 5,27 = OCR 05:36; `v01`). En Isluga 0,81 ≈ la pasada anterior (tabla 05:30, 0,84) y en
  295 5,68 ≈ la siguiente (tabla 05:18, 5,41). En 289 la fila dice 2,97 km y ninguna pasada de esa noche está ahí (tabla 05:42
  a 5,21; OCR 05:00 a 5,41 y 05:42 a 5,27): ahí el OCR eligió mal un marcador, no tomó «otra pasada» (**VP162-07**). En las tres
  `_Dist.png` que miré, el gráfico de MIROVA de esa misma imagen dibuja la pasada en el último día con un punto negro (> 7 km):
  ~13 km (289), ~9,5 km (295) y ~24 km (288), junto al punto rojo cercano de la otra pasada.

### Afirmación 3: el VRP de cada fila es de su pasada y calza con píxeles a 8,7 a 29 km del cráter (port y K)

**CONFIRMADO EN PARTE.** Gravedad: 2.

- VRP de su pasada: CONFIRMADO. Está en la celda de su hora en la imagen (tabla de arriba) y el cenit de esa celda calza con el
  del gránulo Suomi NPP del lote (58,2; 59,2; 20,6; 42,3; 48,9; 62,5°, `v03`) a menos de 1°.
- Port: CONFIRMADO que calza y que no es azar (`v03_pixeles_y_nulo_salida.txt`). Totales del port 1,280 / 1,656 / 2,180 /
  2,278 / 2,526 / 1,785 MW contra MIROVA 1,25 / 1,65 / 1,91 / 2,22 / 2,51 / 1,86; |log razón| mediana de las 6: 0,025. Nulo:
  emparejando cada port de las 6 con una protegida de MIROVA al azar del lote, la mediana tiene p1 = 0,086 y 0 de 2.000
  barajados llegan a 0,025. En todo el lote (72 pares MIROVA > 0 y port > 0) la mediana real es 0,034 contra 1,42 barajada: el
  port sigue a MIROVA cuando miran lo mismo. No es una suma elegida a dedo: es el total del port, no un subconjunto.
- Distancias: REFUTADO el rótulo, no la conclusión (**VP162-01**). El campo 3 de cada píxel del runner es la distancia a (X0, Y0),
  el punto de referencia de MIROVA, no al cráter (`experiments/_s159/portes/mirova_port.py:111`, `np.hypot(X - X0, Y - Y0)`). Mi
  reconstrucción reproduce ese campo con error máximo 0,5 m en los 326 píxeles del lote (control de instrumento), y al cráter de
  `volcanoes.yaml` da: 279 13,2 a 13,7 km (informe 14,3 a 15,0); 285 8,2 y 28,3 a 28,9 (informe 9,0 y 29); 288 21,3 a 24,2;
  289 14,9 (informe 12,5 a 12,6); 294 25,1 a 25,8 (informe 22,3 a 23,0); 295 9,1 a 9,6 (informe 8,7 a 9,2). El (X0, Y0) de
  Tupungatito está a 4,84 km del cráter. Todas siguen lejos del inner (5 y 7 km), así que el veredicto no cambia; el rango
  correcto es «8,2 a 28,9 km del cráter». El campo 4 de cada píxel es la radiancia MIR, no MW.
- K: CONFIRMADO en posición, NO en magnitud. Posición (`v03`, `v04`): el cúmulo lejano de K está a 0,15 a 0,26 km de los
  píxeles del port en 285 y a 0,16 a 0,49 km en 295; en 294 el píxel descartado del record de producción de las 05:18 está a
  0,08 km del objeto del port. Magnitud: K da 0,907 (279), 0,511 (285), 1,742 (288), 2,292 (289), 0,15 publicado far (294) y
  1,112 (295) MW; calza con MIROVA en 289 y de cerca en 288, no en 279, 285, 294 ni 295. La frase del informe «coincide con lo
  que el port y K miden» vale para el port; para K sólo vale la posición.
- **VP162-02**: la «comprobación independiente (A109)» del informe para 294 («NOAA-20, 05:36, ve la misma fuente lejana a 21,9 km
  con 0,20 MW») es un pareo de radios, no de posiciones (A93, A107). El píxel de NOAA-20 a 21,93 km del cráter está en
  -33,3222, -70,0485, a **34,75 km** del objeto que el port ve a las 05:18 (-33,61, -69,90) y a 35,0 km del cúmulo far de K
  (`v04_k_y_vecinas_salida.txt`). Es otro objeto. La existencia de la fuente lejana en un gránulo independiente queda SIN DATO
  en 294 (y en 295, como ya decía el informe).

### Afirmación 4: las 3 que K publica, las publica por un píxel débil del cráter (0,008 a 0,041 MW)

**CONFIRMADO.**

- Predicado del tablero ejecutado con node desde `frontend/index.html` (`banco_paridad.correr_node`), no reconstruido
  (`v05_predicado_k_salida.txt`). Control de identidad del predicado: `([0, 1, 1, 1, 0], [1, 0])`, el valor que exige
  `banco_paridad.controles`. K publica 279, 288 y 289 con display 0,016 / 0,0406 / 0,0079 MW, `summit`; no publica 285, 294
  ni 295 (`far`). Control negativo: el mismo record con el cúmulo movido a `far` a 9 km deja de publicar en los 3.
- Posición: haversine propio desde la lat/lon del cúmulo de K al cráter: 0,255; 0,834; 0,170 km (`v04`), igual al campo del
  record. El objeto lejano entra en el VRP de escena de K (0,907; 1,742; 2,292 MW) y no se publica.
- El port no tiene píxeles cerca del cráter en esas 3: su píxel más cercano está a 13,2 (279), 21,3 (288) y 14,9 km (289).
- Los tres valores están bajo 0,05 MW (regla D-9): no son alertas de MIROVA que se pierdan.

### Afirmación 5: 128 de las 234 protegidas A de VIIRS 375 son sólo OCR anteriores al 2026-10-09

**CONFIRMADO el conteo; NO CONFIRMADO que sean «de ese tipo».** Gravedad: 3 (para la decisión).

- Conteo: 234 protegidas A (canal unión, toda la referencia; rango 2026-01-13 a 2026-10-17), 128 sólo OCR antes del hito, 104 de
  la tabla, 2 sólo OCR desde el hito (`v02`). Conteo crudo sin el agrupador de #903 (OCR alerta ≥ 1 MW sin fila de tabla a
  ≤ 120 s): 128 antes del hito, y 104 filas de tabla ≥ 1 MW (`v06`). Mismo número por los dos caminos.
- Composición (**VP162-03**), con la plataforma tomada de nuestro record VIIRS 375 a ≤ 3 min: **48 Suomi NPP, 8 NOAA-21,
  1 NOAA-20, 71 sin record**. De las 71 sin record, 69 tienen el record más cercano a más de 30 min (casi todas Lastarria y
  Láscar, marzo a junio). Además 88 de las 128 son anteriores al hito de distancia del OCR (2026-06-13) y la regla las saca
  también por `ocr_sin_distancia_medida`. Iguales a las 6 en el sentido estricto (Suomi NPP, con distancia medida, sacadas sólo
  por el hito de Suomi NPP): **11**. Con la regla y la plataforma del record, 125 de las 234 salen «no de cráter»; 71 de ellas
  por no tener plataforma, no por evidencia de otra pasada.
- El informe ya decía «plataforma por resolver»: no se equivoca. Lo que no se sostiene es leer el 128 como «128 casos como
  estas 6», que es como lo enuncia el material de esta tarea.

## Hallazgos propios (por gravedad)

| ID | título | evidencia | confianza | gravedad |
|---|---|---|---|---|
| VP162-03 | El estrato de 128 no es «de Suomi NPP»: 48 SNPP, 9 NOAA, 71 sin plataforma; 88 ya caen por el hito de distancia; sólo 11 son como las 6 | `v02_regla_y_estrato_salida.txt` | CONFIRMADO | 3 |
| VP162-04 | El «0 de 6» de la regla es por construcción (fecha); con plataforma NOAA-20 las 6 salen de cráter | `v02` | CONFIRMADO | 2 |
| VP162-02 | La corroboración de 294 por NOAA-20 mira otro objeto, a 34,75 km (pareo de radios, A93/A107) | `v04_k_y_vecinas_salida.txt` | CONFIRMADO | 2 |
| VP162-01 | Las distancias «al cráter» de los píxeles del port son a (X0, Y0) de MIROVA; al cráter, 8,2 a 28,9 km (Tupungatito hasta 2,8 km de diferencia). Veredicto igual | `mirova_port.py:111`; `v03` | CONFIRMADO | 1 |
| VP162-07 | En 289 la distancia de la fila (2,97 km) no corresponde a ninguna pasada: mal marcador del OCR, no «otra pasada» | `v01_filas_crudas_salida.txt` | CONFIRMADO | 1 |
| VP162-05 | Procedencia: el encabezado dice que la referencia es `latest_consolidado.csv` (ba7b594ab); `02` carga en realidad `mirova_v1_snapshot/registro_vrp_consolidado.csv` (0c8848ff9) por el loader y `03` usa `latest_consolidado.csv`. Las dos copias y la remota de hoy dan lo mismo para las 6 | `scripts/referencia_mirova_unificada.py:71-73`; `v01`, `v06` | CONFIRMADO | 1 |

Cómo se ve en el tablero: ninguno de estos hallazgos cambia lo que el operador ve hoy; pesan en la vara de adopción del
paquete de VIIRS 375 (qué protegidas cuentan). Cómo reproducir: `python -I v01_filas_crudas.py`;
`python -I v02_regla_y_estrato.py <extracción de 719e9c32e con git archive>`; `python -I v03_pixeles_y_nulo.py`;
`python -I v04_k_y_vecinas.py`; `python -I v05_predicado_k.py`; `python -I v06_conteo_crudo.py <consolidado remoto>`. Los v03
a v05 leen el lote de S159 en `D:\vrp-trabajo\temporales\s159_portes\run_39712862945`.

## VERIFICADO LIMPIO

- La copia `_clase_mirova_903.py` es la de 719e9c32e (sólo cambia CRLF), y 719e9c32e es la cabeza abierta del PR #903.
- El reloj de las cabeceras: 6 de 6 posteriores, rango exacto 18 a 102 min, volcán correcto en las 6.
- El md5 repetido de Láscar es el mismo contenido descargado dos veces (blob git idéntico en 4 archivos).
- El VRP de cada fila está en la celda de su hora, y el cenit de la celda calza con el gránulo Suomi NPP.
- El pareo VRP de MIROVA contra el total del port no es azar (nulo medido, 0 de 2.000).
- El objeto lejano que ve el port es el mismo que ve K en 285, 294 y 295 (posiciones a menos de 0,5 km).
- K publica 279, 288 y 289 sólo por el píxel del cráter (predicado en node, control positivo y negativo).
- Los conteos 234, 128 y 104: iguales por el agrupador de #903 y por un conteo crudo.
- `evaluar.dist_regla("cercano")` mide desde (X0, Y0) y no desde el cráter, pero en las 79 pasadas del lote de S159 con
  píxeles del port eso no cambia ninguna clase summit/far (`v03`, última sección). Sólo medido en ese lote.

## SIN DATO

- Si las fuentes lejanas existen en un gránulo independiente: 294 (la corroboración citada es otro objeto) y 295.
- Si el «K re-corrido» del lote de S159 usó exactamente el perfil de producción con K.
- Las `_Dist.png` de 279, 285 y 294; la columna `Nivel_Anomalia_MIROVA` del CSV en las 6 filas.
- La plataforma de 71 de las 128 protegidas sólo OCR anteriores al hito (no hay record nuestro a ≤ 30 min en 69).

## ¿Se sostiene la recomendación?

Para las 6, sí: hay tres evidencias independientes de la fecha (cabecera posterior, magnitud que calza sin azar con un objeto a
8 a 29 km, K que sólo publica el cráter bajo 0,05 MW), así que juzgarlas con la regla de cráter de #903 está respaldado, con el
rango de distancia corregido y sin la corroboración de NOAA-20 en 294. Para el estrato entero no basta: la regla saca por fecha
125 de 234 protegidas, 71 sólo por no tener plataforma y 88 también por el hito de distancia, así que cada adopción tiene que
informar la lectura A al lado y además separar esos dos grupos, sin presentar el 128 como «128 casos como estos 6».
