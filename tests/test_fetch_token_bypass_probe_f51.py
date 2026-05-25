"""F51/S77 TDD — token bypass debe saltar el probe-gate (NRT cron unstuck).

Bug F51 (PR #189 audit): el fix S72 `EARTHDATA_TOKEN` bypass está aplicado
y funciona, pero el probe-gate S70-0 corre ANTES del bypass y aborta con
`RuntimeError("NASA_AUTH_UNREACHABLE")` cuando el probe TCP a
`urs.earthdata.nasa.gov:443` timea-out desde runners Azure de GH Actions.

Resultado: NRT cron 100% caído desde 2026-05-23 (40h+ sin data nueva en
operacional) aunque el bypass por token está correctamente seteado en el
workflow y aceptado por earthaccess >= 0.17.0.

Fix esperado: si `EARTHDATA_TOKEN` está seteado, `auth()` debe:
1. Skip el probe (no aporta info — el bypass evita el host problemático).
2. Hacer `earthaccess.login(strategy="environment")` directo.
3. Si login falla por OTRA razón (credencial inválida), reraise el error
   original — NUNCA levantar `NASA_AUTH_UNREACHABLE` cuando hay token.

Tests cubren:
- Comportamiento WITH token: probe NO se llama, login se intenta directo.
- Comportamiento sin token: comportamiento legacy (probe corre, raise
  NASA_AUTH_UNREACHABLE si probe falla).
- Edge: token vacío string ("") = treated as no token (defensive).

Refs:
- docs/F51_NRT_DOWN_INVESTIGATION_S77.md
- pipeline/fetch.py:auth (líneas 195-275)
- commit 137371b1 (token bypass S72)
- commit c777db79 (probe-gate S70-0)
- tag defensivo: pre-s77-f51-fetch-probe-bypass
"""
from __future__ import annotations

import os
import sys
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def _reset_env_token(monkeypatch):
    """Limpiar EARTHDATA_TOKEN antes de cada test — los tests setean
    explícitamente lo que necesitan."""
    monkeypatch.delenv("EARTHDATA_TOKEN", raising=False)


def test_token_set_skips_probe_and_calls_login():
    """F51 fix esperado: con token seteado, probe NO se llama, login directo.

    Pre-fix (estado actual): probe corre incondicional → si timea-out →
    raise NASA_AUTH_UNREACHABLE aunque token bypass habría funcionado.

    Post-fix: bypass total del probe cuando token está. Login directo.
    """
    with patch.dict(os.environ, {"EARTHDATA_TOKEN": "fake-test-token-12345"}):
        with patch("pipeline.fetch._probe_nasa_auth") as mock_probe, \
             patch("pipeline.fetch.earthaccess.login") as mock_login:
            mock_login.return_value = None  # success
            from pipeline import fetch
            fetch.auth()
            mock_probe.assert_not_called()
            mock_login.assert_called_with(strategy="environment")


def test_token_set_login_fail_reraises_not_nasa_unreachable():
    """Con token seteado y login fallando por OTRA razón, NUNCA debe
    levantar NASA_AUTH_UNREACHABLE — eso solo aplica cuando NO hay token
    y el probe falla. Debe reraise el error original (credencial inválida,
    auth401, etc.) para diagnóstico correcto."""
    with patch.dict(os.environ, {"EARTHDATA_TOKEN": "fake-test-token-12345"}):
        with patch("pipeline.fetch._probe_nasa_auth") as mock_probe, \
             patch("pipeline.fetch.earthaccess.login") as mock_login, \
             patch("time.sleep"):  # acelerar test
            mock_login.side_effect = RuntimeError("401 unauthorized fake")
            from pipeline import fetch
            with pytest.raises(RuntimeError) as exc_info:
                fetch.auth()
            mock_probe.assert_not_called()
            assert "NASA_AUTH_UNREACHABLE" not in str(exc_info.value), (
                "Con token seteado, NUNCA levantar NASA_AUTH_UNREACHABLE — "
                "el token bypass evita el host del probe. Debe reraise error "
                "original (auth/401/etc) para diagnóstico correcto. "
                f"got: {exc_info.value}"
            )


def test_no_token_legacy_probe_behavior():
    """Sin token: comportamiento legacy — probe corre, si falla y los
    retries fallan, raise NASA_AUTH_UNREACHABLE (comportamiento S70-0)."""
    # Sin EARTHDATA_TOKEN (autouse fixture lo borró)
    with patch("pipeline.fetch._probe_nasa_auth", return_value=False) as mock_probe, \
         patch("pipeline.fetch.earthaccess.login") as mock_login, \
         patch("time.sleep"), \
         patch("os.path.exists", return_value=False):  # no netrc
        mock_login.side_effect = RuntimeError("connection failed")
        from pipeline import fetch
        with pytest.raises(RuntimeError) as exc_info:
            fetch.auth()
        mock_probe.assert_called_once()
        assert "NASA_AUTH_UNREACHABLE" in str(exc_info.value), (
            "Sin token, comportamiento legacy: probe falla → raise "
            "NASA_AUTH_UNREACHABLE. got: {exc_info.value}"
        )


def test_token_empty_string_treated_as_no_token():
    """Edge: EARTHDATA_TOKEN='' (string vacío) debe tratarse como sin token.

    Caso defensivo: si el workflow yaml setea la env var con valor vacío
    por error de templating, no queremos romper el bypass legacy ni
    asumir token válido.
    """
    with patch.dict(os.environ, {"EARTHDATA_TOKEN": "   "}):  # whitespace only
        with patch("pipeline.fetch._probe_nasa_auth", return_value=False) as mock_probe, \
             patch("pipeline.fetch.earthaccess.login") as mock_login, \
             patch("time.sleep"), \
             patch("os.path.exists", return_value=False):
            mock_login.side_effect = RuntimeError("connection failed")
            from pipeline import fetch
            with pytest.raises(RuntimeError) as exc_info:
                fetch.auth()
            mock_probe.assert_called_once()  # probe SÍ corre (token "vacío" = no token)
            assert "NASA_AUTH_UNREACHABLE" in str(exc_info.value), (
                "Token whitespace-only debe tratarse como no-token → probe corre "
                "y al fallar dispara NASA_AUTH_UNREACHABLE (legacy)."
            )
