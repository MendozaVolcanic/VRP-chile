# -*- coding: utf-8 -*-
"""V2, X3: ¿el S8 del lector re-sellado de V375-E (tag s172-v375e-lector-resellado, fc3912cb2) marca régimen nuevo
con los PR A, B y #932?

Instrumento: la función cambio_significativo/diff_git del PROPIO lector (copia textual del tag en lecturas/), con
`nombres`/`mostrar` que corren git en el worktree de B (mismo repositorio, refs compartidos). Pregunta 1: si el S8
marcara, diff_git devuelve una lista no vacía. Pregunta 2 (control positivo): un par de commits que cambia código de
pipeline/ de verdad TIENE que salir marcado; si sale vacío el instrumento está muerto.
"""
import importlib.util
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
REPO = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("D:/vrp-trabajo/worktrees/s172-modd-encendido")

spec = importlib.util.spec_from_file_location("lector", AQUI / "lecturas" / "leer_sombra_v375e_resellado.py")
lec = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(lec)
except Exception as e:  # noqa: BLE001  el módulo puede exigir cosas de su checkout al importar
    print("import del lector falló:", type(e).__name__, e)
    raise


def _git(*args):
    p = subprocess.run(["git", *args], cwd=str(REPO), capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env={**__import__("os").environ, "MSYS_NO_PATHCONV": "1"})
    return p.returncode, p.stdout


def nombres(a, b):
    for r in (a, b):
        if _git("rev-parse", "--verify", "--quiet", f"{r}^{{commit}}")[0] != 0:
            return None
    rc, out = _git("diff", "--name-only", a, b, "--", *lec.RUTAS_REGIMEN)
    return None if rc != 0 else [x for x in out.splitlines() if x.strip()]


def mostrar(rev, ruta):
    rc, out = _git("show", f"{rev}:{ruta}")
    return out if rc == 0 else None


PARES = [
    ("base -> PR A", "a3c5a9b49", "0a0dae344"),
    ("PR A -> PR B", "0a0dae344", "c9525f994"),
    ("base -> #932", "a3c5a9b49", "28183712a"),
    ("base -> A+B+#932 (orden ABS, 094b7e9fc)", "a3c5a9b49", "094b7e9fc"),
    ("main de hoy 47cdc446f -> A+B+#932", "47cdc446f", "094b7e9fc"),
    ("CONTROL POSITIVO: pre-s165-mxd03-modis -> base (código de pipeline cambió)", "pre-s165-mxd03-modis", "a3c5a9b49"),
]
print("RUTAS_REGIMEN =", lec.RUTAS_REGIMEN)
print("CLAVES_PERFIL_OTRO_SENSOR =", lec.CLAVES_PERFIL_OTRO_SENSOR)
for nom, a, b in PARES:
    fs = nombres(a, b)
    marcados = lec.diff_git(a, b, nombres=nombres, mostrar=mostrar)
    print(f"\n[{nom}] archivos de RUTAS_REGIMEN que cambian: {None if fs is None else len(fs)}")
    if fs:
        for f in fs[:40]:
            print("   ", f, "-> MARCA" if marcados and f in marcados else "-> no marca")
    print(f"   S8 marca régimen nuevo: {'SI (' + str(len(marcados)) + ')' if marcados else ('SIN DATO' if marcados is None else 'NO')}")
