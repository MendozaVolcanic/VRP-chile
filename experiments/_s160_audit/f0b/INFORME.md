# F0b S160: verificación de los 6 hallazgos de S158 sin verificar (F4-H2, H3, H5, H7, H8 y R2-17)

- Hora del servidor: inicio Thu, 22 Oct 2026 04:19:47 GMT; cierre 04:28:47 GMT más la escritura (cabecera `Date` de api.github.com).
- Commit medido: origin/main `d516b9d8c0fad5b0ca458b9fb57cdf5e6f75f956`; código y datos de la instantánea
  `D:\vrp-trabajo\temporales\s160_audit\main\`; `data/mirova/` de ese commit extraído con `git archive` a
  `D:\vrp-trabajo\temporales\s160_audit\f0b\data\mirova\` (984 KB).
- Referencias: tabla sola `latest_consolidado.csv` (sha256 bc1522c24c924cb5...), combinado tabla más OCR
  `registro_vrp_ocr.csv` (sha256 94679246acbd0db5...), y además la configuración por defecto que usó S158
  (`cargar_referencia_unificada()`: `registro_vrp_consolidado.csv` 2e2c268e8811cdc1... más OCR, histórico y respaldo).
- OSF v2.5: `VRP_GLOBAL_ARCHIVE_2025.csv` (sha256 0863c2407eadd097...), 615.470 filas.
- Modelo y esfuerzo: Claude Opus 5.5, esfuerzo bajo (verificador).
- CARPETA: `C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\f0b\`. `caminos.md` sellado (sha256 7cef7ab0..., 04:20:49 GMT)
  antes de abrir ningún archivo citado; las secciones de `experiments\_s158_audit\f4\INFORME.md` (l. 100 a 133, 151 a
  164, 184 a 205) y `docs/AUDIT_S158_R2.md` l. 160 a 180 las leí DESPUÉS de sellarlo.
- Búsqueda previa por ID en `experiments\_s159\` y `experiments\_s160_audit\` (f1a, f2, f3, f4, v2, v3, v4): 0
  coincidencias para los seis IDs; ninguno estaba resuelto antes.
- Qué NO miré: el punto (c) de F4-H5 (jepv6, Vulcano); el segundo pase de los Tests 2 y 3 (su μ y σ no se persisten);
  el efecto en publicaciones del mínimo de dETI de cumbre (falta el dETI por píxel); MODIS y VIIRS 375 en el código
  de MIROVA (no existe); nada de L1B (prohibido por la tarea). Ninguna llamada a la API de GitHub salvo la cabecera
  `Date` (2 consultas `curl -sI`, sin autenticación).

## En una pantalla

1. Ninguno de los seis cae entero; dos quedan sólo en parte y uno ya estaba registrado fuera de main.
2. **Nuevo, gravedad 3 (V0b-01)**: K1 no decide la detección en producción (el primer pase reemplaza la máscara), pero
   **sí decide el tope D9 de 5 MW**: con K1 = -0,7 (el valor del código de MIROVA en VIIRS 750, candidato del A/B
   «detector del código») Nevados de Chillán SNPP 750 del 2026-10-01 06:00 pasaría de 11,08 MW publicado a 5,0 MW,
   contra 10,0 MW de MIROVA (OCR). F4-H2 no lo vio porque midió el valor de MIROVA, no el uso de K1 en nuestro código.
3. **F4-H3 REFUTADO EN PARTE (V0b-03)**: el mínimo de cumbre 0,003 es inerte en el dNTI (Test 2) pero gobierna el umbral
   del dETI (Test 3) en 14,4 % (MODIS), 5,6 % (VIIRS 375) y 16,6 % (VIIRS 750) de las pasadas nocturnas.
4. **F4-H2 CONFIRMADO EN PARTE (V0b-02)**: «cero negativos sobre -0,8» vale con el combinado y con la referencia de S158;
   con la tabla sola aparece 1 negativo de VIIRS 375 en -0,781 (Láscar, 2026-03-04 05:30), y la tabla es la que decide en
   esa fecha (A119). F4-H5 y F4-H8 CONFIRMADOS en RENDER; F4-H7 CONFIRMADO en el hecho y YA RESUELTO en el registro
   (fuera de main); R2-17 CONFIRMADO con un control positivo que el script original no tenía.

## Veredictos por hallazgo de la lista

| ID | veredicto | G (mía) | G (S158) | resumen |
|---|---|---|---|---|
| F4-H2 | CONFIRMADO EN PARTE | 2 | 1 | números reproducidos exactos con la referencia de S158; con tabla sola 1 negativo V375 sobre -0,8; en producción K1 decide el tope D9 (V0b-01, aparte) |
| F4-H3 | REFUTADO EN PARTE | 2 | 2 | inerte en dNTI (confirmado), NO inerte en dETI; «la caja» está apagada en producción |
| F4-H5 | CONFIRMADO | 2 | 2 | piso duro en los 6 estratos (0 filas bajo el piso), con control de piso falso; (c) jepv6 SIN DATO |
| F4-H7 | CONFIRMADO; registro YA RESUELTO fuera de main | 1 | 2 | -0,5 en `.m` l. 189, -0,6 en `pipeline/profile.py:202`; rama apagada; marca en commit 09f484aa2 (no en d516b9d8c) |
| F4-H8 | CONFIRMADO | 1 | 1 | Tabla 2, p. impresa 336, sólo MODIS, Wright et al. 2002 (RENDER) |
| R2-17 | CONFIRMADO (con matiz de instrumento) | 1 | 1 | 0 diferencias de gráfico ni de tarjeta en 74.811 records de main; mutación de control da 6.801; el control sintético original no distinguía nada |

### F4-H2: K1 casi no decide en Chile; cota K1 ≥ -0,87, no separa -0,8 de -0,7

Caminos comprobados: (1) referencia en tres versiones; (5) tabla contra combinado; (6) uso de K1 en NUESTRO código.

- Medición: `v0b_01_k1_y_minimos.py` → `.out`. Pregunta 1: si hubiera negativos sobre los K1 candidatos, la medición
  los cuenta (lo hace: aparece uno con tabla sola). Pregunta 2: `nti_max` nulo se cuenta aparte (12 a 14 en VIIRS 375,
  0 en el resto); n = 0 imprimiría SIN DATO. Control positivo: los positivos sí cruzan -0,7 (VIIRS 375 25 de 1.392),
  así que el campo puede tomar valores altos. Ventana de los datos: 2026-03-01 a 2026-10-21, 27.190 records
  nocturnos de los 11 Tier A, todos con el detector K (22.297 con `codigo_sha` 3695f6758 del reemplazo del histórico,
  #883/#884).
- Con la referencia por defecto de S158 los números de F4 se reproducen exactos sobre los datos de main (MODIS
  -0,864 n = 5.168; V375 -0,868 n = 3.834; V750 -0,877 n = 5.994; positivos 44/25 en V375, 11/5 en V750, 1 en MODIS).
- Combinado (tabla + OCR sin capas histórico/respaldo): igual, 0 negativos sobre -0,8 en los tres sensores.
- **Tabla sola**: VIIRS 375 negativo limpio máximo **-0,781** (1 de 3.927 sobre -0,8). Es Láscar, VIIRS_NOAA20
  2026-03-04 05:30, `diag_nti_max` = -0,7814 (`v0b_03_neg_tabla_sola.out`). Con el combinado esa pasada es `sin_info`
  porque el OCR trae una ALERTA_TERMICA_OCR de 0,55 MW a las 05:06 esa noche que la tabla no tiene. A119 dice que antes
  del 2026-06-13 la etiqueta que decide es la de la tabla sola, así que la cifra «cero negativos sobre -0,8 en los
  tres» no sobrevive en la versión que decide; pero la pasada sólo parece limpia porque la tabla perdió la alerta de las
  05:06 (defecto conocido de la tabla), así que no es evidencia fuerte de K1_375 > -0,8. La conclusión de fondo
  (los negativos no separan -0,8 de -0,7) se sostiene; la frase «cero en los tres» no.
- Camino 6 (por otro lado): en producción el camino B (NTI > K1, `pipeline/process_viirs.py:1030-1035`) entra a
  `combine_hot_paths` (l. 1255), pero el primer pase de los Tests 2 y 3 reemplaza la máscara (`hot_mask_2d = fp_hot`,
  l. 1328; `ENABLE_FIRST_PASS_TESTS_2_AND_3 = True` leído de `pipeline.profile`). K1 tampoco toca el fondo
  (`ENABLE_TEST1_K1_BG_EXCLUDE = False`) ni el retiro (`ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK = False`). O sea que
  «casi no decide» es cierto para la detección también por el lado del código. Pero queda un camino: el tope D9
  (V0b-01).

### F4-H3: el mínimo de cumbre 0,003 es inerte en los tres sensores; decide 5σ y la caja

- Medición: misma salida, sección M2, por estrato de etiqueta y para dNTI **y** dETI. Control positivo: la fracción
  bajo la mediana da 0,500 en todos los estratos (el instrumento ve fracciones distintas de cero). Pregunta 2: nulos de
  μ/σ contados aparte (8 MODIS, 76 V375, 1 V750 de todas).
- dNTI (Test 2), todas las pasadas nocturnas: μ + 5σ < 0,003 en 47 de 5.582 (0,84 %) MODIS, 2 de 10.768 (0,02 %)
  V375, 17 de 10.755 (0,16 %) V750; en positivos, 0 en los tres. **Confirmado: inerte en el dNTI.**
- dETI (Test 3), mismo denominador: μ + 5σ < 0,003 en **802 de 5.582 (14,4 %) MODIS, 603 de 10.768 (5,6 %) V375,
  1.785 de 10.755 (16,6 %) V750**; en positivos (referencia S158) 2 de 96, 143 de 1.392 (10,3 %) y 61 de 324 (18,8 %).
  Con la conectiva `max` (S153, `ENABLE_TESTS_23_PROSE_BRANCH = True`), el umbral de cumbre del dETI es
  `max(0,003, μ + 5σ)` (`pipeline/detection_context.py:530-537` para dNTI; el dETI pasa `c1_deti_summit = _c1_sum`,
  `pipeline/process_viirs.py:1306-1309`), así que en esas pasadas el 0,003 es el umbral que manda en el Test 3. El paper
  pone el mismo C1 para los dos índices (Coppola et al. 2016a, SP 426, p. 7, columna izquierda, RENDER: «a minimum
  threshold (for both dNTI and dETI) needs to be exceeded»; Tabla 1, ROI1 noche C1 = 0,003) y el código de MIROVA
  de VIIRS 750 también (`MIROVA_VIIRS750_hotspot_detection.m` l. 187, `minimumETIcontrastROI2 = 0.003`).
- Cuánto cambia lo publicado: **SIN DATO** (hace falta el dETI por píxel; `anomaly_pixels` no lo persiste). Que el
  umbral gobierne no implica que decida una publicación: el Test 2 también debe cumplirse.
- «La caja»: `ENABLE_ROI1_BOX_PAPER = False` en producción; hoy la cumbre es el círculo de `inner_radius_km`. La frase
  vale como agenda de medición (D18), no como descripción de producción.
- Veredicto: REFUTADO EN PARTE. Ver V0b-03.

### F4-H5: el OSF v2.5 no puede dar umbrales de detección; sus pisos son los filtros de Coppola 2026

- Paper, RENDER (`experiments\_s158_audit\f4\paginas\Coppola_2026_SciData_p8.png`, p. 8 del PDF, continuación de la
  Tabla 1): «Nighttime VRP threshold (W)» 1.0 × 10⁵ (MODIS), 5.0 × 10⁶ (750), 1.0 × 10⁴ (375); «Daytime VRP threshold
  (W)» 5.0 × 10⁷ en los tres.
- Otro camino (`v0b_04_osf_pisos.py` → `.out`): en los 6 estratos sensor × día/noche hay **0 filas bajo el piso** y el
  mínimo cae justo encima (375 noche 10.004,3 W; 750 noche 5.000.049 W; 1000 noche 100.013 W; día 5,0001 a 5,003 × 10⁷).
  Control: con un piso falso de 2× aparecen miles de filas por debajo (1.454, 20.442, 2.377 de noche), y con 0,5× el
  primer decil queda vacío, o sea que el instrumento distingue un piso real de uno inventado. La densidad junto al piso
  no es cero (103 a 2.980 filas en el primer 10 %), así que el filtro corta una distribución viva: lo que hay debajo no
  está. Y K1, C1 y C2 están en unidades de NTI/dNTI, que el VRP agregado no recupera.
- Matiz: la ventana del archivo que reporto (`timeUTC` mínimo como texto «01/01/2001») difiere de la de S158
  (2000-02-24, parseado); es el formato dd/mm, no afecta nada.
- (b) «Npix = 1 en 151 de 82.782» no lo recalculé (lo trae `02_osf_v25_por_sensor.out`); (c) jepv6: SIN DATO.
- Veredicto: CONFIRMADO. Coincide con A105, que ya decía que el OSF está filtrado; F4-H5 lo baja a cifras por sensor.

### F4-H7: K1 diurno -0,5 en el código, -0,6 en la rama diurna apagada

- `C:\vrp-trabajo\s159-m\experiments\_s158_d17_diseno\osf_codigo_mirova\MIROVA_VIIRS750_hotspot_detection.m`
  (sha256 6b73c84f8bd0a7ff...): l. 178 `absoluteNTIthreshold = -0.7` (noche), l. 189 `absoluteNTIthreshold = -0.5`
  (día); día 15/15 σ, mínimos 0,02 en dNTI y dETI (l. 191-198). Nuestro: `pipeline/profile.py:202`
  `NTI_K1_DAY = -0,6` (sin clave en `mirova_equivalent.yaml`, así que rige el valor por defecto);
  `pipeline/diurno.py:137` lo usa para VIIRS 375 y 750 por igual; `C2_DNTI_DAY = C2_DETI_DAY = 15`,
  `DNTI_CONTEXTUAL_C1_DAY = 0,02` (leídos de `pipeline.profile`). La Tabla 1 de Coppola 2016a (p. 7, RENDER) trae
  K1 diurno -0,6 en ROI1 y ROI2.
- Flags leídos de `pipeline.profile`: `ENABLE_DAYTIME_VIIRS = False`, `ENABLE_DAYTIME_MODIS = False`. Invisible hoy.
- «El informe S158 no lo registra»: cierto para `docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md` (l. 107, 147 y 202 sólo
  traen K1 de noche). **YA RESUELTO** después: `docs/AUDIT_S158.md` l. 110 («el código trae la rama diurna (K1 -0,5,
  glint bajo 12°)»), `docs/AUDIT_S158_R2.md` l. 205 (VB-3) y la marca A113 en `docs/MIROVA_DIVERGENCES.md` D27
  (commit 09f484aa2, 2026-10-21 14:25 -0300, en `origin/claude/s158-audit-r2-0eeee2` y ramas s159). **Pero ninguno de
  esos tres documentos está en main d516b9d8c** (`git show d516b9d8c:docs/AUDIT_S158.md` no existe;
  `git show d516b9d8c:docs/MIROVA_DIVERGENCES.md | grep -c -- '-0,5'` = 0). Quien lea main hoy no lo ve.
- Veredicto: CONFIRMADO; G 1 hoy, 3 el día que se corra el A/B diurno de S151 con -0,6.

### F4-H8: Coppola 2025 cap. 11 Tabla 2 no es evidencia para VIIRS

- RENDER `experiments\_s158_audit\f4\paginas\libro_cap11_p340.png` (p. impresa 336, cabecera «D. Coppola»), Tabla 2:
  la fila NTI trae Nighttime «−0.8», Daytime «−0.6», Satellite «Terra(MODIS) Aqua(MODIS)», Reference «Wright et al.
  2002». No hay fila de VIIRS. Coppola et al. 2016a, p. 6, columna derecha, RENDER (`sp426.5_p6.png`): «settled
  according to the global application and validation of the NTI thresholds within the MODVOLC algorithm».
- Uso como evidencia para VIIRS: `docs/audit_s146/FRENTE_F_FIDELIDAD_VIIRS.md:655` (en la instantánea de main) cita
  esa Tabla 2 en la tabla de fidelidad de VIIRS como «Lo SOSTIENE ... aunque atribuido a MODIS». El uso en
  `pipeline/profile.py:198` es para MODIS diurno, correcto.
- Veredicto: CONFIRMADO, G 1.

### R2-17: las tres vistas coinciden en efecto (0 diferencias sobre 74.811 records)

- Re-corrí el script de S158 apuntado a main (`v0b_05_tres_vistas.js`, mismo instrumento, rutas cambiadas): 74.811
  records, último 2026-10-21 08:10 (el mismo conteo que en el worktree; contado aparte con Python en los dos árboles).
  Gráfico index contra diario, index contra mosaico, diario contra mosaico y tarjeta index contra mosaico: **0**.
  Sólo aparece la categoría «diario grafica > 0 pero index no lo titularía»: 2 records de Puyehue (2025-11-17 06:24
  NOAA-21, 0,037 MW; 2026-01-17 04:54 NOAA-20, 0,165 MW), ninguno en 90 días. No es una divergencia entre copias del
  mismo elemento: el gráfico de index también los muestra; es tarjeta contra gráfico.
- **Matiz de instrumento**: el «control positivo» del script de S158 no distingue nada (el record sintético da 3,3 en
  las tres vistas y las dos variantes legacy dan lo mismo en las tres), así que el 0 de S158 no tenía control. Agregué
  uno real: apagar `USE_F5_CORE` sólo en la copia de diario (`CONTROL=f5off`) produce **6.801** diferencias (710 en 90
  días) en «index contra diario» y «diario contra mosaico» (`v0b_05_tres_vistas_control_f5off.out`). Con eso el 0 vale.
- Latente en el texto: 34 volcanes no Tier A con `innerKm` efectivo 10 en index y 5 en diario (diario sólo grafica los
  11 Tier A). Confirmado por la misma salida.
- Veredicto: CONFIRMADO, G 1.

## Hallazgos propios

### V0b-01
- TÍTULO: K1 decide el tope D9 de 5 MW en producción: con K1 = -0,7 (código de MIROVA, VIIRS 750) Chillán 2026-10-01 06:00 bajaría de 11,08 a 5,0 MW
- ARCHIVO:LÍNEA: `pipeline/process_viirs_mod.py:669-677` (camino B, `nti > NTI_K1_NIGHT`), `:1003` (`n_nti_path`), `:1009-1016` (`_path_d_cap_active` exige `n_nti_path == 0`), `:1110-1112` (aplica el tope al `primary_cluster`); igual en `pipeline/process_viirs.py:1030-1035, 1434, 1439-1446` y `pipeline/process_modis.py:713-717, 1050, 1061`. SCRIPT:SALIDA `v0b_01_k1_y_minimos.out` (sección «K1 en produccion») y `v0b_02_ndc_tope_k1.out`.
- QUÉ PASA: un píxel con NTI sobre K1 y 3 K sobre el fondo cuenta como «camino duro», y su sola presencia desactiva el tope de 5 MW que se aplica a los cúmulos contextuales con fondo frío (bajo 270 K). En Chillán, en erupción, hay noches donde el píxel más caliente tiene NTI entre -0,8 y -0,7: con K1 = -0,8 el tope no actúa; con -0,7 actuaría. Sobre 10.756 records nocturnos de VIIRS 750 (2026-03-01 a 2026-10-21), 17 tienen camino B, 9 lo perderían con -0,7, 2 tienen además fondo bajo 270 K y `pc.vrp_mw` > 5: Nevados de Chillán SNPP 2026-10-01 06:00 (`diag_nti_max` -0,7518, `t_bg_k` 268,76, 11,084 MW) y NOAA-20 2026-10-13 05:54 (-0,7952, 259,59, 5,93 MW). MIROVA (OCR) dio 10,0 MW en VIIRS 750 a las 06:00 del 2026-10-01 (protegida). En VIIRS 375 cambiaría el estado del tope en 38 records, todos bajo 5 MW (sin efecto); en MODIS en 0.
- CÓMO SE VE EN EL DASHBOARD: hoy, nada (K1 = -0,8). Si se adopta K1 -0,7 en VIIRS 750 (A/B «detector del código», `docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md` l. 277), el operador vería Chillán a 5,0 MW en vez de 11,08 MW esa pasada, contra 10,0 MW de MIROVA; la publicación sigue (predicado del tablero con node: `[1,1,0,5,1]` contra `[1,1,0,11.084,1]`).
- CÓMO REPRODUCIRLO: `python v0b_01_k1_y_minimos.py` y `python v0b_02_ndc_tope_k1.py` en CARPETA; volcán NevadosDeChillan, VIIRS_SNPP_750 2026-10-01 06:00 UTC y VIIRS_NOAA20_750 2026-10-13 05:54 UTC. El valor capado (5,0) está simulado sobre una copia del record, no reprocesado.
- CONFIANZA: CONFIRMADO el mecanismo (código leído, campos del record leídos); el valor final publicado bajo K1 -0,7 es SOSPECHA (pasos posteriores al tope, como el modo de un píxel, no los simulé).
- GRAVEDAD 1-5: 3 (mueve un A/B pendiente; el acoplamiento K1 → tope no está en ningún documento que encontré).

### V0b-02
- TÍTULO: «cero negativos sobre -0,8 en los tres sensores» (F4-H2) no vale con la tabla sola: 1 negativo de VIIRS 375 en -0,781
- ARCHIVO:LÍNEA: SCRIPT:SALIDA `v0b_01_k1_y_minimos.out` (bloque `t_tabla_sola`) y `v0b_03_neg_tabla_sola.out`.
- QUÉ PASA: en Láscar la noche del 2026-03-04 MIROVA alertó a las 05:06 (OCR, 0,55 MW) y la tabla perdió esa fila; con la tabla sola la pasada NOAA-20 de las 05:30 (RUTINA en la tabla) queda como negativo limpio, y nuestro NTI máximo ahí es -0,7814. La cota pasa de -0,868 a -0,781 en VIIRS 375 según la referencia, y en esa fecha A119 manda decidir con la tabla sola.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python v0b_03_neg_tabla_sola.py`; Lascar, VIIRS_NOAA20, 2026-03-04 05:30 UTC.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD 1-5: 2 (no decide nada hoy; muestra que la cota depende de la versión de la referencia, que el plan exige informar en las dos).

### V0b-03
- TÍTULO: el mínimo de cumbre 0,003 NO es inerte en el Test 3: gobierna el umbral del dETI en 5,6 a 16,6 % de las pasadas
- ARCHIVO:LÍNEA: `pipeline/process_viirs.py:1306-1309` (`c1_deti_summit = _c1_sum`, `c2_deti_summit = 5`); conectiva `max` por `ENABLE_TESTS_23_PROSE_BRANCH = True`. SCRIPT:SALIDA `v0b_01_k1_y_minimos.out` (M2, columna dETI).
- QUÉ PASA: en escenas homogéneas la dispersión del dETI es tan baja que μ + 5σ queda bajo 0,003, y entonces el umbral fijo del paper manda en el Test 3: 802 de 5.582 MODIS, 603 de 10.768 VIIRS 375, 1.785 de 10.755 VIIRS 750 (todas las pasadas nocturnas, 2026-03-01 a 2026-10-21); en positivos 18,8 % en VIIRS 750. F4-H3 midió sólo el dNTI.
- CÓMO SE VE EN EL DASHBOARD: SIN DATO de cuánto cambia lo publicado (falta el dETI por píxel).
- CÓMO REPRODUCIRLO: `python v0b_01_k1_y_minimos.py`, sección M2.
- CONFIANZA: CONFIRMADO que el piso gobierna el umbral; SOSPECHA que decida publicaciones.
- GRAVEDAD 1-5: 2 (ordena qué número de cumbre importa para VIIRS 375; no se sabe si tuerce una alerta).

## SEGUIMIENTOS

- `experiments/_s158_audit_r2/m2/05_tres_vistas.js` l. 141-150: el «control positivo» no produce diferencias entre
  copias; cualquier medición futura de vistas con ese script necesita una mutación real, como la de `CONTROL=f5off` en `v0b_05_tres_vistas.js`. CONFIRMADO, G 1.
- `docs/audit_s146/FRENTE_F_FIDELIDAD_VIIRS.md:655`: usa la Tabla 2 del cap. 11 como respaldo del K1 de VIIRS (F4-H8).
  CONFIRMADO, G 1.
- Registro en main: las marcas de S158 R2 sobre el K1 diurno (D27) no están en d516b9d8c (F4-H7). CONFIRMADO, G 1.
- La tabla `latest_consolidado.csv` no trae la alerta de Láscar 2026-03-04 05:06 que sí trae el OCR (V0b-02): un caso
  más de filas perdidas por la carrera del scraper. CONFIRMADO, G 1.

## VERIFICADO LIMPIO

- Los números de M1 y M2 de F4 se reproducen exactos sobre los datos de main con la referencia por defecto
  (`python v0b_01_k1_y_minimos.py`, bloque `o_S158_por_defecto`); vara: el script original y sus etiquetas.
- En producción el camino B no entra a la detección: `pipeline/process_viirs.py:1328` (`hot_mask_2d = fp_hot`) con
  `ENABLE_FIRST_PASS_TESTS_2_AND_3 = True`, `ENABLE_TEST1_K1_BG_EXCLUDE = False`,
  `ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK = False`, `ENABLE_TEST1_PATH = False` (todos leídos de `pipeline.profile` con
  `VRP_PROFILE=mirova_equivalent` sobre la instantánea); vara: el código de main.
- Piso duro del OSF en 6 estratos con control de piso falso (`v0b_04_osf_pisos.out`); vara: Tabla 1 de Coppola 2026 en
  RENDER.
- Tabla 1 de Coppola 2016a en RENDER: K1 noche -0,8 / día -0,6, C1 0,003 / 0,01 / 0,02 / 0,02, C2 5 / 10 / 15 / 15.
- Predicado del tablero ejecutado con node (`banco_paridad.correr_node`) y su control de identidad
  `([0,1,1,1,0],[1,0])` (`v0b_02_ndc_tope_k1.out`).
- Tres vistas: 0 diferencias con control positivo de 6.801 (`v0b_05_tres_vistas*.out`).

## SIN DATO

- Efecto en publicaciones del mínimo de dETI de cumbre (V0b-03): falta el dETI por píxel en los records.
- Segundo pase: su μ y σ (recalculados sin los activos, `detection_context.py:927`) no se persisten; no sé si ahí el
  0,003 gobierna también el dNTI.
- F4-H5 (c), jepv6: no lo miré.
- Valor exacto publicado bajo K1 -0,7 en V0b-01 (requiere reproceso, prohibido en esta tarea).

## FUERA DE ALCANCE

- Cualquier arreglo (incluida la decisión de si el tope D9 debería depender de K1).
- K1 de MIROVA para VIIRS 375 y MODIS en su código (no publicado).
