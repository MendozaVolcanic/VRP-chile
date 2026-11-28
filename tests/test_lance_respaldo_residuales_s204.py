# -*- coding: utf-8 -*-
"""S204: dos residuales de gravedad 2 que el cierre de la ronda 6 de Codex atribuyó al PR 1147 (verificados por un
Claude de contexto limpio, D:\\codex-vrp\\_salida\\ronda6\\cierre_verificacion\\VEREDICTO.md).

POR QUÉ estas pruebas.
- R6C-108: si nrt3 se colgó una vez, el proceso pasa a preguntarle primero a nrt4. Si nrt4 responde VACÍO (por ejemplo
  porque todavía no tiene las pasadas que nrt3 ya sirve), la búsqueda se quedaba con ese vacío y nunca volvía a nrt3:
  0 de 124 pasadas recuperadas contra 120 de 124 antes del PR. Un vacío del espejo de reemplazo no es la última palabra.
- R6C-V201: con CMR sano pero incompleto, si el presupuesto ya se gastó, catalogo_incompleto no podía medir el hueco y
  decía «completo»; el respaldo no se intentaba y nada lo registraba. Ahora dice que no pudo medir (True), el respaldo se
  intenta, choca con el presupuesto y queda escrito (LANCE_RESPALDO_SIN_RESPUESTA en fetch.py). Todo sin red.
"""
import io
import json
from datetime import date

import pytest

from pipeline import lance_respaldo as L

ITEM = {"downloadsLink": "https://nrt3.modaps.eosdis.nasa.gov/api/v2/content/archives/"
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


@pytest.fixture(autouse=True)
def limpio(monkeypatch):
    monkeypatch.setattr(L, "_hoy", lambda: date(2026, 11, 27), raising=False)
    L.reiniciar()
    yield
    L.reiniciar()


def resultado(f):
    try:
        return "ok", f()
    except Exception as e:   # noqa: BLE001
        return "error", e


def test_vacio_del_espejo_de_reemplazo_vuelve_a_preguntar_al_principal(monkeypatch):
    """R6C-108: nrt3 se colgó una vez (el orden pasa a nrt4, nrt3); después nrt3 se recupera y nrt4 sigue vacío."""
    estado = {"nrt3_colgado": True}

    def falso(url, timeout=None):
        host = url.split("/")[2]
        if host.startswith("nrt3"):
            if estado["nrt3_colgado"]:
                estado["nrt3_colgado"] = False
                raise TimeoutError("timed out")
            return _Resp(json.dumps({"content": [ITEM]}).encode())
        return _Resp(json.dumps({"content": []}).encode())   # nrt4 sano pero sin las pasadas

    monkeypatch.setattr(L, "_abrir", falso)
    primera = resultado(lambda: L.consultar("VJ102IMG_NRT", CAJA, "2026-11-27"))
    segunda = resultado(lambda: L.consultar("VJ102IMG_NRT", CAJA, "2026-11-27"))
    assert primera[0] == "ok" and primera[1] == []        # nrt3 colgado, nrt4 vacío: no hay más que preguntar
    assert segunda[0] == "ok" and [i["fileId"] for i in segunda[1]] == [3112662237]


def test_vacio_del_principal_no_pregunta_al_espejo(monkeypatch):
    """Con el orden normal, un vacío de nrt3 es la respuesta (como antes del PR 1147): no se duplica el pedido."""
    llamadas = []

    def falso(url, timeout=None):
        llamadas.append(url.split("/")[2])
        return _Resp(json.dumps({"content": []}).encode())

    monkeypatch.setattr(L, "_abrir", falso)
    assert resultado(lambda: L.consultar("VJ102IMG_NRT", CAJA, "2026-11-27")) == ("ok", [])
    assert llamadas == ["nrt3.modaps.eosdis.nasa.gov"]


def test_sin_presupuesto_el_hueco_no_se_da_por_completo(monkeypatch):
    """R6C-V201: con la bolsa agotada no se mide nada y se responde True, para que el respaldo se intente y su falta de
    presupuesto quede registrada; sin salir a la red."""
    llamadas = []
    monkeypatch.setattr(L, "_abrir", lambda url, timeout=None: llamadas.append(url) or _Resp(b"{}"))
    L._GASTADO["reciente"] = L.PRESUPUESTO_S
    assert L.catalogo_incompleto("VJ102IMG_NRT", "2.1", "2026-11-27", ahora=0) is True
    assert llamadas == []
    assert resultado(lambda: L.consultar("VJ102IMG_NRT", CAJA, "2026-11-27"))[0] == "error"


def test_fetch_deja_escrito_el_presupuesto_agotado(monkeypatch):
    """Verificador de #1151, I-2: la afirmación «queda escrito» se prueba en fetch.search_granules real, no sólo en el
    módulo. Con CMR sano y vacío para hoy y la bolsa agotada: sin red, sin cortacircuito y una línea en el log."""
    from datetime import datetime
    from pipeline import fetch
    hoy = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    monkeypatch.setattr(L, "_hoy", lambda: hoy.date())
    monkeypatch.setattr(fetch, "_buscar_en_cmr", lambda *a, **k: [])
    red, diag = [], []
    monkeypatch.setattr(L, "_abrir", lambda url, timeout=None: red.append(url) or _Resp(b"{}"))
    monkeypatch.setattr(fetch, "_diag", diag.append)
    monkeypatch.delenv("VRP_LANCE_RESPALDO", raising=False)
    fetch.limpiar_fallas()
    fetch.reiniciar_respaldos_lance()
    L._GASTADO["reciente"] = L.PRESUPUESTO_S
    res = resultado(lambda: fetch.search_granules("VIIRS_NOAA20_L1B", -23.37, -67.73, 25, hoy))
    fetch.limpiar_fallas()
    fetch.reiniciar_respaldos_lance()
    assert res == ("ok", [])
    assert red == []
    assert any("LANCE_RESPALDO_SIN_RESPUESTA" in m and "presupuesto" in m for m in diag), diag
    assert L._CAIDO is False


def test_bolsa_de_hoy_agotada_no_apaga_los_dias_viejos(monkeypatch):
    """Verificador de #1151, I-2 (mutación M3): agotar una bolsa no enciende el cortacircuito de todo LANCE."""
    monkeypatch.setattr(L, "_abrir", lambda url, timeout=None: _Resp(json.dumps({"content": [ITEM]}).encode()))
    L._GASTADO["reciente"] = L.PRESUPUESTO_S
    assert resultado(lambda: L.catalogo_incompleto("VJ102IMG_NRT", "2.1", "2026-11-27", ahora=0)) == ("ok", True)
    assert resultado(lambda: L.consultar("VJ102IMG_NRT", CAJA, "2026-11-27"))[0] == "error"
    viejo = resultado(lambda: L.consultar("VJ102IMG_NRT", CAJA, "2026-11-20"))
    assert viejo[0] == "ok" and len(viejo[1]) == 1
    assert L._CAIDO is False


def test_con_presupuesto_y_catalogo_completo_sigue_siendo_falso(monkeypatch):
    """El cambio de R6C-V201 no puede volver True un día sano: CMR 10, carpeta 10."""
    def falso(url, timeout=None):
        if "cmr.earthdata" in url:
            return _Resp(b"{}")
        return _Resp(json.dumps({"content": [{"resourceType": "File", "mtime": 0}] * 10}).encode())

    monkeypatch.setattr(L, "_abrir", falso)
    assert L.catalogo_incompleto("VJ102IMG_NRT", "2.1", "2026-11-27", ahora=10 ** 9) is False
