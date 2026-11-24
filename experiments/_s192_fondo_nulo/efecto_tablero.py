# -*- coding: utf-8 -*-
"""S192: qué cambia en el tablero con el reemplazo de fondo nulo, con las funciones reales de frontend/index.html.

POR QUÉ. El tablero no publica un record por tener VRP: mirovaEqVrp exige clase «summit» y cúmulo dentro del radio
interno del volcán (vista por defecto, sin «incluir lejanas»). Este script toma los records objetivo de
data/mirova_equivalent tal como están en un commit (antes del reemplazo), los transforma con reemplazo_fondo_nulo.py
y evalúa en node mirovaEqVrp (por defecto y con lejanas) y escenaSinDato antes y después.

USO: python experiments/_s192_fondo_nulo/efecto_tablero.py [--commit origin/main]   (necesita node)
"""
from __future__ import annotations

import argparse
import copy
import json
import subprocess
import sys
from pathlib import Path

import yaml

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(RAIZ / "tests"))
import reemplazo_fondo_nulo as R  # noqa: E402
from test_reemplazo_fondo_nulo_s192 import _fuente  # noqa: E402


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", default="origin/main")
    a = ap.parse_args(argv)
    inner = {v["name"]: v.get("inner_radius_km") for v in
             yaml.safe_load((RAIZ / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]}
    sha = subprocess.run(["git", "-C", str(RAIZ), "rev-parse", a.commit], capture_output=True, text=True).stdout.strip()
    nombres = subprocess.run(["git", "-C", str(RAIZ), "ls-tree", "--name-only", sha, "data/mirova_equivalent/"],
                             capture_output=True, text=True).stdout.split()
    filas = []
    for n in sorted(nombres):
        if not n.endswith(".json"):
            continue
        d = json.loads(subprocess.run(["git", "-C", str(RAIZ), "show", f"{sha}:{n}"], capture_output=True).stdout)
        for r in d.get("records", []):
            if R.es_objetivo(r):
                v = Path(n).stem
                filas.append({"volcan": v, "inner": inner[v], "antes": r, "despues": R.transformar(copy.deepcopy(r))})
    src = (RAIZ / "frontend" / "index.html").read_text(encoding="utf-8")
    js = "\n".join(_fuente(src, f) for f in ("mirovaEqVrp", "escenaSinDato")) + "\nconst F = " + json.dumps(filas) + \
        ";\nprocess.stdout.write(JSON.stringify(F.map(f => [f.antes, f.despues].map(r => [mirovaEqVrp(r, f.inner), " \
        "mirovaEqVrp(r, f.inner, true), escenaSinDato(r)]))));"
    tmp = AQUI / "_tmp_efecto.js"
    tmp.write_text(js, encoding="utf-8")
    try:
        out = json.loads(subprocess.run(["node", str(tmp)], capture_output=True, text=True, encoding="utf-8",
                                        check=True).stdout)
    finally:
        tmp.unlink()
    print(f"commit {sha}")
    print("| Volcán | Sensor | Pasada (UTC) | Clase antes | Tablero antes (MW) | Con lejanas antes (MW) | Después |")
    print("|---|---|---|---|---|---|---|")
    for f, (antes, despues) in zip(filas, out):
        r = f["antes"]
        print(f"| {f['volcan']} | {r['sensor']} | {r['datetime_utc']} | {r.get('distance_class')} | {antes[0]} | "
              f"{antes[1]} | {despues[0]} MW, «{despues[2]}» |")
    pub = sum(1 for a_, _d in out if a_[0] > 0)
    print(f"\npublicados hoy en la vista por defecto: {pub} de {len(out)}; con lejanas: "
          f"{sum(1 for a_, _d in out if a_[1] > 0)}; después del reemplazo: "
          f"{sum(1 for _a, d_ in out if d_[1] > 0)} con lejanas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
