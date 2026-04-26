# Diagnóstico final S21 — D6 refutado, cuello Tupungatito es límite físico

> Output combinado de experiments 38 (forense) + 39 (locate vent) + 40 (sigma per
> clase) + 41 (multi-ROI granules raw). Cierra S21 con conclusión empírica.

## Cronología del razonamiento S21

1. **Hipótesis inicial S20**: Tupungatito recall 0.57 sub-óptimo por **D6**
   ("background no localizado" — std_bg sobre anillo bbox 50×50 km inflado por
   glaciar lateral; ROI1 5×5 km local debería ser ~0.5–0.8 K).

2. **Task 6 (forense replicable)**: confirmó 12 T4 + 1 T2b + 0 T3 + 2 T1 + 20 TP.
   Recall 0.571 medido. T3=0 valida Regla D S20 sin regresión.

3. **Task 7 (locate active vent)**: centroide ponderado VRP de pixels detectados
   dentro del inner_radius_km a 2.76 km del vent_lat/lon nominal.

4. **Task 8 errado**: leí `process_viirs.py:518` sin trazar el caller. Concluí que
   vent-path usaba vent_lat/lon nominal (no mirova_center). **Falso**: el caller
   `scripts/run_pipeline.py:220` usa `get_effective_vent()` que ya hace fallback
   `mirova_center → vent_lat/lon`.

5. **Re-conclusión Task 8**: D6 sigue siendo el camino. Pero antes de implementar
   el fix con reproceso, validar empíricamente.

6. **Task 8b/41**: descarga 3 granules T4 reales vía earthaccess y mide std_bg en
   ROIs múltiples (global vs summit_3_5 vs summit_5_8 vs summit_5_10).

## Mediciones empíricas (3 granules T4 Tupungatito 2026-04-22 a 2026-04-24)

| ROI | std_bg mediana | n_pixels mediana |
|---|---:|---:|
| annulus_global (2–25 km) | **5.47 K** | 8473 |
| annulus_summit 3–5 km | 4.79 K | 228 |
| annulus_summit 5–8 km | **4.41 K** | 586 |
| annulus_summit 5–10 km | 4.79 K | 1116 |

**Ratio summit_5_8 / global = 0.81**. Hipótesis D6 predecía <0.5.

**Refutado**: el glaciar Tupungatito (5682 m) afecta TODA el área hasta ~10 km, no
solo el anillo lateral. Bajar el ROI no baja std_bg significativamente.

## Inspección de los 3 T4 directamente

| Fecha | Sensor | n_anom | n_vent | t_bg (K) | t_max (K) | final_hotspot dist | source |
|---|---|---:|---:|---:|---:|---:|---|
| 2026-04-24 06:12 | NOAA-20 | 377 | **0** | 264.81 | 280.10 | 26.32 km | eruption |
| 2026-04-23 06:36 | NOAA-20 | 293 | **0** | 264.37 | 279.67 | 25.95 km | eruption |
| 2026-04-22 06:00 | NOAA-21 | 122 | **0** | 264.87 | 277.55 | 27.99 km | eruption |

`n_vent_pixels=0` en los 3 → vent-path no detectó pixel hot dentro del
`vent_radius_km=5` desde mirova_center. Los pixels calientes están todos a 25-28 km
(esquinas del bbox 50×50 km) — son detecciones far espurias o POIs altiplánicos
(probable Cerro Marmolejo NE / cluster SW Tupungatito-El Yeso lejos).

## Threshold vent calculado en T4

Con `std_bg_local ≈ 4.5 K`, `N_SIGMA_VENT=2`, `MAX_VENT_SIGMA_CONTRIB_K=3`:
- `sigma_contrib = min(2 × 4.5, 3) = 3 K` (cap satura)
- `vent_thresh = max(1, 3) = 3 K`

Idéntico al threshold con bg global. **Cambiar a bg local NO movería el threshold**.

## Causa raíz reformulada (definitiva)

La fumarola activa Tupungatito es **sub-pixel + sub-Kelvin con variabilidad
nocturna**. En las pasadas T4 fue genuinamente <3 K sobre fondo. Ningún cambio
local-vs-global de std_bg ayuda porque el cap satura igual.

**¿Por qué MIROVA captura más?** Hipótesis (no validables sin código MIROVA):
- Algoritmo NTI absoluto distinto / más sensible
- Path D dual-ROI con thresholds más permisivos para summit
- Suavizado temporal multi-pasada
- Supervisión manual post-algorítmica (Coppola 2023 §2.5)

## Decisión S22

**No implementar D6** (refutado empíricamente).

**Caminos candidatos S22 ordenados por prometedoresidad**:

### Opción 1 — Verificar Path D contextual en T4 (cero costo)

Nuestro código tiene Path D (dNTI 8-vec Coppola 2016a) ya activo. Si
`diag_n_dnti_ctx_path > 0` en T4 records → Path D detecta el cráter pero
otra parte del pipeline lo descarta. Si `diag_n_dnti_ctx_path = 0` → Path D
tampoco captura → confirmar que es genuinamente sub-detección.

### Opción 2 — A/B test: bajar `MAX_VENT_SIGMA_CONTRIB_K` de 3 a 2

Más permisivo. Riesgo: FPs en otros volcanes con bg alto. Reproceso 30 días
sobre 3 Tier A para validar trade-off.

### Opción 3 — Median + MAD en lugar de mean + std

Más robusto a glaciar (resistente a outliers). Cambio invasivo en
`process_viirs.py`. Reproceso obligatorio.

### Opción 4 — Aceptar como límite físico

Documentar Tupungatito 0.57 como límite del MIR puro nocturno. Foco S22+ en
otros frentes (issue #1 NRT, feature parity dashboard, SWIR Sentinel-2).

## Recomendación

**Opción 1 primero** (verificación gratis, decide si hay margen). Si Path D NO
está disparando en T4, pasar a Opción 2 (A/B test). Si Path D SÍ dispara pero
otra parte filtra → bug fix targetted. Si nada dispara → Opción 4.

## Lecciones del proceso

1. **Validar empíricamente antes de comprometerse** a reprocesos largos. Costó 1
   sesión sigue siendo barato vs 7 horas de reproceso para refutar después.

2. **Trazar callers cuando se lee callee** (CLAUDE.md regla A2 reforzada). Mi
   error H_S21_9 inicial fue leer process_viirs.py sin verificar el caller.

3. **Hipótesis "obvias" pueden ser falsas**: D6 sonaba físicamente plausible
   (glaciar → bg inflado → threshold sube → sub-pixel no dispara) pero la
   medición real lo refutó porque el glaciar afecta toda el área, no solo el
   anillo lateral.

4. **El recall MIROVA tiene componente no-algorítmico** (supervisión humana
   Coppola 2023 §2.5, drift D5). Hay un techo intrínseco que un clon
   100% automático no alcanza sin replicar la curaduría manual.
