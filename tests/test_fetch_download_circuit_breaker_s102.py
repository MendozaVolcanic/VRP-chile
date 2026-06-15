"""S102 — circuit-breaker de descarga (fix root cause incidente NRT).

Root cause (run instrumentado 27085208578): el host LANCE
`nrt3.modaps.eosdis.nasa.gov` da ConnectTimeout a 183s; reintentar 4× por granule
× varias plataformas VIIRS NRT acumulaba >50min → timeout del job. Fix: para
ConnectTimeout/ConnectionError (host caído) NO reintentar 4×, fallar rápido y marcar
el host caído para la corrida → descargas siguientes de ese host se saltan al instante.

Estos tests fijan el comportamiento (anti-regresión):
  - ConnectTimeout → 1 sola llamada a earthaccess.download (no 4×).
  - host marcado caído → 2ª descarga del mismo host se salta SIN llamar download.
  - error genérico (no-connect) → conserva los 4 reintentos (transient).
  - camino de éxito intacto.
"""
import importlib

import pytest
from requests.exceptions import ConnectTimeout

import pipeline.fetch as fetch


class FakeGranule(dict):
    """Granule mock: dict-like (.get) + .data_links() como earthaccess DataGranule."""
    def __init__(self, host="lance.example.gov", ur="LANCE:123"):
        super().__init__(umm={"GranuleUR": ur})
        self._host = host

    def data_links(self):
        return [f"https://{self._host}/path/{self['umm']['GranuleUR']}.nc"]


@pytest.fixture(autouse=True)
def _reset_breaker_and_sleep(monkeypatch):
    """Resetea el circuit-breaker entre tests + anula sleeps de retry.

    S109: el breaker ahora hace un probe TCP antes de tripear (resiliencia a blips).
    Estos tests S102 fijan el comportamiento de 'host caído de verdad' → forzamos el
    probe a False (host no responde) para que el trip sea determinista y sin red real.
    El camino de recuperación (probe True) se cubre en test_fetch_breaker_reprobe_s109.
    """
    fetch._DOWN_DOWNLOAD_HOSTS.clear()
    monkeypatch.setattr("time.sleep", lambda *a, **k: None)
    monkeypatch.setattr(fetch, "_probe_download_host", lambda *a, **k: False)
    yield
    fetch._DOWN_DOWNLOAD_HOSTS.clear()


def test_connect_timeout_fails_fast_no_4x_retry(monkeypatch, tmp_path):
    calls = {"n": 0}

    def boom(*a, **k):
        calls["n"] += 1
        raise ConnectTimeout("HTTPSConnectionPool(host='lance.example.gov')")

    monkeypatch.setattr(fetch.earthaccess, "download", boom)
    g = FakeGranule()
    with pytest.raises(ConnectTimeout):
        fetch.download_granules([g, g], tmp_path)
    assert calls["n"] == 1, f"ConnectTimeout debe fallar rápido (1 intento), hubo {calls['n']}"
    # el host quedó marcado caído
    assert "lance.example.gov" in fetch._DOWN_DOWNLOAD_HOSTS


def test_circuit_breaker_skips_downed_host(monkeypatch, tmp_path):
    calls = {"n": 0}

    def boom(*a, **k):
        calls["n"] += 1
        raise ConnectTimeout("HTTPSConnectionPool(host='lance.example.gov')")

    monkeypatch.setattr(fetch.earthaccess, "download", boom)
    g = FakeGranule(host="lance.example.gov")
    # 1ª: falla y marca el host
    with pytest.raises(ConnectTimeout):
        fetch.download_granules([g], tmp_path)
    assert calls["n"] == 1
    # 2ª: mismo host → debe saltarse SIN llamar download de nuevo
    with pytest.raises(RuntimeError):
        fetch.download_granules([g], tmp_path)
    assert calls["n"] == 1, "el 2º download del host caído NO debe llamar earthaccess.download"


def test_other_host_not_skipped(monkeypatch, tmp_path):
    """Un host distinto (LAADS) no se ve afectado por LANCE caído."""
    seen = []

    def ok(granules, local_path):
        seen.append(granules[0]._host)
        import pathlib
        p = pathlib.Path(local_path) / "f.nc"
        p.write_text("x")
        return [str(p)]

    fetch._DOWN_DOWNLOAD_HOSTS.add("lance.example.gov")
    monkeypatch.setattr(fetch.earthaccess, "download", ok)
    g = FakeGranule(host="laads.example.gov", ur="LAADS:9")
    out = fetch.download_granules([g], tmp_path)
    assert out and seen == ["laads.example.gov"]


def test_generic_error_keeps_4_retries(monkeypatch, tmp_path):
    calls = {"n": 0}

    def boom(*a, **k):
        calls["n"] += 1
        raise ValueError("transient read glitch")

    monkeypatch.setattr(fetch.earthaccess, "download", boom)
    g = FakeGranule()
    with pytest.raises(ValueError):
        fetch.download_granules([g], tmp_path)
    assert calls["n"] == 4, f"error genérico conserva 4 reintentos, hubo {calls['n']}"


def test_success_path_unchanged(monkeypatch, tmp_path):
    def ok(granules, local_path):
        import pathlib
        paths = []
        for i, _ in enumerate(granules):
            p = pathlib.Path(local_path) / f"f{i}.nc"
            p.write_text("x")
            paths.append(str(p))
        return paths

    monkeypatch.setattr(fetch.earthaccess, "download", ok)
    g = FakeGranule()
    out = fetch.download_granules([g, g], tmp_path)
    assert len(out) == 2 and all(p.exists() for p in out)
