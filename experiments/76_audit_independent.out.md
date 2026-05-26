# Audit independiente — R3 implementación re-derivada

Window: 2026-01-29 -> 2026-04-29
Política R3: este script NO comparte código con frontend ni audits previos.
Si discrepa con experiments/65, hay bug en alguno.


## Profile: mirova_equivalent (operacional Phase 1 ON)

| Volcán | Refs | TPs | Recall % | Ratio mediano |
|---|---:|---:|---:|---:|
| Chaiten | 11 | 10 | 90.9 | 14.47 |
| Copahue | 1 | 1 | 100.0 | 3.18 |
| Isluga | 68 | 47 | 69.1 | 0.94 |
| Lascar | 224 | 126 | 56.2 | 1.19 |
| Lastarria | 63 | 27 | 42.9 | 5.71 |
| NevadosDeChillan | 4 | 0 | 0.0 | NA |
| PlanchonPeteroa | 31 | 4 | 12.9 | 0.76 |
| PuyehueCordonCaulle | 58 | 54 | 93.1 | 12.10 |
| Tupungatito | 68 | 25 | 36.8 | 0.54 |
| Villarrica | 3 | 1 | 33.3 | 1.66 |

**GLOBAL — Recall: 55.6% (295/531). Ratio mediano: 1.39x.**

## Profile: filter_OFF (control, Phase 1 OFF)

| Volcán | Refs | TPs | Recall % | Ratio mediano |
|---|---:|---:|---:|---:|
| Chaiten | 11 | 10 | 90.9 | 18.29 |
| Copahue | 1 | 1 | 100.0 | 3.18 |
| Isluga | 68 | 53 | 77.9 | 1.07 |
| Lascar | 224 | 146 | 65.2 | 1.26 |
| Lastarria | 63 | 63 | 100.0 | 18.49 |
| NevadosDeChillan | 4 | 0 | 0.0 | NA |
| PlanchonPeteroa | 31 | 30 | 96.8 | 16.03 |
| PuyehueCordonCaulle | 58 | 55 | 94.8 | 12.10 |
| Tupungatito | 68 | 33 | 48.5 | 0.71 |
| Villarrica | 3 | 3 | 100.0 | 64.92 |

**GLOBAL — Recall: 74.2% (394/531). Ratio mediano: 2.53x.**

## Profile: filter_ON (Phase 1 explicit ON)

| Volcán | Refs | TPs | Recall % | Ratio mediano |
|---|---:|---:|---:|---:|
| Chaiten | 11 | 10 | 90.9 | 14.47 |
| Copahue | 1 | 1 | 100.0 | 3.18 |
| Isluga | 68 | 47 | 69.1 | 0.94 |
| Lascar | 224 | 126 | 56.2 | 1.19 |
| Lastarria | 63 | 27 | 42.9 | 5.71 |
| NevadosDeChillan | 4 | 0 | 0.0 | NA |
| PlanchonPeteroa | 31 | 4 | 12.9 | 0.76 |
| PuyehueCordonCaulle | 58 | 54 | 93.1 | 12.10 |
| Tupungatito | 68 | 25 | 36.8 | 0.54 |
| Villarrica | 3 | 1 | 33.3 | 1.66 |

**GLOBAL — Recall: 55.6% (295/531). Ratio mediano: 1.39x.**

## Profile: D4 (L_bg global)

| Volcán | Refs | TPs | Recall % | Ratio mediano |
|---|---:|---:|---:|---:|
| Chaiten | 11 | 10 | 90.9 | 14.47 |
| Copahue | 1 | 1 | 100.0 | 3.18 |
| Isluga | 68 | 47 | 69.1 | 0.94 |
| Lascar | 224 | 127 | 56.7 | 1.19 |
| Lastarria | 63 | 27 | 42.9 | 5.71 |
| NevadosDeChillan | 4 | 0 | 0.0 | NA |
| PlanchonPeteroa | 31 | 4 | 12.9 | 0.76 |
| PuyehueCordonCaulle | 58 | 54 | 93.1 | 12.10 |
| Tupungatito | 68 | 25 | 36.8 | 0.54 |
| Villarrica | 3 | 1 | 33.3 | 1.66 |

**GLOBAL — Recall: 55.7% (296/531). Ratio mediano: 1.39x.**

================================================================================

## Comparación cross-profile

| Profile | Recall % | Ratio mediano |
|---|---:|---:|
| mirova_equivalent (operacional Phase 1 ON) | 55.6 | 1.39x |
| filter_OFF (control, Phase 1 OFF) | 74.2 | 2.53x |
| filter_ON (Phase 1 explicit ON) | 55.6 | 1.39x |
| D4 (L_bg global) | 55.7 | 1.39x |
