# Session 6 — Final findings and E2 plan

**Date**: 2026-04-08
**Status**: Diagnostic complete, fix identified but NOT yet implemented.

---

## TL;DR

The MODIS eruption-scale detection path on Lascar has been structurally broken since the pipeline's inception (0/183 records with `n_anomalous_pixels > 0` across the entire Lascar history). Every MODIS VRP we've reported for Lascar comes from the vent-scale fallback path, which uses a single pixel within a 3 km radius of the crater.

E1 (exclude vent from ROI p95 filter) was implemented and found to be **inert** — it changed zero records. Root cause: the p95 filter was never the binding constraint.

**The real binding constraint is `t_bg + max(5K, 3·σ_bg)`**, where σ_bg in the 5-25 km annulus around Lascar is routinely 4-6 K (clean records) and 10-16 K (cloud-contaminated records). `3·σ` alone adds 12-48 K to the threshold, making any thermal anomaly impossible to detect with the current logic.

The fix is clearly identified but not yet implemented pending review.

---

## How we got here

### Session 5 claimed median ratio 1.02 vs MIROVA for Lascar

After the scan-angle pixel-area fix (sessions 4-5), the global median ratio dropped from 0.57 to 1.02 — reported as "calibration within 2% of MIROVA". This made it look like the pipeline was well calibrated.

### Session 6 discovered the claim was misleading

Breaking down that "1.02 median" by MODIS VRP magnitude bucket revealed:

| Bucket | n | median ratio |
|---|---:|---:|
| weak (<0.5 MW) | 2 | 2.90 |
| low (0.5-2 MW) | 18 | 1.09 |
| **moderate (2-10 MW)** | **16** | **0.37** |
| high (>10 MW) | 0 | — |

The 2-10 MW bucket was subreporting by ~3x. Initial hypothesis chain (F1-F6) blamed the ROI p95 filter. E1 was implemented to fix it (commit 53d5f62), but the E1 reprocess produced 0 changed records.

### Diagnostic instrumentation (commit b5c48d5) revealed the real truth

Added 4 diagnostic fields to `process_modis.py`:
- `diag_sigma_bg_k`: background standard deviation in the 5-25 km annulus
- `diag_roi_p95_k`: the p95 threshold (post E1)
- `diag_eff_threshold_k`: the effective threshold a pixel must clear
- `diag_t_max_dist_km`: distance of the hottest pixel from the crater

Reprocessed Lascar February 2026 with instrumentation (run 24122021260). Results from 54 MODIS records:

| Stat | value |
|---|---|
| σ_bg median | **5.08 K** |
| σ_bg mean | 5.97 K |
| σ_bg max | **16.36 K** |
| σ_bg min | 3.44 K |
| `3·σ_bg` mean | 17.91 K |
| `3·σ_bg` max | 49.08 K |

**Binding constraint check**: for each record we compared the effective threshold against `t_bg + 3σ` and `p95 + 3K`. Result:

- `t_bg + 3σ` is the binding constraint: **54/54** records (100%)
- `p95 + 3K` is the binding constraint: **0/54** records (0%)

The p95 filter never mattered. E1 was surgery in the wrong place.

---

## Why σ_bg is so large

### Cause A — cloud contamination (~7% of records)

4 of 54 February records have `t_bg` below 260 K:

| dt | t_bg | σ_bg |
|---|---:|---:|
| 2026-02-18 01:00 | 253.4 K | 10.2 |
| 2026-02-19 01:40 | 238.0 K | 11.4 |
| 2026-02-20 02:20 | 241.4 K | 16.4 |
| 2026-02-21 01:20 | **224.9 K** (-48°C) | 11.1 |

A `t_bg = 224.9 K` is physically impossible for Lascar's surroundings (Atacama desert floor stays >270 K even in winter nights). That's the background annulus being dominated by high cold clouds. `process_modis.py` has NO cloud mask (unlike `process_viirs.py`).

### Cause B — orographic heterogeneity (~22% of records)

12 of 54 February records have t_bg ≥ 260 K but σ_bg ≥ 6 K. Lascar is at 5592 m, surrounded by:
- Valleys at ~3000 m (warmer even at night due to subsidence)
- Neighboring peaks (Juriques 5704 m, Aguas Calientes 5924 m)
- High-altitude plateau (Altiplano ~4000 m)

The 5-25 km annulus (BG_INNER_KM=5, BG_OUTER_KM=25 in process_modis.py) sweeps across all of these. Even in cloud-free conditions, the BT range in the annulus is naturally 10-15 K. `std` captures this as "noise" and inflates the detection threshold.

### Cause C — clean well-behaved records (~70% of records)

38 of 54 February records have σ_bg < 6 K. The vast majority of Lascar MODIS passes are in this regime. For these, `3σ = 12-18 K` which is still too high to detect typical 5-10 K anomalies from the vent.

---

## Where the hot pixels actually are

Of the 12 records with `dT > 8 K` in February 2026, the distance of the hottest pixel from the crater was:

| dt | dT (K) | hotspot dist (km) | current VRP |
|---|---:|---:|---:|
| 2026-02-14 07:15 Aqua | 11.45 | 2.34 | vent=3.52 |
| 2026-02-20 07:50 Aqua | 8.33 | 3.58 | vent=1.70 |
| 2026-02-18 01:00 Terra | 13.47 | 4.52 | vent=12.89 |
| 2026-02-17 02:00 Terra | 10.00 | 7.23 | vent=2.04 |
| 2026-02-19 07:10 Aqua | 8.58 | 7.18 | vent=0.89 |
| 2026-02-08 06:45 Aqua | 11.04 | 8.14 | vent=0.00 |
| 2026-02-02 02:00 Terra | 8.74 | 8.89 | vent=0.84 |
| 2026-02-08 01:00 Terra | 8.55 | 9.25 | vent=9.19 |
| 2026-02-21 01:20 Terra | 22.93 | 9.34 | vent=0.66 |
| 2026-02-27 07:20 Aqua | 8.02 | 9.48 | vent=0.99 |
| 2026-02-20 02:20 Terra | 17.73 | 9.57 | vent=1.99 |
| 2026-02-19 01:40 Terra | 18.43 | 6.26 | vent=0.49 |

Only 2 of 12 have the hotspot within 3 km of the crater (the `vent_radius_km` used by the vent-scale path). The majority are 6-10 km away — well outside the vent ROI but inside the 10 km detection ROI.

**Interpretation**: the "active vent region" of Lascar as seen by a 1 km² MODIS pixel is effectively not centered on `vent_lat/vent_lon`. Either:
- The pixel grid doesn't align with the crater center (geometric offset, different pass-to-pass)
- Multiple sub-vents inside the crater bowl, each of which may dominate a different pass
- The hot pixel is actually adjacent to the vent but its center happens to sit ~5-9 km away due to pixel footprint geometry (MODIS can be 10 km elongated at edge of swath)

Either way: the vent-scale fallback's 3 km radius is too tight. And the eruption-scale path would catch these pixels if only the threshold weren't absurdly high.

---

## The fix (E2, not yet implemented)

Two small changes that together should resolve the bucket 2-10 MW gap.

### E2a — Cloud mask in background annulus

Current code (`process_modis.py:177`):
```python
bg_vals = bt_mir[bg_mask & ~np.isnan(bt_mir)]
```

Proposed:
```python
# Cloud mask: exclude pixels colder than 260 K from background statistics.
# High cold clouds routinely contaminate the 5-25 km annulus at Lascar and
# inflate both t_bg (lower than real ground) and σ_bg (mixing hot ground
# and cold cloud tops). This is the same strategy used by process_viirs.py.
CLOUD_MASK_BT = 260.0
bg_vals = bt_mir[bg_mask & ~np.isnan(bt_mir) & (bt_mir > CLOUD_MASK_BT)]
if len(bg_vals) < 10:
    return None
```

Expected impact on February 2026:
- Eliminates the 4 patologically cold records (t_bg < 260)
- May drop σ_bg in a few more records where the annulus has scattered cloud fragments

### E2b — Cap on the sigma component of the threshold

Current code (`process_modis.py:183`):
```python
threshold = max(ANOMALY_THRESHOLD_K, N_SIGMA * std_bg)
```

Proposed:
```python
# Cap the σ component to prevent orographic heterogeneity from blowing up
# the threshold. At high-altitude volcanoes (Lascar 5592 m, Llullaillaco
# 6739 m, etc.) the 5-25 km annulus includes valleys, ridges and plateau
# terrain with natural ΔT ~10-15 K. Applying an uncapped 3σ turns a legit
# 7 K vent anomaly into a rejection.
# 7 K cap chosen empirically: allows detection at clean records (σ<6K and
# 3σ<18K where the real anomalies sit) while still rejecting FPs from
# residual cloud streaks (σ>10K).
MAX_SIGMA_COMPONENT_K = 7.0
sigma_component = min(N_SIGMA * std_bg, MAX_SIGMA_COMPONENT_K)
threshold = max(ANOMALY_THRESHOLD_K, sigma_component)
```

Expected impact on February 2026 (simulated from diag data):
- 26 of 38 "clean" records (σ<6) gain eruption-scale detection with estimated VRP 1.0-2.8 MW
- 12 "clean" records with real dT < 5 K correctly stay zero (below the 5 K floor)
- The 4 cloudy records are already fixed by E2a

### What E2 does NOT change

- No change to `process_viirs.py` or `process_viirs_mod.py`. Those have different detection logic and are already working correctly (VIIRS 375m bucket 2-10 MW median ratio 1.27, VIIRS 750m median ratio 1.11).
- No change to the vent-scale fallback path. It still captures weak signals where the eruption-scale doesn't find anything.
- No change to `P95_VENT_EXCLUSION_KM` from E1. E1 is inert but harmless — I'm leaving it in the code for now because removing it requires a revert commit and the logic is still defensible (the p95 filter itself isn't wrong, it just isn't the binding constraint for Lascar). If next session's testing shows E1 causes side effects, we revert it.

### Risk assessment

The detection logic change increases sensitivity. The risk is false positives on:
1. **Other high-altitude volcanoes**: Llullaillaco, Ojos del Salado, etc. also have 5592+ m summits. Cap of 7 K may be too permissive if their σ_bg is similar to Lascar and they have no real volcanic signal. Mitigation: validate E2 on a known-quiet Chilean volcano (e.g. Chaiten or Michinmahuida, no recent activity) and confirm no new false positives.
2. **Non-volcanic hot pixels within the ROI**: exposed rock, geothermal areas, forest fires. The existing `hotspot_dist_km < MAX_HOTSPOT_DIST_KM = 5` filter in `store.py` and the vent_radius fallback protect against some of these. Mitigation: audit the anomaly_pixels list for any new detections outside of a 10 km radius from the crater center.
3. **VIIRS 750m sensor**: same logic is in `process_viirs_mod.py`. Consider applying E2 there too, OR leaving it alone because VIIRS 750m already works (ratio 1.11). Recommendation: leave VIIRS 750m alone in first pass, apply E2 only to MODIS, measure, then decide.

### Testing plan for session 7

1. Implement E2a + E2b' on `process_modis.py` (two small diffs, keep diag fields)
2. Commit and reprocess Lascar February 2026 with `--overwrite`
3. Verify:
   - Number of MODIS records with `n_anomalous_pixels > 0`: 0 → expected ~25-30 (out of 54)
   - Bucket 2-10 MW median ratio: 0.37 → expected 0.7-0.9
   - Global median ratio: 0.978 → expected ~1.0
   - No records with absurd VRP > 30 MW (sanity check)
   - `diag_eff_threshold_k` should drop from ~290 K to ~280 K on average
4. If good: reprocess all 11 volcanoes for 2026-03-07 → 2026-04-07 with E2 (and scan-fix already applied).
5. Compare Chaiten / Michinmahuida (quiet volcanoes) pre-E2 vs post-E2 to confirm no new false positives.
6. Roll out E2 to `process_viirs_mod.py` if MODIS results are clean.
7. Update `tasks/lessons.md` L6.x with the full root-cause analysis.

### Fallback plan if E2 overshoots

If E2 produces VRPs that overshoot MIROVA by more than 2x consistently:
- Raise `MAX_SIGMA_COMPONENT_K` from 7.0 to 8.0 (less aggressive)
- Or keep sigma uncapped but tighten the annulus: change `BG_INNER_KM, BG_OUTER_KM` from `(5, 25)` to `(8, 15)` which excludes the farthest heterogeneous terrain
- Or use median absolute deviation (MAD × 1.4826) instead of std, which is robust to outliers

If E2 produces NEW false positives on quiet volcanoes (Chaiten gets VRP > 1 MW out of nowhere):
- The 7 K cap is wrong; revert E2b' and keep only E2a
- Investigate whether the FPs are topographic (crater rim rocks) or cloud-related (residual scattered clouds)

---

## Commits in session 6

| Commit | Description |
|---|---|
| `0f039bd` | Phase A: vent TIR detection (REVERTED) |
| `0e5e2eb` | Revert Phase A |
| `fd42536` | Diagnostic framework + F1-F5 findings |
| `0e76938` | MIROVA Lascar regen from consolidated CSV (drop OCR) |
| `d513cae` | Lascar base reprocessed post-revert (baseline for E1 comparison) |
| `53d5f62` | E1: exclude vent from p95 (inert — no effect) |
| `f5f5e12` | Lascar post-E1 reprocess (0 records changed) |
| `b5c48d5` | Diagnostic instrumentation (4 fields) |
| `573b7d5` | Lascar Feb 2026 with diag fields |

## Artifacts in session 6

- `experiments/01_diagnostic_lascar.py` — ratio diagnostic script
- `experiments/01_diagnostic_report.md` — running findings report (F1-F6)
- `experiments/02_verify_bg_overlap_bug.py` — bg_mask overlap investigation (dead end)
- `experiments/03_predict_modis_wooster.py` — Wooster physical prediction
- `experiments/04_session6_final_findings.md` — this document
- `experiments/lascar_baseline_pre_E1.json` — frozen baseline for comparison
- `experiments/lascar_session5_snapshot.json` — session 5 closing state
- `data/mirova/Lascar.json` — regenerated from consolidated CSV (175 records)
- `data/mirova/Lascar_OLD_with_OCR.json` — original (contaminated with OCR)
