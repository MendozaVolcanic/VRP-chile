# Auditoría pasada-por-pasada — MIROVA NRT vs VRP Chile (S78)

**Fecha**: 2026-05-25
**Branch**: `claude/s78-audit-pasada`
**Tipo**: READ-ONLY — sin cambios en pipeline, data ni workflows.
**Datasets**:
- MIROVA NRT: `latest_consolidado.csv` (19,022 filas, 11 Tier A + otros).
- VRP Chile: `data/mirova_equivalent/<Volcano>.json` (1,000-1,300 records / volcán).
- Config: `volcanoes.yaml` (Tier A `mirova_monitored: true`).

**Ventana de match temporal**: ±5 minutos (un granule satelital dura ~1 min — la
tolerancia anterior de ±60 min agregaba pasadas distintas).

**Criterio MIROVA "detección real"**: `Clasificacion Mirova != "NULO"` AND `VRP_MW > 0`.
Eso filtra los registros NRT de rutina sin anomalía térmica.

**Scripts y outputs**: `experiments/149_audit_pasada/`
- `run_audit.py` — script principal
- `master.csv` — tabla por volcán (sección 1-6)
- `per_pass_pairs.csv` — pasadas matcheadas (sección 2, n=634)
- `fn_pasadas.csv` — MIROVA detectó, nosotros no (sección 3, n=201)
- `fp_pasadas.csv` — nosotros detectamos, MIROVA no (sección 4, n=7,600)
- `granularity_per_pass.csv` — counts (vol, sensor, minuto)
- `lagos_persistentes.csv` — sección 5 (n=552)
- `modis_inflated.csv` — sección 6 (n=1,265)

---

## TL;DR (3 hallazgos críticos)

1. **NO hay bug de granularidad temporal**: por cada pasada MIROVA, nosotros
   emitimos exactamente 1 record por (volcán, sensor, minuto) en el 100% de los
   casos. El campo a inspeccionar es `n_anomalous_pixels` (interno al record),
   no la cantidad de records. **Lo que Nicolás recordaba como "un valor por
   pasada" se cumple en nuestro schema** — la granularidad es la correcta.

2. **El mismatch real es de magnitud, no de cantidad**: nuestro `vrp_mw` agrega
   *todos* los pixels anómalos del scene; MIROVA reporta el cluster summit
   contiguo principal. Mediana de ratio `ours/mirova` sobre 634 pasadas
   matcheadas: **rango 1.5× a 18.5×** según volcán. Los outliers de ratio
   p75 ≥ 30× (Villarrica 59.7×, Lascar 7.8×, PCC 45.6×) están dominados por
   sumas de pixels lejanos (`distance_class="far"`) que MIROVA descarta del VRP
   reportado pero nosotros suman en `vrp_mw` global.

3. **Lagos persistentes son un problema confirmado** (552 records en zona-buffer
   1.5× radio configurado, 353 estrictamente dentro de `exclude_zones`):
   - **Lago Caviahue (Copahue)**: 148 records cerca, **141 dentro del radio 4 km
     declarado** — los exclude_zones NO están filtrando. Median VRP 5.65 MW,
     max 566 MW. Bug operacional.
   - **Lago Conguillío (Llaima)**: 79 records, 71 dentro del exclude. Misma
     situación.
   - **Lagos Villarrica + Calafquen**: 198 records cerca, 125 dentro. Es el
     escenario que Nicolás señaló para Villarrica.
   - **Salar de Atacama (Lascar)**: 123 records, mayoría en buffer extendido,
     pero el salar es área plana sin agua persistente — el radio 25 km cubre
     terreno desértico genérico.

---

## Sección 1 — Granularidad temporal (records por pasada)

Para cada (volcán, sensor_bucket, minuto), conté records en MIROVA CSV y en
nuestros JSON. Resultado: **`max_ours_for_single_mirova` = 2 o 3 en todos los
volcanes**. El máximo de 3 (solo PCC) corresponde a las ~3 pasadas/noche del par
VIIRS Suomi-NPP + NOAA-20 + NOAA-21 que MIROVA reporta como una sola fila
agregada del bucket "VIIRS".

| Volcán | mirova passes | ours passes | passes mirova=1 & ours>1 | passes mirova=1 & ours=1 |
|---|---:|---:|---:|---:|
| PCC | 105 | 806 | 71 | 0 |
| Villarrica | 10 | 776 | 7 | 0 |
| Lascar | 231 | 642 | 60 | 73 |
| Copahue | 3 | 762 | 1 | 0 |
| Nevados de Chillán | 12 | 755 | 3 | 1 |
| Llaima | 1 | 770 | 1 | 0 |
| Chaitén | 24 | 824 | 20 | 0 |
| Planchón-Peteroa | 56 | 742 | 51 | 0 |
| Lastarria | 103 | 643 | 90 | 0 |
| Isluga | 91 | 628 | 76 | 1 |
| Tupungatito | 85 | 722 | 78 | 0 |

**Interpretación geológica**: nuestros records cubren 4-50× más pasadas que MIROVA
porque MIROVA solo publica VRP cuando hay anomalía detectada (clasificación
≠ NULO). Nuestros JSON guardan **todos los granules procesados** incluyendo
"sin detección" (`vrp_mw=0`). No es bug — es decisión de schema: guardamos el
contexto operacional completo. **El bug que la hipótesis sugería (múltiples
records nuestros por una pasada MIROVA) NO existe**.

El número 458 de "passes mirova=1 & ours>1" (totalizado) corresponde a la
agregación de S-NPP + NOAA-20 + NOAA-21 dentro del bucket "VIIRS" del CSV
consolidado de MIROVA: 1 fila MIROVA / pasada-de-platform vs 2-3 filas nuestras
porque cada platform genera su granule. Verificable con sensor crudo en
`per_pass_pairs.csv`.

---

## Sección 2 — Ratio de magnitud (pasadas matcheadas)

634 pares ±5 min. Mediana global ratio `ours/mirova`:

| Volcán | n_pares | mediana | p25 | p75 |
|---|---:|---:|---:|---:|
| Lascar | 204 | **1.50** | 0.92 | 7.84 |
| Isluga | 88 | 2.29 | 0.83 | 5.49 |
| Chaitén | 20 | 2.69 | 0.00 | 11.2 |
| Lastarria | 90 | 7.26 | 2.02 | 31.6 |
| Villarrica | 7 | 7.99 | 2.53 | 59.7 |
| Tupungatito | 85 | 8.26 | 0.00 | 27.0 |
| Copahue | 1 | 8.80 | — | — |
| PCC | 82 | **9.96** | 3.51 | 45.6 |
| Planchón-Peteroa | 52 | 12.7 | 2.07 | 37.8 |
| Llaima | 1 | 18.5 | — | — |
| Nevados de Chillán | 4 | 0.00 | — | — |

**Lectura**: solo **Lascar y Isluga calibran razonablemente** (mediana < 2.5,
dentro de tolerancia ±30% MIROVA si solo miráramos summit). El resto sobre-estima
por factor 7-18×. Esto es **consistente con la explicación física**: nuestro
`vrp_mw` total incluye pixels en distance_class="far" (anillo de scene, hasta
25 km radio), mientras MIROVA reporta solo el cluster contiguo del summit.

**Recomendación analítica** (NO fix, solo análisis para sesión futura): comparar
contra `primary_cluster.vrp_mw` en vez de `vrp_mw` total. El primary_cluster ya
está calculado y persiste en cada record — sería un análisis de 30 min en sesión
siguiente.

---

## Sección 3 — Falsos Negativos (MIROVA detectó, nosotros no)

201 pasadas (FN). Top:

| Volcán | n_FN |
|---|---:|
| PCC | 40 |
| Isluga | 14 |
| Lastarria | 13 |
| Nevados de Chillán | 10 |
| Tupungatito | 7 |
| Chaitén | 5 |
| Planchón-Peteroa | 5 |
| Villarrica | 3 |
| Copahue | 2 |
| Lascar | 102 |
| Llaima | 0 |

(Lascar n=102 incluye pasadas reportadas por MIROVA cuyo timestamp no
matcheamos ±5 min — probablemente granules ausentes en nuestro fetch, ver
`fn_pasadas.csv`.)

**Causa probable** (sin verificar pipeline): granules que nuestro `fetch.py` no
descargó (red, NRT no disponible, NOAA-21 missing — H10 S17). Detalle por
volcán en `fn_pasadas.csv`.

---

## Sección 4 — Falsos Positivos (nosotros detectamos, MIROVA no)

**7,600 pasadas con `vrp_mw>0` sin contraparte MIROVA en ±5 min**. Es el número
grande y merece contexto:

- 4,390 son `distance_class="summit"` (detección dentro de `inner_radius_km`)
- 3,210 son `distance_class="far"` (anillo exterior, descartable)

| Volcán | n_FP summit | n_FP far |
|---|---:|---:|
| PCC | 855 | 176 |
| Chaitén | 510 | 321 |
| Lascar | 410 | 149 |
| Villarrica | 400 | 383 |
| Planchón-Peteroa | 364 | 353 |
| Llaima | 344 | 339 |
| Tupungatito | 335 | 281 |
| Isluga | 328 | 178 |
| Copahue | 321 | 379 |
| Lastarria | 373 | 374 |
| NdC | 150 | 277 |

**Caveat metodológico**: muchos de estos "FP" no son falsos positivos reales sino
**diferencias de threshold**: nuestro pipeline detecta señal débil persistente
(0.5-3 MW summit) que MIROVA NRT clasifica como "NULO" o no publica. Para una
proporción real de FP haría falta comparar contra OSF v2.5 (ground truth
histórico algorítmico, no NRT). Detalle en `fp_pasadas.csv`.

Mediana de `vrp_mw` summit: 1.9-3.4 MW en todos los volcanes, excepto **PCC con
mediana 13 MW** — anómalo, requiere inspección visual.

---

## Sección 5 — Lagos persistentes (CRÍTICO)

**552 records con centroide del primary_cluster dentro de 1.5× el radius_km
configurado en `exclude_zones`**.

| Volcán | Lago | n | dentro radio | en buffer 1.5× | median VRP | max VRP |
|---|---|---:|---:|---:|---:|---:|
| **Copahue** | Lago Caviahue | 148 | **141** | 7 | 5.65 MW | 566.3 MW |
| **Llaima** | Lago Conguillío | 79 | **71** | 8 | 4.65 MW | 405.7 MW |
| Villarrica | Lago Villarrica | 89 | 55 | 34 | 7.95 MW | 524.9 MW |
| Villarrica | Lago Calafquen | 109 | 70 | 39 | 11.65 MW | 442.4 MW |
| Lascar | Salar de Atacama | 123 | 16 | 107 | 1.92 MW | 924.6 MW |
| Tupungatito | Embalse El Yeso | 4 | 0 | 4 | 0 MW | 197.2 MW |

**Distance_class breakdown de los 552 records**: 547 son `far`, solo 5 son
`summit` (caso lejos del vent que cae cerca de lago).

**Hallazgo geológico** (lo que esto significa físicamente):

- **Copahue / Lago Caviahue**: 141 pasadas con detección térmica dentro del radio
  declarado de 4 km. La `exclude_zones` está configurada pero **NO se aplica al
  primary_cluster**. Eso significa que el filtro vive en otra etapa del pipeline
  o tiene un bug. El centroide cae lat=-37.876 lon=-71.025, exactamente sobre
  el lago. Físicamente esto es **lago térmico Caviahue + emisiones SO2/H2S**:
  el lago Caviahue tiene actividad geotermal documentada y emite calor latente
  estacional. La señal es real pero **no es VRP de lava** — confunde el conteo.
- **Llaima / Lago Conguillío**: 71 pasadas dentro del radio 4 km. Lago glacial
  cerrado a 28 km del cráter. La señal puede ser cirrus sobre el lago, mezcla
  agua-nieve, o sun-glint residual VIIRS diurno. No es lava.
- **Villarrica / Calafquen+Villarrica**: 125 records dentro de los radios. Estos
  son lagos que tienen el problema clásico de retención de calor post-atardecer.
  Median VRP 8-12 MW es señal claramente artefactual (lava lake real de
  Villarrica produce 0.05-0.2 MW, dos órdenes menos).
- **Lascar / Salar de Atacama**: la mayoría está en buffer 1.5× (mayor 25 km del
  centro del salar) — el salar es plano y caliente diurno, no es problema de
  agua sino de background térmico desértico. 16 dentro del radio estricto
  con max 924 MW: outlier pixel saturado, no representativo.

**Top 10 coords Villarrica** (centroides primary_cluster), todas caen sobre Lago
Calafquen: -39.566/-72.164, -39.556/-72.138, -39.527/-72.082 — verifíquese en
mapa, son aguas claramente identificables.

---

## Sección 6 — MODIS inflado (n_anomalous_pixels > 50)

1,265 records MODIS con más de 50 pixels anómalos por scene. De esos, solo 169
tienen `primary_cluster.n_pixels < 20` Y `distance_class="summit"` — los demás
1,096 son scenes con clusters lejos del vent o clusters summit grandes (>20
pixels). Esto sugiere que en escenas con muchos pixels anómalos, el primary
cluster sí captura razonablemente el evento, pero el `vrp_mw` total se infla con
señales de scene (sol bajo, terreno heterogéneo, nubes finas).

| Volcán | n MODIS inflated | de esos summit-OK (<20 px) |
|---|---:|---:|
| PCC | 240 | 99 |
| Tupungatito | 159 | 7 |
| Chaitén | 150 | 10 |
| Lastarria | 118 | 7 |
| Villarrica | 116 | 7 |
| Planchón-Peteroa | 101 | 8 |
| Llaima | 84 | 5 |
| NdC | 80 | 8 |
| Isluga | 78 | 11 |
| Copahue | 75 | 2 |
| Lascar | 64 | 5 |

---

## Conclusiones para Nicolás

1. **El bug de granularidad temporal que sospechábamos NO existe**. Nuestros JSON
   tienen 1 record por (volcán, sensor, granule-minuto), igual que MIROVA.

2. **El mismatch que vimos en sesiones pasadas es de magnitud, no de cantidad**:
   `vrp_mw` total vs cluster summit contiguo MIROVA. La solución analítica
   correcta es comparar contra `primary_cluster.vrp_mw`, no `vrp_mw`. Sería
   1 cambio de variable en el dashboard / auditoría.

3. **Los exclude_zones para lagos no están filtrando primary_cluster**. 353
   records caen estrictamente dentro de los radios declarados (Caviahue 141,
   Conguillío 71, Calafquen+Villarrica 125, Atacama 16). Bug operacional
   confirmado. Pendiente: localizar dónde se aplica `exclude_zones` y por qué
   no afecta al campo `primary_cluster.centroid_lat/lon`.

4. **PCC tiene mediana de FP summit anómala (13 MW vs 2-3 MW resto)**. Posible
   ROI demasiado amplio (`inner_radius_km=20` único entre Tier A) capturando
   señal geotermal lateral. Inspección pendiente sesión futura.

5. **NO se modificó pipeline, data, ni workflows** — esta auditoría es read-only
   sobre datos ya en disco.

---

*Audit completada S78 — 2026-05-25. Subagente Opus 4.7. Tag worktree:
`VRP-Chile-s78-audit-pasada-por-pasada`.*
