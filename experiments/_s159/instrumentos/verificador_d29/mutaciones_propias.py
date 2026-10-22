# -*- coding: utf-8 -*-
"""Verificador de D-29: mutaciones PROPIAS del evaluador (distintas de las 4 del auditor), medidas por dos caminos:
 (a) la prueba del repo tests/test_evaluar_d25_dias_d29_s160.py sobre la copia mutada (D25_EVALUADOR_DIR), con el tipo
     de cada falla leido del XML de JUnit (ATRAPADA solo por AssertionError, S152/S156);
 (b) los casos sinteticos de cobertura_sintetica.py sobre la misma copia: el numero del consumidor afectado tiene que
     cambiar respecto del evaluador sin mutar (sintetico_real.json). Si no cambia, la mutacion es EQUIVALENTE bajo
     estos datos o el instrumento no la ve, y se dice cual.
La copia vive en experiments/_verif_d29_mut/evaluar_d25.py (RAIZ = AQUI.parents[1] sigue siendo la raiz) y se borra.
Uso: python mutaciones_propias.py --tmp <dir> --out <json> [--solo m1,m2]
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[3]
SRC_PATH = RAIZ / "experiments" / "_s157_prereg_d25" / "evaluar_d25.py"
SRC = SRC_PATH.read_text(encoding="utf-8")
COPIA = RAIZ / "experiments" / "_verif_d29_mut"
TEST = "tests/test_evaluar_d25_dias_d29_s160.py"

L_DIAS = 'DIAS_EXCLUIDOS = {"V1": ("2026-10-13", "2026-10-17", "2026-10-18", "2026-10-19", "2026-10-20"), "V2": ()}'
L_DICT = '        return {k: v for k, v in claves.items() if k.split("|")[2][:10] not in dias}\n'
L_SET = '    return {k for k in claves if k.split("|")[2][:10] not in dias}\n'
LOCAL = ('    from datetime import datetime, timedelta\n'
         '    def _f(k):\n'
         '        t = k.split("|")[2][:16].replace("T", " ")\n'
         '        return (datetime.strptime(t, "%Y-%m-%d %H:%M") - timedelta(hours=3)).strftime("%Y-%m-%d")\n'
         '    if isinstance(claves, dict):\n'
         '        return {k: v for k, v in claves.items() if _f(k) not in dias}\n'
         '    return {k for k in claves if _f(k) not in dias}\n')

# nombre: (antes, despues, casos sinteticos que deberian verla, campo que deberia cambiar)
MUT = {
    "p1_sin_dias_control_positivo": (L_DIAS, 'DIAS_EXCLUIDOS = {"V1": (), "V2": ()}',
                                     "nulo,d_sin_17,todos_sin_13_17_18,dc_17_en_D,mov_17_en_D,g_apagado,madrugada_13", "todos"),
    "p2_crudos_resultado_descartado": ("        R[n] = filtrar_dias(R[n], excl)\n", "        filtrar_dias(R[n], excl)\n",
                                       "d_sin_17,dc_17_en_D", "cobertura_ok / P4_cambia_dc"),
    "p3_tabla_sin_excl": ("filtrar_dias(t, excl).items()", "filtrar_dias(t, ()).items()",
                          "mov_17_en_D,g_apagado", "P4_movidas / determinismo"),
    "p4_cobertura_sin_excl": ("cob = {vs: filtrar_dias(ks, excl) for vs, ks in", "cob = {vs: filtrar_dias(ks, ()) for vs, ks in",
                              "todos_sin_13_17_18", "cobertura_ok"),
    "p5_set_no_filtra": (L_SET, "    return claves\n", "todos_sin_13_17_18", "cobertura_ok"),
    "p6_hora_local_chile": ('    if isinstance(claves, dict):\n' + L_DICT + L_SET, LOCAL, "madrugada_13", "madrugada_en_json"),
    "p7_cabecera_v1_callada": ('    if excl:\n        print("== EVALUADO SIN', '    if False:\n        print("== EVALUADO SIN',
                               "nulo", "cabecera_linea_idx"),
    "p8_sin_el_18": ('"2026-10-17", "2026-10-18", "2026-10-19"', '"2026-10-17", "2026-10-19"', "d_sin_18", "cobertura_ok"),
    "p9_solo_el_mes": ('[2][:10] not in dias', '[2][:7] not in dias', "d_sin_17", "cobertura_ok"),
}


def correr_test(d):
    xml = d / "junit.xml"
    env = dict(os.environ, D25_EVALUADOR_DIR=str(d), PYTHONIOENCODING="utf-8")
    subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--junitxml", str(xml), TEST],
                   cwd=RAIZ, env=env, capture_output=True, text=True)
    casos = list(ET.parse(xml).getroot().iter("testcase"))
    fallas = [(c.get("name"), (f.get("message") or "").split(":")[0]) for c in casos for f in c.findall("failure")]
    errores = [c.get("name") for c in casos for _ in c.findall("error")]
    aser = [n for n, t in fallas if t == "AssertionError"]
    otras = [n for n, t in fallas if t != "AssertionError"]
    estado = "ATRAPADA" if aser and not otras and not errores else ("NO ATRAPADA" if not fallas and not errores else "CAIDA")
    return {"n_pruebas": len(casos), "estado": estado, "fallan_por_asercion": aser, "otras": otras, "errores": errores}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tmp", required=True); ap.add_argument("--out", required=True); ap.add_argument("--solo")
    ap.add_argument("--real", default=str(AQUI / "sintetico_real.json"))
    a = ap.parse_args()
    real = json.load(open(a.real, encoding="utf-8"))["casos"]
    extra = AQUI / "sintetico_real_extra.json"
    if extra.exists():
        real.update(json.load(open(extra, encoding="utf-8"))["casos"])
    res = {}
    for m, (antes, despues, casos, campo) in MUT.items():
        if a.solo and m not in a.solo.split(","):
            continue
        n = SRC.count(antes)
        assert n >= 1, (m, n)
        mut = SRC.replace(antes, despues)
        assert mut != SRC, m
        if COPIA.exists():
            shutil.rmtree(COPIA)
        COPIA.mkdir()
        (COPIA / "evaluar_d25.py").write_text(mut, encoding="utf-8")
        # la copia necesita la referencia congelada al lado (VENTANAS["V1"]["ref"] = AQUI / "_congelado_v1"); la primera
        # corrida sin esto murio en los 9 mutantes y el comparador dijo "VE LA MUTACION" por nulos (A110): control abajo
        shutil.copytree(SRC_PATH.parent / "_congelado_v1", COPIA / "_congelado_v1")
        t = correr_test(COPIA)
        # (b) sinteticos sobre la copia
        out = Path(a.tmp) / ("sint_%s.json" % m)
        p = subprocess.run([sys.executable, str(AQUI / "cobertura_sintetica.py"), "--evaluador", str(COPIA / "evaluar_d25.py"),
                            "--tmp", str(Path(a.tmp) / m), "--out", str(out), "--casos", casos],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        (Path(a.tmp) / ("sint_%s_salida.txt" % m)).write_text(p.stdout + "\n--- stderr ---\n" + p.stderr, encoding="utf-8")
        sint = json.load(open(out, encoding="utf-8"))["casos"] if out.exists() else {}
        difs = {}
        for caso, med in sint.items():
            r0 = real.get(caso, {})
            difs[caso] = {k: [r0.get(k), v] for k, v in med.items()
                          if k not in ("fallo", "primera_linea", "estado") and r0.get(k) != v}
        caido = [c for c, med in sint.items() if med.get("cobertura_ok") is None] or (not sint and ["(sin salida)"])
        vista = any(difs[c] for c in difs) and not caido
        res[m] = {"ocurrencias_reemplazadas": n, "prueba_repo": t, "casos": casos, "campo_esperado": campo,
                  "sintetico_difiere_del_real": vista, "evaluador_caido_en": caido, "diferencias": difs}
        print("%-32s prueba repo: %-11s | sintetico: %s | difs %s" % (
            m, t["estado"], ("EVALUADOR CAIDO en %s" % caido) if caido else
            "VE LA MUTACION" if vista else "NO LA VE (equivalente bajo estos datos o ciego)",
            json.dumps(difs, ensure_ascii=False)[:400]), flush=True)
        shutil.rmtree(COPIA, ignore_errors=True)
    Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    assert not COPIA.exists()


if __name__ == "__main__":
    main()
