# -*- coding: utf-8 -*-
"""Paso 4, los casos que cambian en 03_ablacion.py: para cada celda alertada (con 'todos' o con algun metodo), los
pixeles nativos a menos de 2,5 km de su centro, con barrido, detector, temperatura de brillo MIR (B22 primaria, misma
lambda que el port) y que metodo los quita. Sirve para ver si la publicacion que se gana o se pierde depende de una
copia duplicada del mismo suelo. Lee 03_ablacion.json (no vuelve a correr el port).
Uso: python -I 04_casos.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # VERIFICADOR: importa comun.py del auditor; salidas en verificador/
import numpy as np  # noqa: E402
import comun as CM  # noqa: E402

CASOS = [1120, 1251, 1093, 141, 147, 65, 79, 89]
MET = ["A_centro_cubierto_ant", "A_centro_cubierto_sig", "B_filas_borde", "C_sin_det0"]


def main():
    pr, L = CM.pr_factory()
    obj = CM.objetivos()
    ab = {int(k): v for k, v in json.loads(Path(__file__).with_name("03_ablacion.json").read_text("utf-8")).items()}
    ORA = CM.MP.ORA
    for i in CASOS:
        o, g = obj[i], obj[i]["grilla"]
        n = CM.cargar_nativo(i)
        G = CM.geometria(n, g["epsg"])
        mir = CM.merge_mir_bands(n["b21"], n["b22"], True)
        with CM.MP.longitudes(CM.MP.SENSORES["MODIS"]):
            bt = ORA.radiancia_a_temperatura(np.asarray(mir, float), CM.MP.SENSORES["MODIS"]["lam_mir"])
        Q = {m: CM.mascara_quitar(G, m) for m in MET}
        pr(f"\n== {i} {o['volcan']} {o['hora_utc']} cenit {o['z']} clase {o['clase']} MIROVA {o['mirova_vrp']}")
        for m in ["todos"] + MET:
            v = ab[i][m]
            pr(f"   {m:24s} npix {v['npix']} VRP {v['vrp_mw']} publica {v.get('publica')} celdas "
               f"{[p[:2] for p in v['pixeles']]}")
        celdas = sorted({tuple(p[:2]) for m in ["todos"] + MET for p in ab[i][m]["pixeles"]})
        for (a, b) in celdas:
            xc = g["ul_x"] + g["celda"] * (b + 0.5)
            yc = g["ul_y"] - g["celda"] * (a + 0.5)
            d = np.hypot(G["x"] - xc, G["y"] - yc)
            sel = np.argwhere(d < 2500)
            sel = sel[np.argsort(-bt[tuple(sel.T)])][:6]
            pr(f"   celda ({a},{b}) a {np.hypot(xc - g['X0'], yc - g['Y0']) / 1000:.2f} km de (X0,Y0); 6 nativos mas "
               f"calientes a < 2,5 km: (barrido, det, BT MIR K, dist km, quitado por {'/'.join(x.split('_')[0] + x[-3:] for x in MET)})")
            for (r, c) in sel:
                pr(f"      ({int(G['scan'][r, c])}, {int(G['det'][r, c])}, {bt[r, c]:.2f}, {d[r, c] / 1000:.2f}, "
                   f"{''.join('x' if Q[m][r, c] else '.' for m in MET)})")
    (Path(__file__).with_name("04_casos_salida.txt")).write_bytes(("\n".join(L) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
