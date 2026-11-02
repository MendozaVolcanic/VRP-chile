# -*- coding: utf-8 -*-
"""¿El PR B marcaría régimen nuevo en el S8 del lector V375-E re-sellado? Reusa las funciones del lector
(copia local lector_resellado_copia.py, del tag s172-v375e-lector-resellado) sobre git diff origin/main...B.

Pregunta 1: si process_modis.py cambiara de verdad, ¿se ve? Sí: ast_sin_docstrings distinto → True.
Pregunta 2: control positivo al final: un archivo con una línea de código agregada da True; sólo un comentario da False.
Uso: python -I s8_regimen_pr_b.py <repo> <base> <punta>
"""
import ast
import copy
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
repo, base, punta = sys.argv[1:4]
RUTAS_REGIMEN = ("pipeline/", "volcanoes.yaml", "scripts/run_pipeline.py", ".github/workflows/sombra-codigo-mirova.yml")
PERFILES_REGIMEN = ("pipeline/profiles/mirova_equivalent.yaml", "pipeline/profiles/sombra_codigo_mirova.yaml")
GRILLAS = "pipeline/grillas_mirova.yaml"
CLAVES_ROI_IGNORADAS = ("roi_v750", "roi_modis")
CLAVES_PERFIL_OTRO_SENSOR = ("enable_modis_codigo_mirova", "enable_v750_codigo_mirova",
                             "enable_modis_geo_mxd03", "enable_modis_crater_sin_dato",
                             "enable_modis_dist_desde_crater")


def git(*a):
    r = subprocess.run(["git", *a], cwd=repo, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env={**__import__("os").environ, "MSYS_NO_PATHCONV": "1"})
    return r.returncode, r.stdout


def ast_sin_docstrings(texto):
    arbol = ast.parse(texto)
    for nodo in ast.walk(arbol):
        if isinstance(nodo, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and nodo.body \
                and isinstance(nodo.body[0], ast.Expr) and isinstance(getattr(nodo.body[0], "value", None), ast.Constant) \
                and isinstance(nodo.body[0].value.value, str):
            nodo.body = nodo.body[1:] or [ast.Pass()]
    return ast.dump(arbol, include_attributes=False)


def perfil_sin_otro_sensor(texto):
    import yaml
    d = copy.deepcopy(yaml.safe_load(texto))
    t = d.get("thresholds") if isinstance(d, dict) else None
    if isinstance(t, dict):
        for k in CLAVES_PERFIL_OTRO_SENSOR:
            t.pop(k, None)
    return d


def mostrar(rev, ruta):
    rc, out = git("show", f"{rev}:{ruta}")
    return out if rc == 0 else None


def cambio_significativo(ruta, viejo, nuevo):
    if ruta.startswith("pipeline/profiles/"):
        if ruta not in PERFILES_REGIMEN:
            return False
        if None in (viejo, nuevo):
            return True
        return perfil_sin_otro_sensor(viejo) != perfil_sin_otro_sensor(nuevo)
    if viejo is None or nuevo is None:
        return True
    if ruta.endswith(".py"):
        return ast_sin_docstrings(viejo) != ast_sin_docstrings(nuevo)
    if ruta == GRILLAS:
        raise NotImplementedError
    return viejo != nuevo


rc, out = git("diff", "--name-only", base, punta, "--", *RUTAS_REGIMEN)
fs = [x for x in out.splitlines() if x.strip()]
print(f"archivos de RUTAS_REGIMEN que cambian entre {base} y {punta}: {len(fs)}")
marcan = []
for r in fs:
    sig = cambio_significativo(r, mostrar(base, r), mostrar(punta, r))
    print(f"  {'MARCA ' if sig else 'no    '} {r}")
    if sig:
        marcan.append(r)
print("RESULTADO S8:", "RÉGIMEN NUEVO por " + ", ".join(marcan) if marcan else "sin cambio de régimen")

# CONTROL positivo del instrumento
src = "def f(x):\n    return x\n"
print("CONTROL comentario:", cambio_significativo("pipeline/x.py", src, src + "# comentario\n"))
print("CONTROL código:", cambio_significativo("pipeline/x.py", src, src + "y = 1\n"))
yv = "thresholds:\n  a: 1\n  enable_modis_codigo_mirova: false\n"
yn = "thresholds:\n  a: 1\n  enable_modis_codigo_mirova: true\n"
print("CONTROL perfil sólo flag MODIS:", cambio_significativo("pipeline/profiles/mirova_equivalent.yaml", yv, yn))
print("CONTROL perfil otra clave:", cambio_significativo("pipeline/profiles/mirova_equivalent.yaml", yv, yv.replace("a: 1", "a: 2")))
