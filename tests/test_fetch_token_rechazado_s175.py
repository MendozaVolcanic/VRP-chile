"""S175: un token rechazado o mal formado debe dejar el NRT en ROJO.

POR QUÉ existe este archivo. Todo lo que el pipeline baja de NASA depende de un solo secreto. La
auditoría S175 (verificador V4T) confirmó que con ciertos rechazos el NRT quedaba VERDE sin escribir
un record, y el primer aviso llegaba a las 48 a 72 h: un operador deja de ver anomalías térmicas sin
enterarse. Los tests S123/S124 no lo veían porque armaban la excepción a mano, sin la forma real.

POR QUÉ la red se simula en el transporte y no en earthaccess. Lo que importa aquí es la forma exacta
del error, y esa forma la decide earthaccess con su propio código: si la armáramos a mano repetiríamos
el defecto de S123. Por eso earthaccess corre de verdad y sólo se reemplaza `HTTPAdapter.send`, la
última puerta antes del socket. Además se bloquean los sockets: ninguna prueba puede tocar NASA (A71,
un probe puede bloquear la cuenta) y todos los tokens son sintéticos.

Pruebas de control, verdes también antes del arreglo: el vencimiento natural, los cortes transitorios,
los 403 de EULA y la descarga normal. Vigilan lo que el arreglo no puede romper.
"""
from __future__ import annotations

import http.client
import importlib.util
import io
import json
import socket
import time
from datetime import datetime
from pathlib import Path

import earthaccess
import pytest
import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import ConnectTimeout, InvalidHeader, ReadTimeout
from requests.structures import CaseInsensitiveDict

import pipeline.fetch as fetch

FECHA = datetime(2026, 11, 3)
INICIO = "2026-11-03T05:00:00.000Z"
FIN = "2026-11-03T05:04:59.000Z"
VOLCAN = {"name": "Lascar", "lat": -23.37, "lon": -67.73, "radius_km": 25, "sensors": ["MODIS"]}
TOKEN_BUENO = "token-sintetico-s175"
SECRETO = "SECRETO-SINTETICO-S175"
ETIQUETA = "EARTHDATA_CREDENTIAL_INVALID"


def _corte_conexion(request):
    # POR QUÉ esta forma: es lo que HTTPAdapter.send levanta cuando el servidor corta la conexión.
    return requests.exceptions.ConnectionError(
        ConnectionResetError(104, "Connection reset by peer"), request=request)


def _timeout_conexion(request):
    return ConnectTimeout("connect timed out", request=request)


def _timeout_lectura(request):
    return ReadTimeout("read timed out", request=request)


def _granulo(producto: str) -> dict:
    url = (f"https://ladsweb.modaps.eosdis.nasa.gov/archive/allData/61/{producto}/2026/307/"
           f"{producto}.A2026307.0500.061.NRT.hdf")
    return {
        "meta": {"concept-id": f"G-{producto}-S175", "provider-id": "LAADS", "native-id": producto},
        "umm": {
            "GranuleUR": f"{producto}.A2026307.0500.061.NRT",
            "TemporalExtent": {"RangeDateTime": {"BeginningDateTime": INICIO, "EndingDateTime": FIN}},
            "RelatedUrls": [{"URL": url, "Type": "GET DATA"}],
            "SpatialExtent": {},
            "CollectionReference": {"ShortName": producto, "Version": "61"},
            "DataGranule": {"ArchiveAndDistributionInformation": [{"Size": 1.0, "SizeUnit": "MB"}]},
        },
    }


def _producto_de(url: str) -> str:
    # El orden importa: MOD03 no es subcadena de MOD021KM, pero así se lee sin pensar.
    for producto in ("MOD021KM", "MOD03", "MYD021KM", "MYD03"):
        if producto in url:
            return producto
    return "?"


class RedFalsa:
    """Responde en el transporte. Cada falla es (status, cuerpo) o una función request -> excepción."""

    def __init__(self):
        self.cmr = (200, None)
        self.descarga = (200, b"HDF-FALSO")
        self.descarga_por_producto: dict = {}
        self.peticiones: list[str] = []

    @property
    def n_descargas(self) -> int:
        return sum("ladsweb" in u for u in self.peticiones)

    @staticmethod
    def _respuesta(request, status, cuerpo, cabeceras=None):
        r = requests.Response()
        r.status_code = status
        r._content = cuerpo if cuerpo is not None else b""
        r.headers = CaseInsensitiveDict(cabeceras or {})
        r.url = request.url
        r.request = request
        r.encoding = "utf-8"
        r.raw = io.BytesIO(r._content)
        return r

    def _resolver(self, request, falla, cabeceras=None):
        if callable(falla):
            raise falla(request)
        status, cuerpo = falla
        return self._respuesta(request, status, cuerpo, cabeceras)

    def enviar(self, request):
        url = request.url
        self.peticiones.append(url)
        if "cmr.earthdata.nasa.gov" in url:
            if self.cmr != (200, None):
                return self._resolver(request, self.cmr, {"Content-Type": "application/json"})
            cuerpo = json.dumps({"hits": 1, "items": [_granulo(_producto_de(url))]}).encode()
            return self._respuesta(request, 200, cuerpo,
                                   {"CMR-Hits": "1", "Content-Type": "application/json"})
        if "ladsweb" in url:
            return self._resolver(request, self.descarga_por_producto.get(_producto_de(url), self.descarga))
        # Metadatos de nube y otros hosts que earthaccess consulta al iniciarse.
        return self._respuesta(request, 404, b"")


@pytest.fixture
def red(monkeypatch):
    falsa = RedFalsa()

    def sin_red(*a, **k):
        raise OSError("sin red en las pruebas S175")

    monkeypatch.setattr(socket.socket, "connect", sin_red)
    monkeypatch.setattr(socket, "create_connection", sin_red)
    monkeypatch.setattr(HTTPAdapter, "send", lambda self, request, **k: falsa.enviar(request))
    monkeypatch.setattr(time, "sleep", lambda *_: None)
    # POR QUÉ una sesión nueva: earthaccess guarda la autenticación en el módulo y, si ya estaba
    # autenticado, ignora el token nuevo. Un token de otra prueba cambiaría lo medido.
    monkeypatch.setattr(earthaccess, "_auth", earthaccess.Auth())
    monkeypatch.setattr(earthaccess, "__store__", None, raising=False)
    monkeypatch.setenv("EARTHDATA_TOKEN", TOKEN_BUENO)
    monkeypatch.delenv("EARTHDATA_USERNAME", raising=False)
    monkeypatch.delenv("EARTHDATA_PASSWORD", raising=False)
    monkeypatch.setattr(fetch, "_VENTANA", None)
    monkeypatch.setattr(fetch, "ENABLE_CMR_SEARCH_BREAKER", True)
    fetch.limpiar_fallas()
    fetch.reset_transient_breakers()
    yield falsa
    fetch.limpiar_fallas()
    fetch.reset_transient_breakers()


def _bajar(tmp_path):
    return fetch.fetch_for_volcano(VOLCAN, FECHA, tmp_path)


def _archivos(resultado) -> dict:
    return {plataforma: sorted(p.name for p in rutas) for plataforma, rutas in resultado.items()}


# --- 381: el rechazo de CMR, con un texto que el regex no reconoce -------------------------------

@pytest.mark.parametrize("cuerpo", [b'{"errors":["Token does not exist"]}',
                                    b"",
                                    b'{"errors":["Token is not a valid JWT"]}'],
                         ids=["no_existe", "vacio", "jwt_malformado"])
def test_cmr_401_con_texto_neutro_deja_rojo(red, tmp_path, cuerpo):
    red.cmr = (401, cuerpo)
    with pytest.raises(fetch.EarthdataCredentialError) as ei:
        _bajar(tmp_path)
    assert ETIQUETA in str(ei.value)
    assert "401" in str(ei.value), "el status real tiene que llegar al mensaje"


def test_el_status_del_401_se_recupera_de_la_excepcion_real(red):
    red.cmr = (401, b"")
    fetch.auth()
    with pytest.raises(RuntimeError) as ei:
        earthaccess.search_data(short_name="MOD021KM", version="6.1", count=1,
                                temporal=("2026-11-03", "2026-11-03"))
    assert ei.value.__cause__.response.status_code == 401, "la forma real tiene __cause__.response"
    assert fetch._is_credential_dead(ei.value) == (True, 401)


# --- 382: el rechazo en la descarga, que earthaccess deja sólo en el texto ----------------------

def test_descarga_401_deja_rojo_sin_reintentar(red, tmp_path, monkeypatch):
    red.descarga = (401, b"HTTP Basic: Access denied.\n")
    original, llamadas = fetch.earthaccess.download, []

    def contar(*a, **k):
        llamadas.append(1)
        return original(*a, **k)

    # POR QUÉ se cuenta la llamada y no las peticiones: earthaccess reintenta por su cuenta dentro
    # de cada descarga; lo que este arreglo controla son los cuatro intentos de download_granules.
    monkeypatch.setattr(fetch.earthaccess, "download", contar)
    with pytest.raises(fetch.EarthdataCredentialError) as ei:
        _bajar(tmp_path)
    assert ETIQUETA in str(ei.value)
    assert red.n_descargas > 0, "la descarga tiene que haberse intentado"
    assert len(llamadas) == 1, "un 401 no se cura reintentando"


def test_descarga_403_en_todo_el_volcan_deja_rojo(red, tmp_path):
    """Sin ninguna descarga buena y con 403 de LAADS no hay señal de que el token sirva."""
    red.descarga = (403, b"Forbidden")
    with pytest.raises(fetch.EarthdataCredentialError) as ei:
        _bajar(tmp_path)
    assert ETIQUETA in str(ei.value)
    assert "403" in str(ei.value)


def test_descarga_403_en_una_sola_plataforma_no_aborta(red, tmp_path):
    """Control: si otra plataforma baja, el token sirve y el 403 es de esa colección."""
    red.descarga_por_producto = {"MOD021KM": (403, b"Forbidden"), "MOD03": (403, b"Forbidden")}
    resultado = _archivos(_bajar(tmp_path))
    assert resultado["MODIS_TERRA"] == []
    assert len(resultado["MODIS_AQUA"]) == 2


# --- VPR966-01: la evidencia de que el token sirve vale para todo el proceso ---------------------

def _bajar_dia(tmp_path, nombre):
    # POR QUÉ la carpeta aparte y el reset: así llama run_pipeline, un volcán y una fecha cada vez,
    # con los cortacircuitos reiniciados entre fechas. Sin carpeta aparte el archivo ya existiría.
    fetch.reset_transient_breakers()
    return fetch.fetch_for_volcano(VOLCAN, FECHA, tmp_path / nombre)


def test_403_tras_dias_ya_bajados_no_manda_a_rotar_un_token_sano(red, tmp_path):
    """El NRT baja 7 días y deja el día en curso al final: a las 06 UTC sólo hay Terra publicado.

    Un 403 en esa última fecha no dice nada del token, que acaba de bajar días enteros. Abortar
    pone un volcán en rojo y manda a rotar un secreto sano. El hueco sí debe quedar en la cobertura.
    """
    _bajar_dia(tmp_path, "ayer")
    n_antes = red.n_descargas
    red.descarga = (403, b"Forbidden")
    resultado = _archivos(_bajar_dia(tmp_path, "hoy"))
    assert red.n_descargas > n_antes, "el 403 tiene que haber ocurrido; si no, la prueba no mide nada"
    assert resultado == {"MODIS_TERRA": [], "MODIS_AQUA": []}
    assert {f["plataforma"] for f in fetch.fallas_de_cobertura()} == {"MODIS_TERRA", "MODIS_AQUA"}


def test_una_corrida_nueva_olvida_las_descargas_de_la_anterior(red, tmp_path):
    """limpiar_fallas() marca el inicio de una corrida; lo de antes no avala al token de ahora."""
    _bajar_dia(tmp_path, "corrida_anterior")
    fetch.limpiar_fallas()
    red.descarga = (403, b"Forbidden")
    with pytest.raises(fetch.EarthdataCredentialError) as ei:
        _bajar_dia(tmp_path, "corrida_nueva")
    assert ETIQUETA in str(ei.value)


def test_control_401_tras_dias_ya_bajados_sigue_en_rojo(red, tmp_path):
    """Control: un 401 es un rechazo explícito y un token puede vencer a mitad de corrida."""
    _bajar_dia(tmp_path, "ayer")
    red.descarga = (401, b"Unauthorized")
    with pytest.raises(fetch.EarthdataCredentialError) as ei:
        _bajar_dia(tmp_path, "hoy")
    assert ETIQUETA in str(ei.value)


def test_control_un_corte_no_cuenta_como_descarga_buena(red, tmp_path):
    """Control: un día entero de cortes no prueba que el token sirva; el 403 siguiente aborta."""
    red.descarga = _timeout_lectura
    assert _archivos(_bajar_dia(tmp_path, "ayer")) == {"MODIS_TERRA": [], "MODIS_AQUA": []}
    red.descarga = (403, b"Forbidden")
    with pytest.raises(fetch.EarthdataCredentialError):
        _bajar_dia(tmp_path, "hoy")


def test_descarga_403_de_eula_en_todo_el_volcan_no_aborta(red, tmp_path):
    """Control: earthaccess la distingue por el cuerpo y es por colección, no por credencial."""
    red.descarga = (403, b"Please accept the EULA")
    assert not any(_archivos(_bajar(tmp_path)).values())


def test_cmr_403_de_permisos_no_aborta(red, tmp_path):
    """Control del diseño S123."""
    red.cmr = (403, b'{"errors":["User does not have permission to access collection"]}')
    assert not any(_archivos(_bajar(tmp_path)).values())


# --- V4T-01: el token que no se puede ni enviar --------------------------------------------------

@pytest.mark.parametrize("token", [f"{SECRETO}\n", f"{SECRETO}\r\n", f"{SECRETO[:9]}\n{SECRETO[9:]}"],
                         ids=["salto_final", "crlf_final", "salto_interior"])
def test_token_con_salto_de_linea_deja_rojo_antes_de_salir(red, tmp_path, monkeypatch, token):
    monkeypatch.setenv("EARTHDATA_TOKEN", token)
    with pytest.raises(fetch.EarthdataCredentialError) as ei:
        _bajar(tmp_path)
    assert ETIQUETA in str(ei.value)
    assert red.peticiones == [], "con el token inválido no debe salir ninguna petición"


def test_token_mal_formado_nunca_llega_al_log(red, tmp_path, monkeypatch, capsys):
    """El log de este repositorio es público: ni la salida, ni la excepción, ni la cobertura."""
    monkeypatch.setenv("EARTHDATA_TOKEN", f"{SECRETO}\n")
    visible = ""
    try:
        _bajar(tmp_path)
    except fetch.EarthdataCredentialError as e:
        visible += f"{e!r} {e.__cause__!r} {e.__context__!r}"
    salida = capsys.readouterr()
    visible += salida.out + salida.err + json.dumps(fetch.fallas_de_cobertura(), default=str)
    assert SECRETO not in visible


def _la_pila_lo_puede_enviar(token: str) -> bool:
    # POR QUÉ se pregunta a la pila real: `requests` valida la cabecera y `http.client` la codifica.
    # `putrequest` y `putheader` sólo llenan un búfer; la conexión no se abre.
    try:
        preparada = requests.Request("GET", "https://ejemplo.invalid/",
                                     headers={"Authorization": f"Bearer {token}"}).prepare()
        conexion = http.client.HTTPConnection("ejemplo.invalid")
        conexion.putrequest("GET", "/")
        conexion.putheader("Authorization", preparada.headers["Authorization"])
    except (InvalidHeader, ValueError):  # UnicodeEncodeError es un ValueError
        return False
    return True


@pytest.mark.parametrize("token", ["abc.def.ghi", "abc ", " abc", "ab cd", "   ", "\t", "caña",
                                   "abc\n", "abc\r", "a\nb", "\n", "abc…", "abcΔ"],
                         ids=repr)
def test_auth_rechaza_exactamente_lo_que_la_pila_no_puede_enviar(monkeypatch, token):
    """POR QUÉ la igualdad exacta: un validador más estricto podría tumbar un token que hoy funciona.

    Si NASA puede recibirlo, que decida NASA: su 401 ya deja el NRT en rojo. El validador sólo cubre
    lo que nunca sale del runner, que es justo lo que antes terminaba en verde.
    """
    monkeypatch.setenv("EARTHDATA_TOKEN", token)
    monkeypatch.setattr(fetch, "_probe_nasa_auth", lambda *a, **k: True)
    monkeypatch.setattr(fetch.earthaccess, "login", lambda *a, **k: None)
    try:
        fetch.auth()
        rechazado = False
    except fetch.EarthdataCredentialError:
        rechazado = True
    assert rechazado == (not _la_pila_lo_puede_enviar(token))


# --- Lo que no se puede romper --------------------------------------------------------------------

@pytest.mark.parametrize("cuerpo", [b'{"errors":["Token [ABC] has expired. Please get a new token"]}',
                                    b'{"errors":["Token [x] is invalid"]}'],
                         ids=["vencido", "invalido"])
def test_control_vencimiento_natural_sigue_en_rojo(red, tmp_path, cuerpo):
    red.cmr = (401, cuerpo)
    with pytest.raises(fetch.EarthdataCredentialError):
        _bajar(tmp_path)


def test_control_descarga_normal_entrega_los_mismos_archivos(red, tmp_path):
    resultado = _archivos(_bajar(tmp_path))
    assert resultado == {
        "MODIS_TERRA": ["MOD021KM.A2026307.0500.061.NRT.hdf", "MOD03.A2026307.0500.061.NRT.hdf"],
        "MODIS_AQUA": ["MYD021KM.A2026307.0500.061.NRT.hdf", "MYD03.A2026307.0500.061.NRT.hdf"],
    }
    assert fetch.fallas_de_cobertura() == []


CORTES_CMR = {
    "connect_timeout": _timeout_conexion, "conexion_reseteada": _corte_conexion, "read_timeout": _timeout_lectura,
    "500": (500, b"Internal Server Error"), "502": (502, b"<html>Bad Gateway</html>"), "503": (503, b""),
    "504": (504, b"Gateway Timeout"),
}
CORTES_DESCARGA = {
    "connect_timeout": _timeout_conexion, "conexion_reseteada": _corte_conexion, "read_timeout": _timeout_lectura,
    "500": (500, b"Internal Server Error"), "502": (502, b"<html>Bad Gateway</html>"), "503": (503, b""),
    "429": (429, b"Too Many Requests"),
}


@pytest.mark.parametrize("corte", CORTES_CMR.values(), ids=CORTES_CMR.keys())
def test_control_corte_de_cmr_no_es_credencial(red, tmp_path, corte):
    red.cmr = corte
    assert not any(_archivos(_bajar(tmp_path)).values())
    assert fetch.fallas_de_cobertura(), "el corte tiene que quedar en la cobertura"


@pytest.mark.parametrize("corte", CORTES_DESCARGA.values(), ids=CORTES_DESCARGA.keys())
def test_control_corte_de_descarga_no_es_credencial(red, tmp_path, corte):
    red.descarga = corte
    assert not any(_archivos(_bajar(tmp_path)).values())
    assert fetch.fallas_de_cobertura(), "el corte tiene que quedar en la cobertura"


@pytest.mark.parametrize("corte", [_timeout_lectura, (503, b"")], ids=["read_timeout", "503"])
def test_control_corte_en_una_plataforma_salta_solo_esa(red, tmp_path, corte):
    red.descarga_por_producto = {"MOD021KM": corte}
    resultado = _archivos(_bajar(tmp_path))
    assert resultado["MODIS_TERRA"] == []
    assert len(resultado["MODIS_AQUA"]) == 2


def test_5xx_que_menciona_unauthorized_no_es_credencial(red, tmp_path):
    """Una página de error de un balanceador puede traer esa palabra sin que el token tenga culpa."""
    red.cmr = (502, b"<html>upstream said Unauthorized</html>")
    assert not any(_archivos(_bajar(tmp_path)).values())
    assert fetch.fallas_de_cobertura()


# --- El rojo tiene que llegar hasta el proceso -----------------------------------------------------

def test_process_date_no_se_traga_el_rechazo(red, tmp_path, monkeypatch):
    """Sin esto, un rechazo detectado en fetch podría morir en un except más arriba y volver a verde."""
    espec = importlib.util.spec_from_file_location(
        "run_pipeline_s175", Path(__file__).resolve().parent.parent / "scripts" / "run_pipeline.py")
    run_pipeline = importlib.util.module_from_spec(espec)
    espec.loader.exec_module(run_pipeline)
    monkeypatch.setattr(run_pipeline, "TMP_DIR", tmp_path)
    red.cmr = (401, b"")
    with pytest.raises(fetch.EarthdataCredentialError):
        run_pipeline.process_date({**VOLCAN, "display_name": "Lascar"}, FECHA)
