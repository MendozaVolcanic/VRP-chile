"""
78 — R2 pixel-level Puyehue lacolito 05:42

Compara pixels del TIF MIROVA (mirova-tif-archive) vs pixels reportados/descartados
por VRP-chile para el evento lacolito 2026-05-09 05:42:02 GMT.

Output: confirmación pixel-by-pixel del bug H8 + caracterización de qué pixels
ve MIROVA en el TIF.
"""
from __future__ import annotations
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path
import numpy as np
import tifffile

REPO_ROOT = Path(__file__).resolve().parent.parent
TIF = REPO_ROOT.parent.parent.parent.parent / "mirova-tif-archive" / "data" / "tif" / "PuyehueCordonCaulle" / "20260509_054202_VIIRS375.tif"

# Puyehue config
VOLCANO_LAT = -40.59
VOLCANO_LON = -72.117
VENT_LAT = -40.525499
VENT_LON = -72.146137  # del volcanoes.yaml
INNER_RADIUS_KM = 20

import math
def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1r, lat2r = math.radians(lat1), math.radians(lat2)
    dlat = lat2r - lat1r
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(lat1r)*math.cos(lat2r)*math.sin(dlon/2)**2
    return 2 * R * math.asin(math.sqrt(a))


def main():
    print(f"=== TIF: {TIF}")
    print(f"=== Volcano center: ({VOLCANO_LAT}, {VOLCANO_LON})")
    print(f"=== Vent: ({VENT_LAT}, {VENT_LON})")
    print()

    # Read TIF
    with tifffile.TiffFile(TIF) as tif:
        page = tif.pages[0]
        tp = page.tags["ModelTiepointTag"].value  # (i, j, k, x, y, z)
        sc = page.tags["ModelPixelScaleTag"].value  # (sx, sy, sz)
        arr = page.asarray()
    H, W = arr.shape
    i0, j0, _, x0, y0, _ = tp[:6]
    sx, sy, _ = sc

    def pixel_to_lonlat(j, i):
        lon = x0 + (j - i0) * sx
        lat = y0 - (i - j0) * sy
        return lon, lat

    print(f"=== TIF shape: {arr.shape}")
    print(f"=== Geo: pixel(0,0) = ({x0:.4f}, {y0:.4f}), scale = ({sx:.6f}, {sy:.6f}) deg/px")
    print(f"=== bbox: lon [{x0:.4f}, {pixel_to_lonlat(W-1, 0)[0]:.4f}]  lat [{pixel_to_lonlat(0, H-1)[1]:.4f}, {y0:.4f}]")

    # Distance grid
    print("\\n=== Computing distance grid (vol center)...")
    dists = np.zeros_like(arr)
    for i in range(H):
        for j in range(W):
            lon, lat = pixel_to_lonlat(j, i)
            dists[i, j] = haversine_km(lat, lon, VOLCANO_LAT, VOLCANO_LON)
    print(f"  dist range: {dists.min():.2f} – {dists.max():.2f} km")

    # Mask de pixels válidos (no NaN)
    valid_mask = ~np.isnan(arr)
    print(f"\\n=== valid pixels: {valid_mask.sum()} / {arr.size}")

    # Estadísticas por anillo de distancia
    print("\\n=== Pixels por anillo de distancia ===")
    print(f"{'ring (km)':<15} {'n_pixels':>10} {'min':>8} {'max':>8} {'mean':>8} {'std':>8}")
    rings = [(0, 2), (2, 5), (5, 8), (8, 12), (12, 20), (20, 25), (25, 30), (30, 50)]
    for lo, hi in rings:
        m = valid_mask & (dists >= lo) & (dists < hi)
        if m.sum() == 0:
            continue
        v = arr[m]
        print(f"{lo}-{hi:<15} {m.sum():>10} {v.min():>8.4f} {v.max():>8.4f} {v.mean():>8.4f} {v.std():>8.4f}")

    # Top 30 pixels por valor
    print("\\n=== TOP 30 pixels (más altos en TIF) — coords + dist ===")
    flat = arr.flatten()
    valid_flat = np.where(np.isnan(flat), -np.inf, flat)
    top30 = np.argsort(valid_flat)[-30:][::-1]
    print(f"{'rank':<5} {'i':>4} {'j':>4} {'value':>10} {'lon':>10} {'lat':>10} {'dist (km)':>10}")
    for rank, idx in enumerate(top30, 1):
        i, j = np.unravel_index(idx, arr.shape)
        lon, lat = pixel_to_lonlat(j, i)
        d = dists[i, j]
        print(f"{rank:<5} {i:>4} {j:>4} {arr[i,j]:>10.4f} {lon:>10.4f} {lat:>10.4f} {d:>10.2f}")

    # Pixels en zona lacolito (5-10 km)
    print("\\n=== PIXELS EN ZONA LACOLITO (5-10 km del centro) ===")
    lacolito_mask = valid_mask & (dists >= 5) & (dists <= 10)
    if lacolito_mask.sum() == 0:
        print("  ZERO pixels in lacolito ring!")
    else:
        lac_vals = arr[lacolito_mask]
        print(f"  {lacolito_mask.sum()} pixels")
        print(f"  values: min={lac_vals.min():.4f} max={lac_vals.max():.4f} mean={lac_vals.mean():.4f}")
        # Top 10 hottest in lacolito ring
        ii_lac, jj_lac = np.where(lacolito_mask)
        vals_lac = arr[ii_lac, jj_lac]
        top_idx = np.argsort(vals_lac)[-10:][::-1]
        print("  Top 10 más calientes en zona lacolito:")
        for k in top_idx:
            i, j = ii_lac[k], jj_lac[k]
            lon, lat = pixel_to_lonlat(j, i)
            print(f"    val={arr[i,j]:.4f} ({lat:.4f}, {lon:.4f}) dist={dists[i,j]:.2f}km")

    # Comparar con pixels descartados por VRP-chile
    p_vrp_record = REPO_ROOT / "data" / "mirova_equivalent" / "PuyehueCordonCaulle.json"
    with open(p_vrp_record) as f: data = json.load(f)
    recs = data if isinstance(data, list) else data.get("records", [])
    target = next((r for r in recs if r.get("datetime_utc") == "2026-05-09 05:42" and r.get("sensor") == "VIIRS_NOAA21"), None)
    if target is None:
        print("\\n=== VRP-chile record 05:42 NOAA21 NOT FOUND")
        return
    dp = target.get("discarded_anomaly_pixels", [])
    print(f"\\n=== VRP-chile DISCARDED pixels: {len(dp)}")
    near = [p for p in dp if 5 <= p.get("dist_km", 0) <= 10]
    print(f"  en zona lacolito (5-10 km): {len(near)}")
    if near:
        print(f"  ejemplos:")
        for p in sorted(near, key=lambda x: -x.get("vrp_mw", 0))[:8]:
            # Find this pixel in TIF
            lat, lon = p["lat"], p["lon"]
            # nearest tif pixel
            j_t = int(round((lon - x0) / sx + i0))
            i_t = int(round((y0 - lat) / sy + j0))
            tif_val = arr[i_t, j_t] if 0 <= i_t < H and 0 <= j_t < W else None
            print(f"    VRP-chile: lat={lat:.4f} lon={lon:.4f} dist={p['dist_km']:.2f} bt={p['bt_k']:.1f} vrp={p['vrp_mw']:.4f} → TIF[{i_t},{j_t}]={tif_val}")

    print("\\n=== CONCLUSIÓN ===")
    print("Si valid_pixels en zona lacolito tienen valores > background, MIROVA pudo detectarlos.")
    print("Si VRP-chile descartó pixels en esa zona pero TIF muestra valores claros,")
    print("entonces el bug H8 es la causa de la pérdida.")


if __name__ == "__main__":
    main()
