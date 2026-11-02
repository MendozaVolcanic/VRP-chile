# -*- coding: utf-8 -*-
"""Verificador S172, A4 con git real: repo de juguete en CARPETA con los archivos REALES de origin/main (insumos/).
Q1: si diff_git estuviera roto, ¿lo veria? Si: el commit C3 (edita la asercion) debe dar [WF] y C1/C2 no.
Q2: si el instrumento estuviera muerto (git no resuelve -> None), el resultado se veria distinto (None != []).
Ventana: ninguna (texto de archivos de origin/main sha en insumos/origin_main_sha.txt)."""
import importlib.util, subprocess, sys, shutil
from pathlib import Path
sys.dont_write_bytecode = True
C = Path("D:/vrp-trabajo/temporales/ver_s172_relector")
spec = importlib.util.spec_from_file_location("LS", "D:/vrp-trabajo/worktrees/s172-relector/experiments/_s168/v375e_sombra/leer_sombra_v375e.py")
LS = importlib.util.module_from_spec(spec); spec.loader.exec_module(LS)
repo = C / "repo_juguete"
if repo.exists():
    import os, stat
    shutil.rmtree(repo, onerror=lambda f, p, e: (os.chmod(p, stat.S_IWRITE), f(p)))
(repo / "pipeline/profiles").mkdir(parents=True); (repo / ".github/workflows").mkdir(parents=True); (repo / "scripts").mkdir()
def g(*a):
    r = subprocess.run(["git", "-C", str(repo)] + list(a), capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (a, r.stderr)
    return r.stdout.strip()
g("init", "-q"); g("config", "user.email", "v@x"); g("config", "user.name", "v"); g("config", "core.autocrlf", "false")
ME = (C / "insumos/ME_main.yaml").read_text(encoding="utf-8"); SO = (C / "insumos/SO_main.yaml").read_text(encoding="utf-8")
WF = (C / "insumos/WF_main.yml").read_text(encoding="utf-8")
def w(p, t):
    (repo / p).parent.mkdir(parents=True, exist_ok=True); (repo / p).write_text(t, encoding="utf-8", newline="\n")
w("pipeline/profiles/mirova_equivalent.yaml", ME); w("pipeline/profiles/sombra_codigo_mirova.yaml", SO)
w(".github/workflows/sombra-codigo-mirova.yml", WF); w("scripts/run_pipeline.py", "x = 1\n")
g("add", "-A"); g("commit", "-qm", "base"); B = g("rev-parse", "HEAD")
# C1: sólo encender MODIS en producción + guardia en perfil nuevo + workflow nuevo
w("pipeline/profiles/mirova_equivalent.yaml", ME.replace("thresholds:\n", "thresholds:\n  enable_modis_codigo_mirova: true\n", 1))
w("pipeline/profiles/guardia_k.yaml", "extends: mirova_equivalent\nthresholds:\n  enable_modis_codigo_mirova: false\n")
w(".github/workflows/guardia-k.yml", "name: guardia\n")
w("tests/test_guardia.py", "def test_x(): pass\n")
w("frontend/index.html", "<html>cambio</html>\n")
g("add", "-A"); g("commit", "-qm", "C1"); C1 = g("rev-parse", "HEAD")
# C2: + edita la asercion de la l.110 del workflow de la sombra
lin = WF.splitlines()
w(".github/workflows/sombra-codigo-mirova.yml", "\n".join(lin[:109] + [lin[109].replace(" and p.ENABLE_MODIS_CODIGO_MIROVA", "")] + lin[110:]) + "\n")
g("add", "-A"); g("commit", "-qm", "C2"); C2 = g("rev-parse", "HEAD")
# C3: renombra mirova_equivalent.yaml (git ve un rename)
g("mv", "pipeline/profiles/mirova_equivalent.yaml", "pipeline/profiles/mirova_equivalente_v2.yaml"); g("commit", "-qm", "C3"); C3 = g("rev-parse", "HEAD")
# C4: renombra un .py de pipeline/ (control del rename)
w("pipeline/uno.py", "import os\n" * 3); g("add", "-A"); g("commit", "-qm", "C4a"); C4a = g("rev-parse", "HEAD")
g("mv", "pipeline/uno.py", "pipeline/dos.py"); g("commit", "-qm", "C4b"); C4b = g("rev-parse", "HEAD")
LS.RAIZ = repo
print("base->C1 (MODIS on + guardia perfil nuevo + workflow nuevo + test + index.html):", LS.diff_git(B, C1))
print("   nombres crudos base->C1:", LS.nombres_git(B, C1))
print("base->C2 (+ edita asercion l.110):", LS.diff_git(B, C2))
print("base->C3 (rename del perfil de produccion):", LS.diff_git(B, C3), "| nombres crudos:", LS.nombres_git(B, C3))
print("C4a->C4b (rename de un .py de pipeline/):", LS.diff_git(C4a, C4b), "| nombres crudos:", LS.nombres_git(C4a, C4b))
print("sha inexistente:", LS.diff_git(B, "f" * 40))
ok = (LS.diff_git(B, C1) == [] and LS.diff_git(B, C2) == [".github/workflows/sombra-codigo-mirova.yml"])
print("A4 (git real) CONFIRMADO" if ok else "A4 (git real) REFUTADO")
