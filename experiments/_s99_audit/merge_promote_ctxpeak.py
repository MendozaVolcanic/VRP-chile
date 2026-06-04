"""S100 — Promoción de ctxpeak a data/mirova_equivalent (LOCAL, sin commit).

Lee los artifacts del reproc-promote (s100promo-<vol>-<chunkstart>, 4 vols × 2 chunks
abril+mayo, perfil mirova_equivalent con ctxpeak ya ON). Reemplaza la ventana abr-may
y CONSERVA el resto (marzo previo + junio posterior que el NRT cron irá curando).

GUARD (lección de hoy): NO escribe un volcán si el reproc tiene MENOS detecciones
(pc.vrp>0) en la ventana que el base operacional — eso indicaría under-fetch (como el
A/B parcial) y perdería detecciones reales. Aborta ese vol con WARN.

Uso:
  gh run download <RUN_ID> -D experiments/_s99_audit/_promo_art
  python experiments/_s99_audit/merge_promote_ctxpeak.py
Luego: audit + preview 3 vistas → si OK commit+push.
Rollback: git checkout origin/main -- data/mirova_equivalent/<vol>.json
"""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ART = REPO / "experiments/_s99_audit/_promo_art"
VOLS = ["Tupungatito", "Lastarria", "PlanchonPeteroa", "Llaima"]
W0, W1 = "2026-04-01", "2026-05-31"
CHUNK_STARTS = ["2026-04-01", "2026-05-01"]


def _recs(o):
    return o["records"] if isinstance(o, dict) else o


def _dets(recs, w0=W0, w1=W1):
    return sum(1 for r in recs if w0 <= str(r.get("datetime_utc", ""))[:10] <= w1
               and ((r.get("primary_cluster") or {}).get("vrp_mw", 0) or 0) > 0)


def _chunk(vol, cs):
    hits = list((ART / f"s100promo-{vol}-{cs}").glob(f"{vol}.json"))
    if not hits:
        hits = list(ART.rglob(f"s100promo-{vol}-{cs}/{vol}.json"))
    return hits[0] if hits else None


def main():
    report = []
    for vol in VOLS:
        base_path = REPO / "data/mirova_equivalent" / f"{vol}.json"
        base_obj = json.load(open(base_path, encoding="utf-8"))
        base_recs = _recs(base_obj)
        repro = {}
        missing = []
        for cs in CHUNK_STARTS:
            jf = _chunk(vol, cs)
            if jf is None:
                missing.append(cs); continue
            for r in _recs(json.load(open(jf, encoding="utf-8"))):
                day = str(r.get("datetime_utc", ""))[:10]
                if W0 <= day <= W1:
                    repro[(r.get("datetime_utc"), r.get("sensor"))] = r
        if missing:
            report.append((vol, f"SKIP — faltan chunks {missing}", "", "")); continue
        repro_recs = list(repro.values())
        d_base, d_repro = _dets(base_recs), _dets(repro_recs)
        if d_repro < d_base:
            report.append((vol, f"SKIP — under-fetch ({d_repro}<{d_base} det)", "", "")); continue
        kept = [r for r in base_recs if not (W0 <= str(r.get("datetime_utc", ""))[:10] <= W1)]
        final = kept + repro_recs
        final.sort(key=lambda r: str(r.get("datetime_utc", "")))
        if isinstance(base_obj, dict):
            base_obj["records"] = final; out = base_obj
        else:
            out = final
        json.dump(out, open(base_path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        report.append((vol, f"{len(base_recs)}->{len(final)}",
                       f"det ventana {d_base}->{d_repro}", f"conservados fuera={len(kept)}"))
    print("=== Promoción ctxpeak (LOCAL, con guard anti-underfetch) ===")
    for vol, a, b, c in report:
        print(f"  {vol:<20} {a:<32} {b:<26} {c}")
    print("\nVerificar: audit + preview 3 vistas. Rollback: git checkout origin/main -- data/mirova_equivalent/<vol>.json")


if __name__ == "__main__":
    main()
