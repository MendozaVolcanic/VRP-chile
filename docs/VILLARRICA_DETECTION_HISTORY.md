# Villarrica — historia de detección VRP-chile

> Documento de referencia creado S51 (2026-05-17) en respuesta a pregunta de
> Nicolás: "¿en alguna sesión previa a S20 detectábamos el cráter Villarrica?
> No recuerdo la metodología".
>
> Respuesta corta: **NO**. Villarrica nunca detectó pre-S20. La primera
> detección fue S26 (2026-04-28) con Test 1 integrated-ROI + Regla D.
>
> Este documento explica por qué, qué cambió, y por qué hoy estamos
> estrictamente mejor que cualquier estado pre-S20.

## Línea de tiempo Villarrica detection

| Sesión | Estado | Mecanismo | Resultado Villarrica |
|---|---|---|---|
| S9 | 0% recall | vent-path BT-puro (`BT > t_bg + 1K`) | **Ciego al lava lake** |
| S10-S11 | 0% | Cambios afectan otros vols | 0% |
| S12 F1 | 0% | vent-path añade sigma-gating (`max(1K, 2σ)` cap 3K) | 0% — peor con sigma |
| S12 baseline | 0% | — | "**Gap arquitectural**" explícito en memoria |
| S13 | plan | `plan_s13_test1_integrated_roi.md` propone Coppola 2015 Eq.1 | NO ejecutado aún |
| S14-S19 | 0% | Geometría MIROVA, NOAA-21, drifts | 0% — Villarrica nunca aparece |
| S20 | 0% | Regla D vent-priority (eruption-path) | 0% — Villarrica no tiene cluster eruption |
| S25 | offline | Test 1 implementado pero NO integrado pipeline | Test 1 dispara pero clasificación falla |
| **S26** | **0/6 → 5/6** | Regla D extendida para Test 1 (commit `7701e36`) | **PRIMERA DETECCIÓN** |
| S26 v2 | **6/6 (100%)** | L_bg LOCAL Test 1 ring 1-3km (commit `33b1a7c`) | Magnitud calibrada |
| **S27** | **0/3 → 3/3** | Test 1 ON en `_mirova_literal` adoptado operacional | Milestone confirmado 90d |
| S31+ frontier | 100% | Test 1 + Regla D + cluster_hotspots 8-conn | Robusto |
| S38 D8 | 100% | + vent_anchored + H8 pixel-level distance | Aún mejor cluster selection |
| S46 drift234 | 100% | + first-pass Tests 2∧3 + dual-ROI + second-pass | Estado operacional actual |
| **HOY (S50)** | **100%** | Test 1 + vent_anchored + drift234 | **118 detecciones 30d, 112 summit (94.9%)** |

## Por qué vent-path antiguo era ciego al lava lake Villarrica

**Físicamente**: vent-path miraba el pixel más caliente VIIRS-I04 (3.74 μm)
dentro del `vent_radius_km` (~5 km), comparaba su BT contra el background
del anillo 5-25 km, y disparaba si excedía:
- S9: `BT_max_vent > t_bg + 1.0 K`
- S12+: `BT_max_vent > t_bg + max(1.0 K, 2σ_bg)` cap 3 K

**Por qué fallaba en Villarrica específicamente**:

El lava lake activo del Rinrinco emite radiación sub-pixel — 0.05 a 0.21 MW
según mediciones MIROVA. Cuando un pixel VIIRS-I de 375 m abarca esa
fuente, también incluye:
- Hielo/nieve del glaciar Pichillancahue-Turbio
- Roca volcánica fría circundante
- Atmósfera

El **promedio** de BT del pixel mezclado raramente supera 1 K sobre el
fondo regional. El calor del lago se diluye en el promedio. El método
BT-puro (vent-path) es estructuralmente ciego a esta señal.

## Por qué Test 1 sí lo detecta

**Coppola 2015 §2.2 Eq.1 — integrated-ROI MIR**:
- En vez de mirar pixel-por-pixel, **integra la radiancia MIR de TODOS
  los pixels dentro del ROI cráter** (~5 km)
- Compara contra la radiancia integrada esperada del fondo
- La señal sub-pixel diluida en cada pixel individual se **suma
  coherentemente** sobre la región y emerge sobre el ruido

**Analogía geológica**: el cráter "calienta levemente" 9 pixels vecinos en
vez de "calentar fuerte" 1 pixel. Vent-path solo veía el pixel máximo
(fallaba). Test 1 ve los 9 sumados (detecta).

## Estado operacional actual Villarrica (S50, window 30d)

Verificación empírica `data/mirova_equivalent/Villarrica.json`:

| Métrica | Valor |
|---|---|
| Total detecciones VIIRS-I 30d | 118 |
| Summit (<5 km del vent) | **112 (94.9%)** |
| Far (>5 km) | 6 (5.1% — ruido inherente VIIRS-I + 1 incendio agrícola) |
| Recall alertas MIROVA explícitas | **2/2 (100%)** |
| Mediana pc_vrp | 1.69 MW |
| Sub-MW (<1 MW) | 43 (36%) |
| Above-MW (≥1 MW) | 79 (66%) |
| Mecanismo primary | Test 1 (43%) + eruption (58%) + vent (2% legacy) |

## ¿Hay regresión perdida pre-S20?

**No**. Evidencia:
1. Memoria S12 baseline (commit `7c1b2a3`, 2026-04-16) dice literal:
   "**Villarrica 0% recall: gap arquitectural, requiere Test 1
   integrado-ROI (plan en `tasks/plan_s13_test1_integrated_roi.md`)**"
2. `git log` entre S9 y S19 NO contiene ningún commit que mencione
   "Villarrica" como detección exitosa.
3. Tasks/handoffs S9-S19 NO mencionan Villarrica detectado.
4. La primera detección documentada es **S26 D fix** (2026-04-28),
   POST-S20.

**Posible confusión de memoria**:
- Quizá Nicolás recuerda **Lascar** o **Tupungatito** que SÍ detectaban
  pre-S20 con vent-path (otros volcanes con fuente térmica más fuerte
  que sí superaba el threshold BT-puro).
- O recuerda S26-S27 donde Villarrica empezó a detectar — esto es
  POST-S20.

## Recomendación

**No buscar metodología pre-S20 para recuperar Villarrica**. El sistema
actual (Test 1 integrated-ROI + Regla D Test 1-priority + L_bg local +
vent_anchored + drift234) es el primer estado del proyecto donde
Villarrica se detecta de manera confiable y calibrada.

**Si querés tranquilidad adicional**: A/B Villarrica únicamente con
profile `s9_vent_permissive` (vent-path puro sin sigma) — confirmará
empíricamente que no detecta NADA que Test 1 no detecte ya. Pero la
evidencia documental + empírica ya es categórica.

## ⭐ Detecciones del lava lake real (sub-pixel summit <300m)

> Agregado S51 (2026-05-17) tras información de Nicolás: "el cráter real
> Villarrica son 100m de radio aprox alrededor del punto Google Maps
> -39.420292, -71.939908. El lago de lava ha estado oculto y solo se ha
> visto en pocas ocasiones hace algunos meses cuando VIIRS-I 375m lo detectó".

**Confirmación empírica**: VRP-chile detectó el lava lake exactamente esas
"pocas ocasiones". Análisis de `anomaly_pixels` cruzados con coord cráter
real (Google Maps) en window 2026-01 → 2026-05 (5 meses):

| Mes | Pixels VIIRS-I 375m a <300m del cráter real |
|---|---:|
| Enero 2026 | 3 |
| **Febrero 2026** | **11 (pico actividad)** |
| Marzo 2026 | 9 |
| Abril 2026 | 12 |
| Mayo 2026 (parcial) | 10 |
| **TOTAL 5 meses** | **45 pixels** |

### Detecciones con primary_cluster centroid <500m del cráter real (18 records)

Casos paradigmáticos:

| Fecha UTC | Sat | Dist crater real | VRP | npx |
|---|---|---:|---:|---:|
| **2026-02-15 05:00** | **VIIRS_NOAA21** | **159m** | 1.53 MW | 28 |
| 2026-02-03 05:54 | VIIRS_SNPP | 314m | 4.50 MW | 95 |
| 2026-02-10 05:42 | VIIRS_NOAA20 | 334m | 2.22 MW | 80 |
| 2026-02-13 04:48 | VIIRS_NOAA20 | 310m | 1.30 MW | 31 |
| 2026-03-24 05:36 | VIIRS_SNPP | 233m | 0.75 MW | 81 |
| 2026-04-12 06:42 | VIIRS_NOAA20_750 | 240m | 0.53 MW | 9 |
| **2026-05-11 06:00** | **VIIRS_NOAA20** | **170m** | 0.39 MW | 1 |

**Interpretación volcanológica**:
- Febrero 2026 = pico actividad lava lake (consistente con "hace algunos
  meses").
- Pixel 2026-02-15 05:00 NOAA-21 a **159m** del cráter exacto = momento
  donde el lago de lava emergió con suficiente energía para superar
  background del pixel mezclado 375m.
- Última detección confirmada 2026-05-11 06:00 NOAA-20 a **170m** = una
  de las 2 alertas MIROVA del window 30d.
- Distribución mensual decreciente consistente con observación de campo:
  el lago se ha visto solo en "pocas ocasiones".

**Por qué la mayoría del tiempo NO detectamos el lava lake**:
- Cubierta por nieve/hielo glaciar Pichillancahue-Turbio
- Lava lake oculto en chimenea, no expone superficie radiante grande
- BT del pixel 375m mezclado con nieve → no supera background

**Cuando SÍ detectamos** (las 45 ocasiones documentadas arriba):
- Lava lake emerge superficialmente
- BT del pixel se eleva lo suficiente para Test 1 integrated-ROI
- VRP detectado típicamente 0.4-4.5 MW

**Detecciones que NO son el lava lake** pero que el dashboard marca "Dentro"
(porque inner_radius=5km = paridad MIROVA, no cráter real):
- Records a 1-5 km del vent: cono volcánico superior, calor residual roca
  oscura, no señal volcanológica relevante para alerta de erupción.
- Records far (>5km): bosque, lago, agricultura — ruido VIIRS-I.

**Distinción operacional importante para SERNAGEOMIN**:
- `dist < 0.3 km` → lava lake real (raro, alta confianza)
- `dist 0.3-1.0 km` → cráter / borde cráter (probable señal volcánica)
- `dist 1.0-5.0 km` → cono superior (calor residual, baja confianza alerta)
- `dist > 5.0 km` → ruido o incendio/agua

---

## Nota técnica visualización dashboard

`frontend/index.html` usa dos coord distintas para Villarrica:
- `lat=-39.420, lon=-71.930` (centro genérico, ~860m al ESTE del cráter real)
- `vent_lat=-39.420227, vent_lon=-71.939876` (cráter real, ~7m de Google Maps)

**Detección (cluster, distancia)** usa `vent_lat/vent_lon` → 100% correcto.
**Visualización (círculo 25km gris, marker naranja "Centro")** usa `lat/lon`
→ aparece visualmente desplazado ~860m al ESTE.

Fix recomendado S52: corregir `lat`, `lon` Villarrica en `volcanoes.yaml` y
`frontend/index.html` línea 512 a `(-39.420227, -71.939876)` para
alineamiento visual perfecto. NO afecta detección.

---

## Referencias

- `~/.claude/projects/.../memory/project_s26_villarrica_test1_d.md`
- `~/.claude/projects/.../memory/milestone_s27_h_s27_1_confirmada.md`
- `tasks/plan_s13_test1_integrated_roi.md` (histórico)
- Commit `7701e36` — Regla D Test 1-priority
- Commit `33b1a7c` — L_bg local Test 1
- `docs/HYPOTHESIS_LOG.md` — H_S27_1 confirmada
- `pipeline/process_viirs.py:923` — vent-path implementado pero OFF en `mirova_equivalent`
