# S46 Ronda 1 - Results A/B Coppola literal

Window: 2026-04-16 a 2026-05-16.
Variantes auditadas: 13 (_baseline_s44, _drift1a_only, _drift1b_only, _drift1ab_only, _drift23_only, _drift23_dual_only, _drift4_only, _drift234_only, _drift7_modis_only, _drift7_viirs_only, _drift7_both_only, _coppola_full, _dibella_n12_viirs_only).

## Tabla agregada (Tier A, todos sensores)

| Variante | TP | FN | FP | F1 | Recall | Precision |
|---|---|---|---|---|---|---|
| _baseline_s44 | 199 | 28 | 39 | 85.6% | 87.7% | 83.6% |
| _drift1a_only | 199 | 28 | 39 | 85.6% | 87.7% | 83.6% |
| _drift1b_only | 199 | 28 | 39 | 85.6% | 87.7% | 83.6% |
| _drift1ab_only | 199 | 28 | 39 | 85.6% | 87.7% | 83.6% |
| _drift23_only | 195 | 32 | 39 | 84.6% | 85.9% | 83.3% |
| _drift23_dual_only | 199 | 28 | 39 | 85.6% | 87.7% | 83.6% |
| _drift4_only | 196 | 31 | 39 | 84.8% | 86.3% | 83.4% |
| _drift234_only | 200 | 27 | 39 | 85.8% | 88.1% | 83.7% |
| _drift7_modis_only | 199 | 28 | 39 | 85.6% | 87.7% | 83.6% |
| _drift7_viirs_only | 199 | 28 | 39 | 85.6% | 87.7% | 83.6% |
| _drift7_both_only | 199 | 28 | 39 | 85.6% | 87.7% | 83.6% |
| _coppola_full | 200 | 27 | 39 | 85.8% | 88.1% | 83.7% |
| _dibella_n12_viirs_only | 195 | 32 | 39 | 84.6% | 85.9% | 83.3% |

## Per-sensor breakdown

### MODIS

| Variante | TP | FN | FP | F1 |
|---|---|---|---|---|
| _baseline_s44 | 4 | 17 | 0 | 32.0% |
| _drift1a_only | 4 | 17 | 0 | 32.0% |
| _drift1b_only | 4 | 17 | 0 | 32.0% |
| _drift1ab_only | 4 | 17 | 0 | 32.0% |
| _drift23_only | 4 | 17 | 0 | 32.0% |
| _drift23_dual_only | 4 | 17 | 0 | 32.0% |
| _drift4_only | 4 | 17 | 0 | 32.0% |
| _drift234_only | 4 | 17 | 0 | 32.0% |
| _drift7_modis_only | 4 | 17 | 0 | 32.0% |
| _drift7_viirs_only | 4 | 17 | 0 | 32.0% |
| _drift7_both_only | 4 | 17 | 0 | 32.0% |
| _coppola_full | 4 | 17 | 0 | 32.0% |
| _dibella_n12_viirs_only | 4 | 17 | 0 | 32.0% |

### VIIRS

| Variante | TP | FN | FP | F1 |
|---|---|---|---|---|
| _baseline_s44 | 37 | 6 | 0 | 92.5% |
| _drift1a_only | 37 | 6 | 0 | 92.5% |
| _drift1b_only | 37 | 6 | 0 | 92.5% |
| _drift1ab_only | 37 | 6 | 0 | 92.5% |
| _drift23_only | 33 | 10 | 0 | 86.8% |
| _drift23_dual_only | 37 | 6 | 0 | 92.5% |
| _drift4_only | 35 | 8 | 0 | 89.7% |
| _drift234_only | 39 | 4 | 0 | 95.1% |
| _drift7_modis_only | 37 | 6 | 0 | 92.5% |
| _drift7_viirs_only | 37 | 6 | 0 | 92.5% |
| _drift7_both_only | 37 | 6 | 0 | 92.5% |
| _coppola_full | 39 | 4 | 0 | 95.1% |
| _dibella_n12_viirs_only | 33 | 10 | 0 | 86.8% |

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
| _drift23_only | -1.0 | -1.8 | NEUTRAL - defer Ronda 2 |
| _drift23_dual_only | +0.0 | +0.0 | NEUTRAL - defer Ronda 2 |
| _drift4_only | -0.7 | -1.3 | NEUTRAL - defer Ronda 2 |
| _drift234_only | +0.2 | +0.4 | NEUTRAL win - adopt for paper alignment |
| _drift7_modis_only | +0.0 | +0.0 | NEUTRAL - defer Ronda 2 |
| _drift7_viirs_only | +0.0 | +0.0 | NEUTRAL - defer Ronda 2 |
| _drift7_both_only | +0.0 | +0.0 | NEUTRAL - defer Ronda 2 |
| _coppola_full | +0.2 | +0.4 | NEUTRAL win - adopt for paper alignment |
| _dibella_n12_viirs_only | -1.0 | -1.8 | NEUTRAL - defer Ronda 2 |
