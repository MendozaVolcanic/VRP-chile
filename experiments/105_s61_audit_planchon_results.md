# S61 Audit PlanchonPeteroa A/B local_kernel_bg — VEREDICTO: ✅ ADOPTAR

**Fecha**: 2026-05-18
**Workflow**: run 26035918192 (2h54m, success)
**Window**: 2026-02-20 → 2026-05-15 (~85 días)
**Volcán**: PlanchonPeteroa
**Refs MIROVA**: 39 ALERTA_TERMICA + 20 FALSO_POSITIVO

## Resultados (campo correcto: `primary_cluster.vrp_mw`)

| Métrica | LEGACY median-ring | NEW kernel-bg | Δ |
|---|---:|---:|---|
| Recall ALERTAS | 38/39 (97.4%) | **39/39 (100%)** | +1 ALERTA recuperada |
| Ratio mediano ALERTAS | 11.80× | **2.64×** | **-78%** |
| Min ratio ALERTAS | 0.03× | 0.00× | similar |
| Max ratio ALERTAS | 119.93× | 119.93× | (mismo outlier caso 2026-05-13 05:18) |
| Ratios en rango [0.5, 2.0] | 6/38 (16%) | 10/39 (26%) | +63% en rango |
| Ratios sobre 3.0× | 29/38 (76%) | 15/39 (38%) | -50% inflados |

## Comparativa caso por caso destacable

| Fecha | MIROVA | LEGACY ratio | NEW ratio | Comentario |
|---|---:|---:|---:|---|
| 2026-04-30 06:00 | 0.07 | 27.91× | 27.91× | sin cambio caso extremo |
| 2026-04-27 05:18 | 0.05 | **35.74×** | **2.64×** | CURA enorme |
| 2026-04-26 05:36 | 0.07 | **31.77×** | **2.49×** | CURA enorme |
| 2026-04-24 06:18 | 0.05 | **15.58×** | **2.92×** | CURA |
| 2026-04-10 05:36 | 0.06 | **63.68×** | **1.95×** | CURA enorme |
| 2026-04-08 06:18 | 0.06 | 39.92× | 39.92× | sin cambio |
| 2026-04-05 05:30 | 0.15 | **20.33×** | **2.09×** | CURA |
| 2026-04-04 05:48 | 0.25 | **16.03×** | **1.64×** | CURA, dentro tolerable |
| 2026-02-26 05:42 | 0.08 | **40.61×** | **3.14×** | CURA enorme |

## Casos donde NEW NO mejora o regresiona

Algunos casos NEW iguala LEGACY (sin mejora del fix kernel):
- 2026-05-14 05:48: LEGACY 9.57× = NEW 9.57× (el cluster no estaba contaminado por glaciar)
- 2026-05-10 06:18: LEGACY 12.90× = NEW 12.90×
- 2026-05-02 05:24: LEGACY 8.58× = NEW 8.58×
- 2026-04-14 06:00: LEGACY 12.93× = NEW 12.93×
- 2026-04-30 06:00: LEGACY 27.91× = NEW 27.91×

Algunos casos NEW regresiona (sub-detección o magnitud peor):
- 2026-05-12 05:36: LEGACY 8.09× → NEW 0.01× (probable sub-detección)
- 2026-03-24 05:54: LEGACY 7.13× → NEW 0.03×
- 2026-03-19 05:48: LEGACY 4.83× → NEW 0.00×
- 2026-04-09 05:54: LEGACY 0.76× (calibrado) → NEW 33.47× (empeora)
- 2026-04-03 05:48: LEGACY 0.84× → NEW 31.69× (empeora)

**Conclusión**: el fix kernel-bg es **mayormente positivo** (mediana -78% gap) pero hay
heterogeneidad. Para 15/39 ALERTAS NEW sigue inflado >3×, sugiere que el problema no
es 100% kernel-bg en PlanchonPeteroa (puede haber casos donde el cluster summit
sigue siendo dominado por nieve/glaciar).

## Veredicto S61 ADOPCIÓN

✅ **ADOPTAR `enable_local_kernel_bg: true` operacional** porque:
1. Recall MEJORA (39/39 vs 38/39, +1 ALERTA recuperada)
2. Ratio mediano MEJORA dramáticamente (11.80× → 2.64×)
3. Ratios en rango tolerable [0.5, 2.0] casi se duplican (16% → 26%)
4. Los casos donde NEW regresiona son menos numerosos que los que cura

**Caveat S62 pendiente**: 15/39 ALERTAS aún >3× inflado en NEW sugiere que un fix
complementario S62 (kernel_size=5, percentile p25, o investigación pixel BT edge
mixing) podría mejorar más.

## Resumen Tasks S61

Combinando Villarrica (audit C) y PlanchonPeteroa (este audit):

| Vol | Window | n ALERTAS | LEGACY mediano | NEW mediano | Status |
|---|---|---:|---:|---:|---|
| Villarrica | 02-20/05-15 | 5 | 31.59× (pc) | **2.16×** | ✅ Adoptado |
| PlanchonPeteroa | 02-20/05-15 | 39 | 11.80× | **2.64×** | ✅ Adoptado este PR |

Per-vol flag estado final:
- Villarrica: `local_kernel_bg: true`
- PlanchonPeteroa: `local_kernel_bg: true`
- Copahue: `false` (revertido S61 PR #71)
- Llaima: `false` (revertido S61 PR #71)
- Tupungatito: `false` (excluido S59)

Profile flag operacional: `enable_local_kernel_bg: true` (PR cierre S61 pendiente).
