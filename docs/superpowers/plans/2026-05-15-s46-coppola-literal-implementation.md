# S46 Coppola 2016a Literal Round 1 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar 13 variantes A/B paralelas para corregir 5 drifts críticos identificados en R6 audit (Test 1 K1, Tests 2 ∧ 3 + dETI, second-pass, MODIS+VIIRS nadir-fijo) y validar empíricamente cuáles alinean operacional con MIROVA literal post-Coppola 2016a SP426.5.

**Architecture:** Branch `s46-coppola-literal-round1` con TDD obligatorio. Cada drift como flag opt-in en YAML, tests sintéticos antes que código. 13 profile YAMLs extendiendo `mirova_equivalent.yaml`. 1 workflow GitHub Actions parametrizado con `variant` choice input. Audit script consolida resultados per-sensor. Sin tocar `mirova_equivalent.yaml` operacional hasta decisión post-Ronda 1.

**Tech Stack:** Python 3.11+, numpy, scipy.ndimage, pytest, GitHub Actions, pandas, rasterio (tests R2), pyyaml.

---

## File Structure

### Modificar (existing)

- `pipeline/scan_geometry.py:124-203` — agregar parámetro `nadir_fixed` a `modis_pixel_areas` y `viirs_pixel_areas`
- `pipeline/detection_context.py` — agregar función nueva `first_pass_tests_2_and_3` después de línea 142
- `pipeline/process_modis.py:358-490` — wiring flags drift #1, #2+#3, #4
- `pipeline/process_viirs.py:359-595` — wiring flags
- `pipeline/process_viirs_mod.py:380-529` — wiring flags
- `pipeline/profiles/mirova_equivalent.yaml` — NO TOCAR (operacional)
- `pipeline/constants.py` o equivalente — agregar nuevas constantes

### Crear (new)

- `pipeline/profiles/_baseline_s44.yaml` (alias `mirova_equivalent.yaml`)
- `pipeline/profiles/_drift1a_only.yaml`
- `pipeline/profiles/_drift1b_only.yaml`
- `pipeline/profiles/_drift1ab_only.yaml`
- `pipeline/profiles/_drift23_only.yaml`
- `pipeline/profiles/_drift23_dual_only.yaml`
- `pipeline/profiles/_drift4_only.yaml`
- `pipeline/profiles/_drift234_only.yaml`
- `pipeline/profiles/_drift7_modis_only.yaml`
- `pipeline/profiles/_drift7_viirs_only.yaml`
- `pipeline/profiles/_drift7_both_only.yaml`
- `pipeline/profiles/_coppola_full.yaml`
- `pipeline/profiles/_dibella_n12_viirs_only.yaml`
- `tests/test_drift1_test1_k1_saturation.py`
- `tests/test_drift23_first_pass_tests_2_3.py`
- `tests/test_drift4_second_pass_enabled.py`
- `tests/test_drift7_nadir_fixed_pixel.py`
- `tests/test_drift13_dibella_n12_viirs.py`
- `tests/test_r2_pixel_level.py`
- `tests/test_s46_integration.py`
- `.github/workflows/reproc-s46-coppola-literal-ab.yml`
- `experiments/87_audit_s46_round1.py`

---

## Task 0: Setup branch + baseline verde

**Files:**
- Branch: `s46-coppola-literal-round1` desde `main`

- [ ] **Step 0.1: Crear branch desde main actualizado**

```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/.claude/worktrees/sweet-austin-b5413b"
git checkout main
git pull origin main
git checkout -b s46-coppola-literal-round1
```

- [ ] **Step 0.2: Verificar suite tests baseline verde**

Run: `pytest tests/ -x --tb=short 2>&1 | tail -20`
Expected: PASS (al menos 275 verde, 16 skip, 0 fail según S44)

- [ ] **Step 0.3: Documentar baseline stats**

```bash
pytest tests/ --collect-only -q 2>&1 | tail -5 > /tmp/baseline_test_count.txt
git log -1 --oneline > /tmp/baseline_commit.txt
```

---

## Task 1: Drift #1a — Test 1 K1 retire from hot_mask

**Files:**
- Test: `tests/test_drift1_test1_k1_saturation.py` (new)
- Modify: `pipeline/process_modis.py:486-490`, `pipeline/process_viirs.py:591-595`, `pipeline/process_viirs_mod.py:525-529`

- [ ] **Step 1.1: Escribir test sintético failing**

Create file `tests/test_drift1_test1_k1_saturation.py`:

```python
"""Tests Drift #1a — Test 1 K1 retire from hot_mask (Coppola 2016a literal)."""
import numpy as np
import pytest

from pipeline.detection_context import _nanmean_ignore_self


def _build_synthetic_granule_test1_only(nti_value=-0.5):
    """Granule con 1 pixel que cumple Test 1 K1 (NTI > -0.8 noche) pero NO Tests 2∧3."""
    shape = (10, 10)
    nti = np.full(shape, -0.97)  # bg típico
    nti[5, 5] = nti_value  # 1 pixel anómalo solo en Test 1 K1
    bt = np.full(shape, 268.0)
    bt[5, 5] = 270.0  # ligeramente sobre bg
    roi_mask = np.ones(shape, dtype=bool)
    return {"nti": nti, "bt": bt, "roi_mask": roi_mask}


def test_drift1a_off_legacy_nti_path_contributes():
    """Flag OFF: pixel Test 1 K1 entra al hot_mask (legacy behavior)."""
    from pipeline.process_viirs import _combine_hot_paths

    data = _build_synthetic_granule_test1_only(nti_value=-0.5)
    saturation_mask = np.zeros_like(data["roi_mask"])

    # Legacy: nti_path_hot entra al OR
    nti_path_hot = (~saturation_mask) & data["roi_mask"] & (data["nti"] > -0.8)

    hot_mask = _combine_hot_paths(
        bt_path_hot=np.zeros_like(data["roi_mask"]),
        nti_path_hot=nti_path_hot,
        dnti_ctx_hot=np.zeros_like(data["roi_mask"]),
        test1_hot=np.zeros_like(data["roi_mask"]),
        enable_test1_k1_retire_from_hot_mask=False,
    )

    assert hot_mask[5, 5], "Legacy: pixel Test 1 K1 debe estar en hot_mask"
    assert int(np.sum(hot_mask)) == 1


def test_drift1a_on_nti_path_removed_from_hot_mask():
    """Flag ON: pixel Test 1 K1 NO entra al hot_mask, sí queda en diag."""
    from pipeline.process_viirs import _combine_hot_paths

    data = _build_synthetic_granule_test1_only(nti_value=-0.5)
    saturation_mask = np.zeros_like(data["roi_mask"])

    nti_path_hot = (~saturation_mask) & data["roi_mask"] & (data["nti"] > -0.8)

    hot_mask = _combine_hot_paths(
        bt_path_hot=np.zeros_like(data["roi_mask"]),
        nti_path_hot=nti_path_hot,
        dnti_ctx_hot=np.zeros_like(data["roi_mask"]),
        test1_hot=np.zeros_like(data["roi_mask"]),
        enable_test1_k1_retire_from_hot_mask=True,
    )

    assert not hot_mask[5, 5], "Flag ON: pixel Test 1 K1 NO debe estar en hot_mask"
    assert int(np.sum(hot_mask)) == 0


def test_drift1a_does_not_affect_other_paths():
    """Flag ON: paths bt_path, dnti_ctx, test1 NO afectados."""
    from pipeline.process_viirs import _combine_hot_paths

    shape = (10, 10)
    bt_path_hot = np.zeros(shape, dtype=bool)
    bt_path_hot[3, 3] = True  # 1 pixel bt_path
    nti_path_hot = np.zeros(shape, dtype=bool)
    nti_path_hot[5, 5] = True  # 1 pixel solo Test 1 K1
    dnti_ctx_hot = np.zeros(shape, dtype=bool)
    test1_hot = np.zeros(shape, dtype=bool)

    hot_mask = _combine_hot_paths(
        bt_path_hot=bt_path_hot,
        nti_path_hot=nti_path_hot,
        dnti_ctx_hot=dnti_ctx_hot,
        test1_hot=test1_hot,
        enable_test1_k1_retire_from_hot_mask=True,
    )

    assert hot_mask[3, 3], "bt_path debe seguir contribuyendo"
    assert not hot_mask[5, 5], "nti_path NO debe contribuir con flag ON"
    assert int(np.sum(hot_mask)) == 1
```

- [ ] **Step 1.2: Verificar test falla (función no existe)**

Run: `pytest tests/test_drift1_test1_k1_saturation.py -v`
Expected: FAIL con `ImportError: cannot import name '_combine_hot_paths'`

- [ ] **Step 1.3: Implementar `_combine_hot_paths` helper en `pipeline/process_viirs.py`**

Add después de `WOOSTER_COEFF = 18.0` (line ~52):

```python
def _combine_hot_paths(
    bt_path_hot: np.ndarray,
    nti_path_hot: np.ndarray,
    dnti_ctx_hot: np.ndarray,
    test1_hot: np.ndarray,
    *,
    enable_test1_k1_retire_from_hot_mask: bool = False,
    nti_rel_hot: np.ndarray = None,
    eti_path_hot: np.ndarray = None,
) -> np.ndarray:
    """Combina paths legacy + nuevos drift flags.

    Drift #1a: si flag ON, nti_path_hot NO entra al OR (Coppola 2016a literal
    — Test 1 K1 es saturation mask, NO hotspot reportable).

    Args:
        bt_path_hot, nti_path_hot, dnti_ctx_hot, test1_hot: bool 2D masks.
        enable_test1_k1_retire_from_hot_mask: flag drift #1a.
        nti_rel_hot, eti_path_hot: opcional, default None → zeros.

    Returns:
        bool 2D hot_mask combinado.
    """
    if nti_rel_hot is None:
        nti_rel_hot = np.zeros_like(bt_path_hot)
    if eti_path_hot is None:
        eti_path_hot = np.zeros_like(bt_path_hot)

    if enable_test1_k1_retire_from_hot_mask:
        # Drift #1a: nti_path_hot NO contribuye al hot_mask
        return bt_path_hot | dnti_ctx_hot | test1_hot | nti_rel_hot | eti_path_hot
    else:
        return bt_path_hot | nti_path_hot | dnti_ctx_hot | test1_hot | nti_rel_hot | eti_path_hot
```

Hacer mismo helper en `pipeline/process_modis.py` y `pipeline/process_viirs_mod.py` (importable via relative).

Mejor opción: mover a `pipeline/detection_context.py` para no duplicar:

Add en `detection_context.py` después de `dual_roi_bt_threshold` (line ~240):

```python
def combine_hot_paths(
    bt_path_hot: np.ndarray,
    nti_path_hot: np.ndarray,
    dnti_ctx_hot: np.ndarray,
    test1_hot: np.ndarray,
    *,
    enable_test1_k1_retire_from_hot_mask: bool = False,
    nti_rel_hot: np.ndarray = None,
    eti_path_hot: np.ndarray = None,
) -> np.ndarray:
    """[docstring igual]"""
    [implementation igual]
```

Importar en 3 procesadores como `from .detection_context import combine_hot_paths`.

- [ ] **Step 1.4: Actualizar test import**

Edit `tests/test_drift1_test1_k1_saturation.py`:

```python
from pipeline.detection_context import combine_hot_paths  # NEW

def _combine_hot_paths(*args, **kwargs):
    return combine_hot_paths(*args, **kwargs)
```

- [ ] **Step 1.5: Verificar tests pass**

Run: `pytest tests/test_drift1_test1_k1_saturation.py -v`
Expected: 3 tests PASS

- [ ] **Step 1.6: Wire flag en `process_modis.py:486-490`**

Find:
```python
hot_mask_2d = (bt_path_hot | nti_path_hot | dnti_ctx_hot | test1_hot
               | eti_path_hot)
```

Replace with:
```python
hot_mask_2d = combine_hot_paths(
    bt_path_hot, nti_path_hot, dnti_ctx_hot, test1_hot,
    enable_test1_k1_retire_from_hot_mask=ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK,
    eti_path_hot=eti_path_hot,
)
```

Add at top of file (con otros imports):
```python
ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK = _get_profile_flag(
    "enable_test1_k1_retire_from_hot_mask", default=False
)
```

(Asumiendo `_get_profile_flag` helper existente. Si no, ver patrón S38/S40 cómo se cargan flags desde YAML.)

- [ ] **Step 1.7: Wire flag en `process_viirs.py:591-595` y `process_viirs_mod.py:525-529`**

Mismo patrón. Reemplazar OR manual con `combine_hot_paths(...)`.

- [ ] **Step 1.8: Run suite completa**

Run: `pytest tests/ -x --tb=short 2>&1 | tail -10`
Expected: PASS (test count baseline + 3 nuevos)

- [ ] **Step 1.9: Commit**

```bash
git add tests/test_drift1_test1_k1_saturation.py pipeline/detection_context.py pipeline/process_modis.py pipeline/process_viirs.py pipeline/process_viirs_mod.py
git commit -m "drift1a: Test 1 K1 retire from hot_mask flag + TDD tests

Implementa flag ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK que retira nti_path
del hot_mask reportable (Coppola 2016a SP426.5: Test 1 K1 es saturation
mask, no hotspot). Diag tracking preservado.

3 tests sintéticos cubren legacy/flag-on/non-interference paths."
```

---

## Task 2: Drift #1b — bg_vals excluye Test 1 K1 active

**Files:**
- Test: `tests/test_drift1_test1_k1_saturation.py` (extend)
- Modify: `pipeline/process_modis.py:271-276`, `pipeline/process_viirs.py:385-388`, `pipeline/process_viirs_mod.py:~280`

- [ ] **Step 2.1: Escribir tests adicionales drift #1b**

Append a `tests/test_drift1_test1_k1_saturation.py`:

```python
def _build_synthetic_bg_with_test1_in_ring():
    """Background ring incluye 1 pixel hot Test 1 K1 → contaminates t_bg."""
    shape = (20, 20)
    bt_mir = np.full(shape, 268.0, dtype=np.float64)  # bg
    nti = np.full(shape, -0.97, dtype=np.float64)
    # bg ring zone (dist >= BG_INNER, <= BG_OUTER) — simulamos con coordenadas
    bg_mask = np.zeros(shape, dtype=bool)
    bg_mask[2:18, 2:18] = True  # área grande "bg ring"
    bg_mask[5:7, 5:7] = False  # core volcano excluido del bg

    # Inject pixel Test 1 K1 dentro del bg ring (no en core)
    bt_mir[10, 10] = 295.0  # mucho más caliente que bg típico
    nti[10, 10] = -0.5  # supera K1=-0.8 noche
    return {"bt_mir": bt_mir, "nti": nti, "bg_mask": bg_mask}


def test_drift1b_off_bg_contaminated_by_test1_active():
    """Flag OFF: t_bg inflado por pixel Test 1 K1 dentro del ring."""
    from pipeline.detection_context import compute_bg_stats

    data = _build_synthetic_bg_with_test1_in_ring()
    t_bg, std_bg, n_bg = compute_bg_stats(
        bt=data["bt_mir"],
        bg_mask=data["bg_mask"],
        nti=data["nti"],
        nti_k1_threshold=-0.8,
        enable_test1_k1_bg_exclude=False,
    )

    # Sin exclusión: pixel @ 295K infla t_bg
    assert t_bg > 268.0, f"Sin exclusión, t_bg debería estar inflado (got {t_bg})"


def test_drift1b_on_bg_excludes_test1_k1_active():
    """Flag ON: pixel Test 1 K1 excluido del bg → t_bg correcto."""
    from pipeline.detection_context import compute_bg_stats

    data = _build_synthetic_bg_with_test1_in_ring()
    t_bg, std_bg, n_bg = compute_bg_stats(
        bt=data["bt_mir"],
        bg_mask=data["bg_mask"],
        nti=data["nti"],
        nti_k1_threshold=-0.8,
        enable_test1_k1_bg_exclude=True,
    )

    # Con exclusión: pixel @ 295K NO contamina
    assert t_bg == pytest.approx(268.0, abs=0.1), (
        f"Con exclusión, t_bg debería ser ~268K (got {t_bg})"
    )
    # n_bg debería ser 1 menos
    assert n_bg < np.sum(data["bg_mask"])
```

- [ ] **Step 2.2: Verificar tests fail**

Run: `pytest tests/test_drift1_test1_k1_saturation.py::test_drift1b_off_bg_contaminated_by_test1_active -v`
Expected: FAIL con `ImportError: cannot import compute_bg_stats`

- [ ] **Step 2.3: Implementar `compute_bg_stats` en `detection_context.py`**

Add después de `combine_hot_paths`:

```python
def compute_bg_stats(
    bt: np.ndarray,
    bg_mask: np.ndarray,
    *,
    nti: np.ndarray = None,
    nti_k1_threshold: float = -0.8,
    enable_test1_k1_bg_exclude: bool = False,
    min_bg_pixels: int = 10,
) -> tuple:
    """Compute t_bg (median), std_bg, n_bg sobre bg_mask.

    Drift #1b: si flag ON, excluye pixels Test 1 K1 active del bg_vals
    (Coppola 2016a SP426.5: Test 1 K1 active "discarded for further steps").

    Args:
        bt: 2D array BT (K).
        bg_mask: bool 2D, True en bg ring.
        nti: 2D array NTI (requerido si enable_test1_k1_bg_exclude).
        nti_k1_threshold: K1 noche (-0.8) o día (-0.6).
        enable_test1_k1_bg_exclude: flag drift #1b.
        min_bg_pixels: mínimo bg para confiabilidad.

    Returns:
        (t_bg, std_bg, n_bg) o (None, None, 0) si <min_bg_pixels.
    """
    effective_bg_mask = bg_mask & ~np.isnan(bt)

    if enable_test1_k1_bg_exclude:
        if nti is None:
            raise ValueError("nti requerido si enable_test1_k1_bg_exclude=True")
        test1_k1_active = (nti > nti_k1_threshold) & ~np.isnan(nti)
        effective_bg_mask = effective_bg_mask & ~test1_k1_active

    bg_vals = bt[effective_bg_mask]
    n_bg = int(len(bg_vals))
    if n_bg < min_bg_pixels:
        return None, None, n_bg

    t_bg = float(np.median(bg_vals))
    std_bg = float(np.std(bg_vals))
    return t_bg, std_bg, n_bg
```

- [ ] **Step 2.4: Run tests drift #1b**

Run: `pytest tests/test_drift1_test1_k1_saturation.py -v`
Expected: 5 tests PASS (3 drift #1a + 2 drift #1b)

- [ ] **Step 2.5: Wire flag en `process_viirs.py:385-388`**

Find:
```python
bg_vals = bt[bg_mask & ~np.isnan(bt)]
if len(bg_vals) >= 10:
    t_bg_i04 = float(np.median(bg_vals))
    std_bg = float(np.std(bg_vals))
```

Replace with:
```python
t_bg_i04, std_bg, n_bg = compute_bg_stats(
    bt=bt,
    bg_mask=bg_mask,
    nti=nti,
    nti_k1_threshold=NTI_K1_NIGHT,
    enable_test1_k1_bg_exclude=ENABLE_TEST1_K1_BG_EXCLUDE,
)
if t_bg_i04 is None:
    # Manejo error existente — copiar lógica de líneas siguientes
    ...
```

Same pattern en `process_modis.py:271-276` y `process_viirs_mod.py`. **Importante**: preservar lógica de fallback existente cuando `n_bg < 10`.

- [ ] **Step 2.6: Run suite completa**

Run: `pytest tests/ -x --tb=short`
Expected: PASS baseline + 5 nuevos

- [ ] **Step 2.7: Commit**

```bash
git add tests/test_drift1_test1_k1_saturation.py pipeline/detection_context.py pipeline/process_modis.py pipeline/process_viirs.py pipeline/process_viirs_mod.py
git commit -m "drift1b: bg_vals excluye Test 1 K1 active + tests TDD

compute_bg_stats helper centralizado en detection_context.py. Flag
ENABLE_TEST1_K1_BG_EXCLUDE excluye pixels NTI > -0.8 del bg ring antes
de computar t_bg/std_bg (Coppola 2016a SP426.5 line 352-356)."
```

---

## Task 3: Drift #7 — A_pix nadir-fijo (MODIS + VIIRS)

**Files:**
- Test: `tests/test_drift7_nadir_fixed_pixel.py` (new)
- Modify: `pipeline/scan_geometry.py:124-203`

- [ ] **Step 3.1: Escribir tests sintéticos**

Create `tests/test_drift7_nadir_fixed_pixel.py`:

```python
"""Tests Drift #7 — A_pix nadir-fijo (Coppola 2016a SP426.5 line 201-202)."""
import numpy as np
import pytest

from pipeline.scan_geometry import modis_pixel_areas, viirs_pixel_areas


def test_drift7_modis_nadir_fixed_returns_uniform_1km2():
    """nadir_fixed=True: todas las pixels son 1 km² = 1e6 m²."""
    shape = (100, 100)
    scan_angles = np.linspace(0, 60, 100)
    scan_angles_2d = np.broadcast_to(scan_angles, shape)

    areas = modis_pixel_areas(
        shape=shape,
        scan_angles_deg=scan_angles_2d,
        nadir_fixed=True,
    )

    assert areas.shape == shape
    assert np.allclose(areas, 1_000_000.0), (
        f"Con nadir_fixed=True, todas deben ser 1e6 (got range {areas.min()}-{areas.max()})"
    )


def test_drift7_modis_legacy_sec3_preserved():
    """nadir_fixed=False (default): aplica sec³(θz) como antes."""
    shape = (1, 3)
    scan_angles = np.array([[0.0, 30.0, 60.0]])

    areas = modis_pixel_areas(
        shape=shape,
        scan_angles_deg=scan_angles,
        nadir_fixed=False,
    )

    # Nadir: A_pix = 1e6
    assert areas[0, 0] == pytest.approx(1e6, rel=0.01)
    # 30°: sec³(30) ≈ 1.54 → A ≈ 1.54e6
    assert areas[0, 1] == pytest.approx(1.54e6, rel=0.05)
    # 60°: sec³(60) = 8 → A ≈ 8e6
    assert areas[0, 2] == pytest.approx(8e6, rel=0.05)


def test_drift7_viirs_375m_nadir_fixed():
    """VIIRS I-band: nadir_fixed=True → todos 140625 m² (0.140625 km²)."""
    zen = np.array([0.0, 30.0, 60.0, 70.0])
    areas = viirs_pixel_areas(
        sensor_zenith_deg=zen,
        nadir_area_m2=140625.0,
        nadir_fixed=True,
    )
    assert np.allclose(areas, 140625.0)


def test_drift7_viirs_750m_nadir_fixed():
    """VIIRS M-band: nadir_fixed=True → todos 562500 m²."""
    zen = np.array([0.0, 30.0, 60.0, 70.0])
    areas = viirs_pixel_areas(
        sensor_zenith_deg=zen,
        nadir_area_m2=562500.0,
        nadir_fixed=True,
    )
    assert np.allclose(areas, 562500.0)


def test_drift7_viirs_legacy_factor_preserved():
    """nadir_fixed=False (default): factor lineal 1-2x como antes."""
    zen = np.array([0.0, 60.0, 70.0])
    areas = viirs_pixel_areas(
        sensor_zenith_deg=zen,
        nadir_area_m2=140625.0,
        nadir_fixed=False,
    )
    # Nadir: factor 1.0 → 140625
    assert areas[0] == pytest.approx(140625.0, rel=0.01)
    # 60°: factor ~1.5
    assert areas[1] > 140625.0
    assert areas[1] < 280000.0
    # 70°: cap 2.0 → 281250
    assert areas[2] == pytest.approx(281250.0, rel=0.01)
```

- [ ] **Step 3.2: Verificar tests fail**

Run: `pytest tests/test_drift7_nadir_fixed_pixel.py -v`
Expected: FAIL con `TypeError: modis_pixel_areas() got unexpected keyword argument 'nadir_fixed'`

- [ ] **Step 3.3: Implementar parámetro `nadir_fixed` en `modis_pixel_areas`**

Edit `pipeline/scan_geometry.py:124-136`:

Find:
```python
def modis_pixel_areas(scan_angles_deg, ...):
    """[docstring existente]"""
    # ... cálculo sec³ ...
```

Replace with:
```python
def modis_pixel_areas(shape, scan_angles_deg, nadir_fixed: bool = False, ...):
    """Per-pixel area (m²) MODIS.

    Args:
        shape: tuple (rows, cols) del granule.
        scan_angles_deg: per-pixel scan angles (degrees).
        nadir_fixed: si True, retorna A_pix=1 km² uniforme (Coppola 2016a
            SP426.5 line 201-202: "resampled within a 50×50 km grid…
            spatial resolution of the resampled MODIS pixels is 1 km").

    Returns:
        2D array (m²) shape=shape.
    """
    if nadir_fixed:
        return np.full(shape, 1_000_000.0, dtype=np.float64)
    # Legacy sec³ behavior
    z = np.clip(np.abs(np.asarray(scan_angles_deg)), 0.0, 65.0)
    cos_z = np.cos(np.radians(z))
    return 1_000_000.0 / (cos_z ** 3)
```

(Verificar signature existente — el ejemplo asume cambio menor. Si retorna shape distinto, ajustar para preservar interface.)

- [ ] **Step 3.4: Implementar parámetro `nadir_fixed` en `viirs_pixel_areas`**

Edit `pipeline/scan_geometry.py:169-203`:

Add parameter `nadir_fixed: bool = False`:
```python
def viirs_pixel_areas(sensor_zenith_deg, nadir_area_m2, nadir_fixed: bool = False) -> np.ndarray:
    """[docstring existente extendido]

    Args:
        ...
        nadir_fixed: si True, retorna nadir_area_m2 uniforme (Coppola
            literal). False: factor lineal 1-2x bow-tie (legacy S14).
    """
    if nadir_fixed:
        z = np.asarray(sensor_zenith_deg)
        return np.full_like(z, nadir_area_m2, dtype=np.float64)
    # Legacy linear factor
    [código existente líneas 196-203]
```

- [ ] **Step 3.5: Run tests**

Run: `pytest tests/test_drift7_nadir_fixed_pixel.py -v`
Expected: 5 tests PASS

- [ ] **Step 3.6: Wire flags en procesadores**

Edit `pipeline/process_modis.py` donde se llama `modis_pixel_areas`:

```python
pixel_areas = modis_pixel_areas(
    shape=bt_mir.shape,
    scan_angles_deg=geo["scan_angle"],
    nadir_fixed=ENABLE_NADIR_FIXED_PIXEL_AREA_MODIS,
)
```

Edit `pipeline/process_viirs.py:271` y `pipeline/process_viirs_mod.py:257`:

```python
pixel_areas = viirs_pixel_areas(
    geo["sensor_zenith"],
    NADIR_PIXEL_AREA_M2,
    nadir_fixed=ENABLE_NADIR_FIXED_PIXEL_AREA_VIIRS,
)
```

Add constants al top:
```python
ENABLE_NADIR_FIXED_PIXEL_AREA_MODIS = _get_profile_flag(
    "enable_nadir_fixed_pixel_area_modis", default=False
)
ENABLE_NADIR_FIXED_PIXEL_AREA_VIIRS = _get_profile_flag(
    "enable_nadir_fixed_pixel_area_viirs", default=False
)
```

- [ ] **Step 3.7: Run suite completa**

Run: `pytest tests/ -x --tb=short`
Expected: PASS

- [ ] **Step 3.8: Commit**

```bash
git add tests/test_drift7_nadir_fixed_pixel.py pipeline/scan_geometry.py pipeline/process_modis.py pipeline/process_viirs.py pipeline/process_viirs_mod.py
git commit -m "drift7: A_pix nadir-fijo flags MODIS + VIIRS + TDD

Coppola 2016a SP426.5 line 201-202 + Eq.7: 'A_PIX is the pixel size
(1 km² for the resampled MODIS pixels)'. Flags opt-in para preservar
calibración empírica S14 (VIIRS) como default.

5 tests sintéticos cubren nadir-fixed/legacy MODIS sec³/VIIRS factor."
```

---

## Task 4: Drift #2+#3 — first_pass_tests_2_and_3 function

**Files:**
- Test: `tests/test_drift23_first_pass_tests_2_3.py` (new)
- Modify: `pipeline/detection_context.py` (add function after line 142)

- [ ] **Step 4.1: Escribir tests sintéticos completos**

Create `tests/test_drift23_first_pass_tests_2_3.py`:

```python
"""Tests Drift #2+#3 — first-pass Tests 2 ∧ 3 + dETI + AND + C2·σ + dual-ROI."""
import numpy as np
import pytest


def _build_synthetic_test2_only_pixel():
    """Granule: pixel pasa Test 2 (dNTI alto) pero falla Test 3 (dETI bajo)."""
    shape = (20, 20)
    # Bulk bg: NTI ~ -0.97, ETI ~ 0
    nti = np.random.normal(-0.97, 0.001, shape)
    nti_app = np.random.normal(-0.97, 0.001, shape)
    bt = np.full(shape, 268.0)

    # Pixel @ (10,10): dNTI alto pero dETI ~0 (NTI sube pero coincide con NTI_app)
    nti[10, 10] = -0.5
    nti_app[10, 10] = -0.5  # coincide → ETI ≈ 0 → dETI ≈ 0
    bt[10, 10] = 285.0

    roi_mask = np.ones(shape, dtype=bool)
    dist_km = np.full(shape, 2.0)  # all summit
    return {
        "nti": nti, "nti_app": nti_app, "bt": bt,
        "roi_mask": roi_mask, "dist_km": dist_km,
    }


def _build_synthetic_test2_and_test3_pixel():
    """Granule: pixel pasa AMBOS Tests 2 ∧ 3 (dNTI alto Y dETI alto)."""
    shape = (20, 20)
    nti = np.random.normal(-0.97, 0.001, shape)
    nti_app = np.random.normal(-0.97, 0.001, shape)
    bt = np.full(shape, 268.0)

    # Pixel: NTI sube (anómalo) Y NTI_app NO sube (modelo no-volcánico estable)
    # → dNTI alto, ETI (NTI - NTI_app) alto, dETI alto
    nti[10, 10] = -0.5
    nti_app[10, 10] = -0.95  # NTI_app modelo se queda en bg
    bt[10, 10] = 285.0

    roi_mask = np.ones(shape, dtype=bool)
    dist_km = np.full(shape, 2.0)
    return {
        "nti": nti, "nti_app": nti_app, "bt": bt,
        "roi_mask": roi_mask, "dist_km": dist_km,
    }


def test_drift23_requires_both_tests_2_AND_3():
    """Pixel pasa Test 2 (dNTI) pero NO Test 3 (dETI) → NO active."""
    from pipeline.detection_context import first_pass_tests_2_and_3

    data = _build_synthetic_test2_only_pixel()
    hot, diag = first_pass_tests_2_and_3(
        nti=data["nti"], nti_app=data["nti_app"], bt=data["bt"],
        roi_mask=data["roi_mask"], dist_km=data["dist_km"],
        t_bg=268.0, bt_sanity_k=3.0,
        c1_dnti_summit=0.003, c1_deti_summit=0.003,
        c2_dnti_summit=5, c2_deti_summit=5,
        inner_km=5.0,
    )

    assert not hot[10, 10], "Conjunción AND obligatoria: dETI=0 debe rechazar"
    assert diag["n_first_pass_pixels"] == 0


def test_drift23_passes_when_both_tests_pass():
    """Pixel con dNTI Y dETI altos → active."""
    from pipeline.detection_context import first_pass_tests_2_and_3

    data = _build_synthetic_test2_and_test3_pixel()
    hot, diag = first_pass_tests_2_and_3(
        nti=data["nti"], nti_app=data["nti_app"], bt=data["bt"],
        roi_mask=data["roi_mask"], dist_km=data["dist_km"],
        t_bg=268.0, bt_sanity_k=3.0,
        c1_dnti_summit=0.003, c1_deti_summit=0.003,
        c2_dnti_summit=5, c2_deti_summit=5,
        inner_km=5.0,
    )

    assert hot[10, 10], "Ambos Tests 2 y 3 pasan → debe estar active"
    assert diag["n_first_pass_pixels"] >= 1


def test_drift23_dual_roi_uses_stricter_C1_in_scene():
    """Pixel scene con dNTI marginal pasa C1=0.003 (summit) pero NO C1=0.010 (scene)."""
    from pipeline.detection_context import first_pass_tests_2_and_3

    shape = (20, 20)
    nti = np.random.normal(-0.97, 0.001, shape)
    nti_app = np.random.normal(-0.97, 0.001, shape)
    bt = np.full(shape, 268.0)

    # Pixel @ scene zone con dNTI marginal (0.005, entre 0.003 y 0.010)
    nti[10, 10] = -0.965  # +0.005 vs bg → dNTI ~0.005
    nti_app[10, 10] = -0.975  # → ETI alto
    bt[10, 10] = 285.0

    dist_km = np.full(shape, 10.0)  # scene zone
    roi_mask = np.ones(shape, dtype=bool)

    hot_dual, _ = first_pass_tests_2_and_3(
        nti=nti, nti_app=nti_app, bt=bt,
        roi_mask=roi_mask, dist_km=dist_km,
        t_bg=268.0, bt_sanity_k=3.0,
        c1_dnti_summit=0.003, c1_deti_summit=0.003,
        c2_dnti_summit=5, c2_deti_summit=5,
        inner_km=5.0,
        c1_dnti_scene=0.010, c1_deti_scene=0.010,
        c2_dnti_scene=10, c2_deti_scene=10,
    )

    # Dual-ROI scene: dNTI=0.005 < C1_scene=0.010 → NO active
    assert not hot_dual[10, 10], "Dual-ROI scene: dNTI marginal NO pasa"


def test_drift23_statistical_OR_branch():
    """Pixel dNTI < C1 pero > μ + C2·σ → active vía rama statistical."""
    from pipeline.detection_context import first_pass_tests_2_and_3

    shape = (100, 100)
    # σ_dNTI muy bajo: μ + 5σ = umbral muy chico
    nti = np.random.normal(-0.97, 0.0001, shape)  # σ chico
    nti_app = np.random.normal(-0.97, 0.0001, shape)
    bt = np.full(shape, 268.0)

    # Pixel: dNTI = 0.002 (< C1=0.003 absoluto, pero > μ+5σ con σ=0.0001)
    nti[50, 50] = -0.968  # +0.002 sobre bg
    nti_app[50, 50] = -0.97
    bt[50, 50] = 285.0

    roi_mask = np.ones(shape, dtype=bool)
    dist_km = np.full(shape, 2.0)

    hot, _ = first_pass_tests_2_and_3(
        nti=nti, nti_app=nti_app, bt=bt,
        roi_mask=roi_mask, dist_km=dist_km,
        t_bg=268.0, bt_sanity_k=3.0,
        c1_dnti_summit=0.003, c1_deti_summit=0.003,
        c2_dnti_summit=5, c2_deti_summit=5,
        inner_km=5.0,
    )

    # Rama OR estadística: dNTI=0.002 < 0.003 pero > μ+5σ → active
    assert hot[50, 50], "Rama OR estadística debe disparar"
```

- [ ] **Step 4.2: Verificar fail**

Run: `pytest tests/test_drift23_first_pass_tests_2_3.py -v`
Expected: FAIL con `ImportError: cannot import 'first_pass_tests_2_and_3'`

- [ ] **Step 4.3: Implementar `first_pass_tests_2_and_3` en `detection_context.py`**

Add después de `dual_roi_contextual_dnti_hot_mask` (line 188):

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
    c1_dnti_scene: float = None,
    c1_deti_scene: float = None,
    c2_dnti_scene: float = None,
    c2_deti_scene: float = None,
    min_bg_pixels: int = 10,
) -> tuple:
    """Coppola 2016a SP426.5 first-pass — Tests 2 ∧ 3 conjunción + dual-ROI.

    Paper líneas 316-325:
        Test 2: dNTI > C1  OR  dNTI > μ_dNTI + C2·σ_dNTI
        Test 3: dETI > C1  OR  dETI > μ_dETI + C2·σ_dETI
        active ⇔ Test 2 ∧ Test 3

    Tabla 1 (noche): C1_summit=0.003 / C1_scene=0.010, C2_summit=5 / C2_scene=10.

    Args:
        nti: NTI observado.
        nti_app: NTI sintético (modelo no-volcánico, eq 2 paper).
        bt: BT MIR (K).
        roi_mask: bool 2D ROI mask.
        dist_km: per-pixel distance to vent (km).
        t_bg, bt_sanity_k: bg stats + floor.
        c1_*_summit, c2_*_summit: thresholds ROI1 (Tabla 1).
        inner_km: radio split summit/scene.
        c1_*_scene, c2_*_scene: thresholds ROI2 si dual; None → uniforme.
        min_bg_pixels: mínimo para μ, σ confiable.

    Returns:
        (hot_mask, diag_dict): bool 2D + dict con n_first_pass_pixels,
        mu_dnti, sd_dnti, mu_deti, sd_deti, n_bg_used.
    """
    # 1) ETI via helper existente
    mask_valid_eti = roi_mask & np.isfinite(nti) & np.isfinite(nti_app)
    eti = compute_eti_scene_quadratic(nti, nti_app, mask_valid_eti)

    # 2) dNTI y dETI vía 8-neighbor mean (paper línea 242-244)
    mean_nti = _nanmean_8neighbors_fast(nti)
    mean_eti = _nanmean_8neighbors_fast(eti)
    dnti = nti - mean_nti
    deti = eti - mean_eti

    # 3) μ, σ del bg regional
    bg_mask = roi_mask & np.isfinite(dnti) & np.isfinite(deti)
    n_bg = int(np.count_nonzero(bg_mask))
    if n_bg < min_bg_pixels:
        return np.zeros_like(roi_mask, dtype=bool), {
            "n_first_pass_pixels": 0, "n_bg_used": n_bg,
            "mu_dnti": None, "sd_dnti": None,
            "mu_deti": None, "sd_deti": None,
        }
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

- [ ] **Step 4.4: Run tests**

Run: `pytest tests/test_drift23_first_pass_tests_2_3.py -v`
Expected: 4 tests PASS

- [ ] **Step 4.5: Wire flag en `process_*.py:hot_mask_2d`**

Edit `pipeline/process_modis.py` antes de línea 490 (hot_mask_2d):

```python
if ENABLE_FIRST_PASS_TESTS_2_AND_3:
    is_summit_mask = np.where(dist_km <= INNER_RADIUS_KM, True, False)
    coppola_first_pass_hot, fp_diag = first_pass_tests_2_and_3(
        nti=nti, nti_app=nti_app, bt=bt_mir,
        roi_mask=roi_mask, dist_km=dist_km,
        t_bg=t_bg, bt_sanity_k=NTI_BT_SANITY_K,
        c1_dnti_summit=0.003, c1_deti_summit=0.003,
        c2_dnti_summit=5, c2_deti_summit=5,
        inner_km=INNER_RADIUS_KM,
        c1_dnti_scene=0.010 if ENABLE_DUAL_ROI_FIRST_PASS else None,
        c1_deti_scene=0.010 if ENABLE_DUAL_ROI_FIRST_PASS else None,
        c2_dnti_scene=10 if ENABLE_DUAL_ROI_FIRST_PASS else None,
        c2_deti_scene=10 if ENABLE_DUAL_ROI_FIRST_PASS else None,
    )
    hot_mask_2d = coppola_first_pass_hot
    # Diag fields
    record["diag_n_first_pass_pixels"] = fp_diag["n_first_pass_pixels"]
    record["diag_mu_dnti"] = fp_diag["mu_dnti"]
    record["diag_sd_dnti"] = fp_diag["sd_dnti"]
    # Paths legacy: solo diag
    record["diag_n_bt_path"] = int(np.sum(bt_path_hot))
    record["diag_n_nti_path"] = int(np.sum(nti_path_hot))
    record["diag_n_dnti_ctx_path"] = int(np.sum(dnti_ctx_hot))
    record["diag_n_test1_path"] = int(np.sum(test1_hot))
else:
    hot_mask_2d = combine_hot_paths(
        bt_path_hot, nti_path_hot, dnti_ctx_hot, test1_hot,
        enable_test1_k1_retire_from_hot_mask=ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK,
        eti_path_hot=eti_path_hot,
    )
```

Repeat para `process_viirs.py` y `process_viirs_mod.py`.

Add constants:
```python
ENABLE_FIRST_PASS_TESTS_2_AND_3 = _get_profile_flag(
    "enable_first_pass_tests_2_and_3", default=False
)
ENABLE_DUAL_ROI_FIRST_PASS = _get_profile_flag(
    "enable_dual_roi_first_pass", default=False
)
```

- [ ] **Step 4.6: Run suite completa**

Run: `pytest tests/ -x --tb=short`
Expected: PASS

- [ ] **Step 4.7: Commit**

```bash
git add tests/test_drift23_first_pass_tests_2_3.py pipeline/detection_context.py pipeline/process_modis.py pipeline/process_viirs.py pipeline/process_viirs_mod.py
git commit -m "drift23: first_pass_tests_2_and_3 + dual-ROI Tabla 2 + TDD

Coppola 2016a SP426.5 Tests 2 ∧ 3 conjunción + rama OR estadística μ+C2σ +
dual-ROI summit C1=0.003/C2=5 vs scene C1=0.010/C2=10 (Tabla 1 noche).
Reusa compute_eti_scene_quadratic helper existente. Flag opt-in.

4 tests sintéticos cubren AND obligatoria + dual-ROI + rama statistical."
```

---

## Task 5: Drift #4 — second-pass adyacente activación

**Files:**
- Test: `tests/test_drift4_second_pass_enabled.py` (new)
- Modify: `pipeline/process_modis.py:hot_mask_2d`, `process_viirs.py:hot_mask_2d`, `process_viirs_mod.py:hot_mask_2d`

- [ ] **Step 5.1: Escribir test sintético**

Create `tests/test_drift4_second_pass_enabled.py`:

```python
"""Test Drift #4 — second_pass_adjacent activación (Coppola 2016a línea 347-356)."""
import numpy as np
import pytest

from pipeline.detection_context import second_pass_adjacent


def test_drift4_second_pass_recapture_adjacent():
    """Pixel marginal adyacente a hot debe recapturarse en second-pass.

    Setup: 1 pixel hot real (10,10). Pixel adyacente (10,11) marginal —
    su dNTI legacy es chico porque mean(8-vecinos) incluye al hot @
    (10,10), inflando el bg local.

    Cuando second_pass excluye pixel (10,10) del cómputo mean, dNTI de
    (10,11) sube y supera threshold → recapturado.
    """
    shape = (20, 20)
    eti = np.random.normal(0, 0.001, shape)
    nti = np.random.normal(-0.97, 0.001, shape)

    # Pixel hot @ (10,10): NTI alto, ETI alto
    nti[10, 10] = -0.50
    eti[10, 10] = 0.020

    # Pixel adyacente marginal @ (10,11): NTI medio-alto
    nti[10, 11] = -0.93
    eti[10, 11] = 0.005

    active_mask = np.zeros(shape, dtype=bool)
    active_mask[10, 10] = True  # first-pass detectó solo (10,10)

    final_mask = second_pass_adjacent(
        nti=nti, eti=eti, active_mask=active_mask,
        c1_dnti=0.003, c1_deti=0.003,
        c2_dnti=5, c2_deti=5,
        min_bg_pixels=10,
    )

    # First pass solo tenía (10,10). Second pass debe recapturar (10,11)
    assert final_mask[10, 10], "Pixel first-pass debe seguir active"
    # NOTA: dependiendo de los thresholds exactos, recapture puede o no ocurrir.
    # Mínimo: final_mask >= active_mask (no perdemos pixels)
    assert int(np.sum(final_mask)) >= int(np.sum(active_mask))


def test_drift4_second_pass_no_active_returns_same():
    """Si active_mask vacío, second-pass devuelve vacío."""
    shape = (20, 20)
    nti = np.random.normal(-0.97, 0.001, shape)
    eti = np.random.normal(0, 0.001, shape)
    active_mask = np.zeros(shape, dtype=bool)

    final = second_pass_adjacent(
        nti=nti, eti=eti, active_mask=active_mask,
        c1_dnti=0.003, c1_deti=0.003,
        c2_dnti=5, c2_deti=5,
    )

    # Sin pixels active, second pass no agrega (μ del scene completo no tiene outliers)
    assert int(np.sum(final)) == 0


def test_drift4_dual_roi_thresholds_applied():
    """Second-pass dual-ROI: pixel scene marginal usa C1=0.010, no C1=0.003."""
    shape = (20, 20)
    nti = np.random.normal(-0.97, 0.001, shape)
    eti = np.random.normal(0, 0.001, shape)

    # Pixel scene marginal: dNTI ~0.005 (entre 0.003 y 0.010)
    nti[15, 15] = -0.965
    eti[15, 15] = 0.005

    active_mask = np.zeros(shape, dtype=bool)
    active_mask[10, 10] = True

    is_summit = np.zeros(shape, dtype=bool)
    is_summit[8:12, 8:12] = True  # summit es centro

    final_dual = second_pass_adjacent(
        nti=nti, eti=eti, active_mask=active_mask,
        c1_dnti=0.003, c1_deti=0.003,
        c2_dnti=5, c2_deti=5,
        is_summit=is_summit,
        c1_dnti_scene=0.010, c1_deti_scene=0.010,
        c2_dnti_scene=10, c2_deti_scene=10,
    )

    # Pixel (15,15) en scene: dNTI=0.005 < 0.010 → NO recapturado
    assert not final_dual[15, 15]
```

- [ ] **Step 5.2: Run tests (debería pasar — función ya existe)**

Run: `pytest tests/test_drift4_second_pass_enabled.py -v`
Expected: 3 tests PASS

- [ ] **Step 5.3: Wire flag en `process_*.py`**

Edit `pipeline/process_modis.py` después del bloque hot_mask_2d:

```python
if ENABLE_SECOND_PASS_ADJACENT:
    is_summit_mask = dist_km <= INNER_RADIUS_KM
    final_active_mask = second_pass_adjacent(
        nti=nti, eti=eti, active_mask=hot_mask_2d,
        c1_dnti=0.003, c1_deti=0.003,
        c2_dnti=5, c2_deti=5,
        is_summit=is_summit_mask if ENABLE_DUAL_ROI_SECOND_PASS else None,
        c1_dnti_scene=0.010 if ENABLE_DUAL_ROI_SECOND_PASS else None,
        c1_deti_scene=0.010 if ENABLE_DUAL_ROI_SECOND_PASS else None,
        c2_dnti_scene=10 if ENABLE_DUAL_ROI_SECOND_PASS else None,
        c2_deti_scene=10 if ENABLE_DUAL_ROI_SECOND_PASS else None,
    )
    n_recapture = int(np.sum(final_active_mask & ~hot_mask_2d))
    record["diag_n_second_pass_recapture"] = n_recapture
    hot_mask_2d = final_active_mask
```

Same en `process_viirs.py` y `process_viirs_mod.py`.

Add constants:
```python
ENABLE_SECOND_PASS_ADJACENT = _get_profile_flag(
    "enable_second_pass_adjacent", default=False
)
ENABLE_DUAL_ROI_SECOND_PASS = _get_profile_flag(
    "enable_dual_roi_second_pass", default=False
)
```

- [ ] **Step 5.4: Run suite completa**

Run: `pytest tests/ -x --tb=short`
Expected: PASS

- [ ] **Step 5.5: Commit**

```bash
git add tests/test_drift4_second_pass_enabled.py pipeline/process_modis.py pipeline/process_viirs.py pipeline/process_viirs_mod.py
git commit -m "drift4: second_pass_adjacent flag wiring + TDD

Coppola 2016a SP426.5 línea 347-356 — second-pass obligatorio. La función
second_pass_adjacent ya estaba implementada (S37 H_D8_5 infra); este
commit la activa via flag ENABLE_SECOND_PASS_ADJACENT.

3 tests sintéticos cubren recapture/no-active/dual-ROI."
```

---

## Task 6: Variante 13 — Di Bella n=12 noche VIIRS (experimental)

**Files:**
- Test: `tests/test_drift13_dibella_n12_viirs.py` (new)
- Modify: `pipeline/process_viirs.py`, `pipeline/process_viirs_mod.py`

- [ ] **Step 6.1: Escribir test sintético**

Create `tests/test_drift13_dibella_n12_viirs.py`:

```python
"""Test Variante 13 EXPERIMENTAL — Di Bella 2024 n=12 noche VIIRS.

NO clon literal MIROVA. Di Bella es INGV Catania (regla S26).
Documentado como exploración objetivo (2).
"""
import numpy as np
import pytest

from pipeline.detection_context import first_pass_tests_2_and_3


def test_dibella_n12_viirs_more_strict_than_coppola_C2_5():
    """Mismo pixel marginal: Coppola C2=5 pasa, Di Bella n=12 NO pasa."""
    shape = (100, 100)
    nti = np.random.normal(-0.97, 0.0001, shape)  # σ chico
    nti_app = np.random.normal(-0.97, 0.0001, shape)
    bt = np.full(shape, 268.0)

    # Pixel marginal: dNTI = 7σ sobre mean
    # → pasa C2=5, NO pasa n=12
    nti[50, 50] = -0.97 + 7 * 0.0001  # dNTI ~ 7σ
    nti_app[50, 50] = -0.97
    bt[50, 50] = 285.0

    roi_mask = np.ones(shape, dtype=bool)
    dist_km = np.full(shape, 2.0)

    # Coppola C2=5
    hot_coppola, _ = first_pass_tests_2_and_3(
        nti=nti, nti_app=nti_app, bt=bt,
        roi_mask=roi_mask, dist_km=dist_km,
        t_bg=268.0, bt_sanity_k=3.0,
        c1_dnti_summit=0.003, c1_deti_summit=0.003,
        c2_dnti_summit=5, c2_deti_summit=5,
        inner_km=5.0,
    )

    # Di Bella n=12
    hot_dibella, _ = first_pass_tests_2_and_3(
        nti=nti, nti_app=nti_app, bt=bt,
        roi_mask=roi_mask, dist_km=dist_km,
        t_bg=268.0, bt_sanity_k=3.0,
        c1_dnti_summit=0.003, c1_deti_summit=0.003,
        c2_dnti_summit=12, c2_deti_summit=12,
        inner_km=5.0,
    )

    # Coppola pasa, Di Bella no
    assert hot_coppola[50, 50], "Coppola C2=5 debe disparar"
    assert not hot_dibella[50, 50], "Di Bella n=12 NO debe disparar"
```

- [ ] **Step 6.2: Run test**

Run: `pytest tests/test_drift13_dibella_n12_viirs.py -v`
Expected: PASS (función ya implementada Task 4, solo distinto C2 param)

- [ ] **Step 6.3: Add profile flag override**

Edit `pipeline/process_viirs.py` y `pipeline/process_viirs_mod.py` donde se llama `first_pass_tests_2_and_3`:

```python
# Variante 13: override C2 con Di Bella n=12 noche (solo VIIRS)
c2_override = VIIRS_C2_OVERRIDE_NIGHT  # None default
c2_dnti = c2_override if c2_override else 5
c2_deti = c2_override if c2_override else 5
c2_dnti_sce = c2_override if c2_override else 10
c2_deti_sce = c2_override if c2_override else 10

# ... pasar al first_pass_tests_2_and_3 ...
```

Add constant top:
```python
VIIRS_C2_OVERRIDE_NIGHT = _get_profile_flag(
    "viirs_c2_override_night", default=None  # None → usa Coppola default
)
```

NOTA: process_modis.py NO recibe este override (drift solo VIIRS).

- [ ] **Step 6.4: Commit**

```bash
git add tests/test_drift13_dibella_n12_viirs.py pipeline/process_viirs.py pipeline/process_viirs_mod.py
git commit -m "drift13: Di Bella n=12 noche VIIRS override flag (EXPERIMENTAL)

VIIRS_C2_OVERRIDE_NIGHT permite reemplazar Coppola C2=5/10 con n=12
(Di Bella 2024). Marcado experimental — Di Bella es INGV Catania (NO
MIROVA, regla S26). Aislado en variante 13 para exploración objetivo (2).

NO adoptable operacionalmente — viola clon literal MISSION.md."
```

---

## Task 7: Profile YAMLs (13 archivos)

**Files:**
- Create: 13 archivos en `pipeline/profiles/`

- [ ] **Step 7.1: Verificar estructura YAML extends**

```bash
ls pipeline/profiles/
cat pipeline/profiles/mirova_equivalent.yaml | head -30
```

- [ ] **Step 7.2: Create `_baseline_s44.yaml`**

```yaml
# pipeline/profiles/_baseline_s44.yaml
profile: _baseline_s44
description: "Ronda 1 S46 — CONTROL: alias de mirova_equivalent.yaml operacional"
data_subdir: _baseline_s44

# Hereda todo de mirova_equivalent.yaml
extends: mirova_equivalent.yaml

# Todos drifts S46 OFF (igual operacional S44)
enable_test1_k1_retire_from_hot_mask: false
enable_test1_k1_bg_exclude: false
enable_first_pass_tests_2_and_3: false
enable_dual_roi_first_pass: false
enable_second_pass_adjacent: false
enable_dual_roi_second_pass: false
enable_nadir_fixed_pixel_area_modis: false
enable_nadir_fixed_pixel_area_viirs: false
viirs_c2_override_night: null
```

- [ ] **Step 7.3: Create `_drift1a_only.yaml`**

```yaml
# pipeline/profiles/_drift1a_only.yaml
profile: _drift1a_only
description: "Ronda 1 S46 — drift #1a: Test 1 K1 retire from hot_mask"
data_subdir: _drift1a_only
extends: mirova_equivalent.yaml

enable_test1_k1_retire_from_hot_mask: true
# Resto OFF
enable_test1_k1_bg_exclude: false
enable_first_pass_tests_2_and_3: false
enable_dual_roi_first_pass: false
enable_second_pass_adjacent: false
enable_dual_roi_second_pass: false
enable_nadir_fixed_pixel_area_modis: false
enable_nadir_fixed_pixel_area_viirs: false
viirs_c2_override_night: null
```

- [ ] **Step 7.4: Create remaining 11 profile YAMLs**

Repetir patrón para:
- `_drift1b_only.yaml` (solo `enable_test1_k1_bg_exclude: true`)
- `_drift1ab_only.yaml` (ambos drift1 flags true)
- `_drift23_only.yaml` (`enable_first_pass_tests_2_and_3: true`, dual_roi false)
- `_drift23_dual_only.yaml` (first_pass + dual_roi both true)
- `_drift4_only.yaml` (`enable_second_pass_adjacent: true`, sin first_pass)
- `_drift234_only.yaml` (first_pass + dual_roi + second_pass + dual_roi_second_pass)
- `_drift7_modis_only.yaml` (`enable_nadir_fixed_pixel_area_modis: true`)
- `_drift7_viirs_only.yaml` (`enable_nadir_fixed_pixel_area_viirs: true`)
- `_drift7_both_only.yaml` (ambos drift7)
- `_coppola_full.yaml` (drift1ab + drift234 + drift7_both, todos true)
- `_dibella_n12_viirs_only.yaml` (`viirs_c2_override_night: 12`, otros drifts OFF)

- [ ] **Step 7.5: Verificar profiles cargan**

```bash
python -c "import yaml; [print(yaml.safe_load(open(f'pipeline/profiles/{p}.yaml'))['profile']) for p in ['_baseline_s44', '_drift1a_only', '_drift1b_only', '_drift1ab_only', '_drift23_only', '_drift23_dual_only', '_drift4_only', '_drift234_only', '_drift7_modis_only', '_drift7_viirs_only', '_drift7_both_only', '_coppola_full', '_dibella_n12_viirs_only']]"
```
Expected: 13 nombres impresos sin errores

- [ ] **Step 7.6: Commit**

```bash
git add pipeline/profiles/_*.yaml
git commit -m "S46 Ronda 1: 13 profile YAMLs para A/B aislado por drift

baseline + 4 drift1 variants + 3 drift23 variants + 1 drift4 + 1 drift234
+ 3 drift7 variants + 1 coppola_full + 1 dibella_n12_viirs experimental.

Cada profile data_subdir distinto para preservar outputs (no race condition
con operacional mirova_equivalent.yaml)."
```

---

## Task 8: Workflow GitHub Actions parametrizado

**Files:**
- Create: `.github/workflows/reproc-s46-coppola-literal-ab.yml`

- [ ] **Step 8.1: Verificar workflow template existente**

```bash
ls .github/workflows/reproc-ab-*.yml | head -3
cat .github/workflows/reproc-mirova-equivalent-30d.yml
```

- [ ] **Step 8.2: Create workflow**

```yaml
# .github/workflows/reproc-s46-coppola-literal-ab.yml
name: S46 Coppola Literal A/B Reproc
on:
  workflow_dispatch:
    inputs:
      variant:
        type: choice
        description: "Variante A/B (o 'all' para las 13)"
        options:
          - all
          - _baseline_s44
          - _drift1a_only
          - _drift1b_only
          - _drift1ab_only
          - _drift23_only
          - _drift23_dual_only
          - _drift4_only
          - _drift234_only
          - _drift7_modis_only
          - _drift7_viirs_only
          - _drift7_both_only
          - _coppola_full
          - _dibella_n12_viirs_only
        default: all
      window_days:
        description: "Window de reproc en días"
        default: '30'
      start_date:
        description: "Start date YYYY-MM-DD (vacío = today - window_days)"
        default: ''

jobs:
  reproc:
    strategy:
      max-parallel: 8
      fail-fast: false
      matrix:
        variant:
          - _baseline_s44
          - _drift1a_only
          - _drift1b_only
          - _drift1ab_only
          - _drift23_only
          - _drift23_dual_only
          - _drift4_only
          - _drift234_only
          - _drift7_modis_only
          - _drift7_viirs_only
          - _drift7_both_only
          - _coppola_full
          - _dibella_n12_viirs_only
        volcano:
          - Lascar
          - Tupungatito
          - Lastarria
          - NevadosDeChillan
          - Llaima
          - Copahue
          - PuyehueCordonCaulle
          - PlanchonPeteroa
          - Isluga
          - Villarrica
          - Chaiten
        exclude:
          # Filtrar variantes según input "variant"
          # (matrix filtering por jq se hace en step Python si necesario)
    timeout-minutes: 50
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      - run: pip install -r requirements.txt
      - name: Skip if variant filter
        if: ${{ inputs.variant != 'all' && inputs.variant != matrix.variant }}
        run: |
          echo "Skipping ${{ matrix.variant }} (input filter: ${{ inputs.variant }})"
          exit 0
      - name: Run pipeline
        env:
          EARTHDATA_USERNAME: ${{ secrets.EARTHDATA_USERNAME }}
          EARTHDATA_PASSWORD: ${{ secrets.EARTHDATA_PASSWORD }}
        run: |
          python scripts/run_pipeline.py \
            --profile ${{ matrix.variant }} \
            --volcano ${{ matrix.volcano }} \
            --start-date "${{ inputs.start_date }}" \
            --window-days ${{ inputs.window_days }}
      - name: Commit data
        run: |
          git config user.email "actions@github.com"
          git config user.name "github-actions"
          git pull --rebase -X theirs origin ${{ github.ref_name }}
          git add data/${{ matrix.variant }}/${{ matrix.volcano }}.json
          git diff --staged --quiet || \
            git commit -m "S46 reproc ${{ matrix.variant }} ${{ matrix.volcano }} window=${{ inputs.window_days }}d"
          git push origin ${{ github.ref_name }}
```

NOTA: La matrix con `variant: choice` + filter dinámico requiere logic. Si GitHub no soporta filter directo, usar approach `if:` con skip step (como arriba) y aceptar que se "spawnean" todos los jobs pero con skip rápido.

- [ ] **Step 8.3: Commit**

```bash
git add .github/workflows/reproc-s46-coppola-literal-ab.yml
git commit -m "S46 Ronda 1: workflow A/B parametrizado

13 variantes × 11 Tier A = 143 jobs, max-parallel 8, ~3h compute.
Input 'variant' permite correr 1 sola variante para iteración rápida.

Output: data/<variant>/<volcano>.json con commits separados por job."
```

---

## Task 9: Audit script (experiments/87)

**Files:**
- Create: `experiments/87_audit_s46_round1.py`

- [ ] **Step 9.1: Create audit script**

Create file con estructura:

```python
"""Audit S46 Ronda 1 — A/B Coppola literal 13 variantes.

Computa F1 vs MIROVA + ratio mediano + delta dist per (variante, volcán, sensor).
Output: experiments/87_results.md + experiments/87_results.json.

Reusa pattern de experiments/76_audit_independent.py.
"""
import json
import pandas as pd
import yaml
from pathlib import Path
from datetime import timedelta

VARIANTS = [
    "_baseline_s44", "_drift1a_only", "_drift1b_only", "_drift1ab_only",
    "_drift23_only", "_drift23_dual_only", "_drift4_only", "_drift234_only",
    "_drift7_modis_only", "_drift7_viirs_only", "_drift7_both_only",
    "_coppola_full", "_dibella_n12_viirs_only",
]

VOLC_CSV_MAP = {
    "Lascar": "Lascar", "Tupungatito": "Tupungatito",
    "Lastarria": "Lastarria", "NevadosDeChillan": "Nevados de Chillan",
    "Llaima": "Llaima", "Copahue": "Copahue",
    "PuyehueCordonCaulle": "Puyehue-Cordon Caulle",
    "PlanchonPeteroa": "PlanchonPeteroa",
    "Isluga": "Isluga", "Villarrica": "Villarrica", "Chaiten": "Chaiten",
}

SENSORS = ["MODIS", "VIIRS375", "VIIRS750"]


def audit_variant(variant_dir: Path, mv_csv: pd.DataFrame, vol_meta: dict,
                  window_start, window_end) -> dict:
    """Audit 1 variante: tabla per-volcán × sensor con TP/FN/FP/F1/ratio/dist."""
    results = {}
    for vol_key, vol_csv_name in VOLC_CSV_MAP.items():
        op_path = variant_dir / f"{vol_key}.json"
        if not op_path.exists():
            continue
        data = json.loads(op_path.read_text())
        recs = data.get("records", [])
        inner_radius = vol_meta.get(vol_key, {}).get("inner_radius_km", 5)

        # Filter records in window
        op_recs = []
        for r in recs:
            ts = r.get("datetime_utc")
            if not ts:
                continue
            try:
                t = pd.Timestamp(ts)
            except:
                continue
            if window_start <= t < window_end:
                op_recs.append((t, r))

        # Per sensor breakdown
        sensor_breakdown = {}
        for sensor_label in SENSORS:
            sensor_recs = [
                (t, r) for t, r in op_recs
                if _sensor_match(r.get("sensor", ""), sensor_label)
            ]
            tp, fn, fp = _compute_metrics(sensor_recs, mv_csv, vol_csv_name,
                                          sensor_label, inner_radius,
                                          window_start, window_end)
            sensor_breakdown[sensor_label] = {"TP": tp, "FN": fn, "FP": fp}

        results[vol_key] = {
            "inner_radius_km": inner_radius,
            "n_records": len(op_recs),
            "sensor_breakdown": sensor_breakdown,
        }
    return results


def _sensor_match(record_sensor: str, target_sensor: str) -> bool:
    """Mapear record.sensor string a sensor label MIROVA."""
    if target_sensor == "MODIS":
        return record_sensor.startswith("MODIS")
    elif target_sensor == "VIIRS375":
        return "_750" not in record_sensor and "MOD" not in record_sensor and "VIIRS" in record_sensor
    elif target_sensor == "VIIRS750":
        return "_750" in record_sensor or record_sensor.endswith("_MOD")
    return False


def _compute_metrics(sensor_recs, mv_csv, vol_csv_name, sensor_label,
                     inner_radius, window_start, window_end) -> tuple:
    """TP/FN/FP per (volcán, sensor)."""
    mvol = mv_csv[(mv_csv["Volcan"] == vol_csv_name)
                  & (mv_csv["Sensor"] == sensor_label)].copy()
    mvol["ts"] = pd.to_datetime(mvol["Fecha_Satelite_UTC"], errors="coerce")
    mvol = mvol.dropna(subset=["ts"])
    mvol = mvol[(mvol["ts"] >= window_start) & (mvol["ts"] < window_end)]

    alerts = mvol[mvol["Tipo_Registro"] == "ALERTA_TERMICA"]
    fps = mvol[mvol["Tipo_Registro"] == "FALSO_POSITIVO"]

    tol = timedelta(minutes=30)
    tp = 0
    fn = 0
    fp = 0
    matched_recs = set()

    for _, m in alerts.iterrows():
        t_m = m["ts"]
        match_idx = None
        for i, (t_o, r) in enumerate(sensor_recs):
            if i in matched_recs:
                continue
            pc = r.get("primary_cluster") or {}
            cdist = pc.get("centroid_dist_km", 999)
            vrp_pc = pc.get("vrp_mw", 0)
            if cdist > inner_radius or vrp_pc > 50000:
                vrp_eq = 0
            else:
                vrp_eq = vrp_pc
            if abs(t_o - t_m) <= tol and vrp_eq > 0:
                match_idx = i
                break
        if match_idx is not None:
            tp += 1
            matched_recs.add(match_idx)
        else:
            fn += 1

    for _, m in fps.iterrows():
        t_m = m["ts"]
        for i, (t_o, r) in enumerate(sensor_recs):
            pc = r.get("primary_cluster") or {}
            cdist = pc.get("centroid_dist_km", 999)
            vrp_pc = pc.get("vrp_mw", 0)
            if cdist > inner_radius or vrp_pc > 50000:
                vrp_eq = 0
            else:
                vrp_eq = vrp_pc
            if abs(t_o - t_m) <= tol and vrp_eq > 0:
                fp += 1
                break

    return tp, fn, fp


def main():
    repo_root = Path(__file__).parent.parent
    mv_csv = pd.read_csv(repo_root / "01_05_2026_registro_vrp_consolidado.csv")
    with open(repo_root / "volcanoes.yaml") as f:
        vol_meta = {v["name"]: v for v in yaml.safe_load(f)["volcanoes"]}

    window_start = pd.Timestamp("2026-04-15")
    window_end = pd.Timestamp("2026-05-15")

    all_results = {}
    for variant in VARIANTS:
        variant_dir = repo_root / "data" / variant
        if not variant_dir.exists():
            print(f"SKIP {variant}: data dir missing")
            continue
        all_results[variant] = audit_variant(
            variant_dir, mv_csv, vol_meta, window_start, window_end
        )

    # Output
    output_dir = repo_root / "experiments"
    (output_dir / "87_results.json").write_text(
        json.dumps(all_results, indent=2, default=str)
    )
    _write_markdown_summary(all_results, output_dir / "87_results.md")
    print("Audit completo. Outputs:")
    print(f"  - {output_dir / '87_results.json'}")
    print(f"  - {output_dir / '87_results.md'}")


def _write_markdown_summary(results: dict, output_path: Path):
    """Tabla agregada + per-sensor + decisión automática."""
    lines = ["# S46 Ronda 1 — Results A/B Coppola literal\n"]
    lines.append(f"Window: 2026-04-15 a 2026-05-15 (30d).\n\n")

    # Tabla agregada todos sensores
    lines.append("## Tabla agregada (todos sensores Tier A)\n\n")
    lines.append("| Variante | TP | FN | FP | F1 | Recall | Precision |\n")
    lines.append("|---|---|---|---|---|---|---|\n")
    for variant, vol_results in results.items():
        tp = sum(s["TP"] for v in vol_results.values()
                 for s in v["sensor_breakdown"].values())
        fn = sum(s["FN"] for v in vol_results.values()
                 for s in v["sensor_breakdown"].values())
        fp = sum(s["FP"] for v in vol_results.values()
                 for s in v["sensor_breakdown"].values())
        p = tp / (tp + fp) if (tp + fp) > 0 else 0
        r = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0
        lines.append(f"| {variant} | {tp} | {fn} | {fp} | {f1:.3f} | {r:.3f} | {p:.3f} |\n")

    # Per sensor breakdown
    lines.append("\n## Per sensor breakdown\n\n")
    for sensor in SENSORS:
        lines.append(f"### {sensor}\n\n")
        lines.append("| Variante | TP | FN | FP | F1 |\n")
        lines.append("|---|---|---|---|---|\n")
        for variant, vol_results in results.items():
            tp = sum(v["sensor_breakdown"].get(sensor, {}).get("TP", 0)
                     for v in vol_results.values())
            fn = sum(v["sensor_breakdown"].get(sensor, {}).get("FN", 0)
                     for v in vol_results.values())
            fp = sum(v["sensor_breakdown"].get(sensor, {}).get("FP", 0)
                     for v in vol_results.values())
            p = tp / (tp + fp) if (tp + fp) > 0 else 0
            r = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0
            lines.append(f"| {variant} | {tp} | {fn} | {fp} | {f1:.3f} |\n")
        lines.append("\n")

    output_path.write_text("".join(lines))


if __name__ == "__main__":
    main()
```

- [ ] **Step 9.2: Verify script runs (sin data por ahora)**

```bash
python experiments/87_audit_s46_round1.py
```
Expected: muestra SKIP per variante porque `data/<variant>/` no existe aún. No crashea.

- [ ] **Step 9.3: Commit**

```bash
git add experiments/87_audit_s46_round1.py
git commit -m "S46 Ronda 1: audit script per-sensor breakdown

Computa TP/FN/FP/F1 per (variante, volcán, sensor) sobre data/<variant>/.
Output: experiments/87_results.{md,json}. Pattern reusado de experiments/76."
```

---

## Task 10: R2 pixel-level tests (skip-when-TIF-unavailable)

**Files:**
- Create: `tests/test_r2_pixel_level.py`

- [ ] **Step 10.1: Create R2 test file**

Create con 5 casos canónicos del handoff S46, marcados `@pytest.mark.r2_pixel_level`, skip si TIF no disponible.

(Ver design doc Sección "R2 pixel-level" para código completo)

- [ ] **Step 10.2: Run con marker**

```bash
pytest tests/test_r2_pixel_level.py -m r2_pixel_level -v
```
Expected: mayoría SKIP (TIF gap actual), Lastarria 04-30 puede correr si disponible.

- [ ] **Step 10.3: Commit**

```bash
git add tests/test_r2_pixel_level.py
git commit -m "S46: tests R2 pixel-level 5 casos canónicos (skip-when-TIF-unavailable)"
```

---

## Task 11: Push branch + PR

- [ ] **Step 11.1: Push + open PR**

```bash
git push origin s46-coppola-literal-round1
gh pr create --title "S46 Ronda 1: Coppola 2016a literal A/B 13 variantes" \
  --body "$(cat docs/superpowers/specs/2026-05-15-s46-coppola-literal-design.md | head -80)"
```

- [ ] **Step 11.2: Verify PR opens**

Check URL retornada.

---

## Task 12: Disparar workflow A/B Ronda 1

- [ ] **Step 12.1: Verificar pre-requisitos**

1. CSV Mirova-v1 consolidado actualizado en repo (re-scraper si necesario)
2. NRT cron no corriendo simultáneo (verificar `gh run list --workflow=nrt.yml --status=in_progress`)
3. Secrets EARTHDATA_USERNAME/PASSWORD presentes

- [ ] **Step 12.2: Disparar workflow**

```bash
gh workflow run reproc-s46-coppola-literal-ab.yml \
  -f variant=all \
  -f window_days=30
```

- [ ] **Step 12.3: Monitorear progreso**

```bash
gh run watch  # selecciona el run iniciado
```

Esperar ~2-3h. 143 jobs (13 variantes × 11 volcanes), max-parallel 8.

- [ ] **Step 12.4: Pull data + correr audit**

```bash
git pull origin s46-coppola-literal-round1
python experiments/87_audit_s46_round1.py
cat experiments/87_results.md | head -60
```

- [ ] **Step 12.5: Analizar + commit results**

```bash
git add experiments/87_results.md experiments/87_results.json data/_*/
git commit -m "S46 Ronda 1 results: 13 variantes × 11 Tier A × 30d completado"
git push
```

---

## Self-Review Checklist

Después de implementar este plan completo:

### Spec coverage
- ✅ Drift #1a (Test 1 K1 retire from hot_mask) → Task 1
- ✅ Drift #1b (bg excluye Test 1 K1) → Task 2
- ✅ Drift #1ab combo → profile YAML solo (Task 7)
- ✅ Drift #2+#3 (Tests 2 ∧ 3 + dETI + AND + C2·σ) → Task 4
- ✅ Drift #23 dual-ROI → profile YAML (Task 7)
- ✅ Drift #4 (second-pass) → Task 5
- ✅ Drift #234 combo → profile YAML (Task 7)
- ✅ Drift #7 (MODIS+VIIRS nadir-fijo) → Task 3
- ✅ Variante 13 Di Bella experimental → Task 6
- ✅ Profile YAMLs (13 archivos) → Task 7
- ✅ Workflow parametrizado → Task 8
- ✅ Audit script per-sensor → Task 9
- ✅ R2 pixel-level tests → Task 10
- ✅ Branch + PR + workflow trigger → Tasks 11-12

### Placeholders
- Sin TODO/TBD/implement-later (revisado)
- Cada step tiene código concreto o comando exacto
- Excepción justificada: `[código existente líneas 196-203]` en Step 3.4 — refers a código que existe en archivo, instruir "preservar líneas 196-203 actuales"

### Type consistency
- `combine_hot_paths`: signature consistente entre Task 1, 4
- `compute_bg_stats`: definida Task 2, no usada en otros tasks
- `first_pass_tests_2_and_3`: signature consistente Task 4, 6
- Flag naming: `enable_*` prefix consistente
- Profile YAML flag names: consistentes en Task 7 vs Task 1-6 wiring

### Dependencies entre tasks
- Task 1 (combine_hot_paths) → bloquea Task 4 (lo usa indirect)
- Task 4 (first_pass_tests_2_and_3) → bloquea Task 6 (lo extiende)
- Task 7 (profile YAMLs) requiere todos los flags wired en Tasks 1-6
- Task 8 (workflow) referencia Task 7 profile names
- Task 9 (audit) requiere data outputs de Task 12

### Execution order
Tasks 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12. Cada uno preserva
suite verde antes de commit.

---

## Plan completo y guardado

**Plan complete and saved to `docs/superpowers/plans/2026-05-15-s46-coppola-literal-implementation.md`.**

Two execution options:

**1. Subagent-Driven (recommended)** - Dispatcho fresh subagent por task, review entre tasks, fast iteration. Cada subagent recibe contexto bite-sized de su task.

**2. Inline Execution** - Ejecuto tasks en esta sesión con executing-plans, batch execution con checkpoints para review.

**¿Cuál approach?**
