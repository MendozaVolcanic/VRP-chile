"""S123 — credencial Earthdata muerta debe ABORTAR la corrida, no degradar en silencio.

El incidente que motiva esto: el 2026-07-20 expiró el token de NASA. El pipeline
no distinguió "credencial muerta" de "host caído" y trató el rechazo como un
error transitorio cualquiera: lo atrapó el catch-all de `fetch_for_volcano`,
imprimió un WARN, devolvió `[]` y terminó **exit 0**. El cron siguió corriendo
"verde" 13 días sin producir un solo dato (23-jul → 04-ago, 107 runs).

La distinción es física, no cosmética:
  - host caído / lento  → transitorio. Degradar y seguir es correcto: el dato
    llega en la corrida siguiente (breakers A64/S102 y S116).
  - credencial rechazada → permanente hasta que un humano rote el secret.
    Reintentar no lo cura y degradar lo esconde. Debe fallar RUIDOSO.

Cadena exacta del bug (verificada en el código y en el log de AUDIT_S122:18):
earthaccess ≥0.17 hace `except requests.HTTPError as ex: raise RuntimeError(
ex.response.text)`, o sea un RuntimeError cuyo texto es el body JSON y cuyo
`__cause__` conserva el status 401. Ese RuntimeError NO está en
`_CMR_SEARCH_ERRORS` (bien: no debe tripear el breaker de red), así que subía
intacto hasta el `except Exception` de `fetch_for_volcano`.

Estos tests fijan el comportamiento (anti-regresión):
  - 401 → EarthdataCredentialError con mensaje accionable (rotar secret).
  - el catch-all de fetch_for_volcano NO se la traga  ← captura el bug real.
  - un 401 NO tripea los breakers de red (son mecanismos ortogonales).
  - ReadTimeout sigue degradando a [] (no rompimos A64/S116).
  - un 403 de permisos/EULA NO aborta: es por colección, no por credencial.
"""
from datetime import datetime
from pathlib import Path

import pytest
import requests
from requests.exceptions import ReadTimeout

import pipeline.fetch as fetch

PKEY = "MODIS_TERRA_L1B"
VOLCANO = {"name": "Lascar", "lat": -23.37, "lon": -67.73, "radius_km": 25.0,
           "sensors": ["MODIS"]}


def _earthaccess_style_error(status: int, body: bytes):
    """Réplica de cómo earthaccess envuelve un rechazo HTTP de CMR.

    Devuelve el RuntimeError ya construido, con __cause__ = HTTPError (que es
    donde sobrevive el status_code real).
    """
    resp = requests.Response()
    resp.status_code = status
    resp._content = body
    try:
        resp.raise_for_status()
    except requests.HTTPError as ex:
        return RuntimeError(ex.response.text)


TOKEN_EXPIRED = (401, b'{"errors":["Token [ABC] has expired. Please get a new token"]}')
EULA_DENIED = (403, b'{"errors":["User does not have permission to access collection"]}')


@pytest.fixture(autouse=True)
def _reset_breakers(monkeypatch):
    fetch._CMR_SEARCH_DOWN = False
    fetch._DOWN_DOWNLOAD_HOSTS.clear()
    monkeypatch.setattr(fetch, "ENABLE_CMR_SEARCH_BREAKER", True)
    yield
    fetch._CMR_SEARCH_DOWN = False
    fetch._DOWN_DOWNLOAD_HOSTS.clear()


def test_expired_token_raises_credential_error(monkeypatch):
    """Un 401 de CMR debe convertirse en una excepción tipada y accionable."""
    def boom(*a, **k):
        raise _earthaccess_style_error(*TOKEN_EXPIRED)

    monkeypatch.setattr(fetch.earthaccess, "search_data", boom)
    with pytest.raises(fetch.EarthdataCredentialError) as ei:
        fetch.search_granules(PKEY, -23.37, -67.73, 25.0, datetime(2026, 7, 25))
    msg = str(ei.value)
    assert "EARTHDATA_CREDENTIAL_INVALID" in msg, (
        "el mensaje debe llevar la etiqueta grepeable por el workflow")
    assert "rotar" in msg.lower(), "debe decir QUÉ hacer, no solo que falló"


def test_fetch_for_volcano_aborts_on_dead_credential(monkeypatch, tmp_path):
    """EL test del incidente: el catch-all no debe tragarse la credencial muerta.

    Antes del fix esto devolvía {"MODIS_TERRA": [], "MODIS_AQUA": []} y exit 0
    — que es exactamente cómo el cron estuvo 13 días 'verde' sin datos.
    """
    def boom(*a, **k):
        raise _earthaccess_style_error(*TOKEN_EXPIRED)

    monkeypatch.setattr(fetch, "auth", lambda *a, **k: None)
    monkeypatch.setattr(fetch.earthaccess, "search_data", boom)
    with pytest.raises(fetch.EarthdataCredentialError):
        fetch.fetch_for_volcano(VOLCANO, datetime(2026, 7, 25), Path(tmp_path))


def test_401_does_not_trip_network_breakers(monkeypatch):
    """Ortogonalidad: la credencial no es un problema de red.

    Marcar el host como caído por un 401 sería un diagnóstico falso y además
    silenciaría los sensores restantes de la corrida.
    """
    def boom(*a, **k):
        raise _earthaccess_style_error(*TOKEN_EXPIRED)

    monkeypatch.setattr(fetch.earthaccess, "search_data", boom)
    with pytest.raises(fetch.EarthdataCredentialError):
        fetch.search_granules(PKEY, -23.37, -67.73, 25.0, datetime(2026, 7, 25))
    assert fetch._CMR_SEARCH_DOWN is False, "un 401 no debe tripear el breaker CMR"
    assert fetch._DOWN_DOWNLOAD_HOSTS == set(), "un 401 no debe marcar hosts caídos"


def test_read_timeout_still_degrades(monkeypatch):
    """Anti-regresión A64/S116: lo transitorio sigue degradando, no abortando."""
    def boom(*a, **k):
        raise ReadTimeout("Read timed out")

    monkeypatch.setattr(fetch.earthaccess, "search_data", boom)
    out = fetch.search_granules(PKEY, -23.37, -67.73, 25.0, datetime(2026, 7, 25))
    assert out == [], "ReadTimeout debe seguir degradando a []"
    assert fetch._CMR_SEARCH_DOWN is True, "y debe tripear el breaker CMR"


def test_permission_denied_does_not_abort(monkeypatch):
    """Un 403 por colección/EULA es por-producto, no por-credencial.

    Abortar el run entero por un sensor sin permiso mataría el NRT completo,
    y el 403 también aparece en throttling de NASA (precedente del proyecto).
    Solo abortamos si el cuerpo dice que el problema es la credencial.
    """
    def boom(*a, **k):
        raise _earthaccess_style_error(*EULA_DENIED)

    monkeypatch.setattr(fetch.earthaccess, "search_data", boom)
    with pytest.raises(RuntimeError) as ei:
        fetch.search_granules(PKEY, -23.37, -67.73, 25.0, datetime(2026, 7, 25))
    assert not isinstance(ei.value, fetch.EarthdataCredentialError), (
        "un 403 de permisos NO debe clasificarse como credencial muerta")


# --- S124: el camino de DESCARGA, que es el que realmente usa el token ---
#
# El guard de S123 quedó solo en `search_granules`. Pero la búsqueda CMR es
# PÚBLICA: el token de NASA se usa en la descarga. O sea, el fix cubría el
# camino que no necesita credencial, y una credencial muerta seguía degradando
# en silencio por el otro — el mismo modo de falla del 20-jul, a medias.


def test_download_aborta_con_credencial_muerta(monkeypatch, tmp_path):
    """Una credencial rechazada en la descarga debe abortar, no reintentar 4×."""
    def boom(*a, **k):
        raise _earthaccess_style_error(*TOKEN_EXPIRED)

    monkeypatch.setattr(fetch.earthaccess, "download", boom)
    monkeypatch.setattr(fetch, "_granule_hosts", lambda g: set())
    with pytest.raises(fetch.EarthdataCredentialError) as ei:
        fetch.download_granules([{"fake": "granule"}], Path(tmp_path))
    assert "EARTHDATA_CREDENTIAL_INVALID" in str(ei.value)


def test_download_sigue_reintentando_errores_transitorios(monkeypatch, tmp_path):
    """Anti-regresión: un fallo de red NO debe abortar; conserva sus retries."""
    intentos = {"n": 0}

    def boom(*a, **k):
        intentos["n"] += 1
        raise ReadTimeout("read timed out")

    monkeypatch.setattr(fetch.earthaccess, "download", boom)
    monkeypatch.setattr(fetch, "_granule_hosts", lambda g: set())
    import time as _time
    monkeypatch.setattr(_time, "sleep", lambda *_: None)
    with pytest.raises(Exception) as ei:
        fetch.download_granules([{"fake": "granule"}], Path(tmp_path))
    assert not isinstance(ei.value, fetch.EarthdataCredentialError)
    assert intentos["n"] > 1, "un error transitorio debe reintentarse, no abortar"
