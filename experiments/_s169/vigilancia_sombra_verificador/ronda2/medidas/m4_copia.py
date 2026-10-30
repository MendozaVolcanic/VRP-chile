"""Ronda 2: adaptado de D:/vrp-trabajo/temporales/s169_ver_vigilancia/medidas/m4_mutaciones_rapido.py.
Copia del worktree (scripts, tests, .github, pipeline) en arbol_mut, normalizada a LF; rompe una cosa a la vez y
corre las dos pruebas nuevas. Control: 'ninguna' tiene que dar 0 fallas. Sólo cuenta como atrapada si falla una prueba."""
import os, re, shutil, subprocess, sys
SRC = sys.argv[1]
DST = "D:/vrp-trabajo/temporales/s169_ver_vigilancia_r2/medidas/arbol_mut"
PY = "C:/Users/nmend/AppData/Local/Programs/Python/Python312/python.exe"
if os.path.exists(DST):
    shutil.rmtree(DST)
for d in ("scripts", "tests", ".github", "pipeline"):
    shutil.copytree(os.path.join(SRC, d), os.path.join(DST, d), ignore=shutil.ignore_patterns("__pycache__"))
for raiz, _, archivos in os.walk(DST):
    for a in archivos:
        if a.endswith((".py", ".js", ".yml", ".yaml")):
            p = os.path.join(raiz, a)
            b = open(p, "rb").read()
            if b"\r\n" in b:
                open(p, "wb").write(b.replace(b"\r\n", b"\n"))
RS, JS, WF, MON, TA = ("scripts/revisar_sombra.py", "scripts/nrt_monitor_decision.js",
                       ".github/workflows/sombra-codigo-mirova.yml", ".github/workflows/nrt-monitor.yml",
                       "scripts/tachar_secreto_log.py")
MUT = [
 ("ninguna", None, None, None),
 ("A sin filtro de tiempo", RS, "if t is None or t < desde:", "if t is None:"),
 ("B sin filtro de sha", RS, 'return sha is None or (r.get("regimen") or {}).get("codigo_sha") == sha', "return True"),
 ("C K viejo cuenta", RS, 'for r in nuevos:\n        if r.get("via_codigo_mirova") is True:', 'for r in en_ventana:\n        if r.get("via_codigo_mirova") is True:'),
 ("D SNPP retirada se cuenta viva", RS, "if cese is not None and inicio_dia is not None and inicio_dia >= cese:", "if False:"),
 ("E sin_granulos de cualquier dia", RS, 'and i.get("fecha") == fin}', "}"),
 ("F cobertura ausente no es falla", RS, 'fallas.append("no hay JSON de cobertura: no se sabe qué se buscó")', "pass"),
 ("G fallas de fin ignoradas", RS, 'fallas.append(f"cobertura incompleta: {de_hoy} búsquedas o descargas fallidas del {fin}")', "pass"),
 ("H una plataforma vacia basta", RS, "if p not in vacias:\n            return None", "if p not in vacias:\n            continue"),
 ("I sensor faltante nunca falla", RS, 'fallas.append(f"{s}: ningún record de la vía de {vispera} o {fin} escrito en esta corrida")', "pass"),
 ("J monitor cuenta workflow_dispatch", JS, "r.event === 'schedule' && r.status === 'completed'", "r.status === 'completed'"),
 ("K monitor tope 200 h", JS, "maxHoras = 26", "maxHoras = 200"),
 ("L monitor desde 2020", JS, "const SOMBRA_DESDE = '2026-11-03T15:00:00Z';", "const SOMBRA_DESDE = '2020-11-03T15:00:00Z';"),
 ("M monitor cuenta runs no terminados", JS, "r.status === 'completed' &&\n      r.conclusion === 'success'", "r.conclusion !== 'failure'"),
 ("N workflow sin always() en upload", WF, "      - name: Guardar log y cobertura de la corrida\n        if: always() && steps.correr.outputs.corrio == 'true'", "      - name: Guardar log y cobertura de la corrida\n        if: steps.correr.outputs.corrio == 'true'"),
 ("O workflow --sha vacio", WF, '--sha "${{ github.sha }}"', '--sha ""'),
 ("P workflow inicio constante", WF, "INICIO=$(date -u +%Y-%m-%dT%H:%M:%SZ)", "INICIO=2000-01-01T00:00:00Z"),
 ("P2 workflow inicio en otro formato", WF, "INICIO=$(date -u +%Y-%m-%dT%H:%M:%SZ)", "INICIO=$(date -u +%Y-%m-%d)"),
 ("Q monitor sin if always()", MON, "        if: always()\n        uses: actions/github-script@v7\n        with:\n          retries: 3", "        uses: actions/github-script@v7\n        with:\n          retries: 3"),
 ("R monitor sin permiso issues", MON, "  issues: write\n", ""),
 ("R2 monitor sin permiso actions", MON, "  actions: read\n", ""),
 ("V1 reemplazos viejos cuentan (VV01)", RS, ' and str(r.get("datetime_utc") or "")[:10] >= vispera', ""),
 ("V2 catalogo vacio no es falla (VV02)", RS, 'if set(sensores) <= set(sin_pasada) or {"VIIRS750", "VIIRS375"} <= set(sin_pasada):', "if False:"),
 ("V2b solo los tres sensores (VV02)", RS, 'if set(sensores) <= set(sin_pasada) or {"VIIRS750", "VIIRS375"} <= set(sin_pasada):', "if set(sensores) <= set(sin_pasada):"),
 ("V3 toda falla de cobertura es FALLA (VV03)", RS, "if fecha and fecha < fin:", "if False:"),
 ("V3b toda falla de cobertura es NOTA (VV03)", RS, "if fecha and fecha < fin:", "if True:"),
 ("V4 sin pendiente (VV04)", JS, "if (pendiente) {", "if (false) {"),
 ("V4b pendiente sin tope de edad (VV04)", JS, "horasPendiente = 6", "horasPendiente = 600"),
 ("V4c yml no sale con pendiente (VV04)", MON, "if (d.accion === 'inactivo' || d.accion === 'pendiente') return;", "if (d.accion === 'inactivo') return;"),
 ("V5 resumen del job sin la linea (VV05)", RS, 'fh.write("### Revisión de la sombra', '(lambda *a: None)("### Revisión de la sombra'),
 ("V5b K solo de esta corrida (VV05)", RS, 'for r in en_ventana:\n        if r.get("via_codigo_mirova") is not True:', 'for r in nuevos:\n        if r.get("via_codigo_mirova") is not True:'),
 ("V7 tachar no reemplaza (VV07)", TA, 'txt.replace(token, "***")', "txt"),
 ("V7b workflow no tacha (VV07)", WF, "python scripts/tachar_secreto_log.py pipeline.log cobertura.json", "true"),
]
atrapadas = sobreviven = 0
for nombre, f, a, b in MUT:
    orig = None
    if f:
        p = os.path.join(DST, f)
        orig = open(p, encoding="utf-8", newline="").read()
        if orig.count(a) != 1:
            print(f"{nombre}: PATRON NO ENCONTRADO o repetido ({orig.count(a)})", flush=True); continue
        open(p, "w", encoding="utf-8", newline="").write(orig.replace(a, b, 1))
    r = subprocess.run([PY, "-m", "pytest", "-p", "no:cacheprovider", "-q", "--tb=short", "-rf",
                        "tests/test_revisar_sombra_corrida_s169.py", "tests/test_monitor_sombra_s169.py"],
                       cwd=DST, capture_output=True, text=True, encoding="utf-8",
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    out = r.stdout.splitlines()
    resumen = [l for l in out if re.search(r"\d+ (passed|failed)", l)]
    res = resumen[-1] if resumen else (out[-1:] or ["?"])[0]
    fall = [l.split("::")[-1][:90] for l in out if l.startswith("FAILED")][:3]
    tipos = {}
    for l in out:
        m = re.match(r"^E\s+([A-Za-z_.]+(?:Error|Exception)|assert)", l)
        if m:
            tipos[m.group(1)] = tipos.get(m.group(1), 0) + 1
    no_asercion = {k: v for k, v in tipos.items() if k not in ("assert", "AssertionError")}
    if f:
        estado = "ATRAPADA" if " failed" in res else "SOBREVIVE"
        atrapadas += estado == "ATRAPADA"; sobreviven += estado == "SOBREVIVE"
    else:
        estado = "CONTROL"
    print(f"{nombre}: {res} | {estado} | tipos E: {tipos} | NO-ASERCION: {no_asercion} | {fall}", flush=True)
    if f:
        open(p, "w", encoding="utf-8", newline="").write(orig)
print(f"TOTAL: {atrapadas} atrapadas, {sobreviven} sobreviven de {atrapadas + sobreviven}")
