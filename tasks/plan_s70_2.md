# Plan S70-2: Refinamientos conservadores

**Goal:** Resolver pendientes S70-1 que NO requieren merge de PRs #103/#104 ni cambios al pipeline operacional. Trabajo 100% documental + diagnóstico.

**Architecture:** 3 tareas independientes, todas sin tocar `pipeline/`, `volcanoes.yaml`, `mirova_equivalent.yaml`. Cada una agrega data o docs.

**Tech Stack:** Python (rasterio, pandas), Markdown, gh CLI (read-only).

**Worktree:** `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP-Chile-s70\` rama `s70-2-refinamientos` basada en `s70-1-r2-retroactivo`.

**Misión vinculante**: las 3 tareas pasan P3 alineación interna no-metodológica de `docs/MISSION.md`.

---

## Task 1 — Multi-caso PP para resolver verdict marginal

**Objetivo**: T3 S70-1 (PP) dio verdict marginal por 0.08 ratio sobre límite 2.0. El implementer notó que casos 1.51× y 1.94× hubieran PASS. **Validación honesta requiere mediana sobre N casos**, no 1 caso.

**Hipótesis**: si la mediana ratio PP sobre 3-5 ALERTAs es ≤2.0 con drift mediano ≤3 km, la adopción S61 PP queda validada bajo gates revisadas. Si la mediana excede 2.0 ratio, el verdict marginal es real y la adopción S61 PP requiere investigación.

**Files:**
- Modify: `experiments/124_r2_planchon_peteroa/audit_pp.py` (extender a multi-caso)
- Create: `experiments/124_r2_planchon_peteroa/results_multi.json`
- Modify: `experiments/124_r2_planchon_peteroa/README.md` (Parte 2 — multi-caso)

**Steps**:
1. Identificar 3-5 ALERTAs PP recientes con TIF paralelo (preferir VIIRS375).
2. Extender script para iterar y reportar mediana ratio + mediana drift.
3. Actualizar README con tabla N casos + verdict reformulado por mediana.
4. Commit.

---

## Task 2 — Doc dedicado `docs/R2_GATES_BY_REGIME.md`

**Objetivo**: Consolidar las bandas gates por régimen documentadas en D7 (MIROVA_DIVERGENCES.md) + H_S70_R2_RETROACTIVO_4VOLS (HYPOTHESIS_LOG.md) en un doc operacional dedicado. Para que futuras adopciones S70-N tengan referencia rápida sin re-leer 2 entries.

**Files:**
- Create: `docs/R2_GATES_BY_REGIME.md`
- Modify: `docs/MISSION.md` (nota al final referenciando el nuevo doc)

**Content del nuevo doc**:
- Regímenes térmicos identificados (Tier A Alto, Tier A Muy Bajo, No focal)
- Cómo clasificar régimen de un vol nuevo (ΔT máxima, tamaño cluster típico)
- Bandas gates por régimen (tabla)
- Patrón de aplicación R2 paso a paso
- Casos no aplicables (PCC lacolito) y cómo validar adopción alternativamente

**Steps**:
1. Leer D7 + H_S70_R2_RETROACTIVO_4VOLS para extraer contenido vigente.
2. Escribir doc nuevo consolidando.
3. Agregar nota corta en MISSION.md referenciando.
4. Commit.

---

## Task 3 — Audit frontend bugs menores 6-11 (S67)

**Objetivo**: El audit S67 (memorizado, no en docs) listó 11 inconsistencias frontend. S68 P0 fixes (PR #99) resolvió las críticas (1-5). Quedan 6-11 como menores. T3 lista cuáles son, prioriza, y escribe plan de fix sin implementar (para sesión futura S70-3+).

**Files:**
- Create: `tasks/frontend_bugs_s67_remaining.md` (listado priorizado)

**Steps**:
1. Buscar referencias al audit S67 en docs/HYPOTHESIS_LOG.md, BLOQUE_ARRANQUE_S65.md, BLOQUE_ARRANQUE_S70.md.
2. Identificar los 6 bugs menores restantes (de la lista 1-11).
3. Para cada uno: describir, severidad (UX), file:line aproximado si conocido, propuesta de fix.
4. Commit.

---

## Checkpoint cierre S70-2

- [ ] T1: PP multi-caso con verdict mediano
- [ ] T2: doc R2_GATES_BY_REGIME.md creado + ref en MISSION.md
- [ ] T3: tasks/frontend_bugs_s67_remaining.md con 6 bugs priorizados

PR `s70-2-refinamientos → s70-1-r2-retroactivo` cuando los 3 checkpoints OK.
