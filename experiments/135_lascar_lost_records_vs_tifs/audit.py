"""F2.6.g — R2 pixel-level audit: Lascar lost records S26->S71 vs MIROVA TIF archive.

Identify records where S26 baseline had detection (vrp_mw > 0.01) but S71 current
either has no detection or vrp_mw < 0.01, then cross-check with MIROVA TIF archive
to classify centroide MIROVA distance vs Lascar vent.
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

try:
    import rasterio
except ImportError:
    rasterio = None

ROOT = Path(__file__).parent
S26_PATH = ROOT / "Lascar_S26.json"
S71_PATH = Path("data/mirova_equivalent/Lascar.json")
TIF_DIR = Path("../mirova-tif-archive/data/tif/Lascar")
TIF_INDEX = Path("../mirova-tif-archive/index.csv")

VENT_LAT = -23.36293
VENT_LON = -67.731416
SALAR_LAT = -23.7
SALAR_LON = -68.3

# TIF archive window
ARCHIVE_START = datetime(2026, 5, 8)
ARCHIVE_END = datetime(2026, 5, 21)


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def parse_dt(s):
    if not s:
        return None
    s = s.replace("T", " ").split("+")[0]
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def sensor_match_key(sensor, dt):
    """Map sensor variants to canonical for matching."""
    if not sensor:
        return None
    s = sensor.upper()
    if "MODIS" in s:
        canon = "MODIS"
    elif "VIIRS" in s and ("375" in s or "I" in s.replace("VIIRS", "")):
        canon = "VIIRS375"
    elif "VIIRS" in s:
        canon = "VIIRS750"
    elif "NPP" in s or "NOAA" in s:
        # heuristic - VIIRS
        canon = "VIIRS750"
    else:
        canon = s
    # round to nearest 5 minutes
    if dt:
        minute = (dt.minute // 5) * 5
        bucket = dt.replace(minute=minute, second=0, microsecond=0)
        return (canon, bucket)
    return (canon, None)


def main():
    print("Loading JSONs...")
    s26 = json.loads(S26_PATH.read_text())
    s71 = json.loads(S71_PATH.read_text())

    s26_recs = s26["records"]
    s71_recs = s71["records"]
    print(f"S26: {len(s26_recs)} records | S71: {len(s71_recs)} records")

    # Index S71 by (sensor_canonical, datetime_bucket)
    s71_idx = {}
    for r in s71_recs:
        dt = parse_dt(r.get("datetime_utc"))
        key = sensor_match_key(r.get("sensor"), dt)
        if key[1] is None:
            continue
        s71_idx[key] = r

    # Find S26 records with detection, no match in S71 or vrp_mw<0.01 in S71
    lost = []
    for r in s26_recs:
        vrp = r.get("vrp_mw") or 0
        if vrp <= 0.01:
            continue
        dt = parse_dt(r.get("datetime_utc"))
        if dt is None:
            continue
        key = sensor_match_key(r.get("sensor"), dt)
        s71_r = s71_idx.get(key)
        # try +-5 min adjacent
        if s71_r is None and key[1]:
            for delta in (-5, 5, -10, 10):
                alt_bucket = key[1] + timedelta(minutes=delta)
                alt_key = (key[0], alt_bucket)
                if alt_key in s71_idx:
                    s71_r = s71_idx[alt_key]
                    break
        s71_vrp = (s71_r.get("vrp_mw") or 0) if s71_r else None
        if s71_r is None or s71_vrp <= 0.01:
            lost.append({
                "datetime_utc": r.get("datetime_utc"),
                "sensor": r.get("sensor"),
                "s26_vrp_mw": vrp,
                "s26_hotspot_lat": r.get("final_hotspot_lat"),
                "s26_hotspot_lon": r.get("final_hotspot_lon"),
                "s26_hotspot_dist_km": r.get("final_hotspot_dist_km"),
                "s26_distance_class": r.get("distance_class"),
                "s26_n_anomalous_pixels": r.get("n_anomalous_pixels"),
                "s71_present": s71_r is not None,
                "s71_vrp_mw": s71_vrp,
                "_dt": dt,
                "_sensor_canon": key[0],
            })

    print(f"Lost records total: {len(lost)}")

    # Bucket by archive window
    in_window = [r for r in lost if ARCHIVE_START <= r["_dt"] <= ARCHIVE_END]
    print(f"Lost in archive window (2026-05-08 to 2026-05-20): {len(in_window)}")

    # Match each in_window to a TIF
    if not TIF_INDEX.exists():
        print(f"TIF index not found: {TIF_INDEX}")
        return

    # Parse TIF index
    tifs = []
    with TIF_INDEX.open() as f:
        header = f.readline().strip().split(",")
        for line in f:
            parts = line.strip().split(",")
            if len(parts) < len(header):
                continue
            d = dict(zip(header, parts))
            if d.get("volcano") != "Lascar":
                continue
            try:
                last_mod = datetime.fromisoformat(d["last_modified_utc"].replace("Z", "+00:00")).replace(tzinfo=None)
            except Exception:
                continue
            tifs.append({
                "sensor": d["sensor"],
                "dt": last_mod,
                "tif_path": d["tif_path"],
            })
    print(f"Lascar TIFs indexed: {len(tifs)}")

    # For each lost in_window, find nearest TIF within +- 2h with same sensor
    for r in in_window:
        canon = r["_sensor_canon"]
        target = r["_dt"]
        best = None
        best_delta = None
        for t in tifs:
            if t["sensor"] != canon:
                continue
            delta = abs((t["dt"] - target).total_seconds())
            if delta > 7200:  # 2h
                continue
            if best is None or delta < best_delta:
                best = t
                best_delta = delta
        r["tif_match"] = best["tif_path"] if best else None
        r["tif_delta_sec"] = best_delta

    # For matched TIFs, compute centroid distance to vent
    matched = [r for r in in_window if r.get("tif_match")]
    print(f"Records with TIF match: {len(matched)}")

    if rasterio is None:
        print("WARN: rasterio not available, skipping TIF reads")
        for r in matched:
            r["centroid_dist_km"] = None
            r["category"] = "C"
    else:
        archive_root = Path("../mirova-tif-archive")
        for r in matched:
            tif_path = archive_root / r["tif_match"]
            if not tif_path.exists():
                r["centroid_dist_km"] = None
                r["mirova_vrp_header"] = None
                r["category"] = "C"
                continue
            try:
                with rasterio.open(tif_path) as src:
                    arr = src.read(1).astype(float)
                    # mask 0/nan
                    valid = (arr > 0) & np.isfinite(arr)
                    if not valid.any():
                        r["centroid_dist_km"] = None
                        r["mirova_vrp_header"] = float(arr[valid].sum()) if valid.any() else 0.0
                        r["category"] = "C"
                        continue
                    rows, cols = np.where(valid)
                    weights = arr[valid]
                    # weighted centroid
                    cy = float(np.average(rows, weights=weights))
                    cx = float(np.average(cols, weights=weights))
                    # transform to lat/lon
                    lon, lat = src.xy(cy, cx)
                    dist = haversine_km(VENT_LAT, VENT_LON, lat, lon)
                    dist_salar = haversine_km(SALAR_LAT, SALAR_LON, lat, lon)
                    r["centroid_lat"] = lat
                    r["centroid_lon"] = lon
                    r["centroid_dist_km"] = dist
                    r["centroid_dist_salar_km"] = dist_salar
                    r["mirova_vrp_header"] = float(weights.sum())
                    r["n_valid_pixels"] = int(valid.sum())
                    # tags description in header
                    tags = src.tags()
                    r["tif_tags_sample"] = {k: v for k, v in list(tags.items())[:5]}
                    if dist < 5.0:
                        r["category"] = "A"
                    elif dist > 10.0 or dist_salar < 30.0:
                        r["category"] = "B"
                    else:
                        r["category"] = "mixed"
            except Exception as e:
                r["centroid_dist_km"] = None
                r["category"] = "C"
                r["error"] = str(e)

    # Unmatched in_window -> Cat C
    for r in in_window:
        if not r.get("tif_match"):
            r["category"] = "C"
            r["centroid_dist_km"] = None

    # Tally
    cat_a = sum(1 for r in in_window if r["category"] == "A")
    cat_b = sum(1 for r in in_window if r["category"] == "B")
    cat_c = sum(1 for r in in_window if r["category"] == "C")
    cat_mix = sum(1 for r in in_window if r["category"] == "mixed")
    total = len(in_window)

    print(f"\n=== AUDIT RESULTS (in TIF archive window) ===")
    print(f"Total lost in window: {total}")
    print(f"  Cat A (TP real cráter, <5km): {cat_a} ({100*cat_a/max(total,1):.1f}%)")
    print(f"  Cat B (FP lejano, >10km o Salar): {cat_b} ({100*cat_b/max(total,1):.1f}%)")
    print(f"  Cat mixed (5-10km): {cat_mix} ({100*cat_mix/max(total,1):.1f}%)")
    print(f"  Cat C (sin TIF/no leíble): {cat_c} ({100*cat_c/max(total,1):.1f}%)")

    # Save JSON
    out = {
        "summary": {
            "s26_records": len(s26_recs),
            "s71_records": len(s71_recs),
            "lost_total": len(lost),
            "lost_outside_archive_window": len(lost) - total,
            "lost_in_archive_window": total,
            "cat_A_count": cat_a,
            "cat_B_count": cat_b,
            "cat_mixed_count": cat_mix,
            "cat_C_count": cat_c,
            "vent_lat": VENT_LAT,
            "vent_lon": VENT_LON,
            "archive_window_start": ARCHIVE_START.isoformat(),
            "archive_window_end": ARCHIVE_END.isoformat(),
        },
        "lost_in_window": [
            {k: v for k, v in r.items() if not k.startswith("_")} for r in in_window
        ],
    }
    out_path = ROOT / "audit_results.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nResults saved: {out_path}")

    # Print sample
    print(f"\n=== SAMPLE (first 10 in_window) ===")
    for r in in_window[:10]:
        print(f"  {r['datetime_utc']} {r['sensor']:18s} S26 vrp={r['s26_vrp_mw']:.2f}MW dist={r.get('s26_hotspot_dist_km')} class={r['s26_distance_class']} | cat={r['category']} centroid_dist_vent={r.get('centroid_dist_km')}")


if __name__ == "__main__":
    main()
