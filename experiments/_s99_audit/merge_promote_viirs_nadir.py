"""S103 — Promoción nadir-fijo VIIRS a data/mirova_equivalent (LOCAL, sin commit).

Espejo de merge_promote_nadir.py (S102 MODIS), con el predicado de sensor
INVERTIDO. Lee los artifacts del reproc-s103-viirs-nadir-promote (11 vols x 2
chunks, perfil _s103_viirs_nadir_promote = mirova_equivalent ya flipeado:
nadir-fijo VIIRS + ctxpeak + pisos VIIRS).

ALCANCE: solo se promueven los records **VIIRS** (375 + 750) dentro de la ventana
[2026-01-29 .. 2026-06-07]. Los records **MODIS** del base quedan INTACTOS
(byte-idénticos: ya fueron promovidos a nadir en S102; este fix es VIIRS-only).
Los records fuera de ventana también se conservan. El script VERIFICA que el
conteo MODIS no cambie (byte-identidad por construcción: se conservan los mismos
objetos del base).

GUARD anti-underfetch (#345): el riesgo real es que el reproc haya bajado MENOS
granules VIIRS que el base (cobertura NASA distinta) -> perdería records reales.
Se mide por COBERTURA = total de records VIIRS en la ventana (no por detecciones,
que cambian legítimamente con el área nadir). Si el reproc tiene MENOS records
VIIRS que el base -> SKIP ese vol con WARN.

Uso:
  gh run download <RUN_ID> -D experiments/_s99_audit/_s103_viirs_promo_art
  python experiments/_s99_audit/merge_promote_viirs_nadir.py
Luego: audit (R3) + preview 3 vistas (R2/R8) -> si OK commit+push.
Rollback: git checkout pre-s103-nadir-fixed-viirs -- data/mirova_equivalent/<vol>.json
"""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ART = REPO / "experiments/_s99_audit/_s103_viirs_promo_art"
VOLS = ["Lascar", "PuyehueCordonCaulle", "Tupungatito", "Chaiten", "Villarrica",
        "Llaima", "PlanchonPeteroa", "Copahue", "Isluga", "Lastarria",
        "NevadosDeChillan"]
W0, W1 = "2026-01-29", "2026-06-07"
CHUNK_STARTS = ["2026-01-29", "2026-04-01"]


def _recs(o):
    return o["records"] if isinstance(o, dict) else o


def _is_viirs(r):
    return str(r.get("sensor", "")).startswith("VIIRS")


def _is_modis(r):
    return str(r.get("sensor", "")).startswith("MODIS")


def _in_win(r):
    return W0 <= str(r.get("datetime_utc", ""))[:10] <= W1


def _viirs_cov(recs):
    """Cobertura = nº de records VIIRS en ventana (señal de under-fetch)."""
    return sum(1 for r in recs if _is_viirs(r) and _in_win(r))


def _viirs_dets(recs):
    return sum(1 for r in recs if _is_viirs(r) and _in_win(r)
               and ((r.get("primary_cluster") or {}).get("vrp_mw", 0) or 0) > 0)


def _chunk(vol, cs):
    hits = list((ART / f"s103viirspromo-{vol}-{cs}").glob(f"{vol}.json"))
    if not hits:
        hits = list(ART.rglob(f"s103viirspromo-{vol}-{cs}/{vol}.json"))
    return hits[0] if hits else None


def main():
    report = []
    for vol in VOLS:
        base_path = REPO / "data/mirova_equivalent" / f"{vol}.json"
        base_obj = json.load(open(base_path, encoding="utf-8"))
        base_recs = _recs(base_obj)

        # Reproc VIIRS records (ambos chunks), keyed por (datetime, sensor).
        repro_viirs = {}
        missing = []
        for cs in CHUNK_STARTS:
            jf = _chunk(vol, cs)
            if jf is None:
                missing.append(cs)
                continue
            for r in _recs(json.load(open(jf, encoding="utf-8"))):
                if _is_viirs(r) and _in_win(r):
                    repro_viirs[(r.get("datetime_utc"), r.get("sensor"))] = r
        if missing:
            report.append((vol, f"SKIP — faltan chunks {missing}", "", ""))
            continue

        repro_recs = list(repro_viirs.values())
        cov_base = _viirs_cov(base_recs)
        cov_repro = len(repro_recs)
        if cov_repro < cov_base:
            report.append((vol, f"SKIP — under-fetch VIIRS ({cov_repro}<{cov_base} cov)", "", ""))
            continue

        # Conservar: TODO lo MODIS + todo lo VIIRS fuera de ventana. Reemplazar
        # SOLO los records VIIRS en ventana por los del reproc.
        kept = [r for r in base_recs if not (_is_viirs(r) and _in_win(r))]
        final = kept + repro_recs
        final.sort(key=lambda r: str(r.get("datetime_utc", "")))

        # Verificación byte-identidad MODIS: el conteo MODIS no debe cambiar.
        modis_base = sum(1 for r in base_recs if _is_modis(r))
        modis_final = sum(1 for r in final if _is_modis(r))
        if modis_base != modis_final:
            report.append((vol, f"SKIP — MODIS count cambió {modis_base}!={modis_final}", "", ""))
            continue

        d_base = _viirs_dets(base_recs)
        d_repro = _viirs_dets(repro_recs)
        if isinstance(base_obj, dict):
            base_obj["records"] = final
            out = base_obj
        else:
            out = final
        json.dump(out, open(base_path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        report.append((vol, f"{len(base_recs)}->{len(final)} recs",
                       f"VIIRS cov {cov_base}->{cov_repro}",
                       f"VIIRS det {d_base}->{d_repro} | MODIS {modis_base} intacto"))

    print("=== Promoción nadir-fijo VIIRS (LOCAL, guard por cobertura, MODIS byte-idéntico) ===")
    for vol, a, b, c in report:
        print(f"  {vol:<20} {a:<24} {b:<24} {c}")
    print("\nVerificar: audit R3 + preview 3 vistas (R2/R8).")
    print("Rollback: git checkout pre-s103-nadir-fixed-viirs -- data/mirova_equivalent/<vol>.json")


if __name__ == "__main__":
    main()
