# Bloque arranque S78 — VRP Chile (post cierre S77 2026-05-25)

> Continuación tras cierre S77 superexitoso. **42 PRs S76+S77 mergeados**.
> **8 fixes pipeline críticos** con A45 + tags defensivos en origin.
> Tests baseline: **499 passed, 24 skipped, 0 regresión**.

## 1. Estado al cierre S77

### 8 fixes pipeline críticos cerrados con A45

| Fix | PR | Sha | Impacto |
|---|---|---|---|
| F46 vrp_tir_mw Stefan-Boltzmann (VIIRS I-band) | #177 | a80807f0 | 143 records corregidos |
| F47 cluster rescate (store.py asimetría) | #175 | 34b74f20 | ~400 records recuperados |
| F47 follow-up distance_class='summit' | #181 | 899a4b8d | Rescatados visibles en UI |
| F49 sync MIROVA cron + freshness CI | #187 | c75387fd | MIROVA +3 750 records |
| F50 cap D9 vrp_mw scene-wide | #188 | a80807f0 | 715 records corregidos |
| F51 NRT token bypass probe-gate | #190 | 4a24c8ca | Probe-gate skip con token |
| F52-A Villarrica per-volcano cluster cap | #193 | e52757a9 | Villarrica glaciar fix |
| F52-B drift T1.5 single-pixel sub-MW | #194 | 9b6cc6f2 | Tup/PCC/Cha/PP fix |
| F54 sync workflow regenera mirova JSONs | #198 | 53df8fc6 | Banner stale resuelto |
| F55 earthaccess Store /profile bypass | #199 | 474b7152 | NRT Lascar consistent fix |

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
```

### Validación empírica F52-B confirmada parcial

Audit v2 post-reproc Chaitén/Villarrica/NdC (PR #197 addendum):
- **Chaitén**: 2.33× → **1.56×** (F52-B funcionando, +33% mejora)
- **Villarrica**: 4.81× → **4.11×** (F52-A cap funcionando, leve mejora)
- 6/11 Tier A ya OK: Lascar, Lastarria, Llaima, Isluga, Copahue, PCC
- Tupungatito quedó pendiente (race condition corrupted, restored)

### Aprendizajes meta nuevos (CLAUDE.md A47-A48)

- **A47**: reproc paralelo sobre `data/mirova_equivalent/` corrompe JSONs.
  Mitigación: loop bash secuencial en 1 background process.
- **A48**: subagentes pueden inventar regex razonable pero incorrecta.
  Mitigación: validar convención del proyecto antes (e.g.
  `Counter(r['sensor'])` sobre data real).

## 2. Pendientes activos S78

### P1 — Reproc Tupungatito + NdC focalizado (~1-2h máquina Nicolás)

```bash
# Serial, sin race (lección A47)
python scripts/run_pipeline.py --profile mirova_equivalent --volcano Tupungatito --start 2026-04-24 --end 2026-05-24 --overwrite
python scripts/run_pipeline.py --profile mirova_equivalent --volcano NevadosDeChillan --start 2026-04-24 --end 2026-05-24 --overwrite
python experiments/148_audit_pre_reproc/audit_pre_reproc_v2.py
```

Esperado: Tup 13.01× → 1-3×, NdC recall sale de "(sin matches)".

### P2 — Verificar NRT cron post-F55 (próximo cron ~30 min después de mergeo F55)

```bash
gh run list -R MendozaVolcanic/VRP-chile --workflow=nrt.yml --limit 3
```

Esperado: Lascar sale de failure intermitente. Workflow conclusion
empieza a verse "success".

### P3 — F31 A5 piloto VRPTIR Aveni (Lastarria/Copahue/PP, ~2-3h)

```bash
scripts\run_pilot_a5_s76.bat --days 30
# Después
python scripts\analyze_pilot_a5_results.py
```

Validar `vrptir_aveni_mw` PP contra Aguilera 2021 Qvolc 7-59 MW.

### P4 — Mirova-v1 dashboard parity proposal (TBD subagente PR S77)

PR #200+ con features candidatos a portear. Decidir scope S78.

### P5 — F53 backlog: bug `test1_hot` unbound local var

Detectado en sanity test S77 (1 granule de 14 fallaba). No urgente,
no bloqueante. Fix `pipeline/process_viirs.py:~860` cuando se invoque
test1_hot fuera del scope donde se inicializa.

## 3. Pendientes operacionales no-Claude (Nicolás local)

- **Reproc histórico full** si querés "limpiar" backlog visual completo.
  Tiempo estimado 5-8h VIIRS-only Windows, sin race.
- **Validación A/B 30d natural**: NRT cron acumula records nuevos con
  todos los fixes activos. En 1-2 semanas el dataset visual estará
  lleno de records post-fix sin reproc explícito.
- **MIROVA OSF v2.5 archive descarga** desde Zenodo (no presente local,
  paso 4 del audit S77 PR #196 no ejecutable). Solo si querés cross-check
  contra ground truth post-procesado MIROVA.

## 4. Sistema operacional S78

- **Worktree canónico**: `C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP-Chile-s70/`
- **NRT cron**: cada 2h, matrix 11 Tier A + 19 monitored extras.
- **Sync MIROVA**: cada 1h via workflow `sync-mirova-csv.yml` + regenera JSONs (F54).
- **Health check**: `python scripts/nrt_health_check_s77.py --days 1`

## 5. Cómo arrancar S78

```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP-Chile-s70"
git fetch origin --prune
git checkout main && git pull --ff-only  # (o tu worktree principal)
cat tasks/BLOQUE_ARRANQUE_S78.md  # este doc
python scripts/nrt_health_check_s77.py --days 1  # estado pipeline NRT
python -m pytest tests/ -q --tb=no  # baseline 499 passed
```

## 6. Métricas S77

- **42 PRs** mergeados (#158 a #199).
- **8 fixes pipeline críticos** con A45 explícito.
- **10 tags defensivos** en origin para rollback.
- **499 tests passed** (baseline al cierre), 24 skipped, 0 regresión.
- **Sesión más productiva del proyecto** post-S33.
