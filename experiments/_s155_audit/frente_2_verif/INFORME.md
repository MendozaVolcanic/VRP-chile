# Verificador con contexto limpio, frente 2 (lo que ve el operador)

Worktree `D:\vrp-trabajo\worktrees\s155-audit-f2`, detached en `cb90031a` (origin/main, último NRT 2026-10-19 10:27 UTC).
No leí `experiments/_s155_audit/frente_2/`. Todas las vistas se evaluaron con su código LITERAL cargado en node
(`harness.js`: concatena los `<script>` inline de la vista más `periodo.js` y `cambio_detector.js` en un contexto vm
con un DOM de juguete, y exporta las funciones; no reconstruye ninguna). "Ahora" fijado en 2026-10-19T12:00:00Z.
La única función que no se pudo exportar (`buildDistanceData`, anidada en `renderDetail`) se extrajo como texto del
HTML y se evaluó tal cual. Ventanas: 90 d de diario = 2026-07-21 a 2026-10-19; 30 d de index = desde 2026-09-19.
"K" = record con `regimen.codigo_sha` descendiente de 34cea39e (`git merge-base --is-ancestor`).

Salida cruda de cada medición: el `.out` del mismo nombre en esta carpeta.

## Censo de régimen (base de F2-01, F2-08, F2-12)

`censo_regimen.py` -> `censo_regimen.out`.
- P1: si la marca estuviera rota (todo K o todo C0) lo vería, porque cuento por sha y por ancestría. P2: un record
  sin `regimen` se cuenta como SIN_MARCA, no como C0. Control positivo: 34cea39e da K y su padre da C0.
- Resultado (11 Tier A, corpus completo): **ningún record lleva un sha anterior a K**. Los records C0 no tienen campo
  `regimen` (SIN_MARCA). Desde 2026-09-18 todos son K salvo 26 SIN_MARCA; el primer día con K es 2026-09-18 en los
  11 volcanes. Los 26 son MODIS_TERRA NRT, de 2026-09-28, 10-02 y 10-10.
- Nota: `experiments/_s154_reproc_k/ventana_30d.json` (en `origin/loop/activo`, no en main) declara `sin_k: 56`; hoy
  quedan 26. No averigüé por qué bajó (SIN VERIFICAR); no afecta las conclusiones.

## Veredictos

| ID | Veredicto | Grav. | Evidencia |
|---|---|---|---|
| F2-01 | CONFIRMADO | 4 | `f201_diario_barras.out`, `censo_regimen.out` |
| F2-02 | CONFIRMADO (cifras levemente distintas) | 4 | `f202_chillan.out`, `f202_dt.out`, `f202_cenit.out`, `f202_otros_volcanes.out`, `f202_c0_comparacion.out` |
| F2-03 | CONFIRMADO | 3 | `f203_distancia.out`, `f203_ceros.out` |
| F2-04 | CONFIRMADO en el mecanismo, PARCIAL en "casi toda C0" | 2 | `f204_207_tarjeta.out` |
| F2-05 | CONFIRMADO | 2 | `f205_metricas.out` |
| F2-06 | CONFIRMADO | 2 | `f206_diario_encabezado.out` |
| F2-07 | CONFIRMADO | 3 | `f204_207_tarjeta.out` |
| F2-08 | CONFIRMADO | 2 | `f208_terra_c0.out` |
| F2-09 | PARCIAL | 1 | `f209_nucleo.out`, `f209_mirova_en_los_2.out` |
| F2-10 | CONFIRMADO | 2 | `f210_marcador.out` |
| F2-11 | CONFIRMADO | 1 | `f211_ancla.out`, `frontend/index.html:2268`, `:542` |
| F2-12 | CONFIRMADO | 2 | grep vacío de `regimen` y `codigo_sha` en las 3 vistas y los 2 .js |

### F2-01. La marca del detector está un mes después del escalón de los datos
- `frontend/cambio_detector.js:16` fija `CAMBIO_DETECTOR_UTC = "2026-10-18T09:57:30Z"`; el aviso (l. 40-41) dice
  "Desde el 18 oct ... la réplica usa el detector K ... Las comparaciones que crucen esa fecha mezclan dos detectores".
  Los datos dicen otra cosa: todo record observado desde 2026-09-18 es K (censo). La línea vertical y el aviso
  señalan la frontera equivocada, y en la vista de 30 d de index (todo K salvo 26 Terra) afirman una mezcla que no hay.
- Días con barra en diario (90 d), formato antes del 18-sep | 18-sep a 17-oct | desde 18-oct: VIIRS 375 Copahue
  56|0|0, Llaima 52|0|0, Villarrica 53|2|0, Chaitén 55|3|1, Lastarria 42|16|0, Chillán 39|18|1. Días con algún record
  procesado: 58|30|2 en los 11, así que el vacío no es falta de datos (descarta "días sin datos").
- Caminos descartados: régimen mal separado (censo por sha), reloj (parseUtcMs literal, ventana 90 d literal),
  días sin datos (contados aparte). La cifra de Chaitén depende de la hora "ahora" (3 o 4).
- Dashboard: en diario la actividad de Copahue y Llaima "se apaga" el 18-sep sin marca ese día; la marca está el
  18-oct. Gravedad 4: el texto oficial de la vista orienta mal la lectura de la serie.

### F2-02. Chillán en erupción se muestra un nivel por debajo de MIROVA
- Emparejamiento literal de `computeMetrics` (mismo sensor, ±60 min) desde 2026-09-18: 98 pares; los 98 caen en el
  mismo minuto (dt máximo 0 min), sin filas de MIROVA duplicadas. Razón mediana mostrada/MIROVA: VIIRS 375 0,573,
  VIIRS 750 0,418, MODIS 0,240 (el auditor dijo 0,48 en 750 y 23 de 101; la diferencia es de ventana u hora). De 38
  pasadas que MIROVA rotula Moderado, el tablero muestra Bajo o Muy Bajo en **24**. Nivel menor en 37 pares, mayor en 0.
- No es propio de K ni de Chillán: VIIRS 375 en Láscar da 0,465 con K y 0,562 con C0 (junio a septiembre); Isluga
  0,462 y 0,606. Depende fuerte del cenit en Chillán: cenit < 25° da 0,75 a 0,85; cenit ≥ 45° da 0,19 (750) y 0,51
  (375). Coherente con la lectura vigente de S154 (magnitud cae con el cenit, SIN ATRIBUIR); no atribuyo causa.
- Dashboard: tarjeta y tabla con insignia Bajo donde MIROVA dice Moderado. La línea de MIROVA sí se dibuja en el
  mismo gráfico, lo que atenúa. Gravedad 4 (erupción en curso, sesgo siempre hacia abajo).

### F2-03. El gráfico "Distancia" salta en la frontera
- `buildDistanceData` literal. Fracción de puntos en 0,0 km, C0 (90 d) contra K: Copahue 87 %, Llaima 81 %, PP 77 %,
  Villarrica 74 %, Tupungatito 63 %, Chillán 62 %, Lastarria 57 %, Chaitén 54 %, Isluga 35 %, Láscar 24 %, PCC 17 %;
  con K, 0 % en todos. Los 750 ceros C0 de 4 volcanes son todos `test1_roi` (`f203_ceros.out`), o sea 0 por
  construcción. Mediana Lastarria 0,00 a 1,31 km, Chillán 0,00 a 0,67 km.
- Dashboard: en la pestaña "Distancia" del detalle de index la nube de puntos "se despega del cráter" el 18-sep. El
  propio tablero enseña a leer así una distancia que crece: el tooltip de "MIROVA dist" en diario dice que eso
  "señala posible actividad de flanco" (se refiere a la distancia de MIROVA, no a la nuestra, pero es la lectura que
  el operador trae). Gravedad 3.

### F2-04. Anomalía relativa con base mezclada
- `anomaliaRelativa` literal, Chillán: p93 · 110,6× (n 273, mediana 0,081 MW); con la misma función sobre sólo K:
  p82 · 3,4× (n 104, mediana 2,655). Planchón-Peteroa p83 3,7× contra p72 1,6×.
- PARCIAL: en Chillán la base es 62 % C0, no "casi toda"; en los demás sí (85 a 90 %). Parte del 110× es real (la base
  incluye el volcán tranquilo antes de la erupción), así que el sesgo exagera una alarma que existe; no la crea ni
  la apaga. Gravedad 2.

### F2-05. El panel de métricas cuenta diurnas como FN
- `computeMetrics` literal, ventana por defecto 30 d (`DIAS_POR_DEFECTO = 30`): Chillán VIIRS 375 0,82 (tp 50, fn 11);
  sin las 16 diurnas 0,98 (fn 1); sin diurnas y sin mínimas ≤ 0,05 MW 1,00. VIIRS 750 0,86 a 0,93; MODIS 0,65 a 0,79.
  La regla SN la apliqué por fila (aproximación de `aplicar_regla_minimas`, que agrupa por pasada).
- Subestima el recall propio; no tuerce una decisión de alerta. Gravedad 2.

### F2-06. Encabezados de diario mezclan detectores
- `computeStats` literal (90 d) contra la misma función sobre sólo K: Copahue 257 det. a 0, Llaima 229 a 0,
  Villarrica 255 a 4; Chillán mediana 0,105 a 2,525 MW. Gravedad 2 (la mediana de Chillán mezcla además antes y
  durante la erupción, que es real).

### F2-07. La corroboración de la tarjeta cuenta lejanas y C0
- `corroboracionMirova` literal (90 d): Copahue "MIROVA 5 · nuestras 400"; de las 400, 143 lejanas y 390 C0; con K y
  en la cumbre publica 0. La cuenta de lejanas es permanente (no se arregla sola con el tiempo), la de C0 caduca a
  mediados de diciembre. El tooltip dice que un número nuestro mayor "es lo esperado". Gravedad 3.

### F2-08. 26 MODIS Terra C0 sin marca dentro de la ventana K
- Los 26 SIN_MARCA del censo; con el predicado literal de index se publican 2, ambos en PCC: 2026-09-28 01:25
  (0,852 MW) y 2026-10-10 01:05 (0,378 MW). Gravedad 2.

### F2-09. Núcleo F5' contra cúmulo
- PARCIAL: con K, 284 VIIRS 375 publicados; núcleo > cúmulo en **157** (no 177), < en 74, igual en 53. Como la suma
  de `anomaly_pixels` iguala a `vrp_mw` en 273 de 284 (control de aditividad), núcleo > cúmulo implica que el núcleo
  suma píxeles de fuera del cúmulo. Cambia el nivel en 2 casos, los dos en Chillán y los dos de Bajo a **Moderado**,
  que es lo que MIROVA publicó en esas pasadas (12,17 y 22,13 MW). Ahí acerca, no aleja. Gravedad 1.

### F2-10. MODIS con fuente `eruption`, fuera del arreglo de #853
- Con K, los publicados son 349 VIIRS `ctx_cluster` y 21 MODIS `eruption`. En 4 de los 21 el marcador
  (`pixelesDelMarcador` literal) cae a más de 1 km del centroide del cúmulo, máximo 2,27 km (Chillán 2026-10-15
  07:35). PCC 2026-10-16 01:40: la tabla dice 7,09 km (`hotspot_dist_km`) y el cúmulo está a 0,521 km. Gravedad 2.

### F2-11. Textos obsoletos
- `frontend/index.html:2268` escribe "en el cráter (ancla)" si la distancia es < 0,05 km; con K eso pasa en 5
  records de cumbre `ctx_cluster` (4 Láscar, 1 Tupungatito), que no son ancla. `frontend/index.html:542` titula
  "Métricas de desempeño (S119 ...)". Gravedad 1.

### F2-12. Las vistas no leen la marca de régimen
- grep de `regimen|codigo_sha` en `frontend/index.html`, `diario.html`, `mosaico.html`, `cambio_detector.js`,
  `periodo.js`: 0 coincidencias. Es la causa de F2-01: la fecha se escribió a mano en vez de salir del dato.
  Gravedad 2.

## Hallazgos propios

### V2-01. Una alerta protegida de MIROVA en Copahue queda oculta como "lejana"
- SCRIPT `v201_protegidas.js` -> `v201_protegidas.out`. Alertas nocturnas de MIROVA ≥ 1 MW desde 2026-09-18: 94; el
  tablero publica algo en la misma pasada en 90. De las 4 sin publicar, 3 no tienen cúmulo nuestro (Chillán MODIS
  2026-10-12 07:20 y 2026-10-15 01:05, Chaitén VIIRS 750 2026-10-11 04:36: pérdida de detección). La cuarta,
  **Copahue 2026-10-16 06:18 VIIRS 375, MIROVA 1,34 MW (OCR, SIN_GEOMETRIA)**: el pipeline sí la detecta,
  VIIRS_SNPP, un píxel de 307,4 K sobre fondo de 270,5 K, 1,238 MW, a 6,475 km al oeste del cráter (-37,858,
  -71,257); `inner_radius_km` de Copahue es 4, así que queda `far` y el tablero la oculta.
- Fenómeno: un foco caliente real fuera del radio interno del cráter que MIROVA publicó con casi la misma magnitud.
- Dashboard: invisible con "Solo cráter" (por defecto). Visible con "Incluir lejanas".
- Reproducir: `node experiments/_s155_audit/frente_2_verif/v201_protegidas.js`; volcán Copahue, 2026-10-16 06:18 UTC.
- CONFIANZA: CONFIRMADO que se oculta; SOSPECHA que sea el mismo objeto que MIROVA (la imagen de MIROVA era de otra
  pasada, su distancia es desconocida; la coincidencia de magnitud, 1,34 contra 1,24, es el único indicio).
- GRAVEDAD 3 (el criterio de victoria dice que ninguna protegida se pierde).

## VERIFICADO LIMPIO
- Sin records repetidos: ninguna clave (hora|sensor) se repite en los 11 archivos (`f208_terra_c0.js`, no imprime
  duplicados).
- Sin filas de MIROVA repetidas en Chillán desde 2026-09-18 (`f202_chillan.out`, "duplicadas: 0").
- Emparejamiento con MIROVA de Chillán: los 98 pares en el mismo minuto (`f202_dt.out`).
- Cobertura: todos los días de la ventana de 90 d tienen records procesados en los 11 (`f201_diario_barras.out`,
  58|30|2).
- Régimen: ningún record con sha anterior a K; marca presente en todo record desde 2026-09-18 salvo los 26 Terra
  (`censo_regimen.out`).
- `computeMetrics` literal coincide con mi emparejamiento en TP por sensor (50/37/11, `f202_chillan.out`).
- Fuentes del marcador con K: sólo `ctx_cluster` (VIIRS) y `eruption` (MODIS); ningún `test1_roi` con K
  (`f210_marcador.out`, `f203_distancia.out`).
