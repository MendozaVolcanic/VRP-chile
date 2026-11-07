# F5 S175: identidad del pareo con MIROVA (los tres sensores)

## 1. Encabezado

- Hora del servidor al cerrar: `Date: Sat, 07 Nov 2026 04:32:07 GMT` (cabecera de github.com). Inicio: `04:10:45 GMT` (`C:\Users\nmend\vrp-temporales\s175_audit\insumos\hora_servidor.txt`).
- Commit medido: base `752d348bc67190e53b610989877e2405d238a1bc` (git archive de `data/` y la instantánea de código de la ola 0). Línea base roja (1): datos y referencia de `79f41069727af508397229dca26bbd33418b9e85` (el commit que escribió `latest.json` del 2026-11-02 19:29 UTC) con el código de la base.
- Referencia: copias LF de la ola 0, verificadas por sha256 antes de medir (`f833bfde...` snapshot consolidado, `577a336e...` OCR, `dee76837...` tabla raíz). El git archive del worktree las entrega en CRLF con otro sha256; no se usaron (lección S163).
- Modelo: Opus 5.5 (sesión de Claude Code). Esfuerzo: pedido high; la etiqueta literal de mi contexto dice `reasoning_effort 15`. Corrí en bajo, igual que la sonda de la ola 0.
- CARPETA: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\f5\`. Temporal: `C:\Users\nmend\vrp-temporales\s175_audit\f5\` (629 MB: dos copias privadas de la base, 8 TIF, 4 archivos de Pages).
- Instrumento: los módulos de la base sin modificar (`auto_audit_weekly`, `banco_paridad` con el predicado del tablero en node, `referencia_mirova_unificada`, `clase_mirova`), importados desde una copia privada de la base en `C:\Users\nmend\vrp-temporales\s175_audit\f5\root\`. Scripts y salidas en CARPETA: `f5_base.py`, `f5_medir.py` (salida `f5_medir_out.json`, `i2_pares.csv`), `i2_fuertes.py`, `i2_extension.py`, `i2_tif.py`, `i7_dist_tabla_ocr.py`, `i6_control.py`, `linea_base_1102.py`, `i3_vistas_y_pages.sh`, cada uno con su `.out.txt` o `_out.json`.
- Llamadas a la API de GitHub: 0. Bajadas por raw.githubusercontent.com (8 TIF de `MendozaVolcanic/mirova-tif-archive`) y por GitHub Pages (4 archivos). Ningún pull.
- Qué NO miré, para que mi silencio no se lea como «todo bien»: los detectores (F1, F2, sombra de #945); el PNG Latest10NTI como vara de posición después del 2026-09-22 (no lo georreferencié); los TIF fuera de una muestra de 8; la azimut de los aciertos en general (sólo radio, salvo los 4 TIF con georreferencia válida); `metrica_far_ref` corrida con origen común (sólo leí la línea); la tabla de paridad `comparacion.html` (PREVIEW) más allá de su línea 247; las ventanas anteriores al 2026-06-11.

## 2. En una pantalla

1. Con la distancia de la tabla y un origen común, los aciertos que el banco cuenta por misma pasada son el mismo foco o el mismo cúmulo: de 881 publicados (2026-06-11 a 2026-11-07, base), sólo 1 cae fuera de nuestra extensión de píxeles con distancia de la tabla (Chillán VIIRS 375 2026-10-18 06:48, por 0,1 km). Los otros 25 «fuera» se apoyan en la distancia del OCR, y esa distancia difiere de la tabla en la misma pasada por más de 1 km en 40 de 58 pasadas de Cordón Caulle VIIRS 375 (−4,4 km) (hallazgos 301 y 302).
2. Comparar `final_hotspot_dist_km` con la `Distancia_km` de MIROVA a secas mezcla dos orígenes (vent contra centro de MIROVA): marca 432 de 881 aciertos como otro foco cuando son 83 (desfases constantes de 7,6 km en Cordón Caulle y 5 km en Tupungatito). El banco lo hace en `frac_radio_a_2km` (hallazgo 303).
3. El recall por noche del audit cuenta un acierto de otra pasada en otro lugar: en Cordón Caulle VIIRS 750 el 2026-10-10 la noche sale vista por una pasada de las 04:54 a 18,5 km del centro, mientras la protegida de las 05:54 (7,83 km) está en `PERDIDAS_ACEPTADAS`. Con misma pasada el recall baja de 97,0 a 95,0 % en VIIRS 375 (200 noches) y de 79,2 a 77,4 % en VIIRS 750 (53); MODIS no cambia (16 de 22) (hallazgo 304).
4. El tiempo no pierde pares: los 970 pares tienen |Δt| < 30 s, y ninguna alerta nocturna queda sin par con un record a 2 a 10 min (control positivo visto). Port contra node coinciden en las 275 noches de la ventana del audit. La línea base roja (1) se reproduce exacta: 125/194, 32/42, 14/16.
5. El criterio «ninguna protegida perdida» no tiene casos en 5 de 11 volcanes (0 protegidas nocturnas) y Chillán tiene 136 de 152. Hay 42 protegidas diurnas fuera del criterio, 36 de Chillán, y las 36 tienen una protegida nocturna a menos de 12 h. Los 9 OCR escritos 1,0 MW con nota de truncado, entre ellos Chillán MODIS 2026-10-30 07:15, son protegidas sólo si se lee el truncado hacia abajo (hallazgos 307 a 309).

## 3. Hallazgos (de peor a menos grave)

### 301
- TÍTULO: La distancia del OCR no sirve de vara de posición; casi todos los aciertos «de otra fuente» se apoyan en ella
- ARCHIVO:LÍNEA: `scripts/referencia_mirova_unificada.py:134` (la distancia del OCR sale de la nota con `parse_ocr_distance`); SCRIPT:SALIDA `i7_dist_tabla_ocr.py` → `i7_dist_tabla_ocr_out.json`; `i2_extension.py` → `i2_extension_out.json`
- QUÉ PASA: en una misma pasada, MIROVA da una distancia en su tabla y el OCR lee otra de la imagen. Si las dos son del mismo píxel, tienen que coincidir. No coinciden: OCR menos tabla con |Δ| > 1 km en Cordón Caulle VIIRS 375 en 40 de 58 pasadas antes de Mirova-v1#20 (mediana de los desacuerdos alrededor de −4,4 km) y 2 de 8 desde entonces; Tupungatito VIIRS 375 14 de 26 antes (−2,7 a −3,5 km) y 2 de 6 después; Láscar MODIS 27 de 32 (+1,86 km); Láscar VIIRS 750 25 de 29 (+1,72 km); Chillán VIIRS 375 3 de 11 después. Ventana: todas las alertas OCR con fila de la tabla a ±120 s en el snapshot de la base (2026-01-20 a 2026-11-06). Consecuencia en I2: de 26 aciertos pareados cuyo radio de MIROVA cae fuera de nuestra extensión de píxeles, 25 usan la distancia del OCR (Tupungatito 8, Cordón Caulle 7 entre VIIRS 375 y 750, Planchón 5, Lastarria 3, Láscar 1, Isluga 1). La clase (iii) que esos casos sugieren es del instrumento, no de la física.
- CÓMO SE VE EN EL DASHBOARD: invisible. Es la vara del audit (A119, `referencia_sospechosa`) y del banco (`dist_km` de las filas OCR).
- CÓMO REPRODUCIRLO: `cd /d C:\Users\nmend\vrp-temporales\s175_audit\f5 && python "<CARPETA>\i7_dist_tabla_ocr.py"`. Caso: Cordón Caulle VIIRS_SNPP 2026-06-15 06:24 UTC (OCR 4,19 km, nuestro punto a 7,33 km del centro de MIROVA, tabla de las pasadas vecinas alrededor de 7,6 km).
- CONFIANZA: CONFIRMADO (desacuerdo medido). Que el OCR también clasifique mal ALERTA contra FALSO_POSITIVO por esa distancia es SOSPECHA (la nota usa la distancia contra el límite: «límite 5.0 km» en Láscar y Chillán).
- GRAVEDAD: 3. El audit usa la distancia del OCR cuando la tabla no la tiene; en Tupungatito (inner 7 km) un error de 3 km puede cambiar una alerta OCR de dentro a fuera del círculo.

### 302
- TÍTULO: Con la distancia de la tabla, los aciertos por misma pasada son el mismo foco o el mismo cúmulo; una protegida queda al borde
- ARCHIVO:LÍNEA: SCRIPT:SALIDA `f5_medir.py` (I2) → `i2_pares.csv`, `f5_medir_out.json` clave `I2`; `i2_fuertes.py` → `i2_fuertes_out.json`; `i2_extension.py` → `i2_extension_out.json`; `i2_tif.py` → `i2_tif_out.json`
- QUÉ PASA: la pregunta es si el calor que publicamos en la pasada en que MIROVA alertó es el mismo calor. Universo: los 881 records del banco con etiqueta `pos` (D-9 SN) y publicados por el predicado del tablero, 2026-06-11 a 2026-11-07, base. Con nuestro punto medido desde el centro de MIROVA: 793 compatibles por radio (i?), 83 con radio distinto en más de la tolerancia (iii por radio) y 5 sin distancia de MIROVA (iv). De los 83, 57 tienen el radio de MIROVA dentro del rango de radios de nuestros propios píxeles anómalos más la tolerancia (mismo cúmulo, otro píxel: Lastarria 27, Chillán 22, Láscar 4, Isluga 3, Cordón Caulle 1) y 26 fuera (25 con distancia del OCR, ver 301). La única protegida fuera con distancia de la tabla es Chillán VIIRS_NOAA21 2026-10-18 06:48 (25,79 MW; MIROVA 1,88 km, nuestros píxeles de 0,19 a 1,03 km más 0,75 de tolerancia). Protegidas con acierto dudoso por distancia del OCR: Cordón Caulle VIIRS_SNPP_750 2026-07-03 05:48 (1,0 MW, truncado, OCR 4,59 contra nuestros 7,87 km) y Tupungatito VIIRS_SNPP 2026-09-14 06:18 (2,22 MW, OCR antes de V31, la que el audit ya marca `referencia_sospechosa`). Por TIF (muestra de 8, 4 con georreferencia que reproduce la distancia de la tabla): Láscar VIIRS 750 2026-06-21 05:30 y Lastarria 2026-08-09 05:48 son el mismo píxel (0,35 y 0,69 km); Lastarria 2026-06-12 05:54 (0,83 km), Lastarria 2026-07-14 05:54 (1,28 km) e Isluga 2026-09-22 05:42 (2,01 km) son píxeles distintos, todos con VRP de MIROVA de 0,2 a 0,4 MW.
- CÓMO SE VE EN EL DASHBOARD: el operador ve la alerta publicada en el cráter; en Lastarria e Isluga el píxel de MIROVA puede estar a 1 a 2 km del nuestro.
- CÓMO REPRODUCIRLO: `python "<CARPETA>\f5_base.py"`, `python "<CARPETA>\f5_medir.py"`, `python "<CARPETA>\i2_fuertes.py"`, `python "<CARPETA>\i2_extension.py"`, `python "<CARPETA>\i2_tif.py" C:\Users\nmend\vrp-temporales\s175_audit\f5\tif_descargas`. Casos: Chillán VIIRS_NOAA21 2026-10-18 06:48, Isluga VIIRS_NOAA20 2026-09-22 05:42.
- CONFIANZA: CONFIRMADO para los conteos y los 4 TIF válidos. El paso «máximo del TIF dentro del inner = píxel alertado» sólo está validado por la distancia (azimut sin control): SOSPECHA fuera de esos 4.
- GRAVEDAD: 2. No hay protegida cuyo acierto sea claramente otra fuente con la vara de la tabla.

### 303
- TÍTULO: Comparar nuestro radio con el de MIROVA mezcla dos orígenes (vent contra centro de MIROVA)
- ARCHIVO:LÍNEA: `scripts/banco_paridad.py:450` (`abs(r["pc_dist"] - r["dist_ref"]) <= 2`); origen nuestro en `pipeline/geo_utils.py:53` (`get_detection_anchor`, el vent gana); `frontend/comparacion.html:247` (histograma de `mirDist` contra el nuestro); SCRIPT:SALIDA `f5_medir.py`, `i2_pares.csv` columnas `clase_radio_crudo` y `clase`
- QUÉ PASA: MIROVA mide la distancia desde el centro de su grilla y nosotros desde el cráter (vent). En Cordón Caulle los dos puntos están a 7,58 km, en Tupungatito a unos 5 km y en Planchón a unos 2 km. Comparar radios crudos da desfases casi constantes por volcán (nuestro menos MIROVA, mediana y p10 a p90: Cordón Caulle VIIRS 375 −7,81 [−8,08, −7,26] km, n 91; Tupungatito −4,95 [−5,11, −4,61], n 52; Planchón −1,60, n 40; Láscar −1,08, n 94) y clasifica 432 de 881 aciertos como otro foco; con origen común son 83. `get_detection_anchor` es deliberado (S98); el defecto está en los instrumentos que restan los dos radios.
- CÓMO SE VE EN EL DASHBOARD: en `comparacion.html` (PREVIEW) las distribuciones de distancia salen corridas por volcán. En el banco, `far_ref.frac_radio_a_2km` sale sesgada en Cordón Caulle y Tupungatito.
- CÓMO REPRODUCIRLO: `python "<CARPETA>\f5_medir.py"`; comparar `clase_radio_crudo_final_hotspot_dist_km` con `clase_con_origen_comun_mirova_center` en `f5_medir_out.json`. Caso: Cordón Caulle VIIRS_SNPP_750 2026-07-06 05:54 (tabla 7,83 km, nuestro `final_hotspot_dist_km` 0,31 km, nuestro punto a 7,52 km del centro de MIROVA).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2. Métrica diagnóstica, no decide flags; pero engaña a quien investigue posición (A93, A107).

### 304
- TÍTULO: El recall por noche cuenta como acierto una pasada distinta en otro lugar; con misma pasada baja 2 puntos en VIIRS
- ARCHIVO:LÍNEA: `scripts/auto_audit_weekly.py:377` (`recall_por_sensor` cuenta la noche con cualquier record `dash`), `scripts/auto_audit_weekly.py:1016` (`PERDIDAS_ACEPTADAS`); SCRIPT:SALIDA `f5_medir.py` → `f5_medir_out.json` clave `I1`
- QUÉ PASA: el recall pregunta si esa noche vimos algo dentro del círculo, no si vimos lo que MIROVA vio. Ventana del audit (2026-09-03 a 2026-11-02), base, noches de K y de la vía: VIIRS 375 194 de 200 noches por noche y 190 de 200 con acierto en la misma pasada (por pasada 327 de 341); VIIRS 750 42 de 53 y 41 de 53 (por pasada 75 de 92); MODIS 16 de 22 y 16 de 22 (por pasada 24 de 32). Los 5 aciertos sin misma pasada vienen de otro satélite 24 a 66 min antes o después. Tres son compatibles por radio con origen común (Láscar 2026-10-28, Lastarria 2026-09-21 y Tupungatito 2026-09-29, estas dos con distancia del OCR). Lastarria 2026-09-04 difiere 1,1 a 1,2 km, el mismo patrón de las 27 de Lastarria del hallazgo 302. El quinto es otra fuente: Cordón Caulle VIIRS 750 2026-10-10, nuestra pasada VIIRS_SNPP_750 04:54 con cúmulo a 13,76 km del vent (18,5 km del centro de MIROVA), mientras MIROVA alertó a las 05:54:02 a 7,83 km (1,19 MW, protegida). Esa misma pasada está en `PERDIDAS_ACEPTADAS` como FN de VIIRS 750, así que el audit la da por perdida en la lista de protegidas y por vista en el recall.
- CÓMO SE VE EN EL DASHBOARD: el operador vio la pasada de las 04:54 en otro lugar del círculo de 20 km; la recuperación de esa noche vino por VIIRS 375 en la misma pasada (según el comentario de `PERDIDAS_ACEPTADAS`). Invisible en el recall publicado.
- CÓMO REPRODUCIRLO: `python "<CARPETA>\f5_medir.py"`, clave `I1.aciertos_noche_sin_misma_pasada`. Cordón Caulle VIIRS_SNPP_750 2026-10-10 04:54 y 05:54 UTC.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 3. Cambia el recall publicado en 1,9 a 2,0 puntos en VIIRS; no cambia el veredicto de esta ventana (VIIRS 750 ya está bajo 79,5; VIIRS 375 sigue sobre 93,4).

### 305
- TÍTULO: La tabla de MIROVA no lista la mayoría de las pasadas de Suomi NPP; el denominador de negativos limpios se mueve por satélite y mes
- ARCHIVO:LÍNEA: `scripts/banco_paridad.py` (`etiquetar`, negativo limpio exige fila RUTINA de la tabla a ±120 s); SCRIPT:SALIDA `f5_medir.py` → `f5_medir_out.json` clave `I7.pasadas_nuestras_sin_fila_mirova`
- QUÉ PASA: para que una pasada nuestra cuente como negativo limpio, MIROVA tiene que listar ese gránulo con VRP 0. Pasadas nocturnas nuestras de los 11 Tier A sin ninguna fila de MIROVA a ±120 s: VIIRS_SNPP 197/317 (junio), 307/390 (julio), 280/448 (agosto), 284/493 (septiembre), 258/462 (octubre); VIIRS_SNPP_750 253/315, 326/385, 280/442, 254/489, 284/456. NOAA-21 también tuvo huecos grandes en junio y julio (I-band 90/317 y 118/483; M-band 56/315 y 154/483) y bajó a 30 a 65 por mes después. NOAA-20 y MODIS rondan 3 a 18 %. Noviembre sale alto en todos por la copia vieja de la referencia (hallazgo 306), no por MIROVA. El control con una semana de VIIRS 375 borrada a propósito da 293/293 sin fila contra 2.004/6.507 en el resto: el instrumento ve el hueco.
- CÓMO SE VE EN EL DASHBOARD: invisible. La tasa de falsas publicaciones se calcula casi sin Suomi NPP.
- CÓMO REPRODUCIRLO: `python "<CARPETA>\f5_medir.py"`, claves `I7.pasadas_nuestras_sin_fila_mirova` y `control_I7_hueco`.
- CONFIANZA: CONFIRMADO el conteo. Por qué falta Suomi NPP (MIROVA no lo procesa, o latest.php lo rota antes de que el scraper lo lea): SOSPECHA.
- GRAVEDAD: 2.

### 306
- TÍTULO: El snapshot del consolidado se refresca cada semana y el del OCR cada hora: entre audits el banco con `--snapshot` ve alertas OCR sin las filas RUTINA de esas noches
- ARCHIVO:LÍNEA: `.github/workflows/audit-weekly.yml:55` a `:58` (único que baja el consolidado al snapshot), `.github/workflows/sync-mirova-csv.yml:108` a `:109` (sube la tabla raíz y el OCR del snapshot cada hora); SCRIPT:SALIDA `f5_medir.py` clave `I7`
- QUÉ PASA: en la base, el snapshot del consolidado llega al 2026-11-02 12:20 y el OCR al 2026-11-06 13:15. La tabla raíz tiene 655 filas que el snapshot no (2026-11-02 a 2026-11-06), 57 de ellas alertas; las 6 alertas del 2026-11-02 que faltan son de 17:42 a 21:05 UTC (diurnas, no cambian el audit de ese día). El audit no se ve afectado porque baja los dos CSV al correr. Sí se afecta toda corrida del banco con `--snapshot` y todo instrumento que lea el snapshot entre audits: en esas noches hay alertas del OCR y ningún negativo.
- CÓMO SE VE EN EL DASHBOARD: invisible (el tablero lee `latest_consolidado.csv`, horario).
- CÓMO REPRODUCIRLO: `python "<CARPETA>\f5_medir.py"`, clave `I7.tabla_no_en_snapshot`.
- CONFIANZA: CONFIRMADO el desfase; que alguna corrida rutinaria use `--snapshot` entre audits es SOSPECHA (las vigilancias bajan la referencia viva).
- GRAVEDAD: 2.

### 307
- TÍTULO: Nueve alertas OCR escritas 1,0 MW con nota de truncado deciden la lista de protegidas según cómo se lea el truncado
- ARCHIVO:LÍNEA: `scripts/clase_mirova.py:46` (`UMBRAL_PROTEGIDA_MW = 1.0`) y `:65` (`alerta_protegida`); SCRIPT:SALIDA `f5_medir.py` clave `I8`, comando de la sección I8 abajo
- QUÉ PASA: MIROVA dibuja el VRP truncado en la imagen y el OCR lee el entero. En el snapshot OCR de la base, 63 filas traen «truncado» en la nota (43 con «real ∈ [a, b)» y 20 con «real entre a y b»). Las enteras de 2 MW o menos son 2 MODIS y 7 VIIRS (bucket VIIRS 750) en 1,0 y 5 VIIRS en 2,0. Con la lectura de la propia nota (real en [1, 2)) las 9 en 1,0 son protegidas, como hoy; con el «(±1)» de la nota pueden no serlo. No hay alertas OCR truncadas en 0,x (los valores truncados son enteros), así que redondear hacia arriba no crea protegidas nuevas. El caso de partida, Chillán MODIS 2026-10-30 07:15, es una de las 9: sólo OCR, sin ninguna fila de la tabla de Chillán MODIS a menos de 60 min, nota «VRP truncado por MIROVA en MODIS: real ∈ [1, 2) MW (±1)». La línea base roja (5) se reencuentra: Chillán MODIS 2026-11-06 13:15, 9,0 MW, «real ∈ [9, 10)».
- CÓMO SE VE EN EL DASHBOARD: invisible; aparece como «alerta protegida sin publicar» en el issue del audit.
- CÓMO REPRODUCIRLO: `python "<CARPETA>\f5_medir.py"`, claves `I8.control_5_chillan_20261106_1315` y `I8.caso_chillan_20261030_0715`.
- CONFIANZA: CONFIRMADO el conteo. El valor real de esas 9: SIN DATO.
- GRAVEDAD: 2. Una protegida perdida de Chillán MODIS descansa en una sola fila OCR truncada en el umbral.

### 308
- TÍTULO: El criterio «ninguna protegida perdida» no tiene casos en 5 de los 11 volcanes
- ARCHIVO:LÍNEA: SCRIPT:SALIDA `f5_medir.py` clave `I10`
- QUÉ PASA: protegidas nocturnas de MIROVA (referencia unificada, filtro diurno real del pipeline), 2026-09-01 a 2026-11-07: Chillán 136, Cordón Caulle 8, Isluga 3, Tupungatito 3, Láscar 1, Villarrica 1; Lastarria, Llaima, Chaitén, Copahue y Planchón 0. Total 152 nocturnas de 194 (el orquestador contó 201 por hora UTC sobre la tabla; la diferencia es la vara: filtro real y referencia unificada). En los volcanes sin casos sólo la sobre-publicación en negativos limpios tiene poder; las tasas de F2 y F5 se leen con este n al lado.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python "<CARPETA>\f5_medir.py"`, clave `I10`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2 (de método, lección S146).

### 309
- TÍTULO: 42 protegidas diurnas quedan fuera del criterio por diseño; las 36 de Chillán tienen protegida nocturna a menos de 12 h
- ARCHIVO:LÍNEA: `scripts/auto_audit_weekly.py:296` (`es_pasada_diurna_descartada`); SCRIPT:SALIDA `f5_medir.py` clave `I9`
- QUÉ PASA: de día el Sol reflejado en nube o nieve imita calor (A76), así que el pipeline no mira esas pasadas y el audit no las cuenta. Con el filtro real: 42 de 194 protegidas son diurnas (Chillán MODIS 7, VIIRS 375 17, VIIRS 750 12; Chaitén 1, Isluga 2, Láscar 2, Villarrica 1), de 12 a 13 y 20 a 21 UTC en MODIS y de 17 a 19 UTC en VIIRS. Las 36 de Chillán tienen una protegida nocturna del mismo volcán a menos de 12 h: no eran reflexión. Las otras 6 tienen una alerta nocturna cercana, pero ninguna protegida. Control (8): Chillán a las 17 UTC sale diurna y a las 07 UTC nocturna en los tres sensores.
- CÓMO SE VE EN EL DASHBOARD: el operador no ve nuestra señal de día; la erupción de Chillán sí la ve en las pasadas nocturnas vecinas.
- CÓMO REPRODUCIRLO: `python "<CARPETA>\f5_medir.py"`, claves `I9.lista_diurnas` y `I9.control_8`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2.

### 310
- TÍTULO: El ratio de magnitud de Lastarria VIIRS 375 cambia de banda al restringirlo a la misma pasada
- ARCHIVO:LÍNEA: `scripts/auto_audit_weekly.py` (`evaluar_detector`, razón `max(o["pub"]) / mvrp` de la noche), `:145` (`UNDER_BAND_KNOWN`); SCRIPT:SALIDA `f5_medir.py` clave `I4`
- QUÉ PASA: el audit divide nuestro máximo de la noche por el máximo de MIROVA de la noche, que pueden ser pasadas distintas. Restringido a la misma pasada (mediana por noche de nuestro publicado sobre el VRP de esa fila de MIROVA), ventana del audit: Lastarria VIIRS 375 0,664 (n 15, bajo) pasa a 0,712 (n 13, en banda [0,7, 1,4]); Chillán VIIRS 750 0,683 a 0,526 (n 22, sigue bajo); Láscar VIIRS 375 0,560 a 0,491. Ningún flag cambia: Lastarria, Láscar e Isluga están en `UNDER_BAND_KNOWN` y Chillán ya estaba bajo. No toqué D32: la razón de misma pasada sigue comparando nuestro cúmulo principal con la suma de píxeles de MIROVA.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python "<CARPETA>\f5_medir.py"`, clave `I4.por_vol_sensor`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

### 311
- TÍTULO: Las tres copias de `mirovaEqVrp` difieren y el guard de tres vistas sólo compara `isValidDetection`
- ARCHIVO:LÍNEA: `frontend/index.html:1162`, `frontend/mosaico.html:255`, `frontend/diario.html:255`; `tests/test_guard_predicado_tres_vistas_s147.py` (extrae sólo `function isValidDetection`); SCRIPT:SALIDA `i3_vistas_y_pages.sh` → `i3_vistas_y_pages.out.txt`
- QUÉ PASA: `index` y `mosaico` devuelven `vrp_mw` (con tope de 50.000) para un record sin `primary_cluster` antes de mirar `distance_class`. `diario` mira `distance_class` primero y no pone tope. Además, `index` y `mosaico` usan `innerKm = 10` si no se pasa y `diario` usa su tabla con defecto 5. Hoy está dormido: los 60.326 records sin `primary_cluster` de los 11 Tier A tienen VRP 0 (base), todas las llamadas pasan `innerKm`, y la tabla `INNER_RADIUS_KM` de `diario` coincide con `volcanoes.yaml` en los 11. Ningún test cubre un record sin `primary_cluster` con VRP > 0 y `far`, ni un `innerKm` omitido, ni los 290 records de Cordón Caulle con cúmulo summit entre 10 y 20 km (que el defecto de 10 dejaría fuera).
- CÓMO SE VE EN EL DASHBOARD: hoy nada; si vuelve un record viejo sin `primary_cluster` con VRP, el mapa lo publica y la tendencia de 90 días no.
- CÓMO REPRODUCIRLO: `bash "<CARPETA>/i3_vistas_y_pages.sh"`.
- CONFIANZA: CONFIRMADO (leído y contado).
- GRAVEDAD: 1.

### 312
- TÍTULO: `n_misma_pasada` del audit no es «noches con acierto en la misma pasada»
- ARCHIVO:LÍNEA: `scripts/auto_audit_weekly.py:821` a `:831` (`_misma_pasada`), usado en `estratificar_magnitud`
- QUÉ PASA: el conteo compara la hora de NUESTRA pasada de mayor VRP con la de la alerta de MAYOR VRP de MIROVA esa noche. Da 125/194 (VIIRS 375), y la base roja del plan lo leyó como noches con misma pasada; las noches con algún acierto en la misma pasada son 190/194 (hallazgo 304). El docstring de `estratificar_magnitud` lo dice bien; el riesgo es de lectura.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python "<CARPETA>\linea_base_1102.py" C:\Users\nmend\vrp-temporales\s175_audit\f5\root_1102` y `f5_medir.py` clave `I1`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

## 4. Línea base roja

| # | Qué | Resultado | Salida |
|---|---|---|---|
| 1 | Noches con misma pasada en `latest.json` del 2026-11-02 | Exacto con datos de `79f41069`: VIIRS 375 125/194, VIIRS 750 32/42, MODIS 14/16; recall 97,0/79,2/72,7 igual al publicado. Con la base salen 124/194, 31/42 y 14/15 + 1/1 de la vía (4 días más de records). Ojo: no mide «misma pasada» sino máximo contra máximo (hallazgo 312) | `linea_base_1102.out.txt`, `f5_medir_out.json` `I1.n_misma_pasada_estratificar_magnitud` |
| 2 | Aciertos sintéticos (i), (iii), (iv) | `clasificar`: mismo píxel → i?, movido 15 km → iii, sin distancia → iv | `f5_medir_out.json` `control_I2` |
| 3 | Par desfasado 3 min | Aparece en I6 (−178 s, Chillán VIIRS_NOAA21 2026-06-16) | `i6_control.out.txt` |
| 4 | Port contra node que difieren a propósito | `distance_class` None con `vrp_vent_mw` 0: port 1, node 0; `far`: 0 y 0; summit: 1 y 1 | `f5_medir_out.json` `control_I3` |
| 5 | Fila truncada Chillán MODIS 2026-11-06 13:15 | Encontrada, 9,0 MW, [9, 10) | `f5_medir_out.json` `I8.control_5_...` |
| 6 | Semana de un satélite borrada | VIIRS 375 2026-10-12 a 18: 293/293 sin fila (resto 2.004/6.507) | `control_I7_hueco` |
| 7 | OCR cubre 255 de 970 alertas de la tabla desde el 2026-06-11 | Reencontrado: MODIS 12/58, VIIRS 750 20/195, VIIRS 375 223/717 | `I7.cobertura_ocr_...` |
| 8 | Protegida de Chillán diurna a 17 UTC y nocturna a 07 UTC | Sí en los tres sensores | `I9.control_8` |

Además, control de mi propio port: las 382 noches `dash` que recalculo son idénticas a las del audit (`control_port`). Un primer recorte mío dejaba fuera las noches MODIS de K (filtraba por el detector vigente); lo corregí antes de los números de I1, I3 e I4.

## 5. SEGUIMIENTOS (fuera de mi eje)

- Clasificación ALERTA contra FALSO_POSITIVO del OCR de Mirova-v1 con una distancia que difiere de la tabla en 2 a 4 km en Tupungatito y Cordón Caulle (hallazgo 301): si el OCR decide con esa distancia contra el límite, puede rotular mal. Repo Mirova-v1, fuera de este repo. SOSPECHA.
- `frontend/comparacion.html:247`: el histograma de distancias de MIROVA contra el nuestro mezcla orígenes (hallazgo 303). Es PREVIEW. CONFIRMADO por lectura de la línea; no medí el efecto.
- La máscara de dentro o fuera del círculo: el inner de MIROVA se mide desde su centro y el nuestro desde el vent. En Cordón Caulle el círculo de 20 km queda corrido 7,6 km; en Tupungatito el de 7 km, unos 5 km. Es D17 y la decisión S98 (`docs/MIROVA_DIVERGENCES.md:1200` a `:1202` lo tabula); cuánto cambia la clase summit contra far no lo medí. SOSPECHA de efecto.

## 6. VERIFICADO LIMPIO

- I6 tiempo, vara `clase_mirova.VENTANA_S` = 120 s: los 970 pares nocturnos de la base (VIIRS 375 752, VIIRS 750 172, MODIS 46, 2026-06-11 a 2026-11-07) tienen MIROVA menos nuestra entre 0 y 30 s. Nuestra hora va al minuto y la de MIROVA cae en los 30 s siguientes en todos los pares. Ninguna alerta nocturna queda sin par a ±120 s y con un record a 2 a 10 min. El control (3) muestra que el instrumento lo vería. `python "<CARPETA>\i6_control.py"`.
- I3 port contra node, vara: predicado del tablero ejecutado con node (`banco_paridad.correr_node`) sobre `frontend/index.html` de la base. En las 275 noches con alerta de MIROVA de la ventana del audit (base) coinciden en todas: VIIRS 375 194 y 6, VIIRS 750 42 y 11, MODIS 16 y 6 (publica y no publica). El recall con node es igual al del port. Control (4) visto.
- GitHub Pages sirve lo mismo que la base: sha256 normalizado a LF idéntico para `index.html`, `diario.html`, `mosaico.html` y `cambio_detector.js` (bajados el 2026-11-07 04:32 UTC). `bash "<CARPETA>/i3_vistas_y_pages.sh"`.
- `INNER_RADIUS_KM` de `diario.html:243` igual a `volcanoes.yaml` en los 11; `inner_desde_html()` igual a `auto_audit_weekly.INNER` en los 11 (`f5_base.out.txt`).
- La copia congelada `data/mirova_reference/registro_vrp_ocr.csv` no la lee ningún instrumento vivo: `grep -rn "registro_vrp_ocr"` en `scripts`, `pipeline`, `frontend` y `.github` sólo la nombra en un comentario de `.github/workflows/sync-mirova-csv.yml:16`. Ojo, A92: un grep no ve una ruta armada en partes sin el nombre del archivo en la misma línea.
- Qué lee cada instrumento: el audit baja la tabla y el OCR vivos al snapshot al correr (`audit-weekly.yml:55` a `:58`); las vigilancias de la guardia MODIS y de la sombra bajan los vivos a un temporal (`vigilancia-guardia-modis.yml:52` a `:63`, `vigilancia-sombra.yml:55` a `:66`); el banco lee el snapshot con `--snapshot` y los vivos sin él (`banco_paridad.py` `main`); el tablero (`diario.html:209`, `comparacion.html:170`) lee `latest_consolidado.csv` de Pages.
- Acuerdo de tipo entre tabla y OCR en la misma pasada (desde el 2026-06-11): 255 alerta y alerta, 23 falso positivo y falso positivo, 0 desacuerdos (`I7.acuerdo_tabla_ocr_misma_pasada`). El desacuerdo está en la distancia (301), no en el tipo.
- Reproduje los conteos del orquestador de I7: tabla raíz 47.006 filas (44.060 RUTINA, 1.939 ALERTA_TERMICA, 1.007 FALSO_POSITIVO, 2026-01-10 a 2026-11-06); snapshot consolidado 46.351; OCR 1.238 (1.040, 103, 95); sólo OCR desde el 2026-06-11: 200 VIIRS 375, 9 VIIRS 750 y 1 MODIS. De las 200 de VIIRS 375, 189 tienen una fila de la tabla del mismo volcán y sensor a menos de 60 min (otra pasada) y 11 ninguna (`I7.solo_ocr_contexto`).

## 7. SIN DATO

- Identidad por lat/lon después del 2026-09-22: no hay TIF (los 33 pares volcán y sensor congelados según el índice) y no georreferencié la lámina Latest10NTI. Los 3 casos MODIS de Láscar posteriores (2026-09-25 08:00, 2026-10-08 08:00, 2026-10-26 07:55) no los miré en el índice PNG. Por qué falta el TIF (MIROVA o el poller): SIN DATO.
- Identidad por TIF antes del 2026-09-22 fuera de 8 casos: no bajé más. 4 de los 8 no pasan el control de georreferencia (el máximo dentro del inner no reproduce la distancia de la tabla), así que quedan (iv).
- Valor real de las 9 alertas OCR en 1,0 MW truncadas (307).
- Causa de la falta de Suomi NPP en la tabla (305).

## 8. FUERA DE ALCANCE

Detectores (F1, F2, sombra de #945); arreglos de cualquier tipo; Mirova-v1; ventanas anteriores al 2026-06-11 salvo los conteos de I7 sobre el archivo entero.

## 9. Campo (para mirar contra la lámina de MIROVA)

- Cordón Caulle VIIRS 750, 2026-10-10: nuestra VIIRS_SNPP_750 04:54 UTC (cúmulo a 13,76 km del vent) contra la alerta de MIROVA 05:54:02 UTC (1,19 MW, 7,83 km). Clase (iii) en otra pasada, contada como acierto de la noche.
- Isluga VIIRS 375, VIIRS_NOAA20 2026-09-22 05:42 UTC: el píxel máximo del TIF de MIROVA (−19,16558, −68,84986) está a 2,01 km del nuestro (−19,15445, −68,83477). Clase (iii) por TIF, 0,41 MW.
- Chillán VIIRS 375, VIIRS_NOAA21 2026-10-18 06:48 UTC: protegida de 25,79 MW, tabla a 1,88 km del centro, nuestros 8 píxeles entre 0,19 y 1,03 km. Al borde de la tolerancia, sin TIF: (iv) por posición, (iii) por radio.
