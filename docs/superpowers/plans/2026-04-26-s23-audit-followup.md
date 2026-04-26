# S23 Audit Follow-Up Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) o `superpowers:executing-plans` para implementar task-by-task. Steps usan checkbox (`- [ ]`) syntax.

**Goal:** Cerrar los 18 hallazgos del audit profundo S22 en orden inteligente — bugs críticos primero, luego cobertura tests, luego validaciones de asunciones, finalmente investigaciones científicas y cleanup.

**Architecture:** 7 fases secuenciales. Fases 1-3 ejecutables en una sesión (bugs + tests TDD). Fases 4-7 requieren descargas/exploración — tasks listadas con criterios concretos pero el código se escribe iterativamente cuando llegamos.

**Tech Stack:** Python 3.11, pytest, numpy, pandas, earthaccess, git, GitHub Actions, frontend Vanilla JS + Chart.js.

**Working directory:** `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile`

---

## File Structure

| Archivo | Acción | Responsabilidad |
|---|---|---|
| `pipeline/store.py:150-156` | Modify | Fix Regla D edge case (KeyError) |
| `pipeline/process_modis.py:175-181` + `process_viirs.py:206-214` | Modify | haversine None check |
| `pipeline/process_viirs.py` + `process_viirs_mod.py` | Modify | Local ROI threshold paridad MODIS (decisión) |
| `tests/test_store_regla_d_edge.py` | Create | Edge cases Regla D |
| `tests/test_haversine_robust.py` | Create | None inputs |
| `tests/test_local_roi_paridad.py` | Create | MODIS vs VIIRS local ROI |
| `tests/test_process_modis_core.py` | Create | 8 tests TDD core MODIS funcs |
| `tests/test_store_append_record.py` | Create | Edge cases append_record |
| `tests/test_scan_geometry.py` | Create | Zenithal + bbox mask + areas |
| `tests/test_golden_records.py` | Modify | Expand 4→10+ records |
| `experiments/42_p3_1_dual_roi_validation.py` | Create | E33 reproceso faltante |
| `experiments/43_audit_experimental_yaml.py` | Create | Diff con mirova_equivalent |
| `experiments/44_factor_42_clustering.py` | Create | Investigación MIROVA clustering |
| `experiments/45_dibella_k_viirs_ab.py` | Create | A/B coefs Wooster |
| `experiments/46_aveni_tir_villarrica.py` | Create | VRP_TIR test sub-pixel |
| `experiments/47_json_inflation_audit.py` | Create | Tamaño JSONs Chaitén/Lascar |
| `pipeline/constants.py` | Create | SIGMA, C1, C2 centralizados |
| `pipeline/profiles/mirova_equivalent.yaml` | Modify | P95_VENT_EXCLUSION_KM agregado |
| `frontend/index.html` | Modify | Panel diag_* |
| `scripts/README.md` | Create | Doc 11 scripts legacy |
| `docs/PAPERS_AUDIT.md` | Modify | +10 papers Vault auditados |
| `docs/HYPOTHESIS_LOG.md` | Modify | H_S23_* nuevas + cierre H_S22 |
| `docs/DRIFTS_S17.md` | Modify | D7+ si encontramos drifts nuevos |
| `docs/SESSION_INDEX.md` | Modify | Fila S23 |
| `~memory/project_s23_findings.md` | Create | Hallazgos S23 |
| `tasks/handoff_s24_*.md` | Create | Próxima sesión |

---

## FASE 1 — Bugs latentes en producción (2-3h, sin descargas)

### Task 1: Fix Regla D edge case (KeyError potencial)

**Files:**
- Modify: `pipeline/store.py:150-160`
- Test: `tests/test_store_regla_d_edge.py` (nuevo)

**Contexto**: S20 Regla D asume que cuando `vrp_vent_mw>0` los campos `vent_hotspot_lat/lon/dist_km` existen. Si por algún bug VIIRS retorna `vrp_vent>0` pero los campos son None/missing, el código rompe con KeyError silencioso.

- [ ] **Step 1: Test failing — Regla D maneja vent_hotspot_dist_km missing**

`tests/test_store_regla_d_edge.py`:

```python
"""Edge cases para Regla D vent-priority (S20). Garantizar que NO rompe
KeyError si los campos vent_hotspot_* faltan inesperadamente."""
from __future__ import annotations
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.store import append_record


def _record_with_vent_no_hotspot():
    """Record VIIRS con vrp_vent>0 pero vent_hotspot_* ausentes."""
    return {
        "vrp_mir_mw": 0.5,
        "vrp_vent_mw": 0.15,  # >0 dispara Regla D
        # NOTA: NO hay vent_hotspot_lat/lon/dist_km
        "n_anomalous_pixels": 1,
        "n_vent_pixels": 1,
        "hotspot_lat": -33.4,
        "hotspot_lon": -69.8,
        "hotspot_dist_km": 1.5,
        "final_hotspot_lat": -33.4,
        "final_hotspot_lon": -69.8,
        "final_hotspot_dist_km": 1.5,
        "final_hotspot_source": "eruption",
        "distance_class": "summit",
        "anomaly_pixels": [],
        "t_bg_k": 265.0,
        "t_max_i04_k": 270.0,
        "sensor": "VIIRS_NOAA20",
        "granule": "VJ102IMG.A2026100.0500.021.fake.nc",
        "product_version": "standard",
        "datetime_utc": "2026-04-10 05:00",
    }


def test_regla_d_no_keyerror_when_vent_hotspot_missing(tmp_path):
    """Si vrp_vent>0 pero vent_hotspot_* es None/missing, NO debe crashear."""
    out_dir = tmp_path / "data" / "mirova_equivalent"
    out_dir.mkdir(parents=True)

    rec = _record_with_vent_no_hotspot()

    # NO debe lanzar KeyError ni AttributeError
    append_record(
        volcano_name="TestVolcano",
        record=rec,
        volcano_lat=-33.4,
        volcano_lon=-69.8,
        overwrite=False,
        max_hotspot_dist_km=25.0,
        out_dir=out_dir,
    )

    # JSON guardado, record presente
    out_file = out_dir / "TestVolcano.json"
    assert out_file.exists()
    data = json.loads(out_file.read_text())
    assert len(data["records"]) == 1
    saved = data["records"][0]
    # distance_class queda summit por la rama eruption_path (final_dist<=inner)
    # NO debe cambiar a summit a través de Regla D porque no hay vent_hotspot
    assert saved["distance_class"] == "summit"


def test_regla_d_applies_only_when_vent_fields_complete(tmp_path):
    """Regla D solo dispara si vrp_vent>0 Y todos vent_hotspot_* presentes."""
    out_dir = tmp_path / "data" / "mirova_equivalent"
    out_dir.mkdir(parents=True)

    rec = _record_with_vent_no_hotspot()
    rec["distance_class"] = "far"  # eruption-path lejos
    rec["final_hotspot_dist_km"] = 15.0
    rec["final_hotspot_source"] = "eruption"
    # Sin vent_hotspot_* → Regla D NO aplica → queda far
    append_record(
        volcano_name="TestVolcano",
        record=rec,
        volcano_lat=-33.4,
        volcano_lon=-69.8,
        overwrite=False,
        max_hotspot_dist_km=25.0,
        out_dir=out_dir,
    )

    data = json.loads((out_dir / "TestVolcano.json").read_text())
    saved = data["records"][0]
    assert saved["distance_class"] == "far"  # Regla D no debió promover
```

- [ ] **Step 2: Run test — esperado FAIL (KeyError o falla diferente)**

Run:
```bash
pytest tests/test_store_regla_d_edge.py -v
```
Expected: FAIL en `test_regla_d_no_keyerror_when_vent_hotspot_missing` (KeyError) o el test pasa pero `test_regla_d_applies_only_when_vent_fields_complete` falla porque store.py promueve a summit incorrectamente.

- [ ] **Step 3: Fix store.py — usar `.get()` con check completo**

Localizar el bloque Regla D (alrededor de línea 150-160):

```python
# ANTES
if vrp_vent > 0:
    record["distance_class"] = "summit"
    if record.get("vent_hotspot_lat") is not None:
        record["final_hotspot_lat"] = record["vent_hotspot_lat"]
        record["final_hotspot_lon"] = record["vent_hotspot_lon"]
        record["final_hotspot_dist_km"] = record["vent_hotspot_dist_km"]
        record["final_hotspot_source"] = "vent"
```

Reemplazar por:

```python
# S23 Task 1 fix: Regla D requiere los 3 vent_hotspot_* completos.
# Si alguno falta, Regla D NO aplica (no asumir summit y no promover hotspot).
if vrp_vent > 0:
    vh_lat = record.get("vent_hotspot_lat")
    vh_lon = record.get("vent_hotspot_lon")
    vh_dist = record.get("vent_hotspot_dist_km")
    if vh_lat is not None and vh_lon is not None and vh_dist is not None:
        record["distance_class"] = "summit"
        record["final_hotspot_lat"] = vh_lat
        record["final_hotspot_lon"] = vh_lon
        record["final_hotspot_dist_km"] = vh_dist
        record["final_hotspot_source"] = "vent"
    # Si vent_hotspot_* incompleto: dejar distance_class como vino del eruption-path
    # (no promover a summit "ciegamente" porque hay riesgo de FP).
```

- [ ] **Step 4: Run tests — esperado PASS**

Run:
```bash
pytest tests/test_store_regla_d_edge.py -v
```
Expected: 2 passed.

- [ ] **Step 5: Run full suite para no romper nada**

Run:
```bash
pytest 2>&1 | tail -3
```
Expected: 121+ passed (era 119, +2 nuevos).

- [ ] **Step 6: Commit**

```bash
git add pipeline/store.py tests/test_store_regla_d_edge.py
git commit -m "S23 T1 — Regla D edge case: requires all vent_hotspot_* complete

Audit S22 hallazgo crítico: Regla D (S20) asumía que cuando vrp_vent>0
los campos vent_hotspot_lat/lon/dist_km existían. Si por bug aguas arriba
alguno era None, KeyError silencioso en producción.

Fix: requiere los 3 campos completos antes de promover a summit. Si
incompleto, mantiene la clasificación que dio eruption-path (no asume).

2 tests TDD nuevos (suite 121/121 verde).

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 2: Fix haversine_km None safety + consolidar a scan_geometry

**Files:**
- Modify: `pipeline/scan_geometry.py` (agregar `haversine_km`)
- Modify: `pipeline/process_modis.py:175-181`, `process_viirs.py:206-214`, `process_viirs_mod.py` (importar de scan_geometry)
- Test: `tests/test_haversine_robust.py` (nuevo)

**Contexto**: `haversine_km` está duplicado en 3 archivos (process_modis/viirs/viirs_mod). Si volcano_lat es None → TypeError silencioso. Centralizar + agregar guards.

- [ ] **Step 1: Test failing**

`tests/test_haversine_robust.py`:

```python
"""haversine_km debe manejar inputs None y NaN sin crashear silenciosamente."""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.scan_geometry import haversine_km


def test_haversine_returns_array_for_array_inputs():
    lat2 = np.array([-33.5, -33.6])
    lon2 = np.array([-69.7, -69.6])
    out = haversine_km(-33.4, -69.8, lat2, lon2)
    assert out.shape == (2,)
    assert all(out > 0)


def test_haversine_zero_when_same_point():
    out = haversine_km(-33.4, -69.8, np.array([-33.4]), np.array([-69.8]))
    assert out[0] == pytest.approx(0.0, abs=1e-6)


def test_haversine_raises_when_volcano_lat_is_none():
    """Defensa: volcano_lat=None debe disparar TypeError explícito, no silencioso."""
    with pytest.raises((TypeError, ValueError)):
        haversine_km(None, -69.8, np.array([-33.4]), np.array([-69.8]))


def test_haversine_handles_nan_in_array():
    """NaN en arrays input → NaN en output (no crash)."""
    lat2 = np.array([-33.5, np.nan])
    lon2 = np.array([-69.7, -69.6])
    out = haversine_km(-33.4, -69.8, lat2, lon2)
    assert out.shape == (2,)
    assert not np.isnan(out[0])
    assert np.isnan(out[1])
```

- [ ] **Step 2: Run test — FAIL (function probably not in scan_geometry yet)**

Run:
```bash
pytest tests/test_haversine_robust.py -v
```
Expected: FAIL ImportError (haversine_km no exportado por scan_geometry).

- [ ] **Step 3: Agregar haversine_km a scan_geometry.py**

Después de `EARTH_RADIUS_KM = 6371.0` agregar:

```python
def haversine_km(lat1: float, lon1: float,
                 lat2: np.ndarray, lon2: np.ndarray) -> np.ndarray:
    """Vectorized haversine distance (km) from scalar point to array.

    Args:
        lat1, lon1: scalar floats (volcano center).
        lat2, lon2: numpy arrays (per-pixel grids).

    Returns:
        Array same shape as lat2/lon2, distance in km. NaN propagates.

    Raises:
        TypeError: si lat1 o lon1 es None.
    """
    if lat1 is None or lon1 is None:
        raise TypeError(
            f"haversine_km: lat1/lon1 cannot be None (got {lat1}, {lon1}). "
            "Check volcano YAML config has lat/lon set."
        )
    R = EARTH_RADIUS_KM
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = (np.sin(dlat / 2) ** 2
         + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2))
         * np.sin(dlon / 2) ** 2)
    return R * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))
```

- [ ] **Step 4: Run test — PASS**

Run:
```bash
pytest tests/test_haversine_robust.py -v
```
Expected: 4 passed.

- [ ] **Step 5: Reemplazar definiciones duplicadas (DRY)**

En cada uno de:
- `pipeline/process_modis.py` (línea ~175)
- `pipeline/process_viirs.py` (línea ~206)
- `pipeline/process_viirs_mod.py` (~línea similar)

REEMPLAZAR la definición local de `haversine_km` por:

```python
from pipeline.scan_geometry import haversine_km
```

- [ ] **Step 6: Run full suite — no rompe nada**

Run:
```bash
pytest 2>&1 | tail -3
```
Expected: 125 passed (121 + 4 nuevos).

- [ ] **Step 7: Commit**

```bash
git add pipeline/scan_geometry.py pipeline/process_modis.py pipeline/process_viirs.py pipeline/process_viirs_mod.py tests/test_haversine_robust.py
git commit -m "S23 T2 — haversine_km centralizado a scan_geometry + None safety

DRY: 3 copias idénticas de haversine_km (process_modis/viirs/viirs_mod)
consolidadas en pipeline/scan_geometry.py haversine_km().

Defensa: si volcano_lat/lon es None ahora dispara TypeError explícito en
vez de silenciosamente propagar np.radians(None) → ValueError críptico.

4 tests TDD nuevos (None safety, NaN propagation, scalar→array shape).

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 3: Documentar y decidir divergencia local ROI threshold MODIS vs VIIRS

**Files:**
- Read: `pipeline/process_modis.py:285-288` (tiene local ROI threshold)
- Read: `pipeline/process_viirs.py` (NO tiene equivalente)
- Modify: `docs/DRIFTS_S17.md` (sección nueva D7)
- Test: `tests/test_local_roi_paridad.py` (nuevo, schema-source like S22.1)

**Contexto**: process_modis aplica `effective_threshold = max(t_bg + threshold, roi_p95 + max(3.0, 2.0*roi_std))` que es un filtro local p95. process_viirs NO lo tiene. Esto puede causar:
- MODIS rechaza pixels VIIRS detectaría → underdetect MODIS o overdetect VIIRS.
- Sin razón documentada históricamente.

**Decisión de este task**: NO implementar el fix algorítmico todavía (es scope grande con riesgo). Sí: documentar la divergencia como **D7** y agregar test schema-source que la haga visible.

- [ ] **Step 1: Investigar el git log / código por qué MODIS lo tiene**

Run:
```bash
git log --all --oneline -p -- pipeline/process_modis.py | grep -A3 "roi_p95.*roi_std" | head -20
git log --all --oneline -p -- pipeline/process_viirs.py | grep -A3 "roi_p95.*roi_std" | head -10
```

Documentar en notas: ¿qué sesión introdujo el local ROI threshold en MODIS y por qué?

- [ ] **Step 2: Test schema-source que ALERTE de la divergencia**

`tests/test_local_roi_paridad.py`:

```python
"""Schema-source test: marca explícitamente la divergencia local ROI threshold
entre process_modis y process_viirs. NO falla — solo emite warning si la
divergencia se cierra por accidente sin actualizar este test.

S23 D7: divergencia documentada en docs/DRIFTS_S17.md.
"""
from pathlib import Path

PIPELINE = Path(__file__).parent.parent / "pipeline"


def test_modis_has_local_roi_threshold_documented():
    """Sanity: process_modis.py tiene la fórmula roi_p95 + max(3.0, 2.0*roi_std)."""
    src = (PIPELINE / "process_modis.py").read_text(encoding="utf-8")
    assert "roi_p95" in src and "roi_std" in src, (
        "process_modis.py debería tener la fórmula local ROI threshold "
        "(roi_p95 + max(3.0, 2.0*roi_std)). Si fue eliminada, actualizar D7 "
        "en docs/DRIFTS_S17.md y este test."
    )


def test_viirs_known_to_not_have_local_roi_threshold():
    """D7 documentado: process_viirs NO tiene la fórmula. Si la agregamos,
    actualizar D7 en DRIFTS_S17.md y este test."""
    src = (PIPELINE / "process_viirs.py").read_text(encoding="utf-8")
    # Usar string específico para evitar match por substring débil
    has_formula = "roi_p95 + max(3.0, 2.0" in src or "roi_p95 + max(3" in src
    assert not has_formula, (
        "process_viirs.py AHORA tiene la fórmula local ROI threshold que antes "
        "solo estaba en MODIS. Si fue agregada deliberadamente, actualizar D7 "
        "en docs/DRIFTS_S17.md y este test."
    )


def test_viirs_mod_known_to_not_have_local_roi_threshold():
    """Idem para VIIRS 750m."""
    src = (PIPELINE / "process_viirs_mod.py").read_text(encoding="utf-8")
    has_formula = "roi_p95 + max(3.0, 2.0" in src or "roi_p95 + max(3" in src
    assert not has_formula, (
        "process_viirs_mod.py ahora tiene local ROI threshold. Actualizar D7."
    )
```

- [ ] **Step 3: Run tests**

Run:
```bash
pytest tests/test_local_roi_paridad.py -v
```
Expected: 3 passed (todos pasan en estado actual).

- [ ] **Step 4: Documentar D7 en DRIFTS_S17.md**

Agregar al final de la tabla resumen:

```markdown
| **D7** | **Local ROI threshold MODIS-only (no en VIIRS)** | **Detectado S23 audit** | **Documentado, fix algorítmico diferido S24+** | **S23** |
```

Y nueva sección antes de "## Otros hallazgos que NO son drift":

```markdown
## D7 — Local ROI threshold solo en process_modis (S23 audit)

### Evidencia

`pipeline/process_modis.py:285-288`:
```python
if len(roi_valid) >= 10:
    roi_p95 = float(np.percentile(roi_valid, 95))
    roi_std = float(np.std(roi_valid))
    local_threshold = roi_p95 + max(3.0, 2.0 * roi_std)
    effective_threshold = max(t_bg + threshold, local_threshold)
```

`pipeline/process_viirs.py`: NO tiene equivalente. effective_threshold solo
considera `t_bg + sigma_component` (sin filtro p95 local).

### Implicancia

- MODIS aplica un filtro local p95 que rechaza pixels que solo son levemente
  más calientes que el percentil 95 del ROI.
- VIIRS NO aplica ese filtro → más pixels detectados en VIIRS para mismas
  condiciones físicas.
- Posible explicación parcial del "factor 42" (77 px nuestro vs 4 MIROVA Lascar)
  cuando el sensor es VIIRS.

### Decisión S23

**Documentar como drift, NO fix algorítmico todavía**. El fix puede ir en dos
direcciones (agregar a VIIRS, o quitar de MODIS), y necesita validación A/B
contra OSF v2.5 para decidir cuál es correcto. Diferido S24+.

Test `tests/test_local_roi_paridad.py` alerta si el estado cambia sin
actualizar esta documentación.
```

- [ ] **Step 5: Commit**

```bash
git add tests/test_local_roi_paridad.py docs/DRIFTS_S17.md
git commit -m "S23 T3 — D7 documentado: local ROI threshold MODIS-only

Audit S22 hallazgo crítico: process_modis.py tiene filtro local
roi_p95 + max(3.0, 2.0*roi_std) que process_viirs NO tiene. Divergencia
algorítmica no documentada.

Fix decision: documentar como D7 y agregar tests schema-source que
alerten si el estado cambia sin actualización docs.

Fix algorítmico real (agregar a VIIRS o quitar de MODIS) requiere A/B
contra OSF v2.5 — diferido S24+.

3 tests schema-source nuevos (suite 128/128 verde).

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## FASE 2 — Validación pasiva fixes S22 (observar, sin acción activa)

### Task 4: Verificar próximos 3 cron NRT post-fix

**Files**: solo lectura.

**Contexto**: S22 deployó dos fixes a main (commits `752ddb7` H6 + `aa7ad37` git push conflict + `4351cd6` H6 netrc fix). Hipótesis: tasa éxito NRT sube de 13% → >80%.

- [ ] **Step 1: Esperar próximo cron (cada 2h, próximo ~10:47 UTC)**

Run cuando llegue la hora:
```bash
gh run list -R MendozaVolcanic/VRP-chile --workflow=nrt.yml -L 5 --json status,conclusion,createdAt,databaseId --jq '.[] | "\(.createdAt[:19])  \(.status) \(.conclusion // "nil")"'
```

- [ ] **Step 2: Si run post-fix completes con success → fix validado**

Criterio de éxito: 2/3 próximos runs success → tasa subió. Issue #1 puede cerrarse.

- [ ] **Step 3: Si run post-fix sigue failing → diagnosticar nuevo error**

Run:
```bash
RUN_ID=<latest_failed>
gh run view $RUN_ID -R MendozaVolcanic/VRP-chile --log-failed 2>&1 | tail -40
```
Buscar: `Network unreachable` (H6 falló retry), `Could not apply` (git push aún conflicta), o NUEVO error.

- [ ] **Step 4: Documentar resultado en `~memory/project_s23_findings.md`**

Si éxito: confirmar H6 + fix git push validados. Cerrar Issue #1.
Si falla: nuevo H_S23_X con tipo de error y plan de fix.

---

## FASE 3 — Cobertura tests (impacto alto, sin descargas, ~8-12h)

### Task 5: process_modis.py TDD — 8 tests core

**Files:**
- Test: `tests/test_process_modis_core.py` (nuevo)
- Read only: `pipeline/process_modis.py`

**Contexto**: 6/11 módulos sin tests dedicados. process_modis.py procesa 50% de los records (Tier A) y NO tiene test suite directa.

**Approach**: tests con arrays sintéticos pequeños, sin requerir HDF files reales. Mockear `read_modis_l1b` y `_interp_geo` para inyectar arrays.

- [ ] **Step 1: Escribir test failing 1 — Path A (BT) detecta pixel hot**

`tests/test_process_modis_core.py`:

```python
"""Tests TDD para pipeline/process_modis.py funciones core.

Approach: mockear loaders L1B y geo, inyectar arrays sintéticos pequeños
(50×50). Cubre: BT path, NTI path, sigma gates, vent path, hotspot extraction.
"""
from __future__ import annotations
import sys
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


def _synthetic_modis_scene(hot_pixel_at=(25, 25), hot_bt=320.0,
                           bg_bt=290.0, bg_std=0.5, n=50):
    """Crea escena sintética 50x50 con un pixel hot al center."""
    rng = np.random.default_rng(42)
    bt_b21 = rng.normal(bg_bt, bg_std, size=(n, n)).astype(np.float32)
    bt_b22 = bt_b21.copy()
    bt_b31 = rng.normal(280.0, 0.4, size=(n, n)).astype(np.float32)
    if hot_pixel_at:
        r, c = hot_pixel_at
        bt_b21[r, c] = hot_bt
        bt_b22[r, c] = hot_bt
        bt_b31[r, c] = hot_bt - 30  # TIR menor que MIR para hotspot real
    return {"band21": bt_b21, "band22": bt_b22, "band31": bt_b31}


def _synthetic_modis_geo(center_lat=-33.4, center_lon=-69.8, span_km=15, n=50):
    """Lat/lon grid centrado en (center_lat, center_lon), span ±span_km."""
    dlat = span_km / 111.0
    dlon = span_km / (111.0 * np.cos(np.radians(center_lat)))
    lats = np.linspace(center_lat - dlat, center_lat + dlat, n)
    lons = np.linspace(center_lon - dlon, center_lon + dlon, n)
    lat_grid, lon_grid = np.meshgrid(lats, lons, indexing="ij")
    return {"lat": lat_grid.astype(np.float32),
            "lon": lon_grid.astype(np.float32)}


def test_calculate_vrp_detects_hot_pixel_bt_path():
    """Pixel BT=320K (30K sobre bg=290) debe disparar Path A."""
    from pipeline import process_modis as pm

    bands = _synthetic_modis_scene(hot_pixel_at=(25, 25), hot_bt=320.0)
    geo = _synthetic_modis_geo()

    with patch.object(pm, 'read_modis_l1b', return_value=bands), \
         patch.object(pm, '_interp_geo',
                      side_effect=lambda c, t1, t2: c.reshape(50, 50)
                      if c.size == 2500 else c):
        # Pasar paths fake (no se usan porque mockeamos los loaders)
        result = pm.calculate_vrp(
            hdf_path=Path("fake_MOD021KM.A2026100.0500.061.hdf"),
            geo_path=Path("fake_MOD03.A2026100.0500.061.hdf"),
            volcano_lat=-33.4, volcano_lon=-69.8,
            radius_km=15.0,
            vent_lat=None, vent_lon=None,  # Sin vent path
        )

    assert result is not None
    assert result["n_anomalous_pixels"] >= 1
    assert result["t_max_k"] >= 319.0
```

- [ ] **Step 2: Run test — esperado FAIL o adaptar mocks según error real**

Run:
```bash
pytest tests/test_process_modis_core.py::test_calculate_vrp_detects_hot_pixel_bt_path -v 2>&1 | tail -20
```

Expected: FAIL — ajustar mocks según firma real de `_interp_geo` y `read_modis_l1b`.

- [ ] **Step 3: Iterar hasta PASS** (ajustar mocks según output del FAIL)

Cuando passe, ese test ya valida BT path básica.

- [ ] **Step 4: Tests adicionales — Paths NTI, vent, sigma gates**

Agregar 7 más al archivo (uno por behavior crítica). Cada uno mismo patrón mockear:
1. `test_no_anomalous_when_bg_uniform` (no false positives en escena uniforme)
2. `test_nti_path_fires_when_bt_below_threshold_but_nti_high`
3. `test_vent_path_detects_subkelvin_anomaly_in_vent_radius`
4. `test_sigma_gate_blocks_pixel_below_n_sigma`
5. `test_local_roi_threshold_blocks_pixel_below_p95` (D7 — confirma comportamiento)
6. `test_returns_none_when_volcano_outside_granule`
7. `test_diag_fields_populated_in_return_dict`

(Esqueleto inline aquí; cada uno ~20 líneas de mock + assert).

- [ ] **Step 5: Run full suite y commit**

```bash
pytest 2>&1 | tail -3
# Expected: 136+ passed
git add tests/test_process_modis_core.py
git commit -m "S23 T5 — process_modis.py core TDD (8 tests)

Audit S22: process_modis.py NO tenía tests dedicados a pesar de procesar
50% de records Tier A. Cubierto solo via tests indirectos S18+ forenses.

8 tests con arrays sintéticos 50×50 + mocks de read_modis_l1b/interp_geo:
- BT path detection
- No false positives en escena uniforme
- NTI path standalone (sin BT path)
- Vent path sub-Kelvin
- Sigma gate blocking
- Local ROI threshold (D7 documenta el comportamiento)
- ROI fuera de granule retorna None
- diag_* fields presentes en return

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 6: store.py append_record TDD — edge cases

**Files:**
- Test: `tests/test_store_append_record.py` (nuevo)

**Contexto**: store.py asume que records traen ciertos campos. Múltiples edge cases sin test.

- [ ] **Step 1: Test failing — key collision por mismo (datetime, sensor)**

```python
"""Tests TDD para store.append_record edge cases (S23 audit followup)."""
from __future__ import annotations
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.store import append_record


def _basic_record(dt="2026-04-10 05:00", sensor="VIIRS_NOAA20",
                  vrp=0.5, vrp_vent=0.0):
    return {
        "vrp_mir_mw": vrp,
        "vrp_vent_mw": vrp_vent,
        "n_anomalous_pixels": 1,
        "n_vent_pixels": 0,
        "vent_hotspot_lat": None,
        "vent_hotspot_lon": None,
        "vent_hotspot_dist_km": None,
        "hotspot_lat": -33.4, "hotspot_lon": -69.8, "hotspot_dist_km": 1.0,
        "final_hotspot_lat": -33.4, "final_hotspot_lon": -69.8,
        "final_hotspot_dist_km": 1.0, "final_hotspot_source": "eruption",
        "distance_class": "summit",
        "anomaly_pixels": [],
        "t_bg_k": 265.0, "t_max_i04_k": 270.0,
        "sensor": sensor, "granule": f"fake_{dt}_{sensor}.nc",
        "product_version": "standard", "datetime_utc": dt,
    }


def test_append_record_no_duplicate_key(tmp_path):
    """Mismo (datetime, sensor) NO debe duplicar — overwrite or skip."""
    out = tmp_path / "data" / "mirova_equivalent"
    out.mkdir(parents=True)

    rec = _basic_record(vrp=0.5)
    append_record("V", rec, -33.4, -69.8, overwrite=False,
                  max_hotspot_dist_km=25.0, out_dir=out)
    append_record("V", rec, -33.4, -69.8, overwrite=False,
                  max_hotspot_dist_km=25.0, out_dir=out)
    data = json.loads((out / "V.json").read_text())
    assert len(data["records"]) == 1, "duplicate key debió saltarse"


def test_append_record_overwrite_replaces_existing(tmp_path):
    """overwrite=True reemplaza record con mismo (datetime, sensor)."""
    out = tmp_path / "data" / "mirova_equivalent"
    out.mkdir(parents=True)

    rec1 = _basic_record(vrp=0.5)
    rec2 = _basic_record(vrp=1.0)  # mismo dt+sensor, distinto vrp
    append_record("V", rec1, -33.4, -69.8, overwrite=True,
                  max_hotspot_dist_km=25.0, out_dir=out)
    append_record("V", rec2, -33.4, -69.8, overwrite=True,
                  max_hotspot_dist_km=25.0, out_dir=out)
    data = json.loads((out / "V.json").read_text())
    assert len(data["records"]) == 1
    assert data["records"][0]["vrp_mir_mw"] == 1.0


def test_append_record_far_hotspot_filtered(tmp_path):
    """Si final_hotspot_dist_km > max_hotspot_dist_km, record SE FILTRA."""
    out = tmp_path / "data" / "mirova_equivalent"
    out.mkdir(parents=True)

    rec = _basic_record()
    rec["final_hotspot_dist_km"] = 30.0  # > 25 km max
    append_record("V", rec, -33.4, -69.8, overwrite=False,
                  max_hotspot_dist_km=25.0, out_dir=out)
    json_path = out / "V.json"
    if json_path.exists():
        data = json.loads(json_path.read_text())
        # filtrado o aceptado pero con vrp=0 — comportamiento esperado documentar
        # Si record se acepta, debe tener vrp_mw=0 (filtro por distancia)
        if data["records"]:
            r = data["records"][0]
            assert (r.get("vrp_mw") or r.get("vrp_mir_mw")) == 0


def test_append_record_sanity_cap_50k_mw(tmp_path):
    """vrp_mw que excede 50,000 MW debe saturarse al cap (M4 S19)."""
    out = tmp_path / "data" / "mirova_equivalent"
    out.mkdir(parents=True)

    rec = _basic_record(vrp=100_000.0)  # Imposible físicamente
    append_record("V", rec, -33.4, -69.8, overwrite=False,
                  max_hotspot_dist_km=25.0, out_dir=out)
    data = json.loads((out / "V.json").read_text())
    if data["records"]:
        v = data["records"][0].get("vrp_mw") or data["records"][0].get("vrp_mir_mw")
        assert v <= 50_000.0
```

- [ ] **Step 2-5: Run test, ajustar firma `append_record` según código real, iterar hasta PASS, commit**

```bash
git add tests/test_store_append_record.py
git commit -m "S23 T6 — store.append_record edge cases TDD (4 tests)

Cubre: dup key handling, overwrite mode, far hotspot filter, sanity cap M4.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 7: scan_geometry.py TDD — 6 tests

**Files:**
- Test: `tests/test_scan_geometry.py` (nuevo)

**Contexto**: scan_geometry.py (172 líneas) tiene cálculos críticos (zenithal correction, bbox mask, pixel areas) sin tests dedicados. Solo via uso indirecto en process_*.py.

- [ ] **Step 1-7: Tests TDD para**:
1. `area_factor_from_zenith(0)` == 1.0 (nadir)
2. `area_factor_from_zenith(60)` ≈ 8.0 (sec³(60°)=8)
3. `area_factor_from_zenith(70)` capped (no runaway)
4. `modis_zenith_from_column(677)` ≈ 0 (center column)
5. `modis_pixel_areas` shape match input + nadir column == 1e6
6. `roi_mask_bbox` square bbox correct + corners inside
7. `viirs_pixel_areas` capped to 2.0× nadir
8. `haversine_km` (ya en Task 2 — no duplicar)

(Cada uno ~10-15 líneas con seed fijo para reproducibilidad).

- [ ] Commit:

```bash
git add tests/test_scan_geometry.py
git commit -m "S23 T7 — scan_geometry.py TDD (8 tests)

Cubre: zenithal correction sec³, MODIS column→zenith, pixel areas
(MODIS + VIIRS aggregated), bbox ROI mask. Antes solo cobertura
indirecta via process_*.py.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 8: Expand M1 golden tests (4 → 10+ records)

**Files:**
- Modify: `tests/test_golden_records.py`

**Contexto**: M1 golden tests instalados S19 cubren solo 4 records canónicos. Audit S22 detectó que faltan casos para regresión P3.1, sigma-gating S12, NOAA-21 boundary.

- [ ] **Step 1: Identificar 6+ records canónicos adicionales**

Casos a cubrir:
1. P3.1 dual-ROI summit hot pixel (Lascar c1=0.003)
2. P3.1 dual-ROI scene cold pixel debajo c1=0.010 (no detectado)
3. Sigma-gating S12 F1 regresión: pixel detectado por path D pero filtrado por sigma cap (Tupungatito)
4. NOAA-21 first record post-S18: Lascar 2026-04-15 algún VIIRS_NOAA21
5. Regla D vent-priority (S20): Tupungatito record con vrp_vent>0 → distance_class=summit
6. Regla D edge: vrp_vent>0 sin vent_hotspot_* (S23 Task 1 fix) — distance_class queda eruption-path
7. (opcional) Sanity cap M4: record con vrp_mw cerca de 50K saturado

- [ ] **Step 2: Para cada caso, identificar el record real en data/mirova_equivalent/<vol>.json**

Use un script auxiliar para listarlos:

```python
import json
d = json.load(open('data/mirova_equivalent/Tupungatito.json'))
for r in d['records'][-200:]:
    if (r.get('vrp_vent_mw') or 0) > 0 and r.get('distance_class') == 'summit':
        print(r['datetime_utc'], r['sensor'])
        break
```

- [ ] **Step 3: Add a `test_golden_records.py` 6 nuevos tests parametrizados**

```python
GOLDEN_RECORDS_S23 = [
    {
        "name": "p3_1_summit_lascar",
        "volcano": "Lascar",
        "datetime_utc": "<dt real>",
        "sensor": "VIIRS_NOAA20",
        "expected": {"distance_class": "summit", "diag_n_dnti_ctx_path": ">0"},
    },
    # ... 5 más
]


@pytest.mark.parametrize("case", GOLDEN_RECORDS_S23, ids=lambda c: c["name"])
def test_golden_record_invariant(case):
    d = json.load(open(f'data/mirova_equivalent/{case["volcano"]}.json'))
    rec = next((r for r in d["records"]
                if r["datetime_utc"] == case["datetime_utc"]
                and r["sensor"] == case["sensor"]), None)
    assert rec is not None, f"Record no encontrado: {case}"
    for k, expected in case["expected"].items():
        actual = rec.get(k)
        if isinstance(expected, str) and expected.startswith(">"):
            threshold = float(expected[1:])
            assert (actual or 0) > threshold, f"{k}={actual} no es >{threshold}"
        else:
            assert actual == expected, f"{k}={actual} != {expected}"
```

- [ ] **Step 4: Run + commit**

```bash
pytest tests/test_golden_records.py -v
git add tests/test_golden_records.py
git commit -m "S23 T8 — M1 golden tests expandidos (4→10+ records canónicos)

Cubre regresiones P3.1, S12 F1 sigma-gating, NOAA-21 boundary,
Regla D normal + edge, M4 sanity cap.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

## FASE 4 — Asunciones no testeadas (con descargas, ~4-6h)

> **Nota**: Los tasks de esta fase requieren descarga de granules NASA o lectura de papers. Outline con criterios de aceptación; código exacto se escribe iterativamente.

### Task 9: experiments/42 — E33 P3.1 dual-ROI validation reproceso

**Goal**: ejecutar el reproceso que S15 implementó pero nunca validó cuantitativamente.

**Files**: `experiments/42_p3_1_dual_roi_validation.py`, `experiments/42_results.{json,md}`

**Approach**:
1. Crear profile temporal `_p3_1_disabled` que setea `enable_dnti_dual_roi: false`.
2. Reproceso 14 días sobre 3 Tier A (Tupungatito, Lascar, Lastarria).
3. Forense replicable comparativa baseline (P3.1 on) vs disabled.
4. Decisión: si P3.1 sube recall sin degradar precision → mantener; si no → considerar quitar.

**Criterios aceptación**:
- ✅ Reproceso completo con ambos profiles
- ✅ Forense per-record compara `class_changed` summit/far entre profiles
- ✅ Tabla delta TP/T4 por volcán
- ✅ Decisión documentada en `docs/DRIFTS_S17.md` (D8 si aplica)

**Esfuerzo**: ~2h reproceso + 1h análisis + 30min commit.

---

### Task 10: experiments/43 — experimental.yaml audit

**Goal**: documentar diferencias `experimental.yaml` vs `mirova_equivalent.yaml` y decidir si experimental sigue activo o se archiva.

**Files**: `experiments/43_audit_experimental_yaml.py`, modificación posible `pipeline/profiles/experimental.yaml`.

**Approach**:
1. Diff línea por línea entre los 2 YAMLs.
2. Para cada diferencia: ¿está justificada? ¿Test que falle si se cambia?
3. Si experimental obsoleto → marcar deprecated o renombrar `_ARCHIVE_experimental.yaml`.

**Criterios aceptación**:
- ✅ Tabla de diffs con justificación
- ✅ Decisión activo/archive
- ✅ Tests existentes siguen verde

**Esfuerzo**: 30 min.

---

### Task 11: NTI floor 0.005 — origen y validación

**Goal**: rastrear el origen de `NTI_REL_MIN_FLOOR=0.005` (no aparece en papers auditados). Decidir mantener/cambiar/justificar.

**Files**: solo lectura (git log + docs).

**Approach**:
1. `git log -p pipeline/profile.py | grep -B5 "0.005"` para encontrar commit original.
2. Leer comentario/PR de ese commit.
3. Si justificación empírica → documentar en `docs/PAPERS_AUDIT.md` como "asunción local validada en S\#X".
4. Si sin justificación → A/B test rápido (filtrar 0.001 vs 0.005 vs 0.01) si tiempo permite, o documentar como "open question".

**Criterios aceptación**:
- ✅ Origen identificado con commit + sesión
- ✅ Justificación documentada (empírica o "asunción a validar")
- ✅ Test si encontramos respaldo de paper

**Esfuerzo**: 30 min.

---

### Task 12: Coppola 2016a "second run" — leer paper completo §spatial processing

**Goal**: confirmar si MIROVA aplica un "segundo run" recomputando bg sin pixels activos. Si sí, considerar implementarlo.

**Files**: solo lectura del paper PDF + posible nota en `docs/PAPERS_AUDIT.md`.

**Approach**:
1. Abrir Coppola 2016a SP 426.5 PDF (debería estar en `documentacion/`).
2. Leer §"Spatial processing" / §"Background calculation" completo.
3. Si menciona segundo run → documentar exacto + criterio testable.
4. Si NO → cerrar como "open question resuelta".

**Criterios aceptación**:
- ✅ Paper section completamente leída
- ✅ Decisión: implementar / no aplica / pendiente
- ✅ Update PAPERS_AUDIT con findings

**Esfuerzo**: 1h.

---

## FASE 5 — Investigaciones científicas (descargas, ~6-10h)

### Task 13: Audit 10 papers Vault no procesados

**Papers**: Coppola 2010 (genealogía VRP), 2013 (c_rad), 2020 (review), 2021 (review), 2025 rapid; Massimetti 2024×3; Laiolo 2026; ATBD VIIRS Calibration 2014.

**Files**: `docs/PAPERS_AUDIT.md` extender con secciones por paper.

**Approach**: para cada paper, extraer claims operacionales con valores específicos (umbrales, coeficientes, geometrías). Marcar si nuestro código los implementa.

**Criterios aceptación**: 10 papers tienen sección en PAPERS_AUDIT con tabla de claims + status (implementado/no/N/A).

**Esfuerzo**: 4-6h (~30 min/paper).

---

### Task 14: experiments/44 — Factor 42 clustering MIROVA

**Goal**: descifrar por qué nuestros 77 px ≠ 4 MIROVA en escena Lascar 2025-11-15. Hipótesis: MIROVA agrupa pixels contiguos en cluster.

**Files**: `experiments/44_factor_42_clustering.py`, output JSON/MD.

**Approach**:
1. Cargar nuestros 77 anomaly_pixels Lascar fecha específica.
2. Aplicar `scipy.ndimage.label` con conectividad 4-vecinos. ¿Sale 4-5 clusters? Si sí → MATCH.
3. Probar 8-vecinos también.
4. Si NO match → leer Massimetti 2024 + buscar "cluster" / "agrupación" en código MIROVA referenciado.

**Criterios aceptación**:
- ✅ Hipótesis clustering testeada
- ✅ Si confirma → implementar opcional como output adicional pipeline (no cambia detección)
- ✅ Documentar en `docs/HYPOTHESIS_LOG.md` como H_S23_FACTOR42

**Esfuerzo**: 2-3h.

---

### Task 15: experiments/45 — Di Bella 2024 k_VIIRS A/B

**Goal**: validar empíricamente cual k_VIIRS_I4 es correcto: nuestro 18.0 (Campus) o Di Bella 2.48×10⁷.

**Files**: `experiments/45_dibella_k_viirs_ab.py`.

**Approach**:
1. Tomar 10 pasadas VIIRS I4 Tupungatito con MIROVA refs.
2. Computar VRP con ambos coefs.
3. Comparar con MIROVA OSF/NRT VRP reportado.
4. ¿Cuál minimiza error mediano?

**Criterios aceptación**:
- ✅ Decisión basada en data: mantener Campus o adoptar Di Bella
- ✅ Si Di Bella gana → reproceso completo + validación contra OSF S14

**Esfuerzo**: 1h descarga + 1h análisis.

---

### Task 16: experiments/46 — VRP_TIR Aveni 2025 para Villarrica

**Goal**: scope decision — ¿implementar VRP_TIR como Path D paralelo? Para Villarrica recall 0% (sub-pixel <600K).

**Files**: `experiments/46_aveni_tir_villarrica.py` (POC standalone).

**Approach**:
1. Bajar 5 pasadas VIIRS Villarrica con MIROVA refs.
2. Implementar VRP_TIR Eq.9 Aveni 2025 (k_TIR=60.17) ad-hoc (no integrar al pipeline).
3. ¿Detecta señales que Path A/B/C/D MIR pierden?
4. Decisión: implementar Path TIR (scope grande, S25+) o aceptar Villarrica gap.

**Criterios aceptación**:
- ✅ POC ejecutado con 5 granules
- ✅ Decisión documentada con evidencia

**Esfuerzo**: 3-4h (descarga + POC).

---

## FASE 6 — Mejoras operacionales (~3-4h, sin descargas)

### Task 17: Centralizar constantes físicas

**Goal**: SIGMA, C1, C2 Planck duplicados en 3-4 archivos → módulo `pipeline/constants.py` único.

**Files**: `pipeline/constants.py` (nuevo), modificar 3 procesadores.

**Aceptación**: 119+ tests verde, una sola definición.

**Esfuerzo**: 30 min.

---

### Task 18: P95_VENT_EXCLUSION_KM a profile YAML

**Goal**: hardcoded en process_modis.py → configurable por volcán/profile.

**Aceptación**: profile.yaml, profile.py, process_modis.py actualizados; default 5.0 km mantenido.

**Esfuerzo**: 30 min.

---

### Task 19: Frontend panel diag_*

**Goal**: aprovechar diag_* poblados S22.1 para panel diagnóstico opcional en dashboard.

**Files**: `frontend/index.html` modificación.

**Aceptación**: hover en record muestra `sigma_bg`, `eff_threshold`, `roi_p95`, paths que dispararon.

**Esfuerzo**: 1-2h.

---

### Task 20: scripts/ cleanup + README

**Goal**: documentar cuáles de los 11 scripts legacy aún son útiles.

**Files**: `scripts/README.md` (nuevo).

**Aceptación**: tabla con script, propósito, sesión origen, status (útil/legacy/deprecated).

**Esfuerzo**: 1h.

---

### Task 21: experiments/47 — JSON inflación Chaitén/Lascar audit

**Goal**: investigar por qué Chaitén 8.6 MB y Lascar 22 MB. ¿Campos pesados innecesarios?

**Files**: `experiments/47_json_inflation_audit.py`.

**Aceptación**: identificación de campo inflado + decisión (compresión/dedup/aceptar).

**Esfuerzo**: 1h.

---

### Task 22: Trigger _site Pages deploy + verificar

**Goal**: forzar regenerar GitHub Pages que está stale 21 días.

**Approach**: `gh workflow run pages-deploy.yml` o push trivial a frontend.

**Aceptación**: GitHub Pages refleja último commit main.

**Esfuerzo**: 5 min.

---

## FASE 7 — Cierre S23

### Task 23: Update docs vivos + memoria

**Files:**
- `docs/SESSION_INDEX.md`: fila S23 con todos los hallazgos cerrados.
- `docs/HYPOTHESIS_LOG.md`: H_S23_* registradas + cierres.
- `docs/DRIFTS_S17.md`: D7 (local ROI), D8 si aplica.
- `~memory/project_s23_findings.md`: hallazgos S23.
- `tasks/handoff_s24_*.md`: handoff con outstanding items.

**Aceptación**: SESSION_CLOSE_CHECKLIST bloques A-F todos verdes.

**Esfuerzo**: 30 min.

---

## Self-Review

**1. Spec coverage** (18 hallazgos audit S22):

| # | Hallazgo | Task |
|---|---|---|
| 1 | MODIS-VIIRS local ROI divergencia | Task 3 (D7 doc) ✅ |
| 2 | Regla D edge case | Task 1 ✅ |
| 3 | process_modis sin tests | Task 5 ✅ |
| 4 | Factor 42 clustering | Task 14 ✅ |
| 5 | E33 P3.1 reproceso | Task 9 ✅ |
| 6 | VRP_TIR Aveni 2025 | Task 16 ✅ |
| 7 | Di Bella k_VIIRS A/B | Task 15 ✅ |
| 8 | haversine None | Task 2 ✅ |
| 9 | viirs/store/scan_geom tests | Tasks 6, 7 ✅ |
| 10 | P95_VENT_EXCLUSION_KM | Task 18 ✅ |
| 11 | M1 golden expand | Task 8 ✅ |
| 12 | 10 papers Vault | Task 13 ✅ |
| 13 | Coppola 2° run | Task 12 ✅ |
| 14 | NTI 0.005 floor | Task 11 ✅ |
| 15 | experimental.yaml | Task 10 ✅ |
| 16 | JSON inflación | Task 21 ✅ |
| 17 | _site stale | Task 22 ✅ |
| 18 | Constantes duplicadas | Task 17 ✅ |

Frontend panel + cron NRT validation: Tasks 4, 19. **Cobertura: 18/18 + 2 extras = 20 tasks**.

**2. Placeholder scan**: ningún "TBD" / "implement later". Tasks 9-22 (Fases 4-7) son outlines con criterios concretos pero código exacto se itera al ejecutar — esto es deliberado dado que dependen de findings de Fases anteriores.

**3. Type consistency**: `haversine_km`, `append_record`, `calculate_vrp` mantienen mismas firmas a lo largo del plan.

**4. Riesgos identificados**:
- Task 5 (process_modis TDD) requiere mockear loaders complejos. Tiempo real puede ser 6h.
- Task 9 (E33) requiere descargas — bloqueable por NRT inestabilidad.
- Tasks 13-16 son investigación con scope variable.

---

## Execution Handoff

**Plan completo y guardado a `docs/superpowers/plans/2026-04-26-s23-audit-followup.md`. Dos opciones:**

**1. Inline Execution (recomendado para esta sesión)** — Ejecuto Tasks 1-8 ahora (Fases 1+3, ~6h trabajo TDD), checkpoint cada Task. Aprovecha contexto largo. Fases 4-7 las hacemos en sesiones siguientes con sub-plans dedicados.

**2. Subagent-Driven** — Despacho subagente fresco por Task con review entre tasks. Útil para Tasks 5, 13 (carga grande). Bajo costo de context switch.

**Mi recomendación**: **Inline + arrancar por Fase 1 (Tasks 1-3)** ahora. Son los bugs latentes en producción (~2-3h), bajo riesgo, alto valor. Después decidimos si seguimos Fase 3 (cobertura tests, ~6h) o cerramos sesión.

¿Cuál preferís?
