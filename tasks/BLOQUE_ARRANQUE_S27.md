# Bloque de arranque S27

> **Pegar este bloque al inicio de la próxima sesión** para que Claude tenga
> contexto completo en 30 segundos sin re-derivar.

---

## Estado al cierre S26 (2026-04-29)

**Branch**: `s15-dev` y `main` ambos en `origin` con commits S26.
**Suite tests**: **187/187 verde**.
**NRT cron**: funcionando, Villarrica usa Test 1 dedicado vía profile.

## Lo cerrado en S26 (2026-04-27 a 2026-04-29)

### Hits empíricos
- ✅ Villarrica recall **0/6 → 6/6 (100%)** vía Test 1 + Regla D Test 1-priority + fix VRP-clip + fix L_bg local.
- ✅ Bug VRP_MIR negativo fixeado universal.
- ✅ Bug JSON inflación (Lascar 117 MB > 100 MB GitHub) fixeado con cap top-100 anomaly_pixels.
- ✅ Dashboard summit-default activado (UI limpia).
- ✅ Reproceso histórico 11/11 Tier A con código S26 actual.
- ✅ exclude_zones agregadas Llaima (Conguillío) + Copahue (Caviahue) + Villarrica (Lago Villarrica + Calafquén).

### Lecciones de día — auditoría exhaustiva post-Nicolás-pregunta-cuestionando

**Pregunta crítica de Nicolás**: *"¿estás seguro de esto sobre MIROVA usando 10σ? ¿por qué no lo hacemos?"*

Auditoría sistemática reveló:

1. **Di Bella 2024 NO ES MIROVA**. Es del grupo INGV Catania (RSDF), sistema rival. Por ~10 sesiones lo usábamos como "thresholds MIROVA" — error.

2. **Auditoría 4 agentes paralelos sobre 30+ PDFs detectó 13 papers más confundibles**:
   - 10 papers grupo Catania (Del Negro/Corradino/Cariello/Torrisi/Amato/Malaguti) — sistemas RSDF, V-STAR, FastVRP, CNN, Isolation Forest.
   - 3 papers grupo CNR-IMAA Potenza (Marchese/Pergola/Genzano/Filizzola) — sistema NHI.
   - **Ninguno usar como autoridad MIROVA**.

3. **Auditoría 5 papers MIROVA core no auditados** (Coppola 2020 Frontiers, Coppola 2022 Sabancaya, Coppola 2025 Fernandina, Laiolo 2026 Stromboli, Campion+Coppola lava lakes):
   - **NO añaden N·σ distintos** a Coppola 2016a Tabla 1.
   - **Laiolo 2026 textual**: *"no atmospheric correction or cloud-contamination automatic filtering is applied"*. MIROVA NRT NO filtra nubes ni cura humanamente.
   - Coppola 2025 confirma 51×51 km grid (= nuestro radius_km=25 ✓).

4. **9 parches en código actual NO están en papers MIROVA** (lista en `~memory/project_s26_parches_no_mirova.md`):
   - Cap MAX_SIGMA_COMPONENT_K=7K (S15)
   - Vent-path entero (S6-S12)
   - exclude_zones (S16/S26)
   - Regla D vent-priority (S20) y Test 1-priority (S26 D)
   - Cloud mask BT<260K
   - Pisos VRP por sensor
   - etc.

### Decisión metodológica final S26

**Volver a "MIROVA literal puro"** según papers documentales:
- N·σ = **5σ summit / 10σ scene** noche (Coppola 2016a Tabla 1) en TODOS los sensores.
- **Quitar cap=7K** (parche S15 anula la diferenciación summit/scene).
- **Quitar exclude_zones** (no en MIROVA).
- **Desactivar vent-path** (no en MIROVA).
- **Desactivar Reglas D** (parches nuestros).
- **Desactivar cloud mask BT<260K** (Laiolo 2026 textual).
- **Mantener** Coppola 2015 NTI + Coppola 2016a dNTI 8-vec + P3.1 dual-ROI dNTI + Test 1 integrated-ROI + Stefan-Boltzmann TIR + k Wooster/Campus.

**Los parches NO desaparecen** — quedan como infraestructura disponible para **objetivo (2) "herramienta independiente que mejora MIROVA"** futuro. Pero NO se usan en clon literal.

## Plan formal listo para ejecutar

`docs/superpowers/plans/2026-04-28-mirova-literal-puro.md` — 7 tasks TDD con A/B aislado:

- **T1-T2**: profiles `_mirova_literal` (treatment) + `_mirova_legacy` (control).
- **T3**: nuevo flag `ENABLE_EXCLUDE_ZONES` para deshabilitar zonas.
- **T4-T5**: workflow A/B + dispatch.
- **T6**: forense vs MIROVA NRT.
- **T7**: decisión APROBAR/NO con criterios:
  - Recall agregado cae < 10pp (vs 0.81 actual).
  - FP_far cae ≥ 40%.
  - Ratio mediano ≤ 30× (vs 57× actual).

**Tiempo estimado**: ~1h15min total (30 min código + 30 min Actions + 15 min análisis).

## Pregunta pendiente para Nicolás (CRITICAL — preguntar AL EMPEZAR S27)

**¿Cómo ejecutamos el plan S27 MIROVA literal?**

**1. Subagent-Driven (recomendado)** — dispatch fresh subagent por task, review entre tareas, fast iteration.

**2. Inline Execution** — ejecutar tareas en sesión actual con checkpoints para review.

Nicolás aún no respondió. Esa es la pregunta de arranque S27.

## Recordatorios al arrancar S27

1. **Leer en este orden**:
   - `~memory/MEMORY.md` (índice)
   - `~memory/reference_papers_mirova_canonical.md` (regla canonical autores MIROVA)
   - `~memory/project_s26_parches_no_mirova.md` (inventario parches con valor futuro)
   - `tasks/BLOQUE_ARRANQUE_S27.md` (este archivo)
   - `docs/superpowers/plans/2026-04-28-mirova-literal-puro.md` (plan formal)

2. **NO usar como autoridad MIROVA**: Di Bella 2024, Torrisi 2022/2025, Cariello, Corradino, Amato, Marchese, Pergola, Genzano, Filizzola. Ver `~memory/reference_papers_mirova_canonical.md` para lista completa.

3. **Persistencia in-vivo**: cuando descubras un hallazgo durante S27, persistilo INMEDIATAMENTE.

4. **Skills obligatorias** según CLAUDE.md trigger table:
   - Bug/anomalía → `superpowers-systematic-debugging`
   - Antes de fix `pipeline/` >20 líneas → `writing-plans` (ya hecho ✓)
   - Editar `process_*.py` → `test-driven-development`
   - 2+ investigaciones independientes → `dispatching-parallel-agents`

## Decisiones consolidadas (NO reabrir en S27)

- **Tupungatito recall ~0.40-0.50** = límite físico MIR puro nocturno automatizado.
- **D6 background localizado REFUTADO** empíricamente.
- **MIROVA NRT no supervisa humano** (Laiolo 2026 textual confirmado).
- **Factor 42 = diferencia agregación** (cluster vs pixel), no bug.
- **Test 1 implementado funciona en pipeline** (Villarrica 6/6 con Regla D Test 1-priority).
- **Plan A dual-ROI BT NO APROBADO** — cap=7K anula diferencia (S26).
- **Bug VRP_MIR negativo fixeado** universal.
- **Di Bella + 12 papers más NO son MIROVA** (S26 audit).

## Verificación 30-segundos al arranque

```bash
# 1. Branch al día
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git fetch origin && git status --branch --short
# Expected: ## s15-dev...origin/s15-dev (sin diff)

# 2. Tests verde
pytest 2>&1 | tail -3
# Expected: 187 passed

# 3. NRT health
gh run list -R MendozaVolcanic/VRP-chile --workflow=nrt.yml -L 5 \
  --json status,conclusion,createdAt --jq '.[] | "\(.createdAt[:19]) \(.conclusion // .status)"'
# Expected: mayoría success
```

## Comandos típicos S27

```bash
# Ejecutar plan formal MIROVA literal (Inline si Nicolás eligió):
# Tarea por tarea siguiendo docs/superpowers/plans/2026-04-28-mirova-literal-puro.md

# Si Subagent-Driven:
# Invocar superpowers:subagent-driven-development y dispatch agente por task.
```

## Token usage al cierre S26

~99% del límite Opus 4.7 1M. **CRÍTICO arrancar S27 fresh** para tener context cache caliente y trabajar las 7 tasks del plan sin compactaciones.

---

**Resumen 2 líneas para pegar al primer prompt S27**:

> S26 cerró con auditoría exhaustiva: 13 papers no-MIROVA detectados (Di Bella + Catania + CNR Potenza), 9 parches en código sin respaldo paper. Plan formal listo en `docs/superpowers/plans/2026-04-28-mirova-literal-puro.md` para clon literal puro (5σ/10σ Coppola 2016a Tabla 1, sin parches). **Pregunta pendiente**: ¿Subagent-Driven o Inline Execution? Lee `tasks/BLOQUE_ARRANQUE_S27.md` para contexto completo.
