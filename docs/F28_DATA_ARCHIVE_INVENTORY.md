# Data/_*/ Inventory — S73 cleanup analysis

> Inventario clasificatorio de los 41 subdirectorios A/B históricos bajo `data/_*/`
> (~647 MB total medido con `du -sh`). Generado S73 antes de decidir cleanup.
> **NO destructivo — solo análisis.** Cada row está respaldado por (a) el header
> del profile YAML en `pipeline/profiles/<subdir>.yaml`, (b) handoffs
> `tasks/handoff_s*` / `tasks/BLOQUE_ARRANQUE_S*.md`, y (c) docs verdict:
> `docs/F26_VERDICT_CONSOLIDATED_S72.md`, `docs/MIROVA_DIVERGENCES.md`,
> `docs/HYPOTHESIS_LOG.md`.

## Convenciones

- **Verdict**:
  - **ADOPTADO**: feature mergeada a `mirova_equivalent.yaml` operacional
    (verificable con `grep enable_ pipeline/profiles/mirova_equivalent.yaml`).
  - **REFUTADO**: A/B mostró no aporta (Δrecall/F1 ≤ 0 o regresión).
  - **FALSA ALARMA**: bug auditoría / data stale descubierto después.
  - **INCONCLUYENTE**: n bajo o experimento truncado.
  - **CONTROL**: era el control (baseline) de un A/B — no contiene treatment.
- **Valor beyond-MIROVA**: ALTO = aporta a paper de extensiones futuras
  (objetivo 2); MEDIO = referencia histórica de drift; BAJO = ya reemplazado
  por feature en main; N/A = control puro.
- **Recomendación archivar**: SÍ-safe = controles, treatments REFUTADOS ya
  superados, baselines ya replicados por main; EVALUAR = valor para paper
  o caso ambiguo; NO = aún activo o única referencia retro-comparativa.

## Resumen ejecutivo

- Total subdirs: **41** (~647 MB en disco).
- **SÍ-safe archivar**: 27 subdirs (~390 MB) — controles A/B emparejados,
  treatments REFUTADOS Ronda 2 S46, paths viejos sustituidos.
- **EVALUAR con Nicolás**: 11 subdirs (~190 MB) — drifts atómicos S46 ronda 1
  (drift1a, drift1b, drift23, drift7_modis_only, drift7_viirs_only,
  dibella_n12, coppola_full), `_mirova_literal`, `_no_bt_path`, `_baseline_s44`,
  `_drift234_only`. Valor potencial para paper "beyond-MIROVA".
- **NO archivar**: 3 subdirs (~70 MB) — referencias estructurales aún citadas
  en docs F2.6 (validan deriva S26→S71): `_mirova_literal`, `_baseline_s44`,
  `_drift234_only`.

## Tabla por subdir

| Subdir | MB | Sesión | A/B testeaba | Verdict | Valor beyond-MIROVA | Recomendación |
|---|---|---|---|---|---|---|
| `_baseline_s44` | 28 | S46 R1 | Control idéntico a operacional S44 (pre-Coppola literal). Todos los drifts S46 OFF | CONTROL para R1 (referencia pre-drift234) | MEDIO — snapshot canonical "estado pre-Coppola-literal" | EVALUAR (citado F2.6 como referencia retro; reemplazable por checkout a SHA pre-S46) |
| `_coppola_full` | 15 | S46 R1 | Clon literal Coppola 2016a completo (drift #1ab + #234 dual + #7 both) | REFUTADO vs `_drift234_only` (handoff_s47 §3 "ninguna variante mejora") — drift #7 nadir-fijo perdía edge granules; drift #1ab demasiado estricto | ALTO — paper extension: muestra que "paper-puro" es subóptimo vs MIROVA-NRT real | EVALUAR |
| `_d8_combo_disabled` | 13 | S38 | Control para `_d8_combo_full` (D8+D4+H8 OFF) | CONTROL | N/A | SÍ-safe |
| `_d8_combo_full` | 13 | S38 | D8 vent_anchored + H8 + D4 lbg_global UNIVERSAL | REFUTADO universal (handoff_s40: regresión Tupungatito/Planchón por glaciar frío). Reemplazado por per-vol S39 | BAJO — features ya replicadas (vent_anchored, H8 en main; D4 per-vol gano) | SÍ-safe |
| `_d8_d4_per_vol` | 13 | S39 | D8 + H8 + D4 per-vol (Lascar, Lastarria, NdC en volcanoes.yaml) | ADOPTADO (operacional `enable_test1_lbg_global: true`, gated por per-vol field) | BAJO — ya en main | SÍ-safe |
| `_d8_vent_anchored` | 26 | S38 | vent-anchored clustering + H8 pixel-level filter (verdadero fix D8 selection) | ADOPTADO (operacional `enable_vent_anchored_clustering: true` + `enable_pixel_level_distance_filter: true`) | BAJO — ya en main | SÍ-safe |
| `_d8_vent_anchored_disabled` | 12 | S38 | Control para `_d8_vent_anchored` | CONTROL | N/A | SÍ-safe |
| `_dibella_n12_viirs_only` | 19 | S46 R1 | Di Bella 2024 n=12 noche VIIRS (NO clon MIROVA, INGV Catania) | REFUTADO clon-MIROVA (regla S26 NO MIROVA); pierde ALERTAs legítimas vs C2=5/10 | ALTO — paper beyond-MIROVA: compara régimen alternative-italian-school | EVALUAR |
| `_drift1a_only` | 28 | S46 R1 | Drift #1a aislado: Test 1 K1 retire from hot_mask (Coppola 2016a SP426.5:298) | REFUTADO aislado (no mejora vs control; mejora solo en combo drift234) | MEDIO — referencia de drift atómico | EVALUAR |
| `_drift1ab_only` | 28 | S46 R1 | Drift #1 completo (1a retire + 1b bg exclude) | REFUTADO aislado (handoff_s47 §3 "ronda 2 nada mejora") | MEDIO | EVALUAR |
| `_drift1b_only` | 28 | S46 R1 | Drift #1b aislado: bg_stats exclude active pixels | REFUTADO aislado | MEDIO | EVALUAR |
| `_drift234_only` | 15 | S46 R1 | Combo drifts #2+#3+#4 con dual-ROI Tabla 2 (first_pass Tests 2 ∧ 3 + second_pass) | **ADOPTADO** (operacional: `enable_first_pass_tests_2_and_3`, `enable_dual_roi_first_pass`, `enable_second_pass_adjacent`, `enable_dual_roi_second_pass`). F1 89.2% → 89.9%, MODIS recall 92.3% → 100% | BAJO — ya en main | NO (referencia retro canonical "punto de adopción S46") |
| `_drift23_dual_only` | 12 | S46 R1 | Drift #2+#3 con dual-ROI Tabla 2 sin second-pass | REFUTADO (R2 mostró drift234 con second-pass es óptimo) | MEDIO | SÍ-safe |
| `_drift23_only` | 19 | S46 R1 | Drift #2+#3 uniforme (sin dual-ROI, set summit toda ROI) | REFUTADO (R2 dual-ROI gana) | MEDIO | SÍ-safe |
| `_drift4_only` | 23 | S46 R1 | Drift #4 aislado (second-pass; requiere first_pass ON por arquitectura) | REFUTADO aislado vs combo drift234 | MEDIO | SÍ-safe |
| `_drift7_both_only` | 28 | S46 R1 | Drift #7 completo MODIS+VIIRS A_pix nadir-fijo | REFUTADO (handoff_s47 §3) — paper-puro pierde edge granules | ALTO — paper beyond: A_pix nadir vs scan-angle es decisión arquitectural defendible | EVALUAR |
| `_drift7_modis_only` | 27 | S46 R1 | Drift #7 MODIS aislado (A_pix=1 km² uniforme) | REFUTADO aislado | ALTO — paper beyond: documenta decisión sec³ vs nadir MODIS | EVALUAR |
| `_drift7_viirs_only` | 27 | S46 R1 | Drift #7 VIIRS aislado (A_pix nadir I=0.140625, M=0.5625 km²) | REFUTADO aislado | ALTO — paper beyond: documenta decisión VIIRS factor lineal vs nadir | EVALUAR |
| `_dual_roi_bt_disabled` | 4 | S26 | Control para `_dual_roi_bt_enabled` (mirror operacional pre-dual-ROI BT) | CONTROL | N/A | SÍ-safe |
| `_dual_roi_bt_enabled` | 4 | S26 | mirova_equivalent + dual-ROI N·σ BT (5σ summit, 10σ scene Coppola 2016a Tabla 1) | ADOPTADO (operacional `enable_dual_roi_bt: true`) | BAJO — ya en main | SÍ-safe |
| `_h8_pixel_filter_disabled` | 8 | S35 | Control para `_h8_pixel_filter_enabled` | CONTROL | N/A | SÍ-safe |
| `_h8_pixel_filter_enabled` | 6 | S35 | Bug fix H8 — pixel-level distance filter (reach 13.7% records Tier A 30d) | ADOPTADO (operacional `enable_pixel_level_distance_filter: true`) | BAJO — ya en main | SÍ-safe |
| `_h_d8_5_disabled` | 13 | S37 | Control para `_h_d8_5_full` | CONTROL | N/A | SÍ-safe |
| `_h_d8_5_full` | 13 | S37 | D8 cluster fix vía paper-puro: ETI quadratic + second-pass + sum_vrp | **REFUTADO** A/B 22/22 success negativo (handoff_s38: Δ TP = 0 en TODOS los 11 vols). Bug D8 era de selection, no detección — fix correcto S38 vent_anchored | MEDIO — documenta que "paper-puro detección" no era el problema | SÍ-safe |
| `_local_kernel_bg_enabled` | 20 | S58 | enable_local_kernel_bg=true global vs operacional | ADOPTADO S61+ (operacional `enable_local_kernel_bg: true`, per-vol opt-in en volcanoes.yaml) | BAJO — ya en main | SÍ-safe |
| `_mirova_legacy` | 4 | S27 | Control mirror operacional pre-`_mirova_literal` | CONTROL (marcado borrable en HANDOFF_S28_MORNING.md, nunca borrado) | N/A | SÍ-safe |
| `_mirova_literal` | 78 | S27 | Clon literal MIROVA paper-puro (cap=999K, vent-path OFF, cloud_mask=0, dual-ROI BT, dNTI dual, Test 1 ROI ON, exclude_zones OFF) | ADOPTADO casi todo a operacional vía S27-S29-S46. Magnitudes inflación 1000× vs MIROVA-NRT documentadas F2.6.h (sin filtros S38-S40 era pseudo-paper) | ALTO — referencia canonical "paper Coppola 2016a literal" para paper beyond | NO (citado F2.6 verdict + es el snapshot mayor "paper literal" 78 MB pesa pero valor histórico claro) |
| `_no_bt_path` | 13 | S40 | bt_path_hot OFF — cleanup paths viejos post vent_anchored+D4 | **ADOPTADO crítico** (operacional `enable_bt_path_hot: false`). F2.6 validó: S40 borró 1453 BT pixels Salar Atacama, mediana 1910× inflación eliminada | ALTO — paper beyond: caso paradigmático "feature paper-puro era load para FPs regionales" | EVALUAR (caso de estudio retro F2.6) |
| `_p3_1_disabled` | 16 | S24 | Control para `_p3_1_enabled` (dnti dual-ROI OFF) | CONTROL | N/A | SÍ-safe |
| `_p3_1_enabled` | 12 | S24 | dnti dual-ROI thresholds summit/scene (Coppola 2016a Table 2) | ADOPTADO (operacional `enable_dnti_dual_roi: true`) | BAJO — ya en main | SÍ-safe |
| `_r2_C1_001_summit` | 18 | S46 R2 | Override C1=0.001 summit (más sensible) | REFUTADO (handoff_s47 §3 ninguna variante R2 mejora vs drift234) | MEDIO — sensitivity sweep histórico | SÍ-safe |
| `_r2_C2_3_summit` | 16 | S46 R2 | Override C2=3 summit (más sensible) | REFUTADO | MEDIO | SÍ-safe |
| `_r2_C2_4_summit` | 15 | S46 R2 | Override C2=4 summit | REFUTADO | MEDIO | SÍ-safe |
| `_r2_C2_8_summit` | 15 | S46 R2 | Override C2=8 summit (más estricto) | REFUTADO | MEDIO | SÍ-safe |
| `_r2_baseline_drift234` | 15 | S46 R2 | Control idéntico a drift234 ronda 2 | CONTROL | N/A | SÍ-safe |
| `_r2_drift234_modis_only` | 9 | S46 R2 | drift234 solo MODIS, VIIRS desactivado | REFUTADO (pierde VIIRS detections) | MEDIO | SÍ-safe |
| `_r2_drift234_viirs_only` | 6 | S46 R2 | drift234 solo VIIRS, MODIS desactivado | REFUTADO (pierde MODIS recall 100%) | MEDIO | SÍ-safe |
| `_r2_drift4_alone` | 15 | S46 R2 | second-pass sin first-pass tests 2&3 | FALSA ALARMA "WIN" — preview con n parcial 8-9/11 vol mostraba +1.2pp F1, final 11/11 colapsó a +0.0 (handoff_s47 §4 "regla NUNCA decidir con data parcial") | MEDIO — caso histórico anti-pattern A/B parcial | SÍ-safe |
| `_r2_uniform_no_dual` | 15 | S46 R2 | drift234 sin dual-ROI Tabla 2 (uniform thresholds) | FALSA ALARMA "WIN" — preview 91.1% colapsó a 89.9% en 11/11. Refuta paramétricamente "MIROVA sin dual-ROI" | MEDIO | SÍ-safe |
| `_test1_disabled` | 11 | S25 | Control para `_test1_enabled` (Test 1 OFF, mirror operacional pre-S25) | CONTROL | N/A | SÍ-safe |
| `_test1_enabled` | 12 | S25 | Test 1 integrated-ROI MIR Coppola 2015 §2.2 Eq.1 (validación 6/6 ALERTAs Villarrica sub-pixel) | ADOPTADO (operacional `enable_test1_path: true`) | BAJO — ya en main | SÍ-safe |

## Notas de interpretación

### "REFUTADO aislado" vs "ADOPTADO en combo" (S46 Ronda 1)

Los drifts atómicos `_drift1a_only`, `_drift1b_only`, `_drift1ab_only`,
`_drift23_only`, `_drift23_dual_only`, `_drift4_only`, `_drift7_*_only`
fueron REFUTADOS individualmente porque ninguno mejoraba vs `_baseline_s44`
sin acompañar con el combo `_drift234`. El operacional S46 adoptó **solo** la
combinación `_drift234_only` (Tests 2∧3 + dual-ROI Tabla 2 + second-pass), NO
los drifts atómicos (#1ab, #7). Esto es contraintuitivo desde "paper-literal"
y es **exactamente el insight beyond-MIROVA** que un paper futuro debería
documentar: MIROVA-NRT real es más permisivo que paper publicado.

### Por qué `_mirova_literal` (78 MB) NO debe archivarse aún

- Es la única referencia canonical "paper-puro Coppola 2016a + 2020"
  conservada en data form.
- F2.6.h verificó que sus magnitudes están **infladas 1000× sobre MIROVA-NRT**
  para los mismos eventos ALERTA — esto es **citado actualmente** en
  `docs/F26_VERDICT_CONSOLIDATED_S72.md` como evidencia retroactiva de que
  S38-S40 corrigieron correctamente.
- 78 MB en un repo de 696 MB total es 11% pero la pérdida cognitiva
  archivándolo es alta.

### Por qué `_baseline_s44` y `_drift234_only` están en NO

- Son los dos snapshots que documentan el "antes/después" del paso S46 hacia
  Coppola literal en filtros.
- Reconstruirlos requeriría re-correr S46 ronda 1 (143 jobs Actions, ~3h).

### Falsas alarmas históricas (lección S47)

`_r2_drift4_alone` y `_r2_uniform_no_dual` ambos mostraron preview "WIN +1.2pp F1"
con n=8-9/11 vols, colapsando a 0.0 al completar 11/11. La regla S47+
"NUNCA decidir adopción con data parcial" nació de estos dos casos. Pueden
archivarse safe porque la lección ya está canonicalizada en
`tasks/handoff_s47_2026_05_16.md` §4 y CLAUDE.md aprendizajes.

## Acción sugerida para S73

1. **No tocar** los 3 subdirs `NO`: `_mirova_literal`, `_baseline_s44`,
   `_drift234_only` (~121 MB).
2. **Discutir con Nicolás** los 11 `EVALUAR` (~190 MB) — todos tienen valor
   ALTO o MEDIO-ALTO para un paper beyond-MIROVA. Decisión recomendada:
   conservar mientras el paper esté en backlog activo (S73 backlog P5).
3. **Archivar SÍ-safe** los 27 restantes (~390 MB) tras backup local:
   - Tag git anotado `pre-s73-data-cleanup` apuntando al SHA actual.
   - `git rm -r data/_<subdir>/` por cada uno (no destructivo: recuperable
     via tag).
   - Commit individual o agrupado por categoría (controles, R2, etc.).
