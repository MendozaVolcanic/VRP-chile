# -*- coding: utf-8 -*-
"""S153: ningun perfil derivado de la replica sigue en silencio la adopcion de K.

POR QUE. 51 perfiles hacen `extends: mirova_equivalent`: brazos de A/B ya corridos y evaluados, sondas, el
laboratorio. Cuando la replica adopto K (Test 1 integrado apagado, conectiva `max`, banda 22 primaria; regla
experiments/_s151_prereg_fk_11/REGLA_ADOPCION.md, #848), 46 de ellos pasaron a resolver K sin que nadie los
tocara. `_s146_ab_control`, que en los A/B era «produccion (C0)», habria pasado a ser K: cualquier
re-evaluacion o test que lo usara mediria otra cosa sin dar error. Es el defecto de A117 («un perfil derivado
se vigila por direccion, no por valor») y el mismo que S150 resolvio congelando `experimental.yaml`.

QUE SE HIZO. Cada perfil derivado escribe en su propio YAML los tres flags de K, con el valor que tenia antes de
la adopcion (comprobado en S153 resolviendo los 92 perfiles contra `origin/main`: los 91 que no son produccion
resuelven identico). El brazo K del A/B (`_s149_ab_sin_test1_b22_max`) ya los declaraba con los valores de K.

QUE FIJA ESTE GUARD. (1) Todo perfil que extiende `mirova_equivalent` declara los tres flags en la seccion de
donde los lee `pipeline/profile.py`, asi que un cambio futuro de la replica no se le filtra. (2) El codigo los
resuelve tal como estan declarados (VRP_PROFILE, nunca el YAML: A89). (3) El ancla de los tests escritos sobre
la produccion de antes de K (tests/produccion_pre_k.py) sigue siendo «produccion menos K», y su parche llega a
los tres procesadores.

LAS DOS PREGUNTAS DEL INSTRUMENTO. Si alguien agrega un perfil derivado sin los tres flags, (1) cae; el control
negativo de abajo muestra que el verificador detecta la falta. Si la clave queda en la seccion equivocada, (2)
cae, porque compara contra lo resuelto y no contra lo escrito.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from produccion_pre_k import FLAGS_K, PERFIL, PROCESADORES, produccion_pre_k, valores  # noqa: E402

PERFILES = ROOT / "pipeline" / "profiles"
# clave del YAML -> (constante de pipeline.profile, secciones donde la lee el codigo)
CLAVES_K = {
    "enable_test1_path": ("ENABLE_TEST1_PATH", ("paths",)),                        # profile.py, _p.get
    "enable_tests_23_prose_branch": ("ENABLE_TESTS_23_PROSE_BRANCH", ("paths",)),  # profile.py, _p.get
    "enable_modis_b22_primary": ("ENABLE_MODIS_B22_PRIMARY", ("raiz", "paths")),   # _cfg.get, luego _p.get
}


def _derivados():
    out = {}
    for f in sorted(PERFILES.glob("*.yaml")):
        cfg = yaml.safe_load(f.read_text(encoding="utf-8"))
        if isinstance(cfg, dict) and cfg.get("extends") == "mirova_equivalent":
            out[f.stem] = cfg
    return out


def _declarado(cfg, clave):
    """Valor que el YAML propio del perfil declara para `clave`, en el orden en que el codigo lo lee; None si no."""
    for seccion in CLAVES_K[clave][1]:
        bloque = cfg if seccion == "raiz" else (cfg.get(seccion) or {})
        if clave in bloque:
            return bloque[clave]
    return None


def _faltantes(cfg):
    return [c for c in CLAVES_K if _declarado(cfg, c) is None]


def test_hay_perfiles_derivados_que_vigilar():
    assert len(_derivados()) >= 51


def test_todo_perfil_derivado_declara_los_tres_flags_de_k():
    malos = {n: _faltantes(c) for n, c in _derivados().items() if _faltantes(c)}
    assert not malos, (
        f"perfiles que heredarian K (o el proximo cambio de la replica) en silencio: {malos}. Declarar los tres "
        "flags en su YAML, con el valor que corresponda a lo que el perfil significa (S153, A117)")


def test_control_negativo_el_verificador_ve_la_falta():
    cfg = {"extends": "mirova_equivalent", "paths": {"enable_test1_path": True}}
    assert _faltantes(cfg) == ["enable_tests_23_prose_branch", "enable_modis_b22_primary"]
    # en la seccion equivocada no cuenta: thresholds no es de donde los lee el codigo
    cfg = {"extends": "mirova_equivalent", "thresholds": {k: False for k in CLAVES_K}}
    assert _faltantes(cfg) == list(CLAVES_K)


_LEER_TODOS = """
import importlib, json, os, sys
nombres = json.loads(sys.argv[1]); out = {}
import pipeline.profile as p
for n in nombres:
    os.environ["VRP_PROFILE"] = n
    importlib.reload(p)
    out[n] = {k: getattr(p, k) for k in %r}
print("@@" + json.dumps(out))
""" % (FLAGS_K,)


def test_el_codigo_resuelve_cada_perfil_derivado_como_lo_declara():
    derivados = _derivados()
    r = subprocess.run([sys.executable, "-c", _LEER_TODOS, json.dumps(sorted(derivados))], capture_output=True,
                       text=True, cwd=ROOT, env=dict(os.environ, PYTHONIOENCODING="utf-8"), check=True)
    resuelto = json.loads([l for l in r.stdout.splitlines() if l.startswith("@@")][0][2:])
    malos = {}
    for n, cfg in derivados.items():
        for clave, (const, _sec) in CLAVES_K.items():
            if resuelto[n][const] != bool(_declarado(cfg, clave)):
                malos.setdefault(n, {})[const] = (resuelto[n][const], _declarado(cfg, clave))
    assert not malos, f"(resuelto, declarado): {malos}"


def test_el_ancla_de_los_tests_es_la_produccion_de_antes_de_k():
    vals = valores()  # exige que el ancla difiera de produccion exactamente en FLAGS_K
    assert vals == {"ENABLE_TEST1_PATH": True, "ENABLE_TESTS_23_PROSE_BRANCH": False,
                    "ENABLE_MODIS_B22_PRIMARY": False}
    cfg = yaml.safe_load((PERFILES / f"{PERFIL}.yaml").read_text(encoding="utf-8"))
    assert cfg["extends"] == "mirova_equivalent"


def test_el_parche_del_ancla_llega_a_los_tres_procesadores_y_se_retira():
    """A116: el parche tiene que mover algo. Adentro, la deteccion de antes de K; afuera, otra vez K."""
    import importlib
    mods = [importlib.import_module(m) for m in PROCESADORES]
    antes = {(m.__name__, k): getattr(m, k) for m in mods for k in FLAGS_K if hasattr(m, k)}
    # los tres procesadores leen el Test 1 y la conectiva; la banda 22 solo process_modis
    assert len(antes) == 7, sorted(antes)
    with produccion_pre_k() as vals:
        adentro = {(m.__name__, k): getattr(m, k) for m in mods for k in FLAGS_K if hasattr(m, k)}
    assert all(adentro[c] == vals[c[1]] for c in adentro)
    assert {(m.__name__, k): getattr(m, k) for m in mods for k in FLAGS_K if hasattr(m, k)} == antes
