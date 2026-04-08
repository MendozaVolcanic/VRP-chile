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

### L5.4 — Store-level daytime filter contaminates validation matching
In `validate_lascar_vs_mirova.py`, when MIROVA has a daytime VIIRS record
we have no matching record (filtered), so the "best match" falls back to
the closest nighttime pass of the same day. These mismatched pairs are
physically uncorrelated and create the low/high ratio outliers in the tail
(2-5% of pairs). The true calibration quality is therefore slightly BETTER
than the reported mean 1.14 / median 1.02.

Fix for future validations: require match-time tolerance ≤60 min as a hard
cut, not a "closest" fallback.
