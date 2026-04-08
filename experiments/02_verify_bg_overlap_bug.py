"""
experiments/02_verify_bg_overlap_bug.py

Investigate Finding F3 (ROI / background annulus overlap) with concrete
numerical evidence BEFORE touching any code.

Questions:
  V1. How many Lascar records have anomaly pixels inside the overlap zone
      [BG_INNER_KM=5, radius_km=10]? These pixels would be contaminating bg.
  V2. For records with hotspot_dist_km in [5, 10], how much does t_bg change
      if we simulate "exclude hotspot pixels from bg"?
  V3. For a specific close_pass_zero_vrp example, can we predict whether a
      fix would have detected it? (approximate — we don't have raw BT data
      locally, but we can look at anomaly_pixels positions and back-compute)

No code changes. Prints to stdout. Read-only.
"""
import json
from pathlib import Path

REPO = Path(__file__).parent.parent
SNAPSHOT = REPO / "experiments" / "lascar_session5_snapshot.json"
VOLCANOES = REPO / "volcanoes.yaml"

LASCAR_RADIUS_KM = 10  # from volcanoes.yaml
BG_INNER = 5.0
BG_OUTER = 25.0


def load(path):
    with open(path) as f:
        d = json.load(f)
    return d.get("records", d) if isinstance(d, dict) else d


def main():
    records = load(SNAPSHOT)
    print(f"=== V1: Anomaly pixels in overlap zone [{BG_INNER}, {LASCAR_RADIUS_KM}] km ===")
    print()

    # Count anomaly pixels by distance bucket
    n_records_with_anom = 0
    n_anomaly_pixels_total = 0
    in_overlap = 0
    in_core = 0  # < BG_INNER (inside vent core, clearly inside ROI, NOT in bg)
    outside_overlap = 0  # > LASCAR_RADIUS_KM (shouldn't exist since ROI caps there)
    overlap_records = []  # records with at least one anomaly pixel in overlap

    for r in records:
        ap = r.get("anomaly_pixels") or []
        if not ap:
            continue
        n_records_with_anom += 1
        has_overlap = False
        for px in ap:
            d = px.get("dist_km", 0) or 0
            n_anomaly_pixels_total += 1
            if d < BG_INNER:
                in_core += 1
            elif d <= LASCAR_RADIUS_KM:
                in_overlap += 1
                has_overlap = True
            else:
                outside_overlap += 1
        if has_overlap:
            overlap_records.append(r)

    print(f"Records with >=1 anomaly pixel: {n_records_with_anom}")
    print(f"Total anomaly pixels: {n_anomaly_pixels_total}")
    print(f"  - core [0, {BG_INNER} km]: {in_core} pixels ({100*in_core/max(n_anomaly_pixels_total,1):.1f}%)")
    print(f"  - overlap [{BG_INNER}, {LASCAR_RADIUS_KM} km]: {in_overlap} pixels ({100*in_overlap/max(n_anomaly_pixels_total,1):.1f}%)")
    print(f"  - outside ROI [>{LASCAR_RADIUS_KM} km]: {outside_overlap} (expected 0)")
    print()
    print(f"Records with at least one anomaly pixel in overlap zone: {len(overlap_records)}")
    print(f"  (= {100*len(overlap_records)/max(n_records_with_anom,1):.1f}% of records with anomalies)")
    print()

    print("=== V2: hotspot_dist_km distribution (primary hotspot) ===")
    print()
    dist_buckets = {"0-1": 0, "1-2": 0, "2-3": 0, "3-4": 0, "4-5": 0, "5-6": 0, "6-7": 0, "7-8": 0, "8-9": 0, "9-10": 0, ">10": 0}
    for r in records:
        d = r.get("hotspot_dist_km")
        if d is None:
            continue
        if d < 1: dist_buckets["0-1"] += 1
        elif d < 2: dist_buckets["1-2"] += 1
        elif d < 3: dist_buckets["2-3"] += 1
        elif d < 4: dist_buckets["3-4"] += 1
        elif d < 5: dist_buckets["4-5"] += 1
        elif d < 6: dist_buckets["5-6"] += 1
        elif d < 7: dist_buckets["6-7"] += 1
        elif d < 8: dist_buckets["7-8"] += 1
        elif d < 9: dist_buckets["8-9"] += 1
        elif d < 10: dist_buckets["9-10"] += 1
        else: dist_buckets[">10"] += 1

    for b, c in dist_buckets.items():
        bar = "#" * c
        marker = "  <-- in overlap" if b in ("5-6","6-7","7-8","8-9","9-10") else ""
        print(f"  {b:5s} km: {c:4d} {bar}{marker}")

    overlap_count = sum(v for k, v in dist_buckets.items() if k in ("5-6","6-7","7-8","8-9","9-10"))
    total_with_hs = sum(dist_buckets.values())
    print()
    print(f"Records with hotspot in overlap zone: {overlap_count}/{total_with_hs} "
          f"({100*overlap_count/max(total_with_hs,1):.1f}%)")
    print()

    print("=== V3: Sample close_pass_zero_vrp records (would the fix help?) ===")
    print()
    # The 21 zero_vrp records all had the same-time granule with vrp=0, t_max-t_bg ~5-7K
    # Let's look at what records have BT t_max slightly above t_bg but not counted
    # by looking at borderline cases
    zero_records = [r for r in records if (r.get("vrp_mw", 0) or 0) == 0 and (r.get("vrp_vent_mw", 0) or 0) == 0]
    print(f"Total VRP=0 records: {len(zero_records)}")
    # How many have t_max - t_bg > 3K (borderline)?
    borderline = []
    for r in zero_records:
        tbg = r.get("t_bg_k")
        tmax = r.get("t_max_k") or r.get("t_max_i04_k")
        if tbg is None or tmax is None:
            continue
        delta = tmax - tbg
        if 3 <= delta <= 8:
            borderline.append((delta, r))

    borderline.sort(key=lambda x: -x[0])
    print(f"VRP=0 records with t_max-t_bg in [3, 8] K (borderline detection): {len(borderline)}")
    print()
    print("Top 15 borderline cases (highest dT):")
    print(f"{'date':<18} {'sensor':<22} {'t_bg':>8} {'t_max':>8} {'dT':>6} {'n_cloud':>8}")
    for delta, r in borderline[:15]:
        print(f"{r.get('datetime_utc',''):<18} {r.get('sensor',''):<22} "
              f"{r.get('t_bg_k',0):>8.2f} {(r.get('t_max_k') or r.get('t_max_i04_k') or 0):>8.2f} "
              f"{delta:>6.2f} {r.get('n_cloud_masked', 0) or 0:>8}")
    print()

    print("=== V4: Does radius_km > BG_INNER_KM affect many volcanoes? ===")
    print()
    # Check volcanoes.yaml
    try:
        import yaml
        with open(VOLCANOES) as f:
            cfg = yaml.safe_load(f)
        vs = [v for v in cfg["volcanoes"] if v.get("active", True)]
        overlap_count = 0
        no_overlap_count = 0
        for v in vs:
            rk = v.get("radius_km", 0)
            if rk > BG_INNER:
                overlap_count += 1
            else:
                no_overlap_count += 1
        print(f"Active volcanoes with radius_km > {BG_INNER} (bug affects them): {overlap_count}")
        print(f"Active volcanoes with radius_km <= {BG_INNER} (bug does NOT affect): {no_overlap_count}")
        # List the most-overlapped
        vs_sorted = sorted(vs, key=lambda v: -v.get("radius_km", 0))
        print()
        print("Volcanoes with largest overlap zones:")
        for v in vs_sorted[:10]:
            rk = v.get("radius_km", 0)
            overlap_width = max(0, min(rk, BG_OUTER) - BG_INNER)
            print(f"  {v['name']:<25s} radius_km={rk:>4}  overlap_width={overlap_width:>4} km")
    except ImportError:
        print("(yaml not available, skipping)")


if __name__ == "__main__":
    main()
