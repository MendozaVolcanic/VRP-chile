# Subagente B — Caracterización VRP Chile crudo (pre-frontend filter)
**Frente 2.A S86 — precision gap audit**
Ventana analizada (overlap con CSV Subagente A): `2026-01-29T01:00:00` → `2026-05-18T07:35:00`

## 1. Resumen geológico
El pipeline térmico VRP-Chile detecta una población mucho más amplia que la que MIROVA finalmente publica. Filtrando los JSONs operacionales al overlap con el CSV consolidado (2026-01-10–2026-05-18), tenemos **6158 records 'publishable'** (pc.vrp_mw>0 dentro del inner_radius del KMZ) repartidos entre los 11 Tier A. Ese conjunto es ya el output post-filtro geométrico del frontend; el gap restante respecto a MIROVA (~99%) tiene que explicarse por otra capa de supresión.

## 2. Distribución de pc.vrp_mw (records publishable, por sensor)
| Sensor | n | min | p5 | p25 | p50 | p75 | p95 | max | mean |
|---|---|---|---|---|---|---|---|---|---|
| MODIS | 2574 | 0.067 | 0.751 | 3.569 | 8.498 | 21.005 | 68.416 | 1362.039 | 20.874 |
| VIIRS_I375 | 3681 | 0.001 | 0.036 | 0.262 | 1.252 | 2.644 | 5.985 | 39.629 | 1.892 |
| VIIRS_M750 | 2706 | 0.026 | 0.474 | 1.360 | 2.665 | 5.637 | 16.191 | 91.188 | 5.054 |

## 3. pc.n_pixels — tamaño del cluster primary (publishable, agregado)
Hipótesis: si la mayoría de nuestros records tiene pc.n_pixels=1, MIROVA podría requerir cluster mínimo (≥2-3 px) para suprimir ruido de pixel aislado.

| bucket | count | share |
|---|---|---|
| 1 | 1122 | 18.2% |
| 2 | 431 | 7.0% |
| 3 | 231 | 3.8% |
| 4-5 | 343 | 5.6% |
| 6-10 | 564 | 9.2% |
| 11+ | 3467 | 56.3% |

## 4. pc.path breakdown (inferido de diag_n_*_path)
Path D (dNTI contextual) es históricamente sospechoso de FPs sistémicos en cirrus alto (regla A23).

**Publishable (in-radius):**

| path | count | share |
|---|---|---|
| dNTI | 5078 | 82.5% |
| none | 888 | 14.4% |
| multi:BT+dNTI | 140 | 2.3% |
| multi:BT+NTI+dNTI | 44 | 0.7% |
| multi:NTI+dNTI | 7 | 0.1% |
| BT | 1 | 0.0% |

Fracción dNTI (solo o combinado) sobre publishable: **85.6%**.

## 5. final_hotspot_source breakdown (publishable)
`cluster_rescue` señaliza discrepancia entre pixel single (scene-wide) y cluster vent-anchored (A46/S77).

| source | count |
|---|---|
| eruption | 3311 |
| test1 | 2847 |

## 6. Conteo por volcán
| Vol | inner_km | total | pc.vrp>0 | publishable | R3 fantasma | n_episodios |
|---|---|---|---|---|---|---|
| Chaiten | 5 | 1254 | 917 | 693 | 224 | 1 |
| Copahue | 4 | 1184 | 862 | 415 | 447 | 1 |
| Isluga | 5 | 975 | 671 | 474 | 197 | 1 |
| Lascar | 5 | 1018 | 815 | 598 | 217 | 1 |
| Lastarria | 3 | 1015 | 876 | 559 | 317 | 1 |
| Llaima | 5 | 1200 | 718 | 406 | 312 | 3 |
| NevadosDeChillan | 5 | 1164 | 527 | 234 | 293 | 8 |
| PlanchonPeteroa | 3 | 1138 | 824 | 497 | 327 | 1 |
| PuyehueCordonCaulle | 20 | 1241 | 1164 | 1144 | 20 | 1 |
| Tupungatito | 7 | 1118 | 699 | 576 | 123 | 2 |
| Villarrica | 5 | 1202 | 888 | 562 | 326 | 1 |

## 7. Episodios publishable (gap ≤2 días) — duración en días
| Vol | n_episodios | p50 días | p95 días | max |
|---|---|---|---|---|
| Chaiten | 1 | 109.21 | 109.21 | 109.21 |
| Copahue | 1 | 109.09 | 109.09 | 109.09 |
| Isluga | 1 | 109.26 | 109.26 | 109.26 |
| Lascar | 1 | 109.08 | 109.08 | 109.08 |
| Lastarria | 1 | 109.10 | 109.10 | 109.10 |
| Llaima | 3 | 34.07 | 46.69 | 48.09 |
| NevadosDeChillan | 8 | 6.50 | 28.35 | 33.98 |
| PlanchonPeteroa | 1 | 109.09 | 109.09 | 109.09 |
| PuyehueCordonCaulle | 1 | 109.20 | 109.20 | 109.20 |
| Tupungatito | 2 | 53.54 | 94.53 | 99.08 |
| Villarrica | 1 | 109.09 | 109.09 | 109.09 |

## 8. Por sensor por volcán (resumen total / publishable)
| Vol | Sensor | total | pc.vrp>0 | publishable | R3 | p50 vrp publishable |
|---|---|---|---|---|---|---|
| Chaiten | MODIS | 265 | 265 | 143 | 122 | 11.898 |
| Chaiten | VIIRS_I375 | 474 | 379 | 366 | 13 | 1.071 |
| Chaiten | VIIRS_M750 | 515 | 273 | 184 | 89 | 2.928 |
| Copahue | MODIS | 246 | 245 | 40 | 205 | 7.915 |
| Copahue | VIIRS_I375 | 462 | 353 | 314 | 39 | 1.482 |
| Copahue | VIIRS_M750 | 476 | 264 | 61 | 203 | 3.357 |
| Isluga | MODIS | 202 | 202 | 62 | 140 | 5.970 |
| Isluga | VIIRS_I375 | 378 | 312 | 303 | 9 | 0.363 |
| Isluga | VIIRS_M750 | 395 | 157 | 109 | 48 | 1.370 |
| Lascar | MODIS | 208 | 208 | 53 | 155 | 9.058 |
| Lascar | VIIRS_I375 | 405 | 340 | 335 | 5 | 1.252 |
| Lascar | VIIRS_M750 | 405 | 267 | 210 | 57 | 2.270 |
| Lastarria | MODIS | 198 | 198 | 90 | 108 | 6.660 |
| Lastarria | VIIRS_I375 | 409 | 365 | 358 | 7 | 0.776 |
| Lastarria | VIIRS_M750 | 408 | 313 | 111 | 202 | 2.593 |
| Llaima | MODIS | 237 | 236 | 58 | 178 | 6.432 |
| Llaima | VIIRS_I375 | 469 | 277 | 255 | 22 | 1.727 |
| Llaima | VIIRS_M750 | 494 | 205 | 93 | 112 | 2.109 |
| NevadosDeChillan | MODIS | 245 | 243 | 53 | 190 | 7.498 |
| NevadosDeChillan | VIIRS_I375 | 448 | 147 | 126 | 21 | 1.496 |
| NevadosDeChillan | VIIRS_M750 | 471 | 137 | 55 | 82 | 2.029 |
| PlanchonPeteroa | MODIS | 251 | 251 | 101 | 150 | 9.551 |
| PlanchonPeteroa | VIIRS_I375 | 432 | 372 | 354 | 18 | 1.425 |
| PlanchonPeteroa | VIIRS_M750 | 455 | 201 | 42 | 159 | 2.143 |
| PuyehueCordonCaulle | MODIS | 259 | 257 | 243 | 14 | 23.528 |
| PuyehueCordonCaulle | VIIRS_I375 | 474 | 447 | 446 | 1 | 1.126 |
| PuyehueCordonCaulle | VIIRS_M750 | 508 | 460 | 455 | 5 | 5.563 |
| Tupungatito | MODIS | 232 | 232 | 161 | 71 | 7.000 |
| Tupungatito | VIIRS_I375 | 435 | 329 | 325 | 4 | 1.358 |
| Tupungatito | VIIRS_M750 | 451 | 138 | 90 | 48 | 1.898 |
| Villarrica | MODIS | 237 | 237 | 114 | 123 | 12.728 |
| Villarrica | VIIRS_I375 | 468 | 360 | 342 | 18 | 2.181 |
| Villarrica | VIIRS_M750 | 497 | 291 | 106 | 185 | 3.482 |

## 9. Interpretación geológica preliminar
- **El filtro geométrico del frontend ya descarta ~2803 records 'fantasma' (cluster fuera de inner_radius). Lo que el dashboard muestra es solo el 69% de los pc.vrp>0 detectados crudos.**
- Para cerrar el gap restante con MIROVA, la hipótesis tamaño-de-cluster es directamente testeable: si el histograma pc.n_pixels muestra alta densidad en `1` y `2`, MIROVA probablemente requiere coherencia espacial mínima (≥3 px contiguos en grilla 1km equivalente).
- El path dNTI contextual concentra una fracción no trivial del publishable; si MIROVA no usa dNTI sin co-validación BT/NTI absoluto, este path puede ser el origen estructural del exceso.
- Episodios cortos (mediana <1 día) sugieren detecciones esporádicas no persistentes; MIROVA puede requerir 2-3 noches consecutivas para confirmar.
