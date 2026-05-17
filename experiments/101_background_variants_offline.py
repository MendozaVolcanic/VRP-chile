"""S56 — Background variants offline test.

Hipótesis S55: el problema upstream es que median(ring 5-25km) genera L_bg
muy caliente para pixels summit en invierno (lake/valley adyacente caliente).
MIROVA probable usa background distinto.

Test offline (sin reproc): asumir distribución normal del ring background,
proxy de percentil con `t_bg = median - k·σ_bg`. Aplicar Eq.16 con cada
variante y comparar vs MIROVA.

Casos paradigmáticos: 5 ALERTAS MIROVA Villarrica window 5 meses.
"""
from __future__ import annotations
import json
import math
import io
import sys

if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from pipeline.vrp_regimes import compute_vrp_lava_lake_eq16
from pipeline.constants import C1, C2, SIGMA

# 5 ALERTAS MIROVA confirmadas
CASES = [
    ("2026-05-11 06:00", "VIIRS_NOAA20", 0.31),
    ("2026-05-14 05:48", "VIIRS_NOAA21", 0.31),
    ("2026-04-09 06:00", "VIIRS_NOAA20", 0.11),
    ("2026-03-08 06:00", "VIIRS_NOAA20", 0.21),
    ("2026-02-26 05:42", "VIIRS_NOAA20", 0.12),
]

# Sigma multiplicadores para percentiles aproximados (asumiendo normal)
# p50 = median, p25 ≈ -0.674·σ, p10 ≈ -1.282·σ, p05 ≈ -1.645·σ
PERCENTILE_K = {
    "p50 (current)": 0.0,
    "p25": 0.674,
    "p10": 1.282,
    "p05": 1.645,
    "p01": 2.326,
}


def hav(la1, lo1, la2, lo2):
    R = 6371.0
    p1, p2 = math.radians(la1), math.radians(la2)
    dp = math.radians(la2 - la1)
    dl = math.radians(lo2 - lo1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * R * math.asin(math.sqrt(a))


def get_top_summit_pixel(record, max_dist_km=2.0):
    """Pixel más caliente dentro de max_dist_km del centroide pc."""
    pc = record.get("primary_cluster") or {}
    clat, clon = pc.get("centroid_lat"), pc.get("centroid_lon")
    if clat is None:
        return None
    ap = record.get("anomaly_pixels", []) or []
    candidates = [p for p in ap if hav(p["lat"], p["lon"], clat, clon) <= max_dist_km]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.get("bt_k", 0))


def main():
    data = json.load(open("data/mirova_equivalent/Villarrica.json"))

    print("=" * 110)
    print("S56 — Background variants offline (Eq.16 R2 con T_e=1000K, percentiles ring)")
    print("=" * 110)

    rows = []
    for ts, sensor, mirova_mw in CASES:
        for r in data.get("records", []):
            if not r.get("datetime_utc", "").startswith(ts): continue
            s = r.get("sensor", "")
            if not s.startswith(sensor.split("_")[0] + "_" + sensor.split("_")[1]): continue
            if s.endswith("_750"): continue

            t_bg_median = r.get("t_bg_k") or r.get("diag_t_bg_i04")
            sigma_bg = r.get("diag_sigma_bg_k", 0) or 0
            top = get_top_summit_pixel(r)
            bt_hot = top["bt_k"] if top else None

            if t_bg_median is None or bt_hot is None:
                continue

            print(f"\n=== {ts} {sensor} ===")
            print(f"  MIROVA: {mirova_mw} MW | BT_summit: {bt_hot}K | t_bg_median: {t_bg_median}K | σ_bg: {sigma_bg}K")
            print(f"  {'Variant':<20} {'t_bg':>8} {'ΔBT':>7} {'VRP Eq.16':>12} {'Ratio':>8}")

            row = {"case": ts, "mirova": mirova_mw, "bt_hot": bt_hot, "t_bg_median": t_bg_median, "sigma": sigma_bg}
            for variant, k in PERCENTILE_K.items():
                t_bg_variant = t_bg_median - k * sigma_bg
                result = compute_vrp_lava_lake_eq16(
                    bt_hot_k=bt_hot,
                    bt_bg_k=t_bg_variant,
                    t_bk_k=t_bg_variant,
                )
                delta_bt = bt_hot - t_bg_variant
                vrp = result["vrp_mw"]
                ratio = vrp / mirova_mw if mirova_mw > 0 else 0
                print(f"  {variant:<20} {t_bg_variant:>8.2f} {delta_bt:>7.2f} {vrp:>12.4f} {ratio:>8.2f}x")
                row[variant] = vrp
                row[f"{variant}_ratio"] = ratio
            rows.append(row)
            break

    print("\n" + "=" * 110)
    print("RESUMEN AGREGADO ratios vs MIROVA (target = 1.0):")
    print("=" * 110)
    print(f"  {'Variant':<25} {'mediana':>10} {'promedio':>10} {'min':>8} {'max':>8} {'#hits':>7}")
    for variant in PERCENTILE_K.keys():
        ratios = sorted([r[f"{variant}_ratio"] for r in rows])
        n_hits = sum(1 for x in ratios if 0.3 <= x <= 3.0)  # casos en rango aceptable
        if ratios:
            median = ratios[len(ratios)//2]
            mean = sum(ratios) / len(ratios)
            print(f"  {variant:<25} {median:>9.2f}x {mean:>9.2f}x {min(ratios):>7.2f}x {max(ratios):>7.2f}x {n_hits:>5}/5")


if __name__ == "__main__":
    main()
