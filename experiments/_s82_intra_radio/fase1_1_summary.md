# F-S81-A Fase 1.1 — Clasificación FPs MODIS

**Input**: fp_genuine_all.csv (2768 FPs totales, 857 MODIS)

**Records sin match en JSONs**: 0 (0.0%)


## Distribución por `path_bucket` (proxy del path que disparó)

| Path | N | % |
|---|---:|---:|
| eruption_scene | 831 | 97.0% |
| test1_integrated | 26 | 3.0% |

## Distribución por `cluster_bucket` (primary_cluster.n_pixels)

| Cluster size | N | % |
|---|---:|---:|
| 1px | 307 | 35.8% |
| 2-3px | 263 | 30.7% |
| 4-10px | 188 | 21.9% |
| 11-50px | 79 | 9.2% |
| 50+px | 20 | 2.3% |

## Distribución por `dist_bucket` (ours_dist_km)

| Distancia [km] | N | % |
|---|---:|---:|
| 0-2 | 26 | 3.0% |
| 10-20 | 305 | 35.6% |
| 2-5 | 16 | 1.9% |
| 20+ | 457 | 53.3% |
| 5-10 | 53 | 6.2% |

## Distribución por `vrp_bucket` (ours_vrp_mw)

| VRP [MW] | N | % |
|---|---:|---:|
| 100-1000 | 519 | 60.6% |
| 10-100 | 300 | 35.0% |
| 1-10 | 33 | 3.9% |
| 1000+ | 4 | 0.5% |
| <1 | 1 | 0.1% |

## Distribución por `ours_dist_class`

| Distance class | N | % |
|---|---:|---:|
| far | 765 | 89.3% |
| summit | 92 | 10.7% |

## Distribución por `path_combo` (Path A_BT / B_NTI / D_dNTIctx activos)

| Path combo | N | % |
|---|---:|---:|
| D_dNTIctx | 853 | 99.5% |
| B_NTI+D_dNTIctx | 2 | 0.2% |
| none | 2 | 0.2% |

## Cross-tab: path_combo × dist_bucket

| path_combo      |   0-2 |   10-20 |   2-5 |   20+ |   5-10 |
|:----------------|------:|--------:|------:|------:|-------:|
| B_NTI+D_dNTIctx |     0 |       2 |     0 |     0 |      0 |
| D_dNTIctx       |    26 |     303 |    16 |   455 |     53 |
| none            |     0 |       0 |     0 |     2 |      0 |

## Cross-tab: path_combo × cluster_bucket

| path_combo      |   11-50px |   1px |   2-3px |   4-10px |   50+px |
|:----------------|----------:|------:|--------:|---------:|--------:|
| B_NTI+D_dNTIctx |         0 |     1 |       1 |        0 |       0 |
| D_dNTIctx       |        79 |   304 |     262 |      188 |      20 |
| none            |         0 |     2 |       0 |        0 |       0 |

## Cross-tab: path_bucket × cluster_bucket

| path_bucket      |   11-50px |   1px |   2-3px |   4-10px |   50+px |
|:-----------------|----------:|------:|--------:|---------:|--------:|
| eruption_scene   |        66 |   306 |     262 |      177 |      20 |
| test1_integrated |        13 |     1 |       1 |       11 |       0 |

## Cross-tab: path_bucket × dist_bucket

| path_bucket      |   0-2 |   10-20 |   2-5 |   20+ |   5-10 |
|:-----------------|------:|--------:|------:|------:|-------:|
| eruption_scene   |     1 |     305 |    15 |   457 |     53 |
| test1_integrated |    25 |       0 |     1 |     0 |      0 |

## Cross-tab: cluster_bucket × dist_bucket

| cluster_bucket   |   0-2 |   10-20 |   2-5 |   20+ |   5-10 |
|:-----------------|------:|--------:|------:|------:|-------:|
| 11-50px          |    13 |      23 |     3 |    35 |      5 |
| 1px              |     0 |     102 |     4 |   185 |     16 |
| 2-3px            |     1 |     104 |     3 |   138 |     17 |
| 4-10px           |    12 |      67 |     6 |    91 |     12 |
| 50+px            |     0 |       9 |     0 |     8 |      3 |

## FPs por volcán (top 10)

| Volcán | N FPs |
|---|---:|
| PuyehueCordonCaulle | 98 |
| Chaiten | 96 |
| Tupungatito | 95 |
| PlanchonPeteroa | 89 |
| Villarrica | 87 |
| Llaima | 87 |
| Copahue | 78 |
| Lastarria | 72 |
| NevadosDeChillan | 68 |
| Isluga | 53 |

## Distribución `mirova` tag

| MIROVA tag | N | % |
|---|---:|---:|
| RUTINA | 840 | 98.0% |
| NO_RECORD | 17 | 2.0% |