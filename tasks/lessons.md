# VRP Chile — Lessons learned

> Lecciones de sesiones 5-6 archivadas en `lessons_archive_s5-s6.md`.
> Este archivo contiene **sesión 7 en adelante** (vigentes y operativas).

## Reglas permanentes (resumen rápido)

1. **Pairing one-to-one por timestamp**, nunca bucket-and-best-match. Tolerancia ≤60 min MODIS, ≤30 min VIIRS. Reportar TP/FP/FN siempre. (L7.6)
2. **Cualquier consumidor de refs MIROVA debe assert `clasificacion in {"Muy Bajo","Bajo"}`**. Hard fail, no filtro silencioso. (L7.10)
3. `source: consolidado` es necesario pero NO suficiente — verificar también `clasificacion`. (L7.10)
4. **Nunca declarar victoria con ratio mediano cerca de 1.0** sin cross-check independiente — MIROVA no tiene validación publicada en volcanes andinos. (L7.1)
5. Al portar un criterio de detección de un paper, **igualar también los operadores booleanos** (OR vs MAX), no solo los umbrales. (L7.2)
6. Después de arreglar un constraint, **re-correr diagnósticos** — el binding constraint puede moverse. (L7.3)
7. Cualquier número de S5 ("capture rate 88.7%", "median ratio 1.02", "calibración dentro de 2% de MIROVA") es **inválido**. No citar. (L7.9)
8. **MIROVA GroundOverlay center ≠ MIROVA vent reference**. No usar centroide KMZ como criterio único de posición de vent — cruzar con cluster empírico de TPs o ground truth geológico. (L9.1)

---

## Session 9 (2026-04-08)

### L9.1 — MIROVA KMZ GroundOverlay center is NOT the vent reference

**Context**: In Session 9 Phase 2 we wrote `experiments/extract_mirova_centroids.py`
to parse the `LatLonBox` of every MIROVA `*_Last_GE.kmz` as a cheap
independent cross-check of `volcanoes.yaml` vent coordinates. For each
volcano the script computed the center of the `GroundOverlay` and compared
it against `(lat, lon)` and `(vent_lat, vent_lon)` in YAML.

**Initial (wrong) conclusion**: two volcanoes flagged with >0.5 km offset
from the grid center:
- Tupungatito: 3.00 km offset (YAML -33.400/-69.800 vs MIROVA -33.4269/-69.8004)
- PlanchonPeteroa: 1.87 km offset (YAML -35.240/-70.568 vs MIROVA -35.2232/-70.5695)

I proposed these as "coordinate truncation bugs" to fix in F0 alongside
the well-evidenced RF3 PCC vent fix.

**Ground-truth correction (user, 2026-04-08)**:
- Real Tupungatito active hotspot: **(-33.389044, -69.826374)**
- Real PlanchonPeteroa crater zone: **(-35.241099, -70.573345)**

Verification:

| Volcano | YAML vent | User truth | YAML→truth | MIROVA grid→truth |
|---|---|---|---:|---:|
| Tupungatito | (-33.400, -69.800) | (-33.389, -69.826) | **2.73 km** | 4.83 km |
| PlanchonPeteroa | (-35.240, -70.568) | (-35.241, -70.573) | **0.46 km** | 2.02 km |
| PCC (for comparison) | (-40.585, -72.020) | (-40.523, -72.137) | 12.04 km | 7.64 km |

**In both Tupungatito and PP the YAML vent was already closer to the real
active vent than the MIROVA grid center.** The 2-3 km flagged offsets
measured the distance between our YAML and MIROVA's viewport center, which
for these volcanoes happens to sit away from the active thermal source.

MIROVA's `distancia_km` for Tupungatito FN records (4.37–5.41 km, constant
due to pixel snapping) is consistent with the user ground truth:
distance from MIROVA grid center to real vent = 4.83 km, inside that range.
MIROVA is reporting distance from its own grid center, not from the vent.

**Generalization**:
1. **Grid viewport ≠ reference coordinate**. MIROVA's KMZ `GroundOverlay`
   is a raster viewport centered on an internal MIROVA volcano config
   (typically GVP summit). The active thermal source can be anywhere
   inside the ~50 km² grid, sometimes many km from the viewport center.
2. **KMZ centroids are unreliable as a standalone vent-correctness check.**
   They can (a) falsely flag correct YAML vents (Tupungatito, PP) or
   (b) falsely reassure about wrong vents (a volcano with a crater 1 km
   from grid center but the real vent on a 2011 fissure 7 km away would
   show 0 km flag and still be wrong — cf. PCC RF3).
3. **Valid vent-correctness signals, in increasing order of authority**:
   1. Empirical clustering of our own TP `hotspot_lat/hotspot_lon` (weak
      if few TPs — Tupungatito's 1 TP landed at a spurious location
      6.7 km from the real vent and would have misled us).
   2. MIROVA `distancia_km` constancy across records (tells you MIROVA is
      seeing a single consistent pixel, but not WHERE).
   3. Empirical cluster of 10+ TPs from multiple sensors (RF3 PCC had 24
      TPs within 1.5 km of the 2011 fissure — this IS authoritative).
   4. Independent geological ground truth (SERNAGEOMIN reports, InSAR
      deformation maps, user geologist knowledge). This is the gold
      standard and should be gathered BEFORE proposing coordinate fixes.
4. **Rule**: when flagging a vent as wrong based on geometry alone,
   require at least two independent signals from the list above. For
   Tupungatito/PP I had only signal #1 (and a single weak TP) + a
   misinterpretation of the grid center. That was not enough.

**Consequence for Session 9**:
- F0 reduced to PCC-only reprocess.
- Tupungatito and PP `vent_lat/vent_lon` refined to user ground truth for
  documentation quality, but no reprocess — the 0.46-2.73 km shift is
  within the existing `vent_radius_km` and produces no behavior change.
- The RF6 (Tupungatito recall collapse) root cause is purely the
  NTI-vs-BT-floor operator bug (same as RF4), to be fixed in F1. The vent
  coordinate is not part of the problem.

**Script change**: `experiments/extract_mirova_centroids.py` and
`experiments/mirova_centroids.md` now carry a CAVEAT at the top pointing
at this lesson.

---

## Session 10 (2026-04-12)

### L10.1 — Vent-path produces sensor-dependent false positive rates

**Context**: RF1 (vent_path FP) was the top open issue from Session 9.
Experiment `12_rf1_vent_fp_diagnostic.py` measured vent-only detection rates
on active volcanoes (Tier A+B) vs control volcanoes (Copahue, Llaima,
NevadosDeChillan — zero MIROVA refs).

**Result**: signal-to-noise ratio (active/control vent-only rate) varies by sensor:

| Sensor   | Active rate | Control rate | S/N ratio |
|----------|------------|-------------|-----------|
| VIIRS375 | 20%        | 4.7%        | 4.3×      |
| VIIRS750 | 22%        | 4.4%        | 5.0×      |
| MODIS    | 14%        | 5.6%        | 2.5×      |

MODIS 1 km pixel dilutes sub-pixel thermal anomalies, making the vent-path
(1K threshold) almost indistinguishable from noise. VIIRS (375/750m) has
enough spatial resolution to actually resolve weak crater signals.

**Fix**: `enable_vent_path_modis: false` in mirova_equivalent profile.
MODIS eruption-path remains active. Experimental profile keeps everything.

**Rule**: when a detection path has different physics by sensor (pixel size
fundamentally changes the signal-to-noise), thresholds or enables must be
sensor-specific, not global.

### L10.2 — MIROVA reference gaps are physical, not scraper artifacts

**Context**: the consolidado CSV has ZERO MODIS references for 6 of 8
calibration volcanoes, and zero VIIRS750 references for 4 of 8. This
initially looked like a scraper bug but is actually physical: MIROVA
itself doesn't detect weak volcanoes at coarser resolution.

**Consequence**: any detection our pipeline makes in those sensor×volcano
cells is automatically an FP against the reference — even if the signal
is real. This inflates FP counts and deflates precision unfairly.

**Rule**: when computing per-sensor metrics, flag cells where `ref=0` as
"no reference" rather than "perfect FP rate." OCR data partially fills
these gaps and should always be used for reclassification.

### L10.3 — NTI dual-PATH is essential for cloudy/cold conditions

**Context**: VIIRS 375m (`process_viirs.py`) had NTI dual-PATH since F1
(Session 9). VIIRS 750m (`process_viirs_mod.py`) was missing it — only
had BT-based detection. This meant VIIRS750 missed volcanic signals on
cold/cloudy nights where the absolute BT was depressed but NTI (which
normalizes by TIR) still showed an anomaly.

**Fix**: ported NTI computation (M15 TIR band) and dual-PATH OR logic to
`process_viirs_mod.py`. Now both VIIRS processors have identical detection
philosophy: a pixel is hot if `BT > threshold` OR `NTI > nti_k1_night`.

**Rule**: when adding a detection method to one sensor processor, check
if the same physics applies to all sensor processors. NTI works for any
sensor with co-located MIR+TIR bands.

### L10.4 — Llaima: vent-path noise on dormant volcanic edifice

**Context**: Llaima showed 121 detections (48 MODIS, 44 VIIRS375, 29
VIIRS750) with ZERO MIROVA references. Investigation (`13_llaima_investigation.py`)
revealed:

- 93% are vent-only (n_anomalous_pixels=0)
- VIIRS375 median VRP = 0.033 MW (noise-level)
- Temporally uniform (51% of days) — not episodic
- Repeating VRP values in MODIS (0.328 MW × 7 occurrences)
- 9 eruption-path records all >3.6 km from crater (cloud artifacts)

**Root cause**: Llaima's crater maintains a mild geothermal gradient (~0.5-1K
above regional background). The vent-path 1K threshold is right at the noise
floor for this gradient, triggering on any clear night. This is not volcanic
activity — it's the baseline thermal state of an active-but-quiescent edifice.

MIROVA presumably absorbs this baseline gradient in its own background model,
which is why it publishes nothing.

**Rule**: vent-path detections at <0.1 MW on a dormant volcano with uniform
temporal distribution are not volcanic signals. Need a minimum VRP floor or
temporal clustering filter for future versions.

---

## Session 7 (2026-04-08)

### L7.1 — MIROVA y Aveni publicados NO tienen validación andina
After a careful read of Coppola 2015 (MIROVA spec, GSL SP 426) and Aveni 2024
(TIRVolcH), neither paper presents a single validation figure or case study
against a high-altitude Andean volcano. MIROVA's claim of being
"self-adapting to local climate, temperature and topography" rests on its
NTI/ETI normalization — untested against 5000+ m summits, Altiplano thermal
inversions, and persistent subsidence valleys.

**Why it matters**: we are calibrating RELATIVE to MIROVA, treating it as
ground truth. MIROVA itself may have bias at Andean volcanoes that no one
has measured. A median ratio of 1.0 does not prove correctness — it proves
agreement with an untested reference.

**Concrete unknowns**:
- Does MIROVA under-detect at 5500+ m summits because their NTI floor
  (C1=0.003 ROI1, 0.01 ROI2) was calibrated on Mediterranean/Hawaiian
  volcanoes at much lower altitudes?
- Does MIROVA over-detect due to persistent hot ground at Atacama daytime?
- `distancia_km` at Lascar has a strong mode at exactly 1.00 and 1.41 km —
  suspiciously quantized. Pixel-center snapping or crater coordinate off?
- 8-neighbor spatial contrast (dNTI) cancels orographic cold peaks by
  design, but at high-altitude volcanoes the 8 neighbors of a summit pixel
  can straddle a 1000 m altitude gradient with 10 K BT spread.

**Action**: when our pipeline produces numbers close to MIROVA, DO NOT
declare victory. Cross-check at least one independently verifiable eruption:
- VRP time series during well-documented SERNAGEOMIN thermal episode
  (Lascar 2013 gray plume, Copahue 2015 phreatic, Villarrica 2015 strombolian)
- Calibrated thermal imagery from a ground station if SERNAGEOMIN has one
- Another independent pipeline (Hawaii SHI/VIIRS, NOAA HMS, Sentinel-2 L2A)

### L7.2 — Match the logic operator, not just the threshold
MIROVA's detection is `Test1 OR (Test2 AND Test3)`, with Test2 being
`dNTI > C1 OR dNTI > μ + C2·σ` — an OR with a FIXED floor and a σ-based
tail. Our process_modis.py was `max(ANOMALY_THRESHOLD_K, N_SIGMA * std_bg)`
which is the MAX of floor and σ-tail, i.e. the MORE restrictive of the two.

When σ explodes (cloudy/heterogeneous, σ_bg up to 16 K at Lascar), MIROVA's
OR lets the fixed floor rescue detection; our max forces the σ-inflated
value through and kills it.

**Rule**: when porting a detection criterion, don't just match thresholds —
match boolean operators. MAX and OR-with-floor look identical in the common
case but behave oppositely in the tails, where detection actually matters.

### L7.3 — The right binding constraint may only appear AFTER you fix the wrong one
E2 capped sigma_component to 7 K. Did lower diag_eff_threshold_k by ~5 K.
But bucket 2-10 MW ratio didn't move. Root cause: the p95 local filter
`roi_p95 + 2·roi_std` was always there but masked by the larger bg-sigma
filter. Once we shrunk the bg branch, p95 became the new binding constraint
in 49 of 54 Lascar Feb 2026 records.

Inverse of L6.1: after fixing the bug you could prove, **re-run diagnostics
before claiming success**. The binding constraint can move.

### L7.4 — MODIS lacks NTI dual-criteria — VIIRS has it and calibrates well
`process_viirs.py` (lines 229-288) implements Coppola 2015 NTI dual criteria:
`NTI > NTI_bg + max(0.005, 3·σ_NTI)` per-pixel using L_MIR from I04 and
L_TIR from I05. VIIRS bucket 2-10 MW median ratio 1.27 (within 27% of MIROVA).

`process_modis.py` does NOT read Band 31 (11 µm TIR) and has no NTI. It uses
raw BT in Band 21/22 (MIR), which captures topographic warm spots at the
same apparent BT as real sub-pixel hot volcanic fractions. MODIS bucket
2-10 MW ratio 0.37 (3x undershoot) is a direct consequence.

Already pending in STATUS.md ("NTI para MODIS — Agregar Band 31 11 µm TIR").
Not implemented before because nobody had the diagnostic to prove it was
the root cause. S6-S7 diagnostics now make it the clear E3 target.

### L7.5 — MIROVA/OCR vs MIROVA/consolidado provenance — SUPERSEDED by L7.10
`data/mirova/*.json` from early sessions were OCR-scraped with documented
truncation bias (3.43 → 3.0). Authoritative source:
`registro_vrp_consolidado.csv` (text-scraped HTML, no OCR).

Use `scripts/rebuild_mirova_from_consolidado.py <stem> <csv_volcano_name>`.
Backs up OCR file as `<stem>_OLD_pre_consolidado.json`.

**Rule (revised by L7.10)**: `source: consolidado` is necessary but NOT
sufficient. Must also assert `clasificacion in {"Muy Bajo","Bajo"}`.

### L7.6 — Arbitrary pairing produces deceptive ratios. One-to-one by timestamp
Session 7 reported "Lascar Feb 2026 MODIS bucket 2-10 MW: 16/16 detected,
ratio median 0.37". Re-checked with strict one-to-one pairing (date+hour,
±1 h tolerance):

- MIROVA Feb 2026 has only **14 records**, max **3.94 MW** (no records >5 MW)
- 11/14 paired, 3 missed (FN)
- Paired ratios: 0.12, 0.18, 0.38, 0.75, 0.89, 1.17, 1.19, 1.34, 1.52, 2.50, 3.19 — no correlation, both directions
- **18 detections of ours have NO MIROVA counterpart** (potential FPs), 7 of them >5 MW (one at 11.18 MW)

The 0.37 ratio came from `experiments/09_validate_E3.py` filtering MIROVA to
"VRP_MW between 2 and 10" (only 5 records since MIROVA tops at 3.94) and
matching ours to closest same-day record. Closest-of-day is NOT a valid
pairing rule when there are multiple records per day from different sensors.

**Rules going forward**:
1. **Never compute ratios on bucketed-and-best-matched pairs**. One-to-one
   by `(date, hour, sensor_family)` with explicit time tolerance (≤60 min
   MODIS, ≤30 min VIIRS).
2. **Always report FP and FN counts alongside any ratio**. Median ratio of
   1.0 is meaningless if half the detections are FPs.
3. **Always inspect the MIROVA value range first**. "Bucket 2-10 MW" is
   meaningless if MIROVA's max in the period is 3.94 MW.

### L7.7 — vent_path threshold `t_bg + 1K` is dangerously permissive on active andean volcanoes
Vent-scale fallback in `process_modis.py` triggers when ANY pixel in
`vent_radius_km` ROI exceeds `t_bg + 1.0 K`. Empirical impact on Lascar
Feb 2026: **18 detections with no MIROVA counterpart** (62% FP rate).

Why 1 K too low at Lascar:
- Atacama nighttime σ_bg even after E2 cloud mask is ~1-2 K
- Crater walls retain residual warmth from daytime insolation hours after
  sunset (passive geothermal + thermal mass), routinely producing 2-4 K BT
  excess inside the 4 km vent ROI without being a thermal anomaly
- Off-nadir scan geometry can place a 1 km MODIS pixel at 7 km² ground area,
  multiplying small ΔL into "VRP" of several MW even when ΔBT is only 3-4 K

The 1 K threshold made sense when written for Villarrica passive degassing
(lake glow is real 1-2 K signal). Carrying it to Lascar without revalidation
produced systematic FPs hidden until S7's strict audit.

**Fix not yet shipped — needs E4 plan**. At minimum threshold should be
`max(3 K, σ_bg)`. Deeper issue: vent-scale detection in MODIS at 1 km
resolution conflates "vent thermal residual" with "active hotspot".

### L7.8 — OCR bias is bidirectional, not just truncation
Earlier sessions assumed OCR underestimates VRP because it truncates decimals
(3.43 → 3.0). After regenerating from `consolidado`:
- PCC: OCR-era ratios computed against truncated MIROVA values were inflated
- Tupungatito: same pattern

In Lascar specifically, OCR bias direction depends on the digit being mis-read.
NOT a clean systematic underestimate. Treating OCR refs as "lower bound"
(L5.6) is incorrect — they're noise.

**Implication**: any pre-S7 calibration metric computed against OCR-era refs
is **invalid for both ratio AND capture rate**. The "S5 post-fix median ratio
1.02" reported in L5.2 is **not trustworthy**.

### L7.9 — All session-5 calibration metrics are now obsolete
L7.6 (pairing wrong) + L7.8 (refs OCR-noisy) + L7.7 (vent_path FPs not
counted) means:

- "Capture rate 88.7%" — based on OCR refs, no FP accounting → **invalid**
- "Mean ratio 1.14, median 1.02" — bucket-and-best-match against OCR → **invalid**
- "Improvement factor 1.9x uniform across sensors" — artifact of uniform OCR bias → **invalid**
- "Calibration within ~2% of MIROVA" — **false claim, do not cite**

These numbers were removed from `memory/project_vrp_chile.md`. Until S8/S9
audit completes, **the project has no validated calibration baseline**.

### L7.10 — Post-mortem: the NULO contamination of Session 8
**Date discovered:** 2026-04-08. **Severity:** critical, invalidates S8.

`scripts/rebuild_mirova_from_consolidado.py` originally filtered the
text-scraped `registro_vrp_consolidado.csv` only by `VRP_MW > 0`, ignoring
`Clasificacion Mirova`. CSV has exactly four classification values (verified
against 9717 rows):

| Clasificación     | Records | Meaning                                       |
|-------------------|---------|-----------------------------------------------|
| `NULO`            |  9324   | MIROVA processed and **rejected** — not a thermal detection |
| `Muy Bajo`        |   263   | Real detection, low activity                  |
| `Bajo`            |   118   | Real detection                                |
| `FALSO POSITIVO`  |    12   | MIROVA-confirmed false positive               |

Only `Muy Bajo` and `Bajo` (381 total) are ground truth. NULO records are
granules MIROVA looked at, decided were noise (clouds, hot ground, off-volcano
pixels, sensor artifacts), and discarded. **They are the antithesis of ground
truth.**

The broken script imported all 9324 NULOs as if real detections into
`data/mirova/<volcano>.json`, then fed to S8 audit
(`experiments/10_strict_audit.py`). Every metric — TP/FP/FN, median ratios,
capture rates, "red flag" lists — was computed against a reference set 96% noise.

**Concrete impact per volcano** (real records vs NULO contamination):
Lascar 154/692, PCC 67/922, Lastarria 46/781, Isluga 44/748, Tupungatito
33/458, PlanchonPeteroa 18/840, Chaiten 11/1013, Villarrica 5/949,
NevadosDeChillan 2/950, **Llaima 0/950, Copahue 0/957**. Llaima and Copahue
had zero real thermal records and are NOT calibratable volcanoes at all.

**Why it wasn't caught earlier**:
1. Ref files had `source: consolidado` (L7.5's validation criterion). That
   tells you the provenance of the scrape, NOT that records are real detections.
2. The `clasificacion` field WAS in JSON records but nothing downstream
   looked at it. Defense-in-depth failed.
3. Audit script computed FP rates against contaminated refs — real FPs
   looked like TPs, real TPs looked like FPs. Numbers coherent but meaningless.
4. Expected count per volcano never sanity-checked. Llaima with 950 thermal
   detections in 3 months should have raised an eyebrow.

**Fixes shipped in session 9**:
1. `rebuild_mirova_from_consolidado.py` now filters
   `VALID_CLASSES = {"Muy Bajo", "Bajo"}` with `assert` hard-fail.
2. Set is **closed** — do not speculatively add "Moderado"/"Alto" until
   they actually appear in the CSV.
3. All 11 refs regenerated, verified against expected counts.
4. S8 audit artifacts (scripts 05-10, `AUDIT_S8_baseline.md`,
   `audit_snapshots/`, `lascar_pre_E2_snapshot.json`) were **deleted**, not
   quarantined. Keeping contaminated data on disk is a recontamination risk.

**Rules going forward**:
1. **Every script that consumes a MIROVA ref must assert
   `clasificacion in {"Muy Bajo", "Bajo"}` on every record.** Hard assert,
   not silent filter.
2. **`source: consolidado` is necessary but not sufficient**. Also verify
   `clasificacion` on every record.
3. **When building ground truth from a heterogeneous CSV, the first question
   is "what's in the classification/status/label column"**, not "what
   numeric threshold do I filter on".
4. **Sanity-check expected totals against reality**. Llaima with 950 thermal
   records would have been a screaming alarm.
5. **When a calibration metric looks too good (or too bad), audit the
   reference set BEFORE investigating the pipeline.**

**Obsolescence sweep**: numbers in L7.6, L7.7, L7.9 computed against OCR-era
or contaminated refs remain qualitatively correct (FPs exist, vent_path
issue exists) but specific ratios/counts are suspect and must be recomputed
against clean refs in `AUDIT_S9_baseline.md`.
