"""S106 — Cobertura reproc rest-6 vs PRODUCCIÓN (robusto, A64-reproc).

Truncamiento real = el reproc tiene MENOS granules VIIRS375 que producción en la
ventana. Ausencia legítima de pasadas = ambos coinciden. Compara por (datetime,
sensor) keys, no por calendario.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / "experiments/_s106_fase2/_rest_art"
W0, W1 = "2026-01-29", "2026-06-08"
VOLS = ["Isluga", "Chaiten", "Copahue", "NevadosDeChillan",
        "PlanchonPeteroa", "PuyehueCordonCaulle"]


def recs(p):
    obj = json.load(open(p, encoding="utf-8"))
    return obj.get("records", obj) if isinstance(obj, dict) else obj


def v375_keys(rs):
    out = set()
    for r in rs:
        s = str(r.get("sensor", ""))
        d = (r.get("datetime_utc") or "")[:10]
        if s.startswith("VIIRS") and not s.endswith("750") and W0 <= d <= W1:
            out.add((r.get("datetime_utc"), s))
    return out


print(f"{'vol':<20}{'prod V375':>10}{'reproc':>8}{'falta':>7}{'extra':>7}  veredicto")
for vol in VOLS:
    prod = v375_keys(recs(ROOT / "data/mirova_equivalent" / f"{vol}.json"))
    rep = set()
    for d in ART.glob(f"s106rest-{vol}-*"):
        f = d / f"{vol}.json"
        if f.exists():
            rep |= v375_keys(recs(f))
    falta = len(prod - rep)
    extra = len(rep - prod)
    pct = 100 * falta / max(len(prod), 1)
    verd = "OK (union cubre)" if falta == 0 else (
        f"reproc corto {pct:.0f}% -> union conserva prod en esos" if falta else "")
    print(f"{vol:<20}{len(prod):>10}{len(rep):>8}{falta:>7}{extra:>7}  {verd}")
