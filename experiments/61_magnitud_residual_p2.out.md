# P2 magnitud residual — pareo MIROVA vs nuestro (90d)

Refs MIROVA ALERTA_TERMICA con VRP>0: 545

Pares MIROVA-nuestro encontrados: 412

## Ratio mediano por volcán (todos los TPs con VRP>0 ambos)

| Volcán | n | mediana ratio | mean ratio | mediana MIROVA MW | mediana nuestro MW |
|---|---:|---:|---:|---:|---:|
| Chaiten | 8 | 31.18 | 51.28 | 0.10 | 2.89 |
| Copahue | 1 | 10.81 | 10.81 | 0.21 | 2.27 |
| Isluga | 50 | 1.67 | 4.19 | 0.25 | 0.49 |
| Lascar | 182 | 1.91 | 33.34 | 1.52 | 3.56 |
| Lastarria | 60 | 27.69 | 32.05 | 0.10 | 2.79 |
| PlanchonPeteroa | 30 | 26.14 | 27.80 | 0.09 | 2.73 |
| PuyehueCordonCaulle | 46 | 61.02 | 145.59 | 0.32 | 17.21 |
| Tupungatito | 32 | 0.81 | 15.71 | 0.24 | 0.24 |
| Villarrica | 3 | 65.65 | 61.68 | 0.12 | 7.22 |
| **GLOBAL** | 412 | **6.25** | 40.88 | 0.30 | 2.91 |

## Top 15 peores ratios con MIROVA_VRP < 0.5 MW

| Volcán | Sensor | Fecha UTC | MIROVA MW | Nuestro MW | Ratio | pc_n | pc_VRP | pc_dist | n_anom | n_clu | T1 | T1_pix | vent_pix | clase |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|:--:|---:|---:|---|
| Lascar | MODIS | 2026-04-23 08:00 | 0.190 | 250.07 | 1316.2x | 2 | 14.00 | 25.47 | 88 | 66 | N | 0 | 0 | far |
| PuyehueCordonCaulle | VIIRS375 | 2026-04-10 06:30 | 0.080 | 87.32 | 1091.5x | 11 | 3.34 | 16.88 | 439 | 184 | Y | 71 | 0 | summit |
| PuyehueCordonCaulle | VIIRS375 | 2026-02-10 05:42 | 0.200 | 195.99 | 980.0x | 59 | 39.63 | 16.36 | 759 | 249 | Y | 102 | 0 | summit |
| Lascar | MODIS | 2026-04-27 07:15 | 0.280 | 211.13 | 754.0x | 2 | 9.54 | 29.98 | 65 | 55 | N | 0 | 0 | far |
| PuyehueCordonCaulle | VIIRS375 | 2026-04-08 06:18 | 0.070 | 34.26 | 489.4x | 58 | 2.25 | 0.74 | 249 | 105 | Y | 93 | 0 | summit |
| PuyehueCordonCaulle | VIIRS375 | 2026-04-10 04:48 | 0.110 | 52.77 | 479.7x | 7 | 1.80 | 14.15 | 331 | 155 | Y | 81 | 0 | summit |
| PuyehueCordonCaulle | VIIRS375 | 2026-04-17 05:06 | 0.040 | 18.90 | 472.4x | 60 | 1.66 | 0.69 | 188 | 77 | Y | 77 | 0 | summit |
| Lascar | MODIS | 2026-04-02 07:45 | 0.290 | 120.88 | 416.8x | 2 | 6.23 | 23.39 | 76 | 61 | N | 0 | 0 | far |
| Lascar | MODIS | 2026-03-18 01:15 | 0.270 | 111.03 | 411.2x | 1 | 13.69 | 22.91 | 30 | 26 | N | 0 | 0 | far |
| PuyehueCordonCaulle | VIIRS375 | 2026-02-21 05:36 | 0.110 | 35.35 | 321.3x | 5 | 1.33 | 18.22 | 250 | 99 | Y | 103 | 0 | summit |
| PuyehueCordonCaulle | VIIRS375 | 2026-03-20 05:30 | 0.100 | 31.73 | 317.3x | 15 | 7.06 | 15.62 | 250 | 94 | Y | 95 | 0 | summit |
| Lascar | MODIS | 2026-02-11 07:00 | 0.480 | 141.27 | 294.3x | 2 | 18.85 | 24.38 | 22 | 19 | N | 0 | 0 | far |
| Tupungatito | VIIRS375 | 2026-03-05 05:12 | 0.030 | 8.06 | 268.7x | 74 | 7.07 | 1.41 | 92 | 3 | Y | 90 | 0 | summit |
| PuyehueCordonCaulle | VIIRS375 | 2026-04-11 06:12 | 0.160 | 27.68 | 173.0x | 7 | 2.46 | 15.17 | 234 | 83 | Y | 94 | 0 | summit |
| Chaiten | VIIRS375 | 2026-02-26 05:48 | 0.030 | 4.47 | 149.0x | 82 | 4.18 | 1.11 | 98 | 5 | Y | 95 | 0 | summit |

## Composición de los 30 peores ratios (cualquier MIROVA)

- Test 1 ON: 18/30
- pc_n mediana: 7.0, max: 82
- n_anom_pix mediana: 88.5, max: 759
- Sensores: {'VIIRS375': 17, 'MODIS': 12, 'VIIRS750': 1}
- Volcanes: {'PuyehueCordonCaulle': 14, 'Lascar': 12, 'Chaiten': 2, 'Tupungatito': 1, 'Lastarria': 1}

## ¿pc_vrp (cluster contiguo) está más cerca de MIROVA que vrp_mw (todos los pixels)?

- Mediana ratio TOTAL vrp_mw / MIROVA: 6.25×
- Mediana ratio CLUSTER pc_vrp / MIROVA (donde pc_vrp>0): 2.86×
