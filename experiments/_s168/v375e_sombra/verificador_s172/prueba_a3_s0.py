# Verificador S172, A3. Q1: si S0 dependiera de main, comparar sha del checkout contra sha de origin/main lo mostraria
# (las dos columnas difieren si main cambio). Q2: instrumento muerto (p.ej. archivo ausente) -> columna 'ausente', distinguible.
# Ventana: ninguna (hashes de archivos a fecha de origin/main sha en insumos/origin_main_sha.txt).
import hashlib, importlib.util, subprocess, sys
from pathlib import Path
sys.dont_write_bytecode = True
W = "D:/vrp-trabajo/worktrees/s172-relector"
R = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
spec = importlib.util.spec_from_file_location("LS", f"{W}/experiments/_s168/v375e_sombra/leer_sombra_v375e.py")
LS = importlib.util.module_from_spec(spec); spec.loader.exec_module(LS)
print("RAIZ del lector:", LS.RAIZ)
def sha_main(rel):
    r = subprocess.run(["git", "-C", R, "show", f"origin/main:{rel}"], capture_output=True, env={**__import__("os").environ, "MSYS_NO_PATHCONV": "1"})
    return hashlib.sha256(r.stdout.replace(b"\r\n", b"\n")).hexdigest() if r.returncode == 0 else "ausente_en_main"
n_ok = n_main_igual = 0
for d in (LS.SHA_DEPS, LS.SHA_SELLO_LECTOR):
    for p, s in d.items():
        rel = str(p.relative_to(LS.RAIZ)).replace("\\", "/")
        loc = LS.sha256_lf(p) if p.exists() else "ausente"
        mn = sha_main(rel)
        n_ok += loc == s; n_main_igual += mn == s
        print(f"{'OK ' if loc == s else 'MAL'} sello==checkout:{loc == s!s:5} sello==origin/main:{mn == s!s:5} {rel}")
tot = len(LS.SHA_DEPS) + len(LS.SHA_SELLO_LECTOR)
print(f"checkout coincide con el sello: {n_ok}/{tot}; origin/main hoy coincide con el sello: {n_main_igual}/{tot}")
import os
os.environ["VRP_PROFILE"] = "mirova_equivalent"
deps, malos = LS.cargar_deps()
print("cargar_deps() (S0) sobre el worktree:", "carga ok" if deps else f"CAE {malos}")
