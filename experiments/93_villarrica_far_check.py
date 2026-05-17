"""S49 Villarrica far cases investigation - 6 outliers VIIRS-I 375m window 30d."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parents[1]
VOLC_JSON = REPO / "data" / "mirova_equivalent" / "Villarrica.json"
MIROVA_CSV = REPO / "data" / "mirova_reference" / "mirova_v1_snapshot" / "registro_vrp_consolidado.csv"

VENT_LAT = -39.4196
VENT_LON = -71.9395

TARGETS = [
    ("2026-04-24", "06:18", "NOAA20"),
    ("2026-05-03", "06:30", "SNPP"),
    ("2026-05-04", "05:36", "NOAA21"),
    ("2026-05-12", "07:00", "SNPP"),
    ("2026-05-14", "05:00", "NOAA20"),
    ("2026-05-14", "06:42", "NOAA20"),
]


def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def bearing(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    y = math.sin(dl) * math.cos(p2)
    x = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    br = math.degrees(math.atan2(y, x))
    return (br + 360) % 360


def compass(brg):
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    return dirs[int((brg + 11.25) / 22.5) % 16]


def geo_label(lat, lon, brg, dist):
    # Villarrica regional context
    # Lago Villarrica: ~10-25 km N (centroid ~-39.27, -72.10)
    # Glaciar/cono S
    # Volcan Quetrupillán al E ~7km, Lanin más al E
    # Valles agricolas N, NE, E (Pucón, Curarrehue)
    # Lago Calafquén al SW
    c = compass(brg)
    if c in ("N", "NNE", "NNW") and dist > 15:
        return f"{c} - probable Lago Villarrica / valle Pucón"
    if c in ("NE", "ENE") and dist > 10:
        return f"{c} - valle agrícola Pucón/Curarrehue"
    if c in ("E", "ESE") and 5 < dist < 12:
        return f"{c} - cono Quetrupillán"
    if c in ("SW", "WSW", "S", "SSW") and dist > 10:
        return f"{c} - Lago Calafquén / glaciar S"
    return f"{c} - region s/clasificar"


def main():
    data = json.loads(VOLC_JSON.read_text(encoding="utf-8"))
    records = data.get("records", data) if isinstance(data, dict) else data
    if isinstance(records, dict):
        records = records.get("records", [])

    # Index records by date+time
    matches = []
    for rec in records:
        ts = rec.get("datetime_utc", "")
        if not ts:
            continue
        for d, t, sat in TARGETS:
            if ts.startswith(d) and ts[11:16] == t:
                matches.append((d, t, sat, rec))
                break

    print(f"Found {len(matches)} matching records (target 6)\n")

    rows = []
    for d, t, sat, rec in matches:
        pc = rec.get("primary_cluster") or {}
        clat = pc.get("centroid_lat") or pc.get("lat") or rec.get("final_hotspot_lat")
        clon = pc.get("centroid_lon") or pc.get("lon") or rec.get("final_hotspot_lon")
        if clat is None or clon is None:
            # Try hotspot
            clat = rec.get("hotspot_lat")
            clon = rec.get("hotspot_lon")
        if clat is None:
            print(f"NO COORDS: {d} {t} {sat}")
            print(f"  keys: {list(rec.keys())[:20]}")
            print(f"  pc keys: {list(pc.keys()) if pc else None}")
            continue
        dist = haversine(VENT_LAT, VENT_LON, clat, clon)
        brg = bearing(VENT_LAT, VENT_LON, clat, clon)
        label = geo_label(clat, clon, brg, dist)
        vrp = pc.get("vrp_mw") or rec.get("vrp_mw") or rec.get("pc_vrp_mw")
        npx = pc.get("n_pixels") or rec.get("n_anomalous_pixels")
        rows.append({
            "date": d, "time": t, "sat": sat,
            "clat": round(clat, 4), "clon": round(clon, 4),
            "dist_km": round(dist, 1), "bearing_deg": round(brg),
            "compass": compass(brg), "geo": label,
            "vrp_mw": round(vrp, 2) if vrp else None, "npx": npx,
        })

    df = pd.DataFrame(rows)
    print("=== TABLA 6 CASOS FAR ===")
    print(df.to_string(index=False))
    print()

    # Recurrence check
    if len(df):
        print("=== RECURRENCIA GEOGRAFICA (clat,clon rounded 0.02 deg ~2km) ===")
        df["geo_bin"] = df.apply(lambda r: f"({round(r.clat/0.02)*0.02:.2f},{round(r.clon/0.02)*0.02:.2f})", axis=1)
        print(df.groupby("geo_bin").size().to_string())
        print()

    # MIROVA CSV cross-check
    print("=== MIROVA CSV — Villarrica fechas target ===")
    mv = pd.read_csv(MIROVA_CSV, low_memory=False)
    mv = mv[mv["Volcan"].str.lower() == "villarrica"]
    target_dates = sorted({d for d, _, _ in TARGETS})
    for td in target_dates:
        hit = mv[mv["Fecha_Satelite_UTC"].astype(str).str.startswith(td)]
        print(f"\n  --- {td}: {len(hit)} filas MIROVA Villarrica ---")
        if len(hit):
            print(hit[["Fecha_Satelite_UTC", "Sensor", "VRP_MW", "Distancia_km", "Tipo_Registro", "Clasificacion Mirova"]].to_string(index=False))


if __name__ == "__main__":
    main()
