# Lascar diagnostic report (Paso 1)

**Source JSON**: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\lascar_session5_snapshot.json`
**MIROVA refs**: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\data\mirova\Lascar.json` — 175 records
**Our records**: 644
**Matched pairs (same-day, same-family, dt<=30min, both VRP>0)**: 130

---

## Q1. Why are we missing 23 MIROVA refs?

Category breakdown (n=175):

| Category | Count | % |
|---|---:|---:|
| matched_ok | 107 | 61.1% |
| close_pass_low_vrp | 23 | 13.1% |
| close_pass_zero_vrp | 23 | 13.1% |
| no_close_pass | 22 | 12.6% |
| no_record_in_day | 0 | 0.0% |

Notes:
- `matched_ok`: we detect the ref with a reasonable ratio (>0.5).
- `close_pass_low_vrp`: close-time match exists but our VRP < 50% of MIROVA's.
- `close_pass_zero_vrp`: the SAME overpass exists in our data but produced vrp=0. This is the most actionable category.
- `no_close_pass`: same day but closest record >60 min off — likely a different overpass (day vs night).
- `no_record_in_day`: we have no matching-sensor record on that UTC day at all.

### `close_pass_zero_vrp` detail (n=23)

| MIROVA dt | MIROVA sensor | MIROVA VRP | Our sensor | dt_min | t_bg | t_max | n_anom | n_vent | n_cloud | hs_dist |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 2026-01-11 05:00 | VIIRS | 0.27 | VIIRS_NOAA20_750 | 0 | 265.77 | 271.1 | 0 | 0 | None | None |
| 2026-01-15 01:45 | MODIS | 0.89 | MODIS_TERRA | 0 | 276.32 | 281.96 | 0 | 0 | None | None |
| 2026-01-18 06:12 | VIIRS375 | 0.4 | VIIRS_NOAA20 | 0 | None | None | 0 | 0 | 1326 | None |
| 2026-01-21 06:36 | VIIRS375 | 0.75 | VIIRS_SNPP | 0 | 270.38 | 276.13 | 0 | 0 | 406 | None |
| 2026-01-24 06:00 | VIIRS375 | 0.05 | VIIRS_NOAA20 | 0 | 267.03 | 269.78 | 0 | 0 | 1122 | None |
| 2026-01-25 05:42 | VIIRS | 0.39 | VIIRS_NOAA20_750 | 0 | 270.66 | 275.47 | 0 | 0 | None | None |
| 2026-01-28 04:42 | VIIRS375 | 0.71 | VIIRS_NOAA20 | 0 | 269.86 | 275.56 | 0 | 0 | 5 | None |
| 2026-02-03 06:12 | VIIRS375 | 0.14 | VIIRS_NOAA20 | 0 | 269.61 | 277.34 | 0 | 0 | 87 | None |
| 2026-02-04 05:54 | VIIRS | 0.23 | VIIRS_NOAA20_750 | 0 | 269.45 | 274.85 | 0 | 0 | None | None |
| 2026-02-05 05:36 | VIIRS | 0.28 | VIIRS_NOAA20_750 | 0 | 269.6 | 274.98 | 0 | 0 | None | None |
| 2026-02-09 01:40 | MODIS | 1.67 | MODIS_TERRA | 0 | 278.44 | 283.55 | 0 | 0 | None | None |
| 2026-02-11 01:20 | MODIS | 0.32 | MODIS_TERRA | 0 | 277.61 | 283.11 | 0 | 0 | None | None |
| 2026-02-12 06:24 | VIIRS | 0.15 | VIIRS_SNPP_750 | 0 | 270.61 | 274.71 | 0 | 0 | None | None |
| 2026-02-16 01:20 | MODIS | 1.04 | MODIS_TERRA | 0 | 278.44 | 282.88 | 0 | 0 | None | None |
| 2026-02-17 05:06 | VIIRS375 | 0.09 | VIIRS_NOAA20 | 0 | 268.08 | 268.11 | 0 | 0 | 1213 | None |
| 2026-02-23 04:54 | VIIRS375 | 0.74 | VIIRS_NOAA20 | 0 | 269.98 | 276.47 | 0 | 0 | 0 | None |
| 2026-02-25 06:00 | VIIRS | 0.27 | VIIRS_NOAA20_750 | 0 | 269.6 | 273.71 | 0 | 0 | None | None |
| 2026-02-26 05:42 | VIIRS | 0.21 | VIIRS_NOAA20_750 | 0 | 270.21 | 275.83 | 0 | 0 | None | None |
| 2026-02-28 05:00 | VIIRS | 0.65 | VIIRS_NOAA20_750 | 0 | 266.13 | 271.53 | 0 | 0 | None | None |
| 2026-03-01 01:40 | MODIS | 1.81 | MODIS_TERRA | 0 | 274.96 | 282.42 | 0 | 0 | None | None |
| 2026-03-04 01:55 | MODIS | 0.35 | MODIS_TERRA | 0 | 274.33 | 279.75 | 0 | 0 | None | None |
| 2026-03-16 06:24 | VIIRS | 0.51 | VIIRS_SNPP_750 | 0 | 265.78 | 271.2 | 0 | 0 | None | None |
| 2026-03-27 04:54 | VIIRS | 0.33 | VIIRS_NOAA20_750 | 0 | 267.68 | 271.24 | 0 | 0 | None | None |

### `close_pass_low_vrp` detail (n=23)

| MIROVA dt | MIROVA sensor | MIROVA VRP | Our sensor | dt_min | Our VRP | ratio |
|---|---|---:|---|---:|---:|---:|
| 2026-01-15 05:24 | VIIRS | 1.31 | VIIRS_NOAA20_750 | 0 | 0.422 | 0.32 |
| 2026-01-27 05:00 | VIIRS375 | 0.48 | VIIRS_NOAA20 | 0 | 0.161 | 0.34 |
| 2026-02-12 05:00 | VIIRS | 0.68 | VIIRS_NOAA20_750 | 0 | 0.228 | 0.34 |
| 2026-02-12 05:00 | VIIRS375 | 1.17 | VIIRS_NOAA20 | 0 | 0.503 | 0.43 |
| 2026-02-12 07:35 | MODIS | 2.96 | MODIS_AQUA | 0 | 0.547 | 0.18 |
| 2026-02-14 01:40 | MODIS | 3.43 | MODIS_TERRA | 0 | 1.289 | 0.38 |
| 2026-02-22 07:25 | MODIS | 2.73 | MODIS_AQUA | 0 | 0.328 | 0.12 |
| 2026-02-25 06:00 | VIIRS375 | 2.1 | VIIRS_NOAA20 | 0 | 0.238 | 0.11 |
| 2026-02-28 05:00 | VIIRS375 | 0.8 | VIIRS_NOAA20 | 0 | 0.288 | 0.36 |
| 2026-03-02 07:40 | MODIS | 1.64 | MODIS_AQUA | 0 | 0.761 | 0.46 |
| 2026-03-04 07:15 | MODIS | 2.28 | MODIS_AQUA | 0 | 0.793 | 0.35 |
| 2026-03-05 05:06 | VIIRS375 | 1.73 | VIIRS_NOAA20 | 0 | 0.825 | 0.48 |
| 2026-03-06 01:35 | MODIS | 1.42 | MODIS_TERRA | 0 | 0.559 | 0.39 |
| 2026-03-07 07:35 | MODIS | 2.7 | MODIS_AQUA | 0 | 0.756 | 0.28 |
| 2026-03-09 01:55 | MODIS | 2.02 | MODIS_TERRA | 0 | 0.393 | 0.19 |
| 2026-03-11 04:54 | VIIRS375 | 0.81 | VIIRS_NOAA20 | 0 | 0.299 | 0.37 |
| 2026-03-12 06:18 | VIIRS375 | 0.28 | VIIRS_NOAA20 | 0 | 0.107 | 0.38 |
| 2026-03-12 07:25 | MODIS | 2.22 | MODIS_AQUA | 0 | 0.792 | 0.36 |
| 2026-03-14 01:55 | MODIS | 2.44 | MODIS_TERRA | 0 | 0.870 | 0.36 |
| 2026-03-17 06:24 | VIIRS375 | 1.84 | VIIRS_NOAA20 | 0 | 0.079 | 0.04 |

### `no_record_in_day` detail (n=0)


### `no_close_pass` detail (n=22)

- MIROVA 2026-01-14 17:54 VIIRS375 VRP=0.76 → closest our = VIIRS_NOAA20 Δ=726min VRP=0.985
- MIROVA 2026-01-15 17:54 VIIRS375 VRP=0.51 → closest our = VIIRS_NOAA20 Δ=750min VRP=1.102
- MIROVA 2026-01-23 18:42 VIIRS375 VRP=0.33 → closest our = VIIRS_NOAA20 Δ=744min VRP=0.000
- MIROVA 2026-01-23 20:05 MODIS VRP=0.65 → closest our = MODIS_AQUA Δ=730min VRP=4.596
- MIROVA 2026-02-10 18:06 VIIRS375 VRP=2.1 → closest our = VIIRS_NOAA20 Δ=744min VRP=7.174
- MIROVA 2026-02-14 18:30 VIIRS375 VRP=1.85 → closest our = VIIRS_NOAA20 Δ=744min VRP=5.585
- MIROVA 2026-02-21 18:00 VIIRS375 VRP=3.17 → closest our = VIIRS_NOAA20 Δ=744min VRP=5.308
- MIROVA 2026-02-22 17:42 VIIRS375 VRP=1.22 → closest our = VIIRS_SNPP Δ=666min VRP=0.000
- MIROVA 2026-02-26 17:48 VIIRS375 VRP=0.63 → closest our = VIIRS_NOAA20 Δ=726min VRP=0.457
- MIROVA 2026-02-26 18:06 VIIRS375 VRP=0.53 → closest our = VIIRS_NOAA20 Δ=744min VRP=0.457

---

## Q2. Pairs with worst ratio (systematic bias?)

Global stats on 130 pairs: median=0.978 mean=1.035
  min=0.043 max=3.800 stdev=0.583

### Bottom 15 (we underestimate most)

| MIROVA dt | MIROVA sensor | MIROVA VRP | Our dt | Our sensor | Our VRP | ratio |
|---|---|---:|---|---|---:|---:|
| 2026-02-15 05:48 | VIIRS375 | 4.700 | 2026-02-15 05:48 | VIIRS_NOAA20 | 7.668 | 1.63 |
| 2026-03-09 05:36 | VIIRS375 | 3.440 | 2026-03-09 05:36 | VIIRS_NOAA20 | 5.669 | 1.65 |
| 2026-02-15 05:48 | VIIRS | 4.540 | 2026-02-15 05:48 | VIIRS_NOAA20_750 | 7.500 | 1.65 |
| 2026-02-20 05:54 | VIIRS | 1.570 | 2026-02-20 05:54 | VIIRS_NOAA20_750 | 2.603 | 1.66 |
| 2026-03-19 05:48 | VIIRS375 | 2.760 | 2026-03-19 05:48 | VIIRS_NOAA20 | 4.669 | 1.69 |
| 2026-03-03 05:48 | VIIRS375 | 2.410 | 2026-03-03 05:48 | VIIRS_NOAA20 | 4.166 | 1.73 |
| 2026-02-10 05:42 | VIIRS375 | 4.140 | 2026-02-10 05:42 | VIIRS_NOAA20 | 7.174 | 1.73 |
| 2026-03-22 04:48 | VIIRS375 | 0.070 | 2026-03-22 04:48 | VIIRS_NOAA20 | 0.129 | 1.84 |
| 2026-03-09 05:36 | VIIRS | 2.760 | 2026-03-09 05:36 | VIIRS_NOAA20_750 | 5.274 | 1.91 |
| 2026-03-14 05:42 | VIIRS375 | 2.720 | 2026-03-14 05:42 | VIIRS_NOAA20 | 5.425 | 1.99 |
| 2026-03-28 06:18 | VIIRS375 | 0.110 | 2026-03-28 06:18 | VIIRS_NOAA20 | 0.226 | 2.05 |
| 2026-02-15 07:55 | MODIS | 0.620 | 2026-02-15 07:55 | MODIS_AQUA | 1.550 | 2.50 |
| 2026-03-18 01:15 | MODIS | 0.270 | 2026-03-18 01:15 | MODIS_TERRA | 0.707 | 2.62 |
| 2026-02-11 07:00 | MODIS | 0.480 | 2026-02-11 07:00 | MODIS_AQUA | 1.530 | 3.19 |
| 2026-01-11 06:24 | VIIRS375 | 0.040 | 2026-01-11 06:24 | VIIRS_SNPP | 0.152 | 3.80 |

### Top 15 (we overestimate most)

| MIROVA dt | MIROVA sensor | MIROVA VRP | Our dt | Our sensor | Our VRP | ratio |
|---|---|---:|---|---|---:|---:|
| 2026-03-17 06:24 | VIIRS375 | 1.840 | 2026-03-17 06:24 | VIIRS_NOAA20 | 0.079 | 0.04 |
| 2026-02-25 06:00 | VIIRS375 | 2.100 | 2026-02-25 06:00 | VIIRS_NOAA20 | 0.238 | 0.11 |
| 2026-02-22 07:25 | MODIS | 2.730 | 2026-02-22 07:25 | MODIS_AQUA | 0.328 | 0.12 |
| 2026-02-12 07:35 | MODIS | 2.960 | 2026-02-12 07:35 | MODIS_AQUA | 0.547 | 0.18 |
| 2026-03-09 01:55 | MODIS | 2.020 | 2026-03-09 01:55 | MODIS_TERRA | 0.393 | 0.19 |
| 2026-03-20 07:40 | MODIS | 3.820 | 2026-03-20 07:40 | MODIS_AQUA | 0.842 | 0.22 |
| 2026-03-07 07:35 | MODIS | 2.700 | 2026-03-07 07:35 | MODIS_AQUA | 0.756 | 0.28 |
| 2026-01-15 05:24 | VIIRS | 1.310 | 2026-01-15 05:24 | VIIRS_NOAA20_750 | 0.422 | 0.32 |
| 2026-02-12 05:00 | VIIRS | 0.680 | 2026-02-12 05:00 | VIIRS_NOAA20_750 | 0.228 | 0.34 |
| 2026-01-27 05:00 | VIIRS375 | 0.480 | 2026-01-27 05:00 | VIIRS_NOAA20 | 0.161 | 0.34 |
| 2026-03-04 07:15 | MODIS | 2.280 | 2026-03-04 07:15 | MODIS_AQUA | 0.793 | 0.35 |
| 2026-03-14 01:55 | MODIS | 2.440 | 2026-03-14 01:55 | MODIS_TERRA | 0.870 | 0.36 |
| 2026-03-12 07:25 | MODIS | 2.220 | 2026-03-12 07:25 | MODIS_AQUA | 0.792 | 0.36 |
| 2026-02-28 05:00 | VIIRS375 | 0.800 | 2026-02-28 05:00 | VIIRS_NOAA20 | 0.288 | 0.36 |
| 2026-03-11 04:54 | VIIRS375 | 0.810 | 2026-03-11 04:54 | VIIRS_NOAA20 | 0.299 | 0.37 |

---

## Q3. MODIS sensor-specific gap (session 5 median 0.79 — why?)

Pairs: 36  median=0.789  mean=0.938

By magnitude bucket:

| Bucket | n | median | mean |
|---|---:|---:|---:|
| weak (<0.5 MW) | 2 | 2.903 | 2.903 |
| low (0.5-2 MW) | 18 | 1.086 | 1.090 |
| moderate (2-10 MW) | 16 | 0.366 | 0.521 |
| high (>10 MW) | 0 | 0.000 | 0.000 |

By platform:

- Terra: n=13 median=0.725 mean=0.817
- Aqua:  n=23 median=0.904 mean=1.006


---

## Next-step hypotheses (to decide after reading this)

TBD — fill after reviewing the report.
