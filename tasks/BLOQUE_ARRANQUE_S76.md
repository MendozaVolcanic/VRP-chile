# Bloque arranque S76 — VRP Chile (post cierre S75 2026-05-24)

> Continuación tras cierre S75. 13+ PRs S75 mergeados a main. F30 frontend bugs
> 100% (7/7 estructurales). F31 Aveni VRPTIR plan: A1+A3+A4+A6 ✅, A2+A5 pending.
> Tag defensivo `pre-s75-vrptir-a2-integration` snapshot pre-A2.

## 1. Estado al cierre S75

### F2.8 saturation guard — operacional + empíricamente validado (S74)

Fix mergeado main + reproc empírico run 26345305675 SUCCESS. Fósil PP 695,431 MW
eliminado (post-fix pc.vrp_mw=3.16 MW). Auto-commit `18e8421`.

### F30 frontend bugs — **100% (7/7 estructurales)** ✅

| Bug | Status | PR |
|---|---|---|
| 6 (tabla NRT eqVrp) | ✅ | #142 |
| 7 (marker log10) | ✅ | #142 |
| 8 (auto-refresh 15min + timestamp) | ✅ | #149 |
| 9 (sensor toggle 5 paneles) | ✅ | #145 |
| 10 (sessionStorage persistence) | ✅ | #142 |
| 11a (distance scatter toggle) | ✅ | #142 |
| 11b (CARD_COUNT_WINDOW_DAYS) | ✅ | #155 |

### F31 Aveni VRPTIR plan — A1+A3+A4+A6 ✅, A2+A5 pending

| Task | Status | PR | Confidence A35 |
|---|---|---|---|
| A1 TIRVolcH detector base | ✅ | #153 | confidence:HIGH-VERIFIED (PR #156 9/9 constantes MATCH) |
| A2 Integración process_viirs.py | 🔄 **PENDING S76** (tag defensivo pusheado) | — | — |
| A3 Profile flag + experimental_lowT | ✅ | #154 | HIGH (PDF Aveni 2025 PR #150) |
| A4 Tests TDD | ✅ 43 tests (19 VRPTIR + 4 profile flag + 20 TIRVolcH) | #146+#153+#154 | n/a |
| A5 Piloto Copahue/PP | Pending | — | — |
| A6 PDF verify | ✅ Aveni 2025 (PR #150) + Aveni 2024 (PR #156) | #150+#156 | HIGH |

### Métricas S75

- **Tests**: 456 passed, 24 skipped (vs 432 S74 → +24 nuevos: 20 TIRVolcH + 4 profile flag)
- **PRs S75 mergeados**: 8 (#152-#156, plus race-recovery PRs)
- **Tags defensivos**: 2 (`pre-s73-data-cleanup` S73, `pre-s75-vrptir-a2-integration` S75)
- **0 regresiones** operacional

## 2. Priorización S76 (en orden ejecutar)

### P1 — F31 Task A2: integración VRPTIR/TIRVolcH a process_viirs.py

**Pre-requisito tag defensivo ya hecho**: `pre-s75-vrptir-a2-integration` apunta
a `b6b7e312` (post-PR #156 Aveni 2024 verify).

**Decisión Nicolás S75**: pausa para sesión fresca. Razón: cambio en pipeline
NRT operacional crítico.

**Approach recomendado S76 (mínimo conservador)**:

1. **A2 mínimo: solo reporting-only fields** (~30 min):
   ```python
   # En pipeline/process_viirs.py ANTES del return final del record:
   if ENABLE_VRPTIR_AVENI and bands.get("I05") is not None and not np.isnan(t_bg_i05):
       from pipeline.vrptir import vrp_tir_mw, LAMBDA_VIIRS_I5, A_PIX_VIIRS_I, filter_t_range
       bt_i05_2d = bands["I05"]
       # Usar pixels detectados por nuestro pipeline (NTI/dNTI/Test1) como
       # proxy de TIRVolcH para piloto S76. CAVEAT: NO es TIRVolcH puro
       # (requiere baseline 10-yr pre-computed). Es "our-detector + VRPTIR formula".
       hot_mask_for_vrptir = ...  # nuestro hot_mask existente (NTI/dNTI/etc)
       bt_hot = bt_i05_2d[hot_mask_for_vrptir]
       in_range_mask = filter_t_range(bt_hot, VRPTIR_T_MIN_K, VRPTIR_T_MAX_K)
       bt_hot_inrange = bt_hot[in_range_mask]
       if len(bt_hot_inrange) > 0:
           vrptir_mw = vrp_tir_mw(bt_hot_inrange, t_bg_i05, LAMBDA_VIIRS_I5, A_PIX_VIIRS_I)
           record["vrptir_aveni_mw"] = round(vrptir_mw, 3)
           record["vrptir_aveni_n_pixels"] = int(len(bt_hot_inrange))
           record["vrptir_aveni_caveat"] = "pipeline-detector_proxy"
       else:
           record["vrptir_aveni_mw"] = 0.0
           record["vrptir_aveni_n_pixels"] = 0
   ```

2. **A2 completo (S76+ futuro)**: implementar TIRVolcH real con baselines
   pre-computed. Pre-tasks:
   - Crear `scripts/build_tirvolch_baselines.py` — barre 10-yr VIIRS I5
     cloud-free per volcán Tier A → `data/tirvolch_baselines/<volcano>.npz`
   - Integrar `detect_tirvolch(bt_i05, baseline_mean, baseline_std)` real
   - Validar contra Aveni 2025 Mt Ruapehu ρ=0.93 ground truth si posible
   - ETA: 1-2 sesiones

3. **Fix D1 docstring TIRVolcH**: eliminar mención "Copahue" del docstring de
   `pipeline/detect_tirvolch.py` (paper Aveni 2024 NO menciona Copahue,
   verificado PR #156).

### P2 — F31 Task A5: piloto experimental_lowT.yaml

**Pre-requisito A2 funcional**: profile flag debe activar VRPTIR end-to-end.

Reproc 30d con perfil `experimental_lowT` sobre **3 volcanes candidatos**:
- **Lastarria** (fumarolas — análogo Vulcano)
- **Copahue** (lago cratérico — análogo El Chichón)
- **Planchón-Peteroa** (lago cratérico — Aguilera 2021 ground truth Qvolc 7-59 MW)

Audit:
- Recall vs MIROVA NRT CONS+OCR
- Ratio `vrptir_aveni_mw` vs Aguilera 2021 Qvolc (PP es candidato directo
  validación cruzada — paper open access doi:10.3389/feart.2021.722056)

### P3 — Adopción S77+ si piloto valida

Si recall/ratio aceptables en piloto: mover `enable_vrptir_aveni: true` de
experimental_lowT a mirova_equivalent operacional. **NO antes de validar
contra ground truth chileno**.

### P4 — Persistir cambios en CLAUDE.md

Hay 3-4 aprendizajes meta S75 worth documentar (después A2 done):
- **A44 (candidato)**: race conditions worktree compartido entre múltiples
  subagentes paralelos. Workaround S76+: worktree dedicado per subagente via
  `git worktree add ../VRP-Chile-s76-<task>`.
- **A45 (candidato)**: cuando tarea toca pipeline operacional NRT, A38+A39
  obligatorio (tag defensivo + confirmación explícita) — incluso si Claude
  cree que es seguro.

### P5 — Backup data/_*/ (defer S77+, hoy)

41 subdirs experimentales, ~696 MB. Inventario PR #140 docs/F28_DATA_ARCHIVE_INVENTORY.md.
**Decisión S73 informada**: NO archivar, espacio no apremia + valor beyond-MIROVA.
Tag git `pre-s73-data-cleanup` preserva snapshot.

## 3. Backlog adicional (sin urgencia)

- **TROPOMI SO2** integración (combinación VRP+SO2 multi-parameter — referencia
  Coppola 2026 SSRN Lascar, paper Coppola 2025 Ambae sub-plinian)
- **Task Scheduler Windows** NRT local + 48h obs (P2 desde S73)
- **Paper VRP Chile P5** draft (skills sci-writer disponibles)
- **Aguilera 2021 Table S1** supplementary (Qvolc Landsat 1984-2020) para
  experimento recall PP histórico

## 4. Quick start S76

```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP-Chile-s70"

# Sync
git fetch origin --prune
# (main está en otro worktree — usar pull --rebase desde branch propia)
git checkout -B work-s76 origin/main

# Verificar tag defensivo accesible
git tag -l "pre-s7*"

# Tests baseline
python -m pytest tests/ -q
# Target: 456 passed, 24 skipped

# Si Task A2 sale mal, rollback:
git checkout pre-s75-vrptir-a2-integration -- pipeline/process_viirs.py
```

**Arrancar S76 leyendo (en orden)**:
1. Este doc
2. `docs/F31_AVENI_GRL_2025_EXTRACT.md` (PR #151)
3. `docs/F31_AVENI_2024_TIRVOLCH_VERIFY.md` (PR #156)
4. `docs/F31_AVENI_VRPTIR_PLAN_S74.md` (plan A1-A6)
5. `docs/F31_AGUILERA_2021_PETEROA.md` (ground truth PP)

## 5. Aprendizajes meta S75 (pendiente documentar en CLAUDE.md)

### A44 candidato: worktrees dedicados per subagente paralelo

Race conditions documentadas S75:
- Worktree compartido VRP-Chile-s70/ entre N procesos (yo foreground + M
  subagentes background). Cada uno `git checkout -b` → branch switch global del
  worktree → otros procesos atrapan branch wrong.
- Mitigaciones intentadas: stash + cherry-pick + branch v2. Funcionan pero
  con costos de tiempo.
- Solución S76+ recomendada: cada subagente paralelo crea su worktree dedicado
  vía `git worktree add ../VRP-Chile-s76-<task> origin/main`. Independiente
  filesystem state. Cleanup post-merge con `git worktree remove`.
- Caveat espacio: cada worktree es checkout completo (~hundred MB). Para
  disco al 98% (Nicolás S73), considerar shallow clone o sparse-checkout.

### A45 candidato: tag defensivo + A39 en pipeline NRT operacional

Reforzar A38+A39 cuando target = código pipeline crítico:
- Tag defensivo OBLIGATORIO antes de modificar process_modis.py / process_viirs.py
- Confirmación explícita Nicolás aunque tests baseline OK (A39 excepción
  "alta criticidad")
- Razón: si introducimos bug en pipeline NRT que pasa los tests, NRT cron lo
  ejecutará cada 2h → 12 corridas/día sobre 11+ volcanes → potencial daño
  masivo data antes de detectar
- **Lección S75**: Nicolás aplicó esto bien preguntando "no tienes que salvar
  la configuración actual antes? eso no sería más conservador?" — antes de
  que yo procediera con A2. Era el sanity check correcto.

## 6. PRs S73-S75 mergeados (referencia rápida)

| # | PR título | Commit |
|---|---|---|
| 133 | F2.8 saturation guard MODIS+VIIRS | ab38cb0 |
| 134 | F2.8 workflow heredoc hotfix | cebc463 |
| 135 | BLOQUE_ARRANQUE_S74 | b842c2b |
| 136 | F28_LIT_SEARCH inicial | 83d8901 |
| 137 | F28_LIT_SEARCH 4-way + Dhage leído | 73af5e7 |
| 138 | F2.8 workflow rename v2 | f05a979 |
| 139 | CSV path dehardcoded | 9e028f5 |
| 140 | F30 frontend bugs plan | 5b05158 |
| 141 | F31 Aveni VRPTIR plan | 74659cc |
| 142 | F30 Bugs 6+7+10+11a | 31740a7 |
| 143 | F2.8 v3 + Norway Problem fix | d2ea629 |
| 144 | CLAUDE.md A39+A40-A42 | 4a56c59 |
| 145 | F30 Bug 9 sensor toggle | 3374dbc |
| 146 | F31 VRPTIR formula + 19 tests | c85e60a |
| 147 | CLAUDE.md A43 Norway Problem | 8f528b5 |
| 148 | F2.8 v3 EARTHDATA_TOKEN fix | ab4d3a0 |
| 149 | F30 Bug 8 auto-refresh 15min | e1cc774 |
| 150 | A35 caveat RESOLVED Aveni 2025 PDF verified | b7dce05 |
| 151 | F31 Aveni 2025 GRL extract verbatim | bab4224 |
| 152 | Aguilera 2021 PP crater lake extract | 138cc0d |
| 153 | F31 Task A1 TIRVolcH detector | f5e1187 |
| 154 | F31 Task A3 profile flag + experimental_lowT | 3955841 |
| 155 | F30 Bug 11b CARD_COUNT_WINDOW_DAYS (cierra F30) | 8513b70 |
| 156 | Aveni 2024 TIRVolcH constants verified | b6b7e31 |
| `18e8421` | F2.8.f reproc auto-commit (vrp-bot) | (no PR) |

## 7. Cierre S75 — métricas

- **8 PRs S75 mergeados** (#152-#156 más race-recovery)
- **F30**: 100% (7/7 estructurales)
- **F31**: A1+A3+A4+A6 ✅, A2+A5 pending S76
- **A35 caveats RESUELTOS**: VRPTIR coefs + TIRVolcH constants (9/9 verbatim PDF)
- **Tag defensivo S75**: `pre-s75-vrptir-a2-integration` snapshot pre-A2
- **0 regresiones** operacional
- **3 race conditions** worktree compartido — A44 lección documentada
