# VRP Chile — Lessons archive (sesiones 5-6)

> Archivo histórico. Las lecciones vigentes están en `lessons.md` (sesión 7+).
> Muchas métricas de S5 fueron invalidadas en S7-S8 (ver L7.6-L7.10 en `lessons.md`).

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

### L5.2 — Scan-angle fix validated against MIROVA (Lascar, 203 refs) — INVALIDATED
~~Capture rate 81.3% → 88.7%, mean ratio 0.60 → 1.14, median 0.57 → 1.02.~~
**Invalidado en S7-S8**: refs OCR-noisy + bucket-and-best-match pairing + sin
contar FPs del vent_path. Ver L7.6-L7.9 en `lessons.md`. La uniformidad 1.9x
entre sensores fue artefacto del bias OCR uniforme.

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

Future improvement — separate code path in `process_viirs.py`.

### L5.4 — Store-level daytime filter contaminates validation matching
In `validate_lascar_vs_mirova.py`, when MIROVA has a daytime VIIRS record
we have no matching record (filtered), so the "best match" falls back to
the closest nighttime pass of the same day. These mismatched pairs are
physically uncorrelated and create the low/high ratio outliers.

Fix for future validations: require match-time tolerance ≤60 min as a hard
cut, not a "closest" fallback. (Reforzado en L7.6.)

### L5.5 — Never include eruption-scale TIR in unified vrp_mw without distance filter
**Almost-shipped bug (2026-04-08, caught in local smoke test)**.

Phase A of the band-specific filter originally included `vrp_tir_mw`
(eruption-scale) in the unified `vrp_mw = max(...)` in both `store.py` and
`normalize_data.py`. Lascar empirical safety check verified 0/231 VIIRS 375m
records had `vrp_tir_mw > 0`, so the change looked like a no-op.

**But it wasn't**: on PCC, a VNP02IMG granule from 2026-02-03 05:54 has
`vrp_tir_mw = 95.362 MW` from 92 anomalous pixels 5-15 km from the crater
(forest/geothermal, not volcanic). Existing distance filter is MIR-specific.
Adding `vrp_tir_mw` to max() bypassed the filter and would have inflated
15 PCC records from 0.18 → 95 MW, etc.

**Fix shipped in commit 0f039bd**: only include `vrp_vent_tir_mw` (vent-scale,
tight ROI). Eruption-scale TIR computed but stays out of unified vrp_mw.

**Generalization**: Any time you add a new VRP channel to the unified `max()`,
verify it respects `MAX_HOTSPOT_DIST_KM` — by construction (tight ROI) or
explicit zeroing. Single-volcano empirical checks insufficient: Lascar's
Atacama keeps TIR sub-threshold; PCC's Patagonian forest trips false-positive
TIR easily.

### L5.6 — Caveat: the MIROVA reference CSV is incomplete — SUPERSEDED
Originally noted that some VIIRS 375m/750m records were missing from the
scrape. **Superseded** by L7.10 (NULO contamination): the bigger problem
was that 96% of records loaded were `clasificacion=NULO`, not real detections.

### L5.7 — Detection threshold dominated by 3*sigma_bg, not the 5K floor
Eruption-scale threshold is `max(ANOMALY_THRESHOLD_K=5.0, N_SIGMA=3.0 * sigma_bg)`.
On Lascar MODIS, observed ΔT_max ~5-7 K — above 5 K floor but below
`3*sigma_bg ≈ 7.5 K` when sigma ~2.5 K.

Reframes the bg annulus overlap bug: it matters NOT because hot pixels elevate
mean t_bg (only 2.8% of Lascar anomaly pixels in overlap zone) but because
those few pixels inflate sigma_bg from 1.5 K → 2.5 K, raising `3*sigma` by 3 K
and blocking ΔT=5-7 K detections.

**Practical**: lowering ANOMALY_THRESHOLD_K from 5.0 to 3.0 won't help —
3*sigma is the binding constraint. Actionable fixes: (a) reduce sigma via
better bg_mask, or (b) reduce N_SIGMA from 3.0 to 2.5.

---

## Session 6 (2026-04-08)

### L6.1 — Fix the bug you can prove, not the bug you suspect
Spent half of session 6 chasing wrong hypothesis (`roi_p95` filter blocking
MODIS detections on Lascar). Implemented E1 (commit 53d5f62) to exclude vent
ROI from p95 calculation. Result: 0 records changed in reprocess.

Hypothesis was plausible but I never verified it was the BINDING constraint
before fixing. Verification (commit b5c48d5) showed `t_bg + 3·σ_bg` is the
binding constraint in 100% of records (54/54 February MODIS).

**Generalization**: when fixing multi-constraint detection logic, FIRST
instrument and identify which constraint binds in failing cases, THEN fix
only that one. Symptom-based debugging on multi-filter pipelines wastes
cycles on inert changes.

### L6.2 — MODIS process_modis.py has had broken eruption-scale path forever
Across 3 historical Lascar snapshots (S4 pre-scanfix, S5 post-scanfix, S6
post-revert), MODIS records with `n_anomalous_pixels > 0` is **0 in all 3**
(out of 181/182/183 records). Every MODIS VRP for Lascar comes from the
vent-scale fallback path.

Hidden by vent-scale path: 64% of records (117/183) with 1-pixel detections
gave reasonable VRPs in <2 MW range. Bucket 0.5-2 MW looked calibrated
(median 1.09 vs MIROVA). But bucket 2-10 MW failed (median 0.37) because
vent-scale single nearest pixel doesn't capture the brightest pixel in the
broader ROI.

**Generalization**: when reporting capture rate / median ratio, ALWAYS break
down by sensor AND magnitude bucket. Hiding a structural bug behind a
vent-scale fallback that "mostly works" delayed discovery by 2 sessions.

### L6.3 — At Lascar, σ_bg in the 5-25 km annulus is 5-16 K naturally
Diagnostic data: σ_bg = 5.08 K median, up to 16.36 K. Two causes:

1. **Cloud contamination** (~7% of records): high cold clouds in annulus
   drive `t_bg` below 260 K (one record had 224.86 K, -48°C — physically
   impossible) and σ_bg above 10 K. Fix: exclude pixels with `BT < 260 K`
   from bg statistics, same as `process_viirs.py`.

2. **Orographic heterogeneity** (~22% of records): even cloud-free, Lascar's
   5-25 km annulus sweeps valleys (3000 m), summit (5592 m), neighboring
   peaks (Juriques 5704, Aguas Calientes 5924). Natural BT range 10-15 K.
   Fix: cap sigma component at ~7 K. Alternative: MAD × 1.4826 instead of std.

**Generalization**: classical anomaly detection assuming homogeneous Gaussian
backgrounds breaks at high-altitude andean volcanoes where the ROI annulus
spans several km of vertical relief. Tighten the annulus (8-15 km) or use
robust statistics.

### L6.4 — Active vent area for MODIS hotspot detection ≠ geometric crater
At Lascar, of 12 February records with dT > 8 K, only 2 had hottest pixel
within 3 km of `vent_lat/vent_lon`. The other 10 had hotspots 6-10 km from
crater center, all within the broader 10 km ROI but outside `vent_radius_km=3`.

Two plausible causes (need ground-truth from SERNAGEOMIN):
- Multiple sub-vents within crater bowl
- MODIS pixel footprint geometry: 1×1 km nominal becomes 1×2 km at scan
  edges, geolocation reports pixel center not brightness centroid

**Generalization**: `vent_radius_km` is a logical proximity filter, not a
physical pixel-resolution boundary. For 1 km MODIS pixels at off-nadir
angles, expand by 2-3 km safety margin. Possible fix: larger effective vent
radius (5-6 km) for MODIS, separate from VIIRS 3 km (375 m pixels).

### L6.5 — Always preserve a baseline JSON before reprocessing
Used `experiments/lascar_baseline_pre_E1.json` to measure E1 impact (zero
records changed). Without baseline would have had to deduce inertness from
indirect evidence.

**Generalization**: any time you implement a pipeline fix that affects
historical records, save a frozen copy under
`experiments/<volcano>_<state>_pre_<fix>.json` BEFORE reprocessing.
