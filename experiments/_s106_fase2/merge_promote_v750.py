"""S108 — Promoción del ancla espacial honesta VIIRS750 a data/mirova_equivalent.

Espejo de merge_promote_honest_anchor.py (V375, S106). Lee el reproc flag-ON del
A/B V750 (run 27468739388, 5 vols en experiments/_s106_fase2/_v750_staging/
s106v750-<vol>-<chunk>/<vol>.json) y promueve SOLO los records VIIRS750 dentro de
[2026-01-29 .. 2026-06-08].

ALCANCE: solo records VIIRS750 (sensor *_750) de los 5 vols del A/B. MODIS y V375
del base quedan INTACTOS (el flag enable_honest_anchor_viirs750 solo toca el bloque
de posición de process_viirs_mod.py; V375 tiene su flag separado ya promovido S106).
Los 6 Tier A restantes (Isluga/Chaiten/Copahue/NdC/PP/PCC) quedan PENDIENTES de su
propio reproc V750 (espejo del run S106 27422803708 que cubrió V375).

CRITERIO (S108 audit_v750_paired.py): el ancla SOLO toca posición — verificado en el
código (anchor.py: helper puro; diff path-magnitud V750 desde #401 = +157/-0, todo
gateado). La magnitud del reproc-Standard es >= autoritativa que el disco-NRT
(store.py auto-upgrade NRT->Standard), así que la unión MEJORA fidelidad en granules
borderline (ej. Villarrica 06-07 lava lake: 4.82 MW NRT -> 0.03 MW Standard).

GUARD anti-underfetch (#345/S103): cobertura V750 del reproc >= base o SKIP.

Uso: python experiments/_s106_fase2/merge_promote_v750.py
Luego: audit R3 + preview (R8) -> commit+push.
Rollback: git checkout pre-s108-honest-anchor-v750 -- data/mirova_equivalent/<vol>.json
"""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
AB_STAGING = REPO / "experiments/_s106_fase2/_v750_staging"
AB_VOLS = ["Tupungatito", "Villarrica", "Llaima", "Lascar", "Lastarria"]
REST_VOLS = ["Isluga", "Chaiten", "Copahue", "NevadosDeChillan",
             "PlanchonPeteroa", "PuyehueCordonCaulle"]
W0, W1 = "2026-01-29", "2026-06-08"
CHUNK_STARTS = ["2026-01-29", "2026-04-01"]


def _recs(o):
    return o["records"] if isinstance(o, dict) else o


def _is_v750(r):
    return str(r.get("sensor", "")).endswith("750")


def _in_win(r):
    return W0 <= str(r.get("datetime_utc", ""))[:10] <= W1


def _cov(recs):
    return sum(1 for r in recs if _is_v750(r) and _in_win(r))


def _dets(recs):
    return sum(1 for r in recs if _is_v750(r) and _in_win(r)
               and ((r.get("primary_cluster") or {}).get("vrp_mw", 0) or 0) > 0)


def _chunk_file(vol, cs):
    f = AB_STAGING / f"s106v750-{vol}-{cs}" / f"{vol}.json"
    return f if f.exists() else None


def main():
    report = []
    for vol in AB_VOLS:
        base_path = REPO / "data/mirova_equivalent" / f"{vol}.json"
        base_obj = json.load(open(base_path, encoding="utf-8"))
        base_recs = _recs(base_obj)

        repro_v750, missing = {}, []
        for cs in CHUNK_STARTS:
            jf = _chunk_file(vol, cs)
            if jf is None:
                missing.append(cs)
                continue
            for r in _recs(json.load(open(jf, encoding="utf-8"))):
                if _is_v750(r) and _in_win(r):
                    repro_v750[(r.get("datetime_utc"), r.get("sensor"))] = r
        if missing:
            report.append((vol, f"SKIP — faltan chunks {missing}", "", ""))
            continue

        repro_recs = list(repro_v750.values())
        cov_base, cov_repro = _cov(base_recs), len(repro_recs)
        if cov_repro < cov_base:  # guard anti-underfetch
            report.append((vol, f"SKIP — cobertura {cov_repro}<{cov_base} (underfetch)",
                           "", ""))
            continue

        # UNIÓN (precedente S101/S106): reemplazar solo los records cuyo
        # (datetime, sensor) está en el reproc; conservar legacy lo que NASA no
        # entregó (el ancla no cambia detección — paridad verificada S108).
        kept = [r for r in base_recs
                if not (_is_v750(r) and _in_win(r)
                        and (r.get("datetime_utc"), r.get("sensor")) in repro_v750)]
        n_legacy = sum(1 for r in kept if _is_v750(r) and _in_win(r))
        final = kept + repro_recs
        final.sort(key=lambda r: str(r.get("datetime_utc", "")))

        n_other_base = sum(1 for r in base_recs if not _is_v750(r))
        n_other_final = sum(1 for r in final if not _is_v750(r))
        if n_other_base != n_other_final:
            report.append((vol, f"SKIP — no-V750 cambió {n_other_base}!={n_other_final}",
                           "", ""))
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
                       f"V750 cov {cov_base}->{cov_repro} (+{n_legacy} legacy)",
                       f"dets {d_base}->{d_repro} | no-V750 {n_other_base} intacto"))

    print("=== Promoción ancla honesta V750 (guard cobertura, MODIS/V375 intactos) ===")
    for vol, a, b, c in report:
        print(f"  {vol:<20} {a:<28} {b:<26} {c}")
    print(f"\nPENDIENTE reproc V750 (no promovidos): {', '.join(REST_VOLS)}")
    print("Rollback: git checkout pre-s108-honest-anchor-v750 -- data/mirova_equivalent/<vol>.json")


if __name__ == "__main__":
    main()
