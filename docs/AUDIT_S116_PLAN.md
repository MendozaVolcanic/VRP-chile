# Plan de Auditoría Integral S116 (protocolo A51)

> **Para el ejecutor (próxima sesión):** este es un PLAN, no la auditoría. Ejecutar con
> **subagentes en paralelo** (uno por eje, A26/A51 — `dispatching-parallel-agents`), cada uno
> escribe sus hallazgos a un JSON en `experiments/_s116_audit/<eje>.json` (no pegar stdout gigante
> al contexto, regla de delegación). Luego un paso de **síntesis** consolida a `docs/AUDIT_S116.md`.
> Marcar cada eje con checkbox al completar.

**Objetivo:** Auditoría integral del proyecto VRP Chile (última fue AUDIT_S105; estamos en S116,
~11 sesiones después — A51 manda cada ~20, pero Nicolás la pidió ahora) para detectar fallas
silenciosas, drifts acumulados, deuda técnica e incoherencias cross-source **antes** de seguir con
features nuevas.

**Enfoque:** 8 ejes paralelos + síntesis. Cada eje tiene charter, inputs (qué leer), método
(comandos exactos), **firmas de falla** (qué buscar), criterio de aceptación (qué es "sano"), y
output estructurado. Disparar adversarial (A62): cada eje debe **intentar refutar** "está sano",
no confirmarlo.

**Reglas vinculantes durante la auditoría:** A45 (NO tocar pipeline sin tag+OK — la auditoría es
read-only/diagnóstico, NO implementa fixes), MISSION 3-preguntas, A62 adversarial, A10 (cruzar con
`pc.vrp_mw`, no `record.vrp_mw`), A61 (eje espacial: re-anclar al GVP, lección PCC S115), A82 (NO
reabrir D11-MODIS far→summit), A48 (verificar file:line, no la etiqueta de un subagente).

**Gatillo de pausa (A51):** si la síntesis encuentra **>3 contradicciones cross-source**, pausar
features nuevas y consolidar primero.

---

## §0 — Preparación (antes de disparar subagentes)

- [ ] **Paso 0.1 — Sync + CSV fresco (A17).**
  ```bash
  cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
  git fetch origin --prune && git pull --ff-only
  curl -sL https://raw.githubusercontent.com/MendozaVolcanic/Mirova-v1/main/monitoreo_satelital/registro_vrp_consolidado.csv -o /tmp/cons_fresh.csv
  curl -sL https://raw.githubusercontent.com/MendozaVolcanic/Mirova-v1/main/monitoreo_satelital/registro_vrp_ocr.csv -o /tmp/ocr_fresh.csv
  ```
  Comparar `latest_consolidado.csv` (repo) vs `/tmp/cons_fresh.csv` — si difieren mucho, el cruce
  de recall debe usar el fresco.

- [ ] **Paso 0.2 — Snapshot defensivo (A38).** `git tag pre-s116-audit <sha> && git push origin pre-s116-audit`.
  La auditoría es read-only, pero el tag protege si se decide algún cleanup después.

- [ ] **Paso 0.3 — Crear `experiments/_s116_audit/`** para los JSON de salida de cada eje.

---

## Eje 1 — Fidelidad MISSION / clon literal (subagente: general-purpose)

**Charter:** verificar que NO se acumularon parches anti-MIROVA y que la detección sigue fiel a
Coppola 2016a.

**Inputs:** `docs/MISSION.md` (3 preguntas + tabla anti-patrones), `pipeline/profiles/mirova_equivalent.yaml`,
`docs/AUDIT_S114_PARITY_BY_SENSOR.md` §6d (la verificación file:line de fidelidad), `CLAUDE.md` reglas científicas.

**Método:**
1. Listar **todos** los `enable_*: true` de `mirova_equivalent.yaml`. Para cada uno, responder las
   3 preguntas de MISSION con cita file:line del paper (A48 verbatim).
2. Verificar el estado de la familia "gate intra-radio" S84/S85 (A55 anti-patrón): ¿siguen ON?
   ¿el frontend `mirovaEqVrp` ya hacía esa supresión (redundancia)? Decisión pendiente desde S105.
3. Re-confirmar que la arquitectura de detección MODIS sigue fiel (dual-ROI 5σ/10σ `enable_dual_roi_bt`,
   Tests 2∧3 OR `min(C1,μ+C2σ)`, σ global, second-run, ETI cuadrático, kernel 8-vec) — que ningún
   PR posterior a S114 la haya driftado.

**Firmas de falla:** un flag ON que da NO en las 3 preguntas; un parche que reintroduce un drift
removido (tabla anti-patrones MISSION); un `enable_dual_roi_bt`/Tests cambiado sin pasar por MISSION.

**Criterio de aceptación:** todo `enable_*: true` pasa ≥1 de las 3 preguntas con cita verbatim;
0 parches nuevos de la familia anti-patrón; detección MODIS = la que S114 declaró fiel.

**Output:** `experiments/_s116_audit/eje1_mission.json` — `{flags_on:[{flag, verdict, cita}], antipatrones_nuevos:[], deteccion_fiel:bool, hallazgos:[]}`.

---

## Eje 2 — Integridad del código del pipeline (subagente: general-purpose)

**Charter:** detectar regresiones, bugs de inserción, schema asimétrico, y el dual-anchor.

**Inputs:** `pipeline/process_modis.py`, `process_viirs.py`, `process_viirs_mod.py`, `store.py`,
`detection_context.py`, `scan_geometry.py`, `anchor.py`; `tests/`.

**Método:**
1. **Suite completa:** `python -m pytest tests/ -q` (workaround `-s` si el teardown de captura
   rompe, ver reference_s96). Confirmar 0 fallos. Para CUALQUIER fallo, comparar la función vs
   `git show origin/main:<archivo>` (A50 — "pre-existing" exige verificación cross-source).
2. **Patrón A49** (inserción que se come un `return`): `git log --oneline -30` + revisar inserciones
   recientes entre funciones; confirmar que ninguna función de detección retorna `None` en el
   camino exitoso.
3. **Schema asimétrico A46 (bidireccional, S113):** mapear TODAS las representaciones del hotspot
   (`hotspot_*`, `final_hotspot_*`, `primary_cluster.*`, Test1 integrated) y cada gate downstream
   que tome decisiones binarias (rollup/zero-out, summit/far). Buscar gates que usen UNA
   representación e ignoren otra → candidato F47/A46. Verificar el guard S113 sigue LIVE.
4. **Dual-anchor (S115, incertidumbre residual):** PCC `centroid_dist_km` se mide desde el lacolito
   (`vent_lat` ≠ GVP). ¿Esta dualidad de anclas mete incoherencia en OTROS gates más allá del
   display (ej. A46-style)? ¿Otros volcanes con `vent_lat ≠ lat` (offset) tienen el mismo efecto?
   Ver `reference_s115_pcc_anchor_parity`.

**Firmas de falla:** test rojo no presente en origin/main; función con `return` faltante; gate
binario que usa una sola representación del hotspot; `centroid_dist_km` anclado distinto de lo que
asume un gate downstream.

**Criterio de aceptación:** suite 0 fallos (o todos confirmados pre-existentes vs origin/main);
0 funciones con return faltante; guard A46 LIVE y simétrico donde corresponde; dual-anchor acotado
a display (no contamina gates).

**Output:** `experiments/_s116_audit/eje2_codigo.json` — `{suite:{pass,fail}, regresiones:[], schema_gaps:[], dual_anchor_impact:""}`.

---

## Eje 3 — Integridad de datos / ground truth (subagente: general-purpose)

**Charter:** validar el loader del CSV, frescura, races, y el inventario de `data/_*/`.

**Inputs:** `latest_consolidado.csv`, `registro_vrp_ocr.csv`, `data/mirova_equivalent/*.json`,
loaders del frontend + de audits, `git status` (untracked `data/_*/`).

**Método:**
1. **Loader CSV (raíz del 49% de "FPs" S86):** verificar parsing de OCR consumido, `Distancia_km`,
   alias de nombres (A14: `PlanchonPeteroa` sin guión, `Puyehue-Cordon Caulle`, `Nevados de Chillan`),
   fechas de cobertura. Cruzar conteos por volcán nuestro vs CSV.
2. **JSONs corruptos (A47 race):** `python -c "import json,glob; [json.load(open(f,encoding='utf-8')) for f in glob.glob('data/mirova_equivalent/*.json')]"` — debe no tirar excepción.
3. **Frescura:** ¿`latest_consolidado.csv` está al día? ¿los JSON NRT tienen records recientes
   (día en curso, A96)?
4. **Inventario `data/_*/` + `experiments/_*/`** (untracked, grandes): clasificar archivar/borrar
   (A38) — NO borrar, solo recomendar con inventario.

**Firmas de falla:** JSON que no parsea; volcán con conteo mal por alias; OCR no consumido; CSV
stale; `data/_*/` con >100 MB sin valor.

**Criterio de aceptación:** 11/11 JSON parsean; loader maneja todos los alias; CSV fresco; inventario
`data/_*/` con recomendación por item.

**Output:** `experiments/_s116_audit/eje3_data.json` — `{json_ok:bool, loader_bugs:[], stale:bool, data_dirs_inventory:[]}`.

---

## Eje 4 — Divergencias abiertas + recall por sensor (subagente: general-purpose)

**Charter:** estado de cada divergencia abierta + recall/precision fresco por sensor.

**Inputs:** `docs/MIROVA_DIVERGENCES.md` (catálogo vivo: D2, D3, D11 A70, NEW-8, VIIRS750 dispersión),
`docs/AUDIT_S114_PARITY_BY_SENSOR.md`, `reference_s115_pcc_anchor_parity`.

**Método:**
1. Para cada divergencia abierta, verificar si empeoró/mejoró/se mantiene con data fresca.
2. **Recall/precision por sensor** (re-correr la paridad S114 con CSV fresco): gate dashboard =
   `distance_class=="summit" AND pc.centroid<=inner AND 0<pc.vrp<=50000` (A10). Esperado ~S114:
   VIIRS375 99% / VIIRS750 86% / MODIS 16% (este último = bug etiquetado A46, no falta de detección).
   **Re-anclar distancias al GVP (A61/A3 — lección PCC S115).**
3. Confirmar A82 (D11-MODIS far→summit CERRADO, irreducible) — NO reabrir, solo verificar que no
   regresó la confusión.

**Firmas de falla:** recall que cae en un Tier A vs S114; una divergencia que empeoró silenciosa;
un nuevo far→summit no explicado por A46.

**Criterio de aceptación:** recall por sensor ≈ S114 (±pocos %); divergencias estables o mejor;
0 sorpresas.

**Output:** `experiments/_s116_audit/eje4_divergencias.json` — `{recall_por_sensor:{}, divergencias:[{id,estado}], sorpresas:[]}`.

---

## Eje 5 — Frontend / display coherence (subagente: general-purpose, verificar en preview)

**Charter:** coherencia de las vistas (S92 L5) + el datetime + la magnitud + la página nueva.

**Inputs:** `frontend/index.html`, `diario.html`, `mosaico.html`, `experimental/index.html`,
`comparacion.html` (nueva S115).

**Método:**
1. **Paridad 3 vistas (S92 L5):** todo filtro de display (cirrus suppression, F5' núcleo,
   eqVrpDisplay, geo_class=extension) debe estar replicado en index/diario/mosaico. Buscar
   asimetrías.
2. **Datetime TZ (S115 #6):** grep `new Date(` crudo sobre campos `datetime_utc`/`dt`/`Fecha_*`
   sin `parseUtcMs` en las 4 vistas. (Acaba de arreglarse diario.html; verificar que no quede otro.)
3. **Magnitud coherente:** `mirovaEqVrp` vs `mirovaEqVrpCore` vs F5' toggle — mismo número en
   tabla, chart, mapa, tarjeta (lección S96 tabla vs chart 10×).
4. **Verificar en preview real** (no `node --check`): las 4 vistas + comparacion.html cargan sin
   errores de consola, datos correctos.

**Firmas de falla:** filtro en una vista no en las otras; `new Date()` crudo; magnitud distinta
entre tabla y chart; error de consola.

**Criterio de aceptación:** 4 vistas coherentes; 0 `new Date()` crudo sobre UTC; magnitud unificada;
0 errores de consola en preview.

**Output:** `experiments/_s116_audit/eje5_frontend.json` — `{paridad_vistas:bool, datetime_bugs:[], magnitud_coherente:bool, preview_errors:[]}`.

---

## Eje 6 — Transparencia / SDA CPLT N°372 (subagente: general-purpose)

**Charter:** cumplimiento de la convención de transparencia algorítmica.

**Inputs:** `docs/FICHA_SDA_VRP_CHILE.md` (v1.0 S115), `../../GUIA_MAESTRA_TRANSPARENCIA_ALGORITMICA.md`,
`pipeline/*.py`, `tasks/backlog_s115.md` (deuda cabeceras).

**Método:**
1. **Cabeceras FICHA** (deuda S115): ¿qué archivos de detección/clasificación tienen cabecera FICHA?
   Hoy solo `anchor.py` + `vrp_regimes.py`. Faltan: `process_modis.py`, `process_viirs.py`,
   `process_viirs_mod.py`, `store.py`. Confirmar el gap y proponer el contenido de cada cabecera
   (sin aplicar — toca pipeline → A45, sesión dedicada).
2. **Ficha publicable al día:** ¿v1.0 refleja el estado actual? ¿algún cambio post-S115 que falte?

**Firmas de falla:** archivo que participa en la decisión SIN cabecera FICHA; ficha desactualizada
vs el código.

**Criterio de aceptación:** gap de cabeceras inventariado con contenido propuesto; ficha publicable
coherente con el código.

**Output:** `experiments/_s116_audit/eje6_transparencia.json` — `{cabeceras_faltantes:[], ficha_aldia:bool, propuestas:[]}`.

---

## Eje 7 — Git / operacional / NRT (subagente: general-purpose)

**Charter:** salud del NRT, estado git/worktrees, coherencia docs/memoria.

**Inputs:** `.github/workflows/nrt.yml`, `git worktree list`, runs recientes de GH Actions,
`MEMORY.md`, `docs/AUDIT_S105.md`, `CLAUDE.md` sección Estado.

**Método:**
1. **NRT health:** `gh run list --workflow nrt.yml --limit 20` — tasa de éxito; ¿el breaker LANCE
   (A64) sigue funcionando? ¿algún volcán falla recurrente?
2. **Git/worktrees (A52):** `git worktree list`; ¿solo la raíz en main? ¿branches huérfanas?
   ¿uncommitted relevante?
3. **Coherencia docs/memoria (lección AUDIT_S105: la sección Estado quedó congelada 70 sesiones):**
   ¿`CLAUDE.md` sección Estado sigue siendo puntero (no estado duplicado)? ¿`MEMORY.md` ≤500 líneas?
   ¿el último BLOQUE_ARRANQUE apunta a esta auditoría?

**Firmas de falla:** NRT con fallos recurrentes; worktree no-main stale presentado como canónico;
doc con estado congelado contradiciendo el real.

**Criterio de aceptación:** NRT ≥ ~90% éxito; git limpio; docs/memoria como puntero coherente.

**Output:** `experiments/_s116_audit/eje7_git_nrt.json` — `{nrt_success_rate:float, git_limpio:bool, docs_coherentes:bool, hallazgos:[]}`.

---

## Eje 8 — Backlog / deuda técnica / decisiones pendientes (subagente: general-purpose)

**Charter:** inventariar todo lo diferido y detectar lo que se volvió problema silencioso.

**Inputs:** `tasks/backlog_*.md` (5 archivos), `docs/MIROVA_DIVERGENCES.md` "Pendiente de decisión",
`tasks/BLOQUE_ARRANQUE_S116.md`.

**Método:**
1. Consolidar todos los items de backlog con su razón de diferimiento y antigüedad.
2. Marcar los que se volvieron urgentes o riesgosos (ej. gates intra-radio S84/S85 ON desde S105 sin
   decisión; cabeceras FICHA deuda legal; backfill histórico VIIRS).
3. Cruzar con el frente de display PCC (geo_class=extension, preview hecho S115 — decisión pendiente
   de Nicolás).

**Firmas de falla:** item diferido hace >10 sesiones sin revisión que ahora es riesgo; decisión
pendiente que bloquea otra cosa.

**Criterio de aceptación:** inventario completo priorizado (urgente/medio/bajo) con recomendación.

**Output:** `experiments/_s116_audit/eje8_backlog.json` — `{items:[{id,edad,riesgo,recomendacion}]}`.

---

## §9 — Síntesis (después de los 8 ejes, NO subagente — el hilo principal)

- [ ] Leer los 8 JSON de `experiments/_s116_audit/`.
- [ ] **Contar contradicciones cross-source** (A51). Si >3 → **pausar features, consolidar primero**.
- [ ] Escribir `docs/AUDIT_S116.md` con: veredicto global (sano / con deuda / con fallas), tabla de
      hallazgos por eje (severidad: crítico/alto/medio/bajo), contradicciones cross-source, y un
      **plan de consolidación priorizado** (propuesto, NO ejecutado — cada fix que toque pipeline va
      con A45 + MISSION en su propia sesión).
- [ ] **Verificación adversarial (A62):** para cada hallazgo "crítico/alto", un subagente que intente
      REFUTARLO con datos antes de incluirlo (evitar falsos positivos de auditoría, lección A48/A55).
- [ ] Actualizar `MEMORY.md` (nuevo bloque S116 auditoría) + `tasks/BLOQUE_ARRANQUE_S117.md`.

---

## Self-review del plan (cobertura)

- ✅ Misión/fidelidad (Eje 1), Código (Eje 2), Data (Eje 3), Divergencias/recall (Eje 4),
  Frontend (Eje 5), Transparencia (Eje 6), Git/NRT (Eje 7), Backlog (Eje 8), Síntesis (§9).
- ✅ Cubre los frentes NUEVOS post-S105: dual-anchor S115 (Eje 2/4), A46 bidireccional S113 (Eje 2),
  transparencia SDA (Eje 6), comparación page S115 (Eje 5), GAP #A resuelto (Eje 1 — confirmar
  flag OFF permanente).
- ✅ Read-only/diagnóstico: NINGÚN eje implementa fixes (A45). Los fixes salen como plan priorizado.
- ✅ Adversarial (A62) embebido en cada eje + en la síntesis.
- ✅ Re-anclaje GVP (A61/A3) explícito en Ejes 4 y 2 (la trampa que mordió en S115).

## Ejecución (handoff)

Disparar los 8 ejes como subagentes `general-purpose` en paralelo (A26 — no recortar a 2 por
economía; 8 en paralelo cubre todos los ejes). Cada uno escribe su JSON. Luego el hilo principal
hace §9 síntesis. Estimado: ~1 ronda de subagentes + síntesis. Producir `docs/AUDIT_S116.md`.
