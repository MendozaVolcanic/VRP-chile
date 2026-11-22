# -*- coding: utf-8 -*-
"""S193: la auditoría cuenta el día de MODIS sólo desde que producción lo procesa.

POR QUÉ (el fenómeno y el mecanismo). Producción enciende el día de MODIS (A/B #813, decisión de Nicolás del
2026-11-21) y la historia anterior NO se reprocesa de día: el NRT rellena sólo sus 7 días hacia atrás. Toda la
vigilancia (auditoría semanal, banco de paridad, clasificación de la referencia, vigilancias de guardia y sombra,
evaluador común) decide qué pasadas de MIROVA nos evalúan con `auto_audit_weekly.es_pasada_diurna_descartada`, que
seguía el flag sin mirar la fecha. Con el flag encendido, una alerta diurna de MIROVA de octubre (Chillán en erupción)
contaba como una pasada que miramos y no vimos: corrida el 2026-11-21 sobre los datos de ese día, la ventana de 60 días
bajaba el recall MODIS de 94,3 a 91,7 % y sumaba 16 pasadas sin record, sin que el detector cambiara en nada.

QUÉ FIJAN. (1) La frontera sale de los datos (el primer record MODIS diurno de la serie, con la regla de día de store),
no del merge (S155). (2) Antes de ella la pasada MODIS diurna se descarta como siempre; desde ella, cuenta. (3) Sin
ningún record diurno se descartan todas. (4) VIIRS y la noche no cambian. (5) El flag de MODIS se lee vivo (A89).
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pipeline.profile as prof  # noqa: E402
import scripts.auto_audit_weekly as aa  # noqa: E402

CHILLAN = "NevadosDeChillan"


def _dt(s):
    return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)


@pytest.fixture
def cache_limpio(monkeypatch):
    monkeypatch.setattr(aa, "_INICIO_DIA_MODIS", {})


def _coords():
    return aa._coords_por_volcan()[CHILLAN]


def _escribir(directorio, records):
    (directorio / f"{CHILLAN}.json").write_text(json.dumps({"records": records}), encoding="utf-8")


def test_la_frontera_es_el_primer_record_modis_diurno_de_la_serie(tmp_path, cache_limpio):
    # Chillán: 13:05 UTC es de día y 03:00 UTC de noche. El VIIRS diurno más temprano y la noche MODIS no cuentan.
    _escribir(tmp_path, [
        {"sensor": "MODIS_AQUA", "datetime_utc": "2026-11-10 03:00"},
        {"sensor": "VIIRS_NOAA20", "datetime_utc": "2026-11-12 18:00"},
        {"sensor": "MODIS_TERRA", "datetime_utc": "2026-11-16 13:05"},
        {"sensor": "MODIS_AQUA", "datetime_utc": "2026-11-15 19:00"},
    ])
    assert aa.inicio_dia_modis(str(tmp_path)) == _dt("2026-11-15T19:00:00")


def test_sin_records_diurnos_no_hay_frontera(tmp_path, cache_limpio):
    _escribir(tmp_path, [{"sensor": "MODIS_AQUA", "datetime_utc": "2026-11-10 03:00"}])
    assert aa.inicio_dia_modis(str(tmp_path)) is None


def test_el_dia_de_modis_cuenta_solo_desde_la_frontera(cache_limpio):
    lat, lon = _coords()
    aa.fijar_inicio_dia_modis(_dt("2026-11-15T00:00:00"))
    with patch.object(prof, "ENABLE_DAYTIME_MODIS", True), patch.object(prof, "ENABLE_DAYTIME_VIIRS", False):
        # 2026-10-14 13:05: alerta diurna real de MIROVA (6,98 MW), anterior al encendido: no nos evalúa
        assert aa.es_pasada_diurna_descartada("MODIS", lat, lon, _dt("2026-10-14T13:05:00")) is True
        # la misma hora después de la frontera sí nos evalúa
        assert aa.es_pasada_diurna_descartada("MODIS", lat, lon, _dt("2026-11-16T13:05:00")) is False
        # fecha sin zona: se lee como UTC, igual que la de los records
        assert aa.es_pasada_diurna_descartada("MODIS", lat, lon, datetime(2026, 11, 16, 13, 5)) is False
        # VIIRS sigue a su propio flag, apagado
        assert aa.es_pasada_diurna_descartada("VIIRS375", lat, lon, _dt("2026-11-16T18:00:00")) is True
        # la noche nunca se descarta, antes o después
        for ts in ("2026-10-14T03:00:00", "2026-11-16T03:00:00"):
            assert aa.es_pasada_diurna_descartada("MODIS", lat, lon, _dt(ts)) is False


def test_sin_frontera_se_descarta_todo_el_dia_de_modis(cache_limpio):
    lat, lon = _coords()
    aa.fijar_inicio_dia_modis(None)
    with patch.object(prof, "ENABLE_DAYTIME_MODIS", True):
        assert aa.es_pasada_diurna_descartada("MODIS", lat, lon, _dt("2026-11-16T13:05:00")) is True


def test_con_el_flag_apagado_la_frontera_no_abre_nada(cache_limpio):
    lat, lon = _coords()
    aa.fijar_inicio_dia_modis(_dt("2026-01-01T00:00:00"))
    with patch.object(prof, "ENABLE_DAYTIME_MODIS", False):
        assert aa.es_pasada_diurna_descartada("MODIS", lat, lon, _dt("2026-11-16T13:05:00")) is True


def test_la_frontera_por_defecto_es_la_serie_del_perfil_activo(tmp_path, cache_limpio, monkeypatch):
    """El directorio por defecto es data/<DATA_SUBDIR>/ del perfil activo, no una ruta fija."""
    datos = tmp_path / "data" / "serie_de_prueba"
    datos.mkdir(parents=True)
    _escribir(datos, [{"sensor": "MODIS_TERRA", "datetime_utc": "2026-11-16 13:05"}])
    monkeypatch.setattr(aa, "ROOT", str(tmp_path))
    monkeypatch.setattr(prof, "DATA_SUBDIR", "serie_de_prueba")
    assert aa.inicio_dia_modis() == _dt("2026-11-16T13:05:00")
