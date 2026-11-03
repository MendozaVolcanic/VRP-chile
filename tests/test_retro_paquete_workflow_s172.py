# -*- coding: utf-8 -*-
"""S172/S173: workflow, plan de trozos y C-via por trozo de la prueba retrospectiva del paquete (pre-registro SELLADO
experiments/_s172_prereg_retro/PREREGISTRO_RETRO_PAQUETE.md, tag s173-prereg-retro-sellado, §6 y §10).

POR QUÉ. El workflow corre horas de runner sobre el histórico: si autentica con usuario y clave bloquea la cuenta
(A71); si no instala pyproj la vía vuelve a K en silencio y el job sale verde; si hiciera push a main pisaría datos;
si partiera mal los trozos Chillán se cortaría por tiempo (§10.2) o Tupungatito entraría donde la referencia no lo
cubre (§3.2). Cada prueba fija una de esas cosas, leyendo el yml como lo lee GitHub y ejecutando lo ejecutable (A116).

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) Los conteos de jobs son los del §10.3 del pre-registro (3, 47, 30 y 176), no
otros elegidos aquí. (2) Cada guarda tiene su caso que debe fallar: perfil ajeno, ventana solapada, la línea de
asserts del paso con el perfil de la sombra, C-via con un record sin la marca, con un trozo vacío y con el perfil K
encendido.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WF = ROOT / ".github" / "workflows" / "reproc-retro-paquete.yml"
EXP = ROOT / "experiments" / "_s172_retro_paquete"
sys.path.insert(0, str(EXP))

# mutar_leer_retro.py corre estas pruebas contra una copia mutada (CONTROLES_VIA_MODULO)
import importlib.util as _ilu  # noqa: E402
_spec = _ilu.spec_from_file_location("controles_via_bajo_prueba",
                                     os.environ.get("CONTROLES_VIA_MODULO") or str(EXP / "controles_via.py"))
CV = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(CV)
import plan_trozos as PT  # noqa: E402


def _wf():
    return yaml.safe_load(WF.read_text(encoding="utf-8"))


def _texto():
    return WF.read_text(encoding="utf-8")


# ------------------------------------------------------------------------------------------- workflow
def test_on_entre_comillas_y_solo_dispatch():
    assert re.search(r'^"on":', _texto(), re.M)
    d = _wf()
    assert list(d["on"]) == ["workflow_dispatch"]


def test_solo_token_y_corte_si_viene_vacio():
    t = _texto()
    assert "EARTHDATA_USERNAME" not in t and "EARTHDATA_PASSWORD" not in t
    paso = [s for s in _wf()["jobs"]["reproc"]["steps"] if s.get("id") == "correr"][0]
    assert paso["env"]["EARTHDATA_TOKEN"] == "${{ secrets.EARTHDATA_TOKEN }}"
    run = paso["run"]
    i_corte, i_pipeline = run.index('if [ -z "$EARTHDATA_TOKEN" ]'), run.index("scripts/run_pipeline.py")
    assert i_corte < i_pipeline and "exit 1" in run[i_corte:run.index("fi", i_corte)]


def test_pyproj_instalado_y_comprobado():
    pasos = _wf()["jobs"]["reproc"]["steps"]
    inst = [s for s in pasos if s.get("name") == "Install deps"][0]["run"]
    assert re.search(r"pip install [^\n]*\bpyproj\b", inst)
    nombres = [s.get("name") for s in pasos]
    assert nombres.index("Comprobar pyproj") < nombres.index("Reprocesar los tramos del trozo")


def test_no_hace_push_ni_commit_y_permisos_de_lectura():
    t = _texto()
    assert not re.search(r"\bgit\s+(push|commit|add)\b", t)
    assert set(_wf()["jobs"]) == {"plan", "reproc"}
    assert _wf()["permissions"] == {"contents": "read"}


def test_paralelismo_timeout_runner_y_artifacts():
    d = _wf()
    r = d["jobs"]["reproc"]
    assert r["strategy"]["max-parallel"] <= 6 and r["strategy"]["fail-fast"] is False
    paso = [s for s in r["steps"] if s.get("id") == "correr"][0]
    assert paso["timeout-minutes"] >= 143 and r["timeout-minutes"] >= paso["timeout-minutes"]   # A15: 1,3 x 110
    assert d["jobs"]["plan"]["runs-on"] == r["runs-on"] == "ubuntu-24.04"
    subidas = [s for s in r["steps"] if str(s.get("uses", "")).startswith("actions/upload-artifact")]
    assert len(subidas) == 2 and all(s["with"]["retention-days"] == 30 for s in subidas)
    trozo = [s for s in subidas if s["name"] == "Guardar el trozo"][0]
    assert "if" not in trozo   # un trozo con salida distinta de 0 no se sube como hecho
    assert "github.run_attempt" in trozo["with"]["name"]


def test_el_plan_lo_arma_plan_trozos():
    paso = [s for s in _wf()["jobs"]["plan"]["steps"] if s.get("id") == "split"][0]
    assert "experiments/_s172_retro_paquete/plan_trozos.py" in paso["run"]


def _linea_asserts():
    run = [s for s in _wf()["jobs"]["reproc"]["steps"] if s.get("id") == "correr"][0]["run"]
    linea = [x for x in run.splitlines() if "import sys, pipeline.profile as p" in x][0]
    return re.search(r'python -c "(.*)"\s*$', linea).group(1)


@pytest.mark.parametrize("perfil,ok", [("_s172_retro_paquete", True), ("_s172_retro_k", True),
                                       ("sombra_codigo_mirova", False), ("mirova_equivalent", False)])
def test_la_linea_de_asserts_del_paso_acepta_solo_los_perfiles_de_la_retro(perfil, ok):
    env = dict(os.environ, VRP_PROFILE=perfil, PYTHONDONTWRITEBYTECODE="1")
    r = subprocess.run([sys.executable, "-c", _linea_asserts()], cwd=ROOT, env=env, capture_output=True, text=True)
    assert (r.returncode == 0) == ok, (perfil, r.stdout, r.stderr[-500:])


# ------------------------------------------------------------------------------------------- plan de trozos
V11 = ",".join(PT.TIER_A)
V10 = ",".join(v for v in PT.TIER_A if v != "Tupungatito")
OTROS9 = [v for v in PT.TIER_A if v not in ("Lascar", "NevadosDeChillan")]
D3 = ("2026-10-01:2026-10-16,Lascar@2026-02-01:2026-03-31,NevadosDeChillan@2026-02-01:2026-03-31,"
      + ",".join(f"{v}@2026-02-24:2026-02-24,{v}@2026-03-02:2026-03-02,{v}@2026-03-20:2026-03-20" for v in OTROS9))


@pytest.mark.parametrize("perfil,vols,vent,n", [
    ("_s172_retro_paquete", "Lascar", "2025-06-15:2025-06-15,2026-02-10:2026-02-10,2026-10-05:2026-10-05", 3),  # D1
    ("_s172_retro_paquete", V11, "2026-02-01:2026-03-31,2026-10-01:2026-10-16", 47),                             # D2
    ("_s172_retro_k", V11, D3, 30),                                                                              # D3
    ("_s172_retro_paquete", V10, "2025-02-15:2025-12-31", 176),                                                  # D4
])
def test_los_conteos_de_jobs_son_los_del_preregistro(perfil, vols, vent, n):
    jobs, _ = PT.planificar(perfil, vols, vent)
    assert len(jobs) == n


def test_chillan_en_trozos_de_10_y_los_demas_de_20():
    jobs, _ = PT.planificar("_s172_retro_paquete", V10, "2025-02-15:2025-12-31")
    assert max(j["dias"] for j in jobs if j["vol"] == "NevadosDeChillan") == 10
    assert max(j["dias"] for j in jobs if j["vol"] != "NevadosDeChillan") == 20
    assert {j["minimo"] for j in jobs} == {"0.90"} and {j["tramo"] for j in jobs} == {"R25"}


def test_tupungatito_desde_el_23_de_febrero_y_fuera_de_2025():
    jobs, saltados = PT.planificar("_s172_retro_paquete", "Tupungatito", "2026-02-01:2026-03-31")
    assert min(j["start"] for j in jobs) == "2026-02-23"
    with pytest.raises(PT.Rehusado):
        PT.planificar("_s172_retro_paquete", "Tupungatito", "2025-02-15:2025-12-31")


def test_un_job_no_mezcla_tramos_y_el_perfil_k_espera_k():
    jobs, _ = PT.planificar("_s172_retro_k", V11, D3)
    for j in jobs:
        dias = [t.split(":")[0] for t in j["tramos"].split()]
        assert len({PT.tramo_de(d) for d in dias}) == 1
        assert j["esperado"] == "k" and j["minimo"] == "1.0"


@pytest.mark.parametrize("perfil,vols,vent", [
    ("mirova_equivalent", "Lascar", "2026-02-01:2026-02-10"),
    ("sombra_codigo_mirova", "Lascar", "2026-02-01:2026-02-10"),
    ("_s172_retro_paquete", "Lascar", "2026-02-01:2026-02-10,2026-02-05:2026-02-12"),   # solapadas
    ("_s172_retro_paquete", "Calbuco", "2026-02-01:2026-02-10"),                       # no es Tier A
    ("_s172_retro_paquete", "Lascar", "2026-02-10:2026-02-01"),                        # al revés
])
def test_el_plan_rehusa(perfil, vols, vent):
    with pytest.raises(PT.Rehusado):
        PT.planificar(perfil, vols, vent)


# ------------------------------------------------------------------------------------------- C-via
def _carpeta(tmp_path, recs):
    (tmp_path / "Lascar.json").write_text(json.dumps({"records": recs}), encoding="utf-8")
    return tmp_path


def _r(sensor, marca="__no__"):
    r = {"sensor": sensor}
    if marca != "__no__":
        r["via_codigo_mirova"] = marca
    return r


TRES = ("MODIS_AQUA", "VIIRS_NOAA20", "VIIRS_NOAA20_750")


def test_cvia_verde_con_las_tres_vias(tmp_path):
    c = CV.contar(_carpeta(tmp_path, [_r(s, True) for s in TRES]))
    assert CV.revisar(c)[0] == 0


def test_cvia_rojo_con_un_record_sin_la_marca_en_2026(tmp_path):
    recs = [_r(s, True) for s in TRES for _ in range(99)] + [_r("VIIRS_SNPP", "sin_grilla")]
    c = CV.contar(_carpeta(tmp_path, recs))
    assert CV.revisar(c, minimo=1.0)[0] == 3
    assert CV.revisar(c, minimo=0.90)[0] == 0      # en 2025 el runner sólo avisa bajo 90 %


def test_cvia_rojo_si_la_via_no_corrio(tmp_path):
    c = CV.contar(_carpeta(tmp_path, [_r(s) for s in TRES]))
    assert CV.revisar(c, minimo=0.90)[0] == 3


def test_cvia_rojo_con_trozo_vacio_y_aviso_con_sensor_vacio(tmp_path):
    """VPR940-08: en un trozo de 1 a 3 días un sensor puede no traer records con datos válidos (la vía descarta sin
    record, regla de cobertura). Ya no deja rojo el trozo: avisa y lo marca en la salida, y el trozo se sube; lo
    decide C-cobertura en la lectura. Un trozo sin ningún record sigue rojo."""
    assert CV.revisar(CV.contar(_carpeta(tmp_path, [])))[0] == 4
    c = CV.contar(_carpeta(tmp_path, [_r("MODIS_TERRA", True)]))
    codigo, lineas = CV.revisar(c)
    assert codigo == 0
    assert any(x.startswith("::warning::") and "V375" in x for x in lineas)
    assert sum(x.startswith("SENSOR_VACIO ") for x in lineas) == 2


def test_cvia_perfil_k_no_admite_la_marca(tmp_path):
    assert CV.revisar(CV.contar(_carpeta(tmp_path, [_r(s) for s in TRES])), esperado="k")[0] == 0
    c = CV.contar(_carpeta(tmp_path, [_r(s) for s in TRES] + [_r("MODIS_AQUA", True)]))
    assert CV.revisar(c, esperado="k")[0] == 3


def test_cvia_la_convencion_de_sensores_es_la_del_proyecto():
    assert [CV.sensor(s) for s in ("MODIS_TERRA", "VIIRS_SNPP", "VIIRS_NOAA21", "VIIRS_NOAA20_750", "otro")] == \
        ["MODIS", "V375", "V375", "V750", None]
