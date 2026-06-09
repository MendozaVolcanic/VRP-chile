"""S104 V2 — mergea los 2 chunks de un brazo A/B en un <vol>.json por volcán.

Cada job del A/B corre con --overwrite sobre su rango de fechas, así que cada
artifact tiene SOLO los records de su chunk. Los rangos no se solapan
(2026-01-29..03-31 y 04-01..06-08), así que el merge es concatenación + dedup
por (sensor, datetime_utc) por las dudas.

Uso: python merge_chunks.py <dir_staging> <dir_salida>
  dir_staging/<vol>/<chunk>/<vol>.json  →  dir_salida/<vol>.json
"""
import sys, json
from pathlib import Path

VOLS = ["Tupungatito", "Villarrica", "Llaima", "Lascar", "Lastarria"]


def recs_of(obj):
    return obj.get("records", []) if isinstance(obj, dict) else obj


def main(staging, out):
    staging, out = Path(staging), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for vol in VOLS:
        merged, seen, meta = [], set(), None
        for chunk in sorted((staging / vol).glob("*")):
            f = chunk / f"{vol}.json"
            if not f.exists():
                continue
            obj = json.load(open(f, encoding="utf-8"))
            if meta is None and isinstance(obj, dict):
                meta = {k: v for k, v in obj.items() if k != "records"}
            for r in recs_of(obj):
                key = (r.get("sensor"), r.get("datetime_utc"))
                if key in seen:
                    continue
                seen.add(key)
                merged.append(r)
        merged.sort(key=lambda r: r.get("datetime_utc") or "")
        payload = ({**(meta or {}), "records": merged}) if meta is not None else merged
        json.dump(payload, open(out / f"{vol}.json", "w", encoding="utf-8"))
        print(f"{vol:<14} {len(merged):>5} records")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
