# VRP Chile — Lessons learned

## Session 5 (2026-04-07)

### L5.1 — `store.py` append_record dedupes by (datetime_utc, sensor)
When reprocessing an existing range after an algorithm change, the default
behavior SKIPS any record already present. To force recalculation on existing
records, pass `overwrite=True` to `append_record` (now wired through
`run_pipeline.py --overwrite` and the `nrt.yml` workflow_dispatch input
`overwrite=true`).

**Why it matters:** the scan-angle pixel-area fix from session 4 (commits
1e3428a, 9da2157) would otherwise never have been applied to existing JSON
records. Bug discovered after a "successful" Villarrica reprocess only added
1 new record and touched 0 existing ones — the VRP values in the JSON still
used the old nadir areas.

### L5.2 — Scan-angle fix validated against MIROVA (Lascar, 203 refs)
The scan-angle pixel-area correction (session 4) was validated end-to-end on
Lascar's full 2026 dataset against 203 MIROVA reference records:

| Metric        | Pre-fix | Post-fix |
|---------------|---------|----------|
| Capture rate  | 81.3%   | **88.7%** |
| Mean ratio    | 0.60    | **1.14** |
| Median ratio  | 0.57    | **1.02** |

Improvement factors per sensor family: MODIS 1.87x, VIIRS-I 1.92x, VIIRS-M
1.91x — uniform, matching theoretical prediction (sec³ correction for MODIS,
soft cap 2.0 for VIIRS bow-tie-aggregated pixels).

**The original "0.55 nuestro/MIROVA bias" documented in sessions 3-4 is
now effectively eliminated** — median ratio 1.02 means calibration is
within ~2% of MIROVA.

### L5.3 — MIROVA reports daytime VIIRS375 detections (not in our pipeline)
Several Lascar outliers in the validation (ratio <0.1 or >3) trace to MIROVA
VIIRS375 records at ~18:XX UTC, which is **daytime** at Lascar (local
~14:30). Our pipeline has a global nighttime filter at the `store.py` level
that rejects ALL daytime records for any sensor/band.

**Hypothesis**: MIROVA extracts daytime VIIRS detections using I05 TIR band
(11.45 μm, Stefan-Boltzmann via Aveni 2024 TIRVolcH methodology). TIR is
robust to solar contamination; only MIR (3-4 μm) suffers from it.

**Correct methodology**: the nighttime filter should be **band-specific**:
- MIR (MODIS B21/22, VIIRS I04, VIIRS M13): nighttime-only ✔
- TIR (VIIRS I05 11μm): day and night OK (Aveni 2024)

Impact: a few % extra capture rate would be achievable by allowing daytime
I05 TIR processing through a separate code path in `process_viirs.py`. This
is a future improvement — NOT acted upon in session 5.

### L5.6 — Caveat: the MIROVA reference CSV is incomplete
**User info, 2026-04-08**: the CSV scrape from mirovaweb.it does NOT contain
every MIROVA detection. Specifically some VIIRS 375m and VIIRS 750m records
are missing from the CSV. Implication:

- `capture_rate` measured against `data/mirova/*.json` is a **lower bound**,
  not an absolute truth. A "missed" reference may simply never have been in
  the scraped CSV to begin with.
- **Ratio (quantitative calibration) IS still valid**: when both pipelines
  detect the same event, the VRP comparison is 1:1 real. Median ratio 1.02
  post scan-fix is a legitimate calibration metric.
- **Deprioritize "discovery" metrics**: `close_pass_zero_vrp` and
  `no_close_pass` categories in diagnostic reports may contain refs that
  never existed in the CSV. Don't invest in "capture rate" fixes unless
  you can prove the ref was actually present.
- **Focus future experiments on ratio/bias reduction**, not on catching
  additional references.

### L5.7 — Detection threshold is dominated by 3*sigma_bg, not the 5K floor
The MODIS/VIIRS eruption-scale detection threshold is
`max(ANOMALY_THRESHOLD_K=5.0, N_SIGMA=3.0 * sigma_bg)`. On Lascar's MODIS
records that underestimate 2-10 MW MIROVA signals by 2-3x, the observed
ΔT_max is ~5-7 K — above the 5 K floor but below `3*sigma_bg ≈ 7.5 K` when
sigma is ~2.5 K.

This reframes Finding F3 (bg annulus overlap):
- The overlap bug matters NOT because hot pixels elevate the MEAN t_bg
  (empirically only 2.8% of Lascar anomaly pixels are in the overlap zone,
  so mean shift is minimal)
- But because the few hot pixels that DO fall in the overlap zone inflate
  the STANDARD DEVIATION sigma_bg. Even a handful of outliers can push
  sigma from 1.5 K to 2.5 K, which in turn raises `3*sigma` by 3 K and
  blocks detections in the ΔT=5-7 K range.

**Practical consequence**: lowering the floor `ANOMALY_THRESHOLD_K` from
5.0 to 3.0 would NOT help, because `3*sigma` is already the binding
constraint. The actionable fixes are (a) reducing sigma via better bg_mask
definition, or (b) reducing N_SIGMA from 3.0 to 2.5.

### L5.5 — Never include eruption-scale TIR in unified vrp_mw without the distance filter
**Almost-shipped bug (2026-04-08, caught in local smoke test before commit)**.

Phase A of the band-specific filter originally included `vrp_tir_mw` (eruption-scale) in the unified `vrp_mw = max(...)` in both `store.py` and `normalize_data.py`. Plan agent's empirical safety check verified 0/231 Lascar VIIRS 375m records had `vrp_tir_mw > 0`, so the change looked like a no-op.

**But it wasn't**: on PCC, a VNP02IMG granule from 2026-02-03 05:54 has:
- `vrp_tir_mw = 95.362 MW`
- `vrp_mir_mw = 15.911 MW` but `hotspot_dist_km = 14.68 km`
- 92 anomalous pixels all 5-15 km from the crater (forest/geothermal, not volcanic)

The existing distance filter in `store.py` correctly zeroes `vrp_eruption` when `hotspot_dist_km > 5 km`, but the filter was MIR-specific. Adding `vrp_tir_mw` to the max() bypassed the filter entirely and would have inflated 15 PCC records from 0.18 → 95 MW, 0.02 → 26 MW, etc.

**Root cause**: `vrp_tir_mw` in `process_viirs.py` is computed as the SUM of I05 Stefan-Boltzmann VRP across ALL pixels in the 30 km ROI that exceed the TIR threshold, with NO distance weighting. The eruption-scale TIR path shares the distance-filter problem with eruption-scale MIR but nobody wired the filter in.

**Fix shipped in commit 0f039bd**: only include `vrp_vent_tir_mw` (the new vent-scale path, which uses a tight vent_radius_km ROI and naturally enforces proximity). The eruption-scale `vrp_tir_mw` is computed but stays out of the unified vrp_mw. A proper fix for eruption-scale TIR (applying the same 5 km filter, or tracking per-pixel distances) is future work.

**Generalization for future changes**: Any time you add a new VRP channel to the unified `max()`, verify it respects the `MAX_HOTSPOT_DIST_KM` filter — either by construction (tight ROI) or by explicit zeroing. The Lascar empirical check is insufficient because Lascar's Atacama environment keeps TIR signals sub-threshold; PCC's Patagonian forest trips false-positive TIR easily.

### L5.4 — Store-level daytime filter contaminates validation matching
In `validate_lascar_vs_mirova.py`, when MIROVA has a daytime VIIRS record
we have no matching record (filtered), so the "best match" falls back to
the closest nighttime pass of the same day. These mismatched pairs are
physically uncorrelated and create the low/high ratio outliers in the tail
(2-5% of pairs). The true calibration quality is therefore slightly BETTER
than the reported mean 1.14 / median 1.02.

Fix for future validations: require match-time tolerance ≤60 min as a hard
cut, not a "closest" fallback.


---

## Session 6 — 2026-04-08

### L6.1 — Fix the bug you can prove, not the bug you suspect
Spent half of session 6 chasing a wrong hypothesis (`roi_p95` filter blocking
MODIS detections on Lascar). Implemented E1 (commit 53d5f62) to exclude the
vent ROI from the p95 calculation. Result: 0 records changed in the reprocess.

The hypothesis was plausible (`roi_p95 + 3K` IS a second filter that COULD
block detections) but I never verified it was the BINDING constraint before
implementing the fix. Verification required adding diagnostic instrumentation
(commit b5c48d5) which showed `t_bg + 3·σ_bg` is the binding constraint in
**100% of records** (54/54 February MODIS) — the p95 was always lower than
the sigma threshold, so removing it had zero effect.

**Generalization**: when fixing a multi-constraint detection logic, FIRST
instrument and identify which constraint binds in the failing cases, THEN
fix only that one. Symptom-based debugging on multi-filter pipelines wastes
cycles on inert changes.

### L6.2 — MODIS process_modis.py has had broken eruption-scale path forever
Across 3 historical snapshots of Lascar (sessions 4 pre-scanfix, 5
post-scanfix, 6 post-revert), the count of MODIS records with
`n_anomalous_pixels > 0` is **0 in all 3 snapshots** (out of 181/182/183
records each). Every MODIS VRP we've ever reported for Lascar comes from
the vent-scale fallback path.

This was hidden by the vent-scale path: it captured 64% of records (117/183)
with 1-pixel detections that gave reasonable VRPs in the low (<2 MW) range,
making the bucket 0.5-2 MW look calibrated (median 1.09 vs MIROVA). But
the bucket 2-10 MW failed (median 0.37) because the vent-scale single
nearest pixel doesn't capture the brightest pixel in the broader ROI.

**Generalization**: when reporting capture rate / median ratio, ALWAYS
break down by sensor AND magnitude bucket. Hiding a structural bug behind
a vent-scale fallback that "mostly works" delayed the discovery by 2 sessions.

### L6.3 — At Lascar, σ_bg in the 5-25 km annulus is 5-16 K naturally
Diagnostic data from 54 February 2026 records showed σ_bg = 5.08 K median
with values up to 16.36 K. Two distinct causes:

1. **Cloud contamination** (~7% of records): high cold clouds in the
   annulus drive `t_bg` below 260 K (one record had t_bg = 224.86 K, -48°C
   — physically impossible for Lascar's surroundings) and σ_bg above 10 K.
   Fix: exclude pixels with `BT < 260 K` from background statistics, same
   strategy `process_viirs.py` already uses (commit pending).

2. **Orographic heterogeneity** (~22% of records): even cloud-free, Lascar's
   5-25 km annulus sweeps across valleys (3000 m), the volcano summit
   (5592 m), and neighboring peaks (Juriques 5704, Aguas Calientes 5924).
   The natural BT range is 10-15 K and σ captures it as "noise".
   Fix: cap the sigma component of the threshold at ~7 K to prevent
   orographic σ from dominating (commit pending). Alternative: use MAD ×
   1.4826 instead of std (more robust to mixture distributions).

**Generalization**: classical anomaly detection assuming homogeneous Gaussian
backgrounds breaks at high-altitude andean volcanoes where the ROI annulus
spans several km of vertical relief. Either tighten the annulus (e.g. 8-15 km
instead of 5-25 km) or use robust statistics.

### L6.4 — Active vent area for MODIS-effective hotspot detection is NOT the geometric crater center
At Lascar, of 12 February records with dT > 8 K, only 2 had the hottest
pixel within 3 km of `vent_lat/vent_lon` defined in volcanoes.yaml. The
other 10 had hotspots 6-10 km from the crater center, all within the
broader 10 km ROI but outside the vent_radius_km=3 km used by the
vent-scale fallback.

Two plausible causes (need ground-truth from SERNAGEOMIN):
- Multiple sub-vents within the crater bowl, each dominating different
  passes (consistent with the false-color Sentinel-2 image showing 2-3
  red sub-features within ~200 m diameter)
- MODIS pixel footprint geometry: a 1×1 km nominal pixel becomes a 1×2 km
  footprint at scan edges, and the geolocation reports the pixel center,
  not the brightness centroid. A vent inside a pixel whose center is
  4-5 km from the crater is reported AT 4-5 km even though the actual
  emitter is at the crater.

**Generalization**: `vent_radius_km` from volcanoes.yaml is a logical
proximity filter, not a physical pixel-resolution boundary. For 1 km MODIS
pixels at off-nadir scan angles, expand by 2-3 km of safety margin.
Possible fix in process_modis.py: use a larger effective vent radius
(5-6 km) for the vent-scale fallback when dealing with MODIS, separate
from VIIRS where 3 km is appropriate (375 m pixels).

### L6.5 — Always preserve a baseline JSON before reprocessing for fix-impact measurement
Used `experiments/lascar_baseline_pre_E1.json` to measure E1 impact (zero
records changed). Without this baseline, would have had to deduce E1 was
inert from indirect evidence ("git diff was 1 line"). Having the literal
JSON snapshot let me run the same diagnostic script against both pre and
post and confirm the change was zero.

**Generalization**: any time you implement a pipeline fix that affects
historical records, save a frozen copy under `experiments/<volcano>_<state>_pre_<fix>.json`
BEFORE running the reprocess. This lets later sessions (or the next agent)
re-verify your claim of impact independently.

---

## Session 7 (2026-04-08)

### L7.1 — MIROVA and Aveni published algorithms have NO Andean validation
After a careful read of Coppola 2015 (MIROVA spec, GSL SP 426) and Aveni
2024 (TIRVolcH), neither paper presents a single validation figure or
case study against a high-altitude Andean volcano. MIROVA's claim of being
"self-adapting to local climate, temperature and topography" (Coppola 2015
p. 9) rests on its NTI/ETI normalization and scene-adaptive μ/σ on dNTI
and dETI — untested against the combination of 5000+ m summits, extreme
thermal inversions over the Altiplano, and persistent subsidence valleys
we see at Lascar, Tupungatito, Ojos del Salado, Llullaillaco.

**Why it matters**: we are calibrating our pipeline RELATIVE to MIROVA,
treating it as ground truth. But MIROVA itself may have bias at Andean
volcanoes that no one has measured. A median ratio of 1.0 does not prove
correctness — it proves agreement with an untested reference.

**Concrete unknowns**:
- Does MIROVA under-detect at 5500+ m summits because their NTI floor
  (C1=0.003 ROI1, 0.01 ROI2) was calibrated on Mediterranean and Hawaiian
  volcanoes at much lower altitudes?
- Does MIROVA over-detect due to persistent hot ground at Atacama daytime,
  which its nighttime-only filter doesn't fully solve for early-evening
  passes?
- Their `distancia_km` field at Lascar has a strong mode at exactly 1.00
  and 1.41 km — suspiciously quantized. Could be pixel-center snapping at
  the MODIS grid, could be their own crater coordinate being 1 pixel
  off. Needs independent verification.
- MIROVA uses 8-neighbor spatial contrast (dNTI) which cancels orographic
  cold peaks by design, but at high-altitude volcanoes the 8 neighbors of
  a summit pixel can straddle a 1000 m altitude gradient with 10 K BT
  spread — this might inflate dNTI spuriously or miss real signals.

**Action for future sessions**: when our pipeline produces numbers close
to MIROVA (say global median ratio within 0.9-1.1), DO NOT declare victory.
Cross-check at least one eruption we can independently verify:
- VRP time series during a well-documented SERNAGEOMIN-reported thermal
  episode (Lascar 2013 gray plume, Copahue 2015 phreatic, Villarrica 2015
  strombolian).
- Calibrated thermal imagery from a ground station if SERNAGEOMIN has one.
- Another independent pipeline (Hawaii SHI/VIIRS, NOAA HMS, Sentinel-2
  active fires L2A) applied to the same frame.

When we have divergence with MIROVA at Andean volcanoes we should
investigate WHY before adjusting our pipeline. It may be us, or it may
be them.

**Filed for re-reading when**: we reach stable MODIS detections at any
Andean volcano and start publishing comparative figures vs MIROVA.

### L7.2 — Match the logic operator, not just the threshold
MIROVA's detection is `Test1 OR (Test2 AND Test3)`, with Test2 being
`dNTI > C1 OR dNTI > μ + C2·σ` — an OR with a FIXED floor and a σ-based
tail. Our process_modis.py was `max(ANOMALY_THRESHOLD_K, N_SIGMA * std_bg)`
which is the MAX of floor and σ-tail, i.e. the MORE restrictive of the two.
Subtle but critical difference: when σ explodes (cloudy or heterogeneous
scenes, σ_bg up to 16 K at Lascar), MIROVA's OR lets the fixed floor
rescue detection; our max forces the σ-inflated value through and kills it.

**Rule**: when porting a detection criterion from a reference paper, don't
just match the thresholds — match the boolean operators. MAX and OR with
floor look identical in the common case but behave oppositely in the
tails, and the tails are where detection/no-detection actually matters.

### L7.3 — The right binding constraint may only appear AFTER you fix the wrong one
E2 capped sigma_component to 7 K. This did lower diag_eff_threshold_k by
~5 K. But bucket 2-10 MW ratio didn't move. Root cause: the p95 local
filter `roi_p95 + 2·roi_std` was always there but masked by the larger
bg-sigma filter. Once we shrunk the bg branch, p95 became the new binding
constraint in 49 of 54 Lascar Feb 2026 records.

This is the inverse of L6.1 (fix the bug you can prove): after fixing the
bug you could prove, re-run diagnostics before claiming success. The
binding constraint can move.

### L7.4 — MODIS lacks NTI dual-criteria — VIIRS has it and calibrates well
`process_viirs.py` (lines 229-288) implements Coppola 2015 NTI dual
criteria: `NTI > NTI_bg + max(0.005, 3·σ_NTI)` on a per-pixel basis using
L_MIR from I04 and L_TIR from I05. VIIRS bucket 2-10 MW median ratio is
1.27 (within 27% of MIROVA).

`process_modis.py` does NOT read Band 31 (11 µm TIR) and has no NTI. It
uses raw BT in Band 21/22 (MIR), which captures topographic warm spots
(valleys, exposed rock at lower altitude) at the same apparent BT as real
sub-pixel hot volcanic fractions. MODIS bucket 2-10 MW ratio 0.37 (3x
undershoot) is a direct consequence.

**Already listed as pending in STATUS.md section 5** ("NTI para MODIS —
Agregar Band 31 11 um TIR"). The reason it wasn't implemented before:
nobody had the diagnostic to prove it was the root cause. Session 6-7
diagnostics (diag_eff_threshold_k fields, p95 binding analysis, MIROVA
distancia_km analysis all pointing to MODIS eruption-scale being broken
due to BT-only detection) now make it the clear E3 target.

### L7.5 — MIROVA/OCR vs MIROVA/consolidado provenance
`data/mirova/*.json` files from early sessions were loaded via an OCR
script that screenshots mirovaweb.it pages and reads the VRP values with
OCR. Verified OCR bias: 3.43 read as 3.0, 2.28 read as 2.0 (truncation of
the decimal part). These are ONLY reliable for detection presence/absence,
NOT for quantitative VRP calibration.

The authoritative source is `registro_vrp_consolidado.csv` (text-scraped
from mirovaweb.it HTML tables, no OCR). It contains clean data for:
Chaiten 1025, PCC 989, NevadosDeChillan 960, Copahue 959, Villarrica 954,
Llaima 950, PlanchonPeteroa 858, Lascar 846, Lastarria 828, Isluga 792,
Tupungatito 491.

Use `scripts/rebuild_mirova_from_consolidado.py <stem> <csv_volcano_name>`
to regenerate any reference. It backs up the OCR file as
`<stem>_OLD_pre_consolidado.json` so we can always compare OCR-era vs
text-era numbers if needed.

**Rule**: before trusting any MIROVA comparison, confirm the reference JSON
has `source: consolidado` in its records. If it doesn't, stop and
regenerate.

### L7.6 — Arbitrary pairing produces deceptive ratios. Always one-to-one by timestamp
Session 7 reported "Lascar Feb 2026 MODIS bucket 2-10 MW: 16/16 detected,
ratio median 0.37". After re-checking with strict one-to-one pairing
(matched by date+hour, ±1 h tolerance), the real numbers are very
different:

- MIROVA Feb 2026 has only **14 records**, max **3.94 MW** (no records >5 MW)
- 11/14 paired, 3 missed (FN)
- Paired ratios: 0.12, 0.18, 0.38, 0.75, 0.89, 1.17, 1.19, 1.34, 1.52, 2.50, 3.19 — **no correlation, both directions**
- **18 detections of ours have NO MIROVA counterpart** (potential FPs), 7 of them >5 MW (one at 11.18 MW)

The 0.37 ratio came from `experiments/09_validate_E3.py` filtering MIROVA
to "VRP_MW between 2 and 10" (which actually only matched 5 records since
MIROVA tops at 3.94) and then matching ours to the closest same-day record.
Closest-of-day is NOT a valid pairing rule when we have multiple records
per day from different sensors and overpasses.

**Rules going forward**:
1. **Never compute ratios on bucketed-and-best-matched pairs**. Compute
   one-to-one pairs by `(date, hour, sensor_family)` with explicit time
   tolerance (≤60 min recommended for MODIS, ≤30 min for VIIRS).
2. **Always report FP and FN counts alongside any ratio**. A median ratio
   of 1.0 is meaningless if half the detections are FPs.
3. **Always inspect the MIROVA value range first**. "Bucket 2-10 MW" is
   meaningless if MIROVA's max in that period is 3.94 MW.

### L7.7 — vent_path threshold `t_bg + 1K` is dangerously permissive on active andean volcanoes
The vent-scale fallback in `process_modis.py` triggers when ANY pixel in
the `vent_radius_km` ROI exceeds `t_bg + 1.0 K`. Empirical impact on
Lascar Feb 2026: **18 detections with no MIROVA counterpart** (62% FP
rate of total detections).

Why 1 K is too low at Lascar:
- Atacama desert nighttime σ_bg even after E2 cloud mask is ~1-2 K
- Crater walls retain residual warmth from daytime insolation up to several
  hours after sunset (passive geothermal + thermal mass), routinely
  producing 2-4 K BT excess inside the 4 km vent ROI without being a
  thermal anomaly in MIROVA's sense
- Off-nadir scan geometry can place a 1 km MODIS pixel at 7 km² ground
  area, multiplying any small ΔL into a "VRP" of several MW even when
  the actual ΔBT is only 3-4 K

The 1 K threshold made sense when this code was first written for a different
scenario (Villarrica passive degassing where the lake glow is a real
1-2 K signal). Carrying it to Lascar without revalidation produced
systematic FPs that were hidden until session 7's strict one-to-one
audit (L7.6).

**Fix not yet shipped — needs E4 plan**. At minimum the threshold should
be `max(3 K, σ_bg)` or similar. But the deeper issue is that vent-scale
detection in MODIS at 1 km resolution conflates "vent thermal residual"
with "active hotspot", and there may be no clean threshold that
discriminates them on a per-pass basis.

### L7.8 — OCR bias is bidirectional, not just truncation
Earlier sessions assumed `MIROVA_OCR` underestimates VRP because OCR
truncates decimals (3.43 → 3.0). After session 7 regenerated several
volcanoes from `consolidado`:
- PCC: OCR-era ratios computed against truncated MIROVA values were
  inflated (looked like overestimation by us)
- Tupungatito: same pattern

In Lascar specifically, the OCR bias direction depends on the digit being
mis-read. It is NOT a clean systematic underestimate. Treating it as
"OCR refs are a lower bound" (as L5.6 did) is incorrect — they're noise.

**Implication**: any pre-session-7 calibration metric computed against
OCR-era refs is **invalid for both ratio AND capture rate**. Specifically
the "session 5 post-fix median ratio 1.02" reported in L5.2 and in
`memory/project_vrp_chile.md` is **not trustworthy**. It needs to be
recomputed against `consolidado` refs across all 11 volcanoes before any
calibration claim is made.

### L7.9 — All session-5 calibration metrics are now obsolete
Combining L7.6 (pairing was wrong) + L7.8 (refs were OCR-noisy) +
L7.7 (vent_path FPs not counted as FPs) means:

- "Capture rate 88.7%" — based on OCR refs, no FP accounting → invalid
- "Mean ratio 1.14, median 1.02" — bucket-and-best-match against OCR
  refs → invalid
- "Improvement factor 1.9x uniform across sensors" — uniformity was an
  artifact of the OCR bias being roughly uniform → invalid
- "Calibration within ~2% of MIROVA" — false claim, do not cite

**These numbers must be removed from `memory/project_vrp_chile.md` and
replaced after the session-8 audit (Phase 1 of `tasks/todo.md`).**
Until then, the project has **no validated calibration baseline**.

### L7.10 — Post-mortem: the NULO contamination of Session 8
**Date discovered:** 2026-04-08. **Severity:** critical, invalidates S8.

`scripts/rebuild_mirova_from_consolidado.py` in its original form filtered
the text-scraped `registro_vrp_consolidado.csv` only by `VRP_MW > 0`,
ignoring the `Clasificacion Mirova` field. The CSV has exactly four
classification values (verified against 9717 rows):

| Clasificación     | Records | Meaning                                       |
|-------------------|---------|-----------------------------------------------|
| `NULO`            |  9324   | MIROVA processed and **rejected** — not a thermal detection |
| `Muy Bajo`        |   263   | Real detection, low activity                  |
| `Bajo`            |   118   | Real detection                                |
| `FALSO POSITIVO`  |    12   | MIROVA-confirmed false positive               |

Only `Muy Bajo` and `Bajo` (381 records total across all volcanoes) are
ground truth. The NULO records are granules MIROVA looked at, decided
were noise (clouds, hot ground, off-volcano pixels, sensor artifacts),
and discarded. **They are the antithesis of ground truth.**

The broken script imported all 9324 NULOs as if they were real detections
into `data/mirova/<volcano>.json` files, which were then fed to the Phase 1
Session 8 audit (`experiments/10_strict_audit.py` and friends). Every
metric produced — TP/FP/FN counts, median ratios, capture rates, "red
flag" lists, per-bucket comparisons — was computed against a reference
set that was 96% noise.

**Concrete impact per volcano** (real records vs NULO contamination):
Lascar 154/692, PCC 67/922, Lastarria 46/781, Isluga 44/748, Tupungatito
33/458, PlanchonPeteroa 18/840, Chaiten 11/1013, Villarrica 5/949,
NevadosDeChillan 2/950, **Llaima 0/950, Copahue 0/957**. Llaima and
Copahue had zero real thermal records in the period and are NOT
calibratable volcanoes at all — any "records" the audit found for them
were 100% noise.

**Why it wasn't caught earlier**:
1. The ref files had `source: consolidado` (L7.5's validation criterion),
   which made them look authoritative. `source: consolidado` tells you
   the provenance of the scrape, NOT that the records are real detections.
2. The field `clasificacion` was INCLUDED in the JSON records but nothing
   downstream looked at it. Defense-in-depth failed because no consumer
   asserted on it.
3. The audit script computed FP rates against contaminated refs, making
   real FPs look like TPs (if our pipeline detected something and a NULO
   existed at that time) and real TPs look like FPs (if no NULO existed).
   The numbers were coherent but meaningless.
4. The expected count per volcano was never sanity-checked. A simple
   "Llaima with 950 thermal detections in 3 months" should have raised
   an eyebrow for a volcano that's been quiet for years.

**Fixes shipped in session 9**:
1. `rebuild_mirova_from_consolidado.py` now filters
   `VALID_CLASSES = {"Muy Bajo", "Bajo"}` with `assert` hard-fail if any
   record leaks past.
2. The set is **closed** — do not speculatively add "Moderado"/"Alto"
   until they actually appear in the CSV.
3. All 11 refs regenerated, verified against expected counts.
4. Session 8 audit artifacts (scripts 05-10, `AUDIT_S8_baseline.md`,
   `audit_snapshots/`, `lascar_pre_E2_snapshot.json`) were **deleted**,
   not quarantined. The lesson is documented here instead — keeping
   contaminated data on disk is a recontamination risk with no upside.

**Rules going forward**:
1. **Every script that consumes a MIROVA ref must assert
   `clasificacion in {"Muy Bajo", "Bajo"}` on every record.** Not a
   silent filter — a hard assert. If the assertion fires, the ref is
   corrupted and the run aborts.
2. **`source: consolidado` is necessary but not sufficient**. Also
   verify `clasificacion` on every record before trusting counts.
3. **When building ground truth from a heterogeneous CSV, the first
   question is "what's in the classification/status/label column"**,
   not "what VRP threshold do I filter on". Semantic label fields
   dominate numeric filter fields.
4. **Sanity-check expected totals against reality**. Llaima having 950
   thermal records would have been a screaming alarm if anyone had
   paused to compare with SERNAGEOMIN's published activity level.
5. **When a calibration metric looks too good (or too bad) to believe,
   audit the reference set before investigating the pipeline**. Every
   session 6-7 "weird finding" we investigated (p95 binding, vent_path
   1K FPs, MODIS eruption-path broken forever) was real — but the
   QUANTITATIVE sizing of those findings against MIROVA was wrong
   because of this contamination.

**Obsolescence sweep**: all numbers in L7.6, L7.7, L7.9 computed against
OCR-era or contaminated refs remain qualitatively correct (the FPs exist,
the vent_path issue exists) but any specific ratios or counts in them
are suspect and must be recomputed against the clean refs in session 9's
AUDIT_S9_baseline.md.
