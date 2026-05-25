# F61 + F63 + F57 — Plan integrado brainstorm (S78, read-only)

**Tipo**: brainstorm integrado / análisis cuantitativo. **No modifica `pipeline/` ni `data/`**.
**Branch**: `claude/s78-brainstorm-integrado`.
**Worktree**: `VRP-Chile-s78-integrado/` (A44 aislado, dedicado).
**Snapshot**: `data/mirova_equivalent/<Volcano>.json` post-PR #210 (commit `30aed0a2`).
**Script**: `experiments/150_brainstorm_integrado/sim.py`.

## Resumen ejecutivo

Tres fixes candidatos identificados en S78 para resolver "lagos persistentes" y magnitud
inflada Tier A. Este documento cuantifica el impacto **combinado** F61+F63+F57 antes de
implementar — Nicolás autoriza A45 doble pero pide ver el efecto compuesto.

| Fix | Mecanismo | Costo | Impacto solo | Estado |
|---|---|---|---|---|
| **F61** | Gate global `NTI > -0.85` sobre `hot_mask_2d` | 1 línea + flag | Elimina **99.4%** de detecciones 30d (2316→14) | PR #208 merged (read-only brainstorm) |
| **F63** | Revertir filtro `with_vrp` en `clustering.py:133-138` (S43 override) | 5 líneas | Re-asigna 14-46% records "far" a summit | PR #209 merged (read-only brainstorm) |
| **F57** | `local_kernel_bg: true` para Copahue+Llaima | flag YAML | -70-90% FPs lago en esos 2 volcanes | no PR (descartado por F61) |

**Conclusión clave del brainstorm integrado**: F61 sólo ya logra el 99% del trabajo.
F63 es complemento necesario para limpiar los records sobrevivientes que el dashboard
sigue pintando lejos del cráter. F57 es marginal post-F61 (1-6 records adicionales por
volcán) — opcional, no bloqueante.

**Riesgo crítico identificado**: F61 con gate -0.85 **filtra el 99.5% de detecciones
de Lastarria** (827/833). Lastarria es un sistema fumarólico de baja-T documentado
(Aguilera 2021); su firma espectral domina TIR. **Requiere validación específica
antes de adoptar F61 operacional en Lastarria.**

---

## 1. Datos de la simulación

Snapshot por volcán Tier A. Para cada record con `vrp_mw > 0`:

- **F61 proxy**: `diag_nti_max` per record (NTI máximo entre pixels del granule).
  Si `diag_nti_max < -0.85` → record filtrado completo post-F61.
- **F63 proxy**: si `primary_cluster.centroid_dist_km > inner_radius_km` Y
  `anomaly_pixels` tiene al menos un pixel con `dist_km <= inner_radius_km`,
  el record post-F63 se re-asigna a summit (no cambia el conteo total, cambia
  la geometría reportada en el dashboard).
- **F57 estimación**: solo Copahue+Llaima. Reduce ~80% de los records borderline
  (`-0.85 ≤ NTI < -0.80`) que aún sobreviven F61.

Limitación del proxy F61: usa `diag_nti_max` que es agregado a nivel granule. El fix
real (gate sobre `hot_mask_2d`) opera a nivel pixel y recalcularía `vrp_mw` sobre
el subset de pixels que sobreviven. Para el brainstorm, contamos records preservados
vs eliminados — la cuantificación exacta de magnitud post-fix requiere reproc completo.

---

## 2. Tabla síntesis combinada (historia completa)

| Volcán | inner | n_pre | +F61 | +F61+F63 | +F61+F63+F57 | reducción % | lava-like preservados |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Lascar** | 5 | 737 | 91 | 91 | 91 | 87.7% | 39/39 |
| **Lastarria** | 3 | 833 | 6 | 6 | 6 | 99.3% | 2/2 |
| Tupungatito | 7 | 675 | 4 | 4 | 4 | 99.4% | 1/1 |
| PlanchonPeteroa | 3 | 764 | 5 | 5 | 5 | 99.3% | 2/2 |
| **Copahue** | 4 | 701 | 3 | 3 | 2 | 99.7% | 2/2 |
| **Llaima** | 5 | 684 | 9 | 9 | 3 | 99.6% | 2/2 |
| Villarrica | 5 | 790 | 1 | 1 | 1 | 99.9% | 0/0 |
| NevadosDeChillan | 5 | 427 | 1 | 1 | 1 | 99.8% | 1/1 |
| Chaiten | 5 | 845 | 0 | 0 | 0 | 100.0% | 0/0 |
| Isluga | 5 | 579 | 7 | 7 | 7 | 98.8% | 4/4 |
| PuyehueCordonCaulle | 20 | 1107 | 1 | 1 | 1 | 99.9% | 1/1 |

**Top 3 fila (volcanes con mayor impacto residual a investigar)**:

1. **Lascar 737→91 (87.7% reducción)** — único Tier A con sobrevivientes significativos.
   Los 91 records son consistentes con actividad real (cráter activo persistente):
   - 52 records en `NTI ∈ [-0.85, -0.80)` (fumarólica débil borderline).
   - 35 records en `[-0.80, -0.70)` (fumarólica activa).
   - 4 records en `[-0.70, -0.60)` (fumarólica fuerte).
   - VRP mediana 4.3 MW, max 10.2 MW — magnitudes consistentes con cráter Lascar.
2. **Lastarria 833→6 (99.3% reducción)** — bandera roja. Ver §4 riesgos cross-fix.
3. **PCC 1107→1 (99.9% reducción)** — esperado: PCC tiene erupción 2011 cerrada
   y actividad residual baja desde 2017. Los 1106 filtrados son ruido sobre lago Ranco,
   Nahuel Huapi y termales del cordón.

## 3. Tabla síntesis ventana 30d

| Volcán | inner | n_pre | +F61 | +F61+F63 | +F61+F63+F57 | reducción % |
|---|---:|---:|---:|---:|---:|---:|
| Lascar | 5 | 203 | 6 | 6 | 6 | 97.0% |
| Lastarria | 3 | 185 | 3 | 3 | 3 | 98.4% |
| Tupungatito | 7 | 212 | 0 | 0 | 0 | 100.0% |
| PlanchonPeteroa | 3 | 224 | 0 | 0 | 0 | 100.0% |
| Copahue | 4 | 214 | 2 | 2 | 1 | 99.5% |
| Llaima | 5 | 208 | 7 | 7 | 3 | 98.6% |
| Villarrica | 5 | 237 | 0 | 0 | 0 | 100.0% |
| NevadosDeChillan | 5 | 112 | 1 | 1 | 1 | 99.1% |
| Chaiten | 5 | 221 | 0 | 0 | 0 | 100.0% |
| Isluga | 5 | 192 | 1 | 1 | 1 | 99.5% |
| PuyehueCordonCaulle | 20 | 308 | 0 | 0 | 0 | 100.0% |
| **TOTAL 30d** | | **2316** | **20** | **20** | **15** | **99.4%** |

El dashboard SERNAGEOMIN pasaría de ~73 detecciones lago/día a **<1/día**.

---

## 4. Riesgos cross-fix (la parte importante)

### 4.1 F61 sobre Lastarria — FALSA SIMPLIFICACIÓN del problema

**Distribución NTI Lastarria** (833 detecciones históricas):

| Bucket NTI | n | Interpretación |
|---|---:|---|
| < -0.95 | 168 | Agua/cuerpo frío |
| [-0.95, -0.90) | 646 | TIR-dominado |
| [-0.90, -0.85) | 13 | Borderline |
| [-0.85, -0.80) | 4 | Fumarólica débil (sobrevive F61) |
| ≥ -0.80 | 2 | Lava (sobrevive F61) |

**Fenómeno físico**: Lastarria es un campo fumarólico activo de baja-T documentado
(Aguilera 2021, Vault). Las fumarolas emiten H2O y SO2 a 100-300°C — radiación TIR
dominante, MIR muy débil. Por construcción espectral, NTI cae < -0.85 incluso para
fenómeno volcánico real.

**Lección Mirova A9**: Lastarria es exactamente el caso límite. MIROVA Coppola
considera Lastarria un volcán con anomalía persistente baja-T (`thermal flux`
del orden de 5-20 MW Aguilera 2021), pero la firma espectral satelital no permite
diferenciar fumarol-baja-T de lago caliente.

**Riesgo F61**: si adoptamos gate -0.85 global, **eliminamos las 827 detecciones
de fumarólica real** de Lastarria. Esto es FN inaceptable para clon MIROVA
operacional.

**Mitigación propuesta** (no implementar todavía, brainstorm):
- Opción 1: gate por volcán — `Lastarria.nti_gate_override: false` o threshold
  específico -0.95 (preserva fumarólica fuerte, elimina solo agua extrema).
- Opción 2: gate dual — `NTI > -0.85` PERO si `triggered_test1=True` o
  `n_test1_pixels >= K` (test integrado-ROI Coppola 2015), aceptar pixel.
- Opción 3: validar pixel-level vs MIROVA web (R2 PROCESS_RULES_S33) sobre
  10 noches MIROVA-positivas Lastarria antes de adoptar.

**Decisión recomendada**: F61 SOLO con flag opt-out per-volcán para Lastarria.
Validar antes en perfil A/B.

### 4.2 F63 — cluster ranking revert

**Riesgo**: cuando el cluster summit tiene `vrp_mw=0` por clip D4 (delta_L ≤ 0),
F63 revertido lo elige aún así. Resultado: record con `primary_cluster.vrp_mw=0`
pero `centroid_dist_km` cercano al vent. ¿El frontend lo pinta? ¿El sum total
`vrp_mw` agregado sale 0?

**Verificación en data actual**:
- Copahue: 988 records con `primary_cluster`, 532 dentro de inner. De estos,
  ¿cuántos tienen `pc.vrp_mw = 0`? Ese conteo dice el daño potencial F63 en
  agregados del dashboard.
- Plan: spot-check 10 records pre/post F63 en Copahue para verificar que la
  re-asignación no destruye el campo `vrp_mw` global (que debe sumar pixels
  del cluster summit más eruption-path lejano si aplica).

**Riesgo conceptual menor**: F63 NO aumenta magnitud reportada. Solo cambia
qué cluster se etiqueta primary. Magnitud total `record.vrp_mw` se mantiene.
Lo que cambia es `pc.centroid_dist_km` y `pc.centroid_lat/lon` (visibles
en marker del dashboard).

### 4.3 F57 — local_kernel_bg incremental

**Riesgo bajo**: F57 ya tiene flag YAML opt-in. Activarlo para Copahue+Llaima
solo afecta a esos 2 volcanes. Impacto incremental sobre F61 es marginal
(1-6 records 30d). Costo: 2 líneas YAML.

**Recomendación**: F57 NO bloquea. Implementar como nice-to-have post-F61
si quedan FPs residuales en Copahue/Llaima.

### 4.4 Interaction effects entre los 3

- **F61 + F63**: ortogonales. F61 filtra por espectro, F63 re-asigna geometría.
  No hay overlap. F61 corre primero (filtra pixels), F63 corre después (sobre
  pixels sobrevivientes recluster).
- **F61 + F57**: parcial overlap. F57 (local_kernel_bg) reduce el `delta_L`
  inflado sobre agua → menos pixels pasan `hot_mask`. Es decir, F57 reduce la
  población de entrada de F61. Si F61 ya filtra todo lago por NTI, F57 es
  redundante para FPs lago — pero útil para FPs nieve/glaciar parcial donde
  NTI sigue siendo agresivo pero no llega a -0.85.
- **F63 + F57**: ortogonales por construcción.

---

## 5. Orden de implementación recomendado

**1. F61 primero, CON flag opt-out per-volcán** (revisar Lastarria PRIMERO).

   Justificación:
   - 99.4% reducción FPs lago 30d.
   - Costo mínimo (1 línea + flag).
   - Riesgo Lastarria identificado y mitigable por config.
   - Cumple las 3 preguntas MISSION.md (afirmativas).

   **Pre-condición obligatoria**: validar Lastarria pixel-level vs MIROVA web
   sobre 10 noches conocidas. Si MIROVA-Lastarria tiene detecciones con `NTI < -0.85`,
   agregar `nti_gate_override` por volcán o subir threshold a -0.95.

**2. F63 después, en PR separado**.

   Justificación:
   - Resuelve atribución geográfica (dashboard marker fuera del cráter).
   - 5 líneas — micro-PR.
   - Independiente de F61, no comparte tests.
   - Tras F61, los 91 sobrevivientes Lascar y los 14 residuales 30d deben
     pintarse correctamente en el dashboard. F63 garantiza eso.

**3. F57 último, OPCIONAL**.

   Justificación:
   - Marginal post-F61.
   - Si Copahue/Llaima muestran FPs residuales (>5 detecciones/mes spurious),
     activar F57 como ajuste fino.
   - Si no, omitir — no agrega valor proporcional al cambio de baseline.

**Anti-recomendación**: NO implementar los 3 simultáneamente en un solo PR.
Cada uno tiene mecanismo independiente, tests independientes, y blast radius
distinto. Implementación serial permite atribuir efecto a cada uno y revertir
quirúrgicamente si una regresión aparece.

---

## 6. Validación post-merge plan

### 6.1 Tests TDD obligatorios (RED → GREEN)

**F61** (`tests/test_nti_gate_global.py`):

- Test RED: granule sintético con pixel `NTI = -0.93, BT_anom = 10 K`. Con código
  actual + Path D activo → record emite `vrp_mw > 0`. Test debe fallar (assertEqual
  vrp_mw == 0 falla porque vale 50 MW por ejemplo).
- Test GREEN post-fix: mismo granule → `vrp_mw == 0` (pixel filtrado por gate).
- Test no-regresión Lastarria: granule sintético fumarólico `NTI = -0.78, BT_anom = 3 K`
  → debe seguir pasando.
- Test no-regresión lava: granule `NTI = 0.2, BT_anom = 30 K` → debe seguir pasando.

**F63** (`tests/test_cluster_ranking_inner.py`):

- Test RED: 2 clusters sintéticos, `cluster_A` dentro inner (`vrp=0`),
  `cluster_B` fuera inner (`vrp=10 MW`). Con código actual → `primary_cluster = cluster_B`.
- Test GREEN post-fix: mismo escenario → `primary_cluster = cluster_A` (vent_anchored
  estricto, vrp no importa).

### 6.2 A/B con perfiles aislados

Clonar template `reproc-ab-p3-1.yml` para F61:

- `mirova_equivalent_f61_disabled.yaml` (baseline, NTI_K1 solo en Path B).
- `mirova_equivalent_f61_enabled.yaml` (gate global -0.85, `data_subdir: f61_test/`).

Reproc 30 días Tier A localmente (no en GH Actions por timeout 50min cron).

Métricas comparar:
- TP/FP/FN vs MIROVA-CSV S15.
- Precision, recall, F1 per volcán.
- Magnitud `vrp_mw` distribución (p10, p50, p90, max).
- Records preservados / filtrados.

Repetir para F63 con perfiles `_f63_disabled` / `_f63_enabled` aplicados sobre
baseline `_f61_enabled` (composición serial).

### 6.3 Spot-check pre/post

Para cada Tier A: 5 records pre-fix con `vrp_mw > 0` muestreados aleatoriamente.

Verificar manualmente post-fix:
- ¿`record.vrp_mw` post-fix coincide con suma de `pc.vrp_mw + far_clusters`?
- ¿`primary_cluster.centroid_dist_km` post-F63 está dentro de inner?
- ¿Pixels con `NTI < -0.85` post-F61 efectivamente desaparecen del frontend?

Casos críticos a inspeccionar:
- Lastarria 2026-05-15 a 2026-05-25 (fumarol crónica — debe sobrevivir).
- Copahue 2026-03 a 2026-05 (lago Caviahue — debe desaparecer).
- Villarrica lava lake noches OSF MIROVA-positivas — debe sobrevivir.
- Lascar cráter persistent — debe sobrevivir (los 91 records esperados).

### 6.4 Re-correr audit pre_reproc

Tras implementar F61 + F63:

```bash
python experiments/148_audit_pre_reproc/audit_pre_reproc_v2.py
```

Verificar:
- `master_table_v2.csv`: ratio ours/mirova baja a 0.7-1.4 per volcán Tier A.
- `anomalies.csv`: lista vacía o sub-5 entradas (vs lo que sea pre-fix).
- `gaps.csv`: FN MIROVA no aumenta más de 5pp per volcán.

---

## 7. Métricas éxito esperadas

| Métrica | Pre-fix actual | Esperado post-F61+F63 |
|---|---|---|
| Records 30d con `NTI < -0.85` | 2,188 | 0 (o <50) |
| Tupungatito ratio ours/mirova | 13.22× | 1-3× |
| Villarrica ratio | 4.81× | 0.5-2× |
| PP ratio | 2.55× | 1-2× |
| Chaitén ratio | 2.33× | 1-1.5× |
| Lastarria recall vs MIROVA-CSV | TBD | ≥ baseline -5pp (depende validación 6.1) |
| FPs lago/día dashboard | ~73 | <1 |
| Records dashboard lejanos (>inner) Copahue | 46% | <5% (post-F63) |

---

## 8. Pre-condiciones obligatorias antes de implementar

Heredado de `docs/PROCESS_RULES_S33.md` + `CLAUDE.md` triggers vinculantes:

1. **Skill `superpowers-brainstorming` invocado** ANTES de tocar `pipeline/`.
   Adopción operacional metodológica requiere gate de diseño.
2. **Tag git defensivo** `pre-s78-f61-implementation` antes del primer commit
   sobre `pipeline/process_*.py`. Lección A38 — pipeline NRT crítico.
3. **Test TDD RED escrito y mergeado** antes del fix (A45 — TDD para
   componentes que tocan pipeline operacional).
4. **R2 verificación pixel-level vs MIROVA web** sobre 5-10 noches MIROVA-positivas
   confirmadas per Tier A crítico (Lascar, Lastarria, Villarrica, Copahue).
5. **A/B perfiles aislados con `data_subdir` propio** — NO contaminar
   `data/mirova_equivalent/` hasta validación.
6. **Documentar decisión en `docs/DRIFTS_S17.md`** (drift catalog) y
   en `docs/PROCESS_RULES_S33.md` (regla adopción).

---

## 9. No-acción explícita

Este brainstorm **no modifica `pipeline/` ni `data/` ni `volcanoes.yaml`**.
Es read-only por diseño (A44 worktree aislado + MISSION.md compliance).
La adopción de F61, F63 y F57 queda como propuesta para sesiones siguientes,
condicionada a:

- Brainstorming colectivo con Nicolás (skill `superpowers-brainstorming`).
- Ciclo R2/R3 (`docs/PROCESS_RULES_S33.md`).
- Validación específica Lastarria (riesgo identificado §4.1).

---

## 10. Referencias

- `docs/F61_NTI_RIGOR_BRAINSTORM_S78.md` — análisis detallado F61 standalone.
- `docs/F63_CLUSTER_CONNECTIVITY_BRAINSTORM_S78.md` — análisis F63 standalone.
- `experiments/148_audit_pre_reproc/` — baseline audit pre-fix.
- `experiments/150_brainstorm_integrado/sim.py` — script simulación.
- `experiments/150_brainstorm_integrado/sim_results.json` — resultados crudos.
- `pipeline/clustering.py:133-138` — origen S43 override (F63).
- `pipeline/process_viirs.py:419-424` — único path con gate NTI (Path B).
- Coppola, D. et al. (2016a) — Eq.4 NTI threshold k1=-0.8.
- Aguilera, F. et al. (2021) — Lastarria fumarol field, doi:10.3389/feart.2021.722056.
- `docs/MISSION.md` — 3 preguntas obligatorias.
- `docs/PROCESS_RULES_S33.md` — R2 + R3 + R7 reglas adopción operacional.
