"""S50-PCC-AB: validar fix mirova_center PCC (PR #47) pre vs post-merge.

Merge time: 2026-05-17 02:01 UTC (commit 3d69649).
Cutoff: cualquier record con datetime_utc procesado por NRT cron DESPUES
de 02:01 UTC del 2026-05-17 ya tiene el fix activo.

Lacolito target: -40.582, -72.131
Cone (legacy vent): -40.59, -72.117 aprox.
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PCC_JSON = REPO / "data" / "mirova_equivalent" / "PuyehueCordonCaulle.json"

MERGE_UTC = datetime(2026, 5, 17, 2, 1, 22, tzinfo=timezone.utc)
LACOLITO = (-40.582, -72.131)
CONE = (-40.59, -72.117)


def hav(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def parse_dt(s):
    if not s:
        return None
    s = s.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def main():
    data = json.loads(PCC_JSON.read_text(encoding="utf-8"))
    records = data.get("records", data) if isinstance(data, dict) else data
    print(f"Total records PCC: {len(records)}")

    # extract: datetime, sensor, primary_cluster centroid, record processing time approx
    rows = []
    for r in records:
        dt = parse_dt(r.get("datetime_utc"))
        if dt is None:
            continue
        sensor = r.get("sensor", "?")
        pc = r.get("primary_cluster") or {}
        clat = pc.get("centroid_lat")
        clon = pc.get("centroid_lon")
        cdist = pc.get("centroid_dist_km")
        vrp = pc.get("vrp_mw")
        rows.append({
            "dt": dt,
            "sensor": sensor,
            "clat": clat,
            "clon": clon,
            "cdist_km": cdist,
            "vrp_mw": vrp,
            "dist_to_lacolito": hav(clat, clon, *LACOLITO) if (clat and clon) else None,
            "dist_to_cone": hav(clat, clon, *CONE) if (clat and clon) else None,
        })
    rows.sort(key=lambda x: x["dt"])

    # Use scene datetime as proxy for pre/post fix
    # Reality: NRT cron 02:00 UTC was BEFORE merge (01:30). Next cron ~04:00 UTC post-merge.
    # But datetime_utc is the satellite scene time, not the processing time.
    # The only reliable signal: scene datetime >= MERGE_UTC implies processed post-fix.
    pre = [r for r in rows if r["dt"] < MERGE_UTC]
    post = [r for r in rows if r["dt"] >= MERGE_UTC]

    print(f"\nScene datetime_utc < 2026-05-17 02:01 UTC (pre-merge): {len(pre)}")
    print(f"Scene datetime_utc >= 2026-05-17 02:01 UTC (post-merge candidate): {len(post)}")

    # Distribution of cluster distance for last 20 pre-merge (sanity)
    print("\n=== LAST 10 PRE-MERGE RECORDS (legacy cone-anchored) ===")
    print(f"{'datetime_utc':<22} {'sensor':<10} {'clat':>8} {'clon':>9} {'d_cone':>7} {'d_laco':>7} {'vrp':>7}")
    for r in pre[-10:]:
        print(f"{r['dt'].isoformat():<22} {r['sensor']:<10} "
              f"{(r['clat'] or 0):>8.3f} {(r['clon'] or 0):>9.3f} "
              f"{(r['dist_to_cone'] or -1):>7.2f} {(r['dist_to_lacolito'] or -1):>7.2f} "
              f"{(r['vrp_mw'] or 0):>7.2f}")

    print("\n=== POST-MERGE RECORDS (expected lacolito-anchored) ===")
    if not post:
        print("(empty — NRT cron has NOT run a scene after 02:01 UTC yet, or no PCC scene captured)")
    else:
        print(f"{'datetime_utc':<22} {'sensor':<10} {'clat':>8} {'clon':>9} {'d_cone':>7} {'d_laco':>7} {'vrp':>7}")
        for r in post[:20]:
            print(f"{r['dt'].isoformat():<22} {r['sensor']:<10} "
                  f"{(r['clat'] or 0):>8.3f} {(r['clon'] or 0):>9.3f} "
                  f"{(r['dist_to_cone'] or -1):>7.2f} {(r['dist_to_lacolito'] or -1):>7.2f} "
                  f"{(r['vrp_mw'] or 0):>7.2f}")

    # Aggregate stats
    def stats(rows_):
        ds_laco = [r["dist_to_lacolito"] for r in rows_ if r["dist_to_lacolito"] is not None]
        ds_cone = [r["dist_to_cone"] for r in rows_ if r["dist_to_cone"] is not None]
        if not ds_laco:
            return None
        ds_laco.sort()
        n = len(ds_laco)
        med = ds_laco[n // 2]
        med_cone = sorted(ds_cone)[n // 2] if ds_cone else None
        return {"n": n, "median_d_laco_km": med, "median_d_cone_km": med_cone,
                "min_d_laco": min(ds_laco), "max_d_laco": max(ds_laco)}

    print("\n=== AGG STATS ===")
    print("Pre-merge:", stats(pre))
    print("Post-merge:", stats(post))

    # Last 30 days breakdown
    cutoff = datetime(2026, 4, 17, tzinfo=timezone.utc)
    recent_pre = [r for r in pre if r["dt"] >= cutoff]
    print(f"\nPre-merge last 30d (n={len(recent_pre)}):", stats(recent_pre))


if __name__ == "__main__":
    main()
