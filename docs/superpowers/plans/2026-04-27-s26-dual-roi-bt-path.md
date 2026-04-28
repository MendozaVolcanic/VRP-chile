# Dual-ROI N·σ en eruption-path BT — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans para ejecutar tarea por tarea.

**Goal:** Aplicar thresholds N·σ distintos summit (5σ) vs scene (10σ) en eruption-path BT (Coppola 2016a Tabla 1), análogo a P3.1 dual-ROI ya implementado en Path D dNTI. Esperado: −60-80% FPs lejanos sin tocar recall summit.

**Architecture:** Helper puro en `pipeline/detection_context.py` que computa hot_mask BT con threshold dual. Reusable en los 3 process_*.py. Profile flag `enable_dual_roi_bt` con defaults Coppola 2016a. A/B aislado vs `mirova_equivalent` para validar antes de mergear.

**Tech Stack:** numpy, pytest. No deps nuevos. Reusa `haversine_km`, `MAX_SIGMA_COMPONENT_K`, `ANOMALY_THRESHOLD_K` existentes.

---

## File Structure

- **Modify:** `pipeline/profile.py` — agregar 3 keys (`enable_dual_roi_bt`, `n_sigma_mir_summit`, `n_sigma_mir_scene`).
- **Modify:** `pipeline/detection_context.py` — nueva función `dual_roi_bt_threshold()`.
- **Modify:** `pipeline/process_modis.py` — usar helper si flag activo.
- **Modify:** `pipeline/process_viirs.py` — idem.
- **Modify:** `pipeline/process_viirs_mod.py` — idem.
- **Create:** `pipeline/profiles/_dual_roi_bt_enabled.yaml` — clon mirova_equivalent + flag on.
- **Create:** `pipeline/profiles/_dual_roi_bt_disabled.yaml` — clon mirova_equivalent (control).
- **Create:** `tests/test_dual_roi_bt.py` — 5 tests TDD.
- **Create:** `.github/workflows/reproc-ab-dual-roi-bt.yml` — workflow A/B clon de reproc-ab-test1.yml.

## Criterio de aceptación (definir éxito ANTES de codear)

**A/B 14d × 4 Tier A** (Lascar, Lastarria, Tupungatito, Chaitén):

- ✅ Recall agregado vs MIROVA NRT cae < 5 pp (de 0.80 a ≥0.75).
- ✅ FPs lejanos vrp>1MW caen ≥40% global.
- ✅ Ratio mediano VRP global cae a ≤30× (hoy 57×).

Si las 3 se cumplen → integrar a `mirova_equivalent`. Si NO → no mergear, persistir hallazgos en memoria.

---

### Task 1: Profile keys

**Files:**
- Modify: `pipeline/profile.py:121-130`
- Test: `tests/test_dual_roi_bt.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_dual_roi_bt.py
import os
import importlib

def test_profile_loads_dual_roi_bt_keys(monkeypatch):
    monkeypatch.setenv("VRP_PROFILE", "_dual_roi_bt_enabled")
    import pipeline.profile as profile
    importlib.reload(profile)
    assert profile.ENABLE_DUAL_ROI_BT is True
    assert profile.N_SIGMA_MIR_SUMMIT == 5.0
    assert profile.N_SIGMA_MIR_SCENE == 10.0
```

- [ ] **Step 2: Run test, verify it fails**

Run: `pytest tests/test_dual_roi_bt.py::test_profile_loads_dual_roi_bt_keys -v`
Expected: FAIL — profile no existe + keys no definidas.

- [ ] **Step 3: Add keys to pipeline/profile.py**

After line 124 (`ENABLE_DNTI_DUAL_ROI: bool = ...`):

```python
# S26 Dual-ROI N·σ en eruption-path BT (Coppola 2016a Tabla 1).
# Path BT (eruption) usa thresholds N·σ distintos summit vs scene.
# - summit (dist <= inner_radius_km): N·σ_summit = 5 (sensible).
# - scene  (dist >  inner_radius_km): N·σ_scene  = 10 (estricto).
# Análogo a P3.1 P3.2 que ya aplican dual-ROI en Path D dNTI.
ENABLE_DUAL_ROI_BT: bool = bool(_p.get("enable_dual_roi_bt", False))
N_SIGMA_MIR_SUMMIT: float = float(_t.get("n_sigma_mir_summit", 5.0))
N_SIGMA_MIR_SCENE: float = float(_t.get("n_sigma_mir_scene", 10.0))
```

- [ ] **Step 4: Create profile YAML _dual_roi_bt_enabled**

Copy mirova_equivalent.yaml to `pipeline/profiles/_dual_roi_bt_enabled.yaml`. Update header (S26 A/B test). Update `profile:` and `data_subdir:` to `_dual_roi_bt_enabled`. Add to thresholds:
```yaml
  n_sigma_mir_summit: 5.0
  n_sigma_mir_scene: 10.0
```
Add to paths:
```yaml
  enable_dual_roi_bt: true
```

- [ ] **Step 5: Create profile YAML _dual_roi_bt_disabled**

Copy mirova_equivalent.yaml to `_dual_roi_bt_disabled.yaml`. Solo cambia `profile:` y `data_subdir:` a `_dual_roi_bt_disabled` (control mirror operacional).

- [ ] **Step 6: Run test, verify pass**

Run: `pytest tests/test_dual_roi_bt.py::test_profile_loads_dual_roi_bt_keys -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add pipeline/profile.py pipeline/profiles/_dual_roi_bt_*.yaml tests/test_dual_roi_bt.py
git commit -m "S26 T1 — profile keys ENABLE_DUAL_ROI_BT + A/B profiles"
```

---

### Task 2: Helper `dual_roi_bt_threshold` puro

**Files:**
- Modify: `pipeline/detection_context.py` (final del archivo)
- Test: `tests/test_dual_roi_bt.py` (agregar tests)

- [ ] **Step 1: Write failing tests**

Append to `tests/test_dual_roi_bt.py`:

```python
import numpy as np
from pipeline.detection_context import dual_roi_bt_threshold

def test_dual_roi_bt_summit_lower_threshold_than_scene():
    """Pixel summit con ΔBT=4K SOBRE bg debería pasar 5σ pero no 10σ."""
    bt = np.full((10, 10), 270.0)  # bg uniforme
    bt[5, 5] = 274.0  # summit pixel +4K
    dist_km = np.zeros((10, 10))
    dist_km[5, 5] = 1.0  # dentro inner_km
    roi_mask = np.ones((10, 10), dtype=bool)
    t_bg = 270.0
    std_bg = 0.5  # sigma chico
    # 5σ = 2.5K → +4K pasa. 10σ = 5K → +4K NO pasa.
    hot_summit_only = dual_roi_bt_threshold(
        bt=bt, roi_mask=roi_mask, dist_km=dist_km, t_bg=t_bg, std_bg=std_bg,
        inner_km=3.0, n_sigma_summit=5.0, n_sigma_scene=10.0,
        anomaly_floor_k=2.0, max_sigma_cap_k=7.0,
    )
    assert hot_summit_only[5, 5] == True
    # Pixel scene similar (mismo +4K) pero a 5km no debería pasar
    bt2 = np.full((10, 10), 270.0)
    bt2[5, 5] = 274.0
    dist_km2 = np.full((10, 10), 5.0)  # todo scene
    hot_scene = dual_roi_bt_threshold(
        bt=bt2, roi_mask=roi_mask, dist_km=dist_km2, t_bg=t_bg, std_bg=std_bg,
        inner_km=3.0, n_sigma_summit=5.0, n_sigma_scene=10.0,
        anomaly_floor_k=2.0, max_sigma_cap_k=7.0,
    )
    assert hot_scene[5, 5] == False  # 4K no rompe 10σ=5K

def test_dual_roi_bt_respects_anomaly_floor():
    """Si 5σ < 2K floor, threshold = 2K."""
    bt = np.full((5, 5), 270.0)
    bt[2, 2] = 272.5  # +2.5K
    dist_km = np.zeros((5, 5))  # todo summit
    roi_mask = np.ones((5, 5), dtype=bool)
    hot = dual_roi_bt_threshold(
        bt=bt, roi_mask=roi_mask, dist_km=dist_km, t_bg=270.0, std_bg=0.1,
        inner_km=3.0, n_sigma_summit=5.0, n_sigma_scene=10.0,
        anomaly_floor_k=2.0, max_sigma_cap_k=7.0,
    )
    # 5·0.1 = 0.5K < floor 2K, threshold efectivo summit = 2K. +2.5K pasa.
    assert hot[2, 2] == True

def test_dual_roi_bt_respects_sigma_cap():
    """Si 10σ > 7K cap, threshold = 7K."""
    bt = np.full((5, 5), 270.0)
    bt[2, 2] = 277.5  # +7.5K
    dist_km = np.full((5, 5), 5.0)  # todo scene
    roi_mask = np.ones((5, 5), dtype=bool)
    hot = dual_roi_bt_threshold(
        bt=bt, roi_mask=roi_mask, dist_km=dist_km, t_bg=270.0, std_bg=2.0,
        inner_km=3.0, n_sigma_summit=5.0, n_sigma_scene=10.0,
        anomaly_floor_k=2.0, max_sigma_cap_k=7.0,
    )
    # 10·2 = 20K, cap a 7K. +7.5K pasa.
    assert hot[2, 2] == True

def test_dual_roi_bt_excludes_outside_roi():
    """roi_mask=False → siempre False sin importar BT."""
    bt = np.full((5, 5), 290.0)  # MUY caliente
    dist_km = np.zeros((5, 5))
    roi_mask = np.zeros((5, 5), dtype=bool)  # nada en ROI
    hot = dual_roi_bt_threshold(
        bt=bt, roi_mask=roi_mask, dist_km=dist_km, t_bg=270.0, std_bg=0.5,
        inner_km=3.0, n_sigma_summit=5.0, n_sigma_scene=10.0,
        anomaly_floor_k=2.0, max_sigma_cap_k=7.0,
    )
    assert not hot.any()
```

- [ ] **Step 2: Run tests, verify they fail**

Run: `pytest tests/test_dual_roi_bt.py -v`
Expected: 4 nuevos FAIL — `dual_roi_bt_threshold` no existe.

- [ ] **Step 3: Implement helper at end of `pipeline/detection_context.py`**

```python
def dual_roi_bt_threshold(
    bt: np.ndarray,
    roi_mask: np.ndarray,
    dist_km: np.ndarray,
    t_bg: float,
    std_bg: float,
    inner_km: float,
    n_sigma_summit: float,
    n_sigma_scene: float,
    anomaly_floor_k: float,
    max_sigma_cap_k: float,
) -> np.ndarray:
    """Coppola 2016a Tabla 1: dual-ROI N·σ thresholds en eruption-path BT.

    summit (dist <= inner_km): threshold = max(floor, min(N·σ_summit · std_bg, cap))
    scene  (dist >  inner_km): threshold = max(floor, min(N·σ_scene · std_bg, cap))

    Args:
        bt: 2-D array BT (K).
        roi_mask: pixels válidos a evaluar.
        dist_km: 2-D distancia al vent (km).
        t_bg: median bg.
        std_bg: σ bg.
        inner_km: radio summit/scene split.
        n_sigma_summit, n_sigma_scene: multiplicadores σ.
        anomaly_floor_k: piso ΔBT (Coppola 2015 ANOMALY_THRESHOLD_K, default 2K).
        max_sigma_cap_k: cap σ component (S15 Tema F, default 7K).

    Returns:
        bool array hot_mask con threshold dual aplicado.
    """
    sigma_summit = min(n_sigma_summit * std_bg, max_sigma_cap_k)
    sigma_scene = min(n_sigma_scene * std_bg, max_sigma_cap_k)
    threshold_summit = max(anomaly_floor_k, sigma_summit)
    threshold_scene = max(anomaly_floor_k, sigma_scene)
    eff_summit = t_bg + threshold_summit
    eff_scene = t_bg + threshold_scene

    is_summit = dist_km <= inner_km
    delta_threshold = np.where(is_summit, eff_summit, eff_scene)
    return roi_mask & ~np.isnan(bt) & (bt > delta_threshold)
```

- [ ] **Step 4: Run tests, verify pass**

Run: `pytest tests/test_dual_roi_bt.py -v`
Expected: 4 PASS.

- [ ] **Step 5: Commit**

```bash
git add pipeline/detection_context.py tests/test_dual_roi_bt.py
git commit -m "S26 T2 — helper dual_roi_bt_threshold + 4 tests TDD"
```

---

### Task 3: Integrar en process_modis.py

**Files:**
- Modify: `pipeline/process_modis.py:73-76` (imports), `:252-291` (threshold logic)

- [ ] **Step 1: Add imports**

In imports block (around line 73-76), agregar:

```python
from .profile import (
    # ... existing ...
    ENABLE_DUAL_ROI_BT,
    N_SIGMA_MIR_SUMMIT,
    N_SIGMA_MIR_SCENE,
)
```

- [ ] **Step 2: Modify threshold logic in process_modis.py:252-291**

Replace lines around 252-291:

```python
    sigma_component = min(N_SIGMA * std_bg, MAX_SIGMA_COMPONENT_K)
    threshold = max(ANOMALY_THRESHOLD_K, sigma_component)
    # ... local_threshold logic ...
    bt_path_hot = roi_mask & ~np.isnan(bt_mir) & (bt_mir > effective_threshold)
```

with:

```python
    if ENABLE_DUAL_ROI_BT and inner_radius_km is not None and vent_lat is not None:
        # S26 Coppola 2016a Tabla 1: dual-ROI N·σ summit/scene
        from .detection_context import dual_roi_bt_threshold
        vent_dist_2d = haversine_km(vent_lat, vent_lon, lat, lon)
        bt_path_hot_dual = dual_roi_bt_threshold(
            bt=bt_mir, roi_mask=roi_mask, dist_km=vent_dist_2d,
            t_bg=t_bg, std_bg=std_bg, inner_km=inner_radius_km,
            n_sigma_summit=N_SIGMA_MIR_SUMMIT,
            n_sigma_scene=N_SIGMA_MIR_SCENE,
            anomaly_floor_k=ANOMALY_THRESHOLD_K,
            max_sigma_cap_k=MAX_SIGMA_COMPONENT_K,
        )
        # Combinar con local_threshold (preservar fix histórico p95)
        # local_threshold sigue aplicando — agrega filtro p95 ROI.
        # ... existing local_threshold logic preservada ...
        sigma_component = min(N_SIGMA * std_bg, MAX_SIGMA_COMPONENT_K)
        threshold = max(ANOMALY_THRESHOLD_K, sigma_component)
        # local_threshold para diag (sin afectar bt_path_hot dual)
        # ... existing local_threshold computation ...
        effective_threshold = t_bg + threshold  # diag value
        bt_path_hot = bt_path_hot_dual
        if not np.isnan(local_threshold):
            bt_path_hot = bt_path_hot & (bt_mir > local_threshold)
    else:
        # Comportamiento legacy uniforme N_SIGMA
        sigma_component = min(N_SIGMA * std_bg, MAX_SIGMA_COMPONENT_K)
        threshold = max(ANOMALY_THRESHOLD_K, sigma_component)
        # ... existing local_threshold + effective_threshold logic ...
        bt_path_hot = roi_mask & ~np.isnan(bt_mir) & (bt_mir > effective_threshold)
```

NOTA crítica: este es un boceto. La integración exacta requiere preservar el cómputo `local_threshold` y `effective_threshold` que se usa para `diag_eff_threshold_k` en el record. La implementación final debe:
1. Mantener cómputo de `effective_threshold` legacy para diag.
2. Cuando `ENABLE_DUAL_ROI_BT=True`, sustituir `bt_path_hot` por la versión dual.
3. Cuando OFF, comportamiento idéntico al actual.

- [ ] **Step 3: Run smoke test**

```bash
VRP_PROFILE=_dual_roi_bt_enabled python -c "
from pipeline import profile
print('flag:', profile.ENABLE_DUAL_ROI_BT)
print('summit:', profile.N_SIGMA_MIR_SUMMIT, 'scene:', profile.N_SIGMA_MIR_SCENE)
"
```
Expected: `flag: True`, `summit: 5.0`, `scene: 10.0`.

- [ ] **Step 4: Run full test suite**

Run: `pytest 2>&1 | tail -3`
Expected: todos los tests pasen, 175+ passed.

- [ ] **Step 5: Commit**

```bash
git add pipeline/process_modis.py
git commit -m "S26 T3 — process_modis.py dual-ROI BT detrás de flag"
```

---

### Task 4: Integrar en process_viirs.py

**Files:**
- Modify: `pipeline/process_viirs.py` imports + threshold logic ~líneas 365-372

- [ ] **Step 1: Add imports**

Agregar a la lista de imports de `pipeline.profile`:

```python
    ENABLE_DUAL_ROI_BT,
    N_SIGMA_MIR_SUMMIT,
    N_SIGMA_MIR_SCENE,
```

- [ ] **Step 2: Replace threshold logic around line 367-372**

```python
    if ENABLE_DUAL_ROI_BT and inner_radius_km is not None and vent_lat is not None:
        # S26 dual-ROI BT (Coppola 2016a Tabla 1)
        from .detection_context import dual_roi_bt_threshold
        bt_path_hot = dual_roi_bt_threshold(
            bt=bt, roi_mask=roi_mask, dist_km=vent_dist_per_pixel,
            t_bg=t_bg_i04, std_bg=std_bg, inner_km=inner_radius_km,
            n_sigma_summit=N_SIGMA_MIR_SUMMIT,
            n_sigma_scene=N_SIGMA_MIR_SCENE,
            anomaly_floor_k=ANOMALY_THRESHOLD_K,
            max_sigma_cap_k=MAX_SIGMA_COMPONENT_K,
        )
        sigma_component = min(N_SIGMA_MIR * std_bg, MAX_SIGMA_COMPONENT_K)
        threshold_mir = max(ANOMALY_THRESHOLD_K, sigma_component)
        effective_threshold_diag = t_bg_i04 + threshold_mir  # for diag only
    else:
        sigma_component = min(N_SIGMA_MIR * std_bg, MAX_SIGMA_COMPONENT_K)
        threshold_mir = max(ANOMALY_THRESHOLD_K, sigma_component)
        effective_threshold_diag = t_bg_i04 + threshold_mir
        bt_path_hot = roi_mask & ~np.isnan(bt) & (bt > effective_threshold_diag)
```

- [ ] **Step 3: Run full test suite**

Run: `pytest 2>&1 | tail -3`
Expected: 175+ passed.

- [ ] **Step 4: Commit**

```bash
git add pipeline/process_viirs.py
git commit -m "S26 T4 — process_viirs.py dual-ROI BT detrás de flag"
```

---

### Task 5: Integrar en process_viirs_mod.py

**Files:**
- Modify: `pipeline/process_viirs_mod.py` imports + threshold logic

- [ ] **Step 1-3**: mismo patrón que Task 4 sobre process_viirs_mod.py.

- [ ] **Step 4: Commit**

```bash
git add pipeline/process_viirs_mod.py
git commit -m "S26 T5 — process_viirs_mod.py dual-ROI BT detrás de flag"
```

---

### Task 6: Profile registrar + workflow A/B

**Files:**
- Modify: `pipeline/profile.py:VALID_PROFILES` ya hace discovery dinámico — no necesita cambios.
- Create: `.github/workflows/reproc-ab-dual-roi-bt.yml`

- [ ] **Step 1: Create workflow A/B**

Clon de `.github/workflows/reproc-ab-test1.yml` con cambios:
- name: `A/B reproceso dual-ROI BT (S26)`
- Matrix volcano: `[Lascar, Lastarria, Tupungatito, Chaiten]`
- Matrix profile: `[_dual_roi_bt_enabled, _dual_roi_bt_disabled]`
- Ventana default: `2026-04-12` to `2026-04-25`.
- commit message: `"S26 A/B dual-ROI BT — ${profile} / ${volcano} 14d"`.

- [ ] **Step 2: Commit + push + dispatch**

```bash
git add .github/workflows/reproc-ab-dual-roi-bt.yml
git commit -m "S26 T6 — workflow A/B dual-ROI BT"
git push origin s15-dev
git checkout main && git merge s15-dev --no-edit && git push origin main && git checkout s15-dev
gh workflow run reproc-ab-dual-roi-bt.yml -R MendozaVolcanic/VRP-chile --ref main \
  -f start=2026-04-12 -f end=2026-04-25
```

- [ ] **Step 3: Monitor**

```bash
gh run list -R MendozaVolcanic/VRP-chile --workflow=reproc-ab-dual-roi-bt.yml -L 1
```
Esperar 8 jobs success (4 vol × 2 profiles). Tiempo estimado: 30-45 min.

---

### Task 7: Forense + delta report A/B

**Files:**
- Create: `experiments/55_dual_roi_bt_ab/delta_report.py`

- [ ] **Step 1: Create delta_report.py** — clon de `experiments/51_p31_ab/delta_report.py` con cambios:

```python
PROFILES = ["_dual_roi_bt_enabled", "_dual_roi_bt_disabled"]
VOLCANOES = ["Lascar", "Lastarria", "Tupungatito", "Chaiten"]
```

Reutiliza la lógica TP/FN/FP_far + criterio de aceptación. Adiciona:
- Comparación `recall_summit en/dis`.
- Comparación `n_records_far` y `n_far_high_vrp` (vrp>1MW).
- Comparación `vrp_ratio_median` vs MIROVA NRT.

- [ ] **Step 2: Pull data + run**

```bash
git pull origin main
python experiments/55_dual_roi_bt_ab/delta_report.py
```

- [ ] **Step 3: Verificar criterios de aceptación**

Imprimir explícitamente:
- ✓/✗ Recall agregado cae < 5pp.
- ✓/✗ FPs lejanos (vrp>1MW) caen ≥40%.
- ✓/✗ Ratio mediano global ≤30×.

- [ ] **Step 4: Commit**

```bash
git add experiments/55_dual_roi_bt_ab/
git commit -m "S26 T7 — A/B dual-ROI BT delta report"
```

---

### Task 8: Decisión integrar a `mirova_equivalent`

- [ ] **Step 1: Si los 3 criterios PASS**

Editar `pipeline/profiles/mirova_equivalent.yaml`:

```yaml
thresholds:
  # ... existing ...
  n_sigma_mir_summit: 5.0
  n_sigma_mir_scene: 10.0
paths:
  # ... existing ...
  enable_dual_roi_bt: true
```

Borrar profiles A/B `_dual_roi_bt_enabled.yaml` y `_dual_roi_bt_disabled.yaml`.

Re-dispatch reproceso histórico Tier A con `mirova_equivalent` actualizado.

Persistir hallazgo en `~memory/project_s26_dual_roi_bt_validated.md`.

- [ ] **Step 2: Si NO PASS** (recall cae > 5pp o FPs no bajan suficiente)

NO mergear. Borrar profiles A/B. Persistir hallazgo negativo en memoria con análisis de qué falló.

Reabrir hipótesis: ¿el cap MAX_SIGMA_COMPONENT_K=7K está anulando el efecto dual-ROI? (S19 D2 conclusión).

- [ ] **Step 3: Commit final**

```bash
git add pipeline/ ~memory/
git commit -m "S26 cierre dual-ROI BT — INTEGRADO/NO-INTEGRADO según resultado A/B"
git push origin s15-dev
```

---

## Self-Review checklist (post-plan)

✓ Cada Task tiene criterio de aceptación medible (no "implementar X").
✓ Tests TDD antes que código (Task 2).
✓ A/B aislado antes de integrar (Tasks 6-7-8).
✓ Plan tiene exit criteria CLAROS (3 métricas en Task 7).
✓ Si cualquier task falla, hay rollback path documentado (Task 8 Step 2).

## Antipatrón a evitar

NO descubrir un nuevo problema durante implementación → fixearlo aquí. Si pasa: anotar en backlog, terminar este plan, evaluar después.

## Pendientes que NO entran en este plan (backlog explícito)

- B) Filtro dashboard summit default ON.
- C) Exclude_zones complementarias Villarrica/Planchón/NdC.
- D) Path TIR-only Villarrica.
- Refactor race condition workflow.
- Local p95 threshold ausente VIIRS 375m (D7).
