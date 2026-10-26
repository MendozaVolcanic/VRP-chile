# RA1 (S158, segunda ronda): la magnitud de VIIRS 750 y su fondo

Auditor independiente, 2026-10-21. Worktree `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s158-audit-r2-0eeee2`, rama `claude/s158-audit-r2-0eeee2`, HEAD `e81bfadd5`. No se leyó ningún informe de la primera ronda ni el oráculo de `experiments/_s158_oraculo_mirova/` (la carpeta `experiments/_s158_audit_r2/oraculo/` estaba vacía cuando la necesité, así que el port del `.m` es propio: `port_mirova_v750.py`). Todos los scripts y salidas crudas están en `experiments/_s158_audit_r2/ra1/`.

Vara: los dos `.m` de MIROVA leídos línea a línea (`MIROVA_VIIRS750_VRP.m`, `MIROVA_VIIRS750_hotspot_detection.m`). Flags efectivos leídos de `pipeline.profile` con `VRP_PROFILE=mirova_equivalent` (volcado en `flags_efectivos_mirova_equivalent.txt`). Convención de sensores comprobada con `Counter` (A48): `VIIRS_*_750` son 29.743 records de 74.811; `VIIRS_SNPP/NOAA20/NOAA21` sin sufijo 29.985; `MODIS_*` 15.083 (`extraer_records_v750.txt`).

## Resumen de veredictos

| Afirmación | Veredicto | Evidencia principal |
|---|---|---|
| 1. El fondo del VRP de VIIRS 750 de producción es un escalar del anillo de 5 a 25 km con recorte a cero, y con los mismos píxeles de Etna da otra magnitud que el código de MIROVA | **CONFIRMADA** | `fondo_produccion_etna.txt`: con los 5 píxeles que reproducen `Tot_Lmir_hot` del OSF a 9 cifras, producción da **2,75 MW** contra **9,89 MW** del OSF y 9,81 del port (razón 0,278), y recorta a cero 1 de los 5 píxeles |
| 2. Ese fondo deja en 0 MW cúmulos de cumbre de VIIRS 750 que el tablero oculta | **CONFIRMADA** | `contar_ceros_v750.txt`: 595 de 2.359 cúmulos de cumbre (25,2 %) quedan en 0,0 MW; los 595 están ocultos por el predicado real del tablero (node); 96 son alertas de MIROVA y 11 son protegidas (1 MW o más), entre ellas Chillán 2026-10-01 04:42 con 9,0 MW en MIROVA |

La causa del cero es el recorte en los 595 casos (`ceros_caracterizar.txt`): el píxel del cúmulo está entre 0,6 y 2,7 K más frío que la mediana del anillo (cuartiles de `bt - t_bg`: -2,66 / -1,55 / -0,59 K; 0 de 587 por encima). No apareció otra causa.

## Afirmación 1: el fondo de producción y el de MIROVA sobre la misma pasada de Etna

### Qué hace MIROVA (código, no comentario)

`MIROVA_VIIRS750_VRP.m` l. 63 a 85: pone en NaN los píxeles alertados, dilata esa máscara con un cuadrado de 3, 5 o 7 según `npix` (l. 68 a 78), reconstruye el fondo de M13 bajo el hueco con `fillmissing2(...,'linear')` (l. 81), y resta la suma del fondo interpolado bajo los alertados a la suma de la radiancia observada (l. 83 a 85). **No hay recorte**: `deltaL_MIR` es la diferencia tal cual, y `npix = numel(alert)` (l. 61) suma todos los alertados. Coeficiente `1.97e7 x 0.5625` (l. 88 a 91).

Comprobación del rótulo de los ROI, que el prompt pedía no creer: en la matriz de ejemplo `BOX==2` son 49 píxeles (filas y columnas 30 a 36, un cuadro de 7 x 7 = 5,25 km centrado en el volcán) y `BOX==1` son 350 píxeles (filas 22 a 42, columnas 24 a 42) que lo rodean (salida en la sesión, script inline; se reproduce con `scipy.io.loadmat`). El `.m` aplica a `BOX==2` los umbrales sensibles de noche (5 sigma, pisos 0,003: l. 181 a 187 y 397 a 399) y a `BOX==1` los conservadores (10 sigma, 0,02 y 0,01). O sea que el cuadro chico del centro, el ROI 1 del paper, es el que el código llama ROI 2, y el comentario de las l. 111 a 118 lo rotula al revés. Los 5 píxeles de Etna salen todos de `BOX==2` (`port_mirova_v750_etna.txt`: `pass1_roi2` 4 píxeles, `pass2_roi2` 1).

### El port reproduce el OSF

`port_mirova_v750.py` (desde cero, equivalencias MATLAB a numpy declaradas en su docstring) sobre `VIIRS750_example.mat` (`20231390054-VJ1-19-May-2023`): ángulo de glint 113,1°, 0 píxeles sobre K1, 5 alertados en (fila, col) 0-based (35,32) (36,32) (35,33) (35,34) (36,33), sin duplicados. Fila del OSF v2.5 id 123853 (`VRP_GLOBAL_ARCHIVE_2025.csv`, grep en la sesión): `19/05/2023 00:54, Etna, Satellite 4, Resolution 750, Npix 5, Tot_Lmir_hot 1.96534218, Tot_Lmir_bk 1.072886152, VRP 9889528.362 W`.

| magnitud | port propio | OSF v2.5 | diferencia |
|---|---|---|---|
| Npix | 5 | 5 | 0 |
| Tot_Lmir_hot | 1,965342180 | 1,965342180 | 0 a 9 cifras |
| Tot_Lmir_bk | 1,080444 (griddata lineal) / **1,073662** (misma triangulación, diagonal opuesta) | 1,072886 | +0,70 % / **+0,07 %** |
| VRP | 9,806 / **9,881** MW | 9,890 MW | -0,85 % / **-0,09 %** |

(`port_mirova_v750_etna.txt`, `fillmissing_sensibilidad.txt`.) La detección queda confirmada a 9 cifras; el fondo depende de la diagonal que la triangulación de Delaunay elige en una grilla regular, y con la orientación transpuesta el port cae a 0,07 % del OSF. Cúbico, vecino más cercano y bilineal separable se alejan 6 a 10 %, así que el `fillmissing2` de MATLAB es la interpolación lineal por triángulos y no otra.

### Qué hace producción (archivo:línea, flags efectivos)

- Anillo: `pipeline/process_viirs_mod.py:539` `bg_mask = (dist >= BG_INNER_KM) & (dist <= BG_OUTER_KM)` con `BG_INNER_KM = 5.0`, `BG_OUTER_KM = 25.0`; `dist` es haversine desde `volcano_lat/lon` (l. 515).
- Escalar: `t_bg` es la **mediana de la BT M13** del anillo (`compute_bg_stats`, `pipeline/detection_context.py:1083`, llamada en `process_viirs_mod.py:560-567` con `enable_test1_k1_bg_exclude = False`, así que no retira los píxeles calientes del anillo). `L_bg_rad = Planck(t_bg)` escalar en `process_viirs_mod.py:1041`.
- Fondo por vecinos (D25): `ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750 = False` (`flags_efectivos_mirova_equivalent.txt`), así que el bloque de l. 1047 a 1052 no corre.
- **Recorte**: `process_viirs_mod.py:1056` `delta_L = np.maximum(L_hot - L_bg_rad, 0.0)` por píxel, antes de sumar (l. 1057 a 1058) y antes de armar el cúmulo (l. 1093 a 1100: `cluster_hotspots` suma los `per_pixel_vrp_mw` ya recortados).
- Área y coeficiente: `NADIR_PIXEL_AREA_M2 = 562500` con `ENABLE_NADIR_FIXED_PIXEL_AREA_VIIRS = True` (`scan_geometry.resolve_viirs_pixel_areas`, l. 319), `WOOSTER_COEFF = 19.7` (l. 66): k = 11.081.250, idéntico al `1.97e7 x 0.5625` del `.m`.
- Después del cúmulo: `apply_single_pixel_mode` (l. 1125 a 1130; `pipeline/single_pixel_mode.py:94-133`) con `ENABLE_SINGLE_PIXEL_SUB_MW_MODE = True`, umbral 5 MW, máximo 3 píxeles: si el cúmulo pesa menos de 5 MW y tiene 3 píxeles o menos, publica el **máximo por píxel, no la suma** (ver hallazgo 2).
- Caminos muertos en producción para V750: `ENABLE_TEST1_PATH = False` y ningún record V750 tiene `final_hotspot_source == "test1"` (`Counter`: `ctx_cluster` 2.733, `eruption` 208, `vent` 26, `None` 26.776), así que los bloques de l. 1263 a 1314 no deciden; `MIN_VRP_MW_VIIRS750 = 0.0` (el piso de `store.py:129-137` es inerte); el tope de sanidad de 50.000 MW (`store.py:159-184`) no aparece en ningún cero (categoría `sanity_cap` = 0 en `contar_ceros_v750.txt`).

### Los dos fondos sobre los mismos 5 píxeles de Etna

Fenómeno: Etna tiene 3.300 m y en mayo su cima está más fría que las laderas bajas y el mar que llenan el anillo de 5 a 25 km. La mediana de ese anillo (280,55 K, 3.359 píxeles válidos de 3.368) está **más caliente** que el entorno inmediato del cráter (media de los vecinos 3 x 3 no alertados: 0,199 a 0,227 W m-2 sr-1 um-1, contra 0,346 del anillo). MIROVA interpola el fondo desde la corona local del hueco y ve el exceso completo; producción resta un fondo regional más caliente y se come la mayor parte del exceso.

| píxel (fila,col) | L_hot | fondo .m | dL .m | fondo producción | dL producción |
|---|---|---|---|---|---|
| (35,32) | 0,353470 | 0,220305 | +0,133 | 0,346144 | +0,0073 |
| (36,32) | 0,347472 | 0,220423 | +0,127 | 0,346144 | +0,0013 |
| (35,33) | 0,569708 | 0,210616 | +0,359 | 0,346144 | +0,2236 |
| (35,34) | 0,361932 | 0,218365 | +0,144 | 0,346144 | +0,0158 |
| (36,33) | 0,332761 | 0,210734 | +0,122 | 0,346144 | **-0,0134, recortado a 0** |

Suma del fondo: `.m` 1,0804 (OSF 1,0729), producción 1,7307. `deltaL`: 0,885 (OSF 0,892) contra 0,248. **VRP: 9,81 MW (OSF 9,89) contra 2,75 MW** (razón producción / OSF 0,278). Con 5 píxeles y 2,75 MW el `single_pixel_mode` no actúa (`modo=False`). Control positivo del instrumento: con el fondo por vecinos D25 (flag apagado) la misma función de producción da 10,15 MW, así que el script distingue fondos y el 2,75 no es un artefacto de cómo llamé a la función (`fondo_produccion_etna.txt`).

Qué no se pudo reproducir y cómo se aproximó: la matriz ya está remuestreada a 750 m y producción trabaja sobre el gránulo nativo (`ENABLE_UTM_REGRID = False`), así que el anillo se armó como (píxeles al centro) x 0,75 km con centro en (33,33), que es el centro de `BOX==2`; producción parte de BT (LUT del L1B) y la matriz trae radiancia, así que se invirtió Planck con las constantes del pipeline (`C1 = 119104200`, `C2 = 14388`, 4,05 um, igual que `process_viirs_mod.py:266`) y la ida y vuelta es identidad (máx 1,8e-15), de modo que el fondo de producción es exactamente la mediana de la radiancia del anillo (comprobado: 0,346144 en los dos caminos). Área y coeficiente no necesitan aproximación. `compute_bg_stats` y `bt_to_spectral_radiance` se importaron de producción sin reimplementar.

**Veredicto 1: CONFIRMADA.** Escalar del anillo de 5 a 25 km (mediana de BT), recorte a cero por píxel en `process_viirs_mod.py:1056`, y sobre los mismos píxeles de Etna da 0,28 veces el VRP del OSF y del `.m`.

## Afirmación 2: cúmulos de cumbre en 0 MW ocultos por el tablero

Instrumento: `extraer_records_v750.py` (saca los 2.733 records V750 con `primary_cluster`), `predicado_tablero.js` (extrae `mirovaEqVrp` de `frontend/index.html:1162` e `isValidDetection` de `:1595` por texto y las ejecuta con node; control positivo: cúmulo sintético de 0,5 MW a 1 km da `eq=0.5, valid=true` y el de 0 MW da `eq=0, valid=false`), `contar_ceros_v750.py` (cuenta y cruza). "Cúmulo de cumbre" = `primary_cluster.centroid_dist_km <= inner_radius_km` del volcán (`volcanoes.yaml`; comprobé que coincide con la tabla `VOLCANOES` de `index.html` para los volcanes con records). Régimen por fecha de observación: `pre-K` antes del 2026-09-18, `K` desde esa observación. Ventana total de observación: 2025-02-15 a 2026-10-21 (los avisos A119 de esa ventana están impresos al inicio de `contar_ceros_v750.txt`; el cruce que decide se informa también desde el 2026-03-01).

| régimen | cúmulos de cumbre | en 0,0 MW | ocultos por el tablero | MIROVA miró (fila VIIRS a 60 min) | alerta de MIROVA | protegida (1 MW o más) |
|---|---|---|---|---|---|---|
| pre-K (2025-02-15 a 2026-09-17) | 2.262 | 565 (25,0 %) | 565 de 565 | 239 | 86 | 10 |
| K (2026-09-18 a 2026-10-21) | 97 | 30 (30,9 %) | 30 de 30 | 29 | 10 | 1 |
| control pre-K: cumbre con magnitud > 0 | 1.697 | 0 | 0 de 1.697 (visibles 1.697) | 514 | 344 | 199 |
| control K: cumbre con magnitud > 0 | 67 | 0 | 0 de 67 (visibles 67) | 65 | 48 | 39 |

El predicado del tablero oculta exactamente los ceros y muestra exactamente los no ceros: `isValidDetection` exige `primary_cluster.vrp_mw > 0` (`index.html:1603`) y `mirovaEqVrp` devuelve `pc.vrp_mw` (`:1181`). Los 595 ceros tienen `distance_class = summit` y `single_pixel_mode = True` (587 de 1 píxel, 8 de 2).

Por volcán (ceros de cumbre, todos los regímenes): Tupungatito 202, Isluga 193, Láscar 95, PCC 55, Planchón Peteroa 35, Villarrica 6, Lastarria 4, Chaitén 2, Chillán 3. Entre los volcanes con más ceros están los más altos (Tupungatito 5.600 m, Isluga 5.550 m, Láscar 5.600 m): la cima nevada de noche está más fría que el anillo regional de 5 a 25 km, que es valle o altiplano más bajo.

Cruce con MIROVA, VIIRS 750 (`Sensor == "VIIRS"` del scraper, la misma convención que `index.html:1419`), mismo volcán, 60 min:
- Alertas de MIROVA pareadas a un cúmulo de cumbre nuestro: 488; **96 quedan en 0 MW (19,7 %)**. Protegidas: 249, **11 en 0 (4,4 %)**. Desde el 2026-03-01 (tabla sana, A119): 419 alertas, 84 en 0 (20,0 %); protegidas 9 de 216.
- Por noche (volcán, día UTC) con cúmulo de cumbre V750 y alerta V750 de MIROVA: 266 noches; en **55** no queda ningún V750 visible en el tablero.
- Las 11 protegidas en 0 (`contar_ceros_v750.txt`, lista completa de las 96): Chillán 2026-10-01 04:42 NOAA-20 (MIROVA 9,0 MW; régimen K; `t_bg` 257,35 K, píxel del cúmulo 255,15 K, cenit 67,96°, `inspeccion_casos.txt`), Láscar 2026-03-08 05:00 (3,33), 2026-03-03 04:54 (3,07), 2026-02-21 05:12 (2,39), 2026-04-28 04:54 (2,38), 2026-01-14 05:24 (1,21), 2026-06-07 04:54 (1,18), 2026-05-08 05:12 (1,11), PCC 2026-07-06 05:12 (1,02), 2026-07-03 05:12 y 06:06 (1,00).

### La causa del cero: recorte, no otra

`contar_ceros_v750.txt`, "causa del cero": en 594 de 595 todos los píxeles publicados están en o bajo `t_bg_k`; el restante (Láscar 2026-05-28 05:36) tiene un píxel caliente a 20 km en `anomaly_pixels[0]` y el píxel del cúmulo a 263,50 K = `t_bg` exacto (`inspeccion_casos.txt`). `ceros_caracterizar.txt`, tomando el píxel del cúmulo por su centroide: `bt - t_bg` cuartiles -2,66 / -1,55 / -0,59 K, **0 de 587 por encima**; en los no ceros, +1,69 / +3,42 / +7,51 K. Ni `sanity_cap` ni `d9_capped` aparecen en los ceros.

Por qué `t_max_k` engaña acá: en los 595 ceros `t_max_k` supera a `t_bg` en 12,7 K de mediana, pero `diag_t_max_dist_km` está a 23 a 27 km (cuartiles 23,12 / 26,16 / 26,96; 0 % a 5 km o menos), o sea que es el píxel más caliente de la escena, no el cráter. El pixel del cráter que el detector marca por contraste de NTI está más frío que el valle: la lava sub-píxel brilla en MIR relativo a TIR (NTI) pero no alcanza a subir la BT absoluta de un píxel de 750 m por encima de la mediana regional.

**Veredicto 2: CONFIRMADA.** 595 de 2.359 cúmulos de cumbre V750 en 0,0 MW, los 595 ocultos por el predicado real del tablero, 96 con alerta de MIROVA, 11 protegidas; la causa es el recorte del fondo escalar en los 595.

## Hallazgos (lo peor primero)

### H1. El fondo escalar del anillo de 5 a 25 km esconde del tablero 1 de cada 5 alertas VIIRS 750 de MIROVA, incluida una de 9 MW

- ARCHIVO:LÍNEA: `pipeline/process_viirs_mod.py:539` (anillo), `pipeline/detection_context.py:1083` (mediana), `process_viirs_mod.py:1041` (escalar), `:1056` (recorte); `frontend/index.html:1603` (oculta `pc.vrp_mw == 0`). SCRIPT:SALIDA: `contar_ceros_v750.py` → `contar_ceros_v750.txt`; `ceros_caracterizar.py` → `ceros_caracterizar.txt`.
- QUÉ PASA: de noche la cima de un volcán alto está más fría que el anillo regional de 5 a 25 km (valle, altiplano); la mediana de ese anillo queda por encima de la BT del píxel del cráter aunque éste lleve lava sub-píxel (el detector lo marca por NTI, no por BT absoluta). Producción resta ese fondo caliente y recorta a 0,0 MW en `:1056`; MIROVA interpola el fondo desde la corona local del hueco y no recorta (`MIROVA_VIIRS750_VRP.m:81-85`).
- CÓMO SE VE EN EL DASHBOARD: el record no cuenta como detección (`isValidDetection = false`), la magnitud es 0 y el cúmulo desaparece de contador, pastillas y gráfico. 595 de 2.359 cúmulos de cumbre V750 (25,2 %); 96 alertas de MIROVA V750 (19,7 % de las 488 pareadas), 11 protegidas (4,4 % de 249); 55 de 266 noches con alerta V750 de MIROVA sin ningún V750 visible.
- CÓMO REPRODUCIRLO: `python experiments/_s158_audit_r2/ra1/extraer_records_v750.py && node experiments/_s158_audit_r2/ra1/predicado_tablero.js && python experiments/_s158_audit_r2/ra1/contar_ceros_v750.py`. Caso: Nevados de Chillán, VIIRS_NOAA20_750, 2026-10-01 04:42 UTC, `pc.vrp_mw = 0.0`, píxel 255,15 K contra `t_bg` 257,35 K, MIROVA 9,0 MW. Caso Láscar: 2026-03-08 05:00 UTC NOAA-21, píxel 265,77 K contra 266,74 K, MIROVA 3,33 MW.
- CONFIANZA: CONFIRMADO (código leído, conteo propio, predicado ejecutado con node).
- GRAVEDAD: 5. Una alerta de 9 MW de MIROVA en Chillán, en erupción, con el detector K en producción, aparece en nuestro tablero como "sin detección".

### H2. Cuando no recorta, el mismo fondo deja la magnitud V750 en la mitad de la de MIROVA

- SCRIPT:SALIDA: `ceros_caracterizar.py` → `ceros_caracterizar.txt` ("CONTROL razon"); `spm_razon.py` → `spm_razon.txt`.
- QUÉ PASA: el fondo regional es más caliente que el local también cuando no alcanza a recortar, así que el exceso que queda es menor que el de MIROVA. Sobre 392 alertas V750 de MIROVA pareadas a cúmulos de cumbre con magnitud > 0 (ventana 2025-02-15 a 2026-10-21), `pc.vrp_mw / VRP_MIROVA` tiene cuartiles 0,236 / **0,461** / 0,716 (pre-K n = 344: 0,471; K n = 48: 0,385). En Etna la razón fue 0,278 con los mismos píxeles, así que no es pérdida de detección sino de fondo. Para cúmulos de 1 píxel (donde el `single_pixel_mode` no cambia nada) la mediana es 0,465 (n = 296): el déficit es del fondo, no del modo de un píxel.
- CÓMO SE VE EN EL DASHBOARD: toda magnitud VIIRS 750 de cumbre se lee a la mitad de lo que MIROVA publica para la misma pasada; un cambio real de 2x en el volcán queda al nivel de la dispersión entre sensores.
- CÓMO REPRODUCIRLO: `python experiments/_s158_audit_r2/ra1/ceros_caracterizar.py` tras H1.
- CONFIANZA: CONFIRMADO (medido). Que la causa sea sólo el fondo y no también la selección de píxeles es CON MATIZ: Etna lo aísla (mismos píxeles, razón 0,28), los pares chilenos no (MIROVA puede sumar más píxeles que nosotros).
- GRAVEDAD: 3.

### H3. `single_pixel_mode` publica el máximo por píxel en cúmulos de 2 a 3 píxeles; MIROVA suma todos los alertados

- ARCHIVO:LÍNEA: `pipeline/single_pixel_mode.py:94-133` (vrp = max si `pc.vrp_mw < 5` y `n_pixels <= 3`), llamado en `process_viirs_mod.py:1125-1130`; flags `ENABLE_SINGLE_PIXEL_SUB_MW_MODE = True`, `SUB_MW_REGIME_THRESHOLD_MW = 5.0`, `SINGLE_PIXEL_MAX_CLUSTER_PIXELS = 3`. Contraste: `MIROVA_VIIRS750_VRP.m:61` y `:83-85` suman `numel(alert)` píxeles sin excepción.
- QUÉ PASA: un cúmulo de 2 o 3 píxeles bajo 5 MW se publica con la energía de su píxel más fuerte y no con la suma. SCRIPT:SALIDA `contar_ceros_v750.txt`, sección single_pixel_mode: 385 de 1.764 cúmulos de cumbre con magnitud > 0 tienen `single_pixel_mode = True` y 2 píxeles o más (367 pre-K, 18 K); en los 343 donde el cúmulo es toda la escena, `suma(anomaly_pixels) / pc.vrp_mw` tiene mediana **1,319** y máximo 2,795. Entre esos 385 hay 86 alertas de MIROVA y 72 protegidas. `spm_razon.txt`: la razón contra MIROVA en 2 a 3 píxeles con el modo es 0,426 (n = 86) contra 0,465 en 1 píxel (n = 296) y 0,653 sin el modo (n = 16).
- CÓMO SE VE EN EL DASHBOARD: la magnitud de un cúmulo de 2 a 3 píxeles se lee un 32 % (mediana) por debajo de lo que el propio pipeline calculó; el cambio de 1 a 2 píxeles (crecimiento de la anomalía) casi no mueve el número.
- CÓMO REPRODUCIRLO: `python experiments/_s158_audit_r2/ra1/spm_razon.py` tras H1.
- CONFIANZA: CONFIRMADO en código y conteo. Que esto sea una divergencia contra MIROVA es CONFIRMADO para VIIRS 750 (el `.m` suma) y TRASLADADO para MODIS y VIIRS 375 (no hay código).
- GRAVEDAD: 3.

### H4. El comentario del `.m` rotula al revés los ROI; la matriz de ejemplo dice lo contrario

- ARCHIVO:LÍNEA: `MIROVA_VIIRS750_hotspot_detection.m:111-118` (comentario) contra `:181-187` y `:397-399` (umbrales sensibles a `maskROI2`) y la matriz `VIIRS750_example.mat` (`BOX==2` = 7 x 7 central, `BOX==1` = 21 x 19 alrededor).
- QUÉ PASA: quien lea el comentario armará el `BOX` con el cuadro chico en 1 y el grande en 2, y aplicará los umbrales conservadores a la cumbre y los sensibles al entorno: perdería las anomalías débiles del cráter y publicaría más fuera de él.
- CÓMO SE VE EN EL DASHBOARD: invisible hoy (producción no usa `BOX`); importa para cualquier port.
- CÓMO REPRODUCIRLO: `python -c "import scipy.io as s,numpy as n;B=s.loadmat('experiments/_s158_d17_diseno/osf_codigo_mirova/Example/VIIRS750_example.mat')['BOX'];[print(v,(B==v).sum(),n.where(B==v)[0].min(),n.where(B==v)[0].max()) for v in (1,2)]"`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2 (riesgo para el port, no para producción).

## Fuera de alcance (anotado, no medido)

- La magnitud de MODIS y VIIRS 375 usa el mismo patrón (`np.maximum(..., 0)` y fondo escalar; el comentario de `process_viirs_mod.py:1055` dice "paridad MODIS/VIIRS 375m"). No lo leí en esos procesadores; TRASLADADO.
- `diario.html` y `mosaico.html` llevan copias propias de los helpers; sólo ejecuté las de `index.html`.
- En Chillán 2026-10-01 04:42 el único píxel del cúmulo viene de `diag_n_second_pass_recapture = 1` con `diag_n_first_pass_pixels = 0` y cenit 67,96° (`inspeccion_casos.txt`): un cúmulo de cumbre armado sólo por recaptura del segundo pase, a borde de barrido, cuya magnitud es 0. Si la recaptura sin primer pase es fiel al `.m` (que sí hace segundo pase, l. 228 a 235, pero con los umbrales de cada ROI) queda para RA2 o quien tenga la detección en el alcance.

## VERIFICADO LIMPIO

- Coeficiente y área de VIIRS 750: `WOOSTER_COEFF * NADIR_PIXEL_AREA_M2 = 11.081.250 = 1.97e7 * 0.5625` del `.m` (`fondo_produccion_etna.txt`, línea "coef y area"). Comando: `python experiments/_s158_audit_r2/ra1/fondo_produccion_etna.py`.
- Área nadir fija en producción: `ENABLE_NADIR_FIXED_PIXEL_AREA_VIIRS = True`, `ENABLE_GEOLOCATED_PIXEL_AREA = False` (`flags_efectivos_mirova_equivalent.txt`; `scan_geometry.py:319-375`).
- Ida y vuelta Planck del pipeline (BT a radiancia y vuelta) exacta a 1,8e-15 (`fondo_produccion_etna.txt`).
- La detección del `.m` reproducida por el port: `Npix` y `Tot_Lmir_hot` del OSF a 9 cifras; el fondo a 0,07 % con la diagonal opuesta de la triangulación (`port_mirova_v750_etna.txt`, `fillmissing_sensibilidad.txt`).
- Predicado del tablero: `mirovaEqVrp` (`index.html:1162`) e `isValidDetection` (`:1595`) extraídos por texto y ejecutados con node; control positivo y control cero correctos (`predicado_tablero.txt`). Sobre los 2.733 records V750 con cúmulo: 2.133 válidos, 1.764 con `mirovaEqVrp > 0` (los 369 de diferencia son cúmulos válidos fuera del `inner_radius_km`, que el tablero deja en 0 por distancia, no por magnitud).
- `inner_radius_km` de `volcanoes.yaml` y de la tabla `VOLCANOES` de `index.html` coinciden en todos los volcanes con records V750 (sin línea "OJO" en `contar_ceros_v750.txt`).
- Ningún cero de cumbre viene del tope de sanidad (50.000 MW) ni de `d9_capped`; el piso `MIN_VRP_MW_VIIRS750` es 0,0 (inerte). Caminos del Test 1 muertos en V750 (`ENABLE_TEST1_PATH = False`, 0 records con `final_hotspot_source = test1`).
- Control positivo de la afirmación 2: 1.764 cúmulos de cumbre con magnitud > 0 son todos visibles; 392 de ellos son alertas de MIROVA y 238 protegidas (`contar_ceros_v750.txt`).
- El `.m` no puede producir índices duplicados en la práctica (los alertados del pase 1 y los absolutos quedan en NaN antes del pase 2, y los tres dominios son disjuntos): en Etna 5 índices, 5 distintos.

## Lo que no pude medir

- `fillmissing2` de MATLAB no se puede ejecutar acá: el fondo del `.m` quedó aproximado con `griddata` lineal; la diferencia contra el OSF es 0,70 % con una diagonal y 0,07 % con la otra, y no sé cuál usa MATLAB. No cambia ningún veredicto (producción está a 72 % de distancia).
- La geometría del anillo de producción sobre la matriz de Etna es aproximada (píxeles x 0,75 km, centro (33,33)); producción mide haversine sobre el gránulo nativo. Con 3.359 píxeles en el anillo la mediana es robusta a esa aproximación, pero no lo medí sobre un gránulo chileno real: no descargué gránulos (límite del encargo) y no reprocesé nada.
- No medí cuánto cambia la magnitud de los 595 ceros si se reemplaza el fondo por el de MIROVA (interpolación local): haría falta el gránulo. El control D25 en Etna (10,15 MW) muestra el orden de magnitud, no el valor chileno.
- No separé, en los pares chilenos de H2, cuánto del déficit 0,46 es fondo y cuánto es que MIROVA suma más píxeles: los records no guardan el fondo por píxel de MIROVA. Etna es el único caso con los mismos píxeles.
- Las copias de `mirovaEqVrp` en `diario.html` y `mosaico.html` no se ejecutaron.
