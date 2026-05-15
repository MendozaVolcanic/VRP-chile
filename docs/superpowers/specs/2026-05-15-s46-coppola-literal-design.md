# S46 Design — Coppola 2016a Literal Round 1 A/B

**Fecha**: 2026-05-15 (brainstorming completo S45+R6 cierre)
**Status**: Design APPROVED — listo para implementación con `writing-plans`
**Autor**: Nicolás + Claude (Brainstorming Skill)

---

## Misión vinculante (MISSION.md aplicada)

Reproducir lo más fielmente posible MIROVA NRT sobre volcanes chilenos
usando ÚNICAMENTE metodología documentada en papers MIROVA core. Implementar
filtros Coppola 2016a SP426.5 literal completos.

### Las 3 preguntas aplicadas

Para cada drift propuesto (Drifts #1, #2+#3, #4, #7):

1. **¿En papers MIROVA core?** SÍ — Coppola 2016a Tabla 1 + texto literal:
   - Drift #1: Test 1 K1 "discarded for further steps" (sp426_5.txt:298-300)
   - Drift #2+#3: Tests 2 ∧ 3 conjunción (sp426_5.txt:316-325)
   - Drift #4: second-pass adyacente (sp426_5.txt:347-356)
   - Drift #7: A_pix nadir 1 km² fijo (sp426_5.txt:201-202, 384)

2. **¿Cierra divergencia documentada?** SÍ — R6 audit identificó cada drift
   en `docs/MIROVA_DIVERGENCES.md` S45+R6 sección.

3. **¿Alineación interna?** SÍ — corregir drift histórico, no agregar
   features nuevas. Parches S33-S44 son compensación de estos drifts.

**Variante 13 `_dibella_n12_viirs_only`**: exploración objetivo (2) "mejor
que MIROVA". NO clon literal. Documentada explícitamente como experimental.

---

## Contexto S45+R6 y revelaciones

### R6 audit independiente (21 drifts identificados, ec14991 commit)

5 ALTA severidad, 5 elegidos para Ronda 1:
- **#1**: Test 1 K1 `nti_path_hot` mal-usado como hot_mask (paper: saturation)
- **#2+#3**: First-pass `contextual_dnti_hot_mask` solo dNTI (paper: Tests 2∧3 + dETI + AND + rama C2·σ)
- **#4**: `second_pass_adjacent` OFF (paper: obligatorio)
- **#5**: `primary_cluster.vrp_mw` vs Σ alerted (REINTERPRETADO post-insight TIF — ver abajo)
- **#7**: MODIS `sec³(θz)` vs A_pix nadir-fijo (probable causa ratio 1.21×)

### Insight TIF MIROVA rescatado de s15-dev (commit 64bd37d)

> "El TIF NO es VRP per-pixel sumable. Es producto de visualización del campo
> de radiancia. El VRP reportado viene de **selección específica post-filtros**,
> NO suma del TIF."

**Reinterpretación drift #5**: Eq.8 aplica sobre pixels post-filtros
Tests 1∧2∧3∧second-pass. Con filtros completos, queda cluster específico
naturalmente. NO Σ scene-wide. **Implementar filtros completos puede deprecar
parches S33-S44 automáticamente** (Fase 3 post-Ronda 1).

### Hipótesis arquitectural S46

Los parches S35-S44 (vent_anchored, pixel filter, sanity cap, vrp>0 priority,
final_hotspot_source=test1) son **compensación de filtros incompletos**.
Si implementamos Coppola 2016a literal completo, parches podrían volverse
innecesarios.

---

## Estructura A/B Ronda 1 — 13 variantes paralelas

### Tabla variantes

| # | Variante | Familia | Cambio | Hipótesis |
|---|---|---|---|---|
| 1 | `_baseline_s44` | Control | Operacional actual | Baseline F1 |
| 2 | `_drift1a_only` | Drift #1 | Retirar `nti_path` del `hot_mask` | Test 1 K1 era ruido |
| 3 | `_drift1b_only` | Drift #1 | `bg_vals` excluye Test 1 K1 active | Mejor estimación t_bg |
| 4 | `_drift1ab_only` | Drift #1 | Ambos | Sinergia drift1 |
| 5 | `_drift23_only` | Drifts #2+#3 | First-pass Tests 2 ∧ 3 + C2·σ uniforme (C1=0.003) | Filtros estrictos |
| 6 | `_drift23_dual_only` | Drifts #2+#3 | First-pass + **dual-ROI Tabla 2** (summit C1=0.003 / scene C1=0.010) | Paper Table 2 literal |
| 7 | `_drift4_only` | Drift #4 | Second-pass ON, first-pass legacy | Recapture adyacente |
| 8 | `_drift234_only` | Combo | Tests 2 ∧ 3 + dual-ROI + second-pass | Coppola literal completo |
| 9 | `_drift7_modis_only` | Drift #7 | MODIS A_pix=1km² nadir-fijo | Ratio 1.21× ← sec³ |
| 10 | `_drift7_viirs_only` | Drift #7 | VIIRS I+M nadir-fijo | Verificar factor 1-2x VIIRS |
| 11 | `_drift7_both_only` | Drift #7 | Los 3 sensores nadir-fijo | Drift #7 completo |
| 12 | `_coppola_full` | Combo total | drift1ab + drift234 + drift7_both | Clon literal completo |
| 13 | `_dibella_n12_viirs_only` | EXPERIMENTAL | VIIRS Z-score n=12 noche / n=8 día | Objetivo (2) — NO MIROVA |

### Compute estimado

- 13 variantes × 11 Tier A × 30d = **143 jobs**
- GitHub Actions max-parallel=8 → ~18 batches × 5-10 min = **2-3h total**
- Window inicial Ronda 1: 30d. Fallback 15d si timeouts.

### Estructura archivos

- **13 profile YAMLs** en `pipeline/profiles/_<variant>.yaml` (extends `mirova_equivalent.yaml`)
- **1 workflow parametrizado** `.github/workflows/reproc-s46-coppola-literal-ab.yml`
- **Audit script** `experiments/87_audit_s46_round1.py` (reusa pattern S33 audit_76)
- **Output durable** `data/_<variant>/<volcano>.json` (NO sobreescribe operacional)

---

## Drift #1 design — Test 1 K1 a saturation mask

### Paper

Coppola 2016a SP426.5 (sp426_5.txt:298-300):
> "Pixels that satisfy Test 1 are flagged as 'active' and **subsequently
> discarded (unsuitable) for further steps**"

Test 1 K1 propósito: filtrar pixels saturados ANTES de calcular mean/std bg.
NO reportarlos como hotspots.

### Implementación

**Drift #1a** (variante 2): retirar `nti_path` del `hot_mask`. Pixels Test 1 K1
SE SIGUEN registrando como `diag_n_nti_path` (tracking) pero NO contribuyen al
`hot_mask_2d` reportable.

```python
# En los 3 procesadores
if ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK:
    nti_path_diagnostic = (~saturation_mask) & roi_mask & (nti > NTI_K1_NIGHT)
    diag_n_nti_path = int(np.sum(nti_path_diagnostic))
    nti_path_hot = np.zeros_like(roi_mask)  # NO contribuye
else:
    nti_path_hot = (~saturation_mask) & roi_mask & (nti > NTI_K1_NIGHT)
    diag_n_nti_path = int(np.sum(nti_path_hot))
```

**Drift #1b** (variante 3): `bg_vals` excluye Test 1 K1 active antes de
computar `t_bg/std_bg`.

```python
# En los 3 procesadores, antes de bg_vals computation
if ENABLE_TEST1_K1_BG_EXCLUDE:
    test1_k1_active_mask = (~saturation_mask) & roi_mask & (nti > NTI_K1_NIGHT)
    bg_mask = bg_mask & ~test1_k1_active_mask
bg_vals = bt_mir[bg_mask & ~np.isnan(bt_mir)]
```

**Drift #1ab** (variante 4): ambos flags ON.

### Tests TDD (`tests/test_drift1_test1_k1_saturation.py`)

Ver design Sección 6 brainstorming — cobertura ambos drifts off/on.

---

## Drift #2+#3 design — First-pass Tests 2 ∧ 3 + dETI + AND + rama C2·σ + dual-ROI

### Paper

Coppola 2016a SP426.5 (sp426_5.txt:316-325):
```
Test 2:  dNTI > C1   OR   dNTI > μ_dNTI + C2·σ_dNTI
Test 3:  dETI > C1   OR   dETI > μ_dETI + C2·σ_dETI
pixel active ⇔ Test 2 ∧ Test 3
```

Tabla 1 valores (noche):
- C1: 0.003 ROI1 summit / 0.010 ROI2 scene
- C2: 5 ROI1 / 10 ROI2
- K1: -0.8 (común)

### Implementación

Nueva función `first_pass_tests_2_and_3` en `pipeline/detection_context.py`:

```python
def first_pass_tests_2_and_3(
    nti: np.ndarray,
    nti_app: np.ndarray,
    bt: np.ndarray,
    roi_mask: np.ndarray,
    dist_km: np.ndarray,
    t_bg: float,
    bt_sanity_k: float,
    *,
    c1_dnti_summit: float = 0.003,
    c1_deti_summit: float = 0.003,
    c2_dnti_summit: float = 5,
    c2_deti_summit: float = 5,
    inner_km: float,
    c1_dnti_scene: float = None,  # dual-ROI si provided (0.010)
    c1_deti_scene: float = None,
    c2_dnti_scene: float = None,  # 10
    c2_deti_scene: float = None,
    min_bg_pixels: int = 10,
) -> Tuple[np.ndarray, dict]:
    """Coppola 2016a SP426.5 first-pass — Tests 2 ∧ 3 conjunción + dual-ROI.

    Reusa compute_eti_scene_quadratic (helper existente) para ETI.
    Computa dNTI y dETI vía 8-neighbor mean.
    Tests 2 y 3 con rama OR estadística (μ+C2σ).
    Dual-ROI thresholds según is_summit (Tabla 2 paper).

    Returns:
        (hot_mask, diag_dict) con campos n_first_pass_pixels, mu_dnti, sd_dnti, ...
    """
    # 1) ETI via helper existente
    mask_valid_eti = roi_mask & np.isfinite(nti) & np.isfinite(nti_app)
    eti = compute_eti_scene_quadratic(nti, nti_app, mask_valid_eti)

    # 2) dNTI y dETI vía 8-neighbor arithmetic mean (paper línea 242-244)
    mean_nti = _nanmean_8neighbors_fast(nti)
    mean_eti = _nanmean_8neighbors_fast(eti)
    dnti = nti - mean_nti
    deti = eti - mean_eti

    # 3) μ, σ del bg regional
    bg_mask = roi_mask & np.isfinite(dnti) & np.isfinite(deti)
    n_bg = int(np.count_nonzero(bg_mask))
    if n_bg < min_bg_pixels:
        return np.zeros_like(roi_mask), {"n_first_pass_pixels": 0, "n_bg": n_bg}
    mu_dnti = float(np.mean(dnti[bg_mask]))
    sd_dnti = float(np.std(dnti[bg_mask]))
    mu_deti = float(np.mean(deti[bg_mask]))
    sd_deti = float(np.std(deti[bg_mask]))

    # 4) Threshold por ROI (dual o uniforme)
    is_summit = dist_km <= inner_km
    dual = c1_dnti_scene is not None

    if dual:
        thr_dnti_sum = max(c1_dnti_summit, mu_dnti + c2_dnti_summit * sd_dnti)
        thr_deti_sum = max(c1_deti_summit, mu_deti + c2_deti_summit * sd_deti)
        thr_dnti_sce = max(c1_dnti_scene, mu_dnti + c2_dnti_scene * sd_dnti)
        thr_deti_sce = max(c1_deti_scene, mu_deti + c2_deti_scene * sd_deti)
        pass_2 = np.where(is_summit, dnti > thr_dnti_sum, dnti > thr_dnti_sce)
        pass_3 = np.where(is_summit, deti > thr_deti_sum, deti > thr_deti_sce)
    else:
        thr_dnti = max(c1_dnti_summit, mu_dnti + c2_dnti_summit * sd_dnti)
        thr_deti = max(c1_deti_summit, mu_deti + c2_deti_summit * sd_deti)
        pass_2 = dnti > thr_dnti
        pass_3 = deti > thr_deti

    # 5) Conjunción AND obligatoria + roi + bt sanity
    hot = (
        roi_mask
        & np.isfinite(dnti) & np.isfinite(deti)
        & pass_2 & pass_3
        & (bt > t_bg + bt_sanity_k)
    )

    diag = {
        "n_first_pass_pixels": int(np.sum(hot)),
        "mu_dnti": mu_dnti, "sd_dnti": sd_dnti,
        "mu_deti": mu_deti, "sd_deti": sd_deti,
        "n_bg_used": n_bg,
    }
    return hot, diag
```

Integración en `process_*.py:hot_mask_2d`:

```python
if ENABLE_FIRST_PASS_TESTS_2_AND_3:
    coppola_first_pass_hot, fp_diag = first_pass_tests_2_and_3(...)
    hot_mask_2d = coppola_first_pass_hot  # reemplaza paths legacy

    # Paths legacy se siguen calculando para DIAGNÓSTICO
    diag_n_bt_path = int(np.sum(bt_path_hot))
    diag_n_nti_path = int(np.sum(nti_path_hot))
    diag_n_dnti_ctx_path = int(np.sum(dnti_ctx_hot))
    diag_n_test1_path = int(np.sum(test1_hot))
    # NO contribuyen a hot_mask_2d
else:
    # Legacy
    hot_mask_2d = (bt_path_hot | nti_path_hot | dnti_ctx_hot | test1_hot)
```

### VIIRS thresholds (búsqueda bibliográfica completada)

Resultado: **MIROVA NO publica thresholds VIIRS específicos**. Re-usa
Coppola 2016a Tabla 1 (MODIS) tal cual. Confirmado:
- Campus 2024 La Fossa Vulcano (VIIRS adaptación) NO publica K1/C1/C2 explícitos
- Massimetti tesis describe algoritmo pero NO valores VIIRS distintos
- Di Bella 2024 propone n=12 noche pero **es INGV Catania (NO MIROVA)**

Para clon literal Ronda 1: K1=-0.8, C1=0.003/0.010, C2=5/10 uniforme los 3 sensores.

---

## Drift #4 design — Second-pass adyacente activación

### Paper

Coppola 2016a SP426.5 (sp426_5.txt:347-356):
> "active pixels may strongly modify the average values of their surroundings,
> with a consequent decrease in the dNTI and dETI values of adjacent pixels.
> To avoid this problem, step 2 (spatial analysis) is performed a **SECOND
> TIME**, being particularly careful to eliminate all of the 'active' pixels
> already detected."

### Implementación

`second_pass_adjacent` YA implementada (`detection_context.py:416-523`) con
Tests 2 ∧ 3 + dual-ROI + exclusión active del mean. Sólo flag wiring.

**Drift #4 variante 7** (`_drift4_only`): activar flag con first-pass legacy.

**Drift #4 dentro variante 8** (`_drift234_only`): activar flag con first-pass
Coppola literal (Tests 2∧3). Combina ambos pasos del paper.

```python
# Profile mirova_equivalent_drift4_only.yaml
enable_second_pass_adjacent: true
# Resto OFF
enable_first_pass_tests_2_and_3: false
enable_test1_k1_retire_from_hot_mask: false
```

```python
# En procesadores
if ENABLE_SECOND_PASS_ADJACENT:
    final_active_mask = second_pass_adjacent(
        nti, eti, active_mask=hot_mask_2d,
        c1_dnti=0.003, c1_deti=0.003,
        c2_dnti=5, c2_deti=5,
        is_summit=is_summit_mask,
        c1_dnti_scene=0.010, c1_deti_scene=0.010,
        c2_dnti_scene=10, c2_deti_scene=10,
    )
    hot_mask_2d = final_active_mask
```

---

## Drift #7 design — A_pix nadir-fijo (3 sensores)

### Paper

Coppola 2016a SP426.5 (sp426_5.txt:201-202, 384):
> "resampled within a 50×50 km grid… spatial resolution of the resampled
> MODIS pixels is 1 km" + Eq.7: "A_PIX is the pixel size (**1 km² for the
> resampled MODIS pixels**)"

### Implementación

**Variante 9** `_drift7_modis_only`: MODIS nadir-fijo, VIIRS legacy.
**Variante 10** `_drift7_viirs_only`: VIIRS I+M nadir-fijo, MODIS legacy.
**Variante 11** `_drift7_both_only`: los 3 sensores nadir-fijo.

```python
# pipeline/scan_geometry.py
def modis_pixel_areas(shape, scan_angles_deg, ..., nadir_fixed=False):
    if nadir_fixed:
        return np.full(shape, 1_000_000.0)  # 1 km² in m²
    # Else: existing sec³ behavior

def viirs_pixel_areas(sensor_zenith_deg, nadir_area_m2, nadir_fixed=False):
    if nadir_fixed:
        return np.full_like(sensor_zenith_deg, nadir_area_m2)
    # Else: existing linear factor 1-2x

# WOOSTER_COEFF queda igual (ya internaliza A_pix nadir):
# MODIS k=18.9 × 1e6 = 18,900,000
# VIIRS M13 k=19.7 × 0.5625e6 = 11,081,250
# VIIRS I04 k=18.0 × 140625 = 2,531,250
```

### VIIRS legacy comment preservación

Si A/B muestra VIIRS nadir-fijo = legacy factor 1-2x (calibración S14 OSF
fue empírica vs nadir-fijo presumiblemente), confirma comment scan_geometry.py:182-189:
"residual systematic bias vs MIROVA may still exist; it must come from a
different source not from pixel area." → drift #7 VIIRS es no-op (info valiosa).

---

## Variante 13 — Di Bella n=12 noche VIIRS (experimental objetivo 2)

### Origen
Di Bella et al. 2024 (Advancing Volcanic Activity Monitoring) propone Z-score
n=12 noche VIIRS. **Di Bella es INGV Catania (NO MIROVA, regla S26)**.

### Implementación
```python
# pipeline/profiles/_dibella_n12_viirs_only.yaml
extends: mirova_equivalent.yaml
description: "EXPERIMENTAL — Di Bella 2024 n=12 noche VIIRS. NO clon literal MIROVA."
data_subdir: _dibella_n12_viirs_only

# En VIIRS procesadores SOLO: usar C2_override=12 noche (en lugar de 5/10 Coppola)
enable_first_pass_tests_2_and_3: true  # base Coppola
viirs_c2_override_night: 12  # Di Bella scoring
# MODIS legacy intacto
enable_nadir_fixed_pixel_area_modis: false
```

### Documentación explícita
- NO viola MISSION.md regla 1 porque se prueba como EXPERIMENTAL aislado
- NO adoptable operacionalmente — sería divergencia clon
- Info: ¿n=12 VIIRS mejora recall vs Coppola C2=5/10?
- Si gana significativo → backlog objetivo (2) explorar más

---

## Tests sintéticos TDD

Cobertura por drift, ver Sección 6 brainstorming. Archivos:

```
tests/
├── test_drift1_test1_k1_saturation.py    # variantes 2, 3, 4
├── test_drift23_first_pass_tests_2_3.py  # variantes 5, 6, 8
├── test_drift4_second_pass_enabled.py    # variante 7
├── test_drift7_nadir_fixed_pixel.py      # variantes 9, 10, 11
├── test_drift13_dibella_n12_viirs.py     # variante 13
├── test_r2_pixel_level.py                # 5 casos canónicos (skip si TIF n/a)
└── test_s46_integration.py               # variantes 8 (drift234), 12 (coppola_full)
```

Política TDD obligatoria:
1. Tests escritos ANTES de implementación
2. Tests fail con código actual (baseline)
3. Implementación hasta tests pass
4. Suite verde antes de commit
5. Granules sintéticos in-memory (sin mocks data crítica)

R2 pixel-level (5 casos handoff S46): marcados `@pytest.mark.r2_pixel_level`,
skip automático si TIF no disponible en `mirova-tif-archive/index.csv`.

---

## Métricas + tabla registro durable

### Métricas core

```python
TP = "ALERTA_TERMICA MIROVA capturada (pc.vrp > 0, ±30min)"
FN = "ALERTA_TERMICA MIROVA NO capturada"
FP = "Detección nuestra coincide con FALSO_POSITIVO MIROVA"

Precision = TP / (TP + FP)
Recall = TP / (TP + FN)
F1 = 2 P R / (P + R)
ratio_vrp_median = mediana(pc.vrp_mw / mirova.VRP_MW) sobre TPs
delta_dist_km_median = mediana |pc.centroid_dist_km - mirova.Distancia_km|
```

### Per-sensor agregado

Tabla: 13 variantes × 3 sensores (MODIS, VIIRS375, VIIRS750) = 39 filas.
Permite identificar:
- Drift #7 MODIS: solo afecta rows MODIS
- Drift #234: probable mayor impact VIIRS375 (más pixels Test3 dETI)
- Variante 13: solo afecta VIIRS rows

### Decisión automática post-Ronda 1

```python
for variante in variantes:
    delta_f1 = f1[variante] - f1["_baseline_s44"]
    delta_recall = recall[variante] - recall["_baseline_s44"]

    if delta_f1 > 0.02 and delta_recall > 0:
        decision = "WIN — adopt operacional"
    elif delta_f1 > 0 and delta_recall >= -0.02:
        decision = "NEUTRAL win — adopt for paper alignment"
    elif delta_f1 > -0.02:
        decision = "NEUTRAL — defer Ronda 2"
    else:
        decision = "REGRESS — investigate why"
```

### Outputs durables

- `experiments/87_results.md` — tabla legible
- `experiments/87_results.json` — data crudo
- `data/_<variant>/<volcano>.json` — outputs preservados
- Tag `s46-round1-results` post-completa

---

## Pre-mortem completo (A-P, 8 escenarios)

### A — Coppola literal baja recall catastrófico
Diagnóstico: aislar drift culpable vía variantes individuales. Mitigación:
NO mergear `_coppola_full`. Adoptar solo wins individuales. Backlog VIIRS recalibration.

### B — Drift #1 no impacta
Esperado por audit S45 (0 records únicos). Adoptar para alineación paper.

### C — Drift #7 MODIS NO baja ratio
Investigar drift #21 (bg ring contamination), Aveni 2025 GRL TIR retrieval.

### D — Drift #2+#3 ETI numerical errors
Fallback safe: si <50% pixels válidos ETI, NO aplicar Test 3 + diag.

### E — GitHub Actions timeout
Window 15d Ronda 1 inicial. Split workflows por familia drift.

### F — R2 pixel-level no validable (gap TIF)
Re-scraper Mirova-v1 ANTES Ronda 1. Sin R2, decisión empírica F1 + ratio.

### G — Deprecación parches S33-S44 regresa edge cases
Variante intermedia `_coppola_full_with_legacy_safety` (Coppola literal + sanity cap S41). 30d producción + 0 regresión antes deprecar.

### H — NRT cron concurrencia
A/B usa `data/_<variant>/` separado. NRT cron solo escribe `data/mirova_equivalent/`. Sin race condition.

### I — Schema backward compat dashboard
Schema additive-only. Tests frontend con records nuevos. Audit retro-compatible (default None).

### N — Calibración VIIRS no apropiada
Tabla 1 valores MODIS pueden no funcionar VIIRS. Backlog: ajustar C2 VIIRS empírico (NO Ronda 1). Variante futura objetivo (2).

### P — Drift residual no identificado por R6
Si `_coppola_full` < baseline, hay mecanismo MIROVA no replicado. Acción:
- R6 audit extendido sesión siguiente
- Pixel-by-pixel TIF vs nuestros records cuando archivo crezca
- Escalación: contactar Diego Coppola directo

---

## Plan ejecución

### Pre-implementación
- [x] Brainstorming completo (este doc)
- [ ] Spec self-review (próximo paso)
- [ ] User reviews written spec
- [ ] Invocar `writing-plans` para implementación step-by-step

### Implementación (writing-plans output)
- [ ] Branch `s46-coppola-literal-round1` desde main
- [ ] Tests sintéticos TDD por drift (escribir ANTES)
- [ ] Implementación drifts (`first_pass_tests_2_and_3`, flags wiring)
- [ ] 13 profile YAMLs en `pipeline/profiles/`
- [ ] Workflow `.github/workflows/reproc-s46-coppola-literal-ab.yml`
- [ ] Audit script `experiments/87_audit_s46_round1.py`
- [ ] Suite tests verde (objetivo 290+/0/0)

### Ejecución A/B
- [ ] Re-scraper Mirova-v1 CSV (ground truth fresco)
- [ ] Verificar `mirova-tif-archive` cobertura para R2
- [ ] Disparar workflow Ronda 1 — 143 jobs paralelos
- [ ] Esperar resultados (~2-3h)
- [ ] Correr audit script → `experiments/87_results.md`

### Decisión post-Ronda 1
- [ ] Análisis tabla F1 + ratio + delta_dist per variante
- [ ] Identificar wins / neutrals / regress
- [ ] Decisión arquitectural Ronda 2 según resultados:
  - Caso A (todos wins) → `_coppola_full` vs baseline final
  - Caso B (parcial wins) → `_winners_only`
  - Caso C (regress inesperado) → debugging específico

### Adopción operacional (post-Ronda 2)
- [ ] Update `mirova_equivalent.yaml` con flags winners
- [ ] Migración `data/_<winner>/` → `data/mirova_equivalent/`
- [ ] PR con: design doc + tests + implementación + audit results
- [ ] Review Nicolás antes mergear
- [ ] Verificación R8 (URL pública post-deploy)
- [ ] Tag `s46-coppola-literal-adopted`

---

## Reglas R1-R8 aplicadas

- **R1** unit tests cada función crítica: ✅ `first_pass_tests_2_and_3` + drifts
- **R2** pixel-level vs MIROVA TIF: ✅ `tests/test_r2_pixel_level.py` 5 casos
- **R3** audit independiente: ✅ `experiments/87_audit_s46_round1.py`
- **R4** pre-mortem: ✅ 8 escenarios A-P
- **R5** brainstorming obligatorio: ✅ este doc
- **R6** cuestionar resultados >30%: ✅ decisión automática thresholds
- **R7** synthetic tests: ✅ TDD por drift
- **R8** validación URL pública: ✅ post-adopción

---

## Referencias

### Papers MIROVA core
- **Coppola 2016a SP426.5** — `documentacion/sp426.5.pdf` + `sp426_5.txt`
- **Coppola 2024 Springer chapter** — `documentacion/coppola2024_chapter.txt`
- **Coppola 2025 Stromboli BV** — `documentacion/s00445-025-01932-y.pdf`
- **Massimetti 2024 JGR Stromboli 10y** — `documentacion/nuevos/JGR Solid Earth - 2024 - Massimetti...pdf`
- **Laiolo 2017** — `documentacion/nuevos/laiolo2017.pdf`
- **Campus 2024** — `documentacion/s00445-024-01721-z.pdf`
- **Aveni 2024 RSE** — `documentacion/1-s2.0-S0034425724004140-main.pdf`
- **Aveni 2025 GRL** — `documentacion/Geophysical Research Letters - 2025 - Aveni...pdf`

### NO MIROVA (regla S26)
- Di Bella 2024 — INGV Catania (variante 13 experimental, no clon)

### Docs internos
- `docs/MISSION.md` — misión vinculante
- `docs/MIROVA_DIVERGENCES.md` sección S45+R6 — 21 drifts
- `docs/PROCESS_RULES_S33.md` — reglas R1-R8
- `docs/HYPOTHESIS_LOG.md` — hipótesis acumuladas
- `tasks/handoff_s46_2026_05_14.md` — handoff S45 → S46

### Memory persistente
- `~memory/project_s45_d9_summit_priority.md` — D9 hipótesis (refutada post-R6)
- `~memory/feedback_audit_verify_data_first.md` — lección window ficticio
- `~memory/reference_papers_mirova_canonical.md` — afiliaciones papers

---

## Sign-off

Brainstorming completado. Design APPROVED por Nicolás (interactivamente,
secciones aprobadas paso a paso). Próximo paso: spec self-review + transición
a `writing-plans` skill para implementación.
