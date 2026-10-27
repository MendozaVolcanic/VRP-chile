# -*- coding: utf-8 -*-
"""Verificador D-42: mutaciones PROPIAS de la calibracion de P2 y del estrato 203, corridas contra las pruebas del repo
tal como estan commiteadas en b57ecfe62. Misma mecanica que mutar_calib_p2.py del implementador (copia del evaluador en
experiments/_mutv42_<id>/, RAIZ = AQUI.parents[1]; D25_EVALUADOR_DIR; JUnit XML; ATRAPADA = alguna prueba falla por
AssertionError y ninguna por otra excepcion ni error), pero con mutaciones que el implementador no corrio.

Pregunta 1: si la bateria no vigilara una regla, ¿se ve? Si: la mutacion sale NO ATRAPADA.
Pregunta 2: si el corredor estuviera muerto, ¿se ve? Si: el control (copia sin mutar) tiene que dar 0 fallas y
m04 (todos los sorteos con el mismo signo) es un control positivo que seguro cambia las fracciones.
Una mutacion cuyo texto original no aparece exactamente una vez aborta (no se cuenta una copia sin cambio).

Uso: python v03_mutaciones_propias.py [--solo id1,id2] [--out salida.json]
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[3]
ORIG = RAIZ / "experiments" / "_s157_prereg_d25"
COPIAR = ["evaluar_d25.py", "ADENDA_CALIBRACION.md", "ADENDA_PLACEBO.md", "ADENDA_GEMELO.md", "ADENDA_CALIBRACION_P2.md",
          "NOTA_ESTRATO_203.md", "PREREGISTRO.md"]
T = RAIZ / "tests"
BASE = [T / "test_evaluar_d25_calib_p2_s160.py", T / "test_evaluar_d25_p2_s159.py",
        T / "test_evaluar_d25_dias_d29_s160.py", T / "test_evaluar_d25_punta_a_punta_s160.py"]

LLAMADA = "    f_gana, f_pierde, f_bloquea = calibrar_p2(c, bl_p2, W)\n"
CALIBRADA = "    calibrada = f_gana <= MAX_FALSOS_CALIB and f_pierde <= MAX_FALSOS_CALIB\n"
SORTEO = "    S = np.array([rng.choice((-1.0, 1.0), size=len(uniq))[idx] for _ in range(n_rep)])"
SIN_SUSTRATO = ('    if len(c) < N_MIN_PARES or len(set(bl_p2)) < N_MIN_NOCHES:\n'
                '        det["resultado_sin_calibrar"] = "SIN SUSTRATO"\n'
                '        det["nota_calibracion"] = "no se calibra: sin sustrato (D-34 §5.6)"\n'
                '        return "SIN SUSTRATO", det\n'
                '    W = pesos_bloque(bl_p2)\n')
ANTES = ('    if len(c) < N_MIN_PARES or len(set(bl_p2)) < N_MIN_NOCHES:\n'
         '        det["resultado_sin_calibrar"] = "SIN SUSTRATO"\n'
         '        det["nota_calibracion"] = "no se calibra: sin sustrato (D-34 §5.6)"\n'
         '        if len(c):\n'
         '            W0 = pesos_bloque(bl_p2)\n'
         '            f_gana, f_pierde, f_bloquea = calibrar_p2(c, bl_p2, W0)\n'
         '            det.update(calibrada=bool(f_gana <= MAX_FALSOS_CALIB and f_pierde <= MAX_FALSOS_CALIB),\n'
         '                       falsos_gana=f_gana, falsos_pierde=f_pierde, falsos_bloquea=f_bloquea)\n'
         '            if not det["calibrada"]:\n'
         '                return "INDECIDIBLE", det\n'
         '        return "SIN SUSTRATO", det\n'
         '    W = pesos_bloque(bl_p2)\n')
GLOBAL = ('    if "PIERDE" in p2:                 # verificador H2: un M INDECIDIBLE no esconde una suma perdida\n'
          '        return "NO CUMPLE (suma de errores)", False, False\n'
          '    if "INDECIDIBLE" in p1 + p2 + list(m.values()):\n'
          '        return "INDECIDIBLE", False, False\n')
GLOBAL_MUT = ('    if "INDECIDIBLE" in p1 + p2 + list(m.values()):\n'
              '        return "INDECIDIBLE", False, False\n'
              '    if "PIERDE" in p2:\n'
              '        return "NO CUMPLE (suma de errores)", False, False\n')

MUT = [
    ("m01", "semilla de la calibracion compartida con el intervalo (157)",
     [(LLAMADA, "    f_gana, f_pierde, f_bloquea = calibrar_p2(c, bl_p2, W, semilla=SEMILLA)\n")]),
    ("m02", "la calibracion corre ANTES del SIN SUSTRATO y un fallo lo vuelve INDECIDIBLE", [(SIN_SUSTRATO, ANTES)]),
    ("m03", "fracciones sobre los sorteos que deciden (sin EMPATE) en vez de sobre los 1.000",
     [('    return cuenta["GANA"] / n_rep, cuenta["PIERDE"] / n_rep, cuenta["BLOQUEA"] / n_rep\n',
       '    n_dec = max(1, n_rep - cuenta["EMPATE"])\n    return cuenta["GANA"] / n_dec, cuenta["PIERDE"] / n_dec, cuenta["BLOQUEA"] / n_dec\n')]),
    ("m04", "CONTROL POSITIVO: todos los sorteos con el mismo signo (un solo sorteo repetido)",
     [(SORTEO, "    s0 = rng.choice((-1.0, 1.0), size=len(uniq))[idx]\n    S = np.array([s0 for _ in range(n_rep)])")]),
    ("m05", "el tope se aplica tambien a BLOQUEA",
     [(CALIBRADA, "    calibrada = f_gana <= MAX_FALSOS_CALIB and f_pierde <= MAX_FALSOS_CALIB and f_bloquea <= MAX_FALSOS_CALIB\n")]),
    ("m06", "el neto de cada sorteo se reemplaza por el observado (BLOQUEA/EMPATE del sorteo mal clasificados)",
     [("            cuenta[regla_p2(sumas[:, j], int(round(C[j].sum())))[0]] += 1\n",
       "            cuenta[regla_p2(sumas[:, j], int(round(c.sum())))[0]] += 1\n")]),
    ("m07", "el veredicto CALIBRADO no llega a `ver`: contar publica el resultado sin calibrar",
     [('        ver["P2|%s" % s] = v_\n', '        ver["P2|%s" % s] = det["resultado_sin_calibrar"]\n')]),
    ("m08", "global_ventana: INDECIDIBLE de P2 antes que PIERDE (la otra lectura de §2.5)", [(GLOBAL, GLOBAL_MUT)]),
    ("m09", "or en vez de and: basta una cola bajo el tope",
     [(CALIBRADA, "    calibrada = f_gana <= MAX_FALSOS_CALIB or f_pierde <= MAX_FALSOS_CALIB\n")]),
    ("m10", "1001 sorteos (constante)", [("N_CALIB_P2 = 1000 ", "N_CALIB_P2 = 1001 ")]),
    ("m11", "la calibracion usa OTRA matriz de pesos (semilla 166) y no la W del intervalo observado",
     [("        sumas = Wf @ C.T\n", "        sumas = np.asarray(pesos_bloque(bl, semilla=SEMILLA + 9), dtype=np.float64) @ C.T\n")]),
    ("m12", "bloques en orden de aparicion en vez de ordenados (equivalente en produccion: las claves vienen ordenadas)",
     [("    uniq = sorted(set(bl)); idx = np.array([uniq.index(b) for b in bl])\n    S = ",
       "    uniq = list(dict.fromkeys(bl)); idx = np.array([uniq.index(b) for b in bl])\n    S = ")]),
    ("m13", "el estrato 203 deja entrar VIIRS 375", [('if k.split("|")[1] != s or len(v) != 2', 'if len(v) != 2')]),
    ("m14", "el estrato 203 cuenta tambien los cumulos con pc.vrp_mw > 0 (no exige 0,0 MW)",
     [('rk.get("pc_vrp") not in (0, None):', 'False:')]),
    ("m15", "calibrada se decide con la cola observada sola (GANA mira solo falsos_gana, PIERDE solo falsos_pierde)",
     [(CALIBRADA, '    calibrada = (f_gana <= MAX_FALSOS_CALIB) if v == "GANA" else (f_pierde <= MAX_FALSOS_CALIB) if v == "PIERDE" else True\n')]),
]


def clasificar(xml):
    aser, otras, errores, n = [], [], [], 0
    for c in ET.parse(xml).getroot().iter("testcase"):
        n += 1
        for f in c.findall("failure"):
            msg = (f.get("message") or "").strip()
            (aser if msg.startswith(("assert ", "AssertionError")) else otras).append((c.get("name"), msg.split(":")[0][:60]))
        for e in c.findall("error"):
            errores.append((c.get("name"), (e.get("message") or "")[:60]))
    return n, aser, otras, errores


def una(mid, pruebas, cambios):
    dst = RAIZ / "experiments" / ("_mutv42_%s" % mid)
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir()
    t0 = time.time()
    try:
        for f in COPIAR:
            shutil.copy2(ORIG / f, dst / f)
        shutil.copytree(ORIG / "_congelado_v1", dst / "_congelado_v1")
        src = (dst / "evaluar_d25.py").read_text(encoding="utf-8")
        for a, b in cambios:
            k = src.count(a)
            if k != 1:
                raise SystemExit("mutacion %s: el texto original aparece %d veces (se esperaba 1): %r" % (mid, k, a[:90]))
            src = src.replace(a, b)
        (dst / "evaluar_d25.py").write_text(src, encoding="utf-8")
        xml = AQUI / ("junit_%s.xml" % mid)
        env = dict(os.environ, D25_EVALUADOR_DIR=str(dst), PYTHONIOENCODING="utf-8")
        p = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--junitxml", str(xml)]
                           + [str(x) for x in pruebas], cwd=str(RAIZ), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=env)
        if not xml.exists():
            return {"n": 0, "aser": [], "otras": [], "errores": [("(sin JUnit XML)", p.stdout[-300:])], "seg": time.time() - t0}
        n, aser, otras, errores = clasificar(xml)
    finally:
        shutil.rmtree(dst, ignore_errors=True)
    return {"n": n, "aser": aser, "otras": otras, "errores": errores, "seg": round(time.time() - t0)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo")
    ap.add_argument("--out", default=str(AQUI / "v03_mutaciones_propias.json"))
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sel = [m for m in MUT if not a.solo or m[0] in a.solo.split(",")]
    res = {}
    ctrl = una("control", BASE, [])
    ok = ctrl["n"] > 0 and not (ctrl["aser"] or ctrl["otras"] or ctrl["errores"])
    print("%-5s %-95s %s (%d pruebas, %ds)" % ("ctrl", "copia sin mutar, las cuatro baterias BASE",
                                             "OK, 0 fallas" if ok else "FALLA EL CONTROL", ctrl["n"], ctrl["seg"]), flush=True)
    res["control"] = dict(ctrl, ok=ok)
    if not ok:
        print("RESUMEN: el control no da verde; nada se cuenta", ctrl)
        Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        return 1
    atr = 0
    for mid, nombre, cambios in sel:
        r = una(mid, BASE, cambios)
        atrapada = bool(r["aser"]) and not r["otras"] and not r["errores"]
        estado = "ATRAPADA" if atrapada else ("CAE (no cuenta)" if (r["otras"] or r["errores"]) else "NO ATRAPADA")
        atr += atrapada
        res[mid] = dict(r, nombre=nombre, estado=estado)
        print("%-5s %-95s %s (%d pruebas, %d por asercion, %d otra excepcion, %d errores, %ds)" % (
            mid, nombre, estado, r["n"], len(r["aser"]), len(r["otras"]), len(r["errores"]), r["seg"]), flush=True)
        for t, m in r["aser"][:6]:
            print("        asercion: %s" % t)
        for t, m in r["otras"] + r["errores"]:
            print("        NO CUENTA: %s %s" % (t, m))
    print("\nRESUMEN: %d de %d mutaciones propias atrapadas por asercion" % (atr, len(sel)))
    quedan = sorted(p.name for p in (RAIZ / "experiments").glob("_mutv42_*"))
    print("copias que quedan en experiments/_mutv42_*: %s" % (quedan or "ninguna"))
    Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
