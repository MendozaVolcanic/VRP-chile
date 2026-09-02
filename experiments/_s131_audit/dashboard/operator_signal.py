#!/usr/bin/env python3
"""Parte B: cuanta capacidad de discriminacion tiene la tarjeta para el operador.

Barre ventanas rodantes de 48 h sobre los 100 dias publicados y cuenta que nivel de
alerta habria mostrado cada tarjeta. Si el 100 % de las ventanas dan 'Muy Bajo', la
tarjeta no informa nada al turno de las 3 AM.
Tambien caza el 5.0 MW exacto repetido (posible piso/cap del pipeline).
Read-only.
"""
import io, json, os, sys, argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import replicate_frontend as F  # ya deja sys.stdout en utf-8 (no re-envolver: cierra el buffer)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--step-h", type=int, default=6)
    a = ap.parse_args()
    F.DATA = a.data_dir

    grand = Counter()
    per_vol = {}
    fives = defaultdict(list)
    for vol in F.TIER_A:
        d = F.load(vol)
        recs = d.get("records", [])
        inner = F.INNER[vol]
        ts_all = [F.parse_utc_ms(r.get("datetime_utc")) for r in recs]
        ts_all = [t for t in ts_all if t == t]
        if not ts_all:
            continue
        t0, t1 = min(ts_all) + 48 * 3600000, max(ts_all)
        c = Counter()
        step = a.step_h * 3600000
        t = t0
        while t <= t1:
            det = F.latest_detection(recs, t, False, inner)
            lvl = F.get_level(det["vrp"] if det else 0)[1]
            c[lvl] += 1
            grand[lvl] += 1
            t += step
        per_vol[vol] = c
        # 5.0 MW exacto
        for r in recs:
            v = F.eq_vrp_display(r, inner, False)
            if abs(v - 5.0) < 1e-9:
                fives[vol].append((r.get("datetime_utc"), r.get("sensor"),
                                   (r.get("primary_cluster") or {}).get("vrp_mw"),
                                   r.get("vrp_mw")))

    print("=== Nivel de la tarjeta en ventanas rodantes de 48 h "
          f"(paso {a.step_h} h, ventana publicada = 100 dias) ===")
    order = ["Sin datos", "Muy Bajo", "Bajo", "Moderado", "Alto", "Muy Alto"]
    hdr = f"{'volcan':22}" + "".join(f"{o:>11}" for o in order) + f"{'n':>7}"
    print(hdr)
    for vol, c in per_vol.items():
        n = sum(c.values())
        row = f"{vol:22}" + "".join(f"{100*c[o]/n:>10.1f}%" for o in order) + f"{n:>7}"
        print(row)
    n = sum(grand.values())
    print(f"{'TOTAL':22}" + "".join(f"{100*grand[o]/n:>10.1f}%" for o in order) + f"{n:>7}")

    print("\n=== records con eq_vrp_display == 5.000 exacto ===")
    for vol, lst in fives.items():
        print(f"{vol}: n={len(lst)}  ej={lst[:3]}")
    if not fives:
        print("(ninguno)")


if __name__ == "__main__":
    main()
