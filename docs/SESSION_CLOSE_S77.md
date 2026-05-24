---
title: "S77 cierre — F46 + F47 + dashboard refactors completos"
session: S77
status: closed
ai_generated: true
confidence: high
explored: true
tags:
  - cierre
  - f46
  - f47
  - dashboard
  - nrt
related:
  - docs/F46_VRP_TIR_BUG_S76.md
  - docs/F47_NDC_RECALL_S76.md
  - docs/F48_LLAIMA_COPAHUE_REFS_GAP.md
  - docs/F46_LASTARRIA_IMPACT_S77.md
---

# S77 cierre — bugs pipeline críticos resueltos + dashboard limpio

## Veredicto operacional

**Pipeline NRT post-S77**: los 2 fixes pipeline más impactantes desde S33
están mergeados, testeados, con tags defensivos y monitoreados via health
check. Tests baseline 471 passed, 24 skipped, 0 regresión.

**Dashboard post-S77**: 27% de records antes invisibles ahora se muestran
(NOAA-21), referencia MIROVA por sensor, métricas live recall/precision,
spatial layer Leaflet, guards F46+F47 aplicados, banner refs escasas.

## PRs S77 mergeados (22 total acumulando S76+S77)

### Pipeline (con A45 + tags defensivos)

| PR | Sha | Contenido |
|---|---|---|
| [#175](https://github.com/MendozaVolcanic/VRP-chile/pull/175) | `34b74f20` | F47 H4 fix: cluster rescate store.py |
| [#177](https://github.com/MendozaVolcanic/VRP-chile/pull/177) | `a80807f0` | F46 A+B fix: gate consistencia MIR + threshold subido |
| [#181](https://github.com/MendozaVolcanic/VRP-chile/pull/181) | `899a4b8d` | F47 follow-up CRITICAL: distance_class summit post-rescate |

### Dashboard frontend

| PR | Contenido |
|---|---|
| #161, #170, #174 | F46 hotfix + C1 NOAA-21 + H1+H2+M1 + H3+M5 |
| #164 | Overlay MIROVA per-sensor |
| #166 | Leaflet spatial layer (summit/scene/bbox MIROVA) |
| #167 | Card métricas live recall/precision/F1/ratio |
| #179 | F48 banner refs MIROVA escasas |

### Docs + tooling + tests

| PR | Contenido |
|---|---|
| #162, #163, #168 | F46+F47 docs canónicos + scope reducido |
| #169, #172, #180 | F47 investigación + F48 refs + Lastarria caveat verify |
| #171, #173 | Tests TDD F46+F47 (5+5 xfail-strict) |
| #165, #178 | Scripts piloto F31 A5 + reproc histórico 11 Tier A |
| #176 | CLAUDE.md A46 schema asimétrico |

## Tags defensivos en origin

- `pre-s77-f46-vrp-tir-fix` (sha `2bf909c8`)
- `pre-s77-f47-store-cluster-rescue` (sha `2bf909c8`)
- `pre-s77-f47-distance-class-fix` (sha `fe5251ea`)

Rollback:
```bash
git checkout pre-s77-f47-store-cluster-rescue -- pipeline/store.py
git checkout pre-s77-f46-vrp-tir-fix -- pipeline/process_viirs.py pipeline/profile.py pipeline/profiles/mirova_equivalent.yaml
```

## Health check NRT post-S77

`scripts/nrt_health_check_s77.py` corre en ~5 s sobre `data/mirova_equivalent/`:

```text
Volcan                  n_total  n_win  rescued  F46susp  max_vrp  status
Chaiten                    1312     70        0        0   230.41  alive
Copahue                    1240     68        0        0   218.99  alive
Isluga                     1021     58        0        0   233.23  alive
Lascar                     1065     57        0        0   484.59  alive
Lastarria                  1064     59        0        0   748.21  alive
Llaima                     1255     67        0        0   291.40  alive
NevadosDeChillan           1218     66        0        0   236.24  alive
PlanchonPeteroa            1190     64        0        0   198.51  alive
PuyehueCordonCaulle        1306     85        0        0   675.08  alive
Tupungatito                1173     67        0        0   362.92  alive
Villarrica                 1262     72        0        0   166.99  alive

NRT alive : PASS  (11/11 alive)
F47 fix   : INDETERMINATE (sin rescatados aún en ventana 7d — actividad baja)
F46 fix   : PASS (0 records F46-susp en ventana 7d)
```

Validación esperada en próximos ciclos:
- F47: aparecerán records con `final_hotspot_source='cluster_rescue'` cuando
  algún Tier A active el cráter durante una pasada con FP single far.
- F46: el conteo `F46susp` debe quedar en 0 indefinidamente. Si sube,
  investigación inmediata.

## Hallazgos críticos S77

### CRITICAL #1 — Bug F47 H4 (store.py:183-195)

Gate evaluaba pixel hottest single (que podía ser FP lejano) ignorando el
primary_cluster vent-anchored. ~400 records VRP invisibles en 11 Tier A
durante meses (caso bandera: NdC 2026-02-01 332.756 MW @ 0.536 km del vent
descartado por un FP a 26.58 km).

Fix Opción A: si `cluster_rescues` (cluster cerca + vrp>0) y hotspot single
lejano, rescatar — vrp_eruption = pc.vrp_mw, reescribir hotspot/final_hotspot
al centroide del cluster, etiqueta `final_hotspot_source='cluster_rescue'`,
`distance_class='summit'`, `discarded_reason='single_pixel_far_overridden_by_cluster'`.

### CRITICAL #2 — Bug F46 vrp_tir_mw (process_viirs.py:968-986)

Stefan-Boltzmann puro sobre máscara `max(0.5K, 4σ_bg)` sin gate consistencia
MIR. En terreno heterogéneo (nieve/lago/cirrus) σ_bg se inflaba, 100-230
pixels pasaban el gate, cada uno aportaba ~3-5 MW residual × A_pix → total
3 000-9 600 MW espurios. 143 records afectados. Caso patognomónico: Chaitén
2026-03-25 con `n_anomalous_pixels=0` y `vrp_tir_mw=6 872 MW`.

Fix Opción A+B: nueva helper `_compute_vrp_tir_with_gate` con threshold
subido (`max(3K, 6σ)`) + gate consistencia con `hot_mask_mir` dilatado 3
pixels para tolerar desalineamiento inter-band.

### CRITICAL #3 — distance_class stale post-F47-rescate

Detectado por audit dashboard post-S77 (subagente). El fix F47 H4 reescribía
`final_hotspot_*` pero NO `distance_class`. Como `mirovaEqVrp` filtra por
`distance_class === 'summit'`, los ~400 records rescatados quedaban
**invisibles en el dashboard**. Fix una línea (PR #181): forzar
`distance_class='summit'` dentro del rescue branch.

### HIGH — C1 NOAA-21 invisible

27% del dataset (3 500 records NOAA-21) procesado en NRT desde S18 pero
nunca renderizado en chart, mapa o scatter. Fix: agregar 4 entries a los 3
colorMaps + 2 filtros + 2 push en `buildDatasets`.

## Aprendizajes meta nuevos S77

- **A46** (CLAUDE.md PR #176): schema asimétrico hotspot single vs
  primary_cluster es vector de bugs sistémicos. Audit gates downstream
  cuando agregues una nueva representación.
- **Audit dashboard como fase obligatoria post-pipeline-fix**: F47 mostró
  que fix en pipeline puede ser silenciosamente invisible en UI si
  upstream/frontend tienen lógica que asume schema previo. Después de
  cualquier fix que cambia campos del record, re-audit dashboard.
- **xfail-strict como TDD ratchet**: PR #173 y PR #171 usaron
  `@pytest.mark.xfail(strict=True)` — convierte el "GREEN inesperado"
  en error explícito, forzando al implementador a quitar el marker.
  Mejor que xfail simple que permite drift.

## Pendientes S78

1. **Galería imgs MIROVA P3** — subagente terminó pero PR pendiente de
   commit/merge (verificar status).
2. **Reproc histórico local** — Nicolás corre
   `scripts/run_reproc_post_f46_f47_s77.bat --days 30` (8-15 h máquina)
   para que los ~400 records VRP + 143 vrp_tir espurios se corrijan en
   los JSONs históricos. NRT cron solo afecta records nuevos.
3. **F31 A5 piloto local** — `scripts/run_pilot_a5_s76.bat` (4-8 h)
   sobre 3 candidatos. Después `scripts/analyze_pilot_a5_results.py`
   genera verdict vs Aguilera 2021 PP (7-59 MW).
4. **Re-audit recall/precision post-reproc** —
   `experiments/139_recall_precision_s76/audit.py` debe ver NdC recall
   subir 0.20 → 0.60-0.80.

## Validación cuantitativa post-S77

- **F47 fix**: ~400 records esperados de recuperación (PCC 110, Copahue 79,
  Villarrica 59, Chaitén 49, NdC 33, Llaima 27, Lascar 20, otros 25).
  Verificable con script `experiments/141_f47_h4_rootcause/audit.py`.
- **F46 fix**: 143 records vrp_tir_mw>1000 esperados drop ≥95% (~7 residuales
  máx). Verificable con `experiments/138_audit_mw_outliers_s76/audit2.py`.
- **Lastarria caveat F46**: verificado Δrecall=0 (PR #180), el fix no daña
  el único Tier A con TIR legítimo.
