"""
Experiment 13 — Llaima FP investigation
========================================
MIROVA reports ZERO detections for Llaima in Jan 10 - Apr 10, 2026.
Our pipeline reports 121 detections (all classified FP by audit).
Goal: characterize temporal, spatial, magnitude, and path patterns
to determine if these are systematic noise/artifacts or plausible signals.
"""

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ── Load audit FP records ──────────────────────────────────────────────
audit_path = ROOT / "experiments" / "audit_s10" / "Llaima.json"
with open(audit_path) as f:
    audit = json.load(f)

fp_records = audit["fp_records"]
print(f"Total FP records: {len(fp_records)}")
print(f"Audit totals: {json.dumps(audit['totals'], indent=2)}")
print(f"FP classification: {json.dumps(audit['ocr_reclassification']['fp_classes'], indent=2)}")
print()

# ── Load full data for richer fields ───────────────────────────────────
data_path = ROOT / "data" / "mirova_equivalent" / "Llaima.json"
with open(data_path) as f:
    full_data = json.load(f)

# Build detection records from full data (vrp > 0)
all_detections = []
for r in full_data["records"]:
    vrp = r.get("vrp_mw", 0) or 0
    vrp_vent = r.get("vrp_vent_mw", 0) or 0
    if vrp > 0 or vrp_vent > 0:
        all_detections.append(r)

print(f"Detections from full data (vrp>0 or vrp_vent>0): {len(all_detections)}")
print()

# ── 1. DETECTION PATH BREAKDOWN ───────────────────────────────────────
print("=" * 70)
print("1. DETECTION PATH BREAKDOWN")
print("=" * 70)

vent_only = 0
eruption_path = 0
both = 0

for r in all_detections:
    n_anom = r.get("n_anomalous_pixels", 0) or 0
    n_vent = r.get("n_vent_pixels", 0) or 0
    has_eruption = n_anom > 0
    has_vent = n_vent > 0

    if has_eruption and has_vent:
        both += 1
    elif has_vent:
        vent_only += 1
    elif has_eruption:
        eruption_path += 1

print(f"  Vent-only (n_anom=0, n_vent>=1):    {vent_only}")
print(f"  Eruption-path (n_anom>=1, n_vent=0): {eruption_path}")
print(f"  Both paths:                          {both}")
print()

# ── 2. VRP MAGNITUDE DISTRIBUTION ────────────────────────────────────
print("=" * 70)
print("2. VRP MAGNITUDE DISTRIBUTION (MW)")
print("=" * 70)

vrps_by_family = defaultdict(list)
for r in fp_records:
    fam = r["family"]
    vrps_by_family[fam].append(r["vrp"])

for fam in ["MODIS", "VIIRS375", "VIIRS"]:
    vals = sorted(vrps_by_family.get(fam, []))
    if not vals:
        continue
    n = len(vals)
    median = vals[n // 2]
    print(f"\n  {fam} ({n} detections):")
    print(f"    min={vals[0]:.3f}  p25={vals[n//4]:.3f}  median={median:.3f}"
          f"  p75={vals[3*n//4]:.3f}  max={vals[-1]:.3f}")

    # Bucket counts
    buckets = {"<0.1": 0, "0.1-0.5": 0, "0.5-1": 0, "1-2": 0, "2-5": 0, ">5": 0}
    for v in vals:
        if v < 0.1:
            buckets["<0.1"] += 1
        elif v < 0.5:
            buckets["0.1-0.5"] += 1
        elif v < 1.0:
            buckets["0.5-1"] += 1
        elif v < 2.0:
            buckets["1-2"] += 1
        elif v < 5.0:
            buckets["2-5"] += 1
        else:
            buckets[">5"] += 1
    print(f"    Buckets: {dict(buckets)}")

print()

# ── 3. SPATIAL DISTRIBUTION (hotspot_dist_km) ────────────────────────
print("=" * 70)
print("3. SPATIAL DISTRIBUTION — distance from crater (km)")
print("=" * 70)

dists_with = []
dists_null = 0
for r in fp_records:
    d = r.get("hotspot_dist_km")
    if d is not None:
        dists_with.append((d, r["family"], r["dt"], r["vrp"]))
    else:
        dists_null += 1

print(f"\n  Records with null hotspot_dist_km: {dists_null} / {len(fp_records)}")
print(f"  Records with distance: {len(dists_with)}")
if dists_with:
    print(f"\n  Detections with measurable distance from crater:")
    for d, fam, dt, vrp in sorted(dists_with, key=lambda x: x[0]):
        print(f"    {dt}  {fam:10s}  dist={d:.2f} km  vrp={vrp:.3f} MW")

print()

# ── 4. TEMPORAL DISTRIBUTION ─────────────────────────────────────────
print("=" * 70)
print("4. TEMPORAL DISTRIBUTION")
print("=" * 70)

# Parse dates
dates_by_family = defaultdict(list)
all_dates = []
for r in fp_records:
    dt = datetime.strptime(r["dt"], "%Y-%m-%d %H:%M")
    dates_by_family[r["family"]].append(dt)
    all_dates.append(dt)

all_dates.sort()

# By month
print("\n  By month:")
month_counts = Counter()
for dt in all_dates:
    month_counts[dt.strftime("%Y-%m")] += 1
for m in sorted(month_counts):
    print(f"    {m}: {month_counts[m]} detections")

# By week
print("\n  By ISO week:")
week_counts = Counter()
for dt in all_dates:
    week_counts[dt.strftime("%Y-W%W")] += 1
for w in sorted(week_counts):
    print(f"    {w}: {week_counts[w]}")

# Inter-detection gaps
if len(all_dates) >= 2:
    gaps = [(all_dates[i+1] - all_dates[i]).total_seconds() / 3600
            for i in range(len(all_dates) - 1)]
    gaps_sorted = sorted(gaps)
    n = len(gaps_sorted)
    print(f"\n  Inter-detection gap (hours):")
    print(f"    min={gaps_sorted[0]:.1f}  median={gaps_sorted[n//2]:.1f}"
          f"  p90={gaps_sorted[int(n*0.9)]:.1f}  max={gaps_sorted[-1]:.1f}")

# Daily detection frequency
print("\n  Detection-days vs total days:")
det_days = len(set(dt.date() for dt in all_dates))
total_days = (all_dates[-1] - all_dates[0]).days + 1
print(f"    {det_days} detection-days out of {total_days} total days")
print(f"    Rate: {det_days/total_days:.1%}")

print()

# ── 5. SENSOR BREAKDOWN ─────────────────────────────────────────────
print("=" * 70)
print("5. SENSOR BREAKDOWN (raw_sensor)")
print("=" * 70)

sensor_counts = Counter()
sensor_vrps = defaultdict(list)
for r in fp_records:
    s = r.get("raw_sensor", r["family"])
    sensor_counts[s] += 1
    sensor_vrps[s].append(r["vrp"])

for s in sorted(sensor_counts, key=sensor_counts.get, reverse=True):
    vals = sorted(sensor_vrps[s])
    n = len(vals)
    print(f"  {s:20s}  n={n:3d}  vrp: min={vals[0]:.3f} median={vals[n//2]:.3f} max={vals[-1]:.3f}")

print()

# ── 6. VENT-ONLY SIGNATURE ANALYSIS ─────────────────────────────────
print("=" * 70)
print("6. VENT-ONLY SIGNATURE — n_anomalous_pixels == 0")
print("=" * 70)

# All FP records from audit have n_anomalous and n_vent
vent_only_records = [r for r in fp_records if r.get("n_anomalous_pixels", 0) == 0 and r.get("n_vent_pixels", 0) >= 1]
print(f"\n  Vent-only FPs: {len(vent_only_records)} / {len(fp_records)} ({len(vent_only_records)/len(fp_records):.0%})")
print(f"  All have n_vent_pixels=1: {all(r['n_vent_pixels']==1 for r in vent_only_records)}")
print(f"  All have hotspot_dist_km=null: {all(r['hotspot_dist_km'] is None for r in vent_only_records)}")

# MODIS recurring VRP values (same pixel area => same VRP)
modis_vent = [r for r in vent_only_records if r["family"] == "MODIS"]
modis_vrps = [r["vrp"] for r in modis_vent]
print(f"\n  MODIS vent-only: {len(modis_vent)} records")
print(f"  Unique VRP values: {sorted(set(modis_vrps))}")
vrp_freq = Counter(modis_vrps)
print(f"  VRP frequency: {dict(sorted(vrp_freq.items()))}")

# VIIRS vent-only
viirs375_vent = [r for r in vent_only_records if r["family"] == "VIIRS375"]
viirs_vent = [r for r in vent_only_records if r["family"] == "VIIRS"]
print(f"\n  VIIRS375 vent-only: {len(viirs375_vent)} records")
if viirs375_vent:
    vv = sorted([r["vrp"] for r in viirs375_vent])
    print(f"    VRP range: {vv[0]:.3f} - {vv[-1]:.3f}")
print(f"\n  VIIRS750 vent-only: {len(viirs_vent)} records")
if viirs_vent:
    vv = sorted([r["vrp"] for r in viirs_vent])
    print(f"    VRP range: {vv[0]:.3f} - {vv[-1]:.3f}")

print()

# ── 7. NON-VENT (ERUPTION-PATH) RECORDS ─────────────────────────────
print("=" * 70)
print("7. NON-VENT DETECTIONS (eruption-path or mixed)")
print("=" * 70)

non_vent = [r for r in fp_records if r.get("n_anomalous_pixels", 0) > 0]
print(f"\n  Eruption-path FPs: {len(non_vent)}")
for r in sorted(non_vent, key=lambda x: x["dt"]):
    print(f"    {r['dt']}  {r['family']:10s}  vrp={r['vrp']:.3f} MW"
          f"  n_anom={r['n_anomalous_pixels']}  n_vent={r['n_vent_pixels']}"
          f"  dist={r.get('hotspot_dist_km', 'null')}")

print()

# ── 8. REPEATED VRP VALUES (fingerprint of single-pixel noise) ──────
print("=" * 70)
print("8. REPEATED VRP VALUES (suggests fixed pixel-area artifact)")
print("=" * 70)

all_vrps = [r["vrp"] for r in fp_records]
vrp_counts = Counter(all_vrps)
repeated = {v: c for v, c in vrp_counts.items() if c >= 2}
print(f"\n  VRP values appearing 2+ times:")
for v, c in sorted(repeated.items(), key=lambda x: -x[1]):
    print(f"    VRP={v:.3f} MW  count={c}")

print()

# ── 9. HOUR-OF-DAY DISTRIBUTION ─────────────────────────────────────
print("=" * 70)
print("9. HOUR-OF-DAY (UTC) DISTRIBUTION")
print("=" * 70)

hour_counts = Counter()
for r in fp_records:
    dt = datetime.strptime(r["dt"], "%Y-%m-%d %H:%M")
    hour_counts[dt.hour] += 1

print("\n  Hour (UTC)  Count")
for h in sorted(hour_counts):
    bar = "#" * hour_counts[h]
    print(f"    {h:02d}:xx       {hour_counts[h]:3d}  {bar}")

# Night vs day at Llaima (-38.7 S, ~ UTC-3 in summer, UTC-4 in winter)
# Roughly: UTC 0-10 = local evening/night; UTC 10-22 = local daytime
night_utc = sum(v for k, v in hour_counts.items() if k <= 10)
day_utc = sum(v for k, v in hour_counts.items() if k > 10)
print(f"\n  Night (UTC 00-10, ~local 20-06): {night_utc}")
print(f"  Day (UTC 11-23, ~local 07-19):   {day_utc}")

print()
print("=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"""
Total FP detections: {len(fp_records)}
  - Vent-only path: {len(vent_only_records)} ({len(vent_only_records)/len(fp_records):.0%})
  - Eruption-path:  {len(non_vent)} ({len(non_vent)/len(fp_records):.0%})

Key finding: {len(vent_only_records)} of {len(fp_records)} are VENT-ONLY detections
(n_anomalous_pixels=0, only the single vent pixel triggers).
These have null hotspot_dist_km and VRP from a single pixel's
delta-radiance above background — a weak, repeatable artifact.

MODIS shows {len(modis_vent)} vent-only FPs with only {len(set(modis_vrps))} unique VRP values,
meaning the same pixel produces nearly identical delta-L every pass.
""")
