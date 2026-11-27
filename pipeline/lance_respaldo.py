# ════════════════════════════════════════════════════════════════════
# FICHA SDA · lance_respaldo.py  ·  SDA: VRP Chile (clon MIROVA) · ID: VRP-CL
# Objetivo      : Encontrar en los servidores de LANCE las pasadas NRT que el catalogo CMR de NASA no lista
#                 cuando su indexador se cae o se congela, para que el NRT no las pierda. No detecta ni
#                 clasifica: decide que archivos se buscan, igual que fetch.py.
# Lógica        : Consulta el buscador espacial propio de LANCE (nrt3, y su espejo nrt4 si nrt3 no responde)
#                 por producto, dia y caja del volcan, y convierte cada respuesta en un granulo con la misma
#                 forma y el mismo enlace de descarga que da CMR para ese archivo. Revisa una vez por proceso
#                 la salud de CMR (search/health). Quien decide cuando usarlo es fetch.search_granules.
# Modelo/método : Reglas deterministicas. Sin aprendizaje automatico.
# Datos entrada : API de LANCE /api/v2/content/details (anonima) y CMR /search/health. SIN datos personales.
# Variables     : producto NRT, dia UTC, caja de busqueda (la misma que se le pide a CMR).
# Limitaciones  : La interseccion de la caja la calcula LANCE con su poligono (GRing), no con el de CMR: en el
#                 borde de una pasada puede incluir o excluir un granulo distinto; uno de mas se procesa y no
#                 cubre el volcan, uno de menos se pierde sólo cuando CMR ya fallo. LANCE retiene ~7 a 14 dias.
#                 La API de LANCE cambia mas que CMR y advierte bloqueo de IP por pedidos excesivos.
# Refs/datos    : D:\vrp-trabajo\temporales\s202\latencia_lance\INFORME.md (caida del 26-nov);
#                 D:\vrp-trabajo\temporales\s203\cmr27\lance_vs_cmr_331.txt (27-nov); Coppola et al. 2019
#                 (MIROVA lee LANCE). Plan: docs/superpowers/plans/2026-11-27-respaldo-lance.md.
#                 Entrenamiento: No aplica (sin ML). Ficha: docs/FICHA_SDA_VRP_CHILE.md
# ════════════════════════════════════════════════════════════════════
"""Respaldo de búsqueda por la API de LANCE (S203).

POR QUÉ. Las pasadas NRT llegan primero a LANCE y segundos después CMR las cataloga. El NRT busca sólo en CMR, y una
caída de su indexador no da error: da cero gránulos o una lista vieja. El 26 y el 27-nov de 2026 eso dejó al tablero
sin pasadas que LANCE ya tenía. LANCE tiene su propio buscador espacial, independiente de CMR, que devuelve cada archivo
con el mismo número (`fileId`) que CMR usa en `GranuleUR` (`LANCEMODIS:<fileId>`), así que el gránulo que se arma aquí
es el mismo archivo, con el mismo enlace, que el que habría dado CMR. Sin cambio científico.
"""
import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime

HOSTS = ("nrt3.modaps.eosdis.nasa.gov", "nrt4.modaps.eosdis.nasa.gov")
URL_SALUD_CMR = "https://cmr.earthdata.nasa.gov/search/health"
TIMEOUT_S = 60


class LanceNoResponde(RuntimeError):
    """Ni nrt3 ni nrt4 respondieron la consulta."""


def _abrir(url, timeout=None):
    """Punto único de red (las pruebas lo reemplazan)."""
    return urllib.request.urlopen(url, timeout=timeout)


def conjunto(producto: str) -> str:
    """Conjunto de archivo (archive set) de LANCE en la ruta allData, el mismo que usan los enlaces de CMR: 61 para
    MODIS 6.1 NRT, 5201 para NOAA-20 y NOAA-21 (v2.1), 5200 para Suomi NPP (v2)."""
    if producto.startswith(("MOD0", "MYD0")):
        return "61"
    if producto.startswith(("VJ1", "VJ2")):
        return "5201"
    if producto.startswith("VNP"):
        return "5200"
    raise KeyError(producto)


def consultar(short_name: str, bbox: tuple, fecha: str) -> list:
    """Gránulos de `short_name` del día `fecha` (AAAA-MM-DD) que tocan `bbox` (oeste, sur, este, norte), según el
    buscador de LANCE. Prueba nrt3 y, si no responde, nrt4; si ninguno responde, LanceNoResponde."""
    dia = datetime.strptime(fecha, "%Y-%m-%d")
    w, s, e, n = bbox
    region = "[BBOX]W%s N%s E%s S%s" % (w, n, e, s)
    query = "products=%s&temporalRanges=%d-%03d&regions=%s" % (
        short_name, dia.year, dia.timetuple().tm_yday, urllib.parse.quote(region))
    errores = []
    for host in HOSTS:
        url = "https://%s/api/v2/content/details?%s" % (host, query)
        try:
            with _abrir(url, timeout=TIMEOUT_S) as r:
                datos = json.load(r)
        except (OSError, ValueError) as ex:   # URLError y HTTPError son OSError; JSON roto es ValueError
            errores.append("%s: %s" % (host, ex))
            continue
        return [c for c in datos.get("content", [])
                if c.get("resourceType") == "File" and c.get("products") == short_name]
    raise LanceNoResponde("; ".join(errores))


def a_granulo(item: dict, short_name: str, version: str):
    """Convierte una respuesta de LANCE en un DataGranule con lo que el flujo lee de un gránulo de CMR: GranuleUR,
    inicio, colección y el enlace GET DATA (allData/<conjunto>/<producto>/<año>/<día>/<archivo>)."""
    from earthaccess.results import DataGranule
    inicio = datetime.strptime(item["start"], "%Y-%m-%d %H:%M:%S")
    archivo = item["downloadsLink"].rsplit("/", 1)[1]
    url = "https://%s/api/v2/content/archives/allData/%s/%s/%d/%03d/%s" % (
        HOSTS[0], conjunto(short_name), short_name, inicio.year, inicio.timetuple().tm_yday, archivo)
    ur = "LANCEMODIS:%s" % item["fileId"]
    return DataGranule({
        "meta": {"concept-id": "LANCE-" + ur, "provider-id": "LANCEMODIS", "vrp-origen": "lance"},
        "umm": {"GranuleUR": ur,
                "CollectionReference": {"ShortName": short_name, "Version": version},
                "TemporalExtent": {"RangeDateTime": {"BeginningDateTime": inicio.strftime("%Y-%m-%dT%H:%M:%S.000Z")}},
                "RelatedUrls": [{"URL": url, "Type": "GET DATA"}],
                "DataGranule": {"ArchiveAndDistributionInformation": [{"SizeInBytes": item.get("size", 0)}]}},
    })


_CONGELADO = None


def reiniciar() -> None:
    """Olvida la salud de CMR (pruebas y procesos largos)."""
    global _CONGELADO
    _CONGELADO = None


def catalogo_congelado() -> bool:
    """True si CMR dice que su indexador no está sano (`indexer` con `ok?` falso; CMR lo responde con HTTP 503). Una
    consulta por proceso. Sin respuesta legible, False: la falla de búsqueda de CMR ya dispara el respaldo sola."""
    global _CONGELADO
    if _CONGELADO is not None:
        return _CONGELADO
    try:
        try:
            with _abrir(URL_SALUD_CMR, timeout=20) as r:
                salud = json.load(r)
        except urllib.error.HTTPError as ex:
            salud = json.loads(ex.read().decode("utf-8"))
        _CONGELADO = (salud.get("indexer") or {}).get("ok?") is False
    except (OSError, ValueError, AttributeError):
        _CONGELADO = False
    return _CONGELADO
