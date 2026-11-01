# F2. Unidades y magnitudes: censo de constantes (auditoría S160)

- Fecha y hora del servidor: 2026-10-22 03:33:05 GMT (cabecera `Date` de `gh api -i repos/MendozaVolcanic/VRP-chile`, una llamada; los insumos del orquestador son de las 03:11:55 GMT).
- Commit medido: `origin/main` = `d516b9d8c0fad5b0ca458b9fb57cdf5e6f75f956`, instantánea `D:\vrp-trabajo\temporales\s160_audit\main\` (código y datos). `volcanoes.yaml` no venía en la instantánea: se extrajo con `git show d516b9d8c:volcanoes.yaml` a esa misma carpeta (847 líneas).
- Modelo y esfuerzo: Claude Fable 5.1, `high`.
- CARPETA: `C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\f2\`. Pesado: `D:\vrp-trabajo\temporales\s160_audit\f2\perfil_efectivo.json` (8 KB).
- Código de MIROVA citado: copia local `C:\vrp-trabajo\s159-pruebas\experiments\_s158_d17_diseno\osf_codigo_mirova\` (OSF zm62w), sha256 `6b73c84f…` (`MIROVA_VIIRS750_hotspot_detection.m`) y `af9e9115…` (`MIROVA_VIIRS750_VRP.m`). Es código de VIIRS 750 solamente; toda extensión a VIIRS 375 y MODIS es SOSPECHA y así se marca.
- Referencias de MIROVA: no se usó ninguna cifra de paridad en este frente (la tarea mide unidades y rangos sobre nuestros propios records). Declaro igual los sha256 de las copias congeladas que leí para comprobar que existen: tabla sola `latest_consolidado.csv` `bc1522c24c924cb5…`, OCR `registro_vrp_ocr.csv` `94679246acbd0db5…`.
- Lo que NO miré: `scripts/_archive/`, `pipeline/profiles/_*.yaml` de A/B (solo el perfil efectivo `mirova_equivalent`), `frontend/comparacion.html`, `frontend/periodo.js`, `frontend/cambio_detector.js`, `tests/`, `.github/workflows/`, el `Example/` del OSF. No reprocesé L1B ni despaché workflows. No verifiqué en RENDER ninguna página de paper: toda cita a paper en este informe es TEXTO de un comentario del repositorio o SIN LOCALIZAR, y lo digo en cada caso.

## En una pantalla

1. El censo (2.890 filas, 64 revisadas a mano) encuentra entero el control positivo del plan (14 de 14, código de salida 0) y reproduce los cuatro controles del barrido como discrepancias.
2. Fuera de lo conocido hay cuatro discrepancias nuevas con código leído: el cambio de espacio del kernel (3×3 con central en MIROVA, 8 vecinos acá) también mueve el C1 de cumbre y el piso −0,1 (F2-202); el C2 del segundo pase multiplica la sigma de otro pool (F2-205); el anillo de fondo 5 a 25 km está centrado en el centro del volcán y en PCC el cráter cae adentro (F2-206); el modo de un píxel publica un máximo donde el código de MIROVA suma (F2-209).
3. Medido en la ventana K: el umbral efectivo de escena queda bajo el mínimo de MIROVA en 93 % de las pasadas VIIRS 375, 76 % VIIRS 750 y 58 % MODIS; 32 de 118 cúmulos VIIRS 750 se publican con 0,0 MW por el recorte del fondo; la VRE del tablero integra 2,6 veces más horas que las que hay.
4. Dos umbrales de evaluación viven en otro espacio: `RECALL_MIN` (detector C0) aplicado a K (F2-213) y el tope D9 definido como cirrus pero disparado por altitud (F2-208, hoy 1 record en K).
5. SIN FUENTE: 18 constantes revisadas, contadas y publicadas en el CSV; no son discrepancia.

## Instrumento

### Censo (`censo_magnitudes.py`)

Recorre el AST de `pipeline/*.py` y `scripts/*.py` (constantes en comparaciones, asignaciones, defaults, `.get` con respaldo, `np.clip`/`maximum`/`minimum`/`min`/`max`, kwargs, dicts, returns), los valores efectivos del perfil (`pipeline.profile` importado con `VRP_PROFILE=mirova_equivalent` desde la instantánea, técnica T2; `perfil_efectivo.json` guarda los 148 atributos), `volcanoes.yaml` y los `<script>` de `index.html`, `diario.html` y `mosaico.html` (comparaciones, `const`, `Math.max/min`, `??`/`||`, ternarios). Salida: `censo_bruto.csv` (2.890 filas: 1.155 asignaciones, 353 comparaciones, 268 claves de volcán, 238 returns, 66 del perfil, 221 del frontend, el resto en `control_salida.txt`).

Pregunta 1 (si el censo estuviera roto, ¿se vería?): sí para las clases que cubre el control positivo (asignación de módulo, valor del perfil, comparación, default, clave YAML). No cubre: literales dentro de f-strings, archivos `.js` aparte (`periodo.js`, `cambio_detector.js`), números escritos como cadena, y en JS los literales que no están en comparación ni `const` (por eso `111.0` de `index.html:2927` no tiene fila bruta y se agregó a mano). Esas ausencias son del instrumento, no del repositorio.

Pregunta 2 (si el instrumento estuviera muerto, ¿se vería?): el control positivo sale con código 2 si falta una constante; el control negativo (archivo sin constantes, 0 filas) no distingue "muerto" de "sano" por sí solo y se lee junto con el positivo.

Controles, `control_salida.txt`:
- Positivo: 14 de 14 encontrados. `WOOSTER_COEFF` 18.9 (`process_modis.py:87`), 18.0 (`process_viirs.py:77`), 19.7 (`process_viirs_mod.py:66`); C1 0,003 y 0,010 (`profile.py:104-105`); N·σ 5/10/15 (`profile.py:194,195,203`); tope 5 MW (`profile.py:824`); 1 MW (`clase_mirova.py:46`); 0,05 MW (`clase_mirova.py:106`); `TOL_S` 120 (`banco_paridad.py:76`); `inner_radius_km` 20 de PCC (`volcanoes.yaml:18`) y 3 de Lastarria (`volcanoes.yaml:638`). Los valores efectivos coinciden con los que el plan tomó de `CLAUDE.md`; el perfil efectivo además dice `ENABLE_TEST1_PATH=False`, `ENABLE_TESTS_23_PROSE_BRANCH=True` (conectiva `max`), `ENABLE_MODIS_B22_PRIMARY=True`, `ENABLE_BT_PATH_HOT=False`, y los tres pisos `MIN_VRP_MW_*` en 0,0.
- Negativo: `control_negativo_sin_constantes.py` da 0 filas.
- Conteo contra `grep` independiente (`control_conteo_grep.csv`): AST/grep entre 0,36 (`fetch.py`) y 0,87 (`process_viirs_mod.py`). El grep cuenta índices, versiones de producto, formatos y números en cadenas, que el AST excluye a propósito; no hay archivo donde el AST cuente más que el grep.

### Rangos chilenos (`rangos_chile.py`, `umbral_efectivo.py`, `origen_distancia.py`)

Denominador: los 74.811 records de `data/mirova_equivalent/*.json` de la instantánea (45 volcanes), y aparte la ventana K (observaciones desde 2026-09-18 00:00 UTC, 3.896 records de los 11 Tier A: 777 MODIS, 1.566 VIIRS 375, 1.553 VIIRS 750). Rangos medidos, ventana K (p5 / p50 / p95):
- BT máxima del ROI: MODIS 245 / 274 / 285 K; VIIRS 375 251 / 277 / 288 K; VIIRS 750 246 / 273 / 282 K.
- Fondo (mediana del anillo): 234 / 262 / 277; 236 / 262 / 276; 234 / 260 / 274 K. Bajo 270 K en 81 %, 82 % y 88 % de las pasadas.
- Cenit del sensor: MODIS hasta 65,3°; VIIRS hasta 70,5° (31 records en K sobre 70°).
- VRP del cúmulo publicado (> 0): MODIS 0,28 / 1,02 / 9,2 MW (n = 25); VIIRS 375 0,02 / 0,11 / 3,6 (n = 430); VIIRS 750 0,06 / 0,87 / 13,1 (n = 86). Máximos del corpus entero: 63, 89 y 116 MW.
- Sigma del dNTI de escena: 0,0008 / 0,0020 / 0,0041 (MODIS); 0,0009 / 0,0014 / 0,0024 (V375); 0,0010 / 0,0017 / 0,0033 (V750).

Pregunta 1: el tope D9 tiene que aparecer en 5,0 exacto y el recorte del fondo en 0,0 con píxeles: los dos aparecen (9 y 915 records en el corpus). Pregunta 2: todos los n se imprimen; ninguno es 0 donde se esperaba dato.

## Hallazgos (orden de gravedad)

### F2-201
- TÍTULO: El C1 de escena (0,010) está bajo el mínimo del código de MIROVA y además en otro espacio de kernel; el umbral efectivo de escena queda por debajo del suyo en 93 % de las pasadas VIIRS 375 de la ventana K.
- ARCHIVO:LÍNEA: `pipeline/profile.py:105` (`pipeline/profiles/mirova_equivalent.yaml:124`); aplicación `pipeline/detection_context.py:483-486` (media de 8 vecinos sin el central) y `:532-533` (`max(C1, μ + 10σ)` para dNTI y dETI de escena con el mismo 0,010); MIROVA `MIROVA_VIIRS750_hotspot_detection.m` l. 183 (`minimumNTIcontrastROI1 = 0.02`), l. 186 (`minimumETIcontrastROI1 = 0.01`), l. 281-285 (`colfilt(…, [3 3], 'sliding', neighbourhoodMean)`, media 3×3 que incluye el píxel central).
- QUÉ PASA: fuera de la cumbre, el píxel tibio de un flanco o de un borde de nube destaca de sus vecinos por poco. MIROVA mide ese contraste restando la media 3×3 con el píxel adentro, así que su contraste es 8/9 del nuestro, y exige 0,02 en dNTI y 0,01 en dETI; en nuestras unidades eso es 0,0225 y 0,01125. Nosotros exigimos 0,010 para los dos índices. Con la conectiva `max` el umbral efectivo es `max(0,010, μ + 10σ)`: medido en K, ese umbral queda bajo 0,0225 en 1.449 de 1.554 pasadas VIIRS 375 (93,2 %), 1.173 de 1.552 VIIRS 750 (75,6 %) y 454 de 776 MODIS (58,5 %); para dETI, bajo 0,01125 en 59,2 / 79,3 / 55,2 %.
- CÓMO SE VE EN EL DASHBOARD: publicaciones fuera del `inner_radius_km` que MIROVA no haría; el tablero las esconde con "Solo cráter" salvo en PCC, donde el inner de 20 km las deja pasar (AUDIT_S158 §4 ya contó 8 publicadas a 9,9 a 19 km).
- CÓMO REPRODUCIRLO: `PYTHONIOENCODING=utf-8 python experiments/_s160_audit/f2/umbral_efectivo.py` (filas `dnti_sce` y `deti_sce`).
- CONFIANZA: CONFIRMADO para VIIRS 750 (es el sensor del código). SOSPECHA de que rijan los mismos mínimos en VIIRS 375 y MODIS (no hay código publicado de esos sensores).
- GRAVEDAD: 5. Es el control positivo del plan (S158 F4-H1 y V3), reproducido con otro instrumento y extendido a los tres sensores y al dETI.

### F2-203
- TÍTULO: El recorte a cero del exceso sobre el fondo regional publica 0,0 MW en 27 % de los cúmulos VIIRS 750 de la ventana K, y el tablero los hace desaparecer.
- ARCHIVO:LÍNEA: `pipeline/process_viirs_mod.py:1041` (`L_bg_rad = Planck(t_bg)`, mediana del anillo) y `:1056` (`np.maximum(L_hot - L_bg_rad, 0.0)`); igual en `process_viirs.py:1504` y `process_modis.py:1118`; `frontend/index.html:1603` (`isValidDetection` exige `pc.vrp_mw > 0`); MIROVA `MIROVA_VIIRS750_VRP.m` l. 69-91 (fondo local `fillmissing2` bajo un halo de 3/5/7 celdas, sin recorte).
- QUÉ PASA: en una cumbre nevada el anillo de 5 a 25 km es valle tibio; la mediana del anillo supera al píxel del cráter y el exceso sale negativo y se recorta a 0. El píxel pasó los Tests 2 y 3 (destaca de sus vecinos) pero no tiene energía contra un fondo que no es el suyo.
- CÓMO SE VE EN EL DASHBOARD: el cúmulo existe en el JSON con píxeles y 0,0 MW; `isValidDetection` lo saca del contador del cráter, las pastillas y el gráfico. Ventana K: 32 de 118 cúmulos VIIRS 750 (30 `summit`), 7 de 437 VIIRS 375, 1 de 26 MODIS. Corpus entero: 600 de 2.733 VIIRS 750 (22 %), 278 de 9.690 VIIRS 375, 37 de 619 MODIS; por volcán, Tupungatito 344, Isluga 263, Láscar 135.
- CÓMO REPRODUCIRLO: `python experiments/_s160_audit/f2/rangos_chile.py`, contador `cumulo_con_px_y_vrp_0`; volcán y pasada de ejemplo: cualquier record de Tupungatito VIIRS 750 con `primary_cluster.n_pixels > 0` y `vrp_mw == 0`.
- CONFIANZA: CONFIRMADO (control del plan, `docs/AUDIT_S158_R2.md` §1 fila 1; D25 con A/B pendiente).
- GRAVEDAD: 5 (mueve lo que se publica hoy).

### F2-202
- TÍTULO: El cambio de espacio del kernel también afecta al C1 de cumbre (0,003) y al piso de descarte (−0,1): 12,5 % más laxos que el código de MIROVA.
- ARCHIVO:LÍNEA: `pipeline/profile.py:104`; `pipeline/detection_context.py:60-61` (pisos −0,1), `:127-129` (se aplican a dNTI y a dETI), `:530-531` (`max(0,003, μ + 5σ)` de cumbre); MIROVA `.m` l. 184 y 187 (0,003 para `ROI2`, que es la cumbre: los comentarios del `.m` rotulan ROI1/ROI2 al revés, verificado en S158), l. 298 (`ZI_NTI_spatialContrast < -0.1 → NaN`, solo para NTI).
- QUÉ PASA: el mismo factor 9/8 convierte 0,003 en 0,003375 y −0,1 en −0,1125. En K el umbral de cumbre nuestro queda bajo el convertido en dNTI en 0,2 % (V375), 0,4 % (V750), 2,8 % (MODIS) de las pasadas, y en dETI en 8,2 %, 21,7 % y 18,2 %. Además descartamos del pool los píxeles con dETI < −0,1 y MIROVA no (su descarte es solo sobre el contraste de NTI).
- CÓMO SE VE EN EL DASHBOARD: una fracción chica de publicaciones de cumbre con contraste entre 0,003 y 0,0034 (dNTI) o entre 0,010 y 0,0113 (dETI de escena ya contado en 201).
- CÓMO REPRODUCIRLO: `python experiments/_s160_audit/f2/umbral_efectivo.py` (filas `*_sum`).
- CONFIANZA: CONFIRMADO (código leído en los dos lados).
- GRAVEDAD: 4.

### F2-205
- TÍTULO: C2 (5 y 10) multiplica en el segundo pase la sigma de un pool que MIROVA no usa: sin el descarte < −0,1 ni el borde.
- ARCHIVO:LÍNEA: `pipeline/detection_context.py:923` (`bg_mask = (~active_mask) & isfinite(dnti) & isfinite(deti)`), contra `:492-510` del primer pase (`build_unsuitable_mask`: borde, dNTI < −0,1, dETI < −0,1); MIROVA `.m` l. 211-233 (los dos pases llaman a la misma `contextualDetectionPass`) y l. 298-304 (descarte < −0,1 antes de `mean`/`std`).
- QUÉ PASA: la sigma del contraste es la que decide fuera del piso. En el segundo pase recomputamos μ y σ con los contrastes negativos grandes adentro (sombras, bordes), que MIROVA saca en los dos pases. Una σ inflada sube el umbral y recaptura menos; una σ deflactada recaptura más. El sentido depende de la escena.
- CÓMO SE VE EN EL DASHBOARD: en los píxeles que entran por recaptura (K: 170 pasadas VIIRS 375, 76 VIIRS 750, 14 MODIS con `diag_n_second_pass_recapture > 0`). Efecto en magnitud: SIN DATO (pide píxeles, no records).
- CÓMO REPRODUCIRLO: `grep -n "bg_mask = " pipeline/detection_context.py`; `sed -n 295,305p MIROVA_VIIRS750_hotspot_detection.m`.
- CONFIANZA: CONFIRMADO en el código; impacto SIN DATO.
- GRAVEDAD: 4.

### F2-206
- TÍTULO: El anillo de fondo de 5 a 25 km está centrado en el centro del volcán y no en el cráter: en PCC el cráter queda dentro del anillo que define el fondo.
- ARCHIVO:LÍNEA: `pipeline/profile.py:127-128` (`BG_INNER_KM`, `BG_OUTER_KM`); `pipeline/process_viirs.py:807`, `pipeline/process_viirs_mod.py:539`, `pipeline/process_modis.py:582` (`bg_mask = (dist >= BG_INNER_KM) & (dist <= BG_OUTER_KM)`); `dist` sale de `haversine_km(volcano_lat, volcano_lon, …)` (`process_viirs.py:780`, `process_viirs_mod.py:517`, `process_modis.py:560`), mientras `vent_dist_per_pixel` sale del cráter (`:786`, `:521`, `:564`). Coordenadas: `volcanoes.yaml` PCC centro −40,590 / −72,117 (centro de grilla MIROVA) y cráter −40,5255 / −72,1461: 7,58 km (`origen_distancia_salida.txt`); Tupungatito 2,73 km; Villarrica 0,85; Láscar 0,68; Chaitén 0,59; PP 0,50; los otros cinco 0.
- QUÉ PASA: el anillo excluye 5 km alrededor del centro para que la fuente no entre al fondo. En PCC la fuente está a 7,6 km del centro, o sea dentro del anillo: la mediana del fondo (`t_bg`) y por lo tanto la compuerta de 3 K y el `L_bg` del VRP llevan adentro la zona del lacolito. En Tupungatito el margen es 2,3 km, menos que el `inner_radius_km` de 7.
- CÓMO SE VE EN EL DASHBOARD: en PCC y Tupungatito, magnitudes y compuerta calculadas contra un fondo que contiene a la fuente. Cuánto: SIN DATO (pide píxeles). Nota: con D25 (fondo por vecinos) este anillo deja de alimentar el VRP, pero la compuerta de 3 K y el tope D9 lo siguen usando.
- CÓMO REPRODUCIRLO: `python experiments/_s160_audit/f2/origen_distancia.py` (sección `dist_centro_crater`); `grep -n "bg_mask = " pipeline/process_*.py`.
- CONFIANZA: CONFIRMADO (código y coordenadas); impacto SIN DATO.
- GRAVEDAD: 4.

### F2-209
- TÍTULO: El modo de un píxel publica el píxel máximo donde el código de MIROVA suma todos los alertados; está calibrado con el detector C0.
- ARCHIVO:LÍNEA: `pipeline/profile.py:857` (`SUB_MW_REGIME_THRESHOLD_MW` 5,0; `SINGLE_PIXEL_MAX_CLUSTER_PIXELS` 3; `mirova_equivalent.yaml:533-534`); `pipeline/single_pixel_mode.py:94`; `pipeline/process_viirs_mod.py:1125-1130`; MIROVA `MIROVA_VIIRS750_VRP.m` l. 83-91 (`L_MIRhot = sum(ZI_M13(alert))`).
- QUÉ PASA: un cúmulo de 2 o 3 píxeles con suma bajo 5 MW se publica con el VRP del píxel mayor. El docstring del módulo justifica el modo con razones ours/MIROVA de S77 (detector C0) y reconoce que el alcance real no coincidía con el declarado (S127). El código de MIROVA para VIIRS 750 suma; no hay en él ningún modo de un píxel.
- CÓMO SE VE EN EL DASHBOARD: magnitud menor que la suma en cúmulos chicos. Ventana K: el flag `single_pixel_mode` está en 407 de 430 cúmulos VIIRS 375, 71 de 86 VIIRS 750, 21 de 25 MODIS; cambia la cifra solo cuando `n_pixels > 1`: hasta 102, 27 y 12 cúmulos respectivamente (`single_pixel_salida.txt`). El conteo exacto de cuántos cambian de valor pide las sumas por píxel: SIN DATO.
- CÓMO REPRODUCIRLO: ver `single_pixel_salida.txt` (el comando está en la cabecera del archivo); `sed -n 83,91p MIROVA_VIIRS750_VRP.m`.
- CONFIANZA: CONFIRMADO (código); conteo de magnitudes cambiadas SIN DATO.
- GRAVEDAD: 4. Relacionado con AUDIT_S158 §4 (MIROVA publica la unión; nosotros un cúmulo con modo de un píxel).

### F2-213
- TÍTULO: `RECALL_MIN` del auto-audit se calibró con el detector C0 y se aplica a records del detector K, que en VIIRS 750 publica bajo esa banda.
- ARCHIVO:LÍNEA: `scripts/auto_audit_weekly.py:120` (`RECALL_MIN = {"VIIRS375": 93.4, "VIIRS750": 79.5, "MODIS": 95.0}`), `:20-21` (refs 98,4 / 84,5 / 100), `:742-747` (flag si `recall_crater_pct < RECALL_MIN[s]`, con el nombre del detector en el texto); `frontend/index.html:544` (con K, VIIRS 750 publicó 28 de 42 y 91 de 117 pasadas con alerta: 66,7 y 77,8 %).
- QUÉ PASA: el umbral es una medición del detector anterior. Con K, VIIRS 750 publica menos alertas de MIROVA (y, según la misma nota, ninguna protegida que decida). El flag semanal de recall de VIIRS 750 sale por construcción mientras `n_noches >= 15`, y nombra al detector pero no cambia la banda.
- CÓMO SE VE EN EL DASHBOARD: en el issue semanal del auto-audit y en el bloque de métricas; invisible en el mapa.
- CÓMO REPRODUCIRLO: `sed -n 742,747p scripts/auto_audit_weekly.py`; `sed -n 544p frontend/index.html`.
- CONFIANZA: CONFIRMADO (código y cifras del propio tablero). No corrí el auto-audit: el último `latest.json` no está en la instantánea.
- GRAVEDAD: 4.

### F2-204
- TÍTULO: `inner_radius_km` se aplica desde el cráter en el pipeline y desde el centro del volcán en `anomaly_pixels[].dist_km`, en el respaldo de clase del tablero y bajo el rótulo "Distancia al cráter".
- ARCHIVO:LÍNEA: `volcanoes.yaml:18` (PCC 20); `pipeline/clustering.py:104` (`centroid_dist_km` desde `vent_lat`); `pipeline/process_viirs.py:1530`, `process_viirs_mod.py:1075`, `process_modis.py:1143` (`dist_km` de cada píxel desde `dist`, que es desde `volcano_lat`); `frontend/index.html:3036` (clase de respaldo con `pixels[0].dist_km`), `:3159` (rótulo "Distancia al cráter" con `px.dist_km`), `:1627-1660` (`pixelesDelMarcador`: el primer punto usa `final_hotspot_dist_km`, desde el cráter; los siguientes, `anomaly_pixels`).
- QUÉ PASA: el mismo radio se compara con distancias de dos orígenes. Para el centroide publicado, medido desde los dos orígenes: en K, PCC 8 de 73 cúmulos cambian de clase (7 `summit` hoy serían `far` desde el centro), Tupungatito 2 de 54; corpus entero PCC 88 de 1.906, Tupungatito 19 de 1.286, Láscar 2 de 2.933; los demás 0 (control negativo: centro = cráter).
- CÓMO SE VE EN EL DASHBOARD: el marcador primario y la tabla llevan la distancia desde el cráter; con "Todos los píxeles" los popups de los demás píxeles dicen "Distancia al cráter" y miden desde el centro (hasta 7,6 km de diferencia en PCC). `distance_class` persistido no cambia (0 casos `clase_distinta(pc_vs_final)` en VIIRS).
- CÓMO REPRODUCIRLO: `python experiments/_s160_audit/f2/origen_distancia.py`.
- CONFIANZA: CONFIRMADO (control V3-1 reproducido y medido).
- GRAVEDAD: 3.

### F2-208
- TÍTULO: El tope D9 de 5 MW se define por cirrus (`t_bg < 270 K`) y se dispara por altitud: verdadero en 81 a 88 % de las pasadas K; y "solo contextual" es casi vacío porque el camino de BT está apagado.
- ARCHIVO:LÍNEA: `pipeline/profile.py:824-829` (`mirova_equivalent.yaml:506-507`); `pipeline/process_viirs_mod.py:1009-1015`, `process_viirs.py:1440-1446`, `process_modis.py:1056-1062` (`n_bt_path == 0 and n_nti_path == 0 and t_bg < 270`).
- QUÉ PASA: el fondo del anillo está bajo 270 K en 626 de 777 pasadas MODIS, 1.286 de 1.566 VIIRS 375 y 1.374 de 1.553 VIIRS 750 de la ventana K (altitud, A68), así que el tope está armado casi siempre; `n_bt_path` es 0 en todos los records K (D31) y `n_nti_path > 0` en 56 de 3.896. El tope muerde solo cuando el cúmulo pasa de 5 MW sin que ningún píxel supere NTI −0,8: en K, 1 record (PCC MODIS Terra 2026-10-03 01:25, centroide a 15,3 km, `summit` por el inner de 20); en el corpus, 9 (Láscar 7, PCC 2). Los 4 cúmulos de K sobre 5 MW con fondo frío que no se toparon tenían `n_nti_path > 0`.
- CÓMO SE VE EN EL DASHBOARD: "5,0 MW (tope)" con la leyenda de `PATH_D_CAP_MW` (`index.html:1226-1232`).
- CÓMO REPRODUCIRLO: `python experiments/_s160_audit/f2/rangos_chile.py` (contadores `t_bg<270`, `d9_capped`, lista `capped_K`).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 3 (recorte real, 1 record en producción hoy). La marca S151 de A23 ya anota que el tope recorta sin que lo recortado esté medido como artefacto.

### F2-211
- TÍTULO: La VRE del tablero integra 6 h por record y hay 10,4 records por volcán y día: 62,5 h integradas por día, VRE 2,6 veces sobreestimada.
- ARCHIVO:LÍNEA: `frontend/index.html:2486-2500` (`DT_HOURS = 6`, comentario "each observation ~ 6h window (4 passes/day)"), `:3319` (serie acumulada).
- QUÉ PASA: la VRE es energía, o sea potencia por tiempo. El 6 h supone cuatro pasadas por día y un sensor; hoy hay tres sensores y varias plataformas: en K, de 8,8 (Isluga) a 11,7 (PCC) records por volcán y día (`origen_distancia_salida.txt`). Cada record suma 6 h aunque la pasada siguiente llegue 40 min después.
- CÓMO SE VE EN EL DASHBOARD: "VRE acumulada (GJ)" y el gráfico acumulado, 2,6 veces altos en promedio; no entra en ninguna decisión de alerta.
- CÓMO REPRODUCIRLO: `python experiments/_s160_audit/f2/origen_distancia.py` (sección VRE).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 3 (número publicado, no decide alerta).

### F2-207
- TÍTULO: El tope de cordura de 50 GW se decide con `t_max_k` antes de normalizar `t_max_i04_k`: VIIRS 375 siempre cae en "BT imposible" si supera el tope. Latente.
- ARCHIVO:LÍNEA: `pipeline/store.py:551` (`_apply_sanity_cap`), `:165-166` (`t_max is None → bt_imposible`), `:556-557` (normalización después).
- QUÉ PASA: control R2-7 del plan. Medido: 0 records con `diag_rejected_sanity_cap_mw`, `diag_pc_rejected_sanity_cap_mw` o `vrp_exceeds_sanity_cap` en la instantánea; máximos publicados 89 MW (V375), 116 (V750), 63 (MODIS).
- CÓMO SE VE EN EL DASHBOARD: invisible hoy.
- CÓMO REPRODUCIRLO: `sed -n 551,557p pipeline/store.py`; `python experiments/_s160_audit/f2/rangos_chile.py` (`sanity_cap_anulado`, `vrp_exceeds_sanity_cap`).
- CONFIANZA: CONFIRMADO (lectura; el R2 lo probó con `append_record`).
- GRAVEDAD: 3 (latente; el escenario es la erupción más grande).

### F2-210
- TÍTULO: `BT_PHYSICAL_MAX_K` = 500 K está definido para MODIS B21 y se aplica a los tres sensores.
- ARCHIVO:LÍNEA: `pipeline/store.py:74` (comentario: "MODIS B21 satura cerca de 500 K (Coppola 2025 Cap.11)", TEXTO, SIN LOCALIZAR por mí); `pipeline/process_viirs.py:373` (`BT_LUT_MAX I04 361.77`); `pipeline/process_viirs_mod.py:182` (`M13 634.0`, comentario cita Campus 2022 Tabla 1, TEXTO).
- QUÉ PASA: en VIIRS 375 la BT de I04 clampea en 361,77 K, así que nunca supera 500 y el tope nunca anularía por saturación (y por 207 anula siempre). En VIIRS 750 un píxel real entre 500 y 634 K sería "imposible" y se anularía. Hoy: 0 records sobre 500 K; máximos 356 / 365 / 334 K.
- CÓMO SE VE EN EL DASHBOARD: invisible hoy.
- CÓMO REPRODUCIRLO: `grep -n "BT_PHYSICAL_MAX_K\|BT_LUT_MAX" pipeline/store.py pipeline/process_viirs.py pipeline/process_viirs_mod.py`.
- CONFIANZA: CONFIRMADO (latente).
- GRAVEDAD: 2.

### F2-212
- TÍTULO: La regresión del ETI hace refit iterativo a 3σ (SIN FUENTE) donde el código de MIROVA hace un `polyfit` único excluyendo los alertados; y el segundo pase reusa el ETI del primero.
- ARCHIVO:LÍNEA: `pipeline/detection_context.py:704-707` (`outlier_sigma 3.0`, `max_iter 3`, `min_pixels 10`), `:769-788`; `pipeline/process_viirs_mod.py:916` (`eti_for_second_pass = fp_diag.get("eti")`); MIROVA `.m` l. 328-345 (excluye `absoluteNTIalerts` y `previouslyDetectedAlerts`, exige 3 puntos, un `polyfit`, se recalcula en el segundo pase).
- QUÉ PASA: dos modos distintos de impedir que los píxeles calientes tuerzan la curva de fondo. El nuestro no excluye los alertados del ajuste y compensa con el refit a 3σ; el de MIROVA los excluye y no refitea. Y el segundo pase nuestro no recalcula el ETI (D34 ya lo anota).
- CÓMO SE VE EN EL DASHBOARD: en el dETI de cada píxel; magnitud del efecto SIN DATO.
- CÓMO REPRODUCIRLO: `sed -n 322,345p MIROVA_VIIRS750_hotspot_detection.m`; `sed -n 699,795p pipeline/detection_context.py`.
- CONFIANZA: CONFIRMADO (código); efecto SIN DATO.
- GRAVEDAD: 2.

### F2-236
- TÍTULO: Los N·σ de BT (5 / 10 / 15) son la columna C2 de la Tabla 1 aplicada a otra variable; camino apagado.
- ARCHIVO:LÍNEA: `pipeline/profile.py:194-203`; `pipeline/detection_context.py:607-610`.
- QUÉ PASA: ya rebajado en AUDIT_S146 V-08. Medido: `diag_n_bt_path > 0` en 0 records de la ventana K y 5 de MODIS en el corpus entero.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python experiments/_s160_audit/f2/rangos_chile.py` (`n_bt_path>0`).
- CONFIANZA: CONFIRMADO (inerte).
- GRAVEDAD: 2.

### F2-230 a F2-235 (forma, gravedad 1)
- F2-230. `pipeline/process_viirs.py:77`: la unidad declarada de `WOOSTER_COEFF` ("W/m² per (W/m²/sr/µm)") omite el área; con el área en m² la unidad del coeficiente es sr·µm. CONFIRMADO.
- F2-231. `frontend/index.html:928-929` usa 111,32 km/grado y `:2927-2928` usa 111,0 para el bbox MIROVA de 50 × 50 km: 72 m en 25 km. El pipeline usa 111,32 (`process_viirs.py:536-537`, `process_viirs_mod.py:404-405`, `process_modis.py:487-488`). CONFIRMADO.
- F2-232. Respaldo de `inner_radius_km` cuando el volcán no lo trae: 10 en `index.html:1162` y `mosaico.html`, 5 en `diario.html:265`. Los 11 volcanes listados lo traen (`index.html:728-769`, `diario.html:243-247`, `mosaico.html:217-227`, `auto_audit_weekly.py:115-117`: cuatro copias de la misma tabla). CONFIRMADO.
- F2-233. `LEVELS` (`index.html:792-799`) y `clase_por_vrp` (`clase_mirova.py:50-62`) tienen cinco clases con "Muy Alto" desde 1.000 MW; las leyendas `index.html:2465-2467` y `:3618-3621` tienen cuatro (">100 MW Alto"). CONFIRMADO.
- F2-234. Noche: `store.py:218` usa `solar_elev_deg <= 0`; `scripts/run_pipeline.py:118` usa `< 0.0`. Mismo cero con dos comparadores. El `dayflag` de MIROVA es una entrada del `.m`: cómo lo calcula, SIN DATO. CONFIRMADO.
- F2-235. `np.std` (N) en `detection_context.py:508-510` y `:927-929` donde el `.m` l. 304 y 374 usa `std(…, 0, 'omitnan')` (N−1). Con pools de 449 a 17.464 píxeles (p5 a p100 en K) la diferencia es menor que 0,1 %. CONFIRMADO.

## SEGUIMIENTOS (fuera de mi eje)

- SEG-1 (eje F1). `scripts/banco_paridad.py:75` fija `INICIO_DEFECTO = "2026-03-01"` con el comentario "cobertura CONS >= 99 % y OCR confiable desde marzo"; A119 (`CLAUDE.md`) dice que el OCR tuvo geometría mal calibrada hasta 2026-06-11 y sin distancia hasta 2026-06-13. La fecha está definida sobre la tabla y aplicada también al OCR. CONFIRMADO en el texto; el efecto es de F1.
- SEG-2 (D34, ya catalogada). `NTI_K1_NIGHT` −0,8 (`profile.py:87`, `yaml:47`) contra −0,7 del `.m` l. 178; hoy solo cuenta `n_nti_path` para el predicado del tope D9 (F2-208) porque el Test 1 está apagado.
- SEG-3 (D22, A/B S143). La compuerta `bt > t_bg + 3 K` (`profile.py:88`, `detection_context.py:546`) sigue encendida en los tres sensores (`apply_bt_gate=True`; `ENABLE_TESTS_23_NO_BT_GATE_VIIRS375=False`). SIN FUENTE en paper y en el `.m`. No es de unidades; la anoto porque su `t_bg` es el del anillo de F2-206.
- SEG-4 (forma, mantención). La tabla de `inner_radius_km` por volcán vive en cuatro copias (ver F2-232) más `volcanoes.yaml`; una divergencia futura no tiene guard que yo haya visto (no miré `tests/`).
- SEG-5 (cita). `pipeline/scan_geometry.py:141-144` cita Coppola 2016a "línea 201-202 + Eq.7" para el área nadir fija; es TEXTO del código, no lo verifiqué en RENDER.
- SEG-6 (observado en F2-206). La marca de PCC en `volcanoes.yaml` usa como `lat/lon` el centro de grilla de MIROVA y como `vent` el cráter de 2011; cualquier medición que use `dist` (centro) para PCC está desplazada 7,6 km respecto del cráter. Afecta a `hotspot_dist_km`, `diag_t_max_dist_km` y a los `anomaly_pixels`.

## VERIFICADO LIMPIO

- `WOOSTER_COEFF` 19,7 × 562.500 m² / 1e6 = 1,97e7 × 0,5625 / 1e6 de `MIROVA_VIIRS750_VRP.m` l. 88-91: idéntico (vara: el código de MIROVA). `sed -n 85,91p MIROVA_VIIRS750_VRP.m`; `sed -n 1054,1058p pipeline/process_viirs_mod.py`.
- C2 = 5 (cumbre) y 10 (escena) coinciden con `.m` l. 180-181 (vara: código de MIROVA; el defecto de 205 es el pool, no el valor).
- C1 de cumbre 0,003 para dNTI y dETI coincide con `.m` l. 184 y 187 salvo el factor del kernel (202).
- Área nadir fija en los tres sensores coincide con `pixelAreaKm2 = 0.5625` del `.m` l. 89 para VIIRS 750 (vara: código de MIROVA; para MODIS y V375 la vara es `CLAUDE.md`, no verificada).
- `F5_R_CORE_KM` 0,75 y `F5_BT_EXT_K` 295 idénticos en `pipeline/f5_core.py:40,42`, `index.html:1233-1234`, `diario.html:305-306`, `mosaico.html:295-296` (vara: paridad entre copias; la calibración S95 no la verifiqué).
- `SANITY_CAP` 50.000 idéntico en `store.py:68`, `index.html:1171,1182,1314`, `diario.html:272,368`, `mosaico.html:259,265,354`, `auto_audit_weekly.py:119`.
- `isCirrusArtifact` (273,15 K y 10 MW) y `isDiffuseFieldArtifact` (278,15 K) idénticos en las tres vistas y aplicados a `mirovaEqVrp` (pc), que es la magnitud con que se calibraron según el comentario `index.html:1316-1318`.
- Radio terrestre 6.371 km en `scan_geometry.py:42`, `clustering.py:23`, `f5_core.py:47`.
- Constantes de Planck `constants.py:23-24` con λ en µm en los tres procesadores y en `detection_context.py:673-681` (vara: coherencia interna).
- `vigilancia_sombra.py:59`: 1 − 0,9^29 = 0,953 (calculado: 0,9^29 = 0,047).
- `UMBRAL_PROTEGIDA_MW` 1,0 se aplica a la magnitud de MIROVA, no a la nuestra, y la comparación es "publicamos > 0" (`banco_paridad.py` `etiquetar`): el espacio es el correcto.
- Los pisos `MIN_VRP_MW_*` valen 0,0 en el perfil efectivo (A117): no recortan.
- Clamp de cenit a 70° (`scan_geometry.py:81`): 31 records K sobre 70° quedarían recortados, pero con área nadir fija el clamp no llega a ninguna magnitud.

## SIN DATO

- Efecto en píxeles de 205 (pool del segundo pase), 206 (fondo con el cráter adentro) y 212 (regresión): piden gránulos, no records. No reprocesé L1B por mandato.
- Si los mínimos del `.m` (V750) rigen también en VIIRS 375 y MODIS de MIROVA: no hay código publicado.
- Cómo calcula MIROVA `dayflag`.
- Cuántos cúmulos cambian de valor por el modo de un píxel (209): pide las sumas por píxel.
- El último `latest.json` del auto-audit (213): no está en la instantánea.
- Citas a papers: no rendericé ninguna página; todas las que menciono están marcadas TEXTO o SIN LOCALIZAR.

## FUERA DE ALCANCE

- Cifras de paridad contra la referencia (F1a/F1b); D17 (remuestreo) y D25 (fondo por vecinos) como decisiones; workflows y credenciales; `scripts/_archive/`, perfiles de A/B, `comparacion.html`, `tests/`.

## Archivos de esta carpeta

`censo_magnitudes.py` (instrumento, `--control`), `control_salida.txt`, `control_conteo_grep.csv`, `control_negativo_sin_constantes.py`, `censo_bruto.csv` (2.890 filas automáticas), `armar_censo.py` y `censo_magnitudes.csv` (todas las filas más las 64 revisadas a mano con unidad, espacios, fuente y rangos; `armar_censo_salida.txt`), `rangos_chile.py` con `rangos_chile.txt` y `.json`, `umbral_efectivo.py` con `umbral_efectivo_salida.txt`, `origen_distancia.py` con `origen_distancia_salida.txt`, `single_pixel_salida.txt`, `hallazgos.csv`. Pesado: `D:\vrp-trabajo\temporales\s160_audit\f2\perfil_efectivo.json`.
