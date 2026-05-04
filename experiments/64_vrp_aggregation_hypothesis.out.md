# Driver B Fase 1b — agregación VRP

Samples: 346

## Ratio mediano global por función de agregación

| Función | n_validos | mediana ratio | percentil 25 | percentil 75 | mediana nuestro MW | mediana MIROVA MW |
|---|---:|---:|---:|---:|---:|---:|
| pipeline_reported | 346 | 1.67 | 1.00 | 10.88 | 1.646 | 0.300 |
| sum_all | 346 | 1.46 | 0.92 | 3.75 | 0.720 | 0.300 |
| max_only | 346 | 0.95 | 0.60 | 1.40 | 0.317 | 0.300 |
| top3_sum | 346 | 1.36 | 0.87 | 2.26 | 0.473 | 0.300 |
| top5_sum | 346 | 1.42 | 0.91 | 2.93 | 0.556 | 0.300 |
| sum_>=0.05 | 322 | 1.39 | 0.91 | 2.99 | 0.691 | 0.340 |
| sum_>=0.10 | 282 | 1.28 | 0.92 | 2.27 | 0.936 | 0.450 |
| sum_>=0.20 | 208 | 1.26 | 0.97 | 2.19 | 1.967 | 0.890 |
| sum_>=0.50 | 121 | 1.24 | 0.97 | 1.57 | 2.443 | 1.750 |
| top1_plus_half_top2 | 346 | 1.11 | 0.72 | 1.59 | 0.379 | 0.300 |

## Función max(pixel) por volcán (la más restrictiva)

| Volcán | n | mediana ratio | mediana max_pixel MW | mediana MIROVA MW |
|---|---:|---:|---:|---:|
| Chaiten | 8 | 2.10 | 0.214 | 0.100 |
| Copahue | 1 | 3.17 | 0.666 | 0.210 |
| Isluga | 52 | 0.89 | 0.190 | 0.250 |
| Lascar | 141 | 0.90 | 1.405 | 1.620 |
| Lastarria | 59 | 1.08 | 0.120 | 0.100 |
| PlanchonPeteroa | 12 | 0.53 | 0.061 | 0.140 |
| PuyehueCordonCaulle | 46 | 1.70 | 0.423 | 0.350 |
| Tupungatito | 26 | 0.50 | 0.126 | 0.240 |
| Villarrica | 1 | 0.23 | 0.027 | 0.120 |
