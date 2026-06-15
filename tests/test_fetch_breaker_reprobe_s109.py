"""S109 — resiliencia del circuit-breaker de descarga a timeouts TRANSITORIOS.

S102 hizo el breaker all-or-nothing: al 1er ConnectTimeout marca el host caído PARA
TODA LA CORRIDA → un blip de 60s en la 1ª descarga pierde TODA la data de ese volcán
esa corrida (incidente S109: Láscar/Isluga/Villarrica ~1 día atrás por LANCE intermitente
`nrt3.modaps`, mientras 8 vols sí bajaron — depende de qué job pega la ventana mala).

Fix S109: antes de tripear, probe TCP rápido (5s) al host. Si responde (blip ya
recuperado) → reintentar; si no responde (caído de verdad) → marcar + fallar rápido
(comportamiento S102 intacto). Bounded por el loop de 4 intentos (NO reintroduce el
cuelgue de 50min). Kill-switch `ENABLE_DOWNLOAD_HOST_REPROBE` (env VRP_HOST_REPROBE=0).

Iron Law TDD: escritos ANTES de implementar `_probe_download_host` + la lógica reprobe.
"""
import pytest
from requests.exceptions import ConnectTimeout

import pipeline.fetch as fetch


class FakeGranule(dict):
    def __init__(self, host="lance.example.gov", ur="LANCE:123"):
        super().__init__(umm={"GranuleUR": ur})
        self._host = host

    def data_links(self):
        return [f"https://{self._host}/path/{self['umm']['GranuleUR']}.nc"]


@pytest.fixture(autouse=True)
def _reset(monkeypatch):
    fetch._DOWN_DOWNLOAD_HOSTS.clear()
    monkeypatch.setattr("time.sleep", lambda *a, **k: None)
    monkeypatch.setattr(fetch, "ENABLE_DOWNLOAD_HOST_REPROBE", True)
    yield
    fetch._DOWN_DOWNLOAD_HOSTS.clear()


def test_transient_blip_recovers_via_reprobe(monkeypatch, tmp_path):
    """1er ConnectTimeout pero el host responde al probe (blip) → reintenta y baja."""
    calls = {"n": 0}

    def flaky(granules, local_path):
        calls["n"] += 1
        if calls["n"] == 1:
            raise ConnectTimeout("transient blip")
        import pathlib
        p = pathlib.Path(local_path) / "f.nc"
        p.write_text("x")
        return [str(p)]

    monkeypatch.setattr(fetch.earthaccess, "download", flaky)
    monkeypatch.setattr(fetch, "_probe_download_host", lambda *a, **k: True)  # host recuperado
    out = fetch.download_granules([FakeGranule()], tmp_path)
    assert out, "tras reprobe-OK debe reintentar y bajar"
    assert calls["n"] == 2, f"1 fallo + 1 retry exitoso, hubo {calls['n']}"
    assert "lance.example.gov" not in fetch._DOWN_DOWNLOAD_HOSTS, \
        "host recuperado NO debe quedar marcado caído"


def test_down_host_still_trips_when_probe_fails(monkeypatch, tmp_path):
    """ConnectTimeout + probe falla (caído de verdad) → marca + falla rápido (S102)."""
    calls = {"n": 0}

    def boom(*a, **k):
        calls["n"] += 1
        raise ConnectTimeout("host down")

    monkeypatch.setattr(fetch.earthaccess, "download", boom)
    monkeypatch.setattr(fetch, "_probe_download_host", lambda *a, **k: False)  # caído
    with pytest.raises(ConnectTimeout):
        fetch.download_granules([FakeGranule()], tmp_path)
    assert calls["n"] == 1, "host caído confirmado → 1 sola llamada (S102 intacto)"
    assert "lance.example.gov" in fetch._DOWN_DOWNLOAD_HOSTS


def test_flag_off_keeps_s102_behavior(monkeypatch, tmp_path):
    """Kill-switch: con reprobe OFF, ConnectTimeout tripea al 1er intento sin probar."""
    calls = {"n": 0}
    probed = {"n": 0}

    def boom(*a, **k):
        calls["n"] += 1
        raise ConnectTimeout("blip")

    def probe(*a, **k):
        probed["n"] += 1
        return True

    monkeypatch.setattr(fetch.earthaccess, "download", boom)
    monkeypatch.setattr(fetch, "_probe_download_host", probe)
    monkeypatch.setattr(fetch, "ENABLE_DOWNLOAD_HOST_REPROBE", False)
    with pytest.raises(ConnectTimeout):
        fetch.download_granules([FakeGranule()], tmp_path)
    assert calls["n"] == 1 and probed["n"] == 0, "flag OFF: no prueba, tripea al 1er intento"


def test_reprobe_bounded_no_hang(monkeypatch, tmp_path):
    """Si el download SIEMPRE da ConnectTimeout pero el probe SIEMPRE dice OK, el loop
    de 4 intentos ACOTA (no loop infinito) y termina marcando el host = sin cuelgue."""
    calls = {"n": 0}

    def boom(*a, **k):
        calls["n"] += 1
        raise ConnectTimeout("flapping")

    monkeypatch.setattr(fetch.earthaccess, "download", boom)
    monkeypatch.setattr(fetch, "_probe_download_host", lambda *a, **k: True)
    with pytest.raises(ConnectTimeout):
        fetch.download_granules([FakeGranule()], tmp_path)
    assert calls["n"] <= 4, f"acotado al loop de 4 intentos, hubo {calls['n']}"
    assert "lance.example.gov" in fetch._DOWN_DOWNLOAD_HOSTS, \
        "tras agotar reintentos, marca el host caído (no loop infinito)"
