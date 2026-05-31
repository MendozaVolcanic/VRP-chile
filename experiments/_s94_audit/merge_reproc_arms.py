"""S94 F2 — une los dos brazos del reproc en data/_s94_reproc/<vol>.json.

Arquitectura del reproc dividido (decisión S94, disco local 98%→ahora libre):
  - MODIS  → GitHub Actions (pyhdf), escribe data/_s94_reproc_modis/<vol>.json.
  - VIIRS  → local en Windows (sin pyhdf), escribe data/_s94_reproc_viirs/<vol>.json.

store.py deduplica por (datetime_utc, sensor), así que los records MODIS y VIIRS NO
se pisan — son claves distintas. Este script hace la UNIÓN: combina los records de
ambos brazos por volcán en data/_s94_reproc/<vol>.json, que es lo que
validate_reproc.py / viirs_magnitude_diag.py consumen.

Idempotente, solo lee los dos brazos y escribe el combinado. NO toca operacional.
  python experiments/_s94_audit/merge_reproc_arms.py
"""
import sys, os, io, json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODIS_DIR = os.path.join(REPO, "data/_s94_reproc_modis")
VIIRS_DIR = os.path.join(REPO, "data/_s94_reproc_viirs")
OUT_DIR = os.path.join(REPO, "data/_s94_reproc")
TIER_A = ["PuyehueCordonCaulle", "Villarrica", "Lascar", "Copahue", "NevadosDeChillan",
          "Llaima", "Chaiten", "PlanchonPeteroa", "Lastarria", "Isluga", "Tupungatito"]


def load_records(path):
    if not os.path.exists(path):
        return None
    d = json.load(open(path, encoding="utf-8"))
    return d["records"] if isinstance(d, dict) and "records" in d else d


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"{'Volcán':<20}{'MODIS':>8}{'VIIRS':>8}{'combinado':>11}")
    for vol in TIER_A:
        m = load_records(os.path.join(MODIS_DIR, f"{vol}.json"))
        v = load_records(os.path.join(VIIRS_DIR, f"{vol}.json"))
        if m is None and v is None:
            continue
        by_key = {}
        for rec in (m or []) + (v or []):
            key = (rec.get("datetime_utc"), rec.get("sensor"))
            by_key[key] = rec  # claves disjuntas entre brazos; si colisión, último gana
        merged = sorted(by_key.values(), key=lambda r: (r.get("datetime_utc") or "", r.get("sensor") or ""))
        out = {"volcano": vol, "records": merged}
        json.dump(out, open(os.path.join(OUT_DIR, f"{vol}.json"), "w", encoding="utf-8"),
                  indent=2, ensure_ascii=False)
        print(f"{vol:<20}{len(m or []):>8}{len(v or []):>8}{len(merged):>11}")
    print(f"\nCombinado → {OUT_DIR}/  (consumir con validate_reproc.py)")


if __name__ == "__main__":
    main()
