# Auditoría S150, frente B: lo que ve el operador del OVDAS durante la erupción de Nevados de Chillán

Auditor B, 2026-10-08 (hora del servidor de GitHub al cerrar: 18:24 UTC). Sólo lectura sobre el
repositorio; scripts y salidas en
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s150_audit\B\`.

## 0. Ventana medida, fuentes y eje nuevo

- **Eje que estrena esta auditoría**: la cadena promesa, supuesto, control **pasada por pasada** con el
  predicado literal de las tres vistas ejecutado en node (`vistas.js` extrae las funciones de
  `index.html`, `diario.html` y `mosaico.html`, cada una en su propio contexto, y llama al
  `enrichWithMirovaConfirmation` real con la referencia que carga el tablero), cruzado contra MIROVA
  crudo (CONS y OCR, todas las filas, incluidas RUTINA) en la **misma adquisición** (±10 min).
- **Nuestros datos**: `data/mirova_equivalent/NevadosDeChillan.json` bajado del remoto (raw de `main`,
  commit `327621e2c`) a las 18:14 UTC. **El último record de Chillán es el 2026-10-02 07:35 UTC**
  (`updated` 2026-10-02T12:34:06Z). El último commit que tocó ese archivo es `85be8ec21`
  (2026-10-02 12:34); volví a consultar a las 18:24 y el relleno del 3 al 8 de octubre **todavía no
  llegó al remoto**. Ventana efectiva: **2026-09-20 00:00 a 2026-10-02 07:35 UTC, 138 records**
  (27 MODIS, 56 VIIRS 375, 55 VIIRS 750). Del 2 al 8 de octubre: SIN DATO nuestro.
- **MIROVA**: `registro_vrp_consolidado.csv` y `registro_vrp_ocr.csv` del remoto de Mirova-v1, bajados
  hoy. Para Chillán desde el 20-sep: 317 filas CONS (30 ALERTA_TERMICA, 3 FALSO_POSITIVO, el resto
  RUTINA) y 20 filas OCR.
- **Tablero publicado**: lo abrí en el navegador interno, sólo lectura
  (`https://mendozavolcanic.github.io/VRP-chile/index.html?volcano=NevadosDeChillan`) a las 18:23 UTC.
  El `NevadosDeChillan_recent.json` desplegado es idéntico al remoto en los 138 records de la ventana,
  y el `index.html` desplegado es idéntico al de `main` salvo fin de línea.
- **Control de que mi instrumento es el del tablero**: el tablero vivo muestra en la tarjeta de
  Chillán «MIROVA 39 · nuestras 445 (90 d)»; mi script reproduce **445** exacto
  (`corroboracion_90d_salida.txt`), y las métricas vivas (FN = 8 / 6 / 3) cuadran pasada por pasada
  con mi tabla (§H6).

Dos preguntas del instrumento, comunes a la tabla principal (`tabla_ndc.py`):
1. Si el tablero ocultara toda pasada de erupción, la tabla lo vería (columna `ix_chart` en 0 frente a
   alerta MIROVA en la misma adquisición). Control positivo: 2026-10-01 08:35 MODIS sale oculta.
2. Si node no evaluara o el JSON no trajera la ventana, el resultado sería distinto: el script imprime
   records, última fecha y aborta si node falla. Control positivo del comparador de vistas: un record
   sintético con `distance_class = None` y cúmulo a 1 km sale en el gráfico y no en la tarjeta
   (`control_positivo_vistas_salida.txt`), o sea que el comparador **sí puede** ver una divergencia.

## 1. La tabla en una vista

Resumen por sensor, ventana 20-sep a 2-oct 07:35, unidad pasada (`resumen_salida.txt`):

| sensor | records | publicados por el tablero | pasadas con alerta MIROVA y record nuestro | publicadas | ocultas | nivel distinto al de MIROVA |
|---|---|---|---|---|---|---|
| MODIS | 27 | **1** | 3 | 1 | **2** | 0 |
| VIIRS 375 | 56 | 51 | 11 | 11 | 0 | 2 |
| VIIRS 750 | 55 | 20 | 8 | 7 | 1 | 2 |

Además: 2 alertas diurnas de MIROVA (2026-10-01 18:42, VIIRS 375 y 750) sin record nuestro por diseño,
y 21 filas de alerta de MIROVA entre el 3 y el 8 de octubre sin record nuestro por el apagón.
El detalle pasada por pasada está en `tabla_ndc_salida.txt`; las alertas con su magnitud y su nivel, en
`resumen_salida.txt`.

## 2. Hallazgos, de mayor a menor gravedad

### H1. MODIS de Chillán está casi entero oculto: la etiqueta `far` sale de un píxel que el propio store ya había descartado

- **ARCHIVO:LÍNEA**: `pipeline/process_modis.py:1306-1330` (cascada del `final_hotspot` y
  `derivar_distance_class`), `pipeline/process_modis.py:300-320`, `pipeline/store.py:225-277`
  (filtro por píxel), `pipeline/store.py:347-389` (rescate F47), `frontend/index.html:1056`.
- **QUÉ PASA**: en una noche de invierno el píxel MIR más brillante de la escena MODIS de 51 × 51 km
  suele ser terreno tibio de baja altitud o un borde de la grilla, no el cráter. La etiqueta
  `summit`/`far` sale de ese píxel. El store recorta los píxeles a la geocerca del volcán (25 km) y
  recalcula `hotspot_*`, **pero no recalcula `final_hotspot_*` ni la etiqueta**, así que quedan
  derivadas de un píxel que el mismo store marcó como fuera de la geocerca
  (`discarded_reason = partial_eruption_hotspot_too_far` en los 27 MODIS de la ventana). Y como el
  rescate F47 sólo dispara si `hotspot_dist_km > 25`, y el filtro acaba de dejar `hotspot_dist_km`
  dentro de 25, el rescate escrito justamente para este caso (el comentario de `store.py:337` usa a
  Chillán de ejemplo) no puede disparar.
  Caso testigo: 2026-10-01 08:35 MODIS_AQUA, `final_hotspot_dist_km` 32,84, `hotspot_dist_km` 19,17,
  cúmulo a 0,883 km con 2,293 MW, MIROVA 5,18 MW a 2,24 km.
- **CÓMO SE VE EN EL DASHBOARD**: de 27 pasadas MODIS sólo se publica una (2026-10-01 01:45, 4,17 MW
  contra 6,17 de MIROVA). Las otras dos pasadas MODIS con alerta de MIROVA no aparecen en gráfico,
  tabla, tarjeta ni mosaico: 2026-09-29 07:20 (MIROVA 0,13 MW a 0,0 km; nuestro cúmulo 0,33 MW a
  5,95 km) y 2026-10-01 08:35 (5,18 MW). Es crónico, no de la erupción: en el historial de Chillán hay
  **798 records MODIS `far` con cúmulo con energía dentro de los 5 km del inner**, entre 40 y 52 por
  mes desde febrero (`etiqueta_desde_pixel_descartado_salida.txt`); en septiembre, 17 de esos 43 tienen
  el `final_hotspot` más allá de los 25 km de la geocerca.
- **En la unidad del operador (A94)**: las dos noches afectadas (29-sep y 1-oct) igual se publicaron
  por VIIRS (3,17 y 11,08 MW), así que **0 noches de alerta perdidas** en la ventana. Lo que se pierde
  es la pasada de la mañana (08:35 es la última de la noche) y el sensor MODIS completo como segunda
  opinión.
- **CÓMO REPRODUCIRLO**: `python experiments/_s150_audit/B/tabla_ndc.py` y
  `python experiments/_s150_audit/B/etiqueta_desde_pixel_descartado.py`.
- **CONFIANZA**: CONFIRMADO (código leído, flag resuelto con `pipeline.profile`:
  `ENABLE_PIXEL_LEVEL_DISTANCE_FILTER = True`, `ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER = False`;
  medido en el JSON remoto).
- **GRAVEDAD**: 4.

### H2. Encender el flag de etiqueta por cúmulo, solo, cambia una alerta recuperada por veinte publicaciones donde MIROVA no vio nada (esto cambia el plan)

- **ARCHIVO:LÍNEA**: `pipeline/process_modis.py:300-320`; contrafactual en
  `experiments/_s150_audit/B/tabla_ndc.py --flag-cumulo` (replica `derivar_distance_class` con
  `desde_cluster=True` sobre los MODIS de la ventana y reevalúa las tres vistas en node).
- **QUÉ PASA**: la etiqueta `far` de H1 está haciendo hoy un segundo trabajo que nadie le encargó:
  **esconde el tope D9 de MODIS**. En las noches frías de invierno el camino contextual MODIS de
  Chillán dispara sobre el fondo helado y su cúmulo queda recortado a 5,000 MW (ver H3); todos esos
  records son hoy `far` y no se ven.
- **CÓMO SE VE EN EL DASHBOARD (contrafactual)**: con el flag encendido, MODIS pasaría de 1 a **23
  publicaciones** en 13 días. Recupera **1** de las 2 alertas ocultas (2026-10-01 08:35; la de
  2026-09-29 07:20 sigue oculta porque su cúmulo está a 5,95 km, fuera del inner de 5). Y publica
  **20 pasadas donde MIROVA listó la misma adquisición como RUTINA, 9 de ellas con exactamente
  5,00 MW** (el valor censurado, que el tablero muestra con asterisco y el nivel «Bajo»), más 1 sin fila
  de MIROVA (`tabla_ndc_flag_salida.txt`, `resumen_salida.txt`, segundo bloque).
- **CÓMO REPRODUCIRLO**: `python experiments/_s150_audit/B/tabla_ndc.py --flag-cumulo` y
  `python experiments/_s150_audit/B/resumen.py`.
- **CONFIANZA**: CONFIRMADO como contrafactual de etiqueta (el flag sólo reetiqueta, verificado en
  `process_modis.py:310-320`, y el guard A46 de `store.py:480-486` sólo pasa a `far` cúmulos más allá
  del inner, así que no deshace el cambio). SOSPECHA en lo que no reproduce: no corrí el pipeline.
- **GRAVEDAD**: 4. Consecuencia para el plan: el flag de S132 no es un arreglo gratis; antes de
  encenderlo hay que decidir qué pasa con el tope D9 de MODIS (H3), o el tablero de Chillán se llena
  de «5,00 MW Bajo» en noches de RUTINA.

### H3. El tope de 5 MW está armado en casi todas las pasadas de la erupción, y el tablero lo explica como cirrus

- **ARCHIVO:LÍNEA**: predicado en `pipeline/process_modis.py:1009-1016`,
  `pipeline/process_viirs.py:1415-1422`, `pipeline/process_viirs_mod.py:987-994`; tope en
  `pipeline/path_d_cap.py`; texto del tablero en `frontend/index.html:1101-1103`
  (`TXT_VALOR_CENSURADO`), `frontend/index.html:2071-2077` (tarjeta), `:2330-2333` (detalle),
  `frontend/diario.html:666-676`.
- **QUÉ PASA**: el tope recorta el cúmulo a 5,0 MW cuando no disparó ningún píxel por BT ni por NTI
  absoluto y el fondo está bajo 270 K. Con `ENABLE_BT_PATH_HOT = False` (resuelto con
  `pipeline.profile`) el primer término es siempre verdadero, y en Chillán el NTI absoluto casi nunca
  supera −0,8 ni en erupción. El predicado queda reducido a «noche fría», que en un volcán de
  3.200 m en invierno es casi toda noche. El tablero, en cambio, le dice al operador que un 5,00 es
  «path D sobre cirrus ... probablemente artefacto».
- **Medido** (`tope_d9_en_erupcion_salida.txt`, `tope_d9_pasadas_alerta_salida.txt`): predicado activo
  en **21 de 27** MODIS, **44 de 55** VIIRS 375 y **53 de 55** VIIRS 750 de la ventana; en las pasadas
  con alerta de MIROVA, 1 de 3, 4 de 11 y **6 de 8**. Control: los 61 records de Chillán de 2026 con
  cúmulo exactamente 5,000 tienen el predicado reconstruido activo (61 de 61). En la ventana **no
  recortó ninguna pasada con alerta**: las más fuertes se salvaron por 1 a 3 píxeles NTI o por un
  fondo de 270,2 a 271,8 K (al filo). La pasada 2026-10-01 05:24 VIIRS 750 (MIROVA 9,0 MW, nuestro
  2,66) tenía el tope armado.
- **CÓMO SE VE EN EL DASHBOARD**: hoy, nada en Chillán (los 5,00 de MODIS están ocultos por H1).
  Latente: la primera pasada de erupción sobre 5 MW con fondo frío y sin píxel NTI saldrá como
  «5,00 * MW (tope, no medido)» con un texto que la atribuye a nube.
- **CÓMO REPRODUCIRLO**: `python experiments/_s150_audit/B/tope_d9_en_erupcion.py`. Predicción
  falsable para cuando llegue el relleno: 2026-10-05 05:48 VIIRS 750 (MIROVA CONS 7,86 MW) y
  2026-10-05 06:24 VIIRS 750 (OCR 7,0 MW); si nuestro record sale en 5,000 exacto, el tope recortó
  señal de erupción.
- **CONFIANZA**: CONFIRMADO el mecanismo y el armado; SOSPECHA que vaya a recortar una pasada real
  (no observado aún).
- **GRAVEDAD**: 4 (puede bajar un valor de erupción al tope y rotularlo de artefacto). La magnitud en
  sí es del frente C; acá se reporta el rótulo que ve el operador.

### H4. La referencia de MIROVA del tablero tira las alertas de 10 MW o más

- **ARCHIVO:LÍNEA**: `scripts/rebuild_mirova_from_consolidado.py` (conjunto cerrado
  `VALID_CLASSES = {"Muy Bajo", "Bajo"}`, con la instrucción escrita de no agregar «Moderado»),
  invocado por `.github/workflows/sync-mirova-csv.yml:160-172`; lo consumen `frontend/index.html:975`
  y `frontend/mosaico.html:472`.
- **QUÉ PASA**: MIROVA rotula «Moderado» de 10 a 100 MW (el canal OCR ya lo usa: 5 filas entre 10,0 y
  37,0 MW). El consolidado nunca tuvo una alerta de 10 MW o más en toda su historia (las seis mayores
  de todo el archivo son de Chillán esta semana, máximo 7,86 MW). La primera vez que la tenga, el
  script la rechaza en silencio (sólo deja una línea en el log del workflow).
- **CÓMO SE VE EN EL DASHBOARD**: desaparecerían justo las alertas más fuertes de MIROVA de la línea
  de referencia del gráfico, de la fila «MIROVA x · nuestras y», del cruce `_mirova_confirmed` y de las
  métricas. `diario.html` lee el CSV directo filtrando sólo por `Tipo_Registro` (`diario.html:206`), así
  que las dos vistas empezarían a contar distinto.
- **CÓMO REPRODUCIRLO**: leer el script; universo de clases del CSV en esta sesión:
  NULO 39.969, Muy Bajo 1.347, Bajo 248, FALSO POSITIVO 12.
- **CONFIANZA**: CONFIRMADO el filtro; SOSPECHA que el consolidado use la palabra «Moderado» (lo usa el
  OCR, que lee la misma imagen de MIROVA).
- **GRAVEDAD**: 4 en una erupción que escala; hoy, latente.

### H5. El tablero dice que su referencia de MIROVA es CONS ∪ OCR y es sólo CONS

- **ARCHIVO:LÍNEA**: `data/mirova/NevadosDeChillan.json` (campo `note`: el OCR queda excluido a
  propósito), generado por el script de H4; textos que dicen lo contrario en
  `frontend/index.html:2184`, `:2217` y `:2372`.
- **QUÉ PASA**: MIROVA publica algunas pasadas sólo en sus imágenes; el scraper las rescata por OCR.
  El tablero no las carga, pero tres textos al operador afirman que el universo es CONS ∪ OCR.
- **CÓMO SE VE EN EL DASHBOARD**: en la ventana hay **9 pasadas con alerta sólo en OCR**, entre ellas
  la más fuerte de MIROVA de toda la erupción, VIIRS 750 de 2026-10-01 06:00 con **10,0 MW
  «Moderado»**, y VIIRS 375 de 2026-10-05 06:24 con 8,24 MW. La línea de MIROVA del gráfico muestra
  para VIIRS 750 del 1-oct un máximo de 7,06 MW (banda Bajo) en vez de 10,0 (banda Moderado), y para
  VIIRS 375 del 5-oct 5,77 en vez de 8,24. La fila «MIROVA 39» de la tarjeta tampoco las cuenta.
- **CÓMO REPRODUCIRLO**: `tabla_ndc_salida.txt` (filas con `OCR` sin `CONS` en la misma adquisición).
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 3.

### H6. Las métricas «vs MIROVA (live)» cuentan como perdidas las pasadas que no procesamos

- **ARCHIVO:LÍNEA**: `frontend/index.html:1293-1401` (`computeMetrics`), texto en `:2372-2377`.
- **QUÉ PASA**: un FN debería ser «MIROVA vio y nosotros no». El cálculo cuenta como FN toda alerta de
  MIROVA sin record nuestro a ±60 min, sin distinguir «lo procesamos y no lo vimos» de «no hubo
  pasada procesada» (apagón del NRT, o pasada diurna que el pipeline rechaza por diseño).
- **CÓMO SE VE EN EL DASHBOARD** (leído en vivo a las 18:23 UTC, ventana 30 d): VIIRS 375 recall
  **0,56** (TP 10, FN 8), VIIRS 750 0,45 (TP 5, FN 6), MODIS 0,25 (TP 1, FN 3). Desglosado contra mi
  tabla y contra la página: de los 17 FN, **12 son alertas posteriores a nuestro último record**
  (2-oct 07:35), **2 son la pasada diurna del 1-oct 18:42**, y sólo **3 son pasadas procesadas y
  ocultas** (las dos MODIS de H1 y VIIRS 750 de 2026-10-01 04:42, cúmulo en 0,00 MW contra 0,09 de
  MIROVA). En VIIRS 375 el recall real sobre pasadas procesadas es 10 de 10. El operador lee que el
  sistema se pierde la mitad de la erupción.
- **CÓMO REPRODUCIRLO**: abrir el tablero en Chillán; en consola,
  `allData.NevadosDeChillan.mirovaRecords.filter(m => m.datetime_utc > "2026-10-02 07:35")` da las 12.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 3.

### H7. MIROVA publica alertas diurnas de la erupción que el pipeline descarta siempre

- **ARCHIVO:LÍNEA**: `pipeline/store.py:179-190` (`_reject_daytime`) y `:597`;
  `ENABLE_DAYTIME_MODIS = False` resuelto con `pipeline.profile`.
- **QUÉ PASA**: el docstring dice que MIROVA procesa VIIRS sólo de noche. El consolidado lo contradice:
  2026-10-01 18:42 UTC (15:42 hora local, sol a 47°) MIROVA publicó Chillán VIIRS 375 2,53 MW a
  0,38 km y VIIRS 750 3,71 MW a 0,75 km. En todo el consolidado hay 23 alertas diurnas VIIRS 375,
  3 VIIRS 750 y 5 MODIS, contra 1.184, 286 y 94 nocturnas (misma función de elevación solar del store,
  importada; `alertas_diurnas_mirova_salida.txt`).
- **CÓMO SE VE EN EL DASHBOARD**: el triángulo de MIROVA aparece en el gráfico sin barra nuestra, y la
  pasada cuenta como FN (H6). Nada le avisa al operador que de día el sistema no mira.
- **CONFIANZA**: CONFIRMADO el hecho y la regla; SOSPECHA que las dos de Chillán sean reales y no el
  artefacto solar de A76 (a 0,38 y 0,75 km de un volcán en erupción es lo más probable, pero no lo
  verifiqué con imagen).
- **GRAVEDAD**: 3 (cobertura no declarada; la decisión de procesar de día es de diseño).

### H8. Durante la erupción el tablero lee más bajo que MIROVA, y en 4 pasadas cambia de banda

- **ARCHIVO:LÍNEA**: `frontend/index.html:787-791` (`getLevel`); magnitudes de `primary_cluster.vrp_mw`
  y `f5_core_vrp_mw`.
- **QUÉ PASA**: en las 18 pasadas con alerta que publicamos, la razón nuestro/MIROVA va de 0,15 a 2,39;
  el tablero vivo da mediana **0,58** en VIIRS 375 (10 pares) y **0,35** en VIIRS 750 (5 pares).
  Cuatro quedan en «Muy Bajo» donde MIROVA dice «Bajo»: 2026-09-28 04:42 VIIRS 375 (0,49 contra 2,58),
  2026-09-29 05:00 VIIRS 375 (0,21 contra 1,41 OCR), 2026-09-29 06:00 VIIRS 750 (0,72 contra 2,52) y
  2026-09-29 06:36 VIIRS 750 (0,33 contra 2,03).
- **CÓMO SE VE EN EL DASHBOARD**: color y rótulo de nivel una banda más abajo que MIROVA en esas
  pasadas. La causa de la magnitud es del frente C.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 3.

### H9. La tarjeta de Chillán sube y baja de nivel según qué satélite pasó último

- **ARCHIVO:LÍNEA**: `frontend/index.html:1490-1543` (`latestDetection`, decisión S90),
  `frontend/mosaico.html:422-439` (misma regla desde S130).
- **QUÉ PASA**: la tarjeta muestra la última pasada con detección, no la mayor. En erupción, pasadas
  de distinta geometría se alternan dentro de la misma noche.
- **CÓMO SE VE EN EL DASHBOARD** (reconstruido hora a hora, `tarjeta_y_confirmacion_salida.txt`): el
  1-oct, 4,17 MW Bajo desde las 02:00 UTC, 0,23 Muy Bajo desde las 05:00, 11,08 Moderado desde las
  06:00, 4,21 Bajo desde las 07:00; el 2-oct desde las 06:00, 0,02 Muy Bajo. El badge del detalle dice
  «Moderado · máx 30 d» todo ese tiempo. Está rotulado (tooltip de `index.html:2060`), pero el color
  de la tarjeta lo decide el último satélite, no el volcán.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 2 (decisión de diseño de Nicolás; la reporto para que se
  pruebe en campo, §4).

### H10. «MIROVA publicó en esta pasada» es verdadero a ±60 min, no en la pasada

- **ARCHIVO:LÍNEA**: `frontend/index.html:1415-1455` (tolerancia 60 min, sólo CONS),
  texto en `:2181-2184`.
- **QUÉ PASA**: en una noche con varias pasadas separadas por 20 a 40 min, la marca de una pasada la
  enciende la alerta de otra.
- **CÓMO SE VE EN EL DASHBOARD**: de los 22 records elegibles para la tarjeta con la marca encendida,
  3 no tienen alerta de MIROVA en su propia adquisición: 2026-09-28 05:18 VIIRS_SNPP_750 (MIROVA sin
  fila), 05:36 VIIRS_NOAA20 y 07:00 VIIRS_SNPP (MIROVA las listó RUTINA). Ninguna marca apagada tiene
  alerta en la pasada (contingencia en `tarjeta_y_confirmacion_salida.txt`). La marca además exime de
  los filtros de artefacto.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 2.

### H11. «nuestras 445 (90 d)» cuenta 180 records que el tablero no muestra

- **ARCHIVO:LÍNEA**: `frontend/index.html:2007-2025` (`corroboracionMirova` usa `isValidDetection`
  sin filtro de cráter ni de artefacto).
- **CÓMO SE VE EN EL DASHBOARD**: de 445, 265 se publican; 176 son MODIS `far` ocultos (H1) y 4 VIIRS
  750 (`corroboracion_90d_salida.txt`, 90 d antes de 2026-10-08 18:23 UTC). El cociente contra
  «MIROVA 39» se infla.
- **CONFIANZA**: CONFIRMADO (reproduce el 445 del tablero vivo). **GRAVEDAD**: 2.

### H12. En la capa de hotspots del mapa general, la pasada MODIS del 1-oct 08:35 aparece a 19 km con 5,000 MW

- **ARCHIVO:LÍNEA**: `frontend/index.html:3480-3553` (`updateHotspotLayer`: no filtra `far`, posición
  `hotspot_lat`, magnitud `r.vrp_mw`).
- **QUÉ PASA**: esa capa (opcional, apagada por defecto) dibuja los records `far` en el píxel más
  energético dentro de la geocerca y con la suma de escena, que A10 dice que no es el campo a mostrar.
- **CÓMO SE VE EN EL DASHBOARD**: el único lugar donde aparece la pasada con alerta de MIROVA de
  2026-10-01 08:35 la pone a 19,2 km del cráter con «VRP final 5,000 MW»; el cúmulo real está a 0,88 km
  con 2,29 MW. Leído en código y datos, **no lo verifiqué visualmente** en el mapa.
- **CONFIANZA**: CONFIRMADO por lectura y datos. **GRAVEDAD**: 2.

### H13. Menores

- 5 records VIIRS con cúmulo en exactamente 0,0 MW quedan ocultos por `isValidDetection`
  (`index.html:1474`); uno coincide con alerta de MIROVA de 0,09 MW (2026-10-01 04:42 VIIRS 750).
  CONFIRMADO, gravedad 1.
- El núcleo F5' **sube** la magnitud por sobre el cúmulo en VIIRS 375 en varias pasadas
  (2026-09-29 06:36: 1,30 a 2,68; 2026-10-01 05:24: 2,58 a 3,25), mientras el comentario de
  `index.html:1182` dice que sólo reduce el halo y el tooltip de `diario.html:100` lo presenta como cura
  de una sobreestimación. En esos casos se acerca a MIROVA.
  CONFIRMADO, gravedad 1.

## 3. Censo de compuertas que pueden ocultar o deformar una pasada de erupción

| compuerta | dónde | qué hizo en Chillán, 20-sep a 2-oct |
|---|---|---|
| `distance_class` desde el píxel más caliente (MODIS) | `process_modis.py:1328`, `index.html:1056`, `:1485` | ocultó 26 de 27 MODIS, 2 con alerta (H1) |
| filtro por píxel a la geocerca sin recalcular la etiqueta | `store.py:225-277` | 27 de 27 MODIS con descarte parcial (H1) |
| rescate F47 | `store.py:347-389` | no disparó (último en Chillán: 2026-09-19 05:48) |
| guard A46 summit a far | `store.py:480-486` | sin efecto visible en la ventana |
| `pc.centroid_dist_km > inner` | `index.html:1060` | ocultaría 09-29 07:20 aun con el flag (5,95 km) |
| `isValidDetection` (cúmulo en 0) | `index.html:1474` | 5 ocultos, 1 con alerta de 0,09 MW |
| tope D9 de 5 MW | `path_d_cap.py`, procesadores | armado en la mayoría; no recortó alertas aún (H3) |
| texto «censurado, probablemente cirrus» | `index.html:1101` | ninguno visible; latente (H3) |
| cirrus y campo difuso | `index.html:1207-1238` | 0 records atrapados |
| tope de cordura 50.000 MW | `store.py:116`, vistas | n/a |
| pisos por sensor | `store.py:73` | apagados (0,0 los tres, resuelto con `pipeline.profile`) |
| núcleo F5' | `index.html:1166-1186` | sólo VIIRS 375; a veces sube (H13) |
| rechazo diurno | `store.py:179`, `:597` | 2 alertas diurnas de MIROVA sin record (H7) |
| clases de la referencia | `rebuild_mirova_from_consolidado.py` | latente para 10 MW o más (H4) |
| OCR fuera de la referencia | mismo script | 9 alertas sólo OCR invisibles (H5) |

## 4. Pruebas de campo propuestas (qué mirar en el tablero y qué decide)

1. **Cuando llegue el relleno del 3 al 8 de octubre**, abrir Chillán y buscar en la tabla del detalle
   la pasada 2026-10-05 05:48 VIIRS_NOAA20_750 (o la de 05:48 que exista) y 2026-10-05 06:24 VIIRS 750.
   Si alguna dice «5,00 *» o «tope, no medido» con MIROVA en 7 a 8 MW, H3 dejó de ser latente: el tope
   D9 tiene que salir de las pasadas con señal de cráter antes de cualquier otra cosa. Si dicen un
   número distinto de 5, H3 sigue latente.
2. **Antes de encender `ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER`**, mirar en el tablero con
   «Incluir lejanas» las barras MODIS de Chillán entre el 20-sep y el 2-oct: si se ve una fila de
   5,00 MW en noches donde la línea de MIROVA no tiene triángulo, eso es lo que el flag publicaría en
   el modo por defecto (H2). Decide si el flag va solo o junto con un arreglo del tope.
3. **Mirar las métricas «vs MIROVA (live)» de Chillán** y contar a mano cuántos FN caen después de la
   última pasada procesada: decide si el recall se calcula sólo sobre pasadas procesadas (H6).
4. **Comparar en el gráfico la línea de MIROVA VIIRS 750 del 1-oct (7,06) con la imagen de MIROVA de
   las 06:00 UTC (10,0 Moderado)**: decide si la referencia del tablero debe sumar el OCR o quitar el
   «CONS ∪ OCR» de sus textos (H5), y obliga a abrir el conjunto de clases de H4.
5. **Durante una noche activa, anotar el color de la tarjeta cada hora** y compararlo con el badge
   «máx 30 d»: decide si en erupción la tarjeta debe mostrar el máximo de la noche (H9).

## 5. Lo que queda SIN VERIFICAR

- El comportamiento real del pipeline con el flag encendido (H2 es un contrafactual de etiqueta, no un
  reproceso).
- Que el consolidado vaya a rotular «Moderado» (H4).
- Que las alertas diurnas del 1-oct sean señal y no reflejo solar (H7).
- El dibujo del mapa (H12): no hice captura ni inspeccioné el marcador.
- Todo lo del 2 al 8 de octubre: el remoto no tenía nuestros records a las 18:24 UTC.

## 6. VERIFICADO LIMPIO

- **Las tres vistas dicen lo mismo en Chillán**: en los 138 records de la ventana coinciden el valor del
  gráfico de `index.html`, el de `diario.html` y el sparkline de `mosaico.html`, y la elegibilidad de
  tarjeta de `index.html` y `mosaico.html` (0 diferencias en `resumen_salida.txt`; el comparador sí ve
  una divergencia sintética, `control_positivo_vistas_salida.txt`).
- **Gráfico, tabla, estadísticas y VRE del detalle** usan el mismo `eqVrp` (`index.html:2258`,
  `:2267`, `:2324`, `:2513`, `:3039-3059`): un mismo número por pasada.
- **Lo desplegado es lo del repo**: `NevadosDeChillan_recent.json` de Pages idéntico al remoto en la
  ventana; `index.html` idéntico a `main` salvo CRLF; `data/mirova/NevadosDeChillan.json` generado hoy
  16:27 UTC.
- **El apagón se ve en la tarjeta**: «SIN DATOS», «sin pasadas hace 6 d», «pasada vencida hace 137 h»,
  leído en vivo. La tarjeta no finge actividad ni calma.
- **Filtros cirrus y campo difuso**: 0 records atrapados en la ventana (columna `art`).
- **Records con `distance_class = None`** (35): ninguno tiene cúmulo; no hay ninguno que el gráfico
  muestre y la tarjeta no.
- **Parseo de horas**: todas las vistas usan `parseUtcMs`; las horas de MIROVA y las nuestras parean
  al minuto (los 26 pareos de alerta de la ventana caen en el mismo minuto UTC, medido sobre
  `tabla_ndc.json`).
- **Sin pisos ni topes de cordura activos sobre Chillán** (pisos 0,0; máximo 11,08 MW lejos de 50.000).

Comandos: todos desde
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s150_audit\B\`:
`python tabla_ndc.py`, `python tabla_ndc.py --flag-cumulo`, `python resumen.py`,
`python tarjeta_y_confirmacion.py`, `python etiqueta_desde_pixel_descartado.py`,
`python tope_d9_en_erupcion.py`, `python alertas_diurnas_mirova.py`. Datos crudos bajados hoy en
`datos\` (38 MB; se pueden borrar y volver a bajar con las URL de §0).
