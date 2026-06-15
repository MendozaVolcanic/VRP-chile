"""S109 — Promoción magnitud núcleo-focal MODIS a data/mirova_equivalent (LOCAL, sin commit).

Lee los artifacts de reproc-s109-focal-promote (11 vols x 2 chunks, perfil
_s109_focal_promote = mirova_equivalent ya flipeado: enable_focal_cluster_magnitude:true).

ALCANCE: solo se promueven los records **MODIS** dentro de la ventana [W0..W1]. Los records
VIIRS del base quedan INTACTOS (el fix focal es MODIS-only). Records fuera de ventana se conservan.

GUARD anti-underfetch: si el reproc bajó MENOS records MODIS que el base (cobertura NASA
distinta esa corrida) → SKIP ese vol con WARN (no perder records reales). La detección NO
cambia (A/B C1 0-diffs) — solo cambia pc.vrp_mw (de-inflado). Espejo de merge_promote_nadir.py.

Uso:
  gh run download <RUN_ID> -D experiments/_s109_modis_mag/_promo_art
  python experiments/_s109_modis_mag/merge_promote_focal.py
Luego: audit R3 + preview 3 vistas → si OK commit+push.
Rollback: git checkout origin/main -- data/mirova_equivalent/<vol>.json
"""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ART = REPO / "experiments/_s109_modis_mag/_promo_art"
VOLS = ["Lascar", "PuyehueCordonCaulle", "Tupungatito", "Chaiten", "Villarrica",
        "Llaima", "PlanchonPeteroa", "Copahue", "Isluga", "Lastarria",
        "NevadosDeChillan"]
W0, W1 = "2026-01-29", "2026-06-15"
CHUNK_STARTS = ["2026-01-29", "2026-04-01"]


def _recs(o):
    return o["records"] if isinstance(o, dict) else o


def _is_modis(r):
    return str(r.get("sensor", "")).startswith("MODIS")


def _in_win(r):
    return W0 <= str(r.get("datetime_utc", ""))[:10] <= W1


def _modis_cov(recs):
    return sum(1 for r in recs if _is_modis(r) and _in_win(r))


def _pcv(r):
    return float((r.get("primary_cluster") or {}).get("vrp_mw", 0) or 0)


def _modis_inflated(recs):
    return sum(1 for r in recs if _is_modis(r) and _in_win(r) and _pcv(r) > 5)


def _chunk(vol, cs):
    hits = list((ART / f"s109focalpromo-{vol}-{cs}").glob(f"{vol}.json"))
    if not hits:
        hits = list(ART.rglob(f"s109focalpromo-{vol}-{cs}/{vol}.json"))
    return hits[0] if hits else None


def main():
    report = []
    for vol in VOLS:
        base_path = REPO / "data/mirova_equivalent" / f"{vol}.json"
        base_obj = json.load(open(base_path, encoding="utf-8"))
        base_recs = _recs(base_obj)

        repro_modis = {}
        missing = []
        for cs in CHUNK_STARTS:
            jf = _chunk(vol, cs)
            if jf is None:
                missing.append(cs)
                continue
            for r in _recs(json.load(open(jf, encoding="utf-8"))):
                if _is_modis(r) and _in_win(r):
                    repro_modis[(r.get("datetime_utc"), r.get("sensor"))] = r
        if missing:
            report.append((vol, f"SKIP — faltan chunks {missing}", "", ""))
            continue

        repro_recs = list(repro_modis.values())
        cov_base = _modis_cov(base_recs)
        cov_repro = len(repro_recs)
        if cov_repro < cov_base:
            report.append((vol, f"SKIP — under-fetch MODIS ({cov_repro}<{cov_base} cov)", "", ""))
            continue

        kept = [r for r in base_recs if not (_is_modis(r) and _in_win(r))]
        final = kept + repro_recs
        final.sort(key=lambda r: str(r.get("datetime_utc", "")))

        infl_base = _modis_inflated(base_recs)
        infl_repro = _modis_inflated(repro_recs)
        if isinstance(base_obj, dict):
            base_obj["records"] = final
            out = base_obj
        else:
            out = final
        json.dump(out, open(base_path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        report.append((vol, f"{len(base_recs)}->{len(final)} recs",
                       f"MODIS cov {cov_base}->{cov_repro}",
                       f"MODIS infl>5MW {infl_base}->{infl_repro}"))

    print("=== Promoción magnitud focal MODIS (LOCAL, guard por cobertura) ===")
    for vol, a, b, c in report:
        print(f"  {vol:<20} {a:<22} {b:<24} {c}")
    print("\nEsperado: MODIS infl>5MW baja fuerte (de-inflado); cov igual o mayor.")
    print("Verificar: audit R3 + preview 3 vistas. Rollback: git checkout origin/main -- data/...")


if __name__ == "__main__":
    main()
