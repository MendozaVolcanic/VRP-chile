# Design doc R5 — Gate Path D MODIS intra-radio per-volcán

**Skill triggers respetados** (CLAUDE.md tabla): writing-plans + R5 design doc +
test-driven-development + verification-before-completion.
**Sesión**: S82 (2026-05-26). **Estado**: PROPUESTO, no implementado.
**Bloqueante implementación**: confirmación Nicolás + tag defensivo A45.

## Motivación (resumen Fase 1)

99.5% de FPs MODIS son **Path D (dNTI contextual 8-vecinos) puro**
disparando lejos del cráter (89% a >10 km, 53% a >20 km). MIROVA tagged
RUTINA(vrp=0.0) en 98% de los casos → gate intra-ROI no replicado.
Detalle: `docs/F_S81_A_FASE1_DIAGNOSIS.md`.

## Opciones consideradas

### Opción A — Gate distancia per-volcán empírico (recomendada)

Path D MODIS solo dispara si `distance ≤ R_mirova_modis(volcan)` donde
`R_mirova_modis` se extrae empíricamente del CSV consolidado MIROVA:

```
R_mirova_modis(vol) = percentil_95(distancia_alerta_termica)
  sobre filas del scraper Mirova-v1 donde:
    nombre == vol
    sensor == MODIS_TERRA | MODIS_AQUA
    tag == ALERTA_TERMICA
```

**Justificación física**: el percentil 95 captura el "radio operativo
real" donde MIROVA publica ALERTA — más allá es cola de RUTINA. Es
data-driven sobre la propia hoja de respuestas (CSV scraper).

**Fallback** si vol tiene <5 ALERTAs MIROVA históricas:
`R_mirova_modis = inner_radius_km` del yaml (conservador).

**Persistir**: nuevo campo `mirova_modis_max_path_d_km` en
`volcanoes.yaml` por volcán Tier A. Generado por script offline,
versionado, no recalculado en runtime.

**Impacto estimado**: cae 89% de FPs (los `far`). Los 92 `summit`
remanentes (11%) requieren análisis adicional Fase 2-extra (posible
ajuste de `inner_radius_km` desde KMZ MODIS oficial).

### Opción B — Path D requiere n_pixels ≥ 4 (cluster mínimo)

Path D MODIS solo si `primary_cluster.n_pixels ≥ 4`.

**Impacto**: cae 66.5% de FPs (clusters ≤3 px). Insuficiente: 33.5% de
FPs son clusters ≥4 px que MIROVA igual filtra.

**Veredicto**: no resuelve solo. Complementario a A, no sustituto.

### Opción C — Co-validación con Path A obligatoria

Path D MODIS solo cuenta si Path A (BT clásico) o B (NTI absoluto)
también dispara en el cluster.

**Impacto**: cae ~100% FPs (ninguno tiene Path A en el dataset Fase 1),
**pero** rompe el caso de uso original de Path D (resolver señal
sub-pixel cuando BT clásico no llega). Pierde TPs reales —
particularmente Villarrica lava lake y Chaitén dome débil, donde Path D
es el único que ve la señal.

**Veredicto**: over-kill. Contradice Coppola 2016a SP426.5 §3.2.

### Opción D — Las 3 en paralelo + A/B test

A vs B vs (A+B combinadas) en 3 profiles, reproc 45d × 11 Tier A,
decisión por precisión + recall + F1.

**Veredicto**: trabajo adicional ~3-4h dise+test pero decisión final
empírica. Posible si A no da el resultado esperado, no como default.

## Decisión preliminar

**Opción A** como Fase 2 inicial. **Razones**:

1. **Clon literal MIROVA**: el percentil 95 sobre el CSV scraper
   replica el radio operativo real publicado por MIROVA, no inventa
   threshold.
2. **Cae 89% del problema** en un solo cambio.
3. **No rompe TPs cercanos al cráter** (Villarrica lava lake @
   inner_radius 5 km no afectado, Chaitén dome @ 5 km no afectado).
4. **Reutilizable**: el `R_mirova_modis` per-volcán también sirve para
   validar/comparar `inner_radius_km` actual y, en V2, para VIIRS.

Si A deja FPs residuales >10 por volcán-mes, **combinar con B** en una
Fase 2.5 (no en Fase 2 inicial).

## Criterios de aceptación

Fase 2 implementación se considera completa cuando:

1. **Test sintético geométrico** (TDD obligatorio per skill trigger):
   `tests/test_modis_path_d_intra_radio_gate.py` con casos:
   - Pixel a 30 km, dNTI alto → descarte si `enable_path_d_intra_radio_gate=true`.
   - Pixel a 8 km, dNTI alto → pasa.
   - Volcán sin `mirova_modis_max_path_d_km` configurado → fallback a
     `inner_radius_km`.
   - Flag OFF → comportamiento legacy idéntico.
2. **Script offline** `scripts/build_mirova_modis_radius.py` que parsea
   `latest_consolidado.csv` y emite `volcanoes_radii_modis.yaml` patch
   con `mirova_modis_max_path_d_km: <p95>` per-volcán Tier A.
3. **Profile A/B**:
   `pipeline/profiles/mirova_equivalent_f_s81_a_intra_radio_enabled.yaml`
   y `_disabled.yaml`, cada uno con `data_subdir` aislado (patrón S25).
4. **Workflow A/B GH Actions**: `reproc-ab-f-s81-a-intra-radio.yml`
   matrix max-parallel=1 sobre 11 Tier A × 45 días.
5. **Audit independiente**: `experiments/<N>_r2_f_s81_a_audit.py` con
   métricas precisión MODIS, recall vs ALERTA, FPs por volcán-mes,
   ratio mediano contra MIROVA. Output: tabla comparativa enabled vs
   disabled.
6. **R3 audit cruzado**: cero records nuevos con `final_hotspot_source
   == 'eruption'` cuyo cluster esté a `dist > R_mirova_modis`.

**Umbrales paridad MIROVA esperados** (CLAUDE.md):
- Precisión MODIS Tier A: actual ~0.4-0.5 → objetivo ≥0.70.
- Recall MIROVA ALERTA: actual ~0.85-0.92 → mantener ≥0.85 (Lascar,
  PCC summit).
- FPs por volcán-mes: actual 70-100 → objetivo ≤15.

## Plan de implementación Fase 2

| # | Tarea | Estimado |
|---|---|---:|
| 1 | Tag defensivo `pre-s8N-f-s81-a-gate-modis-path-d` + push | 5 min |
| 2 | Script `build_mirova_modis_radius.py` + correr sobre CSV consolidado | 1.5 h |
| 3 | Test sintético `tests/test_modis_path_d_intra_radio_gate.py` (TDD) | 1 h |
| 4 | Implementación gate en `pipeline/process_modis.py` detrás de flag `enable_path_d_intra_radio_gate` | 2 h |
| 5 | Yaml patch volcanoes con `mirova_modis_max_path_d_km` per Tier A | 30 min |
| 6 | 2 profiles `mirova_equivalent_f_s81_a_intra_radio_{enabled,disabled}.yaml` | 30 min |
| 7 | Workflow GH Actions A/B max-parallel=1 | 30 min |
| 8 | Audit script + decisión adopción | 2 h |
| 9 | Si adopción: PR a `mirova_equivalent.yaml`, R8 verificación dashboard | 1 h |

**Total**: 9 horas Fase 2 completa.

## Pre-mortem (R4 obligatorio)

**¿Qué puede salir mal?**

1. **R_mirova_modis demasiado restrictivo** para volcanes con eventos
   reales `far`: si MIROVA históricamente solo vio ALERTA cerca del
   cráter pero ahora hay un flujo de lava extendido, el percentil 95
   histórico no lo permite. **Mitigación**: usar `max(p95, p99) +
   margen` (ej. 1.5×) y revisar manualmente Tier A con eventos
   recientes extensos.

2. **Tupungatito caso singular**: tiene OSF=0 ALERTAs MIROVA históricas
   pero NRT=60 ALERTAs (project_tiering_osf_v2_5). El percentil 95
   sobre NRT puede ser válido pero hay que verificar que sample es
   suficiente. **Mitigación**: regla `n_alertas ≥ 10` antes de usar
   p95, sino fallback a `inner_radius_km`.

3. **Los 92 FPs `summit` no se resuelven con este gate**: están dentro
   de `inner_radius_km`. **Mitigación**: documentar como Fase 2.5
   pendiente (gate adicional intra-summit), no bloqueante para Fase 2.

4. **Path D útil para señal sub-pixel `far` legítima**: hipotéticamente
   un cono parásito a 8 km del vent principal podría tener señal real
   solo vía Path D. **Mitigación**: el percentil 95 acomoda eso (si
   MIROVA históricamente publica a 8 km, p95 ≥ 8 km).

5. **Drift D9 cirrus alto NO se cura**: este gate es espacial, no
   atmosférico. Path D dentro del radio sobre cirrus alto sigue
   posiblemente disparando. **Mitigación**: tracker para Fase 3 D9
   (independiente).

## Rollback plan

Si tras adopción el recall vs ALERTA cae >0.05 en cualquier Tier A:

1. `enable_path_d_intra_radio_gate: false` en
   `mirova_equivalent.yaml` (1 commit, 1 min revert efectivo).
2. NRT cron próximo (≤2h) restaura comportamiento legacy.
3. Documentar el caso que rompió en
   `experiments/<N>_f_s81_a_recall_regression.md`.

## Datos de soporte

- `experiments/_s82_intra_radio/fase1_1_modis_classified.csv` (857
  filas, full breakdown).
- `experiments/_s82_intra_radio/fase1_1_summary.md` (cross-tabs).
- `docs/F_S81_A_FASE1_DIAGNOSIS.md` (síntesis).
- `experiments/_s81_v2_out/REPORT_S81_GAP_V2.md` (origen del audit).
- `latest_consolidado.csv` (CSV scraper MIROVA al día, root del repo).

## Dependencias

- **F46 VRP_TIR provisional gate (PR #221 mergeado S81)**: ortogonal,
  no bloquea ni es bloqueado.
- **F66 hybrid bg kernel (branch S79 abierto)**: ortogonal (VIIRS, no
  MODIS), Fase 2 puede correr en paralelo.
- **A45 + tag defensivo**: obligatorio antes de tocar
  `pipeline/process_modis.py`.
- **A47 NO paralelo `data/mirova_equivalent/`**: el A/B usa
  `data_subdir` aislados, no aplica.
- **D9 cap path D cirrus alto**: relacionado pero independiente.
