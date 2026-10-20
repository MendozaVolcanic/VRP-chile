"""S157: buscar en CMR una vez por producto y por ventana, no una vez por dia.

POR QUE. Medido en experiments/_s157_busqueda_ventana/MEDICION.md: cada dia y plataforma hace dos busquedas a CMR
(L1B y geolocalizacion), ~590 por trozo de 37 dias. Con CMR lento eso es 45 a 63 % del job; con CMR caido cada
busqueda falla con HTTP 500, cae al `except` generico de fetch_for_volcano y el job sale verde sin datos.

LO QUE ESTAS PRUEBAS FIJAN. (1) La respuesta por dia que sale de la ventana es la MISMA lista que la consulta de un
dia (earthaccess 0.17 manda `temporal=(D, D)` como [D 00:00:00Z, D 23:59:59Z] y CMR cruza por traslape con bordes
incluidos), incluida la regla standard primero, versiones en orden, NRT si el standard del dia viene vacio. (2) Si
la ventana no se puede usar, se vuelve al camino de hoy. (3) Toda busqueda o descarga que no se pudo hacer queda
registrada (cobertura), y un dia sin granulos no.

El CMR simulado responde con la misma regla de traslape y en orden de inicio, como el real.
"""
import copy
from datetime import datetime, timedelta

import pytest
from earthaccess.results import DataGranule
from requests.exceptions import ReadTimeout

import pipeline.fetch as fetch

LAT, LON, R = -36.86, -71.38, 25.0
# Valor de produccion, leido ANTES de que el fixture lo cambie a [0, 0] para que las pruebas no esperen.
ESPERAS_PRODUCCION = list(fetch._VENTANA_ESPERAS_S)
D0 = datetime(2026, 7, 18)


def _fmt(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"


def _g(ur, ini, minutos=5):
    fin = ini + timedelta(minutes=minutos)
    return {"meta": {"concept-id": "G-" + ur, "provider-id": "LAADS"},
            "umm": {"GranuleUR": ur,
                    "TemporalExtent": {"RangeDateTime": {"BeginningDateTime": _fmt(ini),
                                                         "EndingDateTime": _fmt(fin)}},
                    "RelatedUrls": [{"URL": f"https://ladsweb.modaps.eosdis.nasa.gov/archive/{ur}.hdf",
                                     "Type": "GET DATA"}]}}


def _ts(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%fZ")


class FakeCMR:
    """earthaccess.search_data simulado: traslape con bordes incluidos, orden por inicio, corte en `count`."""

    def __init__(self, catalogo, fallar=None):
        self.catalogo = catalogo
        self.llamadas = []
        self.fallar = fallar

    def __call__(self, short_name, version, bounding_box, temporal, count):
        self.llamadas.append((short_name, version, temporal))
        if self.fallar:
            self.fallar(short_name, version, temporal)
        lo = datetime.strptime(temporal[0], "%Y-%m-%d")
        hi = datetime.strptime(temporal[1], "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        sel = []
        for g in self.catalogo.get((short_name, version), []):
            rd = g["umm"]["TemporalExtent"]["RangeDateTime"]
            if _ts(rd["BeginningDateTime"]) <= hi and _ts(rd["EndingDateTime"]) >= lo:
                sel.append(g)
        sel.sort(key=lambda g: g["umm"]["TemporalExtent"]["RangeDateTime"]["BeginningDateTime"])
        return [DataGranule(copy.deepcopy(g), cloud_hosted=False) for g in sel][:count]

    def n_ventana(self):
        return sum(1 for _, _, t in self.llamadas if t[0] != t[1])


def _urs(lista):
    return [g["umm"]["GranuleUR"] for g in lista]


def _dias(n, desde=D0):
    return [desde + timedelta(days=k) for k in range(n)]


def _noches(sn, dias, hora=5, sufijo=""):
    """Dos granulos por dia (una pasada que cae en dos granulos de 5 min)."""
    out = []
    for d in dias:
        for m in (0, 5):
            ini = d.replace(hour=hora, minute=m)
            out.append(_g(f"{sn}.{ini:%Y%j.%H%M}{sufijo}", ini))
    return out


def _red_prohibida(*a, **k):
    raise AssertionError("una prueba no puede tocar NASA (ni auth con el netrc local, A71)")


@pytest.fixture(autouse=True)
def _limpio(monkeypatch):
    # Candado: auth, login y descarga reales prohibidos; cada prueba simula search_data.
    monkeypatch.setattr(fetch.earthaccess, "login", _red_prohibida)
    monkeypatch.setattr(fetch.earthaccess, "download", _red_prohibida)
    monkeypatch.setattr(fetch.earthaccess, "search_data", _red_prohibida)
    fetch.reiniciar_ventana()
    fetch.limpiar_fallas()
    fetch._CMR_SEARCH_DOWN = False
    monkeypatch.setattr(fetch, "ENABLE_CMR_SEARCH_BREAKER", True)
    monkeypatch.setattr(fetch, "_VENTANA_ESPERAS_S", [0, 0])
    monkeypatch.delenv("VRP_BUSQUEDA_VENTANA", raising=False)
    yield
    fetch.reiniciar_ventana()
    fetch.limpiar_fallas()
    fetch._CMR_SEARCH_DOWN = False


def _por_dia(fake, monkeypatch, producto, dias):
    """Lo que devuelve HOY (sin ventana) cada dia: la referencia de identidad."""
    fetch.reiniciar_ventana()
    monkeypatch.setattr(fetch.earthaccess, "search_data", fake)
    return {d.strftime("%Y-%m-%d"): _urs(fetch.search_granules(producto, LAT, LON, R, d)) for d in dias}


def _con_ventana(fake, monkeypatch, producto, dias, **kw):
    fetch.reiniciar_ventana()
    monkeypatch.setattr(fetch.earthaccess, "search_data", fake)
    assert fetch.configurar_ventana(dias, **kw)
    return {d.strftime("%Y-%m-%d"): _urs(fetch.search_granules(producto, LAT, LON, R, d)) for d in dias}


# ---------------------------------------------------------------- reparto por dia (funcion pura)

def _dg(ur, ini, minutos=5):
    return DataGranule(_g(ur, ini, minutos), cloud_hosted=False)


def test_reparto_por_traslape_y_granulo_que_cruza_la_medianoche_va_a_los_dos_dias():
    dias = ["2026-07-18", "2026-07-19"]
    a = _dg("A", datetime(2026, 7, 18, 5, 0))
    cruza = _dg("X", datetime(2026, 7, 18, 23, 57), minutos=6)
    b = _dg("B", datetime(2026, 7, 19, 6, 0))
    out = fetch._repartir_por_dia([a, cruza, b], dias)
    assert _urs(out["2026-07-18"]) == ["A", "X"]
    assert _urs(out["2026-07-19"]) == ["X", "B"]


@pytest.mark.parametrize("ini,minutos", [
    (datetime(2026, 7, 18, 23, 54), 6),                       # termina justo a las 00:00:00.000
    (datetime(2026, 7, 18, 23, 59, 59, 500000), 5),           # empieza en el ultimo segundo del dia
    (datetime(2026, 7, 19, 0, 0, 1), 5),                       # empieza al segundo de la medianoche
])
def test_reparto_cerca_de_la_medianoche_se_consulta_por_dia(ini, minutos):
    out = fetch._repartir_por_dia([_dg("M", ini, minutos)], ["2026-07-18", "2026-07-19"])
    assert out["2026-07-18"] is None and out["2026-07-19"] is None


def test_reparto_sin_tiempos_se_consulta_por_dia():
    g = DataGranule({"meta": {}, "umm": {"GranuleUR": "S"}}, cloud_hosted=False)
    out = fetch._repartir_por_dia([g, _dg("A", datetime(2026, 7, 18, 5))], ["2026-07-18", "2026-07-19"])
    assert out == {"2026-07-18": None, "2026-07-19": None}


def test_reparto_con_veinte_o_mas_en_un_dia_se_consulta_por_dia():
    # la consulta de un dia pide count=20: con 20 o mas, la de hoy truncaria y no seria la misma lista
    veinte = [_dg(f"G{k}", datetime(2026, 7, 18, 4) + timedelta(minutes=5 * k)) for k in range(20)]
    diecinueve = [_dg(f"H{k}", datetime(2026, 7, 19, 4) + timedelta(minutes=5 * k)) for k in range(19)]
    out = fetch._repartir_por_dia(veinte + diecinueve, ["2026-07-18", "2026-07-19"])
    assert out["2026-07-18"] is None
    assert len(out["2026-07-19"]) == 19


# ---------------------------------------------------------------- la ventana reproduce la consulta de un dia

def test_una_consulta_por_producto_y_misma_lista_que_por_dia(monkeypatch):
    dias = _dias(8)
    cat = {("MOD021KM", "6.1"): _noches("MOD021KM", dias),
           ("MOD03", "6.1"): _noches("MOD03", dias)}
    for prod in ("MODIS_TERRA_L1B", "MODIS_TERRA_GEO"):
        ref = _por_dia(FakeCMR(cat), monkeypatch, prod, dias)
        fake = FakeCMR(cat)
        assert _con_ventana(fake, monkeypatch, prod, dias) == ref
        assert len(fake.llamadas) == 1, fake.llamadas


def test_standard_primero_y_nrt_solo_en_los_dias_sin_standard(monkeypatch):
    dias = _dias(8)
    cat = {("VNP02IMG", "2"): _noches("VNP02IMG", dias[:5]),
           ("VNP02IMG_NRT", "2"): _noches("VNP02IMG_NRT", dias[3:], sufijo=".nrt")}
    ref = _por_dia(FakeCMR(cat), monkeypatch, "VIIRS_SNPP_L1B", dias)
    fake = FakeCMR(cat)
    out = _con_ventana(fake, monkeypatch, "VIIRS_SNPP_L1B", dias)
    assert out == ref
    assert all(".nrt" not in u for d in dias[:5] for u in out[d.strftime("%Y-%m-%d")])
    assert all(".nrt" in u for d in dias[5:] for u in out[d.strftime("%Y-%m-%d")])
    # el NRT se consulta solo sobre el tramo que el standard no resolvio
    assert fake.llamadas[1] == ("VNP02IMG_NRT", "2", ("2026-07-23", "2026-07-25"))


def test_versiones_en_orden_noaa20(monkeypatch):
    dias = _dias(8)
    cat = {("VJ102IMG", "2.1"): _noches("VJ102IMG", dias[:3], sufijo=".v21"),
           ("VJ102IMG", "2"): _noches("VJ102IMG", dias, sufijo=".v2")}
    ref = _por_dia(FakeCMR(cat), monkeypatch, "VIIRS_NOAA20_L1B", dias)
    fake = FakeCMR(cat)
    assert _con_ventana(fake, monkeypatch, "VIIRS_NOAA20_L1B", dias) == ref
    assert [c[1] for c in fake.llamadas] == ["2.1", "2"]


def test_dia_vacio_en_todos_los_intentos_queda_vacio(monkeypatch):
    dias = _dias(5)
    cat = {("MOD021KM", "6.1"): _noches("MOD021KM", [dias[0], dias[4]])}
    ref = _por_dia(FakeCMR(cat), monkeypatch, "MODIS_TERRA_L1B", dias)
    assert _con_ventana(FakeCMR(cat), monkeypatch, "MODIS_TERRA_L1B", dias) == ref
    assert ref["2026-07-20"] == []


def test_ventana_truncada_cae_al_camino_por_dia(monkeypatch):
    dias = _dias(4)
    cat = {("MOD021KM", "6.1"): _noches("MOD021KM", dias)}
    monkeypatch.setattr(fetch, "_VENTANA_COUNT", 5)  # 8 granulos en la ventana: el corte la trunca
    ref = _por_dia(FakeCMR(cat), monkeypatch, "MODIS_TERRA_L1B", dias)
    fake = FakeCMR(cat)
    assert _con_ventana(fake, monkeypatch, "MODIS_TERRA_L1B", dias) == ref
    assert sum(1 for _, _, t in fake.llamadas if t[0] == t[1]) == 4


def test_fuera_de_la_ventana_va_por_el_camino_de_hoy(monkeypatch):
    dias = _dias(3)
    cat = {("MOD021KM", "6.1"): _noches("MOD021KM", _dias(5))}
    fake = FakeCMR(cat)
    monkeypatch.setattr(fetch.earthaccess, "search_data", fake)
    fetch.configurar_ventana(dias)
    fetch.search_granules("MODIS_TERRA_L1B", LAT, LON, R, D0 + timedelta(days=4))
    assert fake.n_ventana() == 0 and len(fake.llamadas) == 1


def test_cada_caja_tiene_su_propia_ventana(monkeypatch):
    # dos volcanes en el mismo proceso (corrida local de todos): cada caja consulta su ventana, sin mezclarse
    dias = _dias(3)
    cat = {("MOD021KM", "6.1"): _noches("MOD021KM", dias)}
    fake = FakeCMR(cat)
    monkeypatch.setattr(fetch.earthaccess, "search_data", fake)
    fetch.configurar_ventana(dias)
    for d in dias:
        fetch.search_granules("MODIS_TERRA_L1B", LAT, LON, R, d)
        fetch.search_granules("MODIS_TERRA_L1B", LAT + 1, LON, R, d)
    assert fake.n_ventana() == 2 and len(fake.llamadas) == 2
    assert {c[0] for c in fake.llamadas} == {"MOD021KM"}


def test_interruptor_apaga_la_ventana(monkeypatch):
    # A89: el interruptor se lee donde se usa (configurar_ventana), no se declara y se olvida
    dias = _dias(4)
    cat = {("MOD021KM", "6.1"): _noches("MOD021KM", dias)}
    fake = FakeCMR(cat)
    monkeypatch.setattr(fetch.earthaccess, "search_data", fake)
    monkeypatch.setenv("VRP_BUSQUEDA_VENTANA", "0")
    assert fetch.configurar_ventana(dias) is False
    for d in dias:
        fetch.search_granules("MODIS_TERRA_L1B", LAT, LON, R, d)
    assert fake.n_ventana() == 0 and len(fake.llamadas) == 4


# ---------------------------------------------------------------- fallas de la ventana

def test_ventana_que_falla_dos_veces_cae_al_camino_por_dia_y_se_apaga(monkeypatch):
    dias = _dias(4)
    cat = {("MOD021KM", "6.1"): _noches("MOD021KM", dias),
           ("MYD021KM", "6.1"): _noches("MYD021KM", dias)}

    def fallar(sn, ver, temporal):
        if temporal[0] != temporal[1]:
            raise RuntimeError('{"errors":["An Internal Error has occurred."]}')

    ref = _por_dia(FakeCMR(cat), monkeypatch, "MODIS_TERRA_L1B", dias)
    fake = FakeCMR(cat, fallar=fallar)
    assert _con_ventana(fake, monkeypatch, "MODIS_TERRA_L1B", dias) == ref
    assert fake.n_ventana() == 2  # un intento y un reintento
    # apagada para el resto del proceso: el producto siguiente ya no intenta la ventana
    for d in dias:
        fetch.search_granules("MODIS_AQUA_L1B", LAT, LON, R, d)
    assert fake.n_ventana() == 2
    assert fetch.fallas_de_cobertura() == []  # el camino por dia respondio: no se perdio nada


def test_ventana_que_falla_una_vez_se_reintenta(monkeypatch):
    dias = _dias(4)
    cat = {("MOD021KM", "6.1"): _noches("MOD021KM", dias)}
    estado = {"n": 0}

    def fallar(sn, ver, temporal):
        if temporal[0] != temporal[1] and estado["n"] == 0:
            estado["n"] += 1
            raise ReadTimeout("Read timed out")

    ref = _por_dia(FakeCMR(cat), monkeypatch, "MODIS_TERRA_L1B", dias)
    fake = FakeCMR(cat, fallar=fallar)
    assert _con_ventana(fake, monkeypatch, "MODIS_TERRA_L1B", dias) == ref
    assert len(fake.llamadas) == 2 and fake.n_ventana() == 2


def test_la_ventana_se_reintenta_una_vez_y_acota_el_costo_en_el_nrt():
    # A3 del plan: con CMR caido, la ventana agrega a lo mas un intento, una espera corta y un reintento antes de
    # volver al camino de hoy (dos timeouts de 60 s mas la espera: ~2,5 min en el NRT de 50 min).
    assert len(ESPERAS_PRODUCCION) == 2 and ESPERAS_PRODUCCION[0] == 0
    assert sum(ESPERAS_PRODUCCION) <= 30


def test_credencial_muerta_en_la_ventana_aborta(monkeypatch):
    def fallar(sn, ver, temporal):
        raise RuntimeError("Token expired: invalid_token")

    monkeypatch.setattr(fetch.earthaccess, "search_data", FakeCMR({}, fallar=fallar))
    fetch.configurar_ventana(_dias(3))
    with pytest.raises(fetch.EarthdataCredentialError):
        fetch.search_granules("MODIS_TERRA_L1B", LAT, LON, R, D0)


def test_dia_ya_en_la_ventana_se_sirve_con_el_cortacircuito_encendido(monkeypatch):
    dias = _dias(3)
    cat = {("MOD021KM", "6.1"): _noches("MOD021KM", dias)}
    out = _con_ventana(FakeCMR(cat), monkeypatch, "MODIS_TERRA_L1B", dias[:1])
    fetch._CMR_SEARCH_DOWN = True
    assert _urs(fetch.search_granules("MODIS_TERRA_L1B", LAT, LON, R, D0)) == out["2026-07-18"]
    assert fetch.fallas_de_cobertura() == []


# ---------------------------------------------------------------- cache en disco (segundo brazo)

def test_cache_en_disco_la_reusa_otro_proceso_sin_llamar_a_cmr(monkeypatch, tmp_path):
    dias = _dias(5)
    cat = {("MOD021KM", "6.1"): _noches("MOD021KM", dias)}
    fake = FakeCMR(cat)
    primero = _con_ventana(fake, monkeypatch, "MODIS_TERRA_L1B", dias, cache_dir=tmp_path)
    assert fake.n_ventana() == 1
    originales = {d.strftime("%Y-%m-%d"): fetch.search_granules("MODIS_TERRA_L1B", LAT, LON, R, d) for d in dias}

    def prohibido(*a, **k):
        raise AssertionError("el segundo brazo no debe llamar a CMR")

    fetch.reiniciar_ventana()  # otro proceso: la cache en memoria no existe
    monkeypatch.setattr(fetch.earthaccess, "search_data", prohibido)
    assert fetch.configurar_ventana(dias, cache_dir=tmp_path)
    for d in dias:
        k = d.strftime("%Y-%m-%d")
        otra = fetch.search_granules("MODIS_TERRA_L1B", LAT, LON, R, d)
        assert _urs(otra) == primero[k]
        assert [g["umm"] for g in otra] == [g["umm"] for g in originales[k]]
        assert [g.data_links() for g in otra] == [g.data_links() for g in originales[k]]
        assert [g.cloud_hosted for g in otra] == [g.cloud_hosted for g in originales[k]]


def test_ventana_fallida_no_deja_cache_en_disco(monkeypatch, tmp_path):
    def fallar(sn, ver, temporal):
        raise RuntimeError("HTTP 500")

    monkeypatch.setattr(fetch.earthaccess, "search_data", FakeCMR({}, fallar=fallar))
    fetch.configurar_ventana(_dias(3), cache_dir=tmp_path)
    with pytest.raises(RuntimeError):
        fetch.search_granules("MODIS_TERRA_L1B", LAT, LON, R, D0)  # camino por dia: propaga como hoy
    assert list(tmp_path.glob("*.json")) == []


# ---------------------------------------------------------------- cobertura: lo que no se pudo buscar ni bajar

VOLCAN = {"name": "NevadosDeChillan", "lat": LAT, "lon": LON, "radius_km": R, "sensors": ["MODIS"]}


def test_cobertura_registra_error_http_de_cmr(monkeypatch, tmp_path):
    monkeypatch.setattr(fetch, "auth", lambda: None)

    def fallar(sn, ver, temporal):
        raise RuntimeError('{"errors":["An Internal Error has occurred."]}')

    monkeypatch.setattr(fetch.earthaccess, "search_data", FakeCMR({}, fallar=fallar))
    out = fetch.fetch_for_volcano(VOLCAN, D0, tmp_path)
    assert out == {"MODIS_TERRA": [], "MODIS_AQUA": []}
    fallas = fetch.fallas_de_cobertura()
    assert {(f["plataforma"], f["etapa"]) for f in fallas} == {("MODIS_TERRA", "busqueda"),
                                                               ("MODIS_AQUA", "busqueda")}
    assert all(f["volcan"] == "NevadosDeChillan" and f["fecha"] == "2026-07-18" for f in fallas)


def test_cobertura_registra_cortacircuito_y_timeout(monkeypatch, tmp_path):
    monkeypatch.setattr(fetch, "auth", lambda: None)

    def fallar(sn, ver, temporal):
        raise ReadTimeout("Read timed out")

    monkeypatch.setattr(fetch.earthaccess, "search_data", FakeCMR({}, fallar=fallar))
    fetch.fetch_for_volcano(VOLCAN, D0, tmp_path)
    motivos = sorted(f["motivo"].split(":")[0] for f in fetch.fallas_de_cobertura())
    assert motivos == ["SEARCH_CMR_TIMEOUT", "SEARCH_SKIP"]


def test_cobertura_no_registra_un_dia_sin_granulos(monkeypatch, tmp_path):
    monkeypatch.setattr(fetch, "auth", lambda: None)
    monkeypatch.setattr(fetch.earthaccess, "search_data", FakeCMR({}))
    fetch.fetch_for_volcano(VOLCAN, D0, tmp_path)
    assert fetch.fallas_de_cobertura() == []


def test_cobertura_registra_descarga_fallida(monkeypatch, tmp_path):
    monkeypatch.setattr(fetch, "auth", lambda: None)
    noche = D0.replace(hour=6)  # de noche en Chillan
    cat = {("MOD021KM", "6.1"): [_g("MOD021KM.A", noche)], ("MOD03", "6.1"): [_g("MOD03.A", noche)]}
    monkeypatch.setattr(fetch.earthaccess, "search_data", FakeCMR(cat))

    def no_baja(granules, dest_dir):
        raise RuntimeError("download host(s) down this run")

    monkeypatch.setattr(fetch, "download_granules", no_baja)
    fetch.fetch_for_volcano(VOLCAN, D0, tmp_path)
    fallas = fetch.fallas_de_cobertura()
    assert [(f["plataforma"], f["etapa"]) for f in fallas] == [("MODIS_TERRA", "descarga")]
