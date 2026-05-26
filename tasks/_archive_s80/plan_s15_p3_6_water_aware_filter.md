# P3.6 — Filtro water-aware (discriminación lago ambient vs anomalía volcánica)

> **Ejecutar DESPUES de P3.1 aprobado.** Este fix es ortogonal a P3.1/P3.2
> (se aplica al hot_mask final, no a los paths A/B/C/D). No lo compliques
> con iteraciones P3.1 en curso.

**Goal:** distinguir firma térmica de cuerpo de agua ambient (falso positivo
tipo LagunaDelMaule: 262 pixels de lago entero a ΔT=17 K por capacidad
térmica lacustre) de anomalía volcánica real en lago (Villarrica lava lake,
Tupungatito laguna cratérica, erupción submarina hipotética en cualquier
volcán). Sin perder sensibilidad a futuras anomalías reales.

**Architecture:**
- Water mask externa (Natural Earth ne_10m_lakes.shp o MOD44W tile).
- `active_water_bodies` whitelist per-volcán en `volcanoes.yaml` (lagos
  cratéricos conocidos activos: Tupungatito, Copahue El Agrio, Villarrica
  crater lake, Planchón-Peteroa 4 cráteres).
- Nuevo helper `classify_water_body_pixel(lat, lon, bt, nti, t_bg, water_mask,
  volcano_whitelist, delta_t_threshold, nti_threshold)` → devuelve label
  `"land" | "water_ambient" | "water_anomaly"`.
- Aplicado al `hot_mask_2d` final: pixels etiquetados `water_ambient` se
  descartan del cálculo VRP; `water_anomaly` y `land` se preservan.
- Output record gana campo `water_body_classification` per-pixel + contador
  `n_water_ambient_filtered`.

**Referencia bibliográfica:**
- Aveni et al. 2024 (TIRVolcH, `aveni2024tirvolch`): usa gate contextual
  10σ en "water-dominated" scenes. Inspiración.
- Aguilera et al. 2021 (`aguilera2021evolution`): Planchón-Peteroa Cráter 2
  a 43°C sub-pixel durante unrest — documenta que **no poder discriminar
  bien** cuesta falsos negativos reales en lagos cratéricos pequeños.
- Gap literatura: MIROVA y Coppola 2016a NO abordan este problema
  explícitamente. Esta implementación es innovación propia de VRP Chile,
  defendible ante SERNAGEOMIN.

**Tech Stack:** shapely 2.x (polígonos + point-in-polygon eficiente),
geopandas opcional (solo para loader), numpy. Data: Natural Earth
`ne_10m_lakes.shp` (gratis, dominio público) en `data/geo/`.

**Baseline pre-cambio:**
- LagunaDelMaule: 8+ records abril 2026 con VRP 45-120 MW sobre pixels
  dentro del lago. No-volcánico por literatura (unrest 2007+ es sísmico/
  deformacional, no térmico en cráter).
- Todo NRT normal; no depende del estado P3.1.

**Criterios de aceptación final:**
1. LagunaDelMaule: ≥90% de pixels ambient reclasificados como `water_ambient`
   y descartados del cálculo VRP. VRP publicado baja de 100+ MW a <5 MW.
2. Tupungatito: sensibilidad preservada (mismas detecciones que antes, 0
   pixels reclasificados a `water_ambient` por estar en whitelist).
3. Villarrica lava lake si hay actividad: preservado (ΔT y/o NTI pasan
   gates de `water_anomaly`).
4. Tests unitarios verdes. No regresión en los 11 volcanes Tier A.

---

## Task 1: Water mask loader

**Files:**
- Create: `pipeline/water_mask.py`
- Create: `data/geo/README.md` (instrucciones de download del shapefile)
- Test: `tests/test_water_mask.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_water_mask.py
"""Tests del loader de water mask.

Natural Earth ne_10m_lakes.shp debe cargarse como shapely MultiPolygon.
Primera query point-in-polygon: LagunaDelMaule centro debe ser water=True.
Un punto arbitrario en el desierto debe ser water=False.
"""

from pathlib import Path
import pytest
from pipeline.water_mask import (
    load_water_mask,
    is_water_pixel,
)


def test_loader_returns_callable():
    """El loader devuelve un callable point-in-polygon, no None."""
    mask = load_water_mask(Path("data/geo/ne_10m_lakes.shp"))
    assert callable(mask)


def test_laguna_del_maule_center_is_water():
    """Laguna del Maule centroide aproximado -36.05, -70.52 debe ser agua."""
    mask = load_water_mask(Path("data/geo/ne_10m_lakes.shp"))
    assert is_water_pixel(mask, -36.05, -70.52) == True


def test_atacama_desert_is_not_water():
    """Punto en el desierto de Atacama (-24.0, -68.0) debe ser tierra."""
    mask = load_water_mask(Path("data/geo/ne_10m_lakes.shp"))
    assert is_water_pixel(mask, -24.0, -68.0) == False


def test_vectorized_query_on_array():
    """Query sobre array 2D de lat/lon debe devolver array bool del mismo shape."""
    import numpy as np
    mask = load_water_mask(Path("data/geo/ne_10m_lakes.shp"))
    lats = np.array([[-36.05, -24.0], [-33.4, -39.4]])
    lons = np.array([[-70.52, -68.0], [-69.8, -71.9]])
    result = is_water_pixel(mask, lats, lons)
    assert result.shape == lats.shape
    # Posicion [0,0] es LagunaDelMaule (water), [0,1] Atacama (land)
    assert result[0, 0] == True
    assert result[0, 1] == False
```

- [ ] **Step 2: Run test to verify fails**

Run: `python -m pytest tests/test_water_mask.py -v`
Expected: fails with `ModuleNotFoundError`.

- [ ] **Step 3: Write water mask module**

```python
# pipeline/water_mask.py
"""water_mask.py — Point-in-polygon water mask loader.

Carga Natural Earth ne_10m_lakes.shp y devuelve una funcion query
point-in-polygon eficiente. Usado por P3.6 para discriminar pixels
sobre cuerpos de agua (falsos positivos por capacidad termica lacustre)
de pixels volcanicos sobre tierra.

Data source: https://www.naturalearthdata.com/downloads/10m-physical-vectors/
Licencia: public domain.
"""

from pathlib import Path
import numpy as np

try:
    import shapely
    from shapely.geometry import Point, MultiPolygon
    from shapely.prepared import prep
    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False


def load_water_mask(shp_path: Path):
    """Carga ne_10m_lakes.shp y devuelve PreparedGeometry para queries
    rapidas point-in-polygon.

    Usa fiona (via shapely o geopandas) si disponible. Si el archivo no
    existe, raise FileNotFoundError con instruccion de download.
    """
    if not SHAPELY_AVAILABLE:
        raise ImportError("pip install shapely geopandas fiona")
    if not shp_path.exists():
        raise FileNotFoundError(
            f"Water mask shapefile no encontrado: {shp_path}. "
            f"Descargar ne_10m_lakes.shp de naturalearthdata.com -> "
            f"10m Physical -> Lakes + Reservoirs, y colocar en {shp_path.parent}."
        )
    import geopandas as gpd
    gdf = gpd.read_file(shp_path)
    # Unir todos los polygons en uno solo para query rapida
    union = shapely.unary_union(gdf.geometry.values)
    return prep(union)


def is_water_pixel(prepared_mask, lat, lon):
    """Query point-in-polygon. Escalar o array 2D.

    prepared_mask: output de load_water_mask.
    lat, lon: escalar float o ndarray 2D.
    """
    if np.isscalar(lat):
        return prepared_mask.contains(Point(lon, lat))
    lats = np.asarray(lat)
    lons = np.asarray(lon)
    out = np.zeros(lats.shape, dtype=bool)
    for idx in np.ndindex(lats.shape):
        out[idx] = prepared_mask.contains(Point(lons[idx], lats[idx]))
    return out
```

- [ ] **Step 4: Download shapefile**

```bash
mkdir -p data/geo
# Manual: bajar de https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/physical/ne_10m_lakes.zip
# Extraer ne_10m_lakes.shp + .shx + .dbf + .prj en data/geo/
```

Documentar en `data/geo/README.md` (no commitear el .shp — es 10+ MB; `.gitignore` ya excluye).

- [ ] **Step 5: Verify tests pass**

Run: `python -m pytest tests/test_water_mask.py -v`
Expected: 4 passed.

- [ ] **Step 6: Commit**

```bash
git add pipeline/water_mask.py tests/test_water_mask.py data/geo/README.md .gitignore
git commit -m "S15 P3.6 T1: water mask loader con Natural Earth lakes"
```

---

## Task 2: Classification helper con whitelist

**Files:**
- Modify: `pipeline/water_mask.py` (agregar classify function)
- Test: `tests/test_water_classification.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_water_classification.py
"""Tests de classify_water_body_pixel (P3.6).

Testea los 3 resultados posibles segun combinacion de:
- pixel dentro/fuera water_mask
- dentro/fuera volcano whitelist
- ΔT alto/bajo
- NTI alto/bajo
"""
import numpy as np
from pipeline.water_mask import classify_water_body_pixel


def test_pixel_on_land_always_land():
    """Pixel sin water mask -> 'land' independiente de gates."""
    result = classify_water_body_pixel(
        is_water=False, is_in_whitelist=False,
        bt=300.0, t_bg=280.0, nti=-0.5,
        delta_t_threshold=25.0, nti_threshold=-0.70,
    )
    assert result == "land"


def test_water_ambient_rejected():
    """LagunaDelMaule: pixel en agua, no whitelist, BT tibio (ΔT 17K),
    NTI neutro (-0.90). No pasa gate A (ΔT<25) ni B (NTI<-0.70)."""
    result = classify_water_body_pixel(
        is_water=True, is_in_whitelist=False,
        bt=283.0, t_bg=266.0, nti=-0.90,
        delta_t_threshold=25.0, nti_threshold=-0.70,
    )
    assert result == "water_ambient"


def test_water_anomaly_by_delta_t_absolute():
    """Pixel agua sin whitelist pero ΔT enorme (erupción submarina
    hipotetica): pasa gate A, se clasifica water_anomaly."""
    result = classify_water_body_pixel(
        is_water=True, is_in_whitelist=False,
        bt=320.0, t_bg=280.0, nti=-0.85,   # ΔT=40K
        delta_t_threshold=25.0, nti_threshold=-0.70,
    )
    assert result == "water_anomaly"


def test_water_anomaly_by_nti():
    """Pixel agua NTI alto (roca sub-pixel caliente sobre el lago):
    pasa gate B, clasifica water_anomaly."""
    result = classify_water_body_pixel(
        is_water=True, is_in_whitelist=False,
        bt=295.0, t_bg=285.0, nti=-0.60,   # ΔT=10K pero NTI fuerte
        delta_t_threshold=25.0, nti_threshold=-0.70,
    )
    assert result == "water_anomaly"


def test_whitelist_preserves_normal_sensitivity():
    """Tupungatito laguna cratérica en whitelist: no se aprieta el gate.
    Cualquier anomalia pasa normal -> water_anomaly (senal volcanica real)."""
    result = classify_water_body_pixel(
        is_water=True, is_in_whitelist=True,
        bt=285.0, t_bg=280.0, nti=-0.85,   # senal debil, no pasaria gate estricto
        delta_t_threshold=25.0, nti_threshold=-0.70,
    )
    # En whitelist, asumimos anomalia real por default.
    assert result == "water_anomaly"
```

- [ ] **Step 2: Run test - fails**

- [ ] **Step 3: Implement**

Append to `pipeline/water_mask.py`:

```python
def classify_water_body_pixel(
    is_water: bool,
    is_in_whitelist: bool,
    bt: float,
    t_bg: float,
    nti: float,
    delta_t_threshold: float,
    nti_threshold: float,
) -> str:
    """Clasifica pixel en 'land' | 'water_ambient' | 'water_anomaly'.

    Args:
        is_water: pixel cae dentro del water mask externo (Natural Earth).
        is_in_whitelist: pixel cae dentro de un active_water_body del volcan
            (e.g., Tupungatito laguna cratérica).
        bt, t_bg, nti: brightness temperature, background, Normalized Thermal
            Index del pixel.
        delta_t_threshold: umbral absoluto de anomalia (K) para aceptar en
            agua sin whitelist. Default 25 K.
        nti_threshold: umbral NTI para aceptar en agua sin whitelist.
            Default -0.70 (vs -0.80 standard). Valores mayores = mas estricto.

    Returns:
        "land"           = pixel fuera del water mask, sigue flujo normal.
        "water_ambient"  = en agua, sin whitelist, no pasa gates -> FP descartado.
        "water_anomaly"  = en agua, o en whitelist, o pasa gates -> anomalia real.
    """
    if not is_water:
        return "land"
    if is_in_whitelist:
        return "water_anomaly"
    delta_t = bt - t_bg
    if delta_t > delta_t_threshold:
        return "water_anomaly"
    if nti > nti_threshold:
        return "water_anomaly"
    return "water_ambient"
```

- [ ] **Step 4: Tests pass**

- [ ] **Step 5: Commit**

---

## Task 3: Whitelist en volcanoes.yaml

**Files:**
- Modify: `volcanoes.yaml` (agregar `active_water_bodies` a 4 volcanes)

- [ ] **Step 1: Agregar entries a Tupungatito**

```yaml
- name: Tupungatito
  ...
  active_water_bodies:
    # Laguna cratérica principal. Actividad hidrotermal persistente
    # documentada (Aguilera/Reyes-Hardy 2024).
    - name: crater_lake
      lat: -33.4269
      lon: -69.8004
      radius_km: 1.0
```

- [ ] **Step 2: Copahue**

```yaml
- name: Copahue
  ...
  active_water_bodies:
    # Laguna El Agrio. Lago ácido, temperatura elevada, acople con
    # sistema hidrotermal (Laiolo 2017, Aguilera 2021).
    - name: laguna_el_agrio
      lat: -37.8566
      lon: -71.1832
      radius_km: 0.8
```

- [ ] **Step 3: Villarrica**

```yaml
- name: Villarrica
  ...
  active_water_bodies:
    # Lava lake en el cráter central. VRP histórico 10⁵-10⁷ W en OSF.
    - name: lava_lake_crater
      lat: -39.4203
      lon: -71.9340
      radius_km: 0.3
```

- [ ] **Step 4: PlanchonPeteroa**

```yaml
- name: PlanchonPeteroa
  ...
  active_water_bodies:
    # 4 lagos cratéricos documentados (Aguilera 2021 Frontiers).
    # Cráter 1 (viejo Planchón, MIROVA-center).
    - name: crater_1_planchon
      lat: -35.2232
      lon: -70.5695
      radius_km: 0.5
    # Cráter 2 (Peteroa, SW) — sub-pixel durante unrest 2011.
    - name: crater_2_peteroa
      lat: -35.2411
      lon: -70.5733
      radius_km: 0.5
```

- [ ] **Step 5: Commit**

```bash
git add volcanoes.yaml
git commit -m "S15 P3.6 T3: whitelist active_water_bodies para 4 volcanes"
```

---

## Task 4: Profile keys + integración ortogonal al hot_mask

**Files:**
- Modify: `pipeline/profile.py` (4 constantes nuevas)
- Modify: `pipeline/profiles/mirova_equivalent.yaml`, `experimental.yaml`
- Modify: `pipeline/process_viirs.py`, `process_viirs_mod.py`, `process_modis.py`

- [ ] **Step 1: Profile keys**

`mirova_equivalent.yaml` en `thresholds:`:
```yaml
  # P3.6 S15: water-aware filter.
  water_anomaly_delta_t_k: 25.0
  water_anomaly_nti: -0.70
```

`mirova_equivalent.yaml` en `paths:`:
```yaml
  # P3.6 S15: water-aware filter post-detection.
  # Cuando true, pixels detectados dentro de un water body sin whitelist
  # requieren ΔT > 25K o NTI > -0.70 para ser preservados. Else descartados
  # como "water_ambient".
  enable_water_aware_filter: true
```

`experimental.yaml`: `enable_water_aware_filter: false` (baseline sin filtro).

`profile.py`:
```python
WATER_ANOMALY_DELTA_T_K: float = float(_t.get("water_anomaly_delta_t_k", 25.0))
WATER_ANOMALY_NTI: float = float(_t.get("water_anomaly_nti", -0.70))
ENABLE_WATER_AWARE_FILTER: bool = bool(_p.get("enable_water_aware_filter", False))
```

- [ ] **Step 2: Cargar water mask lazy (singleton)**

Add a `pipeline/water_mask.py`:
```python
_WATER_MASK_CACHE = None

def get_cached_water_mask():
    global _WATER_MASK_CACHE
    if _WATER_MASK_CACHE is None:
        shp = Path(__file__).parent.parent / "data" / "geo" / "ne_10m_lakes.shp"
        try:
            _WATER_MASK_CACHE = load_water_mask(shp)
        except (FileNotFoundError, ImportError):
            _WATER_MASK_CACHE = False   # sentinel: no disponible
    return _WATER_MASK_CACHE
```

- [ ] **Step 3: Integrar en process_viirs.py** (patron similar en los otros 2)

Despues de `hot_mask_2d = bt_path_hot | ... | dnti_ctx_hot`, agregar:

```python
# P3.6 S15: water-aware post-filter.
n_water_ambient_filtered = 0
if ENABLE_WATER_AWARE_FILTER:
    from .water_mask import get_cached_water_mask, is_water_pixel
    from .water_mask import classify_water_body_pixel
    wmask = get_cached_water_mask()
    if wmask is not False:
        # For each hot pixel, check classification
        water_hot = is_water_pixel(wmask, lat, lon) & hot_mask_2d
        if np.any(water_hot):
            active_lakes = volcano_cfg.get("active_water_bodies", [])
            # Vectorized whitelist check: build a mask of pixels within any
            # active body (within its radius_km).
            in_whitelist = np.zeros_like(water_hot)
            for lake in active_lakes:
                dlake = haversine_km(lake["lat"], lake["lon"], lat, lon)
                in_whitelist |= (dlake <= lake["radius_km"])
            # For water pixels NOT in whitelist, apply strict gates
            needs_check = water_hot & ~in_whitelist
            # Compute delta_t_K and check
            delta_t = bt - t_bg_i04
            pass_strict = (delta_t > WATER_ANOMALY_DELTA_T_K) | (nti > WATER_ANOMALY_NTI)
            # Reject: water pixel, not in whitelist, does not pass strict
            reject = needs_check & ~pass_strict
            n_water_ambient_filtered = int(reject.sum())
            hot_mask_2d = hot_mask_2d & ~reject
```

Add al output record: `"n_water_ambient_filtered": n_water_ambient_filtered`.

**Nota**: `volcano_cfg` no está en scope actual del process; pasarlo como
parámetro nuevo a `calculate_vrp` desde `run_pipeline.py`. Ajustar firmas.
Documentar backward-compat: si volcano_cfg=None → skip filtro.

- [ ] **Step 4: Idem process_viirs_mod.py y process_modis.py**

Mismo patron con variables correspondientes.

- [ ] **Step 5: Tests integracion + profile check**

- [ ] **Step 6: Commit**

---

## Task 5: Validación empírica

- [ ] **Step 1: Reprocesar LagunaDelMaule 2026-04 (20 días)**

Requiere agregar LagunaDelMaule a volcanoes.yaml si no está como Tier C.
Luego:
```bash
python scripts/run_pipeline.py --volcano LagunaDelMaule --start 2026-04-01 --end 2026-04-22 --overwrite
```

Expected:
- Antes: 8+ records con VRP 45-120 MW.
- Despues: 0-2 records con VRP residual <5 MW (o 0), `n_water_ambient_filtered`
  alto en cada granule.

- [ ] **Step 2: Reprocesar Tupungatito mismo rango**

Expected: sin regresion. Mismas detecciones que antes. 0 pixels
reclasificados a `water_ambient` (todo pasa via whitelist).

- [ ] **Step 3: Reprocesar Villarrica**

Expected: si hay actividad lava lake, preservada como `water_anomaly`.

- [ ] **Step 4: Delta report + commit**

```bash
python experiments/27_crossmatch_vs_consolidado.py \
    --out experiments/27_crossmatch_post_p36.json
python experiments/34_p36_delta_report.py    # escribir
```

---

## Riesgos conocidos

1. **Resolución Natural Earth**: ne_10m es 1:10M, con simplificación. Lagos
   chicos <1 km² pueden no estar o estar mal delineados. Lagos cratéricos
   (Tupungatito, Villarrica) probablemente ausentes — por eso necesitamos
   whitelist explicita (no fiarse solo del shapefile).

2. **Lagos que secan estacionalmente**: Laguna Leila Norte, ephemeral
   salares. Si el mask dice "water" pero en la imagen es sal seca, el
   filtro anularía detecciones reales sobre salar caliente. Probabilidad
   baja para Chile; monitorear casos con telemetría.

3. **MOD44W alternativa**: más preciso satelitalmente (500 m), podría
   considerarse en futuras iteraciones. Complejidad: actualizado por
   granule en vez de estático.

4. **Performance**: shapely prepared geometry queries ~1 μs per pixel.
   Para un ROI VIIRS 375m de 25 km radio = ~22000 pixels → 22 ms per
   granule. Negligible.

5. **Falso negativo catastrófico**: si hay erupción LagunaDelMaule con
   gate A ΔT > 25K pero agua "amortigua" la señal a 20K → water_ambient
   descartaría. Mitigación: monitorear persistencia temporal; 3 noches
   consecutivas con "water_ambient" anómalamente caliente (aunque no
   supere gate A) es trigger de inspección manual. Fuera del scope P3.6,
   agregable en S16+.

---

## Referencias

- Natural Earth Lakes: https://www.naturalearthdata.com/downloads/10m-physical-vectors/
- `aveni2024tirvolch` en vault — contextual 10σ water-dominated.
- `aguilera2021evolution` — Peteroa 4 lagos cratéricos, caveat sub-pixel.
- `laiolo2017evidences` — Copahue El Agrio desacoplado lago/fumarolas.
- MOD44W documentation: https://lpdaac.usgs.gov/products/mod44wv006/
