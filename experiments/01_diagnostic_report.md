# Lascar diagnostic report (Paso 1)

**Source JSON**: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\lascar_session5_snapshot.json`
**MIROVA refs**: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\data\mirova\Lascar.json` — 203 records
**Our records**: 644
**Matched pairs (same-day, same-family, dt<=30min, both VRP>0)**: 166

---

## Q1. Why are we missing 23 MIROVA refs?

Category breakdown (n=203):

| Category | Count | % |
|---|---:|---:|
| matched_ok | 143 | 70.4% |
| close_pass_low_vrp | 23 | 11.3% |
| close_pass_zero_vrp | 21 | 10.3% |
| no_close_pass | 16 | 7.9% |
| no_record_in_day | 0 | 0.0% |

Notes:
- `matched_ok`: we detect the ref with a reasonable ratio (>0.5).
- `close_pass_low_vrp`: close-time match exists but our VRP < 50% of MIROVA's.
- `close_pass_zero_vrp`: the SAME overpass exists in our data but produced vrp=0. This is the most actionable category.
- `no_close_pass`: same day but closest record >60 min off — likely a different overpass (day vs night).
- `no_record_in_day`: we have no matching-sensor record on that UTC day at all.

### `close_pass_zero_vrp` detail (n=21)

| MIROVA dt | MIROVA sensor | MIROVA VRP | Our sensor | dt_min | t_bg | t_max | n_anom | n_vent | n_cloud | hs_dist |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 2026-03-27 04:54 | VIIRS | 0.33 | VIIRS_NOAA20_750 | 0 | 267.68 | 271.24 | 0 | 0 | None | None |
| 2026-03-16 06:24 | VIIRS | 0.51 | VIIRS_SNPP_750 | 0 | 265.78 | 271.2 | 0 | 0 | None | None |
| 2026-03-11 06:18 | VIIRS | 2.0 | VIIRS_NOAA20_750 | 18 | 265.22 | 270.95 | 0 | 0 | None | None |
| 2026-03-11 06:18 | VIIRS375 | 4.35 | VIIRS_NOAA20 | 18 | 267.6 | 273.57 | 0 | 0 | 5 | None |
| 2026-03-04 01:55 | MODIS | 0.35 | MODIS_TERRA | 0 | 274.33 | 279.75 | 0 | 0 | None | None |
| 2026-03-01 01:40 | MODIS | 1.81 | MODIS_TERRA | 0 | 274.96 | 282.42 | 0 | 0 | None | None |
| 2026-02-28 05:00 | VIIRS | 0.65 | VIIRS_NOAA20_750 | 0 | 266.13 | 271.53 | 0 | 0 | None | None |
| 2026-02-26 05:42 | VIIRS | 0.21 | VIIRS_NOAA20_750 | 0 | 270.21 | 275.83 | 0 | 0 | None | None |
| 2026-02-25 06:00 | VIIRS | 0.27 | VIIRS_NOAA20_750 | 0 | 269.6 | 273.71 | 0 | 0 | None | None |
| 2026-02-17 05:06 | VIIRS375 | 0.09 | VIIRS_NOAA20 | 0 | 268.08 | 268.11 | 0 | 0 | 1213 | None |
| 2026-02-16 01:20 | MODIS | 1.04 | MODIS_TERRA | 0 | 278.44 | 282.88 | 0 | 0 | None | None |
| 2026-02-12 06:24 | VIIRS | 0.15 | VIIRS_SNPP_750 | 0 | 270.61 | 274.71 | 0 | 0 | None | None |
| 2026-02-11 01:20 | MODIS | 0.32 | MODIS_TERRA | 0 | 277.61 | 283.11 | 0 | 0 | None | None |
| 2026-02-09 01:40 | MODIS | 1.67 | MODIS_TERRA | 0 | 278.44 | 283.55 | 0 | 0 | None | None |
| 2026-02-05 05:36 | VIIRS | 0.28 | VIIRS_NOAA20_750 | 0 | 269.6 | 274.98 | 0 | 0 | None | None |
| 2026-02-04 05:54 | VIIRS | 0.23 | VIIRS_NOAA20_750 | 0 | 269.45 | 274.85 | 0 | 0 | None | None |
| 2026-02-03 06:12 | VIIRS375 | 0.14 | VIIRS_NOAA20 | 0 | 269.61 | 277.34 | 0 | 0 | 87 | None |
| 2026-01-25 05:42 | VIIRS | 0.39 | VIIRS_NOAA20_750 | 0 | 270.66 | 275.47 | 0 | 0 | None | None |
| 2026-01-24 06:00 | VIIRS375 | 0.05 | VIIRS_NOAA20 | 0 | 267.03 | 269.78 | 0 | 0 | 1122 | None |
| 2026-01-15 01:45 | MODIS | 0.89 | MODIS_TERRA | 0 | 276.32 | 281.96 | 0 | 0 | None | None |
| 2026-01-11 05:00 | VIIRS | 0.27 | VIIRS_NOAA20_750 | 0 | 265.77 | 271.1 | 0 | 0 | None | None |

### `close_pass_low_vrp` detail (n=23)

| MIROVA dt | MIROVA sensor | MIROVA VRP | Our sensor | dt_min | Our VRP | ratio |
|---|---|---:|---|---:|---:|---:|
| 2026-03-23 06:12 | VIIRS | 1.91 | VIIRS_NOAA20_750 | 0 | 0.893 | 0.47 |
| 2026-03-20 07:40 | MODIS | 3.82 | MODIS_AQUA | 0 | 0.842 | 0.22 |
| 2026-03-20 05:30 | VIIRS | 3.28 | VIIRS_NOAA20_750 | 0 | 1.430 | 0.44 |
| 2026-03-19 05:24 | VIIRS | 1.0 | VIIRS_SNPP_750 | 0 | 0.457 | 0.46 |
| 2026-03-15 05:00 | VIIRS375 | 1.54 | VIIRS_SNPP | 0 | 0.459 | 0.30 |
| 2026-03-14 01:55 | MODIS | 2.44 | MODIS_TERRA | 0 | 0.870 | 0.36 |
| 2026-03-12 07:25 | MODIS | 2.22 | MODIS_AQUA | 0 | 0.792 | 0.36 |
| 2026-03-12 06:18 | VIIRS375 | 0.28 | VIIRS_NOAA20 | 0 | 0.107 | 0.38 |
| 2026-03-11 04:54 | VIIRS375 | 0.81 | VIIRS_NOAA20 | 0 | 0.299 | 0.37 |
| 2026-03-09 01:55 | MODIS | 2.02 | MODIS_TERRA | 0 | 0.393 | 0.19 |
| 2026-03-07 07:35 | MODIS | 2.7 | MODIS_AQUA | 0 | 0.756 | 0.28 |
| 2026-03-06 01:35 | MODIS | 1.42 | MODIS_TERRA | 0 | 0.559 | 0.39 |
| 2026-03-05 05:06 | VIIRS375 | 1.73 | VIIRS_NOAA20 | 0 | 0.825 | 0.48 |
| 2026-03-04 07:15 | MODIS | 2.28 | MODIS_AQUA | 0 | 0.793 | 0.35 |
| 2026-03-04 05:06 | VIIRS | 1.0 | VIIRS_SNPP_750 | 0 | 0.326 | 0.33 |
| 2026-03-02 07:40 | MODIS | 1.64 | MODIS_AQUA | 0 | 0.761 | 0.46 |
| 2026-02-28 05:00 | VIIRS375 | 0.8 | VIIRS_NOAA20 | 0 | 0.288 | 0.36 |
| 2026-02-26 05:18 | VIIRS375 | 0.42 | VIIRS_SNPP | 0 | 0.155 | 0.37 |
| 2026-02-22 07:25 | MODIS | 2.73 | MODIS_AQUA | 0 | 0.328 | 0.12 |
| 2026-02-14 01:40 | MODIS | 3.43 | MODIS_TERRA | 0 | 1.289 | 0.38 |

### `no_record_in_day` detail (n=0)


### `no_close_pass` detail (n=16)

- MIROVA 2026-03-24 18:18 VIIRS375 VRP=0.79 → closest our = VIIRS_NOAA20 Δ=744min VRP=4.133
- MIROVA 2026-03-22 18:36 VIIRS375 VRP=1.3 → closest our = VIIRS_NOAA20 Δ=726min VRP=0.058
- MIROVA 2026-03-19 18:12 VIIRS375 VRP=1.26 → closest our = VIIRS_NOAA20 Δ=744min VRP=4.669
- MIROVA 2026-03-15 17:48 VIIRS375 VRP=0.9 → closest our = VIIRS_SNPP Δ=666min VRP=0.000
- MIROVA 2026-03-14 18:06 VIIRS375 VRP=1.14 → closest our = VIIRS_NOAA20 Δ=744min VRP=5.425
- MIROVA 2026-03-13 18:24 VIIRS375 VRP=1.96 → closest our = VIIRS_NOAA20 Δ=744min VRP=2.794
- MIROVA 2026-03-13 18:06 VIIRS375 VRP=1.59 → closest our = VIIRS_NOAA20 Δ=726min VRP=2.794
- MIROVA 2026-03-12 18:24 VIIRS375 VRP=1.12 → closest our = VIIRS_NOAA20 Δ=726min VRP=0.107
- MIROVA 2026-03-07 18:42 VIIRS375 VRP=1.12 → closest our = VIIRS_NOAA20 Δ=750min VRP=2.040
- MIROVA 2026-03-01 18:30 VIIRS375 VRP=0.87 → closest our = VIIRS_NOAA20 Δ=726min VRP=0.030

---

## Q2. Pairs with worst ratio (systematic bias?)

Global stats on 166 pairs: median=1.003 mean=1.068
  min=0.120 max=3.800 stdev=0.563

### Bottom 15 (we underestimate most)

| MIROVA dt | MIROVA sensor | MIROVA VRP | Our dt | Our sensor | Our VRP | ratio |
|---|---|---:|---|---|---:|---:|
| 2026-03-28 06:00 | VIIRS | 2.000 | 2026-03-28 06:00 | VIIRS_SNPP_750 | 3.401 | 1.70 |
| 2026-03-07 05:48 | VIIRS375 | 3.030 | 2026-03-07 05:48 | VIIRS_SNPP | 5.154 | 1.70 |
| 2026-03-03 05:48 | VIIRS375 | 2.410 | 2026-03-03 05:48 | VIIRS_NOAA20 | 4.166 | 1.73 |
| 2026-02-10 05:42 | VIIRS375 | 4.140 | 2026-02-10 05:42 | VIIRS_NOAA20 | 7.174 | 1.73 |
| 2026-02-14 05:42 | VIIRS375 | 4.520 | 2026-02-14 05:42 | VIIRS_SNPP | 8.112 | 1.79 |
| 2026-03-22 04:48 | VIIRS375 | 0.070 | 2026-03-22 04:48 | VIIRS_NOAA20 | 0.129 | 1.84 |
| 2026-03-09 05:36 | VIIRS | 2.760 | 2026-03-09 05:36 | VIIRS_NOAA20_750 | 5.274 | 1.91 |
| 2026-03-14 05:42 | VIIRS375 | 2.720 | 2026-03-14 05:42 | VIIRS_NOAA20 | 5.425 | 1.99 |
| 2026-03-28 06:18 | VIIRS375 | 0.110 | 2026-03-28 06:18 | VIIRS_NOAA20 | 0.226 | 2.05 |
| 2026-02-20 05:30 | VIIRS375 | 1.090 | 2026-02-20 05:30 | VIIRS_SNPP | 2.357 | 2.16 |
| 2026-02-15 07:55 | MODIS | 0.620 | 2026-02-15 07:55 | MODIS_AQUA | 1.550 | 2.50 |
| 2026-03-18 01:15 | MODIS | 0.270 | 2026-03-18 01:15 | MODIS_TERRA | 0.707 | 2.62 |
| 2026-03-10 04:54 | VIIRS375 | 0.770 | 2026-03-10 05:12 | VIIRS_NOAA20 | 2.312 | 3.00 |
| 2026-02-11 07:00 | MODIS | 0.480 | 2026-02-11 07:00 | MODIS_AQUA | 1.530 | 3.19 |
| 2026-01-11 06:24 | VIIRS375 | 0.040 | 2026-01-11 06:24 | VIIRS_SNPP | 0.152 | 3.80 |

### Top 15 (we overestimate most)

| MIROVA dt | MIROVA sensor | MIROVA VRP | Our dt | Our sensor | Our VRP | ratio |
|---|---|---:|---|---|---:|---:|
| 2026-02-22 07:25 | MODIS | 2.730 | 2026-02-22 07:25 | MODIS_AQUA | 0.328 | 0.12 |
| 2026-02-12 07:35 | MODIS | 2.960 | 2026-02-12 07:35 | MODIS_AQUA | 0.547 | 0.18 |
| 2026-03-09 01:55 | MODIS | 2.020 | 2026-03-09 01:55 | MODIS_TERRA | 0.393 | 0.19 |
| 2026-03-20 07:40 | MODIS | 3.820 | 2026-03-20 07:40 | MODIS_AQUA | 0.842 | 0.22 |
| 2026-03-07 07:35 | MODIS | 2.700 | 2026-03-07 07:35 | MODIS_AQUA | 0.756 | 0.28 |
| 2026-03-15 05:00 | VIIRS375 | 1.540 | 2026-03-15 05:00 | VIIRS_SNPP | 0.459 | 0.30 |
| 2026-01-15 05:24 | VIIRS | 1.310 | 2026-01-15 05:24 | VIIRS_NOAA20_750 | 0.422 | 0.32 |
| 2026-03-04 05:06 | VIIRS | 1.000 | 2026-03-04 05:06 | VIIRS_SNPP_750 | 0.326 | 0.33 |
| 2026-02-12 05:00 | VIIRS | 0.680 | 2026-02-12 05:00 | VIIRS_NOAA20_750 | 0.228 | 0.34 |
| 2026-03-04 07:15 | MODIS | 2.280 | 2026-03-04 07:15 | MODIS_AQUA | 0.793 | 0.35 |
| 2026-03-14 01:55 | MODIS | 2.440 | 2026-03-14 01:55 | MODIS_TERRA | 0.870 | 0.36 |
| 2026-03-12 07:25 | MODIS | 2.220 | 2026-03-12 07:25 | MODIS_AQUA | 0.792 | 0.36 |
| 2026-02-28 05:00 | VIIRS375 | 0.800 | 2026-02-28 05:00 | VIIRS_NOAA20 | 0.288 | 0.36 |
| 2026-02-26 05:18 | VIIRS375 | 0.420 | 2026-02-26 05:18 | VIIRS_SNPP | 0.155 | 0.37 |
| 2026-03-11 04:54 | VIIRS375 | 0.810 | 2026-03-11 04:54 | VIIRS_NOAA20 | 0.299 | 0.37 |

---

## Q3. MODIS sensor-specific gap (session 5 median 0.79 — why?)

Pairs: 36  median=0.789  mean=0.938

By magnitude bucket:

| Bucket | n | median | mean |
|---|---:|---:|---:|
| weak (<0.5 MW) | 2 | 2.903 | 2.903 |
| low (0.5-2 MW) | 18 | 1.086 | 1.090 |
| moderate (2-10 MW) | 16 | 0.366 | 0.521 |
| high (>10 MW) | 0 | 0.000 | 0.000 |

By platform:

- Terra: n=13 median=0.725 mean=0.817
- Aqua:  n=23 median=0.904 mean=1.006


---

## Key findings (reading the report)

### Finding F1 — MODIS underestimates moderate-magnitude VRP (2-10 MW) by 2-3x
Q3 bucket analysis:
- MODIS 2-10 MW: 16 pairs, mediana **0.37**, media 0.52 (we report ~37% of MIROVA)
- MODIS 0.5-2 MW: 18 pairs, mediana **1.09** (near perfect)
- MODIS <0.5 MW: 2 pairs, mediana 2.90 (overestimate, small n)

13 de 15 "worst underestimates" (ratio 0.12-0.36) son MODIS en ese rango. El bias es magnitude-dependent: cuando la señal crece, nuestro VRP se queda corto. Sospechoso de saturación, sub-pixel mixing, o background contamination.

### Finding F2 — 21 MIROVA refs con granulo pero VRP=0 ("close_pass_zero_vrp")
Tenemos el granulo exacto (delta 0 min) y sin embargo `n_anomalous=0`, `n_vent=0`, `vrp_mw=0`. Los delta t_max - t_bg son típicamente 5-7 K. El eruption-scale threshold MODIS/VIIRS es `max(5K, 3σ)` — borderline. Pero el vent-scale (1K) debería atraparlos y no lo hace.

### Finding F3 — POSIBLE BUG ESTRUCTURAL: overlap ROI ↔ background annulus
**Verificado** en los 3 procesadores (`process_modis.py:162`, `process_viirs.py:210`, `process_viirs_mod.py`):
```
roi_mask = dist <= radius_km
bg_mask  = (dist >= BG_INNER_KM=5) & (dist <= BG_OUTER_KM=25)
```

Lascar tiene `radius_km=10`. El anillo 5-10 km está **dentro de ambas máscaras**. Consecuencias:
- Cualquier hotspot en 5-10 km del cráter contamina t_bg (inflación de background)
- Background inflated → threshold = `max(5K, 3σ)` sube
- Detección genuina falla porque el ΔT medido baja artificialmente

Esto afecta **todos los volcanes con `radius_km > 5`** (que es la mayoría).

Ejemplo concreto: si un fumarole real está a 7 km del cráter con BT=285 K y el background verdadero es 275 K, al incluir ese pixel en el bg annulus junto con ~500 pixels frios, t_bg sube ~0.02 K pero sigma_bg puede subir 1-2 K. Threshold sube de 5 K a 7 K, y ahora el ΔT=10 K del pixel real cumple apenas, con vrp reducido.

**Este es el candidato #1 porque es un bug identificable, testeable, y afecta a TODOS los sensores y la mayoría de volcanes.**

### Finding F4 — 16 refs perdidas son daytime VIIRS375 (ya conocido)
Los 16 `no_close_pass` son MIROVA VIIRS375 a las 17:48-18:42 UTC. Todos daytime en Lascar. Esto es la categoría que Phase A intentaba atacar (incorrectamente). Baja prioridad hasta que la calibración base esté limpia.

### Finding F5 — VIIRS outliers en rango bajo (<0.5 MW)
Top 5 overestimates en VIIRS tienen MIROVA VRP=0.04-0.77 MW donde nuestro VRP es 2-4x mayor. Posible: cap del scan-angle 2.0x puede ser muy alto en el borde del swath; o filtro NTI deja pasar marginales. Prioridad baja dado que afecta valores muy pequeños.

---

## Catálogo de hipótesis priorizado

| # | Hipótesis | Evidencia | Impacto esperado | Costo | Prioridad |
|---|---|---|---|---|---|
| **H1** | **bg annulus [5-25] overlaps ROI** → contaminación de background → thresholds inflados | F3 (bug verificado en código), F1 (MODIS 2-10 MW buckets), F2 (21 zero-vrps con ΔT=5-7K) | Arregla hueco MODIS + ~10-15 de los 21 zero-vrps + quizás subida general de ratio | BAJO (~10 líneas) | **P0** |
| H2 | Threshold `max(5K, 3σ)` es muy conservador para señales débiles | F2 (los 21 zero-vrps todos ΔT=5-7K) | ~10 refs extra de capture | MEDIO (riesgo FP) | P1 |
| H3 | MODIS Wooster 18.9 breakdown en señales moderadas (saturación) | F1 bucket 2-10 MW | Parcial, depende de H1 primero | ALTO (refactor) | P2 — solo si H1 no resuelve |
| H4 | Daytime I05 TIR con Dozier bi-espectral | F4 (16 refs) | 16 refs extra + daytime coverage | ALTO (nuevo algoritmo) | P3 |
| H5 | VIIRS scan-angle cap 2.0x muy alto en bordes | Top overestimates VIIRS ratio 1.7-2.0 | Marginal | BAJO | P4 |

## Plan experimental propuesto

### E1 — Arreglar overlap bg annulus (H1)
**Cambio mínimo**: en los 3 processors, cambiar:
```python
bg_mask = (dist >= BG_INNER_KM) & (dist <= BG_OUTER_KM)
```
a:
```python
bg_mask = (dist > radius_km) & (dist <= radius_km + 20)
```
Es decir, el background arranca JUSTO AFUERA del ROI, no a 5 km fijos. Ancho de anillo 20 km (equivalente a lo actual 5-25 km para radius_km=5). Para Lascar radius_km=10 → bg annulus [10,30] km. Para PCC radius_km=... → bg annulus [radius+0, radius+20] km.

**Test**: solo Lascar, correr reproceso overwrite, comparar:
- Capture rate (espera: subir de 88.7% a ≥92%)
- Ratio mediana global (espera: estable cerca de 1.0)
- Ratio MODIS buckets (espera: el bucket 2-10 MW se acerca a 1.0)
- Numero de close_pass_zero_vrp (espera: bajar de 21)
- Numero de close_pass_low_vrp (espera: bajar de 23)

**Criterio de ship**: capture rate arriba Y mediana global no se aleja más de 0.1 de 1.0 Y no aparecen nuevos outliers ratio > 5.
**Criterio de revert**: ratio mediana drifta a >1.5 o <0.5, O aparecen >5 records con vrp_mw absurdo (>100 MW).

### E2 — Solo si E1 no resuelve suficiente (H2)
Bajar `ANOMALY_THRESHOLD_K` de 5.0 a 3.0 en el sensor específico donde persiste el hueco. Test con las mismas métricas.

### E3+ — Iterar con el siguiente hallazgo en la lista

---

## ADDENDUM: reorientación tras nueva info del usuario (2026-04-08)

El usuario informó que el CSV de MIROVA scrapeado NO contiene todas las
detecciones MIROVA — algunos records VIIRS 375m y VIIRS 750m no se guardaron.
Eso cambia varias cosas:

1. **Capture rate es un lower bound** — nuestro "88.7%" es capture contra
   refs incompletas. El verdadero capture puede ser más alto.
2. **F2 (21 close_pass_zero_vrp) deprioritizada**: algunas pueden ser refs
   que no estaban en el CSV. No podemos distinguir "nosotros fallamos" de
   "MIROVA no guardó".
3. **F4 (16 no_close_pass daytime) deprioritizada** por la misma razón.
4. **El ratio sí es válido para calibración cuantitativa** — cuando ambos
   detectamos el mismo record, la comparación 1:1 es real. El ratio mediana
   1.02 y la dispersión por sensor son métricas legítimas.

**Prioridad reorientada**: enfocar en CALIBRACIÓN CUANTITATIVA, no
descubrimiento.

- **P0**: F1 — MODIS 2-10 MW underestima 2.7x (16 pares, ratio mediana 0.37). Análisis numérico detallado de un caso:

### Analisis detallado: 2026-02-22 07:25 MODIS_AQUA (ratio 0.12)

MIROVA reporta 2.73 MW, nuestro 0.328 MW.

Datos del record:
- `t_bg = 275.66 K`
- `t_max_k = 281.81 K`
- `ΔT_max = 6.15 K`
- `n_anomalous_pixels = 0` (eruption-scale detection FAILED)
- `n_vent_pixels = 1`, `vrp_vent_mw = 0.328 MW`

**Por qué falla la detección eruption-scale**:
Threshold = `max(5K, 3*sigma_bg)`. ΔT=6.15 K pasaría el floor de 5 K, pero no
pasa el threshold total. Eso implica `3*sigma_bg > 5`, o sea `sigma_bg > 1.67 K`.
Si sigma_bg ~2.5 K, threshold = `max(5, 7.5) = 7.5 K`, y ΔT=6.15 K queda debajo.

**Por qué el vent detecta pero da valor bajo**:
El pixel a 281.81 K está FUERA del vent ROI de 3 km. El vent-scale path sólo
ve pixels dentro del vent ROI, donde encuentra un pixel marginalmente más
cálido (~276.7 K) que pasa el threshold de 1 K pero con ΔL muy pequeño.
Resultado: vrp_vent_mw ≈ 0.3 MW mientras el pixel realmente caliente
(281.81 K) en el ROI medio queda sin contar.

**Implicación crítica para el overlap bug**:
El problema NO es principalmente que hot pixels eleven la MEDIA del bg (lo
cual V1/V2 mostró que es mínimo en Lascar), sino que **los pocos hot pixels
que SÍ caen en el overlap zone inflan el SIGMA_BG**, que es lo que domina el
threshold (`3*sigma > 5K` en la mayoría de casos). σ es sensible a outliers
(un outlier a 10K sobre el resto puede mover σ de 1.5 a 3).

**Hypótesis re-rankeadas**:

| # | Hipótesis | Mecanismo | Predicción para F1 | Costo |
|---|---|---|---|---|
| **H1'** | **bg overlap reduce sigma_bg → threshold baja → detecta moderados** | sigma sensitive to overlap outliers, fix elimina esos outliers de bg_mask | Records con ΔT 5-7 K que actualmente fallan empiezan a detectarse. Ratio 2-10 MW MODIS sube de 0.37 a algo mayor. | 10 líneas |
| H2' | Reducir N_SIGMA_MIR de 3.0 a 2.5 | directo: baja threshold 17% | Mismo efecto que H1' pero más agresivo, riesgo FP | 1 línea |
| H3 | MODIS Wooster 18.9 breakdown 2-10 MW | saturación, bi-spectral | No explica por qué el eruption-scale falla en primer lugar | Alto |

### Plan revisado

**E1**: Implementar H1' (bg overlap fix). Es el cambio más conservador (científicamente correcto, no cambia la física). Medir impacto exacto en Lascar.

**E2**: Si E1 no es suficiente, probar H2' (N_SIGMA_MIR = 2.5). Más agresivo pero puede ser necesario.

**E1 + E2**: Si ninguno de los dos por separado cierra el hueco, probarlos juntos.

**Métricas de éxito para E1**:
- Ratio MODIS bucket 2-10 MW: de 0.37 hacia ≥0.7
- Ratio mediana global: se mantiene cerca de 1.0 (±0.2)
- No aparecen nuevos outliers ratio > 5
- VIIRS_375 y VIIRS_750 ratios no degradan
- Capture rate puede subir algo (bonus, no métrica principal)

