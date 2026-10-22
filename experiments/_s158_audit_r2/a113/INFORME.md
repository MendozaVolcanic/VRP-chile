# A113, segunda ronda S158: las marcas pendientes de la tabla de F2, verificadas contra el código de MIROVA

Fecha: 2026-10-21. Worktree: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s158-audit-r2-0eeee2`.
Carpeta: `experiments/_s158_audit_r2/a113/` (todas las rutas de scripts y salidas de abajo son relativas a ella).

Leí de la primera ronda sólo lo que el alcance permite: la tabla de 22 afirmaciones (§3 de
`experiments/_s158_audit/f2/INFORME.md`) y la lista de 10 pruebas (H9 de ese informe, sólo su tabla). No leí
`docs/AUDIT_S158.md`, ni los demás informes, ni `docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md`. Las marcas «S158» que ya
estaban en los documentos las traté como afirmaciones a verificar.

## 0. La vara, leída por mí

- `MIROVA_VIIRS750_hotspot_detection.m` (444 líneas) y `MIROVA_VIIRS750_VRP.m` (92 líneas), leídos enteros, y el
  `README.txt` («compact», «not the complete operational MIROVA near-real-time processing chain»).
- **El comentario del código rotula al revés la ROI de cumbre.** Dice que `BOX == 1` es la ROI central y `BOX == 2` la
  extendida (l. 105 a 118). La matriz de ejemplo dice lo contrario (`m08_box_forma.txt`): `BOX == 2` es la caja central
  de 7 × 7 celdas (5,25 km a 750 m, filas y columnas 30 a 36 de 67 × 67) y `BOX == 1` es un rectángulo de 21 × 19
  celdas (15,75 × 14,25 km) menos esa caja; `BOX == 0` es el resto de la ventana de 50 km. Con eso, los umbrales que el
  código llama «ROI2» (5 σ, mínimos 0,003 en NTI y en ETI, de noche) caen en la cumbre, igual que la ROI1 de la Tabla 1
  del paper; los que llama «ROI1» (10 σ, mínimo 0,02 en NTI y 0,01 en ETI) rigen fuera, en `BOX == 1` y `BOX == 0`
  (l. 177 a 199, 389 a 399). Quien lea `minimumNTIcontrastROI1 = 0.02` como «cumbre» se equivoca.
- Paper Coppola 2016a (`documentacion/sp426.5.pdf`) **renderizado a imagen** (p. 5 a 8: `sp426_p5.png` a
  `sp426_p8.png`) y capítulo Coppola 2025 (`documentacion/978-3-031-86841-2.pdf`, p. PDF 341 = impresa 337:
  `coppola2025_cap_pdf341.png`).
- OSF v2.5 (`VRP_GLOBAL_ARCHIVE_2025.csv`, 615.470 filas, 2000-01-03 a 2025-12-12): `m02`, `m03`, `m04`.
- Port mínimo propio de la detección sobre la matriz de ejemplo: `m07_port_mini_ejemplo.txt` (5 alertas, todas en
  `BOX == 2`: 4 del primer pase, 1 del segundo, 0 absolutas).

### Mediciones (cada una con sus dos preguntas en el encabezado del script)

| id | qué mide | resultado | denominador y ventana | ¿ve una falla? / ¿instrumento muerto? |
|---|---|---|---|---|
| m01 | clases de `BOX` en el ejemplo | 0: 4.090, 1: 350, 2: 49 celdas; 0 NaN | matriz 67 × 67 del ejemplo (VJ1, 2023-05-19 00:54) | sí: si la caja no fuera la central, el bounding box lo mostraría / imprime shape y conteos |
| m02 | ¿`Npix` del OSF cuenta píxeles o regiones? | `Tot_Lmir_bk/Npix` plano con el tamaño: V750 0,41 / 0,35 / 0,33 para Npix 2-4 / 5-20 / >20, junto a Planck(280 K, 4,05 µm) = 0,34; V375 0,175 / 0,171 / 0,185; MODIS 0,30 / 0,33 / 0,43 | 100.641 filas V750, 252.374 V375, 262.455 MODIS con Npix > 0, OSF 2000-2025 | sí: si contara regiones de 5 a 50 píxeles la razón crecería 5 a 50 veces / control positivo: VRP recomputado = OSF en mediana 1,000 |
| m03 | VRP negativo y distancia máxima en el OSF | 0 VRP < 0 en los tres sensores; mínimo V750 = 5,0 MW, V375 = 0,01 MW, MODIS = 0,1 MW; `Max_Dist` V750 p50 2,7 km, p99 25,5 km, máx 30 km | mismas filas | **NO** para el recorte de ΔL: el OSF está filtrado por VRP mínimo por sensor, así que un VRP negativo no puede aparecer aunque exista. No lo cuento como verificación del recorte |
| m04 | coeficiente y área de V750 en el OSF | `ΔL × 1,97e7 × 0,5625` = VRP del OSF dentro de 1 % en 92.402 de 100.641 filas (91,8 %); con área 0,75 km²: 0 filas | filas V750 del OSF | sí: el control con 0,75 da 1,333 en mediana y 0 % de coincidencias |
| m05 | flags efectivos de `mirova_equivalent` (vía `pipeline.profile`) | `NTI_K1_NIGHT = -0,8`, `NTI_K1_DAY = -0,6`, `DNTI_CONTEXTUAL_C1_SCENE = 0,01`, `PATH_D_ONLY_CAP_MW = 5,0`, `ENABLE_SECOND_PASS_ADJACENT = True`, `ENABLE_SECOND_PASS_CONDITIONED = False`, `ENABLE_UNSUITABLE_FILTERS_267_273 = True`, `ENABLE_EXCLUDE_ZONES = False` | perfil cargado al 2026-10-21 | el script imprime el nombre del perfil cargado |
| m06 | ¿hay filtro de reflejo solar en el pipeline? | 0 líneas en `pipeline/` y `scripts/run_pipeline.py` | árbol de hoy | control positivo: el mismo grep sobre el .m de MIROVA da 8 líneas |
| m07 | port mínimo de la detección | pase 1: [0, 0, 4] por BOX 0/1/2; pase 2: [0, 0, 1]; ΔL por píxel todos positivos, VRP ≈ 10,0 MW | 1 escena de ejemplo | control positivo: alertas > 0 en la caja. El control «pase con alertas previas vacías = pase 1» da True **por construcción** de mi port, así que no verifica nada del MATLAB: la afirmación sobre el segundo pase descansa en la lectura del código (l. 211 a 235). Sin ΔL negativos, no distingue recorte de no recorte. El fondo usa `griddata` lineal, no `fillmissing2` |
| m08 | forma exacta de las ROI | `BOX == 2` = caja 7 × 7; `BOX == 1` = rectángulo 21 × 19 menos la caja | ejemplo | comparación celda a celda, imprime los conteos |

## 1. Tabla de las 22 afirmaciones

Las líneas de `CLAUDE.md`, `docs/MISSION.md` y `docs/MIROVA_DIVERGENCES.md` son las de hoy, después de mis
ediciones (varias corrieron respecto de la tabla de F2).

Veredicto: CONFIRMADA LA REFUTACIÓN, CON MATIZ (se dice cuál), NO SE SOSTIENE (la refutación), SIN DATO. En las
filas 14 a 22 la tabla de F2 ya decía que la premisa se sostiene; ahí el veredicto es sobre la premisa
(CONFIRMADA) y no corresponde marca. «Pruebas»: A = suite de lectores de documentos y archivos de prueba tocados,
386 pasan, 1 skip, 1 xfail (`pytest_despues_marcas.txt`, contra 381/1/1 de `pytest_linea_base.txt` antes de editar; la
diferencia de 5 es `test_local_kernel_modis.py`, agregado a la segunda corrida); B = suite completa sin el oráculo,
2.347 pasan, 29 skip, 1 xfail, 0 fallas (`pytest_suite_completa.txt`); C = lectores de CLAUDE.md y MISSION.md tras las
últimas dos marcas, 157 pasan (`pytest_lectores_claude_mission.txt`).

| n | afirmación sobre MIROVA | dónde | mi veredicto | evidencia | marca puesta | pruebas |
|---|---|---|---|---|---|---|
| 1 | reporta `n_hotspots` = regiones contiguas; «factor 42 no es bug» | `CLAUDE.md:1709-1720`; `docs/MIROVA_DIVERGENCES.md:36-41`; `docs/MISSION.md:350-355`; `docs/HYPOTHESIS_LOG.md:810`; `experiments/50_FACTOR_42_HALLAZGO.md:42-50` | **CONFIRMADA LA REFUTACIÓN** en los tres sensores (no trasladada: el OSF trae MODIS y V375) | `MIROVA_VIIRS750_VRP.m:61, 83-85`; m02 (fondo por unidad de Npix plano y en Planck(280 K)) | CLAUDE, DIVERGENCES D1 y MISSION: **ya marcadas** (S158), y mi verificación sostiene el núcleo («cuenta píxeles»); sus números 0,67 y «Láscar 4 contra 3» NO los verifiqué. `HYPOTHESIS_LOG.md`: **sí** (nueva). `experiments/50_...`: no (fuera de lo editable). `tests/test_cluster_hotspots.py`: **sí** (comentario) | A, B |
| 2 | segundo pase «sólo si hubo detección y sólo adyacentes» (D2) | `docs/MIROVA_DIVERGENCES.md` D19 (l. 2615, «D2 condicionado como manda Coppola 2016a»); `docs/PREREGISTRO_AB_D1_D2_S135.md:38-42, 84, 180`; `mirova_equivalent.yaml:434-440`; `pipeline/detection_context.py:883-898` | **CON MATIZ**: en VIIRS 750 la condición (a) es **nula en efecto** (con el primer pase vacío el segundo recibe las mismas entradas y devuelve lo mismo, l. 211-235: la única diferencia entre las dos llamadas es `previouslyDetectedAlerts`), y la (b) adyacencia **no existe** (l. 389-399 sobre toda la escena). El paper (p. 7 renderizada) sí dice las dos: para V375, que es lo que mide el pre-registro, la refutación es TRASLADADA | lectura del .m; `sp426_p7.png` | D19: **ya marcada** (l. 2524), dice lo mismo que yo en la parte de código; sus números «19 de 67» no los verifiqué. Pre-registro: **sí**. `tests/test_second_pass_conditioned_s135.py`: **sí** | A, B |
| 3 | «MIROVA no usa máscaras geográficas» | `docs/MISSION.md:302`; `CLAUDE.md` A4 (l. 227); `mirova_equivalent.yaml:291-294` | **CON MATIZ**: refutada en su forma absoluta para V750 (el código admite píxeles NaN en `BOX` y su comentario declara ROI adaptadas por volcán, incluso para excluir volcanes vecinos u otras fuentes térmicas persistentes); **SIN DATO** de si MIROVA excluye algo en Chile (el ejemplo trae 0 NaN, m01); «no en papers» no lo revisé | `.m` l. 25-29, 120-128, 140, 171, 288, 330, 369 | MISSION: **sí**. CLAUDE A4: **sí**. `tests/test_enable_exclude_zones_flag.py`: **sí**. YAML: no (`pipeline/`) | A, B |
| 4 | V750: 12 σ noche, 8 σ día (Di Bella) como «canónico» | `documentacion/BIBLIOGRAPHY_SYNTHESIS.md:248` (fuera de git; leí la tabla en la l. 248 de la raíz del repo) | **CONFIRMADA LA REFUTACIÓN** para V750 (código: 5 σ cumbre / 10 σ fuera de noche, 15 σ de día). Para V375: no hay código; sólo ajena a MIROVA por A9 | `.m` l. 177-199; m08 | El archivo: no (fuera de lo editable y fuera de git). Puse la marca en el puntero que lo presenta como «SOURCE OF TRUTH» (`CLAUDE.md` l. 60, encima de la l. 66): **sí** | A, B, C |
| 5 | fondo del VRP = media de los 8 vecinos «Coppola 2024 L1129 literal» (D8 RESUELTO) | `docs/MIROVA_DIVERGENCES.md` D8 (l. 1303, marca debajo del encabezado); `mirova_equivalent.yaml:450-461`; `pipeline/vrp_regimes.py:39-55` | **CONFIRMADA LA REFUTACIÓN, y más ancha que en la tabla de F2**: (1) la cita L1129, **renderizada**, es una frase condicional del **modelo de dos componentes**, no el fondo del VRP de MIROVA (hallazgo H-R2-1); (2) en V750 el código aparta los vecinos (dilatación 3, 5 o 7) e interpola con `fillmissing2`. Para MODIS el respaldo posible de un fondo local es otro (Coppola 2016a p. 8, «surrounding the active one»); ahí la refutación por código es TRASLADADA | `coppola2025_cap_pdf341.png`; `MIROVA_VIIRS750_VRP.m:63-85`; `sp426_p8.png`; `pipeline/process_viirs_mod.py:460-467` (en M-band el kernel no corre) | D8: **sí**. D25: **ya marcada** (sostengo su texto: halo por npix ≤ 4, ≤ 30, > 30; interpolación lineal; sin recorte). `tests/test_local_kernel_background.py`: **sí**. YAML y `vrp_regimes.py`: no (`pipeline/`) | A, B |
| 6 | de día K1 = -0,6, C1 = 0,02, C2 = 15 para VIIRS; sin filtro de reflejo | `docs/MIROVA_DIVERGENCES.md` D27 (l. 2875 y su marca S151 diurna); `pipeline/diurno.py:128`; `experiments/_s151_ab_diurno/PREREGISTRO.md:18` | **CON MATIZ**: K1 **refutado** en V750 (código -0,5); C1 y C2 **confirmados** (0,02 y 15 en las dos ROI y en NTI y ETI); el rechazo por reflejo solar bajo 12° **no existe** en nuestro pipeline (m06). Para V375, -0,6 TRASLADADO | `.m` l. 83-89, 188-199; m05; m06 | D27: **sí**. `tests/test_rama_diurna_viirs_s151.py`: **sí**. `diurno.py` y el pre-registro de experiments: no | A, B |
| 7 | contraste contra «los 8 vecinos» (media aritmética) | `CLAUDE.md` l. 148 y 177; `docs/MISSION.md:131`; `mirova_equivalent.yaml:114`; `pipeline/detection_context.py:146-155` | **CON MATIZ**: media aritmética confirmada; el conteo **refutado** en V750 (3 × 3 con el central: sin NaN el contraste vale 8/9 del de 8 vecinos, así que los mínimos fijos quedan 9/8 más exigentes). Paper renderizado p. 5: «eight neighbouring pixels», vale para MODIS y V375 | `.m` l. 281-294, 362-368; `sp426_p5.png` | CLAUDE l. 148: **ya marcada** por el punto S158 de l. 123 («media de 3 × 3 con el central»), sostengo. CLAUDE l. 177: **sí** (marca en l. 171). MISSION: **ya marcada** (l. 124), sostengo. `tests/test_detection_context.py`: **sí** | A, B |
| 8 | fuera de la cumbre C1 = 0,010 «Table 2» | `CLAUDE.md:146`; `mirova_equivalent.yaml:116-124`; `docs/MIROVA_DIVERGENCES.md` D9 S45 (l. 1100) | **CON MATIZ**: en V750 el mínimo fuera es 0,02 en NTI y 0,01 en ETI (sólo la mitad cae). La Tabla 1 del paper (renderizada, «Table 1», no «Table 2») da 0,01 en ROI2: vale para MODIS. Además el pasaje D9 S45 deduce una «summit-priority cluster selection» que el código de V750 no tiene: la alerta es la unión de todo y el VRP lo suma | `.m` l. 183-187, 241-248; `VRP.m` l. 83-91; m03 (`Max_Dist` hasta 30 km); `sp426_p7.png` | CLAUDE l. 146: **ya marcada** (punto de l. 123, «mínimo de dNTI fuera de la cumbre (0,02)»), sostengo. D9 S45: **sí**. YAML: no | A, B |
| 9 | K1 = -0,8 de noche para V750 | `mirova_equivalent.yaml:47`; `pipeline/process_viirs_mod.py:481` | **CONFIRMADA LA REFUTACIÓN** (código -0,7). Efectivo hoy: -0,8 (m05) | `.m` l. 178 | YAML y código: no (`pipeline/`). Lo dejé dicho en el comentario de `tests/test_unsuitable_filters.py` | A, B |
| 10 | el Test 1 K1 es «máscara de saturación, no reportable» | `pipeline/detection_context.py:974-984`; `tests/test_drift1_test1_k1_saturation.py:1`; `docs/MIROVA_DIVERGENCES.md:1263` (plan S46, histórico) | **CONFIRMADA LA REFUTACIÓN** por el paper **y** por el código: p. 6 renderizada, «flagged as 'active'»; el código publica los absolutos en `alert` | `sp426_p6.png`; `.m` l. 201-206, 245 | test: **sí**. `detection_context.py`: no (`pipeline/`). DIVERGENCES l. 1263: no, la fila #1 de la misma tabla ya dice «NO ES DRIFT (S100)» | A, B |
| 11 | ΔL se recorta a cero («Wooster physics») | `pipeline/process_viirs_mod.py:1055-1056`; `tests/test_vrp_negative_clip.py:1-9` | **CONFIRMADA LA REFUTACIÓN** para V750 por lectura del código (sin `max` ni recorte de la suma). El OSF **no puede** verlo (filtrado por VRP mínimo, m03), y mi port no tuvo ΔL negativos (m07): ninguna de las dos mediciones cuenta | `VRP.m` l. 83-85 | test: **sí**. D25: **ya marcada**, sostengo. Código: no | A, B |
| 12 | dETI < -0,1 es no apto | `tests/test_unsuitable_filters.py:1-9`; `pipeline/process_viirs_mod.py:881` | **CON MATIZ**: refutada en el programa V750 (sólo el contraste de NTI < -0,1, l. 298; ninguno sobre ETI, l. 368-369); confirmada en el paper (p. 5 renderizada: «dNTI or dETI < -0.1») para MODIS y V375 | `.m` l. 298, 368-369; `sp426_p5.png` | test: **sí**. Código: no | A, B |
| 13 | inmunidad al cirrus por el tope de 5 MW (Opción C) | `docs/MIROVA_DIVERGENCES.md` D9 S71 (l. 304, marca debajo); `mirova_equivalent.yaml:506-507`; `CLAUDE.md` A23; `docs/MISSION.md` lista de Resueltas | **CONFIRMADA LA REFUTACIÓN como mecanismo de MIROVA** en V750: no hay tope ni compuerta por fondo; el único filtro térmico previo es BT de M15 ≤ 200 K. MODIS y V375 TRASLADADA | `VRP.m` l. 83-91; `.m` l. 147-154 | D9 S71: **sí**. A23: **sí**. MISSION (línea previa a «Resueltas»): **sí**. YAML: no | A, B, C |
| 14 | el segundo pase recalcula regresión y aplica el piso (D26 como divergencia) | `docs/MIROVA_DIVERGENCES.md` D26 | **CONFIRMADA** la premisa (el segundo pase llama a la misma función: recalcula polyfit, l. 335-350, y reaplica el piso de NTI, l. 298) | `.m` l. 228-235 | ya marcada (D26), sostengo; no corresponde marca nueva | n/a |
| 15 | no hay compuerta `bt > t_bg + 3 K` en MIROVA (D22) | D22 | **CONFIRMADA** | `.m` sin condición de BT en l. 389-399; sólo BT M15 ≤ 200 K (l. 151) | ya marcada (D22), sostengo | n/a |
| 16 | K1 alerta directa y fuera del fondo (D23, GAP #A) | D23 | **CONFIRMADA** | `.m` l. 206, 245, 276, 328 | ya marcada, sostengo | n/a |
| 17 | conectiva `max`, 5 σ y 0,003 en la cumbre, μ y σ de toda la escena | `docs/MISSION.md:7-17`; `CLAUDE.md:141` | **CONFIRMADA** (con la cumbre = `BOX == 2`, m08). Diferencia despreciable: `std(..., 0, ...)` es N-1 | `.m` l. 303-312, 373-382 | no corresponde | n/a |
| 18 | MIROVA publica la suma de todos los alertados, sin cúmulo ni tope (D32) | D32 | **CONFIRMADA** en el cálculo; matiz: el README declara fuera la parte de «near-real-time reporting», así que lo que el tablero NRT muestra no está en este código. El OSF suma píxeles hasta 30 km (m03) | `.m` l. 241-248; `VRP.m` l. 83-91 | ya marcada (D32), sostengo | n/a |
| 19 | un algoritmo por sensor; lo que varía por volcán es la geometría de la ROI | `docs/MISSION.md:169-174` | **CONFIRMADA** (umbrales fijos en el código; ROI adaptables, l. 120-125) | `.m` l. 120-125, 177-199 | no corresponde | n/a |
| 20 | MIROVA no filtra nubes | YAML l. 10; D14 | **CONFIRMADA con matiz**: no hay máscara de nube; sí descarta BT de M15 ≤ 200 K y escenas con la mitad o más de NaN | `.m` l. 147-154, 163-167 | no corresponde (la premisa no cae) | n/a |
| 21 | coeficiente 1,97e7 y área 0,5625 km² | `CLAUDE.md`, reglas científicas | **CONFIRMADA** por código y por el OSF (91,8 % exacto; 0 % con 0,75 km²). Ver H-R2-2 y H-R2-3 | `VRP.m` l. 88-89; m04 | no corresponde | n/a |
| 22 | la ROI de cumbre es una caja de celdas (D18) | D18 | **CONFIRMADA**; matiz de tamaño: en el ejemplo la caja mide 7 celdas = 5,25 km, no 5 km (`ROI1_BOX_HALF_KM = 2,5`, m05), y el código la declara adaptable por volcán | m08; `.m` l. 397-399 | no corresponde | n/a |

## 2. Las 10 pruebas de la lista H9

Ninguna aserción cambió. Los comentarios van encima de la prueba (o del docstring del módulo, que sigue siendo
docstring). Inserción con `insertar_marcas_tests.py` (conserva CRLF, aborta si el ancla no es única).

| prueba | premisa | mi veredicto | marca | resultado |
|---|---|---|---|---|
| `tests/test_cluster_hotspots.py` | n_hotspots = regiones | REFUTADA (n 1) | sí | pasa (A, B) |
| `tests/test_second_pass_conditioned_s135.py` | condiciones (a) y (b) como regla de MIROVA | CON MATIZ: fiel al paper (vara de V375), no al código de V750 (n 2) | sí | pasa |
| `tests/test_vrp_negative_clip.py` | recorte de ΔL | REFUTADA en V750 (n 11) | sí | pasa |
| `tests/test_unsuitable_filters.py` | dETI < -0,1; K1 -0,8 | CON MATIZ (n 12) y REFUTADA en K1 (n 9) | sí | pasa |
| `tests/test_local_kernel_background.py` | L1129 literal | REFUTADA, cita mal leída (n 5) | sí | pasa |
| `tests/test_drift1_test1_k1_saturation.py` | retirar el K1 del reporte es «literal» | REFUTADA por paper y código (n 10) | sí | pasa |
| `tests/test_rama_diurna_viirs_s151.py` (l. 114) | K1 = -0,6 de día en VIIRS | CON MATIZ (n 6) | sí | pasa |
| `tests/test_enable_exclude_zones_flag.py` | exclude_zones no es MIROVA | CON MATIZ (n 3) | sí | pasa |
| `tests/test_detection_context.py` (l. 251) | 8 vecinos, media aritmética | CON MATIZ (n 7) | sí | pasa |
| `tests/test_daytime_modis.py` | Tabla 1 día y noche en MODIS | NO APLICA: MODIS, manda el paper, y la Tabla 1 renderizada da K1 -0,6, C1 0,02, C2 15 de día | no | pasa (B) |

Agregué además `tests/test_local_kernel_modis.py` (cita L1129, hija de n 5, fuera de la lista): marca sí, pasa.

## 3. Hallazgos nuevos

### H-R2-1. La cita «Coppola 2024 L1129 literal» que sostiene el kernel local de fondo (D8) es una frase del modelo de dos componentes, no el método de fondo del VRP
- ARCHIVO:LÍNEA: `documentacion/978-3-031-86841-2.pdf`, p. PDF 341 = impresa 337, renderizada en
  `coppola2025_cap_pdf341.png`; citada en `docs/MIROVA_DIVERGENCES.md` D8, `docs/HYPOTHESIS_LOG.md` (S57),
  `docs/MIROVA_DETAILED_CITATIONS.md:5-6` y §9, `docs/F66_BG_KERNEL_LOCAL_DEEP_S78.md:53`, `CLAUDE.md` A12,
  `tests/test_local_kernel_background.py:3`, `tests/test_local_kernel_modis.py:5`.
- QUÉ PASA: la frase dice que **si** la temperatura de fondo se toma de los píxeles adyacentes, la ecuación 14 (píxel
  mezcla de fuente caliente y fondo) se puede resolver suponiendo T_hot o A_hot: es el modelo de dos componentes de
  Dozier. El VRP de MIROVA es otra fórmula (ec. 17 de la misma página) y no dice de dónde sale el fondo. El proyecto
  adoptó en S57 a S62 un fondo de 8 vecinos llamándolo «literal» sobre esa frase. En VIIRS 750 el código de MIROVA hace
  lo opuesto: aparta los vecinos.
- DASHBOARD: invisible como cita; el efecto es la magnitud de los 5 volcanes con `local_kernel_bg: true`.
- REPRODUCIR: renderizar la página 341 del PDF del libro con PyMuPDF (`get_pixmap(dpi=110)`).
- CONFIANZA: CONFIRMADO (página leída como imagen).
- GRAVEDAD 2: no tuerce una alerta directamente; quita el respaldo citado a una elección de fondo que hoy sólo se
  justifica por su resultado empírico de S61/S62. Para MODIS hay otro respaldo posible (Coppola 2016a p. 8, renderizada:
  «arithmetic mean of all the pixels surrounding the active one (or around the active cluster)»).

### H-R2-2. El capítulo Coppola 2025 da para VIIRS 750 un área de píxel de 0,75 × 10⁶ m², que no es la que usa MIROVA
- ARCHIVO:LÍNEA: misma página (impresa 337, ec. 17 y párrafo siguiente); m04.
- QUÉ PASA: el texto da `A_pix = 0,75 × 10⁶ m²` para las bandas M de 750 m; el código usa 0,5625 km² y el OSF lo
  reproduce en 91,8 % de las filas, con 0 % usando 0,75 km². Parece una errata (0,75 km de lado, no de área).
- DASHBOARD: invisible hoy; ningún documento ni código nuestro cita ese 0,75 (`grep` sin coincidencias en `docs/`,
  `CLAUDE.md`, `pipeline/*.py`). Si alguien lo tomara del capítulo, el VRP de VIIRS 750 subiría 1,33 veces.
- REPRODUCIR: `python m04_osf_coef_area.py`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD 1.

### H-R2-3. En 8,2 % de las filas de VIIRS 750 del OSF el VRP publicado no es `ΔL × 1,97e7 × 0,5625`
- SCRIPT:SALIDA: `m04_osf_coef_area.txt`: 8.239 de 100.641 filas fuera de 1 %, razón recomputado/publicado p5 1,24,
  p50 1,97, p95 5,08 (siempre mayor que 1); 5.529 de satélite 3 y 2.710 de satélite 4.
- QUÉ PASA: en esas filas el VRP publicado es menor que el que dan las sumas `Tot_Lmir_hot - Tot_Lmir_bk` de la misma
  fila. No sé por qué (agregación de varias pasadas, recorte por distancia aplicado sólo al VRP, otra cosa).
- DASHBOARD: invisible.
- CONFIANZA: SOSPECHA en la causa; el conteo es CONFIRMADO.
- GRAVEDAD 1 para A113; importa a quien use el OSF como vara de magnitud (fuera de mi alcance).

### H-R2-4. El comentario del código de MIROVA invierte los nombres de las ROI respecto del paper
- ARCHIVO:LÍNEA: `MIROVA_VIIRS750_hotspot_detection.m:105-118` contra `m08_box_forma.txt`.
- QUÉ PASA: lo que el código llama `ROI1` (umbrales 10 σ, 0,02 / 0,01) es el exterior; lo que llama `ROI2` (5 σ, 0,003)
  es la caja de cumbre. La Tabla 1 del paper llama ROI1 a la cumbre. Ninguno de los pasajes que marqué cae en esta
  trampa, pero una lectura literal de los nombres del código la produce.
- CONFIANZA: CONFIRMADO. GRAVEDAD 2 si alguien porta el código copiando nombres (pondría los umbrales estrictos en la
  cumbre).

## 4. Citas fuera de la tabla (otros documentos que repiten las afirmaciones)

Marcadas en esta ronda: `docs/HYPOTHESIS_LOG.md` (H_S23_FACTOR42 y la implementación L1129 de S57),
`docs/MIROVA_DETAILED_CITATIONS.md` (encabezado, cubre su §9), `CLAUDE.md` A12 (L1129) y A23 (tope), `docs/MISSION.md`
(línea previa a la lista de «Resueltas»: D8 y D9), `tests/test_local_kernel_modis.py`.

Sin marcar (documentos históricos o fuera de lo editable), por afirmación:
- n 1 (n_hotspots / factor 42): `docs/DRIFTS_S17.md:380`; `docs/MIROVA_DIVERGENCES_CATALOG_S71.md:40, 45`;
  `docs/F47_NDC_RECALL_S76.md:481`; `docs/SESSION_INDEX.md:23`; `docs/AUDIT_INTEGRAL_S81.md:49` y
  `docs/AUDIT_S121_MEJORA_INTEGRAL.md:381` (estos dos hablan del campo `n_hotspots_clustered`, no de MIROVA);
  `experiments/50_FACTOR_42_HALLAZGO.md:42-50`.
- n 5 (L1129): `docs/F66_BG_KERNEL_LOCAL_DEEP_S78.md:53`; `docs/MIROVA_DIVERGENCES_CATALOG_S71.md:12`;
  `pipeline/vrp_regimes.py:39-55`; `pipeline/process_viirs_mod.py:461`; `mirova_equivalent.yaml:450-461`.
- n 4 (12 σ / 8 σ de Di Bella): 13 documentos mencionan «n=12» o «12σ» (`grep -rln` en `docs/`, lista en la sesión:
  AUDIT_S128, AUDIT_S134, DATA_SUBDIRS_INVENTORY_S80, DRIFTS_S17, F28_DATA_ARCHIVE_INVENTORY, HYPOTHESIS_LOG, MISSION,
  PAPERS_AUDIT, RESEARCH_WORKFLOW, S122_ANGLE_BIAS_FINDING, SESSION_INDEX, SESSION_INDEX_CONSOLIDATED_S80,
  papers_mirova_processed_S72_backlog). No los leí uno por uno: no sé cuáles lo presentan como MIROVA. Pendiente.
- n 9, 10, 11, 12 (comentarios de código): `pipeline/process_viirs_mod.py:481` (K1 noche -0,8 / día -0,6),
  `:1055` («Wooster physics»), `:881`; `pipeline/detection_context.py:974-984` («MÁSCARA DE SATURACIÓN»);
  `pipeline/diurno.py:128`; `pipeline/profiles/mirova_equivalent.yaml:47, 114, 116-124, 291-294, 434-440, 506-507`.
  Todos en `pipeline/` (A45): quedan para quien orquesta.
- n 6: `experiments/_s151_ab_diurno/PREREGISTRO.md:18` (fuera de lo editable).

## 5. Fuera de alcance

- H-R2-3 (8,2 % del OSF de V750 con VRP menor que el de sus propias sumas) merece su propio frente si el OSF se usa
  como vara de magnitud.
- El punto S158 de `CLAUDE.md:123` dice «difiere de producción en 10 de 13 puntos»: no verifiqué el conteo. Las
  cuatro diferencias que nombra (K1 -0,7; 0,02 fuera de la cumbre en dNTI; 3 × 3 con el central; fondo interpolado bajo
  halo, sin recorte) sí las verifiqué contra el código.

## VERIFICADO LIMPIO

- Las marcas S158 de la primera ronda sobre D22, D23, D25, D26, D29 y D32 en `docs/MIROVA_DIVERGENCES.md` dicen lo
  que dice el código (leídas una por una: `grep -n "> ⚠️ \*\*S158, código de MIROVA\*\*" docs/MIROVA_DIVERGENCES.md`),
  incluido el halo de D25 (npix ≤ 4 → 3, ≤ 30 → 5, si no 7; `VRP.m` l. 68-74).
- La marca S158 de D19 (segundo pase) coincide con mi lectura independiente en lo que afirma del código.
- Coeficiente 1,97e7 y área 0,5625: `python m04_osf_coef_area.py`.
- `Npix` del OSF cuenta píxeles en los tres sensores: `python m02_osf_npix.py`.
- Los umbrales nocturnos de cumbre (5 σ, 0,003 en NTI y ETI) caen en la caja 7 × 7: `python m01_box_matriz.py`,
  `python m08_box_forma.py` y `.m` l. 177-187.
- Paper Coppola 2016a: «eight neighbouring pixels», «dNTI or dETI < -0.1» (p. 5), Test 1 «flagged as 'active'» (p. 6),
  Tabla 1 y segundo pase condicionado (p. 7), fondo «surrounding the active one» (p. 8): imágenes `sp426_p5.png` a
  `sp426_p8.png`.
- Ninguna prueba quedó roja por las ediciones: `pytest_linea_base.txt` (381 pasan antes), `pytest_despues_marcas.txt`
  (386), `pytest_lectores_claude_mission.txt` (157), `pytest_suite_completa.txt` (2.347 pasan, 0 fallas; sin
  `tests/test_oraculo_mirova_v750_s158.py`, excluido por la regla de independencia).
- Las líneas que agregué no traen guiones largos ni medios (`git diff -U0 | grep '^+'`: la única coincidencia es
  texto viejo de A12 conservado en la misma línea, anterior a esta ronda).

## Lo que no pude medir

- **El recorte de ΔL en datos de MIROVA**: el OSF está filtrado por VRP mínimo por sensor (5 MW en V750), así que un
  VRP negativo no puede aparecer aunque MIROVA no recorte; y la escena de ejemplo no tiene ΔL negativos. La refutación
  de n 11 descansa sólo en la lectura del código.
- **Que el segundo pase de MIROVA sea nulo con el primero vacío** lo saco de la lectura: mi port lo confirma por
  construcción, no contra MATLAB (no tengo MATLAB ni la salida esperada del ejemplo; `run_example.m` no la trae).
- **MODIS y VIIRS 375**: no hay código; toda refutación trasladada desde V750 quedó marcada TRASLADADA, no confirmada.
- **Si MIROVA excluye píxeles o mueve ROI en los volcanes chilenos** (n 3): la matriz de ejemplo es de un volcán no
  chileno y no trae NaN; no hay otra fuente en el repo.
- **«No está en papers»** para `exclude_zones` y para el recorte de ΔL: no barrí los 11 papers.
- **Los números de las marcas de la primera ronda** (razón 0,67, «Láscar 4 contra 3», «19 de 67», «10 de 13»): no los
  reproduje; sostengo sólo la parte de código de esas marcas.
- **Los 13 documentos que citan 12 σ**: no los leí uno por uno.
- No corrí `tests/test_oraculo_mirova_v750_s158.py` (regla de independencia).
