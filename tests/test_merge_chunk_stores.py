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
