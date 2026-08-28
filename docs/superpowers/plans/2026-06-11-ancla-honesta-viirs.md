# Ancla Espacial Honesta — Plan de Implementación VIIRS375 (Fase 1)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans para
> implementar tarea por tarea. Checkboxes para tracking.

**Goal:** Implementar la cascada de ancla honesta flag-OFF en VIIRS375 + A/B de 2 brazos
(vent / NTI-peak), sin tocar detección ni magnitudes (design
`docs/superpowers/specs/2026-06-11-ancla-espacial-honesta-design.md`).

**Architecture:** Helper puro `pipeline/anchor.py` (testeable, primer paso del de-triplicado
P3) + bloque override en `process_viirs.py` DESPUÉS de todos los bloques de magnitud
(que siguen leyendo el `final_hotspot_source` legacy interno) y ANTES del record dict
→ riesgo cero sobre magnitudes, inserción única (A49-safe). Guard en `store.py` para
que el rescate F47 no pise anclas honestas. MODIS/VIIRS750/C1-C2/frontend = Fase 2
(post-A/B, pre-comprometido en design §4).

**Tech Stack:** Python 3.11/3.12, numpy, pytest, GH Actions (patrón S105).

**Scope Fase 1:** `pipeline/anchor.py` (nuevo), `pipeline/process_viirs.py`,
`pipeline/store.py`, `pipeline/profile.py`, 2 profiles A/B, 1 workflow, 1 audit script.

---

### Task 1: Helper puro `resolve_honest_anchor` (TDD)

**Files:**
- Create: `pipeline/anchor.py`
- Test: `tests/test_honest_anchor.py`

- [ ] **Step 1: Test que falla**

```python
"""Tests S106 — cascada de ancla espacial honesta (design 2026-06-11 §3.1).

La cascada decide SOLO posición/clase (lat, lon, dist, source); nunca magnitud.
Casos del design: ctx-cluster gana; Regla D honesta (ctx far + test1 summit →
test1); test1 → vent (modo A) o NTI-peak (modo B, fallback vent); vent-path
legacy; píxel suelto como último recurso documentado; nada → None.
"""
import pytest

from pipeline.anchor import resolve_honest_anchor

VENT = (-33.389044, -69.826374)  # Tupungatito
CTX_SUMMIT = {"centroid_lat": -33.3922, "centroid_lon": -69.8281, "centroid_dist_km": 0.39}
CTX_FAR = {"centroid_lat": -33.30, "centroid_lon": -69.70, "centroid_dist_km": 14.9}
NTI_PEAK = {"lat": -33.3895, "lon": -69.8270, "dist_km": 0.07}
LOOSE = {"lat": -33.28, "lon": -69.66, "dist_km": 19.6}
VENT_HS = {"lat": -33.3891, "lon": -69.8262, "dist_km": 0.02}
INNER = 7.0


def _call(**kw):
    base = dict(ctx_cluster=None, test1_triggered=False, test1_summit_hit=False,
                vent_lat=VENT[0], vent_lon=VENT[1], nti_peak=None,
                vent_hotspot=None, loose_pixel=None, inner_radius_km=INNER,
                mode="vent")
    base.update(kw)
    return resolve_honest_anchor(**base)


def test_ctx_cluster_summit_gana():
    lat, lon, dist, src = _call(ctx_cluster=CTX_SUMMIT, test1_triggered=True,
                                test1_summit_hit=True)
    assert (lat, lon, dist) == (-33.3922, -69.8281, 0.39)
    assert src == "ctx_cluster"


def test_regla_d_honesta_ctx_far_test1_summit_gana_test1():
    lat, lon, dist, src = _call(ctx_cluster=CTX_FAR, test1_triggered=True,
                                test1_summit_hit=True)
    assert (lat, lon) == VENT
    assert dist == 0.0
    assert src == "test1_roi"


def test_ctx_far_sin_test1_ancla_ctx():
    # contextual far sin test1 summit: el cluster ES la detección, far honesto.
    lat, lon, dist, src = _call(ctx_cluster=CTX_FAR)
    assert dist == 14.9
    assert src == "ctx_cluster"


def test_test1_only_modo_vent():
    lat, lon, dist, src = _call(test1_triggered=True, test1_summit_hit=True)
    assert (lat, lon, dist) == (VENT[0], VENT[1], 0.0)
    assert src == "test1_roi"


def test_test1_only_modo_nti_peak():
    lat, lon, dist, src = _call(test1_triggered=True, test1_summit_hit=True,
                                nti_peak=NTI_PEAK, mode="nti_peak")
    assert (lat, lon, dist) == (-33.3895, -69.8270, 0.07)
    assert src == "test1_nti_peak"


def test_modo_nti_peak_sin_peak_cae_a_vent():
    lat, lon, dist, src = _call(test1_triggered=True, test1_summit_hit=True,
                                mode="nti_peak")
    assert (lat, lon, dist) == (VENT[0], VENT[1], 0.0)
    assert src == "test1_roi"


def test_vent_path_legacy_fallback():
    lat, lon, dist, src = _call(vent_hotspot=VENT_HS)
    assert dist == 0.02
    assert src == "vent"


def test_pixel_suelto_ultimo_recurso():
    lat, lon, dist, src = _call(loose_pixel=LOOSE)
    assert dist == 19.6
    assert src == "eruption_loose"


def test_nada_devuelve_none():
    assert _call() == (None, None, None, None)


def test_prioridad_test1_sobre_vent_path_y_loose():
    lat, lon, dist, src = _call(test1_triggered=True, test1_summit_hit=False,
                                vent_hotspot=VENT_HS, loose_pixel=LOOSE)
    # test1 triggered (aunque no summit-hit) con ctx ausente → test1_roi:
    # la integral existe, su posición honesta es el vent del ROI.
    assert src == "test1_roi"
```

- [ ] **Step 2: correr y verificar FAIL**

Run: `python -m pytest tests/test_honest_anchor.py -v -s`
Expected: FAIL `ModuleNotFoundError: No module named 'pipeline.anchor'`

- [ ] **Step 3: implementación mínima**

```python
"""S106 — Ancla espacial honesta (design 2026-06-11 §3.1).

Cascada de POSICIÓN del record (final_hotspot_*). Nunca decide magnitud ni
detección: los bloques de magnitud del pipeline siguen leyendo la semántica
legacy interna; este helper se aplica como override de los campos de posición
justo antes de armar el record.

Principio (auditoría S106 papers-first): un test integrado de ROI no tiene
posición por píxel — la posición MIROVA-real viene de los píxeles flaggeados
por los tests contextuales (Tests 2/3 Coppola 2016a, inmunes a topografía
A69). Cuando solo disparó el Test1 integrado, la posición honesta es el vent
del ROI (modo "vent") o el píxel de NTI máximo del ROI (modo "nti_peak").
"""


def resolve_honest_anchor(ctx_cluster, test1_triggered, test1_summit_hit,
                          vent_lat, vent_lon, nti_peak, vent_hotspot,
                          loose_pixel, inner_radius_km, mode="vent"):
    """Devuelve (lat, lon, dist_km, source) para final_hotspot_*.

    ctx_cluster:  dict centroid_lat/centroid_lon/centroid_dist_km del cluster
                  contextual vent-anchored (hot_mask first-pass, sin Test1) o None.
    nti_peak:     dict lat/lon/dist_km del píxel de NTI máximo del ROI o None.
    vent_hotspot: dict lat/lon/dist_km del vent-path legacy o None.
    loose_pixel:  dict lat/lon/dist_km del píxel suelto scene-wide o None.
    mode:         "vent" | "nti_peak" (destino de los records Test1-dominantes).
    """
    ctx_far = (ctx_cluster is not None and inner_radius_km is not None
               and ctx_cluster["centroid_dist_km"] > inner_radius_km)

    if ctx_cluster is not None and not (ctx_far and test1_summit_hit):
        return (ctx_cluster["centroid_lat"], ctx_cluster["centroid_lon"],
                ctx_cluster["centroid_dist_km"], "ctx_cluster")
    if test1_triggered:
        if mode == "nti_peak" and nti_peak is not None:
            return (nti_peak["lat"], nti_peak["lon"], nti_peak["dist_km"],
                    "test1_nti_peak")
        return (vent_lat, vent_lon, 0.0, "test1_roi")
    if vent_hotspot is not None:
        return (vent_hotspot["lat"], vent_hotspot["lon"],
                vent_hotspot["dist_km"], "vent")
    if loose_pixel is not None:
        return (loose_pixel["lat"], loose_pixel["lon"],
                loose_pixel["dist_km"], "eruption_loose")
    return (None, None, None, None)
```

- [ ] **Step 4: correr y verificar PASS**

Run: `python -m pytest tests/test_honest_anchor.py -v -s`
Expected: 10 passed

- [ ] **Step 5: commit**

```bash
git add pipeline/anchor.py tests/test_honest_anchor.py
git commit -m "feat(s106): helper puro resolve_honest_anchor (TDD, flag-OFF aun sin caller)"
```

---

### Task 2: Flags de perfil

**Files:**
- Modify: `pipeline/profile.py` (junto a `ENABLE_TEST1_LOCAL_BG_NTI`, línea ~288)
- Modify: `pipeline/profiles/mirova_equivalent.yaml` (sección `paths:`, documentación)

- [ ] **Step 1: agregar a `pipeline/profile.py` (después de la línea de ENABLE_TEST1_LOCAL_BG_NTI)**

```python
# S106 — ancla espacial honesta (design 2026-06-11). Solo POSICIÓN del record
# (final_hotspot_*), nunca magnitud/detección. OFF = comportamiento legacy.
ENABLE_HONEST_ANCHOR: bool = bool(_p.get("enable_honest_anchor", False))
# Destino de los records Test1-dominantes: "vent" (cráter, semántica integral)
# o "nti_peak" (píxel de NTI máximo del ROI — conserva fuente real offset).
HONEST_ANCHOR_TEST1_MODE: str = str(_p.get("honest_anchor_test1_mode", "vent"))
```

- [ ] **Step 2: documentar en `mirova_equivalent.yaml` sección `paths:` (con Edit, NO rewrite — A-regla yaml)**

```yaml
  # S106 ancla espacial honesta (design 2026-06-11): posición del final_hotspot
  # desde el cluster contextual / vent / NTI-peak. NO toca deteccion ni magnitud.
  # OFF hasta validar A/B (brazos _honest_anchor_a / _honest_anchor_b).
  enable_honest_anchor: false
  honest_anchor_test1_mode: vent
```

- [ ] **Step 3: verificar import**

Run: `python -c "from pipeline.profile import ENABLE_HONEST_ANCHOR, HONEST_ANCHOR_TEST1_MODE; print(ENABLE_HONEST_ANCHOR, HONEST_ANCHOR_TEST1_MODE)"`
Expected: `False vent`

- [ ] **Step 4: commit**

```bash
git add pipeline/profile.py pipeline/profiles/mirova_equivalent.yaml
git commit -m "feat(s106): flags enable_honest_anchor + honest_anchor_test1_mode (OFF default)"
```

---

### Task 3: Integración en `process_viirs.py` (3 inserciones, A49)

**Files:**
- Modify: `pipeline/process_viirs.py`

- [ ] **Step 1: import del helper + flags** (en el bloque de imports de `pipeline.profile`,
agregar `ENABLE_HONEST_ANCHOR,` y `HONEST_ANCHOR_TEST1_MODE,` en orden alfabético; y debajo
del bloque de imports de pipeline existentes: `from pipeline.anchor import resolve_honest_anchor`)

- [ ] **Step 2: capturar el cluster contextual** — inmediatamente DESPUÉS del bloque
`primary_cluster = apply_single_pixel_mode(...)` que cierra en la línea ~1239 (el del
cluster de `hot_mask_2d`), al mismo nivel de indentación que `primary_cluster = {`:

```python
                    # S106 ancla honesta — snapshot del cluster CONTEXTUAL.
                    # Con first-pass ON, hot_mask_2d = Tests 2∧3 (+second pass)
                    # SIN pixeles Test1 → este cluster es la posición MIROVA-real.
                    # El recompute S31+ (src=test1) pisa primary_cluster más
                    # abajo; preservamos la copia para la cascada del ancla.
                    if ENABLE_HONEST_ANCHOR and primary_cluster is not None:
                        ctx_cluster_anchor = dict(primary_cluster)
```

e inicializar `ctx_cluster_anchor = None` junto a `primary_cluster = None` (línea ~630):

```python
    ctx_cluster_anchor = None  # S106 ancla honesta (snapshot cluster contextual)
```

- [ ] **Step 3: bloque override** — DESPUÉS del bloque Eq.16 (cierra ~línea 1640,
`vrp_mir_mw = _ll["vrp_mw"]`) y ANTES de `record = {` (~1642), nivel de indentación
de función (4 espacios). Verificar con `git diff` que la línea `vrp_mir_mw = _ll[...]`
y la línea `record = {` quedan intactas (A49):

```python
    # S106 — ancla espacial honesta (design 2026-06-11 §3.1). SOLO posición:
    # todos los bloques de magnitud de arriba ya corrieron con la semántica
    # legacy (final_hotspot_source interno). Acá se pisa la POSICIÓN del
    # record con la cascada honesta y se recalcula distance_class.
    if ENABLE_HONEST_ANCHOR:
        _ha_nti_peak = None
        if (HONEST_ANCHOR_TEST1_MODE == "nti_peak" and nti is not None
                and vent_dist_per_pixel is not None):
            _roi3 = (vent_dist_per_pixel <= TEST1_ROI_KM) & ~np.isnan(nti)
            if bool(_roi3.any()):
                _pk_flat = np.nanargmax(np.where(_roi3, nti, -np.inf))
                _pk_r, _pk_c = np.unravel_index(int(_pk_flat), nti.shape)
                _ha_nti_peak = {
                    "lat": round(float(lat[_pk_r, _pk_c]), 5),
                    "lon": round(float(lon[_pk_r, _pk_c]), 5),
                    "dist_km": round(float(vent_dist_per_pixel[_pk_r, _pk_c]), 3),
                }
        _ha_vent_hs = None
        if vent_hotspot_lat is not None and vent_hotspot_lon is not None:
            _ha_vent_hs = {"lat": vent_hotspot_lat, "lon": vent_hotspot_lon,
                           "dist_km": vent_hotspot_dist_km}
        _ha_loose = None
        if hotspot_lat is not None and hotspot_lon is not None:
            _ha_loose = {"lat": hotspot_lat, "lon": hotspot_lon,
                         "dist_km": hotspot_dist_km}
        (final_hotspot_lat, final_hotspot_lon, final_hotspot_dist_km,
         final_hotspot_source) = resolve_honest_anchor(
            ctx_cluster=ctx_cluster_anchor,
            test1_triggered=bool(test1_triggered),
            test1_summit_hit=bool(test1_summit_hit),
            vent_lat=vent_lat, vent_lon=vent_lon,
            nti_peak=_ha_nti_peak,
            vent_hotspot=_ha_vent_hs,
            loose_pixel=_ha_loose,
            inner_radius_km=inner_radius_km,
            mode=HONEST_ANCHOR_TEST1_MODE,
        )
        distance_class = None
        if final_hotspot_dist_km is not None and inner_radius_km is not None:
            distance_class = ("summit" if final_hotspot_dist_km <= inner_radius_km
                              else "far")
```

- [ ] **Step 4: persistir diagnóstico del peak (solo si se computó)** — el record dict ya
serializa `final_hotspot_*` y `distance_class` desde esas variables (verificar). Agregar
al record dict, junto a los campos final_hotspot:

```python
        **({"nti_peak_lat": _ha_nti_peak["lat"],
            "nti_peak_lon": _ha_nti_peak["lon"],
            "nti_peak_dist_km": _ha_nti_peak["dist_km"]}
           if ENABLE_HONEST_ANCHOR and '_ha_nti_peak' in dir() and _ha_nti_peak else {}),
```

(Si el record dict no admite `**` en ese punto, setear las keys después de armar
`record = {...}` con `record["nti_peak_lat"] = ...` bajo el mismo guard — preferir esto último
por legibilidad.)

- [ ] **Step 5: suite completa, 0 regresiones (flag OFF = byte-idéntico)**

Run: `python -m pytest tests/ -x -q -s`
Expected: 705+ passed (695 previos + 10 nuevos), 0 failed

- [ ] **Step 6: commit**

```bash
git add pipeline/process_viirs.py
git commit -m "feat(s106): integrar resolve_honest_anchor en process_viirs (flag OFF, override post-magnitudes)"
```

---

### Task 4: Guard F47 en `store.py` (TDD)

**Files:**
- Modify: `pipeline/store.py:239-257` (rama `cluster_rescues`)
- Test: `tests/test_store_cluster_rescue_f47.py` (agregar caso)

- [ ] **Step 1: test que falla** (agregar al archivo existente, siguiendo su estilo)

```python
def test_rescue_no_pisa_ancla_honesta():
    """S106: si final_hotspot_source es un ancla honesta (ctx_cluster/test1_roi/
    test1_nti_peak), el rescate F47 conserva el rollup vrp pero NO reescribe
    final_hotspot_*/distance_class (el ancla honesta ya es deliberada)."""
    record = {
        "vrp_mw": 0.5, "hotspot_dist_km": 19.6,
        "hotspot_lat": -33.28, "hotspot_lon": -69.66,
        "final_hotspot_lat": -33.389044, "final_hotspot_lon": -69.826374,
        "final_hotspot_dist_km": 0.0, "final_hotspot_source": "test1_roi",
        "distance_class": "summit",
        "primary_cluster": {"centroid_lat": -33.37, "centroid_lon": -69.81,
                             "centroid_dist_km": 2.46, "vrp_mw": 0.4,
                             "n_pixels": 3},
    }
    normalize_record_vrp(record, max_hotspot_dist_km=5.0)
    assert record["final_hotspot_source"] == "test1_roi"
    assert record["final_hotspot_dist_km"] == 0.0
    assert record["distance_class"] == "summit"
    assert record["vrp_mw"] == 0.4  # el rollup F47 sigue ganando (magnitud intacta)
```

(Ajustar el nombre real de la función pública del módulo store que el test file existente
ya usa — usar la misma.)

- [ ] **Step 2: correr y verificar FAIL** (`final_hotspot_source` queda "cluster_rescue")

Run: `python -m pytest tests/test_store_cluster_rescue_f47.py -v -s`

- [ ] **Step 3: guard en store.py** — en la rama `if cluster_rescues:` (línea ~239),
envolver SOLO las reescrituras de posición:

```python
            # F47 rescate — cluster vent-anchored gana al FP single far.
            vrp_eruption = pc_vrp
            record["hotspot_lat"] = pc.get("centroid_lat")
            record["hotspot_lon"] = pc.get("centroid_lon")
            record["hotspot_dist_km"] = pc_cdist
            # S106 ancla honesta: si el upstream ya fijó un ancla deliberada
            # (ctx_cluster / test1_roi / test1_nti_peak), el rescate conserva
            # el rollup de magnitud pero NO pisa la posición/clase honesta.
            _honest_anchor_sources = {"ctx_cluster", "test1_roi", "test1_nti_peak"}
            if record.get("final_hotspot_source") not in _honest_anchor_sources:
                record["final_hotspot_lat"] = pc.get("centroid_lat")
                record["final_hotspot_lon"] = pc.get("centroid_lon")
                record["final_hotspot_dist_km"] = pc_cdist
                record["final_hotspot_source"] = "cluster_rescue"
                record["distance_class"] = "summit"
            record["discarded_reason"] = "single_pixel_far_overridden_by_cluster"
```

(El comentario F47 original de las líneas 249-256 se conserva encima del nuevo `if`.)

- [ ] **Step 4: correr y verificar PASS + suite store completa**

Run: `python -m pytest tests/test_store_cluster_rescue_f47.py tests/test_store.py -v -s`
Expected: todos passed (los casos F47 existentes NO cambian: sus sources son
"eruption"/"test1" legacy, no están en el set honesto)

- [ ] **Step 5: commit**

```bash
git add pipeline/store.py tests/test_store_cluster_rescue_f47.py
git commit -m "feat(s106): guard F47 — rescue conserva rollup pero no pisa anclas honestas"
```

---

### Task 5: Profiles A/B

**Files:**
- Create: `pipeline/profiles/_honest_anchor_a.yaml`
- Create: `pipeline/profiles/_honest_anchor_b.yaml`

- [ ] **Step 1: brazo A (vent)**

```yaml
# VRP-Chile — profile: _honest_anchor_a (S106 A45, A/B ancla espacial honesta)
#
# Brazo A: cascada honesta con Test1-dominante → VENT (semántica integral-ROI).
# Solo POSICIÓN (final_hotspot_*); detección y magnitudes idénticas a baseline.
# Design: docs/superpowers/specs/2026-06-11-ancla-espacial-honesta-design.md §3-4.
extends: mirova_equivalent
profile: _honest_anchor_a
description: >
  A/B S106 ancla honesta, brazo A (test1 -> vent).
paths:
  enable_honest_anchor: true
  honest_anchor_test1_mode: vent
output:
  data_subdir: _honest_anchor_a
```

- [ ] **Step 2: brazo B (nti_peak)** — idéntico salvo:

```yaml
# VRP-Chile — profile: _honest_anchor_b (S106 A45, A/B ancla espacial honesta)
#
# Brazo B: Test1-dominante → píxel de NTI máximo del ROI (conserva posición de
# fuente real offset; discriminador pre-registrado = Lastarria test1-only §3.2).
extends: mirova_equivalent
profile: _honest_anchor_b
description: >
  A/B S106 ancla honesta, brazo B (test1 -> NTI peak del ROI).
paths:
  enable_honest_anchor: true
  honest_anchor_test1_mode: nti_peak
output:
  data_subdir: _honest_anchor_b
```

- [ ] **Step 3: smoke de carga de profile**

Run: `$env:VRP_PROFILE='_honest_anchor_b'; python -c "from pipeline.profile import ENABLE_HONEST_ANCHOR, HONEST_ANCHOR_TEST1_MODE; print(ENABLE_HONEST_ANCHOR, HONEST_ANCHOR_TEST1_MODE)"`
Expected: `True nti_peak`

- [ ] **Step 4: commit**

```bash
git add pipeline/profiles/_honest_anchor_a.yaml pipeline/profiles/_honest_anchor_b.yaml
git commit -m "feat(s106): profiles A/B _honest_anchor_a (vent) / _honest_anchor_b (nti_peak)"
```

---

### Task 6: Workflow A/B

**Files:**
- Create: `.github/workflows/reproc-s106-honest-anchor.yml` (clon de
  `reproc-s105-test1-nti-local-sweep.yml`)

- [ ] **Step 1: crear el yml** (cambios vs template: name, comentario, matrix.profile,
  artifact prefix `s106anchor-`)

```yaml
name: S106 reproc ancla espacial honesta A/B (A45)

# A43 "on" quoted. A/B del ancla honesta (design 2026-06-11): brazo A (test1->vent)
# y brazo B (test1->NTI-peak). Solo POSICION; deteccion/magnitud identicas a baseline
# (criterio duro pre-registrado: trig_t1 y recall IDENTICOS o hay bug). Artifacts,
# NO commitea (A47). Analisis: experiments/_s104_roi_probe/audit_honest_anchor.py.
"on":
  workflow_dispatch:

jobs:
  reproc:
    runs-on: ubuntu-latest
    timeout-minutes: 300
    strategy:
      fail-fast: false
      max-parallel: 6
      matrix:
        profile: [_honest_anchor_a, _honest_anchor_b]
        volcano: [Tupungatito, Villarrica, Llaima, Lascar, Lastarria]
        chunk:
          - { start: "2026-01-29", end: "2026-03-31" }
          - { start: "2026-04-01", end: "2026-06-08" }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install deps
        run: |
          pip install --upgrade pip
          sudo apt-get install -y libhdf4-dev
          pip install pyhdf earthaccess numpy h5py scipy pyyaml
      - name: Reprocess ${{ matrix.profile }} / ${{ matrix.volcano }} / ${{ matrix.chunk.start }}
        env:
          EARTHDATA_TOKEN: ${{ secrets.EARTHDATA_TOKEN }}
          EARTHDATA_USERNAME: ${{ secrets.EARTHDATA_USERNAME }}
          EARTHDATA_PASSWORD: ${{ secrets.EARTHDATA_PASSWORD }}
        timeout-minutes: 290
        run: |
          python scripts/run_pipeline.py \
            --profile ${{ matrix.profile }} \
            --volcano ${{ matrix.volcano }} \
            --start ${{ matrix.chunk.start }} \
            --end ${{ matrix.chunk.end }} \
            --overwrite
      - name: Upload JSON
        uses: actions/upload-artifact@v4
        with:
          name: s106anchor-${{ matrix.profile }}-${{ matrix.volcano }}-${{ matrix.chunk.start }}
          path: data/${{ matrix.profile }}/${{ matrix.volcano }}.json
          if-no-files-found: warn
          retention-days: 7
```

- [ ] **Step 2: validar YAML (Norway problem A43)**

Run: `python -c "import yaml; d=yaml.safe_load(open('.github/workflows/reproc-s106-honest-anchor.yml')); print(list(d.keys()))"`
Expected: `['name', 'on', 'jobs']` (todas strings)

- [ ] **Step 3: commit**

```bash
git add .github/workflows/reproc-s106-honest-anchor.yml
git commit -m "ci(s106): workflow A/B ancla honesta (20 jobs, artifacts)"
```

---

### Task 7: Audit pre-escrito (A16)

**Files:**
- Create: `experiments/_s104_roi_probe/audit_honest_anchor.py`

- [ ] **Step 1: script** (reusa helpers de audit_local_sweep; métricas §4 del design)

```python
"""S106 — Audit del A/B ancla espacial honesta vs predicciones pre-registradas
(design 2026-06-11 §4). Brazos: baseline_mir (disco) / anchor-A / anchor-B.

Criterios DUROS pre-registrados:
  1. trig_t1 y recall IDÉNTICOS al baseline en los 3 brazos (el ancla no toca
     detección — cualquier delta = bug, parar).
  2. offN nevados: Tupungatito ≤300 m, Villarrica ≤200 m (A), dist mediana ≤1.0 km.
  3. Lastarria: mediana de los records ctx CONSERVA el NW real (~2.26 km).
  4. Discriminador A vs B: posiciones de los records test1-source de Lastarria
     en brazo B (¿NTI-peaks caen al NW fumarólico o aleatorios?).

Uso: python audit_honest_anchor.py base:<dir> A:<dir> B:<dir>
"""
import math
import statistics
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from audit_local_sweep import load, v375, hav, VENT, alert_nights, ORDER, NEVADOS


def med(xs):
    return statistics.median(xs) if xs else None


def fmt(x, spec=".0f"):
    return format(x, spec) if x is not None else "—"


def metrics(recs, vol):
    vlat, vlon = VENT[vol]
    vr = v375(recs)
    loc = [r for r in vr if r.get("final_hotspot_lat") is not None]
    offN = [(r["final_hotspot_lat"] - vlat) * 111320 for r in loc]
    dist = [hav(vlat, vlon, r["final_hotspot_lat"], r["final_hotspot_lon"])
            for r in loc]
    t1 = sum(1 for r in vr if r.get("triggered_test1"))
    nights = alert_nights(vol)
    hit = sum(1 for nd in nights
              if any((r.get("datetime_utc") or "")[:10] == nd for r in vr))
    srcs = Counter(r.get("final_hotspot_source") for r in loc)
    return offN, dist, t1, f"{hit}/{len(nights)}", srcs, vr


def main():
    arms = [tuple(a.split(":", 1)) for a in sys.argv[1:]]
    for vol in ORDER:
        print(f"\n=== {vol} ({'NEVADO' if vol in NEVADOS else 'control'}) ===")
        print(f"  {'brazo':<10}{'offN_m':>8}{'dist_km':>8}{'trig_t1':>8}{'recall':>9}  sources")
        for label, d in arms:
            recs = load(Path(__file__).parent / d, vol)
            if recs is None:
                print(f"  {label:<10}(sin data)")
                continue
            offN, dist, t1, recall, srcs, _ = metrics(recs, vol)
            print(f"  {label:<10}{fmt(med(offN)):>8}{fmt(med(dist), '.2f'):>8}"
                  f"{t1:>8}{recall:>9}  {dict(srcs.most_common(4))}")
    # discriminador Lastarria brazo B: posiciones de test1_nti_peak
    for label, d in arms:
        if label != "B":
            continue
        recs = load(Path(__file__).parent / d, "Lastarria")
        if recs is None:
            continue
        vlat, vlon = VENT["Lastarria"]
        pk = [r for r in v375(recs)
              if r.get("final_hotspot_source") == "test1_nti_peak"]
        if not pk:
            print("\nDiscriminador Lastarria-B: 0 records test1_nti_peak")
            continue
        rumbos = Counter()
        for r in pk:
            dlat = (r["final_hotspot_lat"] - vlat) * 111320
            dlon = ((r["final_hotspot_lon"] - vlon) * 111320
                    * math.cos(math.radians(vlat)))
            ang = math.degrees(math.atan2(dlon, dlat)) % 360
            rumbos[["N", "NE", "E", "SE", "S", "SW", "W", "NW"][int((ang + 22.5) // 45) % 8]] += 1
        dists = [hav(vlat, vlon, r["final_hotspot_lat"], r["final_hotspot_lon"])
                 for r in pk]
        print(f"\nDiscriminador Lastarria-B (n={len(pk)}): dist mediana="
              f"{med(dists):.2f} km, rumbos={dict(rumbos.most_common())}")
        print("  → NW dominante = el peak conserva el fumarólico (adoptar B); "
              "aleatorio = gana A por simplicidad.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: smoke con baseline solo**

Run: `python experiments/_s104_roi_probe/audit_honest_anchor.py base:baseline_mir`
Expected: tabla con baseline, sources legacy (test1/eruption/None)

- [ ] **Step 3: commit**

```bash
git add experiments/_s104_roi_probe/audit_honest_anchor.py
git commit -m "test(s106): audit pre-escrito del A/B ancla honesta (criterios §4)"
```

---

### Task 8: PR + merge + dispatch

- [ ] **Step 1: suite completa final**: `python -m pytest tests/ -q -s` → 0 failed
- [ ] **Step 2: push branch + PR** (título: `feat(s106): ancla espacial honesta VIIRS flag-OFF + A/B (A45, tag pre-s106-honest-anchor)`)
- [ ] **Step 3: merge** (A39: mergeStateStatus CLEAN + suite verde; cambio flag-OFF = NRT no afectado)
- [ ] **Step 4: dispatch**: `gh workflow run reproc-s106-honest-anchor.yml --ref main`
- [ ] **Step 5: monitor** de los 20 jobs (patrón Monitor S106)

---

## Self-review (hecho al escribir)

- Spec §3.1 cascada → Task 1/3. §3.2 variantes+discriminador → Task 5/7. §4 criterios →
  Task 7. §5 pasos 1-5 → tag (hecho), TDD (T1/T4), flags (T2), A/B (T5/T6). F47 (riesgo
  §6) → Task 4. MODIS/C1-C2/frontend → Fase 2 explícita (design §4 lo pre-compromete).
- Sin placeholders; código completo en cada step.
- Consistencia de nombres: `resolve_honest_anchor`, `ENABLE_HONEST_ANCHOR`,
  `HONEST_ANCHOR_TEST1_MODE`, sources `ctx_cluster|test1_roi|test1_nti_peak|vent|eruption_loose`
  idénticos en T1/T3/T4/T7.
- Nota T3-Step4: preferida la asignación post-dict (`record["nti_peak_lat"] = ...`).
