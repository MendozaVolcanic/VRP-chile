# AUDIT S138, EJE 1: las afirmaciones de cierre contra el paper y el codigo de hoy

Auditor: agente Eje 1 (Fable 5.1), 2026-09-13, read-only sobre `main` en `6b1dd91ef`.
Suite corrida en esta sesion: `python -m pytest tests/ -q --no-header -p no:cacheprovider` = **1325 passed, 4 skipped, 2 xfailed** (`experiments/_s138_audit/eje1/pytest_s138_eje1.txt`).
Flags efectivos leidos de `pipeline.profile` con `VRP_PROFILE=mirova_equivalent` (140 lineas en `experiments/_s138_audit/eje1/profile_flags_efectivos.txt`), nunca del YAML.
Paper leido con PyMuPDF a `experiments/_s138_audit/eje1/sp426_5_pymupdf.txt` (25 paginas; los numeros de linea que cito son de ese volcado).

## 0. Las dos preguntas del instrumento, para este eje

1. Si una afirmacion de cierre estuviera completamente equivocada, esta revision lo veria? Si: cada una se contrasta con un flag efectivo, un `file:line` leido hoy o una pagina del PDF. Lo que no pude contrastar queda NO VERIFICABLE, no VIGENTE.
2. Si el instrumento estuviera muerto, se veria distinto? Control positivo: la revision encontro afirmaciones FALSAS ya marcadas como tales en CLAUDE.md (A13, A36, A42) y las volvio a refutar por su cuenta con datos de hoy (A13: `Distancia_km` de Villarrica es 0,0 en 3.449 de 3.506 filas del consolidado, 0,84 solo en 15). Un instrumento muerto no habria distinguido esas de las vigentes.

Denominadores y ventanas: cada numero de esta revision lleva su `n` y su ventana en la fila donde aparece (A90).

## 1. Tabla: afirmacion, fuente, premisa, evidencia, veredicto

Veredictos: **VIGENTE** / **CONDICIONADA** (vale solo bajo la lectura o el flag que se indica) / **FALSA** / **NO VERIFICABLE** (en esta sesion, con estos medios).

### 1.1 Seccion "Reglas cientificas (no negociables)" de CLAUDE.md

| # | Afirmacion | Premisa | Evidencia (hoy) | Veredicto |
|---|---|---|---|---|
| C1 | Wooster: MODIS k=18.9, VIIRS750 19.7, VIIRS375 18.0 | coeficientes en codigo | `process_modis.py:82` `WOOSTER_COEFF = 18.9`; `process_viirs_mod.py:64` `19.7`; `process_viirs.py:75` `18.0` | VIGENTE |
| C2 | A_pix nadir fijo en los 3 sensores | flags nadir ON | `ENABLE_NADIR_FIXED_PIXEL_AREA_MODIS = True`, `..._VIIRS = True`; `scan_geometry.py:148/238` devuelven area uniforme si `nadir_fixed` | VIGENTE (como estado del codigo). Ver A66 abajo para la parte "clon literal" |
| C3 | VRP TIR Stefan-Boltzmann puro | constante en codigo | `pipeline/constants.py:14` `SIGMA = 5.670374419e-8`; `ENABLE_VRPTIR_AVENI = False`, `ENABLE_VRP_TIR_OUTPUT = False` | VIGENTE (y el path TIR esta apagado) |
| C4 | N sigma = 5 summit / 10 scene noche, 15 dia | Tabla 1 del paper + flags | PDF p.7 Tabla 1: C2 = 5 / 10 noche, 15 / 15 dia; `N_SIGMA_MIR_SUMMIT=5.0`, `N_SIGMA_MIR_SCENE=10.0`, `N_SIGMA_MIR_DAY=15.0`, `ENABLE_DUAL_ROI_BT=True` | VIGENTE |
| C5 | C1 = 0.003 summit / 0.010 scene, 0.02 dia | Tabla 1 + flags | PDF p.7 Tabla 1: C1 = 0.003 / 0.01 noche, 0.02 / 0.02 dia; `DNTI_CONTEXTUAL_C1_SUMMIT=0.003`, `_SCENE=0.01`, `_DAY=0.02`, `ENABLE_DNTI_DUAL_ROI=True` | VIGENTE |
| C6 | Tests 2 y 3 con la rama OR completa `min(C1, mu+C2 sigma)` | formula del paper | PDF p.7 (volcado l.539-548): el `or` esta en su propia linea, dos veces; `detection_context.py:510` `combinar = max if use_prose_branch else min`, `ENABLE_TESTS_23_PROSE_BRANCH = False` | **CONDICIONADA**: fiel a la FORMULA (p.7 l.540-547); la PROSA del mismo parrafo (l.560-566: "C1 implies that a minimum threshold needs to be exceeded... However, when highly variable scenes...") describe `max`. S136/S137 ya lo registran; la regla en CLAUDE.md no dice bajo cual lectura vale |
| C7 | sigma global per imagen (no del anillo) | pool de mu/sigma | `detection_context.py:492-495` mu/sigma sobre `bg_mask` = ROI suitable (edge + pisos -0,1); paper p.7 "all the suitable pixels within the image" | VIGENTE para el primer pase. Ver hallazgo H6: el second pass usa otro pool |
| C8 | second run (excluye activos, recomputa mu/sigma) | p.8 del paper | `detection_context.py:896-910` pone NaN a los activos y recomputa mu/sigma; `ENABLE_SECOND_PASS_ADJACENT = True` | **CONDICIONADA**: excluye activos y recomputa, pero (a) corre con conjunto activo vacio y sin restriccion a adyacentes porque `ENABLE_SECOND_PASS_CONDITIONED = False` (D19, abierta), y (b) su pool no aplica los filtros unsuitable (H6) |
| C9 | ETI por regresion cuadratica | eqs 4-5 | `compute_eti_scene_quadratic` en `detection_context.py:680`, llamada en `first_pass_tests_2_and_3` l.464 | VIGENTE (nota: `ENABLE_ETI_QUADRATIC_SCENE = False` apaga OTRO path, el "eti_path" de `process_modis.py:775-820`; el primer pase calcula su ETI por su cuenta) |
| C10 | kernel 8 vecinos aritmetico | p.5 "arithmetic mean" | `_nanmean_8neighbors_fast` (`detection_context.py:162`), usado en l.467-470 y 915-916; ningun `np.median` en esas rutas | VIGENTE |
| C11 | "La deteccion MODIS es FIEL a Coppola 2016a (S114)" | auditoria S114 | `process_modis.py:544` `merge_mir_bands(rad21, rad22, ENABLE_MODIS_B22_PRIMARY)` con flag `False` (D21, PDF l.307-310: la 22 manda); `process_modis.py:869` pasa `bt_sanity_k=NTI_BT_SANITY_K` = 3.0 a `first_pass_tests_2_and_3`, que en `detection_context.py:532` exige `bt > t_bg + 3` (D22, PDF p.7 sin condicion de temperatura); `process_modis.py:857-859` `test1_mask=None` porque `ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK = False` (GAP #A: PDF p.6 l.556-558 "Pixels that satisfy Test 1 are flagged as active and subsequently discarded (unsuitable) for further steps"); `ENABLE_UTM_REGRID = False` (PDF p.3 l.325-328 remuestreo a grilla de 1 km); `ENABLE_ROI1_BOX_PAPER = False` (PDF l.349 "box (5 x 5 km)") | **FALSA**. CLAUDE.md ya la marca "FALSO desde S137" por D21 y D22; la marca es correcta y ademas incompleta: quedan GAP #A, el remuestreo (D17) y la caja del ROI1 (D18) como divergencias literales vivas en el codigo de hoy |
| C12 | "GAP #A RESUELTO S115 = MISLABEL, no era un gap real, NO reabrir" | "discarded" = fuera del pool, cubierto por el second run | `docs/MIROVA_DIVERGENCES.md:1319-1335` lo REABRE en S128 y prueba falsas las dos patas; `tests/test_guard_gap_a_pool_musigma_s128.py` (en la suite, verde) existe para que nadie vuelva a cerrarlo asi; codigo: `test1_mask=None` (`process_modis.py:857-859`, `process_viirs.py:1234-1242`, `process_viirs_mod.py:826-834`); `combine_hot_paths` l.1001: los K1 entran al OR del hot mask | **FALSA** como afirmacion de fidelidad (el paper los retira; el codigo no). El "NO reabrir" sobrevive solo como "no repetir el A/B" (S130: sin sustrato, K1 aparece en 0,09 % de las pasadas MODIS). CLAUDE.md contradice al catalogo y al guard |
| C13 | "NO quedan gaps de fidelidad literal pendientes" (frase conservada por historia) | S114 | mismo que C11 | FALSA; la marca "FALSO desde S137" es correcta |
| C14 | Bandas MODIS 21/22 + 31 | codigo | `process_modis.py:546-561`; D20 registra que el paper usa la 32 para el NTI (PDF l.283-289 "band 32... 12.02 um") y el codigo la 31 | CONDICIONADA (D20: hallazgo despreciable cuantificado S128, pero la regla la presenta como canonica sin decirlo) |
| C15 | radius_km = 25 en los 11 Tier A, 5 en los 34; grilla MIROVA "UTM 51 x 51 km" | volcanoes.yaml + KMZ | yaml: `Counter({5: 34, 25: 11})`; PDF l.327 y l.360 dicen "50 x 50 km" | VIGENTE el conteo. CONDICIONADA el "51 x 51": no esta en Coppola 2016a (50 x 50); si viene del KMZ, la regla no lo cita |
| C16 | inner_radius_km por volcan (tabla de 11) | yaml | yaml: PCC 20, Villarrica 5, Lascar 5, Copahue 4, NdC 5, Llaima 5, Chaiten 5, PP 3, Lastarria 3, Isluga 5, Tupungatito 7 | VIGENTE |
| C17 | campo unificado `final_hotspot_lat/lon/dist_km` | schema | presentes en `data/mirova_equivalent/Villarrica.json` (record 2026-09-13 07:00) | VIGENTE |
| C18 | NTI absoluto floor 0.005 legacy | flags | `NTI_REL_MIN_FLOOR = 0.005`, `ENABLE_NTI_RELATIVE_PATH = False` | VIGENTE (path apagado) |

### 1.2 Reglas A1 a A96 con contenido falsable (las puramente procedimentales van en 1.5)

| Regla | Afirmacion de cierre / marca | Evidencia (hoy) | Veredicto |
|---|---|---|---|
| A6 | ejemplo corregido S127: lineas 234/277/324, `get_detection_anchor`, `get_effective_vent` sin llamador en produccion | `scripts/run_pipeline.py:234/277/324` llaman `get_detection_anchor`; `get_effective_vent` solo en `geo_utils.py:81-87` (alias) y en `tests/test_effective_vent.py` | VIGENTE |
| A7 | marca OBSOLETA: `std_bg_i04` etc. no existen; hoy `diag_sigma_bg_k`, `diag_eff_threshold_k`, `diag_nti_std` | claves del ultimo record de Villarrica: los tres `diag_*` presentes, `std_bg_i04` ausente | VIGENTE la marca |
| A10 | dashboard usa `pc.vrp_mw`; `index.html:1466` `isValidDetection`; helper 25/8/8 usos | `frontend/index.html:1057` `const vmw = pc.vrp_mw`; l.1466 `function isValidDetection(r)`; usos de `mirovaEqVrp`: index **26**, diario 8, mosaico 8, comparacion 0 | VIGENTE (el "25" es 26 hoy; drift trivial). Matiz VIIRS375: `store.py:552-554` persiste `f5_core_vrp_mw` |
| A12 | marca FALSA: dT Lascar 16,9 K, Isluga 8,3 K | recalculado hoy con la definicion del libro: Lascar 16,9 (n=1.792 records V375, 2025-02 a 2026-09), Isluga 8,3 (n=1.754) | VIGENTE la marca |
| A13 | marca FALSA: Villarrica no tiene 0,84 fijo | consolidado snapshot: 0,0 en 3.449 de 3.506 filas (98,4 %), 0,84 en 15 | VIGENTE la marca |
| A17 | marca OBSOLETA + nota S125: OCR partido; `build_c2ab_windows.py:64` apunta al snapshot | `.github/workflows/sync-mirova-csv.yml` existe (cron `12 * * * *`) y NO toca el OCR; `audit-weekly.yml:55-58` refresca ambos CSV del snapshot; `build_c2ab_windows.py:64` `OCR = _SNAP / "registro_vrp_ocr.csv"`; copia congelada `data/mirova_reference/registro_vrp_ocr.csv` 235 filas, max ts 1774684200 (2026-03-28); snapshot 937 filas, max ts 1788764040 (2026-09-06) | VIGENTE (los conteos "887" envejecieron a 937; A90) |
| A23 | marca OBSOLETA: D9 cerrada en sus dos caras | `docs/MIROVA_DIVERGENCES.md:512-526`: cara FP con 0 fuga al dashboard; cap C "adoptada y LIVE" = `PATH_D_ONLY_CAP_TBG_MAX_K = 270.0` | VIGENTE como decision. Observacion: el cierre de la cara de magnitud descansa en un cap por `t_bg` que no esta en Coppola 2016a (MISSION lo clasificaria parche); no es tema de este eje |
| A36 | marca OBSOLETA: no se aplica sec3 | flags nadir `True` | VIGENTE la marca |
| A42 / A43 | marca OBSOLETA; `"on":` con comillas | 26 yml con `"on":`, 0 con `on:` | VIGENTE |
| A45 | tags defensivos previos a tocar pipeline | `git tag`: `pre-s75-vrptir-a2-integration`, `pre-s103-nadir-fixed-viirs` existen | VIGENTE (practica) |
| A63 | regresion S65 a S80 cerrada; test de regresion existe | `geo_utils.py:53-79` `get_detection_anchor` prioriza `vent_lat/lon`; Tupungatito conserva `mirova_center_lat/lon` en el yaml (l.807-808) y `vent_lat/lon` (l.819-820); `tests/test_detection_anchor.py` existe y esta en la suite | VIGENTE |
| A64 | circuit breaker por host de descarga | `pipeline/fetch.py:401-418` documenta breaker de descarga (S102/S109) y de busqueda (S116), `reset_transient_breakers` | VIGENTE (leido el codigo del breaker CMR; el de descarga solo por sus comentarios y `reset_transient_breakers`: CONFIRMADO parcial) |
| A66 / A67 | nadir fijo = modo de area clon literal, restaura la calibracion | flags ON; PERO `docs/MIROVA_DIVERGENCES.md:1896-1906` (S130): con nadir fijo ON, nuestro ratio contra MIROVA cae de 0,740 cerca del nadir a 0,253 sobre 50 grados en VIIRS375 (n=2.767), MIROVA plano; "el brazo fiel seria bow-tie + regrid... no implementado" | **CONDICIONADA**: el area uniforme es necesaria pero no reproduce el remuestreo del paper (PDF l.311-328: bow-tie + regrid a 1 km). "Clon literal" queda demasiado fuerte |
| A69 | causa raiz viva en los 3 sensores; `compute_test1_nti` solo en `process_viirs.py:210/1079`; MODIS y V750 solo `compute_test1_mir` | `process_viirs.py:210` import y `:1079` llamada; `process_modis.py:59` y `process_viirs_mod.py:157` importan solo `compute_test1_mir`; `ENABLE_TEST1_NTI_INTEGRAL = False`, `ENABLE_TEST1_PATH = True` | VIGENTE (la marca "OBSOLETO el cierre" es correcta) |
| A81 / A90 | cara (b) far con pc dentro del inner: 9.196 en S130, tasa plana 15-17 % | script `a81_far_summit_conteo.py`: **9.426** records hoy; sobre records Tier A con cluster y vrp>0 (n=36.170) es 26,1 %; sobre TODOS los records (n=59.294) es 15,9 %; ventana 2025-02 a 2026-09; cara (a) = 0 | VIGENTE (el conteo crece con el corpus, exactamente lo que A90 predice) |
| A82 | far a summit MODIS "irreducible", "todos los ejes agotados", apoyado en "la deteccion MODIS YA es fiel a Coppola 2016a" | C11: la premisa de fidelidad es FALSA en el codigo de hoy (B21 primaria, compuerta 3 K, K1 en el pool); `docs/s137`: con B22 el primer paso de MODIS queda vacio y la compuerta borra el crater de Villarrica (A6 del paper) | **CONDICIONADA**: los ejes "agotados" (discriminantes, N sigma, caps, contexto temporal) se barrieron sobre records producidos con B21 + compuerta. Vale bajo esa configuracion; no vale como "agotado" del problema. CLAUDE.md ya la rebajo por la via geometrica (S124); falta rebajarla por la via espectral, que es la que S137 abrio |
| A83 | no existe discriminante fisico per record; solo el eje espacial separa | AUC medidas en `docs/AUDIT_S116_FOLLOWUP.md` (existe) sobre 4.560 records de la misma configuracion | **CONDICIONADA** (misma razon que A82: los records auditados llevan D21 y D22 adentro; el "objeto" que no se podia separar era en parte ruido de banda 21, S137 midio sigma dNTI 3,5 a 4,7 veces mas alto con B21) |
| A84 | posicion del `ctx_cluster` irreducible; NO re-anclar | probe citado `scratchpad/probe_ctx_cluster_s117.py`: **no existe en el repo** (`find` sin resultado); `docs/superpowers/specs/2026-06-11-ancla-espacial-honesta-design.md` existe | **CONDICIONADA** (misma dependencia de configuracion) y su evidencia primaria NO VERIFICABLE: el script vivio en un scratchpad de sesion |
| A85 | cercas intra-radio: 0 robos en 214 noches; flags OFF | `ENABLE_PATH_D_INTRA_RADIO_GATE = False`, `ENABLE_SECOND_PASS_INTRA_RADIO_GATE = False` | VIGENTE como estado; la medicion "0 robos" no la puedo reproducir sin el run (NO VERIFICABLE el numero) |
| A87 | un flag apagado no prueba que el problema se fue | es una regla de metodo; instancia de hoy: `ENABLE_HONEST_ANCHOR_MODIS_FIRST_PASS_GATE = True` gatea a `ENABLE_HONEST_ANCHOR_MODIS = False` | VIGENTE (regla) |
| A89 | ejemplos: `local_kernel_bg_compatible` con puente en `run_pipeline.py:244`; `enable_utm_regrid` leido de `thresholds`; docstring `process_viirs_mod.py:438` con los 5 opt-in | `run_pipeline.py:244/288/334` `local_kernel_bg_compatible=volcano.get("local_kernel_bg", False)`; yaml opt-in = PCC, Villarrica, Chaiten, PP, Lastarria (5); `profile.py:805` `ENABLE_UTM_REGRID = bool(_t.get("enable_utm_regrid", False))` con `_t = _cfg["thresholds"]` (l.79); `process_viirs_mod.py:433-440` nombra los 5 | VIGENTE. Nota: el docstring de `process_viirs_mod.py:435-440` dice que el kernel local "aun no existe" para M-band; `ENABLE_LOCAL_KERNEL_BG = True` en `process_modis.py:1041` y `process_viirs.py:1398` si tiene implementacion; no verifique si M-band ya la tiene (SOSPECHA, fuera del eje) |
| A92 | barrido de guards por subcadena "tras endurecerlos da 0" | corrido hoy `experiments/_s133/auditar_guards_por_subcadena.py`: **1 candidato**: `tests/test_conectiva_tests23_s136.py:204` `assert "min(" in src` | **FALSA hoy** (envejecio: S136 agrego un guard nuevo con la trampa que A92 describe). Ver H5 |
| A93 / A94 / A95 / A96 | reglas de metodo con ejemplos de S134 a S137 | ejemplos coherentes con `docs/AUDIT_S134.md`, `experiments/_s137/RESULTADO_FONDO_LOCAL.md` (leidos); `git stash list` no lo toque (limite read-only) | VIGENTE (A96 NO VERIFICABLE en su detalle de stashes) |

### 1.3 Encabezados del catalogo `docs/MIROVA_DIVERGENCES.md`

| D | Estado declarado (encabezado) | Evidencia (hoy) | Veredicto |
|---|---|---|---|
| D1 | estructural (1 punto vs N pixeles) | `store.py` persiste `n_anomalous_pixels` y `primary_cluster`; el frontend publica `pc.vrp_mw` | VIGENTE |
| D2 | abierta; cobertura 79,2 % medida S128 | `scripts/libro_de_cuentas.py:157` la cita como cota; no la recalcule | NO VERIFICABLE hoy (numero); estado "abierta, mitigada por CONS union OCR" coherente con `build_c2ab_windows.py:62-64` |
| D3 | abierta; conteos de 2026-04-29 sin instrumento | el propio doc lo declara (l.74-76) | VIGENTE como aviso; los numeros NO VERIFICABLES |
| D9 | CERRADA S113, dos caras | l.512-526; cap C efectivo `PATH_D_ONLY_CAP_TBG_MAX_K = 270.0`; `PATH_D_ATM_GATE_TBG_MIN_K = None` (gate A rechazado, coherente) | VIGENTE como decision (ver observacion en A23) |
| D10 | ctxpeak ADOPTADO S100 | `ENABLE_TEST1_CONTEXTUAL_FILTER = True`, `ENABLE_TEST1_CONTEXTUAL_KEEP_PEAK = True`, `FOCAL_CLUSTER_KEEP_PEAK = True`; `process_viirs.py:1778-1790` | VIGENTE como estado; D19 lo cuestiona (abierta) |
| D11 | encabezado l.1259: "CERRADA S114 (irreducible a 1 km; deteccion fiel a Coppola; todos los ejes agotados)" | C11 y A82: la premisa "deteccion fiel" es falsa hoy; el cuerpo (l.1268 en adelante) ya dice "queda ABIERTA sin candidato activo" en S106 y CLAUDE.md la rebajo en S125, pero el **encabezado** sigue diciendo cerrada y fiel | **FALSA en el encabezado** (H2) |
| D12 | congelada; camino "distance_class desde el cluster" NO ADOPTAR (AUDIT_S121) | `docs/AUDIT_S121_D12_AB.md:1,41` "NO ADOPTAR"; `ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER = False`, `ENABLE_HONEST_ANCHOR_MODIS = False` | VIGENTE como decision. El fenomeno (FN MODIS de Lascar por el Salar) sigue abierto; y con D21/D22 vivas, el A/B de S121 tambien se corrio sobre la configuracion cuestionada (CONDICIONADA como cierre del camino) |
| D13 | ABIERTA (documental): la cerca `distance_class != summit` apaga magnitud | `frontend/index.html:1054` `if (r.distance_class && r.distance_class !== "summit" && !includeFar) return 0;` | VIGENTE |
| D14 | CERRADA S128: mascara de nube fuera, cita verificada | `CLOUD_MASK_BT_K = 0.0`; usos `process_modis.py:568/778` y `process_viirs.py:795` quedan `bt > 0` (no-op); `docs/MISSION.md:127` la lista como parche removido | VIGENTE |
| D15 | hallazgo: `Distancia_km` cuantizado | consolidado Villarrica 0,0 en 98,4 % de las filas (mismo dato que A13) | VIGENTE (coherente con el dato) |
| D16 | CERRADA (refutada): la grilla no explica el sub-reporte | l.1848-1866: A/B de 4 brazos, grilla sola no mueve los ratios; pero D17 l.1896-1911 (S130) prueba que el mecanismo geometrico existe por el eje del angulo y que "el brazo fiel seria bow-tie + regrid... no implementado" | **CONDICIONADA**: refuta el brazo "grilla sin de-solapar", no la hipotesis geometrica completa. El encabezado no lo dice |
| D17 | ABIERTA (premisa probada, consecuencia no) | `ENABLE_UTM_REGRID = False`; `get_grid_center` sin llamadores fuera de `geo_utils.py` (grep, y A89: el regrid en `process_modis.py:502` usa el flag, no esa funcion) | VIGENTE |
| D18 | ABIERTA, A/B S130 NO ADOPTAR | `ENABLE_ROI1_BOX_PAPER = False`; PDF l.349 "box (5 x 5 km)"; yaml circulos 3 a 20 km | VIGENTE como estado. El "NO ADOPTAR" se midio bajo D21+D22 (CONDICIONADA como cierre) |
| D19 | ABIERTA, gravedad 5; decision de Nicolas pendiente | flags keep_peak ON (D10); `ENABLE_SECOND_PASS_CONDITIONED = False` = el second pass corre sin conjunto activo y sin restriccion a adyacentes (`detection_context.py:896-898` y el bloque `if conditioned` al final de `second_pass_adjacent`) | VIGENTE |
| D20 | hallazgo despreciable (banda 31 vs 32) | `process_modis.py:847` (`bt_tir=bt31`) usa la banda 31 para NTI_app del primer pase; PDF l.283-289 banda 32 | VIGENTE (el "despreciable" es numero de S128, NO VERIFICABLE hoy) |
| D21 | ABIERTA: B21 primaria; ningun brazo cumple aun | `ENABLE_MODIS_B22_PRIMARY = False`; `process_modis.py:539-561`; PDF l.307-310; `experiments/_s137/RESULTADO_FONDO_LOCAL.md` tabla de 8 brazos, mejor 5/6 y 3/3 | VIGENTE |
| D22 | ABIERTA: compuerta `bt > t_bg + 3 K` en Tests 2 y 3 | `NTI_BT_SANITY_K = 3.0`; pasada a `first_pass_tests_2_and_3` en `process_modis.py:869`, `process_viirs.py:1240`, `process_viirs_mod.py:832`; aplicada en `detection_context.py:532` (y `:269` en el path dNTI); PDF p.7 sin condicion de temperatura; ademas el path K1 la lleva en `process_modis.py:660-666` | VIGENTE (confirmada en los 3 sensores) |

### 1.4 Secciones "cerrado, no rehacer" de los bloques de arranque

`BLOQUE_ARRANQUE_S134.md` y `S135.md` no tienen esa seccion; tienen "Lo que S133/S134 dejo hecho (para no re-auditar)". Las trato igual.

| Bloque | Afirmacion | Evidencia (hoy) | Veredicto |
|---|---|---|---|
| S134 | A/B del area: NO ADOPTAR (invierte el gradiente) | `ENABLE_GEOLOCATED_PIXEL_AREA = False`; `docs/s133/` existe | VIGENTE como estado; la medicion NO VERIFICABLE hoy |
| S134 | A/B de B22: NO ADOPTAR por ahora (n=2) | `ENABLE_MODIS_B22_PRIMARY = False`; pero S137 midio 8 brazos donde B22 cambia el veredicto en 4 de 9 escenas del Apendice A | **CONDICIONADA**: el "no adoptar" de S133 fue por falta de datos; S137 aporto la medicion que faltaba y la deja como decision pendiente de Nicolas, no como cierre |
| S134 | NRT de MODIS corregido (`MYD021KM` v6.1NRT) | no verificado (no toque fetch de NASA, limite del eje) | NO VERIFICABLE |
| S135 | F1 no cumple; F2 "0,21 km" refutado; F3 = D19; F4 NO ADOPTAR; F5 regla C 7 abiertos / 5 con guard | guards en la suite: `test_guard_regla_c_s134.py`, `test_guard_anillo_s134.py`, `test_guard_keep_peak_s134.py` (2 xfail, coinciden con los 2 xfailed de hoy) | VIGENTE (los guards existen y corren); los numeros de F1/F2/F4 NO VERIFICABLES hoy |
| S136 | las 4 perdidas de Puyehue eran un job degradado; el A/B tiene sustrato; D14 sigue cerrada | D14: si (arriba). Lo demas depende de runs de GitHub | D14 VIGENTE; resto NO VERIFICABLE |
| S137 #1 | recalibrar K1 VIIRS: cerrado por dos vias (empirica y tesis) | `NTI_K1_NIGHT`/-0,8 en Tabla 1 (PDF l.585); la parte de la tesis no la pude localizar en `documentacion/_mm_ch*.txt` (grep sin resultado) | CONDICIONADA / NO VERIFICABLE la pata de la tesis |
| S137 #2 | restaurar la union de caminos: el codigo la construye y la descarta en los 3 sensores; no resuelve las 12 noches | `process_modis.py:824` construye `combine_hot_paths` y `:888` la pisa con `fp_hot`; idem `process_viirs.py:1188/1259`, `process_viirs_mod.py:783/851` | VIGENTE la mitad de codigo (CONFIRMADO); "no resuelve las 12 noches" NO VERIFICABLE hoy |
| S137 #3 | bug far a summit: 4 noches de 946, 3 son NdC | cara (b) hoy: 9.426 records (A81); la conversion a noches no la repeti | VIGENTE en unidad de records; en noches NO VERIFICABLE |
| S137 #4 | discriminante geometrico no separa | no reproducido | NO VERIFICABLE |
| S137 #5 | retirar la interseccion contextual: sigue curando | flags ON (D10); medicion no reproducida | NO VERIFICABLE |
| S137 #6 | la conectiva "en sus dos lecturas" cerrada | `experiments/_s137/RESULTADO_FONDO_LOCAL.md`: la prosa cambia el veredicto en 5 de 8 brazos; S138 #6 ya reabre bajo `max` los tres frentes que S136 cerro | **CONDICIONADA** (S138 lo corrige: "bajo `min` siguen cerrados", bajo `max` viven) |
| S137 #7 | filtro de intensidad de Laiolo no es del pipeline NRT | `documentacion/` no tiene el PDF de Laiolo 2026 (solo `laiolo2017.md` y un `.roto`) | NO VERIFICABLE |
| S137 #8, #9 | ruido de banda insuficiente x6; remuestrear exigiria 137 pixeles | no reproducido; S138 #2 mantiene el remuestreo abierto como fidelidad (D17/D18) | NO VERIFICABLE; coherente con S138 |
| S138 #1 | A/B keep_peak corrido, 260 noches, no correrlo | `docs/PREREGISTRO_AB_D1_D2_S135.md` existe; `experiments/_s137/EL_AB_DE_D1_YA_ESTABA_CORRIDO.md` existe | VIGENTE (existencia); resultado NO VERIFICABLE |
| S138 #3 | "B22 no puede mover la deteccion" refutado | tabla S137: B21 formula 6/6 y 0/3 contra B22 formula 4/6 y 2/3 | VIGENTE |
| S138 #4 | el 6/6 de hoy no es solido (A2 es otro objeto) | `RESULTADO_FONDO_LOCAL.md` seccion "Dos lecturas" | VIGENTE (leido; no reproducido) |
| S138 #5 | tag `pre-s137-keeppeak-ab` borrado a proposito | `git tag` no lo contiene (100 tags) | VIGENTE |
| S138 #6 | los 3 frentes de sigma vuelven a vivir bajo `max` | `combinar` en `detection_context.py:510/920`; `ENABLE_TESTS_23_PROSE_BRANCH = False` hoy | VIGENTE |

### 1.5 Reglas procedimentales (no falsables contra codigo o PDF)

A1, A2, A3, A4, A5, A8, A9, A11, A14, A15, A16, A18, A19, A20, A21, A22, A24, A25, A26, A35, A37, A38, A39, A40, A41, A44, A46, A47, A48, A49, A50, A51, A52, A53, A54, A55, A56-A60, A61, A62, A65, A68, A70, A71, A72, A73, A74, A75, A76, A77, A78, A79, A80, A86, A88, A91: son lecciones de metodo o hechos de sesiones pasadas (runs, A/B, incidentes) que no dejan huella verificable en el codigo de hoy, o cuya huella (documento citado) existe. Las conte como NO VERIFICABLES salvo donde un `ls` confirmo el documento citado (`docs/AUDIT_S103_OVERDETECTION_PCC_VILLARRICA.md`, `docs/S103_VIIRS_NADIR_PROMOTE_RESULTS.md`, `docs/R2_GATES_BY_REGIME.md`, `docs/PROCESS_RULES_S33.md`, `docs/AUDIT_S116_FOLLOWUP.md`, `docs/S113_A46_COHERENCE_GUARD.md`, `experiments/50_FACTOR_42_HALLAZGO.md`: todos existen). A80 con su refinamiento S116 es coherente con el estado (usa `nti_max` solo como sanity). A76 depende de una nota de memoria, no del repo.

## 2. Conteo con denominador

Universo revisado: **76 afirmaciones falsables** = 18 de Reglas cientificas (1.1) + 23 filas de reglas A con contenido falsable o marca (1.2) + 17 encabezados D (1.3) + 18 items de los bloques S134 a S138 (1.4). Las reglas procedimentales de 1.5 no entran al denominador porque no admiten veredicto contra codigo o PDF.

| Veredicto | n | % |
|---|---|---|
| VIGENTE | 52 | 68,4 |
| CONDICIONADA | 11 | 14,5 |
| FALSA | 5 | 6,6 |
| NO VERIFICABLE (en esta sesion) | 8 | 10,5 |

Las 5 FALSAS: C11 (deteccion MODIS fiel), C12 (GAP #A mislabel, no reabrir), C13 (no quedan gaps), D11 encabezado (cerrada, fiel, agotada) y A92 ("da 0"). Dos ya llevan marca correcta en CLAUDE.md (C11, C13); las otras tres no.

Las 11 CONDICIONADAS comparten un patron: **se derivaron sobre records producidos con banda 21 primaria y compuerta de 3 K** (A82, A83, A84, S134 B22, S137 #6) o valen solo bajo la lectura de la formula (C6), o solo para el brazo que se probo (D16, A66/A67, C8), o citan un dato que no viene del paper que dicen (C14, C15). Es el patron de A95 aplicado a todo el catalogo: la lectura del paper que hoy sabemos incompleta (S137) esta debajo de casi todo lo que se declaro agotado.

Medida de envejecimiento: **16 de 76 (21 %)** de las afirmaciones falsables ya no valen tal como estan escritas (FALSA o CONDICIONADA), y 3 de las 5 falsas no llevan ninguna marca.

## 3. Hallazgos, por gravedad

### H1. CLAUDE.md sigue diciendo que el GAP #A es un "mislabel" que no hay que reabrir; el catalogo y un guard de la suite dicen lo contrario, y el codigo le da la razon al catalogo
- ARCHIVO:LINEA: `CLAUDE.md` (proyecto), seccion Reglas cientificas, frase "GAP #A ... RESUELTO S115 = MISLABEL ... NO reabrir"; `docs/MIROVA_DIVERGENCES.md:1319-1335`; `tests/test_guard_gap_a_pool_musigma_s128.py:1-30`; `pipeline/process_modis.py:857-859` (`test1_mask=None` porque `ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK = False`); `pipeline/detection_context.py:485-489` (mu/sigma sobre ese pool); PDF p.6 (volcado l.556-558).
- QUE PASA: el paper retira del fondo a los pixeles que ya dispararon el Test 1 (los mas calientes de la escena) antes de calcular mu y sigma. Nosotros los dejamos adentro: el fondo se infla y el umbral `mu + C2 sigma` sube. El efecto medido en S130 es nulo hoy porque casi no hay pixeles K1 (0,09 % de las pasadas MODIS), pero la regla vinculante dice "no es gap", que es falso, y esa frase apaga el frente si un volcan entra en fase efusiva (donde si habria K1).
- COMO SE VE EN EL DASHBOARD: invisible hoy; en fase efusiva seria un umbral mas alto = detecciones que se pierden alrededor de la lava.
- COMO REPRODUCIRLO: `VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p; print(p.ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK)"` da `False`; leer `process_modis.py:857-859`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 3 (torceria decisiones solo en fase efusiva; hoy tuerce la lista de frentes).

### H2. El encabezado de D11 dice "CERRADA S114, deteccion fiel a Coppola, todos los ejes agotados" y ninguna de las tres cosas vale hoy
- ARCHIVO:LINEA: `docs/MIROVA_DIVERGENCES.md:1259`; contra `process_modis.py:544` (B21), `:869` (compuerta), `:857-859` (K1 en el pool); PDF l.307-310 y p.7.
- QUE PASA: el gradiente topografico que D11 describe se midio con una banda ruidosa (B21) y una compuerta de temperatura que el paper no tiene; S137 mostro que con B22 el primer paso de MODIS queda vacio. Los "ejes agotados" (A82, A83, A84) se barrieron sobre esa configuracion. CLAUDE.md ya rebajo A82 por la via geometrica; nadie rebajo el encabezado de D11 ni la via espectral.
- COMO SE VE EN EL DASHBOARD: invisible directamente; apaga el trabajo que podria cambiar el recall MODIS (hoy 16 % segun S114, numero no reproducido aqui).
- COMO REPRODUCIRLO: `grep -n "CERRADA S114" docs/MIROVA_DIVERGENCES.md`; comparar con D21 y D22 del mismo archivo.
- CONFIANZA: CONFIRMADO (la contradiccion documental); SOSPECHA (que al corregir D21/D22 el sesgo de D11 cambie).
- GRAVEDAD: 3.

### H3. Las afirmaciones "agotado / irreducible / no adoptar" de A82, A83, A84, D12 (camino), D18 (A/B) y S134 (B22) heredan la configuracion que S137 puso en duda
- ARCHIVO:LINEA: `CLAUDE.md` A82, A83, A84; `docs/MIROVA_DIVERGENCES.md:1399-1407` (D12), `:1971` (D18); `tasks/BLOQUE_ARRANQUE_S134.md:73-74`.
- QUE PASA: es A95 en masa. Cada uno de esos cierres se apoya en records o A/B corridos con B21 primaria y compuerta de 3 K en los Tests 2 y 3. No digo que sean falsos: digo que no se sabe, y que estan escritos como si se supiera.
- COMO SE VE EN EL DASHBOARD: invisible.
- COMO REPRODUCIRLO: para cada uno, buscar la fecha del A/B y comparar con la fecha de `ENABLE_MODIS_B22_PRIMARY` (S133) y de D22 (S137).
- CONFIANZA: CONFIRMADO (la dependencia); SOSPECHA (el efecto).
- GRAVEDAD: 3.

### H4. A66/A67 llaman "clon literal" al area nadir fija; el paper remuestrea (bow-tie + grilla de 1 km) y S130 midio que nuestro ratio contra MIROVA cae 2,7 veces con el angulo aun con nadir fijo ON
- ARCHIVO:LINEA: `CLAUDE.md` A66, A67; `docs/MIROVA_DIVERGENCES.md:1896-1911`; flags nadir `True`; `ENABLE_UTM_REGRID = False`; PDF l.311-328.
- QUE PASA: fisicamente, un pixel oblicuo de VIIRS integra hasta cuatro veces mas terreno que uno al nadir; el paper elimina eso remuestreando antes de detectar. Nosotros solo fijamos el area en la formula de VRP. La magnitud publicada depende del angulo de la pasada (0,74 a nadir, 0,25 sobre 50 grados, n=2.767 pares VIIRS375, S130).
- COMO SE VE EN EL DASHBOARD: el mismo volcan, la misma noche, reporta magnitudes distintas segun la pasada; el operador ve una serie con dientes que no son del volcan.
- COMO REPRODUCIRLO: `docs/s130/GRADIENTE_CENITAL.md` (existe) y su script.
- CONFIANZA: CONFIRMADO (documentado en el repo; no reproduje el numero).
- GRAVEDAD: 3 (magnitud, no deteccion).

### H5. El guard de la conectiva de S136 pasa por coincidencia: vigila `min(` y `max(`, y la conectiva real no lleva parentesis
- ARCHIVO:LINEA: `tests/test_conectiva_tests23_s136.py:196-204`; `pipeline/detection_context.py:510` y `:920` (`combinar = max if use_prose_branch else min`); los `min(` que satisfacen el assert estan en `detection_context.py:254, 256, 588, 589` (recorte de bounding box y cap de sigma), los `max(` en `:253, 255`.
- QUE PASA: si alguien reemplaza la conectiva por otra cosa, el test sigue verde. Es exactamente la trampa de A92, y A92 dice que el barrido "da 0"; hoy da 1, este.
- COMO SE VE EN EL DASHBOARD: invisible (es un guard).
- COMO REPRODUCIRLO: `python experiments/_s133/auditar_guards_por_subcadena.py` (candidatos: 1); `grep -n "min(" pipeline/detection_context.py`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2.

### H6. El second pass calcula mu y sigma sobre un pool distinto al del primer pase: sin los pisos de -0,1 ni el filtro de borde
- ARCHIVO:LINEA: `pipeline/detection_context.py:904-910` (`bg_mask = (~active_mask) & isfinite(dnti) & isfinite(deti)`) contra `:476-495` del primer pase (`build_unsuitable_mask` con pisos y borde); PDF p.5 (volcado l.502-513: los unsuitable son parte del "step 2") y p.8 (l.615-620: "step 2 ... is performed a second time").
- QUE PASA: el paper repite el paso espacial entero, incluidos los descartes; el codigo repite solo el promedio de vecinos. Los outliers negativos (bordes de nube) vuelven a entrar al fondo del second pass y le inflan sigma. El ROI si se conserva (el ETI es NaN fuera de `mask_valid_eti`), asi que el pool no se va a todo el granule.
- COMO SE VE EN EL DASHBOARD: invisible salvo por la recaptura de pixeles marginales; con `ENABLE_SECOND_PASS_CONDITIONED = False` el second pass ya es el mecanismo de D19.
- COMO REPRODUCIRLO: leer las dos funciones; medir con un probe A75 la diferencia de `sd_dnti` entre pases.
- CONFIANZA: CONFIRMADO (divergencia literal); SOSPECHA (tamano del efecto).
- GRAVEDAD: 2.

### H7. CLAUDE.md cita "grilla MIROVA UTM 51 x 51 km"; Coppola 2016a dice 50 x 50 km dos veces
- ARCHIVO:LINEA: `CLAUDE.md` Reglas geometricas S14; PDF volcado l.327 y l.360; D13 repite "51 x 51".
- QUE PASA: si el 51 viene del KMZ, la regla no lo cita; el radio inscrito de 25,5 km que justifica `radius_km = 25` se apoya en ese numero.
- COMO SE VE EN EL DASHBOARD: invisible.
- CONFIANZA: CONFIRMADO (la discrepancia documental).
- GRAVEDAD: 1.

### H8. A84 cita como evidencia primaria un script que no esta en el repo
- ARCHIVO:LINEA: `CLAUDE.md` A84 cita `scratchpad/probe_ctx_cluster_s117.py`; `find . -name "probe_ctx_cluster_s117*"` sin resultado.
- QUE PASA: la regla "NO re-anclar" descansa en un probe que vivio en un scratchpad de sesion. No se puede volver a correr.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

### H9. Conteos absolutos envejecidos sin marca (A90 sobre CLAUDE.md mismo)
- `mirovaEqVrp` en `index.html`: 25 declarado, 26 hoy. OCR del snapshot: 887 filas declaradas, 937 hoy. Cara (b) de A81: 9.196 declarado (S130), 9.426 hoy. Ninguno cambia un veredicto.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 1.

## 4. VERIFICADO LIMPIO (no hace falta volver a mirar)

- **Tabla 1 del paper contra los flags efectivos**: K1 -0,8 noche, C1 0,003/0,01 noche y 0,02 dia, C2 5/10 noche y 15 dia. Comando: `VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p; print(p.DNTI_CONTEXTUAL_C1_SUMMIT, p.DNTI_CONTEXTUAL_C1_SCENE, p.DNTI_CONTEXTUAL_C1_DAY, p.N_SIGMA_MIR_SUMMIT, p.N_SIGMA_MIR_SCENE, p.N_SIGMA_MIR_DAY)"` y PDF volcado l.583-596.
- **Coeficientes de Wooster y Stefan-Boltzmann**: `grep -n "WOOSTER_COEFF =" pipeline/process_*.py`; `pipeline/constants.py:14`.
- **Kernel de 8 vecinos aritmetico**: `grep -n "np.median\|nanmedian" pipeline/detection_context.py` solo devuelve el fondo de magnitud (l.1064) y un comentario historico; el kernel es `_nanmean_8neighbors_fast`.
- **Conectiva por defecto = formula del paper**: `ENABLE_TESTS_23_PROSE_BRANCH = False`; `detection_context.py:510`.
- **D22 confirmada en los tres sensores**: `grep -n "bt_sanity_k=NTI_BT_SANITY_K" pipeline/process_*.py` (3 llamadas a `first_pass_tests_2_and_3`).
- **D21 confirmada**: `ENABLE_MODIS_B22_PRIMARY = False`; `process_modis.py:544/548/561`.
- **Ancla de deteccion al crater (A63)**: `geo_utils.py:53-79`; `tests/test_detection_anchor.py` en la suite verde.
- **Gates intra-radio S84/S85 apagados (A85)**: `ENABLE_PATH_D_INTRA_RADIO_GATE = False`, `ENABLE_SECOND_PASS_INTRA_RADIO_GATE = False`.
- **Mascara de nube apagada (D14)**: `CLOUD_MASK_BT_K = 0.0`.
- **Nadir fijo ON en los 3 sensores (A36 obsoleta correcta)**: flags `True`.
- **Los tres A/B "NO ADOPTAR" siguen apagados**: `ENABLE_GEOLOCATED_PIXEL_AREA`, `ENABLE_ROI1_BOX_PAPER`, `ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER`, `ENABLE_HONEST_ANCHOR_MODIS`, `ENABLE_UTM_REGRID`, todos `False`.
- **Union de caminos construida y descartada (S137 #2)**: `grep -n "hot_mask_2d = combine_hot_paths\|hot_mask_2d = fp_hot" pipeline/process_*.py` (3 pares).
- **`"on":` con comillas en los 26 workflows (A43)**: `grep -l '^on:' .github/workflows/*.yml | wc -l` = 0.
- **Tags defensivos**: `pre-s75-vrptir-a2-integration`, `pre-s103-nadir-fixed-viirs` existen; `pre-s137-keeppeak-ab` no (S138 #5).
- **Marcas OBSOLETA/FALSA de CLAUDE.md que verifique y son correctas**: A7, A12, A13, A17, A23, A36, A42, A69 (cierre obsoleto), A81/A90, C13.
- **volcanoes.yaml**: 45 volcanes, `radius_km` {25: 11, 5: 34}, 11 `inner_radius_km` iguales a la tabla, 5 opt-in `local_kernel_bg`.
- **Suite**: 1325 passed, 4 skipped, 2 xfailed (los 2 xfail son `test_guard_keep_peak_s134.py`, como declara S135).
- **A81 cara (a) (summit con cluster fuera del inner)**: 0 records hoy sobre n=36.170 (el guard S113 sigue haciendo su trabajo).

## 5. Scripts y salidas de esta sesion

- `experiments/_s138_audit/eje1/profile_flags_efectivos.txt` (flags efectivos, 140 lineas)
- `experiments/_s138_audit/eje1/sp426_5_pymupdf.txt` (paper, 25 paginas)
- `experiments/_s138_audit/eje1/pytest_s138_eje1.txt` (suite)
- `experiments/_s138_audit/eje1/a81_far_summit_conteo.py` y `.txt` (conteo A81 con denominador y serie mensual)
