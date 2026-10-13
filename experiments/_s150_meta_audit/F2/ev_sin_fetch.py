# -*- coding: utf-8 -*-
"""F2 (meta-auditoria S150). Corre experiments/_s149_prereg_invierno/evaluar_ventana.py SIN `git fetch`
(las refs origin/s146-ab/<run> ya existen en el clon; no tocar el repo compartido). Mismos argumentos."""
import io, subprocess, sys, tarfile
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / "experiments" / "_s149_prereg_invierno"))
import evaluar_ventana as ev

def extraer(runs, tmp):
    base = tmp / "runs"
    for r in runs:
        ruta = "experiments/_s146_ab_sin_test1/salidas/%s" % r
        tar = subprocess.run(["git", "archive", "origin/s146-ab/%s" % r, ruta], cwd=RAIZ, capture_output=True, check=True).stdout
        tarfile.open(fileobj=io.BytesIO(tar)).extractall(base)
    return base / "experiments" / "_s146_ab_sin_test1" / "salidas"
ev.extraer = extraer
if __name__ == "__main__":
    sys.exit(ev.main())
