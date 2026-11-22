# -*- coding: utf-8 -*-
"""Control de mutaciones del evaluador pre-registrado (S195; A110, A116; lección S152: una mutación que hace CAER la
prueba no está atrapada).

POR QUÉ. Una prueba que pasa con el evaluador sano no dice que vigile el criterio. Aquí se aplica, una por una, una
mutación del criterio a una COPIA de `evaluar.py` (nunca al del repo), se corre
`tests/test_viirs_dia_control_preregistro_s195.py` contra la copia (variable `EVALUAR_VDIA_PATH`) SIN las pruebas de sello
(`-k "not sello"`: el sello compara constantes y el sha256 y atraparía todo por construcción) y se cuenta como
atrapada sólo si pytest termina con pruebas FALLIDAS por aserción y sin errores de colección o de ejecución.
Controles: la copia sin mutar pasa entera, y una copia que sólo hace caer no cuenta como atrapada.

Uso: python experiments/_s195_viirs_dia_control/mutar.py --tmp D:/vrp-trabajo/temporales/s195/viirs_prereg/mut
Escribe `resultado_mutaciones.json` junto a este archivo.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
PRUEBA = ROOT / "tests" / "test_viirs_dia_control_preregistro_s195.py"

MUTACIONES = [
    ("historia_60_dias", "DIAS_HISTORIA = 30 ", "DIAS_HISTORIA = 60 "),
    ("vecindad_0", "VECINDAD = 1 ", "VECINDAD = 0 "),
    ("vecindad_2", "VECINDAD = 1 ", "VECINDAD = 2 "),
    ("umbral_mw", "UMBRAL_MW = 1.0 ", "UMBRAL_MW = 0.5 "),
    ("dias_swir_7", "DIAS_SWIR = 3 ", "DIAS_SWIR = 7 "),
    ("horas_vecina_24", "HORAS_MIROVA_VECINA = 12 ", "HORAS_MIROVA_VECINA = 24 "),
    ("n_min_a_5", "N_MIN_A = 6 ", "N_MIN_A = 5 "),
    ("n_min_p_4", "N_MIN_P = 5\n", "N_MIN_P = 4\n"),
    ("quitar_mitad", "QUITAR_A = (2, 3)", "QUITAR_A = (1, 2)"),
    ("una_p_perdida", "MAX_P_PERDIDAS = 0\n", "MAX_P_PERDIDAS = 1\n"),
    ("r_mitad", "MAX_R_PERDIDAS = (1, 3)", "MAX_R_PERDIDAS = (1, 2)"),
    ("alfa_r1_005", 'ALFA_REGLA = {"R1": 0.04,', 'ALFA_REGLA = {"R1": 0.05,'),
    ("historia_con_futuro", "i1 = bisect.bisect_left(ts, dt)", "i1 = len(ts)"),
    ("historia_con_el_dia", 'if r["es_dia"] or r["b"] not in SENSORES_VIIRS:', 'if r["b"] not in SENSORES_VIIRS:'),
    ("historia_sin_grilla", 'out |= c', 'out |= c\n    for (v2, b2), (t2, c2) in idx.items():\n        if v2 == vol:\n            for x in c2:\n                out |= x'),
    ("radiante_la_fria", "key=lambda c: (-c[2], c[0], c[1])", "key=lambda c: (c[2], c[0], c[1])"),
    ("r2_cualquiera", "return con_historia(radiante(cs), hist)", "return any(con_historia(c, hist) for c in cs)"),
    ("sin_celdas_suprime", "    if not cs:\n        return True\n    if regla", "    if not cs:\n        return False\n    if regla"),
    ("p_tambien_ocr", 'pasada["estado"] == "alerta" and pasada["fuente"] == "CONS" and', 'pasada["estado"] == "alerta" and'),
    ("p_sin_radio", 'and pasada["dist_km"] <= inner_km):', 'and True):'),
    ("fp_no_es_silencio", 'pasada["estado"] not in ("rutina", "fp")', 'pasada["estado"] not in ("rutina",)'),
    ("vecina_siempre", "(pasada is None and cumbre_cerca)", "(cumbre_cerca)"),
    ("swir_sin_usable", 'if not caja or not caja.get("usable") or not en_caja(rec.get("lat"), rec.get("lon"), caja):\n        return False\n    d0 = rec["dt"].date()\n    for e',
     'if not caja or not en_caja(rec.get("lat"), rec.get("lon"), caja):\n        return False\n    d0 = rec["dt"].date()\n    for e'),
    ("swir_sin_caja", 'or not en_caja(rec.get("lat"), rec.get("lon"), caja):\n        return False\n    d0 = rec["dt"].date()\n    for e', ':\n        return False\n    d0 = rec["dt"].date()\n    for e'),
    ("vecina_ocr", 'any(p["fuente"] == "CONS" and p["estado"] == "alerta"', 'any(p["estado"] == "alerta"'),
    ("pareo_otro_sensor", 'lista = idx.get((rec["vol"], rec["b"]), [])',
     'lista = [p for k, v in idx.items() if k[0] == rec["vol"] for p in v]'),
    ("sin_poder_solo_a", 'if n["A"] < N_MIN_A or n["P"] < N_MIN_P:', 'if n["A"] < N_MIN_A:'),
    ("r1_sin_prioridad", 'if por_regla["R1"]["estado"] == CUMPLE:', 'if False:'),
    ("i1_apagada", "if pubs_dia and sin > MAX_FRAC_SIN_CELDAS * len(pubs_dia):", "if False:"),
    ("i2_apagada", "if tiene < MIN_FRAC_DIAS_HISTORIA * len(ds):", "if False:"),
    ("i3_apagada", "if pasadas_dia_tabla and faltan > MAX_FRAC_MIROVA_SIN_RECORD * len(pasadas_dia_tabla):", "if False:"),
    ("i4_apagada", "if comparables and iguales < MIN_ACUERDO_NOCHE * comparables:", "if False:"),
    ("invalido_no_manda", "    if problemas_instrumento:\n        return {",
     "    if False:\n        return {"),
    ("invalido_con_metricas", '"veredicto": INVALIDO, "regla": None}\n    n = collections',
     '"veredicto": INVALIDO, "regla": None, "n": {}}\n    n = collections'),
    ("universo_sin_o", 'UNIVERSO = ("P", "A", "R", "O")', 'UNIVERSO = ("P", "A", "R")'),
    ("estratificado_sin_estratos", "x = por[s]", "x = por[0]"),
    ("desmentible_sin_escena", 'e.get("alerta") is not None and abs', 'abs'),
    ("r0_siempre", "        return bool(hist)\n", "        return True\n"),
    ("fecha_veredicto_libre", "return hoy_iso >= FECHA_MIN_VEREDICTO", "return True"),
]


def correr(copia):
    env = dict(os.environ, EVALUAR_VDIA_PATH=str(copia), PYTHONIOENCODING="utf-8")
    xml = Path(copia).parent / "junit.xml"
    o = subprocess.run([sys.executable, "-m", "pytest", str(PRUEBA), "-q", "-p", "no:cacheprovider",
                        "-k", "not sello", "--junitxml", str(xml)], capture_output=True, text=True, cwd=str(ROOT),
                       env=env, timeout=600)
    cola = o.stdout.strip().splitlines()[-1] if o.stdout.strip() else ""
    fallidas = int(m.group(1)) if (m := re.search(r"(\d+) failed", cola)) else 0
    errores = int(m.group(1)) if (m := re.search(r"(\d+) error", cola)) else 0
    # Control de caída (S152): una prueba que cae por excepción no atrapa la mutación; sólo cuentan las que fallan
    # por aserción: en el JUnit XML de pytest su mensaje empieza con «assert» o «AssertionError»; el de una caída, con
    # el nombre de la excepción («KeyError: ...»).
    tipos = [f.get("message", "") for f in ET.parse(xml).getroot().iter("failure")] if xml.exists() else []
    por_asercion = sum(1 for t in tipos if t.startswith(("assert", "AssertionError")))
    return o.returncode, fallidas, errores, cola, por_asercion, len(tipos) - por_asercion


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tmp", required=True)
    a = ap.parse_args()
    fuente = (AQUI / "evaluar.py").read_text(encoding="utf-8")
    tmp = Path(a.tmp)
    tmp.mkdir(parents=True, exist_ok=True)
    out = {"control": None, "mutaciones": []}
    sano = tmp / "sano" / "evaluar.py"
    sano.parent.mkdir(exist_ok=True)
    sano.write_text(fuente, encoding="utf-8", newline="\n")
    rc, f, e, cola, _, _ = correr(sano)
    out["control"] = {"rc": rc, "fallidas": f, "errores": e, "cola": cola, "pasa": rc == 0}
    print("control (sin mutar):", cola, flush=True)
    # Control de caída: una copia que sólo hace CAER (excepción en con_historia) no puede contar como atrapada.
    raiz = "def con_historia(celda, hist, vecindad=VECINDAD):\n"
    caida = tmp / "_caida" / "evaluar.py"
    caida.parent.mkdir(exist_ok=True)
    caida.write_text(fuente.replace(raiz, raiz + "    raise KeyError('caida')\n"), encoding="utf-8", newline="\n")
    rc, f, e, cola, f_as, f_ca = correr(caida)
    out["control_caida"] = {"fallidas": f, "por_asercion": f_as, "por_caida": f_ca, "cola": cola,
                            "contada_como_atrapada": rc == 1 and f_as > 0 and e == 0}
    print("control de caída:", out["control_caida"], flush=True)
    for nombre, viejo, nuevo in MUTACIONES:
        n = fuente.count(viejo)
        if n != 1:
            out["mutaciones"].append({"nombre": nombre, "error": "el texto a mutar aparece %d veces" % n})
            print(nombre, "NO APLICA (%d apariciones)" % n, flush=True)
            continue
        copia = tmp / nombre / "evaluar.py"
        copia.parent.mkdir(exist_ok=True)
        copia.write_text(fuente.replace(viejo, nuevo), encoding="utf-8", newline="\n")
        rc, f, e, cola, f_asercion, f_caida = correr(copia)
        atrapada = rc == 1 and f_asercion > 0 and e == 0
        out["mutaciones"].append({"nombre": nombre, "rc": rc, "fallidas": f, "por_asercion": f_asercion,
                                  "por_caida": f_caida, "errores": e, "cola": cola, "atrapada_por_asercion": atrapada})
        print(nombre, "ATRAPADA" if atrapada else "NO ATRAPADA", "|", cola, flush=True)
    n_ok = sum(1 for m in out["mutaciones"] if m.get("atrapada_por_asercion"))
    out["resumen"] = "%d de %d mutaciones atrapadas por aserción; control %s; control de caída %s" % (
        n_ok, len(MUTACIONES), "pasa" if out["control"]["pasa"] else "NO PASA",
        "no cuenta (bien)" if not out["control_caida"]["contada_como_atrapada"] else "CUENTA (mal)")
    print(out["resumen"])
    (AQUI / "resultado_mutaciones.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n",
                                                    encoding="utf-8", newline="\n")
    return 0 if (out["control"]["pasa"] and n_ok == len(MUTACIONES)
                 and not out["control_caida"]["contada_como_atrapada"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
