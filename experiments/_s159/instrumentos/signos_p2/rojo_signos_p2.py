# -*- coding: utf-8 -*-
"""S161, D-45 (ADENDA_SIGNOS_P2.md §5): la salida ROJA de las pruebas nuevas, con las pruebas tal como quedan
commiteadas, contra el evaluador ANTERIOR al cambio (el de c13cf5808, igual al de bcfdc7c76: c13cf5808 sólo agrega la
adenda). Se corre DESPUÉS de la última edición de las pruebas (V29-02: una salida roja de un borrador no vale). La copia
del evaluador va en experiments/_mut_rojo/ (el evaluador calcula RAIZ = AQUI.parents[1]) y se borra. Cada falla se
clasifica por tipo leído del XML de JUnit (S156): por aserción, por otra excepción o error.

Uso: python rojo_signos_p2.py [commit] [sufijo] [pruebas...]
"""
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[3]
COMMIT = sys.argv[1] if len(sys.argv) > 1 else "c13cf5808"
SUFIJO = sys.argv[2] if len(sys.argv) > 2 else ""
PRUEBAS = sys.argv[3:] or ["tests/test_evaluar_d25_signos_p2_s161.py"]
COPIAR = ("evaluar_d25.py", "ADENDA_CALIBRACION.md", "ADENDA_PLACEBO.md", "ADENDA_GEMELO.md")


def clasificar(xml):
    """(n pruebas, [fallas por aserción], [fallas por otra excepción], [errores]), leído del JUnit."""
    aser, otras, errores, n = [], [], [], 0
    for c in ET.parse(xml).getroot().iter("testcase"):
        n += 1
        for f in c.findall("failure"):
            msg = (f.get("message") or "").strip()
            (aser if msg.startswith(("assert ", "AssertionError")) else otras).append(
                (c.get("name"), msg.split(":")[0][:60]))
        for e in c.findall("error"):
            errores.append((c.get("name"), (e.get("message") or "")[:60]))
    return n, aser, otras, errores


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    dst = RAIZ / "experiments" / "_mut_rojo"
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir()
    try:
        for f in COPIAR:
            txt = subprocess.run(["git", "show", "%s:experiments/_s157_prereg_d25/%s" % (COMMIT, f)], cwd=RAIZ,
                                 capture_output=True, check=True).stdout
            (dst / f).write_bytes(txt)
        shutil.copytree(RAIZ / "experiments" / "_s157_prereg_d25" / "_congelado_v1", dst / "_congelado_v1")
        xml = AQUI / ("rojo_signos_p2%s.xml" % SUFIJO)
        env = dict(os.environ, D25_EVALUADOR_DIR=str(dst), PYTHONIOENCODING="utf-8")
        p = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--junitxml", str(xml)]
                           + PRUEBAS, cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
        print(p.stdout[-8000:])
        n, aser, otras, errores = clasificar(xml)
        print("evaluador de %s | pruebas %d | fallan por aserción %d | por otra excepción %d | errores %d | pasan %d" % (
            COMMIT, n, len(aser), len(otras), len(errores), n - len(aser) - len(otras) - len(errores)))
        for t, m in aser:
            print("   ROJA por aserción: %s" % t)
        for t, m in otras + errores:
            print("   OTRA: %s %s" % (t, m))
    finally:
        shutil.rmtree(dst, ignore_errors=True)


if __name__ == "__main__":
    main()
