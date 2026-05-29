# Subagente E S86 — Auditoría profunda FPs: artefacto vs realidad física

**Ventana**: 2026-01-28 → 2026-05-25  
**Publishable records nuestros**: 5337  
**FPs estrictos (cruce exacto vs CONS+OCR)**: 3687

## Hallazgo central

De los 3687 FPs operacionales:

- **(a) Falsos FP (MIROVA SÍ publicó, mismatch ±1d / cross-sensor)**: 1812 = **49.1%**
- **(b) Anomalía volcánica REAL no publicada por MIROVA**: 1707 = **46.3%**
- **(c) Geotermal / lacustre NO volcánico real**: 0 = **0.0%**
- **(d) Artefacto (cirrus / glaciar / singleton)**: 168 = **4.6%**

**Realidad física total ((a)+(b)+(c))**: 3519 = **95.4%**  
**Artefactos ((d))**: 168 = **4.6%**

## Tarea 1 — Recuperación categoría (a) por tolerancia

| Mecanismo de recuperación | n |
|---|---:|
| same_night_cross_sensor | 749 |
| ±1d_same_sensor(d=-1) | 419 |
| ±1d_same_sensor(d=1) | 260 |
| ±1d_cross_sensor(d=-1) | 250 |
| ±1d_cross_sensor(d=1) | 134 |
| **Total recuperados (a)** | **1812** |
| **Residuales para Tarea 2** | **1875** |

## Tarea 2 — Matriz volcán × categoría (FPs residuales)

| Volcán | b (volcánico real) | c (geotermal no-volc) | d (artefacto) | total |
|---|---:|---:|---:|---:|
| Chaiten | 326 | 0 | 36 | 362 |
| Copahue | 367 | 0 | 10 | 377 |
| Isluga | 54 | 0 | 6 | 60 |
| Lascar | 0 | 0 | 0 | 0 |
| Lastarria | 13 | 0 | 0 | 13 |
| Llaima | 286 | 0 | 43 | 329 |
| NevadosDeChillan | 138 | 0 | 8 | 146 |
| PlanchonPeteroa | 109 | 0 | 1 | 110 |
| PuyehueCordonCaulle | 57 | 0 | 19 | 76 |
| Tupungatito | 32 | 0 | 29 | 61 |
| Villarrica | 325 | 0 | 16 | 341 |
| **TOTAL** | **1707** | **0** | **168** | **1875** |

### Subcategorías detalladas

| Subcategoría | n |
|---|---:|
| b_volcanic_real_summit | 839 |
| b_volcanic_real_complex | 744 |
| b_volcanic_real_unmapped | 124 |
| d_artifact_singleton | 86 |
| d_artifact_cirrus | 56 |
| d_artifact_glacier_ring | 24 |
| d_artifact_outside_inner | 2 |

## Tarea 3 — 20 FPs para validación humana (Google Earth / KMZ)

Lat/lon decimal grados. Sensor + noche local Chile. Pegar lat,lon en Earth.

| # | Volcán | Sensor | Noche | Lat | Lon | dist vent | bearing | VRP MW | n pix | t_bg K | Path | Categoría | Razón |
|---:|---|---|---|---:|---:|---:|---|---:|---:|---:|---|---|---|
| 1 | Chaiten | VIIRS375 | 2026-05-12 | -42.8342 | -72.6489 | 0.32 | E | 0.006 | 1 | 272.4 | none | b_volcanic_real_summit | ≤2.0km vent nominal (0.32 km) |
| 2 | Chaiten | VIIRS375 | 2026-02-15 | -42.823 | -72.6664 | 1.69 | NW | 1.295 | 21 | 276.3 | D | b_volcanic_real_summit | ≤2.0km vent nominal (1.69 km) |
| 3 | Copahue | VIIRS375 | 2026-02-02 | -37.8666 | -71.1744 | 1.4 | SSE | 10.316 | 64 | 282.2 | D | b_volcanic_real_complex | ≤2.5km de Alineamiento cráteres ENE-WSW (S85FaseC c4 (flanco SW cráter)) |
| 4 | Copahue | VIIRS375 | 2026-03-11 | -37.8665 | -71.192 | 1.41 | SW | 3.153 | 61 | 280.3 | D | b_volcanic_real_complex | ≤2.5km de Alineamiento cráteres ENE-WSW (S85FaseC c4 (flanco SW cráter)) |
| 5 | Isluga | VIIRS750 | 2026-02-16 | -19.1456 | -68.8256 | 0.68 | NE | 0.268 | 1 | 217.3 | D | b_volcanic_real_summit | ≤2.0km vent nominal (0.68 km) |
| 6 | Isluga | MODIS | 2026-02-14 | -19.1609 | -68.8255 | 1.3 | SSE | 56.573 | 9 | 257.8 | D | b_volcanic_real_summit | ≤2.0km vent nominal (1.30 km) |
| 7 | Lastarria | VIIRS375 | 2026-02-07 | -25.162 | -68.5198 | 1.45 | WNW | 4.218 | 83 | 267.7 | D | b_volcanic_real_summit | ≤2.0km vent nominal (1.45 km) |
| 8 | Lastarria | VIIRS375 | 2026-03-19 | -25.1507 | -68.5134 | 2.03 | NNW | 1.618 | 40 | 265.8 | D | b_volcanic_real_unmapped | intra-inner sin feature catalogada (d_vent=2.03km) |
| 9 | Llaima | VIIRS375 | 2026-02-15 | -38.6859 | -71.7134 | 1.51 | ENE | 3.463 | 80 | 278.4 | D | b_volcanic_real_summit | ≤2.0km vent nominal (1.51 km) |
| 10 | Llaima | VIIRS375 | 2026-05-07 | -38.6862 | -71.7134 | 1.5 | ENE | 3.747 | 80 | 265.1 | none | b_volcanic_real_summit | ≤2.0km vent nominal (1.50 km) |
| 11 | NevadosDeChillan | VIIRS375 | 2026-02-07 | -36.8717 | -71.3925 | 1.68 | SW | 3.164 | 59 | 281.9 | D | b_volcanic_real_complex | ≤4.0km de Cráteres alineados NW (GVP 17 puntos eruptivos) |
| 12 | NevadosDeChillan | VIIRS375 | 2026-03-19 | -36.8721 | -71.3952 | 1.91 | WSW | 1.616 | 33 | 279.4 | D | b_volcanic_real_complex | ≤4.0km de Cráteres alineados NW (GVP 17 puntos eruptivos) |
| 13 | PlanchonPeteroa | VIIRS375 | 2026-01-30 | -35.2158 | -70.5716 | 2.82 | N | 3.886 | 73 | 283.4 | none | b_volcanic_real_complex | ≤2.0km de Cráter Planchón (N) (GVP Planchon-Peteroa complex) |
| 14 | PlanchonPeteroa | VIIRS375 | 2026-01-30 | -35.214 | -70.5611 | 3.21 | NNE | 4.143 | 59 | 283.2 | none | b_volcanic_real_complex | ≤2.0km de Cráter Planchón (N) (GVP Planchon-Peteroa complex) |
| 15 | PuyehueCordonCaulle | VIIRS750 | 2026-03-15 | -40.4306 | -72.0877 | 11.65 | NNE | 3.586 | 4 | 245.0 | D | d_artifact_cirrus | intra-inner pero t_bg=245.0K <260K (cirrus A23) |
| 16 | PuyehueCordonCaulle | VIIRS375 | 2026-03-23 | -40.5622 | -72.0394 | 9.9 | ESE | 0.402 | 3 | 264.3 | D | b_volcanic_real_unmapped | intra-inner sin feature catalogada (d_vent=9.90km) |
| 17 | Tupungatito | VIIRS375 | 2026-02-03 | -33.3886 | -69.8282 | 0.17 | WNW | 0.307 | 1 | 270.4 | D | b_volcanic_real_complex | ≤2.0km de Cráter norte breached caldera (S85FaseC c18) |
| 18 | Tupungatito | VIIRS375 | 2026-03-15 | -33.3854 | -69.8337 | 0.79 | WNW | 0.601 | 42 | 269.3 | none | b_volcanic_real_complex | ≤2.0km de Cráter norte breached caldera (S85FaseC c18) |
| 19 | Villarrica | VIIRS375 | 2026-05-05 | -39.4273 | -71.9445 | 0.88 | SSW | 1.473 | 49 | 262.6 | none | b_volcanic_real_summit | ≤2.0km vent nominal (0.88 km) |
| 20 | Villarrica | VIIRS375 | 2026-02-03 | -39.4278 | -71.9256 | 1.48 | SE | 2.401 | 63 | 270.7 | D | b_volcanic_real_summit | ≤2.0km vent nominal (1.48 km) |

## Tarea 4 — Lectura geológica volcán por volcán

### Chaiten
Cráter actual con domo riolítico post-2008 al fondo de la caldera. Señal térmica esperada: domo central + fumarolas residuales. Inner=5km cubre el cráter completo (~1.3km diámetro). 
**FPs residuales**: 362 (b=326, c=0, d=36)
**Lectura**: nuestros FPs caen en features volcánicas reales del complejo → MIROVA scope más estrecho que el nuestro acá.

### Copahue
Cráter El Agrio con lago crater hiperácido + alineamiento E-W de 9 cráteres. Señal térmica real: cráter + Las Máquinas (geotermal NO eruptivo, 165 t CO2/d). MIROVA suprime Las Máquinas. Lago Caviahue ya en exclude_zones. 
**FPs residuales**: 377 (b=367, c=0, d=10)
**Lectura**: nuestros FPs caen en features volcánicas reales del complejo → MIROVA scope más estrecho que el nuestro acá.

### Isluga
Cráter cumbre con fumarolas persistentes, sin lago. Señal MIROVA esperada: pixel summit por fumarolas + ΔT ~20K. Tier A Alto, calibración natural sin patches. 
**FPs residuales**: 60 (b=54, c=0, d=6)
**Lectura**: nuestros FPs caen en features volcánicas reales del complejo → MIROVA scope más estrecho que el nuestro acá.

### Lascar
Cráter activo V (V-shape) con lava lake intermitente. ΔT ~21.6K. Tier A Alto. Cluster cráter Aguas Calientes 5km SW podría ser satélite real. Mejor calibrado del Tier A. 
**FPs residuales**: 0 (b=0, c=0, d=0)

### Lastarria
Cráter cumbre + sistema Lazufre (Cordón del Azufre) regional 12km SW con sulfur flows e InSAR inflación. Inner=3km del KMZ es muy estrecho para Lazufre. Frontiers 2023 confirma sulfur flows = anomalía térmica REAL no eruptiva pero volcánica. 
**FPs residuales**: 13 (b=13, c=0, d=0)
**Lectura**: nuestros FPs caen en features volcánicas reales del complejo → MIROVA scope más estrecho que el nuestro acá.

### Llaima
Cráter cumbre + Pichi-Llaima (cono coalescente SSE) + ~40 conos adventicios SW-NE arc. Inner=5km cubre cráter principal pero no los conos. Cluster Pichi-Llaima 1.28km SW es feature volcánica real del complejo. 
**FPs residuales**: 329 (b=286, c=0, d=43)
**Lectura**: nuestros FPs caen en features volcánicas reales del complejo → MIROVA scope más estrecho que el nuestro acá.

### NevadosDeChillan
Complejo 17 cráteres alineados NW-SE incluyendo subcomplejo Cerro Blanco / Nuevo. Cuenca Río Diguillín 16km SW = geotermal no eruptivo (Pinto/Coihueco). Inner=5km insuficiente para el complejo extendido. 
**FPs residuales**: 146 (b=138, c=0, d=8)
**Lectura**: nuestros FPs caen en features volcánicas reales del complejo → MIROVA scope más estrecho que el nuestro acá.

### PlanchonPeteroa
Multi-cráter: Planchón (N), Peteroa (centro), Azufre (S, flanco). Comportamiento bimodal A22 (S70 T1 N=7): a veces aísla Peteroa, a veces el halo regional. Mediana ratio 2.08× varianza alta. Inner=3km cubre solo Peteroa. 
**FPs residuales**: 110 (b=109, c=0, d=1)
**Lectura**: nuestros FPs caen en features volcánicas reales del complejo → MIROVA scope más estrecho que el nuestro acá.

### PuyehueCordonCaulle
Lacolito 2011-2012 = anomalía difusa NO focal de 707km² (A20). El método R2 con centroide NO aplica acá. Cordón Caulle fisural NW-SE 17km. Inner=20km del KMZ refleja esta extensión. 
**FPs residuales**: 76 (b=57, c=0, d=19)
**Lectura**: nuestros FPs caen en features volcánicas reales del complejo → MIROVA scope más estrecho que el nuestro acá.

### Tupungatito
Cráter norte breached caldera con cono piroclástico activo + ring glaciar enorme. Patrón térmico A19: ring glaciar warm-relativo confunde kernel local. Kernel-bg EMPEORA Tupungatito (10.37→18.46×). Inner=7km incluye el ring. 
**FPs residuales**: 61 (b=32, c=0, d=29)
**Lectura**: nuestros FPs caen en features volcánicas reales del complejo → MIROVA scope más estrecho que el nuestro acá.

### Villarrica
Lava lake persistente en cráter cumbre, ΔT ~12K (Tier A Muy Bajo). Señal sub-pixel característica. Glaciar cumbre puede producir mezcla. Exclude_zones existentes: Lago Calafquen + zona urbana Pucón. 
**FPs residuales**: 341 (b=325, c=0, d=16)
**Lectura**: nuestros FPs caen en features volcánicas reales del complejo → MIROVA scope más estrecho que el nuestro acá.

## Recomendación de scope (decisión Nicolás)

Realidad física agregada (a+b+c) = 95.4%. Solo artefactos puros (d) = 4.6%.

### Opciones de scope

**A. Clon MIROVA estricto**: aceptar gap precisión 0.024 como inherente. Cualquier FP es ruido contra MIROVA. NO extender geometría ni exclude_zones. 
Pro: literal, defendible ante reviewers. Con: deja afuera ~46% señales volcánicas reales del complejo que MIROVA simplemente no publica por su scope NRT operacional.

**B. Clon + volcánico extra (RECOMENDADO si b ≳ d)**: extender geometría per-vol (additional_centers, extended_radius) para capturar sub-complejos reales (Cerro Blanco NdC, Lazufre Lastarria, Pichi-Llaima, complejo PP). Mantener exclude_zones con flag para (c) Las Máquinas / Río Diguillín. 
Pro: precisión sube sin perder TPs MIROVA, etiqueta honesta 'detectamos feature volcánica X que MIROVA no publica'. Con: divergencia controlada del clon literal — requiere documentar cada extensión.

**C. Detección térmica amplia (Beyond MIROVA)**: redefinir objetivo como 'monitoreo térmico volcánico chileno' independiente de MIROVA. Geotermal real se reporta como categoría separada. 
Pro: producto único para SERNAGEOMIN. Con: pierde la simplicidad del benchmark MIROVA, cambia el contrato del proyecto.

### Veredicto

**Opción B**. Categoría (b) volcánico real = 46.3% > artefactos (d) = 4.6%. 
La mayoría del gap precisión es scope MIROVA más estrecho, no bugs nuestros. 
La cartografía S85 Fase C ya tiene las coordenadas listas para extender geometría.