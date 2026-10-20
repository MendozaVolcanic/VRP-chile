# -*- coding: utf-8 -*-
"""Enmienda POST HOC, declarada (escrita después de ver el resultado del probe, 2026-10-20).

POR QUÉ. El techo de selección pre-registrado (`analizar_probe.py`) suma la potencia de los vecinos no alertados
restando el ANILLO. Dio 0 en los 10 gránulos porque todos los vecinos del cúmulo están más fríos que el anillo
(261 a 269 K contra 272 a 277 K). Pero MIROVA, si alertara a esos vecinos, les restaría la media de SUS vecinos, no el
anillo. Este script acota eso: para cada vecino no alertado del cúmulo, su exceso de radiancia sobre la media de
radiancia de todos los vecinos no alertados del cúmulo (el mismo conjunto), sumado con k·A. Es una cota superior
generosa de lo que la selección podría agregar con el fondo de MIROVA: supone que MIROVA alerta a TODOS los vecinos
más tibios que la media, cosa que el segundo pase de K no hace en ninguno (sp_pasa_t2 = 0 en los 10).

Uso: python seleccion_fondo_vecinos.py resultado
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[2]))
from pipeline.constants import C1, C2  # noqa: E402

LAM = {"MODIS": 3.929, "750": 4.050, "375": 3.740}            # banda con que cada procesador vuelve a radiancia
KA = {"MODIS": 18.9 * 1e6, "750": 19.7 * 562500, "375": 18.0 * 140625}   # k·A nadir (CLAUDE.md, reglas científicas)


def planck(bt, lam):
    return C1 / (lam ** 5 * (np.exp(C2 / (lam * np.asarray(bt, dtype=np.float64))) - 1))


def main():
    print("%-30s %5s %8s %8s %10s %8s" % ("gránulo", "n_vec", "BTvec_med", "BTvec_max", "S_sel_vec", "falta"))
    analisis = {(p["sensor"], p["hhmm"]): p for p in json.loads((Path(sys.argv[1]) / "analisis.json").read_text(encoding="utf-8"))}
    for f in sorted(Path(sys.argv[1]).rglob("*_*.json")):
        if f.name == "analisis.json":
            continue
        r = json.loads(f.read_text(encoding="utf-8"))
        fam = "MODIS" if "MODIS" in r["sensor"] else ("750" if r["sensor"].endswith("_750") else "375")
        br = "d25_rad" if fam == "MODIS" else "d25_h3"
        vec = ((r.get(br) or {}).get("seleccion") or {}).get("vecinos") or []
        if not vec:
            continue
        L = planck([v["bt_k"] for v in vec], LAM[fam])
        s = float(np.sum(np.maximum(L - L.mean(), 0.0)) * KA[fam] / 1e6)
        p = analisis.get((r["sensor"], r["granulo"].split(".")[2]), {})
        x = (p.get("brazos") or {}).get(br, {})
        falta = (p["M"] - x["disp"]) if (p.get("M") and x.get("disp") is not None) else None
        print("%-30s %5d %8.1f %8.1f %10.3f %8s" % (f.stem, len(vec), float(np.median([v["bt_k"] for v in vec])),
                                                    max(v["bt_k"] for v in vec), s, ("%.2f" % falta) if falta is not None else "-"))


if __name__ == "__main__":
    main()
