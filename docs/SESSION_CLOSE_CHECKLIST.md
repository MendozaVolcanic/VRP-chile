# Session Close Checklist (operacional)

> **Quién lo usa**: Claude al cierre de cada sesión, ANTES de declarar la sesión terminada.
> **Por qué existe**: el trigger CLAUDE.md "revise-claude-md + consolidate-memory" decía
> "consolidar lecciones" sin enumerar qué. Resultado S20: cerró sin documentar el schema
> gap std_bg, las 36 imágenes mirovaweb, el CSV externo Mirova-v1, los OCR outliers.
> S21 los descubrió "de nuevo" como si fueran hallazgos. Esta lista lo previene.

## Bloque A — Hallazgos nuevos

- [ ] ¿Hubo H# (hipótesis) nuevos en la sesión?
  - SÍ → entrada en `docs/HYPOTHESIS_LOG.md` con criterio testable + estado.
- [ ] ¿Hubo D# (drifts vs papers / divergencias vs MIROVA) nuevos?
  - SÍ → sección en `docs/MIROVA_DIVERGENCES.md` (catálogo VIVO) con evidencia +
    decisión + sesión esperada. (`DRIFTS_S17.md` quedó histórico-cerrado — AUDIT_S105.)
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
  - `docs/MIROVA_DIVERGENCES.md`: si hubo divergencia nueva/cerrada (catálogo vivo).
  - `docs/INDEX.md`: si se crearon docs nuevos (índice maestro, S105).
  - `docs/DATA_SOURCES.md`: si data sources cambiaron.
  - `docs/PAPERS_AUDIT.md`: si paper nuevo procesado.
  - (`SESSION_INDEX.md` quedó superseded por `SESSION_INDEX_CONSOLIDATED_S80.md` —
    el índice de sesiones vivo es MEMORY.md + bloques de arranque.)
- [ ] **Bloque de arranque + prompt copy-paste (regla S79)**:
  - `tasks/BLOQUE_ARRANQUE_S{N+1}.md` con plan ejecutivo de la próxima sesión.
  - Prompt copy-paste-able para Nicolás al final del bloque.
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
