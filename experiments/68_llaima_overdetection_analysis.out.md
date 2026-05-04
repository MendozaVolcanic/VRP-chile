# P4 Llaima sobre-detección — análisis estadístico

Window: 2026-01-29 -> 2026-04-29

## CSV MIROVA Llaima 90d
Total records MIROVA Llaima (todos sensores, todos tipos): 1201
  - ALERTA_TERMICA: 0
  - RUTINA: 1166
  - FALSO_POSITIVO: 35
  Sensor MODIS: 376 records
  Sensor VIIRS: 431 records
  Sensor VIIRS375: 394 records

## Nuestros records Llaima 90d
Total records: 998
  con vrp_mw>0: 460

## Distribución espacial de nuestras detecciones (vrp_mw>0)
| pc_dist bin | n detecciones |
|---|---:|
| 0-2 km | 167 |
| 2-5 km | 63 |
| 5-10 km | 39 |
| 10-15 km | 80 |
| 15-20 km | 46 |
| >20 km | 65 |

## Distance class (Llaima inner_radius_km=5)
  summit (≤5km): 216
  far (>5km): 244
  None/unset: 0

## Sensor breakdown (vrp_mw>0)
  VIIRS375: 173
  VIIRS750: 149
  MODIS: 138

## Magnitud (vrp_mw global) distribution detecciones Llaima
  n: 460
  min: 0.021 MW | p25: 1.97 | mediana: 4.85 | p75: 35.30 | max: 931.29

## Sample 10 detecciones (top vrp)
| Fecha | Sensor | vrp_mw | pc_n | pc_vrp | pc_dist | dist_class | T1? | n_anom |
|---|---|---:|---:|---:|---:|---|:--:|---:|
| 2026-04-16 08:30 | MODIS_AQUA | 931.29 | 9 | 158.18 | 16.811 | far | N | 97 |
| 2026-02-11 02:55 | MODIS_TERRA | 549.66 | 5 | 59.232 | 20.865 | far | N | 71 |
| 2026-03-06 07:00 | MODIS_AQUA | 460.16 | 6 | 42.525 | 1.262 | far | N | 61 |
| 2026-03-01 01:35 | MODIS_TERRA | 440.25 | 6 | 44.438 | 14.347 | far | N | 53 |
| 2026-03-01 07:05 | MODIS_AQUA | 428.13 | 4 | 26.456 | 15.612 | far | N | 91 |
| 2026-04-08 06:40 | MODIS_AQUA | 422.16 | 3 | 51.866 | 27.07 | far | N | 28 |
| 2026-04-18 08:10 | MODIS_AQUA | 405.71 | 4 | 27.246 | 23.741 | far | N | 86 |
| 2026-03-19 07:05 | MODIS_AQUA | 352.31 | 17 | 28.256 | 16.512 | far | N | 267 |
| 2026-04-26 08:20 | MODIS_AQUA | 332.19 | 3 | 25.856 | 9.862 | far | N | 56 |
| 2026-03-21 08:20 | MODIS_AQUA | 304.46 | 3 | 22.106 | 5.056 | far | N | 36 |

## Veredicto P4 Llaima

- 460 detecciones nuestras vs 0 ALERTA_TERMICA MIROVA = sobre-detección consistente.
- 47% summit-class (216/460). Esto pasa filtro Driver A.
- 53% far-class. Driver A las suprime en frontend, pero quedan en JSON.
- Driver A NO ayuda si las detecciones son summit-class (aunque sean del lago llegando al borde inner).

Hipótesis MIROVA NRT: filtro de persistencia temporal (no detección si record único en 7 días),
o filtro de magnitud absoluta (descarta vrp<X MW), o supervisión humana NRT (parcial).
