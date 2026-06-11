"""S106 — Audit del A/B ancla espacial honesta vs predicciones pre-registradas
(design 2026-06-11 §4). Brazos: baseline_mir (disco) / anchor-A / anchor-B.

Criterios DUROS pre-registrados:
  1. trig_t1 y recall IDÉNTICOS al baseline en los brazos (el ancla no toca
     detección — cualquier delta = bug, parar).
  2. offN nevados: Tupungatito ≤300 m, Villarrica ≤200 m (A), dist mediana ≤1.0 km.
  3. Lastarria: mediana de los records ctx CONSERVA el NW real (~2.26 km).
  4. Discriminador A vs B: posiciones de los records test1-source de Lastarria
     en brazo B (¿NTI-peaks caen al NW fumarólico o aleatorios?).

Uso: python audit_honest_anchor.py base:baseline_mir A:anchor_a B:anchor_b
(dirs relativos a experiments/_s104_roi_probe/)
"""
import math
import statistics
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from audit_local_sweep import load, v375, hav, VENT, alert_nights, ORDER, NEVADOS


def med(xs):
    return statistics.median(xs) if xs else None


def fmt(x, spec=".0f"):
    return format(x, spec) if x is not None else "—"


def metrics(recs, vol):
    vlat, vlon = VENT[vol]
    vr = v375(recs)
    loc = [r for r in vr if r.get("final_hotspot_lat") is not None]
    offN = [(r["final_hotspot_lat"] - vlat) * 111320 for r in loc]
    dist = [hav(vlat, vlon, r["final_hotspot_lat"], r["final_hotspot_lon"])
            for r in loc]
    t1 = sum(1 for r in vr if r.get("triggered_test1"))
    nights = alert_nights(vol)
    hit = sum(1 for nd in nights
              if any((r.get("datetime_utc") or "")[:10] == nd for r in vr))
    srcs = Counter(r.get("final_hotspot_source") for r in loc)
    return offN, dist, t1, f"{hit}/{len(nights)}", srcs


def rumbo(dlat_m, dlon_m):
    ang = math.degrees(math.atan2(dlon_m, dlat_m)) % 360
    return ["N", "NE", "E", "SE", "S", "SW", "W", "NW"][int((ang + 22.5) // 45) % 8]


def main():
    arms = [tuple(a.split(":", 1)) for a in sys.argv[1:]]
    base = Path(__file__).parent
    for vol in ORDER:
        print(f"\n=== {vol} ({'NEVADO' if vol in NEVADOS else 'control'}) ===")
        print(f"  {'brazo':<8}{'offN_m':>8}{'dist_km':>8}{'trig_t1':>8}{'recall':>9}  sources")
        for label, d in arms:
            recs = load(base / d, vol)
            if recs is None:
                print(f"  {label:<8}(sin data)")
                continue
            offN, dist, t1, recall, srcs = metrics(recs, vol)
            print(f"  {label:<8}{fmt(med(offN)):>8}{fmt(med(dist), '.2f'):>8}"
                  f"{t1:>8}{recall:>9}  {dict(srcs.most_common(4))}")

    # discriminador Lastarria brazo B: posiciones de test1_nti_peak
    for label, d in arms:
        if label != "B":
            continue
        recs = load(base / d, "Lastarria")
        if recs is None:
            continue
        vlat, vlon = VENT["Lastarria"]
        pk = [r for r in v375(recs)
              if r.get("final_hotspot_source") == "test1_nti_peak"]
        if not pk:
            print("\nDiscriminador Lastarria-B: 0 records test1_nti_peak")
            continue
        rumbos = Counter()
        for r in pk:
            dlat = (r["final_hotspot_lat"] - vlat) * 111320
            dlon = ((r["final_hotspot_lon"] - vlon) * 111320
                    * math.cos(math.radians(vlat)))
            rumbos[rumbo(dlat, dlon)] += 1
        dists = [hav(vlat, vlon, r["final_hotspot_lat"], r["final_hotspot_lon"])
                 for r in pk]
        print(f"\nDiscriminador Lastarria-B (n={len(pk)}): dist mediana="
              f"{med(dists):.2f} km, rumbos={dict(rumbos.most_common())}")
        print("  -> NW dominante = el peak conserva el fumarolico (adoptar B); "
              "aleatorio = gana A por simplicidad.")

    print("\nCriterios duros §4: trig_t1/recall IDENTICOS a base (delta = BUG) | "
          "offN Tupun<=300 Villarrica<=200(A) | Lastarria ctx conserva NW.")


if __name__ == "__main__":
    main()
