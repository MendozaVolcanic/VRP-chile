# F4 (S160): cierres y reglas con número escritos o modificados desde S146

## 1. Encabezado

- **Hora del servidor**: `Date: Thu, 22 Oct 2026 03:11:55 GMT` (`experiments/_s160_audit/insumos/hora_servidor.txt`, bajado por el orquestador). Mi propia llamada `gh api /rate_limit --include` no devolvió cabeceras en esta shell (0 de las 10 llamadas permitidas consumidas con resultado); las salidas de mis scripts llevan la hora del reloj local (censo: 2026-10-22T03:17 UTC).
- **Commit auditado**: `origin/main = d516b9d8c0fad5b0ca458b9fb57cdf5e6f75f956`, leído en la instantánea `D:\vrp-trabajo\temporales\s160_audit\main\` (código, datos y las dos referencias: `latest_consolidado.csv` sha256 `bc1522c24c924cb5…`, `registro_vrp_ocr.csv` sha256 `94679246acbd0db5…`, comprobados con `sha256sum`). El delta: `git log -p 61cc94e3a..d516b9d8c -- CLAUDE.md docs/MIROVA_DIVERGENCES.md docs/MISSION.md docs/META_RULES_S80.md docs/SINTOMAS.md` = 25 commits, 1.604 líneas insertadas, 46 borradas (`delta_docs.patch`, `delta_docs_solo_agregadas.txt`). `META_RULES_S80.md` no cambió.
- **Modelo y esfuerzo**: Fable 5.1, `high`.
- **CARPETA**: `C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\f4\` (pesado en `D:\vrp-trabajo\temporales\s160_audit\f4\`). Disco al cierre: C: 14 GB, D: 9,9 GB libres.
- **Qué NO miré**: (a) no reprocesé L1B ni despaché workflows; los números de K (`experiments/_s153_fk_v2/`) los verifiqué en el archivo citado, no re-corriendo el evaluador, que es el objeto de F1a; (b) los números heredados de S146 y S147 (A82, A83, A99, D13, D16, D20, D30, D31, D32, V-05, V-06) los clasifiqué como «heredados, verificados por el verificador de su sesión», sin re-medirlos; (c) de `docs/SINTOMAS.md` no verifiqué las cifras que citan la rama `loop/activo` (C53 de `cierres_delta.csv`); (d) no leí la rama `loop/activo` más allá de los pendientes U1 a U13 y F2-H3 a H9; (e) la memoria del agente la leí sólo donde el grep de una rebaja la alcanzó; (f) no verifiqué D17 marca S157 (F_bg 0,85 a 0,73) ni D18 «neto cero en 8 volcanes» ni D33 «96 de 96 bit a bit».

## 2. En una pantalla

1. **H4 se confirma por las dos vías.** De 58 afirmaciones del delta (`cierres_delta.csv`): 15 verificadas, 14 en parte, 4 refutadas, 3 SIN EVIDENCIA, 3 SIN VERIFICAR o SIN DATO, 2 no eran cierres, 17 heredadas de S146/S147 sin re-medir. **Ninguna afirmación que sostenga K cayó** (C01 a C05 se leen en los logs citados).
2. **Lo peor no es un número: es un cambio de régimen que no bajó a nadie.** #883 (en main) reemplazó el histórico entero con K (`DATOS_K_DESDE_UTC = 2025-02-15`; 0 `triggered_test1` en 74.811 records) y `MISSION.md:22-24`, `CLAUDE.md:127`, `SINTOMAS.md:9,19-21,198` y el catálogo siguen diciendo «C0 antes del 2026-09-18, la frontera se moverá cuando se aplique el reproceso» (281, gravedad 5).
3. **Tres números que deciden la evaluación de la réplica ya no se reproducen o nunca tuvieron script entero**: D-4 439/992 (hoy 478/1.055, sin ventana ni hash; 283), D-9 «14 pasadas NONE» (7 del script, 7 de una lectura manual; 284), tope D9 1.565/343 (hoy 16/183 bajo K; 282).
4. **Propagación**: 14 rebajas barridas, 499 hijos; los que se leen primero (`CLAUDE.md`, `MISSION.md`, catálogo, `INDEX.md`) están marcados salvo tres (A118 «D18 nunca se ha medido», `CLAUDE.md:1530`; `README.md` de main con el Test 1 integrado vivo; y todo lo de S158, que no existe en main). La memoria del agente, que se carga en cada sesión, conserva cinco cierres rebajados sin marca (288).
5. **Control positivo**: A83 sale clasificada REBAJADA con marca en `CLAUDE.md:1072`; el instrumento falló la primera vez (ventana de 3 líneas) y se corrigió a «pasaje envolvente» (§6).

## 3. Hallazgos (281 a 297), de peor a mejor

### 281. El reemplazo del histórico con K no bajó a ningún documento rector
- **ARCHIVO:LÍNEA**: `docs/MISSION.md:22-24` («los 30 días previos al merge se reescribieron con K … la frontera se moverá más atrás cuando se aplique el reproceso histórico con K»), `CLAUDE.md:127` y `:190` («en los datos desde la observación del 2026-09-18»), `docs/SINTOMAS.md:9` («C0 antes del 2026-09-18, K después»), `:19-21`, `:109`, `:198`; `docs/MIROVA_DIVERGENCES.md:1444`, `:1507`, `:1640`. Todos en main `d516b9d8c`.
- **QUÉ PASA**: el fenómeno: todo el histórico de los 11 Tier A ya está detectado con K (sin Test 1 integrado, `max`, banda 22), así que cualquier serie, A/B o auto-audit que «estratifique por régimen» en la fecha 2026-09-18 compara K contra K. El código: `8471add46` (#883, S158 1.24, 2026-10-21) reemplazó `data/mirova_equivalent/*.json`, apartó C0 en `data/_c0_residuales/` y puso `DATOS_K_DESDE_UTC = "2025-02-15T00:00:00Z"` (`frontend/cambio_detector.js:32`); el commit no tocó ningún `.md` rector (`git show --stat 8471add46`). Medido: 70.915 records anteriores al 2026-09-18 con 0 `triggered_test1` y 0 `final_hotspot_source` en `test1`/`test1_roi` (`mis_conteos_salida.txt` §1). A85 marca S153 («records MODIS de enero a junio de 2026 escritos con los gates intra-radio encendidos»), A104 y D11/D12 marcas S157 («0 de 3.661 procesados después del merge») describen datos que ya no están en main.
- **CÓMO SE VE EN EL DASHBOARD**: la marca del detector del tablero ya está en 2025-02-15 (correcto); lo invisible es documental: una sesión que lea `MISSION.md` estratifica en una frontera que no existe.
- **CÓMO REPRODUCIRLO**: `git -C C:\vrp-trabajo\s159-pruebas show --stat 8471add46 | grep -v data/`; `grep -n "2026-09-18" D:\vrp-trabajo\temporales\s160_audit\main\docs\MISSION.md`; `python -I mis_conteos.py D:\vrp-trabajo\temporales\s160_audit\main`.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD 5** (sostiene la lectura de los datos de producción y de toda métrica por régimen; la vigilancia #863 y el auto-audit por detector #862 heredan la premisa, SOSPECHA no medida).
- **Marca propuesta** (al inicio de la marca S157 de `docs/MISSION.md`, y copia en `CLAUDE.md:122`, `docs/SINTOMAS.md:17-21` y las tres marcas del catálogo): «⚠️ **S160 (F4-281)**: desde #883 (`8471add46`, 2026-10-21) el histórico de los 11 Tier A está reprocesado con K y `DATOS_K_DESDE_UTC` es 2025-02-15; los records C0 viven en `data/_c0_residuales/`. Toda frase de abajo que diga «antes del 2026-09-18 los datos son C0» describe el estado entre #860 y #883. Texto conservado por historia.»

### 282. El tope D9 de 5 MW casi no actúa bajo K, y las marcas S151 que lo cuantifican ya no se reproducen
- **ARCHIVO:LÍNEA**: `CLAUDE.md:381-390` (A23 marca S151: «Corpus al 2026-10-14 (65.705 records): 1.565 cúmulos topados en 5,0 exacto (277 summit) … 343 cúmulos sobre 5 MW (110 summit)»), `docs/MISSION.md:134-140`, `docs/MIROVA_DIVERGENCES.md:221-235` (y «en Nevados de Chillán … el tope actuó en 7 pasadas MODIS entre el 2026-09-28 y el 2026-10-13, todas `far`»), `docs/SINTOMAS.md:85-87`.
- **QUÉ PASA**: el fenómeno: el tope recorta magnitudes del camino contextual sobre fondo frío; con K (sin Test 1, `max`) ese sustrato se achicó. SCRIPT:SALIDA: el mismo `contar_topados_d9.py` sobre el corpus de hoy (74.811 records, 2025-02-15 a 2026-10-21) da 16 topados (15 `summit`, 11 de Láscar) y 183 sobre 5 MW; en Chillán MODIS 2026-09-28 a 10-13, 0 de 31 pasadas con `d9_capped` (`mis_conteos_salida.txt` §2); la copia del script de D33 cuenta 1 capado entre 582 records K con magnitud. No es una refutación de S151 (A90: su corpus era el del 2026-10-14, anterior a #883); lo que falta es la marca y la re-medición: la «cara de co-validación del path D» que S146 reabrió se midió entera bajo C0.
- **CÓMO SE VE EN EL DASHBOARD**: hoy 16 records con magnitud exactamente 5,0 en toda la serie; antes 1.565. El operador ve menos techos de 5 MW, sin que nadie lo haya escrito.
- **CÓMO REPRODUCIRLO**: `cd D:\vrp-trabajo\temporales\s160_audit\main && python -I C:\vrp-trabajo\s159-pruebas\experiments\_s150_meta_audit\verif_docs\contar_topados_d9.py` (salida en `t1_contar_topados_d9_salida.txt`).
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD 4** (frente D9 abierto, medido bajo un detector que ya no corre).
- **Marca propuesta** (A23, D9 S151, MISSION): «⚠️ **S160 (F4-282)**: los 1.565 y 343 son del corpus C0 del 2026-10-14. Sobre el corpus K de `d516b9d8c` (74.811 records) el mismo script da 16 topados y 183 sobre 5 MW; en Chillán 0 de 31. La cara de co-validación de D9 está sin medir bajo K.»

### 283. D-4: «439 pasadas» y «992» no llevan ventana ni hash, y hoy son 478 y 1.055
- **ARCHIVO:LÍNEA**: `docs/MISSION.md:60-66`, `CLAUDE.md:1695` (glosario Recall), `docs/S151_CRITERIO_CLASE_MIROVA.md:87,109,111`.
- **QUÉ PASA**: la referencia crece hacia adelante y pierde filas hacia atrás (S159: carrera de workflows del scraper). SCRIPT:SALIDA: `scripts/clase_mirova.py` del propio commit, sobre las dos referencias congeladas, da «pasadas protegidas, lectura A: 478 (VIIRS375 247, VIIRS750 162, MODIS 69); lectura B: 1055» (`t1_clase_mirova_salida.txt:23-24`). El número de la decisión D-4 no tiene denominador temporal (A90) y la definición sí lo exige.
- **CÓMO SE VE EN EL DASHBOARD**: invisible; decide cuántas alertas son «protegidas» en toda evaluación de la réplica.
- **CÓMO REPRODUCIRLO**: `cd D:\vrp-trabajo\temporales\s160_audit\main && python -I scripts\clase_mirova.py --cons latest_consolidado.csv --ocr data\mirova_reference\mirova_v1_snapshot\registro_vrp_ocr.csv`.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD 4**.
- **Marca propuesta** (MISSION criterio, punto 1): «⚠️ **S160 (F4-283)**: 439 y 992 son conteos sobre el CSV del 2026-10-14 sin hash; sobre la referencia congelada de `d516b9d8c` (bc1522c2 / 94679246) dan 478 y 1.055. El criterio es la definición, no el número.»

### 284. D-9: de las «14 pasadas NONE con 0,04 MW o menos» sólo 7 salen de un script
- **ARCHIVO:LÍNEA**: `docs/MISSION.md:106` («el banner de MIROVA dice NONE en las 14 pasadas observadas de 0,04 MW o menos y VERY LOW en las de 0,06 MW o más; en 0,05 exacto sale de los dos lados»), `CLAUDE.md` glosario Recall (marca D-9), `experiments/_s151_alertas_minimas/README.md:32-36`.
- **QUÉ PASA**: el fenómeno: la regla SN decide que una alerta de 0,05 MW o menos cuenta como «MIROVA no vio nada», o sea mueve el recall de toda evaluación. El instrumento: `frontera_banner.py` sobre el OCR da NONE 2 en 0,02, 1 en 0,03, 4 en 0,04 (7), 2 NONE y 3 VERY_LOW en 0,05, 8 VERY_LOW en 0,06 (`frontera_salida.txt:4-9`). El README dice que el 14 junta «el OCR de Mirova-v1 y una lectura propia de las imágenes de mayo» y el «5 y 5» en 0,05 tampoco es el 2 y 3 del script. La mitad del sustrato de la frontera es una lectura manual sin archivo.
- **CÓMO SE VE EN EL DASHBOARD**: invisible; cambia la etiqueta de recall en los A/B.
- **CÓMO REPRODUCIRLO**: `type experiments\_s151_alertas_minimas\frontera_salida.txt`; `sed -n 30,38p experiments\_s151_alertas_minimas\README.md`.
- **CONFIANZA**: CONFIRMADO en el conteo; SOSPECHA de que la lectura manual no esté en ningún archivo (busqué `censo_salida.txt`, `cotejar_salida.txt`, `extraer_salida.txt` por nombre, no los leí).
- **GRAVEDAD 4**. **Marca propuesta** (MISSION punto 5): «⚠️ **S160 (F4-284)**: de las 14, 7 están en `frontera_salida.txt`; las otras 7 y el «5 y 5» son lectura manual de mayo sin instrumento persistido. La frontera 0,045 a 0,06 se sostiene con 7 casos del script.»

### 285. A118 sigue diciendo «D18 nunca se ha medido» sin marca
- **ARCHIVO:LÍNEA**: `CLAUDE.md:1530` («D18 nunca se ha medido, y el «NO ADOPTAR» de S130 probablemente salió de este mismo defecto (SOSPECHA)»); la medición: `docs/MIROVA_DIVERGENCES.md:2300-2308` (marca S151: «KC NO CUMPLE (veto) en D1»); `docs/SINTOMAS.md:160` ya dice que ese «nunca se ha medido» «quedó viejo».
- **QUÉ PASA**: la caja ROI1 se midió sobre K en S151 y perdió una protegida MODIS de Láscar (2026-03-27 07:10, 1,0 MW, píxel a 3,2 km). A118 se lee en `CLAUDE.md`, antes que SINTOMAS; A113 (c) manda marcar ahí primero.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `sed -n 1525,1535p D:\vrp-trabajo\temporales\s160_audit\main\CLAUDE.md`.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD 4** (sostiene un frente cerrado por veto). **Marca propuesta**: «⚠️ **S151, marca agregada en S160 (F4-285)**: la caja se midió en S151 con el cableado arreglado: KC NO CUMPLE (veto) en D1 (`docs/MIROVA_DIVERGENCES.md`, D18); el «nunca se ha medido» describe S148.»

### 286. Todo S158 vive sólo en `loop/activo`; en main los textos que se leen primero no saben del código de MIROVA, y en la rama los pendientes U1 a U13 siguen casi todos sin marca
- **ARCHIVO:LÍNEA**: `git cat-file -e d516b9d8c:docs/AUDIT_S158.md` falla; `git show d516b9d8c:docs/MIROVA_DIVERGENCES.md | grep -c D34` = 0; `git log --oneline d516b9d8c..HEAD | wc -l` = 67. En main sin marca: `CLAUDE.md:138` («kernel 8-vec aritmético … FIEL a Coppola 2016a»), `:161` («Kernel 8-vecinos … Drift D1 RESUELTO S17»), `:205` (A4 «no hay máscaras geométricas»), `docs/MISSION.md:290` (`exclude_zones` «MIROVA no usa máscaras geográficas»), `docs/MIROVA_DIVERGENCES.md:1086` («scene=0.010 (Coppola 2016a Table 2)»), `pipeline/detection_context.py:974-984`. En `loop/activo` (HEAD `60762a939`): U1 `docs/MIROVA_DIVERGENCES.md:3314` y `docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md:189,281` sin marca; U2 `CLAUDE.md:123-126` marca sin los límites; U3 D18 `:2385` sin marca; U4 D27 encabezado `:2875` sin marca (cuerpo `:2879-2881` con marca; `pipeline/diurno.py:128` y `PREREGISTRO.md:18` sin marca; el test sí); U5 D8 `:1303-1309` CON marca S158 R2; U8 `:1104`, `CLAUDE.md:152,181` sin marca; U9 `RESUMEN_SELLO.md:3` sin marca; U10 `experiments/50_FACTOR_42_HALLAZGO.md` sin marca; U11 `documentacion/BIBLIOGRAPHY_SYNTHESIS.md:248` (fuera de git) sigue «n=12 nocturno, n=8 diurno (Di Bella 2024)»; U12 memoria sin marca; U13 `docs/DISENO_D17_REMUESTREO_UTM.md:282` sigue «pendiente del verificador». S159 no tocó ninguno (`grep -rn "F2-H[3-9]\|U1[0-4]" experiments/_s159/` vacío; la única mención es la lección en `experiments/_s159/guia_auditorias/A_LECCIONES_PROYECTO.md:337`).
- **QUÉ PASA**: lo que importa de S158 (K1 -0,7; 0,02 fuera de la cumbre; 3 × 3 con el central; fondo interpolado sin recorte; MIROVA sí excluye píxeles por volcán) es exactamente lo que `CLAUDE.md` de main presenta como fidelidad confirmada. Es A113 a escala de rama: la rebaja vive donde no se lee.
- **CÓMO SE VE EN EL DASHBOARD**: invisible. **CÓMO REPRODUCIRLO**: los comandos de arriba desde `C:\vrp-trabajo\s159-pruebas`.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD 4** (D34 toca los umbrales de producción de VIIRS 750; mientras no esté en main, cada sesión fría arranca con la versión vieja).
- **Marcas propuestas**: (U1) en D34 «Alcance»: «⚠️ S158 F4-H6 y V3: la estructura se traslada, los números no; cada sensor se mide contra su referencia»; (U3) D18 encabezado: «⚠️ S158 (H:120-125): MIROVA adapta la ROI por volcán»; (U4) D27 encabezado: «⚠️ S158: en VIIRS 750 el código usa K1 = -0,5 y rechaza reflejo bajo 12°, ver la marca de abajo»; (U8) `CLAUDE.md:138,161` y catálogo `:1104`: «⚠️ S158 (D34): el código publicado usa 3 × 3 con el central y 0,02 fuera de la cumbre; la tabla del paper es la 1»; (A4 `CLAUDE.md:205`, MISSION `:290`): «⚠️ S158 F2-H3: el código admite píxeles excluidos y ROI adaptadas por volcán; «MIROVA no usa máscaras» no se sostiene en absoluto»; (U13) reemplazar «pendiente del verificador» por «confirmado por V3 (S158 R2)».

### 287. El «1 SIN EVIDENCIA» de A113 sigue sin evidencia, nadie lo persiguió en S159, y bajo K la población cambió
- **ARCHIVO:LÍNEA**: `docs/audit_s146/FRENTE_A_SIN_RESPALDO.md:78,138,151` (A-04: «D9: el pilar «207 de 214 son reales» no es reproducible»); hijos sin marca: `memoria/reference_s113_cirrus_d9_scope.md:3,17,23,36,37` y `memoria/project_s113_estado.md:34,40` («mataría 207/214 detecciones reales»).
- **QUÉ PASA**: el probe de S113 nunca se guardó; S146 V-01 reprodujo los denominadores (199/214) y mostró que con «alerta» el máximo es 80 de 214. Sigue SIN EVIDENCIA, no refutado. Con K (282) la población «fondo frío más path D» es otra: el número ya no se puede ni intentar reproducir sobre main.
- **CÓMO SE VE EN EL DASHBOARD**: invisible. **CÓMO REPRODUCIRLO**: `grep -rln "207 de 214" experiments\_s159\` (vacío); `python -I propagacion_grep.py …` (R3).
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD 4** (D9 cara co-validación sigue abierta sobre esta creencia).

### 288. La memoria del agente conserva cinco cierres o números rebajados sin marca
- **ARCHIVO:LÍNEA** (todos en `C:\Users\nmend\.claude\projects\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile\memory\`): `MEMORY.md:50-51` («**S27 Test1 cierra D4 (recall 50→80 %)**», SIN EVIDENCIA desde S147); `reference_s113_cirrus_d9_scope.md:3,17,23,36,37` (207 de 214, 0 fuga); `reference_calidad_referencia_mirova_por_mes.md:11` («cobertura nocturna 86 % enero», corregido S151); `reference_s123_reglas_a86_a88.md:23` («482 píxeles», SIN VERIFICAR S146); `reference_mirova_daytime_cloud_artifact.md:29-30` («SUPERVISIÓN MANUAL», «~5 % aleatorios», cita corrupta S146 y refutada por el código S158); `milestone_s27_h_s27_1_confirmada.md:3`; además `project_s155_estado.md:19` y `feedback_s155_marca_en_los_datos.md:13` (frontera 2026-09-18, ver 281).
- **QUÉ PASA**: `MEMORY.md` se carga entero en cada sesión antes que cualquier documento del repo; es el texto que más «se lee primero» y A113 no lo nombra.
- **CÓMO SE VE EN EL DASHBOARD**: invisible. **CÓMO REPRODUCIRLO**: `python -I propagacion_grep.py D:\…\main <memoria>` (R3, R4, R9, R11, R12).
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD 3**. **Marca propuesta** en `MEMORY.md:50`: «S27 Test1 cierra D4 (recall 50→80 %, ⚠️ SIN EVIDENCIA desde S147; apagado en producción desde K)».

### 289. `README.md` de main describe el Test 1 integrado como detector vivo
- **ARCHIVO:LÍNEA**: `README.md:54` («the **integrated-ROI Test 1** for spatially-extended sub-pixel anomalies»), `:92`, `:131` («sums the MIR excess over the 3 km summit ROI and fires»), `:220`; 0 apariciones de «S153», «#850» ni «⚠️».
- **QUÉ PASA**: es el documento público del SDA (Resolución CPLT N°372); desde #850 ese camino no corre en la réplica.
- **CÓMO REPRODUCIRLO**: `git show d516b9d8c:README.md | grep -n "Test 1"`. **CONFIANZA**: CONFIRMADO. **GRAVEDAD 3** (transparencia; ninguna alerta).

### 290. D27 tercera marca S151: la tabla perdió 53 alertas de la ventana y la marca no lleva hash
- **ARCHIVO:LÍNEA**: `docs/MIROVA_DIVERGENCES.md:2862` («de 1.642 filas `ALERTA_TERMICA`, 37 caen entre 13 y 21 UTC, y 19 de ellas son de 1 MW o más (15 VIIRS 375, 2 VIIRS 750, 2 MODIS; Láscar 9, Nevados de Chillán 8, Villarrica 2), contra 233 protegidas de noche»).
- **SCRIPT:SALIDA**: `mis_conteos_salida.txt` §3 sobre bc1522c2: 1.589 / 37 / 20 (15 VIIRS375, 3 MODIS, 2 VIIRS; Chillán 9, Láscar 9, Villarrica 2) / 228. Control: 1.655 alertas en todo el CSV (2026-01-10 a 2026-10-21), así que el instrumento ve el total. Las 37 de tarde se reproducen; los totales no, por las pérdidas que S159 documentó.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD 3** (A/B diurno pendiente). **Marca propuesta**: añadir el sha256 del CSV y «sobre bc1522c2: 1.589 / 37 / 20 / 228».

### 291. D33: el efecto se reproduce; los n y las razones de la marca son del corpus anterior a #883
- **ARCHIVO:LÍNEA**: `docs/MIROVA_DIVERGENCES.md:3196-3220` («mediana 1,0575, en los 24 records MODIS con K … 12 pasadas … 0,362 → 0,382»), `docs/SINTOMAS.md:58-60`.
- **SCRIPT:SALIDA**: copia del script con la raíz apuntada a la instantánea (`t1_medir_efecto_lambda_salida.txt`): el script detecta solo «frontera K 2025-02-15»; F mediana 1,0587 (n = 581); contra MIROVA n = 95, 0,4926 → 0,5215; controles A y B con error relativo bajo 0,6 %. La dirección y el tamaño (+5 a +7,5 %) se sostienen; el «24» y el «12» ya no existen como población.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD 3** (flag apagado, decisión de Nicolás pendiente).

### 292. A116 y A117 citan números que no están en ningún archivo
- **ARCHIVO:LÍNEA**: `CLAUDE.md:1489` (A116: «cambia 0 de 4.448 records», «392 publicaciones»), `:1503` (A117: «5 de 1.755 records», «17 sesiones»).
- **QUÉ PASA**: `grep -rn "4.448\|4448\|1.755\|1755" docs/ experiments/_s147_* tests/test_guard_laboratorio_no_mas_ciego_s147.py` y la memoria de S147 no traen el número. Son reglas de método; lo que cae es su ejemplo, igual que A87.
- **CONFIANZA**: CONFIRMADO (ausencia por grep; A89: puede estar con otro nombre). **GRAVEDAD 2**.

### 293. Pendientes F2-H3 a F2-H9 de S158: ninguno resuelto en S159
- Detalle por ítem en 286 y en `propagacion.csv` (filas R15). H5 (D8) y H6 (test diurno) llevan marca S158 R2 en `loop/activo`; H3 (A4, MISSION `:290`, yaml `:291-294`), H4 (BIBLIOGRAPHY fuera de git), H7 (`CLAUDE.md:138,161`, catálogo `:1086`), H8 (`detection_context.py:974-984`, A45) y H9 (tests) siguen sin marca en las dos ramas. **CONFIRMADO. GRAVEDAD 3.**

### 294. El censo de cierres creció un tercio y hay tres cifras distintas para «cuántos cierres hay»
- **SCRIPT:SALIDA**: `censo_copia.py` (copia del `censo.py` de S146, sólo cambia la raíz) sobre `61cc94e3a` da 91 afirmaciones y 52 sin respaldo; sobre `d516b9d8c`, 124 y 70 (`censo_cierres_*.json`); 44 textos nuevos (`censo_delta_nuevas.md`). El JSON de S145 del repo dice 109 y 63 (lo escribió la versión anterior del script, cambiada en `5167951c2`); A113 dice «89 cierres auditados» y «50 sin respaldo». Las dos preguntas del instrumento: el censo busca por palabras clave (piso, no medida) y su control sintético pasa (4 de 4). Dato nuevo: de los 44 textos nuevos, la mayoría son **marcas de rebaja** que contienen la palabra que el censo busca («irreducible», «NO ADOPTAR» dentro de una frase que lo rebaja): el instrumento cuenta la corrección como cierre.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD 2**. Propuesta: que el censo registre la versión del script (hash) y que excluya líneas que empiezan con `⚠️` o `> ⚠️`, contándolas aparte.

### 295. A83 (control positivo del barrido): rebajada en `CLAUDE.md`, 11 hijos sin marca
- `CLAUDE.md:1072` CON marca. Sin marca: `docs/AUDIT_S116_C2_GATES.md:79`, `docs/DISENO_SENSIBILIDAD_POR_ZONA_S147.md:55`, `docs/LIBRO_DE_PRUEBAS.md:71`, `docs/audit_s146/*` (5), `memoria/project_s116_estado.md:77`. Son informes de sesión y memoria; A113 (c) los pone al final. **CONFIRMADO. GRAVEDAD 1.**

### 296. SINTOMAS §4 repite «874 de 877 noches» (C0) sin marca de K
- `docs/SINTOMAS.md:139` («874 de 877 noches con alerta detectadas (A98, medido S139, antes de K)»). Dice «antes de K» pero no que con K se pierden 16 de 194 y 26 de 388 alertas Muy Bajo por pasada (C04) ni que el corpus de main ya es K. **CONFIRMADO. GRAVEDAD 2.**

### 297. «Gaua» sigue en 24 perfiles y 45 pasajes sin marca
- `grep -l Gaua pipeline/profiles/*.yaml | wc -l` = 24 (`mirova_equivalent.yaml:497` hoy). La marca S146 vive en el catálogo (`:256-270`); los perfiles van con A45, lo dice el propio catálogo. **CONFIRMADO. GRAVEDAD 1.**

## 4. Resumen de `cierres_delta.csv` (58 afirmaciones)

| veredicto | n | ids |
|---|---|---|
| verificada (artefacto citado dice lo que la afirmación dice; T1 corrido donde el script lo permitía) | 15 | C01, C02, C04, C05, C07, C11, C15, C17, C18, C24, C25, C32, C43, C48, C55 |
| en parte | 14 | C03, C08, C12, C13, C14, C19, C20, C21, C22, C28, C30, C56, y C47/C48 en su número |
| refutada (sobre main de hoy) | 4 | C06, C09, C29, C49 |
| SIN EVIDENCIA | 3 | C10, C26, C27 |
| SIN VERIFICAR o SIN DATO | 5 | C16, C23, C40 (bajo `max`), C51, C53 |
| no era un cierre | 2 | C57, C58 |
| heredada de S146/S147 (verificada por su verificador, no re-medida aquí) | 15 | C31, C33 a C39, C41, C42, C44, C45, C46, C50, C52, C54 |

Lo que sostiene K (C01 a C05, C56) se lee tal cual en `experiments/_s153_fk_v2/v1.log:91,178`, `v2.log:148,223-224,231-233` y `r3/controles_salida.txt:61-63,91-92`; F1a mide si esos logs miden lo que dicen.

## 5. Propagación (`propagacion.csv`, 499 filas)

| rebaja | hits | con marca | sin marca | dónde falta, lo que se lee primero |
|---|---|---|---|---|
| R1 K en producción (S153/S157) | 239 + 4 (README) | 108 | 135 | `README.md:54,92,131,220`; `pipeline/detection_context.py`, `test1_integrated.py`, `profile.py`, `frontend/diario.html`, `mosaico.html` (1 a 2 cada uno, ver salida); el resto son docs de sesión y perfiles de A/B históricos |
| R2 histórico K (#883) | 19 | 16 | 3 (+2 memoria) | `SINTOMAS.md:9,109,198` (281) |
| R3 tope D9 / A23 | 60 | 29 | 31 | memoria (287); informes de S146 |
| R4 A119 corregida | 4 | 3 | 1 | memoria `reference_calidad…:11` |
| R5 A10 / D32 | 6 | 2 | 4 | `frontend/diario.html:250`, `HYPOTHESIS_LOG.md:386` |
| R6 criterio de victoria | 13 | 4 | 9 | `pipeline/profile.py:608`, `tests/test_d18_roi1_caja_s130.py:30` («prioriza recall sobre precision»), memoria `feedback_mirova_equivalent_priorities.md:68` |
| R7 D8' anomalía mayor | 14 | 3 | 11 | `docs/MIROVA_DIVERGENCES.md:1403` (encabezado «RESUELTO S38» sin marca; la marca S151 está 9 líneas abajo), `docs/S124_SELECCION_CLUSTER_MAX_VS_VENT.md:14` |
| R8 D18 medida S151 | 10 | 2 | 8 | `CLAUDE.md:1530` (285); `docs/s129/ROI1_CAJA_VS_CIRCULO.md:13` |
| R9 D4 50→80 SIN EVIDENCIA | 12 | 5 | 7 | `MEMORY.md:50-51` (288) |
| R10 serie continua | 12 | 2 | 10 | `scripts/clasificacion_referencia.py:21` |
| R11 A87 | 5 | 2 | 3 | `docs/AUDIT_S123.md:174`, memoria |
| R12 A76 | 6 | 2 | 4 | memoria `reference_mirova_daytime_cloud_artifact.md:30` |
| R13 Gaua | 52 | 7 | 45 | 24 perfiles (A45) |
| R14 D13 31 % | 11 | 3 | 8 | docs de sesión y memoria |
| R15 S158 (sólo `loop/activo`) | 22 a mano | 3 | 19 | ver 286 |

## 6. Las dos preguntas del instrumento

- **`propagacion_grep.py`**: (1) si la propagación estuviera rota, todo saldría SIN marca: sí lo vería. (2) Control positivo A83: la primera versión (ventana de 3 líneas) dio 12 hits y 0 con marca, o sea **falló**: la marca de A83 está 6 líneas antes del número. Corregido a «pasaje envolvente» (desde el inicio de la regla o encabezado, tope 80 líneas) A83 sale CON marca en `CLAUDE.md`. Control negativo («zanahoria lunar»): 0 hits. Límite declarado: un hijo cuyo pasaje no empiece con `- **A`, `#` o `|` y cuya marca esté a más de 80 líneas sale SIN marca; y una marca que no diga la sesión ni lleve ⚠️ no cuenta. El instrumento sobreestima «sin marca» en informes largos de sesión, nunca en `CLAUDE.md` ni en el catálogo (comprobado en A83 y en R1, donde `CLAUDE.md`, `MISSION.md` y el catálogo dan 0 sin marca).
- **`mis_conteos.py`**: cada bloque imprime el denominador (74.811 records; 42.410 filas; 1.122 filas OCR) y un control que no puede ser cero (1.655 alertas en todo el CSV; 41 alertas MODIS en el OCR). Primera corrida con la clave de tiempo equivocada dio «0 de 0»: lo delató el denominador (74.811 sin parsear) y se corrigió.
- **`censo_copia.py`**: control sintético propio (4 de 4). Busca por palabra clave: piso.
- **`contar_topados_d9.py`, `distancia_mirova.py`, `clase_mirova.py`, copia de `medir_efecto_lambda.py`**: corridos sobre la instantánea; los tres primeros no toman ventana ni declaran hash, que es exactamente el defecto de 282, 283 y C14.

## 7. SEGUIMIENTOS (fuera de mi eje)

- **S-1 (F1a/F1b)**: `experiments/_s151_alertas_minimas/frontera_banner.py` sólo ve 137 filas con banner; la regla SN se apoya en 7 casos del script (284). El evaluador de K selló antes de D-9 («decide con la regla que tenía»): comprobar con qué regla salió el CUMPLE de `combinado.log`. SOSPECHA.
- **S-2 (F1b)**: `contar_topados_d9.py` cuenta magnitudes, no `d9_capped`; con K el campo `d9_capped` aparece en 1 de 582 records con magnitud (`t1_medir_efecto_lambda_salida.txt`, «n_capados_d9»). Si el tope ya no muerde, el perfil `_s150_sin_tope_d9.yaml` mide nada. SOSPECHA.
- **S-3 (F3 o síntesis)**: `scripts/clase_mirova.py` imprime «2026-01 {'coherente': 49, 'incoherente': 15}» (`t1_clase_mirova_salida.txt:2`): 15 filas de enero con la columna `Clasificacion Mirova` incoherente con el VRP. Confianza: leído, no interpretado.
- **S-4 (síntesis)**: la instantánea de D: no tiene `README.md` ni `volcanoes.yaml`; `README.md` lo leí con `git show`. Para F2/F3 conviene saberlo.
- **S-5 (orquestador)**: el censo S145 escribe sobre sus propios archivos y su JSON del repo quedó con la versión vieja del script (109 contra 91 con el script de hoy sobre el mismo árbol). Si alguien compara «109 → 124» lee un crecimiento falso (A90).
- **S-6 (F2 o síntesis)**: `docs/MIROVA_DIVERGENCES.md:1403` (D8' «RESUELTO S38») y `:2337` (D18 «prioridad baja») tienen la marca debajo del encabezado y no en él; A113 (d) lo cuenta como texto sin marcar.

## 8. VERIFICADO LIMPIO (contra qué vara y con qué comando)

- Los números de K citados en `CLAUDE.md`, `MISSION.md` y el catálogo (88,2/85,4 → 2,5/3,7 %; 7 de 825; 18 de 2.173; 107; 242; 39 de 39 contra 6; 7 → 60 de 65; 10,8 → 0,9 %; 16 de 194; 26 de 388) están tal cual en los logs citados, en las líneas citadas. Vara: el archivo, no el evaluador (F1a).
- A119 marca S151 «5 alertas MODIS dependen del OCR, todas de Láscar, 4 nocturnas»: reproducido exacto sobre bc1522c2 y 94679246 con pareo a 120 s (`mis_conteos_salida.txt` §4). Los hitos están en `scripts/calidad_referencia_mirova.py:22-24`.
- D-PCC «revertida a las nueve horas, PR #85»: `git log -S'inner_radius_km: 7' -- volcanoes.yaml` da `fab02ec1c` (#79) y `5d2bea4b9` (#85).
- MISSION S157 «el revert choca en 3 archivos»: `experiments/_s157_propagar_k/revert_hoy.out` tiene 3 `CONFLICT`.
- A113 «27, 5, 1, 7, 10 de 50»: `docs/audit_s146/FRENTE_A_SIN_RESPALDO.md:133-139`.
- A114 y A115: `experiments/_s147_residual/estructura_salida.txt:4,13-18,22,24` y `experiments/_s147_pos/estabilidad_salida.txt:6-10` traen los números (94 = 41 + 6 + 47; 1,3 % y 22,8 %).
- S150 Láscar por meses: `docs/S150_RESULTADO_MESES.md:55-56,61`.
- D18 S151 veto: `experiments/_s151_prereg_caja/resultado_d1/README.md:10,40`; D8' TIF: `experiments/_s151_seleccion_mirova/README.md:18-19,173`; 858/498/360: `docs/audit_s150/meta/AUDITOR_F2_NUMEROS.md:16,24,35`.
- `CLAUDE.md`, `MISSION.md`, `MIROVA_DIVERGENCES.md`, `INDEX.md`, `HYPOTHESIS_LOG.md` de main: 0 hijos sin marca de R1 (K), R3 (tope D9), R4, R9, R10, R11, R12, R14 según el barrido; `pipeline/profiles/mirova_equivalent.yaml:264` lleva la marca S153.
- Gaua: 24 perfiles, igual que decía S146.

## 9. SIN DATO

- Qué regla de mínimas usó el CUMPLE de K (S-1). Qué pasa con el hueco 2025-11-16 a 2026-01-28 (C47) después de #883: no lo medí. D17 marca S157 (F_bg), D18 «neto cero en 8 volcanes», D33 «96 de 96», las cifras de SINTOMAS que viven en `loop/activo` (C53): no leídos. La hora del servidor por llamada propia: `gh api` no devolvió cabeceras en esta shell.

## 10. FUERA DE ALCANCE

- Corregir cualquier documento (propongo marcas; las pone el orquestador). Reprocesar o despachar. Re-medir los cierres heredados de S146 y S147. Auditar `experiments/_s153_fk_v2/` como instrumento (F1a). La rama `loop/activo` más allá de U1 a U13 y F2-H3 a H9.

## 11. Archivos de esta carpeta

`INFORME.md`, `hallazgos.csv`, `cierres_delta.csv`, `propagacion.csv`, `propagacion_grep.py` y su salida, `mis_conteos.py` y su salida, `censo_copia.py` con `censo_cierres_main_d516b9d8c.*`, `censo_cierres_base_61cc94e3a.*` y `censo_delta_nuevas.md`, `armar_propagacion_csv.py`, `t1_contar_topados_d9_salida.txt`, `t1_distancia_mirova_salida.txt`, `t1_clase_mirova_salida.txt`, `t1_medir_efecto_lambda_copia.py` con `t1_medir_efecto_lambda_salida.txt` (y `medir_efecto_lambda_salida.*` que el script escribe a su lado), `delta_docs.patch`, `delta_docs_solo_agregadas.txt`. Pesado: `D:\vrp-trabajo\temporales\s160_audit\f4\base_61cc94e3a\` (los cinco docs rectores en `61cc94e3a`) y `…\f4\lambda\`.
