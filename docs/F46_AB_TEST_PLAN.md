# F46 A/B test plan — gate consistencia MIR/NTI + threshold subido (Opción A+B)

**Sesión**: S77 · **Decisión**: A45 AUTORIZADO Nicolás · **Tag defensivo**: `pre-s77-f46-vrp-tir-fix` (sha 2bf909c8)
**Plan asociado**: `docs/F46_VRP_TIR_BUG_S76.md` §5.3 + §6
**Tests TDD**: `tests/test_vrp_tir_consistency_gate_f46.py` (5/5 PASS post-fix)

---

## 1. Objetivo

Cuantificar empíricamente sobre los 11 volcanes Tier A, ventana 2026-01-31 →
2026-05-17, el efecto del fix F46 (gate consistencia MIR/NTI + threshold
subido a `max(3K, 6σ)` sobre `vrp_tir_mw`).

Baseline operacional post-merge ya correrá con `enable_vrp_tir_consistency_gate: true`
desde el siguiente cron NRT. Este A/B se ejecuta **en paralelo** sobre data
aislada (`data_subdir`) para confirmar que la adopción operacional no introdujo
regresiones invisibles antes del primer ciclo de validación post-merge.

Snapshot del estado actual `data/mirova_equivalent/` pre-fix (15,949 records,
11 volcanes):

| Métrica | Valor pre-fix |
|---|---|
| Outliers `vrp_tir_mw > 1000 MW` | 143 |
| Outliers `vrp_tir_mw > 500 MW` | 268 |
| Outliers con `n_anomalous_pixels=0` (caso Chaiten patognomónico) | 25 |
| Distribución vol top-5: PCC=50, Villarrica=30, Chaiten=27, Llaima=9, LagunaDelMaule=8 | — |

---

## 2. Perfiles aislados

Clonar `pipeline/profiles/mirova_equivalent.yaml` a:

### 2.1 `pipeline/profiles/mirova_equivalent_f46_disabled.yaml` (control legacy)

```yaml
extends: mirova_equivalent
enable_vrp_tir_consistency_gate: false   # comportamiento pre-S77 (max(0.5, 4σ), sin gate)
output:
  data_subdir: experimental/f46_disabled
```

### 2.2 `pipeline/profiles/mirova_equivalent_f46_enabled.yaml` (fix Opción A+B)

```yaml
extends: mirova_equivalent
enable_vrp_tir_consistency_gate: true    # Opción A+B (default post-S77)
vrp_tir_floor_k: 3.0
vrp_tir_n_sigma: 6.0
output:
  data_subdir: experimental/f46_enabled
```

Ambos perfiles solo cambian flags de F46 + `data_subdir` — el resto (paths,
dual-ROI, Test 1, kernel_bg, D9 cap) heredan operacional.

---

## 3. Ejecución (local, no GitHub Actions por timeout 50min)

Per CLAUDE.md S15 aprendizaje: reprocesos >1 día = máquina local. 11 volcanes
× 3.5 meses × 3 sensores cabe en 6-8h locales.

```bash
# Worktree dedicado A44
git worktree add ../VRP-Chile-s77-f46-ab origin/main
cd ../VRP-Chile-s77-f46-ab

# Reproc legacy
for vol in Chaiten Copahue Isluga LagunaDelMaule Lascar Lastarria Llaima \
           NevadosDeChillan PlanchonPeteroa PuyehueCordonCaulle \
           Tupungatito Villarrica; do
    python scripts/run_pipeline.py \
        --profile mirova_equivalent_f46_disabled \
        --volcano $vol \
        --start 2026-01-31 --end 2026-05-17
done

# Reproc fix
for vol in ...; do
    python scripts/run_pipeline.py \
        --profile mirova_equivalent_f46_enabled \
        --volcano $vol \
        --start 2026-01-31 --end 2026-05-17
done
```

`max-parallel: 1` por race condition documentada (CLAUDE.md S25, mismo archivo
JSON por volcán).

---

## 4. Métricas a comparar

Por volcán y agregado Tier A, comparar `f46_disabled` vs `f46_enabled`:

| Métrica | Threshold de aceptación |
|---|---|
| Conteo `vrp_tir_mw > 1000 MW` | reducir 143 → 0 o ≤5 (residuales Stefan-Boltzmann legítimos sobre clusters MIR confirmados) |
| Conteo `vrp_tir_mw > 500 MW` | reducir 268 → ≤30 |
| Conteo records con `n_anomalous_pixels=0` AND `vrp_tir_mw > 100 MW` | 25 → 0 (gate A los veta por construcción) |
| Mediana `vrp_tir_mw` por volcán | Caída ≤30% sobre Lastarria (Tier A con TIR legítimo crónico — fumarolas) |
| Caso Chaitén 2026-03-25 05:18 SNPP | `vrp_tir_mw = 0` post-fix (vs ~6872 MW pre-fix) |
| Mediana ratio `vrp_total_ours / vrp_mirova` Lastarria | Permanecer en [0.7, 1.4] (no degradar paridad MIROVA) |
| `vmax(vrp_tir_mw)` PP | ≤100 MW post-fix (margen 1.7× sobre Aguilera 2021 max 59 MW lago cratérico) |

### 4.1 Foco Lastarria (control de no-regresión TIR legítimo)

Lastarria tiene 71 alertas MIROVA con mediana 0.11 MW VRP en consolidated.
Cualquier caída >10pp en recall Lastarria post-fix es **bloqueante** —
implica que el gate consistencia o el threshold subido están vetando señal
real validada por MIROVA.

### 4.2 Foco Planchón-Peteroa (anchor numérico Aguilera 2021)

PP tiene ground truth físico publicado: Qvolc 7-59 MW lago cratérico
(Aguilera 2021 doi:10.3389/feart.2021.722056). Post-fix, `vrp_tir_mw_PP` en
noches sin cirrus debe caer dentro de 7-59 MW. Si post-fix sigue >100 MW
sobre PP en >5% de noches, el threshold puede necesitar ajuste fino
(siguiente A/B iteración con `vrp_tir_n_sigma: 8.0`).

---

## 5. Caveats

- **No mergear** sin ejecutar este A/B (regla S33 vinculante adopción operacional
  metodológica). El merge a main ya activa el flag default — por eso este
  plan se ejecuta **en paralelo** con monitoreo de primeros 5 cron cycles
  NRT operacional.
- Si tras 5 cron cycles operacional (~10h) los nuevos records reflejan
  `vrp_tir_mw` razonable (<100 MW) en Lastarria/PP/Lascar sin regresión
  en n_anomalous_pixels o `vrp_mir_mw`, rollout adoptado. Si Lastarria
  pierde >10pp recall → rollback inmediato vía `git revert` + tag
  `pre-s77-f46-vrp-tir-fix` recoverable.
- Tag defensivo `pre-s77-f46-vrp-tir-fix` permite rollback total de
  data/mirova_equivalent/ si A/B revela regresión grave post-merge.

---

## 6. Próximos pasos (post-A/B)

1. Si A/B confirma 143 → ≤5 outliers + 0 regresiones recall Lastarria/PP:
   documentar resultado en `docs/MIROVA_DIVERGENCES.md` (cierre F46) y
   marcar fix como ADOPTED.
2. Considerar la versión más estricta `vrp_tir_n_sigma: 8.0` solo si PP
   sigue >100 MW en >5% noches post-fix.
3. Aplicar el mismo patrón helper a `process_modis.py` si el audit
   detecta outliers análogos en MODIS B31 (TIR MODIS no se cubrió en
   este fix).
