# S72 F2.2 - A/B Unsuitable Filters audit

Ventana: 2026-02-20 -> 2026-05-20  (90d)
Matching MIROVA: ±60 min sensor-aware (per-record)
Bug D9: pc.vrp_mw>5.0 MW AND ctx-only (n_bt=0 & n_nti=0) AND t_bg<260.0 K

## Per-volcano: baseline vs A/B

| Volcan | Set | n_alerts | n_rec_det | TP | FP | FN | Recall | Precision | Ratio_med | N_ratio | D9_bug | d9_capped |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Lascar | base | 327 | 655 | 506 | 149 | 114 | 0.82 | 0.77 | 1.29 | 506 | 4 | N/A |
| Lascar | A/B | 327 | 433 | 303 | 130 | 116 | 0.72 | 0.70 | 0.94 | 303 | 0 | N/A |
| Lastarria | base | 92 | 679 | 349 | 330 | 5 | 0.99 | 0.51 | 11.92 | 349 | 3 | N/A |
| Lastarria | A/B | 92 | 425 | 180 | 245 | 5 | 0.97 | 0.42 | 1.35 | 180 | 0 | N/A |
| Isluga | base | 111 | 526 | 238 | 288 | 20 | 0.92 | 0.45 | 1.84 | 238 | 7 | N/A |
| Isluga | A/B | 111 | 433 | 181 | 252 | 22 | 0.89 | 0.42 | 1.33 | 181 | 0 | N/A |
| Villarrica | base | 10 | 701 | 40 | 661 | 1 | 0.98 | 0.06 | 14.75 | 40 | 27 | N/A |
| Villarrica | A/B | 10 | 510 | 25 | 485 | 1 | 0.96 | 0.05 | 15.89 | 25 | 0 | N/A |
| Chaiten | base | 16 | 726 | 51 | 675 | 1 | 0.98 | 0.07 | 7.97 | 51 | 55 | N/A |
| Chaiten | A/B | 16 | 526 | 42 | 484 | 1 | 0.98 | 0.08 | 2.84 | 42 | 0 | N/A |
| PlanchonPeteroa | base | 54 | 652 | 192 | 460 | 4 | 0.98 | 0.29 | 10.34 | 192 | 16 | N/A |
| PlanchonPeteroa | A/B | 54 | 477 | 127 | 350 | 5 | 0.96 | 0.27 | 4.00 | 127 | 0 | N/A |
| Tupungatito | base | 90 | 596 | 229 | 367 | 13 | 0.95 | 0.38 | 11.61 | 229 | 36 | N/A |
| Tupungatito | A/B | 90 | 482 | 187 | 295 | 13 | 0.94 | 0.39 | 9.52 | 187 | 0 | N/A |
| PuyehueCordonCaulle | base | 85 | 930 | 314 | 616 | 13 | 0.96 | 0.34 | 8.65 | 314 | 39 | N/A |
| PuyehueCordonCaulle | A/B | 85 | 562 | 161 | 401 | 13 | 0.93 | 0.29 | 0.51 | 161 | 0 | N/A |
| Llaima | base | 1 | 569 | 3 | 566 | 0 | 1.00 | 0.01 | 23.38 | 3 | 19 | N/A |
| Llaima | A/B | 1 | 489 | 3 | 486 | 0 | 1.00 | 0.01 | 23.38 | 3 | 0 | N/A |
| Copahue | base | 1 | 657 | 4 | 653 | 0 | 1.00 | 0.01 | 5.85 | 4 | 22 | N/A |
| Copahue | A/B | 1 | 483 | 1 | 482 | 0 | 1.00 | 0.00 | 3.18 | 1 | 0 | N/A |

## Delta A/B - baseline

| Volcan | dRecall | dPrecision | dRatio | dD9_bug | dD9_bug_% |
|---|---|---|---|---|---|
| Lascar | -0.09 | -0.07 | -0.35 | -4 | +100% |
| Lastarria | -0.01 | -0.09 | -10.57 | -3 | +100% |
| Isluga | -0.03 | -0.03 | -0.52 | -7 | +100% |
| Villarrica | -0.01 | -0.01 | +1.14 | -27 | +100% |
| Chaiten | -0.00 | +0.01 | -5.13 | -55 | +100% |
| PlanchonPeteroa | -0.02 | -0.03 | -6.34 | -16 | +100% |
| Tupungatito | -0.01 | +0.00 | -2.09 | -36 | +100% |
| PuyehueCordonCaulle | -0.03 | -0.05 | -8.14 | -39 | +100% |
| Llaima | +0.00 | +0.00 | +0.00 | -19 | +100% |
| Copahue | +0.00 | -0.00 | -2.68 | -22 | +100% |

## Resumen criterios S33

- Bug D9 baseline total: **228** -> A/B total: **0** (+100.0%)
- Vols con baseline D9>0: 10; con drop >=50%: **10**
- Vols con ratio mejor o igual: **9/10**
- Vols con recall no-degrade (>5pp) [n_mirova>=10]: **7/8**
- Vols con precision no-degrade: **3/10**

Criterios adopcion S33:
- Bug D9 drop >50% en >=5/10 vols.
- Ratio mediano mejora o se mantiene en >=6/10 vols.
- Recall NO degrada >5pp en ningun vol con n_mirova>=10.
- Precision NO degrada en ningun vol.
- Sin regresion Tier A Alto (Lascar/Lastarria/Isluga).

Caveats:
- NdC excluido (1 vol failure run 26236980698) -> 10/11 sample.
- d9_capped column es N/A: este profile NO emite el campo (es flag del profile path_d_cap_v1).
- d9_capped fix de raiz: ver bug_d9_count como proxy del bug, no del cap aplicado.
