# -*- coding: utf-8 -*-
"""S204: el respaldo LANCE no puede comerse el tope de 50 minutos del job (ronda 6 de Codex, verificada).

POR QUÉ estas pruebas. El cortacircuito del S203 sólo salta cuando nrt3 y nrt4 fallan juntos. La ronda 6 encontró tres
caminos por los que igual se va el tiempo, y el verificador Claude de contexto limpio los dejó en gravedad 3:
- R6FL-118: LANCE responde, pero lento (29 s por consulta): 96 consultas con CMR caído suman 46 min sólo de LANCE.
- R6FL-V201: nrt3 colgado y nrt4 sano: cada consulta paga 30 s en nrt3 antes de ir a nrt4 (48 min).
- R6FL-108: la descarga desde nrt4 no recibe el tiempo de espera mínimo que fetch.py fuerza para nrt3 (timeout None).
El arreglo: un presupuesto de tiempo de red por proceso para el respaldo (al agotarse, el resto del proceso usa sólo
CMR, como antes de #1143), saltar el host que ya falló, y nrt4 en la lista de hosts de NASA. Todo sin red.
"""
import io
import json
from datetime import date

import pytest

from pipeline import lance_respaldo as L

ITEM = {"downloadsLink": "https://nrt4.modaps.eosdis.nasa.gov/api/v2/content/archives/"
                         "VJ102IMG_NRT.A2026331.0506.021.2026331073257.nc",
        "fileId": 3112662237, "name": "VJ102IMG_NRT.A2026331.0506.021.nc", "products": "VJ102IMG_NRT",
        "resourceType": "File", "start": "2026-11-27 05:06:00", "status": "Online", "size": 1}
CAJA = (-68.0, -24.0, -67.5, -23.0)


class _Resp(io.BytesIO):
    headers = {"CMR-Hits": "10"}

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class _Reloj:
    """Reloj falso: cada llamada a la red avanza `paso` segundos."""
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


@pytest.fixture(autouse=True)
def limpio(monkeypatch):
    """«Hoy» fijo en 2026-11-27: las pruebas no dependen del día en que corren (lección R6FL-116)."""
    monkeypatch.setattr(L, "_hoy", lambda: date(2026, 11, 27), raising=False)
    L.reiniciar()
    yield
    L.reiniciar()


def red_lenta(reloj, paso, nrt3_colgado=False, llamadas=None, nrt3_error_rapido=0):
    """nrt3_colgado: nrt3 agota su tiempo de espera; nrt3_error_rapido: nrt3 falla al tiro las primeras N veces."""
    cuenta = {"rapido": 0}

    def falso(url, timeout=None):
        host = url.split("/")[2]
        if llamadas is not None:
            llamadas.append(host)
        if nrt3_colgado and host.startswith("nrt3"):
            reloj.t += L.TIMEOUT_S
            raise TimeoutError("timed out")
        if host.startswith("nrt3") and cuenta["rapido"] < nrt3_error_rapido:
            cuenta["rapido"] += 1
            raise OSError("404 pasajero")
        reloj.t += paso
        return _Resp(json.dumps({"content": [ITEM]}).encode())
    return falso


def resultado(f):
    try:
        return "ok", f()
    except Exception as e:   # noqa: BLE001
        return "error", e


def test_respuestas_lentas_agotan_el_presupuesto_y_cortan(monkeypatch):
    """R6FL-118: con respuestas de 29 s, el respaldo deja de consultar antes de pasar su presupuesto."""
    reloj = _Reloj()
    monkeypatch.setattr(L, "_reloj", reloj, raising=False)
    monkeypatch.setattr(L, "_abrir", red_lenta(reloj, 29.0))
    inicio = reloj.t
    estados = [resultado(lambda: L.consultar("VJ102IMG_NRT", CAJA, "2026-11-27"))[0] for _ in range(96)]
    gastado = reloj.t - inicio
    assert gastado <= L.PRESUPUESTO_S + 2 * L.TIMEOUT_S
    assert estados.count("ok") >= 1 and estados[-1] == "error"


def test_la_lectura_lenta_tambien_gasta_presupuesto(monkeypatch):
    """La conexión abre al tiro pero el cuerpo tarda 29 s en llegar: ese tiempo también cuenta."""
    reloj = _Reloj()

    class _Lenta(_Resp):
        def read(self, *a, **k):
            reloj.t += 29.0
            return super().read(*a, **k)

    monkeypatch.setattr(L, "_reloj", reloj, raising=False)
    monkeypatch.setattr(L, "_abrir", lambda url, timeout=None: _Lenta(json.dumps({"content": [ITEM]}).encode()))
    inicio = reloj.t
    for _ in range(96):
        resultado(lambda: L.consultar("VJ102IMG_NRT", CAJA, "2026-11-27"))
    assert reloj.t - inicio <= L.PRESUPUESTO_S + 2 * L.TIMEOUT_S


def test_conteo_de_cmr_y_carpeta_cuentan_en_el_presupuesto(monkeypatch):
    """R6FL-102: el conteo a CMR y el listado de la carpeta gastan del mismo presupuesto."""
    reloj = _Reloj()
    monkeypatch.setattr(L, "_reloj", reloj, raising=False)
    monkeypatch.setattr(L, "_abrir", red_lenta(reloj, 29.0))
    inicio = reloj.t
    for i in range(60):
        L.catalogo_incompleto("VJ102IMG_NRT", "2.1", "2026-11-27", ahora=0)
        L._INCOMPLETO.clear()
    assert reloj.t - inicio <= L.PRESUPUESTO_S + 3 * L.TIMEOUT_S


def test_nrt3_colgado_se_salta_despues_de_la_primera_falla(monkeypatch):
    """R6FL-V201: con nrt3 colgado y nrt4 sano, nrt3 se intenta una sola vez por proceso."""
    reloj = _Reloj()
    llamadas = []
    monkeypatch.setattr(L, "_reloj", reloj, raising=False)
    monkeypatch.setattr(L, "_abrir", red_lenta(reloj, 1.0, nrt3_colgado=True, llamadas=llamadas))
    oks = [resultado(lambda: L.consultar("VJ102IMG_NRT", CAJA, "2026-11-27"))[0] for _ in range(20)]
    assert oks == ["ok"] * 20
    assert llamadas.count("nrt3.modaps.eosdis.nasa.gov") == 1
    assert llamadas.count("nrt4.modaps.eosdis.nasa.gov") == 20


def test_reiniciar_devuelve_el_orden_y_el_presupuesto(monkeypatch):
    reloj = _Reloj()
    llamadas = []
    monkeypatch.setattr(L, "_reloj", reloj, raising=False)
    monkeypatch.setattr(L, "_abrir", red_lenta(reloj, 1.0, nrt3_colgado=True, llamadas=llamadas))
    resultado(lambda: L.consultar("VJ102IMG_NRT", CAJA, "2026-11-27"))
    L.reiniciar()
    llamadas.clear()
    resultado(lambda: L.consultar("VJ102IMG_NRT", CAJA, "2026-11-27"))
    assert llamadas[0] == "nrt3.modaps.eosdis.nasa.gov"


def test_dias_viejos_no_dejan_a_hoy_sin_respaldo(monkeypatch):
    """I-1 del verificador del PR 1147: el NRT busca de lo más viejo a hoy; una caída larga no puede gastar en los días
    viejos el tiempo de hoy."""
    reloj = _Reloj()
    monkeypatch.setattr(L, "_reloj", reloj, raising=False)
    monkeypatch.setattr(L, "_abrir", red_lenta(reloj, 29.0))
    viejos = [resultado(lambda: L.consultar("VJ102IMG_NRT", CAJA, "2026-11-2%d" % (i % 6)))[0] for i in range(96)]
    assert viejos[-1] == "error"   # la bolsa de los días viejos se agotó
    hoy = [resultado(lambda: L.consultar("VJ102IMG_NRT", CAJA, d))[0] for d in ("2026-11-26", "2026-11-27")]
    assert hoy == ["ok", "ok"]


def test_timeout_de_conexion_envuelto_en_urlerror_tambien_salta(monkeypatch):
    """urllib entrega el tiempo de espera de conexión como URLError(reason=TimeoutError): también es «se colgó»
    (verificador del PR 1147, pasada 2)."""
    import urllib.error
    reloj = _Reloj()
    llamadas = []

    def falso(url, timeout=None):
        host = url.split("/")[2]
        llamadas.append(host)
        if host.startswith("nrt3"):
            reloj.t += L.TIMEOUT_S
            raise urllib.error.URLError(TimeoutError("timed out"))
        reloj.t += 1.0
        return _Resp(json.dumps({"content": [ITEM]}).encode())

    monkeypatch.setattr(L, "_reloj", reloj, raising=False)
    monkeypatch.setattr(L, "_abrir", falso)
    for _ in range(5):
        resultado(lambda: L.consultar("VJ102IMG_NRT", CAJA, "2026-11-27"))
    assert llamadas.count("nrt3.modaps.eosdis.nasa.gov") == 1


def test_error_rapido_no_manda_el_host_al_final(monkeypatch):
    """I-2 del verificador del PR 1147: un 404 pasajero de nrt3 no deja al proceso en nrt4 para siempre."""
    reloj = _Reloj()
    llamadas = []
    monkeypatch.setattr(L, "_reloj", reloj, raising=False)
    monkeypatch.setattr(L, "_abrir", red_lenta(reloj, 1.0, llamadas=llamadas, nrt3_error_rapido=1))
    resultado(lambda: L.consultar("VJ102IMG_NRT", CAJA, "2026-11-27"))
    llamadas.clear()
    resultado(lambda: L.consultar("VJ102IMG_NRT", CAJA, "2026-11-27"))
    assert llamadas == ["nrt3.modaps.eosdis.nasa.gov"]


def test_el_tiempo_de_un_error_tambien_gasta(monkeypatch):
    """Los 30 s que se pierden en un nrt3 colgado cuentan en la bolsa, no sólo las respuestas buenas."""
    reloj = _Reloj()
    monkeypatch.setattr(L, "_reloj", reloj, raising=False)
    monkeypatch.setattr(L, "_abrir", red_lenta(reloj, 1.0, nrt3_colgado=True))
    resultado(lambda: L.consultar("VJ102IMG_NRT", CAJA, "2026-11-27"))
    assert L._GASTADO["reciente"] >= L.TIMEOUT_S + 1.0


def test_el_conteo_tambien_salta_el_host_colgado(monkeypatch):
    """Si nrt3 se cuelga en el listado de la carpeta, la consulta siguiente parte por nrt4."""
    reloj = _Reloj()
    llamadas = []
    monkeypatch.setattr(L, "_reloj", reloj, raising=False)
    monkeypatch.setattr(L, "_abrir", red_lenta(reloj, 1.0, nrt3_colgado=True, llamadas=llamadas))
    L.catalogo_incompleto("VJ102IMG_NRT", "2.1", "2026-11-27", ahora=0)
    llamadas.clear()
    resultado(lambda: L.consultar("VJ102IMG_NRT", CAJA, "2026-11-27"))
    assert llamadas == ["nrt4.modaps.eosdis.nasa.gov"]


def test_salud_de_cmr_gasta_y_respeta_la_bolsa(monkeypatch):
    """catalogo_congelado pasa por el presupuesto: con la bolsa agotada no sale a la red y no rompe nada."""
    llamadas = []
    monkeypatch.setattr(L, "_abrir", lambda url, timeout=None: llamadas.append(url) or _Resp(b'{"indexer": {"ok?": false}}'))
    L._GASTADO["reciente"] = L.PRESUPUESTO_S
    assert L.catalogo_congelado() is False and llamadas == []
    L.reiniciar()
    assert L.catalogo_congelado() is True and len(llamadas) == 1


def test_presupuesto_holgado_para_un_dia_normal():
    """Medido en las NRT del 27-nov 17:50 y 28-nov 01:07 (D:\\vrp-trabajo\\temporales\\s204\\salida_medir_tiempo_*.txt):
    un volcán gastó a lo más 29 s por día. Hoy y ayer caben 10 veces; los seis días viejos, una caída entera."""
    assert L.PRESUPUESTO_S >= 10 * 2 * 29
    assert L.PRESUPUESTO_ANTIGUO_S >= 6 * 29


def test_descarga_desde_nrt4_recibe_tiempo_de_espera(monkeypatch):
    """R6FL-108: fetch.py fuerza 60 s mínimos a los hosts de NASA; nrt4 tiene que estar entre ellos."""
    from pipeline import fetch
    import requests
    vistos = {}

    def registrar(self, method, url, **kwargs):
        vistos[url.split("/")[2]] = kwargs.get("timeout")
        return None

    monkeypatch.setattr(fetch, "_orig_session_request", registrar)
    s = requests.Session()
    for host in ("nrt3.modaps.eosdis.nasa.gov", "nrt4.modaps.eosdis.nasa.gov"):
        requests.Session.request(s, "GET", "https://%s/api/v2/content/archives/x.nc" % host)
    assert vistos["nrt4.modaps.eosdis.nasa.gov"] == vistos["nrt3.modaps.eosdis.nasa.gov"] == 60.0
