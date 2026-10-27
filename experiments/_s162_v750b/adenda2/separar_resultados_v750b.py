# -*- coding: utf-8 -*-
"""S162 V750-B, adenda 2: separa los resultados del run en los de la lista sellada y los de la suplementaria.

POR QUÉ. El run lee `objetivos_run_v750b.json` (sellada + suplementaria), así que cada resultados_XX.json trae las dos.
La lectura sellada (adenda1/leer_v750b.py y analizar_v750b.py) tiene que ver EXACTAMENTE lo que habría visto sin la
suplementaria: el analizador imprime cuántos resultados cargó, y una pasada de más cambiaría esa línea. Este script
escribe dos carpetas con los mismos nombres de archivo: `sellado/` (ids menores que 100000) y `supl/` (los demás). La
lectura sellada corre sobre `sellado/`; el diagnóstico de posición, sobre las dos.
Uso: python separar_resultados_v750b.py --art <carpeta(s) de artefactos> --dest <carpeta nueva>
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ID0 = 100000


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--art", required=True, nargs="+")
    ap.add_argument("--dest", required=True)
    a = ap.parse_args(argv)
    dest = Path(a.dest)
    if dest.exists() and any(dest.iterdir()):
        print(f"{dest} no está vacía: no se escribe encima")
        return 2
    n = {"sellado": 0, "supl": 0}
    for d in a.art:
        for f in sorted(Path(d).rglob("resultados_*.json")):
            filas = json.loads(f.read_text(encoding="utf-8"))
            rel = f.relative_to(d)
            for parte, sel in (("sellado", [r for r in filas if r["id"] < ID0]), ("supl", [r for r in filas if r["id"] >= ID0])):
                q = dest / parte / Path(d).name / rel
                q.parent.mkdir(parents=True, exist_ok=True)
                q.write_text(json.dumps(sel, default=float), encoding="utf-8")
                n[parte] += len(sel)
    print(f"resultados separados: sellado {n['sellado']}, suplementaria {n['supl']} -> {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
