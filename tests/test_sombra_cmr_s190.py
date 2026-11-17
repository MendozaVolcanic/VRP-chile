"""S190: por qué las dos sombras salieron rojas el 2026-11-16 (issues #1027 y #1028) y qué se arregla.

Diagnóstico completo: experiments/_s190_sombras/DIAGNOSTICO.md. Dos defectos propios, los dos fijados aquí:

1. pipeline/fetch.py::search_granules encendía el breaker de CMR al PRIMER ReadTimeout de la búsqueda por día (S116) y
   todas las búsquedas siguientes de esa fecha devolvían [] sin preguntar. La búsqueda por ventana (S157) sí reintenta
   una vez a los 20 s, y el 2026-11-16 esos reintentos salvaron 3 de 3 ReadTimeout; la búsqueda por día no tenía
   reintento y perdió el último día entero de Tupungatito y los VIIRS de Putana y SanJose. A64: ReadTimeout se
   reintenta, ConnectTimeout no. Ahora un ReadTimeout se reintenta UNA vez (mismo producto y versión) antes de
   encender el breaker; ConnectTimeout y ConnectionError lo encienden al primero, como antes. El costo extra está
   acotado a un reintento por fecha (el breaker se enciende si el reintento también falla), lo que conserva la
   garantía de S116 contra el cuelgue de 50 min de Copahue.

2. scripts/revisar_sombra.py dejaba ROJO por una búsqueda fallida del día `fin` aunque ese día no se juzgara porque
   su noche no estaba cerrada al inicio de la corrida (S178). El cron atrasado 8 a 9 h hace que la corrida cruce la
   medianoche UTC: PlanchonPeteroa y NevadosDeChillan quedaron rojos el 2026-11-16 sólo por búsquedas del 2026-11-17,
   un día que la misma revisión declaraba «no se juzga». Ahora la falla de búsqueda deja rojo sólo si es del último
   día JUZGADO (o sin fecha); la de un día sin noche cerrada va como NOTA y la juzga la corrida siguiente.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from requests.exceptions import ConnectTimeout, ReadTimeout

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))

import pipeline.fetch as fetch  # noqa: E402
import test_revisar_sombra_corrida_s169 as T  # noqa: E402  (mismos ayudantes que la batería de S169)

PKEY = "MODIS_TERRA_L1B"


# ------------------------------------------------------------------ 1. reintento de ReadTimeout en la búsqueda por día

@pytest.fixture
def cmr(monkeypatch):
    fetch._CMR_SEARCH_DOWN = False
    monkeypatch.setattr(fetch, "ENABLE_CMR_SEARCH_BREAKER", True)
    monkeypatch.setattr(fetch, "_CMR_DIA_ESPERAS_S", [0, 0])   # sin esperar 20 s en la prueba
    monkeypatch.setattr(fetch, "_VENTANA", None)              # búsqueda por día, sin ventana
    yield
    fetch._CMR_SEARCH_DOWN = False


def _secuencia(monkeypatch, *efectos):
    """search_data que da, en orden, cada efecto (excepción que lanza o lista que devuelve)."""
    llamadas = []

    def falso(*a, **k):
        llamadas.append(k.get("short_name"))
        e = efectos[min(len(llamadas), len(efectos)) - 1]
        if isinstance(e, BaseException):
            raise e
        return e

    monkeypatch.setattr(fetch.earthaccess, "search_data", falso)
    return llamadas


def test_un_read_timeout_aislado_se_reintenta_y_no_enciende_el_breaker(cmr, monkeypatch):
    llamadas = _secuencia(monkeypatch, ReadTimeout("Read timed out"), ["granulo"])
    out = fetch.search_granules(PKEY, -35.2, -70.6, 25.0, fetch.datetime(2026, 11, 16))
    assert out == ["granulo"], out
    assert fetch._CMR_SEARCH_DOWN is False, "un ReadTimeout que se cura al reintentar no debe apagar CMR la fecha entera"
    assert len(llamadas) == 2 and llamadas[0] == llamadas[1], f"el reintento es del mismo producto: {llamadas}"


def test_dos_read_timeout_seguidos_encienden_el_breaker(cmr, monkeypatch):
    llamadas = _secuencia(monkeypatch, ReadTimeout("Read timed out"))
    out = fetch.search_granules(PKEY, -35.2, -70.6, 25.0, fetch.datetime(2026, 11, 16))
    assert out == [] and fetch._CMR_SEARCH_DOWN is True
    assert len(llamadas) == 2, f"un solo reintento, no uno por versión: {llamadas}"


def test_connect_timeout_no_se_reintenta(cmr, monkeypatch):
    """A64: ConnectTimeout no se cura reintentando; enciende el breaker al primero, como en S116."""
    llamadas = _secuencia(monkeypatch, ConnectTimeout("Connect timed out"), ["granulo"])
    out = fetch.search_granules(PKEY, -35.2, -70.6, 25.0, fetch.datetime(2026, 11, 16))
    assert out == [] and fetch._CMR_SEARCH_DOWN is True
    assert len(llamadas) == 1, llamadas


def test_la_espera_real_del_reintento_es_la_de_la_ventana():
    """Mismo reintento que la búsqueda por ventana (S157), que el 2026-11-16 salvó 3 de 3 ReadTimeout."""
    assert fetch._CMR_DIA_ESPERAS_S == fetch._VENTANA_ESPERAS_S == [0, 20]


# ------------------------------------------------------------------ 2. revisor: falla de búsqueda de un día no juzgado

def test_falla_de_busqueda_de_un_dia_sin_noche_cerrada_es_nota(tmp_path):
    """Corrida del 5 atrasada que arranca el 6 a las 00:30 UTC: el 6 no se juzga; sus búsquedas caídas tampoco."""
    rc, out = T.juzgar(tmp_path, 6, T.historial(3, 5), cob=T.cobertura(6, fallas=3, dia_fallas=6),
                       inicio="2026-11-06T00:30:00Z")
    assert rc == 0, out
    assert any(ln.strip().startswith("NOTA") and "2026-11-06" in ln and "búsquedas" in ln for ln in out.splitlines()), out


def test_falla_de_busqueda_del_ultimo_dia_juzgado_sigue_siendo_falla(tmp_path):
    """Misma corrida, pero la búsqueda caída es del 5, la última noche que sí se juzga: rojo, como VV169-03 con `fin`."""
    rc, out = T.juzgar(tmp_path, 6, T.historial(3, 5), cob=T.cobertura(6, fallas=1, dia_fallas=5),
                       inicio="2026-11-06T00:30:00Z")
    assert rc != 0 and "búsquedas o descargas fallidas del 2026-11-05" in out, out
