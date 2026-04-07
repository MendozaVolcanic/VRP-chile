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
import math
from pathlib import Path
from datetime import datetime, timezone


DATA_DIR = Path(__file__).parent.parent / "data"


def _solar_elevation(lat: float, lon: float, dt_utc: datetime) -> float:
    """Quick solar elevation check. Returns degrees (negative = night)."""
    doy = dt_utc.timetuple().tm_yday
    hour_utc = dt_utc.hour + dt_utc.minute / 60.0
    gamma = 2 * math.pi * (doy - 1) / 365.0
    decl = (0.006918 - 0.399912 * math.cos(gamma) + 0.070257 * math.sin(gamma)
            - 0.006758 * math.cos(2 * gamma) + 0.000907 * math.sin(2 * gamma))
    solar_hour = hour_utc + lon / 15.0
    hour_angle = math.radians(15.0 * (solar_hour - 12.0))
    lat_r = math.radians(lat)
    sin_elev = (math.sin(lat_r) * math.sin(decl)
                + math.cos(lat_r) * math.cos(decl) * math.cos(hour_angle))
    return math.degrees(math.asin(max(-1.0, min(1.0, sin_elev))))


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


def append_record(volcano_name: str, record: dict,
                   volcano_lat: float = None, volcano_lon: float = None,
                   overwrite: bool = False):
    """
    Append a VRP record to the volcano's JSON file.
    Deduplicates by (datetime_utc, sensor) — safe to re-run.
    If volcano_lat/lon provided, rejects daytime records as a safety net.
    If overwrite=True, replace any existing record with the same key
    (used for reprocessing with corrected algorithms, e.g. scan-angle fix).
    """
    if record is None:
        return

    # Normalize VRP field: ensure every record has a unified 'vrp_mw' field.
    # VIIRS 375m returns vrp_mir_mw/vrp_vent_mw; MODIS/VIIRS750 return vrp_mw/vrp_vent_mw.
    # The unified vrp_mw = max(eruption-scale, vent-scale) for dashboard consistency.
    #
    # Distance filter: eruption-scale hotspots >5km from crater are almost always
    # non-volcanic (urban, agricultural, or geothermal sources within the search ROI).
    # MIROVA uses a similar proximity filter. We only trust eruption-scale VRP when
    # the hotspot is within MAX_HOTSPOT_DIST_KM of the volcano center.
    MAX_HOTSPOT_DIST_KM = 5.0
    if "vrp_mir_mw" in record and "vrp_mw" not in record:
        record["vrp_mw"] = record["vrp_mir_mw"]
    vrp_eruption = record.get("vrp_mw", 0) or 0
    hotspot_dist = record.get("hotspot_dist_km")
    if hotspot_dist is not None and hotspot_dist > MAX_HOTSPOT_DIST_KM:
        vrp_eruption = 0  # discard distant eruption-scale signal
    vrp_vent = record.get("vrp_vent_mw", 0) or 0
    record["vrp_mw"] = round(max(vrp_eruption, vrp_vent), 3)

    # Normalize t_max_k for VIIRS 375m (uses t_max_i04_k internally)
    if "t_max_i04_k" in record and "t_max_k" not in record:
        record["t_max_k"] = record["t_max_i04_k"]

    # Safety net: reject daytime records (solar contamination → false VRP)
    if volcano_lat is not None and volcano_lon is not None:
        dt_str = record.get("datetime_utc", "")
        try:
            dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
            elev = _solar_elevation(volcano_lat, volcano_lon, dt)
            if elev > 0:
                print(f"  STORE REJECT daytime: {dt_str} {record.get('sensor')} "
                      f"(solar elev={elev:.1f}°)")
                return
        except (ValueError, TypeError):
            pass  # Can't parse — store anyway

    store = _load(volcano_name)
    key = (record.get("datetime_utc"), record.get("sensor"))
    existing_idx = {
        (r.get("datetime_utc"), r.get("sensor")): i
        for i, r in enumerate(store["records"])
    }
    if key in existing_idx:
        if overwrite:
            store["records"][existing_idx[key]] = record
            store["records"].sort(key=lambda r: r.get("datetime_utc", ""))
            _save(volcano_name, store)
    else:
        store["records"].append(record)
        store["records"].sort(key=lambda r: r.get("datetime_utc", ""))
        _save(volcano_name, store)


def get_records(volcano_name: str, last_n: int = None) -> list:
    store = _load(volcano_name)
    records = store["records"]
    if last_n:
        records = records[-last_n:]
    return records
