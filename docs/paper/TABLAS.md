# Tablas del manuscrito — generadas por `scripts/paper_numbers.py`

> Generado 2026-09-07 06:42 UTC · HEAD `c421005c8` · ventana 2026-01-01 → 2026-09-07 · ground truth CONS ∪ OCR (loader canónico). **No editar a mano: regenerar.**

Definiciones: ver docstring del script y `numbers.json` → `definiciones`.


## Table 2 — Tier A volcanoes

| Volcano | Vent (lat, lon) | MIROVA grid centre (lat, lon) | R (km) | inner (km) | n records | MODIS / V750 / V375 | first | last |
|---|---|---|---|---|---|---|---|---|
| Puyehue - Cordón Caulle | -40.525499, -72.146137 | -40.5903, -72.1187 | 25 | 20 | 2566 | 530 / 1014 / 1022 | 2026-01-29 02:35 | 2026-09-07 02:30 |
| Villarrica | -39.420227, -71.939876 | -39.42177, -71.93391 | 25 | 5 | 2806 | 561 / 1121 / 1124 | 2026-01-01 02:20 | 2026-09-07 02:30 |
| Láscar | -23.36293, -67.731416 | -23.37041, -67.73102 | 25 | 5 | 2049 | 422 / 810 / 817 | 2026-01-29 01:00 | 2026-09-07 01:00 |
| Copahue | -37.856, -71.183 | -37.85617, -71.18458 | 25 | 4 | 2408 | 496 / 952 / 960 | 2026-01-29 02:35 | 2026-09-06 07:30 |
| Nevados de Chillán | -36.863, -71.377 | -36.86483, -71.38068 | 25 | 5 | 2415 | 496 / 952 / 967 | 2026-01-29 02:35 | 2026-09-07 02:30 |
| Llaima | -38.692, -71.729 | -38.69215, -71.73063 | 25 | 5 | 2475 | 497 / 988 / 990 | 2026-01-29 02:35 | 2026-09-07 02:30 |
| Chaitén | -42.8344815, -72.6528875 | -42.83496, -72.65005 | 25 | 5 | 2650 | 562 / 1040 / 1048 | 2026-01-29 02:35 | 2026-09-06 07:30 |
| Planchón-Peteroa | -35.241099, -70.573345 | -35.2232, -70.5695 | 25 | 3 | 2324 | 489 / 913 / 922 | 2026-01-29 02:35 | 2026-09-07 02:30 |
| Lastarria | -25.168, -68.507 | -25.16837, -68.50807 | 25 | 3 | 2059 | 415 / 815 / 829 | 2026-01-29 05:12 | 2026-09-07 00:55 |
| Isluga | -19.15, -68.83 | -19.15212, -68.83269 | 25 | 5 | 1982 | 408 / 785 / 789 | 2026-01-29 01:05 | 2026-09-07 01:00 |
| Tupungatito | -33.389044, -69.826374 | -33.42694, -69.80039 | 25 | 7 | 2294 | 468 / 910 / 916 | 2026-01-29 02:35 | 2026-09-07 00:55 |

## Table 3 — MIR radiative power coefficients (Wooster) and OSF v2.5 validation

Validation source: experiments/21_results.json (S14, OSF v2.5, n_rows_total=48360).

| Sensor | k in code | matched formula (OSF v2.5) | k matched | n rows | median error (%) | A_pix mode |
|---|---|---|---|---|---|---|
| MODIS_1000m | {'WOOSTER_COEFF': 18.9} | Coppola2016_Wooster_k18.9_Apix1e6 | 18900000 | 13157 | 1.97e-14 | nadir_fijo |
| VIIRS_750m | {'WOOSTER_COEFF': 19.7} | DiBella2024_k1.11e7 | 11100000 | 2515 | 0.169 | nadir_fijo |
| VIIRS_375m | {'WOOSTER_COEFF': 18.0} | Laiolo2024_k18.0_Apix140625 | 2531250 | 32688 | 1.84e-14 | nadir_fijo |

## Table 4 — Validation against MIROVA NRT per volcano and sensor

Recall = MIROVA alert nights recovered by a dashboard-valid record (same volcano, sensor bucket, UTC date). Ratio = median ours/MIROVA over pass-level pairs (|Δt| ≤ 20 min). «no alert» nights are NOT false positives (A54).

| Volcano | Sensor | n records | MIROVA alert nights | recall (dashboard) | recall (crater) | dashboard nights w/o alert | pairs | ratio median [IQR] |
|---|---|---|---|---|---|---|---|---|
| PuyehueCordonCaulle | MODIS | 530 | 0 | None | None | 202/202 | 0 | — |
| PuyehueCordonCaulle | VIIRS750 | 1014 | 38 | 0.789 | 0.789 | 181/211 | 38 | 0.691 [0.365–1.029] |
| PuyehueCordonCaulle | VIIRS375 | 1022 | 120 | 0.867 | 0.867 | 98/202 | 258 | 1.029 [0.742–1.498] |
| Villarrica | MODIS | 561 | 1 | 0.0 | 1.0 | 44/44 | 0 | — |
| Villarrica | VIIRS750 | 1121 | 6 | 0.833 | 0.833 | 146/151 | 4 | 0.994 [0.769–1.127] |
| Villarrica | VIIRS375 | 1124 | 32 | 1.0 | 1.0 | 203/235 | 38 | 0.945 [0.8–1.225] |
| Lascar | MODIS | 422 | 77 | 0.117 | 0.974 | 5/14 | 9 | 0.799 [0.538–0.965] |
| Lascar | VIIRS750 | 810 | 134 | 0.903 | 0.903 | 49/170 | 178 | 0.533 [0.344–0.753] |
| Lascar | VIIRS375 | 817 | 174 | 0.937 | 0.937 | 30/193 | 316 | 0.53 [0.37–0.684] |
| Copahue | MODIS | 496 | 0 | None | None | 10/10 | 0 | — |
| Copahue | VIIRS750 | 952 | 1 | 1.0 | 1.0 | 95/96 | 2 | 1.302 [1.288–1.317] |
| Copahue | VIIRS375 | 960 | 4 | 1.0 | 1.0 | 210/214 | 7 | 0.912 [0.488–1.29] |
| NevadosDeChillan | MODIS | 496 | 1 | 0.0 | 1.0 | 22/22 | 0 | — |
| NevadosDeChillan | VIIRS750 | 952 | 1 | 1.0 | 1.0 | 57/58 | 0 | — |
| NevadosDeChillan | VIIRS375 | 967 | 11 | 0.455 | 0.455 | 96/101 | 8 | 1.162 [1.111–1.261] |
| Llaima | MODIS | 497 | 0 | None | None | 22/22 | 0 | — |
| Llaima | VIIRS750 | 988 | 0 | None | None | 94/94 | 0 | — |
| Llaima | VIIRS375 | 990 | 2 | 1.0 | 1.0 | 204/206 | 5 | 0.431 [0.182–0.541] |
| Chaiten | MODIS | 562 | 3 | 0.333 | 1.0 | 55/56 | 0 | — |
| Chaiten | VIIRS750 | 1040 | 2 | 0.5 | 0.5 | 154/155 | 1 | 1.15 [1.15–1.15] |
| Chaiten | VIIRS375 | 1048 | 38 | 0.895 | 0.895 | 169/203 | 62 | 1.312 [1.024–1.695] |
| PlanchonPeteroa | MODIS | 489 | 0 | None | None | 27/27 | 0 | — |
| PlanchonPeteroa | VIIRS750 | 913 | 9 | 0.444 | 0.444 | 111/115 | 2 | 6.783 [3.925–9.642] |
| PlanchonPeteroa | VIIRS375 | 922 | 92 | 0.946 | 0.946 | 106/193 | 171 | 0.895 [0.657–1.186] |
| Lastarria | MODIS | 415 | 0 | None | None | 18/18 | 0 | — |
| Lastarria | VIIRS750 | 815 | 0 | None | None | 122/122 | 0 | — |
| Lastarria | VIIRS375 | 829 | 154 | 0.909 | 0.909 | 49/189 | 218 | 0.569 [0.308–1.032] |
| Isluga | MODIS | 408 | 0 | None | None | 15/15 | 0 | — |
| Isluga | VIIRS750 | 785 | 40 | 0.7 | 0.7 | 117/145 | 27 | 1.003 [0.442–3.231] |
| Isluga | VIIRS375 | 789 | 156 | 0.987 | 0.987 | 64/218 | 310 | 0.58 [0.361–0.791] |
| Tupungatito | MODIS | 468 | 0 | None | None | 23/23 | 0 | — |
| Tupungatito | VIIRS750 | 910 | 15 | 0.467 | 0.467 | 107/114 | 3 | 0.09 [0.072–1.306] |
| Tupungatito | VIIRS375 | 916 | 107 | 0.972 | 0.972 | 89/193 | 209 | 0.645 [0.398–0.864] |

### Aggregate by sensor

| Sensor | MIROVA alert nights | recall (dashboard) | recall (crater) | volcanoes with ratio | in band [0.5, 2.0] |
|---|---|---|---|---|---|
| MODIS | 82 | 0.122 | 0.976 | 1 | 1 |
| VIIRS750 | 246 | 0.805 | 0.805 | 8 | 6 |
| VIIRS375 | 890 | 0.931 | 0.931 | 11 | 10 |
