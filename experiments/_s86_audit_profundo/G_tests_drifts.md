# Subagente G — Auditoría tests + drifts + reglas MISSION vs implementación

Fecha: 2026-05-28. Worktree raíz `VRP Chile/` (main al día, S85 cierre).

## Resumen ejecutivo

70 archivos test cubren 22 módulos de `pipeline/` (8342 LOC, 89 funciones). El core algorítmico está bien testeado y los drifts D1/D3/D6 quedaron formalmente cerrados con evidencia en S17–S21. Los gaps reales NO están en los algoritmos centrales, están en **3 áreas estructurales**: (1) `process_viirs_mod.py` (1170 LOC, cobertura ~25%) que es clon parcial de `process_viirs.py` y suele recibir fixes con delay; (2) `profile.py` (530 LOC con 80+ flags) sin ningún test que pine defaults operacionales; (3) la regla científica "MIR solo nocturno" — vinculante por contaminación solar — está implementada en `store.py:_solar_elevation` pero sin test que la cubra directamente.

Confianza en que el pipeline implementa lo declarado en `MISSION.md`: **alta para coeficientes Wooster (k=18.9/19.7/18.0 verificados), Stefan-Boltzmann TIR, kernel mean 8-vec, N·σ 5/10 summit/scene Coppola 2016a Tabla 1, Test 1 integrated (Coppola 2015) operacional**. Media-baja para gates laterales que ya están documentados como drift abierto: D7 (local ROI threshold solo en MODIS+VIIRS_M, ausente en VIIRS_I), D8 (cluster selection diverge MIROVA), D9 (path D cirrus mitigado con cap pero causa raíz arquitectural abierta).

## 1. Coverage por módulo (matriz)

| Módulo | LOC | Funciones | Tests directos | Cobertura | Gap clave |
|---|---:|---:|---:|---:|---|
| `process_modis.py` | 1163 | 6 | 9 | ~60% | `calculate_vrp` es 920 LOC; branches path A/B/C/D no aislados |
| `process_viirs.py` | 1623 | 10 | 8 | ~50% | Módulo más grande; Test1 sin unit tests dedicados |
| **`process_viirs_mod.py`** | **1170** | **6** | **2** | **~25%** | **Clon parcial de process_viirs.py, sin tests path D / Test1 M-band** |
| `store.py` | 427 | 6 | 8 | ~85% | Falta test directo de `_solar_elevation` (MIR night-only) |
| `clustering.py` | 247 | 3 | 4 | ~80% | D8 cluster selection criterion no testeado |
| `detection_context.py` | 938 | 13 | 11 | ~75% | `compute_bg_stats` retorna correcto en main (no es bug A49 reportado S79) |
| `scan_geometry.py` | 225 | 6 | 4 | ~95% | Bien |
| `audit_metrics.py` | 90 | 1 | 8 | ~90% | Bien post-S33 |
| `path_d_intra_radio.py` | 49 | 1 | 1 | ~95% | Bien (S83) |
| `path_d_cap.py` | 50 | 1 | 2 | ~95% | Bien (S71 D9) |
| `fetch.py` | 570 | 12 | 5 | ~60% | Sin test específico del retry IPv4 (H7 S35) |
| `vrp_regimes.py` | 169 | 3 | 3 | ~85% | Bien |
| `test1_integrated.py` | 188 | 2 | 4 | ~85% | Bien |
| `vrptir.py` | 177 | 5 | 4 | ~80% | Bien |
| `exclusion_zones.py` | 137 | 5 | 2 | ~85% | Bien |
| `single_pixel_mode.py` | 138 | 2 | 1 | ~75% | Cubierto |
| `second_pass_intra_radio.py` | 72 | 1 | 1 | ~90% | Bien (S85) |
| **`profile.py`** | **530** | **2** | **0** | **0%** | **80+ flags sin test invariantes** |
| `constants.py` | 26 | 0 | 0 | n/a | Solo Planck — no requiere |
| `geo_utils.py` | 35 | 1 | 1 | ~95% | Bien |
| `detect_tirvolch.py` | 318 | 3 | 1 | ~70% | Experimental |

## 2. Estado de drifts D1–D9

| ID | Concepto | Estado | Test | Verificación main |
|---|---|---|---|---|
| D1 | kernel 8-vec median vs mean | ✅ RESUELTO S17 | `test_detection_context::kernel_uses_arithmetic_mean_not_median` | `detection_context.py:191 np.mean` confirmado |
| D2 | `N_SIGMA=3.0` uniforme | ✅ RESUELTO ESTRUCTURAL — defaults ahora `SUMMIT=5.0 / SCENE=10.0` (`profile.py:187-188`) | `test_drift23_first_pass_tests_2_3` | OK |
| D3 | VRP TIR Stefan-Boltzmann vs Aveni Eq.9 | ✅ RESUELTO S17 (mantener SB) | `test_vrptir_f31`, `test_vrp_tir_consistency_gate_f46` | OK |
| D4 | feature parity escala Low/.../Extreme | Recall sub-pixel CERRADO S27 vía Test1; escala visual abierta | `test_test1_integrated` cubre rescate | OK |
| D5 | magnitud ratio VRP | RE-ABIERTO S33 post-bug `mirovaEqVrp`; ratio Driver A solo 2.53× tolerable | `test_audit_metrics`, `test_r2_pixel_level` | OK |
| D6 | background no localizado | ❌ REFUTADO S21 | `test_local_kernel_background` | OK |
| D7 | local ROI threshold solo MODIS+VIIRS_M | ⚠️ ABIERTO desde S23, decisión diferida | `test_local_roi_paridad` (solo alerta) | `process_viirs.py` NO tiene; los otros 2 sí |
| D8 | cluster selection diverge MIROVA | ⚠️ ABIERTO S35; F47 cluster_rescue mitigó schema, no criterio | `test_d8_vent_anchored`, `test_d8_h_d8_5`, `test_store_cluster_rescue_f47` | `clustering.py` sigue eligiendo por vrp_mw/n_pixels |
| D9 | path D dispara FPs en cirrus | PARCIAL — cap 5MW @ t_bg<270K activo S71; causa raíz arquitectural ABIERTA | `test_path_d_d9_fix` (20 tests sintéticos), `test_path_d_scene_cap_f50` | Cap activo; ratios post-cap siguen 24–83× en cirrus |

## 3. Matriz reglas MISSION × implementación × test

| Regla científica (MISSION.md / CLAUDE.md) | Implementación | Test | Flag riesgo | Estado |
|---|---|---|---|---|
| Wooster MODIS k=18.9 | `process_modis.py:56` | `test_coefficients` | — | OK |
| Wooster VIIRS_M k=19.7 | `process_viirs_mod.py:47` | `test_coefficients` | — | OK |
| Wooster VIIRS_I k=18.0 | `process_viirs.py:54` | `test_coefficients` | — | OK |
| A_pix nadir fijo | `scan_geometry.modis_pixel_areas(nadir_fixed=...)` | `test_drift7_nadir_fixed_pixel` | `ENABLE_NADIR_FIXED_PIXEL_AREA_MODIS/VIIRS` (default ON en operacional) | OK con flag — sin test E2E que pine valor en mirova_equivalent |
| MIR solo nocturno | `store.py:_solar_elevation` line 378–385 | **NINGUNO directo** | — | **RIESGO BAJO-MEDIO** |
| Kernel arithmetic mean 8-vec | `detection_context.py:191` | `test_detection_context` | — | OK |
| VRP TIR Stefan-Boltzmann | `process_viirs.py SIGMA=5.67e-8` | `test_vrptir_f31` | `enable_vrp_tir_provisional_gate_s81` (alternativo, no operacional) | OK |
| 5σ summit / 10σ scene (Coppola 2016a Tabla 1) | `profile.py:187-188` | `test_drift23_first_pass_tests_2_3` | yaml puede override | OK estructural |
| Test 1 integrated (Coppola 2015 Eq.1) | `test1_integrated.py` + paths VIIRS_I/_M | `test_test1_integrated` + 3 más | `enable_test1_path` ON operacional | OK |
| Path D dNTI ctx 8-vec | `detection_context.contextual_dnti_hot_mask` (centralizado, llamado por los 3 procesadores) | `test_viirs_path_d`, `test_path_d_d9_fix` | `enable_dnti_contextual_path` ON + cap D9 | OK con cap |
| MIROVA sin cloud mask BT<260K (Laiolo 2026) | Ausente en código | n/a | — | OK literal |

## 4. Path D deep dive

**Consistencia cross-sensor**: OK. Los 3 procesadores (`process_modis.py:437,448`, `process_viirs.py:765,776`, `process_viirs_mod.py:510,521`) llaman a `contextual_dnti_hot_mask` y `dual_roi_contextual_dnti_hot_mask` centralizados en `detection_context.py`. No hay drift de implementación cross-sensor.

**Protección A23 (cirrus t_bg<260K)**: implementada como **cap defensivo Opción C** (`path_d_only_cap_mw=5.0` @ `path_d_only_cap_tbg_max_k=270.0`, profile mirova_equivalent). NO bloquea path D firing — solo limita magnitud cuando firing es contextual-only y t_bg está bajo. Causa raíz arquitectural **ABIERTA**: Subagente B reportó que 82.5% de records publishable activan solo path D, y Subagente C confirmó 184 FPs / 0 TPs en cirrus. El cap mitiga la magnitud pero no la frecuencia de firing.

**`apply_f66_consistency_gate` (commit `a73775cd`)**: NO mergeada a main. Grep `apply_f66_consistency_gate` en `pipeline/` → 0 hits. `compute_bg_stats` en main retorna correctamente (`detection_context.py:938 return t_bg, std_bg, n_bg`) — la regresión A49 reportada S80 quedó en la rama F66 huérfana, no llegó a operacional.

## 5. Tests schema-regresión (A46)

Cobertura parcial:
- `pc.vrp_mw` cap → `test_sanity_cap_pc`.
- `pc.centroid_dist_km` para mirovaEqVrp → `test_audit_metrics`.
- `final_hotspot_source='cluster_rescue'` → `test_store_cluster_rescue_f47` (F47 H4 explícito).

**Sin cobertura**: ningún test verifica programáticamente que `t_bg_k` esté presente en todo record con cluster, ni que los gates downstream que evalúan `hotspot_*` single y `primary_cluster.*` arrojen veredictos coherentes (riesgo F47-style latente, regla A46).

## 6. Tres riesgos no documentados (top)

### R1 — `process_viirs_mod.py` clon parcial con cobertura ~25%

`process_viirs_mod.py` (1170 LOC, 6 funciones) es copy-paste-derived de `process_viirs.py` con 2 tests directos (`test_coefficients`, `test_d4_per_volcano`). Comparte ~80% de la lógica de paths A/B/C/D, Test1, sanity cap. Patrón histórico: Test1 se agregó S28 a M-band después de S27 en I-band — el delay creó ventana de drift. Cualquier fix S86+ en process_viirs.py (ej. fix D9 path D arquitectural) puede no propagarse sin auditoría manual. Mitigación: refactor a base class compartida o cross-file diff pre-PR obligatorio.

### R2 — `profile.py` (530 LOC, 80+ flags) sin test invariantes

`profile.py` define defaults críticos: `N_SIGMA_MIR_SUMMIT=5.0`, `PATH_D_ONLY_CAP_MW=5.0`, `ENABLE_DNTI_CONTEXTUAL_PATH`, `ENABLE_TEST1_PATH`, `ENABLE_NADIR_FIXED_PIXEL_AREA_*`. Un cambio de default operacional (intencional o accidental) pasa sin alerta hasta que un reproc divergente lo expone. Mitigación: `tests/test_profile_operational_invariants.py` que pin defaults declarados en MISSION.md/CLAUDE.md.

### R3 — MIR night-only gate sin test directo

La regla "MIR solo nocturno" (contaminación solar diurna) está implementada en `store.py:_solar_elevation` (cálculo SPA simplificado) y aplicada como safety net en `store.append_record` (línea 378–385). Ningún test verifica: que records day son rechazados, que la función solar produce ángulos correctos vs ephemeris de referencia, ni que el threshold de elevación está en valor correcto. Si la función solar drift silenciosamente, contamina records con radiación solar — fuente histórica de drifts de magnitud (parche P5 retirado S27). Mitigación: `test_store_solar_night_gate.py` con 4 casos (noche clara accept, día reject, twilight transición, polar edge).

### R4 (bonus) — D7 abierto desde S23

VIIRS_I (sensor crítico para sub-pixel summit donde Test1 captura el 82.5% del recall Lastarria/Villarrica/Chaitén) NO aplica el filtro local p95 que MODIS y VIIRS_M sí aplican (`process_modis.py:285-288`, `process_viirs_mod.py:309-312`). Es candidato sospechoso al patrón "82.5% records publishable activan path D solo" que Subagente B reportó — la cola difusa que el filtro local recortaría en M-band entra al cluster en I-band sin gate.

### R5 (bonus) — D8 cluster selection MIROVA

`clustering.py` sigue eligiendo `primary_cluster` por `vrp_mw` desc o `n_pixels` desc (línea 99–101). Caso Puyehue lacolito S35 confirmó que MIROVA usa otro criterio (probable: proximidad al vent o anomaly score relativo). F47 cluster_rescue mitigó el schema asimétrico que generaba records con vrp=0 cerca del vent, pero el criterio de selección sigue divergente. Latente en los 11 Tier A con doble centro térmico (Tupungatito glaciar+cráter, PCC lacolito+cráter, Planchón complejo multi-cráter).

## Artifacts

- `experiments/_s86_audit_profundo/G_tests_drifts.md` (este reporte).
- `experiments/_s86_audit_profundo/G_tests_drifts.json` (estructurado).

## Confianza global MISSION.md → código

**Alta para core**: coeficientes Wooster, Stefan-Boltzmann TIR, kernel mean, N·σ 5/10 Coppola 2016a, Test1 integrated, path D centralizado cross-sensor. **Media-baja para gates laterales abiertos**: D7 (I-band sin local ROI), D8 (cluster selection), D9 (cirrus mitigado vía cap, causa raíz abierta). Los riesgos top NO son del algoritmo Coppola implementado — son de **estructura del repo**: clon poco testeado (R1), config sin invariantes (R2), regla científica sin test (R3).
