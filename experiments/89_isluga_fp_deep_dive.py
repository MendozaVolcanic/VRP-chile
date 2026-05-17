"""S47 Isluga deep dive: investigar 8 FPs categoria (a) en window 30d.

Lee 88_fps_distribution.json, filtra Isluga FP_a, agrega cross-check con
CSV MIROVA en +-30min (que hotspot reporto MIROVA si lo hizo), y calcula
patron espacial/temporal.
"""
from __future__ import annotations
import json
import sys
import io
import math
from pathlib import Path
from datetime import timedelta

import pandas as pd

if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * R * math.asin(math.sqrt(a))


def bearing(lat1, lon1, lat2, lon2):
    """Bearing in degrees, 0=N, 90=E, 180=S, 270=W."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1)*math.sin(p2) - math.sin(p1)*math.cos(p2)*math.cos(dl)
    b = math.degrees(math.atan2(y, x))
    return (b + 360) % 360


def bearing_label(b):
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    return dirs[round(b / 22.5) % 16]


def main():
    repo = Path(__file__).parent.parent
    fps = json.loads((repo / "experiments" / "88_fps_distribution.json").read_text(encoding="utf-8"))
    isluga_fps = [f for f in fps["fp_records"]
                  if f["vol"] == "Isluga" and f["category"] == "a_mirova_fp"]

    # Vent
    vent_lat, vent_lon = -19.15, -68.83

    # Load MIROVA CSV
    csv_path = repo / "01_05_2026_registro_vrp_consolidado.csv"
    df = pd.read_csv(csv_path)
    df["ts"] = pd.to_datetime(df["Fecha_Satelite_UTC"], errors="coerce", utc=True)
    df = df[df["Volcan"] == "Isluga"].dropna(subset=["ts"]).copy()

    tol = timedelta(minutes=30)

    print("=" * 90)
    print(f"ISLUGA FPs categoria (a) — total {len(isluga_fps)}")
    print(f"Vent ref: ({vent_lat}, {vent_lon}); inner_radius=5 km")
    print("=" * 90)
    print(f"{'#':<3}{'date':<22}{'sens':<10}{'lat':>10}{'lon':>10}{'d_km':>7}"
          f"{'bear':>6}{'vrp_mw':>9}{'npx':>5}")
    print("-" * 90)

    enriched = []
    for i, f in enumerate(isluga_fps, 1):
        lat, lon = f["lat"], f["lon"]
        d = haversine_km(vent_lat, vent_lon, lat, lon)
        b = bearing(vent_lat, vent_lon, lat, lon)
        bl = bearing_label(b)
        ts = pd.Timestamp(f["ts"])
        print(f"{i:<3}{str(ts)[:19]:<22}{f['sensor']:<10}{lat:>10.4f}"
              f"{lon:>10.4f}{d:>7.2f}{bl:>6}{f['vrp_mw']:>9.3f}"
              f"{f['n_pixels']:>5}")
        # cross-check MIROVA
        nearby = df[(df["ts"] - ts).abs() <= tol]
        mirova_info = []
        for _, m in nearby.iterrows():
            mirova_info.append({
                "ts": str(m["ts"]),
                "sensor": m["Sensor"],
                "tipo": m["Tipo_Registro"],
                "vrp": m.get("VRP_MW"),
                "lat": m.get("Lat_Hotspot"),
                "lon": m.get("Lon_Hotspot"),
            })
        enriched.append({**f, "dist_vent": d, "bearing": b, "bearing_label": bl,
                         "mirova_nearby": mirova_info})

    # Patron espacial
    print("\n" + "=" * 90)
    print("PATRON ESPACIAL")
    print("=" * 90)
    lats = [f["lat"] for f in isluga_fps]
    lons = [f["lon"] for f in isluga_fps]
    print(f"Lat: {min(lats):.4f} -> {max(lats):.4f}  (span {(max(lats)-min(lats))*111:.2f} km)")
    print(f"Lon: {min(lons):.4f} -> {max(lons):.4f}  (span {(max(lons)-min(lons))*105:.2f} km)")
    print(f"Centroide FPs: ({sum(lats)/len(lats):.4f}, {sum(lons)/len(lons):.4f})")
    bears = {}
    for f in enriched:
        bl = f["bearing_label"]
        bears[bl] = bears.get(bl, 0) + 1
    print(f"Bearings: {bears}")
    dists = [f["dist_vent"] for f in enriched]
    print(f"Dist al vent: min={min(dists):.2f} max={max(dists):.2f} "
          f"med={sorted(dists)[len(dists)//2]:.2f} km")

    # Patron temporal
    print("\n" + "=" * 90)
    print("PATRON TEMPORAL")
    print("=" * 90)
    hours = {}
    dates = {}
    for f in isluga_fps:
        ts = pd.Timestamp(f["ts"])
        h = ts.hour
        hours[h] = hours.get(h, 0) + 1
        d = str(ts.date())
        dates[d] = dates.get(d, 0) + 1
    print(f"Horas UTC: {sorted(hours.items())}")
    print(f"Fechas: {sorted(dates.items())}")

    # Cross-check MIROVA: que hotspot reporto MIROVA cuando marco FP
    print("\n" + "=" * 90)
    print("CROSS-CHECK MIROVA (+-30 min, mismo volcan)")
    print("=" * 90)
    for i, f in enumerate(enriched, 1):
        print(f"\n#{i} FP en {f['ts'][:19]} ({f['sensor']}) "
              f"lat={f['lat']:.4f} lon={f['lon']:.4f} d={f['dist_vent']:.2f}km")
        if not f["mirova_nearby"]:
            print("  (no MIROVA entries +-30min — categoria b en realidad?)")
        for m in f["mirova_nearby"]:
            mlat, mlon = m.get("lat"), m.get("lon")
            mdist = ""
            if mlat and mlon and not (pd.isna(mlat) or pd.isna(mlon)):
                try:
                    mdist = f" mirova_hotspot=({mlat:.4f},{mlon:.4f}) " \
                            f"d_to_our={haversine_km(f['lat'],f['lon'],mlat,mlon):.2f}km"
                except Exception:
                    pass
            print(f"  MIROVA {m['ts'][:19]} {m['sensor']:<10} {m['tipo']:<18} "
                  f"vrp={m['vrp']}{mdist}")

    out = repo / "experiments" / "89_isluga_fp_deep_dive.json"
    out.write_text(json.dumps(enriched, indent=2, default=str), encoding="utf-8")
    print(f"\nJSON: {out}")


if __name__ == "__main__":
    main()
