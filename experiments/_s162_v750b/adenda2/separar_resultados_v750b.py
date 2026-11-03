# -*- coding: utf-8 -*-
"""S162 V750-B, adenda 2: separa los resultados del run en los de la lista sellada y los de la suplementaria.

POR QUÉ. El run lee `objetivos_run_v750b.json` (sellada + suplementaria), así que cada resultados_XX.json trae las dos.
La lectura sellada (adenda1/leer_v750b.py y analizar_v750b.py) tiene que ver EXACTAMENTE lo que habría visto sin la
suplementaria: el analizador imprime cuántos resultados cargó, y una pasada de más cambiaría esa línea. Este script
escribe dos carpetas: `sellado/` (ids menores que 100000) y `supl/` (los demás), cada carpeta de artefactos con su
índice delante, para que una corrida y su relanzamiento no se pisen aunque se llamen igual (VAD2-01). La
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
    leidas = 0
    for k, d in enumerate(a.art):
        for f in sorted(Path(d).rglob("resultados_*.json")):
            filas = json.loads(f.read_text(encoding="utf-8"))
            leidas += len(filas)
            rel = f.relative_to(d)
            for parte, sel in (("sellado", [r for r in filas if r["id"] < ID0]), ("supl", [r for r in filas if r["id"] >= ID0])):
                # VAD2-01: el índice de la carpeta va en la ruta, así la corrida y su relanzamiento nunca se pisan aunque
                # sus carpetas se llamen igual; el analizador junta los duplicados como siempre (un «ok» gana)
                q = dest / parte / f"{k:02d}_{Path(d).name}" / rel
                if q.exists():
                    print(f"{q} ya existe: no se escribe encima")
                    return 2
                q.parent.mkdir(parents=True, exist_ok=True)
                q.write_text(json.dumps(sel, default=float), encoding="utf-8")
    # el conteo sale de RELEER lo escrito, no de lo que se quiso escribir
    n = {parte: sum(len(json.loads(q.read_text(encoding="utf-8"))) for q in (dest / parte).rglob("resultados_*.json"))
         for parte in ("sellado", "supl")}
    print(f"resultados separados: leídos {leidas}, sellado {n['sellado']}, suplementaria {n['supl']} -> {dest}")
    if n["sellado"] + n["supl"] != leidas:
        print("== la suma de las partes no es lo leído: no uses esta separación")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
