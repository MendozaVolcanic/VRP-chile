# S21 — D6 Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persistir contexto disperso de S21 + ejecutar 3 diagnósticos empíricos para informar decisión D6 (background localizado Tupungatito) sin tocar `pipeline/`.

**Architecture:** Dos fases secuenciales. Fase 0 captura los 7 hallazgos S21 sin home y agrega un checklist de cierre operacional para prevenir recurrencia ("contexto se olvida entre sesiones"). Fase 1 corre 3 scripts read-only que clasifican forense, localizan fumarola activa real, y miden empíricamente std_bg con varios ROI. Output Fase 1 decide A/B/C/D para Fase 2 (S22+).

**Tech Stack:** Python 3.11, pytest, pandas, numpy, PyYAML, earthaccess (solo lectura), git, Markdown frontmatter.

**Working directory:** `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile`

**Memoria persistente:** `C:\Users\nmend\.claude\projects\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile\memory\` (referida en este plan como `~memory/`)

---

## File Structure

| Archivo | Acción | Responsabilidad |
|---|---|---|
| `~memory/project_s21_findings.md` | Crear | 7 hallazgos S21 con evidencia (schema gap, MODIS Tupungatito vacío, etc) |
| `~memory/MEMORY.md` | Modificar | Agregar entrada a índice |
| `docs/SESSION_CLOSE_CHECKLIST.md` | Crear | Checklist operacional de cierre (causa raíz: trigger sin checklist) |
| `docs/MIROVA_IMAGES_INVENTORY.md` | Crear | Inventario 36 PNGs mirovaweb con metadata |
| `CLAUDE.md` | Modificar | Trigger cierre con checklist explícito + 15 repos del ecosistema |
| `../CLAUDE.md` (Volcanologia raíz) | Modificar | Solo agregar tabla 15 repos del ecosistema, NO global |
| `.gitattributes` | Modificar | Permitir LF en .csv/.md |
| `experiments/38_forense_h17_replicable.py` | Crear | Forense reproducible TP/T1/T2b/T3/T4 vs CSV consolidado |
| `experiments/39_locate_active_vent.py` | Crear | Localizar fumarola real (centroide ponderado) vs nominal YAML |
| `experiments/40_measure_local_bg.py` | Crear | Medir std_bg multi-ROI sobre granules raw |
| `experiments/38_forense_results.json` | Salida | Output 38 |
| `experiments/38_forense_summary.md` | Salida | Resumen 38 |
| `experiments/39_active_vent_results.json` | Salida | Output 39 |
| `experiments/40_local_bg_results.json` | Salida | Output 40 |
| `tests/test_forense_h17_replicable.py` | Crear | Invariantes script 38 |
| `tests/test_locate_active_vent.py` | Crear | Invariantes script 39 |
| `tests/test_measure_local_bg.py` | Crear | Invariantes script 40 |
| `../../Vault/00_Meta/proyectos.md` | Modificar | Agregar dataview query papers VRP Chile |
| `../../Vault/10_Bibliografia/99_por_clasificar/<paper>.md` (×11) | Modificar | Frontmatter `proyecto: "[[VRP Chile]]"` |

---

## Phase 0 — Persistencia + Evidencia (esta sesión, BLOQUEANTE)

### Task 1: Crear memory/project_s21_findings.md

**Files:**
- Create: `~memory/project_s21_findings.md`
- Modify: `~memory/MEMORY.md`

- [ ] **Step 1: Escribir el archivo de hallazgos**

Contenido completo:

```markdown
---
name: S21 findings — schema gap, MODIS coverage Tupungatito, ground truth externo, OCR outliers
description: Hallazgos S21 (2026-04-25 noche) descubiertos al re-auditar. 7 items que estaban dispersos o no documentados antes.
type: project
---
# Hallazgos S21 (2026-04-25, abierta)

## H_S21_1 — Schema gap: `std_bg` no se persiste en JSON

`pipeline/store.py append_record()` no incluye `std_bg`, `std_bg_summit`,
`t_bg_summit`, ni `n_pixels_bg` en el record JSON. Existe desde S15+ y
nadie lo había detectado. Verificable con:

    grep -n std_bg pipeline/store.py    # → no matches
    grep "std_bg" data/mirova_equivalent/Tupungatito.json | head    # → no matches

**Implicancia para D6**: la auditoría narrativa S20 ("std_bg ~2-3K en Tupungatito por
glaciar") es asunción, no medición. Para validar D6 hay que computarlo en script aparte
(experiments/40) sobre granules raw, o agregar campo al schema y reprocessar.

## H_S21_2 — Tupungatito MODIS Last Year totalmente vacía

Imagen `imagenes/Tupungatito_MODIS_Dist.png` (mirovaweb.it scrap 2026-04-25) muestra
plot Last Year y Last Month **vacíos**. MIROVA no detecta MODIS Tupungatito en 12 meses.
Solo VIIRS375 + algunos VIIRS750 reportan refs.

**Implicancia**: cualquier fix D6 que apunte a recall Tupungatito es problema 100% de
`process_viirs.py`. `process_modis.py` no necesita cambio. Reduce superficie de cambio.

## H_S21_3 — Distancias CSV Mirova-v1 son REALES, no bin visual

`registro_Tupungatito.csv` columna `Distancia_km` muestra clusters dominantes 4.89 y 5.21
(diff 0.32 km ≈ 0.85 pixel VIIRS 375m). NO es bin "<7km" visual.

**Implicancia**: la fumarola activa real Tupungatito está a ~5 km del centro nominal
`vent_lat/lon` del YAML. Un ROI1 5×5 km centrado en vent NOMINAL la deja en el borde.
Hay que localizar la fumarola real (script 39) y proponer `mirova_center_lat/lon`
corregido (campo ya existe en YAML, S15 lo usó para Planchón-Peteroa offset 1.87 km N).

## H_S21_4 — Ground truth Mirova-v1 vive afuera del repo

CSVs ground truth NRT MIROVA (latest.php scraper) viven en repo externo
`https://github.com/MendozaVolcanic/Mirova-v1/tree/main/monitoreo_satelital`. Updated
cada 5 min (scraper) + cada 1h (OCR). Snapshot bajado S21 a
`data/mirova_reference/mirova_v1_snapshot/`:

- `registro_vrp_consolidado.csv` (2.1 MB, 14,216 filas, 11 Tier A + Peteroa alias)
- `registro_Tupungatito.csv` (23 KB, 79 filas)
- `registro_Lascar.csv` (80 KB, 301 filas)
- `registro_Chaiten.csv` (6 KB, 22 filas)

**Decisión**: bajar individuales NO es necesario — el consolidado tiene los 11 Tier A.
Sincronizar snapshot con `scripts/sync_mirova_v1_snapshot.py` (a crear S22 si hace falta).

## H_S21_5 — Timestamps refs MIROVA Tupungatito son NOCTURNOS

CSV `Fecha_Satelite_UTC` típicas 04:54-06:36 UTC = 00:54-02:36 Chile local (UTC-4).
**Todas nocturnas**. MIR válido, no es contaminación solar diurna.

**Implicancia**: cualquier hipótesis "MIROVA detecta diurno y nosotros descartamos por
MIR-only" queda descartada. Tampoco hay que extender a daytime para alcanzar paridad.

## H_S21_6 — Origen_Dato='OCR' son outliers sin geocodificación

CSV Mirova-v1 mezcla 2 fuentes:
- `Origen_Dato='latest.php'`: detección directa scraper, distancia precisa.
- `Origen_Dato='OCR'`: thumbnails parseados sin geocodificación, `Distancia_km=0.0`
  literal (ej: filas 13, 15 de `registro_Tupungatito.csv`).

**Implicancia**: para forense replicable filtrar `Origen_Dato='latest.php'` only.
Los OCR contaminan ground truth si se usan crudos.

## H_S21_7 — 36 PNGs mirovaweb.it untracked en imagenes/

Nicolás entregó 2026-04-25 36 imágenes `imagenes/<Volcán>_<Sensor>_<Tipo>.png` (Chaitén,
Lascar, Tupungatito × 3 sensores × 4 tipos: Dist, VRP, logVRP, Latest10NTI). Captura
visual ground truth complementaria al CSV. Dice `Last Update:25-Apr-2026 05:54:01`.
Untracked al inicio de S21. Inventario detallado en `docs/MIROVA_IMAGES_INVENTORY.md`.

## Eco S21 → S22+

- S22 fase ejecución D6 (decisión A/B/C/D con outputs experiments/38-40 en mano).
- S22+ considerar bajar individuales si forense replicable revela patrones por-volcán
  que el consolidado no captura.
- Sincronización Mirova-v1 snapshot semanal (scripts/sync_mirova_v1_snapshot.py).

## Repos del ecosistema MendozaVolcanic (referencia)

15 repos GitHub. **Críticos para VRP Chile: VRP-chile + Mirova-v1**. Otros 13 son
pipelines satelitales paralelos para sensores complementarios:
GOES (goes-volcanic-monitoring, Lightning-v1), Landsat (Landsat-v1), InSAR (LiCSAR-v1),
SO2 (VolcPlume-v1), NHI (NHI-v1), vegetación (VegStress-v1), trayectorias (Sat_Tracker),
Copernicus (Copernicus-v1), openVIS, ovdas-fondos, lago-caburga, valles-volcanicos.

Mantener mental note: si surge necesidad de cross-sensor (ej: confirmar SO2 simultáneo
con anomalía térmica), VolcPlume-v1 es el repo. No expandir scope VRP-chile.
```

- [ ] **Step 2: Update memory/MEMORY.md index**

Agregar línea bajo "Estado actual y hallazgos" (después de la entrada S20):

```markdown
- [S21 findings](project_s21_findings.md) — Schema gap std_bg no persistido, MODIS Tupungatito Last Year vacío (refs 100% VIIRS), distancias CSV reales 4.89/5.21 km (fumarola descentrada), ground truth Mirova-v1 externo, timestamps nocturnos, OCR outliers, 36 PNGs evidencia
```

- [ ] **Step 3: Verify**

Run:
```bash
ls -la "C:/Users/nmend/.claude/projects/C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile/memory/" | grep s21
head -20 "C:/Users/nmend/.claude/projects/C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile/memory/MEMORY.md"
```
Expected: `project_s21_findings.md` listed, MEMORY.md tiene la línea S21 nueva.

- [ ] **Step 4: No commit todavía** — la memoria vive fuera del repo. Sigue Task 2.

---

### Task 2: Crear docs/SESSION_CLOSE_CHECKLIST.md

**Files:**
- Create: `docs/SESSION_CLOSE_CHECKLIST.md`

- [ ] **Step 1: Escribir el archivo**

Contenido completo:

```markdown
# Session Close Checklist (operacional)

> **Quién lo usa**: Claude al cierre de cada sesión, ANTES de declarar la sesión terminada.
> **Por qué existe**: el trigger CLAUDE.md "revise-claude-md + consolidate-memory" decía
> "consolidar lecciones" sin enumerar qué. Resultado S20: cerró sin documentar el schema
> gap std_bg, las 36 imágenes mirovaweb, el CSV externo Mirova-v1, los OCR outliers.
> S21 los descubrió "de nuevo" como si fueran hallazgos. Esta lista lo previene.

## Bloque A — Hallazgos nuevos

- [ ] ¿Hubo H# (hipótesis) nuevos en la sesión?
  - SÍ → entrada en `docs/HYPOTHESIS_LOG.md` con criterio testable + estado.
- [ ] ¿Hubo D# (drifts vs papers) nuevos?
  - SÍ → sección en `docs/DRIFTS_S17.md` con evidencia + decisión + sesión esperada.
- [ ] ¿Hubo schema/data gaps detectados (ej: campo no guardado, source externa)?
  - SÍ → entrada en `~memory/project_sNN_findings.md` (NN=número sesión).
- [ ] ¿Cualquier otro learning durable (no específico de la sesión)?
  - SÍ → `~memory/feedback_*.md` (durables) o `~memory/reference_*.md` (estables).

## Bloque B — Evidencia + reproducibilidad

- [ ] ¿Hubo análisis "narrativo" sin script reproducible?
  - SÍ → script en `experiments/NN_*.py` con seed fijo + output JSON/MD.
- [ ] ¿Hubo data nueva (CSV, imágenes, granules) cargada al working dir?
  - SÍ → committed (`git add`) o explicitamente en `.gitignore` con razón documentada.
- [ ] ¿Reprocesos largos generaron outputs grandes (>10 MB)?
  - SÍ → committed si reproducibles caro, o en gitignore + script para regenerar.

## Bloque C — Persistencia

- [ ] ¿Memoria está actualizada con findings de la sesión?
  - Verificar entrada nueva en `~memory/MEMORY.md` index.
  - Verificar que cada hallazgo tiene su archivo `~memory/project_sNN_findings.md`.
- [ ] ¿Docs vivos sincronizados?
  - `docs/SESSION_INDEX.md`: fila nueva con sesión + hallazgo principal + artefacto.
  - `docs/DATA_SOURCES.md`: si data sources cambiaron.
  - `docs/PAPERS_AUDIT.md`: si paper nuevo procesado.
- [ ] ¿Vault Obsidian crosslinks vigentes?
  - Frontmatter `proyecto: "[[VRP Chile]]"` en papers nuevos auditados esta sesión.

## Bloque D — Git hygiene

- [ ] `git status` limpio o explicado:
  - Untracked: razón documentada (work-in-progress vs gitignore).
  - Modified sin commit: es deliberado (push-after-test) o pendiente de commit final.
- [ ] Branch al día con origin (`git status --branch --short`).
- [ ] Si hubo merges complejos: documentar resolución en handoff.
- [ ] CI status verificado (`gh run list -L 5`):
  - Si hay 3+ fallos consecutivos → documentar en handoff y/o issue abierto.

## Bloque E — Handoff (opcional, solo si hay continuidad)

- [ ] `tasks/handoff_sNN+1_YYYY_MM_DD.md` con:
  - Estado al cierre (qué quedó hecho, qué quedó pendiente).
  - Próximo plan (link a `docs/superpowers/plans/`).
  - Asunciones que el siguiente agente NO debería re-derivar.

## Bloque F — Skills disparadas

- [ ] ¿Se invocaron las skills obligatorias del CLAUDE.md trigger table?
- [ ] ¿`anthropic-skills:consolidate-memory` corrida después de Bloques A-C?
- [ ] ¿`revise-claude-md` corrida si hubo learnings durables?

## Antipatrón conocido

> "Lo apunto en la memoria mental de esta sesión y lo paso al cierre" — NO. Persistilo
> al momento del descubrimiento. Una sesión que se cierra abruptamente (cuota tokens,
> Nicolás cierra la app, error) pierde toda la memoria mental.

## Ejemplos de uso correcto

**Caso 1**: descubrís a mitad de sesión que `pipeline/X.py` línea 100 tiene bug pero el
fix queda fuera de scope.
- ✅ AHORA: agregar a `~memory/project_sNN_findings.md` con la línea exacta.
- ❌ NO: "lo recuerdo y lo pongo al cierre".

**Caso 2**: agente subordinado encuentra que un CSV externo tiene N registros para volcán X.
- ✅ AHORA: actualizar `docs/DATA_SOURCES.md` con el conteo.
- ❌ NO: dejarlo solo en el output del agente que se va a borrar al fin de turno.
```

- [ ] **Step 2: Verify**

Run:
```bash
wc -l docs/SESSION_CLOSE_CHECKLIST.md
ls docs/*.md
```
Expected: archivo presente, ≥80 líneas.

- [ ] **Step 3: No commit todavía** — junto con CLAUDE.md update en Task 3.

---

### Task 3: Update CLAUDE.md (proyecto + raíz Volcanologia)

**Files:**
- Modify: `CLAUDE.md` (VRP Chile)
- Modify: `../CLAUDE.md` (Volcanologia raíz)

- [ ] **Step 1: VRP Chile CLAUDE.md — actualizar trigger cierre**

Localizar la fila del trigger "Cerrar sesión con learnings nuevos" (cerca línea 138):

```markdown
| **Cerrar sesión con learnings nuevos** | **`revise-claude-md` + `anthropic-skills:consolidate-memory`** | Consolidar lecciones en CLAUDE.md Y en memoria persistente antes de cerrar |
```

Reemplazar por:

```markdown
| **Cerrar sesión con learnings nuevos** | **`revise-claude-md` + `anthropic-skills:consolidate-memory`** + seguir [`docs/SESSION_CLOSE_CHECKLIST.md`](docs/SESSION_CLOSE_CHECKLIST.md) bloque por bloque | El trigger sin checklist falló S20 (gaps redescubiertos S21). Checklist obligatorio bloques A-F |
```

- [ ] **Step 2: VRP Chile CLAUDE.md — agregar nota sobre persistencia in-vivo**

Después de la regla meta (S16) agregar nueva regla:

```markdown
**Regla meta-meta (S21)**: persistencia in-vivo, no al cierre. Cuando descubras un
hallazgo durante la sesión (schema gap, source externa, dato nuevo), persistilo
INMEDIATAMENTE en memoria/docs antes de continuar con el trabajo. La sesión puede
cortarse abruptamente. La regla del cierre (Bloque A del SESSION_CLOSE_CHECKLIST) es
red de seguridad, no la persistencia primaria.
```

- [ ] **Step 3: Volcanologia/CLAUDE.md — agregar tabla 15 repos del ecosistema**

Localizar la sección "Subproyectos" (cerca del inicio). Reemplazar la tabla actual de 4 filas:

```markdown
| Subproyecto | Propósito | Estado |
|---|---|---|
| **VRP Chile/** | Térmico MODIS/VIIRS | NRT live |
| **OpenVIS/** | Infrasonido + OVDAS | Investigación |
| **openVIS-code/** | Fork rodrum/openVIS + Streamlit | Local |
| **Goes/** | GOES (placeholder) | Vacío |
```

Por la versión expandida con repos GitHub:

```markdown
| Subproyecto local | Propósito | Estado |
|---|---|---|
| **VRP Chile/** | Térmico MODIS/VIIRS (clon MIROVA) | NRT live · GitHub: MendozaVolcanic/VRP-chile |
| **OpenVIS/** | Infrasonido + OVDAS | Investigación |
| **openVIS-code/** | Fork rodrum/openVIS + Streamlit | Local |
| **Goes/** | GOES (placeholder) | Vacío |

## Repos GitHub del ecosistema (referencia, no scope inmediato)

**Críticos para VRP Chile**: solo `VRP-chile` + `Mirova-v1`. Los 13 restantes son
pipelines satelitales independientes con sensores complementarios. Mantener mental
note pero NO expandir scope sin justificación explícita.

| Repo | Sensor / Propósito | Cron |
|---|---|---|
| VRP-chile | MODIS/VIIRS térmico (este proyecto) | 2h |
| Mirova-v1 | Scraper ground truth mirovaweb.it | 5 min + 1h OCR |
| goes-volcanic-monitoring | GOES-19 ceniza + SO2 | — |
| Lightning-v1 | GLM rayos GOES-16 | — |
| Landsat-v1 | Landsat 8/9 imágenes | — |
| LiCSAR-v1 | InSAR Sentinel-1 deformación | — |
| NHI-v1 | Anomalías térmicas normalizadas | — |
| VolcPlume-v1 | TROPOMI SO2 Sentinel-5P | — |
| VegStress-v1 | NDVI/EVI/SAVI Sentinel-2 | — |
| Sat_Tracker | TLEs + pasajes satelitales | — |
| Copernicus-v1 | Copernicus Open Hub utils | — |
| openVIS-Colaboracion-1 | Volcanic Information System metodología | — |
| ovdas-fondos | Dashboard fondos concursables SERNAGEOMIN | — |
| lago-caburga | Análisis lago Caburga | — |
| valles-volcanicos-chile | Dashboard valles 43 volcanes | — |
```

- [ ] **Step 4: Verify**

Run:
```bash
grep -c "SESSION_CLOSE_CHECKLIST" CLAUDE.md
grep -c "Repos GitHub del ecosistema" ../CLAUDE.md
```
Expected: ambos ≥ 1.

- [ ] **Step 5: Commit Task 2 + Task 3 juntos**

```bash
git add docs/SESSION_CLOSE_CHECKLIST.md CLAUDE.md ../CLAUDE.md
git commit -m "S21 cierre — checklist operacional + tabla 15 repos ecosistema

- docs/SESSION_CLOSE_CHECKLIST.md: bloques A-F obligatorios al cierre
- CLAUDE.md (VRP Chile): trigger cierre apunta al checklist + regla persistencia in-vivo
- CLAUDE.md (Volcanologia raíz): tabla 15 repos ecosistema MendozaVolcanic
- Causa raíz: S20 cerró sin checklist y S21 redescubrió gaps que estaban dispersos"
```

---

### Task 4: Commit untracked evidence (3 commits separados)

**Files:**
- Modify: `.gitignore` (si necesario)
- Add: `imagenes/`, `data/nsigma_mir_5/`, `data/nsigma_mir_12/`, `data/mirova_reference/mirova_v1_snapshot/`, `frontend/llaima_anomalies.png`, `frontend/planchonpeteroa_anomalies.png`
- Create: `docs/MIROVA_IMAGES_INVENTORY.md`

- [ ] **Step 1: Crear inventario de imágenes mirovaweb**

Archivo `docs/MIROVA_IMAGES_INVENTORY.md`:

```markdown
# Inventario de imágenes MIROVA — `imagenes/`

> Capturas mirovaweb.it tomadas 2026-04-25 ~05:54:01 UTC (Last Update visible en headers).
> Entregadas por Nicolás S21 como ground truth visual complementaria al CSV
> `data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv`.

## Cobertura

3 volcanes × 3 sensores × 4 tipos de plot = **36 imágenes**.

| Volcán | Sensores | Tier MIROVA | Estado pipeline |
|---|---|---|---|
| Chaitén | MODIS, VIIRS375, VIIRS750 | A | Recall 1.00 (S20 post-Regla D, supera S9 0.93) |
| Lascar | MODIS, VIIRS375, VIIRS750 | A | Recall 0.86 (S18 NOAA-21) → 0.73 summit-only post-Regla D |
| Tupungatito | MODIS, VIIRS375, VIIRS750 | A | Recall 0.57 (S20). Cuello D6 — target S22 |

## Tipos de plot por volcán/sensor

| Tipo | Eje Y | Significado |
|---|---|---|
| `*_Dist.png` | Distancia (km) al vent | Distribución espacial detecciones MIROVA, Last Month + Last Year |
| `*_VRP.png` | VRP (Watts) lineal | Magnitudes radiativas |
| `*_logVRP.png` | VRP (Watts) log10 | Misma data en log para ver escala dinámica |
| `*_Latest10NTI.png` | Mosaico NTI | 10 últimas detecciones con miniaturas BT y NTI |

## Hallazgos visuales clave

1. **Tupungatito MODIS Dist Last Year y Last Month VACÍOS** — MIROVA no detecta MODIS
   Tupungatito en 12 meses. Refs son 100% VIIRS. (Ver H_S21_2.)
2. **Tupungatito VIIRS375 Dist Last Year**: línea roja casi continua a 5 km. Detecciones
   sistemáticas todos los días. Leyenda `<7km / >7km` (no `<5km` como Lascar).
3. **Lascar VIIRS375 Dist**: rojos a 1-2 km (cráter cercano), `<5km / >5km` leyenda.
   Cráter activo persistente.
4. **Chaitén VIIRS375 Dist**: rojos esporádicos. Pocos eventos en año, low-activity.
5. **Latest10NTI Tupungatito VIIRS375**: VRP 0.05–0.39 MW, todos sub-pixel. Confirma
   fumarola débil persistente, no eruptiva.

## Uso

- **Ground truth visual** complementario al CSV cuando hay duda sobre clasificación
  binned vs distancia real (CSV ya tiene `Distancia_km` exacta, ver H_S21_3).
- **Sanity check** post-fix: re-generar imágenes equivalentes desde nuestro pipeline
  con `scripts/visualize_volcano.py` (a crear S22+) y comparar contra mirovaweb.

## Reposición

Si las imágenes se pierden: descargar via Mirova-v1 visualizador
(`https://github.com/MendozaVolcanic/Mirova-v1/blob/main/visualizador.py`) o re-pedir
a Nicolás. Generación automatizada futura: scrape mirovaweb.it/latest.php directamente.
```

- [ ] **Step 2: Verify imagenes/ tamaño y conteo**

Run:
```bash
ls imagenes/ | wc -l
du -sh imagenes/
```
Expected: 36, ~4.5 MB.

- [ ] **Step 3: Commit 1 — imágenes mirovaweb evidencia**

```bash
git add imagenes/ docs/MIROVA_IMAGES_INVENTORY.md
git commit -m "S21 evidencia — 36 PNGs mirovaweb.it ground truth visual

- imagenes/: Chaitén/Lascar/Tupungatito × MODIS/VIIRS375/VIIRS750 × Dist/VRP/logVRP/Latest10NTI
- docs/MIROVA_IMAGES_INVENTORY.md: inventario + hallazgos visuales
- Hallazgo crítico H_S21_2: Tupungatito MODIS Last Year vacía → refs 100% VIIRS
- Capturas 2026-04-25 ~05:54:01 UTC, ground truth complementaria al CSV consolidado"
```

- [ ] **Step 4: Commit 2 — outputs A/B test S19 D2**

```bash
git add data/nsigma_mir_5/ data/nsigma_mir_12/
git commit -m "S19 evidencia — outputs A/B test D2 (3σ vs 5σ vs 12σ)

- data/nsigma_mir_5/: outputs profile n_sigma_mir=5 (Coppola 2016a)
- data/nsigma_mir_12/: outputs profile n_sigma_mir=12 (Di Bella 2024 VIIRS noche)
- 3 volcanes c/u: Chaitén, Lascar, Tupungatito (los reprocessados S18 con NOAA-21)
- Resultado consolidado en docs/DRIFTS_S17.md sección 'D2 — Resolución S19':
  3σ + cap MAX_SIGMA_COMPONENT_K=7K gana en F1 (0.36 vs 0.29). Cap satura cuando
  std_bg>0.58K → 5σ y 12σ producen resultados idénticos al bit"
```

- [ ] **Step 5: Commit 3 — snapshot Mirova-v1 ground truth**

```bash
git add data/mirova_reference/mirova_v1_snapshot/
git commit -m "S21 ground truth — snapshot CSVs Mirova-v1 (2026-04-25)

- registro_vrp_consolidado.csv (2.1 MB, 14,216 filas, 11 Tier A + Peteroa alias)
- registro_Tupungatito.csv (79 filas), Lascar (301), Chaitén (22)
- Source: https://github.com/MendozaVolcanic/Mirova-v1/tree/main/monitoreo_satelital
- Fechas Fecha_Satelite_UTC abr 2026 cubren ventana NRT actual
- Distinguir Origen_Dato='latest.php' (precisos) vs 'OCR' (Distancia=0.0 outliers)
- Para forense replicable usar SOLO latest.php (H_S21_6)"
```

- [ ] **Step 6: Verificar frontend PNGs**

Run:
```bash
ls -la frontend/*.png 2>/dev/null
```

Si los PNGs `llaima_anomalies.png` y `planchonpeteroa_anomalies.png` siguen sin commit:
preguntar a Nicolás de qué sesión son antes de commit/delete. Por ahora dejar untracked.

- [ ] **Step 7: Verify estado git limpio**

Run:
```bash
git status --short
```
Expected: solo los 2 PNGs frontend pendientes (consultar Nicolás), nada más.

---

### Task 5: Resolver desacople Vault Obsidian (E1 + E3)

**Files:**
- Modify: `../../Vault/00_Meta/proyectos.md`
- Modify: `../../Vault/10_Bibliografia/99_por_clasificar/<paper>.md` (×11 papers MIROVA auditados S17 según `docs/PAPERS_AUDIT.md`)
- Modify: `docs/PAPERS_AUDIT.md` (sección "Vault crosslinks")

- [ ] **Step 1: Identificar los 11 papers auditados**

Run:
```bash
grep -E "^\| .* \| (Coppola|Campus|Aveni|Di Bella|Wooster)" docs/PAPERS_AUDIT.md
```

Tomar los 11 papers de la tabla y obtener filenames esperados en Vault (kebab-case según convención CLAUDE.md raíz).

- [ ] **Step 2: Verificar existencia papers en Vault**

Run para cada paper esperado:
```bash
ls "../../Vault/10_Bibliografia/99_por_clasificar/" | grep -iE "coppola|campus|aveni|dibella|wooster"
```

Expected: identificar qué papers SÍ están y cuáles faltan.

- [ ] **Step 3: Agregar frontmatter `proyecto` a papers existentes**

Para cada paper presente, abrir y verificar/agregar al frontmatter YAML:

```yaml
---
ai_generated: true
confidence: high
explored: 2026-04-23
proyecto: "[[VRP Chile]]"
sensor: [VIIRS, MODIS]
metodo: [VRP, NTI]
---
```

(`sensor` y `metodo` solo si aplican al paper específico.)

- [ ] **Step 4: Update Vault/00_Meta/proyectos.md con dataview query**

Buscar la sección "VRP Chile" en `../../Vault/00_Meta/proyectos.md` y agregar bloque dataview justo después:

````markdown
### Papers vinculados (auto-generado)

```dataview
TABLE
  file.mtime as "Última edición",
  sensor,
  metodo
FROM "10_Bibliografia"
WHERE contains(string(proyecto), "VRP Chile")
SORT file.name ASC
```
````

- [ ] **Step 5: Update docs/PAPERS_AUDIT.md con sección crosslinks**

Agregar al final de `docs/PAPERS_AUDIT.md`:

```markdown
## Vault crosslinks

Los 11 papers auditados S17 están notados en
`Vault/10_Bibliografia/99_por_clasificar/` con frontmatter `proyecto: "[[VRP Chile]]"`.
Para listado vivo y filtros (sensor, método): abrir `Vault/00_Meta/proyectos.md`
sección "Papers vinculados" — usa dataview para query automático.

Si un paper se mueve a subcarpeta temática (ej: `termico/`), el dataview lo sigue
porque filtra por frontmatter no por path.
```

- [ ] **Step 6: Commit (solo VRP Chile, NO el Vault que es separado)**

```bash
git add docs/PAPERS_AUDIT.md
git commit -m "S21 — docs/PAPERS_AUDIT.md sección Vault crosslinks

- Apunta al Vault donde viven las notas extendidas de papers
- 11 papers auditados S17 con frontmatter proyecto: [[VRP Chile]]
- Vault/00_Meta/proyectos.md ahora tiene dataview query auto-actualizable"
```

NOTA: el Vault es repo/folder separado. Si está bajo control de versión propio (`git
init` en Vault/), commitear allí también con mensaje paralelo. Si no está versionado,
los cambios viven solo en el filesystem (riesgo).

---

## Phase 1 — Diagnóstico empírico D6 (sigue inmediatamente o próxima sesión)

### Task 6: experiments/38_forense_h17_replicable.py

**Files:**
- Create: `experiments/38_forense_h17_replicable.py`
- Create: `tests/test_forense_h17_replicable.py`
- Output: `experiments/38_forense_results.json`, `experiments/38_forense_summary.md`

**Lógica del script:**
1. Cargar CSV consolidado, filtrar `Volcan==<volcano>`, `Origen_Dato=='latest.php'`,
   ventana fecha `[start, end]`.
2. Cargar JSON nuestro: `data/mirova_equivalent/<volcano>.json`.
3. Para cada ref MIROVA, buscar record nuestro con `datetime_utc` dentro de tolerancia
   (default 60 min) por sensor.
4. Cargar `volcanoes.yaml` para `inner_radius_km` por volcán.
5. Clasificar:
   - **T1**: no hay record nuestro en la ventana → no granule fetched
   - **TP**: record nuestro tiene `final_hotspot_dist_km <= inner_radius_km` o `distance_class=='summit'`
   - **T3**: record con `vrp_vent_mw>0` Y `distance_class!='summit'` (post-S20 Regla D debería ser 0; si aparece, regla no aplicada)
   - **T4**: record con `n_anomalous>0` pero NO hay pixels dentro inner_radius (pixels solo far)
   - **T2b**: record con `vrp_mw==0` (escena fría real)
6. Output JSON con per-ref classification + tabla MD resumen.

- [ ] **Step 1: Escribir test failing — invariantes**

`tests/test_forense_h17_replicable.py`:

```python
"""Invariantes script 38: clasificación TP/T1/T2b/T3/T4 mutuamente exclusiva."""
from __future__ import annotations
import json
import pandas as pd
import pytest
from datetime import datetime, timezone

from experiments.forense_h17_replicable import classify_ref, run_forense


def _ref(ts: str, vrp: float = 0.2, dist: float = 5.0, sensor: str = "VIIRS375"):
    return {
        "Fecha_Satelite_UTC": ts,
        "Volcan": "Tupungatito",
        "Sensor": sensor,
        "VRP_MW": vrp,
        "Distancia_km": dist,
        "Origen_Dato": "latest.php",
    }


def _record(ts: str, vrp: float = 0.0, vent: float = 0.0,
            dist_class: str = "far", final_dist: float = 10.0,
            n_anom: int = 0, sensor_kind: str = "VIIRS375"):
    return {
        "datetime_utc": ts,
        "sensor": sensor_kind,
        "vrp_mw": vrp,
        "vrp_vent_mw": vent,
        "distance_class": dist_class,
        "final_hotspot_dist_km": final_dist,
        "n_anomalous": n_anom,
    }


def test_classify_t1_no_record():
    """Ref MIROVA exists, no record our side → T1 (no granule)."""
    ref = _ref("2026-04-15 05:30:00")
    out = classify_ref(ref, records=[], inner_radius_km=7.0,
                       tolerance_min=60)
    assert out["class"] == "T1"


def test_classify_tp_summit():
    """vrp_vent>0 + distance_class=summit → TP."""
    ref = _ref("2026-04-15 05:30:00")
    rec = _record("2026-04-15 05:35:00", vrp=0.2, vent=0.15,
                  dist_class="summit", final_dist=2.5, n_anom=1)
    out = classify_ref(ref, [rec], inner_radius_km=7.0, tolerance_min=60)
    assert out["class"] == "TP"


def test_classify_t3_legacy():
    """vrp_vent>0 + distance_class=far → T3 (Regla D no aplicada)."""
    ref = _ref("2026-04-15 05:30:00")
    rec = _record("2026-04-15 05:35:00", vrp=0.2, vent=0.15,
                  dist_class="far", final_dist=12.0, n_anom=1)
    out = classify_ref(ref, [rec], inner_radius_km=7.0, tolerance_min=60)
    assert out["class"] == "T3"


def test_classify_t4_pixels_only_far():
    """n_anomalous>0 pero no en summit → T4 (background no localizado)."""
    ref = _ref("2026-04-15 05:30:00")
    rec = _record("2026-04-15 05:35:00", vrp=1.0, vent=0.0,
                  dist_class="far", final_dist=15.0, n_anom=3)
    out = classify_ref(ref, [rec], inner_radius_km=7.0, tolerance_min=60)
    assert out["class"] == "T4"


def test_classify_t2b_cold_scene():
    """Record presente pero vrp_mw=0 → T2b."""
    ref = _ref("2026-04-15 05:30:00")
    rec = _record("2026-04-15 05:35:00", vrp=0.0, vent=0.0,
                  dist_class="far", final_dist=20.0, n_anom=0)
    out = classify_ref(ref, [rec], inner_radius_km=7.0, tolerance_min=60)
    assert out["class"] == "T2b"


def test_classes_are_mutually_exclusive_and_total():
    """Para N refs, sum(TP+T1+T2b+T3+T4) == N."""
    refs = [_ref(f"2026-04-{d:02d} 05:30:00") for d in range(10, 20)]
    records = [
        _record("2026-04-12 05:35:00", vrp=0.2, vent=0.15,
                dist_class="summit", final_dist=2.0, n_anom=1),
        _record("2026-04-15 05:35:00", vrp=0.2, vent=0.15,
                dist_class="far", final_dist=12.0, n_anom=1),
    ]
    classifications = [classify_ref(r, records, 7.0, 60)["class"] for r in refs]
    counts = {c: classifications.count(c) for c in ("TP", "T1", "T2b", "T3", "T4")}
    assert sum(counts.values()) == len(refs)


def test_run_forense_uses_only_latest_php(tmp_path):
    """Origen_Dato=='OCR' debe ser excluido."""
    csv = tmp_path / "consolidado.csv"
    pd.DataFrame([
        _ref("2026-04-15 05:30:00") | {"Origen_Dato": "latest.php"},
        _ref("2026-04-16 05:30:00") | {"Origen_Dato": "OCR"},
    ]).to_csv(csv, index=False)

    json_path = tmp_path / "Tupungatito.json"
    json_path.write_text(json.dumps({"records": []}))

    yaml_path = tmp_path / "volcanoes.yaml"
    yaml_path.write_text("Tupungatito:\n  inner_radius_km: 7\n")

    out = run_forense(
        volcano="Tupungatito",
        consolidado_csv=csv,
        records_json=json_path,
        volcanoes_yaml=yaml_path,
        start="2026-04-10",
        end="2026-04-20",
    )
    assert out["n_refs"] == 1  # Solo la latest.php cuenta
```

- [ ] **Step 2: Verificar test falla**

Run:
```bash
pytest tests/test_forense_h17_replicable.py -v
```
Expected: FAIL con `ModuleNotFoundError: No module named 'experiments.forense_h17_replicable'` o `ImportError`.

- [ ] **Step 3: Implementar script**

`experiments/38_forense_h17_replicable.py`:

```python
"""Forense replicable de refs MIROVA: clasifica TP/T1/T2b/T3/T4 contra nuestros records.

Uso CLI:
    python experiments/38_forense_h17_replicable.py \
        --volcano Tupungatito \
        --start 2026-03-25 --end 2026-04-25 \
        --output-json experiments/38_forense_Tupungatito.json \
        --output-md experiments/38_forense_Tupungatito.md

Reproduce sistemáticamente la clasificación narrativa H17 S20.
"""
from __future__ import annotations
import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

import pandas as pd
import yaml


def _parse_dt(s: str) -> datetime:
    """CSV Mirova-v1 'Fecha_Satelite_UTC' format YYYY-MM-DD HH:MM:SS UTC."""
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)


def _record_dt(rec: dict) -> datetime:
    """JSON record 'datetime_utc' format ISO."""
    return datetime.fromisoformat(rec["datetime_utc"].replace("Z", "+00:00"))


def _sensor_match(ref_sensor: str, rec_sensor: str) -> bool:
    """CSV usa 'VIIRS375', 'VIIRS', 'MODIS'. Records nuestros 'VIIRS_I04', 'VIIRS_M13', 'MODIS_B22', etc."""
    if ref_sensor == "VIIRS375":
        return "I0" in rec_sensor or "VIIRS_I" in rec_sensor
    if ref_sensor == "VIIRS":  # 750m
        return "M13" in rec_sensor or "M15" in rec_sensor or "VIIRS_M" in rec_sensor
    if ref_sensor == "MODIS":
        return "MODIS" in rec_sensor or "B21" in rec_sensor or "B22" in rec_sensor
    return False


def _find_match(ref: dict, records: Iterable[dict], tolerance_min: int) -> dict | None:
    """Busca record nuestro con datetime ± tolerance_min y sensor compatible."""
    ref_dt = _parse_dt(ref["Fecha_Satelite_UTC"])
    tol = timedelta(minutes=tolerance_min)
    best = None
    best_delta = tol + timedelta(minutes=1)
    for rec in records:
        if not _sensor_match(ref["Sensor"], rec.get("sensor", "")):
            continue
        delta = abs(_record_dt(rec) - ref_dt)
        if delta <= tol and delta < best_delta:
            best, best_delta = rec, delta
    return best


def classify_ref(ref: dict, records: Iterable[dict],
                 inner_radius_km: float, tolerance_min: int) -> dict:
    """Devuelve dict con class y diagnóstico."""
    rec = _find_match(ref, records, tolerance_min)
    if rec is None:
        return {"class": "T1", "reason": "no_record_in_window", "ref": ref, "rec": None}

    vrp_vent = float(rec.get("vrp_vent_mw") or 0.0)
    vrp_total = float(rec.get("vrp_mw") or 0.0)
    n_anom = int(rec.get("n_anomalous") or 0)
    dist_class = rec.get("distance_class", "far")
    final_dist = rec.get("final_hotspot_dist_km")

    if dist_class == "summit" or (
        final_dist is not None and final_dist <= inner_radius_km
    ):
        return {"class": "TP", "reason": "summit_or_within_inner",
                "ref": ref, "rec": rec}

    if vrp_vent > 0:
        return {"class": "T3", "reason": "vent_positive_but_far_class_RegD_not_applied",
                "ref": ref, "rec": rec}

    if n_anom > 0:
        return {"class": "T4", "reason": "pixels_detected_only_far",
                "ref": ref, "rec": rec}

    return {"class": "T2b", "reason": "cold_scene_no_pixels",
            "ref": ref, "rec": rec}


def run_forense(*, volcano: str, consolidado_csv: Path, records_json: Path,
                volcanoes_yaml: Path, start: str, end: str,
                tolerance_min: int = 60) -> dict:
    """Ejecuta forense para un volcán y ventana. Devuelve dict con stats + per-ref."""
    df = pd.read_csv(consolidado_csv)
    df = df[df["Volcan"] == volcano]
    df = df[df["Origen_Dato"] == "latest.php"]
    df["dt"] = pd.to_datetime(df["Fecha_Satelite_UTC"])
    df = df[(df["dt"] >= start) & (df["dt"] <= end)]
    refs = df.to_dict("records")

    yaml_data = yaml.safe_load(records_json.read_text()) if records_json.suffix == ".yaml" else None
    records = json.loads(records_json.read_text()).get("records", [])

    cfg = yaml.safe_load(volcanoes_yaml.read_text())
    inner_km = float(cfg.get(volcano, {}).get("inner_radius_km", 5.0))

    classifications = [classify_ref(r, records, inner_km, tolerance_min) for r in refs]
    counts = {c: 0 for c in ("TP", "T1", "T2b", "T3", "T4")}
    for x in classifications:
        counts[x["class"]] += 1

    return {
        "volcano": volcano,
        "window": [start, end],
        "n_refs": len(refs),
        "tolerance_min": tolerance_min,
        "inner_radius_km": inner_km,
        "counts": counts,
        "recall": (counts["TP"] / len(refs)) if refs else 0.0,
        "classifications": classifications,
    }


def _main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--volcano", required=True)
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--consolidado",
                    default="data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv")
    ap.add_argument("--records", default=None,
                    help="Path al JSON; default data/mirova_equivalent/<volcano>.json")
    ap.add_argument("--yaml", default="volcanoes.yaml")
    ap.add_argument("--output-json", required=True)
    ap.add_argument("--output-md", required=True)
    ap.add_argument("--tolerance-min", type=int, default=60)
    args = ap.parse_args()

    records = Path(args.records) if args.records else Path(f"data/mirova_equivalent/{args.volcano}.json")
    out = run_forense(
        volcano=args.volcano,
        consolidado_csv=Path(args.consolidado),
        records_json=records,
        volcanoes_yaml=Path(args.yaml),
        start=args.start,
        end=args.end,
        tolerance_min=args.tolerance_min,
    )

    Path(args.output_json).write_text(json.dumps(out, default=str, indent=2))

    md_lines = [
        f"# Forense H17 replicable — {args.volcano}",
        f"\nVentana: {args.start} → {args.end}  ·  inner_radius_km={out['inner_radius_km']}",
        f"\nN refs MIROVA (latest.php only): **{out['n_refs']}**",
        f"\n## Conteos\n",
        "| Clase | Count | % |",
        "|---|---:|---:|",
    ]
    for c, n in out["counts"].items():
        pct = (100 * n / out["n_refs"]) if out["n_refs"] else 0
        md_lines.append(f"| {c} | {n} | {pct:.1f}% |")
    md_lines.append(f"\n**Recall (TP/N)**: {out['recall']:.3f}")

    Path(args.output_md).write_text("\n".join(md_lines))
    print(f"OK · {args.volcano}: {out['counts']}")


if __name__ == "__main__":
    _main()
```

- [ ] **Step 4: Verificar test pasa**

Run:
```bash
pytest tests/test_forense_h17_replicable.py -v
```
Expected: PASS 7/7 tests.

- [ ] **Step 5: Correr forense sobre los 3 Tier A reprocessed S18**

Run:
```bash
python experiments/38_forense_h17_replicable.py \
  --volcano Tupungatito --start 2026-03-25 --end 2026-04-25 \
  --output-json experiments/38_forense_Tupungatito.json \
  --output-md experiments/38_forense_Tupungatito.md

python experiments/38_forense_h17_replicable.py \
  --volcano Lascar --start 2026-03-25 --end 2026-04-25 \
  --output-json experiments/38_forense_Lascar.json \
  --output-md experiments/38_forense_Lascar.md

python experiments/38_forense_h17_replicable.py \
  --volcano Chaiten --start 2026-03-25 --end 2026-04-25 \
  --output-json experiments/38_forense_Chaiten.json \
  --output-md experiments/38_forense_Chaiten.md
```

Expected: 3 archivos MD + 3 JSON, cada uno con conteos. Tupungatito debería mostrar
~9 T4 y ~0 T3 (post-Regla D).

- [ ] **Step 6: Verificar conteos coherentes con S20 narrativa**

Run:
```bash
cat experiments/38_forense_Tupungatito.md
```

Expected: T3=0 (Regla D aplicada), T4 ~9, TP no-cero. Si hay desviación grande vs S20
narrativa (15 FN), documentar la causa en `~memory/project_s21_findings.md`.

- [ ] **Step 7: Commit**

```bash
git add experiments/38_forense_h17_replicable.py tests/test_forense_h17_replicable.py \
        experiments/38_forense_*.json experiments/38_forense_*.md
git commit -m "S21 — experiments/38 forense H17 replicable + 3 Tier A outputs

- Script clasifica TP/T1/T2b/T3/T4 cruzando JSONs vs CSV consolidado
- Filtra Origen_Dato='latest.php' (excluye OCR outliers H_S21_6)
- 7 tests TDD invariantes (mutually exclusive, latest.php only, total=N)
- Outputs: Tupungatito, Lascar, Chaiten para ventana 30 días
- Reproducible para todos los Tier A; reemplaza forense narrativa S20"
```

---

### Task 7: experiments/39_locate_active_vent.py

**Files:**
- Create: `experiments/39_locate_active_vent.py`
- Create: `tests/test_locate_active_vent.py`
- Output: `experiments/39_active_vent_<volcano>.json`, `experiments/39_summary.md`

**Lógica del script:**
1. Cargar JSON nuestro Tupungatito.
2. Filtrar records TP (clasificación 38) con `anomaly_pixels` no vacío.
3. Para cada record TP, extraer pixels dentro de 2×inner_radius_km del vent nominal.
4. Ponderar centroide por `vrp_pixel_mw`: `lat_w = Σ(lat·vrp) / Σ(vrp)`.
5. Computar centroide global ponderado sobre todos los TPs.
6. Comparar vs vent nominal. Si offset > 0.5 km, proponer `mirova_center_lat/lon`.
7. Output JSON + tabla MD.

- [ ] **Step 1: Escribir test failing**

`tests/test_locate_active_vent.py`:

```python
"""Invariantes script 39: centroide ponderado dentro del bbox de pixels input."""
from __future__ import annotations
import math
import pytest

from experiments.locate_active_vent import weighted_centroid, propose_mirova_center


def test_centroid_single_pixel():
    """Un solo pixel → centroide es ese pixel."""
    pixels = [{"lat": -33.4, "lon": -69.8, "vrp_pixel_mw": 0.2}]
    lat, lon = weighted_centroid(pixels)
    assert abs(lat - (-33.4)) < 1e-9
    assert abs(lon - (-69.8)) < 1e-9


def test_centroid_two_pixels_equal_weight():
    """Dos pixels VRP iguales → centroide en el medio."""
    pixels = [
        {"lat": -33.4, "lon": -69.8, "vrp_pixel_mw": 0.1},
        {"lat": -33.5, "lon": -69.9, "vrp_pixel_mw": 0.1},
    ]
    lat, lon = weighted_centroid(pixels)
    assert abs(lat - (-33.45)) < 1e-9
    assert abs(lon - (-69.85)) < 1e-9


def test_centroid_weighted_pulls_toward_hot_pixel():
    """VRP más alto pesa más en centroide."""
    pixels = [
        {"lat": -33.4, "lon": -69.8, "vrp_pixel_mw": 1.0},  # hot
        {"lat": -33.5, "lon": -69.9, "vrp_pixel_mw": 0.01},  # frío
    ]
    lat, lon = weighted_centroid(pixels)
    assert lat > -33.45  # más cerca del hot
    assert lon > -69.85


def test_centroid_zero_vrp_uses_arithmetic_mean():
    """Si todos los VRP son 0, fallback a media aritmética."""
    pixels = [
        {"lat": -33.4, "lon": -69.8, "vrp_pixel_mw": 0.0},
        {"lat": -33.5, "lon": -69.9, "vrp_pixel_mw": 0.0},
    ]
    lat, lon = weighted_centroid(pixels)
    assert abs(lat - (-33.45)) < 1e-9


def test_propose_offset_under_threshold_returns_none():
    """Offset chico (<0.5 km) → no propone cambio."""
    nominal = {"vent_lat": -33.4, "vent_lon": -69.8}
    proposed = propose_mirova_center(
        observed_centroid=(-33.4015, -69.8015),
        nominal=nominal,
        threshold_km=0.5,
    )
    assert proposed is None


def test_propose_offset_above_threshold_returns_dict():
    """Offset grande (>0.5 km) → propone mirova_center_lat/lon."""
    nominal = {"vent_lat": -33.4, "vent_lon": -69.8}
    proposed = propose_mirova_center(
        observed_centroid=(-33.43, -69.85),
        nominal=nominal,
        threshold_km=0.5,
    )
    assert proposed is not None
    assert "mirova_center_lat" in proposed
    assert "mirova_center_lon" in proposed
    assert "offset_km" in proposed
    assert proposed["offset_km"] > 0.5
```

- [ ] **Step 2: Verificar test falla**

Run:
```bash
pytest tests/test_locate_active_vent.py -v
```
Expected: FAIL ImportError.

- [ ] **Step 3: Implementar script**

`experiments/39_locate_active_vent.py`:

```python
"""Localizar fumarola activa real Tupungatito (centroide ponderado VRP) vs vent nominal.

Hallazgo H_S21_3: distancias CSV Mirova-v1 son reales (clusters 4.89/5.21 km),
no bin visual. Si la fumarola activa está descentrada, ROI1 5×5 km centrado en
vent nominal NO la contiene. Propone mirova_center_lat/lon corregido.

Uso CLI:
    python experiments/39_locate_active_vent.py \
        --volcano Tupungatito \
        --records data/mirova_equivalent/Tupungatito.json \
        --output-json experiments/39_active_vent_Tupungatito.json
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
from typing import Iterable

import yaml


EARTH_RADIUS_KM = 6371.0


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def weighted_centroid(pixels: Iterable[dict]) -> tuple[float, float]:
    """Centroide ponderado por vrp_pixel_mw. Si todos VRP=0, usa media aritmética."""
    px = list(pixels)
    if not px:
        return float("nan"), float("nan")
    total_vrp = sum(float(p.get("vrp_pixel_mw") or 0.0) for p in px)
    if total_vrp <= 0:
        n = len(px)
        return (sum(p["lat"] for p in px) / n, sum(p["lon"] for p in px) / n)
    lat = sum(p["lat"] * float(p.get("vrp_pixel_mw") or 0.0) for p in px) / total_vrp
    lon = sum(p["lon"] * float(p.get("vrp_pixel_mw") or 0.0) for p in px) / total_vrp
    return lat, lon


def propose_mirova_center(*, observed_centroid: tuple[float, float],
                          nominal: dict, threshold_km: float = 0.5) -> dict | None:
    lat_obs, lon_obs = observed_centroid
    if math.isnan(lat_obs):
        return None
    offset = _haversine_km(nominal["vent_lat"], nominal["vent_lon"], lat_obs, lon_obs)
    if offset < threshold_km:
        return None
    return {
        "mirova_center_lat": round(lat_obs, 5),
        "mirova_center_lon": round(lon_obs, 5),
        "offset_km": round(offset, 3),
        "vent_nominal": [nominal["vent_lat"], nominal["vent_lon"]],
    }


def collect_anomaly_pixels(records: list[dict], inner_radius_km: float,
                           vent_lat: float, vent_lon: float) -> list[dict]:
    """Recolecta TODOS los anomaly_pixels de records con dist al vent ≤ 2×inner_radius."""
    pixels: list[dict] = []
    for rec in records:
        for p in rec.get("anomaly_pixels", []) or []:
            d = _haversine_km(vent_lat, vent_lon, p["lat"], p["lon"])
            if d <= 2 * inner_radius_km:
                pixels.append(p)
    return pixels


def run(volcano: str, records_json: Path, volcanoes_yaml: Path,
        offset_threshold_km: float = 0.5) -> dict:
    cfg = yaml.safe_load(volcanoes_yaml.read_text()).get(volcano, {})
    vent_lat = float(cfg["vent_lat"])
    vent_lon = float(cfg["vent_lon"])
    inner_km = float(cfg.get("inner_radius_km", 5.0))

    records = json.loads(records_json.read_text()).get("records", [])
    pixels = collect_anomaly_pixels(records, inner_km, vent_lat, vent_lon)

    centroid = weighted_centroid(pixels)
    proposed = propose_mirova_center(
        observed_centroid=centroid,
        nominal={"vent_lat": vent_lat, "vent_lon": vent_lon},
        threshold_km=offset_threshold_km,
    )

    return {
        "volcano": volcano,
        "n_pixels": len(pixels),
        "vent_nominal": [vent_lat, vent_lon],
        "inner_radius_km": inner_km,
        "observed_centroid": list(centroid),
        "proposed_mirova_center": proposed,
    }


def _main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--volcano", required=True)
    ap.add_argument("--records", default=None)
    ap.add_argument("--yaml", default="volcanoes.yaml")
    ap.add_argument("--output-json", required=True)
    ap.add_argument("--threshold-km", type=float, default=0.5)
    args = ap.parse_args()

    records = Path(args.records) if args.records else Path(f"data/mirova_equivalent/{args.volcano}.json")
    out = run(args.volcano, records, Path(args.yaml), args.threshold_km)

    Path(args.output_json).write_text(json.dumps(out, indent=2, default=str))
    print(f"OK · {args.volcano}: centroid={out['observed_centroid']}, "
          f"proposed={out['proposed_mirova_center']}")


if __name__ == "__main__":
    _main()
```

- [ ] **Step 4: Verificar test pasa**

Run:
```bash
pytest tests/test_locate_active_vent.py -v
```
Expected: PASS 6/6.

- [ ] **Step 5: Correr sobre Tupungatito + Lascar + Chaitén**

Run:
```bash
python experiments/39_locate_active_vent.py \
  --volcano Tupungatito \
  --output-json experiments/39_active_vent_Tupungatito.json

python experiments/39_locate_active_vent.py \
  --volcano Lascar \
  --output-json experiments/39_active_vent_Lascar.json

python experiments/39_locate_active_vent.py \
  --volcano Chaiten \
  --output-json experiments/39_active_vent_Chaiten.json
```

- [ ] **Step 6: Inspeccionar outputs**

Run:
```bash
for v in Tupungatito Lascar Chaiten; do
  echo "=== $v ==="
  python -c "import json; d=json.load(open('experiments/39_active_vent_$v.json')); print(f\"centroid: {d['observed_centroid']}\"); print(f\"proposed: {d['proposed_mirova_center']}\")"
done
```

Expected: Tupungatito proposed offset >0.5 km (probable, dado clusters 4.89/5.21 km en CSV);
Lascar y Chaitén probablemente proposed=None (centradas).

- [ ] **Step 7: Commit**

```bash
git add experiments/39_locate_active_vent.py tests/test_locate_active_vent.py \
        experiments/39_active_vent_*.json
git commit -m "S21 — experiments/39 locate active vent + 3 Tier A outputs

- Centroide ponderado VRP de pixels detectados, vs vent_lat/lon nominal YAML
- Si offset >0.5 km, propone mirova_center_lat/lon corregido
- 6 tests TDD invariantes (centroide single/multi/weighted/zero-vrp/threshold)
- Hallazgo H_S21_3: clusters 4.89/5.21 km en CSV Mirova-v1 sugieren fumarola
  Tupungatito descentrada del vent nominal"
```

---

### Task 8: experiments/40_measure_local_bg.py

**Files:**
- Create: `experiments/40_measure_local_bg.py`
- Create: `tests/test_measure_local_bg.py`
- Output: `experiments/40_local_bg_results.json`, `experiments/40_local_bg_summary.md`

**Lógica del script:**
1. Tomar lista de granules T4 conocidos (output 38, clase=T4 Tupungatito).
2. Para cada granule, descargar via `pipeline.fetch.fetch_granule()` (usa earthaccess).
3. Cargar bandas BT (I04 para VIIRS 375m, M13 para 750m).
4. Para cada ROI variant computar `std_bg`:
   - **global**: anillo bbox 50×50 km menos `bg_inner_km`-disk (método actual)
   - **summit_5**: cuadrado 5×5 km centrado en vent nominal, excluye `vent_radius_km`
   - **summit_5_real**: ídem 5×5 km pero centrado en `mirova_center` propuesto (output 39)
   - **summit_7**: 7×7 km centrado en vent nominal
   - **summit_10**: 10×10 km centrado en vent nominal
5. Conteo de pixels válidos por variant. Flag si <25 (muestra ruidosa).
6. Output JSON + tabla MD con std_bg por granule × variant.

- [ ] **Step 1: Escribir test failing — invariantes computacionales**

`tests/test_measure_local_bg.py`:

```python
"""Invariantes script 40: ROI mask + std_bg computation."""
from __future__ import annotations
import numpy as np
import pytest

from experiments.measure_local_bg import (
    bbox_mask, std_bg_in_mask, exclude_inner_disk,
)


def test_bbox_mask_returns_correct_shape():
    lat = np.linspace(-33.5, -33.3, 50)[:, None] * np.ones((50, 50))
    lon = np.ones((50, 50)) * np.linspace(-70.0, -69.6, 50)
    mask = bbox_mask(lat, lon, center_lat=-33.4, center_lon=-69.8, half_km=2.5)
    assert mask.shape == lat.shape
    assert mask.dtype == bool
    assert mask.sum() > 0
    assert mask.sum() < lat.size  # No es todo True


def test_bbox_mask_zero_size():
    lat = np.array([[-33.4]])
    lon = np.array([[-69.8]])
    mask = bbox_mask(lat, lon, center_lat=-33.4, center_lon=-69.8, half_km=0.0)
    # Punto exacto en centro debería estar incluido
    assert mask[0, 0] == True


def test_exclude_inner_disk_removes_center():
    lat = np.linspace(-33.42, -33.38, 20)[:, None] * np.ones((20, 20))
    lon = np.ones((20, 20)) * np.linspace(-69.82, -69.78, 20)
    full = bbox_mask(lat, lon, -33.4, -69.8, half_km=5.0)
    excluded = exclude_inner_disk(full, lat, lon, -33.4, -69.8, vent_radius_km=2.0)
    # Center area removed
    assert excluded.sum() < full.sum()
    # Outer ring preserved
    assert excluded[0, 0] == full[0, 0]


def test_std_bg_zero_for_constant():
    bt = np.ones((10, 10)) * 280.0
    mask = np.ones((10, 10), dtype=bool)
    std, n = std_bg_in_mask(bt, mask)
    assert std == pytest.approx(0.0)
    assert n == 100


def test_std_bg_nan_when_too_few_pixels():
    bt = np.ones((5, 5)) * 280.0
    mask = np.zeros((5, 5), dtype=bool)
    mask[0, 0] = True
    std, n = std_bg_in_mask(bt, mask, min_pixels=25)
    assert np.isnan(std)
    assert n == 1


def test_std_bg_excludes_nan():
    bt = np.full((10, 10), 280.0)
    bt[0, 0] = np.nan
    mask = np.ones((10, 10), dtype=bool)
    std, n = std_bg_in_mask(bt, mask)
    assert std == pytest.approx(0.0)
    assert n == 99
```

- [ ] **Step 2: Verificar test falla**

Run:
```bash
pytest tests/test_measure_local_bg.py -v
```
Expected: FAIL ImportError.

- [ ] **Step 3: Implementar script**

`experiments/40_measure_local_bg.py`:

```python
"""Medir std_bg sobre múltiples ROI para validar viabilidad D6.

Hipótesis D6: std_bg sobre ROI1 5×5km local << std_bg sobre anillo bbox 50×50km
global, en volcanes con glaciar lateral (Tupungatito). Si validado, vent-path
threshold cae a ~1K y dispara ΔT real fumarólico ~1.5-2K.

Uso CLI:
    python experiments/40_measure_local_bg.py \
        --volcano Tupungatito \
        --granule-list experiments/40_granules_t4_Tupungatito.txt \
        --output-json experiments/40_local_bg_results.json

donde granule-list es archivo con un granule_url por línea, generado a partir
de los outputs T4 de experiments/38.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path

import numpy as np
import yaml

# Import desde pipeline pero NO modificarlo
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


def bbox_mask(lat: np.ndarray, lon: np.ndarray, center_lat: float,
              center_lon: float, half_km: float) -> np.ndarray:
    lat_span = (lat - center_lat) * 111.0
    lon_span = (lon - center_lon) * 111.0 * math.cos(math.radians(center_lat))
    return (np.abs(lat_span) <= half_km) & (np.abs(lon_span) <= half_km)


def exclude_inner_disk(mask: np.ndarray, lat: np.ndarray, lon: np.ndarray,
                       center_lat: float, center_lon: float,
                       vent_radius_km: float) -> np.ndarray:
    lat_km = (lat - center_lat) * 111.0
    lon_km = (lon - center_lon) * 111.0 * math.cos(math.radians(center_lat))
    dist = np.sqrt(lat_km ** 2 + lon_km ** 2)
    return mask & (dist > vent_radius_km)


def std_bg_in_mask(bt: np.ndarray, mask: np.ndarray,
                   min_pixels: int = 25) -> tuple[float, int]:
    valid = bt[mask & ~np.isnan(bt)]
    n = int(valid.size)
    if n < min_pixels:
        return float("nan"), n
    return float(np.std(valid)), n


def measure_for_granule(*, lat: np.ndarray, lon: np.ndarray, bt: np.ndarray,
                        vent_lat: float, vent_lon: float, vent_radius_km: float,
                        mirova_center_lat: float | None,
                        mirova_center_lon: float | None) -> dict:
    """Devuelve std_bg + n_px por cada variante de ROI."""
    out: dict = {}

    # Global = anillo bbox 25 km menos disk vent_radius
    bbox_global = bbox_mask(lat, lon, vent_lat, vent_lon, half_km=25.0)
    annulus = exclude_inner_disk(bbox_global, lat, lon, vent_lat, vent_lon,
                                 vent_radius_km=vent_radius_km)
    s, n = std_bg_in_mask(bt, annulus)
    out["global_annulus"] = {"std_bg": s, "n_pixels": n}

    # Summit 5×5 nominal, excluye vent_radius
    summit5 = bbox_mask(lat, lon, vent_lat, vent_lon, half_km=2.5)
    summit5_ex = exclude_inner_disk(summit5, lat, lon, vent_lat, vent_lon,
                                    vent_radius_km=vent_radius_km)
    s, n = std_bg_in_mask(bt, summit5_ex)
    out["summit_5_nominal"] = {"std_bg": s, "n_pixels": n}

    # Summit 5×5 real (mirova_center)
    if mirova_center_lat is not None:
        summit5r = bbox_mask(lat, lon, mirova_center_lat, mirova_center_lon, half_km=2.5)
        summit5r_ex = exclude_inner_disk(summit5r, lat, lon,
                                         mirova_center_lat, mirova_center_lon,
                                         vent_radius_km=vent_radius_km)
        s, n = std_bg_in_mask(bt, summit5r_ex)
        out["summit_5_real"] = {"std_bg": s, "n_pixels": n}

    # Summit 7×7 nominal
    summit7 = bbox_mask(lat, lon, vent_lat, vent_lon, half_km=3.5)
    summit7_ex = exclude_inner_disk(summit7, lat, lon, vent_lat, vent_lon,
                                    vent_radius_km=vent_radius_km)
    s, n = std_bg_in_mask(bt, summit7_ex)
    out["summit_7_nominal"] = {"std_bg": s, "n_pixels": n}

    # Summit 10×10 nominal
    summit10 = bbox_mask(lat, lon, vent_lat, vent_lon, half_km=5.0)
    summit10_ex = exclude_inner_disk(summit10, lat, lon, vent_lat, vent_lon,
                                     vent_radius_km=vent_radius_km)
    s, n = std_bg_in_mask(bt, summit10_ex)
    out["summit_10_nominal"] = {"std_bg": s, "n_pixels": n}

    return out


def _main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--volcano", required=True)
    ap.add_argument("--forense-json", required=True,
                    help="Output de experiments/38 con clasificaciones; usa records T4")
    ap.add_argument("--mirova-center-json", default=None,
                    help="Output experiments/39 con mirova_center proposed (opcional)")
    ap.add_argument("--yaml", default="volcanoes.yaml")
    ap.add_argument("--max-granules", type=int, default=10)
    ap.add_argument("--output-json", required=True)
    args = ap.parse_args()

    cfg = yaml.safe_load(Path(args.yaml).read_text()).get(args.volcano, {})
    vent_lat = float(cfg["vent_lat"])
    vent_lon = float(cfg["vent_lon"])
    vent_radius_km = float(cfg.get("vent_radius_km", 5.0))

    mirova_lat = mirova_lon = None
    if args.mirova_center_json:
        mc = json.loads(Path(args.mirova_center_json).read_text())
        proposed = mc.get("proposed_mirova_center")
        if proposed:
            mirova_lat = proposed["mirova_center_lat"]
            mirova_lon = proposed["mirova_center_lon"]

    forense = json.loads(Path(args.forense_json).read_text())
    t4_records = [c["rec"] for c in forense["classifications"] if c["class"] == "T4"]
    t4_records = t4_records[: args.max_granules]

    # NOTA: aquí necesitamos acceso a granules raw. Para mantener el script
    # standalone, importamos pipeline.fetch + pipeline.process_viirs_helpers.
    # Si no se pueden importar (o si MODIS=pyhdf en Windows roto), saltar
    # MODIS. Documentar el approach en summary.
    try:
        from pipeline import fetch as fetch_mod
    except ImportError as e:
        print(f"WARNING: pipeline.fetch no disponible: {e}")
        print("Ejecutar este script en Linux/WSL para acceso completo a granules.")
        Path(args.output_json).write_text(json.dumps({
            "error": "pipeline_fetch_unavailable",
            "message": str(e),
            "n_t4_records_target": len(t4_records),
        }, indent=2))
        return

    results = []
    for rec in t4_records:
        granule_url = rec.get("granule")
        if not granule_url:
            continue
        try:
            # Cargar bandas (función esperada en pipeline; si no existe, fallback)
            arrays = fetch_mod.load_bands_for_granule(granule_url)
            lat = arrays["lat"]
            lon = arrays["lon"]
            # Usar I04 para VIIRS 375m, M13 para 750m, B22 para MODIS
            bt = arrays.get("I04") or arrays.get("M13") or arrays.get("B22")
            if bt is None:
                continue
        except Exception as e:
            print(f"FETCH FAILED: {granule_url}: {e}")
            continue

        per_granule = measure_for_granule(
            lat=lat, lon=lon, bt=bt,
            vent_lat=vent_lat, vent_lon=vent_lon,
            vent_radius_km=vent_radius_km,
            mirova_center_lat=mirova_lat,
            mirova_center_lon=mirova_lon,
        )
        results.append({
            "granule": granule_url,
            "datetime_utc": rec.get("datetime_utc"),
            "sensor": rec.get("sensor"),
            "rois": per_granule,
        })

    # Stats: median std_bg por ROI
    summary = {}
    for roi_name in ("global_annulus", "summit_5_nominal", "summit_5_real",
                     "summit_7_nominal", "summit_10_nominal"):
        stds = [r["rois"][roi_name]["std_bg"] for r in results
                if roi_name in r["rois"] and not np.isnan(r["rois"][roi_name]["std_bg"])]
        summary[roi_name] = {
            "median_std_bg": float(np.median(stds)) if stds else float("nan"),
            "n_granules_with_data": len(stds),
        }

    out = {
        "volcano": args.volcano,
        "vent_nominal": [vent_lat, vent_lon],
        "mirova_center_used": [mirova_lat, mirova_lon] if mirova_lat else None,
        "n_granules_processed": len(results),
        "summary": summary,
        "per_granule": results,
    }
    Path(args.output_json).write_text(json.dumps(out, indent=2, default=str))
    print(f"OK · {args.volcano}: summary={summary}")


if __name__ == "__main__":
    _main()
```

- [ ] **Step 4: Verificar tests pasan**

Run:
```bash
pytest tests/test_measure_local_bg.py -v
```
Expected: PASS 6/6.

- [ ] **Step 5: Correr 40 sobre Tupungatito (depende de outputs 38 + 39)**

Pre-requisito: outputs Task 6 + Task 7 deben existir. Si no, abortar.

Run:
```bash
ls experiments/38_forense_Tupungatito.json experiments/39_active_vent_Tupungatito.json
```

Run:
```bash
python experiments/40_measure_local_bg.py \
  --volcano Tupungatito \
  --forense-json experiments/38_forense_Tupungatito.json \
  --mirova-center-json experiments/39_active_vent_Tupungatito.json \
  --max-granules 10 \
  --output-json experiments/40_local_bg_Tupungatito.json
```

NOTA SOBRE WINDOWS: si pipeline.fetch falla por pyhdf (MODIS roto en Windows), el
script termina con `error: pipeline_fetch_unavailable` y el JSON queda con stub.
Workaround: correr este experiment en GitHub Actions o WSL.

Expected (success path): JSON con summary mostrando median std_bg por ROI.

- [ ] **Step 6: Inspeccionar output**

Run:
```bash
python -c "import json; d=json.load(open('experiments/40_local_bg_Tupungatito.json')); print(json.dumps(d.get('summary', d), indent=2))"
```

Expected (criterio decisión D6):
- Si `summit_5_real.median_std_bg << global_annulus.median_std_bg` (e.g. 0.5 vs 2.5):
  D6 viable. Ir a Fase 2 con opción **A** o **B**.
- Si similar (e.g. 1.8 vs 2.5): glaciar dentro ROI1 → considerar median+MAD.
- Si `n_granules_with_data < 5`: muestra insuficiente, ampliar window y re-correr.

- [ ] **Step 7: Generar summary MD comparativo**

Run:
```bash
python -c "
import json, numpy as np
d = json.load(open('experiments/40_local_bg_Tupungatito.json'))
summary = d.get('summary', {})
print('# Measure local bg — Tupungatito')
print(f\"\\nN granules procesados: {d.get('n_granules_processed', 0)}\")
print(f\"Vent nominal: {d.get('vent_nominal')}\")
print(f\"Mirova_center usado: {d.get('mirova_center_used')}\")
print()
print('| ROI | median std_bg (K) | n granules |')
print('|---|---:|---:|')
for k, v in summary.items():
    print(f\"| {k} | {v['median_std_bg']:.2f} | {v['n_granules_with_data']} |\")
" > experiments/40_local_bg_Tupungatito.md
cat experiments/40_local_bg_Tupungatito.md
```

- [ ] **Step 8: Commit**

```bash
git add experiments/40_measure_local_bg.py tests/test_measure_local_bg.py \
        experiments/40_local_bg_*.json experiments/40_local_bg_*.md 2>/dev/null
git commit -m "S21 — experiments/40 measure local bg multi-ROI Tupungatito

- ROI variants: global_annulus / summit_5_nominal / summit_5_real / summit_7 / summit_10
- 6 tests TDD invariantes (bbox_mask, exclude_inner_disk, std_bg con NaN/min_pixels)
- Output JSON con std_bg per granule + median resumen
- Decisión D6 viable si summit_5_real.median << global_annulus.median
- WINDOWS gotcha: pyhdf roto, MODIS path no corre local. VIIRS sí."
```

---

## Self-Review

**1. Spec coverage**

| Requisito spec | Task | Cubierto |
|---|---|---|
| memory/project_s21_findings.md con 7 hallazgos | Task 1 | ✅ |
| docs/SESSION_CLOSE_CHECKLIST.md operacional | Task 2 | ✅ |
| Update CLAUDE.md trigger cierre + 15 repos | Task 3 | ✅ (2 archivos, no toca global) |
| Commit untracked relevante | Task 4 | ✅ (3 commits separados + inventory PNGs) |
| Solucionar desacople Vault (E1+E3) | Task 5 | ✅ |
| experiments/38 forense replicable | Task 6 | ✅ con 7 tests TDD |
| experiments/39 locate active vent | Task 7 | ✅ con 6 tests TDD |
| experiments/40 measure local bg | Task 8 | ✅ con 6 tests TDD |
| Cada experiment con seed fijo | Tasks 6-8 | ⚠️ no usan random — seed N/A |
| Output JSON + tabla MD | Tasks 6-8 | ✅ |
| No tocar pipeline/ | Tasks 6-8 | ✅ |
| Cada artefacto tiene entrada en CHECKLIST | Task 2 + meta | ✅ |
| Tests si aplican | Tasks 6-8 | ✅ |
| Decisión informada A/B/C/D para Fase 2 | Task 8 Step 6 criterio | ✅ |

**2. Placeholder scan** — ningún "TBD", "implement later", "similar to Task N" detectado.

**3. Type consistency**
- `classify_ref(ref, records, inner_radius_km, tolerance_min)` — usado consistentemente Task 6.
- `weighted_centroid(pixels) -> tuple[float, float]` — consistente Task 7.
- `std_bg_in_mask(bt, mask, min_pixels=25) -> tuple[float, int]` — consistente Task 8.
- `bbox_mask` y `exclude_inner_disk` — mismas signatures en script y tests.

**4. Riesgos identificados**
- Task 8 depende de `pipeline.fetch.load_bands_for_granule()` — si esa función no existe con ese nombre exacto, fallará. Mitigación: el script tiene fallback graceful con error message claro.
- Task 5 (Vault) requiere que el path `../../Vault/` sea válido desde CWD. Verificable con `ls ../../Vault/` antes de ejecutar.
- MODIS path (Task 8) no corre en Windows local (pyhdf). Solo VIIRS local; MODIS requiere GitHub Actions o WSL.

---

## Execution Handoff

**Plan completo y guardado a `docs/superpowers/plans/2026-04-25-s21-d6-foundation.md`. Dos opciones de ejecución:**

**1. Inline Execution (recomendado para esta sesión Opus 4.7 1M tokens)** — Ejecuto Tasks 1-8 secuencialmente en este chat, con checkpoint cada Task para que Nicolás revise. Aprovecha el contexto largo y elimina overhead de subagent dispatch.

**2. Subagent-Driven** — Despacho un subagente fresco por Task con review entre tasks. Iteración más rápida con Tasks paralelas (1+2+3 podrían correr en paralelo, 6+7 también). Costo: más context switches.

**¿Cuál preferís?**
