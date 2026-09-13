# EJE 5 (S138): la batería del Apéndice A como instrumento. Auditoría adversarial (T7)

Auditor: agente Eje 5, sesión S138, 2026-09-13. Repo en `main` limpio (HEAD `6b1dd91ef`). Read-only:
nada del repo se modificó; los scripts y salidas de esta auditoría viven en
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s138_audit\eje5\`.

**La pregunta.** El 6/6 y 0/3 de producción, y el 5/6 y 3/3 del mejor brazo de S137, ¿miden
"publicamos el objeto que el autor detectó" o miden otra cosa que coincide por casualidad?

**La respuesta corta.** Miden otra cosa. La batería declara "conforme" un positivo si *cualquier*
pasada nocturna de la fecha UTC publica *cualquier* cúmulo con VRP > 0 a 5 km o menos de la
coordenada del catálogo (`experiments/_s136/conformidad_apendice.py:158-160`). No mira qué pasada
(el autor muestra una sola, con hora en el título de la figura), no mira posición (sólo distancia) y
el JSON de producción ni siquiera guarda la posición del cúmulo. Medido sobre las nueve figuras:
de los 6 "conformes" de producción, **0 son verificables como el objeto del autor, 2 son con
certeza otro objeto y 4 son indeterminables**. En el mejor brazo de S137 (B22 sin compuerta con
fondo local, conectiva prosa) los 5 conformes **sí** son el objeto del autor, y el sexto (A2) también
lo encuentra, a 2,5 km del centroide de la máscara del autor, pero la batería lo cuenta como falso
negativo porque evalúa a 5 km de la cumbre y el objeto está a 11 km. El conteo cambia con el radio
(3, 5 u 8 km) y con la pasada: es un instrumento frágil que hoy se está usando para decidir tres
correcciones al pipeline de producción.

Convención de este documento: "producción" es el brazo `B21 min (hoy)`; los brazos se nombran como
en `experiments/_s137/comparar_brazos_apendice.py`. Todos los números salen de los tres scripts
de `experiments/_s138_audit/eje5/` y sus JSON en `out/` (regla S91); ninguno está transcrito de
un documento anterior.

---

## 0. Cómo se midió (y las dos preguntas del instrumento, contestadas antes de medir)

### 0.1 Posición del autor en las nueve figuras (`medir_9_figuras.py`, salida `out/figuras_9.json`)

Se rasterizó cada página del apéndice a 200 dpi con PyMuPDF, se aisló el panel "ALERT Mask" como
la componente conexa no blanca más grande y aproximadamente cuadrada (el marco más su interior,
negro en los positivos y gris uniforme en los negativos), se descartó un margen de 5 px, y se
calculó el centroide de los píxeles blancos en unidades de celda. Geometría del paper: grilla de
51 x 51 celdas de 1 km centrada en la cumbre (`sp426.5.pdf` p. 3, y el eje 2 lo cita como P06),
norte arriba (verificado en tres figuras por rasgos geográficos: el lago Villarrica al NW aparece
arriba a la izquierda en A6, la costa sur abajo en A2, el valle del Tambo al E a la derecha en A5).

- **Pregunta 1 (¿vería la máscara si estuviera en otro lado?)**: sí. Control positivo con un
  panel sintético: una celda en (36, 26) da 10,13 km a 90,0 grados; en (26, 36) da 10,13 km a
  0,0 grados (esperado 10 km, 90 y 0). Un panel sin blancos da "sin máscara".
- **Pregunta 2 (¿se vería distinto si el instrumento estuviera muerto?)**: sí. Con la escala
  invertida a propósito (norte abajo) el rumbo del (26, 36) pasa a 180,0; con 2 km por celda la
  distancia se dobla a 20,26 km. Y los tres paneles negativos reales (A4, A7, A9) dan "sin
  máscara" (0 píxeles blancos, gris interior 128). Todos los controles pasan.
- **Robustez**: barrido de margen (3 a 9 px) y umbral de blanco (150 a 210) sobre los seis
  positivos: la distancia se mueve como máximo 0,4 km (A2: 10,73 a 11,48 km) y el rumbo como
  máximo 22 grados en A6, donde la máscara está a 0,2 km del centro y el rumbo no significa nada.

La conversión a lat/lon necesita el centro de la figura. Se usaron dos: la coordenada de
`apendice_a.yaml` (que el archivo llama GVP) y `Volc_LAT/Volc_LON` del archivo global de MIROVA
(`data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv`, primera fila de cada IDvolc; Dubbi no está).
Difieren entre 0,45 y 1,62 km. Dato que valida las dos cosas a la vez: con el centro de MIROVA, las
máscaras del autor en A1, A3, A5, A6 y A8 caen a **0,12 a 0,70 km** de la coordenada actual del
catálogo (la cumbre real), mientras que con el centro "GVP" del yaml quedan a 0,7 a 1,3 km. Es decir,
la grilla del autor está centrada en la coordenada del archivo de MIROVA, y sus detecciones están en
la cumbre. Lo uso como centro primario; el otro se reporta.

### 0.2 Reevaluación de la batería sobre los JSON commiteados (`romper_bateria.py`, salida `out/romper_bateria.json`)

`evaluar_caso` se reimplementó de forma paramétrica (radio, referencia, pasada). **Control de
identidad**: con radio 5 km, referencia del yaml y todas las pasadas reproduce **72 de 72**
veredictos commiteados (8 brazos x 9 casos), 0 discrepancias. **Control positivo**: con radio
0,01 km los 48 positivos caen a falso negativo (48 de 48). Sin estos dos controles nada de lo que
sigue valdría.

Sólo 4 de los 8 brazos persisten `pc_lat/pc_lon` (los cuatro "sinBT" de S137, campo agregado en
`conformidad_apendice.py:131`). Para los otros cuatro, incluida producción, la separación entre
nuestro cúmulo y el objeto del autor se acota por abajo con |d_autor - d_nuestro| (A93: la
diferencia de dos radios es una cota inferior de la distancia entre los dos puntos), y se declara
"indeterminable" cuando la cota no alcanza para decidir.

### 0.3 Holdout (`holdout_noches.py`, salida `out/holdout_noches.json` y `out/holdout_modis_historia.txt`)

Mismo loader (`pipeline/mirova_csv_loader.py:123`, CONS unión OCR) y mismo filtro diurno
(`pipeline/store._reject_daytime`) que `scripts/auto_audit_weekly.py:47-48, 140-143`. Cobertura
declarada: el snapshot CONS tiene 36.255 filas del 2026-01-10 al 2026-09-07 y el OCR 937 filas del
2026-01-20 al 2026-09-07, así que la ventana 2026-06-01 a 2026-08-31 está cubierta por la
referencia. Control positivo: Villarrica y Láscar tienen noches > 0.

---

## 1. Las nueve figuras: posición del autor y posición de nuestro cúmulo, brazo por brazo

### 1.1 La máscara del autor

Distancia y rumbo desde el centro de la grilla (celda 26, 26). "d a GVP" es la distancia del punto
del autor a la coordenada de `apendice_a.yaml` usando el centro de MIROVA. Pasada: la del título de
la figura (leído en el raster; el caption sólo trae la fecha).

| caso | volcán | paper | pasada de la figura (UTC) | máscara | dist. centro (km) | rumbo | celdas | d a GVP (km) |
|---|---|---|---|---|---|---|---|---|
| A1 | Bezymianny | detecta | 2012-01-08 15:15 | sí | 1,00 | 118 | 2,1 | 0,43 |
| A2 | Eyjafjallajökull | detecta | 2010-04-07 04:40 | sí | **10,98** | **83** | 8,5 (4,2 x 3,1) | **11,58** |
| A3 | Erta Ale | detecta | 2009-08-16 19:35 | sí | 0,74 | 349 | 3,9 | 0,68 |
| A4 | Dubbi | no detecta | 2013-07-03 19:30 | **sin máscara** | | | 0 | |
| A5 | Ubinas | detecta | 2008-04-03 03:20 | sí | 1,29 | 24 | 1,7 | 0,12 |
| A6 | Villarrica | detecta | 2009-06-24 05:55 | sí | 0,21 | 309 | 1,7 | 0,70 |
| A7 | Tolbachik | no detecta | 2012-11-20 10:40 | **sin máscara** | | | 0 | |
| A8 | Etna | detecta | 2010-02-08 00:55 | sí | 1,15 | 359 | 0,7 | 0,58 |
| A9 | Stromboli | no detecta | 2010-01-19 01:15 | **sin máscara** | | | 0 | |

Cinco de los seis positivos están en la cumbre (a menos de 1,3 km del centro y a menos de 0,7 km de
la coordenada actual). El sexto, A2, está a 11 km al este: en abril de 2010 la erupción de
Eyjafjallajökull era la fisura de Fimmvörðuháls, en el flanco oriental, no el cráter somital (la
erupción somital empezó el 14 de abril; el dato de contexto es histórico y no sale de esta
medición). S137 midió 9,5 a 9,7 km para la misma máscara; este script, con controles y barrido de
robustez, da 10,7 a 11,5. No encontré en `experiments/_s137/` ningún script que produzca el 9,6 (ver
hallazgo H7).

### 1.2 Nuestro cúmulo, brazo por brazo, en la pasada de la figura

"sep" es la separación entre el centroide de nuestro cúmulo primario y el punto del autor (centro
MIROVA). Donde el JSON no tiene posición, "cota" es la cota inferior A93. "d" es nuestra distancia
a la coordenada del yaml, que es lo que la batería mira. Veredicto de objeto: **mismo** si
sep <= 2 km (un píxel remuestreado es 1 km, dos es el vecino inmediato); **otro** si sep > 2 km o
cota > 2 km; **indet.** si sólo hay cota y no alcanza. Para A2, cuya máscara mide 4 celdas, se da
además el veredicto laxo (sep <= 4 km, la extensión de la máscara más una celda).

| caso | producción B21 min | B21 max | B22 min | B22 max | B22 min sinBT | B22 max sinBT | B22 min sinBT loc | B22 max sinBT loc |
|---|---|---|---|---|---|---|---|---|
| A1 (autor a 0,4 km) | d 4,22, 42 px, 5,0 MW: cota 3,79, **otro** | sin cúmulo | d 2,29: cota 1,86, indet. | d 2,29: cota 1,86, indet. | sep 1,86, **mismo** | sep 1,86, **mismo** | sep 1,86, **mismo** | sep 1,86, **mismo** |
| A2 (autor a 11,6 km) | d 3,12: cota 8,47, **otro** | d 9,70, 52,9 MW: cota 1,88, indet. | d 9,13: cota 2,46, **otro** (estricto) | d 9,11: cota 2,47, **otro** (estricto) | sep 3,60: otro / laxo mismo | sep 2,50: otro / laxo **mismo** | sep 3,60: otro / laxo mismo | sep 2,50: otro / laxo **mismo** |
| A3 (0,7 km) | d 1,27: cota 0,60, indet. | idem | idem | idem | sep 1,23, **mismo** | sep 1,23, **mismo** | sep 1,23, **mismo** | sep 1,23, **mismo** |
| A5 (0,1 km) | d 1,16: cota 1,04, indet. | sin cúmulo | d 1,33: cota 1,21, indet. | idem | sep 1,38, **mismo** | sep 1,38, **mismo** | sep 1,38, **mismo** | sep 1,38, **mismo** |
| A6 (0,7 km) | d 1,02: cota 0,31, indet. | sin cúmulo | VRP 0,0 (cúmulo sin magnitud) | VRP 0,0 | VRP 0,0 | VRP 0,0 | sep 0,62, **mismo** | sep 0,74, **mismo** |
| A8 (0,6 km) | d 1,98: cota 1,39, indet. | d 2,26: cota 1,68, indet. | d 0,93: cota 0,34, indet. | idem | sep 0,63, **mismo** | sep 0,63, **mismo** | sep 0,63, **mismo** | sep 0,63, **mismo** |

Resumen por brazo, sobre los positivos que la batería declaró CONFORME (`out/romper_bateria.json`,
`resumen_objeto`):

| brazo | conformes (batería) | mismo objeto | otro objeto | indeterminable |
|---|---|---|---|---|
| B21 min (producción) | 6 | **0** | **2** (A1, A2) | 4 |
| B21 max | 2 | 0 | 0 | 2 |
| B22 min | 4 | 0 | 0 | 4 |
| B22 max | 4 | 0 | 0 | 4 |
| B22 min sinBT | 4 | 4 | 0 | 0 |
| B22 max sinBT | 4 | 4 | 0 | 0 |
| B22 min sinBT loc | 6 | 5 | **1** (A2, vía la pasada 03:00 a 11,5 km del autor) | 0 |
| B22 max sinBT loc | 5 | 5 | 0 | 0 |

Tres cosas que la tabla dice y el "6/6" esconde:

1. **El "conforme" de producción en A1 es otro objeto.** En la pasada de la figura (15:15) publicamos
   42 píxeles con VRP exactamente 5,0 MW a 4,22 km de la cumbre, clasificado `far`; el autor marca 2
   celdas a 0,43 km. El 5,0 exacto es el tope D9 para cúmulos que disparan sólo por el camino D
   contextual (`pipeline/profiles/mirova_equivalent.yaml:469` `path_d_only_cap_mw: 5.0`, aplicado en
   `pipeline/process_modis.py:997-1002, 1064`): el predicado exige `n_bt_path == 0 and n_nti_path == 0`,
   o sea que no disparó ningún camino duro. Lo mismo vale para A5 06:25 (42 px, 5,0 MW) y para el
   falso positivo de A7 10:40 (28 px, 5,0 MW). Producción "coincide" con el autor en A1 publicando
   un campo difuso de 42 píxeles con el tope de un artefacto, no su píxel de cumbre.
2. **El 6/6 de "B22 min sinBT loc" vale 5.** Su conforme en A2 es la pasada de las 03:00 (otra
   noche local, ver H2), con un cúmulo de 0,31 MW a 1,21 km de la cumbre, a **11,5 km** del objeto del
   autor. En la pasada de la figura ese mismo brazo tiene el objeto a 3,6 km (borderline).
3. **El mejor brazo encuentra los seis objetos del autor** y la batería le anota cinco: A2 es el
   objeto correcto (2,5 km del centroide de una máscara de 4 celdas), fuera de la caja de 5 km.

---

## 2. Sensibilidad: radio x referencia x pasada

Celda = positivos conformes / negativos conformes. Referencia: **g** coordenada del yaml, **m** centro
de la grilla de MIROVA, **a** posición medida del autor (para negativos, el centro). Pasada: **t**
todas las nocturnas de la fecha UTC (lo que hace la batería), **f** sólo la de la figura. El asterisco
marca brazos sin posición en el JSON, donde mover la referencia es imposible (n/d) y la celda no vale.

| brazo | 3 g t | 3 g f | 3 a t | 3 a f | **5 g t (batería)** | 5 g f | 5 a t | 5 a f | 8 g t | 8 g f | 8 a t | 8 a f |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B21 min (producción) | 6/0 | **4/0** | n/d | n/d | **6/0** | 6/0 | n/d | n/d | 6/0 | 6/0 | n/d | n/d |
| B21 max | 2/3 | 2/3 | n/d | n/d | 2/3 | 2/3 | n/d | n/d | 3/3 | 2/3 | n/d | n/d |
| B22 min | 4/3 | 4/3 | n/d | n/d | 4/2 | 4/2 | n/d | n/d | 5/2 | 4/2 | n/d | n/d |
| B22 max | 4/3 | 4/3 | n/d | n/d | 4/3 | 4/3 | n/d | n/d | 5/3 | 4/3 | n/d | n/d |
| B22 min sinBT | 4/3 | 4/3 | 5/3 | 4/3 | 4/2 | 4/2 | 5/2 | 5/2 | 5/2 | 4/2 | 5/2 | 5/2 |
| B22 max sinBT | 4/3 | 4/3 | 5/3 | 5/3 | 4/3 | 4/3 | 5/3 | 5/3 | 5/3 | 4/3 | 5/3 | 5/3 |
| B22 min sinBT loc | 6/3 | 5/3 | 5/3 | 5/3 | **6/2** | 5/2 | 6/2 | 6/2 | 6/2 | 5/2 | 6/2 | 6/2 |
| B22 max sinBT loc | 5/3 | 5/3 | **6/3** | **6/3** | **5/3** | 5/3 | 6/3 | 6/3 | **6/3** | 5/3 | 6/3 | 6/3 |

(Tabla completa con la referencia **m** en `out/romper_bateria.json`, clave `sensibilidad`; la
columna m coincide con g en todas las celdas salvo que el brazo no tenga posición.)

Lo que se mueve:

- **Producción** pasa de 6/6 a **4/6** con radio 3 km y sólo la pasada de la figura (pierde A1 y A2,
  justamente los dos "otro objeto"). Ningún radio le cura los negativos (0/3 en todos).
- **El mejor brazo** (B22 max sinBT loc) es 5/3 con la batería, y **6/3, es decir "cumple", con
  cualquiera de estas tres variantes**: referencia en la posición del autor (radio 3, 5 u 8), o
  radio 8 km desde la cumbre. Pero la variante "8 km" cumple por la razón equivocada: a 8 km entra
  la pasada 23:40 (otra noche), con un cúmulo a 7,37 km de la cumbre y a 5,2 km del autor.
- **"B22 min sinBT loc"** es 6/2 con la batería y 6/3 con radio 3 km: el falso positivo de Dubbi
  está a 3,56 y 4,10 km de la cumbre, dentro de 5 y fuera de 3. Con la pasada de la figura cae a 5/x
  porque su A2 vive en la pasada de las 03:00.
- El criterio de S136 ("6 de 6 y 3 de 3, sin indeterminados") **cambia de veredicto para el mismo
  JSON** según el radio y la pasada. Eso es la definición de instrumento frágil.

Dos observaciones sobre los negativos (`out/negativos_control_nti_a2.txt`):

- En producción los tres falsos positivos **sí** ocurren en la pasada de la figura (A4 19:30 1,55 MW a
  2,16 km; A7 10:40 5,0 MW tope D9 a 1,34 km; A9 01:15 **22,1 MW** a 0,63 km). Esos son
  contradicciones genuinas con el autor, no artefactos de la batería.
- El falso positivo de Dubbi en los brazos "min" (2,07 MW a 4,10 km en la pasada de la figura) depende
  de una coordenada que no se puede cotejar con el centro de MIROVA (Dubbi no está en el archivo), y
  está a 0,9 km del borde de la caja. Ver H10.

---

## 3. El instrumento corregido (PROPUESTA, no cambio)

Nada de esto se implementó. Es lo que la batería debería medir para que "conforme" signifique lo
que se le hace decir. Cada punto corrige un defecto concreto de la sección 1 o 2.

1. **Una pasada por caso, la del título de la figura.** `apendice_a.yaml` lleva un campo
   `pasada_utc` por caso (los nueve valores están en la tabla 1.1) y `correr_caso` procesa sólo ese
   granule. Las demás pasadas nocturnas de la fecha pueden correrse como contexto, pero no cuentan
   para el veredicto. Corrige H2 (hoy A2, A8 y A9 mezclan dos noches locales, y el 6/6 de un brazo
   depende de una pasada que el autor no mostró).
2. **Evaluar contra la posición del autor, no contra la cumbre.** `apendice_a.yaml` lleva por caso
   `autor_dist_km` y `autor_rumbo_deg` (tabla 1.1, o mejor, la máscara en celdas), y "conforme" en un
   positivo es: cúmulo con VRP > 0 cuyo centroide cae a menos de (extensión de la máscara + 1 celda)
   del centroide de la máscara, con un mínimo de 2 km. Corrige H1 (hoy A1 y A2 de producción son
   conformes con otro objeto). Para los negativos, la caja sigue siendo el ROI del paper, pero
   sobre la pasada de la figura.
3. **Centro de la grilla = coordenada del archivo de MIROVA**, con la del catálogo actual como
   control (deben diferir < 2 km; hoy difieren 0,45 a 1,62 km). Corrige el sesgo de 0,7 a 1,3 km
   que hoy tiene la conversión de las figuras, y deja Dubbi marcado como "centro no verificable".
4. **Persistir posición y camino en todos los brazos**: `pc_lat`, `pc_lon`, `n_pixels_pc`,
   `diag_n_bt_path`, `diag_n_nti_path` y si el tope D9 estuvo activo. Hoy 4 de 8 brazos, incluida
   la línea base de producción, no tienen posición y no se pueden evaluar por objeto (H5). Sin el
   camino no se distingue "publicamos la cumbre" de "publicamos un campo difuso con tope de 5 MW".
5. **Reemplazar el control de validez por uno que discrimine.** El control actual (NTI del paper
   +-0,06) lo pasan 16 a 18 de las 24 pasadas de *todos* los casos, o sea que no distingue "su
   escena" de "cualquier escena nocturna fría" (H6). Control propuesto: que la pasada sea la del
   título (punto 1) y que el número de píxeles alertados por el autor (celdas de la máscara, tabla
   1.1) esté en la misma década que el nuestro; un cúmulo de 42 píxeles contra 2 celdas del autor
   no es "conforme".
6. **Reportar "cumple" en unidades de objeto**: cuántos de los 6 objetos del autor publicamos en su
   pasada, cuántos objetos publicamos que el autor no marcó (en positivos y negativos), y a qué
   distancia. Un solo conteo 6/6 y 3/3 esconde todo lo de arriba.
7. **Declarar el límite del instrumento en el encabezado de su salida**: nueve escenas de 2008 a
   2013, ninguna chilena salvo Villarrica, ninguna VIIRS. Sirve para verificar la fidelidad del
   algoritmo MODIS al paper, no para adoptar: para eso está el holdout de la sección 4.

---

## 4. Pre-registro del A/B Tier A para D21 y D22 (listo para aprobación; fijado antes de ver resultados)

### 4.1 Por qué hace falta y qué no puede decidir la batería

Tres correcciones (banda 22 como primaria, D21; quitar la compuerta `bt > t_bg + 3 K` de los Tests
2 y 3, D22; fondo local de la magnitud, ecuación 6) se eligieron sobre nueve escenas. Con nueve
escenas y ocho brazos ya se probaron 2 x 2 x 2 combinaciones: la probabilidad de que una combinación
"cumpla" por azar no es despreciable y no se puede estimar con n = 9. La regla del proyecto es que
un cambio a `pipeline/` se adopta con A/B sobre los Tier A, criterio pre-registrado, sin pérdida de
noches confirmadas (decisión de Nicolás, S135) e intervalos bootstrap (T8).

### 4.2 Universo y holdout (medido, `out/holdout_noches.json`)

Ventana **2026-06-01 a 2026-08-31** (92 días), 11 Tier A, pasadas nocturnas (mismo filtro diurno que
el pipeline), referencia CONS unión OCR del snapshot del 2026-09-07. Noches confirmadas por MIROVA
por volcán y sensor:

| volcán | régimen | MODIS | V750 | V375 | cualquier sensor |
|---|---|---|---|---|---|
| Láscar | focal | **15** | 36 | 61 | 61 |
| Lastarria | focal | 0 | 0 | 50 | 50 |
| Isluga | focal | 0 | 19 | 74 | 75 |
| Planchón-Peteroa | focal | 0 | 5 | 28 | 29 |
| Puyehue-Cordón Caulle | focal | 0 | 15 | 37 | 37 |
| Villarrica | nevado | 0 | 6 | 11 | 12 |
| Chaitén | nevado | 0 | 1 | 14 | 14 |
| Tupungatito | nevado | 0 | 2 | 29 | 29 |
| Copahue | nevado | 0 | 1 | 3 | 4 |
| Nevados de Chillán | nevado | 0 | 0 | 5 | 5 |
| Llaima | nevado | 0 | 0 | 0 | 0 |
| **total** | | **15** | 85 | 312 | **316** (focal 252, nevado 64) |

Denominador: 688 pasadas-ALERTA en la ventana, 37 diurnas excluidas. **El hallazgo que condiciona
todo el diseño (H4)**: MIROVA publicó alertas MODIS en esa ventana **sólo en Láscar** (18 pasadas, 15
noches), y su serie MODIS cae a 2 alertas por mes en julio y agosto de 2026 (toda la historia del
CSV: Láscar 77 noches MODIS, Chaitén 3, Villarrica 2, NdC 1; `out/holdout_modis_historia.txt`). Un
A/B de un cambio MODIS que mida "noches confirmadas por MIROVA-MODIS" tendría n = 15 en un volcán y
0 en el estrato nevado, que es donde vive el artefacto que D22 quiere curar (A69, A80). Por eso la
unidad de recall se define contra la confirmación de **cualquier sensor** de MIROVA (la noche es
real si MIROVA la vio con lo que fuera), y el estrato nevado queda con 64 noches, 12 de ellas en
Villarrica, que es el volcán del caso A6.

Estratificación focal/nevado según `scripts/build_c2ab_windows.py:41-42` (S131). **Declarado**: los
scripts de S114 (`experiments/_s114_audit/discriminant_sweep.py:28`) usan otra partición (ponen
Lastarria, Isluga, PP y PCC entre los nevados); se fija la de S131 y no se cambia después de ver datos.

### 4.3 Brazos

Reproceso MODIS (Terra y Aqua) de los 11 Tier A sobre la ventana, un `data_subdir` aislado por brazo
(patrón A47; nunca en paralelo sobre el mismo directorio), en GitHub Actions por chunks (pyhdf no
corre en Windows; A15: timeout >= 1,3 x la duración medida en un piloto de un volcán, que se corre
ANTES de lanzar los 11).

| brazo | banda MIR | compuerta en Tests 2/3 | fondo de magnitud | conectiva |
|---|---|---|---|---|
| 0 control | B21 (hoy) | sí (hoy) | anillo, salvo los 5 opt-in del yaml (hoy) | min (hoy) |
| 1 | B22 | sí | hoy | min |
| 2 | B22 | no | hoy | min |
| 3 | B22 | no | local 3x3 uniforme | min |
| 4 | B22 | no | local 3x3 uniforme | max (prosa) |

Cinco brazos y no ocho. Justificación: la conectiva es ortogonal a las tres correcciones y ya se
midió sola en S136 (B21 max pierde 4 de 6 positivos); repetir min/max en los brazos 1 y 2 duplica el
costo sin pregunta nueva. Se conserva en el candidato final (brazo 3 vs 4) porque ahí es donde la
batería mostró que decide el negativo de Dubbi. Los brazos 1 y 2 existen para atribuir: si el 3 gana,
hay que saber cuánto puso cada corrección, porque cada una toca 13 lugares del código (S137).

### 4.4 Unidades y criterios (fijados ahora)

Unidad: **noche local por volcán** (A91, A94), no record ni pasada. Una noche "publica" en un brazo
si alguna pasada MODIS nocturna de esa noche tiene `primary_cluster.vrp_mw > 0` con
`final_hotspot_dist_km <= inner_radius_km` del volcán en `volcanoes.yaml` (3 a 20 km según volcán;
no un número fijo). Paridad de cobertura (S135): sólo cuentan las noches en que el brazo procesó al
menos una pasada MODIS nocturna; una noche sin pasada procesada no es pérdida ni acierto.

**C1, recall, pérdida cero (decisorio, sin bootstrap: es un conteo).** Noches confirmadas por MIROVA
(cualquier sensor, nocturnas) que el control publica y el brazo no. **Umbral: 0** en cada estrato.
Un brazo que pierde una sola noche confirmada queda descartado, aunque gane en todo lo demás.
Se reporta además la lista de noches confirmadas que el control no publica y el brazo sí (ganancia),
sin que pese en la decisión.

**C2, sobre-detección (decisorio con bootstrap).** Noches sin ALERTA de MIROVA en ningún sensor (con
al menos un registro RUTINA de MIROVA esa noche, para paridad de cobertura de la referencia) en que
el brazo publica. Se compara brazo contra control **pareado por noche**; IC 95 % de la diferencia
por bootstrap de noches (5.000 remuestreos, semilla 42, siguiendo `experiments/_s124_f70/
05_poder_estadistico.py:ic_mediana`), por estrato. "Mejora" = el IC de la diferencia excluye el
cero en el estrato nevado y no incluye un aumento en el focal.

**C3, posición (informativo con bootstrap).** Mediana por volcán de `final_hotspot_dist_km /
inner_radius_km` sobre las noches confirmadas publicadas; IC bootstrap. Un brazo que sube esa
mediana por encima de 1 en algún volcán no se adopta aunque pase C1 y C2 (estaría publicando otro
objeto, el caso A1 de producción).

**C4, magnitud (informativo, no decisorio).** Mediana del ratio nuestro/MIROVA en las 15 noches
MODIS comunes de Láscar, con IC. n demasiado chico para decidir; se reporta para no perderlo.

**Poder.** C1 es determinista. Para C2 el poder se calcula antes de abrir los brazos, sobre el
control solamente: tasa de sobre-detección del control por estrato y su IC bootstrap; el efecto
mínimo detectable es el ancho de ese IC. Si el IC del control en el estrato nevado es más ancho que
la mitad de su tasa, el A/B no puede decidir C2 con esta ventana y hay que ampliarla (hacia atrás:
el CSV cubre desde el 2026-01-10) antes de correr los brazos, no después.

### 4.5 Predicciones escritas (lo que refutaría cada cosa)

- Predicción P1: el brazo 1 (sólo B22) **pierde** noches confirmadas en el estrato nevado (la
  batería lo mostró en A6: sin compuerta quitada, el cráter helado de Villarrica no pasa). Si P1 se
  cumple, D21 no se adopta sola. Si el brazo 1 no pierde ninguna, la premisa "B22 sola rompe los
  nevados" queda refutada y hay que revisar el caso A6.
- Predicción P2: el brazo 3 no pierde ninguna noche confirmada en ningún estrato y reduce C2 en el
  nevado con IC que excluye cero. **Lo refuta**: una sola noche perdida (C1) en cualquier estrato, o
  un IC de C2 que incluya cero en el nevado. Con cualquiera de las dos, D21+D22+fondo local no se
  adopta en esta forma.
- Predicción P3: el brazo 4 (prosa) pierde noches confirmadas en el focal respecto del 3 (S136: la
  prosa apaga positivos). Si no las pierde y además baja C2 más que el 3, la conectiva se reabre
  como decisión aparte, con su propio pre-registro.
- Predicción P4: el brazo 2 (B22 sin compuerta, fondo del anillo) publica cúmulos con VRP = 0,0 en
  cumbres frías (la batería lo mostró en A6 y A8 21:20). En unidades de noche eso es una pérdida
  respecto del 3, no del control. Si el 2 no muestra esas noches con VRP 0, la atribución del fondo
  local está mal y se revisa antes de adoptar.

**Qué resultado refutaría el pre-registro entero**: que el control tenga menos de 30 noches
confirmadas procesadas en el estrato nevado (paridad de cobertura), porque entonces C1 no está
midiendo el estrato donde vive el artefacto y el A/B hay que rehacerlo con otra ventana. Ese
número se verifica antes de correr los brazos 1 a 4.

**Nada de lo anterior se adopta sin A45**: tag defensivo `pre-s13x-d21-d22-ab` y confirmación
explícita de Nicolás, con el veredicto mirado en el dashboard (feedback S107).

---

## 5. Hallazgos, por gravedad

### H1. El "conforme" de la batería no verifica el objeto; en producción 0 de 6 son verificables y 2 son otro objeto
- ARCHIVO:LÍNEA: `experiments/_s136/conformidad_apendice.py:158-160` (publica = VRP > 0 y
  `dist_crater_km <= INNER_KM`, sin posición); SCRIPT: `experiments/_s138_audit/eje5/romper_bateria.py`,
  salida `out/romper_bateria.json` clave `resumen_objeto`.
- QUÉ PASA: el autor marca en A1 dos celdas en la cumbre (0,43 km); nosotros, en su misma pasada
  (15:15), publicamos 42 píxeles con VRP igual al tope D9 (5,0 MW) a 4,22 km, y la batería dice
  "conforme". En A2 el autor marca la fisura a 11,6 km al E y nosotros un cúmulo de 0,5 MW a 3,1 km
  al SE: "conforme". Un radio de 5 km alrededor de la cumbre acepta cualquier cosa que esté cerca,
  y a 1 km de resolución en un nevado eso incluye el gradiente topográfico (A69).
- CÓMO SE VE EN EL DASHBOARD: invisible en el dashboard; visible en las decisiones: el 6/6 de
  producción se ha usado como línea base "que ya cumple los positivos" para juzgar los brazos.
- CÓMO REPRODUCIRLO: `PYTHONIOENCODING=utf-8 python experiments/_s138_audit/eje5/medir_9_figuras.py`
  y luego `... romper_bateria.py`; mirar A1 15:15 y A2 04:40 en el brazo `B21 min (hoy)`.
- CONFIANZA: CONFIRMADO (medido; la cota A93 basta para A1 y A2 sin necesitar la posición).
- GRAVEDAD: 5. Tres correcciones al pipeline de producción se están decidiendo con este conteo.

### H2. La batería mezcla pasadas y noches: el autor muestra una pasada y el JSON tiene de 2 a 4, de hasta dos noches locales
- ARCHIVO:LÍNEA: `conformidad_apendice.py:82-89` (`search_granules` por fecha UTC) y `:143-171`
  (`evaluar_caso` recorre todas); títulos de las figuras (raster, `sp426.5.pdf` pp. 18 a 22) con la
  hora; SCRIPT: `out/negativos_control_nti_a2.txt`, sección "noches distintas".
- QUÉ PASA: A2, A8 y A9 tienen pasadas de dos noches locales distintas bajo la misma fecha UTC. El
  6/6 de "B22 min sinBT loc" existe porque A2 publica en la pasada de las 03:00 (noche anterior a
  la de la figura) un cúmulo en la cumbre, a 11,5 km del objeto del autor. Con sólo la pasada de la
  figura ese brazo es 5/6.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `romper_bateria.py`, tabla (b), columnas "f" contra "t".
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 4.

### H3. El conteo "cumple / no cumple" cambia con el radio: producción 6/6 a 4/6 con 3 km; el mejor brazo 5/3 a 6/3 con 8 km o con la posición del autor
- ARCHIVO:LÍNEA: `conformidad_apendice.py:46` (`INNER_KM = 5.0`); SCRIPT: `out/romper_bateria.json`
  clave `sensibilidad`.
- QUÉ PASA: sección 2. El falso positivo de Dubbi en los brazos "min" está a 3,56 y 4,10 km: dentro
  de 5, fuera de 3. El A2 del mejor brazo está a 2,5 km del autor y a 9,1 km de la cumbre: fuera
  de 5, dentro de 8. El criterio de S136 no es robusto al parámetro que él mismo fija.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `romper_bateria.py`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 4.

### H4. El holdout MODIS de jun-ago 2026 tiene 15 noches confirmadas, todas de Láscar, y 0 en nevados
- SCRIPT: `experiments/_s138_audit/eje5/holdout_noches.py`, `out/holdout_noches.json`;
  `out/holdout_modis_historia.txt` (MODIS por mes: jun 14, jul 2, ago 2).
- QUÉ PASA: MIROVA casi no publica MODIS en los Tier A desde julio de 2026 (2 alertas por mes). Un
  A/B de correcciones MODIS que mida contra MIROVA-MODIS no tiene estrato nevado. El pre-registro
  de la sección 4 lo resuelve con la confirmación de cualquier sensor (316 noches, 64 nevado), y lo
  declara. Si se hubiera pre-registrado "noches confirmadas MODIS" el A/B habría salido "sin
  pérdida" por vacuidad, un cero que no distingue "no perdió" de "no midió".
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `PYTHONIOENCODING=utf-8 python experiments/_s138_audit/eje5/holdout_noches.py`.
- CONFIANZA: CONFIRMADO. (No investigué por qué MIROVA publica tan poco MODIS; puede ser el
  scraper, el sitio o la actividad. Queda como pregunta para el eje que audita la referencia.)
- GRAVEDAD: 4.

### H5. Cuatro de los ocho brazos, incluida la línea base de producción, no persisten la posición del cúmulo
- ARCHIVO:LÍNEA: `conformidad_apendice.py:131` (`pc_lat/pc_lon`, agregado en S137);
  `experiments/_s136/out_apendice/resultado_apendice.json` y `out_apendice_prosa/`,
  `experiments/_s137/out_apendice_b22/` y `out_apendice_b22_prosa/`: la clave `pc_lat` no existe
  en ninguna de sus pasadas (esos brazos corrieron con la versión del script anterior al campo).
- QUÉ PASA: la comparación "producción contra el mejor brazo" es asimétrica: al mejor brazo se le
  puede exigir el objeto, a producción no. Producción no fue rerun después de agregar el campo.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `grep -c '"pc_lat"' experiments/_s136/out_apendice/resultado_apendice.json`
  da 0 (la clave no está en ninguna de las 24 pasadas); en
  `experiments/_s137/out_apendice_b22_sincompuerta/resultado_apendice.json` da 24.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 3.

### H6. El "control de validez" por NTI no discrimina: lo pasan 16 a 18 de las 24 pasadas de todos los casos
- ARCHIVO:LÍNEA: `conformidad_apendice.py:48, 146-156` (`TOL_NTI = 0.06`); SCRIPT:
  `out/negativos_control_nti_a2.txt`, sección "CONTROL DE VALIDEZ NTI".
- QUÉ PASA: la banda del caso A6 (-0,93 +-0,06) la satisfacen pasadas de A1, A5, A7, A8 y A9; la de
  A5, pasadas de siete casos ajenos. Un control que acepta cualquier escena nocturna fría no
  contesta la pregunta 1 del instrumento ("si estuviera mirando otra escena, ¿lo vería?"). En 8
  brazos nunca se disparó.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 3.

### H7. La posición del autor en A2 que usa el post hoc (9,6 km) no la produce ningún script; medida con controles da 10,7 a 11,5 km, y el veredicto post hoc de un brazo cambia con esa diferencia
- ARCHIVO:LÍNEA: `conformidad_apendice.py:230-231` (`POSICION_AUTOR = {"A2": (9.6, 83.0)}`,
  `RADIO_POST_HOC_KM = 3.0`); `experiments/_s137/RESULTADO_ETAPA_Y_FIGURAS.md` (sección
  "Eyjafjallajökull") es la única fuente del 9,6; SCRIPT: `out/figuras_9.json` (A2: 10,98 km, 83,2
  grados; barrido 10,73 a 11,48) y `out/negativos_control_nti_a2.txt` sección "A2 post hoc".
- QUÉ PASA: en "B22 min sinBT" el cúmulo de las 04:40 está a 2,79 km del punto de S137 (conforme post
  hoc) y a 3,44 a 3,60 km del punto medido acá (no conforme). Una evaluación que cambia de
  veredicto con 1,3 km de diferencia en una medición de figura sin script no es reproducible.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CONFIANZA: CONFIRMADO para la medición propia; SOSPECHA sobre el origen del 9,6 (busqué
  `9[,.]6` y `rumbo` en `experiments/_s137/*.py` y no hay productor; `medir_figuras_apendice.py`
  mide sigma, no posición).
- GRAVEDAD: 3.

### H8. Varios "conformes" y un falso positivo de producción son cúmulos del camino D con el tope de 5 MW, no los Tests 2 y 3
- ARCHIVO:LÍNEA: `pipeline/profiles/mirova_equivalent.yaml:469` (`path_d_only_cap_mw: 5.0`),
  `pipeline/process_modis.py:997-1002` (predicado: `n_bt_path == 0 and n_nti_path == 0`), `:1064`
  (aplicación); JSON: producción A1 11:10 y 15:15 (30 y 42 px, 5,0), A5 06:25 (42 px, 5,0), A7
  10:40 (28 px, 5,0); en los brazos B22, A2 23:40 y 03:00 (5,0).
- QUÉ PASA: un VRP exactamente igual a 5,000 en cúmulos de 28 a 42 píxeles es la firma del tope
  D9 (S71/S77, cirrus). La batería cuenta esos cúmulos igual que un píxel de cumbre. El "conforme"
  de A1 y A5 en producción y el falso positivo de A7 son campos difusos capados, es decir, el
  fenómeno A69/A80 vestido de acierto. El JSON no guarda `diag_n_bt_path/nti_path` ni si el tope
  actuó, así que se infiere por el valor exacto.
- CÓMO SE VE EN EL DASHBOARD: en producción real este mismo mecanismo se publica como cúmulo
  `far` de 5 MW (ya documentado en D9/A23); acá lo relevante es que la batería lo premia.
- CONFIANZA: CONFIRMADO el tope y su predicado; SOSPECHA que cada 5,0 exacto sea el tope (es la
  única fuente de un 5,000 que encontré, `grep 5\.0` en `pipeline/`).
- GRAVEDAD: 3.

### H9. El centro de la grilla del autor es la coordenada del archivo de MIROVA, no la del yaml; difieren 0,45 a 1,62 km
- SCRIPT: `out/figuras_9.json`, campos `gvp_vs_centro_mirova_km` y `autor_dist_a_gvp_si_centro_mirova_km`.
- QUÉ PASA: con el centro de MIROVA las máscaras de A1, A3, A5, A6 y A8 caen a 0,12 a 0,70 km de la
  coordenada del yaml; con el centro del yaml, a 0,7 a 1,3 km. El error es chico para la caja de 5
  km, pero mueve el post hoc de A2 en 0,16 km y sesga cualquier comparación de posición.
  Nota: la entrada de Villarrica en `apendice_a.yaml` es la coordenada del cráter a 6 decimales
  (la misma de `volcanoes.yaml`), no la del catálogo GVP que dice el comentario del archivo.
- CONFIANZA: CONFIRMADO (medido en 5 figuras).
- GRAVEDAD: 2.

### H10. El falso positivo de Dubbi en los brazos "min" no es verificable: Dubbi no está en el archivo de MIROVA y el cúmulo está a 0,9 km del borde de la caja
- ARCHIVO:LÍNEA: `apendice_a.yaml` caso A4 (13.579, 41.809, "único que MIROVA no monitorea");
  JSON brazos B22 min: 19:30 2,07 MW a 4,10 km; 22:15 0,13 MW a 3,56 km.
- QUÉ PASA: es el único negativo que separa los brazos "min" de los "max". Su veredicto depende de
  una coordenada sin cotejo y de un radio que la sección 2 mostró frágil. No se puede decidir la
  conectiva con este caso.
- CONFIANZA: SOSPECHA (no hay dato independiente para el centro de Dubbi).
- GRAVEDAD: 2.

### H11. La línea base de la batería no es la configuración de producción para Villarrica
- ARCHIVO:LÍNEA: `conformidad_apendice.py:115` (`local_kernel_bg_compatible=FONDO_LOCAL`, False en
  producción-batería para los nueve); `volcanoes.yaml` Villarrica `local_kernel_bg: True`; flag
  efectivo `pipeline.process_modis.ENABLE_LOCAL_KERNEL_BG = True` (verificado con
  `VRP_PROFILE=mirova_equivalent python -c ...`).
- QUÉ PASA: el yaml lo declara deliberado ("geometría uniforme"), y A6 se verificó aparte con la
  configuración operacional. Pero el brazo "hoy" de la batería no es "hoy" para el único volcán
  chileno del apéndice, y el brazo "fondo local" lo enciende uniforme para nueve volcanes cuando
  producción lo tiene en 5 de 11. Lo anoto para que el A/B (sección 4) declare explícitamente el
  fondo del control por volcán.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2.

### H12. Las listas focal/nevado de S114 y S131 no coinciden
- ARCHIVO:LÍNEA: `scripts/build_c2ab_windows.py:41-42` contra
  `experiments/_s114_audit/discriminant_sweep.py:28-29`.
- QUÉ PASA: un A/B "estratificado focal/nevado" puede dar veredictos distintos según cuál lista use.
  El pre-registro fija la de S131.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

---

## 6. VERIFICADO LIMPIO

Lo que miré y está sano, con el comando que lo confirma:

- **La reimplementación de `evaluar_caso` es fiel**: 72 de 72 veredictos commiteados reproducidos y
  48 de 48 positivos caen a FN con radio 0,01 km. `python experiments/_s138_audit/eje5/romper_bateria.py`
  (bloque "CONTROL DE IDENTIDAD"). Todo lo demás de este informe se apoya en eso.
- **La medición de figuras responde a los controles**: positivo sintético (10,13 km, 90 y 0
  grados), escala invertida (rumbo 180), 2 km por celda (20,26 km), panel vacío ("sin máscara"), y
  los tres negativos reales sin máscara. `python experiments/_s138_audit/eje5/medir_9_figuras.py`.
- **La batería sí procesa la pasada de cada figura**: las nueve pasadas de los títulos (tabla 1.1)
  aparecen en las `pasadas` de los ocho JSON (verificado en el volcado de `romper_bateria.py`,
  columna `publica_en_fig`; para los negativos en `out/negativos_control_nti_a2.txt`). El problema
  es que no la distingue, no que no la tenga.
- **Los ocho brazos están completos**: 9 casos por brazo, 0 indeterminados, ninguna pasada con
  excepción (`comparar_brazos_apendice.py experiments/_s136` y `... experiments/_s137`, y el
  volcado de este eje). `COMPARACION_8_BRAZOS.txt` coincide con lo recomputado.
- **Los negativos de producción fallan en la pasada del autor**, no por mezcla de pasadas: A4 19:30,
  A7 10:40, A9 01:15 publican (`out/negativos_control_nti_a2.txt`). Ese 0/3 es real.
- **Cinco de los seis positivos del autor están en la cumbre** (0,12 a 0,70 km de la coordenada
  actual con el centro de MIROVA): la premisa "el autor detecta el cráter" vale para A1, A3, A5, A6 y
  A8. Sólo A2 es distinto, y ya estaba anotado en S137.
- **El loader del holdout funciona y la referencia cubre la ventana**: CONS hasta 2026-09-07, OCR
  hasta 2026-09-07, `latest_consolidado.csv` hasta 2026-09-13; Villarrica y Láscar > 0 noches.
  `python experiments/_s138_audit/eje5/holdout_noches.py`.
- **Flags efectivos de producción leídos del módulo, no del YAML** (A89):
  `ENABLE_TESTS_23_PROSE_BRANCH=False`, `ENABLE_MODIS_B22_PRIMARY=False`,
  `ENABLE_LOCAL_KERNEL_BG=True`, `PATH_D_ONLY_CAP_MW=5.0`, `NTI_BT_SANITY_K=3.0`.
  `VRP_PROFILE=mirova_equivalent python -c "import pipeline.process_modis as pm; print(pm.ENABLE_TESTS_23_PROSE_BRANCH, pm.ENABLE_MODIS_B22_PRIMARY, pm.ENABLE_LOCAL_KERNEL_BG, pm.PATH_D_ONLY_CAP_MW, pm.NTI_BT_SANITY_K)"`.
- **Nada del repo cambió**: `git status --short` muestra sólo `docs/audit_s138/` y
  `experiments/_s138_audit/` sin trackear, que son las salidas de los ejes.

Lo que NO miré y no hay que dar por auditado: el cableado de los brazos dentro de `calculate_vrp`
(si `ENABLE_MODIS_B22_PRIMARY` realmente cambia la banda en cada uno de los 13 sitios de la
compuerta; es materia del eje que audita "declarado contra efectivo"), la geometría del remuestreo,
y por qué MIROVA publica tan poco MODIS desde julio.

---

## 7. Resumen (menos de 400 palabras)

La batería del Apéndice A no mide "publicamos el objeto que el autor detectó". Mide "publicamos
algo con VRP > 0 a menos de 5 km de la cumbre en alguna pasada nocturna de esa fecha UTC". Con eso,
el 6/6 de producción vale cero como evidencia de fidelidad: de sus seis conformes, ninguno se puede
verificar como el objeto del autor (el JSON no guarda posición) y dos son con certeza otro objeto.
En A1 el autor marca dos celdas en la cumbre y nosotros, en su misma pasada, publicamos 42 píxeles
con el tope de 5 MW del camino D a 4,2 km; en A2 el autor marca la fisura a 11 km al este y
nosotros un cúmulo a 3 km al sureste. Sus tres falsos positivos sí ocurren en la pasada del autor:
ese 0/3 es real.

El mejor brazo de S137 (B22, sin compuerta, fondo local, prosa) sale mejor parado de lo que la
batería le anota: sus cinco conformes son el objeto del autor, medido por posición, y el sexto (A2)
también lo encuentra, a 2,5 km del centroide de una máscara de cuatro celdas, fuera de la caja de
5 km. Pero el instrumento es frágil: producción cae a 4/6 con radio 3 km y sólo la pasada de la
figura; el mejor brazo pasa a "cumple" con radio 8 km o con la referencia en el autor; el 6/6 de
otro brazo depende de una pasada de la noche anterior con un cúmulo a 11,5 km del objeto; y el único
negativo que separa "min" de "max" (Dubbi) está a 0,9 km del borde de la caja, sin centro
verificable. El control de validez por NTI lo pasan 16 a 18 de las 24 pasadas: no controla nada.

La batería sirve como verificación de fidelidad por objeto y por pasada (sección 3); no sirve
para decidir la adopción. Para eso está el pre-registro de la sección 4, condicionado por un
hallazgo: entre junio y agosto de 2026 MIROVA publicó alertas MODIS en un solo volcán (Láscar, 15
noches) y ninguna en los nevados. La pérdida cero se define entonces contra noches confirmadas por
cualquier sensor (316 noches, 64 en nevados), pareada por noche, con IC bootstrap para la
sobre-detección y predicciones escritas (P1 a P4) que dicen qué resultado refuta cada brazo.

Ruta del entregable:
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\audit_s138\EJE_5_bateria_apendice_instrumento.md`.
Scripts y salidas:
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s138_audit\eje5\`
(`medir_9_figuras.py`, `romper_bateria.py`, `holdout_noches.py`, `out/`).
