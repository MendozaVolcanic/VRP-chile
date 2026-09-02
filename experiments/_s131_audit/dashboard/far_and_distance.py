#!/usr/bin/env python3
"""(a) D13: cuanta magnitud apaga la cerca `distance_class != summit` del frontend.
(b) A que distancia del crater caen los marcadores que SI se renderizan (PCC con
    inner_radius_km=20 pinta de rojo-summit todo un lacolito de 20 km).
Read-only.
"""
import io, os, sys, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import replicate_frontend as F
from datetime import datetime, timezone


def q(xs, p):
    if not xs:
        return None
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(p * len(xs)))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--days", type=int, default=90)
    a = ap.parse_args()
    F.DATA = a.data_dir
    now_ms = datetime.now(timezone.utc).timestamp() * 1000

    print(f"=== (a) D13 — magnitud que apaga la cerca summit (ventana {a.days} d) ===")
    print(f"{'volcan':22}{'sum eq summit':>15}{'sum eq +far':>13}{'% apagado':>11}"
          f"{'n far':>8}{'n far MIROVA-conf':>19}")
    gs = gf = 0.0
    for vol in F.TIER_A:
        recs = F.filter_days(F.load(vol).get("records", []), a.days, now_ms)
        inner = F.INNER[vol]
        s = sum(F.eq_vrp_display(r, inner, False) for r in recs
                if F.is_valid_detection(r) and not F.is_thermal_artifact(r, inner))
        sf = sum(F.eq_vrp_display(r, inner, True) for r in recs
                 if F.is_valid_detection(r) and not F.is_thermal_artifact(r, inner))
        nfar = sum(1 for r in recs if r.get("distance_class") == "far")
        nfc = sum(1 for r in recs if r.get("distance_class") == "far" and r.get("_mirova_confirmed"))
        gs += s
        gf += sf
        pct = 100 * (sf - s) / sf if sf > 0 else 0
        print(f"{vol:22}{s:>15.1f}{sf:>13.1f}{pct:>10.1f}%{nfar:>8}{nfc:>19}")
    print(f"{'TOTAL':22}{gs:>15.1f}{gf:>13.1f}{100*(gf-gs)/gf:>10.1f}%")

    print(f"\n=== (b) distancia al crater de los marcadores VISIBLES (summit, {a.days} d) ===")
    print(f"{'volcan':22}{'inner':>6}{'n':>6}{'p50 km':>8}{'p90 km':>8}{'max km':>8}{'>5 km':>8}")
    for vol in F.TIER_A:
        recs = F.filter_days(F.load(vol).get("records", []), a.days, now_ms)
        inner = F.INNER[vol]
        ds = []
        for r in recs:
            if not F.is_valid_detection(r) or r.get("distance_class") == "far":
                continue
            fh = r.get("final_hotspot_source")
            if fh in ("test1_roi", "test1_nti_peak") and r.get("final_hotspot_dist_km") is not None:
                ds.append(r["final_hotspot_dist_km"])
            elif r.get("anomaly_pixels") and r["anomaly_pixels"][0].get("dist_km") is not None:
                ds.append(r["anomaly_pixels"][0]["dist_km"])
            elif r.get("final_hotspot_dist_km") is not None:
                ds.append(r["final_hotspot_dist_km"])
        if not ds:
            continue
        print(f"{vol:22}{inner:>6}{len(ds):>6}{q(ds,.5):>8.2f}{q(ds,.9):>8.2f}"
              f"{max(ds):>8.2f}{100*sum(1 for x in ds if x>5)/len(ds):>7.1f}%")


if __name__ == "__main__":
    main()
