"""S161: el NRT ante el cese de Suomi NPP (2026-11-02 13:00 UTC). Hallazgo 241 de la auditoría S160
(docs/AUDIT_S160.md §2 y decisión 3 de §5) y recomendaciones 6 y 7 del frente S159
(experiments/_s159/cese_snpp/INFORME.md, rama `s159-pruebas`).

POR QUÉ. Cuando un satélite deja de entregar, CMR devuelve cero gránulos y `pipeline/fetch.py` lo vive
igual que una noche en que el satélite no pasó: no registra falla, y `run_pipeline.informar_cobertura`
imprime «Cobertura: completa» y sale 0. Con el cese de Suomi NPP eso mentiría en cada corrida del NRT, y el
mismo hueco dejaría pasar en silencio la muerte no anunciada de NOAA-20, NOAA-21, Terra o Aqua. Dos cosas:
(1) para un día entero posterior a un cese anunciado (scripts/ceses_esperados.json, la misma lista que lee la
vigilancia de #892) la plataforma no se busca, y se dice; (2) una plataforma que no dio ningún gránulo en
toda la corrida no deja decir «completa».

Las pruebas pasan por la vía pública que ya existía antes del cambio (`fetch.fetch_for_volcano` y
`run_pipeline.main` reales, con la red simulada), para que antes del cambio fallen por aserción y no por un
nombre que todavía no existe. Las de control (día del cese, reproceso histórico, todo vivo) pasan antes y
después: muestran que el instrumento puede dar el resultado contrario.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

RAIZ = Path(__file__).parent.parent
_spec = importlib.util.spec_from_file_location("run_pipeline_s161", RAIZ / "scripts" / "run_pipeline.py")
rp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rp)
fetch = rp.fetch

SNPP_L1B = ("VIIRS_SNPP_L1B", "VIIRS_SNPP_MOD_L1B")
OTRAS_L1B = ("MODIS_TERRA_L1B", "MODIS_AQUA_L1B", "VIIRS_NOAA20_L1B", "VIIRS_NOAA21_L1B",
             "VIIRS_NOAA20_MOD_L1B", "VIIRS_NOAA21_MOD_L1B")
VOLCAN = {"name": "Lascar", "lat": -23.37, "lon": -67.73, "radius_km": 25}


def _cese_snpp() -> datetime:
    """Instante del cese según la lista versionada de #892 (no una fecha copiada en la prueba)."""
    ceses = json.loads((RAIZ / "scripts" / "ceses_esperados.json").read_text(encoding="utf-8"))["ceses"]
    snpp = [c for c in ceses if set(c["sensores"]) == {"VIIRS_SNPP", "VIIRS_SNPP_750"}]
    assert len(snpp) == 1, "la lista de ceses no trae a Suomi NPP"
    return datetime.strptime(snpp[0]["desde_utc"], "%Y-%m-%dT%H:%M:%SZ")


CESE = _cese_snpp()
DIA_DEL_CESE = datetime(CESE.year, CESE.month, CESE.day)
DIA_SIGUIENTE = DIA_DEL_CESE + timedelta(days=1)
ANTES = DIA_DEL_CESE - timedelta(days=8)


def _red_prohibida(*a, **k):
    raise AssertionError("una prueba no puede tocar NASA (ni auth con el netrc local, A71)")


@pytest.fixture(autouse=True)
def _limpio(monkeypatch):
    monkeypatch.setattr(fetch.earthaccess, "login", _red_prohibida)
    monkeypatch.setattr(fetch.earthaccess, "search_data", _red_prohibida)
    monkeypatch.setattr(fetch.earthaccess, "download", _red_prohibida)
    monkeypatch.setattr(fetch, "auth", lambda: None)
    # S163 (port de I1 de #889): estas pruebas simulan el día siguiente al cese, que hoy está en el futuro, y el
    # control «completa» usa ANTES (ocho días antes del cese), que fue «hoy» hace poco. Con I1 un día sin terminar más
    # la latencia de LANCE es «día parcial» y cuenta en modo estricto, así que su resultado pasaría a depender del
    # reloj. Acá se mide el cese y la plataforma muda, no el reloj: el día parcial lo prueba
    # tests/test_cobertura_incidencias_s159.py.
    monkeypatch.setattr(fetch, "dia_incompleto", lambda date, ahora=None: False)
    monkeypatch.setenv("VRP_BUSQUEDA_VENTANA", "0")
    for v in ("VRP_VENTANA_BUSQUEDA", "VRP_CACHE_BUSQUEDA_DIR", "GITHUB_STEP_SUMMARY", "GITHUB_ACTIONS"):
        monkeypatch.delenv(v, raising=False)
    fetch.reiniciar_ventana()
    fetch.limpiar_fallas()
    yield
    fetch.reiniciar_ventana()
    fetch.limpiar_fallas()


class _CMR:
    """Simula CMR: un gránulo por producto, salvo las plataformas mudas (cero) o caídas (excepción)."""

    def __init__(self, mudas=(), caidas=()):
        self.mudas, self.caidas, self.pedidos = tuple(mudas), tuple(caidas), []

    def __call__(self, product_key, lat, lon, radius_km, date):
        self.pedidos.append(product_key)
        if product_key.startswith(self.caidas):
            raise RuntimeError("HTTP 500 simulado")
        if product_key.startswith(self.mudas):
            return []
        t = f"{date:%Y-%m-%d}T05:30:00.000Z"
        return [{"umm": {"TemporalExtent": {"RangeDateTime": {"BeginningDateTime": t}}}}]


def _instalar(monkeypatch, cmr):
    monkeypatch.setattr(fetch, "search_granules", cmr)
    monkeypatch.setattr(fetch, "_filter_nighttime_granules", lambda g, lat, lon: g)
    monkeypatch.setattr(fetch, "download_granules", lambda granulos, destino: [])


def _correr_main(monkeypatch, tmp_path, cmr, fecha, extra=()):
    """run_pipeline.main real; process_date sólo llama al fetch real (nada que procesar ni escribir)."""
    _instalar(monkeypatch, cmr)
    monkeypatch.setattr(rp, "process_date",
                        lambda volcano, date, **kw: fetch.fetch_for_volcano(volcano, date, tmp_path / "g"))
    ruta = tmp_path / "cobertura.json"
    monkeypatch.setattr(sys, "argv", ["run_pipeline.py", "--volcano", "Lascar", "--date", f"{fecha:%Y-%m-%d}",
                                      "--cobertura-json", str(ruta), *extra])
    with pytest.raises(SystemExit) as e:
        rp.main()
    return e.value.code, json.loads(ruta.read_text(encoding="utf-8"))


# ------------------------------------------------------------------ (1) no buscar lo que no va a existir

def test_tras_el_cese_no_se_busca_suomi_npp(monkeypatch, tmp_path):
    cmr = _CMR()
    _instalar(monkeypatch, cmr)
    fetch.fetch_for_volcano(VOLCAN, DIA_SIGUIENTE, tmp_path)
    pedidas = [k for k in SNPP_L1B if k in cmr.pedidos]
    assert not pedidas, f"el {DIA_SIGUIENTE:%Y-%m-%d} se siguió buscando Suomi NPP: {pedidas}"
    faltan = [k for k in OTRAS_L1B if k not in cmr.pedidos]
    assert not faltan, f"el cese de Suomi NPP apagó otras plataformas: {faltan}"


def test_el_dia_del_cese_si_se_busca_suomi_npp(monkeypatch, tmp_path):
    """Control: las pasadas nocturnas del día del cese (04:54 a 07:06 UTC) son anteriores a las 13:00."""
    cmr = _CMR()
    _instalar(monkeypatch, cmr)
    fetch.fetch_for_volcano(VOLCAN, DIA_DEL_CESE, tmp_path)
    assert all(k in cmr.pedidos for k in SNPP_L1B), cmr.pedidos


def test_un_reproceso_anterior_al_cese_si_busca_suomi_npp(monkeypatch, tmp_path):
    """Control: el archivo histórico de Suomi NPP sigue disponible (LAADS 199516)."""
    cmr = _CMR()
    _instalar(monkeypatch, cmr)
    fetch.fetch_for_volcano(VOLCAN, ANTES, tmp_path)
    assert all(k in cmr.pedidos for k in SNPP_L1B), cmr.pedidos


def test_sin_la_lista_de_ceses_se_busca_todo(monkeypatch, tmp_path):
    """Si la lista no se puede leer, el NRT vuelve al comportamiento anterior (buscar todo), no a callar."""
    monkeypatch.setattr(fetch, "_RUTA_CESES", tmp_path / "no_existe.json", raising=False)
    monkeypatch.setattr(fetch, "_CESES", None, raising=False)
    cmr = _CMR()
    _instalar(monkeypatch, cmr)
    fetch.fetch_for_volcano(VOLCAN, DIA_SIGUIENTE, tmp_path)
    assert all(k in cmr.pedidos for k in SNPP_L1B), cmr.pedidos


# ------------------------------------------------------------------ (2) no decir «completa» si falta una plataforma

def test_todo_vivo_dice_completa(monkeypatch, tmp_path, capsys):
    """Control nulo: con todas las plataformas entregando, el mensaje sigue siendo «completa»."""
    cod, cob = _correr_main(monkeypatch, tmp_path, _CMR(), ANTES)
    assert "Cobertura: completa" in capsys.readouterr().out
    assert cod in (0, None) and cob["fallas"] == []


def test_una_plataforma_muda_en_toda_la_corrida_no_es_completa(monkeypatch, tmp_path, capsys):
    """Hallazgo 241: Suomi NPP (o cualquier otra) devuelve cero gránulos antes de su cese."""
    cod, cob = _correr_main(monkeypatch, tmp_path, _CMR(mudas=("VIIRS_SNPP",)), ANTES)
    out = capsys.readouterr().out
    assert "Cobertura: completa" not in out, out
    assert "VIIRS_SNPP" in out and "VIIRS_SNPP_750" in out, out
    assert sorted(cob.get("sin_granulos", [])) == ["VIIRS_SNPP", "VIIRS_SNPP_750"], cob
    assert cod in (0, None), "una nota de cobertura no cambia el código de salida del NRT"


def test_tras_el_cese_el_mensaje_nombra_a_suomi_npp_y_no_dice_completa(monkeypatch, tmp_path, capsys):
    cod, cob = _correr_main(monkeypatch, tmp_path, _CMR(mudas=("VIIRS_SNPP",)), DIA_SIGUIENTE)
    out = capsys.readouterr().out
    assert "Cobertura: completa" not in out, out
    assert "cese anunciado" in out and "VIIRS_SNPP" in out, out
    assert sorted(cob.get("retiradas", [])) == ["VIIRS_SNPP", "VIIRS_SNPP_750"], cob
    assert cob.get("sin_granulos") == [], "una plataforma retirada no se cuenta además como muda"
    assert cod in (0, None)


def test_tras_el_cese_el_modo_estricto_no_falla_por_el_retiro(monkeypatch, tmp_path, capsys):
    """Un reproceso que cruza el 2-nov no debe quedar rojo por un cese anunciado."""
    cod, _ = _correr_main(monkeypatch, tmp_path, _CMR(mudas=("VIIRS_SNPP",)), DIA_SIGUIENTE,
                          extra=("--estricto-cobertura",))
    assert cod in (0, None)


def test_una_busqueda_caida_es_falla_y_no_plataforma_muda(monkeypatch, tmp_path, capsys):
    """Una búsqueda que falló ya va como falla de cobertura; no se cuenta otra vez como «sin gránulos»."""
    cod, cob = _correr_main(monkeypatch, tmp_path, _CMR(caidas=("VIIRS_NOAA21",)), ANTES)
    out = capsys.readouterr().out
    assert "Cobertura INCOMPLETA" in out, out
    assert not any(p.startswith("VIIRS_NOAA21") for p in cob.get("sin_granulos", [])), cob
