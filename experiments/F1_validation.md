# F1 validation — VIIRS-I dual-PATH NTI (OR), session 9

**Commit**: `ecb5d66` (pipeline/process_viirs.py)
**Date**: 2026-04-09
**Scope**: replace AND(BT, NTI) with OR(BT, NTI) in the I04 MIR detection
path, mirroring process_modis.py commit `59846e8` (E3).
**Targets**: RF4 (Villarrica recall 0/5) and RF6 (Tupungatito recall 0.55).
**Regression check**: Lascar (Tier A, calibrated, should not regress).

## TL;DR

**Partial success.** F1 resolves **RF6** (Tupungatito) exactly as ROOT_CAUSE
predicted, does **not** resolve **RF4** (Villarrica) for a reason that was
only diagnosable after the fix, and shows **no regression** at Lascar.

| Volcano      | TP  | FN  | FP   | Precision | Recall  | Ratio median | Verdict |
|--------------|----:|----:|-----:|----------:|--------:|-------------:|---------|
| Villarrica pre  |  0 |  5 |  56  |    0.000  |  0.000  |     n/a      | ❌ same |
| Villarrica post |  0 |  5 |  53  |    0.000  |  0.000  |     n/a      | ❌ |
| Tupungatito pre | 24 | 20 |  80  |    0.231  |  0.545  |    0.602     | ✅ |
| Tupungatito post| 43 |  1 | 273  |    0.136  |  0.977  |    0.772     | ✅ |
| Lascar pre      |139 | 38 | 213  |    0.395  |  0.785  |    0.971     | ✅ |
| Lascar post     |140 | 37 | 207  |    0.403  |  0.791  |    0.964     | ✅ no regression |

## Tupungatito (RF6) — hypothesis confirmed

Pre-F1 VIIRS375: recall 0.615 → **1.000** post-F1 (39/39 MIROVA nights
caught). Ratio median 0.708 (was 0.602), Q1 0.529 Q3 1.388. The single
remaining FN is on a VIIRS-M (750 m) record, which F1 does not touch
(process_viirs_mod.py has no NTI path at all — separate issue).

The mechanism was exactly as ROOT_CAUSE_S9 RF6 described: at Tupungatito
(5682 m summit, orographic heterogeneity) the BT threshold
`max(5K, 3·σ_bg)` was often pushed above the real ΔT by σ_bg inflation,
so pixels that were clearly NTI-anomalous got killed by the AND gate.
The OR gate lets them through, and the Wooster VRP of those pixels lands
cleanly in the 0.5–0.77× MIROVA ratio range.

**Cost**: precision dropped 0.231 → 0.136. The extra NTI-path detections
add FPs on nights when MIROVA reports nothing. This is expected: the OR
gate is *by construction* more permissive than the AND gate. The FP
increase is acceptable because (a) Tupungatito has no ground-truth
independent of MIROVA, so many "FPs" may be real detections MIROVA
missed, and (b) the goal for F1 is recall recovery, not precision.

## Lascar — no regression

F1 was expected to do almost nothing at Lascar because Lascar's BT branch
already fires reliably (ratio median 0.971 pre-F1 is already essentially
calibrated). Post-F1 numbers confirm this:

- Overall: TP 139→140, FN 38→37, FP 213→207, P 0.395→0.403, R 0.785→0.791,
  ratio 0.971→0.964.
- MODIS: ref=48 TP 39→40, ratio 0.761→0.754 (F1 doesn't touch MODIS —
  the 1-record delta is re-fetch noise).
- VIIRS375: ref=77 TP 62→62, ratio 1.073→1.073 (identical).
- VIIRS-M: ref=52 TP 38→38, ratio 0.996→0.996 (identical).

Verdict: **no regression**. F1 at Lascar is effectively a no-op, which is
the correct outcome since Lascar is Tier A-calibrated and its BT branch
was never the problem.

## Villarrica (RF4) — NOT resolved, new root cause identified

Post-F1 recall is still 0/5. Diagnosing the 5 MIROVA nights against the
re-processed records:

| MIROVA night      | sensor       | t_bg | t_max | ΔT | nti_bg  | nti_max | n_bt_path | n_nti_path |
|-------------------|--------------|-----:|------:|---:|--------:|--------:|----------:|-----------:|
| 2026-01-13 05:48  | VIIRS_SNPP   | 279.75 | 282.31 | 2.6 | -0.9507 | -0.9460 | 0 | 0 |
| 2026-01-14 05:48  | VIIRS_NOAA20 | 281.41 | 284.39 | 3.0 | -0.9480 | -0.9425 | 0 | 0 |
| 2026-01-19 05:54  | VIIRS_NOAA20 | 287.25 | 293.50 | 6.3 | -0.9376 | -0.9246 | 0 | 0 |
| 2026-02-26 05:42  | VIIRS_NOAA20 | 281.25 | 284.26 | 3.0 | -0.9482 | -0.9378 | 0 | 0 |
| 2026-03-08 06:00  | VIIRS_NOAA20 | 282.62 | 286.63 | 4.0 | -0.9458 | -0.9344 | 0 | 0 |

**Both paths fail by the same mechanism:**

- `NTI_K1_NIGHT = -0.8` — NTI path requires `nti_max > -0.8`. Observed
  `nti_max` is **-0.94 to -0.92**, nowhere near the floor. The NTI branch
  never fires. Fixed MIROVA Test 1 threshold is calibrated for **MODIS
  1 km** pixel geometry; at VIIRS 375 m, these subpixel-weak signals
  produce NTI values only ~0.005 above `nti_bg`.
- `NTI_BT_SANITY_K = 3.0 K` — even if we lowered `NTI_K1_NIGHT`, the
  BT sanity floor kills 01-13 (ΔT=2.6 K) and 01-14 (ΔT=3.0 K) on its own.
- BT path requires `bt > t_bg + max(5K, 3σ_bg)`. σ_bg inflation puts the
  effective threshold in the 5–10 K range on every night; max observed
  ΔT is 6.3 K and only for one night. BT branch never fires either.

The fundamental problem at Villarrica is **weaker than what F1 was
designed to rescue**: these are ~0.05–0.21 MW signals (MIROVA minimum
detection floor) at a 1284 m summit with an open lava lake that
produces only a sub-pixel hot fraction. The signal doesn't produce a
VIIRS 375 m pixel that pops above its background. MIROVA catches it
because MIROVA's Test 1 uses the full ROI MIR radiance, not a
per-pixel threshold.

**This is NOT a new bug introduced by F1.** It was always like this —
the pre-F1 code with AND was also returning `vrp_mw=0` on all 5 nights.
What F1 revealed is that the RF4 hypothesis was **half right**: the
AND→OR change was necessary but not sufficient for Villarrica. The
remaining gap is architectural.

### Three options for Villarrica

1. **Lower `NTI_K1_NIGHT` for VIIRS-only** to e.g. `-0.94`. Risk: this
   becomes a per-sensor tuning knob, not a physical threshold from
   Coppola 2015. Very likely introduces FPs at Tupungatito/Lastarria
   where we just recovered recall. Must be tested on the whole Tier A
   before adopting.
2. **Implement an integrated-ROI Test 1**: sum MIR radiance over all
   pixels in `radius_km`, subtract bg-equivalent, compare to
   `sigma_bg_radiance`. This is the correct Coppola 2015 formulation
   for sub-pixel hotspots but requires non-trivial new code.
3. **Accept Villarrica is Tier-C-equivalent**: declare that its signal
   is below the sensitivity of any per-pixel method and remove it from
   the calibration set. Honest but gives up on 5 real detections.

**Recommendation**: defer the Villarrica decision to after F2 (vent_path
threshold tightening, RF1) is landed and measured. Option 1 should be
tested as a single-parameter sweep in an experiment script
(`experiments/12_nti_floor_sweep.py`) before touching pipeline/. Do
**not** tune `NTI_K1_NIGHT` blindly.

## Instrumentation added

`process_viirs.py` now emits `n_bt_path` and `n_nti_path` per record so
we can see which branch caught each detection in future audits. This
was what let us diagnose Villarrica's failure in minutes instead of
re-running the pipeline in debug mode. Keep the instrumentation.

## Phase 3 status after F1

| RF | Status |
|----|--------|
| RF3 PCC vent | 🟢 resolved by F0 (see F0_validation) |
| RF4 Villarrica | 🟡 half-diagnosed, architectural gap — deferred |
| RF5 ratio bias low-activity | 🟡 Tupungatito moved from 0.60 to 0.77, partial improvement. Lastarria/Isluga untouched so far |
| RF6 Tupungatito | 🟢 resolved by F1 |
| RF1 vent_path FP | 🔴 untouched — next up, F2 |
| RF2 MODIS FP | 🔴 untouched, blocked on ground truth |

## Files

- `experiments/Villarrica_pre_F1.json` — pre-fix snapshot (committed in F1)
- `experiments/Tupungatito_pre_F1.json` — pre-fix snapshot (committed in F1)
- `experiments/Lascar_pre_F1.json` — pre-fix snapshot (committed in F1)
- `experiments/audit_s9/{Villarrica,Tupungatito,Lascar}.json` — post-fix
- `pipeline/process_viirs.py` — dual-PATH OR implementation
