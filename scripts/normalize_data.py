"""
normalize_data.py — Fix records that are missing unified vrp_mw and t_max_k fields.

VIIRS 375m records store vrp_mir_mw/vrp_vent_mw instead of vrp_mw,
and t_max_i04_k instead of t_max_k. This script normalizes all records
so the dashboard and analysis work consistently.

Usage:
    python scripts/normalize_data.py
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


def normalize_record(r: dict) -> dict:
    """Ensure record has unified vrp_mw and t_max_k fields."""
    # Normalize vrp_mw: max(eruption-scale, vent-scale)
    if "vrp_mir_mw" in r and "vrp_mw" not in r:
        r["vrp_mw"] = r["vrp_mir_mw"]

    vrp_eruption = r.get("vrp_mw", 0) or 0
    vrp_vent = r.get("vrp_vent_mw", 0) or 0
    r["vrp_mw"] = round(max(vrp_eruption, vrp_vent), 3)

    # Normalize t_max_k for VIIRS 375m
    if "t_max_i04_k" in r and "t_max_k" not in r:
        r["t_max_k"] = r["t_max_i04_k"]

    return r


def main():
    json_files = sorted(DATA_DIR.glob("*.json"))
    for path in json_files:
        if path.name.startswith("."):
            continue
        with open(path) as f:
            data = json.load(f)

        if "records" not in data:
            continue

        fixed = 0
        for r in data["records"]:
            old_vrp = r.get("vrp_mw")
            normalize_record(r)
            if r["vrp_mw"] != old_vrp:
                fixed += 1

        if fixed > 0:
            with open(path, "w") as f:
                json.dump(data, f, indent=2)

        total = len(data["records"])
        det = sum(1 for r in data["records"] if r.get("vrp_mw", 0) > 0)
        max_vrp = max((r.get("vrp_mw", 0) for r in data["records"]), default=0)
        print(f"{path.stem:25s}: {total:4d} records, {det:3d} detections, "
              f"max VRP={max_vrp:.3f} MW" + (f" ({fixed} fixed)" if fixed else ""))


if __name__ == "__main__":
    main()
