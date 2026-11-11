# -*- coding: utf-8 -*-
"""S180: reglas de experiments/_s180_reemplazo_via/unir_trozos.py (unión de los trozos de la vía).

POR QUÉ. La unión decide qué records de la vía entran a la serie publicada: un trozo viejo en vez del relanzado, una
pasada de borde contada dos veces o un record de otro perfil se publicarían como historia (S174: todo analizador que
decide algo va envuelto en tests/). Cada prueba fija una regla con su caso que falla.
"""
import gzip
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments" / "_s180_reemplazo_via"))
import unir_trozos as U  # noqa: E402


def _r(dt, sensor="VIIRS_NOAA20", perfil=U.PERFIL, **kw):
    r = {"datetime_utc": dt, "sensor": sensor, "via_codigo_mirova": True, "regimen": {"perfil": perfil}}
    r.update(kw)
    return r


def _trozo(base, v, i, a, b, n, recs):
    d = base / f"trozo-{v}-{i}-{a}_{b}-intento-{n}"
    d.mkdir(parents=True)
    (d / f"{v}.json").write_text(json.dumps({"volcano": v, "records": recs}), encoding="utf-8")


def test_usa_el_intento_mas_alto_y_filtra_por_ventana(tmp_path):
    run = tmp_path / "D2"
    _trozo(run, "Lascar", 1, "2026-02-01", "2026-02-10", 1, [_r("2026-02-02 05:00", vrp_mw=1.0)])
    _trozo(run, "Lascar", 1, "2026-02-01", "2026-02-10", 2, [_r("2026-02-02 05:00", vrp_mw=2.0),
                                                              _r("2026-02-11 05:00")])
    stores, inf = U.unir([run])
    assert [r["vrp_mw"] for r in stores["Lascar"]["records"]] == [2.0]
    assert inf["volcanes"]["Lascar"]["fuera_de_ventana"] == 1
    assert inf["volcanes"]["Lascar"]["intentos_mayores_a_1"] == [["2026-02-01", "2026-02-10", 2, "D2"]]


def test_une_despachos_y_reporta_huecos_de_calendario(tmp_path):
    _trozo(tmp_path / "D2", "Lascar", 1, "2026-02-01", "2026-02-10", 1, [_r("2026-02-02 05:00")])
    _trozo(tmp_path / "P4", "Lascar", 1, "2026-02-12", "2026-02-20", 1, [_r("2026-02-15 05:00", "MODIS_AQUA")])
    stores, inf = U.unir([tmp_path / "D2", tmp_path / "P4"])
    i = inf["volcanes"]["Lascar"]
    assert i["huecos"] == ["2026-02-11"] and i["dias"] == 19 and i["records"] == 2
    assert i["marcas"] == {"MODIS:true": 1, "VIIRS375:true": 1}


def test_rehusa_clave_repetida_entre_trozos(tmp_path):
    _trozo(tmp_path / "D2", "Lascar", 1, "2026-02-01", "2026-02-10", 1, [_r("2026-02-05 05:00")])
    _trozo(tmp_path / "P4", "Lascar", 1, "2026-02-05", "2026-02-12", 1, [_r("2026-02-05 05:00")])
    with pytest.raises(U.Rehusado):
        U.unir([tmp_path / "D2", tmp_path / "P4"])


def test_rehusa_record_de_otro_perfil(tmp_path):
    _trozo(tmp_path / "D2", "Lascar", 1, "2026-02-01", "2026-02-10", 1, [_r("2026-02-05 05:00", perfil="_s172_retro_k")])
    with pytest.raises(U.Rehusado):
        U.unir([tmp_path / "D2"])


def test_rehusa_el_mismo_trozo_en_dos_despachos(tmp_path):
    _trozo(tmp_path / "D2", "Lascar", 1, "2026-02-01", "2026-02-10", 1, [])
    _trozo(tmp_path / "P4", "Lascar", 1, "2026-02-01", "2026-02-10", 2, [])
    with pytest.raises(U.Rehusado):
        U.unir([tmp_path / "D2", tmp_path / "P4"])


def test_gz_reproducible_y_legible(tmp_path):
    s = {"volcano": "Lascar", "records": [_r("2026-02-05 05:00")]}
    U.escribir_gz(tmp_path / "a.json.gz", s)
    U.escribir_gz(tmp_path / "b.json.gz", s)
    assert (tmp_path / "a.json.gz").read_bytes() == (tmp_path / "b.json.gz").read_bytes()
    assert json.loads(gzip.decompress((tmp_path / "a.json.gz").read_bytes())) == s


def test_el_intento_mas_alto_gana_aunque_el_orden_alfabetico_no_lo_ponga_al_final(tmp_path):
    run = tmp_path / "P4"   # "intento-10" va antes que "intento-9" en orden alfabético
    _trozo(run, "Lascar", 1, "2026-02-01", "2026-02-10", 10, [_r("2026-02-02 05:00", vrp_mw=10.0)])
    _trozo(run, "Lascar", 1, "2026-02-01", "2026-02-10", 9, [_r("2026-02-02 05:00", vrp_mw=9.0)])
    stores, _ = U.unir([run])
    assert [r["vrp_mw"] for r in stores["Lascar"]["records"]] == [10.0]


def test_gz_sin_hora_en_la_cabecera(tmp_path):
    U.escribir_gz(tmp_path / "a.json.gz", {"volcano": "Lascar", "records": []})
    assert (tmp_path / "a.json.gz").read_bytes()[4:8] == b"\x00\x00\x00\x00"
