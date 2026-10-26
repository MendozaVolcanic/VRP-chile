"""v06_mutaciones.py (A8, instrumento propio): sobre una copia propia de mut/ (codigo del PR), corre
tests/test_bucle_push_main_yml.py (a) sin mutar, (b) con el main.yml de main (linea base roja), (c) con las 4
mutaciones de workflow del autor. Clasifica cada prueba por el MENSAJE de la falla (AssertionError en la
aserción prevista, otra excepcion, o error de fixture), no solo por el conteo del JUnit."""
import os, shutil, subprocess, sys, xml.etree.ElementTree as ET
sys.stdout.reconfigure(encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
SRC = r"D:\vrp-trabajo\s163-d39\mut"
M = os.path.join(AQUI, "mut_v")
CLON = r"D:\vrp-trabajo\s163-d39\mirova-v1"
if not os.path.exists(M):
    shutil.copytree(SRC, M, ignore=shutil.ignore_patterns("imagenes_satelitales", "__pycache__", ".pytest_cache", "junit_mut.xml"))
def git_show(rev, ruta):
    return subprocess.run(["git", "-C", CLON, "show", f"{rev}:{ruta}"], capture_output=True, check=True).stdout.decode("utf-8")
MAINYML = ".github/workflows/main.yml"; OCRYML = ".github/workflows/ocr_workflow.yml"
CASOS = [
 ("control: main.yml del PR (mut/)", None, None),
 ("linea base: main.yml de main (f5fe3b9a64)", MAINYML, ("TEXTO", git_show("main", MAINYML))),
 ("main.yml de la rama s163 (2ad6dd8730)", MAINYML, ("TEXTO", git_show("s163/d39-reposicion-y-bucle", MAINYML))),
 ("R2 main.yml sin reset a origin/main", MAINYML, ("REEMPLAZO", "            git reset --hard origin/main\n", "")),
 ("R2 main.yml vuelve el pull -X ours antes del push", MAINYML, ("REEMPLAZO", "            if git push origin main; then echo", "            git pull origin main --rebase --autostash -X ours || true\n            if git push origin main; then echo")),
 ("R3 main.yml sin guarda", MAINYML, ("REEMPLAZO", '            python guarda_llaves.py "$CSV" --ref origin/main\n', "")),
 ("R2 ocr_workflow vuelve -X ours", OCRYML, ("REEMPLAZO", "if ! git pull origin main --rebase --autostash; then", "if ! git pull origin main --rebase --autostash -X ours; then")),
 ("mutacion propia: main.yml con fetch sin reset pero con pull --rebase SIN -X ours", MAINYML, ("REEMPLAZO", "            git reset --hard origin/main\n", "            git pull origin main --rebase --autostash || true\n")),
]
env = dict(os.environ, PYTHONUTF8="1"); env.pop("MSYS_NO_PATHCONV", None)
for nom, archivo, cambio in CASOS:
    orig = None
    if archivo:
        p = os.path.join(M, archivo); orig = open(p, encoding="utf-8", newline="").read()
        if cambio[0] == "TEXTO":
            nuevo = cambio[1]
        else:
            assert orig.count(cambio[1]) == 1, (nom, orig.count(cambio[1]))
            nuevo = orig.replace(cambio[1], cambio[2])
        open(p, "w", encoding="utf-8", newline="").write(nuevo)
    try:
        x = os.path.join(M, "junit_v06.xml")
        r = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", f"--junitxml={x}",
                            "tests/test_bucle_push_main_yml.py"], cwd=M, env=env, capture_output=True, text=True)
        t = ET.parse(x).getroot(); s = t if t.tag == "testsuite" else t[0]
        print(f"== {nom}: tests {s.get('tests')} failures {s.get('failures')} errors {s.get('errors')} skipped {s.get('skipped')}", flush=True)
        for c in s.iter("testcase"):
            f = c.find("failure"); e = c.find("error"); sk = c.find("skipped")
            if f is not None:
                msg = (f.get("message") or "").splitlines()[0][:160]
                tipo = "AssertionError" if "AssertionError" in (f.get("message") or "") or (f.text or "").strip().startswith("AssertionError") or "assert" in (f.get("message") or "") else "OTRA EXCEPCION"
                print(f"   FALLA {c.get('name')}: [{tipo}] {msg}", flush=True)
            elif e is not None:
                print(f"   ERROR {c.get('name')}: {(e.get('message') or '')[:160]}", flush=True)
            elif sk is not None:
                print(f"   SALTADA {c.get('name')}: {(sk.get('message') or '')[:120]}", flush=True)
            else:
                print(f"   pasa {c.get('name')}", flush=True)
    finally:
        if orig is not None:
            open(p, "w", encoding="utf-8", newline="").write(orig)
print("FIN", flush=True)
