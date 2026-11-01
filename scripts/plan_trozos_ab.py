"""S157: plan de un A/B con todos los brazos en el mismo job: volcanes por trozos de ventana.

Lee ARM_START, ARM_END, ARM_VOLS y ARM_BRAZOS (listas JSON) y ARM_MAX_DAYS (opcional) del entorno, e imprime
`jobs=<json>` para $GITHUB_OUTPUT. Sin ARM_MAX_DAYS, el trozo mide dias_por_trozo(n_brazos), que cabe en el paso de
170 min (A15; scripts/reproc_brazos.py). Lo usa .github/workflows/reproc-s146-ab-sin-test1.yml.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.reproc_brazos import dias_por_trozo  # noqa: E402
from scripts.split_date_window import split_window  # noqa: E402


def plan(start: str, end: str, vols: list[str], brazos: list[str], max_days: int | None = None) -> list[dict]:
    if not brazos:
        raise SystemExit("ARM_BRAZOS vacio")
    md = max_days if max_days else dias_por_trozo(len(brazos))
    trozos = split_window(start, end, md)
    return [{"vol": v, "idx": t["idx"], "start": t["start"], "end": t["end"]} for v in vols for t in trozos]


def main() -> int:
    vols = json.loads(os.environ["ARM_VOLS"])
    brazos = json.loads(os.environ["ARM_BRAZOS"])
    crudo = os.environ.get("ARM_MAX_DAYS", "").strip()
    jobs = plan(os.environ["ARM_START"], os.environ["ARM_END"], vols, brazos, int(crudo) if crudo else None)
    print(f"jobs={json.dumps(jobs)}")
    print(f"{len(brazos)} brazos: {len(vols)} volcanes, {len(jobs)} jobs", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
