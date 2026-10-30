"""M4. Mutaciones sobre una COPIA del arbol (arbol_mut), para ver si las 23 pruebas nuevas atrapan cada una.
PREGUNTAS: (1) si la prueba no atrapara la mutacion, ¿esta medicion lo veria? Si: la mutacion sobrevive (0 fallas).
(2) control de instrumento: la mutacion 'ninguna' (copia sin tocar) tiene que dar 0 fallas, y 'rompe_todo' (sintaxis) debe dar muchas.
Solo cuenta como atrapada si falla una asercion (no un error de import): se reporta el texto de la primera falla."""
import shutil, subprocess, os, re, sys
ROOT = "D:/vrp-trabajo/temporales/s169_ver_vigilancia"
PY = "C:/Users/nmend/AppData/Local/Programs/Python/Python312/python.exe"
MUT = [
 ("ninguna", None, None, None),
 ("A sin filtro de tiempo", "scripts/revisar_sombra.py", "if t is None or t < desde:", "if t is None:"),
 ("B sin filtro de sha", "scripts/revisar_sombra.py", 'return sha is None or (r.get("regimen") or {}).get("codigo_sha") == sha', "return True"),
 ("C K viejo cuenta (otros sobre toda la ventana)", "scripts/revisar_sombra.py", "for r in nuevos:\n        if r.get(\"via_codigo_mirova\") is True:", "for r in en_ventana:\n        if r.get(\"via_codigo_mirova\") is True:"),
 ("D SNPP retirada se cuenta viva", "scripts/revisar_sombra.py", "if cese is not None and inicio_dia is not None and inicio_dia >= cese:", "if False:"),
 ("E sin_granulos de cualquier dia", "scripts/revisar_sombra.py", 'and i.get("fecha") == fin}', "}"),
 ("F cobertura ausente no es falla", "scripts/revisar_sombra.py", 'fallas.append("no hay JSON de cobertura: no se sabe qué se buscó")', "pass"),
 ("G fallas de cobertura ignoradas", "scripts/revisar_sombra.py", 'fallas.append(f"cobertura incompleta: {n_fallas} búsquedas o descargas fallidas")', "pass"),
 ("H una plataforma vacia basta", "scripts/revisar_sombra.py", "if p not in vacias:\n            return None", "if p not in vacias:\n            continue"),
 ("I sensor faltante nunca falla", "scripts/revisar_sombra.py", 'fallas.append(f"{s}: ningún record de la vía escrito en esta corrida")', "pass"),
 ("J monitor cuenta workflow_dispatch", "scripts/nrt_monitor_decision.js", "r.event === 'schedule' && ", ""),
 ("K monitor tope 200 h", "scripts/nrt_monitor_decision.js", "maxHoras = 26", "maxHoras = 200"),
 ("L monitor desde 2020", "scripts/nrt_monitor_decision.js", "const SOMBRA_DESDE = '2026-11-03T15:00:00Z';", "const SOMBRA_DESDE = '2020-11-03T15:00:00Z';"),
 ("M monitor cuenta runs no terminados", "scripts/nrt_monitor_decision.js", "r.status === 'completed' &&\n      r.conclusion === 'success'", "r.conclusion !== 'failure'"),
 ("N workflow sin always() en upload", ".github/workflows/sombra-codigo-mirova.yml", "      - name: Guardar log y cobertura de la corrida\n        if: always() && steps.correr.outputs.corrio == 'true'", "      - name: Guardar log y cobertura de la corrida\n        if: steps.correr.outputs.corrio == 'true'"),
 ("O workflow --sha vacio", ".github/workflows/sombra-codigo-mirova.yml", '--sha "${{ github.sha }}"', '--sha ""'),
 ("P workflow inicio anotado DESPUES (en el paso de revisar)", ".github/workflows/sombra-codigo-mirova.yml", 'INICIO=$(date -u +%Y-%m-%dT%H:%M:%SZ)', 'INICIO=2000-01-01T00:00:00Z'),
 ("Q monitor sin if always()", ".github/workflows/nrt-monitor.yml", "        if: always()\n        uses: actions/github-script@v7\n        with:\n          retries: 3", "        uses: actions/github-script@v7\n        with:\n          retries: 3"),
 ("R monitor sin permiso issues", ".github/workflows/nrt-monitor.yml", "  issues: write\n", ""),
]
for nombre, f, a, b in MUT:
    dst = f"{ROOT}/arbol_mut"
    shutil.rmtree(dst, ignore_errors=True)
    shutil.copytree(f"{ROOT}/arbol", dst)
    estado = "copia sin tocar"
    if f:
        p = f"{dst}/{f}"
        s = open(p, encoding="utf-8", newline="").read()
        if a not in s:
            print(f"{nombre}: PATRON NO ENCONTRADO"); continue
        open(p, "w", encoding="utf-8", newline="").write(s.replace(a, b, 1))
    r = subprocess.run([PY, "-m", "pytest", "-p", "no:cacheprovider", "-q", "--tb=line", "tests/test_revisar_sombra_corrida_s169.py", "tests/test_monitor_sombra_s169.py", "tests/test_cadencia_cron_s133.py", "tests/test_sombra_codigo_mirova_s167.py"], cwd=dst, capture_output=True, text=True, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    out = r.stdout.splitlines()
    resumen = [l for l in out if re.search(r"\d+ (passed|failed)", l)]
    fall = [l for l in out if l.startswith("FAILED") or "Error" in l][:2]
    print(f"{nombre}: {resumen[-1] if resumen else out[-1:]} | {'ATRAPADA' if ' failed' in (resumen[-1] if resumen else '') else 'SOBREVIVE'} | {[x[:130] for x in fall]}")
