# Audit F-S81-B' — gate intra-radio second_pass_recapture (S85)
**Ventana**: 2026-04-12 → 2026-05-26 (45d)
**Sensores**: MODIS + VIIRS (helper integrado en los 3 process_*.py)
**Tolerancia match temporal**: ±60 min
**Profiles**: enabled, disabled, baseline

## Profile: `enabled` — sensor MODIS
| Volcán | N rec | Detec | ALERTA | TP | FP | FN | Prec | Rec | F1 | FPs/mes | Ratio | R3viol | n_2nd_agg | inner |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| PuyehueCordonCaulle | 106 | 106 | 0 | 0 | 106 | 0 | 0.0 | None | None | 70.67 | None | 1 | 17359 | 20.0 |
| Villarrica | 101 | 101 | 0 | 0 | 101 | 0 | 0.0 | None | None | 67.33 | None | 3 | 1150 | 5.0 |
| Lascar | 81 | 80 | 25 | 25 | 55 | 0 | 0.312 | 1.0 | 0.476 | 36.67 | 1.483 | 5 | 991 | 5.0 |
| Copahue | 97 | 97 | 0 | 0 | 97 | 0 | 0.0 | None | None | 64.67 | None | 14 | 741 | 4.0 |
| NevadosDeChillan | 95 | 93 | 0 | 0 | 93 | 0 | 0.0 | None | None | 62.0 | None | 22 | 1108 | 5.0 |
| Llaima | 99 | 99 | 0 | 0 | 99 | 0 | 0.0 | None | None | 66.0 | None | 18 | 1074 | 5.0 |
| Chaiten | 109 | 109 | 0 | 0 | 109 | 0 | 0.0 | None | None | 72.67 | None | 2 | 1182 | 5.0 |
| PlanchonPeteroa | 99 | 97 | 0 | 0 | 97 | 0 | 0.0 | None | None | 64.67 | None | 7 | 359 | 3.0 |
| Lastarria | 86 | 85 | 0 | 0 | 85 | 0 | 0.0 | None | None | 56.67 | None | 9 | 354 | 3.0 |
| Isluga | 80 | 80 | 0 | 0 | 80 | 0 | 0.0 | None | None | 53.33 | None | 6 | 892 | 5.0 |
| Tupungatito | 99 | 99 | 0 | 0 | 99 | 0 | 0.0 | None | None | 66.0 | None | 11 | 2337 | 7.0 |
| **TOTAL** | — | — | — | **25** | **1021** | **0** | **0.024** | **1.000** | — | **61.88** | — | **98** | **27547** | — |

## Profile: `enabled` — sensor VIIRS
| Volcán | N rec | Detec | ALERTA | TP | FP | FN | Prec | Rec | F1 | FPs/mes | Ratio | R3viol | n_2nd_agg | inner |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| PuyehueCordonCaulle | 414 | 296 | 7 | 7 | 289 | 0 | 0.024 | 1.0 | 0.046 | 192.67 | 0.188 | 1 | 1458 | 20.0 |
| Villarrica | 404 | 220 | 0 | 0 | 220 | 0 | 0.0 | None | None | 146.67 | None | 2 | 68 | 5.0 |
| Lascar | 334 | 234 | 43 | 43 | 191 | 0 | 0.184 | 1.0 | 0.31 | 127.33 | 0.387 | 6 | 229 | 5.0 |
| Copahue | 386 | 189 | 0 | 0 | 189 | 0 | 0.0 | None | None | 126.0 | None | 6 | 80 | 4.0 |
| NevadosDeChillan | 396 | 39 | 1 | 0 | 39 | 1 | 0.0 | 0.0 | None | 26.0 | None | 8 | 79 | 5.0 |
| Llaima | 406 | 203 | 0 | 0 | 203 | 0 | 0.0 | None | None | 135.33 | None | 13 | 105 | 5.0 |
| Chaiten | 426 | 200 | 0 | 0 | 200 | 0 | 0.0 | None | None | 133.33 | None | 1 | 140 | 5.0 |
| PlanchonPeteroa | 375 | 174 | 3 | 3 | 171 | 0 | 0.017 | 1.0 | 0.034 | 114.0 | 4.389 | 7 | 121 | 3.0 |
| Lastarria | 340 | 182 | 0 | 0 | 182 | 0 | 0.0 | None | None | 121.33 | None | 4 | 106 | 3.0 |
| Isluga | 322 | 203 | 10 | 10 | 193 | 0 | 0.049 | 1.0 | 0.094 | 128.67 | 2.237 | 3 | 197 | 5.0 |
| Tupungatito | 374 | 208 | 5 | 5 | 203 | 0 | 0.024 | 1.0 | 0.047 | 135.33 | 7.958 | 6 | 107 | 7.0 |
| **TOTAL** | — | — | — | **68** | **2080** | **1** | **0.032** | **0.986** | — | **126.06** | — | **57** | **2690** | — |

## Profile: `disabled` — sensor MODIS
| Volcán | N rec | Detec | ALERTA | TP | FP | FN | Prec | Rec | F1 | FPs/mes | Ratio | R3viol | n_2nd_agg | inner |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| PuyehueCordonCaulle | 106 | 106 | 0 | 0 | 106 | 0 | 0.0 | None | None | 70.67 | None | 1 | 19461 | 20.0 |
| Villarrica | 101 | 101 | 0 | 0 | 101 | 0 | 0.0 | None | None | 67.33 | None | 4 | 5127 | 5.0 |
| Lascar | 81 | 80 | 25 | 25 | 55 | 0 | 0.312 | 1.0 | 0.476 | 36.67 | 1.483 | 5 | 3957 | 5.0 |
| Copahue | 97 | 97 | 0 | 0 | 97 | 0 | 0.0 | None | None | 64.67 | None | 14 | 4337 | 4.0 |
| NevadosDeChillan | 95 | 93 | 0 | 0 | 93 | 0 | 0.0 | None | None | 62.0 | None | 24 | 4926 | 5.0 |
| Llaima | 99 | 99 | 0 | 0 | 99 | 0 | 0.0 | None | None | 66.0 | None | 18 | 4321 | 5.0 |
| Chaiten | 109 | 109 | 0 | 0 | 109 | 0 | 0.0 | None | None | 72.67 | None | 4 | 5887 | 5.0 |
| PlanchonPeteroa | 99 | 98 | 0 | 0 | 98 | 0 | 0.0 | None | None | 65.33 | None | 11 | 4967 | 3.0 |
| Lastarria | 86 | 85 | 0 | 0 | 85 | 0 | 0.0 | None | None | 56.67 | None | 9 | 3408 | 3.0 |
| Isluga | 80 | 80 | 0 | 0 | 80 | 0 | 0.0 | None | None | 53.33 | None | 6 | 3517 | 5.0 |
| Tupungatito | 99 | 99 | 0 | 0 | 99 | 0 | 0.0 | None | None | 66.0 | None | 10 | 7338 | 7.0 |
| **TOTAL** | — | — | — | **25** | **1022** | **0** | **0.024** | **1.000** | — | **61.94** | — | **106** | **67246** | — |

## Profile: `disabled` — sensor VIIRS
| Volcán | N rec | Detec | ALERTA | TP | FP | FN | Prec | Rec | F1 | FPs/mes | Ratio | R3viol | n_2nd_agg | inner |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| PuyehueCordonCaulle | 414 | 296 | 7 | 7 | 289 | 0 | 0.024 | 1.0 | 0.046 | 192.67 | 0.188 | 1 | 1458 | 20.0 |
| Villarrica | 404 | 221 | 0 | 0 | 221 | 0 | 0.0 | None | None | 147.33 | None | 3 | 71 | 5.0 |
| Lascar | 334 | 235 | 43 | 43 | 192 | 0 | 0.183 | 1.0 | 0.309 | 128.0 | 0.387 | 7 | 232 | 5.0 |
| Copahue | 386 | 189 | 0 | 0 | 189 | 0 | 0.0 | None | None | 126.0 | None | 6 | 91 | 4.0 |
| NevadosDeChillan | 396 | 42 | 1 | 0 | 42 | 1 | 0.0 | 0.0 | None | 28.0 | None | 11 | 94 | 5.0 |
| Llaima | 406 | 204 | 0 | 0 | 204 | 0 | 0.0 | None | None | 136.0 | None | 14 | 128 | 5.0 |
| Chaiten | 426 | 200 | 0 | 0 | 200 | 0 | 0.0 | None | None | 133.33 | None | 1 | 141 | 5.0 |
| PlanchonPeteroa | 375 | 174 | 3 | 3 | 171 | 0 | 0.017 | 1.0 | 0.034 | 114.0 | 4.389 | 7 | 126 | 3.0 |
| Lastarria | 340 | 183 | 0 | 0 | 183 | 0 | 0.0 | None | None | 122.0 | None | 5 | 110 | 3.0 |
| Isluga | 322 | 204 | 10 | 10 | 194 | 0 | 0.049 | 1.0 | 0.093 | 129.33 | 2.237 | 4 | 200 | 5.0 |
| Tupungatito | 374 | 208 | 5 | 5 | 203 | 0 | 0.024 | 1.0 | 0.047 | 135.33 | 7.958 | 6 | 109 | 7.0 |
| **TOTAL** | — | — | — | **68** | **2088** | **1** | **0.032** | **0.986** | — | **126.55** | — | **65** | **2760** | — |

## Profile: `baseline` — sensor MODIS
| Volcán | N rec | Detec | ALERTA | TP | FP | FN | Prec | Rec | F1 | FPs/mes | Ratio | R3viol | n_2nd_agg | inner |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| PuyehueCordonCaulle | 111 | 111 | 0 | 0 | 111 | 0 | 0.0 | None | None | 74.0 | None | 1 | 19852 | 20.0 |
| Villarrica | 101 | 101 | 0 | 0 | 101 | 0 | 0.0 | None | None | 67.33 | None | 16 | 4579 | 5.0 |
| Lascar | 81 | 81 | 25 | 25 | 56 | 0 | 0.309 | 1.0 | 0.472 | 37.33 | 1.274 | 23 | 953 | 5.0 |
| Copahue | 97 | 97 | 0 | 0 | 97 | 0 | 0.0 | None | None | 64.67 | None | 53 | 729 | 4.0 |
| NevadosDeChillan | 95 | 94 | 0 | 0 | 94 | 0 | 0.0 | None | None | 62.67 | None | 47 | 856 | 5.0 |
| Llaima | 99 | 99 | 0 | 0 | 99 | 0 | 0.0 | None | None | 66.0 | None | 41 | 678 | 5.0 |
| Chaiten | 109 | 109 | 0 | 0 | 109 | 0 | 0.0 | None | None | 72.67 | None | 4 | 5887 | 5.0 |
| PlanchonPeteroa | 99 | 99 | 0 | 0 | 99 | 0 | 0.0 | None | None | 66.0 | None | 12 | 4968 | 3.0 |
| Lastarria | 86 | 86 | 0 | 0 | 86 | 0 | 0.0 | None | None | 57.33 | None | 9 | 3418 | 3.0 |
| Isluga | 80 | 80 | 0 | 0 | 80 | 0 | 0.0 | None | None | 53.33 | None | 24 | 722 | 5.0 |
| Tupungatito | 99 | 99 | 0 | 0 | 99 | 0 | 0.0 | None | None | 66.0 | None | 8 | 7255 | 7.0 |
| **TOTAL** | — | — | — | **25** | **1031** | **0** | **0.024** | **1.000** | — | **62.48** | — | **238** | **49897** | — |

## Profile: `baseline` — sensor VIIRS
| Volcán | N rec | Detec | ALERTA | TP | FP | FN | Prec | Rec | F1 | FPs/mes | Ratio | R3viol | n_2nd_agg | inner |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| PuyehueCordonCaulle | 404 | 350 | 7 | 7 | 343 | 0 | 0.02 | 1.0 | 0.039 | 228.67 | 0.188 | 1 | 1245 | 20.0 |
| Villarrica | 399 | 269 | 0 | 0 | 269 | 0 | 0.0 | None | None | 179.33 | None | 50 | 36 | 5.0 |
| Lascar | 332 | 233 | 43 | 43 | 190 | 0 | 0.185 | 1.0 | 0.312 | 126.67 | 0.642 | 11 | 38 | 5.0 |
| Copahue | 380 | 248 | 0 | 0 | 248 | 0 | 0.0 | None | None | 165.33 | None | 68 | 27 | 4.0 |
| NevadosDeChillan | 387 | 69 | 1 | 0 | 69 | 1 | 0.0 | 0.0 | None | 46.0 | None | 28 | 47 | 5.0 |
| Llaima | 401 | 229 | 0 | 0 | 229 | 0 | 0.0 | None | None | 152.67 | None | 26 | 40 | 5.0 |
| Chaiten | 400 | 232 | 0 | 0 | 232 | 0 | 0.0 | None | None | 154.67 | None | 11 | 125 | 5.0 |
| PlanchonPeteroa | 357 | 230 | 3 | 3 | 227 | 0 | 0.013 | 1.0 | 0.026 | 151.33 | 4.389 | 58 | 100 | 3.0 |
| Lastarria | 335 | 221 | 0 | 0 | 221 | 0 | 0.0 | None | None | 147.33 | None | 49 | 85 | 3.0 |
| Isluga | 319 | 212 | 10 | 10 | 202 | 0 | 0.047 | 1.0 | 0.09 | 134.67 | 2.098 | 4 | 43 | 5.0 |
| Tupungatito | 362 | 240 | 5 | 5 | 235 | 0 | 0.021 | 1.0 | 0.041 | 156.67 | 5.268 | 15 | 44 | 7.0 |
| **TOTAL** | — | — | — | **68** | **2465** | **1** | **0.027** | **0.986** | — | **149.39** | — | **321** | **1830** | — |

## Decisión adopción (umbrales objetivo)
- R3 violators MODIS+VIIRS (`enabled`): **≤ 30 total** (vs ~106 disabled).
- Reducción `n_2nd_pass_recapture_agg` enabled vs disabled: **≥ 50%** per-vol en NdC/PP/Copahue/Chaiten.
- Cero pérdida TPs MIROVA (especialmente Lascar MODIS 25/25).
- Recall y precision sin regresión >5pp per-vol enabled vs disabled.

### Δ enabled - disabled (per-volcano × sensor)
| Volcán | Sensor | Δ TP | Δ FP | Δ FN | Δ R3 | Δ n_2nd_agg | Δ Recall | Δ Precision |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| PuyehueCordonCaulle | MODIS | +0 | +0 | +0 | +0 | -2102 | n/a | +0.000 |
| PuyehueCordonCaulle | VIIRS | +0 | +0 | +0 | +0 | +0 | +0.000 | +0.000 |
| Villarrica | MODIS | +0 | +0 | +0 | -1 | -3977 | n/a | +0.000 |
| Villarrica | VIIRS | +0 | -1 | +0 | -1 | -3 | n/a | +0.000 |
| Lascar | MODIS | +0 | +0 | +0 | +0 | -2966 | +0.000 | +0.000 |
| Lascar | VIIRS | +0 | -1 | +0 | -1 | -3 | +0.000 | +0.001 |
| Copahue | MODIS | +0 | +0 | +0 | +0 | -3596 | n/a | +0.000 |
| Copahue | VIIRS | +0 | +0 | +0 | +0 | -11 | n/a | +0.000 |
| NevadosDeChillan | MODIS | +0 | +0 | +0 | -2 | -3818 | n/a | +0.000 |
| NevadosDeChillan | VIIRS | +0 | -3 | +0 | -3 | -15 | +0.000 | +0.000 |
| Llaima | MODIS | +0 | +0 | +0 | +0 | -3247 | n/a | +0.000 |
| Llaima | VIIRS | +0 | -1 | +0 | -1 | -23 | n/a | +0.000 |
| Chaiten | MODIS | +0 | +0 | +0 | -2 | -4705 | n/a | +0.000 |
| Chaiten | VIIRS | +0 | +0 | +0 | +0 | -1 | n/a | +0.000 |
| PlanchonPeteroa | MODIS | +0 | -1 | +0 | -4 | -4608 | n/a | +0.000 |
| PlanchonPeteroa | VIIRS | +0 | +0 | +0 | +0 | -5 | +0.000 | +0.000 |
| Lastarria | MODIS | +0 | +0 | +0 | +0 | -3054 | n/a | +0.000 |
| Lastarria | VIIRS | +0 | -1 | +0 | -1 | -4 | n/a | +0.000 |
| Isluga | MODIS | +0 | +0 | +0 | +0 | -2625 | n/a | +0.000 |
| Isluga | VIIRS | +0 | -1 | +0 | -1 | -3 | +0.000 | +0.000 |
| Tupungatito | MODIS | +0 | +0 | +0 | +1 | -5001 | n/a | +0.000 |
| Tupungatito | VIIRS | +0 | +0 | +0 | +0 | -2 | +0.000 | +0.000 |
