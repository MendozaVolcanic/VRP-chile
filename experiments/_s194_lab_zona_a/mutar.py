# -*- coding: utf-8 -*-
"""Control de mutaciones del evaluador pre-registrado (S194; A110, A116; lección S152: una mutación que hace CAER la
prueba no está atrapada).

POR QUÉ. Una prueba que pasa con el evaluador sano no dice que vigile el criterio. Aquí se aplica, una por una, una
mutación del criterio a una COPIA de `evaluar.py` (nunca al del repo), se corre
`tests/test_lab_zona_a_preregistro_s194.py` contra la copia (variable `EVALUAR_LAB_PATH`) SIN las pruebas de sello
(`-k "not sello"`: el sello compara constantes y el sha256 y atraparía todo por construcción) y se cuenta como
atrapada sólo si pytest termina con pruebas FALLIDAS por aserción y sin errores de colección o de ejecución.
Control: la copia sin mutar pasa entera.

Uso: python experiments/_s194_lab_zona_a/mutar.py --tmp D:/vrp-trabajo/temporales/s194_lab_paso2/mut
Escribe `resultado_mutaciones.json` junto a este archivo.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
PRUEBA = ROOT / "tests" / "test_lab_zona_a_preregistro_s194.py"

MUTACIONES = [
    ("alfa", "ALFA = 0.05", "ALFA = 0.5"),
    ("min_volcanes_3", "MIN_VOLCANES_CUMPLE = 4", "MIN_VOLCANES_CUMPLE = 3"),
    ("min_volcanes_5", "MIN_VOLCANES_CUMPLE = 4", "MIN_VOLCANES_CUMPLE = 5"),
    ("n_min_9", "N_MIN_NOCHES = 10 ", "N_MIN_NOCHES = 8 "),
    ("n_min_11", "N_MIN_NOCHES = 10 ", "N_MIN_NOCHES = 11 "),
    ("tasa_035", "TASA_OBJETIVO = 0.30", "TASA_OBJETIVO = 0.35"),
    ("control_sin_desplazar", "DESPLAZAMIENTOS_CONTROL = (15, -15)", "DESPLAZAMIENTOS_CONTROL = (0, 0)"),
    ("control_nunca_falla", "if n_sig > MAX_VOLCANES_SIG_CONTROL:", "if False and n_sig > MAX_VOLCANES_SIG_CONTROL:"),
    ("orden_pareo", "ORDEN_PAREO_DIAS = (0, 1, -1)", "ORDEN_PAREO_DIAS = (1, 0, -1)"),
    ("signo_exceso", "obs = y[g].mean() - y[~g].mean()", "obs = y[~g].mean() - y[g].mean()"),
    ("sin_estratos", "est = np.array([estrato_nube(x[\"nube\"]) for x in u])", "est = np.zeros(len(u), dtype=int)"),
    ("radio_persist", "RADIO_PERSIST_KM = 1.0", "RADIO_PERSIST_KM = 10.0"),
    ("sin_persistencia", "elif len(con_exceso) >= MIN_VOLCANES_CUMPLE and pers[\"supera\"]:",
     "elif len(con_exceso) >= MIN_VOLCANES_CUMPLE:"),
    ("tasa_estricta", "10 * tasas[s][sen][0] <= round(10 * TASA_OBJETIVO)", "10 * tasas[s][sen][0] < round(10 * TASA_OBJETIVO)"),
    ("voto_solo_s", "if r[\"n_S\"] < N_MIN_NOCHES or r[\"n_N\"] < N_MIN_NOCHES:", "if r[\"n_S\"] < N_MIN_NOCHES:"),
    ("cobertura_siempre_igual", "igual = not solo_lab and not solo_prod and", "igual = True or not solo_lab and not solo_prod and"),
    ("invalidas_cuentan", "validos = [(a, b) for a, b in pares if not a[\"invalida\"] and not b[\"invalida\"]]",
     "validos = list(pares)"),
    ("a_no_consume", "if info is not None and info[\"clase\"] is not None:",
     "if info is not None and info[\"clase\"] in (\"S\", \"N\"):"),
    ("sin_poder_global", "elif len(con_poder) < MIN_VOLCANES_CUMPLE:", "elif False:"),
    ("monotonia", "if any(r[i + 1] < r[i] for i in range(len(r) - 1)):", "if False:"),
    ("control_barrido", "return tasas.get(GRILLA_S[0]) == tasas_prod", "return True"),
    ("unidad_pasada", "UNIDAD_TASA = \"noche\"", "UNIDAD_TASA = \"pasada\""),
    ("vota_uniforme", "pers = persistencia_temporal(noches, n_sorteos=n_sorteos)",
     "pers = persistencia(noches, anclas, n_sorteos=n_sorteos)"),
    ("temporal_sin_lejania", "if abs((d - d0).days) > NOCHES_PREVIAS + 3]", "if abs((d - d0).days) > 0]"),
]


def correr(copia):
    env = dict(os.environ, EVALUAR_LAB_PATH=str(copia), PYTHONIOENCODING="utf-8")
    o = subprocess.run([sys.executable, "-m", "pytest", str(PRUEBA), "-q", "-x", "-p", "no:cacheprovider",
                        "-k", "not sello"], capture_output=True, text=True, cwd=str(ROOT), env=env)
    cola = o.stdout.strip().splitlines()[-1] if o.stdout.strip() else ""
    fallidas = int(m.group(1)) if (m := re.search(r"(\d+) failed", cola)) else 0
    errores = int(m.group(1)) if (m := re.search(r"(\d+) error", cola)) else 0
    return o.returncode, fallidas, errores, cola


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
    rc, f, e, cola = correr(sano)
    out["control"] = {"rc": rc, "fallidas": f, "errores": e, "cola": cola, "pasa": rc == 0}
    print("control (sin mutar):", cola, flush=True)
    for nombre, viejo, nuevo in MUTACIONES:
        n = fuente.count(viejo)
        if n != 1:
            out["mutaciones"].append({"nombre": nombre, "error": "el texto a mutar aparece %d veces" % n})
            print(nombre, "NO APLICA (%d apariciones)" % n, flush=True)
            continue
        copia = tmp / nombre / "evaluar.py"
        copia.parent.mkdir(exist_ok=True)
        copia.write_text(fuente.replace(viejo, nuevo), encoding="utf-8", newline="\n")
        rc, f, e, cola = correr(copia)
        atrapada = rc == 1 and f > 0 and e == 0
        out["mutaciones"].append({"nombre": nombre, "rc": rc, "fallidas": f, "errores": e, "cola": cola,
                                  "atrapada_por_asercion": atrapada})
        print(nombre, "ATRAPADA" if atrapada else "NO ATRAPADA", "|", cola, flush=True)
    n_ok = sum(1 for m in out["mutaciones"] if m.get("atrapada_por_asercion"))
    out["resumen"] = "%d de %d mutaciones atrapadas por aserción; control %s" % (
        n_ok, len(MUTACIONES), "pasa" if out["control"]["pasa"] else "NO PASA")
    print(out["resumen"])
    (AQUI / "resultado_mutaciones.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n",
                                                    encoding="utf-8", newline="\n")
    return 0 if (out["control"]["pasa"] and n_ok == len(MUTACIONES)) else 1


if __name__ == "__main__":
    raise SystemExit(main())
