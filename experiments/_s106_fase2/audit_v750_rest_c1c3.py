"""S108 — Audit C1+C3 de los 6 Tier A rest del ancla V750 (run 27482258622) antes de
promover. Espejo reducido de audit_v750_paired.py (sin C2/VENT: la mejora de posición
ya quedó validada en los 5 del A/B; aquí confirmo que el ancla NO tocó detección/magnitud
y que el destape es limpio).

C1: pareado al granule, triggered_test1 + pc.vrp_mw idénticos base-vs-reproc (delta=BUG,
    salvo NRT borderline como Villarrica 06-07).
C3: flips far->summit con pc.vrp>5 = 0 (destape sin inflados nuevos).

Uso: python experiments/_s106_fase2/audit_v750_rest_c1c3.py
"""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
STAGING = REPO / "experiments/_s106_fase2/_v750_rest_staging"
BASE = REPO / "data/mirova_equivalent"
VOLS = ["Isluga", "Chaiten", "Copahue", "NevadosDeChillan", "PlanchonPeteroa",
        "PuyehueCordonCaulle"]
CHUNKS = ["2026-01-29", "2026-04-01"]
W0, W1 = "2026-01-29", "2026-06-08"


def _recs(o):
    return o.get("records", o) if isinstance(o, dict) else o


def is750(r):
    return str(r.get("sensor", "")).endswith("750")


def inwin(r):
    return W0 <= str(r.get("datetime_utc", ""))[:10] <= W1


def main():
    print(f"{'vol':<20}{'common':>8}{'C1_diffs':>9}{'flips_f2s':>10}{'big(>5)':>8}  C1 detail")
    tot_c1 = tot_big = tot_flips = 0
    for vol in VOLS:
        base = {(r["datetime_utc"], r["sensor"]): r
                for r in _recs(json.load(open(BASE / f"{vol}.json", encoding="utf-8")))
                if is750(r) and inwin(r)}
        rep = {}
        for cs in CHUNKS:
            f = STAGING / f"s108v750rest-{vol}-{cs}" / f"{vol}.json"
            if f.exists():
                for r in _recs(json.load(open(f, encoding="utf-8"))):
                    if is750(r) and inwin(r):
                        rep[(r["datetime_utc"], r["sensor"])] = r
        common = set(base) & set(rep)
        c1, flips, big, detail = 0, 0, 0, []
        for k in sorted(common):
            b, r = base[k], rep[k]
            if bool(b.get("triggered_test1")) != bool(r.get("triggered_test1")):
                c1 += 1
                detail.append(f"{k[0]} trig {b.get('triggered_test1')}->{r.get('triggered_test1')}")
            bv = (b.get("primary_cluster") or {}).get("vrp_mw") or 0
            rv = (r.get("primary_cluster") or {}).get("vrp_mw") or 0
            if abs(bv - rv) > 1e-6:
                c1 += 1
                detail.append(f"{k[0]} pc.vrp {round(bv,2)}->{round(rv,2)}")
            if b.get("distance_class") == "far" and r.get("distance_class") == "summit":
                flips += 1
                if rv > 5:
                    big += 1
        tot_c1 += c1; tot_big += big; tot_flips += flips
        print(f"{vol:<20}{len(common):>8}{c1:>9}{flips:>10}{big:>8}  {'; '.join(detail[:2])}")
    print(f"\nTOTAL C1_diffs={tot_c1} (esperado ~0; NRT borderline aceptable) | "
          f"flips far->summit={tot_flips} | big destape(>5)={tot_big} (esperado 0)")
    print(f"  {'>>> REST C1/C3 OK — promover' if tot_big == 0 and tot_c1 <= 6 else '>>> REVISAR antes de promover'}")


if __name__ == "__main__":
    main()
