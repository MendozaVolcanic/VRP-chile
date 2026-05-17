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

## Referencias

- `~/.claude/projects/.../memory/project_s26_villarrica_test1_d.md`
- `~/.claude/projects/.../memory/milestone_s27_h_s27_1_confirmada.md`
- `tasks/plan_s13_test1_integrated_roi.md` (histórico)
- Commit `7701e36` — Regla D Test 1-priority
- Commit `33b1a7c` — L_bg local Test 1
- `docs/HYPOTHESIS_LOG.md` — H_S27_1 confirmada
- `pipeline/process_viirs.py:923` — vent-path implementado pero OFF en `mirova_equivalent`
