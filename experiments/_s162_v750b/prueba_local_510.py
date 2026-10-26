# -*- coding: utf-8 -*-
"""S162 V750-B, prueba sin red del probe sobre las 510 grillas del frente N (pre-registro §11).

POR QUÉ. Antes de gastar un run hay que saber que el probe mide lo que dice: (1) B0 y B1 tienen que dar exactamente lo
que N midió con la caja del .m y con la sensible (mismo oráculo, misma grilla); (2) B2 y B3 tienen que actuar, o sea
cambiar alguna máscara, y donde se espera: Cordón Caulle y Tupungatito, cuyo cráter cae lejos del centro de la grilla.
NO calcula las métricas de decisión (P1, P2): eso es del run, para no mirar el resultado antes del sello.
Uso (desde un árbol de origin/main con esta carpeta): python prueba_local_510.py --insumos <de extraer_insumos.sh de
V750-C> --grillas D:/vrp-trabajo/temporales/s159_n
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

import numpy as np
import yaml

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(RAIZ / "scripts"))
import probe_v750b as PV  # noqa: E402
import objetivos_v750b as OV  # noqa: E402
import banco_paridad as B  # noqa: E402

RUNS = ("run_39682867040", "run_39693661527", "run_39680724047")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--insumos", required=True, type=Path)
    ap.add_argument("--grillas", required=True, type=Path)
    a = ap.parse_args()
    res = {}
    for f in sorted((a.insumos / "n").rglob("resultados_*.json")):
        for r in json.loads(f.read_text(encoding="utf-8")):
            if r.get("estado") == "ok" or r["id"] not in res:
                res[r["id"]] = r
    objs = []
    for nom in ("objetivos_n.json", "objetivos_censo.json"):
        objs += json.loads((a.insumos / "n" / nom).read_text(encoding="utf-8"))
    vy = {v["name"]: v for v in yaml.safe_load((RAIZ / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]}
    OV.completar(objs, vy, B.inner_desde_html())
    L = []

    def pr(*x):
        s = " ".join(str(y) for y in x)
        print(s, flush=True)
        L.append(s)

    pr("celda del cráter por volcán (fila, columna; centro = 33, 33):",
       {v: o["celda_crater"] for v, o in {o["volcan"]: o for o in objs}.items()})
    ctrl = collections.Counter()
    cambia = collections.Counter()
    for o in objs:
        r = res.get(o["id"])
        if not r or r.get("estado") != "ok" or r.get("dayflag") != 0 or not r.get("oraculo"):
            continue
        gp = next((p for run in RUNS for p in sorted((a.grillas / run).glob(f"*/grilla_{o['id']:03d}.npz"))), None)
        if gp is None:
            ctrl["sin_grilla"] += 1
            continue
        z = np.load(gp)
        s = {n: PV.oraculo_caja(z["m13"], z["m15"], 0, r["sunglint"], box, semillas=0)
             for n, box in PV.cajas(tuple(o["celda_crater"]), o["inner_km"]).items()}
        for nom, ref in (("B0", "geo_linear"), ("B1", "geo_linear_anillo_sensible")):
            x, y = s[nom], r["oraculo"][ref]
            ok = x["npix"] == y["npix"] and (x["vrp_mw"] is None and y["vrp_mw"] is None
                                              or abs((x["vrp_mw"] or 0) - (y["vrp_mw"] or 0)) < 1e-9)
            ctrl[f"{nom}_igual_a_N" if ok else f"{nom}_DISTINTO"] += 1
        ctrl["pasadas"] += 1
        for nom in ("B2", "B3"):
            # sólo fila y columna: el tercer campo de cada píxel es la zona de la caja, que cambia por construcción
            if sorted((p[0], p[1]) for p in s[nom]["pixeles"]) != sorted((p[0], p[1]) for p in s["B0"]["pixeles"]):
                cambia[(nom, o["volcan"])] += 1
    pr("controles:", dict(ctrl))
    pr("pasadas con máscara distinta de B0, por brazo y volcán:", dict(sorted(cambia.items())))
    (AQUI / "prueba_local_510_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
