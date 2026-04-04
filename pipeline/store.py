"""
store.py — Persist VRP results as JSON time series, one file per volcano.

Format: data/{volcano_name}.json
{
  "volcano": "PuyehueCordonCaulle",
  "updated": "2024-03-15T12:00:00Z",
  "records": [
    {
      "datetime_utc": "2024-03-14 00:00",
      "sensor": "MODIS_TERRA",
      "vrp_mw": 12.5,
      "n_anomalous_pixels": 3,
      "t_bg_k": 285.2,
      "t_max_k": 310.1,
      "granule": "MOD021KM.A2024074.0000.061..."
    },
    ...
  ]
}
"""

import json
from pathlib import Path
from datetime import datetime, timezone


DATA_DIR = Path(__file__).parent.parent / "data"


def _load(volcano_name: str) -> dict:
    path = DATA_DIR / f"{volcano_name}.json"
    if path.exists():
        with open(path, "r") as f:
            return json.load(f)
    return {"volcano": volcano_name, "updated": "", "records": []}


def _save(volcano_name: str, store: dict):
    DATA_DIR.mkdir(exist_ok=True)
    store["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    path = DATA_DIR / f"{volcano_name}.json"
    with open(path, "w") as f:
        json.dump(store, f, indent=2)


def append_record(volcano_name: str, record: dict):
    """
    Append a VRP record to the volcano's JSON file.
    Deduplicates by (datetime_utc, sensor) — safe to re-run.
    """
    if record is None:
        return

    store = _load(volcano_name)
    key = (record.get("datetime_utc"), record.get("sensor"))
    existing_keys = {
        (r.get("datetime_utc"), r.get("sensor"))
        for r in store["records"]
    }
    if key not in existing_keys:
        store["records"].append(record)
        store["records"].sort(key=lambda r: r.get("datetime_utc", ""))
        _save(volcano_name, store)


def get_records(volcano_name: str, last_n: int = None) -> list:
    store = _load(volcano_name)
    records = store["records"]
    if last_n:
        records = records[-last_n:]
    return records
