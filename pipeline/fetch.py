"""
fetch.py — Download MODIS and VIIRS L1B granules from NASA Earthdata via earthaccess.

For each volcano, downloads:
  - MODIS: MOD021KM (Terra) + MYD021KM (Aqua) + corresponding MOD03/MYD03 geolocation
  - VIIRS: VNP02IMG (Suomi-NPP) + VJ102IMG (NOAA-20) + geolocation VNP03IMG/VJ103IMG

Granules are saved to a temp directory, processed, then deleted.
"""

import math
import os
import earthaccess
from datetime import datetime, timedelta
from pathlib import Path


def _solar_elevation(lat_deg: float, lon_deg: float, dt_utc: datetime) -> float:
    """Approximate solar elevation angle (degrees). Negative = nighttime."""
    doy = dt_utc.timetuple().tm_yday
    hour_utc = dt_utc.hour + dt_utc.minute / 60.0
    gamma = 2 * math.pi * (doy - 1) / 365.0
    decl = (0.006918 - 0.399912 * math.cos(gamma) + 0.070257 * math.sin(gamma)
            - 0.006758 * math.cos(2 * gamma) + 0.000907 * math.sin(2 * gamma))
    solar_hour = hour_utc + lon_deg / 15.0
    hour_angle = math.radians(15.0 * (solar_hour - 12.0))
    lat_r = math.radians(lat_deg)
    sin_elev = (math.sin(lat_r) * math.sin(decl)
                + math.cos(lat_r) * math.cos(decl) * math.cos(hour_angle))
    return math.degrees(math.asin(max(-1.0, min(1.0, sin_elev))))


# Short names for each product in the NASA CMR catalog.
# S12 fix: each product has a "standard" short_name (calibrated, ~3–5 day lag)
# and an "nrt" fallback (LANCE near-real-time, ~3 h lag but only kept ~7–14 d).
# search_granules() tries standard first (permanent calibration, better for
# historical records) and falls back to NRT when standard is not yet
# published — this closes the 3–5 day gap that we had previously.
# MIROVA uses the same strategy; without the NRT fallback our last date
# always lagged LAADS DAAC publication.
PRODUCTS = {
    # MODIS 1km emissive bands
    "MODIS_TERRA_L1B":        {"short_name": "MOD021KM",  "version": "6.1",
                               "nrt": {"short_name": "MOD021KM_NRT", "version": "61"}},
    "MODIS_TERRA_GEO":        {"short_name": "MOD03",     "version": "6.1",
                               "nrt": {"short_name": "MOD03_NRT",     "version": "61"}},
    "MODIS_AQUA_L1B":         {"short_name": "MYD021KM",  "version": "6.1",
                               "nrt": {"short_name": "MYD021KM_NRT", "version": "61"}},
    "MODIS_AQUA_GEO":         {"short_name": "MYD03",     "version": "6.1",
                               "nrt": {"short_name": "MYD03_NRT",     "version": "61"}},
    # VIIRS 375m I-band (IMG product) — Band I04 @ 3.74µm
    "VIIRS_SNPP_L1B":         {"short_name": "VNP02IMG",  "version": "2",
                               "nrt": {"short_name": "VNP02IMG_NRT", "version": "2"}},
    "VIIRS_SNPP_GEO":         {"short_name": "VNP03IMG",  "version": "2",
                               "nrt": {"short_name": "VNP03IMG_NRT", "version": "2"}},
    # NOAA-20 (JPSS-1): try version 2.1 first, then 2, then 1
    "VIIRS_NOAA20_L1B":       {"short_name": "VJ102IMG",  "versions": ["2.1", "2", "1"],
                               "nrt": {"short_name": "VJ102IMG_NRT", "versions": ["2.1", "2"]}},
    "VIIRS_NOAA20_GEO":       {"short_name": "VJ103IMG",  "versions": ["2.1", "2", "1"],
                               "nrt": {"short_name": "VJ103IMG_NRT", "versions": ["2.1", "2"]}},
    # VIIRS 750m M-band (MOD product) — Band M13 @ 4.05µm (same as MIROVA VIIRS750)
    "VIIRS_SNPP_MOD_L1B":     {"short_name": "VNP02MOD",  "version": "2",
                               "nrt": {"short_name": "VNP02MOD_NRT", "version": "2"}},
    "VIIRS_SNPP_MOD_GEO":     {"short_name": "VNP03MOD",  "version": "2",
                               "nrt": {"short_name": "VNP03MOD_NRT", "version": "2"}},
    "VIIRS_NOAA20_MOD_L1B":   {"short_name": "VJ102MOD",  "versions": ["2.1", "2", "1"],
                               "nrt": {"short_name": "VJ102MOD_NRT", "versions": ["2.1", "2"]}},
    "VIIRS_NOAA20_MOD_GEO":   {"short_name": "VJ103MOD",  "versions": ["2.1", "2", "1"],
                               "nrt": {"short_name": "VJ103MOD_NRT", "versions": ["2.1", "2"]}},
    # NOAA-21 (JPSS-2, lanzado nov-2022, operacional ene-2023). MIROVA lo procesa
    # desde 2023; nuestro fetch lo ignoró hasta S18 — cuello de botella recall
    # confirmado H10 (docs/HYPOTHESIS_LOG.md). Solo v2.1 publicada en CMR.
    # Respaldo: JPSS VIIRS SDR Radiometric ATBD Rev C.
    "VIIRS_NOAA21_L1B":       {"short_name": "VJ202IMG",  "versions": ["2.1"],
                               "nrt": {"short_name": "VJ202IMG_NRT", "versions": ["2.1"]}},
    "VIIRS_NOAA21_GEO":       {"short_name": "VJ203IMG",  "versions": ["2.1"],
                               "nrt": {"short_name": "VJ203IMG_NRT", "versions": ["2.1"]}},
    "VIIRS_NOAA21_MOD_L1B":   {"short_name": "VJ202MOD",  "versions": ["2.1"],
                               "nrt": {"short_name": "VJ202MOD_NRT", "versions": ["2.1"]}},
    "VIIRS_NOAA21_MOD_GEO":   {"short_name": "VJ203MOD",  "versions": ["2.1"],
                               "nrt": {"short_name": "VJ203MOD_NRT", "versions": ["2.1"]}},
}


def auth():
    """Authenticate with NASA Earthdata.

    Strategy order: environment vars → netrc. Falla solo si NINGUNA funciona,
    permitiendo correr local con `~/_netrc` (Windows) o `~/.netrc` (Unix) sin
    requerir env vars. CI sigue usando env vars (secrets en GitHub Actions).

    H6 S22 retry+backoff: 3 intentos con waits 5s/15s/45s para mitigar
    "Network is unreachable" intermitente GitHub Actions → urs.earthdata.nasa.gov
    (issue #1, ~40% runs fallaron S20-S22 sin razón clara desde código).
    """
    import time
    delays = [0, 5, 15, 45]  # 4 attempts: immediate + 3 retries
    last_err = None
    for delay in delays:
        if delay:
            time.sleep(delay)
        try:
            earthaccess.login(strategy="environment")
            return
        except Exception as e:
            last_err = e
        try:
            earthaccess.login(strategy="netrc")
            return
        except Exception as e:
            last_err = e
    # Si aquí, todos los attempts fallaron. Reraise el último error.
    raise last_err if last_err else RuntimeError("auth failed")


def product_version_from_granule(filename: str) -> str:
    """
    Return "nrt" if the granule filename corresponds to a LANCE-NRT product,
    "standard" otherwise.

    NRT filenames contain the substring "_NRT" in the short_name prefix, e.g.
    MOD021KM_NRT.A2026100.0215.061.2026100061218.hdf
    VNP02IMG_NRT.A2026103.0554.002.2026103122413.nc

    Standard filenames do not:
    MOD021KM.A2026001.0225.061.2026001131216.hdf
    VJ102IMG.A2026099.0554.021.2026099122413.nc

    Used by process_*.py to tag each record with its data source so the
    historical archive can be audited for NRT vs Standard provenance, and
    so the weekly auto-upgrade cron can identify records to replace when
    Standard becomes available.
    """
    return "nrt" if "_NRT" in filename else "standard"


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

    # S12: try STANDARD (calibrated, permanent) first, then NRT (LANCE, ~3h
    # latency but only kept ~7-14 days). This closes the 3-5 day gap we
    # previously had whenever the standard product hadn't been published yet.
    attempts = [{
        "short_name": p["short_name"],
        "versions": p["versions"] if isinstance(p.get("versions"), list) else [p["version"]],
    }]
    if "nrt" in p:
        nrt = p["nrt"]
        attempts.append({
            "short_name": nrt["short_name"],
            "versions": nrt["versions"] if isinstance(nrt.get("versions"), list) else [nrt["version"]],
        })

    for attempt in attempts:
        for ver in attempt["versions"]:
            results = earthaccess.search_data(
                short_name=attempt["short_name"],
                version=ver,
                bounding_box=bbox,
                temporal=(date_str, date_str),
                count=20,
            )
            if results:
                return results
    return []


def download_granules(granules: list, dest_dir: Path) -> list[Path]:
    """Download a list of granules to dest_dir. Returns list of local file paths.

    H6 S22 retry+backoff: 3 intentos con waits 10s/30s/60s para mitigar
    fallos intermitentes red GitHub→NASA. Cada intento llama earthaccess.download
    completo; si parcialmente exitoso (algunos files OK), retorna lo que pudo.
    """
    import time
    dest_dir.mkdir(parents=True, exist_ok=True)
    delays = [0, 10, 30, 60]
    last_err = None
    for delay in delays:
        if delay:
            time.sleep(delay)
        try:
            paths = earthaccess.download(granules, local_path=str(dest_dir))
            return [Path(p) for p in paths if Path(p).exists()]
        except Exception as e:
            last_err = e
    raise last_err if last_err else RuntimeError("download failed")


def _filter_nighttime_granules(granules: list, lat: float, lon: float,
                                 debug: bool = False) -> list:
    """Filter granule list to only nighttime passes (solar elevation < 0).
    This prevents downloading daytime granules that would be discarded later,
    saving ~50% of bandwidth.

    Set debug=True to print each granule's time+elevation. Useful when
    diagnosing why NRT searches return only "daytime" — distinguishes
    "catalog genuinely only has daytime passes" from "metadata field
    points to the wrong time".
    """
    night = []
    for g in granules:
        try:
            begin = g["umm"]["TemporalExtent"]["RangeDateTime"]["BeginningDateTime"]
            # Parse ISO datetime: "2026-01-01T05:36:00.000Z"
            dt = datetime.strptime(begin[:19], "%Y-%m-%dT%H:%M:%S")
            elev = _solar_elevation(lat, lon, dt)
            if debug:
                name = g.get("umm", {}).get("GranuleUR", "?")
                print(f"    [nightfilter] {name[:70]} begin={begin[:19]} elev={elev:+.1f}deg")
            if elev < 0:
                night.append(g)
        except (KeyError, TypeError, ValueError) as e:
            if debug:
                print(f"    [nightfilter] granule unparseable ({e}), keeping")
            night.append(g)
    return night


def fetch_for_volcano(volcano: dict, date: datetime,
                      tmp_dir: Path, sensors: list[str] = None,
                      skip_noaa20: bool = False,
                      nighttime_only: bool = True) -> dict[str, list[Path]]:
    """
    Download all relevant L1B + geolocation granules for a volcano on a given date.

    Args:
        nighttime_only: If True, filter granules to nighttime passes BEFORE
            downloading (saves ~50% bandwidth). Default True.

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

    all_platforms = []
    if "MODIS" in sensors:
        all_platforms += [
            ("MODIS_TERRA", "MODIS_TERRA_L1B", "MODIS_TERRA_GEO"),
            ("MODIS_AQUA",  "MODIS_AQUA_L1B",  "MODIS_AQUA_GEO"),
        ]
    if "VIIRS" in sensors:
        # 375m I-band — 3 plataformas: SNPP (2011), NOAA-20 (2017), NOAA-21 (2022)
        all_platforms += [
            ("VIIRS_SNPP",    "VIIRS_SNPP_L1B",    "VIIRS_SNPP_GEO"),
            ("VIIRS_NOAA20",  "VIIRS_NOAA20_L1B",  "VIIRS_NOAA20_GEO"),
            ("VIIRS_NOAA21",  "VIIRS_NOAA21_L1B",  "VIIRS_NOAA21_GEO"),
        ]
        # 750m M-band (MIROVA's "VIIRS" or "VIIRS750")
        all_platforms += [
            ("VIIRS_SNPP_750",    "VIIRS_SNPP_MOD_L1B",    "VIIRS_SNPP_MOD_GEO"),
            ("VIIRS_NOAA20_750",  "VIIRS_NOAA20_MOD_L1B",  "VIIRS_NOAA20_MOD_GEO"),
            ("VIIRS_NOAA21_750",  "VIIRS_NOAA21_MOD_L1B",  "VIIRS_NOAA21_MOD_GEO"),
        ]

    if skip_noaa20:
        all_platforms = [(p, l, g) for p, l, g in all_platforms if "NOAA20" not in p]

    for platform, l1b_key, geo_key in all_platforms:
        try:
            l1b_granules = search_granules(l1b_key, lat, lon, radius, date)
            if not l1b_granules:
                continue

            # Pre-download nighttime filter — skip daytime granules entirely
            if nighttime_only:
                before = len(l1b_granules)
                l1b_granules = _filter_nighttime_granules(l1b_granules, lat, lon)
                after = len(l1b_granules)
                skipped = before - after
                # S12: clearer log. "skipped X of Y" removes the ambiguity
                # of the old "skipped X daytime" which sounded like the
                # whole search was daytime when it was just a subset.
                if before:
                    print(f"  {platform}: kept {after} of {before} granules (night filter)")
                if not l1b_granules:
                    continue

            geo_granules = search_granules(geo_key, lat, lon, radius, date)
            matched = _match_granules(l1b_granules, geo_granules)
            platform_dir = tmp_dir / platform
            paths = []
            for l1b_g, geo_g in matched:
                paths += download_granules([l1b_g, geo_g], platform_dir)
            results[platform] = paths
        except Exception as e:
            print(f"  WARN: Failed to fetch {platform}: {e}")
            results[platform] = []

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
