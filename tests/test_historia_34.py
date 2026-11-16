# tests/test_historia_34.py
# -*- coding: utf-8 -*-
"""Reglas de experiments/_historia_34/aplicar_historia_34.py (historia de los 34 con la vía)."""
import gzip
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments" / "_historia_34"))
import aplicar_historia_34 as A  # noqa: E402


def _r(dt, sensor="VIIRS_NOAA20", via=True, perfil="_s172_retro_paquete", vrp=0.0):
    return {"datetime_utc": dt, "sensor": sensor, "via_codigo_mirova": via, "vrp_mw": vrp,
            "regimen": {"perfil": perfil}}


def _union(tmp_path, v, recs):
    d = tmp_path / "union"
    d.mkdir(exist_ok=True)
    (d / f"{v}.json.gz").write_bytes(gzip.compress(json.dumps({"volcano": v, "records": recs}).encode()))
    return d


def test_escribe_solo_lo_anterior_al_corte(tmp_path):
    u = _union(tmp_path, "Calbuco", [_r("2026-11-02 23:59"), _r("2026-11-03 00:00"), _r("2025-02-15 05:00")])
    inf = A.aplicar(u, tmp_path / "hist", aplicar=True)
    s = json.loads((tmp_path / "hist" / "Calbuco.json").read_text(encoding="utf-8"))
    assert [r["datetime_utc"] for r in s["records"]] == ["2025-02-15 05:00", "2026-11-02 23:59"]
    assert s["hasta_utc"] == A.CORTE and inf["Calbuco"]["tras_corte"] == 1


def test_rehusa_caida_a_k_y_otro_perfil(tmp_path):
    for malo in (_r("2025-03-01 05:00", via="sin_grilla"), _r("2025-03-01 05:00", perfil="_s172_retro_k")):
        u = _union(tmp_path, "Calbuco", [malo])
        with pytest.raises(A.Rehusado):
            A.aplicar(u, tmp_path / "hist", aplicar=True)
    assert not (tmp_path / "hist").exists()


def test_rehusa_un_volcan_de_los_11(tmp_path):
    u = _union(tmp_path, "Lascar", [_r("2025-03-01 05:00")])
    with pytest.raises(A.Rehusado):
        A.aplicar(u, tmp_path / "hist", aplicar=True)


def test_ensayo_no_escribe(tmp_path):
    u = _union(tmp_path, "Calbuco", [_r("2025-03-01 05:00")])
    inf = A.aplicar(u, tmp_path / "hist", aplicar=False)
    assert inf["Calbuco"]["nuevos"] == 1 and not (tmp_path / "hist").exists()


def test_una_tanda_repetida_no_duplica_y_gana_lo_que_estaba(tmp_path):
    u = _union(tmp_path, "Calbuco", [_r("2025-03-01 05:00", vrp=1.0)])
    A.aplicar(u, tmp_path / "hist", aplicar=True)
    u = _union(tmp_path, "Calbuco", [_r("2025-03-01 05:00", vrp=9.0), _r("2025-03-02 05:00")])
    inf = A.aplicar(u, tmp_path / "hist", aplicar=True)
    s = json.loads((tmp_path / "hist" / "Calbuco.json").read_text(encoding="utf-8"))
    assert [r["vrp_mw"] for r in s["records"]] == [1.0, 0.0] and inf["Calbuco"]["ya_estaban"] == 1


def test_orden_cronologico_y_sin_claves_repetidas(tmp_path):
    u = _union(tmp_path, "Calbuco", [_r("2025-03-02 05:00"), _r("2025-03-01 05:00"),
                                     _r("2025-03-01 05:00", "MODIS_AQUA")])
    A.aplicar(u, tmp_path / "hist", aplicar=True)
    s = json.loads((tmp_path / "hist" / "Calbuco.json").read_text(encoding="utf-8"))
    fechas = [r["datetime_utc"] for r in s["records"]]
    assert fechas == sorted(fechas) and len(s["records"]) == 3


DATOS = ROOT / "data" / "historia_34"


@pytest.mark.skipif(not DATOS.exists(), reason="sin historia aplicada todavía")
def test_historia_publicada_es_toda_de_la_via_y_anterior_a_la_sombra():
    for f in sorted(DATOS.glob("*.json")):
        s = json.loads(f.read_text(encoding="utf-8"))
        assert f.stem in A.LOS_34 and s["volcano"] == f.stem
        recs = s["records"]
        assert all(r.get("via_codigo_mirova") is True for r in recs), f.stem
        assert all(A._minuto(r["datetime_utc"]) < A.CORTE for r in recs), f.stem
        claves = [A._clave(r) for r in recs]
        assert len(claves) == len(set(claves)), f.stem
