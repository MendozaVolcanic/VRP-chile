"""S98 — Backfill del histórico pre-90d (2026-01-29..2026-03-03) con ancla=cráter.

Reemplaza SOLO ese rango en data/mirova_equivalent/<vol>.json, manteniendo
intacto todo lo demás (los 90d ya promovidos + los records NRT que hayan entrado
mientras corría el reproc). Distinto de merge_promote.py (que reemplazaba el
rango 90d y preservaba pre-90d): acá es al revés.

final = base[día NOT in rango] + artifact[día in rango]
Dedup por (datetime_utc, sensor), ordenado. Escribe LOCAL, sin commit.

Uso: python experiments/_s98_anchor/merge_backfill.py
"""
import json
import subprocess
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
VOLS = ["Tupungatito", "PuyehueCordonCaulle", "PlanchonPeteroa"]
RANGE_LO, RANGE_HI = "2026-01-29", "2026-03-03"
RUN_ID = "26851227816"
ART = _REPO / "experiments/_s98_anchor/_backfill_art"


def _recs(o):
    return o["records"] if isinstance(o, dict) else o


def _in_range(r):
    d = str(r.get("datetime_utc", ""))[:10]
    return RANGE_LO <= d <= RANGE_HI


def main():
    ART.mkdir(parents=True, exist_ok=True)
    dst = ART / RUN_ID
    if not dst.exists():
        print(f">>> gh run download {RUN_ID} ...")
        subprocess.run(["gh", "run", "download", RUN_ID, "-D", str(dst)], check=True)

    report = []
    for vol in VOLS:
        base_path = _REPO / "data/mirova_equivalent" / f"{vol}.json"
        base_obj = json.load(open(base_path, encoding="utf-8"))
        base_recs = _recs(base_obj)

        hits = list(dst.glob(f"s98-anchor-{vol}/{vol}.json")) or list(dst.rglob(f"{vol}.json"))
        if not hits:
            print(f"  WARN {vol}: sin artifact — NO escribo")
            report.append((vol, "SKIP (sin artifact)", None))
            continue
        art_recs = _recs(json.load(open(hits[0], encoding="utf-8")))

        kept = [r for r in base_recs if not _in_range(r)]          # todo menos el rango
        repro = {(r.get("datetime_utc"), r.get("sensor")): r       # rango reprocesado
                 for r in art_recs if _in_range(r)}
        final = kept + list(repro.values())
        final.sort(key=lambda r: str(r.get("datetime_utc", "")))

        if isinstance(base_obj, dict):
            base_obj["records"] = final
            out = base_obj
        else:
            out = final
        json.dump(out, open(base_path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        report.append((vol, f"{len(base_recs)}→{len(final)} recs",
                       f"fuera_rango={len(kept)} rango_repro={len(repro)}"))

    print("\n=== backfill ene-mar (LOCAL, sin commit) ===")
    for vol, a, b in report:
        print(f"  {vol:<22} {a:<22} {b or ''}")
    print("\nSiguiente: verificar det→cráter ene-mar <2km + preview → commit+push.")
    print("Rollback: git checkout origin/main -- data/mirova_equivalent/<vol>.json")


if __name__ == "__main__":
    main()
