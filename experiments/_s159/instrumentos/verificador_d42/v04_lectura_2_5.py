# -*- coding: utf-8 -*-
"""Verificador D-42, afirmacion 8: que hace global_ventana de HOY (b57ecfe62) con cada combinacion de P2 por sensor,
y con M INDECIDIBLE, para juzgar las dos lecturas de ADENDA_CALIBRACION_P2.md §2.5. No decide: informa.

Pregunta 1: si la precedencia estuviera al reves, ¿se ve? Si: la fila (INDECIDIBLE, PIERDE) cambiaria de NO CUMPLE a
INDECIDIBLE. Pregunta 2: si global_ventana estuviera muerta, ¿se ve? Si: (CUMPLE, GANA, GANA) tiene que dar SIN EFECTO
y (VETADO, ...) NO CUMPLE (veto).
"""
import itertools
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[3]
sys.path.insert(0, str(RAIZ / "experiments" / "_s157_prereg_d25"))
import evaluar_d25 as X  # noqa: E402


def ver_base(p1_375="CUMPLE", p1_750="CUMPLE", m="NEUTRO"):
    ver = {"P1|VIIRS375": p1_375, "P1|VIIRS750": p1_750, "P1b|VIIRS375": "SIN CRUCES", "P1b|VIIRS750": "SIN CRUCES"}
    for nom, modo in X.ESTRATOS:
        ver["M|%s" % nom] = m
    return ver


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print("global_ventana de %s" % X.__file__)
    print("== P2 cruzado entre sensores (P1 CUMPLE en los dos, M NEUTRO en todos)")
    for a, b in itertools.product(("INDECIDIBLE", "PIERDE", "GANA", "EMPATE", "BLOQUEA", "SIN SUSTRATO"), repeat=2):
        ver = dict(ver_base(), **{"P2|VIIRS375": a, "P2|VIIRS750": b})
        print("   P2 V375 %-12s V750 %-12s -> %s" % (a, b, X.global_ventana(ver, True)[0]))
    print("== «como hoy con un M INDECIDIBLE»: M VIIRS750|z<=40 INDECIDIBLE, P2 variando")
    for a, b in (("PIERDE", "EMPATE"), ("EMPATE", "EMPATE"), ("BLOQUEA", "EMPATE"), ("GANA", "GANA"), ("INDECIDIBLE", "PIERDE")):
        ver = dict(ver_base(), **{"P2|VIIRS375": a, "P2|VIIRS750": b, "M|VIIRS750|z<=40": "INDECIDIBLE"})
        print("   M INDECIDIBLE, P2 V375 %-12s V750 %-12s -> %s" % (a, b, X.global_ventana(ver, True)[0]))
    print("== controles: VETADO manda antes; CUMPLE/GANA/GANA sin M -> SIN EFECTO")
    print("   VETADO + P2 INDECIDIBLE/PIERDE ->", X.global_ventana(dict(ver_base(p1_375="VETADO"), **{"P2|VIIRS375": "INDECIDIBLE", "P2|VIIRS750": "PIERDE"}), True)[0])
    print("   CUMPLE + GANA/GANA ->", X.global_ventana(dict(ver_base(), **{"P2|VIIRS375": "GANA", "P2|VIIRS750": "GANA"}), True)[0])
    print("== combinar sobre dos ventanas (JSON minimo): V1 INDECIDIBLE, V2 NO CUMPLE (suma de errores) y al reves")
    import json, tempfile  # noqa: E401
    with tempfile.TemporaryDirectory() as td:
        f1, f2 = Path(td) / "v1.json", Path(td) / "v2.json"
        f1.write_text(json.dumps({"ventana": "V1", "estado": "INDECIDIBLE", "mejora": False, "empeora": False, "vale_para_decidir": True, "dias_excluidos": []}), encoding="utf-8")
        f2.write_text(json.dumps({"ventana": "V2", "estado": "NO CUMPLE (suma de errores)", "mejora": False, "empeora": False, "vale_para_decidir": True, "dias_excluidos": []}), encoding="utf-8")
        print("   combinar ->", X.combinar([str(f1), str(f2)]))


if __name__ == "__main__":
    main()
