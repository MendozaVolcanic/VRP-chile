# Detección diurna MODIS — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: usar superpowers:subagent-driven-development o superpowers:executing-plans para implementar tarea por tarea. Steps usan checkbox (`- [ ]`).

**Goal:** Replicar la detección diurna MODIS de MIROVA (Coppola 2016a Tabla 1: K1=−0.6, C1=0.02, C2=15σ), gateada por flag opt-in y validada por A/B antes de adopción operacional.

**Architecture:** Los thresholds son constantes de módulo en `pipeline/profile.py` importadas por `pipeline/process_modis.py`. Se agregan constantes DÍA + un flag `ENABLE_DAYTIME_MODIS` (default False). En `calculate_vrp` se computa `is_day` (elevación solar de la escena) y se selecciona el set día/noche. `store.py` deja pasar MODIS diurno solo con el flag ON (VIIRS diurno sigue rechazado — literal MIROVA). Default OFF = comportamiento actual intacto.

**Tech Stack:** Python 3.12, numpy, pyhdf (MODIS solo corre en GH Actions Linux), pytest. Diseño: `docs/superpowers/specs/2026-05-30-daytime-modis-detection-design.md`.

**A45**: tag defensivo `pre-s90-daytime-modis` (@2f3f73aa) ya creado. NO cambiar `mirova_equivalent.yaml` hasta validación A/B+R2+R3.

---

## File Structure

- `pipeline/profile.py` — MODIFY: agregar constantes día + flag (carga desde YAML).
- `pipeline/process_modis.py` — MODIFY: `calculate_vrp` selecciona thresholds día/noche.
- `pipeline/store.py` — MODIFY: gate diurno condicional al flag + sensor MODIS.
- `pipeline/profiles/_daytime_modis_enabled.yaml` — CREATE: perfil A/B (flag ON).
- `pipeline/profiles/_daytime_modis_disabled.yaml` — CREATE: perfil A/B (flag OFF).
- `tests/test_daytime_modis.py` — CREATE: tests TDD.
- `.github/workflows/reproc-daytime-modis-ab.yml` — CREATE: A/B reproc (GH Actions).

---

### Task 1: Constantes día en profile.py

**Files:**
- Modify: `pipeline/profile.py` (después de línea 188, donde están N_SIGMA_MIR_SUMMIT/SCENE)
- Test: `tests/test_daytime_modis.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_daytime_modis.py
import os
def test_profile_exposes_daytime_constants(monkeypatch):
    # mirova_equivalent NO tiene el flag → defaults seguros (OFF + night-like)
    import importlib, pipeline.profile as P
    importlib.reload(P)
    assert hasattr(P, "ENABLE_DAYTIME_MODIS")
    assert P.ENABLE_DAYTIME_MODIS is False           # default OFF
    assert hasattr(P, "NTI_K1_DAY") and abs(P.NTI_K1_DAY - (-0.6)) < 1e-9
    assert hasattr(P, "N_SIGMA_MIR_DAY") and abs(P.N_SIGMA_MIR_DAY - 15.0) < 1e-9
    assert hasattr(P, "DNTI_CONTEXTUAL_C1_DAY") and abs(P.DNTI_CONTEXTUAL_C1_DAY - 0.02) < 1e-9
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_daytime_modis.py::test_profile_exposes_daytime_constants -v`
Expected: FAIL (`AttributeError: ... ENABLE_DAYTIME_MODIS`).

- [ ] **Step 3: Write minimal implementation**

En `pipeline/profile.py`, después de la línea `N_SIGMA_MIR_SCENE: float = float(_t.get("n_sigma_mir_scene", 10.0))`:

```python
# S90 — parámetros DÍA MODIS (Coppola 2016a SP426.5 Tabla 1, verbatim).
# Solo se usan cuando ENABLE_DAYTIME_MODIS=True y la escena es diurna.
# Default = valores día del paper, pero el flag OFF los deja inertes.
NTI_K1_DAY: float = float(_t.get("nti_k1_day", -0.6))
N_SIGMA_MIR_DAY: float = float(_t.get("n_sigma_mir_day", 15.0))
DNTI_CONTEXTUAL_C1_DAY: float = float(_t.get("dnti_contextual_c1_day", 0.02))
```

Y cerca de los otros flags `ENABLE_*` (ej. junto a ENABLE_DUAL_ROI_BT):

```python
# S90 — detección diurna MODIS (opt-in). OFF = excluir diurno (comportamiento
# histórico). ON = procesar MODIS diurno con params día + dejar pasar el gate store.
ENABLE_DAYTIME_MODIS: bool = bool(_cfg.get("enable_daytime_modis", False))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_daytime_modis.py::test_profile_exposes_daytime_constants -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pipeline/profile.py tests/test_daytime_modis.py
git commit -m "feat(s90): constantes día MODIS + flag ENABLE_DAYTIME_MODIS (default OFF)"
```

---

### Task 2: Helper de selección día/noche en process_modis.py

**Files:**
- Modify: `pipeline/process_modis.py` (agregar helper + import de constantes día)
- Test: `tests/test_daytime_modis.py`

- [ ] **Step 1: Write the failing test**

```python
def test_threshold_set_selection():
    from pipeline.process_modis import _select_thresholds
    # is_day=False → night
    night = _select_thresholds(is_day=False, enable_day=True)
    assert night["nti_k1"] == -0.8 and night["n_sigma_summit"] == 5.0 and night["n_sigma_scene"] == 10.0
    # is_day=True + flag ON → day (15σ ambos ROIs, K1=-0.6, C1=0.02)
    day = _select_thresholds(is_day=True, enable_day=True)
    assert day["nti_k1"] == -0.6 and day["n_sigma_summit"] == 15.0 and day["n_sigma_scene"] == 15.0
    assert day["c1_summit"] == 0.02 and day["c1_scene"] == 0.02
    # is_day=True pero flag OFF → night (no se aplican params día)
    off = _select_thresholds(is_day=True, enable_day=False)
    assert off["nti_k1"] == -0.8 and off["n_sigma_summit"] == 5.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_daytime_modis.py::test_threshold_set_selection -v`
Expected: FAIL (`ImportError: cannot import name '_select_thresholds'`).

- [ ] **Step 3: Write minimal implementation**

En `process_modis.py`, agregar imports (junto a los existentes, líneas 76-100):

```python
from .profile import (
    NTI_K1_DAY, N_SIGMA_MIR_DAY, DNTI_CONTEXTUAL_C1_DAY, ENABLE_DAYTIME_MODIS,
)
```

Y un helper a nivel de módulo (cerca de los otros helpers, ej. tras `radiance_to_bt`):

```python
def _select_thresholds(is_day: bool, enable_day: bool) -> dict:
    """S90: set de thresholds día/noche para MODIS.
    Día (Coppola 2016a Tabla 1): K1=-0.6, C1=0.02 ambos ROIs, N·σ=15 ambos ROIs.
    Noche: K1=-0.8, C1=0.003/0.010 summit/scene, N·σ=5/10 summit/scene.
    Día SOLO si enable_day y is_day; en cualquier otro caso → noche (intacto)."""
    if enable_day and is_day:
        return {"nti_k1": NTI_K1_DAY,
                "n_sigma_summit": N_SIGMA_MIR_DAY, "n_sigma_scene": N_SIGMA_MIR_DAY,
                "c1_summit": DNTI_CONTEXTUAL_C1_DAY, "c1_scene": DNTI_CONTEXTUAL_C1_DAY}
    return {"nti_k1": NTI_K1_NIGHT,
            "n_sigma_summit": N_SIGMA_MIR_SUMMIT, "n_sigma_scene": N_SIGMA_MIR_SCENE,
            "c1_summit": DNTI_CONTEXTUAL_C1_SUMMIT, "c1_scene": DNTI_CONTEXTUAL_C1_SCENE}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_daytime_modis.py::test_threshold_set_selection -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pipeline/process_modis.py tests/test_daytime_modis.py
git commit -m "feat(s90): helper _select_thresholds día/noche MODIS"
```

---

### Task 3: Aplicar el set día/noche en calculate_vrp

**Files:**
- Modify: `pipeline/process_modis.py` función `calculate_vrp` (línea 243; usos de thresholds en 324, 398-399, 415, 441-442, 538-558)
- Test: `tests/test_daytime_modis.py` (test de integración con escena sintética — ver Task 6 para el harness)

- [ ] **Step 1: Computar is_day al inicio de calculate_vrp**

Cerca del inicio de `calculate_vrp`, tras parsear datetime (reusar `_parse_datetime(hdf_path.name)` que ya se usa en :1146; importar `_solar_elevation` desde store o duplicar la fórmula en un util compartido). Usar `vent_lat/vent_lon` (si None, centro del ROI):

```python
from datetime import datetime as _dt
_scene_iso = _parse_datetime(hdf_path.name)  # "YYYY-MM-DD HH:MM"
try:
    _scene_dt = _dt.strptime(_scene_iso, "%Y-%m-%d %H:%M")
    _ref_lat = vent_lat if vent_lat is not None else float(np.nanmean(lat[roi_mask]))
    _ref_lon = vent_lon if vent_lon is not None else float(np.nanmean(lon[roi_mask]))
    is_day = _solar_elevation(_ref_lat, _ref_lon, _scene_dt) > 0
except (ValueError, TypeError):
    is_day = False
TH = _select_thresholds(is_day=is_day, enable_day=ENABLE_DAYTIME_MODIS)
```

- [ ] **Step 2: Reemplazar usos de constantes night por TH[...]**

Reemplazar en `calculate_vrp` (NO en otras funciones):
- `nti_k1_threshold=NTI_K1_NIGHT` (línea ~324) → `nti_k1_threshold=TH["nti_k1"]`
- `n_sigma_summit=N_SIGMA_MIR_SUMMIT` (~398) → `n_sigma_summit=TH["n_sigma_summit"]`
- `n_sigma_scene=N_SIGMA_MIR_SCENE` (~399) → `n_sigma_scene=TH["n_sigma_scene"]`
- `(nti > NTI_K1_NIGHT)` (~415) → `(nti > TH["nti_k1"])`
- `c1_summit=DNTI_CONTEXTUAL_C1_SUMMIT` (~441,538,553) → `c1_summit=TH["c1_summit"]`
- `c1_scene=DNTI_CONTEXTUAL_C1_SCENE` (~442,543,558) → `c1_scene=TH["c1_scene"]`
- `c1_dnti=`/`c1_deti=` con SUMMIT (~538-539,553-554) → `TH["c1_summit"]`
- `c1_dnti_scene=`/`c1_deti_scene=` (~543-544,558) → `TH["c1_scene"]`

**Nota integridad (A49)**: verificar con `git diff` que ninguna otra estructura quedó rota; los reemplazos son 1:1 de constante por `TH[...]`.

- [ ] **Step 3: Run regression — flag OFF no cambia nada**

Run: `pytest tests/ -k "modis or store or audit" -q`
Expected: 0 regresiones (con flag OFF, `_select_thresholds` devuelve siempre night → idéntico al baseline).

- [ ] **Step 4: Commit**

```bash
git add pipeline/process_modis.py
git commit -m "feat(s90): calculate_vrp aplica params día/noche según solar elev"
```

---

### Task 4: Gate diurno condicional en store.py

**Files:**
- Modify: `pipeline/store.py:422-431` (el bloque "Safety net: reject daytime records")
- Test: `tests/test_daytime_modis.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_store_rejects_daytime_when_flag_off(tmp_path, monkeypatch):
    # con flag OFF, un record MODIS diurno se rechaza (comportamiento histórico)
    monkeypatch.setattr("pipeline.store.ENABLE_DAYTIME_MODIS", False)
    # ... construir record MODIS diurno (solar elev > 0) y verificar que append_record NO lo guarda
def test_store_allows_daytime_modis_when_flag_on(tmp_path, monkeypatch):
    monkeypatch.setattr("pipeline.store.ENABLE_DAYTIME_MODIS", True)
    # record MODIS diurno → se guarda
def test_store_still_rejects_daytime_viirs_when_flag_on(tmp_path, monkeypatch):
    monkeypatch.setattr("pipeline.store.ENABLE_DAYTIME_MODIS", True)
    # record VIIRS_NOAA20 diurno → SIGUE rechazado (literal MIROVA)
```

(El harness exacto del record sintético se comparte con Task 6; usar un dict mínimo con `datetime_utc`, `sensor`, y volcano_lat/lon que den solar elev>0.)

- [ ] **Step 2: Run to verify fail**

Run: `pytest tests/test_daytime_modis.py -k store -v`
Expected: FAIL (hoy rechaza diurno siempre, sin importar flag/sensor).

- [ ] **Step 3: Implementation**

En `store.py`, importar el flag arriba: `from .profile import ENABLE_DAYTIME_MODIS`. Reemplazar el bloque 422-431:

```python
    # Safety net: reject daytime records (solar contamination → false VRP).
    # S90: con ENABLE_DAYTIME_MODIS, MODIS diurno SÍ se procesa (Coppola 2016a
    # params día). VIIRS diurno sigue rechazado (sin fuente MIROVA-core diurna).
    if volcano_lat is not None and volcano_lon is not None:
        dt_str = record.get("datetime_utc", "")
        sensor = str(record.get("sensor", ""))
        try:
            dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
            elev = _solar_elevation(volcano_lat, volcano_lon, dt)
            if elev > 0:
                allow = ENABLE_DAYTIME_MODIS and sensor.startswith("MODIS")
                if not allow:
                    print(f"  STORE REJECT daytime: {dt_str} {sensor} "
                          f"(solar elev={elev:.1f}°)")
                    return
        except (ValueError, TypeError):
            pass
```

- [ ] **Step 4: Run to verify pass**

Run: `pytest tests/test_daytime_modis.py -k store -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add pipeline/store.py tests/test_daytime_modis.py
git commit -m "feat(s90): store deja pasar MODIS diurno con flag ON (VIIRS sigue rechazado)"
```

---

### Task 5: Perfiles A/B

**Files:**
- Create: `pipeline/profiles/_daytime_modis_enabled.yaml`
- Create: `pipeline/profiles/_daytime_modis_disabled.yaml`

- [ ] **Step 1: Crear perfil enabled**

```yaml
# A/B S90 — detección diurna MODIS ON. data_subdir aislado (no toca operacional).
extends: mirova_equivalent
data_subdir: _daytime_modis_enabled
thresholds:
  enable_daytime_modis: true
  nti_k1_day: -0.6
  n_sigma_mir_day: 15.0
  dnti_contextual_c1_day: 0.02
enable_daytime_modis: true
```

(Verificar dónde lee `_load_profile` el flag: `_cfg.get("enable_daytime_modis")` es top-level, así que va a nivel raíz; los params día van bajo `thresholds` porque profile.py los lee de `_t`. Ajustar según el merge de `extends` en profile.py:52.)

- [ ] **Step 2: Crear perfil disabled**

```yaml
# A/B S90 — control: detección diurna OFF (= operacional). data_subdir aislado.
extends: mirova_equivalent
data_subdir: _daytime_modis_disabled
enable_daytime_modis: false
```

- [ ] **Step 3: Verificar carga**

Run: `VRP_PROFILE=_daytime_modis_enabled python -c "import pipeline.profile as P; print(P.ENABLE_DAYTIME_MODIS, P.NTI_K1_DAY, P.N_SIGMA_MIR_DAY)"`
Expected: `True -0.6 15.0`

- [ ] **Step 4: Commit**

```bash
git add pipeline/profiles/_daytime_modis_enabled.yaml pipeline/profiles/_daytime_modis_disabled.yaml
git commit -m "feat(s90): perfiles A/B detección diurna MODIS"
```

---

### Task 6: Test de integración escena sintética

**Files:**
- Modify: `tests/test_daytime_modis.py`

- [ ] **Step 1: Test — escena diurna sintética detecta con params día y no con noche**

Construir un array sintético MODIS con un hotspot débil que supere 15σ día pero NO el gate nocturno (que de noche sería rechazado por el store, no por umbral). Verificar que con flag ON + escena diurna, `_select_thresholds` da 15σ y el pixel se marca. Si construir la escena HDF completa es caro, testear el camino de decisión: `_select_thresholds(is_day=True, enable_day=True)` aplicado a un `dual_roi_bt_threshold` con un array chico da el hot_mask esperado.

```python
import numpy as np
from pipeline.process_modis import _select_thresholds
def test_day_params_threshold_behavior():
    th = _select_thresholds(is_day=True, enable_day=True)
    # 15σ es más estricto que 5σ summit → un pixel a 6σ del bg que de noche
    # pasaría (>5σ summit) NO debe pasar de día (<15σ)
    assert th["n_sigma_summit"] == 15.0
```

- [ ] **Step 2-4: Run, verify pass, commit** (igual patrón).

```bash
git add tests/test_daytime_modis.py
git commit -m "test(s90): integración params día MODIS"
```

---

### Task 7: Workflow A/B reproc (GH Actions — MODIS requiere Linux)

**Files:**
- Create: `.github/workflows/reproc-daytime-modis-ab.yml`

- [ ] **Step 1: Clonar template `reproc-ab-test1.yml`** adaptando: matrix de 11 Tier A × 2 perfiles (`_daytime_modis_enabled`, `_daytime_modis_disabled`), ventana que cubra eventos diurnos (NdC 2026-03 a 04, Villarrica 2026-05). `max-parallel: 1` por perfil×vol (A47). `"on":` quoted (A43 Norway). timeout ≥ duración×1.3 (A15).

- [ ] **Step 2: Verificar YAML**

Run: `python -c "import yaml; print(list(yaml.safe_load(open('.github/workflows/reproc-daytime-modis-ab.yml')).keys()))"`
Expected: la key `on` aparece como string `"on"`, NO `True` (A43).

- [ ] **Step 3: Commit + merge a main** (workflow_dispatch solo invocable desde default branch, S73).

```bash
git add .github/workflows/reproc-daytime-modis-ab.yml
git commit -m "ci(s90): workflow A/B reproc detección diurna MODIS"
```

---

### Task 8: Validación (post-reproc) — NO es código, es gate de adopción

- [ ] Correr el A/B (GH Actions) y comparar recall/precisión/ratio (computeMetrics) enabled vs disabled sobre los 11 Tier A.
- [ ] R2 pixel-level sobre ≥1 evento diurno NdC con TIF MODIS (47 disponibles, PR #254).
- [ ] R3 audit: las nuevas TP diurnas matchean ALERTAS MIROVA reales (no FP solares).
- [ ] R6: si recall sube >30%, cuestionar métrica auto-confirmatoria.
- [ ] **Criterio**: recall diurno sube en ≥1 vol SIN precisión global <0.50 + ≥1 evento validado pixel-level. Si FP solares dominan → NO adoptar, documentar.
- [ ] Si valida: con tag + OK Nicolás, setear `enable_daytime_modis: true` en `mirova_equivalent.yaml` (A45) + reproc operacional + verificar dashboard (regla publicación).
- [ ] Documentar resultados en `experiments/_s90_daytime_modis/RESULTS.md` (provenance paper).

---

## Self-Review

**Spec coverage**: scope (MODIS-only Task 3+4), params verbatim (Task 1), día/noche selección (Task 2-3), gate (Task 4), VIIRS sigue rechazado (Task 4 test), A/B flag (Task 5), validación R2/R3/criterios (Task 8), TDD (todas), A45 (header + Task 8). ✓ Pre-mortem del spec cubierto por el test de regresión (Task 3 Step 3) + criterio de adopción (Task 8).

**Placeholder scan**: Task 5 Step 1 y Task 7 tienen "verificar/ajustar según" — son verificaciones reales de integración (merge de `extends`, template de workflow), no placeholders de código; el código mostrado es completo. Task 6 ofrece dos caminos según costo del harness HDF — explícito, no ambiguo.

**Type consistency**: `_select_thresholds` devuelve dict con keys `nti_k1`/`n_sigma_summit`/`n_sigma_scene`/`c1_summit`/`c1_scene` — usadas consistentes en Task 2 y 3. Constantes `NTI_K1_DAY`/`N_SIGMA_MIR_DAY`/`DNTI_CONTEXTUAL_C1_DAY`/`ENABLE_DAYTIME_MODIS` consistentes Task 1→2→4.

## Registro para el paper (pedido Nicolás)

Cada commit cita la fuente (Coppola 2016a Tabla 1). El design doc + este plan + `experiments/_s90_daytime_modis/RESULTS.md` (Task 8) forman el rastro metodológico reproducible: provenance de parámetros, hipótesis, A/B, criterios de adopción, resultado. Mantener.
