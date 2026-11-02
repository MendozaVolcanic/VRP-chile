# Verificador S172: control_s8 de punta a punta sobre el repo de juguete (repo_juguete: base B, C1 = MODIS on + guardia,
# C2 = + edita la aserción, ramas rn/rn2 = renombre de perfil). Q1: si control_s8 no mirara los shas, C2 daria True (MAL).
# Q2: instrumento muerto (git no resuelve) -> "git no lo resuelve" en cambios, distinguible de {}.
import importlib.util, subprocess, sys
from pathlib import Path
sys.dont_write_bytecode = True
repo = Path("D:/vrp-trabajo/temporales/ver_s172_relector/repo_juguete")
spec = importlib.util.spec_from_file_location("LS", "D:/vrp-trabajo/worktrees/s172-relector/experiments/_s168/v375e_sombra/leer_sombra_v375e.py")
LS = importlib.util.module_from_spec(spec); spec.loader.exec_module(LS); LS.RAIZ = repo
def g(*a):
    r = subprocess.run(["git", "-C", str(repo)] + list(a), capture_output=True, text=True, encoding="utf-8"); assert r.returncode == 0, r.stderr; return r.stdout.strip()
B = g("log", "--all", "--format=%H", "--grep=^base$", "-1"); C1 = g("log", "--all", "--format=%H", "--grep=^C1$", "-1"); C2 = g("log", "--all", "--format=%H", "--grep=^C2$", "-1")
RN = g("rev-parse", "rn")
def rec(sha, perfil, dt="2026-11-03 05:00"):
    return {"datetime_utc": dt, "regimen": {"perfil": perfil, "codigo_sha": sha}}
K, V = "mirova_equivalent", "sombra_codigo_mirova"
casos = {
 "base=B, K en C1 (MODIS on + guardia)": ([rec(C1, K)], [rec(B, V)]),
 "base=B, K en C2 (+ edita aserción)": ([rec(C2, K)], [rec(B, V)]),
 "base=B, K con el perfil renombrado (records dicen otro perfil)": ([rec(RN, "mirova_equivalente_v2")], [rec(B, V)]),
 "base=B, K en el rename pero records dicen mirova_equivalent (perfil engañoso)": ([rec(RN, K)], [rec(B, V)]),
 "sha que git no resuelve": ([rec("f" * 40, K)], [rec(B, V)]),
}
for nom, (rk, rv) in casos.items():
    ok, det = LS.control_s8(rk, rv, B, LS.diff_git)
    print(f"{('SIN CAMBIO' if ok else 'MARCA'):10} | {nom} | cambios={ {k[:7]: v for k, v in det['cambios'].items()} } perfiles={det['perfiles']}")
