# -*- coding: utf-8 -*-
"""S160, D-42 §3: corredor de mutaciones del evaluador de D25 para los candados de la cuarta adenda.

Cubre las siete mutaciones de V34-03, las cinco de V29-01, las de la calibración nueva de P2 (§3, tercer punto) y dos
del estrato informativo 203 (NOTA_ESTRATO_203.md: que se cuente y que no decida).

Las dos preguntas del instrumento:
1. Si la batería no vigilara una regla, ¿lo vería? Sí: la mutación de esa regla sale NO ATRAPADA.
2. Si el corredor estuviera muerto, ¿se vería? Sí: primero corre una copia SIN MUTAR (control) con las mismas pruebas,
   y tiene que dar 0 fallas y 0 errores; y una mutación cuyo texto original no aparece exactamente una vez aborta.

ATRAPADA = alguna prueba falla por AssertionError y NINGUNA falla por otra excepción ni da error (S156, V34-04). El tipo
se lee del XML de JUnit (--junitxml), no del resumen de pytest -q. Las copias van en experiments/_mut_<id>/ (el
evaluador calcula RAIZ = AQUI.parents[1]); se borran al terminar cada una. Sin enlaces de carpetas.

Uso: python mutar_calib_p2.py [--solo id1,id2] [--out salida.json]
"""
import argparse
import json
import os
import re
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
CON_PLACEBO = BASE + [T / "test_evaluar_d25_placebo_s159.py"]

LOCAL = ('    from datetime import datetime, timedelta\n'
         '    def _f(k):\n'
         '        t = k.split("|")[2][:16].replace("T", " ")\n'
         '        return (datetime.strptime(t, "%Y-%m-%d %H:%M") - timedelta(hours=3)).strftime("%Y-%m-%d")\n'
         '    if isinstance(claves, dict):\n'
         '        return {k: v for k, v in claves.items() if _f(k) not in dias}\n'
         '    return {k for k in claves if _f(k) not in dias}\n')
FILTRO_UTC = ('    if isinstance(claves, dict):\n'
              '        return {k: v for k, v in claves.items() if k.split("|")[2][:10] not in dias}\n'
              '    return {k for k in claves if k.split("|")[2][:10] not in dias}\n')

# (id, grupo, qué rompe, pruebas, [(original, mutado)])
MUT = [
    # ---- V34-03
    ("v05", "V34-03", "otra semilla en el intervalo de P2", BASE,
     [("    W = pesos_bloque(bl_p2)\n", "    W = pesos_bloque(bl_p2, semilla=SEMILLA + 11)\n")]),
    ("v06", "V34-03", "1.000 remuestreos en el intervalo de P2", BASE,
     [("    W = pesos_bloque(bl_p2)\n", "    W = pesos_bloque(bl_p2, n_boot=1000)\n")]),
    ("v15", "V34-03", "intervalo al 90 % en P2 (percentiles 5 y 95)", BASE,
     [("    lo, hi = float(np.percentile(sumas, 2.5)), float(np.percentile(sumas, 97.5))\n    if hi < 0:\n        return \"GANA\", lo, hi",
       "    lo, hi = float(np.percentile(sumas, 5)), float(np.percentile(sumas, 95))\n    if hi < 0:\n        return \"GANA\", lo, hi")]),
    ("v08", "V34-03", "PIERDE con el borde (lo >= 0)", BASE,
     [('    if lo > 0:\n        return "PIERDE", lo, hi', '    if lo >= 0:\n        return "PIERDE", lo, hi')]),
    ("v16", "V34-03", "tope de la calibración de d' al 10 %", CON_PLACEBO,
     [("    calibrada = f_mej <= MAX_FALSOS_CALIB\n    vols_neg, vols_n, g_vol = 0, 0, {}",
       "    calibrada = f_mej <= 2 * MAX_FALSOS_CALIB\n    vols_neg, vols_n, g_vol = 0, 0, {}")]),
    ("v22", "V34-03", "INDECIDIBLE por d' aunque d no dé MEJORA", CON_PLACEBO,
     [('        if r_dec == "MEJORA" and not detalle["calibrada_dprima"]:', '        if not detalle["calibrada_dprima"]:')]),
    ("v20", "V34-03", "la marca NO VALE PARA DECIDIR no llega al estado", CON_PLACEBO,
     [('    if not res["vale_para_decidir"]:\n        res["estado"] += " | " + res["motivo_validez"]',
       '    if False:\n        res["estado"] += " | " + res["motivo_validez"]')]),
    # ---- V29-01
    ("p2", "V29-01", "filtro de los crudos descartado", BASE,
     [("        R[n] = filtrar_dias(R[n], excl)\n", "        filtrar_dias(R[n], excl)\n")]),
    ("p3", "V29-01", "días excluidos vuelven a la tabla", BASE,
     [("filtrar_dias(t, excl).items()", "filtrar_dias(t, ()).items()")]),
    ("p4", "V29-01", "días excluidos vuelven a la cobertura", BASE,
     [("cob = {vs: filtrar_dias(ks, excl) for vs, ks in", "cob = {vs: filtrar_dias(ks, ()) for vs, ks in")]),
    ("p6", "V29-01", "fecha en hora de Chile (UTC-3)", BASE, [(FILTRO_UTC, LOCAL)]),
    ("p7", "V29-01", "cabecera de V1 callada", BASE,
     [('    if excl:\n        print("== EVALUADO SIN', '    if False:\n        print("== EVALUADO SIN')]),
    # ---- calibración nueva (D-42 §3, tercer punto)
    ("c1", "D-42", "semilla de la calibración (constante 162)", BASE,
     [("SEMILLA_CALIB_P2 = SEMILLA + 4 ", "SEMILLA_CALIB_P2 = SEMILLA + 5 ")]),
    ("c1b", "D-42", "semilla de la calibración en la llamada (159)", BASE,
     [("calibrar_p2(c, bl_p2, W)\n", "calibrar_p2(c, bl_p2, W, semilla=SEMILLA + 2)\n")]),
    ("c2", "D-42", "999 sorteos (constante)", BASE, [("N_CALIB_P2 = 1000 ", "N_CALIB_P2 = 999 ")]),
    ("c2b", "D-42", "200 sorteos en la llamada", BASE,
     [("calibrar_p2(c, bl_p2, W)\n", "calibrar_p2(c, bl_p2, W, n_rep=200)\n")]),
    ("c3", "D-42", "tope al 10 % por cola", BASE,
     [("calibrada = f_gana <= MAX_FALSOS_CALIB and f_pierde <= MAX_FALSOS_CALIB",
       "calibrada = f_gana <= 2 * MAX_FALSOS_CALIB and f_pierde <= 2 * MAX_FALSOS_CALIB")]),
    ("c3b", "D-42", "tope estricto (< en vez de <=)", BASE,
     [("calibrada = f_gana <= MAX_FALSOS_CALIB and f_pierde <= MAX_FALSOS_CALIB",
       "calibrada = f_gana < MAX_FALSOS_CALIB and f_pierde < MAX_FALSOS_CALIB")]),
    ("c4", "D-42", "una cola sola (GANA)", BASE,
     [("calibrada = f_gana <= MAX_FALSOS_CALIB and f_pierde <= MAX_FALSOS_CALIB", "calibrada = f_gana <= MAX_FALSOS_CALIB")]),
    ("c4b", "D-42", "una cola sola (PIERDE)", BASE,
     [("calibrada = f_gana <= MAX_FALSOS_CALIB and f_pierde <= MAX_FALSOS_CALIB", "calibrada = f_pierde <= MAX_FALSOS_CALIB")]),
    ("c4c", "D-42", "las dos colas sumadas contra un solo tope", BASE,
     [("calibrada = f_gana <= MAX_FALSOS_CALIB and f_pierde <= MAX_FALSOS_CALIB",
       "calibrada = f_gana + f_pierde <= 2 * MAX_FALSOS_CALIB")]),
    ("c5", "D-42", "sorteo por pasada en vez de por bloque", BASE,
     [("    S = np.array([rng.choice((-1.0, 1.0), size=len(uniq))[idx] for _ in range(n_rep)])",
       "    S = np.array([rng.choice((-1.0, 1.0), size=len(bl)) for _ in range(n_rep)])")]),
    ("c6", "D-42", "un fallo de la calibración no deja INDECIDIBLE", BASE,
     [('        return "INDECIDIBLE", det\n    return v, det', '        return v, det\n    return v, det')]),
    ("c6b", "D-42", "un fallo deja INDECIDIBLE sólo un GANA (un PIERDE sin calibrar cuenta)", BASE,
     [("    if not calibrada:\n        det[\"nota_calibracion\"]", "    if not calibrada and v == \"GANA\":\n        det[\"nota_calibracion\"]")]),
    ("c7", "D-42", "la calibración corre también sin sustrato (SIN SUSTRATO no informa None)", BASE,
     [('        det["resultado_sin_calibrar"] = "SIN SUSTRATO"\n', '        det.update(resultado_sin_calibrar="SIN SUSTRATO", calibrada=True, falsos_gana=0.0)\n')]),
    # ---- estrato 203 (informa, no decide)
    ("e1", "203", "el estrato decide: P2 de VIIRS 750 queda INDECIDIBLE si hay pasadas 203", BASE,
     [('    info["estrato_203"] = estrato_203(TKD, prot, R, lect, cfg, excluir)\n',
       '    info["estrato_203"] = estrato_203(TKD, prot, R, lect, cfg, excluir)\n'
       '    if info["estrato_203"]["n"]:\n        ver["P2|VIIRS750"] = "INDECIDIBLE"\n')]),
    ("e2", "203", "recupera y enciende cambiados", BASE,
     [('            tot["recupera_D"] += 1', '            tot["enciende_D"] += 1'),
      ('            tot["enciende_D"] += 1\n        else:', '            tot["recupera_D"] += 1\n        else:')]),
    ("e3", "203", "el estrato no exige cumbre", BASE,
     [('rk.get("dc") != "summit" or ', '')]),
]


def clasificar(xml):
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


def una(mid, pruebas, cambios):
    dst = RAIZ / "experiments" / ("_mut_%s" % mid)
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
                raise SystemExit("mutación %s: el texto original aparece %d veces (se esperaba 1): %r" % (mid, k, a[:90]))
            src = src.replace(a, b)
        (dst / "evaluar_d25.py").write_text(src, encoding="utf-8")
        xml = dst / "junit.xml"
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
    ap.add_argument("--out", default=str(AQUI / "mutaciones_salida.json"))
    a = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sel = [m for m in MUT if not a.solo or m[0] in a.solo.split(",")]
    res = {}
    ctrl = una("control", CON_PLACEBO, [])
    ok = ctrl["n"] > 0 and not (ctrl["aser"] or ctrl["otras"] or ctrl["errores"])
    print("%-5s %-8s %-75s %s (%d pruebas, %ds)" % ("ctrl", "control", "copia sin mutar, las cinco baterías",
                                                   "OK, 0 fallas" if ok else "FALLA EL CONTROL", ctrl["n"], ctrl["seg"]), flush=True)
    res["control"] = dict(ctrl, ok=ok)
    if not ok:
        print("RESUMEN: el control no da verde; nada se cuenta", ctrl)
        Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        return 1
    atr, por_grupo = 0, {}
    for mid, grupo, nombre, pruebas, cambios in sel:
        r = una(mid, pruebas, cambios)
        atrapada = bool(r["aser"]) and not r["otras"] and not r["errores"]
        estado = "ATRAPADA" if atrapada else ("CAE (no cuenta)" if (r["otras"] or r["errores"]) else "NO ATRAPADA")
        atr += atrapada
        g = por_grupo.setdefault(grupo, [0, 0]); g[0] += atrapada; g[1] += 1
        res[mid] = dict(r, grupo=grupo, nombre=nombre, estado=estado)
        print("%-5s %-8s %-75s %s (%d pruebas, %d por aserción, %d otra excepción, %d errores, %ds)" % (
            mid, grupo, nombre, estado, r["n"], len(r["aser"]), len(r["otras"]), len(r["errores"]), r["seg"]), flush=True)
        for t, m in r["aser"][:4]:
            print("        aserción: %s" % t)
        for t, m in r["otras"] + r["errores"]:
            print("        NO CUENTA: %s %s" % (t, m))
    print("\nRESUMEN: %d de %d mutaciones atrapadas por aserción | por grupo %s" % (
        atr, len(sel), {k: "%d de %d" % tuple(v) for k, v in por_grupo.items()}))
    quedan = sorted(p.name for p in (RAIZ / "experiments").glob("_mut_*"))
    print("copias que quedan en experiments/_mut_*: %s" % (quedan or "ninguna"))
    Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
