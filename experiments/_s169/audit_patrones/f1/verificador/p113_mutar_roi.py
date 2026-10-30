# -*- coding: utf-8 -*-
"""VF P1-13: mutaciones PROPIAS de scripts/roi_v750b_a_grillas.py (rama s169-roi-v750, 3c5c494b9, extraida a roi_vf/)
contra tests/test_roi_v750b_variantes_s169.py. Cada mutacion se aplica sobre una copia del arbol (el original no se
toca), se corre pytest y se clasifica: ATRAPADA (falla por asercion), CAIDA (error de coleccion/import: no cuenta como
atrapada), NO ATRAPADA (verde). Pregunta 1: si main() estuviera roto, ¿la prueba lo veria? -> mutaciones M1..M4 en main().
Pregunta 2 (control): M0 identidad tiene que salir verde; C1 (mutacion en variante()) tiene que salir ATRAPADA; C2
(rompe el import) tiene que salir CAIDA. Ademas, control directo: correr main() --escribir en la copia y ver el YAML."""
import sys, shutil, subprocess, pathlib, re, os, tempfile
sys.stdout.reconfigure(encoding="utf-8")
BASE = pathlib.Path("roi_vf").resolve()
SCRIPT = "scripts/roi_v750b_a_grillas.py"
orig = (BASE / SCRIPT).read_text(encoding="utf-8")
MUT = {
    "M0 identidad": (None, None),
    "C1 control: variante pone siempre def": ("texto = patron.sub(lambda m: m.group(1) + tipo + m.group(3), texto)",
                                              "texto = patron.sub(lambda m: m.group(1) + 'def' + m.group(3), texto)"),
    "C2 control: import roto": ("import difflib\n", "import difflib\nimport modulo_que_no_existe\n"),
    "M1 main: --escribir no escribe": ('        YAML.write_text(nuevo, encoding="utf-8", newline="")\n', "        pass\n"),
    "M2 main: escribe el viejo": ('YAML.write_text(nuevo,', 'YAML.write_text(viejo,'),
    "M3 main: ignora --brazo (siempre B4)": ("nuevo = variante(viejo, a.brazo)", "nuevo = variante(viejo, 'B4')"),
    "M4 main: choices acepta B6": ('choices=("B0", "B1", "B2", "B3", "B4", "B5")', 'choices=("B0", "B1", "B2", "B3", "B4", "B5", "B6")'),
    "M5 variante: comentario solo si brazo B1": ('    if brazo != "B0":\n        if texto.count', '    if brazo == "B1":\n        if texto.count'),
}
def correr(arbol):
    env = {k: v for k, v in os.environ.items() if k != "VRP_PROFILE"}; env["PYTHONIOENCODING"] = "utf-8"
    o = subprocess.run([sys.executable, "-I", "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests/test_roi_v750b_variantes_s169.py"],
                       cwd=arbol, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=240)
    ult = [l for l in o.stdout.splitlines() if re.search(r"passed|failed|error", l)][-1:] or ["?"]
    return o.returncode, ult[0], o.stdout
for nombre, (viejo, nuevo) in MUT.items():
    d = pathlib.Path(tempfile.mkdtemp(dir=".", prefix="mut_"))
    shutil.copytree(BASE, d / "a")
    if viejo is not None:
        assert orig.count(viejo) == 1, (nombre, orig.count(viejo))
        (d / "a" / SCRIPT).write_text(orig.replace(viejo, nuevo), encoding="utf-8")
    rc, ult, out = correr(d / "a")
    if rc == 0: est = "NO ATRAPADA (verde)"
    elif "error" in ult and "failed" not in ult: est = "CAIDA (error de coleccion, no cuenta)"
    else: est = "ATRAPADA por asercion" if "assert" in out.lower() else "falla sin asercion visible"
    print(f"{nombre:45s} rc={rc} {est} | {ult.strip()}")
    shutil.rmtree(d, ignore_errors=True)
# control directo del efecto de main() --escribir y de la doble aplicacion
d = pathlib.Path(tempfile.mkdtemp(dir=".", prefix="main_")); shutil.copytree(BASE, d / "a"); y = d / "a/pipeline/grillas_mirova.yaml"
def run(*args):
    return subprocess.run([sys.executable, "-I", str(d / "a" / SCRIPT), *args], capture_output=True, text=True, encoding="utf-8")
crlf0 = y.read_bytes().count(b"\r\n")
r1 = run("--brazo", "B1", "--escribir"); t1 = y.read_text(encoding="utf-8")
r2 = run("--brazo", "B4", "--escribir"); t2 = y.read_text(encoding="utf-8")
print("\ncontrol main(): B1 --escribir rc", r1.returncode, "| roi sens en", len(re.findall(r"roi_v750: sens", t1)), "de 11")
print("doble aplicacion B1 y luego B4: roi sens en", len(re.findall(r"roi_v750: sens", t2)), "def en", len(re.findall(r"roi_v750: def", t2)),
      "| comentario dice:", [l for l in t2.splitlines() if "Puesto por la lectura" in l])
y2 = d / "a/pipeline/grillas_mirova.yaml"; b = y2.read_bytes()
print("finales de linea: CRLF antes", crlf0, "despues", b.count(b"\r\n"))
shutil.rmtree(d, ignore_errors=True)
