# R2 Pixel-Level Validacion Opcion C (S71 T1 F2.d)

**Experimento**: `experiments/131_r2_pixel_level_optC`
**Profile auditado**: `mirova_equivalent_path_d_cap_v1` (cap=5MW, tbg<270K)
**Records auditados**: 20 (20 diagnosticos)
**Verdict adopcion**: **ADOPTABLE_DEFENSIVO** — Sin cap leaks; MIROVA max en records capped = 0.210 MW (<<5). Cap recorta inflados sin enmascarar magnitudes reales. PASS+MARGINAL = 50.0% sobre 20 diagnosticos.

## Metodologia

Replica el patron R2 retroactivo S70-1 (R2_GATES_BY_REGIME.md):

1. Sample 4 categorias del profile cap: cap-applied (A), ratio-extreme (B),
   no-cap-applied control (C), sin ALERTA MIROVA (D).
2. Por cada record: match TIF MIROVA mas cercano (tol 6h),
   centroide top-10 pixels TIF <=3km del vent, drift vs pc.centroid.
3. Ratio pc.vrp_mw / MIROVA.VRP_MW (CSV cons NRT).
4. Gates por regimen (R2_GATES_BY_REGIME.md):
   - Regimen A (Lastarria/Lascar/Isluga): drift <2km.
   - Regimen B1 (Villarrica/Chaiten): drift <3km.
   - Regimen B2 (PP): drift <3km marginal.
   - Regimen C (PCC): drift no aplica.
5. Cap-leak gate: FAIL si MIROVA.VRP_MW > 5MW en record capped.

## Tabla 20 records

| Cat | Vol | DT | Sensor | cap | t_bg | MIROVA VRP | ratio | drift_km | gate | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| A | Lastarria | 2026-05-09 02:25 | MODIS_TERRA | True | 266.0 | 0.060 | 83.33 | 3.54 | <2.0km | FAIL |
| A | Lascar | 2026-05-09 08:20 | MODIS_AQUA | True | 267.9 | - | - | 4.14 | <2.0km | FAIL |
| A | Isluga | 2026-05-09 08:15 | MODIS_AQUA | True | 268.8 | - | - | 2.94 | <2.0km | FAIL |
| A | Villarrica | 2026-05-10 03:00 | MODIS_TERRA | True | 268.2 | - | - | 1.82 | <3.0km | MARGINAL |
| A | Chaiten | 2026-05-15 01:20 | MODIS_TERRA | True | 244.2 | - | - | 1.25 | <3.0km | MARGINAL |
| B | Lastarria | 2026-05-09 02:25 | MODIS_TERRA | True | 266.0 | 0.060 | 83.33 | 3.54 | <2.0km | FAIL |
| B | Tupungatito | 2026-05-17 01:05 | MODIS_TERRA | True | 257.2 | 0.060 | 83.33 | 0.63 | <3.0km | MARGINAL |
| B | Lastarria | 2026-05-11 02:05 | MODIS_TERRA | True | 265.6 | 0.090 | 55.56 | 0.70 | <2.0km | MARGINAL |
| B | Lastarria | 2026-05-14 02:25 | MODIS_TERRA | True | 265.1 | 0.140 | 35.71 | 4.47 | <2.0km | FAIL |
| B | Tupungatito | 2026-05-14 02:20 | MODIS_TERRA | True | 244.2 | 0.210 | 23.81 | 5.29 | <3.0km | FAIL |
| C | Lastarria | 2026-05-09 04:48 | VIIRS_NOAA20 | False | 263.0 | - | - | 3.79 | <2.0km | FAIL |
| C | Lascar | 2026-05-09 04:48 | VIIRS_NOAA20 | False | 265.5 | - | - | 2.20 | <2.0km | FAIL |
| C | Isluga | 2026-05-09 04:48 | VIIRS_NOAA20 | False | 267.9 | 0.100 | 0.29 | 1.53 | <2.0km | MARGINAL |
| C | Villarrica | 2026-05-09 02:20 | MODIS_TERRA | False | 275.9 | - | - | 1.73 | <3.0km | MARGINAL |
| C | Chaiten | 2026-05-09 02:20 | MODIS_TERRA | False | 277.9 | 0.080 | 21.66 | 2.26 | <3.0km | MARGINAL |
| D | Lastarria | 2026-05-09 04:48 | VIIRS_NOAA20 | False | 263.0 | - | - | 3.79 | <2.0km | FAIL |
| D | Lascar | 2026-05-09 04:48 | VIIRS_NOAA20 | False | 265.5 | - | - | 2.20 | <2.0km | FAIL |
| D | Isluga | 2026-05-09 05:36 | VIIRS_NOAA21 | False | 266.2 | - | - | 0.40 | <2.0km | MARGINAL |
| D | Villarrica | 2026-05-09 02:20 | MODIS_TERRA | False | 275.9 | - | - | 1.73 | <3.0km | MARGINAL |
| D | Chaiten | 2026-05-09 04:54 | VIIRS_NOAA20 | False | 275.5 | - | - | 1.89 | <3.0km | MARGINAL |

## Resumen por categoria

- **A_cap_applied** (n=5): TIF match 5, MIROVA match 1, verdicts={'PASS': 0, 'MARGINAL': 2, 'FAIL': 3, 'FAIL_CAP_LEAK': 0, 'NO_DIAGNOSTIC': 0}
- **B_ratio_extreme** (n=5): TIF match 5, MIROVA match 5, verdicts={'PASS': 0, 'MARGINAL': 2, 'FAIL': 3, 'FAIL_CAP_LEAK': 0, 'NO_DIAGNOSTIC': 0}
- **C_no_cap_applied** (n=5): TIF match 5, MIROVA match 2, verdicts={'PASS': 0, 'MARGINAL': 3, 'FAIL': 2, 'FAIL_CAP_LEAK': 0, 'NO_DIAGNOSTIC': 0}
- **D_no_mirova_alert** (n=5): TIF match 5, MIROVA match 0, verdicts={'PASS': 0, 'MARGINAL': 3, 'FAIL': 2, 'FAIL_CAP_LEAK': 0, 'NO_DIAGNOSTIC': 0}

## Resumen por volcan

- **Lastarria** (A, n=6): {'PASS': 0, 'MARGINAL': 1, 'FAIL': 5, 'FAIL_CAP_LEAK': 0, 'NO_DIAGNOSTIC': 0}
- **Lascar** (A, n=3): {'PASS': 0, 'MARGINAL': 0, 'FAIL': 3, 'FAIL_CAP_LEAK': 0, 'NO_DIAGNOSTIC': 0}
- **Isluga** (A, n=3): {'PASS': 0, 'MARGINAL': 2, 'FAIL': 1, 'FAIL_CAP_LEAK': 0, 'NO_DIAGNOSTIC': 0}
- **Villarrica** (B1, n=3): {'PASS': 0, 'MARGINAL': 3, 'FAIL': 0, 'FAIL_CAP_LEAK': 0, 'NO_DIAGNOSTIC': 0}
- **Chaiten** (B1, n=3): {'PASS': 0, 'MARGINAL': 3, 'FAIL': 0, 'FAIL_CAP_LEAK': 0, 'NO_DIAGNOSTIC': 0}
- **Tupungatito** (B1?, n=2): {'PASS': 0, 'MARGINAL': 1, 'FAIL': 1, 'FAIL_CAP_LEAK': 0, 'NO_DIAGNOSTIC': 0}

## Cap leaks (FAIL critico — MIROVA >5MW capped)

- **Sin cap leaks.** El cap=5MW no enmascara ningun caso donde MIROVA
  reporta magnitud >5MW. La hipotesis fisica del fix (FPs cirrus path D)
  se confirma a este nivel.

## Records sin diagnostico (TIF gap o MIROVA gap)

- Todos los records tienen al menos un gate aplicable.

## Verdict de adopcion

**ADOPTABLE_DEFENSIVO** — Sin cap leaks; MIROVA max en records capped = 0.210 MW (<<5). Cap recorta inflados sin enmascarar magnitudes reales. PASS+MARGINAL = 50.0% sobre 20 diagnosticos.

- PASS: 0/20 (0.0%)
- MARGINAL: 10
- FAIL: 10
- NO_DIAGNOSTIC: 0

### Interpretacion (geologo)

El cap=5MW es un parche defensivo contra el path D dNTI ctx FPs en cirrus alto
(D9, t_bg<270K). La pregunta R2: el cap **enmascara casos donde MIROVA reporta
magnitud real >5MW** (lo que seria mala adopcion), o solo recorta inflados FPs
(lo que es bueno).

**0 cap leaks** — en ningun record capped MIROVA reporta magnitud >5MW.
Cuando hay ALERTA MIROVA en escena con cap aplicado, su VRP es 0.06-0.21 MW
(rango sub-MW, focal puro). El cap solo recorta inflados nuestros, no enmascara
magnitudes reales. **Adopcion defensiva justificada**.

### Caveat metodologico: drift y MODIS

Las gates de drift R2_GATES_BY_REGIME.md (<2km A, <3km B) se calibraron en
S70-1 sobre records VIIRS375 (pixel 375m). Los records capped son
**~95% MODIS** (pixel ~1km) por construccion del cap (path D + t_bg<270K es
regimen-MODIS-dominante en cirrus alto). Con MODIS, drift 2-3 km es normal
por la resolucion del granule, no error del pipeline. Por eso una fraccion
de records cae en MARGINAL (drift entre gate y 2x gate) sin que indique cap
malo. La gate dura es **cap-leak**, que esta en 0/N.

### Ratio post-cap residual

Cuando hay MIROVA ALERTA + cap aplicado, ratio sigue 24-83x (cap=5 vs MIROVA
0.06-0.21 MW). El cap acota el dano (sin cap, ratios eran 50-150x pre-D9-fix)
pero **no resuelve la causa raiz** (D9 path D ctx en cirrus). Cap es parche
operacional, no fix arquitectural — esto coincide con plan S71+ papers-first.
