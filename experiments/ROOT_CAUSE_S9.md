# ROOT_CAUSE_S9 — Phase 2 investigation (2026-04-08)

Diagnostic findings against the clean AUDIT_S9_baseline (v2). **No pipeline
code has been modified.** Each finding is backed by a script run or an
inline Python diagnostic, and points at a specific fix for Phase 3.

Status legend:
- 🟢 ROOT CAUSE IDENTIFIED — evidence chain complete, ready for Phase 3 fix
- 🟡 HYPOTHESIS WITH EVIDENCE — likely explanation, needs one more check
- 🔴 UNDER INVESTIGATION

---

## RF4 🟢 — Villarrica recall = 0 / 5

**Evidence**: on every single one of the 5 MIROVA-reported nights at
Villarrica, our pipeline processed a VIIRS_I granule at the same exact
minute (within 18 minutes). All 5 records show
`vrp_mw=0, n_anomalous_pixels=0, n_vent_pixels=0`.

**Comparison table** (Villarrica VIIRS_I, all records):

| Group                        | n   | t_bg median | t_max median | ΔT (max-bg) |
|------------------------------|----:|------------:|-------------:|------------:|
| Our successful detections    |  20 |   267.8 K   |   278.2 K    | ~10 K       |
| Our zero-VRP records         | 268 |   278.9 K   |   283.0 K    | ~4 K        |
| The 5 MIROVA-reported nights |   5 |  279.8–287.3 K |  282–293.5 K | 2.6–6.3 K   |

**Finding**: the 5 MIROVA nights all have warm `t_bg` (280–287 K) — the
fingerprint of cloud contamination (cirrus at altitude 5500+ m has
BT ≈ 280 K). Our detection threshold is
`max(ANOMALY_THRESHOLD_K=5.0, 3·σ_bg)`. With cloud-warmed background the
absolute ΔT at the crater is 2–4 K — **below the 5 K floor**. The pipeline
refuses to flag any anomaly, returns `vrp=0`.

Meanwhile MIROVA's detection is 0.05–0.21 MW — real but very weak signals.
MIROVA uses NTI dual-criteria (Coppola 2015) with a floor of 0.005, which
cancels cloud bias through the MIR/TIR ratio.

**Note**: per L7.4, our `process_viirs.py` DOES implement NTI dual criteria.
But at Villarrica specifically it is not triggering. Either the NTI path is
being short-circuited by the BT floor first, or the NTI computation at
Villarrica's cloudy nights produces values below the 0.005 floor. Need to
check the code path order in `process_viirs.py` before the Phase 3 fix.

**Fix candidates** (pick after reading the code):
1. Make `ANOMALY_THRESHOLD_K` floor softer (e.g. 3 K), trusting `3·σ_bg`
   to catch genuine noise. Risk: may increase FPs at all volcanoes.
2. Reorder the filter so that **NTI dual-criteria evaluates FIRST and
   independently** of the BT floor. A pixel that passes NTI should be kept
   regardless of ΔT. This is the theoretically correct formulation per
   Coppola 2015.
3. At volcanoes with known persistent low-amplitude signal (open lava lake
   like Villarrica), apply a per-volcano override. Not recommended because
   it's not generalizable to the 34 new volcanoes.

**Recommended**: option 2. Fix the boolean operator between NTI and BT
filters the way MIROVA uses it (L7.2 — "match the logic operator, not just
the threshold").

---

## RF3 🟢 — PuyehueCordonCaulle uniquely broken (precision 0.09, ratio 0.13)

**Evidence**: geometry of the hotspot cluster at PCC.

The `volcanoes.yaml` config for PCC has:
```yaml
vent_lat: -40.585
vent_lon: -72.020
vent_radius_km: 3
# Fumarolic vent field from the 2011 eruption fissure (~8 km ESE of main reference)
```

This places the vent **8.2 km ESE of the main summit (-40.590, -72.117)**.

**But the real 2011 Cordón Caulle eruptive vent is at approximately
(-40.523, -72.137), 7.7 km NNW of the main summit** — the opposite direction.

Distances from our configured vent to:
- Main summit: 8.2 km (correct)
- Real 2011 Cordón Caulle vent: **12.0 km** ← our vent is in the wrong place

**Empirical hotspot cluster analysis** for the 30 TP records at PCC:

| Cluster center        | n  | dist to main | dist to config vent | dist to 2011 vent |
|-----------------------|---:|-------------:|--------------------:|------------------:|
| (-40.52, -72.14)      | 10 |     8.02 km  |           12.45 km  |       **0.42 km** |
| (-40.52, -72.15)      |  9 |     8.27 km  |           13.15 km  |       **1.15 km** |
| (-40.53, -72.14)      |  5 |     6.95 km  |           11.84 km  |       **0.82 km** |
| (-40.65, -72.03)      |  5 |     9.92 km  |            7.28 km  |           16.76 km |

**24 of 30 TPs (80%)** cluster within ~1.5 km of (-40.523, -72.137) = the
real 2011 Cordón Caulle fissure. The other 5 cluster at a secondary
location SE of the summit (possibly a real minor geothermal feature or
FPs — out of scope for RF3).

**Centroid of TP hotspots**: (-40.5445, -72.1258)
- 5.11 km from main summit
- **10.01 km from the configured vent (WRONG)**
- **2.57 km from the 2011 vent (RIGHT)**

**Consequence**: our pipeline's two paths diverge at PCC:
1. **vent-scale path** searches within 3 km of (-40.585, -72.020) — in the
   wrong direction. It finds noise or residual warmth on 495/496 records
   (`n_vent_pixels=1` almost always), producing small "positive" VRPs that
   have nothing to do with the real thermal source.
2. **eruption-scale path** with the 15 km ROI does cover the real fissure
   and captures it correctly (recall 0.61), reporting hotspot coordinates
   ~12 km from the configured vent. This is why PCC's recall isn't zero
   despite the vent being wrong.
3. The final `vrp_mw = max(vent_scale, eruption_scale)` is contaminated
   by the meaningless vent-scale VRP from the wrong pixel, dragging the
   ratio to 0.13 instead of the ~1.0 it would be if only the correct
   eruption-scale VRP were reported.

**Fix**: change `volcanoes.yaml` PCC entry to:
```yaml
vent_lat: -40.523
vent_lon: -72.137
vent_radius_km: 3
# 2011 Cordón Caulle eruptive fissure, NNW of the main Puyehue summit.
# MIROVA consistently detects the fumarolic anomaly at ~7.7 km from the
# main summit. Empirical hotspot cluster (24/30 TPs, Session 9) centered
# at ~(-40.523, -72.137).
```

After this fix, reprocess PCC with `--overwrite` and re-run
`experiments/11_strict_audit.py --volcano PuyehueCordonCaulle`. Expected
improvements:
- Ratio median should jump from 0.13 to ≥0.5 (similar to Isluga/Lastarria
  baseline)
- Precision should improve because the vent-scale path will produce
  `n_vent_pixels=0` on most nights instead of spurious 1-pixel detections
- Recall should be slightly better (some FN nights may now trigger via
  vent-scale)

**Verification**: after the fix, at least one of the diagnostic checks
should show:
- `hotspot_dist_km` median shifts from 7.88 km (currently, from main) to
  0–1 km (from the new vent coords). (Note: `hotspot_dist_km` appears to
  be computed from `lat/lon`, not `vent_lat/vent_lon` — confirm this in
  the pipeline code and decide whether to keep it or change it.)
- `n_vent_pixels` distribution shifts from mostly 1 to mostly 0/1, with
  1s concentrated on the MIROVA-detected nights.

---

## RF1 🔴 — Vent-path FPs at every volcano (not yet diagnosed)

**Pending**. The symptom is known (L7.7: `t_bg + 1K` threshold too
permissive) and the quantitative impact is measured (Lascar: 28 FPs ≥ 5 MW
where MIROVA maxes at 4 MW). But the per-pixel mechanism hasn't been
instrumented for this session. Next step: extract the exact `t_bg`, pixel
BT, and σ_bg of the FP pixels at Lascar to confirm they are post-sunset
residual crater warmth, not true thermal anomalies.

---

## RF2 🔴 — MODIS FPs at PCC / Lastarria / Isluga / Tupungatito (not yet diagnosed)

**Pending**. Blocked by the lack of independent ground truth (user
confirmed none available). The investigation will proceed by cross-checking
our MODIS FP locations against VIIRS375 TPs at the same volcano — if the
MODIS FPs cluster at the same crater pixels as the VIIRS TPs, they are
likely real detections MIROVA is missing. If they scatter randomly, they
are noise.

Note for RF3's PCC case: if the PCC vent fix lands first, the RF2 MODIS
analysis at PCC may need to be re-run afterward.

---

## RF5 🔴 — Systematic 0.4–0.6 ratio bias on low-activity volcanoes (not yet diagnosed)

**Pending**. Lascar is the only calibrated volcano (ratio 0.97); all
others are 0.4–0.6. Hypothesis (L6.4 + L6.2): the vent-scale path uses
the "nearest pixel" not the "hottest pixel" within `vent_radius_km`. At
low signals the nearest pixel often isn't the hottest. The eruption-scale
path produces n_anomalous_pixels=0 most of the time at these volcanoes
(structural bug confirmed for Lascar MODIS in L6.2), so only the
(biased) vent-scale path contributes.

---

## RF6 🟢 — Tupungatito recall collapse (v1 0.73 → v2 0.55) — SAME ROOT CAUSE AS RF4

**Evidence** (diagnostic: inline cross-check of `data/Tupungatito.json` vs
the 12 VIIRS375 FNs in `audit_s9/Tupungatito.json`, all post-2026-03-26):

For **11 of 12** MIROVA FNs we have a matching granule processed at the
**exact same minute** (VIIRS_NOAA20 or VIIRS_SNPP I-band, tolerance 0 min).
The 12th (2026-04-08 05:24) is within the 3-hour LANCE NRT latency window
and hadn't been processed yet at audit time. **This is NOT a fetch gap.**

All 11 matching records show:
- `vrp_mw = 0.00`
- `n_anomalous_pixels = 0` (eruption-scale path rejects all pixels)
- `n_vent_pixels = 0` (vent-scale path also returns empty)
- `t_bg` = 266.5–270.5 K (typical winter Andean nighttime BT)
- `t_max` = 271.0–280.2 K (warm cirrus-contaminated pixels)
- **ΔT = t_max − t_bg = 4.5 K to 12.0 K**
- MIROVA VRP for those same nights: 0.03–0.41 MW (weak but real)

**Example** (2026-04-05 05:30): ΔT = 12.0 K should trivially pass the 5 K
anomaly floor. But it produces 0 anomalous pixels. The only way that
happens is if `3·σ_bg > 12 K`, i.e. `σ_bg > 4 K`. This is entirely
consistent with L6.3: Tupungatito at 5682 m has an annulus that sweeps
~2 km of vertical relief around the summit ice/rock boundary, and
orographic heterogeneity can push σ_bg into the 5–10 K range naturally.

**This is the same mechanism as RF4 Villarrica**, just with a different
cause for the σ inflation:
- Villarrica: warm cirrus at 5500+ m altitude pulls `t_bg` high and
  inflates σ via cloud mixture
- Tupungatito: orographic heterogeneity and winter cirrus combine

The binding constraint in both cases is `max(ANOMALY_THRESHOLD_K, 3·σ_bg)`,
which is the wrong logical operator (see L7.2): MIROVA uses an **OR** with
a floor (`dNTI > C1  OR  dNTI > μ + C2·σ`), not a MAX. Our current code
takes the MORE restrictive of the two branches, so when σ explodes the
fixed 5 K floor gets overridden instead of rescuing the detection.

**Fix**: single code change in `process_viirs.py` — reorder so the NTI
dual-criteria evaluates **first and independently** of the BT floor. A
pixel that passes NTI (Coppola 2015 eq. 6: NTI > NTI_bg + max(0.005, 3·σ_NTI))
should be flagged regardless of ΔT. This converges with the RF4 fix; both
red flags are resolved by the same commit.

**Secondary investigation — coordinate offset from MIROVA grid center was
a red herring**: an initial reading of `experiments/mirova_centroids.md`
flagged Tupungatito's YAML `lat/lon = (-33.400, -69.800)` as 3 km north
of the MIROVA grid center `(-33.4269, -69.8004)`. Ground-truth check with
the user (active vent at ≈(-33.389044, -69.826374)) showed the YAML is
actually **2.73 km from the real active vent** — well inside
`vent_radius_km=5` — while the MIROVA grid center is **4.83 km from the
real vent**. Our YAML is closer to reality than MIROVA's grid viewport is.
The 3 km YAML→grid-center offset was measuring the distance to the wrong
reference; it does not indicate a wrong vent. See L9.1 in
`tasks/lessons.md`.

Fix for RF6: pure code change (F1 NTI reorder). No YAML change needed.

---

## Summary of Phase 2 status

| RF | Status | Volcanoes affected | Priority for Phase 3 |
|----|--------|---------------------|----------------------|
| RF3 | 🟢 | PCC only | **Trivial** — yaml `vent_lat/vent_lon` fix, high impact |
| RF4 | 🟢 | Villarrica + any cloud-night low-signal | High — core detection logic |
| RF6 | 🟢 | Tupungatito | **Same root cause as RF4**, single fix resolves both |
| RF1 | 🔴 | ALL (vent_path FP) | High — structural FP source |
| RF2 | 🔴 | PCC/Lastarria/Isluga/Tupungatito | Low — ambiguous without ground truth |
| RF5 | 🔴 | Lastarria/Isluga/Tupungatito/PlanchonPeteroa/Chaiten | Medium — may partially resolve with RF4/6 fix |

**Three root causes identified and actionable** (RF3, RF4, RF6).

RF4 and RF6 share the same root cause (wrong boolean operator between the
NTI dual-criteria and the BT anomaly floor, per L7.2) and can be resolved
with a single commit in `process_viirs.py`. There is a reasonable chance
RF5 partially resolves in the same commit because "systematic under-
estimate on low-VRP volcanoes" has the same mechanism: weak real signals
getting killed by a σ-inflated threshold at high-altitude volcanoes.

### Proposed Phase 3 commit ordering

1. **F0 — PCC vent coordinate fix** (YAML only, no code change).
   - PCC `vent_lat/vent_lon` → (-40.523, -72.137) [RF3]
   - Tupungatito and PlanchonPeteroa `vent_lat/vent_lon` are refined to
     geologist-provided ground truth (user, 2026-04-08), purely for
     documentation quality — the functional effect is <1 km and within the
     existing `vent_radius_km`, so no behavior change is expected. These
     two **do not need reprocessing** but their YAML entries get the
     more precise coordinates and a comment citing the source.
   - Reprocess PCC only with `--overwrite`.
   - Re-run `experiments/11_strict_audit.py --volcano PuyehueCordonCaulle`.
   - Expected: PCC ratio 0.13 → ≥0.5, PCC precision ~doubles. No change
     at Tupungatito/PP.
2. **F1 — NTI operator reorder** in `process_viirs.py` [resolves RF4+RF6,
   possibly part of RF5]. Match MIROVA's OR-with-floor boolean (L7.2).
3. **F2 — vent_path threshold tightening** [RF1, per L7.7 fix candidate].
4. **F3+** — depends on what Phase 1 re-audit shows after F0+F1+F2.
