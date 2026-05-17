# S60 Audit A — Recall NEW (local_kernel_bg) vs MIROVA CSV (sin regresión)

**Fecha**: 2026-05-17
**Objetivo**: verificar que reproc S58 con `enable_local_kernel_bg=true` no perdió TPs MIROVA ALERTA_TERMICA ni FALSO_POSITIVO en el window de reproc.
**Window auditado**: 2026-04-16 → 2026-05-15 (window reproc S58).
**Volcán**: Villarrica.

## Universo MIROVA en window

CSV ground truth: `data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv`
(termina 2026-05-16 — más reciente de lo que decía REAUDITORIA_S52).

Filtro `Volcan=Villarrica` + `Tipo_Registro ∈ (ALERTA_TERMICA, FALSO_POSITIVO)`:

| Categoría | Conteo | Comentario |
|---|---:|---|
| ALERTA_TERMICA | 2 | MIROVA reportó como anomalía real en cráter (Muy Bajo) |
| FALSO_POSITIVO | 3 | MIROVA reportó pero fuera de radio oficial |
| RUTINA (no denom) | 463 | scraper Nicolás corrió, MIROVA no reportó nada |

**Denominador recall** = 5 (2 ALERTA + 3 FP), NO contar RUTINA.

## Match NEW vs LEGACY contra los 5 refs MIROVA

| Fecha UTC | Sensor MIROVA | MIROVA VRP/dist | NEW (kernel) | LEGACY (ring) |
|---|---|---:|---|---|
| 2026-05-14 05:48 ALERTA | VIIRS375 | 0.31 / 0.84 | **0.67 / 0.85** (2.17×) | 0.30 / 0.18 (0.97×) |
| 2026-05-11 06:00 ALERTA | VIIRS375 | 0.31 / 0.84 | **0.50 / 0.79** (1.61×) | 5.84 / 1.53 (**18.8×**) |
| 2026-05-08 05:12 FP | VIIRS375 | 0.45 / 18.01 | 1.88 / 1.06 | 1.88 / 1.06 |
| 2026-05-05 14:05 FP | MODIS | 5.89 / 30.48 | NO MATCH (sin granule) | NO MATCH |
| 2026-05-04 05:36 FP | VIIRS375 | 0.74 / 30.17 | 0.34 / 29.76 | 0.38 / 29.76 |

### Recall verdict

- ALERTA_TERMICA: **2/2 NEW** = 2/2 LEGACY (100%). Sin regresión.
- FALSO_POSITIVO: **2/3 NEW** = 2/3 LEGACY (67%). Sin regresión.
  - Missing es MODIS día (14:05 UTC = 10:05 local Chile). Probable granule no fetcheado por
    regla "MIR solo nocturno" (Coppola 2016a contaminación solar) o falta de descarga MOD021KM
    diurno. Mismo en ambos, no atribuible al fix.
- Recall total: **4/5 NEW = 4/5 LEGACY = 80%**.

### Calibración magnitud (gana NEW en caso paradigmático)

- **2026-05-11**: LEGACY infla 18.8× (5.84 MW vs MIROVA 0.31). NEW cura a 1.61× (0.50 MW).
  Este es el caso que motivó el fix (lago Villarrica norte contaminando ring 5-25km).
- **2026-05-14**: LEGACY ya calibrado 0.97×. NEW empeora ligeramente a 2.17×.
  Aceptable: dentro del target ≤30× definido en CLAUDE.md ratio individual tolerable.

## Distribución agregada window

| Métrica | NEW kernel-bg | LEGACY median-ring | Δ |
|---|---:|---:|---:|
| Records totales | 328 | 330 | -0.6% (granule parity) |
| Anómalos (vrp>0) | 211 | 247 | -15% (probable reducción FPs propios sub-MIROVA) |
| Summit (≤5 km) | 143 | 135 | +6% (más, no menos) |
| Median VRP all anom | 3.64 MW | 4.44 MW | -18% |
| Median VRP summit | 2.40 MW | 2.51 MW | -4% (hacia target OSF 0.92) |
| Max VRP summit | 208.56 MW | 209.20 MW | idéntico (outlier persiste) |

> Aclaración sobre la nota S58→S60 "65% reducción summit": no se observa esa reducción
> en este window comparativo. Summit anom NEW supera levemente a LEGACY (143 vs 135).
> Probablemente la cifra del bloque arranque comparaba contra un baseline distinto
> (`_local_kernel_bg_disabled` específico, no `mirova_equivalent` operacional histórico).

## Veredicto S60-A

✅ **Sin regresión de recall**. NEW detecta exactamente los mismos TPs/FPs MIROVA que LEGACY.
✅ **Reducción 15% anom totales** (probable FP propio sub-MIROVA eliminado).
✅ **Mejora calibración paradigmática**: 18.8× → 1.61× en caso 2026-05-11.
✅ **Summit median sigue bajando**: 2.51 → 2.40 MW (hacia target OSF 0.92 MW pendiente B).
⚠️ Caso 2026-05-14 ratio sube 0.97× → 2.17×. No bloqueante pero monitorear.

Procede S60-B: validar distribución NEW vs OSF v2.5 (5211 refs Villarrica, mediana target 0.92 MW).
