# Chaiten + PCC post-fix Driver B — qué path domina los altos ratios


## Chaiten

### Top 10 peores ratios post-fix (10 TPs total)

| Fecha | Sensor | MIROVA MW | Nuestro MW | Ratio | T1? | path_source | pc_n | n_t1pix | n_bt | n_dnti | n_anom |
|---|---|---:|---:|---:|:--:|---|---:|---:|---:|---:|---:|
| 2026-04-07 04:54 | VIIRS375 | 0.080 | 9.20 | 115.0 | Y | eruption | 73 | 73 | 0 | 6 | 76 |
| 2026-02-26 05:48 | VIIRS375 | 0.030 | 2.00 | 66.8 | Y | test1 | 82 | 95 | 0 | 4 | 98 |
| 2026-03-08 06:00 | VIIRS375 | 0.230 | 8.92 | 38.8 | Y | eruption | 93 | 94 | 0 | 3 | 94 |
| 2026-02-20 06:00 | VIIRS375 | 0.090 | 1.65 | 18.3 | Y | eruption | 54 | 71 | 0 | 1 | 71 |
| 2026-04-10 04:48 | VIIRS375 | 0.100 | 1.45 | 14.5 | Y | eruption | 44 | 52 | 0 | 1 | 52 |
| 2026-02-25 06:06 | VIIRS375 | 0.180 | 2.04 | 11.3 | Y | test1 | 47 | 57 | 0 | 2 | 58 |
| 2026-04-04 05:54 | VIIRS375 | 0.130 | 1.21 | 9.3 | Y | eruption | 67 | 84 | 0 | 2 | 84 |
| 2026-03-05 05:12 | VIIRS375 | 0.080 | 0.51 | 6.4 | Y | test1 | 58 | 73 | 0 | 1 | 74 |
| 2026-01-30 05:54 | VIIRS375 | 0.220 | 0.70 | 3.2 | N | eruption | 2 | 0 | 0 | 3 | 3 |
| 2026-04-08 04:36 | VIIRS375 | 0.150 | 0.24 | 1.6 | N | eruption | 1 | 0 | 0 | 5 | 5 |

**Distribución path_source en TPs (10 total):**
  - eruption: 7 (70%)
  - test1: 3 (30%)

**triggered_test1 en TOP 10 peor ratio**: 8/10
**triggered_test1 en TODOS los TPs**: 8/10 (80%)

**Records ratio>=5x (8)**: mediana n_bt=0, n_dnti=2, n_t1=73
**Records ratio<5x (2)**: mediana n_bt=0, n_dnti=5, n_t1=0

## PuyehueCordonCaulle

### Top 10 peores ratios post-fix (55 TPs total)

| Fecha | Sensor | MIROVA MW | Nuestro MW | Ratio | T1? | path_source | pc_n | n_t1pix | n_bt | n_dnti | n_anom |
|---|---|---:|---:|---:|:--:|---|---:|---:|---:|---:|---:|
| 2026-02-13 06:30 | VIIRS375 | 0.020 | 6.01 | 300.3 | Y | test1 | 14 | 66 | 0 | 90 | 153 |
| 2026-02-10 05:42 | VIIRS375 | 0.200 | 39.63 | 198.1 | Y | eruption | 59 | 102 | 24 | 667 | 759 |
| 2026-02-06 05:18 | VIIRS | 0.590 | 69.66 | 118.1 | Y | eruption | 19 | 24 | 0 | 39 | 62 |
| 2026-02-06 05:18 | VIIRS375 | 0.190 | 15.14 | 79.7 | Y | test1 | 24 | 96 | 0 | 99 | 189 |
| 2026-03-13 06:06 | VIIRS375 | 0.160 | 12.47 | 77.9 | Y | test1 | 84 | 86 | 1 | 487 | 563 |
| 2026-03-20 05:30 | VIIRS375 | 0.100 | 7.06 | 70.6 | Y | eruption | 15 | 95 | 0 | 156 | 250 |
| 2026-04-04 05:54 | VIIRS | 0.550 | 34.49 | 62.7 | Y | eruption | 15 | 25 | 0 | 26 | 51 |
| 2026-04-21 06:24 | VIIRS375 | 0.050 | 2.93 | 58.7 | Y | test1 | 11 | 47 | 0 | 46 | 91 |
| 2026-02-06 06:42 | VIIRS375 | 0.200 | 9.05 | 45.2 | Y | eruption | 16 | 48 | 0 | 68 | 114 |
| 2026-04-10 06:30 | VIIRS375 | 0.080 | 3.34 | 41.8 | Y | eruption | 11 | 71 | 0 | 368 | 439 |

**Distribución path_source en TPs (55 total):**
  - eruption: 44 (80%)
  - test1: 11 (20%)

**triggered_test1 en TOP 10 peor ratio**: 10/10
**triggered_test1 en TODOS los TPs**: 55/55 (100%)

**Records ratio>=5x (40)**: mediana n_bt=0, n_dnti=73, n_t1=72
**Records ratio<5x (15)**: mediana n_bt=0, n_dnti=40, n_t1=78


## Veredicto

Si triggered_test1 alto (>80%) + ratio sigue alto → Test 1 SÍ es path pero filtro 5σ insuficiente.
Si triggered_test1 bajo (<50%) + ratio alto → otro path domina, extender filter a path BT/dNTI.
Si n_bt_path o n_dnti_ctx altos en records ratio>5 → ese es el path no-filtrado dominante.
