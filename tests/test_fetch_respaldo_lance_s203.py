# -*- coding: utf-8 -*-
"""S203: respaldo de búsqueda por LANCE cuando CMR falla o se congela (plan
docs/superpowers/plans/2026-11-27-respaldo-lance.md).

POR QUÉ estas pruebas. Cuando el indexador de CMR se cae, CMR responde vacío o una lista vieja sin error y el NRT
pierde pasadas que ya están en LANCE (26 y 27-nov). El respaldo tiene que (1) dar gránulos con la misma forma que los
de CMR, porque el resto del flujo (filtro nocturno, pareo L1B y geolocalización, descarga) no cambia; (2) consultar
LANCE sólo cuando hace falta; (3) no duplicar pasadas ni ocultar una falla que no se recuperó. Todo sin red.
"""
import http.client as http_client
import io
import json
from datetime import datetime, timedelta

import pytest

from pipeline import fetch
from pipeline import lance_respaldo as L

# Item real de la API de LANCE (VJ102IMG_NRT, 2026-11-27 05:06, Láscar), recortado a los campos que se usan.
ITEM_VJ1 = {"archiveSets": [5200, 5201], "dataDay": "2026-331 = 2026-11-27",
            "downloadsLink": "https://nrt3.modaps.eosdis.nasa.gov/api/v2/content/archives/"
                             "VJ102IMG_NRT.A2026331.0506.021.2026331073257.nc",
            "fileId": 3112662237, "illuminations": "N", "name": "VJ102IMG_NRT.A2026331.0506.021.nc",
            "products": "VJ102IMG_NRT", "resourceType": "File", "size": 89484292,
            "start": "2026-11-27 05:06:00", "status": "Online",
            "gringLatitude1": -30.88, "gringLatitude2": -26.09, "gringLatitude3": -5.79, "gringLatitude4": -10.0,
            "gringLongitude1": -44.05, "gringLongitude2": -74.95, "gringLongitude3": -68.16, "gringLongitude4": -41.03}
# Enlace GET DATA que CMR da para ese mismo gránulo (GranuleUR LANCEMODIS:3112662237), leído el 2026-11-27.
URL_CMR_VJ1 = ("https://nrt3.modaps.eosdis.nasa.gov/api/v2/content/archives/allData/5201/VJ102IMG_NRT/2026/331/"
               "VJ102IMG_NRT.A2026331.0506.021.2026331073257.nc")
ITEM_MYD = {"archiveSets": 61, "downloadsLink": "https://nrt3.modaps.eosdis.nasa.gov/api/v2/content/archives/"
                                                "MYD021KM.A2026331.0830.061.2026331100717.NRT.hdf",
            "fileId": 3112700001, "illuminations": "N", "name": "MYD021KM.A2026331.0830.061.NRT.hdf",
            "products": "MYD021KM", "resourceType": "File", "size": 100, "start": "2026-11-27 08:30:00",
            "status": "Online"}


def item(producto, hhmm, file_id, ext="nc", dia="2026-11-27"):
    doy = (datetime.strptime(dia, "%Y-%m-%d") - datetime(2026, 1, 1)).days + 1
    archivo = "%s.A2026%03d.%s.021.2026%03d090000.%s" % (producto, doy, hhmm.replace(":", ""), doy, ext)
    return {"downloadsLink": "https://nrt3.modaps.eosdis.nasa.gov/api/v2/content/archives/" + archivo,
            "fileId": file_id, "name": archivo, "products": producto, "resourceType": "File",
            "start": "%s %s:00" % (dia, hhmm), "status": "Online", "size": 1}


def resultado(f):
    """("ok", valor) o ("error", excepción): para que una prueba falle por aserción y no por excepción (el contador de
    mutaciones sólo cuenta aserciones, lección S202)."""
    try:
        return "ok", f()
    except Exception as e:   # noqa: BLE001
        return "error", e


def gran_cmr(short, version, inicio, ur):
    """Gránulo con la forma de los de CMR (lo mínimo que lee el flujo)."""
    from earthaccess.results import DataGranule
    return DataGranule({"meta": {"concept-id": "G-" + ur, "provider-id": "LANCEMODIS"},
                        "umm": {"GranuleUR": ur, "CollectionReference": {"ShortName": short, "Version": version},
                                "TemporalExtent": {"RangeDateTime": {"BeginningDateTime": inicio}},
                                "RelatedUrls": [{"URL": "https://x/" + ur, "Type": "GET DATA"}]}})


# ── Tarea 1: conversión ──────────────────────────────────────────────────────────────────────────────────────────
def test_a_granulo_viirs_igual_al_de_cmr():
    g = L.a_granulo(ITEM_VJ1, "VJ102IMG_NRT", "2.1")
    assert g["umm"]["GranuleUR"] == "LANCEMODIS:3112662237"
    assert g["umm"]["TemporalExtent"]["RangeDateTime"]["BeginningDateTime"] == "2026-11-27T05:06:00.000Z"
    assert g["umm"]["CollectionReference"] == {"ShortName": "VJ102IMG_NRT", "Version": "2.1"}
    assert g.data_links() == [URL_CMR_VJ1]
    assert g["meta"]["vrp-origen"] == "lance"


def test_a_granulo_modis_conjunto_61():
    g = L.a_granulo(ITEM_MYD, "MYD021KM", "6.1NRT")
    assert g.data_links() == ["https://nrt3.modaps.eosdis.nasa.gov/api/v2/content/archives/allData/61/MYD021KM/"
                              "2026/331/MYD021KM.A2026331.0830.061.2026331100717.NRT.hdf"]
    assert g["umm"]["CollectionReference"]["Version"] == "6.1NRT"


def test_a_granulo_del_espejo_apunta_al_espejo():
    """R-1: nrt4 da otro archivo (otra marca de producción) para la misma pasada; su nombre sólo existe en nrt4.
    Enlace leído del listado allData de nrt4 el 2026-11-27."""
    it = dict(ITEM_MYD, downloadsLink="https://nrt4.modaps.eosdis.nasa.gov/api/v2/content/archives/"
                                      "MYD03.A2026331.0830.061.2026331095452.NRT.hdf")
    g = L.a_granulo(it, "MYD03", "6.1NRT")
    assert g.data_links() == ["https://nrt4.modaps.eosdis.nasa.gov/api/v2/content/archives/allData/61/MYD03/2026/331/"
                              "MYD03.A2026331.0830.061.2026331095452.NRT.hdf"]


def test_a_granulo_rechaza_un_host_ajeno():
    with pytest.raises(ValueError):
        L.a_granulo(dict(ITEM_VJ1, downloadsLink="https://otro.example/x/VJ102IMG_NRT.A2026331.0506.021.nc"),
                    "VJ102IMG_NRT", "2.1")


def test_conjunto_por_producto():
    assert L.conjunto("MOD03") == "61" and L.conjunto("MYD021KM") == "61"
    assert L.conjunto("VJ103MOD_NRT") == "5201" and L.conjunto("VJ202IMG_NRT") == "5201"
    assert L.conjunto("VNP02IMG_NRT") == "5200"
    with pytest.raises(KeyError):
        L.conjunto("XYZ")


# ── Tarea 2: consulta ─────────────────────────────────────────────────────────────────────────────────────────────
class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_consultar_arma_bbox_y_filtra(monkeypatch):
    urls = []

    def falso(url, timeout=None):
        urls.append(url)
        otro = dict(ITEM_VJ1, products="VJ103IMG_NRT", fileId=1)
        return _Resp(json.dumps({"content": [ITEM_VJ1, otro, {"resourceType": "Directory", "products": "VJ102IMG_NRT"}]}).encode())

    monkeypatch.setattr(L, "_abrir", falso)
    items = L.consultar("VJ102IMG_NRT", (-68.0, -24.0, -67.5, -23.0), "2026-11-27")
    assert [i["fileId"] for i in items] == [3112662237]
    assert urls[0].startswith("https://nrt3.modaps.eosdis.nasa.gov/api/v2/content/details?")
    assert "products=VJ102IMG_NRT" in urls[0] and "temporalRanges=2026-331" in urls[0]
    assert "%5BBBOX%5DW-68.0%20N-23.0%20E-67.5%20S-24.0" in urls[0]


def test_consultar_cae_al_espejo_y_despues_falla(monkeypatch):
    hosts = []

    def falso(url, timeout=None):
        hosts.append(url.split("/")[2])
        if "nrt3" in url:
            raise OSError("caido")
        return _Resp(json.dumps({"content": [ITEM_VJ1]}).encode())

    monkeypatch.setattr(L, "_abrir", falso)
    try:
        n = len(L.consultar("VJ102IMG_NRT", (-68, -24, -67, -23), "2026-11-27"))
    except L.LanceNoResponde:
        n = None   # sin espejo: la caída de nrt3 dejaría sin respaldo
    assert n == 1
    assert hosts ==["nrt3.modaps.eosdis.nasa.gov", "nrt4.modaps.eosdis.nasa.gov"]

    def todo_caido(url, timeout=None):
        raise OSError("caido")

    monkeypatch.setattr(L, "_abrir", todo_caido)
    with pytest.raises(L.LanceNoResponde):
        L.consultar("VJ102IMG_NRT", (-68, -24, -67, -23), "2026-11-27")


def test_cortacircuito_de_lance(monkeypatch):
    """R-2: con nrt3 y nrt4 caídos, la segunda consulta del proceso no espera a la red."""
    llamadas = []

    def todo_caido(url, timeout=None):
        llamadas.append(url)
        raise OSError("caido")

    monkeypatch.setattr(L, "_abrir", todo_caido)
    L.reiniciar()
    for _ in range(3):
        with pytest.raises(L.LanceNoResponde):
            L.consultar("VJ102IMG_NRT", (-68, -24, -67, -23), "2026-11-27")
    assert len(llamadas) == 2 and L.TIMEOUT_S <= 30
    L.reiniciar()


def test_respuesta_cortada_cae_al_espejo(monkeypatch):
    """R-5: IncompleteRead no es OSError; antes se escapaba y botaba lo de CMR."""
    def falso(url, timeout=None):
        if "nrt3" in url:
            raise http_client.IncompleteRead(b"{")
        return _Resp(json.dumps({"content": [ITEM_VJ1]}).encode())

    monkeypatch.setattr(L, "_abrir", falso)
    L.reiniciar()
    estado, val = resultado(lambda: L.consultar("VJ102IMG_NRT", (-68, -24, -67, -23), "2026-11-27"))
    assert estado == "ok" and len(val) == 1, val


# ── Tarea 3: salud de CMR ─────────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("cuerpo,esperado", [
    ({"internal-metadata-db": {"ok?": True}, "indexer": {"ok?": False}}, True),
    ({"internal-metadata-db": {"ok?": True}, "indexer": {"ok?": True}}, False),
])
def test_catalogo_congelado(monkeypatch, cuerpo, esperado):
    import urllib.error
    llamadas = []

    def falso(url, timeout=None):
        llamadas.append(url)
        datos = json.dumps(cuerpo).encode()
        if not esperado:
            return _Resp(datos)
        raise urllib.error.HTTPError(url, 503, "Service Unavailable", {}, io.BytesIO(datos))

    monkeypatch.setattr(L, "_abrir", falso)
    L.reiniciar()
    assert L.catalogo_congelado() is esperado
    assert L.catalogo_congelado() is esperado
    assert len(llamadas) == 1   # una vez por proceso


class _RespH(_Resp):
    def __init__(self, datos, headers=None):
        super().__init__(datos)
        self.headers = headers or {}


def _incompleto_con(monkeypatch, n_cmr, n_lance, nrt3_caido=False):
    urls = []

    def falso(url, timeout=None):
        urls.append(url)
        if "cmr.earthdata" in url:
            return _RespH(b"{}", {"CMR-Hits": str(n_cmr)})
        if nrt3_caido and "nrt3" in url:
            raise OSError("caido")
        cont = [{"resourceType": "File", "name": "f%d" % i} for i in range(n_lance)] + [{"resourceType": "Directory"}]
        return _RespH(json.dumps({"content": cont}).encode())

    monkeypatch.setattr(L, "_abrir", falso)
    L.reiniciar()
    return urls


@pytest.mark.parametrize("n_cmr,n_lance,esperado", [
    (241, 240, False),   # día sano: CMR lista uno más (el del borde del día anterior)
    (84, 86, False),     # dos de más: todavía latencia
    (84, 87, True),      # tres de más: hueco del catálogo
    (84, 151, True),     # 27-nov, MYD021KM, 13:36 UTC
])
def test_catalogo_incompleto_umbral(monkeypatch, n_cmr, n_lance, esperado):
    urls = _incompleto_con(monkeypatch, n_cmr, n_lance)
    assert L.catalogo_incompleto("MYD021KM", "6.1NRT", "2026-11-27") is esperado
    assert L.catalogo_incompleto("MYD021KM", "6.1NRT", "2026-11-27") is esperado
    assert len(urls) == 2                                            # una medición por producto y día
    assert "page_size=0" in urls[0] and "version=6.1NRT" in urls[0]
    assert urls[1].endswith("/api/v2/content/details/allData/61/MYD021KM/2026/331")


def test_catalogo_incompleto_usa_el_espejo_y_sin_red_es_falso(monkeypatch):
    urls = _incompleto_con(monkeypatch, 84, 151, nrt3_caido=True)
    assert L.catalogo_incompleto("VJ102IMG_NRT", "2.1", "2026-11-27") is True
    assert "nrt4" in urls[-1]

    def caido(url, timeout=None):
        raise OSError("sin red")

    monkeypatch.setattr(L, "_abrir", caido)
    L.reiniciar()
    assert L.catalogo_incompleto("VJ102IMG_NRT", "2.1", "2026-11-27") is False


def test_catalogo_incompleto_no_cuenta_archivos_recien_llegados(monkeypatch):
    """Un archivo de menos de 15 min puede estar en tránsito a CMR: no es hueco (día en curso)."""
    ahora = 1_800_000_000.0

    def falso(url, timeout=None):
        if "cmr.earthdata" in url:
            return _RespH(b"{}", {"CMR-Hits": "84"})
        viejos = [{"resourceType": "File", "mtime": ahora - 3600} for _ in range(84)]
        nuevos = [{"resourceType": "File", "mtime": ahora - 60} for _ in range(5)]
        return _RespH(json.dumps({"content": viejos + nuevos}).encode())

    monkeypatch.setattr(L, "_abrir", falso)
    L.reiniciar()
    assert L.catalogo_incompleto("MYD021KM", "6.1NRT", "2026-11-27", ahora=ahora) is False
    L.reiniciar()
    assert L.catalogo_incompleto("MYD021KM", "6.1NRT", "2026-11-27", ahora=ahora + L.EDAD_MIN_S) is True   # control


def test_catalogo_incompleto_respeta_y_enciende_el_cortacircuito(monkeypatch):
    llamadas = []

    def falso(url, timeout=None):
        llamadas.append(url)
        if "cmr.earthdata" in url:
            return _RespH(b"{}", {"CMR-Hits": "84"})
        raise OSError("LANCE colgado")

    monkeypatch.setattr(L, "_abrir", falso)
    L.reiniciar()
    assert L.catalogo_incompleto("MYD021KM", "6.1NRT", "2026-11-27") is False
    n = len(llamadas)
    assert n == 3                                                         # CMR-Hits, nrt3, nrt4
    assert L.catalogo_incompleto("VJ102IMG_NRT", "2.1", "2026-11-27") is False
    assert len(llamadas) == n                                             # cortacircuito: ni CMR ni LANCE otra vez
    estado, val = resultado(lambda: L.consultar("VJ102IMG_NRT", (-68, -24, -67, -23), "2026-11-27"))
    assert estado == "error" and isinstance(val, L.LanceNoResponde) and len(llamadas) == n
    L.reiniciar()


def test_hueco_solo_se_mide_hoy_y_ayer(entorno, monkeypatch):
    medidos = []
    monkeypatch.setattr(L, "catalogo_incompleto", lambda s, v, f: medidos.append(f) or True)
    entorno["lance"] = [item("VJ102IMG_NRT", "05:06", 1)]
    for atras in (0, fetch.LANCE_DIAS_HUECO, fetch.LANCE_DIAS_HUECO + 1):
        _buscar(dia=HOY - timedelta(days=atras))
    assert medidos == [(HOY - timedelta(days=a)).strftime("%Y-%m-%d") for a in (0, fetch.LANCE_DIAS_HUECO)]
    assert len(entorno["consultas"]) == 2                                 # el día viejo sin falla ni congelado no consulta


def test_cmr_sano_pero_incompleto_toma_lance(entorno):
    """27-nov 13:36 UTC: health sano, pero CMR sin la pasada 06:48 que LANCE tiene."""
    entorno["incompleto"] = True
    entorno["cmr"] = [gran_cmr("VJ102IMG_NRT", "2.1", DIA + "T05:06:00.000Z", "LANCEMODIS:1")]
    entorno["lance"] = [item("VJ102IMG_NRT", "05:06", 1, dia=DIA), item("VJ102IMG_NRT", "06:48", 2, dia=DIA)]
    assert [g["umm"]["GranuleUR"] for g in _buscar()] == ["LANCEMODIS:1", "LANCEMODIS:2"]


def test_catalogo_congelado_sin_red_es_falso(monkeypatch):
    def caido(url, timeout=None):
        raise OSError("sin red")

    monkeypatch.setattr(L, "_abrir", caido)
    L.reiniciar()
    assert L.catalogo_congelado() is False


# ── Tarea 4: envoltura en search_granules ────────────────────────────────────────────────────────────────────────
HOY = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
DIA = HOY.strftime("%Y-%m-%d")


@pytest.fixture
def entorno(monkeypatch):
    """CMR y LANCE falsos; devuelve un dict para fijar lo que responde cada uno y contar consultas a LANCE."""
    estado = {"cmr": [], "falla_cmr": False, "lance": [], "lance_caido": False, "congelado": False,
              "consultas": [], "cmr_error": None, "incompleto": False}

    def cmr_falso(product_key, lat, lon, radius_km, date):
        if estado["cmr_error"] is not None:
            raise estado["cmr_error"]
        if estado["falla_cmr"]:
            fetch._registrar_falla(product_key, date.strftime("%Y-%m-%d"), "SEARCH_CMR_TIMEOUT: ReadTimeout")
        return list(estado["cmr"])

    def lance_falso(short_name, bbox, fecha):
        estado["consultas"].append((short_name, fecha))
        if estado["lance_caido"]:
            raise L.LanceNoResponde("nrt3 y nrt4 caídos")
        return list(estado["lance"])

    monkeypatch.setattr(fetch, "_buscar_en_cmr", cmr_falso)
    monkeypatch.setattr(L, "consultar", lance_falso)
    monkeypatch.setattr(L, "catalogo_congelado", lambda: estado["congelado"])
    monkeypatch.setattr(L, "catalogo_incompleto", lambda s, v, f: estado["incompleto"])
    monkeypatch.delenv("VRP_LANCE_RESPALDO", raising=False)
    fetch.limpiar_fallas()
    fetch.reiniciar_respaldos_lance()
    yield estado
    fetch.limpiar_fallas()
    fetch.reiniciar_respaldos_lance()


def _buscar(clave="VIIRS_NOAA20_L1B", dia=HOY):
    return fetch.search_granules(clave, -23.37, -67.73, 25, dia)


def test_cmr_congelado_y_vacio_toma_lance(entorno):
    entorno["congelado"] = True
    entorno["lance"] = [item("VJ102IMG_NRT", "05:06", 1), item("VJ102IMG_NRT", "06:48", 2)]
    res = _buscar()
    assert [g["umm"]["GranuleUR"] for g in res] == ["LANCEMODIS:1", "LANCEMODIS:2"]
    assert entorno["consultas"] == [("VJ102IMG_NRT", DIA)]
    assert fetch.respaldos_lance()[0]["n"] == 2


def test_cmr_sano_y_vacio_no_consulta_lance(entorno):
    """R-3 del verificador: el día en curso a las 00 UTC no tiene pasadas; con CMR sano su vacío es la respuesta."""
    entorno["lance"] = [item("VJ102IMG_NRT", "05:06", 1)]
    assert _buscar() == []
    assert entorno["consultas"] == []


def test_cmr_con_error_503_toma_lance(entorno):
    """R-4: un 503 de CMR sale de earthaccess como RuntimeError; antes no pasaba por el respaldo."""
    entorno["cmr_error"] = RuntimeError("CMR 503 Service Unavailable")
    entorno["lance"] = [item("VJ102IMG_NRT", "05:06", 1, dia=DIA)]
    assert [g["umm"]["GranuleUR"] for g in _buscar()] == ["LANCEMODIS:1"]
    assert "RuntimeError: CMR 503" in fetch.respaldos_lance()[0]["falla_cmr"]


def test_cmr_con_error_y_lance_vacio_propaga_el_error(entorno):
    entorno["cmr_error"] = RuntimeError("CMR 503 Service Unavailable")
    estado, val = resultado(_buscar)
    assert estado == "error" and isinstance(val, RuntimeError) and "CMR 503" in str(val), (estado, val)
    assert entorno["consultas"] == [("VJ102IMG_NRT", DIA)]


def test_credencial_muerta_no_pasa_por_lance(entorno):
    entorno["cmr_error"] = fetch.EarthdataCredentialError("401")
    entorno["lance"] = [item("VJ102IMG_NRT", "05:06", 1)]
    estado, val = resultado(_buscar)
    assert estado == "error" and isinstance(val, fetch.EarthdataCredentialError), (estado, val)
    assert entorno["consultas"] == []


def test_error_inesperado_de_lance_no_quita_lo_de_cmr(entorno, monkeypatch):
    """R-5: nada de lo que pase en LANCE puede quitar lo que CMR trajo."""
    entorno["congelado"] = True
    entorno["cmr"] = [gran_cmr("VJ102IMG_NRT", "2.1", DIA + "T05:06:00.000Z", "LANCEMODIS:1")]

    def revienta(*a, **k):
        raise http_client.IncompleteRead(b"")

    monkeypatch.setattr(L, "consultar", revienta)
    estado, val = resultado(_buscar)
    assert estado == "ok" and [g["umm"]["GranuleUR"] for g in val] == ["LANCEMODIS:1"], (estado, val)


def test_item_ilegible_se_salta_sin_tumbar_los_demas(entorno):
    entorno["congelado"] = True
    malo = item("VJ102IMG_NRT", "05:06", 1)
    del malo["start"]
    entorno["lance"] = [malo, item("VJ102IMG_NRT", "06:48", 2)]
    assert [g["umm"]["GranuleUR"] for g in _buscar()] == ["LANCEMODIS:2"]


def test_fecha_con_zona_horaria(entorno):
    from datetime import timezone
    entorno["congelado"] = True
    entorno["lance"] = [item("VJ102IMG_NRT", "05:06", 1, dia=DIA)]
    estado, val = resultado(lambda: fetch.search_granules("VIIRS_NOAA20_L1B", -23.37, -67.73, 25,
                                                          HOY.replace(tzinfo=timezone.utc)))
    assert estado == "ok" and len(val) == 1, (estado, val)


def test_estandar_de_cmr_no_consulta_lance(entorno):
    entorno["cmr"] = [gran_cmr("VJ102IMG", "2.1", DIA + "T05:06:00.000Z", "VJ102IMG.A.0506")]
    entorno["congelado"] = True
    assert len(_buscar()) == 1
    assert entorno["consultas"] == []


def test_nrt_congelado_une_sin_duplicar(entorno):
    entorno["cmr"] = [gran_cmr("VJ102IMG_NRT", "2.1", DIA + "T05:06:00.000Z", "LANCEMODIS:1")]
    entorno["congelado"] = True
    entorno["lance"] = [item("VJ102IMG_NRT", "05:06", 1, dia=DIA), item("VJ102IMG_NRT", "06:48", 2, dia=DIA)]
    res = _buscar()
    assert [g["umm"]["GranuleUR"] for g in res] == ["LANCEMODIS:1", "LANCEMODIS:2"]
    assert res[0]["meta"].get("vrp-origen") != "lance"   # el de CMR se queda
    assert fetch.respaldos_lance()[0]["n"] == 1


def test_nrt_sano_no_consulta_lance(entorno):
    entorno["cmr"] = [gran_cmr("VJ102IMG_NRT", "2.1", DIA + "T05:06:00.000Z", "LANCEMODIS:1")]
    assert len(_buscar()) == 1
    assert entorno["consultas"] == []


def test_dia_viejo_no_consulta(entorno):
    entorno["congelado"] = True
    entorno["lance"] = [item("VJ102IMG_NRT", "05:06", 1)]
    assert _buscar(dia=HOY - timedelta(days=fetch.LANCE_DIAS + 1)) == []
    assert entorno["consultas"] == []
    assert len(_buscar(dia=HOY - timedelta(days=fetch.LANCE_DIAS))) == 1


def test_interruptor_apaga(entorno, monkeypatch):
    monkeypatch.setenv("VRP_LANCE_RESPALDO", "0")
    entorno["congelado"] = True
    entorno["lance"] = [item("VJ102IMG_NRT", "05:06", 1)]
    assert _buscar() == []
    assert entorno["consultas"] == []


def test_falla_de_cmr_recuperada_por_lance_sale_de_las_fallas(entorno):
    entorno["falla_cmr"] = True
    entorno["lance"] = [item("VJ102IMG_NRT", "05:06", 1, dia=DIA)]
    assert len(_buscar()) == 1
    assert fetch.fallas_de_cobertura() == []
    r = fetch.respaldos_lance()[0]
    assert r["producto"] == "VIIRS_NOAA20_L1B" and r["fecha"] == DIA and "SEARCH_CMR_TIMEOUT" in r["falla_cmr"]


def test_falla_de_cmr_y_lance_vacio_deja_la_falla(entorno):
    entorno["falla_cmr"] = True
    assert _buscar() == []
    assert len(fetch.fallas_de_cobertura()) == 1
    assert fetch.respaldos_lance() == []


def test_lance_caido_devuelve_lo_de_cmr(entorno):
    entorno["lance_caido"] = True
    entorno["congelado"] = True
    entorno["cmr"] = [gran_cmr("VJ102IMG_NRT", "2.1", DIA + "T05:06:00.000Z", "LANCEMODIS:1")]
    assert [g["umm"]["GranuleUR"] for g in _buscar()] == ["LANCEMODIS:1"]


def test_modis_usa_version_nrt(entorno):
    entorno["congelado"] = True
    entorno["lance"] = [dict(ITEM_MYD, start=DIA + " 08:30:00")]
    res = _buscar("MODIS_AQUA_L1B")
    assert entorno["consultas"] == [("MYD021KM", DIA)]
    assert res[0]["umm"]["CollectionReference"] == {"ShortName": "MYD021KM", "Version": "6.1NRT"}


def test_lance_ajeno_al_producto_no_se_mezcla(entorno):
    """La API filtra por producto, pero si devolviera otro, a_granulo lo rotularía mal: consultar ya filtra; aquí
    se comprueba que la envoltura no agrega lo que la consulta no devolvió."""
    entorno["lance"] = []
    assert _buscar() == []


# ── Filtro espacial (polígonos reales de LANCE, VJ202MOD_NRT del 2026-11-27, caja de Láscar) ────────────────────
def _poly(lat, lon):
    return {"gringLatitude%d" % (k + 1): v for k, v in enumerate(lat)} | \
           {"gringLongitude%d" % (k + 1): v for k, v in enumerate(lon)}


G_0548 = _poly([-25.112, -20.621, -0.218, -4.326], [-56.261, -85.498, -79.506, -52.787])    # CMR la lista
G_0554 = _poly([-45.775, -40.077, -20.509, -24.998], [-57.91, -95.164, -85.474, -56.255])   # contiene a Láscar
G_0412 = _poly([-43.996, -38.455, -18.781, -23.21], [-32.493, -68.702, -59.472, -30.642])   # borde a cientos de km


def test_toca_caja_con_poligonos_reales():
    media = 25 + L.TOLERANCIA_KM
    assert L.toca_caja(G_0554, -23.37, -67.73, media)
    assert L.toca_caja(G_0548, -23.37, -67.73, media)        # el GRing la deja 2 km fuera; la tolerancia la recupera
    assert not L.toca_caja(G_0548, -23.37, -67.73, 0.001)    # sin tolerancia quedaría fuera (por eso existe)
    assert not L.toca_caja(G_0412, -23.37, -67.73, media)
    assert L.toca_caja({}, -23.37, -67.73, media)             # sin polígono: ante la duda se baja


def test_tolerancia_recupera_un_borde_a_60_km():
    """Con CMR sano, pasadas que CMR lista quedaban con el GRing a 50 o más km de la caja (Villarrica VJ102IMG_NRT
    2026-11-25 18:12; salida_calibrar_filtro.txt): un borde a 60 km de la caja tiene que entrar."""
    import math
    k = 111.32 * math.cos(math.radians(-23.37))
    oeste = -67.73 - (25 + 60) / k                        # borde este del polígono a 60 km de la caja
    poly = _poly([-30.0, -30.0, -15.0, -15.0], [oeste - 5, oeste, oeste, oeste - 5])
    assert L.toca_caja(poly, -23.37, -67.73, 25 + L.TOLERANCIA_KM)
    assert not L.toca_caja(poly, -23.37, -67.73, 25 + 50)


def test_search_granules_descarta_lo_lejano(entorno):
    entorno["congelado"] = True
    entorno["lance"] =[dict(item("VJ202MOD_NRT", "04:12", 1), **G_0412),
                        dict(item("VJ202MOD_NRT", "05:54", 2), **G_0554)]
    res = _buscar("VIIRS_NOAA21_MOD_L1B")
    assert [g["umm"]["GranuleUR"] for g in res] == ["LANCEMODIS:2"]


# ── Integración liviana con el resto del flujo ──────────────────────────────────────────────────────────────────
def test_pareo_filtro_nocturno_y_minuto_con_granulos_de_lance():
    l1b = [L.a_granulo(item("VJ102IMG_NRT", "05:06", 1), "VJ102IMG_NRT", "2.1"),
           L.a_granulo(item("VJ102IMG_NRT", "17:30", 2), "VJ102IMG_NRT", "2.1")]
    geo = [L.a_granulo(item("VJ103IMG_NRT", "05:06", 3), "VJ103IMG_NRT", "2.1")]
    pares = fetch._match_granules(l1b, geo)
    assert len(pares) == 1 and pares[0][1]["umm"]["GranuleUR"] == "LANCEMODIS:3"
    noche = fetch._filter_nighttime_granules(l1b, -23.37, -67.73)
    assert [g["umm"]["GranuleUR"] for g in noche] == ["LANCEMODIS:1"]   # 17:30 UTC es de día en Láscar
    assert fetch._minuto_granulo(l1b[0]) == "2026-11-27 05:06"
