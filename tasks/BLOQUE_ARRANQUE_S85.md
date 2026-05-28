# BLOQUE ARRANQUE S85

**Sesión previa**: S84 (2026-05-27/28). Cerró con 3 hitos grandes + 4 lecciones
durables nuevas.

## §0 — Worktree canónico

**Path**: `C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile`
(raíz reapuntado a main en S82-prep).

**Primer comando**:
```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git fetch origin --prune
git log --oneline HEAD..origin/main  # ¿algo nuevo?
git pull --ff-only
cat tasks/BLOQUE_ARRANQUE_S85.md
```

## Estado al cierre S84

### 3 hitos mergeados

1. **PR #225** — Fix F55 bypass preservando `_http_session` setup. NRT estaba
   100% caído silentemente desde 2026-05-23. Ahora produce records reales
   confirmado en cron 03:57-04:30 UTC del 2026-05-28 (todos los Tier A
   actualizados).

2. **PR #226** — Adopción operacional F-S81-A gate Path D MODIS intra-radio.
   Reduce 93-98% pixels `dnti_ctx` fuera del cono en TODOS los Tier A.
   Cero regresión de TPs MIROVA (Lascar 25/25). Tag `pre-s84-f-s81-a-adoption`
   → `4d9b8771`. Default operacional ahora ON.

3. **Workflow `reproc-ab-f-s81-a-intra-radio.yml`**: agregado
   `EARTHDATA_TOKEN`, timeout 50→140 min, max-parallel 8. Template para
   futuros reprocs A/B 45d.

### Hallazgos durables persistidos

- `docs/F_S81_A_ADOPTION_S84.md` — decisión adopción + datos audit.
- `docs/F_S81_B_BACKLOG_PATH_ABC_GATES.md` — plan Fase B.
- `docs/F_S81_B_SANITY_VIIRS.md` — **1332 ALERTAs MIROVA Tier A** (CONS+OCR)
  caen **100% dentro de inner_radius**. Gate intra-radio análogo en VIIRS
  empíricamente seguro.
- `docs/META_RULES_S80.md` — lecciones A56-A59 agregadas:
  - **A56**: bypass parcial 3rd-party debe preservar responsabilidades
    no-target.
  - **A57**: `set +e` + script tolerante + workflow exit 0 = success
    engañoso. Agregar assertion de contenido.
  - **A58**: NRT healthcheck staleness de records, no solo file_updated.
  - **A59**: reproc 45d × N sensores requiere timeout-minutes ≥ 140.

## Plan ejecutivo S85

### P0 — Fase B Path A/B/C gates intra-radio (priorizado)

Doc plan: `docs/F_S81_B_BACKLOG_PATH_ABC_GATES.md`.

1. **B0 — Audit cuántos R3 residuales** vienen de cada path en operacional.
   Output: tabla `R3_residual_by_path.md` con distribución Path A/B/C/D/Test1.
2. **B1 — Refactor helper** `path_d_intra_radio.py` a `intra_radio_gate.py`
   genérico parametrizando array de entrada. Wrappers per-path.
3. **B2 — Flag bitmask** `intra_radio_gate_paths: ["A","B","C","D"]` en yaml.
4. **B3 — A/B reproc** con profile `_f_s81_b_all_paths` vs `_f_s81_a_only`.
   Workflow template: copiar `reproc-ab-f-s81-a-intra-radio.yml` (ya tiene
   token + timeout 140 + max-parallel 8). Tag `pre-s85-f-s81-b-fase-b`.
5. **B4 — Audit** mismo script `experiments/_s83_f_s81_a/audit.py`
   parametrizado.
6. **B5 — Adopción** si R3 → 0 sin pérdida TPs.

Estimación: 7-10h, sesión completa o partida.

### P1 — Implementar healthcheck NRT staleness (A58)

Workflow `nrt-healthcheck.yml` cron diario:
- Levanta JSONs de los 11 Tier A.
- Si `max(record.datetime_utc) < now() - 48h` → abre issue + envía notif.

ETA: 1-2h. Justificado por bug F55 que tardó 4 días en detectarse.

### P2 — Implementar assertion contenido post-NRT (A57)

Agregar step al `nrt.yml` que verifique que el JSON modificado tiene
records nuevos (no solo "Done."). Si no, FAIL el step.

ETA: 30-45 min. Bajo costo, alto valor preventivo.

### P3 — Auditoría todos workflows `reproc-ab-*` por EARTHDATA_TOKEN faltante

S84 detectó que `reproc-ab-f-s81-a-intra-radio.yml` no tenía TOKEN. Verificar
los demás `.github/workflows/reproc-ab-*.yml` (varios archivados, algunos
activos) por mismo bug. Auditoría rápida con grep + fix masivo.

ETA: 30 min.

## Reglas vinculantes activas

- **A45** tag defensivo + confirmación Nicolás antes de
  `pipeline/process_*.py`, `store.py`, `mirova_equivalent.yaml`.
- **A47** NO paralelo local sobre `data/mirova_equivalent/`.
- **A49** verificar `git diff` post-insert.
- **A50** cross-source verify `origin/main` antes de etiquetar "pre-existing".
- **A52** `git fetch + pull` en worktrees.
- **A56-A59** (S84) — ver `docs/META_RULES_S80.md`.
- **M1** cap PRs/sesión soft 12 hard 20.
- **M2** persistencia in-vivo (no esperar cierre).

## Comunicación

Hablarle a Nicolás como geólogo: fenómeno físico → mecanismo pipeline →
fórmula al final. Cuando proponga adopción operacional, explicar primero
qué hace el cambio sobre el campo térmico, después por qué el audit valida.

## Tags defensivos vigentes

- `pre-s84-f55-bypass-fix` → b309bb04 (pre fix F55 PR #225)
- `pre-s84-f-s81-a-adoption` → 4d9b8771 (pre adopción PR #226)
- (anteriores: `pre-s83-f-s81-a-gate-modis-path-d`, `pre-s82-worktree-switch`,
  `pre-s81-discard-nostalgic-aryabhata`, `pre-s81-pcc-mirova-center`,
  `pre-s81-vrp-tir-gate`, `pre-s80-consolidation`)

## Prompt copy-paste para próxima sesión

```
Sesión S85 — VRP Chile. S84 cerró con 3 hitos:
1. Fix F55 bypass (PR #225) — NRT desbloqueado de bug silencioso 4 días.
2. Adopción F-S81-A gate Path D MODIS intra-radio (PR #226) operacional.
3. Lecciones A56-A59 persistidas en docs/META_RULES_S80.md.

Worktree: C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile

Primer comando:
  cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
  git fetch origin --prune && git pull --ff-only
  cat tasks/BLOQUE_ARRANQUE_S85.md

Lectura obligatoria:
1. tasks/BLOQUE_ARRANQUE_S85.md (plan ejecutivo)
2. docs/F_S81_A_ADOPTION_S84.md (decisión adopción + caveat R3)
3. docs/F_S81_B_BACKLOG_PATH_ABC_GATES.md (Fase B plan)
4. docs/META_RULES_S80.md sección "Lecciones agregadas S84" (A56-A59)

Plan P0:
1. B0 — Audit cuántos R3 residuales vienen de cada path.
2. B1-B2 — Refactor helper + flag bitmask.
3. B3 — A/B reproc Fase B (all paths intra-radio).
4. B4-B5 — Audit + adopción si R3 → 0.

P1 — healthcheck NRT staleness (A58).
P2 — assertion contenido NRT (A57).
P3 — auditoría TOKEN en demás workflows reproc-ab-*.

Reglas activas: A45, A47, A49, A50, A52, A56-A59, M1, M2.

Comunicame como geólogo: fenómeno → mecanismo pipeline → fórmula al final.
```
