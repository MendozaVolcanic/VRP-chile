"""
run_pipeline.py — Main entry point for the VRP processing pipeline.

Usage:
    # Process all active volcanoes for today
    python scripts/run_pipeline.py

    # Process specific volcano and date
    python scripts/run_pipeline.py --volcano PuyehueCordonCaulle --date 2024-03-14

    # Process date range
    python scripts/run_pipeline.py --volcano PuyehueCordonCaulle --start 2024-01-01 --end 2024-03-14

Environment variables required (set in .env or GitHub secrets):
    EARTHDATA_USERNAME
    EARTHDATA_PASSWORD
"""

import argparse
import os

# Load .env file if present (before any other imports that need credentials)
def _load_env():
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    env_path = os.path.abspath(env_path)
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    os.environ.setdefault(key.strip(), val.strip())

_load_env()
import shutil
import sys
import yaml
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline import fetch, process_modis, process_viirs, process_viirs_mod, store


TMP_DIR = Path(__file__).parent.parent / "tmp"
VOLCANOES_FILE = Path(__file__).parent.parent / "volcanoes.yaml"


def load_volcanoes(name_filter: str = None) -> list:
    with open(VOLCANOES_FILE) as f:
        cfg = yaml.safe_load(f)
    volcanoes = [v for v in cfg["volcanoes"] if v.get("active", True)]
    if name_filter:
        volcanoes = [v for v in volcanoes if v["name"] == name_filter]
    return volcanoes


def process_date(volcano: dict, date: datetime):
    """Download and process all granules for a volcano on a given date."""
    print(f"\n>>> {volcano['display_name']} | {date.strftime('%Y-%m-%d')}")

    volcano_tmp = TMP_DIR / volcano["name"] / date.strftime("%Y%m%d")

    try:
        granule_paths = fetch.fetch_for_volcano(volcano, date, volcano_tmp)

        for platform, paths in granule_paths.items():
            if not paths:
                continue

            # Separate L1B and geolocation files
            if "MODIS" in platform:
                l1b_files = [p for p in paths if "MOD021KM" in p.name or "MYD021KM" in p.name]
                geo_files = [p for p in paths if "MOD03" in p.name or "MYD03" in p.name]
                geo_by_time = {_time_key(g.name): g for g in geo_files}

                for l1b in l1b_files:
                    geo = geo_by_time.get(_time_key(l1b.name))
                    if geo is None:
                        print(f"  No geolocation match for {l1b.name}")
                        continue
                    result = process_modis.calculate_vrp(
                        l1b, geo, volcano["lat"], volcano["lon"], volcano["radius_km"]
                    )
                    if result:
                        store.append_record(volcano["name"], result)
                        print(f"  {result['sensor']} | VRP={result['vrp_mw']} MW | "
                              f"T_bg={result['t_bg_k']} K | T_max={result['t_max_k']} K | "
                              f"anomalous_px={result['n_anomalous_pixels']}")

            elif platform in ("VIIRS_SNPP", "VIIRS_NOAA20"):
                # VIIRS 375m I-band (IMG product)
                l1b_files = [p for p in paths if "VNP02IMG" in p.name or "VJ102IMG" in p.name]
                geo_files = [p for p in paths if "VNP03IMG" in p.name or "VJ103IMG" in p.name]
                geo_by_time = {_time_key(g.name): g for g in geo_files}

                for l1b in l1b_files:
                    geo = geo_by_time.get(_time_key(l1b.name))
                    if geo is None:
                        print(f"  No geolocation match for {l1b.name}")
                        continue
                    result = process_viirs.calculate_vrp(
                        l1b, geo,
                        volcano["lat"], volcano["lon"], volcano["radius_km"],
                        vent_lat=volcano.get("vent_lat"),
                        vent_lon=volcano.get("vent_lon"),
                        vent_radius_km=volcano.get("vent_radius_km", 4.0),
                    )
                    if result:
                        store.append_record(volcano["name"], result)
                        vent_str = (f" | VRP_VENT={result['vrp_vent_mw']} MW "
                                    f"({result['n_vent_pixels']}px)"
                                    if volcano.get("vent_lat") else "")
                        print(f"  {result['sensor']} (375m) | VRP_MIR={result['vrp_mir_mw']} MW | "
                              f"VRP_TIR={result['vrp_tir_mw']} MW | "
                              f"T_max={result['t_max_i04_k']} K"
                              f"{vent_str}")

            elif platform in ("VIIRS_SNPP_750", "VIIRS_NOAA20_750"):
                # VIIRS 750m M-band (MOD product) — MIROVA's "VIIRS" channel
                l1b_files = [p for p in paths if "VNP02MOD" in p.name or "VJ102MOD" in p.name]
                geo_files = [p for p in paths if "VNP03MOD" in p.name or "VJ103MOD" in p.name]
                geo_by_time = {_time_key(g.name): g for g in geo_files}

                for l1b in l1b_files:
                    geo = geo_by_time.get(_time_key(l1b.name))
                    if geo is None:
                        print(f"  No geolocation match for {l1b.name}")
                        continue
                    result = process_viirs_mod.calculate_vrp(
                        l1b, geo, volcano["lat"], volcano["lon"], volcano["radius_km"]
                    )
                    if result:
                        store.append_record(volcano["name"], result)
                        print(f"  {result['sensor']} (750m) | VRP={result['vrp_mw']} MW | "
                              f"T_bg={result['t_bg_k']} K | T_max={result['t_max_k']} K | "
                              f"anomalous_px={result['n_anomalous_pixels']}")

    finally:
        # Always delete raw granules after processing
        if volcano_tmp.exists():
            import time, stat
            def _remove_readonly(func, path, _):
                os.chmod(path, stat.S_IWRITE)
                func(path)
            for _ in range(3):
                try:
                    shutil.rmtree(volcano_tmp, onerror=_remove_readonly)
                    break
                except PermissionError:
                    time.sleep(1)
            print(f"  Cleaned up {volcano_tmp}")


def _time_key(filename: str) -> str:
    """Extract YYYYDDDHHMI time key from granule filename."""
    parts = filename.split(".")
    if len(parts) >= 3:
        return parts[1] + parts[2]  # e.g. "A2024074" + "0000"
    return filename


def date_range(start: datetime, end: datetime):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def main():
    parser = argparse.ArgumentParser(description="VRP Chile pipeline")
    parser.add_argument("--volcano", help="Volcano name (default: all active)")
    parser.add_argument("--date", help="Single date YYYY-MM-DD (default: yesterday)")
    parser.add_argument("--start", help="Start date YYYY-MM-DD for range")
    parser.add_argument("--end", help="End date YYYY-MM-DD for range")
    args = parser.parse_args()

    volcanoes = load_volcanoes(args.volcano)
    if not volcanoes:
        print(f"No volcanoes found matching: {args.volcano}")
        sys.exit(1)

    # Determine date(s) to process
    if args.start and args.end:
        dates = list(date_range(
            datetime.strptime(args.start, "%Y-%m-%d"),
            datetime.strptime(args.end, "%Y-%m-%d"),
        ))
    elif args.date:
        dates = [datetime.strptime(args.date, "%Y-%m-%d")]
    else:
        # Default: yesterday (NRT data is typically available with ~3h latency)
        dates = [datetime.utcnow() - timedelta(days=1)]

    for volcano in volcanoes:
        for date in dates:
            process_date(volcano, date)

    print("\nDone.")


if __name__ == "__main__":
    main()
