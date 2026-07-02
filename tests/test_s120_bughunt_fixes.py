# -*- coding: utf-8 -*-
"""S120 — regresión de los fixes de pipeline de la cacería de bugs (batch B).

Cada test captura el bug que el fix resuelve; si una consolidación futura
revierte el fix, el test falla (patrón guard-de-intención A63).
"""
import json

import pytest

from pipeline import fetch, store


# === store._save atómico (bug: kill a mitad de escritura truncaba el JSON) ===

def test_store_save_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    store._save("TestVol", {"volcano": "TestVol", "records": [{"vrp_mw": 1.0}]})
    d = store._load("TestVol")
    assert d["records"][0]["vrp_mw"] == 1.0
    # sin tmp residual
    assert not list(tmp_path.glob("*.tmp"))


def test_store_save_interrupted_keeps_previous_file_valid(tmp_path, monkeypatch):
    """Si json.dump muere a mitad de escritura, el JSON previo queda INTACTO
    (antes: archivo truncado → todas las corridas siguientes crashean en _load)."""
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    store._save("TestVol", {"volcano": "TestVol", "records": [{"vrp_mw": 1.0}]})

    class Boom(RuntimeError):
        pass

    def dump_partial(obj, f, **kw):
        f.write('{"volcano": "TestVol", "rec')  # escritura parcial simulada
        raise Boom("kill a mitad de escritura")

    monkeypatch.setattr(store.json, "dump", dump_partial)
    with pytest.raises(Boom):
        store._save("TestVol", {"volcano": "TestVol", "records": []})

    # el archivo canónico sigue siendo el previo, parseable
    d = json.load(open(tmp_path / "TestVol.json", encoding="utf-8"))
    assert d["records"][0]["vrp_mw"] == 1.0


# === fetch.reset_transient_breakers (bug: breaker pegado en reprocesos multi-día) ===

def test_fetch_reset_transient_breakers(monkeypatch):
    monkeypatch.setattr(fetch, "_CMR_SEARCH_DOWN", True)
    fetch._DOWN_DOWNLOAD_HOSTS.add("nrt3.modaps.eosdis.nasa.gov")
    fetch.reset_transient_breakers()
    assert fetch._CMR_SEARCH_DOWN is False
    assert not fetch._DOWN_DOWNLOAD_HOSTS


# === profile: flags top-level del yaml deben regir (bug: se leían de paths:) ===

def test_bt_sat_guard_flags_reflejan_yaml_top_level():
    """Contrato: los valores del yaml operacional (top-level) son los que expone
    el módulo profile — antes se ignoraban en silencio y regían los defaults."""
    import yaml
    from pipeline import profile

    cfg = yaml.safe_load(open("pipeline/profiles/mirova_equivalent.yaml",
                              encoding="utf-8"))
    assert "enable_bt_sat_secondary_guard" in cfg, \
        "el flag vive top-level en el yaml operacional (si migró, actualizar test y profile.py)"
    assert profile.ENABLE_BT_SAT_SECONDARY_GUARD == bool(cfg["enable_bt_sat_secondary_guard"])
    assert profile.BT_SAT_MIR_K_MODIS == float(cfg["bt_sat_mir_k_modis"])
