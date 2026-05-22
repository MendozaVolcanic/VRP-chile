# A33 — Trust but verify SHAs: caso falsa alarma F2.5.b (2026-05-22)

> **Lección operacional crítica derivada de S72**. Documenta caso donde un audit pixel-level reportó "bug grave" que resultó ser falsa alarma por confusión de versiones del pipeline. Sirve como guard-rail para futuras auditorías comparativas.

## 1. La falsa alarma F2.5.b

### 1.1 Reporte original (incorrecto)

Subagente F2.5.b (S72 2026-05-22) reportó:

> *"El cap NO está capeando a 5 MW — está **aniquilando** clusters chicos (`pc.vrp_mw=1 MW → 0.007 MW`). Probable razón: cap aplicado a pixels pre-cluster colapsa pixels bajo threshold y degenera primary_cluster a 1-pixel sub-floor. **Worth investigar**."*

Ejemplo flagged: Lascar VIIRS NOAA21 2026-03-19 06:36 con `pc.vrp_mw: 0.667 → 0.008 MW` (reducción 83×).

**Conclusión derivada** (también incorrecta): el cap S71 (PR #112) tiene un bug grave que aniquila TPs reales en Lascar Tier A Alto. Cap eliminación D9 viene de aniquilación accidental.

### 1.2 Verificación F2.6.a (correcto)

Code review exhaustivo de la implementación del cap en `pipeline/process_modis.py`, `process_viirs.py`, `process_viirs_mod.py`:

- **Implementación correcta en 6 sitios** (3 procesadores × 2 lugares: eruption initial + Test 1 recompute).
- Pattern: `if _path_d_cap_active and _vrp_c > PATH_D_ONLY_CAP_MW: _vrp_c = PATH_D_ONLY_CAP_MW`.
- Strict `>`, post-cluster, no truncation.

**Verificación empírica decisiva**: en `data/mirova_equivalent_path_d_cap_v1/`, **467 records con `d9_capped=True`**, TODOS con `pc.vrp_mw=5.0` exacto. **Cero records capped con vrp<5**. El cap NO aniquila sub-MW.

El record Lascar 2026-03-19 06:36 reportado por F2.5.b tiene `d9_capped: None` → **el cap NUNCA disparó allí**. La reducción 0.667→0.008 NO es atribuible al cap.

### 1.3 Origen real de la reducción

F2.5.b mezcló registros producidos por **2 versiones distintas del pipeline**:

| Vintage | Commit | Pipeline state | Record `pc.vrp_mw` |
|---|---|---|---|
| S26-vintage | `4c1762f` | Pre-S38/S39/S40/S46/S58/S61/S71 — pipeline antiguo | 0.667 MW |
| S71-actual | `55f76e2` | Post-S38-S61 con dual_roi_BT + vent_anchored + local_kernel_bg + test1_lbg_global + drift234 + cap S71 | 0.008 MW |

La reducción 83× es **deriva arquitectural acumulada S26→S71**, NO el cap S71.

## 2. Causa raíz del error de subagente

F2.5.b extrajo el "record baseline pre-cap" del commit `2a6c8f8` (parent de PR #112). Pero ese commit **YA tenía** todas las adopciones S38-S61 — NO era "pipeline vintage" para todos los records. Algunos records en `data/mirova_equivalent/Lascar.json` fueron producidos en reprocs anteriores (S26 histórico, `4c1762f`) y NUNCA fueron reprocesados con pipeline actual hasta el reproc S71 cap dispatch.

**El error**: asumir que un dataset compartido entre commits significa que los records fueron producidos por ese pipeline. **NO**. Los datasets son acumulativos; un commit puede contener records de procesos anteriores que NO se reprocesaron.

## 3. Aprendizaje meta A33

**A33 (S72 2026-05-22) — Trust but verify SHAs**:

Cuando se compara `data/<setup_A>/<vol>.json` vs `data/<setup_B>/<vol>.json` en audits cross-comparativos:

1. **Verificar SIEMPRE qué SHA del pipeline produjo cada record**. El commit que tiene el archivo NO es necesariamente el pipeline que produjo los records. Pueden ser legacy de reprocs anteriores.

2. **Reprocesar al MISMO SHA** antes de comparar setups. La única comparación válida es:
   - Setup A reprocesado en SHA X.
   - Setup B reprocesado en SHA X (igual).
   - Diferencias atribuibles SOLO al cambio de profile/feature.

3. **Si reprocesar es caro**, documentar EXPLÍCITAMENTE qué pipelines vintage produjeron los records de cada lado.

4. **Field diagnostic obligatorio**: agregar campo `pipeline_sha` o `produced_by_commit` a cada record JSON para trazabilidad. Sin esto, las comparativas cross-version son inválidas.

## 4. Implicaciones retroactivas

### 4.1 F2.2 audit verdict — INVÁLIDO parcialmente

F2.2 comparó `data/mirova_equivalent/` (mix de vintages) vs `data/mirova_equivalent_unsuitable_filters_v1/` (S71-actual). Las diferencias atribuidas a "fix unsuitable filters" pueden ser deriva S26→S71 + cap S71 mezclados.

**Conclusión revisada**: el bug D9 100% elim observado en F2.2 ES real, pero **principalmente atribuible al cap S71 + deriva acumulada**, NO específicamente a unsuitable filters / K1 retire (F2.4 ya confirmó que los flags split no afectan output).

### 4.2 F2.3 + F2.4 — VÁLIDO

F2.4 audit comparó 3 setups producidos en el MISMO SHA (`dc4b286` post-PR #122). Los 3 dan output idéntico → confirma que flags split no aportan. F2.4 conclusion stand.

### 4.3 F2.5.b — INVÁLIDO

Lo del "cap aniquilador" es falsa alarma. Cap S71 funciona como diseñado. No hay bug para fix.

### 4.4 Lascar regression -9.3pp recall — sigue REAL pero re-atribuida

NO es por unsuitable filters (F2.4).
NO es por K1 retire (F2.4).
NO es por cap S71 (F2.6.a).

Es por **deriva arquitectural acumulada S26→S71**. Causa específica pendiente F2.6.c (bisección por feature).

## 5. Acciones derivadas

1. ✅ **6 tests anti-regresión cap** añadidos (PR #123). Blindan la semántica para evitar futuros reports falsos como F2.5.b.
2. 🔄 **F2.6.b A/B reproc no_cap_v1**: comparativa LIMPIA cap-on vs cap-off en pipeline ACTUAL. Único way de saber si el cap S71 actualmente aporta operacionalmente.
3. 🔄 **F2.6.c bisección S38-S61**: identificar feature específica que introdujo la deriva Lascar 0.667→0.008.
4. ⚠️ **Pendiente S73**: agregar campo `pipeline_sha` a record schema para trazabilidad futura.

## 6. Otros documentos afectados por correcciones

- `docs/MIROVA_DIVERGENCES.md` D9 — sub-sección "S71 T1 Fase 2 audit verdict" sigue válida (cap S71 sí elimina D9).
- `docs/MIROVA_DIVERGENCES_CATALOG_S71.md` — sub-sección F2.2 verdict requiere corrección retroactiva: el "fix" testeado era mix de cap S71 + deriva pipeline, no específicamente unsuitable filters.
- `docs/TUPUNGATITO_FINDING_S72.md` — sin cambios, propuesta `mirova_center` sigue válida.
- `docs/BEYOND_MIROVA_EXTENSIONS.md` — agregar lección A33 al backlog.

## 7. Lecciones meta sobre el proceso de investigación

**A33 confirma que el proceso "probar todo, descartar" funciona — pero requiere validación cruzada**. Sin F2.6.a code review, habríamos:

- Implementado un fix innecesario (cambio en cap que ya funcionaba).
- Roto los tests anti-regresión cap del paper future.
- Empeorado el operacional.

**El subagente F2.5.b reportó con alta confianza una conclusión incorrecta**. Sin verificación de SHAs en F2.6.a, esa conclusión habría sido adoptada. **El controller (yo Claude) tampoco detectó la confusión** porque no verificó manualmente los SHAs antes de aceptar el reporte. Lección: **verificar siempre el SHA productor de los records antes de adoptar conclusión de audit comparativo**.
