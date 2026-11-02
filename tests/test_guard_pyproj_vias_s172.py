# -*- coding: utf-8 -*-
"""S172 (mini auditoría, MA172-201/301, VMA172-201): todo workflow que corre un perfil con una vía «código MIROVA»
encendida instala pyproj, y los tres operacionales lo comprueban antes de correr.

POR QUÉ. Las vías pasan cada gránulo a la grilla UTM de MIROVA con pyproj (`pipeline/mirova_v750_codigo.py`,
`remuestrear_grilla`). Si el runner no lo tiene, la vía levanta ImportError en cada gránulo, `scripts/run_pipeline.py`
atrapa la excepción por gránulo y sigue, no se escribe ningún record y el job sale VERDE: MODIS mudo en los 11 volcanes
sin que nadie lo note (el pipeline zombie del CLAUDE.md global, regla 6). Lo midió la mini auditoría en el log real del
run 41353423746 del NRT. La vía no cae a K ante una excepción, sólo ante «sin grilla», «sin MxD03» o «geo distinta».

QUÉ FIJA. (1) Para cada perfil, el valor de las tres vías se lee de pipeline.profile con su VRP_PROFILE (A89), nunca del
YAML. (2) Un workflow «corre» un perfil si llama a run_pipeline.py o fija VRP_PROFILE y nombra el perfil fuera de un
comentario; si alguno de esos perfiles tiene una vía encendida, alguna línea `pip install` del archivo trae pyproj.
(3) nrt.yml, backfill-tier-a.yml y reproc-chunked.yml, que escriben en data/mirova_equivalent/, tienen además un paso
que corre `python -c "import pyproj"` después de instalar y antes de run_pipeline.py, en el mismo job: si pyproj no se
instala, el job queda rojo en vez de verde y vacío.
La prueba se escribió en el PR A, donde sólo la sombra tiene una vía encendida; con el perfil de producción del PR B
(vía de MODIS encendida) el punto (2) daba 22 workflows sin pyproj (rojo visto, ver el mensaje del commit).
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
OPERACIONALES = ("nrt.yml", "backfill-tier-a.yml", "reproc-chunked.yml")

_LEER = """
import importlib, json, os, sys
out = {}
import pipeline.profile as p
for n in json.loads(sys.argv[1]):
    os.environ["VRP_PROFILE"] = n
    try:
        importlib.reload(p)
        out[n] = [bool(p.ENABLE_V750_CODIGO_MIROVA), bool(p.ENABLE_V375_CODIGO_MIROVA), bool(p.ENABLE_MODIS_CODIGO_MIROVA)]
    except Exception as e:
        out[n] = repr(e)
print("@@" + json.dumps(out))
"""


def perfiles_con_via(root=ROOT):
    nombres = sorted(p.stem for p in (Path(root) / "pipeline" / "profiles").glob("*.yaml"))
    r = subprocess.run([sys.executable, "-c", _LEER, json.dumps(nombres)], cwd=root, capture_output=True, text=True,
                       env=dict(os.environ, PYTHONIOENCODING="utf-8"), check=True)
    res = json.loads([ln for ln in r.stdout.splitlines() if ln.startswith("@@")][0][2:])
    return {n for n, v in res.items() if isinstance(v, list) and any(v)}


def _sin_comentarios(texto):
    return "\n".join(ln for ln in texto.splitlines() if not ln.lstrip().startswith("#"))


def _nombra(texto, nombre):
    return re.search(r"(?<![A-Za-z0-9_])" + re.escape(nombre) + r"(?![A-Za-z0-9_])", texto) is not None


def instala_pyproj(texto):
    return re.search(r"pip install[^\n]*(?<![A-Za-z0-9_])pyproj(?![A-Za-z0-9_])", texto) is not None


def workflows_sin_pyproj(root=ROOT, con_via=None):
    """{workflow: perfiles con vía que corre} de los workflows que no instalan pyproj."""
    con_via = perfiles_con_via(root) if con_via is None else con_via
    malos = {}
    for wf in sorted((Path(root) / ".github" / "workflows").glob("*.yml")):
        t = _sin_comentarios(wf.read_text(encoding="utf-8"))
        if "run_pipeline.py" not in t and "VRP_PROFILE" not in t:
            continue
        corre = sorted(n for n in con_via if _nombra(t, n))
        if corre and not instala_pyproj(t):
            malos[wf.name] = corre
    return malos


def test_hay_al_menos_un_perfil_con_via_y_se_lee_desde_pipeline_profile():
    con_via = perfiles_con_via()
    assert "sombra_codigo_mirova" in con_via, "control: la sombra tiene las tres vías encendidas"
    assert "guardia_k_modis" not in con_via and "experimental" not in con_via


def test_todo_workflow_que_corre_un_perfil_con_via_instala_pyproj():
    malos = workflows_sin_pyproj()
    assert not malos, f"workflows que corren un perfil con vía sin instalar pyproj: {malos}"


def test_control_el_instrumento_ve_un_workflow_sin_pyproj(tmp_path):
    """Las dos preguntas del instrumento: un workflow que corre la sombra sin pyproj cae; con pyproj, no."""
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    malo = "jobs:\n  a:\n    steps:\n      - run: |\n          pip install earthaccess numpy\n" \
           "          python scripts/run_pipeline.py --profile sombra_codigo_mirova\n"
    (tmp_path / ".github" / "workflows" / "x.yml").write_text(malo, encoding="utf-8")
    assert workflows_sin_pyproj(tmp_path, {"sombra_codigo_mirova"}) == {"x.yml": ["sombra_codigo_mirova"]}
    (tmp_path / ".github" / "workflows" / "x.yml").write_text(malo.replace("numpy", "numpy pyproj"), encoding="utf-8")
    assert workflows_sin_pyproj(tmp_path, {"sombra_codigo_mirova"}) == {}
    # un perfil nombrado sólo en un comentario no cuenta como «lo corre»
    solo_comentario = "# corre sombra_codigo_mirova en otra parte\njobs:\n  a:\n    steps:\n" \
                      "      - run: python scripts/run_pipeline.py --profile experimental\n"
    (tmp_path / ".github" / "workflows" / "x.yml").write_text(solo_comentario, encoding="utf-8")
    assert workflows_sin_pyproj(tmp_path, {"sombra_codigo_mirova"}) == {}


def _pasos_del_job_que_corre(wf):
    d = yaml.safe_load(wf.read_text(encoding="utf-8"))
    for job in d["jobs"].values():
        pasos = job.get("steps") or []
        if any("run_pipeline.py" in (s.get("run") or "") for s in pasos):
            return pasos
    return []


def test_los_tres_operacionales_comprueban_pyproj_antes_de_correr():
    for nombre in OPERACIONALES:
        pasos = _pasos_del_job_que_corre(ROOT / ".github" / "workflows" / nombre)
        assert pasos, nombre
        i_inst = max(i for i, s in enumerate(pasos) if instala_pyproj(s.get("run") or ""))
        i_chk = [i for i, s in enumerate(pasos) if re.search(r'python -c "import pyproj', s.get("run") or "")]
        i_run = min(i for i, s in enumerate(pasos) if "run_pipeline.py" in (s.get("run") or ""))
        assert i_chk, f"{nombre}: falta el paso que comprueba pyproj"
        assert i_inst < i_chk[0] < i_run, f"{nombre}: el paso de pyproj va después de instalar y antes de correr"
        # el paso de comprobación corre con la misma condición que la instalación (el NRT salta volcanes con un if)
        assert pasos[i_chk[0]].get("if") == pasos[i_inst].get("if"), nombre
