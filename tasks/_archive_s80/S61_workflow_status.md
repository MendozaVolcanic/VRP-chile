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

---

## Task 5 edit ready-to-apply (CONDICIONAL al audit Task 3)

**Solo aplicar si Task 3 reporta**: `✅ ADOPTAR` (recall NEW ≥ LEGACY Y ratio mediano NEW < LEGACY).

Edit en `pipeline/profiles/mirova_equivalent.yaml` después de línea 247:

```yaml
  enable_dual_roi_second_pass: true

  # S61 ADOPCIÓN — kernel local 3×3 (Coppola 2024 L1129, Coppola 2016a L357,
  # Campus 2024 L119) reemplaza median(ring 5-25km) en cálculo background L_bg.
  # Per-vol opt-in via local_kernel_bg flag en volcanoes.yaml.
  # Activos S61:
  #   - Villarrica (audit S60 audit C: ratio 33× → 2.16× sobre 5 ALERTAS reales)
  #   - PlanchonPeteroa (audit S61: ratio 15× → <Y>× sobre 39 ALERTAS reales)
  # Inactivos: Copahue (1.14× calibrado), Llaima (1.01× calibradísimo),
  # Tupungatito (S59 false, revisión S62 pendiente A/B), otros vols no auditados.
  enable_local_kernel_bg: true
```

**Si audit reporta** `⚠️ MIXTO` o `❌ NO ADOPTAR`:
1. NO aplicar este edit
2. Revertir PlanchonPeteroa en `volcanoes.yaml:527` a `local_kernel_bg: false`
3. Mantener Villarrica `local_kernel_bg: true` pero profile flag queda en false → ningún vol recibe el fix operacional
4. Documentar refutación de H_S61_PLANCHON_KERNEL_BG en HYPOTHESIS_LOG

---

## Audit script comando exacto

```bash
git pull --rebase origin main  # importante: traer JSON workflow PP commiteado
python experiments/105_s61_audit_planchon_kernel_bg.py 2>&1 | tee experiments/105_s61_audit_planchon_results.txt
```

---

## Hallazgos paralelos S61 (referencia)

| Vol | LEGACY/MIROVA gap (window 04-16/05-15) | Acción S61 | Pendiente S62 |
|---|---:|---|---|
| Villarrica | 5.68× | Adoptado true (audit C valida) | refinamiento kernel_size=5 |
| PlanchonPeteroa | 15.03× | A/B corriendo (Task 3) | post-audit |
| Copahue | 1.14× | Revertir false (PR #71) | — |
| Llaima | 1.01× | Revertir false (PR #71) | — |
| Tupungatito | 9.80× | mantener false S59 | A/B revisión |
| Lascar | 1.04× | mantener false | — |
| Lastarria | 3.99× | mantener false (no auditado) | A/B candidato |
| Isluga | 4.80× | mantener false (no auditado) | A/B candidato |
| PCC | 52.77× ‼️ | mantener false | A/B alta prioridad |
| Chaiten / NdC | n bajo | — | esperar más ALERTAS |
