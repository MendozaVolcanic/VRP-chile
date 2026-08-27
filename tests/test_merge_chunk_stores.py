# -*- coding: utf-8 -*-
"""Tests del merge de trozos de reproceso (scripts/merge_chunk_stores.py).

Lo que protegen: que partir un reproceso largo en ventanas y unirlo después
devuelva EXACTAMENTE la misma serie que habría producido una corrida entera.
Un merge que pierda records reintroduce, en silencio, la pérdida de datos que
la partición vino a evitar.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.merge_chunk_stores import main, merge_stores  # noqa: E402


def _store(volcano, updated, records):
    return {"volcano": volcano, "updated": updated, "records": records}


def _rec(dt, sensor="VIIRS_SNPP", vrp=1.0):
    return {"datetime_utc": dt, "sensor": sensor, "vrp_mw": vrp}


def _write(tmp_path, name, store):
    p = tmp_path / name
    p.write_text(json.dumps(store), encoding="utf-8")
    return p


def test_une_trozos_disjuntos_sin_perder_records(tmp_path):
    a = _write(tmp_path, "a.json", _store("Villarrica", "2026-08-26T01:00:00Z", [
        _rec("2026-04-02T05:00:00Z"), _rec("2026-04-01T05:00:00Z")]))
    b = _write(tmp_path, "b.json", _store("Villarrica", "2026-08-26T02:00:00Z", [
        _rec("2026-05-10T05:00:00Z")]))

    store, duplicados = merge_stores([a, b])

    assert duplicados == 0
    assert [r["datetime_utc"] for r in store["records"]] == [
        "2026-04-01T05:00:00Z", "2026-04-02T05:00:00Z", "2026-05-10T05:00:00Z"]
    assert store["volcano"] == "Villarrica"


def test_misma_pasada_distinto_sensor_son_records_distintos(tmp_path):
    """La clave es (datetime_utc, sensor), igual que en pipeline/store.py."""
    a = _write(tmp_path, "a.json", _store("V", "2026-08-26T01:00:00Z", [
        _rec("2026-04-01T05:00:00Z", "VIIRS_SNPP")]))
    b = _write(tmp_path, "b.json", _store("V", "2026-08-26T02:00:00Z", [
        _rec("2026-04-01T05:00:00Z", "MODIS_AQUA")]))

    store, duplicados = merge_stores([a, b])

    assert duplicados == 0
    assert len(store["records"]) == 2


def test_ante_choque_gana_el_store_escrito_mas_tarde(tmp_path):
    viejo = _write(tmp_path, "viejo.json", _store("V", "2026-08-26T01:00:00Z", [
        _rec("2026-04-01T05:00:00Z", vrp=1.0)]))
    nuevo = _write(tmp_path, "nuevo.json", _store("V", "2026-08-26T09:00:00Z", [
        _rec("2026-04-01T05:00:00Z", vrp=2.0)]))

    # el orden de los argumentos no debe importar: manda `updated`
    for orden in ([viejo, nuevo], [nuevo, viejo]):
        store, duplicados = merge_stores(orden)
        assert duplicados == 1
        assert store["records"][0]["vrp_mw"] == 2.0


def test_trozo_faltante_no_aborta_pero_avisa(tmp_path, capsys):
    a = _write(tmp_path, "a.json", _store("V", "2026-08-26T01:00:00Z", [
        _rec("2026-04-01T05:00:00Z")]))
    out = tmp_path / "sub" / "V.json"

    rc = main(["--out", str(out), str(a), str(tmp_path / "no_existe.json")])

    assert rc == 0
    assert json.loads(out.read_text(encoding="utf-8"))["records"]
    assert "falta" in capsys.readouterr().err


def test_sin_ningun_trozo_falla_fuerte(tmp_path):
    rc = main(["--out", str(tmp_path / "V.json"), str(tmp_path / "nada.json")])
    assert rc == 1
    assert not (tmp_path / "V.json").exists()


@pytest.mark.parametrize("n_trozos", [1, 4])
def test_particion_equivale_a_corrida_entera(tmp_path, n_trozos):
    """La propiedad que importa: unir los trozos == la serie completa."""
    completa = [_rec(f"2026-04-{d:02d}T05:00:00Z", vrp=float(d)) for d in range(1, 21)]
    por_trozo = len(completa) // n_trozos
    paths = []
    for i in range(n_trozos):
        corte = completa[i * por_trozo:(i + 1) * por_trozo]
        paths.append(_write(tmp_path, f"c{i}.json",
                            _store("V", f"2026-08-26T0{i}:00:00Z", corte)))

    store, _ = merge_stores(paths)

    assert store["records"] == sorted(completa, key=lambda r: r["datetime_utc"])


def test_un_trozo_no_resucita_records_fuera_de_su_ventana(tmp_path):
    """S124 — el bug que dejaba meses enteros sin reprocesar, con el run VERDE.

    Cada job del reproceso hace checkout del archivo COMPLETO, reprocesa solo
    su tramo de fechas, y sube el archivo entero como artifact — o sea, con los
    otros meses en su version VIEJA adentro. El merge ordenaba por `updated` y
    dejaba ganar al ultimo, asi que el trozo que terminaba mas tarde imponia SU
    version de todos los meses y resucitaba lo que otro trozo acababa de
    reprocesar.

    Sintoma real: un reproceso 2026-05-01..08-27 dejo mayo fresco y junio,
    julio y agosto 100 % identicos byte a byte a la corrida anterior.

    Con `ventanas`, cada trozo aporta solo lo suyo.
    """
    import json

    def store(updated, records):
        p = tmp_path / f"{updated}.json"
        p.write_text(json.dumps({"volcano": "V", "updated": updated,
                                 "records": records}), encoding="utf-8")
        return p

    viejo = {"datetime_utc": "2026-06-10 05:00", "sensor": "VIIRS_SNPP", "vrp_mw": 0.0}
    nuevo = {"datetime_utc": "2026-06-10 05:00", "sensor": "VIIRS_SNPP", "vrp_mw": 9.9}
    mayo = {"datetime_utc": "2026-05-10 05:00", "sensor": "VIIRS_SNPP", "vrp_mw": 1.0}

    # el trozo de JUNIO reproceso el record (vrp 9.9) y termino PRIMERO
    junio = store("2026-08-27T10:00", [mayo, nuevo])
    # el trozo de MAYO termino DESPUES y arrastra junio en su version vieja
    may = store("2026-08-27T11:00", [mayo, viejo])

    # sin ventanas: gana el ultimo y junio queda VIEJO (el bug)
    sin, _ = merge_stores([junio, may])
    j = [r for r in sin["records"] if r["datetime_utc"].startswith("2026-06")][0]
    assert j["vrp_mw"] == 0.0, "reproduce el bug: el trozo tardio piso junio"

    # con ventanas: cada trozo aporta solo lo suyo y junio queda REPROCESADO
    con, _ = merge_stores([junio, may],
                          [("2026-06-01", "2026-06-30"), ("2026-05-01", "2026-05-31")])
    j = [r for r in con["records"] if r["datetime_utc"].startswith("2026-06")][0]
    assert j["vrp_mw"] == 9.9, "el trozo de junio debe conservar su reproceso"
    assert len(con["records"]) == 2, "mayo y junio, sin duplicados"
