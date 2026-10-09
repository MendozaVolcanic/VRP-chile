# -*- coding: utf-8 -*-
"""S150 — `first_processed_utc`: cuando una pasada aparecio POR PRIMERA VEZ en nuestros datos.

POR QUE. La latencia del NRT (desde que el satelite pasa hasta que el operador ve el dato) es parte del
producto, y la meta de la charla del congreso es mostrarla medida antes y despues del disparador externo del
cron. `processed_utc` (S132) no sirve para eso a proposito: describe cuando se produjo ESTA version del
record y cambia cuando el producto NRT se reemplaza por el estandar (3 a 5 dias despues) o en un reproceso.
La medicion "antes" (experiments/_s150_latencia/) tuvo que reconstruir la primera aparicion recorriendo el
historial de git. Este campo la deja escrita en el dato y no se reescribe nunca.

Es un campo descriptivo: no entra en deteccion, magnitud ni ninguna compuerta. Records anteriores a S150 no lo
tienen y no se les inventa (su primera aparicion se reconstruye del historial de git si hace falta).

Las dos preguntas del instrumento: si el campo se reescribiera en el upgrade o en el reproceso, los tests 2 y
3 fallan; si no se escribiera nunca, el test 1 falla.
"""
from datetime import datetime, timezone


def _base():
    return dict(datetime_utc="2026-10-01 05:24", sensor="VIIRS_NOAA20", vrp_mw=1.0,
                hotspot_dist_km=0.4)


def test_un_record_nuevo_se_sella_con_su_primera_aparicion(tmp_path, monkeypatch):
    from pipeline import store
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    r = dict(_base(), product_version="nrt")
    store.append_record("TestVolcano", r)
    guardado = store.get_records("TestVolcano")[0]
    assert guardado["first_processed_utc"] == guardado["processed_utc"]
    prim = datetime.strptime(guardado["first_processed_utc"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    assert prim > datetime(2026, 10, 1, 5, 24, tzinfo=timezone.utc)


def test_el_upgrade_nrt_a_estandar_conserva_la_primera_aparicion(tmp_path, monkeypatch):
    from pipeline import store
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    store.append_record("TestVolcano", dict(_base(), product_version="nrt"))
    rec = store.get_records("TestVolcano")[0]
    rec["first_processed_utc"] = "2026-10-01T08:00:00Z"   # la primera aparicion real
    store._save("TestVolcano", {"volcano": "TestVolcano", "records": [rec]})
    store.append_record("TestVolcano", dict(_base(), product_version="standard"))
    nuevo = store.get_records("TestVolcano")[0]
    assert nuevo["product_version"] == "standard"
    assert nuevo["first_processed_utc"] == "2026-10-01T08:00:00Z"
    assert nuevo["processed_utc"] != "2026-10-01T08:00:00Z"   # processed_utc si cambia (S132)


def test_un_reproceso_conserva_la_primera_aparicion(tmp_path, monkeypatch):
    from pipeline import store
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    store.append_record("TestVolcano", dict(_base(), product_version="standard"))
    rec = store.get_records("TestVolcano")[0]
    rec["first_processed_utc"] = "2026-10-01T08:00:00Z"
    store._save("TestVolcano", {"volcano": "TestVolcano", "records": [rec]})
    store.append_record("TestVolcano", dict(_base(), product_version="standard"), overwrite=True)
    assert store.get_records("TestVolcano")[0]["first_processed_utc"] == "2026-10-01T08:00:00Z"


def test_a_un_record_viejo_sin_el_campo_no_se_le_inventa(tmp_path, monkeypatch):
    from pipeline import store
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    store.append_record("TestVolcano", dict(_base(), product_version="nrt"))
    rec = store.get_records("TestVolcano")[0]
    rec.pop("first_processed_utc", None)   # como un record anterior a S150
    store._save("TestVolcano", {"volcano": "TestVolcano", "records": [rec]})
    store.append_record("TestVolcano", dict(_base(), product_version="standard"))
    assert "first_processed_utc" not in store.get_records("TestVolcano")[0]
