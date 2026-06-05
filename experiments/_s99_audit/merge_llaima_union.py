"""S101 — Promocion ctxpeak Llaima por UNION (no replace), para no perder las 7
detecciones que el reproc GH no bajo (under-fetch transient NASA, granules VIIRS
sueltos de mayo). Reproc gana la magnitud (ctxpeak curado); el base rellena las
detecciones que el reproc no tiene. Conserva todo fuera de ventana.

Guard: el resultado debe tener >= detecciones que el base (no perder cobertura).
Rollback: git checkout origin/main -- data/mirova_equivalent/Llaima.json
"""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
VOL = "Llaima"
W0, W1 = "2026-04-01", "2026-05-31"
ART = REPO / "experiments/_s99_audit/_promo_art"


def _recs(o):
    return o["records"] if isinstance(o, dict) else o


def _dets(recs):
    return sum(1 for r in recs if W0 <= str(r.get("datetime_utc", ""))[:10] <= W1
               and ((r.get("primary_cluster") or {}).get("vrp_mw", 0) or 0) > 0)


def main():
    base_path = REPO / "data/mirova_equivalent" / f"{VOL}.json"
    base_obj = json.load(open(base_path, encoding="utf-8"))
    base_recs = _recs(base_obj)

    # reproc: dict por (dt,sensor) dentro de ventana
    repro = {}
    for cs in ["2026-04-01", "2026-05-01"]:
        jf = ART / f"s100promo-{VOL}-{cs}" / f"{VOL}.json"
        if not jf.exists():
            print(f"FALTA chunk {cs}"); return
        for r in _recs(json.load(open(jf, encoding="utf-8"))):
            if W0 <= str(r.get("datetime_utc", ""))[:10] <= W1:
                repro[(r.get("datetime_utc"), r.get("sensor"))] = r

    # base dentro de ventana por key
    base_in = {(r.get("datetime_utc"), r.get("sensor")): r
               for r in base_recs if W0 <= str(r.get("datetime_utc", ""))[:10] <= W1}

    # UNION: reproc gana la magnitud SOLO donde detectó (pc>0). Donde el reproc
    # llegó vacío (granule sin señal: pc=0/test1px=0 por cobertura NASA distinta)
    # pero el base SÍ detectó, se conserva el base (no perder detecciones reales).
    def _pc(r):
        return (r.get("primary_cluster") or {}).get("vrp_mw", 0) or 0
    union = dict(repro)
    filled = 0
    for k, r in base_in.items():
        if _pc(r) > 0 and _pc(union.get(k, {})) <= 0:
            union[k] = r; filled += 1  # reproc vacío, base detectó -> conservar base

    kept_out = [r for r in base_recs if not (W0 <= str(r.get("datetime_utc", ""))[:10] <= W1)]
    final = kept_out + list(union.values())
    final.sort(key=lambda r: str(r.get("datetime_utc", "")))

    d_base, d_final = _dets(base_recs), _dets(final)
    print(f"base ventana det={d_base}  | union ventana det={d_final}  | rellenadas del base={filled}")
    if d_final < d_base:
        print(f"ABORT — union pierde detecciones ({d_final}<{d_base})"); return

    if isinstance(base_obj, dict):
        base_obj["records"] = final; out = base_obj
    else:
        out = final
    json.dump(out, open(base_path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"OK Llaima {len(base_recs)}->{len(final)} records. Verificar preview + commit.")


if __name__ == "__main__":
    main()
