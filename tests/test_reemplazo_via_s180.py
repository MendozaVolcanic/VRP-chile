# -*- coding: utf-8 -*-
"""S180: reglas del reemplazo de la historia con la vía «código MIROVA» en scripts/reemplazar_ventana_reproceso.py.

POR QUÉ. La historia publicada de los 11 Tier A está escrita con K y las pasadas nuevas salen con la vía (MODIS desde
#934, VIIRS 375 desde #974, VIIRS 750 desde #983). Para que el tablero muestre un solo método se reemplaza la historia
con los reprocesos de la vía, una familia de sensor por vez (plan docs/PLAN_REEMPLAZO_HISTORIA_VIA_S178.md y su
verificación limpia). Cada regla nueva y su razón física u operacional:

- `--familia` (MODIS, VIIRS375, VIIRS750, convención A48 de frontend/cambio_detector.js): cada familia cambió de método
  en una fecha distinta; fuera de la familia no se toca nada.
- `--corte-utc` (el instante del encendido de la familia): lo que el NRT escribió con la vía NUNCA se pisa (es la
  fuente desde el encendido) y ningún record del reproceso desde el corte se agrega (desde ahí manda el NRT). Un
  record operacional con cualquier marca de vía (`true` o texto de caída a K) es de producción con la vía encendida.
- `--apartar-sin-par`: la vía descarta el gránulo que roza el volcán por el borde de la franja y K sí lo escribía (1
  a 6 % por volcán). Nicolás decidió el 2026-11-11 (opción A) apartarlas a un archivo de residuos, sin borrarlas, para
  que la serie quede como la escribe hoy la producción.

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) Cada regla tiene su caso que falla con el script viejo (una pasada de otra
familia, una de la vía de producción, una del reproceso posterior al corte, una sin par). (2) El conteo del informe
se compara con el número de records realmente movidos, no consigo mismo.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.reemplazar_ventana_reproceso import reemplazar_ventana, reemplazar_ventana_via  # noqa: E402

PERFIL = "_s172_retro_paquete"


def _rec(dt, sensor, perfil=PERFIL, via=None, **kw):
    r = {"datetime_utc": dt, "sensor": sensor, "vrp_mw": kw.pop("vrp_mw", 0.0),
         "regimen": {"perfil": perfil, "codigo_sha": "a" * 40, "origen": "actions"}}
    if via is not None:
        r["via_codigo_mirova"] = via
    r.update(kw)
    return r


def _store(records):
    return {"volcano": "Lascar", "updated": "2026-11-11T00:00:00Z", "records": records}


OP = "mirova_equivalent"
CORTE = "2026-11-11 13:09"


def _op():
    return _store([
        _rec("2026-11-09 05:00", "VIIRS_NOAA20", OP, vrp_mw=1.0, first_processed_utc="2026-11-09T08:00:00Z"),  # K, par
        _rec("2026-11-09 05:00", "VIIRS_NOAA20_750", OP, vrp_mw=2.0),            # K de otra familia
        _rec("2026-11-09 05:00", "MODIS_AQUA", OP, vrp_mw=3.0),                  # K de otra familia
        _rec("2026-11-09 06:00", "VIIRS_NOAA21", OP, vrp_mw=4.0),                # K sin par: borde
        _rec("2026-11-10 05:00", "VIIRS_NOAA20", OP, via=True, vrp_mw=5.0),      # vía de producción antes del corte
        _rec("2026-11-10 06:00", "VIIRS_SNPP", OP, via="sin_grilla", vrp_mw=6.0),  # caída a K de producción
        _rec("2026-11-11 18:00", "VIIRS_NOAA20", OP, via=True, vrp_mw=7.0),      # vía de producción tras el corte
    ])


def _re():
    return _store([
        _rec("2026-11-09 05:00", "VIIRS_NOAA20", via=True, vrp_mw=10.0),
        _rec("2026-11-09 05:00", "VIIRS_NOAA20_750", via=True, vrp_mw=20.0),
        _rec("2026-11-09 05:00", "MODIS_AQUA", via=True, vrp_mw=30.0),
        _rec("2026-11-09 07:00", "VIIRS_SNPP", via=True, vrp_mw=40.0),           # sólo en la vía: se agrega
        _rec("2026-11-10 05:00", "VIIRS_NOAA20", via=True, vrp_mw=50.0),         # choca con la vía de producción
        _rec("2026-11-10 06:00", "VIIRS_SNPP", via=True, vrp_mw=60.0),           # choca con la caída de producción
        _rec("2026-11-11 14:00", "VIIRS_NOAA21", via=True, vrp_mw=70.0),         # tras el corte: no se agrega
    ])


def _correr(**kw):
    a = dict(familia="VIIRS375", corte_utc=CORTE, apartar_sin_par=True)
    a.update(kw)
    return reemplazar_ventana_via(_op(), _re(), "2025-02-15", "2026-11-11", PERFIL, **a)


def _clave(store):
    return {(r["datetime_utc"], r["sensor"]): r for r in store["records"]}


def test_reemplaza_el_k_de_la_familia_y_hereda_first_processed():
    s, inf, _ = _correr()
    k = _clave(s)
    assert k[("2026-11-09 05:00", "VIIRS_NOAA20")]["vrp_mw"] == 10.0
    assert k[("2026-11-09 05:00", "VIIRS_NOAA20")]["first_processed_utc"] == "2026-11-09T08:00:00Z"
    assert inf["reemplazados"] == 1


def test_otra_familia_no_se_toca_en_ninguna_direccion():
    s, inf, _ = _correr()
    k = _clave(s)
    assert k[("2026-11-09 05:00", "VIIRS_NOAA20_750")]["vrp_mw"] == 2.0
    assert k[("2026-11-09 05:00", "MODIS_AQUA")]["vrp_mw"] == 3.0
    assert inf["reproceso_otra_familia"] == 2


def test_la_via_de_produccion_nunca_se_pisa_tampoco_su_caida_a_k():
    s, inf, _ = _correr()
    k = _clave(s)
    assert k[("2026-11-10 05:00", "VIIRS_NOAA20")]["vrp_mw"] == 5.0
    assert k[("2026-11-10 06:00", "VIIRS_SNPP")]["vrp_mw"] == 6.0
    assert k[("2026-11-11 18:00", "VIIRS_NOAA20")]["vrp_mw"] == 7.0
    assert inf["via_operacional_conservados"] == 2   # los dos de antes del corte que chocaban


def test_nada_del_reproceso_desde_el_corte_se_agrega():
    s, inf, _ = _correr()
    assert ("2026-11-11 14:00", "VIIRS_NOAA21") not in _clave(s)
    assert inf["reproceso_tras_corte"] == 1


def test_la_pasada_solo_en_la_via_se_agrega():
    s, inf, _ = _correr()
    assert _clave(s)[("2026-11-09 07:00", "VIIRS_SNPP")]["vrp_mw"] == 40.0
    assert inf["agregados"] == 1


def test_la_sin_par_se_aparta_sin_borrarla_y_el_conteo_es_el_movido():
    s, inf, apartados = _correr()
    assert ("2026-11-09 06:00", "VIIRS_NOAA21") not in _clave(s)
    assert [(r["datetime_utc"], r["sensor"]) for r in apartados] == [("2026-11-09 06:00", "VIIRS_NOAA21")]
    assert apartados[0]["vrp_mw"] == 4.0
    assert apartados[0]["_apartado"]["motivo"] == "borde_via"
    assert inf["sin_par_apartados"] == len(apartados) == 1
    assert len(s["records"]) + len(apartados) == len(_op()["records"]) + inf["agregados"]


def test_sin_apartar_la_sin_par_se_conserva_como_antes():
    s, inf, apartados = _correr(apartar_sin_par=False)
    assert ("2026-11-09 06:00", "VIIRS_NOAA21") in _clave(s)
    assert apartados == [] and inf["solo_operacional"] == 1


def test_el_k_desde_el_corte_no_se_toca_y_se_cuenta():
    op = _op()
    op["records"].append(_rec("2026-11-11 15:00", "VIIRS_NOAA21", OP, vrp_mw=9.0))
    s, inf, apartados = reemplazar_ventana_via(op, _re(), "2025-02-15", "2026-11-11", PERFIL,
                                               familia="VIIRS375", corte_utc=CORTE, apartar_sin_par=True)
    assert _clave(s)[("2026-11-11 15:00", "VIIRS_NOAA21")]["vrp_mw"] == 9.0
    assert inf["k_desde_el_corte"] == 1
    assert all(r["datetime_utc"] != "2026-11-11 15:00" for r in apartados)


def test_familia_desconocida_se_rehusa():
    with pytest.raises(ValueError):
        _correr(familia="VIIRS")


def test_el_corte_con_t_o_espacio_da_lo_mismo():
    a = _correr(corte_utc="2026-11-11T13:09:21Z")[1]
    b = _correr()[1]
    assert a == b


def test_la_funcion_vieja_sigue_igual():
    s, inf = reemplazar_ventana(_op(), _re(), "2025-02-15", "2026-11-11", PERFIL)
    assert inf["reemplazados"] == 5   # todas las familias, sin respetar la vía de producción: el comportamiento #883


# ---------------------------------------------------------------- CLI
def _cli(tmp_path, *extra, residuo_previo=None):
    op, re_ = tmp_path / "op.json", tmp_path / "re.json"
    op.write_text(json.dumps(_op(), indent=2), encoding="utf-8")
    re_.write_text(json.dumps(_re(), indent=2), encoding="utf-8")
    res = tmp_path / "residuos" / "Lascar.json"
    if residuo_previo is not None:
        res.parent.mkdir(parents=True)
        res.write_text(json.dumps(residuo_previo, indent=2), encoding="utf-8")
    antes = op.read_bytes()
    r = subprocess.run([sys.executable, "scripts/reemplazar_ventana_reproceso.py", "--operacional", str(op),
                        "--reproceso", str(re_), "--desde", "2025-02-15", "--hasta", "2026-11-11",
                        "--perfil-esperado", PERFIL, "--informe", str(tmp_path / "inf.json"),
                        "--familia", "VIIRS375", "--corte-utc", CORTE, "--apartar-sin-par", str(res), *extra],
                       cwd=ROOT, capture_output=True, text=True, env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    return r, op, antes, res


def test_cli_ensayo_no_escribe_ni_la_serie_ni_el_residuo(tmp_path):
    r, op, antes, res = _cli(tmp_path, "--max-solo-operacional", "0.5")
    assert r.returncode == 0, r.stderr
    assert op.read_bytes() == antes and not res.exists()
    inf = json.loads((tmp_path / "inf.json").read_text(encoding="utf-8"))
    assert inf["aplicado"] is False and inf["sin_par_apartados"] == 1


def test_cli_aplicar_escribe_la_serie_y_el_residuo(tmp_path):
    r, op, _, res = _cli(tmp_path, "--max-solo-operacional", "0.5", "--aplicar")
    assert r.returncode == 0, r.stderr
    assert ("2026-11-09 06:00", "VIIRS_NOAA21") not in _clave(json.loads(op.read_text(encoding="utf-8")))
    d = json.loads(res.read_text(encoding="utf-8"))
    assert d["volcano"] == "Lascar" and d["motivo"]
    assert [(x["datetime_utc"], x["sensor"]) for x in d["records"]] == [("2026-11-09 06:00", "VIIRS_NOAA21")]


def test_cli_residuo_previo_se_une_por_clave_sin_duplicar(tmp_path):
    previo = {"volcano": "Lascar", "motivo": "x", "records": [
        _rec("2025-05-01 05:00", "MODIS_TERRA", OP), _rec("2026-11-09 06:00", "VIIRS_NOAA21", OP, vrp_mw=4.0)]}
    r, op, _, res = _cli(tmp_path, "--max-solo-operacional", "0.5", "--aplicar", residuo_previo=previo)
    assert r.returncode == 0, r.stderr
    claves = [(x["datetime_utc"], x["sensor"]) for x in json.loads(res.read_text(encoding="utf-8"))["records"]]
    assert sorted(claves) == [("2025-05-01 05:00", "MODIS_TERRA"), ("2026-11-09 06:00", "VIIRS_NOAA21")]


def test_cli_se_niega_si_las_sin_par_pasan_del_tope_y_no_escribe_nada(tmp_path):
    # 1 sin par de 2 pasadas K de VIIRS 375 en la ventana antes del corte: 0,5 > 0,10
    r, op, antes, res = _cli(tmp_path, "--max-solo-operacional", "0.10", "--aplicar")
    assert r.returncode == 2
    assert op.read_bytes() == antes and not res.exists()


# ---------------------------------------------------------------- experiments/_s180_reemplazo_via/aplicar_via.py
def _aplicar_mod():
    sys.path.insert(0, str(ROOT / "experiments" / "_s180_reemplazo_via"))
    import aplicar_via
    return aplicar_via


def _armar(tmp_path, monkeypatch, op_records, union_records):
    import gzip
    AV = _aplicar_mod()
    monkeypatch.setattr(AV, "TIER_A", ["Lascar"])
    datos, union, res = tmp_path / "datos", tmp_path / "union", tmp_path / "res"
    datos.mkdir(); union.mkdir()
    (datos / "Lascar.json").write_text(json.dumps(_store(op_records), indent=2), encoding="utf-8")
    (union / "Lascar.json.gz").write_bytes(gzip.compress(json.dumps(_store(union_records)).encode()))
    return AV, datos, union, res


def test_aplicar_via_ensayo_no_escribe_y_cuenta_el_k_restante(tmp_path, monkeypatch):
    AV, datos, union, res = _armar(tmp_path, monkeypatch, _op()["records"], _re()["records"])
    antes = (datos / "Lascar.json").read_bytes()
    inf = AV.correr(["VIIRS375"], datos, res, union, 0.6, aplicar=False, fecha="2026-11-11")
    assert (datos / "Lascar.json").read_bytes() == antes and not res.exists()
    i = inf["familias"]["VIIRS375"]["volcanes"]["Lascar"]
    assert i["k_restante_antes_del_corte"] == 0 and i["sin_par_apartados"] == 1


def test_aplicar_via_todo_o_nada_si_pasa_el_tope(tmp_path, monkeypatch):
    AV, datos, union, res = _armar(tmp_path, monkeypatch, _op()["records"], _re()["records"])
    antes = (datos / "Lascar.json").read_bytes()
    inf = AV.correr(["MODIS", "VIIRS375"], datos, res, union, 0.10, aplicar=True, fecha="2026-11-11")
    assert inf["aplicado"] is False and inf["familias"]["VIIRS375"]["rehusados"] == ["Lascar"]
    # nada escrito, tampoco la familia que si cumplia
    assert "MODIS" in inf["familias"] and not res.exists()
    assert (datos / "Lascar.json").read_bytes() == antes


def test_aplicar_via_escribe_serie_y_residuo(tmp_path, monkeypatch):
    AV, datos, union, res = _armar(tmp_path, monkeypatch, _op()["records"], _re()["records"])
    inf = AV.correr(["VIIRS375"], datos, res, union, 0.6, aplicar=True, fecha="2026-11-11")
    assert inf["aplicado"] is True
    serie = _clave(json.loads((datos / "Lascar.json").read_text(encoding="utf-8")))
    assert serie[("2026-11-09 05:00", "VIIRS_NOAA20")]["vrp_mw"] == 10.0
    r = json.loads((res / "Lascar.json").read_text(encoding="utf-8"))
    assert [(x["datetime_utc"], x["sensor"]) for x in r["records"]] == [("2026-11-09 06:00", "VIIRS_NOAA21")]
