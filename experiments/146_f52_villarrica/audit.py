"""F52 audit — Villarrica over-estimation root cause (S77).

Read-only. Cross-checks Villarrica.json detections vs MIROVA NRT
consolidated CSV, separates MATCHED vs UNMATCHED, and computes
spatial/thermal diagnostics to discriminate H1-H4.

Window: >= 2026-05-17 (last 7 days @ S77).
Filters: distance_class=summit, primary_cluster.vrp_mw>0, pc.centroid_dist_km<=5.
"""
from __future__ import annotations
import csv
import json
import math
import sys
import io
from datetime import datetime, timedelta
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

ROOT = Path(__file__).resolve().parents[2]
JSON_PATH = ROOT / "data/mirova_equivalent/Villarrica.json"
CSV_PATH = ROOT / "latest_consolidado.csv"
OUT_PATH = Path(__file__).parent / "audit_result.json"

# Vent (yaml) and known Rinconada lava lake coords
VENT_LAT, VENT_LON = -39.420227, -71.939876
RINCONADA_LAT, RINCONADA_LON = -39.4197, -71.9387
# Lago Villarrica centroid (approx, from yaml exclude_zone)
LAGO_LAT, LAGO_LON = -39.27, -72.09

WINDOW_START = "2026-05-17"
SUMMIT_MAX_DIST_KM = 5.0  # inner_radius_km
TOL_MIN = 60


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def bearing_deg(lat1, lon1, lat2, lon2):
    """Bearing from (lat1,lon1) toward (lat2,lon2), degrees from N clockwise."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    x = math.sin(dl) * math.cos(p2)
    y = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def parse_iso(s):
    # "2026-05-17 02:40"
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise ValueError(s)


def sensor_bucket(s):
    if not s:
        return None
    s = s.upper()
    if "MODIS" in s:
        return "MODIS"
    if "VIIRS" in s or "VJ" in s or "VNP" in s:
        return "VIIRS"
    return s


# Load MIROVA NRT refs for Villarrica
mirova_refs = []
with open(CSV_PATH, encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if row["Volcan"].strip().lower() != "villarrica":
            continue
        try:
            vrp = float(row.get("VRP_MW", 0) or 0)
        except ValueError:
            vrp = 0.0
        if vrp <= 0:
            continue
        try:
            dt = parse_iso(row["Fecha_Satelite_UTC"])
        except Exception:
            continue
        if dt < parse_iso(f"{WINDOW_START} 00:00"):
            continue
        mirova_refs.append({
            "dt": dt,
            "sensor": sensor_bucket(row.get("Sensor")),
            "vrp_mw": vrp,
        })

print(f"MIROVA NRT refs Villarrica >= {WINDOW_START}: {len(mirova_refs)}")

# Load our records
data = json.load(open(JSON_PATH, encoding="utf-8"))
recs_all = data["records"]
recs = []
for r in recs_all:
    dt_s = r.get("datetime_utc", "")
    if dt_s < WINDOW_START:
        continue
    if r.get("distance_class") != "summit":
        continue
    pc = r.get("primary_cluster") or {}
    if (pc.get("vrp_mw") or 0) <= 0:
        continue
    if (pc.get("centroid_dist_km") or 999) > SUMMIT_MAX_DIST_KM:
        continue
    try:
        r["_dt"] = parse_iso(dt_s)
    except Exception:
        continue
    r["_sensor_bucket"] = sensor_bucket(r.get("sensor"))
    recs.append(r)

print(f"Our summit records (window, pc>0, pc_dist<=5km): {len(recs)}")


def match(ours):
    """Find best MIROVA NRT match within ±60 min same sensor bucket."""
    best = None
    best_dt = TOL_MIN + 1
    for m in mirova_refs:
        if m["sensor"] != ours["_sensor_bucket"]:
            continue
        dmin = abs((m["dt"] - ours["_dt"]).total_seconds()) / 60.0
        if dmin <= TOL_MIN and dmin < best_dt:
            best_dt = dmin
            best = m
    return best, best_dt


matched, unmatched = [], []
for r in recs:
    m, dmin = match(r)
    pc = r["primary_cluster"]
    clat, clon = pc.get("centroid_lat"), pc.get("centroid_lon")
    info = {
        "datetime_utc": r["datetime_utc"],
        "sensor": r["sensor"],
        "vrp_mw_total": r.get("vrp_mw"),
        "pc_vrp_mw": pc.get("vrp_mw"),
        "pc_n_pixels": pc.get("n_pixels"),
        "pc_centroid_lat": clat,
        "pc_centroid_lon": clon,
        "pc_centroid_dist_km_yaml": pc.get("centroid_dist_km"),
        "dist_to_rinconada_km": haversine_km(clat, clon, RINCONADA_LAT, RINCONADA_LON) if clat else None,
        "bearing_from_vent_deg": bearing_deg(VENT_LAT, VENT_LON, clat, clon) if clat else None,
        "dist_to_lago_km": haversine_km(clat, clon, LAGO_LAT, LAGO_LON) if clat else None,
        "t_bg_k": r.get("t_bg_k"),
        "t_max_k": r.get("t_max_k"),
        "diag_sigma_bg_k": r.get("diag_sigma_bg_k"),
        "diag_eff_threshold_k": r.get("diag_eff_threshold_k"),
        "n_anomalous_pixels": r.get("n_anomalous_pixels"),
    }
    if m:
        info["mirova_vrp_mw"] = m["vrp_mw"]
        info["dt_diff_min"] = round(dmin, 1)
        info["ratio_ours_over_mirova"] = (
            (pc.get("vrp_mw") or 0) / m["vrp_mw"] if m["vrp_mw"] > 0 else None
        )
        matched.append(info)
    else:
        unmatched.append(info)


def median(xs):
    xs = sorted([x for x in xs if x is not None])
    if not xs:
        return None
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def summary(items, label):
    s = {
        "label": label,
        "n": len(items),
        "median_pc_vrp_mw": median([i["pc_vrp_mw"] for i in items]),
        "median_pc_n_pixels": median([i["pc_n_pixels"] for i in items]),
        "median_pc_dist_to_vent_km": median([i["pc_centroid_dist_km_yaml"] for i in items]),
        "median_pc_dist_to_rinconada_km": median([i["dist_to_rinconada_km"] for i in items]),
        "median_t_bg_k": median([i["t_bg_k"] for i in items]),
        "median_t_max_k": median([i["t_max_k"] for i in items]),
        "median_sigma_bg_k": median([i["diag_sigma_bg_k"] for i in items]),
    }
    return s


# Bearing buckets for UNMATCHED (toward lago = N to NW: bearing 270-360 or 0-30 if lago centroid -39.27,-72.09)
# Lago is ~12-15 km NW of vent. Compute real bearing
brg_lago = bearing_deg(VENT_LAT, VENT_LON, LAGO_LAT, LAGO_LON)
print(f"\nBearing vent->lago_centroid: {brg_lago:.1f} deg ({haversine_km(VENT_LAT,VENT_LON,LAGO_LAT,LAGO_LON):.1f} km)")

# Direction buckets
def bucket_dir(brg):
    if brg is None:
        return "unknown"
    # Lago lies NW (~315 deg). Bucket lateral toward lago.
    if 280 <= brg <= 360 or 0 <= brg <= 20:
        return "toward_lago_NW_N"
    if 20 < brg < 110:
        return "E_NE_SE"
    if 110 <= brg <= 200:
        return "S_SW"
    return "W_SW"


dir_buckets_unmatched = {}
for u in unmatched:
    b = bucket_dir(u["bearing_from_vent_deg"])
    dir_buckets_unmatched.setdefault(b, []).append(u)

# Distance buckets for UNMATCHED (from Rinconada)
dist_buckets_unmatched = {"<1km": [], "1-3km": [], "3-5km": []}
for u in unmatched:
    d = u["dist_to_rinconada_km"]
    if d is None:
        continue
    if d < 1:
        dist_buckets_unmatched["<1km"].append(u)
    elif d < 3:
        dist_buckets_unmatched["1-3km"].append(u)
    else:
        dist_buckets_unmatched["3-5km"].append(u)

out = {
    "window_start_utc": WINDOW_START,
    "vent_yaml": {"lat": VENT_LAT, "lon": VENT_LON},
    "rinconada_known": {"lat": RINCONADA_LAT, "lon": RINCONADA_LON},
    "vent_yaml_dist_to_rinconada_km": haversine_km(VENT_LAT, VENT_LON, RINCONADA_LAT, RINCONADA_LON),
    "n_our_summit_records": len(recs),
    "n_mirova_refs_window": len(mirova_refs),
    "n_matched": len(matched),
    "n_unmatched": len(unmatched),
    "summary_matched": summary(matched, "MATCHED"),
    "summary_unmatched": summary(unmatched, "UNMATCHED"),
    "matched_ratios_median": median([m.get("ratio_ours_over_mirova") for m in matched]),
    "bearing_vent_to_lago_deg": brg_lago,
    "dist_vent_to_lago_km": haversine_km(VENT_LAT, VENT_LON, LAGO_LAT, LAGO_LON),
    "unmatched_dir_buckets": {k: len(v) for k, v in dir_buckets_unmatched.items()},
    "unmatched_dist_buckets_from_rinconada": {k: len(v) for k, v in dist_buckets_unmatched.items()},
    "matched_records": matched,
    "unmatched_records": unmatched,
}

print("\n=== SUMMARY ===")
print(f"Vent yaml -> Rinconada distance: {out['vent_yaml_dist_to_rinconada_km']*1000:.0f} m (H2 verdict)")
print(f"Matched: {len(matched)}  Unmatched: {len(unmatched)}")
print(f"Matched ratio ours/MIROVA median: {out['matched_ratios_median']}")
print(f"Unmatched dir buckets: {out['unmatched_dir_buckets']}")
print(f"Unmatched dist-from-Rinconada buckets: {out['unmatched_dist_buckets_from_rinconada']}")
print(f"\nMATCHED summary: {json.dumps(out['summary_matched'], indent=2)}")
print(f"UNMATCHED summary: {json.dumps(out['summary_unmatched'], indent=2)}")

OUT_PATH.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
print(f"\nWrote {OUT_PATH}")
