# S144: resultado del conteo de pasadas VIIRS 375 con TIF de MIROVA

> Generado por `conteo_tif.py`; no editar a mano. Definiciones en `README.md`, incluida la enmienda.

Entradas: records `beba9b3d16a4`, índice de TIF `da4fe36e8920`, CONS `3b18c772f65a`, OCR `7e3438046ca1`, `frontend/index.html` `24fba8a15713`. Última pasada: 2026-09-19 06:48 UTC. Primera adquisición del índice: 2026-05-09T04:48.

## Ventana `historia`

| nivel de TIF | pasadas | con_tif | con_alerta | alerta_y_tif | patron | patron_y_tif | patron_alerta_tif | publicadas | patron_publicadas_tif |
|---|---|---|---|---|---|---|---|---|---|
| tif_cualquiera | 6231 | 2446 | 920 | 439 | 2540 | 937 | 47 | 4293 | 799 |
| tif_propia | 6231 | 2229 | 920 | 396 | 2540 | 858 | 40 | 4293 | 728 |
| tif_utm_375 | 6231 | 25 | 920 | 6 | 2540 | 7 | 0 | 4293 | 7 |

Etiquetas de todas las pasadas: {'sin_info': 2852, 'pos': 920, 'far_ref': 220, 'neg_limpio': 2239}. Patrón con TIF propio: {'sin_info': 202, 'neg_limpio': 570, 'far_ref': 46, 'pos': 40}.

## Ventana `desde_2026-09-14_0636`

| nivel de TIF | pasadas | con_tif | con_alerta | alerta_y_tif | patron | patron_y_tif | patron_alerta_tif | publicadas | patron_publicadas_tif |
|---|---|---|---|---|---|---|---|---|---|
| tif_cualquiera | 249 | 122 | 43 | 23 | 73 | 34 | 2 | 217 | 34 |
| tif_propia | 249 | 112 | 43 | 22 | 73 | 32 | 2 | 217 | 32 |
| tif_utm_375 | 249 | 25 | 43 | 6 | 73 | 7 | 0 | 217 | 7 |

Etiquetas de todas las pasadas: {'sin_info': 110, 'pos': 43, 'neg_limpio': 89, 'far_ref': 7}. Patrón con TIF propio: {'neg_limpio': 22, 'sin_info': 8, 'pos': 2}.

## Por volcán (historia, TIF propio)

| volcán | pasadas | patrón | patrón y TIF | patrón, alerta y TIF | patrón publicado y TIF |
|---|---|---|---|---|---|
| Lascar | 494 | 132 | 51 | 0 | 19 |
| Lastarria | 499 | 290 | 106 | 24 | 54 |
| Isluga | 476 | 119 | 41 | 6 | 41 |
| Tupungatito | 561 | 169 | 57 | 7 | 57 |
| PlanchonPeteroa | 561 | 228 | 72 | 1 | 72 |
| NevadosDeChillan | 592 | 283 | 96 | 1 | 50 |
| Llaima | 602 | 322 | 100 | 0 | 100 |
| Villarrica | 604 | 337 | 108 | 0 | 108 |
| Copahue | 583 | 396 | 137 | 0 | 137 |
| PuyehueCordonCaulle | 620 | 51 | 14 | 0 | 14 |
| Chaiten | 639 | 213 | 76 | 1 | 76 |

## Contra el conteo exploratorio (ventana desde 2026-09-14 06:36)

| conjunto | exploratorio | TIF cualquiera | TIF propio | TIF UTM 375 |
|---|---|---|---|---|
| pasadas | 290 | 249 | 249 | 249 |
| con_tif | 122 | 122 | 112 | 25 |
| con_alerta | 58 | 43 | 43 | 43 |
| alerta_y_tif | 23 | 23 | 22 | 6 |
| patron | 81 | 73 | 73 | 73 |
| patron_y_tif | 34 | 34 | 32 | 7 |
| patron_alerta_tif | 2 | 2 | 2 | 0 |

## Controles del instrumento

- P2, predicado node: identidad OK.
- P1, placebo (+6 h): 0 pasadas con TIF.
- P1, lectura directa: 2264 TIF leídos con rasterio; CRS {'EPSG:4326': 2240, 'EPSG:32719': 21, 'EPSG:32718': 3}.
- Adquisiciones con TIF UTM de 375 m: 2026-09-14T06:36, 2026-09-15T04:36, 2026-09-15T04:42, 2026-09-15T05:18, 2026-09-15T05:24, 2026-09-15T06:12, 2026-09-15T06:18, 2026-09-15T06:24.
- |Δt| TIF-record: n 2446, mín 0 s, mediana 1.0 s, máx 362 s; 289 en 0 s, 0 sobre 14 min.
- TIF emparejados con más de una pasada nuestra: 171.
- Etiquetas de fecha dentro de los TIF: ninguna.
