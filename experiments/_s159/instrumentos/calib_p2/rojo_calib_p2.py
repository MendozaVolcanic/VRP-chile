# -*- coding: utf-8 -*-
"""S160, D-42: la salida ROJA de las pruebas nuevas, con las pruebas tal como quedan commiteadas, contra el evaluador
ANTERIOR al cambio (el de 5f986a209, igual al de ca65069f6). Se corre DESPUÉS de la última edición de las pruebas
(V29-02: una salida roja de un borrador no vale). La copia va en experiments/_mut_rojo/ (RAIZ = AQUI.parents[1]) y se
borra. Clasifica cada falla por tipo leído del XML de JUnit.
Uso: python rojo_calib_p2.py [commit]"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[3]
sys.path.insert(0, str(AQUI))
from mutar_calib_p2 import clasificar  # noqa: E402

COMMIT = sys.argv[1] if len(sys.argv) > 1 else "5f986a209"
PRUEBAS = ["tests/test_evaluar_d25_calib_p2_s160.py", "tests/test_evaluar_d25_punta_a_punta_s160.py"]


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    dst = RAIZ / "experiments" / "_mut_rojo"
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir()
    try:
        for f in ("evaluar_d25.py", "ADENDA_CALIBRACION.md", "ADENDA_PLACEBO.md", "ADENDA_GEMELO.md"):
            txt = subprocess.run(["git", "show", "%s:experiments/_s157_prereg_d25/%s" % (COMMIT, f)], cwd=RAIZ,
                                 capture_output=True, check=True).stdout
            (dst / f).write_bytes(txt)
        shutil.copytree(RAIZ / "experiments" / "_s157_prereg_d25" / "_congelado_v1", dst / "_congelado_v1")
        xml = AQUI / "rojo_calib_p2.xml"
        env = dict(os.environ, D25_EVALUADOR_DIR=str(dst), PYTHONIOENCODING="utf-8")
        p = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--junitxml", str(xml)] + PRUEBAS,
                           cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
        print(p.stdout[-6000:])
        n, aser, otras, errores = clasificar(xml)
        print("evaluador de %s | pruebas %d | fallan por aserción %d | por otra excepción %d | errores %d" % (
            COMMIT, n, len(aser), len(otras), len(errores)))
        for t, m in aser:
            print("   ROJA por aserción: %s" % t)
        for t, m in otras + errores:
            print("   OTRA: %s %s" % (t, m))
    finally:
        shutil.rmtree(dst, ignore_errors=True)


if __name__ == "__main__":
    main()
