# AUDIT_S9_baseline — honest baseline of the pipeline (2026-04-08)

**Script:** `experiments/11_strict_audit.py`
**Refs:** `data/mirova/*.json` regenerated from consolidado CSV, clasificacion
∈ {Muy Bajo, Bajo} only (L7.10 defense: script hard-fails on any other value)
**Pipeline:** no changes since session 7
**Pairing:** strict 1:1 by (sensor_family, datetime) with tolerance
MODIS ±60 min, VIIRS375 ±30 min, VIIRS ±30 min
**Scope:** Tier A (5 volcanoes) + Tier B (3 volcanoes) = 378 MIROVA refs

This document **replaces** the deleted `AUDIT_S8_baseline.md`. Every number
in it is reproducible by running the script above against the refs in
`data/mirova/` as of commit `9cccdce`.

---

## Summary table

| Volcano              |  ref |   TP |  FN |   FP |    P  |    R  |   F1  | ratio_med |
|----------------------|-----:|-----:|----:|-----:|------:|------:|------:|----------:|
| **Tier A (calibration)** |      |      |     |      |       |       |       |           |
| Lascar               |  154 |  123 |  31 |  190 |  0.39 |  0.80 |  0.53 |     0.989 |
| PuyehueCordonCaulle  |   67 |   41 |  26 |  390 |  0.10 |  0.61 |  0.17 |     0.137 |
| Lastarria            |   46 |   36 |  10 |  110 |  0.25 |  0.78 |  0.38 |     0.460 |
| Isluga               |   44 |   32 |  12 |  163 |  0.16 |  0.73 |  0.27 |     0.449 |
| Tupungatito          |   33 |   24 |   9 |   75 |  0.24 |  0.73 |  0.36 |     0.602 |
| **Tier B (corroboration)** |      |      |     |      |       |       |       |           |
| PlanchonPeteroa      |   18 |   10 |   8 |   56 |  0.15 |  0.56 |  0.24 |     0.375 |
| Chaiten              |   11 |   11 |   0 |  259 |  0.04 |  1.00 |  0.08 |     0.738 |
| Villarrica           |    5 |    0 |   5 |   56 |  0.00 |  0.00 |  —    |     —     |
| **Total**            |  378 |  277 | 101 | 1299 | **0.18** | **0.73** | **0.29** | —         |

**Headline numbers (across the whole calibration/corroboration set):**
- **Precision 0.18** — 82% of our detections are false positives.
- **Recall 0.73** — we catch 73% of what MIROVA sees.
- **F1 0.29** — dominated by the precision collapse.
- **Ratio median at Lascar only ≈ 1.0**, elsewhere 0.1–0.7 (systematic under-estimate).

---

## Red flags

### RF1 — Precision collapse at EVERY volcano
Every single volcano has precision < 0.4. This is not a per-volcano tuning
issue; it's a **structural pipeline problem** that affects the entire
network uniformly. Distribution of FPs across VRP buckets (Lascar example):

| Bucket     | MIROVA refs | Our FPs in same bucket |
|------------|------------:|-----------------------:|
| <0.5 MW    |          36 |                     65 |
| 0.5–1 MW   |          25 |                     30 |
| 1–2 MW     |          41 |                     23 |
| 2–5 MW     |          52 |                     47 |
| 5–10 MW    |           0 |                     23 |
| >10 MW     |           0 |                      2 |

**Critical observation**: MIROVA's maximum VRP at Lascar in this period is
~4 MW, yet our pipeline produces **25 detections ≥5 MW** — all of them FPs.
Same pattern at Tupungatito (8 FPs ≥2 MW on a volcano where MIROVA sees
nothing above 1 MW). This is the quantitative confirmation of **L7.7**
(vent_path `t_bg + 1 K` threshold is dangerously permissive).

### RF2 — MODIS FPs on 4 of 5 Tier A volcanoes
MIROVA has **ZERO MODIS-family records** at PCC, Lastarria, Isluga,
Tupungatito (Lascar is the only Tier A volcano where MIROVA publishes MODIS
detections in this period). Our pipeline produces MODIS detections at all
four, **all counted as FPs**:

- PCC: 115 MODIS detections
- Lastarria: 55
- Isluga: 58
- Tupungatito: 37

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
Ratio medians by volcano:
- Lascar: 0.989 (calibrated)
- Tupungatito: 0.602
- Chaiten: 0.738
- Lastarria: 0.460
- Isluga: 0.449
- PlanchonPeteroa: 0.375
- PCC: 0.137 (broken, see RF3)

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
| Lascar           |    0.86  |      0.79  |    0.76  |
| PCC              |    —     |      0.75  |    0.13  |
| Lastarria        |    —     |      0.78  |    —     |
| Isluga           |    —     |      0.86  |    0.00  |
| Tupungatito      |    —     |      0.83  |    0.00  |
| PlanchonPeteroa  |    —     |      0.56  |    —     |
| Chaiten          |    —     |      1.00  |    1.00  |
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
