# Auditoría S155, frente 2: lo que ve el operador con K

Worktree `D:\vrp-trabajo\worktrees\s155-audit-f2`, detached en `cb90031a` (origin/main del 2026-10-19). Ningún archivo del
repositorio fue modificado; todo lo de esta carpeta son scripts de medición y sus salidas (`*.out`, `*.json`).

Los predicados se ejecutaron con node sobre el código literal de cada vista (A97): `extraer.js` copia el texto de cada
función top-level de `frontend/index.html`, `diario.html` y `mosaico.html` y lo corre en un contexto aislado con el reloj
fijo en 2026-10-19 12:00 UTC. Los flags se leyeron desde `pipeline.profile` (`ENABLE_TEST1_PATH False`,
`ENABLE_TESTS_23_PROSE_BRANCH True`, `ENABLE_MODIS_B22_PRIMARY True`, `ENABLE_DAYTIME_MODIS/VIIRS False`).

Frontera real de los datos, medida (`inventario_regimen.py`): en los 11 Tier A el primer record con `regimen.codigo_sha`
es del **2026-09-18**; los 12 sha presentes descienden de `34cea39e` (merge de K); ningún record anterior al 2026-09-18
trae marca (62.643 sin marca). O sea que en `data/mirova_equivalent/` hoy rige C0 hasta el 2026-09-17 y K desde el
2026-09-18, salvo 26 records sueltos (F2-08).

---

## F2-01. La marca del cambio de detector está en la fecha equivocada: el escalón está un mes antes y sin rótulo

- **ARCHIVO:LÍNEA**: `frontend/cambio_detector.js:16` (`CAMBIO_DETECTOR_UTC = "2026-10-18T09:57:30Z"`), texto en
  `:41-43`. SCRIPT: `escalon_vs_marca.js` → `escalon_vs_marca.out`; `inventario_regimen.out`.
- **QUÉ PASA**: con C0 casi todos los volcanes publicaban en VIIRS 375 casi todas las noches (el Test 1 integrado disparaba
  sobre señal sub-umbral); con K esas noches quedan en blanco. El reproceso de 30 días puso K en los datos desde el
  **2026-09-18**, así que el escalón de la tendencia está ahí. Pero la marca (línea punteada «detector K» en todos los
  gráficos de tiempo y el aviso amarillo de las tres vistas) quedó en la hora del merge de #850, **2026-10-18 09:57 UTC**:
  #851 se commiteó a las 10:02 UTC y los commits `data(backfill) ... 2026-09-18..2026-10-18` llegaron desde las 11:13 UTC
  (`git log`), y nadie movió la marca. El aviso dice además «Las comparaciones que crucen esa fecha mezclan dos
  detectores», que es falso para el 18-oct (los dos lados son K) y calla sobre el 18-sep, que es donde se mezclan.
- **CÓMO SE VE EN EL DASHBOARD**: en `diario.html` (90 días por defecto) días con barra de VIIRS 375, tramo C0
  (2026-07-21 a 09-17, 59 d) contra tramo K sin rotular (09-18 a 10-17, 30 d): Copahue **56 → 0**, Llaima **52 → 0**,
  Villarrica **53 → 2**, Chaitén **55 → 3**, Planchón-Peteroa 45 → 10, Tupungatito 42 → 12. VIIRS 750: Copahue 32 → 0,
  Lastarria 21 → 0, Villarrica 36 → 1. Un geólogo lee «Villarrica, Copahue y Llaima dejaron de tener anomalía térmica el
  18 de septiembre», sin ninguna marca en esa fecha, y una línea «detector K» treinta días después donde no cambia nada.
  En `index.html` pasa lo mismo al elegir 60 d, 90 d o más; en `mosaico.html` (30 d) la línea se dibuja al borde derecho
  de las 11 miniaturas.
- **CÓMO REPRODUCIRLO**: `node experiments/_s155_audit/frente_2/escalon_vs_marca.js`; en pantalla, `diario.html`, tarjeta
  Villarrica o Copahue, período 90 días, mirar el 2026-09-18 UTC y la línea del 2026-10-18.
- **POR QUÉ NO LO ATRAPÓ NADIE**: `tests/test_cambio_detector_s153.py:71-73` sólo exige que la constante sea null o ISO;
  ninguna prueba la compara con la frontera de los datos, y las vistas no leen `regimen.codigo_sha` (0 usos en las tres,
  F2-12).
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 4. Puede hacer leer como cese de actividad (Villarrica, lago de lava) lo que es un cambio de detector.

## F2-02. Chillán en erupción: el nivel que se muestra queda bajo el de MIROVA en uno de cada cuatro pares

- **SCRIPT:SALIDA**: `chillan_nivel_vs_mirova.js` → `.out`, y con referencia sólo de la tabla `chillan_nivel_vs_mirova_tabla.out`;
  caso en `mirova_en_cambios_de_nivel.out` y `caso_nucleo_mayor.out`.
- **QUÉ PASA**: durante la erupción de Nevados de Chillán la anomalía es grande y repartida en varios cúmulos cerca del
  cráter. Lo que el tablero grafica (núcleo F5' en VIIRS 375, cúmulo principal en los demás) es una fracción de lo que
  MIROVA publica para la misma pasada: razón mediana nuestro/MIROVA **0,57** VIIRS 375 (53 pares), **0,48** VIIRS 750
  (37), **0,24** MODIS (11), con la tabla de MIROVA sola. En **23 de 101** pares el tablero dice Muy Bajo o Bajo cuando
  MIROVA publicó Moderado (9 + 9 + 5). Ejemplo 2026-10-18 06:48 VIIRS_NOAA21: cúmulo 4,08 MW, núcleo 8,93 MW, MIROVA
  25,79 MW (Moderado). Mecanismo, SOSPECHA: se publica un solo cúmulo (el más cercano al cráter) y MIROVA suma todos los
  píxeles alertados de la pasada (rebaja de A10, D32); en ese caso hay dos fragmentos a 0,7 km y el más caliente (331 K)
  no es el publicado. Que esto sea propio de K o ya ocurriera con C0 no está medido (con C0 no hubo erupción que comparar).
- **CÓMO SE VE EN EL DASHBOARD**: tarjeta, tabla y gráfico de Chillán en «Bajo» en pasadas en que MIROVA dice «Moderado».
- **CÓMO REPRODUCIRLO**: `SOLO_TABLA=1 node experiments/_s155_audit/frente_2/chillan_nivel_vs_mirova_tabla.js`.
- **CONFIANZA**: CONFIRMADO el desfase y el conteo; SOSPECHA el mecanismo.
- **GRAVEDAD**: 4. Es el nivel de alerta de un volcán en erupción, un escalón por debajo de la referencia.

## F2-03. El gráfico «Distancia» salta de 0,0 km a ~0,2-1,3 km en la frontera: parece migración de la fuente

- **ARCHIVO:LÍNEA**: `frontend/index.html:3273-3299` (`buildDistanceData`, toma `final_hotspot_dist_km` del ancla
  honesta). SCRIPT: `distancia_escalon.js` → `.out` (función anidada extraída por texto y ejecutada); `textos_test1_y_coherencia.out`.
- **QUÉ PASA**: con C0 el 54 % de las detecciones publicadas (1.457 de 2.712, 60 d) venían ancladas por el Test 1 al
  cráter por construcción (`test1_roi`, distancia 0,0 exacta, no medida). Con K el ancla es el centroide del cúmulo, una
  medición. Fracción de puntos en 0,0 km antes y después del 2026-09-18 (90 d): Copahue 0,86 → sin puntos, Llaima 0,81 →
  sin puntos, Planchón-Peteroa 0,77 → 0, Villarrica 0,74 → 0, Tupungatito 0,63 → 0, Chillán 0,62 → 0, Lastarria 0,57 → 0.
  Mediana de la distancia: Lastarria 0 → **1,31 km**, Chillán 0 → **0,67 km**, Planchón-Peteroa 0 → 0,42 km.
- **CÓMO SE VE EN EL DASHBOARD**: pestaña «Distancia» del detalle con período de 60 d o más: nube pegada al eje en cero
  hasta el 18-sep y después dispersa a cientos de metros. En Chillán en erupción se lee como fuente que se aleja del cráter
  (actividad de flanco); `diario.html` dice en su propia ayuda que una distancia que crece «señala posible actividad de
  flanco».
- **CÓMO REPRODUCIRLO**: `node experiments/_s155_audit/frente_2/distancia_escalon.js`; `index.html`, Lastarria o Chillán,
  90 días, pestaña Distancia.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 3 (el período por defecto de 30 d ya no cruza la frontera).

## F2-04. La «anomalía relativa» de la tarjeta compara la pasada K contra una base de 90 días casi toda C0

- **ARCHIVO:LÍNEA**: `frontend/index.html:1834-1852` (`anomaliaRelativa`), llamada en `:2362`.
  SCRIPT: `tarjetas_y_metricas.js` → `.out`.
- **QUÉ PASA**: la base son las detecciones del mismo volcán en los 90 días previos, sin distinguir detector. Hoy la base
  es mayoritariamente C0, que publicaba casi cada noche valores de centésimas de MW. Chillán: base 169 C0 + 104 K, la
  tarjeta dice **percentil 93 · 110,7× su mediana** (mediana 0,081 MW); con la base K sola sería percentil 82 · 3,4×
  (mediana 2,66). Chaitén: base 289 C0 + 9 K, la tarjeta afirma percentil 64 · 1,4×; con K sola la función no afirmaría
  nada (menos de 10, «sin historia suficiente»). PCC 443 C0 + 65 K; Isluga 262 + 68; Tupungatito 206 + 26 (56 % contra
  65 %); Planchón-Peteroa 220 + 18 (3,7× contra 1,6×).
- **CÓMO SE VE EN EL DASHBOARD**: línea «percentil N de su propia base 90 d · X× su mediana» en las tarjetas; la mezcla
  dura hasta ~2026-12-16 (90 días después de la frontera).
- **CÓMO REPRODUCIRLO**: `node experiments/_s155_audit/frente_2/tarjetas_y_metricas.js` (campos `anom_mezclada`,
  `anom_soloK`, `base_C0`, `base_K`).
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 3 (es el indicador que la propia vista declara más importante para vigilancia).

## F2-05. El panel «Métricas vs MIROVA» cuenta como pérdidas las alertas diurnas de MIROVA (la réplica es nocturna)

- **ARCHIVO:LÍNEA**: `frontend/index.html:2546` (`computeMetrics(filtered, mFiltered, ...)`, con `mFiltered` que incluye
  las filas `dia: true`, `:2419-2423`), `computeMetrics` en `:1422-1542`. SCRIPT: `metricas_regla_sn.js` → `.out`.
- **QUÉ PASA**: la nota del gráfico dice «nuestra réplica es sólo nocturna» (`:2632`) y el perfil tiene el diurno
  apagado, pero el recall del panel usa la referencia con las alertas diurnas. Tampoco aplica la regla SN de D-9 (VIIRS 375
  de 0,05 MW o menos = MIROVA no vio nada). Chillán, 30 d por defecto: MODIS 11/17 → 11/14, **VIIRS 375 50/61 (0,82) →
  50/51 (0,98)**, VIIRS 750 37/43 → 37/40. Total 11 Tier A VIIRS 375: 0,859 (panel) → 0,910 sin diurnas → 0,946 con regla SN.
  Defecto previo a K; lo hace visible la erupción de Chillán, que trae 16 alertas diurnas en 30 d.
- **CÓMO SE VE EN EL DASHBOARD**: «Recall 0.82, TP=50 FN=11» en VIIRS 375 de Chillán: parece que la réplica pierde una de
  cada cinco alertas de MIROVA en plena erupción; pierde 1 de 51 nocturnas.
- **CÓMO REPRODUCIRLO**: `node experiments/_s155_audit/frente_2/metricas_regla_sn.js`.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 3.

## F2-06. Encabezados de `diario.html` (90 d por defecto) mezclan C0 y K sin decirlo

- **ARCHIVO:LÍNEA**: `frontend/diario.html:168` (90 d por defecto), `computeStats` `:674`.
  SCRIPT: `diario_stats.js` → `.out`.
- **QUÉ PASA**: «det. nuestras», «Max VRP» y «mediana» suman los dos detectores. Copahue **257** det. (K: **0**), Llaima
  229 (K: 0), Villarrica 255 (K: 4), Chaitén 299 (K: 10). Chillán en erupción: «mediana: 0,11 MW» como «nivel térmico
  típico», cuando la mediana de la ventana K es **2,53 MW**. Tupungatito «Max VRP 5,00 (tope)» viene de C0 (K: 0,19).
- **CÓMO SE VE EN EL DASHBOARD**: tarjetas de `diario.html`, fila de estadísticas.
- **CÓMO REPRODUCIRLO**: `node experiments/_s155_audit/frente_2/diario_stats.js`.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 3.

## F2-07. «MIROVA N · nuestras M (90 d)» de la tarjeta de index cuenta detecciones lejanas y de C0

- **ARCHIVO:LÍNEA**: `frontend/index.html:2177-2195` (`corroboracionMirova`: `nuestras` sólo exige `isValidDetection`, sin
  `isSummitDetection` ni el criterio de publicación). SCRIPT: `tarjetas_y_metricas.js` (`corrob90`, `nuestras90_*`).
- **QUÉ PASA**: Copahue dice «MIROVA 5 · nuestras 400 (90 d)»: de esas 400, 143 son lejanas (no se publican con «Solo
  cráter»), 391 son C0, y las publicadas son 257; con K, 0 en 30 días. Llaima «MIROVA 1 · nuestras 370» (141 lejanas,
  360 C0). El tooltip dice que es lo esperado porque registramos señal real bajo el umbral de MIROVA (A54); con K ese
  número ya no describe lo que hace el detector. La parte «cuenta lejanas» es previa a K; la mezcla es por K.
- **CÓMO SE VE EN EL DASHBOARD**: fila de corroboración de cada tarjeta Tier A.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 3.

## F2-08. 26 records MODIS Terra de C0 quedaron sin reprocesar dentro de la ventana K; 2 se publican en PCC

- **SCRIPT:SALIDA**: `modis_terra_sin_marca.py` → `.out`; `marcador_modis_eruption.out`.
- **QUÉ PASA**: 26 records MODIS_TERRA fechados 2026-09-28, 10-02 y 10-10 (11 volcanes) no tienen `regimen`, no tienen
  gemelo K en ±10 min y fueron procesados el mismo día de la pasada (`processed_utc` 2026-09-28T10:5x, 2026-10-10T04:4x):
  son C0 (banda 21) que el reproceso no reemplazó. Dos están publicados: PCC 2026-09-28 01:25 (0,852 MW, cúmulo a 0,6 km)
  y PCC 2026-10-10 01:05 (0,378 MW). Por qué el reproceso no los tocó y por qué los de octubre no traen marca de régimen:
  SOSPECHA (granos Terra NRT no encontrados por el reproceso; la marca no se escribió en ese camino).
- **CÓMO SE VE EN EL DASHBOARD**: invisible como C0; dos barras MODIS Terra de PCC en la serie K. Su marcador además cae a
  14 y 18 km del cúmulo publicado (F2-10).
- **CÓMO REPRODUCIRLO**: `python experiments/_s155_audit/frente_2/modis_terra_sin_marca.py`.
- **CONFIANZA**: CONFIRMADO (el origen, SOSPECHA). **GRAVEDAD**: 2.

## F2-09. En VIIRS 375 el número mostrado (núcleo F5') no es un recorte del cúmulo publicado: suele ser mayor y de otro fragmento

- **ARCHIVO:LÍNEA**: `frontend/index.html:1248-1293` y `:1295-1316` (igual en diario y mosaico); dato persistido
  `f5_core_vrp_mw`. SCRIPT: `magnitud_k.py` → `.out`; `caso_nucleo_mayor.py` → `.out`.
- **QUÉ PASA**: el comentario de las vistas dice que el núcleo «sólo reduce el halo». Con K el núcleo supera al cúmulo en
  **177 de 284** records VIIRS 375 publicados en el cráter (62 %; con C0 972 de 1.897, 51 %), y cuando lo supera la
  mediana es 1,17× (C0: 1,01×), 56 casos sobre 1,5×, máximo 14,3× (Isluga 2026-10-10 05:06). El núcleo suma alrededor del
  píxel más energético dentro del radio, aunque ese píxel sea de otro cúmulo: en Chillán 2026-10-18 06:48 el cúmulo
  publicado es el fragmento sur (4,08 MW, 5 px) y el núcleo suma el fragmento norte (píxel de 331 K) más los píxeles
  sobre 295 K del sur (8,93 MW). Cambia el nivel en 2 pasadas (Chillán 2026-10-10 06:30 y 10-15 05:00, Bajo → Moderado).
  No es inflado contra MIROVA (que publicó 12,2 y 22,1 MW por OCR en esas pasadas, F2-02): el defecto es de coherencia,
  el número y el marcador (centroide del cúmulo) hablan de objetos distintos.
- **CÓMO SE VE EN EL DASHBOARD**: tabla con «Píxeles 5 / 8» y VRP del núcleo; marcador sobre el fragmento sur; botón
  «Magnitud: Cluster» cambia el número a la mitad.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 2.

## F2-10. Con K, MODIS no es `ctx_cluster`: el arreglo del marcador (#853) no lo cubre y la tabla muestra otra distancia

- **ARCHIVO:LÍNEA**: `frontend/index.html:1620-1631` (`pixelesDelMarcador` desde `:1627`, comentario «con K (#850) todos los records son ctx_cluster»), tabla
  `:2734-2738`. SCRIPT: `marcador_vs_cumulo.py`, `marcador_modis_eruption.py` → `.out`.
- **QUÉ PASA**: los 349 publicados `ctx_cluster` de la ventana K tienen el marcador exactamente en el centroide del
  cúmulo (bien). Pero los 23 MODIS publicados son `final_hotspot_source = "eruption"`, así que el mapa dibuja
  `anomaly_pixels[0]` y la tabla toma `hotspot_dist_km` (el píxel más caliente medido desde el centro del volcán), no el
  cúmulo. En K: marcador a 2,27 km (Chillán 2026-10-15 07:35) y 2,16 km (10-17 08:50) del cúmulo publicado; distancia de
  la tabla PCC 2026-10-16 01:40 **7,09 km** con el cúmulo a 0,52 km, PCC 10-10 07:45 5,42 km contra 2,19, Villarrica
  10-11 01:45 1,16 contra 0,35. La tarjeta, en cambio, usa `pc.centroid_dist_km`: tarjeta y tabla discrepan para la misma
  pasada.
- **CÓMO SE VE EN EL DASHBOARD**: `index.html`, Chillán o PCC, fila MODIS en la tabla y su punto en el mapa.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 2.

## F2-11. Textos que suponen el Test 1 o describen otro detector

- **ARCHIVO:LÍNEA**: `frontend/index.html:2268-2270` («en el cráter (ancla)» si `dist < 0.05`, y tooltip «para
  detecciones por integral (Test 1) es el ancla del cráter»); `:542-552` (modal «Acerca de»: «Algoritmo operacional:
  Coppola 2016a literal ...» y paridad S119, recall VIIRS 375 98,4 %, sin mención de K, `max` ni banda 22).
  SCRIPT: `textos_test1_y_coherencia.out`.
- **QUÉ PASA**: con K hay 5 detecciones publicadas `ctx_cluster` a menos de 50 m que la tarjeta rotula «en el cráter
  (ancla)», cuando son una medición. El modal describe métricas medidas con un detector que ya no corre.
- **CÓMO SE VE EN EL DASHBOARD**: tarjeta (línea de distancia) y modal «ℹ️ Acerca de».
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 1.

## F2-12. Las vistas no leen `regimen.codigo_sha`: la frontera vive sólo en una constante escrita a mano

- **ARCHIVO:LÍNEA**: 0 apariciones de `codigo_sha` o `regimen` en las tres vistas (`grep -c`). `cambio_detector.js:16`.
- **QUÉ PASA**: el dato ya trae el régimen de cada record; el frontend no lo usa para marcar la frontera, separar series
  ni excluir C0 de bases como la de F2-04. Por eso F2-01 y F2-08 son invisibles.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 1 (es la raíz de F2-01, F2-04, F2-06 y F2-08; por sí solo no tuerce nada).

---

## VERIFICADO LIMPIO

Cada medición lleva en su cabecera las dos preguntas del instrumento, el denominador y la ventana.

1. **Las tres vistas publican lo mismo, record a record.** Valor graficado por index (detalle), diario y mosaico, con los
   valores por defecto (Núcleo F5', «Solo cráter»): **0 discrepancias** en las ventanas C0 y K
   (`node predicados_tres_vistas.js`), y 0 en toda la historia con el cruce `_mirova_confirmed` que sólo hace index
   (`node comparador_con_cruce.js`). Control positivo: diario en «Cluster» contra index en «Núcleo» da 267 diferencias
   en 3.687 records K (`node control_discrepancia.js`), así que el comparador sí ve.
2. **Tarjeta de index = tarjeta de mosaico.** `latestDetection` y `latestVRP` dan el mismo valor, hora y nivel en los 11 a
   las 12:00 UTC del 2026-10-19 (`tarjetas_y_metricas.out`).
3. **Con K no hay records que el gráfico muestre y la tarjeta descarte, ni al revés** (0 y 0; en C0, 2 de Villarrica
   MODIS con `cluster_too_large_for_volcano`). `node textos_test1_y_coherencia.js`.
4. **`triggered_test1` vale false en todos los records de la ventana K** (columna t1 de `predicados_tres_vistas.out`),
   y la rama `triggered_test1` de `isValidDetection`/`isSummitDetection` sólo actúa en records sin cúmulo o descartados:
   código muerto con K, sin efecto en lo publicado (punto 3).
5. **`f5_core_vrp_mw` viene persistido en el 100 % de los VIIRS 375 publicados con K** (284 de 284 en el cráter): el
   navegador no recalcula el núcleo. MODIS y VIIRS 750 muestran `pc.vrp_mw` (`magnitud_k.out`).
6. **Marcador del mapa (#853) para `ctx_cluster`**: 349 de 349 publicados K con el marcador sobre el centroide del cúmulo
   (`marcador_vs_cumulo.out`). El problema queda sólo en MODIS (F2-10).
7. **`inner_radius_km` de las tres vistas = `volcanoes.yaml`** en los 11 (`inner_radius_yaml_vs_frontend.py`).
8. **La tabla no rotula «cráter» ninguna fila K** (0 casos de ancla honesta con distancia 0 exacta).
9. **Chart.js se carga antes de `cambio_detector.js` en las tres vistas** (index l. 7 y 12, diario 7 y 10, mosaico 21 y 24),
   así que la línea y el aviso sí se registran; el problema es la fecha (F2-01), no el cableado.
10. **Filtros de artefacto térmico (cirrus y campo difuso)**: no ocultan ningún record con `mirovaEqVrp > 0` en toda la
    historia (0 de 25.202) ni en K (0 de 372) (`node artefactos_k.js`). Ojo: el control positivo falla (nunca disparan),
    así que esto no prueba que funcionen; sólo que hoy no esconden nada al operador.

Límites: no tuve navegador. Quedan para mirar en pantalla: `diario.html` Villarrica y Copahue con 90 d alrededor del
2026-09-18 (F2-01); pestaña «Distancia» de Lastarria y Chillán con 90 d (F2-03); tarjeta de Chillán (línea de percentil,
F2-04); `mosaico.html`, si el rótulo «detector K» se corta en el borde derecho de las miniaturas (SOSPECHA).
