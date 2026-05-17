# BLOQUE DE ARRANQUE S60 — VRP Chile

> Documento creado al cierre de la sesión maratón S52-S58 (2026-05-17).
> 17 PRs mergeados a main. Pipeline operacional intacto. Fix local kernel
> bg validado empíricamente en Villarrica. Listo para S60 audit + adopción.
>
> **LEER ESTE DOC ANTES DE CUALQUIER TASK NUEVO**. Las primeras 3 sesiones
> S52-S54 olvidaron contexto crítico y se gastaron en re-descubrir lo que
> ya estaba documentado.

---

## 1. Lectura obligatoria al inicio S60 (orden estricto)

1. **Este doc** (`tasks/BLOQUE_ARRANQUE_S60.md`) — 5 min
2. **`docs/REAUDITORIA_S52.md`** — contexto crítico que NO debo olvidar
3. **`docs/MIROVA_DETAILED_CITATIONS.md`** (S57, 320 líneas) — citas verbatim
   7 papers core MIROVA, ubicación archivo:línea
4. **`docs/EXCELS_INVENTORY_S57.md`** (S57) — archivos olvidados (OSF v2.5)
5. **`docs/HYPOTHESIS_LOG.md`** entries H_S52-S58 (top 5)
6. **`docs/MISSION.md`** — 3 preguntas vinculantes
7. **`pipeline/profiles/mirova_equivalent.yaml`** — estado flags actuales

Si saltás cualquiera: probable repetir errores de S52 (ej. asumir CSV
es MIROVA cuando es scraper de Nicolás).

---

## 2. Contexto crítico OBLIGATORIO recordar siempre

### 2.1 El CSV consolidado es scraper de Nicolás, NO export MIROVA

`data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv`:
- Scraper personal contra `mirovaweb.it/latest.php`
- `Tipo_Registro` son categorías que **Nicolás** asignó:
  - `ALERTA_TERMICA` = MIROVA reportó alerta (= TP real)
  - `FALSO_POSITIVO` = MIROVA reportó pero fuera de radios oficiales
  - `RUTINA` = scraper corrió pero MIROVA NO reportó nada (vacío)
- **Universo MIROVA reportó** = ALERTA + FP, NO contar RUTINA como denominador

### 2.2 MIROVA NRT es algorítmico puro

Sin supervisión humana en NRT. La curación humana aplica SOLO al OSF v2.5
publicación histórica (Coppola 2023 §2.5).

Por tanto: diferencias recall NRT son **algorítmicas**, NUNCA "MIROVA
revisó manualmente".

### 2.3 Background MIROVA = kernel local 3×3, NO ring 5-25km

Confirmado en TRES papers core MIROVA (citas verbatim en
`docs/MIROVA_DETAILED_CITATIONS.md`):
- Coppola 2024 chapter L1129: "T_bk from pixels adjacent to hot one"
- Coppola 2016a SP426.5 L357-359: "arithmetic mean of pixels surrounding"
- Campus 2024 VIIRS L119-124: idem

**Nuestro pipeline** usaba `median(ring 5-25km)` desde S9. Eso es divergencia.
S58 implementó `compute_local_background` (kernel 3×3) como fix path opt-in.

### 2.4 Cluster aggregation = SUM scene-wide, NO "primary cluster"

Confirmado en tres papers:
- Coppola 2016a Eq.8: `RP = Σ RP_PIX` sobre alerted pixels
- Coppola 2024 Eq.13: `ΔL_tot = Σ ΔL_k`
- Campus 2024 Eq.1: idem

Nuestro `cluster_hotspots(vent_anchored)` (S38) es divergencia operacional.
**Mantener documentado**, no eliminar sin A/B comparativo previo.

### 2.5 OSF v2.5 archive = ground truth histórico (NO usar CSV scraper como primary)

`data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv` (98 MB, no committed):
- 615,470 filas globales, 48,360 chilenas (10 vols 2001-2025)
- **5211 filas Villarrica** con LAT/LON exactos hotspot + VRP Watts + class
- Termina 2025-12-02 (no cubre 2026, sirve **target estadístico**)
- Mediana VIIRS-I = **0.92 MW** (p25=0.27, p10=0.09)
- Snap `Max_Dist=838.5m` = diagonal pixel I-band 375×√5 (no error)

**Antes de validar cualquier magnitud nueva**: cargar OSF chilena y
comparar distribución estadística (mediana, p25/p50/p75).

### 2.6 TIF MIROVA archive ≠ lo que MIROVA reporta

`mirova-tif-archive/data/tif/<Vol>/*.tif` (en máquina de Nicolás):
- Producto **visualización** con sum pixels brutos pre-clustering
- Caso Puyehue lacolito: TIF=2313 MW vs MIROVA reporta 0.18 MW (468× diff)
- **R2 pixel-level válido solo para GEOMETRÍA (centroid)**, NO magnitud

### 2.7 Casos paradigmáticos Villarrica VIIRS-I (5 ALERTAS MIROVA)

Window 2026-01 → 2026-05:

| Fecha UTC | Sat | MIROVA MW | Estado fix |
|---|---|---:|---|
| 2026-05-11 06:00 | NOAA20 | 0.31 | ya calibrado (1.24× legacy, 1.61× new) |
| 2026-05-14 05:48 | NOAA21 | 0.31 | **fix cura 12.08× → 2.17×** ✓ |
| 2026-04-09 06:00 | NOAA20 | 0.11 | fuera window reproc S58 |
| 2026-03-08 06:00 | NOAA20 | 0.21 | fuera window reproc S58 |
| 2026-02-26 05:42 | NOAA20 | 0.12 | fuera window reproc S58 |

Para re-validar los 3 casos fuera window: reproc con `start=2026-02-20`
en el workflow `reproc-ab-local-kernel-bg.yml`.

---

## 3. Estado actual pipeline post-S58

### 3.1 Operacional (`mirova_equivalent` profile)

```yaml
# pipeline/profiles/mirova_equivalent.yaml
enable_vent_anchored_clustering: true     # S38 D8 fix
enable_pixel_level_distance_filter: true  # S35 H8
enable_test1_lbg_global: true             # S39 D4 per-vol
enable_bt_path_hot: false                 # S40 retirado
enable_first_pass_tests_2_and_3: true     # S46 drift234
enable_dual_roi_first_pass: true          # S46 drift234
enable_second_pass_adjacent: true         # S46 drift234
enable_dual_roi_second_pass: true         # S46 drift234
enable_local_kernel_bg: false             # S58 NO ADOPTADO operacional aun
```

### 3.2 Experimental disponible

- `_local_kernel_bg_enabled.yaml` (S58): clon de mirova_equivalent + flag ON

### 3.3 Per-vol opt-in en volcanoes.yaml (S59)

```yaml
- Villarrica: local_kernel_bg: true  # lago N
- Copahue: local_kernel_bg: true     # lago El Agrio activo
- Llaima: local_kernel_bg: true      # lago Conguillío N
- PlanchonPeteroa: local_kernel_bg: true  # laguna + glaciares
# Tupungatito EXPRESAMENTE excluido (ring frío por glaciar)
# Otros 6 vols: default false (gradiente positivo, no necesitan)
```

### 3.4 Métricas finales sesión maratón (audit S48 detection-unified)

- F1: **98.3%** (era 89.9% pre-S47)
- Recall: 97.2%
- Precision: 99.4%
- NRT cron: 97.8% success post-fix H7b

### 3.5 Tests

**335 passed / 16 skipped** sin regresiones.

---

## 4. Pendientes priorizados S60

### Prioridad ALTA

1. **Audit recall NEW vs MIROVA CSV** (sin regresión)
   - Reproc S58 redujo 65% records summit. Verificar no perder TPs MIROVA RUTINA
     ni ALERTAS.
   - Script: adaptar `experiments/88_audit_s47_fps_distribution.py` para
     `data/_local_kernel_bg_enabled/Villarrica.json`

2. **Validar contra OSF v2.5 archive** (ground truth histórico)
   - Cargar `VRP_GLOBAL_ARCHIVE_2025.csv` Villarrica
   - Comparar distribución magnitudes nuestra NEW vs OSF mediana 0.92 MW

3. **Re-reproc con window que incluya 5 casos paradigmáticos**
   - Trigger `reproc-ab-local-kernel-bg.yml` con `start=2026-02-20`
   - Validar 3 casos restantes: 2026-02-26, 2026-03-08, 2026-04-09

### Prioridad MEDIA

4. **R2 pixel-level validation**
   - Extender `tests/test_r2_pixel_level.py` con casos NEW vs MIROVA TIF
   - Verificar geometría centroid mantiene

5. **Refinamientos** si mediana sigue >50% sobre target OSF:
   - `kernel_size=5` (más vecinos)
   - Percentile p25 en lugar de mean del kernel

6. **Extender A/B a otros 3 vols opt-in** (Copahue, Planchón, Llaima)
   - Workflow A/B existente acepta `volcano` parametrizado

### Prioridad BAJA

7. **Adopción operacional si todo valida** (`mirova_equivalent.yaml`)
   - Cambiar `enable_local_kernel_bg: false` → `true`
   - Validar dashboard post-adopción

8. **Investigar `mirova_diff_cluster` 178 casos** (S48 pendiente)

---

## 5. Skills obligatorias S60

Invocar al inicio según corresponda:

| Situación S60 | Skill obligatoria |
|---|---|
| Cualquier bug / regresión / FN inesperado | `superpowers-systematic-debugging` |
| Antes de cambio en `pipeline/` >20 líneas | `writing-plans` |
| Antes de escribir código pipeline | `test-driven-development` |
| Antes de declarar listo / push / cerrar item | `verification-before-completion` |
| 2+ investigaciones paralelas | dispatching-parallel-agents |
| Paso atrás metodológico | `superpowers-brainstorming` |
| Lectura PDFs/Excel | `markitdown` (antes de Read) |
| Búsqueda papers/docs online | `investigacion` (agotar local primero) |
| Cierre sesión con learnings | `revise-claude-md` + `consolidate-memory` |

**Regla meta S57+**: invocar skill si dudás. Costo 30s, beneficio = evitar
fix mal hecho.

---

## 6. Anti-patrones aprendidos en sesión maratón S52-S58

1. **"Asumir que ya leí el paper"** sin verificar línea-por-línea (S57 reveló
   3 papers con citas que olvidé).

2. **"CSV scraper = MIROVA"** — confundir scraper personal de Nicolás con
   datos oficiales MIROVA (corregido S52).

3. **"Supervisión humana en MIROVA NRT"** — solo aplica a OSF v2.5
   publicación (corregido S54).

4. **"`find data/` no es necesario antes de audit"** — OSF v2.5 archive
   estuvo olvidado meses (corregido S57).

5. **"A/B offline siempre detecta el problema"** — S55 fue negativo porque
   trabajaba sobre `anomaly_pixels` ya clipped por bg contaminado. El
   problema era upstream (S56 lo encontró).

6. **"Implementar fix sin papers backing"** — S55 propuso 4 estrategias sin
   paper que las respaldara. MISSION.md las habría descartado.

7. **"Universal sin per-vol audit"** — S58 inicialmente flag global. S58
   audit C reveló que Tupungatito kernel local empeoraría.

---

## 7. Comando de arranque S60 sugerido

```bash
# Sesión S60 prompt inicial
cat tasks/BLOQUE_ARRANQUE_S60.md  # leer este doc primero
cat docs/REAUDITORIA_S52.md
cat docs/MIROVA_DETAILED_CITATIONS.md | head -100
find data/ -name "*.csv" | head -20  # verificar archivos disponibles
python -m pytest 2>&1 | tail -3  # estado tests
gh pr list --state merged --limit 5  # últimos PRs
```

Luego decidir prioridad:
- **Opción A (recomendado)**: Audit recall NEW vs MIROVA CSV
- **Opción B**: Validar contra OSF v2.5
- **Opción C**: Re-reproc con window que cubra 3 casos restantes

---

## 8. Estado git

- Branch: `claude/nostalgic-aryabhata-e05d1e` (worktree S47-S58)
- Main: 17 PRs mergeados sesión maratón (#44-#66)
- Último commit S58: `a8fb0fe` (reproc validation)
- Sin uncommitted changes esperados

```bash
git log --oneline origin/main -5
git status --short  # debería estar limpio
```

---

## 9. URLs útiles

- Repo: https://github.com/MendozaVolcanic/VRP-chile
- Scraper Mirova-v1: https://github.com/MendozaVolcanic/Mirova-v1
- OSF v2.5: https://osf.io/zm62w/
- MIROVA web: http://www.mirovaweb.it/NRT/
- Villarrica page MIROVA: http://www.mirovaweb.it/NRT/volcanoDetails_VIR375.php?volcano_id=357120
- Coord cráter Villarrica real (Nicolás): `(-39.420292, -71.939908)`

---

## 10. Persistencia in-vivo (regla meta-meta S21)

Cuando descubrás hallazgo durante S60: persistir INMEDIATAMENTE en
`docs/HYPOTHESIS_LOG.md` o `docs/MIROVA_DETAILED_CITATIONS.md`. NO esperar
al cierre. La sesión puede cortarse abruptamente.
