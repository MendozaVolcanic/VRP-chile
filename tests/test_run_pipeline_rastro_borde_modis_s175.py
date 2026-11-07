# -*- coding: utf-8 -*-
"""S175 (hallazgo 153 de docs/AUDIT_S175.md): el gránulo MODIS que no deja record deja una línea en el log del NRT.

POR QUÉ, COMO GEÓLOGO. Al borde del barrido el píxel de MODIS mide varios kilómetros y la grilla de 1 km de MIROVA
queda con pocas celdas, o con la celda más cercana lejos del cráter; la vía «código MIROVA» devuelve nada y la pasada
desaparece de producción (171-01). Caso de campo: Villarrica MODIS_AQUA 2026-11-04 07:10 UTC, cenit 65°, escrita por la
guardia K y ausente de producción, con el job del NRT y su revisión de log en verde. Para el operador una pasada que
no existe se ve igual que una noche sin pasada. `scripts/run_pipeline.py` tenía `if result:` sin `else`.

QUÉ NO HACE. No distingue el descarte de borde de la vía del volcán fuera del gránulo: eso lo sabe sólo
`pipeline/process_modis.py` (A45, pendiente). Tampoco registra una incidencia de cobertura: el tipo nuevo vive en
`pipeline/fetch.py` (TIPOS_INCIDENCIA), fuera del alcance de este cambio.

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) Sin record y sin aviso del procesador, la línea sale. (2) Controles: con record
no sale, y si el procesador ya avisó (cráter sin posición, que sí registra incidencia) no se duplica.
"""
import sys
from datetime import datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import scripts.run_pipeline as rp  # noqa: E402

L1B = "MYD021KM.A2026308.0710.061.2026308191510.hdf"
GEO = "MYD03.A2026308.0710.061.2026308185000.hdf"
VOLCAN = {"name": "Villarrica", "display_name": "Villarrica", "lat": -39.42, "lon": -71.93, "radius_km": 25,
          "inner_radius_km": 5}


@pytest.fixture
def correr(monkeypatch, tmp_path, capsys):
    def _correr(calcular, flag=True):
        d = tmp_path / "g"
        d.mkdir(exist_ok=True)
        for n in (L1B, GEO):
            (d / n).write_bytes(b"")
        monkeypatch.setattr(rp, "TMP_DIR", tmp_path / "tmp")
        monkeypatch.setattr(rp.fetch, "fetch_for_volcano", lambda *a, **k: {"MODIS_AQUA": [d / L1B, d / GEO]})
        monkeypatch.setattr(rp.process_modis, "calculate_vrp", calcular)
        monkeypatch.setattr(rp.store, "append_record", lambda *a, **k: None)
        monkeypatch.setattr(rp.vrp_profile, "ENABLE_MODIS_CODIGO_MIROVA", flag, raising=False)
        rp.process_date(VOLCAN, datetime(2026, 11, 4), nighttime_only=False)
        return capsys.readouterr().out
    return _correr


def test_granulo_modis_sin_record_deja_linea_en_el_log(correr):
    out = correr(lambda *a, **k: None)
    linea = [x for x in out.splitlines() if L1B in x]
    assert linea and "sin record" in linea[0] and "171-01" in linea[0], out


def test_con_la_via_apagada_la_linea_no_culpa_a_la_via(correr):
    out = correr(lambda *a, **k: None, flag=False)
    linea = [x for x in out.splitlines() if L1B in x]
    assert linea and "sin record" in linea[0] and "171-01" not in linea[0], out


def test_control_con_record_no_hay_linea(correr):
    rec = {"sensor": "MODIS_AQUA", "vrp_mw": 0.0, "t_bg_k": 263.0, "t_max_k": 270.0, "n_anomalous_pixels": 0}
    out = correr(lambda *a, **k: rec)
    assert not any("sin record" in x for x in out.splitlines()), out


def test_control_si_el_procesador_ya_aviso_no_se_duplica(correr):
    def calcular(*a, al_sin_dato=None, **k):
        al_sin_dato("cráter sin posición en el gránulo")
        return None
    out = correr(calcular)
    assert not any("sin record" in x for x in out.splitlines()), out
