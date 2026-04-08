"""
validate_lascar_vs_mirova.py — Comprehensive validation of Lascar post-scan-fix VRP
against the 203 MIROVA reference records.

Compares:
  1. Pre-fix JSON (data/backups_pre_scanfix/Lascar_pre_scanfix.json)
  2. Post-fix JSON (data/Lascar.json)
  3. MIROVA reference (data/mirova/Lascar.json)

Matching rule: MIROVA record and ours are "paired" if they share the same
UTC day AND the sensor family matches (MIROVA "MODIS" -> our MODIS_*,
MIROVA "VIIRS375" -> our VIIRS_*_375 equivalents, MIROVA "VIIRS" -> VIIRS_*_750).
Within a day, we pick the closest-in-time nonzero detection on the matching
sensor family.

Reports:
  - capture rate (how many MIROVA records we detect at all)
  - ratio nuestro/MIROVA per sensor family, pre vs post fix
  - distribution of ratio changes
"""
import json
from collections import defaultdict
from datetime import datetime
from statistics import mean, median


def load(path):
    with open(path) as f:
        d = json.load(f)
    return d.get("records", d) if isinstance(d, dict) else d


def sensor_family_mirova(s):
    """Map MIROVA sensor strings to our sensor family tags."""
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
        return datetime.strptime(s[:16], "%Y-%m-%d %H:%M")
    except Exception:
        return None


def best_match(miro_rec, ours, tol_minutes=30):
    """Pick best same-family record in `ours` for a given MIROVA rec.
    Prefer same-minute; else closest within `tol_minutes`; else same day."""
    miro_fam = sensor_family_mirova(miro_rec.get("sensor", ""))
    if miro_fam is None:
        return None
    miro_dt = parse_dt(miro_rec.get("datetime_utc", ""))
    if miro_dt is None:
        return None
    miro_day = miro_dt.date()

    same_day = []
    for r in ours:
        if sensor_family_ours(r.get("sensor", "")) != miro_fam:
            continue
        rdt = parse_dt(r.get("datetime_utc", ""))
        if rdt is None or rdt.date() != miro_day:
            continue
        delta = abs((rdt - miro_dt).total_seconds()) / 60.0
        same_day.append((delta, r))

    if not same_day:
        return None
    same_day.sort(key=lambda x: x[0])
    # Prefer match within tolerance, otherwise closest of the day
    within = [x for x in same_day if x[0] <= tol_minutes]
    return (within[0] if within else same_day[0])[1]


def vrp(r):
    return max(r.get("vrp_mw", 0) or 0, r.get("vrp_vent_mw", 0) or 0)


def validate(label, ours, miro):
    print(f"\n=== {label} ===")
    print(f"ours records (total): {len(ours)}")
    print(f"ours with VRP>0: {sum(1 for r in ours if vrp(r) > 0)}")

    matches_by_fam = defaultdict(list)  # family -> list of (miro_vrp, our_vrp)
    unmatched = defaultdict(int)
    our_has_record_but_zero = defaultdict(int)
    no_our_record = defaultdict(int)

    for m in miro:
        fam = sensor_family_mirova(m.get("sensor", ""))
        if fam is None:
            continue
        r = best_match(m, ours)
        mv = m.get("VRP_MW", 0) or 0
        if r is None:
            no_our_record[fam] += 1
            unmatched[fam] += 1
            continue
        ov = vrp(r)
        if ov == 0:
            our_has_record_but_zero[fam] += 1
            unmatched[fam] += 1
            continue
        matches_by_fam[fam].append((mv, ov))

    print()
    print(f"{'family':<12} {'miro_total':>10} {'matched':>8} {'missed_no_rec':>14} {'missed_zero':>12} {'capture_rate':>12}")
    for fam in ("MODIS", "VIIRS_375", "VIIRS_750"):
        miro_total = sum(1 for m in miro if sensor_family_mirova(m.get("sensor", "")) == fam)
        matched = len(matches_by_fam[fam])
        capture = matched / miro_total if miro_total else 0
        print(f"{fam:<12} {miro_total:>10} {matched:>8} {no_our_record[fam]:>14} "
              f"{our_has_record_but_zero[fam]:>12} {capture:>11.1%}")

    total_miro = sum(1 for m in miro if sensor_family_mirova(m.get("sensor", "")) is not None)
    total_matched = sum(len(v) for v in matches_by_fam.values())
    print(f"{'TOTAL':<12} {total_miro:>10} {total_matched:>8} "
          f"{'':>14} {'':>12} {total_matched/total_miro if total_miro else 0:>11.1%}")

    print()
    print(f"{'family':<12} {'n_paired':>8} {'mean_ratio':>11} {'median_ratio':>13} "
          f"{'mean_miro':>10} {'mean_ours':>10}")
    for fam in ("MODIS", "VIIRS_375", "VIIRS_750"):
        pairs = matches_by_fam[fam]
        if not pairs:
            continue
        ratios = [o / m for m, o in pairs if m > 0]
        if ratios:
            print(f"{fam:<12} {len(pairs):>8} {mean(ratios):>11.2f} "
                  f"{median(ratios):>13.2f} "
                  f"{mean(m for m, _ in pairs):>10.3f} "
                  f"{mean(o for _, o in pairs):>10.3f}")

    # Overall
    all_pairs = [p for v in matches_by_fam.values() for p in v]
    if all_pairs:
        all_ratios = [o / m for m, o in all_pairs if m > 0]
        print(f"{'ALL':<12} {len(all_pairs):>8} {mean(all_ratios):>11.2f} "
              f"{median(all_ratios):>13.2f} "
              f"{mean(m for m, _ in all_pairs):>10.3f} "
              f"{mean(o for _, o in all_pairs):>10.3f}")

    return matches_by_fam


def main():
    miro = load("data/mirova/Lascar.json")
    old = load("data/backups_pre_scanfix/Lascar_pre_scanfix.json")
    new = load("data/Lascar.json")

    print(f"MIROVA records: {len(miro)}")

    m_old = validate("PRE-FIX", old, miro)
    m_new = validate("POST-FIX (scan-angle corrected)", new, miro)

    # Delta comparison: same (miro_rec, sensor_family) key change
    print("\n=== DELTA (pre -> post) on common matches ===")
    for fam in ("MODIS", "VIIRS_375", "VIIRS_750"):
        old_idx = {i: (m, o) for i, (m, o) in enumerate(m_old[fam])}
        new_idx = {i: (m, o) for i, (m, o) in enumerate(m_new[fam])}
        # Just report aggregate change
        if not m_new[fam]:
            continue
        old_ratio = mean(o / m for m, o in m_old[fam] if m > 0) if m_old[fam] else 0
        new_ratio = mean(o / m for m, o in m_new[fam] if m > 0) if m_new[fam] else 0
        print(f"  {fam:<12} mean ratio: {old_ratio:.2f} -> {new_ratio:.2f}  "
              f"(improvement factor {new_ratio/old_ratio:.2f}x)" if old_ratio else "")


if __name__ == "__main__":
    main()
