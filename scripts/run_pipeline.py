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
import math
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

# stdout Windows default cp1252 no imprime Unicode (regla encoding del proyecto);
# reconfigure no re-envuelve el stream (patrón S118 analyze.py).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# --- IMPORTANT: parse --profile BEFORE importing pipeline modules ---
# pipeline.profile reads $VRP_PROFILE at import time. If we let the normal
# argparse run after imports, the processors would already be locked to
# whatever the default profile was.
# S24: discovery dinámico de profiles válidos leyendo pipeline/profiles/*.yaml,
# para mantener una source-of-truth única con pipeline/profile.py:VALID_PROFILES.
_PROFILES_DIR = Path(__file__).parent.parent / "pipeline" / "profiles"
_VALID_PROFILES = sorted(p.stem for p in _PROFILES_DIR.glob("*.yaml"))
_early = argparse.ArgumentParser(add_help=False)
_early.add_argument("--profile", default=None, choices=_VALID_PROFILES)
_early_args, _ = _early.parse_known_args()
if _early_args.profile:
    os.environ["VRP_PROFILE"] = _early_args.profile

from pipeline import fetch, process_modis, process_viirs, process_viirs_mod, store
from pipeline import profile as vrp_profile
from pipeline.geo_utils import get_detection_anchor


# Granules crudos (L1B/HDF) — se descargan, procesan y borran por día. Override
# VRP_TMP_DIR para sacarlo de carpetas sincronizadas (OneDrive): la sync a la nube
# desperdicia banda y los file-locks bloquean el rmtree del cleanup (S94). Default
# = repo/tmp (sin cambio en GitHub Actions, que no setea la var).
TMP_DIR = Path(os.environ.get("VRP_TMP_DIR", str(Path(__file__).parent.parent / "tmp")))
VOLCANOES_FILE = Path(__file__).parent.parent / "volcanoes.yaml"
VOLCANIC_FEATURES_FILE = Path(__file__).parent.parent / "pipeline" / "volcanic_features.yaml"


def _load_volcanic_features() -> dict:
    """S88 Frente B — catálogo de features volcánicas catalogadas por volcán,
    usado por store.append_record para el campo geo_class ('extension'). Si el
    archivo no existe o está vacío, devuelve {} (geo_class cae a summit/far por
    geometría inner_radius pura). Ver pipeline/volcanic_features.yaml."""
    if not VOLCANIC_FEATURES_FILE.exists():
        return {}
    with open(VOLCANIC_FEATURES_FILE, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


VOLCANIC_FEATURES = _load_volcanic_features()


def solar_elevation(lat_deg: float, lon_deg: float, dt_utc: datetime) -> float:
    """
    Approximate solar elevation angle (degrees) for a given location and UTC time.
    Negative = sun below horizon (nighttime).
    Accuracy: ~1° — sufficient for day/night classification.
    """
    doy = dt_utc.timetuple().tm_yday
    hour_utc = dt_utc.hour + dt_utc.minute / 60.0

    # Solar declination (Spencer, 1971 approximation)
    gamma = 2 * math.pi * (doy - 1) / 365.0
    decl = (0.006918 - 0.399912 * math.cos(gamma) + 0.070257 * math.sin(gamma)
            - 0.006758 * math.cos(2 * gamma) + 0.000907 * math.sin(2 * gamma))

    # Hour angle (degrees → radians)
    solar_hour = hour_utc + lon_deg / 15.0  # local solar time
    hour_angle = math.radians(15.0 * (solar_hour - 12.0))

    lat_r = math.radians(lat_deg)
    sin_elev = (math.sin(lat_r) * math.sin(decl)
                + math.cos(lat_r) * math.cos(decl) * math.cos(hour_angle))
    return math.degrees(math.asin(max(-1.0, min(1.0, sin_elev))))


def is_nighttime(lat: float, lon: float, dt_utc: datetime) -> bool:
    """True if sun is below horizon (solar elevation < 0°)."""
    return solar_elevation(lat, lon, dt_utc) < 0.0


def _parse_granule_datetime(filename: str) -> datetime | None:
    """Extract UTC datetime from MODIS/VIIRS granule filename."""
    try:
        parts = filename.split(".")
        year = int(parts[1][1:5])
        doy = int(parts[1][5:8])
        hour = int(parts[2][:2])
        minute = int(parts[2][2:4])
        return datetime(year, 1, 1) + timedelta(days=doy - 1, hours=hour, minutes=minute)
    except Exception:
        return None


def load_volcanoes(name_filter: str = None) -> list:
    with open(VOLCANOES_FILE) as f:
        cfg = yaml.safe_load(f)
    volcanoes = [v for v in cfg["volcanoes"] if v.get("active", True)]
    if name_filter:
        volcanoes = [v for v in volcanoes if v["name"] == name_filter]
    return volcanoes


def process_date(volcano: dict, date: datetime, nighttime_only: bool = True,
                 skip_noaa20: bool = False, overwrite: bool = False):
    """Download and process all granules for a volcano on a given date.

    Args:
        nighttime_only: If True, skip daytime passes (solar elevation > 0°).
            MIROVA only uses nighttime data because reflected solar radiation
            in the MIR band (~4µm) creates massive false positives during daytime.
        skip_noaa20: If True, skip NOAA-20 VIIRS products (useful when NASA
            downloads are slow/unreliable).
    """
    print(f"\n>>> {volcano['display_name']} | {date.strftime('%Y-%m-%d')}")

    volcano_tmp = TMP_DIR / volcano["name"] / date.strftime("%Y%m%d")

    def _check_night(l1b_path: Path) -> bool:
        """Return True if granule is nighttime (or if nighttime_only is disabled)."""
        if not nighttime_only:
            return True
        dt = _parse_granule_datetime(l1b_path.name)
        if dt is None:
            return True  # Can't parse → process anyway
        night = is_nighttime(volcano["lat"], volcano["lon"], dt)
        if not night:
            elev = solar_elevation(volcano["lat"], volcano["lon"], dt)
            print(f"  SKIP daytime: {l1b_path.name} (solar elev={elev:.1f}°)")
        return night

    try:
        granule_paths = fetch.fetch_for_volcano(volcano, date, volcano_tmp,
                                                    skip_noaa20=skip_noaa20,
                                                    nighttime_only=nighttime_only)

        # Filter to only files that actually exist on disk
        for platform in granule_paths:
            granule_paths[platform] = [p for p in granule_paths[platform] if p.exists()]

        for platform, paths in granule_paths.items():
            if not paths:
                continue

            # Profile-gated sensor filter. Each processor can be disabled in
            # the active YAML profile without changing calling code.
            if "MODIS" in platform and not vrp_profile.SENSOR_MODIS:
                continue
            if platform in ("VIIRS_SNPP", "VIIRS_NOAA20", "VIIRS_NOAA21") and not vrp_profile.SENSOR_VIIRS_375:
                continue
            if platform in ("VIIRS_SNPP_750", "VIIRS_NOAA20_750", "VIIRS_NOAA21_750") and not vrp_profile.SENSOR_VIIRS_750:
                continue

            # Separate L1B and geolocation files
            if "MODIS" in platform:
                l1b_files = [p for p in paths if "MOD021KM" in p.name or "MYD021KM" in p.name]
                geo_files = [p for p in paths if "MOD03" in p.name or "MYD03" in p.name]
                geo_by_time = {_time_key(g.name): g for g in geo_files}

                for l1b in l1b_files:
                    if not _check_night(l1b):
                        continue
                    geo = geo_by_time.get(_time_key(l1b.name))
                    if geo is None:
                        print(f"  No geolocation match for {l1b.name}")
                        continue
                    try:
                        eff_vent_lat, eff_vent_lon = get_detection_anchor(volcano)
                        result = process_modis.calculate_vrp(
                            l1b, geo, volcano["lat"], volcano["lon"], volcano["radius_km"],
                            vent_lat=eff_vent_lat,
                            vent_lon=eff_vent_lon,
                            vent_radius_km=volcano.get("vent_radius_km", 4.0),
                            inner_radius_km=volcano.get("inner_radius_km"),
                            exclude_zones=volcano.get("exclude_zones"),
                            active_water_bodies=volcano.get("active_water_bodies"),
                            lbg_global_compatible=volcano.get("lbg_global_compatible", False),
                            local_kernel_bg_compatible=volcano.get("local_kernel_bg", False),
                        )
                        if result:
                            store.append_record(volcano["name"], result,
                                                volcano_lat=volcano["lat"], volcano_lon=volcano["lon"],
                                                overwrite=overwrite,
                                                max_hotspot_dist_km=volcano.get("radius_km"),
                                                enable_pixel_level_distance_filter=vrp_profile.ENABLE_PIXEL_LEVEL_DISTANCE_FILTER,
                                                max_cluster_pixels=volcano.get("max_cluster_pixels"),
                                                inner_radius_km=volcano.get("inner_radius_km"),
                                                volcanic_features=VOLCANIC_FEATURES.get(volcano["name"]))
                            vent_str = (f" | VRP_VENT={result.get('vrp_vent_mw', 0)} MW"
                                        if eff_vent_lat is not None and result.get('vrp_vent_mw', 0) > 0 else "")
                            print(f"  {result['sensor']} | VRP={result['vrp_mw']} MW | "
                                  f"T_bg={result['t_bg_k']} K | T_max={result['t_max_k']} K | "
                                  f"anomalous_px={result['n_anomalous_pixels']}{vent_str}")
                    except Exception as e:
                        print(f"  ERROR processing {l1b.name}: {e}")

            elif platform in ("VIIRS_SNPP", "VIIRS_NOAA20", "VIIRS_NOAA21"):
                # VIIRS 375m I-band (IMG product). 3 plataformas: SNPP / NOAA-20 / NOAA-21 (S18)
                l1b_files = [p for p in paths if "VNP02IMG" in p.name or "VJ102IMG" in p.name or "VJ202IMG" in p.name]
                geo_files = [p for p in paths if "VNP03IMG" in p.name or "VJ103IMG" in p.name or "VJ203IMG" in p.name]
                geo_by_time = {_time_key(g.name): g for g in geo_files}

                for l1b in l1b_files:
                    if not _check_night(l1b):
                        continue
                    geo = geo_by_time.get(_time_key(l1b.name))
                    if geo is None:
                        print(f"  No geolocation match for {l1b.name}")
                        continue
                    try:
                        eff_vent_lat, eff_vent_lon = get_detection_anchor(volcano)
                        result = process_viirs.calculate_vrp(
                            l1b, geo,
                            volcano["lat"], volcano["lon"], volcano["radius_km"],
                            vent_lat=eff_vent_lat,
                            vent_lon=eff_vent_lon,
                            vent_radius_km=volcano.get("vent_radius_km", 4.0),
                            inner_radius_km=volcano.get("inner_radius_km"),
                            exclude_zones=volcano.get("exclude_zones"),
                            active_water_bodies=volcano.get("active_water_bodies"),
                            lbg_global_compatible=volcano.get("lbg_global_compatible", False),
                            local_kernel_bg_compatible=volcano.get("local_kernel_bg", False),
                            lava_lake_magmatic=volcano.get("lava_lake_magmatic", False),
                        )
                        if result:
                            store.append_record(volcano["name"], result,
                                                volcano_lat=volcano["lat"], volcano_lon=volcano["lon"],
                                                overwrite=overwrite,
                                                max_hotspot_dist_km=volcano.get("radius_km"),
                                                enable_pixel_level_distance_filter=vrp_profile.ENABLE_PIXEL_LEVEL_DISTANCE_FILTER,
                                                max_cluster_pixels=volcano.get("max_cluster_pixels"),
                                                inner_radius_km=volcano.get("inner_radius_km"),
                                                volcanic_features=VOLCANIC_FEATURES.get(volcano["name"]))
                            vent_str = (f" | VRP_VENT={result['vrp_vent_mw']} MW "
                                        f"({result['n_vent_pixels']}px)"
                                        if eff_vent_lat is not None else "")
                            print(f"  {result['sensor']} (375m) | VRP_MIR={result['vrp_mir_mw']} MW | "
                                  f"VRP_TIR={result['vrp_tir_mw']} MW | "
                                  f"T_max={result['t_max_i04_k']} K"
                                  f"{vent_str}")
                    except Exception as e:
                        print(f"  ERROR processing {l1b.name}: {e}")

            elif platform in ("VIIRS_SNPP_750", "VIIRS_NOAA20_750", "VIIRS_NOAA21_750"):
                # VIIRS 750m M-band (MOD product) — MIROVA's "VIIRS" channel. +NOAA-21 (S18)
                l1b_files = [p for p in paths if "VNP02MOD" in p.name or "VJ102MOD" in p.name or "VJ202MOD" in p.name]
                geo_files = [p for p in paths if "VNP03MOD" in p.name or "VJ103MOD" in p.name or "VJ203MOD" in p.name]
                geo_by_time = {_time_key(g.name): g for g in geo_files}

                for l1b in l1b_files:
                    if not _check_night(l1b):
                        continue
                    geo = geo_by_time.get(_time_key(l1b.name))
                    if geo is None:
                        print(f"  No geolocation match for {l1b.name}")
                        continue
                    try:
                        eff_vent_lat, eff_vent_lon = get_detection_anchor(volcano)
                        result = process_viirs_mod.calculate_vrp(
                            l1b, geo, volcano["lat"], volcano["lon"], volcano["radius_km"],
                            vent_lat=eff_vent_lat,
                            vent_lon=eff_vent_lon,
                            vent_radius_km=volcano.get("vent_radius_km", 4.0),
                            inner_radius_km=volcano.get("inner_radius_km"),
                            exclude_zones=volcano.get("exclude_zones"),
                            active_water_bodies=volcano.get("active_water_bodies"),
                            lbg_global_compatible=volcano.get("lbg_global_compatible", False),
                            local_kernel_bg_compatible=volcano.get("local_kernel_bg", False),
                        )
                        if result:
                            store.append_record(volcano["name"], result,
                                                volcano_lat=volcano["lat"], volcano_lon=volcano["lon"],
                                                overwrite=overwrite,
                                                max_hotspot_dist_km=volcano.get("radius_km"),
                                                enable_pixel_level_distance_filter=vrp_profile.ENABLE_PIXEL_LEVEL_DISTANCE_FILTER,
                                                max_cluster_pixels=volcano.get("max_cluster_pixels"),
                                                inner_radius_km=volcano.get("inner_radius_km"),
                                                volcanic_features=VOLCANIC_FEATURES.get(volcano["name"]))
                            vent_str = (f" | VRP_VENT={result.get('vrp_vent_mw', 0)} MW"
                                        if volcano.get("vent_lat") and result.get('vrp_vent_mw', 0) > 0 else "")
                            print(f"  {result['sensor']} (750m) | VRP={result['vrp_mw']} MW | "
                                  f"T_bg={result['t_bg_k']} K | T_max={result['t_max_k']} K | "
                                  f"anomalous_px={result['n_anomalous_pixels']}{vent_str}")
                    except Exception as e:
                        print(f"  ERROR processing {l1b.name}: {e}")

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


def default_date_window(today: datetime, lookback_days: int = 7):
    """Fechas NRT por defecto: día en curso (día 0) + lookback_days atrás.

    S96: incluye el DÍA EN CURSO (día 0). Las pasadas nocturnas chilenas
    (UTC-4, las más valiosas para VRP-MIR sin contaminación solar) caen en la
    madrugada UTC del día en curso (~03:00-07:00 UTC); LANCE las publica ~3 h
    después. Procesar solo hasta ayer las perdía por ~24 h → dashboard 1 día
    atrás (decisión Nicolás S95: inaceptable para monitoreo operacional). Si
    la pasada de hoy aún no se publicó, process_date no halla granules y la
    corrida siguiente (cron cada 2h) la levanta — idempotente vía dedup
    (datetime_utc, sensor) de store.py. Orden cronológico ascendente (día más
    viejo primero) para que el último record persistido sea el más reciente.
    """
    return [today - timedelta(days=d) for d in range(lookback_days, -1, -1)]


def main():
    parser = argparse.ArgumentParser(description="VRP Chile pipeline")
    parser.add_argument("--profile", default=None, choices=_VALID_PROFILES,
                        help="Detection profile (default: mirova_equivalent). "
                             "Selects thresholds, paths, sensors and output "
                             "data subdirectory. Already consumed before "
                             "imports — this arg exists here only for --help.")
    parser.add_argument("--volcano", help="Volcano name (default: all active)")
    parser.add_argument("--date", help="Single date YYYY-MM-DD (default: today + last 7 days)")
    parser.add_argument("--start", help="Start date YYYY-MM-DD for range")
    parser.add_argument("--end", help="End date YYYY-MM-DD for range")
    parser.add_argument("--no-night-filter", action="store_true",
                        help="Process all passes including daytime (default: nighttime only)")
    parser.add_argument("--skip-noaa20", action="store_true",
                        help="Skip NOAA-20 VIIRS (useful when NASA downloads are slow)")
    parser.add_argument("--overwrite", action="store_true",
                        help="Overwrite existing records (use when reprocessing with corrected algorithms)")
    args = parser.parse_args()

    print(f"=== {vrp_profile.describe()} ===")

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
        # Default: día en curso + últimos 7 días (8 fechas). Ver
        # default_date_window() para el razonamiento (S96 día 0 + ventana
        # 7d para convergencia NRT->Standard del auto-upgrade de store.py).
        today = datetime.utcnow()
        dates = default_date_window(today)

    nighttime_only = not args.no_night_filter
    if nighttime_only:
        print("Nighttime-only mode ON (MIROVA standard). Use --no-night-filter to disable.")

    if args.skip_noaa20:
        print("Skipping NOAA-20 VIIRS products.")

    if args.overwrite:
        print("Overwrite mode ON: existing records will be replaced.")

    # S15 Tema E: scope filtering. Perfil mirova_equivalent procesa solo los
    # 11 volcanes que MIROVA monitorea (Tier A). experimental procesa todos.
    # Cuando se pide --volcano X explicito, se respeta (bypass).
    if vrp_profile.PROFILE_NAME == "mirova_equivalent" and not args.volcano:
        volcanoes = [v for v in volcanoes if v.get("mirova_monitored", False)]
        print(f"Profile mirova_equivalent: filtrado a {len(volcanoes)} volcanes "
              f"MIROVA-monitoreados.")

    for volcano in volcanoes:
        for date in dates:
            process_date(volcano, date, nighttime_only=nighttime_only,
                        skip_noaa20=args.skip_noaa20, overwrite=args.overwrite)

    print("\nDone.")


if __name__ == "__main__":
    main()
