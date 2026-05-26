# Paridad MIROVA — Plan de implementación sesión 10

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que el pipeline VRP Chile iguale las detecciones de MIROVA en los tres sensores (VIIRS375, VIIRS750, MODIS) para los 8 volcanes Tier A+B, medido contra la base consolidada + OCR como referencia complementaria.

**Architecture:** Tres ejes de trabajo en serie: (1) mejorar la auditoría para que los FPs y FNs se clasifiquen honestamente, (2) portar la lógica NTI dual-PATH a VIIRS750 que hoy solo tiene detección por temperatura, (3) diagnosticar y resolver los FPs del vent_path con evidencia, no con suposiciones. Todo corre contra el perfil `mirova_equivalent`. Cero cambios experimentales.

**Tech Stack:** Python 3.11, numpy, h5py, pyyaml. pyhdf solo en GitHub Actions (Linux). Tests locales con fixtures JSON.

**Regla fundamental (Nicolás, sesión 10):**
- VIIRS375 y VIIRS750: **recall completo** — capturar todo lo que MIROVA publica, incluso "Muy Bajo"
- MODIS: también match con MIROVA, pero MODIS físicamente no ve anomalías pequeñas (pixel 1 km), así que MIROVA-MODIS ya solo contiene eventos significativos
- La meta NO es superar a MIROVA, es **igualarla**. La física del sensor se encarga de las diferencias.

---

## Mapa de archivos

| Archivo | Rol | Qué cambia |
|---|---|---|
| `experiments/11_strict_audit.py` | Auditoría vs MIROVA | Task 1: reclasificación de FPs + OCR como ref secundaria |
| `experiments/12_rf1_vent_fp_diagnostic.py` | **NUEVO** — diagnóstico de FPs vent_path | Task 3: instrumento para medir si los FP son reales o ruido |
| `pipeline/process_viirs_mod.py` | Procesador VIIRS 750m | Task 2: agregar NTI dual-PATH + profileizar vent threshold |
| `pipeline/profiles/mirova_equivalent.yaml` | Perfil operacional | Task 2: agregar M15 band config si es necesario |
| `scripts/rebuild_mirova_from_consolidado.py` | Regenera refs desde CSV | Task 1: incorporar clasificación "Medio" del OCR |
| `data/mirova/*.json` | Refs MIROVA por volcán | Task 1: regenerados con OCR complementario |

---

## Task 1: Mejorar la auditoría — FP reclassification + OCR

**Problema que resuelve:** Hoy la auditoría cuenta como "falso positivo" toda detección nuestra que no está en la base MIROVA depurada. Pero esa base tiene gaps (sobre todo VIIRS), y muchas de esas "FPs" son detecciones reales que el scraper no capturó. Esto infla el error aparente y puede llevarnos a "arreglar" cosas que no están rotas.

**Files:**
- Modify: `experiments/11_strict_audit.py`
- Create: `experiments/audit_s10/` (nuevo directorio para snapshots post-reclasificación)
- Read: `10.04.2026 registro_vrp_ocr.csv` (referencia OCR complementaria)
- Read: `10.04.2026 registro_vrp_consolidado.csv` (referencia principal actualizada)

### Sub-task 1.1: Regenerar refs MIROVA con la consolidada actualizada

La consolidada actual (10 abril) tiene más datos que la que usamos en sesión 9.

- [ ] **Step 1: Copiar CSVs actualizados al directorio estándar**

```bash
# Desde la raíz del proyecto
cp "10.04.2026 registro_vrp_consolidado.csv" data/registro_vrp_consolidado.csv
```

- [ ] **Step 2: Regenerar los 11 refs MIROVA**

```bash
python scripts/rebuild_mirova_from_consolidado.py
```

Verificar: debe imprimir conteos por volcán. Comparar con los conteos S9 (380 total Tier A+B) — debería ser igual o mayor.

- [ ] **Step 3: Commit**

```bash
git add data/mirova/*.json data/registro_vrp_consolidado.csv
git commit -m "data: update MIROVA refs from 10-Apr-2026 consolidado"
```

### Sub-task 1.2: Agregar carga de OCR como referencia complementaria

- [ ] **Step 4: Agregar función `load_ocr_ref()` al audit script**

En `experiments/11_strict_audit.py`, agregar después de `load_ref()`:

```python
import csv

OCR_CSV = REPO / "10.04.2026 registro_vrp_ocr.csv"

# Mapeo de sensor OCR a familia (igual que MIROVA)
OCR_SENSOR_TO_FAMILY = {
    "VIIRS375": "VIIRS375",
    "VIIRS": "VIIRS",      # VIIRS en OCR = VIIRS750
    "MODIS": "MODIS",
}

def load_ocr_ref(volcano: str) -> list[dict]:
    """Carga records OCR para un volcán como referencia complementaria.
    
    Los records OCR tienen menor confianza que la consolidada:
    - No tienen distancia_km confiable (siempre 0.0 en la columna)
    - Los VRP pueden tener error de lectura (OCR de imagen)
    - Solo se usan para reclasificar FPs, nunca para agregar FNs
    
    Filtra: solo ALERTA_TERMICA_OCR con Clasificacion in {Muy Bajo, Bajo, Medio}
    """
    if not OCR_CSV.exists():
        return []
    
    # Normalizar nombre de volcán para match con CSV
    # En el CSV: "Puyehue-Cordon Caulle", en nuestro sistema: "PuyehueCordonCaulle"
    name_map = {
        "PuyehueCordonCaulle": "Puyehue-Cordon Caulle",
        "PlanchonPeteroa": "PlanchonPeteroa",
        "NevadosDeChillan": "Nevados de Chillan",
    }
    csv_name = name_map.get(volcano, volcano)
    
    records = []
    with open(OCR_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["Volcan"].strip() != csv_name:
                continue
            tipo = row.get("Tipo_Registro", "").strip()
            if tipo != "ALERTA_TERMICA_OCR":
                continue
            clasif = row.get("Clasificacion Mirova", "").strip()
            if clasif not in {"Muy Bajo", "Bajo", "Medio"}:
                continue
            vrp = float(row.get("VRP_MW", 0.0) or 0.0)
            if vrp <= 0:
                continue
            sensor = row.get("Sensor", "").strip()
            family = OCR_SENSOR_TO_FAMILY.get(sensor)
            if family is None:
                continue
            try:
                dt = parse_dt(row["Fecha_Satelite_UTC"])
            except Exception:
                continue
            records.append({
                "dt": dt,
                "family": family,
                "vrp": vrp,
                "raw_sensor": sensor,
                "clasificacion": clasif,
                "source": "ocr",
            })
    return records
```

- [ ] **Step 5: Modificar clasificación de FPs en `pair_records()` o post-pairing**

Después del pairing actual (que produce `tp_pairs`, `fn_records`, `fp_records`), agregar un segundo paso que intenta matchear los FPs contra el OCR:

```python
def reclassify_fps_with_ocr(fp_records: list[dict], ocr_ref: list[dict]) -> tuple[list[dict], list[dict]]:
    """Intenta matchear FPs contra records OCR.
    
    Un FP que matchea con un record OCR (mismo sensor_family, ±30 min)
    se reclasifica como 'TP-probable-OCR'. No es tan fuerte como un TP
    contra consolidada, pero es evidencia de que no es falso positivo.
    
    Returns: (fp_reclassified_as_tp_ocr, fp_remaining)
    """
    if not ocr_ref:
        return [], fp_records
    
    ocr_by_family = defaultdict(list)
    for r in ocr_ref:
        ocr_by_family[r["family"]].append(dict(r, _used=False))
    
    tp_ocr = []
    fp_remaining = []
    
    for fp in fp_records:
        family = fp["family"]
        tol = timedelta(minutes=30)  # uniforme para OCR
        candidates = ocr_by_family.get(family, [])
        
        matched = False
        for ocr_rec in candidates:
            if ocr_rec["_used"]:
                continue
            if abs(fp["dt"] - ocr_rec["dt"]) <= tol:
                ocr_rec["_used"] = True
                tp_ocr.append({**fp, "ocr_match": ocr_rec})
                matched = True
                break
        
        if not matched:
            fp_remaining.append(fp)
    
    return tp_ocr, fp_remaining
```

- [ ] **Step 6: Agregar clasificación espacial de FPs restantes**

```python
def classify_fp_spatial(fp: dict) -> str:
    """Clasifica un FP por su relación espacial con el cráter.
    
    Returns:
        'fp_near'     — tiene anomalía real <3 km del cráter (probable detección real)
        'fp_far'      — tiene anomalía real >5 km (probable artefacto/incendio)
        'fp_ambiguous' — tiene anomalía real 3-5 km (indeterminado)
        'fp_vent_only' — sin anomalía independiente, solo vent_path (ruido vs señal débil)
    """
    n_anom = fp.get("n_anomalous_pixels", 0)
    if n_anom == 0:
        return "fp_vent_only"
    
    dist = fp.get("hotspot_dist_km")
    if dist is None:
        return "fp_vent_only"
    if dist < 3.0:
        return "fp_near"
    if dist > 5.0:
        return "fp_far"
    return "fp_ambiguous"
```

- [ ] **Step 7: Integrar en el flujo principal de `summarize()`**

Modificar la función `summarize()` para que:
1. Cargue OCR con `load_ocr_ref(volcano)`
2. Llame `reclassify_fps_with_ocr()` sobre los FPs
3. Clasifique los FPs restantes con `classify_fp_spatial()`
4. Reporte métricas separadas:
   - `precision_strict` = TP / (TP + ALL_FP) — como antes
   - `precision_adjusted` = (TP + TP_OCR) / (TP + TP_OCR + FP_remaining) — con OCR
   - Desglose de FPs: n_fp_near, n_fp_far, n_fp_vent_only, n_fp_ambiguous, n_tp_ocr
5. Guarde el snapshot en `experiments/audit_s10/`

- [ ] **Step 8: Correr audit actualizado sobre Tier A+B**

```bash
python experiments/11_strict_audit.py --tier A
python experiments/11_strict_audit.py --tier B
```

Guardar output como `experiments/AUDIT_S10_baseline.md` con tabla por volcán × sensor.

- [ ] **Step 9: Commit**

```bash
git add experiments/11_strict_audit.py experiments/audit_s10/ experiments/AUDIT_S10_baseline.md
git commit -m "audit: add FP reclassification (OCR + spatial) for honest metrics"
```

### Acceptance criteria Task 1:
- [ ] Cada FP tiene un `fp_class` en el snapshot JSON
- [ ] Los FPs que matchean OCR están separados como `tp_ocr`
- [ ] Las métricas reportan tanto precision_strict como precision_adjusted
- [ ] El baseline S10 existe con los 8 volcanes desglosados por sensor

---

## Task 2: Portar NTI dual-PATH a VIIRS-M (750 m)

**Problema que resuelve:** `process_viirs_mod.py` es el único procesador que NO tiene detección por NTI (el índice que compara color infrarrojo MIR vs TIR). Solo decide por temperatura cruda. Esto hace que en noches nubladas o con σ_bg alto, los píxeles reales se pierdan porque el threshold de temperatura se infla. MIROVA usa NTI en VIIRS750, así que sin NTI no tenemos paridad.

**Qué hay que hacer en palabras:**
1. Enseñarle a leer la banda TIR (M15, 10.76 µm) además de la MIR (M13, 4.05 µm) que ya lee
2. Calcular el NTI por píxel (la proporción entre MIR y TIR que revela calor volcánico)
3. Agregar la detección dual: un píxel pasa si CUALQUIERA de las dos pruebas dispara (temperatura O color infrarrojo)
4. Agregar el campo `ENABLE_VENT_PATH` desde el perfil en vez de hardcodeado
5. Agregar los campos de diagnóstico `n_bt_path` y `n_nti_path` que ya existen en VIIRS375

**Files:**
- Modify: `pipeline/process_viirs_mod.py`
- Modify: `pipeline/profiles/mirova_equivalent.yaml` (si necesitamos nuevo parámetro)
- Test: correr auditoría post-cambio y comparar con baseline

- [ ] **Step 1: Agregar lectura de banda M15 (TIR) en `read_viirs_mod_l1b()`**

En `pipeline/process_viirs_mod.py`, constantes nuevas al inicio del archivo (después de `M13_LAMBDA`):

```python
M15_INDEX = 14   # M15 is index 14 in VNP02MOD (M01..M16, 0-based)
M15_LAMBDA = 10.763  # µm — TIR band for NTI computation
```

En la función `read_viirs_mod_l1b()`, agregar lectura de M15 después del bloque de M13:

```python
        # M15 TIR band (10.76 µm) for NTI computation
        band_key_tir = "M15"
        if band_key_tir in obs:
            dn15 = obs[band_key_tir][:]
            lut_key_tir = "M15_brightness_temperature_lut"
            if lut_key_tir in obs:
                lut15 = obs[lut_key_tir][:]
                bt15 = lut15[dn15].astype(np.float32)
                flag_mask15 = np.isin(dn15, list(FLAG_DNS))
                bt15[flag_mask15] = np.nan
                bt15[bt15 < 0] = np.nan
            else:
                ds15 = obs[band_key_tir]
                scale15 = float(ds15.attrs.get("scale_factor", 1.0))
                offset15 = float(ds15.attrs.get("add_offset", 0.0))
                rad15 = dn15.astype(np.float32) * scale15 + offset15
                flag_mask15 = np.isin(dn15, list(FLAG_DNS))
                rad15[flag_mask15] = np.nan
                bt15 = C2_PLANCK / (M15_LAMBDA * np.log(C1_PLANCK / (rad15 * M15_LAMBDA ** 5) + 1))
            result["M15"] = bt15
```

- [ ] **Step 2: Agregar imports de NTI y vent profile constants**

```python
from pipeline.profile import (
    ANOMALY_THRESHOLD_K,
    N_SIGMA_MIR,
    BG_INNER_KM,
    BG_OUTER_KM,
    ENABLE_ERUPTION_PATH,
    ENABLE_VENT_PATH,       # NUEVO — antes no se importaba
    VENT_THRESHOLD_K,        # NUEVO — reemplaza el hardcoded 1.0
    NTI_K1_NIGHT,            # NUEVO — para NTI dual-PATH
    NTI_BT_SANITY_K,         # NUEVO — sanity check del NTI path
)
```

- [ ] **Step 3: Agregar cálculo de NTI en `calculate_vrp()`**

Después del cálculo de `t_bg` y `std_bg`, antes del bloque de detección, agregar:

```python
    # --- NTI: Normalized Thermal Index (Coppola 2015) ---
    # NTI = (L_MIR - L_TIR) / (L_MIR + L_TIR) per pixel
    # Un pixel volcánicamente caliente tiene NTI más alto que el fondo
    # porque el calor volcánico aumenta mucho más la radiancia MIR (4 µm)
    # que la TIR (11 µm). Nubes y variabilidad topográfica afectan ambas
    # bandas por igual, así que el NTI las cancela. Por eso MIROVA lo usa
    # como filtro principal.
    nti_bg = float("nan")
    nti_std = float("nan")
    nti_max = float("nan")
    n_nti_anomalous = 0
    nti = np.full_like(bt, np.nan)

    if "M15" in bands:
        bt_tir = bands["M15"]
        L_mir = bt_to_spectral_radiance(bt, M13_LAMBDA)
        L_tir = bt_to_spectral_radiance(bt_tir, M15_LAMBDA)
        valid_both = ~np.isnan(L_mir) & ~np.isnan(L_tir) & ((L_mir + L_tir) > 0)
        nti[valid_both] = (L_mir[valid_both] - L_tir[valid_both]) / (L_mir[valid_both] + L_tir[valid_both])

        # Estadísticas de NTI del fondo (anillo de background)
        bg_nti = nti[bg_mask & ~np.isnan(nti)]
        if len(bg_nti) >= 10:
            nti_bg = float(np.median(bg_nti))
            nti_std = float(np.std(bg_nti))

        # NTI máximo en la ROI (diagnóstico)
        roi_nti = nti[roi_mask & ~np.isnan(nti)]
        if len(roi_nti) > 0:
            nti_max = float(np.max(roi_nti))
            nti_threshold = nti_bg + max(0.005, 3.0 * nti_std) if not np.isnan(nti_bg) else float("inf")
            n_nti_anomalous = int(np.sum(roi_nti > nti_threshold))
```

- [ ] **Step 4: Reemplazar detección single-path BT por dual-PATH (OR)**

Reemplazar el bloque actual de detección (líneas ~180-204 aprox) por:

```python
    # --- Dual-PATH detection (Coppola 2015 / MIROVA Test 1) ---
    # Un pixel es anomalía si CUALQUIERA de las dos pruebas pasa:
    #   A) BT path: la temperatura del pixel supera el fondo + threshold
    #   B) NTI path: el "color infrarrojo" del pixel parece volcánico
    #      Y además tiene un mínimo de exceso de temperatura (sanity check)
    # El OR es crucial: en noches donde las nubes o la topografía inflan
    # el threshold de temperatura (path A falla), el NTI (path B) todavía
    # funciona porque las nubes afectan MIR y TIR por igual.

    # Path A — BT (detección clásica por temperatura)
    # effective_threshold ya incluye el p95+ROI filter
    bt_path_hot = roi_bt_full > effective_threshold
    n_bt_path = int(np.sum(bt_path_hot & ~np.isnan(roi_bt_full)))

    # Path B — NTI (detección por color infrarrojo, Coppola 2015)
    n_nti_path = 0
    if "M15" in bands and not np.isnan(nti_bg):
        nti_path_hot = (
            roi_mask
            & ~np.isnan(nti)
            & ~np.isnan(bt)
            & (nti > NTI_K1_NIGHT)
            & (bt > (t_bg + NTI_BT_SANITY_K))
        )
        n_nti_path = int(np.sum(nti_path_hot))
    else:
        nti_path_hot = np.zeros_like(roi_mask)

    # Unión: cualquiera de las dos pruebas
    hot_mask_2d = bt_path_hot | nti_path_hot
    hot_rows, hot_cols = np.where(hot_mask_2d)
    n_anomalous = len(hot_rows)
```

- [ ] **Step 5: Profileizar el vent_path threshold**

Reemplazar el bloque actual del vent_path (líneas ~241-258) por:

```python
    # --- Vent-scale detection ---
    vrp_vent_mw = 0.0
    n_vent_pixels = 0
    if (ENABLE_VENT_PATH
            and vent_lat is not None and vent_lon is not None
            and not np.isnan(t_bg)):
        vent_dist = haversine_km(vent_lat, vent_lon, lat, lon)
        vent_roi_mask = vent_dist <= vent_radius_km
        if np.any(vent_roi_mask):
            vent_bt = np.where(vent_roi_mask & ~np.isnan(bt), bt, np.nan)
            if np.any(~np.isnan(vent_bt)):
                flat_idx = np.nanargmax(vent_bt)
                r_vent, c_vent = np.unravel_index(flat_idx, vent_bt.shape)
                t_max_vent = float(vent_bt[r_vent, c_vent])
                if t_max_vent > (t_bg + VENT_THRESHOLD_K):
                    L_vent = bt_to_spectral_radiance(np.float64(t_max_vent), M13_LAMBDA)
                    L_bg_vent = bt_to_spectral_radiance(np.float64(t_bg), M13_LAMBDA)
                    vent_area = float(pixel_areas[r_vent, c_vent])
                    vrp_vent_mw = float(vent_area * WOOSTER_COEFF * (L_vent - L_bg_vent)) / 1e6
                    n_vent_pixels = 1
```

- [ ] **Step 6: Agregar campos NTI al dict de retorno**

```python
    return {
        "vrp_mw": round(vrp_mw, 3),
        "vrp_vent_mw": round(vrp_vent_mw, 3),
        "n_anomalous_pixels": n_anomalous,
        "n_bt_path": n_bt_path,           # NUEVO
        "n_nti_path": n_nti_path,          # NUEVO
        "n_vent_pixels": n_vent_pixels,
        "hotspot_lat": hotspot_lat,
        "hotspot_lon": hotspot_lon,
        "hotspot_dist_km": hotspot_dist_km,
        "anomaly_pixels": anomaly_pixels,
        "t_bg_k": round(t_bg, 2),
        "t_max_k": round(t_max, 2) if not np.isnan(t_max) else None,
        "nti_bg": round(nti_bg, 6) if not np.isnan(nti_bg) else None,    # NUEVO
        "nti_max": round(nti_max, 6) if not np.isnan(nti_max) else None,  # NUEVO
        "sensor": sensor,
        "granule": name,
        "datetime_utc": _parse_datetime(name),
    }
```

- [ ] **Step 7: Reprocesar los 8 volcanes Tier A+B con --overwrite**

```bash
# En GitHub Actions (workflow_dispatch), o localmente si h5py funciona:
python scripts/run_pipeline.py --profile mirova_equivalent --overwrite
```

- [ ] **Step 8: Re-auditar y comparar con baseline S10**

```bash
python experiments/11_strict_audit.py --tier A
python experiments/11_strict_audit.py --tier B
```

Comparar VIIRS750 recall antes/después. Esperamos:
- Recall VIIRS750 suba (NTI path rescata detecciones en noches nubladas)
- Precision VIIRS750 no caiga significativamente
- VIIRS375 y MODIS no cambien (este commit solo toca process_viirs_mod.py)

- [ ] **Step 9: Commit**

```bash
git add pipeline/process_viirs_mod.py
git commit -m "feat: add NTI dual-PATH to VIIRS-M (750m) for MIROVA parity"
```

### Acceptance criteria Task 2:
- [ ] `process_viirs_mod.py` lee M15 (TIR) y computa NTI
- [ ] Detección usa dual-PATH OR (BT | NTI), igual que VIIRS375 y MODIS
- [ ] Vent threshold viene del perfil (`VENT_THRESHOLD_K`), no hardcodeado
- [ ] Records de salida incluyen `n_bt_path`, `n_nti_path`, `nti_bg`, `nti_max`
- [ ] Recall VIIRS750 sube sin regresión en otros sensores

---

## Task 3: Diagnóstico de FPs del vent_path (RF1)

**Problema que resuelve:** El vent_path con threshold `t_bg + 1K` produce muchas detecciones en todos los volcanes. Algunas son actividad volcánica real (Chaiten en su domo, PlanchonPeteroa en sus cráteres), otras son variabilidad térmica natural del terreno. Sin un volcán verdaderamente "inactivo" en Tier A+B como control, no podemos separar las dos poblaciones estadísticamente con los datos actuales.

**Estrategia:** Usar Tier C (Copahue, Llaima, NevadosDeChillan — volcanes sin anomalías confirmadas) como grupo control. Si los Tier C producen vent-only detections a la misma tasa y magnitud que los Tier A+B activos, eso es la firma del ruido de fondo. Si producen significativamente menos, las detecciones en volcanes activos son señal real.

**Files:**
- Create: `experiments/12_rf1_vent_fp_diagnostic.py`
- Read: `data/mirova_equivalent/*.json` (Tier A+B+C)
- Output: `experiments/RF1_diagnostic_s10.md`

- [ ] **Step 1: Escribir el script diagnóstico**

```python
"""
12_rf1_vent_fp_diagnostic.py — Diagnóstico cuantitativo de detecciones vent_path.

Compara la tasa y magnitud de detecciones vent-only entre volcanes con
actividad confirmada (Tier A+B) y volcanes sin actividad (Tier C = control).

Si el control produce la misma tasa → el threshold 1K está debajo del ruido
Si el control produce mucho menos → las detecciones en volcanes activos son reales

Usage:
    python experiments/12_rf1_vent_fp_diagnostic.py
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
from statistics import median, mean
from collections import defaultdict

REPO = Path(__file__).parent.parent
DATA_DIR = REPO / "data" / "mirova_equivalent"

# Volcanes con actividad térmica confirmada (Tier A+B)
ACTIVE = {
    "Lascar": "fumarólica crateral persistente",
    "PuyehueCordonCaulle": "fisura 2011, anomalía persistente",
    "Lastarria": "campo fumarólico extenso",
    "Isluga": "fumarolas",
    "Tupungatito": "fumarolas summit",
    "PlanchonPeteroa": "4 cráteres activos",
    "Chaiten": "domo activo",
    "Villarrica": "lago de lava",
}

# Volcanes sin anomalía confirmada (control)
CONTROL = {
    "Copahue": "sin actividad térmica actual",
    "Llaima": "sin actividad térmica actual",
    "NevadosDeChillan": "posiblemente 1-2 detecciones, no confirmado",
}


def analyze_volcano(name: str) -> dict:
    """Extrae estadísticas de detecciones vent-only para un volcán."""
    path = DATA_DIR / f"{name}.json"
    if not path.exists():
        return {"name": name, "error": "no data file"}
    
    doc = json.loads(path.read_text(encoding="utf-8"))
    records = doc.get("records", [])
    
    total = len(records)
    detections = [r for r in records if (r.get("vrp_mw", 0) or 0) > 0]
    vent_only = [r for r in detections 
                 if r.get("n_vent_pixels", 0) > 0 
                 and r.get("n_anomalous_pixels", 0) == 0]
    eruption_detections = [r for r in detections 
                           if r.get("n_anomalous_pixels", 0) > 0]
    
    # Desglose por sensor
    by_sensor = defaultdict(lambda: {"total": 0, "vent_only": 0, "eruption": 0, "vrps": []})
    for r in records:
        sensor = r.get("sensor", "unknown")
        by_sensor[sensor]["total"] += 1
    for r in vent_only:
        sensor = r.get("sensor", "unknown")
        by_sensor[sensor]["vent_only"] += 1
        by_sensor[sensor]["vrps"].append(r.get("vrp_mw", 0))
    for r in eruption_detections:
        sensor = r.get("sensor", "unknown")
        by_sensor[sensor]["eruption"] += 1
    
    return {
        "name": name,
        "total_records": total,
        "total_detections": len(detections),
        "vent_only": len(vent_only),
        "eruption_detections": len(eruption_detections),
        "vent_only_rate": len(vent_only) / total if total > 0 else 0,
        "vent_only_vrp_median": median([r.get("vrp_mw", 0) for r in vent_only]) if vent_only else 0,
        "vent_only_vrp_max": max([r.get("vrp_mw", 0) for r in vent_only]) if vent_only else 0,
        "by_sensor": dict(by_sensor),
    }


def main():
    print("=" * 70)
    print("RF1 VENT-PATH DIAGNOSTIC — Active vs Control")
    print("=" * 70)
    
    print("\n## ACTIVE VOLCANOES (confirmed thermal anomaly)")
    active_rates = []
    for name, desc in ACTIVE.items():
        stats = analyze_volcano(name)
        if "error" in stats:
            print(f"  {name}: {stats['error']}")
            continue
        rate = stats["vent_only_rate"]
        active_rates.append(rate)
        print(f"  {name} ({desc}):")
        print(f"    Total passes: {stats['total_records']}")
        print(f"    Vent-only detections: {stats['vent_only']} ({rate:.1%} of passes)")
        print(f"    Eruption-path detections: {stats['eruption_detections']}")
        print(f"    Vent-only VRP median: {stats['vent_only_vrp_median']:.3f} MW")
        print(f"    Vent-only VRP max: {stats['vent_only_vrp_max']:.3f} MW")
        print()
    
    print("\n## CONTROL VOLCANOES (no confirmed thermal anomaly)")
    control_rates = []
    for name, desc in CONTROL.items():
        stats = analyze_volcano(name)
        if "error" in stats:
            print(f"  {name}: {stats['error']}")
            continue
        rate = stats["vent_only_rate"]
        control_rates.append(rate)
        print(f"  {name} ({desc}):")
        print(f"    Total passes: {stats['total_records']}")
        print(f"    Vent-only detections: {stats['vent_only']} ({rate:.1%} of passes)")
        print(f"    Eruption-path detections: {stats['eruption_detections']}")
        print(f"    Vent-only VRP median: {stats['vent_only_vrp_median']:.3f} MW")
        print(f"    Vent-only VRP max: {stats['vent_only_vrp_max']:.3f} MW")
        print()
    
    print("\n## COMPARISON")
    if active_rates and control_rates:
        active_median = median(active_rates)
        control_median = median(control_rates)
        print(f"  Active vent-only rate (median):  {active_median:.1%}")
        print(f"  Control vent-only rate (median): {control_median:.1%}")
        if control_median > 0:
            ratio = active_median / control_median
            print(f"  Ratio active/control: {ratio:.2f}x")
        print()
        if control_median > active_median * 0.5:
            print("  CONCLUSION: Control produces comparable vent-only rates.")
            print("  The vent_path threshold is likely below natural variability.")
            print("  Most vent-only detections are NOISE, not volcanic signal.")
        else:
            print("  CONCLUSION: Active volcanoes produce significantly more vent-only")
            print("  detections than control. Many are likely REAL volcanic signals.")
            print("  Raising the threshold would kill real detections.")
    else:
        print("  Insufficient data for comparison.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Correr el diagnóstico**

```bash
python experiments/12_rf1_vent_fp_diagnostic.py > experiments/RF1_diagnostic_s10.md
```

- [ ] **Step 3: Interpretar resultado y decidir**

Según el resultado, una de tres cosas:

**A) Control ≈ Active**: el threshold 1K es ruido en todos. Fix = subir threshold o agregar filtro NTI al vent_path (ya que el eruption path dual ya existe).

**B) Control << Active**: las detecciones vent-only en volcanes activos son reales. NO subir threshold. El "FP" es un gap de la referencia, no un error del pipeline. Documentar y aceptar como known limitation de la referencia.

**C) Resultados mixtos por sensor**: MODIS (1km) puede ser ruido puro pero VIIRS (375/750m) puede ser señal real. Fix = tratar distinto por sensor.

- [ ] **Step 4: Documentar decisión en ROOT_CAUSE_S9.md (sección RF1)**

Actualizar la sección RF1 🔴 con los hallazgos y la decisión.

- [ ] **Step 5: Commit**

```bash
git add experiments/12_rf1_vent_fp_diagnostic.py experiments/RF1_diagnostic_s10.md
git commit -m "diag: RF1 vent-path active vs control comparison"
```

### Acceptance criteria Task 3:
- [ ] El diagnóstico produce un resultado cuantitativo claro (active vs control)
- [ ] La decisión (subir threshold / no subir / por sensor) está documentada con evidencia
- [ ] Si se decide subir threshold, el fix va en Task 4. Si no, se documenta y se cierra RF1.

---

## Task 4: Fix condicional (solo si Task 3 lo justifica)

**Depende de:** el resultado de Task 3.

### Escenario A — si hay que subir el threshold del vent_path:

- [ ] **Step 1: Hacer sweep de thresholds antes de elegir**

```python
# Agregar a 12_rf1_vent_fp_diagnostic.py o crear 13_vent_threshold_sweep.py
# Probar 1K, 1.5K, 2K, 2.5K, 3K contra los 8 volcanes
# Para cada threshold, contar cuántas detecciones sobreviven vs cuántas mueren
# y verificar cuántos TPs de la consolidada se perderían
```

- [ ] **Step 2: Implementar el threshold elegido en el YAML**

```yaml
# pipeline/profiles/mirova_equivalent.yaml
thresholds:
  vent_threshold_k: <valor elegido>
```

- [ ] **Step 3: Reprocesar y re-auditar**
- [ ] **Step 4: Comparar con baseline S10, verificar no-regresión**
- [ ] **Step 5: Commit**

### Escenario B — si el vent_path es señal real:

- [ ] **Step 1: Documentar que RF1 está cerrado como "not a bug"**
- [ ] **Step 2: Ajustar las métricas de la auditoría para reflejar que los vent-only en volcanes activos son "TP-indeterminate", no FP**
- [ ] **Step 3: Commit documentación**

---

## Task 5: Re-auditoría final y reporte

**Después de:** Tasks 1-4 completas.

- [ ] **Step 1: Correr auditoría final con todos los fixes**

```bash
python experiments/11_strict_audit.py --all
```

- [ ] **Step 2: Producir tabla resumen sensor × volcán**

Formato esperado en `experiments/AUDIT_S10_final.md`:

```markdown
| Volcán | Sensor | TP | TP_OCR | FP_near | FP_vent_only | FP_far | FN | Precision_adj | Recall | Ratio_median |
```

- [ ] **Step 3: Comparar con AUDIT_S10_baseline (pre-fixes) y AUDIT_S9 (pre-todo)**

Mostrar delta de cada métrica.

- [ ] **Step 4: Listar FNs restantes con explicación**

Cada FN que quede debe tener una explicación:
- "señal 0.1 MW subpixel en Villarrica — debajo del floor físico del sensor" (aceptado)
- "gap de fecha X — el pipeline no corrió ese día" (fetch gap, no bug)
- "threshold demasiado alto en esta noche específica" (bug residual → RF para siguiente sesión)

- [ ] **Step 5: Commit reporte final**

```bash
git add experiments/AUDIT_S10_final.md experiments/audit_s10/
git commit -m "audit: S10 final report — MIROVA parity assessment per sensor"
```

### Acceptance criteria Task 5:
- [ ] Tabla 8 volcanes × 3 sensores con todas las métricas
- [ ] Cada FN tiene explicación
- [ ] Comparación explícita con baseline anterior
- [ ] Declaración honesta de qué queda pendiente

---

## Task 6: Memoria y docs cleanup

- [ ] **Step 1: Actualizar `memory/project_vrp_chile.md`** con números S10
- [ ] **Step 2: Actualizar `tasks/lessons.md`** con learnings de Tasks 1-5
- [ ] **Step 3: Actualizar `ROOT_CAUSE_S9.md`** cerrando RF1, RF2, RF5 según corresponda
- [ ] **Step 4: Invocar skill `revise-claude-md`** para consolidar reglas nuevas

---

## Notas técnicas para el ejecutor

1. **pyhdf roto en Windows**: los cambios en `process_modis.py` solo se pueden testear en GitHub Actions. Para probar MODIS localmente, usar los fixtures JSON existentes en `data/mirova_equivalent/` y verificar que el audit script funciona contra ellos.

2. **El reprocesamiento con `--overwrite`** requiere acceso a gránulos L1B via earthaccess. Solo funciona con los secrets de GitHub (EARTHDATA_USERNAME/PASSWORD). Para VIIRS-M el reprocesamiento es necesario después de Task 2 porque el pipeline generará resultados distintos con el NTI path.

3. **OCR CSV encoding**: los CSVs están en UTF-8. El campo `Volcan` usa nombres con espacios y guiones ("Puyehue-Cordon Caulle"). El mapping a nombres internos (sin espacios: "PuyehueCordonCaulle") está en el script de auditoría.

4. **Orden de ejecución**: Task 1 → Task 3 pueden correr en paralelo. Task 2 es independiente. Task 4 depende de Task 3. Task 5 depende de todos los anteriores.
