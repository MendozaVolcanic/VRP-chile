# -*- coding: utf-8 -*-
"""Control de mutaciones del re-sello S202 (R5C-101) del evaluador del piso (A110, A116; lección S152: una mutación que
hace CAER la prueba no está atrapada).

POR QUÉ. Que `tests/test_lab_piso_resello_s202.py` pase con el evaluador re-sellado no dice que vigile cada arreglo.
Se aplica, una por una, una mutación que apaga un arreglo a una COPIA de `evaluar.py` (nunca al del repo), se corre esa
prueba contra la copia (`EVALUAR_PISO_PATH`) y cuenta como atrapada sólo si pytest termina con pruebas FALLIDAS por
aserción (todas las fallas AssertionError, R5FA-110) y sin errores. Controles: la copia sin mutar pasa entera, y una
mutación que rompe la carga del módulo (`caida`) y otra que lanza TypeError dentro de `calibrar` (`caida_en_ejecucion`)
tienen que salir NO atrapadas.

Uso: python experiments/_s196_lab_piso/mutar_resello_s202.py --tmp D:/vrp-trabajo/temporales/s202/mut_resello
Escribe `resultado_mutaciones_resello_s202.json` junto a este archivo.
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
FUENTE = AQUI / "evaluar.py"
PRUEBA = ROOT / "tests" / "test_lab_piso_resello_s202.py"
NL = "\n"
COMILLA = '"'

MUTACIONES = {
    "sin_mutar": None,
    "caida": ("import argparse" + NL, "import argparse_que_no_existe" + NL),
    # Control de R5FA-110: el código mutado lanza TypeError dentro de calibrar; las pruebas fallan, pero no por
    # aserción. Tiene que salir NO atrapada.
    "caida_en_ejecucion": ('exclusion = {"n": len(contables),', 'exclusion = {"n": len(contables) + None,'),
    # Cada una apaga una parte del re-sello S202 (R5C-101).
    "sin_exclusion": ("    if excluidas:" + NL + "        comun", "    if False:" + NL + "        comun"),
    "exclusion_sin_produccion": ("excluir_de_carpeta(originales[k], a_contar[k], excluidas)",
                                 "excluir_de_carpeta(originales[k], a_contar[k], excluidas if k != 'prod' else set())"),
    "cuenta_invalidas_en_todos": (" and any(v is None for v in d.values())}", "}"),
    "sin_freno_1": ("    elif decisivas:" + NL, "    elif False:" + NL),
    "freno_1_solo_si_sale": ("if neg_con != neg_sin:", "if neg_con and not neg_sin:"),
    "sin_freno_2": ("    elif supera_tope(len(contables), n_neg_control):" + NL, "    elif False:" + NL),
    "sin_freno_3": ('    elif (eleccion_devueltas["estado"], eleccion_devueltas["valor"]) != (res["estado"], res["valor"]):' + NL,
                    "    elif False:" + NL),
    "freno_3_solo_piso": ('    elif (eleccion_devueltas["estado"], eleccion_devueltas["valor"]) != (res["estado"], res["valor"]):' + NL,
                          '    elif eleccion_devueltas["valor"] != res["valor"]:' + NL),
    "freno_3_sin_devolver": ('v["NOCHE"][0] + pub_quitadas.get(str(k), 0)', 'v["NOCHE"][0]'),
    "tope_mayor_o_igual": ("* n_excluidas > n_noches_neg", "* n_excluidas >= n_noches_neg"),
    "sin_control_de_replica": ("    elif not replica_igual:" + NL, "    elif False:" + NL),
    "sin_publicaciones_quitadas": ("quitadas[str(k)] = quitadas.get(str(k), 0) + 1", "quitadas[str(k)] = 0"),
    "contable_sin_ventana": (" or not _en_ventana({" + COMILLA + "datetime_utc" + COMILLA + ": t}, fin)", ""),
    "clave_sin_canonizar": (
        "        t = datetime.strptime(t, " + COMILLA + "%Y-%m-%d %H:%M" + COMILLA + ").strftime(" + COMILLA
        + "%Y-%m-%d %H:%M" + COMILLA + ")" + NL, "        pass" + NL),
    "sin_declarar_escena": ("[{" + COMILLA + "clave" + COMILLA + ": list(c),",
                            "[{" + COMILLA + "clave" + COMILLA + ": None,"),
}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--tmp", required=True)
    a = ap.parse_args()
    tmp = Path(a.tmp)
    tmp.mkdir(parents=True, exist_ok=True)
    src = FUENTE.read_text(encoding="utf-8")
    out = {}
    for nombre, mut in MUTACIONES.items():
        if mut is None:
            texto = src
        else:
            assert src.count(mut[0]) == 1, (nombre, src.count(mut[0]))
            texto = src.replace(mut[0], mut[1])
        copia = tmp / nombre / "experiments" / "_s196_lab_piso" / "evaluar.py"
        copia.parent.mkdir(parents=True, exist_ok=True)
        env = dict(os.environ, EVALUAR_PISO_PATH=str(copia), PYTHONIOENCODING="utf-8")
        # La copia importa el S194 desde ROOT de su propia ruta: se la apunta al repo.
        texto2 = texto.replace("ROOT = Path(__file__).resolve().parents[2]", "ROOT = Path(%r)" % str(ROOT))
        copia.write_text(texto2, encoding="utf-8")
        r = subprocess.run([sys.executable, "-m", "pytest", str(PRUEBA), "-q", "-p", "no:cacheprovider", "--tb=line",
                            "--basetemp", str(tmp / nombre / "bt")], capture_output=True, text=True,
                           encoding="utf-8", env=env, cwd=str(ROOT))
        ult = (r.stdout.strip().splitlines() or [""])[-1]
        fallan = int(m.group(1)) if (m := re.search(r"(\d+) failed", ult)) else 0
        errores = int(m.group(1)) if (m := re.search(r"(\d+) error", ult)) else 0
        # R5FA-110 (ronda 5 de Codex): una prueba que falla porque el código mutado lanza otra excepción (KeyError,
        # TypeError...) es una caída, no una captura. Con --tb=line cada falla deja «archivo:línea: Tipo: mensaje»,
        # o «archivo:línea: assert ...» si el assert no trae mensaje; cuenta como atrapada sólo si todas las fallas
        # son de aserción.
        tipos = re.findall(r"^\S+\.py:\d+: (\w+)", r.stdout, flags=re.M)
        no_asercion = [t for t in tipos if t not in ("AssertionError", "assert")]
        out[nombre] = {"ultima_linea": ult, "fallan": fallan, "errores": errores, "tipos_de_falla": sorted(set(tipos)),
                       "atrapada": fallan > 0 and errores == 0 and len(tipos) == fallan and not no_asercion}
        print(nombre, "|", ult, "| atrapada" if out[nombre]["atrapada"] else "| NO atrapada", flush=True)
    controles = ("sin_mutar", "caida", "caida_en_ejecucion")
    ok = (out["sin_mutar"]["fallan"] == 0 and out["sin_mutar"]["errores"] == 0 and not out["caida"]["atrapada"]
          and out["caida_en_ejecucion"]["fallan"] > 0 and not out["caida_en_ejecucion"]["atrapada"]
          and all(v["atrapada"] for k, v in out.items() if k not in controles))
    out["_veredicto"] = "OK" if ok else "FALLA"
    print("veredicto:", out["_veredicto"])
    (AQUI / "resultado_mutaciones_resello_s202.json").write_text(json.dumps(out, indent=1, ensure_ascii=False),
                                                                 encoding="utf-8", newline="\n")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
