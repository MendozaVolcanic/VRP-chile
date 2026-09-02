#!/usr/bin/env python3
"""Cuantas de las detecciones que el operador VE estan corroboradas por MIROVA.

Replica `enrichWithMirovaConfirmation` (index.html:1310-1360): mismo bucket de
sensor, +-60 min. El campo `_mirova_confirmed` resultante SOLO se pinta en el
marcador y el popup del mapa (index.html:2609 y :2632) — ni la tarjeta, ni la
tabla "Ultimas detecciones", ni mosaico ni diario lo muestran. Este script mide
cuanto se pierde el operador por eso.
Read-only.
"""
import io, json, os, sys, argparse, bisect
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import replicate_frontend as F
from datetime import datetime, timezone

ROOT = F.ROOT
MIROVA_DIR = os.path.join(ROOT, "data", "mirova")


def our_bucket(s):
    if not s:
        return None
    su = s.upper()
    if su.startswith("MODIS"):
        return "MODIS"
    if "750" in su:
        return "VIIRS750"
    if su.startswith("VIIRS"):
        return "VIIRS375"
    return None


def mirova_bucket(s):
    if not s:
        return None
    su = str(s).upper()
    if su == "MODIS":
        return "MODIS"
    if "375" in su:
        return "VIIRS375"
    if su.startswith("VIIRS"):
        return "VIIRS750"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--days", type=int, default=30)
    a = ap.parse_args()
    F.DATA = a.data_dir
    now_ms = datetime.now(timezone.utc).timestamp() * 1000
    TOL = 60 * 60000

    print(f"=== corroboracion MIROVA de lo que se VE en pantalla (ventana {a.days} d) ===")
    print(f"{'volcan':22}{'det. visibles':>14}{'conf. MIROVA':>14}{'% conf':>9}"
          f"{'refs MIROVA':>13}")
    tv = tc = 0
    for vol in F.TIER_A:
        recs = F.filter_days(F.load(vol).get("records", []), a.days, now_ms)
        inner = F.INNER[vol]
        mp = os.path.join(MIROVA_DIR, vol + ".json")
        mby = {"MODIS": [], "VIIRS375": [], "VIIRS750": []}
        nref = 0
        if os.path.exists(mp):
            mj = json.load(open(mp, encoding="utf-8"))
            for m in mj.get("records", []):
                v = m.get("VRP_MW", m.get("vrp_mw", 0))
                try:
                    v = float(v)
                except (TypeError, ValueError):
                    continue
                if not v > 0:
                    continue
                b = mirova_bucket(m.get("sensor") or m.get("Sensor"))
                if not b:
                    continue
                t = F.parse_utc_ms(m.get("datetime_utc"))
                if t != t:
                    continue
                mby[b].append(t)
                nref += 1
        for k in mby:
            mby[k].sort()
        vis = conf = 0
        for r in recs:
            if not F.is_valid_detection(r):
                continue
            if F.is_thermal_artifact(r, inner):
                continue
            if F.eq_vrp_display(r, inner, False) <= 0:
                continue
            vis += 1
            b = our_bucket(r.get("sensor"))
            t = F.parse_utc_ms(r.get("datetime_utc"))
            if not b or t != t:
                continue
            lst = mby[b]
            i = bisect.bisect_left(lst, t)
            for j in range(max(0, i - 1), min(len(lst), i + 2)):
                if abs(lst[j] - t) <= TOL:
                    conf += 1
                    break
        tv += vis
        tc += conf
        pct = 100 * conf / vis if vis else 0
        print(f"{vol:22}{vis:>14}{conf:>14}{pct:>8.1f}%{nref:>13}")
    print(f"{'TOTAL':22}{tv:>14}{tc:>14}{100*tc/tv:>8.1f}%")


if __name__ == "__main__":
    main()
