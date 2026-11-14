# -*- coding: utf-8 -*-
"""Pruebas del reemplazo de la serie VIIRS 750 de Cordón Caulle con la caja del cráter (S184, PR #999).

POR QUÉ. El script escribe en `data/` (A45). Cada regla de su docstring tiene aquí una prueba que la rompe si cambia:
sólo VIIRS 750 de PCC, la ventana, el par por pasada, el tope de sin par (todo o nada), y que el reproceso venga del
commit con `crater`. La prueba sobre los datos reales corre el ENSAYO (no escribe) con la unión commiteada.
"""
from __future__ import annotations

import gzip
import json
import subprocess
from pathlib import Path

import sys

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "experiments" / "_s184_pcc_crater_aplicar"))
import aplicar_pcc_v750 as ap  # noqa: E402
V = ap.VOLCAN


def rec(dt, sensor, vrp=1.0, sha=ap.CODIGO_SHA, perfil=ap.PERFIL, via=True, fp=None):
    r = {"datetime_utc": dt, "sensor": sensor, "vrp_mw": vrp, "via_codigo_mirova": via,
         "regimen": {"perfil": perfil, "codigo_sha": sha, "origen": "actions"}}
    if fp:
        r["first_processed_utc"] = fp
    return r


def op(*records):
    return {"volcano": V, "records": list(records)}


def inf_union(desde="2025-02-15", hasta="2025-02-20", huecos=()):
    return {"volcanes": {V: {"desde": desde, "hasta": hasta, "huecos": list(huecos)}}}


def test_reemplaza_solo_v750_en_la_ventana_y_conserva_first_processed():
    viejo = rec("2025-02-16 05:00", "VIIRS_NOAA20_750", vrp=10.1, sha="viejo", perfil="mirova_equivalent",
                fp="2025-02-16T09:00:00Z")
    otro = rec("2025-02-16 05:00", "VIIRS_NOAA20", vrp=3.0, sha="viejo", perfil="mirova_equivalent")
    modis = rec("2025-02-16 03:00", "MODIS_AQUA", vrp=2.0, sha="viejo", perfil="mirova_equivalent")
    antes = rec("2025-02-14 05:00", "VIIRS_NOAA20_750", vrp=7.0, sha="viejo")
    tras = rec("2025-02-21 05:00", "VIIRS_NOAA21_750", vrp=8.0, sha="viejo")
    union = op(rec("2025-02-16 05:00", "VIIRS_NOAA20_750", vrp=0.35, fp="2026-11-14T00:00:00Z"),
               rec("2025-02-16 05:00", "VIIRS_NOAA20", vrp=99.0))  # el 375 de la unión no se usa
    store, inf = ap.reemplazar(op(viejo, otro, modis, antes, tras), union, "2025-02-15", "2025-02-20")
    por = {(r["datetime_utc"], r["sensor"]): r for r in store["records"]}
    assert por[("2025-02-16 05:00", "VIIRS_NOAA20_750")]["vrp_mw"] == 0.35
    assert por[("2025-02-16 05:00", "VIIRS_NOAA20_750")]["first_processed_utc"] == "2025-02-16T09:00:00Z"
    assert por[("2025-02-16 05:00", "VIIRS_NOAA20")]["vrp_mw"] == 3.0
    assert por[("2025-02-16 03:00", "MODIS_AQUA")]["vrp_mw"] == 2.0
    assert por[("2025-02-14 05:00", "VIIRS_NOAA20_750")]["vrp_mw"] == 7.0
    assert por[("2025-02-21 05:00", "VIIRS_NOAA21_750")]["vrp_mw"] == 8.0
    assert inf["reemplazados"] == 1 and inf["sin_par_conservados"] == 0 and inf["agregados"] == 0
    assert inf["tras_ventana_sin_tocar"] == 1
    assert len(store["records"]) == 5


def test_sin_first_processed_en_el_publicado_no_hereda_el_del_reproceso():
    union = op(rec("2025-02-16 05:00", "VIIRS_NOAA20_750", fp="2026-11-14T00:00:00Z"))
    store, _ = ap.reemplazar(op(rec("2025-02-16 05:00", "VIIRS_NOAA20_750", sha="viejo")), union,
                             "2025-02-15", "2025-02-20")
    assert "first_processed_utc" not in store["records"][0]


def test_sin_par_se_conserva_y_agregados_se_suman():
    union = op(rec("2025-02-17 05:00", "VIIRS_NOAA21_750", vrp=0.5))
    store, inf = ap.reemplazar(op(rec("2025-02-16 05:00", "VIIRS_NOAA20_750", vrp=4.0, sha="viejo")), union,
                               "2025-02-15", "2025-02-20")
    assert inf["sin_par_conservados"] == 1 and inf["fraccion_sin_par"] == 1.0
    assert inf["agregados"] == 1
    assert [r["vrp_mw"] for r in store["records"]] == [4.0, 0.5]


def test_no_modifica_las_entradas_y_es_idempotente():
    o = op(rec("2025-02-16 05:00", "VIIRS_NOAA20_750", vrp=10.1, sha="viejo"))
    u = op(rec("2025-02-16 05:00", "VIIRS_NOAA20_750", vrp=0.35), rec("2025-02-18 05:00", "VIIRS_NOAA20_750"))
    o0, u0 = json.dumps(o), json.dumps(u)
    s1, _ = ap.reemplazar(o, u, "2025-02-15", "2025-02-20")
    s2, inf2 = ap.reemplazar(s1, u, "2025-02-15", "2025-02-20")
    assert json.dumps(o) == o0 and json.dumps(u) == u0
    assert s1 == s2 and inf2["agregados"] == 0 and inf2["reemplazados"] == 2


@pytest.mark.parametrize("cambio", [
    {"sha": "otro"}, {"perfil": "mirova_equivalent"}, {"via": False}, {"via": None}])
def test_union_de_otro_codigo_perfil_o_sin_via_se_rehusa(cambio):
    u = op(rec("2025-02-16 05:00", "VIIRS_NOAA20_750", **cambio))
    with pytest.raises(ap.Rehusado):
        ap.validar_union(u, inf_union(), "2025-02-15", "2025-02-20")


def test_union_con_huecos_o_corta_se_rehusa():
    u = op(rec("2025-02-16 05:00", "VIIRS_NOAA20_750"))
    ap.validar_union(u, inf_union(), "2025-02-15", "2025-02-20")
    with pytest.raises(ap.Rehusado):
        ap.validar_union(u, inf_union(huecos=["2025-02-17"]), "2025-02-15", "2025-02-20")
    with pytest.raises(ap.Rehusado):
        ap.validar_union(u, inf_union(desde="2025-02-16"), "2025-02-15", "2025-02-20")
    with pytest.raises(ap.Rehusado):
        ap.validar_union(u, inf_union(hasta="2025-02-19"), "2025-02-15", "2025-02-20")


def test_pasada_repetida_se_rehusa():
    r = rec("2025-02-16 05:00", "VIIRS_NOAA20_750")
    with pytest.raises(ap.Rehusado):
        ap.reemplazar(op(r), op(r, r), "2025-02-15", "2025-02-20")
    with pytest.raises(ap.Rehusado):
        ap.reemplazar(op(r, r), op(r), "2025-02-15", "2025-02-20")


def test_otro_volcan_se_rehusa():
    with pytest.raises(ap.Rehusado):
        ap.reemplazar({"volcano": "Lascar", "records": []}, op(), "2025-02-15", "2025-02-20")


def _arbol(tmp_path, publicados, union_recs, hasta="2025-02-20"):
    datos = tmp_path / "datos"
    datos.mkdir()
    (datos / f"{V}.json").write_text(json.dumps(op(*publicados)), encoding="utf-8")
    u = tmp_path / "u.json.gz"
    u.write_bytes(gzip.compress(json.dumps(op(*union_recs)).encode("utf-8")))
    iu = tmp_path / "iu.json"
    iu.write_text(json.dumps(inf_union(hasta=hasta)), encoding="utf-8")
    return datos, u, iu


def test_todo_o_nada_sobre_el_tope_no_escribe(tmp_path):
    pub = [rec(f"2025-02-1{d} 05:00", "VIIRS_NOAA20_750", sha="viejo") for d in range(5, 10)]
    datos, u, iu = _arbol(tmp_path, pub, [rec("2025-02-15 05:00", "VIIRS_NOAA20_750")])
    antes = (datos / f"{V}.json").read_bytes()
    informe = tmp_path / "inf.json"
    codigo = ap.main(["--datos", str(datos), "--union", str(u), "--informe-union", str(iu), "--max-sin-par", "0.02",
                      "--informe", str(informe), "--aplicar"])
    assert codigo == 2
    assert (datos / f"{V}.json").read_bytes() == antes
    inf = json.loads(informe.read_text(encoding="utf-8"))
    assert inf["aplicado"] is False and inf["sin_par_conservados"] == 4 and "rehusado" in inf


def test_ensayo_no_escribe_y_aplicar_si(tmp_path):
    pub = [rec("2025-02-16 05:00", "VIIRS_NOAA20_750", vrp=10.1, sha="viejo")]
    datos, u, iu = _arbol(tmp_path, pub, [rec("2025-02-16 05:00", "VIIRS_NOAA20_750", vrp=0.35)])
    antes = (datos / f"{V}.json").read_bytes()
    args = ["--datos", str(datos), "--union", str(u), "--informe-union", str(iu), "--max-sin-par", "0.02",
            "--informe", str(tmp_path / "inf.json")]
    assert ap.main(args) == 0
    assert (datos / f"{V}.json").read_bytes() == antes
    assert ap.main(args + ["--aplicar"]) == 0
    assert json.loads((datos / f"{V}.json").read_text(encoding="utf-8"))["records"][0]["vrp_mw"] == 0.35


def test_el_commit_del_reproceso_tiene_la_caja_del_crater_en_pcc():
    """POR QUÉ: CODIGO_SHA es la única prueba de que la unión es de `crater` y no de `sens`."""
    r = subprocess.run(["git", "show", f"{ap.CODIGO_SHA}:pipeline/grillas_mirova.yaml"], cwd=RAIZ,
                       capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        pytest.skip("commit del reproceso ausente en este clon (checkout superficial)")
    linea = [x for x in r.stdout.splitlines() if x.strip().startswith(f"{V}:")]
    assert len(linea) == 1 and "roi_v750: crater" in linea[0]


@pytest.mark.skipif(not ap.UNION.exists(), reason="unión aún no commiteada")
def test_ensayo_sobre_los_datos_reales(tmp_path):
    inf = ap.correr(RAIZ / "data" / "mirova_equivalent", ap.UNION, ap.INFORME_UNION, None, 0.02, aplicar=False)
    assert inf["aplicado"] is False
    assert inf["fraccion_sin_par"] <= 0.02
    assert inf["reemplazados"] > 0
