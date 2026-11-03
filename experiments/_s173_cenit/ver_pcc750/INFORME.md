# INFORME del verificador: cenit de VIIRS 750 en Puyehue-Cordón Caulle (ver_pcc750)

## 1. Encabezado

- Fecha y hora del servidor (GitHub, cabecera `Date`): al abrir caminos.md `Tue, 03 Nov 2026 02:48:40 GMT`; al
  cerrar el informe `Tue, 03 Nov 2026 03:02:10 GMT` (hora local de la máquina: noche del 2 al 3 de noviembre).
- Commit sobre el que medí: la copia `pcc750/repo/` del auditor es `origin/main` **f20495d374dc868a3dd789d1e16f662fd24c6210**
  (comprobado archivo por archivo con `git show origin/main:<ruta> | tr -d '\r' | sha256sum` contra la copia: 12 de 12
  iguales normalizados a LF; en bytes difieren todos por CRLF del checkout). El oráculo de S162 que usa el auditor
  (`pcc750/src/s162/oraculo_ablacion.py`, `ablacion.py`) es el de `origin/loop/activo` b9da9adb0
  (`experiments/_s162_v750c/`, sha256 90522155... y e3122298..., iguales). `pipeline/grillas_mirova.yaml` tiene la misma
  fila de PCC en `main` y en `loop/activo` (`roi_v750: def`); `main` trae además los 34 de la sombra.
- Modelo y esfuerzo reales: Claude Fable 5.1 (`claude-fable-5-1`). El esfuerzo del agente lo fija el orquestador y no
  lo puedo leer desde adentro: SIN DATO; lo declaro así en vez de inventarlo.
- CARPETA: `C:/Users/nmend/vrp-wt/s173_cenit/ver_pcc750/`. Scripts e instrumentos que se quedan:
  `caminos.md` (sellado, sha256 a99bc939... con el pie), `rerun/` (copia de los scripts del auditor re-corridos),
  `v01_via_produccion_roi.py` + `v01_salida.txt` + `v01_por_pasada.csv` + `v01_resumen.json`,
  `v02_razon_k_pareo_propio.py` + `v02_salida.txt` + `v02_pares.csv`,
  `v03_fondo_via_vs_oraculo.py` + `v03_salida.txt` + `v03_por_pasada.csv`, `hallazgos.csv`.
- Qué NO miré: no abrí `pcc750/INFORME.md` del auditor (regla del verificador); no re-derivé los brazos nativos del
  runner N (K, F, FC, C) desde los gránulos, porque los gránulos no están en disco: los leí de
  `pcc750/insumos/n/run_*/resultados_*.json` tal como los dejó el run 39682867040 y 39693661527; no corrí ningún
  workflow ni usé credenciales; no medí Chillán ni ningún otro volcán; no verifiqué contra MATLAB la triangulación de
  la vía (me apoyo en la prueba de oro del repositorio, `tests/test_mirova_v750_codigo_s162.py:166`); no abrí la
  sección «Caulle» del informe V750-C de S162; no miré el perfil radial (s05) más allá de re-correrlo.
- Procesos pesados: uno a la vez (rerun en segundo plano terminado antes de lanzar v01; v01, v02 y v03 en serie).
  Disco al cierre: C: 27 GB libres, D: 4,7 GB (no escribí nada en D:).

## 2. En una pantalla

1. Las 7 afirmaciones del auditor se **reproducen número a número** con sus scripts en copia (0 líneas de diferencia
   en s02 a s05 y en todos los CSV; s01 sólo cambia la ruta impresa) y con un pareo propio (v02: 53 alertas,
   0,571 / 0,117 con ceros, Spearman -0,508 fuera del barajado).
2. **Lo que decide la paridad**: la vía «código MIROVA» con la ROI que `grillas_mirova.yaml` le da HOY a PCC (`def`,
   B0) **no publica nada**: 0 de 72 pasadas, pierde las 8 alertas protegidas. Con cualquiera de las otras cuatro ROI
   del prerregistro (B1, B2, B3, B5) la vía queda en mediana **0,96 a 1,00** contra MIROVA en los dos tramos de cenit,
   0 protegidas perdidas y 1 a 5 negativos limpios publicados de 43 (K: 25 de 43). B2 (caja de 7 x 7 movida al
   cráter), que el auditor no corrió y que es la primera en el orden de cercanía al `.m` del prerregistro, no pierde
   ninguna protegida en este subconjunto, contra la predicción §8 del prerregistro.
3. **El instrumento del auditor no es la vía de producción en el fondo**: el oráculo S162 interpola el fondo con la
   Delaunay de scipy sin perturbar; la vía usa la triangulación perturbada que la prueba de oro iguala a MATLAB. Con
   la misma máscara, en 11 de 27 pasadas con alertados la vía da **1,3 a 40 % más** VRP que el oráculo, concentrado en
   cenit ≥ 30° (vía/oráculo mediana 1,047 contra 1,000 bajo 30°). Por eso la afirmación 7 («el código de MIROVA en la
   grilla tampoco es plano, -0,47») vale para el oráculo y **no** para la vía: con la vía la mediana es 0,997 / 0,961
   con ceros y 1,001 / 0,988 sin ceros, y el Spearman queda dentro del barajado con ceros (-0,359) y al borde sin
   ceros (-0,362 con banda [-0,348, +0,353]).
4. La afirmación 3 («la pendiente sale de fracasos de K») es parcial: en las 53 alertas la razón de las pasadas
   **publicadas** también cae con el cenit (0,696 → 0,336, Spearman -0,414 fuera del barajado, 34 de 34 réplicas
   dejando una noche fuera). En el subconjunto de 29 con grilla el «sin ceros» tiene n = 3 sobre 30° y no decide.
5. Las afirmaciones 2, 4, 5 y 6 se confirman; en la 2 el «anillo de K» reconstruido en la grilla es ~1 K más frío que
   el `t_bg` del record de producción (el déficit real es algo mayor, el signo no cambia).

## 3. Veredicto por afirmación

Vara y denominadores comunes: scraper Mirova-v1 del commit f20495d3 (`registro_vrp_consolidado.csv` sha256
3d1fa40d..., `registro_vrp_ocr.csv` d793ba34...), indexado por `scripts/banco_paridad.indexar_referencia` con regla SN
(D-9) y avisos A119 por stderr (la ventana abril a noviembre pisa 7 hitos; para VIIRS 750 de PCC el canal CONS trae 51
de las 53 alertas y el resultado con CONS sola es el mismo: 0,576 / 0,117). Pareo por pasada a ±120 s
(`scripts/clase_mirova.py:112`, `VENTANA_S = 120`). Magnitud nuestra: `disp` del predicado del tablero ejecutado con
node sobre el record, que en VIIRS 750 es `pc.vrp_mw` (control de lectura: 0 discrepancias en 39 publicados). Cenit:
`sensor_zenith_deg` del record (presente en 53 de 53 pares y en 72 de 72 grillas; contra el `Zenith_Sat_deg` del OCR
la única fila que lo trae difiere 0,27°; contra el cenit del píxel central del gránulo en el runner, mediana 0,275° y
máximo 1,27°).

### A1. «K por pasada, abril a noviembre, 53 alertas: 0,571 bajo 30° y 0,117 sobre 30° con ceros; Spearman -0,508 fuera del barajado; en la ventana del auto-audit (22) la pendiente no es significativa»

**CONFIRMADA** (en la parte de los números; la lectura de la ventana corta, ver VPCC750-06).

- Re-corrida de `s01_razon_k_por_pasada.py` en copia: idéntica salvo la ruta (`rerun/s01_salida.txt`).
- Camino propio (`v02_razon_k_pareo_propio.py`, pareo hecho a mano sobre las filas del scraper, Spearman de scipy,
  barajado con numpy semilla 173): 53 alertas (42 noches; 51 CONS, 2 OCR; 0 descartadas por SN), 0 sin record K,
  0 con más de un candidato; con ceros **0,571 [0,111, 0,849] n = 33 contra 0,117 [0,000, 0,473] n = 20**,
  Spearman **-0,508**, barajado [-0,240, +0,252], FUERA. Son **medianas**; las medias son 0,672 y 0,236.
- Dejar una noche fuera: Spearman en [-0,556, -0,481], FUERA 42 de 42. Por plataforma: NOAA-20 (15 / 9) -0,445 FUERA,
  NOAA-21 (15 / 10) -0,545 FUERA, Suomi NPP n = 4 (sin dato). Sin la pasada del 2026-10-10: -0,512 FUERA.
- Control de instrumento: ×2 dobla las medianas (1,141 / 0,235); la referencia corrida +1 día deja 3 pares contra
  39 directos. El VRP de MIROVA mismo no cae con el cenit (0,640 / 0,525, Spearman -0,262 dentro de [-0,280, +0,251]).
- La ventana del auto-audit (22 alertas): Spearman -0,236 dentro de [-0,422, +0,501]; pero las medianas caen igual
  (0,390 → 0,154). Con n = 22 la banda del barajado es ±0,45: eso es falta de poder, no ausencia de pendiente.

### A2. «El anillo de K es 3,6 K más tibio que el fondo local de MIROVA y el lacolito sobresale sólo 4,7 K; en la grilla poner ese fondo baja el código de MIROVA de 1,00 a 0,18; en el gránulo nativo K 0,425 y F 1,128»

**CONFIRMADA EN PARTE** (los cuatro números se reproducen; lo que cae es que el «anillo de K» de la grilla sea
exactamente el de producción: es ~1 K más frío, lo que hace al déficit medido conservador).

- Re-corrida de s03 y s04: idénticas. Camino propio con el fondo de la **vía de producción** y la máscara B1
  (`v03_salida.txt` §4, n = 16 / 9): BT del anillo 5 a 25 km menos BT del fondo de la vía bajo los alertados
  **3,606 K** (z < 30) y 5,535 K (z ≥ 30); BT del alertado menos fondo de la vía **4,720 K** y 4,968 K; alertado menos
  anillo 0,678 K y **-1,590 K** (sobre 30° el lacolito queda por debajo de la mediana del anillo, por eso K recorta a
  0). Misma máscara con el fondo de anillo de K armado por mí (mediana de BT del anillo 5-25 km desde el centro de la
  grilla, Planck, recorte por píxel; `process_viirs_mod.py:570` y l. 1070-1086 leídos): **0,176** [0,000, 0,631] n = 18
  y 0,000 n = 11 (`v01_salida.txt`, «B1_sens fondo anillo K»), contra 0,998 / 0,962 con el fondo del código.
- Nativo: K pc 0,425 / 0,000 (`v01`, mismo denominador de 29, leído del record del runner) y F 1,128 / 0,990 (rerun de
  s03, leído de `resultados_*.json`; no re-derivado desde gránulos, ver «SIN DATO»).
- La parte que cae: `t_bg` del record de K de producción menos la mediana de BT del anillo en la grilla da **+1,007 K**
  (z < 30, n = 16) y +0,849 K (n = 9); en radiancia, Planck(`t_bg` de K) / mediana del anillo en la grilla = 1,049
  [0,952, 1,053] n = 25 (el auditor midió lo mismo en s04 §2: 1,053). O sea que el fondo de producción es todavía
  más tibio que el anillo que el auditor reconstruyó: la diferencia de 3,6 K es un piso. Causas posibles, no
  separadas: el anillo de producción se mide en la geometría del gránulo (sin remuestreo) y desde el lat/lon del
  yaml, el de la grilla desde el centro de MIROVA (70 m de diferencia) sobre celdas interpoladas; y `compute_bg_stats`
  no excluye a los alertados (`ENABLE_TEST1_K1_BG_EXCLUDE` False, leído de `pipeline.profile`), el oráculo sí
  (`~mask`, l. 222).
- Qué es el fondo de K en PCC, leído del código (A89, A6): `process_viirs_mod.py:570`
  `bg_mask = (dist >= BG_INNER_KM) & (dist <= BG_OUTER_KM)` con `BG_INNER_KM 5.0`, `BG_OUTER_KM 25.0` de
  `pipeline.profile`; `detection_context.compute_bg_stats` devuelve `t_bg = median(bt[bg_mask])`; l. 1071-1072
  `L_bg_rad = bt_to_spectral_radiance(t_bg)` y l. 1086 `delta_L = np.maximum(L_hot - L_bg_rad, 0.0)`;
  `ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750` False. PCC tiene `local_kernel_bg: true` en `volcanoes.yaml:54`, pero
  `process_viirs_mod.py:462-469` declara (TEXTO): «la implementación kernel-local para M-band aún no existe», y en el
  archivo `local_kernel_bg_compatible` aparece sólo en la firma y el docstring (l. 448, 462, 469): el flag no actúa
  en VIIRS 750, el anillo 5-25 km es el fondo efectivo.

### A3. «La pendiente sale de fracasos de K (6 de 18 contra 8 de 11)»

**CONFIRMADA EN PARTE**: los conteos sí; la atribución «sale de» no, porque la razón de las pasadas publicadas también
cae con el cenit.

- Conteos (rerun s04 §1, 29 alertas con grilla): z < 30, `a_no_detecta` 3 + `b_detecta_0MW` 3 = 6 de 18; z ≥ 30,
  4 + 4 = 8 de 11; K2 idéntico a K (control). Sobre las 53 alertas (v02): ceros 6 de 33 y 8 de 20; de los 14 ceros, 7
  son records sin cúmulo y 7 cúmulos a 0,0 MW (todos `summit`, 0,14 a 0,50 km del ancla; uno a 17,6 km el 04-30).
- La indicadora «no publica» sube con el cenit: Spearman +0,367, FUERA de [-0,231, +0,236]. Hasta ahí el auditor.
- Pero las **publicadas** (sin ceros, n = 27 / 12): **0,696 → 0,336**, Spearman -0,414 FUERA de [-0,284, +0,313];
  dejando una noche fuera, FUERA 34 de 34 réplicas; con CONS sola 0,733 → 0,336, -0,444 FUERA. Con corte en 40° las
  publicadas dan 0,571 / 0,524 (n = 6 sobre 40°): la caída de las publicadas se concentra entre 30 y 40°.
- En el subconjunto de 29 con grilla el «sin ceros» de K tiene n = 3 sobre 30° (rerun s04 §3: Spearman -0,349 dentro):
  SIN DATO para esa pregunta, no evidencia de que la pendiente sea sólo de ceros.

### A4. «Ni posición ni suma»

**CONFIRMADA**, con el límite de que `Distancia_km` del scraper no trae acimut (A93).

- Camino propio sobre las 53 alertas (`v03_salida.txt` §6): distancia del centroide del cúmulo de K al ancla,
  publicadas, mediana 0,231 km (n = 27) y 0,315 km (n = 12), Spearman +0,263 dentro; distancia de MIROVA 7,830 km en
  los dos tramos. En la grilla (rerun s03): «dist K - celda C más cerca» 0,000 en 14 de 14 y 6 de 6; n_pixels del
  cúmulo de K mediana 1 en los dos tramos (s01 amplia: 1,000 / 1,000). La vía con B2 pone el cúmulo a 0,11 a 0,58
  km del cráter en los 27 positivos con alertados (`v01` detalle, columna distB2).

### A5. «La caja 7 x 7 del ejemplo no alerta en ninguna de 72 pasadas de PCC (gravedad 3), por eso usó cajas B1 y B3 de V750-B»

**CONFIRMADA** el 0 de 72, con la vía de producción y con control positivo; la segunda mitad es incompleta: faltaron
B2 y B5 (ver VPCC750-02).

- `v01` con `pipeline.mirova_v750_codigo.caja_roi("def")` + `detectar_mirova` + `vrp_mirova` + `procesar_grilla` sobre
  las 72 grillas: 0 pasadas con alertados, 0 publicadas, pierde 8 de 8 protegidas. Identidad con la caja `def` y
  `sens` del oráculo en número de alertados: 72 de 72.
- Control positivo (`v03` §5): inyectando radiancia en la celda del cráter (fila 23, col 30, a 7,75 km del centro,
  fuera del 7 x 7 central) la caja `def` alerta desde **+0,05 a +0,08 W m-2 sr-1 um-1** (6 pasadas probadas), y la
  caja `sens` desde +0,00 a +0,01: el exceso real del lacolito (3,9 a 6,8 K sobre el fondo de la vía, unos 0,04 a
  0,07 W) queda bajo los umbrales conservadores (10 σ, mínimo 0,02) y sobre los sensibles (5 σ, 0,003). El
  instrumento ve; la caja no.
- Por qué la vía usaría `def` hoy: `pipeline/grillas_mirova.yaml:38` `PuyehueCordonCaulle: {..., roi_v750: def}` y
  l. 24-27 (TEXTO): «roi_v750: la región sensible del código de MIROVA para el volcán. Hoy "def" en todos (la matriz
  de ejemplo del .m: 7 x 7 sensible al centro dentro de 21 x 21); la decide V750-B (experiments/_s162_v750b/
  PREREGISTRO_V750B.md, lectura el 2026-11-03) y se cambia aquí con su lectura, nunca antes». Y en el prerregistro
  (`origin/main:experiments/_s162_v750b/PREREGISTRO_V750B.md`, §2 l. 56-61) los brazos son B0 def, B1 sens 21 x 21,
  B2 7 x 7 en el cráter, B3 círculo de `inner_radius_km`, B4 (B1 en Caulle y Tupungatito), B5 corona. El §3 l. 138-139
  ordena los elegibles por cercanía al `.m`: «B4 ..., B2 (conserva la caja de 7 × 7 y sólo la mueve), B5 ..., B1, B3».
  El auditor corrió B1 y B3 (`s02_ablacion_pcc.py:69`, bases «sens» y «circ»); no corrió B2 ni B5.

### A6. «El anillo de oraculo_ablacion.py va de inner a 25 km, no de 5 a 25 (con inner 20 en PCC)»

**CONFIRMADA** (leído).

- `pcc750/src/s162/oraculo_ablacion.py:177` (compuerta): `anillo = (dk > (inner_km or 0)) & (dk <= 25.0) & np.isfinite(bt13)`;
  l. 222 (fondo `anillo` del VRP): `anillo = (dk > (inner_km or 0)) & (dk <= 25.0) & np.isfinite(m13) & ~mask`. El
  docstring l. 14 lo declara (TEXTO): «t_bg la mediana del anillo inner..25 km (D22 de K)». K: `process_viirs_mod.py:570`
  `(dist >= BG_INNER_KM) & (dist <= BG_OUTER_KM)` = 5 a 25 km. En PCC, con `inner_radius_km` 20, el oráculo original
  mide 20 a 25 km. En Chillán (inner 5) coinciden salvo el `>` contra `>=` y el centro (grilla contra lat/lon del yaml).
  El arreglo del auditor (brazos «525», `s02_ablacion_pcc.py:102-109`) pasa `inner_km = 5` al oráculo y fija el
  círculo de la caja en 20 km con un monkeypatch local: actúa (s02 control 3b: 27 / 30 / 25 pasadas distintas) y su
  resultado coincide con mi fondo de anillo propio (0,176).

### A7. «El código de MIROVA en la grilla tampoco es plano en PCC (-0,47); F queda 1,3 sobre MIROVA sin ceros»

**CONFIRMADA EN PARTE**: el «-0,47» es del oráculo S162, no de la vía de producción (VPCC750-01); el 1,3 de F se
reproduce.

- Oráculo (rerun s03): C con ceros 1,001 / 0,808, Spearman -0,468 FUERA; S 0,997 / 0,684, -0,430 FUERA.
- Vía de producción, misma máscara (`v01`, `v03` §3): B1 0,997 / **0,961** con ceros, Spearman -0,359 dentro de
  [-0,376, +0,473]; B2 0,998 / 0,987, -0,289 dentro; B3 1,001 / 0,987, -0,392 FUERA de [-0,361, +0,466] por 0,03;
  sin ceros B1 1,001 / 0,988 (n = 16 / 9), -0,362 contra [-0,348, +0,353] (al borde); B2 1,001 / 0,990, -0,267
  dentro. Lo que queda: medianas planas; un Spearman débil negativo, al borde del barajado, con n = 25 a 29.
- F sin ceros (rerun s04 §3): 1,381 [1,028, 1,989] n = 15 y 1,310 n = 7, Spearman -0,227 dentro. Se reproduce. No lo
  re-derivé desde gránulos.

## 4. Hallazgos (orden de gravedad)

### VPCC750-01. El fondo del oráculo S162 no es el de la vía de producción: con la misma máscara da hasta 40 % menos VRP, y la diferencia crece con el cenit

- ARCHIVO:LÍNEA: `pcc750/src/s162/oraculo_ablacion.py:199` (TEXTO: «Igual al port de R2 sin perturbar: Delaunay
  lineal en (fila, columna), vecino más cercano fuera») contra `pcc750/repo/pipeline/mirova_v750_codigo.py:458-463`
  (TEXTO, l. 462-463: «Con esa regla el VRP es el de MATLAB R2026b en 166 de 166 escenas de O2 (máximo 1,55e-15) y el
  fondo completo en 84 de 84 ... con los ejes cambiados calza en 42 de 166 y Qhull en 41 de 84 fondos») y l. 548
  (`_fillmissing2_lineal` perturbada); prueba `origin/main:tests/test_mirova_v750_codigo_s162.py:166`
  (`test_fondo_y_vrp_iguales_a_matlab`). SCRIPT:SALIDA: `v03_fondo_via_vs_oraculo.py` → `v03_salida.txt` §1-3,
  `v03_por_pasada.csv`.
- QUÉ PASA: bajo un píxel caliente aislado el hueco es de 3 x 3 y el centro cae sobre la diagonal del cuadrado de
  vecinos; qué diagonal se elige decide si el fondo es la media de dos vecinos u otros dos, y en el borde del lacolito,
  con gradiente, eso mueve el fondo lo bastante para cambiar un exceso débil. El oráculo del auditor (y el port R2 con
  que se validó) triangula con scipy sin perturbar; la vía usa la regla perturbada que el repositorio iguala a MATLAB.
  Medido con la misma máscara (brazo sens / B1): 11 de 27 pasadas con alertados difieren, **siempre la vía más alta**
  (+1,3 a +40,5 %); vía/oráculo mediana 1,000 bajo 30° y **1,047** (media 1,125) sobre 30°. Inyectando el
  `_fillmissing2_lineal` del oráculo en la vía, las 27 coinciden con el oráculo a 1e-9: es la única diferencia.
- CÓMO SE VE EN EL DASHBOARD: invisible hoy (`ENABLE_V750_CODIGO_MIROVA` False en `pipeline.profile`). El riesgo es de
  decisión: si V750-B o la atribución de piezas se leyeran con el oráculo o con el runner N (`geo_linear` del port
  R2), en PCC se le atribuiría a la vía un déficit de magnitud en cenit alto que la vía no tiene.
- CÓMO REPRODUCIRLO: `cd C:/Users/nmend/vrp-wt/s173_cenit/ver_pcc750 && python -B v03_fondo_via_vs_oraculo.py`;
  pasadas con mayor diferencia: 2026-07-03 05:12 UTC (z 40,5°, +40,5 %), 2026-07-03 06:06 (z 31,6°, +40,0 %),
  2026-07-03 05:48 (z 5,1°, +26,1 %), 2026-07-06 05:12 (z 45,5°, +22,5 %).
- CONFIRMADA: CONFIRMADO (medido). Que la regla perturbada sea la de MATLAB lo tomo de la prueba de oro del repo, no lo
  medí (SOSPECHA en esa parte: sin MATLAB acá).
- GRAVEDAD: 3.

### VPCC750-02. Con la ROI de hoy (`def`) la vía no publica PCC en 0 de 72 pasadas; con B1, B2, B3 o B5 queda en 0,96 a 1,00 contra MIROVA y plana en mediana; B2 no pierde protegidas, contra la predicción del prerregistro

- ARCHIVO:LÍNEA: `pcc750/repo/pipeline/grillas_mirova.yaml:38` y l. 24-27; `origin/main:experiments/_s162_v750b/PREREGISTRO_V750B.md`
  §2 l. 56-61, §3 l. 138-139, §8 l. 164-165 (TEXTO: «B2: como MIROVA ubica el calor de Cordón Caulle a 4,6 a 10,5 km
  del centro y el cráter del yaml está a 7,6 km, predigo que pierde alguna protegida de Cordón Caulle (no elegible)»).
  SCRIPT:SALIDA: `v01_via_produccion_roi.py` → `v01_salida.txt`, `v01_por_pasada.csv`.
- QUÉ PASA: el calor de PCC está en el lacolito y el cráter de 2011, a 7,75 km del centro de la grilla de MIROVA
  (celda (23, 30) contra el centro (33, 33)), fuera del 7 x 7 central: con `def` esa zona es conservadora y el exceso
  de 4 a 7 K no pasa 10 σ. Resultados sobre 72 pasadas nocturnas (2026-04-07 a 2026-10-16; 29 con alerta de MIROVA,
  43 negativos limpios; 8 protegidas): B0 0 alertados, 8 de 8 protegidas perdidas. B1 (sens): 27 publicadas, 0,998 /
  0,962 (z < 30 n = 18, z ≥ 30 n = 11, con ceros), 0 protegidas perdidas, negativos limpios 1 de 15 y 1 de 28.
  **B2 (cráter)**: 27 publicadas, 0,998 / 0,987, Spearman -0,289 dentro, 0 protegidas perdidas, negativos 1 de 15 y
  1 de 28, cúmulo a 0,11 a 0,58 km del cráter. B3 (inner 20): 30 publicadas, 1,001 / 0,987, negativos 1 de 15 y 4 de 28.
  B5 (corona): igual que B1. K de producción (`pub_prod` del censo): negativos 12 de 15 y 13 de 28; pierde la
  protegida del 2026-10-10 (que las cuatro ROI publican a 1,00).
- CÓMO SE VE EN EL DASHBOARD: hoy nada (vía apagada). Si la vía entrara con `def`, PCC VIIRS 750 desaparecería del
  tablero (0 publicaciones donde MIROVA publicó 29). Con B1, B2, B3 o B5 el operador vería PCC con la magnitud de
  MIROVA y sin los 25 negativos que K publica hoy.
- CÓMO REPRODUCIRLO: `python -B v01_via_produccion_roi.py`; sección «PROTEGIDAS» y «NEGATIVOS LIMPIOS».
- CONFIANZA: CONFIRMADO para este subconjunto (72 pasadas del censo N). Que B2 sea elegible en la población completa
  de V750-B es SOSPECHA: el censo tiene 29 positivos y 8 protegidas de PCC.
- GRAVEDAD: 3.

### VPCC750-03. La caída con el cenit no es sólo de ceros: las pasadas publicadas también caen (0,696 → 0,336, fuera del barajado)

- SCRIPT:SALIDA: `v02_razon_k_pareo_propio.py` → `v02_salida.txt` («tablero publicadas (sin ceros)», «dejar una noche
  fuera»); contraste con `rerun/s04_salida.txt` §3 (n = 3 sobre 30°).
- QUÉ PASA: cuando K sí arma cúmulo, la magnitud publicada vale 0,70 de MIROVA cerca del nadir y 0,34 sobre 30°; a
  igual píxel (n_pixels mediana 1 en los dos tramos) eso es el fondo, no la detección: sobre 30° el alertado queda
  1,6 K por debajo de la mediana del anillo (v03 §4), así que el exceso se recorta casi entero aunque no llegue a 0.
  La indicadora de fracaso también sube con el cenit (+0,367 FUERA), así que los dos mecanismos coexisten; la
  afirmación 3 sólo nombra uno.
- CÓMO SE VE EN EL DASHBOARD: en PCC VIIRS 750, las noches con pasadas de borde de barrido muestran barras de 0,1 a
  0,4 MW donde MIROVA publica 0,5 a 1,4 MW, además de las pasadas vacías.
- CÓMO REPRODUCIRLO: `python -B v02_razon_k_pareo_propio.py`; 53 alertas, ventana 2026-04-01 a 2026-11-02.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2.

### VPCC750-04. El «anillo de K» reconstruido en la grilla es ~1 K más frío que el `t_bg` de producción: el déficit medido es un piso

- ARCHIVO:LÍNEA: `pcc750/repo/pipeline/process_viirs_mod.py:570`, `pcc750/repo/pipeline/detection_context.py`
  (`compute_bg_stats`, `t_bg = float(np.median(bg_vals))`), `pcc750/s02_ablacion_pcc.py:197` (`a525 = mediana de m13
  del anillo en la grilla`). SCRIPT:SALIDA: `v03_salida.txt` §4 («t_bg K record - BT anillo grilla» +1,007 / +0,849 K;
  Planck ratio 1,049 [0,952, 1,053] n = 25) y `rerun/s04_salida.txt` §2 (1,053).
- QUÉ PASA: el anillo de producción se mide sobre los píxeles del gránulo (sin remuestrear) desde el lat/lon del yaml
  y sin excluir alertados; el de la grilla sobre celdas interpoladas, desde el centro de MIROVA y excluyendo la
  máscara. El resultado es un fondo de producción ~5 % más radiante (≈1 K) que el que el auditor compara. La
  dirección no cambia ninguna conclusión (el déficit real es algo mayor que 3,6 K y el 0,18 algo menor).
- CÓMO SE VE EN EL DASHBOARD: invisible (es una diferencia entre dos instrumentos de auditoría).
- CÓMO REPRODUCIRLO: `python -B v03_fondo_via_vs_oraculo.py` §4.
- CONFIANZA: CONFIRMADO el tamaño; la descomposición por causa (geometría, centro, exclusión) es SOSPECHA.
- GRAVEDAD: 2.

### VPCC750-05. El anillo del oráculo S162 va de `inner_radius_km` a 25 km (A6): en PCC mide 20 a 25 km, y además es `>` y no `>=`

- ARCHIVO:LÍNEA: `pcc750/src/s162/oraculo_ablacion.py:177` y `:222`; docstring l. 14; contra `process_viirs_mod.py:570`.
- QUÉ PASA: ver A6. Es un defecto del instrumento de S162 cuando se usa en volcanes con inner distinto de 5 (PCC 20,
  Tupungatito 7, Lastarria y Planchón 3, Copahue 4): los brazos «anillo» y «compuerta» del oráculo original no miden
  el fondo de K ahí. En Chillán (inner 5) sólo difieren `>` contra `>=` (una corona de celdas a 5,00 km exacto, que en
  la grilla de 750 m no existe) y el centro.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `grep -n "dk <= 25.0" pcc750/src/s162/oraculo_ablacion.py`.
- CONFIANZA: CONFIRMADO (leído y, con el arreglo «525» del auditor, medido: 27 a 30 pasadas distintas).
- GRAVEDAD: 2 (instrumento; en producción no corre).

### VPCC750-06. «En la ventana del auto-audit la pendiente no se ve» es falta de poder, no ausencia: con n = 22 la banda del barajado es ±0,45 y las medianas caen igual

- SCRIPT:SALIDA: `v02_salida.txt` («auto-audit con ceros» 0,390 / 0,154, Spearman -0,236 dentro de [-0,422, +0,501];
  «auto-audit publicadas» 0,677 / 0,255 n = 10 / 6). `rerun/s01_salida.txt` ventana auditoria.
- QUÉ PASA: el auto-audit mira 2 meses; el fenómeno necesita más pasadas de borde de barrido para salir del ruido.
  La lectura correcta es SIN DATO en la ventana corta, no «no hay pendiente».
- CÓMO SE VE EN EL DASHBOARD: el auto-audit (`data/audit_continuous/latest.json`) marca PCC 0,512 «causa sin medir»
  por noche; no muestra el cenit.
- CÓMO REPRODUCIRLO: `python -B v02_razon_k_pareo_propio.py`, sección «ventana del auto-audit».
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

### VPCC750-07. «Ni posición ni suma» se sostiene, con el límite de que la distancia de MIROVA no tiene acimut

- SCRIPT:SALIDA: `v03_salida.txt` §6; `rerun/s01_salida.txt` («pc n_pixels», «dist pc al volcán km»);
  `rerun/s03_salida.txt` («dist K - celda C más cerca km» 0,000).
- QUÉ PASA: ver A4. Lo que una cota escalar no puede decir (A93, A107) es si el cúmulo de K y el de MIROVA son el
  mismo objeto; lo que sí se mide es que el cúmulo de K cae en la celda del píxel más radiante de la vía en 20 de
  20 pasadas con ambos.
- CÓMO SE VE EN EL DASHBOARD: el marcador de PCC VIIRS 750 está en el lacolito en los dos tramos de cenit.
- CÓMO REPRODUCIRLO: `python -B v03_fondo_via_vs_oraculo.py` §6.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

## 5. SEGUIMIENTOS (fuera de mi eje)

- S-1. **V750-B y la vía**: si la lectura de V750-B se hace con el runner N (`oraculo.geo_linear`, port R2) o con el
  oráculo S162 en vez de con `pipeline.mirova_v750_codigo`, hereda el fondo sin perturbar de VPCC750-01: en PCC las
  magnitudes de cenit alto salen 5 a 40 % bajas. SOSPECHA sobre qué instrumento usa `analizar_v750b.py`; no lo abrí.
  Lo mismo vale para las conclusiones de V750-C en Chillán (S162), que se midieron con el oráculo (SOSPECHA, no medido
  acá). Confianza: SOSPECHA. Archivo: `experiments/_s162_v750b/PREREGISTRO_V750B.md` §9 l. 189.
- S-2. `volcanoes.yaml:54` `local_kernel_bg: true` en PCC y `process_viirs_mod.py:462-469` dice que en M-band no está
  implementado: texto contra código, pero en el sentido inocuo (el yaml promete algo que V750 no hace). Confianza:
  CONFIRMADO (leído). No es de mi eje; vale para que nadie lea «kernel local» como fondo de K en V750.
- S-3. La pérdida aceptada del 2026-10-10 05:54 (#865, #881): la vía la publica a 1,00 de MIROVA (1,193 MW contra
  1,19) con B1, B2, B3 y B5; K no arma cúmulo. Sacarla de las 53 no cambia A1 (-0,512 FUERA). Confianza: CONFIRMADO.
- S-4. El prerregistro V750-B §8 predice «B2 ... pierde alguna protegida de Cordón Caulle»; en las 72 pasadas del
  censo B2 no pierde ninguna de 8. Es una predicción falsable que, en este subconjunto, falla: la lectura de V750-B
  debería mirarlo explícitamente. Confianza: CONFIRMADO en el subconjunto; SOSPECHA en la población.
- S-5. B3 (inner 20) publica 4 de 28 negativos limpios sobre 30° contra 1 de 28 de B1 y B2: en PCC el círculo de 20
  km mete sobre-publicación de borde de barrido. Confianza: CONFIRMADO (n chico).

## 6. VERIFICADO LIMPIO

- Copia del auditor = `origin/main` f20495d3 en los 12 archivos que decide (CSV del scraper, JSON de PCC,
  `latest.json`, procesadores, perfil, yaml, `clase_mirova.py`, `calidad_referencia_mirova.py`): sha256 iguales
  normalizados a LF. Comando: el bucle `git show origin/main:$f | tr -d '\r' | sha256sum` de esta sesión. Vara:
  `origin/main` de hoy tras `git fetch origin --prune`.
- Oráculo y `ablacion.py` = `origin/loop/activo:experiments/_s162_v750c/` (sha256 iguales).
- Re-corrida de s00 a s05 en copia (`rerun/`): s02, s03, s04, s05 y los 6 CSV/JSON con 0 líneas de diferencia; s01
  sólo cambia la ruta impresa; s00 idéntico. Vara: los archivos del auditor.
- Identidad del número de alertados entre la vía de producción (`caja_roi` def y sens) y el oráculo (O y S) en
  72 de 72 pasadas (`v01`, «identidad_def_sens_ok 72»). Vara: `s02_por_pasada.csv`.
- Predicado del tablero: `control_identidad_predicado` ([0, 1, 1, 1, 0], [1, 0]) en s01; `disp` = `pc.vrp_mw` en 39 de
  39 publicados (v02). Vara: `frontend/index.html` ejecutado con node.
- Cenit: `sensor_zenith_deg` presente en 53 de 53 pares y 72 de 72 grillas; contra el píxel central del gránulo
  mediana 0,275°, máximo 1,27° (rerun s02).
- Pareo: 0 alertas sin record a ±120 s, 0 con más de un candidato; referencia corrida +1 día deja 3 de 39 (v02) y
  0 de 72 (v01). VRP de MIROVA de la vara = `mirova_vrp` del objetivo del censo en 29 de 29.
- Controles positivos: ×2 dobla las medianas (v01, v02); +10 % de M13 en los alertados cambia el VRP en 27 / 27 / 30 /
  27 pasadas (B1 / B2 / B3 / B5); la caja `def` alerta una fuente sintética en el cráter desde +0,05 a +0,08 W.

## 7. SIN DATO

- Esfuerzo del agente con que corrí: no legible desde adentro.
- Los brazos nativos F, FC y C del runner N: no re-derivados desde gránulos (no hay L1B en disco; bajarlos exigiría
  credenciales, prohibidas por la tarea). Los números de A2 («K 0,425 y F 1,128») y A7 («F 1,3») están re-corridos
  desde `resultados_*.json`, no re-medidos.
- Equivalencia MATLAB de la triangulación perturbada de la vía: tomada de la prueba de oro del repo; no hay MATLAB acá.
- Pendiente de las publicadas de K en el subconjunto de 29 con grilla: n = 3 sobre 30°.
- Suomi NPP: 4 alertas en abril a noviembre; no se puede estratificar.
- Qué instrumento usa la lectura de V750-B (`analizar_v750b.py`): no lo abrí (fuera del alcance).

## 8. FUERA DE ALCANCE

- Chillán, Tupungatito y los demás volcanes; MODIS y VIIRS 375.
- El informe del auditor (`pcc750/INFORME.md`): no leído a propósito.
- La decisión de qué pieza corregir (fondo o remuestreo): mi entregable es la evaluación. Lo que esta verificación
  deja para esa decisión: en PCC, el déficit de nivel de K es del fondo de anillo (A2 confirmada), la caída con el
  cenit de K es de ceros Y de magnitud publicada (VPCC750-03), y la vía de producción con una ROI que cubra el
  lacolito queda plana en mediana y cerca de 1 (VPCC750-02), con un Spearman residual débil al borde del barajado que
  este subconjunto de 29 no alcanza a decidir.
- Arreglos: ninguno; no toqué nada fuera de `ver_pcc750/`.
