"""
S54-PIXEL-AB-MIROVA: pixel-level comparison Villarrica.

5 paradigmatic cases: extract our pipeline diagnostics + anomaly_pixels,
compare with MIROVA TIFs when available.
"""
import json
import os
import sys
from pathlib import Path

io_enc = "utf-8"
sys.stdout = sys.__stdout__

JSON = Path(r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/.claude/worktrees/nostalgic-aryabhata-e05d1e/data/mirova_equivalent/Villarrica.json")
TIF_DIR = Path(r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/mirova-tif-archive/data/tif/Villarrica")

# Villarrica vent (from volcanoes.yaml — lava lake)
VENT_LAT = -39.4202
VENT_LON = -71.9347

CASES = [
    {"name": "1_2026-05-11_NOAA20", "date": "2026-05-11", "time": "06:00", "sensor_hint": "VIIRS"},
    {"name": "2_2026-05-14_NOAA21", "date": "2026-05-14", "time": "05:48", "sensor_hint": "VIIRS"},
    {"name": "3_2026-04-09_NOAA20", "date": "2026-04-09", "time": "06:00", "sensor_hint": "VIIRS"},
    {"name": "4_2026-03-08_NOAA20", "date": "2026-03-08", "time": "06:00", "sensor_hint": "VIIRS"},
    {"name": "5_2026-02-26_NOAA20", "date": "2026-02-26", "time": "05:42", "sensor_hint": "VIIRS"},
]


def find_record(records, date, time_hint):
    """Find record matching date + approximate time."""
    matches = []
    for r in records:
        dt = r.get("datetime_utc", "")
        if dt.startswith(date):
            matches.append(r)
    return matches


def haversine(lat1, lon1, lat2, lon2):
    import math
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dlam/2)**2
    return 2 * R * math.asin(math.sqrt(a))


def summarize_record(r):
    px = r.get("anomaly_pixels") or []
    dist_to_vent = [
        haversine(VENT_LAT, VENT_LON, p.get("lat"), p.get("lon"))
        for p in px if p.get("lat") is not None
    ]
    summit_px = [d for d in dist_to_vent if d <= 2.5]
    return {
        "dt": r.get("datetime_utc"),
        "sensor": r.get("sensor"),
        "granule": r.get("granule"),
        "vrp_mw": r.get("vrp_mw"),
        "n_anom_px": r.get("n_anomalous_pixels"),
        "n_clusters": r.get("n_hotspots_clustered"),
        "triggered_test1": r.get("triggered_test1"),
        "n_test1_px": r.get("n_test1_pixels"),
        "n_bt_path": r.get("n_bt_path") or r.get("diag_n_bt_path"),
        "n_nti_path": r.get("n_nti_path") or r.get("diag_n_nti_path"),
        "n_dnti_ctx": r.get("n_dnti_ctx_path") or r.get("diag_n_dnti_ctx_path"),
        "t_bg_k": r.get("t_bg_k"),
        "t_max_k": r.get("t_max_k"),
        "sigma_bg": r.get("diag_sigma_bg_k"),
        "nti_bg": r.get("diag_nti_bg") or r.get("nti_bg"),
        "nti_max": r.get("diag_nti_max") or r.get("nti_max"),
        "nti_std": r.get("diag_nti_std"),
        "roi_p95": r.get("diag_roi_p95_k"),
        "eff_thresh": r.get("diag_eff_threshold_k"),
        "t_max_dist": r.get("diag_t_max_dist_km"),
        "final_src": r.get("final_hotspot_source"),
        "dist_class": r.get("distance_class"),
        "n_px_le_2_5km": len(summit_px),
        "n_px_total_anom": len(px),
        "summit_min_dist": min(dist_to_vent) if dist_to_vent else None,
    }


def main():
    with open(JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    recs = data["records"]
    print(f"Loaded {len(recs)} records\n")

    for case in CASES:
        print("=" * 80)
        print(f"CASE {case['name']}  (MIROVA expects crater detection)")
        print("=" * 80)
        matches = find_record(recs, case["date"], case["time"])
        if not matches:
            print(f"  NO record found for {case['date']}")
            continue
        # Filter to night-time around the time hint
        target_hour = int(case["time"].split(":")[0])
        nearby = [r for r in matches if abs(int(r["datetime_utc"].split(" ")[1].split(":")[0]) - target_hour) <= 1]
        if not nearby:
            nearby = matches[:5]
        print(f"  Found {len(matches)} records on date, showing {len(nearby)} near {case['time']}:")
        for r in nearby:
            s = summarize_record(r)
            print(f"  [{s['dt']}] {s['sensor']}")
            print(f"    granule:        {s['granule']}")
            print(f"    vrp_mw:         {s['vrp_mw']}")
            print(f"    n_anom_px:      {s['n_anom_px']}  clusters: {s['n_clusters']}")
            print(f"    n_summit_<=2.5km: {s['n_px_le_2_5km']}  min_dist: {s['summit_min_dist']}")
            print(f"    triggered_test1: {s['triggered_test1']}  n_test1_px: {s['n_test1_px']}  k_obs: {r.get('test1_k_observed')}")
            print(f"    paths: bt={s['n_bt_path']}  nti={s['n_nti_path']}  dnti_ctx={s['n_dnti_ctx']}")
            print(f"    bg/max:  T_bg={s['t_bg_k']:.2f}K  T_max={s['t_max_k']:.2f}K  sigma_bg={s['sigma_bg']}")
            print(f"    NTI:     bg={s['nti_bg']}  max={s['nti_max']}  std={s['nti_std']}")
            print(f"    ROI:     p95={s['roi_p95']}  eff_thresh={s['eff_thresh']}  t_max_dist={s['t_max_dist']}km")
            print(f"    final:   src={s['final_src']}  dist_class={s['dist_class']}")
            # Top-5 anomaly pixels
            px = r.get("anomaly_pixels") or []
            if px:
                px_sorted = sorted(px, key=lambda p: -(p.get("bt_k") or 0))[:5]
                print(f"    top-5 anomaly_pixels (by BT):")
                for p in px_sorted:
                    d = haversine(VENT_LAT, VENT_LON, p.get("lat"), p.get("lon")) if p.get("lat") else None
                    print(f"      lat={p.get('lat'):.4f} lon={p.get('lon'):.4f} BT={p.get('bt_k')} NTI={p.get('nti')} d_vent={d:.2f}km")
        print()


if __name__ == "__main__":
    main()
