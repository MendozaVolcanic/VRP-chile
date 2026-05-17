# S48 VIIRS-DEEP per-volcano analysis (30d 2026-04-16 -> 2026-05-16)

## Tabla VIIRS-I 375m por volcán

| Volcán | inner_km | n_alertas_MIROVA | recall_VIIRS-I | n_summit | n_far | far_ratio | n_sub_MW | n_above_MW | med_pc_vrp |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| PuyehueCordonCaulle | 20 | 23 | 100% (23/23) | 120 | 0 | 0.00 | 65 | 55 | 0.827 |
| Villarrica | 5 | 2 | 100% (2/2) | 115 | 7 | 0.06 | 43 | 79 | 1.693 |
| Lascar | 5 | 44 | 98% (43/44) | 97 | 2 | 0.02 | 50 | 49 | 0.986 |
| Copahue | 4 | 1 | 100% (1/1) | 101 | 6 | 0.06 | 53 | 54 | 1.003 |
| NevadosDeChillan | 5 | 3 | 0% (0/3) | 15 | 5 | 0.25 | 17 | 3 | 0.236 |
| Llaima | 5 | 1 | 100% (1/1) | 96 | 5 | 0.05 | 36 | 65 | 1.617 |
| Chaiten | 5 | 1 | 100% (1/1) | 97 | 2 | 0.02 | 52 | 47 | 0.859 |
| PlanchonPeteroa | 3 | 0 | — | 88 | 8 | 0.08 | 59 | 37 | 0.657 |
| Lastarria | 3 | 36 | 100% (36/36) | 96 | 3 | 0.03 | 92 | 7 | 0.176 |
| Isluga | 5 | 27 | 96% (26/27) | 98 | 1 | 0.01 | 74 | 25 | 0.359 |
| Tupungatito | 7 | 21 | 100% (21/21) | 107 | 2 | 0.02 | 52 | 57 | 1.164 |

## Comparativa per-sensor (n records con pc_vrp>0)

| Volcán | MODIS | VIIRS-M 750 | VIIRS-I 375 | % VIIRS-I del total |
|---|---:|---:|---:|---:|
| PuyehueCordonCaulle | 73 | 132 | 120 | 37% |
| Villarrica | 69 | 75 | 122 | 46% |
| Lascar | 56 | 73 | 99 | 43% |
| Copahue | 66 | 64 | 107 | 45% |
| NevadosDeChillan | 65 | 38 | 20 | 16% |
| Llaima | 68 | 57 | 101 | 45% |
| Chaiten | 74 | 58 | 99 | 43% |
| PlanchonPeteroa | 69 | 69 | 96 | 41% |
| Lastarria | 59 | 72 | 99 | 43% |
| Isluga | 55 | 44 | 99 | 50% |
| Tupungatito | 68 | 63 | 109 | 45% |

## Medianas pc_vrp por sensor

| Volcán | MODIS_med | VIIRS-M_med | VIIRS-I_med |
|---|---:|---:|---:|
| PuyehueCordonCaulle | 4.507 | 0.929 | 0.827 |
| Villarrica | 3.448 | 2.453 | 1.693 |
| Lascar | 2.299 | 1.258 | 0.986 |
| Copahue | 2.282 | 2.487 | 1.003 |
| NevadosDeChillan | 2.474 | 1.288 | 0.236 |
| Llaima | 3.484 | 1.716 | 1.617 |
| Chaiten | 3.857 | 1.631 | 0.859 |
| PlanchonPeteroa | 4.377 | 1.854 | 0.657 |
| Lastarria | 2.484 | 1.101 | 0.176 |
| Isluga | 3.57 | 1.171 | 0.359 |
| Tupungatito | 2.947 | 1.649 | 1.164 |