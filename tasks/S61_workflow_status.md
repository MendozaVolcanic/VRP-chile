# S61 PlanchonPeteroa A/B Workflow Status

## Run info

- **Run ID**: 26035918192
- **URL**: https://github.com/MendozaVolcanic/VRP-chile/actions/runs/26035918192
- **Triggered**: 2026-05-18 13:16:46 UTC
- **Workflow**: `reproc-ab-local-kernel-bg-pp.yml` (S61 Task 1)
- **Window**: 2026-02-20 → 2026-05-15 (~85 días)
- **ETA**: ~3-4h (timeout 300 min via PR #68 S60 ya extendido)
- **Profile target**: `_local_kernel_bg_enabled`
- **Volcano**: PlanchonPeteroa

## Status monitoring

```bash
gh run view 26035918192 -R MendozaVolcanic/VRP-chile --json status,conclusion
```

## Expected output al completar

- `data/_local_kernel_bg_enabled/PlanchonPeteroa.json` commiteado a main
- Records con `datetime_utc` rango 2026-02-20 → 2026-05-15
- ~600-800 records totales (estimación basada en Villarrica con window similar)

## Resultado audit Task 3

Pendiente ejecución hasta workflow completo.
