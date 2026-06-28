"""S116 — circuit-breaker de BÚSQUEDA CMR (espejo de A64 para el host de search).

El breaker S102/S109 cubre el host de DESCARGA (ConnectTimeout). La búsqueda de
metadata (earthaccess.search_data → cmr.earthdata.nasa.gov) puede dar ReadTimeout:
el host acepta la conexión pero responde lento. Incidente Copahue (run 28244166333,
26-jun): ReadTimeout 60s repetido en los 8 sensores → >50min → timeout del job.
A diferencia de la descarga, ReadTimeout NO se cura con probe TCP (el connect SÍ
completa). Fix: al 1er Timeout/ConnectionError de CMR marcar la búsqueda degradada
PARA LA CORRIDA → búsquedas siguientes devuelven [] al instante (degradación: sin
granules ese día; nrt-retry ~30min después reintenta con el breaker reseteado).

Estos tests fijan el comportamiento (anti-regresión):
  - ReadTimeout en search_data → search_granules devuelve [] (NO hang/raise) y tripea.
  - tras tripear → 2ª búsqueda (otro sensor) devuelve [] SIN llamar search_data.
  - ConnectionError también tripea.
  - kill-switch OFF (VRP_CMR_BREAKER=0) → la excepción propaga (comportamiento previo).
  - camino de éxito intacto (search_data devuelve results → se retornan).
"""
import pytest
from requests.exceptions import ReadTimeout, ConnectionError as ReqConnectionError

import pipeline.fetch as fetch

PKEY = "MODIS_TERRA_L1B"  # clave real de PRODUCTS (standard + nrt)


@pytest.fixture(autouse=True)
def _reset_cmr_breaker(monkeypatch):
    """Resetea el breaker CMR entre tests y lo deja ON por defecto."""
    fetch._CMR_SEARCH_DOWN = False
    monkeypatch.setattr(fetch, "ENABLE_CMR_SEARCH_BREAKER", True)
    yield
    fetch._CMR_SEARCH_DOWN = False


def test_read_timeout_returns_empty_and_trips(monkeypatch):
    calls = {"n": 0}

    def boom(*a, **k):
        calls["n"] += 1
        raise ReadTimeout("HTTPSConnectionPool(host='cmr.earthdata.nasa.gov'): Read timed out")

    monkeypatch.setattr(fetch.earthaccess, "search_data", boom)
    out = fetch.search_granules(PKEY, -23.0, -67.7, 25.0, fetch.datetime(2026, 6, 26))
    assert out == [], "ReadTimeout de CMR debe degradar a [] (no hang ni raise)"
    assert fetch._CMR_SEARCH_DOWN is True, "el breaker CMR debe quedar tripeado para la corrida"
    assert calls["n"] == 1, f"debe fallar al 1er Timeout (no reintentar versiones), hubo {calls['n']}"


def test_breaker_skips_subsequent_search_without_calling_cmr(monkeypatch):
    calls = {"n": 0}

    def boom(*a, **k):
        calls["n"] += 1
        raise ReadTimeout("Read timed out")

    monkeypatch.setattr(fetch.earthaccess, "search_data", boom)
    # 1ª: tripea
    assert fetch.search_granules(PKEY, -23.0, -67.7, 25.0, fetch.datetime(2026, 6, 26)) == []
    assert calls["n"] == 1
    # 2ª (otro sensor/llamada): debe saltarse SIN llamar search_data de nuevo
    assert fetch.search_granules("VIIRS_SNPP_L1B", -23.0, -67.7, 25.0, fetch.datetime(2026, 6, 26)) == []
    assert calls["n"] == 1, "tras tripear, la 2ª búsqueda NO debe llamar earthaccess.search_data"


def test_connection_error_also_trips(monkeypatch):
    def boom(*a, **k):
        raise ReqConnectionError("conn reset")

    monkeypatch.setattr(fetch.earthaccess, "search_data", boom)
    assert fetch.search_granules(PKEY, -23.0, -67.7, 25.0, fetch.datetime(2026, 6, 26)) == []
    assert fetch._CMR_SEARCH_DOWN is True


def test_kill_switch_off_propagates_exception(monkeypatch):
    monkeypatch.setattr(fetch, "ENABLE_CMR_SEARCH_BREAKER", False)

    def boom(*a, **k):
        raise ReadTimeout("Read timed out")

    monkeypatch.setattr(fetch.earthaccess, "search_data", boom)
    with pytest.raises(ReadTimeout):
        fetch.search_granules(PKEY, -23.0, -67.7, 25.0, fetch.datetime(2026, 6, 26))
    assert fetch._CMR_SEARCH_DOWN is False, "con el breaker OFF no debe tripear"


def test_success_path_unchanged(monkeypatch):
    sentinel = [{"umm": {"GranuleUR": "G1"}}]

    def ok(*a, **k):
        return sentinel

    monkeypatch.setattr(fetch.earthaccess, "search_data", ok)
    out = fetch.search_granules(PKEY, -23.0, -67.7, 25.0, fetch.datetime(2026, 6, 26))
    assert out == sentinel, "camino de éxito intacto"
    assert fetch._CMR_SEARCH_DOWN is False
