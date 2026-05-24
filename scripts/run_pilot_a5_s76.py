"""F31 A5 piloto S76 — reproc local 3 volcanes con perfil experimental_lowT.

Wrapper sobre `scripts/run_pipeline.py --profile experimental_lowT`. Procesa
una ventana de 30 días para los 3 volcanes candidatos del piloto VRPTIR Aveni
2025 GRL (Plan F31 Task A5):

- Lastarria (fumarolas, análogo Vulcano)
- Copahue (crater lake, análogo El Chichón)
- PlanchonPeteroa (crater lake — Aguilera 2021 ground truth Qvolc 7-59 MW)

EXCLUIDOS por diseño (perfil dice "EXCLUIR" en cabecera):
- PCC (no-focal A20, invalida single-pixel TIRVolcH)
- Lascar / Isluga (Tier A Alto >600K → Wooster MIR ya es óptimo)
- Villarrica (boundary, opcional para sesión futura)

Output: `data/experimental_lowT/<Volcano>.json` con los records normales del
pipeline + 3 campos extra del PR #158:
  - vrptir_aveni_mw
  - vrptir_aveni_n_pixels
  - vrptir_aveni_caveat

Uso (local Windows, máquina de Nicolás):
    python scripts/run_pilot_a5_s76.py
        [--days 30]              # ventana hacia atrás desde hoy
        [--volcanoes Lastarria Copahue PlanchonPeteroa]   # override default
        [--dry-run]              # solo imprime los comandos, no los ejecuta

Por qué local y no GH Actions (regla S15):
- 3 volcanes × 30 días × 1-3 granules/día × ~5-15 min/granule (fetch+process)
  ≈ 4-8 horas en serie. GH Actions timeout 50 min/step, no entra. Local sí.
- pyhdf disponible en Windows local desde S46 (instalación manual via .whl);
  MODIS sigue siendo Linux-only en pipeline, así que para Lastarria/Copahue
  vamos a usar solo VIIRS (`--sensor viirs375 viirs750`).

Validación post-corrida (cuando termine):
- Cruzar `vrptir_aveni_mw` en records de PlanchonPeteroa contra ground truth
  Aguilera 2021 (7-59 MW). Ver `docs/F31_AGUILERA_2021_PETEROA.md`.
- Si la mediana cae dentro del rango, candidato a flip operacional S78
  (con A45 obligatorio: tag defensivo + tu OK explícito).
- Si cae factor ≥5× fuera, queda en experimental y documentamos el desfasaje.

Refs:
- pipeline/profiles/experimental_lowT.yaml
- docs/F31_AVENI_VRPTIR_PLAN_S74.md
- docs/F31_AGUILERA_2021_PETEROA.md (ground truth piloto)
- tasks/BLOQUE_ARRANQUE_S76.md (P2 piloto A5)
- PR #158 (integración A2 — agrega los 3 campos al record)
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path


DEFAULT_VOLCANOES = ("Lastarria", "Copahue", "PlanchonPeteroa")
PROFILE = "experimental_lowT"
REPO_ROOT = Path(__file__).resolve().parent.parent
RUN_PIPELINE = REPO_ROOT / "scripts" / "run_pipeline.py"


def build_command(volcano: str, start: str, end: str) -> list[str]:
    """Construye la lista de args para invocar run_pipeline.py."""
    return [
        sys.executable,
        str(RUN_PIPELINE),
        "--profile", PROFILE,
        "--volcano", volcano,
        "--start", start,
        "--end", end,
    ]


def main() -> int:
    p = argparse.ArgumentParser(
        description="F31 A5 piloto VRPTIR Aveni S76 — wrapper local 3 volcanes.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--days", type=int, default=30,
                   help="Ventana hacia atras desde hoy en dias (default 30).")
    p.add_argument("--volcanoes", nargs="+", default=list(DEFAULT_VOLCANOES),
                   help=f"Volcanes a procesar (default {' '.join(DEFAULT_VOLCANOES)}).")
    p.add_argument("--dry-run", action="store_true",
                   help="Solo imprime los comandos, no los ejecuta.")
    args = p.parse_args()

    end = date.today()
    start = end - timedelta(days=args.days)
    start_s = start.isoformat()
    end_s = end.isoformat()

    print(f"\n[A5 piloto] Profile     : {PROFILE}")
    print(f"[A5 piloto] Output       : data/{PROFILE}/<Volcano>.json")
    print(f"[A5 piloto] Ventana      : {start_s} -> {end_s} ({args.days} dias)")
    print(f"[A5 piloto] Volcanes     : {', '.join(args.volcanoes)}")
    print(f"[A5 piloto] Dry-run      : {args.dry_run}")
    print(f"[A5 piloto] run_pipeline : {RUN_PIPELINE}")
    print()

    if not RUN_PIPELINE.exists():
        print(f"ERROR: no encuentro {RUN_PIPELINE}", file=sys.stderr)
        return 2

    failures: list[tuple[str, int]] = []
    for vol in args.volcanoes:
        cmd = build_command(vol, start_s, end_s)
        print(f"--- {vol} ---")
        print("  " + " ".join(cmd))
        if args.dry_run:
            continue
        rc = subprocess.call(cmd, cwd=str(REPO_ROOT))
        if rc != 0:
            print(f"  [FAIL] {vol} -> exit {rc}")
            failures.append((vol, rc))
        else:
            print(f"  [OK]   {vol}")
        print()

    if args.dry_run:
        print("\n[A5 piloto] dry-run, ningun pipeline corrido.")
        return 0

    print("\n[A5 piloto] Resumen:")
    print(f"  exito : {len(args.volcanoes) - len(failures)} / {len(args.volcanoes)}")
    for vol, rc in failures:
        print(f"  fail  : {vol} (exit {rc})")

    if failures:
        return 1
    print("\nProximo paso: cruzar data/experimental_lowT/PlanchonPeteroa.json")
    print("contra Aguilera 2021 Qvolc 7-59 MW (ver docs/F31_AGUILERA_2021_PETEROA.md).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
