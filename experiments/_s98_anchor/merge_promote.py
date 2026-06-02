"""S98 — Merge de promoción: ensambla los 90 días reprocesados (ancla=cráter)
con el histórico pre-90d intacto, en data/mirova_equivalent/ (LOCAL, sin commit).

Cada chunk-artifact trae el JSON completo de main + SU rango reprocesado. Para
dejar el rango 90d LIMPIO (solo lo reprocesado, sin fantasmas del ancla viejo),
se reemplaza el rango completo: final = pre-90d(base) + records del artifact de
cada sub-rango. Dedup por (datetime_utc, sensor), ordenado por fecha.

Tras correr: revisar el reporte, correr audits, verificar en preview las 3 vistas,
y SOLO entonces commit+push (procedimiento docs/S98_PROMOTION_PROCEDURE.md).
Rollback local: git checkout origin/main -- data/mirova_equivalent/<vol>.json

Uso: python experiments/_s98_anchor/merge_promote.py
(los run-ids de los chunks están abajo; ajustar si se re-disparan).
"""
import json
import subprocess
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
VOLS = ["Tupungatito", "PuyehueCordonCaulle", "PlanchonPeteroa"]
WINDOW_START = "2026-03-04"  # 90 días

# (run_id, chunk_start, chunk_end) — rangos disjuntos que cubren los 90 días
CHUNKS = [
    ("26839962842", "2026-03-04", "2026-04-02"),
    ("26839967867", "2026-04-03", "2026-05-02"),
    ("26839973072", "2026-05-03", "2026-06-02"),
]
ART = _REPO / "experiments/_s98_anchor/_promote_art"


def _recs(obj):
    return obj["records"] if isinstance(obj, dict) else obj


def _download():
    ART.mkdir(parents=True, exist_ok=True)
    for run_id, _, _ in CHUNKS:
        dst = ART / run_id
        if dst.exists():
            print(f"  artifact {run_id} ya descargado")
            continue
        print(f">>> gh run download {run_id} ...")
        subprocess.run(["gh", "run", "download", run_id, "-D", str(dst)], check=True)


def _chunk_json(run_id, vol):
    hits = list((ART / run_id).glob(f"s98-anchor-{vol}/{vol}.json"))
    if not hits:
        hits = list((ART / run_id).rglob(f"{vol}.json"))
    return hits[0] if hits else None


def main():
    _download()
    report = []
    for vol in VOLS:
        base_path = _REPO / "data/mirova_equivalent" / f"{vol}.json"
        base_obj = json.load(open(base_path, encoding="utf-8"))
        base_recs = _recs(base_obj)

        # pre-90d intactos
        kept = [r for r in base_recs if str(r.get("datetime_utc", ""))[:10] < WINDOW_START]
        # reprocesado: por chunk, solo su sub-rango
        repro = {}
        missing = []
        for run_id, s, e in CHUNKS:
            jf = _chunk_json(run_id, vol)
            if jf is None:
                missing.append(run_id)
                continue
            crecs = _recs(json.load(open(jf, encoding="utf-8")))
            for r in crecs:
                day = str(r.get("datetime_utc", ""))[:10]
                if s <= day <= e:
                    repro[(r.get("datetime_utc"), r.get("sensor"))] = r
        if missing:
            print(f"  WARN {vol}: faltan artifacts {missing} — NO escribo este vol")
            report.append((vol, "SKIP (artifacts faltantes)", None, None))
            continue

        final = kept + list(repro.values())
        final.sort(key=lambda r: str(r.get("datetime_utc", "")))
        if isinstance(base_obj, dict):
            base_obj["records"] = final
            out = base_obj
        else:
            out = final
        json.dump(out, open(base_path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        days = sorted(str(r.get("datetime_utc", ""))[:10] for r in final if r.get("datetime_utc"))
        report.append((vol, f"{len(base_recs)}→{len(final)} recs",
                       f"pre90d={len(kept)} repro={len(repro)}",
                       f"{days[0]}..{days[-1]}"))

    print("\n=== merge de promoción (LOCAL, sin commit) ===")
    for vol, a, b, c in report:
        print(f"  {vol:<22} {a:<22} {b or '':<22} {c or ''}")
    print("\nSiguiente: audits + preview 3 vistas → si OK, commit+push.")
    print("Rollback: git checkout origin/main -- data/mirova_equivalent/<vol>.json")


if __name__ == "__main__":
    main()
