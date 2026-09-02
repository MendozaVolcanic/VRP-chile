#!/usr/bin/env python3
"""Que ve el operador en el mapa: cuantos marcadores, en cuantas coordenadas
distintas, y cuantos son el ancla test1_roi (= la coordenada exacta del crater,
puesta por construccion, no medida).

Replica index.html:2472-2560 con los defaults del dashboard
(onlyPrimaryPixel=true, includeFarDistance=false, ventana 30 d).
Read-only.
"""
import io, os, sys, argparse
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import replicate_frontend as F


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--now", default=None)
    a = ap.parse_args()
    F.DATA = a.data_dir
    from datetime import datetime, timezone
    now_ms = (datetime.fromisoformat(a.now).replace(tzinfo=timezone.utc).timestamp() * 1000
              if a.now else datetime.now(timezone.utc).timestamp() * 1000)

    print(f"=== marcadores del mapa (ventana {a.days} d, 'Solo crater', "
          "'solo pixel primario' = defaults) ===")
    print(f"{'volcan':22}{'markers':>9}{'coords dist':>13}{'% en 1 coord':>14}"
          f"{'src=test1_roi':>15}{'far ocultos':>13}{'far MODIS':>11}")
    for vol in F.TIER_A:
        d = F.load(vol)
        recs = F.filter_days(d.get("records", []), a.days, now_ms)
        inner = F.INNER[vol]
        markers, coords, src = 0, Counter(), Counter()
        far_hidden, far_modis = 0, 0
        for r in recs:
            if not F.is_valid_detection(r):
                continue
            dc = r.get("distance_class")
            if dc == "far":
                far_hidden += 1
                if str(r.get("sensor") or "").startswith("MODIS"):
                    far_modis += 1
                continue
            fh = r.get("final_hotspot_source")
            honest = fh in ("test1_roi", "test1_nti_peak")
            if honest and r.get("final_hotspot_lat") is not None:
                lat, lon = r["final_hotspot_lat"], r["final_hotspot_lon"]
            elif r.get("anomaly_pixels"):
                p = r["anomaly_pixels"][0]
                lat, lon = p.get("lat"), p.get("lon")
            elif r.get("final_hotspot_lat") is not None:
                lat, lon = r["final_hotspot_lat"], r["final_hotspot_lon"]
            elif r.get("hotspot_lat") is not None:
                lat, lon = r["hotspot_lat"], r["hotspot_lon"]
            else:
                continue
            if lat is None or lon is None:
                continue
            markers += 1
            coords[(round(lat, 5), round(lon, 5))] += 1
            src[fh] += 1
        if not markers:
            continue
        top = coords.most_common(1)[0]
        print(f"{vol:22}{markers:>9}{len(coords):>13}{100*top[1]/markers:>13.1f}%"
              f"{100*src['test1_roi']/markers:>14.1f}%{far_hidden:>13}{far_modis:>11}")


if __name__ == "__main__":
    main()
