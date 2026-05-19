# S62 Workflow Status

## Run A/B Lastarria + Tupungatito (kernel-bg)

- **Run ID**: 26072884472
- **URL**: https://github.com/MendozaVolcanic/VRP-chile/actions/runs/26072884472
- **Triggered**: 2026-05-19 ~01:00 UTC (post-merge PR #79)
- **Window**: 2026-03-01 → 2026-05-19 (80 días)
- **ETA**: ~3-4h (matrix max-parallel=2)
- **Profile**: `_local_kernel_bg_enabled`
- **Outputs**:
  - `data/_local_kernel_bg_enabled/Lastarria.json`
  - `data/_local_kernel_bg_enabled/Tupungatito.json`

## Run Reproc PCC operacional (inner_radius=7)

- **Run ID**: 26072886354
- **URL**: https://github.com/MendozaVolcanic/VRP-chile/actions/runs/26072886354
- **Triggered**: 2026-05-19 ~01:00 UTC
- **Window**: 2026-04-01 → 2026-05-19 (49 días)
- **ETA**: ~2-3h
- **Profile**: `mirova_equivalent` (operacional)
- **Output**: `data/mirova_equivalent/PuyehueCordonCaulle.json`

## Estado al disparar

- PR #79 mergeado a main: PCC `inner_radius_km: 7` ya activo
- Workflows disparados ambos `in_progress` (verificado +15s post-trigger)
- Tests pipeline: 335 passed / 16 skipped
- NRT cron continúa cada 2h aplicando flags actuales

## Próximos pasos cuando completen

1. Pull main para traer JSONs reprocesados
2. Run audit script `experiments/110_s62_audit_pcc_lastarria_tupungatito.py`
3. Decisión Task 7 (adopción Lastarria/Tupungatito si validan)
4. Cierre S62 + bloque arranque S63
