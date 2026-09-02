# S131 · Eje «lo declarado vs lo efectivo» (T9)

> Todos los números salen de
> `experiments/_s131_audit/declarado_vs_efectivo/01_verificar.py` → `01_resultados.json`.
> Ninguno transcrito a mano (S91). Los guards propuestos están escritos y corriendo en
> `experiments/_s131_audit/declarado_vs_efectivo/02_guards_propuestos.py`.
> Sesión read-only: no se tocó git, ni el pipeline, ni los docs auditados.

## Resultado

**47 afirmaciones verificadas · 15 CONFIRMADAS · 16 FALSAS · 13 OBSOLETAS · 3 SIN RESPALDO.**
De las 16 falsas, **cuatro están en el documento legal publicable** (`FICHA_SDA_VRP_CHILE.md`
y la cabecera FICHA de un módulo), que es donde una afirmación falsa cuesta más caro.

Lo más importante en una línea: **la ficha de transparencia declara un producto satelital que
el sistema nunca descarga y dos mitigaciones de sesgo que están apagadas en el perfil
operacional**; y **el README le atribuye al pipeline el centrado de grilla que la divergencia
D17 declara justamente NO implementado**. Los tres son afirmaciones sobre el sistema hechas
hacia afuera.

Un patrón se repite y conviene nombrarlo antes de la tabla: en cuatro de los cinco hallazgos
graves **el texto correcto ya existía en el repo**. `process_modis.py:10` nombra bien el
producto MODIS mientras la ficha lo nombra mal; `docs/MIROVA_DIVERGENCES.md:1883` dice que la
grilla no está centrada donde el README dice que sí; `scripts/libro_de_cuentas.py:261` mide el
ΔT de Láscar que A12 declara mal, desde S128. Es el corolario de A89 otra vez: el error no está
en el código, está en quien lo describe, y el desmentido ya estaba escrito.

### Conteos por fuente

| fuente | confirmadas | falsas | obsoletas | sin respaldo | n |
|---|---|---|---|---|---|
| `docs/FICHA_SDA_VRP_CHILE.md` (+ cabecera FICHA de `vrp_regimes.py`) | 4 | 4 | 1 | 1 | 10 |
| `docs/MISSION.md` | 1 | 0 | 4 | 0 | 5 |
| `CLAUDE.md` (incluye las citas `file:line` y los coeficientes Wooster) | 6 | 6 | 1 | 0 | 13 |
| `README.md` | 2 | 3 | 1 | 0 | 6 |
| `docs/MIROVA_DIVERGENCES.md` | 1 | 0 | 2 | 1 | 4 |
| `docs/INDEX.md` | 0 | 0 | 1 | 0 | 1 |
| `MAPA_WORKSPACE.md` (workspace) | 0 | 2 | 0 | 0 | 2 |
| docstrings y comentarios de `pipeline/` | 1 | 0 | 3 | 0 | 4 |
| dato publicado (`data/mirova_equivalent/`) | 0 | 1 | 0 | 0 | 1 |
| `scripts/libro_de_cuentas.py` | 0 | 0 | 0 | 1 | 1 |
| **total** | **15** | **16** | **13** | **3** | **47** |

*(Los conteos salen de `01_resultados.json`, no de contar las filas de las tablas de abajo:
esas incluyen tres entradas descriptivas —R7, P5, P6— que remiten a un check ya contado en
otra fila y no se suman dos veces.)*

### Los 5 más graves

1. **La ficha legal dice que el sistema se alimenta de MOD14/MYD14** — el producto de
   anomalías térmicas/incendios de MODIS. El pipeline descarga **MOD021KM/MYD021KM** (radiancias
   L1B calibradas) más `MOD03/MYD03` de geolocalización, y calcula las anomalías él mismo. Es
   una descripción incorrecta de la entrada del SDA en un documento pensado para publicarse.
   Se propaga además a `pipeline/vrp_regimes.py:10`.
2. **La ficha declara dos mitigaciones de sesgo que están apagadas**: «zonas de exclusión»
   (`ENABLE_EXCLUDE_ZONES=False`, removidas en S27 y listadas por `MISSION.md` como parche
   retirado) y el sesgo topográfico «mitigado normalizando por índice térmico (NTI)»
   (`ENABLE_TEST1_NTI_INTEGRAL=False`; `compute_test1_nti` sólo se importa en VIIRS 375, y MODIS
   y V750 importan únicamente `compute_test1_mir`). O sea: la ficha declara mitigado un límite
   físico que sigue sin mitigar, y en el sensor donde el píxel grande lo amplifica (A80).
3. **El README afirma que la grilla de 50×50 km usa el centro oficial de MIROVA, «desacoplado a
   propósito» del cráter.** No lo usa: `get_grid_center()` (`geo_utils.py:29`) no tiene ningún
   llamador en producción y `ENABLE_UTM_REGRID=False`. Es exactamente lo que D17 declara como
   consecuencia NO implementada y lo que AUDIT_S127 Hallazgo 7 volvió a verificar.
4. **1.635 records publicados llevan el sello del piso VRP sin que el piso haya actuado.**
   `store.py:99-103` escribe `diag_vrp_floor_mw` y `vrp_mw = 0.0` juntos, así que el sello
   implica magnitud cero. En el corpus vivo (60.694 records, 2025-02 a 2026-09) hay 1.635
   sellados y **los 1.635 tienen `vrp_mw > 0`** — el reproceso de S130 restauró la magnitud y
   dejó el sello pegado. Una auditoría futura leería «el piso pisó 1.635 records» y sería falso
   (A87 + A90).
5. **A12 sigue sin marcar y su ejemplo contradice su propia regla.** Declara «Láscar 21,6 K,
   Isluga ~20 K» como volcanes con ΔT > 20 K calibrados sin fix; medido dan **16,9 K y 8,3 K**.
   Isluga cae **debajo** del corte de 12 K con el que A12 define la clase que SÍ necesita
   kernel-bg. `scripts/libro_de_cuentas.py:261-264` lo registra desde S128 y la regla siguió sin
   marcar — Fuga 1 del protocolo, en directo.

---

## Tabla por fuente

Severidad: ALTA = puede inducir una decisión equivocada o va en un documento publicable ·
MEDIA = confunde a una sesión fría · BAJA = deriva de referencia.

### 1 · `docs/FICHA_SDA_VRP_CHILE.md` (documento legal, CPLT Res. Ex. N°372)

| # | afirmación | estado | evidencia | fix propuesto |
|---|---|---|---|---|
| F1 | «Categorías de datos: … sensores MODIS (**MOD14/MYD14**) y VIIRS» | **FALSO** · ALTA | `pipeline/fetch.py:176-183` sólo pide `MOD021KM`/`MYD021KM`/`MOD03`/`MYD03`; `MOD14` no aparece en ningún short_name. `pipeline/process_modis.py:10` ya lo dice bien | reemplazar por: «Radiancia y temperatura de brillo de los productos calibrados de nivel 1B: MODIS `MOD021KM`/`MYD021KM` con su geolocalización `MOD03`/`MYD03`, y VIIRS `VNP02IMG`/`VJ102IMG`/`VJ202IMG` (375 m) y `VNP02MOD`/`VJ102MOD`/`VJ202MOD` (750 m) con sus geolocalizaciones. El sistema calcula las anomalías térmicas a partir de la radiancia; no consume productos de anomalías de terceros.» |
| F2 | «Mitigación: filtros de contexto, **zonas de exclusión** y degradación explícita a fondo regional» | **FALSO** · ALTA | `ENABLE_EXCLUDE_ZONES=False` en el perfil operacional; `MISSION.md` las lista como parche removido en S27 por no estar en los papers MIROVA | quitar «zonas de exclusión» de la enumeración. El texto queda: «Mitigación: filtros de contexto y degradación explícita a fondo regional.» |
| F3 | «*Sesgo topográfico …* mitigado normalizando por índice térmico (NTI).» | **FALSO** · ALTA | `ENABLE_TEST1_NTI_INTEGRAL=False`; `compute_test1_nti` se importa sólo en `process_viirs.py:206`, mientras `process_modis.py:59` y `process_viirs_mod.py:153` importan únicamente `compute_test1_mir` | reemplazar la última cláusula por: «El sistema no aplica hoy una corrección para este sesgo: la normalización por índice térmico (NTI) está implementada pero desactivada, y la posición estimada del foco puede desplazarse hasta ~1 km respecto del cráter en los volcanes de cumbre nevada. El límite está caracterizado y documentado.» |
| F4 | «*Artefactos solares diurnos:* … mitigado restringiendo la detección MIR a pasadas nocturnas» | CONFIRMADO | `scripts/run_pipeline.py:170` `nighttime_only=True` por defecto, aplicado en las tres ramas de sensor (l. 227, 270, 317); `nrt.yml:176,196` no pasa `--no-night-filter` | — |
| F5 | v1.4: «los parámetros del ajuste (activación, umbral 5,0 MW y máximo de 3 píxeles) permanecen idénticos» | CONFIRMADO | `SUB_MW_REGIME_THRESHOLD_MW=5.0`, `SINGLE_PIXEL_MAX_CLUSTER_PIXELS=3` | — |
| F6 | v1.3: `path_d_intra_radio.py` y `second_pass_intra_radio.py` desactivados | CONFIRMADO | ambos flags `False` en el perfil efectivo | — |
| F7 | v1.2: `vrptir.py` diagnóstico (`ENABLE_VRPTIR_AVENI=False`) y `detect_tirvolch.py` sin referencias en producción | CONFIRMADO | flag `False`; ningún módulo importa `detect_tirvolch` | — |
| F8 | El historial declara **14** módulos con cabecera FICHA (6 núcleo en v1.1 + 8 secundarios en v1.2) | **OBSOLETO** · MEDIA | hoy son **16**: `regrid.py` y `vrp_regimes.py` llevan la cabecera sin que ninguna versión de la ficha los declare | agregar una fila v1.5 al historial que registre la incorporación de `regrid.py` y `vrp_regimes.py`, o —mejor, siguiendo el criterio de v1.4— **borrar el conteo del historial** y apuntar al guard que enumera los módulos con cabecera |
| F9 | Alcance de trazabilidad: `scan_geometry.py` | **SIN RESPALDO** · MEDIA | el módulo fija `A_pix`, multiplicador directo del VRP, o sea cae bajo el criterio v1.2 «módulos que deciden la magnitud»; no tiene cabecera FICHA y tampoco figura en la lista de exclusiones justificadas | decidir explícitamente: o cabecera FICHA en `scan_geometry.py`, o una línea en el criterio de alcance de v1.2 que lo excluya con razón escrita. Hoy no está ni adentro ni afuera |
| F10 | Cabecera FICHA de `pipeline/vrp_regimes.py:10`: «Datos entrada: Radiancia MODIS (MOD14/MYD14) y VIIRS» | **FALSO** · ALTA | contra `pipeline/process_modis.py:10`, que dice `MOD021KM/MYD021KM` correctamente | alinear con la redacción de `process_modis.py:10`: «Datos entrada : Radiancia/temperatura de brillo MODIS MOD021KM/MYD021KM y VIIRS I04/I05, M13/M15. SIN datos personales.» |

### 2 · `docs/MISSION.md`

| # | afirmación | estado | evidencia | fix propuesto |
|---|---|---|---|---|
| M1 | «Pisos VRP por sensor — ⚠️ **SIGUEN ACTIVOS** (corregido S124). `pipeline/store.py:459-468` aplica `MIN_VRP_MW_VIIRS375=0.02`, `_VIIRS750=0.15`, `_MODIS=0.05` … Alcance medido S124: 1564 de 23990 records summit (6,5 %)» | **OBSOLETO** · ALTA | los tres pisos valen **0.0** en el perfil efectivo (S130 los retiró). La cita también drifteó: el helper es `store.py:72-103` y se llama en `store.py:489`; las líneas 459-468 son hoy el guard A46 | reemplazar la celda de estado por: «⚠️ **RETIRADOS S130.** Los tres pisos valen `0.0` en `mirova_equivalent.yaml`; el mecanismo se conserva en `pipeline/store.py:_apply_vrp_floor` porque el perfil `experimental` sigue usándolo. La decisión se apoya en el canon (Coppola 2014 midió el corte en 2 MW y lo rechazó). Alcance del retiro: 582 de 57.730 records dejaron de ser invisibles al dashboard.» |
| M2 | «Cloud mask BT<260K — ⚠️ **SIGUE ACTIVA en VIIRS 375**. `process_viirs.py:674` tiene `CLOUD_BT_THRESHOLD = 260.0` hardcodeado … Retirarla es cambiar el literal por la constante del perfil (una línea, requiere A45)» | **OBSOLETO** · ALTA | `process_viirs.py:786` dice `CLOUD_BT_THRESHOLD = CLOUD_MASK_BT_K` y el perfil vale `0.0`. El cambio de una línea que MISSION propone **ya se hizo en S126 (#535)** | reemplazar por: «✅ **RETIRADA S126 (#535).** El umbral sale del perfil (`process_viirs.py:786`) y `cloud_mask_bt_k` vale `0.0` desde S29, así que la máscara está apagada en los tres sensores. D14 cerrada en S127 con la cita de Laiolo 2026 verificada verbatim. Guards: `tests/test_cloud_mask_from_profile_s125.py` y `tests/test_cloud_mask_operacional_s126.py`.» |
| M3 | Regla D Test 1-priority «está vivo y **sin flag** en los 3 procesadores (`process_viirs.py:1502-1568`, `process_modis.py:1167-1204`, `process_viirs_mod.py:1055`)» | **OBSOLETO** · BAJA | los bloques están hoy en `process_viirs.py:1642-1710`, `process_modis.py:1196-1230`, `process_viirs_mod.py:1069`; y ya no es «sin flag»: `process_viirs.py:1695` pasa `weak_cluster_enabled=ENABLE_TEST1_PRIORITY_WEAK_CLUSTER` | actualizar las tres referencias y cambiar «sin flag» por «parcialmente gateado: la rama de clúster rival débil depende de `ENABLE_TEST1_PRIORITY_WEAK_CLUSTER`; las dos ramas históricas (Regla D y única fuente) corren siempre». **Mejor aún**: quitar los números de línea y nombrar el bloque (`# Regla D Test 1-priority`), que es estable y greppeable |
| M4 | `MAX_SIGMA_COMPONENT_K` neutralizado por valor (999.0), default del código 7.0 | CONFIRMADO | perfil efectivo `999.0` | — |
| M5 | Resumen de divergencias: «**Abiertas**: D2 · D3 · D11 cara posición» | **OBSOLETO** · MEDIA | el catálogo declara además **D13** abierta (documental, S124, `:1457`), **D17** abierta (S124/S125, `:1883`) y **D18** abierta (S129/S130, `:1960`). El resumen quedó congelado en S105 | borrar la enumeración y reemplazarla por: «El catálogo `docs/MIROVA_DIVERGENCES.md` es la lista viva; esta sección no la duplica. Para el estado de hoy, leer los encabezados de cada D en ese archivo.» Es el mismo remedio que S127 aplicó a la lista de volcanes: una lista copiada envejece sola |

### 3 · `CLAUDE.md`

| # | afirmación | estado | evidencia | fix propuesto |
|---|---|---|---|---|
| C1 | l. 126: «**`radius_km = 25 km` uniforme** para volcanes chilenos» | **FALSO** · MEDIA | `volcanoes.yaml`: `{5: 34, 25: 11}` — 25 km sólo en los 11 Tier A | «**`radius_km = 25 km` en los 11 Tier A** — replica la grilla MIROVA UTM 51×51 km (radio inscrito 25,5 km). Los 34 volcanes restantes quedan en 5 km.» |
| C2 | Tabla `inner_radius_km` por volcán (Reglas geométricas S14) | CONFIRMADO | coincide en los 11 contra `volcanoes.yaml` | — |
| C3 | l. 1091: «`volcanoes.yaml` (45 configurados, **11 con data, 34 sin pull**)» | **FALSO** · MEDIA | los 45 tienen archivo con records en `data/mirova_equivalent/`; los 34 no-Tier-A traen entre **67 y 94** records cada uno (ventana 2026-04-17 a 2026-04-24) | «`volcanoes.yaml` (45 configurados · 11 Tier A con serie continua desde 2025-02 · 34 con una ventana corta de abril-2026 en `data/mirova_equivalent/`, fuera del cron NRT)» |
| C4 | l. 1233: «los **6** workflows que hacen `git push` a main comparten `group: push-main` — nrt, **nrt-retry**, sync-mirova-csv, **audit-weekly**, backfill y reproc» | **FALSO** · ALTA | **9** workflows hacen `git push`; **5** están en `push-main` (`backfill-geometry`, `backfill-tier-a`, `nrt`, `reproc-s120-eq16-villarrica`, `sync-mirova-csv`). **`nrt-retry.yml` no pushea** — dispara `nrt.yml` con `gh workflow run` (l. 99) y no declara concurrency alguna. **`audit-weekly.yml` sí pushea** pero con grupo propio `audit-weekly` | ver C5: se arreglan juntas |
| C5 | l. 1238: «**Verificado S127: hay 3 excepciones deliberadas**» (`reproc-s124-ndc-focus`, `reproc-s124-villarrica-op-ab`, job `merge` de `reproc-chunked`) | **FALSO** · MEDIA | son **4**: se suma `audit-weekly.yml`, que cumple el criterio (retry ×5 con backoff, `audit-weekly.yml:71-77`) pero no está documentada | reemplazar las dos entradas por: «**Concurrency**: un workflow que hace `git push` a main debe tener **o** `group: push-main`, **o** su propio bucle de reintento `pull --rebase` + `push` (5 intentos con backoff). Las dos cosas juntas sólo agregan el riesgo de perder runs encolados, porque GitHub mantiene un solo run pendiente por grupo y `nrt.yml` ocupa el lock ~50 min de cada 2 h. **No listar acá quién está en cada grupo** — la lista envejece; la mide `tests/test_guard_declarado_vs_efectivo_s131.py::G4`. En `nrt.yml` el grupo va a nivel **workflow**, nunca a nivel job (los 11 volcanes son una matrix y se perderían 9 por corrida).» |
| C6 | A43: todo yml nuevo usa `"on":` entre comillas | CONFIRMADO | los 18 workflows parsean la clave como string con `yaml.safe_load` | — |
| C7 | `nrt.yml`: cron cada 2 h, matrix por volcán, timeout 50 min per-step, max-parallel 8, fail-fast false | CONFIRMADO | `cron "0 */2 * * *"` (l. 12), `timeout-minutes: 50` en los dos pasos de proceso (l. 173 y 193), job 60 (l. 69), `max-parallel: 8` (l. 80), `fail-fast: false` (l. 76) | — |
| C8 | A12, l. 215: «Vols con ΔT >20K (**Lascar 21.6K, Isluga ~20K**) calibrados naturalmente sin fix» | **FALSO** · ALTA | medido: Láscar **16,9 K**, Isluga **8,3 K**. Isluga queda **debajo** del corte de 12 K con el que la propia A12 define la clase que necesita kernel-bg. Registrado en `scripts/libro_de_cuentas.py:261-264` desde S128 | marcar la regla: «⚠️ **El ejemplo es FALSO — medido S128, marcado S131.** Los ΔT reales son Láscar **16,9 K** e Isluga **8,3 K** (`scripts/libro_de_cuentas.py`, ids `A12_dT_lascar`/`A12_dT_isluga`). Isluga cae debajo del propio corte de 12 K, o sea el ejemplo ilustra la clase contraria a la que dice ilustrar. **El mecanismo de A12 sigue valiendo** (ΔT bajo + anillo frío → ΔL inflado en Test 1 integrado); lo que no vale es usar estos dos volcanes como el caso "no necesita fix", ni el umbral de 20 K derivado de ellos. A19 se apoya en A12 y hereda el caveat.» |
| C9 | frontend: 3 vistas live + `comparacion.html` preview sin `mirovaEqVrp` (25/8/8/0) | CONFIRMADO | conteo real: index 25, diario 8, mosaico 8, comparación 0 | — |
| C10 | Coeficientes Wooster 18,9 (MODIS) / 19,7 (V750) / 18,0 (V375) | CONFIRMADO | `process_modis.py:82`, `process_viirs_mod.py:63`, `process_viirs.py:74` | — |
| C11 | N·σ 5 summit / 10 scene / 15 día; C1 0,003 / 0,010 / 0,02; NTI floor 0,005 | CONFIRMADO | perfil efectivo: 5,0 / 10,0 / 15,0 · 0,003 / 0,01 / 0,02 · 0,005 | — |
| C12 | Sección Estado §4: «abiertas D2 y D3 … y D12» | **OBSOLETO** · MEDIA | el catálogo declara además D13, D17 y D18 abiertas | mismo remedio que M5: no duplicar la lista, apuntar al catálogo |
| C13 | Citas `file:line` de las reglas A y notas (10 muestreadas) | **FALSO** · MEDIA | **4 de 10 drifteadas**: `process_viirs_mod.py:409` (A89, docstring de los 5 opt-in) ahora está en la **416**; `process_viirs.py:958` (A69, `compute_test1_nti`) está en la **206**/**1070**; `process_modis.py:674` y `process_viirs_mod.py:665` (imports de `compute_test1_mir`) están en la **59** y la **153**; `frontend/index.html:680` (A10, `pc.vrp_mw`) es hoy una fila de la lista de volcanes. Las 6 restantes apuntan bien, incluidas las que S127 corrigió (A6 `run_pipeline.py:234/277/324`, A89 `:244`, `geo_utils.py:29`, `index.html:1372`) | **dejar de citar números de línea en las reglas.** Citar el símbolo (`get_detection_anchor`, `compute_test1_nti`, `isValidDetection`) es estable, greppeable y no envejece. Donde el número sea imprescindible, cubrirlo con el guard G8, que es el contrato que S127 dejó a medias: arregló A6 y no puso el test que impide que vuelva a driftear — y drifteó otra vez, en otras cuatro |

### 4 · `README.md` (cara pública del repo)

| # | afirmación | estado | evidencia | fix propuesto |
|---|---|---|---|---|
| R1 | «Detection anchored to the physical crater (`vent_lat/lon`), while **the 50×50 km grid uses the official MIROVA grid center** — these are decoupled on purpose» | **FALSO** · ALTA | `get_grid_center()` (`geo_utils.py:29`) no tiene ningún llamador en producción (verificado en AUDIT_S127 Hallazgo 7) y `ENABLE_UTM_REGRID=False`. Es la consecuencia que D17 declara NO implementada | «**Detection anchored to the physical crater** (`vent_lat/lon`). The ROI is currently built around the configured volcano coordinates, **not** around the official MIROVA grid center — see divergence D17 in `docs/MIROVA_DIVERGENCES.md`. `get_grid_center()` exists but is not wired into the production path.» |
| R2 | Feature list: «**TIR VRP** (VIIRS I05, 11.45 µm): Stefan-Boltzmann (Aveni et al. 2024, TIRVolcH)» | **FALSO** · ALTA | `ENABLE_VRP_TIR_OUTPUT=False` y `ENABLE_VRPTIR_AVENI=False`: **24.290 de 24.318** records con el campo valen 0. Los 28 con valor son residuo de abril-2026 (máx **4.817 MW**, exactamente la clase de outlier que motivó apagarlo). `detect_tirvolch.py` sigue sin importarlo nadie | mover la línea de «Features» a una sección «Implemented but disabled» con el texto: «**TIR VRP** (VIIRS I05, Stefan-Boltzmann, Aveni et al. 2024) — implemented, currently silenced (`enable_vrp_tir_output: false`) pending the full Coppola 2024 Eq.16 fix; the field is emitted as 0.» |
| R3 | «34 additional volcanoes are configured under the `experimental` profile (outside the operational dashboard)» | **FALSO** · MEDIA | los 34 tienen records dentro de `data/mirova_equivalent/`, el subdirectorio operacional (67-94 cada uno) | «34 additional volcanoes are configured but outside the NRT cron; they carry a short April-2026 backfill window in `data/mirova_equivalent/` and are not part of the operational dashboard selection.» |
| R4 | «Dashboard (frontend — **3 standalone views**)» | **OBSOLETO** · BAJA | son 4 desplegadas; `comparacion.html` se rotula «PREVIEW S115». CLAUDE.md se corrigió en S127, el README no | «Dashboard (frontend — 3 live views + 1 preview)» y agregar la fila de `comparacion.html` marcándola como preview |
| R5 | «Nadir-fixed pixel area … no sec³ off-nadir scaling» | CONFIRMADO | ambos flags nadir-fijo en `True` | — |
| R6 | «Night-time only MIR processing (barrier at fetch, process and store stages)» | CONFIRMADO | `run_pipeline.py:170` default `True`, `_check_night` en las tres ramas (l. 227, 270, 317) | — |
| R7 | Coeficientes Wooster 18,9 / 19,7 / 18,0 con error ≤0,17 % contra OSF v2.5 | CONFIRMADO (los coeficientes) | los tres valores coinciden con el código | el «≤0,17 %» no tiene instrumento hoy — ver §7 |

### 5 · `docs/MIROVA_DIVERGENCES.md`

| # | afirmación | estado | evidencia | fix propuesto |
|---|---|---|---|---|
| D-a | **D2**: «Cobertura estimada: ~70 % para VIIRS» + «Pendiente: re-scrapear con script Mirova-v1» | **OBSOLETO** · MEDIA | S128 la midió en **79,2 %** y el loader CONS ∪ OCR de S86 la mitigó de facto. La sección no tiene ninguna nota posterior al 2026-04-29. El propio CLAUDE.md ya avisa que «el doc nunca se actualizó» — o sea el error está identificado desde hace sesiones y sin corregir | agregar al encabezado de D2: «> **Actualización S128/S131.** La cobertura medida es **79,2 %**, no ~70 %, y el loader canónico CONS ∪ OCR (S86) ya la mitiga de facto: las métricas del dashboard no la sufren. D2 queda **abierta como sesgo residual conocido**, sin acción pendiente de re-scrapeo. El número se recomputa con el instrumento del libro de cuentas.» |
| D-b | **D3**: conteos de categorías MIROVA (13.378 RUTINA, 407 Muy Bajo, 165 Bajo, 253 FP; 234 FPs en 10 Tier A, 24 propios) | **SIN RESPALDO** · MEDIA | la sección no nombra ningún script que los recompute y no hay entrada de D3 en `scripts/libro_de_cuentas.py`. Son conteos absolutos sobre un corpus vivo (A90): el CSV creció y los porcentajes ya no se comparan contra nada | no borrar: **rebajar**. Agregar «> **S131**: estos conteos son del 2026-04-29 y no tienen instrumento que los recompute. Se conservan como fotografía de esa fecha; **no usar como línea base** sin volver a medirlos con la ventana declarada (A90).» Y agregar la fila `D3_fp_mirova` al libro de cuentas |
| D-c | **D18**, encabezado: «**ABIERTA (medida, sin A/B)** S129» | **OBSOLETO** · BAJA | el A/B se corrió en S130 y su veredicto (NO ADOPTAR) está en el cuerpo de la misma sección, l. 2018-2043, citando `docs/s130/VEREDICTO_AB_D18.md` | cambiar el encabezado a «**ABIERTA (A/B corrido S130 → NO ADOPTAR; divergencia de fidelidad literal, prioridad baja)**» |
| D-d | **D12**, nota S105: «Siguen ON en `mirova_equivalent.yaml`» (gates intra-radio) | CONFIRMADO (con reserva) · BAJA | la frase sigue ahí y el flag efectivo es `False`, pero la propia sección trae abajo el bloque «✅ RESUELTO S118 (flip OFF)». Riesgo de lectura parcial, no afirmación sin corregir | tachar la frase in situ (`~~Siguen ON~~ → OFF desde S118`) en vez de dejar que dependa de leer 30 líneas más abajo. Es el hallazgo que el protocolo cuenta **redescubierto 3 veces** |

### 6 · Docstrings y comentarios de `pipeline/`

Se muestrearon los ~30 comentarios y docstrings con afirmación numérica o de estado (umbrales,
áreas, coeficientes, flags). El barrido usó las ocho clases de afirmación de T9
(«no-op», «idéntico», «siempre», «sólo afecta a X», «en producción»…).

| # | afirmación | estado | evidencia | fix propuesto |
|---|---|---|---|---|
| P1 | `scan_geometry.py:1-28`, docstring del módulo: «*Without correction, VRP values use the nadir pixel area and **underestimate** radiative power at off-nadir pixels*» + «For MODIS at the scan edge the correction is ~13×» | **OBSOLETO** · MEDIA | los dos flags nadir-fijo están **ON** (A66/A67): la rama sec³ no se ejecuta en producción en ningún sensor. El aviso correcto existe recién en la l. 232, dentro de un bloque agregado en S122 | mover el aviso al principio del docstring: «**Nota operacional:** el pipeline usa área de píxel **nadir-fija** en los tres sensores (`ENABLE_NADIR_FIXED_PIXEL_AREA_*`, A66/A67), replicando el resampleo de MIROVA a grilla de área constante. La corrección sec³ que documenta este módulo **no se ejecuta en producción**; se conserva para el modo histórico y los A/B.» |
| P2 | `scan_geometry.py`, docstring de `roi_mask_bbox`: «MIROVA publica detecciones en esas esquinas … **Cambiar a bbox recupera esas refs**» | **OBSOLETO** · MEDIA | `ENABLE_ROI1_BOX_PAPER=False` y `ROI1_BOX_HALF_KM=2.5` km — o sea la caja 5×5 del ROI1 (D18), no el bbox 50×50 que el docstring propone. El A/B de D18 (S130) dio **NO ADOPTAR** | quitar la recomendación («Cambiar a bbox recupera esas refs») y dejar la descripción geométrica. Agregar: «Uso actual: el flag `enable_roi1_box_paper` (OFF) aplica esta función con `half_km = ROI1_BOX_HALF_KM = 2,5` para la caja 5×5 del ROI1 (D18), no para el bbox 50×50 de la ROI completa.» |
| P3 | `process_viirs.py:1797-1799`: «`valid_mask = cloud_free` … igualar el criterio del fondo global (**excluye nubes I05<260K**) para no inflar la magnitud con topes de nube fríos» | **OBSOLETO** · MEDIA | `CLOUD_MASK_BT_K = 0.0`, así que `cloud_free = I05 >= 0.0` es una máscara **todo-True** y no excluye nada. Importa porque el anillo intermedio es justo el mecanismo que la FICHA describe como recuperación de focos sub-píxel | «`valid_mask = cloud_free`: mantiene el mismo criterio que el fondo global. Desde S126 la máscara de nube está apagada (`cloud_mask_bt_k: 0.0`), así que hoy `cloud_free` no excluye nada; el parámetro se conserva para que ambos fondos sigan acoplados si la máscara se reactiva.» |
| P4 | `process_modis.py:314-315`, `_select_thresholds`: «con `enable_day=False` el comportamiento es idéntico al histórico (siempre noche) → no toca operacional» | CONFIRMADO | `ENABLE_DAYTIME_MODIS=False` | — |
| P5 | `store.py:72-103`, docstring de `_apply_vrp_floor`: «APAGADO en el perfil operacional desde S130 (los tres pisos valen 0)» | CONFIRMADO | los tres pisos valen `0.0`. **Es el ejemplo de cómo se hace bien**: el docstring nombra el flag, la sesión y la medición (582 de 57.730) | — |
| P6 | Cabeceras FICHA «Datos entrada» de los 16 módulos | 15 CONFIRMADAS / 1 FALSA | sólo `vrp_regimes.py:10` dice MOD14/MYD14; los 15 restantes describen bien su entrada | ver F10 |

### 7 · Cadencia, salidas publicadas y mapa del workspace

`docs/INDEX.md`, `README.md` y `MAPA_WORKSPACE.md` contra los 18 workflows efectivos.

**Los 6 workflows con cron activo hoy** (los otros 12 son `workflow_dispatch` o `push`):

| workflow | cron | qué produce |
|---|---|---|
| `nrt.yml` | `0 */2 * * *` (cada 2 h) | records de los 11 Tier A → `data/mirova_equivalent/` |
| `sync-mirova-csv.yml` | `12 * * * *` (cada hora) | CSV de referencia MIROVA |
| `pages-deploy.yml` | `50 */2 * * *` + push a `frontend/**` | dashboard |
| `reproc-watchdog.yml` | `20 * * * *` | vigilancia de reprocesos |
| `nrt-retry.yml` | `30 1-23/2 * * *` | re-dispara `nrt.yml` (no pushea) |
| `nrt-monitor.yml` | `30 */6 * * *` · `nrt-healthcheck.yml` `0 12 * * *` | alertas de frescura |
| `audit-weekly.yml` | `0 9 * * 1` (lunes) | `data/audit_continuous/` |

Coinciden con lo documentado en `README.md` («cron every 2 hours») y `CLAUDE.md`.

| # | afirmación | estado | evidencia | fix propuesto |
|---|---|---|---|---|
| I1 | `docs/INDEX.md`: **AUDIT_S127.md** marcada como «**Última**» | **OBSOLETO** · MEDIA | existen auditorías hasta S131; `AUDIT_S128.md` no figura en el índice. Es la **4.ª vez** que se redescubre «INDEX congelado» (Fuga 1 del protocolo) — y el propio índice trae el aviso «⚠️ No hardcodear cuál es la vigente acá» | borrar la marca «Última» de la fila de S127 y dejar sólo el aviso con el comando. Cerrar con el guard G6, que es la única forma de que no vuelva por quinta vez |
| W1 | `MAPA_WORKSPACE.md`, grafo de dependencias (l. 70-71): «VRP Chile 🔴 **CAÍDO**» | **FALSO** · MEDIA | el mismo documento declara en la l. 18 «🟢 **RECUPERADO** (verificado 2026-08-09)». El grafo ASCII no se actualizó: contradicción interna dentro del doc. Además la ficha es del 2026-08-09 y hoy es 2026-09-02 (A86) | cambiar el nodo del grafo a «VRP Chile 🟢» y re-verificar la frescura contra el remote antes de citar el mapa |
| W2 | `MAPA_WORKSPACE.md` l. 21: «Latente en VRP-chile (**5 de 6 sin grupo de concurrency**)» | **FALSO** · MEDIA | 9 workflows pushean; 5 tienen `push-main` y los 4 restantes tienen grupo propio **con** retry ×5. **Ninguno queda sin grupo y sin retry** — el guard G4 pasa hoy | «VRP-chile: los 9 workflows que pushean a main tienen grupo `push-main` o retry propio; la carrera está cubierta (verificado S131).» |
| L1 | `scripts/libro_de_cuentas.py` — cobertura del instrumento | **SIN RESPALDO** · MEDIA | 13 afirmaciones con instrumento: **11 OK**, **2 con deriva** (`git_mb` 6.507,8 → 6.930,6; `data_mb` 1.034,7 → 1.100,8, ambas de AUDIT_S128 §5). El propio script reporta **415 números SIN instrumento** en el repo. **Ninguna de las 16 afirmaciones falsas de esta auditoría tenía instrumento** — y la única que sí lo tenía (A12) llevaba tres sesiones marcada como deriva sin que nadie corrigiera la regla | el libro funciona; lo que falta es **cerrar el lazo**: que una fila en deriva abra tarea, no que se lea y siga. Y agregar las filas que esta auditoría deja medibles: `pisos_vrp_efectivos`, `cloud_mask_bt_k`, `n_workflows_push_main`, `A12_dT_*` ya está |

---

## Guards propuestos (regla B: nada pasa a CONFIRMADO/FALSO/OBSOLETO sin test que lo mida)

Están escritos y **corriendo hoy** en
`experiments/_s131_audit/declarado_vs_efectivo/02_guards_propuestos.py`. La sesión que aplique
los fixes los mueve a `tests/test_guard_declarado_vs_efectivo_s131.py` sin reescribirlos.
Estado actual: **5 de 8 fallan**, que es lo que se espera antes de aplicar los fixes.

| guard | qué impide | cierra | hoy |
|---|---|---|---|
| **G1** | que un documento publicable o una cabecera FICHA nombre un producto NASA que `fetch.py` no descarga. Deriva la lista de `short_name` del código, no de una constante | F1, F10 | **falla** (4 ocurrencias) |
| **G2** | que la FICHA declare una mitigación de sesgo cuyo flag está apagado. Mapea frase → flag y consulta `pipeline.profile`, nunca el YAML | F2, F3 | **falla** (2) |
| **G3** | que un record publicado lleve `diag_vrp_floor_mw` con `vrp_mw > 0`. Es el invariante que `store.py:99-103` garantiza al escribir y que un reproceso parcial rompe | el hallazgo #4 | **falla** (1.635/1.635) |
| **G4** | que un workflow pushee a main sin `push-main` **ni** retry propio. Mide la condición, no la lista de nombres — por eso no envejece | C4, C5, W2 | pasa |
| **G5** | `"on":` sin comillas (A43) | C6 | pasa |
| **G6** | que `docs/INDEX.md` no nombre la auditoría más reciente del directorio | I1 | **falla** |
| **G7** | que un campo del schema traiga valor > 0 mientras su flag productor está OFF (instancia: `vrp_tir_mw`) | R2 | **falla** (28) |
| **G8** | que una cita `file:line` de CLAUDE.md deje de apuntar al símbolo que nombra. Tabla explícita a propósito: es el contrato, no una heurística | C13 | pasa (las 4 que S127 corrigió) |

**El principio de diseño, que vale más que los guards**: cuatro de ellos (G1, G2, G4, G6)
**derivan la verdad del código** en vez de fijar una lista esperada. Es la lección de S127
—corregir una lista la deja envejecer de nuevo— aplicada a cuatro clases más. Los otros cuatro
sí fijan un valor porque son invariantes, no inventarios.

**Y una advertencia sobre G8**: S127 corrigió el ejemplo drifteado de A6 y **no puso el test que
impide que vuelva a driftear**. Cuatro sesiones después hay otras cuatro citas drifteadas. La
corrección sin guard tiene vida media de pocas sesiones — es la Fuga 1 medida en vivo.

## Pendientes declarados (regla C)

Lo que esta auditoría **no** verificó, para que la siguiente empiece por acá:

1. El «error ≤0,17 % contra OSF v2.5» de los coeficientes Wooster (CLAUDE.md y README) no tiene
   instrumento: el archivo OSF no está en el repo y no hay script que lo recompute. **SIN RESPALDO**
   no auditado — no se clasificó porque no se pudo medir.
2. Los 28 records con `vrp_tir_mw > 0` de abril-2026: no se determinó si son residuo de un perfil
   experimental mezclado o de una ventana con el flag encendido. G7 los detecta; el origen queda abierto.
3. Los 34 volcanes no-Tier-A con ventana de abril-2026 dentro de `data/mirova_equivalent/`: no se
   verificó si el frontend los muestra. Si los muestra, el hallazgo C3/R3 sube de MEDIA a ALTA.
4. Los ~415 números sin instrumento que reporta el libro de cuentas: se muestrearon los de las
   cinco fuentes del encargo, no el total.

## La regla que deja

> Una lista copiada envejece; una condición derivada del código, no. Cuando un documento
> tenga que afirmar algo sobre el estado del sistema, la forma correcta es **nombrar el
> instrumento que lo mide**, no escribir el valor.

Y su corolario, que es de S127 y esta sesión vuelve a confirmar: **corregir el texto sin dejar
el guard es aplazar el mismo hallazgo, no cerrarlo.**
