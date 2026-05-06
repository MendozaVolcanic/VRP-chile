# C — Investigación pixel-level Phase 1 destrucción recall


================================================================================
## Lastarria

Refs MIROVA: 63, regresiones OFF→ON: 36

### Análisis pixel por record (sample top 5)

| Fecha | Sensor | MIROVA MW | OFF pc_vrp | OFF pc_n | OFF pc_dist | n_anom | n_t1 | t_bg | std_bg | t_max | nti_max |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2026-04-29 06:18 | VIIRS375 | 0.100 | 2.91 | 67 | 0.734 | 82 | 79 | 262.26 | 1.65 | 270.91 | -0.962 | b? |
| 2026-04-23 06:30 | VIIRS375 | 0.070 | 0.81 | 26 | 1.7 | 70 | 67 | 263.30 | 1.97 | 273.38 | -0.958 | b? |
| 2026-04-22 06:30 | VIIRS375 | 0.050 | 0.98 | 27 | 1.9 | 54 | 52 | 263.34 | 2.11 | 271.29 | -0.960 | a |
| 2026-04-18 05:36 | VIIRS375 | 0.150 | 2.41 | 48 | 1.776 | 86 | 82 | 264.14 | 2.40 | 276.43 | -0.955 | b? |
| 2026-04-15 06:30 | VIIRS375 | 0.160 | 0.90 | 27 | 1.439 | 67 | 66 | 262.79 | 1.89 | 272.79 | -0.959 | b? |

### Veredicto Lastarria

- Regresiones totales: 36
- **Caso (a) ruido bg-tibio**: 9 (25%)
- **Caso (b) señal real**: 25 (69%)
- Indeterminado: 0
  → Phase 1 destruye señal real en Lastarria; revertir.

================================================================================
## Villarrica

Refs MIROVA: 3, regresiones OFF→ON: 2

### Análisis pixel por record (sample top 5)

| Fecha | Sensor | MIROVA MW | OFF pc_vrp | OFF pc_n | OFF pc_dist | n_anom | n_t1 | t_bg | std_bg | t_max | nti_max |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2026-03-08 06:00 | VIIRS375 | 0.210 | 6.63 | 69 | 1.277 | 74 | 71 | 282.62 | 3.07 | 290.85 | -0.928 | a |
| 2026-02-26 05:42 | VIIRS375 | 0.120 | 10.11 | 84 | 1.159 | 95 | 85 | 281.25 | 3.49 | 292.03 | -0.926 | a |

### Veredicto Villarrica

- Regresiones totales: 2
- **Caso (a) ruido bg-tibio**: 2 (100%)
- **Caso (b) señal real**: 0 (0%)
- Indeterminado: 0
  → Phase 1 hace lo correcto en Villarrica; recall caído refleja eliminación falsos.

================================================================================
## PlanchonPeteroa

Refs MIROVA: 31, regresiones OFF→ON: 26

### Análisis pixel por record (sample top 5)

| Fecha | Sensor | MIROVA MW | OFF pc_vrp | OFF pc_n | OFF pc_dist | n_anom | n_t1 | t_bg | std_bg | t_max | nti_max |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2026-04-27 06:06 | VIIRS375 | 0.070 | 1.38 | 37 | 1.736 | 84 | 83 | 269.58 | 5.05 | 277.20 | -0.944 | a |
| 2026-04-27 05:18 | VIIRS375 | 0.050 | 1.79 | 50 | 1.058 | 71 | 69 | 269.61 | 5.17 | 278.14 | -0.944 | a |
| 2026-04-26 05:36 | VIIRS375 | 0.070 | 2.22 | 78 | 1.051 | 88 | 83 | 268.51 | 4.70 | 278.63 | -0.949 | a |
| 2026-04-25 05:54 | VIIRS375 | 0.090 | 1.35 | 43 | 1.766 | 75 | 71 | 268.70 | 4.82 | 279.55 | -0.948 | a |
| 2026-04-24 06:18 | VIIRS375 | 0.050 | 0.78 | 29 | 1.61 | 57 | 53 | 269.49 | 5.27 | 278.25 | -0.945 | a |

### Veredicto PlanchonPeteroa

- Regresiones totales: 26
- **Caso (a) ruido bg-tibio**: 26 (100%)
- **Caso (b) señal real**: 0 (0%)
- Indeterminado: 0
  → Phase 1 hace lo correcto en PlanchonPeteroa; recall caído refleja eliminación falsos.


## Veredicto global

Si caso (a) domina en los 3 volcanes → Phase 1 es correcto, recall caído es artefacto.
Si caso (b) domina → Phase 1 destruye señal real, revertir.
Si mixto → decisión basada en preferencia recall vs ratio.
