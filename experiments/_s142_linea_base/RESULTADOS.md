# S142: linea base de sobre-publicacion, regimen posterior a #535

Generado por `experiments/_s142_linea_base/linea_base_post535.py` desde `linea_base_post535.json` (regla S91: ningun numero de este archivo se escribio a mano).

## El fenomeno

Hasta el PR #535 la mascara de nube de 260 K trataba la nieve fria de invierno como nube. En esas pasadas el primer pase quedaba sin pixeles de fondo y el record no podia publicar, hubiera o no calor. Eso no era precision: era ceguera, y bajaba la tasa de publicacion en pasadas donde MIROVA miro y no vio nada. Al apagar la mascara las pasadas vuelven a tener fondo y el dashboard publica en ellas como en el resto. La linea base de S139 (63,5 %) y la del auto-audit mezclan ambos regimenes, asi que subestiman lo que produccion hace hoy.

## Procedencia

- Checkout `a54ce6d32`, igual a origin/main: True.
- Referencia `registro_vrp_consolidado.csv`: sha `d944cd9cb`, commit 2026-09-15T12:51:01Z (remoto Mirova-v1).
- Referencia `registro_vrp_ocr.csv`: sha `2712d1743`, commit 2026-09-15T11:32:19Z (remoto Mirova-v1).
- Ultima fila de referencia por sensor: {'MODIS': '2026-09-15', 'VIIRS375': '2026-09-15', 'VIIRS750': '2026-09-15'}. Ultimo dato nuestro: noche 2026-09-15.
- Predicado: `frontend/index.html` sha `24fba8a15`. Estratos: `scripts/build_c2ab_windows.py:41-42` (focal Lascar, Lastarria, Isluga, PlanchonPeteroa, PuyehueCordonCaulle; nevado Llaima, Copahue, Villarrica, NevadosDeChillan, Tupungatito, Chaiten).
- Tramos por noche UTC; `pasadas_con_tramo_discordante` contra la hora exacta de los merges: antes_535_misma_longitud 0, entre_535_y_571 0, despues_571 0, contexto_marzo_a_535 0.

## 1. Tabla principal: publicacion en negativos limpios por sensor y tramo

Cada celda: tasa, de n. Pasada = variante principal del banco; estricta = sin ALERTA ni FP en la noche del volcan; noche = noche de volcan.

| Sensor | Tramo | Noches UTC | Pasada | Pasada estricta | Noche de volcan | Recall pasada | Recall noche | sin_info |
|---|---|---|---|---|---|---|---|---|
| MODIS | antes_535_misma_longitud | 2026-08-14 a 2026-08-28 (15) | 11,2 % de 331 | 11,2 % de 197 | 17,1 % de 164 | 0,0 % de 1 (n<20) | 0,0 % de 1 (n<20) | 26 |
| MODIS | entre_535_y_571 | 2026-08-29 a 2026-08-31 (3) | 4,5 % de 67 | 7,1 % de 42 | 9,1 % de 33 | s/d de 0 | s/d de 0 | 1 |
| MODIS | despues_571 | 2026-09-01 a 2026-09-15 (15) | 10,2 % de 325 | 8,0 % de 188 | 14,2 % de 162 | 100,0 % de 1 (n<20) | 100,0 % de 1 (n<20) | 13 |
| MODIS | contexto_marzo_a_535 | 2026-03-01 a 2026-08-28 (181) | 11,5 % de 4009 | 10,8 % de 2383 | 18,6 % de 1910 | 10,5 % de 76 | 12,3 % de 65 | 250 |
| VIIRS375 | antes_535_misma_longitud | 2026-08-14 a 2026-08-28 (15) | 62,1 % de 301 | 62,8 % de 296 | 80,4 % de 97 | 89,2 % de 83 | 95,7 % de 47 | 300 |
| VIIRS375 | entre_535_y_571 | 2026-08-29 a 2026-08-31 (3) | 84,4 % de 64 | 84,4 % de 64 | 100,0 % de 20 | 100,0 % de 11 (n<20) | 100,0 % de 7 (n<20) | 54 |
| VIIRS375 | despues_571 | 2026-09-01 a 2026-09-15 (15) | 87,1 % de 295 | 87,2 % de 290 | 100,0 % de 93 | 100,0 % de 104 | 100,0 % de 54 | 276 |
| VIIRS375 | contexto_marzo_a_535 | 2026-03-01 a 2026-08-28 (181) | 60,7 % de 2675 | 60,8 % de 2651 | 79,8 % de 1104 | 96,0 % de 1200 | 98,1 % de 720 | 4217 |
| VIIRS750 | antes_535_misma_longitud | 2026-08-14 a 2026-08-28 (15) | 23,1 % de 458 | 25,2 % de 306 | 55,1 % de 147 | 83,3 % de 18 (n<20) | 88,2 % de 17 (n<20) | 236 |
| VIIRS750 | entre_535_y_571 | 2026-08-29 a 2026-08-31 (3) | 27,6 % de 87 | 18,6 % de 59 | 64,5 % de 31 | 100,0 % de 2 (n<20) | 100,0 % de 2 (n<20) | 46 |
| VIIRS750 | despues_571 | 2026-09-01 a 2026-09-15 (15) | 21,2 % de 496 | 19,7 % de 300 | 48,0 % de 154 | 66,7 % de 12 (n<20) | 100,0 % de 9 (n<20) | 185 |
| VIIRS750 | contexto_marzo_a_535 | 2026-03-01 a 2026-08-28 (181) | 22,3 % de 4367 | 20,6 % de 2763 | 55,9 % de 1772 | 82,9 % de 251 | 86,2 % de 203 | 3657 |
| CUALQUIERA | antes_535_misma_longitud | 2026-08-14 a 2026-08-28 (15) | 30,3 % de 1090 | 35,7 % de 799 | 88,4 % de 95 | 87,2 % de 102 | 100,0 % de 48 | 562 |
| CUALQUIERA | entre_535_y_571 | 2026-08-29 a 2026-08-31 (3) | 37,2 % de 218 | 41,2 % de 165 | 100,0 % de 20 | 100,0 % de 13 (n<20) | 100,0 % de 7 (n<20) | 101 |
| CUALQUIERA | despues_571 | 2026-09-01 a 2026-09-15 (15) | 35,4 % de 1116 | 42,0 % de 778 | 100,0 % de 93 | 96,6 % de 117 | 100,0 % de 57 | 474 |
| CUALQUIERA | contexto_marzo_a_535 | 2026-03-01 a 2026-08-28 (181) | 27,7 % de 11051 | 31,3 % de 7797 | 89,7 % de 1099 | 89,6 % de 1527 | 99,6 % de 737 | 8124 |

## 2. Estrato focal y nevado (banda de terminado: focal 10 %, nevado 15 %)

| Estrato | Sensor | Tramo | Pasada | Estricta | Noche de volcan | Recall noche |
|---|---|---|---|---|---|---|
| focal | MODIS | antes_535_misma_longitud | 17,7 % de 141 | 20,6 % de 68 | 23,0 % de 74 | 0,0 % de 1 (n<20) |
| focal | MODIS | entre_535_y_571 | 6,9 % de 29 | 16,7 % de 12 (n<20) | 13,3 % de 15 (n<20) | s/d de 0 |
| focal | MODIS | despues_571 | 17,4 % de 144 | 17,3 % de 52 | 20,3 % de 74 | s/d de 0 |
| focal | MODIS | contexto_marzo_a_535 | 19,9 % de 1630 | 29,6 % de 523 | 26,8 % de 829 | 12,3 % de 65 |
| focal | VIIRS375 | antes_535_misma_longitud | 53,8 % de 104 | 55,6 % de 99 | 66,7 % de 36 | 96,5 % de 29 |
| focal | VIIRS375 | entre_535_y_571 | 94,4 % de 18 (n<20) | 94,4 % de 18 (n<20) | 100,0 % de 6 (n<20) | 100,0 % de 7 (n<20) |
| focal | VIIRS375 | despues_571 | 84,5 % de 84 | 84,0 % de 81 | 100,0 % de 27 | 100,0 % de 38 |
| focal | VIIRS375 | contexto_marzo_a_535 | 54,2 % de 607 | 54,6 % de 597 | 72,0 % de 257 | 98,6 % de 556 |
| focal | VIIRS750 | antes_535_misma_longitud | 21,2 % de 184 | 29,1 % de 103 | 47,6 % de 63 | 90,9 % de 11 (n<20) |
| focal | VIIRS750 | entre_535_y_571 | 40,0 % de 35 | 29,4 % de 17 (n<20) | 46,2 % de 13 (n<20) | 100,0 % de 2 (n<20) |
| focal | VIIRS750 | despues_571 | 25,1 % de 203 | 21,0 % de 81 | 52,3 % de 65 | 100,0 % de 9 (n<20) |
| focal | VIIRS750 | contexto_marzo_a_535 | 30,1 % de 1666 | 32,5 % de 618 | 65,5 % de 715 | 89,0 % de 182 |
| nevado | MODIS | antes_535_misma_longitud | 6,3 % de 190 | 6,2 % de 129 | 12,2 % de 90 | s/d de 0 |
| nevado | MODIS | entre_535_y_571 | 2,6 % de 38 | 3,3 % de 30 | 5,6 % de 18 (n<20) | s/d de 0 |
| nevado | MODIS | despues_571 | 4,4 % de 181 | 4,4 % de 136 | 9,1 % de 88 | 100,0 % de 1 (n<20) |
| nevado | MODIS | contexto_marzo_a_535 | 5,7 % de 2379 | 5,5 % de 1860 | 12,4 % de 1081 | s/d de 0 |
| nevado | VIIRS375 | antes_535_misma_longitud | 66,5 % de 197 | 66,5 % de 197 | 88,5 % de 61 | 94,4 % de 18 (n<20) |
| nevado | VIIRS375 | entre_535_y_571 | 80,4 % de 46 | 80,4 % de 46 | 100,0 % de 14 (n<20) | s/d de 0 |
| nevado | VIIRS375 | despues_571 | 88,1 % de 211 | 88,5 % de 209 | 100,0 % de 66 | 100,0 % de 16 (n<20) |
| nevado | VIIRS375 | contexto_marzo_a_535 | 62,6 % de 2068 | 62,6 % de 2054 | 82,2 % de 847 | 96,3 % de 164 |
| nevado | VIIRS750 | antes_535_misma_longitud | 24,4 % de 274 | 23,2 % de 203 | 60,7 % de 84 | 83,3 % de 6 (n<20) |
| nevado | VIIRS750 | entre_535_y_571 | 19,2 % de 52 | 14,3 % de 42 | 77,8 % de 18 (n<20) | s/d de 0 |
| nevado | VIIRS750 | despues_571 | 18,4 % de 293 | 19,2 % de 219 | 44,9 % de 89 | s/d de 0 |
| nevado | VIIRS750 | contexto_marzo_a_535 | 17,5 % de 2701 | 17,1 % de 2145 | 49,5 % de 1057 | 61,9 % de 21 |

## 3. Por volcan (tramo despues_571 contra antes_535_misma_longitud)

### MODIS

| Volcan | Estrato | Pasada antes | Pasada despues | Noche antes | Noche despues | Recall noche despues |
|---|---|---|---|---|---|---|
| Lascar | focal | 3,9 % de 26 | 0,0 % de 27 | 7,1 % de 14 (n<20) | 0,0 % de 15 (n<20) | s/d de 0 |
| Lastarria | focal | 0,0 % de 27 | 4,0 % de 25 | 0,0 % de 15 (n<20) | 7,1 % de 14 (n<20) | s/d de 0 |
| Isluga | focal | 3,7 % de 27 | 0,0 % de 25 | 6,7 % de 15 (n<20) | 0,0 % de 15 (n<20) | s/d de 0 |
| Tupungatito | nevado | 3,3 % de 30 | 6,7 % de 30 | 6,7 % de 15 (n<20) | 13,3 % de 15 (n<20) | s/d de 0 |
| PlanchonPeteroa | focal | 9,4 % de 32 | 0,0 % de 33 | 13,3 % de 15 (n<20) | 0,0 % de 15 (n<20) | s/d de 0 |
| NevadosDeChillan | nevado | 3,1 % de 32 | 3,3 % de 30 | 6,7 % de 15 (n<20) | 7,1 % de 14 (n<20) | s/d de 0 |
| Llaima | nevado | 3,1 % de 32 | 0,0 % de 30 | 6,7 % de 15 (n<20) | 0,0 % de 15 (n<20) | s/d de 0 |
| Villarrica | nevado | 6,7 % de 30 | 14,3 % de 28 | 13,3 % de 15 (n<20) | 28,6 % de 14 (n<20) | 100,0 % de 1 (n<20) |
| Copahue | nevado | 3,0 % de 33 | 0,0 % de 30 | 6,7 % de 15 (n<20) | 0,0 % de 15 (n<20) | s/d de 0 |
| PuyehueCordonCaulle | focal | 69,0 % de 29 | 70,6 % de 34 | 86,7 % de 15 (n<20) | 93,3 % de 15 (n<20) | s/d de 0 |
| Chaiten | nevado | 18,2 % de 33 | 3,0 % de 33 | 33,3 % de 15 (n<20) | 6,7 % de 15 (n<20) | s/d de 0 |

### VIIRS375

| Volcan | Estrato | Pasada antes | Pasada despues | Noche antes | Noche despues | Recall noche despues |
|---|---|---|---|---|---|---|
| Lascar | focal | 6,7 % de 15 (n<20) | 87,5 % de 16 (n<20) | 33,3 % de 6 (n<20) | 100,0 % de 5 (n<20) | 100,0 % de 8 (n<20) |
| Lastarria | focal | 23,1 % de 13 (n<20) | 81,2 % de 16 (n<20) | 20,0 % de 5 (n<20) | 100,0 % de 5 (n<20) | 100,0 % de 6 (n<20) |
| Isluga | focal | 100,0 % de 8 (n<20) | 66,7 % de 6 (n<20) | 100,0 % de 3 (n<20) | 100,0 % de 2 (n<20) | 100,0 % de 13 (n<20) |
| Tupungatito | nevado | 31,8 % de 22 | 92,9 % de 14 (n<20) | 57,1 % de 7 (n<20) | 100,0 % de 5 (n<20) | 100,0 % de 8 (n<20) |
| PlanchonPeteroa | focal | 68,4 % de 38 | 82,8 % de 29 | 75,0 % de 12 (n<20) | 100,0 % de 9 (n<20) | 100,0 % de 3 (n<20) |
| NevadosDeChillan | nevado | 53,6 % de 28 | 92,1 % de 38 | 77,8 % de 9 (n<20) | 100,0 % de 12 (n<20) | 100,0 % de 2 (n<20) |
| Llaima | nevado | 71,8 % de 39 | 86,4 % de 44 | 91,7 % de 12 (n<20) | 100,0 % de 13 (n<20) | s/d de 0 |
| Villarrica | nevado | 64,5 % de 31 | 84,1 % de 44 | 100,0 % de 9 (n<20) | 100,0 % de 13 (n<20) | 100,0 % de 1 (n<20) |
| Copahue | nevado | 79,5 % de 39 | 88,6 % de 44 | 92,3 % de 13 (n<20) | 100,0 % de 14 (n<20) | s/d de 0 |
| PuyehueCordonCaulle | focal | 60,0 % de 30 | 94,1 % de 17 (n<20) | 90,0 % de 10 (n<20) | 100,0 % de 6 (n<20) | 100,0 % de 8 (n<20) |
| Chaiten | nevado | 79,0 % de 38 | 88,9 % de 27 | 100,0 % de 11 (n<20) | 100,0 % de 9 (n<20) | 100,0 % de 5 (n<20) |

### VIIRS750

| Volcan | Estrato | Pasada antes | Pasada despues | Noche antes | Noche despues | Recall noche despues |
|---|---|---|---|---|---|---|
| Lascar | focal | 12,1 % de 33 | 11,1 % de 36 | 33,3 % de 12 (n<20) | 41,7 % de 12 (n<20) | 100,0 % de 3 (n<20) |
| Lastarria | focal | 9,5 % de 42 | 4,3 % de 46 | 20,0 % de 15 (n<20) | 14,3 % de 14 (n<20) | s/d de 0 |
| Isluga | focal | 16,2 % de 37 | 39,0 % de 41 | 69,2 % de 13 (n<20) | 71,4 % de 14 (n<20) | 100,0 % de 1 (n<20) |
| Tupungatito | nevado | 36,4 % de 44 | 21,3 % de 47 | 78,6 % de 14 (n<20) | 66,7 % de 15 (n<20) | s/d de 0 |
| PlanchonPeteroa | focal | 12,8 % de 39 | 20,4 % de 44 | 30,8 % de 13 (n<20) | 42,9 % de 14 (n<20) | 100,0 % de 1 (n<20) |
| NevadosDeChillan | nevado | 10,9 % de 46 | 8,5 % de 47 | 20,0 % de 15 (n<20) | 21,4 % de 14 (n<20) | s/d de 0 |
| Llaima | nevado | 15,7 % de 51 | 21,6 % de 51 | 46,7 % de 15 (n<20) | 46,7 % de 15 (n<20) | s/d de 0 |
| Villarrica | nevado | 25,7 % de 35 | 20,4 % de 49 | 80,0 % de 10 (n<20) | 46,7 % de 15 (n<20) | s/d de 0 |
| Copahue | nevado | 27,7 % de 47 | 18,4 % de 49 | 60,0 % de 15 (n<20) | 40,0 % de 15 (n<20) | s/d de 0 |
| PuyehueCordonCaulle | focal | 60,6 % de 33 | 55,6 % de 36 | 100,0 % de 10 (n<20) | 100,0 % de 11 (n<20) | 100,0 % de 4 (n<20) |
| Chaiten | nevado | 31,4 % de 51 | 20,0 % de 50 | 86,7 % de 15 (n<20) | 46,7 % de 15 (n<20) | s/d de 0 |

## 4. Control del instrumento por tramo

| Tramo | identidad predicado | todo_publica da 1 | nada_publica da 0 | AUC oraculo 1 | barajado en [0,4; 0,6] | volcanes con AUC |
|---|---|---|---|---|---|---|
| antes_535_misma_longitud | True | True | True | True | True | 6 |
| entre_535_y_571 | True | True | True | True | None | 0 |
| despues_571 | True | True | True | True | True | 7 |
| contexto_marzo_a_535 | True | True | True | True | True | 9 |

AUC barajado y real (magnitud del display V375, por volcan) en despues_571: barajado {'Lascar': 0.494, 'Lastarria': 0.501, 'Isluga': 0.473, 'Tupungatito': 0.506, 'PlanchonPeteroa': 0.522, 'PuyehueCordonCaulle': 0.496, 'Chaiten': 0.493}; real {'Lascar': 0.708, 'Lastarria': 0.949, 'Isluga': 0.881, 'Tupungatito': 0.91, 'PlanchonPeteroa': 0.917, 'PuyehueCordonCaulle': 0.99, 'Chaiten': 0.958}.

## 5. Caveats medidos

- **antes_535_misma_longitud**: 1788 pasadas nocturnas; etiquetas {'neg_limpio': 1090, 'sin_info': 562, 'far_ref': 34, 'pos': 102}; celdas volcan-sensor con 0 < n_neg < 20: 36.
- **entre_535_y_571**: 340 pasadas nocturnas; etiquetas {'neg_limpio': 218, 'sin_info': 101, 'pos': 13, 'far_ref': 8}; celdas volcan-sensor con 0 < n_neg < 20: 64.
- **despues_571**: 1730 pasadas nocturnas; etiquetas {'neg_limpio': 1116, 'sin_info': 474, 'far_ref': 23, 'pos': 117}; celdas volcan-sensor con 0 < n_neg < 20: 38.
- **contexto_marzo_a_535**: 20992 pasadas nocturnas; etiquetas {'pos': 1527, 'sin_info': 8124, 'neg_limpio': 11051, 'far_ref': 290}; celdas volcan-sensor con 0 < n_neg < 20: 0.

Celdas chicas en despues_571: Chaiten|MODIS|noche, Chaiten|VIIRS375|noche, Chaiten|VIIRS750|noche, Copahue|MODIS|noche, Copahue|VIIRS375|noche, Copahue|VIIRS750|noche, Isluga|MODIS|noche, Isluga|VIIRS375|noche, Isluga|VIIRS375|pasada, Isluga|VIIRS750|noche, Lascar|MODIS|noche, Lascar|VIIRS375|noche, Lascar|VIIRS375|pasada, Lascar|VIIRS750|noche, Lastarria|MODIS|noche, Lastarria|VIIRS375|noche, Lastarria|VIIRS375|pasada, Lastarria|VIIRS750|noche, Llaima|MODIS|noche, Llaima|VIIRS375|noche, Llaima|VIIRS750|noche, NevadosDeChillan|MODIS|noche, NevadosDeChillan|VIIRS375|noche, NevadosDeChillan|VIIRS750|noche, PlanchonPeteroa|MODIS|noche, PlanchonPeteroa|VIIRS375|noche, PlanchonPeteroa|VIIRS750|noche, PuyehueCordonCaulle|MODIS|noche, PuyehueCordonCaulle|VIIRS375|noche, PuyehueCordonCaulle|VIIRS375|pasada, PuyehueCordonCaulle|VIIRS750|noche, Tupungatito|MODIS|noche, Tupungatito|VIIRS375|noche, Tupungatito|VIIRS375|pasada, Tupungatito|VIIRS750|noche, Villarrica|MODIS|noche, Villarrica|VIIRS375|noche, Villarrica|VIIRS750|noche.

## 6. Lectura

**Que muestra el corte.** En VIIRS 375 m el salto es de regimen, no de estacion: el tramo de 15 noches inmediatamente anterior a #535 (mismo invierno) publica en 62,1 % de 301 (IC 95 % Wilson 56,5 % a 67,4 %) de los negativos limpios por pasada; los tres dias entre merges ya estan en 84,4 % de 64 (IC 95 % Wilson 73,6 % a 91,3 %); y despues de #571 en 87,1 % de 295 (IC 95 % Wilson 82,8 % a 90,5 %). Que el tramo entre merges ya este alto con el piso VRP todavia puesto atribuye el salto a la mascara (#535), no al piso (#571), igual que `experiments/_s141_ndc/regimen_535.json`. Por noche de volcan el tramo nuevo publica en 100,0 % de 93 noches negativas: hoy toda noche en que MIROVA miro sin ver nada termina con algo publicado en el dashboard. El recall no se pago: 100,0 % de 54 noches positivas.

VIIRS 750 m y MODIS no muestran escalon: VIIRS 750 23,1 % antes y 21,2 % despues; MODIS 11,2 % y 10,2 %. SOSPECHA (no medido aca): la mascara de 260 K de #535 era la de VIIRS 375 (D14); este informe no verifico en codigo si alcanzaba a los otros sensores.

**Volcanes que se salen.** En VIIRS 375 los mayores saltos por pasada son focales de altura (Lascar 6,7 % a 87,5 %, Lastarria 23,1 % a 81,2 %) y Tupungatito (31,8 % a 92,9 %), pero los tres con n menor que 20 en al menos un tramo. En MODIS la tasa focal la sostiene Puyehue-Cordon Caulle (70,6 % de 34), el campo difuso del lacolito ya descrito en A20/A68; el resto de los focales MODIS esta bajo 5 %. En VIIRS 750 Puyehue-Cordon Caulle (55,6 %) e Isluga (39,0 %) encabezan.

**Linea base propuesta para la Fase 1 (tramo despues_571, noches 2026-09-01 a 2026-09-15).**

| Sensor | Estrato | Pasada | Noche de volcan | Banda de terminado |
|---|---|---|---|---|
| MODIS | focal | 17,4 % de 144 (IC 95 % Wilson 12,0 % a 24,4 %) | 20,3 % de 74 | 10,0 % |
| MODIS | nevado | 4,4 % de 181 (IC 95 % Wilson 2,3 % a 8,5 %) | 9,1 % de 88 | 15,0 % |
| VIIRS375 | focal | 84,5 % de 84 (IC 95 % Wilson 75,3 % a 90,7 %) | 100,0 % de 27 | 10,0 % |
| VIIRS375 | nevado | 88,1 % de 211 (IC 95 % Wilson 83,1 % a 91,8 %) | 100,0 % de 66 | 15,0 % |
| VIIRS750 | focal | 25,1 % de 203 (IC 95 % Wilson 19,7 % a 31,5 %) | 52,3 % de 65 | 10,0 % |
| VIIRS750 | nevado | 18,4 % de 293 (IC 95 % Wilson 14,4 % a 23,3 %) | 44,9 % de 89 | 15,0 % |

Reemplazo del 63,5 % (S139) y del valor del auto-audit (`data/audit_continuous/latest.json`, ventana movil de 60 dias): VIIRS 375 total 87,1 % de 295 (IC 95 % Wilson 82,8 % a 90,5 %); focal 84,5 % de 84 (IC 95 % Wilson 75,3 % a 90,7 %); nevado 88,1 % de 211 (IC 95 % Wilson 83,1 % a 91,8 %). Como referencia, el mismo instrumento sobre marzo a #535 da 60,7 % de 2675 (IC 95 % Wilson 58,8 % a 62,5 %), o sea la mezcla subestimaba la linea base de produccion en mas de 20 puntos.

**Recomendaciones.**

1. El auto-audit deberia fijar el inicio de su ventana de falsas publicaciones en 2026-09-01 hasta que la ventana de 60 dias quede entera dentro del regimen nuevo (a partir de fines de octubre). Con la ventana movil actual mezcla regimenes y el numero sube solo, semana a semana, sin que cambie el pipeline (A90).

2. La banda de terminado (10 % focal, 15 % nevado por pasada) sigue siendo defendible como destino, porque se ancla en el ~5 % de falsas que declara MIROVA (spec §2 y §7.2), no en la linea base. Lo que cambia es la distancia: hay que bajar unos 75 puntos en VIIRS 375, no 50. Y en noche de volcan la linea base es el techo, asi que todo A/B debe reportarse por pasada y por noche: un brazo que baje la tasa por pasada sin sacar ninguna noche de 100 % no cambia lo que el operador ve.

3. Con 15 noches por tramo la mayoria de las celdas volcan-sensor por noche tiene n < 20 (ver §5). La linea base solo es firme por sensor y por estrato. Un A/B de Fase 1 debe correr sobre al menos este mismo tramo (despues de #571) para ambos brazos y no compararse contra la mezcla de marzo.

**Caveats.** (a) Estacion: el tramo anterior es de la segunda quincena de agosto y el posterior de la primera de septiembre; ambos invierno, y el escalon ocurre dentro de los tres dias entre merges, lo que es dificil de explicar por estacion, pero un aporte estacional menor no esta descartado (SOSPECHA, no medido). (b) `sin_info`: en despues_571, 276 de 698 pasadas VIIRS 375 (39,5 %) no tienen fila CONS RUTINA con VRP 0 a +-2 min y quedan fuera del denominador; si MIROVA deja de listar pasadas de forma no aleatoria el negativo limpio podria sesgarse (SOSPECHA). (c) La referencia incluye filas del mismo dia de la corrida; las pasadas de la ultima noche que aun no tienen fila caen en `sin_info`, no en el denominador.
