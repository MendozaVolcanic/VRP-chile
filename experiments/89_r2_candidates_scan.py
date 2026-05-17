"""S47 R2 expansion: escanear TIFs vs records VRP-chile y proponer casos.

Output:
  1) tabla TIFs por volcan+sensor con (min_date, max_date, count)
  2) candidatos donde TIF tiene match record (±5 min) y centroide ≤ 5 km
  3) propuesta R2_CASES Python snippet
"""
from __future__ import annotations
import sys, io, json, math
from pathlib import Path
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO_ROOT = Path(__file__).resolve().parent.parent
TIF_ARCHIVE_ROOT = REPO_ROOT.parent.parent.parent.parent / "mirova-tif-archive"
TIF_INDEX = TIF_ARCHIVE_ROOT / "index.csv"

SENSOR_VRP_PREFIXES = {
    "MODIS":    ("MODIS_AQUA", "MODIS_TERRA"),
    "VIIRS750": ("VIIRS_SNPP_750", "VIIRS_NOAA20_750", "VIIRS_NOAA21_750"),
    "VIIRS375": ("VIIRS_SNPP", "VIIRS_NOAA20", "VIIRS_NOAA21"),
}


def ts_from_filename(p):
    try:
        stem = Path(str(p)).stem
        ds, ts, _ = stem.split("_", 2)
        return pd.Timestamp(f"{ds[:4]}-{ds[4:6]}-{ds[6:]} {ts[:2]}:{ts[2:4]}:{ts[4:]}", tz="UTC")
    except Exception:
        return pd.NaT


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def read_tif_pixels(tif_path):
    import numpy as np
    import tifffile as tf
    with tf.TiffFile(str(tif_path)) as tif:
        page = tif.pages[0]
        tp = page.tags["ModelTiepointTag"].value
        sc = page.tags["ModelPixelScaleTag"].value
        arr = page.asarray()
    i0, j0, _, x0, y0, _ = tp[:6]
    sx, sy, _ = sc
    valid = (arr > 0) & np.isfinite(arr)
    out = []
    for i, j in zip(*valid.nonzero()):
        lon = x0 + (int(j) - i0) * sx
        lat = y0 - (int(i) - j0) * sy
        out.append((float(lat), float(lon), float(arr[int(i), int(j)])))
    return out


def weighted_centroid(pixels):
    total = sum(p[2] for p in pixels)
    if total <= 0:
        return None
    lat = sum(p[0] * p[2] for p in pixels) / total
    lon = sum(p[1] * p[2] for p in pixels) / total
    return (lat, lon, total)


def load_records(volcano):
    path = REPO_ROOT / "data" / "mirova_equivalent" / f"{volcano}.json"
    if not path.exists():
        return []
    with open(path) as f:
        data = json.load(f)
    return data if isinstance(data, list) else data.get("records", [])


def find_record(records, sensor_label, target_dt, tol_min=5):
    prefixes = SENSOR_VRP_PREFIXES.get(sensor_label, ())
    require_no_750 = (sensor_label == "VIIRS375")
    best = None
    best_diff = pd.Timedelta(minutes=tol_min)
    if target_dt.tz is None:
        target_dt = target_dt.tz_localize("UTC")
    for r in records:
        s = r.get("sensor", "")
        if not any(s.startswith(p) for p in prefixes):
            continue
        if require_no_750 and s.endswith("_750"):
            continue
        ts = r.get("datetime_utc", "")
        if not ts:
            continue
        try:
            rdt = pd.Timestamp(ts)
            if rdt.tz is None:
                rdt = rdt.tz_localize("UTC")
        except Exception:
            continue
        diff = abs(rdt - target_dt)
        if diff <= best_diff:
            best_diff = diff
            best = r
    return best


def main():
    idx = pd.read_csv(TIF_INDEX)
    idx["ts"] = idx["tif_path"].apply(ts_from_filename)
    idx = idx.dropna(subset=["ts"])

    # 1) Tabla por volcan+sensor
    print("=" * 80)
    print("(1) TIFs por volcan+sensor")
    print("=" * 80)
    summary = idx.groupby(["volcano", "sensor"]).agg(
        count=("ts", "size"),
        min_date=("ts", "min"),
        max_date=("ts", "max"),
    ).reset_index()
    print(summary.to_string(index=False))

    # 2) Scan candidatos
    print()
    print("=" * 80)
    print("(2) Candidatos con record match + centroid ≤ 5 km")
    print("=" * 80)

    cache_records = {}
    candidates = []
    for _, row in idx.iterrows():
        volcano = row["volcano"]
        sensor = row["sensor"]
        if sensor not in SENSOR_VRP_PREFIXES:
            continue
        if volcano not in cache_records:
            cache_records[volcano] = load_records(volcano)
        recs = cache_records[volcano]
        if not recs:
            continue
        granule_time = row["ts"]
        rec = find_record(recs, sensor, granule_time, tol_min=5)
        if rec is None:
            continue
        tif_path = TIF_ARCHIVE_ROOT / row["tif_path"]
        if not tif_path.exists():
            continue
        try:
            pixels = read_tif_pixels(tif_path)
        except Exception as e:
            continue
        if not pixels:
            continue
        cen = weighted_centroid(pixels)
        if cen is None:
            continue
        pc = rec.get("primary_cluster") or {}
        vrp_lat = pc.get("centroid_lat") or rec.get("final_hotspot_lat") or rec.get("hotspot_lat")
        vrp_lon = pc.get("centroid_lon") or rec.get("final_hotspot_lon") or rec.get("hotspot_lon")
        if vrp_lat is None or vrp_lon is None:
            continue
        dist = haversine_km(cen[0], cen[1], vrp_lat, vrp_lon)
        candidates.append({
            "volcano": volcano,
            "sensor": sensor,
            "granule_ts": granule_time.strftime("%Y-%m-%d %H:%M"),
            "tif_centroid": (round(cen[0], 4), round(cen[1], 4)),
            "tif_vrp_sum": round(cen[2], 3),
            "tif_pixels": len(pixels),
            "vrp_centroid": (round(vrp_lat, 4), round(vrp_lon, 4)),
            "pc_vrp_mw": round((pc.get("vrp_mw") or rec.get("vrp_mw") or 0), 3),
            "dist_km": round(dist, 3),
            "rec_dt": rec.get("datetime_utc"),
        })

    cdf = pd.DataFrame(candidates)
    if cdf.empty:
        print("Sin candidatos!")
        return
    cdf = cdf.sort_values(["volcano", "sensor", "granule_ts"])
    print(cdf.to_string(index=False))

    # Pasa o falla assert: dist <= max(2, dist+1) -> siempre true
    # Necesitamos elegir representativos. Filtrar dist <= 10 km (sanity)
    valid = cdf[cdf["dist_km"] <= 10.0].copy()
    print()
    print("=" * 80)
    print(f"(2b) Candidatos válidos (dist ≤ 10 km): {len(valid)}/{len(cdf)}")
    print("=" * 80)

    drift = cdf[cdf["dist_km"] > 10.0]
    if not drift.empty:
        print()
        print("=" * 80)
        print(f"(3) DRIFT POTENCIAL (dist > 10 km, {len(drift)} casos)")
        print("=" * 80)
        print(drift.to_string(index=False))

    # 3) Proponer 3-5 casos: diversidad volcano+sensor
    print()
    print("=" * 80)
    print("(4) Propuesta R2_CASES (diversidad volcano+sensor)")
    print("=" * 80)
    seen = set()
    picks = []
    # Ordenar por dist ascendente, tomar primeros por (volcano,sensor) único
    for _, r in valid.sort_values("dist_km").iterrows():
        key = (r["volcano"], r["sensor"])
        if key in seen:
            continue
        seen.add(key)
        picks.append(r)
        if len(picks) >= 8:
            break

    print()
    print("R2_CASES_NEW = [")
    for r in picks:
        exp_dist = max(0.5, round(r["dist_km"], 2))
        exp_vrp = r["pc_vrp_mw"] if r["pc_vrp_mw"] > 0 else round(r["tif_vrp_sum"], 2)
        hipo = f"{r['volcano']} {r['sensor']} {r['granule_ts']}"
        print(f"    (\"{r['volcano']}\", \"{r['sensor']}\", \"{r['granule_ts']}\", "
              f"{exp_dist}, {exp_vrp}, \"{hipo}\"),")
    print("]")

    # Persist for review
    out = REPO_ROOT / "experiments" / "89_r2_candidates_scan_result.csv"
    cdf.to_csv(out, index=False)
    print(f"\nFull candidate list → {out}")


if __name__ == "__main__":
    main()
