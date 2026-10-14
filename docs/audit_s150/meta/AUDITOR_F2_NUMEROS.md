# Meta-auditoría S150, frente F2: re-medir los números que hoy deciden el plan (S147 a S150)

> Auditor F2, 2026-10-09. Eje: **re-ejecutar, no releer**. No modifiqué ningún archivo del repo; mis scripts y
> salidas están en `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s150_meta_audit\F2\`.
> Las extracciones de los runs (git archive con ruta, sin `git fetch`: las refs `origin/s146-ab/<run>` ya estaban en
> el clon) y las tablas por pasada quedaron en el scratchpad de la sesión, no en el repo. Envoltorio sin fetch:
> `experiments\_s150_meta_audit\F2\ev_sin_fetch.py` (llama al `evaluar_ventana.py` original sin tocarlo).

## 0. En una pantalla

**Todos los números de cabecera se reproducen al dígito**, corriendo los mismos scripts sobre los mismos runs:
la conectiva `max` de septiembre (29,8 a 2,7 %, 137 a 135 de 143), los cinco meses de abril a agosto (salida
de `medir_predicciones` idéntica byte a byte salvo encabezados), el agregado (829 de 2.324 a 63; 946 de 988),
MODIS en Láscar (B 0/73, J 68/73 y 11/96, K 67/73 y 2/96), el costo oculto (50 apagadas, 34 con RUTINA VRP 0,
14 de las 16 sin fila son Suomi NPP), las 46 alertas débiles y su tabla, el residual (57,3 % contra 9,1 %) y
las 858 detecciones lejanas de MIROVA.

**Reproducir con el mismo script sólo prueba que nadie transcribió mal** (pregunta 1 del instrumento: un
defecto compartido por el instrumento no se vería). Por eso agregué cinco mediciones independientes. Ninguna
voltea la decisión sobre `max` en VIIRS 375; dos cambian cómo se presenta y una cambia el peso de un frente:

| # | hallazgo | gravedad |
|---|---|---|
| H1 | Las "858 detecciones lejanas" que sostienen la regla de la anomalía mayor son **58 % diurnas** (498); de noche, que es lo único que la réplica procesa, son **360** | 3 |
| H2 | El "2,7 % en negativos limpios" mide sólo el 34 % de las pasadas; en las pasadas sin veredicto de MIROVA en noches sin alerta (1.838) F publica **6,6 %** | 2 |
| H3 | El "F pierde entre 25 y 44 % de lo que B publica bajo 0,05 MW" **no se reproduce**: es 15 a 38 % por mes, n de 4 a 15; agregado 24 % [14, 37] | 2 |
| H4 | "36 pérdidas confiables" son **34** con la regla del propio S150 (ningún OCR de Suomi NPP es etiqueta confiable); y con esa regla el camino D22 pesa **13 de 30** (43 %), no 15 de 42 | 2 |
| H5 | El "F conserva 95,7 %" esconde a Chaitén: **29 de 35 (82,9 %)**; y los negativos los ponen volcanes tranquilos mientras las positivas las ponen Láscar, Isluga, Cordón Caulle y Lastarria | 2 |
| H6 | AUDIT_S149 rotula su tabla "del 1 al 21 de septiembre", pero la celda MODIS "11,5 %" sale de otra ventana (marzo a septiembre); la de septiembre da 12,5 % | 1 |
| H7 | La fila de agosto del §0 de S150_RESULTADO_MESES sigue diciendo **NO ADOPTAR** sin marca en la fila, aunque sus dos pérdidas fuertes ya se declararon filas del OCR con la imagen de otra pasada | 1 |

**Qué cambia para el plan.** (a) La decisión de recall de `max` que espera a Nicolás se puede contestar con un
número agregado y su intervalo: bajo 0,10 MW, F pierde 12,6 % [9,0, 17,4] de lo que B publica con la etiqueta
completa y 13,9 % [9,7, 19,6] con la confiable; sobre 0,5 MW, **0 de 119** con la etiqueta confiable. (b) El
pre-registro del A/B "vent_anchored contra vrp_max" debe trabajar con las 360 lejanas nocturnas, no con 858.
(c) Con etiquetas confiables, la mitad de las pérdidas de la tabla (12 de 24) viene del camino D22 más segundo
pase: el A/B de D22 (hoy suspendido, #773) pesa más de lo que decía el "15 de 42".

## 1. Inventario de afirmaciones numéricas que sostienen decisiones, y su estado

Ventana de cada número entre corchetes. "Brazos" = reproceso con el código de hoy (mismo régimen, no cruza #535
dentro de un A/B); "producción" = records escritos por el código de su época.

| afirmación (fuente) | ventana | se reproduce | cómo |
|---|---|---|---|
| `max` en V375: negativos limpios 29,8 a 2,7 %; recall 137 a 135 de 143 (S148) | 2026-09-01 a 09-20, post #535 | **sí** | por un camino distinto del evaluador original: `armar_tabla.py` + `agregado.py` sobre `experiments/_s147_lectura/.../prelim_s148` → 111/373 a 10/373; 137/143, F conserva 135 (`F2/sept_agregado_mio.txt`) |
| Costo oculto: 50 publicaciones apagadas en noches con alerta; 34 con RUTINA VRP 0, 16 sin fila (S149) | ídem | **sí** | c1, c2, c4 de `experiments/_s149_costo_oculto/` idénticos (`F2/costo_oculto/`); c3 idéntico salvo la línea de perfil |
| 14 de las 16 sin fila son Suomi NPP (memoria S149) | ídem | **sí** | `F2/m5_sin_fila_por_satelite.py`: sin fila 14 SNPP + 2 NOAA-20; RUTINA 11 SNPP, 14 N20, 9 N21 |
| Meses: negativos limpios B a F por mes; borde/nadir; recall por pasada; P5; C8b; determinismo (S150) | abril a agosto (agosto hasta el 27), pre #535 | **sí** | `ev_sin_fetch.py` por mes: salida idéntica a `resultados/<mes>_VIIRS375.txt` salvo encabezados (`F2/salidas/`) |
| Agregado: 829/2.324 (35,7 %) a 63 (2,7 %); F conserva 946/988 (95,7 %) y 684/708 tabla sola (S150) | abril a agosto | **sí** | `agregado.py` sobre mis 5 tablas, `diff` = IDENTICO (`F2/agregado_abril_agosto_mio.txt`) |
| Recall por tramo de magnitud (S150 §2) | abril, junio a agosto | **sí** | `recall_por_magnitud.py`, `diff` = igual (`F2/rpm_*.txt`) |
| "F pierde entre 25 y 44 % de lo que B publica bajo 0,05 MW" (S150 §0 l. 40) | abril a agosto | **no** | H3 |
| MODIS Láscar: B 0/73, 0/96; J 68/73, 11/96; K 67/73, 2/96, con Wilson (S150) | marzo a junio | **sí** | `modis_lascar_brazos.py` sobre mis extracciones, `diff` = IDENTICO (`F2/modis_lascar_mio.txt`) |
| Abril: el job repetido de Chaitén corrió "sin cambios en `pipeline/`" (S150 §1) | runs 35639417826 y 37823348991 | **sí** | `git diff --stat d46b7ec59 327621e2c -- pipeline/`: sólo cuatro perfiles `_s150_*.yaml` nuevos, cero código |
| Débiles: F pierde 46 de 1.143 (42 V375 + 4 V750); μ y σ idénticos entre brazos (S150) | abril a agosto | **sí** | `perdidas_max.py` sobre mis extracciones: `filas_mias.json` == `filas.json` (True); `clases_rechazo` IDENTICO |
| Débiles: 36 confiables; 27 por primer pase y 15 por D22 | abril a agosto | **parcial** | H4 |
| Residual: 57 % (borde, fondo < 260 K) contra 9 % (nadir, fondo > 270 K) (S147) | 2026-09-01 a 09-20 | **sí** | `estructura_del_residual.py` sobre run 35521542153: idéntico; sólo cambia "pasadas nuestras n" 12.407 a 13.299 (corpus vivo, A90) |
| Anomalía mayor: desde marzo, 1.398 alertas en radio y 858 lejanas a mediana 20 km (AUDIT_S150 §8) | 2026-03-01 a 10-09 | **parcial** | H1 (858 sí; 1.398 hoy da 1.401 por CSV vivo) |
| MODIS producción: 11,7 % de alertas contra 11,5 % de negativos (AUDIT_S149 l. 20-21) | mezcla | **parcial** | H6 |
| Producción: vent_anchored encendido y conectiva `max` apagada (AUDIT_S150 §8) | hoy | **sí** | `VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p; ..."` → `ENABLE_VENT_ANCHORED_CLUSTERING True`, `ENABLE_TESTS_23_PROSE_BRANCH False`; `pipeline/clustering.py:40,55,58` |

## 2. Hallazgos, de mayor a menor gravedad

### H1. Las 858 detecciones lejanas que justifican "gana la anomalía mayor" son mayoritariamente diurnas

- **SCRIPT:SALIDA**: `experiments\_s150_meta_audit\F2\m4_anomalia_mayor_858.py` → `m4_salida.txt`.
- **QUÉ PASA.** De día, el sol calienta el suelo y los incendios forestales arden con más fuerza, y el MIR diurno
  está contaminado por reflexión solar: MIROVA lista en su tabla muchas fuentes a 15 a 30 km del cráter en las
  pasadas de la tarde. La réplica sólo procesa la noche ("MIR solo nocturno"). El número que se usó para la
  decisión mezcla las dos. Sobre `latest_consolidado.csv` (2026-03-01 a 2026-10-09): 858 filas FALSO_POSITIVO
  con VRP > 0, **498 con hora UTC de 13 a 21** (pasadas de la tarde en Chile) y **360 entre 00 y 12 UTC**. Las
  nocturnas: 332 VIIRS 375, 17 VIIRS 750, 11 MODIS; mediana de distancia 20,56 km (cuartiles 15,61 y 24,52),
  VRP mediano 0,58 MW (contra 1,37 MW del total). Las ALERTA_TERMICA son casi todas nocturnas (1.377 de 1.401).
  Además: la columna "Clasificacion Mirova" = NULO de esas 858 **no es de MIROVA**, la escribe el scraper
  (`Mirova-v1/scraper.py` l. 144-154: `vrp > 0` y `dist > limite_km` → FALSO_POSITIVO, `es_alerta_real` False →
  clasificación NULO); no sirve como evidencia de que MIROVA las descarte ni de que las publique como alerta.
  Y que la tabla traiga una sola fila por pasada (0 pasadas con FALSO y ALERTA a la vez) no prueba que esa fila
  sea "la anomalía mayor" de la escena: es compatible con varias reglas de selección (SOSPECHA, no medido).
- **CÓMO SE VE EN EL DASHBOARD.** Invisible hoy. Si el A/B "vent_anchored contra vrp_max" se pre-registra con
  858 como tamaño del fenómeno, la expectativa de cuántas pasadas nocturnas cambian queda inflada 2,4 veces.
- **CÓMO REPRODUCIRLO.** `python experiments/_s150_meta_audit/F2/m4_anomalia_mayor_858.py` desde la raíz
  (lee `latest_consolidado.csv`, que es vivo: los conteos crecen).
- **CONFIANZA.** CONFIRMADO (conteos y código del scraper leídos). El corte 00-12 UTC como "noche" es
  aproximado y está declarado; el histograma por hora (`m4_salida.txt`, bloque M4b) muestra dos grupos
  limpios, 04-07 UTC y 17-19 UTC, así que el corte no es sensible.
- **GRAVEDAD 3.** Puede torcer el diseño y la expectativa del A/B que cambia la regla de selección del cúmulo
  en la réplica, que decide qué magnitud y qué distancia ve el operador cuando hay dos fuentes en la escena.

### H2. El 2,7 % en negativos limpios mide un tercio de las pasadas; en las pasadas sin veredicto de MIROVA, F publica 6,6 %

- **SCRIPT:SALIDA**: `F2/m11_sin_info_desglose.py` → `m11_salida.txt`; `F2/m11b_sin_veredicto_por_satelite.py`;
  `F2/m10_por_satelite.py` → `m10_salida.txt`.
- **QUÉ PASA.** El evaluador sólo juzga las pasadas donde MIROVA dio un veredicto (alerta, o RUTINA con VRP 0
  en una noche sin alerta). De las 6.864 pasadas V375 de abril a agosto, 3.276 quedan `sin_info`, fuera de todo
  denominador. Desglosadas: 605 RUTINA en noche con alerta (el estrato P5; F publica 14,0 %), 627 sin fila en
  noche con alerta (F 41,8 %, esperable: hay actividad esa noche), 206 RUTINA en noche con detección lejana
  (F 4,4 %) y **1.838 sin fila de MIROVA en noches sin alerta, donde F publica 121 (6,6 %)**, 2,4 veces la tasa
  de los negativos limpios. Por satélite: N20 5,2 %, N21 9,9 %, SNPP 5,4 % (1.090 de las 1.838 son SNPP, que la
  tabla casi no lista). Por zona, al revés que el residual del control: nadir 10,4 %, medio 6,9 %, borde 2,5 %.
  No es un error del número (está bien definido y declarado como "negativos limpios"); es que la frase "F calla
  donde MIROVA calla, 2,7 %" no describe lo que el operador verá: en esas 1.838 pasadas no sabemos si MIROVA
  calla, porque no las lista.
- **CÓMO SE VE EN EL DASHBOARD.** Con `max` adoptado, unas 24 publicaciones al mes (121 en 5 meses) en noches en
  que MIROVA no alertó y no dejó fila para esa pasada; el operador no puede contrastarlas con MIROVA.
- **CÓMO REPRODUCIRLO.** Extraer los cinco meses con `F2/ev_sin_fetch.py` (comandos en §4) y correr
  `python experiments/_s150_meta_audit/F2/m11_sin_info_desglose.py <tmp>/{abril,mayo,junio,julio,agosto}/tabla.json`.
- **CONFIANZA.** CONFIRMADO el conteo. "Sin fila" se infiere de `rutina_pasada` falso y etiqueta `sin_info`
  (aproximado, declarado en el script). Si esas 121 son calor real o ruido: SIN DATO.
- **GRAVEDAD 2.** No voltea `max`, pero la cifra de cabecera sub-representa lo que el tablero mostrará en las
  pasadas sin contraste, sobre todo de Suomi NPP.

### H3. "F pierde entre 25 y 44 % bajo 0,05 MW" no se reproduce; el número agregado cabe en una línea

- **ARCHIVO:LÍNEA**: `docs\S150_RESULTADO_MESES.md:40`. **SCRIPT:SALIDA**: `F2/m9_tramo_debil_agregado.py` →
  `m9_salida.txt`; `F2/rpm_abr.txt`, `F2/rpm_jja.txt`, `experiments\_s149_prereg_invierno\resultados\recall_por_magnitud_sept_mayo.txt`.
- **QUÉ PASA.** Un foco débil (lago de lava chico, fumarola) que apenas sube la radiancia de un píxel es lo
  primero que `max` apaga. Cuánto: pérdidas de F sobre lo que B publica bajo 0,05 MW, por mes, abril 1 de 4,
  mayo 2 de 13, junio 3 de 15, julio 3 de 10, agosto 3 de 8: **15 a 38 %**, no 25 a 44. Ninguna forma de
  cálculo que probé da 44 (en puntos porcentuales da 14 a 33; 44 es el complemento de "con max 56 %" de agosto,
  que tiene otro denominador). Con n de 4 a 15 por mes, la cifra mensual no sostiene un rango. Agregado de abril
  a agosto, con Wilson 95 %:

  | tramo de MIROVA | etiqueta completa: B publica, F pierde | etiqueta confiable (tabla, u OCR desde 06-13 sin Suomi NPP) |
  |---|---|---|
  | bajo 0,05 MW | 50; 12 (24,0 % [14,3, 37,4]) | 41; 11 (26,8 % [15,7, 41,9]) |
  | 0,05 a 0,10 | 188; 18 (9,6 % [6,1, 14,6]) | 146; 15 (10,3 % [6,3, 16,3]) |
  | bajo 0,10 total | 238; 30 (12,6 % [9,0, 17,4]) | 187; 26 (13,9 % [9,7, 19,6]) |
  | 0,10 a 0,50 | 561; 7 | 432; 4 |
  | 0,5 MW o más | 189; 5 (2,6 %) | **119; 0 (0,0 % [0,0, 3,1])** |

- **CÓMO SE VE EN EL DASHBOARD.** Con `max`, se apagaría del orden de una de cada ocho alertas bajo 0,10 MW
  que hoy (sin Test 1) se publicarían; sobre 0,5 MW, ninguna con etiqueta confiable.
- **CÓMO REPRODUCIRLO.** `python experiments/_s150_meta_audit/F2/m9_tramo_debil_agregado.py <tmp>/{abril,...,agosto}/tabla.json`.
  Control: los conteos por mes con etiqueta completa coinciden con `recall_por_magnitud.py` (junio bajo 0,05:
  B 15, F 12; julio B 10, F 7).
- **CONFIANZA.** CONFIRMADO.
- **GRAVEDAD 2.** Es exactamente la pregunta que queda en manos de Nicolás (AUDIT_S150 §8, decisión 1b); el
  rango citado la exagera y carece de intervalo.

### H4. Las pérdidas "confiables" son 34, y con esa regla el camino D22 pesa la mitad en la tabla

- **ARCHIVO:LÍNEA**: `docs\S150_ALERTAS_DEBILES_MAX.md:23-29`; regla de confiabilidad en `docs\S150_IMAGENES_SNPP.md` §3.2.
  **SCRIPT:SALIDA**: `F2/m6_perdidas_confiables.py` y `F2/m6b_camino_por_etiqueta.py` → `m6_salida.txt`.
- **QUÉ PASA.** El documento cuenta como confiables las alertas de la tabla y las del OCR desde el 2026-06-13,
  y saca sólo las 5 filas de Suomi NPP cuya imagen se comprobó que era de otra pasada → 36. Pero el propio S150
  (`S150_IMAGENES_SNPP.md` §3.2) dice que **ninguna** alerta de Suomi NPP que llega sólo por OCR es confiable
  mientras no se compruebe su cabecera, y hay dos más sin comprobar (Lastarria 2026-08-21 05:24 y Planchón
  Peteroa 2026-08-24 06:12, filas 37 y 42 de la tabla del documento). Con esa regla: **34** (30 V375 + 4 V750).
  Y el reparto por camino cambia: con todas las etiquetas, 27 primer pase y 15 D22 (36 %); con la confiable del
  documento, 18 y 14; con la estricta, **17 y 13 (43 %)**; **sólo con la tabla, 12 y 12 (50 %)**. El "14 o 15"
  que circula mezcla dos denominadores (15 de 42 contra 14 de 32). Salvedad heredada y verificada en el código:
  "primer pase" cuenta píxeles de toda la escena (`diag_n_first_pass_pixels`), no el píxel publicado, y la
  compuerta D22 usa el mismo `t_bg` que el record (`pipeline/process_viirs.py:1278-1281` pasa `t_bg=t_bg_i04`,
  persistido como `t_bg_k` en `:2175`; la compuerta en `pipeline/detection_context.py:546`).
- **CÓMO SE VE EN EL DASHBOARD.** Invisible; pesa en el orden de las pruebas.
- **CÓMO REPRODUCIRLO.** `python experiments/_s150_meta_audit/F2/m6_perdidas_confiables.py experiments/_s150_meta_audit/F2/filas_mias.json`
  (`filas_mias.json` es idéntico a `experiments/_s150_debiles/filas.json`, comprobado).
- **CONFIANZA.** CONFIRMADO.
- **GRAVEDAD 2.** El A/B de D22 está suspendido (#773); con etiquetas limpias explica la mitad de lo que `max`
  le quita a la tabla, más de lo que sugería "15 de 42".

### H5. El 95,7 % agregado esconde a Chaitén, y negativos y positivas vienen de volcanes distintos

- **SCRIPT:SALIDA**: `F2/m7_por_volcan.py` → `m7_salida.txt`.
- **QUÉ PASA.** Abril a agosto, V375. Los negativos limpios los ponen sobre todo los volcanes tranquilos
  (Llaima 356, Copahue 339, Villarrica 329, Chaitén 322, Chillán 302), con 2 a 35 positivas cada uno; las
  positivas las ponen Láscar 207, Isluga 189, Cordón Caulle 163 y Lastarria 153, con 38 a 206 negativos. O sea
  que "35,7 a 2,7 %" y "conserva 95,7 %" se miden casi sobre volcanes distintos. Por volcán, F conserva 82,9 %
  en **Chaitén (29 de 35)**, 93,0 % en Tupungatito, 93,8 % en Planchón Peteroa, 98 a 99 % en Láscar e Isluga. En
  negativos, F queda en 9,7 % [6,4, 14,5] en Cordón Caulle y 10,3 % [4,8, 20,8] en Lastarria, al borde de la meta
  de 10 % de la tabla de terminado; Copahue 0 de 339.
- **CÓMO SE VE EN EL DASHBOARD.** Chaitén (domo, señal débil): con `max`, una de cada seis alertas de MIROVA que
  hoy se publicarían sin Test 1 dejaría de verse.
- **CÓMO REPRODUCIRLO.** `python experiments/_s150_meta_audit/F2/m7_por_volcan.py <tmp>/{abril,...,agosto}/tabla.json`.
- **CONFIANZA.** CONFIRMADO (las sumas por volcán dan 2.324/829/63 y 988/946).
- **GRAVEDAD 2.** Regla S126: el veredicto de recall debería mirarse por volcán, no sólo agregado.

### H6. AUDIT_S149: la celda MODIS de su tabla no es de la ventana que la tabla declara

- **ARCHIVO:LÍNEA**: `docs\AUDIT_S149.md:16` ("medido hoy en producción, del 1 al 21 de septiembre") y `:20-21`.
- **QUÉ PASA.** El 11,5 % de MODIS en negativos sale de `experiments\_s149_audit\frente_c\chequeos.txt:9,13`
  (marzo a 08-28 y 08-29 a 09-21, los dos dan 11,5 %, así que no mezcla régimen); la ventana declarada da
  **12,5 % (60 de 479)** (`hoy_0901_0921.txt`, `tabla_hoy.txt`). El 11,7 % de alertas es marzo a septiembre y
  sólo Láscar (ya observado por el verificador de S150, H3). La conclusión "MODIS no discrimina" no cambia.
- **CÓMO SE VE EN EL DASHBOARD.** Invisible.
- **CONFIANZA.** CONFIRMADO (leído en los tres archivos). **GRAVEDAD 1.**

### H7. La fila de agosto sigue diciendo NO ADOPTAR sin marca

- **ARCHIVO:LÍNEA**: `docs\S150_RESULTADO_MESES.md:32`. La corrección (las dos pérdidas fuertes de agosto son
  filas del OCR con imagen de otra pasada) vive en el párrafo de las líneas 34 a 43 y en §3, no en la fila. Mi
  re-ejecución de agosto da "perdidas con 0.5 MW o mas: 2 | FALLA" con la etiqueta completa porque el
  evaluador no excluye esas filas: el veredicto mecánico sigue siendo el viejo. Es A113 (la marca va al inicio
  del pasaje). **CONFIANZA** CONFIRMADO. **GRAVEDAD 1.**

## 3. Mediciones independientes que dieron limpio (no son reproducción del mismo script)

**M3, etiquetador escrito desde cero** (`F2/m3_pareo_y_etiquetas.py`, sin `banco_paridad`): sobre las 6.864
pasadas V375 de abril a agosto coincide con el etiquetador del evaluador en **6.858**; las 6 diferencias son
dos `pos`→`sin_info`, dos `sin_info`→`neg_limpio` y dos al revés. Pregunta 1: si el pareo de ±2 min estuviera
corrido, ampliar la tolerancia movería mucho; a ±10 min sólo pasan 83 `sin_info` a `neg_limpio` y 17 a `pos`
(3,6 % y 1,7 % de esos denominadores). El 64 % de las pasadas tiene fila a ≤ 2 min y el 34 % no tiene ninguna
a menos de 10 min (pasadas que MIROVA no lista, no desfase). Pregunta 2: un instrumento muerto daría 0
coincidencias.

**M2, positivas por canal, fecha y satélite** (`F2/m2_estratos_etiqueta.py`): de las 988 positivas que B publica,
280 llegan sólo por OCR, y **187 de ellas son de Suomi NPP** (19 % del total), la clase que S150 declaró no
confiable; la tabla trae sólo 52 de Suomi NPP. Quitarlas no cambia nada: conservación 95,7 % con todo, 96,6 %
con la tabla, 95,9 % con la etiqueta confiable estricta (708 de 738). La etiqueta "sólo OCR" no esconde un
recall distinto (93,6 % contra 96,6 %).

**M8, posición del cúmulo de F contra B** (`F2/m8_posicion_F_vs_B.py`): de las 946 positivas que los dos brazos
publican, 702 tienen el mismo centroide exacto, 207 a menos de 0,4 km, 32 entre 0,4 y 2 km y **5 a más de 2 km**
(la mayor, Cordón Caulle 2026-07-25 05:54, 10,4 km). `max` no mueve el cúmulo de las alertas. Matiz: de los 63
negativos limpios que F todavía publica, 11 tienen el cúmulo a más de 2 km del de B. Lo que esta medición NO
cubre: el movimiento del cúmulo al apagar el Test 1 (el motivo del NO ADOPTAR de S147), porque B y F están los
dos sin Test 1; los meses de S150 no tienen ningún criterio de posición contra producción.

**M10, negativos por satélite** (`F2/m10_por_satelite.py`): `max` apaga parejo en los tres satélites dentro de
los negativos limpios (F/B 0,08 N20, 0,09 N21, 0,04 SNPP) y conserva parejo las positivas (0,97, 0,96, 0,94).

**Ventanas y calidad de la referencia.** Todas las ventanas de S150 caen antes de #535 (agosto termina el 27) y
la de S148 después (01 a 20 de septiembre); dentro de cada A/B los dos brazos corren el mismo código, así que
#535 no mezcla regímenes en ninguna comparación B contra F. Abril, mayo y junio deciden con la tabla sola
(A119), julio y agosto con tabla y OCR; el aviso de `calidad_referencia_mirova` se imprime en cada corrida.
Lo que sí cruza fechas de calidad es la tabla por tramo de magnitud (H3), que usa la etiqueta completa en abril
a junio; con la confiable el resultado casi no cambia.

## 4. Cómo reproducir todo

Desde `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile`, con `T` una carpeta temporal fuera
del repo:

```
python experiments/_s150_meta_audit/F2/ev_sin_fetch.py --nombre abril --desde 2026-04-01 --hasta 2026-04-30 --control _s146_ab_sin_test1 --brazo _s147_ab_sin_test1_max --runs 35639417826 37823348991 --tmp $T
python experiments/_s150_meta_audit/F2/ev_sin_fetch.py --nombre mayo --desde 2026-05-01 --hasta 2026-05-31 --control _s146_ab_sin_test1 --brazo _s147_ab_sin_test1_max --runs 35599902448 --gemelo _s149_ab_sin_test1_gemelo --runs-gemelo 35599941522 --tmp $T
#   junio 35675490175 (gemelo 35679063864), julio 35728617326 (35728872410), agosto 2026-08-01 a 08-27 35759688167 (35766187578)
python experiments/_s149_prereg_invierno/agregado.py $T/{abril,mayo,junio,julio,agosto}/tabla.json
python experiments/_s150_meta_audit/F2/m<N>_*.py $T/{abril,mayo,junio,julio,agosto}/tabla.json
```

Septiembre: `armar_tabla.py --control experiments/_s147_lectura/experiments/_s146_ab_sin_test1/salidas/prelim_s148/_s146_ab_sin_test1 --brazo .../_s147_ab_sin_test1_max --cons experiments/_s146_ab_sin_test1/_congelado/registro_vrp_consolidado.csv --ocr .../registro_vrp_ocr.csv --desde 2026-09-01 --hasta 2026-09-20`.

## 5. VERIFICADO LIMPIO (no hace falta volver a mirarlo)

| qué | comando que lo confirma | resultado |
|---|---|---|
| Los cinco meses de `max` (P1, P2, P4, P5, C8b, cobertura, determinismo) | `ev_sin_fetch.py` por mes y `diff` contra `experiments/_s149_prereg_invierno/resultados/<mes>_VIIRS375.txt` | idéntico salvo encabezados; mayo marca FALLA de determinismo por cobertura del gemelo (282 de 292), ya documentado (H5 del verificador S150) |
| Agregado abril a agosto | `agregado.py` + `diff` | IDENTICO |
| Septiembre, por un camino distinto del evaluador original | `armar_tabla.py` + `agregado.py` | 111/373 a 10/373; 137/143 a 135 |
| Recall por tramo | `recall_por_magnitud.py` + `diff` | igual |
| MODIS Láscar B/J/K | `modis_lascar_brazos.py` + `diff` | IDENTICO |
| Costo oculto 50 / 34 / 16 / 14 SNPP | c1, c2, c4 + `diff`; `m5_sin_fila_por_satelite.py` | idéntico; 14 SNPP de 16 |
| 46 pérdidas, μ y σ iguales entre brazos | `perdidas_max.py`; comparación de JSON | `filas_mias.json == filas.json`; 0 de 1.143 distintos |
| Residual 57,3 % (43/75, Wilson [46,1, 67,9]) contra 9,1 % (3/33, [3,1, 23,6]) | `estructura_del_residual.py --datos <run 35521542153>` | idéntico; intervalos separados, pero la celda del 9 % tiene 3 eventos |
| El job de Chaitén de abril corrió el mismo código | `git diff --stat d46b7ec59 327621e2c -- pipeline/` | sólo 4 perfiles nuevos |
| El etiquetador del evaluador | `m3_pareo_y_etiquetas.py` (independiente) | 6.858 de 6.864 iguales; robusto a la tolerancia |
| `max` no mueve el cúmulo de las alertas | `m8_posicion_F_vs_B.py` | 5 de 946 a más de 2 km |
| Producción hoy: vent_anchored sí, `max` no | `VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p; ..."` | True / False |
| D22 usa el mismo `t_bg` que se persiste | lectura `pipeline/process_viirs.py:1278-1281,2175`, `pipeline/detection_context.py:546` | sí |

**No cubrí**: la sonda de tres campos y la carpeta `meta/` (fuera de alcance); las AUC de σ de S150 débiles
(con entrada idéntica la salida es idéntica, no lo cuento como verificación); que el job de GitHub haya
aplicado los flags declarados (los logs no los imprimen, sigue SIN VERIFICAR); si las 121 publicaciones de H2
o las 858 lejanas son calor real (pide imagen o gránulo).
