# S26 D final — Test 1 Villarrica vs 6 ALERTAs MIROVA

Profile: `mirova_equivalent_villarrica_test1` (Test 1 activo + fix VRP-clip).
Workflow: `reproc-villarrica-test1-refs.yml` 5 ventanas refs MIROVA.

| Ref MIROVA | VRP MIROVA | Records VIIRS375 | Test1 disparó | Hit summit | VRP nuestro |
|---|---:|---:|---:|---|---:|
| 2026-01-13 05:48 | 0.050 | 3 | 3/3 | ✗ | 562.787 |
| 2026-01-14 05:48 | 0.070 | 4 | 3/4 | ✗ | 367.639 |
| 2026-01-19 05:54 | 0.090 | 4 | 3/4 | ✗ | 17.932 |
| 2026-02-26 05:42 | 0.120 | 4 | 0/4 | ✗ | 452.773 |
| 2026-03-08 06:00 | 0.210 | 4 | 3/4 | ✗ | 209.443 |
| 2026-04-09 06:00 | 0.110 | 4 | 3/4 | ✗ | 1.201 |

## Resumen

- Refs MIROVA: 6
- Refs con summit-class hit (vrp_mw>0): **0/6** (recall 0.00)
- Refs con Test 1 disparando: **5/6**

Pre-D (sin Test 1): recall summit Villarrica era 0/6.

**RESULTADO: ✗ NO APROBADO** → Test 1 en pipeline no captura.