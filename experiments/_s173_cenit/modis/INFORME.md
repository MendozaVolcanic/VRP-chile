# S173 cenit MODIS de Chillán: qué pieza de la vía «código MIROVA» corrige la caída oblicua

## 1. Encabezado

- Hora del servidor (header `Date` de la API de GitHub): inicio Tue, 03 Nov 2026 00:42:18 GMT; última medición
  Tue, 03 Nov 2026 01:01:48 GMT.
- Commit medido: `origin/main` 5de08ebf62d1ea092c485c0a030f323f2cbdcf2a (worktree disperso propio en
  `C:/Users/nmend/vrp-wt/s173_cenit_modis_wt`, borrado al terminar). Antecedentes leídos de `origin/loop/activo`
  ddd83c5b901e46451dfc0e422656162ad29a29cc.
- Modelo: Claude Opus 5.5 (claude-opus-5-5). Esfuerzo: mi sesión no lo expone como valor verificable (SIN DATO); es el
  que fijó quien me lanzó, y conviene que lo confirme desde su llamada.
- CARPETA: `C:/Users/nmend/vrp-wt/s173_cenit/modis/` (scripts y salidas lado a lado; `_ref_*` son copias de lectura).
- Rama `claude/s173-cenit-modis` (commit f57972af6, desde `origin/main`) y PR en borrador
  https://github.com/MendozaVolcanic/VRP-chile/pull/937. No despaché nada, no mergeé, no toqué `pipeline/`, `data/`
  ni `frontend/`.
- Qué NO miré: VIIRS 375 y VIIRS 750; el detector de K por dentro (no lo reemplacé por pieza, ver SIN DATO); los
  gránulos de las 27 pasadas (no bajé nada de NASA); los otros diez volcanes salvo lo que trae el lote S162 (Láscar,
  Llaima); ningún paper; la ablación «hacia adelante» (K más una pieza de la vía); el día.

## 2. En una pantalla

1. No hay una pieza única. Cuando el satélite mira el domo de lado, el calor del foco queda repartido en un píxel
   grande. Si a la vía MOD-D le devuelvo cualquiera de tres piezas de K, la caída oblicua vuelve: el fondo del anillo
   recortado a cero (D25), el cálculo sin remuestrear con área de nadir (D17) o la geolocalización de 5 km. En Chillán, con el fondo de K, la razón
   sobre 30° cae de 1,075 a 0,014 (n 10, grillas del A/B de MOD-D); en el lote nativo, sin remuestreo, cae de 0,992 a
   0,52 (n 6, Láscar y Chillán, cenit confundido con volcán).
2. El fenómeno del fondo, medido: el anillo de 5 a 25 km está 7 a 8 K más tibio que el fondo local de la cumbre en
   todos los cenit, y el exceso del foco sobre el fondo local cae de 13,3 K (z < 30) a 5,1 K (z ≥ 30); en 5 de las 10
   pasadas oblicuas ninguna celda alertada supera al anillo, y el recorte a cero las borra.
3. El halo del fondo y la suma de todos contra el cúmulo no son la palanca (sin tendencia con el cenit).
4. Las salidas existentes no contestaban: la ablación S162 es del bow tie (D28, que ni K ni la vía tratan) y sus 3
   alertas de Chillán están sobre 50°. La de Chillán con D17 sobre sus propias pasadas queda preparada (PR #937), sin correr.
5. Producción ya lo confirma en dos pasadas: con la vía, el 2026-11-02 a 41,4° y 52,0° la razón es 1,189 y 1,114.

Informe: `C:/Users/nmend/vrp-wt/s173_cenit/modis/INFORME.md`

## 3. El fenómeno, antes que los números

El domo de Chillán está en una cumbre más fría que los valles que la rodean. De noche, un píxel MODIS centrado en el
cráter ve roca fría con un foco pequeño muy caliente; el exceso de radiancia MIR del píxel es la potencia del foco
repartida en el suelo que cubre ese píxel. A 2° de cenit el píxel cubre ~1 km²; a 58° cubre varias veces eso, y el
mismo foco produce un exceso por píxel varias veces menor (el foco no cambió, se diluyó).

La vía MOD-D, como MIROVA, hace tres cosas que K no hace y las tres compensan esa dilución:
- interpola el gránulo a una grilla fija de 1 km y cuenta cada celda con 1 km²: el píxel grande se reparte en varias
  celdas y la suma recupera el área (D17);
- resta un fondo local, interpolado bajo el cúmulo desde las celdas vecinas de la cumbre, que es tan frío como la
  cumbre: el exceso diluido sigue siendo positivo (D25);
- ubica cada píxel con la geolocalización de 1 km del MxD03, no con la de 5 km interpolada, que corre las posiciones.

K cuenta el píxel nativo con el área del nadir (pierde el factor de área) y le resta la mediana de un anillo de 5 a
25 km, que está 7 a 8 K más tibio: el exceso diluido de la pasada oblicua queda por debajo del anillo y el recorte a cero lo
anula. Por eso la caída no es lineal: a 58° no es «menos VRP», es «nada», y por eso se pierden las alertas protegidas.

## 4. Respuesta a la pregunta (1): qué hace `03_ablacion.py` de S162

Leído en `origin/loop/activo:experiments/_s162_modis_bowtie/real/03_ablacion.py` y `comun.py`:
- Aísla UNA pieza que no es D17 ni D25: el bow tie (D28), es decir, quitar del barrido los píxeles que el barrido vecino
  ya cubre, con cinco métodos (`A_centro_cubierto_ant`, `A_centro_cubierto_sig`, `A_huella_entera_ant`,
  `B_filas_borde`, `C_sin_det0`) contra `todos` (`comun.py`, `ORDEN_METODOS` y `mascara_quitar`).
- Insumos: los 403 recortes nativos del lote 40120713181 (`nativo_NNNN.npz`, con B21, B22, B31, lat/lon del MxD03 y
  de 5 km, cenit por píxel), los resultados del lote y el port `fisica` de S159 (`experiments/_s159/portes/mirova_port.py`,
  anterior a la regla de empates del fondo de S163).
- Sí incluye Chillán: 39 pasadas, 3 con detección del port, las 3 alertas protegidas y las 3 sobre 50° (2026-10-01
  08:35 z 50,5; 10-15 01:05 z 57,6; 10-12 07:20 z 58,2); bajo 30° hay 11 pasadas de Chillán y ninguna con detección
  (`01_salida.txt`). Partirla por cenit no responde: no hay alerta de Chillán bajo 30° en el lote y el bow tie no es
  una diferencia entre K y la vía (CMODIS-05).
- Lo que sí sirve del lote son sus recortes nativos: con ellos corrí la ablación de D17 en Windows (03).

## 5. Mediciones (con las dos preguntas del instrumento)

Estadística común: razón = VRP publicado (K) o VRP del brazo / VRP de MIROVA en la misma pasada; Spearman razón contra
cenit con 200 barajados del cenit (semilla 173), rango 95 % del barajado entre corchetes (`_estadistica.py`).

### 01, lista de pasadas y salidas existentes (`01_pasadas_y_salidas_existentes.py` → `01_salida.txt`, `01_salida.json`)
- Insumo: `s02_pareo_por_pasada.py` de S172, reutilizado sin cambios (sha256 igual al de la rama salvo CRLF), corrido
  sobre la copia de `origin/main` de hoy, ventana 2026-04-01 a 2026-11-02 (`s02_v_main_salida.txt`,
  `s02_v_main_pasadas.csv`). Cenit = `sensor_zenith_deg` del record (`scripts/banco_paridad.py:286`).
- P1: control positivo, razón = cos(z) da Spearman −1,0; reproduce el de S172 en su ventana (−0,867, n 12). P2: el
  barajado; s02 trae su control de referencia corrida un día (MODIS 0 pares).
- 27 pasadas MODIS con alerta (25 escritas por K y 2 por la vía). K, ventana de S172: 12 pares, Spearman −0,867
  [−0,608; 0,538], z < 30 0,749 (n 6), z ≥ 30 0,204 (n 6), 4 alertas sin publicar (las 4 a 57,6 a 58,4°). Hasta el
  2026-11-02: 20 pares, −0,866 [−0,422; 0,48], 0,678 (n 10) y 0,204 (n 10), 5 sin publicar.
- Brazo V del A/B de MOD-D (`modd_resultado_f4.json`, copia de `origin/loop/activo`, sha256 312e2050…): 12 pares,
  Spearman +0,497 [−0,601; 0,538], z < 30 0,926, z ≥ 30 1,1; con las 4 recuperadas (16) +0,15 [−0,468; 0,429]. El
  cociente V/K crece con el cenit de 0,99 a 10,57 (Spearman +0,944 [−0,636; 0,448]).

### 02, ablación de magnitud sobre las grillas capturadas de Chillán (`02_ablacion_grillas_chillan.py` → `02_salida.txt`)
- Insumo: las grillas 51 × 51 que guardó el A/B de MOD-D (`D:/vrp-trabajo/temporales/s170_ab*/*/grillas/
  grilla_NevadosDeChillan_<fecha>.npz`), 16 de las 25 pasadas K (las 9 del 2026-10-27 al 10-31 no tienen grilla).
- P1: V0 recalculado da la máscara capturada en 16 de 16 y el VRP capturado a 4,45e-4 MW (redondeo a 3 decimales; por
  `procesar_grilla` con el patch, 0 de diferencia); V0 / MIROVA = razon_b de la lectura en 16 de 16; X2 dobla el VRP
  sin mover celdas en 16 de 16; FA y FSH cambian el VRP en 16 de 16. La grilla capturada es la de
  `grilla_del_volcan` de main en 16 de 16. P2: SC no cambia nada en 0 de 16 (un solo cúmulo en todas): un brazo que no
  actúa da V0 exacto, y eso se ve. Fidelidad de FA al fondo de K: t_bg del anillo en la grilla menos t_bg_k del
  record K, mediana −0,02 K, rango [−2,10; +0,81] K (n 16).
- Publicación con el predicado del tablero (node sobre `frontend/index.html` de main).

| brazo (n 16) | Spearman [barajado] | z < 30 (n 6) | z ≥ 30 (n 10) | publica |
|---|---|---|---|---|
| K (no publicada = 0) | −0,907 [−0,521; 0,502] | 0,749 | 0,107 | 12 |
| V0 (la vía) | +0,150 [−0,479; 0,562] | 0,926 | 1,075 | 16 |
| FA (fondo de K) | −0,546 [−0,478; 0,412] | 0,47 | 0,014 | 11 |
| FSH (sin halo) | −0,121 [−0,535; 0,438] | 0,926 | 1,032 | 16 |
| SC (sólo cúmulo) | igual a V0 | 0,926 | 1,075 | 16 |
| FA_SC | igual a FA | 0,47 | 0,014 | 11 |

Celdas alertadas por la vía contra el cenit: Spearman +0,197 [−0,572; 0,455], medianas 4,5 y 7,0: el conteo de la
grilla no crece en proporción al área del píxel.

### 02b, el fondo en temperaturas (`02b_temperaturas_grilla.py` → `02b_salida.txt`)
- P1: el exceso local promedio es positivo en 16 de 16 (son alertas de la vía). P2: si el anillo fuera el fondo local,
  «anillo menos local» daría 0; da 7 a 8 K.
- Anillo menos fondo local: Spearman −0,138 [−0,465; 0,479], medianas 8,22 K (z < 30) y 7,28 K (z ≥ 30): no depende del
  cenit. Exceso sobre el fondo local: −0,756 [−0,503; 0,456], 13,27 y 5,12 K. Exceso sobre el anillo: −0,732
  [−0,497; 0,447], +5,27 y −2,51 K. Celdas alertadas sobre el anillo: 0 de 6 (10-10 07:40), 0 de 5 (10-15 01:05),
  0 de 9 (10-25 07:20), 0 de 3 (10-12 07:20), 0 de 1 (09-29 07:20).

### 03, ablación sobre recortes nativos del lote S162 (`03_ablacion_nativa_lote.py` → `03_salida.txt`, `03_salida.json`)
- Insumo: 403 pasadas evaluables del lote (C:\vrp-trabajo\temporales\s162_negmodis\run_40120713181), 11 alertas
  protegidas (8 Láscar a 2,4 a 40,5°, 3 Chillán a 50,5 a 58,2°). Ventana de los datos: 2026-03-01 01:35 a 2026-10-21 08:05 (403 pasadas).
- P1: V0 = port del lote en npix en 403 de 403; en VRP difiere en 6 (ids 65, 75, 97, 141, 1120, 1251), y 03c muestra
  que es la triangulación del fondo: con Qhull el VRP es el del port en 6 de 6 (`03c_salida.txt`). X2 = 2 × V0 en 13 de
  13. NAT cambia npix o VRP en 13 de 403 (las 13 con detección). P2: SC cambia 0 de 403.
- Protegidas (n 11), razón contra MIROVA:

| brazo | Spearman [barajado] | z < 30 (n 5) | z ≥ 30 (n 6) | protegidas que publica |
|---|---|---|---|---|
| K (record del lote) | −0,788 [−0,460; 0,528] | 0,549 | 0,174 | |
| V0 | +0,155 [−0,591; 0,609] | 1,074 | 0,992 | 11 |
| FA | −0,633 [−0,510; 0,620] | 0,48 | 0,243 | 9 |
| FSH | +0,100 [−0,673; 0,591] | 0,969 | 0,973 | 11 |
| RN (vecino más cercano) | −0,473 [−0,564; 0,609] | 1,313 | 0,9 | 11 |
| G5 (geolocalización 5 km) | −0,401 [−0,624; 0,524] | 0,699 | 0,171 | 9 |
| NAT (sin remuestreo, 1 km²) | −0,815 [−0,510; 0,492] | 1,246 | 0,52 | (sin record) |
| NAT_AREA (sin remuestreo, 1/cos³) | −0,169 [−0,633; 0,597] | 1,249 | 1,184 | (sin record) |

Las 3 protegidas sobre 50° son las 3 de Chillán: en esta población el cenit está confundido con el volcán.

### 04 y 05, lista para el workflow y prueba del arnés
- `04_lista_para_workflow.py` escribe `pasadas_chillan_modis.json` de la rama (27 pasadas, 16 con razón V de la lectura).
- `probar_local.py` (rama) en Windows: 0 fallas, incluidas las 16 grillas capturadas (`probar_local_salida.txt`).
- `05_mutaciones_prueba_local.sh` → `05_salida.txt`: sin mutar 0 fallas; patch que ignora el brazo 3; X2 que no dobla
  1; anillo desde 0 km 0; caja nativa toda sensible 0 (CMODIS-08).
- Guards de workflows de `tests/` sobre la rama: 101 pasan, 6 saltados (`guards_workflow_salida.txt`).

## 6. Hallazgos (orden por gravedad)

### CMODIS-01
- TÍTULO: Con el fondo de K, la vía MOD-D vuelve a hundir a Chillán en las pasadas oblicuas (D25 es palanca)
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `02_ablacion_grillas_chillan.py` : `02_salida.txt` (tabla de brazos); fondo de K en
  `pipeline/process_modis.py:717` (anillo) y `:1253` (recorte a cero) de main 5de08eb; fenómeno en `02b_salida.txt`
- QUÉ PASA: la cumbre de Chillán es más fría que el anillo de 5 a 25 km (7 a 8 K, en todos los cenit). Con la pasada
  oblicua el exceso del foco sobre la cumbre baja de 13,3 a 5,1 K, y contra la mediana del anillo queda bajo cero:
  restando el fondo de K con el recorte a cero, sobre la detección de la vía, la razón cae a 0,014 sobre 30° (n 10)
  contra 1,075 de la vía, y se pierden 5 de 16 publicaciones (las 4 de 57,6 a 58,4° y la de 35,1°). También baja el nadir (0,47
  contra 0,926).
- CÓMO SE VE EN EL DASHBOARD: con K, una pasada MODIS oblicua de Chillán aparece como actividad cinco a diez veces
  menor o no aparece; con la vía no.
- CÓMO REPRODUCIRLO: `python -B 02_ablacion_grillas_chillan.py <copia de main>` en CARPETA; ej. NdC MODIS_AQUA
  2026-10-25 07:20 UTC (z 58,0: V0 2,55 MW, FA 0,00) y MODIS_TERRA 2026-10-16 01:40 (z 3,2: V0 13,10, FA 7,74).
- CONFIANZA: CONFIRMADO (medido; es ablación hacia atrás sobre las grillas de la vía, FA aproxima el anillo de K sobre
  celdas de la grilla, con t_bg a −0,02 K de mediana del de K)
- GRAVEDAD 1-5: 4

### CMODIS-02
- TÍTULO: Sin remuestrear (área de nadir por píxel nativo, como K) la vía también vuelve a caer con el cenit (D17 es palanca)
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `03_ablacion_nativa_lote.py` : `03_salida.txt` (filas NAT y NAT_AREA); remuestreo de
  la vía en `pipeline/mirova_v750_codigo.py` (`remuestrear_grilla`, l. 198 en main 5de08eb)
- QUÉ PASA: el píxel oblicuo cubre más suelo; la grilla lo copia en varias celdas de 1 km² y la suma recupera el área.
  Corriendo el mismo detector, fondo y suma de la vía sobre los píxeles nativos con 1 km² cada uno, la razón sobre 30°
  cae a 0,52 (n 6) contra 0,992, Spearman −0,815 (fuera del barajado), y dos alertas protegidas de Chillán (57,6° y
  58,2°) no detectan. Con el área de cada píxel nativo (1/cos³) la tendencia desaparece (Spearman −0,169, z ≥ 30
  1,184), salvo esas dos que siguen sin detección: el remuestreo también decide la detección, no sólo el área.
- CÓMO SE VE EN EL DASHBOARD: igual que CMODIS-01.
- CÓMO REPRODUCIRLO: `python -B 03_ablacion_nativa_lote.py <copia de main>`; NdC MODIS_AQUA 2026-10-01 08:35 (V0 5,721,
  NAT 2,796, NAT_AREA 10,876), MODIS_TERRA 2026-10-15 01:05 y MODIS_AQUA 2026-10-12 07:20 (NAT 0).
- CONFIANZA: CONFIRMADO el número; que valga para Chillán bajo 30° es SOSPECHA (en esta población los 3 casos
  oblicuos son de Chillán y los de bajo 30° de Láscar). Lo resuelve el workflow del PR #937.
- GRAVEDAD 1-5: 4

### CMODIS-03
- TÍTULO: La geolocalización de 5 km (la de K) dentro de la vía baja la razón en todos los cenit, y más en los oblicuos
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `03_salida.txt` (fila G5); `pipeline/mirova_v750_codigo.py::leer_geo_mxd03`
  (docstring: la interpolada corre las posiciones 1 a 3 km hacia el nadir)
- QUÉ PASA: con las posiciones de la grilla de 5 km el foco cae en otras celdas: protegidas z < 30 0,699 y z ≥ 30
  0,171 (V0: 1,074 y 0,992); publica 9 de 11; Chillán 2026-10-01 08:35 0,06 de V0, 10-12 07:20 0. Aparecen 2
  publicaciones nuevas en negativos a más de 60° (`03b_salida.txt`).
- CÓMO SE VE EN EL DASHBOARD: magnitud menor y, a veces, cúmulo fuera de la cumbre.
- CÓMO REPRODUCIRLO: igual que CMODIS-02; Láscar MODIS 2026-04-07 07:35 (z 11,3: V0 1,878, G5 0,434).
- CONFIANZA: CONFIRMADO (medido en el lote, no en las pasadas de Chillán bajo 30°)
- GRAVEDAD 1-5: 3

### CMODIS-04
- TÍTULO: La pregunta «D17 o D25» es una falsa disyuntiva en MODIS: cada una sola reproduce la caída al quitarla
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `02_salida.txt` y `03_salida.txt`
- QUÉ PASA: las tres piezas (fondo, remuestreo con área, geolocalización) son cada una necesaria para que la vía quede
  plana con el cenit. Lo medido es hacia atrás (quitar una pieza a la vía). Si a K le agrego una sola, no se midió, y
  sumar los efectos de piezas que interactúan no es válido: el fondo de K sólo es dañino porque el foco quedó diluido.
  Adoptar una pieza sobre K sin medirla así puede no curar nada.
- CÓMO SE VE EN EL DASHBOARD: invisible (es una decisión de diseño).
- CÓMO REPRODUCIRLO: comparar las filas FA, NAT y G5 de las dos tablas.
- CONFIANZA: CONFIRMADO lo de hacia atrás; lo de hacia adelante SIN DATO.
- GRAVEDAD 1-5: 3

### CMODIS-05
- TÍTULO: La tarea llama a D25 «geometría del borde del barrido»; en el catálogo D25 es el fondo, y el bow tie (D28) no separa K de la vía
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `docs/MIROVA_DIVERGENCES.md` de main, l. 2861 (TEXTO: «## D25: El fondo del VRP es la
  mediana de un anillo regional de 5 a 25 km»), l. 3034 (TEXTO: «## D28: El bow tie de MODIS no se trata en ningún paso
  del perfil operacional»); `pipeline/mirova_v750_codigo.py::remuestrear_grilla` interpola con todos los píxeles
- QUÉ PASA: si la palanca se buscara en «la geometría del borde» siguiendo el nombre de la tarea, se iría al bow tie, que
  ni K ni la vía quitan: no puede explicar por qué la vía es plana y K no. Es justo el riesgo de palanca equivocada
  que la tarea declara.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `git show origin/main:docs/MIROVA_DIVERGENCES.md | sed -n '2861p;3034p'`
- CONFIANZA: CONFIRMADO (leído)
- GRAVEDAD 1-5: 2

### CMODIS-06
- TÍTULO: El halo del fondo y la suma de todos los alertados contra el cúmulo no son la palanca
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `02_salida.txt` y `03_salida.txt` (FSH, SC)
- QUÉ PASA: sin halo la razón queda plana (Spearman −0,121 en Chillán, z ≥ 30 1,032); el cúmulo es único en las 16
  pasadas de Chillán y en las 403 del lote, así que sumar sólo el cúmulo da lo mismo.
- CÓMO SE VE EN EL DASHBOARD: nada.
- CÓMO REPRODUCIRLO: igual que CMODIS-01.
- CONFIANZA: CONFIRMADO
- GRAVEDAD 1-5: 2

### CMODIS-07
- TÍTULO: Las magnitudes del port en el lote S162 (y en `03_ablacion.json`) son anteriores a la regla de empates del fondo; no son las de la vía de hoy
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `03c_fondo_qhull.py` : `03c_salida.txt`
- QUÉ PASA: en 6 pasadas el VRP de la vía de hoy y el del port difieren (Llaima 2026-07-24 01:05: 0,114 contra 0,430
  MW, un píxel); con Qhull se reproduce el port en 6 de 6. Lo que se lea del lote como «magnitud de la vía» hereda esa
  diferencia; las razones del port contra MIROVA de `03_ablacion_salida.txt` de S162 no son las de producción.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python -B 03c_fondo_qhull.py <copia de main>`
- CONFIANZA: CONFIRMADO
- GRAVEDAD 1-5: 2

### CMODIS-08
- TÍTULO: La prueba local del arnés no atrapa dos defectos del arnés mismo
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `05_mutaciones_prueba_local.sh` : `05_salida.txt`
- QUÉ PASA: un anillo que arranca en 0 km (incluye la cumbre) y una caja nativa toda sensible pasan la prueba sin
  fallas. La primera la acota el control de t_bg contra K de 02 (mediana −0,02 K), la segunda no tiene control.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `bash 05_mutaciones_prueba_local.sh <worktree de la rama>`
- CONFIANZA: CONFIRMADO
- GRAVEDAD 1-5: 2

### CMODIS-09
- TÍTULO: Producción con la vía ya da razón cerca de 1 en dos pasadas oblicuas de Chillán
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `01_salida.txt` (pasadas 2026-11-02 01:15 y 07:30, `via True`)
- QUÉ PASA: a 41,4° y 52,0° la razón es 1,189 y 1,114, donde K daba ~0,2. n 2.
- CÓMO SE VE EN EL DASHBOARD: dos puntos MODIS de Chillán con magnitud del orden de la de MIROVA.
- CÓMO REPRODUCIRLO: `python -B 01_pasadas_y_salidas_existentes.py <copia de main>`
- CONFIANZA: CONFIRMADO
- GRAVEDAD 1-5: 1

## 7. SEGUIMIENTOS (fuera de mi eje)

- Una quinta alerta MODIS de Chillán sin publicar con K, 2026-10-30 07:15 (z 63,1°, 1,0 MW, sólo OCR), fuera de la
  ventana de S172 (`01_salida.txt`). Confianza CONFIRMADO; ya escrita por K, no por la vía.
- Sensibilidad del fondo de la vía a la triangulación en cúmulos de un píxel (×3,8 en Llaima 2026-07-24 01:05,
  `03c_salida.txt`): la regla de empates es la de S163 y está validada contra MATLAB; lo anoto porque un brazo de un
  píxel es frágil en cualquier A/B. Confianza CONFIRMADO el número.
- Que la grilla no cuente celdas en proporción al área (02: +0,197, n.s.) concuerda con la tarea 1.14 citada en
  `docs/SINTOMAS.md` l. 39 (TEXTO: «el Npix de MIROVA no crece hacia el borde»); no lo verifiqué contra MIROVA.

## 8. VERIFICADO LIMPIO

- El pareo de S172 reproduce en main de hoy su Spearman MODIS (−0,867, n 12) en su ventana: `01_salida.txt`. Vara: la
  salida de S172 (`s03_salida.json`, leída en su INFORME), no la mía.
- La vía de hoy sobre las grillas capturadas da exactamente lo que capturó el A/B de MOD-D (máscara 16 de 16, VRP al
  redondeo, razón 16 de 16): `02_salida.txt`. Vara: los npz del A/B y `modd_resultado_f4.json`.
- La grilla de MIROVA de Chillán de main es la del A/B (16 de 16): misma vara.
- Ni K ni la vía quitan duplicados del bow tie: la vía interpola con todos los píxeles (`remuestrear_grilla`), y D28
  dice que el perfil operacional no los trata (l. 3034). Vara: el código de main y el catálogo.
- El workflow nuevo pasa los guards de workflows del repositorio (101 pasan, 6 saltados): `guards_workflow_salida.txt`.

## 9. SIN DATO

- Ablación de D17 sobre las 27 pasadas de Chillán (con sus nativos): necesita el workflow del PR #937 en `main`
  (merge con frase de Nicolás) y despacharlo; no lo hice.
- Hacia adelante (K más una sola pieza de la vía): el detector de K corre sobre el barrido con su anillo y su
  segundo pase; no está en el arnés.
- Las 9 pasadas K del 2026-10-27 al 10-31: sin grilla capturada; entran al workflow.
- Publicación de NAT y NAT_AREA: no arman record (sólo magnitud).
- Esfuerzo de razonamiento de esta sesión: no visible.

## 10. FUERA DE ALCANCE

- VIIRS 375 y VIIRS 750 (otros frentes de S173). La vía de VIIRS 750 tiene su propia ablación (V750-C).
- Si la potencia de MIROVA misma cae con el cenit (lo que haría que razón ~1 no fuera «verdad»): ver S158 en
  `docs/SINTOMAS.md`; no lo medí.
