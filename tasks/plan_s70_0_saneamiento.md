# Plan S70-0: Bloque cero de saneamiento

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolver 3 pre-condiciones críticas detectadas en auditoría S70 (NRT cron al 5% éxito, hallazgo "TIF ≠ VRP sumable" no documentado, CSV OCR fuera de repo) antes de arrancar R2 retroactivo Chaiten.

**Architecture:** Plan de diagnóstico + saneamiento. Cada tarea produce evidencia, documentación o fix mínimo — NO toca código de `pipeline/`. Las tareas T1-T2 son independientes y pueden ejecutarse en paralelo. T3 y T4 dependen del verdict de T2. T5 es independiente.

**Tech Stack:** Python 3.12 (Anaconda), `rasterio` (lectura TIF), `pandas` (CSV), `gh` CLI (GitHub API + workflows), Git worktrees.

**Worktree:** `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP-Chile-s70\` rama `s70-0-saneamiento`.

**Misión vinculante**: Las 3 preguntas de `docs/MISSION.md`. Este plan cumple porque T1/T5 son "alineación interna no-metodológica" (P3) y T2-T4 "cierra divergencia documentada" (P2).

**Criterio de salida del bloque cero** (para arrancar S70-1 R2 Chaiten):
1. T1: NRT cron success rate ≥80% en próximos 5 runs (≥4/5).
2. T2: verdict claro confirmado/refutado sobre "TIF ≠ VRP sumable".
3. T3: si T2 confirma → método R2 replanteado en docs. Si refuta → archivado.
4. T4: docs actualizados consistentes con T2.
5. T5: CSV OCR recuperado a repo o exclusión justificada.

---

## File Structure

| Acción | Path | Responsabilidad |
|---|---|---|
| Modify | `tasks/SETUP_LOG_S70.md` | Commit setup S70 ya escrito |
| Create | `experiments/120_audit_tif_vrp_sumable/audit_lastarria.py` | Script auditoría TIF vs cluster MIROVA |
| Create | `experiments/120_audit_tif_vrp_sumable/README.md` | Documentación del experimento |
| Create | `experiments/120_audit_tif_vrp_sumable/results.json` | Salida estructurada de la comparación |
| Create | `experiments/121_nrt_cron_diagnosis/diagnosis.md` | Reporte de diagnóstico NRT |
| Modify (condicional T2 confirmado) | `docs/MIROVA_DIVERGENCES.md` | Agregar entry D6 |
| Modify (condicional T2) | `docs/HYPOTHESIS_LOG.md` | Entry H_S70_TIF_VRP_SUMABILITY |
| Modify (condicional T2 confirmado) | `tasks/BLOQUE_ARRANQUE_S70.md` | Replantear método R2 si hallazgo confirmado |
| Modify | `.github/workflows/nrt.yml` | Fix NRT cron (contenido depende de diagnóstico T1) |
| Maybe Create | `data/mirova_reference/registro_vrp_ocr.csv` | Si T5 lo recupera |
| Modify | `tasks/BLOQUE_ARRANQUE_S70.md` | Anotar resolución CSV OCR (T5) |

---

### Task 1: Diagnóstico NRT cron

**Files:**
- Create: `experiments/121_nrt_cron_diagnosis/diagnosis.md`

**Objetivo:** Identificar root cause de los 19 fallos consecutivos en últimos 20 runs (issue #1).

- [ ] **Step 1: Commit setup ya hecho previamente (no perder trabajo)**

```bash
cd C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP-Chile-s70
git add tasks/SETUP_LOG_S70.md tasks/plan_s70_0_saneamiento.md
git commit -m "S70-0 setup: worktree limpio + plan saneamiento"
```

Expected: commit creado en rama `s70-0-saneamiento`.

- [ ] **Step 2: Listar últimos 10 fallos NRT con metadata**

```bash
gh run list --workflow nrt.yml --status failure --limit 10 --json databaseId,createdAt,conclusion,displayTitle,headBranch > /tmp/nrt_failures.json
cat /tmp/nrt_failures.json | python -c "import json,sys; d=json.load(sys.stdin); [print(f'{r[\"databaseId\"]} {r[\"createdAt\"]} {r[\"displayTitle\"]}') for r in d]"
```

Expected: 10 líneas con run IDs, timestamps, títulos.

- [ ] **Step 3: Para los 3 fallos más recientes, inspeccionar jobs fallidos**

```bash
mkdir -p experiments/121_nrt_cron_diagnosis
# Reemplazar <RUN_ID> con los IDs de Step 2
for ID in <RUN_ID_1> <RUN_ID_2> <RUN_ID_3>; do
    echo "=== Run $ID ===" >> experiments/121_nrt_cron_diagnosis/raw_runs.txt
    gh run view $ID --json jobs --jq '.jobs[] | select(.conclusion=="failure") | {name, conclusion, startedAt, completedAt}' >> experiments/121_nrt_cron_diagnosis/raw_runs.txt
    echo "" >> experiments/121_nrt_cron_diagnosis/raw_runs.txt
done
```

Expected: archivo con jobs fallidos por run. Identificar si fallan los mismos vols o aleatorio.

- [ ] **Step 4: Inspeccionar logs del job más representativo**

```bash
# Tomar el job más reciente fallido (no cancelled)
gh run view <RUN_ID_1> --log-failed > experiments/121_nrt_cron_diagnosis/sample_log.txt 2>&1
# Buscar patrones de error conocidos
grep -E "earthaccess|TimeoutError|HTTPError|granule|401|403|503|killed|exit code" experiments/121_nrt_cron_diagnosis/sample_log.txt | head -30
```

Expected: stack traces o mensajes de error específicos. Salida típica: timeout en fetch, auth EARTHDATA expired, NASA LANCE 503, o `process_*.py` crash.

- [ ] **Step 5: Clasificar patrón y escribir diagnóstico**

Identificar cuál de las 4 ramas conocidas aplica:
- **Rama A — Timeout per-job**: jobs corren >25 min y `timeout-minutes` los mata. Solución: aumentar timeout o splitear matrix.
- **Rama B — Auth EARTHDATA expirada**: errores 401 en logs. Solución: rotar `EARTHDATA_PASSWORD` en secrets GitHub.
- **Rama C — NASA LANCE / earthaccess API rota**: errores 503, HTTPError repetitivos. Solución: agregar reintento o fallback NRT→Standard.
- **Rama D — Vol específico siempre falla**: si NdC, Tupungatito o Lascar siempre en lista. Solución: aislar ese vol, debugger separado.

Escribir el diagnóstico:

```bash
cat > experiments/121_nrt_cron_diagnosis/diagnosis.md <<'EOF'
# Diagnóstico NRT cron — 2026-05-20

## Datos
- Fallos consecutivos: 19/20 últimos runs
- Issue abierto: #1 priority-high desde 2026-05-20T10:01Z
- Última falla: 2026-05-20T10:49Z

## Patrón identificado
[Rama A/B/C/D según evidencia]

## Evidencia
[Pegar 5-10 líneas relevantes de sample_log.txt]

## Root cause
[1 párrafo]

## Fix propuesto
[Lista de cambios específicos a aplicar en Task 2]

## Criterio de validación
≥80% success rate en próximos 5 runs después del fix.
EOF
```

Editar el archivo con los datos reales del análisis.

- [ ] **Step 6: Commit diagnóstico**

```bash
git add experiments/121_nrt_cron_diagnosis/
git commit -m "S70-0 T1: diagnóstico NRT cron 19/20 failures"
```

Expected: commit creado.

---

### Task 2: Fix NRT cron según diagnóstico

**Files:**
- Modify: `.github/workflows/nrt.yml` (contenido depende de la rama identificada en T1)
- (Condicional Rama B) Rotar `EARTHDATA_PASSWORD` en GitHub secrets — requiere acceso de Nicolás
- Create: `experiments/121_nrt_cron_diagnosis/fix_applied.md`

**Objetivo:** Aplicar fix mínimo según diagnóstico Task 1. Validar.

- [ ] **Step 1: Leer estado actual del workflow**

```bash
cat .github/workflows/nrt.yml
```

Expected: ver `timeout-minutes`, `matrix.volcano`, `max-parallel`, steps de `process_modis.py`, `process_viirs.py`, etc.

- [ ] **Step 2: Aplicar fix según rama de diagnóstico**

**Si Rama A (timeout)**:

```yaml
# En .github/workflows/nrt.yml, step que corre process_*.py:
# Cambiar timeout-minutes: 25 → 50 (ajustar según logs Task 1)
# O si el bottleneck es un vol específico, separar a workflow propio
```

Editar `.github/workflows/nrt.yml` con `Edit` tool, cambiando valor exacto.

**Si Rama B (auth)**:
Pedir a Nicolás rotar `EARTHDATA_USERNAME` y `EARTHDATA_PASSWORD` en GitHub repo settings → Secrets and variables → Actions. Esperar confirmación. NO modificar workflow.

**Si Rama C (NASA LANCE flaky)**:

```yaml
# Agregar retry a step de fetch:
- name: Fetch + process
  run: python scripts/run_pipeline.py ...
  continue-on-error: false
# Wrap en retry action (3 reintentos con backoff)
```

Usar `nick-fields/retry@v3` action o equivalente. Ver doc actions.

**Si Rama D (vol específico)**:

```yaml
# Identificar el vol problemático (ej: NdC)
# Aislarlo a un job separado con timeout extendido
# O removerlo temporalmente de matrix con TODO para re-incluir
```

- [ ] **Step 3: Validar workflow sintaxis local**

```bash
gh workflow view nrt.yml --yaml > /tmp/nrt_current.yml
diff .github/workflows/nrt.yml /tmp/nrt_current.yml
```

Expected: diff muestra solo el cambio aplicado. No errores de parse.

- [ ] **Step 4: Documentar fix aplicado**

```bash
cat > experiments/121_nrt_cron_diagnosis/fix_applied.md <<'EOF'
# Fix NRT cron — 2026-05-20

## Rama de diagnóstico aplicada
[A/B/C/D]

## Cambio específico
[Diff de .github/workflows/nrt.yml o "rotación secret realizada por Nicolás"]

## Hipótesis de fix
[1 párrafo: por qué este cambio resuelve el patrón identificado]

## Plan validación
- Disparar manualmente un run: `gh workflow run nrt.yml`
- Esperar 4 ciclos cron (cada 2h = 8h total)
- Verificar success rate ≥80% (4/5)
EOF
```

- [ ] **Step 5: Commit fix**

```bash
git add .github/workflows/nrt.yml experiments/121_nrt_cron_diagnosis/fix_applied.md
git commit -m "S70-0 T1-fix: NRT cron rama [A/B/C/D] — [descripción 1 línea]"
git push origin s70-0-saneamiento
```

Expected: push exitoso. PR aún NO se crea (esperamos validación).

- [ ] **Step 6: Disparar run manual + monitorear**

```bash
gh workflow run nrt.yml
sleep 60
gh run list --workflow nrt.yml --limit 1
```

Expected: ver run en estado `in_progress` o `queued`.

Esperar ~30-45 min. Después:

```bash
gh run list --workflow nrt.yml --limit 5 --json conclusion,createdAt | python -c "import json,sys; d=json.load(sys.stdin); print(f'Success: {sum(1 for r in d if r[\"conclusion\"]==\"success\")}/{len(d)}')"
```

**Criterio de aceptación T1**: ≥4/5 success en próximos 5 runs (~8-10h después del fix). Si falla, volver a T1 Step 5 con otra hipótesis.

- [ ] **Step 7: Cerrar issue #1 si validación OK**

```bash
gh issue comment 1 --body "Fix S70-0 T1 aplicado. Success rate post-fix: X/5. Cerrando."
gh issue close 1
```

---

### Task 3: Auditoría hallazgo "TIF ≠ VRP sumable"

**Files:**
- Create: `experiments/120_audit_tif_vrp_sumable/audit_lastarria.py`
- Create: `experiments/120_audit_tif_vrp_sumable/README.md`
- Create: `experiments/120_audit_tif_vrp_sumable/results.json`

**Objetivo:** Replicar método R2 del agente S69 sobre TIF Lastarria. Comparar centroide top10 pixels vs cluster MIROVA reportado en KMZ del mismo evento. Verdict binario: el TIF es sumable / no es sumable como VRP per-pixel.

**Caso paradigmático**: Lastarria 2026-05-09 03:48 UTC VIIRS375 (single overpass, single vol — minimiza ruido). Path TIF: `data/tif/Lastarria/20260509_034843_VIIRS750.tif` o el VIIRS375 más cercano del mismo evento.

- [ ] **Step 1: Verificar rasterio instalado**

```bash
python -c "import rasterio; print(rasterio.__version__)"
```

Si falla: `pip install rasterio` (en env Anaconda activo).

Expected: versión impresa (≥1.3 OK).

- [ ] **Step 2: Setup dir + descarga TIF y KMZ paralelo**

```bash
mkdir -p experiments/120_audit_tif_vrp_sumable
cd experiments/120_audit_tif_vrp_sumable

# El repo mirova-tif-archive está paralelo, lo leemos directo
ls ../../../mirova-tif-archive/data/tif/Lastarria/ | head -20
```

Identificar TIF VIIRS375 reciente con KMZ paralelo:

```bash
ls ../../../mirova-tif-archive/data/tif/Lastarria/ | grep VIIRS375 | tail -3
ls ../../../mirova-tif-archive/data/kmz/Lastarria/ | grep VIIRS375 | tail -3
```

Expected: ver pares TIF + KMZ del mismo timestamp.

Volver al worktree root:

```bash
cd ../..  # volver a worktree root
```

- [ ] **Step 3: Escribir test fixture — TIF sintético controlado**

```python
# experiments/120_audit_tif_vrp_sumable/test_method.py
import numpy as np
import rasterio
from rasterio.transform import from_origin

def make_synthetic_tif(path):
    """Crea TIF 100x100 con 1 cluster en (50,50) de 9 pixels valor 10 MW c/u
    y 90 pixels noise valor 0.1 MW dispersos."""
    arr = np.zeros((100, 100), dtype=np.float32)
    arr[49:52, 49:52] = 10.0  # cluster 9 pix × 10 MW = 90 MW total
    rng = np.random.default_rng(42)
    noise_mask = rng.random((100, 100)) < 0.09
    arr[noise_mask & (arr == 0)] = 0.1
    transform = from_origin(-69.0, -25.0, 0.001, 0.001)
    with rasterio.open(
        path, 'w', driver='GTiff', height=100, width=100, count=1,
        dtype=np.float32, crs='EPSG:4326', transform=transform
    ) as dst:
        dst.write(arr, 1)
    return arr

if __name__ == "__main__":
    arr = make_synthetic_tif("/tmp/synthetic.tif")
    print(f"Suma total: {arr.sum():.1f} MW")
    print(f"Cluster esperado: 9 pix × 10 MW = 90 MW")
    print(f"Noise esperado: ~{(arr>0).sum()-9} pix × 0.1 MW")
```

Ejecutar:

```bash
python experiments/120_audit_tif_vrp_sumable/test_method.py
```

Expected: "Suma total: ~99 MW", "Cluster esperado: 90 MW". Confirma que rasterio escribe/lee correcto.

- [ ] **Step 4: Implementar método R2 del agente S69 — top10 pixels ponderado**

```python
# experiments/120_audit_tif_vrp_sumable/audit_lastarria.py
"""Auditoría hallazgo S33+ 'TIF MIROVA ≠ VRP sumable'.

Método R2 del agente S69 sobre TIF Lastarria. Compara contra cluster MIROVA del KMZ.

Pre-condición: T1 ya validado (NRT cron sano) — opcional, pero la data debe estar fresca.
"""
import json
import numpy as np
import rasterio
from pathlib import Path
from xml.etree import ElementTree as ET
import zipfile

TIF_ARCHIVE = Path("../../mirova-tif-archive")  # ajustar si CWD distinto
RESULTS_PATH = Path(__file__).parent / "results.json"


def load_tif(path: Path) -> tuple[np.ndarray, rasterio.Affine]:
    """Lee TIF y devuelve (array, transform)."""
    with rasterio.open(path) as src:
        return src.read(1), src.transform


def top_n_centroid(arr: np.ndarray, transform: rasterio.Affine, n: int = 10):
    """Método R2 S69: centroide ponderado de los top-N pixels con valor positivo.

    Devuelve (lat_centroid, lon_centroid, total_mw, n_used)."""
    flat = arr.flatten()
    pos_idx = np.where(flat > 0)[0]
    if len(pos_idx) == 0:
        return None, None, 0.0, 0
    n_used = min(n, len(pos_idx))
    top_pos = pos_idx[np.argsort(flat[pos_idx])[-n_used:]]
    rows, cols = np.unravel_index(top_pos, arr.shape)
    weights = flat[top_pos]
    # Convertir row/col a lat/lon usando affine transform
    xs, ys = rasterio.transform.xy(transform, rows, cols)
    xs = np.array(xs)
    ys = np.array(ys)
    lon_c = float((xs * weights).sum() / weights.sum())
    lat_c = float((ys * weights).sum() / weights.sum())
    return lat_c, lon_c, float(weights.sum()), n_used


def parse_kmz_header(kmz_path: Path) -> dict:
    """Extrae VRP, distancia, y centroide del KMZ MIROVA.

    El KMZ contiene un doc.kml con descripción HTML que incluye 'VRP: X MW @ Y km'.
    También un Placemark del centroide del cluster reportado."""
    with zipfile.ZipFile(kmz_path) as zf:
        kml_name = [n for n in zf.namelist() if n.endswith('.kml')][0]
        kml = zf.read(kml_name).decode('utf-8', errors='replace')
    # Buscar VRP en descripción (texto plano + entidades HTML)
    import re
    vrp_match = re.search(r'VRP[:\s]+([\d.]+)\s*MW', kml, re.IGNORECASE)
    dist_match = re.search(r'@\s*([\d.]+)\s*km', kml, re.IGNORECASE)
    # Buscar coordenadas del primer Placemark
    ns = {'kml': 'http://www.opengis.net/kml/2.2'}
    root = ET.fromstring(kml)
    coords_elem = root.find('.//kml:Placemark/kml:Point/kml:coordinates', ns)
    cluster_lat, cluster_lon = None, None
    if coords_elem is not None and coords_elem.text:
        parts = coords_elem.text.strip().split(',')
        cluster_lon = float(parts[0])
        cluster_lat = float(parts[1])
    return {
        'vrp_mw_header': float(vrp_match.group(1)) if vrp_match else None,
        'dist_km_header': float(dist_match.group(1)) if dist_match else None,
        'cluster_lat': cluster_lat,
        'cluster_lon': cluster_lon,
    }


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dp = np.radians(lat2 - lat1)
    dl = np.radians(lon2 - lon1)
    a = np.sin(dp/2)**2 + np.cos(p1)*np.cos(p2)*np.sin(dl/2)**2
    return 2 * R * np.arcsin(np.sqrt(a))


def audit_case(tif_path: Path, kmz_path: Path) -> dict:
    """Audita un caso TIF+KMZ paralelos."""
    arr, transform = load_tif(tif_path)
    lat_top10, lon_top10, mw_top10, n_used = top_n_centroid(arr, transform, n=10)
    full_sum_mw = float(arr[arr > 0].sum())
    full_pos_pixels = int((arr > 0).sum())
    kmz_data = parse_kmz_header(kmz_path)

    drift_km = None
    ratio_mw = None
    if kmz_data['cluster_lat'] is not None and lat_top10 is not None:
        drift_km = float(haversine_km(
            lat_top10, lon_top10, kmz_data['cluster_lat'], kmz_data['cluster_lon']
        ))
    if kmz_data['vrp_mw_header'] and mw_top10 > 0:
        ratio_mw = mw_top10 / kmz_data['vrp_mw_header']

    return {
        'tif': tif_path.name,
        'kmz': kmz_path.name,
        'top10_centroid_lat': lat_top10,
        'top10_centroid_lon': lon_top10,
        'top10_sum_mw': mw_top10,
        'top10_n_used': n_used,
        'full_tif_sum_mw': full_sum_mw,
        'full_tif_pos_pixels': full_pos_pixels,
        'kmz_cluster_lat': kmz_data['cluster_lat'],
        'kmz_cluster_lon': kmz_data['cluster_lon'],
        'kmz_vrp_mw_header': kmz_data['vrp_mw_header'],
        'kmz_dist_km_header': kmz_data['dist_km_header'],
        'drift_centroid_km': drift_km,
        'ratio_top10_vs_header': ratio_mw,
    }


def main():
    # Lastarria caso paradigmático: VIIRS375 reciente con KMZ paralelo
    tif_dir = TIF_ARCHIVE / "data/tif/Lastarria"
    kmz_dir = TIF_ARCHIVE / "data/kmz/Lastarria"
    tifs = sorted(tif_dir.glob("*VIIRS375.tif"))[-5:]  # 5 más recientes
    results = []
    for tif in tifs:
        kmz = kmz_dir / tif.name.replace('.tif', '.kmz')
        if not kmz.exists():
            continue
        try:
            r = audit_case(tif, kmz)
            results.append(r)
            print(f"\n{tif.name}:")
            print(f"  TIF total sum: {r['full_tif_sum_mw']:.1f} MW ({r['full_tif_pos_pixels']} pix)")
            print(f"  TIF top10 sum: {r['top10_sum_mw']:.2f} MW")
            print(f"  KMZ header VRP: {r['kmz_vrp_mw_header']} MW")
            print(f"  Ratio top10/header: {r['ratio_top10_vs_header']}")
            print(f"  Drift centroid: {r['drift_centroid_km']} km")
        except Exception as e:
            print(f"FAIL {tif.name}: {e}")
            results.append({'tif': tif.name, 'error': str(e)})

    RESULTS_PATH.write_text(json.dumps(results, indent=2, default=str))
    print(f"\n✓ Resultados → {RESULTS_PATH}")

if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Ejecutar auditoría**

```bash
cd C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP-Chile-s70
python experiments/120_audit_tif_vrp_sumable/audit_lastarria.py
```

Expected: salida con 3-5 casos. Cada uno muestra `full_tif_sum_mw` (suma total TIF), `top10_sum_mw` (método S69), `kmz_vrp_mw_header` (lo que MIROVA realmente reporta).

**Verdict binario**:
- Si `top10_sum_mw` ≈ `kmz_vrp_mw_header` (ratio 0.5-2.0) en ≥3/5 casos → **REFUTADO**. El método R2 S69 es correcto. Archivar hallazgo S33+.
- Si `top10_sum_mw` >> `kmz_vrp_mw_header` (ratio >10×) consistentemente → **CONFIRMADO**. El TIF NO es sumable. Método R2 está midiendo el campo de radiancia completo, no el VRP del cluster MIROVA. Replantear método.

- [ ] **Step 6: Escribir README del experimento**

```bash
cat > experiments/120_audit_tif_vrp_sumable/README.md <<'EOF'
# Experimento 120 — Auditoría "TIF MIROVA ≠ VRP sumable" (S70-0 T2)

## Pregunta
¿El TIF que descargamos del repo `mirova-tif-archive` es VRP per-pixel sumable, o es producto de visualización del campo de radiancia (no sumable)?

## Origen del hallazgo
Commit `64bd37d` (s15-dev local, no en main) reportó: TIF Lascar tiene 17,911 pixels positivos sumando 1680 MW, pero el header MIROVA reporta "VRP: 0.2 MW @ 9.7 km". El TIF NO es VRP per-pixel sumable.

Si la observación es correcta, el método R2 retroactivo del agente S69 Lastarria (que ponderó top-10 pixels del TIF para validar la calibración) puede estar comparando contra el objeto incorrecto. Aplicar el método a Chaiten/PCC/Villarrica/PP sin validar propagaría el error.

## Método
1. Tomar 5 TIFs VIIRS375 Lastarria recientes con KMZ paralelo.
2. Para cada uno: calcular centroide ponderado top-10 pixels (método S69) + suma MW del cluster.
3. Parsear KMZ del mismo evento: extraer `VRP: X MW @ Y km` del header + lat/lon del Placemark del cluster.
4. Comparar:
   - Ratio `top10_mw / header_mw` (1.0 = coinciden)
   - Drift `centroid_top10` vs `cluster_kmz` (km)

## Verdict
- **REFUTADO** si ratio ∈ [0.5, 2.0] y drift <2 km en ≥3/5 casos → método R2 S69 OK
- **CONFIRMADO** si ratio >10× consistente → TIF no sumable, replantear R2

## Resultados
Ver `results.json`.

## Consecuencia
- Si REFUTADO: archivar el hallazgo del commit `64bd37d` con nota explicativa. R2 retroactivo Chaiten S70-1 procede.
- Si CONFIRMADO: documentar como D6 en `docs/MIROVA_DIVERGENCES.md`, entry `H_S70_TIF_VRP_SUMABILITY` en `HYPOTHESIS_LOG`, replantear método R2 antes de S70-1.
EOF
```

- [ ] **Step 7: Commit experimento**

```bash
git add experiments/120_audit_tif_vrp_sumable/
git commit -m "S70-0 T2: audit TIF VRP sumability — 5 casos Lastarria"
```

---

### Task 4: Documentar verdict T2 + decisión sobre método R2

**Files (depende del verdict)**:

**Si REFUTADO**:
- Modify: `docs/HYPOTHESIS_LOG.md` (agregar entry `H_S70_TIF_VRP_SUMABILITY` con verdict REFUTADO)
- Modify: `experiments/120_audit_tif_vrp_sumable/README.md` (sección "verdict" con conclusión + referencia a commit s15-dev como archivado)

**Si CONFIRMADO**:
- Modify: `docs/MIROVA_DIVERGENCES.md` (agregar entry D6)
- Modify: `docs/HYPOTHESIS_LOG.md` (entry CONFIRMADO + implicaciones)
- Modify: `tasks/BLOQUE_ARRANQUE_S70.md` (replantear método R2 en sección 3, prioridad MEDIA)

- [ ] **Step 1: Leer estructura actual de HYPOTHESIS_LOG.md**

```bash
head -50 docs/HYPOTHESIS_LOG.md
```

Identificar formato de entry para mantener consistencia.

- [ ] **Step 2: Si REFUTADO — agregar entry archivado**

Editar `docs/HYPOTHESIS_LOG.md`, agregar al inicio:

```markdown
## H_S70_TIF_VRP_SUMABILITY — REFUTADA (2026-05-20)

**Hipótesis**: TIF descargado de `mirova-tif-archive` NO es VRP per-pixel sumable, sino producto de visualización del campo de radiancia.

**Origen**: Observación commit local `64bd37d` (s15-dev) S33+ sobre Lascar: 17,911 pixels=1680 MW vs header 0.2 MW @ 9.7km.

**Test S70-0 T2**: `experiments/120_audit_tif_vrp_sumable/audit_lastarria.py` sobre 5 TIFs Lastarria recientes.

**Resultado**: ratio top10/header ∈ [X, Y] (mediana Z), drift centroide < 2 km en N/5 casos. El método R2 del agente S69 SÍ está midiendo aproximadamente el VRP del cluster, no el campo completo.

**Veredicto**: REFUTADA. Método R2 retroactivo S69 (centroide top-10 pixels ponderado) es válido para replicar en Chaiten/PCC/Villarrica/PP en S70-1.

**Acción**: hallazgo S33+ del commit `64bd37d` archivado. Anotar en `experiments/120_audit_tif_vrp_sumable/README.md`.
```

(Reemplazar X/Y/Z/N con valores reales de `results.json`.)

- [ ] **Step 3: Si CONFIRMADO — agregar D6 a MIROVA_DIVERGENCES.md**

Editar `docs/MIROVA_DIVERGENCES.md`, agregar al final (manteniendo formato de D1-D5):

```markdown
## D6 — TIF `mirova-tif-archive` no es VRP per-pixel sumable (S70-0)

**Observación**: TIFs del repo `mirova-tif-archive` (scraper paralelo, cada 5 min) contienen el campo de radiancia/anomalía completo. La suma de todos los pixels positivos NO equivale al `VRP` que MIROVA reporta en el header del KMZ paralelo.

**Evidencia S70-0 T2**: `experiments/120_audit_tif_vrp_sumable/audit_lastarria.py` sobre 5 TIFs Lastarria:
- Ratio `top10_pixels_sum / header_VRP_mw` mediana: [Z]× (esperado 1.0 si fuera sumable)
- Drift centroide top10 vs cluster KMZ: [W] km mediana

**Implicación operacional**: el método R2 retroactivo aplicado por agente S69 Lastarria (centroide ponderado top-10 pixels TIF) está midiendo aproximadamente el centroide del campo, no el cluster MIROVA. La calibración Lastarria S69 puede no ser pixel-level-validada.

**Acción S70-0 T4**: replantear método R2 en `tasks/BLOQUE_ARRANQUE_S70.md` sección 3. Opciones:
1. Parsear cluster directo del KMZ (Placemark coordinates) en vez de top-10 pixels del TIF.
2. Filtrar TIF a pixels con valor > umbral observado en header MIROVA.
3. Combinar ambas señales: KMZ para centroide nominal, TIF para validación de gradiente.

**Pendiente S70-1**: ejecutar R2 Lastarria con método nuevo y verificar que el resultado validado S69 sigue siendo consistente.
```

(Reemplazar Z/W con valores reales.)

- [ ] **Step 4: Si CONFIRMADO — entry en HYPOTHESIS_LOG (versión confirmada)**

```markdown
## H_S70_TIF_VRP_SUMABILITY — CONFIRMADA (2026-05-20)

[similar estructura al Step 2, pero con verdict CONFIRMADA y referencias a D6]
```

- [ ] **Step 5: Si CONFIRMADO — replantear método R2 en BLOQUE_ARRANQUE_S70.md**

Editar `tasks/BLOQUE_ARRANQUE_S70.md` sección 3 (R2 retroactivos), reemplazar el bloque de método:

```markdown
### Prioridad MEDIA — R2 retroactivos (método REPLANTEADO post-S70-0 T2)

**ATENCIÓN**: el método original S69 (centroide top-10 pixels TIF ponderado) fue refutado en S70-0 T2 como medida del cluster MIROVA. Ver `docs/MIROVA_DIVERGENCES.md` D6.

**Método nuevo (S70-1)**: parsear cluster directo del KMZ paralelo en `mirova-tif-archive/data/kmz/<Vol>/`. Cada KMZ contiene Placemark con coordenadas del centroide reportado por MIROVA + descripción con "VRP: X MW @ Y km" del cluster.

[resto del bloque adaptado]
```

- [ ] **Step 6: Commit decisiones T4**

```bash
git add docs/ tasks/BLOQUE_ARRANQUE_S70.md
git commit -m "S70-0 T4: verdict TIF sumability [REFUTADO/CONFIRMADO] + docs"
```

---

### Task 5: Resolver CSV OCR universe

**Files:**
- (Posible) Create: `data/mirova_reference/registro_vrp_ocr.csv`
- Modify: `tasks/BLOQUE_ARRANQUE_S70.md` (anotar resolución)

**Objetivo:** Recuperar `registro_vrp_ocr.csv` (universe S62 con +457 ALERTAS_TERMICA_OCR) a `data/mirova_reference/` o documentar exclusión justificada.

- [ ] **Step 1: Verificar si CSV ya existe en repo (origin/main)**

```bash
ls data/mirova_reference/*.csv 2>&1
git ls-tree -r origin/main --name-only | grep -i "ocr\|consolidado" | head -10
```

Expected: listar CSVs ya commiteados. Si `registro_vrp_ocr.csv` aparece → ya resuelto, saltar a Step 5.

- [ ] **Step 2: Buscar CSV en ubicaciones conocidas**

```bash
# Ubicación 1: backup defensivo S15-dev (más probable)
find ../backup-s15-dev-untracked-2026-05-20 -iname "*ocr*.csv" 2>&1

# Ubicación 2: scraper Mirova-v1 (origen)
ls "C:/Users/nmend/OneDrive/Escritorio/claude/Automatizacion web/Automatizacion web/Mirova-v1" 2>&1 | head -20
find "C:/Users/nmend/OneDrive/Escritorio/claude/Automatizacion web/Automatizacion web/Mirova-v1" -iname "*ocr*.csv" 2>&1 | head -10
```

Expected: ubicar el CSV. Si no aparece en ninguno, ir a Step 4 (documentar exclusión).

- [ ] **Step 3: Si encontrado — validar contenido del CSV**

```python
# /tmp/validate_ocr.py
import pandas as pd
import sys
df = pd.read_csv(sys.argv[1])
print(f"Filas: {len(df)}")
print(f"Columnas: {list(df.columns)}")
print(f"Tipos de registro: {df['Tipo_Registro'].value_counts().to_dict() if 'Tipo_Registro' in df.columns else 'columna ausente'}")
if 'Volcan' in df.columns:
    print(f"Vols cubiertos: {df['Volcan'].value_counts().to_dict()}")
print(f"Rango fechas: {df.iloc[:,0].min()} → {df.iloc[:,0].max()}")
```

```bash
python /tmp/validate_ocr.py <ruta_csv_encontrado>
```

Expected: confirmar que tiene ALERTAS_TERMICA_OCR como esperado por memoria S62 (~457 entries adicionales). Si no, ir a Step 4.

- [ ] **Step 4a: Si CSV válido — copiar a repo + commit**

```bash
cp "<ruta_origen>" data/mirova_reference/registro_vrp_ocr.csv
git add data/mirova_reference/registro_vrp_ocr.csv

cat > /tmp/commit_msg.txt <<'EOF'
S70-0 T5: agregar CSV OCR universe a data/mirova_reference/

Recupera registro_vrp_ocr.csv (universe S62 con +457 ALERTAS_TERMICA_OCR).
Origen: [ruta exacta del Step 2].
Cobertura: [conteos del Step 3].
Esto restaura reproducibilidad externa de calibraciones Lastarria/Chaiten/PCC S62-S63.
EOF
git commit -F /tmp/commit_msg.txt
```

- [ ] **Step 4b: Si NO encontrado o inválido — documentar exclusión**

Editar `tasks/BLOQUE_ARRANQUE_S70.md`, agregar sección al final:

```markdown
## CSV OCR universe (S70-0 T5 — exclusión justificada)

**Estado**: NO recuperado a `data/mirova_reference/`.

**Búsqueda S70-0 T5**:
- `backup-s15-dev-untracked-2026-05-20/`: [no encontrado / encontrado pero obsoleto / etc.]
- Mirova-v1 scraper en `C:/Users/nmend/OneDrive/Escritorio/claude/Automatizacion web/Automatizacion web/Mirova-v1`: [estado]

**Implicación**: las calibraciones S62-S63 (Lastarria 1.07×, Chaiten 2.23×, PCC 0.29×) usaron un universo expandido que NO es reproducible externamente con el repo actual. Las ratios reportadas son evidencia interna válida pero no auditable por terceros.

**Alternativa S70-1+**: re-correr auditorías de calibración usando solo `data/mirova_reference/*registro_vrp_consolidado.csv` (sin OCR). Comparar ratios resultantes. Si divergen >50% del valor S62-S63, marcar las adopciones como "calibradas en universe OCR no público" en `MIROVA_DIVERGENCES.md`.
```

- [ ] **Step 5: Commit cierre T5**

```bash
git add tasks/BLOQUE_ARRANQUE_S70.md
git commit -m "S70-0 T5: CSV OCR universe [recuperado/exclusión documentada]"
```

---

## Checkpoint salida bloque cero S70-0

- [ ] **T1 cron NRT**: success rate ≥80% en 5 runs post-fix (medido ~8h después de aplicar fix)
- [ ] **T2 audit TIF**: `experiments/120_audit_tif_vrp_sumable/results.json` con 3-5 casos, verdict claro
- [ ] **T3+T4 docs**: HYPOTHESIS_LOG entry creada + MIROVA_DIVERGENCES.md D6 si confirmado + BLOQUE_ARRANQUE_S70 replanteado si confirmado
- [ ] **T5 OCR**: CSV recuperado a `data/mirova_reference/` o exclusión documentada en BLOQUE_ARRANQUE_S70

**Cuando todos los checkpoints están ✓**: abrir PR `s70-0-saneamiento → main` para review de Nicolás. Después arrancar S70-1 (R2 retroactivo Chaiten + 3 vols restantes adoptados).

```bash
gh pr create --title "S70-0 Saneamiento: NRT cron + audit TIF + OCR universe" \
  --body "$(cat <<'EOF'
## Resumen
Bloque cero S70 — resuelve 3 pre-condiciones detectadas en auditoría integral S70:
- T1: NRT cron rescatado de 5% → ≥80% success rate
- T2: hallazgo "TIF ≠ VRP sumable" auditado, verdict [CONFIRMADO/REFUTADO]
- T5: CSV OCR universe [recuperado/exclusión documentada]

Ver `tasks/plan_s70_0_saneamiento.md` para plan completo y `experiments/120-121/` para evidencia.

## Test plan
- [x] T1: success rate ≥80% medido en 5 runs post-fix
- [x] T2: `experiments/120_audit_tif_vrp_sumable/results.json` válido
- [x] Docs actualizados: HYPOTHESIS_LOG, MIROVA_DIVERGENCES (si aplica), BLOQUE_ARRANQUE_S70

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

## Self-review (writing-plans skill)

**Cobertura spec**:
- ✅ T1 (NRT cron) → Task 1 + Task 2
- ✅ T2 (audit TIF) → Task 3
- ✅ T3 (CSV OCR) → Task 5
- ✅ T4 (persistir hallazgo) → Task 4

**Placeholder scan**: Step 3 de Task 1 contiene `<RUN_ID_1>` etc. — son placeholders intencionales que se resuelven dinámicamente con la salida del Step 2. Aceptable: el plan es ejecutable secuencialmente. Step 2 de Task 2 contiene "[A/B/C/D según evidencia]" — también intencional (decision tree con 4 ramas concretas detalladas).

**Type consistency**: funciones `top_n_centroid`, `parse_kmz_header`, `audit_case` consistentes a lo largo de Task 3. `audit_lastarria.py` único nombre de archivo. `data/mirova_reference/registro_vrp_ocr.csv` único path para CSV OCR.

**Sin gaps detectados.**
