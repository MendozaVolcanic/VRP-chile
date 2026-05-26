# F66 Híbrido — Dual-bg Consistency Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar el gate de consistencia secundario con kernel local 3×3 sobre los 3 procesadores (MODIS, VIIRS-I 375m, VIIRS-M 750m), validar Fase 1 (3 vol × 30d), preparar PR sin merge a operacional.

**Architecture:** Helper único `apply_f66_consistency_gate()` en `pipeline/detection_context.py` (DRY) que recibe `bt + hot_mask + kernel + dt_min`, computa `t_bg_local` per pixel via `compute_local_background()` existente, y filtra pixels con `ΔT_local < dt_min` (excepto NaN fallback). Cada `process_*.py` llama al helper post-`hot_mask` y persiste diag. Profile flag aislado `_f66_dt5k.yaml` con `data_subdir` propio — NO toca operacional.

**Tech Stack:** Python 3.12, numpy, pyyaml, pytest, earthaccess. pipeline/vrp_regimes.py:21 ya tiene `compute_local_background()` (NO recrear).

---

## File Structure

**Files to create:**
- `tests/test_f66_bg_kernel_consistency.py` — 7 tests sintéticos cubriendo escenarios físicos canónicos
- `pipeline/profiles/_f66_dt5k.yaml` — profile dedicado Fase 1, `data_subdir: f66_dt5k`
- `experiments/152_f66_audit_phase1/audit.py` — audit comparativo post-reproc
- `experiments/152_f66_audit_phase1/r2_pixel_level.md` — R2 vs MIROVA web 5 records × 3 vol
- `docs/F66_RESULTS_PHASE1_S79.md` — resultados + decisión Fase 2/3

**Files to modify:**
- `pipeline/detection_context.py` — agregar helper `apply_f66_consistency_gate()` después de `compute_bg_stats` (~line 940)
- `pipeline/profile.py` — agregar 3 nuevos campos `enable_bg_kernel_consistency_gate`, `kernel_consistency_dt_k`, `kernel_consistency_size` (~line 90)
- `pipeline/process_viirs.py` — invocación helper post hot_mask (~line 720)
- `pipeline/process_viirs_mod.py` — invocación helper post hot_mask (~line 475)
- `pipeline/process_modis.py` — invocación helper post hot_mask (~line 430)

**Files explicitly NOT modified:**
- `pipeline/vrp_regimes.py` — `compute_local_background()` se reutiliza tal cual
- `volcanoes.yaml` — sin cambios per-vol (gate uniforme Fase 1)
- `pipeline/profiles/mirova_equivalent.yaml` — sin cambios (gate default OFF; Fase 3 lo enciende en otra sesión)

---

## Task 0: Setup defensivo A45 (BLOQUEANTE — confirmación Nicolás)

**Files:** (sin cambios de código)

- [ ] **Step 1: Verificar baseline tests verde antes de tocar nada**

Run: `cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP-Chile-s79-f66" && python -m pytest tests/ -q --tb=no 2>&1 | tail -5`
Expected: `507 passed, 24 skipped` (o número ≥ ese; cualquier failure detiene plan)

- [ ] **Step 2: Crear tag defensivo apuntando a origin/main**

```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP-Chile-s79-f66"
git tag pre-s79-f66-hybrid 9d4dd082
git push origin pre-s79-f66-hybrid
git rev-parse pre-s79-f66-hybrid
```

Expected output: `9d4dd082b86d57e809d831d605f61a7131afddb0`

- [ ] **Step 3: Pedir confirmación A45 explícita a Nicolás**

Use AskUserQuestion con:
- Question: "Tag defensivo `pre-s79-f66-hybrid` creado. ¿Confirmás avanzar a TDD + implementación pipeline?"
- Header: "Confirmación A45"
- Options:
  - "Confirmo, avanzar TDD"
  - "Hacer una verificación más antes"
  - "Pausar, revisar plan de nuevo"

NO avanzar a Task 1 hasta tener "Confirmo".

---

## Task 1: Helper apply_f66_consistency_gate + test inicial (TDD red→green)

**Files:**
- Create: `tests/test_f66_bg_kernel_consistency.py`
- Modify: `pipeline/detection_context.py` (agregar después de línea ~940)

- [ ] **Step 1: Write the failing test (test 1/7 — lago uniforme vetado)**

Create `tests/test_f66_bg_kernel_consistency.py`:

```python
"""Tests sintéticos F66 dual-bg consistency gate (S79 P1).

Cubre 7 escenarios físicos canónicos en pipeline VRP Chile:
1. Lago uniforme tibio (Caviahue/Conguillío) → vetado
2. Lava lake sub-pixel (Villarrica) → válido
3. Lava extendida cluster (vecinos hot) → fallback ring válido
4. Cirrus dispersa (vecinos cirrus aún más fríos) → válido pero cap D9 limita VRP
5. Salar borde halita (Lascar) → vetado borderline
6. Pixel borde imagen vecinos NaN → fallback válido
7. dNTI dual-ROI Path D compat (regression no rompe path existente)
"""
import numpy as np
import pytest

from pipeline.detection_context import apply_f66_consistency_gate


def test_lake_uniform_vetoed():
    """Lago Caviahue uniforme 278K + pixel central 279K: ΔT=1K < 5K → vetado."""
    bt = np.full((10, 10), 278.0)
    bt[5, 5] = 279.0
    hot_mask = np.zeros((10, 10), dtype=bool)
    hot_mask[5, 5] = True

    hot_mask_out, diag = apply_f66_consistency_gate(
        bt, hot_mask, kernel_size=3, dt_min=5.0
    )

    assert hot_mask_out[5, 5] == False, "Pixel lago uniforme debe ser vetado"
    assert diag["n_evaluated"] == 1
    assert diag["n_vetoed"] == 1
    assert diag["n_nan_fallback"] == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_f66_bg_kernel_consistency.py::test_lake_uniform_vetoed -v 2>&1 | tail -10`
Expected: FAIL with `ImportError: cannot import name 'apply_f66_consistency_gate' from 'pipeline.detection_context'`

- [ ] **Step 3: Write minimal implementation**

Edit `pipeline/detection_context.py`, append after `compute_bg_stats` (after line 938):

```python


# ---------------------------------------------------------------------------
# F66 Dual-bg consistency gate (S79 P1, design doc 2026-05-26)
#
# Filtra pixels donde el "calor" es un artefacto del background ring 5-25 km
# (lago tibio rodeado de terreno frío distante) vs señal espacial real.
#
# MIROVA-faithful: Coppola 2024 L1129 + Coppola 2016a L240-249 + L357-359 +
# Campus 2024 L119-124 verbatim usan background local (vecinos inmediatos
# 3×3 = 8-conn) — nuestro pipeline usa ring annular, que es un drift.
# Este helper actúa como gate de consistencia secundario PRESERVANDO la
# arquitectura ring (gate primario sin cambios).
#
# Edge cases:
#   - Todos vecinos hot/NaN → t_bg_local = NaN → fallback ring (no vetar)
#   - Algunos vecinos NaN → mean(válidos)
#   - Pixel borde imagen → vecinos truncados, mismo fallback
# ---------------------------------------------------------------------------


def apply_f66_consistency_gate(
    bt: np.ndarray,
    hot_mask: np.ndarray,
    *,
    kernel_size: int = 3,
    dt_min: float = 5.0,
) -> tuple[np.ndarray, dict]:
    """Apply F66 dual-bg consistency gate sobre hot_mask del ring.

    Para cada pixel marcado hot por gate primario (ring 5-25 km), computa
    t_bg_local con kernel 3×3 (vecinos inmediatos) excluyendo otros hot y
    NaN. Si ΔT_local = bt - t_bg_local < dt_min → vetar.

    Política edge case: si t_bg_local es NaN (todos vecinos hot o NaN) →
    fallback ring (no vetar) para preservar recall en lava extendida.

    Args:
        bt: 2D array BT en K.
        hot_mask: bool 2D, True para pixels marcados hot por gate primario.
        kernel_size: lado kernel cuadrado (impar). Default 3 = 8 vecinos.
        dt_min: ΔT_local mínimo en K para que pixel pase el gate.

    Returns:
        (hot_mask_filtered, diag_dict) donde diag_dict tiene:
            n_evaluated: pixels que entraron al gate (= hot_mask.sum())
            n_vetoed: pixels rechazados por ΔT < dt_min
            n_nan_fallback: pixels con t_bg_local NaN (passed por fallback)
    """
    from pipeline.vrp_regimes import compute_local_background

    hot_rows_arr, hot_cols_arr = np.where(hot_mask)
    n_evaluated = int(hot_rows_arr.size)

    if n_evaluated == 0:
        return hot_mask.copy(), {
            "n_evaluated": 0,
            "n_vetoed": 0,
            "n_nan_fallback": 0,
        }

    t_bg_locals = compute_local_background(
        bt, hot_rows_arr.tolist(), hot_cols_arr.tolist(),
        kernel_size=kernel_size,
    )
    t_bg_locals_arr = np.asarray(t_bg_locals, dtype=float)
    delta_t_local = bt[hot_rows_arr, hot_cols_arr] - t_bg_locals_arr
    nan_fallback = np.isnan(t_bg_locals_arr)
    passes = (delta_t_local >= dt_min) | nan_fallback

    hot_mask_out = np.zeros_like(hot_mask)
    hot_mask_out[hot_rows_arr[passes], hot_cols_arr[passes]] = True

    diag = {
        "n_evaluated": n_evaluated,
        "n_vetoed": int((~passes).sum()),
        "n_nan_fallback": int(nan_fallback.sum()),
    }
    return hot_mask_out, diag
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_f66_bg_kernel_consistency.py::test_lake_uniform_vetoed -v 2>&1 | tail -10`
Expected: `1 passed`

- [ ] **Step 5: Commit**

```bash
git add tests/test_f66_bg_kernel_consistency.py pipeline/detection_context.py
git commit -m "feat(detection_context): F66 dual-bg consistency gate helper + test 1/7

apply_f66_consistency_gate() reusa compute_local_background (vrp_regimes.py:21)
sobre hot_mask del gate primario ring. Pixels con ΔT_local < dt_min vetados;
fallback ring para vecinos NaN/hot (preserva recall lava extendida).

MIROVA-faithful: Coppola 2024 L1129 + Coppola 2016a L240-249 + Campus 2024
L119-124 verbatim usan bg local 8-conn.

Test 1/7: lago uniforme vetado (Caviahue/Copahue patrón).

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: 6 tests sintéticos adicionales (regression coverage)

**Files:**
- Modify: `tests/test_f66_bg_kernel_consistency.py`

- [ ] **Step 1: Agregar 6 tests adicionales**

Append a `tests/test_f66_bg_kernel_consistency.py`:

```python


def test_lava_lake_sub_pixel_passes():
    """Lava lake Villarrica sub-pixel: vecinos fríos 270K, pixel 285K → ΔT=15K → válido."""
    bt = np.full((10, 10), 270.0)
    bt[5, 5] = 285.0
    hot_mask = np.zeros((10, 10), dtype=bool)
    hot_mask[5, 5] = True

    hot_mask_out, diag = apply_f66_consistency_gate(
        bt, hot_mask, kernel_size=3, dt_min=5.0
    )

    assert hot_mask_out[5, 5] == True
    assert diag["n_vetoed"] == 0


def test_extended_lava_cluster_fallback():
    """Cluster lava extendida 5×5 todos hot: t_bg_local NaN → fallback válido."""
    bt = np.full((10, 10), 270.0)
    bt[3:8, 3:8] = 320.0
    hot_mask = np.zeros((10, 10), dtype=bool)
    hot_mask[3:8, 3:8] = True

    hot_mask_out, diag = apply_f66_consistency_gate(
        bt, hot_mask, kernel_size=3, dt_min=5.0
    )

    # Pixels en bordes del cluster tienen vecinos no-hot fuera del cluster
    # → ΔT_local grande → pasa. Pixel central [5,5] tiene los 8 vecinos
    # también hot → NaN → fallback (pasa).
    assert hot_mask_out[5, 5] == True, "Pixel central cluster con todos vecinos hot debe pasar (fallback)"
    assert hot_mask_out.sum() == 25, "Todos los 25 pixels del cluster preservados"
    assert diag["n_nan_fallback"] >= 1


def test_cirrus_dispersed_passes():
    """Pixel cráter caliente 295K rodeado de cirrus fría 245K → ΔT=50K → válido.

    F66 NO veta este caso. El cap D9=5MW del profile (otro path) maneja
    el VRP inflado downstream. F66 solo decide entrada a hot_mask.
    """
    bt = np.full((10, 10), 245.0)  # cirrus cubriendo escena
    bt[5, 5] = 295.0  # cráter caliente real
    hot_mask = np.zeros((10, 10), dtype=bool)
    hot_mask[5, 5] = True

    hot_mask_out, diag = apply_f66_consistency_gate(
        bt, hot_mask, kernel_size=3, dt_min=5.0
    )

    assert hot_mask_out[5, 5] == True
    assert diag["n_vetoed"] == 0


def test_border_pixel_nan_fallback():
    """Pixel en (0,0) con vecinos fuera de imagen + NaN: fallback ring válido."""
    bt = np.full((10, 10), 270.0)
    bt[0, 0] = 285.0
    bt[0, 1] = np.nan  # vecino NaN
    bt[1, 0] = np.nan
    bt[1, 1] = np.nan
    # Todos los vecinos válidos del kernel 3×3 son NaN → t_bg_local NaN
    hot_mask = np.zeros((10, 10), dtype=bool)
    hot_mask[0, 0] = True

    hot_mask_out, diag = apply_f66_consistency_gate(
        bt, hot_mask, kernel_size=3, dt_min=5.0
    )

    assert hot_mask_out[0, 0] == True, "Border pixel con vecinos NaN debe pasar fallback"
    assert diag["n_nan_fallback"] == 1


def test_salar_border_halita_vetoed():
    """Salar Atacama Lascar borde halita: vecinos 277K, pixel 280K → ΔT=3K < 5K → vetado."""
    bt = np.full((10, 10), 270.0)
    bt[3:6, 3:6] = 277.0  # halita Salar
    bt[4, 4] = 280.0  # pixel central marginal
    hot_mask = np.zeros((10, 10), dtype=bool)
    hot_mask[4, 4] = True

    hot_mask_out, diag = apply_f66_consistency_gate(
        bt, hot_mask, kernel_size=3, dt_min=5.0
    )

    assert hot_mask_out[4, 4] == False, "Pixel Salar borde con vecinos halita debe ser vetado"
    assert diag["n_vetoed"] == 1


def test_empty_hot_mask():
    """Hot mask vacío: no-op, no errores."""
    bt = np.full((10, 10), 270.0)
    hot_mask = np.zeros((10, 10), dtype=bool)

    hot_mask_out, diag = apply_f66_consistency_gate(
        bt, hot_mask, kernel_size=3, dt_min=5.0
    )

    assert hot_mask_out.sum() == 0
    assert diag["n_evaluated"] == 0
    assert diag["n_vetoed"] == 0


def test_dnti_dual_roi_path_d_compat():
    """Regression: F66 gate NO interfiere con dNTI dual-ROI Path D existente.

    Path D dispara con dnti > C1 contextual; F66 actúa sobre el hot_mask
    resultante. Pixel que pasa Path D + tiene ΔT_local válida → pasa ambos.
    """
    # Escenario: pixel central 285K con vecinos 270K (lava lake sub-pixel).
    # Si llegó aquí significa Path D ya disparó (dnti residual positivo).
    # F66 debe confirmar (ΔT_local = 15K >> 5K).
    bt = np.full((20, 20), 270.0)
    bt[10, 10] = 285.0
    hot_mask = np.zeros((20, 20), dtype=bool)
    hot_mask[10, 10] = True  # Path D dispara este pixel

    hot_mask_out, diag = apply_f66_consistency_gate(
        bt, hot_mask, kernel_size=3, dt_min=5.0
    )

    assert hot_mask_out[10, 10] == True, "Path D pixel debe sobrevivir F66 gate"
    assert diag["n_vetoed"] == 0
```

- [ ] **Step 2: Run 7 tests, verificar todos green**

Run: `python -m pytest tests/test_f66_bg_kernel_consistency.py -v 2>&1 | tail -15`
Expected: `7 passed`

- [ ] **Step 3: Commit**

```bash
git add tests/test_f66_bg_kernel_consistency.py
git commit -m "test(F66): 6 tests sintéticos adicionales (escenarios 2-7)

Cobertura completa escenarios físicos canónicos:
- Lava lake sub-pixel Villarrica (pasa, ΔT=15K)
- Cluster lava extendida fallback ring (preserva recall)
- Cirrus dispersa (pasa F66, cap D9 limita VRP downstream)
- Border pixel NaN fallback
- Salar borde halita Lascar (vetado, ΔT=3K<5K)
- dNTI dual-ROI Path D compat regression

7/7 tests passing.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: Profile parsing en profile.py

**Files:**
- Modify: `pipeline/profile.py` (después de NTI_K1_NIGHT, línea ~87)

- [ ] **Step 1: Write failing test for profile parsing**

Append a `tests/test_f66_bg_kernel_consistency.py`:

```python


def test_profile_defaults_f66_off():
    """Profile mirova_equivalent debe tener F66 default OFF."""
    from pipeline.profile import Profile

    p = Profile.load("mirova_equivalent")

    assert p.enable_bg_kernel_consistency_gate == False
    assert p.kernel_consistency_dt_k == 5.0  # default = anomaly_threshold_k
    assert p.kernel_consistency_size == 3
```

- [ ] **Step 2: Run test, verificar fail**

Run: `python -m pytest tests/test_f66_bg_kernel_consistency.py::test_profile_defaults_f66_off -v 2>&1 | tail -10`
Expected: FAIL with `AttributeError: 'Profile' object has no attribute 'enable_bg_kernel_consistency_gate'`

- [ ] **Step 3: Read current profile.py loading code**

Run: `python -c "from pathlib import Path; import re; t = Path('pipeline/profile.py').read_text(encoding='utf-8'); print(t[t.find('NTI_K1_NIGHT'):t.find('NTI_K1_NIGHT')+800])"`

Inspeccionar el patrón usado para definir nuevos campos del profile.

- [ ] **Step 4: Implement profile fields**

Edit `pipeline/profile.py`. Buscar la sección de carga de thresholds (cerca línea 87 donde está `NTI_K1_NIGHT: float = float(_t["nti_k1_night"])`) y agregar después:

```python
# F66 dual-bg consistency gate (S79, design doc 2026-05-26)
# Filtra pixels con ΔT_local < dt_min usando kernel 3×3 vecinos inmediatos
# (Coppola 2016a verbatim). Default OFF en mirova_equivalent; ON en profiles
# dedicados (_f66_dt5k.yaml). Ver pipeline/detection_context.py:apply_f66_consistency_gate
enable_bg_kernel_consistency_gate: bool = bool(
    _t.get("enable_bg_kernel_consistency_gate", False)
)
kernel_consistency_dt_k: float = float(
    _t.get("kernel_consistency_dt_k", _t.get("anomaly_threshold_k", 5.0))
)
kernel_consistency_size: int = int(_t.get("kernel_consistency_size", 3))
```

Si el archivo usa dataclass con __init__ explícito, agregar los 3 campos como atributos en el `__init__` y leerlos desde `_t` ahí. Si usa parseo procedural, agregarlos como variables módulo después de NTI_K1_NIGHT.

- [ ] **Step 5: Run test, verificar pass**

Run: `python -m pytest tests/test_f66_bg_kernel_consistency.py::test_profile_defaults_f66_off -v 2>&1 | tail -10`
Expected: `1 passed`

- [ ] **Step 6: Verify baseline tests aún green**

Run: `python -m pytest tests/ -q --tb=no 2>&1 | tail -5`
Expected: `508 passed, 24 skipped` (era 507, ahora +1 test F66)

- [ ] **Step 7: Commit**

```bash
git add pipeline/profile.py tests/test_f66_bg_kernel_consistency.py
git commit -m "feat(profile): F66 gate parameters parsing default OFF

3 nuevos campos en Profile:
- enable_bg_kernel_consistency_gate (bool, default False)
- kernel_consistency_dt_k (float, default = anomaly_threshold_k = 5.0)
- kernel_consistency_size (int, default 3 = 8-conn kernel)

Activación solo en profiles dedicados (_f66_dt5k.yaml siguiente).
Test profile defaults F66 OFF en mirova_equivalent.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: Integración en process_viirs.py (375m I-band)

**Files:**
- Modify: `pipeline/process_viirs.py` (cerca línea 720, post hot_mask compute)

- [ ] **Step 1: Read current hot_mask compute region**

Run: `grep -n "hot_mask" pipeline/process_viirs.py | head -20`

Identificar la línea donde `hot_mask` queda final (post merge de Path A/B/C/D/Test1) y donde comienza el bloque que extrae hot pixels para cálculo de VRP.

- [ ] **Step 2: Add F66 gate invocation post hot_mask**

Edit `pipeline/process_viirs.py`. Después del bloque donde `hot_mask` queda computado en su forma final (line ~720 según grep) y ANTES del bloque que extrae hot pixels para cómputo VRP, insertar:

```python
        # F66 dual-bg consistency gate (S79 P1, design doc 2026-05-26)
        # Filtra pixels donde gate ring marcó hot pero kernel local 3×3
        # muestra ΔT_local < dt_min (lago tibio, Salar borde, halita).
        # Fallback ring para vecinos NaN/hot (preserva lava extendida).
        if profile.enable_bg_kernel_consistency_gate:
            from pipeline.detection_context import apply_f66_consistency_gate

            hot_mask, f66_diag = apply_f66_consistency_gate(
                bt_i4,  # BT MIR I04 (canal de detección)
                hot_mask,
                kernel_size=profile.kernel_consistency_size,
                dt_min=profile.kernel_consistency_dt_k,
            )
            record_diag["f66_n_evaluated"] = f66_diag["n_evaluated"]
            record_diag["f66_n_vetoed"] = f66_diag["n_vetoed"]
            record_diag["f66_n_nan_fallback"] = f66_diag["n_nan_fallback"]
```

NOTA: el nombre exacto de la variable BT usada en `process_viirs.py` puede ser `bt_i4`, `bt`, o `bt_mir`. Verificar con grep y usar el nombre exacto. También verificar nombre del dict de diagnóstico (`record_diag`, `diag`, etc).

- [ ] **Step 3: Verify import compiles**

Run: `python -c "from pipeline import process_viirs"`
Expected: sin errores (sin output o solo warnings).

- [ ] **Step 4: Run baseline tests + F66 tests aún green**

Run: `python -m pytest tests/ -q --tb=short 2>&1 | tail -10`
Expected: `508 passed, 24 skipped` (sin regresiones).

- [ ] **Step 5: Commit**

```bash
git add pipeline/process_viirs.py
git commit -m "feat(process_viirs): integrar F66 gate en VIIRS I-band 375m

Invocación condicional apply_f66_consistency_gate() post hot_mask cuando
flag enable_bg_kernel_consistency_gate=True. Persistir diag fields
(n_evaluated, n_vetoed, n_nan_fallback) al record.

Sin cambio comportamiento cuando flag OFF (mirova_equivalent default).

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: Integración en process_viirs_mod.py (750m M-band)

**Files:**
- Modify: `pipeline/process_viirs_mod.py` (cerca línea 475, post hot_mask compute)

- [ ] **Step 1: Read current hot_mask compute region**

Run: `grep -n "hot_mask" pipeline/process_viirs_mod.py | head -20`

- [ ] **Step 2: Add F66 gate invocation idéntico a Task 4**

Edit `pipeline/process_viirs_mod.py`. Mismo patrón que Task 4 Step 2 pero usando la variable BT correcta para M13 (probablemente `bt_m13` o `bt`).

```python
        # F66 dual-bg consistency gate (S79 P1, design doc 2026-05-26)
        if profile.enable_bg_kernel_consistency_gate:
            from pipeline.detection_context import apply_f66_consistency_gate

            hot_mask, f66_diag = apply_f66_consistency_gate(
                bt_m13,  # BT MIR M13 (canal de detección VIIRS M-band)
                hot_mask,
                kernel_size=profile.kernel_consistency_size,
                dt_min=profile.kernel_consistency_dt_k,
            )
            record_diag["f66_n_evaluated"] = f66_diag["n_evaluated"]
            record_diag["f66_n_vetoed"] = f66_diag["n_vetoed"]
            record_diag["f66_n_nan_fallback"] = f66_diag["n_nan_fallback"]
```

- [ ] **Step 3: Verify import compiles**

Run: `python -c "from pipeline import process_viirs_mod"`
Expected: sin errores.

- [ ] **Step 4: Run all tests**

Run: `python -m pytest tests/ -q --tb=short 2>&1 | tail -10`
Expected: `508 passed, 24 skipped`.

- [ ] **Step 5: Commit**

```bash
git add pipeline/process_viirs_mod.py
git commit -m "feat(process_viirs_mod): integrar F66 gate en VIIRS M-band 750m

Mismo patrón Task 4 (process_viirs.py). DRY: reusa apply_f66_consistency_gate
helper en detection_context.py.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 6: Integración en process_modis.py (B21/22 1km)

**Files:**
- Modify: `pipeline/process_modis.py` (cerca línea 430, post hot_mask compute)

- [ ] **Step 1: Read current hot_mask compute region**

Run: `grep -n "hot_mask" pipeline/process_modis.py | head -20`

- [ ] **Step 2: Add F66 gate invocation idéntico**

Edit `pipeline/process_modis.py`. Mismo patrón pero usando la variable BT correcta para B21/22 (probablemente `bt_mir` con fallback B22→B21).

```python
        # F66 dual-bg consistency gate (S79 P1, design doc 2026-05-26)
        if profile.enable_bg_kernel_consistency_gate:
            from pipeline.detection_context import apply_f66_consistency_gate

            hot_mask, f66_diag = apply_f66_consistency_gate(
                bt_mir,  # BT MIR B22 (primary) o B21 (fallback)
                hot_mask,
                kernel_size=profile.kernel_consistency_size,
                dt_min=profile.kernel_consistency_dt_k,
            )
            record_diag["f66_n_evaluated"] = f66_diag["n_evaluated"]
            record_diag["f66_n_vetoed"] = f66_diag["n_vetoed"]
            record_diag["f66_n_nan_fallback"] = f66_diag["n_nan_fallback"]
```

- [ ] **Step 3: Verify import compiles (skip si pyhdf no disponible Windows)**

Run: `python -c "from pipeline import process_modis" 2>&1 | head -5`
Expected: sin errores, O warning sobre pyhdf no disponible (esperado Windows — no bloqueante).

- [ ] **Step 4: Run all tests**

Run: `python -m pytest tests/ -q --tb=short 2>&1 | tail -10`
Expected: `508 passed, 24 skipped`.

- [ ] **Step 5: Commit**

```bash
git add pipeline/process_modis.py
git commit -m "feat(process_modis): integrar F66 gate en MODIS 1km

Mismo patrón Task 4/5. Cobertura completa los 3 procesadores.

Reproc MODIS solo via GitHub Actions Linux (pyhdf roto Windows). Fase 1
validación usa VIIRS-only en local Nicolás.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 7: Profile yaml dedicado _f66_dt5k.yaml

**Files:**
- Create: `pipeline/profiles/_f66_dt5k.yaml`

- [ ] **Step 1: Create profile file**

Create `pipeline/profiles/_f66_dt5k.yaml`:

```yaml
# VRP-Chile — profile: _f66_dt5k (S79 Fase 1 A/B test)
#
# Test del F66 híbrido dual-bg consistency gate con threshold 5K
# (= anomaly_threshold_k mirova_equivalent, coherencia interna).
#
# Design doc: docs/superpowers/specs/2026-05-26-f66-hybrid-bg-kernel-consistency-gate-design.md
# Plan: docs/superpowers/plans/2026-05-26-f66-hybrid-bg-kernel-consistency-gate.md
#
# Objetivo Fase 1: validar reducción FPs lago en Copahue/Llaima/Villarrica
# sin perder TPs reales. NO operacional hasta Fase 3 (mergear flag en
# mirova_equivalent post-validación).

extends: mirova_equivalent

profile: _f66_dt5k
description: >
  F66 híbrido dual-bg consistency gate ON con kernel 3×3 y threshold 5K.
  Profile A/B aislado — NO contamina operacional.
data_subdir: f66_dt5k

thresholds:
  # Override mirova_equivalent: activar gate F66
  enable_bg_kernel_consistency_gate: true
  kernel_consistency_dt_k: 5.0
  kernel_consistency_size: 3
```

- [ ] **Step 2: Verify profile loads correctly**

Run: `python -c "from pipeline.profile import Profile; p = Profile.load('_f66_dt5k'); print(f'enable_f66={p.enable_bg_kernel_consistency_gate} dt_k={p.kernel_consistency_dt_k} kernel={p.kernel_consistency_size} data_subdir={p.data_subdir}')"`
Expected: `enable_f66=True dt_k=5.0 kernel=3 data_subdir=f66_dt5k`

- [ ] **Step 3: Add profile loading test**

Append a `tests/test_f66_bg_kernel_consistency.py`:

```python


def test_profile_f66_dt5k_loads_with_overrides():
    """Profile _f66_dt5k debe heredar mirova_equivalent + override F66 ON."""
    from pipeline.profile import Profile

    p = Profile.load("_f66_dt5k")

    assert p.enable_bg_kernel_consistency_gate == True
    assert p.kernel_consistency_dt_k == 5.0
    assert p.kernel_consistency_size == 3
    assert p.data_subdir == "f66_dt5k"
    # Hereda de mirova_equivalent
    assert p.anomaly_threshold_k == 5.0  # mismo valor base
```

- [ ] **Step 4: Run profile test**

Run: `python -m pytest tests/test_f66_bg_kernel_consistency.py::test_profile_f66_dt5k_loads_with_overrides -v 2>&1 | tail -10`
Expected: `1 passed`

- [ ] **Step 5: Commit**

```bash
git add pipeline/profiles/_f66_dt5k.yaml tests/test_f66_bg_kernel_consistency.py
git commit -m "feat(profile): _f66_dt5k.yaml dedicado Fase 1 A/B test

Profile aislado con extends: mirova_equivalent + override enable_f66=true,
dt_k=5.0, kernel=3. data_subdir=f66_dt5k separa output del operacional.

NO contamina mirova_equivalent. Fase 1 reproc compara data/f66_dt5k/ vs
data/mirova_equivalent/ en mismos 3 vol × 30d.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 8: Baseline tests + sanity check end-to-end

**Files:** (sin cambios de código)

- [ ] **Step 1: Run full test suite**

Run: `python -m pytest tests/ -q --tb=short 2>&1 | tail -10`
Expected: `509 passed, 24 skipped` (508 base + 1 nuevo test profile loading)

- [ ] **Step 2: Smoke test del helper standalone con escenario real-like**

Run:
```bash
python -c "
import numpy as np
from pipeline.detection_context import apply_f66_consistency_gate

# Escenario mixto: lago + cráter + cluster + cirrus en mismo array
bt = np.full((30, 30), 270.0)
bt[5:8, 5:8] = 279.0   # lago 3x3 Caviahue
bt[15, 15] = 285.0     # lava lake sub-pixel Villarrica
bt[20:25, 20:25] = 320.0  # cluster lava extendida
bt[10, 25] = 295.0     # cráter con cirrus
bt[9:12, 24:27] = np.where(bt[9:12, 24:27] == 270.0, 245.0, bt[9:12, 24:27])  # cirrus

hot_mask = np.zeros((30, 30), dtype=bool)
hot_mask[6, 6] = True      # lago candidato (debe vetar)
hot_mask[15, 15] = True    # lava lake (debe pasar)
hot_mask[22, 22] = True    # cluster centro (fallback)
hot_mask[10, 25] = True    # cirrus crater (pasa)

out, diag = apply_f66_consistency_gate(bt, hot_mask, kernel_size=3, dt_min=5.0)
print(f'Diag: {diag}')
print(f'Lago vetado: {not out[6, 6]}')
print(f'Lava lake pasa: {out[15, 15]}')
print(f'Cluster fallback: {out[22, 22]}')
print(f'Cirrus crater pasa: {out[10, 25]}')
"
```

Expected:
```
Diag: {'n_evaluated': 4, 'n_vetoed': 1, 'n_nan_fallback': 1}
Lago vetado: True
Lava lake pasa: True
Cluster fallback: True
Cirrus crater pasa: True
```

- [ ] **Step 3: No commit needed (validación, no cambios)**

---

## Task 9: Reproc Fase 1 Copahue 30d VIIRS-only

**Files:** (genera `data/f66_dt5k/Copahue.json`)

- [ ] **Step 1: Compute ventana 30d**

Run: `python -c "from datetime import date, timedelta; e = date.today(); s = e - timedelta(days=30); print(f'--start {s} --end {e}')"`
Expected: algo como `--start 2026-04-26 --end 2026-05-26`

- [ ] **Step 2: Reproc Copahue VIIRS-only**

```bash
python scripts/run_pipeline.py \
  --profile _f66_dt5k \
  --volcano Copahue \
  --sensor viirs \
  --start 2026-04-26 \
  --end 2026-05-26 \
  --overwrite
```

Tiempo estimado: ~10-15 min (depende de cobertura).
Expected: termina sin error, escribe `data/f66_dt5k/Copahue.json` con records 30d.

- [ ] **Step 3: Verify output**

Run: `python -c "import json; d = json.load(open('data/f66_dt5k/Copahue.json')); print(f'Records: {len(d[\"records\"])}'); print(f'First: {d[\"records\"][0][\"timestamp\"][:16]}'); print(f'Last: {d[\"records\"][-1][\"timestamp\"][:16]}')"`
Expected: Records >0, primera y última fecha dentro de la ventana.

- [ ] **Step 4: Spot check diag F66 persisted**

Run: `python -c "import json; d = json.load(open('data/f66_dt5k/Copahue.json')); recs = [r for r in d['records'] if r.get('f66_n_evaluated', 0) > 0]; print(f'Records con f66 diag: {len(recs)}/{len(d[\"records\"])}'); print('Sample:', recs[0] if recs else 'NONE')"`
Expected: ≥10 records con f66_n_evaluated > 0.

- [ ] **Step 5: No commit yet (data accumula, commitea al final)**

---

## Task 10: Reproc Fase 1 Llaima 30d VIIRS-only

**Files:** (genera `data/f66_dt5k/Llaima.json`)

- [ ] **Step 1: Reproc Llaima**

```bash
python scripts/run_pipeline.py \
  --profile _f66_dt5k \
  --volcano Llaima \
  --sensor viirs \
  --start 2026-04-26 \
  --end 2026-05-26 \
  --overwrite
```

Expected: termina sin error.

- [ ] **Step 2: Verify output (mismo que Task 9 Step 3-4)**

Run: `python -c "import json; d = json.load(open('data/f66_dt5k/Llaima.json')); print(f'Records: {len(d[\"records\"])}'); recs = [r for r in d['records'] if r.get('f66_n_evaluated', 0) > 0]; print(f'Con f66 diag: {len(recs)}')"`

---

## Task 11: Reproc Fase 1 Villarrica 30d VIIRS-only

**Files:** (genera `data/f66_dt5k/Villarrica.json`)

- [ ] **Step 1: Reproc Villarrica**

```bash
python scripts/run_pipeline.py \
  --profile _f66_dt5k \
  --volcano Villarrica \
  --sensor viirs \
  --start 2026-04-26 \
  --end 2026-05-26 \
  --overwrite
```

- [ ] **Step 2: Verify output**

Run: `python -c "import json; d = json.load(open('data/f66_dt5k/Villarrica.json')); print(f'Records: {len(d[\"records\"])}'); recs = [r for r in d['records'] if r.get('f66_n_evaluated', 0) > 0]; print(f'Con f66 diag: {len(recs)}')"`

- [ ] **Step 3: Commit los 3 outputs juntos**

```bash
git add data/f66_dt5k/Copahue.json data/f66_dt5k/Llaima.json data/f66_dt5k/Villarrica.json
git commit -m "data(F66): reproc Fase 1 Copahue + Llaima + Villarrica VIIRS-only 30d

3 vol críticos para FPs lago/lacolito sub Tier A. Profile _f66_dt5k aislado.
Diag fields f66_n_evaluated / f66_n_vetoed / f66_n_nan_fallback persistidos
por record. Próximo: audit comparativo Task 12 vs data/mirova_equivalent/.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 12: Audit comparativo data/f66_dt5k vs data/mirova_equivalent

**Files:**
- Create: `experiments/152_f66_audit_phase1/audit.py`
- Create: `experiments/152_f66_audit_phase1/audit_results.json`
- Create: `experiments/152_f66_audit_phase1/audit_report.md`

- [ ] **Step 1: Write audit script**

Create `experiments/152_f66_audit_phase1/audit.py`:

```python
"""F66 Fase 1 audit comparativo data/f66_dt5k vs data/mirova_equivalent.

3 vol Copahue, Llaima, Villarrica × 30d VIIRS-only.

Métricas reportadas per vol:
- n_records_total: total records procesados
- n_records_vrp_gt0: con detección VRP>0
- n_far_30d: detecciones distance_class=far (>inner_radius)
- median_vrp_mw: mediana VRP entre vrp>0
- f66_n_evaluated_total: pixels que entraron al gate (sum)
- f66_n_vetoed_total: pixels rechazados por F66 (sum)
- f66_n_nan_fallback_total: pixels fallback ring (sum)
- recall_vs_mirova_csv: TBD (cross-match con latest_consolidado.csv)
- delta_n_far_30d: f66 vs mirova_eq (% reducción FPs lago)
- delta_n_records_vrp_gt0: f66 vs mirova_eq (% TPs preservados)
"""
import json
from pathlib import Path

VOLCANES = ["Copahue", "Llaima", "Villarrica"]
PROFILES = ["mirova_equivalent", "f66_dt5k"]

def load_records(profile, volcano):
    path = Path(f"data/{profile}/{volcano}.json")
    if not path.exists():
        return []
    d = json.loads(path.read_text(encoding="utf-8"))
    return d.get("records", [])

def metrics(records, ventana_start="2026-04-26", ventana_end="2026-05-26"):
    in_win = [r for r in records if ventana_start <= r["timestamp"][:10] <= ventana_end]
    vrp_gt0 = [r for r in in_win if r.get("vrp_mw", 0) > 0]
    far_30d = [r for r in in_win if r.get("distance_class") == "far"]
    f66_eval = sum(r.get("f66_n_evaluated", 0) for r in in_win)
    f66_vetoed = sum(r.get("f66_n_vetoed", 0) for r in in_win)
    f66_fallback = sum(r.get("f66_n_nan_fallback", 0) for r in in_win)
    vrp_vals = sorted([r.get("vrp_mw", 0) for r in vrp_gt0])
    median_vrp = vrp_vals[len(vrp_vals)//2] if vrp_vals else None
    return {
        "n_records_total": len(in_win),
        "n_records_vrp_gt0": len(vrp_gt0),
        "n_far_30d": len(far_30d),
        "median_vrp_mw": median_vrp,
        "f66_n_evaluated_total": f66_eval,
        "f66_n_vetoed_total": f66_vetoed,
        "f66_n_nan_fallback_total": f66_fallback,
    }

def main():
    results = {}
    for vol in VOLCANES:
        results[vol] = {}
        for prof in PROFILES:
            recs = load_records(prof, vol)
            results[vol][prof] = metrics(recs)
        m_eq = results[vol]["mirova_equivalent"]
        f66 = results[vol]["f66_dt5k"]
        results[vol]["delta"] = {
            "delta_n_records_vrp_gt0_pct": (
                100.0 * (f66["n_records_vrp_gt0"] - m_eq["n_records_vrp_gt0"]) / m_eq["n_records_vrp_gt0"]
                if m_eq["n_records_vrp_gt0"] else None
            ),
            "delta_n_far_30d_pct": (
                100.0 * (f66["n_far_30d"] - m_eq["n_far_30d"]) / m_eq["n_far_30d"]
                if m_eq["n_far_30d"] else None
            ),
        }
    out_path = Path("experiments/152_f66_audit_phase1/audit_results.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(results, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run audit**

Run: `python experiments/152_f66_audit_phase1/audit.py`
Expected: JSON con métricas per vol, escrito a `audit_results.json`.

- [ ] **Step 3: Generate audit report (manual interpretation)**

Create `experiments/152_f66_audit_phase1/audit_report.md` con análisis humano de los resultados. Plantilla:

```markdown
# F66 Fase 1 Audit Report

**Profile A**: mirova_equivalent (baseline)
**Profile B**: _f66_dt5k (F66 híbrido dual-bg gate ON, kernel 3×3, dt_min=5K)
**Ventana**: 2026-04-26 a 2026-05-26 (30d)
**Sensores**: VIIRS-only (I-band 375m + M-band 750m)

## Resultados per volcán

### Copahue
- n_records_vrp_gt0: <A> → <B> (Δ <pct>%)
- n_far_30d (FPs lago Caviahue): <A> → <B> (Δ <pct>%)
- median_vrp_mw: <A> → <B>
- F66 pixels vetoed total: <N>
- F66 fallback total: <N>

### Llaima
[idem]

### Villarrica
[idem]

## Veredicto

### Métricas éxito Fase 1 (de design doc)
- [ ] Recall preservado: vs latest_consolidado.csv recall ≥ pre-F66 - 5%
- [ ] FPs lago reducidos: n_far_30d Copahue/Llaima ≤ 50% del pre-F66
- [ ] Ratio VRP estable: mediana vrp_mw / vrp_mw_mirova cambia <30%
- [ ] R2 pixel-level: ≥4/5 records por vol coinciden con MIROVA web (Task 13)

### Decisión Fase 2/3

- Si todas las métricas pasan: **mergear a Fase 3** (PR rollout a mirova_equivalent operacional en sesión separada).
- Si reducción FPs lago <30%: **Fase 2** (probar otros thresholds dt_k=3 / 2σ / per-vol).
- Si recall destruido >5%: **revertir + brainstorm** approach distinto.
```

Completar manualmente con los números obtenidos.

- [ ] **Step 4: Commit audit**

```bash
git add experiments/152_f66_audit_phase1/
git commit -m "experiments(152): F66 Fase 1 audit Copahue/Llaima/Villarrica

Comparativo data/f66_dt5k/ vs data/mirova_equivalent/ ventana 30d
VIIRS-only. Reporta n_records, n_far_30d, median_vrp_mw, f66 diag totals,
delta % per vol.

Análisis humano en audit_report.md con veredicto métricas éxito Fase 1.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 13: R2 validación pixel-level vs MIROVA web

**Files:**
- Create: `experiments/152_f66_audit_phase1/r2_pixel_level.md`

- [ ] **Step 1: Identificar 5 records canónicos por volcán**

Para cada vol (Copahue/Llaima/Villarrica), elegir 5 records `vrp_mw > 0` que también:
- Existan en `latest_consolidado.csv` (MIROVA NRT ground truth)
- O tengan archivo MIROVA web públicamente verificable

Run para cada vol:
```bash
python -c "
import json, csv
csv_path = 'data/mirova_reference/latest_consolidado.csv'
mirova_ts = set()
with open(csv_path, encoding='utf-8') as f:
    for row in csv.DictReader(f):
        if row.get('Volcano') == 'Copahue':
            mirova_ts.add(row['Date'][:10] + 'T' + row['Time'][:5])
d = json.load(open('data/f66_dt5k/Copahue.json'))
canon = [r for r in d['records'] if r.get('vrp_mw', 0) > 0 and r['timestamp'][:16] in mirova_ts][:5]
for r in canon:
    print(f'{r[\"timestamp\"][:16]} sensor={r[\"sensor\"]} vrp={r[\"vrp_mw\"]:.1f}MW class={r.get(\"distance_class\", \"?\")} f66_vetoed={r.get(\"f66_n_vetoed\", 0)}')
"
```

Repetir para Llaima y Villarrica.

- [ ] **Step 2: Para cada record canónico, verificar manualmente en mirovaweb.it**

Para cada uno de los 15 records (5×3), abrir mirovaweb.it → Volcano → Date, descargar TIF/PNG si disponible, comparar pixel-level:
- ¿MIROVA reporta detección esa noche?
- ¿Coordenadas del cluster coinciden con nuestro pixel hot?
- ¿VRP magnitude está dentro de ±50% del nuestro?

Documentar en `experiments/152_f66_audit_phase1/r2_pixel_level.md`:

```markdown
# F66 Fase 1 R2 — Pixel-level validation vs MIROVA web

5 records canónicos por volcán (Copahue, Llaima, Villarrica) cross-matched con mirovaweb.it.

## Copahue

| Timestamp | Sensor | Our VRP (MW) | MIROVA reporta? | Pixel match? | VRP ±50%? | Verdict |
|---|---|---:|:---:|:---:|:---:|---|
| 2026-05-01 06:45 | VIIRS_NPP_I | 12.4 | ✓ | ✓ | ✓ | TP confirmado |
| ... | | | | | | |

## Llaima
[idem 5 filas]

## Villarrica
[idem 5 filas]

## Resumen R2

- Total: 15 records
- TP confirmados: X/15
- Discrepancias: Y/15 (detalladas abajo)
- Veredicto: ≥4/5 por vol = PASA, sino INVESTIGAR
```

- [ ] **Step 3: Commit R2 report**

```bash
git add experiments/152_f66_audit_phase1/r2_pixel_level.md
git commit -m "experiments(152): F66 Fase 1 R2 pixel-level vs MIROVA web

15 records canónicos (5×3 vol) cross-matched con mirovaweb.it. Verifica
coordenadas cluster, magnitud VRP ±50%, presencia detección.

Métrica éxito: ≥4/5 records por volcán coinciden con MIROVA web.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 14: Documentar resultados + decisión Fase 2/3

**Files:**
- Create: `docs/F66_RESULTS_PHASE1_S79.md`

- [ ] **Step 1: Síntesis resultados**

Create `docs/F66_RESULTS_PHASE1_S79.md`:

```markdown
---
title: "F66 Fase 1 — Resultados híbrido dual-bg gate"
session: S79
status: complete
ai_generated: true
confidence: <medium|high>
explored: true
tags: [results, f66, lagos, mirova-faithful]
related:
  - docs/superpowers/specs/2026-05-26-f66-hybrid-bg-kernel-consistency-gate-design.md
  - docs/superpowers/plans/2026-05-26-f66-hybrid-bg-kernel-consistency-gate.md
  - experiments/152_f66_audit_phase1/audit_results.json
  - experiments/152_f66_audit_phase1/audit_report.md
  - experiments/152_f66_audit_phase1/r2_pixel_level.md
---

# F66 Fase 1 — Resultados

## Setup

- Profile: `_f66_dt5k` (kernel 3×3, dt_min=5K = anomaly_threshold_k)
- Ventana: 30d (<start> a <end>)
- Sensores: VIIRS-only (Windows constraint, MODIS pendiente GH Actions)
- Volcanes: Copahue, Llaima, Villarrica

## Métricas (resumen de audit_results.json)

[Tabla con números reales obtenidos de Task 12]

## R2 validación pixel-level

[Resumen de Task 13: X/15 records confirmados vs MIROVA web]

## Veredicto métricas éxito Fase 1

- [ ] Recall preservado vs latest_consolidado.csv
- [ ] FPs lago reducidos ≥50% Copahue/Llaima
- [ ] Ratio VRP estable
- [ ] R2 pixel-level ≥4/5 por vol

## Decisión

[Una de las tres opciones:]

### Opción A — Avanzar a Fase 3 (rollout mirova_equivalent)

Todas las métricas pasaron. En sesión separada (S80):
- Tag defensivo `pre-s79-f66-rollout`
- Confirmación Nicolás A45
- Edit `pipeline/profiles/mirova_equivalent.yaml` → enable_bg_kernel_consistency_gate: true + kernel_consistency_dt_k: 5.0
- NRT cron empieza a aplicar gate automáticamente

### Opción B — Fase 2 (probar otros thresholds)

Reducción FPs lago insuficiente. Clonar profile a `_f66_dt3k.yaml`, `_f66_dt_2sigma.yaml`, `_f66_per_vol.yaml`. Reproc paralelo (serial A47). Análisis comparativo.

### Opción C — Revert + brainstorm distinto

Recall destruido >5% o R2 falló. Cerrar F66 híbrido como no viable; reconsiderar F65 TOP 2 (sensor fusion) o approach comprehensivo F66 (migrar `compute_bg_stats` completamente).
```

Completar con números reales y elegir A/B/C.

- [ ] **Step 2: Commit results doc**

```bash
git add docs/F66_RESULTS_PHASE1_S79.md
git commit -m "docs(F66): resultados Fase 1 + decisión Fase 2/3

[Una línea describiendo el veredicto: 'Fase 1 PASA, avanzar a Fase 3' o
'Reducción FPs insuficiente, Fase 2 con threshold ajustado' o 'Recall
destruido, pivotar approach']

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 15: PR con resultados

**Files:** (sin cambios de código)

- [ ] **Step 1: Push branch + create PR**

```bash
git push -u origin claude/s79-f66-hybrid-bg-gate

gh pr create --title "F66 híbrido — Dual-bg consistency gate (Fase 1 validación)" --body "$(cat <<'PRBODY'
## Summary

Implementación + validación Fase 1 del F66 híbrido dual-bg consistency gate (S79 P1).

**Approach**: gate de consistencia secundario con kernel local 3×3 sobre el hot_mask del ring 5-25 km. Pixel solo hot si AMBOS gates lo confirman. Lago tibio: ring sí, kernel no → vetado. Cráter real: ambos sí → válido. Lava extendida cluster: vecinos hot → NaN → fallback ring (preserva recall).

**MIROVA-faithful**: Coppola 2024 L1129 + Coppola 2016a L240-249 + L357-359 + Campus 2024 L119-124 verbatim usan bg local 8-conn.

## Docs

- Design: docs/superpowers/specs/2026-05-26-f66-hybrid-bg-kernel-consistency-gate-design.md
- Plan: docs/superpowers/plans/2026-05-26-f66-hybrid-bg-kernel-consistency-gate.md
- Resultados Fase 1: docs/F66_RESULTS_PHASE1_S79.md
- Audit: experiments/152_f66_audit_phase1/

## Cambios código

- `pipeline/detection_context.py`: helper apply_f66_consistency_gate() (~50 líneas + docstring)
- `pipeline/profile.py`: 3 nuevos campos parsing default OFF (~10 líneas)
- `pipeline/process_modis.py`, `process_viirs.py`, `process_viirs_mod.py`: invocación condicional (~15 líneas c/u)
- `pipeline/profiles/_f66_dt5k.yaml`: profile dedicado Fase 1 (NUEVO)
- `tests/test_f66_bg_kernel_consistency.py`: 8 tests sintéticos (NUEVO)

## Defaults sin cambio operacional

- `mirova_equivalent.yaml` NO modificado. Flag default OFF allí.
- Profile `_f66_dt5k` aislado con `data_subdir: f66_dt5k`. NO toca operacional.
- NRT cron sigue comportamiento actual.

## Defensive tag

`pre-s79-f66-hybrid` → `9d4dd082` pusheado a origin (A45).

## Test plan

- [x] Tests sintéticos 7/7 passing (escenarios físicos canónicos)
- [x] Baseline tests 509 passing, 24 skipped (sin regresiones)
- [x] Reproc 30d × 3 vol VIIRS-only (Copahue, Llaima, Villarrica)
- [x] Audit comparativo data/f66_dt5k vs data/mirova_equivalent
- [x] R2 pixel-level vs MIROVA web (5 records × 3 vol)
- [ ] **NO mergear hasta Fase 3 (rollout)** — decisión en sesión S80+ tras review Nicolás

## Veredicto

Ver docs/F66_RESULTS_PHASE1_S79.md sección "Decisión" (Opción A/B/C).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
PRBODY
)"
```

- [ ] **Step 2: Verify PR URL returned**

Expected output: `https://github.com/MendozaVolcanic/VRP-chile/pull/<N>`

- [ ] **Step 3: Mark PR as draft (NO merge inmediato — espera Fase 3 decisión)**

```bash
gh pr ready <PR_NUMBER> --undo
```

Confirma el PR queda como Draft.

- [ ] **Step 4: Reportar a Nicolás vía AskUserQuestion**

Use AskUserQuestion con:
- Question: "F66 Fase 1 completa. PR Draft #<N> abierto con resultados. ¿Cómo procedemos?"
- Options:
  - "Aprobar mergeo PR (continuar a Fase 3 rollout en sesión siguiente)"
  - "Revisar resultados detenidamente antes de decidir"
  - "Fase 2 — probar threshold distinto"
  - "Revertir — approach no funcionó"

---

## Self-Review

### 1. Spec coverage (vs design doc 2026-05-26-f66-hybrid-bg-kernel-consistency-gate-design.md)

| Sección spec | Cubierto por |
|---|---|
| §2 Solución pseudocódigo | Task 1 (helper) + Tasks 4-6 (integración) |
| §3 Cambios en código | Tasks 1, 3, 4, 5, 6, 7 |
| §4 Edge cases | Task 1 implementación + Task 2 tests |
| §5 Tests sintéticos (7 escenarios) | Task 1 (1 test) + Task 2 (6 tests) + Task 3 (1 test profile) + Task 7 (1 test profile_f66) = 9 tests totales |
| §6 Plan validación Fase 1 | Tasks 9-13 |
| §6 Métricas éxito | Task 12 (audit) + Task 13 (R2) + Task 14 (resumen) |
| §7 Riesgos y mitigación | Task 0 (A45) + Task 8 (sanity) |
| §8 Rollback plan | Task 15 (PR Draft, no merge) |
| §9 Decisiones pendientes | Task 0 (A45 explícito) + Task 14 (decisión Fase 2/3) |

Sin gaps detectados.

### 2. Placeholder scan

Búsqueda de patterns "TODO", "TBD", "fill in", "similar to":
- Task 14 Step 1 contiene "<start>", "<end>", "<medium|high>", "[Tabla con números reales]" — esto NO son placeholders del plan, son markers para que Nicolás complete con valores empíricos post-reproc. Aclarado en steps.
- Task 4 Step 2 menciona "Verificar nombre exacto con grep y usar el nombre exacto" — esto es disclaimer porque no leí en detalle process_viirs.py. NO es placeholder del plan, es instrucción para el implementor de verificar.
- Sin "implementar después" o "agregar appropriate handling" detectados.

### 3. Type consistency

- `apply_f66_consistency_gate()` firma: `(bt, hot_mask, *, kernel_size, dt_min) -> tuple[np.ndarray, dict]` consistente en Tasks 1, 4, 5, 6, 7.
- `compute_local_background()` signature: `(bt_grid, hot_rows, hot_cols, kernel_size=3) -> list[float]` ya existente en vrp_regimes.py, reusada idéntica en Task 1.
- Profile fields: `enable_bg_kernel_consistency_gate`, `kernel_consistency_dt_k`, `kernel_consistency_size` consistentes en Tasks 3, 7 y profiles yaml.
- Record diag fields: `f66_n_evaluated`, `f66_n_vetoed`, `f66_n_nan_fallback` consistentes en Tasks 4, 5, 6.

Sin inconsistencias.

### 4. Risk: pyhdf Windows

Task 6 (process_modis.py) explícitamente note el constraint pyhdf. Tests pass via mock. Fase 1 reproc usa VIIRS-only, MODIS reproc queda para Fase 3 vía GH Actions Linux post-merge.

### 5. Risk: A45 enforcement

Task 0 Step 3 hace AskUserQuestion explícita pidiendo "Confirmo" antes de avanzar. Sin ese gate, el plan NO procede.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-26-f66-hybrid-bg-kernel-consistency-gate.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
