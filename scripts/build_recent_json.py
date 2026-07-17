#!/usr/bin/env python3
"""Genera JSONs "recientes" livianos por volcán para la carga inicial del dashboard.

POR QUÉ (fenómeno → mecanismo): el backfill histórico (S120) llevó los JSONs
operacionales a 13-17 MB cada uno. El dashboard carga los 11 Tier A en paralelo
(~171 MB) → en red real los fetches timeoutean (>30s por archivo) y el mapa/tabla
quedan vacíos aunque el deploy sea exitoso. La vista por defecto solo muestra 30
días, así que no necesita bajar años de historia.

Este script escribe `<vol>_recent.json` con solo los últimos RECENT_DAYS días. El
frontend lo carga por defecto (~8-10 MB total) y baja el `<vol>.json` completo solo
si el usuario pide >90 días. NO toca el pipeline de detección ni los JSONs completos
del repo — es solo re-empaquetado para el display (misión: clon literal intacto).

Se ejecuta en pages-deploy.yml sobre `_site/data/` (el artefacto publicado), NO
sobre el repo. Idempotente.

Uso:
    python scripts/build_recent_json.py --data-dir _site/data/mirova_equivalent
    python scripts/build_recent_json.py --data-dir _site/data/mirova_equivalent --days 100
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

RECENT_DAYS = 100  # cubre el toggle de 90 días del dashboard con margen


def parse_dt(s: str) -> datetime | None:
    """datetime_utc del pipeline: 'YYYY-MM-DD HH:MM' (UTC). Tolerante a 'T' y sufijos."""
    if not s:
        return None
    t = str(s).strip().replace("T", " ")[:16]
    try:
        return datetime.strptime(t, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    except ValueError:
        try:
            return datetime.strptime(t[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            return None


def filter_recent(doc: dict, cutoff: datetime) -> dict:
    """Devuelve una copia del doc con solo los records >= cutoff. Conserva metadata."""
    recs = doc.get("records", []) if isinstance(doc, dict) else doc
    kept = [r for r in recs
            if (dt := parse_dt(r.get("datetime_utc", ""))) is not None and dt >= cutoff]
    if isinstance(doc, dict):
        out = dict(doc)
        out["records"] = kept
        out["_recent_window_days"] = RECENT_DAYS  # marca para el frontend / debug
        return out
    return {"records": kept, "_recent_window_days": RECENT_DAYS}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True,
                    help="dir con los <vol>.json (ej. _site/data/mirova_equivalent)")
    ap.add_argument("--days", type=int, default=RECENT_DAYS)
    ap.add_argument("--now", default=None,
                    help="ISO override para tests (ej. 2026-07-16); default = ahora UTC")
    args = ap.parse_args()

    data_dir = Path(args.data_dir)
    if not data_dir.is_dir():
        print(f"ERROR: no existe {data_dir}", file=sys.stderr)
        return 2

    now = (datetime.fromisoformat(args.now).replace(tzinfo=timezone.utc)
           if args.now else datetime.now(timezone.utc))
    cutoff = now - timedelta(days=args.days)

    total_in = total_out = n_files = 0
    for jf in sorted(data_dir.glob("*.json")):
        if jf.stem.endswith("_recent"):
            continue
        try:
            doc = json.loads(jf.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            print(f"  skip {jf.name}: {e}", file=sys.stderr)
            continue
        recent = filter_recent(doc, cutoff)
        out_path = jf.with_name(f"{jf.stem}_recent.json")
        out_path.write_text(json.dumps(recent, ensure_ascii=False, separators=(",", ":")),
                            encoding="utf-8")
        n_in = len(doc.get("records", []) if isinstance(doc, dict) else doc)
        n_out = len(recent["records"])
        total_in += n_in
        total_out += n_out
        n_files += 1
        mb_full = jf.stat().st_size / 1048576
        mb_recent = out_path.stat().st_size / 1048576
        print(f"  {jf.stem:<22} {n_out:>5}/{n_in:<6} records  "
              f"{mb_recent:>5.1f}/{mb_full:<5.1f} MB")

    print(f"\n{n_files} archivos · {total_out}/{total_in} records retenidos "
          f"(ventana {args.days}d, cutoff {cutoff:%Y-%m-%d})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
