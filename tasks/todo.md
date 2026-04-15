# Session 9 — Clean-slate plan post NULO contamination (2026-04-08)

## Context

Session 8 was invalidated by the NULO contamination bug (see
`tasks/lessons.md` L7.10). Every audit, every metric, every red flag from
S8 was computed against reference files that were 96% noise. All S8
artifacts have been **deleted**, not quarantined — contaminated data on
disk is a recontamination risk with no upside.

As of start of session 9:
- `scripts/rebuild_mirova_from_consolidado.py` is fixed with
  `VALID_CLASSES = {"Muy Bajo", "Bajo"}` and a hard-fail assert.
- All 11 `data/mirova/<volcano>.json` refs are regenerated and verified
  against expected counts (total 380 real records across the network).
- Pre-session-9 audit scripts and reports are deleted.
- **Pipeline code in `pipeline/` has NOT been touched since session 7.**

## Volcano calibration tiering

Based on actual MIROVA-real-record counts, volcanoes are in three tiers:

### Tier A — Calibration set (≥30 real records)
Used for quantitative calibration. Every metric must be reported for
these volcanoes.
- Lascar (154)
- PuyehueCordonCaulle (67)
- Lastarria (46)
- Isluga (44)
- Tupungatito (33)

### Tier B — Corroboration set (5-29 real records)
Used only as secondary check. Too few records for stable statistics but
large enough to flag gross errors.
- PlanchonPeteroa (18)
- Chaiten (11)
- Villarrica (5)

### Tier C — NRT-only, not calibratable (<5 records)
Kept in the NRT pipeline for opportunistic detection but **do not validate
the pipeline against them**. Zero or near-zero signal in the period means
any "ratio" or "capture rate" is undefined.
- NevadosDeChillan (2)
- Llaima (0)
- Copahue (0)

**Rule**: no calibration claim may cite Tier C volcanoes as evidence.

---

## Phase 1 — Build clean baseline (NO pipeline changes)

Goal: produce an honest, reproducible baseline of the current pipeline's
performance against clean MIROVA refs, across Tier A and Tier B
(8 volcanoes, 378 records).

### 1.1 — Write `experiments/11_strict_audit.py`

Parameters: `--volcano <stem>` or `--all`, `--tier A|B|all`.

Must do:
- Load `data/<volcano>.json` (ours) and `data/mirova/<volcano>.json` (ref)
- **HARD-FAIL** if any record in the ref has
  `clasificacion not in {"Muy Bajo", "Bajo"}`. Abort the run with a clear
  error pointing to L7.10. This is the defense-in-depth that would have
  caught S8 day one.
- **HARD-FAIL** if the ref `source` field does not start with
  `registro_vrp_consolidado`.
- Strict 1:1 pairing by `(date, hour, sensor_family)` with tolerance:
  MODIS ±60 min, VIIRS-I ±30 min, VIIRS-M ±30 min.
- Every record → one of `{TP, FP, FN}`. No "closest-of-day" fallback.
- Per-sensor and per-MIROVA-VRP-bucket:
  `<0.5`, `0.5-1`, `1-2`, `2-5`, `5-10`, `>10` MW
  - n MIROVA records in bucket
  - n TP, n FN, n FP-in-same-bucket
  - Ratio Q1/median/Q3 of `ours/mirova` for TPs only
- Save per-volcano snapshot JSON to `experiments/audit_s9/<volcano>.json`
- Summary metrics: precision, recall, F1, median ratio per volcano

### 1.2 — Run audit on Tier A + Tier B, produce report

- [ ] Run `experiments/11_strict_audit.py --tier A`
- [ ] Run `experiments/11_strict_audit.py --tier B`
- [ ] Collate into `experiments/AUDIT_S9_baseline.md`
  - One section per volcano with sensor × bucket table
  - Summary table across all 8 volcanoes
  - "Red flags" section: any volcano where `precision < 0.8` OR
    `median ratio ∉ [0.5, 2.0]`

### 1.3 — Acceptance criterion
Phase 1 is done when:
- `experiments/11_strict_audit.py` exists, committed, runs on any volcano.
- `experiments/AUDIT_S9_baseline.md` exists with all 8 Tier A+B volcanoes.
- 8 per-volcano snapshots exist in `experiments/audit_s9/`.
- **Zero lines of `pipeline/` code have changed.**

---

## Phase 2 — Root-cause investigation (NO pipeline changes)

For each red flag from Phase 1, identify the root cause using diagnostic
scripts only. Hypotheses inherited from sessions 6-7 that likely remain
valid (but need quantitative re-sizing against clean refs):

- **H1 — vent_path `t_bg + 1K` produces FPs at Lascar** (L7.7). The bug
  is structural and has nothing to do with the ref contamination. Must
  still verify the magnitude of FPs against clean Lascar (not 18 as
  previously reported; re-count).
- **H2 — MODIS eruption-scale path detects 0 records at Lascar** (L6.2).
  Structural, independent of refs. The per-record diagnostics in
  `n_anomalous_pixels` will confirm whether this is still true with
  current pipeline code.
- **H3 — local p95 + 2·σ_roi is the binding constraint** (L7.3). Needs
  instrumentation to re-verify after any previous session's reverts.

For each hypothesis:
- [ ] Write a short diagnostic script under `experiments/12_<hyp>.py`
- [ ] Produce evidence (numbers, distributions, records)
- [ ] Document in `experiments/ROOT_CAUSE_S9.md`

### 2.1 — Acceptance criterion
Phase 2 is done when each Phase 1 red flag has a written, data-backed
hypothesis in `experiments/ROOT_CAUSE_S9.md`. **Still zero pipeline
changes.**

---

## Phase 3 — Evidence-based fixes (one at a time)

One fix per commit. For each fix:
1. Save baseline snapshot: `experiments/<volcano>_pre_<fix_id>.json`.
2. Implement the fix in `pipeline/`.
3. Reprocess via `run_pipeline.py --overwrite` for affected dates.
4. Re-run `experiments/11_strict_audit.py` for affected volcanoes.
5. Compare pre/post in `experiments/<fix_id>_validation.md`.
6. Acceptance: target volcano metrics must improve AND no other volcano
   may regress beyond noise. If regression, revert.
7. New lesson in `tasks/lessons.md`.

Candidate fixes (priority pending Phase 2 evidence):
- F1: Tighten vent_path threshold → `t_bg + max(3K, 1.5·σ_bg)` (L7.7)
- F2: Revisit local p95 + 2·σ_roi (L7.3)
- F3: Decide on E3 NTI dual-criteria (L7.4 says VIIRS has it, MODIS doesn't)
- F4: Full VIIRS audit against clean refs (never done)

Do NOT pre-commit to F1-F4 ordering. Let Phase 2 decide.

---

## Phase 4 — Memory and docs cleanup

- [ ] Rewrite `memory/project_vrp_chile.md`:
  - Delete all session 5 calibration claims (ratio 1.02, capture 88.7%)
  - Delete any reference to `AUDIT_S8_baseline.md` (deleted)
  - Replace with S9 baseline numbers citing `AUDIT_S9_baseline.md`
- [ ] Update `tasks/lessons.md` with Phase 2-3 learnings
- [ ] Update `STATUS.md` and `README.md`:
  - Remove "calibration within X% of MIROVA" claims
  - Add explicit tiering (A/B/C) and note Tier C is not calibratable
- [ ] Add a brief "errata" section in README noting the session 8
  correction, so the public record is honest.

---

## Out of scope for session 9

- 34 new volcanoes pull
- Frontend changes
- Band-specific nighttime filter (L5.3)
- New sensors (Sentinel, GOES, Landsat)
- Merging `Peteroa` (1 record) into `PlanchonPeteroa` — decision deferred
- Any pipeline change before Phase 2 is complete

---

## Open questions (ask before Phase 3)

1. **Peteroa**: the CSV has a separate `Peteroa` entry (1 real record)
   distinct from `PlanchonPeteroa` (18). Merge? Ignore? Treat as its own
   volcano? Currently ignored.
2. **OCR backups (`_OLD_pre_consolidado.json`)**: keep as archaeological
   evidence or delete? User said keep if not a nuisance — current policy
   is keep.
3. **Tier C volcanoes in NRT**: Llaima/Copahue/NevadosDeChillan keep
   running in production but produce no calibration signal. OK to leave?
4. **Rollback of vent_path entirely**: if F1's conservative threshold
   doesn't kill all FPs, are we OK removing the vent-scale fallback and
   relying only on eruption-scale ROI? Costs weak-signal recall but
   kills structural FPs.
5. **SERNAGEOMIN ground truth**: is there a non-MIROVA validation source
   (thermal cameras, eruption logs, ash reports) we can use as a third
   corner? L7.1 flagged "MIROVA may have Andean bias" — we can only
   break that circular reasoning with an independent reference.

---

## Immediate next step

Write `experiments/11_strict_audit.py` with NULO hard-fail, then run it
on Lascar first (highest record count, best signal-to-noise for bugfinding).

---

## S12 status (2026-04-14)

**CERRADO**:
- ✅ NRT gap (Apr 10–14 invisible): fix `bf75df4`. LANCE fallback en
  `fetch.py`. 22 detecciones recuperadas en Isluga solo.
- ✅ F1b sigma cap en vent-path: commit `4c80429`. Recall recovery
  Tupungatito 10%→83%, Chaiten 13%→87%, Lastarria 34%→85%.
- ✅ Refs MIROVA actualizadas a 14042026 (+769 rows, +4 días,
  +37 refs Apr 10-14).
- ✅ `product_version` tagging + auto-upgrade NRT→Standard en store.py.
- ✅ `Peteroa`+`PlanchonPeteroa` merge en rebuild (28 refs total).
- ✅ CLAUDE.md actualizado: glosario TP/FP/FN + regla dashboard + regla
  subagentes para control de contexto.

**EN EJECUCIÓN** (F1b full history, ETA 19:45 UTC):
- 24429645510 PuyehueCordonCaulle
- 24429646443 Isluga
- 24429647594 Villarrica
- 24429648865 Llaima
- 24429651060 NevadosDeChillan
- 24429683329 Copahue

**PENDIENTE S13**:
- Auditoría uniforme todos los 11 volcanes con F1b aplicado uniformly.
- Trade-off analysis: bajar `MAX_VENT_SIGMA_CONTRIB_K` de 3.0 a 2.5 si
  FPs operacionales superan tolerancia del operador.
- **Test 1 integrado-ROI de Coppola 2015**: requerido para resolver
  Villarrica 0% recall arquitectural. Las 6 refs de Villarrica son
  NTI-only con señales sub-pixel (~0.05–0.21 MW) que ningún threshold
  per-pixel va a capturar. Implementar como método B: sum MIR radiance
  over full ROI, compare vs sigma_radiance_ROI. Documentado L12.2.
- Chaiten precision: 134 FPs a VRP 0.1–1 MW es mucho. Investigar si
  son fumarolas reales (MIROVA no consolida) vs ruido estructural.
- OCR cobertura: solo 301 refs totales, lo que limita OCR
  reclassification. Propuesta: expandir OCR scraping o dejar así y
  aceptar precision P_adj conservadora.
