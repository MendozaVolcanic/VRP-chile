"""
experiments/01_diagnostic_lascar.py

Phase 1 diagnostic: understand exactly where the pipeline falls short of MIROVA
on Lascar, BEFORE trying any fixes. Output is a written report consumed by
humans to decide which experiment to run next.

Three questions:
  Q1. The 23 MIROVA refs we DON'T capture — why? (no granule / filtered /
      below threshold / wrong distance / other)
  Q2. The pairs with worst ratio — is there a systematic pattern (sensor,
      magnitude bucket, time of day)?
  Q3. The MODIS sensor-specific gap (pre-Phase A median 0.79 — underestimates
      ~21%). Is it at swath edge? Particular dates? Low vs high VRP?

Input: a Lascar JSON file (pass as --source=<path>, default = session 5
snapshot at experiments/lascar_session5_snapshot.json).
Reference: data/mirova/Lascar.json (203 refs).

Produces a plain-text report at experiments/01_diagnostic_report.md.
"""
import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean, median, stdev

REPO = Path(__file__).parent.parent
MIROVA_PATH = REPO / "data" / "mirova" / "Lascar.json"
DEFAULT_SOURCE = REPO / "experiments" / "lascar_session5_snapshot.json"
OUTPUT = REPO / "experiments" / "01_diagnostic_report.md"


def load(path):
    with open(path) as f:
        d = json.load(f)
    return d.get("records", d) if isinstance(d, dict) else d


def sensor_family_mirova(s):
    if s == "MODIS":
        return "MODIS"
    if s == "VIIRS375":
        return "VIIRS_375"
    if s == "VIIRS":
        return "VIIRS_750"
    return None


def sensor_family_ours(s):
    if s in ("MODIS_TERRA", "MODIS_AQUA"):
        return "MODIS"
    if s in ("VIIRS_SNPP", "VIIRS_NOAA20"):
        return "VIIRS_375"
    if s in ("VIIRS_SNPP_750", "VIIRS_NOAA20_750"):
        return "VIIRS_750"
    return None


def parse_dt(s):
    try:
        return datetime.strptime(str(s)[:16], "%Y-%m-%d %H:%M")
    except Exception:
        return None


def vrp(r):
    return max(r.get("vrp_mw", 0) or 0, r.get("vrp_vent_mw", 0) or 0)


def same_day_family_records(miro_rec, ours):
    """All our records on the same UTC day and matching sensor family."""
    fam = sensor_family_mirova(miro_rec.get("sensor", ""))
    miro_dt = parse_dt(miro_rec.get("datetime_utc"))
    if fam is None or miro_dt is None:
        return []
    day = miro_dt.date()
    out = []
    for r in ours:
        if sensor_family_ours(r.get("sensor", "")) != fam:
            continue
        rdt = parse_dt(r.get("datetime_utc"))
        if rdt is None or rdt.date() != day:
            continue
        delta_min = abs((rdt - miro_dt).total_seconds()) / 60.0
        out.append((delta_min, r))
    out.sort(key=lambda x: x[0])
    return out


def classify_miss(miro_rec, ours):
    """Diagnose WHY we missed a MIROVA reference.

    Returns (category, details_dict):
      - 'no_record_in_day'  : no our-record with matching sensor family on that day
      - 'no_close_pass'     : records exist but closest is >60 min away (likely different pass)
      - 'close_pass_zero_vrp': close-time record exists but vrp=0 (threshold / filter / cloud)
      - 'close_pass_low_vrp' : close record has small vrp<0.5*miro (underestimate)
      - 'matched_ok'         : close record within reasonable factor (not a miss)
    """
    same_day = same_day_family_records(miro_rec, ours)
    mv = miro_rec.get("VRP_MW", 0) or 0
    if not same_day:
        return "no_record_in_day", {"n_same_day": 0}
    closest = same_day[0]
    delta_min = closest[0]
    ov = vrp(closest[1])
    if delta_min > 60:
        return "no_close_pass", {
            "closest_delta_min": delta_min,
            "closest_sensor": closest[1].get("sensor"),
            "closest_vrp": ov,
            "n_same_day": len(same_day),
        }
    if ov == 0:
        return "close_pass_zero_vrp", {
            "closest_delta_min": delta_min,
            "closest_sensor": closest[1].get("sensor"),
            "t_bg_k": closest[1].get("t_bg_k"),
            "t_max_k": closest[1].get("t_max_k") or closest[1].get("t_max_i04_k"),
            "n_anomalous_pixels": closest[1].get("n_anomalous_pixels"),
            "n_vent_pixels": closest[1].get("n_vent_pixels"),
            "n_cloud_masked": closest[1].get("n_cloud_masked"),
            "hotspot_dist_km": closest[1].get("hotspot_dist_km"),
        }
    if ov < 0.5 * mv:
        return "close_pass_low_vrp", {
            "closest_delta_min": delta_min,
            "closest_sensor": closest[1].get("sensor"),
            "closest_vrp": ov,
            "miro_vrp": mv,
            "ratio": ov / mv if mv else 0,
        }
    return "matched_ok", {
        "closest_delta_min": delta_min,
        "closest_sensor": closest[1].get("sensor"),
        "closest_vrp": ov,
        "miro_vrp": mv,
        "ratio": ov / mv if mv else 0,
    }


def build_matched_pairs(miro, ours, tol_minutes=30):
    """Return list of (miro_rec, our_rec, ratio) where matched within tolerance
    and our_vrp > 0, our_rec is same sensor family."""
    pairs = []
    for m in miro:
        same_day = same_day_family_records(m, ours)
        if not same_day or same_day[0][0] > tol_minutes:
            continue
        r = same_day[0][1]
        ov = vrp(r)
        mv = m.get("VRP_MW", 0) or 0
        if ov == 0 or mv == 0:
            continue
        pairs.append((m, r, ov / mv))
    return pairs


def q1_analyze_missed(miro, ours):
    """Classify each MIROVA reference as captured or missed-reason-X."""
    cats = defaultdict(list)
    for m in miro:
        cat, details = classify_miss(m, ours)
        cats[cat].append((m, details))
    return cats


def q2_analyze_worst_ratios(pairs, n=15):
    """Top and bottom N pairs by ratio."""
    s = sorted(pairs, key=lambda p: p[2])
    return s[:n], s[-n:]


def q3_modis_gap_analysis(pairs, ours):
    """Understand the MODIS underestimation. Split by magnitude, look at
    t_max_k, scan-related hints from anomaly pixel distances."""
    modis_pairs = [p for p in pairs if sensor_family_mirova(p[0]["sensor"]) == "MODIS"]
    if not modis_pairs:
        return {}

    ratios = [p[2] for p in modis_pairs]
    result = {
        "n_pairs": len(modis_pairs),
        "median_ratio": median(ratios),
        "mean_ratio": mean(ratios),
    }

    # Bucket by MIROVA magnitude
    buckets = {"weak (<0.5 MW)": [], "low (0.5-2 MW)": [], "moderate (2-10 MW)": [], "high (>10 MW)": []}
    for p in modis_pairs:
        mv = p[0]["VRP_MW"]
        if mv < 0.5:
            buckets["weak (<0.5 MW)"].append(p[2])
        elif mv < 2:
            buckets["low (0.5-2 MW)"].append(p[2])
        elif mv < 10:
            buckets["moderate (2-10 MW)"].append(p[2])
        else:
            buckets["high (>10 MW)"].append(p[2])
    result["buckets"] = {k: {"n": len(v), "median_ratio": median(v) if v else 0, "mean_ratio": mean(v) if v else 0} for k, v in buckets.items()}

    # Split by Terra vs Aqua
    terra_ratios = [p[2] for p in modis_pairs if p[1]["sensor"] == "MODIS_TERRA"]
    aqua_ratios = [p[2] for p in modis_pairs if p[1]["sensor"] == "MODIS_AQUA"]
    result["MODIS_TERRA"] = {"n": len(terra_ratios), "median": median(terra_ratios) if terra_ratios else 0, "mean": mean(terra_ratios) if terra_ratios else 0}
    result["MODIS_AQUA"] = {"n": len(aqua_ratios), "median": median(aqua_ratios) if aqua_ratios else 0, "mean": mean(aqua_ratios) if aqua_ratios else 0}

    # Look at our MODIS records: how many anomalous pixels have dist > 1 km?
    # Hint at whether we pick distant cooler pixels dragging VRP down.
    dists_modis = []
    for p in modis_pairs:
        ap = p[1].get("anomaly_pixels") or []
        if ap:
            for px in ap:
                dists_modis.append(px.get("dist_km", 0) or 0)
    if dists_modis:
        result["anomaly_pixel_distance_km"] = {
            "n_pixels": len(dists_modis),
            "median": median(dists_modis),
            "max": max(dists_modis),
            "mean": mean(dists_modis),
        }
    return result


def write_report(miro, ours, cats, top, bot, modis_info, source_path):
    pairs_all = build_matched_pairs(miro, ours)

    lines = []
    lines.append(f"# Lascar diagnostic report (Paso 1)")
    lines.append("")
    lines.append(f"**Source JSON**: `{source_path}`")
    lines.append(f"**MIROVA refs**: `{MIROVA_PATH}` — {len(miro)} records")
    lines.append(f"**Our records**: {len(ours)}")
    lines.append(f"**Matched pairs (same-day, same-family, dt<=30min, both VRP>0)**: {len(pairs_all)}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Q1. Why are we missing 23 MIROVA refs?")
    lines.append("")

    total = len(miro)
    lines.append(f"Category breakdown (n={total}):")
    lines.append("")
    lines.append(f"| Category | Count | % |")
    lines.append(f"|---|---:|---:|")
    for cat in ("matched_ok", "close_pass_low_vrp", "close_pass_zero_vrp", "no_close_pass", "no_record_in_day"):
        c = len(cats.get(cat, []))
        lines.append(f"| {cat} | {c} | {100*c/total:.1f}% |")
    lines.append("")
    lines.append("Notes:")
    lines.append("- `matched_ok`: we detect the ref with a reasonable ratio (>0.5).")
    lines.append("- `close_pass_low_vrp`: close-time match exists but our VRP < 50% of MIROVA's.")
    lines.append("- `close_pass_zero_vrp`: the SAME overpass exists in our data but produced vrp=0. This is the most actionable category.")
    lines.append("- `no_close_pass`: same day but closest record >60 min off — likely a different overpass (day vs night).")
    lines.append("- `no_record_in_day`: we have no matching-sensor record on that UTC day at all.")
    lines.append("")

    # Detail the zero-VRP misses — the most diagnostic category
    zeros = cats.get("close_pass_zero_vrp", [])
    lines.append(f"### `close_pass_zero_vrp` detail (n={len(zeros)})")
    lines.append("")
    if zeros:
        lines.append("| MIROVA dt | MIROVA sensor | MIROVA VRP | Our sensor | dt_min | t_bg | t_max | n_anom | n_vent | n_cloud | hs_dist |")
        lines.append("|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|")
        for m, d in zeros:
            lines.append(
                f"| {m.get('datetime_utc')} | {m.get('sensor')} | {m.get('VRP_MW')} "
                f"| {d.get('closest_sensor')} | {d.get('closest_delta_min'):.0f} "
                f"| {d.get('t_bg_k')} | {d.get('t_max_k')} "
                f"| {d.get('n_anomalous_pixels')} | {d.get('n_vent_pixels')} "
                f"| {d.get('n_cloud_masked')} | {d.get('hotspot_dist_km')} |"
            )
    lines.append("")

    # close_pass_low_vrp detail
    lows = cats.get("close_pass_low_vrp", [])
    lines.append(f"### `close_pass_low_vrp` detail (n={len(lows)})")
    lines.append("")
    if lows:
        lines.append("| MIROVA dt | MIROVA sensor | MIROVA VRP | Our sensor | dt_min | Our VRP | ratio |")
        lines.append("|---|---|---:|---|---:|---:|---:|")
        for m, d in lows[:20]:
            lines.append(
                f"| {m.get('datetime_utc')} | {m.get('sensor')} | {m.get('VRP_MW')} "
                f"| {d.get('closest_sensor')} | {d.get('closest_delta_min'):.0f} "
                f"| {d.get('closest_vrp'):.3f} | {d.get('ratio'):.2f} |"
            )
    lines.append("")

    no_day = cats.get("no_record_in_day", [])
    lines.append(f"### `no_record_in_day` detail (n={len(no_day)})")
    lines.append("")
    if no_day:
        miro_sensors = Counter(m[0].get("sensor") for m in no_day)
        lines.append(f"By MIROVA sensor: {dict(miro_sensors)}")
        # Assume this is likely daytime VIIRS375 that we filter out
        lines.append("")
        for m, d in no_day[:15]:
            dt = m.get("datetime_utc", "")
            lines.append(f"- {dt} {m.get('sensor')} VRP={m.get('VRP_MW')}")
    lines.append("")

    no_close = cats.get("no_close_pass", [])
    lines.append(f"### `no_close_pass` detail (n={len(no_close)})")
    lines.append("")
    if no_close:
        for m, d in no_close[:10]:
            lines.append(
                f"- MIROVA {m.get('datetime_utc')} {m.get('sensor')} VRP={m.get('VRP_MW')} "
                f"→ closest our = {d.get('closest_sensor')} Δ={d.get('closest_delta_min'):.0f}min VRP={d.get('closest_vrp'):.3f}"
            )
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Q2. Pairs with worst ratio (systematic bias?)")
    lines.append("")

    if pairs_all:
        ratios = [p[2] for p in pairs_all]
        lines.append(f"Global stats on {len(pairs_all)} pairs: median={median(ratios):.3f} mean={mean(ratios):.3f}")
        if len(ratios) > 1:
            lines.append(f"  min={min(ratios):.3f} max={max(ratios):.3f} stdev={stdev(ratios):.3f}")
        lines.append("")

        lines.append("### Bottom 15 (we underestimate most)")
        lines.append("")
        lines.append("| MIROVA dt | MIROVA sensor | MIROVA VRP | Our dt | Our sensor | Our VRP | ratio |")
        lines.append("|---|---|---:|---|---|---:|---:|")
        for m, r, ratio in bot:
            lines.append(
                f"| {m.get('datetime_utc')} | {m.get('sensor')} | {m.get('VRP_MW'):.3f} "
                f"| {r.get('datetime_utc')} | {r.get('sensor')} | {vrp(r):.3f} | {ratio:.2f} |"
            )
        lines.append("")

        lines.append("### Top 15 (we overestimate most)")
        lines.append("")
        lines.append("| MIROVA dt | MIROVA sensor | MIROVA VRP | Our dt | Our sensor | Our VRP | ratio |")
        lines.append("|---|---|---:|---|---|---:|---:|")
        for m, r, ratio in top:
            lines.append(
                f"| {m.get('datetime_utc')} | {m.get('sensor')} | {m.get('VRP_MW'):.3f} "
                f"| {r.get('datetime_utc')} | {r.get('sensor')} | {vrp(r):.3f} | {ratio:.2f} |"
            )
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Q3. MODIS sensor-specific gap (session 5 median 0.79 — why?)")
    lines.append("")
    if modis_info:
        lines.append(f"Pairs: {modis_info['n_pairs']}  median={modis_info['median_ratio']:.3f}  mean={modis_info['mean_ratio']:.3f}")
        lines.append("")
        lines.append("By magnitude bucket:")
        lines.append("")
        lines.append("| Bucket | n | median | mean |")
        lines.append("|---|---:|---:|---:|")
        for b, s in modis_info["buckets"].items():
            lines.append(f"| {b} | {s['n']} | {s['median_ratio']:.3f} | {s['mean_ratio']:.3f} |")
        lines.append("")
        lines.append("By platform:")
        lines.append("")
        lines.append(f"- Terra: n={modis_info['MODIS_TERRA']['n']} median={modis_info['MODIS_TERRA']['median']:.3f} mean={modis_info['MODIS_TERRA']['mean']:.3f}")
        lines.append(f"- Aqua:  n={modis_info['MODIS_AQUA']['n']} median={modis_info['MODIS_AQUA']['median']:.3f} mean={modis_info['MODIS_AQUA']['mean']:.3f}")
        lines.append("")
        if "anomaly_pixel_distance_km" in modis_info:
            d = modis_info["anomaly_pixel_distance_km"]
            lines.append(f"Anomalous pixels distance to crater: n={d['n_pixels']} median={d['median']:.2f} km  max={d['max']:.2f} km  mean={d['mean']:.2f} km")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Next-step hypotheses (to decide after reading this)")
    lines.append("")
    lines.append("TBD — fill after reviewing the report.")
    lines.append("")

    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report written to: {OUTPUT}")
    print()
    print("\n".join(lines[:40]))  # preview


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=str(DEFAULT_SOURCE))
    args = parser.parse_args()
    miro = load(MIROVA_PATH)
    ours = load(args.source)

    cats = q1_analyze_missed(miro, ours)
    pairs = build_matched_pairs(miro, ours)
    top, bot = q2_analyze_worst_ratios(pairs, n=15)
    modis_info = q3_modis_gap_analysis(pairs, ours)

    write_report(miro, ours, cats, top, bot, modis_info, args.source)


if __name__ == "__main__":
    main()
