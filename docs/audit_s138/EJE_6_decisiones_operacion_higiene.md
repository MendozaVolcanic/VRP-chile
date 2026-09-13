# Auditoría S138, eje 6: decisiones, operación e higiene

**Fecha del servidor (header `Date` de `gh api`)**: 2026-09-13 11:49 UTC. Todos los "hace N horas" de este informe se miden contra esa hora, no contra la memoria de la sesión (A86).
**Estado del repo al auditar**: checkout local en `6b1dd91ef` (main); `origin/main` un commit más adelante (`f47edb0cb`, "sync CSV + regenerate per-volcano JSONs", automático). Toda lectura de datos se hizo sobre `origin/main` con `git show origin/main:<ruta>` o por API, nunca sobre el checkout (regla 5 del mapa del workspace).
**Scripts de medición**: `experiments/_s138_audit/eje6/` (`cadencia_nrt.py`, `zombies.py`, `frontend_vs_datos.py`, `clasificar_ramas.py`, `clasificar_ramas_v2.py`, con sus JSON de entrada). Cada uno lleva en su docstring las dos preguntas del instrumento, el control positivo, la ventana y el denominador.
**Modo**: read-only. No se editó, commiteó, borró ni disparó nada.

---

## 1. Tabla única de decisiones (S134 §D, S135, S136, S137, S138) con estado real hoy

Fuentes leídas: `docs/AUDIT_S134.md` §D (l. 422-433), `tasks/BLOQUE_ARRANQUE_S135.md` (l. 74-80), `tasks/BLOQUE_ARRANQUE_S136.md` §1 (l. 52-61) y "Decisiones que siguen esperando" (l. 335-352), `tasks/BLOQUE_ARRANQUE_S137.md` §b (l. 30-39), `tasks/BLOQUE_ARRANQUE_S138.md` §b (l. 28-41). El estado se verificó contra el código, los perfiles cargados con `pipeline.profile` (perfil `mirova_equivalent`), `experiments/`, `docs/` y `gh pr list --state merged` de hoy, no contra el traspaso siguiente.

Convención de estado: **EJECUTADA** (hay PR/commit/experimento verificado), **SUPERADA** (otra decisión la reformuló o la dejó sin objeto; se cita), **ABIERTA** (espera al dueño o no tiene rastro de ejecución).

| id | origen | pregunta (resumida) | opciones | recomendación de entonces | ESTADO HOY | evidencia verificada en esta sesión |
|---|---|---|---|---|---|---|
| S134-D1 | AUDIT_S134 §D | `keep_peak` publica un píxel del borde del disco como summit con 0,03-0,17 MW en los 11 Tier A | (a) documentar; (b) probe A75 en CI; (c) A/B keep_peak OFF/ON estratificado | (b) y luego (c) | **EJECUTADA en (b) y (c); la ADOPCIÓN sigue ABIERTA (ver S138-4)** | (b) PR #598/#599 "probe A75 por etapa VIIRS375 para D19", `experiments/_s135_probe_etapas/`. (c) PR #605 "A/B de 5 brazos sobre 6 volcanes", `experiments/_s135_ab_d1d2/`, `.github/workflows/reproc-s135-ab-d1d2.yml`; S138 §e.1: "dos chunks verdes, 260 noches, ningún brazo cumple". No existe flag `ENABLE_KEEP_PEAK` (`pipeline.profile` lo confirma: `<<NO EXISTE>>`); el A/B corrió por brazos del workflow |
| S134-D2 | AUDIT_S134 §D | second pass sin conjunto activo (2.295/3.164 records) | (a) condicionar a `n_first_pass > 0` y vecindad 8; (b) reponer compuerta BT; (c) dejar | (a) con A/B | **EJECUTADA en implementación y A/B; ADOPCIÓN ABIERTA** | `ENABLE_SECOND_PASS_CONDITIONED = False` en producción (medido hoy con `VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile"`), PR #605 (17 tests). Mismo A/B que D1 |
| S134-D3 | AUDIT_S134 §D | flip `ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER` | (a) no encender; (b) re-correr A/B con C2' en unidades de `inner_radius`; (c) encender | (b) | **ABIERTA** | Flag `False` hoy (medido). `docs/s133/C2_NORMALIZADO_INNER_RADIUS.md` es el diagnóstico retrospectivo de S133 sobre el A/B de S132 (l. 8-11: "los 9.218 records MODIS del flip far→summit del A/B de S132"); no hay experimento posterior a S133 que use C2' (`grep -rl "C2'" experiments/_s134* .. _s138*` sólo devuelve binarios PNG/TIF). El A/B con C2' **no corrió** |
| S134-D4 | AUDIT_S134 §D | coordenada del cráter de Isluga (único Tier A con `vent_*` a 2 decimales) | (a) refinar con imagen/DEM; (b) dejar | (a) | **SUPERADA en su forma (a); reformulada como S138-5, ABIERTA** | `volcanoes.yaml:662-682`: `lat: -19.15`, `lon: -68.83`, `vent_lat: -19.15`, `vent_lon: -68.83` (sin cambio); `mirova_center_lat/lon: -19.15212/-68.83269`. S138 §b.5: refinar con DEM "sería divergir del paper"; propone usar el `mirova_center` dentro de D17 |
| S134-D5 | AUDIT_S134 §D | corroboración MIROVA por volcán en el dashboard | (a) indicador 90 d; (b) nada | (a) | **EJECUTADA** | PR #628 (2026-09-12). `frontend/index.html:1999` `corroboracionMirova(d, dias)` lee `d.mirovaRecords`, que `loadVolcano` (l. 975-977) carga de `data/mirova/<V>.json`. Ese archivo lo regenera `sync-mirova-csv.yml:79-119` desde `latest_consolidado.csv`; último commit remoto `f47edb0cb` 2026-09-13 11:49 UTC. Llaima: 1 record (2026-05-15) → "0 alertas en 90 d" es coherente con el dato. Sólo está en `index.html` (`diario`/`mosaico`: 0 ocurrencias de "corrobor"); es un indicador de tarjeta, no un filtro, así que S92 L5 no lo exige en las tres |
| S134-D6 | AUDIT_S134 §D | ley de área intermedia f(θ) por píxel | (a) A/B en S135 por píxel en `resolve_viirs_pixel_areas`; (b) archivar | (a), después de D1/D2 | **ABIERTA (ya sin bloqueo: D1/D2 corrieron)** | `grep -rln "resolve_viirs_pixel_areas\|ley de área\|f(θ)" experiments/_s135* _s136 _s137` → 0 archivos. No corrió |
| S134-D7 | AUDIT_S134 §D | marcador "extensión" para PCC (no-op medido 0/5.340) | (a) ajustar `volcanic_features.yaml`; (b) quitarlo; (c) dejar | sin recomendación técnica (pregunta volcanológica) | **ABIERTA** | `pipeline/volcanic_features.yaml:31-44` sin cambios; último commit que lo tocó: 2026-05-30 (#249) |
| S134-D8 | AUDIT_S134 §D | re-correr B22 con ventana ancha (Isluga 66 / Láscar 62) | (a) sí; (b) archivar hasta D1 | (b) | **SUPERADA por S137-2 (reformulada como A/B de magnitud), ABIERTA** | `ENABLE_MODIS_B22_PRIMARY = False` (medido). S137 corrió B22 sobre las 9 escenas del Apéndice A (PR #630-#636), no sobre Isluga/Láscar con ventana ancha |
| S136-1 | BLOQUE S136 §1 | ¿adoptar el brazo B pese a fallar la paridad por dos centésimas? | (a) adoptar; (b) no adoptar y perseguir Test 1 | (b) | **SUPERADA: es la misma pregunta que S138-4** | S138 §b.4 la repite con las mismas opciones y recomendación. Ningún flag cambió (ver D2) |
| S136-2 | BLOQUE S136 §1 | ¿investigar que el Test 1 integrado no deba intersectarse con la máscara contextual? | (a) sí con MISSION y A/B propio; (b) archivar | (a) | **EJECUTADA (probe); veredicto formalmente indeterminado** | PR #609 "gate MISSION + probe de 3 brazos sobre la intersección contextual del Test 1", #611-#613. S137 §e.5 lo da por cerrado ("sigue curando"), pero S137 §d SOSPECHA dice "n insuficiente (3 contra el umbral de 4), formalmente sigue indeterminado". Las dos frases conviven en el mismo archivo (l. 121-123 y l. 141) |
| S136-3 | BLOQUE S136 §1 | ¿re-enunciar D19 con el matiz de Copahue y el denominador que se mueve? | (a) reescribirla; (b) dejarla | (a) | **ABIERTA** | `docs/MIROVA_DIVERGENCES.md:2058-2143` (cuerpo de D19): 0 menciones a S136, S137, "Copahue" o "re-enunci". El encabezado (l. 2058) quedó en S135 |
| S136-4 | BLOQUE S136 §1 | notas al editor de §4 y §5 del paper esperan lectura de Nicolás | (a) ahora; (b) después | (a) | **ABIERTA (no verificable en el repo: es una lectura)** | `docs/paper/` tiene `sec4_background.md`, `sec5_methods.md`, `sec6_validation.md`; 7 líneas con "editor". Nada en el repo marca que se hayan leído |
| S136-5 | BLOQUE S136 §1 | ¿automatizar el reintento de jobs del A/B con cobertura corta? | (a) automatizar; (b) verificar a mano | (b) | **SUPERADA** | El A/B terminó con cobertura completa (S136 §4: "brazo B no pierde ninguna noche, 203 pasadas"; S138 §e.1: "dos chunks verdes"). `reproc-s135-ab-d1d2.yml`: 0 líneas con retry/reintent/attempt, coherente con (b) |
| S136-6 | BLOQUE S136 (l. 352) | qué es el objeto a 2,97 km E del cráter de Villarrica (08-31, +8 K, dNTI positivo) | (sin opciones) | (sin recomendación) | **ABIERTA** | "2,97 km" aparece sólo en `docs/AUDIT_S134.md`, `docs/MIROVA_DIVERGENCES.md`, `docs/PREREGISTRO_AB_D1_D2_S135.md` y `experiments/_s134_audit/f3/`; nada en `_s136`/`_s137` |
| S137-1 | BLOQUE S137 §b | el "Test 1 integrado" no está en el paper: ¿declararlo como divergencia en el artículo? | (a) declararlo; (b) corregirlo antes | (a) | **ABIERTA** | `grep -rn -i "test 1 integrado\|integrated test 1" docs/paper/*.md` → 0 |
| S137-2 | BLOQUE S137 §b | ¿re-evaluar el A/B de B22 con criterio de magnitud? | (a) sí, sin apuro; (b) cerrado | (a) | **ABIERTA** (absorbe D8) | `docs/s133/AB_B22_VEREDICTO.md` sigue en NO ADOPTAR; sin A/B de magnitud posterior |
| S137-3 | BLOQUE S137 §b | cerrar D12 formalmente | (a) cerrar; (b) dejar | (a) | **ABIERTA** | `docs/MIROVA_DIVERGENCES.md:1399`: "D12 ... SECCIÓN CONGELADA EN S106/S108; leer primero la nota S125". Sin cierre |
| S137-4 | BLOQUE S137 §b | perseguir las tres opciones de por qué el piso 0,003 no sobre-detecta en MIROVA | (a) perseguirlas, paper primero; (b) parar | (a) | **PARCIALMENTE EJECUTADA, ABIERTA en la opción (2)** | Opción (3) remuestreo: medida, S138 §e.2 ("sube sigma"). Opción (1) escala del dNTI: medida en las figuras del paper, S138 §a (sigma ~0,0008). Opción (2) filtros sobre los candidatos: sin rastro en `_s137` ni en S138 §a/§d |
| S137-5 | BLOQUE S137 §b | guiones largos en el resto del repo | (a) barrido completo; (b) sólo lo nuevo | (b) | **ABIERTA por defecto (b), sin acto** | Conteo hoy: `pipeline/detection_context.py` 37, `pipeline/profile.py` 70 (S137 decía 71) |
| S138-1 | BLOQUE S138 §b | implementar como flags OFF en `pipeline/` la compuerta fuera de los Tests 2/3 y el fondo local uniforme (A45) | (a) sí; (b) no | (a), después de S138 | **ABIERTA** | No hay flag para la compuerta (`grep "t_bg + 3\|compuerta" pipeline/process_modis.py pipeline/detection_context.py` → sólo un comentario, l. 871). `ENABLE_TEST1_LOCAL_BG_NTI` existe pero es de S105 (`profile.py:284-288`, "fondo LOCAL sobre NTI en el Test1 ... sólo junto a `enable_test1_nti_integral`"), no el fondo local uniforme de S137 |
| S138-2 | BLOQUE S138 §b | qué conectiva lleva el A/B | (a) prosa `max`; (b) fórmula `min`; (c) ambas | (c) | **ABIERTA** | El brazo de la prosa ya tiene flag: `ENABLE_TESTS_23_PROSE_BRANCH = False` (`profile.py:647-649`, PR #621) |
| S138-3 | BLOQUE S138 §b | corregir la evaluación de A2 con la posición de la figura (9,6 km) | (a) desde la próxima serie; (b) no | (a) tras medir las 9 figuras | **ABIERTA** | Sin PR posterior a #637 |
| S138-4 | BLOQUE S138 §b | adopción del A/B de keep_peak (ningún brazo cumple) | (a) adoptar B; (b) no adoptar, mover al Test 1; (c) dejar | (b) | **ABIERTA** (es D1/D2 adopción y S136-1) | Flags OFF, ver D2 |
| S138-5 | BLOQUE S138 §b | D4 reformulada: usar `mirova_center` como ancla de Isluga dentro de D17 | (a) sí; (b) dejar | (a) | **ABIERTA** | `volcanoes.yaml:669-670` tiene el `mirova_center`; `get_grid_center()` "no la llama nadie en producción" (S138 §d, no re-verificado aquí: SOSPECHA heredada) |
| S138-6 | BLOQUE S138 §b | ¿lanzar la auditoría S138 antes de tocar nada? | (a) sí; (b) primero el A/B | (a) | **EJECUTADA** | `docs/PLAN_AUDITORIA_S138.md` existe (11.273 bytes); este informe es el eje 6. Ningún PR sobre `pipeline/` desde #637 (`gh pr list --state merged` de hoy: el último es #637) |

**Conteo (denominador: 25 entradas de decisión en las cinco fuentes; ventana: S134 a S138, 2026-09-05 a 2026-09-13)**: **EJECUTADAS 5** (D1 y D2 en su parte experimental, D5, S136-2, S138-6) · **SUPERADAS 4** (D4, D8, S136-1, S136-5) · **ABIERTAS 16** (D3, D6, D7, S136-3, S136-4, S136-6, S137-1 a S137-5, S138-1 a S138-5), donde S137-4 está parcialmente ejecutada. Tres de las abiertas son la misma pregunta escrita tres veces (D1/D2 adopción = S136-1 = S138-4), y dos más son reformulaciones (D4→S138-5, D8→S137-2): **de 16 abiertas, 12 son distintas**.

**Lo que esto dice del proceso**: el error de S137 (recomendar un A/B ya corrido) no fue un descuido puntual. La misma decisión vive en tres bloques con tres números distintos, y el bloque que la reformula no marca la anterior como superada. Este cuadro es la primera vez que las 25 están juntas con estado; conviene que el próximo bloque de arranque lo herede como única tabla y que cada reformulación borre o marque la anterior.

---

## 2. Operación

### 2.1 Cadencia del cron NRT (`nrt.yml`, cron `0 */2 * * *`, 12 corridas esperadas por día)

Script: `experiments/_s138_audit/eje6/cadencia_nrt.py` sobre `nrt_runs.json` (`gh run list --workflow=nrt.yml --limit 200`, 200 runs entre 2026-08-17 10:30 y 2026-09-13 08:57 UTC; 198 `schedule`, 2 `workflow_dispatch`, todos en `main`).

**Ventana 14 días (2026-08-30 11:49 → 2026-09-13 11:49 UTC)**: **73 corridas programadas de 168 esperadas (43 %)**, **73 verdes, 0 rojas**. Huecos mayores a 4 h entre corridas consecutivas: **49**; el hueco típico es de **4,7 a 5,9 h** (el cron de 2 h llega cada ~5 h). Máximo: 8,2 h (2026-08-31 10:33 → 18:47). Último run programado a las 08:57 UTC, 2,9 h antes de la hora del servidor.

| día | corridas | verdes | rojas |
|---|---|---|---|
| 08-30 (parcial) | 3 | 3 | 0 |
| 08-31 | 4 | 4 | 0 |
| 09-01 a 09-04 | 5 c/u | 5 | 0 |
| 09-05 | 7 | 7 | 0 |
| 09-06 | 6 | 6 | 0 |
| 09-07 a 09-11 | 5 c/u | 5 | 0 |
| 09-12 | 6 | 6 | 0 |
| 09-13 (hasta 11:49) | 2 | 2 | 0 |

Promedio sobre los 198 runs programados descargados (27 días): **7,35 corridas por día** (esperado 12).

**Comparación con S133**: `docs/s133/CADENCIA_DEL_CRON.md:32-40` midió 11,8 corridas/día antes (23-26 ago) y **4,8 después** (30 ago a 3 sep), "entrega 98 % → 40 %", y lo atribuyó a GitHub (afecta por igual a los cuatro workflows con cron). **Hoy: 5,2/día, 43 %. La degradación no se recuperó en los diez días siguientes; es el régimen vigente.** Se confirma también la segunda mitad del diagnóstico de S133: **no se pierden records**, porque cada corrida procesa el día entero (ver 2.2: 102 a 136 records/día en los 11 Tier A, los 11 con datos los 14 días). Lo que se degrada es la latencia: una pasada nocturna espera hasta ~5 h por el siguiente cron.

Los otros crons muestran lo mismo: `sync-mirova-csv` (cron horario) 60 corridas entre 2026-09-03 21:41 y 2026-09-13 11:48 = **6,3/día de 24 (26 %)**, 60/60 verdes (S133 midió 22 %). `nrt-healthcheck` (cron 12:00 UTC) arrancó entre las **14:08 y las 16:47 UTC** en sus últimas 10 corridas (2 a 4,8 h tarde). `pages-deploy` (cron `:50 */2`): 15 corridas programadas entre sus últimas 30 (el resto `workflow_run` disparadas por el NRT, la última 2026-09-13 10:17).

**Instrumento**: pregunta 1, un cron muerto daría 0 corridas/día y se vería. Pregunta 2, si `gh` fallara el JSON no existiría (se declara N=200). Control positivo: `nrt-retry` (cron cada 2 h a :30) da 30/30 verdes con la misma cadencia degradada, es decir el conteo ve corridas cuando las hay.

### 2.2 Detector de zombies por volcán

Script: `experiments/_s138_audit/eje6/zombies.py`. Campo de fecha del record verificado leyendo uno: `datetime_utc` ("2026-09-13 07:00", hora de adquisición) y `processed_utc` (ISO, hora de proceso). El JSON tiene raíz `{volcano, updated, records}`. Lectura desde `origin/main`; último commit remoto por archivo con `gh api "repos/.../commits?path=data/mirova_equivalent/<V>.json&per_page=1"`. Último verde por volcán: `gh run view <run> --json jobs` sobre los 3 últimos runs programados (34748715101 08:57, 34735193402 03:19, 34726222628 23:45 del 12): **33/33 jobs `success`**.

| volcán | N records | último `datetime_utc` | último `processed_utc` | h desde proceso (a 11:49) | records 14 d | días con record /14 | último commit remoto |
|---|---|---|---|---|---|---|---|
| Lastarria | 4.727 | 09-13 06:36 | 09-13 09:16 | 2,5 | 139 | 14 | 09-13 09:33 `e4b20aed9` |
| Lascar | 4.669 | 09-13 06:36 | 09-13 09:19 | 2,5 | 134 | 14 | 09-13 09:39 `9b54ce0a9` |
| Isluga | 4.550 | 09-13 06:30 | 09-13 09:15 | 2,6 | 130 | 14 | 09-13 09:31 `0bd553378` |
| NevadosDeChillan | 5.511 | 09-13 06:36 | 09-13 09:48 | 2,0 | 158 | 14 | 09-13 10:03 `fa3792ce4` |
| Llaima | 5.700 | 09-13 07:00 | 09-13 09:55 | 1,9 | 157 | 14 | 09-13 10:17 `52ef5c335` |
| Villarrica | 6.545 | 09-13 07:00 | 09-13 09:22 | 2,4 | 158 | 14 | 09-13 09:45 `30c98f0a5` |
| Chaiten | 6.022 | 09-13 07:00 | 09-13 09:19 | 2,5 | 167 | 14 | 09-13 09:39 `aee14b049` |
| **PlanchonPeteroa** | 5.303 | **09-12 08:00** | **09-12 20:29** | **15,3** | 141 | **13** | **09-12 20:43** `c7ba1002e` |
| Tupungatito | 5.263 | 09-13 06:36 | 09-13 09:18 | 2,5 | 149 | 14 | 09-13 09:37 `e0c8a5f38` |
| Copahue | 5.567 | 09-13 06:36 | 09-13 09:58 | 1,8 | 151 | 14 | 09-13 10:16 `144ecbc63` |
| PuyehueCordonCaulle | 5.437 | 09-13 07:00 | 09-13 09:21 | 2,5 | 169 | 14 | 09-13 09:44 `497d504f6` |
| Calbuco (control, fuera del cron) | 91 | 2026-04-24 | (sin campo) | n/a | 0 | 0 | 2026-04-25 |
| Osorno (control, fuera del cron) | 91 | 2026-04-24 | (sin campo) | n/a | 0 | 0 | 2026-09-02 (edición S132, no NRT) |

Records por día de los 11 Tier A sumados (ventana 14 d): 102 a 136 por día, sin ningún día en cero. Los dos controles negativos dan 0 records recientes: el instrumento distingue "viejo" de "no medido".

**Ningún volcán es zombie en el sentido de S133 (verde durante semanas sin producir).** Pero PlanchonPeteroa muestra el mecanismo en pequeño: sus dos jobs de hoy (03:19 y 08:57) fueron `success` y no aportaron ningún record de la noche del 13, mientras los otros 10 volcanes sí tienen sus pasadas de 06:30-07:00. La causa está en el log del job `103701222253` (run 08:57): el cortacircuitos por host de A64 marcó `nrt3.modaps.eosdis.nasa.gov` como caído al primer ConnectTimeout y saltó las 6 plataformas VIIRS ("DOWNLOAD_SKIP host caído ... WARN: Failed to fetch VIIRS_SNPP/NOAA20/NOAA21 y sus _750"), terminando en "No changes to commit for PlanchonPeteroa" y exit 0. En el mismo run, los jobs de Villarrica (`103701222157`) y Láscar (`103701222163`) descargaron **los mismos granules** (ids LANCEMODIS 3032690900/3032689134) de ese mismo host sin problema. En el run de 03:19 el job de PP descargó VIIRS_750 desde LAADS pero falló MODIS_TERRA con "Max retries exceeded" contra `nrt3`. El diseño (S123, `nrt.yml` bloque "records stale") avisa a 72 h por step y `nrt-healthcheck` abre issue a 48 h: una noche entera de un volcán puede quedar sin dato hasta dos días sin que nadie lo vea. Ver hallazgo H2.

### 2.3 `sync-mirova-csv.yml` y los CSV de referencia

- Últimas 60 corridas: todas `schedule` y `success`; última 2026-09-13 11:48 UTC. Escribe `latest_consolidado.csv` (raíz) y regenera `data/mirova/<V>.json` (`sync-mirova-csv.yml:79-119`). Último commit remoto: `f47edb0cb` 2026-09-13 11:49.
- `latest_consolidado.csv` en `origin/main`: 37.308 filas, fecha máxima **2026-09-13 08:40** (fresco).
- `data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv`: 36.255 filas, máxima **2026-09-07 13:30**; `registro_vrp_ocr.csv` del snapshot: 937 filas, máxima 2026-09-07 06:54. Los refresca `audit-weekly.yml:55-57` (curl al repo del scraper) con cron lunes 09:00 UTC; su última corrida programada fue 2026-09-07 14:52 (verde) y el commit `a8d96442a` del mismo día. El desfase de hasta una semana es el que S135 documentó (BLOQUE S136 l. 320-333); hoy son 6 días.
- `data/mirova_reference/registro_vrp_ocr.csv` (fuera del snapshot): 235 filas, máxima **2026-03-28**. Sigue congelado (A17, S125 B1). No medí quién lo consume hoy: SOSPECHA de que nadie, `build_c2ab_windows.py` ya apunta al snapshot según A17.

### 2.4 Otros workflows con cron (7 de 26 yml) y quién dispara los otros 19

| workflow | cron | último run programado | conclusión (últimos 30) |
|---|---|---|---|
| nrt.yml | `0 */2 * * *` | 2026-09-13 08:57 | 73/73 verdes en 14 d |
| nrt-retry.yml | `30 1-23/2 * * *` | 2026-09-13 06:28 | 30/30; sólo relanza si el último NRT terminó `failure` (l. 58-60); con 0 fallos es un no-op correcto |
| nrt-monitor.yml | `30 */6 * * *` | 2026-09-13 05:13 | 30/30; abre issue si 3 corridas seguidas fallan (no mide cadencia) |
| nrt-healthcheck.yml | `0 12 * * *` | 2026-09-12 14:34 | 30/30; umbral 48 h por volcán |
| pages-deploy.yml | `50 */2 * * *` + `workflow_run` + push | 2026-09-13 10:17 (`workflow_run`) | 30/30 |
| sync-mirova-csv.yml | `12 * * * *` | 2026-09-13 11:48 | 60/60 |
| audit-weekly.yml | `0 9 * * 1` | 2026-09-07 14:52 | 9 verdes, 1 cancelada (de 10 programadas) |
| reproc-watchdog.yml | `20 * * * *` | 2026-09-13 10:18 | 30/30 |

Los 19 restantes: `tests.yml` (`pull_request`, `push`, `workflow_dispatch`) y 18 `workflow_dispatch` puros: `backfill-geometry`, `backfill-tier-a`, `reproc-chunked` y **15 yml de experimentos** (`probe-s136-*` ×3, `probe-s137-*` ×2, `reproc-s120`, `s121`, `s124` ×2, `s129`, `s130`, `s133` ×2, `s135`). Ninguno se dispara desde otro yml (`workflow_call` no aparece). No son "no usados" en el sentido A89 (se disparan a mano), pero la regla del proyecto para A/B (CLAUDE.md, tabla de skills) dice copiarlos desde `_archive/` y volver a archivarlos al terminar; 15 quedaron en la carpeta viva.

### 2.5 Frontend contra datos (T7)

`index.html:975-977` lee `data/mirova_equivalent/<V>_recent.json` (ventana de 100 días) y `data/mirova/<V>.json`. `_recent.json` **no está en el repo** (FALTA en `origin/main` para los 11, verificado con `git show`): lo construye `pages-deploy.yml:76` (`scripts/build_recent_json.py`) en `_site/` al desplegar. Verificado en el sitio publicado (`https://mendozavolcanic.github.io/VRP-chile/`, `index.html` con `Last-Modified: Sun, 13 Sep 2026 10:18:35 GMT`):

| archivo servido | N | máx `datetime_utc` | `updated`/`generated_at` | coincide con `origin/main` |
|---|---|---|---|---|
| `data/mirova_equivalent/Villarrica_recent.json` | 1.128 | 2026-09-13 07:00 | 2026-09-13T09:22:36Z | sí (JSON completo: 09-13 07:00) |
| `data/mirova_equivalent/PlanchonPeteroa_recent.json` | 1.037 | 2026-09-12 08:00 | 2026-09-12T20:29:01Z | sí (el hueco de PP se ve en el dashboard) |
| `data/mirova/Villarrica.json` | 27 | 2026-09-04 07:50 | 2026-09-13T06:07:22Z | un sync atrás (repo: 11:49); se despliega en el próximo `workflow_run`/cron |

**Helpers de filtrado por vista** (regla S92 L5: el mismo filtro en las tres vistas live):

| helper | `index.html` | `diario.html` | `mosaico.html` | coincide |
|---|---|---|---|---|
| `mirovaEqVrp` | `(r, innerKm=10, includeFar)`: sin `primary_cluster` → `vrp_mw` con cap 50.000; `distance_class != summit` → 0; `pc.centroid_dist_km > innerKm` → 0; `pc.vrp_mw` con cap | `(r, volcanoName)`: `distance_class` primero; sin `pc` → `r.vrp_mw ?? 0` **sin cap**; `INNER_RADIUS_KM[vol] ?? 5`; cap sobre `pc.vrp_mw` | igual a `index` | lógica igual; **dos diferencias inertes** (ver abajo) |
| cirrus (`isCirrusArtifact`) | `t_max_k < 273.15` y eq > 10 MW y no `_mirova_confirmed` | igual | igual | sí |
| campo difuso (`isDiffuseFieldArtifact`, S93) | vía `isThermalArtifact` | `t_max_k < 278.15` | igual | sí |
| núcleo F5' (`f5_core_vrp_mw`) | `mirovaEqVrpCore` l. 1126 lee el campo del pipeline; toggle `USE_F5_CORE` default `true` (l. 1086) | l. 303, mismo campo | l. 299, mismo campo; default `true` (`sessionStorage`) | sí |
| `inner_radius_km` por Tier A | lista inline l. 714-748 | tabla `INNER_RADIUS_KM` l. 227-231 | lista inline | **11/11 iguales** entre YAML y las 3 vistas (medido) |
| corroboración MIROVA (S137 D5) | `corroboracionMirova` l. 1999 | no | no | indicador de tarjeta, no filtro: no aplica S92 |

Las dos diferencias en `mirovaEqVrp` de `diario` (fallback sin cap 50.000 y orden `distance_class`/fallback invertido) sólo actúan sobre records **sin `primary_cluster`**. Medido en `origin/main` (11 Tier A): hay **18.923** de esos records (hasta hoy, 2026-09-13 07:00: son las no-detecciones, no fósiles pre-S27), **todos con `vrp_mw = 0` y sin `distance_class`**, 0 con `vrp_mw > 50.000`. Hoy el camino es inerte; queda anotado en VERIFICADO LIMPIO con la condición bajo la cual dejaría de serlo.

`comparacion.html`: 0 `mirovaEqVrp`, por diseño (preview S115). No se reporta.

---

## 3. Higiene de git y disco

Medido sobre el checkout canónico (`git worktree list`: sólo la raíz, en `main`).

### 3.1 Ramas

- Remotas: **197** (`git branch -r | wc -l`), de las que 195 son ramas de trabajo (sin `HEAD` ni `main`). Locales: **117** (114 con upstream, 1 marcada `gone`, 2 sin upstream incluida `_respaldo_s126`).
- Clasificación por contenido (`clasificar_ramas.py` + `_v2.py`; `ramas.json` tiene el detalle rama a rama). Método: archivos que la rama cambió respecto de su merge-base con `origin/main` (excluyendo `data/`); si todos están idénticos en main, INTEGRADA. Como main sigue editando los mismos archivos después del squash, 114 salieron "pendientes" por diff; la v2 cruzó cada una con sus PR (`gh api pulls?head=...&state=all`). Control positivo: `s137-cierre` (squash de hoy) sale INTEGRADA por contenido mientras `git cherry` la marca con 0 pendientes; y para `s15-dev` el diff "pendiente" tiene **0 líneas exclusivas de la rama** (main sólo agregó).

| clase | n | qué es |
|---|---|---|
| INTEGRADA_POR_PR (PR mergeado; main editó después los mismos archivos) | 109 | borrables |
| INTEGRADA (contenido idéntico a main) | 28 | borrables |
| SIN_CAMBIOS respecto del merge-base (s70-s75, 51 ramas: `s72-*` 20, `claude/s74-*` 11, `claude/s75-*` 7, `claude/s73-*` 5, `s71-*` 4, `s70-*` 3, otra 1) | 51 | borrables |
| SOLO_DATA (`claude/s127-relanzar-corona`, `s100-promote-data`) | 2 | revisar si el JSON de data importa; probablemente borrables |
| **PENDIENTE_REAL (sin PR, con líneas que main no tiene)** | **4** | ver abajo |
| PR_CERRADO_SIN_MERGE (`claude/s124-brazoC-y-mascara`, PR #528 cerrado) | 1 | decisión explícita de no mergear; borrable con tag |

Las 4 con contenido que main no tiene (líneas exclusivas medidas con `git diff origin/main origin/<rama> -- <archivo> | grep -c "^+[^+]"`):

| rama | último commit | contenido exclusivo |
|---|---|---|
| `s15-dev` | 2026-05-08 | 0 líneas (sólo `docs/MIROVA_DIVERGENCES.md` más viejo). **Integrada de facto**; es la rama donde la raíz quedó atascada hasta S82 (A52) |
| `claude/s79-f66-hybrid-bg-gate` | 2026-05-26 | **trabajo real**: `pipeline/detection_context.py` 85, `process_modis.py` 45, `process_viirs.py` 74, `process_viirs_mod.py` 47, `profile.py` 80, `tests/test_f66_bg_kernel_consistency.py` 120, spec 374 + plan 967 líneas. F66 quedó "parcial" (PR #219) y con gate provisional (#221); esta rama es la versión completa que nunca entró |
| `claude/s126-lascar-tif` | 2026-08-29 | dos scripts contra el TIF de MIROVA (`experiments/_s126_lascar/04_*.py` 166 l., `_s126_villarrica/02_*.py` 155 l.) con sus JSON, y 27-29 líneas más en dos docs S126 que main sí tiene |
| `claude/s126-villarrica-tif` | 2026-08-29 | subconjunto de la anterior |

### 3.2 Stashes (4; ninguno de una sesión viva; las 4 ramas base ya no existen localmente)

| stash | fecha | rama base (local / remota) | archivos |
|---|---|---|---|
| `stash@{0}` | 2026-05-25 09:24 | `work-s78-audit-final` (no / no) | `data/mirova_equivalent/Tupungatito.json` (5.573 líneas, +1.073/-4.542), `experiments/148_audit_pre_reproc/master_table_v2.csv`. **Es el que se reaplicó solo en S137** (A96) |
| `stash@{1}` | 2026-05-23 17:25 | `claude/s74-frontend-bugs-plan` (no / sí) | `pages-deploy.yml` +8, `CLAUDE.md` +6, `frontend/diario.html` +7 |
| `stash@{2}` | 2026-05-23 03:00 | `s72-cierre-bloque-s73` (no / sí) | `data/mirova_equivalent/Lascar.json` +225/-7 |
| `stash@{3}` | 2026-05-22 12:17 | `s72-f2.6b-no-cap-ab` (no / sí) | `tests/test_path_d_d9_fix.py` +72/-16 |

Dos de los cuatro tocan JSON operacionales de `data/mirova_equivalent/`: cualquier `stash pop` accidental los reescribe con datos de mayo.

### 3.3 Disco

- `df -h .`: **476 GB, 473 GB usados, 3,1 GB libres (100 %)**. S138 hablaba de 98 %; hoy es 100 % redondeado. S134 ya registró `MemoryError` en la suite por el pagefile.
- `.git`: **7,8 GB** (`git count-objects -vH`: 9 packs, 6,61 GiB en packs, de los cuales un solo pack de 6,44 GB; **1,15 GiB en 3.523 objetos sueltos**; 173 `prune-packable`). `data/`: 1,1 GB (`mirova_equivalent/` 272 MB, `mirova_equivalent_pre_s27/` 195 MB, `mirova_reference/` 100 MB, `experimental/` 84 MB). `experiments/`: 1,3 GB.

### 3.4 Lista de limpieza propuesta (no ejecutada; requiere A38: tag defensivo + inventario + confirmación)

Tag previo, antes de cualquier borrado: `git tag -a pre-s138-git-cleanup -m "snapshot defensivo antes de limpiar ramas/stashes S138" && git push origin pre-s138-git-cleanup`. Con eso, todo lo borrado se recupera con `git checkout pre-s138-git-cleanup -- <ruta>` o navegando el tag. Para las ramas, además, un archivo `docs/audit_s138/RAMAS_BORRADAS_S138.txt` con `rama sha` de cada una (`git rev-parse origin/<rama>`), que es lo que permite `git branch <rama> <sha>` si hace falta.

1. **Ramas remotas borrables (188 de 195)**: las 109 INTEGRADA_POR_PR + 28 INTEGRADA + 51 SIN_CAMBIOS (lista exacta en `ramas.json`, campo `state2`). Borrado en lotes con `git push origin --delete <ramas>` después del tag y del archivo de shas.
2. **`s15-dev`**: borrable (0 líneas exclusivas), pero dejarla hasta que Nicolás confirme, por su historia (A52).
3. **Ramas locales**: las 114 con upstream que apunten a ramas borradas quedarán `gone`; `git fetch --prune` + borrado local de las `gone`. `_respaldo_s126` (sin upstream): preguntar.
4. **Stashes**: los 4 son de S72 a S78 y sus ramas base no existen localmente. Propuesta: guardarlos como ramas de respaldo antes de tirarlos (`git branch respaldo/stash-s78-audit stash@{0}` etc., o `git stash branch`), y después `git stash drop` uno a uno, empezando por `stash@{0}` (el que se reaplicó solo). Nunca `stash pop`.
5. **`.git`**: después de borrar ramas, `git gc --prune=now` (compacta los 1,15 GiB sueltos y los 173 prune-packable; el pack de 6,4 GB es la historia de `data/` y no baja sin reescribirla). Ganancia esperada modesta (~1 GB); el disco al 100 % es un problema del PC, no del repo (476 GB totales).
6. **Workflows de experimentos**: mover los 15 `probe-s13x`/`reproc-s1xx` de `.github/workflows/` a `_archive/` (regla del proyecto); son `workflow_dispatch` puros, no pierden nada.
7. **`data/mirova_reference/registro_vrp_ocr.csv`** (congelado 2026-03-28): candidato a borrar o marcar como histórico, sólo tras confirmar que nadie lo lee (no medido aquí).

**NO borrar**: `claude/s79-f66-hybrid-bg-gate` (trabajo real de pipeline sin PR; decidir si se archiva como tag `archive/f66-hybrid-bg-gate` o se abre PR), `claude/s126-lascar-tif` y `claude/s126-villarrica-tif` (scripts contra el TIF sin equivalente en main; mismo tratamiento), `claude/s124-brazoC-y-mascara` hasta que se anote por qué se cerró el PR #528, las dos SOLO_DATA hasta revisar el JSON, ningún tag existente (100), `data/mirova_equivalent_pre_s27/` (195 MB; tiene tag `pre-*` según A38, no verificado aquí).

---

## 4. Hallazgos (por gravedad; formato del preámbulo)

### H1. La cadencia del NRT sigue en el 43 % desde el 30 de agosto; ningún monitor mide cadencia
- **SCRIPT:SALIDA**: `experiments/_s138_audit/eje6/cadencia_nrt.py` → 73 corridas programadas de 168 en 14 d; 49 huecos > 4 h; hueco típico 4,7-5,9 h. `docs/s133/CADENCIA_DEL_CRON.md:32-40` (4,8/día, 40 % en S133).
- **QUÉ PASA**: una pasada nocturna (06:30-07:00 UTC) puede esperar hasta ~5 h el siguiente cron en vez de 2. GitHub entrega la mitad de las corridas programadas a los cuatro workflows con cron; no es configuración nuestra (`nrt.yml:12` sigue en `0 */2`). `nrt-monitor` (3 fallos seguidos) y `nrt-healthcheck` (48 h) no ven una cadencia baja con 0 fallos.
- **CÓMO SE VE EN EL DASHBOARD**: todo se ve, más tarde. La latencia de una anomalía nueva sube de 3-4 h a 5-7 h.
- **CÓMO REPRODUCIRLO**: `gh run list --workflow=nrt.yml --limit 200 --json createdAt,event` y contar por día.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 3 (atrasa una alerta, no la pierde).

### H2. Un job puede terminar verde sin descargar nada cuando el cortacircuitos de A64 declara caído a LANCE en el primer ConnectTimeout; PlanchonPeteroa perdió la noche del 13 mientras dos jobs vecinos bajaban los mismos granules
- **ARCHIVO:LÍNEA**: log del job `103701222253` (run 34748715101, 2026-09-13 08:57): "DOWNLOAD_SKIP host caído ['nrt3.modaps.eosdis.nasa.gov']" ×6 plataformas VIIRS, "No changes to commit for PlanchonPeteroa", exit 0. Jobs `103701222157` (Villarrica) y `103701222163` (Láscar) del mismo run: `DOWNLOAD_DONE` de LANCEMODIS 3032690900/3032689134, los mismos ids. `pipeline/fetch.py` (cortacircuitos por host, #364; no releído aquí). `nrt.yml` bloque "Tier A stale": warning a 72 h, `sys.exit(0)`. `nrt-healthcheck.yml:12`: 48 h.
- **QUÉ PASA**: LANCE es intermitente por conexión, no por host; el cortacircuitos, pensado para el hang de 50 min (A64), convierte un timeout aislado en "saltar todo lo de este host en este job". El job es `success`, así que ni `nrt-retry` (sólo relanza `failure`) ni `nrt-monitor` actúan. Con la cadencia de H1, la siguiente oportunidad es ~5 h después, y si vuelve a caer en el primer intento, otras 5. El aviso llega a las 48 h.
- **CÓMO SE VE EN EL DASHBOARD**: hoy PP muestra su última pasada del 12 a las 08:00 (`PlanchonPeteroa_recent.json` servido: máx 2026-09-12 08:00); los otros 10 volcanes están al 13. Un operador ve "sin novedad" en PP durante una noche que sí se observó.
- **CÓMO REPRODUCIRLO**: `gh run view --job 103701222253 --log | grep -a "DOWNLOAD_SKIP\|No changes"`; comparar con `gh run view --job 103701222157 --log | grep -a "3032690900"`. Volcán PlanchonPeteroa, pasadas 2026-09-13 ~06:36 UTC.
- **CONFIANZA**: CONFIRMADO (mecanismo y caso). SOSPECHA: que ocurra con frecuencia; sólo se midió el caso de hoy (1 volcán de 11 en 1 run de 3 revisados a nivel job). **GRAVEDAD**: 3 (una noche de un volcán invisible hasta 48 h; no es pérdida definitiva porque cada corrida reprocesa el día).

### H3. Las decisiones viven repetidas en tres bloques sin marca de "superada"; D19 no se re-enunció
- **ARCHIVO:LÍNEA**: `tasks/BLOQUE_ARRANQUE_S136.md:52-61` (#1), `S138.md:28-41` (#4): misma pregunta; `S134 §D D4` vs `S138 #5`; `D8` vs `S137 #2`. `docs/MIROVA_DIVERGENCES.md:2058-2143`: 0 menciones a S136/S137 pese a la decisión S136-3 (a).
- **QUÉ PASA**: el error de S137 (recomendar el A/B ya corrido) tiene esta causa: nadie podía saber sin leer cuatro archivos qué estaba hecho. De 16 abiertas, sólo 12 son distintas.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: sección 1 de este informe.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 2 (tuerce el trabajo, no una alerta).

### H4. Disco al 100 % y `.git` de 7,8 GB con 1,15 GiB de objetos sueltos
- **SCRIPT:SALIDA**: `df -h .` → 3,1 GB libres de 476; `git count-objects -vH` → size 1,15 GiB, size-pack 6,61 GiB, 173 prune-packable.
- **QUÉ PASA**: la suite ya dio `MemoryError` por pagefile (AUDIT_S134, seguimientos). Un reproceso local o un `pip install` puede fallar por espacio, no por código.
- **CÓMO SE VE EN EL DASHBOARD**: invisible (el NRT corre en GitHub).
- **CÓMO REPRODUCIRLO**: los dos comandos.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 2.

### H5. Cuatro stashes de mayo, dos con JSON operacionales, sobre ramas que ya no existen; uno ya se reaplicó solo
- **SCRIPT:SALIDA**: `git stash list --format='%gd %ci %s'`; `git stash show --stat stash@{0}` → `data/mirova_equivalent/Tupungatito.json` +1.073/-4.542.
- **QUÉ PASA**: un `git stash pop` con árbol limpio reaplica el más reciente (A96): en S137 pisó Tupungatito.json con datos de mayo hasta que se restauró. Mientras existan, el riesgo se repite.
- **CÓMO SE VE EN EL DASHBOARD**: si llega a commitearse, Tupungatito retrocede a mayo de 2026.
- **CÓMO REPRODUCIRLO**: los comandos de arriba (no hacer `pop`).
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 2.

### H6. Una rama con trabajo real de pipeline sin PR (`claude/s79-f66-hybrid-bg-gate`) y dos con scripts contra el TIF (`claude/s126-*-tif`)
- **SCRIPT:SALIDA**: `clasificar_ramas_v2.py` → PENDIENTE_REAL 4; líneas exclusivas: pipeline 85+45+74+47+80, tests 120, spec+plan 1.341; `_s126_lascar/04_*.py` 166, `_s126_villarrica/02_*.py` 155.
- **QUÉ PASA**: F66 quedó "parcial" (#219) con gate provisional (#221); la versión completa nunca entró ni se archivó con nombre. Si alguien limpia "todas las ramas viejas", se pierde.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `git diff origin/main origin/claude/s79-f66-hybrid-bg-gate -- pipeline/ tests/ | grep -c "^+[^+]"`.
- **CONFIANZA**: CONFIRMADO (existe). SOSPECHA: si vale la pena rescatarlo (no evaluado). **GRAVEDAD**: 1.

### H7. 15 workflows de experimentos en la carpeta viva de `.github/workflows/`
- **ARCHIVO**: `probe-s136-*.yml` ×3, `probe-s137-*.yml` ×2, `reproc-s120`, `s121`, `s124` ×2, `s129`, `s130`, `s133` ×2, `s135` (todos `workflow_dispatch` puros; `python -c "yaml.safe_load"` sobre cada uno).
- **QUÉ PASA**: la regla del proyecto (tabla de skills, "A/B test") dice copiarlos desde `_archive/` y volver a archivarlos. Cualquiera de ellos es un botón de reproceso a mano contra `data/`.
- **CÓMO SE VE EN EL DASHBOARD**: invisible salvo que alguien lo dispare.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 1.

### H8. El snapshot de referencia va hasta 7 días detrás del frontend; y un CSV OCR congelado desde marzo sigue en el repo
- **ARCHIVO**: `data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv` máx 2026-09-07 vs `latest_consolidado.csv` máx 2026-09-13; `data/mirova_reference/registro_vrp_ocr.csv` máx 2026-03-28 (235 filas).
- **QUÉ PASA**: ya documentado en S135 (BLOQUE S136 l. 320-333) y A17. Lo nuevo es sólo que sigue igual. Toda medición que use el snapshot cuenta como "detectamos y MIROVA no" los últimos días de la semana si no recorta la ventana.
- **CÓMO SE VE EN EL DASHBOARD**: no lo afecta (el frontend usa `latest_consolidado.csv` vía `data/mirova/`).
- **CONFIANZA**: CONFIRMADO (fechas). SOSPECHA: que el OCR congelado no tenga consumidor. **GRAVEDAD**: 1.

### H9. `S136-2` figura como "cerrado" (S137 §e.5) y como "formalmente indeterminado" (S137 §d) en el mismo archivo
- **ARCHIVO:LÍNEA**: `tasks/BLOQUE_ARRANQUE_S137.md:141` ("Retirar la intersección contextual. Los datos apuntan a que sigue curando") vs l. 121-123 ("n insuficiente (3 contra el umbral de 4), formalmente sigue indeterminado").
- **QUÉ PASA**: es el patrón de A95: un cierre sin la medición que lo respalde. Quien lea sólo §e no vuelve a mirarlo.
- **CONFIANZA**: CONFIRMADO (las dos frases). **GRAVEDAD**: 1.

---

## 5. VERIFICADO LIMPIO (no volver a mirar en la treinta, salvo que cambie el comando)

- **Ningún run rojo del NRT en 14 días**: 73/73 `success` (`cadencia_nrt.py`); 33/33 jobs por volcán en los 3 últimos runs (`gh run view <id> --json jobs`).
- **Los 11 Tier A tienen records en los 14 días, sin un día en cero** (102-136 records/día sumados); el último commit remoto de cada JSON es de hoy salvo PP (ayer 20:43, ver H2). `zombies.py`. Los dos controles fuera del cron dan 0 recientes: el detector distingue.
- **El sitio publicado está al día**: `index.html` `Last-Modified 2026-09-13 10:18 GMT`; `Villarrica_recent.json` servido = máx 2026-09-13 07:00 = JSON completo en `origin/main`. `pages-deploy` corre por `workflow_run` tras cada NRT (última 10:17) además del cron.
- **`_recent.json` no está en el repo y no debe estarlo**: lo construye `pages-deploy.yml:76` en `_site/`. No es un archivo faltante.
- **`sync-mirova-csv`**: 60/60 verdes; `latest_consolidado.csv` máx 2026-09-13 08:40; `data/mirova/<V>.json` regenerados 11:49. El indicador D5 de `index.html:1999` lee un dato que existe y está fresco.
- **`inner_radius_km` de los 11 Tier A**: idéntico en `volcanoes.yaml`, `index.html`, `mosaico.html` y la tabla `INNER_RADIUS_KM` de `diario.html` (0 discrepancias de 11; script inline en esta sesión, reproducible con el bloque de la sección 2.5).
- **Filtros de display en las tres vistas**: cirrus (`t_max_k < 273.15` y > 10 MW), campo difuso (`< 278.15`), núcleo F5' (`f5_core_vrp_mw`, toggle default `true`) y el gate `distance_class`/`centroid_dist_km` coinciden. La única asimetría (fallback sin cap en `diario.html` para records sin `primary_cluster`) es inerte: 18.923 records sin `pc` en los 11 Tier A y **0 con `vrp_mw > 0`**. Dejaría de serlo sólo si el pipeline empezara a escribir `vrp_mw > 0` sin `primary_cluster`; el comando para re-medirlo está en `frontend_vs_datos.py` y en el bloque inline de la sección 2.5.
- **Flags de las decisiones, todos OFF en producción** (medidos con `pipeline.profile`, perfil `mirova_equivalent`): `ENABLE_SECOND_PASS_CONDITIONED`, `ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER`, `ENABLE_TEST1_NTI_INTEGRAL`, `ENABLE_UTM_REGRID`, `ENABLE_MODIS_B22_PRIMARY`, `ENABLE_TESTS_23_PROSE_BRANCH`, `ENABLE_TEST1_LOCAL_BG_NTI`. Nada se encendió entre S134 y hoy.
- **Ningún PR sobre `pipeline/` después de #637**; el último mergeado es #637 (2026-09-13). `gh pr list --state merged --limit 70`.
- **`nrt-retry`, `nrt-monitor`, `reproc-watchdog`**: 30/30 verdes; su silencio es correcto (0 fallos), no zombie: cada uno tiene una condición explícita leída en el yml (`nrt-retry.yml:58-60`).
- **Concurrencia de `nrt.yml`**: `group: push-main`, `cancel-in-progress: false`, `max-parallel: 8`, `timeout-minutes: 80` por job (l. 56-80). Peor job observado en los 3 runs: Villarrica 48 min; peor run completo: 03:19 → 04:40 (81 min con 3 jobs en cola por el `max-parallel`).
- **`git worktree list`**: sólo la raíz, en `main`. `git status`: limpio salvo las dos carpetas de esta auditoría.
- **Squash vs `git cherry`**: verificado el control positivo (`s137-cierre` sale INTEGRADA por contenido); la clasificación de ramas no usó `cherry`.
- **El bloque "records stale" de `nrt.yml` y `nrt-healthcheck.yml`** hacen lo que dicen (72 h aviso / 48 h issue); lo que no hacen (ver H2) es diseño de S123, no bug.

---

## Resumen (menos de 400 palabras)

**Qué se está rompiendo.** Dos cosas, ninguna nueva ni corregida. Primero, GitHub entrega desde el 30 de agosto el 43 % de las corridas del NRT (73 de 168 en 14 días, huecos de 5 h en vez de 2), el régimen que S133 midió en 40 %. No se pierden records, pero una anomalía nueva tarda 5 a 7 h en vez de 3 en llegar al dashboard, y ningún monitor mide cadencia. Segundo, el hallazgo propio de este eje: un job del NRT puede terminar verde sin bajar nada. Hoy a las 08:57 el cortacircuitos de A64 declaró caído a LANCE en el job de Planchón-Peteroa al primer timeout y saltó las seis plataformas VIIRS, mientras Villarrica y Láscar bajaban los mismos granules en el mismo run. PP es el único Tier A sin la noche del 13, el job fue `success`, `nrt-retry` sólo relanza fallos y el aviso llega a las 48 h.

**Decisiones.** De 25 entradas en cinco fuentes: 5 ejecutadas, 4 superadas y 16 abiertas, de las que sólo 12 son distintas (la adopción del A/B está escrita tres veces). Ningún flag cambió; ningún PR tocó `pipeline/` desde #637. D19 no se re-enunció aunque se decidió hacerlo.

**Frontend.** Coincide con los datos: sitio publicado a las 10:18 de hoy, filtros iguales en las tres vistas, `inner_radius_km` 11/11 idénticos, indicador D5 leyendo un archivo regenerado a las 11:49. La asimetría de `diario.html` (fallback sin cap) es inerte: 0 de 18.923 records sin cluster tienen VRP.

**Higiene.** 197 ramas remotas: 188 borrables, 4 con contenido real sin PR (la que importa: `claude/s79-f66-hybrid-bg-gate`, ~330 líneas de pipeline y tests) y 1 cerrada a propósito. 4 stashes de mayo, dos con JSON operacionales, uno ya reaplicado solo en S137. Disco al 100 % (3,1 GB libres), `.git` 7,8 GB.

**Ruta.** (1) Tag `pre-s138-git-cleanup` + archivo de shas; recién entonces borrar las 188 ramas, convertir los stashes en ramas de respaldo y `gc`. (2) Decidir sobre el cortacircuitos (reintentar una vez antes de declarar el host caído, o que un job con 0 descargas no sea un `success` mudo); toca `pipeline/fetch.py`, así que A45. (3) Un monitor de cadencia (menos de 6 corridas en 24 h abre issue), pedido en S133 y todavía inexistente. (4) Heredar la tabla de la sección 1 como única lista de decisiones en el bloque de arranque S139.
