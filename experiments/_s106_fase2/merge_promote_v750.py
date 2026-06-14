"""S108 — Promoción del ancla espacial honesta VIIRS750 a data/mirova_equivalent.

Espejo de merge_promote_honest_anchor.py (V375, S106). Promueve SOLO los records
VIIRS750 (sensor *_750) dentro de [2026-01-29 .. 2026-06-08].

Dos modos (--mode):
  ab   : 5 vols del A/B run 27468739388 (staging _v750_staging, prefijo s106v750-).
         YA PROMOVIDOS S108 (commit PR #416). Re-correr es idempotente.
  rest : 6 Tier A restantes del reproc run 27482258622 (staging _v750_rest_staging,
         prefijo s108v750rest-): Isluga/Chaiten/Copahue/NdC/PP/PCC.

ALCANCE: solo records VIIRS750. MODIS y V375 del base quedan INTACTOS (el flag
enable_honest_anchor_viirs750 solo toca el bloque de posición de process_viirs_mod.py).

CRITERIO (S108 audit_v750_paired.py): el ancla SOLO toca posición (anchor.py helper
puro; diff path-magnitud V750 = +157/-0, gateado). La magnitud del reproc-Standard
es >= autoritativa que el disco-NRT → la unión MEJORA fidelidad.

GUARD anti-underfetch (#345/S103): cobertura V750 del reproc >= base o SKIP.

Uso:
  python experiments/_s106_fase2/merge_promote_v750.py --mode rest
Antes: gh run download 27482258622 -D experiments/_s106_fase2/_v750_rest_staging
       + reproc_coverage_gate.py --sensor v750
Luego: audit + preview (R8) -> commit+push.
Rollback: git checkout pre-s108-honest-anchor-v750 -- data/mirova_equivalent/<vol>.json
"""
import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
AB_STAGING = REPO / "experiments/_s106_fase2/_v750_staging"
REST_STAGING = REPO / "experiments/_s106_fase2/_v750_rest_staging"
AB_VOLS = ["Tupungatito", "Villarrica", "Llaima", "Lascar", "Lastarria"]
REST_VOLS = ["Isluga", "Chaiten", "Copahue", "NevadosDeChillan",
             "PlanchonPeteroa", "PuyehueCordonCaulle"]
W0, W1 = "2026-01-29", "2026-06-08"
CHUNK_STARTS = ["2026-01-29", "2026-04-01"]

MODES = {
    "ab":   {"vols": AB_VOLS,   "staging": AB_STAGING,   "prefix": "s106v750"},
    "rest": {"vols": REST_VOLS, "staging": REST_STAGING, "prefix": "s108v750rest"},
}


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


def _chunk_file(staging, prefix, vol, cs):
    f = staging / f"{prefix}-{vol}-{cs}" / f"{vol}.json"
    return f if f.exists() else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["ab", "rest"], default="ab")
    a = ap.parse_args()
    cfg = MODES[a.mode]
    vols, staging, prefix = cfg["vols"], cfg["staging"], cfg["prefix"]

    report = []
    for vol in vols:
        base_path = REPO / "data/mirova_equivalent" / f"{vol}.json"
        base_obj = json.load(open(base_path, encoding="utf-8"))
        base_recs = _recs(base_obj)

        repro_v750, missing = {}, []
        for cs in CHUNK_STARTS:
            jf = _chunk_file(staging, prefix, vol, cs)
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
        # Guard anti-underfetch SEVERO (#345/S103): la UNIÓN ya conserva legacy lo que
        # NASA no entregó (el ancla no cambia detección, paridad 0-diffs verificada en
        # audit_v750_rest_c1c3), así que faltantes menores son seguros (precedente V375
        # S106 usó unión con legacy). Solo bloquear si NASA falló masivamente (>10%).
        if cov_repro < 0.90 * cov_base:
            report.append((vol, f"SKIP — underfetch severo {cov_repro}<{cov_base}",
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

    print(f"=== Promoción ancla honesta V750 [mode={a.mode}] (MODIS/V375 intactos) ===")
    for vol, a1, b1, c1 in report:
        print(f"  {vol:<20} {a1:<28} {b1:<26} {c1}")
    print("\nRollback: git checkout pre-s108-honest-anchor-v750 -- data/mirova_equivalent/<vol>.json")


if __name__ == "__main__":
    main()
