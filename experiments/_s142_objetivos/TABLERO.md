# Tablero de objetivos de paridad con MIROVA (S142)

Generado por `experiments/_s142_objetivos/objetivos.py` desde `objetivos.json` (regla S91: ningún número se escribió a mano). Generado 2026-09-15T13:34:22+00:00 sobre `d54099ea7`. Records leídos del commit de la línea base post-#535 `a54ce6d32` con `git show` (en HEAD ya hay 5 commits NRT posteriores en `data/mirova_equivalent`, que este tablero deja fuera a propósito para medir sobre el mismo banco). Referencia Mirova-v1 fijada a los sha de esa línea base: consolidado `d944cd9cb`, OCR `2712d1743`. Predicado: `frontend/index.html` blob `24fba8a15` (línea base: `24fba8a15`).

**Control del instrumento.** Etiquetas por tramo idénticas a las de `linea_base_post535.json`: antes_535_misma_longitud True, entre_535_y_571 True, despues_571 True. Si alguno diera False, la magnitud y la consistencia no estarían sobre el mismo banco que la detección y las falsas.

## Qué se está comparando, en términos físicos

MIROVA y nosotros miramos las mismas pasadas nocturnas de VIIRS y MODIS sobre los 11 volcanes. Hay tres preguntas distintas. **Detección**: en una noche en que MIROVA vio calor en el cráter, ¿el operador ve algo en nuestro dashboard? **Falsas publicaciones**: en una pasada que MIROVA procesó y donde no vio nada (RUTINA con VRP 0, sin alerta esa noche en ese sensor), ¿publicamos igual? Es la sobre-publicación: píxeles tibios de flanco, nieve o fondo que nuestro pipeline convierte en un cúmulo en el cráter. **Magnitud**: cuando ambos vemos el foco en la misma pasada, ¿cuánta potencia radiativa le asignamos respecto de MIROVA? Una razón bajo 1 significa que integramos menos píxeles del foco o menos exceso por píxel; la línea base congelada ya separó eso contra el OSF.

## 1. Objetivo contra hoy, por sensor

Hoy = régimen posterior a #571, noches UTC 2026-09-01 a 2026-09-15. Línea base congelada = `banco.json` S139/S140, 2026-03-01 a 2026-09-14. La magnitud de la línea base usa el mismo pareo NRT de este script sobre esa ventana (la línea base congelada no la tenía por pasada en el NRT, sólo contra el OSF 2025).

| Sensor | Criterio | Objetivo | Hoy (post #571) | Línea base congelada | Veredicto hoy |
|---|---|---|---|---|---|
| MODIS | detección, focal | 0 noches con alerta perdidas respecto de la línea base (criterio relativo, se juzga en A/B sobre las mismas noches) | 0 perdidas de 0 noches con alerta | 57 perdidas de 65 | sin pérdidas en el tramo (n<20) |
| MODIS | detección, nevado | 0 noches con alerta perdidas respecto de la línea base (criterio relativo, se juzga en A/B sobre las mismas noches) | 0 perdidas de 1 noches con alerta | 0 perdidas de 1 | sin pérdidas en el tramo (n<20) |
| MODIS | falsas por pasada, focal | ≤ 10,0 % | 17,4 % (25 de 144; IC95 12,0 % a 24,4 %) | 19,5 % (351 de 1799; IC95 17,8 % a 21,4 %) | no cumple |
| MODIS | falsas por pasada, nevado | ≤ 15,0 % | 4,4 % (8 de 181; IC95 2,3 % a 8,5 %) | 5,5 % (144 de 2593; IC95 4,7 % a 6,5 %) | cumple |
| MODIS | magnitud | informativa | total 0,81 (n 1 (n<30)); volcanes n≥30: ninguno | total 0,80 (n 9 (n<30)); n≥30: ninguno; fuera de banda: ninguno | informativa (línea base: sin n suficiente) |
| VIIRS375 | detección, focal | 0 noches con alerta perdidas respecto de la línea base (criterio relativo, se juzga en A/B sobre las mismas noches) | 0 perdidas de 38 noches con alerta | 8 perdidas de 599 | sin pérdidas en el tramo |
| VIIRS375 | detección, nevado | 0 noches con alerta perdidas respecto de la línea base (criterio relativo, se juzga en A/B sobre las mismas noches) | 0 perdidas de 16 noches con alerta | 6 perdidas de 179 | sin pérdidas en el tramo (n<20) |
| VIIRS375 | falsas por pasada, focal | ≤ 10,0 % | 84,5 % (71 de 84; IC95 75,3 % a 90,7 %) | 58,7 % (415 de 707; IC95 55,0 % a 62,3 %) | no cumple |
| VIIRS375 | falsas por pasada, nevado | ≤ 15,0 % | 88,1 % (186 de 211; IC95 83,1 % a 91,8 %) | 65,2 % (1512 de 2319; IC95 63,2 % a 67,1 %) | no cumple |
| VIIRS375 | magnitud | mediana por pasada en [0,8 ; 1,25] en cada volcán con n ≥ 30 | total 0,83 (n 104); volcanes n≥30: ninguno | total 0,71 (n 1264); n≥30: Chaiten, Isluga, Lascar, Lastarria, PlanchonPeteroa, PuyehueCordonCaulle, Tupungatito; fuera de banda: Chaiten, Isluga, Lascar, Lastarria, Tupungatito | sin n suficiente (línea base: no cumple) |
| VIIRS750 | detección, focal | 0 noches con alerta perdidas respecto de la línea base (criterio relativo, se juzga en A/B sobre las mismas noches) | 0 perdidas de 9 noches con alerta | 20 perdidas de 193 | sin pérdidas en el tramo (n<20) |
| VIIRS750 | detección, nevado | 0 noches con alerta perdidas respecto de la línea base (criterio relativo, se juzga en A/B sobre las mismas noches) | 0 perdidas de 0 noches con alerta | 8 perdidas de 21 | sin pérdidas en el tramo (n<20) |
| VIIRS750 | falsas por pasada, focal | ≤ 10,0 % | 25,1 % (51 de 203; IC95 19,7 % a 31,5 %) | 29,6 % (563 de 1900; IC95 27,6 % a 31,7 %) | no cumple |
| VIIRS750 | falsas por pasada, nevado | ≤ 15,0 % | 18,4 % (54 de 293; IC95 14,4 % a 23,3 %) | 17,6 % (535 de 3041; IC95 16,3 % a 19,0 %) | no cumple |
| VIIRS750 | magnitud | mediana por pasada en [0,8 ; 1,25] en cada volcán con n ≥ 30 | total 0,32 (n 8 (n<30)); volcanes n≥30: ninguno | total 0,57 (n 218); n≥30: Lascar, PuyehueCordonCaulle; fuera de banda: Lascar, PuyehueCordonCaulle | sin n suficiente (línea base: no cumple) |
| MODIS | Láscar, publicación en pasadas con alerta mayor que en negativas (despues_571) | significativamente mayor | con alerta s/d (n 0); negativas 0,0 % (0 de 27; IC95 0,0 % a 12,5 %); p Fisher una cola s/d | todos los volcanes: con alerta 100,0 % (1 de 1; IC95 20,6 % a 100,0 %), negativas 10,2 % (33 de 325; IC95 7,3 % a 13,9 %) | sin n suficiente |
| MODIS | Láscar, publicación en pasadas con alerta mayor que en negativas (linea_base_s139) | significativamente mayor | con alerta 10,5 % (8 de 76; IC95 5,4 % a 19,4 %); negativas 1,7 % (4 de 233; IC95 0,7 % a 4,3 %); p Fisher una cola 0,0020 | todos los volcanes: con alerta 11,7 % (9 de 77; IC95 6,3 % a 20,8 %), negativas 11,3 % (495 de 4392; IC95 10,4 % a 12,2 %) | cumple |
| todos | control: noches con alerta de hoy iguales a las de la línea base post-#535 por estrato y sensor | igual | True | | |
| MODIS | pasos literales D19, D21 a D25 | implementados y activos | no se mide con este instrumento; los seis figuran ABIERTOS en `docs/MIROVA_DIVERGENCES.md` l. 2097, 2221, 2246, 2275, 2285, 2295 (leído S142) | igual | no cumple |

Nota sobre el criterio MODIS: la spec (l. 84) lo escribe para Láscar pero su valor de partida (11,5 % contra 10,2 %) viene de `docs/audit_s139/VERIFICADOR.md` l. 138, que suma todos los volcanes MODIS. La fila 'todos los volcanes' reproduce esa comparación; sólo en Láscar la diferencia es significativa, con una publicación de apenas un décimo de las pasadas con alerta.

Magnitud total por sensor y tramo (mediana por pasada, n):

| Sensor | linea_base_s139 | antes_535_misma_longitud | entre_535_y_571 | despues_571 |
|---|---|---|---|---|
| MODIS | 0,80 (n 9 (n<30)) | s/d (n 0) | s/d (n 0) | 0,81 (n 1 (n<30)) |
| VIIRS375 | 0,71 (n 1264) | 0,71 (n 74) | 0,82 (n 11 (n<30)) | 0,83 (n 104) |
| VIIRS750 | 0,57 (n 218) | 0,92 (n 15 (n<30)) | 0,91 (n 2 (n<30)) | 0,32 (n 8 (n<30)) |

## 2. Detección: noches con alerta de MIROVA que no publicamos (hoy)

- MODIS focal: 0 de 0: ninguna.
- MODIS nevado: 0 de 1: ninguna.
- VIIRS375 focal: 0 de 38: ninguna.
- VIIRS375 nevado: 0 de 16: ninguna.
- VIIRS750 focal: 0 de 9: ninguna.
- VIIRS750 nevado: 0 de 0: ninguna.

Recall por noche de volcán, cualquier sensor: hoy 100,0 % de 57; línea base congelada 99,6 % de 798. Por sensor hoy: MODIS 100,0 % de 1; VIIRS375 100,0 % de 54; VIIRS750 100,0 % de 9.

## 3. Magnitud por volcán (nuestro/MIROVA por pasada, lo que ve el operador)

Pares en toda la ventana: 1657 (fuente elegida {'CONS': 1250, 'OCR': 407}). Pasadas con fila CONS y OCR a la vez: 305; OCR/CONS 1,00 (n 305), iguales a ±5 % en 82,6 %. Filas de MIROVA pareadas con más de una pasada nuestra (descartadas por duplicado): 0.

### MODIS

| Volcán | Estrato | Hoy post #571 | Antes #535 (15 noches) | Línea base NRT 03-01 a 09-14 | Cúmulo pc en la línea base NRT | No publicados (línea base) |
|---|---|---|---|---|---|---|
| Lascar | focal | s/d (n 0) | s/d (n 0) | mediana 0,75, geom 0,75, p25-p75 0,51 a 0,93, en banda 25,0 %, n 8 (n<30) | 0,75 (n 8 (n<30)) | 68 de 76 |
| Lastarria | focal | s/d (n 0) | s/d (n 0) | s/d (n 0) | s/d (n 0) | 0 de 0 |
| Isluga | focal | s/d (n 0) | s/d (n 0) | s/d (n 0) | s/d (n 0) | 0 de 0 |
| Tupungatito | nevado | s/d (n 0) | s/d (n 0) | s/d (n 0) | s/d (n 0) | 0 de 0 |
| PlanchonPeteroa | focal | s/d (n 0) | s/d (n 0) | s/d (n 0) | s/d (n 0) | 0 de 0 |
| NevadosDeChillan | nevado | s/d (n 0) | s/d (n 0) | s/d (n 0) | s/d (n 0) | 0 de 0 |
| Llaima | nevado | s/d (n 0) | s/d (n 0) | s/d (n 0) | s/d (n 0) | 0 de 0 |
| Villarrica | nevado | 0,81 (n 1 (n<30)) | s/d (n 0) | mediana 0,81, geom 0,81, p25-p75 0,81 a 0,81, en banda 100,0 %, n 1 (n<30) | 0,81 (n 1 (n<30)) | 0 de 1 |
| Copahue | nevado | s/d (n 0) | s/d (n 0) | s/d (n 0) | s/d (n 0) | 0 de 0 |
| PuyehueCordonCaulle | focal | s/d (n 0) | s/d (n 0) | s/d (n 0) | s/d (n 0) | 0 de 0 |
| Chaiten | nevado | s/d (n 0) | s/d (n 0) | s/d (n 0) | s/d (n 0) | 0 de 0 |

Total MODIS línea base NRT: mediana 0,80, geom 0,75, p25-p75 0,54 a 0,92, en banda 33,3 %, n 9 (n<30). Focal: 0,75 (n 8 (n<30)); nevado: 0,81 (n 1 (n<30)). Por fuente: CONS 0,80 (n 9 (n<30)), OCR s/d (n 0). Hoy post #571: mediana 0,81, geom 0,81, p25-p75 0,81 a 0,81, en banda 100,0 %, n 1 (n<30).

### VIIRS375

| Volcán | Estrato | Hoy post #571 | Antes #535 (15 noches) | Línea base NRT 03-01 a 09-14 | Cúmulo pc en la línea base NRT | No publicados (línea base) | OSF 2025 (R_med, n) | Auto-audit por noche 2026-07-16 a 2026-09-14 |
|---|---|---|---|---|---|---|---|---|
| Lascar | focal | 0,63 (n 15 (n<30)) | 0,47 (n 12 (n<30)) | mediana 0,56, geom 0,51, p25-p75 0,41 a 0,70, en banda 11,6 %, n 268 | 0,43 (n 268) | 7 de 275 | 0,58 (n 390) | 0,43 (n 43 noches) |
| Lastarria | focal | 1,05 (n 8 (n<30)) | 0,26 (n 7 (n<30)) | mediana 0,55, geom 0,48, p25-p75 0,33 a 1,01, en banda 20,3 %, n 177 | 0,48 (n 177) | 18 de 195 | 0,65 (n 253) | 0,40 (n 24 noches) |
| Isluga | focal | 0,55 (n 28 (n<30)) | 0,70 (n 20 (n<30)) | mediana 0,60, geom 0,54, p25-p75 0,43 a 0,81, en banda 23,2 %, n 263 | 0,54 (n 263) | 3 de 266 | 0,57 (n 333) | 0,54 (n 52 noches) |
| Tupungatito | nevado | 0,67 (n 15 (n<30)) | 0,83 (n 11 (n<30)) | mediana 0,67, geom 0,59, p25-p75 0,47 a 0,86, en banda 22,4 %, n 156 | 0,67 (n 156) | 8 de 164 | s/d | 0,82 (n 15 noches) |
| PlanchonPeteroa | focal | 1,01 (n 5 (n<30)) | 1,12 (n 1 (n<30)) | mediana 0,97, geom 0,98, p25-p75 0,72 a 1,26, en banda 35,0 %, n 120 | 0,92 (n 120) | 1 de 121 | 0,92 (n 166) | 1,12 (n 10 noches) |
| NevadosDeChillan | nevado | 0,86 (n 2 (n<30)) | 1,27 (n 3 (n<30)) | mediana 1,13, geom 1,11, p25-p75 1,08 a 1,26, en banda 50,0 %, n 8 (n<30) | 1,12 (n 8 (n<30)) | 4 de 12 | 0,01 (n 15) | 1,08 (n 4 noches) |
| Llaima | nevado | s/d (n 0) | s/d (n 0) | mediana 0,43, geom 0,43, p25-p75 0,31 a 0,73, en banda 33,3 %, n 3 (n<30) | 0,43 (n 3 (n<30)) | 0 de 3 | s/d | s/d |
| Villarrica | nevado | 0,84 (n 1 (n<30)) | 0,86 (n 5 (n<30)) | mediana 0,90, geom 0,94, p25-p75 0,82 a 1,07, en banda 75,0 %, n 24 (n<30) | 0,87 (n 24 (n<30)) | 0 de 24 | 1,35 (n 16) | 0,81 (n 13 noches) |
| Copahue | nevado | s/d (n 0) | s/d (n 0) | mediana 0,96, geom 0,91, p25-p75 0,80 a 1,16, en banda 50,0 %, n 4 (n<30) | 0,97 (n 4 (n<30)) | 0 de 4 | 0,74 (n 28) | 1,18 (n 2 noches) |
| PuyehueCordonCaulle | focal | 1,08 (n 23 (n<30)) | 0,75 (n 11 (n<30)) | mediana 1,04, geom 1,07, p25-p75 0,77 a 1,44, en banda 38,8 %, n 196 | 0,66 (n 196) | 7 de 203 | 0,93 (n 234) | 0,95 (n 30 noches) |
| Chaiten | nevado | 1,35 (n 7 (n<30)) | 0,83 (n 4 (n<30)) | mediana 1,35, geom 1,30, p25-p75 1,09 a 1,73, en banda 24,4 %, n 45 | 0,98 (n 45) | 0 de 45 | 1,40 (n 64) | 1,13 (n 13 noches) |

Total VIIRS375 línea base NRT: mediana 0,71, geom 0,65, p25-p75 0,48 a 1,01, en banda 25,1 %, n 1264. Focal: 0,68 (n 1024); nevado: 0,80 (n 240). Por fuente: CONS 0,73 (n 910), OCR 0,66 (n 354). Hoy post #571: mediana 0,83, geom 0,77, p25-p75 0,53 a 1,14, en banda 31,7 %, n 104.

### VIIRS750

| Volcán | Estrato | Hoy post #571 | Antes #535 (15 noches) | Línea base NRT 03-01 a 09-14 | Cúmulo pc en la línea base NRT | No publicados (línea base) |
|---|---|---|---|---|---|---|
| Lascar | focal | 0,40 (n 3 (n<30)) | 0,61 (n 2 (n<30)) | mediana 0,54, geom 0,50, p25-p75 0,40 a 0,75, en banda 15,2 %, n 151 | 0,54 (n 151) | 8 de 159 |
| Lastarria | focal | s/d (n 0) | s/d (n 0) | s/d (n 0) | s/d (n 0) | 0 de 0 |
| Isluga | focal | s/d (n 0) | 2,11 (n 2 (n<30)) | mediana 1,06, geom 1,40, p25-p75 0,56 a 3,27, en banda 23,1 %, n 26 (n<30) | 1,06 (n 26 (n<30)) | 12 de 38 |
| Tupungatito | nevado | s/d (n 0) | s/d (n 0) | mediana 0,07, geom 0,07, p25-p75 0,06 a 0,08, en banda 0,0 %, n 2 (n<30) | 0,07 (n 2 (n<30)) | 11 de 13 |
| PlanchonPeteroa | focal | 1,67 (n 1 (n<30)) | 1,07 (n 1 (n<30)) | mediana 1,67, geom 2,81, p25-p75 1,37 a 7,08, en banda 33,3 %, n 3 (n<30) | 1,67 (n 3 (n<30)) | 6 de 9 |
| NevadosDeChillan | nevado | s/d (n 0) | s/d (n 0) | s/d (n 0) | s/d (n 0) | 0 de 0 |
| Llaima | nevado | s/d (n 0) | s/d (n 0) | s/d (n 0) | s/d (n 0) | 0 de 0 |
| Villarrica | nevado | s/d (n 0) | 0,99 (n 4 (n<30)) | mediana 0,99, geom 0,84, p25-p75 0,77 a 1,13, en banda 75,0 %, n 4 (n<30) | 0,99 (n 4 (n<30)) | 2 de 6 |
| Copahue | nevado | s/d (n 0) | s/d (n 0) | mediana 1,33, geom 1,33, p25-p75 1,33 a 1,33, en banda 0,0 %, n 1 (n<30) | 1,33 (n 1 (n<30)) | 0 de 1 |
| PuyehueCordonCaulle | focal | 0,09 (n 4 (n<30)) | 0,69 (n 6 (n<30)) | mediana 0,57, geom 0,51, p25-p75 0,29 a 0,99, en banda 23,3 %, n 30 | 0,57 (n 30) | 8 de 38 |
| Chaiten | nevado | s/d (n 0) | s/d (n 0) | mediana 1,15, geom 1,15, p25-p75 1,15 a 1,15, en banda 100,0 %, n 1 (n<30) | 1,15 (n 1 (n<30)) | 0 de 1 |

Total VIIRS750 línea base NRT: mediana 0,57, geom 0,58, p25-p75 0,39 a 0,85, en banda 18,8 %, n 218. Focal: 0,57 (n 210); nevado: 0,99 (n 8 (n<30)). Por fuente: CONS 0,55 (n 183), OCR 0,68 (n 35). Hoy post #571: mediana 0,32, geom 0,27, p25-p75 0,09 a 0,58, en banda 0,0 %, n 8 (n<30).

**Los tres volcanes VIIRS 375 más lejos de 1 en magnitud (línea base NRT, n ≥ 30, por |log mediana|):** Lastarria 0,55 (n 177); Lascar 0,56 (n 268); Isluga 0,60 (n 263).

**¿Cuentan lo mismo el NRT y el OSF?** El OSF v2.5 no es el producto NRT: según `docs/audit_s139/OSF_VS_NRT.md` l. 12-16 (lectura de Coppola et al. 2026, Scientific Data, p. 7-8, no releída en esta sesión) se construye con una clase automática y umbrales VRP por sensor, y su pareo (`scripts/descomponer_magnitud_osf.py:86-89, 116`) exige un cúmulo en el cráter, no el predicado del dashboard, y es de 2025. El NRT publica cada alerta tal cual. El total VIIRS 375 contra el OSF es R_med 0,70 (n 1499), y contra el NRT en la ventana de la línea base es 0,71 (n 1264). Donde las dos referencias coinciden, el sesgo es del pipeline y no de la referencia; donde difieren, pesa la selección de pasadas de cada una (umbral del OSF, año, predicado).

Volcanes V375 con n ≥ 15 en ambas referencias, mediana NRT / mediana OSF: Lascar 0,56 contra 0,58 (cociente 0,96); Lastarria 0,55 contra 0,65 (cociente 0,85); Isluga 0,60 contra 0,57 (cociente 1,04); PlanchonPeteroa 0,97 contra 0,92 (cociente 1,05); Villarrica 0,90 contra 1,35 (cociente 0,67); PuyehueCordonCaulle 1,04 contra 0,93 (cociente 1,12); Chaiten 1,35 contra 1,40 (cociente 0,96). Coinciden a ±20 %: Lascar, Lastarria, Isluga, PlanchonPeteroa, PuyehueCordonCaulle, Chaiten; difieren: Villarrica.

## 4. Consistencia del propio MIROVA

**Definiciones, fijadas antes de mirar los números** (copiadas del JSON):

- `pasada_mirova`: filas nocturnas de MIROVA del mismo volcan y sensor agrupadas a +-2 min (CONS y OCR juntas); estado ALERTA si alguna fila es ALERTA, FP si alguna es FALSO_POSITIVO y ninguna ALERTA, RUTINA si no
- `listada`: pasada MIROVA en estado ALERTA o RUTINA (FP excluida: calor fuera del limite, sin informacion del crater, igual que el banco)
- `noche`: fecha UTC de la pasada, igual que el banco
- `C1_repeticion_intra_sensor`: VIIRS 375: en noches de volcan con >= 1 pasada ALERTA y >= 2 listadas, sobre pares ordenados (i ALERTA, j distinta listada) la fraccion con j ALERTA. Tasa base: fraccion ALERTA entre todas las listadas del volcan.
- `C1b_contradiccion_canales`: pasadas MIROVA con fila CONS RUTINA y fila OCR ALERTA a la vez (MIROVA se contradice entre su CSV y su imagen)
- `C2_entre_sensores`: en noches con >= 1 pasada ALERTA en el sensor A, fraccion de pasadas listadas del sensor B esa noche que son ALERTA (A=V375,B=V750 y A=V750,B=V375)
- `C2b_falsas_de_mirova_contra_otro_sensor`: analogo MIROVA-contra-MIROVA de la banda: noches negativas segun el sensor A (>= 1 listada, ninguna ALERTA ni FP en A) y fraccion de pasadas listadas del sensor B esa noche con ALERTA
- `C3_persistencia_noche`: VIIRS 375, noches listadas: P(noche ALERTA | noche anterior ALERTA) y P(noche ALERTA | noche anterior listada sin ALERTA ni FP); C3b: fraccion de pasadas listadas en ALERTA en la noche siguiente a una noche negativa
- `C4_negativos_adyacentes`: nuestros neg_limpio VIIRS 375: fraccion cuya noche esta a +-1 noche de una noche con ALERTA V375 de MIROVA en el mismo volcan, y tasa de publicacion nuestra en adyacentes y no adyacentes

### Ventana linea_base_s139 (2026-03-01 a 2026-09-14)

| Grupo | C1 vecina V375 también alerta | C1 tasa base alerta | C1 noches todas alerta | C2 V375 alerta: V750 alerta | C2 V750 alerta: V375 alerta | C2b V375 negativa: V750 alerta | C2b V750 negativa: V375 alerta | C3 alerta tras alerta | C3 alerta tras negativa | C3b pasadas alerta tras noche negativa | C1b contradicciones CONS/OCR |
|---|---|---|---|---|---|---|---|---|---|---|---|
| TOTAL | 56,9 % (1414 de 2484; IC95 55,0 % a 58,9 %) | 24,6 % (1326 de 5390; IC95 23,5 % a 25,8 %) | 25,6 % (184 de 720; IC95 22,5 % a 28,9 %) | 12,7 % (246 de 1939; IC95 11,3 % a 14,2 %) | 69,5 % (387 de 557; IC95 65,5 % a 73,2 %) | 0,2 % (6 de 3168; IC95 0,1 % a 0,4 %) | 19,4 % (934 de 4813; IC95 18,3 % a 20,5 %) | 74,1 % (541 de 730; IC95 70,8 % a 77,2 %) | 17,1 % (189 de 1107; IC95 15,0 % a 19,4 %) | 10,5 % (300 de 2858; IC95 9,4 % a 11,7 %) | 0 |
| focal | 61,3 % (1226 de 1999; IC95 59,2 % a 63,4 %) | 44,2 % (1072 de 2427; IC95 42,2 % a 46,2 %) | 29,8 % (165 de 554; IC95 26,1 % a 33,7 %) | 15,6 % (228 de 1465; IC95 13,8 % a 17,5 %) | 72,0 % (362 de 503; IC95 67,9 % a 75,7 %) | 0,5 % (4 de 736; IC95 0,2 % a 1,4 %) | 36,9 % (705 de 1912; IC95 34,7 % a 39,1 %) | 80,2 % (450 de 561; IC95 76,7 % a 83,3 %) | 42,4 % (106 de 250; IC95 36,4 % a 48,6 %) | 27,8 % (185 de 665; IC95 24,6 % a 31,4 %) | 0 |
| nevado | 38,8 % (188 de 485; IC95 34,5 % a 43,2 %) | 8,6 % (254 de 2963; IC95 7,6 % a 9,6 %) | 11,5 % (19 de 166; IC95 7,4 % a 17,2 %) | 3,8 % (18 de 474; IC95 2,4 % a 5,9 %) | 46,3 % (25 de 54; IC95 33,7 % a 59,4 %) | 0,1 % (2 de 2432; IC95 0,0 % a 0,3 %) | 7,9 % (229 de 2901; IC95 7,0 % a 8,9 %) | 53,8 % (91 de 169; IC95 46,3 % a 61,2 %) | 9,7 % (83 de 857; IC95 7,9 % a 11,8 %) | 5,2 % (115 de 2193; IC95 4,4 % a 6,3 %) | 0 |
| Lascar | 67,2 % (310 de 461; IC95 62,8 % a 71,4 %) | 58,4 % (277 de 474; IC95 53,9 % a 62,8 %) | 41,7 % (58 de 139; IC95 33,9 % a 50,0 %) | 42,0 % (152 de 362; IC95 37,0 % a 47,1 %) | 74,2 % (210 de 283; IC95 68,8 % a 79,0 %) | 0,0 % (0 de 78; IC95 0,0 % a 4,7 %) | 35,1 % (67 de 191; IC95 28,7 % a 42,1 %) | 88,7 % (126 de 142; IC95 82,5 % a 92,9 %) | 50,0 % (13 de 26; IC95 32,1 % a 67,9 %) | 34,8 % (23 de 66; IC95 24,5 % a 46,9 %) | 0 |
| Lastarria | 52,3 % (158 de 302; IC95 46,7 % a 57,9 %) | 46,1 % (198 de 430; IC95 41,4 % a 50,8 %) | 25,4 % (28 de 110; IC95 18,2 % a 34,3 %) | 0,0 % (0 de 301; IC95 0,0 % a 1,3 %) | s/d (n 0) | 0,0 % (0 de 89; IC95 0,0 % a 4,1 %) | 46,2 % (195 de 422; IC95 41,5 % a 51,0 %) | 84,9 % (101 de 119; IC95 77,3 % a 90,2 %) | 61,5 % (16 de 26; IC95 42,5 % a 77,6 %) | 39,0 % (23 de 59; IC95 27,6 % a 51,7 %) | 0 |
| Isluga | 60,0 % (288 de 480; IC95 55,5 % a 64,3 %) | 57,6 % (268 de 465; IC95 53,1 % a 62,1 %) | 28,3 % (39 de 138; IC95 21,4 % a 36,3 %) | 9,3 % (32 de 343; IC95 6,7 % a 12,9 %) | 64,1 % (59 de 92; IC95 53,9 % a 73,2 %) | 3,8 % (2 de 53; IC95 1,0 % a 12,8 %) | 55,8 % (207 de 371; IC95 50,7 % a 60,8 %) | 93,3 % (126 de 135; IC95 87,8 % a 96,5 %) | 58,8 % (10 de 17; IC95 36,0 % a 78,4 %) | 41,0 % (16 de 39; IC95 27,1 % a 56,6 %) | 0 |
| Tupungatito | 51,0 % (158 de 310; IC95 45,4 % a 56,5 %) | 34,6 % (165 de 477; IC95 30,5 % a 39,0 %) | 15,4 % (14 de 91; IC95 9,4 % a 24,2 %) | 4,6 % (12 de 260; IC95 2,7 % a 7,9 %) | 63,3 % (19 de 30; IC95 45,5 % a 78,1 %) | 0,5 % (1 de 182; IC95 0,1 % a 3,0 %) | 33,1 % (146 de 441; IC95 28,9 % a 37,6 %) | 72,5 % (71 de 98; IC95 62,9 % a 80,3 %) | 48,4 % (30 de 62; IC95 36,4 % a 60,6 %) | 30,4 % (52 de 171; IC95 24,0 % a 37,7 %) | 0 |
| PlanchonPeteroa | 42,5 % (96 de 226; IC95 36,2 % a 49,0 %) | 25,2 % (123 de 488; IC95 21,6 % a 29,2 %) | 15,6 % (12 de 77; IC95 9,2 % a 25,3 %) | 3,0 % (6 de 202; IC95 1,4 % a 6,3 %) | 46,2 % (12 de 26; IC95 28,8 % a 64,5 %) | 0,8 % (2 de 243; IC95 0,2 % a 2,9 %) | 24,1 % (111 de 460; IC95 20,4 % a 28,2 %) | 64,9 % (48 de 74; IC95 53,5 % a 74,8 %) | 32,1 % (26 de 81; IC95 22,9 % a 42,9 %) | 17,5 % (38 de 217; IC95 13,0 % a 23,1 %) | 0 |
| NevadosDeChillan | 9,1 % (2 de 22; IC95 2,5 % a 27,8 %) | 2,6 % (12 de 467; IC95 1,5 % a 4,4 %) | 9,1 % (1 de 11; IC95 1,6 % a 37,7 %) | 0,0 % (0 de 30; IC95 0,0 % a 11,3 %) | s/d (n 0) | 0,0 % (0 de 423; IC95 0,0 % a 0,9 %) | 2,6 % (12 de 465; IC95 1,5 % a 4,5 %) | 0,0 % (0 de 9; IC95 0,0 % a 29,9 %) | 6,2 % (9 de 144; IC95 3,3 % a 11,5 %) | 2,9 % (10 de 350; IC95 1,6 % a 5,2 %) | 0 |
| Llaima | 28,6 % (2 de 7; IC95 8,2 % a 64,1 %) | 0,6 % (3 de 491; IC95 0,2 % a 1,8 %) | 0,0 % (0 de 2; IC95 0,0 % a 65,8 %) | 0,0 % (0 de 6; IC95 0,0 % a 39,0 %) | s/d (n 0) | 0,0 % (0 de 489; IC95 0,0 % a 0,8 %) | 0,6 % (3 de 491; IC95 0,2 % a 1,8 %) | 0,0 % (0 de 2; IC95 0,0 % a 65,8 %) | 1,2 % (2 de 171; IC95 0,3 % a 4,2 %) | 0,7 % (3 de 430; IC95 0,2 % a 2,0 %) | 0 |
| Villarrica | 0,0 % (0 de 46; IC95 0,0 % a 7,7 %) | 4,8 % (25 de 516; IC95 3,3 % a 7,0 %) | 0,0 % (0 de 24; IC95 0,0 % a 13,8 %) | 7,6 % (5 de 66; IC95 3,3 % a 16,5 %) | 27,8 % (5 de 18; IC95 12,5 % a 50,9 %) | 0,0 % (0 de 443; IC95 0,0 % a 0,9 %) | 4,0 % (20 de 498; IC95 2,6 % a 6,1 %) | 25,0 % (6 de 24; IC95 12,0 % a 44,9 %) | 11,9 % (19 de 159; IC95 7,8 % a 17,9 %) | 4,6 % (19 de 416; IC95 2,9 % a 7,0 %) | 0 |
| Copahue | 0,0 % (0 de 7; IC95 0,0 % a 35,4 %) | 0,8 % (4 de 484; IC95 0,3 % a 2,1 %) | 0,0 % (0 de 4; IC95 0,0 % a 49,0 %) | 0,0 % (0 de 11; IC95 0,0 % a 25,9 %) | 0,0 % (0 de 3; IC95 0,0 % a 56,1 %) | 0,2 % (1 de 469; IC95 0,0 % a 1,2 %) | 0,8 % (4 de 481; IC95 0,3 % a 2,1 %) | 0,0 % (0 de 4; IC95 0,0 % a 49,0 %) | 2,4 % (4 de 166; IC95 0,9 % a 6,0 %) | 1,0 % (4 de 413; IC95 0,4 % a 2,5 %) | 0 |
| PuyehueCordonCaulle | 70,6 % (374 de 530; IC95 66,5 % a 74,3 %) | 36,1 % (206 de 570; IC95 32,3 % a 40,2 %) | 31,1 % (28 de 90; IC95 22,5 % a 41,3 %) | 14,8 % (38 de 257; IC95 11,0 % a 19,6 %) | 79,4 % (81 de 102; IC95 70,6 % a 86,1 %) | 0,0 % (0 de 273; IC95 0,0 % a 1,4 %) | 26,7 % (125 de 468; IC95 22,9 % a 30,9 %) | 53,8 % (49 de 91; IC95 43,7 % a 63,7 %) | 41,0 % (41 de 100; IC95 31,9 % a 50,8 %) | 29,9 % (85 de 284; IC95 24,9 % a 35,5 %) | 0 |
| Chaiten | 28,0 % (26 de 93; IC95 19,9 % a 37,8 %) | 8,5 % (45 de 528; IC95 6,4 % a 11,2 %) | 11,8 % (4 de 34; IC95 4,7 % a 26,6 %) | 1,0 % (1 de 101; IC95 0,2 % a 5,4 %) | 33,3 % (1 de 3; IC95 6,2 % a 79,2 %) | 0,0 % (0 de 426; IC95 0,0 % a 0,9 %) | 8,4 % (44 de 525; IC95 6,3 % a 11,1 %) | 43,8 % (14 de 32; IC95 28,2 % a 60,7 %) | 12,3 % (19 de 155; IC95 8,0 % a 18,4 %) | 6,5 % (27 de 413; IC95 4,5 % a 9,3 %) | 0 |

| Grupo | C4 negativos limpios V375 a ±1 noche de una alerta | publicamos en adyacentes | publicamos en no adyacentes |
|---|---|---|---|
| TOTAL | 24,7 % (747 de 3026; IC95 23,2 % a 26,2 %) | 66,4 % (496 de 747; IC95 62,9 % a 69,7 %) | 62,8 % (1431 de 2279; IC95 60,8 % a 64,8 %) |
| focal | 56,7 % (401 de 707; IC95 53,0 % a 60,3 %) | 65,1 % (261 de 401; IC95 60,3 % a 69,6 %) | 50,3 % (154 de 306; IC95 44,8 % a 55,9 %) |
| nevado | 14,9 % (346 de 2319; IC95 13,5 % a 16,4 %) | 67,9 % (235 de 346; IC95 62,8 % a 72,6 %) | 64,7 % (1277 de 1973; IC95 62,6 % a 66,8 %) |
| Lascar | 67,1 % (51 de 76; IC95 55,9 % a 76,6 %) | 37,2 % (19 de 51; IC95 25,3 % a 51,0 %) | 20,0 % (5 de 25; IC95 8,9 % a 39,1 %) |
| Lastarria | 64,3 % (54 de 84; IC95 53,6 % a 73,7 %) | 44,4 % (24 de 54; IC95 32,0 % a 57,6 %) | 20,0 % (6 de 30; IC95 9,5 % a 37,3 %) |
| Isluga | 64,6 % (31 de 48; IC95 50,4 % a 76,6 %) | 87,1 % (27 de 31; IC95 71,2 % a 94,9 %) | 76,5 % (13 de 17; IC95 52,7 % a 90,5 %) |
| Tupungatito | 54,9 % (95 de 173; IC95 47,5 % a 62,1 %) | 54,7 % (52 de 95; IC95 44,7 % a 64,4 %) | 44,9 % (35 de 78; IC95 34,3 % a 55,9 %) |
| PlanchonPeteroa | 44,9 % (106 de 236; IC95 38,7 % a 51,3 %) | 68,9 % (73 de 106; IC95 59,5 % a 76,9 %) | 55,4 % (72 de 130; IC95 46,8 % a 63,6 %) |
| NevadosDeChillan | 11,4 % (45 de 396; IC95 8,6 % a 14,9 %) | 44,4 % (20 de 45; IC95 30,9 % a 58,8 %) | 34,2 % (120 de 351; IC95 29,4 % a 39,3 %) |
| Llaima | 2,2 % (10 de 461; IC95 1,2 % a 4,0 %) | 70,0 % (7 de 10; IC95 39,7 % a 89,2 %) | 71,4 % (322 de 451; IC95 67,1 % a 75,4 %) |
| Villarrica | 19,7 % (85 de 431; IC95 16,2 % a 23,7 %) | 80,0 % (68 de 85; IC95 70,3 % a 87,1 %) | 70,8 % (245 de 346; IC95 65,8 % a 75,3 %) |
| Copahue | 3,6 % (16 de 445; IC95 2,2 % a 5,8 %) | 93,8 % (15 de 16; IC95 71,7 % a 98,9 %) | 78,3 % (336 de 429; IC95 74,2 % a 82,0 %) |
| PuyehueCordonCaulle | 60,5 % (159 de 263; IC95 54,4 % a 66,2 %) | 74,2 % (118 de 159; IC95 66,9 % a 80,4 %) | 55,8 % (58 de 104; IC95 46,2 % a 64,9 %) |
| Chaiten | 23,0 % (95 de 413; IC95 19,2 % a 27,3 %) | 76,8 % (73 de 95; IC95 67,4 % a 84,2 %) | 68,9 % (219 de 318; IC95 63,6 % a 73,7 %) |

### Ventana despues_571 (2026-09-01 a 2026-09-15)

| Grupo | C1 vecina V375 también alerta | C1 tasa base alerta | C1 noches todas alerta | C2 V375 alerta: V750 alerta | C2 V750 alerta: V375 alerta | C2b V375 negativa: V750 alerta | C2b V750 negativa: V375 alerta | C3 alerta tras alerta | C3 alerta tras negativa | C3b pasadas alerta tras noche negativa | C1b contradicciones CONS/OCR |
|---|---|---|---|---|---|---|---|---|---|---|---|
| TOTAL | 54,1 % (152 de 281; IC95 48,2 % a 59,8 %) | 21,6 % (113 de 524; IC95 18,3 % a 25,3 %) | 17,2 % (10 de 58; IC95 9,6 % a 28,9 %) | 5,5 % (10 de 182; IC95 3,0 % a 9,8 %) | 70,0 % (21 de 30; IC95 52,1 % a 83,3 %) | 0,3 % (1 de 311; IC95 0,1 % a 1,8 %) | 18,6 % (92 de 494; IC95 15,4 % a 22,3 %) | 75,5 % (37 de 49; IC95 61,9 % a 85,4 %) | 18,5 % (15 de 81; IC95 11,6 % a 28,3 %) | 8,8 % (23 de 260; IC95 6,0 % a 12,9 %) | 0 |
| focal | 58,8 % (124 de 211; IC95 52,0 % a 65,2 %) | 35,7 % (85 de 238; IC95 29,9 % a 42,0 %) | 22,5 % (9 de 40; IC95 12,3 % a 37,5 %) | 7,9 % (10 de 126; IC95 4,4 % a 14,0 %) | 70,0 % (21 de 30; IC95 52,1 % a 83,3 %) | 1,1 % (1 de 87; IC95 0,2 % a 6,2 %) | 30,8 % (64 de 208; IC95 24,9 % a 37,3 %) | 76,5 % (26 de 34; IC95 60,0 % a 87,6 %) | 36,4 % (8 de 22; IC95 19,7 % a 57,0 %) | 19,4 % (13 de 67; IC95 11,7 % a 30,4 %) | 0 |
| nevado | 40,0 % (28 de 70; IC95 29,3 % a 51,7 %) | 9,8 % (28 de 286; IC95 6,9 % a 13,8 %) | 5,6 % (1 de 18; IC95 1,0 % a 25,8 %) | 0,0 % (0 de 56; IC95 0,0 % a 6,4 %) | s/d (n 0) | 0,0 % (0 de 224; IC95 0,0 % a 1,7 %) | 9,8 % (28 de 286; IC95 6,9 % a 13,8 %) | 73,3 % (11 de 15; IC95 48,0 % a 89,1 %) | 11,9 % (7 de 59; IC95 5,9 % a 22,5 %) | 5,2 % (10 de 193; IC95 2,8 % a 9,3 %) | 0 |
| Lascar | 61,1 % (22 de 36; IC95 44,9 % a 75,2 %) | 37,8 % (17 de 45; IC95 25,1 % a 52,4 %) | 37,5 % (3 de 8; IC95 13,7 % a 69,4 %) | 8,3 % (2 de 24; IC95 2,3 % a 25,9 %) | 44,4 % (4 de 9; IC95 18,9 % a 73,3 %) | 0,0 % (0 de 16; IC95 0,0 % a 19,4 %) | 36,1 % (13 de 36; IC95 22,5 % a 52,4 %) | 66,7 % (4 de 6; IC95 30,0 % a 90,3 %) | 40,0 % (2 de 5; IC95 11,8 % a 76,9 %) | 18,8 % (3 de 16; IC95 6,6 % a 43,0 %) | 0 |
| Lastarria | 20,0 % (4 de 20; IC95 8,1 % a 41,6 %) | 20,0 % (9 de 45; IC95 10,9 % a 33,8 %) | 0,0 % (0 de 7; IC95 0,0 % a 35,4 %) | 0,0 % (0 de 23; IC95 0,0 % a 14,3 %) | s/d (n 0) | 0,0 % (0 de 16; IC95 0,0 % a 19,4 %) | 20,0 % (9 de 45; IC95 10,9 % a 33,8 %) | 60,0 % (3 de 5; IC95 23,1 % a 88,2 %) | 66,7 % (2 de 3; IC95 20,8 % a 93,8 %) | 37,5 % (3 de 8; IC95 13,7 % a 69,4 %) | 0 |
| Isluga | 60,6 % (40 de 66; IC95 48,5 % a 71,5 %) | 60,4 % (29 de 48; IC95 46,3 % a 73,0 %) | 23,1 % (3 de 13; IC95 8,2 % a 50,3 %) | 2,6 % (1 de 39; IC95 0,4 % a 13,2 %) | 100,0 % (3 de 3; IC95 43,9 % a 100,0 %) | 0,0 % (0 de 6; IC95 0,0 % a 39,0 %) | 57,8 % (26 de 45; IC95 43,3 % a 71,0 %) | 91,7 % (11 de 12; IC95 64,6 % a 98,5 %) | 50,0 % (1 de 2; IC95 9,4 % a 90,5 %) | 33,3 % (2 de 6; IC95 9,7 % a 70,0 %) | 0 |
| Tupungatito | 55,0 % (22 de 40; IC95 39,8 % a 69,3 %) | 36,4 % (16 de 44; IC95 23,8 % a 51,1 %) | 12,5 % (1 de 8; IC95 2,2 % a 47,1 %) | 0,0 % (0 de 26; IC95 0,0 % a 12,9 %) | s/d (n 0) | 0,0 % (0 de 15; IC95 0,0 % a 20,4 %) | 36,4 % (16 de 44; IC95 23,8 % a 51,1 %) | 85,7 % (6 de 7; IC95 48,7 % a 97,4 %) | 66,7 % (2 de 3; IC95 20,8 % a 93,8 %) | 33,3 % (3 de 9; IC95 12,1 % a 64,6 %) | 0 |
| PlanchonPeteroa | 33,3 % (6 de 18; IC95 16,3 % a 56,2 %) | 14,9 % (7 de 47; IC95 7,4 % a 27,7 %) | 0,0 % (0 de 4; IC95 0,0 % a 49,0 %) | 0,0 % (0 de 12; IC95 0,0 % a 24,2 %) | 0,0 % (0 de 3; IC95 0,0 % a 56,1 %) | 3,3 % (1 de 30; IC95 0,6 % a 16,7 %) | 15,9 % (7 de 44; IC95 7,9 % a 29,4 %) | 66,7 % (2 de 3; IC95 20,8 % a 93,8 %) | 25,0 % (2 de 8; IC95 7,1 % a 59,1 %) | 12,5 % (3 de 24; IC95 4,3 % a 31,0 %) | 0 |
| NevadosDeChillan | 0,0 % (0 de 6; IC95 0,0 % a 39,0 %) | 6,4 % (3 de 47; IC95 2,2 % a 17,2 %) | 0,0 % (0 de 3; IC95 0,0 % a 56,1 %) | 0,0 % (0 de 8; IC95 0,0 % a 32,4 %) | s/d (n 0) | 0,0 % (0 de 41; IC95 0,0 % a 8,6 %) | 6,4 % (3 de 47; IC95 2,2 % a 17,2 %) | 50,0 % (1 de 2; IC95 9,4 % a 90,5 %) | 16,7 % (2 de 12; IC95 4,7 % a 44,8 %) | 5,4 % (2 de 37; IC95 1,5 % a 17,7 %) | 0 |
| Llaima | s/d (n 0) | 0,0 % (0 de 48; IC95 0,0 % a 7,4 %) | s/d (n 0) | s/d (n 0) | s/d (n 0) | 0,0 % (0 de 47; IC95 0,0 % a 7,6 %) | 0,0 % (0 de 48; IC95 0,0 % a 7,4 %) | s/d (n 0) | 0,0 % (0 de 11; IC95 0,0 % a 25,9 %) | 0,0 % (0 de 37; IC95 0,0 % a 9,4 %) | 0 |
| Villarrica | 0,0 % (0 de 5; IC95 0,0 % a 43,5 %) | 3,9 % (2 de 51; IC95 1,1 % a 13,2 %) | 0,0 % (0 de 2; IC95 0,0 % a 65,8 %) | 0,0 % (0 de 4; IC95 0,0 % a 49,0 %) | s/d (n 0) | 0,0 % (0 de 46; IC95 0,0 % a 7,7 %) | 3,9 % (2 de 51; IC95 1,1 % a 13,2 %) | 100,0 % (1 de 1; IC95 20,6 % a 100,0 %) | 7,7 % (1 de 13; IC95 1,4 % a 33,3 %) | 2,3 % (1 de 43; IC95 0,4 % a 12,1 %) | 0 |
| Copahue | s/d (n 0) | 0,0 % (0 de 47; IC95 0,0 % a 7,6 %) | s/d (n 0) | s/d (n 0) | s/d (n 0) | 0,0 % (0 de 46; IC95 0,0 % a 7,7 %) | 0,0 % (0 de 47; IC95 0,0 % a 7,6 %) | s/d (n 0) | 0,0 % (0 de 12; IC95 0,0 % a 24,2 %) | 0,0 % (0 de 40; IC95 0,0 % a 8,8 %) | 0 |
| PuyehueCordonCaulle | 73,2 % (52 de 71; IC95 62,0 % a 82,2 %) | 43,4 % (23 de 53; IC95 30,9 % a 56,7 %) | 37,5 % (3 de 8; IC95 13,7 % a 69,4 %) | 25,0 % (7 de 28; IC95 12,7 % a 43,4 %) | 93,3 % (14 de 15; IC95 70,2 % a 98,8 %) | 0,0 % (0 de 19; IC95 0,0 % a 16,8 %) | 23,7 % (9 de 38; IC95 13,0 % a 39,2 %) | 75,0 % (6 de 8; IC95 40,9 % a 92,8 %) | 25,0 % (1 de 4; IC95 4,6 % a 69,9 %) | 15,4 % (2 de 13; IC95 4,3 % a 42,2 %) | 0 |
| Chaiten | 31,6 % (6 de 19; IC95 15,4 % a 54,0 %) | 14,3 % (7 de 49; IC95 7,1 % a 26,7 %) | 0,0 % (0 de 5; IC95 0,0 % a 43,5 %) | 0,0 % (0 de 18; IC95 0,0 % a 17,6 %) | s/d (n 0) | 0,0 % (0 de 29; IC95 0,0 % a 11,7 %) | 14,3 % (7 de 49; IC95 7,1 % a 26,7 %) | 60,0 % (3 de 5; IC95 23,1 % a 88,2 %) | 25,0 % (2 de 8; IC95 7,1 % a 59,1 %) | 14,8 % (4 de 27; IC95 5,9 % a 32,5 %) | 0 |

| Grupo | C4 negativos limpios V375 a ±1 noche de una alerta | publicamos en adyacentes | publicamos en no adyacentes |
|---|---|---|---|
| TOTAL | 28,5 % (84 de 295; IC95 23,6 % a 33,9 %) | 85,7 % (72 de 84; IC95 76,7 % a 91,6 %) | 87,7 % (185 de 211; IC95 82,6 % a 91,5 %) |
| focal | 61,9 % (52 de 84; IC95 51,2 % a 71,5 %) | 82,7 % (43 de 52; IC95 70,3 % a 90,6 %) | 87,5 % (28 de 32; IC95 71,9 % a 95,0 %) |
| nevado | 15,2 % (32 de 211; IC95 10,9 % a 20,6 %) | 90,6 % (29 de 32; IC95 75,8 % a 96,8 %) | 87,7 % (157 de 179; IC95 82,1 % a 91,7 %) |
| Lascar | 81,2 % (13 de 16; IC95 57,0 % a 93,4 %) | 84,6 % (11 de 13; IC95 57,8 % a 95,7 %) | 100,0 % (3 de 3; IC95 43,9 % a 100,0 %) |
| Lastarria | 56,2 % (9 de 16; IC95 33,2 % a 76,9 %) | 77,8 % (7 de 9; IC95 45,3 % a 93,7 %) | 85,7 % (6 de 7; IC95 48,7 % a 97,4 %) |
| Isluga | 100,0 % (6 de 6; IC95 61,0 % a 100,0 %) | 66,7 % (4 de 6; IC95 30,0 % a 90,3 %) | s/d (n 0) |
| Tupungatito | 57,1 % (8 de 14; IC95 32,6 % a 78,6 %) | 87,5 % (7 de 8; IC95 52,9 % a 97,8 %) | 100,0 % (6 de 6; IC95 61,0 % a 100,0 %) |
| PlanchonPeteroa | 44,8 % (13 de 29; IC95 28,4 % a 62,5 %) | 76,9 % (10 de 13; IC95 49,7 % a 91,8 %) | 87,5 % (14 de 16; IC95 64,0 % a 96,5 %) |
| NevadosDeChillan | 23,7 % (9 de 38; IC95 13,0 % a 39,2 %) | 88,9 % (8 de 9; IC95 56,5 % a 98,0 %) | 93,1 % (27 de 29; IC95 78,0 % a 98,1 %) |
| Llaima | 0,0 % (0 de 44; IC95 0,0 % a 8,0 %) | s/d (n 0) | 86,4 % (38 de 44; IC95 73,3 % a 93,6 %) |
| Villarrica | 6,8 % (3 de 44; IC95 2,4 % a 18,2 %) | 66,7 % (2 de 3; IC95 20,8 % a 93,8 %) | 85,4 % (35 de 41; IC95 71,6 % a 93,1 %) |
| Copahue | 0,0 % (0 de 44; IC95 0,0 % a 8,0 %) | s/d (n 0) | 88,6 % (39 de 44; IC95 76,0 % a 95,0 %) |
| PuyehueCordonCaulle | 64,7 % (11 de 17; IC95 41,3 % a 82,7 %) | 100,0 % (11 de 11; IC95 74,1 % a 100,0 %) | 83,3 % (5 de 6; IC95 43,6 % a 97,0 %) |
| Chaiten | 44,4 % (12 de 27; IC95 27,6 % a 62,7 %) | 100,0 % (12 de 12; IC95 75,8 % a 100,0 %) | 80,0 % (12 de 15; IC95 54,8 % a 93,0 %) |

### Lo que implica para las bandas (sin cambiarlas)

1. **MIROVA repite entre pasadas vecinas de la misma noche en 56,9 %** de los casos (VIIRS 375, línea base, n 2484 pares), contra una tasa base de alerta de 24,6 % por pasada listada. Físicamente es esperable que no sea 100 %: un foco sub-píxel débil cae distinto en la grilla de cada órbita, cambia el ángulo de visión y la nube fina entra y sale. Pero esa inconsistencia no entra al denominador de la banda: el negativo limpio del banco exige que MIROVA no haya alertado esa noche en ese sensor, así que contra pasadas vecinas de la misma noche MIROVA da 0 % de falsas por construcción.
2. **El análogo que sí se compara con la banda** es MIROVA contra otro de sus propios instrumentos o contra su noche anterior. En noches negativas de V375, MIROVA alerta en 0,2 % de las pasadas V750 (n 3168); en noches negativas de V750 alerta en 19,4 % de las pasadas V375 (n 4813); y la noche siguiente a una noche V375 negativa alerta en 10,5 % de las pasadas V375 listadas (n 2858). Por estrato (C3b): focal 27,8 %, nevado 5,2 %. Estos números no son tasas de error de MIROVA (la actividad cambia de verdad de una noche a otra y cada sensor tiene otro umbral de detección), pero dan el orden de magnitud de cuánto se contradice MIROVA consigo mismo con la misma aritmética de la banda.
3. Con la definición C3b, MIROVA contra su noche anterior da focal 27,8 % (banda 10,0 %) y nevado 5,2 % (banda 15,0 %): no quedan ambos dentro. Es un INDICIO, no la prueba que pide la spec §2: C3b mezcla la inconsistencia de MIROVA con cambios reales de actividad de una noche a otra, que en los focales activos (Láscar, Isluga, Lastarria, Puyehue-Cordón Caulle) son frecuentes, y no hay forma de separarlos con estos datos. Decidir si reabre las bandas es de Nicolás. C2b no es comparable directo porque V375 y V750 tienen sensibilidades distintas al mismo foco.
4. **¿Explica la inconsistencia de MIROVA nuestra sobre-publicación?** Hoy 28,5 % de nuestros negativos limpios V375 están a una noche de una alerta de MIROVA en el mismo volcán. Publicamos en 85,7 % de los adyacentes y en 87,7 % de los no adyacentes (n 211). Lejos de toda alerta la tasa sigue muy por encima de la banda: la sobre-publicación no es un efecto de la actividad intermitente que MIROVA pierde. 

## 5. Otros valores

- **Posición**: no encontré medición de posición del NRT posterior a #535 (busqué en `experiments/_s141*` y `_s142*`; las distancias del probe S141 son contra el OSF 2025 y las de `_s142_ndc` son de Nevados de Chillán). No se midió aquí: el CSV de MIROVA trae sólo un radio sin acimut (A93) y comparar radios da una cota inferior, no una distancia. SOSPECHA pendiente.
- **Latencia del despacho del cron NRT** (`experiments/_s141_cron/atraso_despacho.json`, generado 2026-09-15T11:21:23+00:00): 57 corridas schedule, atraso de creación mediano 56 min y máximo 120 min; 4,75 corridas por día contra 12 franjas declaradas. Es el atraso de GitHub en despachar, no la latencia satélite a dashboard (que suma LANCE ~3 h y el proceso), que no está medida.
- **Auto-audit semanal** (2026-07-16 a 2026-09-14), recall por noche en el dashboard: VIIRS375 96,6 % de 177; VIIRS750 87,2 % de 39; MODIS 33,3 % de 3. Usa otra unidad (noche sensor, criterio eje 2 S119) y ventana móvil que mezcla regímenes.

## 6. Caveats

- **15 noches.** El tramo posterior a #571 tiene 38 noches con alerta V375 focales y 16 nevadas; ningún volcán llega a n ≥ 30 pares de magnitud en VIIRS 375 hoy (ninguno), así que el veredicto de magnitud por volcán sólo se puede dar sobre la ventana larga, que mezcla el régimen previo a #535.
- **La ventana larga mezcla regímenes** (máscara de nube hasta #535, piso VRP hasta #571). Para la magnitud el efecto esperado es chico (el piso quitaba cúmulos de < 0,02 MW, que casi no parean con alertas), pero no está medido pasada a pasada: comparar la columna antes de #535 con la de hoy por volcán.
- **sin_info**: las pasadas nuestras sin fila CONS a ±2 min quedan fuera de todo denominador (276 de 698 pasadas V375 del tramo hoy, 39,5 %). La consistencia de MIROVA sólo usa pasadas que MIROVA listó; si MIROVA deja de listar pasadas de forma no aleatoria, C1 a C3 se sesgan (SOSPECHA).
- **Noche = fecha UTC**, igual que el banco. Las pasadas nocturnas chilenas caen casi todas entre 00 y 10 UTC, pero una pasada de las 23 UTC quedaría en otra noche (no medido).
- **La línea base congelada** (`banco.json`) usó otra referencia (commits de Mirova-v1 del 2026-09-14); sus conteos por estrato se suman aquí desde `por_volcan` redondeando tasa × n.
- **Detección como criterio**: la spec lo define relativo a la línea base y se evalúa en A/B sobre las mismas noches; aquí sólo se puede decir cuántas noches se pierden hoy.
