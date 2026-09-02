#!/usr/bin/env python3
"""Costo informativo de "ultima pasada" (S90/S130) frente al maximo de la ventana.

La tarjeta titula con la ULTIMA deteccion de 48 h. Si la ultima pasada es una
VIIRS375 debil y 20 h antes hubo un MODIS de 5 MW, el operador ve el numero chico.
Mide, sobre ventanas rodantes: cuanto se pierde y cuantas veces cambia el NIVEL.
Read-only.
"""
import io, os, sys, argparse
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import replicate_frontend as F


def max_in_window(records, now_ms, inner_km, hours=48):
    cutoff = now_ms - hours * 3600000
    best = None
    for r in records:
        ts = F.parse_utc_ms(r.get("datetime_utc"))
        if not (ts >= cutoff) or ts > now_ms:
            continue
        if not F.is_summit_detection(r) or not F.is_valid_detection(r):
            continue
        if F.is_thermal_artifact(r, inner_km):
            continue
        v = F.eq_vrp_display(r, inner_km, False)
        if v <= 0:
            continue
        if best is None or v > best[0]:
            best = (v, r.get("datetime_utc"), r.get("sensor"))
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--step-h", type=int, default=6)
    a = ap.parse_args()
    F.DATA = a.data_dir
    print("=== ultima pasada vs maximo de 48 h (paso %d h, 100 dias publicados) ===" % a.step_h)
    print(f"{'volcan':22}{'n_vent':>8}{'lvl distinto':>14}{'ratio med max/ult':>20}{'ej peor caso':>34}")
    tot_n = tot_diff = 0
    for vol in F.TIER_A:
        d = F.load(vol)
        recs = d.get("records", [])
        inner = F.INNER[vol]
        ts_all = [t for t in (F.parse_utc_ms(r.get("datetime_utc")) for r in recs) if t == t]
        if not ts_all:
            continue
        t, t1 = min(ts_all) + 48 * 3600000, max(ts_all)
        step = a.step_h * 3600000
        n = diff = 0
        ratios = []
        worst = None
        while t <= t1:
            last = F.latest_detection(recs, t, False, inner)
            mx = max_in_window(recs, t, inner)
            if last and mx:
                n += 1
                lv_l = F.get_level(last["vrp"])[1]
                lv_m = F.get_level(mx[0])[1]
                if lv_l != lv_m:
                    diff += 1
                ratios.append(mx[0] / last["vrp"] if last["vrp"] > 0 else float("inf"))
                if worst is None or (mx[0] / max(last["vrp"], 1e-9)) > worst[0]:
                    worst = (mx[0] / max(last["vrp"], 1e-9), last["vrp"], mx[0], mx[1], mx[2])
            t += step
        if not n:
            continue
        ratios.sort()
        med = ratios[len(ratios) // 2]
        tot_n += n
        tot_diff += diff
        ej = (f"{worst[1]:.2f}->{worst[2]:.2f} MW @{worst[3]} {worst[4]}"
              if worst else "-")
        print(f"{vol:22}{n:>8}{100*diff/n:>13.1f}%{med:>20.1f}   {ej:<34}")
    print(f"{'TOTAL':22}{tot_n:>8}{100*tot_diff/tot_n:>13.1f}%")


if __name__ == "__main__":
    main()
