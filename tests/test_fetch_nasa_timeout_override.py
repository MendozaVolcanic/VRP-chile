"""TDD S47 H7b — override de connect/read timeout para hosts NASA Earthdata.

Contexto: 9 runs NRT consecutivos fallidos 2026-05-16 con ConnectTimeout en
urs.earthdata.nasa.gov:443. El timeout viene hardcoded en
earthaccess.auth._find_or_create_token (timeout=10s en session.post). Cuando
NASA está saturada (no caída), 10s no alcanza para handshake TLS y el retry
de nuestro auth() dispara inmediato.

Fix S47: monkeypatch requests.Session.request para forzar timeout mínimo 60s
en hosts NASA Earthdata. Aplicado en pipeline/fetch.py al import.
"""

import requests

import pipeline.fetch  # noqa: F401  — el import aplica el monkeypatch


def _captured_timeout(url, supplied_timeout=None):
    """Llama a Session.request(GET, url) interceptando antes del network IO
    para capturar qué timeout se está pasando.
    """
    captured = {}

    class _StopHere(Exception):
        pass

    orig_send = requests.Session.send

    def _intercept_send(self, request, **kwargs):
        captured["timeout"] = kwargs.get("timeout")
        raise _StopHere()

    requests.Session.send = _intercept_send
    try:
        s = requests.Session()
        try:
            if supplied_timeout is None:
                s.request("GET", url)
            else:
                s.request("GET", url, timeout=supplied_timeout)
        except _StopHere:
            pass
        return captured["timeout"]
    finally:
        requests.Session.send = orig_send


def test_nasa_host_no_timeout_supplied_forces_60s():
    """Si el caller no pasa timeout, se inyecta 60s."""
    t = _captured_timeout("https://urs.earthdata.nasa.gov/api/users/find_or_create_token")
    assert t == 60.0


def test_nasa_host_low_timeout_raised_to_60s():
    """earthaccess pasa timeout=10s hardcoded — debe ser elevado a 60s."""
    t = _captured_timeout(
        "https://urs.earthdata.nasa.gov/api/users/find_or_create_token",
        supplied_timeout=10,
    )
    assert t == 60.0


def test_nasa_host_high_timeout_preserved():
    """Si el caller ya pidió un timeout mayor, no lo bajamos."""
    t = _captured_timeout(
        "https://cmr.earthdata.nasa.gov/search/granules.json",
        supplied_timeout=120,
    )
    assert t == 120


def test_nasa_host_tuple_timeout_normalized():
    """Si pasan (connect, read), el read se eleva a >=60 y connect a >=30."""
    t = _captured_timeout(
        "https://urs.earthdata.nasa.gov/api/users/find_or_create_token",
        supplied_timeout=(5, 10),
    )
    assert t == (30.0, 60.0)


def test_non_nasa_host_timeout_not_touched():
    """Hosts no-NASA respetan el timeout que pase el caller (10s aquí)."""
    t = _captured_timeout(
        "https://example.com/whatever",
        supplied_timeout=10,
    )
    assert t == 10


def test_non_nasa_host_no_timeout_left_as_none():
    """Sin host NASA, no inyectamos timeout (preserva default del caller)."""
    t = _captured_timeout("https://example.com/whatever")
    assert t is None
