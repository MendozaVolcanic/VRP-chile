# -*- coding: utf-8 -*-
"""Verificador D-34: mutaciones PROPIAS del evaluador (c44709e27), una o mas por regla nueva, contra la bateria
tests/test_evaluar_d25_p2_s159.py y tests/test_evaluar_d25_placebo_s159.py.

Las dos preguntas del instrumento:
1. Si la bateria no vigilara una regla, lo veria? Si: la mutacion de esa regla sale NO ATRAPADA.
2. Si el corredor estuviera muerto, se veria? Si: el control (copia sin mutar) tiene que dar 0 fallas, y una
   mutacion con texto original ausente aborta en vez de contarse.

Cuenta como ATRAPADA solo la mutacion que falla por ASERCION (AssertionError en el JUnit XML) y sin errores de
coleccion; una falla por otra excepcion es CAE y no cuenta (igual que mutar_comparador.py del implementador).

Las copias viven en raiz_falsa/experiments/mut_NN/ dentro de esta carpeta (el evaluador calcula RAIZ como
AQUI.parents[1], y raiz_falsa tiene junctions a scripts/, frontend/ y los experiments que importa), asi no se escribe
nada fuera de la carpeta del verificador. Las mutaciones solo de P2 corren solo el archivo de pruebas de P2 (las del
placebo no tocan P2 y tardan 3 min); las demas corren los dos archivos.
"""
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[3]
ORIG = RAIZ / "experiments" / "_s157_prereg_d25"
RF = AQUI / "raiz_falsa"
COPIAR = ("evaluar_d25.py", "ADENDA_CALIBRACION.md", "ADENDA_PLACEBO.md", "ADENDA_GEMELO.md")
P2 = (RAIZ / "tests" / "test_evaluar_d25_p2_s159.py",)
AMBAS = P2 + (RAIZ / "tests" / "test_evaluar_d25_placebo_s159.py",)

# (id, nombre, regla que vigila, pruebas, [(original, mutado), ...])
MUTACIONES = [
    ("m01", "BLOQUEA con el lado invertido (neto < 0 bloquea)", "D-34 5.5", P2,
     [('    elif neto > 0:\n        return "BLOQUEA", det', '    elif neto < 0:\n        return "BLOQUEA", det')]),
    ("m02", "SIN SUSTRATO con 4 pasadas en vez de 5", "D-34 5.6", P2,
     [('    if len(c) < N_MIN_PARES or len(set(bl_p2)) < N_MIN_NOCHES:',
       '    if len(c) < N_MIN_PARES - 1 or len(set(bl_p2)) < N_MIN_NOCHES:')]),
    ("m03", "SIN SUSTRATO con 2 noches en vez de 3", "D-34 5.6", P2,
     [('    if len(c) < N_MIN_PARES or len(set(bl_p2)) < N_MIN_NOCHES:',
       '    if len(c) < N_MIN_PARES or len(set(bl_p2)) < N_MIN_NOCHES - 1:')]),
    ("m04", "las noches del sustrato se cuentan como pasadas", "D-34 5.6", P2,
     [('    if len(c) < N_MIN_PARES or len(set(bl_p2)) < N_MIN_NOCHES:',
       '    if len(c) < N_MIN_PARES or len(bl_p2) < N_MIN_NOCHES:')]),
    ("m05", "otra semilla en el bootstrap de P2 (no la de M)", "D-34 5.3", P2,
     [('    W = pesos_bloque(bl_p2)', '    W = pesos_bloque(bl_p2, semilla=SEMILLA + 11)')]),
    ("m06", "1.000 remuestreos en P2 en vez de 10.000", "D-34 5.3", P2,
     [('    W = pesos_bloque(bl_p2)', '    W = pesos_bloque(bl_p2, n_boot=1000)')]),
    ("m07", "GANA con el borde (hi <= 0)", "D-34 5.4", P2,
     [('    if hi < 0:\n        return "GANA", det', '    if hi <= 0:\n        return "GANA", det')]),
    ("m08", "PIERDE con el borde (lo >= 0)", "D-34 5.4", P2,
     [('    if lo > 0:\n        return "PIERDE", det', '    if lo >= 0:\n        return "PIERDE", det')]),
    ("m09", "las pasadas con error en los dos brazos entran al neto (union en vez de diferencia simetrica)", "D-34 5.1", P2,
     [('            for k in sorted(eK ^ eD)]', '            for k in sorted(eK | eD)]')]),
    ("m10", "la lista atribuye el error al brazo equivocado", "D-34 5.7", P2,
     [('"error_de": "D" if x["c"] > 0 else "K"', '"error_de": "K" if x["c"] > 0 else "D"')]),
    ("m11", "BLOQUEA cambia el texto pero no marca la ventana (empeora sigue False)", "D-34 5.5", P2,
     [('                  "ADENDA_GEMELO.md D-34) | M: %s" % (", ".join(bloq), estado))\n        empeora = True',
       '                  "ADENDA_GEMELO.md D-34) | M: %s" % (", ".join(bloq), estado))')]),
    ("m12", "SIN SUSTRATO bloquea como BLOQUEA", "D-34 5.6", P2,
     [('    bloq = [s for s in SENS if ver["P2|%s" % s] == "BLOQUEA"]',
       '    bloq = [s for s in SENS if ver["P2|%s" % s] in ("BLOQUEA", "SIN SUSTRATO")]')]),
    ("m13", "bloque por volcan solo (sin la noche)", "D-34 5.3", P2,
     [('"bloque": "%s|%s" % (k.split("|")[0], k.split("|")[2][:10])}\n            for k in sorted(eK ^ eD)]',
       '"bloque": k.split("|")[0]}\n            for k in sorted(eK ^ eD)]')]),
    ("m14", "regla (b) D-33 con margen 3 en vez de 2", "D-34 5.8", P2,
     [('    if v_a in ("GANA", "PIERDE") and margen <= 2:', '    if v_a in ("GANA", "PIERDE") and margen <= 3:')]),
    ("m15", "intervalo al 90 % en P2 (percentiles 5 y 95)", "D-34 5.3", P2,
     [('    lo, hi = float(np.percentile(sumas, 2.5)), float(np.percentile(sumas, 97.5))',
       '    lo, hi = float(np.percentile(sumas, 5)), float(np.percentile(sumas, 95))')]),
    ("m16", "tope de la calibracion de d' al 10 % en vez de 5 %", "D-32", AMBAS,
     [('    calibrada = f_mej <= MAX_FALSOS_CALIB\n    vols_neg, vols_n, g_vol = 0, 0, {}',
       '    calibrada = f_mej <= 2 * MAX_FALSOS_CALIB\n    vols_neg, vols_n, g_vol = 0, 0, {}')]),
    ("m17", "999 repeticiones en la calibracion de d'", "D-32", AMBAS,
     [('N_CALIB_DPRIMA = 1000                    # sellado (D-32)', 'N_CALIB_DPRIMA = 999')]),
    ("m18", "otra semilla en la calibracion de d' (SEMILLA + 4)", "D-32", AMBAS,
     [('SEMILLA_CALIB_DPRIMA = SEMILLA + 3       # = 160, sellada (D-32)', 'SEMILLA_CALIB_DPRIMA = SEMILLA + 4')]),
    ("m19", "la calibracion de d' exige la cola EMPEORA en vez de la de MEJORA", "D-30.2", AMBAS,
     [('    calibrada = f_mej <= MAX_FALSOS_CALIB\n    vols_neg, vols_n, g_vol = 0, 0, {}',
       '    calibrada = f_emp <= MAX_FALSOS_CALIB\n    vols_neg, vols_n, g_vol = 0, 0, {}')]),
    ("m20", "la marca NO VALE PARA DECIDIR no llega al estado de la ventana (solo al JSON)", "D-30.4", AMBAS,
     [('    if not res["vale_para_decidir"]:\n        res["estado"] += " | " + res["motivo_validez"]',
       '    if False:\n        res["estado"] += " | " + res["motivo_validez"]')]),
    ("m21", "combinar no arrastra la marca de validez", "D-30.4", AMBAS,
     [('    if any(r.get("vale_para_decidir") is False for r in rs):\n        final +=',
       '    if False:\n        final +=')]),
    ("m22", "INDECIDIBLE por d' aunque d no de MEJORA (sobre-alcance de D-30.1)", "D-30.1", AMBAS,
     [('        if r_dec == "MEJORA" and not detalle["calibrada_dprima"]:',
       '        if not detalle["calibrada_dprima"]:')]),
    ("m23", "INDECIDIBLE de d' se decide con la cola EMPEORA ademas (calibrada = ambas colas) y NEUTRO donde va INDECIDIBLE",
     "D-30.1", AMBAS,
     [('            r_dec = "INDECIDIBLE"\n            detalle["nota"] = "%s (falsos MEJORA',
       '            r_dec = "NEUTRO"\n            detalle["nota"] = "%s (falsos MEJORA')]),
]


def una(mid, nombre, pruebas, cambios):
    dst = RF / "experiments" / ("mut_%s" % mid)
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    try:
        for f in COPIAR:
            shutil.copy2(ORIG / f, dst / f)
        src = (dst / "evaluar_d25.py").read_text(encoding="utf-8")
        for a, b in cambios:
            n = src.count(a)
            if n != 1:
                raise SystemExit("mutacion %s '%s': el texto original aparece %d veces (se esperaba 1): %r" % (mid, nombre, n, a[:90]))
            src = src.replace(a, b)
        (dst / "evaluar_d25.py").write_text(src, encoding="utf-8")
        env = dict(os.environ, D25_EVALUADOR_DIR=str(dst), PYTHONIOENCODING="utf-8")
        xml = dst / "resultado.xml"
        p = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--junitxml", str(xml),
                            *[str(x) for x in pruebas]], cwd=str(RAIZ), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=env)
        out = p.stdout + p.stderr
        fallidas, errores = [], []
        if xml.exists():
            for c in ET.parse(xml).getroot().iter("testcase"):
                for f in c.findall("failure"):
                    msg = (f.get("message") or "").strip()
                    tipo = "AssertionError" if msg.startswith(("assert ", "AssertionError")) else msg.split(":")[0]
                    fallidas.append((c.get("name"), tipo))
                for e in c.findall("error"):
                    errores.append(c.get("name"))
        else:
            errores.append("(sin JUnit XML)")
    finally:
        shutil.rmtree(dst, ignore_errors=True)
    por_asercion = [t for t, tipo in fallidas if tipo == "AssertionError"]
    otras = [(t, tipo) for t, tipo in fallidas if tipo != "AssertionError"]
    resumen = (re.findall(r"^\d+ (?:failed|passed).*$", out, flags=re.M) or ["(sin linea de resumen)"])[-1]
    return por_asercion, otras, errores, resumen


def main():
    desde = sys.argv[1] if len(sys.argv) > 1 else None   # reanudar desde un id (el control ya corrio en la primera pasada)
    if desde:
        print("reanudando desde %s (el control m00 y las anteriores ya corrieron, ver la salida previa)" % desde)
        pa, ot, er, res, ok = [], [], [], "(control no repetido)", True
    else:
        pa, ot, er, res = una("00", "control: copia sin mutar", AMBAS, [])
        ok = not (pa or ot or er) and "passed" in res and "failed" not in res
    print("%-4s %-95s %-10s %-22s %s" % ("m00", "control: copia sin mutar (las dos pruebas)", "control", "OK, 0 fallas" if ok else "FALLA EL CONTROL", res), flush=True)
    if not ok:
        print("RESUMEN: el control no da verde; nada se cuenta")
        return 1
    atr, tot, no_atr = 0, 0, []
    for mid, nombre, regla, pruebas, cambios in MUTACIONES:
        if desde and mid < desde:
            continue
        pa, ot, er, res = una(mid, nombre, pruebas, cambios)
        atrapada = bool(pa) and not er
        estado = "ATRAPADA por asercion" if atrapada else "CAE (no cuenta)" if (ot or er) else "NO ATRAPADA"
        tot += 1; atr += atrapada
        if not atrapada:
            no_atr.append((mid, nombre, estado))
        print("%-4s %-95s %-10s %-22s %s" % (mid, nombre, regla, estado, res), flush=True)
        for t in pa:
            print("        asercion: %s" % t)
        for t, tipo in ot:
            print("        otra falla (no cuenta): %s %s" % (t, tipo))
        for t in er:
            print("        error (no cuenta): %s" % t)
    print("\nRESUMEN: %d de %d mutaciones propias atrapadas por asercion" % (atr, tot))
    for x in no_atr:
        print("   NO atrapada: %s %s (%s)" % x)
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
