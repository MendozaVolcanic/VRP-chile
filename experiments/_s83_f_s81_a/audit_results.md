# Audit F-S81-A — gate Path D MODIS intra-radio
**Ventana**: 2026-04-12 → 2026-05-26 (45d)
**Sensor**: MODIS solo (gate por diseño)
**Tolerancia match temporal**: ±60 min
**Profiles**: enabled, disabled, baseline

## Profile: `enabled`
| Volcán | N rec | Detec | ALERTA | TP | FP | FN | Prec | Rec | F1 | FPs/mes | Ratio | R3viol | inner |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| PuyehueCordonCaulle | 104 | 104 | 0 | 0 | 104 | 0 | 0.0 | None | None | 69.33 | None | 1 | 20.0 |
| Villarrica | 101 | 101 | 0 | 0 | 101 | 0 | 0.0 | None | None | 67.33 | None | 4 | 5.0 |
| Lascar | 81 | 80 | 25 | 25 | 55 | 0 | 0.312 | 1.0 | 0.476 | 36.67 | 1.483 | 5 | 5.0 |
| Copahue | 97 | 97 | 0 | 0 | 97 | 0 | 0.0 | None | None | 64.67 | None | 14 | 4.0 |
| NevadosDeChillan | 95 | 93 | 0 | 0 | 93 | 0 | 0.0 | None | None | 62.0 | None | 24 | 5.0 |
| Llaima | 99 | 99 | 0 | 0 | 99 | 0 | 0.0 | None | None | 66.0 | None | 18 | 5.0 |
| Chaiten | 109 | 109 | 0 | 0 | 109 | 0 | 0.0 | None | None | 72.67 | None | 4 | 5.0 |
| PlanchonPeteroa | 99 | 98 | 0 | 0 | 98 | 0 | 0.0 | None | None | 65.33 | None | 11 | 3.0 |
| Lastarria | 86 | 85 | 0 | 0 | 85 | 0 | 0.0 | None | None | 56.67 | None | 9 | 3.0 |
| Isluga | 80 | 80 | 0 | 0 | 80 | 0 | 0.0 | None | None | 53.33 | None | 6 | 5.0 |
| Tupungatito | 99 | 99 | 0 | 0 | 99 | 0 | 0.0 | None | None | 66.0 | None | 10 | 7.0 |
| **TOTAL** | — | — | — | **25** | **1020** | **0** | **0.024** | **1.000** | — | **61.82** | — | **106** | — |

## Profile: `disabled`
| Volcán | N rec | Detec | ALERTA | TP | FP | FN | Prec | Rec | F1 | FPs/mes | Ratio | R3viol | inner |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| PuyehueCordonCaulle | 106 | 106 | 0 | 0 | 106 | 0 | 0.0 | None | None | 70.67 | None | 1 | 20.0 |
| Villarrica | 101 | 101 | 0 | 0 | 101 | 0 | 0.0 | None | None | 67.33 | None | 4 | 5.0 |
| Lascar | 81 | 80 | 25 | 25 | 55 | 0 | 0.312 | 1.0 | 0.476 | 36.67 | 1.483 | 5 | 5.0 |
| Copahue | 97 | 97 | 0 | 0 | 97 | 0 | 0.0 | None | None | 64.67 | None | 14 | 4.0 |
| NevadosDeChillan | 95 | 93 | 0 | 0 | 93 | 0 | 0.0 | None | None | 62.0 | None | 24 | 5.0 |
| Llaima | 99 | 99 | 0 | 0 | 99 | 0 | 0.0 | None | None | 66.0 | None | 18 | 5.0 |
| Chaiten | 109 | 109 | 0 | 0 | 109 | 0 | 0.0 | None | None | 72.67 | None | 4 | 5.0 |
| PlanchonPeteroa | 99 | 98 | 0 | 0 | 98 | 0 | 0.0 | None | None | 65.33 | None | 11 | 3.0 |
| Lastarria | 86 | 85 | 0 | 0 | 85 | 0 | 0.0 | None | None | 56.67 | None | 9 | 3.0 |
| Isluga | 80 | 80 | 0 | 0 | 80 | 0 | 0.0 | None | None | 53.33 | None | 6 | 5.0 |
| Tupungatito | 99 | 99 | 0 | 0 | 99 | 0 | 0.0 | None | None | 66.0 | None | 10 | 7.0 |
| **TOTAL** | — | — | — | **25** | **1022** | **0** | **0.024** | **1.000** | — | **61.94** | — | **106** | — |

## Profile: `baseline`
| Volcán | N rec | Detec | ALERTA | TP | FP | FN | Prec | Rec | F1 | FPs/mes | Ratio | R3viol | inner |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| PuyehueCordonCaulle | 111 | 111 | 0 | 0 | 111 | 0 | 0.0 | None | None | 74.0 | None | 1 | 20.0 |
| Villarrica | 101 | 101 | 0 | 0 | 101 | 0 | 0.0 | None | None | 67.33 | None | 16 | 5.0 |
| Lascar | 81 | 81 | 25 | 25 | 56 | 0 | 0.309 | 1.0 | 0.472 | 37.33 | 1.274 | 23 | 5.0 |
| Copahue | 97 | 97 | 0 | 0 | 97 | 0 | 0.0 | None | None | 64.67 | None | 53 | 4.0 |
| NevadosDeChillan | 95 | 94 | 0 | 0 | 94 | 0 | 0.0 | None | None | 62.67 | None | 47 | 5.0 |
| Llaima | 99 | 99 | 0 | 0 | 99 | 0 | 0.0 | None | None | 66.0 | None | 41 | 5.0 |
| Chaiten | 109 | 109 | 0 | 0 | 109 | 0 | 0.0 | None | None | 72.67 | None | 4 | 5.0 |
| PlanchonPeteroa | 99 | 99 | 0 | 0 | 99 | 0 | 0.0 | None | None | 66.0 | None | 12 | 3.0 |
| Lastarria | 86 | 86 | 0 | 0 | 86 | 0 | 0.0 | None | None | 57.33 | None | 9 | 3.0 |
| Isluga | 80 | 80 | 0 | 0 | 80 | 0 | 0.0 | None | None | 53.33 | None | 24 | 5.0 |
| Tupungatito | 99 | 99 | 0 | 0 | 99 | 0 | 0.0 | None | None | 66.0 | None | 8 | 7.0 |
| **TOTAL** | — | — | — | **25** | **1031** | **0** | **0.024** | **1.000** | — | **62.48** | — | **238** | — |

## Decisión adopción (umbrales objetivo)
- Precision MODIS Tier A: **≥ 0.70**
- Recall MIROVA: **≥ 0.85** (no regresión >5pp per-vol vs disabled/baseline)
- FPs/vol-mes MODIS: **≤ 15**
- R3 violators (eruption fuera inner_radius en `enabled`): **0**

### Δ enabled - disabled (per-volcano)
| Volcán | Δ TP | Δ FP | Δ FN | Δ Recall | Δ Precision | Δ FPs/mes |
|---|---:|---:|---:|---:|---:|---:|
| PuyehueCordonCaulle | +0 | -2 | +0 | n/a | +0.000 | -1.34 |
| Villarrica | +0 | +0 | +0 | n/a | +0.000 | +0.00 |
| Lascar | +0 | +0 | +0 | +0.000 | +0.000 | +0.00 |
| Copahue | +0 | +0 | +0 | n/a | +0.000 | +0.00 |
| NevadosDeChillan | +0 | +0 | +0 | n/a | +0.000 | +0.00 |
| Llaima | +0 | +0 | +0 | n/a | +0.000 | +0.00 |
| Chaiten | +0 | +0 | +0 | n/a | +0.000 | +0.00 |
| PlanchonPeteroa | +0 | +0 | +0 | n/a | +0.000 | +0.00 |
| Lastarria | +0 | +0 | +0 | n/a | +0.000 | +0.00 |
| Isluga | +0 | +0 | +0 | n/a | +0.000 | +0.00 |
| Tupungatito | +0 | +0 | +0 | n/a | +0.000 | +0.00 |
