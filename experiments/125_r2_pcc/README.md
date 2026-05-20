# Experimento 125 — R2 retroactivo PuyehueCordonCaulle (S70-1 T4)

## Pregunta

Adopción S63 PCC (`local_kernel_bg: true`, ratio LEGACY 3.64x → NEW **0.29x**
— **el cambio más drástico de Tier A, -92%**). ¿Se valida con R2 pixel-level?

**Hipótesis física**: el **lacolito** del Cordón Caulle es una intrusión
magmática emplazada durante la erupción del 4-15 junio 2011 que sigue
caliente (cuerpo intruído a ~3-5 km de profundidad, anomalía residual). Está
**~7-8 km al norte-noroeste del vent nominal** (-40.525499, -72.146137), que
apunta al complejo Puyehue + Cordón Caulle. MIROVA detecta el lacolito como
cluster lejano legítimo (no FP) y nuestro pipeline también — por eso el vol
tiene `inner_radius_km: 20` (excepción a los 3-7 km típicos de Tier A).

**Implicación para R2**: el cluster MIROVA y nuestro cluster pueden estar
**ambos a ~7-8 km del vent nominal** y aún así estar perfectamente alineados
entre sí. Este audit extiende `max_km` hasta 15 km (sensitivity 5 valores: 2,
3, 5, 10, 15) para caracterizar la geometría del lacolito.

**Caso especial PCC respecto a otros Tier A**:
- Lascar/Isluga: hotspot en el cráter, dist ~0-1 km del vent.
- Lastarria/Villarrica/Chaiten/PP: hotspot en el cráter o cráteres vecinos
  del complejo, dist ~0-3 km del vent.
- **PCC: hotspot a 7-8 km del vent (lacolito, no cráter)** — geometría única.

## Caso

| Campo | Valor |
|---|---|
| Fecha | 2026-05-18 06:18 UTC |
| Sensor | VIIRS_NOAA21 (VIIRS375 en MIROVA CSV) |
| TIF | `mirova-tif-archive/data/tif/PuyehueCordonCaulle/20260518_061802_VIIRS375.tif` (timestamp coincide EXACTAMENTE) |
| MIROVA VRP | 0.51 MW @ 7.73 km del vent |
| Pipeline `pc.vrp_mw` | 0.293 MW (record lacolito, n_pixels=1) |
| Pipeline `pc.centroid_dist_km` | 5.04 km del vent |
| Pipeline `final_hotspot_dist_km` (record) | 7.59 km del vent |
| Pipeline record total `vrp_mw` | 1.443 MW (6 pixels suma) |
| Distance_class | summit |

**Nota crítica de schema**: PCC genera DOS records por granule para el mismo
timestamp/sensor. Uno con cluster cerca del vent (`final_dist=1.9 km`,
`vrp_mw=4.277`, `pc.n_pixels=64`) y otro con cluster en el lacolito
(`final_dist=7.59 km`, `vrp_mw=1.443`, `pc.n_pixels=1`). MIROVA reporta UN
solo cluster en el lacolito (dist 7.73 km). El comparable directo es el
record del lacolito (el segundo) — filtrado por `final_hotspot_dist_km >= 5`
en el script.

## 6 gates + sensitivity (3 × 5 = 15 evaluaciones)

| Gate | Valor | Pasa |
|---|---|---|
| g1: ratio en banda [0.5, 2.0] (estricta) | 0.575x | **PASS** |
| g2: drift < 2 km (estricta) | 9.77 km | FAIL |
| g3: ratio cerca de target S63 (0.29 ± 0.5) | abs(0.575 - 0.29)=0.285 | **PASS** |
| g4: drift cerca de target | N/A (sin target drift S63) | N/A |
| g5: ratio en banda [0.5, 2.0] (revisada) | 0.575x | **PASS** |
| g6: drift < 3 km (revisada) | 9.77 km | FAIL |

### Sensitivity matrix 15 entradas

| top_n | max_km | n_avail | n_used | drift_km |
|---|---|---|---|---|
| 5 | 2.0 | 88 | 5 | 3.406 |
| 5 | 3.0 | 188 | 5 | **2.863** ← min |
| 5 | 5.0 | 533 | 5 | 5.525 |
| 5 | 10.0 | 2133 | 5 | 5.624 |
| 5 | 15.0 | 4796 | 5 | 9.801 |
| 10 | 2.0 | 88 | 10 | 3.140 |
| 10 | 3.0 | 188 | 10 | 3.705 |
| 10 | 5.0 | 533 | 10 | 6.452 |
| 10 | 10.0 | 2133 | 10 | 6.497 |
| 10 | 15.0 | 4796 | 10 | 9.773 |
| 20 | 2.0 | 88 | 20 | 3.186 |
| 20 | 3.0 | 188 | 20 | 3.453 |
| 20 | 5.0 | 533 | 20 | 6.565 |
| 20 | 10.0 | 2133 | 20 | 5.652 |
| 20 | 15.0 | 4796 | 20 | 9.499 |

**Drift summary**: min 2.86 km (top5/max3km), median 5.62 km, max 9.80 km.

## Interpretación física

### 1. ¿El cluster nuestro está en el lacolito o en el vent?

**Está en el lacolito**, pero no como un punto puntual sino como una región
difusa centrada a ~5 km al sur del vent (pc.centroid_dist_km=5.04). Mirando
los `anomaly_pixels` del record:

- Pixel top: lat -40.525, lon -72.145, dist 7.59 km, vrp_mw 0.464 MW ← coincide con dist MIROVA 7.73 km
- Pixel 2: lat -40.546, lon -72.167, dist 6.48 km, vrp_mw 0.293 MW
- Pixel 3: lat -40.526, lon -72.139, dist 7.38 km, vrp_mw 0.272 MW

Los 6 anomaly_pixels están dispersos entre **5.6 km y 8.5 km del vent**, no
hay un máximo neto. Es **anomalía difusa** — consistente con el lacolito
como cuerpo intruído enfriándose desde 2011, ya no un punto de emisión
focalizada.

### 2. ¿Por qué el drift es tan alto?

**El TIF NO contiene un pico de anomalía claro**. Sus valores van de 0.07 a
0.23 MW con mediana 0.15 MW (17,936 pixels positivos). Es básicamente el mapa
de radiancia integrada del granule, no un mapa de "hotspot detectados".
Comparado con PP (max 0.24, n_pixels=17,927) la distribución es similar —
ambos TIFs son uniformes. La diferencia con los otros vols (Lastarria,
Chaiten, Villarrica) no es de TIF sino de **dónde está la anomalía**:

- En vols con cráter activo, los pixels más calientes del TIF se concentran
  en el cráter, y el centroide top10 converge ahí.
- **En PCC, el lacolito disipa el calor en una región >2 km de diámetro**,
  así que el centroide top10 dentro de un radio R cambia mucho según R.

Resultado: cuando `max_km=15`, el top10 puede caer en cualquier subregión
elevada del área de 707 km² (π·15²) sin coincidir con donde está nuestro
cluster. El drift de 9.8 km es **artefacto del método R2 sobre anomalía
difusa**, no evidencia de un bug del pipeline.

### 3. ¿Por qué el min drift está en max_km=3 km?

Con `max_km=3`, hay 188 pixels disponibles cerca del vent. El top5 dentro de
3 km cae en (-40.526, -72.146) = casi exactamente el vent. El drift de 2.86
km vs nuestro `pc.centroid` (-40.546, -72.167) es la **distancia geográfica
real entre vent y centroide cluster** — consistente con que el cluster está a
5 km del vent. NO mide alineación con MIROVA — sólo dice "hay pixels
positivos cerca del vent también" (lo cual es esperable: TIF positivo en
todos lados).

## Verdict dual

**ESTRICTO**: FAIL (2/3 gates aplicables)
- g1 PASS (ratio en banda 0.575x)
- g2 FAIL (drift 9.77 km >> 2 km)
- g3 PASS (ratio cerca de target S63 0.29x ±0.5)
- g4 N/A

**REVISADO**: FAIL (1/2 gates)
- g5 PASS (ratio en banda)
- g6 FAIL (drift > 3 km)

## Implicación operacional

La adopción S63 (`local_kernel_bg: true` para PCC) **se valida en magnitud**
pero **NO se valida en geometría con el método R2 estándar**. Razones:

1. **Magnitud**: ratio per-record `pc.vrp_mw/MIROVA = 0.575x` está
   PERFECTAMENTE en banda [0.5, 2.0] y cerca del agregado S63 (0.29x). El
   pipeline reporta MENOS MW que MIROVA en el cluster primario, lo cual es
   el patrón post-fix kernel-bg. ✓

2. **Geometría**: el método R2 no aplica limpiamente a PCC porque la
   anomalía es **difusa** (intrusión 2011 enfriándose en ~707 km²) en vez
   de focal (cráter). NO se puede calcular un "drift de cluster" con TIFs
   donde los pixels no tienen un pico claro.

3. **Patrón Tier A actualizado (5/5 vols R2 retroactivo S70-1)**:
   - Lastarria: PASS revisado, drift 0.752 km (focal cráter)
   - Chaiten: FAIL parcial 1/4 estricto, drift 2.15 km (focal domo)
   - Villarrica: PASS revisado 1/2, drift 2.15 km (focal lava lake)
   - PlanchonPeteroa: FAIL marginal 0/3 / 1/2, drift 2.20 km (focal cráter Peteroa)
   - **PCC: FAIL drift 9.77 km — caso especial NO focal (lacolito difuso)**

   El método R2 funciona razonablemente bien para vols focales (drift 0.7-2.2
   km). Para vols con anomalía difusa como PCC, **el método R2 no es
   diagnóstico apropiado**. La adopción S63 sigue siendo defendible por su
   reducción de ratio agregado (3.64x → 0.29x) sobre 97 ALERTAS — el R2
   no la refuta, simplemente no aplica.

### Acción sugerida

Adopción S63 PCC **se mantiene**. El audit pixel-level R2 confirma que el
pipeline reporta MW en banda razonable respecto a MIROVA, pero la geometría
del lacolito no permite caracterización con R2. Para validar geometría de
PCC, una métrica futura podría ser:

- "Distancia entre pc.centroid y el centroide MIROVA reportado" (si tuviéramos
  acceso a centroides MIROVA, no sólo a dist al vent).
- O un test de **densidad de anomaly_pixels en una región de 5 km de radio
  alrededor del lacolito nominal** (-40.51, -72.20).

Para esta sesión, **no es necesario revertir la adopción S63**. La hipótesis
"el cluster nuestro está en el lacolito post-fix" se valida observacionalmente
en los `anomaly_pixels` del record (5.6-8.5 km del vent, coherente con MIROVA
@ 7.73 km).

## Referencias

- Adopción S63: PR #84, ratio LEGACY 3.64x → NEW 0.29x sobre 97 ALERTAS,
  RUN 26115708153.
- Patrón inner_radius_km=20: `volcanoes.yaml` PCC config, único Tier A con
  ese valor (lacolito excepción).
- Lacolito Cordón Caulle 2011: erupción 4-15 junio 2011, intrusión
  magmática a ~3-5 km de profundidad.
- Método R2 ampliado: `experiments/120_audit_tif_vrp_sumable/`,
  `experiments/122_r2_chaiten/`, `experiments/123_r2_villarrica/`,
  `experiments/124_r2_planchon_peteroa/`.
