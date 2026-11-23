# -*- coding: utf-8 -*-
"""Control de mutaciones del evaluador de la palanca del piso (S196; A110, A116; lección S152: una mutación que hace
CAER la prueba no está atrapada).

POR QUÉ. Que las pruebas pasen con el evaluador sano no dice que vigilen el criterio. Se aplica, una por una, una
mutación a una COPIA de `evaluar.py` (nunca al del repo), se corre `tests/test_lab_piso_preregistro_s196.py` contra
la copia (`EVALUAR_PISO_PATH`) SIN las pruebas de sello (`-k "not sello"`: comparan constantes y sha256 y atraparían
todo por construcción), y cuenta como atrapada sólo si pytest termina con pruebas FALLIDAS por aserción y sin
errores. Dos controles: la copia sin mutar pasa entera, y una mutación que rompe la carga del módulo (`caida`) tiene
que salir NO atrapada: si saliera atrapada, el contador estaría contando caídas como aciertos.

Uso: python experiments/_s196_lab_piso/mutar.py --tmp D:/vrp-trabajo/temporales/s196_piso/mut
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
PRUEBA = ROOT / "tests" / "test_lab_piso_preregistro_s196.py"

MUTACIONES = [
    ("tasa_estricta", "10 * tasas[k][sen][0] <= round", "10 * tasas[k][sen][0] < round"),
    ("tasa_035", "TASA_OBJETIVO = E.TASA_OBJETIVO", "TASA_OBJETIVO = 0.35"),
    ("unidad_pasada", "UNIDAD_TASA = E.UNIDAD_TASA", "UNIDAD_TASA = \"pasada\""),
    ("monotonia_off", "if any(r[i + 1] < r[i] for i in range(len(r) - 1)):", "if False:"),
    ("camino_sin_control", "CAMINO = (CONTROL,) + GRILLA_PISO", "CAMINO = GRILLA_PISO"),
    ("sin_minimo_negativos", "if any(tasas[k][sen][1] < N_MIN_NEG for k in CAMINO):", "if False:"),
    ("sin_valor_off", "if not ok(CONTROL):", "if False:"),
    ("sin_valor_de_piso_off", "if not ok(GRILLA_PISO[0]):", "if False:"),
    ("sin_extension_off", "if S_A == S_CONTROL and elegido == PISO_PROD:", "if False:"),
    ("rotulo_piso_de_hoy_off", "if elegido == GRILLA_PISO[0]:", "if False:"),
    ("rotulo_piso_de_grilla_off", "if elegido == GRILLA_PISO[-1]:", "if False:"),
    ("control_tasas_siempre", "if tasas.get(CONTROL) != tasas_prod:", "if False:"),
    ("control_tasas_s5_siempre", "return S_A != S_CONTROL or tasas.get(GRILLA_PISO[0]) == tasas_prod", "return True"),
    ("identidad_ignora_diferencias", "\"identico\": not dif and (permitir_vacio or len(a) > 0),",
     "\"identico\": (permitir_vacio or len(a) > 0),"),
    ("identidad_acepta_vacio", "\"identico\": not dif and (permitir_vacio or len(a) > 0),", "\"identico\": not dif,"),
    ("firma_sin_diag", "+ tuple(dg.get(c) for c in CAMPOS_DIAG) + (json.dumps", "+ (json.dumps"),
    ("firma_sin_s1", " + (json.dumps(dg.get(\"s1\"), sort_keys=True),))", ")"),
    ("firma_sin_vrp", "CAMPOS_IDENTIDAD = (\"vrp_mw\", ", "CAMPOS_IDENTIDAD = ("),
    ("firma_sin_clase", "\"distance_class\", \"final_hotspot_lat\"", "\"final_hotspot_lat\""),
    ("calibrar_sin_identidad", "    if not all(v[\"identico\"] for v in ident.values()):", "    if False:"),
    ("calibrar_sin_donde_no_actua", "    elif not all(v[\"identico\"] for v in fuera.values()):", "    elif False:"),
    ("calibrar_sin_cuentas", "    elif not control_tasas(tasas, tasas_prod):", "    elif False:"),
    ("zona_no_actua_de_noche", "(r.get(\"diag_codigo_mirova\") or {}).get(\"dayflag\") == 1", "(r.get(\"diag_codigo_mirova\") or {}).get(\"dayflag\") == 0"),
    ("vara_propia", "veredicto = E.veredicto", "veredicto = lambda *a, **k: None"),
    ("delega_solo_poder", "if argv and argv[0] in (\"evaluar\", \"poder\"):", "if argv and argv[0] in (\"poder\",):"),
]
CAIDA = ("caida", "E = _cargar_s194()", "E = None")


def correr(copia):
    env = dict(os.environ, EVALUAR_PISO_PATH=str(copia), PYTHONIOENCODING="utf-8")
    o = subprocess.run([sys.executable, "-m", "pytest", str(PRUEBA), "-q", "-p", "no:cacheprovider",
                        "-k", "not sello"], capture_output=True, text=True, cwd=str(ROOT), env=env)
    cola = o.stdout.strip().splitlines()[-1] if o.stdout.strip() else ""
    fallidas = int(m.group(1)) if (m := re.search(r"(\d+) failed", cola)) else 0
    errores = int(m.group(1)) if (m := re.search(r"(\d+) error", cola)) else 0
    return o.returncode, fallidas, errores, cola


def _arbol(base, texto):
    """La copia vive en <base>/experiments/_s196_lab_piso/evaluar.py junto a una copia byte a byte del evaluador S194
    en <base>/experiments/_s194_lab_zona_a/: el evaluador resuelve la vara relativa a su raíz."""
    copia = base / "experiments" / "_s196_lab_piso" / "evaluar.py"
    s194 = base / "experiments" / "_s194_lab_zona_a" / "evaluar.py"
    copia.parent.mkdir(parents=True, exist_ok=True)
    s194.parent.mkdir(parents=True, exist_ok=True)
    s194.write_bytes((ROOT / "experiments" / "_s194_lab_zona_a" / "evaluar.py").read_bytes())
    copia.write_text(texto, encoding="utf-8", newline="\n")
    return copia


def aplicar(fuente, tmp, nombre, viejo, nuevo):
    n = fuente.count(viejo)
    if n != 1:
        return {"nombre": nombre, "error": "el texto a mutar aparece %d veces" % n}
    copia = _arbol(tmp / nombre, fuente.replace(viejo, nuevo))
    rc, f, e, cola = correr(copia)
    return {"nombre": nombre, "rc": rc, "fallidas": f, "errores": e, "cola": cola,
            "atrapada_por_asercion": rc == 1 and f > 0 and e == 0}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tmp", required=True)
    a = ap.parse_args()
    fuente = (AQUI / "evaluar.py").read_text(encoding="utf-8")
    tmp = Path(a.tmp)
    tmp.mkdir(parents=True, exist_ok=True)
    sano = _arbol(tmp / "sano", fuente)
    rc, f, e, cola = correr(sano)
    out = {"control": {"rc": rc, "fallidas": f, "errores": e, "cola": cola, "pasa": rc == 0}, "mutaciones": []}
    print("control (sin mutar):", cola, flush=True)
    caida = aplicar(fuente, tmp, *CAIDA)
    out["control_de_caida"] = dict(caida, esperado="NO atrapada (cae con error)",
                                   ok=not caida.get("atrapada_por_asercion") and caida.get("errores", 0) > 0)
    print("control de caída:", "OK" if out["control_de_caida"]["ok"] else "FALLA", "|", caida.get("cola"), flush=True)
    for nombre, viejo, nuevo in MUTACIONES:
        r = aplicar(fuente, tmp, nombre, viejo, nuevo)
        out["mutaciones"].append(r)
        print(nombre, "NO APLICA" if "error" in r else ("ATRAPADA" if r["atrapada_por_asercion"] else "NO ATRAPADA"),
              "|", r.get("cola", r.get("error")), flush=True)
    n_ok = sum(1 for m in out["mutaciones"] if m.get("atrapada_por_asercion"))
    out["resumen"] = "%d de %d mutaciones atrapadas por aserción; control %s; control de caída %s" % (
        n_ok, len(MUTACIONES), "pasa" if out["control"]["pasa"] else "NO PASA",
        "ok" if out["control_de_caida"]["ok"] else "FALLA")
    print(out["resumen"])
    (AQUI / "resultado_mutaciones.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n",
                                                    encoding="utf-8", newline="\n")
    return 0 if (out["control"]["pasa"] and out["control_de_caida"]["ok"] and n_ok == len(MUTACIONES)) else 1


if __name__ == "__main__":
    raise SystemExit(main())
