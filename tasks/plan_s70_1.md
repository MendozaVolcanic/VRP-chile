# Plan S70-1: R2 retroactivos + cleanup workflows

> **For agentic workers:** Use superpowers:subagent-driven-development to implement task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Cerrar la deuda audit S67 aplicando R2 retroactivo pixel-level a Chaiten, Villarrica, PlanchonPeteroa, PCC (4 vols adoptados S61-S63 sin R2). Adicionalmente, archivar 14 workflows obsoletos para limpiar el directorio CI.

**Architecture:** Aplicar el patrón R2 verdadero validado en S70-0 T3 Step 8 (`experiments/120_audit_tif_vrp_sumable/audit_lastarria_real_method.py`) a 4 vols nuevos. Cada R2 produce un script independiente + results.json + entry en `HYPOTHESIS_LOG`. Cleanup workflows es separado, mecánico.

**Tech Stack:** Python 3.12 (rasterio, pandas, numpy), Git, `gh` CLI.

**Worktree:** `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP-Chile-s70\` rama `s70-1-r2-retroactivo` basada en `s70-0-saneamiento` (commit `3d10384`).

**Pre-condición**: PR #103 (S70-0) NO mergeado todavía. Este trabajo construye encima del cero. Cuando S70-0 merge a main, S70-1 rebase es trivial.

**Misión vinculante**: `docs/MISSION.md` — R2 retroactivos cierran divergencia documentada D7 (preliminar — adopciones sin validación pixel-level) y por tanto pasan P2 de las 3 preguntas. Cleanup workflows es P3 alineación interna.

**Patrón R2 verdadero (validado S70-0 T3 Step 8)**:

1. Cargar record matching del vol target en `data/mirova_equivalent/<Vol>.json`. Filtrar por timestamp ALERTA MIROVA del día específico.
2. Extraer `pc.vrp_mw` y `pc.centroid_lat/lon` del record.
3. Buscar match en `data/mirova_reference/*registro_vrp_consolidado.csv` (o el OCR si aplica). Extraer `VRP_MW` MIROVA del mismo timestamp y `Distancia_km`.
4. Descargar TIF correspondiente de `../mirova-tif-archive/data/tif/<Vol>/<timestamp>_<sensor>.tif`.
5. Calcular centroide TIF top10 pixels **<3km del vent** ponderado (función `top_n_centroid_near_vent`).
6. Verdict 4 gates:
   - ratio magnitud `pc.vrp_mw / MIROVA_CSV.VRP_MW` ∈ [0.5, 2.0]
   - drift `top10_centroid TIF` vs `pc.centroid` < 2 km
   - ratio close to expected (target adopción S6X)
   - drift close to expected

**Tolerancias R2 PASS** (consensuadas S70-0):
- Ratio magnitud in band [0.5, 2.0]
- Drift centroide < 2 km
- Conformidad: ambos gates en simultaneous PASS.

---

## File Structure

| Acción | Path | Responsabilidad |
|---|---|---|
| Create | `experiments/122_r2_chaiten/audit_chaiten.py` | R2 retroactivo Chaiten |
| Create | `experiments/122_r2_chaiten/results.json` | Resultados Chaiten |
| Create | `experiments/123_r2_villarrica/audit_villarrica.py` | R2 Villarrica |
| Create | `experiments/123_r2_villarrica/results.json` | |
| Create | `experiments/124_r2_planchon_peteroa/audit_pp.py` | R2 PlanchonPeteroa |
| Create | `experiments/124_r2_planchon_peteroa/results.json` | |
| Create | `experiments/125_r2_pcc/audit_pcc.py` | R2 PCC |
| Create | `experiments/125_r2_pcc/results.json` | |
| Modify | `docs/HYPOTHESIS_LOG.md` | Entry consolidada `H_S70_R2_RETROACTIVO_4VOLS` |
| Modify | `tasks/BLOQUE_ARRANQUE_S70.md` | Marcar pendiente "R2 retroactivos" como ✅ done |
| Move | `.github/workflows/reproc-*.yml` (14 files) | A `.github/workflows/_archive/` |
| Modify | `.github/workflows/_archive/README.md` (new) | Explicación de archive |

---

### Task 1: R2 retroactivo Chaiten

**Objetivo**: Validar adopción S63 Chaiten kernel-bg (ratio LEGACY 9.78× → NEW 2.23×) con R2 pixel-level.

**Caso paradigmático**: ALERTA MIROVA Chaiten más reciente disponible en CSV NRT, post-adopción kernel-bg S63 (después de 2026-05-19), con TIF VIIRS375 paralelo en `mirova-tif-archive`.

**Files:**
- Create: `experiments/122_r2_chaiten/audit_chaiten.py`
- Create: `experiments/122_r2_chaiten/results.json`
- Create: `experiments/122_r2_chaiten/README.md`

- [ ] **Step 1: Identificar caso**

```bash
cd C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP-Chile-s70

# Buscar ALERTAS Chaiten recientes en CSV NRT
python -c "
import pandas as pd
df = pd.read_csv('data/mirova_reference/01_05_2026 registro_vrp_consolidado.csv')
chaiten = df[(df['Volcan'].str.contains('Chait', case=False)) & (df['Tipo_Registro']=='ALERTA_TERMICA')]
print(f'Total ALERTAS Chaiten: {len(chaiten)}')
print(chaiten[['Fecha_Satelite_UTC','Sensor','VRP_MW','Distancia_km']].tail(5))
"

# Buscar TIFs disponibles para Chaiten
ls ../mirova-tif-archive/data/tif/Chaiten/ | grep VIIRS375 | tail -5
ls ../mirova-tif-archive/data/tif/Chaiten/ | grep VIIRS750 | tail -3
ls ../mirova-tif-archive/data/tif/Chaiten/ | grep MODIS | tail -3
```

Identificar 1 ALERTA con TIF paralelo del mismo timestamp.

- [ ] **Step 2: Crear dir + script template**

```bash
mkdir -p experiments/122_r2_chaiten
cp experiments/120_audit_tif_vrp_sumable/audit_lastarria_real_method.py experiments/122_r2_chaiten/audit_chaiten.py
```

Editar `audit_chaiten.py`:
- Cambiar `VOLCANO = "Lastarria"` → `"Chaiten"`
- Cambiar `TARGET_DATE = "2026-05-14"` → fecha real del caso elegido
- Cambiar `TARGET_TIME = "05:48"` → hora real
- Cambiar `VENT_LAT/LON` → coords vent Chaiten de `volcanoes.yaml` (-42.835, -72.646 aprox)
- Cambiar `TARGET_PC_CENTROID` → leer del JSON al vuelo (no hardcodear)
- Cambiar `TARGET_MIROVA_VRP` → valor real del CSV
- Cambiar paths a `experiments/122_r2_chaiten/...`

- [ ] **Step 3: Ejecutar + capturar resultados**

```bash
python experiments/122_r2_chaiten/audit_chaiten.py
```

Expected: salida con 4 gates evaluadas. Verdict PASS si los 4 dan True; FAIL si alguno False.

- [ ] **Step 4: Escribir README documentando**

Plantilla README:
```markdown
# Experimento 122 — R2 retroactivo Chaiten

## Caso
[Fecha + sensor + ALERTA MIROVA]

## Resultado
- Ratio magnitud: [X]× (target S63 adopción: ~2.23×, MIROVA: [Y] MW, ours: [Z] MW)
- Centroide TIF top10 <3km vent: [lat, lon]
- pc.centroid: [lat, lon]
- Drift: [N] km

## Verdict
- ratio_in_band: ✓/✗
- drift_ok: ✓/✗
- ratio_close_to_target: ✓/✗
- drift_close_to_target: ✓/✗
- **Global**: PASS/FAIL

## Implicación
- Si PASS: adopción S63 Chaiten kernel-bg VALIDADA con R2 pixel-level.
- Si FAIL: revisar mecanismo (puede requerir investigación adicional S70-1+).
```

- [ ] **Step 5: Commit**

```bash
git add experiments/122_r2_chaiten/
git commit -m "S70-1 T1: R2 retroactivo Chaiten — [PASS/FAIL]"
```

---

### Task 2: R2 retroactivo Villarrica

Mismo patrón que Task 1. Diferencias:
- `VOLCANO = "Villarrica"`
- vent: -39.420, -71.939
- Target adopción S61: 2.17× (legacy 31.59× → kernel-bg)
- Path: `experiments/123_r2_villarrica/`

- [ ] **Step 1-5**: idénticos a Task 1 con sustituciones. Commit message: `"S70-1 T2: R2 retroactivo Villarrica — [PASS/FAIL]"`.

---

### Task 3: R2 retroactivo PlanchonPeteroa

- `VOLCANO = "PlanchonPeteroa"`
- vent: -35.240, -70.572 (verificar `volcanoes.yaml`)
- Target adopción S61: 2.84× (legacy 11.80×)
- Path: `experiments/124_r2_planchon_peteroa/`

- [ ] **Step 1-5**: idénticos. Commit message: `"S70-1 T3: R2 retroactivo PlanchonPeteroa — [PASS/FAIL]"`.

---

### Task 4: R2 retroactivo PCC (PuyehueCordonCaulle)

- `VOLCANO = "PuyehueCordonCaulle"`
- vent: -40.590, -72.117 (verificar `volcanoes.yaml`)
- Target adopción S63: 0.29× (legacy 3.64×)
- Path: `experiments/125_r2_pcc/`
- **Nota especial**: PCC tiene `inner_radius_km: 20` (lacolito). El filtro `<3km vent` puede ser muy estricto. Si pixels insuficientes, agregar fallback `<5km` con nota.

- [ ] **Step 1-5**: idénticos con la nota sobre inner_radius. Commit: `"S70-1 T4: R2 retroactivo PCC — [PASS/FAIL]"`.

---

### Task 5: Consolidar resultados en docs

**Files:**
- Modify: `docs/HYPOTHESIS_LOG.md` (entry consolidada)
- Modify: `tasks/BLOQUE_ARRANQUE_S70.md` (marcar deuda audit S67 cerrada)

- [ ] **Step 1: Entry HYPOTHESIS_LOG**

Agregar al inicio (después de H_S70_TIF_VRP_SUMABILITY):

```markdown
## H_S70_R2_RETROACTIVO_4VOLS — Adopciones S61-S63 validadas con R2 pixel-level

- **Formulada**: S70-1 (2026-05-20) tras validación del método R2 verdadero en S70-0 T3 Step 8 (Lastarria 1.05× exact match S69).
- **Casos**: Chaiten (S63), Villarrica (S61), PlanchonPeteroa (S61), PCC (S63).
- **Método**: patrón documentado en `experiments/120_audit_tif_vrp_sumable/README.md` Parte 2.
- **Resultados**:
  - Chaiten: ratio [X]×, drift [N] km — [PASS/FAIL]
  - Villarrica: ratio [X]×, drift [N] km — [PASS/FAIL]
  - PP: ratio [X]×, drift [N] km — [PASS/FAIL]
  - PCC: ratio [X]×, drift [N] km — [PASS/FAIL]
- **Implicación**: las adopciones S61-S63 quedan validadas pixel-level con R2 verdadero. Cierra deuda audit S67.
- **Estado**: CONFIRMADA / [PARCIAL si algún FAIL].
```

- [ ] **Step 2: Marcar pendiente cerrado en BLOQUE_ARRANQUE_S70**

En sección 3 "R2 retroactivos", reemplazar el bloque pendiente por:

```markdown
> **S70-1 RESUELTO (2026-05-20)**: R2 retroactivo aplicado a los 4 vols. Resultados en `experiments/122-125/` y entry `H_S70_R2_RETROACTIVO_4VOLS` en HYPOTHESIS_LOG.
```

- [ ] **Step 3: Commit**

```bash
git add docs/HYPOTHESIS_LOG.md tasks/BLOQUE_ARRANQUE_S70.md
git commit -m "S70-1 T5: consolidar R2 retroactivo 4 vols en docs"
```

---

### Task 6: Cleanup 14 workflows obsoletos

**Files:**
- Move: `.github/workflows/reproc-*.yml` (14 files) → `.github/workflows/_archive/`
- Create: `.github/workflows/_archive/README.md` (índice + razón de archive)

**Lista exacta** (de audit S70 final reviewer):
1. `reproc-villarrica-test1.yml`
2. `reproc-villarrica-test1-refs.yml`
3. `reproc-no-bt-path-15d.yml`
4. `reproc-ab-p3-1.yml`
5. `reproc-ab-test1.yml`
6. `reproc-ab-test1pix-filter.yml`
7. `reproc-d8-d4-per-vol-15d.yml`
8. `reproc-ab-d8-combo.yml`
9. `reproc-ab-d8-vent-anchored.yml`
10. `reproc-ab-h-d8-5.yml`
11. `reproc-ab-h8.yml`
12. `reproc-ndc-retry.yml`
13. `reproc-vent-anchored-30d-preview.yml`
14. `reproc-failed-tier-a.yml`

- [ ] **Step 1: Verificar lista contra disco**

```bash
ls .github/workflows/reproc-*.yml | wc -l
ls .github/workflows/reproc-*.yml
```

Esperable: 14 archivos (o conteo similar — el reviewer dijo 14, ajustar si hay variación).

- [ ] **Step 2: Mover a _archive/**

```bash
mkdir -p .github/workflows/_archive
git mv .github/workflows/reproc-villarrica-test1.yml .github/workflows/_archive/
git mv .github/workflows/reproc-villarrica-test1-refs.yml .github/workflows/_archive/
git mv .github/workflows/reproc-no-bt-path-15d.yml .github/workflows/_archive/
git mv .github/workflows/reproc-ab-p3-1.yml .github/workflows/_archive/
git mv .github/workflows/reproc-ab-test1.yml .github/workflows/_archive/
git mv .github/workflows/reproc-ab-test1pix-filter.yml .github/workflows/_archive/
git mv .github/workflows/reproc-d8-d4-per-vol-15d.yml .github/workflows/_archive/
git mv .github/workflows/reproc-ab-d8-combo.yml .github/workflows/_archive/
git mv .github/workflows/reproc-ab-d8-vent-anchored.yml .github/workflows/_archive/
git mv .github/workflows/reproc-ab-h-d8-5.yml .github/workflows/_archive/
git mv .github/workflows/reproc-ab-h8.yml .github/workflows/_archive/
git mv .github/workflows/reproc-ndc-retry.yml .github/workflows/_archive/
git mv .github/workflows/reproc-vent-anchored-30d-preview.yml .github/workflows/_archive/
git mv .github/workflows/reproc-failed-tier-a.yml .github/workflows/_archive/
```

GitHub Actions ignora archivos en subdirectorios de `.github/workflows/`, por lo que el archive es funcional.

- [ ] **Step 3: README de archive**

```bash
cat > .github/workflows/_archive/README.md <<'EOF'
# Workflows archivados — S70-1 (2026-05-20)

Los workflows en este directorio son experimentales A/B históricos de sesiones S15-S40.
Todos están **archivados** porque sus features fueron adoptadas en `mirova_equivalent` operacional
o refutadas. NO se ejecutan (GitHub Actions ignora subdirectorios de `.github/workflows/`).

## Por qué archivar en lugar de borrar

Historia metodológica: cada workflow representa un A/B real (data + decisión).
Mantenerlos accesibles facilita auditoría retroactiva si surge la pregunta "qué se probó".

## Lista archivada (14 archivos)

[Lista con 1 línea por workflow describiendo qué A/B testeaba]

## Cómo restaurar uno si se necesita

```bash
git mv .github/workflows/_archive/<nombre>.yml .github/workflows/
git commit -m "Restaurar workflow <nombre> para [razón]"
```
EOF
```

Editar el README llenando las descripciones de cada workflow (1 línea c/u — leer el header de cada yml para identificar el A/B test).

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/_archive/
git commit -m "S70-1 T6: archivar 14 workflows obsoletos (reproc-* S15-S40)"
```

---

## Checkpoint cierre S70-1

- [ ] R2 Chaiten: PASS/FAIL claro en results.json
- [ ] R2 Villarrica: PASS/FAIL claro
- [ ] R2 PP: PASS/FAIL claro
- [ ] R2 PCC: PASS/FAIL claro
- [ ] HYPOTHESIS_LOG H_S70_R2_RETROACTIVO_4VOLS entry creada
- [ ] BLOQUE_ARRANQUE_S70 marcado deuda cerrada
- [ ] 14 workflows movidos a _archive/

Cuando todos los checkpoints ✓: PR `s70-1-r2-retroactivo → main`.

---

## Self-review

**Spec coverage**: ✅ 4 R2 + consolidación + cleanup workflows. Goldens se difieren (depende NRT cron post-merge PR #103).

**Placeholders**: ratios target están como `[X]×` y resultados como `[N]` — son intencionales (los implementers llenan con valores reales al ejecutar). Pero el patrón está claro.

**Sin gaps detectados.**

---

## Cierre S70-1 (2026-05-20)

**Tasks completadas**: T1 Chaiten + T1.5 sensitivity + T2 Villarrica + T3 PP + T4 PCC + T5 consolidación.

**Commits**:
- `1583281` T1 Chaiten
- `ee37e51` T1.5 sensitivity ampliada
- `67a7a36` T2 Villarrica
- `fc48ede` T3 PP
- `7adb87d` T4 PCC
- [SHA T5] T5 consolidación docs

**Verdict global**: 5/5 Tier A R2 evaluados. Deuda audit S67 cerrada bajo gates apropiadas al régimen del vol.

**Próximo bloque**: T6 archivar 14 workflows obsoletos (pendiente en plan).
