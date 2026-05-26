# F2.5.b — Lascar records perdidos con cap S71 (PR #112)

**Ventana**: 2026-02-20 → 2026-05-20 (90 días).
**Comparación**: pre-cap (snapshot commit `2a6c8f8`, parent de #112) vs `data/mirova_equivalent_path_d_cap_v1/Lascar.json` (cap-only reproc, S71).
**Ground truth**: CONS (1056 rows Lascar) + OCR (98 rows Lascar) en la ventana, matching ±60 min en familia sensor (MODIS/VIIRS).

## Universo

| Set | Records | Notas |
|---|---|---|
| pre-cap (mirova_equivalent) | 815 | I+M-bands |
| cap-only (path_d_cap_v1) | 500 | solo I-band/MODIS — perfil A/B no reproc VIIRS 750m |
| **shared (matching keys)** | **500** | universo válido de comparación |
| only_in_pre | 315 | **todos VIIRS_*_750**, NO lost-to-cap (perfil A/B no los procesó) |

## Categorías

| | Count | Cat A (MIROVA detect) | Cat B (MIROVA RUTINA/no match) | Cat C |
|---|---|---|---|---|
| **LOST** (det → no-det) | **13** | **6 (46%)** | **7 (54%)** | — |
| **CAPPED** (det ambos, magnitud distinta) | **320** | **185 (58%)** | **135 (42%)** | — |

## Detalle LOST (13 records)

| datetime_utc | sensor | pre_pc_vrp | cap_pc_vrp | t_bg | ctx_path | categ | mirova |
|---|---|---|---|---|---|---|---|
| 2026-02-22 04:54 | VIIRS_SNPP | 1.034 | 0.009 | 272.3 | 1 | A | ALERTA 1.26 MW @2.4km |
| 2026-02-26 04:48 | VIIRS_NOAA21 | 1.237 | 0.007 | 270.1 | 1 | A | OCR 0.42 MW |
| 2026-02-27 05:00 | VIIRS_SNPP | 0.850 | 0.006 | 269.3 | 2 | A | OCR 0.33 MW |
| 2026-03-03 06:36 | VIIRS_NOAA21 | 0.903 | 0.007 | 267.4 | 1 | A | ALERTA 2.41 MW @1.5km |
| 2026-03-19 06:36 | VIIRS_NOAA21 | 0.667 | 0.008 | 267.1 | 1 | A | ALERTA 2.96 MW @1.5km |
| 2026-05-13 04:54 | VIIRS_SNPP | 0.099 | 0.000 | 264.0 | 3 | A | ALERTA 0.69 MW @1.7km |
| 2026-04-14 00:50 | MODIS_TERRA | 22.896 | 0.000 | 271.4 | 1 | B (no match) | — |
| 7 records VIIRS | varios | 0.7-2.3 | 0.0 | 264-270 | 1-7 | B (RUTINA 0) | RUTINA 0 MW |

**Mecanismo**: en todos los LOST el `diag_n_dnti_ctx_path > 0` y `diag_n_bt_path = diag_n_nti_path = 0` → la detección venía 100% de path D contextual. El cap llevó `pc.vrp_mw` de ~1 MW a ~0.005 MW (cluster degenera a 1-pixel sub-floor), no a 5 MW. Esto sugiere que **el cap NO solo capea — para clusters chicos en t_bg<270K colapsa el primary_cluster a sub-floor** (probablemente porque el cap se aplica al pixel antes de clustering y los pixels post-cap caen debajo del threshold de inclusión).

## Top 10 CAPPED (mayor reducción)

| datetime | sensor | pre_pc | cap_pc | ratio | t_bg | categ | mirova |
|---|---|---|---|---|---|---|---|
| 2026-02-20 02:20 | MODIS_TERRA | 71.6 | 0.40 | 178× | 241 | B | RUTINA 0 |
| 2026-04-05 08:00 | MODIS_AQUA | 21.6 | 0.24 | 90× | 274 | B | RUTINA 0 |
| 2026-02-28 01:00 | MODIS_TERRA | 70.1 | 2.21 | 32× | 273 | B | RUTINA 0 |
| 2026-03-01 01:40 | MODIS_TERRA | 3.76 | 0.06 | 61× | 275 | **A** | ALERTA 1.81 |
| 2026-02-23 04:54 | VIIRS_NOAA20 | 1.24 | 0.02 | 56× | 270 | A (FP MIROVA) | FALSO_POSITIVO 0.74 |
| 2026-03-31 05:00 | VIIRS_SNPP | 3.42 | 0.07 | 52× | 268 | A | ALERTA 1.03 |

Los Cat-A capped son consistentes con MIROVA (cuando MIROVA reporta ~1-3 MW, post-cap nos vamos a 0.06-0.24 MW — sub-cap, ratio NEW/MIROVA cae a <0.1×). Esto sugiere que el cap **sub-corrige** en algunos eventos reales también.

## Verdict

- **LOST 6/13 son Cat A (TP perdido real)** — todos VIIRS path-D-only, MIROVA detecta ALERTA con VRP_MW 0.3-3 MW @ 1.5-2.4 km. El cap los aniquila completamente (1 MW → 0.007 MW) en lugar de capearlos a 5 MW. **Esto explica directamente la -9.3pp Lascar recall** observada en F2.2.
- **LOST 7/13 son Cat B** (incluye 1 MODIS 22.9 MW sin match — sospechoso FP eliminado, saludable).
- **CAPPED 185/320 son Cat A** (58%): donde MIROVA sí detectaba — el cap ahí reduce magnitud sistemáticamente por debajo de MIROVA, perjudicando el ratio NEW/MIROVA pero NO bajando recall (siguen contando como detección).

**Distribución global**: de 333 records afectados (lost+capped), **191 son Cat A (MIROVA detect, 57%)** y **142 Cat B (no MIROVA, 43%)**. No alcanza el umbral >70% B "cap saludable" ni >50% A "cap demasiado agresivo".

## Recomendación

**El verdict es MIXED, sesgado hacia Cat A**:

1. La regression -9.3pp recall Lascar atribuida a unsuitable filters/K1 retire en F2.2 es **principalmente atribuible al cap S71**, no al split F1.2 — el cap aniquila 6 TPs reales VIIRS path-D-only.
2. El mecanismo "aniquilación vs capeo" es un bug del cap: se esperaba `vrp_mw → 5 MW`, está dando `vrp_mw → 0.007 MW`. Worth investigar si el cap se aplica pre-cluster (entonces colapsa clusters chicos) o post-cluster.
3. **Sub-recomendación operacional**: antes de adoptar cap permanente en Lascar, sería prudente:
   - Investigar el mecanismo de aniquilación (¿cap pre-cluster vs post-cluster?).
   - Considerar **per-vol opt-out cap para Lascar** (volcán Tier A Alto, alta SNR, no sufre D9 cirrus FPs típicos).
   - O reformular el cap: aplicar solo a `pc.vrp_mw > cap_mw` (no a todo pixel).

El cap es necesario para D9 (FPs cirrus alto en otros vols), pero en Lascar genera más daño (6 TP loss + 185 TPs sub-corregidos) que beneficio (1 MODIS 22.9 MW sospechoso eliminado + 132 RUTINA capeados de no-match).
