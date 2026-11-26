# -*- coding: utf-8 -*-
"""Control de mutaciones del re-sello S200 del evaluador del piso (A110, A116; lección S152: una mutación que hace
CAER la prueba no está atrapada).

POR QUÉ. Que `tests/test_lab_piso_resello_s200.py` pase con el evaluador re-sellado no dice que vigile cada arreglo.
Se aplica, una por una, una mutación que apaga un arreglo a una COPIA de `evaluar.py` (nunca al del repo), se corre esa
prueba contra la copia (`EVALUAR_PISO_PATH`) y cuenta como atrapada sólo si pytest termina con pruebas FALLIDAS por
aserción y sin errores. Controles: la copia sin mutar pasa entera, y una mutación que rompe la carga del módulo
(`caida`) tiene que salir NO atrapada.

Uso: python experiments/_s196_lab_piso/mutar_resello_s200.py --tmp D:/vrp-trabajo/temporales/s200/mut_resello
Escribe `resultado_mutaciones_resello_s200.json` junto a este archivo.
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
PRUEBA = ROOT / "tests" / "test_lab_piso_resello_s200.py"

MUTACIONES = {
    "sin_mutar": None,
    "caida": ("import argparse\n", "import argparse_que_no_existe\n"),
    "v201_sin_filtro_de_dia": ("quedan = [r for r in recs if not rechaza_como_laboratorio(r, vol, dia, herr)]",
                               "quedan = list(recs)"),
    "v201_filtra_viirs": ("dia, enable_daytime_viirs=True)", "dia, enable_daytime_viirs=False)"),
    "101_sin_cobertura": ('if not cob["igual"]:', "if False:"),
    "101_sin_ventana": ("return E.VENTANA_CALIBRACION_INICIO <= str(r.get(\"datetime_utc\", \"\"))[:10] <= fin",
                        "return True"),
    "102_sin_poder_minimo": ("any(v < N_MIN_FUERA for v in fuera_en_ventana.values())", "False"),
    # Re-sello S200b (observaciones del verificador de #1129)
    "b1_sin_poder_tapa_invalido": ('res["estado"] != INVALIDO and any(', "any("),
    "b2_poder_sin_ventana": ("for r in _sin_actuar(recs[str(p)]) if _en_ventana(r, fin))",
                             "for r in _sin_actuar(recs[str(p)]))"),
    "b3_coordenadas_por_record": ("quedan = [r for r in recs if not rechaza_como_laboratorio(r, vol, dia, herr)]",
                                  "quedan = [r for r in recs if not rechaza_como_laboratorio(r, vol, dia)]"),
    # S200c (R4FD-107, acta de la ronda 4)
    "107_acepta_otro_fin": ("    if fin != FIN_SELLADO:\n", "    if False:\n"),
    # S202: la salida agrega "exclusion_comun" después de "muestra"; la mutación es la misma.
    "107_sin_muestra": ('"muestra": muestra,', '"muestra": {},'),
    "105_sin_codigo": ('elif not cod["igual"]:', "elif False:"),
    "105_sin_declarar": ('codigos.setdefault(str(sha),', 'codigos.setdefault("uno",'),
    "106_sin_procedencia": ("referencia = {n: _sha256(Path(dest) / n) for n in CSV_REFERENCIA if (Path(dest) / n).exists()}",
                            "referencia = {}"),
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
        copia.write_text(texto, encoding="utf-8")
        env = dict(os.environ, EVALUAR_PISO_PATH=str(copia), PYTHONIOENCODING="utf-8")
        # La copia importa el S194 desde ROOT de su propia ruta: se la apunta al repo con un enlace de ruta.
        texto2 = texto.replace("ROOT = Path(__file__).resolve().parents[2]", "ROOT = Path(%r)" % str(ROOT))
        copia.write_text(texto2, encoding="utf-8")
        r = subprocess.run([sys.executable, "-m", "pytest", str(PRUEBA), "-q", "-p", "no:cacheprovider",
                            "--basetemp", str(tmp / nombre / "bt")], capture_output=True, text=True,
                           encoding="utf-8", env=env, cwd=str(ROOT))
        ult = (r.stdout.strip().splitlines() or [""])[-1]
        fallan = int(m.group(1)) if (m := re.search(r"(\d+) failed", ult)) else 0
        errores = int(m.group(1)) if (m := re.search(r"(\d+) error", ult)) else 0
        out[nombre] = {"ultima_linea": ult, "fallan": fallan, "errores": errores,
                       "atrapada": fallan > 0 and errores == 0}
        print(nombre, "|", ult, "| atrapada" if out[nombre]["atrapada"] else "| NO atrapada")
    ok = (out["sin_mutar"]["fallan"] == 0 and out["sin_mutar"]["errores"] == 0 and not out["caida"]["atrapada"]
          and all(v["atrapada"] for k, v in out.items() if k not in ("sin_mutar", "caida")))
    out["_veredicto"] = "OK" if ok else "FALLA"
    print("veredicto:", out["_veredicto"])
    (AQUI / "resultado_mutaciones_resello_s200.json").write_text(json.dumps(out, indent=1, ensure_ascii=False),
                                                                 encoding="utf-8", newline="\n")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
