# -*- coding: utf-8 -*-
"""S159, D-28 §3 (iv): mutaciones del comparador de M en experiments/_s157_prereg_d25/evaluar_d25.py.

POR QUÉ. Las pruebas de tests/test_evaluar_d25_placebo_s159.py tienen que atrapar cada forma de romper lo que selló
D-28, y atraparla por una ASERCIÓN: una mutación que hace caer el módulo o una prueba por KeyError, AttributeError o
similar NO cuenta como atrapada (memoria S152 y S156: control de caída). Las cuatro que pide la adenda: el comparador no
se aplica, ĝ fijo en 1, EMPEORA juzgado sobre d′ en vez de d, la compuerta reaparece. Se agregan dos más del mismo
cambio (el comparador ni se calcula; ĝ no se recalcula en el bootstrap) y se informan aparte.

Cada mutación corre en una copia (experiments/_s159_mut_cmp_<n>/, borrada al terminar) con el evaluador mutado y las
dos adendas, y la prueba lee esa copia por la variable D25_EVALUADOR_DIR. Una mutación cuyo texto original no aparece
exactamente una vez aborta el corredor (no se cuenta como atrapada ni como escapada).

Uso: python mutar_comparador.py            -> imprime una línea por mutación y el RESUMEN
"""
import os
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
ORIG = RAIZ / "experiments" / "_s157_prereg_d25"
COPIAR = ("evaluar_d25.py", "ADENDA_CALIBRACION.md", "ADENDA_PLACEBO.md")
PRUEBA = RAIZ / "tests" / "test_evaluar_d25_placebo_s159.py"

# (nombre, requerida por D-28 §3 iv, [(texto original, texto mutado), ...])
MUTACIONES = [
    ("el comparador se calcula pero no se aplica", True,
     [('        if r_dec == "MEJORA" and not detalle["dprima_da_mejora"]:', '        if False:')]),
    ("ĝ fijo en 1 (log 0), en el punto y en el bootstrap", True,
     [('    g_hat = float(np.median(g))                        # §2.1, estimación puntual',
       '    g_hat = 0.0'),
      ('    g_b = medianas_ponderadas(g, W)', '    g_b = np.zeros(W.shape[0])')]),
    ("EMPEORA juzgado sobre d′ en vez de d", True,
     [('        if r_dec == "MEJORA" and not detalle["dprima_da_mejora"]:',
       '        if r_dec == "EMPEORA":\n            r_dec = detalle["regla_dprima"]\n'
       '        if r_dec == "MEJORA" and not detalle["dprima_da_mejora"]:')]),
    ("la compuerta reaparece (evaluar_m marca INVALIDO y global_ventana lo aplica)", True,
     [('                                                          comparador=False)[0] for g in PLACEBO_GANANCIAS}\n'
       '    return ver, info',
       '                                                          comparador=False)[0] for g in PLACEBO_GANANCIAS}\n'
       '        if "MEJORA" in info["M_placebo"][nom].values():\n'
       '            ver["PLACEBO"] = "INVALIDO: placebo da MEJORA en %s" % nom\n'
       '    return ver, info'),
      ('    if not ok_ctrl:\n        return "INDECIDIBLE", False, False\n    p1 = ',
       '    if str(ver.get("PLACEBO", "")).startswith("INVALIDO"):\n'
       '        return "INVALIDO POR INSTRUMENTO (%s)" % ver["PLACEBO"], False, False\n'
       '    if not ok_ctrl:\n        return "INDECIDIBLE", False, False\n    p1 = ')]),
    ("el comparador ni se calcula", False,
     [('    if comparador and modo_calib == "simetrica" and modo != "informa":',
       '    if False and comparador and modo_calib == "simetrica" and modo != "informa":')]),
    ("ĝ no se recalcula en cada réplica (fijo en el punto dentro del bootstrap)", False,
     [('    g_b = medianas_ponderadas(g, W)', '    g_b = np.full(W.shape[0], g_hat)')]),
]


def una(i, nombre, cambios):
    dst = RAIZ / "experiments" / ("_s159_mut_cmp_%02d" % i)
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir()
    try:
        for f in COPIAR:
            shutil.copy2(ORIG / f, dst / f)
        src = (dst / "evaluar_d25.py").read_text(encoding="utf-8")
        for a, b in cambios:
            n = src.count(a)
            if n != 1:
                raise SystemExit("mutación '%s': el texto original aparece %d veces (se esperaba 1): %r" % (nombre, n, a[:90]))
            src = src.replace(a, b)
        (dst / "evaluar_d25.py").write_text(src, encoding="utf-8")
        env = dict(os.environ, D25_EVALUADOR_DIR=str(dst), PYTHONIOENCODING="utf-8")
        # El tipo de cada falla se lee del JUnit XML. La primera versión parseaba la línea FAILED del resumen corto de
        # pytest, que sin ancho de terminal sale sin el tipo de excepción, y daba NO ATRAPADA a fallas reales.
        xml = dst / "resultado.xml"
        p = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--junitxml", str(xml),
                            str(PRUEBA)], cwd=str(RAIZ), capture_output=True, text=True, encoding="utf-8",
                           errors="replace", env=env)
        out = p.stdout + p.stderr
        fallidas, errores = [], []
        if xml.exists():
            for c in ET.parse(xml).getroot().iter("testcase"):
                for f in c.findall("failure"):
                    # Un `assert x` sin mensaje sale como «assert ...» (reescritura de pytest) y uno con mensaje como
                    # «AssertionError: ...»; las dos son aserción. Cualquier otra excepción sale con su tipo delante.
                    msg = (f.get("message") or "").strip()
                    tipo = "AssertionError" if msg.startswith(("assert ", "AssertionError")) else msg.split(":")[0]
                    fallidas.append((c.get("name"), tipo))
                for e in c.findall("error"):
                    errores.append(c.get("name"))
        else:
            errores.append("(sin JUnit XML: pytest no llegó a correr el módulo)")
    finally:
        shutil.rmtree(dst, ignore_errors=True)
    por_asercion = [t for t, tipo in fallidas if tipo == "AssertionError"]
    otras = [(t, tipo) for t, tipo in fallidas if tipo != "AssertionError"]
    resumen = (re.findall(r"^\d+ (?:failed|passed).*$", out, flags=re.M) or ["(sin línea de resumen)"])[-1]
    return por_asercion, otras, errores, resumen, out


def main():
    # Control del corredor (A110: el nulo se mide): la copia SIN mutar tiene que dar 0 fallas. Si no, el corredor no sirve.
    por_asercion, otras, errores, resumen, _ = una(0, "control: copia sin mutar", [])
    ctrl_ok = not (por_asercion or otras or errores) and "passed" in resumen and "failed" not in resumen
    print("%-80s %-8s %-22s %s" % ("control: copia sin mutar", "control", "OK, 0 fallas" if ctrl_ok else
                                   "FALLA EL CONTROL", resumen), flush=True)
    if not ctrl_ok:
        print("\nRESUMEN: el control sin mutar no da verde; las mutaciones no se cuentan")
        return 1
    filas, n_req, atr_req, n_ext, atr_ext = [], 0, 0, 0, 0
    for i, (nombre, req, cambios) in enumerate(MUTACIONES, 1):
        por_asercion, otras, errores, resumen, out = una(i, nombre, cambios)
        atrapada = bool(por_asercion) and not errores
        estado = ("ATRAPADA por aserción" if atrapada else
                  "CAE (no cuenta)" if (otras or errores) else "NO ATRAPADA")
        if req:
            n_req += 1; atr_req += atrapada
        else:
            n_ext += 1; atr_ext += atrapada
        print("%-80s %-8s %-22s %s" % (nombre, "requerida" if req else "extra", estado, resumen), flush=True)
        for t in por_asercion:
            print("      aserción: %s" % t)
        for t, tipo in otras:
            print("      otra falla (no cuenta): %s %s" % (t, tipo))
        for t in errores:
            print("      error (no cuenta): %s" % t)
    print("\nRESUMEN: %d de %d requeridas (D-28 §3 iv) atrapadas por aserción; extras %d de %d" % (
        atr_req, n_req, atr_ext, n_ext))
    return 0 if atr_req == n_req and atr_ext == n_ext else 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
