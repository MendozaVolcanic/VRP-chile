"""S102 — Promoción nadir-fijo MODIS a data/mirova_equivalent (LOCAL, sin commit).

Lee los artifacts del reproc-s102-nadir-promote (11 vols x 2 chunks, perfil
_s102_nadir_promote = mirova_equivalent ya flipeado: nadir-fijo MODIS + piso 0.05).

ALCANCE: solo se promueven los records **MODIS** dentro de la ventana
[2026-01-29 .. 2026-06-04]. Los records VIIRS del base quedan INTACTOS (el fix
nadir es MODIS-only; no re-tocamos VIIRS para evitar variacion de fetch NASA).
Los records fuera de ventana tambien se conservan.

GUARD anti-underfetch (#345): el verdadero riesgo es que el reproc haya bajado
MENOS granules MODIS que el base (cobertura NASA distinta) -> perderia records
reales. Se mide por COBERTURA = total de records MODIS en la ventana (no por
detecciones, que cambian legitimamente con el piso 0.27->0.05). Si el reproc
tiene MENOS records MODIS que el base -> SKIP ese vol con WARN.

Uso:
  gh run download <RUN_ID> -D experiments/_s99_audit/_s102_promo_art
  python experiments/_s99_audit/merge_promote_nadir.py
Luego: audit (R3) + preview 3 vistas (R2/R8) -> si OK commit+push.
Rollback: git checkout origin/main -- data/mirova_equivalent/<vol>.json
"""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ART = REPO / "experiments/_s99_audit/_s102_promo_art"
VOLS = ["Lascar", "PuyehueCordonCaulle", "Tupungatito", "Chaiten", "Villarrica",
        "Llaima", "PlanchonPeteroa", "Copahue", "Isluga", "Lastarria",
        "NevadosDeChillan"]
W0, W1 = "2026-01-29", "2026-06-04"
CHUNK_STARTS = ["2026-01-29", "2026-04-01"]


def _recs(o):
    return o["records"] if isinstance(o, dict) else o


def _is_modis(r):
    return str(r.get("sensor", "")).startswith("MODIS")


def _in_win(r):
    return W0 <= str(r.get("datetime_utc", ""))[:10] <= W1


def _modis_cov(recs):
    """Cobertura = nº de records MODIS en ventana (señal de under-fetch)."""
    return sum(1 for r in recs if _is_modis(r) and _in_win(r))


def _modis_dets(recs):
    return sum(1 for r in recs if _is_modis(r) and _in_win(r)
               and ((r.get("primary_cluster") or {}).get("vrp_mw", 0) or 0) > 0)


def _chunk(vol, cs):
    hits = list((ART / f"s102promo-{vol}-{cs}").glob(f"{vol}.json"))
    if not hits:
        hits = list(ART.rglob(f"s102promo-{vol}-{cs}/{vol}.json"))
    return hits[0] if hits else None


def main():
    report = []
    for vol in VOLS:
        base_path = REPO / "data/mirova_equivalent" / f"{vol}.json"
        base_obj = json.load(open(base_path, encoding="utf-8"))
        base_recs = _recs(base_obj)

        # Reproc MODIS records (ambos chunks), keyed por (datetime, sensor).
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

        # Conservar: TODO lo VIIRS + todo lo fuera de ventana. Reemplazar SOLO
        # los records MODIS en ventana por los del reproc.
        kept = [r for r in base_recs if not (_is_modis(r) and _in_win(r))]
        final = kept + repro_recs
        final.sort(key=lambda r: str(r.get("datetime_utc", "")))

        d_base = _modis_dets(base_recs)
        d_repro = _modis_dets(repro_recs)
        if isinstance(base_obj, dict):
            base_obj["records"] = final
            out = base_obj
        else:
            out = final
        json.dump(out, open(base_path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        report.append((vol, f"{len(base_recs)}->{len(final)} recs",
                       f"MODIS cov {cov_base}->{cov_repro}",
                       f"MODIS det {d_base}->{d_repro}"))

    print("=== Promoción nadir-fijo MODIS (LOCAL, guard por cobertura) ===")
    for vol, a, b, c in report:
        print(f"  {vol:<20} {a:<22} {b:<24} {c}")
    print("\nVerificar: audit R3 + preview 3 vistas (R2/R8).")
    print("Rollback: git checkout origin/main -- data/mirova_equivalent/<vol>.json")


if __name__ == "__main__":
    main()
