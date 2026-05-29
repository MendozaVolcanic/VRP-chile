# Experimento K S86 — Criterio de selección de cluster (evidencia preliminar)

**Ventana**: 2026-01-28 → 2026-05-25. **TP matcheados con VRP MIROVA**: 490.

## Limitación central (A18)

El JSON guarda **solo el primary_cluster** ya elegido con el criterio **C1 vent_anchored** (S38). No hay clusters alternativos almacenados. Por lo tanto **NO se puede re-rankear C2 (vrp_max_inner) ni C3 (vrp_max_within_footprint) sin REPROCESO real**. La regla A18 es explícita: el preview offline filtra records ya seleccionados con el parámetro viejo, pero el reproc real rerunnea la selección desde cero y puede elegir un cluster distinto. Lo que sigue es **evidencia preliminar** para decidir si vale el reproc A/B en S87, no veredicto.

## Lectura física

MIROVA, cuando publica, reporta un VRP y una distancia radial al vent. Si nuestro criterio actual (el cluster más cercano al cráter) reproduce esa magnitud, el ratio nuestro/MIROVA ronda 1. Si sistemáticamente subreporta (ratio <1), significa que el cluster pegado al vent es más débil que el que MIROVA realmente vio — y entonces convendría elegir el de mayor VRP dentro del radio (C2). Si sobre-reporta (ratio >1), el primary está capturando señal de más (halo, escena) y un criterio más fino — la huella J — ayudaría a recortarlo.

## K.a — Ratio VRP nuestro (C1) / MIROVA por volcán

**Global**: {'n': 490, 'median_ratio': 4.593, 'mean_ratio': 14.371, 'p25': 1.252, 'p75': 18.6, 'frac_ratio_lt_1': 0.184, 'frac_ratio_lt_0p5': 0.094, 'frac_ratio_gt_2': 0.631}

| Volcán | n | mediana ratio | p25 | p75 | %ratio<1 | %ratio<0.5 | %ratio>2 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Chaiten | 16 | 10.344 | 4.422 | 39.04 | 0.0 | 0.0 | 1.0 |
| Copahue | 1 | 15.595 | 15.595 | 15.595 | 0.0 | 0.0 | 1.0 |
| Isluga | 73 | 3.318 | 1.392 | 7.692 | 0.192 | 0.055 | 0.63 |
| Lascar | 111 | 1.469 | 1.078 | 2.115 | 0.198 | 0.063 | 0.279 |
| Lastarria | 89 | 3.488 | 0.34 | 22.056 | 0.303 | 0.27 | 0.539 |
| Llaima | 2 | 12.251 | 12.036 | 12.466 | 0.0 | 0.0 | 1.0 |
| NevadosDeChillan | 1 | 0.547 | 0.547 | 0.547 | 1.0 | 0.0 | 0.0 |
| PlanchonPeteroa | 53 | 13.339 | 6.667 | 27.914 | 0.019 | 0.019 | 0.943 |
| PuyehueCordonCaulle | 64 | 6.988 | 0.823 | 19.848 | 0.281 | 0.141 | 0.688 |
| Tupungatito | 68 | 19.734 | 9.217 | 28.981 | 0.103 | 0.015 | 0.868 |
| Villarrica | 12 | 21.449 | 15.342 | 42.397 | 0.0 | 0.0 | 1.0 |

- Volcanes con subreporte sistemático (mediana ratio <0.8, n≥5): **0**.
- Volcanes con sobre-reporte sistemático (mediana ratio >1.5, n≥5): **7**.

## K.b — Concordancia radial: nuestro dist vs MIROVA Distancia_km

**Global**: {'n': 485, 'median_diff_km': -0.796, 'mean_abs_diff_km': 1.9, 'frac_within_1km': 0.52, 'frac_within_2km': 0.728}

| Volcán | n | mediana Δdist km | |Δ| medio km | %≤1km | %≤2km |
|---|---:|---:|---:|---:|---:|
| Chaiten | 16 | 0.114 | 0.77 | 0.812 | 0.938 |
| Copahue | 1 | -2.87 | 2.87 | 0.0 | 0.0 |
| Isluga | 70 | -0.185 | 0.862 | 0.557 | 0.943 |
| Lascar | 111 | -0.796 | 1.029 | 0.64 | 0.856 |
| Lastarria | 89 | -0.512 | 0.834 | 0.685 | 1.0 |
| Llaima | 2 | -0.528 | 1.752 | 0.0 | 0.5 |
| NevadosDeChillan | 1 | -1.56 | 1.56 | 0.0 | 1.0 |
| PlanchonPeteroa | 53 | -0.605 | 0.68 | 0.792 | 1.0 |
| PuyehueCordonCaulle | 62 | -3.24 | 6.283 | 0.016 | 0.081 |
| Tupungatito | 68 | -3.915 | 3.229 | 0.206 | 0.235 |
| Villarrica | 12 | -0.142 | 0.596 | 0.917 | 1.0 |

(Δdist = nuestro centroid_dist_km − MIROVA Distancia_km. Positivo = nuestro cluster está más lejos del vent que el de MIROVA.)

## K.c — Candidatos a incendio/artefacto (primary fuera de huella, alto VRP)

| Volcán | n publishable | n fuera huella | n fuera + VRP≥3MW |
|---|---:|---:|---:|
| Chaiten | 570 | 212 | 59 |
| Copahue | 408 | 113 | 21 |
| Isluga | 444 | 57 | 1 |
| Lascar | 577 | 42 | 7 |
| Lastarria | 485 | 22 | 1 |
| Llaima | 373 | 71 | 9 |
| NevadosDeChillan | 180 | 145 | 38 |
| PlanchonPeteroa | 430 | 11 | 0 |
| PuyehueCordonCaulle | 980 | 67 | 29 |
| Tupungatito | 424 | 124 | 69 |
| Villarrica | 466 | 114 | 30 |

**Vols del sur** (Villarrica, Llaima, Chaitén, PCC, NdC, Copahue, PP): 186 candidatos VRP≥3MW fuera de huella sobre 3407 publishable = 5.46%.

## K.1 — Recomendación

**1. ¿Subreporta C1 vent_anchored?** NO. El ratio mediano global es 4.593 (>1) y 0/11 vols subreportan (mediana <0.8). Al contrario, 7 vols **sobre-reportan** (mediana >1.5). Esto refuta la hipótesis 'vent_anchored elige un cluster más débil que MIROVA'. El sobre-reporte es el drift de magnitud per-vol ya documentado (PP 4.39×, Tupungatito 5.27×, MEMORY A12/A19) + el factor de agregación cluster vs pixel (S23 T14), NO un problema de selección de cluster. **Implicación**: C2 vrp_max_inner empeoraría el sobre-reporte (elegiría clusters aún más grandes). No es el camino.

**2. ¿Vale la pena el gate huella canónica (más fino que inner_radius)?** SÍ, condicionalmente. J mostró que la huella separa artefacto (FP-d 40.7% dentro) de volcánico (TP 94.7%, FP-b 83.3% dentro) mucho mejor que el inner_radius circular (todo publishable está dentro del inner por definición). El caso más claro es **Tupungatito**: 69 records VRP≥3MW fuera de la huella, casi todos VIIRS750 a ~6.5 km del cráter = ring glaciar (A19). La huella los aísla limpiamente; el inner_radius=7km no. Implementación natural: campo derivado `pc.within_footprint` por vol, como refinamiento del gate frontend, NO como nuevo gate de pipeline (evitar anti-patrón A55 'gate intra-radio por path').

**3. ¿Frecuencia de candidatos a incendio en vols del sur?** 186/3407 = 5.46% publishable con VRP≥3MW fuera de la huella. Es un problema **acotado, no masivo**. La concentración real está en Tupungatito (ring glaciar, ya categoría d conocida) y en PCC/NdC donde la huella es difusa o degenerada (ver caveat). En el sur estricto el candidato dominante es Chaitén (59) y NdC (38) — requieren inspección visual antes de tratarlos como incendio: pueden ser features reales del complejo (categoría b).

### Caveats de la huella

- **NevadosDeChillan**: solo 1 TP en la ventana → r95 degenerado (0 km, floored a 0.5). Su columna 'fuera de huella' está inflada artificialmente. NO interpretar los 38 candidatos NdC como incendios sin más TPs.
- **Copahue / Llaima**: 1–2 TP → huella poco robusta.
- **PCC**: huella legítimamente extendida/difusa (lacolito, r95=16.9 km). Los candidatos PCC fuera de huella están a >17 km = realmente fuera del complejo (posibles incendios del valle), coherente con la intuición.

**Decisión final C1/C2/C3 requiere reproc A/B real (A18). Recomendación: NO migrar a C2. Evaluar en S87 el campo derivado `pc.within_footprint` como refinamiento de etiquetado (Bloque 3 del plan S87), construyendo la huella solo en vols con n_TP≥10 (Lascar, Tupungatito, Lastarria, Isluga, PCC, PP, Chaitén).**
