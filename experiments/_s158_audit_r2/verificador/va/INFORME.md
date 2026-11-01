# Verificador VA, segunda ronda S158: veredictos sobre los 10 hallazgos

Contexto limpio: no leí los INFORME.md de los auditores ni VEREDICTOS_ANTES_DE_COMPARAR.md. Cada veredicto se apoya en
una lectura o medición mía por otro camino (scripts `v01` a `v09` en esta carpeta, con su `.txt` de salida). Código de
`pipeline/` idéntico a `origin/main` (`git diff --stat origin/main -- pipeline/` vacío). Flags leídos de
`pipeline.profile` con `VRP_PROFILE=mirova_equivalent`. Corpus: `data/mirova_equivalent/*.json` al 2026-10-21
(74.811 records, 71.968 de los 11 Tier A). Referencia NRT: `latest_consolidado.csv` + OCR del snapshot.

## El fenómeno en una línea

En la cumbre nevada de noche el cráter suele estar más frío que la mediana de un anillo de 5 a 25 km que baja a valles y
salares tibios. Un píxel débil que el segundo pase marca sin compuerta de temperatura queda con exceso de radiancia
negativo contra ese fondo, el recorte lo deja en 0,0 MW y el tablero lo oculta. MIROVA, en cambio, interpola el fondo
con los vecinos inmediatos (a la misma altitud) y no recorta. Los hallazgos 1, 2, 6 y 8 son eslabones de esa cadena.

## Tabla de veredictos

| n | veredicto | mi gravedad | mi evidencia | caminos por los que podía estar mal y cómo los descarté |
|---|---|---|---|---|
| 1 | CONFIRMADO | 3 | `pipeline/process_viirs_mod.py:539` (`bg_mask = dist 5 a 25 km`), `pipeline/detection_context.py:1083` (`t_bg = np.median`), `process_viirs_mod.py:1041` (Planck de la mediana), `:1056` (`np.maximum(L_hot - L_bg_rad, 0.0)`); flag `ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750 = False` leído de `pipeline.profile`. `.m`: `MIROVA_VIIRS750_VRP.m:64-85` enmascara alertados, dilata 3/5/7, `fillmissing2(...,'linear')`, `sum(hot) - sum(bk)` sin recorte | Que el flag del fondo por vecinos (D25) estuviera encendido: leído, apagado. Que el `.m` tuviera un recorte en otra parte: leí las 92 líneas, no hay `max(...,0)`. Gravedad bajada de 5: ver n = 2, el efecto sobre alertas de la misma pasada es sub-MW |
| 2 | CON MATIZ | 3 | `v01`: 595 de 2.359 cúmulos de cumbre V750 con `pc.vrp_mw == 0` (25,2 %), 595 de 595 ocultos por `isValidDetection` (`frontend/index.html:1600`, `pc.vrp_mw > 0`), 592 con todos los píxeles listados `bt_k <= t_bg_k`. `v02`: pareo por pasada | **El 96 y el 11 salen de parear a 60 min, que junta pasadas de otro satélite.** Con la referencia, la hora de MIROVA coincide exacta con la nuestra en 6.468 de 10.756 records V750 (`v02`). A la misma pasada (8 min, obs >= 2026-01-10): 64 alertas de MIROVA, **0 de 1 MW o más**, 84 sólo RUTINA. Los 9 «protegidos» desde marzo son alertas de 1 a 9 MW de la pasada siguiente (p. ej. Láscar 2026-03-03 04:54 contra 05:48), y en esas mismas pasadas MIROVA puso RUTINA o 0,09 a 0,53 MW. El conteo base (595) lo reproduje exacto sin usar `records_v750.json` ni el predicado de node |
| 10 | CON MATIZ | 3 | `v08`: port mío (`va_port.py`, escrito desde el `.m`) sobre los `.npz`, con reproyección propia (pyproj, diferencia 0,00 m) y remuestreo propio (igual al del probe a 1e-13). Láscar 10-08 0,328 MW (0,912), Chillán 10-10 12,367 (0,942), Villarrica 09-19 0,474 (1,054); producción 0,0 / 10,481 / 0,227 | (a) **El denominador es 8, no 7**: con gránulo «ok» hay 8 alertas de MIROVA (Láscar 10-08 y 09-26, PCC 10-10 y 10-16, Chillán 10-10, Villarrica 09-19, Tupungatito 08-21, Chaitén 10-06). (b) **Láscar 10-08 no es robusto al interpolador**: con 30 triangulaciones perturbadas el VRP va de 0,193 a 0,328 MW (0,54 a 0,91 de MIROVA); el «a menos de 10 %» es el extremo superior. Chillán (12,35 a 12,53) y Villarrica (0,474 fijo) sí son robustos. (c) En 2 de las 5 no reproducidas producción publica algo y el port nada (Láscar 09-26: 0,485 contra 0,74; Chaitén 10-06: 0,207 contra 0,18). El port no es una mejora uniforme con n = 8. (d) El BOX 21 × 21 del probe es supuesto; con el bloque real de Etna (21 × 19) los 8 resultados son idénticos. Controles negativos (Llaima RUTINA, Tupungatito 03-01) dan 0 |
| 3 | CONFIRMADO | 3 | `pipeline/single_pixel_mode.py:159-187` (`max(finite_vrps)` si `vrp < 5` y `n_pixels <= 3`); flags `SUB_MW_REGIME_THRESHOLD_MW = 5.0`, `SINGLE_PIXEL_MAX_CLUSTER_PIXELS = 3`; `.m:83-85` suma. `v03`: V750, 385 de 1.764 cúmulos de cumbre publicados con `single_pixel_mode` y 2 o más píxeles; donde el cúmulo es toda la escena (n = 343) suma/publicado mediana 1,319, p75 1,644, máx 2,795, y `pc == max(pixel)` en 343 de 343 | Control: n = 1 da 1,000 (1.194 de 1.195). Que la suma de `anomaly_pixels` no sea la del cúmulo: me restringí a `n_anomalous_pixels == pc.n_pixels`. Alcance mayor que el dicho: mismo mecanismo en V375 (2.364 de 7.225) y MODIS (153 de 512), mediana 1,35 y 1,37 |
| 4 | CON MATIZ | 3 | `v04`, pareo propio desde el CSV del OSF (2025, noche, 10 min, control rho(SatZen OSF, cenit nuestro) = 1,000). V375: rho(Npix MIROVA, cenit) = +0,08, rho(n_anom nuestro, cenit) = -0,24. **MODIS: rho(Npix MIROVA, cenit) = +0,285 (pareado) y +0,30 en las 12.938 filas chilenas del OSF, medianas 3 a 8 de nadir a 60°** | En V375 la afirmación se sostiene. **En MODIS el Npix de MIROVA no es plano: sube con el ángulo** (su remuestreo a grilla fija reparte el píxel grande en más celdas) y el nuestro baja poco (-0,13). La caída de la razón en MODIS la mueve sobre todo el lado de MIROVA. En el OSF V750 el Npix también sube fuerte (+0,60, medianas 5 a 12), aunque los pares V750 (n = 45) no muestran tendencia. Las dos caras apuntan a lo mismo (D17: área nadir fija sin remuestreo), pero «la caída es de nuestro conteo» vale sólo para V375 |
| 6 | CONFIRMADO | 3 | `pipeline/process_modis.py:582` (anillo), `:1083` (`L_bg_global` de la mediana), `:1118` (recorte); `local_kernel_bg` no está declarado para Láscar en `volcanoes.yaml`. `v01`: 37 ceros de 549 cúmulos de cumbre MODIS (619 records con cúmulo), 30 de Láscar, 37 de 37 con píxeles `<= t_bg`. `v09`: a la misma pasada, 9 alertas de MIROVA desde 2026-01-10, una de 1,04 MW (Láscar 2026-02-16 01:20 Terra, nuestro píxel 275,1 K contra anillo 276,55 K y `t_max` 290,7 K a 30,6 km) | Pareo a 8 y a 60 min da lo mismo en MODIS. El 619 es «records MODIS con `primary_cluster`», no «con píxeles» en otro sentido. Que fuera el tope D9: 0 de 37 con `d9_capped` |
| 8 | CONFIRMADO | 3 | `detection_context.py:546` (`gate_bt = bt > t_bg + bt_sanity_k`, `apply_bt_gate` default True en `:221` y la llamada V750 en `process_viirs_mod.py:882` no lo cambia), `:958-960` (segundo pase: `newly_active` sólo con Tests 2 y 3, sin compuerta), `ENABLE_SECOND_PASS_CONDITIONED = False`. `v06`: 1.257 records V750 sólo por segundo pase, de 28.581 con el campo (Tier A) | Subo la gravedad de 2 a 3 por VA-1: este pase es el origen de casi todos los ceros de 1, 2 y 6. Matiz de vara: el `.m` no tiene compuerta de temperatura en ningún pase, así que lo divergente respecto de MIROVA es la compuerta del primer pase (D22), no la recaptura |
| 7 | CONFIRMADO | 2 | `v01`: 71.968 records con `processed_utc`, 0 antes de 2026-10-18T09:57:30Z (mín 2026-10-18T10:03:43Z); los 38 `codigo_sha` descienden del squash de K `34cea39e` (control positivo HEAD rc 0, negativo rc 1); `pipeline/store.py:533` reescribe el sello sólo en la versión que se guarda (`:679-690`) | Que `processed_utc` se reescribiera al guardar sin reprocesar: leí `append_record`, el sello va en el record nuevo y sólo se guarda si reemplaza. Matiz: 2.843 records de los 34 volcanes no Tier A no tienen sello ni régimen (detector desconocido, anterior a S132). Consecuencia que no tuerce alertas pero sí evaluaciones: la frase de `CLAUDE.md` («los datos cambian de detector en la observación del 2026-09-18») quedó vieja y pide marca A113 |
| 5 | CON MATIZ | 2 | `v05`, pareo propio OSF 2025 V375; fondo nuestro = el que se resta (`diag_L_bg_local` cuando existe), coherente con Planck(`t_bg_k`) a 0,9997 a 1,0003 en 2.106 pares | Las cifras de Isluga (1,194, +3,2 K), Láscar (1,163, +2,7 K) y Copahue (1,066) se reproducen, pero Copahue tiene p25 0,898 (no es un sesgo claro) y **los otros dos volcanes con anillo salen más fríos**: Llaima 0,950 y Chillán 0,893. El anillo no es un sesgo caliente uniforme, depende del relieve. Donde corre el kernel local (Chaitén, Lastarria, PP, PCC, Villarrica) la razón es 0,93 a 0,98. Además se comparan conjuntos de píxeles distintos (los nuestros contra los alertados de MIROVA) |
| 9 | CONFIRMADO (matiz menor) | 2 | `v07`: port mío sobre la matriz de Etna: Npix 5 (los 5 en `BOX == 2`), hot 1,965342180 exacto; fondo Qhull 1,080443826; 65 fondos distintos en 300 triangulaciones perturbadas, rango 1,060 a 1,086 (VRP 0,985 a 1,014 del OSF), y uno igual al OSF a 9 decimales (aparece 4 veces) | El rango y la coincidencia los reproduje con código propio. Matiz: «ningún port en Python» es fuerte; vale para un port con la triangulación por defecto de Qhull mientras no se conozca la regla de MATLAB. La banda depende de la escena: en Láscar 10-08 fue de hasta -41 % (30 triangulaciones, `v08`) |

## Hallazgos propios

**VA-1. Los ceros de cumbre los fabrica el segundo pase, en los tres sensores**
- `v09_modis_protegida.txt` (segundo bloque) y `v06`: cúmulos de cumbre con `pc.vrp_mw == 0` y `diag_n_first_pass_pixels == 0` con recaptura > 0: V750 594 de 595, MODIS 37 de 37, V375 270 de 271.
- Qué pasa: el primer pase exige `bt > t_bg + 3 K`; ningún píxel más frío que el anillo puede salir de ahí. El segundo pase (sin compuerta, sin condicionar) agrega un píxel de contraste NTI/ETI local que está más frío que la mediana del anillo; el fondo del VRP lo deja en 0 y el tablero lo esconde. Los hallazgos 1, 2, 6 y 8 son una sola cadena.
- Dashboard: el operador no ve nada esa pasada; en 64 pasadas V750 y 9 MODIS MIROVA sí publicó (sub-MW salvo una de 1,04 MW).
- Reproducir: `python experiments/_s158_audit_r2/verificador/va/v06_segundo_pase.py`; caso Láscar MODIS 2026-02-16 01:20 Terra.
- CONFIRMADO. Gravedad 3. Implicancia para el arreglo: tocar sólo el fondo (D25) o sólo la compuerta no basta para entender el efecto; hay que medir los dos juntos.

**VA-2. V375 también tiene 271 cúmulos de cumbre en 0,0 MW ocultos**
- `v09_modis_protegida.txt`, segundo bloque: V375 cero 271 (270 sólo segundo pase) de 7.496 cúmulos de cumbre.
- No los pareé con MIROVA. CONFIRMADO el conteo, efecto en alertas SIN DATO. Gravedad 2.

**VA-3. El acierto de Láscar 2026-10-08 en la prueba con gránulos depende de la triangulación** (ver n = 10). CONFIRMADO, gravedad 2.

**VA-4. Rótulo invertido del BOX y forma del ROI1**
- `v07` y lectura de la matriz: `BOX == 2` es el 7 × 7 central (filas y columnas 30 a 36, 49 celdas) con umbrales sensibles de noche (`.m:180-187`, sigma 5, mínimos 0,003); `BOX == 1` es un bloque de 21 × 19 (filas 22 a 42, columnas 24 a 42, 350 celdas), no un cuadrado de 21 × 21. Los comentarios del `.m:111-118` rotulan al revés.
- Sin efecto medido en los 8 gránulos chilenos (mismo resultado con 21 × 21 y con 21 × 19). CONFIRMADO, gravedad 1.

## VERIFICADO LIMPIO

- Código de producción igual a `origin/main`: `git diff --stat origin/main -- pipeline/` vacío.
- Clasificación de sensor del lector: 29.743 V750, 29.985 V375, 15.083 MODIS (`v01`, sensores crudos impresos).
- El predicado del tablero oculta todo cúmulo en 0: `frontend/index.html:1600` y `mirovaEqVrp` (`:1162-1183`) devuelven 0 con `pc.vrp_mw == 0`.
- Ningún cero de cumbre viene del tope D9 (0 de 595 V750, 0 de 37 MODIS con `d9_capped`).
- El segundo pase no recaptura fuera de la caja de 25 km en V750: máximo `dist_km` de `anomaly_pixels` <= 36 km en 2.782 de 2.782 records con píxeles (una línea en la sesión, sin script aparte).
- `diag_L_bg_w_m2_sr_um` es Planck(`t_bg_k`) a 3,74 µm (0,9997 a 1,0003, n = 2.106, `v05`).
- Georreferencia de los `.npz`: reproyectar lat/lon con pyproj da los mismos x, y (0,00 m) y mi remuestreo coincide con la grilla guardada a 1e-13 (`v08`).
- Mi port del `.m` reproduce Npix y Tot_Lmir_hot del OSF en Etna exactos y los números base del probe en los 8 gránulos (`v07`, `v08`).
- `processed_utc` describe la versión guardada del record (`pipeline/store.py:533`, `:665-690`, reemplazo sólo con overwrite o upgrade).

## Lo que no pude medir

- La vara del paper para el fondo del VRP en MODIS y V375: no rendericé páginas de `sp426.5.pdf`. Los hallazgos 5 y 6 quedan verificados como hecho medido, no como divergencia de paper.
- La regla con que MATLAB elige la diagonal en `fillmissing2`: sin MATLAB, sólo la evidencia empírica de Etna.
- La posición real de la grilla de MIROVA en Chile (el `ul_x/ul_y` sale de los TIF de 375 m, supuesto del probe).
- Qué magnitud ve el operador en V375: el tablero publica `f5_core_vrp_mw` ahí; no medí cuánto cambia el hallazgo 3 en esa vista (SOSPECHA de que el efecto visible en V375 es otro).
- El pareo con MIROVA de los 271 ceros de V375 (VA-2).
- No despaché workflows ni bajé gránulos; la prueba 10 se verificó sólo sobre los recortes guardados.

## Archivos

Todos en `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s158-audit-r2-0eeee2\experiments\_s158_audit_r2\verificador\va\`:
`v01_ceros_cumbre_y_regimen.py/.txt`, `v02_dt_pareo_v750.py/.txt`, `v03_single_pixel_mode.py/.txt`, `v04_npix_cenit.py/.txt`,
`v05_fondo_anillo_vs_osf.py/.txt`, `v06_segundo_pase.py/.txt`, `v07_port_minimo_etna.py/.txt`, `va_port.py`,
`v08_granulos_port_propio.py/.txt`, `v09_modis_protegida.txt`.
