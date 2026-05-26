# S76 - Audit recall/precision Tier A (operacional fresco)

Ventana: 2026-02-01 -> 2026-05-20 (108d)
Matching: sensor-aware +/-60 min
Ground truth: CONS + OCR ALERTA_TERMICA
Setup: data/mirova_equivalent/ (post PRs S71-S75)

## Tabla principal

| Volcan | n_alert | n_rec | n_det | TP | FP | FN | Recall | Precision | F1 | Ratio_med | vmax(MW) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Lascar | 370 | 1013 | 798 | 590 | 208 | 126 | 0.82 | 0.74 | 0.78 | 1.39 | 142.3 |
| Lastarria | 107 | 1012 | 845 | 415 | 430 | 6 | 0.99 | 0.49 | 0.66 | 14.62 | 40.4 |
| Isluga | 119 | 967 | 650 | 262 | 388 | 21 | 0.93 | 0.40 | 0.56 | 1.96 | 87.6 |
| Villarrica | 10 | 1194 | 879 | 41 | 838 | 1 | 0.98 | 0.05 | 0.09 | 13.61 | 151.0 |
| Chaiten | 17 | 1245 | 905 | 56 | 849 | 1 | 0.98 | 0.06 | 0.12 | 8.04 | 534.2 |
| PlanchonPeteroa | 59 | 1129 | 804 | 210 | 594 | 5 | 0.98 | 0.26 | 0.41 | 10.56 | 538.2 |
| Tupungatito | 94 | 1108 | 692 | 233 | 459 | 14 | 0.94 | 0.34 | 0.50 | 11.19 | 190.9 |
| PuyehueCordonCaulle | 102 | 1240 | 1154 | 389 | 765 | 15 | 0.96 | 0.34 | 0.50 | 10.93 | 1362.0 |
| Llaima | 1 | 1190 | 709 | 3 | 706 | 0 | 1.00 | 0.00 | 0.01 | 23.38 | 64.3 |
| Copahue | 1 | 1173 | 843 | 4 | 839 | 0 | 1.00 | 0.00 | 0.01 | 5.85 | 219.0 |
| NevadosDeChillan | 8 | 1155 | 518 | 1 | 517 | 4 | 0.20 | 0.00 | 0.00 | 45.65 | 332.8 |

## Diff vs S12 baseline (2026-04-16)

| Volcan | S12 recall | S76 recall | Delta | Estado |
|---|---|---|---|---|
| Chaiten | 0.87 | 0.98 | +0.11 | MEJORA |
| Lastarria | 0.85 | 0.99 | +0.14 | MEJORA |
| Tupungatito | 0.83 | 0.94 | +0.11 | MEJORA |
| PuyehueCordonCaulle | 0.82 | 0.96 | +0.14 | MEJORA |
| Lascar | 0.55 | 0.82 | +0.27 | MEJORA |
| Villarrica | 0.00 | 0.98 | +0.98 | MEJORA |

## Diagnostico volcanes problematicos (recall<0.5 OR precision<0.5 OR ratio fuera 0.5-2.0)

- **Lastarria**: precision_baja(0.49), ratio_fuera_rango(14.62), no_cov=6
    TP=415 FP=430 FN=6, vmax=40.376 vmed=1.915, alertas=107 no_cov=6
- **Isluga**: precision_baja(0.40)
    TP=262 FP=388 FN=21, vmax=87.633 vmed=1.4875, alertas=119 no_cov=0
- **Villarrica**: precision_baja(0.05), ratio_fuera_rango(13.61)
    TP=41 FP=838 FN=1, vmax=150.962 vmed=3.575, alertas=10 no_cov=0
- **Chaiten**: precision_baja(0.06), ratio_fuera_rango(8.04)
    TP=56 FP=849 FN=1, vmax=534.18 vmed=2.585, alertas=17 no_cov=0
- **PlanchonPeteroa**: precision_baja(0.26), ratio_fuera_rango(10.56)
    TP=210 FP=594 FN=5, vmax=538.23 vmed=2.268, alertas=59 no_cov=0
- **Tupungatito**: precision_baja(0.34), ratio_fuera_rango(11.19)
    TP=233 FP=459 FN=14, vmax=190.853 vmed=2.504, alertas=94 no_cov=0
- **PuyehueCordonCaulle**: precision_baja(0.34), ratio_fuera_rango(10.93), no_cov=3
    TP=389 FP=765 FN=15, vmax=1362.039 vmed=3.2184999999999997, alertas=102 no_cov=3
- **Llaima**: precision_baja(0.00), ratio_fuera_rango(23.38)
    TP=3 FP=706 FN=0, vmax=64.268 vmed=2.701, alertas=1 no_cov=0
- **Copahue**: precision_baja(0.00), ratio_fuera_rango(5.85)
    TP=4 FP=839 FN=0, vmax=218.953 vmed=2.667, alertas=1 no_cov=0
- **NevadosDeChillan**: recall_bajo(0.20), precision_baja(0.00), ratio_fuera_rango(45.65), no_cov=3
    TP=1 FP=517 FN=4, vmax=332.756 vmed=2.777, alertas=8 no_cov=3

## Notas metodologicas

- `pc.vrp_mw` con fallback global `vrp_mw` (convencion A4 desde experiments/137).
- Matching sensor-aware (MODIS vs VIIRS no se cruzan).
- Tolerancia +/-60 min cubre desfase scraper vs L1B + multiple granules/noche.
- FN solo cuenta alertas con cobertura sensor (no penaliza nights sin granule).
- Baseline S12 viene de CLAUDE.md (snapshot 2026-04-16, pre S15-S75 changes).