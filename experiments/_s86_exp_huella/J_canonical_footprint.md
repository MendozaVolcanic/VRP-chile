# Experimento J S86 — Huella canónica volcánica per-vol

**Ventana**: 2026-01-28 → 2026-05-25.
**Records publishable**: 5337 | **TP**: 1650 | **FP**: 3687.

## Lectura física

La hipótesis de Nicolás es geológicamente sólida: el calor volcánico sale de una fuente fija — el cráter activo, el lago cratérico, el lacolito intruido. Esa fuente no se mueve de una noche a la otra. Por lo tanto la anomalía térmica real debe agruparse, mes tras mes, en un mismo punto del terreno. Una detección que aparece lejos de esa nube — un foco térmico que surge fuera de la huella — es sospechosa: un incendio de pastizal en verano, un reflejo, una nube fría que el kernel contextual confunde. La huella canónica formaliza esa intuición: la construimos con los centroides de los clusters que MIROVA nos confirmó (TP), porque esos son, por definición, los puntos donde un operador defendió 'esto es el volcán'.

## J.1 — Huella por volcán

| Volcán | n TP coords | centroide (lat,lon) | r50 km | r90 km | r95 km | d→vent km | forma |
|---|---:|---|---:|---:|---:|---:|---|
| Chaiten | 64 | -42.8323,-72.6584 | 0.746 | 1.191 | 1.28 | 0.512 | compacta |
| Copahue | 4 | -37.8685,-71.1732 | 1.379 | 2.127 | 2.216 | 1.64 | intermedia |
| Isluga | 220 | -19.1575,-68.8334 | 0.87 | 1.741 | 2.576 | 0.907 | compacta |
| Lascar | 335 | -23.3610,-67.7379 | 0.745 | 1.272 | 1.424 | 0.694 | compacta |
| Lastarria | 290 | -25.1598,-68.5118 | 0.962 | 2.69 | 2.902 | 1.031 | intermedia |
| Llaima | 7 | -38.6797,-71.7294 | 0.722 | 2.3 | 2.698 | 1.364 | intermedia |
| NevadosDeChillan | 1 | -36.8694,-71.3954 | 0.0 | 0.0 | 0.0 | 1.79 | compacta |
| PlanchonPeteroa | 181 | -35.2226,-70.5688 | 1.565 | 2.274 | 2.343 | 2.1 | intermedia |
| PuyehueCordonCaulle | 287 | -40.5249,-72.1124 | 5.254 | 14.484 | 16.886 | 2.849 | extendida/difusa |
| Tupungatito | 227 | -33.3859,-69.8300 | 0.637 | 0.946 | 1.333 | 0.492 | compacta |
| Villarrica | 34 | -39.4134,-71.9437 | 0.65 | 1.664 | 1.811 | 0.831 | compacta |

- **r50/r90/r95**: radio (km) que contiene 50/90/95% de los centroides TP respecto al centroide medio de la huella. Mide la dispersión espacial.
- **forma**: compacta (r90≤2 km, foco puntual), intermedia (2–5 km), extendida/difusa (>5 km).

## J.2 — Estabilidad temporal (drift centroide mes a mes)

| Volcán | n meses | drift máx entre meses (km) | drift medio (km) |
|---|---:|---:|---:|
| Chaiten | 5 | 1.433 | 0.819 |
| Copahue | 1 | None | None |
| Isluga | 5 | 1.489 | 0.718 |
| Lascar | 5 | 0.483 | 0.312 |
| Lastarria | 5 | 0.848 | 0.425 |
| Llaima | 2 | 1.535 | 1.535 |
| NevadosDeChillan | 1 | None | None |
| PlanchonPeteroa | 4 | 0.809 | 0.642 |
| PuyehueCordonCaulle | 5 | 10.721 | 6.056 |
| Tupungatito | 4 | 3.254 | 1.678 |
| Villarrica | 4 | 0.748 | 0.545 |

Lectura: si el drift máximo entre meses es pequeño (≤ r95 de la huella), la huella es **estable durante el año** — confirma la hipótesis de Nicolás. Drift grande indica o bien fuente migrante (raro) o bien contaminación del primary por clusters no-volcánicos algunos meses.

## J.3 — Separación huella vs categorías (% dentro del r95)

| Volcán | TP %∈r95 (n) | FP-b %∈r95 (n) | FP-d %∈r95 (n) |
|---|---|---|---|
| Chaiten | 93.8 (64) | 68.2 (415) | 16.5 (91) |
| Copahue | 75.0 (4) | 74.3 (373) | 48.4 (31) |
| Isluga | 95.0 (220) | 95.4 (175) | 22.4 (49) |
| Lascar | 94.9 (335) | 91.9 (234) | 25.0 (8) |
| Lastarria | 94.8 (290) | 97.1 (173) | 90.9 (22) |
| Llaima | 85.7 (7) | 92.6 (296) | 31.4 (70) |
| NevadosDeChillan | 100.0 (1) | 22.5 (142) | 5.4 (37) |
| PlanchonPeteroa | 95.0 (181) | 99.1 (220) | 100.0 (29) |
| PuyehueCordonCaulle | 94.8 (287) | 96.8 (533) | 78.1 (160) |
| Tupungatito | 94.7 (227) | 88.6 (88) | 6.4 (109) |
| Villarrica | 94.1 (34) | 78.1 (389) | 37.2 (43) |

**Pooled (todos los vols)**: TP 94.7% (n=1650), FP-b 83.3% (n=3038), FP-d 40.7% (n=649).

**Métrica clave**: si TP y FP-b (volcánico real del complejo) caen mayoritariamente DENTRO del r95, y FP-d (artefacto) caen FUERA, entonces el gate 'dentro de la huella' separa volcánico de artefacto mejor que el inner_radius circular.

### inner_radius vs huella r95 (¿la huella es más fina?)

| Volcán | inner_radius km | huella r95 km | huella más fina por (km) |
|---|---:|---:|---:|
| Chaiten | 5.0 | 1.28 | 3.72 |
| Copahue | 4.0 | 2.216 | 1.784 |
| Isluga | 5.0 | 2.576 | 2.424 |
| Lascar | 5.0 | 1.424 | 3.576 |
| Lastarria | 3.0 | 2.902 | 0.098 |
| Llaima | 5.0 | 2.698 | 2.302 |
| NevadosDeChillan | 5.0 | 0.0 | 5.0 |
| PlanchonPeteroa | 3.0 | 2.343 | 0.657 |
| PuyehueCordonCaulle | 20.0 | 16.886 | 3.114 |
| Tupungatito | 7.0 | 1.333 | 5.667 |
| Villarrica | 5.0 | 1.811 | 3.189 |

## J.4 — Casos especiales (PCC lacolito, Lascar cráter, Tupungatito lago)

### PuyehueCordonCaulle
- Huella: centroide (-40.5249, -72.1124), r95=16.886 km, forma **extendida/difusa**, a 2.849 km del vent.
- **Candidatos a incendio/artefacto** (publishable, centroide fuera del r95, alto VRP): 15 listados (top por VRP):

  | noche | sensor | VRP MW | dist a huella km | TP? | cat FP |
  |---|---|---:|---:|---|---|
  | 2026-02-16 | MODIS | 48.258 | 19.31 | False | b |
  | 2026-03-16 | MODIS | 38.957 | 21.83 | False | d |
  | 2026-01-29 | MODIS | 29.988 | 17.92 | False | d |
  | 2026-02-20 | VIIRS750 | 25.333 | 17.63 | False | b |
  | 2026-04-05 | VIIRS750 | 23.139 | 18.38 | False | b |
  | 2026-03-06 | VIIRS750 | 19.799 | 18.43 | False | b |
  | 2026-02-20 | VIIRS750 | 19.12 | 17.75 | False | b |
  | 2026-03-06 | VIIRS750 | 18.38 | 19.31 | False | b |
  | 2026-03-31 | VIIRS750 | 18.096 | 19.89 | False | b |
  | 2026-04-08 | VIIRS750 | 14.996 | 20.18 | False | d |

### Lascar
- Huella: centroide (-23.3610, -67.7379), r95=1.424 km, forma **compacta**, a 0.694 km del vent.
- **Candidatos a incendio/artefacto** (publishable, centroide fuera del r95, alto VRP): 15 listados (top por VRP):

  | noche | sensor | VRP MW | dist a huella km | TP? | cat FP |
  |---|---|---:|---:|---|---|
  | 2026-02-02 | VIIRS750 | 8.82 | 1.6 | False | b |
  | 2026-02-08 | VIIRS750 | 7.676 | 1.44 | False | b |
  | 2026-02-02 | VIIRS375 | 5.134 | 1.52 | False | b |
  | 2026-03-10 | MODIS | 5.037 | 1.61 | True | — |
  | 2026-03-17 | VIIRS750 | 4.511 | 1.56 | False | b |
  | 2026-03-31 | VIIRS750 | 4.045 | 1.53 | False | b |
  | 2026-05-07 | VIIRS750 | 3.96 | 2.39 | False | d |
  | 2026-02-02 | VIIRS750 | 2.472 | 2.59 | False | b |
  | 2026-04-11 | VIIRS375 | 2.285 | 2.38 | False | b |
  | 2026-04-09 | VIIRS750 | 2.219 | 2.51 | False | b |

### Tupungatito
- Huella: centroide (-33.3859, -69.8300), r95=1.333 km, forma **compacta**, a 0.492 km del vent.
- **Candidatos a incendio/artefacto** (publishable, centroide fuera del r95, alto VRP): 15 listados (top por VRP):

  | noche | sensor | VRP MW | dist a huella km | TP? | cat FP |
  |---|---|---:|---:|---|---|
  | 2026-03-09 | VIIRS750 | 19.781 | 6.44 | False | d |
  | 2026-02-04 | VIIRS750 | 15.039 | 6.57 | False | d |
  | 2026-02-03 | VIIRS750 | 14.169 | 6.46 | False | d |
  | 2026-05-15 | VIIRS750 | 13.492 | 6.14 | False | d |
  | 2026-03-17 | VIIRS750 | 13.329 | 6.43 | False | d |
  | 2026-02-15 | VIIRS750 | 12.603 | 6.62 | False | d |
  | 2026-04-25 | VIIRS750 | 12.414 | 6.66 | False | d |
  | 2026-04-12 | VIIRS750 | 12.341 | 6.47 | False | d |
  | 2026-04-14 | VIIRS750 | 12.211 | 6.88 | False | d |
  | 2026-04-26 | VIIRS750 | 12.19 | 6.58 | False | d |

## Limitaciones

- JSON solo guarda primary_cluster (criterio vent_anchored S38). No clusters alternativos.
- MIROVA CSV sin lat/lon (solo Distancia_km radial; OCR en Nota como dist~XX km).
- Loader hereda bugs F-B1/B2 (OCR distancia no consumida, alias). Huella construida con cruce exacto C.
- Categorias FP a/b/c/d via heuristica geografica replicada de script_E (no verificacion humana).
