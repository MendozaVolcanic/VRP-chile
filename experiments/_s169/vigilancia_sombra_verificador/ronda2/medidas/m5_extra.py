"""Mutaciones EXTRA (mias, no las 32 del autor) sobre los puntos que R1-R6 piden y que las 32 no tocan.
P1: si el codigo estuviera roto de ese modo, las 2 pruebas nuevas lo verian? P2: control sin mutar tiene que dar 39 passed.
Solo cuenta como atrapada si falla una prueba por aserccion; se informa el tipo de excepcion."""
import os, re, shutil, subprocess, sys
SRC = sys.argv[1]
DST = "D:/vrp-trabajo/temporales/s169_ver_vigilancia_r2/medidas/arbol_mut2"
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
RS, JS, TA, WF = "scripts/revisar_sombra.py", "scripts/nrt_monitor_decision.js", "scripts/tachar_secreto_log.py", ".github/workflows/sombra-codigo-mirova.yml"
MUT = [
 ("ninguna", None, None, None),
 ("X1 vispera = fin-2", RS, "timedelta(days=1)).strftime", "timedelta(days=2)).strftime"),
 ("X2 vispera no cuenta (> en vez de >=)", RS, '[:10] >= vispera:', '[:10] > vispera:'),
 ("X3 frontera de 6 h inclusiva (<=)", JS, "< horasPendiente", "<= horasPendiente"),
 ("X4 pendiente cuenta workflow_dispatch", JS, "r.event === 'schedule' && r.status !== 'completed'", "r.status !== 'completed'"),
 ("X5 pendiente solo queued", JS, "r.status !== 'completed' &&\n    r.created_at", "r.status === 'queued' &&\n    r.created_at"),
 ("X6 pendiente antes que ok", JS, "if (ultima && (ahoraMs - Date.parse(ultima.created_at)) / 3.6e6 <= maxHoras) {", "if (false) {"),
 ("X7 R2: usa | en vez de <= (cualquiera de los dos VIIRS)", RS, '{"VIIRS750", "VIIRS375"} <= set(sin_pasada)', '{"VIIRS750", "VIIRS375"} & set(sin_pasada)'),
 ("X8 R3: sin fecha cuenta como vieja", RS, "if fecha and fecha < fin:", "if fecha < fin:"),
 ("X9 R3: NOTA de dia viejo se pierde", RS, "        for fecha in sorted(viejas):\n            notas.append(", "        for fecha in []:\n            notas.append("),
 ("X10 R5: linea K solo si hay K", RS, 'resumen += (f"\\n  K caídos en la ventana: {sum(k_ventana.values())}"', 'resumen += ("" if not k_ventana else f"\\n  K caídos en la ventana: {sum(k_ventana.values())}"'),
 ("X11 R5: summary solo en verde", RS, 'if ruta:', 'if ruta and ok:'),
 ("X12 tachar: sin strip", TA, '.strip()', ''),
 ("X13 tachar: token vacio reemplaza '' (corrompe)", TA, "    if not token:\n        print(\"sin EARTHDATA_TOKEN en el entorno: nada que tachar\")\n        return 0\n", ""),
 ("X14 tachar solo pipeline.log", TA, "for r in rutas:", "for r in rutas[:1]:"),
 ("X15 tachar: sale 0 sin escribir", TA, "p.write_text(txt.replace(token, \"***\"), encoding=\"utf-8\")", "pass"),
 ("X16 workflow: tachar sin always()", WF, "      - name: Tachar el token en el log y la cobertura\n        if: always() && steps.correr.outputs.corrio == 'true'", "      - name: Tachar el token en el log y la cobertura\n        if: steps.correr.outputs.corrio == 'true'"),
 ("X17 workflow: tachar sin env del token", WF, "        env:\n          EARTHDATA_TOKEN: ${{ secrets.EARTHDATA_TOKEN }}\n        run: |\n          python scripts/tachar_secreto_log.py", "        run: |\n          python scripts/tachar_secreto_log.py"),
 ("X18 workflow: tachar solo pipeline.log", WF, "python scripts/tachar_secreto_log.py pipeline.log cobertura.json", "python scripts/tachar_secreto_log.py pipeline.log"),
]
KEEP = ('ninguna', 'X1 ', 'X3 ', 'X4 ', 'X6 ', 'X7 ', 'X8 ', 'X12 ', 'X13 ', 'X15 ', 'X16 ', 'X17 ')
MUT = [m for m in MUT if m[0].startswith(KEEP)]
atrapadas = sobreviven = 0
for nombre, f, a, b in MUT:
    orig = None
    if f:
        p = os.path.join(DST, f)
        orig = open(p, encoding="utf-8", newline="").read()
        if orig.count(a) != 1:
            print(f"{nombre}: PATRON NO ENCONTRADO o repetido ({orig.count(a)})", flush=True); continue
        open(p, "w", encoding="utf-8", newline="").write(orig.replace(a, b, 1))
    r = subprocess.run([PY, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-q", "--tb=short", "-rf",
                        "tests/test_revisar_sombra_corrida_s169.py", "tests/test_monitor_sombra_s169.py"],
                       cwd=DST, capture_output=True, text=True, encoding="utf-8",
                       env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"})
    out = r.stdout.splitlines()
    resumen = [l for l in out if re.search(r"\d+ (passed|failed)", l)]
    res = resumen[-1] if resumen else (out[-1:] or ["?"])[0]
    fall = [l.split("::")[-1][:70] for l in out if l.startswith("FAILED")][:2]
    tipos = sorted({re.sub(r"^.* - ", "", l).split(":")[0].split(" ")[0] for l in out if l.startswith("FAILED")})
    if f:
        estado = "ATRAPADA" if " failed" in res else "SOBREVIVE"
        atrapadas += estado == "ATRAPADA"; sobreviven += estado == "SOBREVIVE"
    else:
        estado = "CONTROL"
    print(f"{nombre}: {res} | {estado} | {tipos} | {fall}", flush=True)
    if f:
        open(p, "w", encoding="utf-8", newline="").write(orig)
print(f"TOTAL: {atrapadas} atrapadas, {sobreviven} sobreviven de {atrapadas + sobreviven}")
