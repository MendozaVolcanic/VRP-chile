"""
fetch.py — Download MODIS and VIIRS L1B granules from NASA Earthdata via earthaccess.

For each volcano, downloads:
  - MODIS: MOD021KM (Terra) + MYD021KM (Aqua) + corresponding MOD03/MYD03 geolocation
  - VIIRS: VNP02IMG (Suomi-NPP) + VJ102IMG (NOAA-20) + geolocation VNP03IMG/VJ103IMG

Granules are saved to a temp directory, processed, then deleted.
"""

import math
import os
import socket
from datetime import datetime, timedelta
from pathlib import Path


# S72 — local NRT testing support: cargar `.env` del repo root si existe.
# Permite correr pipeline local sin setear env vars en cada shell. El `.env`
# está en `.gitignore` (no se commitea). Parse manual minimal — NO requiere
# python-dotenv para minimizar dependencias en CI. Si la variable ya está
# definida en el ambiente (e.g. CI con GH Secrets), tiene prioridad sobre `.env`.
# Ver docs/LOCAL_NRT_SETUP.md para setup.
def _load_dotenv_if_present() -> None:
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return
    try:
        with env_path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip().strip("'").strip('"')
                # Solo seteamos si NO está ya en env (GH Secrets prioridad).
                if key and key not in os.environ:
                    os.environ[key] = val
    except OSError:
        pass  # archivo ilegible — silenciamos para no romper CI.


_load_dotenv_if_present()


import earthaccess  # noqa: E402 — debe ir después de _load_dotenv para que earthaccess vea el token

# H7 (S35): Force IPv4 for NASA Earthdata DNS resolution. Errno 101
# "Network is unreachable" en GitHub-hosted runners es típicamente IPv6
# routing degradado — el runner resuelve urs.earthdata.nasa.gov a una
# dirección IPv6 y no puede rutear. Forzar AF_INET evita el problema sin
# afectar nada local. Aplica solo al proceso (no al sistema).
_orig_getaddrinfo = socket.getaddrinfo
def _ipv4_only_getaddrinfo(host, *args, **kwargs):
    res = _orig_getaddrinfo(host, *args, **kwargs)
    res4 = [r for r in res if r[0] == socket.AF_INET]
    return res4 if res4 else res  # fallback al original si no hay IPv4
socket.getaddrinfo = _ipv4_only_getaddrinfo

# H7b (S47): Override connect/read timeout para hosts NASA Earthdata.
# earthaccess.auth._find_or_create_token() pasa timeout=10s hardcoded en su
# session.post() → si urs.earthdata.nasa.gov tarda >10s en TLS handshake
# (carga alta o degradación intermitente, observado 9 runs consecutivos
# fallidos 2026-05-16), el connect timeout dispara ANTES de cualquier
# retry de nuestro auth(). Solución: monkeypatch requests.Session.request
# para forzar timeout mínimo 60s en hosts NASA. Tests reales (S47): NASA
# responde en 200-800ms cuando OK, falla limpio cuando down — pero cuando
# está saturada puede tardar 15-30s. 60s es defensivo.
try:
    import requests as _requests
    _NASA_HOSTS = ("urs.earthdata.nasa.gov", "cmr.earthdata.nasa.gov",
                   "data.lpdaac.earthdatacloud.nasa.gov", "ladsweb.modaps.eosdis.nasa.gov",
                   "nrt3.modaps.eosdis.nasa.gov")
    _MIN_TIMEOUT = 60.0
    _orig_session_request = _requests.Session.request
    def _request_with_nasa_timeout(self, method, url, **kwargs):
        if any(h in url for h in _NASA_HOSTS):
            t = kwargs.get("timeout")
            if t is None:
                kwargs["timeout"] = _MIN_TIMEOUT
            elif isinstance(t, (int, float)) and t < _MIN_TIMEOUT:
                kwargs["timeout"] = _MIN_TIMEOUT
            elif isinstance(t, tuple) and len(t) == 2:
                connect_t, read_t = t
                kwargs["timeout"] = (max(connect_t, 30.0), max(read_t, _MIN_TIMEOUT))
        return _orig_session_request(self, method, url, **kwargs)
    _requests.Session.request = _request_with_nasa_timeout
except ImportError:
    pass  # requests no instalado (entornos de test sin red)


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


# S70-0 T2: probe rápido NASA Earthdata auth endpoint.
# Cuando urs.earthdata.nasa.gov:443 está caído upstream (saturado, mantenimiento,
# o balancer drop SYN-ACK), el handshake TLS no completa y cada attempt agota su
# connect-timeout de 60s. Con 8 reintentos esto produce ~22 min de espera muerta
# por job — 31 min totales en runners GitHub Actions. T1 (commit c6373aa) midió
# 19/20 runs fallidos en este patrón. El probe TCP rápido (5s) detecta el outage
# antes y permite acortar la budget a ~2 min, liberando los runners para el cron.
NASA_AUTH_HOST = "urs.earthdata.nasa.gov"
NASA_AUTH_PORT = 443
_PROBE_FAIL_DELAYS = [0, 30, 90]  # 3 attempts, ~2 min total when probe fails


def _probe_nasa_auth(timeout: float = 5.0) -> bool:
    """Probe TCP rápido a NASA Earthdata auth endpoint.

    Devuelve True si el handshake TCP a (NASA_AUTH_HOST, 443) completa en <timeout>
    segundos, False en cualquier error (timeout, connection refused, OSError de red).

    NOTA: solo testea reachability TCP/443. NO valida TLS handshake ni credenciales
    — eso lo hace earthaccess.login() después. Es suficiente para distinguir
    "NASA upstream caída" de "todo OK", que es la única decisión que necesitamos
    tomar para escoger entre budget largo (22 min) y budget corto (2 min).
    """
    try:
        with socket.create_connection((NASA_AUTH_HOST, NASA_AUTH_PORT), timeout=timeout):
            return True
    except (socket.timeout, OSError):
        return False


def auth():
    """Authenticate with NASA Earthdata.

    Strategy order: environment vars → netrc (si archivo existe). Falla solo si
    NINGUNA funciona. Permite correr local con `~/_netrc` (Windows) o `~/.netrc`
    (Unix) sin requerir env vars. CI sigue usando env vars (secrets GitHub
    Actions); netrc se skipea automáticamente si no existe.

    S72 EARTHDATA_TOKEN bypass (fix throttling NASA-Azure):
    earthaccess 0.17.0 `_get_credentials` prefiere automáticamente
    `EARTHDATA_TOKEN` env var sobre `EARTHDATA_USERNAME`+`EARTHDATA_PASSWORD`.
    Cuando `EARTHDATA_TOKEN` está seteado: setea `self.token = {"access_token":
    user_token}` + `self.authenticated = True` directamente, SIN llamar
    `_find_or_create_token` (el endpoint que NASA throttle desde rango IP /16
    de Azure GH-hosted runners — DoS-mitigation colateral confirmado en
    forum.earthdata.nasa.gov t=2764). Esto resuelve el issue NRT cron post-#103
    que en S71-S72 fallaba 100% por ConnectTimeout al endpoint token-creation.
    Setup: ver `docs/EARTHDATA_TOKEN_SETUP.md`. Token vida 60 días, rotar c/50.

    H6 S22 retry+backoff: 4 intentos con waits 5s/15s/45s para mitigar
    "Network is unreachable" intermitente. Bug fix S22 (run 07:14 failure):
    netrc fallback solo si archivo existe — antes lanzaba FileNotFoundError
    en CI runners ocultando el verdadero error de environment.

    H7 S35 extended retry: subido a 6 intentos con waits hasta 180s para
    mitigar transients de hasta ~5 min observados en runs 9-10 mayo. Combinar
    con IPv4 force (top of file) que apunta al root cause más probable.

    H7b S47 extended further: 9 runs consecutivos fallidos 2026-05-16 por
    ConnectTimeout en urs.earthdata.nasa.gov:443 — degradación >5 min.
    Subido a 8 intentos hasta 480s (waits 0/10/30/60/120/240/360/480, ~22 min
    total) + override de timeout requests a 60s (top of file). Si NASA tarda
    en recuperarse >22 min, el job falla y el siguiente cron (cada 2h) reintenta.

    S70-0 T2 fix outage upstream: probe TCP a urs.earthdata.nasa.gov:443 antes
    del retry loop. Si el probe falla en 5s, la budget se acorta a _PROBE_FAIL_DELAYS
    (~2 min) y al agotarse lanza RuntimeError("NASA_AUTH_UNREACHABLE: ...") con
    mensaje distinguible para que el workflow nrt.yml pueda etiquetar el run
    como [NASA_DOWN] sin cambiar el exit code (badge sigue rojo, decisión
    conservadora Nicolás S70-0). Si el probe pasa, comportamiento normal con
    budget largo de 22 min.
    """
    import os
    import time
    netrc_path_unix = os.path.expanduser("~/.netrc")
    netrc_path_win = os.path.expanduser("~/_netrc")
    has_netrc = os.path.exists(netrc_path_unix) or os.path.exists(netrc_path_win)

    # Probe TCP rápido. Si NASA upstream está caída, acortamos budget de 22 min
    # a ~2 min para no desperdiciar minutos de GitHub Actions × 9 vols × cada cron.
    probe_ok = _probe_nasa_auth(timeout=5.0)
    if probe_ok:
        delays = [0, 10, 30, 60, 120, 240, 360, 480]  # 8 attempts, ~22 min total
    else:
        delays = list(_PROBE_FAIL_DELAYS)  # ~2 min total

    last_err = None
    for delay in delays:
        if delay:
            time.sleep(delay)
        try:
            earthaccess.login(strategy="environment")
            return
        except Exception as e:
            last_err = e
        if has_netrc:
            try:
                earthaccess.login(strategy="netrc")
                return
            except Exception as e:
                last_err = e

    # Si aquí, todos los attempts fallaron. Si la causa fue probe failure,
    # marcamos el error como NASA_AUTH_UNREACHABLE para que nrt.yml lo detecte.
    if not probe_ok:
        raise RuntimeError(
            f"NASA_AUTH_UNREACHABLE: NASA Earthdata auth ({NASA_AUTH_HOST}:{NASA_AUTH_PORT}) "
            f"no responde a probe TCP en 5s ni a {len(delays)} reintentos cortos "
            f"(budget {sum(_PROBE_FAIL_DELAYS)}s). Upstream outage. Última excepción: {last_err}"
        )
    # Caso probe OK pero login falló igualmente — credencial inválida, glitch
    # transient o similar. Reraise el último error original (será environment
    # error en CI, netrc error solo si netrc existe).
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
