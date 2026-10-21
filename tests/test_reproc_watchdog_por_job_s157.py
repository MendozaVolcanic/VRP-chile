# -*- coding: utf-8 -*-
"""Guard S157: el reproc-watchdog juzga la duración de cada JOB y no repite avisos iguales.

POR QUÉ. La auditoría S155 (F3-10, `docs/AUDIT_S155.md`, arreglo 7) midió que
`evaluarCorrida` llamaba «colgada» a una corrida por la EDAD DEL RUN (`created_at`),
cuando el techo de GitHub es de 6 h por JOB. Un reproceso por trozos de 178 jobs con
`max-parallel: 8` vive más de 30 h siendo perfectamente sano: el run 39125546355
(2026-10-18 12:01 a 2026-10-19 20:22 UTC) no tuvo ningún job sobre 2,9 h y aun así
el watchdog lo dio por «colgado sobre el techo de 6 h por job» cada hora. Y como el
texto del aviso llevaba «hace X h», cada comentario era distinto del anterior: la
issue #824 juntó 28 comentarios en 4 días. Ese ruido es el daño: tapa la falla real.

Este guard EJECUTA las funciones puras del script inline en Node (lección S126: un
cambio de comportamiento necesita un test que falle sin el cambio). El caso principal
no es inventado: reconstruye, hora a hora, el estado de los 178 jobs reales del run
39125546355 a partir de su `started_at` y `completed_at` (`tests/datos_s157/`).
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
FIXTURE = os.path.join(ROOT, "tests", "datos_s157", "watchdog_run_39125546355_jobs.json")

INICIO = "// --- SELECCION PURA"
FIN = "// --- FIN SELECCION PURA ---"


@pytest.fixture(scope="module")
def wf():
    with io.open(WATCHDOG, encoding="utf-8") as fh:
        return yaml.safe_load(fh.read())


@pytest.fixture(scope="module")
def script(wf):
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
                         capture_output=True, text=True, encoding="utf-8",
                         cwd=ROOT)
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout.strip().splitlines()[-1])


# Reconstruye el estado de cada job real a la hora `ahora`. Los jobs todavía en cola
# llevan `started_at` = creación del run: es el peor caso (GitHub puede poblar ese
# campo antes de que el job arranque), y el criterio no debe contarlos como corriendo.
REPLAY_JS = r"""
const fx = JSON.parse(require('fs').readFileSync(%s, 'utf8'));
function jobsA(ahoraMs) {
  return fx.jobs.map(j => {
    const s = Date.parse(j.started_at), e = Date.parse(j.completed_at);
    if (e <= ahoraMs) return j;
    if (s <= ahoraMs) return {...j, status: 'in_progress', conclusion: null, completed_at: null};
    return {...j, status: 'queued', conclusion: null, started_at: fx.run.created_at, completed_at: null};
  });
}
function runA(ahoraMs) {
  return {...fx.run, status: 'in_progress', conclusion: null};
}
"""


def _replay(bloque, cuerpo_js):
    return _node(bloque, (REPLAY_JS % json.dumps(FIXTURE)) + cuerpo_js)


def test_fixture_es_el_run_real():
    """El caso principal descansa en datos reales: 178 jobs, ninguno sobre 3 h."""
    with io.open(FIXTURE, encoding="utf-8") as fh:
        fx = json.load(fh)
    assert fx["run"]["id"] == 39125546355
    assert len(fx["jobs"]) == 178


def test_run_39125546355_no_es_colgado_en_ninguna_hora(bloque_puro):
    """El caso de F3-10: el run vivió ~32 h y en ninguna hora hubo un job colgado.

    Se barre cada hora desde la creación del run hasta su último job, más las dos horas
    exactas en que el watchdog viejo comentó #824 (25,6 h y 31,9 h de edad).
    """
    got = _replay(bloque_puro, r"""
const t0 = Date.parse(fx.run.created_at), t1 = Date.parse('2026-10-19T20:22:00Z');
const horas = [Date.parse('2026-10-19T13:34:43Z'), Date.parse('2026-10-19T19:57:37Z')];
for (let t = t0 + 36e5; t < t1; t += 36e5) horas.push(t);
const res = horas.map(t => ({t: new Date(t).toISOString(),
  v: evaluarCorrida(runA(t), jobsA(t), t, 7, 14)}));
// Control positivo sobre los mismos datos: si un trozo hubiese quedado corriendo desde
// la creación del run, el instrumento tiene que poder decir «colgada» (A110/A116).
const tc = Date.parse('2026-10-19T13:34:43Z');
const conColgado = jobsA(tc).map((j, i) => i === 0
  ? {...j, status: 'in_progress', conclusion: null, started_at: fx.run.created_at, completed_at: null}
  : j);
const control = evaluarCorrida(runA(tc), conColgado, tc, 7, 14);
console.log(JSON.stringify({n: res.length, malos: res.filter(x => x.v !== null), control}));
""")
    assert got["control"] is not None and got["control"]["tipo"] == "colgada", (
        "el control positivo no dio colgada: el barrido de abajo no prueba nada")
    assert got["n"] >= 30
    assert got["malos"] == [], (
        "el watchdog volvió a llamar colgado a un reproceso sano de jobs cortos: %s"
        % got["malos"][:3])


def test_job_que_pasa_el_techo_si_es_colgado(bloque_puro):
    """Un job real en curso desde hace 8 h sí es colgado, aunque los demás estén bien."""
    got = _node(bloque_puro, r"""
const ahora = Date.parse('2026-10-20T12:00:00Z');
const r = {status: 'in_progress', conclusion: null, created_at: '2026-10-20T03:00:00Z'};
const jobs = [
  {name: 'trozo 1', status: 'completed', conclusion: 'success',
   started_at: '2026-10-20T03:00:10Z', completed_at: '2026-10-20T05:00:00Z'},
  {name: 'trozo 2', status: 'in_progress', conclusion: null,
   started_at: '2026-10-20T04:00:00Z', completed_at: null},
  {name: 'trozo 3', status: 'in_progress', conclusion: null,
   started_at: '2026-10-20T10:00:00Z', completed_at: null},
];
console.log(JSON.stringify(evaluarCorrida(r, jobs, ahora, 7, 14)));
""")
    assert got is not None and got["tipo"] == "colgada"
    assert [j["name"] for j in got["jobs"]] == ["trozo 2"], (
        "el aviso tiene que nombrar el job que pasó el techo, y sólo ése")
    assert got["jobs"][0]["horas"] == pytest.approx(8.0)


def test_run_con_jobs_fallidos_es_fallida_no_colgada(bloque_puro):
    """Un run terminado en failure, de 30 h de vida y jobs cortos: fallida, nunca colgada."""
    got = _node(bloque_puro, r"""
const ahora = Date.parse('2026-10-19T20:30:00Z');
const r = {status: 'completed', conclusion: 'failure', created_at: '2026-10-18T12:01:01Z'};
const jobs = [
  {name: 'trozo 5', status: 'completed', conclusion: 'failure',
   started_at: '2026-10-19T10:00:00Z', completed_at: '2026-10-19T12:50:00Z'},
  {name: 'trozo 6', status: 'completed', conclusion: 'success',
   started_at: '2026-10-19T10:00:00Z', completed_at: '2026-10-19T11:00:00Z'},
];
console.log(JSON.stringify(evaluarCorrida(r, jobs, ahora, 7, 14)));
""")
    assert got is not None and got["tipo"] == "fallida"


def test_run_en_cola_sin_jobs_empezados_no_es_colgado(bloque_puro):
    """Un run en cola hace 10 h (concurrency o max-parallel), sin jobs corriendo: no es colgado.

    Se prueban las dos formas en que la API lo muestra: sin jobs todavía, y con jobs en
    cola que ya traen `started_at` poblado.
    """
    got = _node(bloque_puro, r"""
const ahora = Date.parse('2026-10-20T13:00:00Z');
const r = {status: 'queued', conclusion: null, created_at: '2026-10-20T03:00:00Z'};
const enCola = [{name: 'trozo 1', status: 'queued', conclusion: null,
                 started_at: '2026-10-20T03:00:05Z', completed_at: null}];
const p = {status: 'pending', conclusion: null, created_at: '2026-10-20T03:00:00Z'};
console.log(JSON.stringify([evaluarCorrida(r, [], ahora, 7, 14),
                            evaluarCorrida(r, enCola, ahora, 7, 14),
                            evaluarCorrida(p, [], ahora, 7, 14)]));
""")
    assert got == [None, None, None]


def test_sin_jobs_legibles_es_sin_dato_no_sano(bloque_puro):
    """Si la API de jobs falló (502 tras los reintentos), el run en curso queda SIN DATO.

    No puede leerse como sano: eso dejaría cerrar el issue sin haber mirado.
    """
    got = _node(bloque_puro, r"""
const r = {status: 'in_progress', conclusion: null, created_at: '2026-10-20T03:00:00Z'};
console.log(JSON.stringify(evaluarCorrida(r, null, Date.parse('2026-10-20T13:00:00Z'), 7, 14)));
""")
    assert got is not None and got["tipo"] == "sin_dato"


def test_la_linea_del_aviso_no_cambia_con_la_hora(bloque_puro):
    """El texto del aviso no lleva edades: el mismo estado da el mismo texto a cualquier hora.

    Con «hace X h» cada comentario era distinto y la deduplicación nunca habría actuado.
    """
    got = _node(bloque_puro, r"""
const wf = {name: 'Reproc por trozos'};
const r = {status: 'completed', conclusion: 'failure', created_at: '2026-10-18T12:01:01Z',
           html_url: 'https://example/runs/1'};
const a = Date.parse('2026-10-19T21:00:00Z'), b = Date.parse('2026-10-20T09:00:00Z');
const rc = {status: 'in_progress', conclusion: null, created_at: '2026-10-20T03:00:00Z',
            html_url: 'https://example/runs/2'};
const jc = [{name: 'trozo 2', status: 'in_progress', conclusion: null,
             started_at: '2026-10-20T04:00:00Z', completed_at: null}];
const c = Date.parse('2026-10-20T12:00:00Z'), d = Date.parse('2026-10-20T15:00:00Z');
console.log(JSON.stringify([
  lineaProblema(wf, r, evaluarCorrida(r, [], a, 7, 14)),
  lineaProblema(wf, r, evaluarCorrida(r, [], b, 7, 14)),
  lineaProblema(wf, rc, evaluarCorrida(rc, jc, c, 7, 14)),
  lineaProblema(wf, rc, evaluarCorrida(rc, jc, d, 7, 14))]));
""")
    assert got[0] == got[1], "la línea de una corrida fallida cambia con la hora"
    assert got[2] == got[3], "la línea de un job colgado cambia con la hora"
    assert "trozo 2" in got[2] and "2026-10-20T04:00:00Z" in got[2]
    assert "https://example/runs/2" in got[2]


def test_no_repite_un_comentario_igual(bloque_puro):
    """Se comenta sólo si el aviso cambió respecto del último del watchdog en la issue."""
    got = _node(bloque_puro, r"""
const nuevo = 'aviso A\n' + MARCA;
const viejo = 'aviso B\n' + MARCA;
const issue = {body: viejo};
const bot = b => ({body: b, user: {login: 'github-actions[bot]'}});
const hum = b => ({body: b, user: {login: 'MendozaVolcanic'}});
const casos = [
  // el último del watchdog es igual: no se comenta
  debeComentar(nuevo, issue, [bot(viejo), bot(nuevo)]),
  // igual salvo fin de línea CRLF y espacios al final: tampoco
  debeComentar(nuevo, issue, [bot('aviso A  \r\n' + MARCA + '\r\n')]),
  // un humano comentó después: se compara contra el último DEL WATCHDOG
  debeComentar(nuevo, issue, [bot(nuevo), hum('relanzo los trozos')]),
  // el aviso cambió: se comenta
  debeComentar(nuevo, issue, [bot(nuevo), bot(viejo)]),
  // sin comentarios del watchdog: se compara contra el cuerpo de la issue
  debeComentar(nuevo, {body: nuevo}, [hum('nota humana')]),
  debeComentar(nuevo, {body: viejo}, []),
  // comentarios viejos sin marca (anteriores a S157) no cuentan como del watchdog
  debeComentar(nuevo, {body: viejo}, [bot('aviso A')]),
  // un humano que copia el aviso con su marca tampoco cuenta (H4 del verificador)
  debeComentar(nuevo, issue, [bot(nuevo), hum('cito:\n' + viejo)]),
];
console.log(JSON.stringify(casos));
""")
    assert got == [False, False, False, True, False, True, True, False]


def test_reintenta_ante_errores_de_servidor(wf):
    """GitHub devuelve 502 a veces: el cliente de github-script tiene que reintentar."""
    w = wf["jobs"]["vigilar"]["steps"][0]["with"]
    assert int(w.get("retries", 0)) >= 3, "sin `retries`, un 502 suelto tumba la vigilancia"


def test_jobs_y_comentarios_se_leen_paginados(script):
    """Un reproceso por trozos tiene 178 jobs y #824 llegó a 28 comentarios: hay que paginar."""
    assert re.search(r"paginate\(\s*github\.rest\.actions\.listJobsForWorkflowRun", script), (
        "los jobs se leen sin paginar: con más de 100 jobs el job colgado puede quedar fuera")
    assert re.search(r"paginate\(\s*github\.rest\.issues\.listComments", script), (
        "los comentarios se leen sin paginar: la deduplicación compararía contra uno viejo")


# --- Punta a punta: el script ENTERO con un GitHub simulado -------------------------
# Las funciones puras pueden estar bien y el cableado mal (A118: un flag que no llega a
# su consumidor). Esto corre el script tal cual, con la API reemplazada por datos.
SIM_JS = r"""
const fx = JSON.parse(require('fs').readFileSync(%(fixture)s, 'utf8'));
const esc = %(esc)s;
const AHORA = Date.parse(esc.ahora);
Date.now = () => AHORA;
const log = {comentarios: [], creados: [], cerrados: [], fallo: null, jobsLeidos: 0};
const jobsA = t => fx.jobs.map(j => {
  const s = Date.parse(j.started_at), e = Date.parse(j.completed_at);
  if (e <= t) return j;
  if (s <= t) return {...j, status: 'in_progress', conclusion: null, completed_at: null};
  return {...j, status: 'queued', conclusion: null, started_at: fx.run.created_at, completed_at: null};
});
const WF = {id: 1, name: 'Reproc por trozos', path: '.github/workflows/reproc-chunked.yml'};
const listJobs = async () => {};
const listComments = async () => {};
const github = {
  paginate: async (fn, p) => {
    if (fn === listJobs) {
      log.jobsLeidos++;
      if (esc.jobs502) { const e = new Error('Server Error'); e.status = 502; throw e; }
      if (p.run_id !== fx.run.id) return [];  // corridas extra: en cola, sin jobs
      return esc.jobsColgado
        ? jobsA(AHORA).map((j, i) => i === 0 ? {...j, status: 'in_progress',
            conclusion: null, started_at: fx.run.created_at, completed_at: null} : j)
        : jobsA(AHORA);
    }
    if (fn === listComments) return esc.comentarios;
    throw new Error('paginate inesperado');
  },
  rest: {
    // S158: el script también lee la lista de corridas juzgadas (#876); acá no existe (404).
    repos: {getContent: async ({path}) => {
      if (path === '.github/reproc-watchdog-juzgadas.json') {
        if (esc.juzgadasTexto == null)
          throw Object.assign(new Error('Not Found'), {status: 404});
        return {data: {content: Buffer.from(esc.juzgadasTexto, 'utf8').toString('base64')}};
      }
      return {data: [{type: 'file', path: WF.path}]};
    }},
    actions: {
      listRepoWorkflows: async () => ({data: {workflows: [WF]}}),
      listWorkflowRuns: async () => ({data: {workflow_runs: (esc.runsAntes || []).concat([{...fx.run,
        status: esc.runStatus, conclusion: esc.runConclusion}]).concat(esc.runsDespues || [])}}),
      listJobsForWorkflowRun: listJobs,
    },
    issues: {
      listForRepo: async () => ({data: esc.issues}),
      listComments,
      createComment: async p => { log.comentarios.push(p.body); },
      create: async p => { log.creados.push(p.body); },
      update: async p => { log.cerrados.push(p.issue_number); },
    },
  },
};
const core = {info: () => {}, warning: () => {}, setFailed: m => { log.fallo = m; }};
const context = {repo: {owner: 'o', repo: 'r'}};
(async () => {
%(script)s
})().then(() => console.log(JSON.stringify(log)),
          e => { console.error(e); process.exit(1); });
"""

TITULO = "Reproc: corrida fallida o colgada"


def _simular(script, **esc):
    node = shutil.which("node")
    if node is None:
        pytest.skip("node no disponible en este entorno")
    base = {"ahora": "2026-10-19T13:34:43Z", "runStatus": "in_progress",
            "runConclusion": None, "issues": [], "comentarios": [],
            "jobs502": False, "jobsColgado": False}
    base.update(esc)
    js = SIM_JS % {"fixture": json.dumps(FIXTURE), "esc": json.dumps(base),
                   "script": script}
    out = subprocess.run([node, "-e", js], capture_output=True, text=True, encoding="utf-8",
                         cwd=ROOT)
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout.strip().splitlines()[-1])


def test_simulado_run_real_en_curso_no_abre_issue(script):
    """A la hora del comentario falso de #824 (25,6 h de run), el script no avisa nada."""
    log = _simular(script)
    assert log["creados"] == [] and log["comentarios"] == [], (
        "el watchdog abrió un aviso por un reproceso sano: %s" % log["creados"][:1])
    assert log["fallo"] is None
    assert log["jobsLeidos"] == 1, "el script no leyó los jobs del run en curso"


def test_simulado_job_colgado_abre_issue_y_no_lo_repite(script):
    """Con un job colgado se abre la issue; una hora después, mismo estado: silencio."""
    log1 = _simular(script, jobsColgado=True)
    assert len(log1["creados"]) == 1 and "corre desde 2026-10-18T12:01:01Z" in log1["creados"][0]
    issue = {"number": 900, "title": TITULO, "body": log1["creados"][0]}
    log2 = _simular(script, jobsColgado=True, ahora="2026-10-19T14:34:43Z",
                    issues=[issue], comentarios=[{"body": "lo miro"}])
    assert log2["creados"] == [] and log2["comentarios"] == [], (
        "el watchdog repitió el mismo aviso una hora después")
    # control: si el estado cambia (el run terminó en failure), sí comenta
    log3 = _simular(script, runStatus="completed", runConclusion="failure",
                    issues=[issue], comentarios=[])
    assert len(log3["comentarios"]) == 1 and "termino en `failure`" in log3["comentarios"][0]
    # y una hora después, con ese comentario ya puesto (y uno humano debajo): silencio.
    # Esto exige que el aviso lleve la MARCA: sin ella el script compararía siempre
    # contra el cuerpo original de la issue y comentaría cada hora desde el 2.º cambio.
    log4 = _simular(script, runStatus="completed", runConclusion="failure",
                    ahora="2026-10-19T14:34:43Z", issues=[issue],
                    comentarios=[{"body": log3["comentarios"][0],
                                  "user": {"login": "github-actions[bot]"}},
                                 {"body": "relanzo", "user": {"login": "MendozaVolcanic"}}])
    assert log4["comentarios"] == [], "repitió el aviso de la corrida fallida"


def test_simulado_502_no_cierra_el_issue(script):
    """Si los jobs no se pueden leer, no se cierra la issue abierta y el run queda en rojo."""
    issue = {"number": 900, "title": TITULO, "body": "aviso viejo"}
    log = _simular(script, jobs502=True, issues=[issue])
    assert log["cerrados"] == [], "cerró la issue sin haber podido mirar los jobs"
    assert log["fallo"] and "sin dato" in log["fallo"]


def test_simulado_sin_problemas_cierra(script):
    """Control del anterior: con los jobs legibles y sanos, la issue abierta sí se cierra."""
    issue = {"number": 900, "title": TITULO, "body": "aviso viejo"}
    log = _simular(script, issues=[issue])
    assert log["cerrados"] == [900] and log["fallo"] is None


def _lista(run_id, attempt=1, motivo="ya juzgada", referencia="issue #876"):
    return json.dumps({"juzgadas": [{"run_id": run_id, "run_attempt": attempt,
                                     "motivo": motivo, "referencia": referencia}]})


def test_simulado_juzgada_cierra_el_issue_y_sin_lista_comenta(script):
    """S158 #876, punta a punta: la falla juzgada deja cerrar el issue; sin la lista, no.

    El control es el mismo escenario sin la lista: tiene que comentar la falla, o el
    cierre de arriba no probaría que la exención llegó al script real (A116, A118).
    """
    issue = {"number": 900, "title": TITULO, "body": "aviso viejo"}
    fallida = dict(runStatus="completed", runConclusion="failure", issues=[issue])
    sin = _simular(script, **fallida)
    assert len(sin["comentarios"]) == 1 and "termino en `failure`" in sin["comentarios"][0]
    con = _simular(script, juzgadasTexto=_lista(39125546355), **fallida)
    assert con["cerrados"] == [900] and con["comentarios"] != [] and con["fallo"] is None
    assert "Cerrando" in con["comentarios"][0]
    otra = _simular(script, juzgadasTexto=_lista(39125546355, attempt=2), **fallida)
    assert otra["cerrados"] == [] and "termino en `failure`" in otra["comentarios"][0], (
        "un juicio sobre otro intento eximió la corrida")


def test_simulado_lista_invalida_va_al_rojo_y_no_exime(script):
    """Una lista con una entrada sin motivo no exime nada y deja el job en rojo."""
    issue = {"number": 900, "title": TITULO, "body": "aviso viejo"}
    log = _simular(script, runStatus="completed", runConclusion="failure", issues=[issue],
                   juzgadasTexto=_lista(39125546355, motivo=" "))
    assert log["cerrados"] == [] and "termino en `failure`" in log["comentarios"][0]
    assert log["fallo"] and "juzgadas" in log["fallo"]


def test_simulado_corrida_en_curso_detras_de_otra_en_cola(script):
    """Dos trozos relanzados: la última corrida espera en cola y la anterior tiene un job
    colgado. Mirar sólo la última corrida lo dejaría invisible."""
    en_cola = {"id": 1, "created_at": "2026-10-19T13:00:00Z", "status": "pending",
               "conclusion": None, "html_url": "https://example/runs/1"}
    log = _simular(script, jobsColgado=True, runsAntes=[en_cola])
    assert len(log["creados"]) == 1 and "39125546355" in log["creados"][0], (
        "el job colgado de la corrida anterior no se reportó")
    assert "example/runs/1" not in log["creados"][0], "la corrida en cola no es colgada"



def test_rerun_de_corrida_vieja_cuenta_desde_su_ultimo_intento(bloque_puro):
    """H2 del verificador: un re-run conserva `created_at` viejo. Con la ventana medida
    desde `created_at`, un job colgado 9 h en un re-run de una corrida de 20 días no
    avisaba. La ventana se mide desde `run_started_at`."""
    got = _node(bloque_puro, r"""
const ahora = Date.parse('2026-10-20T12:00:00Z');
const r = {status: 'in_progress', conclusion: null, created_at: '2026-09-30T00:00:00Z',
           run_started_at: '2026-10-20T02:00:00Z', run_attempt: 2};
const jobs = [{name: 'trozo 4', status: 'in_progress', conclusion: null,
               started_at: '2026-10-20T03:00:00Z', completed_at: null}];
const f = {status: 'completed', conclusion: 'failure', created_at: '2026-09-30T00:00:00Z',
           run_started_at: '2026-10-20T02:00:00Z', run_attempt: 2};
console.log(JSON.stringify([evaluarCorrida(r, jobs, ahora, 7, 14),
                            evaluarCorrida(f, [], ahora, 7, 14)]));
""")
    assert got[0] is not None and got[0]["tipo"] == "colgada"
    assert got[1] is not None and got[1]["tipo"] == "fallida"


def test_corrida_estancada_sin_jobs_corriendo(bloque_puro):
    """H3 del verificador: una corrida viva hace más de 72 h sin ningún job corriendo
    (huérfana o en cola eterna) se avisa; a las 30 h, en cola detrás de max-parallel, no."""
    got = _node(bloque_puro, r"""
const r = {status: 'queued', conclusion: null, created_at: '2026-10-10T00:00:00Z'};
const enCola = [{name: 'trozo 1', status: 'queued', conclusion: null,
                 started_at: '2026-10-10T00:00:05Z', completed_at: null},
                {name: 'trozo 0', status: 'completed', conclusion: 'success',
                 started_at: '2026-10-10T00:00:05Z', completed_at: '2026-10-10T02:00:00Z'}];
const corriendo = enCola.concat([{name: 'trozo 2', status: 'in_progress', conclusion: null,
                 started_at: '2026-10-13T05:00:00Z', completed_at: null}]);
const t80 = Date.parse('2026-10-13T08:00:00Z'), t30 = Date.parse('2026-10-11T06:00:00Z');
console.log(JSON.stringify([evaluarCorrida(r, enCola, t80, 7, 14, 72),
                            evaluarCorrida(r, enCola, t30, 7, 14, 72),
                            evaluarCorrida(r, corriendo, t80, 7, 14, 72)]));
""")
    assert got[0] is not None and got[0]["tipo"] == "estancada"
    assert got[1] is None, "una corrida de 30 h en cola no está estancada"
    assert got[2] is None, "con un job corriendo (de 3 h) no está estancada"


def test_simulado_sin_dato_va_al_rojo_y_no_al_texto(script):
    """H5 del verificador: con una falla real y otra corrida SIN DATO, el aviso lleva sólo la
    falla (si llevara el SIN DATO, un 502 intermitente lo haría alternar y repetir) y el job
    de Actions queda en rojo."""
    en_curso = {"id": 2, "created_at": "2026-10-19T13:00:00Z", "status": "in_progress",
                "conclusion": None, "html_url": "https://example/runs/2"}
    log = _simular(script, runStatus="completed", runConclusion="failure",
                   jobs502=True, runsDespues=[en_curso])
    assert len(log["creados"]) == 1 and "termino en `failure`" in log["creados"][0]
    assert "SIN DATO" not in log["creados"][0] and "example/runs/2" not in log["creados"][0]
    assert log["fallo"] and "example/runs/2" in log["fallo"]
