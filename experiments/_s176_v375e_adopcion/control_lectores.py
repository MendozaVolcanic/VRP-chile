# -*- coding: utf-8 -*-
"""S176 (diseño decisión 6): ¿el PR A marca régimen en los lectores sellados? Con control positivo (A110).

POR QUÉ, COMO GEÓLOGO. Las lecturas selladas de V375-E y V750-A comparan la sombra con la regla escrita antes de mirar. Si un
cambio de código ajeno a la vía contara como otro régimen, la lectura quedaría partida en dos y sin sustrato. El PR A sólo agrega
guardia y vigilancia, así que no debe contar. Pero un cero del instrumento no significa nada si no se le ve dar otra cosa: por
eso cada lector se corre también sobre commits fabricados que SÍ deben marcar.

V375-E: el S8 del lector del tag s172-v375e-lector-resellado (se ejecuta su texto tal cual, con RAIZ apuntando a este clon) sobre
la comparación real main -> cabeza del PR, y sobre commits fabricados con `git commit-tree`, sin tocar ninguna rama.
V750-A (#964): su régimen se lee del record (`regimen.codigo_sha`, `diag_codigo_mirova.roi`), no de un diff: se comprueba que la
cabeza del PR desciende del corte (#939, 58edb9788) y que el PR no toca nada que cambie la ROI o el código de la vía; control
positivo, un commit anterior al corte tiene que dar «anterior» y el mapa de ROI de B4 tiene que distinguir los dos volcanes.

Uso: python -I experiments/_s176_v375e_adopcion/control_lectores.py <base> <cabeza>
"""
import ast
import functools
import importlib.util
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8")
TAG = "s172-v375e-lector-resellado"
LECTOR = "experiments/_s168/v375e_sombra/leer_sombra_v375e.py"
RAMA_964 = "origin/claude/s175-v750a-reconcilia"
LECTOR_964 = "experiments/_s162_v750a/evaluar_v750a.py"
CORTE_939 = "58edb9788"


def git(*a, inp=None, env=None):
    r = subprocess.run(["git", "-C", str(RAIZ)] + list(a), capture_output=True, text=True, encoding="utf-8", errors="replace",
                       input=inp, env=env)
    return r.returncode, r.stdout.strip()


def fabricar(base, ruta, sustituir):
    """Un commit nuevo sobre `base` con `ruta` cambiada por sustituir(texto). No toca ninguna rama ni el árbol de trabajo."""
    rc, txt = git("show", f"{base}:{ruta}")
    assert rc == 0, ruta
    nuevo = sustituir(txt + "\n")
    assert nuevo != txt + "\n", ruta
    rc, blob = git("hash-object", "-w", "--stdin", inp=nuevo)
    assert rc == 0
    with tempfile.TemporaryDirectory() as t:
        env = dict(os.environ, GIT_INDEX_FILE=str(Path(t) / "index"),
                   GIT_AUTHOR_NAME="control", GIT_AUTHOR_EMAIL="c@c", GIT_COMMITTER_NAME="control", GIT_COMMITTER_EMAIL="c@c")
        assert git("read-tree", base, env=env)[0] == 0
        assert git("update-index", "--add", "--cacheinfo", f"100644,{blob},{ruta}", env=env)[0] == 0
        rc, arbol = git("write-tree", env=env)
        assert rc == 0
        rc, sha = git("commit-tree", arbol, "-p", base, "-m", "control fabricado", env=env)
        assert rc == 0
    return sha


def main(base, cabeza):
    base = git("rev-parse", base)[1]
    cabeza = git("rev-parse", cabeza)[1]
    print(f"base {base}\ncabeza {cabeza}")
    rc, nombres = git("diff", "--name-only", base, cabeza)
    print("archivos del PR:\n  " + nombres.replace("\n", "\n  "))

    # ---- V375-E, el lector sellado tal cual
    rc, src = git("show", f"{TAG}:{LECTOR}")
    assert rc == 0
    with tempfile.TemporaryDirectory() as t:
        arch = Path(t) / "leer_sombra_v375e.py"
        arch.write_text(src, encoding="utf-8")
        spec = importlib.util.spec_from_file_location("lector_v375e", arch)
        L = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(L)
    L.RAIZ = RAIZ            # el lector corre git sobre este clon
    print(f"\n== V375-E, S8 del lector del tag {TAG}")
    print("RUTAS_REGIMEN:", L.RUTAS_REGIMEN, "\nPERFILES_REGIMEN:", L.PERFILES_REGIMEN)
    r = L.diff_git(base, cabeza)
    print(f"real: main -> cabeza del PR marca: {r} (tiene que ser [])")
    assert r == [], r
    ME = "pipeline/profiles/mirova_equivalent.yaml"
    SO = "pipeline/profiles/sombra_codigo_mirova.yaml"
    WS = ".github/workflows/sombra-codigo-mirova.yml"
    casos = [
        ("POSITIVO enciende V375 en producción (B1)", ME, lambda s: re.sub(r"(\nthresholds:\n)", r"\1  enable_v375_codigo_mirova: true\n", s, count=1), True),
        ("POSITIVO cambia un umbral de producción", ME, lambda s: re.sub(r"anomaly_threshold_k:\s*[\d.]+", "anomaly_threshold_k: 9.9", s, count=1), True),
        ("POSITIVO apaga V375 en la sombra", SO, lambda s: s.replace("enable_v375_codigo_mirova: true", "enable_v375_codigo_mirova: false"), True),
        ("POSITIVO edita la aserción del workflow de la sombra", WS, lambda s: s.replace("vias V750 V375 MODIS encendidas", "vias distintas"), True),
        ("POSITIVO cambia código de pipeline/", "pipeline/mirova_v750_codigo.py", lambda s: s + "\nX_CONTROL = 1\n", True),
        ("NEGATIVO enciende V750 en producción (B2): no es de este lector", ME, lambda s: re.sub(r"(\nthresholds:\n)", r"\1  enable_v750_codigo_mirova: true\n", s, count=1), False),
        ("NEGATIVO perfil nuevo en pipeline/profiles/", "pipeline/profiles/guardia_k_viirs.yaml", lambda s: s + "# nota\n", False),
    ]
    for nombre, ruta, f, debe in casos:
        padre = cabeza if git("cat-file", "-e", f"{cabeza}:{ruta}")[0] == 0 else base
        sha = fabricar(padre, ruta, f)
        r = L.diff_git(cabeza, sha)
        marca = bool(r)
        print(f"  {nombre}: marca {r} {'OK' if marca == debe else 'MAL'}")
        assert marca == debe, nombre
    print("V375-E: el PR no marca régimen; 5 positivos marcan y 2 negativos no.")

    # ---- V750-A: por los datos
    print(f"\n== V750-A ({RAMA_964}, lector de #964)")
    # La función real del lector, extraída de su texto (lo demás del lector pide artefactos del run: SIN DATO de punta a punta).
    rc, src964 = git("show", f"{RAMA_964}:{LECTOR_964}")
    assert rc == 0
    nodo = next(n for n in ast.parse(src964).body if isinstance(n, ast.FunctionDef) and n.name == "es_ancestro")
    g964 = {"subprocess": subprocess, "RAIZ": RAIZ, "functools": functools}
    exec(compile(ast.Module(body=[nodo], type_ignores=[]), "evaluar_v750a.py", "exec"), g964)
    es_ancestro = g964["es_ancestro"]
    r = es_ancestro(CORTE_939, cabeza)
    print(f"es_ancestro({CORTE_939}, cabeza del PR) del lector: {r} (tiene que ser True: la sombra posterior al PR sigue dentro)")
    assert r is True
    rc, viejo = git("rev-parse", CORTE_939 + "^")
    r = es_ancestro(CORTE_939, viejo)
    print(f"control positivo: es_ancestro con el commit anterior al corte {viejo[:9]}: {r} (tiene que ser False)")
    assert r is False
    r = es_ancestro(CORTE_939, "0" * 40)
    print(f"control positivo: es_ancestro con un sha que este clon no conoce: {r} (tiene que ser None, SIN DATO)")
    assert r is None
    rc, tocados = git("diff", "--name-only", base, cabeza, "--", "pipeline/grillas_mirova.yaml", "pipeline/mirova_v750_codigo.py",
                      "pipeline/process_viirs_mod.py", "pipeline/store.py", "pipeline/profiles/sombra_codigo_mirova.yaml",
                      "volcanoes.yaml", "scripts/run_pipeline.py", "experiments/_s162_v750a")
    print(f"archivos del PR que cambian ROI, código o perfil de la vía de 750 o el lector: [{tocados}] (tiene que ser vacío)")
    assert tocados == ""
    rc, grilla = git("show", f"{cabeza}:pipeline/grillas_mirova.yaml")
    sens = sorted(m.group(1) for m in re.finditer(r"^\s*(\w+):\s*\{[^\n]*roi_v750:\s*sens", grilla, re.M))
    defs = sorted(m.group(1) for m in re.finditer(r"^\s*(\w+):\s*\{[^\n]*roi_v750:\s*def", grilla, re.M))
    print(f"control positivo del mapa de ROI: sens {sens}; def {len(defs)} volcanes (el lector separa por este campo)")
    assert sens == ["PuyehueCordonCaulle", "Tupungatito"] and defs
    rc, s375 = git("grep", "-c", "ENABLE_V375_CODIGO_MIROVA", f"{cabeza}", "--", "pipeline/process_viirs_mod.py", "pipeline/process_modis.py")
    print(f"el flag de V375 en el procesador de V750 y en el de MODIS: rc {rc} [{s375}] (rc 1 y vacío: no lo leen)")
    assert rc == 1 and s375 == ""
    rc, s375b = git("grep", "-c", "ENABLE_V375_CODIGO_MIROVA", f"{cabeza}", "--", "pipeline/process_viirs.py")
    print(f"control positivo: en el procesador de VIIRS 375 sí aparece: [{s375b}]")
    assert rc == 0 and s375b
    print("V750-A: el PR no cambia la ROI, el código ni el perfil de la vía de 750, y su régimen no cuenta el PR.")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
