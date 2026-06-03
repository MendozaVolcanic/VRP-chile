# Auditoría de A/B tests abandonados — S99

> **Veta**: perfiles A/B (`pipeline/profiles/*.yaml`) que se MONTARON (perfil +
> reproc) pero NUNCA se concluyeron formalmente → posibles hallazgos perdidos.
> Disciplina systematic-debugging: inventario → buscar veredicto → clasificar.
> NO se tocó código ni datos. Citas a archivo verbatim.
>
> Complementa (sin duplicar): `flags_off.md` (flags OFF en profile.py) y
> `github_estado.md` (ramas/PRs/issues). Esta veta mira el **eje A/B-perfil**.

## Método

1. Inventario de los ~85 perfiles en `pipeline/profiles/`. Leí la cabecera
   (comentario) de cada NO-operacional.
2. Para cada uno busqué veredicto registrado en: `docs/` (F26_VERDICT,
   MIROVA_DIVERGENCES, DRIFTS_S17, DATA_SUBDIRS_INVENTORY_S80,
   F28_DATA_ARCHIVE_INVENTORY, F_S81_*, PROCESS_RULES_S33), `experiments/*/*.md`
   y `git log`.
3. Clasifiqué cada A/B: **CONCLUIDO** (adoptado/refutado/archivado bien) vs
   **COLGADO** (sin veredicto + impacto en magnitud/recall).

## Hallazgo principal

**La gran mayoría de los A/B ESTÁN bien cerrados.** El proyecto tiene una
contabilidad de veredictos sorprendentemente buena: `F28_DATA_ARCHIVE_INVENTORY.md`
(S73) le asigna veredicto explícito a los 41 subdirs A/B S24–S46, y
`F26_VERDICT_CONSOLIDATED_S72.md` + `MIROVA_DIVERGENCES.md` cierran los hilos
S71–S72. La sospecha de Nicolás ("abandonamos ideas valiosas a medio camino")
se cumple solo en **3–4 casos**, y casi todos son de **precisión/beyond-MIROVA**,
no de recall perdido. El único A/B genuinamente colgado **con impacto de
magnitud** es de la sesión en curso (S99, esperado) y uno arqueológico (Driver B
Phase 2).

---

## Tabla maestra (perfiles A/B no operacionales)

| Perfil(es) A/B | Hipótesis testeada | ¿Concluido? | Veredicto registrado | Impacto |
|---|---|---|---|---|
| `_s99_test1_baseline/_pixfilter/_core` | Recortar Test1 a foco compacto espacial (Cand. B) vs filtro por-píxel (Cand. A) para curar 19× Tupungatito | **NO — EN VUELO** | Reproc corriendo (run 79221944677+, `_ab_watch.log`); flag `enable_test1_spatial_core` OFF; audit `ab_test1_audit.py` pre-escrito sin ejecutar | **ALTO (magnitud)** — es el §2 activo de S99 |
| `mirova_equivalent_phase2` (`enable_final_pixel_filter`) | Filtro N·σ dual-ROI sobre la MASK FINAL combinada (post-OR todos los paths), no solo Test1 | **NO — COLGADO** | Sin doc de veredicto. Driver B Phase 1 (`test1pix`) se adoptó con métrica BUGGY (S33) y luego la línea Driver B quedó desacreditada; Phase 2 nunca se re-validó. `enable_test1_pixel_filter: false` y `enable_final_pixel_filter` ausente del operacional | **MEDIO-ALTO (magnitud)** — apuntaba a los pixels marginales que inflan ratio (mismo problema que S99 ataca ahora por otra vía) |
| `mirova_equivalent_no_cap_v1` (F2.6.b) | ¿El cap D9 5MW aporta o ya es redundante con features S38-S71? | SÍ (parcial) | `experiments/137_3way_audit/audit.md`: "0/9 vols idénticos; mantener cap por defensa, no depende de él". **Caveat**: arm Lascar/Villarrica MISSING (workflow failure F2.6.b) | BAJO — verdict alcanzado pese a arms faltantes |
| `mirova_equivalent_bt_path_on_v1` (F2.6.e) | Revertir S40 (bt_path ON) → ¿Lascar vuelve a ~389 MW? | SÍ | `experiments/137_3way_audit`: NO confirma (0.41× vmax, recall -10pp). **Mantener bt_path OFF** | BAJO — bien cerrado |
| `mirova_equivalent_path_d_atm_gate_v1` (D9 Op.A) | Gate atmosférico t_bg<265K para path D cirrus | SÍ | `MIROVA_DIVERGENCES.md` S71 Fase2: refutado (recall 6/7) | BAJO — cerrado |
| `mirova_equivalent_path_d_covalidation_v1` (D9 Op.B) | Path D solo cuenta si BT/NTI también dispara | SÍ | `MIROVA_DIVERGENCES.md` S71 Fase2: refutado (recall 5/7) | BAJO — cerrado |
| `mirova_equivalent_path_d_cap_v1` (D9 Op.C) | Cap 5MW @ t_bg<270K path-D-only | SÍ | **ADOPTADO S71** (`path_d_only_cap_mw: 5.0` en operacional) | — cerrado/adoptado |
| `mirova_equivalent_unsuitable_filters_v1` / `_unsuitable_only_v1` / `_test1_retire_only_v1` (S72 F1.2/F2.3) | Filtros unsuitable §267-273 + K1 retire §298-300 al pool bg | SÍ | `experiments/132/133` 4-way audit + `F26_VERDICT`: causó "Lascar regression" que resultó ILUSORIA (eran FPs Salar). NO adoptado tal cual; lógica entró vía drift234 | MEDIO — cerrado, lección A34 |
| `mirova_equivalent_f_s81_a_intra_radio_enabled/_disabled` (S83) | Gate path D intra-radio (cono) MODIS | SÍ | **ADOPTADO S84** (`F_S81_A_ADOPTION_S84.md`) | — cerrado/adoptado |
| `mirova_equivalent_f_s81_b_prime_2nd_pass_gate_enabled/_disabled` (S85) | Gate intra-radio sobre second_pass_recapture | SÍ | **ADOPTADO S85** (`F_S81_B_PRIME_ADOPTION_S85.md`) | — cerrado/adoptado |
| Drifts S46 R1: `_drift1a/_1b/_1ab/_23/_23_dual/_4/_7_*/_coppola_full/_baseline_s44` | Clon literal Coppola 2016a, drift por drift | SÍ | `F28_DATA_ARCHIVE_INVENTORY` + `DATA_SUBDIRS_INVENTORY_S80`: solo combo `_drift234_only` ADOPTADO S46; atómicos REFUTADOS aislados | BAJO — todos cerrados |
| R2 S46 R2: `_r2_C1_001/_C2_3/_4/_8/_uniform_no_dual/_drift4_alone/_drift234_*_only` | Sweep C1/C2 + ablaciones dual-ROI/sensor | SÍ | `F28_INVENTORY`: REFUTADOS (drift234 con dual-ROI gana). `_r2_drift4_alone` + `_uniform_no_dual` = FALSA ALARMA "WIN" parcial (lección A "nunca decidir con n parcial") | BAJO — cerrados |
| `_d8_vent_anchored(_disabled)` / `_d8_combo_*` / `_d8_d4_per_vol` / `_h_d8_5_*` (S37-39) | Fix selección de cluster D8 | SÍ | vent_anchored + H8 + D4-per-vol ADOPTADOS; `_h_d8_5` (paper-puro) REFUTADO (Δ TP=0 en 11 vols); combo universal REFUTADO (glaciar) | BAJO — cerrados |
| `_h8_pixel_filter_*` (S35) | Filtro distancia pixel-level | SÍ | ADOPTADO (`enable_pixel_level_distance_filter: true`) | — cerrado |
| `_test1_enabled/_disabled` (S25) | Test1 integrated-ROI Villarrica sub-píxel | SÍ | ADOPTADO (`enable_test1_path: true`) | — cerrado |
| `_dual_roi_bt_enabled/_disabled` (S26) | Dual-ROI N·σ BT 5σ/10σ | SÍ | ADOPTADO (`enable_dual_roi_bt: true`) | — cerrado |
| `_p3_1_enabled/_disabled` (S24) | dNTI dual-ROI summit/scene | SÍ | ADOPTADO (`enable_dnti_dual_roi: true`) | — cerrado |
| `_no_bt_path` (S40) | bt_path OFF cleanup | SÍ | ADOPTADO crítico (borró 1453 px Salar) | — cerrado |
| `_local_kernel_bg_enabled` (S58) | kernel-bg local | SÍ | ADOPTADO S61 (per-vol opt-in) | — cerrado |
| `nsigma_mir_5` / `nsigma_mir_12` (S18 D2) | N·σ 5σ (Coppola) vs 12σ (Di Bella) vs 3σ | SÍ | `DRIFTS_S17.md` D2 RESUELTO S19: mantener 3σ. **NOTA**: el verdict descansaba en cap=7K que igualaba 5σ/12σ; el operacional post-S29 usa cap=999K (sin cap) → el A/B D2 quedó técnicamente DESACTUALIZADO respecto al cap actual | MEDIO — ver §"Sutilezas" |
| `low_vent_cap` (S22.2) | `max_vent_sigma_contrib_k` 3→2 | SÍ (efectivamente) | vent-path entero quedó OFF post-S27 (reemplazado por Test1). El A/B perdió relevancia | BAJO — obsoleto por cambio arquitectural |
| `s9_vent_permissive` (S16 E1) | `n_sigma_vent=0` restaurar recall S9 | SÍ | `SESSION_INDEX`/DRIFTS_S17: H1 sigma-gating REFUTADA (E1 no mueve recall; cuello real era NOAA-21 faltante, H10) | BAJO — cerrado |
| `mirova_equivalent_lbg_global` (S33 D4) | L_bg global anillo 5-25km Tupungatito | SÍ | Entró como `enable_test1_lbg_global` per-vol (D4); combo universal refutado | BAJO — cerrado |
| `mirova_equivalent_villarrica_test1` (S26) | Profile dedicado Villarrica Test1 | SÍ | Test1 se generalizó a operacional S26-S29; profile dedicado quedó vestigial | BAJO — obsoleto (vestigial) |
| `mirova_equivalent_test1pix_filter/_disabled` (S32 Driver B Ph1) | Intersectar mask Test1 con N·σ dual-ROI | SÍ (pero contaminado) | Adoptado con métrica BUGGY (S33), luego revertido (`enable_test1_pixel_filter: false`). `PROCESS_RULES_S33` marca milestones S27-S32 como "métricas posiblemente contaminadas, re-validar antes de citar" | MEDIO — ver §Driver B |
| `_mirova_literal` / `_coppola_full` / `_dibella_n12_viirs_only` | Paridad literal paper / Di Bella (objetivo 2) | SÍ | Referencia "paper-puro" (inflado 1000×); Di Bella refutado clon-MIROVA. Valor beyond-MIROVA para paper | BAJO — cerrados (valor doc) |
| `_s88_reproc_validation` / `_s94_reproc(_modis/_viirs)` / `_s97_refresh_viirs*` / `_s98_anchor` / `mirova_equivalent_backfill_nov2025` | Perfiles de REPROC/validación, no A/B de hipótesis | N/A | No son A/B de feature; son backfill/refresh con config operacional | N/A |
| `experimental` / `experimental_lowT` | Perfil objetivo-2 general | N/A | Sandbox, no A/B operacional | N/A |

---

## Los "colgados sin veredicto" que más valdría retomar

Ordenados por **impacto × cercanía a concluirse**:

### 1. (EN VUELO — no perder de vista) `_s99_test1_*` — recorte compacidad Test1
- **Estado**: reproc corriendo HOY (run 79221944677+ en `_ab_watch.log`), flag
  `enable_test1_spatial_core` OFF, audit `ab_test1_audit.py` pre-escrito.
- **Impacto ALTO**: es el fix candidato del 19× Tupungatito (S99 §2). NO está
  abandonado — es la tarea activa. Riesgo: que la sesión corte antes de bajar
  artifacts + correr el audit + decidir adopción (A45). **Acción**: al volver,
  descargar artifacts → `ab_test1_audit.py` → veredicto (canario FN Villarrica).

### 2. (COLGADO REAL) `mirova_equivalent_phase2` — `enable_final_pixel_filter`
- **Por qué importa**: ataca exactamente lo que S99 ataca ahora (los 14-49
  pixels marginales de Test1/path-D que inflan el ratio) pero por una vía más
  general: filtro N·σ dual-ROI sobre la mask FINAL combinada de todos los paths.
- **Por qué quedó colgado**: era "Driver B Phase 2", construido sobre Phase 1,
  y toda la línea Driver B se desacreditó cuando S33 descubrió que la métrica
  `mirovaEqVrp` con la que se "validó" Phase 1 tenía un bug. Phase 1 se revirtió
  (`enable_test1_pixel_filter: false`) pero **Phase 2 nunca se re-evaluó con la
  métrica corregida**. No hay doc de veredicto para Phase 2.
- **Acción sugerida**: antes de S99 cerrar el fix espacial, vale 1 reproc de
  control con `enable_final_pixel_filter` (métrica corregida + audit independiente
  R3) para ver si el filtro N·σ global iguala o supera al recorte espacial. Si
  el recorte espacial S99 ya cubre el caso, declarar Phase 2 REFUTADO formalmente
  y archivar el perfil (cierra un cabo suelto de 4 años de proyecto).

### 3. (PARCIAL/COLGADO técnico) D2 `nsigma_mir_5/12` desactualizado por el cap
- El verdict S19 "mantener 3σ" era correcto ENTONCES, pero descansaba en que
  el cap `MAX_SIGMA_COMPONENT_K=7K` igualaba 5σ y 12σ. El operacional **post-S29
  usa cap=999K (sin cap efectivo)** → la premisa del A/B D2 ya no se cumple.
- **Impacto MEDIO (magnitud/precisión)**: con cap retirado, 3σ vs 5σ/10σ
  podrían YA NO ser equivalentes, y 3σ uniforme no tiene respaldo de paper
  (Coppola pide 5σ summit/10σ scene). No es "idea valiosa perdida" sino una
  **conclusión que caducó al cambiar otra pieza** y nadie re-corrió el A/B.
- **Acción**: nota de bajo costo — re-correr D2 (3σ vs dual 5σ/10σ) sobre el
  pipeline actual sin cap. Posiblemente ya esté cubierto por dual-ROI BT
  adoptado S26, pero conviene confirmar que 3σ uniforme sigue justificado.

### 4. (NICE-TO-HAVE, precisión) F_S81_C — `enable_r3_zone_suppression`
- `F_S81_C_R3_NATURE_AUDIT.md` refutó la hipótesis "R3 = zonas geográficas"
  (solo 38% identificables) pero dejó "próximos pasos" (catalogar 18 clusters
  nuevos + A/B gate `enable_r3_zone_suppression`) **nunca ejecutados**.
- **Impacto BAJO**: es precisión/beyond-MIROVA (FPs lejanos), no recall ni
  magnitud del cráter. Per A55, gates intra-radio extra requieren clasificar
  primero la categoría física. Backlog legítimo, no urgencia.

## Conclusión

De ~30 perfiles A/B distintos, **solo 1 está genuinamente colgado con impacto
de magnitud** (`mirova_equivalent_phase2`/Driver B Phase 2), **1 está en vuelo
hoy** (`_s99_test1_*`, esperado), y **1 tiene un veredicto caducado** por cambio
de cap (D2 nsigma). El resto está correctamente concluido (adoptado, refutado, o
archivado con doc). El sistema de veredictos del proyecto (F28_INVENTORY +
F26_VERDICT + MIROVA_DIVERGENCES) es robusto. La sospecha de Nicolás es válida
pero acotada: el cabo suelto real es **Driver B Phase 2**, quedó huérfano cuando
el bug de métrica S33 hundió toda la línea Driver B sin re-evaluar Phase 2 — y
resulta ser la MISMA idea (filtrar pixels marginales que inflan ratio) que S99
está reimplementando por otra vía. Vale cerrarlo formalmente.
