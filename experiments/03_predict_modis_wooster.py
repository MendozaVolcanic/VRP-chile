"""
experiments/03_predict_modis_wooster.py

For the 16 MODIS records in the 2-10 MW bucket (where our pipeline reports
n_anomalous=0 due to the roi_p95 filter), compute what Wooster would give
IF the pipeline did apply it to the observed t_max_k pixel.

This is the prediction for E1's expected impact. If the Wooster-predicted
VRP for each record lands close to MIROVA's value, it confirms that:
  1. The physics (Wooster MIR) is correct for Lascar
  2. The scan-angle and pixel-area corrections are working
  3. The sole issue is the p95 filter blocking an otherwise-correct detection

No code changes. No pipeline changes. Pure math from the existing JSON.
"""
import json
import math
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).parent.parent

# MODIS Band 21/22 constants (Coppola 2015)
C1 = 1.19104e8    # W um^4 / m^2 / sr (2hc^2)
C2 = 14388.0      # um K (hc/k)
LAMBDA = 3.93     # um (MODIS MIR band center)
WOOSTER = 18.9    # empirical coefficient from Wooster et al. 2003

MODIS_NADIR_PIXEL_AREA_M2 = 1_000_000.0  # 1 km^2 at nadir


def planck_L(T):
    """Spectral radiance at 3.93 um for temperature T (K). W/m^2/sr/um."""
    return C1 / (LAMBDA ** 5 * (math.exp(C2 / (LAMBDA * T)) - 1))


def wooster_vrp_mw(T_pixel, T_bg, pixel_area_m2):
    """
    Wooster MIR VRP for a single pixel.
    Uses Planck radiance at T_pixel and T_bg (not radiance-of-median).
    """
    L_hot = planck_L(T_pixel)
    L_bg = planck_L(T_bg)
    return pixel_area_m2 * WOOSTER * (L_hot - L_bg) / 1e6


def sensor_fam_ours(s):
    if s and s.startswith("MODIS"):
        return "MODIS"
    if s in ("VIIRS_SNPP", "VIIRS_NOAA20"):
        return "VIIRS_375"
    if s in ("VIIRS_SNPP_750", "VIIRS_NOAA20_750"):
        return "VIIRS_750"
    return None


def sensor_fam_mir(s):
    return {"MODIS": "MODIS", "VIIRS375": "VIIRS_375", "VIIRS": "VIIRS_750"}.get(s)


def parse_dt(s):
    try:
        return datetime.strptime(str(s)[:16], "%Y-%m-%d %H:%M")
    except Exception:
        return None


def main():
    mirova = json.load(open(REPO / "data" / "mirova" / "Lascar.json"))["records"]
    ours = json.load(open(REPO / "experiments" / "lascar_session5_snapshot.json"))["records"]

    # Collect MODIS 2-10 MW pairs
    pairs = []
    for m in mirova:
        if sensor_fam_mir(m["sensor"]) != "MODIS":
            continue
        mv = m["VRP_MW"]
        if mv < 2 or mv >= 10:
            continue
        mdt = parse_dt(m["datetime_utc"])
        if not mdt:
            continue
        # Find closest same-day MODIS record in ours
        candidates = []
        for r in ours:
            if sensor_fam_ours(r.get("sensor", "")) != "MODIS":
                continue
            rdt = parse_dt(r.get("datetime_utc", ""))
            if rdt is None or rdt.date() != mdt.date():
                continue
            delta = abs((rdt - mdt).total_seconds()) / 60.0
            candidates.append((delta, r))
        if not candidates:
            continue
        candidates.sort(key=lambda x: x[0])
        delta, r = candidates[0]
        if delta > 30:
            continue
        pairs.append((m, r))

    print(f"MODIS 2-10 MW pairs: {len(pairs)}\n")

    # For each pair, compute:
    #   - current pipeline VRP (actual reported)
    #   - Wooster VRP using t_max_k (if filters weren't blocking)
    #   - MIROVA value
    #   - predicted ratio if E1 works

    print(f"{'MIROVA dt':<18} {'sensor':<12} {'miro':>6} {'our':>7} {'t_bg':>7} {'t_max':>7} "
          f"{'dT':>5} {'wooster_pred':>13} {'pred_ratio':>11} {'curr_ratio':>11}")
    print("-" * 125)

    wooster_ratios = []
    current_ratios = []
    improvements = []
    for m, r in pairs:
        mv = m["VRP_MW"]
        ov = max(r.get("vrp_mw", 0) or 0, r.get("vrp_vent_mw", 0) or 0)
        t_bg = r.get("t_bg_k")
        t_max = r.get("t_max_k") or r.get("t_max_i04_k")
        if t_bg is None or t_max is None:
            continue
        dT = t_max - t_bg

        # Predicted Wooster VRP assuming we counted a SINGLE pixel at t_max_k
        # (conservative: Lascar's vent fits in 1 MODIS pixel, so single-pixel
        # is the expected detection count for fumarolic 2-10 MW signals)
        w_vrp = wooster_vrp_mw(t_max, t_bg, MODIS_NADIR_PIXEL_AREA_M2)

        pred_ratio = w_vrp / mv
        curr_ratio = ov / mv
        wooster_ratios.append(pred_ratio)
        current_ratios.append(curr_ratio)
        improvements.append((r["datetime_utc"], r["sensor"], mv, ov, w_vrp))

        print(f"{m['datetime_utc']:<18} {r['sensor']:<12} {mv:>6.2f} {ov:>7.3f} "
              f"{t_bg:>7.2f} {t_max:>7.2f} {dT:>5.2f} "
              f"{w_vrp:>13.3f} {pred_ratio:>11.2f} {curr_ratio:>11.2f}")

    from statistics import mean, median

    print()
    print("=" * 125)
    print(f"Current pipeline:  mean ratio = {mean(current_ratios):.3f}  median = {median(current_ratios):.3f}")
    print(f"Wooster predicted: mean ratio = {mean(wooster_ratios):.3f}  median = {median(wooster_ratios):.3f}")
    print()
    print("INTERPRETATION:")
    print(f"  If the Wooster prediction median is close to 1.0, it means the 'physics is")
    print(f"  right' and the p95 filter is the SOLE obstacle. E1 (H6 fix) should bring")
    print(f"  the current ratios close to the wooster column.")
    print()
    print("  If the Wooster prediction is systematically off (e.g., median < 0.8), then")
    print(f"  there's additional calibration work beyond the p95 filter (sub-pixel mixing,")
    print(f"  scan-angle, background choice).")
    print()

    # How many would change category from close_pass_low/zero to matched_ok (ratio >= 0.5)?
    cross_0p5 = sum(1 for r in wooster_ratios if r >= 0.5)
    cross_0p8 = sum(1 for r in wooster_ratios if r >= 0.8)
    print(f"Records with predicted ratio >= 0.5 (would become 'matched_ok'): {cross_0p5}/{len(wooster_ratios)}")
    print(f"Records with predicted ratio >= 0.8 (near-perfect calibration):  {cross_0p8}/{len(wooster_ratios)}")

    # Sensitivity: what if pixel area is the SCAN-ANGLE-CORRECTED area instead of 1 km^2?
    # We don't have the actual scan zenith per record, but we know the correction can
    # multiply by 1x (nadir) to ~13x (edge). Use a median of ~2x for illustration.
    print()
    print("Sensitivity: same prediction with 1.5x pixel area (mid-swath scan correction):")
    ratios_1p5 = []
    for m, r in pairs:
        mv = m["VRP_MW"]
        t_bg = r.get("t_bg_k")
        t_max = r.get("t_max_k") or r.get("t_max_i04_k")
        if t_bg is None or t_max is None:
            continue
        w_vrp = wooster_vrp_mw(t_max, t_bg, MODIS_NADIR_PIXEL_AREA_M2 * 1.5)
        ratios_1p5.append(w_vrp / mv)
    print(f"  median predicted ratio (1.5x area): {median(ratios_1p5):.3f}")
    print(f"  mean predicted ratio (1.5x area):   {mean(ratios_1p5):.3f}")


if __name__ == "__main__":
    main()
