# -*- coding: utf-8 -*-
"""O2-375, magnitud PRELIMINAR de V375-C en las escenas de 1 a 4 píxeles: razón contra MIROVA con el fondo del port y con
la vara (vara_preliminar_375.json), por brazo, sólo en pasadas positivas (MIROVA alertó) con VRP de MIROVA > 0.

POR QUÉ aparte del evaluador. La lectura M del evaluador es la mediana sobre TODAS las positivas publicadas, y las de 1 a 4
píxeles son una parte; una mediana puede no moverse aunque esa parte cambie. Esta tabla mira sólo esa parte. No filtra por
publicación (el evaluador sí): es una cota de cuánto puede mover la vara, no la lectura que decide.
Uso: python -I magnitud_vara_375.py
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
BRAZOS = ("M14", "C13", "C14", "C21", "M13", "M21", "PIX7", "SENS", "CIRC", "SENS_PT")


def main():
    vara = {e["posicion"]: e for e in json.loads((AQUI / "vara_preliminar_375.json").read_text(encoding="utf-8"))["escenas"]}
    et = json.loads((AQUI / "entradas_v375_etiquetas.json").read_text(encoding="utf-8"))["escenas"]
    print(f"regla de relleno: {json.loads((AQUI / 'vara_preliminar_375.json').read_text(encoding='utf-8'))['regla']}")
    print("brazo  n   mediana port/MIROVA  mediana vara/MIROVA  cambian>1%  máx |vara/port - 1|")
    for b in BRAZOS:
        filas = [(e, vara[e["posicion"]]) for e in et if b in e["brazos"] and e["clase"].startswith("pos")
                 and e.get("lote") != "CTL" and (e.get("mirova_vrp_mw") or 0) > 0]
        if not filas:
            continue
        rp = np.array([v["vrp_port_mw"] / e["mirova_vrp_mw"] for e, v in filas])
        rv = np.array([v["vrp_vara_mw"] / e["mirova_vrp_mw"] for e, v in filas])
        d = np.array([abs(v["vrp_vara_mw"] / v["vrp_port_mw"] - 1) if v["vrp_port_mw"] else np.inf for _, v in filas])
        print(f"{b:6s} {len(filas):3d}  {np.median(rp):8.3f}             {np.median(rv):8.3f}            "
              f"{int((d > 0.01).sum()):4d}       {np.max(d):.3f}")


if __name__ == "__main__":
    main()
