"""S53 — Calibración empírica T_e para R2 Eq.16 lava lake Villarrica.

Hipótesis: T_e=1000K default Burgi-Coppola da VRP ~6× menor que MIROVA real.
Buscar T_e óptimo que minimice error contra 5 ALERTAS MIROVA confirmadas.

Casos canónicos (verificados S52 audit S47-A2):
- 2026-05-11 06:00 NOAA20: MIROVA 0.31 MW
- 2026-05-14 05:48 NOAA21: MIROVA 0.31 MW
- 2026-04-09 06:00 NOAA20: MIROVA 0.11 MW
- 2026-03-08 06:00 NOAA20: MIROVA 0.21 MW
- 2026-02-26 05:42 NOAA20: MIROVA 0.12 MW

Para cada caso: extraer BT_hot del pixel summit más caliente, BT_bg ring,
aplicar Eq.16 con range T_e [400, 1500] y plotear ratio vs MIROVA.
"""
from __future__ import annotations
import json
import io
import sys

import pandas as pd

from pipeline.vrp_regimes import compute_vrp_lava_lake_eq16

if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# 5 ALERTAS MIROVA Villarrica VIIRS-I confirmadas (sub-pixel summit lava lake)
MIROVA_ALERTS = [
    ("2026-05-11 06:00", "VIIRS_NOAA20", 0.31),
    ("2026-05-14 05:48", "VIIRS_NOAA21", 0.31),
    ("2026-04-09 06:00", "VIIRS_NOAA20", 0.11),
    ("2026-03-08 06:00", "VIIRS_NOAA20", 0.21),
    ("2026-02-26 05:42", "VIIRS_NOAA20", 0.12),
]


def get_summit_pixel(record, max_dist_km=2.0):
    """Extrae el pixel más caliente dentro de max_dist_km del vent."""
    ap = record.get("anomaly_pixels") or []
    summit = [p for p in ap if p.get("dist_km", 999) <= max_dist_km]
    if not summit:
        return None
    # Top hottest
    return max(summit, key=lambda p: p.get("bt_k", 0))


def main():
    data = json.load(open("data/mirova_equivalent/Villarrica.json"))
    recs = data.get("records", [])
    rec_idx = {(r["datetime_utc"][:16], r.get("sensor", "")): r for r in recs}

    print("=" * 80)
    print("Calibración empírica T_e — 5 casos MIROVA Villarrica VIIRS-I 375m")
    print("=" * 80)
    print()

    # T_e a probar
    te_range = [400, 600, 800, 1000, 1200, 1400]

    rows = []
    for ts, sensor, mirova_vrp in MIROVA_ALERTS:
        rec = rec_idx.get((ts, sensor))
        if rec is None:
            # Buscar prefix match
            for (k_ts, k_sensor), r in rec_idx.items():
                if k_ts.startswith(ts[:16]) and k_sensor == sensor:
                    rec = r
                    break
        if rec is None:
            print(f"⚠️  Sin record: {ts} {sensor}")
            continue

        pixel = get_summit_pixel(rec)
        if pixel is None:
            print(f"⚠️  Sin pixel summit: {ts} {sensor}")
            continue

        bt_hot = pixel["bt_k"]
        # T_bg desde t_bg_k del record (background ring 5-25km MIROVA-equivalent)
        bt_bg = rec.get("t_bg_k")
        if bt_bg is None:
            # Fallback diag_t_bg_i04 (en records más antiguos)
            bt_bg = rec.get("diag_t_bg_i04")
        if bt_bg is None:
            print(f"⚠️  Sin t_bg_k: {ts} {sensor}")
            continue

        print(f"\n=== {ts} {sensor} ===")
        print(f"  MIROVA reportó: {mirova_vrp} MW")
        print(f"  Pixel summit: BT={bt_hot}K, dist={pixel['dist_km']}km")
        print(f"  T_bg estimado: {bt_bg}K")
        print(f"  pc.vrp_mw actual (Wooster sum): {rec.get('primary_cluster',{}).get('vrp_mw')}")
        print()
        print(f"  T_e (K) | VRP R2 (MW) | A_hot (m²) | Ratio vs MIROVA")
        print(f"  --------|-------------|------------|----------------")
        for te in te_range:
            r2 = compute_vrp_lava_lake_eq16(
                bt_hot_k=bt_hot,
                bt_bg_k=bt_bg,
                t_bk_k=bt_bg,
                t_e_k=float(te),
            )
            ratio = r2["vrp_mw"] / mirova_vrp if mirova_vrp > 0 else None
            print(f"  {te:5d}   | {r2['vrp_mw']:.4f}      | {r2['a_hot_m2']:.2f}       | {ratio:.2f}")
            rows.append({
                "case": ts,
                "sensor": sensor,
                "mirova_vrp": mirova_vrp,
                "bt_hot": bt_hot,
                "bt_bg": bt_bg,
                "t_e": te,
                "vrp_r2": r2["vrp_mw"],
                "a_hot": r2["a_hot_m2"],
                "ratio": ratio,
            })

    # Resumen agregado
    print("\n" + "=" * 80)
    print("AGREGADO — ratio mediano per T_e")
    print("=" * 80)
    df = pd.DataFrame(rows)
    summary = df.groupby("t_e").agg(
        n=("ratio", "count"),
        ratio_median=("ratio", "median"),
        ratio_min=("ratio", "min"),
        ratio_max=("ratio", "max"),
    )
    print(summary)
    print()
    print("T_e con mejor balance ratio_median cerca de 1.0:")
    summary["dist_from_1"] = (summary["ratio_median"] - 1.0).abs()
    best = summary.nsmallest(3, "dist_from_1")
    print(best)


if __name__ == "__main__":
    main()
