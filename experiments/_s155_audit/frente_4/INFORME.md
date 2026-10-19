# Frente 4 S155: cierres y afirmaciones que el detector K pudo volver falsos

Worktree `D:\vrp-trabajo\worktrees\s155-audit-f4`, detached en `cb90031a` (origin/main del 2026-10-19). Sólo
lectura del repo; todo lo que se escribió vive en esta carpeta. No se despachó nada, no se reprocesó nada, no se
autenticó contra Earthdata. Referencia de MIROVA: el snapshot del repo en ese commit
(`data/mirova_reference/mirova_v1_snapshot/`, sha CONS `756bcf02`, OCR `5398eae3`, impresos por `banco_K.out`).

## 0. Cómo se separó K de C0, y los instrumentos

- Flags de producción leídos desde `pipeline.profile` (A89): `ENABLE_TEST1_PATH False`,
  `ENABLE_TESTS_23_PROSE_BRANCH True`, `ENABLE_MODIS_B22_PRIMARY True` (comando en VERIFICADO LIMPIO).
- Un record es «K» si `processed_utc` es posterior al merge de #850 (2026-10-18 09:57:30 UTC); si no, «C0».
  `regimen_records.py` (P1: si K no se hubiera aplicado, el grupo K tendría `triggered_test1 > 0`; P2, control
  positivo: el grupo C0 tiene 24.363 records con `triggered_test1`, el K 0 de 3.661).
- Ventana K: observaciones 2026-09-18 a 2026-10-18 (11 Tier A, 3.577 records). Ventana de contraste C0: 2026-08-18 a
  2026-09-17. **Confusor declarado**: estación distinta (agosto-septiembre contra septiembre-octubre); sólo se
  reportan diferencias de un orden de magnitud o atadas a un mecanismo.
- «Publica» = predicado del tablero ejecutado con node (`scripts/banco_paridad.py`, importado, no copiado), con su
  control de identidad afirmado en cada script (`([0,1,1,1,0],[1,0])`) y AUC barajado ~0,5 (`banco_K.out`).
- Censo: `censo_k.py` importa los detectores de `experiments/_s145_censo_cierres/censo.py` y los extiende a 40
  documentos (los 5 rectores, `tasks/backlog_*.md`, 30 `experiments/*/README.md`), con etiqueta de dependencia de K
  (Test 1, conectiva, banda). **Límite**: busca por palabras clave, es un piso; una dependencia de K redactada sin
  nombrar Test 1, conectiva ni banda no se etiqueta (A82 y A98 no salieron etiquetadas y dependen de K). Resultado:
  167 cierres, 57 con dependencia de K, 53 de ellos con sesión máxima citada menor que S153 (`censo_k.out`).
  `citas.py` cuenta menciones por ID en 569 archivos para priorizar (D25 418, D22 406, D9 392, A82 250...).

## 1. Hallazgos, de mayor a menor gravedad

### F4-01. La marca del cambio de detector está un mes corrida: el escalón de la serie cae el 2026-09-18 y el tablero y la ficha SDA lo ponen el 2026-10-18

- ARCHIVO:LÍNEA: `frontend/cambio_detector.js:15` (`CAMBIO_DETECTOR_UTC = "2026-10-18T09:57:30Z"`), la línea se dibuja
  en el eje de tiempo de la observación (`cambio_detector.js`, plugin, `x.getPixelForValue(t)`); aviso «Las
  comparaciones que crucen esa fecha mezclan dos detectores» (`textoAviso`). `docs/FICHA_SDA_VRP_CHILE.md:7` («rige
  desde el merge del PR de adopción, cuya fecha y hora UTC muestran las tres vistas»). `docs/MISSION.md:16`.
  SCRIPT:SALIDA `escalon_vs_marca.out`, `chillan_escalon.out`.
- QUÉ PASA: el volcán no cambió el 18 de septiembre; cambió el detector con que se reescribieron esos días. Los 30
  días previos al merge se reprocesaron con K, así que en la serie la frontera C0/K está en la fecha de observación
  2026-09-18, no en la del merge. VIIRS 375 nocturno publicado: 0,86 el 17-sep (42/49, 0 de 49 records con K) a 0,16
  el 18-sep (8/50, 50 de 50 con K); alrededor del 18-oct no hay escalón (0,16 a 0,36, todo K). El aviso dice lo
  contrario de lo que pasa: cruzar el 18-oct no mezcla detectores, cruzar el 18-sep sí. Cuando el histórico por
  trozos (#852) se aplique, la frontera se moverá de nuevo (al 2025-02-15) y la marca seguirá en el merge.
- CÓMO SE VE EN EL DASHBOARD: en la tendencia de 90 días, todos los volcanes «se apagan» el 18-sep sin línea ni
  aviso en esa fecha. Nevados de Chillán: 4 a 5 pasadas publicadas por noche del 4 al 17-sep, 0 del 19 al 27-sep,
  mientras MIROVA publica 0 alertas casi todos esos días en las dos mitades (es nuestro detector, no el volcán). Es
  exactamente la lectura «la actividad declina» que `cambio_detector.js` dice existir para evitar.
- CÓMO REPRODUCIRLO: `python experiments/_s155_audit/frente_4/escalon_vs_marca.py` y `chillan_escalon.py`.
- CONFIANZA: CONFIRMADO (medido y leído).
- GRAVEDAD: 4. Puede torcer la lectura de tendencia de un volcán en erupción y la ficha pública de transparencia
  declara una fecha de vigencia que no corresponde a los datos.

### F4-02. Quedan 26 records C0 dentro de la ventana «reprocesada con K», y el tablero publica dos de ellos como cumbre en pasadas donde MIROVA no vio nada

- SCRIPT:SALIDA `c0_residuales.out` (control: frontera 2026-01-01 da 0, frontera 2027 da 3.577 de 3.577),
  `pcc_d9_k.out`. Contexto: `loop/activo:experiments/_s154_reproc_k/ventana_30d.json` declaraba 56 «sin K» con la
  ref de ese día; hoy quedan 26.
- QUÉ PASA: 26 pasadas MODIS Terra nocturnas (00:50 a 02:25 UTC) de 2026-09-28, 10-02 y 10-10, en los 11 volcanes,
  conservan el detector viejo (granules NRT; SOSPECHA: el reproceso no pudo volver a bajarlos). 24 son `far`; las 2
  de Puyehue-Cordón Caulle son `summit` y se publican: 2026-09-28 01:25 (0,852 MW) y 2026-10-10 01:05 (0,378 MW);
  para la segunda el consolidado de MIROVA trae RUTINA con VRP 0 en esa misma pasada.
- CÓMO SE VE EN EL DASHBOARD: dos detecciones MODIS de PCC con magnitud, generadas por el detector retirado, dentro
  del período que el tablero rotula como K. Toda métrica de la «ventana K» las mezcla (A104, A85 S153).
- CÓMO REPRODUCIRLO: `python experiments/_s155_audit/frente_4/c0_residuales.py`; PCC, MODIS_TERRA, 2026-10-10 01:05.
- CONFIANZA: CONFIRMADO (la causa del no reproceso, SOSPECHA).
- GRAVEDAD: 3.

### F4-03. A98 («la brecha es sobre-publicación, no recall») se invirtió con K

- ARCHIVO:LÍNEA: `CLAUDE.md:1294` (A98, «874 de 877 noches con alerta detectadas»), sin marca de K. SCRIPT:SALIDA
  `banco_K.out`, `banco_C0.out`, `noches_perdidas_k.out`.
- QUÉ PASA: con C0 (ventana previa) se publicaba en 121 de 121 noches-volcán con alerta y en 98,4 % de las noches que
  MIROVA miró sin ver nada. Con K: publicación en negativos limpios por pasada 1,5 % (n 1.937) y por noche 12,6 %
  (n 182); recall por noche 88 de 97 (regla original) y 81 de 85 (regla SN de D-9). Las 4 noches perdidas con SN
  están todas bajo 1 MW: Villarrica 2026-09-25 (MODIS, MIROVA 0,9 MW, nuestro record sin cúmulo), Chaitén 10-11
  (0,16), PCC 10-18 (0,10), Isluga 09-19 (0,06; nosotros publicamos cúmulos lejanos que coinciden con los
  FALSO_POSITIVO de MIROVA a 17,1 y 24,6 km, no el cráter). Bajo 1 MW MISSION pesa igual una alerta perdida que una
  publicación de más: la brecha ya no es «sobre-publicación» y una sesión que lea A98 prioriza el frente equivocado.
  Lo mismo para `MEMORY.md` («VIIRS captura TODO lo que MIROVA publica»), que no es del repo.
- CÓMO SE VE EN EL DASHBOARD: noches con alerta débil de MIROVA sin ninguna detección nuestra.
- CÓMO REPRODUCIRLO: `python experiments/_s155_audit/frente_4/noches_perdidas_k.py`.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 3 (dirige qué se investiga; no tuerce una alerta protegida en esta ventana).

### F4-04. Con `max`, el sigma gobierna el umbral en casi todas las pasadas: caen A103 y el «efecto nulo» heredado de D26 y del GAP #A

- ARCHIVO:LÍNEA: `CLAUDE.md:1312` (A103: «el piso C1 = 0,003 como umbral efectivo en los 70»);
  `docs/HYPOTHESIS_LOG.md:1509` (H_S141_VECINO_FOCO_V2, misma frase); `docs/MIROVA_DIVERGENCES.md:2745-2751` (D26,
  marca S153 «bajo `max` el término del sigma **puede** gobernar»); `CLAUDE.md:148` (GAP #A «efecto nulo hoy»).
  SCRIPT:SALIDA `sigma_gobierna_y_magnitud.out` (parte 1).
- QUÉ PASA: el umbral del contraste térmico de cumbre es el mayor entre el piso fijo y «media + 5 desviaciones» del
  fondo. Con K, `diag_mu_dnti + 5 · diag_sd_dnti > 0,003` en 1.417 de 1.417 records VIIRS 375, 1.416 de 1.416 VIIRS
  750 y 719 de 731 MODIS: el umbral efectivo es el término estadístico, no el piso. Bajo `min` ese mismo dato hacía
  gobernar al piso, por eso A103 lo encontró. Consecuencia: todo lo que ensucia la media y la desviación del pool
  (D26, sin los filtros de no aptos del paper; GAP #A, los píxeles del Test 1 del paper que no se retiran) pasa de
  «efecto nulo» a decidir el umbral en producción.
- CÓMO SE VE EN EL DASHBOARD: invisible directamente; decide qué píxel débil se publica.
- CÓMO REPRODUCIRLO: `python experiments/_s155_audit/frente_4/sigma_gobierna_y_magnitud.py`.
- CONFIANZA: CONFIRMADO que el sigma gobierna; SOSPECHA el tamaño del efecto de D26 y GAP #A (no medido).
- GRAVEDAD: 3. REABRIR MEDICIÓN: D26 y GAP #A sobre K (pool con y sin filtros, mismo granule, cuántas publicaciones
  cambian en positivos y negativos limpios).

### F4-05. El «NO ADOPTAR» de D22/D25 (H_S143) se midió con el Test 1 encendido y `min`; el pre-registro sobre `max` está escrito y sin resultado

- ARCHIVO:LÍNEA: `docs/HYPOTHESIS_LOG.md:1525` (H_S143_D22_D25, «resuelta como no adoptar»);
  `pipeline/profiles/_s142_ab_*.yaml` (los 6 brazos con `enable_test1_path: true` y
  `enable_tests_23_prose_branch: false`, leídos); `docs/MIROVA_DIVERGENCES.md:2645` (D22) y `:2740` (D25: «MODIS
  sigue con la mediana... no hay ni qué medir»); `pipeline/profiles/_s150_max_sin_d22.yaml` y
  `experiments/_s150_ab_d22/` (pre-registro sin carpeta de resultado).
- QUÉ PASA: la línea base de ese A/B en negativos limpios era 0,917, la saturación de A114. El propio perfil de S150
  dice que con `max` la compuerta D22 bloquea 16 de 36 alertas débiles perdidas. Con K esas alertas débiles son
  justamente el costo (F4-03). Además D25 en MODIS ya tiene sustrato con K: Láscar 2026-10-08 08:00 MODIS_AQUA,
  cúmulo de cumbre a 0,77 km en 0,0 MW contra 0,29 MW de MIROVA (`modis_pos_k.out`; la noche la cubre VIIRS 375).
- CÓMO SE VE EN EL DASHBOARD: alertas débiles sin detección; cráter con magnitud 0.
- CONFIANZA: CONFIRMADO (perfiles y salidas leídos). GRAVEDAD: 3. REABRIR MEDICIÓN: correr el pre-registro de
  `experiments/_s150_ab_d22/` (o uno nuevo con K como control) y el sustrato de D25 en MODIS y V750 sobre K.

### F4-06. A117 es falsa con K: el laboratorio corre C0 y es más ciego que la réplica en MODIS

- ARCHIVO:LÍNEA: `CLAUDE.md:1483` («Hoy el laboratorio es **idéntico** al operacional salvo el directorio»);
  `tests/test_guard_laboratorio_no_mas_ciego_s147.py` (sólo compara pisos de magnitud, l. 15);
  `docs/FICHA_SDA_VRP_CHILE.md:25` («en MODIS el método nuevo publica 39 de 39 de esas alertas en Láscar contra 6
  del método anterior»); `experiments/_s153_fk_v2/v1.log:60-61` (K recupera NdC MODIS 2026-10-01 08:35, 5,18 MW, que
  C0 no publica).
- QUÉ PASA: `VRP_PROFILE=experimental` da `ENABLE_TEST1_PATH True`, `PROSE False`, `B22 False`; igual
  `experimental_ndc_focus`. Es deliberado como sombra (MISSION:15), pero A117 sigue diciendo «idéntico» y su guard
  no ve la dirección de detección: el laboratorio pierde alertas protegidas MODIS que la réplica ve. La sombra sólo
  vigila pérdidas en una dirección.
- CÓMO SE VE EN EL DASHBOARD: invisible (perfil de laboratorio).
- CONFIANZA: CONFIRMADO. GRAVEDAD: 3.

### F4-07. La paridad de magnitud se midió bajo C0: con K la mediana cae a 0,56 en VIIRS 375 y 0,42 en VIIRS 750

- ARCHIVO:LÍNEA: `docs/MIROVA_DIVERGENCES.md:1452` (S103 R3: VIIRS 375 0,78×, VIIRS 750 0,80×, «MANTENER ctxpeak»);
  `CLAUDE.md:804` y `:819` (A66, A67), `:1296` (A99 «~0,7»), `docs/MISSION.md:204` («D5 magnitud» resuelta por
  nadir + ctxpeak). SCRIPT:SALIDA `sigma_gobierna_y_magnitud.out` (parte 2).
- QUÉ PASA: mediana de magnitud publicada (node) / VRP de MIROVA en pasadas con alerta: VIIRS 375 0,780 (n 210, C0)
  a 0,564 (n 144, K); VIIRS 750 0,604 (n 26) a 0,418 (n 29); MODIS 0,812 (n 1) a 0,246 (n 7). Con `max` entran menos
  píxeles al cúmulo y la diferencia con la suma de MIROVA (D32) crece. «D5 resuelta» ya no describe la réplica.
- CÓMO SE VE EN EL DASHBOARD: magnitudes cerca de la mitad de las de MIROVA desde el 18-sep.
- CONFIANZA: CONFIRMADO (con confusor estacional; el salto es mayor que lo que la estación explica en S153, que midió
  lo mismo por pares: «unos 28 % menos»). GRAVEDAD: 3. REABRIR MEDICIÓN: D32 y paridad de magnitud sobre K.

### F4-08. Los números de A82, A81, D12 y D9 son de C0; con K MODIS sí separa, y D9 sigue vivo con sustrato mínimo

- ARCHIVO:LÍNEA: `CLAUDE.md:1020` (A82: 89,1 % contra 93,7 %, «sin contraste»), `docs/MISSION.md:210-217`,
  `CLAUDE.md:998` (A81), `docs/MIROVA_DIVERGENCES.md:1640` (D12), `CLAUDE.md:365` (A23/D9). SCRIPT:SALIDA
  `metricas_cierres_k.out`, `modis_pos_k.out`, `contadores_k.out`, `pcc_d9_k.out`.
- QUÉ PASA: cúmulo con magnitud dentro del inner en MODIS: C0 617/699 negativos limpios (88,3 %, reproduce A82); K
  28/581 negativos (4,8 %) contra 7/11 positivos (63,6 %). El «destapar descubre por igual noches con y sin
  actividad» era una propiedad de C0. `far` con magnitud en el inner: C0 564/735, K 23/732. En la ventana K la
  etiqueta `far` no oculta ninguna pasada positiva (los 7 positivos con cúmulo de cumbre se publican) y ocultaría 20
  negativos, así que la decisión de no destapar sigue en pie con otra razón (n chico). Cúmulos MODIS topados en 5,0
  MW: 116 (C0) a 1 (K), y ese uno se publica: PCC 2026-10-03 01:25 MODIS_TERRA, fondo 254,8 K, cúmulo a 15,3 km
  (inner 20), `d9_capped`, contra RUTINA 0 de MIROVA en esa pasada.
- CÓMO SE VE EN EL DASHBOARD: un falso 5,0 MW en PCC el 3-oct.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 2. REABRIR MEDICIÓN: A82 con más ventana bajo K; sustrato de D9 bajo K antes de la
  Fase 3.

### F4-09. Cinco flags del Test 1 siguen en True, documentados como adoptados, y con K no hacen nada

- ARCHIVO:LÍNEA: `pipeline/process_viirs.py:1876-1887` (filtro contextual y `keep_peak` exigen
  `final_hotspot_source == "test1"`), `:1950` y `:1977` (recomputes con `effective_L_bg`), `:1798-1803` (prioridad
  de cúmulo débil, exige `test1_centroid_lat`); `docs/MIROVA_DIVERGENCES.md:1434` (D10 «ADOPTADO S100»), `:1452`
  (S103), `CLAUDE.md:1307` (A100 «nunca apagarlo solo»), `docs/CIERRE_FRENTE_KEEP_PEAK_S144.md` (sin marca de K;
  D19 sí la tiene, `:2443`).
- QUÉ PASA: `ENABLE_TEST1_CONTEXTUAL_FILTER`, `..._KEEP_PEAK`, `..._INTERMEDIATE_BG`, `..._LBG_GLOBAL` y
  `..._PRIORITY_WEAK_CLUSTER` valen True y sólo actúan sobre el camino del Test 1 integrado; 0 de 3.661 records K
  tienen fuente `test1` (`regimen_records.out`). No es un error de producción, pero cinco cierres describen como
  activa una maquinaria muerta, y la ficha CPLT debe describir lo que corre.
- CÓMO SE VE EN EL DASHBOARD: invisible. CONFIANZA: CONFIRMADO. GRAVEDAD: 2 (marca A113 pendiente).

### F4-10. La marca S153 de D19 dice que K no toca el segundo pase; el segundo pase sí recibe la conectiva

- ARCHIVO:LÍNEA: `docs/MIROVA_DIVERGENCES.md:2443`; `pipeline/process_viirs.py:1235` y `:1375`
  (`use_prose_branch=ENABLE_TESTS_23_PROSE_BRANCH` en `second_pass_adjacent`).
- QUÉ PASA: la estructura (correr sin conjunto activo) sigue igual, pero su umbral pasó a `max`; el «sigue abierto»
  de D2 hereda medidas tomadas con `min`. CONFIANZA: CONFIRMADO. GRAVEDAD: 2. Invisible en el tablero.

### F4-11. Con la banda 22 primaria, el VRP MODIS se calcula con la longitud de onda de la banda 21: 5 a 6 % menos

- ARCHIVO:LÍNEA: `pipeline/process_modis.py:553-554` (BT de B22 a 3,959 µm), `:1036`, `:1040`, `:1062` (radiancia
  con `BAND21_LAMBDA` = 3,929 µm); `:773` y `:857` (`nti_app` igual). Ya registrado como H511 en
  `docs/audit_s139/EJE_5_factibilidad_operacional.md:127` (SOSPECHA el efecto, no medido). SCRIPT:SALIDA
  `h511_lambda.out` (control: misma lambda da 1,000).
- QUÉ PASA: con K el defecto latente entró a producción. El exceso de radiancia sale 0,944 a 0,957 del correcto para
  fondos de 250 a 275 K y focos de 280 a 330 K. El comentario de `:772` («B21 primary, B22 fallback») quedó al revés.
- CÓMO SE VE EN EL DASHBOARD: magnitudes MODIS 5 % bajas. CONFIANZA: CONFIRMADO. GRAVEDAD: 2.

### F4-12. D4 «resuelta en S27» por el Test 1, y D23 crece con `max`

- ARCHIVO:LÍNEA: `docs/MISSION.md:203` (D4 recall sub-píxel resuelta S27), `docs/MIROVA_DIVERGENCES.md:107` (D4, sin
  marca), `:2676` (D23).
- QUÉ PASA: la cura de D4 era el Test 1, hoy apagado; el costo está medido (F4-03, y 21 alertas VIIRS 375 en V1). La
  marca global de MISSION:7 lo cubre en general, pero la línea 203 no nombra al Test 1. D23 (interiores de colada
  con dNTI ~0 que el paper captura por NTI > K1): con `max` les cuesta más pasar; con K, `n_nti_path > 0` (NTI > K1 y BT > fondo + 3 K, `process_viirs.py:1030-1036`) en 37 de
  1.428 records VIIRS 375 y 15 de 1.417 VIIRS 750 (C0: 7 y 0; `contadores_k.out`; MODIS no trae el campo, SIN DATO). SOSPECHA de
  efecto mayor en fase efusiva. GRAVEDAD: 2.

### F4-13. D13: el 31 % se sostiene por coincidencia; su composición se dio vuelta

- `metricas_cierres_k.out`: cúmulos con magnitud ocultos por la cerca `distance_class != summit`: K 165/529 (31,2 %),
  pero MODIS pasa de 654/730 (C0) a 28/51 y VIIRS 375 de 6/1.200 a 119/395. El enunciado agregado sigue en pie;
  cualquier lectura por sensor de D13 es de C0. CONFIRMADO. GRAVEDAD: 1.

## 2. Tabla de cierres revisados

| cierre | archivo:línea | medido bajo | depende de K por | recomendación |
|---|---|---|---|---|
| A98 brecha = sobre-publicación | CLAUDE.md:1294 | C0 (S139) | Test 1 y `min` hacían publicar | REABRIR (F4-03) |
| A103 piso C1 umbral efectivo | CLAUDE.md:1312; HYPOTHESIS_LOG.md:1509 | C0 (`min`) | conectiva | REABRIR (F4-04) |
| D26 efecto nulo / GAP #A efecto nulo | DIVERGENCES:2745; CLAUDE.md:148 | `min` | conectiva | REABRIR MEDICIÓN (F4-04) |
| H_S143 D22/D25 NO ADOPTAR | HYPOTHESIS_LOG.md:1525 | Test 1 on, `min` (perfiles leídos) | Test 1, conectiva | REABRIR MEDICIÓN (F4-05) |
| D25 MODIS «no hay ni qué medir» | DIVERGENCES:2740 | C0 | banda, conectiva | REABRIR MEDICIÓN (F4-05) |
| A117 laboratorio idéntico | CLAUDE.md:1483 | antes de S153 | todo K | FALSO hoy (F4-06) |
| S103 0,78×/0,80×, A66/A67, A99, D5 resuelta | DIVERGENCES:1452; CLAUDE.md:804,819,1296; MISSION.md:204 | C0 | Test 1, conectiva | REABRIR MEDICIÓN (F4-07) |
| A82 89,1/93,7 sin contraste | CLAUDE.md:1020; MISSION.md:210 | C0 | banda, conectiva, Test 1 | REABRIR (F4-08) |
| A81/D12 no destapar far→summit | CLAUDE.md:998; DIVERGENCES:1640 | C0 | banda, conectiva | SIGUE EN PIE en la ventana K, con otra razón (F4-08) |
| A23/D9 cara abierta | CLAUDE.md:365 | C0 | conectiva | REABRIR sustrato (F4-08) |
| D10 ctxpeak ADOPTADO, A100, cierre keep_peak S144 | DIVERGENCES:1434; CLAUDE.md:1307; CIERRE_FRENTE_KEEP_PEAK_S144.md | C0 | Test 1 | SIGUE EN PIE como historia; inerte con K (F4-09) |
| D19 marca «K no toca D2» | DIVERGENCES:2443 | S153 | conectiva | precisar (F4-10) |
| D21 adoptada «como el paper» | DIVERGENCES:2603 | S153 | banda | SIGUE EN PIE con H511 (F4-11) |
| D4 resuelta S27 | MISSION.md:203; DIVERGENCES:107 | C0 | Test 1 | REABRIR texto (F4-12) |
| D13 31 % | DIVERGENCES:1724 | C0 | todo K | SIGUE EN PIE agregado (F4-13) |
| D18 caja NO ADOPTAR | DIVERGENCES:2304-2313 | candidato K (S151, KC veto) | sí, ya medido con K | SIGUE EN PIE (sólo leído) |
| D30 Test 1 propio | DIVERGENCES:2851 | S153 | Test 1 | RESUELTA por K (verificado: flag False, 0 records test1) |
| D31 camino BT | DIVERGENCES:3024 | independiente | no | SIGUE EN PIE (0 records con BT en C0 y K) |
| A114 saturación por Test 1 | CLAUDE.md:1427 | C0 | Test 1 | SIGUE EN PIE (regla de método) |
| A83, A84, A85 | CLAUDE.md:1046,1072,1096 | C0 | Test 1, conectiva | SIN EVIDENCIA bajo K (no re-medidos) |
| A12, A19 (kernel-bg por volcán) | CLAUDE.md:273 | C0 | justificación atada al Test 1 | SIN EVIDENCIA bajo K (el kernel sí actúa sobre el camino contextual, `process_viirs.py:1471`, `process_modis.py:1054`) |
| D2, D3, A11, A119 | catálogo | referencia MIROVA | no | SIGUEN EN PIE (no dependen del detector) |

## 3. VERIFICADO LIMPIO

- Flags de K en producción: `VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p; print(p.ENABLE_TEST1_PATH, p.ENABLE_TESTS_23_PROSE_BRANCH, p.ENABLE_MODIS_B22_PRIMARY)"` da `False True True`.
- K se aplicó en los records reprocesados: 0 de 3.661 records K con `triggered_test1`, `n_test1_pixels > 0` o fuente
  `test1` (`regimen_records.py`; control C0 24.363 con `triggered_test1`).
- D31: `diag_n_bt_path > 0` en 0 records, C0 y K (`contadores_k.py`).
- Gates intra-radio apagados: `ENABLE_PATH_D_INTRA_RADIO_GATE False`, `ENABLE_SECOND_PASS_INTRA_RADIO_GATE False`
  (mismo comando de flags).
- Predicado del tablero en los scripts: identidad con los casos del guard S139 y AUC barajado ~0,5 por volcán
  (`banco_K.out`, `banco_C0.out`).
- Ninguna noche con alerta de 1 MW o más quedó sin publicar en la ventana K (0 de 97, regla original; 0 de 85, SN;
  `noches_perdidas_k.out`).
- Marcas S153 ya propagadas (no repetir): MISSION.md:7, :183, :328; CLAUDE.md:112, :138; DIVERGENCES:802, :1557,
  :2443, :2603, :2747, :2851.
- Control del censo extendido OK (`censo_k.out`).
- No se escribió nada fuera de `experiments/_s155_audit/frente_4/` (`git status --short` sólo muestra esa carpeta).
