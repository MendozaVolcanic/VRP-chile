# Bloque arranque S79 — VRP Chile (post cierre S78 final 2026-05-25)

> Continuación tras cierre S78 ampliado (Mirova-v1 parity + brainstorm
> 7-mecanismos lagos persistentes). **65 PRs S76+S77+S78 mergeados**.
> Tests 507 passing, 24 skipped, 0 regresión.

## ⚡ Primer comando (LEER PRIMERO)

```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP-Chile-s70"
git fetch origin --prune
git pull --ff-only  # (rama work-* o crear nueva desde origin/main)
ls tasks/BLOQUE_ARRANQUE_S*.md | tail -1   # debe ser S79.md
python -m pytest tests/ -q --tb=no  # baseline 507 passed
```

## 1. Estado al cierre S78 ampliado

### Sprint Mirova-v1 parity (S78)

| PR | Feature | Estado |
|---|---|---|
| #201 | `docs/MIROVA_V1_PARITY_PROPOSAL_S77.md` | ✅ doc plan |
| #202 | F1 mosaico panorámico `frontend/mosaico.html` | ✅ mergeado |
| #203 | F2 bandas MIROVA + F5 tags región | ✅ mergeado |

### Brainstorm 7-mecanismos (S78, **clave para entender lagos**)

| # | Mecanismo | Status final | Razón |
|---|---|---|---|
| F60 VSROI per-volcán | Postponed S79+ | Útil pero secundario |
| **F61 NTI gate -0.85** | ❌ **INVALIDADO** (PR #208 +#213) | F64 demostró que destruye 98% TPs por física Planck. K1 paper es saturación bg, NO gate detección |
| F62 Test 1 K_sigma | ✅ Paper-literal OK (PR #210) | No bug |
| **F63 Cluster ranking S43** | ❌ **Rechazado post-TDD** (PR #215) | Trade-off legítimo Tup/Last/PP vs Copahue indistinguible sin metadata |
| F64 NTI método vs ours | ✅ Sin drift (PR #213) | Coppola 2016a verbatim |
| F65 5-10 approaches alt | ✅ Top 3 docs (PR #212) | Approach 5 viable, Approach 4 TIRVolcH definitivo |
| **F66 BG kernel local 3×3** | 🎯 **BUG RAÍZ identificado** (PR #214) | `compute_bg_stats` ring 5-25 km vs MIROVA kernel local 3×3. **Plan S79 P1** |

Lectura crítica antes de tocar nada: `docs/F66_BG_KERNEL_LOCAL_DEEP_S78.md`.

### Fixes pipeline críticos con A45 (acumulados S76+S77+S78)

| Fix | PR | Sha | Resultado |
|---|---|---|---|
| F46 vrp_tir_mw Stefan-Boltzmann | #177 | a80807f0 | 143 records VIIRS I-band corregidos |
| F47 cluster rescate | #175 | 34b74f20 | ~400 records recuperados |
| F47 follow-up distance_class summit | #181 | 899a4b8d | Hace visibles los rescatados en UI |
| F49 sync MIROVA CSV + freshness CI | #187 | c75387fd | MIROVA fresh +3 750 records |
| F50 cap D9 vrp_mw scene-wide | #188 | a80807f0 | 715 records MODIS+VIIRS corregidos |
| F51 NRT token bypass probe-gate | #190 | 4a24c8ca | NRT cron 28-30/30 ok |
| F52-A Villarrica cluster cap | #193 | e52757a9 | Villarrica 11× → 4.81× |
| F52-B drift T1.5 single-pixel | #194 | 9b6cc6f2 | Chaitén 2.33→1.56, parcial |
| F54 sync workflow regenera mirova JSONs | #198 | 53df8fc6 | Banner F49 stale resuelto |
| F55 earthaccess Store /profile bypass | #199 | (subagente) | NRT mejora marginal |
| F53 test1_hot UnboundLocalError defensive | #204 | 347a6b5f | 1/14 granules ya no falla |

### Tags defensivos en origin (rollback A45)

```
pre-s73-data-cleanup
pre-s75-vrptir-a2-integration
pre-s77-f46-vrp-tir-fix
pre-s77-f47-store-cluster-rescue
pre-s77-f47-distance-class-fix
pre-s77-f50-vrp-mw-cap
pre-s77-f51-fetch-probe-bypass
pre-s77-f52a-villarrica-cluster-cap
pre-s77-f52b-single-pixel-sub-mw
pre-s77-f55-profile-bypass
pre-s78-f53-test1-hot
pre-s78-f56-enable-exclude-zones  # NO USADO (rechazado, no MIROVA-faithful)
pre-s78-f63-cluster-rank          # NO USADO (rechazado post-TDD)
```

## 2. Lección operacional crítica S78

**El instinto "lagos persistentes = bug simple" es FALSO**. 8 brainstorms paralelos demostraron:

1. **F46/F47/F50/F52 S77 ya arreglaron los bugs CRÍTICOS de pipeline**.
2. **NO existen quick wins simples** para "lagos persistentes". Cada propuesta naive tiene contraindicaciones:
   - exclude_zones (F56) → no MIROVA-faithful (Coppola NO usa)
   - NTI gate -0.85 (F61) → destruye 98% TPs por física Planck Andes
   - Cluster ranking revert (F63) → trade-off legítimo Tup/Last/PP vs Copahue
3. **Bug raíz real**: drift documental conocido. `compute_bg_stats` usa ring 5-25 km median; MIROVA usa kernel local 3×3 (Coppola 2024 L1129, Coppola 2016a L357, Campus 2024 L119).
4. **Lo que ves como "FP lago" en dashboard puede ser realidad física**: TPs con NTI<-0.85 son naturales en Andes (Planck puro a t_hot 285-295K).

**Antes de proponer cualquier fix S79 que toque pipeline NRT**: leer F66 doc completo + invocar `superpowers-brainstorming` skill como gate.

## 3. Plan S79 priorizado

### P1 (top prioridad) — F66 fix bg kernel local

#### P1.a — F66 híbrido (1 sesión, mejor ROI)

**Concepto**: dual-bg consistency gate. Computar t_bg local (kernel 3×3) cuando `compute_bg_stats` (ring 5-25 km) sugiere hot pixel, descartar si ΔT_local < 3 K.

**Por qué funciona**:
- Pixel lago: vecinos también lago → t_bg local ≈ pixel → ΔT_local ≈ 0 → descartado ✓
- Pixel cráter: vecinos roca fría → t_bg local << pixel → ΔT_local >> 0 → válido ✓

**Pasos**:
1. `superpowers-brainstorming` gate antes de empezar.
2. Tag defensivo `pre-s79-f66-hybrid` + push.
3. TDD primero sobre patrón sintético (R1).
4. Implementación en `pipeline/process_modis.py` + `process_viirs.py` con flag `enable_bg_kernel_gate: true`.
5. A/B con profiles `_f66_disabled.yaml` / `_f66_enabled.yaml` (data_subdir aislado).
6. Reproc 30d sobre 3 vol crítico (Copahue, Llaima, Villarrica) — VIIRS-only Windows.
7. Validar pixel-level vs MIROVA web (R2 obligatorio).
8. Audit independiente (R3) post-fix.
9. Merge si recall mantiene ≥ pre-fix y FPs lago < 50% reducidos.

**Riesgos**:
- Exacerba D9 cirrus (mitigable con cap=5MW S71 ya activo).
- PCC lacolito puede ser señal real, no FP geográfico — caso especial.
- Lava lake real Villarrica (vecinos lava lake) podría tener ΔT_local bajo también — needs validation.

#### P1.b — F66 comprehensive (2-3 sesiones, fix definitivo)

Migrar `compute_bg_stats` completamente a kernel local 5×5 per-pixel. Approach MIROVA-faithful real. Esfuerzo M. Solo si P1.a no logra resultado satisfactorio.

### P2 — Validación visual dashboard (usuario, no Claude)

`Ctrl+F5` sobre dashboard live:
- Selector volcán con optgroups CVZ/SVZ-N/SVZ-S/AVZ.
- Bandas horizontales translucent en chart.
- Nav header `🗺️ Mosaico` → 11 mini-cards.
- Click mini-card → drill-down.

### P3 — F31 A5 piloto VRPTIR Aveni (cuando ocurra evento térmico)

Cuando se de un evento con BT>300K en algún Tier A (verano sur enero-marzo 2026):
```bash
scripts\run_pilot_a5_s76.bat --days 30
python scripts\analyze_pilot_a5_results.py
```

Validar `vrptir_aveni_mw` PP contra Aguilera 2021 Qvolc 7-59 MW.

### P4 — F60 VSROI polygonal

Aveni 2024 polygon-based ROI per-volcán. 5 vol con vent desplazado (PCC lacolito SE, Lastarria solfatara SW, Tupungatito offset, Villarrica compacto, PP pit). Esfuerzo M.

### P5 — Backlog operacional

- **F55 NRT auth deep**: monkey-patch `Store.set_requests_session` para skip `/profile`. NRT actual 28-30/30 OK pero Lascar esporádico.
- **Reproc MODIS histórico**: GH Actions Linux (pyhdf disponible). Solo si necesario para limpieza visual.
- **Refactor frontend lib**: extraer `mirovaEqVrp`/`getLevel`/`latestVRP` a `frontend/lib/mirova_eq.js`. Evita drift entre `index.html` / `diario.html` / `mosaico.html`.
- **MIROVA OSF v2.5** descarga manual desde Zenodo (cross-check histórico, no urgente).
- **Self-hosted runner local Chile** (long-term F55 alternative).

## 4. Reglas operacionales activas (vinculantes)

### Skills triggers obligatorios (de CLAUDE.md)

| Situación | Skill |
|---|---|
| Cualquier bug, FP/FN inesperado, "no entiendo por qué pasa esto" | `superpowers-systematic-debugging` |
| Cambio código >20 líneas en pipeline | `writing-plans` + `test-driven-development` |
| **Antes de cualquier cambio enable_*: true en pipeline/profiles/mirova_equivalent.yaml** | `superpowers-brainstorming` + R2 pixel-level vs MIROVA |
| Antes de declarar fix listo, push, cerrar issue | `verification-before-completion` |
| 2+ investigaciones independientes paralelizables | `dispatching-parallel-agents` |
| Operaciones HDF/NetCDF/DataFrames grandes | `pandas-pro` |
| Audit script >5 min | `python-performance-optimization` |

### A45 obligatorio antes de tocar pipeline NRT

`process_*.py`, `store.py`, `pipeline/profiles/mirova_equivalent.yaml`:
1. Tag defensivo `pre-s79-<fix>` + push a origin.
2. Confirmación explícita Nicolás vía `AskUserQuestion` (no asumir).
3. NRT cron corre 12×/día × 11+ volcanes — bug que pasa tests rompe semántica masivamente.

### A47 NO paralelo sobre `data/mirova_equivalent/`

Lección S77: 4 procesos `run_pipeline.py` paralelo sobre mismo dir corrompió JSONs por race condition. **Reprocs locales DEBEN ser serial** (1 proceso). Para múltiples volcanes, loop bash secuencial.

### A44 worktrees dedicados per subagente paralelo

Cada subagente que tocará git debe trabajar en su propio worktree:
```bash
git worktree add ../VRP-Chile-s79-<task> origin/main
```

Cleanup post-merge desde el worktree principal:
```bash
git worktree remove ../VRP-Chile-s79-<task>
```

### Conventions importantes

- **Comunicar como geólogo, no programador**: fenómeno físico primero, mecanismo pipeline después, fórmula al final.
- **MIROVA canónico**: Coppola/Laiolo/Massimetti/Campus/Aveni/Cigolini (Torino+Firenze+Sapienza Roma). **NO MIROVA**: Di Bella (INGV Catania, RSDF), Marchese (CNR-IMAA, NHI).
- **YAML `on:`**: usar comillas `"on":` para evitar Norway problem (A43).
- **CSV path**: `latest_consolidado.csv` hard-copy actualizado por workflow `sync-mirova-csv.yml` (cron 1h).

## 5. Sistema operacional S79

- **Worktree canónico**: `C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP-Chile-s70/`
- **NRT cron**: cada 2h, matrix 11 Tier A + 19 monitored extras. 28-30/30 jobs success típico, Lascar esporádico fail (auth NASA Azure).
- **Sync MIROVA**: cada 1h via `sync-mirova-csv.yml` + regenera `data/mirova/<vol>.json` (F54).
- **Health check**: `python scripts/nrt_health_check_s77.py --days 1`
- **Audit ratios**: `python experiments/148_audit_pre_reproc/audit_pre_reproc_v2.py`

## 6. Documentos clave a leer

Antes de empezar S79, leer en orden:

1. `docs/SESSION_CLOSE_S78.md` (este cierre).
2. **`docs/F66_BG_KERNEL_LOCAL_DEEP_S78.md`** (bug raíz + 3 niveles de fix).
3. `docs/F64_NTI_METHOD_BRAINSTORM_S78.md` (por qué F61 NO funciona).
4. `docs/F65_APPROACHES_ALTERNATIVOS_S78.md` (Top 3 approaches recomendados).
5. `docs/AUDITORIA_PRE_REPROC_S77_ADDENDUM_V2.md` (ratios actuales por volcán).

## 7. Métricas acumuladas S76+S77+S78

- **65 PRs mergeados** (#158-#215).
- **11 fixes pipeline críticos** con A45.
- **3 features Mirova-v1 parity** + 6 dashboard refactors S77.
- **13 tags defensivos** en origin.
- **507 tests passing** (vs 432 pre-S76 = **+75 tests**).
- **8 brainstorms paralelos** S78 = nivel rigor metodológico máximo del proyecto.
- **4 lecciones meta** nuevas en CLAUDE.md (A44, A45, A46, A47).

## 8. Veredicto operacional

- ✅ Pipeline NRT estable.
- ✅ NRT cron 28-30/30 funcional.
- ✅ MIROVA refs fresh (sync cron 1h).
- ✅ Dashboard mejorado (mosaico + bandas + regiones).
- ⏳ Bug raíz lagos documentado pero NO implementado (F66, S79 P1).
- ⏳ A5 piloto VRPTIR esperando evento térmico estacional.

**Cualquier sesión nueva DEBE empezar por aquí + leer docs §6 antes de proponer fixes.**
