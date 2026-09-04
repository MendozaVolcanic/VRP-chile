# -*- coding: utf-8 -*-
"""Guard S133 — el reproc-watchdog no vigila workflows que ya no existen (issue #567).

POR QUÉ. `listRepoWorkflows` devuelve también los workflows BORRADOS del repo: GitHub
conserva la entidad para poder seguir mostrando su historial de corridas. Medido el
2026-09-03 sobre MendozaVolcanic/VRP-chile, `reproc-f28-pp-saturation.yml` —archivo
inexistente en `.github/workflows/` desde mayo— seguía apareciendo con
`state: "active"` y su última corrida fallida (2026-05-23) hacía que el watchdog
comentara la issue #567 una vez por hora, 22 veces. El daño no es la molestia: ese
ruido tapa la alerta real cuando llegue.

Filtrar por `state == "active"` NO habría servido (la evidencia de arriba lo refuta),
así que la fuente de verdad de «existe» pasó a ser el repo. Este guard no comprueba
que el texto diga eso: **ejecuta** las dos funciones puras del script inline en Node
con casos que reproducen el defecto. Lección S126: un cambio de comportamiento
necesita un test que falle sin el cambio.
"""
import io
import json
import os
import re
import shutil
import subprocess

import pytest
import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WATCHDOG = os.path.join(ROOT, ".github", "workflows", "reproc-watchdog.yml")

INICIO = "// --- SELECCION PURA"
FIN = "// --- FIN SELECCION PURA ---"


@pytest.fixture(scope="module")
def wf():
    # io.open + encoding explícito: en Windows el default cp1252 revienta con los
    # acentos y las flechas del YAML (constraint de encoding del proyecto).
    with io.open(WATCHDOG, encoding="utf-8") as fh:
        return yaml.safe_load(fh.read())


@pytest.fixture(scope="module")
def bloque_puro(wf):
    script = wf["jobs"]["vigilar"]["steps"][0]["with"]["script"]
    assert INICIO in script and FIN in script, (
        "el script inline perdió los marcadores de la sección pura; sin ellos este "
        "guard no puede ejecutar la lógica real")
    return script[script.index(INICIO):script.index(FIN) + len(FIN)]


def _node(bloque, harness):
    node = shutil.which("node")
    if node is None:
        pytest.skip("node no disponible en este entorno")
    out = subprocess.run([node, "-e", bloque + "\n" + harness],
                         capture_output=True, text=True, cwd=ROOT)
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout.strip().splitlines()[-1])


def test_a43_key_on_quoteada():
    """La key del trigger tiene que ser el string "on", no el booleano True (A43)."""
    with io.open(WATCHDOG, encoding="utf-8") as fh:
        claves = list(yaml.safe_load(fh.read()).keys())
    assert "on" in claves, f"la key del trigger parseó como {claves} (falta quotear \"on\":)"
    assert not any(k is True for k in claves)


def test_watchdog_ignora_workflow_borrado(bloque_puro):
    """El caso exacto de la issue #567: la API lo da `active`, el repo ya no lo tiene."""
    api = [
        {"path": ".github/workflows/reproc-f28-pp-saturation.yml",
         "state": "active", "name": "f28 borrado"},
        {"path": ".github/workflows/reproc-s133-b22-ab.yml",
         "state": "active", "name": "b22 vivo"},
    ]
    repo = [".github/workflows/reproc-s133-b22-ab.yml",
            ".github/workflows/reproc-watchdog.yml",
            ".github/workflows/nrt.yml"]
    sel = _node(bloque_puro, "console.log(JSON.stringify("
                "seleccionarVigilados(%s, %s).map(w => w.path)));"
                % (json.dumps(api), json.dumps(repo)))
    assert sel == [".github/workflows/reproc-s133-b22-ab.yml"], (
        "el watchdog volvió a vigilar un workflow borrado del repo")


def test_watchdog_conserva_los_filtros_previos(bloque_puro):
    """No se perdieron las exclusiones que ya existían: _archive/ y el propio watchdog."""
    api = [{"path": p, "name": p} for p in [
        ".github/workflows/_archive/reproc-f28-v3.yml",
        ".github/workflows/reproc-watchdog.yml",
        ".github/workflows/nrt.yml",
        ".github/workflows/reproc-chunked.yml",
    ]]
    repo = [w["path"] for w in api]  # todos existen en el repo
    sel = _node(bloque_puro, "console.log(JSON.stringify("
                "seleccionarVigilados(%s, %s).map(w => w.path)));"
                % (json.dumps(api), json.dumps(repo)))
    assert sel == [".github/workflows/reproc-chunked.yml"]


@pytest.mark.parametrize("run,dias,espera", [
    # una corrida fallida reciente sí se reporta
    ({"status": "completed", "conclusion": "failure", "created_at": "2026-09-03T00:00:00Z"},
     0.2, "fallida"),
    # la misma falla, pero de hace 100 días: ya no es accionable (A/B de una sola vez
    # que jamás va a volver a correr en verde → issue que nunca cierra)
    ({"status": "completed", "conclusion": "failure", "created_at": "2026-09-03T00:00:00Z"},
     100, None),
    # verde y cancelada nunca son problema
    ({"status": "completed", "conclusion": "success", "created_at": "2026-09-03T00:00:00Z"},
     0.2, None),
    ({"status": "completed", "conclusion": "cancelled", "created_at": "2026-09-03T00:00:00Z"},
     0.2, None),
    # en curso hace 9 h = colgada (el techo de GitHub es 6 h por job)
    ({"status": "in_progress", "conclusion": None, "created_at": "2026-09-03T00:00:00Z"},
     9 / 24, "colgada"),
    # en curso hace 2 h = todavía normal
    ({"status": "in_progress", "conclusion": None, "created_at": "2026-09-03T00:00:00Z"},
     2 / 24, None),
])
def test_evaluar_corrida(bloque_puro, run, dias, espera):
    ahora = "new Date('2026-09-03T00:00:00Z').getTime() + %f*86400000" % dias
    got = _node(bloque_puro, "console.log(JSON.stringify(evaluarCorrida(%s, %s, 7, 14)));"
                % (json.dumps(run), ahora))
    assert (got or {}).get("tipo") == espera


def test_la_ventana_de_antiguedad_esta_declarada(wf):
    """El bound de antigüedad tiene que existir y ser finito: sin él, el ruido es perpetuo."""
    script = wf["jobs"]["vigilar"]["steps"][0]["with"]["script"]
    m = re.search(r"MAX_DIAS_ANTIGUEDAD\s*=\s*(\d+)", script)
    assert m, "desapareció MAX_DIAS_ANTIGUEDAD del watchdog"
    assert 1 <= int(m.group(1)) <= 60


def test_la_verdad_de_existencia_sale_del_repo(wf):
    """El script lee los archivos reales de .github/workflows, no confía en `state`."""
    script = wf["jobs"]["vigilar"]["steps"][0]["with"]["script"]
    assert "repos.getContent" in script and "'.github/workflows'" in script, (
        "el watchdog dejó de derivar la lista de workflows vivos del repo")
    assert "core.setFailed" in script, (
        "sin abortar al fallar getContent, el watchdog volvería a vigilar fantasmas")
