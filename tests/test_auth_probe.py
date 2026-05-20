"""Tests para probe rápido en pipeline.fetch.auth() (S70-0 T2).

Contexto: 19/20 runs NRT consecutivos fallidos por ConnectTimeout en
urs.earthdata.nasa.gov:443 (mismo patrón S47). Cada job moría a ~31 min
exactos por agotar 8 reintentos × 60s connect-timeout. T2 agrega un probe
TCP rápido (5s) antes del retry loop largo: si el probe falla, acorta
budget a ~2 min y lanza RuntimeError distinguible para que el workflow
pueda etiquetar el run como [NASA_DOWN].
"""

import socket
from unittest import mock

import pytest


def test_probe_fast_returns_true_when_endpoint_reachable(monkeypatch):
    """Probe debe devolver True cuando socket.create_connection no levanta."""
    from pipeline.fetch import _probe_nasa_auth

    mock_conn = mock.MagicMock()
    mock_conn.__enter__ = mock.MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = mock.MagicMock(return_value=False)
    monkeypatch.setattr(
        socket, "create_connection", mock.MagicMock(return_value=mock_conn)
    )
    assert _probe_nasa_auth(timeout=5.0) is True


def test_probe_fast_returns_false_on_timeout(monkeypatch):
    """Probe debe devolver False cuando socket.create_connection levanta socket.timeout."""
    from pipeline.fetch import _probe_nasa_auth

    monkeypatch.setattr(
        socket,
        "create_connection",
        mock.MagicMock(side_effect=socket.timeout("timed out")),
    )
    assert _probe_nasa_auth(timeout=5.0) is False


def test_probe_fast_returns_false_on_connection_refused(monkeypatch):
    """Probe debe devolver False cuando conexión se rechaza."""
    from pipeline.fetch import _probe_nasa_auth

    monkeypatch.setattr(
        socket,
        "create_connection",
        mock.MagicMock(side_effect=ConnectionRefusedError("refused")),
    )
    assert _probe_nasa_auth(timeout=5.0) is False


def test_probe_fast_returns_false_on_os_error(monkeypatch):
    """Probe debe devolver False ante cualquier OSError (DNS, network unreachable, etc.)."""
    from pipeline.fetch import _probe_nasa_auth

    monkeypatch.setattr(
        socket,
        "create_connection",
        mock.MagicMock(side_effect=OSError("Network is unreachable")),
    )
    assert _probe_nasa_auth(timeout=5.0) is False


def test_auth_raises_nasa_unreachable_when_probe_fails(monkeypatch):
    """auth() debe lanzar RuntimeError con 'NASA_AUTH_UNREACHABLE' si probe falla
    y los reintentos cortos tampoco logran login.
    """
    from pipeline import fetch

    monkeypatch.setattr(fetch, "_probe_nasa_auth", lambda timeout=5.0: False)
    # Acortar delays mock para no esperar minutos en test
    monkeypatch.setattr(fetch, "_PROBE_FAIL_DELAYS", [0, 0, 0])  # 3 retries quick

    # Simular que earthaccess.login también falla (NASA caída de verdad)
    monkeypatch.setattr(
        fetch.earthaccess,
        "login",
        mock.MagicMock(side_effect=Exception("connect timeout")),
    )

    with pytest.raises(RuntimeError, match="NASA_AUTH_UNREACHABLE"):
        fetch.auth()


def test_auth_succeeds_normally_when_probe_ok(monkeypatch):
    """Si el probe pasa, auth() debe ejecutar el flujo normal y no lanzar
    NASA_AUTH_UNREACHABLE. Login fake retorna OK al primer intento.
    """
    from pipeline import fetch

    monkeypatch.setattr(fetch, "_probe_nasa_auth", lambda timeout=5.0: True)
    monkeypatch.setattr(fetch.earthaccess, "login", mock.MagicMock(return_value=None))

    # No debe lanzar
    fetch.auth()


def test_auth_does_not_raise_unreachable_if_login_succeeds_after_probe_fail(monkeypatch):
    """Caso borde: probe falla (red intermitente) pero earthaccess.login() funciona
    en un reintento corto. auth() debe retornar normal, no lanzar NASA_AUTH_UNREACHABLE.
    """
    from pipeline import fetch

    monkeypatch.setattr(fetch, "_probe_nasa_auth", lambda timeout=5.0: False)
    monkeypatch.setattr(fetch, "_PROBE_FAIL_DELAYS", [0, 0, 0])
    monkeypatch.setattr(fetch.earthaccess, "login", mock.MagicMock(return_value=None))

    # No debe lanzar — login funcionó aunque el probe haya fallado
    fetch.auth()
