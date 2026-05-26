# NTI Relative Path (Path C) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a third detection path ("Path C — NTI relative") to the VIIRS processors that detects pixels where `nti > nti_bg + max(0.005, 3*sigma_nti)`, gated behind a profile flag `enable_nti_relative_path`. This targets weak fumarolic signals (0.05-0.3 MW) at PlanchonPeteroa, Villarrica, and similar volcanoes where Path A (BT) and Path B (NTI absolute) both fail.

**Architecture:** The NTI relative threshold (`nti_bg + max(0.005, 3*sigma_nti)`) is already computed in `process_viirs.py` (line 255) for diagnostic counting (`n_nti_anomalous`). Path C promotes this from a diagnostic counter to an actual detection criterion, OR-ed with Paths A and B. A BT sanity check (`bt > t_bg + NTI_BT_SANITY_K`) prevents cold-pixel false triggers. The flag lives in the profile YAML so it can be enabled in `experimental` only — `mirova_equivalent` stays untouched.

**Tech Stack:** Python 3.11, numpy, pyyaml. No new dependencies.

**Scientific basis:** Coppola 2015 Eq.2-4 defines NTI = (L_MIR - L_TIR)/(L_MIR + L_TIR) and uses dNTI (pixel NTI vs background NTI) as the primary MIROVA detection criterion. Our Path B uses an absolute NTI floor (-0.8), which is unreachable for weak signals (PP NTI values are -0.93 to -0.95). Path C uses the relative criterion that MIROVA actually uses.

**Risk:** Opening a more sensitive path increases FP exposure. Mitigations:
1. BT sanity floor prevents cold-pixel false triggers
2. Only enabled in `experimental` profile initially
3. Output records include `n_nti_rel_path` counter for post-hoc audit
4. Re-audit with `experiments/11_strict_audit.py` before any promotion to operational

---

### File map

| File | Action | Responsibility |
|------|--------|----------------|
| `pipeline/profiles/experimental.yaml` | Modify | Add `enable_nti_relative_path: true` |
| `pipeline/profiles/mirova_equivalent.yaml` | Modify | Add `enable_nti_relative_path: false` |
| `pipeline/profile.py` | Modify | Export new `ENABLE_NTI_RELATIVE_PATH` constant |
| `pipeline/process_viirs.py` | Modify | Add Path C logic, OR into `hot_mask_2d`, add counter |
| `pipeline/process_viirs_mod.py` | Modify | Add `nti_std` computation, add Path C logic, add counter |
| `tests/test_nti_relative_path.py` | Create | Unit tests for Path C detection logic |

---

### Task 1: Add profile flag

**Files:**
- Modify: `pipeline/profiles/experimental.yaml:35-41`
- Modify: `pipeline/profiles/mirova_equivalent.yaml` (paths section)
- Modify: `pipeline/profile.py:72-77`

- [ ] **Step 1: Add flag to experimental.yaml**

In `pipeline/profiles/experimental.yaml`, add to the `paths:` section:

```yaml
paths:
  enable_eruption_path: true
  enable_vent_path: true
  enable_vent_path_modis: true
  # Session 11: NTI relative path (Path C) for weak fumarolic signals.
  # Uses nti > nti_bg + max(0.005, 3*sigma_nti) instead of absolute NTI floor.
  # Targets PP (recall 0.54) and Villarrica (recall 0/6). See plan_s11.
  enable_nti_relative_path: true
```

- [ ] **Step 2: Add flag (disabled) to mirova_equivalent.yaml**

In `pipeline/profiles/mirova_equivalent.yaml`, add to the `paths:` section:

```yaml
paths:
  enable_eruption_path: true
  enable_vent_path: true
  enable_vent_path_modis: false
  # NTI relative path disabled in operational profile until validated.
  enable_nti_relative_path: false
```

- [ ] **Step 3: Export flag in profile.py**

In `pipeline/profile.py`, after line 77 (`ENABLE_VENT_PATH_MODIS`), add:

```python
# Session 11: NTI-relative detection path (Path C) for weak fumarolic signals.
# When True, pixels passing nti > nti_bg + max(0.005, 3*sigma_nti) AND
# bt > t_bg + NTI_BT_SANITY_K are included in hot_mask_2d.
ENABLE_NTI_RELATIVE_PATH: bool = bool(_p.get("enable_nti_relative_path", False))
```

Also add it to the `describe()` function string:

```python
def describe() -> str:
    return (
        f"[VRP profile={PROFILE_NAME}] "
        f"anomaly_K={ANOMALY_THRESHOLD_K} "
        f"nsigma_mir={N_SIGMA_MIR} "
        f"vent_K={VENT_THRESHOLD_K} "
        f"nti_k1={NTI_K1_NIGHT} "
        f"nti_rel={'on' if ENABLE_NTI_RELATIVE_PATH else 'off'} "
        f"vent_path={'on' if ENABLE_VENT_PATH else 'off'} "
        f"sensors=MODIS:{SENSOR_MODIS} V375:{SENSOR_VIIRS_375} V750:{SENSOR_VIIRS_750} "
        f"data_subdir={DATA_SUBDIR}"
    )
```

- [ ] **Step 4: Verify profile loads**

Run:
```bash
python -c "import os; os.environ['VRP_PROFILE']='experimental'; from pipeline.profile import ENABLE_NTI_RELATIVE_PATH; print(f'experimental: {ENABLE_NTI_RELATIVE_PATH}')"
python -c "from pipeline.profile import ENABLE_NTI_RELATIVE_PATH; print(f'mirova_equivalent: {ENABLE_NTI_RELATIVE_PATH}')"
```

Expected:
```
experimental: True
mirova_equivalent: False
```

- [ ] **Step 5: Commit**

```bash
git add pipeline/profiles/experimental.yaml pipeline/profiles/mirova_equivalent.yaml pipeline/profile.py
git commit -m "feat: add enable_nti_relative_path flag to profiles (Path C)"
```

---

### Task 2: Write tests for Path C detection logic

**Files:**
- Create: `tests/test_nti_relative_path.py`

The tests use synthetic numpy arrays to verify the OR logic without needing real HDF/NetCDF files.

- [ ] **Step 1: Create test file**

```python
"""
Tests for Path C (NTI-relative) detection logic.

These test the core boolean masking that Path C adds, using synthetic arrays.
We don't test the full process_granule pipeline (requires HDF files) —
we test the detection decision logic that Path C introduces.
"""
import numpy as np
import pytest


def compute_nti_relative_mask(nti, bt, roi_mask, nti_bg, nti_std, t_bg, bt_sanity_k):
    """
    Replicate the Path C mask logic that will be added to process_viirs.py.
    A pixel passes Path C if:
      - It is in the ROI
      - nti > nti_bg + max(0.005, 3.0 * nti_std)    [relative NTI threshold]
      - bt > t_bg + bt_sanity_k                      [BT sanity floor]
    """
    nti_threshold = nti_bg + max(0.005, 3.0 * nti_std)
    return (
        roi_mask
        & ~np.isnan(nti)
        & ~np.isnan(bt)
        & (nti > nti_threshold)
        & (bt > (t_bg + bt_sanity_k))
    )


class TestPathCDetection:
    """Path C: NTI-relative detection for weak fumarolic signals."""

    def _make_scene(self, n=20):
        """Create a synthetic n×n scene with known background."""
        np.random.seed(42)
        roi_mask = np.zeros((n, n), dtype=bool)
        roi_mask[5:15, 5:15] = True  # 10×10 ROI in center

        # Background NTI ~ -0.95 ± 0.002 (typical Andean volcano)
        nti = np.full((n, n), -0.950) + np.random.normal(0, 0.002, (n, n))
        # Background BT ~ 275 K
        bt = np.full((n, n), 275.0) + np.random.normal(0, 1.0, (n, n))

        nti_bg = -0.950
        nti_std = 0.002
        t_bg = 275.0
        bt_sanity_k = 3.0

        return nti, bt, roi_mask, nti_bg, nti_std, t_bg, bt_sanity_k

    def test_no_anomaly_in_background(self):
        """Pure background scene: no pixels should pass Path C."""
        nti, bt, roi_mask, nti_bg, nti_std, t_bg, bt_sanity_k = self._make_scene()
        mask = compute_nti_relative_mask(nti, bt, roi_mask, nti_bg, nti_std, t_bg, bt_sanity_k)
        assert np.sum(mask) == 0

    def test_weak_fumarole_detected(self):
        """Single pixel with NTI bump +0.015 and BT +4K: should pass Path C."""
        nti, bt, roi_mask, nti_bg, nti_std, t_bg, bt_sanity_k = self._make_scene()
        # Inject weak fumarole at pixel (10, 10)
        nti[10, 10] = nti_bg + 0.015   # delta=0.015 > max(0.005, 3*0.002=0.006)
        bt[10, 10] = t_bg + 4.0        # 4K > sanity 3K
        mask = compute_nti_relative_mask(nti, bt, roi_mask, nti_bg, nti_std, t_bg, bt_sanity_k)
        assert np.sum(mask) == 1
        assert mask[10, 10]

    def test_nti_anomaly_below_bt_sanity_rejected(self):
        """NTI is anomalous but BT is too cold: should be rejected."""
        nti, bt, roi_mask, nti_bg, nti_std, t_bg, bt_sanity_k = self._make_scene()
        nti[10, 10] = nti_bg + 0.015
        bt[10, 10] = t_bg + 2.0  # 2K < sanity 3K
        mask = compute_nti_relative_mask(nti, bt, roi_mask, nti_bg, nti_std, t_bg, bt_sanity_k)
        assert np.sum(mask) == 0

    def test_bt_warm_but_nti_normal_rejected(self):
        """BT above sanity but NTI within background: should be rejected."""
        nti, bt, roi_mask, nti_bg, nti_std, t_bg, bt_sanity_k = self._make_scene()
        bt[10, 10] = t_bg + 5.0   # warm
        # nti stays at background level
        mask = compute_nti_relative_mask(nti, bt, roi_mask, nti_bg, nti_std, t_bg, bt_sanity_k)
        assert np.sum(mask) == 0

    def test_outside_roi_rejected(self):
        """Anomalous pixel outside ROI: should be rejected."""
        nti, bt, roi_mask, nti_bg, nti_std, t_bg, bt_sanity_k = self._make_scene()
        # Pixel (2, 2) is outside ROI (roi_mask is [5:15, 5:15])
        nti[2, 2] = nti_bg + 0.015
        bt[2, 2] = t_bg + 4.0
        mask = compute_nti_relative_mask(nti, bt, roi_mask, nti_bg, nti_std, t_bg, bt_sanity_k)
        assert np.sum(mask) == 0

    def test_nan_pixels_rejected(self):
        """NaN in either NTI or BT: should be rejected."""
        nti, bt, roi_mask, nti_bg, nti_std, t_bg, bt_sanity_k = self._make_scene()
        nti[10, 10] = nti_bg + 0.015
        bt[10, 10] = np.nan  # NaN BT
        mask = compute_nti_relative_mask(nti, bt, roi_mask, nti_bg, nti_std, t_bg, bt_sanity_k)
        assert np.sum(mask) == 0

    def test_sigma_floor_005(self):
        """When sigma is very small, floor of 0.005 applies."""
        nti, bt, roi_mask, nti_bg, nti_std, t_bg, bt_sanity_k = self._make_scene()
        nti_std_tiny = 0.001  # 3*0.001 = 0.003 < floor 0.005
        # Delta of 0.004 should fail (below floor 0.005)
        nti[10, 10] = nti_bg + 0.004
        bt[10, 10] = t_bg + 4.0
        mask = compute_nti_relative_mask(nti, bt, roi_mask, nti_bg, nti_std_tiny, t_bg, bt_sanity_k)
        assert np.sum(mask) == 0
        # Delta of 0.006 should pass (above floor 0.005)
        nti[10, 10] = nti_bg + 0.006
        mask = compute_nti_relative_mask(nti, bt, roi_mask, nti_bg, nti_std_tiny, t_bg, bt_sanity_k)
        assert np.sum(mask) == 1

    def test_planchonpeteroa_scenario(self):
        """
        Reproduce the PP FN scenario: nti_delta=0.013, bt delta=7K.
        With sigma_nti=0.004, threshold = max(0.005, 0.012) = 0.012.
        Delta 0.013 > 0.012: should detect.
        """
        nti, bt, roi_mask, nti_bg, nti_std, t_bg, bt_sanity_k = self._make_scene()
        nti_bg_pp = -0.950
        nti_std_pp = 0.004
        t_bg_pp = 276.0
        nti[10, 10] = nti_bg_pp + 0.013
        bt[10, 10] = t_bg_pp + 7.0
        mask = compute_nti_relative_mask(nti, bt, roi_mask, nti_bg_pp, nti_std_pp, t_bg_pp, bt_sanity_k)
        assert np.sum(mask) == 1
```

- [ ] **Step 2: Run tests to verify they pass with the reference function**

Run:
```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
python -m pytest tests/test_nti_relative_path.py -v
```

Expected: 8 tests PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/test_nti_relative_path.py
git commit -m "test: add unit tests for NTI relative path (Path C) detection logic"
```

---

### Task 3: Add Path C to process_viirs.py (375m)

**Files:**
- Modify: `pipeline/process_viirs.py:60-68` (imports)
- Modify: `pipeline/process_viirs.py:296-311` (detection block)
- Modify: `pipeline/process_viirs.py:403-414` (output dict)

- [ ] **Step 1: Add import of ENABLE_NTI_RELATIVE_PATH**

In `pipeline/process_viirs.py`, the import block near line 60. Add `ENABLE_NTI_RELATIVE_PATH` to the import list from `pipeline.profile`:

```python
from pipeline.profile import (
    ANOMALY_THRESHOLD_K,
    N_SIGMA_MIR,
    TIR_THRESHOLD_K,
    N_SIGMA_TIR,
    VENT_THRESHOLD_K,
    N_SIGMA_VENT,
    BG_INNER_KM,
    BG_OUTER_KM,
    NTI_K1_NIGHT,
    NTI_BT_SANITY_K,
    ENABLE_VENT_PATH,
    ENABLE_ERUPTION_PATH,
    ENABLE_NTI_RELATIVE_PATH,
)
```

- [ ] **Step 2: Add Path C mask after Path B (around line 307)**

After the existing `nti_path_hot` block and before `hot_mask_2d = bt_path_hot | nti_path_hot`, add Path C:

```python
            # Path C — NTI relative path (Session 11).
            # Uses the contextual NTI threshold (nti_bg + max(0.005, 3*sigma))
            # instead of the absolute NTI_K1_NIGHT floor. This detects weak
            # fumarolic signals (0.05-0.3 MW) where the NTI shifts by ~0.01
            # above background — too small for the -0.8 absolute floor but
            # clearly anomalous against the local sigma (~0.002-0.004).
            # Gated by enable_nti_relative_path (experimental only).
            n_nti_rel_path = 0
            if (ENABLE_NTI_RELATIVE_PATH
                    and "I05" in bands
                    and not np.isnan(nti_bg)
                    and len(bg_nti) >= 10):
                nti_rel_threshold = nti_bg + max(0.005, 3.0 * nti_std)
                nti_rel_hot = (
                    roi_mask
                    & ~np.isnan(nti)
                    & ~np.isnan(bt)
                    & (nti > nti_rel_threshold)
                    & (bt > (t_bg_i04 + NTI_BT_SANITY_K))
                )
                n_nti_rel_path = int(np.sum(nti_rel_hot))
            else:
                nti_rel_hot = np.zeros_like(bt_path_hot)

            hot_mask_2d = bt_path_hot | nti_path_hot | nti_rel_hot
```

**Important**: Remove the old line `hot_mask_2d = bt_path_hot | nti_path_hot` and replace it with the new three-way OR shown above.

Note: `bg_nti` and `nti_std` are computed earlier (lines 251-254) and are in scope here. `nti` array is also in scope from the NTI computation block.

- [ ] **Step 3: Also initialize n_nti_rel_path = 0 near the other counters (line 276-277)**

Add after `n_nti_path = 0`:

```python
    n_nti_rel_path = 0
```

- [ ] **Step 4: Add n_nti_rel_path to the output dict (around line 409)**

Add after `"n_nti_path": n_nti_path,`:

```python
        "n_nti_rel_path": n_nti_rel_path,
```

- [ ] **Step 5: Verify syntax**

Run:
```bash
python -c "import os; os.environ['VRP_PROFILE']='experimental'; from pipeline import process_viirs; print('OK')"
```

Expected: `OK` (no import errors).

- [ ] **Step 6: Commit**

```bash
git add pipeline/process_viirs.py
git commit -m "feat: add Path C (NTI relative) to process_viirs.py for weak fumarolic detection"
```

---

### Task 4: Add Path C to process_viirs_mod.py (750m)

**Files:**
- Modify: `pipeline/process_viirs_mod.py` (imports, NTI stats, detection block, output dict)

The 750m processor is similar but currently lacks `nti_std` and `n_nti_anomalous`.

- [ ] **Step 1: Add ENABLE_NTI_RELATIVE_PATH to the import**

Find the import block from `pipeline.profile` and add `ENABLE_NTI_RELATIVE_PATH`.

- [ ] **Step 2: Compute nti_std in the NTI statistics block (around line 228-236)**

Currently the NTI block only computes `nti_bg` and `nti_max`. Add `nti_std` and `n_nti_anomalous`:

Replace:
```python
        bg_nti = nti[bg_mask & ~np.isnan(nti)]
        if len(bg_nti) >= 10:
            nti_bg = float(np.median(bg_nti))

            # ROI NTI max for diagnostics
            roi_nti = nti[roi_mask]
            roi_nti_valid = roi_nti[~np.isnan(roi_nti)]
            if len(roi_nti_valid) > 0:
                nti_max = float(np.max(roi_nti_valid))
```

With:
```python
        bg_nti = nti[bg_mask & ~np.isnan(nti)]
        if len(bg_nti) >= 10:
            nti_bg = float(np.median(bg_nti))
            nti_std = float(np.std(bg_nti))
            nti_threshold = nti_bg + max(0.005, 3.0 * nti_std)

            # ROI NTI anomalies
            roi_nti = nti[roi_mask]
            roi_nti_valid = roi_nti[~np.isnan(roi_nti)]
            if len(roi_nti_valid) > 0:
                nti_max = float(np.max(roi_nti_valid))
                n_nti_anomalous = int(np.sum(roi_nti_valid > nti_threshold))
```

Also initialize `nti_std = float("nan")` and `n_nti_anomalous = 0` near the other NTI variable initializations.

- [ ] **Step 3: Add Path C to the detection block (around line 280-283)**

After `nti_path_hot` and before `hot_mask_2d`:

```python
    # Path C — NTI relative path (Session 11)
    n_nti_rel_path = 0
    if (ENABLE_NTI_RELATIVE_PATH
            and nti is not None
            and not np.isnan(nti_bg)
            and not np.isnan(nti_std)):
        nti_rel_threshold = nti_bg + max(0.005, 3.0 * nti_std)
        nti_rel_hot = (
            roi_mask
            & ~np.isnan(nti)
            & ~np.isnan(bt)
            & (nti > nti_rel_threshold)
            & (bt > (t_bg + NTI_BT_SANITY_K))
        )
        n_nti_rel_path = int(np.sum(nti_rel_hot))
    else:
        nti_rel_hot = np.zeros_like(roi_mask)

    hot_mask_2d = bt_path_hot | nti_path_hot | nti_rel_hot
```

Remove the old `hot_mask_2d = bt_path_hot | nti_path_hot`.

- [ ] **Step 4: Add n_nti_rel_path and n_nti_anomalous to the output dict**

Add to the return dict:
```python
        "n_nti_anomalous": n_nti_anomalous,
        "n_nti_rel_path": n_nti_rel_path,
```

- [ ] **Step 5: Verify syntax**

Run:
```bash
python -c "import os; os.environ['VRP_PROFILE']='experimental'; from pipeline import process_viirs_mod; print('OK')"
```

Expected: `OK`.

- [ ] **Step 6: Commit**

```bash
git add pipeline/process_viirs_mod.py
git commit -m "feat: add Path C (NTI relative) to process_viirs_mod.py, add nti_std computation"
```

---

### Task 5: Verify end-to-end with dry run

**Files:** None modified. Verification only.

- [ ] **Step 1: Verify mirova_equivalent does NOT activate Path C**

```bash
python -c "
from pipeline.profile import ENABLE_NTI_RELATIVE_PATH, PROFILE_NAME
assert PROFILE_NAME == 'mirova_equivalent'
assert ENABLE_NTI_RELATIVE_PATH == False
print('mirova_equivalent: Path C correctly disabled')
"
```

- [ ] **Step 2: Verify experimental DOES activate Path C**

```bash
python -c "
import os; os.environ['VRP_PROFILE'] = 'experimental'
from pipeline.profile import ENABLE_NTI_RELATIVE_PATH, PROFILE_NAME
assert PROFILE_NAME == 'experimental'
assert ENABLE_NTI_RELATIVE_PATH == True
print('experimental: Path C correctly enabled')
"
```

- [ ] **Step 3: Run unit tests**

```bash
python -m pytest tests/test_nti_relative_path.py -v
```

Expected: 8 tests PASS.

- [ ] **Step 4: Commit dashboard changes (from earlier in session)**

```bash
git add frontend/index.html .claude/launch.json
git commit -m "feat: add hotspot anomaly layer to overview map with volcano filter"
```

Note: Do NOT commit `frontend/llaima_anomalies.png` or `frontend/planchonpeteroa_anomalies.png` — those are diagnostic artifacts, not production files.

---

### Acceptance criteria

1. `mirova_equivalent` profile: `ENABLE_NTI_RELATIVE_PATH = False`, zero behavior change
2. `experimental` profile: `ENABLE_NTI_RELATIVE_PATH = True`, Path C active
3. Path C fires when `nti > nti_bg + max(0.005, 3*sigma_nti)` AND `bt > t_bg + NTI_BT_SANITY_K`
4. `n_nti_rel_path` counter appears in output JSON for auditing
5. All 8 unit tests pass
6. Both processor modules (`process_viirs.py`, `process_viirs_mod.py`) have identical Path C logic

### Reversion plan

If Path C produces unacceptable FPs in experimental:
1. Set `enable_nti_relative_path: false` in `experimental.yaml`
2. Reprocess affected volcanoes with `--overwrite`
3. No code changes needed — the flag gates everything

### Next steps after implementation

1. Dispatch GitHub Actions reprocessing for PlanchonPeteroa and Villarrica with `--profile experimental`
2. Run `experiments/11_strict_audit.py` on experimental output to compare recall/FP rates
3. If recall improves without FP explosion, consider promoting to mirova_equivalent
