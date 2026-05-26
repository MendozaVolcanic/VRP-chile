# Bloque arranque S80 — VRP Chile (post S79 parcial 2026-05-26)

> Continuación tras S79 parcial. **F66 híbrido Tasks 0-4 completas, Tasks 5-15
> pendientes**. 2 PRs cleanup mergeados (#217 workflows + #218 experiments).
> Tests F66: 9/9 passing. Baseline pre-existing: 510 passed + 6 fails (issue
> investigable).

## ⚡ Primer comando (LEER PRIMERO)

```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP-Chile-s70"
git fetch origin --prune
ls tasks/BLOQUE_ARRANQUE_S*.md | tail -1   # debe ser S80.md
```

Si vas a retomar F66 implementación:

```bash
# Worktree dedicado F66 todavía existe (NO removerlo todavía)
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP-Chile-s79-f66"
git status   # debe estar limpio en branch claude/s79-f66-hybrid-bg-gate
git log --oneline -8  # 7 commits F66 + 1 plan + 1 design
python -m pytest tests/test_f66_bg_kernel_consistency.py -v   # 9/9 passing esperado
```

## 1. Estado al cierre S79 parcial

### S79 completas

| PR/Tag | Contenido | Estado |
|---|---|---|
| Tag `pre-s79-workflows-cleanup` → 4d6c1e93 | Defensivo pre-archive workflows | ✅ pusheado |
| [PR #217](https://github.com/MendozaVolcanic/VRP-chile/pull/217) | Archive 9 reproc-* legacy + fix yml roto que disparaba 18+ fails CI por push | ✅ mergeado `0691a3b6` |
| [PR #218](https://github.com/MendozaVolcanic/VRP-chile/pull/218) | Backlog 9 experiments S76 (audits + piloto A5, sin snapshots 60MB) | ✅ mergeado `9d4dd082` |
| Tag `pre-s79-f66-hybrid` → 9d4dd082 | Defensivo pre-F66 implementación | ✅ pusheado |
| Design doc F66 híbrido | `docs/superpowers/specs/2026-05-26-f66-hybrid-bg-kernel-consistency-gate-design.md` | ✅ commit `4ec7d221` |
| Plan F66 bite-sized 15 tasks | `docs/superpowers/plans/2026-05-26-f66-hybrid-bg-kernel-consistency-gate.md` | ✅ commit `a93f88f9` |

### S79 F66 implementación parcial (4/12 tasks código)

Branch: `claude/s79-f66-hybrid-bg-gate` (pusheado en origin, NO mergeado)
Worktree: `C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP-Chile-s79-f66/`

| Task | Estado | Commit |
|---|---|---|
| **Task 0**: Setup A45 (tag defensivo + confirmación Nicolás) | ✅ | (tag) |
| **Task 1**: Helper `apply_f66_consistency_gate` + test 1 (TDD red→green) | ✅ | `a73775cd` |
| Task 1 fix: dead line removed (cut-paste leftover) | ✅ | `5cd8d680` |
| **Task 2**: 7 tests sintéticos adicionales (8 total) | ✅ | `f8d2d156` |
| **Task 3**: Profile parsing (3 module globals + Profile class wrapper) | ✅ | `aa1708db` |
| **Task 4**: Integración process_viirs.py (I-band 375m) | ✅ | `2fe10bc0` |
| **Task 5**: Integración process_viirs_mod.py (M-band 750m) | ⏳ pending |
| **Task 6**: Integración process_modis.py (B21/22 1km) | ⏳ pending |
| **Task 7**: Profile yaml dedicado `_f66_dt5k.yaml` | ⏳ pending |
| **Task 8**: Baseline tests + sanity check | ⏳ pending |
| **Task 9**: Reproc Copahue 30d VIIRS-only (SERIAL A47) | ⏳ pending |
| **Task 10**: Reproc Llaima 30d VIIRS-only | ⏳ pending |
| **Task 11**: Reproc Villarrica 30d VIIRS-only | ⏳ pending |
| **Task 12**: Audit comparativo data/f66_dt5k vs data/mirova_equivalent | ⏳ pending |
| **Task 13**: R2 pixel-level vs MIROVA web (5 records × 3 vol) | ⏳ **MANUAL Nicolás** |
| **Task 14**: Docs resultados + decisión Fase 2/3 | ⏳ pending |
| **Task 15**: PR Draft (NO merge inmediato) | ⏳ pending |

### Tests F66 actuales

- **9/9 F66 passing** (8 sintéticos + 1 profile defaults)
- **510 passed baseline** (sin regresiones nuevas)
- **6 pre-existing fails** detectados S79 (issue separado — ver §3)

## 2. Plan S80 priorizado

### P1 — Continuar F66 implementación (Tasks 5-15)

**Subagent-Driven approach ya aprobado por Nicolás S79.**

Plan ejecutable directo desde el plan:
```bash
# Worktree F66 ya existe
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP-Chile-s79-f66"

# Task 5: integración process_viirs_mod.py (M-band 750m)
# Patrón idéntico a Task 4 commit 2fe10bc0. Variable BT: bands["M13"]
# Localización: post hot_mask final (exclude_zones), antes de extracción hot pixels

# Task 6: integración process_modis.py (B21/22 1km)
# Idem. Variable BT: probablemente bt_mir o bands["B22"]/bands["B21"]
# Caveat Windows: pyhdf roto. Import test puede dar warning aceptable.

# Task 7: profile yaml
cat > pipeline/profiles/_f66_dt5k.yaml <<'EOF'
extends: mirova_equivalent

profile: _f66_dt5k
description: >
  F66 híbrido dual-bg consistency gate ON con kernel 3×3 y threshold 5K.
  Profile A/B aislado — NO contamina operacional.
data_subdir: f66_dt5k

thresholds:
  enable_bg_kernel_consistency_gate: true
  kernel_consistency_dt_k: 5.0
  kernel_consistency_size: 3
EOF

# Task 8: sanity tests
python -m pytest tests/ -q --tb=no
# Esperado: 511 passed (510 baseline + 1 nuevo test_profile_f66_dt5k_loads), 6 pre-existing fails, 24 skipped

# Tasks 9-11: reproc SERIAL VIIRS-only (NO paralelo A47)
START=$(date -d '30 days ago' +%Y-%m-%d)
END=$(date +%Y-%m-%d)

for vol in Copahue Llaima Villarrica; do
    python scripts/run_pipeline.py \
      --profile _f66_dt5k \
      --volcano $vol \
      --sensor viirs \
      --start $START --end $END \
      --overwrite
done

# Task 12: audit (script ya documentado en plan)
python experiments/152_f66_audit_phase1/audit.py
```

### P2 — Investigar 6 tests pre-existing fallidos (issue independiente)

**Hipótesis raíz** (detectada S79 Task 1 review):
- `pipeline/process_modis.py:316` espera 3-tuple de `compute_bg_stats`
- `compute_bg_stats` retorna `None` literal (no tupla `(None, None, n_bg)`) cuando `n_bg < min_bg_pixels`
- Error: `TypeError: cannot unpack non-iterable NoneType object`

Tests afectados:
- `tests/test_drift1_test1_k1_saturation.py::test_drift1b_off_bg_contaminated_by_test1_active`
- `tests/test_drift1_test1_k1_saturation.py::test_drift1b_on_bg_excludes_test1_k1_active`
- `tests/test_process_modis_core.py::test_calculate_vrp_no_anomaly_in_uniform_scene`
- `tests/test_process_modis_core.py::test_calculate_vrp_returns_diag_fields`
- `tests/test_process_modis_core.py::test_calculate_vrp_sensor_field_correct`
- `tests/test_process_modis_core.py::test_calculate_vrp_product_version_detection`

**Verificar**:
```bash
python -m pytest tests/test_process_modis_core.py::test_calculate_vrp_no_anomaly_in_uniform_scene -v
# Inspeccionar pipeline/process_modis.py:316 + compute_bg_stats retorno
grep -n "compute_bg_stats" pipeline/process_modis.py pipeline/detection_context.py
```

**Importante**: investigar si los 6 fails afectan reproc real (no solo unit tests sobre mocks).

### P3 — Otras prioridades backlog

- A5 piloto VRPTIR Aveni (cuando ocurra evento térmico estacional)
- F60 VSROI polygonal
- TROPOMI SO2
- Frontend refactor lib

## 3. Reglas operacionales vinculantes (sin cambios desde S79)

### Skills triggers obligatorios
- `superpowers-systematic-debugging` antes de cualquier fix de bug pipeline
- `superpowers-brainstorming` antes de cualquier `enable_*: true` en `mirova_equivalent.yaml`
- `verification-before-completion` antes de declarar listo
- `test-driven-development` antes de tocar pipeline
- `writing-plans` antes de implementación >20 líneas

### A45 obligatorio
Tag defensivo + confirmación Nicolás antes de tocar:
- `pipeline/process_*.py`
- `store.py`
- `pipeline/profiles/mirova_equivalent.yaml`

### A47 NO paralelo sobre `data/mirova_equivalent/`
Race conditions documentadas S77. Reprocs locales SERIALES.

### A44 worktrees dedicados per subagente paralelo
Worktrees activos:
- `VRP-Chile-s70/` — canónico, branch work-s78-bloque-arranque-s79 (huérfano post-merge)
- `VRP-Chile-s79-f66/` — branch claude/s79-f66-hybrid-bg-gate (F66 implementación)
- `VRP-Chile-s80-bloque/` — branch claude/s80-bloque-arranque (este doc) — cleanup post-merge

### Convenciones
- Comunicar como geólogo (fenómeno físico → mecanismo pipeline → fórmula al final)
- MIROVA canónico: Coppola/Laiolo/Massimetti/Campus/Aveni/Cigolini
- NO MIROVA: Di Bella (INGV Catania), Marchese (CNR-IMAA NHI)
- YAML `on:` con comillas (A43 Norway problem)
- HEREDOC commit messages con Co-Authored-By Claude

## 4. Tags defensivos en origin (rollback A45)

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
pre-s79-workflows-cleanup  ← S79 nuevo
pre-s79-f66-hybrid         ← S79 nuevo
```

## 5. Documentos clave a leer S80

Antes de retomar F66:

1. **`docs/superpowers/specs/2026-05-26-f66-hybrid-bg-kernel-consistency-gate-design.md`** (design doc aprobado).
2. **`docs/superpowers/plans/2026-05-26-f66-hybrid-bg-kernel-consistency-gate.md`** (plan ejecución con Tasks 5-15 detalladas).
3. `docs/F66_BG_KERNEL_LOCAL_DEEP_S78.md` (motivación bug raíz documental).
4. `docs/F64_NTI_METHOD_BRAINSTORM_S78.md` (por qué F61/F65-TOP-1 no eran viables — insight Path B nunca dispara).

## 6. Sistema operacional S80

- **NRT cron**: cada 2h, matrix 11 Tier A + 19 extras. 28-30/30 jobs success típico.
- **Sync MIROVA**: cada 1h via `sync-mirova-csv.yml`.
- **Health check**: `python scripts/nrt_health_check_s77.py --days 1`
- **CI ruido eliminado**: 9 reproc-* legacy workflows archivados S79 PR #217.

## 7. Veredicto operacional al cierre S79

- ✅ Pipeline NRT estable (3 commits NRT entre cierre S79 y este bloque).
- ✅ Cleanup CI ruido (18+ fails/4h eliminados).
- ✅ Experiments S76 persistidos en git history.
- ✅ Tag defensivo + design doc + plan F66 aprobados.
- ✅ F66 helper + 9 tests + integración VIIRS-I implementados.
- ⏳ F66 incompleto: Tasks 5-15 (M-band + MODIS + profile yaml + reproc + R2 + PR).
- ⚠️ 6 tests pre-existing fallando en main (issue investigable).

**Cualquier sesión nueva empezar por este bloque + leer §5 docs antes de retomar Tasks 5+.**
