# Audit F-S81-B' — gate intra-radio second_pass_recapture (S85)
**Ventana**: 2026-04-12 → 2026-05-26 (45d)
**Sensores**: MODIS + VIIRS (helper integrado en los 3 process_*.py)
**Tolerancia match temporal**: ±60 min
**Profiles**: enabled, disabled, baseline

⚠️  JSONs faltantes (22): ['mirova_equivalent_f_s81_b_prime_2nd_pass_gate_enabled/PuyehueCordonCaulle.json', 'mirova_equivalent_f_s81_b_prime_2nd_pass_gate_enabled/Villarrica.json', 'mirova_equivalent_f_s81_b_prime_2nd_pass_gate_enabled/Lascar.json', 'mirova_equivalent_f_s81_b_prime_2nd_pass_gate_enabled/Copahue.json', 'mirova_equivalent_f_s81_b_prime_2nd_pass_gate_enabled/NevadosDeChillan.json']...

## Profile: `enabled` — sensor MODIS
| Volcán | N rec | Detec | ALERTA | TP | FP | FN | Prec | Rec | F1 | FPs/mes | Ratio | R3viol | n_2nd_agg | inner |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **TOTAL** | — | — | — | **0** | **0** | **0** | **nan** | **nan** | — | **0.00** | — | **0** | **0** | — |

## Profile: `enabled` — sensor VIIRS
| Volcán | N rec | Detec | ALERTA | TP | FP | FN | Prec | Rec | F1 | FPs/mes | Ratio | R3viol | n_2nd_agg | inner |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **TOTAL** | — | — | — | **0** | **0** | **0** | **nan** | **nan** | — | **0.00** | — | **0** | **0** | — |

## Profile: `disabled` — sensor MODIS
| Volcán | N rec | Detec | ALERTA | TP | FP | FN | Prec | Rec | F1 | FPs/mes | Ratio | R3viol | n_2nd_agg | inner |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **TOTAL** | — | — | — | **0** | **0** | **0** | **nan** | **nan** | — | **0.00** | — | **0** | **0** | — |

## Profile: `disabled` — sensor VIIRS
| Volcán | N rec | Detec | ALERTA | TP | FP | FN | Prec | Rec | F1 | FPs/mes | Ratio | R3viol | n_2nd_agg | inner |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **TOTAL** | — | — | — | **0** | **0** | **0** | **nan** | **nan** | — | **0.00** | — | **0** | **0** | — |

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
