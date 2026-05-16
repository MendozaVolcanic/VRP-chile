# S46 Ronda 1 - Results A/B Coppola literal

Window: 2026-04-16 a 2026-05-16.
Variantes auditadas: 13 (_baseline_s44, _drift1a_only, _drift1b_only, _drift1ab_only, _drift23_only, _drift23_dual_only, _drift4_only, _drift234_only, _drift7_modis_only, _drift7_viirs_only, _drift7_both_only, _coppola_full, _dibella_n12_viirs_only).

## Tabla agregada (Tier A, todos sensores)

| Variante | TP | FN | FP | F1 | Recall | Precision |
|---|---|---|---|---|---|---|
| _baseline_s44 | 214 | 13 | 39 | 89.2% | 94.3% | 84.6% |
| _drift1a_only | 214 | 13 | 39 | 89.2% | 94.3% | 84.6% |
| _drift1b_only | 214 | 13 | 39 | 89.2% | 94.3% | 84.6% |
| _drift1ab_only | 214 | 13 | 39 | 89.2% | 94.3% | 84.6% |
| _drift23_only | 213 | 14 | 39 | 88.9% | 93.8% | 84.5% |
| _drift23_dual_only | 213 | 14 | 39 | 88.9% | 93.8% | 84.5% |
| _drift4_only | 217 | 10 | 39 | 89.9% | 95.6% | 84.8% |
| _drift234_only | 217 | 10 | 39 | 89.9% | 95.6% | 84.8% |
| _drift7_modis_only | 214 | 13 | 39 | 89.2% | 94.3% | 84.6% |
| _drift7_viirs_only | 214 | 13 | 39 | 89.2% | 94.3% | 84.6% |
| _drift7_both_only | 214 | 13 | 39 | 89.2% | 94.3% | 84.6% |
| _coppola_full | 217 | 10 | 39 | 89.9% | 95.6% | 84.8% |
| _dibella_n12_viirs_only | 213 | 14 | 39 | 88.9% | 93.8% | 84.5% |

## Per-sensor breakdown

### MODIS

| Variante | TP | FN | FP | F1 |
|---|---|---|---|---|
| _baseline_s44 | 18 | 3 | 0 | 92.3% |
| _drift1a_only | 18 | 3 | 0 | 92.3% |
| _drift1b_only | 18 | 3 | 0 | 92.3% |
| _drift1ab_only | 18 | 3 | 0 | 92.3% |
| _drift23_only | 18 | 3 | 0 | 92.3% |
| _drift23_dual_only | 18 | 3 | 0 | 92.3% |
| _drift4_only | 21 | 0 | 0 | 100.0% |
| _drift234_only | 21 | 0 | 0 | 100.0% |
| _drift7_modis_only | 18 | 3 | 0 | 92.3% |
| _drift7_viirs_only | 18 | 3 | 0 | 92.3% |
| _drift7_both_only | 18 | 3 | 0 | 92.3% |
| _coppola_full | 21 | 0 | 0 | 100.0% |
| _dibella_n12_viirs_only | 18 | 3 | 0 | 92.3% |

### VIIRS

| Variante | TP | FN | FP | F1 |
|---|---|---|---|---|
| _baseline_s44 | 38 | 5 | 0 | 93.8% |
| _drift1a_only | 38 | 5 | 0 | 93.8% |
| _drift1b_only | 38 | 5 | 0 | 93.8% |
| _drift1ab_only | 38 | 5 | 0 | 93.8% |
| _drift23_only | 37 | 6 | 0 | 92.5% |
| _drift23_dual_only | 37 | 6 | 0 | 92.5% |
| _drift4_only | 39 | 4 | 0 | 95.1% |
| _drift234_only | 39 | 4 | 0 | 95.1% |
| _drift7_modis_only | 38 | 5 | 0 | 93.8% |
| _drift7_viirs_only | 38 | 5 | 0 | 93.8% |
| _drift7_both_only | 38 | 5 | 0 | 93.8% |
| _coppola_full | 39 | 4 | 0 | 95.1% |
| _dibella_n12_viirs_only | 37 | 6 | 0 | 92.5% |

### VIIRS375

| Variante | TP | FN | FP | F1 |
|---|---|---|---|---|
| _baseline_s44 | 158 | 5 | 39 | 87.8% |
| _drift1a_only | 158 | 5 | 39 | 87.8% |
| _drift1b_only | 158 | 5 | 39 | 87.8% |
| _drift1ab_only | 158 | 5 | 39 | 87.8% |
| _drift23_only | 158 | 5 | 39 | 87.8% |
| _drift23_dual_only | 158 | 5 | 39 | 87.8% |
| _drift4_only | 157 | 6 | 39 | 87.5% |
| _drift234_only | 157 | 6 | 39 | 87.5% |
| _drift7_modis_only | 158 | 5 | 39 | 87.8% |
| _drift7_viirs_only | 158 | 5 | 39 | 87.8% |
| _drift7_both_only | 158 | 5 | 39 | 87.8% |
| _coppola_full | 157 | 6 | 39 | 87.5% |
| _dibella_n12_viirs_only | 158 | 5 | 39 | 87.8% |

## Decision automatica (delta F1 vs baseline_s44)

| Variante | dF1 (pp) | dRecall (pp) | Decision |
|---|---|---|---|
| _drift1a_only | +0.0 | +0.0 | NEUTRAL - defer Ronda 2 |
| _drift1b_only | +0.0 | +0.0 | NEUTRAL - defer Ronda 2 |
| _drift1ab_only | +0.0 | +0.0 | NEUTRAL - defer Ronda 2 |
| _drift23_only | -0.2 | -0.4 | NEUTRAL - defer Ronda 2 |
| _drift23_dual_only | -0.2 | -0.4 | NEUTRAL - defer Ronda 2 |
| _drift4_only | +0.7 | +1.3 | NEUTRAL win - adopt for paper alignment |
| _drift234_only | +0.7 | +1.3 | NEUTRAL win - adopt for paper alignment |
| _drift7_modis_only | +0.0 | +0.0 | NEUTRAL - defer Ronda 2 |
| _drift7_viirs_only | +0.0 | +0.0 | NEUTRAL - defer Ronda 2 |
| _drift7_both_only | +0.0 | +0.0 | NEUTRAL - defer Ronda 2 |
| _coppola_full | +0.7 | +1.3 | NEUTRAL win - adopt for paper alignment |
| _dibella_n12_viirs_only | -0.2 | -0.4 | NEUTRAL - defer Ronda 2 |
