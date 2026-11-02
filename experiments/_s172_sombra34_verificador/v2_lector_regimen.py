"""VS34 V-2: que marcaria el lector sellado de V375-E (tag s170-v375e-lector) como cambio de regimen entre la base
(main 14fb62030) y la punta de la rama. Reusa las funciones del lector (extraidas por ast), no las reescribe.
Q1 (si el lector estuviera roto, lo veria?): control positivo = comparar con un cambio sintetico en pipeline/x.py.
Q2 (si el instrumento estuviera muerto?): el resultado seria [] igual que 'no cambia'; por eso se imprime el control."""
import ast, copy, subprocess, sys
SRC = open("lector_s170.py", encoding="utf-8").read()
tree = ast.parse(SRC)
want = {"ast_sin_docstrings", "grillas_sin_roi", "cambio_significativo"}
ns = {"copy": copy, "ast": ast}
consts = {"RUTAS_REGIMEN", "PERFILES_REGIMEN", "GRILLAS", "CLAVES_ROI_IGNORADAS"}
for n in tree.body:
    if isinstance(n, ast.FunctionDef) and n.name in want:
        exec(compile(ast.Module([n], []), "x", "exec"), ns)
    if isinstance(n, ast.Assign) and any(getattr(t, "id", None) in consts for t in n.targets):
        exec(compile(ast.Module([n], []), "x", "exec"), ns)
R = "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
def git(*a):
    p = subprocess.run(["git", "-C", R] + list(a), capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stdout
def diff(a, b):
    rc, out = git("diff", "--name-only", a, b, "--", *ns["RUTAS_REGIMEN"])
    fs = [x for x in out.splitlines() if x.strip()]
    res = []
    for r in fs:
        v = git("show", f"{a}:{r}"); n = git("show", f"{b}:{r}")
        v = v[1] if v[0] == 0 else None; n = n[1] if n[0] == 0 else None
        res.append((r, ns["cambio_significativo"](r, v, n)))
    return res
print("RUTAS_REGIMEN", ns["RUTAS_REGIMEN"], ns["PERFILES_REGIMEN"])
print("base->punta (archivos en rutas de regimen y si cuentan):", diff("pre-s172-sombra-34", "30d9f9418"))
# control positivo: dos commits de main que se sabe tocaron pipeline/*.py
rc, out = git("log", "--format=%H", "-n", "40", "14fb62030", "--", "pipeline/process_viirs.py")
shas = out.split()
print("control positivo (cambio real previo en pipeline/process_viirs.py):", shas[:1])
if len(shas) >= 2:
    print(diff(shas[-1], shas[0]))
