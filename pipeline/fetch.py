"""
fetch.py — Download MODIS and VIIRS L1B granules from NASA Earthdata via earthaccess.

For each volcano, downloads:
  - MODIS: MOD021KM (Terra) + MYD021KM (Aqua) + corresponding MOD03/MYD03 geolocation
  - VIIRS: VNP02IMG (Suomi-NPP) + VJ102IMG (NOAA-20) + geolocation VNP03IMG/VJ103IMG

Granules are saved to a temp directory, processed, then deleted.
"""

import os
import earthaccess
from datetime import datetime, timedelta
from pathlib import Path


# Short names for each product in the NASA CMR catalog
PRODUCTS = {
    "MODIS_TERRA_L1B":   {"short_name": "MOD021KM",  "version": "061"},
    "MODIS_TERRA_GEO":   {"short_name": "MOD03",     "version": "061"},
    "MODIS_AQUA_L1B":    {"short_name": "MYD021KM",  "version": "061"},
    "MODIS_AQUA_GEO":    {"short_name": "MYD03",     "version": "061"},
    "VIIRS_SNPP_L1B":    {"short_name": "VNP02IMG",  "version": "002"},
    "VIIRS_SNPP_GEO":    {"short_name": "VNP03IMG",  "version": "002"},
    "VIIRS_NOAA20_L1B":  {"short_name": "VJ102IMG",  "version": "002"},
    "VIIRS_NOAA20_GEO":  {"short_name": "VJ103IMG",  "version": "002"},
}


def auth():
    """Authenticate with NASA Earthdata. Uses env vars or ~/.netrc."""
    earthaccess.login(strategy="environment")


def search_granules(product_key: str, lat: float, lon: float,
                    radius_km: float, date: datetime) -> list:
    """
    Search for granules covering a given location on a given date.

    Returns a list of earthaccess granule objects.
    """
    p = PRODUCTS[product_key]
    # Bounding box from radius (rough approximation: 1 degree lat ~ 111 km)
    delta = radius_km / 111.0
    bbox = (lon - delta, lat - delta, lon + delta, lat + delta)
    date_str = date.strftime("%Y-%m-%d")

    results = earthaccess.search_data(
        short_name=p["short_name"],
        version=p["version"],
        bounding_box=bbox,
        temporal=(date_str, date_str),
        count=20,
    )
    return results


def download_granules(granules: list, dest_dir: Path) -> list[Path]:
    """Download a list of granules to dest_dir. Returns list of local file paths."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    paths = earthaccess.download(granules, local_path=str(dest_dir))
    return [Path(p) for p in paths]


def fetch_for_volcano(volcano: dict, date: datetime,
                      tmp_dir: Path, sensors: list[str] = None) -> dict[str, list[Path]]:
    """
    Download all relevant L1B + geolocation granules for a volcano on a given date.

    Returns:
        {
          "MODIS_TERRA": [l1b_path, geo_path],
          "MODIS_AQUA":  [l1b_path, geo_path],
          "VIIRS_SNPP":  [l1b_path, geo_path],
          "VIIRS_NOAA20":[l1b_path, geo_path],
        }
    """
    auth()
    lat, lon = volcano["lat"], volcano["lon"]
    radius = volcano.get("radius_km", 30)
    sensors = sensors or volcano.get("sensors", ["MODIS", "VIIRS"])
    results = {}

    if "MODIS" in sensors:
        for platform, l1b_key, geo_key in [
            ("MODIS_TERRA", "MODIS_TERRA_L1B", "MODIS_TERRA_GEO"),
            ("MODIS_AQUA",  "MODIS_AQUA_L1B",  "MODIS_AQUA_GEO"),
        ]:
            l1b_granules = search_granules(l1b_key, lat, lon, radius, date)
            if not l1b_granules:
                continue
            geo_granules = search_granules(geo_key, lat, lon, radius, date)
            # Match granules by acquisition time (same timestamp in filename)
            matched = _match_granules(l1b_granules, geo_granules)
            platform_dir = tmp_dir / platform
            paths = []
            for l1b_g, geo_g in matched:
                paths += download_granules([l1b_g, geo_g], platform_dir)
            results[platform] = paths

    if "VIIRS" in sensors:
        for platform, l1b_key, geo_key in [
            ("VIIRS_SNPP",   "VIIRS_SNPP_L1B",   "VIIRS_SNPP_GEO"),
            ("VIIRS_NOAA20", "VIIRS_NOAA20_L1B",  "VIIRS_NOAA20_GEO"),
        ]:
            l1b_granules = search_granules(l1b_key, lat, lon, radius, date)
            if not l1b_granules:
                continue
            geo_granules = search_granules(geo_key, lat, lon, radius, date)
            matched = _match_granules(l1b_granules, geo_granules)
            platform_dir = tmp_dir / platform
            paths = []
            for l1b_g, geo_g in matched:
                paths += download_granules([l1b_g, geo_g], platform_dir)
            results[platform] = paths

    return results


def _match_granules(l1b_list: list, geo_list: list) -> list[tuple]:
    """
    Match L1B and geolocation granules by their acquisition datetime.
    MODIS/VIIRS filenames encode the datetime (e.g. A2024074.0000 = day 74 of 2024, 00:00 UTC).
    Returns list of (l1b_granule, geo_granule) tuples.
    """
    def granule_time(g):
        # earthaccess granule has .data_links() and metadata
        try:
            return g["umm"]["TemporalExtent"]["RangeDateTime"]["BeginningDateTime"]
        except (KeyError, TypeError):
            return str(g)

    geo_by_time = {granule_time(g): g for g in geo_list}
    matched = []
    for l1b in l1b_list:
        t = granule_time(l1b)
        if t in geo_by_time:
            matched.append((l1b, geo_by_time[t]))
    return matched
