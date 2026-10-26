# Placebos de D-44 y de ganancia sobre producción (generado por placebos_produccion.py)

Commit `f391376a064575139a38ff4cb3fc15151aa26485`; referencia hasta 2026-10-25; regla de mínimas SN. Sha256 de la referencia en el JSON.

## Sustrato e identidad

| ventana | sensor | canal | pasadas MIROVA | prod observa / no observa | alertas <1 MW (pub.) | negativos (pub.) | identidad: P2 disc., P1b |
|---|---|---|---|---|---|---|---|
| T 2026-04-01..2026-06-12 | VIIRS375 | tabla | 1905 | 1902 / 3 | 350 (338) | 1042 (53) | 0, 0/0 |
| T 2026-04-01..2026-06-12 | VIIRS750 | tabla | 2105 | 2099 / 6 | 75 (49) | 1829 (20) | 0, 0/0 |
| T 2026-03-01..2026-06-12 | MODIS | tabla | 2407 | 2366 / 41 | 26 (21) | 2254 (20) | 0, 0/0 |
| O 2026-06-13..2026-10-25 | VIIRS375 | union | 4232 | 4074 / 12 | 602 (573) | 2444 (88) | 0, 0/0 |
| O 2026-06-13..2026-10-25 | VIIRS750 | union | 4068 | 3910 / 24 | 99 (60) | 3558 (35) | 0, 0/0 |
| O 2026-06-13..2026-10-25 | MODIS | union | 3031 | 2864 / 58 | 16 (11) | 2813 (19) | 0, 0/0 |
| O 2026-06-13..2026-10-25 | VIIRS375 | tabla | 4027 | 3881 / 12 | 465 (445) | 2497 (106) | 0, 0/0 |
| O 2026-06-13..2026-10-25 | VIIRS750 | tabla | 4052 | 3897 / 24 | 99 (60) | 3558 (35) | 0, 0/0 |
| O 2026-06-13..2026-10-25 | MODIS | tabla | 3030 | 2863 / 58 | 16 (11) | 2813 (19) | 0, 0/0 |

## P2: placebo simétrico (c), tasa de falsos (debe quedar bajo 5 % por cola)

BLOQUEA (D-45: el neto va en contra del brazo sin llegar a significancia) no es un falso de la prueba: sin ningún efecto sale cerca de la mitad de las veces que el neto no es cero. Un BLOQUEA no es evidencia contra un brazo (verificador de S163).

| ventana | sensor | canal | fracción | GANA | PIERDE | BLOQUEA | SIN SUSTRATO | B mediana |
|---|---|---|---|---|---|---|---|---|
| T | VIIRS375 | tabla | 0.50 | 17/400 (4.2 %; IC95 2.7 a 6.7) | 9/400 (2.2 %; IC95 1.2 a 4.2) | 146/400 (36.5 %; IC95 31.9 a 41.3) | 0/400 (0.0 %; IC95 0.0 a 0.9) | 20 |
| T | VIIRS375 | tabla | 1.00 | 20/400 (5.0 %; IC95 3.3 a 7.6) | 21/400 (5.2 %; IC95 3.5 a 7.9) | 154/400 (38.5 %; IC95 33.9 a 43.4) | 0/400 (0.0 %; IC95 0.0 a 0.9) | 40 |
| T | VIIRS750 | tabla | 0.50 | 2/400 (0.5 %; IC95 0.1 a 1.8) | 5/400 (1.2 %; IC95 0.5 a 2.9) | 141/400 (35.2 %; IC95 30.7 a 40.1) | 0/400 (0.0 %; IC95 0.0 a 0.9) | 10 |
| T | VIIRS750 | tabla | 1.00 | 11/400 (2.8 %; IC95 1.5 a 4.9) | 9/400 (2.2 %; IC95 1.2 a 4.2) | 157/400 (39.2 %; IC95 34.6 a 44.1) | 0/400 (0.0 %; IC95 0.0 a 0.9) | 20 |
| T | MODIS | tabla | 0.50 | 9/400 (2.2 %; IC95 1.2 a 4.2) | 13/400 (3.2 %; IC95 1.9 a 5.5) | 149/400 (37.2 %; IC95 32.6 a 42.1) | 0/400 (0.0 %; IC95 0.0 a 0.9) | 8 |
| T | MODIS | tabla | 1.00 | 18/400 (4.5 %; IC95 2.9 a 7.0) | 11/400 (2.8 %; IC95 1.5 a 4.9) | 177/400 (44.2 %; IC95 39.5 a 49.1) | 0/400 (0.0 %; IC95 0.0 a 0.9) | 17 |
| O | VIIRS375 | union | 0.50 | 20/400 (5.0 %; IC95 3.3 a 7.6) | 13/400 (3.2 %; IC95 1.9 a 5.5) | 173/400 (43.2 %; IC95 38.5 a 48.1) | 0/400 (0.0 %; IC95 0.0 a 0.9) | 42 |
| O | VIIRS375 | union | 1.00 | 22/400 (5.5 %; IC95 3.7 a 8.2) | 15/400 (3.8 %; IC95 2.3 a 6.1) | 183/400 (45.8 %; IC95 40.9 a 50.6) | 0/400 (0.0 %; IC95 0.0 a 0.9) | 83 |
| O | VIIRS750 | union | 0.50 | 24/400 (6.0 %; IC95 4.1 a 8.8) | 17/400 (4.2 %; IC95 2.7 a 6.7) | 139/400 (34.8 %; IC95 30.2 a 39.5) | 0/400 (0.0 %; IC95 0.0 a 0.9) | 18 |
| O | VIIRS750 | union | 1.00 | 19/400 (4.8 %; IC95 3.1 a 7.3) | 16/400 (4.0 %; IC95 2.5 a 6.4) | 179/400 (44.8 %; IC95 40.0 a 49.6) | 0/400 (0.0 %; IC95 0.0 a 0.9) | 37 |
| O | MODIS | union | 0.50 | 6/400 (1.5 %; IC95 0.7 a 3.2) | 5/400 (1.2 %; IC95 0.5 a 2.9) | 192/400 (48.0 %; IC95 43.1 a 52.9) | 0/400 (0.0 %; IC95 0.0 a 0.9) | 9 |
| O | MODIS | union | 1.00 | 26/400 (6.5 %; IC95 4.5 a 9.3) | 17/400 (4.2 %; IC95 2.7 a 6.7) | 143/400 (35.8 %; IC95 31.2 a 40.6) | 0/400 (0.0 %; IC95 0.0 a 0.9) | 18 |
| O | VIIRS375 | tabla | 0.50 | 18/400 (4.5 %; IC95 2.9 a 7.0) | 14/400 (3.5 %; IC95 2.1 a 5.8) | 162/400 (40.5 %; IC95 35.8 a 45.4) | 0/400 (0.0 %; IC95 0.0 a 0.9) | 41 |
| O | VIIRS375 | tabla | 1.00 | 17/400 (4.2 %; IC95 2.7 a 6.7) | 9/400 (2.2 %; IC95 1.2 a 4.2) | 163/400 (40.8 %; IC95 36.0 a 45.6) | 0/400 (0.0 %; IC95 0.0 a 0.9) | 82 |
| O | VIIRS750 | tabla | 0.50 | 24/400 (6.0 %; IC95 4.1 a 8.8) | 17/400 (4.2 %; IC95 2.7 a 6.7) | 139/400 (34.8 %; IC95 30.2 a 39.5) | 0/400 (0.0 %; IC95 0.0 a 0.9) | 18 |
| O | VIIRS750 | tabla | 1.00 | 19/400 (4.8 %; IC95 3.1 a 7.3) | 16/400 (4.0 %; IC95 2.5 a 6.4) | 179/400 (44.8 %; IC95 40.0 a 49.6) | 0/400 (0.0 %; IC95 0.0 a 0.9) | 37 |
| O | MODIS | tabla | 0.50 | 6/400 (1.5 %; IC95 0.7 a 3.2) | 5/400 (1.2 %; IC95 0.5 a 2.9) | 192/400 (48.0 %; IC95 43.1 a 52.9) | 0/400 (0.0 %; IC95 0.0 a 0.9) | 9 |
| O | MODIS | tabla | 1.00 | 26/400 (6.5 %; IC95 4.5 a 9.3) | 17/400 (4.2 %; IC95 2.7 a 6.7) | 143/400 (35.8 %; IC95 31.2 a 40.6) | 0/400 (0.0 %; IC95 0.0 a 0.9) | 18 |

## P2: poder (a debe dar GANA, b debe dar PIERDE)

| ventana | sensor | canal | fracción | a: GANA | a: SIN SUSTRATO | b: PIERDE | b: SIN SUSTRATO |
|---|---|---|---|---|---|---|---|
| T | VIIRS375 | tabla | 0.10 | 37/40 (92.5 %; IC95 80.1 a 97.4) | 3/40 (7.5 %; IC95 2.6 a 19.9) | 40/40 (100.0 %; IC95 91.2 a 100.0) | 0/40 (0.0 %; IC95 0.0 a 8.8) |
| T | VIIRS375 | tabla | 0.25 | 40/40 (100.0 %; IC95 91.2 a 100.0) | 0/40 (0.0 %; IC95 0.0 a 8.8) | 40/40 (100.0 %; IC95 91.2 a 100.0) | 0/40 (0.0 %; IC95 0.0 a 8.8) |
| T | VIIRS375 | tabla | 0.50 | 40/40 (100.0 %; IC95 91.2 a 100.0) | 0/40 (0.0 %; IC95 0.0 a 8.8) | 40/40 (100.0 %; IC95 91.2 a 100.0) | 0/40 (0.0 %; IC95 0.0 a 8.8) |
| T | VIIRS750 | tabla | 0.10 | 0/40 (0.0 %; IC95 0.0 a 8.8) | 40/40 (100.0 %; IC95 91.2 a 100.0) | 39/40 (97.5 %; IC95 87.1 a 99.6) | 1/40 (2.5 %; IC95 0.4 a 12.9) |
| T | VIIRS750 | tabla | 0.25 | 38/40 (95.0 %; IC95 83.5 a 98.6) | 2/40 (5.0 %; IC95 1.4 a 16.5) | 40/40 (100.0 %; IC95 91.2 a 100.0) | 0/40 (0.0 %; IC95 0.0 a 8.8) |
| T | VIIRS750 | tabla | 0.50 | 40/40 (100.0 %; IC95 91.2 a 100.0) | 0/40 (0.0 %; IC95 0.0 a 8.8) | 40/40 (100.0 %; IC95 91.2 a 100.0) | 0/40 (0.0 %; IC95 0.0 a 8.8) |
| T | MODIS | tabla | 0.10 | 0/40 (0.0 %; IC95 0.0 a 8.8) | 40/40 (100.0 %; IC95 91.2 a 100.0) | 0/40 (0.0 %; IC95 0.0 a 8.8) | 40/40 (100.0 %; IC95 91.2 a 100.0) |
| T | MODIS | tabla | 0.25 | 39/40 (97.5 %; IC95 87.1 a 99.6) | 1/40 (2.5 %; IC95 0.4 a 12.9) | 36/40 (90.0 %; IC95 77.0 a 96.0) | 4/40 (10.0 %; IC95 4.0 a 23.1) |
| T | MODIS | tabla | 0.50 | 40/40 (100.0 %; IC95 91.2 a 100.0) | 0/40 (0.0 %; IC95 0.0 a 8.8) | 40/40 (100.0 %; IC95 91.2 a 100.0) | 0/40 (0.0 %; IC95 0.0 a 8.8) |
| O | VIIRS375 | union | 0.10 | 40/40 (100.0 %; IC95 91.2 a 100.0) | 0/40 (0.0 %; IC95 0.0 a 8.8) | 40/40 (100.0 %; IC95 91.2 a 100.0) | 0/40 (0.0 %; IC95 0.0 a 8.8) |
| O | VIIRS375 | union | 0.25 | 40/40 (100.0 %; IC95 91.2 a 100.0) | 0/40 (0.0 %; IC95 0.0 a 8.8) | 40/40 (100.0 %; IC95 91.2 a 100.0) | 0/40 (0.0 %; IC95 0.0 a 8.8) |
| O | VIIRS375 | union | 0.50 | 40/40 (100.0 %; IC95 91.2 a 100.0) | 0/40 (0.0 %; IC95 0.0 a 8.8) | 40/40 (100.0 %; IC95 91.2 a 100.0) | 0/40 (0.0 %; IC95 0.0 a 8.8) |
| O | VIIRS750 | union | 0.10 | 0/40 (0.0 %; IC95 0.0 a 8.8) | 40/40 (100.0 %; IC95 91.2 a 100.0) | 40/40 (100.0 %; IC95 91.2 a 100.0) | 0/40 (0.0 %; IC95 0.0 a 8.8) |
| O | VIIRS750 | union | 0.25 | 40/40 (100.0 %; IC95 91.2 a 100.0) | 0/40 (0.0 %; IC95 0.0 a 8.8) | 40/40 (100.0 %; IC95 91.2 a 100.0) | 0/40 (0.0 %; IC95 0.0 a 8.8) |
| O | VIIRS750 | union | 0.50 | 40/40 (100.0 %; IC95 91.2 a 100.0) | 0/40 (0.0 %; IC95 0.0 a 8.8) | 40/40 (100.0 %; IC95 91.2 a 100.0) | 0/40 (0.0 %; IC95 0.0 a 8.8) |
| O | MODIS | union | 0.10 | 0/40 (0.0 %; IC95 0.0 a 8.8) | 40/40 (100.0 %; IC95 91.2 a 100.0) | 0/40 (0.0 %; IC95 0.0 a 8.8) | 40/40 (100.0 %; IC95 91.2 a 100.0) |
| O | MODIS | union | 0.25 | 40/40 (100.0 %; IC95 91.2 a 100.0) | 0/40 (0.0 %; IC95 0.0 a 8.8) | 0/40 (0.0 %; IC95 0.0 a 8.8) | 40/40 (100.0 %; IC95 91.2 a 100.0) |
| O | MODIS | union | 0.50 | 40/40 (100.0 %; IC95 91.2 a 100.0) | 0/40 (0.0 %; IC95 0.0 a 8.8) | 40/40 (100.0 %; IC95 91.2 a 100.0) | 0/40 (0.0 %; IC95 0.0 a 8.8) |
| O | VIIRS375 | tabla | 0.10 | 40/40 (100.0 %; IC95 91.2 a 100.0) | 0/40 (0.0 %; IC95 0.0 a 8.8) | 40/40 (100.0 %; IC95 91.2 a 100.0) | 0/40 (0.0 %; IC95 0.0 a 8.8) |
| O | VIIRS375 | tabla | 0.25 | 40/40 (100.0 %; IC95 91.2 a 100.0) | 0/40 (0.0 %; IC95 0.0 a 8.8) | 40/40 (100.0 %; IC95 91.2 a 100.0) | 0/40 (0.0 %; IC95 0.0 a 8.8) |
| O | VIIRS375 | tabla | 0.50 | 40/40 (100.0 %; IC95 91.2 a 100.0) | 0/40 (0.0 %; IC95 0.0 a 8.8) | 40/40 (100.0 %; IC95 91.2 a 100.0) | 0/40 (0.0 %; IC95 0.0 a 8.8) |
| O | VIIRS750 | tabla | 0.10 | 0/40 (0.0 %; IC95 0.0 a 8.8) | 40/40 (100.0 %; IC95 91.2 a 100.0) | 40/40 (100.0 %; IC95 91.2 a 100.0) | 0/40 (0.0 %; IC95 0.0 a 8.8) |
| O | VIIRS750 | tabla | 0.25 | 40/40 (100.0 %; IC95 91.2 a 100.0) | 0/40 (0.0 %; IC95 0.0 a 8.8) | 40/40 (100.0 %; IC95 91.2 a 100.0) | 0/40 (0.0 %; IC95 0.0 a 8.8) |
| O | VIIRS750 | tabla | 0.50 | 40/40 (100.0 %; IC95 91.2 a 100.0) | 0/40 (0.0 %; IC95 0.0 a 8.8) | 40/40 (100.0 %; IC95 91.2 a 100.0) | 0/40 (0.0 %; IC95 0.0 a 8.8) |
| O | MODIS | tabla | 0.10 | 0/40 (0.0 %; IC95 0.0 a 8.8) | 40/40 (100.0 %; IC95 91.2 a 100.0) | 0/40 (0.0 %; IC95 0.0 a 8.8) | 40/40 (100.0 %; IC95 91.2 a 100.0) |
| O | MODIS | tabla | 0.25 | 40/40 (100.0 %; IC95 91.2 a 100.0) | 0/40 (0.0 %; IC95 0.0 a 8.8) | 0/40 (0.0 %; IC95 0.0 a 8.8) | 40/40 (100.0 %; IC95 91.2 a 100.0) |
| O | MODIS | tabla | 0.50 | 40/40 (100.0 %; IC95 91.2 a 100.0) | 0/40 (0.0 %; IC95 0.0 a 8.8) | 40/40 (100.0 %; IC95 91.2 a 100.0) | 0/40 (0.0 %; IC95 0.0 a 8.8) |

## P2: placebo simétrico por estrato (fracción 1,0)

| ventana | sensor | canal | eje | estrato | GANA | PIERDE | SIN SUSTRATO |
|---|---|---|---|---|---|---|---|
| T | VIIRS375 | tabla | cenit | sin_cenit | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| T | VIIRS375 | tabla | cenit | z00-10 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| T | VIIRS375 | tabla | cenit | z10-20 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| T | VIIRS375 | tabla | cenit | z20-30 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| T | VIIRS375 | tabla | cenit | z30-40 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| T | VIIRS375 | tabla | cenit | z40-50 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| T | VIIRS375 | tabla | cenit | z50-60 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| T | VIIRS375 | tabla | cenit | z60-70 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| T | VIIRS375 | tabla | cenit | z70-80 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| T | VIIRS375 | tabla | regimen | antes_535 | 3/200 (1.5 %; IC95 0.5 a 4.3) | 5/200 (2.5 %; IC95 1.1 a 5.7) | 0/200 (0.0 %; IC95 0.0 a 1.9) |
| T | VIIRS750 | tabla | cenit | sin_cenit | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| T | VIIRS750 | tabla | cenit | z00-10 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| T | VIIRS750 | tabla | cenit | z10-20 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| T | VIIRS750 | tabla | cenit | z20-30 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| T | VIIRS750 | tabla | cenit | z30-40 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| T | VIIRS750 | tabla | cenit | z40-50 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| T | VIIRS750 | tabla | cenit | z50-60 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| T | VIIRS750 | tabla | cenit | z60-70 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| T | VIIRS750 | tabla | cenit | z70-80 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| T | VIIRS750 | tabla | regimen | antes_535 | 4/200 (2.0 %; IC95 0.8 a 5.0) | 4/200 (2.0 %; IC95 0.8 a 5.0) | 0/200 (0.0 %; IC95 0.0 a 1.9) |
| T | MODIS | tabla | cenit | sin_cenit | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| T | MODIS | tabla | cenit | z00-10 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| T | MODIS | tabla | cenit | z10-20 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| T | MODIS | tabla | cenit | z20-30 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| T | MODIS | tabla | cenit | z30-40 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| T | MODIS | tabla | cenit | z40-50 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| T | MODIS | tabla | cenit | z50-60 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| T | MODIS | tabla | cenit | z60-70 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| T | MODIS | tabla | regimen | antes_535 | 7/200 (3.5 %; IC95 1.7 a 7.0) | 5/200 (2.5 %; IC95 1.1 a 5.7) | 0/200 (0.0 %; IC95 0.0 a 1.9) |
| O | VIIRS375 | union | cenit | sin_cenit | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | VIIRS375 | union | cenit | z00-10 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | VIIRS375 | union | cenit | z10-20 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | VIIRS375 | union | cenit | z20-30 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | VIIRS375 | union | cenit | z30-40 | 12/200 (6.0 %; IC95 3.5 a 10.2) | 8/200 (4.0 %; IC95 2.0 a 7.7) | 0/200 (0.0 %; IC95 0.0 a 1.9) |
| O | VIIRS375 | union | cenit | z40-50 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | VIIRS375 | union | cenit | z50-60 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | VIIRS375 | union | cenit | z60-70 | 12/200 (6.0 %; IC95 3.5 a 10.2) | 8/200 (4.0 %; IC95 2.0 a 7.7) | 0/200 (0.0 %; IC95 0.0 a 1.9) |
| O | VIIRS375 | union | cenit | z70-80 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | VIIRS375 | union | regimen | 535_a_K | 5/200 (2.5 %; IC95 1.1 a 5.7) | 6/200 (3.0 %; IC95 1.4 a 6.4) | 0/200 (0.0 %; IC95 0.0 a 1.9) |
| O | VIIRS375 | union | regimen | antes_535 | 13/200 (6.5 %; IC95 3.8 a 10.8) | 10/200 (5.0 %; IC95 2.7 a 9.0) | 0/200 (0.0 %; IC95 0.0 a 1.9) |
| O | VIIRS375 | union | regimen | desde_K | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | VIIRS750 | union | cenit | sin_cenit | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | VIIRS750 | union | cenit | z00-10 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | VIIRS750 | union | cenit | z10-20 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | VIIRS750 | union | cenit | z20-30 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | VIIRS750 | union | cenit | z30-40 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | VIIRS750 | union | cenit | z40-50 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | VIIRS750 | union | cenit | z50-60 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | VIIRS750 | union | cenit | z60-70 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | VIIRS750 | union | cenit | z70-80 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | VIIRS750 | union | regimen | 535_a_K | 7/200 (3.5 %; IC95 1.7 a 7.0) | 5/200 (2.5 %; IC95 1.1 a 5.7) | 0/200 (0.0 %; IC95 0.0 a 1.9) |
| O | VIIRS750 | union | regimen | antes_535 | 4/200 (2.0 %; IC95 0.8 a 5.0) | 8/200 (4.0 %; IC95 2.0 a 7.7) | 0/200 (0.0 %; IC95 0.0 a 1.9) |
| O | VIIRS750 | union | regimen | desde_K | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | MODIS | union | cenit | sin_cenit | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | MODIS | union | cenit | z00-10 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | MODIS | union | cenit | z10-20 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | MODIS | union | cenit | z20-30 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | MODIS | union | cenit | z30-40 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | MODIS | union | cenit | z40-50 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | MODIS | union | cenit | z50-60 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | MODIS | union | cenit | z60-70 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | MODIS | union | regimen | 535_a_K | 4/200 (2.0 %; IC95 0.8 a 5.0) | 4/200 (2.0 %; IC95 0.8 a 5.0) | 0/200 (0.0 %; IC95 0.0 a 1.9) |
| O | MODIS | union | regimen | antes_535 | 4/200 (2.0 %; IC95 0.8 a 5.0) | 4/200 (2.0 %; IC95 0.8 a 5.0) | 0/200 (0.0 %; IC95 0.0 a 1.9) |
| O | MODIS | union | regimen | desde_K | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | VIIRS375 | tabla | cenit | sin_cenit | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | VIIRS375 | tabla | cenit | z00-10 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | VIIRS375 | tabla | cenit | z10-20 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | VIIRS375 | tabla | cenit | z20-30 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | VIIRS375 | tabla | cenit | z30-40 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | VIIRS375 | tabla | cenit | z40-50 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | VIIRS375 | tabla | cenit | z50-60 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | VIIRS375 | tabla | cenit | z60-70 | 6/200 (3.0 %; IC95 1.4 a 6.4) | 3/200 (1.5 %; IC95 0.5 a 4.3) | 0/200 (0.0 %; IC95 0.0 a 1.9) |
| O | VIIRS375 | tabla | cenit | z70-80 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | VIIRS375 | tabla | regimen | 535_a_K | 6/200 (3.0 %; IC95 1.4 a 6.4) | 3/200 (1.5 %; IC95 0.5 a 4.3) | 0/200 (0.0 %; IC95 0.0 a 1.9) |
| O | VIIRS375 | tabla | regimen | antes_535 | 12/200 (6.0 %; IC95 3.5 a 10.2) | 5/200 (2.5 %; IC95 1.1 a 5.7) | 0/200 (0.0 %; IC95 0.0 a 1.9) |
| O | VIIRS750 | tabla | cenit | sin_cenit | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | VIIRS750 | tabla | cenit | z00-10 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | VIIRS750 | tabla | cenit | z10-20 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | VIIRS750 | tabla | cenit | z20-30 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | VIIRS750 | tabla | cenit | z30-40 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | VIIRS750 | tabla | cenit | z40-50 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | VIIRS750 | tabla | cenit | z50-60 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | VIIRS750 | tabla | cenit | z60-70 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | VIIRS750 | tabla | cenit | z70-80 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | VIIRS750 | tabla | regimen | 535_a_K | 7/200 (3.5 %; IC95 1.7 a 7.0) | 5/200 (2.5 %; IC95 1.1 a 5.7) | 0/200 (0.0 %; IC95 0.0 a 1.9) |
| O | VIIRS750 | tabla | regimen | antes_535 | 4/200 (2.0 %; IC95 0.8 a 5.0) | 8/200 (4.0 %; IC95 2.0 a 7.7) | 0/200 (0.0 %; IC95 0.0 a 1.9) |
| O | MODIS | tabla | cenit | sin_cenit | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | MODIS | tabla | cenit | z00-10 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | MODIS | tabla | cenit | z10-20 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | MODIS | tabla | cenit | z20-30 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | MODIS | tabla | cenit | z30-40 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | MODIS | tabla | cenit | z40-50 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | MODIS | tabla | cenit | z50-60 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | MODIS | tabla | cenit | z60-70 | 0/200 (0.0 %; IC95 0.0 a 1.9) | 0/200 (0.0 %; IC95 0.0 a 1.9) | 200/200 (100.0 %; IC95 98.1 a 100.0) |
| O | MODIS | tabla | regimen | 535_a_K | 4/200 (2.0 %; IC95 0.8 a 5.0) | 4/200 (2.0 %; IC95 0.8 a 5.0) | 0/200 (0.0 %; IC95 0.0 a 1.9) |
| O | MODIS | tabla | regimen | antes_535 | 4/200 (2.0 %; IC95 0.8 a 5.0) | 4/200 (2.0 %; IC95 0.8 a 5.0) | 0/200 (0.0 %; IC95 0.0 a 1.9) |

## M: identidad y placebo de ganancia (con comparador no debe quedar MEJORA)

| ventana | sensor | canal | estrato | pares | noches | identidad | K/MIROVA | falsos MEJORA/EMPEORA (calib. sobre K×1,2) | falsos MEJORA d′ | K×1,2 sin / con | K×0,8 sin / con |
|---|---|---|---|---|---|---|---|---|---|---|---|
| T | VIIRS375 | tabla | VIIRS375 | 376 | 283 | NEUTRO | 0.635 | 0.040 / 0.020 | 0.000 | MEJORA / NEUTRO | EMPEORA / EMPEORA |
| T | VIIRS375 | tabla | z00-10 | 45 | 45 | NEUTRO | 0.822 | 0.010 / 0.030 | 0.000 | MEJORA / NEUTRO | EMPEORA / EMPEORA |
| T | VIIRS375 | tabla | z10-20 | 56 | 56 | NEUTRO | 0.779 | 0.025 / 0.020 | 0.000 | MEJORA / NEUTRO | EMPEORA / EMPEORA |
| T | VIIRS375 | tabla | z20-30 | 49 | 49 | NEUTRO | 0.673 | 0.020 / 0.030 | 0.000 | MEJORA / NEUTRO | EMPEORA / EMPEORA |
| T | VIIRS375 | tabla | z30-40 | 54 | 52 | NEUTRO | 0.585 | 0.015 / 0.030 | 0.000 | MEJORA / NEUTRO | EMPEORA / EMPEORA |
| T | VIIRS375 | tabla | z40-50 | 71 | 65 | NEUTRO | 0.496 | 0.010 / 0.030 | 0.000 | MEJORA / NEUTRO | EMPEORA / EMPEORA |
| T | VIIRS375 | tabla | z50-60 | 70 | 67 | NEUTRO | 0.587 | 0.025 / 0.040 | 0.000 | MEJORA / NEUTRO | EMPEORA / EMPEORA |
| T | VIIRS375 | tabla | z60-70 | 31 | 31 | NEUTRO | 0.679 | 0.020 / 0.035 | 0.000 | MEJORA / NEUTRO | EMPEORA / EMPEORA |
| T | VIIRS750 | tabla | VIIRS750 | 91 | 76 | NEUTRO | 0.534 | 0.015 / 0.025 | 0.000 | MEJORA / NEUTRO | EMPEORA / EMPEORA |
| T | VIIRS750 | tabla | z00-10 | 12 | 12 | NEUTRO | 0.700 | 0.025 / 0.020 | 0.000 | MEJORA / NEUTRO | EMPEORA / EMPEORA |
| T | VIIRS750 | tabla | z10-20 | 20 | 20 | NEUTRO | 0.686 | 0.030 / 0.025 | 0.000 | MEJORA / NEUTRO | EMPEORA / EMPEORA |
| T | VIIRS750 | tabla | z20-30 | 17 | 17 | NEUTRO | 0.553 | 0.010 / 0.025 | 0.000 | NEUTRO / NEUTRO | EMPEORA / EMPEORA |
| T | VIIRS750 | tabla | z30-40 | 15 | 15 | NEUTRO | 0.396 | 0.020 / 0.025 | 0.000 | MEJORA / NEUTRO | EMPEORA / EMPEORA |
| T | VIIRS750 | tabla | z40-50 | 22 | 17 | NEUTRO | 0.551 | 0.010 / 0.030 | 0.000 | NEUTRO / NEUTRO | EMPEORA / EMPEORA |
| T | VIIRS750 | tabla | z50-60 | 5 | 5 | NEUTRO | 0.431 | 0.045 / 0.020 | 0.000 | NEUTRO / NEUTRO | EMPEORA / EMPEORA |
| T | MODIS | tabla | MODIS | 60 | 50 | NEUTRO | 0.496 | 0.025 / 0.025 | 0.000 | NEUTRO / NEUTRO | EMPEORA / EMPEORA |
| T | MODIS | tabla | z00-10 | 9 | 9 | NEUTRO | 0.571 | 0.015 / 0.015 | 0.000 | NEUTRO / NEUTRO | EMPEORA / EMPEORA |
| T | MODIS | tabla | z10-20 | 20 | 18 | NEUTRO | 0.634 | 0.030 / 0.035 | 0.000 | NEUTRO / NEUTRO | EMPEORA / EMPEORA |
| T | MODIS | tabla | z20-30 | 14 | 13 | NEUTRO | 0.427 | 0.005 / 0.030 | 0.000 | NEUTRO / NEUTRO | EMPEORA / EMPEORA |
| T | MODIS | tabla | z30-40 | 11 | 10 | NEUTRO | 0.393 | 0.030 / 0.050 | 0.000 | NEUTRO / NEUTRO | EMPEORA / EMPEORA |
| T | MODIS | tabla | z40-50 | 6 | 6 | NEUTRO | 0.224 | 0.020 / 0.010 | 0.000 | NEUTRO / NEUTRO | EMPEORA / EMPEORA |
| O | VIIRS375 | union | VIIRS375 | 614 | 366 | NEUTRO | 0.648 | 0.030 / 0.020 | 0.000 | MEJORA / NEUTRO | EMPEORA / EMPEORA |
| O | VIIRS375 | union | z00-10 | 97 | 97 | NEUTRO | 0.809 | 0.005 / 0.015 | 0.000 | MEJORA / NEUTRO | EMPEORA / EMPEORA |
| O | VIIRS375 | union | z10-20 | 83 | 83 | NEUTRO | 0.727 | 0.020 / 0.025 | 0.000 | MEJORA / NEUTRO | EMPEORA / EMPEORA |
| O | VIIRS375 | union | z20-30 | 91 | 81 | NEUTRO | 0.637 | 0.025 / 0.035 | 0.000 | MEJORA / NEUTRO | EMPEORA / EMPEORA |
| O | VIIRS375 | union | z30-40 | 92 | 88 | NEUTRO | 0.629 | 0.020 / 0.025 | 0.000 | MEJORA / NEUTRO | EMPEORA / EMPEORA |
| O | VIIRS375 | union | z40-50 | 98 | 91 | NEUTRO | 0.553 | 0.025 / 0.020 | 0.000 | MEJORA / NEUTRO | EMPEORA / EMPEORA |
| O | VIIRS375 | union | z50-60 | 108 | 99 | NEUTRO | 0.552 | 0.020 / 0.040 | 0.000 | MEJORA / NEUTRO | EMPEORA / EMPEORA |
| O | VIIRS375 | union | z60-70 | 45 | 42 | NEUTRO | 0.401 | 0.030 / 0.025 | 0.000 | MEJORA / NEUTRO | EMPEORA / EMPEORA |
| O | VIIRS750 | union | VIIRS750 | 96 | 73 | NEUTRO | 0.451 | 0.020 / 0.015 | 0.000 | MEJORA / NEUTRO | EMPEORA / EMPEORA |
| O | VIIRS750 | union | z00-10 | 19 | 19 | NEUTRO | 0.655 | 0.020 / 0.020 | 0.000 | MEJORA / NEUTRO | EMPEORA / EMPEORA |
| O | VIIRS750 | union | z10-20 | 22 | 22 | NEUTRO | 0.615 | 0.015 / 0.030 | 0.000 | NEUTRO / NEUTRO | EMPEORA / EMPEORA |
| O | VIIRS750 | union | z20-30 | 16 | 16 | NEUTRO | 0.444 | 0.015 / 0.015 | 0.000 | MEJORA / NEUTRO | EMPEORA / EMPEORA |
| O | VIIRS750 | union | z30-40 | 13 | 13 | NEUTRO | 0.310 | 0.015 / 0.030 | 0.000 | MEJORA / NEUTRO | EMPEORA / EMPEORA |
| O | VIIRS750 | union | z40-50 | 15 | 14 | NEUTRO | 0.431 | 0.015 / 0.040 | 0.000 | MEJORA / NEUTRO | EMPEORA / EMPEORA |
| O | VIIRS750 | union | z50-60 | 7 | 7 | NEUTRO | 0.297 | 0.060 / 0.070 | 0.000 | INDECIDIBLE / INDECIDIBLE | INDECIDIBLE / INDECIDIBLE |
| O | VIIRS750 | union | z60-70 | 4 | 3 | SIN SUSTRATO | | | | | |
| O | MODIS | union | MODIS | 20 | 18 | NEUTRO | 0.637 | 0.030 / 0.010 | 0.000 | MEJORA / NEUTRO | EMPEORA / EMPEORA |
| O | MODIS | union | z00-10 | 4 | 4 | SIN SUSTRATO | | | | | |
| O | MODIS | union | z10-20 | 9 | 9 | NEUTRO | 0.847 | 0.015 / 0.015 | 0.000 | NEUTRO / NEUTRO | EMPEORA / EMPEORA |
| O | MODIS | union | z20-30 | 3 | 3 | SIN SUSTRATO | | | | | |
| O | MODIS | union | z30-40 | 2 | 2 | SIN SUSTRATO | | | | | |
| O | MODIS | union | z40-50 | 1 | 1 | SIN SUSTRATO | | | | | |
| O | MODIS | union | z50-60 | 1 | 1 | SIN SUSTRATO | | | | | |
| O | VIIRS375 | tabla | VIIRS375 | 473 | 332 | NEUTRO | 0.674 | 0.025 / 0.030 | 0.000 | MEJORA / NEUTRO | EMPEORA / EMPEORA |
| O | VIIRS375 | tabla | z00-10 | 75 | 75 | NEUTRO | 0.823 | 0.015 / 0.025 | 0.000 | MEJORA / NEUTRO | EMPEORA / EMPEORA |
| O | VIIRS375 | tabla | z10-20 | 61 | 61 | NEUTRO | 0.713 | 0.015 / 0.030 | 0.000 | MEJORA / NEUTRO | EMPEORA / EMPEORA |
| O | VIIRS375 | tabla | z20-30 | 69 | 68 | NEUTRO | 0.644 | 0.015 / 0.045 | 0.000 | MEJORA / NEUTRO | EMPEORA / EMPEORA |
| O | VIIRS375 | tabla | z30-40 | 73 | 69 | NEUTRO | 0.635 | 0.010 / 0.020 | 0.000 | MEJORA / NEUTRO | EMPEORA / EMPEORA |
| O | VIIRS375 | tabla | z40-50 | 78 | 72 | NEUTRO | 0.581 | 0.010 / 0.035 | 0.000 | MEJORA / NEUTRO | EMPEORA / EMPEORA |
| O | VIIRS375 | tabla | z50-60 | 82 | 78 | NEUTRO | 0.611 | 0.015 / 0.020 | 0.000 | MEJORA / NEUTRO | EMPEORA / EMPEORA |
| O | VIIRS375 | tabla | z60-70 | 35 | 32 | NEUTRO | 0.451 | 0.010 / 0.025 | 0.000 | MEJORA / NEUTRO | EMPEORA / EMPEORA |
| O | VIIRS750 | tabla | VIIRS750 | 88 | 70 | NEUTRO | 0.434 | 0.020 / 0.015 | 0.000 | MEJORA / NEUTRO | EMPEORA / EMPEORA |
| O | VIIRS750 | tabla | z00-10 | 18 | 18 | NEUTRO | 0.657 | 0.020 / 0.020 | 0.000 | MEJORA / NEUTRO | EMPEORA / EMPEORA |
| O | VIIRS750 | tabla | z10-20 | 20 | 20 | NEUTRO | 0.553 | 0.010 / 0.035 | 0.000 | NEUTRO / NEUTRO | EMPEORA / EMPEORA |
| O | VIIRS750 | tabla | z20-30 | 13 | 13 | NEUTRO | 0.474 | 0.015 / 0.030 | 0.000 | MEJORA / NEUTRO | EMPEORA / EMPEORA |
| O | VIIRS750 | tabla | z30-40 | 13 | 13 | NEUTRO | 0.310 | 0.015 / 0.030 | 0.000 | MEJORA / NEUTRO | EMPEORA / EMPEORA |
| O | VIIRS750 | tabla | z40-50 | 13 | 12 | NEUTRO | 0.385 | 0.010 / 0.025 | 0.000 | MEJORA / NEUTRO | EMPEORA / EMPEORA |
| O | VIIRS750 | tabla | z50-60 | 7 | 7 | NEUTRO | 0.297 | 0.060 / 0.070 | 0.000 | INDECIDIBLE / INDECIDIBLE | INDECIDIBLE / INDECIDIBLE |
| O | VIIRS750 | tabla | z60-70 | 4 | 3 | SIN SUSTRATO | | | | | |
| O | MODIS | tabla | MODIS | 20 | 18 | NEUTRO | 0.637 | 0.030 / 0.010 | 0.000 | MEJORA / NEUTRO | EMPEORA / EMPEORA |
| O | MODIS | tabla | z00-10 | 4 | 4 | SIN SUSTRATO | | | | | |
| O | MODIS | tabla | z10-20 | 9 | 9 | NEUTRO | 0.847 | 0.015 / 0.015 | 0.000 | NEUTRO / NEUTRO | EMPEORA / EMPEORA |
| O | MODIS | tabla | z20-30 | 3 | 3 | SIN SUSTRATO | | | | | |
| O | MODIS | tabla | z30-40 | 2 | 2 | SIN SUSTRATO | | | | | |
| O | MODIS | tabla | z40-50 | 1 | 1 | SIN SUSTRATO | | | | | |
| O | MODIS | tabla | z50-60 | 1 | 1 | SIN SUSTRATO | | | | | |

Duración: 5452 s.
