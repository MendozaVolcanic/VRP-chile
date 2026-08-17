"""
fetch.py — Download MODIS and VIIRS L1B granules from NASA Earthdata via earthaccess.

For each volcano, downloads:
  - MODIS: MOD021KM (Terra) + MYD021KM (Aqua) + corresponding MOD03/MYD03 geolocation
  - VIIRS: VNP02IMG (Suomi-NPP) + VJ102IMG (NOAA-20) + geolocation VNP03IMG/VJ103IMG

Granules are saved to a temp directory, processed, then deleted.
"""

import math
import os
import re
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


# ── F55/S77 — Profile-bypass para earthaccess.Store ───────────────────────────
# Bug F55 (PR #199 investigation): earthaccess >= 0.17.0 `Store.__init__`
# llama `set_requests_session("https://urs.earthdata.nasa.gov/profile")` para
# sembrar cookies URS, AUNQUE haya EARTHDATA_TOKEN seteado. En runners Azure
# de GH Actions ese host está bloqueado/timea-out → ConnectTimeoutError →
# NRT cron caído. F51 fix anterior (probe-gate) eliminó el primer síntoma
# pero el GET a /profile sigue pasando dentro de Store.__init__.
#
# Fix: monkey-patch `Store.set_requests_session` para no-op cuando URL
# contiene "/profile" Y EARTHDATA_TOKEN está seteado. Las cookies URS
# NO son necesarias para granule downloads (la session ya lleva
# Authorization: Bearer <token>).
#
# Idempotente: instalar 2 veces = 1 patch efectivo (no recursión).
_profile_bypass_installed = False


def _install_profile_bypass():
    """F55: monkey-patch earthaccess.Store.set_requests_session bypass /profile."""
    global _profile_bypass_installed
    if _profile_bypass_installed:
        return
    import earthaccess.store as eastore  # local import para evitar circular
    if hasattr(eastore.Store, "_original_set_requests_session"):
        # Ya parcheado antes (test fixture reset puede haberlo dejado a medias)
        eastore.Store.set_requests_session = (
            eastore.Store._original_set_requests_session
        )
        delattr(eastore.Store, "_original_set_requests_session")
    original = eastore.Store.set_requests_session

    def _patched_set_requests_session(self, url, *args, **kwargs):
        if "/profile" in (url or "") and os.environ.get("EARTHDATA_TOKEN", "").strip():
            # F55 bypass refined (S84): skip GET a /profile cuando hay token,
            # PERO preservar setup de _http_session — el original lo hacía
            # como side-effect (línea `if not hasattr(self, "_http_session"):
            # self._http_session = self.auth.get_session()`). Sin esto,
            # download() después falla "session hasn't been set up yet" y
            # el NRT termina exit 0 sin records desde 2026-05-23 (bug F55
            # pre-S84). Las cookies URS siguen sin ser necesarias — el token
            # lleva Authorization: Bearer.
            if not hasattr(self, "_http_session"):
                self._http_session = self.auth.get_session()
            return None
        return original(self, url, *args, **kwargs)

    eastore.Store._original_set_requests_session = original
    eastore.Store.set_requests_session = _patched_set_requests_session
    _profile_bypass_installed = True


# Instalar el patch ANTES de cualquier earthaccess.login() en este módulo.
_install_profile_bypass()

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
    # F55/S77 defensa-en-profundidad: re-instalar el profile-bypass por si
    # algún caller (test fixture, monkey-patch ajeno) lo deshizo entre
    # imports. Idempotente — no-op si ya está instalado.
    _install_profile_bypass()
    netrc_path_unix = os.path.expanduser("~/.netrc")
    netrc_path_win = os.path.expanduser("~/_netrc")
    has_netrc = os.path.exists(netrc_path_unix) or os.path.exists(netrc_path_win)

    # F51/S77 fix — Token bypass debe saltar el probe-gate S70-0.
    # earthaccess >= 0.17.0 con EARTHDATA_TOKEN seteado NUNCA toca el host
    # problemático urs.earthdata.nasa.gov (skip _find_or_create_token). El
    # probe TCP S70-0 a ese mismo host NO aporta info útil cuando hay token,
    # y el raise NASA_AUTH_UNREACHABLE final aborta el cron sin razón.
    # Pre-fix: NRT 100% caído 2026-05-23+ aunque token OK en workflow.
    # Whitespace-only treated as no token (defensa vs templating yaml).
    has_token = bool((os.environ.get("EARTHDATA_TOKEN") or "").strip())

    # Probe TCP rápido. Si NASA upstream está caída, acortamos budget de 22 min
    # a ~2 min para no desperdiciar minutos de GitHub Actions × 9 vols × cada cron.
    if has_token:
        # Con token, skip probe completamente (no aporta info — bypass evita
        # el host). Budget largo para retries de otros transients (granule DL).
        probe_ok = True
        delays = [0, 10, 30, 60, 120, 240, 360, 480]
    else:
        probe_ok = _probe_nasa_auth(timeout=5.0)
        if probe_ok:
            delays = [0, 10, 30, 60, 120, 240, 360, 480]
        else:
            delays = list(_PROBE_FAIL_DELAYS)

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

    # Si aquí, todos los attempts fallaron. Si la causa fue probe failure
    # (y NO había token bypass), marcamos NASA_AUTH_UNREACHABLE para que
    # nrt.yml lo detecte. Con token la etiqueta sería engañosa — el bypass
    # no toca el host del probe, así que un fallo con token es OTRA cosa
    # (credencial inválida, glitch del granule download, etc).
    if not probe_ok and not has_token:
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


# ── S116 — circuit-breaker por host de BÚSQUEDA CMR (espejo de A64 para search) ──
# POR QUÉ: el breaker S102/S109 protege el host de DESCARGA (ConnectTimeout). La
# búsqueda de metadata va a `cmr.earthdata.nasa.gov` vía earthaccess.search_data, y
# ese host puede dar ReadTimeout: acepta la conexión TCP pero responde lento. Incidente
# Copahue (run 28244166333, 26-jun-2026): ReadTimeout 60s (el override de timeout del
# top del file) repetido en los 8 sensores → >50min → timeout del job. A diferencia de
# la descarga, ReadTimeout NO se cura con un probe TCP (el connect SÍ completa; el
# problema es la lentitud de respuesta), así que NO replicamos el reprobe S109: al 1er
# Timeout/ConnectionError de CMR marcamos la búsqueda degradada PARA ESTA CORRIDA y las
# búsquedas siguientes devuelven [] al instante. Degradación segura: sin granules ese
# día → la corrida nrt-retry (~30min después) reintenta con el breaker reseteado (estado
# por-proceso). Kill-switch: env VRP_CMR_BREAKER=0 → comportamiento previo (sin breaker).
_CMR_SEARCH_DOWN: bool = False
ENABLE_CMR_SEARCH_BREAKER: bool = os.environ.get("VRP_CMR_BREAKER", "1") != "0"


def reset_transient_breakers():
    """S120 (cacería): los breakers (CMR search + hosts de descarga) se diseñaron
    para corridas de 1 día NRT (estado por-proceso, el retry ~30min los resetea).
    Pero run_pipeline loopea rangos multi-día en UN proceso (backfill/reproc):
    un timeout transitorio del día 1 degradaba TODOS los días restantes a []
    silencioso. run_pipeline llama esto al inicio de cada fecha."""
    global _CMR_SEARCH_DOWN
    _CMR_SEARCH_DOWN = False
    _DOWN_DOWNLOAD_HOSTS.clear()
try:
    # requests.Timeout = base de ReadTimeout y ConnectTimeout; ConnectionError aparte.
    from requests.exceptions import Timeout as _Timeout, \
        ConnectionError as _ReqConnErr
    _CMR_SEARCH_ERRORS = (_Timeout, _ReqConnErr)
except Exception:  # pragma: no cover — requests siempre presente
    _CMR_SEARCH_ERRORS = _CONNECT_ERRORS or (Exception,)


# ---------------------------------------------------------------------------
# S123 — credencial muerta ≠ host caído.
#
# Todo lo de arriba (breakers A64/S102 y S116) asume fallas TRANSITORIAS de red:
# degradar a [] y seguir es correcto porque la corrida siguiente recupera. Una
# credencial rechazada es lo contrario: permanente hasta que un humano rote el
# secret. Reintentarla no la cura y degradarla la esconde — el 2026-07-20 expiró
# el token y el cron corrió 13 días "verde" sin producir un dato (107 runs),
# porque el rechazo terminaba en el catch-all de fetch_for_volcano como un WARN.
#
# earthaccess ≥0.17 envuelve el rechazo HTTP en `RuntimeError(response.text)`,
# perdiendo el tipo pero conservando el status en `__cause__.response`. Por eso
# hay que mirar ambos, y caer al texto cuando ni eso sobrevive.
# ---------------------------------------------------------------------------
class EarthdataCredentialError(RuntimeError):
    """Credencial NASA inválida/expirada: permanente, requiere intervención."""


# Un 401 ya es inequívoco. Un 403 NO alcanza: NASA lo usa también para
# colecciones sin EULA aceptada y para throttling, y abortar por eso mataría el
# NRT entero por un solo sensor. Para 403 (o status ausente) exigimos que el
# cuerpo hable explícitamente de la credencial.
_CRED_DEAD_PAT = re.compile(
    r"token .{0,40}?(expired|invalid|revoked)"
    r"|invalid[_ ](credentials|token)"
    r"|unauthorized",
    re.I)


def _is_credential_dead(exc: BaseException) -> tuple[bool, int | None]:
    """¿Este error es 'la credencial no sirve' (y no 'la red falló')?

    Devuelve (es_credencial_muerta, status_http_si_se_pudo_recuperar).
    """
    resp = (getattr(getattr(exc, "__cause__", None), "response", None)
            or getattr(exc, "response", None))
    code = getattr(resp, "status_code", None)
    body = (str(exc) or "")[:400]
    if code == 401:
        return True, 401
    if code == 403 and _CRED_DEAD_PAT.search(body):
        return True, 403
    if code is None and _CRED_DEAD_PAT.search(body):
        return True, None
    return False, code


def _raise_if_credential_dead(exc: BaseException, where: str) -> None:
    """Reclasifica y aborta si la causa es la credencial; si no, no hace nada."""
    dead, code = _is_credential_dead(exc)
    if not dead:
        return
    raise EarthdataCredentialError(
        f"EARTHDATA_CREDENTIAL_INVALID [{where}]: NASA rechazó la credencial "
        f"(HTTP {code if code is not None else '?'}). Hay que **rotar** el "
        f"secret EARTHDATA (ver docs/EARTHDATA_TOKEN_SETUP.md) — no es un "
        f"outage y reintentar no lo cura. Detalle: {str(exc)[:200]}"
    ) from exc


def search_granules(product_key: str, lat: float, lon: float,
                    radius_km: float, date: datetime) -> list:
    """
    Search for granules covering a given location on a given date.

    Returns a list of earthaccess granule objects.

    S116 circuit-breaker (incidente Copahue): si CMR (`cmr.earthdata.nasa.gov`)
    ya dio Timeout/ConnectionError en esta corrida, devuelve [] al instante (no
    quema otro ReadTimeout de 60s por cada sensor restante). Ver bloque arriba.
    """
    global _CMR_SEARCH_DOWN
    # Breaker CMR-search: si ya tripeó en esta corrida, fast-fail (degrada a []).
    if ENABLE_CMR_SEARCH_BREAKER and _CMR_SEARCH_DOWN:
        _diag(f"SEARCH_SKIP CMR degradada esta corrida [{product_key}]")
        return []

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
            try:
                results = earthaccess.search_data(
                    short_name=attempt["short_name"],
                    version=ver,
                    bounding_box=bbox,
                    temporal=(date_str, date_str),
                    count=20,
                )
            except _CMR_SEARCH_ERRORS as e:
                # S116: CMR caído/lento → tripear el breaker para la corrida y
                # degradar a [] (no reintentar versiones ni quemar 60s × sensores).
                if ENABLE_CMR_SEARCH_BREAKER:
                    _CMR_SEARCH_DOWN = True
                    _diag(f"SEARCH_CMR_TIMEOUT host=cmr.earthdata.nasa.gov -> breaker ON "
                          f"esta corrida [{product_key}] err={type(e).__name__}: {str(e)[:90]}")
                    return []
                raise  # breaker OFF → comportamiento previo (propaga)
            except Exception as e:
                # S123: acá llega el rechazo de credencial (earthaccess lo
                # envuelve en RuntimeError, así que no cae en el except de
                # arriba — y está bien que no caiga: no debe tripear el breaker
                # de red). Si es la credencial, aborta; cualquier otra cosa
                # sigue propagando como antes.
                _raise_if_credential_dead(e, f"search:{product_key}")
                raise
            if results:
                return results
    return []


def _diag(msg: str) -> None:
    """S102 — diagnostic boundary log (timestamped, flushed). print-only, sin
    cambio de comportamiento. Sirve para ubicar EXACTAMENTE dónde se cuelga el
    NRT cron cuando un job timeoutea a 50 min (hipótesis: earthaccess.download
    sin timeout de pared). flush=True es crítico: el stdout debe llegar al log
    de GitHub ANTES de que el timeout mate el proceso. Ver
    docs/superpowers/specs (incidente NRT) + project_s102_estado."""
    import time as _t
    print(f"[diag {_t.strftime('%H:%M:%S', _t.gmtime())}Z] {msg}", flush=True)


# ── S102 — circuit-breaker por host de descarga ───────────────────────────────
# Root cause incidente NRT (run 27085208578, prueba instrumentada): el host LANCE
# `nrt3.modaps.eosdis.nasa.gov` da ConnectTimeout a 183s; reintentar 4× por cada
# granule × varias plataformas VIIRS NRT acumula >50min → timeout del job. Un host
# caído NO se cura reintentando. Patrón análogo a _probe_nasa_auth (S70-0) pero para
# el host de descarga: al 1er ConnectTimeout marcamos el host caído PARA ESTA CORRIDA
# y las descargas siguientes de ese host fallan al instante (devolvemos lo de LAADS,
# que sí responde). El reintento real lo da nrt-retry.yml (~30min después, host puede
# haberse recuperado). Estado por-proceso → cada job de GH Actions arranca limpio.
_DOWN_DOWNLOAD_HOSTS: set = set()

# S109 — resiliencia a timeouts TRANSITORIOS: antes de marcar un host caído para TODA
# la corrida (S102 all-or-nothing), probe TCP rápido (5s). Si responde = blip ya
# recuperado → reintentar; si no = caído de verdad → marcar + saltar (S102). Acota el
# caso "un blip de 60s en la 1ª descarga pierde el día del volcán" (incidente S109:
# Láscar/Isluga/Villarrica ~1 día atrás por `nrt3.modaps` intermitente). El loop de 4
# intentos acota el peor caso (NO reintroduce el cuelgue de 50min). Kill-switch: env
# VRP_HOST_REPROBE=0 desactiva y vuelve al comportamiento S102. Default ON.
ENABLE_DOWNLOAD_HOST_REPROBE: bool = os.environ.get("VRP_HOST_REPROBE", "1") != "0"

# ConnectTimeout/ConnectionError = el host no acepta la conexión (caído/bloqueado).
# Se distingue de ReadTimeout u otros transients (esos SÍ se reintentan).
try:
    from requests.exceptions import ConnectTimeout as _ConnectTimeout, \
        ConnectionError as _ConnectionError
    _CONNECT_ERRORS = (_ConnectTimeout, _ConnectionError)
except Exception:  # pragma: no cover — requests siempre está, defensa
    _CONNECT_ERRORS = ()


def _granule_hosts(granules: list) -> set:
    """Hosts (netloc) de los data_links de los granules. Vacío si no se puede
    determinar (degradación segura: no se hace skip). earthaccess DataGranule
    expone .data_links()."""
    from urllib.parse import urlparse
    hosts = set()
    for g in granules:
        try:
            for url in g.data_links():
                h = urlparse(url).netloc
                if h:
                    hosts.add(h)
        except Exception:
            pass
    return hosts


def _probe_download_host(host: str, timeout: float = 5.0) -> bool:
    """Probe TCP rápido a un host de descarga (puerto 443). True si el connect TCP
    completa en <timeout>s, False en timeout/refused/OSError de red. Espejo de
    _probe_nasa_auth (S70-0): distingue 'host caído' de 'blip transitorio ya
    recuperado' ANTES de tripear el circuit-breaker para toda la corrida (S109).
    Solo testea reachability TCP/443 (no el download) — suficiente para la decisión
    retry-vs-skip, igual que el probe de auth para la decisión budget-largo-vs-corto."""
    if not host:
        return False
    try:
        with socket.create_connection((host, 443), timeout=timeout):
            return True
    except (socket.timeout, OSError):
        return False


def download_granules(granules: list, dest_dir: Path) -> list[Path]:
    """Download a list of granules to dest_dir. Returns list of local file paths.

    H6 S22 retry+backoff: para errores transitorios (ReadTimeout, etc.) reintenta
    con waits 10s/30s/60s. Cada intento llama earthaccess.download completo; si
    parcialmente exitoso (algunos files OK), retorna lo que pudo.

    S102 circuit-breaker (root cause NRT, run 27085208578): para ConnectTimeout
    /ConnectionError (host caído) NO reintenta 4× (no se cura) — falla rápido y
    marca el host caído para la corrida, de modo que las descargas siguientes de
    ese host se saltan al instante. Esto evita acumular 4×183s × N granules > 50min.
    Markers _diag para diagnóstico continuo.
    """
    import time
    dest_dir.mkdir(parents=True, exist_ok=True)
    names = ",".join(str(g.get("umm", {}).get("GranuleUR", "?"))[:40] for g in granules) \
        if all(hasattr(g, "get") for g in granules) else f"{len(granules)} items"
    hosts = _granule_hosts(granules)

    # Circuit-breaker: si TODOS los hosts destino ya fallaron ConnectTimeout en
    # esta corrida, fallar al instante (no quemar otro connect-timeout largo).
    if hosts and hosts <= _DOWN_DOWNLOAD_HOSTS:
        _diag(f"DOWNLOAD_SKIP host caído {sorted(hosts)} [{names}]")
        raise RuntimeError(f"download host(s) down this run: {sorted(hosts)}")

    delays = [0, 10, 30, 60]
    last_err = None
    for attempt, delay in enumerate(delays):
        if delay:
            time.sleep(delay)
        t0 = time.time()
        _diag(f"DOWNLOAD_START attempt={attempt} n={len(granules)} dest={dest_dir.name} [{names}]")
        try:
            paths = earthaccess.download(granules, local_path=str(dest_dir))
            _diag(f"DOWNLOAD_DONE attempt={attempt} elapsed={time.time()-t0:.1f}s n_files={len(paths)}")
            return [Path(p) for p in paths if Path(p).exists()]
        except _CONNECT_ERRORS as e:
            last_err = e
            # S109 — resiliencia a blip transitorio: antes de marcar el host caído PARA
            # LA CORRIDA, probe TCP rápido (5s). Si el host responde = fue un timeout
            # transitorio (ya recuperado) → reintentar (continue, sin marcar caído). Si
            # no responde, o ya es el último intento → caído de verdad → marcar + fallar
            # rápido (comportamiento S102). El loop de 4 intentos acota el peor caso →
            # NO reintroduce el cuelgue de 50min (probe 5s << ConnectTimeout 60s).
            if (ENABLE_DOWNLOAD_HOST_REPROBE and hosts
                    and attempt < len(delays) - 1
                    and all(_probe_download_host(h) for h in hosts)):
                _diag(f"DOWNLOAD_REPROBE_OK attempt={attempt} elapsed={time.time()-t0:.1f}s "
                      f"host={sorted(hosts)} → blip transitorio, reintentando")
                continue
            # Host caído: marcar + fallar rápido (no reintentar). nrt-retry.yml
            # reintenta la corrida ~30min después con el circuit-breaker reseteado.
            if hosts:
                _DOWN_DOWNLOAD_HOSTS.update(hosts)
            _diag(f"DOWNLOAD_CONNFAIL attempt={attempt} elapsed={time.time()-t0:.1f}s "
                  f"host_down={sorted(hosts) or 'unknown'} err={type(e).__name__}: {str(e)[:90]}")
            break
        except Exception as e:
            _diag(f"DOWNLOAD_ERR attempt={attempt} elapsed={time.time()-t0:.1f}s err={type(e).__name__}: {str(e)[:120]}")
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
    _diag(f"AUTH_START volcano={volcano.get('name','?')} date={date:%Y-%m-%d}")
    auth()
    _diag("AUTH_OK")
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
            _diag(f"SEARCH_START {platform}")
            l1b_granules = search_granules(l1b_key, lat, lon, radius, date)
            _diag(f"SEARCH_DONE {platform} n_l1b={len(l1b_granules)}")
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
        except EarthdataCredentialError:
            # S123: NO degradar. Este catch-all es justo donde el token expirado
            # se convertía en un WARN inofensivo y el job terminaba exit 0 con
            # cero granules — 13 días de cron "verde" sin datos. Si la credencial
            # está muerta, todas las plataformas van a fallar igual: que el run
            # muera ruidoso y con la causa en el mensaje.
            raise
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
