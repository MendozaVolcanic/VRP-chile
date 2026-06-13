"""S106 — Auditar cobertura de fechas de los artifacts rest-6 (lección A64-reproc).

Un job puede salir conclusion=success pero con data truncada si el circuit-breaker
toleró un host NASA caído. Verificar que cada chunk cubra su rango antes de promover.
"""
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parents[2] / "experiments/_s106_fase2/_rest_art"
EXP_END = {"2026-01-29": "2026-03-29", "2026-04-01": "2026-06-06"}  # fin mínimo

for d in sorted(BASE.iterdir()):
    if not d.is_dir():
        continue
    m = re.match(r"s106rest-(\w+)-(.+)", d.name)
    if not m:
        continue
    vol, cs = m.groups()
    f = d / f"{vol}.json"
    if not f.exists():
        print(f"{d.name}: SIN JSON")
        continue
    obj = json.load(open(f, encoding="utf-8"))
    recs = obj.get("records", obj) if isinstance(obj, dict) else obj
    dates = sorted({(r.get("datetime_utc") or "")[:10]
                    for r in recs if r.get("datetime_utc")})
    lo, hi = (dates[0], dates[-1]) if dates else ("-", "-")
    flag = "" if (dates and hi >= EXP_END.get(cs, "9999")) else "  <-- TRUNCADO"
    print(f"{vol:<20}{cs}  n={len(recs):>4}  {lo}..{hi}{flag}")
