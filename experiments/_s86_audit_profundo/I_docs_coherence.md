# Subagente I — Coherencia docs cross-source (S86)

**Fecha**: 2026-05-28
**Scope**: auditoría coherencia entre CLAUDE.md (global + Volcanologia + VRP Chile), MISSION.md, SESSION_INDEX_CONSOLIDATED_S80.md, META_RULES_S80.md, MEMORY.md, HYPOTHESIS_LOG.md, MIROVA_DIVERGENCES.md, BIBLIOGRAPHY_SYNTHESIS.md, todos los `tasks/BLOQUE_ARRANQUE_S*.md` activos, `volcanoes.yaml`, perfiles, y docs F_* recientes (S81-S86).

---

## Veredicto global

**El proyecto NO está coherente en estado S86**. Detecté 7 contradicciones cross-source (3 ALTAS, 4 MEDIAS) que ya están confundiendo decisiones operacionales. Es analogía al monitoreo de un volcán con instrumentos desincronizados: cada sismómetro reporta bien lo que mide, pero quien integra la señal recibe lecturas contradictorias sobre el estado del sistema. Regla M8 dispara: >3 contradicciones — el protocolo dice **pausar features nuevas y consolidar primero**.

Lo bueno: cada doc individual sigue siendo coherente con su scope. El problema es la sincronización entre ellos.

---

## Inventario rápido

| Categoría | Cantidad |
|---|---:|
| docs/*.md totales | 86 |
| docs modificados S81-S86 (28d) | 24 |
| tasks/BLOQUE_ARRANQUE_S*.md activos | 10 (S74,76,78,79,80,81,82,84,85,86) |
| memory/*.md | 34 |
| MEMORY.md líneas | 282 (bajo cap M9=500) |
| Perfiles pipeline/profiles/*.yaml | 30 |
| Perfil operacional | `mirova_equivalent.yaml` |

11 Tier A canónicos confirmados consistentes en `volcanoes.yaml` + CLAUDE.md proyecto + MEMORY.md + SESSION_INDEX_S80: PuyehueCordonCaulle, Villarrica, Lascar, Copahue, NevadosDeChillan, Llaima, Chaiten, PlanchonPeteroa, Lastarria, Isluga, Tupungatito.

---

## Matriz de contradicciones

### C1 (ALTA) — Worktree canónico: tres docs vivos, tres paths distintos

- `CLAUDE.md` proyecto §Working worktree declara `VRP-Chile-s70/`.
- `MEMORY.md` §Worktree canónico S80 dice `VRP-Chile-s80-consolidation/` y marca s70 con WARNING branch huérfano.
- `tasks/BLOQUE_ARRANQUE_S86.md` §0 declara `VRP Chile/` raíz como canónico.

Cualquier sesión Claude nueva entra primero por CLAUDE.md y aterriza en worktree atrasado. S82-prep ya documentó el problema (regla A52) pero CLAUDE.md no fue actualizado. **Impacto verificable: este propio subagente recibió path canónico distinto en cada source.**

### C2 (ALTA) — Reglas A54-A60 huérfanas

- `CLAUDE.md` proyecto define hasta **A53**.
- `docs/META_RULES_S80.md` §"Lecciones durables S84" define **A56-A60**.
- **A54 y A55 nunca existieron** (gap numérico).
- `BLOQUE_ARRANQUE_S86.md` §3 cita A56-A60 como activas asumiendo que están en CLAUDE.md.

Cualquier sesión que ignore META_RULES_S80.md pierde reglas operacionales críticas (A56 bypass earthaccess, A58 healthcheck staleness, A60 TOKEN en workflows). Ya costaron 4 días de NRT caído en S84.

### C3 (MEDIA) — Offset Tupungatito vent: tres geometrías

- `CLAUDE.md` §A13: "offset 3 km S".
- `MEMORY.md` §Sesión S80: "offset 3.00 km S confirmado contra MEMORY.md (S15 documentaba 2.99 km SE)".
- `SESSION_INDEX_S80` §Fase B: "offset 2.99 km SE del vent".

S vs SE son direcciones diferentes. Impacto bajo (cálculo aproximado), pero ejemplo del drift que se acumula.

### C4 (ALTA) — Drift D8 huérfano

D8 fue planteado S35 como bug crítico (factor 27× ratio Puyehue por cluster selection erróneo).
- `CLAUDE.md` proyecto §Estado §S35: D8 NUEVO en investigación.
- `docs/MIROVA_DIVERGENCES.md`: lista D1, D2, ..., D6, D7, D9. **Salta D8**.
- `SESSION_INDEX_CONSOLIDATED_S80.md` Tabla §2: lista D1-D7, no menciona D8.

Tres opciones: (a) fue resuelto por `enable_vent_anchored_clustering` (S38), (b) sigue abierto, (c) fue refutado. Ninguno de los tres docs lo dice. **Hipótesis colgada con consecuencias operacionales serias.**

### C5 (MEDIA) — Lista papers MIROVA core diverge

- `MISSION.md` §3 preguntas lista 10 papers (Coppola 2015/2016a/2020/2024/2025/2022 + Campus + Aveni + Laiolo + Massimetti).
- `CLAUDE.md` proyecto §A9 lista autores MIROVA: "Coppola, Laiolo, Massimetti, Campus, Aveni, **Cigolini**".

Cigolini está en CLAUDE.md A9 pero no en MISSION.md. Solapamiento alto pero gap formal.

### C6 (ALTA) — Adopción PR #224 y #229 vs MISSION.md 3 preguntas

`F_S81_C_R3_NATURE_AUDIT.md` cabecera S85 reconoce que el gate intra-radio **YA EXISTÍA en frontend desde S33** y nunca fue mostrado al usuario. Las hipótesis Fase B/C fueron REFUTADAS por datos (367/367 ALERTAs MIROVA intra-radio, 100% uniforme).

Pero **PR #224 y PR #229 fueron mergeados y adoptados ANTES de esa refutación**, con justificación "mejora interna -59% pixels MODIS recapturados ruidosos".

Aplicando MISSION.md a posteriori:
- **PR #224 (F-S81-A path D MODIS intra-radio)**: pregunta 1 papers = NO. Pregunta 2 divergencia = NO. Pregunta 3 alineación interna = PARCIAL (replica lo que frontend ya hacía). **Veredicto: GRIS.**
- **PR #229 (F-S81-B' second_pass intra-radio)**: pregunta 1 papers = NO. Pregunta 2 divergencia = NO. Pregunta 3 alineación interna = SÍ (mejora campo térmico publicado a dashboard, -59% MODIS). PERO afecta cálculo VRP MODIS aggregado, no solo render. **Veredicto: GRIS.**

Ambos pasan la regla por la puerta 3 con la lectura más amplia. MISSION.md §Anti-patrones lista "Subir inner_radius_km ad-hoc" como rechazado S27 — los gates intra-radio acumulados son análogos. **Riesgo emergente**: si en S87+ se proponen 3-4 gates intra-radio más por path, se cae otra vez en el ciclo de drift que S27 cerró. Recomendación R4: agregar fila explícita a MISSION.md tabla anti-patrones.

### C7 (MEDIA) — MEMORY.md sin entrada S86

S86 está en curso con outputs concretos:
- Mec 1 propuesto adoptable (G1 = sensor_bucket != VIIRS_M_750).
- Mec 2 (gate t_bg ≥260K) REFUTADO con datos (cuesta 3 TPs Lascar 2026-02-17).
- Mec 3 (persistencia temporal ≥2 noches) REFUTADO con datos (nuestros FPs también persisten 79%).
- Hallazgo paralelo MODIS Lascar recall 0.125.

Pero MEMORY.md sigue terminando en S85. Regla M2 ("persistencia in-vivo no esperar al cierre") está siendo violada parcialmente. Si la sesión S86 se corta, 3-4h de investigación con 3 hipótesis refutadas se pierden y podrían re-investigarse.

---

## Reglas A1-A60 — status

Detallado en `I_docs_coherence.json §reglas_status`. Resumen:

- **A1-A53**: definidas en CLAUDE.md proyecto. Vigentes y aplicables. No detectadas obsoletas.
- **A54, A55**: gap numérico. No existen.
- **A56-A60**: huérfanas en `docs/META_RULES_S80.md`. **No migradas a CLAUDE.md proyecto**. Citadas como activas en BLOQUE_ARRANQUE_S86 (riesgo de pérdida).
- **M1-M10**: vigentes. M2 (persistencia in-vivo) violada parcialmente en S86.

---

## Misión vs realidad (PRs S81-S85)

| PR | Tema | P1 papers | P2 divergencia | P3 infra | Veredicto |
|---|---|---|---|---|---|
| #221 | F46 VRP_TIR gate | SÍ (Coppola 2024 + Aveni 2024) | N/A | N/A | OK |
| #224 | F-S81-A Path D MODIS intra-radio | NO | NO | PARCIAL | **GRIS** |
| #229 | F-S81-B' second_pass intra-radio | NO | NO | SÍ (afecta render + VRP) | **GRIS** |

**Anti-patrón detectado**: gates intra-radio acumulando sin respaldo paper. Analogía S27 con "Subir inner_radius_km ad-hoc" (rechazado). Recomendación: agregar fila a MISSION.md tabla anti-patrones para frenar la pendiente.

---

## Hipótesis colgadas

1. **D8 cluster selection (factor 27× Puyehue)** — mencionado CLAUDE.md S35, ausente de docs canónicos S80. **Prioridad**: cerrar formalmente.
2. **H_S70_PATH_D_CIRRUS_FP** — confirmada + fix diferido S71. S86 Mec 2 lo refuta como gate único. **Persistir resolution**.
3. **D7 local ROI threshold p95 VIIRS375** — diferido. Sin actualizar desde S80.
4. **Frente 1.A schema mirova_publishable** — diseñado en F_PRECISION_GAP_INVESTIGATION_S86 para S87.
5. **Frente 3 magnitud PCC/Tupu/PP** — bloqueo bloque S86, sin prioridad asignada.
6. **F66 dual-bg consistency gate Tasks 7-15** — SESSION_INDEX_S80 lo declara prioritario para S81+. **NO mencionado en BLOQUE_ARRANQUE_S86**. ¿Abandonado, diferido, abierto?

---

## MEMORY.md health

| Métrica | Valor | Estado |
|---|---|---|
| Líneas | 282 | OK bajo cap M9=500 |
| Warning system reminder 200 | Supera | Decisión usuario |
| Última sesión documentada | S85 | ❌ S86 ausente |
| Entradas apuntando a docs inexistentes | 0 | OK |
| Subdocs memoria activos | 34 | OK |

**Gap principal**: entrada S86 pendiente. Hallazgos Mec 1/2/3 refutados de F_PRECISION_GAP_INVESTIGATION_S86.md no están en memoria todavía.

---

## Recomendaciones priorizadas

### Críticas — resolver antes de S87 (~30 min total)

| ID | Acción | Resuelve |
|---|---|---|
| **R1** | Actualizar `CLAUDE.md` proyecto §Working worktree para declarar `VRP Chile/` raíz como canónico (o el worktree main-tracking actual). Eliminar declaración s70/. | C1 |
| **R2** | Migrar A56-A60 desde `docs/META_RULES_S80.md` a `CLAUDE.md` proyecto §"Reglas operacionales" como nueva subsección "Aprendizajes S84-S85". Si no, agregar nota explícita en CLAUDE.md "A54-A60 viven en META_RULES_S80.md". | C2 |
| **R3** | Cerrar formalmente D8 en `docs/MIROVA_DIVERGENCES.md`. Verificar si `enable_vent_anchored_clustering` (S38) lo cierra. Si no, reabrir con plan. | C4 |
| **R4** | Agregar fila a MISSION.md §Anti-patrones tabla: "Gate intra-radio sin respaldo paper — PR #224 y PR #229 adoptados por justificación infra (alineación frontend); revisar si se proponen 3-4 más". | C6 prevención |

### Altas — cierre S86 (~45 min)

- **R5**: persistir entrada S86 en MEMORY.md con hallazgos (Mec 1 propuesto, Mec 2 y Mec 3 refutados con datos, hallazgo paralelo MODIS Lascar recall 0.125), refs a F_PRECISION_GAP_INVESTIGATION_S86.md + experiments/_s86_*. Resuelve C7.
- **R6**: actualizar HYPOTHESIS_LOG.md cerrando H_S70_PATH_D_CIRRUS_FP con resolution "Mec 2 propuesto S86, refutado como gate único por costar 3 TPs Lascar evento eruptivo 2026-02-17".
- **R7**: generar tasks/BLOQUE_ARRANQUE_S87.md con plan Frente 1.A (G1) o Frente 4 (exclude_zones extendido).

### Medias — consolidar inicio S87

- **R8**: actualizar SESSION_INDEX_CONSOLIDATED_S80.md → S86 con §Fase D resumen S81-S86.
- **R9**: ejecutar audit flags M4 anticipado (programada S100). Hay 30 perfiles, varios huérfanos. Detectaría flags `enable_path_d_intra_radio_gate` + `enable_second_pass_intra_radio_gate` ahora ON sin documentar en CLAUDE.md.
- **R10**: aclarar status F66 (Tasks 7-15 desde S80).

### Bajas — archivar

- **R11**: mover tasks/BLOQUE_ARRANQUE_S74/76/78/79/80/81/82/84/85.md a tasks/_archive/.

---

## Reformulación regla M8

La regla M8 dice "cada 20 sesiones auditoría completa". La velocidad real S70-S86 (~3 PRs/sesión sostenido, 24 docs modificados últimos 28 días) acumula contradicciones más rápido que ese intervalo. **Recomendación**: reformular a "cada **10 sesiones O 25 PRs**, lo primero". Si Nicolás está pidiendo auditoría profunda S86 con 3 subagentes, es señal empírica que el intervalo S80→S100 era demasiado laxo.

---

## Lectura final (tono geólogo)

El proyecto está en un estado análogo a un volcán bien monitoreado con instrumentos individualmente confiables pero **desincronizados**. Cada paper (CLAUDE.md, MEMORY.md, MISSION.md, SESSION_INDEX) reporta correctamente lo que mide en su scope, pero el operador que sintetiza la imagen general entre sesiones recibe lecturas contradictorias sobre el estado del sistema. **No es falla del pipeline, es deriva documental acumulada**.

La consolidación S80 hizo exactamente esto. El intervalo S80-S86 (6 sesiones, ~24 PRs, 24 docs tocados) ya muestra acumulación suficiente para requerir otra mini-consolidación. Si se ejecutan R1-R4 ahora (30 min) + R5-R7 al cierre S86 (45 min) + R8-R10 al inicio S87 (1h), el sistema vuelve a coherencia operacional sin sacrificar la velocidad de cambio.

El riesgo no atendido: el patrón "gate intra-radio acumulando" (PR #224 + #229) es el mismo mecanismo que MISSION.md §Anti-patrones documenta como causa del ciclo cerrado S27. Si entra un PR #N más de la misma familia sin pasar las 3 preguntas explícitas, se reabre el ciclo.

---

## Archivos generados

- `experiments/_s86_audit_profundo/I_docs_coherence.md` (este doc)
- `experiments/_s86_audit_profundo/I_docs_coherence.json`
