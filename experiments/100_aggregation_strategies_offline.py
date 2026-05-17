"""S55 — A/B offline 4 estrategias agregacion vs 5 casos paradigmaticos MIROVA Villarrica.

Hipótesis (S54): pc.vrp_mw infla 12-84x vs MIROVA porque agrupa 60-90 pixels
conectados sum total. MIROVA reporta menos magnitud. ¿Cuál estrategia
agregación replica MIROVA?

4 estrategias probadas offline (usando anomaly_pixels + diag_t_bg_i04):
1. top_pixel: solo pixel mas caliente dentro de 2km del centroide pc
2. eq16_two_component: Eq.16 Coppola 2024 con T_e=1000K sobre top pixel
3. threshold_strict: sum pixels con vrp_individual > 0.05 MW dentro de 2km
4. summit_radius_filter: sum pixels dentro de 1km del centroide pc

Sin reproc (5 min vs 30 min Github Actions).
"""
from __future__ import annotations
import json
import math
import io
import sys

if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from pipeline.vrp_regimes import compute_vrp_lava_lake_eq16

MIROVA_REFS = [
    ("2026-05-11 06:00", "VIIRS_NOAA20", 0.31),
    ("2026-05-14 05:48", "VIIRS_NOAA21", 0.31),
    ("2026-04-09 06:00", "VIIRS_NOAA20", 0.11),
    ("2026-03-08 06:00", "VIIRS_NOAA20", 0.21),
    ("2026-02-26 05:42", "VIIRS_NOAA20", 0.12),
]


def hav(la1, lo1, la2, lo2):
    R = 6371.0
    p1, p2 = math.radians(la1), math.radians(la2)
    dp = math.radians(la2 - la1)
    dl = math.radians(lo2 - lo1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * R * math.asin(math.sqrt(a))


def strategy_top_pixel(record, max_dist_km=2.0):
    """Estrategia 1: top-1 pixel mas caliente dentro de max_dist_km del centroide pc."""
    pc = record.get("primary_cluster") or {}
    clat, clon = pc.get("centroid_lat"), pc.get("centroid_lon")
    if clat is None:
        return None
    ap = record.get("anomaly_pixels", []) or []
    candidates = [p for p in ap if hav(p["lat"], p["lon"], clat, clon) <= max_dist_km]
    if not candidates:
        return 0.0
    return max(p.get("vrp_mw", 0) for p in candidates)


def strategy_eq16(record, max_dist_km=2.0):
    """Estrategia 2: Eq.16 R2 con T_e=1000K aplicado al pixel mas caliente."""
    pc = record.get("primary_cluster") or {}
    clat, clon = pc.get("centroid_lat"), pc.get("centroid_lon")
    if clat is None:
        return None
    ap = record.get("anomaly_pixels", []) or []
    candidates = [p for p in ap if hav(p["lat"], p["lon"], clat, clon) <= max_dist_km]
    if not candidates:
        return 0.0
    top = max(candidates, key=lambda p: p.get("bt_k", 0))
    t_bg = record.get("t_bg_k") or record.get("diag_t_bg_i04") or 280.0
    result = compute_vrp_lava_lake_eq16(
        bt_hot_k=top["bt_k"],
        bt_bg_k=t_bg,
        t_bk_k=t_bg,
    )
    return result["vrp_mw"]


def strategy_threshold_strict(record, max_dist_km=2.0, vrp_min=0.05):
    """Estrategia 3: sum pixels con vrp_individual > vrp_min dentro max_dist_km."""
    pc = record.get("primary_cluster") or {}
    clat, clon = pc.get("centroid_lat"), pc.get("centroid_lon")
    if clat is None:
        return None
    ap = record.get("anomaly_pixels", []) or []
    candidates = [p for p in ap
                  if hav(p["lat"], p["lon"], clat, clon) <= max_dist_km
                  and p.get("vrp_mw", 0) > vrp_min]
    return sum(p.get("vrp_mw", 0) for p in candidates)


def strategy_summit_radius(record, radius_km=1.0):
    """Estrategia 4: sum pixels dentro de radius_km del centroide pc."""
    pc = record.get("primary_cluster") or {}
    clat, clon = pc.get("centroid_lat"), pc.get("centroid_lon")
    if clat is None:
        return None
    ap = record.get("anomaly_pixels", []) or []
    candidates = [p for p in ap if hav(p["lat"], p["lon"], clat, clon) <= radius_km]
    return sum(p.get("vrp_mw", 0) for p in candidates)


def main():
    data = json.load(open("data/mirova_equivalent/Villarrica.json"))

    print("=" * 100)
    print("S55 A/B offline - 4 estrategias agregacion vs 5 casos paradigmaticos MIROVA Villarrica")
    print("=" * 100)
    print(f"\n{'Caso':<30} {'MIROVA':>8} {'pc.vrp (sum)':>13} {'top_pixel':>10} {'eq16':>8} {'thresh':>9} {'radius1km':>11}")
    print("-" * 100)

    rows = []
    for ts, sensor_pref, mirova_mw in MIROVA_REFS:
        for r in data.get("records", []):
            if not r.get("datetime_utc", "").startswith(ts): continue
            s = r.get("sensor", "")
            if not s.startswith(sensor_pref.split("_")[0] + "_" + sensor_pref.split("_")[1]): continue
            if s.endswith("_750"): continue

            pc = r.get("primary_cluster") or {}
            pc_vrp = pc.get("vrp_mw", 0) or 0

            s1 = strategy_top_pixel(r)
            s2 = strategy_eq16(r)
            s3 = strategy_threshold_strict(r)
            s4 = strategy_summit_radius(r)

            print(f"{ts:<30} {mirova_mw:>8.2f} {pc_vrp:>13.3f} {(s1 or 0):>10.3f} {(s2 or 0):>8.4f} {(s3 or 0):>9.3f} {(s4 or 0):>11.3f}")
            rows.append({
                "case": ts, "mirova": mirova_mw, "pc": pc_vrp,
                "top_pixel": s1, "eq16": s2, "thresh": s3, "radius1km": s4
            })
            break

    print("-" * 100)
    print()
    print("RATIOS vs MIROVA (target = 1.0):")
    print(f"{'Caso':<30} {'pc/MIROVA':>11} {'top/MIROVA':>11} {'eq16/MIROVA':>12} {'thresh/MIROVA':>14} {'radius1/MIROVA':>15}")
    print("-" * 100)
    for row in rows:
        mir = row["mirova"]
        r_pc = row["pc"] / mir if mir > 0 and row["pc"] is not None else 0
        r_top = (row["top_pixel"] or 0) / mir if mir > 0 else 0
        r_eq16 = (row["eq16"] or 0) / mir if mir > 0 else 0
        r_th = (row["thresh"] or 0) / mir if mir > 0 else 0
        r_r1 = (row["radius1km"] or 0) / mir if mir > 0 else 0
        print(f"{row['case']:<30} {r_pc:>10.2f}x {r_top:>10.2f}x {r_eq16:>11.2f}x {r_th:>13.2f}x {r_r1:>14.2f}x")

    print()
    print("RESUMEN AGREGADO (mediana ratio, ideal cerca de 1.0):")
    valid = [r for r in rows if r["mirova"] > 0]
    for key in ["pc", "top_pixel", "eq16", "thresh", "radius1km"]:
        ratios = sorted([(r[key] or 0) / r["mirova"] for r in valid if r[key] is not None])
        if not ratios: continue
        median = ratios[len(ratios)//2]
        mean = sum(ratios) / len(ratios)
        print(f"  {key:<15}: mediana={median:.2f}x  promedio={mean:.2f}x  rango=[{min(ratios):.2f}x, {max(ratios):.2f}x]")


if __name__ == "__main__":
    main()
