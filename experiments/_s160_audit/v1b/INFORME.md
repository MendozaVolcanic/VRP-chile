# V1b: verificación de los hallazgos y celdas FALLA del frente F1b (S160)

## 1. Encabezado

- Hora del servidor: inicio 2026-10-22 04:30:40 GMT, última lectura 04:47:12 GMT (header Date de api.github.com).
- Commit medido: origin/main = d516b9d8c0fad5b0ca458b9fb57cdf5e6f75f956 (instantánea D:\vrp-trabajo\temporales\s160_audit\main\),
  más, leídos con `git show`: d6d9b8e05 (código del A/B de D18 de S130), 1888c1e3e (#535), las ramas origin/s146-ab/35548121381,
  /35558196104, /35521542153 y origin/loop/activo.
- Modelo: Opus 5.5 (esfuerzo de la sesión). Rol: verificador con contexto limpio. No abrí f1b\INFORME.md ni matriz_instrumentos.csv.
- CARPETA: C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\v1b\ (datos: D:\vrp-trabajo\temporales\s160_audit\v1b\, 58 MB).
- caminos.md escrito antes de abrir los archivos citados; sha256 4978bf466b59f14a46eacc3d3fd83f3b39b2c440118a491fafbdf23e890e5490, sellado a las 04:30:40 GMT.
- Plan sin cambios: `git diff 60762a939 -- docs/PLAN_AUDITORIA_S160.md` dio 0 líneas.
- Referencia usada cuando corrí evaluadores: tabla `latest_consolidado.csv` (sha256 bc1522c24c924cb5…) y OCR
  `registro_vrp_ocr.csv` (sha256 94679246acbd0db5…), ambos de la instantánea de main. Los evaluadores de S143 y S146 combinan
  tabla y OCR; no corrí la versión de tabla sola de ninguno (SIN DATO, ver §6).
- Qué NO miré: la reimplementación de `etiquetar`; las celdas R4 y R16 de S125, R16 de S130, R13 de la caja S151 más allá de leer
  su salida; los datos de los brazos del A/B diurno (no están versionados); los informes de verificadores en %TEMP% (no existen).
  Mi silencio sobre esas celdas no es OK: van en SIN DATO.

## 2. En una pantalla

1. 180 se sostiene en el hecho (ahora con el commit exacto del run 33456630043, d6d9b8e05: segundo pase con el círculo y Test 1
   encendido), pero NO en la gravedad: D18 hoy no la cierra S130 sino el veto de S151, y ese veto cuelga de UNA alerta MODIS de
   Láscar con VRP 1,00 MW, justo en el umbral de protegida (hallazgo propio V1b-01, gravedad 3).
2. 181 cae en su parte numérica: el 133 de 143 y C4 falso salen de un control sin la reparación 35558196104 (le faltan 71 pasadas);
   con la reparación sale 137 de 143, C4 verdadero y 2362 de 2362 idénticas en el control positivo del pre-registro. El
   INDECIDIBLE es real pero declarado, y la conectiva `max` en producción no cuelga de S148 (REGLA_ADOPCION l. 37-39). Gravedad 2.
3. 182 cae en su conclusión: D22 está ABIERTA en el catálogo y su estado lo sostiene la tarea 1.3 de S151, no S143; y el régimen de
   #535 no existe dentro de los brazos reprocesados (0 de 3.400 records con máscara de nube, contra 341 de 384 en producción antes de
   #535). Sí se confirma la saturación por el Test 1 (control publica 91,7 % de 1.170 negativos). Gravedad 2.
4. 188 y 189: hechos confirmados en parte; el empate de 188 es una convención declarada (FALLA en empate) y #535 no toca MODIS (189).
   Las 45 celdas: 25 confirmadas o confirmadas en parte (casi todas de gravedad 1 o 2; las de gravedad 3 son la caja S151),
   11 refutadas, no aplicables o literales sin efecto, 9 SIN DATO (tabla en §5). Ninguna celda sostiene hoy una decisión en producción.

## 3. Hallazgos verificados (lista recibida), por gravedad propia

### 180 · CONFIRMADO EN PARTE · gravedad propia 2 (el auditor dio 4)
- TÍTULO: El NO ADOPTAR de D18 en S130 salió de un instrumento que no podía ver la caja (segundo pase con círculo, Test 1 encendido)
- ARCHIVO:LÍNEA: d6d9b8e05:pipeline/process_viirs.py l. 1135 y 1259 (`is_summit = vent_dist_per_pixel <= inner_radius_km`, sin
  `_roi1_mask`); mismo patrón en d6d9b8e05:pipeline/process_modis.py l. 734 y 865 y process_viirs_mod.py l. 719 y 833;
  d6d9b8e05:pipeline/profiles/_s130_d18_caja.yaml l. 149, 270, 433, 434 (`enable_roi1_box_paper: true`, `enable_test1_path: true`,
  `enable_second_pass_adjacent: true`, `enable_dual_roi_second_pass: true`, todos bajo `paths:`, que lee `_p = _cfg["paths"]`,
  d6d9b8e05:pipeline/profile.py l. 131); experiments/_s130_d18/veredicto_d18.py `valida()` cuenta `triggered_test1 is True` como detección.
- QUÉ PASA: la caja endurece el umbral fuera de 5 × 5 km sólo en el primer pase; el segundo pase recaptura con el umbral laxo del
  círculo, y el Test 1 integrado publica por su cuenta (la métrica F3 lo cuenta). El instrumento de S130 medía el cableado.
- Lo nuevo de esta verificación: el auditor lo dejó en SOSPECHA para S130; ahora es CONFIRMADO: `gh api …/runs/33456630043` da
  head_sha d6d9b8e05b1ac13fe4da24f84bc46f07f676a407, el mismo commit que leí. r8_consumidores.py sobre ese archivo:
  `r8_d6d9_salida.txt` (l. 1135 y 1259 «mascara en contexto: NO»).
- Lo que cae: la gravedad 4. D18 no la cierra hoy S130: docs/MIROVA_DIVERGENCES.md l. 2339-2346 (marca S151) la cierra el veto KC
  de `experiments/_s151_prereg_caja/resultado_d1/`, medido con la caja en los dos pases desde #738; y la marca S148 (l. 2359-2373)
  ya dice que S130 «NO mide la caja». El hallazgo agrega la confirmación, no un cierre vivo.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `git show d6d9b8e05:pipeline/process_viirs.py | sed -n 1255,1280p`; `python -B experiments/_s160_audit/f1b/r8_consumidores.py D:/vrp-trabajo/temporales/s160_audit/v1b/process_viirs_d6d9.py`.
- Medición, las dos preguntas: (1) si la caja llegara al segundo pase, la línea mostraría `roi1_summit_mask(...)` como en main l. 1346;
  sí lo vería (control: main da «SI» en l. 1206 y 1346, `r8_main_mio_salida.txt`). (2) Si el script estuviera muerto, aborta por assert.
  Ojo: el veredicto global del script no distingue (ver V1b-03).

### 181 · CONFIRMADO EN PARTE · gravedad propia 2 (el auditor dio 4)
- TÍTULO: El A/B de la conectiva (S148) se declaró CONFIRMADA mientras su evaluador imprime INDECIDIBLE
- ARCHIVO:LÍNEA: docs/S148_RESULTADO_AB_CONECTIVA.md §2 (párrafo «⚠️ El evaluador imprime INDECIDIBLE…») y §3; experiments/_s147_ab_conectiva/PREREGISTRO.md §5;
  experiments/_s151_prereg_fk_11/REGLA_ADOPCION.md l. 37-39.
- Confirmado: el evaluador imprime INDECIDIBLE (reproducido: `s148_reparado_stdout.txt` l. 8) por la banda 80-92 % de tasa de
  publicación del control, calibrada para producción con Test 1; C6 y C7 salen falsos.
- Refutado 1, los números: el auditor usó el control del run 35548121381 SIN la reparación 35558196104 (su salida dice «cobertura:
  control 2315, brazo 2386»). Conté por volcán: le faltan 24 a Chaitén, 23 a Tupungatito y 24 a Villarrica (71). Con la reparación
  (extraída por ruta de origin/s146-ab/35558196104): cobertura 2386 contra 2386, recall del control **137 de 143**, brazo 135,
  **C4 verdadero** (`s148_reparado_stdout.txt` l. 9, 12, 22). Coincide con el documento S148.
- Refutado 2, el control que el pre-registro sí define (§5: el B de este run reproduce al B del run 35521542153): pasando ese B como
  `--produccion`, «n_pasadas_comparadas 2362, fraccion_publicacion_identica 1.0, diferencias_por_campo {}»
  (`s148_ctrlpos_prereg_stdout.txt` l. 6). La banda que hace imprimir INDECIDIBLE no está en el pre-registro de S147 y el documento
  S148 lo declara.
- Refutado 3, el alcance: la conectiva en producción viene de la adopción de K. REGLA_ADOPCION.md l. 37-39, TEXTO: «Antes de V2 ya se
  sabía mucho de `max`: S149 y S150 (contra el brazo B, sin Test 1) y Chillán en erupción (#796). Esta regla no la usa para decidir».
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: ver `s148_reparado_stdout.txt` y el comando en §7.
- Las dos preguntas: (1) si el recall del control estuviera mal, la cifra cambiaría (cambió de 133 a 137 al reparar: el instrumento lo ve).
  (2) Control positivo: 2362/2362 idénticas contra un B independiente; si el evaluador estuviera muerto no habría pares.

### 189 · CONFIRMADO EN PARTE · gravedad propia 3
- TÍTULO: Los probes MxD03 (1.17, 1.21, 1.23) decidieron bajo C0, con artefactos fuera del repo y pendientes de repetir sobre K
- Confirmado: las 7 rutas %TEMP% citadas en los README (verif_117, verif_121, verif_123 ×2, mxd03_117\art, probe_121\art,
  verif_117r\v5_along_track.py) NO existen en este computador (`ls`, esta sesión). En main no hay ningún `resultado/` de los tres
  probes; en origin/loop/activo hay 0 (1.17), 3 (1.21) y 7 (1.23) archivos. Los README de main y de loop/activo siguen diciendo
  «NO corrida» aunque corrieron. El desenlace (tasks/LOOP_OBJETIVOS.md de loop/activo l. 321-336) es «PIERDE PROTEGIDA» por la letra,
  con las 2 pérdidas de Láscar causadas por el Test 1 al cruzar su umbral: la fila que de verdad falla es R9, no R10. El pre-registro
  sobre K existe como borrador v2 (experiments/_s159/mxd03_prereg/PREREGISTRO_MXD03.md l. 1-6).
- Refutado: R10 por #535 en estos probes MODIS. #535 (1888c1e3e) sólo cambió `pipeline/process_viirs.py` entre los procesadores
  (`git show --stat 1888c1e3e`), y los brazos se reprocesan con un solo código.
- SOSPECHA abierta: la vara VIIRS de la 1.23 sale de `data/mirova_equivalent/*.json` de producción
  (loop/activo:experiments/_s151_mxd03_sola_123/construir_vara_viirs.py l. 110), que sí mezcla records escritos antes y después de
  #535 y del reproceso con K.
- Nombre del veredicto: no dice «NO ADOPTAR», dice «PIERDE PROTEGIDA» (no adoptable).
- CÓMO SE VE EN EL DASHBOARD: invisible. Gravedad 3 porque sostiene el A/B pendiente D-19.

### 182 · CONFIRMADO EN PARTE · gravedad propia 2 (el auditor dio 4)
- TÍTULO: El A/B de D22 y D25 (S143) decidió sobre una ventana que cruza #535, pisa hitos, con el Test 1 encendido
- Confirmado: ventana 2026-06-01 a 2026-08-31 (parametros.json), 0 apariciones de «535» en evaluar.py; Test 1 encendido en los 6
  brazos (`enable_test1_path: true` en _s142_ab_control l. 30, _literal l. 19, _lit_con_compuerta l. 14); el control publica en
  **0,917 de 1.170** negativos limpios (`s143_hitos_salida.txt`): saturado (A114). La referencia se fija por sha (bien) pero combina
  tabla y OCR sin informar la tabla sola, y la ventana pisa los hitos del OCR del 06-11, 06-13 y 08-06.
- Refutado 1, el régimen de #535 dentro de los datos: `nube_por_tramo_salida.txt`: VIIRS 375 del brazo control, n_cloud_masked > 0 en
  **0 de 3.290** records antes de 2026-08-28 23:00 y **0 de 110** después; lo mismo en lit_con_compuerta. Control positivo: producción
  de Chillán en 1888c1e3e^ (antes de #535), **341 de 384**. Los brazos se reprocesaron con un solo código: no hay dos regímenes.
  Además, 7 de 272 noches confirmadas caen desde el 08-29 y ningún brazo pierde una noche ahí.
- Refutado 2, el efecto de los hitos: pérdidas antes del 06-14 por brazo: literal 2 de 5, lit_con_compuerta 3 de 25, keep_peak 0 de 1.
  Sacándolas, ningún criterio 1 cambia (literal sigue con 3, compuerta con 22).
- Refutado 3, «su NO ADOPTAR es lo que hoy cierra D22»: docs/MIROVA_DIVERGENCES.md l. 2678, TEXTO: «**ABIERTA (divergencia literal
  confirmada…)**»; tasks/LOOP_OBJETIVOS.md (main) l. 163, TEXTO: «**1.3 A/B de D22, pre-registro v2.** RESUELTA SIN A/B 2026-10-14
  (#788)», y la sonda 1.2 sigue sin marcar (l. 158). Y el brazo que reponía la compuerta perdió 25 noches contra 5 del literal: S143
  es evidencia contra la compuerta, no un cierre de D22.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python -B experiments/_s160_audit/v1b/nube_por_tramo.py D:/vrp-trabajo/temporales/s160_audit/v1b/ndc_pre535.json D:/vrp-trabajo/temporales/s160_audit/f1b/s143/s143_ab`;
  `python -B experiments/_s160_audit/v1b/s143_hitos.py D:/vrp-trabajo/temporales/s160_audit/v1b/res_s143.json`.

### 188 · CONFIRMADO EN PARTE · gravedad propia 2
- TÍTULO: El A/B diurno tiene un G1 que empata con su p95 y una W4 que cruza #535
- Confirmado: el empate está en la salida (loop/activo:…/W2_W6_s154/evaluar_salida.txt l. 322-323, «+0.2303 | p95 del nulo barajado
  +0.2303»), y W4 (2026-08-13 a 08-31) cruza el 08-28.
- Refutado en su lectura de defecto: la regla es `"CUMPLE" if d > p95 + EPS_D else "FALLA"` (evaluar_diurno.py l. 553) con
  `EPS_D = 1e-12` (l. 531), y el comentario l. 528-530 declara la convención. Con 20 positivos D es discreto: un empate exacto con el
  p95 es esperable y se resuelve como FALLA a propósito. W2 a W6 falla con margen (+0,1816 contra +0,2446) y G2 falla en los dos
  sensores (2236 de 2511; 766 de 2466).
- SIN DATO: que W4 mezcle dos regímenes dentro de los brazos (los JSON de los brazos diurnos no están versionados). Por lo medido en
  S143 (refutación 1 de 182) espero que no, pero no lo medí aquí.

## 4. Hallazgos propios (V1b-01 en adelante)

### V1b-01 · El veto que hoy cierra D18 cuelga de una alerta de MIROVA de 1,00 MW, justo en el umbral de protegida
- ARCHIVO:LÍNEA: experiments/_s151_prereg_caja/resultado_d1/evaluar_D1_con_repeticion.txt (sección 7, «perdida: Lascar|MODIS|2026-03-27 07:10 | MIROVA 1.0 MW | MODIS_AQUA | pixeles de K: {'C': 1}»);
  scripts/clase_mirova.py l. 46 `UMBRAL_PROTEGIDA_MW = 1.0` y l. 72 `if v is None or v < umbral: return False` (o sea, protegida con
  VRP ≥ 1,0); latest_consolidado.csv fila 1774595400 (`Lascar,MODIS,1.0,1.41,ALERTA_TERMICA,Bajo`); `decimales_vrp_mirova_salida.txt`
  (alertas con dos decimales 1.508, con uno 147; entre 0,98 y 1,02 MW hay 13, tres de ellas en «1.0»).
- QUÉ PASA: en el volcán, un píxel MODIS caliente de Láscar cae a 3,2 km del cráter, en la corona, mientras MIROVA lo ubica a 1,41 km;
  la diferencia es del orden del corrimiento de geolocalización MODIS hacia el nadir que el propio catálogo reconoce (l. 2339-2346). En
  el código, la caja lo apaga y esa alerta es protegida porque su VRP publicado es 1,0 ≥ 1,0. El VRP de MIROVA viene con dos decimales
  (1.508 alertas con dos decimales, 147 con uno, que son ceros finales recortados): «1.0» es 1,00, o sea un valor real en [0,995; 1,005).
  Un redondeo de MIROVA hacia abajo, o un corrimiento de 1 km del píxel, quita la única pérdida y con ella el veto.
- CÓMO SE VE EN EL DASHBOARD: invisible; decide si la caja del paper se adopta.
- CÓMO REPRODUCIRLO: `grep 1774595400 latest_consolidado.csv`; script del conteo de decimales en §7.
- CONFIANZA: CONFIRMADO los hechos (valor, umbral, decimales); SOSPECHA que el veto no sea robusto (no corrí la caja con otra geolocalización).
- GRAVEDAD: 3 (sostiene el cierre de un frente; el catálogo ya condiciona el cierre a la geolocalización, no al umbral).
- Dos preguntas: (1) si la alerta estuviera bajo 1 MW, el conteo la sacaría de protegida (la regla es explícita). (2) Si mi lectura del CSV
  estuviera muerta, el conteo de decimales daría 0: dio 1.655.

### V1b-02 · La verificación numérica de 181 hecha por F1b usó un control incompleto, y el evaluador no lo avisó
- ARCHIVO:LÍNEA: experiments/_s146_ab_sin_test1/evaluar.py l. 338-345 (`"pareja": not faltan`, donde `faltan = kc - kb`) y l. 527-531;
  experiments/_s160_audit/f1b/s148/real_stdout.txt l. 9 («cobertura: control 2315, brazo 2386, faltan 0 (pareja=True)»).
- QUÉ PASA: C0 sólo falla cuando al BRAZO le faltan pasadas. La cobertura del control se vigila dentro del control positivo, pero ese
  control positivo ya falla por la banda en todo brazo sin Test 1, y cuando alguien lo pasa por alto (como S148, con razón declarada)
  pasa por alto también la cobertura del control. Así salió el 133 de 143 del auditor.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: comando del auditor en LISTA.md; compárese con `s148_reparado_stdout.txt`.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 2 (instrumento reusado por A/B pendientes).

### V1b-03 · r8_consumidores.py imprime FALLA también sobre el código ya arreglado
- ARCHIVO:LÍNEA: experiments/_s160_audit/f1b/r8_consumidores.py l. 21-32; `r8_main_mio_salida.txt`: sobre main da «R8: FALLA (4 consumidor(es) sin la mascara)».
- QUÉ PASA: cuenta como «consumidor» un docstring (l. 725 de main) y las asignaciones de `distance_class` (etiqueta del tablero, no
  umbral). Su veredicto global no distingue código roto de código arreglado; sólo la lectura línea a línea sí (main da «SI» en las
  dos líneas del segundo pase, d6d9 da «NO»). La conclusión de 180 sobrevive porque se apoya en esas líneas.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 2 (si otra celda R8 se marcó FALLA sólo por la línea final del script, no vale; no puedo ver la matriz).

### V1b-04 · R10 por #535 en A/B reprocesados es una falla de la fila, no del instrumento
- SCRIPT:SALIDA: `nube_por_tramo_salida.txt`.
- QUÉ PASA: #535 cambió el código; el corpus de producción quedó con dos regímenes porque los records viejos no se reescribieron.
  Un A/B que reprocesa todos sus días con un solo código no tiene ese cambio de régimen en sus brazos (0 de 3.400 records con máscara
  de nube contra 341 de 384 en producción vieja). Las celdas R10 de S143, del diurno y de los tres MxD03 son literales sin efecto,
  salvo cuando el instrumento lee producción (la vara VIIRS de la 1.23, SOSPECHA en 189).
- CONFIANZA: CONFIRMADO para S143; SOSPECHA para el diurno (sin datos). GRAVEDAD: 2.

### V1b-05 · El criterio 1 de S143 se da por cumplido con 0 noches cuando el evaluador excluye todos los volcanes
- SCRIPT:SALIDA: `s143_r2_sin_dia.md` (l. 37 «Evaluados: ninguno», l. 69 «Pérdidas … **0** … Cumple: **sí**»).
- QUÉ PASA: borré el 2026-07-01 de una copia del control (40 records en 9 volcanes). El evaluador ve la cobertura despareja y excluye
  los 9 volcanes (bien), pero imprime «Cumple: sí» en el criterio 1 sobre 0 noches, y el total sale «no» por el criterio 2 sin dato, no
  como INDECIDIBLE. Un lector que mire sólo el criterio 1 ve verde. Lo mismo explica el `placebo.md` del auditor con «Total: 0».
- CONFIANZA: CONFIRMADO. GRAVEDAD: 1 (S143 no sostiene hoy ningún cierre; ver 182).

### V1b-06 · El NO ADOPTAR de la prosa de S136 quedó superado por K
- ARCHIVO:LÍNEA: experiments/_s136/VEREDICTO_CONECTIVA.md (commit 4e1d7dcca, «NO ADOPTAR la prosa»); CLAUDE.md del proyecto, marca S153
  (`enable_tests_23_prose_branch: true` en producción).
- QUÉ PASA: las celdas R1 y R16 de este instrumento son reales en forma (no hay pre-registro propio de la conectiva antes de 4e1d7dcca),
  pero el instrumento ya no sostiene ninguna decisión: la decisión vigente es la contraria.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 1.

## 5. Las 45 celdas FALLA

Criterio: gravedad según la decisión que hoy sostiene el instrumento. «Literal sin efecto» = la condición de la fila se cumple pero no
podía cambiar el veredicto.

| # | instrumento | fila | veredicto | evidencia de esta sesión | grav. |
|---|---|---|---|---|---|
| 1 | S125 magnitud | R4 | SIN DATO | no medí | sin |
| 2 | S125 magnitud | R11 | CONFIRMADO | salida del auditor s125/x1.2.txt: con la magnitud del brazo ×1,2, los IC aún «SE SOLAPAN» en los 4 volcanes (Villarrica n 14). La vara no puede ver un efecto del tamaño buscado (+17 %). Leído, no re-corrido | 2 |
| 3 | S125 magnitud | R16 | SIN DATO | no medí | sin |
| 4 | S126 corona | R2 | SIN DATO | leí s126/sin_dia.txt (mismo veredicto que real); no borré otro día | sin |
| 5 | S126 corona | R9 | CONFIRMADO, efecto chico | Test 1 encendido en los 3 brazos (6130675c4, 024f9f057); #543: de 80 noches comparadas, 3 salen del Test 1 y 77 del contextual | 1 |
| 6 | S126 corona | R14 | CONFIRMADO | `_s126_lib.FUENTES_GT` l. 68-69 lee los CSV vivos del repo sin hash | 1 |
| 7 | S129 fondos | R9 | literal sin efecto | Test 1 encendido (262b1d644), pero el veredicto cayó por falta de sustrato (docs/s130/VEREDICTO_AB_D18.md: «K1 se cruza en el 0,09 % de las pasadas MODIS») | 1 |
| 8 | S129 fondos | R14 | CONFIRMADO | veredicto.py l. 31 importa `cargar_mirova` de `_s126_lib` (CSV vivo, sin hash) | 1 |
| 9 | S130 D18 | R8 | CONFIRMADO | ver 180 (commit exacto del run) | 2 |
| 10 | S130 D18 | R9 | CONFIRMADO | `enable_test1_path: true` en los dos brazos; `valida()` cuenta `triggered_test1` | 2 |
| 11 | S130 D18 | R14 | CONFIRMADO | veredicto_d18.py importa `cargar_mirova` de `_s126_lib` (vivo, sin hash) | 1 |
| 12 | S130 D18 | R16 | SIN DATO | no medí («redistribuye, no recorta» es el nombre; no comparé contra la regla) | sin |
| 13 | S135 D1 D2 | R9 | CONFIRMADO EN PARTE | control hereda `enable_test1_path: true` de mirova_equivalent (ed3494bfa); para D1 (keep_peak, que vive dentro del Test 1) la fila NO APLICA; para D2 (segundo pase) sí | 1 |
| 14 | S135 D1 D2 | R14 | CONFIRMADO | evaluar_ab.py l. 181-182: `load_mirova_alertas` sobre el snapshot del repo, sin hash | 1 |
| 15 | S136 probe 3 brazos | R1 | CONFIRMADO EN PARTE | pre-registro a333463f0 (17:24) antes del resultado 8cbc3658b (17:53); el evaluador cambió después de ver el control (filtro por sensor, ventana 20→3 min), con razón en el docstring, sin rótulo post hoc en el pre-registro. No hubo veredicto | 1 |
| 16 | S136 probe 3 brazos | R9 | REFUTADO (no aplica) | el objeto medido ES el Test 1 contextual (pre-registro l. 1-10) | sin |
| 17 | S136 probe 3 brazos | R14 | SIN DATO | `mirova_vrp_mw` viene del JSON del probe; no rastreé su fuente | sin |
| 18 | S136 Apéndice A conectiva | R1 | CONFIRMADO, sin efecto vigente | ver V1b-06 | 1 |
| 19 | S136 Apéndice A conectiva | R16 | CONFIRMADO, sin efecto vigente | ver V1b-06 | 1 |
| 20 | S143 D22 D25 | R5 | CONFIRMADO EN PARTE | el único nulo del veredicto es `control_contra_si_mismo` = {0, 0, 0.0} (identidad); pero MUTACIONES.md muestra 25 de 27 mutaciones muertas, o sea que el instrumento sí puede dar distinto | 1 |
| 21 | S143 D22 D25 | R9 | CONFIRMADO | control publica 0,917 de 1.170 negativos; Test 1 encendido en los 6 brazos | 2 |
| 22 | S143 D22 D25 | R10 | literal sin efecto | ver 182, refutación 1 | 1 |
| 23 | S143 D22 D25 | R14 | literal sin efecto | ver 182, refutación 2 | 1 |
| 24 | S144 keep_peak | R1 | CONFIRMADO, declarado | docs/CIERRE_FRENTE_KEEP_PEAK_S144.md l. 3-6: la medida pre-registrada v7 «nunca se corrió sobre su muestra»; el cierre se apoya en nulos medidos por los verificadores al iterar el diseño (7 versiones, f6a1cb962 a 1b0c37a5d) | 2 |
| 25 | S146 sin Test 1 | R16 | CONFIRMADO EN PARTE | docs/S147_RESULTADO_AB_SIN_TEST1.md l. 8-9: «NO ADOPTAR» junto a «el mecanismo quedó confirmado», que la regla no prueba | 1 |
| 26 | S146 A2 | R1 | CONFIRMADO, declarado | criterio y resultado en el mismo commit 61cc94e3a; el criterio declara «NO es ciego» y un hash (HASH_PRE_REGISTRO.txt, 06:30:52 UTC) que git no fecha | 1 |
| 27 | S147/S148 conectiva | R8 | SIN DATO | la máscara de la caja no es el valor que cambia este A/B (cambia la conectiva); no busqué consumidores de la conectiva | sin |
| 28 | S147/S148 conectiva | R16 | CONFIRMADO EN PARTE | «Hipótesis CONFIRMADA» con evaluador INDECIDIBLE (ver 181); declarado | 1 |
| 29 | S149 invierno | R1 | REFUTADO en lo grave | la adenda v3 (a23bddce3, 11:45) se escribió con mayo corriendo pero «antes de evaluar ninguna ventana», rotulada y aprobada; no cambia criterios, agrega ventanas y la etiqueta que decide | 1 |
| 30 | S150 D22 | R5 | literal sin efecto | el A/B se SUSPENDIÓ y nunca corrió (PREREGISTRO.md l. 3-19 de main) | 1 |
| 31 | S150 Chillán | R6 | SIN DATO | la autoprueba del auditor cae con StopIteration (probar_medir_ndc.py l. 97: no hay record topado y `far` en C0 con los datos del worktree): no midió placebos | sin |
| 32 | S150 Chillán | R16 | SIN DATO | no medí | sin |
| 33 | S151 diurno | R10 | SIN DATO | ver 188 | sin |
| 34 | S151 diurno | R11 | REFUTADO | tolerancia 1e-12 (evaluar_diurno.py l. 531) | sin |
| 35 | S151 caja D18 | R4 | CONFIRMADO EN PARTE | población: 10 protegidas que K publica, sólo Láscar, 14 días (evaluar_D1_con_repeticion.txt); la vara es externa (MIROVA), pero el veto lo decide 1 de 10 | 3 |
| 36 | S151 caja D18 | R11 | CONFIRMADO (otra forma) | ver V1b-01: la alerta que veta está en 1,00 MW, el umbral exacto | 3 |
| 37 | S151 caja D18 | R13 | REFUTADO (no aplica) | el veredicto es un veto por pasada, no un agregado | sin |
| 38 | S151 presupuesto | R1 | CONFIRMADO, declarado | PREREGISTRO.md l. 3-4: «Va en el mismo commit que los resultados, así que git no prueba el orden (V-16)» (ae64e2f36) | 1 |
| 39 | S151 presupuesto | R14 | CONFIRMADO EN PARTE | referencia fijada por sha (b_regimen_actual.py l. 225-227) e `indexar_referencia` avisa; la ventana 2026-03-01 a 10-14 (c_palancas_ab.py l. 228) pisa los hitos del OCR; no verifiqué si los separa | 2 |
| 40 | S151 MxD03 1.17 | R10 | REFUTADO | #535 no tocó MODIS (ver 189) | sin |
| 41 | S151 MxD03 1.21 | R10 | REFUTADO | ídem | sin |
| 42 | S151 MxD03 1.23 | R10 | REFUTADO para los brazos; SOSPECHA para la vara VIIRS | ver 189 | 2 |
| 43 | S151 Chillán saturación | R14 | CONFIRMADO EN PARTE | referencia fijada (evaluar_saturacion.py l. 53) y avisa (l. 179); ventana 2026-09-28 a 10-16 pisa los hitos del 10-09 y 10-10 (Suomi NPP, sin geometría); no verifiqué si los separa | 2 |
| 44 | CONTROL (c) N ponderado | R3 | CONFIRMADO | re-corrí r3_censo_vs_ponderado.py: salida idéntica (`r3_rerun_salida.txt`); el censo dice «60 de 119 medidos» y «dE_F (censo) = 60 - 0 - 48 = 12» (07_censo_analizar_salida.txt l. 10 y 12), contra 152,33 encendidos ponderados > techo 119 | control |
| 45 | CONTROL (d) caja G/H | R8 | CONFIRMADO | además de la rama G, en el código de S130 (d6d9) y con control negativo en main; leer por línea (V1b-03) | control |

## 6. Secciones aparte

### SEGUIMIENTOS (fuera de mi eje)
- El preámbulo de esta tarea ubica `UMBRAL_PROTEGIDA_MW` en scripts/banco_paridad.py l. 46; está en scripts/clase_mirova.py l. 46
  (banco_paridad.py l. 46 es `import random`). Confianza CONFIRMADO, gravedad 1.
- Los README de experiments/_s151_mxd03_* en main y en loop/activo dicen «NO corrida» después de corridos. CONFIRMADO, gravedad 1.
- La autoprueba de Chillán (experiments/_s150_ndc/probar_medir_ndc.py l. 97) depende de que los datos de producción del worktree
  tengan un record topado y `far` en la ventana; con los datos de hoy cae. CONFIRMADO (salida del auditor), gravedad 1.
- Los brazos de la corona de S126 se borraron en #547 por correr con el bug del fondo y se relanzaron (214a12838). El veredicto que use
  datos anteriores a 214a12838 no vale. No verifiqué qué datos usó el veredicto oficial. SOSPECHA, gravedad 1.

### VERIFICADO LIMPIO
- El control positivo del pre-registro de S147 (B contra B del run 35521542153): 2362 de 2362 idénticas. Vara: el §5 de ese pre-registro.
- La reparación del control de S148: cobertura 2386/2386 y recall 137/143. Vara: los JSON de las ramas s146-ab, no el documento.
- La salida de `r3_censo_vs_ponderado.py` es reproducible byte a byte.
- Que el evaluador de S143 detecta un día borrado en el brazo (excluye los 9 volcanes). Vara: un placebo propio (2026-07-01), distinto
  del día del auditor (2026-07-15 en S126 y 2026-09-10 en S148).

### SIN DATO
- Celdas 1, 3, 4, 12, 17, 27, 31, 32, 33 de la tabla del §5 (9 celdas), más la parte «W4 mezcla regímenes» de 188.
- Paridad en «tabla sola» de los evaluadores de S143 y S146 que corrí: sólo combinado.
- Si el veto de la caja S151 sobrevive con la geolocalización MxD03 o con la alerta en 0,99 MW: no lo corrí.

### FUERA DE ALCANCE
- Reprocesar L1B, despachar workflows, la reimplementación de `etiquetar`, el veredicto de D25 (#890).

## 7. Comandos

```
# 181, control reparado (D:\vrp-trabajo\temporales\s160_audit\v1b\s148\_s146_ab_sin_test1 = control del run 35548121381
# con Chaiten, Tupungatito y Villarrica de origin/s146-ab/35558196104)
python -B experiments/_s146_ab_sin_test1/evaluar.py --control D:/vrp-trabajo/temporales/s160_audit/v1b/s148/_s146_ab_sin_test1 \
  --brazo D:/vrp-trabajo/temporales/s160_audit/f1b/s148/experiments/_s146_ab_sin_test1/salidas/35548121381/_s147_ab_sin_test1_max \
  --out experiments/_s160_audit/v1b/s148_reparado.json
# idem con --produccion D:/vrp-trabajo/temporales/s160_audit/v1b/s148/b_35521542153 -> s148_ctrlpos_prereg_stdout.txt
# 182
python -B experiments/_s160_audit/v1b/nube_por_tramo.py D:/vrp-trabajo/temporales/s160_audit/v1b/ndc_pre535.json D:/vrp-trabajo/temporales/s160_audit/f1b/s143/s143_ab
python -B experiments/_s160_audit/v1b/s143_hitos.py D:/vrp-trabajo/temporales/s160_audit/v1b/res_s143.json
# V1b-05
python -B experiments/_s143_evaluador/evaluar.py --dir D:/vrp-trabajo/temporales/s160_audit/v1b/s143_r2 --brazos _v1b_sin_dia \
  --ref-cons <main>/latest_consolidado.csv --ref-ocr <main>/data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv --B 200 \
  --out-json experiments/_s160_audit/v1b/s143_r2_sin_dia.json --out-md experiments/_s160_audit/v1b/s143_r2_sin_dia.md
# V1b-01, decimales del VRP de MIROVA en alertas (latest_consolidado.csv de main): 1.508 con dos decimales, 147 con uno
```

Llamadas a la API de GitHub: 4 (repos con -i, runs/33456630043, rate_limit ×2).
