# -*- coding: utf-8 -*-
"""Verificador D-42, afirmacion 5: re-corre la salida ROJA de las 37 pruebas nuevas (commiteadas en b57ecfe62) contra
el evaluador de 5f986a209, igual que rojo_calib_p2.py del implementador, pero con el JUnit XML escrito en esta carpeta
(no se toca calib_p2/). Clasifica por tipo de falla y lista tambien las 13 que PASAN sobre el arbol viejo (no miden
el cambio, A116). Copia en experiments/_mutv42b_rojo/ (RAIZ = AQUI.parents[1]) y se borra.
Uso: python v06_rojo_rerun.py [commit]"""
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[4]
COMMIT = sys.argv[1] if len(sys.argv) > 1 else "5f986a209"
SUFIJO = sys.argv[2] if len(sys.argv) > 2 else ""
KEXPR = sys.argv[sys.argv.index("-k") + 1] if "-k" in sys.argv else None
PRUEBAS = ["tests/test_evaluar_d25_calib_p2_s160.py", "tests/test_evaluar_d25_punta_a_punta_s160.py"]


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    dst = RAIZ / "experiments" / "_mutv42b_rojo"
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir()
    try:
        for f in ("evaluar_d25.py", "ADENDA_CALIBRACION.md", "ADENDA_PLACEBO.md", "ADENDA_GEMELO.md"):
            txt = subprocess.run(["git", "show", "%s:experiments/_s157_prereg_d25/%s" % (COMMIT, f)], cwd=RAIZ,
                                 capture_output=True, check=True).stdout
            (dst / f).write_bytes(txt)
        shutil.copytree(RAIZ / "experiments" / "_s157_prereg_d25" / "_congelado_v1", dst / "_congelado_v1")
        xml = AQUI / ("v16_rojo_rerun%s.xml" % SUFIJO)
        env = dict(os.environ, D25_EVALUADOR_DIR=str(dst), PYTHONIOENCODING="utf-8")
        p = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--junitxml", str(xml)] + PRUEBAS + (["-k", KEXPR] if KEXPR else []),
                           cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
        print(p.stdout[-1500:])
        n = aser = otras = err = 0
        pasan = []
        for c in ET.parse(xml).getroot().iter("testcase"):
            n += 1
            fs, es = c.findall("failure"), c.findall("error")
            if es:
                err += 1
            elif fs:
                msg = (fs[0].get("message") or "").strip()
                if msg.startswith(("assert ", "AssertionError")):
                    aser += 1
                else:
                    otras += 1
                    print("   OTRA: %s %s" % (c.get("name"), msg[:80]))
            elif not c.findall("skipped"):
                pasan.append("%s::%s" % (c.get("classname", "").split(".")[-1], c.get("name")))
        print("evaluador de %s | pruebas %d | fallan por asercion %d | por otra excepcion %d | errores %d | pasan %d" % (
            COMMIT, n, aser, otras, err, len(pasan)))
        for t in pasan:
            print("   PASA sobre el arbol viejo (no mide el cambio D-42): %s" % t)
    finally:
        shutil.rmtree(dst, ignore_errors=True)


if __name__ == "__main__":
    main()
