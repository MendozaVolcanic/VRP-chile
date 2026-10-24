# -*- coding: utf-8 -*-
"""S162 V750-B: ensayo del analizador sobre las 510 grillas del frente N, en el formato que deja el probe.

POR QUÉ. El analizador tiene que correr de punta a punta (cargar, armar records, predicado del tablero con node,
controles) antes de que exista el run, y sus controles tienen que dar verde sobre datos conocidos: el control «K =
producción» usa los records de K que N guardó, y el nulo del contador perturba lo que las cajas publican. Se corre con
--solo-controles: NO imprime métricas de decisión (no se mira el resultado antes del sello).
Uso (desde un árbol de origin/main con esta carpeta):
  python ensayo_analizador.py --insumos <de extraer_insumos.sh de V750-C> --grillas D:/vrp-trabajo/temporales/s159_n
      --dest <carpeta temporal fuera del repo>
  python analizar_v750b.py --art <dest>/art --objetivos <dest>/objetivos_ensayo.json --evaluador <evaluar_d25.py>
      --solo-controles --salida <dest>/salida.txt
"""
from __future__ import annotations

import argparse
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
    ap.add_argument("--dest", required=True, type=Path)
    a = ap.parse_args()
    res = {}
    for f in sorted((a.insumos / "n").rglob("resultados_*.json")):
        for r in json.loads(f.read_text(encoding="utf-8")):
            if r.get("estado") == "ok" or r["id"] not in res:
                res[r["id"]] = r
    objs = []
    for nom in ("objetivos_n.json", "objetivos_censo.json"):
        objs += [o for o in json.loads((a.insumos / "n" / nom).read_text(encoding="utf-8")) if o["lab"] in
                 ("pos", "neg_limpio")]
    vy = {v["name"]: v for v in yaml.safe_load((RAIZ / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]}
    OV.completar(objs, vy, B.inner_desde_html())
    salida = []
    for o in objs:
        o["en_sc"] = False
        r = res.get(o["id"])
        if not r or r.get("estado") != "ok" or r.get("dayflag") != 0:
            continue
        gp = next((p for run in RUNS for p in sorted((a.grillas / run).glob(f"*/grilla_{o['id']:03d}.npz"))), None)
        if gp is None:
            continue
        z = np.load(gp)
        orc = {n: PV.oraculo_caja(z["m13"], z["m15"], 0, r["sunglint"], box, semillas=0)
               for n, box in PV.cajas(tuple(o["celda_crater"]), o["inner_km"]).items()}
        salida.append({"id": o["id"], "volcan": o["volcan"], "hora_utc": o["hora_utc"], "estado": "ok",
                       "dayflag": 0, "sunglint": r["sunglint"], "cobertura": PV.cobertura(z["m13"]),
                       "oraculo": orc, "brazos": {"K": r["brazos"]["K"]}})
    (a.dest / "art").mkdir(parents=True, exist_ok=True)
    (a.dest / "art" / "resultados_00.json").write_text(json.dumps(salida, default=float), encoding="utf-8")
    (a.dest / "objetivos_ensayo.json").write_text(json.dumps(objs, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"ensayo: {len(objs)} objetivos, {len(salida)} resultados en {a.dest}")


if __name__ == "__main__":
    main()
