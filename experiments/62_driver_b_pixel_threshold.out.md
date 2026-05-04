# Driver B — pixel threshold simulation

Samples summit con cluster + pixels: 374

Sanity check pc_vrp reportado vs recomputado por pixels:
  diff% mediano: 60.1%
  diff% max: 100.0%

## Distribución de pixels intra-cluster (Lastarria, top 5 peores ratios)

### Lastarria VIIRS375 2026-02-16 05:30 — MIROVA 0.040 MW vs nuestro 0.86 MW (ratio 22x)
  cluster: 14 pixels, suma=0.86 MW
  top 5 vrp pixel: ['0.207', '0.113', '0.110', '0.093', '0.083']
  bottom 5 vrp pixel: ['0.0325', '0.0151', '0.0041', '0.0000', '0.0000']
  pixels >0.5 MW: 0, >0.1 MW: 3, >0.05 MW: 8, >0.01 MW: 11
### Lastarria VIIRS375 2026-02-09 06:00 — MIROVA 0.060 MW vs nuestro 0.68 MW (ratio 11x)
  cluster: 14 pixels, suma=0.68 MW
  top 5 vrp pixel: ['0.157', '0.093', '0.079', '0.077', '0.062']
  bottom 5 vrp pixel: ['0.0165', '0.0102', '0.0000', '0.0000', '0.0000']
  pixels >0.5 MW: 0, >0.1 MW: 1, >0.05 MW: 7, >0.01 MW: 11
### Lastarria VIIRS375 2026-04-19 06:06 — MIROVA 0.030 MW vs nuestro 0.28 MW (ratio 9x)
  cluster: 17 pixels, suma=0.28 MW
  top 5 vrp pixel: ['0.090', '0.054', '0.046', '0.039', '0.018']
  bottom 5 vrp pixel: ['0.0000', '0.0000', '0.0000', '0.0000', '0.0000']
  pixels >0.5 MW: 0, >0.1 MW: 0, >0.05 MW: 2, >0.01 MW: 6
### Lastarria VIIRS375 2026-02-10 05:42 — MIROVA 0.120 MW vs nuestro 1.06 MW (ratio 9x)
  cluster: 19 pixels, suma=1.06 MW
  top 5 vrp pixel: ['0.198', '0.150', '0.138', '0.073', '0.070']
  bottom 5 vrp pixel: ['0.0183', '0.0174', '0.0035', '0.0000', '0.0000']
  pixels >0.5 MW: 0, >0.1 MW: 3, >0.05 MW: 8, >0.01 MW: 16
### Lastarria VIIRS375 2026-03-03 05:48 — MIROVA 0.100 MW vs nuestro 0.54 MW (ratio 5x)
  cluster: 21 pixels, suma=0.54 MW
  top 5 vrp pixel: ['0.101', '0.080', '0.072', '0.054', '0.047']
  bottom 5 vrp pixel: ['0.0000', '0.0000', '0.0000', '0.0000', '0.0000']
  pixels >0.5 MW: 0, >0.1 MW: 1, >0.05 MW: 4, >0.01 MW: 11

## Ratio mediano global vs piso pixel-level

| Piso pixel MW | Mediana ratio nuestro/MIROVA | n_samples utiles | n_pixels promedio en cluster |
|---:|---:|---:|---:|
| ≥0.00 | 1.19x | 299 | 8.6 |
| ≥0.01 | 1.21x | 291 | 3.1 |
| ≥0.05 | 1.24x | 264 | 2.6 |
| ≥0.10 | 1.24x | 226 | 2.4 |
| ≥0.20 | 1.24x | 173 | 2.3 |
| ≥0.50 | 1.19x | 105 | 1.8 |

## Por volcán con piso pixel ≥ 0.05 MW (hipótesis MIROVA default)

| Volcán | n | mediana ratio | mediana MIROVA | mediana nuestro filt |
|---|---:|---:|---:|---:|
| Chaiten | 7 | 3.62 | 0.100 | 0.362 |
| Copahue | 1 | 3.17 | 0.210 | 0.666 |
| Isluga | 31 | 1.05 | 0.280 | 0.307 |
| Lascar | 112 | 1.10 | 1.750 | 1.943 |
| Lastarria | 44 | 2.07 | 0.100 | 0.164 |
| PlanchonPeteroa | 3 | 0.76 | 0.120 | 0.076 |
| PuyehueCordonCaulle | 45 | 7.57 | 0.350 | 1.713 |
| Tupungatito | 21 | 0.55 | 0.230 | 0.145 |
