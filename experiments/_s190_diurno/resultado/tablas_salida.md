### Regla sellada (decide)

Compuertas que fallan: ['I4b Isluga|MODIS|2026-07-22: pasadas diurnas de MIROVA y ningún record diurno del brazo']

Veredicto final por opción: {'enable_daytime_modis': 'INVÁLIDO POR INSTRUMENTO', 'enable_daytime_viirs': 'INVÁLIDO POR INSTRUMENTO'}

| sensor | protegidas recuperadas | alertas recuperadas | negativos publicados | base (caso) | sin Chillán | sin W7 | M5 pares, mediana | M8 ≥1 MW sin fila | veredicto del sensor |
|---|---|---|---|---|---|---|---|---|---|
| MODIS | 7 de 7 | 7 de 9 | 1 de 2223 | DECIDE NICOLÁS CON M4 (e-ii) | SIN CAMBIO | ADOPTAR | 7, 1.110 | 0 | DECIDE NICOLÁS CON M4 |
| VIIRS375 | 23 de 42 | 31 de 53 | 8 de 2620 | ADOPTAR (b) | DECIDE NICOLÁS CON M4 | DECIDE NICOLÁS CON M4 | 31, 1.003 | 11 | DECIDE NICOLÁS CON M4 |
| VIIRS750 | 13 de 18 | 13 de 18 | 0 de 2910 | ADOPTAR (b) | NO ADOPTAR | ADOPTAR | 13, 1.000 | 5 | DECIDE NICOLÁS CON M4 |

### INFORMATIVO: dejando pasar el I4b de Isluga (no decide)

Compuertas que fallan: ninguna

Veredicto final por opción: {'enable_daytime_modis': 'DECIDE NICOLÁS CON M4', 'enable_daytime_viirs': 'DECIDE NICOLÁS CON M4'}

| sensor | protegidas recuperadas | alertas recuperadas | negativos publicados | base (caso) | sin Chillán | sin W7 | M5 pares, mediana | M8 ≥1 MW sin fila | veredicto del sensor |
|---|---|---|---|---|---|---|---|---|---|
| MODIS | 7 de 7 | 7 de 9 | 1 de 2223 | DECIDE NICOLÁS CON M4 (e-ii) | SIN CAMBIO | ADOPTAR | 7, 1.110 | 0 | DECIDE NICOLÁS CON M4 |
| VIIRS375 | 23 de 42 | 31 de 53 | 8 de 2620 | ADOPTAR (b) | DECIDE NICOLÁS CON M4 | DECIDE NICOLÁS CON M4 | 31, 1.003 | 11 | DECIDE NICOLÁS CON M4 |
| VIIRS750 | 13 de 18 | 13 de 18 | 0 de 2910 | ADOPTAR (b) | NO ADOPTAR | ADOPTAR | 13, 1.000 | 5 | DECIDE NICOLÁS CON M4 |

- MODIS, M8 (publicaciones diurnas de 1 MW o más en pasadas sin fila de MIROVA): []
- MODIS, protegidas no publicadas: []
- MODIS, por ventana: {'W2': {'P': 0, 'P_obs': 0, 'amb': 0, 'amb_obs': 1, 'neg_pub': 0, 'neg_obs': 377}, 'W3': {'P': 0, 'P_obs': 0, 'amb': 0, 'amb_obs': 0, 'neg_pub': 0, 'neg_obs': 252}, 'W4': {'P': 0, 'P_obs': 0, 'amb': 0, 'amb_obs': 1, 'neg_pub': 0, 'neg_obs': 416}, 'W5': {'P': 0, 'P_obs': 0, 'amb': 0, 'amb_obs': 0, 'neg_pub': 0, 'neg_obs': 447}, 'W6': {'P': 1, 'P_obs': 1, 'amb': 0, 'amb_obs': 0, 'neg_pub': 0, 'neg_obs': 308}, 'W7': {'P': 6, 'P_obs': 6, 'amb': 0, 'amb_obs': 0, 'neg_pub': 1, 'neg_obs': 423}}
- VIIRS375, M8 (publicaciones diurnas de 1 MW o más en pasadas sin fila de MIROVA): ['Tupungatito|VIIRS375|2026-08-30 18:42|1.653 MW', 'Villarrica|VIIRS375|2026-08-19 18:48|2.940 MW', 'Villarrica|VIIRS375|2026-08-23 18:54|2.501 MW', 'Lascar|VIIRS375|2026-09-19 18:12|2.122 MW', 'Lastarria|VIIRS375|2026-10-12 17:42|6.218 MW', 'NevadosDeChillan|VIIRS375|2026-10-01 17:42|2.663 MW', 'NevadosDeChillan|VIIRS375|2026-10-01 18:18|7.299 MW', 'NevadosDeChillan|VIIRS375|2026-10-16 18:06|12.289 MW', 'NevadosDeChillan|VIIRS375|2026-10-17 18:24|7.459 MW', 'NevadosDeChillan|VIIRS375|2026-10-27 17:54|12.751 MW', 'NevadosDeChillan|VIIRS375|2026-10-27 18:54|4.394 MW']
- VIIRS375, protegidas no publicadas: ['Chaiten|VIIRS375|2026-09-11 18:12:01', 'Isluga|VIIRS375|2026-07-25 17:24:02', 'Isluga|VIIRS375|2026-08-31 17:30:02', 'Isluga|VIIRS375|2026-09-14 18:42:00', 'Lascar|VIIRS375|2026-06-15 17:24:01', 'Lascar|VIIRS375|2026-06-24 17:36:00', 'Lascar|VIIRS375|2026-06-24 18:00:01', 'Lascar|VIIRS375|2026-06-28 17:30:02', 'Lascar|VIIRS375|2026-06-28 18:24:01', 'Lascar|VIIRS375|2026-08-27 17:42:00', 'Lascar|VIIRS375|2026-09-19 17:30:01', 'Lastarria|VIIRS375|2026-06-15 17:24:01', 'Lastarria|VIIRS375|2026-06-28 17:30:02', 'Lastarria|VIIRS375|2026-06-28 18:06:00', 'Lastarria|VIIRS375|2026-06-28 18:24:01', 'Lastarria|VIIRS375|2026-06-29 17:42:00', 'Lastarria|VIIRS375|2026-06-30 17:24:00', 'Villarrica|VIIRS375|2026-08-17 19:06:00', 'Villarrica|VIIRS375|2026-08-21 18:54:02']
- VIIRS375, por ventana: {'W2': {'P': 0, 'P_obs': 11, 'amb': 0, 'amb_obs': 1, 'neg_pub': 3, 'neg_obs': 473}, 'W3': {'P': 0, 'P_obs': 1, 'amb': 2, 'amb_obs': 2, 'neg_pub': 2, 'neg_obs': 379}, 'W4': {'P': 1, 'P_obs': 5, 'amb': 2, 'amb_obs': 4, 'neg_pub': 0, 'neg_obs': 476}, 'W5': {'P': 1, 'P_obs': 4, 'amb': 2, 'amb_obs': 2, 'neg_pub': 2, 'neg_obs': 509}, 'W6': {'P': 5, 'P_obs': 5, 'amb': 1, 'amb_obs': 1, 'neg_pub': 1, 'neg_obs': 352}, 'W7': {'P': 16, 'P_obs': 16, 'amb': 1, 'amb_obs': 1, 'neg_pub': 0, 'neg_obs': 431}}
- VIIRS750, M8 (publicaciones diurnas de 1 MW o más en pasadas sin fila de MIROVA): ['NevadosDeChillan|VIIRS750|2026-10-01 18:18|2.866 MW', 'NevadosDeChillan|VIIRS750|2026-10-17 18:24|12.085 MW', 'NevadosDeChillan|VIIRS750|2026-10-27 17:54|6.166 MW', 'NevadosDeChillan|VIIRS750|2026-10-27 18:54|12.529 MW', 'PuyehueCordonCaulle|VIIRS750|2026-10-21 18:48|2.358 MW']
- VIIRS750, protegidas no publicadas: ['Isluga|VIIRS750|2026-06-21 18:36:00', 'Isluga|VIIRS750|2026-09-04 18:30:00', 'NevadosDeChillan|VIIRS750|2026-10-24 18:12:01', 'PlanchonPeteroa|VIIRS750|2026-08-14 17:42:02', 'Tupungatito|VIIRS750|2026-08-20 17:30:02']
- VIIRS750, por ventana: {'W2': {'P': 0, 'P_obs': 1, 'amb': 0, 'amb_obs': 0, 'neg_pub': 0, 'neg_obs': 608}, 'W3': {'P': 0, 'P_obs': 0, 'amb': 0, 'amb_obs': 0, 'neg_pub': 0, 'neg_obs': 405}, 'W4': {'P': 0, 'P_obs': 2, 'amb': 0, 'amb_obs': 0, 'neg_pub': 0, 'neg_obs': 509}, 'W5': {'P': 0, 'P_obs': 1, 'amb': 0, 'amb_obs': 0, 'neg_pub': 0, 'neg_obs': 529}, 'W6': {'P': 2, 'P_obs': 2, 'amb': 0, 'amb_obs': 0, 'neg_pub': 0, 'neg_obs': 382}, 'W7': {'P': 11, 'P_obs': 12, 'amb': 0, 'amb_obs': 0, 'neg_pub': 0, 'neg_obs': 477}}

