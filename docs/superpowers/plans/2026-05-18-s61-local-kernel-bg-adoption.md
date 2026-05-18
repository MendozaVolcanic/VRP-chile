# S61 — Adopción operacional `local_kernel_bg` con validación PlanchónPeteroa

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adoptar `enable_local_kernel_bg: true` en perfil operacional `mirova_equivalent.yaml` con flag per-vol ajustado correctamente, después de validar A/B en PlanchónPeteroa (segundo vol que también necesita el fix por mecanismo distinto: glaciar heterogéneo, no lago cálido).

**Architecture:** Confirmar empíricamente que PlanchónPeteroa con `local_kernel_bg=true` cura el ratio mediano LEGACY 15.03× igual que lo hizo en Villarrica (33×→2.16×). Si valida, activar flag profile operacional sabiendo que solo afecta vols con `local_kernel_bg: true` en `volcanoes.yaml`. Revertir Copahue/Llaima a `false` antes de activar para evitar regresión en vols ya calibrados.

**Tech Stack:** GitHub Actions (workflow_dispatch), Python 3.11 pipeline, YAML configs, JSON output, gh CLI.

---

## File Structure

| Archivo | Responsabilidad | Operación |
|---|---|---|
| `.github/workflows/reproc-ab-local-kernel-bg-pp.yml` | Workflow A/B reproc PlanchónPeteroa | **Crear** |
| `volcanoes.yaml` | Per-vol flags `local_kernel_bg` | **Modificar** líneas 124 (Copahue), 263 (Llaima) |
| `pipeline/profiles/mirova_equivalent.yaml` | Profile flag operacional | **Modificar** línea 121 (post-A) |
| `experiments/105_s61_audit_planchon_kernel_bg.py` | Audit script PlanchónPeteroa pre/post fix | **Crear** |
| `experiments/105_s61_audit_planchon_results.md` | Resultado A/B PlanchónPeteroa | **Crear** |
| `experiments/106_s61_dashboard_validation.md` | Verificación frontend post-adopción | **Crear** |
| `docs/HYPOTHESIS_LOG.md` | Append H_S61_PLANCHON_KERNEL_BG | **Modificar** |
| `~memory/MEMORY.md` | Update S61 entry | **Modificar** |
| `tasks/BLOQUE_ARRANQUE_S62.md` | Bloque arranque siguiente sesión | **Crear** |

---

## Task 1: Crear workflow A/B para PlanchónPeteroa

**Files:**
- Create: `.github/workflows/reproc-ab-local-kernel-bg-pp.yml`

**Razón**: el workflow `reproc-ab-local-kernel-bg.yml` está hardcoded a `--volcano Villarrica`. Necesitamos uno equivalente para PlanchónPeteroa (no parametrizar el original porque queremos historial limpio por vol).

- [ ] **Step 1.1: Crear workflow PlanchónPeteroa**

Contenido completo del archivo:

```yaml
name: A/B reproceso local kernel background — PlanchonPeteroa (S61)

# S61: Validar enable_local_kernel_bg=true en PlanchonPeteroa.
# Audit S60 mostró ratio mediano LEGACY/MIROVA 15.03x sobre 18 ALERTAS
# window 04-16/05-15. Hipotesis: glaciar heterogeneo en ring 5-25km infla
# background median. Kernel 3x3 local debe curar.

on:
  workflow_dispatch:
    inputs:
      start:
        description: "Start date YYYY-MM-DD"
        required: true
        default: "2026-04-16"
      end:
        description: "End date YYYY-MM-DD (inclusive)"
        required: true
        default: "2026-05-15"

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

      - name: Run reprocess — _local_kernel_bg_enabled / PlanchonPeteroa
        env:
          EARTHDATA_USERNAME: ${{ secrets.EARTHDATA_USERNAME }}
          EARTHDATA_PASSWORD: ${{ secrets.EARTHDATA_PASSWORD }}
        timeout-minutes: 280
        run: |
          python scripts/run_pipeline.py \
            --profile _local_kernel_bg_enabled \
            --volcano PlanchonPeteroa \
            --start ${{ github.event.inputs.start }} \
            --end ${{ github.event.inputs.end }} \
            --overwrite

      - name: Commit reprocessed A/B data
        run: |
          set +e
          git config user.name  "vrp-bot"
          git config user.email "vrp-bot@github-actions"
          git add "data/_local_kernel_bg_enabled/PlanchonPeteroa.json" 2>/dev/null
          git diff --staged --quiet && { echo "No changes to commit"; exit 0; }
          git commit -m "S61 A/B local kernel bg — PlanchonPeteroa ${{ github.event.inputs.start }}→${{ github.event.inputs.end }}"
          for attempt in 1 2 3 4 5; do
            git pull --rebase -X theirs origin main && git push && exit 0
            echo "push attempt $attempt failed, sleeping $((attempt * 10))s"
            git rebase --abort 2>/dev/null
            sleep $((attempt * 10))
          done
          echo "all push attempts failed"; exit 1
```

- [ ] **Step 1.2: Commit workflow**

```bash
git add .github/workflows/reproc-ab-local-kernel-bg-pp.yml
git commit -m "S61: workflow A/B local_kernel_bg para PlanchonPeteroa"
```

- [ ] **Step 1.3: Push + PR + merge**

```bash
git push -u origin <current-branch>
gh pr create --title "S61: workflow A/B local_kernel_bg PlanchonPeteroa" --body "Workflow nuevo para reproc A/B PlanchonPeteroa, mismo patrón que reproc-ab-local-kernel-bg.yml Villarrica."
gh pr merge <PR#> --squash --delete-branch -R MendozaVolcanic/VRP-chile
```

- [ ] **Step 1.4: Verificar workflow disponible en main**

```bash
gh workflow list -R MendozaVolcanic/VRP-chile | grep -i planchon
```

Expected: línea conteniendo `reproc-ab-local-kernel-bg-pp.yml`.

---

## Task 2: Disparar reproc A/B PlanchónPeteroa

**Files:**
- Modify: ninguno (solo trigger remoto)

- [ ] **Step 2.1: Trigger workflow con window completo**

```bash
gh workflow run reproc-ab-local-kernel-bg-pp.yml \
  -f start=2026-02-20 \
  -f end=2026-05-15 \
  -R MendozaVolcanic/VRP-chile
```

- [ ] **Step 2.2: Anotar run ID y URL**

```bash
gh run list --workflow=reproc-ab-local-kernel-bg-pp.yml -R MendozaVolcanic/VRP-chile --limit 1 --json databaseId,url
```

Anotar `databaseId` y `url` para monitoreo. Guardar en `tasks/S61_workflow_status.md`:

```
## S61 PlanchonPeteroa A/B
- Run ID: <ID>
- URL: <URL>
- Triggered: <fecha hora UTC>
- ETA: triggered_at + 3h
- Window: 2026-02-20 → 2026-05-15
```

- [ ] **Step 2.3: Esperar terminación**

Worker debe pausar ~3h y verificar al final:

```bash
gh run view <ID> -R MendozaVolcanic/VRP-chile --json status,conclusion
```

Expected al cabo de ~3h: `{"status":"completed","conclusion":"success"}`.

Si `conclusion=="failure"`: investigar logs (`gh run view <ID> --log`). Si timeout: revisar duración exacta y considerar split window. Si error pipeline: rebajar window o investigar antes de seguir.

---

## Task 3: Audit pre/post fix PlanchónPeteroa

**Files:**
- Create: `experiments/105_s61_audit_planchon_kernel_bg.py`
- Create: `experiments/105_s61_audit_planchon_results.md`

- [ ] **Step 3.1: Pull main para tener data NEW**

```bash
git pull --rebase origin main
ls -la data/_local_kernel_bg_enabled/PlanchonPeteroa.json
```

Expected: archivo existe, modificado <1h ago.

- [ ] **Step 3.2: Escribir audit script**

Crear `experiments/105_s61_audit_planchon_kernel_bg.py`:

```python
"""S61 Audit — PlanchonPeteroa LEGACY vs NEW kernel-bg.

Compara ratio MIROVA/nuestro sobre window 02-20/05-15 ALERTAS reales.
"""
import json, csv, statistics
from datetime import datetime
from pathlib import Path

VOL = 'PlanchonPeteroa'
WINDOW_START = datetime(2026,2,20)
WINDOW_END = datetime(2026,5,15,23,59,59)

CSV = 'data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv'
NEW = f'data/_local_kernel_bg_enabled/{VOL}.json'
LEGACY = f'data/mirova_equivalent/{VOL}.json'


def load_mirova_refs():
    refs = []
    with open(CSV, encoding='utf-8') as f:
        for row in csv.DictReader(f):
            if row['Volcan'] != VOL: continue
            if row['Tipo_Registro'] not in ('ALERTA_TERMICA','FALSO_POSITIVO'): continue
            try: dt = datetime.strptime(row['Fecha_Satelite_UTC'],'%Y-%m-%d %H:%M:%S')
            except: continue
            if not (WINDOW_START <= dt <= WINDOW_END): continue
            try: vrp = float(row['VRP_MW'])
            except: continue
            refs.append({'dt':dt,'sensor':row['Sensor'],'vrp':vrp,
                        'dist':float(row['Distancia_km']),'tipo':row['Tipo_Registro']})
    return refs


def sensor_family(s):
    if 'MODIS' in s: return 'MODIS'
    if '750' in s: return 'VIIRS750'
    if 'VIIRS' in s: return 'VIIRS375'
    return s


def match_records(refs, recs_path, label):
    with open(recs_path, encoding='utf-8') as f:
        recs = json.load(f).get('records',[])
    results = []
    for r in refs:
        candidates = []
        for rec in recs:
            try: rec_dt = datetime.fromisoformat(rec['datetime_utc'].replace('Z',''))
            except: continue
            if abs((rec_dt - r['dt']).total_seconds()) > 900: continue
            if sensor_family(rec.get('sensor','')) != sensor_family(r['sensor']): continue
            candidates.append(rec)
        if candidates:
            best = max(candidates, key=lambda x: x.get('vrp_mw') or 0)
            vrp_ours = best.get('vrp_mw') or 0
            dist_ours = best.get('final_hotspot_dist_km') or best.get('hotspot_dist_km') or -1
            ratio = vrp_ours/r['vrp'] if r['vrp']>0 else 0
            results.append({**r, 'matched':True, 'our_vrp':vrp_ours, 'our_dist':dist_ours, 'ratio':ratio})
        else:
            results.append({**r, 'matched':False, 'our_vrp':0, 'our_dist':-1, 'ratio':0})
    return results


def summarize(results, label):
    alerta = [r for r in results if r['tipo']=='ALERTA_TERMICA']
    alerta_matched = [r for r in alerta if r['matched'] and r['our_vrp']>0]
    ratios = [r['ratio'] for r in alerta_matched]
    print(f'\n=== {label} ===')
    print(f'ALERTA recall: {len(alerta_matched)}/{len(alerta)}')
    if ratios:
        print(f'Ratio ALERTAS: median={statistics.median(ratios):.2f}x  min={min(ratios):.2f}  max={max(ratios):.2f}')
        in_range = sum(1 for r in ratios if 0.5 <= r <= 2.0)
        print(f'Ratios en rango tolerable [0.5, 2.0]: {in_range}/{len(ratios)}')


if __name__ == '__main__':
    refs = load_mirova_refs()
    print(f'PlanchonPeteroa MIROVA refs window: {len(refs)}')
    legacy_res = match_records(refs, LEGACY, 'LEGACY median-ring')
    new_res = match_records(refs, NEW, 'NEW kernel-bg')

    summarize(legacy_res, 'LEGACY median-ring')
    summarize(new_res, 'NEW kernel-bg')

    # Side-by-side compare
    print('\n=== Side-by-side per ALERTA ===')
    print(f'{"DateTime":20} {"MIROVA":>7} {"LEGACY":>15} {"NEW":>15}')
    for l, n in zip(legacy_res, new_res):
        if l['tipo'] != 'ALERTA_TERMICA': continue
        l_str = f'{l["our_vrp"]:.2f}({l["ratio"]:.1f}x)' if l['matched'] else 'NO MATCH'
        n_str = f'{n["our_vrp"]:.2f}({n["ratio"]:.1f}x)' if n['matched'] else 'NO MATCH'
        print(f'{l["dt"]!s:20} {l["vrp"]:>7.2f} {l_str:>15} {n_str:>15}')
```

- [ ] **Step 3.3: Run audit y capturar output**

```bash
python experiments/105_s61_audit_planchon_kernel_bg.py 2>&1 | tee experiments/105_s61_audit_planchon_results.txt
```

Expected output:
- `ALERTA recall NEW` ≥ `ALERTA recall LEGACY` (sin regresión).
- `Ratio ALERTAS NEW median` < `LEGACY median` (mejora calibración).
- Ratios NEW idealmente en rango [0.5, 2.0] como Villarrica post-fix.

- [ ] **Step 3.4: Escribir markdown results**

Crear `experiments/105_s61_audit_planchon_results.md`:

```markdown
# S61 Audit PlanchonPeteroa A/B local_kernel_bg

**Fecha**: <hoy>
**Workflow**: run <ID>
**Window**: 2026-02-20 → 2026-05-15

## Resultados

[Pegar output del script aquí]

## Verdict

| Métrica | LEGACY | NEW | Δ |
|---|---:|---:|---:|
| ALERTA recall | <X>/<N> | <Y>/<N> | <%> |
| Ratio mediano ALERTAS | <X>× | <Y>× | <%> |
| Ratios en rango [0.5, 2.0] | <X>/<N> | <Y>/<N> | — |

[Conclusión: fix valida / fix neutral / fix regresiona]

## Decisión adopción

Si recall NEW ≥ LEGACY Y ratio mediano NEW < LEGACY:
- ✅ Adoptar fix profile-wide (Task 5)
- Mantener PlanchonPeteroa en `local_kernel_bg: true`

Si recall NEW < LEGACY:
- ❌ NO adoptar para PlanchonPeteroa
- Revertir `volcanoes.yaml`: PlanchonPeteroa → false
- Mantener fix solo Villarrica
```

- [ ] **Step 3.5: Commit audit**

```bash
git add experiments/105_s61_audit_planchon_kernel_bg.py experiments/105_s61_audit_planchon_results.md
git commit -m "S61 audit PlanchonPeteroa A/B local_kernel_bg"
```

---

## Task 4: Revertir flags Copahue/Llaima en `volcanoes.yaml`

**Files:**
- Modify: `volcanoes.yaml:124` (Copahue), `volcanoes.yaml:263` (Llaima)

**Razón**: audit S60 offline + lagos físicos confirma que Copahue (ratio LEGACY/MIROVA 1.14×) y Llaima (1.01×) están calibrados. Aplicar fix los empeoraría.

- [ ] **Step 4.1: Revertir Copahue**

Modificar `volcanoes.yaml` líneas alrededor de 124. Cambiar:

```yaml
  local_kernel_bg: true
```

a:

```yaml
  # S61: revertido false tras audit S60 (ratio LEGACY/MIROVA 1.14x = calibrado).
  # Lago Caviahue tibio aporta contaminación moderada pero ya alineada con MIROVA NRT.
  # Aplicar fix bajaría magnitudes ya correctas (riesgo under-detection).
  local_kernel_bg: false
```

Verificar con grep:

```bash
grep -A2 "name: Copahue" volcanoes.yaml | head -30 | grep -A1 local_kernel
```

Expected: `local_kernel_bg: false`.

- [ ] **Step 4.2: Revertir Llaima**

Modificar `volcanoes.yaml` líneas alrededor de 263. Cambiar:

```yaml
  local_kernel_bg: true
```

a:

```yaml
  # S61: revertido false tras audit S60 (ratio LEGACY/MIROVA 1.01x = calibradísimo).
  # Lago Conguillío frío similar al terreno andino → no contamina ring. Fix dañino.
  local_kernel_bg: false
```

Verificar:

```bash
grep -A2 "name: Llaima" volcanoes.yaml | grep -A1 local_kernel
```

Expected: `local_kernel_bg: false`.

- [ ] **Step 4.3: Tests pipeline siguen pasando**

```bash
python -m pytest tests/ -x 2>&1 | tail -5
```

Expected: `335 passed / 16 skipped` (sin regresión por cambio yaml).

- [ ] **Step 4.4: Commit**

```bash
git add volcanoes.yaml
git commit -m "S61: revertir local_kernel_bg false para Copahue y Llaima (calibrados)"
```

---

## Task 5: Activar profile flag operacional (CONDICIONAL — solo si Task 3 valida)

**Files:**
- Modify: `pipeline/profiles/mirova_equivalent.yaml:121`

**Pre-condición**: Task 3.4 verdict = "fix valida" (recall sin regresión + ratio mediano NEW < LEGACY).

**Si NO valida**: saltar a Task 6 con `enable_local_kernel_bg` quedando en `false`. PlanchonPeteroa también a `false` en yaml.

- [ ] **Step 5.1: Cambiar profile flag**

Modificar `pipeline/profiles/mirova_equivalent.yaml` alrededor de línea 121. Cambiar:

```yaml
  enable_local_kernel_bg: false             # S58 NO ADOPTADO operacional aun
```

a:

```yaml
  # S61 ADOPTED — kernel local 3x3 (Coppola 2024 L1129) para vols con
  # local_kernel_bg: true en volcanoes.yaml.
  # Validación A/B:
  # - Villarrica window 02-20/05-15: ratio mediano LEGACY 33x → NEW 2.16x (5 ALERTAS)
  # - PlanchonPeteroa window 02-20/05-15: ratio mediano LEGACY 15x → NEW <Y>x (18 ALERTAS)
  # Per-vol opt-in: Villarrica + PlanchonPeteroa true; Copahue/Llaima/Tupungatito false.
  enable_local_kernel_bg: true
```

- [ ] **Step 5.2: Tests siguen pasando**

```bash
python -m pytest tests/ -x 2>&1 | tail -5
```

Expected: `335 passed / 16 skipped`.

- [ ] **Step 5.3: Smoke test pipeline local (1 día Villarrica)**

```bash
python scripts/run_pipeline.py --profile mirova_equivalent --volcano Villarrica \
  --start 2026-05-15 --end 2026-05-15 --dry-run 2>&1 | tail -10
```

Expected: termina sin error, logs muestran "local_kernel_bg=true aplicado".

Si falla por flag no leído: verificar `pipeline/vrp_regimes.py:compute_local_background()` lee el flag correcto.

- [ ] **Step 5.4: Commit adopción**

```bash
git add pipeline/profiles/mirova_equivalent.yaml
git commit -m "S61 ADOPT: enable_local_kernel_bg=true en mirova_equivalent operacional"
```

---

## Task 6: PR + merge cierre S61

**Files:**
- ninguno (operación git)

- [ ] **Step 6.1: Push branch**

```bash
git push
```

- [ ] **Step 6.2: Crear PR cierre S61**

```bash
gh pr create --title "S61 ADOPT local_kernel_bg + revertir Copahue/Llaima" --body "$(cat <<'EOF'
## Summary
- **Task 1-3**: workflow A/B PlanchonPeteroa + audit valida fix sobre 18 ALERTAS.
  - Recall: NEW <X>/18 vs LEGACY <Y>/18
  - Ratio mediano ALERTAS: NEW <Z>x vs LEGACY 15.03x
- **Task 4**: revertir Copahue y Llaima a local_kernel_bg=false (calibrados, fix dañino).
- **Task 5**: activar enable_local_kernel_bg=true en mirova_equivalent.yaml operacional.

## Per-vol flag estado final
| Vol | local_kernel_bg | Razón |
|---|---|---|
| Villarrica | true | Audit S60 5 ALERTAS: ratio 33x → 2.16x |
| PlanchonPeteroa | true | Audit S61 18 ALERTAS: ratio 15x → <Z>x |
| Copahue | false | Calibrado (1.14x), fix dañino |
| Llaima | false | Calibrado (1.01x), fix dañino |
| Tupungatito | false | Ring frío glaciar (excluido S59) |

## Próximos ciclos NRT
Cron cada 2h aplicará automáticamente el nuevo comportamiento para Villarrica y
PlanchonPeteroa. Monitorear próximos 2-3 ciclos (Task 7).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 6.3: Merge tras CI verde**

```bash
gh pr view <PR#> -R MendozaVolcanic/VRP-chile --json statusCheckRollup
# Verificar checks ok, después:
gh pr merge <PR#> --squash --delete-branch -R MendozaVolcanic/VRP-chile
```

---

## Task 7: Verificación post-deploy (próximos 2-3 ciclos cron NRT)

**Files:**
- Create: `experiments/106_s61_post_deploy_verification.md`

**Pre-condición**: Task 5 ejecutado (enable_local_kernel_bg=true en main).

- [ ] **Step 7.1: Esperar próximo ciclo cron NRT**

Cron `.github/workflows/nrt.yml` corre cada 2h. Esperar primer ciclo post-merge.

```bash
gh run list --workflow=nrt.yml -R MendozaVolcanic/VRP-chile --limit 3 --json databaseId,createdAt,conclusion
```

- [ ] **Step 7.2: Verificar Villarrica y PlanchonPeteroa procesaron OK**

```bash
gh run view <run-id> --log -R MendozaVolcanic/VRP-chile 2>&1 | grep -A2 "Villarrica\|PlanchonPeteroa" | head -30
```

Expected: ambos vols completan sin error. Records nuevos commiteados a `data/mirova_equivalent/`.

- [ ] **Step 7.3: Comparar magnitudes post-deploy vs últimas pre-deploy**

```bash
python -c "
import json
from datetime import datetime
for v in ['Villarrica','PlanchonPeteroa']:
    with open(f'data/mirova_equivalent/{v}.json') as f:
        recs = json.load(f).get('records',[])
    # últimos 10
    sorted_recs = sorted(recs, key=lambda r: r.get('datetime_utc',''), reverse=True)[:10]
    print(f'\\n=== {v} últimos 10 ===')
    for r in sorted_recs:
        if (r.get('vrp_mw') or 0) > 0:
            dist = r.get('final_hotspot_dist_km') or 99
            print(f'  {r[\"datetime_utc\"][:19]} {r[\"sensor\"]:15} vrp={r[\"vrp_mw\"]:.2f} dist={dist:.2f}')
"
```

Expected: magnitudes Villarrica/PlanchonPeteroa coherentes (<5 MW summit típicamente, no outliers extremos 100+ MW como pre-fix).

- [ ] **Step 7.4: Cross-check con dashboard GitHub Pages**

Abrir https://mendozavolcanic.github.io/VRP-chile/ y navegar a Villarrica + PlanchónPeteroa.
Verificar:
- Detecciones recientes visibles (no vacío)
- Magnitudes coherentes con histórico previo (no salto brusco x10 ni a 0)
- Mapa muestra hotspot en cráter (no Salar lejano)

Si dashboard muestra anomalías visuales:
- Caso A (magnitudes a 0): fix demasiado agresivo, revertir Task 5.
- Caso B (vacío total): bug pipeline, investigar.
- Caso C (magnitudes saltadas): documentar y validar contra MIROVA web.

- [ ] **Step 7.5: Escribir verification report**

Crear `experiments/106_s61_post_deploy_verification.md`:

```markdown
# S61 Post-deploy verification

**Fecha**: <hoy>
**Ciclos NRT verificados**: <N runs>

## Villarrica
- Records nuevos: <N>
- Magnitud mediana últimos 10: <X> MW
- Dashboard OK: yes/no

## PlanchonPeteroa
- Records nuevos: <N>
- Magnitud mediana últimos 10: <X> MW
- Dashboard OK: yes/no

## Verdict
[adopción estable / regresión detectada / pendiente más ciclos]
```

- [ ] **Step 7.6: Commit verification**

```bash
git add experiments/106_s61_post_deploy_verification.md
git commit -m "S61: post-deploy verification próximos ciclos NRT"
```

---

## Task 8: Cierre S61

**Files:**
- Modify: `docs/HYPOTHESIS_LOG.md` (append H_S61_PLANCHON_KERNEL_BG)
- Modify: `~memory/MEMORY.md` (entry S61)
- Create: `tasks/BLOQUE_ARRANQUE_S62.md`

- [ ] **Step 8.1: Append hipótesis S61**

Insertar al inicio de `docs/HYPOTHESIS_LOG.md` (antes de `## H_S60_KERNEL_BG_HELPS_MIROVA_DAYS`):

```markdown
## H_S61_PLANCHON_KERNEL_BG — Fix kernel-bg también necesario en PlanchonPeteroa (glaciar heterogéneo)

- **Formulada**: S61 (<fecha>) tras audit C y descubrimiento error S60 (scraper sí cubre PlanchonPeteroa como 'PlanchonPeteroa' sin guión).
- **Hipótesis**: el ratio LEGACY/MIROVA 15.03× en PlanchonPeteroa NO es por lago cálido (no hay lago grande en ring), sino por heterogeneidad glaciar en el ring 5-25km. Kernel local 3×3 cura igual.
- **Evidencia a favor**:
  - 18 ALERTAS window 02-20/05-15 con LEGACY ratio mediano 15.03× (min 0.23, max 130×)
  - Agente lagos confirmó: complejo glaciar grande, sin lago contaminante
  - Fix kernel mecánicamente actúa contra heterogeneidad del background, no requiere lago específico
  - Audit A/B Task 3: NEW recall <X>/18, ratio mediano <Y>× (vs LEGACY 15.03×)
- **Estado**: <CONFIRMADA o REFUTADA según Task 3 result>
- **Resolución**: adoptado en `mirova_equivalent.yaml` con per-vol flag PlanchonPeteroa=true (Task 5).

---
```

- [ ] **Step 8.2: Update MEMORY.md**

Insertar al inicio de `~memory/MEMORY.md` (antes de S60 entry):

```markdown
## S61 (<fecha>) — Adopción operacional local_kernel_bg + revertir Copahue/Llaima

**BLOQUE ARRANQUE S62**: `tasks/BLOQUE_ARRANQUE_S62.md`.

### Hallazgos S61
- Audit A/B PlanchonPeteroa 18 ALERTAS window 02-20/05-15: ratio mediano LEGACY 15.03× → NEW <Y>×.
- Adoptado `enable_local_kernel_bg: true` en `mirova_equivalent.yaml` operacional.
- Per-vol final: Villarrica + PlanchonPeteroa true; Copahue/Llaima/Tupungatito false.
- Mecanismo PlanchonPeteroa distinto de Villarrica: glaciar heterogéneo (no lago).

### Estado tests: 335 passed / 16 skipped.

---
```

- [ ] **Step 8.3: Crear BLOQUE_ARRANQUE_S62.md**

```markdown
# BLOQUE DE ARRANQUE S62 — VRP Chile

## 1. Lectura obligatoria S62

1. **Este doc** — 3 min
2. **`tasks/BLOQUE_ARRANQUE_S61.md`** — contexto S61
3. **`tasks/BLOQUE_ARRANQUE_S60.md`** — contexto histórico maratón
4. **`experiments/105_s61_audit_planchon_results.md`** — resultado A/B
5. **`experiments/106_s61_post_deploy_verification.md`** — verificación post-deploy
6. **`pipeline/profiles/mirova_equivalent.yaml`** — confirmar flags actuales

## 2. Estado al cierre S61

### Adopción operacional
- `enable_local_kernel_bg: true` en `mirova_equivalent.yaml`
- Per-vol flags: Villarrica + PlanchonPeteroa true; resto false
- Cron NRT cada 2h aplica automáticamente

### Métricas finales
- Villarrica audit C: ratio mediano LEGACY 33× → NEW 2.16× sobre 5 ALERTAS
- PlanchonPeteroa audit S61: ratio mediano LEGACY 15.03× → NEW <Y>×
- Tests: 335 passed / 16 skipped

## 3. Pendientes S62

### Prioridad MEDIA
1. Monitorear próximos 5-10 ciclos cron NRT (extensión Task 7 S61)
2. Refinamientos kernel (si hay tiempo y datos justifican):
   - `kernel_size=5` (25 vecinos) — más estabilidad
   - Percentile `p25` del kernel — robusto outliers
3. Cross-check con MIROVA web casos paradigmáticos S58-S61

### Prioridad BAJA
4. Investigar gap recall 53% Villarrica (FPs MIROVA daytime no procesables — decisión MIR-nocturno)
5. Evaluar agregar otros vols Tier A al opt-in si scraper expande cobertura

## 4. Errores S61 a no repetir
- Buscar nombre vol en CSV con TODAS las variantes (con/sin guión, con/sin tilde) — S60 perdió PlanchónPeteroa
- Verificar workflow timeout vs duración esperada antes de disparar (regla S60)
- Comparar vs MIROVA CSV NRT window-aligned, no OSF agregado

## 5. Estado git
- Último PR mergeado S61: <PR#>
- Main al día con todas las adopciones
```

- [ ] **Step 8.4: Commit cierre**

```bash
git add docs/HYPOTHESIS_LOG.md ~memory/MEMORY.md tasks/BLOQUE_ARRANQUE_S62.md
# Nota: ~memory/MEMORY.md está fuera de repo, NO se commitea. Solo HYPOTHESIS_LOG + BLOQUE.
git restore --staged ~memory/MEMORY.md 2>/dev/null || true
git add docs/HYPOTHESIS_LOG.md tasks/BLOQUE_ARRANQUE_S62.md
git commit -m "S61 CIERRE: hipótesis + bloque arranque S62"
```

- [ ] **Step 8.5: Push + PR + merge cierre**

```bash
git push
gh pr create --title "S61 CIERRE: adopción + post-deploy + bloque S62" --body "Cierre formal sesión S61: hipótesis persistida, bloque arranque S62 con pendientes."
gh pr merge <PR#> --squash --delete-branch -R MendozaVolcanic/VRP-chile
```

---

## Plan de contingencia: ¿qué si Task 3 NO valida?

Si audit PlanchonPeteroa muestra:
- Recall NEW < LEGACY (regresión)
- O ratio mediano NEW > LEGACY (empeora)

Entonces:
1. **Saltar Task 5** (NO adoptar profile flag global)
2. **Cambiar volcanoes.yaml**: PlanchonPeteroa de `local_kernel_bg: true` a `false`.
   Resultado: solo Villarrica con flag true, pero como el profile flag queda en false,
   ningún vol recibe el fix operacional. Villarrica sigue funcionando con LEGACY.
3. **Considerar fix Villarrica-specific**: rama larga si Nicolás quiere mantener el
   beneficio Villarrica sin profile flag. Implementación: hardcode `local_kernel_bg`
   check en `pipeline/process_viirs.py` para Villarrica.
4. **Investigar S62**: por qué fix funciona Villarrica pero no PlanchonPeteroa.
   Hipótesis: heterogeneidad glaciar requiere kernel diferente (size=5, p25).

---

## Self-review

**Spec coverage**: ✓ Todas las tareas A-E del scope inicial cubiertas:
- A: Tasks 1-3 (workflow + reproc + audit)
- B: Task 4 (revert Copahue/Llaima)
- C: Task 5 (profile flag, condicional)
- D: Task 7 (post-deploy verification)
- E: Task 7.4 (dashboard validation, parte de D)

**Placeholders**: ✓ Todos los paths son exactos. Únicos placeholders intencionales son:
- `<ID>`, `<URL>`, `<PR#>` para identificadores remotos no predecibles
- `<X>`, `<Y>`, `<Z>` para métricas que Task 3 produce (engineering data)
- `<fecha>` para fecha real de ejecución
Estos son legítimos: el engineer los completa con el output real cuando ejecuta.

**Type consistency**: ✓ `local_kernel_bg` (per-vol flag) y `enable_local_kernel_bg` (profile flag) usados consistentemente. Workflow file names matchean (`reproc-ab-local-kernel-bg-pp.yml`).

**Conflictos potenciales**: Task 5 (profile flag) tiene pre-condición sobre Task 3. Plan de contingencia explícito si no valida.

---

Plan complete and saved to `docs/superpowers/plans/2026-05-18-s61-local-kernel-bg-adoption.md`.

## Execution options

**1. Subagent-Driven (recommended)** - dispatcho fresh subagent per task, review entre tasks, iteración rápida especialmente para Task 1 (workflow), Task 3 (audit) y Task 7 (verification).

**2. Inline Execution** - ejecutar las 8 tasks en esta misma sesión usando executing-plans, con checkpoints en Tasks 3 (post-audit) y 5 (adopción).
