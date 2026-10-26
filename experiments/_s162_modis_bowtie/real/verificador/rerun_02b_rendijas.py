# -*- coding: utf-8 -*-
"""Paso 2b: los huecos que mide 02_cobertura.py, ¿son rendijas finas entre huellas o suelo sin mirar de verdad?
Repite el conteo en la caja de la ROI1 (+/- 7,875 km) con la huella agrandada 20 % (0,1 pixel por lado). Una rendija
de menos de 0,2 pixel se cierra; un hueco de verdad (un detector entero quitado sin copia) no. Control: C_sin_det0
tiene que seguir con huecos en el nadir. Al reves, el doble conteo se repite con la huella achicada 20 %: un
traslape de menos de 0,2 pixel (borde con borde) desaparece; una copia entera del mismo suelo no. Ademas lista las pasadas con mas de 10 % de huecos en 'todos' (borde del
granulo o falta de dato, no metodo).
Uso: python -I 02b_rendijas.py
"""
from __future__ import annotations

import collections
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # VERIFICADOR: importa comun.py del auditor; salidas en verificador/
import numpy as np  # noqa: E402
import comun as CM  # noqa: E402


def estrato(z):
    return "z<15" if z < 15 else "15-25" if z < 25 else "25-40" if z < 40 else "40-50" if z < 50 else "z>=50"


def main():
    pr, L = CM.pr_factory()
    obj, res = CM.objetivos(), CM.resultados()
    ids = [i for i in sorted(obj) if CM.evaluable(res.get(i))]
    tab = collections.defaultdict(lambda: collections.defaultdict(list))
    malas = []
    for i in ids:
        o, g = obj[i], obj[i]["grilla"]
        n = CM.cargar_nativo(i)
        G = CM.geometria(n, g["epsg"])
        px, py = CM.puntos_caja(g, 7875.0)
        for m in CM.ORDEN_METODOS:
            q = CM.mascara_quitar(G, m)
            c1, _ = CM.conteo_cobertura(G, q, px, py, escala=1.0)
            c2, _ = CM.conteo_cobertura(G, q, px, py, escala=1.2)
            c3, _ = CM.conteo_cobertura(G, q, px, py, escala=0.8)
            tab[estrato(o["z"])][m].append(((c1 == 0).mean(), (c2 == 0).mean(), (c1 >= 2).mean(), (c3 >= 2).mean()))
            if m == "todos" and (c1 == 0).mean() > 0.10:
                malas.append((i, o["volcan"], o["hora_utc"], o["z"], round(float((c1 == 0).mean()), 3),
                              int(np.isnan(n["lat_mxd03"]).sum()), int(np.isnan(n["b31"]).sum())))
    pr("caja ROI1 (+/- 7,875 km). Media por pasada: huecos con huella nominal | huecos con huella 1,2x | 2+ nominal | 2+ con huella 0,8x")
    for e in ("z<15", "15-25", "25-40", "40-50", "z>=50"):
        pr(f"  {e} (n {len(tab[e]['todos'])})")
        for m in CM.ORDEN_METODOS:
            v = np.array(tab[e][m])
            pr(f"     {m:24s} 0: {v[:, 0].mean():.4f} | 0 (1,2x): {v[:, 1].mean():.4f} | 2+: {v[:, 2].mean():.4f} | "
               f"2+ (0,8x): {v[:, 3].mean():.4f}")
    pr("\npasadas con mas de 10 % de huecos en 'todos' (id, volcan, hora, cenit, frac 0, NaN lat, NaN B31 del recorte):")
    for x in malas:
        pr("  ", x)
    (Path(__file__).with_name("02b_rendijas_salida.txt")).write_bytes(("\n".join(L) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
