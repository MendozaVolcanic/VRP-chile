# AUDIT_S9_baseline — honest baseline of the pipeline (2026-04-08)

**Script:** `experiments/11_strict_audit.py`
**Refs:** `data/mirova/*.json` regenerated from `registro_vrp_consolidado al 08042026.csv`
(11,319 rows, 445 real records, range 2026-01-10 → 2026-04-08),
clasificacion ∈ {Muy Bajo, Bajo} only (L7.10 defense: script hard-fails
on any other value).
**Pipeline:** no changes since session 7
**Pairing:** strict 1:1 by (sensor_family, datetime) with tolerance
MODIS ±60 min, VIIRS375 ±30 min, VIIRS ±30 min
**Scope:** Tier A (5 volcanoes) + Tier B (3 volcanoes) = 442 MIROVA refs

This document **replaces** the deleted `AUDIT_S8_baseline.md`. Every number
in it is reproducible by running the script above against the refs in
`data/mirova/`.

**Revision history:**
- 2026-04-08 v1: first clean baseline against 378 refs (old CSV, up to 2026-03-28)
- 2026-04-08 v2: re-run against new CSV with +64 real records and +11
  days of coverage (this version). All 5 red flags confirmed or worsened.

---

## Summary table (v2, against 442-record new CSV)

| Volcano              |  ref |   TP |  FN |   FP |    P  |    R  |   F1  | ratio_med |
|----------------------|-----:|-----:|----:|-----:|------:|------:|------:|----------:|
| **Tier A (calibration)** |      |      |     |      |       |       |       |           |
| Lascar               |  177 |  139 |  38 |  213 |  0.40 |  0.79 |  0.53 |     0.971 |
| PuyehueCordonCaulle  |   74 |   45 |  29 |  432 |  0.09 |  0.61 |  0.16 |     0.132 |
| Lastarria            |   55 |   42 |  13 |  127 |  0.25 |  0.76 |  0.38 |     0.459 |
| Isluga               |   49 |   35 |  14 |  200 |  0.15 |  0.71 |  0.25 |     0.432 |
| Tupungatito          |   44 |   24 |  20 |   80 |  0.23 |  0.55 |  0.32 |     0.602 |
| **Tier B (corroboration)** |      |      |     |      |       |       |       |           |
| PlanchonPeteroa      |   24 |   14 |  10 |   62 |  0.18 |  0.58 |  0.28 |     0.377 |
| Chaiten              |   14 |   13 |   1 |  422 |  0.03 |  0.93 |  0.06 |     0.738 |
| Villarrica           |    5 |    0 |   5 |   56 |  0.00 |  0.00 |  —    |     —     |
| **Total**            |  442 |  312 | 130 | 1592 | **0.16** | **0.71** | **0.26** | —         |

**Headline numbers (against 442 clean refs):**
- **Precision 0.16** — 84% of our detections are false positives.
- **Recall 0.71** — we catch 71% of what MIROVA sees.
- **F1 0.26** — dominated by the precision collapse.
- **Ratio median at Lascar only ≈ 1.0**, elsewhere 0.1–0.74 (systematic under-estimate).

**v1 → v2 deltas** (old 378-ref CSV vs new 442-ref CSV):
- Precision 0.18 → 0.16, Recall 0.73 → 0.71, F1 0.29 → 0.26 (all slightly worse).
- FPs grew faster than TPs in the new 11-day window, confirming the
  structural FP problem gets worse with more data, not better.
- **Tupungatito recall dropped 0.73 → 0.55**: the 11 new Tupungatito records
  in the new CSV are 0 TPs / 11 FNs. Worth flagging separately.
- All 5 red flags below are confirmed or worsened.

---

## Red flags

### RF1 — Precision collapse at EVERY volcano
Every single volcano has precision < 0.4. This is not a per-volcano tuning
issue; it's a **structural pipeline problem** that affects the entire
network uniformly. Distribution of FPs across VRP buckets (Lascar, v2):

| Bucket     | MIROVA refs | Our FPs in same bucket |
|------------|------------:|-----------------------:|
| <0.5 MW    |          40 |                     72 |
| 0.5–1 MW   |          28 |                     33 |
| 1–2 MW     |          49 |                     30 |
| 2–5 MW     |          60 |                     50 |
| 5–10 MW    |           0 |                     25 |
| >10 MW     |           0 |                      3 |

**Critical observation**: MIROVA's maximum VRP at Lascar in this period is
~4 MW, yet our pipeline produces **28 detections ≥5 MW** — all of them FPs.
Same pattern at Tupungatito (17 FPs ≥1 MW on a volcano where MIROVA sees
nothing above 1 MW). This is the quantitative confirmation of **L7.7**
(vent_path `t_bg + 1 K` threshold is dangerously permissive).

### RF2 — MODIS FPs on 4 of 5 Tier A volcanoes
MIROVA has **ZERO MODIS-family records** at PCC, Lastarria, Isluga,
Tupungatito in the new CSV as well (Lascar is the only Tier A volcano
where MIROVA publishes MODIS detections). Our pipeline produces MODIS
detections at all four, **all counted as FPs**:

- PCC: 130 MODIS detections (v1: 115)
- Lastarria: 64 (v1: 55)
- Isluga: 67 (v1: 58)
- Tupungatito: 41 (v1: 37)

Two possible interpretations (must decide in Phase 2 before "fixing"):

1. **Our MODIS is spuriously detecting noise** at those volcanoes. The
   vent_path 1 K threshold fires on warm crater walls, off-nadir pixel
   geometry inflation (L7.7), or orographic BT heterogeneity (L6.3), and
   none of them are real thermal signals.
2. **MIROVA structurally excludes MODIS at those volcanoes** (e.g. because
   of the 1 km resolution not resolving the sub-km thermal footprint at
   small active vents, or because MIROVA has per-volcano NTI floors tuned
   so conservatively that MODIS never triggers for low-activity Andean
   volcanoes). In that case our MODIS detections may be partially real
   discoveries MIROVA is missing — or they may still be FPs. Can't tell
   from MIROVA alone.

Without an **independent ground truth** we cannot distinguish these two
cases. This ties back to L7.1 and open question #5 in the S9 plan.

### RF3 — PuyehueCordonCaulle is uniquely broken
PCC has precision 0.10 and **ratio median 0.137** — we underestimate MIROVA
VRP by 7x where we agree. This is very different from the other Tier A
volcanoes (ratios 0.45–1.0). VIIRS M-band is especially bad: 15 MIROVA refs,
we catch only 2 (recall 13%). Something specific is wrong with PCC
processing that isn't explained by the global vent_path issue.

Possible causes (to investigate in Phase 2):
- Wrong volcano coordinates / radius in `volcanoes.yaml`?
- PCC has multiple crater/fissure vents and our single `vent_lat/vent_lon`
  is pointing at a dead cone?
- Cloud cover over PCC region is high — maybe our cloud mask is too
  aggressive and excludes real detections that MIROVA keeps?
- Backgrounding: PCC sits in a forested/volcanic terrain where the
  eruption-path annulus has very different statistics than Lascar's desert.

### RF4 — Villarrica recall = 0
0 TPs out of 5 MIROVA refs. We have 10 VIIRS375 detections in the same
period but none pair within the ±30 min tolerance window. Two options:
- Timing offset (granule datetime convention mismatch?)
- The MIROVA refs and our detections are on different passes entirely
  (we see the ones MIROVA misses and vice versa)

Easy to diagnose: print the datetime lists side by side for Villarrica.

### RF5 — Systematic under-estimate on low-activity volcanoes
Ratio medians by volcano (v2):
- Lascar: 0.971 (calibrated)
- Chaiten: 0.738
- Tupungatito: 0.602
- Lastarria: 0.459
- Isluga: 0.432
- PlanchonPeteroa: 0.377
- PCC: 0.132 (broken, see RF3)

### RF6 (new in v2) — Tupungatito recall collapse on new data
The 11 extra MIROVA records added to Tupungatito in the new CSV (from
the 2026-03-28 → 2026-04-08 period) are **0 TPs / 11 FNs**. Tupungatito
recall dropped from 0.73 (v1) to 0.55 (v2) as a direct result. Either:
- Something changed operationally at Tupungatito in early April that
  MIROVA catches and we don't (new vent activity outside our ROI?)
- Our pipeline had a gap in that period (missed granules? cron failure?)
- The new records cluster at a specific sensor or time that we filter out
This warrants a quick diagnostic in Phase 2: pull the 11 Tupungatito FNs
from `experiments/audit_s9/Tupungatito.json` and check their dates,
sensors, and whether we had matching granules at all.

Excluding Lascar and PCC, ratios cluster around **0.4–0.6**. This is a
**systematic 2× under-estimate** at low-VRP volcanoes, possibly because:
- Our vent-scale VRP is computed from a single nearest pixel. At low
  signals near the detection floor, the nearest pixel is not the hottest
  pixel and we systematically clip.
- The eruption-scale ROI is producing zero VRP (n_anomalous_pixels=0) at
  these volcanoes and only the vent-scale is contributing.
- Pixel-area assumption (nadir + scan-angle correction) may be slightly
  off in ways that hide at Lascar (variety of magnitudes) but dominate at
  low signals.

---

## Per-family breakdown

Recall is much better for VIIRS375 than for VIIRS (750 m) or MODIS at
low-activity volcanoes:

| Volcano          | MODIS R  | VIIRS375 R | VIIRS R  |
|------------------|---------:|-----------:|---------:|
| Lascar           |    0.81  |      0.81  |    0.73  |
| PCC              |    —     |      0.75  |    0.12  |
| Lastarria        |    —     |      0.76  |    —     |
| Isluga           |    —     |      0.85  |    0.00  |
| Tupungatito      |    —     |      0.61  |    0.00  |
| PlanchonPeteroa  |    —     |      0.58  |    —     |
| Chaiten          |    —     |      0.92  |    1.00  |
| Villarrica       |    —     |      0.00  |    —     |

VIIRS 750 m M-band has terrible recall at low-activity volcanoes (0 at
Isluga, 0 at Tupungatito, 0.13 at PCC). Worth confirming the M-band pipeline
(`process_viirs_mod.py`) is actually producing detections for those — it
might be silently no-op for sub-MW signals.

---

## What we are NOT claiming

- We are not claiming MIROVA is correct. L7.1 still applies: MIROVA has
  no Andean validation published and may have its own bias.
- We are not claiming our FPs are all bad. Some may be real detections
  MIROVA is missing. Without independent ground truth (SERNAGEOMIN ground
  cameras, Sentinel-2 active-fire L2A, or similar) we cannot tell.
- We are not claiming the 0.18 precision is the true precision — it is
  the precision **against MIROVA**, which may itself be biased low.
- We are not reporting any calibration metric for Tier C volcanoes
  (NevadosDeChillan, Llaima, Copahue). They have 2, 0, 0 real records
  respectively; any metric would be dominated by small-sample noise or
  undefined. They remain in NRT but out of calibration.

---

## Phase 2 entry criteria (what to investigate next)

In priority order:

1. **Villarrica timing mismatch** (RF4) — quick diagnostic, could be a
   5-minute fix.
2. **PCC specific breakdown** (RF3) — inspect volcanoes.yaml coordinates,
   compare our detection locations vs MIROVA distancia_km, check cloud
   cover rate.
3. **Lascar vent_path FP spectrum** (RF1) — instrument which pixels are
   triggering the vent_path. Confirm L7.7 quantitatively: is it really
   `t_bg + 1 K` on post-sunset residual warmth?
4. **MODIS-only FPs at low-activity volcanoes** (RF2) — is MIROVA silent
   because MODIS is unreliable, or because MIROVA's own filter is too
   strict? Compare our MODIS FP locations to nearest MIROVA VIIRS375 TP
   in time — if they cluster at the same crater we're probably real.
5. **Systematic 0.4–0.6 ratio bias** (RF5) — check vent_path VRP
   computation details, compare hottest-pixel vs nearest-pixel strategies.

None of these involve pipeline code changes. Phase 2 is pure investigation.

---

## Artifacts produced by this audit

- `experiments/11_strict_audit.py` — the audit script
- `experiments/audit_s9/*.json` — per-volcano reproducible snapshots
  (8 files, one per Tier A + Tier B volcano)
- `experiments/AUDIT_S9_baseline.md` — this document

## Re-run instructions

```bash
# full Tier A + B
python experiments/11_strict_audit.py --tier A
python experiments/11_strict_audit.py --tier B

# single volcano
python experiments/11_strict_audit.py --volcano Lascar
```

Any future divergence from these numbers means either the pipeline
changed (good — validate against this baseline) or the refs were
contaminated again (bad — the hard-fail in the script will catch it
first).
