# Auditoría S173: ¿la magnitud baja de Tupungatito VIIRS 375 es el mismo mecanismo que en Chillán?

## 1. Encabezado

- Hora del servidor: inicio Tue, 03 Nov 2026 02:30:17 GMT; última medición 02:40:06 GMT (header `Date` de la API de
  GitHub).
- Commit medido: `origin/main` f20495d374dc868a3dd789d1e16f662fd24c6210 (`COMMIT_MAIN.txt`): records K de
  `data/mirova_equivalent/Tupungatito.json`, referencia de MIROVA, pipeline/, scripts/, frontend/ y volcanoes.yaml,
  copiados por `git archive` en `C:/Users/nmend/vrp-wt/s173_cenit/tupun375/repo/` (se deja para reproducir). Antecedente
  y scripts reusados: `origin/loop/activo` b9da9adb0 (`experiments/_s173_cenit/README.md`) y las carpetas
  `C:/Users/nmend/vrp-wt/s173_cenit/v375/` y `modis/`. Auto-audit: `data/audit_continuous/latest.json` de origin/main
  (generado 2026-11-02T19:29:57Z, copia en `_auto_audit_latest.json`).
- Modelo: Claude Opus 5.5 (claude-opus-5-5). Esfuerzo: bajo, el que fijó la configuración de esta sesión (no lo elegí).
- CARPETA: `C:/Users/nmend/vrp-wt/s173_cenit/tupun375/`
- Qué NO miré: MODIS y VIIRS 750 de Tupungatito (sólo anoto lo que salió de pasada en s01); los otros volcanes; el día;
  gránulos L1B (no bajé nada); el remuestreo aislado (D17) sobre el barrido nativo; los TIF de MIROVA; ningún paper; la
  sombra de V375-E (vacía por diseño hasta el 2026-11-03 según el README de S173, no lo re-verifiqué); el lector sellado
  y sus mutaciones; el pixel a pixel de qué celdas suma K contra qué celdas suma la vía.

## 2. En una pantalla

1. Sí, es el mismo mecanismo que en Chillán, pero con el NIVEL dominando: K pierde 59 % ya cerca del nadir (0,41 bajo 30°)
   y cae a 0,24 sobre 30° (Spearman −0,52, fuera del barajado; 168 pares por pasada, 2026-02-14 a 2026-11-02). MIROVA es
   plana en magnitud con el cenit (0,17 contra 0,16 MW).
2. V375-E sobre los mismos gránulos queda en 1,01 / 1,02 sin pendiente (23 pasadas, 2026-04-04 a 2026-09-18); V375-E / K
   sube de 2,34 a 3,93 (Spearman +0,65, fuera).
3. La pieza es el fondo: con la máscara y la grilla de la vía, cambiar sólo el fondo por el `t_bg` (mediana del anillo
   5 a 25 km) del record K de la misma pasada, con recorte a cero, reproduce a K: 0,415 / 0,246 contra 0,394 / 0,251 de K
   (K / ese brazo = 1,02). El anillo está 6,9 K más tibio que el fondo local de la cumbre en los dos tramos; el exceso del
   foco débil es de sólo 10,6 K de nadir y 8,5 K de lado: el anillo se come casi todo de frente y más de lado.
4. Las 11 alertas de MIROVA que K no publica están todas a 48° o más; 9 son el cráter con todos los píxeles en 0 MW.
5. Las cuatro alertas grandes (1,25 a 2,51 MW, sólo OCR de Suomi NPP antes del 2026-10-09) son fuentes a 9 a 25 km del
   cráter según la vía: referencia sospechosa, incluidas las dos «protegidas sin publicar» del auto-audit.

Informe: `C:/Users/nmend/vrp-wt/s173_cenit/tupun375/INFORME.md`

## 3. El fenómeno, antes que el número

Tupungatito es una cumbre de unos 5.600 m cubierta de glaciar, con un lago cratérico y fumarolas: la señal térmica es
débil y persistente, unas décimas de MW. De noche, la cumbre helada está fría (mediana I4 de la cumbre, 244 K) y los
valles a 5 a 25 km están más tibios (249 K en la grilla). El foco del cráter, visto por un píxel de 375 m, sólo sube unos
9 a 11 K sobre su entorno inmediato.

MIROVA mide el exceso del foco contra su entorno inmediato (interpola el fondo bajo los alertados, fuera de un halo). K lo
mide contra la mediana del anillo de 5 a 25 km, que en Tupungatito cae en los valles tibios, unos 7 K por encima del
entorno del cráter, y recorta a cero lo que quede negativo. Con un exceso de 10 K y un fondo 7 K demasiado alto, K se
queda con un tercio de la energía aun mirando de frente: eso es el NIVEL. De lado, el píxel se estira en el terreno y el
calor del foco se diluye: el contraste cae a unos 8,5 K, pero el error de fondo sigue en 7 K, y lo que queda es aún
menos, o cero: eso es la PENDIENTE, y es lo mismo que el README de S173 describe en Chillán. La diferencia con Chillán es
la escala de la señal: en Chillán el domo en erupción tiene contraste grande y el error de fondo de 7 a 8 K pesa poco de
frente (K 0,75 de nadir); en Tupungatito el mismo error de fondo es comparable a la señal y domina.

## 4. Mediciones (cada una con sus dos preguntas)

Razón = VRP publicado por K (predicado del tablero ejecutado con node, `banco_paridad.cargar_nuestros`; `disp`) / VRP de la
fila ALERTA de MIROVA de la misma pasada (±120 s, unión CONS+OCR con D-9 SN, CONS si existe). Cenit = `sensor_zenith_deg`
del record K (el de la vía difiere a lo más 1,82°, `s03_v375e_resumen.json`). Barajado: 200, semilla 173, dentro del
sensor (un solo sensor, VIIRS 375). Tramos < 30° y >= 30°, más 30 a 50 y >= 50 como detalle.

### s01: pareo por pasada de K (`s01_pareo_k.py`, copia de `s02_pareo_por_pasada.py` de S172 con el volcán por variable)
- Salidas: `s01_k_resumen.json`, `s01_k_pasadas.csv` (2.718 records nocturnos), `s01_k_stderr.txt` (avisos A119).
- Ventana de los datos: 2026-02-14 (primer dato de Tupungatito en la tabla, A119) a 2026-11-02.
- P1: ×2 dobla la mediana (0,335 a 0,671); identidad del predicado `[0,1,1,1,0]`, `[1,0]`; lectura directa del JSON
  contra node: 0 diferencias; desfase máximo de hora del par: 2 s. P2: con la referencia corrida un día quedan 55 pares de
  168: el nulo NO es limpio, porque Tupungatito tiene señal casi todas las noches y la órbita se repite dentro de ±120 s
  (es el límite que S172 ya dejó escrito para Chillán). No uso este control como prueba de nada.
- VIIRS 375: 1.086 pasadas nocturnas, 179 con alerta de MIROVA, 168 pares, razón mediana 0,335 (por noche 0,361, 120
  noches). Sólo tabla: 135 pares, 0,336.

### s02: K por tramo de cenit (`s02_estratos_k.py`, `s02_salida.json`, `s02_salida.txt`)
- P1: control positivo de pendiente, razón × cos²(z): Spearman de −0,522 a −0,799, fuera del barajado. P2: rango del
  barajado al lado de cada Spearman; con n < 8, SIN DATO; n impreso por conjunto.

| conjunto (ventana de los pares) | n | z < 30 | z >= 30 | 30 a 50 | z >= 50 | Spearman [barajado 95 %] |
|---|---|---|---|---|---|---|
| U unión, 2026-02-14 05:48 a 2026-11-02 06:18 | 168 | 0,429 (82) | 0,243 (86) | 0,228 (51) | 0,251 (35) | −0,522 [−0,140; +0,159] |
| C sólo tabla, 2026-02-14 a 2026-11-02 | 135 | 0,440 (66) | 0,241 (69) | 0,229 (44) | 0,244 (25) | −0,570 [−0,176; +0,173] |
| U sin sospechosas (U-S) | 145 | 0,412 (73) | 0,243 (72) | 0,229 (44) | 0,247 (28) | −0,516 [−0,156; +0,155] |
| S sospechosas (sólo OCR Suomi NPP antes del 2026-10-09), aparte | 23 | 0,521 (9) | 0,231 (14) | 0,134 (7) | 0,272 (7) | −0,550 [−0,433; +0,395] |
| C desde 2026-04-01 | 107 | 0,448 (55) | 0,256 (52) | 0,270 (36) | 0,248 (16) | −0,601 [−0,211; +0,167] |
| C desde 2026-06-13 | 51 | 0,542 (28) | 0,332 (23) | 0,336 (17) | 0,305 (6) | −0,569 [−0,256; +0,261] |

- Por plataforma (U): NOAA-20 −0,552 (fuera), NOAA-21 −0,571 (fuera), Suomi NPP −0,436 (dentro de [−0,455; +0,316], n 31).
- La razón casi no depende de la magnitud de MIROVA (Spearman −0,156; terciles 0,372 / 0,336 / 0,303) y la magnitud de
  MIROVA no depende del cenit (Spearman +0,026; mediana 0,17 MW bajo 30°, 0,16 sobre 30°): la caída es de K.
- Selección (todas las pasadas desde 2026-04-01, no sólo pares): MIROVA alerta en 28 % de las pasadas bajo 30°, 18 % entre
  30 y 50 y 7,7 % sobre 50; K publica en 48,5 / 39,7 / 11,5 %. Las razones están condicionadas a que MIROVA haya alertado.
- Reconciliación con el auto-audit (ventana 2026-09-03 a 2026-11-02): 34 pares por pasada, 0,334 (0,448 / 0,281,
  Spearman −0,489 fuera); por noche con la pasada de mayor VRP de MIROVA, 24 noches, 0,324. El 0,371 n 25 del auto-audit es
  máximo sobre máximo por noche, otra definición; los dos dan el mismo orden.

### s03 y s04: V375-E sobre los lotes retrospectivos (`s03_v375e_retro.py`, `s04_estratos_via.py`)
- s03 es `s02_v375e_retro.py` de `v375/` con el volcán por variable: corre `mirova_v750_codigo.procesar_grilla` de main con
  `caja_v375` sobre las grillas de S162, S162b, S159 y FAR, y pasa el record por node. Ventana de los lotes en
  Tupungatito: 2026-04-04 a 2026-10-21; 180 pasadas únicas, 70 con alertados de la vía, 28 con alerta de MIROVA; 3
  entradas con estado no ok (S162b), 2 duplicadas.
- P1: node contra `vrp_mw` del record de la vía: 30 publicadas, diferencia 0. Contra el C13 que guardó el probe (otra
  implementación): 60 pares, 17 difieren más de 1e-3 MW, máximo 0,080 MW (igual que CV375-08 de Chillán; no lo
  perseguí). P2: si las grillas no se leyeran, «via_con_pixeles» sería 0; da 70.
- s04 es `s03_estratos_cenit.py` de `v375/` sin cambios de lógica (`s04_salida.txt`, `s04_salida.json`).

| mismas pasadas (B: K y vía publicadas, alerta MIROVA; 2026-04-04 05:48 a 2026-09-18 06:42) | n | z < 30 | z >= 30 | z >= 50 | Spearman [barajado] |
|---|---|---|---|---|---|
| K producción / MIROVA | 23 | 0,394 (12) | 0,251 (11) | 0,190 (5) | −0,503 [−0,408; +0,412] fuera |
| V375-E publicada / MIROVA | 23 | 1,010 (12) | 1,017 (11) | 1,006 (5) | +0,120 [−0,342; +0,382] dentro |
| V375-E / K | 23 | 2,336 (12) | 3,930 (11) | 5,320 (5) | +0,645 [−0,391; +0,371] fuera |

Los brazos de ROI de V375-C (C13, C21, CIRC, n 18) dan 1,0 en los dos tramos: la caja no es la pieza (lo mismo que
CV375-05 en Chillán).

### s05: fondo y temperaturas en la grilla de la vía (`s05_fondo_temperaturas.py`, `s05_salida.txt`, `s05_salida.json`)
- Misma máscara de alertados (la de la vía), misma grilla; sólo cambia el fondo. Brazos: VIA (fondo local del `.m`),
  ANI (mediana BT I4 del anillo 5 a 25 km en la grilla, sin recorte), ANI_REC (ídem con recorte a cero), ANIK_REC (fondo =
  `t_bg` del record K de producción de la misma pasada, con recorte a cero, que es lo que hace K en
  `pipeline/process_viirs.py:1515` y `:1536`), CERO (fondo cero).
- P1: VIA recalculado contra `vrp_mw` del record: diferencia máxima 0,0005 MW sobre 70 (redondeo). CERO >= VIA en 70 de
  70. El anillo de la grilla contra el `t_bg` del record K: mediana +1,22 K (p10 0,81, p90 1,83), Spearman 0,998 sobre 180
  pasadas: es el mismo anillo, con 1,2 K de sesgo por la otra geometría. P2: anillo menos fondo local = 0 en 0 de 70.

| brazo / MIROVA (24 pasadas summit con alerta, 2026-04-04 a 2026-09-18) | mediana | z < 30 (12) | z >= 30 (12) | Spearman [barajado] |
|---|---|---|---|---|
| VIA | 1,015 | 1,010 | 1,015 | +0,080 [−0,339; +0,389] |
| ANIK_REC (fondo de K, recorte) | 0,298 | 0,415 | 0,246 | −0,224 [−0,353; +0,436] |
| ANI_REC (anillo en grilla, recorte) | 0,192 | 0,272 | 0,167 | −0,231 [−0,349; +0,413] |
| ANI (anillo en grilla, sin recorte) | 0,136 | 0,269 | 0,060 | −0,229 [−0,343; +0,404] |
| CERO (techo) | 2,485 | 2,163 | 2,588 | +0,537 fuera |
| K producción / ANIK_REC (n 22) | 1,024 | 1,085 | 0,944 | −0,425 [−0,448; +0,433] dentro |

Temperaturas en esas 24 pasadas: exceso de los alertados sobre el fondo local 10,61 K bajo 30° y 8,49 K sobre 30°
(Spearman −0,491, fuera de [−0,403; +0,363]); `t_bg` de K menos fondo local 6,86 / 6,99 K (Spearman −0,202, dentro);
anillo de la grilla menos fondo local 8,38 / 7,96 K. En las 180 pasadas con grilla: cumbre a 2 km del cráter 244,5 / 244,0
K, anillo 250,4 / 248,8 K, anillo menos cumbre 6,3 / 4,2 K (Spearman −0,229, fuera) y, en las 70 con alertados, 7,07 /
6,81 K (dentro).

### s06: alertas que K no publica (`s06_alertas_sin_publicar.py`, `s06_salida.txt`)
- P1: 11, igual a `n_alerta_sin_publicar` de s01. P2: si el CSV no se leyera, 0.
- Las 11 tienen cenit entre 48,5° y 66,3°. 9 son el cráter (`distance_class` summit o sin cúmulo, `n_pos` 0: todos los
  píxeles con VRP 0); 2 son far (2026-09-28 05:18 a 21,6 km y 2026-09-29 04:54 a 9,4 km). 7 son sospechosas (sólo OCR de
  Suomi NPP antes del 2026-10-09); las 4 de la tabla (2026-03-06 06:36, 04-06 06:30, 04-10 06:24, 05-23 04:42) son
  0,09 a 0,13 MW, todas bajo 1 MW.

## 5. Hallazgos (orden por gravedad)

### CTUPUN375-01
- TÍTULO: La magnitud baja de Tupungatito VIIRS 375 es el fondo de anillo de K con recorte: el mismo mecanismo que Chillán, con el nivel dominando
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `s05_fondo_temperaturas.py` : `s05_salida.txt` (brazos VIA, ANIK_REC, «K prod / ANIK_REC»); `pipeline/process_viirs.py:812`, `:839`, `:1515`, `:1536` (origin/main)
- QUÉ PASA: el foco débil del cráter sube unos 10 K sobre su entorno, y K le resta como fondo la mediana del anillo de 5 a
  25 km, que cae en valles 6,9 K más tibios, y recorta a cero el resto. Con la misma máscara y grilla que reproducen a
  MIROVA (1,01 / 1,02), cambiar sólo el fondo por el `t_bg` de K de la misma pasada da 0,415 / 0,246, igual a K (0,394 /
  0,251; K sobre ese brazo 1,02, n 22). El nivel (59 % perdido de frente) y la pendiente (el exceso se diluye de 10,6 a 8,5
  K de lado mientras el error de fondo sigue en 6,9 K) salen del mismo término. En código: el fondo de K es
  `bt_to_spectral_radiance(t_bg_i04)` (l. 1515) con el anillo medido desde `volcano_lat/lon` (l. 812, 839) y
  `delta_L = np.maximum(L_hot - L_bg, 0.0)` (l. 1536); `enable_vrp_bg_neighbor_mean_viirs375: false` en
  `pipeline/profiles/mirova_equivalent.yaml:485`, así que el fondo de vecinos (D25, l. 1524) no corre.
- CÓMO SE VE EN EL DASHBOARD: Tupungatito VIIRS 375 aparece a un tercio de MIROVA en cualquier noche, y a un cuarto o menos
  cuando el satélite mira de lado; el operador ve el lago cratérico más débil de lo que MIROVA dice.
- CÓMO REPRODUCIRLO: en la CARPETA, `python -B s01_pareo_k.py repo 2026-02-14 2026-11-02 s01_k`; `python -B
  s03_v375e_retro.py repo s01_k_pasadas.csv s03_v375e`; `python -B s05_fondo_temperaturas.py repo s03_v375e_pasadas.csv
  s01_k_pasadas.csv s05` (con `repo` = `git archive origin/main scripts frontend pipeline volcanoes.yaml
  data/mirova_reference data/mirova_equivalent/Tupungatito.json`). Caso: Tupungatito VIIRS_NOAA20 2026-05-30 05:00 UTC (z
  54,4°: MIROVA 0,32, VIA 0,322, ANIK_REC 0,083, K 0,059; valores en `s05_salida.json`).
- CONFIANZA: CONFIRMADO el contrafactual (medido, n 24, retrospectivo, lotes de abril a septiembre); que los píxeles que K
  suma sean los mismos que la vía es SOSPECHA (no lo comparé; la coincidencia 1,02 lo sugiere pero no lo prueba).
- GRAVEDAD 1-5: 4 (decide la palanca: no es la caja ni la geometría del borde, es el fondo; la vía o el fondo de vecinos la
  corrigen en Tupungatito)

### CTUPUN375-02
- TÍTULO: K cae con el cenit en Tupungatito VIIRS 375 sobre todo el corpus, y MIROVA no
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `s02_estratos_k.py` : `s02_salida.txt`
- QUÉ PASA: por pasada, K da 0,43 bajo 30° y 0,24 sobre 30° (168 pares, Spearman −0,52 fuera de [−0,14; +0,16]); igual con
  sólo la tabla (−0,57), sin las sospechosas (−0,52), desde abril (−0,60) y desde el 13 de junio (−0,57). La magnitud de
  MIROVA no depende del cenit (+0,03) y la razón casi no depende de la magnitud (−0,16). Pasado 30° la razón ya no baja más
  (30 a 50: 0,23; >= 50: 0,25): la pendiente es un escalón, no una rampa (la selección de MIROVA, que alerta en 7,7 % de las
  pasadas sobre 50° contra 28 % bajo 30°, puede aplanar el tramo alto; SOSPECHA).
- CÓMO SE VE EN EL DASHBOARD: la serie VIIRS 375 de Tupungatito salta según el satélite y el ángulo de la pasada aunque el
  volcán no cambie.
- CÓMO REPRODUCIRLO: `python -B s02_estratos_k.py s01_k_pasadas.csv s02_salida.json`
- CONFIANZA: CONFIRMADO
- GRAVEDAD 1-5: 3

### CTUPUN375-03
- TÍTULO: V375-E reproduce a MIROVA en Tupungatito en todos los ángulos; su ganancia sobre K crece con el cenit
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `s04_estratos_via.py` : `s04_salida.txt` (B_K, B_via_publicada, B_via_sobre_K)
- QUÉ PASA: en las mismas 23 pasadas, la vía da 1,010 / 1,017 / 1,006 (z < 30 / >= 30 / >= 50) contra MIROVA y K 0,394 /
  0,251 / 0,190; la vía sobre K pasa de 2,34 a 3,93 y 5,32 (Spearman +0,645, fuera). Es la vía entera (lotes
  retrospectivos), no la sombra.
- CÓMO SE VE EN EL DASHBOARD: con la vía, Tupungatito VIIRS 375 tendría la magnitud de MIROVA; hoy es invisible (la vía no
  publica).
- CÓMO REPRODUCIRLO: `python -B s04_estratos_via.py s01_k_pasadas.csv s03_v375e_pasadas.csv s04_salida.json`
- CONFIANZA: CONFIRMADO (n 23, abril a septiembre; los lotes no son una muestra al azar de las pasadas)
- GRAVEDAD 1-5: 3

### CTUPUN375-04
- TÍTULO: Las alertas de MIROVA que K pierde en Tupungatito son todas oblicuas y casi todas el cráter con 0 MW (la cara de recall del mismo mecanismo)
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `s06_alertas_sin_publicar.py` : `s06_salida.txt`
- QUÉ PASA: de 179 alertas, 11 sin publicar, todas con cenit de 48,5° a 66,3°; 9 tienen el cúmulo de K en el cráter (o sin
  cúmulo) y todos los píxeles con VRP 0: el foco diluido queda bajo la mediana del anillo y el recorte lo borra. Las 4 de
  la tabla son de 0,09 a 0,13 MW (bajo 1 MW, no protegidas). La vía recupera la de 2026-04-06 06:30 (0,087 contra 0,09,
  `s04_salida.txt`, `via_pub_K_no`).
- CÓMO SE VE EN EL DASHBOARD: noche sin punto VIIRS 375 en Tupungatito cuando MIROVA marcó una alerta débil en una pasada
  oblicua.
- CÓMO REPRODUCIRLO: `python -B s06_alertas_sin_publicar.py s01_k_pasadas.csv`; Tupungatito VIIRS_NOAA20 2026-03-06 06:36
  UTC (z 63,2°, MIROVA 0,12 CONS, K summit, n_pos 0).
- CONFIANZA: CONFIRMADO el conteo; que el recorte sea la causa en cada una es SOSPECHA salvo 2026-04-06 (la vía la ve)
- GRAVEDAD 1-5: 2

### CTUPUN375-05
- TÍTULO: Las alertas grandes sólo de OCR de Suomi NPP en Tupungatito son fuentes a 9 a 25 km del cráter, incluidas las dos «protegidas sin publicar» del auto-audit
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `s05_fondo_temperaturas.py` : `s05_salida.txt` (bloque «alertas de MIROVA con vía de clase far»); `_auto_audit_latest.json` (`informado_aparte.protegidas`)
- QUÉ PASA: en 2026-08-01 05:00, 09-14 06:18, 09-28 05:18 y 09-29 04:54 (Suomi NPP, sólo OCR, 1,25 a 2,51 MW) la vía, sobre
  el mismo gránulo, reproduce la magnitud de MIROVA (1,280; 2,278; 2,525; 1,781) pero con todos sus alertados a 13,2;
  14,9; 25,1 y 9,2 km del cráter, mientras el OCR dice 3 a 5,7 km. Encaja con el hito A119 (la distancia del OCR de Suomi
  NPP antes del 2026-10-09 puede ser de otra pasada; el VRP sí es suyo). Esas magnitudes no son del lago cratérico. Dos de
  ellas entran a los pares de K como razones de 0,004 y 0,013 (K publica el cráter); las otras dos son las «protegidas sin
  publicar» que el auto-audit ya informa aparte. Si la de 25 km es el Embalse El Yeso (25 a 27 km SE, `volcanoes.yaml`
  l. 835 y 838, `exclude_zones`) no lo comprobé: SOSPECHA.
- CÓMO SE VE EN EL DASHBOARD: invisible en el mapa (K las marca far o publica el cráter); en el auto-audit aparecen como
  alertas protegidas perdidas, y arrastran la mediana de la razón (poco: U 0,335 contra U-S 0,336).
- CÓMO REPRODUCIRLO: como CTUPUN375-01; Tupungatito VIIRS_SNPP 2026-09-28 05:18 UTC.
- CONFIANZA: CONFIRMADO que la vía las ubica lejos; SOSPECHA qué fuente son
- GRAVEDAD 1-5: 2 (una alerta protegida que es una fuente lejana no debe contar como pérdida de recall)

### CTUPUN375-06
- TÍTULO: El control negativo de la referencia corrida un día no es un nulo en Tupungatito (55 de 168 pares sobreviven)
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `s01_pareo_k.py` : `s01_k_resumen.json` (`control_neg_shift1d_n_pares`)
- QUÉ PASA: el lago cratérico emite casi todas las noches y la órbita se repite dentro de ±120 s, así que correr la
  referencia un día vuelve a encontrar alertas. El instrumento de pareo no queda refutado (identidad, node contra JSON y
  desfase de 2 s están bien), pero ese control no sirve aquí como P2.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: como s01.
- CONFIANZA: CONFIRMADO
- GRAVEDAD 1-5: 1

### CTUPUN375-07
- TÍTULO: La vía re-corrida y el C13 del probe difieren más de 1e-3 MW en 17 de 60 pasadas de Tupungatito
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `s03_v375e_retro.py` : `s03_v375e_resumen.json` (`control_via_vs_C13`)
- QUÉ PASA: máximo 0,080 MW; no miré cuáles ni por qué (el mismo patrón que CV375-08 en Chillán, atribuido en parte al
  relleno). No mueve las medianas de la vía, que dan 1,0 con cualquiera de las dos.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: como s03.
- CONFIANZA: SOSPECHA (de la causa)
- GRAVEDAD 1-5: 1

## 6. Respuesta a las tres preguntas

1. K por tramo de cenit, todo el corpus pareable (2026-02-14 a 2026-11-02, 168 pares): 0,429 (82) bajo 30°, 0,243 (86)
   sobre 30°, Spearman −0,522 fuera del barajado. Robusto a sólo tabla, a quitar las sospechosas y a recortar la ventana a
   abril o a junio.
2. V375-E: existe en los lotes (180 pasadas, 70 con alertados, 23 pares con K y vía publicadas): 1,010 / 1,017 contra
   MIROVA, V375-E / K 2,34 / 3,93.
3. Las dos cosas, con el nivel dominando: 59 % perdido de frente y la mitad de lo que queda perdido de lado. El fondo de K
   contra el de la vía explica el nivel y la pendiente a la vez (CTUPUN375-01): el error de fondo es constante (6,9 K) y
   la señal se diluye de lado. En la grilla no queda una pendiente residual que pida otra pieza (K sobre ANIK_REC 1,085 /
   0,944, Spearman −0,425 dentro del barajado con n 22); un efecto de área o remuestreo (D17) pequeño no se puede
   descartar con ese n.

## 7. SEGUIMIENTOS (fuera de mi eje)

- VIIRS 750 en Tupungatito: K publica 7 de 1.077 pasadas nocturnas y deja sin publicar 12 de 14 alertas de MIROVA (2
  pares, razón 0,072), `s01_k_resumen.json`. Puede ser el mismo fondo con un píxel más grande; no lo medí. SOSPECHA,
  gravedad 2.
- El auto-audit cuenta como «protegidas sin publicar» dos alertas que la vía ubica a 9 y 25 km (CTUPUN375-05); ya las
  separa en `informado_aparte`, pero el flag de magnitud usa la unión. Gravedad 1.
- El fondo de vecinos de K (`enable_vrp_bg_neighbor_mean_viirs375`, `pipeline/process_viirs.py:1524`, apagado en
  `mirova_equivalent.yaml:485`) es una palanca dentro de K que ataca justo este término; no busqué si tiene A/B en
  Tupungatito. Gravedad 2.

## 8. VERIFICADO LIMPIO

1. El pareo de S172 corre igual sobre Tupungatito (vara: sus propios controles; identidad del predicado, node contra
   JSON 0 diferencias, desfase máximo 2 s; `s01_k_resumen.json`).
2. El anillo que mido en la grilla es el anillo de K (vara: el `t_bg` del record K de producción de la misma pasada;
   Spearman 0,998, sesgo +1,22 K en 180 pasadas, `s05_salida.txt`). Por eso uso el `t_bg` del record, no el de la grilla,
   en el brazo que compara con K.
3. La magnitud que el tablero publicaría para la vía es su `vrp_mw` (vara: node; 30 de 30, diferencia 0).
4. MIROVA no cae con el cenit en magnitud (vara: el VRP de MIROVA de las 168 pasadas pareadas; Spearman +0,026).
5. Tupungatito no usa kernel local en el fondo de K (no tiene `local_kernel_bg` en su bloque de `volcanoes.yaml`, bloque que empieza en la l. 800, y el comentario de `pipeline/process_viirs.py` l. 1497 a 1500 lo excluye a propósito); el fondo es el
   anillo global.

## 9. SIN DATO

- La sombra de V375-E en Tupungatito: no la medí (el README de S173 dice que está vacía hasta el 2026-11-03).
- Ablación del remuestreo solo (D17) en Tupungatito: necesita los L1B; no bajé nada.
- V375-E antes del 2026-04-04 y después del 2026-09-18 con alerta de MIROVA: los lotes no traen pares.
- Correspondencia celda a celda entre los píxeles que suma K y los que suma la vía.

## 10. FUERA DE ALCANCE

MODIS, VIIRS 750 (salvo el seguimiento), otros volcanes, reprocesos, descargas, cambios en pipeline/, data/ o frontend/,
propuestas de arreglo.
