"""S106 — Promoción del ancla espacial honesta (VIIRS375) a data/mirova_equivalent.

Adaptación de merge_promote_viirs_nadir.py (S103). Lee los reprocs flag-ON del
brazo A ganador del A/B (run 27343409067, 5 vols, ya en
experiments/_s104_roi_probe/_staging_anchor_a/) y del run de los 6 Tier A
restantes (run 27422803708, artifacts s106rest-<vol>-<chunk> descargados a
experiments/_s106_fase2/_rest_art/).

ALCANCE: solo se promueven los records **VIIRS375** (sensor VIIRS_* sin sufijo
_750) dentro de la ventana [2026-01-29 .. 2026-06-08]. MODIS y VIIRS750 del base
quedan INTACTOS (el flag enable_honest_anchor solo toca process_viirs.py; los
espejos MODIS/V750 tienen flags separados OFF). Records fuera de ventana se
conservan (NRT 06-09+ queda legacy hasta el próximo ciclo natural).

GUARD anti-underfetch (#345/S103): cobertura V375 del reproc >= base o SKIP.

Uso:
  python experiments/_s106_fase2/merge_promote_honest_anchor.py
Luego: audit R3 + preview (R8) -> commit+push.
Rollback: git checkout pre-s106-honest-anchor -- data/mirova_equivalent/<vol>.json
"""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
AB_STAGING = REPO / "experiments/_s104_roi_probe/_staging_anchor_a"
REST_ART = REPO / "experiments/_s106_fase2/_rest_art"
AB_VOLS = ["Tupungatito", "Villarrica", "Llaima", "Lascar", "Lastarria"]
REST_VOLS = ["Isluga", "Chaiten", "Copahue", "NevadosDeChillan",
             "PlanchonPeteroa", "PuyehueCordonCaulle"]
W0, W1 = "2026-01-29", "2026-06-08"
CHUNK_STARTS = ["2026-01-29", "2026-04-01"]


def _recs(o):
    return o["records"] if isinstance(o, dict) else o


def _is_v375(r):
    s = str(r.get("sensor", ""))
    return s.startswith("VIIRS") and not s.endswith("750")


def _in_win(r):
    return W0 <= str(r.get("datetime_utc", ""))[:10] <= W1


def _cov(recs):
    return sum(1 for r in recs if _is_v375(r) and _in_win(r))


def _dets(recs):
    return sum(1 for r in recs if _is_v375(r) and _in_win(r)
               and ((r.get("primary_cluster") or {}).get("vrp_mw", 0) or 0) > 0)


def _chunk_file(vol, cs):
    if vol in AB_VOLS:
        f = AB_STAGING / vol / cs / f"{vol}.json"
        return f if f.exists() else None
    f = REST_ART / f"s106rest-{vol}-{cs}" / f"{vol}.json"
    return f if f.exists() else None


def main():
    report = []
    for vol in AB_VOLS + REST_VOLS:
        base_path = REPO / "data/mirova_equivalent" / f"{vol}.json"
        base_obj = json.load(open(base_path, encoding="utf-8"))
        base_recs = _recs(base_obj)

        repro_v375, missing = {}, []
        for cs in CHUNK_STARTS:
            jf = _chunk_file(vol, cs)
            if jf is None:
                missing.append(cs)
                continue
            for r in _recs(json.load(open(jf, encoding="utf-8"))):
                if _is_v375(r) and _in_win(r):
                    repro_v375[(r.get("datetime_utc"), r.get("sensor"))] = r
        if missing:
            report.append((vol, f"SKIP — faltan chunks {missing}", "", ""))
            continue

        repro_recs = list(repro_v375.values())
        cov_base, cov_repro = _cov(base_recs), len(repro_recs)

        # UNIÓN (precedente S101 Llaima #345): reemplazar solo los records cuyo
        # (datetime, sensor) está en el reproc; conservar del base los granules
        # que NASA no entregó en esta corrida (quedan con ancla legacy — el
        # ancla no cambia detección, paridad verificada 0-diffs pareados §8).
        kept = [r for r in base_recs
                if not (_is_v375(r) and _in_win(r)
                        and (r.get("datetime_utc"), r.get("sensor")) in repro_v375)]
        n_legacy = sum(1 for r in kept if _is_v375(r) and _in_win(r))
        final = kept + repro_recs
        final.sort(key=lambda r: str(r.get("datetime_utc", "")))

        n_other_base = sum(1 for r in base_recs if not _is_v375(r))
        n_other_final = sum(1 for r in final if not _is_v375(r))
        if n_other_base != n_other_final:
            report.append((vol, f"SKIP — no-V375 cambió {n_other_base}!={n_other_final}", "", ""))
            continue

        d_base, d_repro = _dets(base_recs), _dets(repro_recs)
        if isinstance(base_obj, dict):
            base_obj["records"] = final
            out = base_obj
        else:
            out = final
        json.dump(out, open(base_path, "w", encoding="utf-8"), indent=2,
                  ensure_ascii=False)
        report.append((vol, f"{len(base_recs)}->{len(final)} recs",
                       f"V375 cov {cov_base}->{cov_repro} (+{n_legacy} legacy)",
                       f"dets {d_base}->{d_repro} | no-V375 {n_other_base} intacto"))

    print("=== Promoción ancla honesta V375 (guard cobertura, MODIS/V750 intactos) ===")
    for vol, a, b, c in report:
        print(f"  {vol:<20} {a:<24} {b:<24} {c}")
    print("\nRollback: git checkout pre-s106-honest-anchor -- data/mirova_equivalent/<vol>.json")


if __name__ == "__main__":
    main()
