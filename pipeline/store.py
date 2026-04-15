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

from pipeline.profile import (
    DATA_SUBDIR,
    MIN_VRP_MW_VIIRS375,
    MIN_VRP_MW_VIIRS750,
    MIN_VRP_MW_MODIS,
)


# Per-profile data directory: data/mirova_equivalent/ or data/experimental/
DATA_DIR = Path(__file__).parent.parent / "data" / DATA_SUBDIR


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
    DATA_DIR.mkdir(parents=True, exist_ok=True)
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
    vrp_vent = record.get("vrp_vent_mw", 0) or 0

    # S12 fix: when eruption VRP is discarded by distance filter, also clear
    # the hotspot_lat/lon/dist + anomaly_pixels so the dashboard does NOT
    # render the record at a non-volcanic feature (e.g., a warm lake 10 km
    # from the crater). If vent-path fired, the effective detection is at
    # the vent; dashboard fallback logic will then place it on the vent
    # marker. If neither fired (vrp=0), record will be silent.
    # The discarded eruption pixel info is preserved in diagnostic fields.
    if hotspot_dist is not None and hotspot_dist > MAX_HOTSPOT_DIST_KM:
        # Preserve diagnostic info for auditing (not displayed in dashboard)
        record["discarded_hotspot_lat"] = record.get("hotspot_lat")
        record["discarded_hotspot_lon"] = record.get("hotspot_lon")
        record["discarded_hotspot_dist_km"] = hotspot_dist
        record["discarded_reason"] = "eruption_hotspot_too_far"
        if record.get("anomaly_pixels"):
            record["discarded_anomaly_pixels"] = record["anomaly_pixels"]
        # Clear display fields — dashboard will treat as vent-only if vent
        # fired, or as non-detection if not.
        record["hotspot_lat"] = None
        record["hotspot_lon"] = None
        record["hotspot_dist_km"] = None
        record["anomaly_pixels"] = []
        vrp_eruption = 0  # discard distant eruption-scale signal
    record["vrp_mw"] = round(max(vrp_eruption, vrp_vent), 3)

    # S12 2026-04-15: piso VRP por sensor (paridad MIROVA).
    # Si vrp_mw < piso_sensor, se trata como no-detección (vrp_mw = 0).
    # Preserva el valor original en diag_vrp_raw_mw para auditoría.
    sensor = record.get("sensor", "")
    if "375" in sensor or sensor in ("VIIRS_SNPP", "VIIRS_NOAA20"):
        floor = MIN_VRP_MW_VIIRS375
    elif "750" in sensor:
        floor = MIN_VRP_MW_VIIRS750
    elif "MODIS" in sensor:
        floor = MIN_VRP_MW_MODIS
    else:
        floor = 0.0
    if floor > 0 and 0 < record["vrp_mw"] < floor:
        record["diag_vrp_raw_mw"] = record["vrp_mw"]
        record["diag_vrp_floor_mw"] = floor
        record["vrp_mw"] = 0.0
        # El operador sigue viendo el record (con vrp=0) pero no cuenta
        # como detección en auditoría ni en dashboard "últimas VRP>0".

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
        existing = store["records"][existing_idx[key]]
        # S12: auto-upgrade NRT -> standard. If the previously stored record
        # came from a LANCE-NRT granule and the new one is a definitive
        # Standard product, replace it even without overwrite=True. This
        # lets the regular 6-hourly NRT cron automatically consolidate the
        # historical archive to Standard once NASA publishes the L1B,
        # typically 3-5 days after the overpass. No separate weekly cron
        # needed, no records lost, no bias accumulated.
        is_upgrade = (
            existing.get("product_version") == "nrt"
            and record.get("product_version") == "standard"
        )
        if overwrite or is_upgrade:
            store["records"][existing_idx[key]] = record
            store["records"].sort(key=lambda r: r.get("datetime_utc", ""))
            _save(volcano_name, store)
            if is_upgrade and not overwrite:
                print(f"  STORE upgrade NRT->standard: {key[0]} {key[1]}")
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
