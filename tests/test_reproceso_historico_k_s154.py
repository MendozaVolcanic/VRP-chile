# -*- coding: utf-8 -*-
"""S154: reproceso historico con K en un perfil aislado y reemplazo de la ventana en la serie operacional.

POR QUE. Con K adoptada (#850, 2026-10-18 09:57:30 UTC), la historia de `data/mirova_equivalent/` quedo escrita
con el detector anterior. Reprocesarla con `backfill-tier-a.yml` toma el grupo `push-main` horas por ola y deja al
NRT esperando; con Chillan en erupcion eso no se acepta. La via elegida por Nicolas: reprocesar por trozos en
paralelo en un perfil aislado (`reproc-chunked.yml`, que se niega a correr contra la replica) y despues reemplazar
la ventana en los archivos operacionales con `scripts/reemplazar_ventana_reproceso.py`, probado antes de usarlo.

QUE FIJA. (1) El perfil aislado resuelve IDENTICO a la replica en todas las constantes de `pipeline.profile` salvo
el nombre y el directorio: si no, el reproceso no seria K. (2) El reemplazo es por clave (pasada, sensor) y solo
dentro de la ventana; fuera de ella no cambia nada. (3) No borra una pasada que el reproceso no trajo (un corte de
NASA no es «K no la ve»): la conserva, la informa, y si son demasiadas se niega a escribir. (4) Hereda
`first_processed_utc` como lo hace `store.append_record`. (5) Rechaza records que no vienen del perfil esperado.
"""
import copy
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.reemplazar_ventana_reproceso import reemplazar_ventana  # noqa: E402

PERFIL = "_s154_reproc_k_historico"


def _rec(dt, sensor="VIIRS_SNPP", perfil=PERFIL, **kw):
    r = {"datetime_utc": dt, "sensor": sensor, "vrp_mw": kw.pop("vrp_mw", 0.0),
         "processed_utc": kw.pop("processed_utc", "2026-10-18T12:00:00Z"),
         "regimen": {"perfil": perfil, "codigo_sha": "a" * 40, "origen": "actions"}}
    r.update(kw)
    return r


def _store(vol, records):
    return {"volcano": vol, "updated": "2026-10-18T00:00:00Z", "records": records}


def _op():
    return _store("Villarrica", [
        _rec("2025-02-14T05:00:00", perfil="mirova_equivalent", vrp_mw=1.0, first_processed_utc="2025-02-14T09:00:00Z"),
        _rec("2025-03-01T05:00:00", perfil="mirova_equivalent", vrp_mw=2.0, first_processed_utc="2025-03-01T09:00:00Z"),
        _rec("2025-03-01T05:00:00", sensor="MODIS_AQUA", perfil="mirova_equivalent", vrp_mw=3.0),
        _rec("2025-03-02T05:00:00", perfil="mirova_equivalent", vrp_mw=4.0),
        _rec("2025-04-01T05:00:00", perfil="mirova_equivalent", vrp_mw=5.0),
    ])


def _re():
    return _store("Villarrica", [
        _rec("2025-03-01T05:00:00", vrp_mw=20.0, first_processed_utc="2026-10-18T12:00:00Z"),
        _rec("2025-03-01T05:00:00", sensor="MODIS_AQUA", vrp_mw=30.0, first_processed_utc="2026-10-18T12:00:00Z"),
        _rec("2025-03-03T05:00:00", vrp_mw=60.0, first_processed_utc="2026-10-18T12:00:00Z"),
        _rec("2025-04-01T05:00:00", vrp_mw=50.0),
    ])


def _por_clave(store):
    return {(r["datetime_utc"], r["sensor"]): r for r in store["records"]}


def test_reemplaza_por_clave_solo_dentro_de_la_ventana():
    op = _op()
    nuevo, inf = reemplazar_ventana(op, _re(), "2025-02-15", "2025-03-31", PERFIL)
    k = _por_clave(nuevo)
    assert k[("2025-03-01T05:00:00", "VIIRS_SNPP")]["vrp_mw"] == 20.0
    assert k[("2025-03-01T05:00:00", "MODIS_AQUA")]["vrp_mw"] == 30.0
    # fuera de la ventana, intactos, aunque el reproceso traiga la misma clave
    assert k[("2025-02-14T05:00:00", "VIIRS_SNPP")] == _op()["records"][0]
    assert k[("2025-04-01T05:00:00", "VIIRS_SNPP")]["vrp_mw"] == 5.0
    assert inf["reemplazados"] == 2 and inf["reproceso_fuera_de_ventana"] == 1


def test_hereda_first_processed_utc_como_store():
    nuevo, _ = reemplazar_ventana(_op(), _re(), "2025-02-15", "2025-03-31", PERFIL)
    k = _por_clave(nuevo)
    assert k[("2025-03-01T05:00:00", "VIIRS_SNPP")]["first_processed_utc"] == "2025-03-01T09:00:00Z"
    # el operacional no lo tenia: no se inventa (store.append_record hace pop)
    assert "first_processed_utc" not in k[("2025-03-01T05:00:00", "MODIS_AQUA")]
    # pasada nueva: conserva el suyo
    assert k[("2025-03-03T05:00:00", "VIIRS_SNPP")]["first_processed_utc"] == "2026-10-18T12:00:00Z"


def test_agrega_pasadas_nuevas_y_conserva_las_que_el_reproceso_no_trajo():
    nuevo, inf = reemplazar_ventana(_op(), _re(), "2025-02-15", "2025-03-31", PERFIL)
    k = _por_clave(nuevo)
    assert k[("2025-03-03T05:00:00", "VIIRS_SNPP")]["vrp_mw"] == 60.0
    assert k[("2025-03-02T05:00:00", "VIIRS_SNPP")]["vrp_mw"] == 4.0   # C0 conservado, no borrado
    assert inf["agregados"] == 1
    assert inf["solo_operacional"] == 1
    assert inf["solo_operacional_claves"] == [["2025-03-02T05:00:00", "VIIRS_SNPP"]]
    assert inf["operacional_en_ventana"] == 3
    assert len(nuevo["records"]) == 6


def test_orden_por_fecha_y_no_muta_las_entradas():
    op, re_ = _op(), _re()
    op0, re0 = copy.deepcopy(op), copy.deepcopy(re_)
    nuevo, _ = reemplazar_ventana(op, re_, "2025-02-15", "2025-03-31", PERFIL)
    fechas = [r["datetime_utc"] for r in nuevo["records"]]
    assert fechas == sorted(fechas)
    assert op == op0 and re_ == re0


def test_rechaza_records_de_otro_perfil():
    re_ = _re()
    re_["records"][0]["regimen"]["perfil"] = "mirova_equivalent"
    with pytest.raises(ValueError, match="perfil"):
        reemplazar_ventana(_op(), re_, "2025-02-15", "2025-03-31", PERFIL)


def test_rechaza_volcanes_distintos():
    re_ = _re()
    re_["volcano"] = "Llaima"
    with pytest.raises(ValueError, match="volc"):
        reemplazar_ventana(_op(), re_, "2025-02-15", "2025-03-31", PERFIL)


def _cli(tmp_path, *extra):
    op, re_ = tmp_path / "op.json", tmp_path / "re.json"
    op.write_text(json.dumps(_op(), indent=2), encoding="utf-8")
    re_.write_text(json.dumps(_re(), indent=2), encoding="utf-8")
    antes = op.read_bytes()
    r = subprocess.run([sys.executable, "scripts/reemplazar_ventana_reproceso.py", "--operacional", str(op),
                        "--reproceso", str(re_), "--desde", "2025-02-15", "--hasta", "2025-03-31",
                        "--perfil-esperado", PERFIL, "--informe", str(tmp_path / "inf.json"), *extra],
                       cwd=ROOT, capture_output=True, text=True, env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    return r, op, antes


def test_cli_ensayo_no_escribe(tmp_path):
    r, op, antes = _cli(tmp_path, "--max-solo-operacional", "0.5")
    assert r.returncode == 0, r.stderr
    assert op.read_bytes() == antes
    assert json.loads((tmp_path / "inf.json").read_text(encoding="utf-8"))["aplicado"] is False


def test_cli_aplicar_escribe(tmp_path):
    r, op, _ = _cli(tmp_path, "--max-solo-operacional", "0.5", "--aplicar")
    assert r.returncode == 0, r.stderr
    k = _por_clave(json.loads(op.read_text(encoding="utf-8")))
    assert k[("2025-03-01T05:00:00", "VIIRS_SNPP")]["vrp_mw"] == 20.0


def test_cli_se_niega_si_faltan_demasiadas_pasadas(tmp_path):
    # 1 de 3 pasadas operacionales en la ventana no vino en el reproceso: 0,33 > 0,10
    r, op, antes = _cli(tmp_path, "--max-solo-operacional", "0.10", "--aplicar")
    assert r.returncode == 2
    assert op.read_bytes() == antes


# ---- el perfil aislado es la replica con otro directorio ----------------------------------------------------

def test_perfil_aislado_existe_y_escribe_en_su_propio_directorio():
    cfg = yaml.safe_load((ROOT / "pipeline" / "profiles" / f"{PERFIL}.yaml").read_text(encoding="utf-8"))
    assert cfg["extends"] == "mirova_equivalent"
    # reproc-chunked sube data/<perfil>/<Vol>.json: el directorio tiene que llamarse como el perfil
    assert cfg["output"]["data_subdir"] == PERFIL


_RESOLVER = """
import importlib, json, os, sys
out = {}
for n in sys.argv[1:]:
    os.environ["VRP_PROFILE"] = n
    import pipeline.profile as p
    p = importlib.reload(p)
    out[n] = {k: repr(getattr(p, k)) for k in dir(p) if k.isupper()}
print("@@" + json.dumps(out))
"""


def test_perfil_aislado_resuelve_identico_a_la_replica():
    r = subprocess.run([sys.executable, "-c", _RESOLVER, "mirova_equivalent", PERFIL], capture_output=True,
                       text=True, cwd=ROOT, env=dict(os.environ, PYTHONIOENCODING="utf-8"), check=True)
    res = json.loads([l for l in r.stdout.splitlines() if l.startswith("@@")][0][2:])
    a, b = res["mirova_equivalent"], res[PERFIL]
    distintos = {k for k in set(a) | set(b) if a.get(k) != b.get(k)}
    assert distintos == {"PROFILE_NAME", "DATA_SUBDIR"}, sorted(distintos)
    assert len(a) > 100   # el instrumento ve las constantes de verdad, no un modulo vacio
