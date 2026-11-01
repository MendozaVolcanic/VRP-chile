# -*- coding: utf-8 -*-
"""S161, D-45 §5 (ADENDA_SIGNOS_P2.md): corredor de mutaciones del evaluador de D25 para los candados de la quinta
adenda. Copia de experiments/_s159/instrumentos/calib_p2/mutar_calib_p2.py (D-42), extendida:

  * las 12 mutaciones de §5 (con sus variantes: la 4 en B <= 3 y B <= 5, la 7 en 12 y en «menor estricto», la 8 en la
    constante y en la llamada, la 3 en el exacto y en los sorteos, la 12 en D-34 y en D-42);
  * las baterías que ya existían (V34-03, V29-01, D-42 y el estrato 203), re-apuntadas al código nuevo donde el texto
    cambió (c6, c6b, c7: la decisión de D-42 ahora es el campo `resultado_d42`; m07 y m07b: contar publica D-34 o D-42
    en vez de D-45);
  * la mutación equivalente «5 % o menos» contra «menos del 5 %» se corre APARTE y se declara: no entra al total.

Las dos preguntas del instrumento:
1. Si la batería no vigilara una regla, ¿lo vería? Sí: la mutación de esa regla sale NO ATRAPADA.
2. Si el corredor estuviera muerto, ¿se vería? Sí: primero corre una copia SIN MUTAR (control) con las mismas pruebas y
   tiene que dar 0 fallas y 0 errores; y una mutación cuyo texto original no aparece exactamente una vez aborta.

ATRAPADA = alguna prueba falla por AssertionError y NINGUNA falla por otra excepción ni da error (S156, V34-04). El tipo
se lee del XML de JUnit, no del resumen de pytest. Las copias van en experiments/_mut_<id>/ (el evaluador calcula
RAIZ = AQUI.parents[1]) y se borran al terminar cada una. Cada pytest usa su propio --basetemp, para poder correr
varias mutaciones en paralelo sin que una limpie el directorio temporal de otra. Sin enlaces de carpetas.

S161, después del reinicio del computador del 2026-10-23 13:21 UTC (se perdieron los resultados, que sólo se
escribían al final): cada mutación terminada se agrega en el acto a --parcial (JSONL, una línea por mutación) y una
corrida nueva salta las que ya están ahí. El control sin mutar se vuelve a correr en cada corrida del script y queda
también en el JSONL (una línea por corrida), así cada tramo tiene su propio control verde.

Uso: python mutar_signos_p2.py [--solo id1,id2] [--out salida.json] [--parcial parcial.jsonl] [--paralelo N]
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[3]
ORIG = RAIZ / "experiments" / "_s157_prereg_d25"
COPIAR = ["evaluar_d25.py", "ADENDA_CALIBRACION.md", "ADENDA_PLACEBO.md", "ADENDA_GEMELO.md", "ADENDA_CALIBRACION_P2.md",
          "ADENDA_SIGNOS_P2.md", "NOTA_ESTRATO_203.md", "NOTA_D44.md", "PREREGISTRO.md"]
T = RAIZ / "tests"
TODAS = [T / "test_evaluar_d25_signos_p2_s161.py", T / "test_evaluar_d25_calib_p2_s160.py",
         T / "test_evaluar_d25_p2_s159.py", T / "test_evaluar_d25_dias_d29_s160.py",
         T / "test_evaluar_d25_punta_a_punta_s160.py", T / "test_evaluar_d25_placebo_s159.py"]

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
CALIB_OK = "calibrada = f_gana <= MAX_FALSOS_CALIB and f_pierde <= MAX_FALSOS_CALIB"
REG_GANA = '    if neto < 0 and TOPE_P2_DEN * pr["gana"][0] <= pr["gana"][1]:\n'
REG_PIERDE = '    if neto > 0 and TOPE_P2_DEN * pr["pierde"][0] <= pr["pierde"][1]:\n'

# (id, grupo, qué rompe, [(original, mutado)])
MUT = [
    # ---- D-45 §5, las 12
    ("s01", "D-45", "1. dos colas en vez de una (el valor-p duplicado)",
     [(REG_GANA, REG_GANA.replace("TOPE_P2_DEN * pr", "TOPE_P2_DEN * 2 * pr")),
      (REG_PIERDE, REG_PIERDE.replace("TOPE_P2_DEN * pr", "TOPE_P2_DEN * 2 * pr"))]),
    ("s02", "D-45", "2. tope al 10 % en vez del 5 %", [("TOPE_P2_DEN = 20 ", "TOPE_P2_DEN = 10 ")]),
    ("s03", "D-45", "3. cola de GANA con «mayor o igual» (exacto)",
     [("k_gana = sum(k for v, k in dist.items() if v <= neto)", "k_gana = sum(k for v, k in dist.items() if v >= neto)")]),
    ("s03b", "D-45", "3. cola de GANA con «mayor o igual» (sorteos)",
     [("m_gana, m_pierde = int((tot <= neto).sum()),", "m_gana, m_pierde = int((tot >= neto).sum()),")]),
    ("s04a", "D-45", "4. SIN SUSTRATO con B de 3 o menos", [("MAX_B_SIN_SUSTRATO_P2 = 4 ", "MAX_B_SIN_SUSTRATO_P2 = 3 ")]),
    ("s04b", "D-45", "4. SIN SUSTRATO con B de 5 o menos", [("MAX_B_SIN_SUSTRATO_P2 = 4 ", "MAX_B_SIN_SUSTRATO_P2 = 5 ")]),
    ("s04c", "D-45", "4. SIN SUSTRATO con B < 4 en la regla",
     [("    if B <= MAX_B_SIN_SUSTRATO_P2:\n", "    if B < MAX_B_SIN_SUSTRATO_P2:\n")]),
    ("s05", "D-45", "5. B contado sin los bloques de suma 0",
     [("    B = len(sumas)                                          # incluidos",
       "    B = sum(1 for x in sumas if x != 0)                       # incluidos")]),
    ("s05b", "D-45", "5. los bloques de suma 0 fuera de las sumas",
     [("    sumas = [por_bloque[b] for b in sorted(por_bloque)]    #",
       "    sumas = [por_bloque[b] for b in sorted(por_bloque) if por_bloque[b]]    #")]),
    ("s06", "D-45", "6. signo sorteado por pasada en vez de por bloque",
     [("    sumas = [por_bloque[b] for b in sorted(por_bloque)]    #", "    sumas = [int(x[\"c\"]) for x in contrib]    #")]),
    ("s07a", "D-45", "7. corte del exacto en 12", [("MAX_B_EXACTO_P2 = 20 ", "MAX_B_EXACTO_P2 = 12 ")]),
    ("s07b", "D-45", "7. corte del exacto en 21", [("MAX_B_EXACTO_P2 = 20 ", "MAX_B_EXACTO_P2 = 21 ")]),
    ("s07c", "D-45", "7. exacto con B < 20 (menor estricto)",
     [("    if B <= MAX_B_EXACTO_P2:\n", "    if B < MAX_B_EXACTO_P2:\n")]),
    ("s08a", "D-45", "8. semilla de los sorteos 163 (constante)", [("SEMILLA_P2_SIGNOS = SEMILLA + 5 ", "SEMILLA_P2_SIGNOS = SEMILLA + 6 ")]),
    ("s08b", "D-45", "8. 9.999 sorteos (constante)", [("N_SORTEOS_P2_SIGNOS = 10000 ", "N_SORTEOS_P2_SIGNOS = 9999 ")]),
    ("s08c", "D-45", "8. semilla 157 en la llamada",
     [("    pr = prueba_signos_p2(sumas, neto)\n", "    pr = prueba_signos_p2(sumas, neto, semilla=SEMILLA)\n")]),
    ("s08d", "D-45", "8. 1.000 sorteos en la llamada",
     [("    pr = prueba_signos_p2(sumas, neto)\n", "    pr = prueba_signos_p2(sumas, neto, n_sorteos=1000)\n")]),
    ("s09", "D-45", "9. valor-p por sorteos sin el +1",
     [("    den = int(n_sorteos) + 1\n", "    den = int(n_sorteos)\n"),
      ('"gana": [1 + m_gana, den], "pierde": [1 + m_pierde, den], "dos_colas": [1 + m_dos, den]',
       '"gana": [m_gana, den], "pierde": [m_pierde, den], "dos_colas": [m_dos, den]')]),
    ("s10", "D-45", "10. BLOQUEA con neto 0",
     [('    if neto > 0:\n        return "BLOQUEA"', '    if neto >= 0:\n        return "BLOQUEA"')]),
    ("s11", "D-45", "11. la calibración de D-42 todavía decide (un fallo deja INDECIDIBLE)",
     [("    return regla_signos_p2(neto, B, pr), det\n",
       "    v45 = regla_signos_p2(neto, B, pr)\n    return (\"INDECIDIBLE\" if det[\"calibrada\"] is False else v45), det\n")]),
    # s12a (primera versión, ic95 y resultado de D-34 en None a la vez) quedó en mutaciones_parcial.jsonl como CAE: dos
    # pruebas de tests/test_evaluar_d25_p2_s159.py indexan det["ic95"] sin preguntar antes (TypeError). Se parte en dos:
    ("s12a1", "D-45", "12. el resultado de D-34 deja de informarse",
     [("    det.update(ic95=[lo, hi], resultado_sin_calibrar=v, calibrada",
       "    det.update(ic95=[lo, hi], resultado_sin_calibrar=None, calibrada")]),
    ("s12a2", "D-45", "12. el intervalo de D-34 deja de informarse (se espera CAE: ver README)",
     [("    det.update(ic95=[lo, hi], resultado_sin_calibrar=v, calibrada",
       "    det.update(ic95=None, resultado_sin_calibrar=v, calibrada")]),
    ("s12b", "D-45", "12. el resultado de D-42 deja de informarse",
     [('               resultado_d42=v if calibrada else "INDECIDIBLE")', "               resultado_d42=None)")]),
    ("s12c", "D-45", "12. los falsos de D-42 dejan de informarse",
     [("calibrada=bool(calibrada), falsos_gana=f_gana,\n               falsos_pierde=f_pierde, falsos_bloquea=f_bloquea,",
       "calibrada=None, falsos_gana=None,\n               falsos_pierde=None, falsos_bloquea=None,")]),
    # ---- §4: lo que se informa (agregadas, no exigidas por §5)
    ("i01", "D-45 §4", "las sumas de bloque sin los ceros en el detalle",
     [('"sumas_bloque": sorted(sumas),', '"sumas_bloque": sorted(x for x in sumas if x),')]),
    # i02 (primera versión, [1, den // 2]) se rompía sola con B = 0 (ZeroDivisionError en el evaluador mutado): no medía
    # nada. Queda en mutaciones_parcial.jsonl como historia; la reemplaza i02b.
    ("i02b", "D-45 §4", "el p mínimo con 2^(B+1)",
     [('"minimo": [1, den], "semilla": None', '"minimo": [1, 2 * den], "semilla": None')]),
    # ---- V34-03 (el intervalo de D-34 que ahora informa, y el comparador de M)
    ("v05", "V34-03", "otra semilla en el intervalo de P2",
     [("    W = pesos_bloque(bl_p2)\n", "    W = pesos_bloque(bl_p2, semilla=SEMILLA + 11)\n")]),
    ("v06", "V34-03", "1.000 remuestreos en el intervalo de P2",
     [("    W = pesos_bloque(bl_p2)\n", "    W = pesos_bloque(bl_p2, n_boot=1000)\n")]),
    ("v15", "V34-03", "intervalo al 90 % en P2 (percentiles 5 y 95)",
     [("    lo, hi = float(np.percentile(sumas, 2.5)), float(np.percentile(sumas, 97.5))\n    if hi < 0:\n        return \"GANA\", lo, hi",
       "    lo, hi = float(np.percentile(sumas, 5)), float(np.percentile(sumas, 95))\n    if hi < 0:\n        return \"GANA\", lo, hi")]),
    ("v08", "V34-03", "PIERDE con el borde (lo >= 0)",
     [('    if lo > 0:\n        return "PIERDE", lo, hi', '    if lo >= 0:\n        return "PIERDE", lo, hi')]),
    ("v16", "V34-03", "tope de la calibración de d' al 10 %",
     [("    calibrada = f_mej <= MAX_FALSOS_CALIB\n    vols_neg, vols_n, g_vol = 0, 0, {}",
       "    calibrada = f_mej <= 2 * MAX_FALSOS_CALIB\n    vols_neg, vols_n, g_vol = 0, 0, {}")]),
    ("v22", "V34-03", "INDECIDIBLE por d' aunque d no dé MEJORA",
     [('        if r_dec == "MEJORA" and not detalle["calibrada_dprima"]:', '        if not detalle["calibrada_dprima"]:')]),
    ("v20", "V34-03", "la marca NO VALE PARA DECIDIR no llega al estado",
     [('    if not res["vale_para_decidir"]:\n        res["estado"] += " | " + res["motivo_validez"]',
       '    if False:\n        res["estado"] += " | " + res["motivo_validez"]')]),
    # ---- V29-01
    ("p2", "V29-01", "filtro de los crudos descartado",
     [("        R[n] = filtrar_dias(R[n], excl)\n", "        filtrar_dias(R[n], excl)\n")]),
    ("p3", "V29-01", "días excluidos vuelven a la tabla", [("filtrar_dias(t, excl).items()", "filtrar_dias(t, ()).items()")]),
    ("p4", "V29-01", "días excluidos vuelven a la cobertura",
     [("cob = {vs: filtrar_dias(ks, excl) for vs, ks in", "cob = {vs: filtrar_dias(ks, ()) for vs, ks in")]),
    ("p6", "V29-01", "fecha en hora de Chile (UTC-3)", [(FILTRO_UTC, LOCAL)]),
    ("p7", "V29-01", "cabecera de V1 callada",
     [('    if excl:\n        print("== EVALUADO SIN', '    if False:\n        print("== EVALUADO SIN')]),
    # ---- D-42 (ahora informa: se vigila en los campos que informan)
    ("c1", "D-42", "semilla de la calibración (constante 162)",
     [("SEMILLA_CALIB_P2 = SEMILLA + 4 ", "SEMILLA_CALIB_P2 = SEMILLA + 5 ")]),
    ("c1b", "D-42", "semilla de la calibración en la llamada (159)",
     [("calibrar_p2(c, bl_p2, W)\n", "calibrar_p2(c, bl_p2, W, semilla=SEMILLA + 2)\n")]),
    ("c2", "D-42", "999 sorteos (constante)", [("N_CALIB_P2 = 1000 ", "N_CALIB_P2 = 999 ")]),
    ("c2b", "D-42", "200 sorteos en la llamada", [("calibrar_p2(c, bl_p2, W)\n", "calibrar_p2(c, bl_p2, W, n_rep=200)\n")]),
    ("c3", "D-42", "tope al 10 % por cola",
     [(CALIB_OK, "calibrada = f_gana <= 2 * MAX_FALSOS_CALIB and f_pierde <= 2 * MAX_FALSOS_CALIB")]),
    ("c3b", "D-42", "tope estricto (< en vez de <=)",
     [(CALIB_OK, "calibrada = f_gana < MAX_FALSOS_CALIB and f_pierde < MAX_FALSOS_CALIB")]),
    ("c4", "D-42", "una cola sola (GANA)", [(CALIB_OK, "calibrada = f_gana <= MAX_FALSOS_CALIB")]),
    ("c4b", "D-42", "una cola sola (PIERDE)", [(CALIB_OK, "calibrada = f_pierde <= MAX_FALSOS_CALIB")]),
    ("c4c", "D-42", "las dos colas sumadas contra un solo tope",
     [(CALIB_OK, "calibrada = f_gana + f_pierde <= 2 * MAX_FALSOS_CALIB")]),
    ("c5", "D-42", "sorteo por pasada en vez de por bloque",
     [("    S = np.array([rng.choice((-1.0, 1.0), size=len(uniq))[idx] for _ in range(n_rep)])",
       "    S = np.array([rng.choice((-1.0, 1.0), size=len(bl)) for _ in range(n_rep)])")]),
    ("c6", "D-42", "un fallo de la calibración no deja INDECIDIBLE (en resultado_d42)",
     [('               resultado_d42=v if calibrada else "INDECIDIBLE")', "               resultado_d42=v)")]),
    ("c6b", "D-42", "un fallo deja INDECIDIBLE sólo un GANA (en resultado_d42)",
     [('               resultado_d42=v if calibrada else "INDECIDIBLE")',
       '               resultado_d42=v if (calibrada or v != "GANA") else "INDECIDIBLE")')]),
    ("c7", "D-42", "la calibración corre también sin sustrato (SIN SUSTRATO no informa None)",
     [('        det.update(resultado_sin_calibrar="SIN SUSTRATO", resultado_d42="SIN SUSTRATO",\n',
       '        det.update(resultado_sin_calibrar="SIN SUSTRATO", resultado_d42="SIN SUSTRATO", calibrada=True, falsos_gana=0.0,\n')]),
    ("m07", "V42-02", "contar publica el resultado de D-34 sin calibrar",
     [('        ver["P2|%s" % s] = v_\n', '        ver["P2|%s" % s] = det["resultado_sin_calibrar"]\n')]),
    ("m07b", "V42-02", "contar publica el resultado de D-42",
     [('        ver["P2|%s" % s] = v_\n', '        ver["P2|%s" % s] = det["resultado_d42"]\n')]),
    ("n04", "V42-04", "el detalle de D-42 declara sorteos y semilla desde las constantes",
     [("n_sorteos=n_usados, semilla_calibracion=semilla_usada,", "n_sorteos=N_CALIB_P2, semilla_calibracion=SEMILLA_CALIB_P2,")]),
    ("n05", "V42-04", "el detalle de D-45 declara sorteos y semilla desde las constantes",
     [('"minimo": [1, den], "semilla": int(semilla), "n_sorteos": int(n_sorteos)}',
       '"minimo": [1, den], "semilla": SEMILLA_P2_SIGNOS, "n_sorteos": N_SORTEOS_P2_SIGNOS}')]),
    # ---- estrato 203 (informa, no decide)
    ("e1", "203", "el estrato decide: P2 de VIIRS 750 queda INDECIDIBLE si hay pasadas 203",
     [('    info["estrato_203"] = estrato_203(TKD, prot, R, lect, cfg, excluir)\n',
       '    info["estrato_203"] = estrato_203(TKD, prot, R, lect, cfg, excluir)\n'
       '    if info["estrato_203"]["n"]:\n        ver["P2|VIIRS750"] = "INDECIDIBLE"\n')]),
    ("e2", "203", "recupera y enciende cambiados",
     [('            tot["recupera_D"] += 1', '            tot["enciende_D"] += 1'),
      ('            tot["enciende_D"] += 1\n        else:', '            tot["recupera_D"] += 1\n        else:')]),
    ("e3", "203", "el estrato no exige cumbre", [('rk.get("dc") != "summit" or ', '')]),
]
# Equivalente declarada (§5): con el método exacto el valor-p es k / 2^B y nunca vale 1/20 justo; con sorteos es
# (1 + m) / 10.001 y tampoco. Se corre para mostrar que ninguna prueba la distingue; NO entra al total.
EQUIVALENTE = ("q01", "equivalente", "«menos del 5 %» en vez de «5 % o menos» (declarada equivalente, §5)",
               [(REG_GANA, REG_GANA.replace("<= pr", "< pr")), (REG_PIERDE, REG_PIERDE.replace("<= pr", "< pr"))])


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


def una(mid, cambios, pruebas=TODAS):
    dst = RAIZ / "experiments" / ("_mut_%s" % mid)
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir()
    bt = Path(tempfile.gettempdir()) / ("bt_mut_%s" % mid)
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
        env = dict(os.environ, D25_EVALUADOR_DIR=str(dst), PYTHONIOENCODING="utf-8", OPENBLAS_NUM_THREADS="2",
                   OMP_NUM_THREADS="2", MKL_NUM_THREADS="2")
        p = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--basetemp", str(bt),
                            "--junitxml", str(xml)] + [str(x) for x in pruebas], cwd=str(RAIZ), capture_output=True,
                           text=True, encoding="utf-8", errors="replace", env=env)
        if not xml.exists():
            return {"n": 0, "aser": [], "otras": [], "errores": [("(sin JUnit XML)", p.stdout[-300:])],
                    "seg": round(time.time() - t0)}
        n, aser, otras, errores = clasificar(xml)
    finally:
        shutil.rmtree(dst, ignore_errors=True)
        shutil.rmtree(bt, ignore_errors=True)
    return {"n": n, "aser": aser, "otras": otras, "errores": errores, "seg": round(time.time() - t0)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo")
    ap.add_argument("--out", default=str(AQUI / "mutaciones_salida.json"))
    ap.add_argument("--paralelo", type=int, default=4)
    ap.add_argument("--parcial", default=str(AQUI / "mutaciones_parcial.jsonl"))
    a = ap.parse_args()
    parcial = Path(a.parcial)
    hechas = {}
    if parcial.exists():
        for l in open(parcial, encoding="utf-8"):
            try:
                x = json.loads(l)
            except ValueError:
                continue
            if x.get("id") != "control":
                hechas[x["id"]] = x
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sel = [m for m in MUT if not a.solo or m[0] in a.solo.split(",")]
    equiv = [] if a.solo and EQUIVALENTE[0] not in a.solo.split(",") else [EQUIVALENTE]
    # antes de gastar tiempo: cada texto original aparece exactamente una vez en el evaluador de hoy
    src = (ORIG / "evaluar_d25.py").read_text(encoding="utf-8")
    for mid, _, _, cambios in sel + equiv:
        for x, _y in cambios:
            if src.count(x) != 1:
                raise SystemExit("mutación %s: el texto original aparece %d veces: %r" % (mid, src.count(x), x[:90]))
    res = {}
    ctrl = una("control", [])
    ok = ctrl["n"] > 0 and not (ctrl["aser"] or ctrl["otras"] or ctrl["errores"])
    print("%-5s %-8s %-75s %s (%d pruebas, %ds)" % ("ctrl", "control", "copia sin mutar, las seis baterías",
                                                   "OK, 0 fallas" if ok else "FALLA EL CONTROL", ctrl["n"], ctrl["seg"]), flush=True)
    res["control"] = dict(ctrl, ok=ok)
    with open(parcial, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(dict(ctrl, ok=ok, id="control", hora=time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())),
                            ensure_ascii=False) + "\n")
    if not ok:
        print("RESUMEN: el control no da verde; nada se cuenta", ctrl)
        Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        return 1
    import threading
    candado = threading.Lock()

    def una_y_anotar(mid, cambios):
        r = una(mid, cambios)
        with candado, open(parcial, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(dict(r, id=mid), ensure_ascii=False) + "\n")
        print("   terminada %s (%ds)" % (mid, r["seg"]), flush=True)
        return r

    pend = [m for m in sel + equiv if m[0] not in hechas]
    print("ya hechas en %s: %d; quedan %d" % (parcial.name, len([m for m in sel + equiv if m[0] in hechas]), len(pend)),
          flush=True)
    with ThreadPoolExecutor(max_workers=a.paralelo) as ex:
        futs = {m[0]: ex.submit(una_y_anotar, m[0], m[3]) for m in pend}
        rs = {mid: f.result() for mid, f in futs.items()}
    rs.update({mid: {k: x[k] for k in ("n", "aser", "otras", "errores", "seg")} for mid, x in hechas.items()})
    atr, por_grupo = 0, {}
    for mid, grupo, nombre, cambios in sel + equiv:
        r = rs[mid]
        atrapada = bool(r["aser"]) and not r["otras"] and not r["errores"]
        estado = "ATRAPADA" if atrapada else ("CAE (no cuenta)" if (r["otras"] or r["errores"]) else "NO ATRAPADA")
        if grupo != "equivalente":
            atr += atrapada
            g = por_grupo.setdefault(grupo, [0, 0]); g[0] += atrapada; g[1] += 1
        res[mid] = dict(r, grupo=grupo, nombre=nombre, estado=estado)
        print("%-5s %-8s %-75s %s (%d pruebas, %d por aserción, %d otra excepción, %d errores, %ds)" % (
            mid, grupo, nombre, estado, r["n"], len(r["aser"]), len(r["otras"]), len(r["errores"]), r["seg"]), flush=True)
        for t, m in r["aser"][:4]:
            print("        aserción: %s" % t)
        for t, m in r["otras"] + r["errores"]:
            print("        NO CUENTA: %s %s" % (t, m))
    print("\nRESUMEN: %d de %d mutaciones atrapadas por aserción (sin la equivalente declarada) | por grupo %s" % (
        atr, len(sel), {k: "%d de %d" % tuple(v) for k, v in por_grupo.items()}))
    if equiv:
        print("equivalente declarada q01: %s (se espera NO ATRAPADA: ninguna prueba puede distinguirla)" % res["q01"]["estado"])
    quedan = sorted(p.name for p in (RAIZ / "experiments").glob("_mut_*"))
    print("copias que quedan en experiments/_mut_*: %s" % (quedan or "ninguna"))
    Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
