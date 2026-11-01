# F0a: verificación de los 10 pendientes de S158 (gravedad 1 o 2) que nadie verificó

## Encabezado

- Hora del servidor al empezar: Thu, 22 Oct 2026 04:07:02 GMT; al cerrar la medición: 04:18:44 GMT (4 llamadas a la API
  de GitHub de 5 permitidas).
- Commit medido: `origin/main` = `d516b9d8c0fad5b0ca458b9fb57cdf5e6f75f956`, instantánea `D:\vrp-trabajo\temporales\s160_audit\main\`
  (código, datos de `data/mirova_equivalent/` y las dos referencias: `latest_consolidado.csv` sha256 `bc1522c24c924cb5…`,
  `data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv` sha256 `94679246acbd0db5…`).
- Modelo: Claude Fable 5.1, esfuerzo por defecto del subagente. Verificador con contexto limpio: no abrí los
  `INFORME.md` de S158 antes de sellar `caminos.md` (sha256 `e7e898e5aa2c3188…`, sellado 04:08:18 GMT); después leí sólo las
  secciones de cada hallazgo en las líneas que da `LISTA.md` (f1 l. 120 a 141, 166 a 179, 192 a 230; f6 l. 92 a 165) y lo declaro.
- CARPETA: `C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\f0a\`. Scripts con su salida al lado: `v01` a `v09`.
- Vara para «MIROVA hace X» en VIIRS 750: los dos `.m` de OSF zm62w en
  `experiments/_s158_d17_diseno/osf_codigo_mirova/` (H = `MIROVA_VIIRS750_hotspot_detection.m`, V = `MIROVA_VIIRS750_VRP.m`),
  leídos enteros en esta sesión; identidad con OSF comprobada en `v01_hash_osf_salida.txt` (los 6 archivos dan el sha256
  que OSF declara tras normalizar CRLF a LF; el crudo no coincide, así que el instrumento distingue).
- «Publica» = `scripts/banco_paridad.py::correr_node` sobre `frontend/index.html` del commit (A97), con control de
  identidad en `v02` (record vacío da 0, record summit de 0,5 MW da 1).
- Lo que NO miré: VIIRS 375 y MODIS (no hay código de MIROVA para ellos; todo lo de abajo es V750 salvo donde se dice);
  MATLAB (no está instalado; F6-5 se probó en GNU Octave 11.3); el CSV del OSF v2.5 (no está en disco y no gasté la API
  en bajarlo); el scraper Mirova-v1 en su fuente (cito el documento del repo que lo leyó); ningún L1B ni workflow.
- Búsqueda previa de cada ID en `experiments/_s159/` y en los otros frentes de S160 (f1a, f2, f3, f4, v2, v3): ningún
  frente de S160 cita estos IDs. `experiments/_s159/osf_codigo/INFORME.md` (ola 1 de S159) sí cita F1 H4, H6, H8 y H9
  en su tabla de 42 pasos y reproduce F1-H4 con el oráculo (su H5: 171 de 190 escenas); lo cito donde corresponde.

## En una pantalla

1. Los diez se sostienen con el código y los datos de hoy: 7 CONFIRMADOS, 3 CONFIRMADOS EN PARTE, 0 REFUTADOS. Ninguno
   estaba ya verificado por otro frente de S160.
2. Dos son más graves de lo que S158 anotó: **F1-H6** (gravedad 4, no 2: es el sustrato en K de D32, que el catálogo de
   `main` ya tiene con gravedad 4; cambia la magnitud publicada en 1 de cada 5 V750 publicados, 14 de 67 en producción K)
   y **F6-3** (gravedad 3: la decisión «el código manda sobre el paper» para V750 se apoya en un solo caso, Etna, que no
   ejercita K1, el 0,02 fuera de la cumbre ni la rama diurna; la validación en Octave de S159 compara port con original,
   no con un resultado publicado).
3. **F1-H4** se reproduce exacto por otro camino (83,4 % / 4,8 % en todo el corpus; 75,6 % / 6,2 % en producción K; varía
   de 75,9 a 93,9 % por volcán, así que el diagnóstico no es constante) y sigue sin adoptar: `DNTI_CONTEXTUAL_C1_SCENE =
   0.01` en `pipeline.profile`. Hoy mueve sólo píxeles `far` (1,5 % de las pasadas tienen alguno): gravedad 2.
4. **Hallazgo propio V0a-01, gravedad 3**: nada de S158 está en `main`. El PR #885 sigue ABIERTO (`gh pr view 885`:
   `state OPEN`, `mergedAt null`), `s158-d17-diseno` no es ancestro de `d516b9d8c`, y en la instantánea no existen
   `docs/AUDIT_S158.md`, `docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md` ni D34 en `docs/MIROVA_DIVERGENCES.md` (0 coincidencias
   en 3.220 líneas). Todo «ya catalogado en D34» de S158 y S159 vale en la rama, no en producción.
5. **F6-4** se estrecha: el scraper rotula `vrp <= 0` como RUTINA conservando el valor, y hay 0 negativos en las 42.410
   filas de la tabla y 0 en las 1.122 del OCR; el filtro que S158 sospechaba no está en el scraper (salvo que pierda el
   signo al leer, SOSPECHA), así que lo que no publica negativos es MIROVA o su paso de publicación.

## Veredictos, de mayor a menor gravedad propia

### F1-H6. Lo publicado es un cúmulo con modo de un píxel; MIROVA suma todos los alertados de la escena
- VEREDICTO: **CONFIRMADO**; además **YA CATALOGADO** en `main` como D32 (`docs/MIROVA_DIVERGENCES.md:3122`, «ABIERTA (registrada
  S147, verificada con contexto limpio, gravedad 4; prioridad MEDIA, no es la palanca del 0,7)», TEXTO). S158 lo dio como «el
  sustrato en K» de D32 y le puso gravedad 2; el catálogo le da 4 al fenómeno.
- ARCHIVO:LÍNEA: `pipeline/process_viirs_mod.py:1098-1130` (cúmulo `vent_anchored`, luego `apply_single_pixel_mode`);
  `pipeline/single_pixel_mode.py:5-6` («Si un cluster cae en regimen sub-MW (vrp_mw < threshold Y n_pixels ≤ max_pixels),
  reporta vrp_mw = max(per_pixel_vrp) (pixel mas caliente) en vez de la suma del cluster», TEXTO); MIROVA: V:83-85
  (`L_MIRhot = sum(ZI_M13(alert), 'omitnan')` sobre todos los índices de H:241-248, que concatena las tres regiones y los dos pases).
- SCRIPT:SALIDA: `v02_sustrato_v750.py` → `v02_sustrato_v750_salida.txt`, bloque F1-H6. Camino distinto al de S158: «publica»
  por `correr_node`, tres ventanas.
- QUÉ PASA: un foco que entibia dos o tres píxeles se informa por el más caliente; MIROVA suma los tres. Medido sobre los
  V750 publicados por el tablero: todo el corpus (2025-02-15 a 2026-10-21) 1.764 publicados, modo de un píxel en 1.732, con más
  de un píxel en 385; razón `pc.vrp_mw` / suma de todos los píxeles guardados (top-100 más descartados; ningún record con los
  100 llenos): mediana 1,000, p5 0,483, **< 0,9 en 419 (23,8 %)**. Producción K (desde 2026-09-18): 67 publicados, 52 en modo
  de un píxel (18 con más de un píxel), < 0,9 en **14 (20,9 %)**, p5 0,376. Reproduce los números de S158 (52 de 67, 18, 20,9 %).
  La razón se mide contra NUESTROS píxeles alertados, no los de MIROVA: es el efecto de la regla de suma sola, no la brecha total.
- CÓMO SE VE EN EL DASHBOARD: magnitud más baja en uno de cada cinco V750 publicados; no cambia si se publica.
- CÓMO REPRODUCIRLO: `python -I experiments/_s160_audit/f0a/v02_sustrato_v750.py` (lee la instantánea de D:).
- CONFIANZA: CONFIRMADO. GRAVEDAD PROPIA: **4** (mueve la magnitud publicada en producción; no la decisión de publicar).

### F6-3. Los umbrales de detección de VIIRS 750 no tienen contraste con ningún resultado publicado
- VEREDICTO: **CONFIRMADO** (en lo que se puede medir en disco); SIN DATO en el piso del OSF v2.5.
- SCRIPT:SALIDA: re-corrí `experiments/_s158_audit/f6/m15_etna_caminos.py` → `v08_m15_rerun_salida.txt`: «absolutas 0  pase1
  [box0, roi1, roi2] [0, 0, 4]  pase2 [0, 0, 1]  clase BOX de cada alerta: [2, 2, 2, 2, 2]», con el umbral de dNTI fuera de la
  cumbre en el piso 0,02 en los dos pases (`thr_dnti_box0_roi1: 0.02`) sin que ningún píxel lo cruce. O sea que K1 = −0,7
  (H:178), el mínimo 0,02 (H:183), los 10σ (H:180) y toda la rama diurna (H:188-199) no se ejercitan en el único caso con resultado
  de MIROVA. `v03_csv_referencia_salida.txt`: el NRT de Chile vive debajo del piso del OSF, tabla sola 297 de 315 alertas VIIRS 750
  bajo 5 MW (mediana 0,60), combinado 377 de 410 (ventana 2026-01-10 a 2026-10-21).
- Por otro camino: `experiments/_s159/o1/` validó el port contra Octave con el mismo `.mat`; eso compara port con original, no
  original con un resultado publicado, así que no cierra este hallazgo. Las 190 escenas chilenas de `_s159/osf_codigo` (su H5)
  muestran que fuera de la cumbre el piso 0,02 manda en 171 de 190: la palanca que no se puede contrastar es justo la que decide.
- Lo que NO pude medir: «piso de 5,00005 MW de noche y 50,0028 MW de día» en el OSF v2.5 (el CSV no está en disco; SIN DATO).
- CÓMO SE VE EN EL DASHBOARD: si se adoptan K1 = −0,7 y 0,02 fuera de la cumbre, cambian las alertas débiles de V750 sin medición
  que lo respalde; hoy no está adoptado (`NTI_K1_NIGHT = -0.8`, `DNTI_CONTEXTUAL_C1_SCENE = 0.01` en `pipeline.profile`).
- CONFIANZA: CONFIRMADO. GRAVEDAD PROPIA: **3** (mueve una decisión pendiente de adopción para V750: la regla «manda el código»
  del 2026-10-21 se apoya en un caso que no prueba esos números). S158 también le puso 3 pese a estar en la lista de 1 o 2.

### F1-H4. Fuera de la cumbre el mínimo de MIROVA en NTI es 0,02 (0,0225 en nuestras unidades) y decide en 3 de cada 4 pasadas; el nuestro (0,01) decide en 6 %
- VEREDICTO: **CONFIRMADO** (números reproducidos exactos por otro instrumento; no adoptado; no catalogado en `main`).
- ARCHIVO:LÍNEA: H:183 `minimumNTIcontrastROI1 = 0.02` y H:184 `minimumNTIcontrastROI2 = 0.003`, aplicados en H:306-312 con
  `max(μ + Nσ, mínimo)`; H:389-395: BOX 0 y BOX 1 usan el umbral ROI1 (el de 0,02), BOX 2 el ROI2. En el `.mat` la clase 2 es la caja
  central de 7 × 7 (`v05_box_mat_salida.txt`: filas y columnas 30 a 36, centro (33,33)), así que «ROI1» del código es FUERA de la
  cumbre. Nuestro: `DNTI_CONTEXTUAL_C1_SCENE = 0.01` (leído de `pipeline.profile` con `VRP_PROFILE=mirova_equivalent`, no del
  YAML); `pipeline/detection_context.py:525-533` (`combinar = max` con `ENABLE_TESTS_23_PROSE_BRANCH = True`).
- El 9/8: nuestro fondo local es la media de los 8 vecinos sin el centro (`detection_context.py:162-179`); el de MIROVA es la
  media 3 × 3 con el centro (H:281-287, `colfilt(..., [3 3], 'sliding', mean 'omitnan')`). Con los 8 vecinos válidos,
  x − (x + 8m)/9 = (8/9)(x − m): 0,02 de MIROVA equivale a 0,0225 en nuestras unidades. Vale exacto sólo con 8 vecinos válidos.
- SCRIPT:SALIDA: `v02_sustrato_v750_salida.txt`, bloque F1-H4 (28.580 records V750 Tier A con `diag_mu_dnti`/`diag_sd_dnti` del
  primer pase, ventana 2025-02-15 a 2026-10-21): μ + 10σ(dNTI) < 0,0225 en **83,4 %** y < 0,01 en **4,8 %**; desde 2026-03-01
  (n = 10.755) 84,5 % y 5,7 %; producción K (n = 1.552) **75,6 % y 6,2 %**; publicados K (n = 67) 53,7 % y 1,5 %. Por volcán
  (desde marzo) va de 75,9 % (Planchón Peteroa) a 93,9 % (Lastarria): el diagnóstico varía, no es constante. Idénticos a S158.
- Caminos de `caminos.md` comprobados: (1) misma variable, dNTI contextual en los dos; (3) nuestro σ sale del barrido nativo
  (D17), lo dice S158 y sigue siendo cierto; (6) no está adoptado ni en el perfil ni en el laboratorio; (7) S158 leyó la matriz,
  no el rótulo.
- Sustrato: records con algún píxel alertado (top-100 más descartados) fuera del `inner_radius_km`: 160 de 10.756 desde marzo
  (1,5 %), 21 de ellos publicados; en producción K 23 de 1.553, 2 publicados. SIN DATO si esos píxeles pertenecen al cúmulo publicado
  (el record no dice qué píxeles forman `primary_cluster`).
- CÓMO SE VE EN EL DASHBOARD: invisible salvo que un cúmulo cruce el borde del inner (no medible desde el record).
- CONFIANZA: CONFIRMADO. GRAVEDAD PROPIA: **2** (mueve píxeles `far` que el tablero oculta; sube a 3 si un A/B de D18 o de la
  caja de 5 × 5 km los vuelve publicables).

### F6-8. La dilatación del fondo también agranda los huecos que ya trae M13, y los TIF de MIROVA traen huecos
- VEREDICTO: **CONFIRMADO**, y el sustrato es mayor que el que S158 midió.
- ARCHIVO:LÍNEA: V:76-78 `exclusionMask = imdilate(isnan(ZI_M13masked), strel('square', kernelSize))`: dilata TODO NaN, no sólo
  los alertados (V:64-65 los puso a NaN antes); V:81 `fillmissing2(..., 'linear')` rellena después.
- SCRIPT:SALIDA: `v07_tif_nan.py` → `v07_tif_nan_salida.txt`. Leí los **653** GeoTIFF VIIRS750 locales de `mirova-tif-archive`
  (sin pull, feedback S143; sin `_lm`), no sólo los 5 de S158: los 653 son 67 × 67, EPSG:4326, `TIFFTAG_SOFTWARE = MATLAB
  R2024b, Mapping Toolbox 24.2`, md5 únicos; **653 de 653 traen NaN** (mediana 29, mín 6, máx 4.452); **27 tienen NaN dentro de
  la caja central de 7 × 7** y 45 dentro del anillo de 21 × 19. Control: un NaN forzado en (33,33) se cuenta. Los 5 de S158 dan 21,
  163, 42, 44, 24 y 48 (S158 dijo «entre 14 y 70»: Isluga 163 no cabe; no persigo la diferencia, puede ser `nodata`).
- SOSPECHA que hereda de S158: estos TIF son EPSG:4326 (A106: la grilla UTM nativa duró 8 adquisiciones en septiembre), o sea
  remuestreados; parte de los huecos puede ser del remuestreo, no de `ZI_M13`.
- Qué mueve: nada en producción (`ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750 = False`, nuestro fondo es la mediana del anillo); sí al
  oráculo y al brazo de D25 que imitan el fondo de MIROVA: `_s158_oraculo_mirova/mirova_v750.py:214-216` dilata igual y deja NaN
  fuera de la envolvente de `griddata` («SUPUESTO DECLARADO», l. 20-23).
- CONFIANZA: CONFIRMADO (código y conteo); SOSPECHA (que los TIF sean `ZI_M13`). GRAVEDAD PROPIA: **2** (toca el A/B pendiente de
  D25 por el lado del oráculo; 27 escenas con hueco junto al cráter en 653).

### F6-4. El código no recorta ΔL, pero MIROVA nunca publica una alerta con VRP nulo o negativo
- VEREDICTO: **CONFIRMADO EN PARTE**: la parte factual se reproduce en las dos referencias y el «filtro» se estrecha; sigue SIN
  DATO dónde está.
- ARCHIVO:LÍNEA: V:83-91 (`deltaL_MIR = L_MIRhot - L_MIRbk` y `VRP_MW = deltaL_MIR .* 1.97e7 .* 0.5625 ./ 1e6`, sin `max(…, 0)`).
  Nuestro: `pipeline/process_viirs_mod.py:1056` `delta_L = np.maximum(L_hot - L_bg_rad, 0.0)` (recorta).
- SCRIPT:SALIDA: `v03_csv_referencia_salida.txt` (tabla sola: VIIRS 315 alertas, mín 0,090, ≤ 0: **0**; combinado: 410, ≤ 0: **0**;
  VIIRS375 1.231 / 2.123 con mín 0,010; MODIS 109 / 150 con mín 0,130; **0 filas de cualquier tipo con VRP < 0** en 42.410 de la
  tabla y 1.122 del OCR). `v06_rutina_no_cero_salida.txt`: RUTINA 39.827, con VRP == 0 39.813; las 14 con VRP ≠ 0 son todas de
  2026-01-10 a 01-14 (scraper inestable, A119), positivas.
- Lo nuevo: el scraper rotula `vrp <= 0` como RUTINA conservando el valor (`docs/audit_s139/EJE_1_semantica_etiquetas_referencia.md`
  l. 43, TEXTO: «`Tipo_Registro = RUTINA` | `vrp <= 0` (`scraper.py:153-154`)»; no leí `scraper.py`). Una alerta negativa servida por
  MIROVA aparecería como RUTINA con VRP negativo, y hay 0 en 39.827. El filtro no está en el scraper, salvo que pierda el signo al
  leer la tabla (SOSPECHA, no verificable sin el scraper).
- CÓMO SE VE EN EL DASHBOARD: invisible hoy (recortamos); si se copia «sin recorte» literal, alertas de VRP ≤ 0 que MIROVA no muestra.
- CONFIANZA: CONFIRMADO lo factual; SOSPECHA el mecanismo. GRAVEDAD PROPIA: **2** (toca el brazo «sin recorte» de D25).

### F1-H9. Un record sin detección vale 0,0 MW; MIROVA lo declara NaN y advierte que no es emisión cero
- VEREDICTO: **CONFIRMADO**, con un matiz que lo acota.
- ARCHIVO:LÍNEA: V:19-22 («An empty ALERT produces VRP_MW = NaN, not zero. No detected alert does not demonstrate zero emission»,
  TEXTO) y V:45-52; README.txt:70-72. Nuestro: `pipeline/process_viirs_mod.py:1027` `vrp_mw = 0.0`; `pipeline/store.py:359`
  `vrp_eruption = record.get("vrp_mw", 0) or 0` (el `or 0` convierte 0,0 en el entero 0, de ahí el `int:0` de abajo);
  `frontend/index.html:1028` `if (v == null) continue;` (toDailyMax salta sólo `null`, un 0 entra como punto de altura 0).
- SCRIPT:SALIDA: `v02_sustrato_v750_salida.txt`, bloque F1-H9: **25.848 de 28.581** records V750 sin detección, todos con
  `vrp_mw` = 0 (entero), `primary_cluster` None, ningún campo de nube o cobertura (`cloud_fraction`, `coverage`, … ausentes en
  todos), 0 publicados por node.
- El matiz: una escena sin anillo suficiente no se escribe: `process_viirs_mod.py:568` `if t_bg is None: return None` y
  `scripts/run_pipeline.py:336` `if result:` antes de `append_record`. O sea que «sin fondo» ya es ausencia y no cero; el 0 cubre
  sólo «miró con fondo y no alertó», nublado o no. Para `banco_paridad` (que etiqueta por pareo de pasada) el 0 y la ausencia
  pesan igual, «no publica»; la diferencia muerde a un consumidor que promedie o grafique la serie. En las tres vistas no hay
  promedios (`grep` en `diario.html` y `mosaico.html`: sólo `reduce(... Math.max ...)`).
- CÓMO SE VE EN EL DASHBOARD: invisible (barra de altura 0).
- CONFIANZA: CONFIRMADO. GRAVEDAD PROPIA: **1** (de forma; sube si algún consumidor externo promedia los JSON).

### F1-H8. Diferencias de entrada sin sustrato medible desde los records
- VEREDICTO: **CONFIRMADO EN PARTE**: los tres «no se persiste» y los proxies se reproducen; el sesgo de −0,55 % es de modelo.
- ARCHIVO:LÍNEA: `process_viirs_mod.py:244-253` (BT de M13 por `M13_brightness_temperature_lut`, `float32`), `:278-286` (M15 ídem),
  `:352-355` (`bt_to_spectral_radiance`, Planck con `C1 = 1.191042e8`, `C2 = 14388.0` de `pipeline/constants.py:20-21`); MIROVA
  recibe radiancia (H:19-23) y usa h 6,6256e-34, c 2,9979e8, k 1,38e-23 (H:410-412).
- SCRIPT:SALIDA: `v09_h8_proxies_salida.txt` (loader propio): V750 Tier A 28.581 records; `t_max_k` máximo **364,86 K**; `t_bg_k`
  mínimo 207,55 K; `t_bg < 220 K` en **44 de 28.581**; ningún campo con «M15», «TIR» ni «sat» en el nombre. Reproduce S158.
- Lo que no se puede medir sigue sin poderse: BT de M15 y píxeles saturados (anulados antes de llegar a `t_max_k`). El −0,55 % a
  240 K depende de una respuesta espectral rectangular supuesta: SOSPECHA, como S158 lo marcó. Por otro camino,
  `_s159/osf_codigo/INFORME.md` filas 9 y 11 midió sobre 190 escenas chilenas 0 píxeles de M15 ≤ 200 K y 0 escenas rechazadas
  por mitad NaN (y 66 y 25 de 600 sintéticas, control). No re-medí el proxy «64 de 1.553 bajo 50 % de cobertura» (exige el p95
  por clase de cenit; SIN DATO).
- CONFIANZA: CONFIRMADO lo que falta; SOSPECHA el número. GRAVEDAD PROPIA: **1**.

### F6-5. La función de VRP probablemente falla, en vez de devolver NaN, cuando la detección rechazó la escena
- VEREDICTO: **CONFIRMADO en GNU Octave 11.3; SOSPECHA en MATLAB** (no instalado).
- ARCHIVO:LÍNEA: V:42-43 `validateattributes(alert, {'numeric'}, {'real','vector','integer','positive'}, …)` corre antes del
  `isempty` de V:50; H:81 `alert = [];` con `return` en H:88 (sun-glint) y H:166 (mitad NaN); `Example/run_example.m:27-28` llama a
  la función de VRP sin condicionar.
- SCRIPT:SALIDA: `v04_vacio_octave.m` → `v04_vacio_octave_salida.txt`: `size([]) = 0x0`, `size(find(zeros(3))) = 0x1`,
  `isvector([]) = 0`; **0x0 → `ERROR: Octave:expected-vector | MIROVA_VIIRS750_VRP: alert (argument #2) must be vector`**;
  **0x1 → `VRP_MW = NaN, npix = 0` sin error**; la detección con `sunglint = 5` devuelve `0x0`; con el ejemplo devuelve 5 × 1
  (Etna, 5 alertas, como el oráculo). Control: índice fuera de rango da `MIROVA:InvalidAlertIndex`.
- Consecuencia: con el código tal cual, el NaN documentado (V:19-22) sólo se alcanza en escena aceptada sin alertas; en escena
  rechazada el ejemplo oficial falla. El oráculo del proyecto devuelve NaN en los dos casos (más permisivo), como dijo S158.
- CÓMO SE VE EN EL DASHBOARD: invisible (no toca nuestro pipeline).
- CONFIANZA: CONFIRMADO en Octave; SOSPECHA en MATLAB (`validateattributes` puede tratar el 0 × 0 distinto). GRAVEDAD PROPIA: **1**.

### F6-7. Algunos comentarios afirman efectos que el código no tiene
- VEREDICTO: **CONFIRMADO** en (a) y (b).
- (a) H:434 `firstRadiationConstant = 2 * 3.14 * h * (c^2)` y H:443 `L = spectralExitance ./ 3.14`: el 3,14 se multiplica y se divide,
  se cancela salvo redondeo; el comentario H:427-428 («intentionally preserved to maintain numerical consistency») atribuye un
  efecto que no existe.
- (b) H:111 llama a `BOX == 1` «central volcanic ROI» y H:115 a `BOX == 2` «extended volcanic ROI». `v05_box_mat_salida.txt`:
  clase 2 n = 49, filas 30 a 36 y columnas 30 a 36 (caja de 7 × 7 centrada en (33,33)); clase 1 n = 350, filas 22 a 42 y columnas
  24 a 42 (21 × 19); clase 0 n = 4.090. Exacto lo que dijo S158.
- Propagación (camino 1 de `caminos.md`): la memoria `reference_codigo_mirova_osf.md` y `_s159/osf_codigo/INFORME.md` §1 leen la
  matriz, no el rótulo. Bien.
- CONFIANZA: CONFIRMADO. GRAVEDAD PROPIA: **1**.

### F6-6. El README describe otro empaquetado que el depositado
- VEREDICTO: **CONFIRMADO**.
- ARCHIVO:LÍNEA: README.txt:15-18 lista `example/VIIRS750_example.mat`, `example/run_example.m`, `CITATION.cff`, `LICENSE`;
  README.txt:30 `load('example/VIIRS750_example.mat')`. En disco y en OSF (`v01_hash_osf_salida.txt`, `osf_metadatos_codigo.txt`):
  `Example/` con mayúscula, `CITATION.txt`, `LICENSE.txt`. `run_example.m:8-12` arma la ruta con `fileparts` y `fullfile`, así que
  el ejemplo corre; el fragmento del README no, en un sistema que distingue mayúsculas.
- Camino 1 de `caminos.md` (versión posterior): los 6 archivos están en `current_version 1` y el log de OSF sólo trae renombres de
  carpetas y de cita después del 2026-07-24 (`_s159/osf_codigo/INFORME.md` §5); no hay otra distribución en OSF.
- CONFIANZA: CONFIRMADO. GRAVEDAD PROPIA: **1**.

## Hallazgos propios

### V0a-01. Nada de S158 está en `main`: el PR #885 sigue abierto, y el catálogo de producción no tiene D34
- ARCHIVO:LÍNEA: `gh pr view 885 --json state,mergedAt,mergeCommit` → `state OPEN`, `mergedAt null`, `headRefName
  s158-d17-diseno`; `git merge-base --is-ancestor origin/s158-d17-diseno d516b9d8c` → NO es ancestro; en la instantánea de SHA_MAIN
  `ls docs | grep S158` vacío y `grep -n D34 docs/MIROVA_DIVERGENCES.md` 0 de 3.220 líneas. `experiments/_s158_d17_diseno/`,
  `_s158_audit/` y `_s158_oraculo_mirova/` existen sólo en el worktree.
- QUÉ PASA: la memoria del proyecto (`reference_codigo_mirova_osf.md`: «Copia con hashes en … (rama s158-d17-diseno, PR #885)
  … catálogo D34») y `_s159/osf_codigo/INFORME.md` (24 de 29 pasos «ya tienen D en el catálogo») hablan como si D34 fuera parte del
  catálogo vivo. En `main` no está: una sesión fría que lea `docs/MIROVA_DIVERGENCES.md` de producción no encuentra la divergencia
  K1 −0,7 / 0,02 / 3 × 3 con central / fondo `fillmissing2`, ni la decisión «manda el código».
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: los tres comandos de arriba desde `C:\vrp-trabajo\s159-pruebas`.
- CONFIANZA: CONFIRMADO. GRAVEDAD: **3** (A113: un cierre o una divergencia que vive sólo en una rama abierta es un cierre que
  la siguiente auditoría vuelve a reportar como nuevo; es exactamente el motivo de esta lista).

### V0a-02. `vrp_mw` queda como entero 0 en los records sin detección por el `or 0` de `store.py:359`
- ARCHIVO:LÍNEA: `pipeline/store.py:359` `vrp_eruption = record.get("vrp_mw", 0) or 0`, luego `:456` `round(max(vrp_eruption,
  vrp_vent), 3)`; `v02_sustrato_v750_salida.txt`: 25.848 de 25.848 con `int:0`.
- QUÉ PASA: forma; `0.0` es falso en Python y el `or` lo reemplaza por el entero. No cambia ningún predicado (`> 0` da lo mismo).
- CONFIANZA: CONFIRMADO. GRAVEDAD: **1**.

### V0a-03. El ejemplo oficial del OSF falla en escena rechazada (parte de F6-5, lo separo porque es del paquete, no de la función)
- ARCHIVO:LÍNEA: `Example/run_example.m:23-28`: llama `MIROVA_VIIRS750_VRP(S.ZI_M13, alert)` sin `if ~isempty(alert)`; con
  `sunglint < 12` la detección devuelve `0x0` (`v04_vacio_octave_salida.txt`) y la función de VRP lanza error (en Octave).
- CONFIANZA: CONFIRMADO en Octave; SOSPECHA en MATLAB. GRAVEDAD: **1**.

## SEGUIMIENTOS (fuera de mi eje, reproducibles)

1. `experiments/_s158_oraculo_mirova/mirova_v750.py:187-199` (`_fillmissing2_linear` con `griddata`): deja NaN fuera de la
   envolvente convexa; si un píxel alertado quedara con fondo NaN, V:84 lo omite de `L_MIRbk` y no de `L_MIRhot` (V:83) y el VRP
   sube. No ocurre en el ejemplo (marco excluido en H:102-103 y alertas interiores); puede ocurrir con huecos de M13 grandes
   (27 de 653 TIF con NaN en la caja central). SOSPECHA, gravedad 2, toca D25 y O2 («`fillmissing2` real pendiente en MATLAB»).
2. Los 5 TIF de S158 dan 21, 163, 42, 44, 24 y 48 NaN con `rasterio` contra «entre 14 y 70» de F6-8: Isluga 163 no cabe. Puede ser
   `nodata` distinto de NaN o un archivo re-servido. `v07_tif_nan_salida.txt`. Gravedad 1.
3. 14 filas RUTINA con VRP > 0 en la tabla, todas del 2026-01-10 al 01-14 (`v06_rutina_no_cero_salida.txt`): sustrato de A119
   («inestable hasta el 2026-02-24»), no es nuevo; lo dejo porque `banco_paridad.etiquetar` (l. 310) exige `vrp_mw == 0` para
   `rutina_pasada`, así que esas 14 no cuentan como RUTINA ahí. Gravedad 1.

## VERIFICADO LIMPIO

| qué | vara | cómo |
|---|---|---|
| La copia local del código OSF es la publicada | sha256 de la API de OSF (`f6/osf_metadatos_codigo.txt`) | `v01_hash_osf_salida.txt`: 6 de 6 iguales tras CRLF → LF; el crudo no coincide (control) |
| `correr_node` ve la diferencia entre un record vacío y uno publicable | predicado del tablero | `v02`: 0 y 1 |
| Los `diag_mu_dnti` / `diag_sd_dnti` no son constantes | variación por volcán | `v02`: 75,9 a 93,9 % |
| El oráculo reproduce el ejemplo de OSF | `m15` de S158 re-corrido | `v08`: 5 alertas, VRP 9,8809 MW, `L_hot 1.96534218` |
| Octave corre la detección del `.m` y da lo mismo que el oráculo en Etna | `.m` original | `v04`: 5 alertas 5 × 1 |
| Perfil de producción: C1 fuera 0,01, K1 −0,8, `max`, Test 1 integrado apagado, D25 apagado, rama diurna apagada | `pipeline.profile` de SHA_MAIN | volcado en esta sesión (no del YAML) |

## SIN DATO

- Piso de 5 MW del OSF v2.5 (F6-3): el CSV no está en disco.
- Comportamiento de `validateattributes` con `[]` en MATLAB (F6-5): sin MATLAB.
- Si los píxeles fuera del inner forman parte del cúmulo publicado (F1-H4): el record no guarda qué píxeles son el `primary_cluster`.
- Si el scraper pierde el signo al leer un VRP negativo (F6-4): no leí `scraper.py`.
- Proxy «64 de 1.553 bajo 50 % de cobertura» (F1-H8): no re-medido.

## FUERA DE ALCANCE

VIIRS 375 y MODIS; reprocesos; workflows; cualquier arreglo. Nada fuera de CARPETA se tocó (las copias de los `.m` y el `.mat`
sólo se leyeron).
