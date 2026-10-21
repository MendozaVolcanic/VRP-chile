# -*- coding: utf-8 -*-
"""Guard S158: el reproc-watchdog no reabre corridas que ya se juzgaron (issue #876).

POR QUÉ. El watchdog reporta la ÚLTIMA corrida de cada reproceso si terminó en falla, y
sólo deja de reportarla cuando llega una corrida más nueva. Pero hay corridas que se
juzgan sin relanzarse: la repetición D1 de la caja (38698329137, evaluada con
`--repeticion`) y la prueba corta del A/B de D25 (39510227734, roja sólo porque su
recolectar cuenta como faltantes a los diez volcanes que la ventana no corre). Cerrar el
issue no basta: a la hora siguiente el watchdog lo reabre con las mismas dos corridas, y
ese ruido es justo el que tapa la falla verdadera (mismo daño que #567 y #824).

El arreglo es una lista en el repo, `.github/reproc-watchdog-juzgadas.json`, con el id
y el INTENTO de cada corrida juzgada, el motivo y dónde quedó juzgada. La exención es
estrecha a propósito: (a) sólo vale para una corrida TERMINADA, nunca para un job
colgado; (b) vale para ese intento, así que una corrida relanzada que vuelve a fallar se
reporta; (c) una entrada sin motivo o sin referencia se rechaza, para que la lista no se
vuelva un lugar donde esconder fallas.

Como el guard de S157, este EJECUTA las funciones puras del script inline en Node.
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
JUZGADAS = os.path.join(ROOT, ".github", "reproc-watchdog-juzgadas.json")

INICIO = "// --- SELECCION PURA"
FIN = "// --- FIN SELECCION PURA ---"


@pytest.fixture(scope="module")
def script():
    with io.open(WATCHDOG, encoding="utf-8") as fh:
        wf = yaml.safe_load(fh.read())
    return wf["jobs"]["vigilar"]["steps"][0]["with"]["script"]


@pytest.fixture(scope="module")
def bloque_puro(script):
    assert INICIO in script and FIN in script
    return script[script.index(INICIO):script.index(FIN) + len(FIN)]


def _node(bloque, harness):
    node = shutil.which("node")
    if node is None:
        pytest.skip("node no disponible en este entorno")
    out = subprocess.run([node, "-e", bloque + "\n" + harness],
                         capture_output=True, text=True, encoding="utf-8", cwd=ROOT)
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout.strip().splitlines()[-1])


LISTA_JS = r"""
const lista = parsearJuzgadas(JSON.stringify({juzgadas: [
  {run_id: 38698329137, run_attempt: 1, motivo: 'repeticion D1 ya evaluada',
   referencia: 'issue #876'}]}));
const ahora = Date.parse('2026-10-21T03:00:00Z');
"""


def test_juzgada_terminada_no_se_reporta_y_sin_lista_si(bloque_puro):
    """La corrida juzgada no se reporta; la MISMA corrida sin la lista sí (control, A116)."""
    got = _node(bloque_puro, LISTA_JS + r"""
const r = {id: 38698329137, run_attempt: 1, status: 'completed', conclusion: 'failure',
           created_at: '2026-10-15T07:22:38Z', run_started_at: '2026-10-15T07:22:38Z'};
console.log(JSON.stringify({con: evaluarCorrida(r, [], ahora, 7, 14, 72, lista),
                            sin: evaluarCorrida(r, [], ahora, 7, 14, 72)}));
""")
    assert got["sin"] is not None and got["sin"]["tipo"] == "fallida", (
        "sin la lista la corrida tiene que dar fallida: si no, la prueba de abajo no mide nada")
    assert got["con"] is None


def test_relanzada_que_vuelve_a_fallar_se_reporta(bloque_puro):
    """El juicio vale para un intento: el intento 2 de la misma corrida se vigila de nuevo."""
    got = _node(bloque_puro, LISTA_JS + r"""
const r = {id: 38698329137, run_attempt: 2, status: 'completed', conclusion: 'failure',
           created_at: '2026-10-15T07:22:38Z', run_started_at: '2026-10-21T01:00:00Z'};
console.log(JSON.stringify(evaluarCorrida(r, [], ahora, 7, 14, 72, lista)));
""")
    assert got is not None and got["tipo"] == "fallida"


def test_la_lista_no_exime_un_job_colgado(bloque_puro):
    """Una corrida en curso con un job sobre el techo se reporta aunque su id esté juzgado."""
    got = _node(bloque_puro, LISTA_JS + r"""
const r = {id: 38698329137, run_attempt: 1, status: 'in_progress', conclusion: null,
           created_at: '2026-10-20T16:00:00Z', run_started_at: '2026-10-20T16:00:00Z'};
const jobs = [{name: 'trozo 1', status: 'in_progress', conclusion: null,
               started_at: '2026-10-20T17:00:00Z', completed_at: null}];
console.log(JSON.stringify(evaluarCorrida(r, jobs, ahora, 7, 14, 72, lista)));
""")
    assert got is not None and got["tipo"] == "colgada"


@pytest.mark.parametrize("entrada", [
    {"run_id": 1, "run_attempt": 1, "referencia": "issue #876"},
    {"run_id": 1, "run_attempt": 1, "motivo": "   ", "referencia": "issue #876"},
    {"run_id": 1, "run_attempt": 1, "motivo": "x"},
    {"run_id": 1, "motivo": "x", "referencia": "issue #876"},
    {"run_attempt": 1, "motivo": "x", "referencia": "issue #876"},
])
def test_parsear_rechaza_entradas_incompletas(bloque_puro, entrada):
    """Sin id, intento, motivo o referencia, la lista no se acepta (no es un escondite)."""
    # Control fuera del try: una entrada completa se acepta. Sin esto, un ReferenceError
    # (función inexistente) contaría como «rechazo» y la prueba pasaría sin medir nada.
    got = _node(bloque_puro, r"""
const ok = parsearJuzgadas(%s);
let error = null;
try { parsearJuzgadas(%s); } catch (e) { error = String(e.message || e); }
console.log(JSON.stringify({ok: [...ok], error}));
""" % (json.dumps(json.dumps({"juzgadas": [
        {"run_id": 1, "run_attempt": 1, "motivo": "x", "referencia": "issue #876"}]})),
       json.dumps(json.dumps({"juzgadas": [entrada]}))))
    assert got["ok"] == ["1:1"], "el control no se aceptó: la prueba no mide el rechazo"
    assert got["error"], "parsearJuzgadas aceptó una entrada incompleta: %s" % entrada


def test_el_archivo_del_repo_es_valido_y_trae_las_dos_de_876(bloque_puro):
    """La lista commiteada pasa el mismo parser que usa el watchdog y trae las dos de #876."""
    with io.open(JUZGADAS, encoding="utf-8") as fh:
        texto = fh.read()
    got = _node(bloque_puro, r"""
const s = parsearJuzgadas(%s);
console.log(JSON.stringify([...s].sort()));
""" % json.dumps(texto))
    assert "38698329137:1" in got
    assert "39510227734:1" in got


def test_el_workflow_lee_la_lista_y_la_pasa_a_evaluar(script):
    """El script lee la lista desde el repo y se la pasa a evaluarCorrida (frontera de palabra, A92)."""
    assert re.search(r"path:\s*'\.github/reproc-watchdog-juzgadas\.json'", script), (
        "el watchdog no lee .github/reproc-watchdog-juzgadas.json")
    assert re.search(r"(?<![A-Za-z0-9_])parsearJuzgadas\s*\(", script.split(FIN)[1]), (
        "fuera del bloque puro nadie llama a parsearJuzgadas")
    llamada = re.search(r"(?<![A-Za-z0-9_])evaluarCorrida\s*\(([^;]*)\);", script.split(FIN)[1])
    assert llamada and re.search(r"(?<![A-Za-z0-9_])juzgadas\s*$", llamada.group(1).strip()), (
        "la llamada real a evaluarCorrida no recibe la lista de juzgadas")
