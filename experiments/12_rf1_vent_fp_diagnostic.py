"""
Experiment 12 — RF1 Vent-path false-positive diagnostic

Compare vent-only detection rates between volcanoes WITH confirmed thermal
anomalies (Active group) and volcanoes WITHOUT (Control group).

If control volcanoes show similar vent-only rates as active volcanoes,
the vent path is picking up noise (terrain variability, not volcanic signal).
If control << active, the vent path captures real sub-pixel thermal signal.

Breakdown by sensor family is critical: MODIS 1km pixels mix more background
than VIIRS 375m, so noise characteristics differ.
"""

import json
import os
from pathlib import Path
from collections import defaultdict
import statistics

DATA_DIR = Path(r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\data\mirova_equivalent")

ACTIVE = ["Lascar", "PuyehueCordonCaulle", "Lastarria", "Isluga",
          "Tupungatito", "PlanchonPeteroa", "Chaiten"]
CONTROL = ["Copahue", "Llaima", "NevadosDeChillan"]

SENSOR_FAMILIES = {
    "VIIRS375": ["VIIRS_SNPP", "VIIRS_NOAA20"],
    "VIIRS750": ["VIIRS_SNPP_750", "VIIRS_NOAA20_750"],
    "MODIS": ["MODIS_TERRA", "MODIS_AQUA"],
}

def classify_sensor(sensor_name):
    for family, members in SENSOR_FAMILIES.items():
        if sensor_name in members:
            return family
    return "UNKNOWN"


def analyze_volcano(name):
    fpath = DATA_DIR / f"{name}.json"
    if not fpath.exists():
        print(f"  WARNING: {fpath} not found")
        return None
    with open(fpath) as f:
        data = json.load(f)

    records = data.get("records", [])
    if not records:
        return None

    # Global stats
    stats = {
        "name": name,
        "total": len(records),
        "detections": 0,
        "vent_only": 0,
        "eruption_path": 0,
        "vent_only_vrps": [],
        "by_sensor": defaultdict(lambda: {
            "total": 0, "detections": 0, "vent_only": 0,
            "eruption_path": 0, "vent_only_vrps": []
        }),
    }

    for r in records:
        vrp = r.get("vrp_mw", 0) or 0
        n_anom = r.get("n_anomalous_pixels", 0) or 0
        n_vent = r.get("n_vent_pixels", 0) or 0
        vrp_vent = r.get("vrp_vent_mw", 0) or 0
        sensor = r.get("sensor", "UNKNOWN")
        family = classify_sensor(sensor)

        is_detection = vrp > 0
        is_vent_only = (vrp > 0) and (n_anom == 0) and (n_vent > 0)
        is_eruption = n_anom > 0

        stats["by_sensor"][family]["total"] += 1

        if is_detection:
            stats["detections"] += 1
            stats["by_sensor"][family]["detections"] += 1
        if is_vent_only:
            stats["vent_only"] += 1
            stats["vent_only_vrps"].append(vrp_vent)
            stats["by_sensor"][family]["vent_only"] += 1
            stats["by_sensor"][family]["vent_only_vrps"].append(vrp_vent)
        if is_eruption:
            stats["eruption_path"] += 1
            stats["by_sensor"][family]["eruption_path"] += 1

    return stats


def fmt_rate(n, total):
    if total == 0:
        return "  -  "
    pct = 100.0 * n / total
    return f"{pct:5.1f}%"


def fmt_vrp_stats(vrps):
    if not vrps:
        return "  -  "
    med = statistics.median(vrps)
    if len(vrps) >= 2:
        q = statistics.quantiles(vrps, n=4)
        return f"med={med:.2f}  p25={q[0]:.2f}  p75={q[2]:.2f}  max={max(vrps):.2f}"
    return f"med={med:.2f}  max={max(vrps):.2f}"


def print_section(title, volcanoes, all_stats):
    print(f"\n{'='*90}")
    print(f"  {title}")
    print(f"{'='*90}")
    header = f"{'Volcano':<22} {'Passes':>6} {'Detect':>6} {'Erupt':>5} {'VentOnly':>8} {'VO Rate':>7}  VRP_vent stats"
    print(header)
    print("-" * 90)
    for s in all_stats:
        if s["name"] not in volcanoes:
            continue
        print(f"{s['name']:<22} {s['total']:>6} {s['detections']:>6} {s['eruption_path']:>5} "
              f"{s['vent_only']:>8} {fmt_rate(s['vent_only'], s['total']):>7}  "
              f"{fmt_vrp_stats(s['vent_only_vrps'])}")


def print_sensor_breakdown(all_stats):
    print(f"\n{'='*90}")
    print("  SENSOR FAMILY BREAKDOWN")
    print(f"{'='*90}")

    for family in ["VIIRS375", "VIIRS750", "MODIS"]:
        print(f"\n--- {family} ---")
        header = f"{'Volcano':<22} {'Group':<8} {'Passes':>6} {'Detect':>6} {'Erupt':>5} {'VentOnly':>8} {'VO Rate':>7}"
        print(header)
        print("-" * 75)

        active_vo = 0
        active_total = 0
        control_vo = 0
        control_total = 0

        for s in all_stats:
            sf = s["by_sensor"].get(family)
            if sf is None or sf["total"] == 0:
                continue
            group = "Active" if s["name"] in ACTIVE else "Control"
            print(f"{s['name']:<22} {group:<8} {sf['total']:>6} {sf['detections']:>6} "
                  f"{sf['eruption_path']:>5} {sf['vent_only']:>8} {fmt_rate(sf['vent_only'], sf['total']):>7}")

            if s["name"] in ACTIVE:
                active_vo += sf["vent_only"]
                active_total += sf["total"]
            elif s["name"] in CONTROL:
                control_vo += sf["vent_only"]
                control_total += sf["total"]

        print("-" * 75)
        print(f"  {'Active aggregate':<28} {active_total:>6} {'':>6} {'':>5} {active_vo:>8} {fmt_rate(active_vo, active_total):>7}")
        print(f"  {'Control aggregate':<28} {control_total:>6} {'':>6} {'':>5} {control_vo:>8} {fmt_rate(control_vo, control_total):>7}")

        if active_total > 0 and control_total > 0:
            ar = 100.0 * active_vo / active_total
            cr = 100.0 * control_vo / control_total
            ratio = ar / cr if cr > 0 else float('inf')
            print(f"  => Active/Control ratio: {ratio:.2f}x")
        elif control_total > 0 and control_vo == 0:
            print(f"  => Control has 0 vent-only detections")
        else:
            print(f"  => Insufficient data for ratio")


def main():
    all_names = ACTIVE + CONTROL
    all_stats = []
    for name in all_names:
        s = analyze_volcano(name)
        if s:
            all_stats.append(s)

    print_section("ACTIVE VOLCANOES (confirmed thermal anomaly)", ACTIVE, all_stats)
    print_section("CONTROL VOLCANOES (no confirmed thermal anomaly)", CONTROL, all_stats)

    # Aggregate comparison
    print(f"\n{'='*90}")
    print("  AGGREGATE COMPARISON")
    print(f"{'='*90}")

    for group_name, group_list in [("Active", ACTIVE), ("Control", CONTROL)]:
        total = sum(s["total"] for s in all_stats if s["name"] in group_list)
        det = sum(s["detections"] for s in all_stats if s["name"] in group_list)
        vo = sum(s["vent_only"] for s in all_stats if s["name"] in group_list)
        ep = sum(s["eruption_path"] for s in all_stats if s["name"] in group_list)
        vo_vrps = []
        for s in all_stats:
            if s["name"] in group_list:
                vo_vrps.extend(s["vent_only_vrps"])

        print(f"\n  {group_name}:  passes={total}  detections={det}  eruption={ep}  vent_only={vo}  "
              f"vent_only_rate={fmt_rate(vo, total)}")
        if vo_vrps:
            print(f"    VRP_vent stats: {fmt_vrp_stats(vo_vrps)}")

    # Per-sensor breakdown
    print_sensor_breakdown(all_stats)

    # Conclusion
    print(f"\n{'='*90}")
    print("  INTERPRETATION")
    print(f"{'='*90}")

    active_total = sum(s["total"] for s in all_stats if s["name"] in ACTIVE)
    active_vo = sum(s["vent_only"] for s in all_stats if s["name"] in ACTIVE)
    control_total = sum(s["total"] for s in all_stats if s["name"] in CONTROL)
    control_vo = sum(s["vent_only"] for s in all_stats if s["name"] in CONTROL)

    if active_total > 0 and control_total > 0:
        ar = 100.0 * active_vo / active_total
        cr = 100.0 * control_vo / control_total
        print(f"\n  Overall vent-only rate:  Active = {ar:.2f}%   Control = {cr:.2f}%")
        if cr > 0:
            ratio = ar / cr
            print(f"  Ratio Active/Control = {ratio:.2f}x")
            if ratio < 1.5:
                print("\n  CONCLUSION: Vent-only rates are SIMILAR between active and control.")
                print("  => The vent path is likely picking up NOISE (terrain variability),")
                print("     not real volcanic signal. Consider raising the vent threshold or")
                print("     removing the vent path from the mirova_equivalent profile.")
            elif ratio < 3.0:
                print("\n  CONCLUSION: Vent-only rate is MODERATELY higher in active volcanoes.")
                print("  => Mixed signal: some real detections but substantial noise floor.")
                print("     Check per-sensor breakdown to see if one sensor family is cleaner.")
            else:
                print("\n  CONCLUSION: Vent-only rate is MUCH higher in active volcanoes.")
                print("  => The vent path is capturing real volcanic signal.")
                print("     Noise floor from control is low relative to active signal.")
        else:
            print("  Control has 0 vent-only detections.")
            if active_vo > 0:
                print("\n  CONCLUSION: Strong evidence that vent-only detections are real signal.")
            else:
                print("\n  CONCLUSION: Neither group has vent-only detections — path is inactive.")
    else:
        print("\n  Insufficient data for comparison.")


if __name__ == "__main__":
    main()
