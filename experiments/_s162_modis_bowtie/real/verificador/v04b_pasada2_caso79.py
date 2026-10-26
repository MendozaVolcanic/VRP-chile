# -*- coding: utf-8 -*-
"""Verificador B4, mecanismo del caso 79 (Lascar 2026-03-15 07:45, z 30,5, crater visto UNA vez): con A la magnitud
sube 8,7 % y aparece la celda (24,24) sin que cambie ninguna celda de la caja ROI1 (A_sig: 0 de 225) ni los umbrales
de la pasada 1. Hipotesis: la celda entra por la PASADA 2 (fondo local recomputado sin los alertados de la pasada 1) y
por el umbral de cumbre u_nti2 = max(mu + 5 sigma, 0,003), cuyo sigma es GLOBAL (toda la grilla de 51 x 51 km): las
~130 celdas que cambian a mas de 8 km del crater mueven sigma y bajan el umbral lo justo.
Mide, con 'todos', A_ant y A_sig: u_nti2 / u_eti2 de la pasada 2, y para la celda (24,24) su c_nti y c_eti de la
pasada 2 (recomputados como el oraculo), con el margen contra el umbral.
Pregunta 1: si el mecanismo fuera otro (p. ej. cambio de valor en la celda), el margen de la celda cambiaria y el
umbral no; si es el que se postula, la celda no cambia y el umbral si. Pregunta 2: 'todos' contra si mismo da 0.
Uso: python -I v04b_pasada2_caso79.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np  # noqa: E402
import comun as CM  # noqa: E402

AQUI = Path(__file__).resolve().parent
ORA = CM.MP.ORA


def pasada2_detalle(mir, tir, box, dayflag, cfg, celda):
    """Replica ORA.detectar hasta la pasada 2 y devuelve umbrales y c_nti/c_eti de la pasada 2 en `celda`."""
    with CM.MP.longitudes(cfg):
        m13 = np.asarray(mir, float)
        m15 = np.array(tir, float)
        box = np.array(box, float)
        box[:, [0, -1]] = np.nan
        box[[0, -1], :] = np.nan
        m0 = np.where(box == 0, 1.0, np.nan)
        m1 = np.where(box == 1, 1.0, np.nan)
        m2 = np.where(box == 2, 1.0, np.nan)
        excl = np.isnan(box)
        bt15 = ORA.radiancia_a_temperatura(m15, ORA.LAMBDA_M15)
        with np.errstate(invalid="ignore"):
            frio = bt15 <= 200
        bt15[frio] = np.nan
        m15[frio] = np.nan
        with np.errstate(invalid="ignore", divide="ignore"):
            nti = (m13 - m15) / (m13 + m15)
        nti_roi = nti.copy()
        nti_roi[excl] = np.nan
        u_abs, s1, s2, n1, n2, e1, e2 = (-0.7, 10, 5, 0.02, 0.003, 0.01, 0.003) if dayflag == 0 else \
            (-0.5, 15, 15, 0.02, 0.02, 0.02, 0.02)
        with np.errstate(invalid="ignore"):
            absol = nti_roi > u_abs
        p1 = ORA._pasada_contextual(nti_roi, bt15, m15, excl, m0, m1, m2, absol, s1, s2, n1, n2, e1, e2)
        ctx1 = p1[0] | p1[1] | p1[2]
        exc2 = absol | ctx1
        p2 = ORA._pasada_contextual(nti_roi, bt15, m15, excl, m0, m1, m2, exc2, s1, s2, n1, n2, e1, e2)
        # c_nti y c_eti de la pasada 2 en la celda (mismas lineas que el oraculo, l. 275-298 y 319-368)
        pob = nti_roi.copy()
        pob[exc2] = np.nan
        fondo_loc = ORA._media_3x3_omitnan(pob)
        fondo_loc[excl] = np.nan
        c_nti = pob - fondo_loc
        with np.errstate(invalid="ignore"):
            c_nti[c_nti < -0.1] = np.nan
        m13_esp = ORA.temperatura_a_radiancia(bt15, ORA.LAMBDA_M13)
        with np.errstate(invalid="ignore", divide="ignore"):
            nti_esp = (m13_esp - m15) / (m13_esp + m15)
        nti_esp[exc2] = np.nan
        nti_esp[excl] = np.nan
        ref = np.polyval(np.array(p2[3]["coef"]), nti_esp)
        eti = pob - ref
        c_eti = eti - ORA._media_3x3_omitnan(eti)
        c_eti[excl] = np.nan
        a, b = celda
        return {"n_p1": int(ctx1.sum()), "n_p2": int((p2[0] | p2[1] | p2[2]).sum()), "box": float(box[a, b]),
                "u_nti2": p2[3]["u_nti2"], "u_eti2": p2[3]["u_eti2"], "mu2": p2[3]["mu_nti"], "sd2": p2[3]["sd_nti"],
                "mu_e2": p2[3]["mu_eti"], "sd_e2": p2[3]["sd_eti"], "c_nti": float(c_nti[a, b]),
                "c_eti": float(c_eti[a, b]), "alerta_p2": bool((p2[0] | p2[1] | p2[2])[a, b]),
                "n_ajuste": p2[3]["n_ajuste"]}


def main():
    pr, L = CM.pr_factory()
    obj, res = CM.objetivos(), CM.resultados()
    cfg = CM.MP.SENSORES["MODIS"]
    for i, celda in [(79, (24, 24)), (147, (26, 25)), (65, (27, 25))]:
        o, r, g = obj[i], res[i], obj[i]["grilla"]
        n = CM.cargar_nativo(i)
        G = CM.geometria(n, g["epsg"])
        box = CM.MP.caja(g, g["X0"], g["Y0"], "fisica")
        pr(f"\n== {i} {o['volcan']} {o['hora_utc']} z {o['z']:.1f}; celda {celda}")
        for m in ["todos", "A_centro_cubierto_ant", "A_centro_cubierto_sig"]:
            q = CM.mascara_quitar(G, m)
            mir, tir = CM.PP.grillar(CM.crop_desde_nativo(n, q), g, g["epsg"])
            d = pasada2_detalle(mir, tir, box, r["dayflag"], cfg, celda)
            pr(f"   {m:22s} box {d['box']:.0f} n_p1 {d['n_p1']} n_p2 {d['n_p2']} | pasada 2: u_nti2 {d['u_nti2']:.6f} "
               f"(mu {d['mu2']:+.6f} sd {d['sd2']:.6f}; piso 0,003) u_eti2 {d['u_eti2']:.6f} (sd_e {d['sd_e2']:.6f}) "
               f"n_ajuste {d['n_ajuste']} | celda: c_nti {d['c_nti']:+.6f} (margen {d['c_nti'] - d['u_nti2']:+.6f}) "
               f"c_eti {d['c_eti']:+.6f} (margen {d['c_eti'] - d['u_eti2']:+.6f}) alerta_p2 {d['alerta_p2']}")
    (AQUI / "v04b_pasada2_caso79_salida.txt").write_bytes(("\n".join(L) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
