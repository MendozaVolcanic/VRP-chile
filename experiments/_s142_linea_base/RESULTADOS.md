# S142: linea base de sobre-publicacion, regimen posterior a #535

Generado por `experiments/_s142_linea_base/linea_base_post535.py` desde `linea_base_post535.json` (regla S91: ningun numero de este archivo se escribio a mano).

## El fenomeno

Hasta el PR #535 la mascara de nube de 260 K trataba la nieve fria de invierno como nube. En esas pasadas el primer pase quedaba sin pixeles de fondo y el record no podia publicar, hubiera o no calor. Eso no era precision: era ceguera, y bajaba la tasa de publicacion en pasadas donde MIROVA miro y no vio nada. Al apagar la mascara las pasadas vuelven a tener fondo y el dashboard publica en ellas como en el resto. La linea base de S139 (63,5 %) y la del auto-audit mezclan ambos regimenes, asi que subestiman lo que produccion hace hoy.

## Procedencia

- Checkout `3ee3d15be`, igual a origin/main: True.
- Referencia `registro_vrp_consolidado.csv`: sha `336d7c5cf`, commit 2026-09-18T05:35:58Z (remoto Mirova-v1).
- Referencia `registro_vrp_ocr.csv`: sha `f9805ad39`, commit 2026-09-17T11:32:09Z (remoto Mirova-v1).
- Ultima fila de referencia por sensor: {'MODIS': '2026-09-18', 'VIIRS375': '2026-09-17', 'VIIRS750': '2026-09-17'}. Ultimo dato nuestro: noche 2026-09-17.
- Predicado: `frontend/index.html` sha `24fba8a15`. Estratos: `scripts/build_c2ab_windows.py:41-42` (focal Lascar, Lastarria, Isluga, PlanchonPeteroa, PuyehueCordonCaulle; nevado Llaima, Copahue, Villarrica, NevadosDeChillan, Tupungatito, Chaiten).
- Tramos por noche UTC; `pasadas_con_tramo_discordante` contra la hora exacta de los merges: antes_535_misma_longitud 0, entre_535_y_571 0, despues_571 0, contexto_marzo_a_535 0.

## 1. Tabla principal: publicacion en negativos limpios por sensor y tramo

Cada celda: tasa, de n. Pasada = variante principal del banco; estricta = sin ALERTA ni FP en la noche del volcan; noche = noche de volcan.

| Sensor | Tramo | Noches UTC | Pasada | Pasada estricta | Noche de volcan | Recall pasada | Recall noche | sin_info |
|---|---|---|---|---|---|---|---|---|
| MODIS | antes_535_misma_longitud | 2026-08-12 a 2026-08-28 (17) | 11,1 % de 388 | 10,4 % de 240 | 17,7 % de 186 | 0,0 % de 1 (n<20) | 0,0 % de 1 (n<20) | 26 |
| MODIS | entre_535_y_571 | 2026-08-29 a 2026-08-31 (3) | 4,5 % de 67 | 7,1 % de 42 | 9,1 % de 33 | s/d de 0 | s/d de 0 | 1 |
| MODIS | despues_571 | 2026-09-01 a 2026-09-17 (17) | 11,2 % de 385 | 9,5 % de 211 | 16,1 % de 186 | 100,0 % de 1 (n<20) | 100,0 % de 1 (n<20) | 13 |
| MODIS | contexto_marzo_a_535 | 2026-03-01 a 2026-08-28 (181) | 11,5 % de 4009 | 10,8 % de 2383 | 18,6 % de 1910 | 10,5 % de 76 | 12,3 % de 65 | 250 |
| VIIRS375 | antes_535_misma_longitud | 2026-08-12 a 2026-08-28 (17) | 62,6 % de 358 | 63,2 % de 353 | 80,7 % de 114 | 89,7 % de 87 | 95,9 % de 49 | 338 |
| VIIRS375 | entre_535_y_571 | 2026-08-29 a 2026-08-31 (3) | 84,4 % de 64 | 84,4 % de 64 | 100,0 % de 20 | 100,0 % de 11 (n<20) | 100,0 % de 7 (n<20) | 54 |
| VIIRS375 | despues_571 | 2026-09-01 a 2026-09-17 (17) | 86,5 % de 325 | 86,5 % de 318 | 100,0 % de 102 | 100,0 % de 129 | 100,0 % de 68 | 332 |
| VIIRS375 | contexto_marzo_a_535 | 2026-03-01 a 2026-08-28 (181) | 60,7 % de 2675 | 60,8 % de 2651 | 79,8 % de 1104 | 96,0 % de 1200 | 98,1 % de 720 | 4217 |
| VIIRS750 | antes_535_misma_longitud | 2026-08-12 a 2026-08-28 (17) | 22,6 % de 530 | 23,6 % de 365 | 54,8 % de 168 | 79,0 % de 19 (n<20) | 83,3 % de 18 (n<20) | 266 |
| VIIRS750 | entre_535_y_571 | 2026-08-29 a 2026-08-31 (3) | 27,6 % de 87 | 18,6 % de 59 | 64,5 % de 31 | 100,0 % de 2 (n<20) | 100,0 % de 2 (n<20) | 46 |
| VIIRS750 | despues_571 | 2026-09-01 a 2026-09-17 (17) | 21,0 % de 562 | 18,8 % de 329 | 47,7 % de 174 | 68,8 % de 16 (n<20) | 91,7 % de 12 (n<20) | 230 |
| VIIRS750 | contexto_marzo_a_535 | 2026-03-01 a 2026-08-28 (181) | 22,3 % de 4367 | 20,6 % de 2763 | 55,9 % de 1772 | 82,9 % de 251 | 86,2 % de 203 | 3657 |
| CUALQUIERA | antes_535_misma_longitud | 2026-08-12 a 2026-08-28 (17) | 30,3 % de 1276 | 34,9 % de 958 | 88,4 % de 112 | 86,9 % de 107 | 100,0 % de 51 | 630 |
| CUALQUIERA | entre_535_y_571 | 2026-08-29 a 2026-08-31 (3) | 37,2 % de 218 | 41,2 % de 165 | 100,0 % de 20 | 100,0 % de 13 (n<20) | 100,0 % de 7 (n<20) | 101 |
| CUALQUIERA | despues_571 | 2026-09-01 a 2026-09-17 (17) | 34,8 % de 1272 | 41,6 % de 858 | 100,0 % de 99 | 96,6 % de 146 | 100,0 % de 71 | 575 |
| CUALQUIERA | contexto_marzo_a_535 | 2026-03-01 a 2026-08-28 (181) | 27,7 % de 11051 | 31,3 % de 7797 | 89,7 % de 1099 | 89,6 % de 1527 | 99,6 % de 737 | 8124 |

## 2. Estrato focal y nevado (banda de terminado: focal 10 %, nevado 15 %)

| Estrato | Sensor | Tramo | Pasada | Estricta | Noche de volcan | Recall noche |
|---|---|---|---|---|---|---|
| focal | MODIS | antes_535_misma_longitud | 18,3 % de 164 | 19,1 % de 84 | 25,0 % de 84 | 0,0 % de 1 (n<20) |
| focal | MODIS | entre_535_y_571 | 6,9 % de 29 | 16,7 % de 12 (n<20) | 13,3 % de 15 (n<20) | s/d de 0 |
| focal | MODIS | despues_571 | 18,7 % de 171 | 21,4 % de 56 | 22,4 % de 85 | s/d de 0 |
| focal | MODIS | contexto_marzo_a_535 | 19,9 % de 1630 | 29,6 % de 523 | 26,8 % de 829 | 12,3 % de 65 |
| focal | VIIRS375 | antes_535_misma_longitud | 54,8 % de 126 | 56,2 % de 121 | 67,4 % de 43 | 96,7 % de 30 |
| focal | VIIRS375 | entre_535_y_571 | 94,4 % de 18 (n<20) | 94,4 % de 18 (n<20) | 100,0 % de 6 (n<20) | 100,0 % de 7 (n<20) |
| focal | VIIRS375 | despues_571 | 85,6 % de 90 | 84,7 % de 85 | 100,0 % de 29 | 100,0 % de 45 |
| focal | VIIRS375 | contexto_marzo_a_535 | 54,2 % de 607 | 54,6 % de 597 | 72,0 % de 257 | 98,6 % de 556 |
| focal | VIIRS750 | antes_535_misma_longitud | 24,0 % de 217 | 30,2 % de 126 | 50,7 % de 73 | 90,9 % de 11 (n<20) |
| focal | VIIRS750 | entre_535_y_571 | 40,0 % de 35 | 29,4 % de 17 (n<20) | 46,2 % de 13 (n<20) | 100,0 % de 2 (n<20) |
| focal | VIIRS750 | despues_571 | 26,3 % de 228 | 21,2 % de 85 | 53,4 % de 73 | 100,0 % de 11 (n<20) |
| focal | VIIRS750 | contexto_marzo_a_535 | 30,1 % de 1666 | 32,5 % de 618 | 65,5 % de 715 | 89,0 % de 182 |
| nevado | MODIS | antes_535_misma_longitud | 5,8 % de 224 | 5,8 % de 156 | 11,8 % de 102 | s/d de 0 |
| nevado | MODIS | entre_535_y_571 | 2,6 % de 38 | 3,3 % de 30 | 5,6 % de 18 (n<20) | s/d de 0 |
| nevado | MODIS | despues_571 | 5,1 % de 214 | 5,2 % de 155 | 10,9 % de 101 | 100,0 % de 1 (n<20) |
| nevado | MODIS | contexto_marzo_a_535 | 5,7 % de 2379 | 5,5 % de 1860 | 12,4 % de 1081 | s/d de 0 |
| nevado | VIIRS375 | antes_535_misma_longitud | 66,8 % de 232 | 66,8 % de 232 | 88,7 % de 71 | 94,7 % de 19 (n<20) |
| nevado | VIIRS375 | entre_535_y_571 | 80,4 % de 46 | 80,4 % de 46 | 100,0 % de 14 (n<20) | s/d de 0 |
| nevado | VIIRS375 | despues_571 | 86,8 % de 235 | 87,1 % de 233 | 100,0 % de 73 | 100,0 % de 23 |
| nevado | VIIRS375 | contexto_marzo_a_535 | 62,6 % de 2068 | 62,6 % de 2054 | 82,2 % de 847 | 96,3 % de 164 |
| nevado | VIIRS750 | antes_535_misma_longitud | 21,7 % de 313 | 20,1 % de 239 | 57,9 % de 95 | 71,4 % de 7 (n<20) |
| nevado | VIIRS750 | entre_535_y_571 | 19,2 % de 52 | 14,3 % de 42 | 77,8 % de 18 (n<20) | s/d de 0 |
| nevado | VIIRS750 | despues_571 | 17,4 % de 334 | 18,0 % de 244 | 43,6 % de 101 | 0,0 % de 1 (n<20) |
| nevado | VIIRS750 | contexto_marzo_a_535 | 17,5 % de 2701 | 17,1 % de 2145 | 49,5 % de 1057 | 61,9 % de 21 |

## 3. Por volcan (tramo despues_571 contra antes_535_misma_longitud)

### MODIS

| Volcan | Estrato | Pasada antes | Pasada despues | Noche antes | Noche despues | Recall noche despues |
|---|---|---|---|---|---|---|
| Lascar | focal | 3,3 % de 30 | 3,1 % de 32 | 6,2 % de 16 (n<20) | 5,9 % de 17 (n<20) | s/d de 0 |
| Lastarria | focal | 3,2 % de 31 | 3,2 % de 31 | 5,9 % de 17 (n<20) | 5,9 % de 17 (n<20) | s/d de 0 |
| Isluga | focal | 3,2 % de 31 | 0,0 % de 29 | 5,9 % de 17 (n<20) | 0,0 % de 17 (n<20) | s/d de 0 |
| Tupungatito | nevado | 2,9 % de 35 | 5,7 % de 35 | 5,9 % de 17 (n<20) | 11,8 % de 17 (n<20) | s/d de 0 |
| PlanchonPeteroa | focal | 10,5 % de 38 | 2,6 % de 39 | 17,6 % de 17 (n<20) | 5,9 % de 17 (n<20) | s/d de 0 |
| NevadosDeChillan | nevado | 5,3 % de 38 | 2,8 % de 36 | 11,8 % de 17 (n<20) | 5,9 % de 17 (n<20) | s/d de 0 |
| Llaima | nevado | 2,6 % de 38 | 0,0 % de 35 | 5,9 % de 17 (n<20) | 0,0 % de 17 (n<20) | s/d de 0 |
| Villarrica | nevado | 5,6 % de 36 | 15,2 % de 33 | 11,8 % de 17 (n<20) | 31,2 % de 16 (n<20) | 100,0 % de 1 (n<20) |
| Copahue | nevado | 2,6 % de 39 | 2,9 % de 35 | 5,9 % de 17 (n<20) | 5,9 % de 17 (n<20) | s/d de 0 |
| PuyehueCordonCaulle | focal | 67,7 % de 34 | 72,5 % de 40 | 88,2 % de 17 (n<20) | 94,1 % de 17 (n<20) | s/d de 0 |
| Chaiten | nevado | 15,8 % de 38 | 5,0 % de 40 | 29,4 % de 17 (n<20) | 11,8 % de 17 (n<20) | s/d de 0 |

### VIIRS375

| Volcan | Estrato | Pasada antes | Pasada despues | Noche antes | Noche despues | Recall noche despues |
|---|---|---|---|---|---|---|
| Lascar | focal | 14,3 % de 21 | 89,5 % de 19 (n<20) | 37,5 % de 8 (n<20) | 100,0 % de 6 (n<20) | 100,0 % de 9 (n<20) |
| Lastarria | focal | 18,8 % de 16 (n<20) | 83,3 % de 18 (n<20) | 16,7 % de 6 (n<20) | 100,0 % de 6 (n<20) | 100,0 % de 7 (n<20) |
| Isluga | focal | 92,9 % de 14 (n<20) | 66,7 % de 6 (n<20) | 100,0 % de 5 (n<20) | 100,0 % de 2 (n<20) | 100,0 % de 14 (n<20) |
| Tupungatito | nevado | 30,8 % de 26 | 92,9 % de 14 (n<20) | 62,5 % de 8 (n<20) | 100,0 % de 5 (n<20) | 100,0 % de 10 (n<20) |
| PlanchonPeteroa | focal | 68,3 % de 41 | 82,8 % de 29 | 76,9 % de 13 (n<20) | 100,0 % de 9 (n<20) | 100,0 % de 5 (n<20) |
| NevadosDeChillan | nevado | 52,9 % de 34 | 93,3 % de 45 | 72,7 % de 11 (n<20) | 100,0 % de 14 (n<20) | 100,0 % de 3 (n<20) |
| Llaima | nevado | 67,4 % de 46 | 80,4 % de 51 | 92,9 % de 14 (n<20) | 100,0 % de 15 (n<20) | s/d de 0 |
| Villarrica | nevado | 65,7 % de 35 | 84,1 % de 44 | 100,0 % de 10 (n<20) | 100,0 % de 13 (n<20) | 100,0 % de 4 (n<20) |
| Copahue | nevado | 82,6 % de 46 | 86,0 % de 50 | 93,3 % de 15 (n<20) | 100,0 % de 16 (n<20) | s/d de 0 |
| PuyehueCordonCaulle | focal | 64,7 % de 34 | 94,4 % de 18 (n<20) | 90,9 % de 11 (n<20) | 100,0 % de 6 (n<20) | 100,0 % de 10 (n<20) |
| Chaiten | nevado | 82,2 % de 45 | 90,3 % de 31 | 100,0 % de 13 (n<20) | 100,0 % de 10 (n<20) | 100,0 % de 6 (n<20) |

### VIIRS750

| Volcan | Estrato | Pasada antes | Pasada despues | Noche antes | Noche despues | Recall noche despues |
|---|---|---|---|---|---|---|
| Lascar | focal | 10,0 % de 40 | 9,5 % de 42 | 28,6 % de 14 (n<20) | 35,7 % de 14 (n<20) | 100,0 % de 3 (n<20) |
| Lastarria | focal | 14,3 % de 49 | 5,9 % de 51 | 29,4 % de 17 (n<20) | 18,8 % de 16 (n<20) | s/d de 0 |
| Isluga | focal | 20,9 % de 43 | 42,5 % de 47 | 66,7 % de 15 (n<20) | 75,0 % de 16 (n<20) | 100,0 % de 1 (n<20) |
| Tupungatito | nevado | 31,4 % de 51 | 20,8 % de 53 | 75,0 % de 16 (n<20) | 64,7 % de 17 (n<20) | s/d de 0 |
| PlanchonPeteroa | focal | 15,6 % de 45 | 23,5 % de 51 | 40,0 % de 15 (n<20) | 50,0 % de 16 (n<20) | 100,0 % de 1 (n<20) |
| NevadosDeChillan | nevado | 9,4 % de 53 | 7,1 % de 56 | 17,6 % de 17 (n<20) | 17,6 % de 17 (n<20) | s/d de 0 |
| Llaima | nevado | 13,8 % de 58 | 20,3 % de 59 | 41,2 % de 17 (n<20) | 41,2 % de 17 (n<20) | s/d de 0 |
| Villarrica | nevado | 23,7 % de 38 | 18,9 % de 53 | 81,8 % de 11 (n<20) | 43,8 % de 16 (n<20) | 0,0 % de 1 (n<20) |
| Copahue | nevado | 24,1 % de 54 | 16,4 % de 55 | 58,8 % de 17 (n<20) | 41,2 % de 17 (n<20) | s/d de 0 |
| PuyehueCordonCaulle | focal | 62,5 % de 40 | 56,8 % de 37 | 100,0 % de 12 (n<20) | 100,0 % de 11 (n<20) | 100,0 % de 6 (n<20) |
| Chaiten | nevado | 28,8 % de 59 | 20,7 % de 58 | 82,3 % de 17 (n<20) | 52,9 % de 17 (n<20) | s/d de 0 |

## 4. Control del instrumento por tramo

| Tramo | identidad predicado | todo_publica da 1 | nada_publica da 0 | AUC oraculo 1 | barajado en [0,4; 0,6] | volcanes con AUC |
|---|---|---|---|---|---|---|
| antes_535_misma_longitud | True | True | True | True | True | 6 |
| entre_535_y_571 | True | True | True | True | None | 0 |
| despues_571 | True | True | True | True | True | 7 |
| contexto_marzo_a_535 | True | True | True | True | True | 9 |

AUC barajado y real (magnitud del display V375, por volcan) en despues_571: barajado {'Lascar': 0.494, 'Lastarria': 0.496, 'Isluga': 0.503, 'Tupungatito': 0.482, 'PlanchonPeteroa': 0.489, 'PuyehueCordonCaulle': 0.498, 'Chaiten': 0.504}; real {'Lascar': 0.751, 'Lastarria': 0.948, 'Isluga': 0.891, 'Tupungatito': 0.925, 'PlanchonPeteroa': 0.922, 'PuyehueCordonCaulle': 0.992, 'Chaiten': 0.915}.

## 5. Caveats medidos

- **antes_535_misma_longitud**: 2052 pasadas nocturnas; etiquetas {'neg_limpio': 1276, 'sin_info': 630, 'far_ref': 39, 'pos': 107}; celdas volcan-sensor con 0 < n_neg < 20: 35.
- **entre_535_y_571**: 340 pasadas nocturnas; etiquetas {'neg_limpio': 218, 'sin_info': 101, 'pos': 13, 'far_ref': 8}; celdas volcan-sensor con 0 < n_neg < 20: 64.
- **despues_571**: 2022 pasadas nocturnas; etiquetas {'neg_limpio': 1272, 'sin_info': 575, 'far_ref': 29, 'pos': 146}; celdas volcan-sensor con 0 < n_neg < 20: 38.
- **contexto_marzo_a_535**: 20992 pasadas nocturnas; etiquetas {'pos': 1527, 'sin_info': 8124, 'neg_limpio': 11051, 'far_ref': 290}; celdas volcan-sensor con 0 < n_neg < 20: 0.

Celdas chicas en despues_571: Chaiten|MODIS|noche, Chaiten|VIIRS375|noche, Chaiten|VIIRS750|noche, Copahue|MODIS|noche, Copahue|VIIRS375|noche, Copahue|VIIRS750|noche, Isluga|MODIS|noche, Isluga|VIIRS375|noche, Isluga|VIIRS375|pasada, Isluga|VIIRS750|noche, Lascar|MODIS|noche, Lascar|VIIRS375|noche, Lascar|VIIRS375|pasada, Lascar|VIIRS750|noche, Lastarria|MODIS|noche, Lastarria|VIIRS375|noche, Lastarria|VIIRS375|pasada, Lastarria|VIIRS750|noche, Llaima|MODIS|noche, Llaima|VIIRS375|noche, Llaima|VIIRS750|noche, NevadosDeChillan|MODIS|noche, NevadosDeChillan|VIIRS375|noche, NevadosDeChillan|VIIRS750|noche, PlanchonPeteroa|MODIS|noche, PlanchonPeteroa|VIIRS375|noche, PlanchonPeteroa|VIIRS750|noche, PuyehueCordonCaulle|MODIS|noche, PuyehueCordonCaulle|VIIRS375|noche, PuyehueCordonCaulle|VIIRS375|pasada, PuyehueCordonCaulle|VIIRS750|noche, Tupungatito|MODIS|noche, Tupungatito|VIIRS375|noche, Tupungatito|VIIRS375|pasada, Tupungatito|VIIRS750|noche, Villarrica|MODIS|noche, Villarrica|VIIRS375|noche, Villarrica|VIIRS750|noche.

## 6. Lectura

**Que muestra el corte.** En VIIRS 375 m el salto es de regimen, no de estacion: el tramo de 15 noches inmediatamente anterior a #535 (mismo invierno) publica en 62,6 % de 358 (IC 95 % Wilson 57,4 % a 67,4 %) de los negativos limpios por pasada; los tres dias entre merges ya estan en 84,4 % de 64 (IC 95 % Wilson 73,6 % a 91,3 %); y despues de #571 en 86,5 % de 325 (IC 95 % Wilson 82,3 % a 89,8 %). Que el tramo entre merges ya este alto con el piso VRP todavia puesto atribuye el salto a la mascara (#535), no al piso (#571), igual que `experiments/_s141_ndc/regimen_535.json`. Por noche de volcan el tramo nuevo publica en 100,0 % de 102 noches negativas: hoy toda noche en que MIROVA miro sin ver nada termina con algo publicado en el dashboard. El recall no se pago: 100,0 % de 68 noches positivas.

VIIRS 750 m y MODIS no muestran escalon: VIIRS 750 22,6 % antes y 21,0 % despues; MODIS 11,1 % y 11,2 %. SOSPECHA (no medido aca): la mascara de 260 K de #535 era la de VIIRS 375 (D14); este informe no verifico en codigo si alcanzaba a los otros sensores.

**Volcanes que se salen.** En VIIRS 375 los mayores saltos por pasada son focales de altura (Lascar 14,3 % a 89,5 %, Lastarria 18,8 % a 83,3 %) y Tupungatito (30,8 % a 92,9 %), pero los tres con n menor que 20 en al menos un tramo. En MODIS la tasa focal la sostiene Puyehue-Cordon Caulle (72,5 % de 40), el campo difuso del lacolito ya descrito en A20/A68; el resto de los focales MODIS esta bajo 5 %. En VIIRS 750 Puyehue-Cordon Caulle (56,8 %) e Isluga (42,5 %) encabezan.

**Linea base propuesta para la Fase 1 (tramo despues_571, noches 2026-09-01 a 2026-09-17).**

| Sensor | Estrato | Pasada | Noche de volcan | Banda de terminado |
|---|---|---|---|---|
| MODIS | focal | 18,7 % de 171 (IC 95 % Wilson 13,6 % a 25,2 %) | 22,4 % de 85 | 10,0 % |
| MODIS | nevado | 5,1 % de 214 (IC 95 % Wilson 2,9 % a 9,0 %) | 10,9 % de 101 | 15,0 % |
| VIIRS375 | focal | 85,6 % de 90 (IC 95 % Wilson 76,8 % a 91,4 %) | 100,0 % de 29 | 10,0 % |
| VIIRS375 | nevado | 86,8 % de 235 (IC 95 % Wilson 81,9 % a 90,5 %) | 100,0 % de 73 | 15,0 % |
| VIIRS750 | focal | 26,3 % de 228 (IC 95 % Wilson 21,0 % a 32,4 %) | 53,4 % de 73 | 10,0 % |
| VIIRS750 | nevado | 17,4 % de 334 (IC 95 % Wilson 13,7 % a 21,8 %) | 43,6 % de 101 | 15,0 % |

Reemplazo del 63,5 % (S139) y del valor del auto-audit (`data/audit_continuous/latest.json`, ventana movil de 60 dias): VIIRS 375 total 86,5 % de 325 (IC 95 % Wilson 82,3 % a 89,8 %); focal 85,6 % de 90 (IC 95 % Wilson 76,8 % a 91,4 %); nevado 86,8 % de 235 (IC 95 % Wilson 81,9 % a 90,5 %). Como referencia, el mismo instrumento sobre marzo a #535 da 60,7 % de 2675 (IC 95 % Wilson 58,8 % a 62,5 %), o sea la mezcla subestimaba la linea base de produccion en mas de 20 puntos.

**Recomendaciones.**

1. El auto-audit deberia fijar el inicio de su ventana de falsas publicaciones en 2026-09-01 hasta que la ventana de 60 dias quede entera dentro del regimen nuevo (a partir de fines de octubre). Con la ventana movil actual mezcla regimenes y el numero sube solo, semana a semana, sin que cambie el pipeline (A90).

2. La banda de terminado (10 % focal, 15 % nevado por pasada) sigue siendo defendible como destino, porque se ancla en el ~5 % de falsas que declara MIROVA (spec §2 y §7.2), no en la linea base. Lo que cambia es la distancia: hay que bajar unos 75 puntos en VIIRS 375, no 50. Y en noche de volcan la linea base es el techo, asi que todo A/B debe reportarse por pasada y por noche: un brazo que baje la tasa por pasada sin sacar ninguna noche de 100 % no cambia lo que el operador ve.

3. Con 15 noches por tramo la mayoria de las celdas volcan-sensor por noche tiene n < 20 (ver §5). La linea base solo es firme por sensor y por estrato. Un A/B de Fase 1 debe correr sobre al menos este mismo tramo (despues de #571) para ambos brazos y no compararse contra la mezcla de marzo.

**Caveats.** (a) Estacion: el tramo anterior es de la segunda quincena de agosto y el posterior de la primera de septiembre; ambos invierno, y el escalon ocurre dentro de los tres dias entre merges, lo que es dificil de explicar por estacion, pero un aporte estacional menor no esta descartado (SOSPECHA, no medido). (b) `sin_info`: en despues_571, 332 de 814 pasadas VIIRS 375 (40,8 %) no tienen fila CONS RUTINA con VRP 0 a +-2 min y quedan fuera del denominador; si MIROVA deja de listar pasadas de forma no aleatoria el negativo limpio podria sesgarse (SOSPECHA). (c) La referencia incluye filas del mismo dia de la corrida; las pasadas de la ultima noche que aun no tienen fila caen en `sin_info`, no en el denominador.
