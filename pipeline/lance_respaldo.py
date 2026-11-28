# ════════════════════════════════════════════════════════════════════
# FICHA SDA · lance_respaldo.py  ·  SDA: VRP Chile (clon MIROVA) · ID: VRP-CL
# Objetivo      : Encontrar en los servidores de LANCE las pasadas NRT que el catalogo CMR de NASA no lista
#                 cuando su indexador se cae o se congela, para que el NRT no las pierda. No detecta ni
#                 clasifica: decide que archivos se buscan, igual que fetch.py.
# Lógica        : Consulta el buscador espacial propio de LANCE (nrt3, y su espejo nrt4 si nrt3 no responde)
#                 por producto, dia y caja del volcan, y convierte cada respuesta en un granulo con la misma
#                 forma y el mismo enlace de descarga que da CMR para ese archivo. Revisa una vez por proceso
#                 la salud de CMR (search/health). Quien decide cuando usarlo es fetch.search_granules.
#                 Gasta a lo mas PRESUPUESTO_S (10 min) de red por proceso y salta el espejo que ya fallo; al
#                 agotarse, el proceso sigue sólo con CMR (S204, ronda 6 de Codex: R6FL-118, R6FL-V201, R6FL-102).
# Modelo/método : Reglas deterministicas. Sin aprendizaje automatico.
# Datos entrada : API de LANCE /api/v2/content/details (anonima) y CMR /search/health. SIN datos personales.
# Variables     : producto NRT, dia UTC, caja de busqueda (la misma que se le pide a CMR).
# Limitaciones  : La interseccion de la caja la calcula LANCE con su poligono (GRing), no con el de CMR: en el
#                 borde de una pasada puede incluir o excluir un granulo distinto; uno de mas se procesa y no
#                 cubre el volcan, uno de menos se pierde sólo cuando CMR ya fallo. LANCE retiene ~7 a 14 dias.
#                 La API de LANCE cambia mas que CMR y advierte bloqueo de IP por pedidos excesivos. Con el respaldo
#                 activo, en VIIRS 750 (sin corte de 5 km al centro) un granulo de borde que CMR habria excluido puede
#                 dejar un record «escena_invalida» de 0 MW (pasada no medida) que con CMR no existiria; y el dia de
#                 un granulo que cruza la medianoche puede no coincidir con el de CMR (verificador limpio S203, R-3
#                 y R-7). Cuantos casos: SIN MEDIR; solo ocurre cuando el respaldo dispara para ese producto y dia
#                 (CMR fallo, esta congelado o le faltan archivos de ese producto y dia), aunque el hueco este en
#                 horas que no tocan al volcan. Con CMR sano y completo agrega dos pedidos (CMR-Hits y listado de
#                 la carpeta de LANCE) por producto y dia, solo hoy y ayer, una vez por proceso.
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
import contextlib
import http.client
import json
import math
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime

HOSTS = ("nrt3.modaps.eosdis.nasa.gov", "nrt4.modaps.eosdis.nasa.gov")
URL_SALUD_CMR = "https://cmr.earthdata.nasa.gov/search/health"
# POR QUÉ 30 s y un cortacircuito por proceso (verificador limpio S203, R-2): con CMR caído cada búsqueda pasa por
# aquí; si LANCE también está colgado, 60 s por host y por búsqueda sumaban hasta 96 min en un job que tiene 50. Ahora
# la primera vez que nrt3 y nrt4 fallan juntos, LANCE queda marcado caído para el resto del proceso: el peor caso es
# una espera de 2 × 30 s por proceso.
TIMEOUT_S = 30
_CAIDO = False
_ERRORES_RED = (OSError, ValueError, http.client.HTTPException)   # URLError y HTTPError son OSError; IncompleteRead no
# POR QUÉ un presupuesto de tiempo por proceso (ronda 6 de Codex, R6FL-118 y R6FL-102, verificados por un Claude de
# contexto limpio en gravedad 3): el cortacircuito sólo salta si nrt3 y nrt4 fallan juntos, y LANCE puede responder
# lento sin fallar (con respuestas de 29 s y CMR caído en 8 fechas por 12 productos, 46 min sólo de LANCE, en un job de
# 50). Toda llamada de red de este módulo gasta de un mismo presupuesto; al agotarse, LANCE queda marcado caído y el
# resto del proceso usa sólo CMR, como antes del respaldo. 10 min: el 27-nov (run 46044996773) el respaldo de Láscar
# tardó unos 40 s en 12 productos, así que un día normal usa menos de una décima.
PRESUPUESTO_S = 600
_GASTADO = 0.0
_reloj = time.monotonic
# POR QUÉ se salta el host que falló (R6FL-V201): con nrt3 colgado y nrt4 sano el cortacircuito no salta y cada consulta
# pagaba 30 s en nrt3 antes de ir a nrt4 (48 min). El primer host que falla pasa al final de la lista para el resto
# del proceso.
_ORDEN = list(HOSTS)


@contextlib.contextmanager
def _con_presupuesto(url, timeout):
    """Abre `url` gastando del presupuesto del proceso todo lo que dure el bloque (apertura y lectura del cuerpo); si
    ya se agotó, enciende el cortacircuito y no sale a la red."""
    global _GASTADO, _CAIDO
    if _GASTADO >= PRESUPUESTO_S:
        _CAIDO = True
        raise LanceNoResponde("presupuesto de %d s del respaldo agotado en este proceso" % PRESUPUESTO_S)
    t0 = _reloj()
    try:
        with _abrir(url, timeout=timeout) as r:
            yield r
    finally:
        _GASTADO += _reloj() - t0


def _fallo_host(host):
    """El host que no respondió pasa al final del orden para el resto del proceso."""
    if host in _ORDEN and _ORDEN[-1] != host:
        _ORDEN.remove(host)
        _ORDEN.append(host)


class LanceNoResponde(RuntimeError):
    """Ni nrt3 ni nrt4 respondieron la consulta (o LANCE ya se marcó caído en este proceso)."""


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
    buscador de LANCE. Prueba nrt3 y, si no responde, nrt4; si ninguno responde, LanceNoResponde y LANCE queda
    marcado caído para el resto del proceso."""
    global _CAIDO
    if _CAIDO:
        raise LanceNoResponde("LANCE marcado caído en este proceso (cortacircuito)")
    dia = datetime.strptime(fecha, "%Y-%m-%d")
    w, s, e, n = bbox
    region = "[BBOX]W%s N%s E%s S%s" % (w, n, e, s)
    query = "products=%s&temporalRanges=%d-%03d&regions=%s" % (
        short_name, dia.year, dia.timetuple().tm_yday, urllib.parse.quote(region))
    errores = []
    for host in list(_ORDEN):
        url = "https://%s/api/v2/content/details?%s" % (host, query)
        try:
            with _con_presupuesto(url, TIMEOUT_S) as r:
                datos = json.load(r)
        except _ERRORES_RED as ex:
            errores.append("%s: %s" % (host, ex))
            _fallo_host(host)
            continue
        return [c for c in datos.get("content", [])
                if c.get("resourceType") == "File" and c.get("products") == short_name]
    _CAIDO = True
    raise LanceNoResponde("; ".join(errores))


# Tolerancia del filtro espacial, en km sobre el radio de búsqueda. POR QUÉ existe el filtro: la búsqueda por región de
# LANCE devuelve también gránulos cuyo polígono queda a cientos de km de la caja (Láscar 2026-11-27: NOAA-21 04:12 con
# el borde a 573 km). POR QUÉ tan generoso: el polígono GRing de LANCE tiene sólo cuatro esquinas y no sigue el borde
# curvo de la pasada, así que no reproduce a CMR. Calibrado contra CMR sano (2026-11-21, 23 y 25; Láscar, Villarrica,
# Nevados de Chillán y Chaitén; VJ102IMG_NRT, VJ202MOD_NRT, MOD021KM y MYD021KM; 176 gránulos de LANCE,
# D:\vrp-trabajo\temporales\s203\lance_vivo\salida_calibrar_filtro.txt): con 25 km se pierden 5 de 123 pasadas que CMR
# lista; con 100 km, 1 (diurna) y entran 23 de más. Uno de más no hace daño: si no cubre el volcán, la vía devuelve None
# y no hay record (mirova_v750_codigo.calcular_vrp_granulo: menos de 100 píxeles a menos de 45 km del cráter); sólo
# cuesta su descarga, y sólo cuando CMR falló.
TOLERANCIA_KM = 100.0


def _plano(lon, lat, lon0, lat0):
    return (lon - lon0) * 111.32 * math.cos(math.radians(lat0)), (lat - lat0) * 111.0


def _cruzan(p1, p2, q1, q2):
    def o(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    return o(p1, p2, q1) * o(p1, p2, q2) < 0 and o(q1, q2, p1) * o(q1, q2, p2) < 0


def _dentro(pt, poly):
    c = False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
        if (y1 > pt[1]) != (y2 > pt[1]) and pt[0] < (x2 - x1) * (pt[1] - y1) / (y2 - y1) + x1:
            c = not c
    return c


def toca_caja(item: dict, lat: float, lon: float, media_km: float) -> bool:
    """True si el polígono GRing del gránulo corta el cuadrado de lado 2·media_km centrado en (lat, lon), en plano
    local. Sin polígono legible, True: ante la duda se baja y la vía decide si cubre el volcán."""
    try:
        poly = [_plano(float(item["gringLongitude%d" % k]), float(item["gringLatitude%d" % k]), lon, lat)
                for k in (1, 2, 3, 4)]
    except (KeyError, TypeError, ValueError):
        return True
    caja = [(-media_km, -media_km), (media_km, -media_km), (media_km, media_km), (-media_km, media_km)]
    if any(_dentro(c, poly) for c in caja) or any(abs(x) <= media_km and abs(y) <= media_km for x, y in poly):
        return True
    return any(_cruzan(poly[i], poly[(i + 1) % 4], caja[j], caja[(j + 1) % 4]) for i in range(4) for j in range(4))


def a_granulo(item: dict, short_name: str, version: str):
    """Convierte una respuesta de LANCE en un DataGranule con lo que el flujo lee de un gránulo de CMR: GranuleUR,
    inicio, colección y el enlace GET DATA (allData/<conjunto>/<producto>/<año>/<día>/<archivo>).
    POR QUÉ el host del propio ítem (verificador limpio S203, R-1): nrt3 y nrt4 procesan cada pasada por separado y el
    archivo lleva otra marca de producción (MYD03 27-nov 08:30: ...100627 en nrt3, ...095452 en nrt4); el nombre que
    dio nrt4 sólo existe en nrt4 (allData de nrt4 lo lista con ese mismo enlace, comprobado el 2026-11-27)."""
    from earthaccess.results import DataGranule
    inicio = datetime.strptime(item["start"], "%Y-%m-%d %H:%M:%S")
    host = urllib.parse.urlparse(item["downloadsLink"]).netloc
    if host not in HOSTS:
        raise ValueError("enlace de LANCE con un host inesperado: %r" % item["downloadsLink"])
    archivo = item["downloadsLink"].rsplit("/", 1)[1]
    url = "https://%s/api/v2/content/archives/allData/%s/%s/%d/%03d/%s" % (
        host, conjunto(short_name), short_name, inicio.year, inicio.timetuple().tm_yday, archivo)
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
_INCOMPLETO: dict = {}
URL_CMR_GRANULOS = "https://cmr.earthdata.nasa.gov/search/granules.json"
# POR QUÉ un segundo disparador (S203, medido el 27-nov a las 13:36 UTC): cuando el indexador de CMR vuelve, `health` dice
# sano y CMR cataloga las pasadas NUEVAS, pero las del tiempo que estuvo caído no vuelven (MYD021KM del día 331: 151
# archivos en LANCE, 84 en CMR; MOD021KM sin nada después de las 06:15). Mirar sólo la salud perdería justo ese hueco.
# Se compara, por producto y día, cuántos archivos tiene la carpeta de LANCE con cuántos lista CMR. En días sanos CMR
# lista uno MÁS que la carpeta (el gránulo del borde del día anterior) en los ocho productos medidos (2026-11-21 y 23,
# D:\vrp-trabajo\temporales\s203\cmr27\lance_vs_cmr_325.txt y _327.txt); con CMR sano el gránulo llega al catálogo
# segundos después que a la carpeta (S202). Tres de más en LANCE ya no es latencia: es un hueco del catálogo.
UMBRAL_HUECO = 3
# Sólo cuentan los archivos de la carpeta con al menos EDAD_MIN_S de antigüedad (campo mtime): con CMR sano el gránulo
# llega al catálogo segundos después que a la carpeta (S202), así que uno más nuevo puede estar en tránsito y no es
# hueco (verificador limpio S203, segunda pasada, mecanismo (a): día en curso).
EDAD_MIN_S = 15 * 60


def reiniciar() -> None:
    """Olvida la salud de CMR, los huecos medidos y el cortacircuito de LANCE (pruebas y procesos largos)."""
    global _CONGELADO, _CAIDO, _GASTADO
    _CONGELADO = None
    _CAIDO = False
    _GASTADO = 0.0
    _ORDEN[:] = list(HOSTS)
    _INCOMPLETO.clear()


def _antiguo(c: dict, limite: float) -> bool:
    """True si el archivo es anterior a `limite`. Un mtime ausente o ilegible cuenta como antiguo: un dato raro de un
    archivo no puede tomarse como LANCE caído y apagar el respaldo (verificador limpio S203, tercera pasada)."""
    try:
        return float(c.get("mtime", 0)) <= limite
    except (TypeError, ValueError):
        return True


def catalogo_incompleto(short_name: str, version: str, fecha: str, ahora: float | None = None) -> bool:
    """True si la carpeta del día en LANCE tiene al menos UMBRAL_HUECO archivos (de más de EDAD_MIN_S) más que los
    gránulos que CMR lista para ese producto y día. Una medición por producto y día por proceso. Sin respuesta legible
    de alguno de los dos, False (la falla de búsqueda de CMR ya dispara el respaldo sola). Respeta el cortacircuito de
    LANCE y lo enciende si nrt3 y nrt4 no responden el listado (verificador limpio S203, segunda pasada: sin esto, con
    CMR sano y LANCE colgado un job esperaba hasta 96 min)."""
    global _CAIDO
    if _CAIDO:
        return False
    clave = (short_name, version, fecha)
    if clave in _INCOMPLETO:
        return _INCOMPLETO[clave]
    dia = datetime.strptime(fecha, "%Y-%m-%d")
    limite = (time.time() if ahora is None else ahora) - EDAD_MIN_S
    resultado = False
    try:
        q = urllib.parse.urlencode({"short_name": short_name, "version": version, "page_size": 0,
                                    "temporal": "%sT00:00:00Z,%sT23:59:59Z" % (fecha, fecha)})
        with _con_presupuesto(URL_CMR_GRANULOS + "?" + q, TIMEOUT_S) as r:
            n_cmr = int(r.headers.get("CMR-Hits"))
        n_lance = None
        for host in list(_ORDEN):
            url = "https://%s/api/v2/content/details/allData/%s/%s/%d/%03d" % (
                host, conjunto(short_name), short_name, dia.year, dia.timetuple().tm_yday)
            try:
                with _con_presupuesto(url, TIMEOUT_S) as r:
                    n_lance = sum(1 for c in json.load(r).get("content", [])
                                  if c.get("resourceType") == "File" and _antiguo(c, limite))
                break
            except _ERRORES_RED:
                _fallo_host(host)
                continue
        if n_lance is None:
            _CAIDO = True
        resultado = n_lance is not None and n_lance - n_cmr >= UMBRAL_HUECO
    except (_ERRORES_RED + (TypeError, KeyError, LanceNoResponde)):   # LanceNoResponde: presupuesto agotado
        resultado = False
    _INCOMPLETO[clave] = resultado
    return resultado


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
