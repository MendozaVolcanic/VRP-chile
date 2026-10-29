# -*- coding: utf-8 -*-
"""S167 V375-E, adenda 3 (§9.11): repaso del nulo para las mutaciones que el nulo completo dejó sin atrapar por aserción
(L85 cayó con KeyError y se reescribió para que no caiga; L94 sobrevivió y se le agregó la prueba de la curva que la
atrapa). Corre la identidad, el control de caída y esas mutaciones con la batería de hoy, con las mismas funciones de
mutar_adenda2.py. Uso: python -I repasar_mutaciones.py L85 L94  (escribe repasar_mutaciones_salida.txt)
"""
import io
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import mutar_adenda2 as M  # noqa: E402


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    L = []

    def pr(s):
        print(s, flush=True)
        L.append(s)
    ids = sys.argv[1:]
    por_id = {m[0]: m for m in M.MUTACIONES}
    assert ids and all(k in por_id for k in ids), ids
    e, f = M.una("identidad", None)
    pr(f"IDENTIDAD (copia sin mutar): {'PASA' if e == 'SOBREVIVE' else 'FALLA ' + e} {f[:3]}")
    e, f = M.una("control", M.CONTROL)
    pr(f"CONTROL (rompe la importación): {e} {f}  (tiene que ser CAIDA)")
    for k in ids:
        e, f = M.una(k, por_id[k])
        pr(f"{k} {e:9s} {f[:2]}")
    (AQUI / "repasar_mutaciones_salida.txt").write_text("".join(x + chr(10) for x in L), encoding="utf-8")


if __name__ == "__main__":
    main()
