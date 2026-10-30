"""S169 ronda 3: nulo de mutaciones de la vigilancia de la sombra (adaptado del m4 del verificador).

Copia del worktree (scripts, tests, .github, pipeline) en una carpeta de D:/vrp-trabajo/temporales/, normalizada a LF;
rompe una cosa a la vez y corre las dos pruebas nuevas con --junitxml. Una mutación cuenta como ATRAPADA sólo si al
menos una prueba falla por AssertionError (leído del atributo `type` del XML); una falla de otro tipo (error de
colección, TypeError, CalledProcessError) no cuenta y se informa aparte. Control: 'ninguna' tiene que dar 0 fallas.
Todos los temporales (copia, XML, tmp_path de pytest) van bajo D:/vrp-trabajo/temporales/s169_vigilancia/.

Uso: python m4_mutaciones_r3.py <ruta del worktree>
"""
import os, shutil, subprocess, sys
import xml.etree.ElementTree as ET

SRC = sys.argv[1]
BASE = "D:/vrp-trabajo/temporales/s169_ver_vigilancia_r3/medidas/nulo"
DST = BASE + "/arbol_mut_r3"
XML = BASE + "/m4_r3_junit.xml"
TMP = BASE + "/m4_r3_pytest_tmp"
PY = sys.executable
os.makedirs(BASE, exist_ok=True)
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
 # control del clasificador: un JS que no compila hace fallar las pruebas por CalledProcessError, no por aserción;
 # tiene que salir NO atrapada. No entra al total.
 ("CONTROL js roto", JS, "function decidirSombra(", "function decidirSombra(("),
 # ronda 1 y verificador (A a R), con los textos de hoy
 ("A sin filtro de tiempo", RS, "if desde is None or t is None or t < desde:", "if desde is None or t is None:"),
 ("B sin filtro de sha", RS, 'return sha is None or (r.get("regimen") or {}).get("codigo_sha") == sha', "return True"),
 ("C K de la ventana cuenta como de esta corrida", RS, 'for r in nuevos:\n        if r.get("via_codigo_mirova") is not True:', 'for r in en_ventana:\n        if r.get("via_codigo_mirova") is not True:'),
 ("D SNPP retirada se cuenta viva", RS, "if cese is not None and inicio_dia is not None and inicio_dia >= cese:", "if False:"),
 ("E sin_granulos de cualquier dia", RS, 'and i.get("fecha") == dia}', "}"),
 ("F cobertura ausente no es falla", RS, 'fallas.append("no hay JSON de cobertura legible: no se sabe qué se buscó")', "pass"),
 ("G fallas de fin ignoradas", RS, 'fallas.append(f"cobertura incompleta: {de_hoy} búsquedas o descargas fallidas del {fin} o sin fecha")', "pass"),
 ("H una plataforma vacia basta", RS, "if p not in vacias:\n            return None", "if p not in vacias:\n            continue"),
 ("I dia sin records nunca falla", RS, 'fallas.append(f"{s} {d}: ningún record de la vía y ninguna prueba de que no hubo pasada")', "pass"),
 ("J monitor cuenta workflow_dispatch", JS, "r.event === 'schedule' && r.status === 'completed'", "r.status === 'completed'"),
 ("K monitor tope 200 h", JS, "maxHoras = 26", "maxHoras = 200"),
 ("L monitor desde 2020", JS, "const SOMBRA_DESDE = '2026-11-03T15:00:00Z';", "const SOMBRA_DESDE = '2020-11-03T15:00:00Z';"),
 ("M monitor cuenta runs no terminados", JS, "r.status === 'completed' &&\n      r.conclusion === 'success'", "r.conclusion !== 'failure'"),
 ("N workflow sin always() en upload", WF, "if: always() && steps.correr.outputs.corrio == 'true' && steps.tachar.outcome == 'success'", "if: steps.correr.outputs.corrio == 'true' && steps.tachar.outcome == 'success'"),
 ("O workflow --sha vacio", WF, '--sha "${{ github.sha }}"', '--sha ""'),
 ("P workflow inicio constante", WF, "INICIO=$(date -u +%Y-%m-%dT%H:%M:%SZ)", "INICIO=2000-01-01T00:00:00Z"),
 ("P2 workflow inicio en otro formato", WF, "INICIO=$(date -u +%Y-%m-%dT%H:%M:%SZ)", "INICIO=$(date -u +%Y-%m-%d)"),
 ("Q monitor sin if always()", MON, "        if: always()\n        uses: actions/github-script@v7\n        with:\n          retries: 3", "        uses: actions/github-script@v7\n        with:\n          retries: 3"),
 ("R monitor sin permiso issues", MON, "  issues: write\n", ""),
 ("R2 monitor sin permiso actions", MON, "  actions: read\n", ""),
 # ronda 2
 ("V2 catalogo vacio no es falla", RS, 'if set(sensores) <= set(sin_pasada_d) or {"VIIRS750", "VIIRS375"} <= set(sin_pasada_d):', "if False:"),
 ("V2b solo los tres sensores", RS, 'if set(sensores) <= set(sin_pasada_d) or {"VIIRS750", "VIIRS375"} <= set(sin_pasada_d):', "if set(sensores) <= set(sin_pasada_d):"),
 ("V3 toda falla de cobertura es FALLA", RS, "if fecha and fecha < fin:", "if False:"),
 ("V3b toda falla de cobertura es NOTA", RS, "if fecha and fecha < fin:", "if True:"),
 ("V4 sin pendiente", JS, "if (pendiente) {", "if (false) {"),
 ("V4b pendiente sin tope de edad", JS, "horasPendiente = 6", "horasPendiente = 600"),
 ("V4c yml no sale con pendiente", MON, "if (d.accion === 'inactivo' || d.accion === 'pendiente') return;", "if (d.accion === 'inactivo') return;"),
 ("V5 resumen del job sin la linea", RS, 'fh.write("### Revisión de la sombra', '(lambda *a: None)("### Revisión de la sombra'),
 ("V5b K solo de esta corrida", RS, 'for r in en_ventana:\n        if r.get("via_codigo_mirova") is not True:\n            k = str(r.get("via_codigo_mirova"))\n            k_ventana', 'for r in nuevos:\n        if r.get("via_codigo_mirova") is not True:\n            k = str(r.get("via_codigo_mirova"))\n            k_ventana'),
 ("V7 tachar no reemplaza", TA, 'txt = txt.replace(v, "***")', "pass"),
 ("V7b workflow no tacha", WF, "python scripts/tachar_secreto_log.py pipeline.log cobertura.json", "true"),
 # ronda 3 (control por día, VR2-01 a VR2-05)
 ("W1 sin control de corrida muerta", RS, 'fallas.append("ningún record de la vía escrito en esta corrida: la corrida no produjo nada")', "pass"),
 ("W2 dias antes de la fecha minima se juzgan", RS, "a = max(date.fromisoformat(ini), date.fromisoformat(FECHA_MINIMA))", "a = date.fromisoformat(ini)"),
 ("W3 sin control por dia (solo fin)", RS, "        for d in dias:\n", "        for d in dias[-1:]:\n"),
 ("W4 un K cuenta como record de la via", RS, '        if r.get("via_codigo_mirova") is True:\n            hay.add(', '        if True:\n            hay.add('),
 ("W5 la prueba de ausencia de otro dia vale", RS, "vacias = _sin_pasada(s, cobertura or {}, d)", "vacias = _sin_pasada(s, cobertura or {}, fin)"),
 ("W6 fecha minima distinta", RS, 'FECHA_MINIMA = "2026-11-03"', 'FECHA_MINIMA = "2026-11-04"'),
 ("W7 JSON corrupto sin linea de K", RS, '        resumen += "\\n  K caídos en la ventana: sin dato (el JSON de la sombra no se pudo leer)"', "        pass"),
 ("W8 desde-utc vacio no es falla", RS, '        fallas.append(f"--desde-utc vacío o ilegible ({desde_utc!r}): no se sabe qué escribió esta corrida")', "        pass"),
 ("W9 cobertura corrupta da traceback", RS, "    except (OSError, ValueError) as e:\n        errores.append", "    except OSError as e:\n        errores.append"),
 ("T1 tachado falla abierto", TA, "    return 1 if fallo else 0", "    return 0"),
 ("T2 upload no espera al tachado", WF, " && steps.tachar.outcome == 'success'", ""),
 ("T3 sin variante url", TA, "quote(token, safe=\"\"), quote_plus(token), ", ""),
 ("T4 sin variante json escapada", TA, ' token.replace("/", "\\\\/"),\n          json.dumps(token)[1:-1].replace("/", "\\\\/")}', "}"),
 # las 4 de VR2-05 (X3, X8, X12, X13 del verificador)
 ("X3 frontera de 6 h inclusiva", JS, "< horasPendiente", "<= horasPendiente"),
 ("X8 falla sin fecha pasa a NOTA", RS, "if fecha and fecha < fin:", "if fecha < fin:"),
 ("X12 token sin strip", TA, 'token = (os.environ.get("EARTHDATA_TOKEN") or "").strip()', 'token = (os.environ.get("EARTHDATA_TOKEN") or "")'),
 ("X13 sin guarda de token vacio", TA, "    if not token:\n        print(", "    if False:\n        print("),
 # mutaciones propias del verificador R3 sobre T1
 ("Y1 el ultimo dia (fin) no se juzga", RS, "for i in range((b - a).days + 1)]", "for i in range((b - a).days)]"),
 ("Y2 el primer dia no se juzga", RS, "return [(a + timedelta(days=i)).isoformat() for i in range((b - a).days + 1)]", "return [(a + timedelta(days=i + 1)).isoformat() for i in range((b - a).days)]"),
 ("Y3 cualquier incidencia vale como prueba", RS, 'if i.get("tipo") == "sin_granulos" and i.get("fecha") == dia}', 'if i.get("fecha") == dia}'),
 ("Y4 un record de otro sensor cubre el dia", RS, "if (d, s) in hay:", "if any((d, x) in hay for x in sensores):"),
 ("Y6 corrida muerta: basta un K nuevo", RS, 'via_nuevos = sum(1 for r in nuevos if r.get("via_codigo_mirova") is True)', "via_nuevos = len(nuevos)"),
 ("Y7 SNPP vivo no exigido", RS, "if p not in vacias:\n            return None", "if p not in vacias and not p.startswith('VIIRS_SNPP'):\n            return None"),
 ("Y8 catalogo vacio solo con tres sensores", RS, 'or {"VIIRS750", "VIIRS375"} <= set(sin_pasada_d)', "or False"),
 ("Y9 retirada cuenta como vacia aunque cese sea posterior", RS, "if cese is not None and inicio_dia is not None and inicio_dia >= cese:", "if cese is not None and inicio_dia is not None:"),
]


def correr():
    if os.path.exists(XML):
        os.remove(XML)
    subprocess.run([PY, "-m", "pytest", "-p", "no:cacheprovider", "-q", "--basetemp=" + TMP, "--junitxml=" + XML,
                    "tests/test_revisar_sombra_corrida_s169.py", "tests/test_monitor_sombra_s169.py"],
                   cwd=DST, capture_output=True, text=True, encoding="utf-8",
                   env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    if not os.path.exists(XML):
        return None
    total, por_tipo, nombres = 0, {}, []
    for tc in ET.parse(XML).getroot().iter("testcase"):
        total += 1
        for tag in ("failure", "error"):
            el = tc.find(tag)
            if el is None:
                continue
            # pytest no pone `type` en su XML: la clase sale del mensaje («AssertionError: ...» o «assert ...» de un
            # assert desnudo) y de la última línea del traceback («E   SomeError: ...»). Un <error> nunca es aserción.
            msg = el.get("message") or ""
            texto = el.text or ""
            ultima_e = [ln for ln in texto.splitlines() if ln.startswith("E   ")]
            if tag == "failure" and (msg.startswith("AssertionError") or msg.startswith("assert ")
                                     or (ultima_e and "AssertionError" in ultima_e[-1])):
                t = "AssertionError"
            else:
                t = tag + ":" + (msg.split(":")[0][:40] or "?")
            por_tipo[t] = por_tipo.get(t, 0) + 1
            if t == "AssertionError":
                nombres.append(tc.get("name"))
    return total, por_tipo, nombres


atrapadas = sobreviven = 0
SEL = sys.argv[2:]
for nombre, f, a, b in MUT:
    if SEL and nombre != "ninguna" and not any(nombre.startswith(x) for x in SEL):
        continue
    orig = None
    if f:
        p = os.path.join(DST, f)
        orig = open(p, encoding="utf-8", newline="").read()
        if orig.count(a) != 1:
            print(f"{nombre}: PATRON NO ENCONTRADO o repetido ({orig.count(a)})", flush=True)
            sobreviven += 1
            continue
        open(p, "w", encoding="utf-8", newline="").write(orig.replace(a, b, 1))
    res = correr()
    if f:
        open(p, "w", encoding="utf-8", newline="").write(orig)
    if res is None:
        print(f"{nombre}: SIN XML (pytest no corrió)", flush=True)
        sobreviven += f is not None
        continue
    total, por_tipo, nombres = res
    if not f or nombre.startswith("CONTROL"):
        print(f"{nombre}: {total} pruebas, fallas {por_tipo or 'ninguna'} | CONTROL, por aserción: {len(nombres)}",
              flush=True)
        continue
    estado = "ATRAPADA" if nombres else "SOBREVIVE"
    atrapadas += bool(nombres); sobreviven += not nombres
    print(f"{nombre}: {total} pruebas, fallas {por_tipo} | {estado} | {nombres[:3]}", flush=True)
print(f"TOTAL: {atrapadas} atrapadas por aserción, {sobreviven} sobreviven de {atrapadas + sobreviven}")
