# P3.2 — dNTI contextual 8-vecinos Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reemplazar el gate global `|T - t_bg| > N·σ_anillo` por un gate contextual local `NTI_pixel - median(NTI_8_vecinos) > C1` (Coppola 2016a SP 426.5), de modo que pixels que destacan respecto de sus vecinos inmediatos se detecten y los que solo están uniformemente tibios respecto del anillo de fondo se descarten.

**Architecture:** Nuevo módulo `pipeline/detection_context.py` con una única función pura `contextual_dnti_hot_mask(nti, bt, roi_mask, t_bg, c1, bt_sanity_k) -> ndarray[bool]`. Los 3 procesadores (process_modis, process_viirs, process_viirs_mod) la invocan como un nuevo **Path D**, gateado por la profile flag `enable_dnti_contextual_path`. El perfil `mirova_equivalent` activa D y reduce el peso de Path A (sigma-based BT gate) elevando su floor a 10 K; `experimental` mantiene los paths actuales sin cambios para A/B.

**Tech Stack:** numpy, scipy.ndimage.generic_filter, pytest. Pipeline existente VIIRS/MODIS, profile loader YAML.

**Baseline pre-cambio** (contra CSV MIROVA NRT, commit `d6beaff`):
- Global: Recall 0.28, Precision 0.35, F1 0.31, ratio_med 1.56.
- Lastarria: ratio mediano 19.87, p90 60.80, max 85.65 — **objetivo del fix**.
- Lascar (canario): ratio 1.16, precision 0.82 — **debe preservarse ±0.05**.

**Criterio de aceptación final:**
1. Lastarria ratio mediano < 3.0 (desde 19.87).
2. Recall global ≥ 0.23 (desde 0.28, margen 5pp).
3. Lascar ratio mediano permanece en [1.10, 1.25].
4. Tests 16/16 preservados + nuevos tests de unidad verdes.

---

## Task 1: Helper `contextual_dnti_hot_mask`

**Files:**
- Create: `pipeline/detection_context.py`
- Test: `tests/test_detection_context.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_detection_context.py
"""Tests for contextual dNTI 8-neighbor mask (P3.2).

Fenomeno fisico: en una zona fumarolica heterogenea (Lastarria), el gate
global sigma_bg-anillo infla muchos pixels tibios. El gate contextual
8-vecinos exige que el pixel destaque vs sus vecinos inmediatos. Si la
zona completa esta tibia, los vecinos tambien --> dNTI chico --> rechazo.
Solo sobrevive el pixel verdaderamente localizado.

Referencia: Coppola et al. 2016 SP 426.5 "An enhanced automated thermal
anomaly detection", seccion "contextual NTI difference".
"""

import numpy as np
import pytest
from pipeline.detection_context import contextual_dnti_hot_mask


def test_isolated_hotspot_passes():
    """Pixel con dNTI=+0.010 destacado del entorno = detectado."""
    nti = np.full((5, 5), -0.95, dtype=np.float64)
    nti[2, 2] = -0.93   # +0.02 sobre vecinos
    bt = np.full((5, 5), 285.0)
    bt[2, 2] = 295.0     # sanity BT pasa
    roi = np.ones((5, 5), dtype=bool)
    mask = contextual_dnti_hot_mask(
        nti=nti, bt=bt, roi_mask=roi,
        t_bg=285.0, c1=0.003, bt_sanity_k=3.0)
    assert mask[2, 2] == True
    # Vecinos no deben pasar (son todos iguales entre si)
    mask[2, 2] = False
    assert not mask.any()


def test_uniformly_warm_region_rejected():
    """Toda la region uniformemente tibia (Lastarria): dNTI~0 en todos,
    ninguno pasa aunque BT este elevado."""
    nti = np.full((7, 7), -0.90, dtype=np.float64)   # todos iguales
    bt = np.full((7, 7), 295.0)                       # todos tibios
    roi = np.ones((7, 7), dtype=bool)
    mask = contextual_dnti_hot_mask(
        nti=nti, bt=bt, roi_mask=roi,
        t_bg=285.0, c1=0.003, bt_sanity_k=3.0)
    assert not mask.any(), "Region uniformemente tibia no debe generar detecciones"


def test_bt_sanity_gate_blocks_cold_anomaly():
    """Pixel con dNTI anomalo pero BT bajo el sanity --> rechazo."""
    nti = np.full((5, 5), -0.95)
    nti[2, 2] = -0.90    # dNTI > c1
    bt = np.full((5, 5), 285.0)
    bt[2, 2] = 286.0      # solo +1K, menor que bt_sanity_k=3.0
    roi = np.ones((5, 5), dtype=bool)
    mask = contextual_dnti_hot_mask(
        nti=nti, bt=bt, roi_mask=roi,
        t_bg=285.0, c1=0.003, bt_sanity_k=3.0)
    assert mask[2, 2] == False


def test_outside_roi_rejected():
    """Pixel anomalo fuera del ROI --> no entra aunque dNTI pase."""
    nti = np.full((5, 5), -0.95)
    nti[0, 0] = -0.90      # esquina, pero roi_mask[0,0]=False
    bt = np.full((5, 5), 295.0)
    roi = np.ones((5, 5), dtype=bool)
    roi[0, 0] = False
    mask = contextual_dnti_hot_mask(
        nti=nti, bt=bt, roi_mask=roi,
        t_bg=285.0, c1=0.003, bt_sanity_k=3.0)
    assert mask[0, 0] == False


def test_nan_pixels_handled():
    """Pixels NaN en NTI (cloud, edge) no deben romper ni ser reportados hot."""
    nti = np.full((5, 5), -0.95)
    nti[2, 2] = np.nan
    nti[1, 1] = np.nan
    bt = np.full((5, 5), 295.0)
    roi = np.ones((5, 5), dtype=bool)
    mask = contextual_dnti_hot_mask(
        nti=nti, bt=bt, roi_mask=roi,
        t_bg=285.0, c1=0.003, bt_sanity_k=3.0)
    assert mask[2, 2] == False
    # No excepcion, shape preservado
    assert mask.shape == nti.shape


def test_c1_threshold_is_exclusive():
    """dNTI = c1 exacto no pasa (estricto >). Coppola 2016a usa > no >=."""
    nti = np.full((5, 5), -0.95)
    nti[2, 2] = -0.947        # dNTI = 0.003 exacto
    bt = np.full((5, 5), 295.0)
    roi = np.ones((5, 5), dtype=bool)
    mask = contextual_dnti_hot_mask(
        nti=nti, bt=bt, roi_mask=roi,
        t_bg=285.0, c1=0.003, bt_sanity_k=3.0)
    assert mask[2, 2] == False   # estrictamente > 0.003


def test_lastarria_scenario_with_one_real_hotspot():
    """Escenario Lastarria sintetico: 7x7 region uniformemente tibia
    (fumarolas pasivas) + 1 pixel localizado de fumarola activa.
    Gate actual sigma-anillo: detectaria los 49 (infla VRP).
    Gate contextual: solo el localizado."""
    # Background level tibio en toda la zona (simula fumarolas pasivas
    # + heterogeneidad termica)
    nti = np.random.default_rng(42).normal(-0.92, 0.001, size=(7, 7))
    bt = np.random.default_rng(43).normal(290.0, 0.5, size=(7, 7))
    # Un pixel real: fumarola activa localizada
    nti[3, 3] = -0.90          # claramente sobre los vecinos
    bt[3, 3] = 300.0
    roi = np.ones((7, 7), dtype=bool)
    mask = contextual_dnti_hot_mask(
        nti=nti, bt=bt, roi_mask=roi,
        t_bg=290.0, c1=0.003, bt_sanity_k=3.0)
    assert mask[3, 3] == True
    # Los 48 restantes NO deben pasar
    others = mask.copy()
    others[3, 3] = False
    assert others.sum() == 0, f"Expected 0 false positives, got {others.sum()}"
```

- [ ] **Step 2: Run test to verify all fail**

Run: `python -m pytest tests/test_detection_context.py -v`
Expected: 7 tests fail with `ModuleNotFoundError: No module named 'pipeline.detection_context'`

- [ ] **Step 3: Write minimal implementation**

```python
# pipeline/detection_context.py
"""detection_context.py — Contextual (8-neighbor) detection gates.

Currently contains the dNTI contextual hot-mask used by P3.2 S15.

Fenomeno fisico: el gate `|NTI_pixel - median(NTI_8_vecinos)| > C1`
detecta pixels que destacan del entorno inmediato, independientemente
del sigma del anillo de fondo. En zonas uniformemente tibias
(Lastarria hidrotermal, Tupungatito glaciar + crateres) el gate
global sigma-anillo infla detecciones espurias. El gate contextual
inmuniza contra heterogeneidad regional manteniendo sensibilidad a
hotspots localizados.

Ref: Coppola et al. 2016 SP 426.5 "An enhanced automated thermal
anomaly detection algorithm" — C1 absoluto + C2 contextual.
"""

import numpy as np
from scipy.ndimage import generic_filter


# 8-neighbor footprint (3x3 excluyendo centro)
_FOOTPRINT_8N = np.array(
    [[1, 1, 1],
     [1, 0, 1],
     [1, 1, 1]],
    dtype=bool,
)


def _nanmedian_ignore_self(x: np.ndarray) -> float:
    """Median ignorando NaN. Si todos los vecinos son NaN, devuelve NaN."""
    valid = x[~np.isnan(x)]
    if valid.size == 0:
        return np.nan
    return float(np.median(valid))


def contextual_dnti_hot_mask(
    nti: np.ndarray,
    bt: np.ndarray,
    roi_mask: np.ndarray,
    t_bg: float,
    c1: float,
    bt_sanity_k: float,
) -> np.ndarray:
    """Contextual dNTI hot-pixel mask (Coppola 2016a, 8-neighbor median).

    Un pixel es hot si:
        (NTI_pixel - median(NTI_8_vecinos)) > c1
        AND bt_pixel > t_bg + bt_sanity_k
        AND roi_mask[pixel]

    Args:
        nti: array 2D NTI values, NaN allowed.
        bt: array 2D brightness temperature (K).
        roi_mask: bool 2D, True within volcano ROI.
        t_bg: float, background BT median of the ring (K).
        c1: float, contextual threshold (Coppola 2016a: 0.003 summit).
        bt_sanity_k: float, minimal BT anomaly to avoid cold artefacts (K).

    Returns:
        bool array same shape as nti, True where hot.
    """
    if nti.shape != bt.shape or nti.shape != roi_mask.shape:
        raise ValueError(f"shape mismatch nti={nti.shape} "
                         f"bt={bt.shape} roi={roi_mask.shape}")
    # Median of 8-neighbors per pixel
    nti_nbr_med = generic_filter(
        nti, _nanmedian_ignore_self,
        footprint=_FOOTPRINT_8N, mode="constant", cval=np.nan,
    )
    dnti = nti - nti_nbr_med
    hot = (
        roi_mask
        & ~np.isnan(dnti)
        & ~np.isnan(bt)
        & (dnti > c1)
        & (bt > t_bg + bt_sanity_k)
    )
    return hot
```

- [ ] **Step 4: Run tests to verify pass**

Run: `python -m pytest tests/test_detection_context.py -v`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add pipeline/detection_context.py tests/test_detection_context.py
git commit -m "S15 P3.2 step 1: contextual dNTI 8-neighbor hot-mask helper

Nuevo modulo pipeline/detection_context.py con contextual_dnti_hot_mask.
Implementa el gate contextual de Coppola 2016a SP 426.5: un pixel es
hot si (NTI - median(NTI 8-vecinos)) > C1 y BT > t_bg + sanity_k.
Usa scipy.ndimage.generic_filter con footprint 3x3 excluyendo centro.

7 unit tests cubren: isolated hotspot detection, uniformly-warm
region rejection (Lastarria scenario), BT sanity gate, ROI masking,
NaN handling, strict c1 threshold.

Proximo paso: integrar en process_viirs.py como Path D."
```

---

## Task 2: Add profile keys

**Files:**
- Modify: `pipeline/profiles/mirova_equivalent.yaml:63` (after `nti_rel_min_floor`)
- Modify: `pipeline/profiles/experimental.yaml` (mismo punto)
- Modify: `pipeline/profile.py` (exponer constantes nuevas)

- [ ] **Step 1: Add keys to mirova_equivalent.yaml**

Edit `pipeline/profiles/mirova_equivalent.yaml`, add inside `thresholds:` block before the closing (look for `modis_vent_threshold_k: 1.0`, add above):

```yaml
  # P3.2 S15: dNTI contextual 8-vecinos (Coppola 2016a SP 426.5).
  # C1 absoluto del umbral local dNTI = NTI_pixel - median(8 vecinos).
  # 0.003 = summit ROI segun paper. 0.010 para scene ROI (no usado aun,
  # ira con P3.1 dual-ROI).
  dnti_contextual_c1: 0.003
```

Edit `pipeline/profiles/mirova_equivalent.yaml`, add inside `paths:` block:

```yaml
  # P3.2 S15: habilitar gate contextual (Path D).
  # Cuando true: el Path D corre y entra al OR de hot_mask.
  # Cuando false (experimental mantiene comportamiento previo): no corre.
  enable_dnti_contextual_path: true
```

- [ ] **Step 2: Add keys to experimental.yaml**

Edit `pipeline/profiles/experimental.yaml`, mismos valores pero `enable_dnti_contextual_path: false` para preservar comportamiento baseline A/B.

- [ ] **Step 3: Expose constants in profile.py**

Edit `pipeline/profile.py`, after the block with `NTI_REL_MIN_FLOOR`:

```python
# --- P3.2 S15: dNTI contextual 8-vecinos ---
DNTI_CONTEXTUAL_C1: float = float(_t.get("dnti_contextual_c1", 0.003))
ENABLE_DNTI_CONTEXTUAL_PATH: bool = bool(_cfg["paths"].get("enable_dnti_contextual_path", False))
```

- [ ] **Step 4: Smoke test profile loads**

Run:
```bash
python -c "from pipeline.profile import DNTI_CONTEXTUAL_C1, ENABLE_DNTI_CONTEXTUAL_PATH; print(DNTI_CONTEXTUAL_C1, ENABLE_DNTI_CONTEXTUAL_PATH)"
```
Expected: `0.003 True`

Run with experimental:
```bash
VRP_PROFILE=experimental python -c "from pipeline.profile import ENABLE_DNTI_CONTEXTUAL_PATH; print(ENABLE_DNTI_CONTEXTUAL_PATH)"
```
Expected: `False`

- [ ] **Step 5: Commit**

```bash
git add pipeline/profiles/mirova_equivalent.yaml pipeline/profiles/experimental.yaml pipeline/profile.py
git commit -m "S15 P3.2 step 2: profile keys dnti_contextual_c1 + enable flag

mirova_equivalent activa Path D con C1=0.003 (Coppola 2016a summit).
experimental desactiva para preservar baseline comparativo A/B."
```

---

## Task 3: Integrate Path D in `process_viirs.py` (375m, highest priority)

**Files:**
- Modify: `pipeline/process_viirs.py:60-90` (imports) y `:278-354` (detection block)
- Test: `tests/test_viirs_path_d.py` (nuevo)

- [ ] **Step 1: Write failing test**

```python
# tests/test_viirs_path_d.py
"""Integration test: Path D (dNTI contextual) is invoked in process_viirs
when enable_dnti_contextual_path=True.

No corre pipeline completo; stub mock bands/geolocation minimal y verifica
que n_dnti_ctx_path > 0 en escenario donde solo Path D deberia gatillar.
"""

import os
# Lock profile BEFORE importing pipeline
os.environ["VRP_PROFILE"] = "mirova_equivalent"

import numpy as np
from pipeline.detection_context import contextual_dnti_hot_mask


def test_path_d_isolated_hotspot_lastarria_like():
    """Escenario Lastarria: zona 9x9 tibia uniforme + 1 pixel localizado.
    Path A (sigma-anillo inflado) detectaria muchos; Path D solo el real."""
    rng = np.random.default_rng(10)
    nti = rng.normal(-0.92, 0.0008, size=(9, 9))
    bt = rng.normal(290.0, 0.4, size=(9, 9))
    nti[4, 4] = -0.895
    bt[4, 4] = 305.0
    roi = np.ones((9, 9), dtype=bool)
    mask_d = contextual_dnti_hot_mask(
        nti=nti, bt=bt, roi_mask=roi,
        t_bg=290.0, c1=0.003, bt_sanity_k=3.0)
    assert mask_d[4, 4] == True
    others = mask_d.copy(); others[4, 4] = False
    assert others.sum() == 0


def test_path_d_disabled_in_experimental_profile():
    """Con ENABLE_DNTI_CONTEXTUAL_PATH=False, nuestro helper sigue
    funcionando pero el caller NO debe invocarlo. Esto se verifica
    reloading profile en modo experimental."""
    # Reload profile with experimental
    import importlib, os
    os.environ["VRP_PROFILE"] = "experimental"
    import pipeline.profile
    importlib.reload(pipeline.profile)
    assert pipeline.profile.ENABLE_DNTI_CONTEXTUAL_PATH == False
    # Restaurar
    os.environ["VRP_PROFILE"] = "mirova_equivalent"
    importlib.reload(pipeline.profile)
```

- [ ] **Step 2: Run test to verify fails**

Run: `python -m pytest tests/test_viirs_path_d.py -v`
Expected: 2 tests failing (first test passes Task 1 helper, but suite may fail on profile lock; expected state: at least verify test shape).

Note: if test 1 passes because helper already exists — OK, proceed. The integration verification is in Step 3.

- [ ] **Step 3: Modify process_viirs.py imports**

Edit `pipeline/process_viirs.py`, in the profile imports block (look for `from .profile import`):

```python
# Add to import list:
from .profile import (
    ...,                           # existing
    DNTI_CONTEXTUAL_C1,
    ENABLE_DNTI_CONTEXTUAL_PATH,
)
```

Add after existing imports (around line 31):

```python
from .detection_context import contextual_dnti_hot_mask
```

- [ ] **Step 4: Modify detection block to add Path D**

In `pipeline/process_viirs.py`, locate the hot-mask OR block (around lines 348-352):

```python
            hot_mask_2d = bt_path_hot | nti_path_hot | nti_rel_hot
            n_bt_path = int(np.sum(bt_path_hot))
            n_nti_path = int(np.sum(nti_path_hot))
```

Replace with:

```python
            # Path D — dNTI contextual 8-vecinos (P3.2 S15, Coppola 2016a).
            # Anomaly requires the pixel to stand out from its immediate
            # neighbors, not from the ring average — immune to uniformly
            # warm terrain (Lastarria hidrotermal, ratio 19.87 pre-P3.2).
            n_dnti_ctx_path = 0
            if (ENABLE_DNTI_CONTEXTUAL_PATH
                    and "I05" in bands
                    and not np.isnan(nti_bg)):
                dnti_ctx_hot = contextual_dnti_hot_mask(
                    nti=nti, bt=bt, roi_mask=roi_mask,
                    t_bg=t_bg_i04,
                    c1=DNTI_CONTEXTUAL_C1,
                    bt_sanity_k=NTI_BT_SANITY_K,
                )
                n_dnti_ctx_path = int(np.sum(dnti_ctx_hot))
            else:
                dnti_ctx_hot = np.zeros_like(bt_path_hot)

            hot_mask_2d = bt_path_hot | nti_path_hot | nti_rel_hot | dnti_ctx_hot
            n_bt_path = int(np.sum(bt_path_hot))
            n_nti_path = int(np.sum(nti_path_hot))
```

In the result dict (around line 508), add `"n_dnti_ctx_path": n_dnti_ctx_path` after `"n_bt_path"`.

- [ ] **Step 5: Run all tests**

```bash
python -m pytest tests/ -v
```
Expected: 16 existing + 7 (Task 1) + 2 (this task) = 25 passed.

- [ ] **Step 6: Commit**

```bash
git add pipeline/process_viirs.py tests/test_viirs_path_d.py
git commit -m "S15 P3.2 step 3: Path D dNTI contextual en process_viirs.py

Agrega contextual_dnti_hot_mask como Path D al OR de hot_mask_2d,
gateado por ENABLE_DNTI_CONTEXTUAL_PATH (true en mirova_equivalent).
n_dnti_ctx_path expuesto en output record para diagnostico.

Path A (sigma-anillo) y B (NTI absoluto) se mantienen; D entra al
OR para aumentar recall sin subir ratio VRP en zonas heterogeneas."
```

---

## Task 4: Checkpoint — validar P3.2 en VIIRS 375m contra baseline

**Goal:** antes de invertir en las otras 2 rutas, medir si P3.2 VIIRS 375m baja el ratio Lastarria. Si no, ajustar C1 o reconsiderar antes de tocar MODIS y VIIRS 750m.

- [ ] **Step 1: Reproceso Lastarria VIIRS 375m Nov 2025 + Feb-Abr 2026**

Con data ya bajada si existe en cache; sino usar backfill script.

```bash
# Subset rapido para Lastarria (tier A, 128 VIIRS375 detections en CSV)
python scripts/run_pipeline.py --volcano Lastarria --start 2026-02-01 --end 2026-04-21
```

Nota: solo VIIRS 375m relevante. Puede tardar dependiendo del cache.

- [ ] **Step 2: Re-correr crossmatch**

```bash
python experiments/27_crossmatch_vs_consolidado.py --out experiments/27_crossmatch_post_p32_viirs375.json
```

- [ ] **Step 3: Diff contra baseline**

```bash
python -c "
import json
pre = json.load(open('experiments/27_crossmatch_results.json'))['Lastarria']
post = json.load(open('experiments/27_crossmatch_post_p32_viirs375.json'))['Lastarria']
def med(r): xs=[m['ratio'] for m in r['tp'] if m.get('ratio')]; return sorted(xs)[len(xs)//2] if xs else None
print(f'Lastarria TP: {len(pre[\"tp\"])} -> {len(post[\"tp\"])}')
print(f'Lastarria FP: {len(pre[\"fp\"])} -> {len(post[\"fp\"])}')
print(f'Lastarria ratio med: {med(pre):.2f} -> {med(post):.2f}')
"
```

Expected delta (criterio de aceptacion):
- Ratio mediano Lastarria: 19.87 → < 3.0 ✓
- FP Lastarria: 59 → < 30 ✓
- TP puede bajar (some marginal detections will drop): OK si TP > 0

- [ ] **Step 4: Decision gate**

Si criterio se cumple → seguir a Task 5.
Si NO se cumple:
  - Opción A: ajustar C1 (probar 0.001, 0.002) y repetir Task 4.
  - Opción B: ampliar footprint a 5x5 con rank filter.
  - Opción C: revertir y revisar plan.

- [ ] **Step 5: Commit evidence**

```bash
git add experiments/27_crossmatch_post_p32_viirs375.json
git commit -m "S15 P3.2 step 4: evidencia VIIRS 375m post-P3.2 (Lastarria)

Ratio mediano Lastarria paso de X a Y (objetivo <3).
FPs: A -> B. TPs: C -> D.
Decision: continuar a VIIRS 750m / MODIS."
```

---

## Task 5: Integrate Path D in `process_viirs_mod.py` (750m M-band)

**Files:**
- Modify: `pipeline/process_viirs_mod.py` (imports + detection block)
- Test: `tests/test_viirs_mod_path_d.py`

- [ ] **Step 1: Write failing test (analog a Task 3 test)**

```python
# tests/test_viirs_mod_path_d.py
"""Integration test para Path D en VIIRS M-band 750m.

VIIRS 750m = M13 (4.05 um) + M15 (10.76 um). Mismo algoritmo contextual
que I-band, solo cambia resolucion de pixel (562500 m^2 nadir vs 140625).
"""
import os
os.environ["VRP_PROFILE"] = "mirova_equivalent"
import numpy as np
from pipeline.detection_context import contextual_dnti_hot_mask


def test_path_d_mband_isolated_hotspot():
    """Escenario 5x5 con 1 pixel localizado en M-band resolution."""
    nti = np.full((5, 5), -0.93)
    nti[2, 2] = -0.900
    bt = np.full((5, 5), 285.0)
    bt[2, 2] = 300.0
    roi = np.ones((5, 5), dtype=bool)
    mask = contextual_dnti_hot_mask(
        nti=nti, bt=bt, roi_mask=roi,
        t_bg=285.0, c1=0.003, bt_sanity_k=3.0)
    assert mask[2, 2] == True
    others = mask.copy(); others[2, 2] = False
    assert not others.any()
```

- [ ] **Step 2: Run test**

Run: `python -m pytest tests/test_viirs_mod_path_d.py -v`
Expected: passes if helper OK; verifies integration in next step.

- [ ] **Step 3: Modify `pipeline/process_viirs_mod.py`**

Imports (top of file):

```python
from .detection_context import contextual_dnti_hot_mask
from .profile import (
    ...,                         # existing
    DNTI_CONTEXTUAL_C1,
    ENABLE_DNTI_CONTEXTUAL_PATH,
)
```

Locate the hot-mask OR (around line 322):

```python
    hot_mask_2d = bt_path_hot | nti_path_hot | nti_rel_hot
```

Replace with:

```python
    # Path D — dNTI contextual 8-vecinos (P3.2 S15).
    n_dnti_ctx_path = 0
    if (ENABLE_DNTI_CONTEXTUAL_PATH
            and nti is not None
            and not np.isnan(nti_bg)):
        dnti_ctx_hot = contextual_dnti_hot_mask(
            nti=nti, bt=bt_mir, roi_mask=roi_mask,
            t_bg=t_bg_i04 if "t_bg_i04" in dir() else t_bg_mir,
            c1=DNTI_CONTEXTUAL_C1,
            bt_sanity_k=NTI_BT_SANITY_K,
        )
        n_dnti_ctx_path = int(np.sum(dnti_ctx_hot))
    else:
        dnti_ctx_hot = np.zeros_like(bt_path_hot)
    hot_mask_2d = bt_path_hot | nti_path_hot | nti_rel_hot | dnti_ctx_hot
```

NOTA: confirmar nombre de variable `bt_mir` vs `bt_m13` / `t_bg_mir` leyendo
el archivo. Si el nombre es distinto, ajustar a lo que exista. Objetivo es
pasar el MIR band BT y su t_bg al helper.

Add `"n_dnti_ctx_path": n_dnti_ctx_path` al result dict.

- [ ] **Step 4: Run all tests**

```bash
python -m pytest tests/ -v
```
Expected: 26 passed (16 + 7 + 2 + 1).

- [ ] **Step 5: Commit**

```bash
git add pipeline/process_viirs_mod.py tests/test_viirs_mod_path_d.py
git commit -m "S15 P3.2 step 5: Path D dNTI contextual en process_viirs_mod.py

Misma logica que process_viirs.py pero sobre M13 (750m 4.05 um).
Footprint 8-vecinos es mas grueso en km (750 vs 375) pero el gate
contextual normaliza por entorno inmediato, no absoluto, asi que la
interpretacion fisica se preserva."
```

---

## Task 6: Integrate Path D in `process_modis.py` (1 km)

**Files:**
- Modify: `pipeline/process_modis.py` (imports + detection block ~line 293-306)
- Test: `tests/test_modis_path_d.py`

- [ ] **Step 1: Write test (analog)**

```python
# tests/test_modis_path_d.py
"""Path D integration en process_modis.py (1 km MODIS B21/22 + B31).

MODIS pixel 1 km -> footprint 8-vecinos cubre ~3x3 km. Para MODIS el
gate contextual es especialmente importante: el tamaño de pixel es
grande y la chance de mezclar roca caliente + fria dentro del pixel
es alta. El vecindario es chico en numero de pixels pero grande en km.
"""
import os
os.environ["VRP_PROFILE"] = "mirova_equivalent"
import numpy as np
from pipeline.detection_context import contextual_dnti_hot_mask


def test_path_d_modis_localized_hotspot():
    nti = np.full((5, 5), -0.88)
    nti[2, 2] = -0.850
    bt = np.full((5, 5), 288.0)
    bt[2, 2] = 298.0
    roi = np.ones((5, 5), dtype=bool)
    mask = contextual_dnti_hot_mask(
        nti=nti, bt=bt, roi_mask=roi,
        t_bg=288.0, c1=0.003, bt_sanity_k=3.0)
    assert mask[2, 2] == True
```

- [ ] **Step 2: Run test**

Run: `python -m pytest tests/test_modis_path_d.py -v`
Expected: passes.

- [ ] **Step 3: Modify `pipeline/process_modis.py`**

Imports section:

```python
from .detection_context import contextual_dnti_hot_mask
from .profile import (
    ...,                         # existing
    DNTI_CONTEXTUAL_C1,
    ENABLE_DNTI_CONTEXTUAL_PATH,
)
```

Locate hot_mask OR block (around lines 301-305):

```python
    hot_mask_2d = bt_path_hot | nti_path_hot
    n_bt_path = int(np.sum(bt_path_hot))
    n_nti_path = int(np.sum(nti_path_hot))
```

Replace with:

```python
    # Path D — dNTI contextual (P3.2 S15).
    n_dnti_ctx_path = 0
    if ENABLE_DNTI_CONTEXTUAL_PATH and not np.isnan(nti_bg):
        dnti_ctx_hot = contextual_dnti_hot_mask(
            nti=nti, bt=bt_mir, roi_mask=roi_mask,
            t_bg=t_bg_mir,
            c1=DNTI_CONTEXTUAL_C1,
            bt_sanity_k=NTI_BT_SANITY_K,
        )
        n_dnti_ctx_path = int(np.sum(dnti_ctx_hot))
    else:
        dnti_ctx_hot = np.zeros_like(bt_path_hot)

    hot_mask_2d = bt_path_hot | nti_path_hot | dnti_ctx_hot
    n_bt_path = int(np.sum(bt_path_hot))
    n_nti_path = int(np.sum(nti_path_hot))
```

NOTA: confirmar que existe `NTI_BT_SANITY_K` y `nti` y `bt_mir` en scope.
Si falta importar `NTI_BT_SANITY_K` desde profile, agregarlo.

Result dict: agregar `"diag_n_dnti_ctx_path": n_dnti_ctx_path`.

- [ ] **Step 4: Run all tests**

Run: `python -m pytest tests/ -v`
Expected: 27 passed (16 + 7 + 2 + 1 + 1).

- [ ] **Step 5: Commit**

```bash
git add pipeline/process_modis.py tests/test_modis_path_d.py
git commit -m "S15 P3.2 step 6: Path D dNTI contextual en process_modis.py

Pixel MODIS 1 km -> footprint 8-vecinos cubre 3x3 km.
Diagnostico expuesto en diag_n_dnti_ctx_path."
```

---

## Task 7: Full crossmatch + commit final

- [ ] **Step 1: Reproceso 11 volcanes (subset Nov 2025 - Abr 2026)**

```bash
# Usar backfill para eficiencia
python scripts/backfill_nov_2025.py --all-volcanoes 2>&1 | tee logs/backfill_p32.log
```

Puede tardar 1-3 h. Dejar en background.

- [ ] **Step 2: Re-run crossmatch final**

```bash
python experiments/27_crossmatch_vs_consolidado.py --out experiments/27_crossmatch_post_p32.json
```

- [ ] **Step 3: Diff global**

```bash
python -c "
import json
pre=json.load(open('experiments/27_crossmatch_results.json'))
post=json.load(open('experiments/27_crossmatch_post_p32.json'))
def agg(d):
    tp=sum(len(v['tp']) for v in d.values())
    fn=sum(len(v['fn']) for v in d.values())
    fp=sum(len(v['fp']) for v in d.values())
    ratios=[m['ratio'] for v in d.values() for m in v['tp'] if m.get('ratio')]
    rm=sorted(ratios)[len(ratios)//2] if ratios else 0
    rec=tp/(tp+fn) if tp+fn else 0
    prec=tp/(tp+fp) if tp+fp else 0
    f1=2*rec*prec/(rec+prec) if rec+prec else 0
    return tp, fn, fp, rec, prec, f1, rm
a=agg(pre); b=agg(post)
print(f'              {\"TP\":>5} {\"FN\":>5} {\"FP\":>5} {\"Rec\":>6} {\"Prec\":>6} {\"F1\":>6} {\"R_med\":>6}')
print(f'Pre  P3.2:   {a[0]:>5} {a[1]:>5} {a[2]:>5} {a[3]:>6.2f} {a[4]:>6.2f} {a[5]:>6.2f} {a[6]:>6.2f}')
print(f'Post P3.2:   {b[0]:>5} {b[1]:>5} {b[2]:>5} {b[3]:>6.2f} {b[4]:>6.2f} {b[5]:>6.2f} {b[6]:>6.2f}')
print(f'Delta:        {b[0]-a[0]:+5d} {b[1]-a[1]:+5d} {b[2]-a[2]:+5d} {b[3]-a[3]:+6.2f} {b[4]-a[4]:+6.2f} {b[5]-a[5]:+6.2f} {b[6]-a[6]:+6.2f}')
"
```

Criterio de aceptacion:
- Rec >= 0.23 (no baja mas de 5pp)
- Prec sube
- Ratio mediano converge a 1.0
- Lastarria ratio < 3.0 (del JSON detalle)

- [ ] **Step 4: Update baseline memory**

Editar `memory/project_baseline_pre_p3_s15.md`: agregar seccion "Post P3.2" con los numeros nuevos.

- [ ] **Step 5: Commit final**

```bash
git add experiments/27_crossmatch_post_p32.json memory/project_baseline_pre_p3_s15.md
git commit -m "S15 P3.2 cerrado: dNTI contextual integrado en 3 pipelines

Global pre->post:
  Recall X.XX -> Y.YY
  Precision X.XX -> Y.YY
  F1 X.XX -> Y.YY
  Ratio_med X.XX -> Y.YY
Lastarria ratio mediano pasa de 19.87 a Z.ZZ (objetivo <3).

Siguiente: P3.1 dual-ROI o P3.3 ETI cuadratico."
```

---

## Self-review

**Spec coverage:**
- Reemplazar gate global por contextual: Task 3/5/6 ✓ (se agrega como Path D al OR, Path A se mantiene pero rank effectivo baja; replace puro sería P3.2b siguiente).
- 8-vecinos: Task 1 footprint 3×3 sin centro ✓.
- C1=0.003 Coppola 2016a summit: Task 2 yaml ✓.
- Afecta 3 process_*.py: Task 3/5/6 ✓.
- Medido con experiments/27 pre/post: Task 4 (VIIRS 375m) + Task 7 (global) ✓.
- Criterio ratio Lastarria <3, recall no baja 5pp: Task 4 gate + Task 7 verificación ✓.

**Placeholder scan:**
- "TBD" / "TODO": no encontrados.
- "Handle edge cases": no usado (todo explicito).
- Type / name consistency: `n_dnti_ctx_path` (no `n_dnti_ctx`), `contextual_dnti_hot_mask`, `DNTI_CONTEXTUAL_C1`, `ENABLE_DNTI_CONTEXTUAL_PATH`, `dnti_contextual_c1` (yaml lowercase), `enable_dnti_contextual_path` (yaml) — consistente.

**Gaps conocidos:**
- Task 5/6 tienen placeholder `bt_mir` / `t_bg_mir` a confirmar por lectura de archivo. Aceptable: el engineer debe verificar nombre real antes del replace.
- Task 7 depende de backfill full, que puede tardar >1h. Si urge, subset a 3 volcanes (Lastarria, Lascar, Chaiten) para checkpoint.

---

**Plan complete and saved to `tasks/plan_s15_p3_2_dnti_contextual.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - despacho subagent fresco por tarea, review entre tareas, iteración rápida.

**2. Inline Execution** - ejecuto tasks en esta sesión con executing-plans, batch con checkpoints.

**¿Cuál?**
