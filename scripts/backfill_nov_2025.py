"""
backfill_nov_2025.py — S15 Paso 1b reproceso masivo para cross-match OSF v2.5.

Descarga y procesa VIIRS (375m + 750m) para 4 volcanes chilenos Tier A/B
durante todo noviembre 2025. Output separado del operacional:
`data/mirova_equivalent_backfill_nov2025/<Volcano>.json`.

Volcanes:   Lascar, Villarrica, Copahue, Chaiten  (30 días × 4 = 120 combos)
Sensores:   VIIRS SNPP + NOAA-20 (I-band 375m + M-band 750m). Sin MODIS
            (pyhdf roto en Windows — MODIS corre en Actions Linux).
Patrón:     fetch-process-delete granule-por-granule (herencia de process_date).
            Pico de disco ~100 MB. Tráfico total ~24 GB.

Uso:
    python scripts/backfill_nov_2025.py               # 30 días × 4 volcanes
    python scripts/backfill_nov_2025.py --smoke       # 1 día × 1 volcán (dry-run)
    python scripts/backfill_nov_2025.py --volcano Lascar --start 2025-11-01 --end 2025-11-03

Requiere: ~/.netrc con credenciales Earthdata válidas (validado S14).
"""

import argparse
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Lock profile ANTES de importar pipeline (igual que run_pipeline.py).
os.environ["VRP_PROFILE"] = "mirova_equivalent_backfill_nov2025"

# .env opcional para EARTHDATA_* (override ~/.netrc si está)
def _load_env():
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())
_load_env()

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.run_pipeline import process_date, load_volcanoes  # noqa: E402
from pipeline import profile as vrp_profile  # noqa: E402


BACKFILL_VOLCANOES = ["Lascar", "Villarrica", "Copahue", "Chaiten"]
BACKFILL_START = datetime(2025, 11, 1)
BACKFILL_END = datetime(2025, 11, 30)


def date_range(start: datetime, end: datetime):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def main():
    p = argparse.ArgumentParser(description="S15 Paso 1b backfill Nov 2025")
    p.add_argument("--smoke", action="store_true",
                   help="Dry-run: 1 día × 1 volcán (Lascar 2025-11-15)")
    p.add_argument("--volcano", help="Restringir a un solo volcán")
    p.add_argument("--start", help="YYYY-MM-DD override start")
    p.add_argument("--end", help="YYYY-MM-DD override end")
    args = p.parse_args()

    # Safety: el profile debe haber cargado con data_subdir separado.
    assert vrp_profile.DATA_SUBDIR == "mirova_equivalent_backfill_nov2025", (
        f"Profile mal cargado: DATA_SUBDIR={vrp_profile.DATA_SUBDIR}. "
        "El backfill NO debe escribir sobre data operacional."
    )
    print(f"=== {vrp_profile.describe()} ===")

    if args.smoke:
        volcano_names = ["Lascar"]
        dates = [datetime(2025, 11, 15)]
        print("SMOKE TEST: Lascar 2025-11-15 (1 día, 1 volcán)")
    else:
        volcano_names = [args.volcano] if args.volcano else BACKFILL_VOLCANOES
        start = datetime.strptime(args.start, "%Y-%m-%d") if args.start else BACKFILL_START
        end = datetime.strptime(args.end, "%Y-%m-%d") if args.end else BACKFILL_END
        dates = list(date_range(start, end))

    volcanoes = [v for v in load_volcanoes() if v["name"] in volcano_names]
    missing = set(volcano_names) - {v["name"] for v in volcanoes}
    if missing:
        print(f"ERROR: volcanes no encontrados en volcanoes.yaml: {missing}")
        sys.exit(1)

    total = len(volcanoes) * len(dates)
    print(f"Total combos: {len(volcanoes)} volcanes × {len(dates)} días = {total}")

    i = 0
    for volcano in volcanoes:
        for date in dates:
            i += 1
            print(f"\n[{i}/{total}] {volcano['name']} {date.date()}")
            try:
                process_date(volcano, date, nighttime_only=True,
                             skip_noaa20=False, overwrite=True)
            except Exception as e:
                print(f"  FAIL {volcano['name']} {date.date()}: {e}")
                # Continuar con el siguiente — backfill tolera huecos.

    print("\nBackfill Nov 2025 completo.")


if __name__ == "__main__":
    main()
