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
