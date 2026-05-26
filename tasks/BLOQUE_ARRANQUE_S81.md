# Bloque arranque S81 — VRP Chile (post consolidación S80)

> Sesión nueva tras S80 (consolidación + auditoría post-pérdida-contexto). El
> proyecto está organizado: nuevas reglas, nuevo SESSION_INDEX canónico,
> MEMORY.md condensado, F66 implementación parcial Tasks 0-6.

## ⚡ Primer comando (LEER PRIMERO)

```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP-Chile-s80-consolidation"  # o cualquier worktree main-tracking
git fetch origin --prune
git pull --ff-only

# DOC ANCLA — leer primero
cat docs/SESSION_INDEX_CONSOLIDATED_S80.md  # 320 líneas, 5 min
cat docs/META_RULES_S80.md                  # reglas M1-M10 preventivas, vinculantes desde S81
```

Si vas a retomar F66 Tasks 7-15:

```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP-Chile-s79-f66"
git status   # debe estar limpio en branch claude/s79-f66-hybrid-bg-gate
git pull --ff-only origin claude/s79-f66-hybrid-bg-gate
python -m pytest tests/test_f66_bg_kernel_consistency.py -v  # 9/9 passing
python -m pytest tests/ -q --tb=no                            # 516 passed, 24 skipped
```

## 1. Estado al cierre S80 (resumen ejecutivo)

### Hecho
- **Auditoría completa** con 5 subagentes paralelos detectó contradicciones cross-source post-pérdida-contexto.
- **`docs/SESSION_INDEX_CONSOLIDATED_S80.md`**: mapa canónico S1-S80 que reemplaza a `SESSION_INDEX.md` viejo.
- **`docs/META_RULES_S80.md`**: reglas M1-M10 preventivas (cap PRs/sesión, persistencia in-vivo, audit trimestral, etc.).
- **`CLAUDE.md` proyecto**: A49-A53 nuevos aprendizajes S80.
- **MEMORY.md**: 762 → 158 líneas. Detalle a `memory/MEMORY_ARCHIVE_S32_S75.md`.
- **9 volcanes Tier A con `mirova_center`** extraído de KMZ oficiales MIROVA (gap #3 cerrado). 11/11 ahora documentados.
- **F66 Tasks 5-6** implementación M-band 750m + MODIS 1km. **Helper `compute_bg_stats` regresión fixed** (S79 etiquetó como "pre-existing" — era regresión Task 1 que comió el `return` final).
- **Cleanup**: 30 tasks/*.md superados archivados a `_archive_s80/`. Inventario data subdirs (696 MB), branches huérfanas (24 mergeadas + 12 únicas) documentados sin pruning destructivo.

### Pendiente prioritario S81

| P | Tema | Comando arranque |
|---|---|---|
| **P1** | F66 Task 7 profile yaml `_f66_dt5k.yaml` | Ver plan F66 Task 7 en `docs/superpowers/plans/2026-05-26-f66-hybrid-bg-kernel-consistency-gate.md` |
| **P2** | F66 Tasks 9-11 reproc SERIAL Copahue/Llaima/Villarrica 30d | A47 vinculante — NO paralelo `data/mirova_equivalent/` |
| **P3** | F66 Task 12 audit + Task 13 R2 manual Nicolás | 5 records × 3 vols vs MIROVA web |
| **P4** | F66 Task 15 PR + bloque arranque S82 | Solo después R2 manual |
| P5 | Investigar `claude/nostalgic-aryabhata-e05d1e` (40 commits únicos no mergeados) | `git log --oneline origin/claude/nostalgic-aryabhata-e05d1e --not origin/main` |
| P6 | Decidir cleanup branches mergeadas (24 candidatas) | Ver `docs/BRANCHES_CLEANUP_S80.md` |
| P7 | F31 VRPTIR Aveni A2 integración pipeline | Esperar evento baja-T enero-marzo |

## 2. F66 — recordatorio físico crítico

**Lo que no podés olvidar de S78-S80**:

- Path B (NTI absoluto >-0.8) **nunca dispara en Andes Chile**: 0/8142 TPs.
  F65 TOP 1 era noop. F61/F65 no son el approach correcto.
- **F66 dual-bg consistency gate** ataca el path D dNTI contextual donde
  realmente entran TPs y FPs. El gate pregunta si el calor en un pixel
  candidato es **espacialmente compacto** (kernel local 3×3 confirma
  ΔT >5K) o **artefacto regional** (kernel local plano, calor solo en
  el ring 5-25 km).
- F66 helper + 9 tests + integración en los 3 sensores I4/M13/B21-22
  todo done. Sin profile yaml que lo encienda, el flag queda OFF
  (mirova_equivalent default). NRT operacional intacto.

## 3. Reglas operacionales (sin cambios — vinculantes desde S81)

Detalle completo en `docs/META_RULES_S80.md`. Resumen:

- **M1** Cap soft 12 PRs/sesión, hard 20. Pasado soft → consolidar.
- **M2** Persistencia in-vivo. Hallazgo no trivial → persistir inmediato.
- **M3** "Pre-existing fails" requiere verificación contra `origin/main`.
- **M4** Audit flags trimestral (próximo S100 o 2026-08-15).
- **M5** Post-insert verify: no comer return adyacente (lección S80).
- **M6** Worktrees no-main pueden estar atrasados → `git fetch + pull` siempre.
- **M7** Bloque arranque self-contained: linkear `SESSION_INDEX_CONSOLIDATED`.
- **M8** Auditoría completa cada 20 sesiones (próxima S100).
- **M9** Rotar MEMORY.md al pasar 800 líneas (hecho S80, ahora 158).
- **M10** Subagentes paralelos con scope acotado + resumen ≤800 tokens.

Reglas técnicas:
- **A45** Tag defensivo + confirmación Nicolás antes pipeline NRT operacional.
- **A47** NO paralelo sobre `data/mirova_equivalent/` (race).
- **A44** Worktrees dedicados per subagente paralelo.
- **A49** Insert no debe comer return adyacente.
- **A50** Verificación cross-source pre etiquetar "pre-existing".
- **A52** Worktrees no-main pueden estar atrasados.
- **A53** Cap PRs/sesión + persistencia agresiva.

## 4. Tags defensivos en origin (rollback A45)

Última lista:
```
...
pre-s78-f53-test1-hot
pre-s78-f56-enable-exclude-zones
pre-s78-f63-cluster-rank
pre-s79-workflows-cleanup
pre-s79-f66-hybrid         → 9d4dd082
pre-s80-consolidation      → origin/main al inicio S80  ⭐ NUEVO
```

## 5. Sistema operacional S81

- **NRT cron**: cada 2h, matrix 11 Tier A + 19 extras. 7/10 últimas success post-PR #190.
- **Sync MIROVA**: cada 1h `sync-mirova-csv.yml`.
- **Workflows activos main**: 5 (`nrt`, `nrt-monitor`, `nrt-retry`, `pages-deploy`, `sync-mirova-csv`).
- **Workflows archivados**: 35+ en `_archive/` (PR #217).
- **Tests**: 507 passed + 24 skipped (main, sin F66 branch). F66 branch: 516 passed.

## 6. Veredicto cierre S80

- ✅ Contexto recuperado: SESSION_INDEX canónico + MEMORY.md ≤200 líneas.
- ✅ Reglas preventivas instaladas: META_RULES + A49-A53 en CLAUDE.md.
- ✅ Gap #3 cerrado: 11/11 Tier A con `mirova_center`.
- ✅ Regresión `compute_bg_stats` fixed (impacto: 0 — branch F66 aislada).
- ✅ Cleanup tasks/ aplicado.
- ⏳ F66 incompleto: Tasks 7-15 pendientes (no urgencia, NRT estable).
- ⚠️ Branches huérfanas + data subdirs 696 MB inventariados, pruning futuro.

**Próxima sesión empezar por `docs/SESSION_INDEX_CONSOLIDATED_S80.md`
y `docs/META_RULES_S80.md` antes de tocar nada.**
