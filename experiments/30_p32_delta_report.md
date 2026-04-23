# P3.2 — Delta Report pre/post reproceso

Generado por `experiments/30_p32_delta_report.py`.

## Global

| Metrica | Pre-P3.2 | Post-P3.2 | Delta |
|---|---:|---:|---:|
| TP | 224 | 225 | +1 |
| FN | 585 | 584 | -1 |
| FP | 423 | 443 | +20 |
| Recall | 0.28 | 0.28 | +0.00 |
| Precision | 0.35 | 0.34 | -0.01 |
| F1 | 0.31 | 0.30 | -0.00 |
| Ratio mediano | 1.56 | 1.57 | +0.00 |

## Por volcan

| Volcan | TP pre/post | Ratio pre/post | Recall pre/post |
|---|---|---|---|
| Chaiten | 0/0 | 0.00/0.00 | 0.00/0.00 |
| Copahue | 1/1 | 1.24/1.24 | 0.06/0.06 |
| Isluga | 13/13 | 1.23/1.23 | 0.14/0.14 |
| Lascar | 88/89 | 1.16/1.17 | 0.35/0.35 |
| Lastarria | 69/69 | 19.87/19.91 | 0.53/0.53 |
| Llaima | 2/2 | 10.82/10.82 | 0.06/0.06 |
| NevadosDeChillan | 1/1 | 1.45/1.45 | 0.03/0.03 |
| PlanchonPeteroa | 3/3 | 4.80/4.80 | 0.06/0.06 |
| PuyehueCordonCaulle | 44/44 | 1.35/1.35 | 0.48/0.48 |
| Tupungatito | 3/3 | 3.35/3.35 | 0.04/0.04 |
| Villarrica | 0/0 | 0.00/0.00 | 0.00/0.00 |

## Veredicto criterios P3.2

**P3.2 NO APROBADO**

- [FAIL] Lastarria ratio mediano < 3.0 (pre 19.87 -> post 19.91)
- [OK] Lascar ratio mediano en [1.10, 1.30] (post 1.17)
- [OK] Recall global >= 0.23 (post 0.28)
