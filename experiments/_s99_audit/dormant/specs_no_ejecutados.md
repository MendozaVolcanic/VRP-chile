# Auditoría S99 — Diseños / planes escritos pero NO ejecutados (o a medias)

> Generado 2026-06-03. Scope: `docs/superpowers/specs/*.md` + `tasks/*.md`.
> Cruzado con código (`pipeline/`, profiles, tests) y git log.
> Solo lectura. No se tocó código ni datos.

Distinción clave usada: **"decidido NO hacer con justificación"** (refutado por
datos / A/B / contradice MISSION) vs **"quedó colgado"** (diseño completo, sin
veredicto explícito de descarte, simplemente no se retomó).

---

## Tabla maestra — design docs (`docs/superpowers/specs/`)

| Doc | Qué propone | Estado | Impacto potencial |
|---|---|---|---|
| `2026-05-06-vrp-integrated-eq1.md` | VRP Test1 = Coppola 2015 Eq.1 textual (suma neta SIN clip per-píxel, max global) cuando `final_hotspot_source=test1`. Flag `ENABLE_VRP_INTEGRATED_EQ1`. | **NO-EJECUTADO** (colgado). Diseño completo con 5 fases, A/B, tests. 0 implementación: no existe flag ni rama en code, 0 commits. | **ALTO** — ataca directamente la inflación de magnitud Test1 (Lastarria 18×, Villarrica 65×, PCC 12×). Es la causa raíz del 19× Tupungatito que S99 ataca por otra vía (Núcleo espacial). |
| `2026-05-17-vrp-three-regimes-design.md` | 3 regímenes VRP (Coppola 2024): R1 Wooster >600K (ya), **R2 lava-lake sub-píxel Eq.16 (Burgi-Coppola, T_e=1000K)**, **R3 crater-lake hidrotermal Eq.25**. Flags per-vol `lava_lake_magmatic`/`crater_lake_hydrothermal`. | **A MEDIAS y abandonado**. R2 (`compute_vrp_lava_lake_eq16`) **escrito + testeado** en `pipeline/vrp_regimes.py` (S57, commit `1a982742`) pero **NUNCA wired** a `process_*.py` (solo `compute_local_background` se importa). R3 (`compute_vrp_crater_lake_eq25`) ni se escribió. `detect_regime` tampoco. Flags yaml nunca creados. | **ALTO** — apunta exactamente al problema crónico que sigue abierto S99: Villarrica/lava-lake sub-píxel inflado ~30×. Función ya escrita y validada con tests; falta integrarla. |
| `2026-05-10-d8-cluster-selection.md` + `2026-05-11-plan-integrado-s36.md` | H_D8_5: clon literal Coppola 2016a — ETI cuadrático scene-wide + second-pass + **reporting Σ RP_pix sin primary_cluster** + distancia = píxel activo más lejano. | **PARCIAL → refutado/superado**. ETI cuadrático + second-pass se implementaron (S37) y A/B los refutó como detección (delta TP +0). El **reporting Σ-global (deprecar `primary_cluster`)** NUNCA se adoptó; en su lugar S38 adoptó `vent_anchored` (otra solución a D8). | MEDIO — la idea de Σ-global vs primary_cluster sigue siendo la divergencia arquitectural raíz con MIROVA; quedó documentada pero descartada por riesgo. |
| `2026-05-11-plan-integrado-s36.md` Bloque D | **HotLINK CNN (USGS AVO) como benchmark R3 independiente** (tri-way VRP-chile vs MIROVA vs HotLINK). +22% recall / −12% FP reportado en Alaska. | **NO-EJECUTADO** (colgado). 0 refs a "hotlink" en code/scripts/profiles. Nunca clonado ni corrido. | MEDIO — daría una vara de medición INDEPENDIENTE de MIROVA (rompe la circularidad "nos medimos solo contra MIROVA"). No mejora el clon directamente. |
| `2026-05-12-paths-retirement-analysis.md` | Retirar paths heredados (`bt_path`, `nti_rel`, `dnti_ctx`) dejando solo los 3 de papers MIROVA core. Flag `enable_only_h_d8_5_paths`. | **PARCIAL**. `bt_path` SÍ se retiró (S40, `enable_bt_path_hot:false`). `nti_rel` sigue OFF pero no se borró del código. `dnti_ctx_hot` sigue ON (no se retiró — habría sido redundante solo si H_D8_5 validaba, y no validó). Flag `enable_only_h_d8_5_paths` nunca se creó. | BAJO — limpieza de claridad/alineación-paper, no mejora métricas. Parcialmente hecho. |
| `2026-05-12-d8-combo-fix.md` | Combo D8 vent_anchored + H8 + D4 los 3 juntos. | **EJECUTADO** (con matiz). vent_anchored + H8 adoptados S38; D4 se adoptó S39 pero **per-vol** (universal regresionaba Tupungatito). Resuelto. | — (cerrado) |
| `2026-05-13-frontend-audit-s38.md` | Filtro "Solo post-S38" + 4 recomendaciones frontend S39+. | **EJECUTADO** (filtro). Las **4 recomendaciones S39+** (toggle sum_active, reasignar distance_class, cleanup fallbacks vrp_mir_mw, default postS38=true) quedaron colgadas, todas BAJO impacto. | BAJO |
| `2026-05-15-s46-coppola-literal-design.md` | A/B 13 variantes drifts Coppola literal (drift1/23/4/7 + Di Bella n12). | **EJECUTADO parcialmente**. drift234 (first+second pass dual-ROI) ADOPTADO S46. **Drift #7 (A_pix nadir-fijo, sospechoso del ratio MODIS 1.21×)** y **variante 13 Di Bella n12 VIIRS** (objetivo-2) quedaron como variantes A/B sin adopción ni veredicto documentado de descarte. | MEDIO (drift7) — el ratio MODIS 1.21× sigue sin cerrarse; drift7 era la hipótesis principal. |
| `2026-05-29-s88-pc-classification-design.md` | `geo_class` (summit/extension/far) en store + `mirova_confirmed` en frontend + `volcanic_features.yaml`. | **EJECUTADO** (S89, geo_class + volcanic_features.yaml + tests presentes). Fase 2 (`artifact_candidate` físico PCC/Tupun) diferida explícitamente. | — (Fase 1 cerrada) |
| `2026-05-30-*` (cirrus / diffuse / clon-por-sensor) | Display suppression + plan 5 fases clon-por-sensor. | **EJECUTADO** (display S90-S93). **F3 co-validación SOLO-MODIS** (raíz, pipeline) quedó pendiente A45. | MEDIO (F3) |
| `2026-05-31-f5-coldfield-magnitude-design.md` | Núcleo F5' magnitud campo-frío. | **EJECUTADO** display (S95-S96). Pipeline pendiente A45 (= lo que S99 retoma). | — (en curso S99) |
| `2026-06-02-detection-anchor-crater-design.md` | Fix ancla al cráter. | **EJECUTADO + PROMOVIDO** S98. | — (cerrado) |
| `2026-06-03-test1-magnitude-compactness-design.md` | Cand B `ENABLE_TEST1_SPATIAL_CORE`. | **EN CURSO** (S99, hoy). NO dormant. | — |

---

## Tabla — planes / backlogs (`tasks/`)

| Archivo | Item | Estado | Impacto |
|---|---|---|---|
| `backlog_s27.md` §B | Re-scrape Mirova-v1 para cubrir gap ~30% VIIRS del CSV consolidado | **COLGADO**. El gap CSV sigue siendo fuente de sesgo TP/FN documentado hasta S86/S94 (loader OCR). Mitigado parcialmente por usar OCR (A11), nunca re-scrapeado a fondo. | MEDIO — ground truth sesgado afecta TODAS las métricas de recall/precision. |
| `backlog_s27.md` §C | Investigar D4 sub-pixel summit (Lastarria/Planchón) bajando granules pixel-level | **SUPERADO** por kernel-bg S61 + D4 per-vol S39. Cerrado de facto. | — |
| `backlog_s27.md` Bugs 9-18 frontend | 10 bugs LOW dashboard (exclude_zones invisibles, 86k markers PCC, CSV export incompleto, VOLCANOES_ALL hardcoded, etc.) | **COLGADO**, casi todos BAJO. Algunos pueden seguir vivos (CSV export incompleto, límite markers). | BAJO |
| `backlog_s32_schema_gap_anomaly_pixels.md` | `anomaly_pixels` ≠ `primary_cluster.vrp_mw` (Test1 path). Opción A/B/C. | **RESUELTO** tarde (S94 PR #294 portó Test1 anomaly_pixels; S95 a MODIS/V750). Estuvo colgado ~62 sesiones — rompía el mapa del dashboard y bloqueaba F5'. | — (cerrado, lección: gaps de schema laten años) |
| `backlog_s93_pipeline_diffuse_field_gate.md` | Gate "campo difuso" en PIPELINE (no solo display) para PCC MODIS 337 MW | **COLGADO con justificación parcial**. Display ya lo oculta; pipeline lo sigue generando. Decisión Nicolás: opcional, no urgente. Reaparece como "fuera de alcance §7" en spec S99. | MEDIO — datos crudos siguen sucios (afecta paper/provenance, no operacional). |
| `tasks/decisions_s14.md`, `tasks/lessons.md`, handoffs S17-S47 | varios | mayoría superados o consolidados en CLAUDE.md/MEMORY | — |

---

## TOP 5 diseños valiosos NO ejecutados que valdría retomar

### 1. VRP three-regimes R2 lava-lake (`2026-05-17-vrp-three-regimes-design.md`)
- **Por qué vale**: el problema que persigue (lava-lake sub-píxel inflado ~30×,
  Villarrica) sigue ABIERTO en S99 y es justamente el "canario FN" del fix de hoy.
- **Cuán completo**: muy alto. `compute_vrp_lava_lake_eq16` ya escrito y con tests
  (`tests/test_vrp_regimes_lava_lake.py`). Falta SOLO: `detect_regime`, wiring en
  process_*, flags yaml, A/B Villarrica 30d. Diseño tiene criterios CA1-CA5,
  pre-mortem, MISSION 3-preguntas (pasa). Burgi-Coppola T_e=1000K es paper MIROVA core.
- **Riesgo de no retomarlo**: se reinventa el mismo cálculo desde cero (ya pasó:
  el Núcleo F5' display y el Cand B S99 son aproximaciones espaciales al MISMO
  problema que Eq.16 resuelve físicamente).

### 2. VRP integrated Eq.1 textual (`2026-05-06-vrp-integrated-eq1.md`)
- **Por qué vale**: ataca la inflación de magnitud Test1 (la familia entera de
  18-65× ratios) en su raíz conceptual: dejamos de clipar per-píxel y sumamos neto
  como dice el paper. Es complementario (no excluyente) al Cand B espacial S99.
- **Cuán completo**: diseño completo (fórmula, alcance, 5 fases, tests, pre-mortem,
  MISSION pasa por Coppola 2015 §2.2). 0 código.
- **Caveat**: S99 eligió el camino espacial (Núcleo). Conviene al menos compararlos
  en el A/B S99 antes de descartar definitivamente Eq.1 — son hipótesis rivales sobre
  la MISMA falla.

### 3. Drift #7 — A_pix nadir-fijo MODIS (`2026-05-15-s46-coppola-literal-design.md`, variantes 9-11)
- **Por qué vale**: el ratio MODIS ~1.21× vs MIROVA sigue sin explicación cerrada;
  drift7 (quitar la corrección sec³ y usar 1 km² fijo como el paper) es la hipótesis
  principal y nunca se corrió/adoptó su veredicto. Coppola 2016a Eq.7 es literal.
- **Cuán completo**: alto — perfiles `_drift7_*` ya existen, implementación de
  `nadir_fixed` en scan_geometry diseñada. Falta correr el A/B aislado y decidir.
- **Riesgo**: contradice A36 (sec³ es física real off-nadir). Hay que reconciliar:
  ¿MIROVA resamplea a grilla 1 km ANTES de calcular área? Diseño lo plantea, sin cerrar.

### 4. HotLINK como benchmark independiente (`2026-05-11-plan-integrado-s36.md` Bloque D)
- **Por qué vale**: hoy nos medimos SOLO contra MIROVA → circularidad. Un detector
  CNN independiente (open-source USGS) daría una segunda vara y detectaría si
  perdemos eventos que NI MIROVA publica (relevante para el objetivo-2 "mejor que
  MIROVA" y para validar la categoría-b de S86).
- **Cuán completo**: plan operativo (clonar, instalar TF 2.15, correr sobre Lascar/
  Puyehue, tri-way). 0 ejecución.
- **Caveat**: no mejora el clon literal; es investigación/validación. Esfuerzo medio-alto.

### 5. H_D8_5 reporting Σ-global (deprecar primary_cluster) (`2026-05-10-d8-cluster-selection.md`)
- **Por qué vale**: es la divergencia arquitectural MÁS profunda documentada —
  MIROVA NO selecciona un primary_cluster, suma todos los píxeles activos y reporta
  distancia al píxel más lejano. Todo nuestro andamiaje (vent_anchored, F5', Cand B)
  son parches alrededor de tener un concepto (primary_cluster) que MIROVA no usa.
- **Cuán completo**: matemática completa leída del paper. La detección (ETI/2nd-pass)
  se implementó y refutó; el **reporting Σ-global** se decidió NO hacer por riesgo de
  romper los 157/191 casos que ya matcheaban.
- **Caveat**: descarte tuvo justificación (riesgo regresión amplia). Pero con el
  loader corregido (S94) y TIFs MIROVA (S98+) hoy se podría A/B-testear con menos
  riesgo del que había en S37. Vale reabrir la pregunta, no necesariamente adoptar.

---

## Notas de método
- "Implementado" verificado por presencia de flag en `mirova_equivalent.yaml` +
  función wired en `process_*.py`, no solo por existencia de archivo/test.
- Varios diseños se "ejecutaron a medias" porque su A/B los refutó como mejora de
  DETECCIÓN (H_D8_5) pero su componente de REPORTING quedó sin probar — distinción
  importante para no concluir "se hizo" cuando solo se hizo la mitad.
- El patrón recurrente de mayor valor perdido: **funciones escritas + testeadas pero
  nunca wired** (lava_lake Eq.16) y **fórmulas-raíz diseñadas pero sustituidas por
  parches** (Eq.1 textual → Núcleo espacial; Σ-global → vent_anchored).
