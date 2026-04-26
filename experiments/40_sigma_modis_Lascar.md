# Análisis std_bg por clase forense — Lascar

Hipótesis D6: T4 tiene `diag_sigma_bg_k` (std_bg global) significativamente
más alto que TP, lo que infla el threshold vent y no dispara la fumarola.

## Distribución `diag_sigma_bg_k` (K) por clase

| Clase | n | median | mean | p25 | p75 | p95 | std |
|---|---:|---:|---:|---:|---:|---:|---:|
| TP | 6 | 5.037 | 5.080 | 4.893 | 5.352 | 5.503 | 0.325 |
| T4 | 2 | 4.405 | 4.405 | 4.260 | 4.550 | 4.667 | 0.291 |
| T2b | 12 | 5.215 | 4.976 | 4.891 | 5.292 | 5.383 | 0.485 |

## Diagnóstico D6

- Ratio mediano T4/TP de `diag_sigma_bg_k`: **0.87**
- ⚠️ **REFUTA D6**: std_bg global en T4 es similar a TP. El problema NO es background inflado — buscar otra causa (ej: posición fumarola del experiment 39, o granule MODIS vacío H_S21_2).

## `diag_eff_threshold_k` (threshold efectivo aplicado, K)

| Clase | n | median | mean | p95 |
|---|---:|---:|---:|---:|
| TP | 6 | 277.885 | 281.380 | 290.055 |
| T4 | 2 | 286.030 | 286.030 | 289.414 |
| T2b | 12 | 281.940 | 281.718 | 286.156 |
