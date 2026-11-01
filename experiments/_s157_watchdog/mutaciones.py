# -*- coding: utf-8 -*-
"""Batería de mutaciones del reproc-watchdog S157 (A110: un control se valida midiendo su nulo).

POR QUÉ. Que las pruebas pasen sobre el código nuevo no dice que vigilen algo. Cada
mutación de abajo reintroduce un defecto concreto (el de F3-10, el de F3-07, o uno del
cableado) y se mira si alguna prueba lo rechaza.

Regla de conteo: una mutación es ATRAPADA sólo si al menos una prueba falla por una
aserción de comportamiento. Si lo único que falla es que node se cayó (el
`assert out.returncode == 0` de los ayudantes) o pytest no pudo colectar, es CAIDA:
la prueba no miró el comportamiento, sólo vio que el programa no corre. El control
de caída es la mutación M00, que rompe la sintaxis a propósito y tiene que salir
CAIDA, no ATRAPADA.

Se corre sobre una copia en un directorio temporal: el árbol de trabajo no se toca.

Uso:  python experiments/_s157_watchdog/mutaciones.py
"""
import io
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
YML = os.path.join(ROOT, ".github", "workflows", "reproc-watchdog.yml")
TESTS = ["test_reproc_watchdog_por_job_s157.py", "test_reproc_watchdog_vivos_s133.py"]

MUTACIONES = [
    ("M00 control de caida: sintaxis rota",
     "function lineaProblema(w, r, v) {", "function lineaProblema(w, r, v) {{"),
    ("M01 F3-10: la edad del RUN vuelve a decidir 'colgada'",
     "              if (colgados.length) return { tipo: 'colgada', jobs: colgados };",
     "              if (colgados.length || edad > horasColgado) return { tipo: 'colgada', jobs: colgados };"),
    ("M02 cuenta jobs en cola como corriendo",
     ".filter(j => j.status === 'in_progress' && j.started_at)",
     ".filter(j => j.status !== 'completed' && j.started_at)"),
    ("M03 umbral del job ignorado (cualquier job en curso es colgado)",
     ".filter(j => j.horas > horasColgado);", ".filter(j => j.horas > 0);"),
    ("M04 SIN DATO se lee como sano",
     "if (!Array.isArray(jobs)) return { tipo: 'sin_dato' };",
     "if (!Array.isArray(jobs)) return null;"),
    ("M05 la ventana de antiguedad se ignora",
     "if (!(edad <= maxDias * 24)) return null;", "if (!(edad <= maxDias * 2400)) return null;"),
    ("M06 una corrida cancelada se reporta como fallida",
     "r.conclusion !== 'success' && r.conclusion !== 'cancelled'",
     "r.conclusion !== 'success'"),
    ("M07 F3-07: la linea del job colgado vuelve a llevar horas",
     "+ `${j.started_at}`).join('; ')}",
     "+ `${j.started_at} (${j.horas.toFixed(1)} h)`).join('; ')}"),
    ("M08 F3-07: la linea de la fallida vuelve a llevar la hora de lectura",
     "termino en `\n                  + `\\`${r.conclusion}\\` · ${r.html_url}`;",
     "termino en `\n                  + `\\`${r.conclusion}\\` (${v.leido || Math.random()}) · ${r.html_url}`;"),
    ("M09 debeComentar siempre comenta",
     "return normalizar(cuerpo) !== normalizar(ultimo);", "return true;"),
    ("M10 debeComentar compara contra cualquier comentario, no el del watchdog",
     ".filter(c => String(c.body || '').includes(MARCA)\n"
     "                && c.user && c.user.login === AUTOR)",
     ".filter(c => true)"),
    ("M11 normalizar no quita espacios finales",
     ".map(l => l.replace(/\\s+$/, ''))", ".map(l => l)"),
    ("M12 cableado: el script no consulta debeComentar",
     "if (debeComentar(cuerpo, issue, comentarios)) {", "if (true) {"),
    ("M13 cableado: no se leen los jobs del run en curso",
     "                if (r.status !== 'completed') {\n                  try {",
     "                if (false) {\n                  try {"),
    ("M14 cableado: solo se mira la ultima corrida",
     "runs.filter((r, i) => i === 0 || r.status !== 'completed')", "runs.slice(0, 1)"),
    ("M15 SIN DATO no impide cerrar la issue",
     "              if (sinDato.length) {\n                // Sin dato no es verde",
     "              if (false) {\n                // Sin dato no es verde"),
    ("M16 sin reintentos ante 502", "          retries: 3\n", "          retries: 0\n"),
    ("M17 jobs sin paginar",
     "jobs = await github.paginate(github.rest.actions.listJobsForWorkflowRun,\n"
     "                      { owner, repo, run_id: r.id, filter: 'latest', per_page: 100 });",
     "jobs = (await github.rest.actions.listJobsForWorkflowRun(\n"
     "                      { owner, repo, run_id: r.id, filter: 'latest', per_page: 100 })).data.jobs;"),
    ("M19 H2: la ventana vuelve a contarse desde created_at (re-run invisible)",
     "const inicio = r.run_started_at || r.created_at;", "const inicio = r.created_at;"),
    ("M20 H3: sin aviso de corrida estancada",
     "if (edad > horasEstancada && !jobs.some(j => j.status === 'in_progress'))",
     "if (false)"),
    ("M21 H3: estancada cuenta jobs en cola como corriendo",
     "!jobs.some(j => j.status === 'in_progress')", "!jobs.some(j => j.status !== 'completed')"),
    ("M22 H4: la deduplicacion no mira el autor",
     "&& c.user && c.user.login === AUTOR);", ");"),
    ("M23 H5: el SIN DATO vuelve al texto del aviso",
     "'', ...problemas, '',", "'', ...problemas, ...sinDato, '',"),
    ("M18 la MARCA no va en el aviso",
     "              MARCA,\n            ].join('\\n');", "            ].join('\\n');"),
]


def correr(yml_texto):
    tmp = tempfile.mkdtemp(prefix="mut_s157_")
    try:
        os.makedirs(os.path.join(tmp, ".github", "workflows"))
        os.makedirs(os.path.join(tmp, "tests"))
        with io.open(os.path.join(tmp, ".github", "workflows", "reproc-watchdog.yml"),
                     "w", encoding="utf-8", newline="\n") as fh:
            fh.write(yml_texto)
        for t in TESTS:
            shutil.copy(os.path.join(ROOT, "tests", t), os.path.join(tmp, "tests", t))
        shutil.copytree(os.path.join(ROOT, "tests", "datos_s157"),
                        os.path.join(tmp, "tests", "datos_s157"))
        xml = os.path.join(tmp, "r.xml")
        subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                        "--junitxml", xml, "tests"], cwd=tmp, capture_output=True)
        if not os.path.exists(xml):
            return [], ["(pytest no produjo resultado)"]
        aserc, caidas = [], []
        for tc in ET.parse(xml).getroot().iter("testcase"):
            for f in list(tc.findall("failure")) + list(tc.findall("error")):
                texto = (f.get("message") or "") + (f.text or "")
                nombre = tc.get("name")
                if f.tag == "error" or "out.returncode == 0" in texto \
                        or "AssertionError" not in texto:
                    caidas.append(nombre)
                else:
                    aserc.append(nombre)
        return aserc, caidas
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    with io.open(YML, encoding="utf-8") as fh:
        base = fh.read()
    a, c = correr(base)
    print(f"BASE sin mutar: fallas por asercion={len(a)} caidas={len(c)}")
    assert not a and not c, "la base tiene que pasar entera antes de mutar"
    atrapadas = vivas = caidas = 0
    for nombre, viejo, nuevo in MUTACIONES:
        n = base.count(viejo)
        if n != 1:
            print(f"{nombre}: NO APLICA (el texto a mutar aparece {n} veces)")
            vivas += 1
            continue
        a, c = correr(base.replace(viejo, nuevo))
        if a:
            veredicto = "ATRAPADA"; atrapadas += 1
        elif c:
            veredicto = "CAIDA"; caidas += 1
        else:
            veredicto = "VIVA"; vivas += 1
        print(f"{nombre}: {veredicto}  (por asercion: {a[:3]}{'...' if len(a) > 3 else ''}; "
              f"caidas: {len(c)})")
    print(f"\nTOTAL {len(MUTACIONES)}: atrapadas={atrapadas} caidas={caidas} vivas={vivas}")
    print("Esperado: M00 CAIDA (control) y todas las demas ATRAPADAS.")


if __name__ == "__main__":
    main()
