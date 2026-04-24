# Session Index VRP Chile

> Resumen 1-2 líneas por sesión con hallazgo principal. Mantener cronológicamente.

| S# | Fecha | Hallazgo principal | Artefacto |
|---|---|---|---|
| S1-S8 | 2026-01 a 2026-03 | Bootstrapping pipeline: fetch VIIRS+MODIS, estructura YAML volcanes, NTI path + vent path simple, 11 volcanes Tier A | `pipeline/` inicial |
| S9 | 2026-03 | Vent-path con threshold fijo 1K (no sigma-gating): recall alto Tupungatito 0.977, Chaitén 0.929. FPs no-filtrados | commit `ecb5d66` |
| S10 | 2026-03 | `ENABLE_VENT_PATH_MODIS=false` para bajar 21% FPs en Lascar — causó regresión MODIS 0.83→0.058 | commit `56a1318` |
| S11 | 2026-04 | Path C NTI relativo en experimental | commit `2ee346e` |
| S12 | 2026-04-12 a 2026-04-16 | **Sigma-gating vent-path** `max(1K, 2σ)` → "elimina 85% FPs" pero mata TPs sub-pixel (Tupungatito 0.977→0.5, Chaitén 0.929→0.5). Matrix 45 volcanes, NRT cron 2h | commits `6eaed67` (F1), `4c80429` (F1b cap 3K), `39e6bb0` (pisos VRP) |
| S13 | 2026-04-17 | Plan integrated-ROI para Villarrica sub-pixel | `tasks/plan_s13_test1_integrated_roi.md` |
| S14 | 2026-04-18 a 2026-04-20 | Fix geometría MIROVA-equivalent: `radius_km=25` uniforme, `inner_radius_km` per-volcán de KML oficial. Schema unificado `final_hotspot_*`. **Validación empírica coeficientes Wooster** contra OSF v2.5: error ≤0.17% en 48,360 filas. Coeffs: MODIS=18.9, VIIRS M=19.7, VIIRS I=18.0 | `experiments/21_results.json`, commit `5478bce` |
| S15 | 2026-04-21 a 2026-04-22 | **4 fixes arquitecturales**: (P3.2) dNTI contextual 8-vecinos Path D; (P3.1) dual-ROI thresholds summit/scene; (Tema E) bbox 50×50 km reemplaza círculo; (Tema F) sigma-cap eruption-path VIIRS=7K. Reproceso background pendiente validación. **NO pusheado a main** | `tasks/handoff_mananero_2026_04_22.md` |
| S16 | 2026-04-23 (primera mitad) | Diagnóstico H1 con `git show 6eaed67` confirmado: commit S12 F1 causó regresión. Profile `s9_vent_permissive` creado con `n_sigma_vent=0`. **Bug bbox: Salar de Atacama (Lascar) y Embalse El Yeso (Tupungatito) capturados** como FPs 200-1500 MW. **P3.6 exclusion zones** implementado en `pipeline/exclusion_zones.py` + `volcanoes.yaml`. Reproceso E1+P3.6 pendiente | commits `d461f4a`, `6f87989`, handoff `tasks/handoff_s17_2026_04_23.md` |
| **S17** | **2026-04-23 (segunda mitad)** | **Investigación sistemática con 4 skills invocadas + 11 agentes paralelos**. Hallazgos: **(1) fix performance Path D factor 2400×** (commit `ad030f5`); **(2) H1 sigma-gating REFUTADA** — E1 no mueve recall; **(3) H10 CONFIRMADA — NOAA-21 missing en fetch.py** es el cuello real; **(4) 3 drifts detectados en código vs papers**: median→mean, N·σ=3→5-10-15, TIR Stefan vs Aveni. **Auditoría 10 papers** Coppola/Campus/Wooster/Di Bella/Aveni consolidada. **Arquitectura de memoria instalada**: docs/DRIFTS, PAPERS_AUDIT, DATA_SOURCES, HYPOTHESIS_LOG, SESSION_INDEX | docs/ completo + commit `ad030f5` |
| **S18** | **2026-04-24** | **H10 IMPLEMENTADA y VALIDADA empíricamente**. (1) **Integración NOAA-21** (VJ202IMG/VJ203IMG/VJ202MOD/VJ203MOD v2.1) en fetch.py + sensor labels en process_viirs*.py + piso store.py + dispatch run_pipeline.py. 15 tests TDD nuevos (65/65 verde). (2) **Reproceso 3 volcanes Tier A** ventana 2026-04-08→04-22 (local paralelo, 45-75 min). (3) **Recall H10 validado contra MIROVA NRT**: Lascar 0.52→**0.86** (+14 TP), Chaitén 0.50→**1.00** (+1 TP), Tupungatito 0.24→**0.41** (+3 TP). H10 confirmada — NOAA-21 agrega TPs reales. Tupungatito queda bajo 0.77 del handoff → **H17 nueva** (Embalse El Yeso / σ_bg) para S19. (4) **Dashboard refactor mayor** a pedido del geólogo: fix FP 1.5M MW Lastarria (granule MODIS dañado, 357 pixels BT=566K), archivo histórico de 34 no-Tier-A a `data/archive/` + 12 `_OLD_*` via `git mv` (preserva historia git), filtro a 11 Tier A + 45 cards con "Sin datos", conteos 🎯/📍 7d, toggle "Solo cráter / Incluir lejanas" (default cráter), tabla con columna Zona + atenuación filas far, 3 radios sincronizados con YAML (25 km + inner_radius_km 3-20 km + vent_radius_km 2-5 km), fix distanceCounts con fallback vrp_vent>0. (5) Infraestructura A/B drift D2 instalada (profiles nsigma_mir_5/12 + experiments/37) pero ejecución diferida S19. (6) Merge `s15-dev→main` con 68 conflictos resueltos (34 UD no-Tier-A archivados, 34 UU experimental accept HEAD, 7 UU Tier A: 3 reproceso / 4 NRT) | commits pipeline `b08b71f`, reproceso `80bc302`, merge `f78ad5d`. Dashboard: `cd8e8e5`/`a0d6053`/`15f6849`/`9501d58`/`397b55f`/`47b9fd1` |

---

## Glosario de sesiones (convenciones)

- **Sesión** = un bloque de trabajo focused Claude Code + Nicolás, con handoff al final.
- **Numeración**: S1 = bootstrapping; S17 = 2026-04-23 PM.
- **Handoff**: archivo en `tasks/handoff_s##_YYYY_MM_DD.md` que resume estado al cierre.

---

## Próximas sesiones planeadas

### S18 — Fix drifts + NOAA-21
- Corregir D1 (mean vs median) en `detection_context.py` con TDD.
- Agregar NOAA-21 a `fetch.py` + `process_viirs.py` + `process_viirs_mod.py` con TDD.
- Reproceso 3 volcanes Tier A (Tupungatito, Chaitén, Lascar) con pipeline ampliado.
- Test A/B para drift D2 (N·σ): 3 configs vs OSF v2.5.
- Si valida → push main.
- Auditar Coppola 2022 Sabancaya (s00445-022-01523-1.pdf).

### S19 — TIR + parity dashboard
- Auditar Aveni 2024 TIRVolcH RSE → resolver drift D3.
- Feature parity dashboard: Combined MIR series + escala alerta.
- `tests/regression/` con snapshots dorados OSF v2.5.

### S20+ — SWIR + preflight
- SWIR pipeline Massimetti 2020 (Sentinel-2 MSI + Landsat-8/9 OLI) — scope grande.
- `scripts/preflight_cmr_coverage.py` — chequeo CMR antes de afirmar "sin data".
