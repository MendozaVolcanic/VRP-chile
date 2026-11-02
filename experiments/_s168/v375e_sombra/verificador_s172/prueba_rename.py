# Verificador S172: hueco del rename del perfil de produccion (git diff --name-only con deteccion de renombre).
# Q1: si fuera falso que el rename pasa, esto lo veria: imprime [] o [ruta]. Q2: un instrumento muerto (None) se distingue de [].
import importlib.util, subprocess, sys
from pathlib import Path
sys.dont_write_bytecode = True
repo = Path("D:/vrp-trabajo/temporales/ver_s172_relector/repo_juguete")
spec = importlib.util.spec_from_file_location("LS", "D:/vrp-trabajo/worktrees/s172-relector/experiments/_s168/v375e_sombra/leer_sombra_v375e.py")
LS = importlib.util.module_from_spec(spec); spec.loader.exec_module(LS); LS.RAIZ = repo
def g(*a):
    r = subprocess.run(["git", "-C", str(repo)] + list(a), capture_output=True, text=True, encoding="utf-8"); assert r.returncode == 0, r.stderr; return r.stdout.strip()
C1 = g("log", "--format=%H", "--grep=^C1$", "-1")
g("checkout", "-q", "-B", "rn", C1)
g("mv", "pipeline/profiles/mirova_equivalent.yaml", "pipeline/profiles/mirova_equivalente_v2.yaml"); g("commit", "-qm", "rename")
R = g("rev-parse", "HEAD")
print("C1->rename del perfil de produccion: nombres crudos", LS.nombres_git(C1, R), "| diff_git", LS.diff_git(C1, R))
g("checkout", "-q", "-B", "rn2", C1)
g("mv", "pipeline/profiles/sombra_codigo_mirova.yaml", "pipeline/profiles/sombra_v2.yaml"); g("commit", "-qm", "rename2")
R2 = g("rev-parse", "HEAD")
print("C1->rename del perfil de la sombra: nombres crudos", LS.nombres_git(C1, R2), "| diff_git", LS.diff_git(C1, R2))
g("checkout", "-q", "-B", "del", C1)
g("rm", "-q", "pipeline/profiles/sombra_codigo_mirova.yaml"); g("commit", "-qm", "del")
R3 = g("rev-parse", "HEAD")
print("C1->borrado puro del perfil de la sombra: nombres crudos", LS.nombres_git(C1, R3), "| diff_git", LS.diff_git(C1, R3))
