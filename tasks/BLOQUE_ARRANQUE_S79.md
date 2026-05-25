# Bloque arranque S79 — VRP Chile (post cierre S78 2026-05-25)

> Continuación tras cierre S78 (Mirova-v1 parity sprint + F53). **53 PRs
> S76+S77+S78 mergeados**. Tests 501 passing, 24 skipped, 0 regresión.

## 1. Estado al cierre S78

### Fixes pipeline críticos con A45 (acumulados)

| Fix | PR | Sha |
|---|---|---|
| F46 vrp_tir_mw Stefan-Boltzmann | #177 | a80807f0 |
| F47 cluster rescate | #175 | 34b74f20 |
| F47 follow-up distance_class | #181 | 899a4b8d |
| F49 sync MIROVA cron + freshness CI | #187 | c75387fd |
| F50 cap D9 vrp_mw scene-wide | #188 | a80807f0 |
| F51 NRT token bypass probe-gate | #190 | 4a24c8ca |
| F52-A Villarrica per-volcano cluster cap | #193 | e52757a9 |
| F52-B drift T1.5 single-pixel sub-MW | #194 | 9b6cc6f2 |
| F54 sync workflow regenera mirova JSONs | #198 | 53df8fc6 |
| F55 earthaccess Store /profile bypass | #199 | 474b7152 |
| **F53 test1_hot UnboundLocalError defensive init** | **#204** | **347a6b5f** |

### Features Mirova-v1 parity (S78)

- **F1** Mosaico panorámico `frontend/mosaico.html` (PR #202).
- **F2** Bandas MIROVA en charts (PR #203).
- **F5** Tags región CVZ/SVZ/AVZ + sort N→S (PR #203).

### Tags defensivos en origin (11 total)

Ver `docs/SESSION_CLOSE_S78.md` §"Tags defensivos".

## 2. Pendientes activos S79

### P1 — Validación visual dashboard (tu browser)

`Ctrl+F5` sobre https://mendozavolcanic.github.io/VRP-chile/:
- Verificar selector volcán con optgroups CVZ/SVZ-N/SVZ-S/AVZ.
- Verificar bandas horizontales translucent en chart timeline.
- Click `🗺️ Mosaico` en nav header → verificar grid 11 mini-cards.
- Click cualquier mini-card → drill-down a `index.html?volcano=...`.

Si algo no se ve bien, F1/F2/F5 son fixable en frontend bite-sized.

### P2 — F31 A5 piloto VRPTIR Aveni (tu máquina local, 4-8h)

```bash
scripts\run_pilot_a5_s76.bat --days 30
# Después de que termine:
python scripts\analyze_pilot_a5_results.py
```

Validar `vrptir_aveni_mw` PP contra Aguilera 2021 Qvolc 7-59 MW.
Si dentro de banda → candidato flip operacional S80+ con A45.

### P3 — Reproc focalizado opcional (tu máquina, ~1-2h)

NRT cron natural ya está aplicando los fixes a records nuevos. Si
querés "limpiar" backlog visual histórico, los volcanes que más se
benefician son Tupungatito (13.22×) y NdC (sin matches MIROVA).

```bash
# Serial, sin race (lección A47)
python scripts/run_pipeline.py --profile mirova_equivalent --volcano Tupungatito --start 2026-04-24 --end 2026-05-24 --overwrite
python scripts/run_pipeline.py --profile mirova_equivalent --volcano NevadosDeChillan --start 2026-04-24 --end 2026-05-24 --overwrite
python experiments/148_audit_pre_reproc/audit_pre_reproc_v2.py
```

### P4 — Mirova-v1 parity backlog S79+

Doc `docs/MIROVA_V1_PARITY_PROPOSAL_S77.md` (PR #201) tiene 5+ features
adicionales no priorizadas en sprint S78:
- F3, F4, F6+ — features menores (estimar bite-sized cada uno).

### P5 — Refactor frontend lib (opcional, M)

Duplicación lógica científica entre `index.html`, `diario.html`,
`mosaico.html`. Extraer a `frontend/lib/mirova_eq.js`:
- `mirovaEqVrp(r, innerKm, includeFar)`
- `getLevel(vrp)` + `LEVELS`
- `latestVRP(records, ...)`
- `isSummitDetection(r)`
- `isValidDetection(r)`

Beneficio: 1 source-of-truth, evita drift entre páginas. Esfuerzo M
(~2-3h) por cambios manuales de 3 archivos + script de check
consistencia.

### P6 — Backlog general

- **MODIS_AQUA 07:25 contamination** (F50 mitigado pero cirrus extendido
  natural fenómeno).
- **OSF v2.5 archive** descarga manual (Zenodo, para cross-check
  histórico).
- **Self-hosted runner local Chile** S80+ para evitar bloqueo Azure
  NASA Earthdata (long-term solution F55 alternativa).

## 3. Sistema operacional S79

- **Worktree canónico**: `C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP-Chile-s70/`
- **NRT cron**: cada 2h, matrix 11 Tier A + 19 monitored extras.
- **Sync MIROVA**: cada 1h via `sync-mirova-csv.yml` + regenera JSONs (F54).
- **Health check**: `python scripts/nrt_health_check_s77.py --days 1`
- **Audit ratios**: `python experiments/148_audit_pre_reproc/audit_pre_reproc_v2.py`

## 4. Cómo arrancar S79

```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP-Chile-s70"
git fetch origin --prune
git checkout main  # (o el worktree principal)
git pull --ff-only
cat tasks/BLOQUE_ARRANQUE_S79.md  # este doc
python -m pytest tests/ -q --tb=no  # baseline 501 passed
```

## 5. Métricas acumuladas S76+S77+S78

- **53 PRs mergeados** (#158-#204).
- **11 fixes pipeline críticos** con A45.
- **3 features Mirova-v1 parity** + 6 dashboard refactors S77.
- **11 tags defensivos** en origin.
- **501 tests passing** (vs 432 pre-S76 = **+69 tests**).
- **2 lecciones meta** nuevas en CLAUDE.md (A47, A48).
