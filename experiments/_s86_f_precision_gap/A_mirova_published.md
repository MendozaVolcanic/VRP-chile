# S86 Frente 2.A — Qué publica MIROVA empíricamente

_Generado por `script_A.py`. CSV CONS=17966 filas, OCR=520 filas._

## 1. Ventana temporal y volumen

- Primera captura: **2026-01-10 19:06:00** UTC
- Última captura: **2026-05-25 06:36:01** UTC
- Duración: **134 días**
- CONS total: 17966 filas — de las cuales **763** son ALERTA_TERMICA
- OCR total: 520 filas — de las cuales **501** son ALERTA_TERMICA_OCR

## 2. Conteos por volcán × sensor (ALERTAs, CONS+OCR)

| Volcán | MODIS | VIIRS | VIIRS375 | VIIRS750 | TOTAL |
|---|---:|---:|---:|---:|---:|
| Lascar | 106 | 149 | 242 | 0 | 497 |
| PuyehueCordonCaulle | 0 | 22 | 155 | 0 | 177 |
| Lastarria | 0 | 0 | 174 | 0 | 174 |
| Isluga | 0 | 17 | 135 | 0 | 152 |
| Tupungatito | 0 | 9 | 100 | 0 | 109 |
| PlanchonPeteroa | 0 | 2 | 90 | 0 | 92 |
| Chaiten | 0 | 1 | 32 | 0 | 33 |
| Villarrica | 0 | 0 | 16 | 0 | 16 |
| NevadosDeChillan | 2 | 1 | 5 | 0 | 8 |
| Llaima | 1 | 0 | 3 | 0 | 4 |
| Copahue | 1 | 0 | 1 | 0 | 2 |

## 3. Distribución VRP_MW publicada por sensor

¿Hay un corte inferior? Si p05 ≫ 0.05 MW, MIROVA no publica anomalías débiles.

| Sensor | N | min | p05 | p25 | p50 | p75 | p95 | max | mean |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| MODIS | 110 | 0.190 | 0.303 | 0.992 | 1.325 | 2.000 | 3.000 | 15.00 | 1.619 |
| VIIRS | 201 | 0.150 | 0.200 | 0.580 | 1.000 | 2.000 | 3.250 | 5.00 | 1.363 |
| VIIRS375 | 953 | 0.020 | 0.050 | 0.120 | 0.250 | 0.670 | 2.734 | 9.27 | 0.649 |

## 4. Distancia al vent vs inner_radius_km

Si MIROVA es estricto, n_outside_inner_radius debe ser 0 en todos los volcanes (confirma audit S85).

| Volcán | Sensor | N | inner_km | min | p50 | p95 | max | N fuera |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Chaiten | VIIRS | 1 | 5 | 0.00 | 0.00 | 0.00 | 0.00 | 0 |
| Chaiten | VIIRS375 | 32 | 5 | 0.00 | 0.38 | 0.75 | 1.06 | 0 |
| Copahue | MODIS | 1 | 4 | 0.00 | 0.00 | 0.00 | 0.00 | 0 |
| Copahue | VIIRS375 | 1 | 4 | 3.69 | 3.69 | 3.69 | 3.69 | 0 |
| Isluga | VIIRS | 17 | 5 | 0.00 | 0.75 | 1.48 | 3.18 | 0 |
| Isluga | VIIRS375 | 135 | 5 | 0.00 | 0.53 | 1.26 | 3.09 | 0 |
| Lascar | MODIS | 106 | 5 | 0.00 | 1.00 | 2.00 | 2.24 | 0 |
| Lascar | VIIRS | 149 | 5 | 0.00 | 1.50 | 1.68 | 2.37 | 0 |
| Lascar | VIIRS375 | 242 | 5 | 0.00 | 0.84 | 1.68 | 5.00 | 0 |
| Lastarria | VIIRS375 | 174 | 3 | 0.00 | 1.35 | 2.52 | 2.70 | 0 |
| Llaima | MODIS | 1 | 5 | 0.00 | 0.00 | 0.00 | 0.00 | 0 |
| Llaima | VIIRS375 | 3 | 5 | 0.00 | 0.00 | 1.69 | 1.88 | 0 |
| NevadosDeChillan | MODIS | 2 | 5 | 0.00 | 0.70 | 1.34 | 1.41 | 0 |
| NevadosDeChillan | VIIRS | 1 | 5 | 3.35 | 3.35 | 3.35 | 3.35 | 0 |
| NevadosDeChillan | VIIRS375 | 5 | 5 | 0.00 | 0.38 | 3.96 | 4.28 | 0 |
| PlanchonPeteroa | VIIRS | 2 | 3 | 1.68 | 2.02 | 2.34 | 2.37 | 0 |
| PlanchonPeteroa | VIIRS375 | 90 | 3 | 0.00 | 1.61 | 2.02 | 2.37 | 0 |
| PuyehueCordonCaulle | VIIRS | 22 | 20 | 0.00 | 7.83 | 8.55 | 8.55 | 0 |
| PuyehueCordonCaulle | VIIRS375 | 155 | 20 | 0.00 | 7.65 | 8.55 | 12.11 | 0 |
| Tupungatito | VIIRS | 9 | 7 | 4.37 | 5.03 | 5.41 | 5.41 | 0 |
| Tupungatito | VIIRS375 | 100 | 7 | 0.00 | 5.04 | 5.42 | 6.55 | 0 |
| Villarrica | VIIRS375 | 16 | 5 | 0.00 | 0.84 | 0.84 | 0.84 | 0 |

**4b. CERO ALERTAs fuera del inner_radius en los 11 Tier A** — confirma audit S85 empíricamente.

## 5. Persistencia temporal de episodios (gap ≤2 días)

Distribución global de duraciones de episodio:

- 2 noches: **12** episodios
- 1 noche: **37** episodios
- 4-7 noches: **18** episodios
- 8+ noches: **20** episodios
- 3 noches: **12** episodios

Por volcán:

| Volcán | N episodios | Duración media (d) | Duración máx (d) |
|---|---:|---:|---:|
| Chaiten | 14 | 1.5 | 4 |
| Copahue | 2 | 1.0 | 1 |
| Isluga | 10 | 8.5 | 33 |
| Lascar | 4 | 31.0 | 106 |
| Lastarria | 9 | 12.8 | 45 |
| Llaima | 3 | 1.0 | 1 |
| NevadosDeChillan | 6 | 1.0 | 1 |
| PlanchonPeteroa | 17 | 3.8 | 17 |
| PuyehueCordonCaulle | 14 | 7.0 | 24 |
| Tupungatito | 11 | 6.7 | 31 |
| Villarrica | 9 | 2.0 | 6 |

## 6. Hora local (Chile) de las ALERTAs

Físicamente: MIR solo nocturno (contaminación solar), TIR 24h. ¿Se ve en la data?

Histograma agregado (hora local Chile → N ALERTAs):

| Hora | N |
|---:|---:|
| 00 | 36 |
| 01 | 300 |
| 02 | 525 |
| 03 | 216 |
| 04 | 37 |
| 10 | 2 |
| 13 | 30 |
| 14 | 31 |
| 15 | 34 |
| 16 | 3 |
| 21 | 18 |
| 22 | 30 |
| 23 | 2 |

## 7. Clasificación MIROVA en ALERTAs

¿Hay categorías intermedias o solo NULO/Bajo/...? ¿NULO conviven con ALERTA?

**ALERTAs (Tier A, CONS+OCR):**

- `Muy Bajo`: 689
- `Bajo`: 363
- `Medio`: 204
- `Alto`: 8

**Sanity RUTINA (CONS, Tier A):**

- `NULO`: 16828
- `FALSO POSITIVO`: 12

## 8. OCR vs CONS — ¿segundo canal de publicación?

- ALERTAs en CONS (latest.php JSON): **763**
- ALERTAs en OCR (extraídas de imágenes por-vol): **501**
- Overlap (mismas claves): **140**
- Solo en OCR (publicadas SOLO vía imagen): **361**
- Solo en CONS: **623**

Interpretación: si `n_ocr_only` es alto, MIROVA tiene un segundo canal de publicación que solo aparece en las imágenes por-volcán y no en `latest.php`. Universo MIROVA real = CONS ∪ OCR (regla A11).
