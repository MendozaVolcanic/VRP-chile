# Validación Test 1 vs 6 ALERTAs MIROVA Villarrica (S25 final)

Para cada ref MIROVA, buscamos los records VIIRS 375m de los 3 satélites
(SNPP/NOAA20/NOAA21) en ±60 min en cada profile A/B.

| Ref MIROVA | VRP MIROVA | Records (en/dis) | Test 1 disparó | n_anom dis | n_anom en | Veredicto |
|---|---:|---|---|---:|---:|---|
| 2026-01-13 05:48 | 0.050 | 3/3 | 3/3 | 3 | 3 | = Ambos detectan |
| 2026-01-14 05:48 | 0.070 | 4/4 | 3/4 | 4 | 4 | = Ambos detectan |
| 2026-01-19 05:54 | 0.090 | 4/4 | 3/4 | 4 | 4 | = Ambos detectan |
| 2026-02-26 05:42 | 0.120 | 4/4 | 3/4 | 4 | 4 | = Ambos detectan |
| 2026-03-08 06:00 | 0.210 | 4/4 | 3/4 | 3 | 3 | = Ambos detectan |
| 2026-04-09 06:00 | 0.110 | 4/4 | 3/4 | 3 | 3 | = Ambos detectan |

## Recall summary

- Refs MIROVA con ≥1 granule disparando Test 1 (enabled): **6/6**
- Refs MIROVA con ≥1 granule detectado por paths actuales (disabled): 6/6

## Detalle por record (enabled profile)

| Ref | Sensor | Triggered Test 1 | K obs | n_test1 | n_anom | n_bt | n_dnti | VRP | class |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| 2026-01-13 05:48 | VIIRS_NOAA21 | ✓ | 5.3 | 68 | 1367 | 1293 | 23 | 763.6780 | far |
| 2026-01-13 05:48 | VIIRS_SNPP | ✓ | 4.3 | 88 | 2014 | 1916 | 25 | 1189.9450 | far |
| 2026-01-13 05:48 | VIIRS_NOAA20 | ✓ | 3.4 | 69 | 1689 | 1616 | 14 | 963.0320 | far |
| 2026-01-14 05:48 | VIIRS_NOAA21 | ✓ | 8.2 | 43 | 1026 | 978 | 9 | 471.6820 | far |
| 2026-01-14 05:48 | VIIRS_SNPP | ✓ | 6.3 | 76 | 1551 | 1473 | 13 | 822.3470 | far |
| 2026-01-14 05:48 | VIIRS_NOAA20 | ✓ | 4.3 | 86 | 1876 | 1786 | 12 | 0.0000 | far |
| 2026-01-14 05:48 | VIIRS_NOAA21 | ✗ | 2.4 | 0 | 921 | 919 | 3 | 412.8210 | far |
| 2026-01-19 05:54 | VIIRS_NOAA21 | ✓ | 6.0 | 53 | 70 | 15 | 2 | 0.0000 | far |
| 2026-01-19 05:54 | VIIRS_SNPP | ✓ | 9.2 | 73 | 112 | 32 | 7 | 0.0000 | far |
| 2026-01-19 05:54 | VIIRS_NOAA20 | ✓ | 6.7 | 86 | 119 | 29 | 4 | 0.0000 | far |
| 2026-01-19 05:54 | VIIRS_NOAA21 | ✗ | 2.7 | 0 | 17 | 17 | 0 | 8.0660 | far |
| 2026-02-26 05:42 | VIIRS_NOAA21 | ✓ | 9.7 | 69 | 1285 | 1213 | 3 | 495.4290 | far |
| 2026-02-26 05:42 | VIIRS_SNPP | ✓ | 4.8 | 49 | 1337 | 1279 | 15 | 634.4730 | far |
| 2026-02-26 05:42 | VIIRS_NOAA20 | ✓ | 5.0 | 85 | 1927 | 1840 | 10 | 967.3560 | far |
| 2026-02-26 05:42 | VIIRS_NOAA21 | ✗ | 2.8 | 0 | 1076 | 1073 | 3 | 468.0900 | far |
| 2026-03-08 06:00 | VIIRS_NOAA21 | ✓ | 9.3 | 59 | 286 | 226 | 1 | 74.0560 | far |
| 2026-03-08 06:00 | VIIRS_SNPP | ✓ | 5.5 | 73 | 1052 | 975 | 4 | 386.6260 | far |
| 2026-03-08 06:00 | VIIRS_NOAA20 | ✓ | 4.2 | 71 | 1071 | 999 | 3 | 398.2750 | far |
| 2026-03-08 06:00 | VIIRS_NOAA21 | ✗ | 3.0 | 0 | 0 | 0 | 0 | 0.0000 | - |
| 2026-04-09 06:00 | VIIRS_NOAA21 | ✓ | 7.0 | 41 | 44 | 1 | 2 | 0.0000 | far |
| 2026-04-09 06:00 | VIIRS_SNPP | ✓ | 5.6 | 72 | 75 | 3 | 0 | 0.0000 | far |
| 2026-04-09 06:00 | VIIRS_NOAA20 | ✓ | 4.5 | 72 | 76 | 2 | 2 | 0.0000 | far |
| 2026-04-09 06:00 | VIIRS_NOAA21 | ✗ | 2.0 | 0 | 0 | 0 | 0 | 0.0000 | - |

## Veredicto Test 1 (clon-MIROVA recall)

**Recall Villarrica enabled = 1.00 (6/6)**
Recall Villarrica disabled (control) = 1.00 (6/6)

Test 1 captura 6 refs nuevas pero queda corto del 50%. **EVALUAR**:
  - Bajar k_sigma de 3.0 a 2.5 (más permisivo).
  - Refinar inner_ring_km / roi_km.
  - Verificar que el cálculo en pipeline coincide con el POC offline.