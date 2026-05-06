# Design — VRP integrated Coppola 2015 Eq.1 textual (S33+)

> Brainstorming session 2026-05-06. Hipótesis post-refutación Driver B
> Phase 1/2/D4. Aplica reglas S33 (R1-R7) con disciplina.

## Contexto

Estado operacional post-S33 (commit `2fa5da6`):
- Driver A solo (frontend `mirovaEqVrp` con fix S33, sin filtros pipeline).
- Recall global 74.2%, ratio mediano 2.53× (medido con métrica corregida
  `pipeline.audit_metrics.mirova_eq_vrp` + `experiments/76_audit_independent`).
- Magnitud inflada en volcanes con activity sub-pixel:
  - Lastarria 18.5×, Villarrica 64.9×, Planchón 16.0×, Chaiten 18.3×, PCC 12.1×.
- Phase 1 (5σ filter pixel) refutado: destruyó recall sin razón física válida.
- D4 (L_bg global) refutado: efecto despreciable post-fix S33.

## Problema científico

Cuando Test 1 dispara (Coppola 2015 Eq.1 integrated trigger), nuestro
pipeline calcula VRP descomponiendo per-pixel:

```python
t1_delta_L = np.maximum(t1_L - test1_L_bg_local, 0.0)  # clip ≥0 PER pixel
vrp_mir_mw = sum(t1_area * k * t1_delta_L) / 1e6        # SUM
```

Esto **diverge** de Coppola 2015 §2.2 Eq.1 textual:
- Eq.1 dice: `VRP = k · Σ(L_obs - L_bg) · A_pix` integrado sobre la ROI **sin
  clip por pixel**. Pixels más fríos que bg contribuyen negativo a la suma
  neta. Solo el integrado final puede ser 0 si la suma neta es negativa.
- Nuestra implementación clipa cada pixel a 0 antes de sumar — eso infla la
  magnitud porque pixels marginalmente fríos NO compensan los marginalmente
  calientes (el bg se "inflala" por construcción).

Hipótesis: implementar Eq.1 textual baja la magnitud sin destruir recall
(el trigger sigue disparando — solo cambia cómo reportamos VRP).

## Aproximación elegida

**(a) Alcance**: solo cuando `final_hotspot_source = "test1"` (Test 1 ganó
la cascada). Path BT clásico mantiene cálculo per-pixel (Coppola 2016a).

**(F1) Fórmula**: Coppola 2015 Eq.1 sin clip per-pixel, max(0) global.

```python
t1_delta_L_neto = np.sum((t1_L - test1_L_bg_local) * t1_area)  # sin clip
vrp_int_mw = max(0.0, WOOSTER_COEFF * t1_delta_L_neto / 1e6)
```

**(O1) primary_cluster con integrated**: `pc.vrp_mw = vrp_int_mw`, centroid
del Test 1 ROI (que es por definición ~1-3km del vent, garantiza summit-class
en `mirovaEqVrp`).

```python
if final_hotspot_source == "test1":
    primary_cluster = {
        "n_pixels": test1_n_contrib,
        "vrp_mw": round(vrp_int_mw, 3),
        "centroid_lat": test1_centroid_lat,  # del ROI Test 1
        "centroid_lon": test1_centroid_lon,
        "centroid_dist_km": test1_hotspot_dist_km,  # ya cerca del vent
    }
```

## Las 3 preguntas MISSION.md

**(1) ¿En papers MIROVA core?** **SÍ** — Coppola 2015 §2.2 Eq.1 textual.
Implementación literal del paper. NO mezcla metodologías como Phase 1
(que combinaba Coppola 2016a Tabla 1 con Coppola 2015 Test 1).

**(2) ¿Cierra divergencia?** **SÍ** — D5 magnitud (re-abierto S33).
Implementa la fórmula textual del paper que YA estaba referenciada en
nuestro código pero descomponiendo per-pixel.

**(3) ¿Alineación interna?** N/A — pasa preguntas 1 y 2.

## Criterios de aceptación

A/B test 11 Tier A 90d. Comparar:
- **Driver A solo** (operacional actual): recall 74.2%, ratio 2.53×.
- **Driver A + Eq.1 textual**: TBD.

Aprobado si:
- Recall global ≥73% (paridad con operacional, no destrucción).
- Ratio mediano ≤2.0× (mejora significativa).
- Lastarria/Villarrica/Planchón ratio ≤10× (vs 18-65× actual).
- Ningún volcán cae a recall 0% (sub-detección catastrófica).

NO aprobado si:
- Recall caída >5pp en cualquier volcán (excepto N/A baja muestra).
- Ratio mediano sube vs Driver A solo.

## Riesgos identificados

**R1 — Suma negativa en records con cráter cubierto por nube fría**: si la
ROI Test 1 tiene mayoría de pixels más fríos que L_bg (porque nube de
hielo cubre el cráter), suma neta negativa → VRP=0. Es decir, si MIROVA
reporta alerta pero nuestro Test 1 dispara con suma negativa, perdemos.

Mitigación: el trigger Test 1 solo dispara si ΔL_ROI > k_sigma · σ_ΔL.
Si la suma neta es positiva (trigger), el VRP integrated también lo será.
La probabilidad de "trigger positivo + integrated negativo" es baja.

**R2 — Pérdida de info pixel-level fina**: con O1, el `primary_cluster`
no refleja extensión del cluster contiguo Test 1 (que era info útil para
visualización pixel-level). Trade-off aceptable: la extensión está en
`anomaly_pixels` (top-100), `n_test1_pixels`, `triggered_test1`.

**R3 — Tupungatito recall sigue 48%**: este fix NO resuelve sub-pixel
catástrófico Tupungatito (causa: cluster fuera del inner_radius=7km).
Eso es D4 verdadero, no D5. Se trata por separado.

## Plan de implementación con disciplina S33

### Fase 1: Brainstorming + design doc
- ✅ Brainstorming session.
- ✅ Design doc (este).
- ⏳ User review (pendiente).

### Fase 2: R2 verificación pixel-level con MIROVA web (S33 regla)
- Identificar 5 granules específicos donde el fix se espera tener efecto:
  - Lastarria con MIROVA "Muy Bajo" 0.05-0.15 MW + nuestro pc_vrp 5-30 MW.
  - Villarrica con MIROVA "Muy Bajo" 0.10-0.20 MW + nuestro pc_vrp 30-65 MW.
  - Chaiten con MIROVA bajo + nuestro alto.
  - 1 caso edge: Lascar (path BT dominante, Eq.1 NO aplica) — debería NO
    cambiar.
  - 1 caso edge: Tupungatito (recall <50%) — verificar que NO empeore.

- Para cada granule: descargar L1B + procesar manualmente con la fórmula
  Eq.1 textual. Comparar pixels y suma con plot Latest10NTI MIROVA.

- Si pixels y suma corresponden a lo que MIROVA reporta → R2 pasa,
  proceder Fase 3. Si NO → refutar y volver a la mesa.

### Fase 3: Implementación + tests
- `pipeline/profile.py`: flag `ENABLE_VRP_INTEGRATED_EQ1` (default OFF
  backward-compat).
- `pipeline/process_viirs.py` + `process_modis.py` + `process_viirs_mod.py`:
  rama condicional cuando flag ON + final_hotspot_source='test1' →
  computar Eq.1 textual.
- `tests/test_vrp_integrated_eq1.py`: tests sintéticos R1+R7:
  - Records con suma neta positiva → VRP > 0.
  - Records con suma neta negativa → VRP = 0.
  - Records sin Test 1 disparado → comportamiento sin cambio.
  - Records con Test 1 que ganó cascada → Eq.1 aplicada.
  - Records con Test 1 sin ganar cascada → comportamiento path BT (sin Eq.1).

### Fase 4: A/B test + audit independiente
- Profile `mirova_equivalent_vrp_integrated.yaml` con flag ON.
- Workflow `reproc-ab-vrp-integrated.yml` (clonado patrón S32 con artifacts).
- Audit con `experiments/76_audit_independent.py` (incluye nuevo profile).
- R6 cuestionar resultados: si "ratio cae 50%" → preguntar la métrica.

### Fase 5: Decisión adopción
Si A/B aprobado por todos los criterios + R2 confirmado pixel-level →
adopción operacional con merge inteligente similar a sync Phase 1 OFF.
Si no → documentar refutación en `docs/MIROVA_DIVERGENCES.md`.

## Tiempo estimado

- Fase 2 R2: 2-3h (descarga + procesamiento manual + comparación).
- Fase 3 implementación: 1h (cambio focalizado, ~30 líneas por procesador).
- Fase 4 A/B: 5-6h (workflow tipo Phase 2/D4).
- Fase 5 decisión + merge: 1h.
- Total: 9-11h para validación completa.

## Self-review pre-aprobación

- ✅ Las 3 preguntas MISSION.md cumplidas explícitamente.
- ✅ Alcance focalizado (solo Test 1 path), no rediseño universal.
- ✅ Criterios de aceptación cuantitativos.
- ✅ Riesgos identificados con mitigación.
- ✅ Plan de validación incluye R2 (verificación pixel-level) ANTES de
     implementación. Disciplina S33 aplicada.
- ✅ Tests sintéticos planeados R1+R7.
- ✅ Default OFF backward-compat (no contamina operacional sin A/B).
- ⏳ User review pendiente.

## Alternativas memorizadas (si F1 no aprueba)

- (b) Trigger expandido: cuando triggered_test1=True aunque no gane cascada.
- (c) Universal: rediseño VRP para todos los path. Alcance máximo, riesgo alto.
- (F2) F1 + L_bg global: combinación. D4 ya refutado pero podría reanimarse
      si F1 valida y queda residual sub-pixel Tupungatito.
- (O2) Eliminar primary_cluster cuando integrated. Más invasivo dashboard.
- (O3) cluster_hotspots con escala proporcional. Complejidad sin valor claro.
