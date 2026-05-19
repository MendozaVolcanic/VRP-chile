# S62 — PCC inner_radius fix + A/B Lastarria/Tupungatito kernel-bg

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Aplicar quick win PCC `inner_radius_km: 20→7` (validado offline 97 ALERTAS, ratio 3.51× → 1.86×), disparar A/B kernel-bg para Lastarria + Tupungatito (patrón térmico igual a Villarrica/PP según investigación H S61), y refrescar dashboard PCC con reproc operacional.

**Architecture:** 3 cambios YAML/workflow paralelos. (1) Edit `volcanoes.yaml` PCC, (2) crear workflow A/B Lastarria+Tupungatito kernel-bg (profile experimental `_local_kernel_bg_enabled`), (3) crear workflow reproc operacional PCC para refresh dashboard tras el cambio inner_radius. NO se toca código pipeline. Tests existentes no se afectan.

**Tech Stack:** YAML config (volcanoes.yaml), GitHub Actions workflows (matrix max-parallel=2), Python 3.11 pipeline existente, gh CLI.

---

## File Structure

| Archivo | Responsabilidad | Operación |
|---|---|---|
| `volcanoes.yaml` | PCC `inner_radius_km: 20 → 7` con comentario | **Modificar** línea ~7 (PCC bloque) |
| `.github/workflows/reproc-ab-lastarria-tupungatito.yml` | A/B kernel-bg Lastarria + Tupungatito | **Crear** |
| `.github/workflows/reproc-pcc-operacional.yml` | Reproc PCC operacional con nuevo inner_radius | **Crear** |
| `experiments/110_s62_audit_pcc_lastarria_tupungatito.py` | Audit post-workflows (script) | **Crear** post-reproc |
| `experiments/110_s62_results.md` | Resultado audit + decisión adopción | **Crear** post-reproc |
| `docs/HYPOTHESIS_LOG.md` | Append H_S62_PCC + H_S62_LASTARRIA_TUPUNGATITO | **Modificar** post-results |
| `tasks/BLOQUE_ARRANQUE_S63.md` | Bloque arranque siguiente | **Crear** al cierre |

---

## Task 1: Quick win PCC `inner_radius_km` 20→7

**Files:**
- Modify: `volcanoes.yaml` (bloque PuyehueCordonCaulle)

**Razón**: preview offline S61 con 97 ALERTAS (CONS+OCR) window 80d mostró:
- inner=20 (actual): ratio mediano 3.51×, 86 detected, 16% en rango [0.5-2.0]
- inner=7: ratio mediano **1.86×** (-47%), 63 detected, 22% en rango
- inner=5: ratio 4.02× (TOO TIGHT, recall colapsa)

Sweet spot inner=7 km. Validado contra `lacolito` (`mirova_center` PCC = -40.582, -72.131).

- [ ] **Step 1.1: Localizar línea PCC inner_radius_km en volcanoes.yaml**

Run: `grep -n "inner_radius_km" volcanoes.yaml | grep -B5 "mirova_center_lat: -40.582"` o buscar bloque `name: PuyehueCordonCaulle`. Línea esperada ~500-510.

```bash
grep -n -A30 "^- name: PuyehueCordonCaulle" volcanoes.yaml | grep "inner_radius_km" | head -1
```

Expected: línea con `inner_radius_km: 20`.

- [ ] **Step 1.2: Editar volcanoes.yaml PCC**

Cambiar:
```yaml
  inner_radius_km: 20  # MIROVA KML oficial — summit/far visual
```
a:
```yaml
  # S62 reducido 20→7 — preview offline 97 ALERTAS CONS+OCR window 80d:
  # ratio mediano 3.51× → 1.86× (-47%), recall 86→63 (-27% acepta porque
  # records perdidos son clusters >7km lacolito que MIROVA reporta como
  # far, no summit). 20 km era extremadamente permisivo vs otros Tier A
  # (Villarrica=5, Lascar=5, Lastarria=3). Validado con mirova_center=lacolito.
  # Si recall NRT regresiona >40%, revertir a 10 o 12.
  inner_radius_km: 7
```

Verificar:
```bash
grep -A1 "^- name: PuyehueCordonCaulle" volcanoes.yaml | head -5
grep -B2 -A3 "inner_radius_km: 7" volcanoes.yaml | grep -A2 "S62 reducido"
```

Expected: ver el comentario S62 + `inner_radius_km: 7`.

- [ ] **Step 1.3: Tests pipeline siguen pasando**

```bash
python -m pytest tests/ -x -q
```

Expected: `335 passed, 16 skipped` (sin regresión por cambio yaml — los tests no parsean inner_radius_km específicamente para PCC).

- [ ] **Step 1.4: Commit**

```bash
git add volcanoes.yaml
git commit -m "S62 quick win PCC: inner_radius_km 20→7 (preview offline 97 ALERTAS ratio 3.51x→1.86x)"
```

---

## Task 2: Crear workflow A/B Lastarria + Tupungatito kernel-bg

**Files:**
- Create: `.github/workflows/reproc-ab-lastarria-tupungatito.yml`

**Razón**: investigación H S61 (`experiments/108_s62_tupungatito_test1_investigation.md` + hipótesis `H_S61_LASTARRIA_KERNEL_BG_NEEDED`) reveló que Lastarria + Tupungatito tienen el mismo patrón térmico que Villarrica/PP:
- ΔT bajo (~12K Lastarria) o régimen Muy Bajo
- Background ring frío (Atacama desierto / glaciar) → ΔL inflado
- Test 1 integrated-ROI suma muchos pixels marginales → magnitud inflada 7-8×

Hipótesis: fix kernel-bg cura igual que Villarrica (de 31× → 2.16×) y PP (11× → 2.64×).

Profile usado: `_local_kernel_bg_enabled` (ya existe, S58). Output `data/_local_kernel_bg_enabled/<Vol>.json` (no operacional aún).

- [ ] **Step 2.1: Crear workflow A/B Lastarria+Tupungatito**

Contenido del archivo:

```yaml
name: A/B reproceso local kernel background — Lastarria + Tupungatito (S62)

# S62 hipótesis (H S61): Lastarria y Tupungatito sufren mismo mecanismo
# que Villarrica/PP — ring background frío (Atacama desierto / glaciar)
# sesga L_bg bajo → ΔL inflado → Test 1 integrated-ROI suma pixels
# marginales → magnitud 7-8× vs MIROVA NRT.
#
# Profile target: _local_kernel_bg_enabled (igual que S58 Villarrica/PP).
# Window default cubre 4-5 ALERTAS Lastarria + 22 ALERTAS Tupungatito CONS.

on:
  workflow_dispatch:
    inputs:
      start:
        description: "Start date YYYY-MM-DD"
        required: true
        default: "2026-03-01"
      end:
        description: "End date YYYY-MM-DD (inclusive)"
        required: true
        default: "2026-05-19"

jobs:
  reproc:
    runs-on: ubuntu-latest
    timeout-minutes: 300
    permissions:
      contents: write
    strategy:
      fail-fast: false
      max-parallel: 2
      matrix:
        volcano: [Lastarria, Tupungatito]

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

      - name: Run reprocess — _local_kernel_bg_enabled / ${{ matrix.volcano }}
        env:
          EARTHDATA_USERNAME: ${{ secrets.EARTHDATA_USERNAME }}
          EARTHDATA_PASSWORD: ${{ secrets.EARTHDATA_PASSWORD }}
        timeout-minutes: 280
        run: |
          python scripts/run_pipeline.py \
            --profile _local_kernel_bg_enabled \
            --volcano ${{ matrix.volcano }} \
            --start ${{ github.event.inputs.start }} \
            --end ${{ github.event.inputs.end }} \
            --overwrite

      - name: Commit reprocessed A/B data
        run: |
          set +e
          git config user.name  "vrp-bot"
          git config user.email "vrp-bot@github-actions"
          git add "data/_local_kernel_bg_enabled/${{ matrix.volcano }}.json" 2>/dev/null
          git diff --staged --quiet && { echo "No changes to commit"; exit 0; }
          git commit -m "S62 A/B local kernel bg — ${{ matrix.volcano }} ${{ github.event.inputs.start }}→${{ github.event.inputs.end }}"
          for attempt in 1 2 3 4 5; do
            git pull --rebase -X theirs origin main && git push && exit 0
            echo "push attempt $attempt failed, sleeping $((attempt * 10))s"
            git rebase --abort 2>/dev/null
            sleep $((attempt * 10))
          done
          echo "all push attempts failed"; exit 1
```

- [ ] **Step 2.2: Validar YAML sintaxis local**

```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/reproc-ab-lastarria-tupungatito.yml'))" && echo "YAML OK"
```

Expected: `YAML OK`.

- [ ] **Step 2.3: Commit**

```bash
git add .github/workflows/reproc-ab-lastarria-tupungatito.yml
git commit -m "S62 Task 2: workflow A/B kernel-bg Lastarria + Tupungatito"
```

---

## Task 3: Crear workflow reproc operacional PCC

**Files:**
- Create: `.github/workflows/reproc-pcc-operacional.yml`

**Razón**: Task 1 cambia `inner_radius_km` PCC en `volcanoes.yaml` pero el cron NRT solo procesa el día corriente. Los records históricos PCC en `data/mirova_equivalent/PuyehueCordonCaulle.json` siguen con clusters seleccionados con inner=20. Para que el dashboard refleje el nuevo inner=7, hay que reprocesar el window de actividad reciente.

Window: 2026-04-01 → 2026-05-19 (49 días, cubre ~30 ALERTAS PCC CONS + ~15 OCR).

- [ ] **Step 3.1: Crear workflow reproc operacional PCC**

Contenido del archivo:

```yaml
name: Reproc operacional PuyehueCordonCaulle (S62 inner_radius fix)

# S62: Task 1 cambió inner_radius_km PCC 20→7 en volcanoes.yaml.
# Cron NRT solo procesa día corriente → records históricos del dashboard
# siguen con clusters seleccionados con inner=20.
# Este workflow reprocesa PCC operacional para refresh el dashboard
# con clusters bajo el nuevo inner_radius=7.
# Sobreescribe data/mirova_equivalent/PuyehueCordonCaulle.json directamente.

on:
  workflow_dispatch:
    inputs:
      start:
        description: "Start date YYYY-MM-DD"
        required: true
        default: "2026-04-01"
      end:
        description: "End date YYYY-MM-DD (inclusive)"
        required: true
        default: "2026-05-19"

jobs:
  reproc:
    runs-on: ubuntu-latest
    timeout-minutes: 300
    permissions:
      contents: write

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

      - name: Run reprocess — mirova_equivalent / PuyehueCordonCaulle
        env:
          EARTHDATA_USERNAME: ${{ secrets.EARTHDATA_USERNAME }}
          EARTHDATA_PASSWORD: ${{ secrets.EARTHDATA_PASSWORD }}
        timeout-minutes: 280
        run: |
          python scripts/run_pipeline.py \
            --profile mirova_equivalent \
            --volcano PuyehueCordonCaulle \
            --start ${{ github.event.inputs.start }} \
            --end ${{ github.event.inputs.end }} \
            --overwrite

      - name: Commit refreshed operational data
        run: |
          set +e
          git config user.name  "vrp-bot"
          git config user.email "vrp-bot@github-actions"
          git add "data/mirova_equivalent/PuyehueCordonCaulle.json" 2>/dev/null
          git diff --staged --quiet && { echo "No changes to commit"; exit 0; }
          git commit -m "S62 reproc operacional PCC inner_radius=7 ${{ github.event.inputs.start }}→${{ github.event.inputs.end }}"
          for attempt in 1 2 3 4 5; do
            git pull --rebase -X theirs origin main && git push && exit 0
            echo "push attempt $attempt failed, sleeping $((attempt * 10))s"
            git rebase --abort 2>/dev/null
            sleep $((attempt * 10))
          done
          echo "all push attempts failed"; exit 1
```

- [ ] **Step 3.2: Validar YAML sintaxis**

```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/reproc-pcc-operacional.yml'))" && echo "YAML OK"
```

Expected: `YAML OK`.

- [ ] **Step 3.3: Commit**

```bash
git add .github/workflows/reproc-pcc-operacional.yml
git commit -m "S62 Task 3: workflow reproc operacional PCC inner_radius=7"
```

---

## Task 4: PR + merge S62 cambios

**Files:**
- ninguno (operación git)

- [ ] **Step 4.1: Push branch**

```bash
git push -u origin claude/s62-execution
```

- [ ] **Step 4.2: Crear PR cambios S62**

```bash
gh pr create --title "S62: PCC inner_radius 20→7 + workflows A/B Lastarria/Tupungatito + reproc PCC" --body "$(cat <<'EOF'
## Summary

3 cambios paralelos S62:

1. **PCC `inner_radius_km` 20→7** en `volcanoes.yaml`. Preview offline 97 ALERTAS (CONS+OCR): ratio mediano 3.51× → **1.86×** (-47%). Recall 86→63 (acepta).

2. **Workflow A/B Lastarria + Tupungatito kernel-bg**. Hipótesis: mismo patrón térmico Villarrica/PP. Si valida, agregar a per-vol `local_kernel_bg: true` en S63.

3. **Workflow reproc operacional PCC** con nuevo inner_radius para refresh dashboard.

## Test plan

- [x] Tests pipeline: 335 passed / 16 skipped
- [ ] Disparar workflow A/B Lastarria+Tupungatito → audit
- [ ] Disparar workflow reproc PCC → verificar dashboard

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 4.3: Merge tras checks**

```bash
gh pr view <PR#> -R MendozaVolcanic/VRP-chile --json statusCheckRollup
# Si verde:
gh pr merge <PR#> --squash --delete-branch -R MendozaVolcanic/VRP-chile
```

---

## Task 5: Disparar workflows en paralelo

**Files:**
- ninguno (operación remota)

- [ ] **Step 5.1: Disparar A/B Lastarria + Tupungatito**

```bash
gh workflow run reproc-ab-lastarria-tupungatito.yml \
  -f start=2026-03-01 \
  -f end=2026-05-19 \
  -R MendozaVolcanic/VRP-chile
```

- [ ] **Step 5.2: Disparar reproc operacional PCC**

```bash
gh workflow run reproc-pcc-operacional.yml \
  -f start=2026-04-01 \
  -f end=2026-05-19 \
  -R MendozaVolcanic/VRP-chile
```

- [ ] **Step 5.3: Anotar IDs runs y monitorear inicio**

```bash
sleep 15
gh run list --workflow=reproc-ab-lastarria-tupungatito.yml -R MendozaVolcanic/VRP-chile --limit 1 --json databaseId,status
gh run list --workflow=reproc-pcc-operacional.yml -R MendozaVolcanic/VRP-chile --limit 1 --json databaseId,status
```

Expected: ambos `status=in_progress` o `queued`.

- [ ] **Step 5.4: Crear `tasks/S62_workflow_status.md`**

Contenido:

```markdown
# S62 Workflow Status

## Run A/B Lastarria + Tupungatito
- Run ID: <ID-1>
- URL: https://github.com/MendozaVolcanic/VRP-chile/actions/runs/<ID-1>
- Triggered: <fecha hora UTC>
- Window: 2026-03-01 → 2026-05-19 (80 días)
- ETA: ~3-4h
- Profile: `_local_kernel_bg_enabled`
- Output: `data/_local_kernel_bg_enabled/Lastarria.json` y `Tupungatito.json`

## Run Reproc PCC operacional
- Run ID: <ID-2>
- URL: https://github.com/MendozaVolcanic/VRP-chile/actions/runs/<ID-2>
- Triggered: <fecha hora UTC>
- Window: 2026-04-01 → 2026-05-19 (49 días)
- ETA: ~2-3h
- Profile: `mirova_equivalent` (operacional)
- Output: `data/mirova_equivalent/PuyehueCordonCaulle.json`

## Audit pendiente

Cuando ambos terminen:
1. Run audit script `experiments/110_s62_audit_pcc_lastarria_tupungatito.py`
2. Decidir adopción Lastarria/Tupungatito kernel-bg → `volcanoes.yaml` `local_kernel_bg: true`
3. Validar PCC dashboard refleja inner=7 con magnitudes correctas
```

```bash
git add tasks/S62_workflow_status.md
git commit -m "S62 Task 5: workflows disparados — status tracking"
```

---

## Task 6: Audit post-workflows (cuando terminen)

**Files:**
- Create: `experiments/110_s62_audit_pcc_lastarria_tupungatito.py`
- Create: `experiments/110_s62_results.md`

**Pre-condición**: ambos workflows Task 5 completados (`conclusion=success`).

- [ ] **Step 6.1: Esperar terminación + pull main**

```bash
# Monitor cada ~30 min hasta completar
gh run view <ID-1> -R MendozaVolcanic/VRP-chile --json status,conclusion
gh run view <ID-2> -R MendozaVolcanic/VRP-chile --json status,conclusion

# Cuando ambos completados:
git pull --rebase origin main
ls -la data/_local_kernel_bg_enabled/Lastarria.json data/_local_kernel_bg_enabled/Tupungatito.json
ls -la data/mirova_equivalent/PuyehueCordonCaulle.json
```

Expected: 3 archivos modificados con fechas hoy.

- [ ] **Step 6.2: Crear audit script `experiments/110_s62_audit_pcc_lastarria_tupungatito.py`**

```python
"""S62 Audit — PCC inner_radius=7 + A/B Lastarria/Tupungatito kernel-bg.

Verifica:
- PCC operacional con inner=7: ratio mediano cura (esperado 1.86x preview)
- Lastarria A/B: NEW kernel-bg vs LEGACY (esperado curar gap 7.67x)
- Tupungatito A/B: NEW kernel-bg vs LEGACY (esperado curar gap 8.20x)

Uso:
  git pull --rebase origin main
  python experiments/110_s62_audit_pcc_lastarria_tupungatito.py
"""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import csv, json, statistics
from datetime import datetime
from pathlib import Path

WINDOW_START = datetime(2026, 3, 1)
WINDOW_END = datetime(2026, 5, 19, 23, 59, 59)

CSV_CONS = 'data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv'
CSV_OCR = 'C:/Users/nmend/AppData/Local/Temp/csv_ocr.csv'


def sensor_family(s):
    if 'MODIS' in s: return 'MODIS'
    if '750' in s: return 'VIIRS750'
    if 'VIIRS' in s: return 'VIIRS375'
    return s


def load_refs(path, vol_csv, types):
    refs = []
    with open(path, encoding='utf-8') as f:
        for row in csv.DictReader(f):
            if row.get('Volcan') != vol_csv: continue
            if row.get('Tipo_Registro') not in types: continue
            try: dt = datetime.strptime(row['Fecha_Satelite_UTC'], '%Y-%m-%d %H:%M:%S')
            except: continue
            if not (WINDOW_START <= dt <= WINDOW_END): continue
            try: vrp = float(row['VRP_MW'])
            except: continue
            refs.append({'dt': dt, 'sensor': row['Sensor'], 'vrp': vrp, 'tipo': row['Tipo_Registro']})
    return refs


def audit(json_path, vol_csv, label):
    if not Path(json_path).exists():
        print(f'\n{label}: {json_path} NO EXISTE — workflow no completó?')
        return
    cons = load_refs(CSV_CONS, vol_csv, ['ALERTA_TERMICA'])
    ocr = load_refs(CSV_OCR, vol_csv, ['ALERTA_TERMICA_OCR'])
    refs = cons + ocr
    if not refs:
        print(f'\n{label}: 0 ALERTAS en window')
        return

    with open(json_path, encoding='utf-8') as f:
        recs = json.load(f).get('records', [])

    ratios = []
    detected = 0
    for r in refs:
        cands = []
        for rec in recs:
            try: rdt = datetime.fromisoformat(rec['datetime_utc'].replace('Z', ''))
            except: continue
            if abs((rdt - r['dt']).total_seconds()) > 900: continue
            if sensor_family(rec.get('sensor', '')) != sensor_family(r['sensor']): continue
            cands.append(rec)
        if not cands: continue
        best = min(cands, key=lambda x: (x.get('primary_cluster') or {}).get('centroid_dist_km', 99))
        pc = best.get('primary_cluster') or {}
        pc_vrp = pc.get('vrp_mw', 0)
        if pc_vrp <= 0: continue
        detected += 1
        if r['vrp'] > 0:
            ratios.append(pc_vrp / r['vrp'])

    print(f'\n=== {label} ===')
    print(f'  ALERTAS window: {len(refs)} ({len(cons)} CONS + {len(ocr)} OCR)')
    print(f'  Detected pc.vrp>0: {detected}/{len(refs)} = {100*detected/len(refs):.0f}%')
    if ratios:
        med = statistics.median(ratios)
        in_range = sum(1 for x in ratios if 0.5 <= x <= 2.0)
        le3 = sum(1 for x in ratios if x <= 3.0)
        print(f'  Ratio pc.vrp / MIROVA: median={med:.2f}x  min={min(ratios):.2f}  max={max(ratios):.2f}')
        print(f'  En rango [0.5, 2.0]: {in_range}/{len(ratios)} ({100*in_range/len(ratios):.0f}%)')
        print(f'  Aceptable ≤3.0x: {le3}/{len(ratios)} ({100*le3/len(ratios):.0f}%)')


def main():
    # Lastarria: A/B NEW vs LEGACY
    audit('data/mirova_equivalent/Lastarria.json', 'Lastarria',
          'Lastarria OPERACIONAL (LEGACY, sin fix)')
    audit('data/_local_kernel_bg_enabled/Lastarria.json', 'Lastarria',
          'Lastarria NEW (con kernel-bg fix)')

    # Tupungatito: A/B NEW vs LEGACY
    audit('data/mirova_equivalent/Tupungatito.json', 'Tupungatito',
          'Tupungatito OPERACIONAL (LEGACY, sin fix)')
    audit('data/_local_kernel_bg_enabled/Tupungatito.json', 'Tupungatito',
          'Tupungatito NEW (con kernel-bg fix)')

    # PCC: solo operacional (cambio inner=7 ya aplicado a TODOS los records reprocesados)
    audit('data/mirova_equivalent/PuyehueCordonCaulle.json', 'Puyehue-Cordon Caulle',
          'PCC OPERACIONAL post-reproc (inner_radius_km=7)')


if __name__ == '__main__':
    main()
```

- [ ] **Step 6.3: Run audit y capturar output**

```bash
python experiments/110_s62_audit_pcc_lastarria_tupungatito.py 2>&1 | tee experiments/110_s62_results.txt
```

Expected sections con números. Si algún archivo no existe: investigar workflow.

- [ ] **Step 6.4: Crear `experiments/110_s62_results.md`**

Llenar con resultados del Step 6.3:

```markdown
# S62 Audit Results

**Fecha**: <hoy>
**Workflows**:
- A/B Lastarria/Tupungatito: run <ID-1>
- PCC reproc operacional: run <ID-2>

## Lastarria

| Métrica | LEGACY (sin fix) | NEW (con fix) | Δ |
|---|---:|---:|---:|
| Recall | <X>/<N> | <Y>/<N> | |
| Ratio mediano | <X>× | <Y>× | <%> |
| En rango [0.5, 2.0] | <X>/<N> | <Y>/<N> | |

[Verdict: ADOPTAR / MIXTO / NO ADOPTAR]

## Tupungatito

[Misma estructura]

## PCC (inner_radius_km=7 vs 20)

| Métrica | inner=20 baseline | inner=7 (post-reproc) | Δ |
|---|---:|---:|---:|
| Recall | <X> | <Y> | |
| Ratio mediano | <X>× | <Y>× | <%> |
| En rango [0.5, 2.0] | <X>/<N> | <Y>/<N> | |

Baseline inner=20: del audit S61 — ratio mediano 3.51×.

[Verdict: MANTENER inner=7 / REVERTIR si recall colapsa]
```

- [ ] **Step 6.5: Commit audit**

```bash
git add experiments/110_s62_audit_pcc_lastarria_tupungatito.py experiments/110_s62_results.md
git commit -m "S62 Task 6: audit results post-reproc PCC + Lastarria/Tupungatito A/B"
```

---

## Task 7: (CONDICIONAL) Adoptar Lastarria/Tupungatito en `volcanoes.yaml`

**Files:**
- Modify: `volcanoes.yaml` (bloques Lastarria, Tupungatito)

**Pre-condición**: Task 6 audit muestra para cada vol:
- Recall NEW ≥ LEGACY (sin regresión)
- Ratio mediano NEW < LEGACY (mejora)

**Si NO valida**: saltar este Task. Lastarria/Tupungatito quedan en `local_kernel_bg: false`.

- [ ] **Step 7.1: Si Lastarria valida — activar flag**

Localizar bloque `name: Lastarria` en `volcanoes.yaml`. Buscar `local_kernel_bg:` o agregar si no existe.

Cambiar a:
```yaml
  # S62 ADOPCIÓN: A/B kernel-bg cura gap LEGACY 7.67× → NEW <Y>× sobre <N> ALERTAS
  # (CONS+OCR window 80d). Patrón térmico ΔT ~12K + ring desierto Atacama frío.
  # Coppola 2024 L1129 kernel local cura magnitud.
  local_kernel_bg: true
```

- [ ] **Step 7.2: Si Tupungatito valida — activar flag**

Igual en bloque Tupungatito:
```yaml
  # S62 ADOPCIÓN: A/B kernel-bg cura gap LEGACY 8.20× → NEW <Y>×. Reverte
  # decisión S59 que asumía "ring glaciar empeoraría" — investigación H S61
  # mostró que el cluster cráter tiene pixels con vecinos roca (no glaciar
  # pure), kernel local ayuda.
  local_kernel_bg: true
```

- [ ] **Step 7.3: Tests pipeline siguen pasando**

```bash
python -m pytest tests/ -x -q
```

Expected: `335 passed, 16 skipped`.

- [ ] **Step 7.4: Commit**

```bash
git add volcanoes.yaml
git commit -m "S62 Task 7: adoptar local_kernel_bg=true para <vols validados>"
```

---

## Task 8: PR cierre S62 + verificación

**Files:**
- ninguno (operación git)

- [ ] **Step 8.1: Push + PR cierre**

```bash
git push
gh pr create --title "S62 cierre: adopción Lastarria/Tupungatito + audit PCC inner=7" --body "$(cat <<'EOF'
## Summary
- Task 1-3: cambios S62 mergeados (PCC inner_radius, workflows A/B)
- Task 5: workflows disparados
- Task 6: audit results en `experiments/110_s62_results.md`
- Task 7: adopción Lastarria/Tupungatito (si validaron)

## Resultados Lastarria
[pegar de Task 6.4]

## Resultados Tupungatito
[pegar de Task 6.4]

## Resultados PCC inner=7
[pegar de Task 6.4]

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 8.2: Merge**

```bash
gh pr merge <PR#> --squash --delete-branch -R MendozaVolcanic/VRP-chile
```

- [ ] **Step 8.3: Verificación post-deploy NRT**

Esperar próximo cron NRT (cada 2h). Verificar Lastarria/Tupungatito/PCC procesan OK con nuevos flags.

```bash
# Próximo cron NRT
gh run list --workflow=nrt.yml -R MendozaVolcanic/VRP-chile --limit 3 --json status,conclusion,createdAt

# Verificar 3 vols procesados OK
gh run view <NRT-run-id> -R MendozaVolcanic/VRP-chile --json jobs | python -c "
import json, sys
d = json.load(sys.stdin)
for j in d['jobs']:
    if 'Lastarria' in j['name'] or 'Tupungatito' in j['name'] or 'PuyehueCordon' in j['name']:
        print(f'{j[\"name\"]}: {j[\"conclusion\"]}')
"
```

Expected: 3 vols `success`.

---

## Task 9: Cierre S62 (HYPOTHESIS_LOG + bloque arranque S63)

**Files:**
- Modify: `docs/HYPOTHESIS_LOG.md` (resoluciones H_S61_LASTARRIA + H_S61_TUPUNGATITO)
- Create: `tasks/BLOQUE_ARRANQUE_S63.md`

- [ ] **Step 9.1: Cerrar hipótesis S61**

En `docs/HYPOTHESIS_LOG.md`, encontrar `H_S61_LASTARRIA_KERNEL_BG_NEEDED` y agregar al final:

```markdown
- **Validación S62**: A/B kernel-bg ratio mediano <X>× → <Y>× sobre <N> ALERTAS (CONS+OCR). Adopción <SÍ/NO>.
```

Mismo para `H_S61_TUPUNGATITO_KERNEL_BG_REVIEW` con datos Task 6.

- [ ] **Step 9.2: Crear bloque arranque S63**

```markdown
# BLOQUE DE ARRANQUE S63 — VRP Chile

## 1. Lectura obligatoria

1. Este doc
2. `tasks/BLOQUE_ARRANQUE_S62.md` — contexto S62
3. `tasks/BLOQUE_ARRANQUE_S61.md` — contexto S61
4. `experiments/110_s62_results.md` — audit S62
5. `docs/HYPOTHESIS_LOG.md` H_S61 + H_S62

## 2. Estado al cierre S62

### Adopciones operacionales acumuladas
- Villarrica + PlanchonPeteroa: kernel-bg true (S61)
- Lastarria/Tupungatito: <true si validó S62 / false si no>
- PCC inner_radius_km: 7 (S62)
- Copahue/Llaima/Lascar/Isluga: false (calibrados)

### Métricas finales S62
- Villarrica: ratio mediano 2.16× (S61)
- PlanchonPeteroa: 2.84×
- PCC: <X>× (post-inner=7)
- Lascar: 1.32× (calibrado)
- Isluga: 1.11× (calibrado)
- Lastarria: <X>× (post-fix si valida)
- Tupungatito: <X>×

## 3. Pendientes S63

### Prioridad MEDIA
1. Chaiten gap 10.28× — investigar (poca data, esperar más ALERTAS)
2. NevadosDeChillan — esperar más actividad MIROVA
3. Llaima/Copahue — esperar más data (poca actividad)

### Prioridad BAJA — Refinamientos
4. kernel_size=5 vs 3 (subagent S61 sugirió como mejora calibración Villarrica
   gap residual 42% sobre OSF target). Implementación trivial (5 líneas), test
   sintético antes de A/B.
5. Investigar coords MIROVA per vol más profundamente si surge necesidad

## 4. Errores S62 a no repetir
- Disparar workflow con timeout incorrecto sin verificar duración estimada (S60 lesson)
- Confiar en audit con `record.vrp_mw` (S61 lesson — usar siempre `pc.vrp_mw`)
- Asumir mecanismo físico sin verificar gap empírico (S60 Copahue/Llaima lesson)
```

- [ ] **Step 9.3: Commit cierre**

```bash
git add docs/HYPOTHESIS_LOG.md tasks/BLOQUE_ARRANQUE_S63.md
git commit -m "S62 cierre: hipótesis resueltas + bloque arranque S63"
git push
```

---

## Plan de contingencia

### Si A/B Lastarria/Tupungatito NO valida (ratio NEW ≥ LEGACY)

1. **NO modificar `volcanoes.yaml`** (mantener `local_kernel_bg: false`).
2. Documentar refutación en HYPOTHESIS_LOG (`H_S61_LASTARRIA_KERNEL_BG_NEEDED` → REFUTADA).
3. Investigar otros mecanismos S63: kernel_size=5, Test 1 threshold per-vol.
4. NO disparar reproc operacional Lastarria/Tupungatito.

### Si PCC inner=7 colapsa recall (>40% caída)

1. **Revertir** a `inner_radius_km: 10` o `12` en `volcanoes.yaml` Task 1.
2. Re-disparar reproc PCC operacional con valor intermedio.
3. Documentar trade-off recall vs precision en HYPOTHESIS_LOG.

### Si algún workflow falla (timeout, NASA error)

1. Verificar logs: `gh run view <ID> --log-failed`
2. Si NASA timeout intermitente (3/45 vols pattern conocido): retry workflow.
3. Si timeout exceeded: split window (e.g. 2 mitades).

---

## Self-review

**1. Spec coverage**: ✓ Todas las 3 tareas A+B+C del spec inicial:
- A: Task 1 (PCC inner_radius)
- B: Tasks 2, 5 (workflow A/B + dispatch Lastarria/Tupungatito)
- C: Tasks 3, 5 (workflow + dispatch reproc PCC)
- Más Tasks 6-9 para cierre formal.

**2. Placeholders**: ✓ Únicos placeholders intencionales son `<ID-1>`, `<ID-2>`, `<PR#>`, `<X>`, `<Y>`, `<N>` que el engineer reemplaza con valores reales runtime.

**3. Type consistency**: ✓ `local_kernel_bg` (per-vol flag) consistente en Tasks 1, 7. `inner_radius_km` PCC consistente Task 1, 7.

**4. Tests**: ✓ Tests pipeline corren en Tasks 1.3, 7.3. NO se modifica código pipeline (solo YAML), entonces tests existentes alcanzan.

---

Plan complete and saved to `docs/superpowers/plans/2026-05-19-s62-pcc-lastarria-tupungatito.md`.

## Execution options

**1. Subagent-Driven** - dispatcho fresh subagent per task con review. Más overhead, contexto limpio. Ideal para tasks con múltiples archivos.

**2. Inline Execution (recommended)** - ejecutar las 9 tasks en esta misma sesión. Tasks son simples (YAML edits, workflow trigger, audit). Costo bajo, iteración rápida.

¿Cuál preferís?
