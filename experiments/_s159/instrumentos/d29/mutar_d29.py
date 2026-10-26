# -*- coding: utf-8 -*-
"""S160 nocturna: mutaciones de D-29 sobre una copia de evaluar_d25.py en experiments/_mut_d29_<m>/ (RAIZ =
AQUI.parents[1] tiene que seguir siendo la raíz del repo). Cuenta como ATRAPADA sólo si alguna prueba de
tests/test_evaluar_d25_dias_d29_s160.py falla por AssertionError y ninguna por otra excepción (S156)."""
import os, re, shutil, subprocess, sys
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[4]
SRC = (RAIZ / "experiments/_s157_prereg_d25/evaluar_d25.py").read_text(encoding="utf-8")
MUT = {
    "m1_filtro_no_filtra": ("    dias = set(dias)\n    if not dias:\n        return claves\n",
                            "    dias = set(dias)\n    if True:\n        return claves\n"),
    "m2_cobertura_sin_filtrar": ("    cob = {vs: filtrar_dias(ks, excl) for vs, ks in\n",
                                 "    cob = {vs: ks for vs, ks in\n"),
    "m3_veredicto_sin_declarar": ('    if excl:   # D-29', '    if False:   # D-29'),
    "m4_dias_sin_el_13": ('DIAS_EXCLUIDOS = {"V1": ("2026-10-13", ', 'DIAS_EXCLUIDOS = {"V1": ('),
}
res = {}
for m, (a, b) in MUT.items():
    assert SRC.count(a) == 1, (m, SRC.count(a))
    d = RAIZ / "experiments" / ("_mut_d29_" + m)
    d.mkdir(exist_ok=True)
    (d / "evaluar_d25.py").write_text(SRC.replace(a, b), encoding="utf-8")
    env = dict(os.environ, D25_EVALUADOR_DIR=str(d), PYTHONIOENCODING="utf-8")
    xml = d / "junit.xml"
    p = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--junitxml", str(xml),
                        "tests/test_evaluar_d25_dias_d29_s160.py"], cwd=RAIZ, env=env, capture_output=True, text=True)
    # Tipo de cada falla desde el XML de JUnit (la primera version leia la linea de resumen de -q, que no trae el
    # tipo, y daba NO ATRAPADA en las 4: control del instrumento en d29/README.md).
    import xml.etree.ElementTree as ET
    casos = ET.parse(xml).getroot().iter("testcase")
    fallas, errores = [], []
    for c in casos:
        for f in c.findall("failure"):
            fallas.append((f.get("message") or "").split(":")[0])
        errores += [e for e in c.findall("error")]
    assert sum(1 for _ in ET.parse(xml).getroot().iter("testcase")) == 5, "no corrieron las 5 pruebas"
    aser = [f for f in fallas if f == "AssertionError"]
    otras = [f for f in fallas if f != "AssertionError"]
    res[m] = "ATRAPADA" if aser and not otras and not errores else ("NO ATRAPADA" if not fallas and not errores else "CAIDA")
    print("%-28s %s | fallas %s | errores %d" % (m, res[m], fallas, len(errores)))
    shutil.rmtree(d)
print("RESUMEN: %d de %d atrapadas por asercion" % (sum(v == "ATRAPADA" for v in res.values()), len(res)))
