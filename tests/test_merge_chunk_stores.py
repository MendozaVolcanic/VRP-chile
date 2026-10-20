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


# ---------------------------------------------------------------------------
# S157: --base. El merge conserva lo que el archivo de destino ya tiene fuera
# de las ventanas de la corrida.
#
# POR QUE: sin base, el merge escribia data/<perfil>/<Vol>.json SOLO con los
# trozos de su propia corrida. Relanzar dos trozos caidos de un volcan borraba
# en main todo el resto de su historico (paso con NevadosDeChillan en S157).
# ---------------------------------------------------------------------------

def _dump(path, store):
    """Igual que pipeline/store.py::_save: indent=2, ensure_ascii por defecto."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(store, f, indent=2)
    return path


def _tres_meses():
    abril = [_rec("2026-04-02T05:00:00Z", vrp=0.1), _rec("2026-04-20T05:10:00Z", "MODIS_AQUA", 0.2)]
    mayo = [_rec("2026-05-03T05:00:00Z", vrp=0.3), _rec("2026-05-15T05:00:00Z", vrp=0.4)]
    junio = [_rec("2026-06-07T05:00:00Z", vrp=0.5), _rec("2026-06-29T06:00:00Z", vrp=0.6)]
    return abril, mayo, junio


def _correr(out, base, ventanas, trozos):
    args = ["--out", str(out)]
    if base is not None:
        args += ["--base", str(base)]
    if ventanas is not None:
        args += ["--ventanas", *ventanas]
    return main(args + ["--", *[str(t) for t in trozos]])


def _records(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))["records"]


def test_base_conserva_las_ventanas_que_la_corrida_no_toca(tmp_path):
    abril, mayo, junio = _tres_meses()
    base = _dump(tmp_path / "base.json", _store("V", "2026-10-01T00:00:00Z", abril + mayo + junio))
    # el trozo de mayo reprocesa: cambia una pasada, pierde otra y trae una nueva
    mayo_k = [_rec("2026-05-03T05:00:00Z", vrp=9.3), _rec("2026-05-28T05:00:00Z", vrp=9.8)]
    trozo = _dump(tmp_path / "c_mayo.json", _store("V", "2026-10-20T00:00:00Z", abril + mayo_k + junio))
    out = tmp_path / "out" / "V.json"

    assert _correr(out, base, ["2026-05-01:2026-05-31"], [trozo]) == 0

    recs = _records(out)
    fuera = [r for r in recs if not r["datetime_utc"].startswith("2026-05")]
    dentro = [r for r in recs if r["datetime_utc"].startswith("2026-05")]
    # abril y junio: los de la base, byte a byte y en el mismo orden
    assert [json.dumps(r) for r in fuera] == [json.dumps(r) for r in abril + junio]
    # mayo: exactamente lo del trozo; la pasada 05-15 de la base NO resucita
    assert [json.dumps(r) for r in dentro] == [json.dumps(r) for r in mayo_k]


def test_base_conserva_aunque_el_trozo_no_traiga_los_otros_meses(tmp_path):
    """El caso de Chillan: el artefacto del trozo trae sólo su tramo (perfil
    nuevo o checkout sin el resto). Abril y junio tienen que salir de la base."""
    abril, mayo, junio = _tres_meses()
    base = _dump(tmp_path / "base.json", _store("V", "2026-10-01T00:00:00Z", abril + mayo + junio))
    trozo = _dump(tmp_path / "c.json", _store("V", "2026-10-20T00:00:00Z", mayo))
    out = tmp_path / "V.json"

    assert _correr(out, base, ["2026-05-01:2026-05-31"], [trozo]) == 0

    assert [json.dumps(r) for r in _records(out)] == \
        [json.dumps(r) for r in abril + mayo + junio]


def test_base_identica_al_trozo_da_el_mismo_archivo_byte_a_byte(tmp_path):
    abril, mayo, junio = _tres_meses()
    st = _store("V", "2026-10-01T00:00:00Z", abril + mayo + junio)
    base = _dump(tmp_path / "base.json", st)
    trozo = _dump(tmp_path / "c.json", st)
    out = tmp_path / "V.json"

    assert _correr(out, base, ["2026-05-01:2026-05-31"], [trozo]) == 0

    assert out.read_bytes() == base.read_bytes()


@pytest.mark.parametrize("base_vacia", ["no_existe", "sin_records"])
def test_sin_base_util_el_resultado_es_el_de_siempre(tmp_path, base_vacia):
    abril, mayo, junio = _tres_meses()
    trozo = _dump(tmp_path / "c.json", _store("V", "2026-10-20T00:00:00Z", abril + mayo + junio))
    base = tmp_path / "base.json"
    if base_vacia == "sin_records":
        _dump(base, _store("V", "2026-10-01T00:00:00Z", []))
    hoy, con = tmp_path / "hoy.json", tmp_path / "con.json"

    assert _correr(hoy, None, ["2026-05-01:2026-05-31"], [trozo]) == 0
    assert _correr(con, base, ["2026-05-01:2026-05-31"], [trozo]) == 0

    assert con.read_bytes() == hoy.read_bytes()


def test_base_bordes_de_ventana_son_inclusivos_por_fecha(tmp_path):
    """La ventana se compara por fecha UTC (primeros 10 caracteres), cerrada en
    los dos extremos, igual que el filtro de --ventanas sobre los trozos."""
    bordes = [_rec("2026-04-30T23:59:59Z", vrp=1.0), _rec("2026-05-01T00:00:00Z", vrp=2.0),
              _rec("2026-05-31 23:59", vrp=3.0), _rec("2026-06-01 00:00", vrp=4.0)]
    base = _dump(tmp_path / "base.json", _store("V", "2026-10-01T00:00:00Z", bordes))
    # el trozo de mayo NO trajo ninguna de las dos pasadas de borde de mayo
    trozo = _dump(tmp_path / "c.json", _store("V", "2026-10-20T00:00:00Z",
                                              [_rec("2026-05-10T05:00:00Z", vrp=5.0)]))
    out = tmp_path / "V.json"

    assert _correr(out, base, ["2026-05-01:2026-05-31"], [trozo]) == 0

    assert [r["vrp_mw"] for r in _records(out)] == [1.0, 5.0, 4.0]


def test_base_choque_dentro_de_la_ventana_gana_el_trozo_y_no_es_duplicado(tmp_path, capsys):
    base = _dump(tmp_path / "base.json", _store("V", "2026-10-25T00:00:00Z", [
        _rec("2026-05-03T05:00:00Z", vrp=1.0)]))
    # aunque la base tenga `updated` MAS reciente, dentro de la ventana manda el trozo
    trozo = _dump(tmp_path / "c.json", _store("V", "2026-10-20T00:00:00Z", [
        _rec("2026-05-03T05:00:00Z", vrp=2.0)]))
    out = tmp_path / "V.json"

    assert _correr(out, base, ["2026-05-01:2026-05-31"], [trozo]) == 0

    st = json.loads(out.read_text(encoding="utf-8"))
    assert [r["vrp_mw"] for r in st["records"]] == [2.0]
    assert st["updated"] == "2026-10-25T00:00:00Z"
    assert "(0 duplicados" in capsys.readouterr().out


def test_base_duplicados_entre_trozos_se_siguen_contando(tmp_path, capsys):
    """Dos trozos con ventanas solapadas (relanzamiento): la regla vieja sigue."""
    base = _dump(tmp_path / "base.json", _store("V", "2026-10-01T00:00:00Z", [
        _rec("2026-04-02T05:00:00Z", vrp=0.1)]))
    a = _dump(tmp_path / "a.json", _store("V", "2026-10-20T01:00:00Z", [
        _rec("2026-05-03T05:00:00Z", vrp=1.0)]))
    b = _dump(tmp_path / "b.json", _store("V", "2026-10-20T02:00:00Z", [
        _rec("2026-05-03T05:00:00Z", vrp=2.0)]))
    out = tmp_path / "V.json"

    assert _correr(out, base, ["2026-05-01:2026-05-31", "2026-05-01:2026-05-31"], [a, b]) == 0

    assert [r["vrp_mw"] for r in _records(out)] == [0.1, 2.0]
    assert "(1 duplicados" in capsys.readouterr().out


def test_base_trozo_caido_no_borra_su_ventana(tmp_path):
    """Un trozo sin artefacto no aporta ventana: su tramo queda como estaba en
    la base, en vez de desaparecer de main."""
    abril, mayo, junio = _tres_meses()
    base = _dump(tmp_path / "base.json", _store("V", "2026-10-01T00:00:00Z", abril + mayo + junio))
    trozo_mayo = _dump(tmp_path / "c_mayo.json", _store("V", "2026-10-20T00:00:00Z",
                                                        [_rec("2026-05-03T05:00:00Z", vrp=9.3)]))
    out = tmp_path / "V.json"

    assert _correr(out, base, ["2026-05-01:2026-05-31", "2026-06-01:2026-06-30"],
                   [trozo_mayo, tmp_path / "c_junio_no_existe.json"]) == 0

    recs = _records(out)
    assert [json.dumps(r) for r in recs if r["datetime_utc"].startswith("2026-06")] == \
        [json.dumps(r) for r in junio]


def test_base_record_sin_fecha_se_conserva(tmp_path):
    base = _dump(tmp_path / "base.json", _store("V", "2026-10-01T00:00:00Z", [
        {"sensor": "VIIRS_SNPP", "vrp_mw": 7.0}]))
    trozo = _dump(tmp_path / "c.json", _store("V", "2026-10-20T00:00:00Z", [
        _rec("2026-05-03T05:00:00Z")]))
    out = tmp_path / "V.json"

    assert _correr(out, base, ["2026-05-01:2026-05-31"], [trozo]) == 0

    assert len(_records(out)) == 2


def test_base_sin_ventanas_se_rechaza(tmp_path):
    """Sin ventanas no se sabe que tramo cubre la corrida: no hay forma segura
    de decidir que conservar de la base."""
    base = _dump(tmp_path / "base.json", _store("V", "2026-10-01T00:00:00Z", []))
    trozo = _dump(tmp_path / "c.json", _store("V", "2026-10-20T00:00:00Z", [_rec("2026-05-03T05:00:00Z")]))
    out = tmp_path / "V.json"

    assert _correr(out, base, None, [trozo]) == 1
    assert not out.exists()


def test_base_de_otro_volcan_se_rechaza(tmp_path):
    base = _dump(tmp_path / "base.json", _store("Lascar", "2026-10-01T00:00:00Z",
                                                [_rec("2026-04-02T05:00:00Z")]))
    trozo = _dump(tmp_path / "c.json", _store("Villarrica", "2026-10-20T00:00:00Z",
                                              [_rec("2026-05-03T05:00:00Z")]))
    out = tmp_path / "V.json"

    assert _correr(out, base, ["2026-05-01:2026-05-31"], [trozo]) == 1
    assert not out.exists()
