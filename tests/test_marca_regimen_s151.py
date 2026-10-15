# -*- coding: utf-8 -*-
"""Tarea 0.6 del loop (S151): cada record dice con que perfil y con que codigo se produjo.

POR QUE. 0 de 65.206 records lo decian (VERIFICADOR_DATOS S150 D7). Un JSON de produccion mezcla records
de meses distintos, reprocesos parciales y cambios de flags; sin la marca, una comparacion antes y despues
de un cambio (A104: los regimenes separados por #535) no sabe que records son de que regimen, y la
reconstruccion por fechas de merge falla en silencio con los reprocesos. Bloquea toda adopcion futura.

Es un campo descriptivo: no entra en deteccion, magnitud ni en ninguna compuerta. Se reescribe en cada
version del record (como `processed_utc`), porque describe ESTA version, no la primera.

Las dos preguntas del instrumento: si la marca no se escribiera, el test 1 falla; si se escribiera fija y
no siguiera al codigo (por ejemplo, copiada del record anterior en un reproceso), el test 3 falla.
"""


def _base():
    return dict(datetime_utc="2026-10-01 05:24", sensor="VIIRS_NOAA20", vrp_mw=1.0,
                hotspot_dist_km=0.4, product_version="standard")


def test_un_record_nuevo_lleva_perfil_y_sha(tmp_path, monkeypatch):
    from pipeline import profile, store
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    monkeypatch.setenv("GITHUB_SHA", "a" * 40)
    store.append_record("TestVolcano", _base())
    reg = store.get_records("TestVolcano")[0]["regimen"]
    assert reg["perfil"] == profile.PROFILE_NAME
    assert reg["codigo_sha"] == "a" * 40
    assert reg["origen"] == "actions"


def test_fuera_de_actions_el_sha_sale_de_git(tmp_path, monkeypatch):
    import re
    from pipeline import store
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    monkeypatch.delenv("GITHUB_SHA", raising=False)
    store.append_record("TestVolcano", _base())
    reg = store.get_records("TestVolcano")[0]["regimen"]
    assert reg["origen"] == "local"
    # En un checkout el sha existe; sin git queda None, que tambien es una respuesta honesta.
    assert reg["codigo_sha"] is None or re.fullmatch(r"[0-9a-f]{40}", reg["codigo_sha"])


def test_un_reproceso_reescribe_la_marca(tmp_path, monkeypatch):
    from pipeline import store
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    monkeypatch.setenv("GITHUB_SHA", "a" * 40)
    store.append_record("TestVolcano", _base())
    monkeypatch.setenv("GITHUB_SHA", "b" * 40)
    store.append_record("TestVolcano", _base(), overwrite=True)
    assert store.get_records("TestVolcano")[0]["regimen"]["codigo_sha"] == "b" * 40


def test_la_marca_no_toca_la_magnitud(tmp_path, monkeypatch):
    from pipeline import store
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    store.append_record("TestVolcano", _base())
    r = store.get_records("TestVolcano")[0]
    assert r["vrp_mw"] == 1.0
