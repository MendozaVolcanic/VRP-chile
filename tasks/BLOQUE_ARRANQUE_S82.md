# Bloque arranque S82 — prompt copy-paste para Nicolás

**Generado al cierre S81 (2026-05-26)** según feedback durable
`memory/feedback_session_close_handoff_prompt.md`.

---

## Copy-paste para Claude al inicio de S82

```
Inicio sesión S82 — VRP Chile, post-S81 (PR #221 abierto sin merge: VRP_TIR
gate provisional + PCC mirova_center clon literal). Worktree principal:
C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP-Chile-s80-consolidation/

Lectura obligatoria al inicio (orden estricto):
1. cat docs/AUDIT_INTEGRAL_S81.md   # síntesis 12 frentes, con corrección frente #4
2. cat docs/MIROVA_INTRA_RADIO_GATE_S81.md   # hallazgo crítico: 77% FPs MODIS son gate intra-radio
3. cat memory/reference_mirova_csv_scraper_tags.md (vía path absoluto memory dir)
   # interpretación correcta tags scraper Mirova-v1
4. cat docs/F46_VRP_TIR_GATE_S81.md   # mitigación VRP_TIR + roadmap F46 completo
5. cat tasks/backlog_data_integrity_session.md   # plan 7 items diferido S81
6. cat docs/SESSION_INDEX_CONSOLIDATED_S80.md + docs/META_RULES_S80.md

Primer comando obligatorio:
  cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP-Chile-s80-consolidation"
  git fetch origin --prune
  git log --oneline HEAD..origin/main
  gh pr view 221  # estado PR S81 abierto
  python -m pytest tests/ -q --tb=no | tail -3   # esperado: 513 passed, 24 skipped

ESTADO POST-S81:
- A1 nostalgic-aryabhata: CERRADA (tag pre-s81-discard-nostalgic-aryabhata)
- A2 VRP_TIR gate provisional: MERGED PR #221 (esperando mi merge si todavía abierto)
- A4 PCC mirova_center clon literal: MERGED PR #221
- A3 dedup PCC + endurecer store: DIFERIDO sesión data integrity dedicada
- Re-audit gap MIROVA con tags correctos: HECHO, hallazgo F-S81-A reformulado P0
- NRT operacional sano (post-2026-05-25 13:28Z fix F55)
- Dashboard parity 100%
- mirova-tif-archive activo (último push 2026-05-26)

TAREAS PRIORIZADAS S82 (decidir cuál arrancar):

P0 candidatos:
1. F-S81-A reformulado (gate intra-radio MIROVA MODIS) — 10-16h
   Plan completo: docs/MIROVA_INTRA_RADIO_GATE_S81.md
   Fase 1 diagnóstico clasificar ~800 FPs MODIS por path/cluster/NDVI/MOD14
   77% del ruido del pipeline en MODIS sale de ahí.

2. F46 completo VRP_TIR (Coppola 2024 Eq.16 background subtraction) — 14-16h
   Plan: docs/F46_VRP_TIR_BUG_S76.md + mitigación actual docs/F46_VRP_TIR_GATE_S81.md
   Repara 726 records históricos + desbloquea F31 + cura drift científico.

3. Sesión data integrity dedicada — 5-7h
   Plan: tasks/backlog_data_integrity_session.md (7 items, incluye dedup PCC,
   endurecer store.upsert_record, vrp_zero_reason schema, σ_bg guard, M11 regla).

P1:
4. F66 Tasks 7-15 (background kernel hybrid + consistency gate) — 8-12h
   Plan: docs/superpowers/plans/2026-05-26-f66-hybrid-bg-kernel-consistency-gate.md
   Branch claude/s79-f66-hybrid-bg-gate, Tasks 0-6 done. R2 manual Nicolás 5×3.

5. NdC recall 0% investigación — 4h
   4 granules específicos VIIRS-I 375m sub-pixel.
   Lista en docs/AUDIT_INTEGRAL_S81.md frente #4.

P2 (deuda técnica):
6. Tests sintéticos process_viirs core (cobertura 14%→50%) — 4-6h
7. Regenerar golden records — 2-3h
8. Worktree raíz s15-dev (1185 commits ahead) — decidir merge o eliminar.
9. EARTHDATA_TOKEN expira 2026-07-20 — calendario.

REGLAS VINCULANTES ACTIVAS:
- M2 persistencia in-vivo
- A45 tag defensivo + confirmación Nicolás antes pipeline/process_*.py, store.py, mirova_equivalent.yaml
- A47 NO paralelo sobre data/mirova_equivalent/
- A52 git fetch + pull en worktrees antes de asumir estado
- M1 cap PRs/sesión soft 12 hard 20
- M5 post-insert verify (git diff antes de commit cuando insertás entre funciones)
- Reference scraper tags Mirova-v1 (NUEVA S81): ALERTA_TERMICA / FALSO_POSITIVO /
  NULO / RUTINA son convención del scraper nuestro, NO terminología MIROVA.
  Para "MIROVA vio algo" contar ALERTA ∪ FALSO_POSITIVO.

Comunicame como geólogo: fenómeno físico → mecanismo pipeline → fórmula al final.

¿Qué priorizamos para S82?
```

---

## Hallazgos persistidos S81 (referencia rápida)

| Doc | Contenido |
|---|---|
| `docs/AUDIT_INTEGRAL_S81.md` | Síntesis 12 frentes auditoría integral con 12 subagentes |
| `docs/MIROVA_INTRA_RADIO_GATE_S81.md` | Hallazgo crítico re-audit: 77% FPs MODIS son gate intra-radio MIROVA faltante |
| `docs/F46_VRP_TIR_GATE_S81.md` | Mitigación provisional + roadmap F46 + checklist adopción |
| `docs/BEYOND_MIROVA_EXTENSIONS.md §10` | EXT-12 PCC dual-anchor (idea preservada) |
| `tasks/backlog_data_integrity_session.md` | Plan A.3 diferido (7 items, 5-7h) |
| `memory/reference_mirova_csv_scraper_tags.md` | Interpretación tags scraper Mirova-v1 (Nicolás explícito S81) |

## Tags defensivos S81

- `pre-s81-discard-nostalgic-aryabhata` — branch eliminada cero-content
- `pre-s81-vrp-tir-gate` — VRP_TIR provisional gate pre-cambio
- `pre-s81-pcc-mirova-center` — PCC mirova_center pre-update KMZ literal

## PR S81

[#221 — F46 provisional gate S81: silenciar vrp_tir_mw hasta fix completo](https://github.com/MendozaVolcanic/VRP-chile/pull/221)

3 commits:
- `767fb8f2` F46 provisional gate VRP_TIR (Opción D parte 1)
- `6b3d3820` PCC mirova_center adoptado coords KMZ MIROVA literal
- `f3a938ae` Cierre AUDIT_INTEGRAL + re-audit gap v2 + hallazgo intra-radio

513 tests passing, sin regresión.
