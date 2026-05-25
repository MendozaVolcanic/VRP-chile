"""F55/S77 TDD — earthaccess Store.__init__ /profile bypass cuando hay token.

Investigación S77 (worktree VRP-Chile-s77-f55-nrt-deep) descubrió que la
hipótesis del fix F51 (S77 anterior) era parcialmente equivocada. El
docstring afirmaba que `earthaccess.login(strategy="environment")` con
`EARTHDATA_TOKEN` seteado NUNCA toca `urs.earthdata.nasa.gov`. Eso es
falso a partir de la lectura empírica de earthaccess 0.17.0:

  - `Auth._get_credentials` con token NO llama a `_find_or_create_token`.
  - PERO `earthaccess.api.login()` SIEMPRE crea un `Store(auth)` después.
  - `Store.__init__` llama `set_requests_session(f"https://{edl_hostname}/profile")`
    para sembrar cookies URS. Eso pega un GET a `/profile` aunque haya
    token.

Resultado en GH Actions Azure: el GET a `urs.earthdata.nasa.gov/profile`
timea-out (red bloqueada upstream) → `ConnectTimeoutError` → NRT cron
caído al 100%.

Evidencia empírica (S77 reproducción local, EARTHDATA_TOKEN fake):
  earthaccess version: 0.17.0
  [HTTP] GET https://urs.earthdata.nasa.gov/profile   ← bug F55
  [HTTP] GET https://urs.earthdata.nasa.gov/home
  ...

Fix F55: monkey-patch `earthaccess.store.Store.set_requests_session` ANTES
de llamar `earthaccess.login()`. Si el URL contiene `/profile` y hay
token (`EARTHDATA_TOKEN` env), el patch no-op (silencioso). Las cookies
URS NO son necesarias para granule downloads: las sessions ya llevan
`Authorization: Bearer <token>` (ver `auth.py:230`).

Tests cubren:
- Patch instalado idempotentemente (instalar 2 veces = 1 patch efectivo).
- Llamadas con `/profile` Y token → no-op (no HTTP request).
- Llamadas con `/profile` Y SIN token → comportamiento original (HTTP request).
- Llamadas SIN `/profile` (otros DAACs) → siempre passthrough.
- Reproducción end-to-end: con token + URL `/profile` mockeada para timeout,
  `auth()` completa OK (no leak de TimeoutError).
"""
from __future__ import annotations

import os
import socket
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _reset_env_token(monkeypatch):
    monkeypatch.delenv("EARTHDATA_TOKEN", raising=False)
    monkeypatch.delenv("EARTHDATA_USERNAME", raising=False)
    monkeypatch.delenv("EARTHDATA_PASSWORD", raising=False)


def _reset_patch_state():
    """Reset el flag de instalación del patch entre tests (idempotencia
    en la implementación lo expone como módulo-attr)."""
    from pipeline import fetch
    if hasattr(fetch, "_profile_bypass_installed"):
        fetch._profile_bypass_installed = False
    # restaurar set_requests_session original si fue patched
    import earthaccess.store as eastore
    if hasattr(eastore.Store, "_original_set_requests_session"):
        eastore.Store.set_requests_session = (
            eastore.Store._original_set_requests_session
        )
        delattr(eastore.Store, "_original_set_requests_session")


@pytest.fixture(autouse=True)
def _reset_patch(request):
    _reset_patch_state()
    yield
    _reset_patch_state()


def test_install_profile_bypass_is_idempotent():
    """Instalar el patch dos veces NO debe wrappear doble (cf. recursion)."""
    from pipeline import fetch
    import earthaccess.store as eastore
    fetch._install_profile_bypass()
    first_func = eastore.Store.set_requests_session
    fetch._install_profile_bypass()
    second_func = eastore.Store.set_requests_session
    assert first_func is second_func, "Patch no idempotente — wrap doble"


def test_profile_url_with_token_is_noop():
    """Con EARTHDATA_TOKEN seteado, set_requests_session(/profile) NO debe
    pegar HTTP request — el patch retorna sin tocar la red."""
    import earthaccess.store as eastore
    from pipeline import fetch

    os.environ["EARTHDATA_TOKEN"] = "fake-token-123"
    fetch._install_profile_bypass()

    fake_store = MagicMock(spec=eastore.Store)
    fake_store._http_session = MagicMock()
    fake_store._requests_cookies = {}
    # Llamar el método patcheado
    eastore.Store.set_requests_session(
        fake_store, "https://urs.earthdata.nasa.gov/profile"
    )
    # El http_session NO debe haber sido invocado para /profile
    fake_store._http_session.request.assert_not_called()


def test_profile_url_without_token_calls_original():
    """Sin token, comportamiento original: hace HTTP request a /profile."""
    import earthaccess.store as eastore
    from pipeline import fetch

    fetch._install_profile_bypass()  # patched, pero sin token debe passthrough

    fake_store = MagicMock(spec=eastore.Store)
    fake_resp = MagicMock(status_code=200)
    fake_store._http_session = MagicMock()
    fake_store._http_session.request.return_value = fake_resp
    fake_store._http_session.cookies.get_dict.return_value = {}
    fake_store._requests_cookies = {}

    eastore.Store.set_requests_session(
        fake_store, "https://urs.earthdata.nasa.gov/profile"
    )
    fake_store._http_session.request.assert_called_once()


def test_non_profile_url_always_calls_original():
    """URLs distintas a /profile siempre passthrough (token o no)."""
    import earthaccess.store as eastore
    from pipeline import fetch

    os.environ["EARTHDATA_TOKEN"] = "fake-token-123"
    fetch._install_profile_bypass()

    fake_store = MagicMock(spec=eastore.Store)
    fake_resp = MagicMock(status_code=200)
    fake_store._http_session = MagicMock()
    fake_store._http_session.request.return_value = fake_resp
    fake_store._http_session.cookies.get_dict.return_value = {}
    fake_store._requests_cookies = {}

    eastore.Store.set_requests_session(
        fake_store, "https://e4ftl01.cr.usgs.gov/MOLT/MOD021KM.061/"
    )
    fake_store._http_session.request.assert_called_once()


def test_auth_completes_when_profile_would_timeout():
    """End-to-end F55: simular que /profile timea (red bloqueada Azure).

    Con el fix instalado, `auth()` debe completar sin levantar TimeoutError
    — el patch interceptó el GET a /profile antes que pegara la red.
    Pre-fix: TimeoutError leak desde Store.__init__.
    """
    import earthaccess.store as eastore
    from pipeline import fetch

    os.environ["EARTHDATA_TOKEN"] = "fake-token-for-test"

    # Patchear el http session del Store para que cualquier GET a /profile
    # eleve TimeoutError (simula el fallo Azure).
    original_set_session = eastore.Store.set_requests_session

    def mocked_login(strategy=None):
        # Reproducir el flujo real: login() crea un Store y ese Store
        # llama set_requests_session(/profile).
        import earthaccess
        auth = MagicMock()
        auth.authenticated = True
        auth.system.edl_hostname = "urs.earthdata.nasa.gov"
        auth.get_session.return_value = MagicMock()
        # Simular Store.__init__ comportamiento: llama set_requests_session
        # con la URL /profile. Si el patch F55 NO está, esto haría HTTP real
        # y timeoutearía. Como instalamos el patch antes de login, debe noop.
        fake_store_self = MagicMock()
        fake_store_self._http_session = MagicMock()
        fake_store_self._http_session.request.side_effect = (
            socket.timeout("Connection to urs.earthdata.nasa.gov timed out")
        )
        fake_store_self._requests_cookies = {}
        # Esta llamada con el patch debe NO-OP (token seteado).
        eastore.Store.set_requests_session(
            fake_store_self, "https://urs.earthdata.nasa.gov/profile"
        )
        return auth

    with patch("pipeline.fetch.earthaccess.login", side_effect=mocked_login), \
         patch("pipeline.fetch._probe_nasa_auth", return_value=True), \
         patch("time.sleep"):
        # Si el fix funciona, auth() retorna sin excepción.
        fetch.auth()
