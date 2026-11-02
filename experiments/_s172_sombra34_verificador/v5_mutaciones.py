"""VS34 V-5: mutaciones propias sobre una COPIA (copia/, git archive de 30d9f9418) para ver si las pruebas pueden fallar.
Q1: cada mutacion es un defecto plausible que NO debe pasar; 'ATRAPADA' = alguna prueba cae por la razon correcta
(se imprime la primera linea FAILED). 'NO ATRAPADA' = el defecto pasa en verde.
Q2: la corrida sin mutar (control) debe dar verde (52 passed, v5_base_verde_salida.txt) y una mutacion trivial
(romper la sintaxis del archivo) debe dar rojo (control positivo del instrumento).
Se restaura el archivo despues de cada mutacion."""
import subprocess, sys, os, re, shutil, time
BASE = "D:/vrp-trabajo/temporales/ver_s172_sombra34/copia"
env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
T = "tests/test_sombra_34_s172.py"
def rd(p): return open(f"{BASE}/{p}", encoding="utf-8").read()
def wr(p, s): open(f"{BASE}/{p}", "w", encoding="utf-8", newline=chr(10)).write(s)
def run(files=(T,), k=None):
    cmd = [sys.executable, "-m", "pytest", *files, "-q", "-p", "no:cacheprovider", "-x"]
    if k: cmd += ["-k", k]
    p = subprocess.run(cmd, cwd=BASE, env=env, capture_output=True, text=True, encoding="utf-8")
    out = p.stdout + p.stderr
    fails = [l for l in out.splitlines() if l.startswith("FAILED") or " passed" in l or " failed" in l or "error" in l.lower()[:40]]
    return p.returncode, fails[:3]
HECHAS = ("CTRL", "G1 ", "G2 ", "G3 ", "G4 ", "G5 ", "G6 ", "W1 ")
def mut(nombre, path, viejo, nuevo, files=(T,), k=None, count=1):
    if nombre.startswith(HECHAS): return
    s = rd(path)
    if callable(viejo): viejo, nuevo = viejo(s), nuevo
    assert viejo in s, f"{nombre}: patron no encontrado en {path}"
    wr(path, s.replace(viejo, nuevo, count))
    t0 = time.time()
    try:
        rc, f = run(files, k)
    finally:
        wr(path, s)
    print(f"{'ATRAPADA   ' if rc != 0 else 'NO ATRAPADA'} | {nombre} | {int(time.time()-t0)}s | {f}", flush=True)
G, WF, VG, VW, PF = "pipeline/grillas_mirova.yaml", ".github/workflows/sombra-34.yml", "scripts/vigilar_sombra_34.py", ".github/workflows/vigilancia-sombra-34.yml", "pipeline/profiles/sombra_34.yaml"
# control positivo del instrumento: sintaxis rota
mut("CTRL: sintaxis rota en vigilar_sombra_34.py", VG, "import argparse", "import argparse\n)(", k="vigilancia")
# grillas
mut("G1 Hudson x0 +5000 m", G, "x0: 657469.5", "x0: 662469.5")
mut("G2 Lascar (Tier A) y0 +1 m", G, "y0: 7414948.7", "y0: 7414949.7")
mut("G3 Mocho-Choshuenco epsg 32718->32719", G, "MochoChoshuenco:     {epsg: 32718", "MochoChoshuenco:     {epsg: 32719")
mut("G4 Antuco roi_v750 def->sens", G, "Antuco:              {epsg: 32719, x0: 292096.3, y0: 5857497.5, centro_lat: -37.40600, centro_lon: -71.34900, roi_v750: def}", "Antuco:              {epsg: 32719, x0: 292096.3, y0: 5857497.5, centro_lat: -37.40600, centro_lon: -71.34900, roi_v750: sens}")
mut("G5 Taapaca centro_lat 0.5 grados corrido (V750)", G, "centro_lat: -18.10000", "centro_lat: -18.60000")
mut("G6 grilla de Hudson borrada (queda sin grilla)", G, lambda t: [l for l in t.splitlines(True) if l.lstrip().startswith("Hudson:")][0], "")
# workflow
mut("W1 cron dentro de la ventana del NRT (7 5)", WF, 'cron: "7 13 * * *"', 'cron: "7 5 * * *"')
mut("W2 EARTHDATA_USERNAME agregado", WF, "EARTHDATA_TOKEN: ${{ secrets.EARTHDATA_TOKEN }}\n          VRP_MEDIR", "EARTHDATA_TOKEN: ${{ secrets.EARTHDATA_TOKEN }}\n          EARTHDATA_USERNAME: x\n          VRP_MEDIR")
mut("W3 un volcan sale de la matriz (Hudson)", WF, "Hudson, ", "")
mut("W4 git add de la carpeta de la sombra de los 11", WF, 'git add "data/sombra_34/${{ matrix.volcano }}.json"', 'git add "data/sombra_codigo_mirova/${{ matrix.volcano }}.json"')
mut("W5 grupo de concurrencia push-main", WF, "group: sombra-34", "group: push-main")
mut("W6 sin corte por token vacio", WF, '-z "$EARTHDATA_TOKEN"', '-z "$OTRA"')
mut("W7 workflow escribe en data/mirova_equivalent (--profile mirova_equivalent)", WF, "--profile sombra_34 --volcano", "--profile mirova_equivalent --volcano")
mut("W8 timeout del paso 75 -> 5 min", WF, "timeout-minutes: 75", "timeout-minutes: 5")
mut("W9 permissions contents write -> read (el push fallaria)", WF, "contents: write", "contents: read")
mut("W10 fail-fast true", WF, "fail-fast: false", "fail-fast: true")
mut("W11 paso Tachar sin always (no se sube nunca tras fallo)", WF, "- name: Tachar el token en el log y la cobertura\n        id: tachar\n        if: always() && steps.correr.outputs.corrio == 'true'", "- name: Tachar el token en el log y la cobertura\n        id: tachar\n        if: steps.correr.outputs.corrio == 'true'")
mut("W12 revision de records pierde always()", WF, "if: always() && steps.correr.outputs.corrio == 'true'\n        run: |\n          python scripts/revisar_sombra.py", "if: steps.correr.outputs.corrio == 'true'\n        run: |\n          python scripts/revisar_sombra.py")
# perfil
mut("P1 data_subdir = mirova_equivalent", PF, "data_subdir: sombra_34", "data_subdir: mirova_equivalent")
mut("P2 enable_test1_path true", PF, "enable_test1_path: false", "enable_test1_path: true")
mut("P3 enable_modis_codigo_mirova false", PF, "enable_modis_codigo_mirova: true", "enable_modis_codigo_mirova: false")
mut("P4 volcano_overrides con inner 5 agregado", PF, "output:\n  data_subdir: sombra_34", "volcano_overrides:\n  Hudson: {inner_radius_km: 5}\noutput:\n  data_subdir: sombra_34")
# vigilancia script
mut("V1 acepta via truthy (no solo True)", VG, 'r.get("via_codigo_mirova") is not True', 'not r.get("via_codigo_mirova")')
mut("V2 ventana default 48 -> 480 h", VG, "def vigilar(dir_datos, volcanes, ahora, horas=48, alta=None)", "def vigilar(dir_datos, volcanes, ahora, horas=480, alta=None)")
mut("V3 ignora el perfil", VG, 'reg.get("perfil") != PERFIL', 'False')
mut("V4 matriz vacia da OK", VG, 'out["veredicto"] = "CIEGA"\n        out["ciegos"].append({"volcano": None', 'out["veredicto"] = "OK"\n        out["ciegos"].append({"volcano": None')
mut("V5 exit 0 aun en CIEGA", VG, 'return 1 if d["veredicto"] == "CIEGA" else 0', 'return 0')
mut("V6 un solo volcan fresco basta (all->any)", VG, 'out["veredicto"] = "CIEGA" if out["ciegos"] else "OK"', 'out["veredicto"] = "CIEGA" if len(out["ciegos"]) == len(volcanes) else "OK"')
# vigilancia workflow
mut("VW1 CIEGA no abre issue (se mezcla con OK)", VW, "OK|ESPERA) echo", "OK|ESPERA|CIEGA) echo")
mut("VW2 --dir apunta a la sombra de los 11", VW, "--dir data/sombra_34", "--dir data/sombra_codigo_mirova")
mut("VW3 cron imposible (31 de febrero)", VW, 'cron: "27 23 * * *"', 'cron: "27 23 31 2 *"')
mut("VW4 checkout de otra rama", VW, "ref: main", "ref: gh-pages")
mut("VW5 permissions issues write -> read", VW, "issues: write", "issues: read")
mut("VW6 abrir() nunca crea (solo comenta)", VW, 'gh issue create --title', 'echo gh-issue-create-omitido --title')
mut("VW7 veredicto leido de otro archivo", VW, "veredicto.json')['veredicto']", "veredicto_x.json')['veredicto']")
print("FIN")
