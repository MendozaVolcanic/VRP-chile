"""S190 (auditoría de Codex, ronda 2, frente 6): una descarga vacía o parcial no es una descarga buena.

POR QUÉ existe este archivo. La pasada que no se baja no deja record, y un hueco en la serie de un volcán se lee en el
tablero como «noche sin anomalía». Tres defectos de la misma raíz, confirmados por el verificador Claude del frente 6
(`D:\\codex-vrp\\_salida\\ronda2\\f6_verificacion\\VEREDICTO.md`):

- F6-101: `earthaccess.download` puede devolver una lista vacía sin excepción (gránulo sin enlace GET DATA, o el
  almacén sin sesión; versión 0.17.0, la del runner). `download_granules` la devolvía como éxito: la pasada se perdía sin
  falla ni incidencia, y una falta parcial (el L1B sin su geolocalización) tampoco se veía.
- F6-V201: esa descarga vacía ponía `_DESCARGA_BUENA = True`, y con eso un token que LAADS rechaza con 403 en otra
  plataforma ya no abortaba la corrida (defensa S175): NRT verde sin datos.
- F6-102 (y F6-V202): el `try` envolvía el bucle de pares entero, así que una pasada que fallaba al bajar botaba las
  pasadas ya bajadas de esa plataforma y ni intentaba las siguientes.

La red no se toca: se reemplaza `earthaccess.download`, la frontera que `download_granules` llama, y `time.sleep` para no
esperar los reintentos. Las pruebas de control (descarga completa) pasan también antes del arreglo.
"""
from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

import pipeline.fetch as fetch

FECHA = datetime(2026, 11, 3)
AHORA = datetime(2026, 11, 10)
VOLCAN = {"name": "Lascar", "lat": -23.37, "lon": -67.73, "radius_km": 25, "sensors": ["MODIS"]}


def _granulo(producto: str, hhmm: str) -> dict:
    inicio = f"2026-11-03T{hhmm[:2]}:{hhmm[2:]}:00.000Z"
    return {"umm": {"GranuleUR": f"{producto}.A2026307.{hhmm}.061.NRT",
                    "TemporalExtent": {"RangeDateTime": {"BeginningDateTime": inicio}}}}


def _nombre(g: dict) -> str:
    return g["umm"]["GranuleUR"] + ".hdf"


class DescargaFalsa:
    """Imita earthaccess.download: escribe un archivo por gránulo, salvo los que se le pide omitir o hacer fallar."""

    def __init__(self, omitir=(), fallar=None):
        self.omitir = set(omitir)      # GranuleUR que «bajan» sin archivo (respuesta vacía de la biblioteca)
        self.fallar = fallar or {}     # GranuleUR -> excepción que levanta la biblioteca
        self.llamadas = 0

    def __call__(self, granulos, local_path):
        self.llamadas += 1
        rutas = []
        for g in granulos:
            ur = g["umm"]["GranuleUR"]
            if ur in self.fallar:
                raise self.fallar[ur]
            if ur in self.omitir:
                continue
            p = Path(local_path) / _nombre(g)
            p.write_bytes(b"HDF-FALSO")
            rutas.append(str(p))
        return rutas


@pytest.fixture(autouse=True)
def _aislado(monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda s: None)
    monkeypatch.setattr(fetch, "auth", lambda: None)
    fetch.limpiar_fallas()
    yield
    fetch.limpiar_fallas()


def _par(hhmm: str, mir="MOD021KM", geo="MOD03"):
    return [_granulo(mir, hhmm), _granulo(geo, hhmm)]


# ── download_granules ─────────────────────────────────────────────────────────────────────────────

def test_control_descarga_completa_devuelve_los_dos_archivos(monkeypatch, tmp_path):
    monkeypatch.setattr(fetch.earthaccess, "download", DescargaFalsa())
    rutas = fetch.download_granules(_par("0500"), tmp_path)
    assert sorted(p.name for p in rutas) == sorted(_nombre(g) for g in _par("0500"))


def test_f6_101_descarga_vacia_no_es_exito(monkeypatch, tmp_path):
    par = _par("0500")
    falsa = DescargaFalsa(omitir={g["umm"]["GranuleUR"] for g in par})
    monkeypatch.setattr(fetch.earthaccess, "download", falsa)
    with pytest.raises(RuntimeError, match="incompleta"):
        fetch.download_granules(par, tmp_path)
    assert falsa.llamadas > 1, "una respuesta vacía puede ser pasajera: se reintenta antes de fallar"


def test_f6_101_descarga_parcial_no_es_exito(monkeypatch, tmp_path):
    par = _par("0500")
    monkeypatch.setattr(fetch.earthaccess, "download", DescargaFalsa(omitir={par[1]["umm"]["GranuleUR"]}))
    with pytest.raises(RuntimeError, match="incompleta"):
        fetch.download_granules(par, tmp_path)


def test_f6_101_vacia_pasajera_se_recupera_en_el_reintento(monkeypatch, tmp_path):
    par = _par("0500")
    buena = DescargaFalsa()
    vacia = DescargaFalsa(omitir={g["umm"]["GranuleUR"] for g in par})
    secuencia = iter([vacia, buena])
    monkeypatch.setattr(fetch.earthaccess, "download", lambda gs, local_path: next(secuencia)(gs, local_path))
    assert len(fetch.download_granules(par, tmp_path)) == 2


# ── fetch_for_volcano ─────────────────────────────────────────────────────────────────────────────

def _buscar_con(pares_por_clave: dict):
    def buscar(clave, lat, lon, radius, date):
        return list(pares_por_clave.get(clave, []))
    return buscar


def _fetch(tmp_path):
    return fetch.fetch_for_volcano(VOLCAN, FECHA, tmp_path, nighttime_only=False, ahora=AHORA)


def test_f6_102_una_pasada_mala_no_bota_las_ya_bajadas(monkeypatch, tmp_path):
    a, b = _par("0500"), _par("0510")
    monkeypatch.setattr(fetch, "search_granules", _buscar_con({
        "MODIS_TERRA_L1B": [a[0], b[0]], "MODIS_TERRA_GEO": [a[1], b[1]]}))
    monkeypatch.setattr(fetch.earthaccess, "download",
                        DescargaFalsa(fallar={b[0]["umm"]["GranuleUR"]: RuntimeError("corte de lectura")}))
    res = _fetch(tmp_path)
    assert sorted(p.name for p in res["MODIS_TERRA"]) == sorted(_nombre(g) for g in a)
    fallas = [f for f in fetch.fallas_de_cobertura() if f["plataforma"] == "MODIS_TERRA"]
    assert [f["etapa"] for f in fallas] == ["descarga"]


def test_f6_v202_una_pasada_mala_no_impide_intentar_las_siguientes(monkeypatch, tmp_path):
    a, b = _par("0500"), _par("0510")
    monkeypatch.setattr(fetch, "search_granules", _buscar_con({
        "MODIS_TERRA_L1B": [a[0], b[0]], "MODIS_TERRA_GEO": [a[1], b[1]]}))
    monkeypatch.setattr(fetch.earthaccess, "download",
                        DescargaFalsa(fallar={a[0]["umm"]["GranuleUR"]: RuntimeError("corte de lectura")}))
    res = _fetch(tmp_path)
    assert sorted(p.name for p in res["MODIS_TERRA"]) == sorted(_nombre(g) for g in b)


def test_f6_101_descarga_vacia_en_la_corrida_queda_como_falla(monkeypatch, tmp_path):
    a = _par("0500")
    monkeypatch.setattr(fetch, "search_granules", _buscar_con({
        "MODIS_TERRA_L1B": [a[0]], "MODIS_TERRA_GEO": [a[1]]}))
    monkeypatch.setattr(fetch.earthaccess, "download", DescargaFalsa(omitir={g["umm"]["GranuleUR"] for g in a}))
    res = _fetch(tmp_path)
    assert res["MODIS_TERRA"] == []
    assert [(f["plataforma"], f["etapa"]) for f in fetch.fallas_de_cobertura()] == [("MODIS_TERRA", "descarga")]


def _rechazo_403():
    e = RuntimeError("Forbidden")
    e.response = SimpleNamespace(status_code=403)
    return e


def test_f6_v201_descarga_vacia_no_apaga_el_aborto_por_403(monkeypatch, tmp_path):
    terra, aqua = _par("0500"), _par("0640", "MYD021KM", "MYD03")
    monkeypatch.setattr(fetch, "search_granules", _buscar_con({
        "MODIS_TERRA_L1B": [terra[0]], "MODIS_TERRA_GEO": [terra[1]],
        "MODIS_AQUA_L1B": [aqua[0]], "MODIS_AQUA_GEO": [aqua[1]]}))
    monkeypatch.setattr(fetch.earthaccess, "download", DescargaFalsa(
        omitir={g["umm"]["GranuleUR"] for g in terra},
        fallar={aqua[0]["umm"]["GranuleUR"]: _rechazo_403()}))
    with pytest.raises(fetch.EarthdataCredentialError):
        _fetch(tmp_path)


def test_control_403_con_una_descarga_buena_no_aborta(monkeypatch, tmp_path):
    terra, aqua = _par("0500"), _par("0640", "MYD021KM", "MYD03")
    monkeypatch.setattr(fetch, "search_granules", _buscar_con({
        "MODIS_TERRA_L1B": [terra[0]], "MODIS_TERRA_GEO": [terra[1]],
        "MODIS_AQUA_L1B": [aqua[0]], "MODIS_AQUA_GEO": [aqua[1]]}))
    monkeypatch.setattr(fetch.earthaccess, "download", DescargaFalsa(
        fallar={aqua[0]["umm"]["GranuleUR"]: _rechazo_403()}))
    res = _fetch(tmp_path)
    assert len(res["MODIS_TERRA"]) == 2 and res["MODIS_AQUA"] == []
