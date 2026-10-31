# -*- coding: utf-8 -*-
"""S170: cuándo una lectura sellada en un tag puede aceptar records corridos en el tag ANTERIOR del runner (§8.8).

POR QUÉ. La adenda a N-01 se selló después de correr t1 a t3: los jobs corrieron en `s170-modd-f4-candado` (d65fd231d)
y la lectura se hace con el evaluador de `s170-modd-f4-candado-n01`. El control de procedencia exige un solo commit y
quedaba en rojo aunque el runner hubiera hecho exactamente lo mismo en los dos. El §7 manda arreglar el instrumento y
repetir la lectura, no la corrida. Nicolás lo autorizó (2026-10-31, vía la coordinadora S170).

LA REGLA (mecánica; no mira ningún resultado del A/B). Se acepta el commit del runner sólo si:
  1. el commit de la lectura desciende del commit del runner (`git merge-base --is-ancestor`);
  2. ningún archivo que el job del runner ejecuta o lee para producir los records cambia entre los dos commits
     (ARCHIVOS_RUNNER: el arnés, la población, el workflow, pipeline/, scripts/, el tablero, data/ de producción, las
     herramientas de re-corrida en su sha, evaluar_d25 y volcanoes.yaml);
  3. de evaluar_f4.py, que el arnés importa, no cambia nada de lo que el arnés alcanza: las definiciones que nombra
     (`E.<nombre>`), las que ésas usan, y toda sentencia de nivel de módulo que se ejecuta al importarlo.
Lo que sólo habilita el job (la batería, el resto del evaluador, el manifiesto) queda fuera: no produce records, y la
lectura lo comprueba aparte contra su propio tag (control `manifiesto`).
"""
from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

ARCHIVOS_RUNNER = (   # una entrada por línea: mutar_procedencia_runner.py quita cada una
    "experiments/_s166_modd_f4/probe_f4.py",
    "experiments/_s166_modd_f4/poblacion_f4.json",
    "experiments/_s166_modd_f4/humo_f4.txt",
    "experiments/_s166_modd_f4/head_e.py",
    ".github/workflows/probe-s168-modd-f4.yml",
    "pipeline/",
    "scripts/",
    "frontend/index.html",
    "data/mirova_equivalent/",
    "experiments/_s162_mxd03/",
    "experiments/_s151_mxd03_etiquetas/",
    "experiments/_s151_mxd03_cumulo_121/",
    "experiments/_s151_mxd03_sola_123/",
    "experiments/_s151_probe_mod03/",
    "experiments/_s157_prereg_d25/evaluar_d25.py",
    "experiments/_s146_ab_sin_test1/evaluar.py",
    "experiments/_s151_prereg_fk_11/evaluar_fk.py",
    "volcanoes.yaml",
)
EVALUAR = "experiments/_s166_modd_f4/evaluar_f4.py"
PROBE = "experiments/_s166_modd_f4/probe_f4.py"
ALIAS_EVALUAR = "E"                     # probe_f4: `import evaluar_f4 as E`


def _git(raiz, *args, ok=(0,)):
    p = subprocess.run(["git", "-c", "core.autocrlf=false", "-C", str(raiz), *args], capture_output=True)
    if p.returncode not in ok:
        raise RuntimeError("git %s: %s" % (" ".join(args), p.stderr.decode("utf-8", "replace")[:300]))
    return p


def _show(raiz, commit, ruta):
    return _git(raiz, "show", "%s:%s" % (commit, ruta)).stdout.decode("utf-8")


def nombres_usados(fuente_probe, alias=ALIAS_EVALUAR):
    """Los `E.<nombre>` que el arnés usa."""
    return {n.attr for n in ast.walk(ast.parse(fuente_probe))
            if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == alias}


def _es_bloque_main(st):
    """`if __name__ == "__main__":` sin else (un else sí corre al importar)."""
    return (isinstance(st, ast.If) and not st.orelse and isinstance(st.test, ast.Compare)
            and isinstance(st.test.left, ast.Name)
            and st.test.left.id == "__name__" and len(st.test.comparators) == 1
            and isinstance(st.test.comparators[0], ast.Constant) and st.test.comparators[0].value == "__main__")


def huella_alcanzable(fuente_evaluar, usados):
    """{clave: ast.dump} de lo que el arnés alcanza en evaluar_f4: las definiciones nombradas, las que éstas usan
    (cierre por nombres de nivel de módulo) y toda sentencia de nivel de módulo que no es def/class (corre al importar)."""
    mod = ast.parse(fuente_evaluar)
    defs, al_importar = {}, {}
    for st in mod.body:   # las sentencias se numeran entre ellas, para que agregar una def no corra la numeración
        if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            defs[st.name] = st
        elif _es_bloque_main(st):   # `if __name__ == "__main__":` no corre al importar
            continue
        else:
            al_importar["sentencia_%03d" % len(al_importar)] = st
    pend, vistos = [n for n in usados if n in defs], set()
    for st in al_importar.values():
        pend += [n.id for n in ast.walk(st) if isinstance(n, ast.Name) and n.id in defs]
    while pend:
        n = pend.pop()
        if n in vistos:
            continue
        vistos.add(n)
        pend += [m.id for m in ast.walk(defs[n]) if isinstance(m, ast.Name) and m.id in defs and m.id not in vistos]
    out = {"def:" + n: ast.dump(defs[n]) for n in sorted(vistos)}
    out.update({k: ast.dump(v) for k, v in al_importar.items()})
    return out


def compatible(raiz, commit_runner, commit_lectura):
    """La regla del módulo. Devuelve {"ok", "desciende", "cambiados", "evaluar_distinto", "usados"}."""
    raiz = Path(raiz)
    desciende = _git(raiz, "merge-base", "--is-ancestor", commit_runner, commit_lectura, ok=(0, 1)).returncode == 0
    cambiados = [x for x in _git(raiz, "diff", "--name-only", commit_runner, commit_lectura, "--",
                                 *ARCHIVOS_RUNNER).stdout.decode("utf-8").splitlines() if x]
    usados = nombres_usados(_show(raiz, commit_runner, PROBE))
    h_r = huella_alcanzable(_show(raiz, commit_runner, EVALUAR), usados)
    h_l = huella_alcanzable(_show(raiz, commit_lectura, EVALUAR), usados)
    distinto = sorted(k for k in set(h_r) | set(h_l) if h_r.get(k) != h_l.get(k))
    return {"ok": desciende and not cambiados and not distinto, "desciende": desciende, "cambiados": cambiados[:30],
            "evaluar_distinto": distinto[:30], "usados": sorted(usados)}


# ------------------------------------------------------------------ guarda: lo que el arnés carga de verdad
_RASTREO = r"""
import sys, os
vistos = set()
def gancho(ev, args):
    if ev == "open" and args and isinstance(args[0], (str, bytes, os.PathLike)):
        vistos.add(os.path.abspath(os.fsdecode(args[0])))
sys.addaudithook(gancho)
sys.path.insert(0, sys.argv[1])
import probe_f4  # noqa
for v in sorted(vistos):
    print(v)
"""


def archivos_cargados_por_probe(raiz):
    """Los archivos del repo que se abren al importar probe_f4.py (gancho de auditoría «open», que también ve los imports
    y las cargas por ruta). Los imports perezosos dentro de funciones caen en pipeline/ y scripts/."""
    raiz = Path(raiz).resolve()
    p = subprocess.run([sys.executable, "-c", _RASTREO, str(raiz / "experiments/_s166_modd_f4")], capture_output=True,
                       text=True, encoding="utf-8", errors="replace", cwd=str(raiz),
                       env=dict(os.environ, F4_RAIZ=str(raiz), PYTHONIOENCODING="utf-8"))
    if p.returncode != 0:
        raise RuntimeError("no se pudo importar probe_f4: %s" % p.stderr[-300:])
    out = set()
    for ln in p.stdout.splitlines():
        if not os.path.isabs(ln):   # avisos que el pipeline imprime al importarse
            continue
        try:
            rel = Path(ln).resolve().relative_to(raiz).as_posix()
        except ValueError:
            continue
        if "/__pycache__/" in "/" + rel:   # el import leyó el .pyc: cuenta su fuente
            d, f = rel.rsplit("/__pycache__/", 1) if "/" in rel.split("__pycache__")[0] else ("", rel.split("/", 1)[1])
            rel = (d + "/" if d else "") + f.split(".")[0] + ".py"
        if not rel.startswith(".git/"):
            out.add(rel)
    return out


def no_cubiertos(cargados):
    """Los cargados que no cubre ARCHIVOS_RUNNER (evaluar_f4.py va aparte, por lo que el arnés alcanza)."""
    return sorted(r for r in cargados if r != EVALUAR and not any(
        r == e or (e.endswith("/") and r.startswith(e)) for e in ARCHIVOS_RUNNER))
