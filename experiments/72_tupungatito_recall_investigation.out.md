# Tupungatito recall investigation

Window: 2026-01-29 -> 2026-04-29
Refs MIROVA Tupungatito ALERTA_TERMICA: 68

## Distribución refs MIROVA Tupungatito

VRP: min=0.030, p25=0.120, mediana=0.210, p75=0.260, max=0.590
Sensores: {'VIIRS375': 60, 'VIIRS': 8}

## Categorización refs MIROVA Tupungatito

- TPs (nosotros detectamos summit): 33 (48.5%)
- FNs vrp_mw=0 (no detección nuestra): 35 (51.5%)
- FNs dist_class=far (cluster lejos): 0 (0.0%)
- FNs sin match temporal (granule no procesado?): 0 (0.0%)

### H1: distribución VRP MIROVA en FNs

FNs vrp=0 (35): min=0.030, mediana=0.170, max=0.590

### H4: distribución sensor en FNs

  - ('vrp=0', 'VIIRS'): 8
  - ('vrp=0', 'VIIRS375'): 27

### H2 + H3: diagnostics pipeline en FNs vrp=0 (top 10)

| Fecha | Sensor | MIROVA MW | T1? | n_t1pix | t_bg | std_bg | t_max | nti_max | n_anom |
|---|---|---:|:--:|---:|---:|---:|---:|---:|---:|
| 2026-04-27 05:18 | VIIRS_NOAA20 | 0.110 | Y | 88 | 264.52 | 3.205 | 280.6 | -0.949223 | 88 |
| 2026-04-26 04:48 | VIIRS_NOAA21 | 0.110 | Y | 54 | 264.4 | 3.286 | 278.46 | -0.952554 | 54 |
| 2026-04-25 05:54 | VIIRS_NOAA20 | 0.200 | Y | 80 | 264.25 | 3.114 | 278.91 | -0.9516 | 80 |
| 2026-04-24 06:12 | VIIRS_NOAA20 | 0.110 | Y | 55 | 264.81 | 3.466 | 280.1 | -0.949752 | 55 |
| 2026-04-23 06:36 | VIIRS_NOAA20 | 0.030 | Y | 40 | 264.37 | 3.36 | 279.67 | -0.9505 | 40 |
| 2026-04-22 06:00 | VIIRS_NOAA21 | 0.030 | Y | 68 | 264.87 | 2.809 | 277.55 | -0.95363 | 68 |
| 2026-04-21 06:18 | VIIRS_NOAA21 | 0.120 | Y | 62 | 263.82 | 3.052 | 277.66 | -0.953505 | 62 |
| 2026-04-21 05:30 | VIIRS_NOAA20 | 0.200 | Y | 85 | 264.14 | 3.129 | 278.16 | -0.952702 | 85 |
| 2026-04-15 05:42 | VIIRS_NOAA20_750 | 0.320 | N | 0 | 263.09 | 4.054 | 277.9 | -0.915195 | 1 |
| 2026-04-14 05:12 | VIIRS_NOAA21 | 0.100 | Y | 68 | 268.16 | 4.095 | 284.84 | -0.941733 | 68 |

## Veredicto preliminar

- 31/35 FNs vrp=0 son MIROVA<0.3 MW (sub-pixel) — H1 probable.
