# ════════════════════════════════════════════════════════════════════
# FICHA SDA · run_pipeline.py  ·  SDA: VRP Chile (clon MIROVA) · ID: VRP-CL
# Objetivo      : Punto de entrada del sistema: para cada volcan y dia busca las escenas, corre la
#                 deteccion por sensor y guarda los registros que publica el tablero. Al final dice que
#                 parte de la cobertura falto, para que un dato ausente no pase por «no hubo nada».
# Lógica        : Recorre volcanes y dias (el NRT: hoy y los 7 anteriores), llama a pipeline/fetch.py y a
#                 los procesadores MODIS / VIIRS 375 m / VIIRS 750 m, y guarda con pipeline/store.py. La
#                 cobertura informa fallas, plataformas que faltaron (S161: cese o cero granulos) y, por volcan y
#                 dia, busquedas vacias, L1B sin geolocalizacion y dias parciales (S159, I1).
# Modelo/método : Reglas deterministicas (orquestacion). Sin aprendizaje automatico.
# Datos entrada : volcanoes.yaml, perfil de pipeline/profiles/, granulos L1B de NASA. SIN datos personales.
# Variables     : Perfil, volcanes, ventana de fechas, filtro nocturno, modo estricto de cobertura.
# Limitaciones  : El NRT no usa el modo estricto: una cobertura incompleta avisa y sale 0, y la corrida
#                 siguiente vuelve a intentar. Una plataforma que falta se informa como nota, sin cambiar el
#                 codigo de salida.
# Refs/datos    : docs/AUDIT_S160.md (hallazgo 241); experiments/_s157_busqueda_ventana/MEDICION.md.
#                 Entrenamiento: No aplica (sin ML). Ficha: docs/FICHA_SDA_VRP_CHILE.md
# ════════════════════════════════════════════════════════════════════
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

from pipeline import fetch, process_modis, process_viirs, process_viirs_mod, store, diurno  # S151 D-10
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


def apply_volcano_overrides(volcanoes: list) -> list:
    """S124: aplica los overrides per-volcán del perfil activo.

    `volcanoes.yaml` es compartido por todos los perfiles, así que un perfil
    experimental no podía cambiar la geometría de un volcán sin arrastrar al
    producto operacional. Esto lo permite sin tocar el archivo común.

    Devuelve una lista NUEVA (copia superficial por volcán): mutar la entrada
    contaminaría a cualquier otro consumidor que ya tenga la referencia.
    """
    overrides = getattr(vrp_profile, "VOLCANO_OVERRIDES", None) or {}
    if not overrides:
        return volcanoes
    out = []
    for v in volcanoes:
        ov = overrides.get(v.get("name"))
        if not ov:
            out.append(v)
            continue
        merged = dict(v)
        merged.update(ov)
        print(f"  [perfil {vrp_profile.PROFILE_NAME}] override {v['name']}: "
              f"{', '.join(f'{k}={val}' for k, val in ov.items())}")
        out.append(merged)
    return out


def load_volcanoes(name_filter: str = None) -> list:
    with open(VOLCANOES_FILE) as f:
        cfg = yaml.safe_load(f)
    volcanoes = [v for v in cfg["volcanoes"] if v.get("active", True)]
    if name_filter:
        volcanoes = [v for v in volcanoes if v["name"] == name_filter]
    return apply_volcano_overrides(volcanoes)


def process_date(volcano: dict, date: datetime, nighttime_only: bool = True,
                 skip_noaa20: bool = False, overwrite: bool = False):
    """Download and process all granules for a volcano on a given date.

    Args:
        nighttime_only: If True, skip daytime passes (solar elevation > 0°). S151: MIROVA
            processes VIIRS by day too (Campus 2022 p. 16-17); VIIRS daytime is opened by the
            profile flag ENABLE_DAYTIME_VIIRS through pipeline/diurno.py (D-10, OFF).
        skip_noaa20: If True, skip NOAA-20 VIIRS products (useful when NASA
            downloads are slow/unreliable).
    """
    print(f"\n>>> {volcano['display_name']} | {date.strftime('%Y-%m-%d')}")

    volcano_tmp = TMP_DIR / volcano["name"] / date.strftime("%Y%m%d")

    def _check_night(l1b_path: Path, platform: str = "") -> bool:
        """True si se procesa: noche, nighttime_only apagado, o VIIRS con rama diurna (D-10)."""
        if not diurno.aplica_filtro_nocturno(nighttime_only, platform):
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
                    if not _check_night(l1b, platform):
                        continue
                    geo = geo_by_time.get(_time_key(l1b.name))
                    if geo is None:
                        _sin_geolocalizacion(volcano, date, platform, l1b)  # S159 (I1, VB-1)
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
                    if not _check_night(l1b, platform):
                        continue
                    geo = geo_by_time.get(_time_key(l1b.name))
                    if geo is None:
                        _sin_geolocalizacion(volcano, date, platform, l1b)  # S159 (I1, VB-1)
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
                    if not _check_night(l1b, platform):
                        continue
                    geo = geo_by_time.get(_time_key(l1b.name))
                    if geo is None:
                        _sin_geolocalizacion(volcano, date, platform, l1b)  # S159 (I1, VB-1)
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
        # Always delete raw granules after processing.
        # S157: salvo VRP_CONSERVAR_GRANULOS=1, que pone scripts/reproc_brazos.py para que el
        # brazo siguiente del A/B use los mismos gránulos; el driver borra el día al terminar.
        if volcano_tmp.exists() and os.environ.get("VRP_CONSERVAR_GRANULOS") != "1":
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


def _sin_geolocalizacion(volcano: dict, date: datetime, platform: str, l1b: Path) -> None:
    """S159 (I1, VB-1): un L1B en disco sin su archivo de geolocalización. Antes sólo se imprimía y la cobertura
    decía «completa»; ahora queda como incidencia (pipeline/fetch.py, TIPOS_INCIDENCIA). Función aparte, y no tres
    líneas en cada procesador, para no correr las citas archivo:línea de CLAUDE.md (guard G8)."""
    print(f"  No geolocation match for {l1b.name}")
    fetch.registrar_incidencia("sin_geolocalizacion", volcano["name"], date.strftime("%Y-%m-%d"), platform,
                               f"L1B en disco sin su geolocalización: {l1b.name}")


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


def informar_cobertura(fallas: list, ruta_json=None, estricto: bool = False,
                       plataformas: dict | None = None, incidencias: list | None = None) -> int:
    """S157: dice qué búsquedas y descargas no se pudieron hacer, y devuelve el código de salida.

    POR QUÉ: con CMR caído cada búsqueda caía en un WARN y el job salía verde sin datos
    (experiments/_s157_busqueda_ventana/MEDICION.md §3). En un reproceso eso deja un tramo
    viejo o vacío pasando por hecho (A108); con --estricto-cobertura el job sale con 3. El NRT
    no usa el modo estricto: avisa y sigue, porque la corrida siguiente vuelve a intentar.

    S161: `plataformas` es `fetch.cobertura_por_plataforma()`. POR QUÉ: un satélite que deja de
    entregar da cero gránulos, que no es una falla, y la corrida decía «completa» aunque faltara
    una plataforma entera (hallazgo 241 de docs/AUDIT_S160.md). Ahora «completa» exige además que
    ninguna plataforma esté retirada por cese anunciado ni haya dado cero en todas sus búsquedas.
    Eso se informa como nota y no cambia el código de salida: un cese anunciado es permanente y no
    debe dejar rojo cada reproceso que cruce su fecha, y en un día suelto cero gránulos puede ser
    legítimo. Que el modo estricto falle por una plataforma muda queda como decisión aparte.

    S159 (I1; AUDIT_S158_R2, R2-9 y VB-1), portado en S163: `incidencias` es
    `fetch.incidencias_de_cobertura()`, lo que no es falla pero tampoco es cobertura completa, por
    volcán y día: búsqueda sin gránulos (sin juicio: no cuenta ni en modo estricto), L1B sin
    geolocalización y día parcial (cuentan en modo estricto). Con cualquiera de ellas el resumen deja
    de decir «completa». Sin modo estricto el código de salida sigue en 0 (el NRT no cambia de color).
    """
    import json
    from collections import defaultdict
    plataformas = plataformas or {}
    incidencias = list(incidencias or [])
    cuentan = any(i.get("cuenta_estricto") for i in incidencias)
    retiradas = sorted(p for p, c in plataformas.items() if c.get("retirada"))
    sin_granulos = sorted(p for p, c in plataformas.items()
                          if c.get("sin_granulos") and not c.get("con_granulos") and not c.get("retirada"))
    if ruta_json:
        Path(ruta_json).parent.mkdir(parents=True, exist_ok=True)
        with open(ruta_json, "w", encoding="utf-8") as fh:
            json.dump({"fallas": fallas, "n": len(fallas), "plataformas": plataformas,
                       "retiradas": retiradas, "sin_granulos": sin_granulos,
                       "incidencias": incidencias, "n_incidencias": len(incidencias)},
                      fh, ensure_ascii=False, indent=1)
    if not fallas and not retiradas and not sin_granulos and not incidencias:
        print("Cobertura: completa (ninguna búsqueda ni descarga fallida, ninguna incidencia).")
        return 0
    if retiradas or sin_granulos:
        notas = [f"{p}: no se buscó en {plataformas[p]['retirada']} volcán-día por cese anunciado desde "
                 f"{plataformas[p]['cese_desde']} UTC (scripts/ceses_esperados.json)" for p in retiradas]
        notas += [f"{p}: ningún gránulo en sus {plataformas[p]['sin_granulos']} búsquedas de la corrida "
                  f"(¿la plataforma dejó de entregar?)" for p in sin_granulos]
        print("Cobertura: faltan plataformas enteras (nota, no es búsqueda fallida).")
        for n in notas:
            print(f"  {n}")
        if sin_granulos and os.environ.get("GITHUB_ACTIONS") == "true":
            print(f"::warning title=Plataforma sin gránulos::{', '.join(sin_granulos)} no dio ningún "
                  f"gránulo en toda la corrida", flush=True)
        resumen = os.environ.get("GITHUB_STEP_SUMMARY")
        if resumen:
            try:
                with open(resumen, "a", encoding="utf-8") as fh:
                    fh.write("### Plataformas que faltan\n" + "\n".join(f"- {n}" for n in notas) + "\n")
            except OSError:
                pass
    if incidencias:
        _informar_incidencias(incidencias, hay_fallas=bool(fallas))
    if not fallas:
        return 3 if (estricto and cuentan) else 0
    por_volcan = defaultdict(lambda: defaultdict(list))
    for f in fallas:
        por_volcan[f.get("volcan") or "?"][f.get("fecha") or "?"].append(f)
    print(f"Cobertura INCOMPLETA: {len(fallas)} búsquedas o descargas fallidas.")
    resumen = os.environ.get("GITHUB_STEP_SUMMARY")
    lineas = []
    for volcan, por_fecha in sorted(por_volcan.items()):
        for fecha, fs in sorted(por_fecha.items()):
            detalle = ", ".join(f"{x.get('plataforma')}:{x.get('etapa')}" for x in fs)
            print(f"  {volcan} {fecha}: {detalle} | {fs[0].get('motivo', '')[:100]}")
            lineas.append(f"- {volcan} {fecha}: {detalle}")
        if os.environ.get("GITHUB_ACTIONS") == "true":
            fechas = sorted(por_fecha)
            print(f"::warning title=Cobertura incompleta {volcan}::{len(fechas)} días con búsquedas o "
                  f"descargas fallidas: {', '.join(fechas[:12])}{' ...' if len(fechas) > 12 else ''}",
                  flush=True)
    if resumen:
        try:
            with open(resumen, "a", encoding="utf-8") as fh:
                fh.write("### Cobertura incompleta\n" + "\n".join(lineas) + "\n")
        except OSError:
            pass
    return 3 if estricto else 0


def _informar_incidencias(incidencias: list, hay_fallas: bool) -> None:
    """S159 (I1): imprime las incidencias por tipo, volcán y día, y las agrega al resumen del job.

    Sin ::warning: el NRT procesa siempre el día en curso (parcial) y vería un aviso por volcán en cada corrida."""
    from collections import defaultdict
    titulos = {"sin_granulos": "sin gránulos, sin juicio (la búsqueda respondió vacía; el código no sabe si "
                               "debía haber pasada)",
               "sin_geolocalizacion": "L1B sin geolocalización (descartados sin procesar)",
               "dia_parcial": "día parcial (no había terminado más la latencia mínima de LANCE)"}
    if hay_fallas:
        print(f"Además, {len(incidencias)} incidencias de cobertura.")
    else:
        print(f"Cobertura NO COMPLETA: {len(incidencias)} incidencias (ninguna búsqueda ni descarga fallida).")
    lineas = ["### Incidencias de cobertura"]
    por_tipo = defaultdict(lambda: defaultdict(list))
    for i in incidencias:
        por_tipo[i.get("tipo")][(i.get("volcan") or "?", i.get("fecha") or "?")].append(i)
    for tipo in sorted(por_tipo):
        cuenta = ("cuenta en modo estricto" if any(x.get("cuenta_estricto") for v in por_tipo[tipo].values()
                                                   for x in v) else "no cuenta en modo estricto")
        print(f"  {titulos.get(tipo, tipo)}; {cuenta}:")
        for (volcan, fecha), xs in sorted(por_tipo[tipo].items()):
            plat = ", ".join(str(x.get("plataforma") or "todas") for x in xs)
            print(f"    {volcan} {fecha}: {plat} | {xs[0].get('motivo', '')[:100]}")
            lineas.append(f"- {tipo}: {volcan} {fecha}: {plat}")
    resumen = os.environ.get("GITHUB_STEP_SUMMARY")
    if resumen:
        try:
            with open(resumen, "a", encoding="utf-8") as fh:
                fh.write("\n".join(lineas) + "\n")
        except OSError:
            pass


def _ventana_del_entorno(dates: list) -> tuple | None:
    """VRP_VENTANA_BUSQUEDA=INI:FIN: la ventana de búsqueda la fija quien llama (reproc_brazos,
    que corre un día por proceso dentro de la ventana del A/B). Toda fecha debe caer dentro."""
    crudo = os.environ.get("VRP_VENTANA_BUSQUEDA", "").strip()
    if not crudo:
        return None
    ini, fin = crudo.split(":")
    for d in dates:
        if not (ini <= d.strftime("%Y-%m-%d") <= fin):
            raise SystemExit(f"VRP_VENTANA_BUSQUEDA={crudo} no contiene la fecha {d:%Y-%m-%d}")
    return ini, fin


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
    parser.add_argument("--cobertura-json", default=None,
                        help="S157: escribe aquí las búsquedas y descargas que no se pudieron hacer")
    parser.add_argument("--estricto-cobertura", action="store_true",
                        help="S157: sale con código 3 si hubo búsquedas o descargas fallidas "
                             "(reprocesos; el NRT no lo usa)")
    args = parser.parse_args()

    # S120 (cacería de bugs): --start sin --end (o viceversa) caía en silencio
    # a la ventana NRT default de 8 días — fechas equivocadas sin aviso.
    if bool(args.start) != bool(args.end):
        parser.error("--start y --end deben usarse juntos (rango de fechas)")

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
    # S151 D-10: el perfil puede abrir el día sólo para VIIRS. Se avisa en el log para que una
    # corrida del A/B diurno no se confunda con una nocturna (con el flag apagado no se imprime).
    if diurno.flag_viirs_diurno():
        print("Rama diurna VIIRS ABIERTA por perfil (ENABLE_DAYTIME_VIIRS): VIIRS se procesa de "
              "día con la Tabla 1 diurna de Coppola 2016a; MODIS sigue con su propia regla.")

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

    # S157: una búsqueda a CMR por producto y por ventana, no una por día (pipeline/fetch.py).
    ventana_env = _ventana_del_entorno(dates)
    fetch.limpiar_fallas()

    for volcano in volcanoes:
        fetch.reiniciar_ventana()
        fetch.configurar_ventana(dates, cache_dir=os.environ.get("VRP_CACHE_BUSQUEDA_DIR") or None,
                                 ventana=ventana_env)
        for date in dates:
            # S120 (cacería): los breakers de fetch son per-día; sin reset, un
            # timeout transitorio del día 1 silenciaba todos los días restantes
            # de un reproceso multi-día (backfill).
            fetch.reset_transient_breakers()
            process_date(volcano, date, nighttime_only=nighttime_only,
                        skip_noaa20=args.skip_noaa20, overwrite=args.overwrite)

    codigo = informar_cobertura(fetch.fallas_de_cobertura(), ruta_json=args.cobertura_json,
                                estricto=args.estricto_cobertura,
                                plataformas=fetch.cobertura_por_plataforma(),
                                incidencias=fetch.incidencias_de_cobertura())
    print("\nDone.")
    sys.exit(codigo)


if __name__ == "__main__":
    main()
