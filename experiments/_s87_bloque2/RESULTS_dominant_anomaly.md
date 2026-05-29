# Validación 1:1 anomalía dominante — RESULTADO S87 (Bloque 2 parte 2 + Bloque central)

**Fecha**: 2026-05-29 (S87). **Script**: `dominant_anomaly.py`.
**Datos**: loader canónico `load_mirova_alertas` (CONS∪OCR, distancia resuelta) +
`anomaly_pixels` persistidos en `data/mirova_equivalent/*.json` (11 Tier A).
**Ventana**: 2026-01-29 → 2026-05-28.

## Pregunta (refinamiento Nicolás S86)

Para cada pasada satelital donde MIROVA reporta SU mayor anomalía a una distancia
D_mirova del centro de referencia, ¿la mayor anomalía que NOSOTROS reportamos cae
en el mismo punto (gap ≤2 km)?

A/B **offline** de tres criterios de selección (sin reproceso — los pixels crudos
están persistidos):
- **vent_anchored**: el `primary_cluster` que el pipeline ya elige (S38 D8 fix).
- **vrp_max**: el cluster de mayor VRP de toda la escena (lo que MIROVA hace).
- **vrpmax_in**: el cluster de mayor VRP **dentro** del `inner_radius`.

Distancias: TODAS recalculadas desde `mirova_center` del volcanoes.yaml (comparable
con MIROVA ≈ Smithsonian GVP). Hallazgo de schema (A3): `anomaly_pixels.dist_km`
mide desde mirova_center; `primary_cluster.centroid_dist_km` mide desde vent. NO
mezclar — el script recalcula todo desde mirova_center.

## Resultado (tol = 2 km)

| Volcán | n | vent_anchored | vrp_max | vrpmax_in |
|---|---:|---:|---:|---:|
| Lastarria | 87 | **98.9%** | 41.4% | 83.9% |
| PlanchonPeteroa | 53 | **94.3%** | 62.3% | 90.6% |
| Chaiten | 16 | **93.8%** | 87.5% | 87.5% |
| Villarrica | 11 | **90.9%** | 54.5% | 90.9% |
| Isluga | 74 | **83.8%** | 58.1% | 74.3% |
| NevadosDeChillan | 5 | 80.0% | 60.0% | 80.0% |
| Tupungatito | 57 | **77.2%** | 40.4% | 61.4% |
| Lascar | 159 | **67.3%** | 49.1% | 65.4% |
| PuyehueCordonCaulle | 62 | 25.8% | 24.2% | 25.8% |
| Llaima | 3 | 33.3% | 33.3% | 33.3% |
| Copahue | 2 | 0.0% | 0.0% | 0.0% |

**Global ponderado (n=529)**: vent_anchored **74.7%** · vrp_max 47.7%.
**Global sin PCC (difuso) y n≥10 (n=457)**: vent_anchored **81.8%**.

> **Nota (ver §4)**: el 74.7% es un **piso**. La columna vent_anchored lee el
> `primary_cluster` persistido, que mezcla records pre-S38 (estrategia vieja
> `vrp_max`, no reprocesados) y post-S38 (`vent_anchored` real). Los records
> históricos con bug `vrp_max` (Lascar feb eruptivo) tiran el promedio hacia
> abajo. El pipeline **actual** matchea mejor; validación limpia requiere
> reproceso histórico con config vigente (S88).

## Conclusiones

### 1. El criterio de selección actual (vent_anchored) es el correcto — A/B con datos

vent_anchored gana sobre vrp_max en **9/11 volcanes** (empata en los 2 de n<4). En
Lastarria 98.9% vs 41.4%; PlanchonPeteroa 94.3% vs 62.3%; Tupungatito 77.2% vs
40.4%. **Cambiar a vrp_max empeoraría el match en casi todos.** Esto **refuta la
hipótesis del experimento L preliminar** (S86), que proponía evaluar `vrp_max_inner`
o re-anclar como fix. El A/B muestra que el pipeline ya elige bien.

Mecanismo físico: MIROVA, en vols de cráter compacto (la mayoría), reporta la
anomalía pegada al centro de referencia. vent_anchored hace lo mismo (prioriza
proximidad al vent). vrp_max, en cambio, se va al cluster de mayor VRP que durante
saturación/erupción o sobre campos dispersos cae lejos del cráter → diverge.

### 2. Validación positiva fuerte del pipeline

En los volcanes de cráter compacto (Lastarria, PP, Chaitén, Villarrica, Isluga) el
match es **84-99%**: nuestra anomalía dominante = la de MIROVA en la gran mayoría de
pasadas. El pipeline reporta la misma ubicación que MIROVA donde el fenómeno es
puntual.

### 3. PCC (25.8%) NO es bug de selección — es un campo térmico difuso

Ambos criterios dan casi igual (25.8% vs 24.2%): la divergencia **no** depende del
cluster elegido. El sistema Puyehue–Cordón Caulle tiene un lacolito difuso de ~707
km² (A20, A24). VIIRS a 375 m **resuelve** ese campo extendido en muchos focos
dispersos sobre ~40 km; MIROVA (resolución más gruesa + su criterio de cluster) lo
**colapsa** a un punto (~7.7 km). Una pasada típica (2026-02-02 VIIRS_SNPP): 100
pixels en 6+ clusters a 6-20 km; el de mayor VRP a 18.8 km, MIROVA a 7.7 km.
**Categoría (b) del marco S86** — feature volcánica real no priorizada por MIROVA.
No forzar un fix (violaría clon + A55). El experimento L preliminar (0%) era un
artefacto de comparar radialmente solo OCR/VIIRS sin reconstruir escena.

### 4. Lascar (67.3%): NO es bug del pipeline actual — es deuda de datos históricos pre-S38

De 52 no-match Lascar: 13 son MIROVA-halo ~3.3 km vs nuestro cráter ~0.5 km
(divergencia física menor); **31 son eventos eruptivos MODIS feb-2026** donde el
`primary` en disco está a 18-29 km con VRP inflado (142, 109 MW) mientras MIROVA
reporta el cráter a ~1 km.

**Causa raíz (investigada S87, NO es el pipeline actual)**: `vent_anchored` se adoptó
en `mirova_equivalent.yaml` el **2026-05-12 (S38 Bloque B)**. Los records de febrero
son anteriores → se generaron con la estrategia vieja `vrp_max` (elige el cluster de
mayor VRP de escena, que durante una erupción MODIS off-nadir cae lejos del cráter por
pixels saturados dispersos, A36). El NRT solo procesa el día actual, así que esos
records históricos **nunca se reprocesaron** y conservan el primary lejano.

**Verificación con corte temporal** (records post-2026-05-12 = pipeline actual):
los 5 no-match post-S38 de Lascar tienen `vent_anchored` eligiendo correctamente el
cráter/borde (3.6, 5.8 km en MODIS; 0.8-0.9 km en VIIRS) — **NO** los 18-29 km de
febrero. El bug catastrófico desaparece con la config actual; los residuales son gaps
chicos (~2-4 km, MIROVA reporta un halo a ~3.5 km mientras nosotros apuntamos al
cráter).

**Lección metodológica**: el experimento lee el `primary_cluster` tal como quedó
persistido, que **mezcla épocas de estrategia** (pre/post-S38). El "67% de Lascar" es
un piso contaminado por records históricos con bug `vrp_max`, NO un problema del
pipeline actual. Para una validación limpia del estado actual haría falta **reprocesar
la ventana completa con la config vigente** (reproceso histórico local, no GH Actions
por timeout — regla S15). **Candidato S88**: reproc histórico Lascar feb-2026 con
config actual → los 31 records eruptivos pasarían a apuntar al cráter.

### 5. Tupungatito (77%) y Chaitén (94%) — Frente D: gaps ~3 km son referencia/dispersión, no error

Investigación de la dirección (bearing) de nuestra anomalía dominante desde el
`mirova_center`:

- **Tupungatito**: nuestro primary apunta consistentemente al cráter (bearing
  mediano 322° ≈ el del vent 330°), pero queda a ~5.4 km del `mirova_center`
  **porque el mirova_center está a 4.86 km del cráter activo** (offset KMZ confirmado
  en `AUDIT_INTEGRAL_S81.md:154` — "3 km SE" era subestimación humana). El
  `mirova_center` ≈ coord GVP nominal (-33.4,-69.8); el cráter activo está al NW. El
  gap de distancia vs MIROVA es por **qué punto se usa para medir** (centro de
  grilla/GVP, regla A13), NO por error de ubicación. **Resuelve C3 de la auditoría
  S86.** Las divergencias residuales son su régimen Muy Bajo (ΔT chico) + ring
  glaciar (A19).
- **Chaitén**: `mirova_center` bien centrado (0.24 km del vent). Los pocos no-match
  son dispersión real del domo (bearing variable, MIROVA reporta a ~2.8-3.1 km
  actividad dispersa del complejo) — categoría (b), no offset.

## Premisa del plan refutada (Bloque 2 parte 2)

El bloque de arranque predijo "rehacer el cruce TP/FP con el loader → gap precisión
≤0.5". **Verificado falso con datos**: el cruce S86 (`script_C`) **ya unía CONS∪OCR**.
El "subconteo MIROVA ~45%" del Subagente F es a nivel de **pasada individual** (loader
977 vs solo-CONS 654 = +49%), pero el cruce de precisión opera a nivel **noche local**,
donde múltiples pasadas colapsan: el loader da 606 noche-ALERTA keys vs 556 de
script_C = **+9%** (parte por ventana). Rehacer el cruce binario subiría TP de ~556 a
~606 noches; los 1.523 FP (95% realidad física, marco S86) no se mueven. El gap
precisión 0.243 es genuino y se explica por el marco fundacional, no por un bug de
conteo del cruce.

## Fix de correctitud aplicado al loader

`pipeline/mirova_csv_loader.py`: OCR sin patrón de distancia en `Nota_Validacion` →
`dist_km = None` (antes heredaba el `0.0` de `Distancia_km`, que en OCR es "no
informado"). Impacto en el análisis: 13/532 filas (2.4%), conclusiones idénticas.
+2 tests (`test_load_ocr_sin_distancia_es_none`, `test_load_cons_usa_distancia_km`),
suite loader 22 passed.

## Escudo anti-drift respetado

- NO se cambió el criterio de selección (vent_anchored validado como óptimo).
- NO se tocó pipeline NRT (`process_*.py`, `store.py`, `clustering.py`) — análisis
  100% offline. Sin tag defensivo necesario (A45 no disparada).
- NO huella como gate. NO exclude_zones. NO gate intra-radio.
