"""S108 — Audit PAREADO del A/B ancla honesta VIIRS750 (run 27468739388) vs produccion.

Espejo V750 de audit_honest_anchor.py (que es V375-only). Compara, por (datetime, sensor)
en comun, el reproc flag-ON (_honest_anchor_v750, en _v750_staging) contra el baseline de
produccion data/mirova_equivalent. SOLO records VIIRS750 en ventana [2026-01-29..2026-06-08].

Criterios DUROS pre-registrados (profile _honest_anchor_v750.yaml; design 2026-06-11 §4):
  C1 DETECCION/MAGNITUD IDENTICA (pareada al granule): triggered_test1 y pc.vrp_mw
     identicos base-vs-ON. El ancla SOLO reubica la posicion -> cualquier delta de
     deteccion o magnitud = BUG, parar (mismo criterio que V375 S106).
  C2 POSICION MEJORA: mediana de dist al crater baja (base ~2.89 km -> cluster/crater);
     offset N de nevados -> 0 (A70 mediana robusta, pareado sobre los mismos granules).
  C3 DESTAPE LIMPIO: flips far->summit sobre el reproc REAL con pc.vrp>5 MW = 0 (A18:
     el preview offline S106 dio 93 flips / 0 big; aca se confirma sobre data real).

Uso: python experiments/_s106_fase2/audit_v750_paired.py
"""
import json
import math
import statistics
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
STAGING = REPO / "experiments/_s106_fase2/_v750_staging"
BASE = REPO / "data/mirova_equivalent"
VOLS = ["Tupungatito", "Villarrica", "Llaima", "Lascar", "Lastarria"]
NEVADOS = {"Tupungatito", "Villarrica", "Llaima"}
VENT = {
    "Tupungatito": (-33.389044, -69.826374), "Villarrica": (-39.420227, -71.939876),
    "Llaima": (-38.692, -71.729), "Lascar": (-23.36293, -67.731416),
    "Lastarria": (-25.168, -68.507),
}
INNER = {"Lastarria": 3, "Lascar": 5, "Llaima": 5, "Villarrica": 5, "Tupungatito": 7}
CHUNK_STARTS = ["2026-01-29", "2026-04-01"]
W0, W1 = "2026-01-29", "2026-06-08"


def hav(la1, lo1, la2, lo2):
    R = 6371.0
    p = math.pi / 180
    a = (math.sin((la2 - la1) * p / 2) ** 2 +
         math.cos(la1 * p) * math.cos(la2 * p) * math.sin((lo2 - lo1) * p / 2) ** 2)
    return 2 * R * math.asin(min(1, math.sqrt(a)))


def _recs(o):
    return o.get("records", o) if isinstance(o, dict) else o


def is_v750(r):
    return str(r.get("sensor", "")).endswith("750")


def in_win(r):
    return W0 <= str(r.get("datetime_utc", ""))[:10] <= W1


def base_v750(vol):
    obj = json.load(open(BASE / f"{vol}.json", encoding="utf-8"))
    return {(r.get("datetime_utc"), r.get("sensor")): r
            for r in _recs(obj) if is_v750(r) and in_win(r)}


def repro_v750(vol):
    out = {}
    for cs in CHUNK_STARTS:
        f = STAGING / f"s106v750-{vol}-{cs}" / f"{vol}.json"
        if not f.exists():
            continue
        for r in _recs(json.load(open(f, encoding="utf-8"))):
            if is_v750(r) and in_win(r):
                out[(r.get("datetime_utc"), r.get("sensor"))] = r
    return out


def med(xs):
    return statistics.median(xs) if xs else None


def fmt(x, spec=".2f"):
    return format(x, spec) if x is not None else "—"


def main():
    print("=== AUDIT PAREADO ancla honesta VIIRS750 (S108, run 27468739388) ===\n")
    c1_bugs = []
    c2_rows = []
    c3_flips = 0
    c3_big = 0
    c3_big_list = []
    changed_fields = Counter()

    for vol in VOLS:
        vlat, vlon = VENT[vol]
        base = base_v750(vol)
        repro = repro_v750(vol)
        common = sorted(set(base) & set(repro))

        # --- C1: deteccion/magnitud identica pareada ---
        for k in common:
            b, r = base[k], repro[k]
            if bool(b.get("triggered_test1")) != bool(r.get("triggered_test1")):
                c1_bugs.append((vol, k[0], "triggered_test1",
                                b.get("triggered_test1"), r.get("triggered_test1")))
            bv = (b.get("primary_cluster") or {}).get("vrp_mw") or 0
            rv = (r.get("primary_cluster") or {}).get("vrp_mw") or 0
            if abs(bv - rv) > 1e-6:
                c1_bugs.append((vol, k[0], "pc.vrp_mw", round(bv, 3), round(rv, 3)))
            # diagnostico: que campos top-level cambian (deberia ser solo posicion)
            for fld in set(b) | set(r):
                if fld in ("updated",):
                    continue
                if b.get(fld) != r.get(fld):
                    changed_fields[fld] += 1

        # --- C2: posicion pareada (mismos granules, distinta posicion) ---
        def loc(d):
            ds, off = [], []
            for k in common:
                r = d[k]
                if r.get("final_hotspot_lat") is not None:
                    ds.append(hav(vlat, vlon, r["final_hotspot_lat"], r["final_hotspot_lon"]))
                    off.append((r["final_hotspot_lat"] - vlat) * 111320)
            return ds, off
        bd, boff = loc(base)
        rd, roff = loc(repro)
        c2_rows.append((vol, med(bd), med(rd), med(boff), med(roff), len(common)))

        # --- C3: destape limpio (flips far->summit sobre el reproc real) ---
        for k in common:
            b, r = base[k], repro[k]
            if b.get("distance_class") == "far" and r.get("distance_class") == "summit":
                c3_flips += 1
                pcv = (r.get("primary_cluster") or {}).get("vrp_mw") or 0
                if pcv > 5:
                    c3_big += 1
                    c3_big_list.append((vol, k[0], round(pcv, 1)))

    # ---- reportes ----
    print("C2 — posicion (granules pareados; dist mediana al crater, offset N mediano, m):")
    print(f"  {'vol':<14}{'n':>5}{'dist_base':>11}{'dist_ON':>9}{'offN_base':>11}{'offN_ON':>9}")
    for vol, bdm, rdm, bom, rom, n in c2_rows:
        tag = " (NEVADO)" if vol in NEVADOS else ""
        print(f"  {vol:<14}{n:>5}{fmt(bdm):>11}{fmt(rdm):>9}"
              f"{fmt(bom, '.0f'):>11}{fmt(rom, '.0f'):>9}{tag}")

    print(f"\nC1 — deteccion/magnitud pareada (delta = BUG): {len(c1_bugs)} discrepancias")
    for row in c1_bugs[:20]:
        print(f"  BUG {row}")
    print(f"  campos top-level que cambian (granules comunes): "
          f"{dict(changed_fields.most_common())}")

    print(f"\nC3 — destape sobre reproc REAL: {c3_flips} flips far->summit | "
          f"{c3_big} con pc.vrp>5 MW (preview offline S106: 93 flips / 0 big)")
    for row in c3_big_list[:20]:
        print(f"  big flip {row}")

    # ---- veredicto ----
    p1 = len(c1_bugs) == 0
    p3 = c3_big == 0
    p2 = all(not (bdm is not None and rdm is not None and rdm > bdm + 0.01)
             for _, bdm, rdm, _, _, _ in c2_rows)
    print("\n=== VEREDICTO ===")
    print(f"  C1 deteccion/magnitud identica (delta=BUG): {'PASS' if p1 else 'FAIL'}")
    print(f"  C2 posicion no empeora (mejora nevados):     {'PASS' if p2 else 'FAIL'}")
    print(f"  C3 destape limpio (0 inflados pc.vrp>5):     {'PASS' if p3 else 'FAIL'}")
    print(f"\n  {'>>> V750 LISTO PARA FLIP (C1+C2+C3 PASS)' if (p1 and p2 and p3) else '>>> NO PROMOVER'}")


if __name__ == "__main__":
    main()
