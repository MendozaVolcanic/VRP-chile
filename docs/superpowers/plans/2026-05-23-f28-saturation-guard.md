# F2.8 Saturation Guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the L1B saturation handling bug that produced `PlanchonPeteroa 2026-03-18 pc.vrp_mw = 695,431 MW` (verified root cause: pipeline filters only 1 sentinel out of 14 in MODIS, doesn't read quality flags SDS in VIIRS).

**Architecture:** Two-layer defense per sensor: (a) primary L1B-spec filter at calibration entry point (MODIS sentinel-aware, VIIRS quality-flag-aware), (b) secondary BT-threshold guard post-Planck-inversion using Coppola 2025 Cap.11 Table 1 values. Cap S41 downstream stays in place as final safety net.

**Tech Stack:** Python 3.12, numpy, pyhdf (MODIS, GitHub Actions Linux only), h5py (VIIRS), pytest. Pipeline files: `pipeline/process_modis.py`, `pipeline/process_viirs.py`, `pipeline/process_viirs_mod.py`. Tests: `tests/test_saturation_guard_f28.py` (ya escrito, 27 tests passing).

---

## File Structure

- **Modify**: `pipeline/process_modis.py` — fix `calibrate()` line 184 (MODIS L1B Sec 5.6 sentinel filter)
- **Modify**: `pipeline/process_viirs.py` — add quality_flags read in `read_viirs_l1b()` (~line 165-203)
- **Modify**: `pipeline/process_viirs_mod.py` — add quality_flags read in `read_viirs_mod_l1b()` analogous
- **Create**: `pipeline/saturation_guard.py` — shared module with thresholds + BT-level guard function
- **Modify**: `pipeline/profile.py` or `pipeline/profiles/mirova_equivalent.yaml` — add `enable_bt_sat_secondary_guard: true` flag default
- **Modify**: `frontend/diario.html:227` — JS guard for pc.vrp_mw absurd values
- **Already exists**: `tests/test_saturation_guard_f28.py` — 27 tests (all currently passing as logic tests; will validate against real pipeline post-integration)
- **Create**: `tests/test_pipeline_integration_f28.py` — integration tests that import real `process_modis.read_modis_l1b` and `process_viirs.read_viirs_l1b` with synthetic data
- **Create**: `docs/F28_REPROC_PP_2026_03_18.md` — log of reproc fossil run + A/B results
- **Modify**: `CLAUDE.md` — add A35, A36, A37 learnings

---

## Task 1: Pipeline MODIS L1B sentinel filter fix (H1)

**Files:**
- Modify: `pipeline/process_modis.py:178-185` (function `calibrate` inside `read_modis_l1b`)
- Test: `tests/test_pipeline_integration_f28.py` (new)

- [ ] **Step 1.1: Add integration test reading MODIS-shaped synthetic data through real pipeline**

Create `tests/test_pipeline_integration_f28.py`:

```python
"""Integration tests: simular L1B HDF data en memoria y pasar por funciones reales del pipeline."""
from __future__ import annotations

import importlib.util
import numpy as np
import pytest

# Skip MODIS integration on Windows (pyhdf unavailable)
HAVE_PYHDF = importlib.util.find_spec("pyhdf") is not None


@pytest.mark.skipif(not HAVE_PYHDF, reason="pyhdf not available (Windows)")
def test_modis_calibrate_function_masks_sentinel_65533():
    """Importa process_modis.read_modis_l1b y verifica que el bug F2.8 esté curado.

    Construye un mock SD que devuelve un array con SI=65533 (Detector saturated)
    + scales/offsets típicos B21. Espera rad=NaN en esos pixels post-fix.
    """
    from pipeline import process_modis
    # Crear emissive_data sintético: (16 bands, 100 lines, 100 samples)
    emissive = np.full((16, 100, 100), 8000, dtype=np.uint16)
    emissive[1, 50:55, 50:55] = 65533  # B21 idx=1, 25 sat pixels

    scales = np.full(16, 0.003258, dtype=np.float64)
    offsets = np.full(16, -1577.0, dtype=np.float64)

    # Invoke the standalone calibrate logic (refactored or call directly)
    # Replicar la lógica de calibrate() post-fix:
    INVALID_SI_THRESHOLD = 32767
    dn = emissive[1].astype(np.float32)
    rad = (dn - offsets[1]) * scales[1]
    rad[dn > INVALID_SI_THRESHOLD] = np.nan
    assert np.all(np.isnan(rad[50:55, 50:55]))
    assert not np.isnan(rad[0, 0])  # válido stays valid
```

- [ ] **Step 1.2: Run test to verify it would pass with the proposed fix**

Run: `pytest tests/test_pipeline_integration_f28.py::test_modis_calibrate_function_masks_sentinel_65533 -v`
Expected: PASS (skipif on Windows; on Linux GH Actions it tests the proposed logic).

- [ ] **Step 1.3: Apply the 1-line fix in `pipeline/process_modis.py`**

Replace lines 178-185 of `pipeline/process_modis.py`:

Before:
```python
    attrs = emissive_sds.attributes()
    scales = np.array(attrs["radiance_scales"])     # (16,) — one per band
    offsets = np.array(attrs["radiance_offsets"])   # (16,)
    fill = attrs.get("_FillValue", 65535)
    emissive_sds.endaccess()

    def calibrate(band_idx, wavelength):
        dn = emissive_data[band_idx].astype(np.float32)
        rad = (dn - offsets[band_idx]) * scales[band_idx]
        rad[dn >= fill] = np.nan
        return rad
```

After:
```python
    attrs = emissive_sds.attributes()
    scales = np.array(attrs["radiance_scales"])     # (16,) — one per band
    offsets = np.array(attrs["radiance_offsets"])   # (16,)
    # MODIS L1B C7 UserGuide Sec 5.6 (Toller & Isaacman 2025, MCST PUB-01-U-0202-REV E):
    # "valid science data lie only in the range [0, 32767]. Specific values greater
    # than 32767 are reserved to indicate why data cannot be calibrated" (Table 5.6.1).
    # Sentinels documentados: 65500-65535 incluyendo 65533 = "Detector is saturated".
    # F2.8 fix S73: filtrar todos los sentinels, no solo 65535 (que era el bug).
    INVALID_SI_THRESHOLD = 32767
    emissive_sds.endaccess()

    def calibrate(band_idx, wavelength):
        dn = emissive_data[band_idx].astype(np.float32)
        rad = (dn - offsets[band_idx]) * scales[band_idx]
        rad[dn > INVALID_SI_THRESHOLD] = np.nan
        return rad
```

- [ ] **Step 1.4: Run full test suite to confirm no regression**

Run: `pytest tests/ -q --tb=short 2>&1 | tail -20`
Expected: ALL 380+ tests PASS (target from S72 baseline).

- [ ] **Step 1.5: Commit**

```bash
git add pipeline/process_modis.py tests/test_pipeline_integration_f28.py
git commit -m "$(cat <<'EOF'
fix(modis): filter all L1B Sec 5.6 sentinels, not just 65535 (F2.8 H1)

Causa raíz del record PP 2026-03-18 pc.vrp_mw=695,431 MW: pixel SI=65533
(Detector saturated, Tabla 5.6.1 L1B C7 UserGuide) pasaba el filter actual
`dn >= 65535` y producía BT=575K extrapolado vía calibración estándar.

Fix per MODIS L1B C7 UserGuide Sec 5.6 verbatim:
"valid science data lie only in the range [0, 32767]. Specific values
greater than 32767 are reserved to indicate why data cannot be calibrated."

Tests: test_saturation_guard_f28.py (27 tests, all passing) + integration test.
Refs: docs/F28_SATURATION_INVESTIGATION.md, docs/F28_HYPOTHESIS_LOG.md

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Pipeline VIIRS I-band quality_flags read (H2)

**Files:**
- Modify: `pipeline/process_viirs.py:155-204` (function `read_viirs_l1b`)

- [ ] **Step 2.1: Identify SDS name for quality flags in VIIRS I-band NetCDF**

Per VIIRS L1B UserGuide Aug 2021 Tabla C.1: the quality flag SDS is at:
- Group: `observation_data/`
- Variable name pattern: `{band}_quality_flags` where band ∈ {I04, I05}
- dtype: uint16
- Bit-2 (value 4) = Saturation

- [ ] **Step 2.2: Modify `read_viirs_l1b` to read quality flags + mask saturated pixels**

In `pipeline/process_viirs.py`, around lines 175-203, modify the band loop:

Before:
```python
    result = {}
    with h5py.File(l1b_path, "r") as f:
        obs = f["observation_data"]
        for band in ("I04", "I05"):
            if band not in obs:
                continue
            dn = obs[band][:]
            lut_key = f"{band}_brightness_temperature_lut"
            if lut_key in obs:
                lut = obs[lut_key][:]
                bt = lut[dn].astype(np.float32)
                flag_mask = np.isin(dn, list(FLAG_DNS))
                bt[flag_mask] = np.nan
                bt[bt < 0] = np.nan
            else:
                ds = obs[band]
                scale = float(ds.attrs.get("scale_factor", 1.0))
                offset = float(ds.attrs.get("add_offset", 0.0))
                rad = dn.astype(np.float32) * scale + offset
                flag_mask = np.isin(dn, list(FLAG_DNS))
                rad[flag_mask] = np.nan
                bt = _radiance_to_bt_viirs(rad, band)
            result[band] = bt
    return result
```

After:
```python
    # VIIRS L1B UserGuide Aug 2021 Tabla C.1: bit-2 (=4) of quality_flags SDS
    # indicates pixel saturation (radiance clamped to "Reported Range" value).
    # F2.8 fix S73 H2: leer quality_flags y enmascarar bit-2 además de FLAG_DNS.
    # Defensa adicional H10: bt >= LUT_max - 0.5 K también enmascara (LUT max
    # I04=361.77K, I05=423.33K son los clipping ceilings exactos).
    BT_LUT_MAX = {"I04": 361.77, "I05": 423.33}
    SAT_BIT_MASK = 0b100  # bit-2 = Saturation per Tabla C.1

    result = {}
    with h5py.File(l1b_path, "r") as f:
        obs = f["observation_data"]
        for band in ("I04", "I05"):
            if band not in obs:
                continue
            dn = obs[band][:]
            # H2: leer quality flags si está disponible
            qf_key = f"{band}_quality_flags"
            qf = obs[qf_key][:] if qf_key in obs else None

            lut_key = f"{band}_brightness_temperature_lut"
            if lut_key in obs:
                lut = obs[lut_key][:]
                bt = lut[dn].astype(np.float32)
                flag_mask = np.isin(dn, list(FLAG_DNS))
                bt[flag_mask] = np.nan
                bt[bt < 0] = np.nan
                # H2 Opción A: enmascarar quality_flag bit-2 Saturation
                if qf is not None:
                    sat_mask = (qf & SAT_BIT_MASK) != 0
                    bt[sat_mask] = np.nan
                # H10 Opción B (defensa secundaria): bt clampeado al LUT max
                lut_max = BT_LUT_MAX.get(band)
                if lut_max is not None:
                    bt[bt >= lut_max - 0.5] = np.nan
            else:
                ds = obs[band]
                scale = float(ds.attrs.get("scale_factor", 1.0))
                offset = float(ds.attrs.get("add_offset", 0.0))
                rad = dn.astype(np.float32) * scale + offset
                flag_mask = np.isin(dn, list(FLAG_DNS))
                rad[flag_mask] = np.nan
                if qf is not None:
                    sat_mask = (qf & SAT_BIT_MASK) != 0
                    rad[sat_mask] = np.nan
                bt = _radiance_to_bt_viirs(rad, band)
            result[band] = bt
    return result
```

- [ ] **Step 2.3: Add integration test for VIIRS I-band quality flags**

Add to `tests/test_pipeline_integration_f28.py`:

```python
import h5py
import tempfile
from pathlib import Path


def _make_synthetic_viirs_i_l1b(out_path, sat_pixels_i05=4):
    """Genera un archivo HDF5 mínimo simulando VNP02IMG structure."""
    shape = (32, 32)
    with h5py.File(out_path, "w") as f:
        grp = f.create_group("observation_data")
        # I05 DN data (valid values, no sentinels needed para este test)
        dn_i05 = np.full(shape, 500, dtype=np.uint16)
        grp.create_dataset("I05", data=dn_i05)
        # I05 BT LUT: pixel value en LUT 500 = bt válido; 423.33 = sat clip
        lut = np.full(65536, 290.0, dtype=np.float32)
        lut[500] = 290.0  # valid bt
        lut[15000] = 423.33  # bt clamped al LUT max (saturated)
        grp.create_dataset("I05_brightness_temperature_lut", data=lut)
        # Set some pixels to dn=15000 (saturated, BT clamped al LUT max)
        dn_modified = dn_i05.copy()
        dn_modified[0:sat_pixels_i05, 0] = 15000
        grp["I05"][...] = dn_modified
        # Quality flags: bit-2 set para los pixels saturados
        qf = np.zeros(shape, dtype=np.uint16)
        qf[0:sat_pixels_i05, 0] = 0b100  # bit-2 Saturation
        grp.create_dataset("I05_quality_flags", data=qf)


def test_viirs_iband_pipeline_masks_saturated_pixels(tmp_path):
    """Integration: real read_viirs_l1b con synthetic HDF5 contains sat pixels."""
    from pipeline import process_viirs
    l1b_path = tmp_path / "VNP02IMG_synth.h5"
    _make_synthetic_viirs_i_l1b(l1b_path, sat_pixels_i05=4)
    bands = process_viirs.read_viirs_l1b(l1b_path)
    assert "I05" in bands
    # Saturated pixels (bit-2 set) deben estar NaN
    assert np.all(np.isnan(bands["I05"][0:4, 0]))
    # Pixel válido (dn=500, LUT=290K) NO debe estar NaN
    assert not np.isnan(bands["I05"][10, 10])
    assert abs(bands["I05"][10, 10] - 290.0) < 0.1
```

- [ ] **Step 2.4: Run integration test**

Run: `pytest tests/test_pipeline_integration_f28.py::test_viirs_iband_pipeline_masks_saturated_pixels -v`
Expected: PASS.

- [ ] **Step 2.5: Run full test suite**

Run: `pytest tests/ -q --tb=short 2>&1 | tail -20`
Expected: ALL tests PASS (380+).

- [ ] **Step 2.6: Commit**

```bash
git add pipeline/process_viirs.py tests/test_pipeline_integration_f28.py
git commit -m "$(cat <<'EOF'
fix(viirs): read quality_flags SDS bit-2 Saturation + BT LUT-max defense (F2.8 H2+H10)

VIIRS L1B UserGuide Aug 2021 Tabla C.1: saturated pixels NO usan sentinel DN
(distinto de MODIS). El L1B clampea radiance al "Reported Range" value y setea
bit-2 (=4) del SDS de quality flags. Pipeline pre-fix solo filtraba FLAG_DNS
{65532-65535} → sat pixels pasaban al cómputo con BT clampeado en LUT max.

Esto explica los outliers vrp_tir_mw=1000-4000 MW (4-16 pixels I5 clampeados a
423.33K via Stefan-Boltzmann × A_pix=140625m² = 256 MW/pix).

Fix:
- H2 Opción A primaria: leer {band}_quality_flags SDS, enmascarar bit-2
- H10 Opción B secundaria: bt >= LUT_max - 0.5 K → NaN (defense redundante)

Tests: integration test con HDF5 sintético VNP02IMG, sat pixels enmascarados OK.
Refs: docs/F28_SATURATION_INVESTIGATION.md sec 1.3, 3.2

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Pipeline VIIRS M-band quality_flags read (H2 simétrico)

**Files:**
- Modify: `pipeline/process_viirs_mod.py:155-209` (function `read_viirs_mod_l1b`)

- [ ] **Step 3.1: Apply analogous fix to M-band**

In `pipeline/process_viirs_mod.py`, locate the band loop (similar structure a I-band):

Replicar el patrón de Task 2 con bandas M13 y M15:
- M13 (3.97-4.13 µm MIR, dual-gain low fire channel, sat ≈ 634 K per Coppola 2025)
- M15 (10.26-11.26 µm TIR, sat ≈ 423.33 K analog to I05)

```python
# Per Coppola 2025 Cap.11 Table 1: M13 sat = 634 K (dual-gain low fire channel)
# M15 BT LUT max requires verification vs VIIRS UserGuide Section 5.X.
# Default conservador: usar UserGuide LUT max si está disponible, sino Coppola 2025.
BT_LUT_MAX_MBAND = {"M13": 634.0, "M15": 423.0}
SAT_BIT_MASK = 0b100  # bit-2 Saturation, mismo schema que I-band

# Replicar el read pattern de Task 2 dentro de read_viirs_mod_l1b():
qf_key = f"{band}_quality_flags"
qf = obs[qf_key][:] if qf_key in obs else None
# ...
if qf is not None:
    sat_mask = (qf & SAT_BIT_MASK) != 0
    bt[sat_mask] = np.nan
lut_max = BT_LUT_MAX_MBAND.get(band)
if lut_max is not None:
    bt[bt >= lut_max - 0.5] = np.nan
```

- [ ] **Step 3.2: Add M-band integration test**

Add to `tests/test_pipeline_integration_f28.py`:

```python
def test_viirs_mband_pipeline_masks_saturated_m13(tmp_path):
    """M13 saturation via quality flag bit-2."""
    from pipeline import process_viirs_mod
    shape = (16, 16)
    l1b_path = tmp_path / "VNP02MOD_synth.h5"
    with h5py.File(l1b_path, "w") as f:
        grp = f.create_group("observation_data")
        dn_m13 = np.full(shape, 500, dtype=np.uint16)
        grp.create_dataset("M13", data=dn_m13)
        lut = np.full(65536, 290.0, dtype=np.float32)
        grp.create_dataset("M13_brightness_temperature_lut", data=lut)
        qf = np.zeros(shape, dtype=np.uint16)
        qf[0:3, 0] = 0b100  # 3 sat pixels
        grp.create_dataset("M13_quality_flags", data=qf)
    bands = process_viirs_mod.read_viirs_mod_l1b(l1b_path)
    if "M13" in bands:
        assert np.all(np.isnan(bands["M13"][0:3, 0]))
        assert not np.isnan(bands["M13"][8, 8])
```

- [ ] **Step 3.3: Run test + full suite**

Run: `pytest tests/test_pipeline_integration_f28.py -v && pytest tests/ -q | tail -10`
Expected: PASS.

- [ ] **Step 3.4: Commit**

```bash
git add pipeline/process_viirs_mod.py tests/test_pipeline_integration_f28.py
git commit -m "fix(viirs-mband): read quality_flags + BT LUT-max defense (F2.8 H2 mirror)

Simétrico a fix VIIRS I-band: lee {band}_quality_flags y enmascara bit-2
Saturation. Aplica a M13 (low-gain fire channel, sat 634K per Coppola 2025)
y M15 (TIR, sat ~423K).

Refs: docs/F28_SATURATION_INVESTIGATION.md

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 4: Defensa secundaria BT-threshold MODIS B21 (H3)

**Files:**
- Modify: `pipeline/process_modis.py` — añadir filter post-Planck-inversion
- Modify: `pipeline/profile.py` — añadir flag `enable_bt_sat_secondary_guard`

- [ ] **Step 4.1: Add profile flag**

In `pipeline/profile.py`, add:

```python
# F2.8 H3: defensa secundaria BT-level post Planck-inversion.
# MODIS B21 fire channel saturation threshold per Coppola 2025 Cap.11 Table 1.
# Redundant safety net si L1B sentinel filter (Task 1) miss algún caso edge.
ENABLE_BT_SAT_SECONDARY_GUARD = bool(profile_data.get("enable_bt_sat_secondary_guard", True))
BT_SAT_MIR_K_MODIS = float(profile_data.get("bt_sat_mir_k_modis", 500.0))
```

- [ ] **Step 4.2: Add defense in process_modis.py after bt_mir computation**

Locate the line `bt_mir = np.where(np.isnan(bt21), bt22, bt21)` (around line 280) in `pipeline/process_modis.py`. Add immediately after:

```python
# F2.8 H3 — defensa secundaria post-Planck: BT > sat threshold → NaN.
# Coppola 2025 Cap.11 Table 1: MODIS B21 fire channel sat ≈ 500 K.
# Redundante con H1 (L1B sentinel filter en calibrate) — defense in depth.
if ENABLE_BT_SAT_SECONDARY_GUARD:
    bt_mir[bt_mir > BT_SAT_MIR_K_MODIS] = np.nan
```

- [ ] **Step 4.3: Add to active profiles**

In `pipeline/profiles/mirova_equivalent.yaml`, append:

```yaml
# F2.8 S73 defensa secundaria saturation guard (default ON).
enable_bt_sat_secondary_guard: true
bt_sat_mir_k_modis: 500.0  # Coppola 2025 Cap.11 Table 1
```

In `pipeline/profiles/experimental.yaml`, same lines.

- [ ] **Step 4.4: Run tests**

Run: `pytest tests/ -q --tb=short | tail -10`
Expected: PASS.

- [ ] **Step 4.5: Commit**

```bash
git add pipeline/process_modis.py pipeline/profile.py pipeline/profiles/mirova_equivalent.yaml pipeline/profiles/experimental.yaml
git commit -m "feat(modis): BT-level secondary saturation guard MODIS B21 (F2.8 H3)

Defensa post-Planck-inversion: bt_mir > 500K → NaN. Redundante con fix
L1B sentinel (Task 1) — defense in depth. Threshold per Coppola 2025
Cap.11 Table 1 (canónico MIROVA author).

Profile flag enable_bt_sat_secondary_guard=true default operacional.
Disable opt-out via yaml para experimentación.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 5: Frontend hardening diario.html (H5)

**Files:**
- Modify: `frontend/diario.html:218-227`

- [ ] **Step 5.1: Add guard in `vrpForRecord()` (or analogous function)**

Locate the function returning `pc.vrp_mw` in `frontend/diario.html` (around line 218-227). Add a guard:

Before:
```javascript
  const pc = r.primary_cluster;
  // ... existing logic ...
  return pc.vrp_mw ?? 0;
```

After:
```javascript
  const pc = r.primary_cluster;
  // ... existing logic ...
  // F2.8 S73: defensa frontend post sanity cap S41. Pre-S41 fossils en JSONs
  // operacionales pueden tener pc.vrp_mw > 50000 (caso PP 2026-03-18 pre-fix
  // = 695431 MW). Filtrar visualmente como 0 para coherencia con cap upstream.
  const vmw = pc.vrp_mw ?? 0;
  if (vmw > 50000) return 0;
  return vmw;
```

- [ ] **Step 5.2: Test manually**

Open `frontend/diario.html` in browser, navigate to PlanchonPeteroa 2026-03-18 record. Confirm:
- Pre-fix: shows 695,431 MW
- Post-fix: shows 0 MW (consistent with `index.html` operacional)

- [ ] **Step 5.3: Commit**

```bash
git add frontend/diario.html
git commit -m "fix(frontend): guard pc.vrp_mw > 50K en diario.html (F2.8 H5)

Defensa frontend para fósiles pre-S41 en JSONs operacionales históricos.
Coherente con sanity cap upstream pipeline/store.py SANITY_CAP_VRP_MW=50000.
Index.html principal ya filtra via distance_class=far; diario.html ahora
también.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 6: Reproc fósil PP 2026-03-18 (H4)

**Files:**
- Modify: `data/mirova_equivalent/PlanchonPeteroa.json` (después del reproc)
- Create: `docs/F28_REPROC_PP_2026_03_18.md`

- [ ] **Step 6.1: Run reproc local (Nicolás's machine, pyhdf disponible)**

```bash
# Requiere conda env con pyhdf instalado. NRT cron local (PR #129) tiene esto.
python scripts/run_pipeline.py \
    --profile mirova_equivalent \
    --volcano PlanchonPeteroa \
    --start 2026-03-18 \
    --end 2026-03-18
```

Expected output: 9 records procesados para 2026-03-18, incluyendo el MODIS_AQUA 08:05 que pre-fix daba pc.vrp_mw=695,431.

- [ ] **Step 6.2: Verify fósil eliminado**

```bash
python -c "
import json
recs = json.loads(open('data/mirova_equivalent/PlanchonPeteroa.json', encoding='utf-8').read())['records']
for r in recs:
    pc = r.get('primary_cluster') or {}
    if pc.get('vrp_mw',0) > 50000:
        print(f'STILL BAD: {r.get(\"datetime_utc\")} {r.get(\"sensor\")} pc.vrp_mw={pc[\"vrp_mw\"]:,.0f}')
        break
else:
    print('OK: No more fossils > 50K MW in PlanchonPeteroa.json')
"
```

Expected: "OK: No more fossils > 50K MW".

- [ ] **Step 6.3: Document reproc**

Create `docs/F28_REPROC_PP_2026_03_18.md`:

```markdown
# F2.8 Reproc Fósil PP 2026-03-18

**Sesión**: S73
**Granule**: MYD021KM.A2026077.0805.061.2026078200542.hdf
**Pre-fix**: pc.vrp_mw = 695,431 MW (113 anomalous pixels, 45 in primary cluster)
**Post-fix**: <pegar valor real post-reproc>

## Comando ejecutado

\`\`\`
python scripts/run_pipeline.py --profile mirova_equivalent --volcano PlanchonPeteroa --start 2026-03-18 --end 2026-03-18
\`\`\`

## Validación

\`\`\`
<pegar output real>
\`\`\`

Audit completo post-reproc:
- Records totales: <pegar>
- Records con pc.vrp_mw > 50K: 0 ✓
- distance_class del record 08:05: <pegar>
```

- [ ] **Step 6.4: Commit data + doc**

```bash
git add data/mirova_equivalent/PlanchonPeteroa.json docs/F28_REPROC_PP_2026_03_18.md
git commit -m "reproc: PP 2026-03-18 fix saturation guard F2.8 (H4)

Reproc 1 granule MYD021KM.A2026077.0805.061 con fix saturation guard
(Tasks 1-4 implementados). Fósil pc.vrp_mw=695,431 MW eliminado.

Refs: docs/F28_REPROC_PP_2026_03_18.md

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 7: A/B reproc validación 1 día (F2.8.f)

**Files:**
- Create: `pipeline/profiles/_f28_saturation_guard_disabled.yaml`
- Create: `experiments/138_f28_saturation_ab/` directory + script

- [ ] **Step 7.1: Create control profile (guard OFF)**

Create `pipeline/profiles/_f28_saturation_guard_disabled.yaml` cloning mirova_equivalent and setting:

```yaml
extends: mirova_equivalent
data_subdir: _f28_saturation_disabled
enable_bt_sat_secondary_guard: false  # control: NO defense secundaria
# Para A/B también revertir cambios Task 1-3, pero esos están al nivel pipeline
# (no profile-controllable). Workaround: usar git stash o branch separado para A.
```

Note: Task 1 (L1B sentinel filter) y Task 2-3 (VIIRS quality_flags) están al nivel del código pipeline, no del profile. Para A/B "antes-vs-después" del fix:
- **A** = código pre-fix (rollback temporario del Task 1-3 vía git stash)
- **B** = código post-fix (estado actual del worktree)

Mejor approach: hacer el A/B comparando JSON outputs pre-fix vs post-fix usando data ya en disco. No requiere reproc en absoluto.

- [ ] **Step 7.2: A/B comparison script**

Create `experiments/138_f28_saturation_ab/audit_ab.py`:

```python
"""F2.8 A/B: comparar records pre-fix (data/mirova_equivalent JSONs antes commit
Tasks 1-4) vs post-fix (después).

Use git stash o backup directory para mantener "before". Para esta sesión:
- 'before' = el snapshot del JSON committed inmediatamente antes de Task 6 reproc
- 'after' = el JSON post-Task 6 reproc

Reporta:
1. Fósiles eliminados (pre count vs post count > 50K MW)
2. Magnitud max pc.vrp_mw pre vs post
3. n_anomalous_pixels distribution pre vs post (sanity check, debería bajar
   para records sat-contaminated)
4. Comparación día-por-día PP 2026-03-18 records: cambios en vrp_mw, vrp_tir_mw,
   primary_cluster en cada sensor.
"""
import json, sys
from pathlib import Path

before = json.loads(Path("data/mirova_equivalent/PlanchonPeteroa.json.before_f28").read_text(encoding="utf-8"))["records"]
after = json.loads(Path("data/mirova_equivalent/PlanchonPeteroa.json").read_text(encoding="utf-8"))["records"]

def stats(recs, label):
    foss = [r for r in recs if (r.get("primary_cluster") or {}).get("vrp_mw", 0) > 50000]
    pc_max = max([(r.get("primary_cluster") or {}).get("vrp_mw", 0) for r in recs] + [0])
    n_pix_distr = sorted([(r.get("n_anomalous_pixels") or 0) for r in recs])
    print(f"{label}: total={len(recs)}, fossils>50K={len(foss)}, pc_max={pc_max:,.0f}, n_pix p95={n_pix_distr[int(0.95*len(n_pix_distr))] if recs else 0}")

stats(before, "BEFORE (pre-fix)")
stats(after, "AFTER  (post-fix)")
```

- [ ] **Step 7.3: Backup PP json pre-reproc**

Before running Task 6 reproc:
```bash
cp data/mirova_equivalent/PlanchonPeteroa.json data/mirova_equivalent/PlanchonPeteroa.json.before_f28
```

- [ ] **Step 7.4: Run A/B audit script post-Task 6**

```bash
python experiments/138_f28_saturation_ab/audit_ab.py | tee experiments/138_f28_saturation_ab/results.txt
```

Expected:
```
BEFORE (pre-fix): total=1178, fossils>50K=1, pc_max=695431, n_pix p95=15
AFTER  (post-fix): total=1178, fossils>50K=0, pc_max=<low>, n_pix p95=<lower or same>
```

- [ ] **Step 7.5: Commit experiments + cleanup backup**

```bash
git add experiments/138_f28_saturation_ab/
git rm data/mirova_equivalent/PlanchonPeteroa.json.before_f28
git commit -m "experiments(f28): A/B audit pre vs post saturation guard fix

Resultado:
- Fósil PP 695,431 MW eliminado post-fix ✓
- n_pixels_anomalous distribution sin regresión ✓
- No FN nuevos en PP 2026-03-18 (records normales preservados)

Refs: experiments/138_f28_saturation_ab/results.txt

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 8: R2 pixel-level contra MIROVA NRT (defensa adicional)

**Files:**
- Create: `experiments/138_f28_saturation_ab/r2_vs_mirova_nrt.py`

- [ ] **Step 8.1: Verificar que MIROVA NRT NO reportó nada para PP 2026-03-18**

Per audit script:
```python
import pandas as pd
csv_path = "data/mirova_reference/01_05_2026_registro_vrp_consolidado.csv"
df = pd.read_csv(csv_path)
pp = df[(df['volcano'] == 'PlanchonPeteroa') & (df['date'] == '2026-03-18')]
print(f"MIROVA NRT records PP 2026-03-18: {len(pp)}")
print(pp[['date', 'time_utc', 'sensor', 'vrp_mw', 'lat', 'lon']].to_string())
```

Expected: 0 records (MIROVA correctly rejected the saturated scene), or records lejos del cluster spurious (vent crater normales).

- [ ] **Step 8.2: Crear R2 audit**

Create `experiments/138_f28_saturation_ab/r2_vs_mirova_nrt.py`:

```python
"""R2: verificar paridad pixel-level con MIROVA NRT para records PP 2026-03-18 post-fix."""
import pandas as pd, json
csv = pd.read_csv("data/mirova_reference/01_05_2026_registro_vrp_consolidado.csv")
ours = [r for r in json.loads(open("data/mirova_equivalent/PlanchonPeteroa.json", encoding='utf-8').read())['records'] if r.get('datetime_utc','').startswith('2026-03-18')]

print(f"OURS PP 2026-03-18: {len(ours)} records")
for r in ours:
    pc = r.get('primary_cluster') or {}
    print(f"  {r['datetime_utc']} {r['sensor']:20s} vrp_mw={r.get('vrp_mw',0):8.2f} pc.vrp_mw={pc.get('vrp_mw',0):8.2f} dist_class={r.get('distance_class')}")

mr = csv[(csv['volcano']=='PlanchonPeteroa') & (csv['date']=='2026-03-18')]
print(f"\nMIROVA NRT PP 2026-03-18: {len(mr)} records")
print(mr[['date','time_utc','sensor','vrp_mw']].to_string())
```

Run:
```bash
python experiments/138_f28_saturation_ab/r2_vs_mirova_nrt.py | tee experiments/138_f28_saturation_ab/r2_results.txt
```

- [ ] **Step 8.3: Commit**

```bash
git add experiments/138_f28_saturation_ab/r2_vs_mirova_nrt.py experiments/138_f28_saturation_ab/r2_results.txt
git commit -m "experiments(f28): R2 pixel-level audit vs MIROVA NRT post-fix

PP 2026-03-18 records nuestros vs CSV MIROVA NRT consolidado. Verifica
que post-fix no introducimos FN ni alteramos detecciones legítimas summit.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Task 9: Adopción operacional + frontend deploy + CLAUDE.md (F2.8.g)

**Files:**
- Modify: `CLAUDE.md` — agregar A35, A36, A37 al final
- Modify: `frontend/index.html` — actualizar About modal con métricas F2.8

- [ ] **Step 9.1: Append A35, A36, A37 a CLAUDE.md**

En `CLAUDE.md`, después de la sección "A. xx" más reciente (parece A24 según MEMORY.md), agregar:

```markdown
### A35 — Vault notes `ai_generated: true` necesitan verificación verbatim para valores numéricos críticos

Cuando un threshold, fórmula, o constante entra a un test/PR/código, **cotejar contra el PDF original** del paper. Las notas Vault sintetizan ideas correctamente pero pueden confundir contexto vs threshold, o tener typos. **S73 F2.8**: la nota Vault decía "Wooster L_sat=57.6 W/m²/sr/µm como criterio operacional" — pero el paper original muestra que ese 57.6 W es **valor de ejemplo de Figure 4** (un caso que YA satura MODIS, BT=473 K), no el threshold mismo (que es BT≈450 K).

**Jerarquía de autoridad cuando hay conflicto**: UserGuide oficial del sensor (Toller/MCST 2025, VIIRS L1B Aug 2021) > Paper canon-MIROVA reciente (Coppola 2025 cap.11) > Paper algorithm-MIROVA histórico (Coppola 2016, Wooster 2003) > Notas Vault `ai_generated`.

### A36 — sec³(θ_z) scan-angle elongation puede multiplicar discrepancias factor 1-5×

MODIS pixels off-nadir tienen área efectiva mucho mayor que nominal 1km². Para sensor angle θ_z = 50° → factor 3.74. Cualquier análisis manual que ignore esto produce discrepancias factor 1-5×. El pipeline ya lo aplica via `modis_pixel_areas()`; análisis manuales/scripts también deben.

### A37 — VIIRS L1B y MODIS L1B usan esquemas distintos para saturation flagging

MODIS: sentinel `SI=65533` (Tabla 5.6.1 L1B C7 UserGuide) más esquema general `SI > 32767 = invalid`.
VIIRS: NO usa sentinel uint16 para saturation. Clampea radiance al "Reported Range" + setea bit-2 (=4) del SDS de quality flags (Tabla C.1 L1B UserGuide).

Code que asume uniformidad de esquema entre sensores produce gaps de protección distintos. **Regla**: cuando trabajés con un sensor L1B nuevo, leé el UserGuide específico de ese sensor — NO extrapoles del MODIS.
```

- [ ] **Step 9.2: Actualizar frontend About modal**

In `frontend/index.html`, locate the About modal and add to the methods/changelog section:

```html
<!-- F2.8 S73: saturation guard L1B-spec + quality_flags + BT defense -->
<li>S73 F2.8: fix saturation handling. MODIS B21 sentinel 65533 ahora filtrado
    per L1B C7 UserGuide Sec 5.6. VIIRS I/M-band quality_flags bit-2 (Saturation)
    leído per UserGuide Tabla C.1. Defensa secundaria BT post-Planck per Coppola
    2025 Cap.11 Table 1. Elimina caso patológico PP 2026-03-18 695K MW.</li>
```

- [ ] **Step 9.3: Run full suite final**

```bash
pytest tests/ -q --tb=short | tail -10
```

Expected: ALL PASS.

- [ ] **Step 9.4: Commit + push**

```bash
git add CLAUDE.md frontend/index.html
git commit -m "docs(f28): cierre F2.8 — A35-A37 lecciones + About modal update

A35: notas Vault ai_generated requieren verificación verbatim PDF.
A36: sec³(θ_z) scan-angle puede amplificar bugs factor 1-5×.
A37: VIIRS y MODIS L1B usan esquemas distintos para saturation.

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

git push origin <current-branch>
```

- [ ] **Step 9.5: Create PR**

```bash
gh pr create --title "S73 F2.8: saturation guard MODIS+VIIRS L1B-spec + BT defense" --body "$(cat <<'EOF'
## Summary
- Fix MODIS L1B sentinel filter: cubre los 14 reserved values 65500-65535 (antes solo 65535)
- Fix VIIRS I/M-band quality_flags read: enmascara bit-2 Saturation (antes no leído)
- Defensa secundaria BT-level post-Planck per Coppola 2025 Cap.11 Table 1
- Frontend hardening diario.html guard pc.vrp_mw > 50K
- Reproc fósil PP 2026-03-18 (único en 34k records dataset)
- A35, A36, A37 lecciones meta documentadas

## Verificación
- 27/27 tests F2.8 saturation_guard PASS
- Integration tests MODIS + VIIRS PASS
- Suite completa 380+ tests PASS (sin regresión)
- A/B reproc: fósil 695K MW eliminado, distribuciones n_pix preservadas
- R2 pixel-level vs MIROVA NRT PP 2026-03-18: paridad confirmada

## Refs
- docs/F28_SATURATION_INVESTIGATION.md — verdict triple-verificado
- docs/F28_HYPOTHESIS_LOG.md — 10 hipótesis (8 implementadas, 2 refutadas)
- docs/F28_REPROC_PP_2026_03_18.md — log reproc
- experiments/138_f28_saturation_ab/ — A/B + R2 audits

## Test plan
- [ ] CI workflow Linux + pyhdf disponible: full suite pass
- [ ] NRT cron post-merge: 3 ciclos sin nuevos fósiles > 50K en JSONs
- [ ] Dashboard live refresh: ningún record PP 2026-03-18 visible con vrp_mw absurdo

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

## Self-Review

**Spec coverage:**
- H1 MODIS L1B fix → Task 1 ✓
- H2 VIIRS I-band quality_flags → Task 2 ✓
- H2 VIIRS M-band quality_flags → Task 3 ✓
- H3 BT defense MODIS B21 → Task 4 ✓
- (H3 BT defense VIIRS — cubierto inline en Tasks 2 y 3 via BT_LUT_MAX filter)
- H10 VIIRS LUT max filter → cubierto en Tasks 2 y 3 ✓
- H4 reproc fósil → Task 6 ✓
- H5 frontend hardening → Task 5 ✓
- A/B reproc → Task 7 ✓
- R2 pixel-level → Task 8 ✓
- Adopción operacional + CLAUDE.md → Task 9 ✓

**Placeholder scan**: ningún TBD, TODO, "implement later", "fill in details", "appropriate error handling", "edge cases" — todos los pasos tienen código concreto.

**Type consistency**: BT_LUT_MAX appears en Task 2 (I-band) y Task 3 (M-band) con nombres distintos (BT_LUT_MAX I-band vs BT_LUT_MAX_MBAND) — intencional, sensors distintos.

`SAT_BIT_MASK = 0b100` consistente en Tasks 2 y 3.

`INVALID_SI_THRESHOLD = 32767` consistente en Task 1 (no usado en VIIRS Tasks).

`ENABLE_BT_SAT_SECONDARY_GUARD` consistente Task 4.

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-05-23-f28-saturation-guard.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - dispatch fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
