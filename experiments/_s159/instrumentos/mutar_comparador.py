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

S159, D-34 (ADENDA_GEMELO.md): el corredor corre también tests/test_evaluar_d25_p2_s159.py y agrega las cuatro
mutaciones de la regla nueva de P2 (bootstrap por pasada en vez de por bloque, sin la variante BLOQUEA, signo invertido,
lista vacía), contadas aparte.

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
COPIAR = ("evaluar_d25.py", "ADENDA_CALIBRACION.md", "ADENDA_PLACEBO.md", "ADENDA_GEMELO.md")
PRUEBAS = (RAIZ / "tests" / "test_evaluar_d25_placebo_s159.py", RAIZ / "tests" / "test_evaluar_d25_p2_s159.py")

# (nombre, requerida por D-28 §3 iv, [(texto original, texto mutado), ...])
MUTACIONES = [
    ("el comparador se calcula pero no se aplica", True,
     [('        elif r_dec == "MEJORA" and not detalle["dprima_da_mejora"]:', '        elif False:')]),
    ("ĝ fijo en 1 (log 0), en el punto y en el bootstrap", True,
     [('    g_hat = float(np.median(g))                        # §2.1, estimación puntual',
       '    g_hat = 0.0'),
      ('    g_b = medianas_ponderadas(g, W)', '    g_b = np.zeros(W.shape[0])')]),
    ("EMPEORA juzgado sobre d′ en vez de d", True,
     [('        if r_dec == "MEJORA" and not detalle["calibrada_dprima"]:',
       '        if r_dec == "EMPEORA":\n            r_dec = detalle["regla_dprima"]\n'
       '        if r_dec == "MEJORA" and not detalle["calibrada_dprima"]:')]),
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
    # S159, segunda vuelta (D-30 y H3 del verificador con contexto limpio, verificador_comparador/INFORME.md): las tres
    # mutaciones que ninguna prueba atrapaba, y tres de los cambios de D-30. Se cuentan aparte en el resumen.
    ("H3: opción A sobre d′ retirada (d′ basta con un volcán)", "d30",
     [('"dprima_da_mejora": bool(r_p == "MEJORA" and calibrada and vols_neg >= MIN_VOLCANES_MEJORA)}',
       '"dprima_da_mejora": bool(r_p == "MEJORA" and calibrada)}')]),
    ("H3: calibración de d′ ignorada (calibrada siempre True)", "d30",
     [('    calibrada = f_mej <= MAX_FALSOS_CALIB\n    vols_neg, vols_n, g_vol = 0, 0, {}',
       '    calibrada = True\n    vols_neg, vols_n, g_vol = 0, 0, {}')]),
    ("H3: opción A de d′ contada con d en vez de d′", "d30",
     [('            vols_n += 1; vols_neg += float(np.median(dp[sel])) < 0',
       '            vols_n += 1; vols_neg += float(np.median((np.abs(lD) - np.abs(lK))[sel])) < 0')]),
    ("D-30.1: calibración de d′ fallida vuelve a NEUTRO", "d30",
     [('        if r_dec == "MEJORA" and not detalle["calibrada_dprima"]:', '        if False:')]),
    ("D-30.2: calibración de d′ exige también la cola EMPEORA", "d30",
     [('    calibrada = f_mej <= MAX_FALSOS_CALIB\n    vols_neg, vols_n, g_vol = 0, 0, {}',
       '    calibrada = f_mej <= MAX_FALSOS_CALIB and f_emp <= MAX_FALSOS_CALIB\n    vols_neg, vols_n, g_vol = 0, 0, {}')]),
    ("D-30.4: la calibración sellada vale para decidir", "d30",
     [('    if calibracion == "simetrica":\n        return {"vale_para_decidir": True',
       '    if True:\n        return {"vale_para_decidir": True')]),
    ("D-32: la calibración de d′ vuelve a 200 repeticiones", "d30",
     [('N_CALIB_DPRIMA = 1000                    # sellado (D-32)', 'N_CALIB_DPRIMA = 200')]),
    # D-34 (ADENDA_GEMELO.md §5): la regla nueva de P2
    ("D-34: bootstrap de P2 por pasada en vez de por bloque", "d34",
     [('    W = pesos_bloque(bl_p2)', '    W = pesos_pasada(len(bl_p2))')]),
    ("D-34: sin la variante (un neto en contra que no llega a PIERDE no bloquea)", "d34",
     [('    elif neto > 0:\n        return "BLOQUEA", det', '    elif False:\n        return "BLOQUEA", det')]),
    ("D-34: signo invertido (errores de K menos errores de D)", "d34",
     [('"c": 1 if k in eD else -1', '"c": -1 if k in eD else 1')]),
    ("D-34: lista de discordantes vacía", "d34",
     [('    return out\n\n\ndef regla_b_d33', '    return []\n\n\ndef regla_b_d33')]),
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
                            *[str(x) for x in PRUEBAS]], cwd=str(RAIZ), capture_output=True, text=True, encoding="utf-8",
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
    n_req = atr_req = n_ext = atr_ext = n_d30 = atr_d30 = n_d34 = atr_d34 = 0
    for i, (nombre, req, cambios) in enumerate(MUTACIONES, 1):
        por_asercion, otras, errores, resumen, out = una(i, nombre, cambios)
        atrapada = bool(por_asercion) and not errores
        estado = ("ATRAPADA por aserción" if atrapada else
                  "CAE (no cuenta)" if (otras or errores) else "NO ATRAPADA")
        if req == "d30":
            n_d30 += 1; atr_d30 += atrapada
        elif req == "d34":
            n_d34 += 1; atr_d34 += atrapada
        elif req:
            n_req += 1; atr_req += atrapada
        else:
            n_ext += 1; atr_ext += atrapada
        print("%-80s %-8s %-22s %s" % (nombre, "D-30" if req == "d30" else "D-34" if req == "d34" else "requerida" if req else "extra", estado,
                                       resumen), flush=True)
        for t in por_asercion:
            print("      aserción: %s" % t)
        for t, tipo in otras:
            print("      otra falla (no cuenta): %s %s" % (t, tipo))
        for t in errores:
            print("      error (no cuenta): %s" % t)
    print("\nRESUMEN: %d de %d requeridas (D-28 §3 iv) atrapadas por aserción; extras %d de %d; segunda vuelta (D-30, D-32 y "
          "H3 del verificador) %d de %d; P2 de D-34 %d de %d" % (atr_req, n_req, atr_ext, n_ext, atr_d30, n_d30,
                                                                atr_d34, n_d34))
    return 0 if (atr_req, atr_ext, atr_d30, atr_d34) == (n_req, n_ext, n_d30, n_d34) else 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
