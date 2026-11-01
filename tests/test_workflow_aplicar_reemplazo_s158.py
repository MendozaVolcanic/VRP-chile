# -*- coding: utf-8 -*-
"""Guard S158: el workflow que aplica un reemplazo de datos REGENERA sobre main, nunca rebasa.

POR QUÉ. El reemplazo del histórico con K (tarea 1.24, PR #883) chocó dos veces con el NRT, que cada hora
escribe en los mismos 11 JSON. Fusionar trozos de un JSON de 30 MB con lo que escribió el NRT no tiene una
resolución correcta, y el NRT rebasa con `-X theirs`, que hace ganar al commit que se reaplica. Lo que sí
funciona, y se usó a mano en S158, es volver a correr el script de reemplazo (determinista) sobre el main
del momento. Este workflow hace eso dentro de su bucle de reintento: si el push pierde la carrera, vuelve a
`origin/main` y regenera, en vez de rebasar.

Contrato que vigila:
1. `"on"` entre comillas (A43) y sólo `workflow_dispatch`.
2. La regeneración (el script) corre DENTRO del bucle, después de `reset --hard origin/main`.
3. No hay `rebase` ni `-X theirs` en ninguna parte.
4. Las pruebas corren antes del push, en el mismo intento.
5. Concurrencia propia, sin `cancel-in-progress`: no entra al grupo `push-main`, donde un pendiente desplaza a
   otro (GitHub guarda uno solo por grupo) y podría expulsar un NRT encolado.
6. Exige confirmación explícita y un script bajo `experiments/`.
"""
import io
import os
import re

import pytest
import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WF = os.path.join(ROOT, ".github", "workflows", "aplicar-reemplazo.yml")


@pytest.fixture(scope="module")
def texto():
    with io.open(WF, encoding="utf-8") as fh:
        return fh.read()


@pytest.fixture(scope="module")
def wf(texto):
    return yaml.safe_load(texto)


def _paso_aplicar(wf):
    pasos = wf["jobs"]["aplicar"]["steps"]
    return next(p["run"] for p in pasos if "reset --hard origin/main" in (p.get("run") or ""))


def test_on_entre_comillas_y_solo_dispatch(texto, wf):
    assert re.search(r'^"on":', texto, re.M), "A43: la clave on va entre comillas"
    assert list(wf["on"].keys()) == ["workflow_dispatch"]


def test_regenera_dentro_del_bucle_y_no_rebasa(wf):
    run = _paso_aplicar(wf)
    bucle = re.search(r"for attempt in[^\n]*\n(.*?)\n\s*done", run, re.S)
    assert bucle, "falta el bucle de reintento"
    cuerpo = bucle.group(1)
    i_reset = cuerpo.find("git reset --hard origin/main")
    i_script = cuerpo.find('bash "$SCRIPT"')
    i_tests = cuerpo.find("python -m pytest")
    i_push = cuerpo.find("git push origin HEAD:main")
    assert -1 not in (i_reset, i_script, i_tests, i_push), (i_reset, i_script, i_tests, i_push)
    assert i_reset < i_script < i_tests < i_push, "orden: reset, regenerar, probar, empujar"
    # Sólo en los comandos: los comentarios del archivo explican justamente por qué no se rebasa.
    comandos = "\n".join(p.get("run") or "" for p in wf["jobs"]["aplicar"]["steps"])
    comandos = "\n".join(l for l in comandos.splitlines() if not l.strip().startswith("#"))
    assert "rebase" not in comandos and "-X theirs" not in comandos


def test_concurrencia_propia(wf):
    c = wf["concurrency"]
    assert c["group"] != "push-main" and c["cancel-in-progress"] is False


def test_exige_confirmacion_y_script_en_experiments(wf, texto):
    entradas = wf["on"]["workflow_dispatch"]["inputs"]
    assert {"confirmacion", "script", "pruebas"} <= set(entradas)
    assert re.search(r'\[\s*"\$\{\{\s*inputs\.confirmacion\s*\}\}"\s*!=\s*"si"\s*\]', texto)
    assert re.search(r'experiments/\*', texto), "el script tiene que vivir bajo experiments/"
