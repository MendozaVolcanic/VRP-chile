# MIROVA Literal Puro — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans para ejecutar tarea por tarea con checkpoints.

**Goal:** Convertir profile `mirova_equivalent` en clon literal de MIROVA según papers Coppola 2016a + Coppola 2020 Frontiers + Campus 2022/2024 + Aveni 2024 RSE — quitando todos los parches que NO están en literatura MIROVA y aplicando thresholds documentados (5σ summit / 10σ scene noche).

**Architecture:** Profile A/B aislado `_mirova_literal` clon de `mirova_equivalent` con cambios. Reproceso 14d × 4 Tier A vs profile control mirror. Decisión data-driven post A/B: si recall agregado se mantiene/sube y FPs scene caen → mergear. Si recall cae → diagnóstico arquitectural claro de qué nos falta.

**Tech Stack:** Python pipeline existente. No deps nuevas. Reusa `dual_roi_bt_threshold` ya implementado S26 (helper puro).

---

## Contexto y motivación (por qué este plan)

Auditoría exhaustiva 2026-04-28 sobre 30+ PDFs reveló:

1. **9 papers más además de Di Bella 2024 NO son MIROVA** — son del grupo INGV Catania (Del Negro, Corradino, Cariello, Torrisi, Amato) y CNR-IMAA Potenza (Marchese, Pergola). NO usar como autoridad MIROVA.
2. **5 papers MIROVA core auditados nuevos** (Coppola 2020, Coppola 2022 Sabancaya, Coppola 2025 Fernandina, Laiolo 2026 Stromboli, Campion+Coppola lava lakes) — NO añaden thresholds nuevos, confirman 5σ/10σ Coppola 2016a Tabla 1.
3. **Laiolo 2026 textual**: *"no atmospheric correction or cloud-contamination automatic filtering is applied"* + *"we avoid the visual inspection... to discard cloud-contaminated images"*. MIROVA NRT NO cura ni filtra nubes.

Nuestro código actual tiene **9 parches que NO están en ningún paper MIROVA**:
- `MAX_SIGMA_COMPONENT_K=7K` cap (S15)
- `MAX_VENT_SIGMA_CONTRIB_K=3K` cap (S12)
- `exclude_zones` (Salar, lagos)
- Vent-path entero (S6-S12)
- Regla D vent-priority (S20)
- Regla D Test 1-priority (S26 D)
- Cloud mask BT<260K (S6)
- Path C NTI relativo (default OFF, OK)
- Pisos VRP por sensor

Plan: **eliminar parches contrarios a paper, aplicar thresholds documentados, medir empíricamente**.

---

## Criterio de aceptación (definir antes de codear)

A/B 14d × 4 Tier A (Lascar, Lastarria, Tupungatito, Villarrica) vs CSV consolidado MIROVA NRT:

✅ **Mergear si**:
- Recall agregado vs MIROVA NRT cae < 10 pp (de 0.81 a ≥0.71). Margen amplio porque algunos parches sí rescataban TPs.
- FPs lejanos vrp>1MW caen ≥40% global.
- Ratio mediano VRP global ≤30× (hoy 57×).

❌ **NO mergear si** alguno falla. Persistir hallazgo como "qué arquitectural falta vs MIROVA literal" para futura sesión.

---

## File Structure

- **Modify**: `pipeline/profiles/mirova_equivalent.yaml` — solo cambios de defaults a futuros (mantener actual durante A/B).
- **Create**: `pipeline/profiles/_mirova_literal.yaml` — profile A/B treatment con cambios.
- **Create**: `pipeline/profiles/_mirova_legacy.yaml` — profile A/B control = mirror exacto operacional actual.
- **Create**: `.github/workflows/reproc-ab-mirova-literal.yml` — workflow A/B 4 vol × 2 profiles.
- **Create**: `experiments/56_mirova_literal_ab/delta_report.py` — forense + criterios de aceptación.
- **No modificar código pipeline**: los parches a deshabilitar ya tienen flags. Solo cambiar valores YAML.

---

### Task 1: Profile `_mirova_legacy` (control mirror operacional)

**Files:**
- Create: `pipeline/profiles/_mirova_legacy.yaml`

- [ ] **Step 1: Clone profile**

```bash
cp pipeline/profiles/mirova_equivalent.yaml pipeline/profiles/_mirova_legacy.yaml
```

- [ ] **Step 2: Edit header + data_subdir**

Cambiar líneas 1-15 (header) y línea ~117 (data_subdir):

```yaml
# VRP-Chile — profile: _mirova_legacy (S27 A/B control)
#
# CLON byte-a-byte de mirova_equivalent.yaml. Solo difiere en data_subdir
# para A/B aislado vs _mirova_literal.

profile: _mirova_legacy
description: >
  A/B control: mirova_equivalent operacional intacto, parches incluidos
  (cap=7K, vent-path, exclude_zones via volcanoes.yaml, Regla D).

# ... resto idéntico a mirova_equivalent.yaml ...

output:
  data_subdir: _mirova_legacy
```

- [ ] **Step 3: Verify profile loads**

```bash
VRP_PROFILE=_mirova_legacy python -c "
from pipeline import profile
print('profile:', profile.PROFILE_NAME)
print('enable_vent_path:', profile.ENABLE_VENT_PATH)
print('max_sigma_component_k:', profile.MAX_SIGMA_COMPONENT_K)
print('data_subdir:', profile.DATA_SUBDIR)
"
```

Expected:
```
profile: _mirova_legacy
enable_vent_path: True
max_sigma_component_k: 7.0
data_subdir: _mirova_legacy
```

- [ ] **Step 4: Commit**

```bash
git add pipeline/profiles/_mirova_legacy.yaml
git commit -m "S27 T1 — profile _mirova_legacy A/B control (mirror operacional)"
```

---

### Task 2: Profile `_mirova_literal` (treatment con cambios)

**Files:**
- Create: `pipeline/profiles/_mirova_literal.yaml`

- [ ] **Step 1: Clone**

```bash
cp pipeline/profiles/mirova_equivalent.yaml pipeline/profiles/_mirova_literal.yaml
```

- [ ] **Step 2: Aplicar 6 cambios al profile**

**Cambio 2a — Header y data_subdir** (líneas 1-15 y final):

```yaml
# VRP-Chile — profile: _mirova_literal (S27 A/B treatment)
#
# CLON LITERAL MIROVA según papers Coppola 2016a Tabla 1 + Coppola 2020
# Frontiers + Campus 2022/2024 + Aveni 2024 RSE. Eliminar parches no-paper:
# - cap MAX_SIGMA_COMPONENT_K=7K → cap=999K (efectivo: sin cap).
# - vent-path desactivado (no existe en papers MIROVA).
# - cloud_mask_bt_k=260K → 0.0 (Laiolo 2026: MIROVA NRT no filtra nubes).
# - dual-ROI BT activado con 5σ summit / 10σ scene (Coppola 2016a Tabla 1).
# - dnti dual-ROI activado (P3.1 ya implementado).
# - Test 1 desactivado (queda flag para experimental futuro).
#
# data_subdir: _mirova_literal (NO contamina operacional).

profile: _mirova_literal
description: >
  A/B treatment: clon MIROVA literal según Coppola 2016a + 2020 + Campus 2024.
  Sin parches.
```

**Cambio 2b — thresholds** (sección `thresholds:`):

```yaml
thresholds:
  anomaly_threshold_k: 5.0
  tir_threshold_k: 0.5
  n_sigma_mir: 3.0  # legacy fallback (no usado cuando enable_dual_roi_bt=true)
  n_sigma_tir: 4.0
  vent_threshold_k: 1.0  # no usado, vent-path desactivado
  n_sigma_vent: 2.0
  nti_k1_night: -0.8
  nti_bt_sanity_k: 3.0
  cloud_mask_bt_k: 0.0  # CAMBIO: MIROVA NRT no filtra nubes (Laiolo 2026 explícito)
  max_sigma_component_k: 999.0  # CAMBIO: cap efectivo deshabilitado
  min_vrp_mw_viirs375: 0.02
  min_vrp_mw_viirs750: 0.15
  min_vrp_mw_modis:    0.27
  min_vent_pixels: 1
  max_vent_sigma_contrib_k: 999.0  # CAMBIO: cap vent también deshabilitado
  nti_rel_n_sigma: 3.0
  nti_rel_min_floor: 0.005
  dnti_contextual_c1: 0.003
  dnti_contextual_c1_summit: 0.003
  dnti_contextual_c1_scene: 0.010
  modis_vent_threshold_k: 1.0
  modis_vent_vrp_floor_mw: 0.0
  # S27 — N·sigma MIROVA literal (Coppola 2016a Tabla 1)
  n_sigma_mir_summit: 5.0
  n_sigma_mir_scene: 10.0
```

**Cambio 2c — paths** (sección `paths:`):

```yaml
paths:
  enable_eruption_path: true
  enable_vent_path: false  # CAMBIO: vent-path NO existe en MIROVA papers
  enable_vent_path_modis: false  # CAMBIO: idem
  enable_nti_relative_path: false  # mantener OFF (no en MIROVA)
  enable_dnti_contextual_path: true  # P3.2 Coppola 2016a SP 426.5
  enable_dnti_dual_roi: true  # P3.1 Coppola 2016a Table 2
  enable_test1_path: false  # CAMBIO: Test 1 disponible pero OFF en literal puro
  # S27 — dual-ROI BT (Coppola 2016a Tabla 1) ACTIVADO
  enable_dual_roi_bt: true
```

**Cambio 2d — output**:

```yaml
output:
  data_subdir: _mirova_literal
```

- [ ] **Step 3: Verify profile loads**

```bash
VRP_PROFILE=_mirova_literal python -c "
from pipeline import profile
print('enable_vent_path:', profile.ENABLE_VENT_PATH)
print('enable_dual_roi_bt:', profile.ENABLE_DUAL_ROI_BT)
print('n_sigma_summit:', profile.N_SIGMA_MIR_SUMMIT)
print('n_sigma_scene:', profile.N_SIGMA_MIR_SCENE)
print('max_sigma_cap:', profile.MAX_SIGMA_COMPONENT_K)
print('cloud_mask_bt_k:', profile.CLOUD_MASK_BT_K)
"
```

Expected:
```
enable_vent_path: False
enable_dual_roi_bt: True
n_sigma_summit: 5.0
n_sigma_scene: 10.0
max_sigma_cap: 999.0
cloud_mask_bt_k: 0.0
```

- [ ] **Step 4: Commit**

```bash
git add pipeline/profiles/_mirova_literal.yaml
git commit -m "S27 T2 — profile _mirova_literal A/B treatment (5sigma/10sigma + sin parches)"
```

---

### Task 3: Verificar que `volcanoes.yaml exclude_zones` NO se aplique en `_mirova_literal`

**Contexto**: las exclude_zones están en `volcanoes.yaml` (no en profile YAML). El código las aplica si existen. Para `_mirova_literal` queremos que NO se apliquen.

**Files:**
- Modify: `pipeline/process_modis.py`, `pipeline/process_viirs.py`, `pipeline/process_viirs_mod.py`

- [ ] **Step 1: Add profile flag `enable_exclude_zones`**

Edit `pipeline/profile.py` (después de `ENABLE_DUAL_ROI_BT`):

```python
# S27 MIROVA literal: flag para deshabilitar exclude_zones (parche nuestro).
# MIROVA NO usa máscaras geográficas. Default true (operacional mantiene),
# false en _mirova_literal para test A/B.
ENABLE_EXCLUDE_ZONES: bool = bool(_p.get("enable_exclude_zones", True))
```

- [ ] **Step 2: Use flag in process_modis.py**

Find the section that loads exclude_zones from volcano dict:

```bash
grep -n "exclude_zones" pipeline/process_modis.py | head -5
```

In the relevant location (where `exclude_zones` is read from volcano), add guard:

```python
# S27: cuando ENABLE_EXCLUDE_ZONES=False (literal MIROVA), ignorar zonas.
if not ENABLE_EXCLUDE_ZONES:
    exclude_zones = None
    active_water_bodies = None
```

Repeat in `process_viirs.py` and `process_viirs_mod.py` at equivalent locations.

- [ ] **Step 3: Add to imports**

In each `process_*.py`, add `ENABLE_EXCLUDE_ZONES` to the `from .profile import (...)` block.

- [ ] **Step 4: Add to `_mirova_literal.yaml` paths**

```yaml
paths:
  # ... existing ...
  enable_exclude_zones: false  # S27 MIROVA literal: parche nuestro deshabilitado
```

- [ ] **Step 5: Verify suite green**

```bash
pytest 2>&1 | tail -3
```

Expected: 187 passed (mismo número, no rompe nada).

- [ ] **Step 6: Commit**

```bash
git add pipeline/profile.py pipeline/process_modis.py pipeline/process_viirs.py pipeline/process_viirs_mod.py pipeline/profiles/_mirova_literal.yaml
git commit -m "S27 T3 — flag ENABLE_EXCLUDE_ZONES, off en _mirova_literal"
```

---

### Task 4: Workflow A/B reproc

**Files:**
- Create: `.github/workflows/reproc-ab-mirova-literal.yml`

- [ ] **Step 1: Create workflow**

```yaml
name: A/B reproceso MIROVA literal puro (S27)

# Workflow dispatch-only para validación cuantitativa de "MIROVA literal":
# - 5σ summit / 10σ scene noche (Coppola 2016a Tabla 1).
# - Sin cap=7K (parche S15 deshabilitado).
# - Sin vent-path (no existe en papers MIROVA).
# - Sin exclude_zones (parche nuestro).
# - Sin cloud mask BT<260K (Laiolo 2026: MIROVA NRT no filtra).
# - Mantiene Coppola 2015 NTI Test 2 + Coppola 2016a dNTI 8-vec mean +
#   P3.1 dual-ROI dNTI + Stefan-Boltzmann TIR + k Wooster/Campus.
#
# Profiles paralelos:
#   _mirova_literal  → treatment (literal puro)
#   _mirova_legacy   → control (operacional con parches)

on:
  workflow_dispatch:
    inputs:
      start:
        description: "Start date YYYY-MM-DD"
        required: true
        default: "2026-04-12"
      end:
        description: "End date YYYY-MM-DD"
        required: true
        default: "2026-04-25"

jobs:
  reproc:
    runs-on: ubuntu-latest
    timeout-minutes: 60
    permissions:
      contents: write
    strategy:
      fail-fast: false
      max-parallel: 8
      matrix:
        volcano: [Lascar, Lastarria, Tupungatito, Villarrica]
        profile: [_mirova_literal, _mirova_legacy]
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          sudo apt-get install -y libhdf4-dev
          pip install pyhdf
          pip install earthaccess numpy h5py scipy pyyaml

      - name: Run reprocess — ${{ matrix.profile }} / ${{ matrix.volcano }}
        env:
          EARTHDATA_USERNAME: ${{ secrets.EARTHDATA_USERNAME }}
          EARTHDATA_PASSWORD: ${{ secrets.EARTHDATA_PASSWORD }}
        timeout-minutes: 50
        run: |
          python scripts/run_pipeline.py \
            --profile ${{ matrix.profile }} \
            --volcano ${{ matrix.volcano }} \
            --start ${{ github.event.inputs.start }} \
            --end ${{ github.event.inputs.end }} \
            --overwrite

      - name: Commit reprocessed A/B data
        run: |
          set +e
          git config user.name  "vrp-bot"
          git config user.email "vrp-bot@github-actions"
          git add "data/${{ matrix.profile }}/${{ matrix.volcano }}.json" 2>/dev/null
          git diff --staged --quiet && { echo "No changes to commit"; exit 0; }
          git commit -m "S27 A/B MIROVA literal — ${{ matrix.profile }} / ${{ matrix.volcano }} 14d"
          for attempt in 1 2 3 4 5; do
            git pull --rebase -X theirs origin main && git push && exit 0
            echo "push attempt $attempt failed, sleeping $((attempt * 10))s"
            git rebase --abort 2>/dev/null
            sleep $((attempt * 10))
          done
          echo "all push attempts failed"; exit 1
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/reproc-ab-mirova-literal.yml
git commit -m "S27 T4 — workflow A/B reproceso MIROVA literal puro"
```

---

### Task 5: Push to main + dispatch

- [ ] **Step 1: Push s15-dev + sync main**

```bash
git push origin s15-dev
git checkout main
git pull origin main
git merge s15-dev --no-edit
git push origin main
git checkout s15-dev
```

- [ ] **Step 2: Dispatch workflow**

```bash
gh workflow run reproc-ab-mirova-literal.yml -R MendozaVolcanic/VRP-chile --ref main \
  -f start=2026-04-12 -f end=2026-04-25
```

- [ ] **Step 3: Capture run ID**

```bash
sleep 5
gh run list -R MendozaVolcanic/VRP-chile --workflow=reproc-ab-mirova-literal.yml -L 1 \
  --json databaseId,status
```

Save the `databaseId` for later monitoring.

- [ ] **Step 4: Wait for completion**

```bash
RUN_ID=<from step 3>
until [ "$(gh run view $RUN_ID -R MendozaVolcanic/VRP-chile --json status -q .status)" = "completed" ]; do
  sleep 90
done
gh run view $RUN_ID -R MendozaVolcanic/VRP-chile --json conclusion,jobs \
  --jq '.jobs[] | "\(.name) :: \(.conclusion)"'
```

Expected: 8/8 success o documentar failures (transitorios NASA Earthdata son aceptables).

---

### Task 6: Forense + delta report con criterios de aceptación

**Files:**
- Create: `experiments/56_mirova_literal_ab/delta_report.py`

- [ ] **Step 1: Create directory**

```bash
mkdir -p experiments/56_mirova_literal_ab
```

- [ ] **Step 2: Create delta_report.py**

```python
"""56_mirova_literal_ab/delta_report.py — A/B MIROVA literal vs legacy (S27).

Criterio de aceptación (plan_2026-04-28-mirova-literal-puro.md):
  - Recall agregado vs MIROVA NRT cae < 10 pp.
  - FPs lejanos vrp>1MW caen ≥40% global.
  - Ratio mediano VRP global ≤30× (hoy 57×).

Si las 3 PASS → mergear flags a `mirova_equivalent.yaml`.
Si NO PASS → persistir hallazgo, NO mergear.
"""
from __future__ import annotations
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))
from experiments.forense_h17_replicable import _parse_dt_csv, _parse_dt_record, sensor_match

PROFILES = ["_mirova_literal", "_mirova_legacy"]
VOLCANOES = ["Lascar", "Lastarria", "Tupungatito", "Villarrica"]
START = datetime(2026, 4, 12, tzinfo=timezone.utc)
END = datetime(2026, 4, 25, 23, 59, 59, tzinfo=timezone.utc)
TOL = timedelta(minutes=60)
CSV_PATH = ROOT / "data" / "mirova_reference" / "mirova_v1_snapshot" / "registro_vrp_consolidado.csv"
OUT = Path(__file__).parent / "DELTA_REPORT.md"


def _vol_csv_name(v):
    return {"PuyehueCordonCaulle": "Puyehue-Cordon Caulle",
            "PlanchonPeteroa": "Planchon-Peteroa",
            "NevadosDeChillan": "Nevados de Chillan"}.get(v, v)


def metrics_for(profile, volcano):
    p = ROOT / "data" / profile / f"{volcano}.json"
    if not p.exists():
        return None
    raw = json.loads(p.read_text(encoding="utf-8"))
    records = raw["records"] if isinstance(raw, dict) else raw

    df = pd.read_csv(CSV_PATH)
    df = df[(df.Volcan == _vol_csv_name(volcano)) & (df.Tipo_Registro == "ALERTA_TERMICA")].copy()
    df["dt"] = df.Fecha_Satelite_UTC.apply(_parse_dt_csv)
    refs = df[(df.dt >= START) & (df.dt <= END)]

    tp, fn = 0, 0
    matched = set()
    ratios = []
    for _, ref in refs.iterrows():
        ref_dt = ref["dt"]
        ref_sensor = ref["Sensor"]
        ref_vrp = ref["VRP_MW"]
        found = False
        for rec in records:
            try:
                rec_dt = _parse_dt_record(rec["datetime_utc"])
            except Exception:
                continue
            if rec_dt < START or rec_dt > END:
                continue
            if abs((rec_dt - ref_dt).total_seconds()) > TOL.total_seconds():
                continue
            if not sensor_match(ref_sensor, rec["sensor"]):
                continue
            if rec.get("vrp_mw", 0) > 0 and rec.get("distance_class") == "summit":
                tp += 1
                matched.add(id(rec))
                if ref_vrp > 0:
                    ratios.append(rec["vrp_mw"] / ref_vrp)
                found = True
                break
        if not found:
            fn += 1

    fp_far_high = sum(1 for r in records
                      if r.get("vrp_mw", 0) > 1
                      and r.get("distance_class") == "far"
                      and id(r) not in matched
                      and r.get("datetime_utc"))

    recall = tp / (tp + fn) if (tp + fn) else float("nan")
    rmed = sorted(ratios)[len(ratios) // 2] if ratios else float("nan")
    return {"tp": tp, "fn": fn, "fp_far_high": fp_far_high, "recall": recall,
            "ratio_med": rmed, "n_refs": len(refs), "ratios": ratios}


def main():
    rows = {p: {v: metrics_for(p, v) for v in VOLCANOES} for p in PROFILES}

    lines = ["# A/B MIROVA literal puro — Delta Report (S27)", ""]
    lines.append(f"Ventana: {START.date()} → {END.date()} (14d).")
    lines.append("")
    lines.append("| Volcán | Refs | TP lit/leg | FN lit/leg | FP_far lit/leg | Recall lit/leg | Ratio med lit/leg |")
    lines.append("|---|---:|---|---|---|---|---|")

    agg = {p: {"tp": 0, "fn": 0, "fp_far_high": 0, "ratios": []} for p in PROFILES}
    for v in VOLCANOES:
        lit = rows[PROFILES[0]][v]
        leg = rows[PROFILES[1]][v]
        if lit is None or leg is None:
            lines.append(f"| {v} | — | — | — | — | — | — |")
            continue
        n_refs = lit["n_refs"]
        lines.append(
            f"| {v} | {n_refs} | "
            f"{lit['tp']}/{leg['tp']} | "
            f"{lit['fn']}/{leg['fn']} | "
            f"{lit['fp_far_high']}/{leg['fp_far_high']} | "
            f"{lit['recall']:.2f}/{leg['recall']:.2f} | "
            f"{lit['ratio_med']:.2f}/{leg['ratio_med']:.2f} |"
        )
        for k in ["tp", "fn", "fp_far_high"]:
            agg[PROFILES[0]][k] += lit[k]
            agg[PROFILES[1]][k] += leg[k]
        agg[PROFILES[0]]["ratios"].extend(lit["ratios"])
        agg[PROFILES[1]]["ratios"].extend(leg["ratios"])

    rec_lit = agg[PROFILES[0]]["tp"] / (agg[PROFILES[0]]["tp"] + agg[PROFILES[0]]["fn"]) if (agg[PROFILES[0]]["tp"] + agg[PROFILES[0]]["fn"]) else 0
    rec_leg = agg[PROFILES[1]]["tp"] / (agg[PROFILES[1]]["tp"] + agg[PROFILES[1]]["fn"]) if (agg[PROFILES[1]]["tp"] + agg[PROFILES[1]]["fn"]) else 0
    rmed_lit = sorted(agg[PROFILES[0]]["ratios"])[len(agg[PROFILES[0]]["ratios"]) // 2] if agg[PROFILES[0]]["ratios"] else 0
    rmed_leg = sorted(agg[PROFILES[1]]["ratios"])[len(agg[PROFILES[1]]["ratios"]) // 2] if agg[PROFILES[1]]["ratios"] else 0

    lines.append("")
    lines.append("## Agregado")
    lines.append("")
    lines.append("| Métrica | MIROVA Literal | Legacy (parches) | Δ |")
    lines.append("|---|---:|---:|---:|")
    lines.append(f"| TP | {agg[PROFILES[0]]['tp']} | {agg[PROFILES[1]]['tp']} | {agg[PROFILES[0]]['tp']-agg[PROFILES[1]]['tp']:+d} |")
    lines.append(f"| FN | {agg[PROFILES[0]]['fn']} | {agg[PROFILES[1]]['fn']} | {agg[PROFILES[0]]['fn']-agg[PROFILES[1]]['fn']:+d} |")
    lines.append(f"| FP_far | {agg[PROFILES[0]]['fp_far_high']} | {agg[PROFILES[1]]['fp_far_high']} | {agg[PROFILES[0]]['fp_far_high']-agg[PROFILES[1]]['fp_far_high']:+d} |")
    lines.append(f"| Recall | {rec_lit:.3f} | {rec_leg:.3f} | {rec_lit-rec_leg:+.3f} |")
    lines.append(f"| Ratio mediano | {rmed_lit:.2f} | {rmed_leg:.2f} | {rmed_lit-rmed_leg:+.2f} |")
    lines.append("")

    delta_recall_pp = (rec_lit - rec_leg) * 100
    fp_drop = (agg[PROFILES[1]]["fp_far_high"] - agg[PROFILES[0]]["fp_far_high"]) / agg[PROFILES[1]]["fp_far_high"] if agg[PROFILES[1]]["fp_far_high"] else 0

    crit1 = delta_recall_pp >= -10
    crit2 = fp_drop >= 0.40
    crit3 = rmed_lit <= 30

    lines.append("## Veredicto")
    lines.append("")
    lines.append(f"- {'✓' if crit1 else '✗'} Recall cae < 10 pp → Δ = {delta_recall_pp:+.1f} pp.")
    lines.append(f"- {'✓' if crit2 else '✗'} FP_far cae ≥ 40% → caída = {fp_drop*100:+.1f}%.")
    lines.append(f"- {'✓' if crit3 else '✗'} Ratio mediano ≤ 30× → ratio literal = {rmed_lit:.1f}×.")
    lines.append("")
    if crit1 and crit2 and crit3:
        lines.append("**APROBADO** → mergear flags a `mirova_equivalent.yaml`.")
    else:
        lines.append("**NO APROBADO** → persistir hallazgo, NO mergear.")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Delta report en {OUT}")
    print()
    print("\n".join(lines))


if __name__ == "__main__":
    import io
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    main()
```

- [ ] **Step 3: Pull data + run delta**

```bash
git pull origin main
python experiments/56_mirova_literal_ab/delta_report.py
```

- [ ] **Step 4: Commit**

```bash
git add experiments/56_mirova_literal_ab/
git commit -m "S27 T6 — delta report A/B MIROVA literal puro"
```

---

### Task 7: Decisión basada en resultado

- [ ] **Step 1: Si los 3 criterios PASS**

Editar `pipeline/profiles/mirova_equivalent.yaml`:
1. Sección `thresholds:`: agregar `n_sigma_mir_summit: 5.0`, `n_sigma_mir_scene: 10.0`, cambiar `cloud_mask_bt_k: 0.0`, `max_sigma_component_k: 999.0`, `max_vent_sigma_contrib_k: 999.0`.
2. Sección `paths:`: `enable_vent_path: false`, `enable_vent_path_modis: false`, `enable_dual_roi_bt: true`, `enable_exclude_zones: false`, `enable_test1_path: false`.

Borrar profiles `_mirova_literal.yaml` y `_mirova_legacy.yaml` post-merge (cleanup).

Re-dispatch reproceso histórico Tier A con `mirova_equivalent` actualizado.

Persistir hallazgo en `~memory/project_s27_mirova_literal_aprobado.md`:
- Recall agregado L vs L pre.
- FP_far reducción.
- Magnitud paridad.
- Lecciones.

- [ ] **Step 2: Si los 3 criterios NO PASS**

NO mergear. Borrar profiles A/B (cleanup).

Persistir en `~memory/project_s27_mirova_literal_negativo.md`:
- Resultado por criterio (cuál falló).
- Hipótesis qué arquitectural falta vs MIROVA literal.
- Pendientes para sesión futura (probable: investigar cómo MIROVA compone paths internamente).

- [ ] **Step 3: Commit final**

```bash
git add pipeline/ memory/ experiments/
git commit -m "S27 cierre MIROVA literal — APROBADO/NO-APROBADO según resultado A/B"
git push origin s15-dev
```

---

## Self-Review

**Spec coverage**:
- ✓ T1-T2: profiles A/B aislados.
- ✓ T3: exclude_zones flag.
- ✓ T4-T5: workflow + dispatch.
- ✓ T6: forense + criterios aceptación.
- ✓ T7: decisión + cleanup.

**Placeholder scan**:
- ✓ Todos los pasos contienen código completo.
- ✓ Comandos exactos con expected output.
- ✓ Sin "TBD" ni "implementar después".

**Type consistency**:
- ✓ Profile names consistentes (`_mirova_literal` y `_mirova_legacy` en todo el plan).
- ✓ Variables consistentes (`ENABLE_EXCLUDE_ZONES`, `N_SIGMA_MIR_SUMMIT`, etc.).
- ✓ Workflow filenames consistentes (`reproc-ab-mirova-literal.yml`).

## Antipatrón a evitar

NO descubrir un nuevo problema durante implementación → fixearlo aquí. Si pasa: anotar en backlog (`tasks/backlog_s27.md`), terminar este plan, evaluar después.

## Pendientes que NO entran en este plan (backlog explícito)

- Investigar cómo MIROVA compone paths internamente (cascada vs OR), si Task 7 falla.
- Test 1 a MODIS y VIIRS 750m (si literal puro funciona pero queremos mejorar Villarrica recall).
- Path TIR-only Villarrica (Aveni 2024 RSE TIRVolcH completo).
- Fix outliers magnitud Villarrica 2026-01-14 y 2026-02-26 (1693-2597× ratio).
- Auditar 6 papers MIROVA core restantes (Coppola 2009, 2013, Aveni 2023 MERSI-II, Aveni 2025 lava cooling, Massimetti 2024 Stromboli, Campion lava lakes ya hecho parcial).
- Refactor race condition matrix paralelo (max-parallel:1 cuando mismo archivo).
